#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claim_task.py — 1-Click Nhận ca làm việc (Claim Shift) cho Gemini hoặc Claude.
Usage:
    python claim_task.py --agent CLAUDE
    python claim_task.py --agent GEMINI
"""

import argparse
import sys
import subprocess
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="1-Click Nhận ca làm việc cho Multi-Agent (Gemini, Claude, Codex)")
    parser.add_argument("--agent", required=True, choices=["GEMINI", "CLAUDE", "CODEX", "USER", "User", "gemini", "claude", "codex"],
                        help="Tên Agent nhận ca (GEMINI, CLAUDE hoặc CODEX)")
    parser.add_argument("--workspace", default=None, help="Thư mục workspace tùy chọn")
    args = parser.parse_args()

    agent_name = args.agent.upper()
    script_dir = Path(__file__).resolve().parent
    sync_bus_script = script_dir / "sync_bus.py"

    cmd = [sys.executable, str(sync_bus_script), "--claim", "--agent", agent_name]
    if args.workspace:
        import os
        os.environ["DUAL_AGENT_WORKSPACE"] = str(Path(args.workspace).resolve())

    print(f"\n=======================================================")
    print(f" [DUAL-AGENT BRIDGE] Yêu cầu nhận ca cho: {agent_name}")
    print(f"=======================================================")

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)

    if res.returncode == 0:
        print(f"\n>>> [THÀNH CÔNG] {agent_name} đã nhận ca và khóa Mutex an toàn!")
        print(f">>> Trạng thái: IN_PROGRESS | Đối tác sẽ không ghi đè.")
    else:
        print(f"\n>>> [LỖI] Không thể nhận ca. Mã thoát: {res.returncode}")

    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
