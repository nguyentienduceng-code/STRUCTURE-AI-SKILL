"""Regression Test Suite for 2D Cognitive Dispatcher & Dual-Plane Bus v3.4.

Compatible with ``unittest`` discovery and ``_auto_register_unregistered()`` in
``run_all_tests.py``. Uses a class-scoped temporary workspace for deterministic routing and isolated product and relay checks.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure sibling modules resolve cleanly when invoked from run_all_tests.py
_THIS_DIR = Path(__file__).resolve().parent
_DISPATCHER_DIR = _THIS_DIR.parent / "skills" / "Global_Dispatcher"
for _p in (_DISPATCHER_DIR, _THIS_DIR):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

if "intent_classifier" in sys.modules and not hasattr(sys.modules["intent_classifier"], "IntentClassifier2D"):
    del sys.modules["intent_classifier"]

from intent_classifier import IntentClassifier2D, MODE_PRODUCT, MODE_SOLO, MODE_SYSTEM
from product_deliverable_gate import JargonLinter, ProductDeliverableGate
from sync_bus_2d_patch import SyncBus2DAdapter, approve_drafts


class TestDispatcher2DModes(unittest.TestCase):
    """End-to-end verification of 2D routing, project resolution, and Deliverable Gate."""

    _tmp_root: Path
    _workspace: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_root = Path(tempfile.mkdtemp(prefix="dispatcher_2d_test_"))
        cls._workspace = cls._tmp_root / "Google_AI_Studio"
        (cls._workspace / "01_Projects" / "17_LIEN_CHIEU_DA_NANG" / "04_Deliverables_ToTrinh").mkdir(
            parents=True
        )
        (cls._workspace / "01_Structural_Projects" / "16.BPTC_SUNRISE_Q12" / "04_Deliverables_ToTrinh").mkdir(
            parents=True
        )
        (cls._workspace / "01_Structural_Projects" / "18_SUNRISE_TOWER_B" / "04_Deliverables_ToTrinh").mkdir(
            parents=True
        )
        (cls._workspace / "01_Structural_Projects" / "05_MONT_ALP" / "04_Deliverables_ToTrinh").mkdir(
            parents=True
        )
        (cls._workspace / ".agents" / "memory" / "audits").mkdir(parents=True)
        cls.classifier = IntentClassifier2D(workspace_root=cls._workspace)
        cls.adapter = SyncBus2DAdapter(workspace_root=cls._workspace, classifier=cls.classifier)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls._tmp_root, ignore_errors=True)

    def approval(self, work):
        draft = self._workspace / (work["request_id"] + ".txt")
        draft.write_text("Kết quả trình duyệt", encoding="utf-8")
        return approve_drafts(work, "Đồng ý", [draft])

    def test_01_product_collab_lien_chieu(self) -> None:
        prompt = "Rà soát tờ trình và thuyết minh khảo sát địa chất Liên Chiểu Đà Nẵng xuất hồ sơ hoàn chỉnh"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.domain_skill, "SKILL_GEOTECH")
        self.assertEqual(res.engagement_mode, MODE_PRODUCT)
        self.assertTrue(res.use_dual_agent_bus)
        self.assertEqual(res.claude_role, "LEAD_AUDITOR_TCVN")
        self.assertFalse(res.needs_project_confirmation)
        self.assertIsNotNone(res.deliverable_dir_posix)
        self.assertIn("17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh", res.deliverable_dir_posix or "")

    def test_02_system_upgrade_fixes_zero_confidence(self) -> None:
        prompt = "Nâng cấp hệ thống Dual Agent lên v3.3 thêm tính năng kiểm tra tự động"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_SYSTEM)
        self.assertEqual(res.domain_skill, "SKILL_SYSTEM_ENGINEERING")
        self.assertGreater(res.domain_confidence, 0.5)
        self.assertGreater(res.mode_confidence, 0.5)
        self.assertEqual(res.claude_role, "SOFTWARE_ARCHITECT")
        self.assertFalse(res.enforce_deliverable_gate)
        self.assertFalse(res.enforce_jargon_linter)

    def test_03_solo_execution_disables_bus_ipc(self) -> None:
        prompt = "Giải thích nhanh công thức tính độ võng sàn BTCT theo TCVN 5574:2018"
        res = self.classifier.classify(prompt)
        self.assertIn(res.domain_skill, ("Structural_Design_Engineer", "SKILL_STRUCTURAL_RC"))
        self.assertEqual(res.engagement_mode, MODE_SOLO)
        self.assertFalse(res.use_dual_agent_bus)
        self.assertEqual(res.claude_role, "NONE")

        payload = self.adapter.prepare_handover_payload(
            prompt=prompt,
            task_id="T-SOLO-01",
            task_title="Tra cứu độ võng sàn",
        )
        self.assertIsNone(payload)

    def test_04_hybrid_project_script_patch_stays_product_collab(self) -> None:
        prompt = "Sửa script xuất thuyết minh dự án Liên Chiểu bị lỗi tràn bảng rồi xuất lại file Word"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_PRODUCT)
        self.assertTrue(res.allow_script_patch)
        self.assertFalse(res.needs_project_confirmation)
        self.assertEqual(res.claude_role, "LEAD_AUDITOR_TCVN")
        self.assertIn("17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh", res.deliverable_dir_posix or "")

    def test_05_multi_root_discovers_structural_projects(self) -> None:
        prompt = "Xuất hồ sơ thuyết minh kết cấu dự án Mont Alp hoàn chỉnh"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_PRODUCT)
        self.assertFalse(res.needs_project_confirmation)
        self.assertIn("01_Structural_Projects/05_MONT_ALP/04_Deliverables_ToTrinh", res.deliverable_dir_posix or "")

    def test_06_ambiguous_project_triggers_confirmation(self) -> None:
        prompt = "Xuất hồ sơ thuyết minh dự án Sunrise hoàn chỉnh"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_PRODUCT)
        self.assertTrue(res.needs_project_confirmation)
        self.assertIsNotNone(res.project_resolution)
        self.assertEqual(res.project_resolution["status"], "AMBIGUOUS")
        self.assertGreaterEqual(len(res.project_resolution["candidates"]), 2)

        payload = self.adapter.prepare_handover_payload(
            prompt=prompt,
            task_id="T-AMBIG-01",
            task_title="Xuất hồ sơ Sunrise",
        )
        self.assertIsNotNone(payload)
        self.assertEqual(payload["status"], "NEEDS_PROJECT_CONFIRMATION")

    def test_07_low_confidence_defaults_safely_to_solo(self) -> None:
        prompt = "Xem giúp anh phương án này xem ổn chưa nhé"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_SOLO)
        self.assertFalse(res.use_dual_agent_bus)
        self.assertLess(res.mode_confidence, 0.35)

    def test_08_explicit_override_flags(self) -> None:
        res_sys = self.classifier.classify("/sys Kiểm tra lại toàn bộ quy trình Liên Chiểu")
        self.assertEqual(res_sys.engagement_mode, MODE_SYSTEM)
        self.assertEqual(res_sys.mode_confidence, 1.0)

        res_solo = self.classifier.classify("/solo Rà soát nhanh tờ trình Liên Chiểu")
        self.assertEqual(res_solo.engagement_mode, MODE_SOLO)
        self.assertFalse(res_solo.use_dual_agent_bus)

    def test_09_core_path_reference_forces_system_upgrade(self) -> None:
        prompt = "Cập nhật hàm handover trong .agents/tools/sync_bus.py để hỗ trợ v3.4"
        res = self.classifier.classify(prompt)
        self.assertEqual(res.engagement_mode, MODE_SYSTEM)
        self.assertGreaterEqual(res.mode_confidence, 0.9)

    def test_10_deliverable_gate_blocks_stray_md_only(self) -> None:
        prompt = "Rà soát tờ trình khảo sát địa chất Liên Chiểu Đà Nẵng xuất hồ sơ hoàn chỉnh"
        payload = self.adapter.prepare_handover_payload(
            prompt=prompt,
            task_id="T-GATE-MD",
            task_title="Thẩm tra Liên Chiểu (Stray MD)",
        )
        self.assertIsNotNone(payload)
        stray_md = self._workspace / ".agents" / "memory" / "audits" / "stray_audit.md"
        stray_md.write_text("# Draft audit notes", encoding="utf-8")

        result = self.adapter.complete_handover_with_gate(
            payload,
            user_report_vi="Đã thẩm tra xong, xem file nháp tại .agents/memory/audits/stray_audit.md, đạt yêu cầu.",
        )
        self.assertEqual(result["status"], "BLOCKED_GATE")
        self.assertEqual(result["human_handoff"]["deliverable_gate_status"], "BLOCKED_MISSING_DELIVERABLE")
        self.assertIn("file nháp .md", result["human_handoff"]["deliverable_gate_message_vi"])

    def test_11_deliverable_gate_blocks_jargon_and_passes_clean_report(self) -> None:
        prompt = "Rà soát tờ trình khảo sát địa chất Liên Chiểu Đà Nẵng xuất hồ sơ hoàn chỉnh"
        payload = self.adapter.prepare_handover_payload(
            prompt=prompt,
            task_id="T-GATE-DOCX",
            task_title="Thẩm tra Liên Chiểu (DOCX)",
        )
        self.assertIsNotNone(payload)

        deliv_file = (
            self._workspace
            / "01_Projects"
            / "17_LIEN_CHIEU_DA_NANG"
            / "04_Deliverables_ToTrinh"
            / "ToTrinh_DiaChat_LienChieu_Rev02.docx"
        )
        from docx import Document
        approval = self.approval(payload)
        draft = Document()
        draft.add_paragraph("Dự án 17_LIEN_CHIEU_DA_NANG")
        draft.save(deliv_file)

        # 11a. Dev jargon must be blocked even when real .docx exists
        blocked = self.adapter.complete_handover_with_gate(
            payload,
            user_report_vi="Đã unpack SSOT và xác nhận SHA-256 receipt gate=PASS cho file .docx.",
        )
        self.assertEqual(blocked["status"], "BLOCKED_GATE")
        self.assertEqual(blocked["human_handoff"]["deliverable_gate_status"], "BLOCKED_JARGON_VIOLATION")

        # 11b. Clean 3-point Vietnamese technical report must pass & record silent SHA-256
        clean_report = (
            "1. Đã sửa: Chuẩn hóa bảng chỉ tiêu cơ lý đất theo TCVN 9362:2012 và căn chỉnh thể thức Nghị định 30.\n"
            "2. File hoàn chỉnh: 01_Projects\\17_LIEN_CHIEU_DA_NANG\\04_Deliverables_ToTrinh\\ToTrinh_DiaChat_LienChieu_Rev02.docx\n"
            "3. Kết luận: Số liệu đạt yêu cầu bàn giao Chủ đầu tư."
        )
        passed = self.adapter.complete_handover_with_gate(payload, user_report_vi=clean_report, approval=approval)
        self.assertEqual(passed["status"], "COMPLETED")
        self.assertEqual(passed["human_handoff"]["deliverable_gate_status"], "PASS")
        self.assertEqual(passed["human_handoff"]["verified_files"], ["ToTrinh_DiaChat_LienChieu_Rev02.docx"])
        self.assertEqual(len(passed["bus_meta"]["evidence_hashes"]), 1)

    def test_12_system_upgrade_bypasses_product_gate(self) -> None:
        prompt = "Nâng cấp hệ thống Dual Agent lên v3.3 thêm tính năng kiểm tra tự động"
        payload = self.adapter.prepare_handover_payload(
            prompt=prompt,
            task_id="T-SYS-PASS",
            task_title="Nâng cấp Dual Agent v3.4",
        )
        self.assertIsNotNone(payload)
        done = self.adapter.complete_handover_with_gate(
            payload,
            user_report_vi="Refactored sync_bus.py with atomic lock and SHA-256 receipts, 46/46 pytest PASS.",
        )
        self.assertEqual(done["status"], "COMPLETED")
        self.assertEqual(done["human_handoff"]["deliverable_gate_status"], "BYPASSED_SYSTEM_MODE")

    def test_13_same_product_four_choices_and_project_mismatch(self):
        from docx import Document
        prompt = "Xuất tờ trình cho Mont Alp, tham khảo .agents/AGENTS.md"
        for choice in ("AUTO", "CLAUDE_ONLY", "GEMINI_ONLY", "DUAL"):
            with self.subTest(choice=choice):
                name = f"{choice}.docx"
                work = self.adapter.prepare_handover_payload(
                    prompt, choice, prompt, agent_selection=choice,
                    expected_files=[name], project_identity="Công trình Mont Alp",
                )
                route = work["dispatch_2d"]
                self.assertEqual(route["engagement_mode"], MODE_PRODUCT)
                self.assertTrue(route["enforce_deliverable_gate"])
                self.assertEqual(route["use_dual_agent_bus"], choice in {"AUTO", "DUAL"})
                self.assertIn("approve", [s["step"] for s in route["execution_plan"]])
                file = Path(route["deliverable_dir_posix"]) / name
                report = f"1. Đã rà soát bố cục.\n2. File {file}\n3. Đạt."
                approval = self.approval(work)
                doc = Document()
                doc.add_paragraph("Công trình khác")
                doc.save(file)
                result = self.adapter.complete_handover_with_gate(work, report, approval=approval)
                self.assertEqual(result["human_handoff"]["deliverable_gate_status"], "BLOCKED_PROJECT_IDENTITY")
                doc.add_paragraph("Công trình Mont Alp")
                doc.save(file)
                result = self.adapter.complete_handover_with_gate(work, report, approval=approval)
                self.assertEqual(result["status"], "COMPLETED")
                self.assertEqual(result["human_handoff"]["verification_level"], "SELF_CHECKED")

    def test_14_project_preference_and_per_request_overrides(self):
        project = self._workspace / "01_Structural_Projects/05_MONT_ALP"
        pref = project / ".agent-selection"
        pref.write_text("GEMINI_ONLY", encoding="utf-8")
        self.addCleanup(pref.unlink)
        prompt = "Xuất hồ sơ dự án Mont Alp"
        self.assertEqual(self.classifier.classify(prompt).agent_selection, "GEMINI_ONLY")
        for suffix, expected in [
            ("riêng ca này chỉ dùng Claude", "CLAUDE_ONLY"),
            ("chỉ muốn sài Germini", "GEMINI_ONLY"),
            ("dùng Claude và Gemini", "DUAL"), ("tự động chọn tác tử", "AUTO"),
            ('theo ví dụ “chỉ dùng Claude”', "GEMINI_ONLY"),
        ]:
            self.assertEqual(self.classifier.classify(prompt + ", " + suffix).agent_selection, expected)
        with self.assertRaises(ValueError):
            self.classifier.classify(prompt + ", chỉ dùng Claude, chỉ dùng Gemini")

    def test_15_single_agent_excludes_bus_and_wrong_actor(self):
        bus = self._workspace / "isolated-bus.json"
        adapter = SyncBus2DAdapter(self._workspace, bus)
        for choice, actor in (("CLAUDE_ONLY", "CLAUDE"), ("GEMINI_ONLY", "GEMINI")):
            for cmd in ("/solo giải thích", "/sys nâng cấp skill", "/prod xuất tờ trình Mont Alp"):
                work = adapter.prepare_handover_payload(cmd, cmd, cmd, agent_selection=choice, write_to_bus=True)
                owners = {s["owner"] for s in work["dispatch_2d"]["execution_plan"]}
                self.assertLessEqual(owners, {actor, "USER"})
                with self.assertRaises(ValueError):
                    adapter.complete_handover_with_gate(work, "", agent_name="OTHER")
                adapter.complete_handover_with_gate(work, "Đã kiểm tra", write_to_bus=True)
                self.assertFalse(bus.exists())

    def test_16_reference_flags_ambiguous_target_and_patch_rights(self):
        for ref in (".agents/AGENTS.md", ".agents\\\\skills\\\\STANDARDS_LOCK.md"):
            prompt = f"Sửa tờ trình Mont Alp, tham khảo {ref}, chỉ dùng Claude"
            work = self.adapter.prepare_handover_payload(prompt, "T", prompt)
            self.assertEqual(work["dispatch_2d"]["engagement_mode"], MODE_PRODUCT)
            self.assertFalse(work["dispatch_2d"]["allow_script_patch"])
            self.assertIn("Dùng script hiện có", work["human_handoff"]["handover_prompt"])
        self.assertEqual(self.classifier.classify("Hoàn thiện bộ 05_MONT_ALP").engagement_mode, MODE_PRODUCT)
        self.assertNotEqual(self.classifier.classify("Giải thích cú pháp /prod và /solo").engagement_mode, MODE_PRODUCT)
        with self.assertRaises(ValueError):
            self.classifier.classify("/sys /prod làm hồ sơ")
        work = self.adapter.prepare_handover_payload("/prod xuất tờ trình Sunrise", "T", "T", agent_selection="GEMINI_ONLY")
        self.assertEqual(self.adapter.complete_handover_with_gate(work, "")["status"], "NEEDS_PROJECT_CONFIRMATION")

    def test_17_independent_review_must_match_current_files(self):
        from docx import Document
        work = self.adapter.prepare_handover_payload(
            "Lập tờ trình Mont Alp", "review", "review", agent_selection="CLAUDE_ONLY",
            expected_files=["review.docx"], independent_review_required=True,
        )
        file = Path(work["dispatch_2d"]["deliverable_dir_posix"]) / "review.docx"
        approval = self.approval(work)
        doc = Document()
        doc.add_paragraph("05_MONT_ALP")
        doc.save(file)
        report = f"Đã rà soát. File {file}. Kết luận đạt."
        from functools import partial
        self.assertEqual(self.adapter.complete_handover_with_gate(work, report)["status"], "AWAITING_USER_APPROVAL")
        check = partial(self.adapter.complete_handover_with_gate, approval=approval)
        self.assertEqual(check(work, report)["status"], "AWAITING_INDEPENDENT_REVIEW")
        hashes = work["bus_meta"]["evidence_hashes"].copy()
        self.assertEqual(check(work, report, reviewed_by="CLAUDE", reviewed_hashes=hashes)["status"], "AWAITING_INDEPENDENT_REVIEW")
        reviewed = check(work, report, reviewed_by="Kỹ sư A", reviewed_hashes=hashes)
        self.assertEqual(reviewed["human_handoff"]["verification_level"], "INDEPENDENT")
        doc.add_paragraph("Số liệu đã sửa")
        doc.save(file)
        self.assertEqual(check(work, report, reviewed_by="Kỹ sư A", reviewed_hashes=hashes)["status"], "AWAITING_INDEPENDENT_REVIEW")
        self.assertFalse(JargonLinter().lint("All done.").passed)
        self.assertFalse(JargonLinter().lint("Đã rà soát file theo TCVN.").passed)


    def test_18_approval_binds_response_ticket_and_draft(self):
        from sync_bus_2d_patch import current_approval
        work = self.adapter.prepare_handover_payload("Lập tờ trình Mont Alp", "A", "A")
        approval = self.approval(work)
        draft = Path(next(iter(approval["draft_hashes"])))
        self.assertTrue(current_approval(work, approval, []))
        for key, value in (("response", "Không đồng ý"), ("request_id", "other"), ("draft_hashes", {})):
            self.assertFalse(current_approval(work, {**approval, key: value}, []))
        for response in ("OK nhưng cần sửa", "Để tôi xem lại", ""):
            with self.assertRaises(ValueError):
                approve_drafts(work, response, [draft])
        draft.write_text("Đã điều chỉnh sau khi duyệt", encoding="utf-8")
        self.assertFalse(current_approval(work, approval, []))

    def test_19_cli_product_cycle_and_shared_bus(self):
        from docx import Document
        ws = self._workspace
        folder = ws / "01_Structural_Projects/05_MONT_ALP"
        bus = ws / ".agents/memory/DUAL_AGENT_BUS.json"
        planner = _DISPATCHER_DIR / "dispatch_task.py"
        relay = _THIS_DIR.parent / "tools/sync_bus.py"
        env = dict(os.environ, DUAL_AGENT_WORKSPACE=str(ws), LOCALAPPDATA=str(ws / "local"),
                   PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")

        def invoke(script, *args, success=True):
            proc = subprocess.run([sys.executable, "-B", str(script), *map(str, args)], env=env,
                                  cwd=ws, capture_output=True, text=True, encoding="utf-8", timeout=45)
            self.assertEqual(proc.returncode == 0, success, proc.stderr or proc.stdout)
            return proc.stdout

        invoke(planner, "set-default", "--workspace", ws, "--project-dir", folder, "--agent-selection", "CLAUDE_ONLY")
        self.addCleanup((folder / ".agent-selection").unlink)
        for choice, actor in [("DUAL", "CLAUDE"), ("CLAUDE_ONLY", "CLAUDE"),
                              ("GEMINI_ONLY", "GEMINI"), ("AUTO", "CLAUDE")]:
            with self.subTest(choice=choice):
                ticket = ws / (choice + ".json")
                record = ws / (choice + ".approval.json")
                draft = ws / (choice + ".draft.txt")
                report = ws / (choice + ".report.txt")
                output = folder / "04_Deliverables_ToTrinh" / (choice + ".docx")
                flags = [] if choice == "CLAUDE_ONLY" else ["--agent-selection", choice]
                invoke(planner, "prepare", "--workspace", ws, "--prompt", "Lập tờ trình Mont Alp xuất Word",
                       "--ticket", ticket, "--expected-file", output.name, "--project-identity", "Dự án thử", *flags)
                work = json.loads(ticket.read_text(encoding="utf-8"))
                self.assertEqual(work["dispatch_2d"]["agent_selection"], choice)
                args = ("--auto", "--sender", "GEMINI", "--target", "CLAUDE", "--dispatch-ticket", ticket,
                        "--summary", "Chuyển hồ sơ", "--task", "Rà soát hồ sơ", "--action-type", "META")
                if choice == "DUAL":
                    invoke(relay, *args, "--project", "WRONG_PROJECT", success=False)
                old_bus = bus.read_bytes() if bus.exists() else None
                invoke(relay, *args)
                paired = choice in ("AUTO", "DUAL")
                if paired:
                    published = json.loads(bus.read_text(encoding="utf-8"))
                    self.assertEqual(published["work_ticket"]["request_id"], work["request_id"])
                    self.assertEqual(published["project_context"]["project_code"], folder.name)
                else:
                    self.assertEqual(bus.read_bytes(), old_bus)
                draft.write_text("Dự án thử — kết quả kiểm tra", encoding="utf-8")
                invoke(planner, "approve", "--ticket", ticket, "--response", "Đồng ý",
                       "--draft", draft, "--approval-record", record)
                doc = Document()
                doc.add_paragraph(draft.read_text(encoding="utf-8"))
                doc.save(output)
                summary = f"1. Đã rà soát.\n2. File {output}.\n3. Kết luận đạt."
                report.write_text(summary, encoding="utf-8")
                result = json.loads(invoke(planner, "check", "--ticket", ticket, "--report", report,
                                           "--actor", actor, "--approval-record", record))
                self.assertEqual(result["human_handoff"]["verification_level"], "SELF_CHECKED")
                if paired:
                    complete = ("--complete", "--agent", actor, "--summary", summary)
                    invoke(relay, *complete, success=False)
                    invoke(relay, *complete, "--approval-record", record)
                    self.assertEqual(json.loads(bus.read_text(encoding="utf-8"))["handoff_status"], "COMPLETED")
                else:
                    self.assertEqual(bus.read_bytes(), old_bus)

    def test_20_agent_directives_preserve_skills_order_and_review(self):
        for directive in ("chỉ dùng Claude", "chỉ dùng Gemini", "dùng Claude và Gemini", "Claude + Gemini"):
            prompt = f"Tính lại dầm rồi lập tờ trình Mont Alp, {directive}"
            work = self.adapter.prepare_handover_payload(prompt, "chain", prompt)
            self.assertEqual(work["status"], "QUEUED")
            dispatch = work["dispatch_2d"]
            stages = dispatch["skill_workflow"]["stages"]
            self.assertEqual([s["skill"] for s in stages], ["Structural_Design_Engineer", "Design_Evaluation"])
            owners = [s["owner"] for s in stages]
            expected = {"chỉ dùng Claude": ["CLAUDE"] * 2, "chỉ dùng Gemini": ["GEMINI"] * 2}
            self.assertEqual(owners, expected.get(directive, ["GEMINI", "CLAUDE"]))
            self.assertTrue(stages[0]["requires_review_gate"])
            self.assertEqual(stages[1]["depends_on"], [1])
            self.assertTrue(all(Path(path).is_file() for path in dispatch["skill_files"]))
            self.assertEqual([Path(path).parent.name for path in dispatch["skill_files"]], [s["skill"] for s in stages])
        prompt = "/sys nâng cấp bộ điều phối, chỉ dùng Gemini"
        work = self.adapter.prepare_handover_payload(prompt, "sys", prompt)
        self.assertEqual(work["dispatch_2d"]["primary_skill"], "Global_Dispatcher")

    def test_21_match_identity_and_required_formats_in_real_files(self):
        import ezdxf
        import fitz
        import openpyxl
        names = ["contract.xlsx", "contract.pdf", "contract.dxf"]
        work = self.adapter.prepare_handover_payload(
            "Lập tờ trình Mont Alp xuất Excel và PDF và DXF", "formats", "formats",
            agent_selection="GEMINI_ONLY", expected_files=names, project_identity="MON-12",
        )
        self.assertCountEqual(work["dispatch_2d"]["required_extensions"], [".xlsx", ".pdf", ".dxf"])
        approval = self.approval(work)
        folder = Path(work["dispatch_2d"]["deliverable_dir_posix"])
        excel, pdf, dxf = [folder / name for name in names]
        book = openpyxl.Workbook()
        book.active["A1"] = "Dự án MON-12"
        book.save(excel)
        book.close()
        with fitz.open() as doc:
            doc.new_page().insert_text((70, 70), "Project MON-12")
            doc.save(pdf)
        report = f"Đã rà soát. File {excel}, {pdf}, {dxf}. Kết luận đạt."
        def check():
            return self.adapter.complete_handover_with_gate(work, report, agent_name="GEMINI", approval=approval)
        self.assertEqual(check()["status"], "BLOCKED_GATE")
        drawing = ezdxf.new()
        label = drawing.modelspace().add_text("Project MON-120")
        drawing.saveas(dxf)
        self.assertEqual(check()["human_handoff"]["deliverable_gate_status"], "BLOCKED_PROJECT_IDENTITY")
        label.dxf.text = "Project MON-12"
        drawing.saveas(dxf)
        self.assertEqual(check()["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
