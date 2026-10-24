#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sprint1_reporting.py — Bộ kiểm thử tự động cho Sprint 1 (ARGON SPEC v8.0)
Nâng cấp thuyết minh tính toán, phụ lục step-by-step và chuẩn hóa TCVN.
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import unittest
from pathlib import Path

# Thêm đường dẫn các skills vào sys.path
TESTS_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = TESTS_DIR.parent
SKILLS_ROOT = AGENTS_ROOT / "skills"

sys.path.insert(0, str(SKILLS_ROOT / "SKILL_PHULUC"))
sys.path.insert(0, str(SKILLS_ROOT / "Structural_Design_Engineer" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "SKILL_VERIFY" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "Design_Evaluation" / "scripts"))


class TestSprint1Reporting(unittest.TestCase):

    def test_1_1_generator_full_materials(self):
        """Test 1.1: Kiểm tra độ chính xác cơ sở dữ liệu vật liệu theo TCVN 5574:2018 Bảng 7 & 13"""
        import generator_full

        # Bê tông B30
        self.assertIn("B30", generator_full.CONCRETE_GRADES)
        b30 = generator_full.CONCRETE_GRADES["B30"]
        self.assertEqual(b30["Rbt"], 1.15, "B30 Rbt phải là 1.15 MPa theo Bảng 7 TCVN 5574:2018 (không phải 1.20)")
        self.assertEqual(b30["Rb"], 17.0, "B30 Rb phải là 17.0 MPa")

        # Cốt thép CB400-V
        self.assertIn("CB400-V", generator_full.STEEL_GRADES_RC)
        cb400 = generator_full.STEEL_GRADES_RC["CB400-V"]
        self.assertEqual(cb400["Rs"], 350, "CB400-V Rs phải là 350 MPa theo Bảng 13 TCVN 5574:2018 (không phải 340)")
        self.assertEqual(cb400["Rsc"], 350, "CB400-V Rsc phải là 350 MPa")

        # Cốt thép CB500-V
        self.assertIn("CB500-V", generator_full.STEEL_GRADES_RC)
        cb500 = generator_full.STEEL_GRADES_RC["CB500-V"]
        self.assertEqual(cb500["Rs"], 435, "CB500-V Rs phải là 435 MPa theo Bảng 13 TCVN 5574:2018")
        self.assertEqual(cb500["Rsc"], 400, "CB500-V Rsc phải là 400 MPa theo Bảng 13 TCVN 5574:2018")

        # Các cấp độ bền bổ sung
        for grade in ["B12.5", "B22.5", "B45", "B50", "B55", "B60"]:
            self.assertIn(grade, generator_full.CONCRETE_GRADES, f"Thiếu cấp độ bền bê tông bổ sung: {grade}")

        for sgrade in ["CB240-T", "CB300-T"]:
            self.assertIn(sgrade, generator_full.STEEL_GRADES_RC, f"Thiếu nhóm cốt thép bổ sung: {sgrade}")

    def test_1_2_export_calc_sheet_rendering(self):
        """Test 1.2: export_calc_sheet.py không in raw JSON, thay số đầy đủ, dynamic eta"""
        import export_calc_sheet

        mock_calc_data = {
            "Standard_Method": "TCVN 5574:2018",
            "Input": {
                "Rebar_Grade": "CB400-V",
                "Diameter_mm": 20,
                "Concrete_Grade": "B25",
                "Stress_Ratio": 1.0,
                "Alpha_alpha": 1.0
            },
            "Results": {
                "Anchorage_Length_Basic_mm": 778,
                "Anchorage_Length_Design_mm": 778,
                "Lap_Length_Design_mm": 934,
                "eta_anchorage": 0.85,
                "eta_lap": 0.92
            },
            "Calculation_Logs": [
                {
                    "Step": 1,
                    "Description": "Cường độ chịu kéo tính toán của bê tông Rbt",
                    "Formula": "Tra bảng 7 TCVN 5574:2018",
                    "Substitution": "Cấp độ bền B25 -> Rbt = 1.05 MPa",
                    "Result": "1.05 MPa",
                    "Citation": {"Standard": "TCVN 5574:2018", "Table": "Bảng 7", "Page": "32"}
                },
                {
                    "Step": 2,
                    "Description": "Cường độ bám dính tính toán R_bond",
                    "Formula": "R_bond = eta_1 * eta_2 * R_bt",
                    "Values": "2.5 * 1.0 * 1.05",  # Test fallback to Values if Substitution not present
                    "Result": "2.625 MPa",
                    "Citation": {"Standard": "TCVN 5574:2018", "Clause": "Mục 10.3.5, CT 191", "Page": "180"}
                }
            ]
        }

        md = export_calc_sheet.generate_markdown(mock_calc_data, "Kiểm tra Chiều dài Neo Cốt Thép")

        # 1. Mục 2 không được chứa raw JSON block
        self.assertNotIn("```json", md, "Mục 2 không được in raw JSON block")
        self.assertIn("Thông số kỹ thuật", md)
        self.assertIn("Giá trị", md)
        self.assertIn("Đường kính cốt thép", md)

        # 2. Mục 4 phải có thay số ở cả 2 bước (kể cả fallback Values)
        self.assertIn("- **Thay số:** `Cấp độ bền B25 -> Rbt = 1.05 MPa`", md)
        self.assertIn("- **Thay số:** `2.5 * 1.0 * 1.05`", md)
        self.assertIn("Trang 32", md)
        self.assertIn("Trang 180", md)

        # 3. Mục 5 phải quét động các chỉ số eta
        self.assertIn("0.850", md)
        self.assertIn("0.920", md)
        self.assertIn("Hệ số sử dụng (η)", md)

    def test_1_3_report_consistency_tcvn_symbols(self):
        """Test 1.3: report_consistency_check.py nhận dạng đúng các ký hiệu TCVN và dấu phẩy thập phân"""
        import report_consistency_check

        sample_text = (
            "BÁO CÁO TÍNH TOÁN KẾT CẤU:\n"
            "Bê tông: Rb = 17,0 MPa, Rbt = 1,15 MPa\n"
            "Cốt thép: Rs = 350,0 MPa, Rsw = 280,0 MPa\n"
            "Cấu tạo neo: L_an = 778,0 mm, L_lap = 934,0 mm\n"
            "Bề rộng khe nứt: a_crc = 0,25 mm, η = 0,85\n"
        )

        extracted = report_consistency_check.extract_numbers_from_text(sample_text)

        self.assertIn("Rb", extracted)
        self.assertEqual(extracted["Rb"][0], 17.0)

        self.assertIn("Rbt", extracted)
        self.assertEqual(extracted["Rbt"][0], 1.15)

        self.assertIn("Rs", extracted)
        self.assertEqual(extracted["Rs"][0], 350.0)

        self.assertIn("Rsw", extracted)
        self.assertEqual(extracted["Rsw"][0], 280.0)

        self.assertIn("L_an", extracted)
        self.assertEqual(extracted["L_an"][0], 778.0)

        self.assertIn("L_lap", extracted)
        self.assertEqual(extracted["L_lap"][0], 934.0)

        self.assertIn("a_crc", extracted)
        self.assertEqual(extracted["a_crc"][0], 0.25)

        self.assertIn("eta", extracted)
        self.assertEqual(extracted["eta"][0], 0.85)

    def test_1_4_report_dispatcher_normalization(self):
        """Test 1.4: report_dispatcher.py ánh xạ hai chiều giữa schema tiếng Anh và khóa tiếng Việt"""
        import report_dispatcher

        english_handoff = {
            "project_context": {
                "project_name": "Tòa nhà Văn phòng Thăng Long",
                "phase": "TKKT",
                "engineer": "AI Engineer"
            },
            "payload": {
                "standard": "TCVN 5574:2018",
                "calculation_logs": [
                    {"step": 1, "description": "Kiểm tra uốn", "formula": "M <= M_Rd", "result": "PASS"}
                ],
                "results": {"eta_flexure": 0.82}
            }
        }

        normalized = report_dispatcher._normalize_handoff_schema(english_handoff)

        self.assertEqual(normalized["Ten_Du_An"], "Tòa nhà Văn phòng Thăng Long")
        self.assertEqual(normalized["Giai_Doan_TK"], "TKKT")
        self.assertEqual(len(normalized["Calculation_Logs"]), 1)
        self.assertEqual(normalized["Calculation_Logs"][0]["step"], 1)
        self.assertEqual(normalized["Tieu_Chuan"], "TCVN 5574:2018")


if __name__ == "__main__":
    unittest.main()
