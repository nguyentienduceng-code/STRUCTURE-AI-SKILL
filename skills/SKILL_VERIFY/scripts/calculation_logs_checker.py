import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
from datetime import datetime

def validate_calculation_logs(calc_logs):
    """
    Kiểm tra tính nhất quán của Calculation_Logs.

    Args:
        calc_logs: List các bước tính toán, mỗi bước là dict với:
            - Step_Number
            - Description
            - Formula
            - Substitution
            - Result
            - Citation (optional)

    Returns:
        Dict báo cáo validation
    """

    report = {
        "Verification_Type": "Calculation-Logs-Consistency",
        "Timestamp": datetime.now().isoformat(),
        "Total_Steps": len(calc_logs),
        "Issues": [],
        "Overall_Status": "PASS"
    }

    previous_results = {}  # Dict để track kết quả các bước trước

    for idx, step in enumerate(calc_logs):
        step_num = step.get("Step_Number", idx + 1)

        # Kiểm tra 1: Các trường bắt buộc
        required_fields = ["Description", "Formula", "Substitution", "Result"]
        missing_fields = [field for field in required_fields if field not in step or not step[field]]

        if missing_fields:
            report["Overall_Status"] = "WARNING"
            report["Issues"].append({
                "Type": "MISSING_REQUIRED_FIELD",
                "Severity": "WARNING",
                "Step": step_num,
                "Missing_Fields": missing_fields,
                "Description": f"Bước {step_num} thiếu trường: {', '.join(missing_fields)}",
                "Action": "Bổ sung đầy đủ Formula, Substitution, Result cho mọi bước"
            })
            continue

        # Kiểm tra 2: Citation structure (nếu có)
        if "Citation" in step and step["Citation"]:
            citation = step["Citation"]
            required_citation_fields = ["Standard", "Year", "Clause", "Table", "Page", "Description"]
            missing_citation = [f for f in required_citation_fields if f not in citation]

            if missing_citation:
                report["Overall_Status"] = "WARNING"
                report["Issues"].append({
                    "Type": "INCOMPLETE_CITATION",
                    "Severity": "WARNING",
                    "Step": step_num,
                    "Missing_Fields": missing_citation,
                    "Description": f"Citation ở bước {step_num} thiếu: {', '.join(missing_citation)}",
                    "Action": "Bổ sung đầy đủ 6 trường cho Citation"
                })

        # Kiểm tra 3: Result consistency với bước tiếp theo
        result_text = step["Result"]
        substitution_text = step["Substitution"]

        # Parse các giá trị số từ Result
        # Ví dụ: "M_Rd = 310.5 kN.m" → {"M_Rd": 310.5}
        import re
        result_values = {}
        matches = re.findall(r'(\w+)\s*=\s*([\d.]+)', result_text)
        for var_name, value in matches:
            result_values[var_name] = float(value)

        previous_results[step_num] = result_values

        # Kiểm tra xem Substitution có sử dụng giá trị từ bước trước không
        # Và giá trị đó có khớp với Result của bước trước không
        sub_values = {}
        sub_matches = re.findall(r'(\w+)\s*=\s*([\d.]+)', substitution_text)
        for var_name, value in sub_matches:
            sub_values[var_name] = float(value)

        # So sánh với previous_results
        for var, val in sub_values.items():
            # Tìm xem var này có xuất hiện trong Result của bước nào trước đó không
            for prev_step, prev_vals in previous_results.items():
                if prev_step >= step_num:
                    break

                if var in prev_vals:
                    expected_val = prev_vals[var]
                    # Cho phép sai lệch 0.1% do làm tròn
                    if abs(val - expected_val) / max(expected_val, 0.001) > 0.001:
                        report["Overall_Status"] = "WARNING"
                        report["Issues"].append({
                            "Type": "CALCULATION_INCONSISTENCY",
                            "Severity": "MEDIUM",
                            "Step": step_num,
                            "Variable": var,
                            "Expected_Value": expected_val,
                            "Used_Value": val,
                            "Description": f"Bước {step_num} sử dụng {var} = {val}, nhưng bước {prev_step} cho {var} = {expected_val}",
                            "Action": "Kiểm tra lại script tính toán hoặc làm tròn số"
                        })

    # Tóm tắt
    report["Summary"] = {
        "Total_Steps": len(calc_logs),
        "Issues_Count": len(report["Issues"]),
        "Missing_Field_Count": len([i for i in report["Issues"] if i["Type"] == "MISSING_REQUIRED_FIELD"]),
        "Inconsistency_Count": len([i for i in report["Issues"] if i["Type"] == "CALCULATION_INCONSISTENCY"]),
        "Citation_Issue_Count": len([i for i in report["Issues"] if i["Type"] == "INCOMPLETE_CITATION"])
    }

    return report


def generate_report_text(report):
    """
    Tạo báo cáo văn bản.
    """

    output = f"""
╔═══════════════════════════════════════════════════════════════╗
║       CALCULATION LOGS CONSISTENCY CHECKER REPORT             ║
╚═══════════════════════════════════════════════════════════════╝

Thời gian: {report['Timestamp']}
Trạng thái: {report['Overall_Status']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÓM TẮT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tổng số bước tính:           {report['Summary']['Total_Steps']}
Vấn đề phát hiện:            {report['Summary']['Issues_Count']}
  - Thiếu trường bắt buộc:   {report['Summary']['Missing_Field_Count']}
  - Không nhất quán:         {report['Summary']['Inconsistency_Count']}
  - Citation không đầy đủ:   {report['Summary']['Citation_Issue_Count']}

"""

    if report["Issues"]:
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VẤN ĐỀ PHÁT HIỆN ({len(report['Issues'])})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for idx, issue in enumerate(report["Issues"], 1):
            severity_icon = "🔴" if issue["Severity"] == "CRITICAL" else "⚠️" if issue["Severity"] == "MEDIUM" else "ℹ️"
            output += f"\n{idx}. {severity_icon} [{issue['Severity']}] {issue['Type']} - Bước {issue['Step']}\n"
            output += f"   {issue['Description']}\n"
            output += f"   → {issue['Action']}\n"

    if report["Overall_Status"] == "PASS":
        output += "\n✅ KẾT LUẬN: Calculation_Logs nhất quán, đầy đủ thông tin.\n"
    else:
        output += "\n⚠️  KẾT LUẬN: Phát hiện vấn đề. Cần kiểm tra và sửa Calculation_Logs.\n"

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculation Logs Consistency Checker")
    parser.add_argument("--logs", required=True, help="File JSON chứa Calculation_Logs")
    parser.add_argument("--output", help="File output (optional)")
    parser.add_argument("--format", choices=["json", "text", "both"], default="text")

    args = parser.parse_args()

    # Đọc calc logs
    with open(args.logs, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Nếu file chứa wrapper object, extract Calculation_Logs
    if isinstance(data, dict) and "Calculation_Logs" in data:
        calc_logs = data["Calculation_Logs"]
    elif isinstance(data, list):
        calc_logs = data
    else:
        print("❌ ERROR: File phải chứa array Calculation_Logs hoặc object có trường Calculation_Logs")
        sys.exit(1)

    # Validate
    report = validate_calculation_logs(calc_logs)

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
