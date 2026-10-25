# -*- coding: utf-8 -*-
"""
test_cognitive_and_control_systems.py — Kiểm tra toàn diện Bộ Điều Khiển Hệ Thống và Đồ Thị Tri Thức Tiêu Chuẩn (v2.0)
Bao gồm:
1. Circuit Breaker (Cầu dao tự ngắt bảo vệ phần mềm + tự phát sinh TraceSpan TRIP_CIRCUIT / CIRCUIT_RECOVERED)
2. Execution Guard (Hàng rào an toàn phân quyền)
3. Loop Breaker (Chống lặp vô tận và ping-pong tác tử)
4. Blackbox Trace Recorder (Hộp đen hành trình + Xoay vòng trace rotation)
5. Standards Graph v2.0 (SQLite CTEs, WAL Checkpoint, Truy vấn ngược query_standard_impact, Phát hiện xung đột E004, Bourbon Steel nodes)
6. Lessons Learned Repository (Ký ức kinh nghiệm liên dự án Mem0 style)
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import unittest
from pathlib import Path

# Thêm đường dẫn import
AGENTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENTS_ROOT / "tools"))
sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "standards"))
sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "memory"))

from system_controller import (
    CircuitBreaker, CircuitState, CircuitBreakerTripped,
    ExecutionGuard, GuardDecision, LoopBreaker, BlackboxRecorder, SystemController
)
from standards_graph import StandardsGraph
from project_memory import LessonsLearnedRepository, LessonLearned


class TestSystemController(unittest.TestCase):
    def test_circuit_breaker_trip_and_recovery(self):
        cb = CircuitBreaker("test_etabs", failure_threshold=2, recovery_timeout=0.2)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_execution())

        # Thất bại lần 1
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # Thất bại lần 2 -> Tripped
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.allow_execution())

        # Thử gọi hàm khi OPEN -> Phải ném ngoại lệ
        with self.assertRaises(CircuitBreakerTripped):
            cb.call(lambda: "should_fail")

        # Đợi hạ nhiệt 0.25s -> Phải chuyển sang HALF_OPEN
        time.sleep(0.25)
        self.assertTrue(cb.allow_execution())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

        # Gọi thành công trong HALF_OPEN -> Quay về CLOSED
        res = cb.call(lambda: "recovered")
        self.assertEqual(res, "recovered")
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_execution_guard_forbidden_commands(self):
        guard = ExecutionGuard(mode="SAFE")

        # Lệnh bình thường -> ALLOW
        res_ok = guard.evaluate_tool_call("calc_beam", {"command": "python calc.py"})
        self.assertEqual(res_ok["decision"], GuardDecision.ALLOW.value)

        # Lệnh nguy hiểm -> BLOCK
        res_bad = guard.evaluate_tool_call("run_shell", {"command": "rm -rf /root"})
        self.assertEqual(res_bad["decision"], GuardDecision.BLOCK.value)

    def test_execution_guard_read_only_mode(self):
        guard_ro = ExecutionGuard(mode="READ_ONLY")

        # Tool đọc -> ALLOW
        res_read = guard_ro.evaluate_tool_call("revit_read_properties")
        self.assertEqual(res_read["decision"], GuardDecision.ALLOW.value)

        # Tool sửa/tạo/xóa -> BLOCK
        res_write = guard_ro.evaluate_tool_call("revit_modify_elements")
        self.assertEqual(res_write["decision"], GuardDecision.BLOCK.value)

    def test_loop_breaker_ping_pong_detection(self):
        lb = LoopBreaker(max_hops=6)

        # Chuỗi bình thường A -> B -> C -> D
        r1 = lb.record_hop("Agent_A")
        r2 = lb.record_hop("Agent_B")
        r3 = lb.record_hop("Agent_C")
        self.assertFalse(r3["is_loop"])

        # Tạo ping-pong: A -> B -> A -> B
        lb.reset()
        lb.record_hop("Structural_Design_Engineer")
        lb.record_hop("Cost_Estimator")
        lb.record_hop("Structural_Design_Engineer")
        r_loop = lb.record_hop("Cost_Estimator")
        self.assertTrue(r_loop["is_loop"])
        self.assertIn("ping-pong", r_loop["reason"])

    def test_blackbox_trace_recorder(self):
        recorder = BlackboxRecorder()
        trace_id = recorder.generate_trace_id()
        self.assertTrue(trace_id.startswith("TRC-"))

        span = recorder.start_span(trace_id, actor="Structural_Design_Engineer", action="calculate_beam")
        time.sleep(0.01)  # tạo độ trễ nhỏ
        recorder.end_span(span, status="SUCCESS", metadata={"element": "D1"})

        self.assertEqual(span.status, "SUCCESS")
        self.assertGreater(span.duration_ms, 0)

        summary = recorder.export_summary()
        self.assertGreaterEqual(summary["success_count"], 1)


class TestStandardsGraph(unittest.TestCase):
    """
    Dùng DB TẠM cho mọi test để không ghi rò rỉ vào standards_graph.db production.
    """

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "standards_graph_test.db"
        self.sg = StandardsGraph(db_path=self.db_path, auto_checkpoint_on_exit=False)

    def tearDown(self):
        self._tmp.cleanup()

    def test_standards_graph_traversal_and_queries(self):
        sg = self.sg

        # Tra cứu cấu kiện dầm
        reqs = sg.query_element_requirements("ELEMENT_BEAM")
        self.assertEqual(reqs["element"]["name"], "Dầm bê tông cốt thép")
        self.assertIn("TCVN 5574:2018", reqs["connected_standards"])
        self.assertIn("TCVN 2737:2023", reqs["connected_standards"])
        self.assertGreaterEqual(len(reqs["applicable_clauses"]), 3)
        self.assertGreaterEqual(len(reqs["verification_checks"]), 1)

    def test_standards_graph_custom_node_and_edge(self):
        sg = self.sg
        # Thêm một node tùy chỉnh
        sg.upsert_node("CUSTOM_CHECK_DEFLECTION", {
            "type": "check",
            "name": "Kiểm tra võng sàn console",
            "threshold": "<= L/100"
        })
        node = sg.get_node("CUSTOM_CHECK_DEFLECTION")
        self.assertIsNotNone(node)
        self.assertEqual(node["threshold"], "<= L/100")

    def test_v2_wal_checkpoint_execution(self):
        """Roadmap v2.0 §2.1.A: Kiểm tra thực thi PRAGMA wal_checkpoint(TRUNCATE) và bắt lỗi mode sai."""
        res = self.sg.checkpoint("TRUNCATE")
        self.assertEqual(res["mode"], "TRUNCATE")
        self.assertEqual(res["status"], "OK")
        with self.assertRaises(ValueError):
            self.sg.checkpoint("INVALID_MODE")

    def test_v2_query_standard_impact_bidirectional(self):
        """Roadmap v2.0 §2.1.B: Kiểm tra truy vấn ngược từ Tiêu chuẩn -> Cấu kiện, Điều khoản, Phép kiểm & Bản cũ."""
        impact = self.sg.query_standard_impact("TCVN 5574:2018")
        self.assertNotIn("error", impact)
        elem_ids = {e["id"] for e in impact["affected_elements"]}
        self.assertIn("ELEMENT_BEAM", elem_ids)
        self.assertIn("ELEMENT_COLUMN", elem_ids)
        self.assertIn("ELEMENT_SLAB", elem_ids)
        self.assertGreaterEqual(impact["impact_summary"]["clauses_count"], 3)
        self.assertGreaterEqual(impact["impact_summary"]["checks_count"], 2)
        # Phải phát hiện bản cũ TCVN 5574:2012 đang gắn cạnh CONFLICT_WITH
        conflict_ids = {c["id"] for c in impact["conflicting_or_legacy_standards"]}
        self.assertIn("TCVN_5574_2012", conflict_ids)

    def test_v2_standard_conflict_detector_e004(self):
        """Roadmap v2.0 §2.1.C: Tự động phát hiện tiêu chuẩn hết hiệu lực và dùng lẫn lộn 2 phiên bản (E004)."""
        # Trường hợp 1: Dùng tiêu chuẩn cũ và trộn 2 phiên bản TCVN 5574
        res_bad = self.sg.detect_standard_conflicts(["TCVN 5574:2018", "TCVN 5574:2012", "TCVN 5575:2012"])
        self.assertTrue(res_bad["has_conflict"])
        self.assertEqual(res_bad["error_code"], "E004")
        types = {c["conflict_type"] for c in res_bad["conflicts"]}
        self.assertIn("DEPRECATED_STANDARD_USED", types)
        self.assertIn("MIXED_VERSIONS_IN_PROJECT", types)

        # Trường hợp 2: Bộ tiêu chuẩn hoàn toàn hợp lệ theo STANDARDS_LOCK v3.1.0
        res_ok = self.sg.detect_standard_conflicts(["TCVN 2737:2023", "TCVN 5574:2018", "TCVN 5575:2024", "Thông tư 34/2026/TT-BXD"])
        self.assertFalse(res_ok["has_conflict"])
        self.assertIsNone(res_ok["error_code"])

    def test_v2_bourbon_industrial_steel_nodes(self):
        """Kiểm tra các node tri thức Nhà thép Tiền chế & Xà gồ Z (Bourbon Project: MBMA 2012, AISC 360-10, AISI S100)."""
        peb = self.sg.query_element_requirements("ELEMENT_PEB_PORTAL_FRAME")
        self.assertIn("MBMA 2012", peb["connected_standards"])
        self.assertIn("AISC 360-10", peb["connected_standards"])
        self.assertIn("TCVN 5575:2024", peb["connected_standards"])

        purlin = self.sg.query_element_requirements("ELEMENT_CFS_PURLIN")
        self.assertIn("AISI S100-2007", purlin["connected_standards"])
        self.assertTrue(any(c["id"] == "CHECK_PURLIN_DEFLECTION" for c in purlin["verification_checks"]))


class TestLessonsLearnedRepository(unittest.TestCase):
    """
    Dùng thư mục LƯU TRỮ TẠM cho mọi test để không ghi rò rỉ vào file production
    (.agents/_SHARED/memory/projects/global_lessons_learned.json).
    """

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_find_lessons_by_tags_and_category(self):
        repo = LessonsLearnedRepository(storage_dir=self.storage_dir)

        # Tìm theo tag dam_chuyen
        lessons_tag = repo.find_lessons(tags=["dam_chuyen"])
        self.assertGreaterEqual(len(lessons_tag), 1)
        self.assertEqual(lessons_tag[0].project_code, "Prime_Diamond")

        # Tìm theo category CLIENT_PREF
        lessons_cat = repo.find_lessons(category="CLIENT_PREF")
        self.assertGreaterEqual(len(lessons_cat), 1)
        self.assertEqual(lessons_cat[0].project_code, "SS1")

        # Thêm bài học mới
        new_lesson = LessonLearned(
            lesson_id="LL-TEST-01",
            project_code="TEST_PROJECT",
            category="FOUNDATION",
            issue_description="Lún lệch móng đơn trên nền đất yếu",
            root_cause="Không kiểm tra ứng suất hữu hiệu tầng đất bùn",
            preventive_solution="Chuyển sang móng bè hoặc ép cọc BTCT",
            tags=["mong_don", "dat_yeu"]
        )
        repo.add_lesson(new_lesson)
        found = repo.find_lessons(tags=["dat_yeu"])
        self.assertTrue(any(l.lesson_id == "LL-TEST-01" for l in found))


# ==============================================================================
# TEST HỒI QUY — chống tái phát các lỗi đã phát hiện khi review (Claude, 2026-10-24)
# ==============================================================================

class TestRegressionClaudeReview(unittest.TestCase):
    """Các lỗi runtime đã tìm ra trong lần review đầu tiên — phải luôn xanh."""

    def test_traverse_both_direction_works(self):
        """BUG-001: traverse(direction='both') ném ProgrammingError do sai số binding."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            sg = StandardsGraph(db_path=Path(td) / "g.db", auto_checkpoint_on_exit=False)
            res = sg.traverse("ELEMENT_BEAM", direction="both", max_depth=2)
            self.assertIsInstance(res, list)
            self.assertGreater(len(res), 0)

    def test_traverse_all_directions_do_not_leak_handles(self):
        """BUG-002: mỗi hàm phải đóng connection SQLite, không rò rỉ file handle."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            sg = StandardsGraph(db_path=Path(td) / "g.db", auto_checkpoint_on_exit=False)
            for d in ("outbound", "inbound", "both"):
                sg.traverse("ELEMENT_BEAM", direction=d, max_depth=2)
            # Trên Windows, file đã đóng thì mới xoá được.
            self.assertTrue((Path(td) / "g.db").exists())

    def test_upsert_edge_is_idempotent(self):
        """BUG-003: gọi upsert_edge 2 lần cùng quan hệ không được nhân bản cạnh."""
        import tempfile
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "g.db"
            sg = StandardsGraph(db_path=db, auto_checkpoint_on_exit=False)
            sg.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_MOMENT", "governed_by")
            sg.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_MOMENT", "governed_by")
            conn = sqlite3.connect(str(db))
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM edges WHERE source=? AND target=?",
                    ("ELEMENT_BEAM", "CLAUSE_5574_MOMENT")
                ).fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(count, 1)

    def test_loop_breaker_respects_max_cycle_repeats(self):
        """
        BUG-004: max_cycle_repeats = số chu kỳ 2 tác tử đầy đủ cần có trước khi trip.
        max_cycle_repeats=2 -> trip ở A,B,A,B (4 hop).
        max_cycle_repeats=3 -> chưa trip ở 4-5 hop, trip ở 6 hop (A,B,A,B,A,B).
        """
        lb = LoopBreaker(max_hops=20, max_cycle_repeats=3)
        lb.record_hop("A")
        lb.record_hop("B")
        lb.record_hop("A")
        self.assertFalse(lb.record_hop("B")["is_loop"])  # 4 hop: mới 2 chu kỳ
        self.assertFalse(lb.record_hop("A")["is_loop"])  # 5 hop
        self.assertTrue(lb.record_hop("B")["is_loop"])   # 6 hop: đủ 3 chu kỳ

        # max_cycle_repeats=2 -> trip sớm hơn, ở 4 hop
        lb2 = LoopBreaker(max_hops=20, max_cycle_repeats=2)
        lb2.record_hop("A")
        lb2.record_hop("B")
        lb2.record_hop("A")
        self.assertTrue(lb2.record_hop("B")["is_loop"])

    def test_circuit_breaker_allow_execution_does_not_consume_probe(self):
        """
        BUG-005: allow_execution() phải chuyển OPEN->HALF_OPEN nhưng KHÔNG tiêu tốn
        lượt thử, nếu không thì call() ngay sau đó sẽ bị chặn oan.
        """
        cb = CircuitBreaker("reg_test", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        time.sleep(0.15)
        self.assertTrue(cb.allow_execution())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        # Lượt thử vẫn phải còn -> call() phải chạy được
        self.assertEqual(cb.call(lambda: "ok"), "ok")
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_circuit_breaker_half_open_single_probe(self):
        """BUG-006: HALF_OPEN chỉ cho 1 lượt thử đồng thời."""
        cb = CircuitBreaker("reg_probe", failure_threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        time.sleep(0.1)
        self.assertTrue(cb._try_acquire_probe())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        # Lượt thử thứ 2 phải bị từ chối
        self.assertFalse(cb._try_acquire_probe())

    def test_execution_guard_does_not_block_read_tools_by_substring(self):
        """BUG-007: 'recalculate' chứa chuỗi 'calc' không được coi là tool ghi."""
        guard = ExecutionGuard(mode="READ_ONLY")
        res = guard.evaluate_tool_call("recalculate_beam")
        self.assertEqual(res["decision"], GuardDecision.ALLOW.value)

    def test_blackbox_recorder_persists_span_to_disk(self):
        """BUG-008: vết thực thi phải được ghi bền vững xuống đĩa."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            rec = BlackboxRecorder(log_dir=Path(td))
            trace_id = rec.generate_trace_id()
            span = rec.start_span(trace_id, actor="A", action="act")
            rec.end_span(span, status="SUCCESS")
            files = list(Path(td).glob("traces/*.jsonl"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            self.assertIn(trace_id, content)
            self.assertIn("SUCCESS", content)

    def test_sync_bus_atomic_write_leaves_no_partial_file(self):
        """BUG-009: ghi bus phải nguyên tử — không còn file .tmp sót lại."""
        import tempfile
        sys.path.insert(0, str(AGENTS_ROOT / "tools"))
        import sync_bus
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "bus.json"
            sync_bus._atomic_write_json(target, {"x": 1, "v": "tiêu chuẩn ✓"})
            import json
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["x"], 1)
            self.assertEqual(list(Path(td).glob("*.tmp*")), [])

    def test_sync_bus_file_lock_is_exclusive(self):
        """BUG-010: FileLock phải chặn được lần giành khoá thứ hai."""
        import tempfile
        sys.path.insert(0, str(AGENTS_ROOT / "tools"))
        import sync_bus
        with tempfile.TemporaryDirectory() as td:
            lock_path = Path(td) / "t.lock"
            l1 = sync_bus.FileLock(lock_path, timeout=0.2)
            self.assertTrue(l1.acquire())
            l2 = sync_bus.FileLock(lock_path, timeout=0.3)
            self.assertFalse(l2.acquire())
            l1.release()
            l3 = sync_bus.FileLock(lock_path, timeout=0.3)
            self.assertTrue(l3.acquire())
            l3.release()

    def test_skill_guard_preflight_blocks_dangerous_shell(self):
        """BUG-011: skill_guard phải chặn lệnh shell nguy hiểm."""
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        from skill_guard import preflight
        allowed, reason = preflight("Test", "run_shell", {"command": "rm -rf /"})
        self.assertFalse(allowed)
        self.assertIn("GUARD_BLOCKED", reason)

    def test_skill_guard_import_paths_resolve_for_all_3_skills(self):
        """
        BUG-013: đường dẫn import skill_guard trong 3 skill phải resolve tới
        .agents/_SHARED/SHARED_CONTEXT thật (không rơi vào nhánh except im lặng).
        """
        import importlib
        skills = {
            "approval_gate": ("Global_Dispatcher", "scripts"),
            "report_dispatcher": ("Design_Evaluation", "scripts"),
            "export_calc_sheet": ("Structural_Design_Engineer", "scripts"),
        }
        for mod_name, (skill, sub) in skills.items():
            p = AGENTS_ROOT / "skills" / skill / sub
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            sys.modules.pop(mod_name, None)
            mod = importlib.import_module(mod_name)
            self.assertTrue(
                getattr(mod, "_GUARD_AVAILABLE", False),
                f"{skill}: _GUARD_AVAILABLE=False — skill_guard không import được (guard bị vô hiệu hoá âm thầm)."
            )
            guard_dir = mod._find_skill_guard_dir()
            self.assertIsNotNone(guard_dir, f"{skill}: không tìm thấy _SHARED/SHARED_CONTEXT")
            self.assertTrue(guard_dir.is_dir(), f"{skill}: {guard_dir} không tồn tại")

    def test_skill_guard_fail_closed_on_controller_error(self):
        """
        BUG-014: khi controller (đã cài) ném exception, preflight phải CHẶN
        (fail-closed), không cho chạy tự do như hard-code fail_open=True ở v1.0.
        """
        import importlib
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        skill_guard = importlib.import_module("skill_guard")
        importlib.reload(skill_guard)

        class Boom:
            def preflight_check(self, *a, **k):
                raise RuntimeError("simulated controller crash")
            loop_breaker = None

        skill_guard._controller = Boom()
        skill_guard._controller_available = True
        skill_guard._controller_import_attempted = True

        # Mặc định (policy fail_closed=True) -> CHẶN
        ok, why = skill_guard.preflight("GD", "some_tool")
        self.assertFalse(ok)
        self.assertIn("CONTROLLER_ERROR", why)

        # fail_open=True (ghi đè) -> cho phép
        ok, why = skill_guard.preflight("GD", "some_tool", fail_open=True)
        self.assertTrue(ok)
        self.assertIn("FAIL_OPEN", why)

        # Whitelist tool trong policy -> cho phép
        skill_guard._policy_cache = dict(skill_guard.load_policy())
        skill_guard._policy_cache["tools_fail_open"] = ["some_tool"]
        ok, why = skill_guard.preflight("GD", "some_tool")
        self.assertTrue(ok)

        # Reset state module về sạch để không ảnh hưởng test khác
        importlib.reload(skill_guard)

    def test_skill_guard_harness_missing_allows_with_warning_by_default(self):
        """
        BUG-014b: khi chưa có hạ tầng guard (không import được controller),
        mặc định CHO PHÉP + cảnh báo (không thể chặn cái chưa tồn tại).
        """
        import importlib
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        skill_guard = importlib.import_module("skill_guard")
        importlib.reload(skill_guard)

        skill_guard._controller = None
        skill_guard._controller_available = False
        skill_guard._controller_import_attempted = True

        ok, why = skill_guard.preflight("GD", "some_tool")
        self.assertTrue(ok)
        self.assertIn("HARNESS_MISSING", why)

        # Policy block -> CHẶN
        skill_guard._policy_cache = dict(skill_guard._DEFAULT_POLICY)
        skill_guard._policy_cache["harness_missing_policy"] = "block"
        ok, why = skill_guard.preflight("GD", "some_tool")
        self.assertFalse(ok)
        self.assertIn("HARNESS_MISSING", why)

        # Reset state module về sạch (controller thật) để không ảnh hưởng test khác
        importlib.reload(skill_guard)

    def test_skill_guard_guard_mode_from_policy_and_env(self):
        """
        BUG-014c: chế độ guard phải được chọn từ guard_policy.json (readonly_skills)
        và ghi đè được bằng env var GUARD_MODE.
        """
        import importlib
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        skill_guard = importlib.import_module("skill_guard")
        importlib.reload(skill_guard)

        self.assertEqual(skill_guard.get_guard_mode("Global_Dispatcher"), "SAFE")

        skill_guard._policy_cache = dict(skill_guard.load_policy())
        skill_guard._policy_cache["readonly_skills"] = ["Design_Evaluation"]
        self.assertEqual(skill_guard.get_guard_mode("Design_Evaluation"), "READ_ONLY")

        os.environ["GUARD_MODE"] = "UNRESTRICTED"
        self.assertEqual(skill_guard.get_guard_mode("Design_Evaluation"), "UNRESTRICTED")
        del os.environ["GUARD_MODE"]
        skill_guard._policy_cache = None
        importlib.reload(skill_guard)

    def test_skill_guard_env_override_fail_open(self):
        """BUG-014d: env var GUARD_FAIL_OPEN=1 cho phép chạy tiếp khi controller lỗi."""
        import importlib
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        skill_guard = importlib.import_module("skill_guard")
        importlib.reload(skill_guard)

        class Boom:
            def preflight_check(self, *a, **k):
                raise RuntimeError("boom")
            loop_breaker = None

        skill_guard._controller = Boom()
        skill_guard._controller_available = True
        skill_guard._controller_import_attempted = True

        os.environ["GUARD_FAIL_OPEN"] = "1"
        ok, why = skill_guard.preflight("GD", "some_tool")
        self.assertTrue(ok)
        self.assertIn("FAIL_OPEN", why)
        del os.environ["GUARD_FAIL_OPEN"]
        importlib.reload(skill_guard)

    def test_circuit_breaker_emits_trip_and_recovery_spans(self):
        """Roadmap v2.0 §2.2.A: CircuitBreaker phát sinh TraceSpan khi trip và khi recover."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            rec = BlackboxRecorder(log_dir=Path(td))
            cb = CircuitBreaker("etabs_test", failure_threshold=2, recovery_timeout=0.1, recorder=rec)

            # Thất bại lần 1: chưa trip
            cb.record_failure()
            self.assertEqual(len(rec.traces), 0)

            # Thất bại lần 2: trip sang OPEN -> phải có span TRIP_CIRCUIT:etabs_test
            cb.record_failure()
            self.assertEqual(cb.state, CircuitState.OPEN)
            self.assertEqual(len(rec.traces), 1)
            trip_span = rec.traces[0]
            self.assertEqual(trip_span.action, "TRIP_CIRCUIT:etabs_test")
            self.assertEqual(trip_span.status, "CIRCUIT_OPEN")
            self.assertEqual(trip_span.metadata["consecutive_failures"], 2)

            # Đợi hạ nhiệt -> chuyển sang HALF_OPEN
            time.sleep(0.15)
            self.assertTrue(cb.allow_execution())
            self.assertEqual(cb.state, CircuitState.HALF_OPEN)

            # Phục hồi thành công -> phải có span CIRCUIT_RECOVERED:etabs_test
            cb.record_success()
            self.assertEqual(cb.state, CircuitState.CLOSED)
            self.assertEqual(len(rec.traces), 2)
            recov_span = rec.traces[1]
            self.assertEqual(recov_span.action, "CIRCUIT_RECOVERED:etabs_test")
            self.assertEqual(recov_span.status, "SUCCESS")

    def test_blackbox_trace_rotation(self):
        """Roadmap v2.0 §2.2: BlackboxRecorder hỗ trợ xoay vòng dọn dẹp file trace cũ."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            rec = BlackboxRecorder(log_dir=Path(td), max_trace_files=3)
            trace_dir = Path(td) / "traces"
            trace_dir.mkdir(parents=True, exist_ok=True)

            # Tạo 5 file trace giả lập với timestamp khác nhau
            now = time.time()
            for i in range(5):
                f = trace_dir / f"trace_2026010{i}.jsonl"
                f.write_text(f'{{"trace_id": "T{i}"}}\n', encoding="utf-8")
                # Đặt st_mtime cách nhau 100 giây
                os.utime(f, (now - (10 - i) * 100, now - (10 - i) * 100))

            # Giới hạn max_files=3 -> dọn 2 file cũ nhất
            removed = rec.rotate_traces(max_files=3, max_age_days=30)
            self.assertEqual(len(removed), 2)
            self.assertEqual(len(list(trace_dir.glob("trace_*.jsonl"))), 3)

            # Thử dọn theo max_age_days = 0.0001 ngày (vài giây) -> dọn hết
            removed_all = rec.rotate_traces(max_files=10, max_age_days=0.00001)
            self.assertEqual(len(removed_all), 3)
            self.assertEqual(len(list(trace_dir.glob("trace_*.jsonl"))), 0)

    def test_lessons_repository_does_not_pollute_production_file(self):
        """BUG-012: test không được ghi vào file bài học production."""
        import tempfile
        prod = AGENTS_ROOT / "_SHARED" / "memory" / "projects" / "global_lessons_learned.json"
        before = prod.read_text(encoding="utf-8") if prod.exists() else None
        with tempfile.TemporaryDirectory() as td:
            repo = LessonsLearnedRepository(storage_dir=Path(td))
            repo.add_lesson(LessonLearned(
                lesson_id="LL-ISOLATED", project_code="T", category="BEAM",
                issue_description="x", root_cause="y", preventive_solution="z"
            ))
        after = prod.read_text(encoding="utf-8") if prod.exists() else None
        self.assertEqual(before, after)


if __name__ == '__main__':
    print("=" * 80)
    print(" CHẠY BỘ KIỂM THỬ: HỆ THỐNG KIỂM SOÁT VẬN HÀNH & ĐỒ THỊ TRI THỨC (v2.0)")
    print("=" * 80)
    unittest.main(verbosity=2)
