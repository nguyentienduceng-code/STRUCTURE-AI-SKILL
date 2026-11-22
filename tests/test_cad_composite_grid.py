# -*- coding: utf-8 -*-
"""
test_cad_composite_grid.py — Verification for Multi-Scale Composite Grid & Layer Profiles (DCE Pro v5.0)
========================================================================================================
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
SHARED_CTX = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY_DIR = AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"

for p in (str(SHARED_CTX), str(CAD_DIR), str(VERIFY_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cad_layer_standard as cls
import cad_plan_engine as cpe


class TestCadCompositeGrid(unittest.TestCase):
    def test_01_profile_selection(self):
        """Kiểm tra việc chọn đúng 3 Profile: BTCT (15), STEEL_PEB (16), BPTC (12)."""
        btct_layers = cls.select_layer_profile("BTCT")
        steel_layers = cls.select_layer_profile("STEEL_PEB")
        bptc_layers = cls.select_layer_profile("BPTC")

        self.assertEqual(len(btct_layers), 15)
        self.assertEqual(len(steel_layers), 16)
        self.assertEqual(len(bptc_layers), 12)

        # Kiểm tra layer đặc thù
        btct_names = {l[0] for l in btct_layers}
        steel_names = {l[0] for l in steel_layers}
        bptc_names = {l[0] for l in bptc_layers}

        self.assertIn("DCE_Cot", btct_names)
        self.assertIn("DCE_Thep_Chu", btct_names)

        self.assertIn("DCE_Steel_Main", steel_names)
        self.assertIn("DCE_Steel_Plate", steel_names)
        self.assertIn("DCE_Steel_Bolt", steel_names)
        self.assertIn("DCE_Steel_Weld", steel_names)

        self.assertIn("DCE_BPTC_Equip", bptc_names)
        self.assertIn("DCE_BPTC_Tie", bptc_names)
        self.assertIn("DCE_BPTC_Anchor", bptc_names)
        self.assertIn("DCE_BPTC_SafeZone", bptc_names)

    def test_02_resolve_composite_grid_layout(self):
        """Kiểm tra thuật toán phân vùng PRIMARY_ZONE (60%) và DETAIL_GRID (40%)."""
        spec = cpe.DceSheetLayoutPlanner.resolve_composite_grid(
            model_w_mm=12000.0,
            model_h_mm=8000.0,
            detail_specs=[
                {"cell_id": "CT-01", "scale": 10, "title": "CHI TIẾT ĐẦU CỘT"},
                {"cell_id": "CT-02", "scale": 15, "title": "CHI TIẾT CHÂN CỘT"},
            ],
            sheet_size="A1",
        )

        self.assertEqual(spec.layout_mode, "COMPOSITE_DETAIL_GRID")
        self.assertEqual(len(spec.detail_cells), 2)
        S_main = spec.scale

        cell_0 = spec.detail_cells[0]
        cell_1 = spec.detail_cells[1]

        self.assertEqual(cell_0.cell_id, "CT-01")
        self.assertEqual(cell_0.scale_S, 10.0)
        self.assertEqual(cell_0.scale_label, "1/10")
        self.assertEqual(cell_0.dim_style, "Dce_10MV")
        self.assertAlmostEqual(cell_0.dimlfac, 10.0 / S_main, places=3)

        self.assertEqual(cell_1.cell_id, "CT-02")
        self.assertEqual(cell_1.scale_S, 15.0)
        self.assertEqual(cell_1.scale_label, "1/15")
        self.assertEqual(cell_1.dim_style, "Dce_15MV")
        self.assertAlmostEqual(cell_1.dimlfac, 15.0 / S_main, places=3)

        # Bounding box không chồng lấn giữa 2 cell
        # Cell 0 ở trên (y lớn hơn), Cell 1 ở dưới (y nhỏ hơn)
        self.assertGreater(cell_0.bbox[1], cell_1.bbox[3] - 1.0)

        # Tất cả các cell phải nằm gọn trong inner_bbox và không đè sidebar
        in_x0, in_y0, in_x1, in_y1 = spec.inner_bbox
        for c in (cell_0, cell_1):
            cx0, cy0, cx1, cy1 = c.bbox
            self.assertGreaterEqual(cx0, in_x0)
            self.assertLessEqual(cx1, in_x1)
            self.assertGreaterEqual(cy0, in_y0)
            self.assertLessEqual(cy1, in_y1)

    def test_03_composite_grid_empty_details(self):
        """Nếu danh sách detail_specs rỗng, layout vẫn hợp lệ không lỗi."""
        spec = cpe.DceSheetLayoutPlanner.resolve_composite_grid(
            model_w_mm=10000.0,
            model_h_mm=6000.0,
            detail_specs=[],
        )
        self.assertEqual(spec.layout_mode, "COMPOSITE_DETAIL_GRID")
        self.assertEqual(len(spec.detail_cells), 0)


if __name__ == "__main__":
    unittest.main()
