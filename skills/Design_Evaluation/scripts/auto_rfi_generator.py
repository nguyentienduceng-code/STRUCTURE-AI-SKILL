import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import hashlib
from datetime import datetime

def generate_rfi(issue_description, context, project_name, drawings=None, impact=None, deadline_days=7):
    """
    Tự động tạo RFI (Request for Information) khi phát hiện Data Missing hoặc mâu thuẫn thiết kế.

    Args:
        issue_description: Vấn đề cần làm rõ (ngắn gọn)
        context: Bối cảnh chi tiết (đang làm gì mà phát hiện vấn đề)
        project_name: Tên dự án
        drawings: List các bản vẽ liên quan
        impact: Ảnh hưởng nếu không làm rõ
        deadline_days: Thời hạn phản hồi (ngày)
    """

    # Tạo mã RFI tự động
    # FIX-LOGIC-02: Dùng hashlib.md5 thay vì hash() để đảm bảo deterministic
    rfi_date = datetime.now()
    issue_hash = int(hashlib.md5(issue_description.encode('utf-8')).hexdigest()[:6], 16) % 1000
    rfi_code = f"RFI-KC-{rfi_date.strftime('%Y%m%d')}-{issue_hash:03d}"

    # Phân loại mức độ ưu tiên
    if impact and any(keyword in impact.lower() for keyword in ['sập', 'nguy hiểm', 'an toàn', 'nghiêm trọng', 'critical']):
        priority = "URGENT"
        priority_color = "🔴"
    elif impact and any(keyword in impact.lower() for keyword in ['chậm tiến độ', 'delay', 'schedule', 'cost']):
        priority = "HIGH"
        priority_color = "🟠"
    else:
        priority = "NORMAL"
        priority_color = "🟡"

    # Tự động phát hiện loại vấn đề
    issue_category = "Khác"
    if "thiếu" in issue_description.lower() or "missing" in issue_description.lower():
        issue_category = "Thiếu thông tin"
    elif "mâu thuẫn" in issue_description.lower() or "conflict" in issue_description.lower():
        issue_category = "Mâu thuẫn giữa các tài liệu"
    elif "không rõ" in issue_description.lower() or "unclear" in issue_description.lower():
        issue_category = "Thông tin không rõ ràng"
    elif "tiêu chuẩn" in issue_description.lower() or "citation" in issue_description.lower():
        issue_category = "Yêu cầu bổ sung căn cứ tiêu chuẩn"

    # Tính deadline
    deadline_date = datetime.now()
    from datetime import timedelta
    deadline_date = deadline_date + timedelta(days=deadline_days)

    # Tạo template RFI
    rfi_content = {
        "RFI_Code": rfi_code,
        "Date_Issued": rfi_date.strftime('%d/%m/%Y'),
        "Project_Name": project_name,
        "Category": issue_category,
        "Priority": priority,
        "Priority_Symbol": priority_color,
        "Issue": {
            "Summary": issue_description,
            "Context": context,
            "Related_Drawings": drawings if drawings else ["Chưa xác định"],
            "Specific_Questions": []
        },
        "Impact_If_Not_Resolved": impact if impact else "Không thể tiếp tục phân tích/thiết kế. Có thể ảnh hưởng tiến độ.",
        "Response_Required_By": deadline_date.strftime('%d/%m/%Y'),
        "Submitted_By": "Trợ lý AI - Kỹ sư QLTK",
        "To": "Đơn vị Thiết kế / Tư vấn giám sát",
        "Status": "Open"
    }

    # Tự động tạo câu hỏi cụ thể
    if "thiếu" in issue_description.lower():
        rfi_content["Issue"]["Specific_Questions"].append(
            f"Yêu cầu bổ sung thông tin: {issue_description}"
        )
    if "mâu thuẫn" in issue_description.lower():
        rfi_content["Issue"]["Specific_Questions"].append(
            "Giá trị nào là đúng? Yêu cầu xác nhận và sửa đổi các tài liệu còn lại để thống nhất."
        )
    if "tiêu chuẩn" in issue_description.lower():
        rfi_content["Issue"]["Specific_Questions"].append(
            "Yêu cầu cung cấp căn cứ tính toán: Tiêu chuẩn (Mã + Năm), Điều/Bảng, Trang số."
        )

    # Thêm câu hỏi mặc định nếu chưa có
    if not rfi_content["Issue"]["Specific_Questions"]:
        rfi_content["Issue"]["Specific_Questions"].append(
            "Yêu cầu làm rõ thông tin và cung cấp tài liệu/bản vẽ cập nhật."
        )

    return rfi_content


def generate_rfi_document(rfi_data, output_format="json"):
    """
    Xuất RFI thành file văn bản (JSON hoặc DOCX).
    """

    if output_format == "json":
        return json.dumps(rfi_data, indent=2, ensure_ascii=False)

    elif output_format == "markdown":
        md = f"""# REQUEST FOR INFORMATION (RFI)

---

**RFI Code:** {rfi_data['RFI_Code']}
**Date Issued:** {rfi_data['Date_Issued']}
**Project:** {rfi_data['Project_Name']}
**Priority:** {rfi_data['Priority_Symbol']} {rfi_data['Priority']}
**Category:** {rfi_data['Category']}

---

## 1. VẤN ĐỀ CẦN LÀM RÕ

**Tóm tắt:**
{rfi_data['Issue']['Summary']}

**Bối cảnh:**
{rfi_data['Issue']['Context']}

**Bản vẽ/Tài liệu liên quan:**
"""
        for dwg in rfi_data['Issue']['Related_Drawings']:
            md += f"- {dwg}\n"

        md += f"""
---

## 2. CÂU HỎI CỤ THỂ

"""
        for idx, question in enumerate(rfi_data['Issue']['Specific_Questions'], 1):
            md += f"{idx}. {question}\n"

        md += f"""
---

## 3. ẢNH HƯỞNG NẾU KHÔNG LÀM RÕ

{rfi_data['Impact_If_Not_Resolved']}

---

## 4. THÔNG TIN PHẢN HỒI

**Thời hạn phản hồi:** {rfi_data['Response_Required_By']}
**Người gửi:** {rfi_data['Submitted_By']}
**Người nhận:** {rfi_data['To']}
**Trạng thái:** {rfi_data['Status']}

---

## 5. GHI CHÚ

- RFI này được tạo tự động bởi AI khi phát hiện thiếu dữ liệu trong quá trình phân tích kỹ thuật.
- Yêu cầu đơn vị thiết kế phản hồi qua email hoặc cập nhật trên hệ thống quản lý dự án.
- Nếu không nhận được phản hồi đúng hạn, vấn đề sẽ được leo thang lên Ban Quản lý Dự án.

---

*Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""
        return md

    return None


def batch_generate_rfis(data_missing_list, project_name):
    """
    Tạo hàng loạt RFI từ danh sách Data Missing.

    Args:
        data_missing_list: List các string "Data Missing: ..."
        project_name: Tên dự án
    """

    rfis = []

    for idx, missing_item in enumerate(data_missing_list, 1):
        # Parse "Data Missing: [Tên thông số]"
        if ":" in missing_item:
            issue = missing_item.split(":", 1)[1].strip()
        else:
            issue = missing_item

        context = f"Trong quá trình phân tích kỹ thuật, AI phát hiện thiếu thông số: {issue}. Không thể hoàn tất tính toán định lượng."

        rfi = generate_rfi(
            issue_description=issue,
            context=context,
            project_name=project_name,
            impact="Không thể kiểm tra đầy đủ các điều kiện chịu lực. Rủi ro kỹ thuật chưa được đánh giá.",
            deadline_days=7
        )

        rfis.append(rfi)

    return rfis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Generate RFI from Data Missing")
    parser.add_argument("--issue", required=True, help="Vấn đề cần làm rõ")
    parser.add_argument("--context", required=True, help="Bối cảnh chi tiết")
    parser.add_argument("--project", required=True, help="Tên dự án")
    parser.add_argument("--drawings", help="Bản vẽ liên quan (phân cách bằng ;)")
    parser.add_argument("--impact", help="Ảnh hưởng nếu không làm rõ")
    parser.add_argument("--deadline", type=int, default=7, help="Thời hạn phản hồi (ngày)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Format output")
    parser.add_argument("--output", help="File output (optional)")

    args = parser.parse_args()

    drawings = args.drawings.split(";") if args.drawings else None

    rfi = generate_rfi(
        issue_description=args.issue,
        context=args.context,
        project_name=args.project,
        drawings=drawings,
        impact=args.impact,
        deadline_days=args.deadline
    )

    output_text = generate_rfi_document(rfi, output_format=args.format)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"✅ RFI đã được xuất: {args.output}")
    else:
        print(output_text)
