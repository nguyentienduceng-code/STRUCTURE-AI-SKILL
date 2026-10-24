"""
test_suite12_doc_intelligence.py
=================================
Sprint 4 · Suite 12 — Document Intelligence & Conflict Detection

Kiểm thử tự động cho 5 tool mới:
  • doc_reader.py             — đọc hồ sơ kỹ thuật (+ OCR)
  • conflict_analyzer.py     — phát hiện xung đột chéo
  • version_differ.py        — so sánh phiên bản
  • rebar_provided_checker.py — As_req vs As_prov
  • report_pipeline.py       — pipeline đầu cuối

Mục tiêu: ≥ 60 checks, 0 failures.
"""

import sys
import os
import json
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm thư mục tools vào path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# ─────────────────────────────────────────────────────────────────────────────
# Import modules under test
# ─────────────────────────────────────────────────────────────────────────────

import doc_reader as dr
import conflict_analyzer as ca
import version_differ as vd
import rebar_provided_checker as rc
import report_pipeline as rp


# ─────────────────────────────────────────────────────────────────────────────
# Suite A: doc_reader — core functions
# ─────────────────────────────────────────────────────────────────────────────

class TestDocReaderPatterns(unittest.TestCase):
    """A: Pattern extraction từ raw text."""

    def test_A01_load_pattern_kn_m2(self):
        """Extract tải kN/m² từ text."""
        text = "Tĩnh tải sàn: 3.5 kN/m²"
        eng, _ = dr._extract_engineering_data(text)
        self.assertTrue(len(eng["loads"]) >= 1, "Phải nhận dạng được tải trọng")

    def test_A02_load_value_correct(self):
        """Giá trị tải trọng extract đúng."""
        text = "Hoạt tải văn phòng = 5.0 kN/m²"
        eng, _ = dr._extract_engineering_data(text)
        values = [l["value"] for l in eng["loads"]]
        self.assertIn(5.0, values, "Giá trị 5.0 phải được extract")

    def test_A03_section_pattern_bxh(self):
        """Extract tiết diện BxH."""
        text = "Dầm D1 tiết diện 300x600mm"
        eng, _ = dr._extract_engineering_data(text)
        self.assertTrue(len(eng["sections"]) >= 1, "Phải nhận dạng tiết diện")

    def test_A04_section_dimensions(self):
        """Giá trị B và H đúng."""
        text = "Cột C1: 400x400"
        eng, _ = dr._extract_engineering_data(text)
        secs = eng["sections"]
        self.assertTrue(any(s["b_mm"] == 400 and s["h_mm"] == 400 for s in secs),
                        "Phải extract b=400, h=400")

    def test_A05_rebar_pattern(self):
        """Extract cốt thép 4Ø25."""
        text = "Cốt thép chịu kéo: 4Ø25"
        eng, _ = dr._extract_engineering_data(text)
        self.assertTrue(len(eng["rebar_schedule"]) >= 1, "Phải nhận dạng cốt thép")

    def test_A06_rebar_diameter(self):
        """Đường kính cốt thép đúng."""
        text = "6φ20 thép chịu uốn"
        eng, _ = dr._extract_engineering_data(text)
        dias = [r["dia_mm"] for r in eng["rebar_schedule"]]
        self.assertIn(20.0, dias)

    def test_A07_material_concrete(self):
        """Nhận dạng grade bê tông B30."""
        text = "Bê tông B30, thép CB400V"
        eng, _ = dr._extract_engineering_data(text)
        grades = [m["grade"] for m in eng["materials"]]
        self.assertIn("B30", grades)

    def test_A08_material_steel(self):
        """Nhận dạng grade thép CB400V."""
        text = "Sử dụng thép CB400V theo TCVN"
        eng, _ = dr._extract_engineering_data(text)
        grades = [m["grade"] for m in eng["materials"]]
        self.assertIn("CB400V", grades)

    def test_A09_spt_pattern(self):
        """Nhận dạng chỉ số SPT."""
        text = "Lớp 1: N = 8 búa (sét dẻo mềm)"
        eng, _ = dr._extract_engineering_data(text)
        self.assertTrue(len(eng["soil_params"]) >= 1, "Phải nhận dạng SPT")

    def test_A10_spt_value(self):
        """Giá trị SPT đúng."""
        text = "NSPT = 15 búa lớp cát trung"
        eng, _ = dr._extract_engineering_data(text)
        spts = [s["SPT_N"] for s in eng["soil_params"]]
        self.assertIn(15.0, spts)

    def test_A11_confidence_high(self):
        """Confidence HIGH khi đủ data."""
        result = dr._demo_result()
        conf = dr._compute_confidence(result)
        self.assertEqual(conf, "HIGH", "Demo result phải cho confidence HIGH")

    def test_A12_demo_mode_complete(self):
        """Demo mode trả về cấu trúc đầy đủ."""
        result = dr._demo_result()
        required_keys = ["source_file", "source_type", "engineering_data",
                         "confidence_level", "Calculation_Logs", "Standard_Method"]
        for key in required_keys:
            self.assertIn(key, result, f"Thiếu key: {key}")

    def test_A13_demo_loads_not_empty(self):
        """Demo có dữ liệu tải trọng."""
        result = dr._demo_result()
        loads = result["engineering_data"]["loads"]
        self.assertGreater(len(loads), 0, "Demo phải có tải trọng")

    def test_A14_demo_sections_not_empty(self):
        """Demo có dữ liệu tiết diện."""
        result = dr._demo_result()
        secs = result["engineering_data"]["sections"]
        self.assertGreater(len(secs), 0, "Demo phải có tiết diện")

    def test_A15_unsupported_format_error(self):
        """Định dạng không hỗ trợ → error result có cấu trúc đúng."""
        result = dr._error_result("test.xyz", "XYZ", "Không hỗ trợ", [])
        self.assertIn("error", result)
        self.assertEqual(result["confidence_level"], "LOW")

    def test_A16_rebar_column_detect(self):
        """Nhận dạng cột header bảng thống kê thép."""
        header = ["Ký hiệu", "Đường kính (mm)", "Số lượng", "Chiều dài (mm)"]
        col_map = dr._detect_rebar_columns(header)
        self.assertIn("mark", col_map)
        self.assertIn("dia", col_map)
        self.assertIn("count", col_map)
        self.assertIn("length", col_map)


# ─────────────────────────────────────────────────────────────────────────────
# Suite B: conflict_analyzer
# ─────────────────────────────────────────────────────────────────────────────

class TestConflictAnalyzer(unittest.TestCase):
    """B: Phát hiện xung đột chéo."""

    def setUp(self):
        self.demo_docs = ca._demo_docs()

    def test_B01_demo_returns_dict(self):
        """Demo mode chạy thành công."""
        result = ca.analyze_conflicts(self.demo_docs)
        self.assertIsInstance(result, dict)

    def test_B02_has_required_keys(self):
        """Kết quả có đủ các key bắt buộc."""
        result = ca.analyze_conflicts(self.demo_docs)
        for key in ["conflict_summary", "conflicts", "passes", "overall_assessment"]:
            self.assertIn(key, result, f"Thiếu key: {key}")

    def test_B03_load_mismatch_detected(self):
        """C01: Phát hiện chênh lệch tải trọng > 5%."""
        # doc_a tĩnh tải 3.5 kN/m², doc_b là 4.5 kN/m² → delta 28.6%
        result = ca.analyze_conflicts(self.demo_docs, threshold_pct=5.0)
        c01_conflicts = [c for c in result["conflicts"] if c["type"] == "LOAD_MISMATCH"]
        self.assertGreater(len(c01_conflicts), 0, "Phải phát hiện ít nhất 1 LOAD_MISMATCH")

    def test_B04_load_mismatch_severity(self):
        """C01: Severity đúng khi delta > 20%."""
        result = ca.analyze_conflicts(self.demo_docs, threshold_pct=5.0)
        c01 = [c for c in result["conflicts"] if c["type"] == "LOAD_MISMATCH"]
        severities = [c["severity"] for c in c01]
        self.assertIn("CRITICAL", severities, "Delta 28.6% phải là CRITICAL")

    def test_B05_section_mismatch_detected(self):
        """C02: Phát hiện tiết diện khác nhau."""
        result = ca.analyze_conflicts(self.demo_docs)
        c02 = [c for c in result["conflicts"] if c["type"] == "SECTION_MISMATCH"]
        self.assertGreater(len(c02), 0, "Phải phát hiện SECTION_MISMATCH")

    def test_B06_material_mismatch_detected(self):
        """C03: Phát hiện grade bê tông khác nhau."""
        result = ca.analyze_conflicts(self.demo_docs)
        c03 = [c for c in result["conflicts"] if c["type"] == "MATERIAL_MISMATCH"]
        self.assertGreater(len(c03), 0, "Phải phát hiện MATERIAL_MISMATCH")

    def test_B07_tcvn_violation_detected(self):
        """C05: Phát hiện η > 1.0."""
        doc_with_eta = {
            "source_file": "test_eta.json",
            "raw_text_preview": "Kiểm tra uốn: η = 1.05 > 1.0 — không đạt",
            "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[]},
        }
        result = ca.analyze_conflicts([doc_with_eta])
        c05 = [c for c in result["conflicts"] if c["type"] == "TCVN_VIOLATION"]
        self.assertGreater(len(c05), 0, "Phải phát hiện TCVN_VIOLATION khi η=1.05")

    def test_B08_tcvn_violation_critical(self):
        """C05: η > 1.0 → severity CRITICAL."""
        doc = {
            "source_file": "eta_test.json",
            "raw_text_preview": "η = 1.15",
            "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[]},
        }
        result = ca.analyze_conflicts([doc])
        c05 = [c for c in result["conflicts"] if c["type"] == "TCVN_VIOLATION"]
        if c05:
            self.assertEqual(c05[0]["severity"], "CRITICAL")

    def test_B09_eta_ok_no_violation(self):
        """C05: η = 0.75 → PASS, không conflict."""
        doc = {
            "source_file": "eta_ok.json",
            "raw_text_preview": "Kết quả: η = 0.75 — đạt yêu cầu",
            "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[]},
        }
        result = ca.analyze_conflicts([doc], checks=["C05"])
        c05_violations = [c for c in result["conflicts"] if c["type"] == "TCVN_VIOLATION"]
        self.assertEqual(len(c05_violations), 0, "η=0.75 không phải vi phạm")

    def test_B10_geotech_weak_soil_warning(self):
        """C04: SPT < 5 → CRITICAL conflict."""
        doc_geo = {
            "source_file": "DCCT.json",
            "raw_text_preview": "",
            "engineering_data": {
                "loads":[], "sections":[], "materials":[], "rebar_schedule":[],
                "soil_params": [{"SPT_N": 3.0}, {"SPT_N": 4.0}],
            },
        }
        doc_design = {
            "source_file": "ThietKe.json",
            "raw_text_preview": "",
            "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[]},
        }
        result = ca.analyze_conflicts([doc_geo, doc_design], checks=["C04"])
        c04 = [c for c in result["conflicts"] if c["type"] == "GEOTECH_MISMATCH"]
        self.assertGreater(len(c04), 0, "SPT_avg=3.5 phải trigger GEOTECH_MISMATCH")

    def test_B11_threshold_respected(self):
        """Threshold 0% → mọi chênh lệch đều là conflict."""
        result = ca.analyze_conflicts(self.demo_docs, threshold_pct=0.0)
        c01 = [c for c in result["conflicts"] if c["type"] == "LOAD_MISMATCH"]
        self.assertGreater(len(c01), 0)

    def test_B12_conflict_has_recommendation(self):
        """Mọi conflict phải có trường recommendation."""
        result = ca.analyze_conflicts(self.demo_docs)
        for cf in result["conflicts"]:
            self.assertIn("recommendation", cf, f"Thiếu recommendation ở {cf['id']}")
            self.assertTrue(len(cf["recommendation"]) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# Suite C: version_differ
# ─────────────────────────────────────────────────────────────────────────────

class TestVersionDiffer(unittest.TestCase):
    """C: So sánh phiên bản hồ sơ."""

    def setUp(self):
        self.rev_a, self.rev_b = vd._demo_docs()

    def test_C01_demo_returns_dict(self):
        """Demo diff chạy thành công."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        self.assertIsInstance(result, dict)

    def test_C02_has_required_keys(self):
        """Kết quả có đủ key."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        for key in ["change_summary", "changes", "unchanged", "overall_assessment"]:
            self.assertIn(key, result, f"Thiếu key: {key}")

    def test_C03_major_changes_detected(self):
        """Phát hiện thay đổi MAJOR (tiết diện, tải trọng)."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        self.assertGreater(result["change_summary"]["MAJOR"], 0,
                           "Phải phát hiện thay đổi MAJOR")

    def test_C04_added_element_detected(self):
        """Phát hiện cấu kiện ADDED (Dầm D3 mới)."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        self.assertGreater(result["change_summary"]["ADDED"], 0,
                           "Phải phát hiện Dầm D3 được thêm vào")

    def test_C05_removed_element_detected(self):
        """Phát hiện cấu kiện REMOVED (Dầm D2 bị xóa)."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        self.assertGreater(result["change_summary"]["REMOVED"], 0,
                           "Phải phát hiện Dầm D2 bị xóa")

    def test_C06_load_change_is_major(self):
        """Tải trọng thay đổi → MAJOR."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        load_changes = [c for c in result["changes"] if "loads" in c["field"]]
        major_load = [c for c in load_changes if c["category"] == "MAJOR"]
        self.assertGreater(len(major_load), 0, "Thay đổi tải trọng phải là MAJOR")

    def test_C07_material_change_is_major(self):
        """Thay đổi grade vật liệu → MAJOR."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        mat_changes = [c for c in result["changes"] if "materials" in c["field"]]
        major_mat = [c for c in mat_changes if c["category"] == "MAJOR"]
        self.assertGreater(len(major_mat), 0, "Thay đổi grade phải là MAJOR")

    def test_C08_unchanged_items_tracked(self):
        """Cấu kiện không đổi được theo dõi."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        self.assertGreater(result["total_unchanged"], 0,
                           "Phải có ít nhất 1 mục không thay đổi (Cột C1)")

    def test_C09_identical_docs_no_changes(self):
        """2 doc giống hệt nhau → 0 changes."""
        result = vd.diff_versions(self.rev_a, self.rev_a)
        self.assertEqual(result["total_changes"], 0, "2 doc giống nhau → 0 changes")

    def test_C10_report_generation(self):
        """Tạo báo cáo Markdown không lỗi."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        report = vd.generate_diff_report(result)
        self.assertIn("# Báo cáo So sánh Phiên bản", report)
        self.assertIn("MAJOR", report)

    def test_C11_delta_pct_calculated(self):
        """Delta % được tính đúng cho thay đổi số."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        numeric_changes = [c for c in result["changes"] if c.get("delta_pct") is not None]
        for ch in numeric_changes:
            self.assertGreater(ch["delta_pct"], 0, "Delta % phải > 0")

    def test_C12_changes_sorted_by_severity(self):
        """Changes được sắp xếp MAJOR trước MINOR."""
        result = vd.diff_versions(self.rev_a, self.rev_b)
        changes = result["changes"]
        if len(changes) > 1:
            first_cat = changes[0]["category"]
            self.assertIn(first_cat, ["MAJOR", "REMOVED", "ADDED"],
                          "Thay đổi quan trọng phải đứng đầu")

    def test_C13_numeric_delta_helper(self):
        """Hàm _numeric_delta tính đúng."""
        self.assertAlmostEqual(vd._numeric_delta(300, 400), 33.33, places=1)
        self.assertAlmostEqual(vd._numeric_delta(5.0, 4.0), 20.0, places=1)
        self.assertIsNone(vd._numeric_delta("abc", "xyz"))

    def test_C14_classify_change_major(self):
        """Field b_mm → MAJOR."""
        cat = vd._classify_change("sections.D1.b_mm", 300, 250)
        self.assertEqual(cat, "MAJOR")

    def test_C15_classify_change_minor(self):
        """Field không structural → MINOR."""
        cat = vd._classify_change("sections.D1.note", "ok", "updated")
        self.assertEqual(cat, "MINOR")

    def test_C16_classify_tiny_change_minor(self):
        """Thay đổi < 1% → MINOR (làm tròn số)."""
        cat = vd._classify_change("loads.label.value", 3.50, 3.51)
        self.assertEqual(cat, "MINOR")


# ─────────────────────────────────────────────────────────────────────────────
# Suite D: rebar_provided_checker (Gap 2)
# ─────────────────────────────────────────────────────────────────────────────

class TestRebarProvidedChecker(unittest.TestCase):
    """D: As_required vs As_provided."""

    def test_D01_parse_single_group(self):
        """Parse '4Ø25' → As đúng."""
        as_prov, bars = rc.parse_rebar_notation("4Ø25")
        expected = 4 * 3.14159 / 4 * 25**2
        self.assertAlmostEqual(as_prov, expected, delta=1.0)

    def test_D02_parse_multiple_groups(self):
        """Parse '2Ø32+2Ø20' → tổng As đúng."""
        as_prov, bars = rc.parse_rebar_notation("2Ø32+2Ø20")
        a32 = 2 * 3.14159 / 4 * 32**2
        a20 = 2 * 3.14159 / 4 * 20**2
        self.assertAlmostEqual(as_prov, a32 + a20, delta=2.0)

    def test_D03_parse_phi_notation(self):
        """Parse '6φ20' → As đúng."""
        as_prov, _ = rc.parse_rebar_notation("6φ20")
        expected = 6 * 3.14159 / 4 * 20**2
        self.assertAlmostEqual(as_prov, expected, delta=1.0)

    def test_D04_as_ok_when_sufficient(self):
        """As_provided ≥ As_required → status OK."""
        as_prov, _ = rc.parse_rebar_notation("4Ø25")  # ~1963mm²
        result = rc.check_as("Dầm D1", 1500.0, as_prov)
        self.assertEqual(result["status"], "OK")

    def test_D05_as_critical_when_insufficient(self):
        """As_provided << As_required → severity CRITICAL."""
        as_prov, _ = rc.parse_rebar_notation("3Ø16")  # ~603mm²
        result = rc.check_as("Dầm D1", 1520.0, as_prov)
        self.assertEqual(result["severity"], "CRITICAL")

    def test_D06_as_insufficient_status(self):
        """Status INSUFFICIENT khi thiếu thép."""
        result = rc.check_as("Dầm D2", 1200.0, 900.0)
        self.assertEqual(result["status"], "INSUFFICIENT")

    def test_D07_shortfall_calculated(self):
        """Shortfall được tính đúng."""
        result = rc.check_as("Dầm D3", 1000.0, 800.0)
        self.assertAlmostEqual(result["shortfall_mm2"], 200.0, delta=1.0)

    def test_D08_shortfall_pct(self):
        """Shortfall % đúng."""
        result = rc.check_as("Dầm D4", 1000.0, 800.0)
        self.assertAlmostEqual(result["shortfall_pct"], 20.0, delta=0.1)

    def test_D09_recommendation_present(self):
        """Có recommendation khi thiếu thép."""
        result = rc.check_as("Cột C1", 2000.0, 1500.0)
        self.assertIn("recommendation", result)
        self.assertTrue(len(result["recommendation"]) > 10)

    def test_D10_ratio_calculated(self):
        """Tỷ lệ As_provided/As_required đúng."""
        result = rc.check_as("Dầm D5", 1000.0, 1500.0)
        self.assertAlmostEqual(result["As_ratio"], 1.5, delta=0.01)

    def test_D11_skip_when_no_requirement(self):
        """As_required = 0 → SKIP."""
        result = rc.check_as("Dầm D6", 0.0, 1000.0)
        self.assertEqual(result["status"], "SKIP")

    def test_D12_bar_area_table(self):
        """BAR_AREA table có giá trị đúng cho Ø25."""
        a25 = rc.BAR_AREA[25]
        expected = 3.14159 / 4 * 625
        self.assertAlmostEqual(a25, expected, delta=0.1)

    def test_D13_calc_as_provided_from_list(self):
        """Tính As_provided từ list dict."""
        items = [{"dia_mm": 25, "count": 4}]
        total = rc.calc_as_provided(items)
        expected = 4 * 3.14159 / 4 * 625
        self.assertAlmostEqual(total, expected, delta=1.0)

    def test_D14_has_standard_ref(self):
        """Kết quả có trường Standard."""
        result = rc.check_as("CK", 1000.0, 1200.0)
        self.assertIn("Standard", result)
        self.assertIn("TCVN", result["Standard"])


# ─────────────────────────────────────────────────────────────────────────────
# Suite E: report_pipeline (Gap 3)
# ─────────────────────────────────────────────────────────────────────────────

class TestReportPipeline(unittest.TestCase):
    """E: Pipeline đầu cuối."""

    def test_E01_demo_runs_without_error(self):
        """Demo pipeline chạy thành công."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir, mode="review")
            self.assertIsInstance(result, dict)

    def test_E02_demo_has_read_result(self):
        """Pipeline demo có read_result."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            self.assertIn("read_result", result)
            self.assertTrue(result["read_result"])

    def test_E03_demo_has_conflict_result(self):
        """Pipeline demo có conflict_result."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            self.assertIsNotNone(result.get("conflict_result"))

    def test_E04_demo_has_rebar_results(self):
        """Pipeline demo có rebar_results."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            self.assertGreater(len(result.get("rebar_results", [])), 0)

    def test_E05_output_md_created(self):
        """File báo cáo .md được tạo."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            md_path = result.get("output_md")
            self.assertIsNotNone(md_path)
            self.assertTrue(os.path.exists(md_path), f"File không tồn tại: {md_path}")

    def test_E06_output_json_created(self):
        """File JSON data được tạo."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            json_path = result.get("output_json")
            self.assertIsNotNone(json_path)
            self.assertTrue(os.path.exists(json_path))

    def test_E07_md_contains_heading(self):
        """Báo cáo MD có heading đúng."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            with open(result["output_md"], encoding="utf-8") as f:
                content = f.read()
            self.assertIn("BÁO CÁO THẨM TRA", content)

    def test_E08_md_contains_conflict_section(self):
        """Báo cáo MD có phần Xung đột."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            with open(result["output_md"], encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Xung đột", content)

    def test_E09_md_contains_disclaimer(self):
        """Báo cáo MD có disclaimer bắt buộc."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            with open(result["output_md"], encoding="utf-8") as f:
                content = f.read()
            self.assertIn("kỹ sư có chứng chỉ hành nghề", content)

    def test_E10_pipeline_logs_present(self):
        """Pipeline logs được ghi."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(demo=True, output_dir=tmpdir)
            self.assertGreater(len(result.get("pipeline_logs", [])), 0)

    def test_E11_write_markdown_report_no_crash(self):
        """write_markdown_report không crash với data rỗng."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_report.md")
            rp.write_markdown_report(
                {"meta": {}, "read_result": {"engineering_data": {}}, "pipeline_logs": []},
                path
            )
            self.assertTrue(os.path.exists(path))

    def test_E12_nonexistent_file_handled(self):
        """File không tồn tại được xử lý gracefully."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rp.run_pipeline(
                input_path="/nonexistent/file.pdf",
                mode="review",
                output_dir=tmpdir,
            )
            self.assertIsInstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDocReaderPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestConflictAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestVersionDiffer))
    suite.addTests(loader.loadTestsFromTestCase(TestRebarProvidedChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestReportPipeline))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
