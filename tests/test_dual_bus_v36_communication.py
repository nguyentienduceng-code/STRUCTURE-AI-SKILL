# -*- coding: utf-8 -*-
"""Unit tests for Dual-Agent Bridge v3.6 (capabilities, lifecycle state, work_ticket preservation, blocked-return NEED_REVIEW)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import sync_bus  # noqa: E402


class DualBusV36CommunicationTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.mem_dir = self.root / ".agents" / "memory"
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.bus_path = self.mem_dir / "DUAL_AGENT_BUS.json"
        self.memo_path = self.mem_dir / "DUAL_AGENT_HANDOFF_MEMO.md"
        self.ptr_path = self.mem_dir / "_CA_HIEN_TAI.md"
        self.lock_path = self.root / "locks" / "bus.lock"
        self.receipts_dir = self.root / "receipts"

        patches = [
            patch.object(sync_bus, "WORKSPACE_ROOT", self.root),
            patch.object(sync_bus, "BUS_PATH", self.bus_path),
            patch.object(sync_bus, "MEMO_PATH", self.memo_path),
            patch.object(sync_bus, "ACTIVE_POINTER_PATH", self.ptr_path),
            patch.object(sync_bus, "LOCK_PATH", self.lock_path),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

        p_rec = patch.object(sync_bus, "_receipts_dir", return_value=self.receipts_dir)
        p_rec.start()
        self.addCleanup(p_rec.stop)

    def test_detect_environment_capabilities_fields(self) -> None:
        caps = sync_bus.detect_environment_capabilities(self.root)
        self.assertEqual(caps["schema_version"], "3.6")
        self.assertIn("accoreconsole_available", caps)
        self.assertIn("accoreconsole_readonly_cmd", caps)
        self.assertIn("--audit-only", caps["accoreconsole_readonly_cmd"])
        self.assertFalse(caps["sheet_set_manager_native_dst"])
        self.assertFalse(caps["live_peer_messaging_between_tabs"])

    def test_blocked_return_need_review_without_force_releases_lock(self) -> None:
        initial = {
            "work_ticket": {
                "bus_version": "3.4",
                "task_id": "TEST_S3",
                "status": "IN_PROGRESS",
                "dispatch_2d": {"primary_skill": "Design_Evaluation", "use_dual_agent_bus": True},
            },
            "project_context": {
                "project_code": "03_Sprint2_KetQua_NeChu_CAD",
                "project_purpose": "Kiem tra",
                "action_type": "CAD",
            },
            "last_updated_by": "GEMINI",
            "timestamp": "2026-11-24T22:00:00+07:00",
            "handoff_status": "IN_PROGRESS",
            "current_holder": "CLAUDE",
            "summary": "Dang lam",
            "artifacts_modified": [".agents/memory/DUAL_AGENT_BUS.json"],
            "next_action_for_partner": {
                "target_agent": "CLAUDE",
                "task_description": "Verify CAD",
                "command": "Verify CAD",
                "acceptance_criteria": [],
            },
            "Verification_Status": "IN_PROGRESS",
        }
        self.bus_path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")

        res = sync_bus.request_review(
            agent="CLAUDE",
            summary="Mâu thuẫn số lượng 7 vs 8 workbook và thiếu Sheet Set Manager",
            next_agent="GEMINI",
            blocked_return=True,
            blocking_questions=["Chốt 7 hay 8 workbook?", "Cần DuAn.dst native hay manifest?"],
            task_description="Chốt phạm vi trước khi tạo gói",
        )
        self.assertEqual(res["handoff_status"], "NEED_REVIEW")
        self.assertEqual(res["current_holder"], "IDLE")
        self.assertEqual(res["Verification_Status"], "BLOCKED_RETURN")
        self.assertEqual(res["next_action_for_partner"]["target_agent"], "GEMINI")
        self.assertEqual(len(res["next_action_for_partner"]["blocking_questions"]), 2)
        self.assertIn("BLOCKED_RETURN", self.memo_path.read_text(encoding="utf-8"))
        self.assertIn("Năng lực môi trường (v3.6)", self.ptr_path.read_text(encoding="utf-8"))

    def test_auto_handoff_preserves_work_ticket_and_lifecycle_state(self) -> None:
        seed_bus = {
            "work_ticket": {
                "bus_version": "3.4",
                "task_id": "KEEP_ME",
                "status": "PENDING",
                "dispatch_2d": {"primary_skill": "Design_Evaluation", "use_dual_agent_bus": True},
            },
            "project_context": {"project_code": "03_Sprint2_KetQua_NeChu_CAD"},
        }
        self.bus_path.write_text(json.dumps(seed_bus, ensure_ascii=False, indent=2), encoding="utf-8")

        with patch.object(sync_bus, "_route_handoff", return_value=None):
            res = sync_bus.auto_handoff(
                sender="GEMINI",
                target="CLAUDE",
                project_code="03_Sprint2_KetQua_NeChu_CAD",
                action_type="CODE",
                summary="Nâng cấp cầu nối v3.6",
                task_description="Xác minh cầu nối v3.6",
                files=[".agents/tools/sync_bus.py"],
                auto_detect_files=False,
                artifact_lifecycle_state="NATIVE_VALIDATED",
            )
        self.assertIn("work_ticket", res)
        self.assertEqual(res["work_ticket"]["task_id"], "KEEP_ME")
        self.assertEqual(res["project_context"]["artifact_lifecycle_state"], "NATIVE_VALIDATED")
        self.assertIn("environment_capabilities", res)
        self.assertTrue(sync_bus.validate_bus_payload(res)[0])

    def test_need_review_and_complete_accept_evidence_files(self) -> None:
        preview = self.root / "out" / "preview.png"
        report = self.root / ".agents" / "memory" / "audits" / "03_sprint2_ketqua_nechu_cad" / "claude" / "R2_RESULT.md"
        preview.parent.mkdir(parents=True, exist_ok=True)
        report.parent.mkdir(parents=True, exist_ok=True)
        preview.write_bytes(b"png-bytes")
        report.write_text("# R2_RESULT.md\n", encoding="utf-8")

        initial = {
            "project_context": {"project_code": "03_Sprint2_KetQua_NeChu_CAD", "project_purpose": "Kiem tra", "action_type": "CAD"},
            "last_updated_by": "GEMINI",
            "timestamp": "2026-11-26T10:00:00+07:00",
            "handoff_status": "IN_PROGRESS",
            "current_holder": "CLAUDE",
            "summary": "Dang kiem tra CAD",
            "artifacts_modified": [".agents/memory/DUAL_AGENT_BUS.json"],
            "next_action_for_partner": {
                "target_agent": "CLAUDE",
                "task_description": "Verify CAD",
                "command": "Verify CAD",
                "acceptance_criteria": [],
            },
            "Verification_Status": "IN_PROGRESS",
        }
        self.bus_path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")

        rev = sync_bus.request_review(
            agent="CLAUDE",
            summary="Đã kiểm tra CAD và đính kèm bằng chứng preview.",
            next_agent="GEMINI",
            files=[str(preview), ".agents/memory/DUAL_AGENT_BUS.json"],
            evidence_files=[str(preview)],
            report_file=str(report),
            check_evidence_on_disk=True,
        )
        self.assertEqual(rev["handoff_status"], "NEED_REVIEW")
        self.assertEqual(rev["current_holder"], "IDLE")
        self.assertEqual(rev["next_action_for_partner"]["target_agent"], "GEMINI")
        self.assertEqual(rev["next_action_for_partner"]["evidence_files"], ["out/preview.png"])

        comp = sync_bus.complete_task(
            agent="GEMINI",
            summary="Đã nghiệm thu xong với bằng chứng trên đĩa.",
            files=[str(preview)],
            evidence_files=[str(preview)],
            report_file=str(report),
            check_evidence_on_disk=True,
        )
        self.assertEqual(comp["handoff_status"], "COMPLETED")
        self.assertEqual(comp["current_holder"], "IDLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
