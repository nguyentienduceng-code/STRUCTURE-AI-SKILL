# tools/_render_markdown.py
# Pure function: nhận ReportData, trả về chuỗi Markdown.
# KHÔNG có I/O, KHÔNG subprocess, KHÔNG narrative tự do. Toàn bộ là tables + bullets.

from __future__ import annotations

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _collect_changelog import ChangelogLatest
    from _collect_calculators import CalculatorInventory
    from _collect_keyword_db import KeywordDbStats
    from _collect_skills import Skill
    from _collect_tests import TestRunResult
    from _collect_standards import StandardRow
    from _verify_claims import StaleClaim


@dataclass
class ReportData:
    """Tổng hợp tất cả data cần cho report."""

    captured_at: str
    skills: list  # list[Skill]
    tests: object  # TestRunResult
    keyword_db: object  # KeywordDbStats
    standards: list  # list[StandardRow]
    changelog: object  # ChangelogLatest
    calculators: object  # CalculatorInventory
    stale_claims: list = field(default_factory=list)  # list[StaleClaim]
    policy_engine: dict = field(default_factory=dict)


def _emoji_status(passed: bool, total: int | None) -> str:
    if total is None:
        return "⛔ UNPARSED"
    return "✅" if passed else "❌"


def render_report(data) -> str:
    """Render ReportData thành Markdown. Pure function."""
    lines: list[str] = []
    # ===== HEADER =====
    lines.append("# BÁO CÁO KỸ THUẬT TỔNG HỢP HỆ THỐNG AGENTIC")
    lines.append("# *(Auto-generated bởi `tools/sync_report.py`)*")
    lines.append("")
    lines.append(f"> **Phiên bản tài liệu:** v{data.captured_at}  ")
    lines.append("> **Cơ sở hệ thống:** `.agents/`  ")
    lines.append("> **Cách tái tạo:** `python tools/sync_report.py [--dry-run]`")
    lines.append("")

    # ===== §1 TỔNG QUAN =====
    n_skills = len(data.skills)
    n_prod = sum(1 for s in data.skills if getattr(s, "status", "") == "production")
    n_placeholder = sum(1 for s in data.skills if getattr(s, "status", "") == "placeholder")
    n_calc = getattr(data.calculators, "total_count", 0)
    n_std = len(data.standards)
    lines.append("## 1. TỔNG QUAN")
    lines.append("")
    lines.append(f"- **Skills:** {n_skills} ({n_prod} production + {n_placeholder} placeholder v0.1.0)")
    lines.append(
        f"- **Test suites:** {len(data.tests.suites)} — Grand total: "
        f"{data.tests.grand_total_passed} passed / {data.tests.grand_total_failed} failed"
    )
    lines.append(f"- **Tiêu chuẩn locked:** {n_std}")
    lines.append(f"- **Calculator scripts:** {n_calc}")
    lines.append(f"- **Changelog mới nhất:** {data.changelog.version} ({data.changelog.date})")
    policy_engine_data = getattr(data, "policy_engine", None)
    if policy_engine_data:
        pe_phase = policy_engine_data.get("phase", "Phase C (Full Suite)")
        pe_rules = policy_engine_data.get("active_rules_count", 0)
        pe_triggers = policy_engine_data.get("triggers_count", 0)
        pe_red_flags = policy_engine_data.get("red_flags_count", 0)
        lines.append(
            f"- **Policy Engine:** {pe_phase} ({pe_rules} rules active: VE/Repair, {pe_triggers} triggers, {pe_red_flags} red flags, RFI priority)"
        )
    if not data.tests.all_passed:
        lines.append("")
        lines.append("> ⚠️ **Có test suite thất bại.** Xem chi tiết §3.")
    lines.append("")

    # ===== §2 SKILL INVENTORY =====
    lines.append("## 2. SKILL INVENTORY")
    lines.append("")
    lines.append("| # | Skill | Version | Last Updated | Status |")
    lines.append("|---|---|---|---|---|")
    for i, s in enumerate(data.skills, 1):
        status_icon = "🟢" if s.status == "production" else "🟡"
        lines.append(f"| {i} | {s.name} | {s.version} | {s.last_updated} | {status_icon} {s.status} |")
    lines.append("")

    # ===== §3 TEST SUITES =====
    lines.append("## 3. KẾT QUẢ TEST SUITES")
    lines.append("")
    lines.append("| # | Suite | Passed/Total | Failed | Time (s) | Status |")
    lines.append("|---|---|---|---|---|---|")
    for i, s in enumerate(data.tests.suites, 1):
        passed_total = (
            f"{s.passed_count}/{s.total_count}"
            if s.total_count is not None
            else "—"
        )
        failed = s.failed_count if s.failed_count is not None else "—"
        status = _emoji_status(s.passed, s.total_count)
        if s.timed_out:
            status = "⏱ TIMEOUT"
        elif s.error:
            status = f"💥 {s.error[:30]}"
        lines.append(
            f"| {i} | {s.name} | {passed_total} | {failed} | {s.elapsed_sec:.2f} | {status} |"
        )
    lines.append("")
    lines.append(
        f"**Grand total:** {data.tests.grand_total_passed} passed / "
        f"{data.tests.grand_total_failed} failed trong {data.tests.total_elapsed_sec:.2f}s"
    )
    if data.tests.unparsed_suites:
        lines.append("")
        lines.append(f"⚠️ **Unparsed suites:** {', '.join(data.tests.unparsed_suites)}")
    lines.append("")

    # ===== §4 KEYWORD DATABASE =====
    lines.append("## 4. KEYWORD DATABASE")
    lines.append("")
    kwdb = data.keyword_db
    lines.append(f"- **Schema version:** {kwdb.schema_version} (last updated {kwdb.last_updated})")
    lines.append(
        f"- **Skills có config:** {kwdb.actual_skill_count} (so với declared {kwdb.declared_total_keywords} tổng keywords)"
    )
    lines.append("")
    lines.append("| Loại | Actual count |")
    lines.append("|---|---|")
    lines.append(f"| Primary keywords | {kwdb.actual_primary_keyword_count} |")
    lines.append(f"| Secondary keywords | {kwdb.actual_secondary_keyword_count} |")
    lines.append(f"| Regex patterns | {kwdb.actual_regex_count} |")
    lines.append(f"| Anti-keywords | {kwdb.actual_anti_keyword_count} |")
    lines.append(f"| **Tổng (p+s+r)** | **{kwdb.actual_total_keyword_count}** |")
    lines.append("")
    if kwdb.declared_total_keywords and kwdb.declared_total_keywords != kwdb.actual_total_keyword_count:
        delta = kwdb.actual_total_keyword_count - kwdb.declared_total_keywords
        sign = "+" if delta > 0 else ""
        lines.append(
            f"> ℹ️ `_meta.total_keywords` khai báo = {kwdb.declared_total_keywords}, "
            f"thực tế đếm được = {kwdb.actual_total_keyword_count} "
            f"({sign}{delta})."
        )
        lines.append("")
    lines.append(f"**Tie-breaker keys:** `{', '.join(kwdb.tie_breaker_keys) or '(none)'}`")
    lines.append("")
    lines.append(f"**Pipeline templates ({len(kwdb.pipeline_templates)}):**")
    for t in kwdb.pipeline_templates:
        lines.append(f"- `{t}`")
    lines.append("")

    # ===== §5 TIÊU CHUẨN =====
    lines.append("## 5. TIÊU CHUẨN LOCKED")
    lines.append("")
    lines.append(f"**Tổng cộng:** {n_std} rows trong bảng chốt phiên bản")
    lines.append("")
    lines.append("| # | Lĩnh vực | Phiên bản chuẩn | Phiên bản cũ (đối chiếu) |")
    lines.append("|---|---|---|---|")
    for i, row in enumerate(data.standards, 1):
        legacy = row.legacy if row.legacy else "—"
        lines.append(f"| {i} | {row.domain} | **{row.current}** | {legacy} |")
    lines.append("")

    # ===== §6 CALCULATOR INVENTORY =====
    lines.append("## 6. CALCULATOR INVENTORY")
    lines.append("")
    lines.append(f"**Tổng:** {n_calc} scripts trong {data.calculators.skill_count_with_calculators} skills")
    lines.append("")
    lines.append("| Skill | Số scripts |")
    lines.append("|---|---|")
    for skill_name in sorted(data.calculators.by_skill.keys()):
        n = len(data.calculators.by_skill[skill_name])
        lines.append(f"| {skill_name} | {n} |")
    lines.append("")

    # ===== §7 CHANGELOG =====
    lines.append("## 7. CHANGELOG MỚI NHẤT")
    lines.append("")
    lines.append(f"**{data.changelog.version}** ({data.changelog.date}) — {data.changelog.title}")
    lines.append("")
    lines.append(f"- {data.changelog.bullet_count} bullets trong entry này")
    lines.append("")

    # ===== §8 STALE-CLAIMS =====
    lines.append("## 8. STALE-CLAIMS PHÁT HIỆN")
    lines.append("")
    if not data.stale_claims:
        lines.append("✅ **Không phát hiện stale-claim.** Báo cáo mới đồng bộ với code.")
    else:
        n_err = sum(1 for c in data.stale_claims if c.severity == "ERROR")
        n_warn = sum(1 for c in data.stale_claims if c.severity == "WARNING")
        lines.append(
            f"Tổng: **{len(data.stale_claims)}** stale-claims "
            f"({n_err} ERROR, {n_warn} WARNING)"
        )
        lines.append("")
        lines.append("| # | Severity | Pattern | Báo cáo cũ nói | Code thực tế | Excerpt |")
        lines.append("|---|---|---|---|---|---|")
        for i, c in enumerate(data.stale_claims, 1):
            sev_icon = "🔴" if c.severity == "ERROR" else "🟡"
            excerpt = c.line_excerpt.replace("|", "\\|")[:120]
            lines.append(
                f"| {i} | {sev_icon} {c.severity} | {c.pattern_id} | "
                f"`{c.reported_value}` | `{c.actual_value}` | {excerpt} |"
            )
    lines.append("")

    # ===== APPROVAL MATRIX & DISCLAIMER =====
    lines.append("---")
    lines.append("")
    lines.append("## APPROVAL MATRIX")
    lines.append("")
    lines.append("| Bên | Trách nhiệm | Đề xuất |")
    lines.append("|---|---|---|")
    lines.append(
        "| AI Assistant | Tạo báo cáo tự động từ code/docs | Trợ lý AI — cần kỹ sư có chứng chỉ "
        "hành nghề kiểm tra xác nhận trước khi ký |"
    )
    lines.append("| Kỹ sư chứng chỉ hành nghề | Xác minh & ký duyệt | — |")
    lines.append("")
    lines.append(
        "*Disclaimer: Tài liệu này do trợ lý AI lập tự động từ code và docs. "
        "Kết quả mang tính tham khảo. Tuân thủ AGENTS.md §8.*"
    )
    lines.append("")
    return "\n".join(lines)
