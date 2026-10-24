#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cognitive_brain_20261022.py — Bộ Kiểm thử Chuyên sâu "Bộ Não Xử Lý, Phân Tích & Nhận Biết Việc" (Cognitive Brain v2.0)
Kiểm tra toàn diện 10 nhóm lỗi nhận thức, phân tích ngữ nghĩa, trích xuất thực thể kỹ thuật, và điều phối đa tác vụ (BRAIN-BUG-01 đến BRAIN-BUG-10).
"""

from __future__ import annotations

import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import tempfile
import unittest
from pathlib import Path

_PATCHES_DIR = Path(__file__).resolve().parent.parent / "intermediate" / "patches"
sys.path.insert(0, str(_PATCHES_DIR))

import importlib.util
for _mod_name in (
    "intent_classifier", "approval_state", "approval_gate",
    "review_gate_engine", "confidence_score",
    "validate_handoff_schema", "handoff_manager", "project_memory"
):
    _mod_file = _PATCHES_DIR / f"{_mod_name}.py"
    if _mod_name not in sys.modules and _mod_file.exists():
        _spec = importlib.util.spec_from_file_location(_mod_name, str(_mod_file))
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules[_mod_name] = _mod
            _spec.loader.exec_module(_mod)


from intent_classifier import IntentClassifier, EntityExtractor, TEST_CASES, COGNITIVE_BENCHMARK_CASES
from approval_state import (
    ApprovalLevel,
    determine_approval_level,
    is_affirmative_response,
    is_negative_response,
    is_ambiguous_response,
)
from approval_gate import ApprovalCardGenerator, ApprovalContext
from review_gate_engine import ReviewGate
from confidence_score import ConfidenceCalculator
from validate_handoff_schema import validate_handoff
from handoff_manager import Handoff
from project_memory import ProjectMemory, DesignDecision


class TestCognitiveBrainV2(unittest.TestCase):
    """Kiểm thử toàn diện 10 nâng cấp Bộ Não Xử Lý & Nhận Biết Việc (2026-10-22)."""

    @classmethod
    def setUpClass(cls):
        cls.clf = IntentClassifier(db_path=str(_PATCHES_DIR / "keyword_database.json"))

    def test_01_zero_score_guard_no_false_default_to_de(self):
        """BRAIN-BUG-01: Câu lệnh ngoài miền kỹ thuật phải trả về primary_skill=None, conf=0.0 thay vì gán nhầm Design_Evaluation."""
        res = self.clf.classify("Xin chào hôm nay thời tiết thế nào")
        self.assertIsNone(res["primary_skill"])
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["confidence_level"], "LOW")

    def test_02_sls_crack_deflection_vs_forensic_disambiguation(self):
        """BRAIN-BUG-02: Bài toán tính/kiểm tra bề rộng vết nứt SLS (a_crc) và độ võng phải về SDE, không bị SKILL_FORENSIC cướp quyền."""
        sls_prompts = [
            "Kiểm tra bề rộng vết nứt và độ võng dầm B25 nhịp 8m",
            "Kiểm tra vết nứt uốn dầm B1 theo trạng thái giới hạn thứ hai SLS (a_crc <= 0.3mm)",
            "Tính bề rộng vết nứt a_crc của dầm BTCT B25 theo TCVN 5574:2018",
        ]
        for p in sls_prompts:
            res = self.clf.classify(p)
            self.assertEqual(res["primary_skill"], "Structural_Design_Engineer", f"Failed SLS routing for: {p}")
            self.assertGreaterEqual(res["confidence"], 0.85)

        forensic_res = self.clf.classify("Điều tra nguyên nhân nứt dầm tầng 3 ngoài hiện trường")
        self.assertEqual(forensic_res["primary_skill"], "SKILL_FORENSIC")

    def test_03_unaccented_vietnamese_recognition(self):
        """BRAIN-BUG-03: Nhận diện chính xác 100% câu lệnh tiếng Việt không dấu của kỹ sư."""
        unaccented_cases = [
            ("Tinh cot thep dam 300x600 nhip 6m be tong B25 thep CB400-V chiu momen 250 kNm", "Structural_Design_Engineer"),
            ("Tham tra ho so thiet ke ket cau tang ham va lap to trinh", "Design_Evaluation"),
            ("Thiet ke cop pha san day 150mm va cay chong", "SKILL_TEMPWORKS"),
            ("Phan tich SPT ho khoan HK1 va tinh thong so Plaxis", "SKILL_GEOTECH"),
            ("Lap phu luc tinh toan thuyet minh ket cau day du", "SKILL_PHULUC"),
        ]
        for p, expected in unaccented_cases:
            res = self.clf.classify(p)
            self.assertEqual(res["primary_skill"], expected, f"Failed unaccented prompt: {p}")
            self.assertGreaterEqual(res["confidence"], 0.85)

    def test_04_domain_ontology_tcvn_2023_2026_coverage(self):
        """BRAIN-BUG-04: Nhận diện đầy đủ Phân cấp công trình (TT 34/2026, QCVN 03:2022), Gió 2737:2023, Động đất 9386:2025, Chọc thủng, Cọc 10304:2025."""
        cases = [
            ("Phân cấp công trình nhà chung cư 25 tầng tổng diện tích sàn 45000m2 theo Thông tư 34/2026/TT-BXD", "Project_Manager"),
            ("Xác định cấp hậu quả C1 C2 C3 và cấp công trình theo QCVN 03:2022/BXD", "Project_Manager"),
            ("Tính tải trọng gió tác dụng lên nhà cao 60m tại TP.HCM theo TCVN 2737:2023", "Structural_Design_Engineer"),
            ("Tính tải trọng động đất theo phổ phản ứng TCVN 9386:2025 cho khu vực Quận 1", "Structural_Design_Engineer"),
            ("Kiểm tra chọc thủng sàn phẳng không dầm dày 220mm cột 500x500 theo TCVN 5574:2018", "Structural_Design_Engineer"),
            ("Tính sức chịu tải cọc khoan nhồi D1000 dài 45m theo SPT TCVN 10304:2025", "Structural_Design_Engineer"),
        ]
        for p, expected in cases:
            res = self.clf.classify(p)
            self.assertEqual(res["primary_skill"], expected, f"Failed ontology routing: {p}")
            self.assertGreaterEqual(res["confidence"], 0.85)

    def test_05_word_boundary_mention_override_and_multi_stage_dag(self):
        """BRAIN-BUG-05: Chống khớp nhầm từ khóa ngắn ('ve' trong 'review'), hỗ trợ @mention override và chuỗi DAG 3+ skills."""
        rev_res = self.clf.classify("Review phương án kết cấu", verbose=True)
        self.assertEqual(rev_res["primary_skill"], "Design_Evaluation")
        ce_matches = rev_res["debug"]["match_details"].get("Cost_Estimator", {}).get("matched", [])
        self.assertNotIn("[PRIMARY] VE", ce_matches)

        self.assertEqual(self.clf.classify("@DE tính cốt thép dầm B1")["primary_skill"], "Design_Evaluation")
        self.assertEqual(self.clf.classify("@SDE review bản vẽ kết cấu")["primary_skill"], "Structural_Design_Engineer")
        self.assertEqual(self.clf.classify("@GEO kiểm tra cọc")["primary_skill"], "SKILL_GEOTECH")

        dag1 = self.clf.classify("Phân tích địa chất SPT rồi tính móng cọc rồi lập phụ lục tính toán")
        self.assertTrue(dag1["is_pipeline"])
        self.assertEqual(
            dag1["pipeline"]["skills"],
            ["SKILL_GEOTECH", "Structural_Design_Engineer", "SKILL_PHULUC"],
        )

        dag2 = self.clf.classify("Tính dầm B1 300x600 rồi kiểm chứng chéo với ETABS rồi xuất thuyết minh phụ lục")
        self.assertTrue(dag2["is_pipeline"])
        self.assertEqual(
            dag2["pipeline"]["skills"],
            ["Structural_Design_Engineer", "SKILL_VERIFY", "SKILL_PHULUC"],
        )

    def test_06_deep_entity_extractor_v2(self):
        """BRAIN-BUG-06: Trích xuất dấu âm M=-250kNm, Mx/My, phân biệt lực cắt Q=180kN với tải q, thép I350x175x7x11 Q345B, sàn 5mx6m, giả định đúng cấu kiện."""
        ext_beam = EntityExtractor.extract(
            "Tính cốt thép dầm 300x600 nhịp 6m bê tông B25 thép CB400-V chịu momen M = -250 kNm, lực cắt Q = 180 kN",
            "Structural_Design_Engineer",
        )
        self.assertEqual(ext_beam["loads"].get("M"), -250.0)
        self.assertEqual(ext_beam["loads"].get("V"), 180.0)
        self.assertNotIn("q", ext_beam["loads"])

        ext_col = EntityExtractor.extract(
            "Kiểm tra cột 500x500 cao 4m chịu lực dọc N = 2500 kN, Mx = 120 kNm, My = 80 kNm, bê tông B35, thép CB500-V",
            "Structural_Design_Engineer",
        )
        self.assertEqual(ext_col["geometry"].get("H"), 4.0)
        self.assertEqual(ext_col["loads"].get("N"), 2500.0)
        self.assertEqual(ext_col["loads"].get("Mx"), 120.0)
        self.assertEqual(ext_col["loads"].get("My"), 80.0)
        self.assertTrue(any("a = 40mm" in a for a in ext_col["assumptions"]))

        ext_slab = EntityExtractor.extract(
            "Tính sàn 2 phương kích thước 5m x 6m dày 120mm, tĩnh tải g = 3.5 kN/m2, hoạt tải p = 2.0 kN/m2",
            "Structural_Design_Engineer",
        )
        self.assertEqual(ext_slab["geometry"].get("Lx"), 6.0)
        self.assertEqual(ext_slab["geometry"].get("Ly"), 5.0)
        self.assertEqual(ext_slab["loads"].get("g"), 3.5)
        self.assertEqual(ext_slab["loads"].get("p"), 2.0)
        self.assertTrue(any("a = 20mm" in a for a in ext_slab["assumptions"]))

        ext_steel = EntityExtractor.extract(
            "Tính dầm thép I350x175x7x11 nhịp 8m thép Q345B",
            "Structural_Design_Engineer",
        )
        self.assertEqual(ext_steel["geometry"].get("profile"), "I350x175x7x11")
        self.assertEqual(ext_steel["geometry"].get("tw"), 7)
        self.assertEqual(ext_steel["geometry"].get("tf"), 11)
        self.assertEqual(ext_steel["materials"].get("steel_grade"), "Q345B")
        self.assertFalse(any("B25" in a for a in ext_steel["assumptions"]))

        ctx = ApprovalContext(
            request_id="APR-TEST",
            user_prompt="Tính dầm",
            stages=["SDE"],
            extracted_materials={"concrete": "B25", "rebar": "CB400-V"},
        )
        card = ApprovalCardGenerator.generate(ctx)
        self.assertIn("CB400-V", card)

    def test_07_approval_response_negation_and_conditional_safety(self):
        """BRAIN-BUG-07: Các câu từ chối ('Không đồng ý', 'Đừng chạy vội', 'Khoan chạy') và câu điều kiện ('OK nhưng...') tuyệt đối không được trả về is_affirmative=True."""
        must_not_approve = [
            "Không đồng ý",
            "Tôi không duyệt phương án này",
            "OK nhưng sửa lại nhịp 6m",
            "Có thể bị sai tải trọng, khoan chạy",
            "Chưa duyệt được đâu",
            "Đừng chạy vội",
            "Hủy kế hoạch",
            "Bắt đầu nhưng giảm tiết diện xuống",
        ]
        for r in must_not_approve:
            self.assertFalse(is_affirmative_response(r), f"Dangerous false-affirmative on: '{r}'")

        self.assertTrue(is_ambiguous_response("OK nhưng sửa lại nhịp 6m"))
        self.assertTrue(is_ambiguous_response("Có thể bị sai tải trọng, khoan chạy"))
        self.assertTrue(is_negative_response("Đừng chạy vội"))

    def test_08_approval_level_thresholds_with_high_stages_and_tokens(self):
        """BRAIN-BUG-08: Pipeline >= 5 stages (kèm tools > 0) hoặc tokens >= 50,000 phải đạt mức HIGH approval."""
        lvl1, req1 = determine_approval_level(6, 4, 30000)
        self.assertEqual(lvl1, ApprovalLevel.HIGH)
        self.assertTrue(req1)

        lvl2, req2 = determine_approval_level(2, 2, 60000)
        self.assertEqual(lvl2, ApprovalLevel.HIGH)
        self.assertTrue(req2)

    def test_09_review_gate_and_confidence_score_case_insensitivity(self):
        """BRAIN-BUG-09: ReviewGate và ConfidenceCalculator hỗ trợ chuẩn viết hoa AGENTS.md §5 (Calculation_Logs, Standard_Method) và STANDARDS_LOCK v3.1.0."""
        sample_output = {
            "Standard_Method": "Thông tư 34/2026/TT-BXD & TCVN 5574:2018",
            "inputs": {"b": 300, "h": 600, "concrete": "B25"},
            "results": {"eta_M": 0.78, "eta_V": 0.62},
            "Calculation_Logs": [
                {
                    "step": 1,
                    "formula": "M_ult = R_b * b * x * (h_0 - 0.5*x)",
                    "substitution": "14.5 * 300 * 120 * (565 - 60)",
                    "result": 263.6,
                    "citation": "TCVN 5574:2018 — Mục 8.1.2 — Trang 65 — Tính cấu kiện chịu uốn",
                }
            ],
            "confidence_score": 0.92,
        }
        gate = ReviewGate(sample_output)
        passed = gate.run_all_checks()
        self.assertTrue(passed, f"ReviewGate blocked valid AGENTS.md §5 output: {[c.errors for c in gate.checks]}")

        calc = ConfidenceCalculator()
        score = calc.calculate_overall(sample_output)
        self.assertGreaterEqual(score, 0.80)

    def test_10_handoff_timezone_and_project_memory_resilience(self):
        """BRAIN-BUG-10: validate_handoff_schema hỗ trợ timestamp có múi giờ (+07:00), Handoff dùng v3.1.0, và ProjectMemory tạo DesignDecision không lỗi."""
        h = Handoff(
            handoff_type="structural_to_tempworks",
            project_id="PRJ-01",
            source_skill="Structural_Design_Engineer",
            target_skill="SKILL_TEMPWORKS",
            timestamp="2026-10-22T20:00:00+07:00",
            data={"slab_thickness_mm": 200},
            calculation_log_ids=["LOG-001"],
            confidence_level="HIGH",
        )
        h_json = h.to_json()
        self.assertEqual(h_json["project_context"]["standards_lock_version"], "v3.1.0")

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            import json
            json.dump(h_json, f, ensure_ascii=False)
            tmp_path = f.name
        try:
            valid, errors, warnings = validate_handoff(tmp_path)
            self.assertTrue(valid, f"Handoff validation failed: {errors}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory("TEST_PRJ", memory_dir=tmpdir)
            mem.create_context("Dự án Thử nghiệm", "BVTC")
            dec = DesignDecision(
                decision_id="DEC-01",
                date="2026-10-22",
                description="Chọn phương án sàn phẳng 220mm",
                approved_by="Kỹ sư trưởng",
            )
            mem.add_decision(dec)
            loaded_decs = mem.get_decisions()
            self.assertEqual(len(loaded_decs), 1)
            self.assertEqual(loaded_decs[0].rationale, "Theo quyết định kỹ thuật")


if __name__ == "__main__":
    unittest.main(verbosity=2)
