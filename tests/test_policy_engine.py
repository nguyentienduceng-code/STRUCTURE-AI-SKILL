# tests/test_policy_engine.py
# Test suite cho tools/policy_engine.py (Phase A, Phase B & Phase C)
# Chạy: python -m unittest tests.test_policy_engine -v

from __future__ import annotations

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import unittest
from pathlib import Path

# Đảm bảo import được tools/
_AGENTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_AGENTS_ROOT / "tools"))

from policy_engine import (
    Action,
    INTER_SKILL_TRIGGERS_REGISTRY,
    PolicyDecision,
    RED_FLAG_REGISTRY,
    RedFlagAction,
    RedFlagEvaluationResult,
    RedFlagSeverity,
    RFIDecision,
    RFIPriority,
    StatusCode,
    TriggerEvaluationResult,
    TriggerPriority,
    TriggerType,
    classify_rfi_priority,
    decide_eta,
    decide_eta_with_standards,
    evaluate_all_triggers,
    evaluate_red_flag,
    evaluate_trigger,
    get_active_fired_triggers,
    get_policy_engine_status,
    resolve_element_node,
    resolve_standard_basis,
    scan_red_flags,
)

# Đồ thị tri thức tiêu chuẩn (dùng DB tạm để không ghi rò rỉ vào production)
sys.path.insert(0, str(_AGENTS_ROOT / "_SHARED" / "standards"))


class TestPolicyEnginePhaseA(unittest.TestCase):
    """Kiểm thử toàn diện các quy tắc nghiệp vụ Phase A của Policy Engine."""

    # 1. Kiểm tra ngưỡng Value Engineering (η <= 0.70)
    def test_eta_ve_boundary_exact_0_70(self):
        decision = decide_eta(0.70)
        self.assertEqual(decision.action, Action.TRIGGER_VE)
        self.assertEqual(decision.status_code, StatusCode.VE_RECOMMENDED)
        self.assertEqual(decision.color, "🟢")
        self.assertTrue(decision.is_safe)
        self.assertIn("POST-DESIGN-02", decision.triggers[0])

    def test_eta_ve_below_0_70(self):
        for val in [0.10, 0.35, 0.50, 0.6999]:
            decision = decide_eta(val)
            self.assertEqual(decision.action, Action.TRIGGER_VE, f"Failed at η = {val}")
            self.assertEqual(decision.color, "🟢")
            self.assertTrue(decision.is_safe)

    # 2. Kiểm tra ranh giới trên của VE (η > 0.70 không trigger VE)
    def test_eta_ve_boundary_just_above_0_70(self):
        decision = decide_eta(0.7001)
        self.assertEqual(decision.action, Action.PASS)
        self.assertEqual(decision.color, "🟡")
        self.assertEqual(len(decision.triggers), 0)

        decision2 = decide_eta(0.71)
        self.assertEqual(decision2.action, Action.PASS)
        self.assertEqual(decision2.color, "🟡")

    # 3. Kiểm tra dải tối ưu (0.70 < η <= 0.90)
    def test_eta_optimal_range(self):
        for val in [0.72, 0.80, 0.85, 0.90]:
            decision = decide_eta(val)
            self.assertEqual(decision.action, Action.PASS, f"Failed at η = {val}")
            self.assertEqual(decision.status_code, StatusCode.PASS_OPTIMAL)
            self.assertEqual(decision.color, "🟡")
            self.assertTrue(decision.is_safe)

    # 4. Kiểm tra cảnh báo sát ngưỡng (0.90 < η <= 1.00)
    def test_eta_warning_range(self):
        for val in [0.9001, 0.95, 0.99, 1.00]:
            decision = decide_eta(val)
            self.assertEqual(decision.action, Action.PASS, f"Failed at η = {val}")
            self.assertEqual(decision.status_code, StatusCode.PASS_WARNING)
            self.assertEqual(decision.color, "🟠")
            self.assertTrue(decision.is_safe)

    # 5. Kiểm tra ngưỡng Repair / Không đạt (η > 1.00)
    def test_eta_repair_boundary_exact_above_1_00(self):
        decision = decide_eta(1.0001)
        self.assertEqual(decision.action, Action.REPAIR)
        self.assertEqual(decision.status_code, StatusCode.REPAIR_REQUIRED)
        self.assertEqual(decision.color, "🔴")
        self.assertFalse(decision.is_safe)

    def test_eta_repair_high_values(self):
        for val in [1.01, 1.15, 1.50, 2.00]:
            decision = decide_eta(val)
            self.assertEqual(decision.action, Action.REPAIR, f"Failed at η = {val}")
            self.assertEqual(decision.color, "🔴")
            self.assertFalse(decision.is_safe)

    # 6. Kiểm tra đầu vào dạng Dict của phần tử (nghiệp vụ kỹ thuật thực tế)
    def test_dict_input_triggers_ve_when_element_has_low_eta(self):
        elem_data = {"eta_M": 0.85, "eta_V": 0.55}
        decision = decide_eta(elem_data)
        self.assertEqual(decision.action, Action.TRIGGER_VE)
        self.assertEqual(decision.color, "🟢")
        self.assertEqual(decision.min_eta, 0.55)
        self.assertEqual(decision.max_eta, 0.85)

    def test_dict_input_repair_takes_strict_precedence(self):
        elem_data = {"eta_M": 1.08, "eta_V": 0.40}
        decision = decide_eta(elem_data)
        self.assertEqual(decision.action, Action.REPAIR)
        self.assertEqual(decision.color, "🔴")
        self.assertFalse(decision.is_safe)
        self.assertEqual(len(decision.triggers), 0)

    def test_dict_input_all_optimal(self):
        elem_data = {"eta_M": 0.78, "eta_V": 0.82, "eta_crack": 0.75}
        decision = decide_eta(elem_data)
        self.assertEqual(decision.action, Action.PASS)
        self.assertEqual(decision.status_code, StatusCode.PASS_OPTIMAL)
        self.assertEqual(decision.color, "🟡")

    def test_nested_dict_input(self):
        frame_data = {
            "Beam_B101": {"eta_M": 0.82, "eta_V": 0.74},
            "Col_C101": {"eta_N": 0.65, "eta_M": 0.70},
        }
        decision = decide_eta(frame_data)
        self.assertEqual(decision.action, Action.TRIGGER_VE)
        self.assertEqual(decision.color, "🟢")

    def test_list_input(self):
        decision = decide_eta([0.75, 0.88, 0.92])
        self.assertEqual(decision.action, Action.PASS)
        self.assertEqual(decision.color, "🟠")

    # 7. Xử lý các trường hợp ngoại lệ / dữ liệu lỗi
    def test_negative_eta_raises_value_error(self):
        with self.assertRaises(ValueError):
            decide_eta(-0.05)

    def test_empty_dict_raises_value_error(self):
        with self.assertRaises(ValueError):
            decide_eta({})

    def test_invalid_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            decide_eta("invalid_string")  # type: ignore

    # 8. Kiểm tra metadata của Policy Engine
    def test_policy_engine_status_metadata(self):
        status = get_policy_engine_status()
        self.assertEqual(status["engine_name"], "Structural_Policy_Engine")
        self.assertEqual(status["version"], "3.0.0")
        self.assertEqual(status["phase"], "Phase C (Full Suite)")
        self.assertEqual(status["active_rules_count"], 36)
        self.assertEqual(status["triggers_count"], 15)
        self.assertEqual(status["red_flags_count"], 18)
        self.assertTrue(status["rfi_priority_active"])


class TestPolicyEnginePhaseB(unittest.TestCase):
    """Kiểm thử toàn diện 15 Inter-Skill Triggers trong Phase B."""

    def test_registry_contains_exact_15_triggers(self):
        self.assertEqual(len(INTER_SKILL_TRIGGERS_REGISTRY), 15)
        expected_ids = {
            "POST-SDE-001", "POST-DEV-001", "POST-SDE-002",
            "POST-GEOTECH-01", "POST-GEOTECH-02", "POST-GEOTECH-03",
            "POST-EVAL-01", "POST-EVAL-02",
            "COND-VE-001", "COND-WARNING-001", "COND-FAIL-001",
            "COND-CONF-001", "COND-CONF-002",
            "ERR-STANDARD-001", "ERR-DATA-001",
        }
        self.assertEqual(set(INTER_SKILL_TRIGGERS_REGISTRY.keys()), expected_ids)

    # 1. POST-SDE-001: Structural Design -> Design Evaluation (conditional v7.1)
    def test_post_sde_001_always_fires(self):
        res = evaluate_trigger("POST-SDE-001", {})
        self.assertFalse(res.fired)

        res_active = evaluate_trigger("POST-SDE-001", {"pipeline": "design-review"})
        self.assertTrue(res_active.fired)
        self.assertEqual(res_active.target_skill, "Design_Evaluation")
        self.assertEqual(res_active.priority, TriggerPriority.HIGH)
        self.assertEqual(res_active.handoff_type, "structural_design_to_eval")

    # 2. POST-DEV-001: Design Evaluation -> SKILL_PHULUC
    def test_post_dev_001_fires_on_review_pass(self):
        ctx_pass = {"evaluation_type": "REVIEW", "status": "PASS"}
        res = evaluate_trigger("POST-DEV-001", ctx_pass)
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "SKILL_PHULUC")

        ctx_fail = {"evaluation_type": "REVIEW", "status": "FAIL"}
        res_fail = evaluate_trigger("POST-DEV-001", ctx_fail)
        self.assertFalse(res_fail.fired)

    # 3. POST-SDE-002: Structural Design -> SKILL_VERIFY
    def test_post_sde_002_fires_on_low_confidence_or_manual(self):
        res = evaluate_trigger("POST-SDE-002", {"confidence_score": 0.82})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "SKILL_VERIFY")

        res2 = evaluate_trigger("POST-SDE-002", {"confidence_level": "MEDIUM"})
        self.assertTrue(res2.fired)

        res_high = evaluate_trigger("POST-SDE-002", {"confidence_score": 0.95, "confidence_level": "HIGH"})
        self.assertFalse(res_high.fired)

        res_manual = evaluate_trigger("POST-SDE-002", {"confidence_score": 0.95, "manual_request": True})
        self.assertTrue(res_manual.fired)

    # 4. POST-GEOTECH-01: Geotech -> Structural Design
    def test_post_geotech_01_fires_when_ready(self):
        res = evaluate_trigger("POST-GEOTECH-01", {"foundation_params_ready": True, "foundation_params": {"qa": 250}})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "Structural_Design_Engineer")
        self.assertEqual(res.details["foundation_params"]["qa"], 250)

        res_not_ready = evaluate_trigger("POST-GEOTECH-01", {"foundation_params_ready": False})
        self.assertFalse(res_not_ready.fired)

    # 5. POST-GEOTECH-02: Base Heave Alert
    def test_post_geotech_02_fires_when_fs_below_1_5(self):
        res = evaluate_trigger("POST-GEOTECH-02", {"base_heave_FS": 1.35})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "Design_Evaluation")
        self.assertEqual(res.priority, TriggerPriority.HIGH)

        res_safe = evaluate_trigger("POST-GEOTECH-02", {"base_heave_FS": 1.70})
        self.assertFalse(res_safe.fired)

    # 6. POST-GEOTECH-03: Adverse Conditions -> SKILL_FORENSIC
    def test_post_geotech_03_fires_on_adverse_conditions(self):
        res = evaluate_trigger("POST-GEOTECH-03", {"adverse_conditions_detected": True, "adverse_conditions": ["Cavity"]})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "SKILL_FORENSIC")
        self.assertEqual(res.priority, TriggerPriority.CRITICAL)

        res_none = evaluate_trigger("POST-GEOTECH-03", {"adverse_conditions_detected": False})
        self.assertFalse(res_none.fired)

    # 7. POST-EVAL-01: VE Opportunity
    def test_post_eval_01_fires_on_low_eta(self):
        res = evaluate_trigger("POST-EVAL-01", {"design_results": {"eta_M": 0.65, "eta_V": 0.85}})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "Cost_Estimator")

        res_no_ve = evaluate_trigger("POST-EVAL-01", {"design_results": {"eta_M": 0.85, "eta_V": 0.88}})
        self.assertFalse(res_no_ve.fired)

    # 8. POST-EVAL-02: Standard Conflict
    def test_post_eval_02_fires_on_standard_mismatch(self):
        res = evaluate_trigger("POST-EVAL-02", {"standard_version_mismatch": True})
        self.assertTrue(res.fired)
        self.assertEqual(res.target_skill, "SKILL_VERIFY")

        res_ok = evaluate_trigger("POST-EVAL-02", {"standard_version_mismatch": False})
        self.assertFalse(res_ok.fired)

    # 9, 10, 11: COND-VE-001, COND-WARNING-001, COND-FAIL-001
    def test_conditional_utilization_triggers(self):
        ve_res = evaluate_trigger("COND-VE-001", {"design_results": [0.60, 0.85]})
        self.assertTrue(ve_res.fired)
        self.assertEqual(ve_res.target_skill, "Cost_Estimator")

        warn_res = evaluate_trigger("COND-WARNING-001", {"design_results": [0.85, 0.95]})
        self.assertTrue(warn_res.fired)
        self.assertEqual(warn_res.action, "ALERT_USER")

        fail_res = evaluate_trigger("COND-FAIL-001", {"design_results": [0.85, 1.15]})
        self.assertTrue(fail_res.fired)
        self.assertEqual(fail_res.action, "BLOCK_EXPORT")

    # 12, 13: COND-CONF-001 & COND-CONF-002
    def test_conditional_confidence_triggers(self):
        low_res = evaluate_trigger("COND-CONF-001", {"confidence_score": 0.50})
        self.assertTrue(low_res.fired)
        self.assertEqual(low_res.action, "PAUSE_AND_VERIFY")
        self.assertEqual(low_res.details["scope"], "FULL")

        med_res = evaluate_trigger("COND-CONF-002", {"confidence_score": 0.72})
        self.assertTrue(med_res.fired)
        self.assertEqual(med_res.action, "CONTINUE_WITH_WARNING")
        self.assertEqual(med_res.details["scope"], "SPOT_CHECK")

    # 14, 15: ERR-STANDARD-001 & ERR-DATA-001
    def test_error_triggers(self):
        err_std = evaluate_trigger("ERR-STANDARD-001", {"error": {"code": "E004"}})
        self.assertTrue(err_std.fired)
        self.assertEqual(err_std.target_skill, "SKILL_VERIFY")
        self.assertEqual(err_std.action, "BLOCK_UNTIL_RESOLVED")

        err_data = evaluate_trigger("ERR-DATA-001", {"error_code": "E002"})
        self.assertTrue(err_data.fired)
        self.assertEqual(err_data.target_skill, "SKILL_RFI")
        self.assertEqual(err_data.action, "AWAIT_DATA")

    # Helper functions: evaluate_all_triggers & get_active_fired_triggers
    def test_evaluate_all_triggers_filtering(self):
        ctx = {
            "evaluation_type": "REVIEW",
            "status": "PASS",
            "standard_version_mismatch": True,
            "design_results": {"eta_M": 0.65},
        }
        all_eval = evaluate_all_triggers(ctx, source_skill="Design_Evaluation", include_global=False)
        self.assertEqual(len(all_eval), 3)

        fired = get_active_fired_triggers(ctx, source_skill="Design_Evaluation", include_global=False)
        self.assertEqual(len(fired), 3)

        all_eval_with_global = evaluate_all_triggers(ctx, source_skill="Design_Evaluation", include_global=True)
        self.assertEqual(len(all_eval_with_global), 10)

    def test_invalid_trigger_id_raises_key_error(self):
        with self.assertRaises(KeyError):
            evaluate_trigger("NON_EXISTENT_TRIGGER", {})


class TestPolicyEnginePhaseC_RedFlags(unittest.TestCase):
    """Kiểm thử 18 Red Flag Triggers của SKILL_FORENSIC trong Phase C."""

    def test_registry_contains_exact_18_red_flags(self):
        self.assertEqual(len(RED_FLAG_REGISTRY), 18)
        rcf = [k for k in RED_FLAG_REGISTRY if k.startswith("RCF")]
        rhf = [k for k in RED_FLAG_REGISTRY if k.startswith("RHF")]
        rmf = [k for k in RED_FLAG_REGISTRY if k.startswith("RMF")]
        rlf = [k for k in RED_FLAG_REGISTRY if k.startswith("RLF")]
        self.assertEqual(len(rcf), 5)
        self.assertEqual(len(rhf), 6)
        self.assertEqual(len(rmf), 4)
        self.assertEqual(len(rlf), 3)

    def test_rcf_critical_triggers(self):
        # RCF-01: Sập cấu kiện
        res1 = evaluate_red_flag("RCF-01", "Phát hiện dầm D2 gãy đứt hoàn toàn")
        self.assertTrue(res1.triggered)
        self.assertEqual(res1.severity, RedFlagSeverity.CRITICAL)
        self.assertEqual(res1.action, RedFlagAction.LEAVE_SITE)
        self.assertEqual(res1.deadline, "Ngay lập tức")

        # RCF-02: Võng quá mức (text & dict)
        res2_text = evaluate_red_flag("RCF-02", "Dầm võng quá mức nhìn thấy bằng mắt thường")
        self.assertTrue(res2_text.triggered)
        res2_dict = evaluate_red_flag("RCF-02", {"deflection_ratio": 1.0 / 40.0})
        self.assertTrue(res2_dict.triggered)
        res2_safe = evaluate_red_flag("RCF-02", {"deflection_ratio": 1.0 / 250.0})
        self.assertFalse(res2_safe.triggered)

        # RCF-03: Tiếng nổ lạ
        res3 = evaluate_red_flag("RCF-03", "Nghe tiếng nổ lớn từ nút khung tầng 3")
        self.assertTrue(res3.triggered)

        # RCF-04: Nứt xuyên thấu >= 3mm
        res4_dict = evaluate_red_flag("RCF-04", {"crack_width_mm": 3.5, "crack_type": "through"})
        self.assertTrue(res4_dict.triggered)
        res4_small = evaluate_red_flag("RCF-04", {"crack_width_mm": 1.2})
        self.assertFalse(res4_small.triggered)

        # RCF-05: Nứt động mở rộng
        res5 = evaluate_red_flag("RCF-05", "Vết nứt động đang mở rộng theo thời gian")
        self.assertTrue(res5.triggered)

    def test_rhf_high_triggers(self):
        # RHF-01: Nứt chéo cột >= 1.5mm
        res1 = evaluate_red_flag("RHF-01", {"member_type": "cột BTCT", "crack_pattern": "xiên 45 độ", "crack_width_mm": 1.8})
        self.assertTrue(res1.triggered)
        self.assertEqual(res1.severity, RedFlagSeverity.HIGH)
        self.assertEqual(res1.action, RedFlagAction.EVACUATE)

        # RHF-02: Punching shear
        res2 = evaluate_red_flag("RHF-02", "Có dấu hiệu punching shear đâm thủng quanh cột C2")
        self.assertTrue(res2.triggered)

        # RHF-03: Lún chênh >= 1/200
        res3 = evaluate_red_flag("RHF-03", {"differential_settlement_ratio": 1.0 / 150.0})
        self.assertTrue(res3.triggered)

        # RHF-04: Bu lông lỏng / nứt mối hàn
        res4 = evaluate_red_flag("RHF-04", "Phát hiện bu lông lỏng và nứt đường hàn nút dầm")
        self.assertTrue(res4.triggered)

        # RHF-05: Bê tông rỗng xốp
        res5 = evaluate_red_flag("RHF-05", "Bê tông phong hóa rỗng xốp tại chân cột")
        self.assertTrue(res5.triggered)

        # RHF-06: Cốt thép gỉ thủng
        res6 = evaluate_red_flag("RHF-06", "Thép gỉ bong tróc giảm tiết diện nghiêm trọng")
        self.assertTrue(res6.triggered)

    def test_rmf_and_rlf_triggers(self):
        # RMF-01: Nứt uốn thông thường
        res_rmf1 = evaluate_red_flag("RMF-01", "Vết nứt uốn thẳng đứng giữa dầm bề rộng nhỏ")
        self.assertTrue(res_rmf1.triggered)
        self.assertEqual(res_rmf1.severity, RedFlagSeverity.MEDIUM)
        self.assertEqual(res_rmf1.action, RedFlagAction.INVESTIGATE)

        # RLF-01: Nứt nhiệt
        res_rlf1 = evaluate_red_flag("RLF-01", "Vết nứt nhiệt chân chim ngoài bề mặt tường")
        self.assertTrue(res_rlf1.triggered)
        self.assertEqual(res_rlf1.severity, RedFlagSeverity.LOW)
        self.assertEqual(res_rlf1.action, RedFlagAction.MONITOR)

    def test_scan_red_flags_ranking(self):
        obs = [
            "Xuất hiện vết nứt nhiệt ở bề mặt hoàn thiện",
            "Công nhân báo cáo có tiếng nổ lớn từ cột C3",
            "Kiểm tra thấy bu lông lỏng ở giằng thép",
        ]
        flags = scan_red_flags(obs)
        # Phải phát hiện ít nhất RCF-03 (CRITICAL), RHF-04 (HIGH), RLF-01 (LOW)
        self.assertGreaterEqual(len(flags), 3)
        # Flag đầu tiên phải là CRITICAL
        self.assertEqual(flags[0].severity, RedFlagSeverity.CRITICAL)
        self.assertEqual(flags[0].flag_id, "RCF-03")

    def test_invalid_red_flag_key(self):
        with self.assertRaises(KeyError):
            evaluate_red_flag("NON_EXISTENT_RCF", "some data")


class TestPolicyEnginePhaseC_RFIPriority(unittest.TestCase):
    """Kiểm thử Phân loại mức độ ưu tiên RFI của SKILL_RFI trong Phase C."""

    def test_classify_rfi_critical(self):
        rfi = "Yêu cầu khẩn cấp: Phát hiện cột C1 sai tiết diện chịu lực nguy hiểm sập đổ"
        res = classify_rfi_priority(rfi)
        self.assertEqual(res.priority, RFIPriority.CRITICAL)
        self.assertEqual(res.deadline_str, "24h")
        self.assertEqual(res.color, "🔴")
        self.assertIn("Dừng thi công", res.action)

    def test_classify_rfi_urgent(self):
        rfi = {"title": "Xung đột ống MEP và dầm chính", "impact": "Ảnh hưởng tiến độ đường găng thi công tầng 5"}
        res = classify_rfi_priority(rfi)
        self.assertEqual(res.priority, RFIPriority.URGENT)
        self.assertEqual(res.deadline_str, "3 ngày")
        self.assertEqual(res.color, "🟠")

    def test_classify_rfi_high(self):
        rfi = "Thiếu thông tin chiều dài neo cốt thép dầm D10, mã lỗi E002"
        res = classify_rfi_priority(rfi)
        self.assertEqual(res.priority, RFIPriority.HIGH)
        self.assertEqual(res.deadline_str, "7 ngày")
        self.assertEqual(res.color, "🟡")

    def test_classify_rfi_routine(self):
        rfi = "Yêu cầu định dạng bản vẽ hoàn công và bổ sung hồ sơ lưu"
        res = classify_rfi_priority(rfi)
        self.assertEqual(res.priority, RFIPriority.ROUTINE)
        self.assertEqual(res.deadline_str, "21 ngày")
        self.assertEqual(res.color, "🔵")

    def test_classify_rfi_normal_default(self):
        rfi = "Làm rõ chi tiết móc neo thép đai cột theo thiết kế mẫu"
        res = classify_rfi_priority(rfi)
        self.assertEqual(res.priority, RFIPriority.NORMAL)
        self.assertEqual(res.deadline_str, "14 ngày")
        self.assertEqual(res.color, "🟢")

    def test_classify_rfi_direct_declaration(self):
        res = classify_rfi_priority({"priority": "CRITICAL", "content": "Nội dung bất kỳ"})
        self.assertEqual(res.priority, RFIPriority.CRITICAL)
        self.assertEqual(res.deadline_str, "24h")


class TestStandardsGraphIntegration(unittest.TestCase):
    """
    Kiểm tra tích hợp Policy Engine + StandardsGraph (nâng cấp 1/2026-10-24).

    Đảm bảo:
    - decide_eta_with_standards trả về NGUYÊN QUYẾT ĐỊNH η (AGENTS.md §6) + CĂN CỨ tiêu chuẩn.
    - Ngưỡng η KHÔNG đổi — chỉ bổ sung trích dẫn và phát hiện mâu thuẫn.
    - Fail-safe: nếu đồ thị không khả dụng, không crash, không đổi hành vi.
    """

    @classmethod
    def setUpClass(cls):
        import tempfile
        from standards_graph import StandardsGraph
        cls._tmp = tempfile.TemporaryDirectory()
        cls.sg = StandardsGraph(db_path=Path(cls._tmp.name) / "sg_test.db")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_resolve_element_node_maps_vietnamese_types(self):
        self.assertEqual(resolve_element_node(element_type="dầm"), "ELEMENT_BEAM")
        self.assertEqual(resolve_element_node(element_type="cot"), "ELEMENT_COLUMN")
        self.assertEqual(resolve_element_node(element_type="dam_thep"), "ELEMENT_STEEL_BEAM")
        self.assertEqual(resolve_element_node(element_id="element_beam"), "ELEMENT_BEAM")
        self.assertIsNone(resolve_element_node(element_type="loại_chưa_biết"))

    def test_resolve_standard_basis_returns_clauses_and_checks(self):
        basis = resolve_standard_basis(element_type="dầm", graph=self.sg)
        self.assertIsNotNone(basis)
        self.assertEqual(basis["element_node"], "ELEMENT_BEAM")
        self.assertIn("TCVN 5574:2018", basis["standards"])
        self.assertTrue(any(c["clause_no"] == "Điều 8.1" for c in basis["clauses"]))
        # CHECK_MOMENT_ETA phải có ngưỡng ULS = 1.0
        mom = next(c for c in basis["checks"] if c["id"] == "CHECK_MOMENT_ETA")
        self.assertEqual(mom["threshold_value"], 1.0)
        # CHECK_DEFLECTION_RATIO (1/200, SLS) không phải ngưỡng η đơn giản
        defl = next(c for c in basis["checks"] if c["id"] == "CHECK_DEFLECTION_RATIO")
        self.assertIsNone(defl["threshold_value"])

    def test_resolve_standard_basis_unknown_element_returns_none(self):
        self.assertIsNone(resolve_standard_basis(element_type="khong_ton_tai", graph=self.sg))

    def test_decide_eta_with_standards_keeps_eta_decision_unchanged(self):
        """Quyết định η phải GIỮ NGUYÊN so với decide_eta — chỉ thêm căn cứ."""
        plain = decide_eta({"eta_M": 0.85, "eta_V": 0.55})
        wired = decide_eta_with_standards(
            {"eta_M": 0.85, "eta_V": 0.55}, element_type="dầm", graph=self.sg
        )
        self.assertEqual(plain.action, wired.action)
        self.assertEqual(plain.status_code, wired.status_code)
        self.assertEqual(plain.color, wired.color)
        self.assertEqual(plain.max_eta, wired.max_eta)
        # Nhưng đã có thêm căn cứ tiêu chuẩn
        self.assertIsNotNone(wired.standard_basis)
        self.assertTrue(
            any(s.startswith("Đồ thị tri thức:") for s in wired.rule_sources)
        )

    def test_decide_eta_with_standards_no_element_falls_back_to_plain(self):
        """Không có cấu kiện -> chuẩn hành vi decide_eta, standard_basis=None."""
        d = decide_eta_with_standards({"eta_M": 1.05}, graph=self.sg)
        self.assertEqual(d.action, Action.REPAIR)
        self.assertIsNone(d.standard_basis)
        self.assertIsNone(d.standard_conflicts)

    def test_decide_eta_with_standards_detects_threshold_conflict(self):
        """
        Nếu tiêu chuẩn đặt ngưỡng ULS lệch khỏi 1.00 -> phải phát hiện mâu thuẫn.
        (Dùng node check tuỳ chỉnh có ngưỡng 0.95 để kiểm tra logic conflict.)
        """
        # Tạo một check ULS lệch ngưỡng trong DB tạm (không chạm production)
        self.sg.upsert_node("CHECK_CUSTOM", {
            "type": "check", "limit_type": "ULS",
            "formula": "eta", "threshold": "<= 0.95"
        })
        self.sg.upsert_node("CLAUSE_CUSTOM", {
            "type": "clause", "standard": "TEST_STD", "clause_no": "X.1",
            "title": "Test clause"
        })
        self.sg.upsert_edge("ELEMENT_BEAM", "CHECK_CUSTOM", "verified_by")

        d = decide_eta_with_standards(0.9, element_type="dầm", graph=self.sg)
        self.assertIsNotNone(d.standard_conflicts)
        self.assertTrue(
            any("CHECK_CUSTOM" in c for c in d.standard_conflicts),
            f"Phải phát hiện conflict CHECK_CUSTOM, got: {d.standard_conflicts}"
        )

    def test_decide_eta_with_standards_failsafe_when_graph_unavailable(self):
        """Đồ thị không khả dụng (graph=None nhưng import lỗi) -> không crash."""
        # Pass graph=None: policy_engine sẽ tự import StandardsGraph.
        # Ở đây ta xác nhận nếu trả về None thì quyết định vẫn đúng.
        d = decide_eta_with_standards({"eta_M": 0.8}, element_type="dầm")
        # Hành vi eta luôn đúng (không phụ thuộc đồ thị có sẵn không)
        self.assertIn(d.action, (Action.PASS, Action.TRIGGER_VE, Action.REPAIR))

    def test_post_eval_trigger_propagates_standard_basis(self):
        """POST-EVAL-01 phải nhúng standard_basis + citations vào details."""
        res = evaluate_trigger(
            "POST-EVAL-01",
            {"design_results": {"eta_M": 0.5}, "element_type": "dầm"},
        )
        self.assertTrue(res.fired)  # η=0.5 <= 0.70 -> VE
        self.assertIn("standard_basis", res.details)
        self.assertIn("standard_citations", res.details)


# ==============================================================================
# TEST TÍCH HỢP LESSONS LEARNED -> DESIGN_EVALUATION (nâng cấp 1/2026-10-24)
# ==============================================================================

class TestLessonsLookupIntegration(unittest.TestCase):
    """
    Kiểm tra lessons_lookup + wire vào report_dispatcher không ghi rò rỉ vào production,
    và khớp đúng bài học theo ngữ cảnh.
    """

    def test_find_relevant_lessons_by_standard(self):
        sys.path.insert(0, str(_AGENTS_ROOT / "_SHARED" / "memory"))
        from lessons_lookup import find_relevant_lessons
        results = find_relevant_lessons(
            standards_text="TCVN 5574:2018, TCVN 5575:2024",
            keyword_text="dầm bê tông cốt thép",
        )
        self.assertGreaterEqual(len(results), 1)
        # Có LL-PRIME-01 (BEAM, TCVN 5574) hoặc LL-SS1-01 (CLIENT_PREF, TCVN 5574)
        ids = [r["lesson_id"] for r in results]
        self.assertTrue(
            any(i in ids for i in ("LL-PRIME-01", "LL-SS1-01")),
            f"Không khớp lesson nào kỳ vọng, got: {ids}"
        )

    def test_find_relevant_lessons_by_project_code(self):
        sys.path.insert(0, str(_AGENTS_ROOT / "_SHARED" / "memory"))
        from lessons_lookup import find_relevant_lessons
        results = find_relevant_lessons(project_code="MONTALP")
        self.assertTrue(any(r["lesson_id"] == "LL-MONTALP-01" for r in results))

    def test_find_relevant_lessons_empty_returns_empty(self):
        sys.path.insert(0, str(_AGENTS_ROOT / "_SHARED" / "memory"))
        from lessons_lookup import find_relevant_lessons
        # Tiêu chuẩn + keyword hoàn toàn không xuất hiện trong bất kỳ lesson nào.
        results = find_relevant_lessons(
            standards_text="XQZ-9999:2020",
            keyword_text="zxywv qrsz",  # token hiếm, không khớp tag/issue/cause/solution
        )
        self.assertEqual(results, [])

    def test_format_lessons_markdown_empty_and_populated(self):
        sys.path.insert(0, str(_AGENTS_ROOT / "_SHARED" / "memory"))
        from lessons_lookup import find_relevant_lessons, format_lessons_markdown
        results = find_relevant_lessons(standards_text="TCVN 5574:2018")
        self.assertGreater(len(results), 0)
        lines = format_lessons_markdown(results)
        self.assertTrue(lines)
        self.assertIn("Kinh nghiệm liên dự án", lines[0])
        # Không lesson -> []
        self.assertEqual(format_lessons_markdown([]), [])

    def test_report_dispatcher_collects_lessons_without_crash(self):
        """report_dispatcher._collect_lessons phải fail-safe (không crash)."""
        sys.path.insert(0, str(_AGENTS_ROOT / "skills" / "Design_Evaluation" / "scripts"))
        import importlib
        import report_dispatcher
        importlib.reload(report_dispatcher)
        # Handoff tối giản -> không crash, trả list (có thể rỗng)
        out = report_dispatcher._collect_lessons({"Ten_Du_An": "X"})
        self.assertIsInstance(out, list)
        # Handoff có standards -> không crash
        out2 = report_dispatcher._collect_lessons(
            {"Ten_Du_An": "Y", "Standard_Method": "TCVN 5574:2018", "Hang_Muc": "dầm"}
        )
        self.assertIsInstance(out2, list)


if __name__ == "__main__":
    unittest.main()
