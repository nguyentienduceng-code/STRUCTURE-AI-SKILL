"""
validate_registry.py — Kiểm tra tính nhất quán giữa registry.json và thực tế files
Chạy: python validate_registry.py

Exit codes:
    0 = All OK
    1 = Validation failed (issues found)
    2 = Cannot read registry.json

Updated v2.0.0 (2026-08-30):
  - Fix path discovery cho cấu trúc _CORE_SKILLS mới
  - Tương thích với registry.json dùng field 'name' (không phải 'file_path')
  - Thêm UTF-8 output cho Windows console
"""

import json
import os
import sys
from pathlib import Path

# Force UTF-8 output for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Màu terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def get_script_dir():
    """Tìm Technical_Illustrator/scripts từ vị trí bất kỳ."""
    # Thử các path có thể
    candidates = [
        Path(__file__).parent.parent.parent / 'Technical_Illustrator' / 'scripts',
        Path(__file__).parent.parent / 'Technical_Illustrator' / 'scripts',
    ]
    for path in candidates:
        if path.exists():
            return path
    # Fallback
    return candidates[0]


def load_registry():
    registry_path = get_script_dir() / 'registry.json'
    if not registry_path.exists():
        print(f"{RED}ERROR: registry.json not found at {registry_path}{RESET}")
        sys.exit(2)

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_scripts(registry):
    """Kiểm tra scripts trong registry có file thực tế không."""
    issues = []
    warnings = []
    scripts_dir = get_script_dir()

    print(f"\n{BOLD}=== Validating Scripts ==={RESET}")

    # Check scripts in registry
    for script in registry.get('scripts', []):
        script_name = script.get('name', '')
        if not script_name:
            continue

        # Skip if marked as internal
        if script.get('internal', False):
            continue

        # DEPRECATED scripts được phép nằm trong _deprecated/
        script_status = script.get('status', '')
        if script_status == 'DEPRECATED':
            # Check nếu file thực sự ở _deprecated/
            dep_path = scripts_dir / '_deprecated' / script_name
            if dep_path.exists():
                # OK - deprecated script đã được archive đúng chỗ
                continue
            # Nếu không tìm thấy → MISSING
            issues.append({
                'type': 'MISSING_DEPRECATED_FILE',
                'file': script_name,
                'message': f"DEPRECATED script listed but file not in _deprecated/: {script_name}"
            })
            continue

        script_path = scripts_dir / script_name

        if not script_path.exists():
            issues.append({
                'type': 'MISSING_FILE',
                'file': script_name,
                'message': f"Script listed in registry but file not found: {script_name}"
            })

    # Check for scripts NOT in registry (orphan files)
    actual_scripts = []
    scripts_folder = scripts_dir
    if scripts_folder.exists():
        for f in scripts_folder.rglob('*.py'):
            rel_path = f.relative_to(scripts_dir).as_posix()
            # Skip __pycache__
            if '__pycache__' not in rel_path and '_deprecated' not in rel_path:
                actual_scripts.append(rel_path)

    registered_names = [s.get('name', '') for s in registry.get('scripts', [])]
    for script_path in actual_scripts:
        if script_path not in registered_names:
            warnings.append({
                'type': 'ORPHAN_SCRIPT',
                'file': script_path,
                'message': f"Script file exists but NOT in registry: {script_path}"
            })

    return issues, warnings


def validate_structure(registry):
    """Validate registry structure."""
    issues = []

    print(f"\n{BOLD}=== Validating Registry Structure ==={RESET}")

    # Required top-level fields
    required_fields = ['registry_version', 'scripts']
    for field in required_fields:
        if field not in registry:
            issues.append({
                'type': 'MISSING_FIELD',
                'field': field,
                'message': f"Missing required field in registry: {field}"
            })

    # Validate each script has required fields
    for script in registry.get('scripts', []):
        required_script_fields = ['name', 'description']
        for field in required_script_fields:
            if field not in script:
                issues.append({
                    'type': 'MISSING_SCRIPT_FIELD',
                    'file': script.get('name', 'UNKNOWN'),
                    'field': field,
                    'message': f"Script missing required field '{field}': {script.get('name', 'UNKNOWN')}"
                })

    return issues


def validate_cad_integration(registry):
    """Check CAD integration scripts"""
    issues = []
    cad_dir = get_script_dir() / 'cad_integration'

    print(f"\n{BOLD}=== Validating CAD Integration ==={RESET}")

    if cad_dir.exists():
        cad_scripts = list(cad_dir.glob('*.py'))
        if cad_scripts:
            cad_in_registry = any('cad_integration' in s.get('name', '')
                                  for s in registry.get('scripts', []))
            if not cad_in_registry:
                warnings_count = 1
                issues.append({
                    'type': 'MISSING_CAD_IN_REGISTRY',
                    'message': "CAD integration folder exists but scripts not in registry"
                })

    return issues


def print_report(issues, warnings):
    has_issues = len(issues) > 0
    has_warnings = len(warnings) > 0

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}VALIDATION REPORT{RESET}")
    print(f"{'='*60}{RESET}")

    if issues:
        print(f"\n{RED}{BOLD}❌ ISSUES ({len(issues)}){RESET}")
        for issue in issues:
            print(f"  [{issue['type']}] {issue['message']}")

    if warnings:
        print(f"\n{YELLOW}{BOLD}⚠️  WARNINGS ({len(warnings)}){RESET}")
        for warning in warnings:
            print(f"  [{warning['type']}] {warning['message']}")

    if not issues and not warnings:
        print(f"{GREEN}{BOLD}✅ ALL CHECKS PASSED{RESET}")
        print(f"   Registry is consistent with actual files.")

    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Issues: {len(issues)}")
    print(f"  Warnings: {len(warnings)}")

    return len(issues) == 0


def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}SKILL VALIDATION TOOL — Technical Illustrator{RESET}")
    print(f"{'='*60}{RESET}")

    try:
        registry = load_registry()
        print(f"\n{GREEN}✓{RESET} Loaded registry.json (version: {registry.get('registry_version', 'N/A')})")

        # Run validations
        script_issues, script_warnings = validate_scripts(registry)
        structure_issues = validate_structure(registry)
        cad_issues = validate_cad_integration(registry)

        all_issues = script_issues + structure_issues + cad_issues
        all_warnings = script_warnings

        success = print_report(all_issues, all_warnings)

        # Save report
        report_path = get_script_dir() / 'validation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': str(Path(__file__).stat().st_mtime),
                'registry_version': registry.get('registry_version', 'N/A'),
                'issues': all_issues,
                'warnings': all_warnings,
                'success': success
            }, f, indent=2, ensure_ascii=False)

        print(f"\nReport saved to: {report_path}")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"{RED}ERROR: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
