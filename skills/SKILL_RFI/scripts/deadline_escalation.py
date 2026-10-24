#!/usr/bin/env python3
"""
deadline_escalation.py — RFI/NCR Deadline Notification & Escalation Engine
===========================================================================
Script tự động theo dõi và nhắc nhở deadline RFI/NCR/Submittal.

Features:
- Theo dõi deadline RFI
- Gửi notification khi sắp hết hạn (3 ngày, 1 ngày, quá hạn)
- Tự động escalation theo mức ưu tiên
- Dashboard trạng thái

Usage:
    python deadline_escalation.py --scan [--days 7] [--output report.json]
    python deadline_escalation.py --notify [--rfi_id RFI-001]
"""

import json
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
from pathlib import Path

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RFIDeadline:
    """Thông tin deadline RFI"""
    rfi_id: str
    title: str
    status: str
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    submitted_date: str
    due_date: str
    assigned_to: str
    category: str
    attachments: List[str] = field(default_factory=list)
    notes: str = ""
    escalation_level: int = 0
    last_reminder: Optional[str] = None

@dataclass
class EscalationEvent:
    """Sự kiện escalation"""
    timestamp: str
    rfi_id: str
    event_type: str  # reminder, escalation, overdue, closed
    message: str
    recipients: List[str]

@dataclass
class NotificationConfig:
    """Cấu hình notification"""
    reminder_days: List[int] = field(default_factory=lambda: [7, 3, 1])
    escalation_threshold: int = 1  # Số lần reminder trước khi escalation
    auto_close_days: int = 14  # Ngày tự động đóng nếu không phản hồi

# =============================================================================
# TRACKING ENGINE
# =============================================================================

class DeadlineTracker:
    """
    Engine theo dõi và xử lý deadline RFI.
    """

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or "rfi_deadlines.json"
        self.config = NotificationConfig()
        self.events: List[EscalationEvent] = []
        self._load_data()

    def _load_data(self):
        """Load dữ liệu từ file"""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.events = [EscalationEvent(**e) for e in data.get("events", [])]
        except (FileNotFoundError, json.JSONDecodeError):
            self.events = []

    def _save_data(self):
        """Lưu dữ liệu"""
        data = {
            "events": [asdict(e) for e in self.events]
        }
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def calculate_days_until_due(self, due_date_str: str) -> int:
        """Tính số ngày đến hạn"""
        due_date = datetime.fromisoformat(due_date_str)
        today = datetime.now()
        return (due_date - today).days

    def get_status(self, rfi: RFIDeadline) -> str:
        """Xác định trạng thái deadline"""
        days_left = self.calculate_days_until_due(rfi.due_date)

        if rfi.status in ["CLOSED", "APPROVED"]:
            return "CLOSED"
        elif days_left < 0:
            return "OVERDUE"
        elif days_left == 0:
            return "DUE_TODAY"
        elif days_left <= 3:
            return "DUE_SOON"
        elif days_left <= 7:
            return "DUE_THIS_WEEK"
        else:
            return "ON_TRACK"

    def should_remind(self, rfi: RFIDeadline) -> bool:
        """Kiểm tra có cần gửi reminder không"""
        days_left = self.calculate_days_until_due(rfi.due_date)

        # Kiểm tra các mốc reminder
        if days_left in self.config.reminder_days:
            # Kiểm tra chưa gửi reminder gần đây
            if rfi.last_reminder:
                last = datetime.fromisoformat(rfi.last_reminder)
                if (datetime.now() - last).days < 1:
                    return False
            return True

        # Quá hạn
        if days_left < 0 and rfi.escalation_level == 0:
            return True

        return False

    def get_priority_emoji(self, priority: str) -> str:
        """Lấy emoji theo mức ưu tiên"""
        return {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }.get(priority, "⚪")

    def get_status_emoji(self, status: str) -> str:
        """Lấy emoji theo trạng thái"""
        return {
            "ON_TRACK": "✅",
            "DUE_THIS_WEEK": "🟡",
            "DUE_SOON": "🟠",
            "DUE_TODAY": "⚠️",
            "OVERDUE": "🚨",
            "CLOSED": "✅✅"
        }.get(status, "⚪")

    def generate_reminder_message(self, rfi: RFIDeadline) -> str:
        """Tạo nội dung reminder"""
        days_left = self.calculate_days_until_due(rfi.due_date)
        priority_emoji = self.get_priority_emoji(rfi.priority)

        if days_left < 0:
            days_overdue = abs(days_left)
            message = f"""🚨 **RFI QUÁ HẠN**

**{rfi.rfi_id}**: {rfi.title}
⏰ Đã quá hạn: **{days_overdue} ngày**
📌 Ưu tiên: {priority_emoji} {rfi.priority}
👤 Phụ trách: {rfi.assigned_to}
📅 Deadline: {rfi.due_date}

⚠️ Cần xử lý ngay!
"""
        elif days_left == 0:
            message = f"""⚠️ **RFI ĐẾN HẠN HÔM NAY**

**{rfi.rfi_id}**: {rfi.title}
📌 Ưu tiên: {priority_emoji} {rfi.priority}
👤 Phụ trách: {rfi.assigned_to}
📅 Deadline: **HÔM NAY**

⏰ Cần hoàn thành trước 17:00!
"""
        else:
            message = f"""📅 **NHẮC NHỞ RFI SẮP HẾT HẠN**

**{rfi.rfi_id}**: {rfi.title}
⏰ Còn **{days_left} ngày**
📌 Ưu tiên: {priority_emoji} {rfi.priority}
👤 Phụ trách: {rfi.assigned_to}
📅 Deadline: {rfi.due_date}

Vui lòng kiểm tra và xử lý!
"""
        return message

    def process_reminder(self, rfi: RFIDeadline) -> Optional[EscalationEvent]:
        """Xử lý reminder cho một RFI"""
        if not self.should_remind(rfi):
            return None

        message = self.generate_reminder_message(rfi)
        days_left = self.calculate_days_until_due(rfi.due_date)

        # Xác định recipients theo escalation
        recipients = [rfi.assigned_to]

        if days_left < 0 or days_left <= 1:
            # Thêm PM
            recipients.append("Project Manager")

        if days_left < 0 and rfi.priority in ["HIGH", "CRITICAL"]:
            # Thêm stakeholders
            recipients.append("Design Lead")
            recipients.append("Construction Manager")

        event = EscalationEvent(
            timestamp=datetime.now().isoformat(),
            rfi_id=rfi.rfi_id,
            event_type="reminder" if days_left >= 0 else "overdue_reminder",
            message=message,
            recipients=recipients
        )

        self.events.append(event)
        rfi.last_reminder = datetime.now().isoformat()

        if days_left < 0:
            rfi.escalation_level += 1

        return event

    def scan_all(self, rfis: List[RFIDeadline]) -> List[EscalationEvent]:
        """Scan tất cả RFI và xử lý reminders"""
        events = []
        for rfi in rfis:
            event = self.process_reminder(rfi)
            if event:
                events.append(event)

        if events:
            self._save_data()

        return events

    def generate_dashboard(self, rfis: List[RFIDeadline]) -> Dict:
        """Tạo dashboard trạng thái"""
        summary = {
            "total": len(rfis),
            "by_status": {},
            "by_priority": {},
            "overdue": [],
            "due_soon": [],
            "critical": []
        }

        for rfi in rfis:
            status = self.get_status(rfi)

            # Count by status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

            # Count by priority
            summary["by_priority"][rfi.priority] = summary["by_priority"].get(rfi.priority, 0) + 1

            # Add to overdue list
            if status == "OVERDUE":
                summary["overdue"].append({
                    "id": rfi.rfi_id,
                    "title": rfi.title,
                    "days_overdue": abs(self.calculate_days_until_due(rfi.due_date)),
                    "priority": rfi.priority
                })

            # Add to due soon list
            if status in ["DUE_TODAY", "DUE_SOON"]:
                summary["due_soon"].append({
                    "id": rfi.rfi_id,
                    "title": rfi.title,
                    "days_left": self.calculate_days_until_due(rfi.due_date),
                    "priority": rfi.priority
                })

            # Add critical items
            if rfi.priority == "CRITICAL" and status != "CLOSED":
                summary["critical"].append({
                    "id": rfi.rfi_id,
                    "title": rfi.title,
                    "status": status,
                    "assigned_to": rfi.assigned_to
                })

        return summary

# =============================================================================
# CLI INTERFACE
# =============================================================================

def print_dashboard(dashboard: Dict):
    """In dashboard ra console"""
    print("\n" + "="*60)
    print("📊 RFI DEADLINE DASHBOARD")
    print("="*60)

    print(f"\n📈 Tổng số: {dashboard['total']} RFI")

    print("\n📋 Theo trạng thái:")
    for status, count in sorted(dashboard["by_status"].items()):
        emoji = {
            "ON_TRACK": "✅",
            "DUE_THIS_WEEK": "🟡",
            "DUE_SOON": "🟠",
            "DUE_TODAY": "⚠️",
            "OVERDUE": "🚨",
            "CLOSED": "✅✅"
        }.get(status, "⚪")
        print(f"  {emoji} {status}: {count}")

    print("\n🔴 Ưu tiên:")
    for priority, count in sorted(dashboard["by_priority"].items()):
        emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }.get(priority, "⚪")
        print(f"  {emoji} {priority}: {count}")

    if dashboard["overdue"]:
        print("\n🚨 QUÁ HẠN:")
        for item in sorted(dashboard["overdue"], key=lambda x: -x["days_overdue"]):
            print(f"  • {item['id']}: {item['title']} "
                  f"(quá {item['days_overdue']} ngày)")

    if dashboard["due_soon"]:
        print("\n⚠️ SẮP HẾT HẠN:")
        for item in sorted(dashboard["due_soon"], key=lambda x: x["days_left"]):
            days_str = "HÔM NAY" if item["days_left"] == 0 else f"{item['days_left']} ngày"
            print(f"  • {item['id']}: {item['title']} ({days_str})")

    if dashboard["critical"]:
        print("\n🔴 CRITICAL:")
        for item in dashboard["critical"]:
            print(f"  • {item['id']}: {item['title']} [{item['status']}]")

    print("\n" + "="*60)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="RFI Deadline Notification & Escalation Engine"
    )
    parser.add_argument("--scan", action="store_true",
                      help="Scan tất cả RFI và gửi reminders")
    parser.add_argument("--days", type=int, default=7,
                      help="Số ngày scan trước (mặc định: 7)")
    parser.add_argument("--rfi", help="RFI ID cụ thể")
    parser.add_argument("--status", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                      help="Lọc theo ưu tiên")
    parser.add_argument("--output", "-o", help="Lưu kết quả ra JSON")
    parser.add_argument("--data", default="rfi_deadlines.json",
                      help="File dữ liệu RFI")

    args = parser.parse_args()

    # Initialize tracker
    tracker = DeadlineTracker(args.data)

    # Sample RFI data (trong thực tế sẽ load từ database)
    sample_rfis = [
        RFIDeadline(
            rfi_id="RFI-001",
            title="Yêu cầu xác nhận kích thước móng",
            status="OPEN",
            priority="HIGH",
            submitted_date=(datetime.now() - timedelta(days=5)).isoformat(),
            due_date=(datetime.now() + timedelta(days=1)).isoformat(),
            assigned_to="Nguyễn Văn A",
            category="STRUCTURAL"
        ),
        RFIDeadline(
            rfi_id="RFI-002",
            title="Thay đổi vật liệu tầng 5",
            status="OPEN",
            priority="CRITICAL",
            submitted_date=(datetime.now() - timedelta(days=10)).isoformat(),
            due_date=(datetime.now() - timedelta(days=2)).isoformat(),
            assigned_to="Trần Thị B",
            category="ARCHITECTURAL"
        ),
        RFIDeadline(
            rfi_id="RFI-003",
            title="Xác nhận cao độ đấu nối",
            status="OPEN",
            priority="MEDIUM",
            submitted_date=(datetime.now() - timedelta(days=3)).isoformat(),
            due_date=(datetime.now() + timedelta(days=5)).isoformat(),
            assigned_to="Lê Văn C",
            category="MEP"
        ),
        RFIDeadline(
            rfi_id="RFI-004",
            title="Kiểm tra chi tiết neo",
            status="OPEN",
            priority="LOW",
            submitted_date=(datetime.now() - timedelta(days=2)).isoformat(),
            due_date=(datetime.now() + timedelta(days=10)).isoformat(),
            assigned_to="Phạm Văn D",
            category="STRUCTURAL"
        )
    ]

    if args.scan:
        # Scan all RFIs
        events = tracker.scan_all(sample_rfis)

        # Generate dashboard
        dashboard = tracker.generate_dashboard(sample_rfis)
        print_dashboard(dashboard)

        if events:
            print(f"\n📧 Đã tạo {len(events)} notification(s)")
            for event in events:
                print(f"\n{event.message}")

        if args.output:
            output = {
                "dashboard": dashboard,
                "events": [asdict(e) for e in events],
                "timestamp": datetime.now().isoformat()
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Đã lưu vào: {args.output}")

    elif args.rfi:
        # Single RFI check
        rfi = next((r for r in sample_rfis if r.rfi_id == args.rfi), None)
        if rfi:
            status = tracker.get_status(rfi)
            days_left = tracker.calculate_days_until_due(rfi.due_date)

            print(f"\n📋 RFI: {rfi.rfi_id}")
            print(f"   Tiêu đề: {rfi.title}")
            print(f"   Trạng thái: {tracker.get_status_emoji(status)} {status}")
            print(f"   Ưu tiên: {tracker.get_priority_emoji(rfi.priority)} {rfi.priority}")
            print(f"   Deadline: {rfi.due_date}")

            if days_left < 0:
                print(f"   ⚠️ Đã quá hạn: {abs(days_left)} ngày")
            elif days_left == 0:
                print(f"   ⚠️ Hết hạn: HÔM NAY")
            else:
                print(f"   Còn: {days_left} ngày")

            if tracker.should_remind(rfi):
                print(f"\n📧 Cần gửi reminder!")
                print(tracker.generate_reminder_message(rfi))
        else:
            print(f"❌ Không tìm thấy RFI: {args.rfi}")

    else:
        # Show dashboard only
        dashboard = tracker.generate_dashboard(sample_rfis)
        print_dashboard(dashboard)

if __name__ == "__main__":
    main()
