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
import json
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
    ("13. Sprint 5 Comprehensive Verification & Reporting (17 tests)", [sys.executable, str(TESTS_DIR / "test_suite13_verification.py")]),
    ("14. Policy Engine & Multi-Trigger Rules (55 tests)", [sys.executable, str(TESTS_DIR / "test_policy_engine.py")]),
    ("15. Sync Report System Consistency (14 tests)", [sys.executable, str(TESTS_DIR / "test_sync_report.py")]),
    ("16. Cognitive & System Control Engine (40 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_and_control_systems.py")]),
    ("17. XLSX View Sanity — Anti-[Repaired] (regression openpyxl sheetViews/MergedCell)", [sys.executable, str(TESTS_DIR / "test_suite17_xlsx_view_sanity.py")]),
    ("18. DCE CAD Compliance & Zero White Text Lock (25 tests)", [sys.executable, str(TESTS_DIR / "test_dce_cad_compliance.py")]),
    ("19. Dual-Agent Bridge & Bus IPC (7 tests)", [sys.executable, str(SKILLS_ROOT / "SKILL_DUAL_AGENT_BRIDGE" / "tests" / "test_dual_agent_bridge.py")]),
    ("20. Cognitive Brain v2.0 Benchmark (10 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_brain_20261022.py")]),
    ("21. R&D & Structural TCVN Regression Patches (20 checks)", [sys.executable, str(TESTS_DIR / "test_rd_structural_patches_20261022.py")]),
    ("22. Cognitive Architecture v2 — Dynamic DAG, Cycles, Budget & JSONL (47 tests)", [sys.executable, str(TESTS_DIR / "test_cognitive_architecture_v2.py")]),
    ("23. PDF Citation Grounding & Input Provenance Guard (62 tests)", [sys.executable, str(TESTS_DIR / "test_citation_grounding_guard.py")]),
    ("24. Nonlinear RC Fiber Section P-Mx-My 3D (23 tests)", [sys.executable, str(TESTS_DIR / "test_rc_section_pm_3d.py")]),
    ("25. Project Data Adapter & E2E Batch Pipeline (34 tests)", [sys.executable, str(TESTS_DIR / "test_project_data_pipeline.py")]),
    ("26. Durable Project Orchestration & Agent Roles (39 tests)", [sys.executable, str(TESTS_DIR / "test_project_orchestration_p1.py")]),
    ("27. CAD Edit Workbench (9 tests)", [sys.executable, str(TESTS_DIR / "test_cad_edit_workbench.py")]),
    ("28. DCE Virtual Drive Guard & MCP Preview Lifecycle (18 tests)", [sys.executable, '-B', str(TESTS_DIR / "test_dce_virtual_drive_guard.py")]),
    ("29. MCP DCE-CAD Server & Vision Tools (12 tests)", [sys.executable, str(TESTS_DIR / "test_mcp_dce_cad_server.py")]),
    ("30. CAD Scene Index & Collision Solver (Sprint 2 Anti-Collision) (35 tests)", [sys.executable, str(TESTS_DIR / "test_cad_collision_solver.py")]),
    ("31. Dynamic Sheet-Scale Governor & SSOT Layout (Directive v5.0) (11 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_sheet_scale_fitter.py")]),
    ("32. CAD Semantics v6 C1 Renderer & Tag Placement (6 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_cad_v6_c1.py")]),
    ("33. CAD Semantics v6 C2 Sheet Set & Dual Viewport (3 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_cad_v6_c2.py")]),
    ("34. Bootstrap Matrix — hook fail-closed wrapper (4 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_bootstrap_matrix.py")]),
    ("35. MCP machine-local installer (3 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_setup_dce_cad_mcp.py")]),
    ("36. Release manifest & registry tool (4 tests)", [sys.executable, "-B", str(TESTS_DIR / "test_release_manifest_tool.py")]),
]

# Smoke tier includes the real-PDF grounding guard. Slow reporting, CAD,
# control timing, nonlinear solving and durable orchestration remain in full CI.
FAST_SUITES = {1, 2, 3, 4, 5, 6, 8, 9, 14, 15, 17, 18, 19, 20, 21, 22, 23, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36}


def _auto_register_unregistered():
    """Self-heal: register any .agents/tests/test_*.py not already in SUITES.

    Prevents "dead on arrival" — a newly dropped unit-test file is picked up by
    `--full` automatically (the hardcoded SUITES list previously left 12 files
    unregistered, incl. the P4.1/P4.2/P4.3 suites). Auto-registered suites are
    full-CI only (not in FAST_SUITES) since CAD-heavy suites run slow.
    """
    already = {Path(c[-1]).name for _n, c in SUITES if c and c[-1].endswith(".py")}
    # These have dedicated runner entries (calculators / integration), not unit suites.
    skip = {"test_runner.py", "test_e2e_pipeline.py", "integration_test.py"}
    next_no = len(SUITES)
    added = []
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        if f.name in already or f.name in skip:
            continue
        next_no += 1
        SUITES.append((f"{next_no}. [auto] {f.stem} (auto-registered unit suite)", [sys.executable, str(f)]))
        added.append(f.name)
    return added

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    tier = parser.add_mutually_exclusive_group()
    tier.add_argument('--fast', action='store_true', help='Development smoke tier (target <15s); not full certification')
    tier.add_argument('--full', action='store_true', help='All registered suites for CI/CD (default)')
    parser.add_argument('--suite', type=int, action='append', help='Run only these suite numbers (repeatable)')
    parser.add_argument('--report-dir', type=Path, help='Save JSON timing report and complete per-suite logs')
    parser.add_argument('--timeout', type=float, default=300, help='Per-suite timeout in seconds (default: 300)')
    args = parser.parse_args()
    if args.timeout <= 0 or not __import__('math').isfinite(args.timeout):
        parser.error('Timeout must be positive and finite')
    if args.fast and args.suite:
        parser.error('--fast cannot be combined with --suite; use explicit selection or the smoke tier')
    _auto_added = _auto_register_unregistered()
    if _auto_added:
        print(f" [auto] Đã tự đăng ký {len(_auto_added)} suite chưa có trong SUITES: {', '.join(_auto_added)}")
    selected = SUITES
    if args.fast:
        selected = [(name, cmd) for name, cmd in SUITES if int(name.split('.', 1)[0]) in FAST_SUITES]
    if args.suite:
        available = {int(name.split('.', 1)[0]) for name, _ in SUITES}
        if set(args.suite) - available:
            parser.error('Unknown suite number')
        selected = [(name, cmd) for name, cmd in SUITES if int(name.split('.', 1)[0]) in args.suite]
    print("=" * 80)
    print(" RUN ALL TESTS — BỘ KIỂM TRA TOÀN DIỆN HỆ SINH THÁI .AGENTS")
    print("=" * 80)

    if args.report_dir:
        args.report_dir = args.report_dir.resolve()
        args.report_dir.mkdir(parents=True, exist_ok=True)
    print(f" Tier: {'fast' if args.fast else 'selected' if args.suite else 'full'} | {len(selected)}/{len(SUITES)} suites", flush=True)
    total_start = time.perf_counter()
    all_passed = True
    results = []

    for name, cmd in selected:
        print(f"\n▶ Chạy: {name}...", flush=True)
        start = time.perf_counter()
        test_env = {**os.environ, "PYTHONUTF8": "1"}
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=test_env,
                               cwd=AGENTS_ROOT.parent, timeout=args.timeout)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or ''
            p = subprocess.CompletedProcess(cmd, 124, decoded(error.stdout), decoded(error.stderr) + '\nSUITE_TIMEOUT')
        elapsed = time.perf_counter() - start
        if args.report_dir:
            number = int(name.split('.', 1)[0])
            (args.report_dir / f'suite_{number:02d}.log').write_text(
                f'command={cmd!r}\nexit_code={p.returncode}\nwall_seconds={elapsed:.6f}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}', encoding='utf-8')
        passed = (p.returncode == 0)
        results.append((name, passed, elapsed))
        if passed:
            print(f" ✅ ĐẠT ({elapsed:.2f}s)")
        else:
            print(f" ❌ THẤT BẠI ({elapsed:.2f}s)")
            print(" --- Chi tiết lỗi ---")
            print(p.stdout)
            print(p.stderr)
            all_passed = False

    print("\n" + "=" * 80)
    print(" TỔNG KẾT BỘ KIỂM TRA")
    print("=" * 80)
    for name, passed, elapsed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f" {status} | {name:<50s} ({elapsed:.2f}s)")

    total_elapsed = time.perf_counter() - total_start
    if args.report_dir:
        report = {'tier': 'fast' if args.fast else 'selected' if args.suite else 'full',
                  'registered_suites': len(SUITES), 'selected_suites': len(results),
                  'all_passed': all_passed, 'wall_seconds': total_elapsed,
                  'suites': [{'number': int(name.split('.', 1)[0]), 'name': name, 'passed': passed,
                              'wall_seconds': elapsed} for name, passed, elapsed in results]}
        (args.report_dir / 'timings.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print("-" * 80)
    if all_passed:
        print(f" 🎉 TẤT CẢ TEST SUITES ĐỀU VƯỢT QUA! (Tổng thời gian: {total_elapsed:.2f}s)")
        return 0
    else:
        print(f" ⚠️ CÓ TEST SUITE THẤT BẠI. (Tổng thời gian: {total_elapsed:.2f}s)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
