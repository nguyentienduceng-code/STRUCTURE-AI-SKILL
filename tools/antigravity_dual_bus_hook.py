# -*- coding: utf-8 -*-
"""Unified Antigravity & Claude Code Dual-Agent Bus auto-pickup and DWG safety hook."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure") and sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

ROOT: Path = Path(__file__).resolve().parents[2]
BUS_PATH: Path = ROOT / ".agents" / "memory" / "DUAL_AGENT_BUS.json"
STATE_PATH: Path = (
    Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
    / "GoogleAIStudio"
    / "locks"
    / "bus_injected_sessions.json"
)

VALID_TARGETS = {"CLAUDE", "GEMINI", "CODEX"}
CLAUDE_KEYWORDS = ("claude", "sonnet", "opus", "haiku", "anthropic")
GEMINI_KEYWORDS = ("gemini", "flash", "neon", "carbon", "argon")
EXPLICIT_CLAIM_TRIGGERS = ("/nhan-ca", "nhận ca", "nhan ca", "claim task")
FORCE_REINJECT_TRIGGERS = ("/nhan-ca", "nhận ca", "nhan ca")
MAX_STATE_ENTRIES = 200
MAX_BRIEFING_CHARS = 1480


def _load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _save_state_atomic(path: Path, state: Dict[str, float]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Retain at most MAX_STATE_ENTRIES most recent entries.
        if len(state) > MAX_STATE_ENTRIES:
            ordered = sorted(state.items(), key=lambda kv: float(kv[1]), reverse=True)[:MAX_STATE_ENTRIES]
            state = dict(ordered)
        payload = json.dumps(state, ensure_ascii=False, indent=2)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.stem}.tmp.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, str(path))
        finally:
            if os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
    except Exception:
        # Never block chat invocation if cache state cannot be persisted.
        pass


def _detect_active_agent(event: Dict[str, Any], is_claude_code: bool, target: str) -> str:
    if is_claude_code:
        return "CLAUDE"
    model_name = str(event.get("modelName", "") or "").lower()
    user_input = str(event.get("lastUserInput", "") or "").strip().lower()
    if any(kw in model_name for kw in CLAUDE_KEYWORDS):
        return "CLAUDE"
    if any(kw in model_name for kw in GEMINI_KEYWORDS):
        return "GEMINI"
    if model_name in {"", "auto"} and any(trig in user_input for trig in EXPLICIT_CLAIM_TRIGGERS):
        return target
    return ""


def _build_briefing(bus: Dict[str, Any], target: str) -> tuple[str, str, str, str, int]:
    ctx = bus.get("project_context") or {}
    project_code = str(ctx.get("project_code") or bus.get("work_ticket", {}).get("task_id") or "00_GENERAL")
    sender = str(bus.get("last_updated_by") or "PARTNER").upper()
    ticket = bus.get("work_ticket") or {}
    request_id = str(ticket.get("request_id") or bus.get("timestamp") or "N/A")
    next_act = bus.get("next_action_for_partner") or {}
    task_desc = str(next_act.get("task_description") or next_act.get("command") or "")
    deliverable = str(next_act.get("deliverable") or "")
    summary = str(bus.get("summary") or "")
    target_files = [str(f) for f in (next_act.get("target_files") or [])[:12]]
    criteria = [str(c) for c in (next_act.get("acceptance_criteria") or [])[:6]]
    blocking_questions = [str(q) for q in (next_act.get("blocking_questions") or [])[:5] if str(q).strip()]
    report_file = str(next_act.get("report_file") or "")
    acceptance_cmd = str(next_act.get("acceptance_cmd") or "")
    handover_prompt = str((ticket.get("human_handoff") or {}).get("handover_prompt") or "")
    handoff_st = str(bus.get("handoff_status") or "PENDING").upper()
    verif_st = str(bus.get("Verification_Status") or "").upper()
    env_caps = bus.get("environment_capabilities") if isinstance(bus.get("environment_capabilities"), dict) else None

    footer = (
        f"Chạy ngay: python .agents/tools/sync_bus.py --claim --agent {target} "
        "để khóa ca trước khi làm; nếu thiếu đầu vào/công cụ, trả ca ngay qua --need-review --blocked-return."
    )

    core_lines: List[str] = [
        f"[DUAL-AGENT AUTO-PICKUP | {handoff_st}{('/' + verif_st) if verif_st else ''}] Dự án: {project_code} | {sender} ➔ {target} | ID: {request_id}",
        f"Nhiệm vụ: {task_desc}",
    ]
    if blocking_questions:
        core_lines.append("Điểm chặn/Câu hỏi: " + " ; ".join(blocking_questions))
    if deliverable:
        core_lines.append(f"Sản phẩm: {deliverable}")
    if target_files:
        core_lines.append("Tệp mục tiêu (" + str(len(target_files)) + "): " + ", ".join(target_files))
    if criteria:
        core_lines.append("Tiêu chí: " + " ; ".join(criteria))
    if report_file:
        core_lines.append(f"Báo cáo pha: {report_file}")
    if acceptance_cmd:
        core_lines.append(f"Lệnh verify: {acceptance_cmd}")
    if env_caps:
        ac_ok = "YES" if env_caps.get("accoreconsole_available") else "NO"
        dst_ok = bool(env_caps.get("sheet_set_manager_native_dst", False))
        core_lines.append(f"Env: accoreconsole={ac_ok} (--audit-only OK), native_dst={dst_ok}, async_bus_only=True")

    core_text = "\n".join(core_lines)
    budget = MAX_BRIEFING_CHARS - len(core_text) - len(footer) - 8

    optional_lines: List[str] = []
    if summary and budget > 40:
        clipped_sum = summary if len(summary) <= min(budget - 12, 320) else summary[: min(budget - 15, 317)] + "..."
        optional_lines.append(f"Tóm tắt: {clipped_sum}")
        budget -= len(optional_lines[-1]) + 1
    if handover_prompt and budget > 60:
        flat_prompt = " | ".join(line.strip() for line in handover_prompt.splitlines() if line.strip())
        clipped_hp = flat_prompt if len(flat_prompt) <= budget - 16 else flat_prompt[: budget - 19] + "..."
        optional_lines.append(f"Chỉ dẫn phiếu: {clipped_hp}")

    parts = [core_text]
    if optional_lines:
        parts.extend(optional_lines)
    parts.append(footer)
    briefing = "\n".join(parts)
    if len(briefing) > MAX_BRIEFING_CHARS:
        keep_end = f"\n{footer}"
        briefing = briefing[: MAX_BRIEFING_CHARS - len(keep_end) - 3] + "..." + keep_end
    return briefing, project_code, sender, target, len(target_files)


def _handle_auto_pickup(event: Dict[str, Any], is_claude_code: bool) -> Dict[str, Any]:
    bus = _load_json_safe(BUS_PATH)
    if not bus:
        return {}
    if str(bus.get("handoff_status", "")).upper() not in {"PENDING", "NEED_REVIEW"}:
        return {}
    if str(bus.get("current_holder", "IDLE") or "IDLE").upper() not in {"IDLE", "", "NONE"}:
        return {}

    next_act = bus.get("next_action_for_partner") or {}
    target = str(next_act.get("target_agent", "")).upper()
    if target not in VALID_TARGETS:
        return {}

    active_agent = _detect_active_agent(event, is_claude_code, target)
    if active_agent != target:
        return {}

    user_text = str(
        event.get("prompt") if is_claude_code else event.get("lastUserInput", "")
    ).strip().lower()
    force_reinject = any(trig in user_text for trig in FORCE_REINJECT_TRIGGERS)

    session_id = str(event.get("conversationId") or event.get("session_id") or "default")
    ticket_key = str((bus.get("work_ticket") or {}).get("request_id") or bus.get("timestamp") or "unknown")
    cache_key = f"{session_id}:{ticket_key}"

    state_raw = _load_json_safe(STATE_PATH) or {}
    state: Dict[str, float] = {
        str(k): float(v) for k, v in state_raw.items() if isinstance(v, (int, float))
    }
    if cache_key in state and not force_reinject:
        return {}

    state[cache_key] = time.time()
    _save_state_atomic(STATE_PATH, state)

    briefing, project_code, sender, target_label, file_count = _build_briefing(bus, target)
    if is_claude_code:
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": briefing,
            }
        }

    user_md = (
        f"> 📨 **Dual-Agent Auto-Pickup:** Đã tự động nạp phiếu bàn giao "
        f"**`{project_code}`** từ **`{sender}` ➔ `{target_label}`** "
        f"(`{file_count}` tệp mục tiêu). Anh/chị không cần gõ `@file` hay dán lại lệnh."
    )
    return {
        "injectSteps": [
            {
                "systemMessage": {
                    "systemMessage": briefing,
                    "metadata": {"user_markdown": user_md},
                }
            }
        ]
    }


def _map_antigravity_tool_event(event: Dict[str, Any], kind: str) -> Optional[Dict[str, Any]]:
    tool_call = event.get("toolCall") or {}
    raw_name = str(tool_call.get("name", ""))
    args = tool_call.get("args") or {}
    cwd = str(event.get("cwd") or ROOT)

    if raw_name == "run_command":
        mapped_name = "PowerShell"
        mapped_input: Dict[str, Any] = {"command": str(args.get("CommandLine", ""))}
    elif raw_name == "write_file":
        mapped_name = "Write"
        mapped_input = {"file_path": str(args.get("Path", ""))}
    elif raw_name in {"edit_file", "multi_edit"}:
        mapped_name = "Edit"
        mapped_input = {"file_path": str(args.get("Path", ""))}
    elif raw_name.startswith("mcp_"):
        mapped_name = raw_name if raw_name.startswith("mcp__") else f"mcp__{raw_name[4:]}"
        mapped_input = dict(args)
    else:
        return None

    return {
        "hook_event_name": kind,
        "tool_name": mapped_name,
        "tool_input": mapped_input,
        "cwd": cwd,
    }


def _handle_antigravity_tool(event: Dict[str, Any], kind: str) -> Dict[str, Any]:
    try:
        mapped = _map_antigravity_tool_event(event, kind)
        if mapped is None:
            return {"decision": "allow"} if kind == "PreToolUse" else {}

        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import claude_safety_hook  # noqa: E402

        orig_root = claude_safety_hook.ROOT
        claude_safety_hook.ROOT = str(ROOT)
        try:
            action, message = claude_safety_hook.handle(mapped)
        finally:
            claude_safety_hook.ROOT = orig_root

        if kind == "PreToolUse":
            if action == "deny":
                return {"decision": "deny", "reason": message}
            if action == "ask":
                return {"decision": "ask", "reason": message}
            return {"decision": "allow"}
        return {}
    except Exception as exc:
        if kind == "PreToolUse":
            return {"decision": "deny", "reason": f"Safety hook internal error (fail-closed): {exc}"}
        return {}


def handle(event: Dict[str, Any]) -> Dict[str, Any]:
    """Process one Antigravity or Claude Code hook payload and return JSON output."""
    if not isinstance(event, dict):
        return {}

    if "hookEventName" in event:
        kind = str(event.get("hookEventName", ""))
        if kind in {"PreInvocation", "SessionStart"}:
            return _handle_auto_pickup(event, is_claude_code=False)
        if kind in {"PreToolUse", "PostToolUse"}:
            return _handle_antigravity_tool(event, kind)
        return {}

    if event.get("hook_event_name") == "UserPromptSubmit":
        return _handle_auto_pickup(event, is_claude_code=True)

    return {}


def _is_non_pre_tool_event(raw: str) -> bool:
    low = raw.lower()
    if '"pretooluse"' in low or "pretooluse" in low:
        return False
    return any(tok in low for tok in ("preinvocation", "sessionstart", "userpromptsubmit", "posttooluse"))


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
        out = handle(event)
    except Exception as exc:
        # Fail-closed for PreToolUse / unknown non-empty payloads; fail-open for chat auto-pickup events.
        if raw.strip() and not _is_non_pre_tool_event(raw):
            out = {"decision": "deny", "reason": f"Malformed PreToolUse payload (fail-closed): {exc}"}
        else:
            out = {}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
