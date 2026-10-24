import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
from datetime import datetime

def compare_results(result1, result2, threshold=5.0):
    """
    So sánh kết quả từ 2 module tính toán.

    Args:
        result1: Dict kết quả từ module 1
        result2: Dict kết quả từ module 2
        threshold: Ngưỡng cảnh báo (%)

    Returns:
        Dict chứa báo cáo so sánh
    """

    comparison = {
        "Verification_Type": "Inter-Module",
        "Timestamp": datetime.now().isoformat(),
        "Threshold": threshold,
        "Variances": [],
        "Overall_Status": "PASS",
        "Issues": []
    }

    # Danh sách các trường số cần so sánh
    numeric_fields = [
        ("M_Rd", "kN.m", 5.0),
        ("V_Rd", "kN", 5.0),
        ("N_Rd", "kN", 5.0),
        ("eta_M", "%", 3.0),
        ("eta_V", "%", 3.0),
        ("eta_N", "%", 3.0),
        ("As_required", "mm²", 10.0),
        ("As_provided", "mm²", 10.0)
    ]

    for field, unit, field_threshold in numeric_fields:
        if field in result1 and field in result2:
            val1 = float(result1[field])
            val2 = float(result2[field])

            # Tránh chia cho 0
            if val1 == 0 and val2 == 0:
                variance = 0.0
            elif val1 == 0:
                variance = 100.0
            else:
                variance = abs(val1 - val2) / val1 * 100.0

            variance_entry = {
                "Field": field,
                "Module1_Value": val1,
                "Module2_Value": val2,
                "Variance_Percent": round(variance, 2),
                "Unit": unit,
                "Threshold": field_threshold
            }

            comparison["Variances"].append(variance_entry)

            # Phân loại severity
            if variance > field_threshold * 2:
                severity = "CRITICAL"
                comparison["Overall_Status"] = "CRITICAL"
                comparison["Issues"].append({
                    "Type": "INTER_MODULE_VARIANCE",
                    "Severity": severity,
                    "Field": field,
                    "Description": f"Sai lệch {field} = {variance:.2f}% vượt ngưỡng {field_threshold*2}%",
                    "Module1": val1,
                    "Module2": val2,
                    "Action": "BẮT BUỘC kiểm tra lại cả 2 module, xác định module nào đúng"
                })
            elif variance > field_threshold:
                severity = "WARNING"
                if comparison["Overall_Status"] == "PASS":
                    comparison["Overall_Status"] = "WARNING"
                comparison["Issues"].append({
                    "Type": "INTER_MODULE_VARIANCE",
                    "Severity": severity,
                    "Field": field,
                    "Description": f"Sai lệch {field} = {variance:.2f}% (ngưỡng: {field_threshold}%)",
                    "Module1": val1,
                    "Module2": val2,
                    "Action": "Kiểm tra giả định và làm tròn số. Chấp nhận nếu có giải thích hợp lý."
                })

    # Kiểm tra tiêu chuẩn
    if "Standard" in result1 and "Standard" in result2:
        if result1["Standard"] != result2["Standard"]:
            comparison["Overall_Status"] = "CRITICAL"
            comparison["Issues"].append({
                "Type": "STANDARD_VERSION_CONFLICT",
                "Severity": "CRITICAL",
                "Description": f"Module 1 dùng {result1['Standard']}, Module 2 dùng {result2['Standard']}",
                "Action": "BẮT BUỘC thống nhất phiên bản tiêu chuẩn theo STANDARDS_LOCK.md"
            })

    # Tóm tắt
    comparison["Summary"] = {
        "Total_Comparisons": len(comparison["Variances"]),
        "Critical_Count": len([i for i in comparison["Issues"] if i["Severity"] == "CRITICAL"]),
        "Warning_Count": len([i for i in comparison["Issues"] if i["Severity"] == "WARNING"]),
        "Pass_Count": len(comparison["Variances"]) - len(comparison["Issues"])
    }

    return comparison


def generate_report_text(comparison):
    """
    Tạo báo cáo dạng văn bản dễ đọc.
    """

    report = f"""
╔═══════════════════════════════════════════════════════════════╗
║           INTER-MODULE VERIFICATION REPORT                    ║
╚═══════════════════════════════════════════════════════════════╝

Thời gian: {comparison['Timestamp']}
Ngưỡng cảnh báo: {comparison['Threshold']}%
Trạng thái tổng thể: {comparison['Overall_Status']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SO SÁNH CÁC TRƯỜNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    for var in comparison["Variances"]:
        status_icon = "✅" if var["Variance_Percent"] <= var["Threshold"] else "⚠️" if var["Variance_Percent"] <= var["Threshold"] * 2 else "🔴"
        report += f"""
{status_icon} {var['Field']}:
   Module 1: {var['Module1_Value']:.2f} {var['Unit']}
   Module 2: {var['Module2_Value']:.2f} {var['Unit']}
   Sai lệch: {var['Variance_Percent']:.2f}% (ngưỡng: {var['Threshold']}%)
"""

    if comparison["Issues"]:
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VẤN ĐỀ PHÁT HIỆN ({len(comparison['Issues'])})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for idx, issue in enumerate(comparison["Issues"], 1):
            severity_icon = "🔴" if issue["Severity"] == "CRITICAL" else "⚠️"
            report += f"""
{idx}. {severity_icon} [{issue['Severity']}] {issue['Type']}
   {issue['Description']}
   → {issue['Action']}
"""

    report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TÓM TẮT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tổng số so sánh: {comparison['Summary']['Total_Comparisons']}
✅ Pass:          {comparison['Summary']['Pass_Count']}
⚠️  Warning:      {comparison['Summary']['Warning_Count']}
🔴 Critical:      {comparison['Summary']['Critical_Count']}

"""

    if comparison["Overall_Status"] == "CRITICAL":
        report += "❌ KẾT LUẬN: KHÔNG được phép xuất báo cáo cho đến khi xử lý các lỗi CRITICAL.\n"
    elif comparison["Overall_Status"] == "WARNING":
        report += "⚠️  KẾT LUẬN: Có cảnh báo cần xem xét. User có thể chấp nhận nếu có giải thích hợp lý.\n"
    else:
        report += "✅ KẾT LUẬN: Kết quả nhất quán giữa 2 module. An toàn để xuất báo cáo.\n"

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inter-Module Verification")
    parser.add_argument("--result1", required=True, help="File JSON kết quả module 1")
    parser.add_argument("--result2", required=True, help="File JSON kết quả module 2")
    parser.add_argument("--threshold", type=float, default=5.0, help="Ngưỡng cảnh báo (%%)")
    parser.add_argument("--output", help="File output JSON (optional)")
    parser.add_argument("--format", choices=["json", "text", "both"], default="text", help="Format output")

    args = parser.parse_args()

    # Đọc file JSON
    with open(args.result1, 'r', encoding='utf-8') as f:
        result1 = json.load(f)

    with open(args.result2, 'r', encoding='utf-8') as f:
        result2 = json.load(f)

    # So sánh
    comparison = compare_results(result1, result2, args.threshold)

    # Output
    if args.format in ["json", "both"]:
        json_output = json.dumps(comparison, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"✅ JSON output: {args.output}")
        else:
            print(json_output)

    if args.format in ["text", "both"]:
        text_output = generate_report_text(comparison)
        if args.output and args.format == "both":
            text_file = args.output.replace(".json", ".txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_output)
            print(f"✅ Text output: {text_file}")
        else:
            print(text_output)
