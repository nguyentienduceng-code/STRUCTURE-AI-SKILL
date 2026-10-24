# tools/_collect_standards.py
# Bộ thu thập: Parse STANDARDS_LOCK.md, trích bảng tiêu chuẩn đang khóa.

from __future__ import annotations

import re
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StandardRow:
    """Một dòng trong bảng tiêu chuẩn."""

    domain: str
    current: str
    legacy: str | None
    pdf_ref: str | None


# [FIX BUG-RD-02]: Mở rộng STD_REGEX để bắt đầy đủ TCVN, TCXDVN, QCVN, ACI, Thông tư (TT), Bowles, Robertson
STD_REGEX = re.compile(
    r"(TCVN|TCXDVN|QCVN|ACI|Thông\s+tư|TT|Bowles|Robertson)\s+([\w./\-()]+:?[\w./\-()]*)",
    re.IGNORECASE,
)
ROW_DELIM = re.compile(r"^\s*\|.*\|\s*$")
SECTION_HEADING = re.compile(r"^##\s+", re.MULTILINE)


def collect_standards(lock_path: Path) -> list[StandardRow]:
    """Parse STANDARDS_LOCK.md, trả về list StandardRow.

    Tìm section bắt đầu bằng '## 1.' (Bảng Chốt Phiên bản); nếu không có
    thì fallback scan toàn file bằng STD_REGEX.
    """
    if not lock_path.exists():
        return []
    text = lock_path.read_text(encoding="utf-8", errors="replace")
    m_section = re.search(r"^##\s*1\.\s*Bảng\s*Chốt.*$", text, re.MULTILINE | re.IGNORECASE)
    if m_section:
        start = m_section.end()
        m_next = SECTION_HEADING.search(text, start)
        section_text = text[start : m_next.start()] if m_next else text[start:]
    else:
        section_text = text
    rows: list[StandardRow] = []
    for line in section_text.splitlines():
        if not ROW_DELIM.match(line):
            continue
        if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        # Bỏ dòng header của bảng
        if "Lĩnh vực" in cells[0] or "Phiên bản CHUẨN" in cells[1]:
            continue
        domain = cells[0]
        current = cells[1]
        legacy = cells[2] if len(cells) > 2 else None
        pdf_ref = cells[3] if len(cells) > 3 else None
        domain = re.sub(r"\*\*", "", domain).strip()
        m_current = STD_REGEX.search(current.replace("**", ""))
        current_clean = m_current.group(0) if m_current else current.replace("**", "").strip()
        if legacy in ("—", "-", "", "None"):
            legacy = None
        else:
            legacy_clean = re.sub(r"\*\*", "", legacy).strip()
            m_legacy = STD_REGEX.search(legacy_clean)
            legacy = m_legacy.group(0) if m_legacy else (legacy_clean or None)
        if pdf_ref in ("—", "-", ""):
            pdf_ref = None
        else:
            pdf_ref = re.sub(r"\*\*", "", pdf_ref).strip() or None
        if STD_REGEX.search(current_clean):
            rows.append(
                StandardRow(
                    domain=domain,
                    current=current_clean,
                    legacy=legacy,
                    pdf_ref=pdf_ref,
                )
            )
    return rows


def collect_standards_summary(lock_path: Path) -> dict:
    """Tóm tắt: total rows, distinct current codes, distinct legacy codes."""
    rows = collect_standards(lock_path)
    currents = sorted({r.current for r in rows if r.current})
    legacys = sorted({r.legacy for r in rows if r.legacy})
    return {
        "total": len(rows),
        "distinct_current": len(currents),
        "distinct_legacy": len(legacys),
        "current_codes": currents,
        "legacy_codes": legacys,
    }
