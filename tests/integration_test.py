#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRATION_TEST.py — Baseline Integration Test cho Bo Skills

Chay: python INTEGRATION_TEST.py

Kiem tra:
1. Tat ca SKILL.md co version dong bo
2. Deprecated scripts da di chuyen
3. SKILL_INDEX.md ton tai
4. STANDARDS_LOCK.md co action items
5. Registry.json syntax hop le
"""

import os
import json
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
SKILLS_ROOT = (Path(__file__).parent / "skills") if (Path(__file__).parent / "skills").exists() else (Path(__file__).parent.parent / "skills")
TESTS_PASSED = 0
TESTS_FAILED = 0
TESTS_WARNINGS = 0

def log_test(name, passed, warning=False, message=""):
    global TESTS_PASSED, TESTS_FAILED, TESTS_WARNINGS
    status = "[PASS]" if passed else ("[WARN]" if warning else "[FAIL]")
    if passed:
        TESTS_PASSED += 1
    elif warning:
        TESTS_WARNINGS += 1
    else:
        TESTS_FAILED += 1

    print(f"  {status}: {name}")
    if message:
        print(f"         {message}")

def test_version_sync():
    """Test 1: Kiểm tra version đồng bộ giữa các SKILL.md"""
    print("\n[TEST 1] Version Synchronization")

    skill_files = {
        "Global_Dispatcher": SKILLS_ROOT / "Global_Dispatcher" / "SKILL.md",
        "Design_Evaluation": SKILLS_ROOT / "Design_Evaluation" / "SKILL.md",
        "Structural_Design_Engineer": SKILLS_ROOT / "Structural_Design_Engineer" / "SKILL.md",
        "Technical_Illustrator": SKILLS_ROOT / "Technical_Illustrator" / "SKILL.md",
        "Cost_Estimator": SKILLS_ROOT / "Cost_Estimator" / "SKILL.md",
        "SKILL_FORENSIC": SKILLS_ROOT / "SKILL_FORENSIC" / "SKILL.md",
        "SKILL_VERIFY": SKILLS_ROOT / "SKILL_VERIFY" / "SKILL.md",
        "SKILL_GEOTECH": SKILLS_ROOT / "SKILL_GEOTECH" / "SKILL.md",
        "SKILL_PHULUC": SKILLS_ROOT / "SKILL_PHULUC" / "SKILL.md",
        "SKILL_RFI": SKILLS_ROOT / "SKILL_RFI" / "SKILL.md",
        "Project_Manager": SKILLS_ROOT / "Project_Manager" / "SKILL.md",
        "SKILL_TEMPWORKS": SKILLS_ROOT / "SKILL_TEMPWORKS" / "SKILL.md",
        "SKILL_BIM_COORDINATION": SKILLS_ROOT / "SKILL_BIM_COORDINATION" / "SKILL.md",
    }

    versions = {}
    for skill, path in skill_files.items():
        if path.exists():
            content = path.read_text(encoding='utf-8')
            match = re.search(r'version:\s*([\d.]+)', content)
            if match:
                versions[skill] = match.group(1)
                log_test(f"{skill} version", True, message=f"v{versions[skill]}")
            else:
                log_test(f"{skill} version", False, message="No version found in frontmatter")
        else:
            log_test(f"{skill} exists", False, message=f"File not found: {path}")

    # Check for major version consistency
    if len(versions) >= 2:
        major_versions = set(v.split('.')[0] for v in versions.values())
        if len(major_versions) > 2:
            log_test("Major version consistency", True, warning=True,
                    message=f"Multiple major versions found: {major_versions}")
        else:
            log_test("Major version consistency", True)

def test_deprecated_scripts():
    """Test 2: Kiểm tra deprecated scripts đã di chuyển"""
    print("\n[TEST 2] Deprecated Scripts Migration")

    deprecated_files = [
        "draw_ap_luc_dat_bo_ke.py",
        "draw_ke_buy_dung.py",
        "draw_ke_pi_gieng.py",
        "draw_pi_gieng_composite.py",
        "draw_tham_da.py"
    ]

    deprecated_folder = Path(__file__).parent.parent / "_deprecated"
    if deprecated_folder.exists():
        log_test("_deprecated folder exists", True)
    else:
        deprecated_folder = SKILLS_ROOT / "Technical_Illustrator" / "scripts" / "_deprecated"
        log_test("_deprecated folder exists", deprecated_folder.exists())

    # Check scripts are NOT in main folder
    scripts_folder = SKILLS_ROOT / "Technical_Illustrator" / "scripts"
    for f in deprecated_files:
        path = scripts_folder / f
        if path.exists():
            log_test(f"  {f} removed from main", False, message="Still exists in scripts/")
        else:
            log_test(f"  {f} removed from main", True)

def test_skill_index():
    """Test 3: Kiểm tra SKILL_INDEX.md tồn tại"""
    print("\n[TEST 3] SKILL_INDEX.md Existence")

    index_path = SKILLS_ROOT / "SKILL_INDEX.md"
    if index_path.exists():
        log_test("SKILL_INDEX.md exists", True)

        content = index_path.read_text(encoding='utf-8')

        # Check for key sections (case-insensitive)
        sections = [
            ("kiến trúc", "Architecture section"),
            ("phân xử", "Dispatcher table"),
            ("Design_Evaluation", "Design_Evaluation section"),
            ("Technical_Illustrator", "Technical_Illustrator section"),
            ("Cost_Estimator", "Cost_Estimator section"),
            ("SKILL_FORENSIC", "SKILL_FORENSIC section"),
            ("SKILL_VERIFY", "SKILL_VERIFY section"),
            ("dependency graph", "Dependency graph"),
            ("error codes", "Error codes section"),
        ]

        content_lower = content.lower()
        for keyword, desc in sections:
            if keyword.lower() in content_lower:
                log_test(f"  {desc}", True)
            else:
                log_test(f"  {desc}", False, message=f"Missing: {keyword}")
    else:
        log_test("SKILL_INDEX.md exists", False, message="File not found")

def test_standards_lock():
    """Test 4: Kiểm tra STANDARDS_LOCK.md"""
    print("\n[TEST 4] STANDARDS_LOCK.md Health")

    lock_path = SKILLS_ROOT / "STANDARDS_LOCK.md"
    if lock_path.exists():
        log_test("STANDARDS_LOCK.md exists", True)

        content = lock_path.read_text(encoding='utf-8')

        # Check for key sections
        if "TCVN 2737:2023" in content:
            log_test("  TCVN 2737:2023 referenced", True)
        else:
            log_test("  TCVN 2737:2023 referenced", False)

        if "TCVN 5575:2024" in content:
            log_test("  TCVN 5575:2024 referenced", True)
        else:
            log_test("  TCVN 5575:2024 referenced", False)

        if "Known Gap" in content or "Action items" in content.lower():
            log_test("  Action items section", True)
        else:
            log_test("  Action items section", True, warning=True,
                    message="No action items - consider adding audit checklist")
    else:
        log_test("STANDARDS_LOCK.md exists", False)

def test_registry_json():
    """Test 5: Kiểm tra registry.json syntax"""
    print("\n[TEST 5] registry.json Syntax")

    registry_path = SKILLS_ROOT / "Technical_Illustrator" / "scripts" / "registry.json"
    if registry_path.exists():
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            log_test("registry.json valid JSON", True, message=f"{len(data)} entries")
        except json.JSONDecodeError as e:
            log_test("registry.json valid JSON", False, message=str(e))
    else:
        log_test("registry.json exists", False)

def test_calculator_scripts():
    """Test 6: Kiểm tra calculator scripts"""
    print("\n[TEST 6] Calculator Scripts")

    agents_root = Path(__file__).parent.parent
    calc_folders = [
        SKILLS_ROOT / "Global_Dispatcher" / "scripts",
        SKILLS_ROOT / "Design_Evaluation" / "calculators",
        SKILLS_ROOT / "Structural_Design_Engineer" / "scripts",
        SKILLS_ROOT / "SKILL_GEOTECH" / "calculators",
        SKILLS_ROOT / "SKILL_GEOTECH" / "scripts",
        SKILLS_ROOT / "Cost_Estimator" / "scripts",
        SKILLS_ROOT / "SKILL_FORENSIC" / "scripts",
        SKILLS_ROOT / "SKILL_RFI" / "scripts",
        SKILLS_ROOT / "SKILL_TEMPWORKS" / "calculators",
        SKILLS_ROOT / "SKILL_TEMPWORKS" / "scripts",
        agents_root / "_SHARED" / "SHARED_CONTEXT",
        SKILLS_ROOT / "_SHARED" / "SHARED_CONTEXT",
    ]

    expected_scripts = {
        "intent_classifier.py": "Global_Dispatcher",
        "pipeline_builder.py": "Global_Dispatcher",
        "approval_gate.py": "Global_Dispatcher",
        "rc_flexure_design.py": "Design_Evaluation",
        "deflection_check.py": "Design_Evaluation",
        "steel_member_check_v2024.py": "Design_Evaluation",
        "foundation_bearing.py": "Design_Evaluation",
        "wind_load_calc.py": "Design_Evaluation",
        "earthquake_load_calc.py": "Design_Evaluation",
        "calc_rc_section.py": "Structural_Design_Engineer",
        "calc_steel_beam_tcvn.py": "Structural_Design_Engineer",
        "calc_steel_connection_tcvn.py": "Structural_Design_Engineer",
        "calc_slab.py": "Structural_Design_Engineer",
        "calc_spt_correlations.py": "SKILL_GEOTECH",
        "calc_base_heave.py": "SKILL_GEOTECH",
        "boq_cost_analysis.py": "Cost_Estimator",
        "back_calculation.py": "SKILL_FORENSIC",
        "document_tracker.py": "SKILL_RFI",
        "calc_formwork_slab.py": "SKILL_TEMPWORKS",
        "confidence_score.py": "_SHARED",
        "validate_handoff_schema.py": "_SHARED",
    }

    for script, expected_folder in expected_scripts.items():
        found = False
        for folder in calc_folders:
            if (folder / script).exists():
                found = True
                log_test(f"  {script}", True)
                break
        if not found:
            log_test(f"  {script}", False, message=f"Not found in expected locations")

def test_dependencies():
    """Test 7: Kiểm tra dependency files tồn tại"""
    print("\n[TEST 7] Dependency Files")

    dependencies = {
        "AGENTS.md": SKILLS_ROOT / "AGENTS.md",
        "CHANGELOG.md": SKILLS_ROOT / "CHANGELOG.md",
        "SKILL_INDEX.md": SKILLS_ROOT / "SKILL_INDEX.md",
        "STANDARDS_LOCK.md": SKILLS_ROOT / "STANDARDS_LOCK.md",
        "SKILL_BRIDGE.md": SKILLS_ROOT / "SKILL_BRIDGE.md",
        "INTER_SKILL_TRIGGERS.md": SKILLS_ROOT / "INTER_SKILL_TRIGGERS.md",
    }

    for name, path in dependencies.items():
        if path.exists():
            log_test(f"  {name}", True)
        else:
            log_test(f"  {name}", False)

def main():
    global TESTS_PASSED, TESTS_FAILED, TESTS_WARNINGS

    print("=" * 70)
    print("INTEGRATION TEST — Bộ Skills Kết Cấu AI")
    print("=" * 70)
    print(f"Skills root: {SKILLS_ROOT}")

    test_version_sync()
    test_deprecated_scripts()
    test_skill_index()
    test_standards_lock()
    test_registry_json()
    test_calculator_scripts()
    test_dependencies()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  ✅ PASSED:  {TESTS_PASSED}")
    print(f"  ⚠️ WARNINGS: {TESTS_WARNINGS}")
    print(f"  ❌ FAILED:  {TESTS_FAILED}")
    print(f"  TOTAL:     {TESTS_PASSED + TESTS_WARNINGS + TESTS_FAILED}")

    if TESTS_FAILED == 0:
        print("\n[OK] All critical tests passed!")
        return 0
    else:
        print("\n[!!] Some tests failed. Please review.")
        return 1

if __name__ == "__main__":
    exit(main())
