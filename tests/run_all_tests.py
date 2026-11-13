#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all_tests.py — Bộ điều khiển chạy toàn bộ test suites của hệ sinh thái .agents
"""

import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import subprocess
import time
from pathlib import Path

TESTS_DIR = Path(__file__).parent
AGENTS_ROOT = TESTS_DIR.parent
SKILLS_ROOT = AGENTS_ROOT / "skills"

SUITES = [
    ("1. Integration Test (64 checks)", [sys.executable, str(TESTS_DIR / "integration_test.py")]),
    ("2. Regression Calculator Test (13 calculators)", [sys.executable, str(TESTS_DIR / "test_runner.py")]),
    ("3. Pre-Execution Approval Gate (32 tests)", [sys.executable, str(SKILLS_ROOT / "Global_Dispatcher" / "scripts" / "test_approval_gate.py")]),
    ("4. Intent Classifier Benchmark (17 tests)", [sys.executable, str(SKILLS_ROOT / "Global_Dispatcher" / "scripts" / "intent_classifier.py"), "--test"]),
    ("5. E2E Pipeline Workflow", [sys.executable, str(AGENTS_ROOT / "_SHARED" / "tests" / "test_e2e_pipeline.py")]),
    ("6. DE Calculators Unit Tests (10 tests)", [sys.executable, str(SKILLS_ROOT / "Design_Evaluation" / "calculators" / "tests" / "run_tests.py")]),
    ("7. Sprint 1 Reporting & TCVN Tests (4 tests)", [sys.executable, str(TESTS_DIR / "test_sprint1_reporting.py")]),
    ("8. Sprint 2 Cross-Doc Conflict Control Tests (3 tests)", [sys.executable, str(TESTS_DIR / "test_sprint2_conflict_control.py")]),
    ("9. Sprint 3 Phase 2 CAD/BIM/ETABS Tools (61 tests)", [sys.executable, str(TESTS_DIR / "test_phase2_tools.py")]),
    ("10. Sprint 3 Phase 3 DCE Pro Integration Tests (19 tests)", [sys.executable, str(TESTS_DIR / "test_dce_integration.py")]),
    ("11. Sprint 3.4 DCE Deep Integration Tests (16 tests)", [sys.executable, str(TESTS_DIR / "test_dce_deep_integration.py")]),
    ("12. Sprint 4 Document Intelligence & Conflict Detection (70 tests)", [sys.executable, str(TESTS_DIR / "test_suite12_doc_intelligence.py")]),
    ("13. Sprint 5 Comprehensive Verification & Reporting (16 tests)", [sys.executable, str(TESTS_DIR / "test_suite13_verification.py")]),
    ("14. Policy Engine & Multi-Trigger Rules (55 tests)", [sys.executable, str(TESTS_DIR / "test_policy_engine.py")]),
    ("15. Sync Report System Consistency (14 tests)", [sys.executable, str(TESTS_DIR / "test_sync_report.py")]),
    ("16. Cognitive & System Control Engine (40 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_and_control_systems.py")]),
    ("17. XLSX View Sanity — Anti-[Repaired] (regression openpyxl sheetViews/MergedCell)", [sys.executable, str(TESTS_DIR / "test_suite17_xlsx_view_sanity.py")]),
    ("18. DCE CAD Compliance & Zero White Text Lock (9 tests)", [sys.executable, str(TESTS_DIR / "test_dce_cad_compliance.py")]),
    ("19. Dual-Agent Bridge & Bus IPC (3 tests)", [sys.executable, str(SKILLS_ROOT / "SKILL_DUAL_AGENT_BRIDGE" / "tests" / "test_dual_agent_bridge.py")]),
    ("20. Cognitive Brain v2.0 Benchmark (10 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_brain_20261022.py")]),
    ("21. R&D & Structural TCVN Regression Patches (20 checks)", [sys.executable, str(TESTS_DIR / "test_rd_structural_patches_20261022.py")]),
    ("22. Cognitive Architecture v2 — Dynamic DAG, Cycles, Budget & JSONL (47 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_architecture_v2.py")]),
    ("23. PDF Citation Grounding & Input Provenance Guard (60 tests)", [sys.executable, str(TESTS_DIR / "test_citation_grounding_guard.py")]),
    ("24. Nonlinear RC Fiber Section P-Mx-My 3D (23 tests)", [sys.executable, str(TESTS_DIR / "test_rc_section_pm_3d.py")]),
    ("25. Project Data Adapter & E2E Batch Pipeline (34 tests)", [sys.executable, str(TESTS_DIR / "test_project_data_pipeline.py")]),
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=int, action='append', help='Run only these suite numbers (repeatable)')
    args = parser.parse_args()
    selected = SUITES
    if args.suite:
        available = {int(name.split('.', 1)[0]) for name, _ in SUITES}
        if set(args.suite) - available:
            parser.error('Unknown suite number')
        selected = [(name, cmd) for name, cmd in SUITES if int(name.split('.', 1)[0]) in args.suite]
    print("=" * 80)
    print(" RUN ALL TESTS — BỘ KIỂM TRA TOÀN DIỆN HỆ SINH THÁI .AGENTS")
    print("=" * 80)

    total_start = time.time()
    all_passed = True
    results = []

    for name, cmd in selected:
        print(f"\n▶ Chạy: {name}...")
        start = time.time()
        test_env = {**os.environ, "PYTHONUTF8": "1"}
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=test_env)
        elapsed = time.time() - start
        passed = (p.returncode == 0)
        results.append((name, passed, elapsed))
        if passed:
            print(f" ✅ ĐẠT ({elapsed:.2f}s)")
        else:
            print(f" ❌ THẤT BẠI ({elapsed:.2f}s)")
            print(" --- Chi tiết lỗi ---")
            print(p.stderr or p.stdout)
            all_passed = False

    print("\n" + "=" * 80)
    print(" TỔNG KẾT BỘ KIỂM TRA")
    print("=" * 80)
    for name, passed, elapsed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f" {status} | {name:<50s} ({elapsed:.2f}s)")

    total_elapsed = time.time() - total_start
    print("-" * 80)
    if all_passed:
        print(f" 🎉 TẤT CẢ TEST SUITES ĐỀU VƯỢT QUA! (Tổng thời gian: {total_elapsed:.2f}s)")
        return 0
    else:
        print(f" ⚠️ CÓ TEST SUITE THẤT BẠI. (Tổng thời gian: {total_elapsed:.2f}s)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
