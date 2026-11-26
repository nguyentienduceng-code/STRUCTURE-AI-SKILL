#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
handover_task.py — 1-Click Bàn giao ca trực (Handover Shift) cho Gemini hoặc Claude.
Usage:
    python handover_task.py --sender GEMINI --target CLAUDE \
        --project 01_PROJECT_A --task "Kiểm tra chéo và chạy test" \
        --criteria "100% test pass;TypeScript 0 error"
"""

import argparse
import sys
import subprocess
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="1-Click Bàn giao ca trực Multi-Agent (Gemini, Claude, Codex) kèm Checklist")
    parser.add_argument("--sender", required=True, choices=["GEMINI", "CLAUDE", "CODEX", "USER", "User", "gemini", "claude", "codex"], help="Agent gửi bàn giao")
    parser.add_argument("--target", required=True, choices=["GEMINI", "CLAUDE", "CODEX", "USER", "User", "gemini", "claude", "codex"], help="Agent nhận bàn giao")
    parser.add_argument("--project", default="00_GENERAL", help="Mã dự án (project code)")
    parser.add_argument("--purpose", default="Bàn giao ca trực định kỳ", help="Mục tiêu bàn giao")
    parser.add_argument("--task", required=True, help="Nhiệm vụ cụ thể cho Agent đối tác")
    parser.add_argument("--criteria", required=True, help="Tiêu chí nghiệm thu (phân cách bởi dấu chấm phẩy ';')")
    parser.add_argument("--summary", default="", help="Tóm tắt công việc đã thực hiện")
    parser.add_argument("--workspace", default=None, help="Thư mục workspace tùy chọn")
    parser.add_argument("--agent-selection", choices=["AUTO", "CLAUDE_ONLY", "GEMINI_ONLY", "CODEX_ONLY", "DUAL"])
    parser.add_argument("--dispatch-ticket")
    args = parser.parse_args()

    sender = args.sender.upper()
    target = args.target.upper()
    script_dir = Path(__file__).resolve().parent
    sync_bus_script = script_dir / "sync_bus.py"

    cmd = [
        sys.executable, str(sync_bus_script),
        "--auto",
        "--sender", sender,
        "--target", target,
        "--project", args.project,
        "--purpose", args.purpose,
        "--task", args.task,
        "--criteria", args.criteria,
        "--confirm"
    ]
    if args.agent_selection:
        cmd.extend(["--agent-selection", args.agent_selection])
    if args.dispatch_ticket:
        cmd.extend(["--dispatch-ticket", args.dispatch_ticket])
    if args.summary:
        cmd.extend(["--summary", args.summary])

    if args.workspace:
        import os
        os.environ["DUAL_AGENT_WORKSPACE"] = str(Path(args.workspace).resolve())

    print(f"\n=======================================================")
    print(f" [DUAL-AGENT BRIDGE] Bàn giao ca: {sender} ➔ {target}")
    print(f" Dự án: {args.project} | Nhiệm vụ: {args.task}")
    print(f"=======================================================")

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)

    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
