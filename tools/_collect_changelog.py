# tools/_collect_changelog.py
# Bộ thu thập: Đọc CHANGELOG.md, trả về entry mới nhất (version, date, title).

from __future__ import annotations

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChangelogLatest:
    """Entry mới nhất trong CHANGELOG.md."""

    version: str = "unknown"
    date: str = "unknown"
    title: str = "unknown"
    bullet_count: int = 0
    raw_heading: str = ""


HEADING_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2})\s*[—-]+\s*(v[\d.]+)\s*:\s*(.+?)\s*$",
    re.MULTILINE,
)


def collect_latest_changelog(changelog_path: Path) -> ChangelogLatest:
    """Đọc CHANGELOG.md, trả về entry mới nhất (heading `## YYYY-MM-DD — vX.Y.Z: Title` đầu tiên)."""
    result = ChangelogLatest()
    if not changelog_path.exists():
        return result
    text = changelog_path.read_text(encoding="utf-8", errors="replace")
    m = HEADING_RE.search(text)
    if not m:
        return result
    result.date = m.group(1)
    result.version = m.group(2)
    result.title = m.group(3).strip()
    result.raw_heading = m.group(0)
    # Đếm bullet trong body (đến heading ## tiếp theo hoặc hết file)
    body_start = m.end()
    next_heading = re.search(r"^##\s+", text[body_start:], re.MULTILINE)
    body = text[body_start : body_start + next_heading.start()] if next_heading else text[body_start:]
    # Bullet = dòng bắt đầu bằng "- **" hoặc "- "
    bullets = re.findall(r"^\s*-\s+\*\*", body, re.MULTILINE)
    result.bullet_count = len(bullets)
    return result
