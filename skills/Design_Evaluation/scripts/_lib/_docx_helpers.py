# -*- coding: utf-8 -*-
"""
_docx_helpers.py — Shared DOCX utilities cho tất cả generators (v4.2 — Zero White Text & Landscape Gantt Engine).

Cung cấp:
- Hệ màu Bảng biểu In ấn Tự nhiên (Natural Print Palette — Điều 12b AGENTS.md):
  + Header Bảng: Nền sáng gốc khoáng Xanh Đá Phiến Sương Nhạt (#DCE4EC) hoặc Đá Vôi Sáng (#EAE6DF)
    đi kèm chữ đậm Xanh Thép Trầm (#1E3246) hoặc Mực Than Chì (#1C1E21).
  + Dòng dữ liệu (Data rows): Chữ tối (#1C1E21), nền xen kẽ Trắng (#FFFFFF) và Ngà Giấy Tự Nhiên (#F8F7F4).
  + Dòng Tổng kết (Summary rows): Chữ tối (#1E3246), nền Xám Khoáng Ấm (#F2EFE9) hoặc Xô Thơm Nhạt (#EBF3ED).
- Auto-Linter `sanitize_docx_table_colors(doc)` tự động gắn vào `doc.save()` để quét và chặn 100% chữ màu trắng
  trong mọi bảng biểu trước khi ghi file.
- `add_landscape_gantt_section(doc, image_path, ...)`: Tự động tạo Section Break ngắt sang 01 trang A4 Xoay Ngang
  (Landscape 29.7 x 21.0 cm) riêng biệt để nhúng biểu đồ tiến độ MS Project 300 DPI sắc nét, sau đó tự động trả về
  khổ A4 Dọc (Portrait 21.0 x 29.7 cm) cho các trang nội dung còn lại.
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import re
from typing import List, Optional, Tuple, Union, Dict

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml
from docx.document import Document as DocumentObject


# ════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE — Natural Print Palette (Điều 12b AGENTS.md — Zero White Text)
# ════════════════════════════════════════════════════════════════════════════

COLOR_PRIMARY = '1E3246'            # Xanh Thép Trầm — Prussian Slate (Headings, Table Header Text)
COLOR_ACCENT = '2E4A62'             # Xanh Đá Phiến — Muted Steel Blue (Subheadings H2/H3)
COLOR_TABLE_HEADER_BG = 'DCE4EC'    # Xanh Đá Phiến Sương Nhạt (Table Header Fill — Luma > 88%)
COLOR_TABLE_HEADER_LIME = 'EAE6DF'  # Đá Vôi Sáng (Warm Limestone Header Fill)
COLOR_TABLE_HEADER_TEXT = '1E3246'  # Chữ đậm Xanh Thép Trầm (Tuyệt đối cấm chữ trắng)
COLOR_TEXT_DARK = '1C1E21'          # Mực Than Chì (Data Rows & Body Text)
COLOR_TEXT_MED = '5A626A'           # Xám Chì Ấm (Captions, Footers)
COLOR_ROW_ALT = 'F8F7F4'            # Ngà Giấy Tự Nhiên (Alternating Data Row Fill)
COLOR_LABEL_BG = 'F2EFE9'           # Xám Khoáng Ấm (Summary Rows & Left Label Column)
COLOR_SUMMARY_SAGE = 'EBF3ED'       # Xô Thơm Nhạt (Summary Pass Rows)
COLOR_GRID_BORDER = 'D0CEC7'        # Đường lưới mảnh Xám Đá
COLOR_WARN_BG = 'FBF3E4'
COLOR_WARN_BORDER = '8F5314'
COLOR_CRITICAL = '8C261E'
COLOR_SUCCESS = '1E5631'
COLOR_INFO = '1F4E5B'


def _hex_luma(hex_str: str) -> float:
    clean = str(hex_str or '').strip().lstrip('#').upper()
    if len(clean) == 8:
        clean = clean[-6:]
    if len(clean) != 6:
        return 255.0
    try:
        r, g, b = int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b
    except Exception:
        return 255.0


def _iter_tables_recursive(parent):
    for tbl in getattr(parent, 'tables', []):
        yield tbl
        for row in tbl.rows:
            for cell in row.cells:
                yield from _iter_tables_recursive(cell)


def sanitize_docx_table_colors(
    doc: DocumentObject,
    default_header_text_hex: str = COLOR_PRIMARY,
    default_body_text_hex: str = COLOR_TEXT_DARK,
    default_header_bg_hex: str = COLOR_TABLE_HEADER_BG,
) -> Dict[str, int]:
    """
    AUTO-LINTER BẢNG BIỂU WORD (ĐIỀU 12B AGENTS.MD — ZERO WHITE TEXT LOCK):
    Quét 100% các `run` và ô (`tcPr/shd`) trong toàn bộ bảng biểu (kể cả bảng lồng nhau & bảng Header/Footer)
    trước khi `doc.save()`. Nếu phát hiện `run` có màu chữ trắng (`FFFFFF` / `(255, 255, 255)`) -> Tự động
    ghi đè về `#1E3246` (hoặc `#1C1E21`). Nếu phát hiện ô nền tối (`Luma < 140`) -> Chuyển về `#DCE4EC`.
    """
    stats = {'white_runs_fixed': 0, 'dark_cells_fixed': 0, 'tables_scanned': 0}
    seen_tc = set()

    containers = [doc]
    for sec in getattr(doc, 'sections', []):
        for hf_attr in ('header', 'footer', 'first_page_header', 'first_page_footer', 'even_page_header', 'even_page_footer'):
            hf = getattr(sec, hf_attr, None)
            if hf is not None:
                containers.append(hf)

    for container in containers:
        for tbl in _iter_tables_recursive(container):
            stats['tables_scanned'] += 1
            for r_idx, row in enumerate(tbl.rows):
                for cell in row.cells:
                    tc_id = id(cell._tc)
                    if tc_id not in seen_tc:
                        seen_tc.add(tc_id)
                        tcPr = cell._tc.find(qn('w:tcPr'))
                        if tcPr is not None:
                            for shd in tcPr.findall(qn('w:shd')):
                                fill_val = (shd.get(qn('w:fill')) or '').strip().upper()
                                if fill_val and fill_val not in ('AUTO', 'NONE', COLOR_ROW_ALT, COLOR_LABEL_BG, COLOR_SUMMARY_SAGE):
                                    if _hex_luma(fill_val) < 140.0:
                                        shd.set(qn('w:fill'), default_header_bg_hex)
                                        stats['dark_cells_fixed'] += 1

                    for p in cell.paragraphs:
                        pPr = p._p.find(qn('w:pPr'))
                        if pPr is not None:
                            for p_shd in pPr.findall(qn('w:shd')):
                                p_fill = (p_shd.get(qn('w:fill')) or '').strip().upper()
                                if p_fill and p_fill not in ('AUTO', 'NONE'):
                                    if _hex_luma(p_fill) < 140.0:
                                        p_shd.set(qn('w:fill'), default_header_bg_hex)
                                        stats['dark_cells_fixed'] += 1

                        for run in p.runs:
                            is_white = False
                            try:
                                if run.font and run.font.color and run.font.color.rgb:
                                    if str(run.font.color.rgb).upper() == '1E3246':
                                        pass
                                    elif str(run.font.color.rgb).upper() in ('FFFFFF', 'FEFEFE', 'FDFDFD'):
                                        is_white = True
                            except Exception:
                                pass

                            rPr = run._r.find(qn('w:rPr'))
                            if rPr is not None:
                                c_elem = rPr.find(qn('w:color'))
                                if c_elem is not None:
                                    c_val = (c_elem.get(qn('w:val')) or '').strip().upper()
                                    if c_val in ('FFFFFF', 'FEFEFE', 'FDFDFD'):
                                        is_white = True

                            if is_white:
                                target_hex = default_header_text_hex if (run.bold or r_idx == 0) else default_body_text_hex
                                run.font.color.rgb = RGBColor.from_string(target_hex)
                                stats['white_runs_fixed'] += 1

                        for r_elem in p._p.iter(qn('w:r')):
                            rPr = r_elem.find(qn('w:rPr'))
                            if rPr is not None:
                                c_elem = rPr.find(qn('w:color'))
                                if c_elem is not None:
                                    c_val = (c_elem.get(qn('w:val')) or '').strip().upper()
                                    if c_val in ('FFFFFF', 'FEFEFE', 'FDFDFD'):
                                        c_elem.set(qn('w:val'), default_header_text_hex if r_idx == 0 else default_body_text_hex)
                                        stats['white_runs_fixed'] += 1

    return stats


def _attach_auto_sanitize_on_save(doc: DocumentObject) -> DocumentObject:
    """Bọc hàm doc.save() để tự động chạy sanitize_docx_table_colors(doc) trước khi ghi xuống đĩa."""
    orig_save = doc.save

    def _safe_save(path_or_stream, *args, **kwargs):
        sanitize_docx_table_colors(doc)
        return orig_save(path_or_stream, *args, **kwargs)

    doc.save = _safe_save
    return doc


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENT SETUP
# ════════════════════════════════════════════════════════════════════════════

def new_document(template_path: Optional[str] = None) -> DocumentObject:
    """Tạo document mới chuẩn A4 và tự động gắn khóa bảo vệ sanitize_docx_table_colors(doc) khi save."""
    if template_path and os.path.exists(template_path):
        doc = Document(template_path)
    else:
        doc = Document()

    setup_page(doc)
    _attach_auto_sanitize_on_save(doc)
    return doc


def setup_page(doc: DocumentObject, top_cm: float = 2.0, bottom_cm: float = 2.0,
               left_cm: float = 3.0, right_cm: float = 1.8):
    for section in doc.sections:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.top_margin = Cm(top_cm)
        section.bottom_margin = Cm(bottom_cm)
        section.left_margin = Cm(left_cm)
        section.right_margin = Cm(right_cm)
    return doc


# ════════════════════════════════════════════════════════════════════════════
# TYPOGRAPHY & MATH HELPERS (RULE 12C — CLEAN TYPOGRAPHY & MATH LOCK)
# ════════════════════════════════════════════════════════════════════════════

MATH_SYMBOLS_MAP = {
    r'\implies': '⇒', r'\rightarrow': '→', r'\to': '→', r'\times': '×',
    r'\approx': '≈', r'\ge': '≥', r'\le': '≤', r'\leq': '≤', r'\geq': '≥',
    r'\neq': '≠', r'\pm': '±', r'\cdot': '·', r'\alpha': 'α', r'\beta': 'β',
    r'\gamma': 'γ', r'\delta': 'δ', r'\eta': 'η', r'\theta': 'θ', r'\lambda': 'λ',
    r'\mu': 'μ', r'\nu': 'ν', r'\rho': 'ρ', r'\sigma': 'σ', r'\tau': 'τ',
    r'\phi': 'ϕ', r'\omega': 'ω', r'\Delta': 'Δ', r'\Sigma': 'Σ', r'\Omega': 'Ω',
    r'\quad': ' ', r'\qquad': '  ', r'\,': ' ',
}


def clean_math_symbols(text: str) -> str:
    """Quy đổi các macro ký hiệu toán học LaTeX sang ký tự Unicode tương ứng."""
    res = text
    for k, v in MATH_SYMBOLS_MAP.items():
        res = res.replace(k, v)
    return res


def parse_inline_math_and_scripts(text: str):
    """
    Phân tách chuỗi văn bản thành danh sách tokens (content, token_type).
    token_type gồm:
      - 'normal': văn bản thông thường
      - 'sub': chỉ số dưới (subscript)
      - 'sup': chỉ số trên (superscript)
    Tự động khử sạch cú pháp raw LaTeX ($...$ hoặc $$...$$) và \\text{...}, \\mathrm{...}.
    """
    if not text:
        return []

    # 1. Khử bọc \\text{...}, \\mathrm{...}, \\mathbf{...} giữ nguyên nội dung bên trong
    text = re.sub(r'\\(?:text|mathrm|mathbf|boldsymbol)\{([^}]+)\}', r'\1', str(text))
    text = clean_math_symbols(text)

    # 2. Loại bỏ cặp dấu $ raw LaTeX
    text = re.sub(r'\$\$([^$]+)\$\$', r'\1', text)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)

    tokens = []
    # Khớp các mẫu chỉ số: base_sub hoặc base^sup (VD: H_max, H_{max}, f_{cd}, As_req, m^2, 10^5)
    pattern = re.compile(r'([A-Za-zα-ωΑ-ΩΔ0-9]+)([_^])(?:\{([^}]+)\}|([A-Za-z0-9,]+))')

    last_idx = 0
    for m in pattern.finditer(text):
        start, end = m.span()
        if start > last_idx:
            raw_chunk = text[last_idx:start].replace('}', '')
            if raw_chunk:
                tokens.append((raw_chunk, 'normal'))
        base = m.group(1)
        script_char = m.group(2)
        script_val = m.group(3) if m.group(3) is not None else m.group(4)

        tokens.append((base, 'normal'))
        if script_char == '_':
            tokens.append((script_val, 'sub'))
        else:
            tokens.append((script_val, 'sup'))
        last_idx = end

    if last_idx < len(text):
        raw_tail = text[last_idx:].replace('}', '')
        if raw_tail:
            tokens.append((raw_tail, 'normal'))

    return tokens


def add_formatted_runs_to_paragraph(p, text: str, size: float = 12.0,
                                    color: str = COLOR_TEXT_DARK,
                                    bold: bool = False, italic: bool = False,
                                    font_name: str = 'Times New Roman'):
    """
    Render chuỗi văn bản vào paragraph với hỗ trợ tự động định dạng subscript, superscript,
    khử bỏ $ raw LaTeX, và tô màu chuẩn cho các huy hiệu trạng thái [ĐẠT] / [KHÔNG ĐẠT].
    """
    if not text:
        return

    # Tách riêng các nhãn trạng thái kỹ thuật
    badge_pat = r'(\[(?:ĐẠT|KHÔNG ĐẠT|OK|PASSED|FAILED)\](?:\s*\([^\)]+\))?)'
    chunks = re.split(badge_pat, str(text))

    for chunk in chunks:
        if not chunk:
            continue
        if re.match(badge_pat, chunk):
            is_fail = any(k in chunk.upper() for k in ['KHÔNG ĐẠT', 'FAIL'])
            r = p.add_run(chunk)
            r.font.name = font_name
            r.font.size = Pt(size)
            r.bold = True
            r.italic = italic
            r.font.color.rgb = RGBColor.from_string(COLOR_CRITICAL if is_fail else COLOR_SUCCESS)
            continue

        # Phân giải toán học & chỉ số dưới/trên
        tokens = parse_inline_math_and_scripts(chunk)
        for val, kind in tokens:
            if not val:
                continue
            r = p.add_run(val)
            r.font.name = font_name
            r.font.size = Pt(size)
            r.bold = bold
            r.font.color.rgb = RGBColor.from_string(color)
            if kind == 'sub':
                r.font.subscript = True
                r.italic = italic or (len(val) <= 3 and val.isalpha())
            elif kind == 'sup':
                r.font.superscript = True
            else:
                r.italic = italic


# ════════════════════════════════════════════════════════════════════════════
# PARAGRAPH HELPERS
# ════════════════════════════════════════════════════════════════════════════

def pf(p, sb: float = 0, sa: float = 4, ls: float = 1.15):
    pf2 = p.paragraph_format
    pf2.space_before = Pt(sb)
    pf2.space_after = Pt(sa)
    pf2.line_spacing = ls
    pf2.line_spacing_rule = WD_LINE_SPACING.MULTIPLE


def add_h(doc, text: str, lv: int = 1, color: str = COLOR_PRIMARY,
          align=WD_ALIGN_PARAGRAPH.LEFT):
    h = doc.add_heading(text, level=lv)
    h.alignment = align
    for r in h.runs:
        r.font.color.rgb = RGBColor.from_string(color)
        r.font.bold = True
        if lv == 1:
            r.font.size = Pt(16)
        elif lv == 2:
            r.font.size = Pt(14)
        else:
            r.font.size = Pt(12)
    pf(h, sb=6 if lv == 1 else 4, sa=2)
    h.paragraph_format.keep_with_next = True
    return h


def add_p(doc, text: str, bold: bool = False, italic: bool = False,
          size: float = 13.0, color: str = COLOR_TEXT_DARK,
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, sa: float = 4,
          indent_cm: float = 0):
    p = doc.add_paragraph()
    p.alignment = align
    if indent_cm > 0:
        p.paragraph_format.left_indent = Cm(indent_cm)
    pf(p, sa=sa)
    if text:
        add_formatted_runs_to_paragraph(p, text, size=size, color=color, bold=bold, italic=italic)
    return p


def add_bullet(doc, text: str, bp: Optional[str] = None,
               size: float = 12.5, color: str = COLOR_PRIMARY,
               indent_cm: float = 0.6):
    """
    Thêm đoạn văn dạng Bullet (List Bullet).
    KHẮC PHỤC TRIỆT ĐỂ DOUBLE BULLET (Điều 12c AGENTS.md):
    - Tự động lstrip các ký tự `•`, `-`, `–`, `—`, `*` khỏi `bp` và `text`.
    - Tự động nhận diện nếu dữ liệu là danh sách đánh số/chữ cái (1., a)) để chuyển sang `add_item()`.
    """
    clean_text = str(text or "").lstrip("•-–—* \t")
    clean_bp = str(bp or "").lstrip("•-–—* \t") if bp else ""

    # Nếu text hoặc bp bắt đầu bằng đánh số (1., 2.) hoặc chữ cái (a), b)) -> Chuyển sang add_item
    enum_match = re.match(r"^(\d+[\.\)]|[a-zA-Z][\.\)])\s*(.*)$", clean_bp or clean_text)
    if enum_match:
        prefix_val = enum_match.group(1) + " "
        body_val = enum_match.group(2) if (clean_bp or clean_text).startswith(enum_match.group(1)) else clean_text
        return add_item(doc, body_val, prefix=prefix_val, size=size, color=color, indent_cm=indent_cm)

    p = doc.add_paragraph(style='List Bullet')
    pf(p, sa=2)
    p.paragraph_format.left_indent = Cm(indent_cm)
    if clean_bp:
        r1 = p.add_run(clean_bp)
        r1.bold = True
        r1.font.size = Pt(size)
        r1.font.color.rgb = RGBColor.from_string(color)
    if clean_text:
        add_formatted_runs_to_paragraph(p, clean_text, size=size, color=COLOR_TEXT_DARK)
    return p


def add_item(doc, text: str, prefix: str = "",
             size: float = 12.5, color: str = COLOR_TEXT_DARK,
             prefix_color: str = COLOR_PRIMARY,
             indent_cm: float = 0.6, first_line_indent_cm: float = -0.4,
             bold_prefix: bool = True):
    """
    Đoạn văn thụt đầu dòng dùng cho danh sách đánh số (1., 2.) hoặc chữ cái (a), b)).
    TUYỆT ĐỐI KHÔNG dùng style='List Bullet' để không bị dính dấu chấm tròn trước số.
    """
    p = doc.add_paragraph()
    pf(p, sa=2.5)
    p.paragraph_format.left_indent = Cm(indent_cm)
    if first_line_indent_cm != 0:
        p.paragraph_format.first_line_indent = Cm(first_line_indent_cm)

    clean_prefix = str(prefix or "").lstrip("•-–—* \t")
    clean_text = str(text or "").lstrip("•-–—* \t")

    if clean_prefix:
        r_pref = p.add_run(clean_prefix)
        r_pref.bold = bold_prefix
        r_pref.font.size = Pt(size)
        r_pref.font.color.rgb = RGBColor.from_string(prefix_color)

    if clean_text:
        add_formatted_runs_to_paragraph(p, clean_text, size=size, color=color)

    return p


def add_box(doc, text: str, bg: str = COLOR_WARN_BG,
            border_color: str = COLOR_WARN_BORDER,
            text_color: str = COLOR_TEXT_DARK):
    p = doc.add_paragraph()
    pf(p, sb=4, sa=4)
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.right_indent = Cm(0.4)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), bg)
    pPr.append(shd)
    r = p.add_run(text)
    r.font.size = Pt(11.0)
    r.font.italic = True
    r.font.color.rgb = RGBColor.from_string(text_color)
    return p


def add_callout(doc, text: str, kind: str = 'info'):
    style_map = {
        'info': {'bg': 'EDF3F5', 'border': COLOR_INFO, 'text': '1F4E5B'},
        'warn': {'bg': COLOR_WARN_BG, 'border': COLOR_WARN_BORDER, 'text': '8F5314'},
        'critical': {'bg': 'F9EBE8', 'border': COLOR_CRITICAL, 'text': '8C261E'},
        'success': {'bg': 'EBF3ED', 'border': COLOR_SUCCESS, 'text': '1E5631'},
    }
    s = style_map.get(kind, style_map['info'])
    return add_box(doc, text, bg=s['bg'], border_color=s['border'], text_color=s['text'])


# ════════════════════════════════════════════════════════════════════════════
# TABLE HELPERS (NATURAL PRINT PALETTE — ZERO WHITE TEXT)
# ════════════════════════════════════════════════════════════════════════════

def set_cell_bg(cell, hex_color: str):
    clean = str(hex_color or '').strip().lstrip('#').upper()
    if _hex_luma(clean) < 140.0:
        clean = COLOR_TABLE_HEADER_BG
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), clean)
    tcPr.append(shd)


def set_tbl_border(table, color: str = 'D0CEC7', size: int = 4):
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    tblB = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'), 'single')
        b.set(qn('w:sz'), '8' if side in ('top', 'bottom') else str(size))
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), COLOR_PRIMARY if side in ('top', 'bottom') else color)
        tblB.append(b)
    tblPr.append(tblB)


def build_table(doc, headers: List[str], rows: List[List[str]],
                col_widths_cm: Optional[List[float]] = None,
                header_bg: str = COLOR_TABLE_HEADER_BG,
                alt_row_bg: str = COLOR_ROW_ALT,
                header_text_color: str = COLOR_TABLE_HEADER_TEXT,
                body_size: float = 11.0,
                header_size: float = 11.5,
                align_data=WD_ALIGN_PARAGRAPH.LEFT,
                align_header=WD_ALIGN_PARAGRAPH.CENTER):
    """
    Build styled table chuẩn Natural Print Palette (Điều 12b AGENTS.md):
    - Header row: nền sáng #DCE4EC (hoặc #EAE6DF), chữ đậm #1E3246 (tự động chặn mọi mã FFFFFF).
    - Data rows: chữ tối #1C1E21, nền xen kẽ trắng và #F8F7F4.
    - Summary rows (bắt đầu bằng TỔNG / KẾT LUẬN / CỘNG): chữ đậm #1E3246, nền #F2EFE9.
    """
    if str(header_text_color).strip().lstrip('#').upper() == 'FFFFFF':
        header_text_color = COLOR_TABLE_HEADER_TEXT
    if _hex_luma(header_bg) < 140.0:
        header_bg = COLOR_TABLE_HEADER_BG

    n_cols = len(headers)
    t = doc.add_table(rows=1 + len(rows), cols=n_cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_tbl_border(t)

    header_tr = t.rows[0]._tr.get_or_add_trPr()
    header_tr.append(parse_xml(r'<w:tblHeader {}/>'.format(nsdecls('w'))))

    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ''
        set_cell_bg(cell, header_bg)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = align_header
        p.paragraph_format.keep_with_next = True
        pf(p, sb=1.5, sa=1.5)
        r = p.add_run(str(h))
        r.bold = True
        r.font.size = Pt(header_size)
        r.font.color.rgb = RGBColor.from_string(header_text_color)

    for i, row in enumerate(rows):
        trPr = t.rows[i + 1]._tr.get_or_add_trPr()
        trPr.append(parse_xml(r'<w:cantSplit {}/>'.format(nsdecls('w'))))
        first_val = str(row[0]).strip().upper() if row else ''
        is_sum = any(first_val.startswith(k) for k in ('TỔNG', 'KẾT LUẬN', 'CỘNG', 'TRUNG BÌNH'))

        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = ''
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if is_sum:
                set_cell_bg(cell, COLOR_LABEL_BG)
            elif i % 2 == 1:
                set_cell_bg(cell, alt_row_bg)
            p = cell.paragraphs[0]
            p.alignment = align_data
            pf(p, sb=1.0, sa=1.0)
            cell_color = COLOR_PRIMARY if is_sum else COLOR_TEXT_DARK
            add_formatted_runs_to_paragraph(p, str(val), size=body_size, color=cell_color, bold=is_sum)

    if col_widths_cm:
        for j, w in enumerate(col_widths_cm):
            for row in t.rows:
                row.cells[j].width = Cm(w)

    return t


# ════════════════════════════════════════════════════════════════════════════
# IMAGE & LANDSCAPE MS PROJECT GANTT EMBEDDING HELPERS (ĐẶC TÍNH 8)
# ════════════════════════════════════════════════════════════════════════════

def add_img(doc, path: str, w: float = 16.0, caption: Optional[str] = None):
    if not os.path.exists(path):
        return add_p(
            doc, f'[Ảnh không tìm thấy: {path}]',
            italic=True, color=COLOR_CRITICAL, size=10
        )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=4, sa=2)
    p.add_run().add_picture(path, width=Cm(w))
    if caption:
        return add_image_caption(doc, caption)
    return p


def add_image_centered(doc, img_path: str, width_cm: float = 15.0,
                       caption: Optional[str] = None):
    return add_img(doc, img_path, w=width_cm, caption=caption)


def add_image_caption(doc, caption: str, color: str = COLOR_TEXT_MED):
    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(cp, sb=0, sa=8)
    for r in cp.runs:
        r.font.size = Pt(10.5)
        r.font.italic = True
        r.font.color.rgb = RGBColor.from_string(color)
    return cp


def add_landscape_gantt_section(
    doc: DocumentObject,
    image_path: str,
    section_title: str = "BIỂU ĐỒ TIẾN ĐỘ TỔNG THỂ DỰ ÁN (CHUẨN MICROSOFT PROJECT — 300 DPI)",
    caption: str = "Hình: Biểu đồ Tiến độ Tổng thể (Split View: Bảng WBS 8 Cột & Biểu đồ Đường găng CPM chuẩn Microsoft Project)",
    width_cm: float = 25.4,
    restore_portrait: bool = True,
) -> DocumentObject:
    """
    [ĐẶC TÍNH 8] CƠ CHẾ NHÚNG THÔNG MINH VÀO VĂN BẢN WORD (.DOCX):
    - Tự động tạo Section Break ngắt sang 01 trang A4 Xoay Ngang (Landscape: 29.7 cm x 21.0 cm) riêng biệt.
    - Nhúng biểu đồ MS Project độ phân giải 300 DPI với chiều rộng 25.4 cm (sắc nét 100%, không bị co rúm chữ).
    - Tự động tạo Section Break trả về khổ A4 Dọc (Portrait: 21.0 cm x 29.7 cm) cho các trang nội dung còn lại.
    """
    sec_land = doc.add_section(WD_SECTION.NEW_PAGE)
    sec_land.orientation = WD_ORIENT.LANDSCAPE
    sec_land.page_width = Cm(29.7)
    sec_land.page_height = Cm(21.0)
    sec_land.top_margin = Cm(1.5)
    sec_land.bottom_margin = Cm(1.5)
    sec_land.left_margin = Cm(2.0)
    sec_land.right_margin = Cm(2.0)

    if section_title:
        p_t = doc.add_paragraph()
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p_t, sb=0, sa=4)
        p_t.paragraph_format.keep_with_next = True
        r_t = p_t.add_run(section_title)
        r_t.bold = True
        r_t.font.name = "Times New Roman"
        r_t.font.size = Pt(13)
        r_t.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

    if os.path.exists(image_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p_img, sb=2, sa=2)
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(image_path, width=Cm(width_cm))
    else:
        add_p(doc, f"[Không tìm thấy tệp biểu đồ tiến độ: {image_path}]", italic=True, color=COLOR_CRITICAL)

    if caption:
        add_image_caption(doc, caption)

    if restore_portrait:
        sec_port = doc.add_section(WD_SECTION.NEW_PAGE)
        sec_port.orientation = WD_ORIENT.PORTRAIT
        sec_port.page_width = Cm(21.0)
        sec_port.page_height = Cm(29.7)
        sec_port.top_margin = Cm(2.0)
        sec_port.bottom_margin = Cm(2.0)
        sec_port.left_margin = Cm(3.0)
        sec_port.right_margin = Cm(1.8)

    return doc


# ════════════════════════════════════════════════════════════════════════════
# HEADER & FOOTER
# ════════════════════════════════════════════════════════════════════════════

def add_header_footer(doc, project_name: str = '', report_title: str = '',
                      page_numbers: bool = True):
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        for p in list(header.paragraphs):
            p.clear()
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if project_name:
            r = hp.add_run(project_name)
            r.font.size = Pt(10.5)
            r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)
            r.bold = True
        if report_title:
            r2 = hp.add_run(f' | {report_title}')
            r2.font.size = Pt(10.0)
            r2.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)

        footer = section.footer
        footer.is_linked_to_previous = False
        for p in list(footer.paragraphs):
            p.clear()
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if page_numbers:
            r = fp.add_run('Trang ')
            r.font.size = Pt(10.5)
            r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)
            _add_page_field(fp)
            r = fp.add_run(' / ')
            r.font.size = Pt(10.5)
            r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)
            _add_total_pages_field(fp)

    return doc


def _add_page_field(paragraph):
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run.font.size = Pt(10.0)


def _add_total_pages_field(paragraph):
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'NUMPAGES'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run.font.size = Pt(10.0)


def add_cover_page(doc, project_name: str, report_title: str,
                   subtitle: str = '', author: str = '', date_str: str = '',
                   version: str = 'v1.0', logo_path: Optional[str] = None):
    if logo_path and os.path.exists(logo_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p, sb=20, sa=4)
        p.add_run().add_picture(logo_path, width=Cm(4.0))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=36, sa=4)
    r = p.add_run(project_name.upper())
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(COLOR_ACCENT)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=2, sa=8)
    r = p.add_run('─' * 30)
    r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=4, sa=4)
    r = p.add_run(report_title)
    r.font.size = Pt(24)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

    if subtitle:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p, sb=2, sa=24)
        r = p.add_run(subtitle)
        r.font.size = Pt(13)
        r.italic = True
        r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)

    info_table = doc.add_table(rows=3, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False

    info = [
        ('Người thực hiện:', author or 'AI Structural Engineer'),
        ('Phiên bản:', version),
        ('Ngày:', date_str or '—'),
    ]
    for i, (label, value) in enumerate(info):
        c1 = info_table.rows[i].cells[0]
        c1.text = ''
        set_cell_bg(c1, COLOR_LABEL_BG)
        p = c1.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(label)
        r.font.size = Pt(10.5)
        r.bold = True
        r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

        c2 = info_table.rows[i].cells[1]
        c2.text = ''
        p = c2.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(value)
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_DARK)

    doc.add_page_break()
    return doc


def add_toc(doc, title: str = 'MỤC LỤC'):
    add_h(doc, title, lv=1)
    p = doc.add_paragraph()
    pf(p, sb=4, sa=4)
    run = p.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = r'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t')
    t.text = 'Click chuột phải → Update Field để cập nhật Mục lục.'
    fldChar2.append(t)
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)
    doc.add_page_break()
    return doc
