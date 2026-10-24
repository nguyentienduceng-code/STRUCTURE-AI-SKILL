# tools/_verify_claims.py
# Tính năng cốt lõi: Phát hiện STALE-CLAIMS trong báo cáo markdown cũ.
# Đọc file .md, extract numeric/categorical claims qua regex, so sánh với ReportData mới.
# Trả về list[StaleClaim].

from __future__ import annotations

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class StaleClaim:
    """Một claim sai lệch phát hiện được."""

    pattern_id: str
    line_excerpt: str
    reported_value: str
    actual_value: str
    severity: str  # "ERROR" | "WARNING" | "INFO"


# Forward declaration cho type hint
@dataclass
class _ReportDataLike:
    """Subset của ReportData mà verify_claims cần. Tránh import vòng."""

    pass


# Bảng pattern: (id, regex, value_extractor(ReportData) -> int|str, severity_if_mismatch)
# value_extractor nhận object có các thuộc tính tests, keyword_db, standards, skills.

def _safe_get(obj, *path, default=None):
    """Truy cập an toàn theo path: _safe_get(d, 'tests', 'suites', 3, 'total_count')."""
    cur = obj
    for p in path:
        if cur is None:
            return default
        if isinstance(p, int):
            if not hasattr(cur, "__iter__") or isinstance(cur, (str, bytes)):
                return default
            try:
                cur = cur[p]
            except (IndexError, KeyError, TypeError):
                return default
        else:
            cur = getattr(cur, p, None)
    return cur if cur is not None else default


def _t_suites(obj) -> dict:
    """Helper: trả về {name: SuiteResult} cho tests.suites."""
    suites = _safe_get(obj, "tests", "suites", default=[]) or []
    return {s.name: s for s in suites}


def _ext_intent(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Intent" in name:
            return sr.total_count
    return None


def _ext_intent_passed(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Intent" in name:
            return sr.passed_count
    return None


def _ext_integration_total(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Integration" in name:
            return sr.total_count
    return None


def _ext_integration_passed(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Integration" in name:
            return sr.passed_count
    return None


def _ext_regression_total(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Regression" in name:
            return sr.total_count
    return None


def _ext_approval_total(obj) -> Optional[int]:
    s = _t_suites(obj)
    for name, sr in s.items():
        if "Approval" in name:
            return sr.total_count
    return None


def _ext_kwdb_regex(obj) -> Optional[int]:
    return _safe_get(obj, "keyword_db", "actual_regex_count")


def _ext_kwdb_declared(obj) -> Optional[int]:
    return _safe_get(obj, "keyword_db", "declared_total_keywords")


def _ext_kwdb_tiebreaker(obj) -> Optional[int]:
    tb = _safe_get(obj, "keyword_db", "tie_breaker_keys", default=[]) or []
    return len(tb)


def _ext_kwdb_pipeline(obj) -> Optional[int]:
    pt = _safe_get(obj, "keyword_db", "pipeline_templates", default=[]) or []
    return len(pt)


def _ext_standards(obj) -> Optional[int]:
    st = _safe_get(obj, "standards", default=[]) or []
    return len(st)


def _ext_skills(obj) -> Optional[int]:
    sk = _safe_get(obj, "skills", default=[]) or []
    return len(sk)


# Severity theo pattern id
DEFAULT_SEVERITY = {
    "tests/intent": "ERROR",
    "tests/integration": "ERROR",
    "tests/regression": "ERROR",
    "tests/approval": "ERROR",
    "kwdb/regex": "ERROR",
    "kwdb/declared_total": "WARNING",
    "kwdb/tie_breaker": "ERROR",
    "kwdb/pipeline": "ERROR",
    "standards/count": "ERROR",
    "skills/total": "ERROR",
}


CLAIM_PATTERNS: list[tuple[str, str, Callable, str]] = [
    ("tests/intent", r"(\d+)\s*test\s*cases?", _ext_intent, "ERROR"),
    ("tests/integration", r"(\d+)/(\d+)\s*(?:Integration|integration|checks?)", _ext_integration_total, "ERROR"),
    ("tests/regression", r"(\d+)\s*Calculators?\s*Passed", _ext_regression_total, "ERROR"),
    ("kwdb/regex", r"(\d+)\s*regex\s*patterns?", _ext_kwdb_regex, "ERROR"),
    ("kwdb/declared_total", r"(\d+)\+?\s*(?:từ\s*khóa|keywords?)", _ext_kwdb_declared, "WARNING"),
    ("kwdb/tie_breaker", r"(\d+)\s*(?:tie[\s-]?breaker|nhóm\s+tie)", _ext_kwdb_tiebreaker, "ERROR"),
    ("kwdb/pipeline", r"(\d+)\s*(?:pipeline\s+templates?|template\s+pipeline)", _ext_kwdb_pipeline, "ERROR"),
    ("standards/count", r"(\d+)\s*tiêu\s*chuẩn", _ext_standards, "ERROR"),
    ("skills/total", r"(\d+)\s*skills?\s*(?:chuyên\s*trách|nghiệp\s*vụ)?", _ext_skills, "ERROR"),
]


# Cờ bỏ qua: nếu dòng trong báo cáo cũ đã có "⚠️ Mơ hồ" / "❌ Sai" / "KHÔNG" thì coi như đã acknowledged
ACKNOWLEDGED_MARKERS = ("⚠️", "❌ Sai", "❌ Không", "KHÔNG phải", "đã sửa", "đã verify")


def diff_against_existing_report(
    existing_md_path: Path, new_data
) -> list[StaleClaim]:
    """Đọc file markdown, so sánh claims với new_data, trả về list[StaleClaim].

    Không raise. Nếu file không tồn tại → trả về list rỗng.
    """
    if not existing_md_path.exists():
        return []
    text = existing_md_path.read_text(encoding="utf-8", errors="replace")
    findings: list[StaleClaim] = []
    for line in text.splitlines():
        # Bỏ qua dòng đã acknowledged
        if any(m in line for m in ACKNOWLEDGED_MARKERS):
            continue
        # Bỏ qua dòng trong bảng stale-claims hoặc table header/summary
        if line.strip().startswith("|") and ("🔴" in line or "🟡" in line or "stale-claim" in line.lower()):
            continue
        # Bỏ qua dòng inventory calculator (số skills có calculators khác tổng số skills)
        if "scripts trong" in line or "calculators trong" in line:
            continue
        for pid, pattern, extractor, sev in CLAIM_PATTERNS:
            for m in re.finditer(pattern, line, re.IGNORECASE):
                try:
                    actual = extractor(new_data)
                except Exception:
                    actual = None
                if actual is None:
                    continue
                # Lấy group đầu tiên có chữ số
                claimed = next(
                    (g for g in m.groups() if g and g.isdigit()),
                    None,
                )
                if claimed is None:
                    continue
                try:
                    claimed_int = int(claimed)
                except ValueError:
                    continue
                if claimed_int != actual:
                    # Đặc biệt: với test/intent, nếu claimed < actual thì có thể là stale (low n);
                    # nếu claimed > actual thì vẫn là ERROR vì là sai số.
                    findings.append(
                        StaleClaim(
                            pattern_id=pid,
                            line_excerpt=line.strip()[:200],
                            reported_value=str(claimed_int),
                            actual_value=str(actual),
                            severity=sev,
                        )
                    )
    return findings
