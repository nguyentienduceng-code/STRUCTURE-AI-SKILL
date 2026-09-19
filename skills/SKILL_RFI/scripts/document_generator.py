"""
SKILL_RFI - Document Generator (RFI/NCR/Submittal/CO/TQ)
Tạo tất cả các loại giao dịch kỹ thuật

Usage:
    python document_generator.py --type RFI --issue "Thiếu mác bê tông cột"
    python document_generator.py --type NCR --issue "Vết nứt cột tầng 3"
    python document_generator.py --type SUBMITTAL --issue "Shop Drawing dầm B1"
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

DOCUMENT_TYPES = {
    "RFI": {
        "name": "Request for Information",
        "short_name": "RFI",
        "from_parties": ["Designer", "CSHT", "Contractor", "QC"],
        "to_parties": ["Designer", "CSHT"],
        "default_deadline": 7,
        "urgency_keywords": ["sập", "nguy hiểm", "an toàn", "nghiêm trọng", "critical"]
    },
    "NCR": {
        "name": "Non-Conformance Report",
        "short_name": "NCR",
        "from_parties": ["CSHT", "QC", "Owner"],
        "to_parties": ["Contractor"],
        "default_deadline": 1,
        "urgency_keywords": ["sập", "nguy hiểm", "an toàn", "nứt", "vết nứt", "critical"]
    },
    "SUBMITTAL": {
        "name": "Shop Drawing / Material Submittal",
        "short_name": "SUB",
        "from_parties": ["Contractor"],
        "to_parties": ["Designer", "CSHT"],
        "default_deadline": 14,
        "urgency_keywords": ["gấp", "khẩn", "cần gấp"]
    },
    "CO": {
        "name": "Change Order",
        "short_name": "CO",
        "from_parties": ["Contractor", "Designer"],
        "to_parties": ["Owner", "CSHT"],
        "default_deadline": 3,
        "urgency_keywords": ["phát sinh", "thay đổi", "bổ sung", "tăng giảm"]
    },
    "TQ": {
        "name": "Technical Query",
        "short_name": "TQ",
        "from_parties": ["Contractor", "CSHT"],
        "to_parties": ["Designer"],
        "default_deadline": 5,
        "urgency_keywords": ["phức tạp", "cần phân tích", "chuyên sâu"]
    },
    "PBRFI": {
        "name": "Pre-Bid Request for Information",
        "short_name": "PB-RFI",
        "from_parties": ["Contractor"],
        "to_parties": ["Owner", "Designer"],
        "default_deadline": 3,
        "urgency_keywords": ["trước đấu thầu", "làm rõ"]
    }
}

PRIORITY_CONFIG = {
    "CRITICAL": {
        "keywords": ["sập", "nguy hiểm", "an toàn", "nghiêm trọng", "critical", "cháy", "nổ", "nứt"],
        "deadline_days": 1,
        "symbol": "🔴"
    },
    "URGENT": {
        "keywords": ["chậm tiến độ", "delay", "schedule", "cost", "phát sinh", "thay đổi", "gấp"],
        "deadline_days": 3,
        "symbol": "🟠"
    },
    "HIGH": {
        "keywords": ["thiếu", "missing", "cần xác nhận", "không rõ", "unclear", "quan trọng"],
        "deadline_days": 7,
        "symbol": "🟡"
    },
    "NORMAL": {
        "keywords": ["xác nhận", "confirm", "làm rõ", "bổ sung"],
        "deadline_days": 14,
        "symbol": "🟢"
    },
    "ROUTINE": {
        "keywords": ["cập nhật", "thông tin thêm", "routine"],
        "deadline_days": 21,
        "symbol": "🔵"
    }
}

NCR_SEVERITY = {
    "MINOR": {
        "keywords": ["nhỏ", "minor", "không ảnh hưởng"],
        "action": "Sửa và kiểm tra"
    },
    "MAJOR": {
        "keywords": ["lớn", "major", "ảnh hưởng chất lượng"],
        "action": "Dừng, đề xuất, chờ duyệt"
    },
    "CRITICAL": {
        "keywords": ["nghiêm trọng", "critical", "kết cấu", "an toàn"],
        "action": "Dừng ngay, báo cáo Owner"
    }
}


# ============================================================================
# DOCUMENT GENERATOR
# ============================================================================

def generate_document(
    doc_type,
    issue_description,
    context,
    project_name,
    from_party=None,
    to_party=None,
    drawings=None,
    impact=None,
    deadline_days=None,
    priority_override=None,
    related_docs=None,
    attachments=None,
    submitted_by="Trợ lý AI - Kỹ sư QLTK"
):
    """
    Tạo một tài liệu giao dịch (RFI/NCR/Submittal/CO/TQ).
    """

    config = DOCUMENT_TYPES.get(doc_type.upper(), DOCUMENT_TYPES["RFI"])

    # Generate document code
    doc_date = datetime.now()
    issue_hash = int(hashlib.md5(issue_description.encode('utf-8')).hexdigest()[:6], 16) % 1000

    # Party prefix
    party_prefix = from_party[:3].upper() if from_party else "GEN"
    doc_code = f"{config['short_name']}-{party_prefix}-{doc_date.strftime('%Y%m%d')}-{issue_hash:03d}"

    # Determine priority
    if priority_override:
        priority = priority_override.upper()
        priority_config = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["HIGH"])
        priority_symbol = priority_config["symbol"]
        if deadline_days is None:
            deadline_days = priority_config["deadline_days"]
    else:
        priority = detect_priority(issue_description, impact, config)
        priority_config = PRIORITY_CONFIG[priority]
        priority_symbol = priority_config["symbol"]
        if deadline_days is None:
            deadline_days = priority_config["deadline_days"]

    # Calculate deadline
    deadline_date = doc_date + timedelta(days=deadline_days)

    # Determine NCR severity if applicable
    ncr_severity = None
    if doc_type.upper() == "NCR":
        ncr_severity = detect_ncr_severity(issue_description)
        if ncr_severity == "CRITICAL":
            priority = "CRITICAL"
            priority_symbol = "🔴"
            deadline_days = 1
            deadline_date = doc_date + timedelta(days=1)

    # Auto-generate specific questions/items
    items = generate_items(doc_type, issue_description)

    # Determine recipient if not specified
    if to_party is None and config["to_parties"]:
        to_party = config["to_parties"][0]

    # Create document data
    doc_data = {
        "Doc_Code": doc_code,
        "Doc_Type": doc_type.upper(),
        "Doc_Name": config["name"],
        "Date_Issued": doc_date.strftime('%d/%m/%Y'),
        "Project_Name": project_name,
        "Priority": priority,
        "Priority_Symbol": priority_symbol,
        "Status": "Draft",
        "From_Party": from_party or "AI Assistant",
        "To_Party": to_party,
        "Issue": {
            "Summary": issue_description,
            "Context": context,
            "Related_Drawings": drawings if drawings else [],
            "Items": items,
            "Related_Documents": related_docs or []
        },
        "Impact_If_Not_Resolved": impact if impact else "Có thể ảnh hưởng đến tiến độ và chất lượng.",
        "Deadline": deadline_date.strftime('%d/%m/%Y'),
        "Days_To_Deadline": deadline_days,
        "Submitted_By": submitted_by,
        "Attachments": attachments or [],
        "Tracking": {
            "Created_Date": doc_date.strftime('%d/%m/%Y'),
            "Days_Open": 0,
            "Overdue": False,
            "Escalation_Level": 0,
            "Last_Updated": doc_date.strftime('%d/%m/%Y'),
            "History": [
                {
                    "date": doc_date.strftime('%d/%m/%Y %H:%M'),
                    "action": "Created",
                    "user": "System"
                }
            ]
        },
        "Response": None,
        "Approved": None,
        "Resolved_Date": None
    }

    # Add NCR-specific fields
    if doc_type.upper() == "NCR" and ncr_severity:
        doc_data["NCR_Severity"] = ncr_severity
        doc_data["NCR_Severity_Action"] = NCR_SEVERITY[ncr_severity]["action"]

    # Add Submittal-specific fields
    if doc_type.upper() == "SUBMITTAL":
        doc_data["Submittal_Status"] = "Pending Review"
        doc_data["Approval_History"] = []

    # Add CO-specific fields
    if doc_type.upper() == "CO":
        doc_data["CO_Amount"] = 0
        doc_data["CO_Time_Impact"] = 0
        doc_data["CO_Status"] = "Pending Approval"

    return doc_data


def detect_priority(issue_description, impact, config):
    """Tự động phát hiện mức ưu tiên."""
    text = (issue_description + " " + (impact or "")).lower()

    # Check document-specific urgency first
    for keyword in config.get("urgency_keywords", []):
        if keyword in text:
            return "CRITICAL"

    # Check general priority
    for priority in ["CRITICAL", "URGENT", "HIGH", "NORMAL", "ROUTINE"]:
        config_p = PRIORITY_CONFIG[priority]
        for keyword in config_p["keywords"]:
            if keyword in text:
                return priority

    return "HIGH"  # Default for RFI/TQ


def detect_ncr_severity(issue_description):
    """Phát hiện mức độ nghiêm trọng của NCR."""
    text = issue_description.lower()

    for severity, config in NCR_SEVERITY.items():
        for keyword in config["keywords"]:
            if keyword in text:
                return severity

    return "MINOR"  # Default


def generate_items(doc_type, issue_description):
    """Tự động tạo danh sách items/câu hỏi dựa trên loại tài liệu."""
    items = []
    text = issue_description.lower()

    if doc_type.upper() == "RFI":
        if "mác" in text or "bê tông" in text:
            items.append("Mác bê tông thiết kế là bao nhiêu? (VD: B25, B30)")
            items.append("Có yêu cầu đặc biệt về độ bền không?")
        if "thép" in text:
            items.append("Loại thép và cấp độ bền là gì? (VD: CB400-V, CB500-V)")
        if "kích thước" in text or "chiều dài" in text:
            items.append("Kích thước thiết kế là bao nhiêu?")
        if not items:
            items.append("Yêu cầu cung cấp thông tin đầy đủ.")

    elif doc_type.upper() == "NCR":
        items.append("Mô tả chi tiết không phù hợp:")
        items.append("Vị trí cụ thể:")
        items.append("Nguyên nhân dự kiến:")
        items.append("Đề xuất biện pháp khắc phục:")

    elif doc_type.upper() == "SUBMITTAL":
        items.append("Mô tả item gửi duyệt:")
        items.append("Reference drawing/specification:")
        items.append("Yêu cầu kiểm tra cụ thể:")

    elif doc_type.upper() == "CO":
        items.append("Mô tả thay đổi:")
        items.append("Khối lượng thay đổi (+/-):")
        items.append("Đơn giá áp dụng:")
        items.append("Ảnh hưởng tiến độ (ngày):")

    elif doc_type.upper() == "TQ":
        items.append("Câu hỏi kỹ thuật cụ thể:")
        items.append("Phân tích đã thực hiện:")
        items.append("Đề xuất của bạn:")

    return items


def save_document(doc_data, registry_path=None):
    """Lưu tài liệu vào registry."""

    if registry_path is None:
        registry_path = Path(__file__).parent.parent / "data" / "document_registry.json"

    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = create_empty_registry()

    # Update project name
    if doc_data["Project_Name"] and registry.get("project_name") != doc_data["Project_Name"]:
        if registry.get("project_name"):
            print(f"⚠️ Warning: Registry đang dùng cho dự án '{registry['project_name']}'")
        registry["project_name"] = doc_data["Project_Name"]

    # Add document to appropriate category
    doc_type = doc_data["Doc_Type"]
    if doc_type not in registry["documents"]:
        registry["documents"][doc_type] = []

    registry["documents"][doc_type].append(doc_data)
    registry["last_updated"] = datetime.now().strftime('%Y-%m-%d')

    # Update statistics
    update_statistics(registry)

    # Save
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✅ Đã lưu: {doc_data['Doc_Code']}")
    return doc_data["Doc_Code"]


def create_empty_registry():
    """Tạo registry rỗng."""
    return {
        "project_name": "",
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "parties": {},
        "documents": {
            "RFI": [],
            "NCR": [],
            "SUBMITTAL": [],
            "CO": [],
            "TQ": [],
            "PBRFI": []
        },
        "statistics": {}
    }


def update_statistics(registry):
    """Cập nhật thống kê registry."""

    stats = {}

    for doc_type, docs in registry["documents"].items():
        type_stats = {
            "total": len(docs),
            "draft": 0,
            "open": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "overdue": 0,
            "critical": 0
        }

        today = datetime.now()

        for doc in docs:
            status = doc.get("Status", "Draft")

            if status in ["Draft"]:
                type_stats["draft"] += 1
            elif status in ["Submitted", "Under Review"]:
                type_stats["open"] += 1
            elif status in ["Pending", "Pending Review", "Pending Approval"]:
                type_stats["pending"] += 1
            elif status in ["Approved", "Closed"]:
                type_stats["approved"] += 1
            elif status in ["Rejected"]:
                type_stats["rejected"] += 1

            # Check overdue
            if doc.get("Tracking", {}).get("Overdue", False):
                type_stats["overdue"] += 1

            # Check critical
            if doc.get("Priority") == "CRITICAL" and status not in ["Approved", "Closed"]:
                type_stats["critical"] += 1

        stats[doc_type.lower()] = type_stats

    registry["statistics"] = stats


def generate_markdown(doc_data):
    """Chuyển document JSON thành Markdown format."""

    doc_type = doc_data["Doc_Type"]
    doc_name = doc_data["Doc_Name"]

    md = f"""# {doc_name.upper()} ({doc_type})

---

**Mã:** {doc_data['Doc_Code']}
**Ngày phát hành:** {doc_data['Date_Issued']}
**Dự án:** {doc_data['Project_Name']}
**Mức ưu tiên:** {doc_data['Priority_Symbol']} {doc_data['Priority']}
**Trạng thái:** {doc_data['Status']}

---

## 1. THÔNG TIN GỬI/NHẬN

**Từ (From):** {doc_data['From_Party']}
**Đến (To):** {doc_data['To_Party']}
**Người phát hành:** {doc_data['Submitted_By']}

"""

    # NCR specific
    if doc_type == "NCR" and doc_data.get("NCR_Severity"):
        md += f"**Mức độ NCR:** {doc_data['NCR_Severity']} - {doc_data.get('NCR_Severity_Action', '')}\n\n"

    md += f"""## 2. NỘI DUNG

**Tóm tắt:**
{doc_data['Issue']['Summary']}

**Bối cảnh:**
{doc_data['Issue']['Context']}
"""

    if doc_data['Issue']['Related_Drawings']:
        md += f"\n**Bản vẽ/Tài liệu liên quan:**\n"
        for dwg in doc_data['Issue']['Related_Drawings']:
            md += f"- {dwg}\n"

    if doc_data['Issue']['Items']:
        md += f"\n---\n\n## 3. CÁC MỤC CỤ THỂ\n\n"
        for idx, item in enumerate(doc_data['Issue']['Items'], 1):
            md += f"{idx}. {item}\n"

    if doc_data['Issue']['Related_Documents']:
        md += f"\n**Tài liệu liên quan:**\n"
        for ref in doc_data['Issue']['Related_Documents']:
            md += f"- {ref}\n"

    md += f"""
---

## 4. ẢNH HƯỞNG NẾU KHÔNG XỬ LÝ

{doc_data['Impact_If_Not_Resolved']}

---

## 5. THÔNG TIN PHẢN HỒI

**Thời hạn:** {doc_data['Deadline']}
**Còn lại:** {doc_data['Days_To_Deadline']} ngày

"""

    if doc_data.get("Response"):
        md += f"""
---

## 6. PHẢN HỒI ĐÃ NHẬN

**Ngày nhận:** {doc_data['Response'].get('Date', 'N/A')}
**Nội dung:**
{doc_data['Response'].get('Content', '')}

"""

    md += f"""---
## 7. TRẠNG THÁI

**Trạng thái hiện tại:** {doc_data['Status']}

**Lịch sử:**
"""
    for h in doc_data.get("Tracking", {}).get("History", []):
        md += f"- [{h['date']}] {h['action']}\n"

    md += f"""

---

*Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""

    return md


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SKILL_RFI - Tạo Document (RFI/NCR/Submittal/CO/TQ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
    # Tạo RFI
    python document_generator.py --type RFI --issue "Thiếu mác bê tông cột" --project "Dự án ABC"

    # Tạo NCR
    python document_generator.py --type NCR --issue "Vết nứt cột tầng 3" --project "Dự án ABC" --from-party CSHT

    # Tạo Submittal
    python document_generator.py --type SUBMITTAL --issue "Shop Drawing dầm B1" --project "Dự án ABC" --from-party Contractor
        """
    )

    parser.add_argument("--type", required=True, choices=["RFI", "NCR", "SUBMITTAL", "CO", "TQ", "PBRFI"],
                        help="Loại tài liệu")
    parser.add_argument("--issue", required=True, help="Mô tả vấn đề cần xử lý")
    parser.add_argument("--context", help="Bối cảnh chi tiết")
    parser.add_argument("--project", required=True, help="Tên dự án")
    parser.add_argument("--from-party", help="Bên gửi (Designer/CSHT/Contractor/QC)")
    parser.add_argument("--to-party", help="Bên nhận")
    parser.add_argument("--drawings", help="Bản vẽ liên quan (phân cách bằng ;)")
    parser.add_argument("--impact", help="Ảnh hưởng nếu không xử lý")
    parser.add_argument("--deadline", type=int, help="Số ngày deadline")
    parser.add_argument("--priority", choices=["critical", "urgent", "high", "normal", "routine"],
                        help="Override mức ưu tiên")
    parser.add_argument("--output", help="File output (mặc định: lưu vào registry)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Format output")

    args = parser.parse_args()

    if not args.context:
        args.context = f"Trong quá trình kiểm tra/giám sát dự án {args.project}, phát hiện vấn đề: {args.issue}"

    drawings = args.drawings.split(";") if args.drawings else None

    doc = generate_document(
        doc_type=args.type,
        issue_description=args.issue,
        context=args.context,
        project_name=args.project,
        from_party=args.from_party,
        to_party=args.to_party,
        drawings=drawings,
        impact=args.impact,
        deadline_days=args.deadline,
        priority_override=args.priority
    )

    # Save to registry
    save_document(doc)

    # Output
    if args.format == "json":
        output = json.dumps(doc, indent=2, ensure_ascii=False)
    else:
        output = generate_markdown(doc)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Đã xuất: {args.output}")
    else:
        print(output)
