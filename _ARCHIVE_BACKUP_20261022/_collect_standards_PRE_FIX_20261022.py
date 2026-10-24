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


# Regex tìm mã tiêu chuẩn: TCVN 5574:2018, QCVN 03:2022, ACI 347-04
STD_REGEX = re.compile(
    r"(TCVN|QCVN|ACI)\s+([\w./\-]+:?[\w./\-]*)",
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
    # Tìm section "## 1. Bảng Chốt"
    m_section = re.search(r"^##\s*1\.\s*Bảng\s*Chốt.*$", text, re.MULTILINE | re.IGNORECASE)
    if m_section:
        start = m_section.end()
        # Cắt đến heading ## tiếp theo
        m_next = SECTION_HEADING.search(text, start)
        section_text = text[start : m_next.start()] if m_next else text[start:]
    else:
        section_text = text  # fallback toàn file
    rows: list[StandardRow] = []
    for line in section_text.splitlines():
        if not ROW_DELIM.match(line):
            continue
        # Bỏ separator |---|---|---|
        if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        domain = cells[0]
        current = cells[1]
        legacy = cells[2] if len(cells) > 2 else None
        pdf_ref = cells[3] if len(cells) > 3 else None
        # Làm sạch: domain bỏ ** markdown bold
        domain = re.sub(r"\*\*", "", domain).strip()
        # Làm sạch current: lấy text đầu tiên có dạng TCVN/QCVN/ACI
        m_current = STD_REGEX.search(current.replace("**", ""))
        current_clean = m_current.group(0) if m_current else current.replace("**", "").strip()
        # Legacy có thể là "—" → None
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
        # Chỉ thêm nếu current chứa mã tiêu chuẩn
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
