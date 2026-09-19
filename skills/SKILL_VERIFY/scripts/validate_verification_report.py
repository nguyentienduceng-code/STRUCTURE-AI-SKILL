#!/usr/bin/env python3
"""
validate_verification_report.py — Validate SKILL_VERIFY output JSON against schema

Usage:
    python validate_verification_report.py --input verification_report.json
    python validate_verification_report.py --input verification_report.json --strict
"""

import argparse
import json
import sys
from pathlib import Path

# ─── Schema definition ────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "Verification_ID",
    "Timestamp",
    "Project",
    "Scope",
    "Verification_Types",
    "Results",
    "Overall_Status",
]

RESULTS_REQUIRED = ["Total_Checks", "Passed", "Warnings", "Critical"]
OVERALL_STATUSES = {"PASSED", "FAILED", "PARTIAL", "ERROR"}
VERIFICATION_TYPES = {
    "Inter-Module",
    "Standard-Version",
    "Calculation-Logs",
    "External-Software",
    "Report-Consistency",
}


# ─── Validation functions ─────────────────────────────────────────────────────

def validate_report(data: dict, strict: bool = False) -> list:
    issues = []

    # 1. Required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            issues.append(f"REQUIRED field missing: '{field}'")

    # 2. Results structure
    if "Results" in data:
        res = data["Results"]
        for field in RESULTS_REQUIRED:
            if field not in res:
                issues.append(f"Results missing field: '{field}'")
        # Types and ranges
        for field in ["Total_Checks", "Passed", "Warnings", "Critical"]:
            if field in res:
                v = res[field]
                if not isinstance(v, (int, float)):
                    issues.append(f"Results.{field} must be numeric, got {type(v).__name__}: {v}")
                if v < 0:
                    issues.append(f"Results.{field} must be >= 0, got {v}")

        # Sum check
        total = res.get("Total_Checks", 0)
        passed = res.get("Passed", 0)
        warnings = res.get("Warnings", 0)
        critical = res.get("Critical", 0)
        if isinstance(total, (int, float)) and isinstance(passed, (int, float)):
            if total < passed + warnings + critical:
                issues.append(
                    f"Results.Total_Checks ({total}) < Passed({passed}) + "
                    f"Warnings({warnings}) + Critical({critical}) — không nhất quán"
                )

    # 3. Overall status
    status = data.get("Overall_Status", "")
    if status not in OVERALL_STATUSES:
        issues.append(
            f"Overall_Status='{status}' không hợp lệ. "
            f"Chọn: {sorted(OVERALL_STATUSES)}"
        )

    # 4. Verification types
    vtypes = data.get("Verification_Types", [])
    for vt in vtypes:
        if vt not in VERIFICATION_TYPES:
            issues.append(
                f"Verification_Types contains invalid type: '{vt}'. "
                f"Valid: {sorted(VERIFICATION_TYPES)}"
            )

    # 5. Timestamp format
    ts = data.get("Timestamp", "")
    if ts:
        try:
            from datetime import datetime
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            issues.append(f"Timestamp format invalid: '{ts}'. Use ISO 8601 format.")

    # 6. Verification_ID format
    vid = data.get("Verification_ID", "")
    if vid and not vid.startswith("VRF-"):
        issues.append(f"Verification_ID should start with 'VRF-', got: '{vid}'")

    # 7. Issues array structure
    for i, issue in enumerate(data.get("Issues", [])):
        if not isinstance(issue, dict):
            issues.append(f"Issues[{i}] must be an object, got {type(issue).__name__}")
            continue
        for req in ["Type", "Severity"]:
            if req not in issue:
                issues.append(f"Issues[{i}] missing required field: '{req}'")
        sev = issue.get("Severity", "")
        if sev not in {"WARNING", "CRITICAL", "INFO"}:
            issues.append(
                f"Issues[{i}].Severity='{sev}' không hợp lệ. "
                f"Chọn: WARNING, CRITICAL, INFO"
            )

    # 8. Strict mode: check all numeric fields non-negative
    if strict:
        numeric_fields = [
            ("Results.Passed", data.get("Results", {}).get("Passed")),
            ("Results.Warnings", data.get("Results", {}).get("Warnings")),
            ("Results.Critical", data.get("Results", {}).get("Critical", 0)),
        ]
        for path, val in numeric_fields:
            if val is not None and val < 0:
                issues.append(f"[STRICT] Negative value not allowed: {path} = {val}")

    return issues


def format_report(issues: list, data: dict) -> str:
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("  SKILL_VERIFY — Schema Validation Report")
    lines.append("=" * 60)

    vid = data.get("Verification_ID", "N/A")
    status = data.get("Overall_Status", "N/A")
    lines.append(f"  ID:         {vid}")
    lines.append(f"  Status:     {status}")
    lines.append(f"  Validation: {'✅ PASS' if not issues else f'❌ FAIL ({len(issues)} issues)'}")

    if issues:
        lines.append("\n  Issues:")
        for issue in issues:
            lines.append(f"    • {issue}")
    else:
        lines.append("\n  ✅ Schema is valid — all checks passed.")

    lines.append("=" * 60 + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Validate SKILL_VERIFY output JSON")
    parser.add_argument("--input", type=str, required=True, help="JSON file to validate")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation")
    parser.add_argument("--output", type=str, help="Save validation result to JSON")
    args = parser.parse_args()

    # Load file
    path = Path(args.input)
    if not path.exists():
        print(f"[E001] File not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[E002] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    # Validate
    issues = validate_report(data, strict=args.strict)
    report = format_report(issues, data)
    print(report)

    # Save result
    result = {
        "Verification_ID": data.get("Verification_ID", ""),
        "Valid": len(issues) == 0,
        "Issue_Count": len(issues),
        "Issues": issues,
        "Strict_Mode": args.strict,
        "File_Validated": str(path.resolve()),
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[I001] Validation result saved: {args.output}", file=sys.stderr)

    sys.exit(0 if not issues else 1)


if __name__ == "__main__":
    main()
