# -*- coding: utf-8 -*-
"""Tests for Unified Antigravity & Claude Code Dual-Agent Bus Auto-Pickup & DWG Guard Hook."""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
AGENTS_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import antigravity_dual_bus_hook as hook  # noqa: E402
import claude_safety_hook  # noqa: E402


class AntigravityDualBusHookTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.bus_path = self.root / ".agents" / "memory" / "DUAL_AGENT_BUS.json"
        self.state_path = self.root / "locks" / "bus_injected_sessions.json"
        self.bus_path.parent.mkdir(parents=True, exist_ok=True)
        self.project = self.root / "01_Projects" / "Case"
        self.out = self.project / "04_Deliverables_ToTrinh"
        self.out.mkdir(parents=True, exist_ok=True)
        self.original = self.project / "Original.DWG"
        self.original.write_bytes(b"original-dwg")

        for attr, val in (("ROOT", self.root), ("BUS_PATH", self.bus_path), ("STATE_PATH", self.state_path)):
            p = patch.object(hook, attr, val)
            p.start()
            self.addCleanup(p.stop)

    def _write_bus(self, *, status: str = "PENDING", holder: str = "IDLE", target: str = "CLAUDE", req_id: str = "req-001") -> None:
        payload = {
            "project_context": {"project_code": "03_Sprint2_KetQua_NeChu_CAD"},
            "last_updated_by": "GEMINI",
            "timestamp": "2026-11-24T09:35:29+07:00",
            "handoff_status": status,
            "current_holder": holder,
            "summary": "Đã xuất 8 bản vẽ KC.02-KC.09 đạt PASS Bộ lọc 8.",
            "next_action_for_partner": {
                "target_agent": target,
                "task_description": "Thẩm tra độc lập KC.02-KC.09",
                "deliverable": "8 DXF AC1021 + preview PNG",
                "target_files": [
                    "01_Projects/03_Sprint2_KetQua_NeChu_CAD/04_Deliverables_ToTrinh/KC-02_MatBangKetCauNgam.dxf"
                ],
                "acceptance_criteria": ["8/8 PASS Bộ lọc 8", "Khớp PDF gốc"],
                "report_file": ".agents/memory/audits/03_sprint2_ketqua_nechu_cad/gemini/KC02_KC09_RESULT.md",
                "acceptance_cmd": "python 01_Projects/03_Sprint2_KetQua_NeChu_CAD/build_catlai_kc02_kc09_sheets.py",
            },
            "work_ticket": {
                "request_id": req_id,
                "human_handoff": {"handover_prompt": "Kiểm tra theo Điều 3 AGENTS.md."},
            },
        }
        self.bus_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_pre_invocation_injects_once_for_matching_claude_model(self) -> None:
        self._write_bus(status="PENDING", holder="IDLE", target="CLAUDE", req_id="req-claude-1")
        ev = {
            "hookEventName": "PreInvocation",
            "conversationId": "conv-sonnet-01",
            "modelName": "claude-sonnet-5-5",
            "lastUserInput": "thẩm tra đi",
        }
        out1 = hook.handle(ev)
        self.assertIn("injectSteps", out1)
        sys_msg = out1["injectSteps"][0]["systemMessage"]
        self.assertLess(len(sys_msg["systemMessage"]), 1500)
        self.assertIn("03_Sprint2_KetQua_NeChu_CAD", sys_msg["systemMessage"])
        self.assertIn("user_markdown", sys_msg["metadata"])

        # Same conversation & ticket must deduplicate on second turn
        out2 = hook.handle(ev)
        self.assertEqual(out2, {})

    def test_pre_invocation_skips_mismatched_model(self) -> None:
        self._write_bus(status="PENDING", holder="IDLE", target="CLAUDE", req_id="req-claude-2")
        ev = {
            "hookEventName": "PreInvocation",
            "conversationId": "conv-gemini-01",
            "modelName": "gemini-4-carbon",
            "lastUserInput": "tiếp tục",
        }
        self.assertEqual(hook.handle(ev), {})

    def test_explicit_nhan_ca_reinjects_and_handles_auto_model(self) -> None:
        self._write_bus(status="PENDING", holder="IDLE", target="CLAUDE", req_id="req-auto-1")
        ev = {
            "hookEventName": "PreInvocation",
            "conversationId": "conv-auto-01",
            "modelName": "auto",
            "lastUserInput": "nhận ca",
        }
        out1 = hook.handle(ev)
        self.assertIn("injectSteps", out1)

        # Normal message on "auto" should NOT re-inject, while explicit "nhận ca" forces re-inject
        ev_normal = dict(ev, lastUserInput="làm tiếp đi")
        self.assertEqual(hook.handle(ev_normal), {})
        out_reinject = hook.handle(ev)
        self.assertIn("injectSteps", out_reinject)

    def test_claude_code_user_prompt_submit(self) -> None:
        self._write_bus(status="PENDING", holder="IDLE", target="CLAUDE", req_id="req-cc-1")
        ev = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "cc-sess-1",
            "prompt": "kiểm tra bản vẽ giúp tôi",
        }
        out1 = hook.handle(ev)
        self.assertIn("hookSpecificOutput", out1)
        self.assertEqual(out1["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("sync_bus.py --claim --agent CLAUDE", out1["hookSpecificOutput"]["additionalContext"])
        self.assertLess(len(out1["hookSpecificOutput"]["additionalContext"]), 1500)

        out2 = hook.handle(ev)
        self.assertEqual(out2, {})

    def test_antigravity_pre_tool_use_dwg_guard(self) -> None:
        out_write = hook.handle({
            "hookEventName": "PreToolUse",
            "cwd": str(self.project),
            "toolCall": {"name": "write_file", "args": {"Path": str(self.original)}},
        })
        self.assertEqual(out_write["decision"], "deny")

        out_cmd = hook.handle({
            "hookEventName": "PreToolUse",
            "cwd": str(self.project),
            "toolCall": {"name": "run_command", "args": {"CommandLine": f'echo x > "{self.original}"'}},
        })
        self.assertEqual(out_cmd["decision"], "deny")

        new_dwg = self.out / "new.dwg"
        out_new = hook.handle({
            "hookEventName": "PreToolUse",
            "cwd": str(self.project),
            "toolCall": {"name": "write_file", "args": {"Path": str(new_dwg)}},
        })
        self.assertEqual(out_new["decision"], "allow")

        out_push = hook.handle({
            "hookEventName": "PreToolUse",
            "cwd": str(self.project),
            "toolCall": {"name": "run_command", "args": {"CommandLine": "git push origin main"}},
        })
        self.assertEqual(out_push["decision"], "ask")

    def test_installed_hooks_json_subprocess_and_latency(self) -> None:
        hooks_cfg = json.loads((AGENTS_ROOT / "hooks.json").read_text(encoding="utf-8"))
        pickup_cmd = hooks_cfg["dual-agent-auto-pickup"]["PreInvocation"][0]["command"]
        safety_cmd = hooks_cfg["antigravity-dwg-safety"]["PreToolUse"][0]["hooks"][0]["command"]
        pickup_argv = claude_safety_hook.tokens(pickup_cmd)
        safety_argv = claude_safety_hook.tokens(safety_cmd)

        # Safe non-mutating payload using mismatched modelName (unless bus targets GEMINI, use unknown) + read-only cmd
        pre_inv_payload = json.dumps({
            "hookEventName": "PreInvocation",
            "conversationId": "ci-smoke-test",
            "modelName": "test-probe-noop",
            "lastUserInput": "status check",
        })
        pre_tool_payload = json.dumps({
            "hookEventName": "PreToolUse",
            "cwd": str(AGENTS_ROOT.parent),
            "toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}},
        })

        latencies_ms = []
        for argv, payload, expected_keys in (
            (pickup_argv, pre_inv_payload, None),
            (safety_argv, pre_tool_payload, {"decision": "allow"}),
            (pickup_argv, pre_inv_payload, None),
            (safety_argv, pre_tool_payload, {"decision": "allow"}),
            (safety_argv, pre_tool_payload, {"decision": "allow"}),
        ):
            t0 = time.perf_counter()
            proc = subprocess.run(
                argv,
                input=payload,
                text=True,
                capture_output=True,
                encoding="utf-8",
                cwd=str(AGENTS_ROOT),
            )
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            parsed = json.loads(proc.stdout)
            if expected_keys:
                self.assertEqual(parsed, expected_keys)

        self.assertLess(statistics.median(latencies_ms), 100.0, f"Latencies ms: {latencies_ms}")

    def test_pre_tool_use_fail_closed_on_malformed_or_exception(self) -> None:
        # 1. Runtime exception inside claude_safety_hook on PreToolUse MUST return deny
        with patch.object(claude_safety_hook, "handle", side_effect=RuntimeError("boom")):
            out_err = hook.handle({
                "hookEventName": "PreToolUse",
                "cwd": str(self.project),
                "toolCall": {"name": "write_file", "args": {"Path": str(self.out / "new.dwg")}},
            })
        self.assertEqual(out_err["decision"], "deny")
        self.assertIn("fail-closed", out_err["reason"])

        # 2. Malformed JSON mentioning PreToolUse via subprocess stdin MUST fail-closed with deny
        hooks_cfg = json.loads((AGENTS_ROOT / "hooks.json").read_text(encoding="utf-8"))
        safety_cmd = hooks_cfg["antigravity-dwg-safety"]["PreToolUse"][0]["hooks"][0]["command"]
        safety_argv = claude_safety_hook.tokens(safety_cmd)
        proc = subprocess.run(
            safety_argv,
            input='{"hookEventName": "PreToolUse", "broken_json": ',
            text=True,
            capture_output=True,
            encoding="utf-8",
            cwd=str(AGENTS_ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed["decision"], "deny")
        self.assertIn("fail-closed", parsed["reason"])

    def test_pre_invocation_injects_on_need_review_with_blocking_questions(self) -> None:
        self._write_bus(status="NEED_REVIEW", holder="IDLE", target="GEMINI", req_id="req-blocked-1")
        payload = json.loads(self.bus_path.read_text(encoding="utf-8"))
        payload["Verification_Status"] = "BLOCKED_RETURN"
        payload["environment_capabilities"] = {
            "accoreconsole_available": True,
            "sheet_set_manager_native_dst": False,
        }
        payload["next_action_for_partner"]["blocking_questions"] = ["Chốt 7 hay 8 workbook?"]
        self.bus_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        out = hook.handle({
            "hookEventName": "PreInvocation",
            "conversationId": "conv-gemini-needrev-1",
            "modelName": "gemini-4-neon",
            "lastUserInput": "kiểm tra lại",
        })
        self.assertIn("injectSteps", out)
        msg = out["injectSteps"][0]["systemMessage"]["systemMessage"]
        self.assertIn("NEED_REVIEW/BLOCKED_RETURN", msg)
        self.assertIn("Chốt 7 hay 8 workbook?", msg)
        self.assertIn("Env: accoreconsole=YES", msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
