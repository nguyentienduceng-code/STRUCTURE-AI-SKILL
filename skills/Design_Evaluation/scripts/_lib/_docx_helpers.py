"""
_docx_helpers.py — Shared DOCX utilities cho tất cả generators.

Gom các helpers đang bị duplicate trong:
- generate_ncr_ke_buy_dung.py
- generate_tham_da_docx.py
- generate_ke_pi_gieng_docx.py
- generate_bao_cao_bo_ke.py

Cung cấp:
- Paragraph helpers (add_h, add_p, pf, add_bullet)
- Table helpers (set_cell_bg, set_tbl_border, build_table, style_table)
- Image helpers (add_img, add_image_centered)
- Special blocks (add_box, add_callout)
- Document setup (new_document, setup_page, add_cover_page, add_toc)
- Header/Footer (add_header_footer, page_number)

Usage:
    from _lib._docx_helpers import new_document, add_h, add_p, build_table

Updated: 2026-08-31 — Phase A of Reporting Upgrade v4.0
"""

import os
from typing import List, Optional, Tuple, Union

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.document import Document as DocumentObject


# ════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE — Standardized theo corporate branding
# ════════════════════════════════════════════════════════════════════════════

# Primary navy (headings, borders, table headers)
COLOR_PRIMARY = '1C3557'
# Accent blue (subheadings, links)
COLOR_ACCENT = '2980B9'
# Text dark
COLOR_TEXT_DARK = '222222'
# Text medium
COLOR_TEXT_MED = '555555'
# Alt row background (zebra striping)
COLOR_ROW_ALT = 'DDE8F5'
# Warning yellow background
COLOR_WARN_BG = 'FFF9C4'
# Warning yellow border
COLOR_WARN_BORDER = 'CC8800'
# Critical red
COLOR_CRITICAL = 'C0392B'
# Success green
COLOR_SUCCESS = '27AE60'
# Info cyan
COLOR_INFO = '3498DB'


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENT SETUP
# ════════════════════════════════════════════════════════════════════════════

def new_document(template_path: Optional[str] = None) -> DocumentObject:
    """
    Tạo document mới. Nếu có template, copy từ template.
    Setup default A4, margins theo NĐ 30/2020 (3cm L/R, 2cm T/B).
    """
    if template_path and os.path.exists(template_path):
        doc = Document(template_path)
    else:
        doc = Document()

    setup_page(doc)
    return doc


def setup_page(doc: DocumentObject, top_cm: float = 2.0, bottom_cm: float = 2.0,
               left_cm: float = 3.0, right_cm: float = 3.0):
    """
    Setup page A4 với margins chuẩn NĐ 30/2020/NĐ-CP:
    - Lề trên: 2 cm
    - Lề dưới: 2 cm
    - Lề trái: 3 cm
    - Lề phải: 2 cm (mặc định) hoặc 3 cm (nếu inán)
    """
    for section in doc.sections:
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.top_margin = Cm(top_cm)
        section.bottom_margin = Cm(bottom_cm)
        section.left_margin = Cm(left_cm)
        section.right_margin = Cm(right_cm)
    return doc


# ════════════════════════════════════════════════════════════════════════════
# PARAGRAPH HELPERS
# ════════════════════════════════════════════════════════════════════════════

def pf(p, sb: float = 0, sa: float = 4, ls: float = 1.15):
    """Set paragraph format: space_before, space_after, line_spacing."""
    pf2 = p.paragraph_format
    pf2.space_before = Pt(sb)
    pf2.space_after = Pt(sa)
    pf2.line_spacing = ls
    pf2.line_spacing_rule = WD_LINE_SPACING.MULTIPLE


def add_h(doc, text: str, lv: int = 1, color: str = COLOR_PRIMARY,
          align=WD_ALIGN_PARAGRAPH.LEFT):
    """
    Add heading với style chuẩn.
    Level 1: 16pt bold, màu primary
    Level 2: 14pt bold, màu primary
    Level 3: 12pt bold, màu accent
    """
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
    pf(h, sb=10 if lv == 1 else 6, sa=4)
    h.paragraph_format.keep_with_next = True
    return h


def add_p(doc, text: str, bold: bool = False, italic: bool = False,
          size: float = 10.5, color: str = COLOR_TEXT_DARK,
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, sa: float = 4,
          indent_cm: float = 0):
    """Add paragraph với format chuẩn."""
    p = doc.add_paragraph()
    p.alignment = align
    if indent_cm > 0:
        p.paragraph_format.left_indent = Cm(indent_cm)
    pf(p, sa=sa)
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor.from_string(color)
    return p


def add_bullet(doc, text: str, bp: Optional[str] = None,
               size: float = 10, color: str = COLOR_PRIMARY,
               indent_cm: float = 0.6):
    """Add bullet point, optionally với bold prefix."""
    p = doc.add_paragraph(style='List Bullet')
    pf(p, sa=2)
    p.paragraph_format.left_indent = Cm(indent_cm)
    if bp:
        r1 = p.add_run(bp)
        r1.bold = True
        r1.font.size = Pt(size)
        r1.font.color.rgb = RGBColor.from_string(color)
        r2 = p.add_run(text)
        r2.font.size = Pt(size)
    else:
        r = p.add_run(text)
        r.font.size = Pt(size)
    return p


def add_box(doc, text: str, bg: str = COLOR_WARN_BG,
            border_color: str = COLOR_WARN_BORDER,
            text_color: str = '333333'):
    """Add highlighted box (callout) với background color."""
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
    r.font.size = Pt(10)
    r.font.italic = True
    r.font.color.rgb = RGBColor.from_string(text_color)
    return p


def add_callout(doc, text: str, kind: str = 'info'):
    """
    Add colored callout box.
    kind: 'info' (cyan), 'warn' (yellow), 'critical' (red), 'success' (green)
    """
    style_map = {
        'info':     {'bg': 'D6EAF8', 'border': '3498DB', 'text': '1B4F72'},
        'warn':     {'bg': COLOR_WARN_BG, 'border': COLOR_WARN_BORDER, 'text': '7D6608'},
        'critical': {'bg': 'F5B7B1', 'border': COLOR_CRITICAL, 'text': '78281F'},
        'success':  {'bg': 'D5F5E3', 'border': COLOR_SUCCESS, 'text': '196F3D'},
    }
    s = style_map.get(kind, style_map['info'])
    return add_box(doc, text, bg=s['bg'], border_color=s['border'], text_color=s['text'])


# ════════════════════════════════════════════════════════════════════════════
# TABLE HELPERS
# ════════════════════════════════════════════════════════════════════════════

def set_cell_bg(cell, hex_color: str):
    """Set background color cho 1 cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_tbl_border(table, color: str = COLOR_PRIMARY, size: int = 6):
    """Set borders cho toàn bộ table."""
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    tblB = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'), 'single')
        b.set(qn('w:sz'), str(size))
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), color)
        tblB.append(b)
    tblPr.append(tblB)


def build_table(doc, headers: List[str], rows: List[List[str]],
                col_widths_cm: Optional[List[float]] = None,
                header_bg: str = COLOR_PRIMARY,
                alt_row_bg: str = COLOR_ROW_ALT,
                header_text_color: str = 'FFFFFF',
                body_size: float = 9.5,
                header_size: float = 10,
                align_data=WD_ALIGN_PARAGRAPH.LEFT,
                align_header=WD_ALIGN_PARAGRAPH.CENTER):
    """
    Build styled table với:
    - Header row (bold, colored background, white text)
    - Alternating row background (zebra striping)
    - Borders
    - Custom column widths (optional)
    """
    n_cols = len(headers)
    t = doc.add_table(rows=1 + len(rows), cols=n_cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_tbl_border(t)

    # Header row
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ''
        set_cell_bg(cell, header_bg)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = align_header
        pf(p, sb=2, sa=2)
        r = p.add_run(str(h))
        r.bold = True
        r.font.size = Pt(header_size)
        r.font.color.rgb = RGBColor.from_string(header_text_color)

    # Data rows
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = ''
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            # Zebra striping
            if i % 2 == 1:
                set_cell_bg(cell, alt_row_bg)
            p = cell.paragraphs[0]
            p.alignment = align_data
            pf(p, sb=1, sa=1)
            r = p.add_run(str(val))
            r.font.size = Pt(body_size)
            r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_DARK)

    # Column widths
    if col_widths_cm:
        for j, w in enumerate(col_widths_cm):
            for row in t.rows:
                row.cells[j].width = Cm(w)

    return t


# ════════════════════════════════════════════════════════════════════════════
# IMAGE HELPERS
# ════════════════════════════════════════════════════════════════════════════

def add_img(doc, path: str, w: float = 16.0, caption: Optional[str] = None):
    """
    Add image centered với optional caption.
    Nếu file không tồn tại, in error message thay vì crash.
    """
    if not os.path.exists(path):
        return add_p(
            doc, f'[Ảnh không tìm thấy: {path}]',
            italic=True, color=COLOR_CRITICAL, size=9
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
    """Alias cho add_img với width_cm."""
    return add_img(doc, img_path, w=width_cm, caption=caption)


def add_image_caption(doc, caption: str, color: str = COLOR_TEXT_MED):
    """Add italic caption dưới ảnh."""
    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(cp, sb=0, sa=8)
    for r in cp.runs:
        r.font.size = Pt(9)
        r.font.italic = True
        r.font.color.rgb = RGBColor.from_string(color)
    return cp


# ════════════════════════════════════════════════════════════════════════════
# HEADER & FOOTER
# ════════════════════════════════════════════════════════════════════════════

def add_header_footer(doc, project_name: str = '', report_title: str = '',
                      page_numbers: bool = True):
    """
    Add header (project name + report title) và footer (page X/Y).
    Áp dụng cho TẤT CẢ sections.
    """
    for section in doc.sections:
        # Header
        header = section.header
        header.is_linked_to_previous = False
        # Clear existing paragraphs
        for p in list(header.paragraphs):
            p.clear()
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if project_name:
            r = hp.add_run(project_name)
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)
            r.bold = True
        if report_title:
            r2 = hp.add_run(f'  |  {report_title}')
            r2.font.size = Pt(9)
            r2.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)

        # Footer với page numbers
        footer = section.footer
        footer.is_linked_to_previous = False
        for p in list(footer.paragraphs):
            p.clear()
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if page_numbers:
            # Trang X / Y
            r = fp.add_run('Trang ')
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)
            _add_page_field(fp)
            r = fp.add_run(' / ')
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)
            _add_total_pages_field(fp)

    return doc


def _add_page_field(paragraph):
    """Insert PAGE field code vào paragraph."""
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
    run.font.size = Pt(9)


def _add_total_pages_field(paragraph):
    """Insert NUMPAGES field code vào paragraph."""
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
    run.font.size = Pt(9)


# ════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════════════════════

def add_cover_page(doc, project_name: str, report_title: str,
                   subtitle: str = '', author: str = '', date_str: str = '',
                   version: str = 'v1.0', logo_path: Optional[str] = None):
    """
    Add professional cover page.
    Layout:
    - Top: logo (optional) + spacer
    - Center: project name, report title, subtitle
    - Bottom: author, version, date
    """
    # Logo (top, centered)
    if logo_path and os.path.exists(logo_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p, sb=20, sa=10)
        p.add_run().add_picture(logo_path, width=Cm(4.0))

    # Spacer
    for _ in range(4):
        doc.add_paragraph()

    # Project name
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=4, sa=4)
    r = p.add_run(project_name.upper())
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(COLOR_ACCENT)

    # Title divider
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=2, sa=8)
    r = p.add_run('─' * 30)
    r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

    # Report title
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf(p, sb=4, sa=4)
    r = p.add_run(report_title)
    r.font.size = Pt(24)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)

    # Subtitle
    if subtitle:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf(p, sb=2, sa=12)
        r = p.add_run(subtitle)
        r.font.size = Pt(13)
        r.italic = True
        r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_MED)

    # Spacer
    for _ in range(8):
        doc.add_paragraph()

    # Bottom info
    info_table = doc.add_table(rows=3, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False

    info = [
        ('Người thực hiện:', author or 'AI Structural Engineer'),
        ('Phiên bản:', version),
        ('Ngày:', date_str or '—'),
    ]
    for i, (label, value) in enumerate(info):
        # Label cell
        c1 = info_table.rows[i].cells[0]
        c1.text = ''
        p = c1.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(label)
        r.font.size = Pt(10)
        r.bold = True
        r.font.color.rgb = RGBColor.from_string(COLOR_PRIMARY)
        # Value cell
        c2 = info_table.rows[i].cells[1]
        c2.text = ''
        p = c2.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(value)
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor.from_string(COLOR_TEXT_DARK)

    # Page break
    doc.add_page_break()
    return doc


# ════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (TOC)
# ════════════════════════════════════════════════════════════════════════════

def add_toc(doc, title: str = 'MỤC LỤC'):
    """
    Add Table of Contents (TOC).
    Word sẽ tự động update khi mở file.
    Yêu cầu: Heading 1, 2, 3 đã được dùng trong document.
    """
    add_h(doc, title, lv=1)

    p = doc.add_paragraph()
    pf(p, sb=4, sa=4)
    run = p.add_run()

    # Insert TOC field
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = r'TOC \o "1-3" \h \z \u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')

    # Placeholder text (Word sẽ replace)
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