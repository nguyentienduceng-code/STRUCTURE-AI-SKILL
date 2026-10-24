#!/usr/bin/env python3
"""
Audit Logger — Ghi log mọi hành động xuất file và phê duyệt

Mục đích:
- Tạo audit trail cho compliance
- Ghi lại timestamp, user, file, action
- Phát hiện suspicious activity

Usage:
    python audit_logger.py log --action export --file output.docx --user "Kỹ sư A"
    python audit_logger.py log --action approve --file output.docx --user "Kỹ sư A"
    python audit_logger.py query --user "Kỹ sư A"
    python audit_logger.py query --action export --days 7
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import uuid

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================================
# CONFIGURATION
# ============================================================================

AUDIT_DIR = Path(__file__).parent
AUDIT_LOG_FILE = AUDIT_DIR / "audit_log.json"

COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BLUE": "\033[94m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m"
}

# Valid actions
VALID_ACTIONS = [
    "export",        # Xuất file
    "approve",       # Phê duyệt
    "reject",        # Từ chối
    "review",        # Review gate triggered
    "download",      # Tải file
    "delete",       # Xóa file
    "modify",       # Sửa đổi
    "share",        # Chia sẻ
]


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class AuditEntry:
    """Một entry trong audit log"""
    id: str
    timestamp: str
    action: str
    user: str
    file: str
    project: Optional[str]
    skill: Optional[str]  # Skill tạo ra action
    session_id: Optional[str]
    details: Optional[Dict]
    ip_address: Optional[str]  # Có thể null cho local

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        # Handle migration from older format
        if "details" not in data:
            data["details"] = {}
        if "ip_address" not in data:
            data["ip_address"] = None
        if "session_id" not in data:
            data["session_id"] = None
        return cls(**data)


# ============================================================================
# AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """Audit logger chính"""

    def __init__(self, log_file: Path = None):
        self.log_file = log_file or AUDIT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Ensure log file exists
        if not self.log_file.exists():
            self._init_log_file()

    def _init_log_file(self):
        """Khởi tạo file log mới"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "entries": []
            }, f, indent=2, ensure_ascii=False)

    def _load_log(self) -> Dict:
        """Load toàn bộ log file"""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._init_log_file()
            return {"version": "1.0.0", "created_at": datetime.now().isoformat(), "entries": []}

    def _save_log(self, data: Dict):
        """Lưu log file (atomic write)"""
        # Write to temp file first
        temp_file = self.log_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Rename to actual file
        temp_file.replace(self.log_file)

    def log(self, action: str, file: str, user: str = "unknown",
            project: Optional[str] = None, skill: Optional[str] = None,
            session_id: Optional[str] = None,
            details: Optional[Dict] = None,
            ip_address: Optional[str] = None) -> AuditEntry:
        """
        Ghi một entry vào audit log.

        Args:
            action: Loại action (export, approve, reject, ...)
            file: Đường dẫn file liên quan
            user: Tên người thực hiện
            project: Mã dự án (tùy chọn)
            skill: Skill tạo ra action (tùy chọn)
            session_id: Session ID của Claude (tùy chọn)
            details: Thông tin bổ sung
            ip_address: Địa chỉ IP (tùy chọn)

        Returns:
            AuditEntry đã được tạo
        """
        # Validate action
        if action not in VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}. Must be one of: {VALID_ACTIONS}")

        # Create entry
        entry = AuditEntry(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            action=action,
            user=user,
            file=str(file),
            project=project,
            skill=skill,
            session_id=session_id,
            details=details or {},
            ip_address=ip_address
        )

        # Load, append, save
        data = self._load_log()
        data["entries"].append(entry.to_dict())

        # Keep only last 10000 entries to prevent file bloat
        if len(data["entries"]) > 10000:
            data["entries"] = data["entries"][-10000:]

        self._save_log(data)

        return entry

    def query(self, action: Optional[str] = None,
              user: Optional[str] = None,
              file: Optional[str] = None,
              project: Optional[str] = None,
              days: Optional[int] = None,
              limit: int = 100) -> List[AuditEntry]:
        """
        Truy vấn audit log.

        Args:
            action: Filter theo action
            user: Filter theo user
            file: Filter theo file path
            project: Filter theo project
            days: Chỉ lấy entries trong N ngày gần nhất
            limit: Giới hạn số kết quả

        Returns:
            List of AuditEntry
        """
        data = self._load_log()
        entries = []

        for entry_data in data.get("entries", []):
            entry = AuditEntry.from_dict(entry_data)

            # Apply filters
            if action and entry.action != action:
                continue
            if user and entry.user.lower() != user.lower():
                continue
            if file and file.lower() not in entry.file.lower():
                continue
            if project and entry.project != project:
                continue

            # Date filter
            if days:
                entry_time = datetime.fromisoformat(entry.timestamp)
                cutoff = datetime.now() - timedelta(days=days)
                if entry_time < cutoff:
                    continue

            entries.append(entry)

        # Sort by timestamp descending
        entries.sort(key=lambda x: x.timestamp, reverse=True)

        return entries[:limit]

    def get_recent(self, limit: int = 20) -> List[AuditEntry]:
        """Lấy N entries gần nhất"""
        return self.query(limit=limit)

    def export_summary(self, days: int = 30) -> Dict:
        """
        Xuất summary statistics trong N ngày.

        Returns:
            Dict với statistics
        """
        entries = self.query(days=days)

        if not entries:
            return {
                "period_days": days,
                "total_actions": 0,
                "by_action": {},
                "by_user": {},
                "by_project": {},
                "recent_files": []
            }

        # Count by action
        by_action = {}
        for e in entries:
            by_action[e.action] = by_action.get(e.action, 0) + 1

        # Count by user
        by_user = {}
        for e in entries:
            by_user[e.user] = by_user.get(e.user, 0) + 1

        # Count by project
        by_project = {}
        for e in entries:
            if e.project:
                by_project[e.project] = by_project.get(e.project, 0) + 1

        # Recent files
        recent_files = list(dict.fromkeys(e.file for e in entries[:10]))

        return {
            "period_days": days,
            "total_actions": len(entries),
            "by_action": by_action,
            "by_user": by_user,
            "by_project": by_project,
            "recent_files": recent_files
        }


# ============================================================================
# CLI
# ============================================================================

def print_entry(entry: AuditEntry, verbose: bool = False):
    """In một entry ra console"""

    action_colors = {
        "export": COLORS["GREEN"],
        "approve": COLORS["GREEN"],
        "reject": COLORS["RED"],
        "review": COLORS["BLUE"],
        "delete": COLORS["RED"],
        "modify": COLORS["YELLOW"],
    }

    color = action_colors.get(entry.action, COLORS["RESET"])

    # Format timestamp
    dt = datetime.fromisoformat(entry.timestamp)
    time_str = dt.strftime("%Y-%m-%d %H:%M")

    print(f"{color}{entry.action.upper():<10}{COLORS['RESET']} | {time_str} | {entry.user:<20} | {entry.file}")

    if verbose and entry.project:
        print(f"            Project: {entry.project}")
    if verbose and entry.skill:
        print(f"            Skill: {entry.skill}")
    if verbose and entry.details:
        for k, v in entry.details.items():
            print(f"            {k}: {v}")


def main():
    parser = argparse.ArgumentParser(
        description="Audit Logger — Ghi và truy vấn audit trail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python audit_logger.py log --action export --file output.docx --user "KS. Nguyen Van A"
  python audit_logger.py log --action approve --file report.pdf --user "KS. Tran Van B" --project "DA-001"
  python audit_logger.py query --action export --days 7
  python audit_logger.py summary --days 30
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # log command
    log_parser = subparsers.add_parser("log", help="Ghi một entry vào audit log")
    log_parser.add_argument("--action", "-a", required=True, choices=VALID_ACTIONS,
                           help="Loại action")
    log_parser.add_argument("--file", "-f", required=True,
                           help="Đường dẫn file liên quan")
    log_parser.add_argument("--user", "-u", required=True,
                           help="Tên người thực hiện")
    log_parser.add_argument("--project", "-p", help="Mã dự án")
    log_parser.add_argument("--skill", "-s", help="Skill tạo ra action")
    log_parser.add_argument("--session", help="Session ID")
    log_parser.add_argument("--details", "-d", help="JSON details")

    # query command
    query_parser = subparsers.add_parser("query", help="Truy vấn audit log")
    query_parser.add_argument("--action", "-a", choices=VALID_ACTIONS, help="Filter theo action")
    query_parser.add_argument("--user", "-u", help="Filter theo user")
    query_parser.add_argument("--file", "-f", help="Filter theo file (partial match)")
    query_parser.add_argument("--project", "-p", help="Filter theo project")
    query_parser.add_argument("--days", "-d", type=int, help="Chỉ entries trong N ngày")
    query_parser.add_argument("--limit", "-l", type=int, default=100, help="Giới hạn kết quả")
    query_parser.add_argument("--verbose", "-v", action="store_true", help="Hiển thị chi tiết")

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Xuất summary statistics")
    summary_parser.add_argument("--days", "-d", type=int, default=30, help="Số ngày tính统计")

    args = parser.parse_args()

    logger = AuditLogger()

    if args.command == "log":
        details = None
        if args.details:
            try:
                details = json.loads(args.details)
            except json.JSONDecodeError:
                print(f"{COLORS['RED']}Error: Invalid JSON in --details{COLORS['RESET']}")
                sys.exit(1)

        entry = logger.log(
            action=args.action,
            file=args.file,
            user=args.user,
            project=args.project,
            skill=args.skill,
            session_id=args.session,
            details=details
        )

        print(f"{COLORS['GREEN']}✓ Audit entry logged:{COLORS['RESET']}")
        print(f"  ID: {entry.id}")
        print(f"  Action: {entry.action}")
        print(f"  User: {entry.user}")
        print(f"  File: {entry.file}")
        print(f"  Time: {entry.timestamp}")

    elif args.command == "query":
        entries = logger.query(
            action=args.action,
            user=args.user,
            file=args.file,
            project=args.project,
            days=args.days,
            limit=args.limit
        )

        if not entries:
            print("No entries found.")
        else:
            print(f"\n{'─' * 80}")
            print(f"{'ACTION':<10} | {'TIME':<20} | {'USER':<20} | {'FILE'}")
            print(f"{'─' * 80}")

            for entry in entries:
                print_entry(entry, verbose=args.verbose)

            print(f"{'─' * 80}")
            print(f"Total: {len(entries)} entries")

    elif args.command == "summary":
        summary = logger.export_summary(days=args.days)

        print(f"\n{COLORS['BOLD']}AUDIT SUMMARY (Last {summary['period_days']} days){COLORS['RESET']}")
        print(f"{'─' * 60}")
        print(f"Total actions: {summary['total_actions']}")

        if summary['by_action']:
            print(f"\nBy Action:")
            for action, count in sorted(summary['by_action'].items(), key=lambda x: -x[1]):
                print(f"  {action:<15} {count:>5}")

        if summary['by_user']:
            print(f"\nBy User:")
            for user, count in sorted(summary['by_user'].items(), key=lambda x: -x[1])[:10]:
                print(f"  {user:<20} {count:>5}")

        if summary['recent_files']:
            print(f"\nRecent Files:")
            for f in summary['recent_files'][:5]:
                print(f"  • {f}")

    else:
        parser.print_help()


# ============================================================================
# INTEGRATION POINT — Review Gate
# ============================================================================

def integrate_with_review_gate(review_gate_result: Dict, user: str, file_path: str) -> AuditEntry:
    """
    Tích hợp với Review Gate Engine.

    Gọi hàm này khi user approve tại Review Gate.

    Args:
        review_gate_result: Kết quả từ ReviewGate.to_json()
        user: Tên user approve
        file_path: Đường dẫn file được approve

    Returns:
        AuditEntry đã được log
    """
    logger = AuditLogger()

    # Extract info from review gate
    gate_data = review_gate_result.get("review_gate", {})
    input_summary = review_gate_result.get("input_summary", {})

    details = {
        "review_status": gate_data.get("status"),
        "overall_passed": gate_data.get("overall_passed"),
        "checks_passed": sum(1 for c in gate_data.get("checks", []) if c.get("passed")),
        "checks_total": len(gate_data.get("checks", [])),
        "element_id": input_summary.get("element_id"),
        "standard_method": input_summary.get("standard_method"),
        "confidence_score": input_summary.get("confidence_score")
    }

    return logger.log(
        action="approve",
        file=file_path,
        user=user,
        skill="ReviewGate",
        details=details
    )


if __name__ == "__main__":
    main()
