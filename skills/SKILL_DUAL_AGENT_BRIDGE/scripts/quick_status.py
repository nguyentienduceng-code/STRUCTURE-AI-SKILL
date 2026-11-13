#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quick_status.py — 1-Click Xem nhanh trạng thái hệ thống điều phối Dual-Agent.
Usage:
    python quick_status.py
"""

import json
import sys
import os
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def find_bus_file():
    env_ws = os.environ.get("DUAL_AGENT_WORKSPACE")
    candidates = []
    if env_ws:
        candidates.append(Path(env_ws) / "memory" / "DUAL_AGENT_BUS.json")

    candidates.extend([
        Path.cwd() / "memory" / "DUAL_AGENT_BUS.json",
        Path("G:/My Drive/Google AI Studio/memory/DUAL_AGENT_BUS.json"),
        Path("J:/My Drive/AI AGENT/memory/DUAL_AGENT_BUS.json"),
        Path("D:/AI AGENT/memory/DUAL_AGENT_BUS.json"),
    ])

    for c in candidates:
        if c.is_file():
            return c
    return None

def main():
    bus_file = find_bus_file()
    print("\n" + "=" * 65)
    print("        🛰️  TRẠNG THÁI HỆ THỐNG DUAL-AGENT (IPC BUS) 🛰️")
    print("=" * 65)

    if not bus_file:
        print(" [!] Chưa tìm thấy tệp memory/DUAL_AGENT_BUS.json nào.")
        print("     Hệ thống đang ở trạng thái nhàn rỗi (IDLE).")
        print("=" * 65)
        return

    try:
        with open(bus_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f" [LỖI] Không thể đọc JSON từ {bus_file}: {e}")
        return

    ctx = data.get("project_context", {})
    partner = data.get("next_action_for_partner", {})
    status = data.get("handoff_status", "UNKNOWN")
    holder = data.get("current_holder", "IDLE")

    status_icon = "🟢" if status == "COMPLETED" else "🟡" if status == "IN_PROGRESS" else "🔵"

    print(f" Vị trí Bus       : {bus_file.as_posix()}")
    print(f" Mã dự án         : {ctx.get('project_code', 'N/A')}")
    print(f" Mục tiêu         : {ctx.get('project_purpose', 'N/A')}")
    print(f" Trạng thái ca    : {status_icon} {status}")
    print(f" Tác tử giữ ca    : 👤 {holder}")
    print(f" Cập nhật bởi     : {data.get('last_updated_by', 'N/A')} lúc {data.get('timestamp', 'N/A')}")
    print("-" * 65)
    print(f" Tóm tắt tiến độ  : {data.get('summary', 'Chưa có tóm tắt')}")
    print("-" * 65)
    print(f" 🎯 Tác tử tiếp nhận : {partner.get('target_agent', 'N/A')}")
    print(f" 📋 Nhiệm vụ tiếp theo: {partner.get('task_description', 'N/A')}")

    criteria = partner.get("acceptance_criteria", [])
    if criteria:
        print(" ✅ Tiêu chí nghiệm thu (Acceptance Criteria):")
        for i, c in enumerate(criteria, 1):
            print(f"    [{i}] {c}")

    target_files = partner.get("target_files", [])
    if target_files:
        print(" 📁 Tệp tin mục tiêu (Target Files):")
        for f in target_files:
            print(f"    - {f}")

    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
