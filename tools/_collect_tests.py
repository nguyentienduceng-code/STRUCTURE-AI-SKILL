# tools/_collect_tests.py
# Bộ thu thập: Chạy 6 test suites từ run_all_tests.py, parse stdout, trả về TestRunResult.
# Import SUITES thay vì redefine; nếu test_runner.py thay đổi, sync_report tự pick up.

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SuiteResult:
    """Kết quả chạy 1 test suite."""

    name: str
    cmd: list[str]
    passed: bool
    elapsed_sec: float
    passed_count: Optional[int] = None
    failed_count: Optional[int] = None
    total_count: Optional[int] = None
    raw_stdout_tail: str = ""
    returncode: int = -1
    timed_out: bool = False
    error: str = ""


@dataclass
class TestRunResult:
    """Kết quả tổng hợp tất cả suites."""

    suites: list[SuiteResult] = field(default_factory=list)
    all_passed: bool = True
    total_elapsed_sec: float = 0.0
    grand_total_passed: int = 0
    grand_total_failed: int = 0
    unparsed_suites: list[str] = field(default_factory=list)


# ----- Per-suite parsers -----
# Mỗi parser: nhận stdout (str), trả về tuple (passed_count, failed_count, total_count) hoặc None nếu không parse được.

def _parse_integration(stdout: str) -> Optional[tuple[int, int, int]]:
    # Body in: "  ✅ PASSED:  67\n  ⚠️ WARNINGS: ...\n  ❌ FAILED:  0\n  TOTAL:     ..."
    m_pass = re.search(r"PASSED:\s+(\d+)", stdout)
    m_fail = re.search(r"FAILED:\s+(\d+)", stdout)
    m_total = re.search(r"TOTAL:\s+(\d+)", stdout)
    if not (m_pass and m_fail and m_total):
        return None
    return int(m_pass.group(1)), int(m_fail.group(1)), int(m_total.group(1))


def _parse_regression(stdout: str) -> Optional[tuple[int, int, int]]:
    # "  SUMMARY: 16/16 PASSED | 0 FAILED | 0 ERRORS"
    m = re.search(
        r"SUMMARY:\s+(\d+)/(\d+)\s+PASSED\s+\|\s+(\d+)\s+FAILED(?:\s+\|\s+(\d+)\s+ERRORS)?",
        stdout,
    )
    if not m:
        return None
    passed = int(m.group(1))
    total = int(m.group(2))
    failed = int(m.group(3))
    return passed, failed, total


def _parse_approval_gate(stdout: str) -> Optional[tuple[int, int, int]]:
    # unittest: "Tests run: 32" / "Failures: 0" / "Errors: 0"
    m_run = re.search(r"Tests run:\s+(\d+)", stdout)
    m_fail = re.search(r"Failures:\s+(\d+)", stdout)
    m_err = re.search(r"Errors:\s+(\d+)", stdout)
    if not m_run:
        return None
    total = int(m_run.group(1))
    failed = int((m_fail.group(1) if m_fail else "0"))
    passed = total - failed - int((m_err.group(1) if m_err else "0"))
    return passed, failed, total


def _parse_intent(stdout: str) -> Optional[tuple[int, int, int]]:
    # Output: "  RESULT: 15/17 passed (88.2%%)" — chú ý 2 dấu % do f-string escape
    m = re.search(r"RESULT:\s+(\d+)/(\d+)\s+passed", stdout)
    if not m:
        return None
    passed = int(m.group(1))
    total = int(m.group(2))
    return passed, total - passed, total


def _parse_e2e(stdout: str) -> Optional[tuple[int, int, int]]:
    # Format: 4 stages, mỗi stage in "  <NAME>: ...: ✅ PASS/❌ FAIL"
    # Đếm trong "Stage Results:" block. Nếu không có, tìm "Overall: ✅ PASS" + 1 stage
    matches = re.findall(r":\s*✅\s*PASS\b", stdout)
    if matches:
        # Số PASS = số ✅ PASS trong output
        return len(matches), 0, len(matches)
    # Fallback: tìm "Overall: ✅ PASS" → 1 stage
    if "Overall: ✅ PASS" in stdout:
        return 1, 0, 1
    return None


def _parse_de_calc(stdout: str) -> Optional[tuple[int, int, int]]:
    # Format: "  SUMMARY: 10 passed, 0 failed"
    m = re.search(r"SUMMARY:\s+(\d+)\s+passed,\s+(\d+)\s+failed", stdout)
    if not m:
        return None
    passed = int(m.group(1))
    failed = int(m.group(2))
    return passed, failed, passed + failed


def _parse_unittest(stdout: str) -> Optional[tuple[int, int, int]]:
    """Parser cho unittest chuẩn (Ran X tests in ... OK / FAILED)."""
    m_ran = re.search(r"Ran\s+(\d+)\s+tests?", stdout)
    if not m_ran:
        return None
    total = int(m_ran.group(1))
    if re.search(r"\bOK\b", stdout):
        return total, 0, total
    m_fail = re.search(r"failures=(\d+)", stdout)
    m_err = re.search(r"errors=(\d+)", stdout)
    failed = (int(m_fail.group(1)) if m_fail else 0) + (int(m_err.group(1)) if m_err else 0)
    passed = max(0, total - failed)
    return passed, failed, total


def _parse_phase2(stdout: str) -> Optional[tuple[int, int, int]]:
    """Parser cho test_phase2_tools.py (Passed : X, Failed : Y, Total : Z)."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", stdout)
    m_pass = re.search(r"Passed\s*:\s*(\d+)", clean)
    m_fail = re.search(r"Failed\s*:\s*(\d+)", clean)
    m_total = re.search(r"Total\s*:\s*(\d+)", clean)
    if not (m_pass and m_fail and m_total):
        return None
    return int(m_pass.group(1)), int(m_fail.group(1)), int(m_total.group(1))


# Map suite name (substring) → parser
PARSER_BY_HINT = [
    ("Sprint 5", _parse_unittest),
    ("Sprint 4", _parse_unittest),
    ("Sprint 3.4", _parse_unittest),
    ("Sprint 3 Phase 3", _parse_unittest),
    ("Sprint 3 Phase 2", _parse_phase2),
    ("Sprint 2", _parse_unittest),
    ("Sprint 1", _parse_unittest),
    ("Policy Engine", _parse_unittest),
    ("Sync Report", _parse_unittest),
    ("1. Integration Test", _parse_integration),
    ("Integration Test", _parse_integration),
    ("Regression Calculator", _parse_regression),
    ("Approval Gate", _parse_approval_gate),
    ("Intent Classifier", _parse_intent),
    ("E2E Pipeline", _parse_e2e),
    ("DE Calculators", _parse_de_calc),
]


def _select_parser(suite_name: str):
    """Trả về parser function dựa trên tên suite (substring match)."""
    for hint, parser in PARSER_BY_HINT:
        if hint in suite_name:
            return parser
    return None


# ----- Import SUITES từ run_all_tests.py -----

def _load_suites_from(tests_dir: Path) -> list[tuple[str, list[str]]]:
    """Import SUITES list từ tests/run_all_tests.py. Trả về [(name, cmd)]."""
    target = tests_dir / "run_all_tests.py"
    if not target.exists():
        return []
    spec = importlib.util.spec_from_file_location("run_all_tests", target)
    if not spec or not spec.loader:
        return []
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return []
    suites = getattr(mod, "SUITES", [])
    return [(name, cmd) for name, cmd in suites]


def _run_one_suite(name: str, cmd: list[str], timeout: int = 300) -> SuiteResult:
    """Chạy 1 suite, parse output, trả về SuiteResult."""
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = time.time() - start
        stdout = (proc.stdout or "") + "\n" + (proc.stderr or "")
        returncode = proc.returncode
        passed_bool = returncode == 0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return SuiteResult(
            name=name,
            cmd=cmd,
            passed=False,
            elapsed_sec=elapsed,
            timed_out=True,
            returncode=-1,
            error=f"timeout after {timeout}s",
            raw_stdout_tail="",
        )
    except Exception as e:
        elapsed = time.time() - start
        return SuiteResult(
            name=name,
            cmd=cmd,
            passed=False,
            elapsed_sec=elapsed,
            returncode=-1,
            error=str(e),
            raw_stdout_tail="",
        )
    parser = _select_parser(name)
    passed_count = failed_count = total_count = None
    if parser:
        parsed = parser(stdout)
        if parsed:
            passed_count, failed_count, total_count = parsed
    return SuiteResult(
        name=name,
        cmd=cmd,
        passed=passed_bool,
        elapsed_sec=elapsed,
        passed_count=passed_count,
        failed_count=failed_count,
        total_count=total_count,
        raw_stdout_tail=stdout[-2048:],
        returncode=returncode,
    )


def run_all_test_suites(
    tests_dir: Path,
    suite_timeout_sec: int = 300,
    cache_path: Optional[Path] = None,
) -> TestRunResult:
    """Chạy toàn bộ SUITES, trả về TestRunResult. Nếu cache_path tồn tại → đọc cache, không chạy lại.

    Sau khi chạy thật, ghi kết quả vào cache_path (JSON) để dùng sau.
    """
    suites_def = _load_suites_from(tests_dir)
    if not suites_def:
        return TestRunResult(
            suites=[],
            all_passed=False,
            unparsed_suites=["run_all_tests.py not loadable"],
        )
    result = TestRunResult()
    total_start = time.time()
    for name, cmd in suites_def:
        sr = _run_one_suite(name, cmd, timeout=suite_timeout_sec)
        result.suites.append(sr)
        if not sr.passed:
            result.all_passed = False
        if sr.passed_count is not None:
            result.grand_total_passed += sr.passed_count
        if sr.failed_count is not None:
            result.grand_total_failed += sr.failed_count
        if sr.passed_count is None and not sr.timed_out and not sr.error:
            result.unparsed_suites.append(sr.name)
    result.total_elapsed_sec = time.time() - total_start
    if cache_path:
        _write_cache(cache_path, result)
    return result


def _write_cache(cache_path: Path, result: TestRunResult) -> None:
    """Ghi kết quả ra JSON cache."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "all_passed": result.all_passed,
        "total_elapsed_sec": result.total_elapsed_sec,
        "grand_total_passed": result.grand_total_passed,
        "grand_total_failed": result.grand_total_failed,
        "unparsed_suites": result.unparsed_suites,
        "suites": [
            {
                "name": s.name,
                "passed": s.passed,
                "elapsed_sec": s.elapsed_sec,
                "passed_count": s.passed_count,
                "failed_count": s.failed_count,
                "total_count": s.total_count,
                "timed_out": s.timed_out,
                "error": s.error,
            }
            for s in result.suites
        ],
    }
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_test_cache(cache_path: Path) -> TestRunResult:
    """Đọc cache JSON, trả về TestRunResult. Nếu cache không tồn tại → trả về rỗng."""
    if not cache_path.exists():
        return TestRunResult(suites=[], all_passed=False, unparsed_suites=["cache not found"])
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return TestRunResult(suites=[], all_passed=False, unparsed_suites=["cache parse error"])
    suites = [
        SuiteResult(
            name=s["name"],
            cmd=[],
            passed=s["passed"],
            elapsed_sec=s["elapsed_sec"],
            passed_count=s.get("passed_count"),
            failed_count=s.get("failed_count"),
            total_count=s.get("total_count"),
            timed_out=s.get("timed_out", False),
            error=s.get("error", ""),
        )
        for s in payload.get("suites", [])
    ]
    return TestRunResult(
        suites=suites,
        all_passed=payload.get("all_passed", False),
        total_elapsed_sec=payload.get("total_elapsed_sec", 0.0),
        grand_total_passed=payload.get("grand_total_passed", 0),
        grand_total_failed=payload.get("grand_total_failed", 0),
        unparsed_suites=payload.get("unparsed_suites", []),
    )
