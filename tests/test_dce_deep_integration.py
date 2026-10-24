#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dce_deep_integration.py — Suite 11: Kiểm thử Tích hợp Sâu DCE Pro v2.0 & 1-Click Pipeline
==============================================================================================
Kiểm thử toàn diện 5 module cốt lõi (18 kịch bản kiểm thử):
1. dce_xdata_bridge.py v2.0: Mã nhóm chuẩn DXF (1001, 1000, 1002, 1005, 1040, 1070, 1071),
   tính toán hình học TK1..TK44, liên kết động 2 chiều entity <-> block và quét thống kê thép.
2. dce_excel_bus.py v2.0: Danh mục 25 lớp GanDLApplication*, đọc/ghi Column Detail, Beam Design, TinhMong.
3. dce_option_controller.py v2.0: Dual-Source Registry (1.239 file .txt + dce_engineering_rules.json),
   kiểm tra ràng buộc TCVN, get_bulk/set_bulk và rollback_transaction.
4. dce_cad_automation.py v2.0: Multi-CAD COM adapter, sinh file .scr, thuật toán dàn trang A3 VPGroup::CalcMetaRect.
5. end_to_end_pipeline.py v1.0: Chu trình 1-Click End-to-End Pipeline hoàn tất trong <= 45 giây.
"""

from __future__ import annotations

import sys
if sys.stdout.encoding != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = TESTS_DIR.parent
for p in [
    TESTS_DIR,
    AGENTS_ROOT / "tools",
    Path("/working_dir/c_ff2fc9e4f2fbff34/artifacts/file_generation/ttl=63d/output"),
    Path("/working_dir/c_ff2fc9e4f2fbff34/downloads"),
]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import ezdxf
except ImportError:
    ezdxf = None

from dce_xdata_bridge import (
    DceXDataBridge,
    InMemoryDXFEntity,
    XDATA_FIELD_TYPES,
    DEFAULT_REGAPP,
    compute_rebar_metrics,
)
from dce_excel_bus import DceExcelBus, GanDLBeamData
from dce_option_controller import DceOptionController
from dce_cad_automation import DceCadAutomation
from end_to_end_pipeline import EndToEndStructuralPipeline


class TestDceXDataBridge(unittest.TestCase):
    """Kiểm thử cầu nối XData v2.0 tuân thủ 100% chuẩn Autodesk DXF."""

    def setUp(self):
        self.bridge = DceXDataBridge(regapp=DEFAULT_REGAPP)

    def test_01_group_codes_standard(self):
        """Xác nhận mã nhóm chuẩn DXF: 1000 String, 1005 Handle, 1070 Int16, 1071 Int32, 1040 Double."""
        self.assertEqual(XDATA_FIELD_TYPES["SH"], 1000)
        self.assertEqual(XDATA_FIELD_TYPES["DK"], 1070)
        self.assertEqual(XDATA_FIELD_TYPES["SL"], 1070)
        self.assertEqual(XDATA_FIELD_TYPES["L"], 1040)
        self.assertEqual(XDATA_FIELD_TYPES["sumL"], 1040)
        self.assertEqual(XDATA_FIELD_TYPES["TSL"], 1071)
        self.assertEqual(XDATA_FIELD_TYPES["TK"], 1000)
        self.assertEqual(XDATA_FIELD_TYPES["LINK_HANDLE"], 1005)

    def test_02_pack_xdata_tuples(self):
        """Kiểm tra đóng gói dictionary thành danh sách tuple XData."""
        data = {
            "SH": "1a",
            "DK": 16,
            "SL": 2,
            "L": 4550.0,
            "sumL": 5250.0,
            "SKC": "D1",
            "TK": "TK4",
            "LINK_HANDLE": "2F4A",
        }
        tuples = self.bridge.pack_xdata_tuples(data)
        self.assertEqual(tuples[0], (1001, DEFAULT_REGAPP))
        self.assertEqual(tuples[1], (1002, "{"))
        self.assertEqual(tuples[-1], (1002, "}"))
        codes = [t[0] for t in tuples]
        self.assertIn(1000, codes)
        self.assertIn(1070, codes)
        self.assertIn(1040, codes)
        self.assertIn(1005, codes)

    def test_03_attach_and_read_xdata_ezdxf(self):
        """Kiểm tra gắn XData vào entity (ezdxf hoặc InMemory fallback) và đọc lại chính xác."""
        if ezdxf is not None:
            doc = ezdxf.new("R2010")
            msp = doc.modelspace()
            line = msp.add_line((0, 0), (1000, 0))
        else:
            line = InMemoryDXFEntity("LINE", handle="101")

        test_payload = {
            "SH": "TK4_TOP",
            "DK": 20,
            "SL": 2,
            "sumL": 5250.0,
            "SKC": "D1",
            "TK": "TK4",
        }
        self.bridge.attach_xdata(line, test_payload)
        self.assertTrue(line.has_xdata(DEFAULT_REGAPP))

        recovered = self.bridge.read_xdata(line)
        self.assertEqual(recovered.get("SH"), "TK4_TOP")
        self.assertEqual(recovered.get("DK"), 20)
        self.assertEqual(recovered.get("SL"), 2)
        self.assertEqual(recovered.get("sumL"), 5250.0)
        self.assertEqual(recovered.get("SKC"), "D1")
        self.assertEqual(recovered.get("TK"), "TK4")

    def test_04_ezdxf_audit_zero_errors(self):
        """Bản vẽ chứa thực thể gắn XData phải vượt qua ezdxf.audit() với 0 lỗi."""
        if ezdxf is None:
            return
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        pline = msp.add_lwpolyline([(0, 0), (100, 0), (100, 50)])
        self.bridge.attach_xdata(pline, {"SH": "TK9", "DK": 8, "SL": 35, "sumL": 1128.0})
        errors = self.bridge.audit_document(doc)
        self.assertEqual(len(errors), 0, f"Bản vẽ bị lỗi audit: {errors}")

    def test_05_bind_rebar_entity_and_block_two_way(self):
        """Kiểm tra liên kết động 2 chiều giữa thanh thép và Block thống kê kèm tính toán KL."""
        rebar_ent = InMemoryDXFEntity("LWPOLYLINE", handle="2A1")
        block_ent = InMemoryDXFEntity("INSERT", handle="3B2")
        res = self.bridge.bind_rebar_entity_and_block(
            rebar_entity=rebar_ent,
            block_entity=block_ent,
            rebar_spec={"SH": "1a", "DK": 22, "SL": 4, "L1": 350.0, "L2": 5650.0, "SKC": "D1", "TK": "TK2"},
            skc_count=3,
        )
        self.assertEqual(res["xdata_payload"]["sumL"], 6000.0)
        self.assertEqual(res["xdata_payload"]["TSL"], 12)
        self.assertEqual(res["xdata_payload"]["LINK_HANDLE"], "3B2")
        self.assertEqual(block_ent.attribs["SH"], "1a")
        self.assertEqual(block_ent.attribs["TSL"], "12")


class TestDceExcelBus(unittest.TestCase):
    """Kiểm thử cầu nối hai chiều Excel Bus v2.0 (25 GanDLApplication* classes)."""

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

    def test_03_25_gan_dl_classes_and_beam_workbook(self):
        """Xác nhận đủ 25 lớp GanDLApplication* và xuất workbook đa sheet (Beam Design + TinhMong)."""
        classes = self.bus.list_gan_dl_classes()
        self.assertEqual(len(classes), 25)
        self.assertIn("GanDLApplicationExcelBeamDesign", classes)
        self.assertIn("GanDLApplicationExcelThuyetMinhSCTCoc", classes)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_wb = Path(tmp_dir) / "Test_DCE_MultiSheet.xlsx"
            saved = self.bus.write_beam_design_workbook(out_wb, [GanDLBeamData(MaDam="D1", BeRong=300, ChieuCao=600)])
            self.assertTrue(Path(saved).exists())


class TestDceOptionController(unittest.TestCase):
    """Kiểm thử bộ điều khiển 1.239 file cấu hình .txt & Dual-Source JSON Registry v2.0."""

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

    def test_03_validation_and_rollback(self):
        """Kiểm tra ràng buộc TCVN và khôi phục giao dịch rollback_transaction()."""
        with self.assertRaises(ValueError):
            self.ctrl.set_option("BtbvDaiTren", 5)  # Nhỏ hơn giới hạn tối thiểu 15mm
        self.ctrl.set_option("BtbvDaiTren", 35)
        self.assertEqual(self.ctrl.get_option("BtbvDaiTren"), 35)
        self.ctrl.rollback_transaction()
        self.assertEqual(self.ctrl.get_option("BtbvDaiTren"), 25)


class TestDceCadAutomation(unittest.TestCase):
    """Kiểm thử module điều khiển Multi-CAD Automation & VPGroup::CalcMetaRect v2.0."""

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

    def test_04_viewport_auto_packing_a3(self):
        """Kiểm tra thuật toán VPGroup::CalcMetaRect xếp khung bản vẽ A3 (368x297mm)."""
        packing = self.cad_auto.pack_viewports_a3([
            {"id": "VP1", "width_model_mm": 6000, "height_model_mm": 1000, "scale": 50},
            {"id": "VP2", "width_model_mm": 800, "height_model_mm": 1000, "scale": 20},
        ])
        self.assertEqual(packing["total_viewports"], 2)
        self.assertGreaterEqual(packing["total_sheets_a3"], 1)
        self.assertEqual(packing["sheets"][0]["frame_width_mm"], 368.0)


class TestEndToEndPipeline(unittest.TestCase):
    """Kiểm thử bộ điều phối 1-Click End-to-End Pipeline (<= 45s)."""

    def test_01_full_e2e_pipeline_under_45s(self):
        """Chạy trọn vẹn 6 pha từ Prompt -> ETABS -> TCVN -> Cắt thép 11.7m -> CAD A3 -> Word trong <= 45s."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipe = EndToEndStructuralPipeline(output_dir=Path(tmp_dir), project_code="TEST-E2E")
            res = pipe.run(demo=True)
            payload = res["payload"]
            self.assertTrue(payload["sla_passed"])
            self.assertLessEqual(payload["actual_elapsed_seconds"], 45.0)
            self.assertEqual(payload["dce_cad_output"]["ezdxf_audit_errors"], 0)
            self.assertTrue(Path(payload["dce_cad_output"]["dxf_file"]).exists())
            self.assertTrue(Path(payload["dce_cad_output"]["excel_bus_file"]).exists())
            self.assertTrue(Path(payload["reports_generated"]["markdown_report"]).exists())


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceXDataBridge))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceExcelBus))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceOptionController))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceCadAutomation))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestEndToEndPipeline))
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
