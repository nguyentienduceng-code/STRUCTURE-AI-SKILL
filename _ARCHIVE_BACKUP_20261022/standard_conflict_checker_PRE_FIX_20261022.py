import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import os
from datetime import datetime

def load_standards_lock(repo_root):
    """
    Đọc STANDARDS_LOCK.md để lấy phiên bản tiêu chuẩn chính thức.
    """

    standards_lock_path = os.path.join(repo_root, "STANDARDS_LOCK.md")

    if not os.path.exists(standards_lock_path):
        return None

    standards = {}

    with open(standards_lock_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

        for line in lines:
            # Parse dòng dạng: | TCVN 5574 | 2018 | Bê tông | ✅ Active |
            if "|" in line and "TCVN" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    code = parts[1]
                    year = parts[2]
                    status = parts[4]

                    if "Active" in status or "✅" in status:
                        standards[code] = f"{code}:{year}"

    return standards


def extract_standards_from_results(results_list):
    """
    Trích xuất tất cả các tiêu chuẩn được sử dụng từ danh sách kết quả.

    Args:
        results_list: List các dict kết quả, mỗi dict có trường "Standard" và "Element"

    Returns:
        Dict: {element_id: standard_used}
    """

    element_standards = {}

    for result in results_list:
        if "Element" in result and "Standard" in result:
            element_id = result["Element"]
            standard = result["Standard"]
            element_standards[element_id] = standard

    return element_standards


def check_conflicts(element_standards, official_standards=None):
    """
    Kiểm tra xung đột phiên bản tiêu chuẩn.

    Args:
        element_standards: Dict {element_id: standard_used}
        official_standards: Dict {code: official_version} từ STANDARDS_LOCK.md

    Returns:
        Dict báo cáo xung đột
    """

    report = {
        "Verification_Type": "Standard-Version-Conflict",
        "Timestamp": datetime.now().isoformat(),
        "Conflicts": [],
        "Warnings": [],
        "Overall_Status": "PASS"
    }

    # Nhóm các element theo base code (TCVN 5574, TCVN 5575, etc.)
    standards_by_code = {}

    for element, standard in element_standards.items():
        # Parse "TCVN 5574:2018" → code="TCVN 5574", year="2018"
        if ":" in standard:
            code, year = standard.split(":", 1)
            code = code.strip()
            year = year.strip()
        else:
            code = standard
            year = "Unknown"

        if code not in standards_by_code:
            standards_by_code[code] = {}

        if year not in standards_by_code[code]:
            standards_by_code[code][year] = []

        standards_by_code[code][year].append(element)

    # Kiểm tra từng code
    for code, years_dict in standards_by_code.items():
        if len(years_dict) > 1:
            # Conflict: Cùng 1 tiêu chuẩn nhưng nhiều phiên bản
            report["Overall_Status"] = "CRITICAL"
            report["Conflicts"].append({
                "Type": "MULTIPLE_VERSIONS_USED",
                "Severity": "CRITICAL",
                "Standard_Code": code,
                "Versions_Used": list(years_dict.keys()),
                "Elements_Per_Version": {year: elems for year, elems in years_dict.items()},
                "Description": f"Cùng tiêu chuẩn {code} nhưng sử dụng {len(years_dict)} phiên bản khác nhau",
                "Action": "BẮT BUỘC thống nhất phiên bản. Kiểm tra STANDARDS_LOCK.md để xác định phiên bản chính thức."
            })

        # Kiểm tra với official standards nếu có
        if official_standards and code in official_standards:
            official_version = official_standards[code]

            for year, elements in years_dict.items():
                used_version = f"{code}:{year}"

                if used_version != official_version:
                    report["Warnings"].append({
                        "Type": "VERSION_MISMATCH_WITH_LOCK",
                        "Severity": "WARNING",
                        "Standard_Code": code,
                        "Used_Version": used_version,
                        "Official_Version": official_version,
                        "Elements": elements,
                        "Description": f"Đang dùng {used_version} nhưng STANDARDS_LOCK.md quy định {official_version}",
                        "Action": "Cân nhắc cập nhật lên phiên bản mới hoặc cập nhật STANDARDS_LOCK.md nếu cố tình dùng phiên bản cũ"
                    })

    # Tóm tắt
    report["Summary"] = {
        "Total_Standards": len(standards_by_code),
        "Conflict_Count": len(report["Conflicts"]),
        "Warning_Count": len(report["Warnings"])
    }

    return report


def generate_report_text(report):
    """
    Tạo báo cáo văn bản.
    """

    output = f"""
╔═══════════════════════════════════════════════════════════════╗
║       STANDARD VERSION CONFLICT CHECKER REPORT                ║
╚═══════════════════════════════════════════════════════════════╝

Thời gian: {report['Timestamp']}
Trạng thái: {report['Overall_Status']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÓM TẮT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tổng số tiêu chuẩn: {report['Summary']['Total_Standards']}
🔴 Conflicts:       {report['Summary']['Conflict_Count']}
⚠️  Warnings:       {report['Summary']['Warning_Count']}

"""

    if report["Conflicts"]:
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CONFLICTS ({len(report['Conflicts'])})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for idx, conflict in enumerate(report["Conflicts"], 1):
            output += f"""
{idx}. {conflict['Standard_Code']}
   Phát hiện: {len(conflict['Versions_Used'])} phiên bản khác nhau
   Các phiên bản: {', '.join(conflict['Versions_Used'])}

   Chi tiết:
"""
            for ver, elems in conflict["Elements_Per_Version"].items():
                output += f"   - {ver}: {len(elems)} cấu kiện ({', '.join(elems[:3])}{'...' if len(elems) > 3 else ''})\n"

            output += f"   → {conflict['Action']}\n"

    if report["Warnings"]:
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WARNINGS ({len(report['Warnings'])})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for idx, warning in enumerate(report["Warnings"], 1):
            output += f"""
{idx}. {warning['Description']}
   Đang dùng:  {warning['Used_Version']}
   Chuẩn:      {warning['Official_Version']}
   Cấu kiện:   {', '.join(warning['Elements'][:5])}{'...' if len(warning['Elements']) > 5 else ''}
   → {warning['Action']}
"""

    if report["Overall_Status"] == "CRITICAL":
        output += "\n❌ KẾT LUẬN: KHÔNG xuất báo cáo cho đến khi giải quyết xung đột phiên bản.\n"
    elif report["Warnings"]:
        output += "\n⚠️  KẾT LUẬN: Có cảnh báo về phiên bản tiêu chuẩn. Xem xét cập nhật.\n"
    else:
        output += "\n✅ KẾT LUẬN: Không phát hiện xung đột phiên bản.\n"

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standard Version Conflict Checker")
    parser.add_argument("--results", required=True, help="File JSON chứa danh sách kết quả")
    parser.add_argument("--repo_root", default=".", help="Thư mục gốc repo (để tìm STANDARDS_LOCK.md)")
    parser.add_argument("--output", help="File output (optional)")
    parser.add_argument("--format", choices=["json", "text", "both"], default="text")

    args = parser.parse_args()

    # Đọc results
    with open(args.results, 'r', encoding='utf-8') as f:
        results_list = json.load(f)

    # Đọc STANDARDS_LOCK
    official_standards = load_standards_lock(args.repo_root)

    # Trích xuất standards
    element_standards = extract_standards_from_results(results_list)

    # Kiểm tra conflicts
    report = check_conflicts(element_standards, official_standards)

    # Output
    if args.format in ["json", "both"]:
        json_output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"✅ JSON saved: {args.output}")
        else:
            print(json_output)

    if args.format in ["text", "both"]:
        text_output = generate_report_text(report)
        if args.output and args.format == "both":
            text_file = args.output.replace(".json", ".txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_output)
            print(f"✅ Text saved: {text_file}")
        else:
            print(text_output)
