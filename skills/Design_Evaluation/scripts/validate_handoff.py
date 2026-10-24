"""
validate_handoff.py — Kiểm tra tính hợp lệ của JSON handoff từ SKILLKC sang SKILL_REPORT
Chạy: python validate_handoff.py <json_file.json>

Exit codes:
    0 = Validation passed
    1 = Validation failed
    2 = Cannot read file or invalid JSON
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

# Màu terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'
CYAN = '\033[96m'

# JSON Schema cho handoff JSON
HANDOFF_SCHEMA = {
    "required": [
        "Ten_Du_An",
        "Giai_Doan_TK",
        "Ngay"
    ],
    "properties": {
        "Ten_Du_An": {
            "type": "string",
            "min_length": 1,
            "description": "Tên dự án"
        },
        "Hang_Muc": {
            "type": "string",
            "description": "Hạng mục cụ thể"
        },
        "Giai_Doan_TK": {
            "type": "string",
            "enum": ["TKCS", "TKKT", "BVTC", "Hoàn công"],
            "description": "Giai đoạn thiết kế"
        },
        "Ngay": {
            "type": "string",
            "pattern": r"^\d{1,2}/\d{1,2}/\d{4}$",
            "description": "Ngày lập (DD/MM/YYYY)"
        },
        "Calculation_Logs": {
            "type": "array",
            "item_schema": {
                "required": ["Step", "Formula", "Result"],
                "optional": ["Values", "Citation", "Unit"]
            }
        },
        "Citations": {
            "type": "array",
            "item_schema": {
                "required": ["Ma_Tieu_Chuan", "Nam_Ban_Hanh", "Dieu_Bang_Muc", "Trich_Yeu"],
                "optional": ["Trang_So", "Ten_Bang_Hinh", "Nguon_File", "Citation_Status"]
            }
        },
        "Constructability_Risk": {
            "type": "string",
            "pattern": r"^(MINOR|MAJOR|CRITICAL)\s*—\s*.+",
            "description": "Format: SEVERITY — description"
        },
        "Kien_Nghi": {
            "type": "string",
            "min_length": 1
        }
    }
}

def load_json(filepath: str) -> Optional[Dict]:
    """Load JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{RED}ERROR: File not found: {filepath}{RESET}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"{RED}ERROR: Invalid JSON: {e}{RESET}")
        sys.exit(2)

def validate_field(data: Dict, field: str, schema: Dict, path: str = "") -> List[Dict]:
    """Validate a single field"""
    issues = []
    value = data.get(field)

    # Check required
    if 'required' in schema and field in schema['required']:
        if value is None or (schema['type'] == 'string' and str(value).strip() == ''):
            issues.append({
                'type': 'MISSING_REQUIRED',
                'field': f"{path}.{field}" if path else field,
                'message': f"Required field missing or empty: {field}"
            })
            return issues

    # Skip validation if field not present
    if value is None:
        return issues

    # Type validation
    expected_type = schema.get('type')
    if expected_type:
        if expected_type == 'string' and not isinstance(value, str):
            issues.append({
                'type': 'WRONG_TYPE',
                'field': f"{path}.{field}" if path else field,
                'message': f"Expected string, got {type(value).__name__}"
            })
        elif expected_type == 'array' and not isinstance(value, list):
            issues.append({
                'type': 'WRONG_TYPE',
                'field': f"{path}.{field}" if path else field,
                'message': f"Expected array, got {type(value).__name__}"
            })
        elif expected_type == 'object' and not isinstance(value, dict):
            issues.append({
                'type': 'WRONG_TYPE',
                'field': f"{path}.{field}" if path else field,
                'message': f"Expected object, got {type(value).__name__}"
            })

    # Enum validation
    if 'enum' in schema and value not in schema['enum']:
        issues.append({
            'type': 'INVALID_ENUM',
            'field': f"{path}.{field}" if path else field,
            'message': f"Invalid value '{value}'. Must be one of: {schema['enum']}"
        })

    # Pattern validation (regex)
    if 'pattern' in schema and isinstance(value, str):
        if not re.match(schema['pattern'], value):
            issues.append({
                'type': 'INVALID_FORMAT',
                'field': f"{path}.{field}" if path else field,
                'message': f"Value '{value}' does not match pattern: {schema['pattern']}"
            })

    # Min length
    if 'min_length' in schema and isinstance(value, str) and len(value) < schema['min_length']:
        issues.append({
            'type': 'TOO_SHORT',
            'field': f"{path}.{field}" if path else field,
            'message': f"String too short (min {schema['min_length']}): {value}"
        })

    return issues

def validate_calculation_logs(data: Dict) -> List[Dict]:
    """Validate Calculation_Logs array"""
    issues = []
    logs = data.get('Calculation_Logs', [])

    if not isinstance(logs, list):
        return [{
            'type': 'WRONG_TYPE',
            'field': 'Calculation_Logs',
            'message': f"Expected array, got {type(logs).__name__}"
        }]

    required_fields = ['Step', 'Formula', 'Result']

    for i, log_entry in enumerate(logs):
        if not isinstance(log_entry, dict):
            issues.append({
                'type': 'INVALID_ARRAY_ITEM',
                'field': f'Calculation_Logs[{i}]',
                'message': f"Expected object, got {type(log_entry).__name__}"
            })
            continue

        for field in required_fields:
            if field not in log_entry:
                issues.append({
                    'type': 'MISSING_CALC_FIELD',
                    'field': f'Calculation_Logs[{i}].{field}',
                    'message': f"Missing required field in Calculation_Log entry {i}: {field}"
                })

    return issues

def validate_citations(data: Dict) -> List[Dict]:
    """Validate Citations array"""
    issues = []
    citations = data.get('Citations', [])

    if not isinstance(citations, list):
        return [{
            'type': 'WRONG_TYPE',
            'field': 'Citations',
            'message': f"Expected array, got {type(citations).__name__}"
        }]

    required_fields = ['Ma_Tieu_Chuan', 'Nam_Ban_Hanh', 'Dieu_Bang_Muc', 'Trich_Yeu']

    for i, citation in enumerate(citations):
        if not isinstance(citation, dict):
            issues.append({
                'type': 'INVALID_ARRAY_ITEM',
                'field': f'Citations[{i}]',
                'message': f"Expected object, got {type(citation).__name__}"
            })
            continue

        for field in required_fields:
            if field not in citation:
                issues.append({
                    'type': 'MISSING_CITATION_FIELD',
                    'field': f'Citations[{i}].{field}',
                    'message': f"Missing required field in Citation {i}: {field}"
                })

        # Validate Citation_Status if present
        if 'Citation_Status' in citation:
            valid_statuses = ['VERIFIED', 'UNVERIFIED', 'PENDING']
            if citation['Citation_Status'] not in valid_statuses:
                issues.append({
                    'type': 'INVALID_CITATION_STATUS',
                    'field': f'Citations[{i}].Citation_Status',
                    'message': f"Invalid status '{citation['Citation_Status']}'. Must be one of: {valid_statuses}"
                })

    return issues

def validate_constructability_risk(data: Dict) -> List[Dict]:
    """Validate Constructability_Risk format"""
    issues = []
    risk = data.get('Constructability_Risk')

    if risk and isinstance(risk, str):
        if not re.match(r'^(MINOR|MAJOR|CRITICAL)\s*—\s*.+', risk):
            issues.append({
                'type': 'INVALID_RISK_FORMAT',
                'field': 'Constructability_Risk',
                'message': f"Invalid format: '{risk}'. Expected: 'SEVERITY — description'"
            })

    return issues

def validate_handoff(data: Dict) -> Dict:
    """Main validation function"""
    all_issues = []
    warnings = []

    # Validate top-level required fields
    for field in HANDOFF_SCHEMA.get('required', []):
        issues = validate_field(data, field, HANDOFF_SCHEMA['properties'].get(field, {}))
        all_issues.extend(issues)

    # Validate optional fields if present
    for field, schema in HANDOFF_SCHEMA.get('properties', {}).items():
        if field not in HANDOFF_SCHEMA.get('required', []):
            issues = validate_field(data, field, schema)
            all_issues.extend(issues)

    # Validate Calculation_Logs
    if 'Calculation_Logs' in data:
        all_issues.extend(validate_calculation_logs(data))

    # Validate Citations
    if 'Citations' in data:
        all_issues.extend(validate_citations(data))

    # Validate Constructability_Risk
    if 'Constructability_Risk' in data:
        all_issues.extend(validate_constructability_risk(data))

    # Check for unverified items without warnings
    unverified_citations = [
        c for c in data.get('Citations', [])
        if c.get('Citation_Status') == 'UNVERIFIED'
    ]
    if unverified_citations:
        warnings.append({
            'type': 'UNVERIFIED_CITATIONS',
            'count': len(unverified_citations),
            'message': f"Found {len(unverified_citations)} unverified citations — must display warning in report"
        })

    # Check for missing Calculation_Logs when doing quantitative analysis
    if data.get('Giai_Doan_TK') in ['TKKT', 'BVTC']:
        if 'Calculation_Logs' not in data:
            warnings.append({
                'type': 'MISSING_CALC_LOGS',
                'message': "Giai đoạn TKKT/BVTC should have Calculation_Logs"
            })

    return {
        'issues': all_issues,
        'warnings': warnings,
        'valid': len(all_issues) == 0
    }

def print_report(result: Dict, filepath: str):
    """Print validation report"""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}HANDOFF VALIDATION REPORT{RESET}")
    print(f"File: {filepath}")
    print(f"{'='*60}\n")

    if result['valid'] and not result['warnings']:
        print(f"{GREEN}{BOLD}✅ VALIDATION PASSED{RESET}")
        print("   JSON handoff is properly formatted.")
    else:
        if result['issues']:
            print(f"{RED}{BOLD}❌ VALIDATION FAILED ({len(result['issues'])} issues){RESET}")
            print()
            for issue in result['issues']:
                print(f"  [{CYAN}{issue['type']}{RESET}] {issue['message']}")
                if 'field' in issue:
                    print(f"    {YELLOW}Field: {issue['field']}{RESET}")

        if result['warnings']:
            print(f"\n{YELLOW}{BOLD}⚠️  WARNINGS ({len(result['warnings'])}){RESET}")
            for warning in result['warnings']:
                print(f"  [{warning['type']}] {warning['message']}")

    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Issues: {len(result['issues'])}")
    print(f"  Warnings: {len(result['warnings'])}")

def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage: python validate_handoff.py <json_file.json>{RESET}")
        print(f"\nExample: python validate_handoff.py DUAN_A_handoff.json")
        sys.exit(2)

    filepath = sys.argv[1]

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}SKILLKC HANDOFF VALIDATION TOOL{RESET}")
    print(f"{'='*60}{RESET}")

    data = load_json(filepath)
    print(f"{GREEN}✓{RESET} Loaded: {filepath}")

    result = validate_handoff(data)
    print_report(result, filepath)

    # Save report
    report_path = Path(filepath).parent / f"validation_report_{Path(filepath).stem}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {report_path}")

    sys.exit(0 if result['valid'] else 1)

if __name__ == '__main__':
    main()
