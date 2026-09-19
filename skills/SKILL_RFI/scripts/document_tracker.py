"""
SKILL_RFI - Document Tracker
Theo dõi trạng thái tất cả các loại tài liệu (RFI/NCR/Submittal/CO/TQ)

Usage:
    python document_tracker.py --list
    python document_tracker.py --list --type RFI
    python document_tracker.py --status RFI-DES-20260830-001 --update Approved
    python document_tracker.py --overdue
    python document_tracker.py --critical
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def load_registry(registry_path=None):
    """Load document registry."""
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / "data" / "document_registry.json"

    if not registry_path.exists():
        print(f"❌ Registry not found: {registry_path}")
        return None

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_registry(registry, registry_path=None):
    """Save document registry."""
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / "data" / "document_registry.json"

    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def update_tracking(doc, registry):
    """Cập nhật tracking info cho một tài liệu."""

    today = datetime.now()

    # Parse deadline
    try:
        deadline = datetime.strptime(doc.get("Deadline", ""), '%d/%m/%Y')
    except:
        deadline = today + timedelta(days=7)

    # Calculate days
    created = datetime.strptime(doc["Tracking"]["Created_Date"], '%d/%m/%Y')
    days_open = (today - created).days
    days_to_deadline = (deadline - today).days

    # Update tracking
    doc["Tracking"]["Days_Open"] = days_open
    doc["Days_To_Deadline"] = days_to_deadline
    doc["Tracking"]["Overdue"] = days_to_deadline < 0
    doc["Tracking"]["Last_Updated"] = today.strftime('%d/%m/%Y')

    # Auto-escalation check
    if days_to_deadline < 0:
        overdue_days = abs(days_to_deadline)
        if overdue_days > 14:
            doc["Tracking"]["Escalation_Level"] = 3
        elif overdue_days > 7:
            doc["Tracking"]["Escalation_Level"] = 2
        elif overdue_days > 2:
            doc["Tracking"]["Escalation_Level"] = 1

    return doc


def list_documents(registry, doc_type_filter=None, status_filter=None, priority_filter=None,
                   overdue_only=False, critical_only=False):
    """Liệt kê tất cả tài liệu với filters."""

    all_docs = []

    # Collect all documents
    doc_types = registry.get("documents", {})
    if doc_type_filter:
        doc_types = {doc_type_filter.upper(): doc_types.get(doc_type_filter.upper(), [])}

    for dtype, docs in doc_types.items():
        for doc in docs:
            doc["_doc_type"] = dtype
            all_docs.append(doc)

    # Apply filters
    if status_filter:
        all_docs = [d for d in all_docs if d.get("Status") == status_filter]

    if priority_filter:
        all_docs = [d for d in all_docs if d.get("Priority") == priority_filter.upper()]

    if overdue_only:
        all_docs = [d for d in all_docs if d.get("Tracking", {}).get("Overdue", False)]

    if critical_only:
        all_docs = [d for d in all_docs if d.get("Priority") == "CRITICAL"]

    # Update tracking for all
    for doc in all_docs:
        update_tracking(doc, registry)

    # Sort by priority then deadline
    priority_order = {"CRITICAL": 0, "URGENT": 1, "HIGH": 2, "NORMAL": 3, "ROUTINE": 4}
    all_docs.sort(key=lambda x: (
        priority_order.get(x.get("Priority", "NORMAL"), 5),
        x.get("Days_To_Deadline", 999)
    ))

    return all_docs


def print_document_list(docs, title="DOCUMENT LIST"):
    """In danh sách tài liệu ra console."""

    if not docs:
        print("📭 Không có tài liệu nào phù hợp.")
        return

    # Group by type
    by_type = {}
    for doc in docs:
        dtype = doc.get("_doc_type", "UNKNOWN")
        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(doc)

    # Header
    print(f"\n╔{'═' * 90}╗")
    print(f"║ {title.center(88)} ║")
    print(f"╠{'═' * 90}╣")

    # Stats
    total = len(docs)
    critical = len([d for d in docs if d.get("Priority") == "CRITICAL"])
    overdue = len([d for d in docs if d.get("Tracking", {}).get("Overdue", False)])

    print(f"║ Tổng: {total} | Critical: {critical} | Quá hạn: {overdue}".ljust(91) + "║")
    print(f"╠{'═' * 90}╣")

    for dtype, type_docs in by_type.items():
        print(f"║ 📄 {dtype} ({len(type_docs)})".ljust(91) + "║")
        print(f"╟{'─' * 90}╢")

        # Column headers
        print(f"║ {'Mã':<22} {'Mức':<10} {'Từ':<12} {'Đến':<12} {'Deadline':<12} {'Còn lại':<10} {'Trạng thái':<8} ║")
        print(f"╟{'─' * 90}╢")

        for doc in type_docs[:10]:  # Limit 10 per type
            code = doc.get("Doc_Code", "")[:20]
            priority_sym = doc.get("Priority_Symbol", "")
            priority = doc.get("Priority", "")[:8]
            from_party = doc.get("From_Party", "")[:10]
            to_party = doc.get("To_Party", "")[:10]
            deadline = doc.get("Deadline", "")[:10]
            days_left = doc.get("Days_To_Deadline", 0)

            if days_left < 0:
                days_str = f"{abs(days_left)}d!!"
            elif days_left == 0:
                days_str = "Hnay!"
            else:
                days_str = f"{days_left}d"

            status = doc.get("Status", "")[:8]

            print(f"║ {code:<22} {priority_sym}{priority:<9} {from_party:<12} {to_party:<12} {deadline:<12} {days_str:<10} {status:<8} ║")

        if len(type_docs) > 10:
            print(f"║   ... và {len(type_docs) - 10} tài liệu khác".ljust(91) + "║")

        print(f"╟{'─' * 90}╢")

    print(f"╚{'═' * 90}╝")


def update_document_status(doc_code, new_status, notes=None, registry=None):
    """Cập nhật trạng thái tài liệu."""

    if registry is None:
        registry = load_registry()
        if registry is None:
            return False

    today = datetime.now().strftime('%d/%m/%Y %H:%M')

    for dtype, docs in registry.get("documents", {}).items():
        for doc in docs:
            if doc.get("Doc_Code") == doc_code:
                old_status = doc.get("Status")

                # Update status
                doc["Status"] = new_status

                # Add to history
                if "History" not in doc["Tracking"]:
                    doc["Tracking"]["History"] = []

                doc["Tracking"]["History"].append({
                    "date": today,
                    "action": f"Status changed: {old_status} → {new_status}",
                    "user": "System"
                })

                if notes:
                    doc["Tracking"]["History"].append({
                        "date": today,
                        "action": f"Notes: {notes}",
                        "user": "System"
                    })

                # Update tracking
                update_tracking(doc, registry)

                # Auto-update based on type
                if new_status in ["Approved", "Closed"]:
                    doc["Approved"] = today
                elif new_status in ["Rejected"]:
                    doc["Rejected"] = today

                # Update specific status fields
                if doc.get("Doc_Type") == "SUBMITTAL":
                    if new_status == "Approved":
                        doc["Submittal_Status"] = "Approved"
                    elif new_status == "Revise and Resubmit":
                        doc["Submittal_Status"] = "Revision Required"
                elif doc.get("Doc_Type") == "CO":
                    if new_status == "Approved":
                        doc["CO_Status"] = "Approved"

                save_registry(registry)
                print(f"✅ Đã cập nhật: {doc_code} → {new_status}")
                return True

    print(f"❌ Không tìm thấy: {doc_code}")
    return False


def add_response(doc_code, response_content, attachments=None, registry=None):
    """Thêm phản hồi cho tài liệu."""

    if registry is None:
        registry = load_registry()
        if registry is None:
            return False

    today = datetime.now().strftime('%d/%m/%Y %H:%M')

    for dtype, docs in registry.get("documents", {}).items():
        for doc in docs:
            if doc.get("Doc_Code") == doc_code:
                doc["Response"] = {
                    "Content": response_content,
                    "Date": today,
                    "Attachments": attachments or []
                }

                # Add to history
                doc["Tracking"]["History"].append({
                    "date": today,
                    "action": "Response received",
                    "user": "Recipient"
                })

                # Auto-update status based on doc type
                current_status = doc.get("Status", "Draft")
                if current_status == "Draft":
                    doc["Status"] = "Submitted"
                elif current_status == "Submitted":
                    doc["Status"] = "Under Review"

                save_registry(registry)
                print(f"✅ Đã thêm phản hồi cho: {doc_code}")
                return True

    print(f"❌ Không tìm thấy: {doc_code}")
    return False


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SKILL_RFI - Document Tracker")

    parser.add_argument("--list", action="store_true", help="Liệt kê tất cả tài liệu")
    parser.add_argument("--type", help="Filter theo loại (RFI/NCR/SUBMITTAL/CO/TQ)")
    parser.add_argument("--status", help="Filter theo trạng thái")
    parser.add_argument("--priority", help="Filter theo mức ưu tiên")
    parser.add_argument("--overdue", action="store_true", help="Chỉ hiển thị quá hạn")
    parser.add_argument("--critical", action="store_true", help="Chỉ hiển thị Critical")

    parser.add_argument("--update", help="Cập nhật trạng thái (mã tài liệu)")
    parser.add_argument("--new-status", help="Trạng thái mới")
    parser.add_argument("--notes", help="Ghi chú khi cập nhật")

    parser.add_argument("--response", help="Thêm phản hồi (mã tài liệu)")
    parser.add_argument("--content", help="Nội dung phản hồi")

    parser.add_argument("--detail", help="Hiển thị chi tiết một tài liệu (mã)")

    args = parser.parse_args()

    registry = load_registry()
    if registry is None:
        sys.exit(1)

    # Detail view
    if args.detail:
        for dtype, docs in registry.get("documents", {}).items():
            for doc in docs:
                if doc.get("Doc_Code") == args.detail:
                    update_tracking(doc, registry)
                    print(f"\n{'=' * 70}")
                    print(f"📄 {doc.get('Doc_Type')}: {doc['Doc_Code']}")
                    print(f"{'=' * 70}")
                    print(f"Trạng thái: {doc['Priority_Symbol']} {doc['Priority']} - {doc['Status']}")
                    print(f"Từ: {doc.get('From_Party')} → Đến: {doc.get('To_Party')}")
                    print(f"Deadline: {doc['Deadline']} (còn {doc['Days_To_Deadline']} ngày)")

                    if doc.get("NCR_Severity"):
                        print(f"NCR Severity: {doc['NCR_Severity']} - {doc.get('NCR_Severity_Action', '')}")

                    print(f"\n📝 Vấn đề: {doc['Issue']['Summary']}")
                    print(f"\n📖 Bối cảnh: {doc['Issue']['Context']}")

                    if doc.get("Response"):
                        print(f"\n💬 Phản hồi ({doc['Response'].get('Date', 'N/A')}):")
                        print(f"   {doc['Response'].get('Content', '')[:200]}...")

                    print(f"\n📜 Lịch sử:")
                    for h in doc.get("Tracking", {}).get("History", []):
                        print(f"  - [{h['date']}] {h['action']}")
                    break
        else:
            print(f"❌ Không tìm thấy: {args.detail}")

    # Update status
    elif args.update:
        if not args.new_status:
            print("❌ Cần chỉ định --new-status")
        else:
            update_document_status(args.update, args.new_status, args.notes, registry)

    # Add response
    elif args.response:
        if not args.content:
            print("❌ Cần nhập --content")
        else:
            add_response(args.response, args.content, registry=registry)

    # List view
    elif args.list:
        docs = list_documents(
            registry,
            args.type,
            args.status,
            args.priority,
            args.overdue,
            args.critical
        )
        title = f"DOCUMENT LIST"
        if args.type:
            title += f" - {args.type.upper()}"
        if args.priority:
            title += f" - {args.priority.upper()}"
        if args.overdue:
            title += " - QUÁ HẠN"
        if args.critical:
            title += " - CRITICAL"

        print_document_list(docs, title)

    else:
        parser.print_help()
