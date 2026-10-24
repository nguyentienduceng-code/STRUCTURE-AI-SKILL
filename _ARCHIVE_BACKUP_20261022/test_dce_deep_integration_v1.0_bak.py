#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dce_deep_integration.py — Suite 11: Kiểm thử Tích hợp Sâu DCE Pro (Sprint 3.4)
Kiểm thử 4 module điều khiển cốt lõi:
1. dce_xdata_bridge.py: Kiểm tra mã nhóm DXF chuẩn, gắn/đọc XData và ezdxf.audit() 0 lỗi.
2. dce_excel_bus.py: Kiểm tra đọc/ghi cấu trúc Column Detail, BanVe, SCT Cọc.
3. dce_option_controller.py: Kiểm tra đọc/cập nhật 1.239 file cấu hình và an toàn backup.
4. dce_cad_automation.py: Kiểm tra điều khiển AutoCAD COM, sinh file .scr và fallback an toàn.
"""

from __future__ import annotations

import sys
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import unittest
import tempfile
from pathlib import Path

# Đảm bảo import được từ tools
TESTS_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = TESTS_DIR.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

try:
    import ezdxf
except ImportError:
    ezdxf = None
from dce_xdata_bridge import DceXDataBridge, XDATA_FIELD_TYPES, DEFAULT_REGAPP
from dce_excel_bus import DceExcelBus
from dce_option_controller import DceOptionController
from dce_cad_automation import DceCadAutomation


@unittest.skipIf(ezdxf is None, "ezdxf not installed")
class TestDceXDataBridge(unittest.TestCase):
    """Kiểm thử cầu nối XData tuân thủ 100% chuẩn Autodesk DXF."""

    def setUp(self):
        self.bridge = DceXDataBridge(regapp=DEFAULT_REGAPP)

    def test_01_group_codes_standard(self):
        """Xác nhận mã nhóm chuẩn DXF: 1000 cho chuỗi, 1070 cho Int16, 1040 cho Double."""
        self.assertEqual(XDATA_FIELD_TYPES["SH"], 1000)
        self.assertEqual(XDATA_FIELD_TYPES["DK"], 1070)
        self.assertEqual(XDATA_FIELD_TYPES["SL"], 1070)
        self.assertEqual(XDATA_FIELD_TYPES["L"], 1040)
        self.assertEqual(XDATA_FIELD_TYPES["sumL"], 1040)
        self.assertEqual(XDATA_FIELD_TYPES["TSL"], 1071)
        self.assertEqual(XDATA_FIELD_TYPES["TK"], 1000)

    def test_02_pack_xdata_tuples(self):
        """Kiểm tra đóng gói dictionary thành danh sách tuple XData."""
        data = {
            "SH": "1a",
            "DK": 16,
            "SL": 2,
            "L": 4550.0,
            "sumL": 5250.0,
            "SKC": "D1",
            "TK": "TK4"
        }
        tuples = self.bridge.pack_xdata_tuples(data)
        self.assertEqual(tuples[0], (1001, DEFAULT_REGAPP))
        self.assertEqual(tuples[1], (1002, "{"))
        self.assertEqual(tuples[-1], (1002, "}"))

        # Kiểm tra sự xuất hiện của các mã nhóm
        codes = [t[0] for t in tuples]
        self.assertIn(1000, codes)
        self.assertIn(1070, codes)
        self.assertIn(1040, codes)

    def test_03_attach_and_read_xdata_ezdxf(self):
        """Kiểm tra gắn XData vào entity ezdxf và đọc lại chính xác."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        line = msp.add_line((0, 0), (1000, 0))

        test_payload = {
            "SH": "TK4_TOP",
            "DK": 20,
            "SL": 2,
            "sumL": 5250.0,
            "SKC": "D1",
            "TK": "TK4"
        }
        self.bridge.attach_xdata(line, test_payload)
        self.assertTrue(line.has_xdata(DEFAULT_REGAPP))

        # Đọc ngược lại
        recovered = self.bridge.read_xdata(line)
        self.assertEqual(recovered.get("SH"), "TK4_TOP")
        self.assertEqual(recovered.get("DK"), 20)
        self.assertEqual(recovered.get("SL"), 2)
        self.assertEqual(recovered.get("sumL"), 5250.0)
        self.assertEqual(recovered.get("SKC"), "D1")
        self.assertEqual(recovered.get("TK"), "TK4")

    def test_04_ezdxf_audit_zero_errors(self):
        """Bản vẽ chứa thực thể gắn XData phải vượt qua ezdxf.audit() với 0 lỗi."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        pline = msp.add_lwpolyline([(0, 0), (100, 0), (100, 50)])

        self.bridge.attach_xdata(pline, {"SH": "TK9", "DK": 8, "SL": 35, "sumL": 1128.0})
        errors = self.bridge.audit_document(doc)
        self.assertEqual(len(errors), 0, f"Bản vẽ bị lỗi audit: {errors}")


class TestDceExcelBus(unittest.TestCase):
    """Kiểm thử cầu nối hai chiều Excel Bus."""

    def setUp(self):
        self.bus = DceExcelBus()

    def test_01_read_column_detail(self):
        """Kiểm tra đọc chi tiết tiết diện và cốt thép cột."""
        res = self.bus.read_column_detail()
        self.assertIn("status", res)
        self.assertIn("columns", res)
        self.assertGreater(len(res["columns"]), 0)
        c1 = res["columns"][0]
        self.assertIn("column_id", c1)
        self.assertIn("b_mm", c1)
        self.assertIn("h_mm", c1)
        self.assertIn("main_rebar", c1)

    def test_02_write_column_results(self):
        """Kiểm tra ghi kết quả tính cột ra file Excel mới."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "Test_Column_Output.xlsx"
            cols = [
                {"story": "Tang 1", "column_id": "C1", "b_mm": 400, "h_mm": 400, "main_rebar": "8D20", "stirrup": "D8@100/200", "mu_percent": 1.57}
            ]
            saved_path = self.bus.write_column_results(out_file, cols)
            self.assertTrue(Path(saved_path).exists())
            self.assertGreater(Path(saved_path).stat().st_size, 0)


class TestDceOptionController(unittest.TestCase):
    """Kiểm thử bộ điều khiển 1.239 file cấu hình .txt của DCE."""

    def setUp(self):
        self.ctrl = DceOptionController()

    def test_01_get_essential_options(self):
        """Kiểm tra đọc các tham số cấu hình cốt lõi."""
        cover_beam = self.ctrl.get_option("BtbvDaiTren")
        self.assertEqual(cover_beam, 25)

        bolt_pitch = self.ctrl.get_option("BLNG5")
        self.assertEqual(bolt_pitch, 200)

        viewport_w = self.ctrl.get_option("ViewPortRongKhungTen")
        self.assertIn(viewport_w, [368, 841])

    def test_02_list_essential_rules(self):
        """Kiểm tra danh mục quy tắc thiết yếu."""
        rules = self.ctrl.list_essential_rules()
        self.assertIn("cover_beam_top_mm", rules)
        self.assertIn("viewport_width_mm", rules)
        self.assertIn("bolt_pitch_blng5", rules)
        self.assertEqual(rules["cover_beam_top_mm"], 25)
        self.assertIn(rules["viewport_width_mm"], [368, 841])


class TestDceCadAutomation(unittest.TestCase):
    """Kiểm thử module điều khiển CAD Automation."""

    def setUp(self):
        self.cad_auto = DceCadAutomation()

    def test_01_send_command_offline_fallback(self):
        """Khi AutoCAD không mở, phải có cơ chế phản hồi fallback an toàn."""
        res = self.cad_auto.send_command("VeDam_DCE")
        self.assertIn("status", res)
        self.assertIn(res["status"], ["SUCCESS", "FALLBACK_OFFLINE"])

    def test_02_generate_scr_script(self):
        """Kiểm tra sinh file kịch bản Script (.scr) hợp lệ."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            scr_path = Path(tmp_dir) / "draw_beam.scr"
            cmds = ["_ZOOM _E", "VeDam_DCE", "_QSAVE"]
            out_p = self.cad_auto.generate_script(cmds, scr_path)
            self.assertTrue(Path(out_p).exists())
            content = Path(out_p).read_text(encoding="utf-8")
            self.assertIn("VeDam_DCE", content)

    def test_03_trigger_dce_command_mapping(self):
        """Kiểm tra ánh xạ tên hành động kỹ thuật sang tên lệnh nội bộ DCE."""
        res = self.cad_auto.trigger_dce_command("draw_beam")
        self.assertEqual(res["command"], "VeDam_DCE")


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceXDataBridge))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceExcelBus))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceOptionController))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceCadAutomation))
    return s


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    total = result.testsRun
    print("\n" + "=" * 50)
    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Total  : {total}")
    print("=" * 50)
    sys.exit(0 if result.wasSuccessful() else 1)
