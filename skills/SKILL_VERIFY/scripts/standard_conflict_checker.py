import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import os
import re
from datetime import datetime

STD_CODE_YEAR_RE = re.compile(
    r"((?:TCVN|TCXDVN|QCVN|ACI|Thông\s+tư|TT)\s+[\w./\-]+?)(?:[:\-](\d{4}(?:/[A-Z\-]+)?|\d{2}))\b",
    re.IGNORECASE,
)


def load_standards_lock(repo_root):
    """
    [FIX BUG-RD-03]: Đọc STANDARDS_LOCK.md (hỗ trợ cả định dạng bảng v3.1.0:
    | Lĩnh vực | Phiên bản CHUẨN | Phiên bản CŨ | File PDF chuẩn |
    và định dạng legacy 5 cột) để lấy phiên bản tiêu chuẩn chính thức.
    Tìm ở cả repo_root/STANDARDS_LOCK.md và repo_root/skills/STANDARDS_LOCK.md.
    """
    repo_root_str = str(repo_root)
    candidates = [
        repo_root_str if os.path.isfile(repo_root_str) else "",
        os.path.join(repo_root_str, "STANDARDS_LOCK.md"),
        os.path.join(repo_root_str, "skills", "STANDARDS_LOCK.md"),
    ]
    standards_lock_path = next((p for p in candidates if os.path.exists(p)), None)
    if not standards_lock_path:
        return None

    standards = {}
    with open(standards_lock_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_section_1 = False
    for line in lines:
        if re.match(r"^##\s*1\.", line.strip()):
            in_section_1 = True
            continue
        if in_section_1 and re.match(r"^##\s*2\.", line.strip()):
            break
        if "|" not in line:
            continue
        if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        if "Lĩnh vực" in parts[0] or "Phiên bản" in parts[1]:
            continue

        # Hỗ trợ định dạng cũ (| TCVN 5574 | 2018 | Bê tông | ✅ Active |)
        if len(parts) >= 4 and ("Active" in parts[-1] or "✅" in parts[-1]):
            code = parts[0].replace("**", "").strip()
            year = parts[1].replace("**", "").strip()
            standards[code] = f"{code}:{year}"
            continue

        # Hỗ trợ định dạng chuẩn STANDARDS_LOCK.md v3.1.0: cột 2 là Phiên bản CHUẨN
        current_col = parts[1].replace("**", "").strip()
        for match in STD_CODE_YEAR_RE.finditer(current_col):
            base_code = re.sub(r"\s+", " ", match.group(1).strip())
            year_part = match.group(2).strip()
            sep = "-" if base_code.upper().startswith("ACI") else ":"
            standards[base_code] = f"{base_code}{sep}{year_part}"

    return standards


def extract_standards_from_results(results_list):
    """
    Trích xuất tất cả các tiêu chuẩn được sử dụng từ danh sách kết quả.
    """
    element_standards = {}
    for result in results_list:
        if "Element" in result and ("Standard" in result or "Standard_Method" in result):
            element_id = result["Element"]
            standard = result.get("Standard") or result.get("Standard_Method")
            element_standards[element_id] = standard
    return element_standards


def check_conflicts(element_standards, official_standards=None):
    """
    Kiểm tra xung đột phiên bản tiêu chuẩn.
    """
    report = {
        "Verification_Type": "Standard-Version-Conflict",
        "Timestamp": datetime.now().isoformat(),
        "Conflicts": [],
        "Warnings": [],
        "Overall_Status": "PASS",
        "Standard_Method": "STANDARDS_LOCK v3.1.0",
        "Calculation_Logs": []
    }

    standards_by_code = {}

    for element, standard in element_standards.items():
        if ":" in standard:
            code, year = standard.split(":", 1)
            code = code.strip()
            year = year.strip().split()[0]
        else:
            code = standard.strip()
            year = "Unknown"

        if code not in standards_by_code:
            standards_by_code[code] = {}
        if year not in standards_by_code[code]:
            standards_by_code[code][year] = []
        standards_by_code[code][year].append(element)

    for code, years_dict in standards_by_code.items():
        if len(years_dict) > 1:
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

    report["Summary"] = {
        "Total_Standards": len(standards_by_code),
        "Conflict_Count": len(report["Conflicts"]),
        "Warning_Count": len(report["Warnings"])
    }
    report["Calculation_Logs"].append({
        "Step": 1,
        "Description": "Đối chiếu phiên bản tiêu chuẩn giữa các cấu kiện và STANDARDS_LOCK.md",
        "Result": f"Total={len(standards_by_code)}, Conflicts={len(report['Conflicts'])}, Warnings={len(report['Warnings'])}"
    })

    return report


def generate_report_text(report):
    output = f"""
╔═══════════════════════════════════════════════════════════════╗
║ STANDARD VERSION CONFLICT CHECKER REPORT                      ║
╚═══════════════════════════════════════════════════════════════╝

Thời gian: {report['Timestamp']}
Trạng thái: {report['Overall_Status']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÓM TẮT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tổng số tiêu chuẩn: {report['Summary']['Total_Standards']}
🔴 Conflicts: {report['Summary']['Conflict_Count']}
⚠️ Warnings: {report['Summary']['Warning_Count']}
"""
    if report["Conflicts"]:
        output += f"\n🔴 CONFLICTS ({len(report['Conflicts'])})\n"
        for idx, conflict in enumerate(report["Conflicts"], 1):
            output += f"{idx}. {conflict['Standard_Code']}: {', '.join(conflict['Versions_Used'])} -> {conflict['Action']}\n"

    if report["Warnings"]:
        output += f"\n⚠️ WARNINGS ({len(report['Warnings'])})\n"
        for idx, warning in enumerate(report["Warnings"], 1):
            output += f"{idx}. {warning['Description']} (Đang dùng: {warning['Used_Version']} | Chuẩn: {warning['Official_Version']})\n"

    if report["Overall_Status"] == "CRITICAL":
        output += "\n❌ KẾT LUẬN: KHÔNG xuất báo cáo cho đến khi giải quyết xung đột phiên bản.\n"
    elif report["Warnings"]:
        output += "\n⚠️ KẾT LUẬN: Có cảnh báo về phiên bản tiêu chuẩn. Xem xét cập nhật.\n"
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

    with open(args.results, 'r', encoding='utf-8') as f:
        results_list = json.load(f)

    official_standards = load_standards_lock(args.repo_root)
    element_standards = extract_standards_from_results(results_list)
    report = check_conflicts(element_standards, official_standards)

    if args.format in ["json", "both"]:
        json_output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
        else:
            print(json_output)

    if args.format in ["text", "both"]:
        text_output = generate_report_text(report)
        if args.output and args.format == "both":
            text_file = args.output.replace(".json", ".txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_output)
        else:
            print(text_output)
