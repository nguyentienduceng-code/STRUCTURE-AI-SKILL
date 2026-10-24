# .agents/tools/sync_bus.py
# Giao thức Cầu nối File (File-based IPC Bus) giữa Claude Code và Gemini Antigravity

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Đảm bảo UTF-8 theo Quy tắc AGENTS.md
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def find_workspace_root() -> Path:
    """Tự động dò tìm thư mục gốc workspace chứa .agents và memory."""
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / ".agents").is_dir() and (curr / "memory").is_dir():
            return curr
        curr = curr.parent
    # Fallback chuẩn: .agents/tools -> parents[2]
    return Path(__file__).resolve().parents[2]


WORKSPACE_ROOT = find_workspace_root()
BUS_PATH = WORKSPACE_ROOT / "memory" / "DUAL_AGENT_BUS.json"


def post_handoff(sender: str, target: str, summary: str, next_cmd: str, files: list[str], status: str = "PENDING_ACTION"):
    """Ghi trạng thái bàn giao vào DUAL_AGENT_BUS.json."""
    BUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_updated_by": sender,
        "timestamp": datetime.now().astimezone().isoformat(),
        "summary": summary,
        "artifacts_modified": [f.strip() for f in files if f.strip()],
        "next_action_for_partner": {
            "target_agent": target,
            "command": next_cmd
        },
        "Verification_Status": status
    }
    BUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SYNC_BUS] ✅ Đã bàn giao trạng thái từ {sender} -> {target}")
    print(f"           Vị trí: {BUS_PATH}")
    print(f"           Lệnh tiếp theo: {next_cmd}")


def read_bus() -> dict:
    """Đọc trạng thái hiện tại từ bus."""
    if not BUS_PATH.exists():
        print(f"[SYNC_BUS] ⚠️ File bus chưa tồn tại tại {BUS_PATH}")
        return {}
    data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def show_usage():
    print("Sử dụng sync_bus.py:")
    print("  python .agents/tools/sync_bus.py <SENDER> <TARGET> <SUMMARY> <NEXT_COMMAND> <FILES_COMMA_SEPARATED> [STATUS]")
    print("\nVí dụ:")
    print('  python .agents/tools/sync_bus.py CLAUDE GEMINI "Đã viết xong 4 script" "Chạy test và tổng hợp" "file1.py,file2.py"')
    print("\nĐọc trạng thái hiện tại:")
    print("  python .agents/tools/sync_bus.py --read")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in ("--read", "-r", "read"):
        read_bus()
        sys.exit(0)

    if len(sys.argv) < 6:
        show_usage()
        sys.exit(1)

    sender = sys.argv[1]
    target = sys.argv[2]
    summary = sys.argv[3]
    next_cmd = sys.argv[4]
    files_str = sys.argv[5]
    status = sys.argv[6] if len(sys.argv) > 6 else "PENDING_PARTNER_ACTION"

    post_handoff(sender, target, summary, next_cmd, files_str.split(","), status)
