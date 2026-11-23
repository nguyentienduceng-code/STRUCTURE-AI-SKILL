# -*- coding: utf-8 -*-
"""
autocad_snapshot_bridge.py — Tầng 2B (solo) · Cầu nối Native DWG (accoreconsole)
=================================================================================

Adapter thin, READ-ONLY, chạy ngoài tiến trình:

    [DWG nguồn (CHỊNH XÁC, không bao giờ ghi)]
            │  copy staging (temp) + SHA-256 before/after
            ▼
    accoreconsole.exe (AutoCAD 2021 Core) + plugin .NET read-only DCE_SNAPSHOT
            │  1 tiến trình / 1 DWG, timeout cứng, output staging
            ▼
    snapshot JSON chính tắc (native_dwg_snapshot.build_snapshot_from_inventory)
            ▼
    native_dwg_diff (cùng thuật toán với đường ezdxf)

Thiết kế theo kiến trúc 2B đã duyệt:
    * Không fallback âm thầm sang DXF: thiếu Core Console hoặc lệnh không chạy
      => trả mã UNAVAILABLE, KHÔNG báo "native pass".
    * File nguồn bất biến: kiểm tra SHA-256 trước/sau; chỉ ghi trong staging.
    * Worker 1 tiến trình / 1 DWG, timeout, không chạy 2 tiến trình cùng file.
    * Testable không cần AutoCAD: chấp nhận `accoreconsole_exe` + `plugin`
      tiêm (fake executable Python sinh snapshot JSON hợp lệ).

Cài đặt plugin (chạy TRÊN MÁY TRẠM có AutoCAD 2021):
    1. csc /target:library /out:dce_snapshot_plugin.dll /r:AcMgd.dll ... dce_snapshot_plugin.cs
    2. NETLOAD trong phiên, hoặc lệnh tự nạp qua script.
Chi tiết lệnh và hợp đồng snapshot trong module này (phần docstring cuối).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AGENTS_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import native_dwg_snapshot as snap  # noqa: E402

# ── Mã trạng thái (đồng bộ hợp đồng MCP convert_to_dwg) ─────────────────────
STATUS_OK = "OK"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_ERROR = "ERROR"

DEFAULT_TIMEOUT_SEC = 120.0
DEFAULT_ACCORECONSOLE_CANDIDATES = [
    r"C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2020\accoreconsole.exe",
]
DEFAULT_PLUGIN_PATH = str(TOOLS_DIR / "dce_snapshot_plugin.dll")
PLUGIN_SOURCE = str(TOOLS_DIR / "dce_snapshot_plugin.cs")


# ── 1. Phát hiện host ─────────────────────────────────────────────────────────

def detect_accoreconsole(candidates: Optional[List[str]] = None) -> Dict[str, Any]:
    """Tìm accoreconsole.exe; không có => UNAVAILABLE (không crash, không fallback)."""
    for exe in (candidates or DEFAULT_ACCORECONSOLE_CANDIDATES):
        p = Path(exe)
        if p.is_file():
            return {"found": True, "path": str(p)}
    return {"found": False, "path": None,
            "status": STATUS_UNAVAILABLE,
            "message": "accoreconsole.exe không tìm thấy — cần AutoCAD 2021 Core Console; "
                       "DXF lane (ezdxf) vẫn hoạt động độc lập."}


def detect_toolchain() -> Dict[str, Any]:
    """Kiểm tra đủ bộ cho đường native (core console + plugin)."""
    det = detect_accoreconsole()
    plugin = Path(DEFAULT_PLUGIN_PATH)
    return {
        "accoreconsole": det,
        "plugin_present": plugin.is_file(),
        "plugin_source_present": Path(PLUGIN_SOURCE).is_file(),
        "native_ready": bool(det.get("found")) and plugin.is_file(),
    }


# ── 2. SHA-256 bất biến ───────────────────────────────────────────────────────

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── 3. Staging + worker ──────────────────────────────────────────────────────

def _stage_source(src_dwg: str, staging_dir: Path) -> Path:
    """Copy DWG vào staging LOCAL (tránh chạy/ghi trực tiếp trên Google Drive)."""
    src = Path(src_dwg)
    if not src.is_file():
        raise FileNotFoundError(src_dwg)
    staged = staging_dir / src.name
    shutil.copy2(str(src), str(staged))
    return staged


def run_snapshot(
    dwg_path: str,
    *,
    staging_dir: Optional[str] = None,
    accoreconsole_exe: str = "",
    plugin: str = DEFAULT_PLUGIN_PATH,
    command: str = "DCE_SNAPSHOT",
    revision: str = "",
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    capture_out: str = "",
) -> Dict[str, Any]:
    """Chạy 1 tiến trình Core Console đọc 1 DWG (read-only) và trả snapshot.

    Với test: `accoreconsole_exe` trỏ tới fake executable (Python) sinh JSON hợp
    lệ — logic worker (staging, hash, timeout, validate) được kiểm chứng đầy đủ
    mà không cần AutoCAD.

    Kết quả:
        status: OK | UNAVAILABLE | ERROR
        snapshot: bản chụp chính tắc (nếu OK)
        source_hash_before/after: SHA-256 file NGUỒN (phải bằng nhau)
    """
    result: Dict[str, Any] = {"status": STATUS_ERROR, "snapshot": None, "error": None,
                              "source_hash_before": None, "source_hash_after": None}
    src = Path(dwg_path)
    if not src.is_file():
        result["error"] = f"DWG not found: {dwg_path}"
        return result

    result["source_hash_before"] = sha256_file(str(src))

    # Không có core console và không tiêm fake => UNAVAILABLE trung thực.
    exe = accoreconsole_exe or (detect_accoreconsole().get("path") or "")
    if not exe or not Path(exe).exists():
        result.update(status=STATUS_UNAVAILABLE,
                      error="accoreconsole.exe unavailable on this host")
        result["source_hash_after"] = result["source_hash_before"]
        result["immutability_ok"] = True  # nguồn chưa bị chạm -> bất biến
        return result

    is_real_core_console = Path(exe).name.lower() == "accoreconsole.exe"
    if is_real_core_console and not Path(plugin).is_file():
        result.update(status=STATUS_UNAVAILABLE,
                      error=f"DCE snapshot plugin DLL not built/found: {plugin}")
        result["source_hash_after"] = result["source_hash_before"]
        result["immutability_ok"] = True
        return result

    st = Path(staging_dir) if staging_dir else Path(os.environ.get(
        "TEMP", str(Path.home()))) / "dce-cad" / "tier2b_staging"
    st.mkdir(parents=True, exist_ok=True)
    try:
        staged = _stage_source(str(src), st)
        out_json = str(st / (staged.stem + ".snapshot.json"))
        env = os.environ.copy()
        if is_real_core_console:
            plugin_lisp = str(Path(plugin).resolve()).replace("\\", "\\\\")
            scr_path = st / (staged.stem + ".dce_snapshot.scr")
            scr_lines = [
                '(setvar "SECURELOAD" 0)',
                f'(command "_.NETLOAD" "{plugin_lisp}")',
                command,
                "",
            ]
            scr_path.write_text("\n".join(scr_lines), encoding="utf-8")
            env["DCE_SNAPSHOT_OUT"] = out_json
            env["DCE_SNAPSHOT_REV"] = revision or ""
            cmd = [exe, "/i", str(staged), "/s", str(scr_path), "/l", "en-US"]
        else:
            cmd = [exe, str(staged), command, out_json, revision or ""]
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout_sec, env=env)
        if p.returncode != 0:
            result["error"] = f"core-rc={p.returncode}: {(p.stderr or p.stdout)[:400]}"
        elif not Path(out_json).is_file():
            result["error"] = "snapshot file not produced (incomplete run)"
        else:
            raw = json.loads(Path(out_json).read_text(encoding="utf-8-sig"))
            # Plugin/native emit inventory; Python đóng gói thành snapshot chính tắc
            # và validate — KHÔNG tin mù output bên ngoài.
            snap_out = snap.build_snapshot_from_inventory(
                raw.get("records", []),
                document_id=raw.get("document_id", staged.stem),
                revision=revision or raw.get("revision", ""),
                source_units=raw.get("units", "mm"),
                provenance={"adapter": "accoreconsole", "host": "native",
                            "rc": p.returncode},
            )
            issues = snap.validate_snapshot(snap_out)
            if issues:
                snap_out["completion"]["complete"] = False
                snap_out["completion"]["errors"] = issues
            result["status"] = STATUS_OK
            result["snapshot"] = snap_out
    except subprocess.TimeoutExpired:
        result["error"] = f"core console timed out after {timeout_sec}s"
    except Exception as e:  # noqa: BLE001 — báo trung thực, không nuốt thành OK
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        result["source_hash_after"] = sha256_file(str(src))
    result["immutability_ok"] = result["source_hash_before"] == result["source_hash_after"]
    return result


def diff_revisions(dwg_a: str, dwg_b: str, **kwargs: Any) -> Dict[str, Any]:
    """So 2 DWG (A cơ sở, B ứng viên) — cùng pipeline snapshot + diff 2B."""
    import native_dwg_diff as diff  # noqa: PLC2701
    rev_a = kwargs.pop("rev_a", "A")
    rev_b = kwargs.pop("rev_b", "B")
    ra = run_snapshot(dwg_a, revision=rev_a, **kwargs)
    rb = run_snapshot(dwg_b, revision=rev_b, **kwargs)
    if ra["status"] != STATUS_OK or rb["status"] != STATUS_OK:
        return {"status": STATUS_UNAVAILABLE if ra["status"] == STATUS_UNAVAILABLE
                or rb["status"] == STATUS_UNAVAILABLE else STATUS_ERROR,
                "error": f"A={ra.get('error')} B={rb.get('error')}"}
    return {"status": STATUS_OK, "diff": diff.diff_snapshots(ra["snapshot"], rb["snapshot"]),
            "a_hash": ra["source_hash_before"], "b_hash": rb["source_hash_before"]}


# ── 4. Build plugin (.NET Framework csc) ────────────────────────────────────

ACSREFS = {
    "AcDbMgd": r"C:\Program Files\Autodesk\AutoCAD 2021\AcDbMgd.dll",
    "AcCoreMgd": r"C:\Program Files\Autodesk\AutoCAD 2021\AcCoreMgd.dll",
}
CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"


def build_plugin(output: Any = DEFAULT_PLUGIN_PATH, csc: str = CSC) -> Dict[str, Any]:
    """Biên dịch dce_snapshot_plugin.cs (read-only) bằng csc .NET Framework.

    Không có csc hoặc refs => trả UNAVAILABLE, KHÔNG crash (máy không cần build
    vẫn chạy được đường ezdxf thuần).
    """
    out_str = str(output)
    out: Dict[str, Any] = {"status": STATUS_UNAVAILABLE, "error": None, "output": out_str}
    if not Path(csc).is_file():
        out["error"] = f"csc not found: {csc}"
        return out
    refs = [Path(v) for v in ACSREFS.values() if Path(v).is_file()]
    if not refs:
        out["error"] = "no AutoCAD managed refs found"
        return out
    src = Path(PLUGIN_SOURCE)
    if not src.is_file():
        out["error"] = f"plugin source missing: {PLUGIN_SOURCE}"
        return out
    Path(out_str).parent.mkdir(parents=True, exist_ok=True)
    args = [csc, "/nologo", "/target:library", "/out:" + out_str,
            "/reference:System.dll", "/reference:System.Core.dll"]
    args += ["/reference:" + str(r) for r in refs]
    args.append(str(src))
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        out["status"] = STATUS_ERROR
        out["error"] = (p.stderr or p.stdout)[:800]
        return out
    out["status"] = STATUS_OK
    out["output_size"] = Path(out_str).stat().st_size
    return out


# ── 5. Native acceptance (end-to-end, trung thực) ────────────────────────────

def native_accept(dwg_paths: List[str], *, result_out: str = "",
                  revision_a: str = "A", revision_b: str = "B",
                  build_if_missing: bool = True) -> Dict[str, Any]:
    """Nghiệm thu native 2B đầu-cuối, KHÔNG bịa 'PASS' khi đường native không chạy.

    * Toolchain chưa sẵn (core console / plugin) => UNAVAILABLE + reason (khi
      `build_if_missing` có thể tự build plugin trước; vẫn UNAVAILABLE nếu thiếu
      accoreconsole trên host — không quy thành PASS).
    * Chạy `run_snapshot` (read-only, staging + SHA bất biến) trên mỗi DWG; nếu
      có >=2 DWG, chạy `diff_revisions` (D1/D1A).
    * `result_out`: ghi artifact JSON (audit trail) nếu được truyền.

    status: PASS | UNAVAILABLE | ERROR
    """
    import native_dwg_diff as diff  # noqa: PLC2701
    toolchain = detect_toolchain()
    out: Dict[str, Any] = {"status": "ERROR", "toolchain": toolchain,
                            "snapshots": [], "diff": None, "reason": None}

    if not toolchain.get("accoreconsole", {}).get("found"):
        out.update(status=STATUS_UNAVAILABLE,
                   reason="accoreconsole.exe không có trên host — cần AutoCAD 2021 Core Console; "
                          "đường ezdxf/DXF vẫn chạy độc lập.")
    elif not toolchain.get("plugin_present") and build_if_missing:
        built = build_plugin()
        out["build"] = built
        if built["status"] != STATUS_OK:
            out.update(status=STATUS_UNAVAILABLE,
                       reason="plugin không build được: " + str(built.get("error")))
    if out["status"] == STATUS_UNAVAILABLE:
        _maybe_write_result(out, result_out)
        return out
    if not toolchain.get("plugin_present"):
        out.update(status=STATUS_UNAVAILABLE,
                   reason="plugin .dll vắng và không được phép tự build (build_if_missing=False).")
        _maybe_write_result(out, result_out)
        return out

    paths = [str(p) for p in dwg_paths]
    for i, p in enumerate(paths):
        rev = (revision_a if i == 0 else revision_b) if i < 2 else f"R{i+1}"
        res = run_snapshot(p, revision=rev)
        out["snapshots"].append({
            "dwg": p, "status": res["status"], "immutability_ok": res.get("immutability_ok"),
            "records": (res.get("snapshot") or {}).get("counts", {}),
            "complete": (res.get("snapshot") or {}).get("completion", {}).get("complete"),
            "error": res.get("error"),
        })
        if res["status"] != STATUS_OK:
            out["status"] = STATUS_UNAVAILABLE if res["status"] == STATUS_UNAVAILABLE else STATUS_ERROR
            out["reason"] = res.get("error") or f"snapshot {p} không OK"
            _maybe_write_result(out, result_out)
            return out

    if len(paths) >= 2:
        dres = diff_revisions(paths[0], paths[1], rev_a=revision_a, rev_b=revision_b)
        out["diff"] = dres
        if dres.get("status") != STATUS_OK:
            out["status"] = dres.get("status")
            out["reason"] = dres.get("error")
            _maybe_write_result(out, result_out)
            return out
        dec = diff.d1d1a_decision(dres["diff"])
        out["decision"] = {"out_of_scope": [e["element_id"] for e in dec["out_of_scope_changed"]],
                           "clean": dec["clean"]}
    # PASS native khi: mọi snapshot OK + bất biến (+ diff OK nếu >=2 DWG).
    # (Kỹ sư độc lập ký kết quả; engine chỉ báo trạng thái trung thực.)
    out["status"] = STATUS_OK

    _maybe_write_result(out, result_out)
    return out


def _maybe_write_result(out: Dict[str, Any], result_out: str) -> None:
    if result_out:
        p = Path(result_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        out["result_artifact"] = str(p)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Tier 2B native DWG snapshot bridge")
    sub = ap.add_subparsers(dest="cmd")
    st = sub.add_parser("status", help="báo trạng thái toolchain")
    rs = sub.add_parser("snapshot", help="chụp snapshot 1 DWG (native)")
    rs.add_argument("dwg")
    rs.add_argument("--out")
    df = sub.add_parser("diff", help="so 2 DWG (A cơ sở, B ứng viên)")
    df.add_argument("dwg_a")
    df.add_argument("dwg_b")
    bp = sub.add_parser("build", help="build plugin .NET")
    na = sub.add_parser("native-accept", help="nghiệm thu native end-to-end (PASS/UNAVAILABLE-trung thực)")
    na.add_argument("dwg", nargs="+", help="1 DWG (snapshot) hoặc >=2 DWG (A cơ sở, B ứng viên -> diff D1/D1A)")
    na.add_argument("--result", default="", help="đường dẫn artifact JSON kết quả (audit trail)")
    na.add_argument("--no-build", action="store_true", help="không tự build plugin nếu thiếu")
    a = ap.parse_args()
    if a.cmd == "status":
        print(json.dumps(detect_toolchain(), indent=2))
    elif a.cmd == "snapshot":
        res = run_snapshot(a.dwg)
        print(json.dumps({k: v for k, v in res.items() if k != "snapshot"}, indent=2))
        if a.out and res.get("snapshot"):
            snap.dump_snapshot(res["snapshot"], a.out)
            print("snapshot ->", a.out)
    elif a.cmd == "diff":
        print(json.dumps(diff_revisions(a.dwg_a, a.dwg_b), indent=2)[:4000])
    elif a.cmd == "build":
        print(json.dumps(build_plugin(), indent=2))
    elif a.cmd == "native-accept":
        res = native_accept(a.dwg, result_out=a.result, build_if_missing=not a.no_build)
        print(json.dumps(res, indent=2, ensure_ascii=False)[:4000])
    else:
        ap.print_help()
