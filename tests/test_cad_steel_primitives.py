# -*- coding: utf-8 -*-
"""
test_cad_steel_primitives.py — Unit Tests for Parametric Steel Primitives (DCE Pro v5.0)
========================================================================================
"""

from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
SHARED_CTX = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"

for p in (str(SHARED_CTX), str(CAD_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
import cad_steel_primitives as csp


class TestCadSteelPrimitives(unittest.TestCase):
    def setUp(self):
        self.doc = ezdxf.new("AC1021")
        self.msp = self.doc.modelspace()

    def test_01_profile_parser(self):
        """Kiểm tra parser các loại tiết diện thép chuẩn."""
        p_h = csp.parse_steel_profile("H200x200x8x12")
        self.assertEqual(p_h["type"], "H")
        self.assertEqual(p_h["H"], 200.0)
        self.assertEqual(p_h["B"], 200.0)
        self.assertAlmostEqual(p_h["weight_kgm"], 49.9, places=0)

        p_u = csp.parse_steel_profile("U200x73x7")
        self.assertEqual(p_u["type"], "U")
        self.assertEqual(p_u["H"], 200.0)

        p_box = csp.parse_steel_profile("BOX_150x150x5")
        self.assertEqual(p_box["type"], "BOX")
        self.assertAlmostEqual(p_box["weight_kgm"], 22.4, places=1)

        p_pl = csp.parse_steel_profile("PL20x400x500")
        self.assertEqual(p_pl["type"], "PLATE")
        self.assertAlmostEqual(p_pl["total_weight_kg"], 31.4, places=1)

    def test_02_draw_rolled_section(self):
        """Kiểm tra vẽ mặt cắt và hình chiếu dầm H."""
        res_sec = csp.draw_rolled_section(self.msp, "H200x200x8x12", origin=(1000, 1000), view_mode="SECTION")
        self.assertGreater(len(res_sec["entities"]), 0)
        self.assertEqual(res_sec["view_mode"], "SECTION")
        self.assertGreater(res_sec["weight_kg"], 0.0)

        res_elev = csp.draw_rolled_section(self.msp, "H200x200x8x12", origin=(0, 0), length_mm=6000.0, view_mode="ELEVATION")
        self.assertGreater(len(res_elev["entities"]), 0)
        self.assertAlmostEqual(res_elev["weight_kg"], 49.9 * 6.0, delta=10.0)

    def test_03_draw_tapered_member(self):
        """Kiểm tra vẽ cấu kiện vát tiết diện (Cột/kèo PEB)."""
        res = csp.draw_tapered_member(
            self.msp,
            p_start=(0, 0),
            p_end=(0, 6000),
            h_start=300.0,
            h_end=600.0,
            tf=12.0,
            tw=8.0,
            bf=200.0,
        )
        self.assertGreater(len(res["entities"]), 0)
        self.assertEqual(res["length_mm"], 6000.0)
        self.assertGreater(res["weight_kg"], 100.0)

    def test_04_draw_gusset_plate(self):
        """Kiểm tra vẽ bản mã ngũ giác và tính diện tích Shoelace."""
        pts = [(0, 0), (500, 0), (500, 300), (300, 450), (0, 450)]
        res = csp.draw_gusset_plate(self.msp, pts, thickness_mm=20.0, mark="BM-01")
        self.assertGreater(len(res["entities"]), 0)
        self.assertEqual(res["thickness_mm"], 20.0)
        self.assertGreater(res["area_mm2"], 150000.0)
        self.assertGreater(res["weight_kg"], 20.0)

    def test_05_draw_bolt_array_and_tcvn_check(self):
        """Kiểm tra lưới bu lông và cảnh báo TCVN 5575:2024."""
        # Trường hợp PASS: M24 (d0=27mm), p1=100 >= 67.5, p2=100 >= 67.5
        res_pass = csp.draw_bolt_array(
            self.msp,
            origin=(1000, 1000),
            rows=3,
            cols=2,
            p1=100.0,
            p2=100.0,
            d_bolt=24.0,
            plate_bbox=(850, 850, 1150, 1150),
        )
        self.assertEqual(res_pass["bolt_count"], 6)
        self.assertTrue(res_pass["tcvn_check"]["pass"])

        # Trường hợp VIOLATION: bước quá sát (p=40 < 2.5*27=67.5)
        res_fail = csp.draw_bolt_array(
            self.msp,
            origin=(0, 0),
            rows=2,
            cols=2,
            p1=40.0,
            p2=40.0,
            d_bolt=24.0,
        )
        self.assertFalse(res_fail["tcvn_check"]["pass"])
        self.assertGreater(len(res_fail["tcvn_check"]["warnings"]), 0)

    def test_06_draw_weld_symbol_tcvn(self):
        """Kiểm tra vẽ ký hiệu đường hàn TCVN."""
        res = csp.draw_weld_symbol_tcvn(
            self.msp,
            target_pt=(500, 500),
            leg_hf_mm=8.0,
            length_lw_mm=320.0,
            both_sides=True,
        )
        self.assertGreater(len(res["entities"]), 0)
        self.assertEqual(res["hf_mm"], 8.0)
        self.assertEqual(res["lw_mm"], 320.0)

    def test_07_compute_steel_bom(self):
        """Kiểm tra tổng hợp Bảng thống kê thép (BOM)."""
        items = [
            {"mark": "K-01", "section": "H300x300x10x15", "steel_grade": "SS400", "qty": 4, "length_mm": 6000},
            {"mark": "BM-01", "spec": "PL20x400x500", "steel_grade": "SS400", "qty": 8, "total_weight_kg": 31.4 * 8},
        ]
        bom = csp.compute_steel_bom(items)
        self.assertEqual(bom["total_items"], 2)
        self.assertGreater(bom["total_weight_kg"], 1000.0)
        self.assertEqual(len(bom["headers"]), 9)

    def test_08_paired_profile_and_fallback_warning(self):
        """Kiểm tra tiết diện ghép đôi 2U/2L và cảnh báo fallback khi không nhận dạng (K4)."""
        p_u = csp.parse_steel_profile("U200x73x7")
        p_2u = csp.parse_steel_profile("2U200x73x7")
        self.assertTrue(p_2u.get("paired"))
        self.assertEqual(p_2u["type"], "U")
        self.assertAlmostEqual(p_2u["weight_kgm"], round(p_u["weight_kgm"] * 2.0, 2), places=1)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            p_unk = csp.parse_steel_profile("UNKNOWN_XYZ")
        self.assertTrue(any(issubclass(w.category, UserWarning) for w in caught))
        self.assertTrue(p_unk.get("fallback_warning"))
        self.assertIn("Data Missing", str(caught[0].message))
        with self.assertRaises(ValueError):
            csp.parse_steel_profile("UNKNOWN_XYZ", strict=True)

    def test_09_weld_symbol_full_length_label(self):
        """Kiểm tra nhãn 'lw toàn bộ' khi chiều dài mối hàn lw <= 0 (K5)."""
        res = csp.draw_weld_symbol_tcvn(
            self.msp,
            target_pt=(200, 200),
            leg_hf_mm=6.0,
            length_lw_mm=0.0,
        )
        self.assertIn("lw toàn bộ", res.get("label", ""))
        texts = [e.dxf.text for e in res["entities"] if e.dxftype() == "TEXT"]
        self.assertTrue(any("lw toàn bộ" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
