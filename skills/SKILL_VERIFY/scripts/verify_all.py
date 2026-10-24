#!/usr/bin/env python3
"""
verify_all.py — Unified CLI: chạy tất cả 5 loại kiểm chứng cùng lúc

Usage:
    python verify_all.py --handoff skillkc_output.json --sde sde_output.json [options]

Exit codes:
    0  = PASS (all checks passed or warnings only)
    1  = FAIL (CRITICAL issue found)
    2  = ERROR (script error / missing inputs)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import sys
import os
from pathlib import Path

# ─── Inline verification logic (không phụ thuộc module import) ─────────────

def check_inter_module(result1: dict, result2: dict, threshold: float) -> dict:
    """So sánh 2 kết quả cùng cấu kiện."""
    checks = []
    warnings = []
    for key in ["M_Rd", "V_Rd", "N_Rd"]:
        if key not in result1 or key not in result2:
            continue
        v1 = float(result1[key])
        v2 = float(result2[key])
        var = abs(v1 - v2) / v1 * 100
        status = "PASS" if var < threshold else "FAIL"
        checks.append({
            "Type": "INTER_MODULE_VARIANCE",
            "Field": key,
            "Value1": round(v1, 3),
            "Value2": round(v2, 3),
            "Variance_pct": round(var, 2),
            "Threshold_pct": threshold,
            "Status": status
        })
        if status == "FAIL":
            warnings.append(f"Sai lệch {key}: {var:.2f}% > {threshold}%")
    return {"InterModule": checks, "Warnings": warnings}


def check_standard_conflict(result1: dict, result2: dict) -> dict:
    """Phát hiện xung đột phiên bản tiêu chuẩn."""
    s1 = result1.get("Standard_Method", "")
    s2 = result2.get("Standard_Method", "")
    if s1 and s2 and s1 != s2:
        return {
            "Conflict": True,
            "Standard1": s1,
            "Standard2": s2,
            "Severity": "CRITICAL",
            "Message": f"Xung đột tiêu chuẩn: '{s1}' vs '{s2}'. Thống nhất theo STANDARDS_LOCK.md."
        }
    return {"Conflict": False, "Standard": s1 or s2}


def check_calculation_logs(logs: list) -> dict:
    """Kiểm tra nhất quán Calculation_Logs."""
    issues = []
    for i, step in enumerate(logs):
        for field in ["Formula", "Substitution", "Result"]:
            if field not in step:
                issues.append(f"Bước {i+1}: thiếu '{field}'")
        if i > 0 and "Result" in logs[i-1] and "Substitution" in step:
            prev = logs[i-1]["Result"]
            if prev and prev not in step["Substitution"]:
                issues.append(f"Bước {i+1}: Result bước {i} không xuất hiện trong Substitution bước {i+1}")
    return {"Issues": issues, "Status": "FAIL" if issues else "PASS"}


def summarize(results: dict) -> str:
    """In bảng tóm tắt kết quả kiểm chứng."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("  SKILL_VERIFY — Báo cáo Kiểm chứng Tổng hợp")
    lines.append("=" * 60)

    # Inter-module
    im = results.get("InterModule", {})
    im_checks = im.get("InterModule", []) if isinstance(im, dict) else im
    if im_checks:
        lines.append(f"\n1. Inter-Module Variance ({len(im_checks)} checks):")
        for c in im_checks:
            icon = "✅" if c["Status"] == "PASS" else "❌"
            lines.append(f"   {icon} {c['Field']}: {c['Value1']} vs {c['Value2']} → {c['Variance_pct']}%")

    # Standard conflict
    sc = results.get("StandardConflict", {})
    conflict = sc.get("Conflict", False)
    lines.append(f"\n2. Standard Version Conflict: {'❌ XUNG ĐỘT' if conflict else '✅ OK'}")
    if conflict:
        lines.append(f"   → {sc.get('Message', '')}")

    # Calculation logs
    cl = results.get("CalculationLogs", {})
    lines.append(f"\n3. Calculation Logs Consistency: {cl.get('Status', 'N/A')}")
    for issue in cl.get("Issues", []):
        lines.append(f"   ⚠️  {issue}")

    # External software
    ext = results.get("ExternalSoftware", [])
    lines.append(f"\n4. External Software Comparison: {len(ext)} checks")
    for e in ext:
        icon = "✅" if e.get("Variance_pct", 999) < 5 else "⚠️"
        lines.append(f"   {icon} {e.get('Element', '?')}: {e.get('AI_Value')} vs {e.get('Reference_Value')} → {e.get('Variance_pct', 0):.2f}%")

    # Report consistency
    rc = results.get("ReportConsistency", {})
    lines.append(f"\n5. Report Data Consistency: {rc.get('Status', 'N/A')}")
    for issue in rc.get("Mismatches", []):
        lines.append(f"   ❌ {issue}")

    # 6. Cross-Document Conflict Control (CDC-01 to CDC-08)
    cdc = results.get("CrossDocConflict", {})
    if cdc:
        issues = cdc.get("Issues", [])
        summary = cdc.get("Summary", {})
        status = cdc.get("Overall_Status", "PASS")
        icon = "✅ OK" if status == "PASS" else ("❌ CRITICAL" if status == "CRITICAL" else "⚠️ " + status)
        lines.append(f"\n6. Cross-Document Conflict Control (CDC): {icon}")
        lines.append(f"   Tổng: {summary.get('Total_Issues', 0)} (Critical: {summary.get('Critical_Count', 0)}, Major: {summary.get('Major_Count', 0)}, Warning: {summary.get('Warning_Count', 0)})")
        for iss in issues:
            sev_mark = "❌" if iss.get("Severity") == "CRITICAL" else "⚠️"
            lines.append(f"   {sev_mark} [{iss.get('Rule_ID')}] ({iss.get('Disciplines')}): {iss.get('Title')}")

    # Overall
    has_critical = (
        conflict or
        any(c.get("Status") == "FAIL" for c in im_checks) or
        (cdc and cdc.get("Overall_Status") == "CRITICAL")
    )
    lines.append(f"\n{'='*60}")
    if has_critical:
        lines.append("  ❌ OVERALL: FAILED — Có lỗi CRITICAL. Không xuất báo cáo.")
    else:
        lines.append("  ✅ OVERALL: PASSED — Có thể xuất báo cáo sau khi duyệt.")
    lines.append("=" * 60 + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="SKILL_VERIFY: Unified verification CLI")
    parser.add_argument("--handoff", type=str, help="SKILLKC JSON output file")
    parser.add_argument("--sde", type=str, help="Structural_Design_Engineer JSON output file")
    parser.add_argument("--logs", type=str, help="Calculation logs JSON file")
    parser.add_argument("--etabs", type=str, help="ETABS export JSON file")
    parser.add_argument("--report", type=str, help="Generated report JSON for consistency check")
    parser.add_argument("--graph", type=str, help="Project Truth Graph JSON file for cross-doc conflict check")
    parser.add_argument("--threshold", type=float, default=5.0, help="Variance threshold %% (default: 5.0)")
    parser.add_argument("--output", type=str, help="Save result to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    args = parser.parse_args()

    results = {}

    # 1. Inter-module
    if args.handoff and args.sde:
        try:
            with open(args.handoff, encoding="utf-8") as f:
                r1 = json.load(f)
            with open(args.sde, encoding="utf-8") as f:
                r2 = json.load(f)
            results["InterModule"] = check_inter_module(r1, r2, args.threshold)
            results["StandardConflict"] = check_standard_conflict(r1, r2)
        except FileNotFoundError as e:
            results["_error"] = f"File not found: {e}"
        except json.JSONDecodeError as e:
            results["_error"] = f"Invalid JSON: {e}"

    # 2. Calculation logs
    if args.logs:
        try:
            with open(args.logs, encoding="utf-8") as f:
                logs_data = json.load(f)
            logs_list = logs_data.get("Calculation_Logs", logs_data) if isinstance(logs_data, dict) else logs_data
            results["CalculationLogs"] = check_calculation_logs(logs_list)
        except FileNotFoundError:
            results["CalculationLogs"] = {"Issues": ["File not found"], "Status": "ERROR"}
        except json.JSONDecodeError:
            results["CalculationLogs"] = {"Issues": ["Invalid JSON"], "Status": "ERROR"}

    # 3 & 4. External software comparison
    if args.etabs:
        results["ExternalSoftware"] = []
        try:
            with open(args.etabs, encoding="utf-8") as f:
                etabs_data = json.load(f)
            for row in etabs_data.get("Comparison", []):
                ai_v = float(row.get("AI_Value", 0))
                ref_v = float(row.get("Reference_Value", 0))
                var = abs(ai_v - ref_v) / ref_v * 100 if ref_v else 0
                row["Variance_pct"] = round(var, 2)
                results["ExternalSoftware"].append(row)
        except Exception as e:
            results["ExternalSoftware"] = [{"Error": str(e)}]

    # 5. Report consistency
    if args.report:
        results["ReportConsistency"] = {"Status": "N/A", "Mismatches": []}
        # Placeholder — requires docx parsing, handled by report_consistency_check.py

    # 6. Cross-Document Conflict Control (CDC-01 to CDC-08)
    if args.graph:
        try:
            from cross_doc_conflict_checker import run_conflict_checks
        except ImportError:
            sys.path.insert(0, str(Path(__file__).parent))
            from cross_doc_conflict_checker import run_conflict_checks

        try:
            with open(args.graph, encoding="utf-8") as f:
                graph_data = json.load(f)
            results["CrossDocConflict"] = run_conflict_checks(graph_data)
        except FileNotFoundError:
            results["CrossDocConflict"] = {"Overall_Status": "ERROR", "Issues": [{"Title": "File not found", "Severity": "CRITICAL"}]}
        except json.JSONDecodeError:
            results["CrossDocConflict"] = {"Overall_Status": "ERROR", "Issues": [{"Title": "Invalid JSON", "Severity": "CRITICAL"}]}

    # Output
    if not args.quiet:
        print(summarize(results))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # Exit code
    im_checks = results.get("InterModule", {}).get("InterModule", [])
    has_critical = (
        results.get("StandardConflict", {}).get("Conflict") or
        any(c.get("Status") == "FAIL" for c in im_checks) or
        (results.get("CrossDocConflict", {}).get("Overall_Status") == "CRITICAL")
    )
    if results.get("_error"):
        print("ERROR:", results["_error"], file=sys.stderr)
        sys.exit(2)
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
