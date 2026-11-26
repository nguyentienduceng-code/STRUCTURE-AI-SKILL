# -*- coding: utf-8 -*-
"""
test_cad_sprint3_xref_workbook.py — Unit tests cho Sprint 3 (3 Native Cát Lái Xrefs + `-XREF` binding + `--audit-only`).
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf

_AGENTS = Path(__file__).resolve().parents[1]
_CAD_INT = _AGENTS / "skills" / "Technical_Illustrator" / "cad_integration"
_TOOLS = _AGENTS / "tools"
for _p in (str(_CAD_INT), str(_TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from accoreconsole_adapter import (  # noqa: E402
    attach_xrefs_via_accoreconsole,
    audit_dwg_readonly_via_accoreconsole,
    convert_dxf_to_dwg_via_accoreconsole,
    detect_accoreconsole,
)
from cad_xref_workbook_builder import (  # noqa: E402
    CATLAI_X_AXES,
    CATLAI_Y_AXES,
    WORKBOOK_SPECS,
    build_catlai_xref_arch_bg_dxf,
    build_catlai_xref_grid_dxf,
    build_catlai_xref_titleblock_dxf,
)


class TestCadSprint3XrefWorkbook(unittest.TestCase):
    def test_build_3_catlai_xrefs_native(self) -> None:
        self.assertEqual(len(WORKBOOK_SPECS), 8)
        self.assertEqual([w["sheet_no"] for w in WORKBOOK_SPECS], ["KC.02", "KC.03", "KC.04", "KC.05", "KC.06", "KC.07", "KC.08", "KC.09"])

        with tempfile.TemporaryDirectory() as tmp:
            tp = Path(tmp)
            p_grid = tp / "01_XREF_GRID.dxf"
            p_arch = tp / "02_XREF_ARCH_BG.dxf"
            p_tb = tp / "03_XREF_TITLEBLOCK_A3.dxf"

            r1 = build_catlai_xref_grid_dxf(p_grid)
            r2 = build_catlai_xref_arch_bg_dxf(p_arch)
            r3 = build_catlai_xref_titleblock_dxf(p_tb)
            self.assertEqual(r1["axes_x"], len(CATLAI_X_AXES))
            self.assertEqual(r1["axes_y"], len(CATLAI_Y_AXES))
            self.assertTrue(p_grid.is_file() and p_arch.is_file() and p_tb.is_file())

            d_grid = ezdxf.readfile(str(p_grid))
            bubbles = [e for e in d_grid.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "Dce_KhTenTruc"]
            self.assertGreaterEqual(len(bubbles), 14)
            named_g = [b.name for b in d_grid.blocks if not b.name.startswith("*")]
            self.assertLessEqual(len(named_g), 35)

            d_arch = ezdxf.readfile(str(p_arch))
            ranh_pts = []
            kt_boxes = []
            for e in d_arch.modelspace():
                if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "DCE_RanhDat":
                    ranh_pts = [(round(pt[0], 1), round(pt[1], 1)) for pt in e.get_points("xy")]
                elif e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "DCE_KT":
                    kt_boxes.append([(round(pt[0], 1), round(pt[1], 1)) for pt in e.get_points("xy")])
            self.assertEqual(ranh_pts, [(0.0, 0.0), (18000.0, 0.0), (18000.0, 5000.0), (0.0, 5000.0)])
            # Xác minh không còn hình học cầu thang tự bịa (6700..10200)
            self.assertNotIn([(6700.0, 2400.0), (10200.0, 2400.0), (10200.0, 4800.0), (6700.0, 4800.0)], kt_boxes)
            self.assertIn([(14450.0, 2500.0), (16000.0, 2500.0), (16000.0, 4000.0), (14450.0, 4000.0)], kt_boxes)

            d_tb = ezdxf.readfile(str(p_tb))
            tbs = [e for e in d_tb.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "DCE_TITLEBLOCK_A3"]
            self.assertEqual(len(tbs), 1)
            att_map = {a.dxf.tag: a.dxf.text for a in tbs[0].attribs}
            self.assertEqual(att_map.get("TEN_CONG_TRINH"), "NHÀ Ở RIÊNG LẺ")
            self.assertEqual(att_map.get("DIA_DIEM"), "THỬA 1039 TỜ BẢN ĐỒ 20")
            for empty_tag in ("CHU_DAU_TU", "CONG_TY", "GIAM_DOC", "KIEM_TRA", "THIET_KE", "THE_HIEN"):
                self.assertEqual(att_map.get(empty_tag), "", f"Placeholder tag not cleared: {empty_tag}")

    def test_accoreconsole_xref_binding_and_readonly_audit(self) -> None:
        if not detect_accoreconsole():
            self.skipTest("accoreconsole.exe not installed")

        with tempfile.TemporaryDirectory() as tmp:
            tp = Path(tmp)
            xref_dir = tp / "01_Xref"
            wb_dir = tp / "02_Workbook"
            xref_dir.mkdir()
            wb_dir.mkdir()

            grid_dxf = tp / "01_XREF_GRID.dxf"
            build_catlai_xref_grid_dxf(grid_dxf)
            grid_dwg = xref_dir / "01_XREF_GRID.dwg"
            conv = convert_dxf_to_dwg_via_accoreconsole(grid_dxf, grid_dwg)
            self.assertEqual(conv["status"], "OK")

            host_dxf = tp / "host.dxf"
            hd = ezdxf.new("R2018")
            hd.modelspace().add_circle((9000.0, 2500.0), 300.0)
            hd.saveas(str(host_dxf))

            host_dwg = wb_dir / "01_KC-TEST.dwg"
            bind_res = attach_xrefs_via_accoreconsole(
                host_dxf,
                host_dwg,
                [{"src_path": str(grid_dwg), "rel_path": r"..\01_Xref\01_XREF_GRID.dwg", "mode": "Overlay", "insert_pt": "0,0", "scale": 1.0, "layer": "DCE_XREF_GRID"}],
            )
            self.assertEqual(bind_res["status"], "OK", bind_res)
            self.assertEqual(bind_res["audit_errors"], 0)
            self.assertEqual(bind_res["xref_count"], 1)
            self.assertEqual(bind_res["xrefs"][0]["path"], r"..\01_Xref\01_XREF_GRID.dwg")

            sha_before = hashlib.sha256(host_dwg.read_bytes()).hexdigest()
            aud = audit_dwg_readonly_via_accoreconsole(host_dwg)
            sha_after = hashlib.sha256(host_dwg.read_bytes()).hexdigest()
            self.assertEqual(aud["status"], "OK", aud)
            self.assertEqual(aud["audit_errors"], 0)
            self.assertEqual(aud["xref_count"], 1)
            self.assertEqual(sha_before, sha_after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
