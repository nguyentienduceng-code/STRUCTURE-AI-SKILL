# tools/sync_report.py
# CLI entry point: thu thập dữ liệu từ code/docs, verify stale-claims, render Markdown,
# ghi đè file docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md.

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    # Trên Windows console mặc định dùng cp1252, gây lỗi khi in tiếng Việt.
    # Dùng reconfigure() (Python 3.7+) thay vì TextIOWrapper để tránh lỗi
    # "I/O operation on closed file" khi subprocess con đóng stream.
    for _name in ("stdout", "stderr"):
        _stream = getattr(sys, _name)
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

# Cho phép `python tools/sync_report.py` chạy được khi cwd là .agents/
_THIS_DIR = Path(__file__).resolve().parent
_AGENTS_ROOT = _THIS_DIR.parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from _collect_calculators import collect_calculators  # noqa: E402
from _collect_changelog import collect_latest_changelog  # noqa: E402
from _collect_keyword_db import collect_keyword_db_stats  # noqa: E402
from _collect_skills import collect_skills, collect_skills_summary, SkillFrontmatterError  # noqa: E402
from _collect_standards import collect_standards  # noqa: E402
from _collect_tests import run_all_test_suites, load_test_cache  # noqa: E402
from _render_markdown import ReportData, render_report  # noqa: E402
from _verify_claims import diff_against_existing_report  # noqa: E402

SKILLS_ROOT = _AGENTS_ROOT / "skills"
TESTS_DIR = _AGENTS_ROOT / "tests"
DOCS_DIR = _AGENTS_ROOT / "docs"
KWDB_PATH = SKILLS_ROOT / "Global_Dispatcher" / "scripts" / "keyword_database.json"
STANDARDS_PATH = SKILLS_ROOT / "STANDARDS_LOCK.md"
CHANGELOG_PATH = SKILLS_ROOT / "CHANGELOG.md"
DEFAULT_OUTPUT = DOCS_DIR / "BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md"
DEFAULT_CACHE = _AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT" / "_active" / "last_test_run.json"


def build_report_data(skip_tests: bool, cache_path: Path) -> ReportData:
    """Thu thập tất cả dữ liệu từ code/docs thực tế."""
    # Skills
    try:
        skills = collect_skills(SKILLS_ROOT)
        skill_warnings: list[str] = []
    except SkillFrontmatterError as e:
        skill_warnings = [f"W003: {e}"]
        skills = []
    # Tests
    if skip_tests:
        tests = load_test_cache(cache_path)
    else:
        tests = run_all_test_suites(TESTS_DIR, cache_path=cache_path)
    # Keyword DB
    kwdb = collect_keyword_db_stats(KWDB_PATH)
    # Standards
    standards = collect_standards(STANDARDS_PATH)
    # Changelog
    changelog = collect_latest_changelog(CHANGELOG_PATH)
    # Calculators
    calculators = collect_calculators(SKILLS_ROOT)
    # Policy Engine (Phase A)
    try:
        from policy_engine import get_policy_engine_status
        policy_status = get_policy_engine_status()
    except Exception:
        policy_status = {}
    return ReportData(
        captured_at=datetime.now().isoformat(timespec="seconds"),
        skills=skills,
        tests=tests,
        keyword_db=kwdb,
        standards=standards,
        changelog=changelog,
        calculators=calculators,
        stale_claims=[],  # sẽ fill sau
        policy_engine=policy_status,
    )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="sync_report",
        description="Đồng bộ BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md từ code/docs thực tế.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Ví dụ:
  python tools/sync_report.py                      # chạy tests, ghi đè file
  python tools/sync_report.py --dry-run             # render ra stdout, không ghi file
  python tools/sync_report.py --output /tmp/x.md    # ghi ra file khác
  python tools/sync_report.py --skip-tests          # dùng cache test
  python tools/sync_report.py --strict              # exit 3 nếu có stale-claim ERROR
""",
    )
    ap.add_argument("--dry-run", action="store_true", help="Render ra stdout, không ghi file")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Đường dẫn output (.md)")
    ap.add_argument("--skip-tests", action="store_true", help="Đọc cache test thay vì chạy lại")
    ap.add_argument("--tests-cache", type=Path, default=DEFAULT_CACHE, help="File cache kết quả test")
    ap.add_argument("--strict", action="store_true", help="Exit 3 nếu verify_claims tìm thấy ERROR")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    # Bước 1: thu thập dữ liệu
    print(f"[*] Thu thập dữ liệu từ {_AGENTS_ROOT} ...", file=sys.stderr)
    print(f"    skip_tests={args.skip_tests}, cache={args.tests_cache}", file=sys.stderr)
    data = build_report_data(skip_tests=args.skip_tests, cache_path=args.tests_cache)
    print(
        f"    → {len(data.skills)} skills, {len(data.tests.suites)} test suites, "
        f"{len(data.standards)} tiêu chuẩn, {data.calculators.total_count} calculators",
        file=sys.stderr,
    )
    # Bước 2: verify stale-claims
    if args.output.exists() and not args.dry_run:
        print(f"[*] Phát hiện stale-claims trong {args.output.name} ...", file=sys.stderr)
        data.stale_claims = diff_against_existing_report(args.output, data)
        n_err = sum(1 for c in data.stale_claims if c.severity == "ERROR")
        n_warn = sum(1 for c in data.stale_claims if c.severity == "WARNING")
        print(
            f"    → {len(data.stale_claims)} findings ({n_err} ERROR, {n_warn} WARNING)",
            file=sys.stderr,
        )
    # Bước 3: render
    rendered = render_report(data)
    # Bước 4: output
    if args.dry_run:
        print(rendered)
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"✅ Đã ghi: {args.output}", file=sys.stderr)
    print(
        f"   Stale-claims: {len(data.stale_claims)} "
        f"(ERROR={sum(1 for c in data.stale_claims if c.severity == 'ERROR')})",
        file=sys.stderr,
    )
    if args.strict and any(c.severity == "ERROR" for c in data.stale_claims):
        return 3
    if not data.tests.all_passed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
