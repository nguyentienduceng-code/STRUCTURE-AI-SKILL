# -*- coding: utf-8 -*-
"""accoreconsole_adapter.py — Isolated Autodesk AutoCAD 2021 Core Console DXF->DWG & AUDIT/PLOT adapter."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_ACCORECONSOLE_CANDIDATES: List[str] = [
    r"C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2020\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe",
]


def detect_accoreconsole(candidates: Optional[List[str]] = None) -> Optional[str]:
    """Return path to AutoCAD accoreconsole.exe if installed on host, else None."""
    env_exe = os.environ.get("ACCORECONSOLE_EXE", "").strip()
    search_list: List[str] = ([env_exe] if env_exe else []) + list(candidates or DEFAULT_ACCORECONSOLE_CANDIDATES)
    for item in search_list:
        if item and Path(item).is_file():
            return str(Path(item))
    return None


def _decode_console_output(raw: bytes) -> str:
    if not raw:
        return ""
    if b"\x00" in raw:
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def _is_temp_path(path: Path) -> bool:
    tmp_root = Path(tempfile.gettempdir()).resolve()
    try:
        path.resolve().relative_to(tmp_root)
        return True
    except ValueError:
        return False


def convert_dxf_to_dwg_via_accoreconsole(
    dxf_path: str | Path,
    out_dwg: str | Path = "",
    *,
    target_version: str = "2018",
    purge_all: bool = True,
    run_audit: bool = True,
    timeout_sec: float = 90.0,
    accoreconsole_exe: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert DXF to native AutoCAD DWG inside an isolated local temp workspace."""
    exe = accoreconsole_exe or detect_accoreconsole()
    if not exe or not Path(exe).is_file():
        return {
            "status": "UNAVAILABLE",
            "engine": "accoreconsole",
            "reason": "AutoCAD Core Console (accoreconsole.exe) không tìm thấy trên máy.",
        }

    src_dxf = Path(dxf_path).resolve()
    if not src_dxf.is_file():
        return {"status": "E001", "engine": "accoreconsole", "error": f"Không tìm thấy tệp DXF: {dxf_path}"}
    if src_dxf.suffix.lower() != ".dxf":
        return {"status": "E001", "engine": "accoreconsole", "error": f"Tệp không đúng định dạng .dxf: {dxf_path}"}

    dst_dwg: Optional[Path] = None
    if str(out_dwg).strip():
        dst_dwg = Path(out_dwg).resolve()
        # Protect any pre-existing DWG outside temp scratch from accidental overwrite
        if dst_dwg.exists() and not _is_temp_path(dst_dwg):
            return {
                "status": "DENIED",
                "engine": "accoreconsole",
                "error": f"Từ chối ghi đè tệp DWG đã tồn tại (bảo vệ bất biến): {dst_dwg}",
            }

    job_id = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=f"accore_{job_id}_") as td:
        td_path = Path(td)
        staged_dxf = td_path / src_dxf.name
        staged_dwg = td_path / src_dxf.with_suffix(".dwg").name
        scr_path = td_path / "convert.scr"

        shutil.copy2(str(src_dxf), str(staged_dxf))
        out_forward = str(staged_dwg).replace("\\", "/")

        lines = ["FILEDIA", "0"]
        if purge_all:
            lines.extend(["_-PURGE", "_ALL", "*", "_N"])
        if run_audit:
            lines.extend(["_AUDIT", "_Y"])
        lines.extend(["_SAVEAS", str(target_version), f'"{out_forward}"', "_QUIT", "_Y", ""])
        scr_path.write_text("\n".join(lines), encoding="utf-8")

        try:
            proc = subprocess.run(
                [exe, "/i", str(staged_dxf), "/s", str(scr_path), "/l", "en-US"],
                capture_output=True,
                timeout=timeout_sec,
                check=False,
            )
        except Exception as exc:
            return {"status": "FAIL", "engine": "accoreconsole", "error": str(exc)}

        log_text = _decode_console_output(proc.stdout)
        if not staged_dwg.is_file() or staged_dwg.stat().st_size == 0:
            err_tail = "\n".join(ln.strip() for ln in log_text.splitlines()[-15:] if ln.strip())
            return {
                "status": "FAIL",
                "engine": "accoreconsole",
                "returncode": proc.returncode,
                "error": f"accoreconsole không tạo được DWG. Log: {err_tail}",
            }

        audit_errors: Optional[int] = None
        audit_fixes: Optional[int] = None
        m = re.search(r"Total errors found\s+(\d+)\s+fixed\s+(\d+)", log_text, re.IGNORECASE)
        if m:
            audit_errors = int(m.group(1))
            audit_fixes = int(m.group(2))

        if dst_dwg is not None:
            dst_dwg.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(staged_dwg), str(dst_dwg))
            final_dwg = dst_dwg
        else:
            fallback_dir = Path(tempfile.gettempdir()) / "accoreconsole_exports"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            final_dwg = fallback_dir / f"{src_dxf.stem}_{job_id}.dwg"
            shutil.copy2(str(staged_dwg), str(final_dwg))

        return {
            "status": "OK",
            "engine": "accoreconsole",
            "accoreconsole_exe": exe,
            "target_version": target_version,
            "output_dwg": str(final_dwg),
            "verified_file_exists": final_dwg.is_file(),
            "file_bytes": final_dwg.stat().st_size if final_dwg.is_file() else 0,
            "audit_errors": audit_errors,
            "audit_fixes": audit_fixes,
            "returncode": proc.returncode,
        }


def _parse_xref_list(log_text: str) -> List[Dict[str, str]]:
    """Parse AutoCAD `-XREF ? *` table rows (`\"name\"   Overlay|Attach   path`)."""
    xrefs: List[Dict[str, str]] = []
    pat = re.compile(r'^\s*"([^"]+)"\s+(Overlay|Attach)\s+(.+?)\s*$', re.IGNORECASE)
    for ln in log_text.splitlines():
        m = pat.match(ln)
        if m:
            xrefs.append({
                "name": m.group(1),
                "type": m.group(2).capitalize(),
                "path": m.group(3).strip(),
            })
    return xrefs


def audit_dwg_readonly_via_accoreconsole(
    dwg_path: str | Path,
    *,
    timeout_sec: float = 90.0,
    accoreconsole_exe: Optional[str] = None,
) -> Dict[str, Any]:
    """Run read-only AutoCAD Core Console AUDIT + Xref inspection on an isolated temp copy (never mutates original DWG)."""
    import hashlib

    exe = accoreconsole_exe or detect_accoreconsole()
    if not exe or not Path(exe).is_file():
        return {
            "status": "UNAVAILABLE",
            "engine": "accoreconsole",
            "mode": "audit_only_readonly",
            "reason": "AutoCAD Core Console (accoreconsole.exe) không tìm thấy trên máy.",
        }

    src_path = Path(dwg_path).resolve()
    if not src_path.is_file():
        return {
            "status": "E001",
            "engine": "accoreconsole",
            "mode": "audit_only_readonly",
            "error": f"Không tìm thấy tệp CAD: {dwg_path}",
        }
    if src_path.suffix.lower() not in {".dwg", ".dxf"}:
        return {
            "status": "E001",
            "engine": "accoreconsole",
            "mode": "audit_only_readonly",
            "error": f"Tệp không đúng định dạng .dwg/.dxf: {dwg_path}",
        }

    source_sha256 = hashlib.sha256(src_path.read_bytes()).hexdigest()
    job_id = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=f"accore_audit_{job_id}_") as td:
        td_path = Path(td)
        # Mirror sibling 01_Xref/ folder when inspecting a Sprint 3 Workbook so relative Xrefs resolve cleanly
        sibling_xref = src_path.parent.parent / "01_Xref"
        if sibling_xref.is_dir():
            wb_dir = td_path / src_path.parent.name
            wb_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(sibling_xref), str(td_path / "01_Xref"), dirs_exist_ok=True)
            staged = wb_dir / src_path.name
            run_cwd = wb_dir
        else:
            staged = td_path / src_path.name
            run_cwd = td_path
        scr_path = td_path / "audit_readonly.scr"
        shutil.copy2(str(src_path), str(staged))
        scr_path.write_text("FILEDIA\n0\n_AUDIT\n_N\n-XREF\n?\n*\n_QUIT\n_Y\n", encoding="utf-8")

        try:
            proc = subprocess.run(
                [exe, "/i", str(staged), "/s", str(scr_path), "/l", "en-US"],
                capture_output=True,
                timeout=timeout_sec,
                cwd=str(run_cwd),
                check=False,
            )
        except Exception as exc:
            return {
                "status": "FAIL",
                "engine": "accoreconsole",
                "mode": "audit_only_readonly",
                "source_dwg": str(src_path),
                "error": str(exc),
            }

        log_text = _decode_console_output(proc.stdout)
        audit_errors: Optional[int] = None
        audit_fixes: Optional[int] = None
        m = re.search(r"Total errors found\s+(\d+)\s+fixed\s+(\d+)", log_text, re.IGNORECASE)
        if m:
            audit_errors = int(m.group(1))
            audit_fixes = int(m.group(2))
        xrefs = _parse_xref_list(log_text)

        tail_lines = [ln.strip() for ln in log_text.splitlines() if ln.strip()][-15:]
        ok = proc.returncode == 0 and m is not None
        return {
            "status": "OK" if ok else "FAIL",
            "engine": "accoreconsole",
            "mode": "audit_only_readonly",
            "accoreconsole_exe": exe,
            "source_dwg": str(src_path),
            "source_sha256": source_sha256,
            "readonly_verified": True,
            "audit_errors": audit_errors,
            "audit_fixes": audit_fixes,
            "xrefs": xrefs,
            "xref_count": len(xrefs),
            "returncode": proc.returncode,
            "log_tail": tail_lines,
        }


def attach_xrefs_via_accoreconsole(
    src_cad: str | Path,
    out_dwg: str | Path,
    xrefs: List[Dict[str, Any]],
    *,
    target_version: str = "2018",
    timeout_sec: float = 90.0,
    accoreconsole_exe: Optional[str] = None,
) -> Dict[str, Any]:
    """Bind real relative Xrefs (`Overlay`/`Attach`) onto a CAD sheet via AutoCAD 2021 Core Console."""
    import hashlib

    exe = accoreconsole_exe or detect_accoreconsole()
    if not exe or not Path(exe).is_file():
        return {
            "status": "UNAVAILABLE",
            "engine": "accoreconsole",
            "reason": "AutoCAD Core Console (accoreconsole.exe) không tìm thấy trên máy.",
        }

    src_p = Path(src_cad).resolve()
    dst_p = Path(out_dwg).resolve()
    if not src_p.is_file():
        return {"status": "E001", "engine": "accoreconsole", "error": f"Không tìm thấy tệp nguồn: {src_cad}"}
    if dst_p.exists() and not _is_temp_path(dst_p):
        return {
            "status": "DENIED",
            "engine": "accoreconsole",
            "error": f"Từ chối ghi đè DWG đã tồn tại ngoài temp (bảo vệ bất biến): {dst_p}",
        }

    job_id = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=f"accore_xref_{job_id}_") as td:
        td_path = Path(td)
        xref_dir = td_path / "01_Xref"
        wb_dir = td_path / "02_Workbook"
        xref_dir.mkdir(parents=True, exist_ok=True)
        wb_dir.mkdir(parents=True, exist_ok=True)

        staged_src = wb_dir / src_p.name
        staged_out = wb_dir / dst_p.name
        shutil.copy2(str(src_p), str(staged_src))

        scr_lines: List[str] = ["FILEDIA", "0"]
        for xr in xrefs:
            xr_src = Path(xr["src_path"]).resolve()
            if not xr_src.is_file():
                return {"status": "E001", "engine": "accoreconsole", "error": f"Không tìm thấy tệp Xref: {xr_src}"}
            shutil.copy2(str(xr_src), str(xref_dir / xr_src.name))
            rel_path = str(xr.get("rel_path") or f"..\\01_Xref\\{xr_src.name}")
            mode_opt = "_O" if str(xr.get("mode", "Overlay")).strip().lower().startswith("o") else "_A"
            ins_pt = str(xr.get("insert_pt", "0,0"))
            sc = float(xr.get("scale", 1.0))
            rot = float(xr.get("rotation", 0.0))
            layer_name = str(xr.get("layer", "")).strip()
            if layer_name:
                scr_lines.extend(["-LAYER", "_M", layer_name, ""])
            scr_lines.extend([
                "-XREF",
                mode_opt,
                f'"{rel_path}"',
                ins_pt,
                f"{sc:g}",
                f"{sc:g}",
                f"{rot:g}",
            ])

        out_forward = str(staged_out).replace("\\", "/")
        scr_lines.extend(["_AUDIT", "_Y", "_SAVEAS", str(target_version), f'"{out_forward}"', "-XREF", "?", "*", "_QUIT", "_Y", ""])
        scr_path = td_path / "bind_xrefs.scr"
        scr_path.write_text("\n".join(scr_lines), encoding="utf-8")

        try:
            proc = subprocess.run(
                [exe, "/i", str(staged_src), "/s", str(scr_path), "/l", "en-US"],
                capture_output=True,
                timeout=timeout_sec,
                cwd=str(wb_dir),
                check=False,
            )
        except Exception as exc:
            return {"status": "FAIL", "engine": "accoreconsole", "error": str(exc)}

        log_text = _decode_console_output(proc.stdout)
        if not staged_out.is_file() or staged_out.stat().st_size == 0:
            err_tail = "\n".join(ln.strip() for ln in log_text.splitlines()[-20:] if ln.strip())
            return {
                "status": "FAIL",
                "engine": "accoreconsole",
                "returncode": proc.returncode,
                "error": f"accoreconsole không xuất được Workbook DWG gắn Xref. Log: {err_tail}",
            }

        audit_errors: Optional[int] = None
        audit_fixes: Optional[int] = None
        m = re.search(r"Total errors found\s+(\d+)\s+fixed\s+(\d+)", log_text, re.IGNORECASE)
        if m:
            audit_errors = int(m.group(1))
            audit_fixes = int(m.group(2))
        parsed_xrefs = _parse_xref_list(log_text)

        dst_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(staged_out), str(dst_p))
        dwg_bytes = dst_p.read_bytes()
        return {
            "status": "OK",
            "engine": "accoreconsole",
            "target_version": target_version,
            "output_dwg": str(dst_p),
            "file_bytes": len(dwg_bytes),
            "sha256": hashlib.sha256(dwg_bytes).hexdigest(),
            "audit_errors": audit_errors,
            "audit_fixes": audit_fixes,
            "xrefs": parsed_xrefs,
            "xref_count": len(parsed_xrefs),
            "returncode": proc.returncode,
        }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="AutoCAD Core Console adapter (isolate temp DWG export & read-only AUDIT).")
    parser.add_argument("--detect", action="store_true", help="Print detected accoreconsole.exe path as JSON.")
    parser.add_argument("--audit-only", type=str, default="", help="Run read-only AutoCAD AUDIT on a .dwg/.dxf file copy in temp.")
    args = parser.parse_args()

    if args.detect:
        exe = detect_accoreconsole()
        print(json.dumps({"accoreconsole_exe": exe, "available": bool(exe)}, ensure_ascii=False))
        sys.exit(0 if exe else 1)

    if args.audit_only:
        res = audit_dwg_readonly_via_accoreconsole(args.audit_only)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res.get("status") == "OK" else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
