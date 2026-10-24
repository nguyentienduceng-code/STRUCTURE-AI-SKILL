# tests/test_sync_report.py
# Test suite cho tools/sync_report.py.
# Chạy: python -m unittest tests.test_sync_report -v

from __future__ import annotations

import io
import json
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Đảm bảo tools/ có thể import
_AGENTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_AGENTS_ROOT / "tools"))

from _collect_calculators import collect_calculators  # noqa: E402
from _collect_changelog import collect_latest_changelog  # noqa: E402
from _collect_keyword_db import collect_keyword_db_stats  # noqa: E402
from _collect_skills import collect_skills  # noqa: E402
from _collect_standards import collect_standards  # noqa: E402
from _collect_tests import load_test_cache  # noqa: E402
from _render_markdown import render_report, ReportData  # noqa: E402
from _verify_claims import diff_against_existing_report, StaleClaim  # noqa: E402
from sync_report import build_report_data, parse_args  # noqa: E402

SKILLS_ROOT = _AGENTS_ROOT / "skills"
KWDB_PATH = SKILLS_ROOT / "Global_Dispatcher" / "scripts" / "keyword_database.json"
STANDARDS_PATH = SKILLS_ROOT / "STANDARDS_LOCK.md"
CHANGELOG_PATH = SKILLS_ROOT / "CHANGELOG.md"


class TestCollectSkills(unittest.TestCase):
    """Walk SKILLS_ROOT thật, đảm bảo parse 13 skills với version đúng."""

    def test_returns_13_skills(self):
        skills = collect_skills(SKILLS_ROOT)
        self.assertEqual(len(skills), 13, f"Expected 13 skills, got {len(skills)}")
        names = {s.name for s in skills}
        expected = {
            "Cost_Estimator", "Design_Evaluation", "Global_Dispatcher",
            "Project_Manager", "SKILL_BIM_COORDINATION", "SKILL_FORENSIC",
            "SKILL_GEOTECH", "SKILL_PHULUC", "SKILL_RFI", "SKILL_TEMPWORKS",
            "SKILL_VERIFY", "Structural_Design_Engineer", "Technical_Illustrator",
        }
        self.assertEqual(names, expected)

    def test_versions_match_semver(self):
        skills = collect_skills(SKILLS_ROOT)
        import re
        for s in skills:
            self.assertRegex(s.version, r"^\d+\.\d+\.\d+$", f"{s.name} version invalid: {s.version}")
            self.assertIn(s.status, ("production", "placeholder"), f"{s.name} status invalid: {s.status}")

    def test_production_vs_placeholder(self):
        skills = collect_skills(SKILLS_ROOT)
        production = [s for s in skills if s.status == "production"]
        placeholder = [s for s in skills if s.status == "placeholder"]
        # 11 production + 2 placeholder (PM, BIM đều major=0, SKILL_TEMPWORKS v1.0.0 is production)
        self.assertEqual(len(production), 11)
        self.assertEqual(len(placeholder), 2)
        placeholder_names = {s.name for s in placeholder}
        self.assertEqual(placeholder_names, {"Project_Manager", "SKILL_BIM_COORDINATION"})


class TestCollectKeywordDb(unittest.TestCase):
    """Load keyword_database.json thật."""

    def test_stats(self):
        stats = collect_keyword_db_stats(KWDB_PATH)
        self.assertEqual(stats.schema_version, "1.1.0")
        self.assertEqual(stats.actual_skill_count, 12)
        self.assertEqual(stats.actual_regex_count, 61)
        self.assertEqual(stats.tie_breaker_keys, ["description", "rules"])
        self.assertEqual(len(stats.pipeline_templates), 7)
        self.assertEqual(stats.declared_total_keywords, 417)
        # Tổng primary+secondary+regex phải > 0
        self.assertGreater(stats.actual_total_keyword_count, 0)


class TestCollectStandards(unittest.TestCase):
    """Parse STANDARDS_LOCK.md thật."""

    def test_at_least_15_standards(self):
        rows = collect_standards(STANDARDS_PATH)
        self.assertGreaterEqual(len(rows), 15, f"Only {len(rows)} rows parsed")
        # Tất cả rows phải có current chứa TCVN/TCXDVN/QCVN/ACI/Thông tư/TT/Bowles/Robertson
        import re
        for r in rows:
            self.assertRegex(r.current, r"(TCVN|TCXDVN|QCVN|ACI|Thông\s+tư|TT|Bowles|Robertson)", f"Bad current: {r.current}")


class TestCollectChangelog(unittest.TestCase):
    """Parse CHANGELOG.md thật."""

    def test_latest_is_v6_4(self):
        cl = collect_latest_changelog(CHANGELOG_PATH)
        self.assertEqual(cl.version, "v6.4")
        self.assertEqual(cl.date, "2026-10-15")
        self.assertGreater(cl.bullet_count, 0)


class TestCollectCalculators(unittest.TestCase):
    """Walk calculators per skill."""

    def test_total_at_least_50(self):
        inv = collect_calculators(SKILLS_ROOT)
        self.assertGreaterEqual(inv.total_count, 50, f"Only {inv.total_count} calculators")
        # Design_Evaluation phải có calculators (ít nhất 5)
        self.assertIn("Design_Evaluation", inv.by_skill)
        self.assertGreaterEqual(len(inv.by_skill["Design_Evaluation"]), 5)


class TestRenderReportDeterministic(unittest.TestCase):
    """render_report phải deterministic với cùng input."""

    def test_same_input_same_output(self):
        from _collect_changelog import ChangelogLatest
        from _collect_calculators import CalculatorInventory
        from _collect_keyword_db import KeywordDbStats
        data = ReportData(
            captured_at="2026-10-17T00:00:00",
            skills=[],
            tests=type("T", (), {"suites": [], "grand_total_passed": 0, "grand_total_failed": 0,
                                  "all_passed": True, "total_elapsed_sec": 0.0, "unparsed_suites": []})(),
            keyword_db=KeywordDbStats(schema_version="1.0.0", last_updated="2026-10-12",
                                       declared_total_keywords=100, actual_skill_count=0,
                                       actual_primary_keyword_count=0, actual_secondary_keyword_count=0,
                                       actual_regex_count=0, actual_anti_keyword_count=0,
                                       actual_total_keyword_count=0, tie_breaker_keys=[],
                                       pipeline_templates=[]),
            standards=[],
            changelog=ChangelogLatest(version="v6.4", date="2026-10-15",
                                       title="Test", bullet_count=0),
            calculators=CalculatorInventory(by_skill={}, total_count=0, skill_count_with_calculators=0),
            stale_claims=[],
        )
        out1 = render_report(data)
        out2 = render_report(data)
        self.assertEqual(out1, out2)


class TestVerifyClaimsDetectsDrift(unittest.TestCase):
    """Tạo báo cáo giả có claims sai, verify phát hiện."""

    def test_detects_wrong_intent_test_count(self):
        from _collect_changelog import ChangelogLatest
        from _collect_calculators import CalculatorInventory
        from _collect_keyword_db import KeywordDbStats
        from _collect_tests import SuiteResult, TestRunResult

        # Tạo data giả: intent test count = 17
        fake_suite = SuiteResult(
            name="Intent Classifier Benchmark (17 tests)",
            cmd=[], passed=True, elapsed_sec=0.1,
            passed_count=17, failed_count=0, total_count=17,
        )
        data = ReportData(
            captured_at="2026-10-17T00:00:00",
            skills=[],
            tests=TestRunResult(suites=[fake_suite], all_passed=True,
                                 grand_total_passed=17, grand_total_failed=0),
            keyword_db=KeywordDbStats(),
            standards=[],
            changelog=ChangelogLatest(),
            calculators=CalculatorInventory(),
            stale_claims=[],
        )
        # Tạo file .md giả có claim sai: "15 test cases" thay vì 17
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Test\n\nIntent classifier chạy 15 test cases, pass 100%.\n")
            f.flush()
            md_path = Path(f.name)
        try:
            findings = diff_against_existing_report(md_path, data)
            self.assertGreater(len(findings), 0, "Should detect '15 test cases' vs actual 17")
            # Phải có pattern tests/intent
            ids = {f.pattern_id for f in findings}
            self.assertIn("tests/intent", ids)
            # Severity ERROR
            errors = [f for f in findings if f.severity == "ERROR"]
            self.assertGreater(len(errors), 0)
        finally:
            md_path.unlink()


class TestSkipTestsLoadsCache(unittest.TestCase):
    """Đảm bảo --skip-tests đọc cache thay vì chạy subprocess."""

    def test_load_test_cache_reads_json(self):
        cache_payload = {
            "schema_version": "1.0",
            "captured_at": "2026-10-17T00:00:00",
            "all_passed": True,
            "total_elapsed_sec": 1.0,
            "grand_total_passed": 50,
            "grand_total_failed": 0,
            "unparsed_suites": [],
            "suites": [
                {
                    "name": "Fake Suite",
                    "passed": True,
                    "elapsed_sec": 1.0,
                    "passed_count": 50,
                    "failed_count": 0,
                    "total_count": 50,
                    "timed_out": False,
                    "error": "",
                }
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(cache_payload, f)
            f.flush()
            cache_path = Path(f.name)
        try:
            result = load_test_cache(cache_path)
            self.assertEqual(len(result.suites), 1)
            self.assertEqual(result.suites[0].total_count, 50)
            self.assertEqual(result.grand_total_passed, 50)
        finally:
            cache_path.unlink()


class TestMalformedSkillFrontmatter(unittest.TestCase):
    """Skill thiếu version → không crash, trả về list rỗng hoặc raise."""

    def test_missing_version_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "BadSkill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: BadSkill\ndescription: no version here\n---\n# Body\n",
                encoding="utf-8",
            )
            from _collect_skills import SkillFrontmatterError
            with self.assertRaises(SkillFrontmatterError):
                collect_skills(tmp_path)


class TestCLIArgs(unittest.TestCase):
    """parse_args xử lý flags đúng."""

    def test_default_args(self):
        with mock.patch("sys.argv", ["sync_report"]):
            args = parse_args()
            self.assertFalse(args.dry_run)
            self.assertFalse(args.skip_tests)
            self.assertFalse(args.strict)

    def test_dry_run_flag(self):
        with mock.patch("sys.argv", ["sync_report", "--dry-run"]):
            args = parse_args()
            self.assertTrue(args.dry_run)

    def test_strict_flag(self):
        with mock.patch("sys.argv", ["sync_report", "--strict"]):
            args = parse_args()
            self.assertTrue(args.strict)


if __name__ == "__main__":
    unittest.main()
