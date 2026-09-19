"""
_report_utils.py — Citation, η, Unicode rendering helpers.

Cung cấp:
- format_eta(value, decimals=2) — format utilization ratio (η = 0.85)
- format_citation(citation) — render CitationObject 4-tuple
- render_citation_badge(status) — VERIFIED / UNVERIFIED badge
- format_number(value, precision) — format số liệu kỹ thuật
- safe_filename(text) — sanitize cho file names
- unicode_escape(s) — fallback cho Windows console cp1252
- parse_iso_date(d) — parse ISO date strings

Updated: 2026-08-31 — Phase A of Reporting Upgrade v4.0
"""

import re
from typing import Optional, Union
from datetime import datetime, date


# ════════════════════════════════════════════════════════════════════════════
# NUMERIC FORMATTERS
# ════════════════════════════════════════════════════════════════════════════

def format_eta(value: Optional[float], decimals: int = 2) -> str:
    """
    Format utilization ratio.
    η = 0.85 → 'η = 0.85'
    η = 1.05 → 'η = 1.05 ❌'
    η = None → 'η = N/A'
    """
    if value is None:
        return 'η = N/A'
    formatted = f'{value:.{decimals}f}'
    if value > 1.0:
        return f'η = {formatted} ❌'
    elif value > 0.95:
        return f'η = {formatted} ⚠️'
    else:
        return f'η = {formatted} ✅'


def format_eta_percent(value: Optional[float], decimals: int = 1) -> str:
    """Format utilization as percentage: 0.85 → '85.0%'"""
    if value is None:
        return 'N/A'
    return f'{value * 100:.{decimals}f}%'


def format_number(value: Optional[Union[int, float]], precision: int = 2,
                  unit: str = '') -> str:
    """
    Format số liệu kỹ thuật.
    1234.5678, precision=2 → '1,234.57'
    0.000123, precision=4 → '0.0001'
    """
    if value is None:
        return 'N/A'
    if isinstance(value, int) or (isinstance(value, float) and value == int(value)):
        formatted = f'{int(value):,}'
    else:
        formatted = f'{value:,.{precision}f}'
    if unit:
        formatted += f' {unit}'
    return formatted


def format_currency(value: Optional[float], currency: str = 'VND',
                    precision: int = 0) -> str:
    """
    Format tiền tệ Việt Nam.
    1234567 → '1,234,567 ₫'
    """
    if value is None:
        return 'N/A'
    formatted = f'{value:,.{precision}f}'
    if currency == 'VND':
        return f'{formatted} ₫'
    return f'{formatted} {currency}'


# ════════════════════════════════════════════════════════════════════════════
# CITATION RENDERING
# ════════════════════════════════════════════════════════════════════════════

def format_citation(citation: dict) -> str:
    """
    Format CitationObject (theo schema) thành chuỗi 4-tuple.
    CitationObject = {
        Ma_Tieu_Chuan, Nam_Ban_Hanh, Dieu_Bang_Muc,
        Ten_Bang_Hinh?, Trang_So?, Trich_Yeu, Nguon_File?
    }

    Output:
    'TCVN 5574:2018 — Điều 10.2.3 — Trang 45 — Hệ số tin cậy γ_b'

    Nếu thiếu field: gracefully handle.
    """
    if not citation:
        return '[No citation]'

    parts = []

    # 1. Mã tiêu chuẩn + năm
    ma = citation.get('Ma_Tieu_Chuan', '')
    nam = citation.get('Nam_Ban_Hanh', '')
    if ma:
        if nam:
            parts.append(f'{ma}:{nam}')
        else:
            parts.append(ma)

    # 2. Điều/Bảng/Mục
    dieu = citation.get('Dieu_Bang_Muc', '')
    ten_bang = citation.get('Ten_Bang_Hinh', '')
    if dieu:
        if ten_bang:
            parts.append(f'{dieu} {ten_bang}')
        else:
            parts.append(dieu)

    # 3. Trang
    trang = citation.get('Trang_So', '')
    if trang:
        parts.append(f'Trang {trang}')

    # 4. Trích yếu
    trich = citation.get('Trich_Yeu', '')
    if trich:
        parts.append(trich)

    return ' — '.join(parts) if parts else '[Empty citation]'


def format_citation_short(citation: dict) -> str:
    """Short form: 'TCVN 5574:2018 Đ.10.2'"""
    if not citation:
        return '—'
    ma = citation.get('Ma_Tieu_Chuan', '')
    nam = citation.get('Nam_Ban_Hanh', '')
    dieu = citation.get('Dieu_Bang_Muc', '')
    base = f'{ma}:{nam}' if nam else ma
    if dieu:
        base += f' {dieu}'
    return base or '—'


def render_citation_badge(status: str) -> str:
    """Render VERIFIED/UNVERIFIED badge."""
    if status == 'VERIFIED':
        return '✅ VERIFIED'
    elif status == 'UNVERIFIED':
        return '⚠️ UNVERIFIED'
    elif status == 'PARTIAL':
        return '🟡 PARTIAL'
    return f'❓ {status}'


# ════════════════════════════════════════════════════════════════════════════
# DATE FORMATTERS
# ════════════════════════════════════════════════════════════════════════════

def parse_iso_date(date_str: Optional[str]) -> Optional[date]:
    """Parse ISO date string (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def format_vn_date(d: Optional[Union[date, datetime, str]],
                   format_str: str = '%d/%m/%Y') -> str:
    """Format date theo chuẩn Việt Nam DD/MM/YYYY."""
    if d is None:
        return '—'
    if isinstance(d, str):
        d = parse_iso_date(d) or datetime.now()
    return d.strftime(format_str)


# ════════════════════════════════════════════════════════════════════════════
# FILENAME SANITIZER
# ════════════════════════════════════════════════════════════════════════════

def safe_filename(text: str, max_length: int = 100) -> str:
    """
    Sanitize text để dùng làm filename.
    Bỏ special chars, replace spaces với underscore.
    """
    if not text:
        return 'untitled'

    # Vietnamese accent removal (basic)
    text = text.replace('ă', 'a').replace('Ă', 'A')
    text = text.replace('â', 'a').replace('Â', 'A')
    text = text.replace('ê', 'e').replace('Ê', 'E')
    text = text.replace('ô', 'o').replace('Ô', 'O')
    text = text.replace('ơ', 'o').replace('Ơ', 'O')
    text = text.replace('ư', 'u').replace('Ư', 'U')
    text = text.replace('đ', 'd').replace('Đ', 'D')

    # Replace special chars
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text)
    text = re.sub(r'-+', '-', text)

    # Trim length
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip('_-')


# ════════════════════════════════════════════════════════════════════════════
# UNICODE ESCAPE (for Windows console cp1252)
# ════════════════════════════════════════════════════════════════════════════

def safe_print(s: str):
    """Print an toàn trên Windows console với Unicode fallback."""
    try:
        print(s)
    except UnicodeEncodeError:
        # Fallback: replace non-ASCII with closest ASCII
        safe_s = s.encode('ascii', 'replace').decode('ascii')
        print(safe_s)


# ════════════════════════════════════════════════════════════════════════════
# PRIORITY/Severity RENDERING
# ════════════════════════════════════════════════════════════════════════════

PRIORITY_SYMBOLS = {
    'CRITICAL': '🔴',
    'URGENT': '🟠',
    'HIGH': '🟡',
    'NORMAL': '🟢',
    'ROUTINE': '🔵',
}

PRIORITY_DEADLINES = {
    'CRITICAL': 1,   # days
    'URGENT': 3,
    'HIGH': 7,
    'NORMAL': 14,
    'ROUTINE': 21,
}


def render_priority_badge(level: str) -> str:
    """Render priority badge with symbol."""
    sym = PRIORITY_SYMBOLS.get(level, '⚪')
    return f'{sym} {level}'


def get_priority_deadline_days(level: str) -> int:
    """Default deadline in days cho priority level."""
    return PRIORITY_DEADLINES.get(level, 14)


# ════════════════════════════════════════════════════════════════════════════
# RATING HELPERS
# ════════════════════════════════════════════════════════════════════════════

RATING_COLORS = {
    'GREEN': '🟢',
    'YELLOW': '🟡',
    'ORANGE': '🟠',
    'RED': '🔴',
}


def render_rating(rating: str) -> str:
    """Render rating badge."""
    color = RATING_COLORS.get(rating, '⚪')
    return f'{color} {rating}'