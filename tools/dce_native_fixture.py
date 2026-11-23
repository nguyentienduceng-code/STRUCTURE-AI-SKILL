# -*- coding: utf-8 -*-
"""
dce_native_fixture.py — Tầng 2B (solo) · Fixture D1/D1A xác định cho native acceptance
======================================================================================

Mục đích (kiến trúc 2B §3): tạo một CẶP bản vẽ D1 → D1A hoàn toàn xác định để
chứng minh end-to-end "so revision native DWG", KHÔNG cần AutoCAD GUI:

    * `make_d1_d1a_pair()`: dựng 2 document ezdxf (mm) qua `ezdxf` + gắn định danh
      2A (`DCE_ELEMENT_ID`) bằng `dce_xdata_bridge.attach_element_identity`.
      Hai cấu kiện CÙNG mark "D1" (nhịp A–B và B–C), hai element_id RIÊNG
      (BEAM_AB, BEAM_BC) — đúng "bài thi D1/D1A": đổi 1 nhịp (B–C) 250×500
      -> 250×600 + đổi nhãn D1A, NHƯNG type dùng chung không được làm nhịp kia sai.

    * `to_dwg()`: DXF -> DWG qua ODA File Converter (đường đã có trong
      `mcp_dce_cad_server.convert_to_dwg`). ODA KHÔNG CÀI => trả UNAVAILABLE trung
      thực, KHÔNG bịa file DWG (nguyên tắc "native không pass giả").

Xác định: không random, không timestamp; cùng input => cùng file. Đơn vị = mm.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AGENTS_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import dce_xdata_bridge as xdata  # noqa: E402

try:
    import ezdxf  # type: ignore
    _HAVE_EZDXF = True
except ImportError:  # pragma: no cover
    ezdxf = None  # type: ignore
    _HAVE_EZDXF = False

# ODA File Converter (đường DXF->DWG) — đọc cùng nguồn sự thật với convert_to_dwg.
try:
    import mcp_dce_cad_server as _mcp  # noqa: E402
    ODA_EXE: str = str(getattr(_mcp, "ODA_EXE", ""))
except Exception:  # pragma: no cover - mcp chưa import được vẫn dùng default
    ODA_EXE = r"C:\Program Files\ODA\ODA File Converter\ODAFileConverter.exe"

# Regapp nghiệp vụ mang (mark, b_mm, h_mm) — cả 2 đường (ezdxf + native .NET)
# đọc CÙNG regapp này để MỘT thuật toán diff thấy được sự khác D1/D1A.
BEAM_REGAPP = "DCE_BEAM"

# Hai nhịp dầm cùng mark D1 (element_id RIÊNG — không tự ghép theo mark).
_BEAMS = [
    # (element_id, role, floor, mark_d1, b_mm, h_mm, x0_mm, x1_mm)
    ("BEAM_AB", "PRIMARY_GEOM", "L2", "D1", 250.0, 500.0, 0.0, 3000.0),
    ("BEAM_BC", "PRIMARY_GEOM", "L2", "D1", 250.0, 500.0, 3000.0, 6000.0),
]
# D1A: CHỈ nhịp B–C (BEAM_BC) được duyệt đổi 250×500 -> 250×600 + nhãn D1A.
_D1A_OVERRIDE = ("BEAM_BC", 600.0, "D1A")


def _beam_payload(mark: str, b_mm: float, h_mm: float) -> str:
    return f"MARK={mark};B={b_mm:.1f};H={h_mm:.1f}"


def _make_doc(override: Optional[tuple]) -> Any:
    """Dựng 1 document ezdxf (mm) gồm 2 dầm; `override` (nếu có) đổi nhịp B–C."""
    doc = ezdxf.new("R2010", setup=False)
    doc.units = 4  # mm
    msp = doc.modelspace()
    if "DCE" not in doc.layers:
        doc.layers.new("DCE")
    for eid, role, floor, mark, b_mm, h_mm, x0, x1 in _BEAMS:
        ov_h = ov_mark = None
        if override and override[0] == eid:
            _, ov_h, ov_mark = override
        h = ov_h if ov_h is not None else h_mm
        mk = ov_mark if ov_mark is not None else mark
        # Dầm = LWPOLYLINE chữ nhật (chiều cao h, chiều dày b) ở tầng L2.
        vl = msp.add_lwpolyline(
            [(x0, 0.0), (x1, 0.0), (x1, h), (x0, h)], close=True, dxfattribs={"layer": "DCE"}
        )
        # Định danh 2A (ID/ROLE/FLOOR) — khóa ghép bền.
        xdata.attach_element_identity(vl, eid, role, floor)
        # Nghiệp vụ (MARK/B/H) — đọc bởi CẢ đường ezdxf lẫn native, cùng 1 thuật toán diff.
        if BEAM_REGAPP not in doc.appids:
            doc.appids.add(BEAM_REGAPP)
        vl.set_xdata(BEAM_REGAPP, [(1000, _beam_payload(mk, b_mm, h))])
    return doc


def make_d1_d1a_pair(out_dir: str) -> Dict[str, Any]:
    """Tạo cặp D1/D1A (DXF) xác định trong `out_dir`.

    Trả về dict với đường dẫn 2 file + trạng thái. `status`:
      OK            — 2 DXF đã sinh (đủ chạy native snapshot + diff D1/D1A)
      UNAVAILABLE   — ezdxf vắng (không bịa file)
    """
    import os
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    if not _HAVE_EZDXF:
        return {"status": "UNAVAILABLE", "reason": "ezdxf not available; cannot build fixture",
                "d1_dxf": None, "d1a_dxf": None}
    d1_path = d / "TIER2B_D1.dxf"
    d1a_path = d / "TIER2B_D1A.dxf"
    _make_doc(None).saveas(str(d1_path))
    _make_doc(_D1A_OVERRIDE).saveas(str(d1a_path))
    return {"status": "OK",
            "d1_dxf": str(d1_path), "d1a_dxf": str(d1a_path),
            "da_name": "D1", "da_name_b": "D1A",
            "beams": [b[0] for b in _BEAMS]}


def to_dwg(dxf_paths: List[str], out_dir: str) -> Dict[str, Any]:
    """DXF -> DWG qua ODA File Converter. ODA vắng => UNAVAILABLE (không bịa DWG)."""
    import os, json, subprocess, shutil
    pth = Path(out_dir); pth.mkdir(parents=True, exist_ok=True)
    if not ODA_EXE or not Path(ODA_EXE).is_file():
        return {"status": "UNAVAILABLE",
                "reason": f"ODA File Converter không tìm thấy tại {ODA_EXE}",
                "suggestion": ("Cài ODA (miễn phí, Open Design Alliance) rồi set env "
                               "ODA_FILE_CONVERTER; hoặc giao file .dxf trực tiếp."),
                "dwg_paths": {p: None for p in dxf_paths}}
    out: Dict[str, Any] = {"status": "OK", "dwg_paths": {}}
    for dxf in dxf_paths:
        base = Path(dxf).stem
        conv_in = pth / f"oda_in_{base}"; conv_out = pth / f"oda_out_{base}"
        conv_in.mkdir(parents=True, exist_ok=True); conv_out.mkdir(parents=True, exist_ok=True)
        (conv_in / Path(dxf).name).write_bytes(Path(dxf).read_bytes())
        try:
            subprocess.run([ODA_EXE, str(conv_in), str(conv_out), "0", "dxf", "dwg"],
                           check=False, timeout=120, capture_output=True)
            dwgs = list(conv_out.glob("*.dwg"))
            if dwgs:
                dest = pth / f"{base}.dwg"
                shutil.copy2(str(dwgs[0]), str(dest))
                out["dwg_paths"][dxf] = str(dest)
            else:
                out["status"] = "FAIL"
                out["dwg_paths"][dxf] = None
        except Exception as e:  # noqa: BLE001
            out["status"] = "ERROR"
            out["dwg_paths"][dxf] = None
            out.setdefault("error", str(e))
        finally:
            shutil.rmtree(str(conv_in), ignore_errors=True)
            shutil.rmtree(str(conv_out), ignore_errors=True)
    return out


def main(argv: Optional[List[str]] = None) -> int:
    import argparse, json, os
    ap = argparse.ArgumentParser(description="Tier 2B D1/D1A native fixture")
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "dce-cad", "tier2b_fixture"))
    ap.add_argument("--dwg", action="store_true", help="cũng thử DXF->DWG (ODA; UNAVAILABLE nếu thiếu)")
    a = ap.parse_args(argv)
    r = make_d1_d1a_pair(a.out)
    if a.dwg and r.get("d1_dxf"):
        r["dwg"] = to_dwg([r["d1_dxf"], r["d1a_dxf"]], a.out)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get("status") in ("OK",) else 2


if __name__ == "__main__":
    sys.exit(main())
