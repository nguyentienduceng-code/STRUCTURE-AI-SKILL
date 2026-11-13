#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dual_agent_audit.py — Bộ công cụ Thẩm tra Đối kháng Độc lập (Red-Team Audit Engine).
Cung cấp ma trận đồng thuận (Consensus Matrix) giữa Maker và Auditor.
Usage:
    python dual_agent_audit.py --mode simulation
    python dual_agent_audit.py --mode file_ipc --outbox path/to/outbox.json
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def evaluate_consensus(maker_verdict: str, auditor_verdict: str) -> dict:
    """
    Ma trận đồng thuận lưỡng cực (Consensus Matrix):
    - UNANIMOUS_APPROVE : Cả 2 đồng thuận duyệt ➔ Chốt xuất xưởng.
    - CONDITIONAL_PASS  : Auditor yêu cầu thận trọng (CAUTION) ➔ Ghi chú warning.
    - HARD_VETO         : Một bên từ chối (REJECT / VETO) ➔ Khóa quy trình, trả về Maker fix.
    """
    maker = maker_verdict.upper()
    auditor = auditor_verdict.upper()

    if "VETO" in [maker, auditor] or "REJECT" in [maker, auditor]:
        return {
            "consensus": "HARD_VETO",
            "decision": "BLOCKED",
            "action": "Dừng quy trình ngay lập tức. Yêu cầu Maker rà soát nguyên nhân từ chối."
        }
    elif "CAUTION" in [maker, auditor]:
        return {
            "consensus": "CONDITIONAL_PASS",
            "decision": "PROCEED_WITH_WARNING",
            "action": "Cho phép tiến hành nhưng phải ghi nhận các cờ cảnh báo (Flags)."
        }
    else:
        return {
            "consensus": "UNANIMOUS_APPROVE",
            "decision": "PASSED",
            "action": "Đồng thuận tuyệt đối 100%. Sẵn sàng xuất xưởng / đóng gói."
        }

def main():
    parser = argparse.ArgumentParser(description="Dual-Agent Adversarial Red-Team Auditor")
    parser.add_argument("--mode", default="simulation", choices=["simulation", "file_ipc"],
                        help="Chế độ thẩm tra: simulation hoặc file_ipc")
    parser.add_argument("--maker-action", default="APPROVE", choices=["APPROVE", "CAUTION", "REJECT"],
                        help="Quyết định từ Agent Maker (Gemini)")
    parser.add_argument("--auditor-action", default="APPROVE", choices=["APPROVE", "CAUTION", "REJECT", "VETO"],
                        help="Quyết định từ Agent Auditor (Claude)")
    parser.add_argument("--outbox", default=None,
                        help="Đường dẫn file JSON outbox/bus khi chạy ở chế độ --mode file_ipc")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")
    args = parser.parse_args()

    maker_action = args.maker_action
    auditor_action = args.auditor_action
    divergence_flags: list = []

    if args.mode == "file_ipc":
        if not args.outbox:
            print("[LỖI] Chế độ --mode file_ipc yêu cầu truyền --outbox <path/to/file.json>.", file=sys.stderr)
            sys.exit(2)
        outbox_path = Path(args.outbox)
        if not outbox_path.is_file():
            print(f"[LỖI] Không tìm thấy file outbox: {outbox_path}", file=sys.stderr)
            sys.exit(1)
        with open(outbox_path, "r", encoding="utf-8") as f:
            ipc_data = json.load(f)
        maker_action = str(ipc_data.get("maker_action", ipc_data.get("maker_verdict", maker_action))).upper()
        auditor_action = str(ipc_data.get("auditor_action", ipc_data.get("auditor_verdict", auditor_action))).upper()
        divergence_flags = list(ipc_data.get("divergenceFlags", ipc_data.get("divergence_flags", [])) or [])
        if divergence_flags and auditor_action == "APPROVE":
            auditor_action = "CAUTION"

    result = evaluate_consensus(maker_action, auditor_action)
    result["mode"] = args.mode
    result["maker_action"] = maker_action
    result["auditor_action"] = auditor_action
    result["divergence_flags"] = divergence_flags

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["decision"] != "BLOCKED" else 1)

    print("\n" + "=" * 65)
    print("      ⚔️  DUAL-AGENT ADVERSARIAL AUDIT (RED-TEAM GATE) ⚔️")
    print("=" * 65)
    print(f" Chế độ chạy     : {args.mode.upper()}")
    print(f" Phán quyết Maker: {maker_action}")
    print(f" Phán quyết Audit: {auditor_action}")
    if divergence_flags:
        print(f" Divergence Flags: {', '.join(str(x) for x in divergence_flags)}")
    print("-" * 65)

    icon = "✅" if result["decision"] == "PASSED" else "⚠️" if result["decision"] == "PROCEED_WITH_WARNING" else "🛑"

    print(f" Ma trận Đồng thuận: {result['consensus']}")
    print(f" Kết luận Cuối cùng: {icon} {result['decision']}")
    print(f" Chỉ thị Hành động : {result['action']}")
    print("=" * 65 + "\n")
    sys.exit(0 if result["decision"] != "BLOCKED" else 1)

if __name__ == "__main__":
    main()
