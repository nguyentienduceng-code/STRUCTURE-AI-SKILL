# tools/_collect_keyword_db.py
# Bộ thu thập: Đọc Global_Dispatcher/scripts/keyword_database.json,
# trích số liệu cấu trúc (regex count, tie-breaker count, pipeline count,
# declared vs actual delta).

from __future__ import annotations

import json
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class KeywordDbStats:
    """Số liệu thống kê keyword database."""

    schema_version: str = "unknown"
    last_updated: str = "unknown"
    declared_total_keywords: int = 0
    actual_skill_count: int = 0
    actual_primary_keyword_count: int = 0
    actual_secondary_keyword_count: int = 0
    actual_regex_count: int = 0
    actual_anti_keyword_count: int = 0
    actual_total_keyword_count: int = 0  # primary + secondary + regex
    tie_breaker_keys: list[str] = field(default_factory=list)
    pipeline_templates: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _count_in_skill(skill_cfg: dict) -> tuple[int, int, int, int]:
    """Đếm primary, secondary, regex, anti trong 1 skill config."""
    primary = skill_cfg.get("primary_keywords", []) or []
    secondary = skill_cfg.get("secondary_keywords", []) or []
    regexes = skill_cfg.get("regex_patterns", []) or []
    anti = skill_cfg.get("anti_keywords", []) or []
    # Nếu primary/secondary là dict (keyed by category) thì flatten
    if isinstance(primary, dict):
        primary = [v for vs in primary.values() for v in (vs if isinstance(vs, list) else [vs])]
    if isinstance(secondary, dict):
        secondary = [v for vs in secondary.values() for v in (vs if isinstance(vs, list) else [vs])]
    if isinstance(regexes, dict):
        regexes = [v for vs in regexes.values() for v in (vs if isinstance(vs, list) else [vs])]
    if isinstance(anti, dict):
        anti = [v for vs in anti.values() for v in (vs if isinstance(vs, list) else [vs])]
    return (
        len(primary) if isinstance(primary, list) else 0,
        len(secondary) if isinstance(secondary, list) else 0,
        len(regexes) if isinstance(regexes, list) else 0,
        len(anti) if isinstance(anti, list) else 0,
    )


def collect_keyword_db_stats(json_path: Path) -> KeywordDbStats:
    """Đọc file JSON, trả về KeywordDbStats. Không raise — lỗi ghi vào warnings."""
    stats = KeywordDbStats()
    if not json_path.exists():
        stats.warnings.append(f"W005: file không tồn tại: {json_path}")
        return stats
    try:
        data: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        stats.warnings.append(f"W005: lỗi parse JSON: {e}")
        return stats
    meta = data.get("_meta", {}) or {}
    stats.schema_version = str(meta.get("version", "unknown"))
    stats.last_updated = str(meta.get("last_updated", "unknown"))
    stats.declared_total_keywords = int(meta.get("total_keywords", 0) or 0)
    skills = data.get("skills", {}) or {}
    if not isinstance(skills, dict):
        stats.warnings.append("W005: 'skills' không phải dict")
        return stats
    stats.actual_skill_count = len(skills)
    for skill_name, skill_cfg in skills.items():
        if not isinstance(skill_cfg, dict):
            stats.warnings.append(f"W005: skill '{skill_name}' không phải dict")
            continue
        p, s, r, a = _count_in_skill(skill_cfg)
        stats.actual_primary_keyword_count += p
        stats.actual_secondary_keyword_count += s
        stats.actual_regex_count += r
        stats.actual_anti_keyword_count += a
    stats.actual_total_keyword_count = (
        stats.actual_primary_keyword_count
        + stats.actual_secondary_keyword_count
        + stats.actual_regex_count
    )
    # Tie-breakers
    tb = data.get("tie_breakers", {}) or {}
    if isinstance(tb, dict):
        stats.tie_breaker_keys = list(tb.keys())
    elif isinstance(tb, list):
        stats.tie_breaker_keys = [str(x) for x in tb]
    # Pipeline templates
    pt = data.get("pipeline_templates", {}) or {}
    if isinstance(pt, dict):
        stats.pipeline_templates = sorted(pt.keys())
    elif isinstance(pt, list):
        stats.pipeline_templates = [str(x) for x in pt]
    return stats
