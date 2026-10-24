#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX GENERATOR V2.0 — BỘ ENGINE XUẤT HỒ SƠ THUYẾT MINH TÍNH TOÁN KẾT CẤU & ĐỊA KỸ THUẬT
Hỗ trợ lựa chọn 2 Bộ Chuẩn Trình Bày & Bố Trí Chapter trích xuất từ `THUYET MINH MAU`:
  1. `--style bktechs` : BỘ CHUẨN 1 — Phong cách BKTECHS (Viện - Trường / Thẩm tra / TMTT Chuyên sâu)
  2. `--style tvtk`    : BỘ CHUẨN 2 — Phong cách TVTK Đa Hạng Mục (9 Chương Cơ sở Chung + N Chương Phụ lục Hạng mục)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import html
import os
import re
import zipfile
import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor


# ==============================================================================
# CẤU HÌNH ĐỊNH DẠNG CHO 2 BỘ CHUẨN (BKTECHS vs TVTK ĐA HẠNG MỤC)
# ==============================================================================
STYLE_CONFIGS = {
    "bktechs": {
        "name": "BỘ CHUẨN 1 — PHONG CÁCH BKTECHS (VIỆN - TRƯỜNG / CHUYÊN SÂU)",
        "font_family": "Times New Roman",
        "body_size": 12,
        "h1_size": 14,
        "h2_size": 13,
        "h3_size": 12,
        "table_size": 10,
        "h1_color": RGBColor(0x00, 0x20, 0x60),      # Xanh Navy đậm (#002060)
        "h2_color": RGBColor(0x00, 0x70, 0xC0),      # Xanh Lam sáng (#0070C0)
        "h3_color": RGBColor(0x1F, 0x4E, 0x79),      # Xanh đậm (#1F4E79)
        "body_color": RGBColor(0x1A, 0x1A, 0x1A),
        "table_header_fill": "002060",               # Nền xanh Navy đậm, chữ trắng
        "table_header_text": RGBColor(0xFF, 0xFF, 0xFF),
        "table_alt_fill": "F2F5F9",
        "table_highlight_fill": "FFF2CC",            # Vàng nhạt cho dòng Kiểm tra / Kết luận
        "dot_after_number": True,                    # 1. / 1.1. / 1.1.1.
    },
    "tvtk": {
        "name": "BỘ CHUẨN 2 — PHONG CÁCH TVTK ĐA HẠNG MỤC (TKKT / BVTC TỔNG HỢP)",
        "font_family": "Arial",
        "body_size": 11,
        "h1_size": 13,
        "h2_size": 11.5,
        "h3_size": 11,
        "table_size": 10,
        "h1_color": RGBColor(0x00, 0x20, 0x60),      # Xanh đậm (#002060)
        "h2_color": RGBColor(0x00, 0x70, 0xC0),      # Xanh lam (#0070C0)
        "h3_color": RGBColor(0x1F, 0x4E, 0x79),
        "body_color": RGBColor(0x1A, 0x1A, 0x1A),
        "table_header_fill": "B4C6E7",               # Nền xanh lam nhạt chuẩn mẫu ICP/Hà Tiên
        "table_header_text": RGBColor(0x00, 0x00, 0x00),
        "table_alt_fill": "F9FAFC",
        "table_highlight_fill": "E2EFDA",            # Xanh lá nhạt cho dòng Đạt / OK
        "dot_after_number": False,                   # 1 / 1.1 / 1.1.1
    },
}


# ==============================================================================
# CÁC HÀM TIỆN ÍCH OPENXML (BORDERS, SHADING, PAGE FIELDS, TOC)
# ==============================================================================
def set_cell_shading(cell, color_hex: str):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="BFBFBF", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def set_paragraph_bottom_border(paragraph, color_hex="FFC000", sz="12", val="single"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="4" w:color="{color_hex}"/>'
        f"</w:pBdr>"
    )
    pPr.append(pBdr)


def set_paragraph_top_border(paragraph, color_hex="BFBFBF", sz="6", val="single"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="4" w:color="{color_hex}"/>'
        f"</w:pBdr>"
    )
    pPr.append(pBdr)


def set_paragraph_left_border(paragraph, color_hex="002060", sz="18", val="single"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="8" w:color="{color_hex}"/>'
        f"</w:pBdr>"
    )
    pPr.append(pBdr)


def set_paragraph_shading(paragraph, color_hex="F2F5F9"):
    pPr = paragraph._p.get_or_add_pPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    pPr.append(shd)


def normalize_engineering_symbols(text: str) -> str:
    """
    Chuẩn hóa các ký hiệu kỹ thuật, toán học và xây dựng hay dùng trong thuyết minh:
    - Đường kính thép: %%c, Phi, phi, fi trước số -> Φ (VD: Phi 20 -> Φ20, %%c16 -> Φ16)
    - So sánh: <=, =< -> ≤; >=, => -> ≥; +- -> ±
    - Đơn vị mũ: m2 -> m², m3 -> m³, mm2 -> mm², cm2 -> cm², kN/m2 -> kN/m², daN/cm2 -> daN/cm², kNm -> kN.m
    - Ký tự Hy Lạp: eta -> η, sigma -> σ, tau -> τ, gamma -> γ, alpha -> α, beta -> β, delta -> δ, Delta -> Δ
    - Phép nhân kích thước: 200x400 -> 200 × 400, 200*400 -> 200 × 400
    - Trạng thái kiểm tra: [OK], [DAT] -> [ĐẠT], [FAIL] -> [KHÔNG ĐẠT]
    """
    if not text:
        return text

    # Thay thế đường kính thép: %%c, Phi, phi, fi (VD: Phi 20, phi18, %%c16, fi 12)
    text = re.sub(r'(?:%%c|[Pp]hi|fi)\s*([0-9]+(?:\.[0-9]+)?)', r'Φ\1', text)

    # Toán học & so sánh
    text = re.sub(r'<=\s*', '≤ ', text)
    text = re.sub(r'>=\s*', '≥ ', text)
    text = re.sub(r'\+-\s*', '±', text)
    text = re.sub(r'\\le\b', '≤', text)
    text = re.sub(r'\\ge\b', '≥', text)
    text = re.sub(r'\\pm\b', '±', text)
    text = re.sub(r'\\times\b', '×', text)

    # Đơn vị kỹ thuật xây dựng
    text = re.sub(r'(\d+)\s*kN/?m2\b', r'\1 kN/m²', text)
    text = re.sub(r'\bkN/?m2\b', 'kN/m²', text)
    text = re.sub(r'(\d+)\s*daN/?cm2\b', r'\1 daN/cm²', text)
    text = re.sub(r'\bdaN/?cm2\b', 'daN/cm²', text)
    text = re.sub(r'(\d+)\s*kNm/m\b', r'\1 kN.m/m', text)
    text = re.sub(r'\bkNm/m\b', 'kN.m/m', text)
    text = re.sub(r'(\d+)\s*kNm\b', r'\1 kN.m', text)
    text = re.sub(r'\bkNm\b', 'kN.m', text)
    text = re.sub(r'(\d+)\s*m2\b', r'\1 m²', text)
    text = re.sub(r'(\d+)\s*m3\b', r'\1 m³', text)
    text = re.sub(r'(\d+)\s*mm2\b', r'\1 mm²', text)
    text = re.sub(r'(\d+)\s*cm2\b', r'\1 cm²', text)
    text = re.sub(r'(\d+)\s*mm3\b', r'\1 mm³', text)
    text = re.sub(r'(\d+)\s*cm3\b', r'\1 cm³', text)

    # Kích thước tiết diện: 200x400 hoặc 200*400 -> 200 × 400
    text = re.sub(r'(\d+)\s*[xX]\s*(\d+)', r'\1 × \2', text)
    text = re.sub(r'(\d+)\s*\*\s*(\d+)', r'\1 × \2', text)

    # Góc / độ: 30 do C, 30^o, 30 \circ
    text = re.sub(r'(\d+)\s*(?:độ|\^o|\\circ)\s*C\b', r'\1°C', text)
    text = re.sub(r'(\d+)\s*(?:độ|\^o|\\circ)\b', r'\1°', text)

    # Ký hiệu thẻ sub / sup trong markdown nếu có
    text = re.sub(r'<sup>2</sup>', '²', text)
    text = re.sub(r'<sup>3</sup>', '³', text)
    text = re.sub(r'<sup>(.*?)</sup>', r'^\1', text)
    text = re.sub(r'<sub>(.*?)</sub>', r'_\1', text)

    # Ký tự Hy Lạp thường dùng trong thuyết minh
    greek_replacements = [
        (r'\b[Ee]ta\b', 'η'),
        (r'\b[Ee]ta_([A-Za-z0-9_]+)', r'η_\1'),
        (r'\b[Ss]igma\b', 'σ'),
        (r'\b[Tt]au\b', 'τ'),
        (r'\b[Gg]amma\b', 'γ'),
        (r'\b[Aa]lpha\b', 'α'),
        (r'\b[Bb]eta\b', 'β'),
        (r'\b[Dd]elta\b', 'δ'),
        (r'\b[Dd]elta_([A-Za-z0-9_]+)', r'δ_\1'),
        (r'\bphi\s*=', 'φ ='),
        (r'\\eta\b', 'η'),
        (r'\\sigma\b', 'σ'),
        (r'\\tau\b', 'τ'),
        (r'\\gamma\b', 'γ'),
        (r'\\alpha\b', 'α'),
        (r'\\beta\b', 'β'),
        (r'\\delta\b', 'δ'),
        (r'\\Delta\b', 'Δ'),
        (r'\\phi\b', 'φ'),
        (r'\\Phi\b', 'Φ'),
    ]
    for pattern, rep in greek_replacements:
        text = re.sub(pattern, rep, text)

    # Chuẩn hóa trạng thái kiểm tra
    text = re.sub(r'\[(?:OK|DAT|ĐẠT)\]', '[ĐẠT]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:FAIL|FAILED|KHONG DAT|KHÔNG ĐẠT)\]', '[KHÔNG ĐẠT]', text, flags=re.IGNORECASE)

    return text


# ==============================================================================
# BỘ CHUYỂN ĐỔI CÔNG THỨC TOÁN LATEX SANG NATIVE WORD OMML (OFFICE MATH XML)
# ==============================================================================
try:
    from pylatexenc.latexwalker import (
        LatexWalker,
        LatexCharsNode,
        LatexMacroNode,
        LatexGroupNode,
        LatexMathNode,
    )
    HAS_PYLATEXENC = True
except ImportError:
    HAS_PYLATEXENC = False

GREEK_AND_MATH_SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ",
    "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν",
    "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "Sigma": "Σ",
    "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ", "Phi": "Φ",
    "chi": "χ", "psi": "ψ", "omega": "ω", "Omega": "Ω",
    "cdot": "·", "times": "×", "div": "÷", "pm": "±", "mp": "∓",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠",
    "approx": "≈", "equiv": "≡", "sim": "∼", "infty": "∞",
    "sum": "∑", "prod": "∏", "int": "∫", "partial": "∂",
    "degree": "°", "circ": "°", "prime": "′",
}


def _node_to_omml(node) -> str:
    if isinstance(node, LatexCharsNode):
        return _chars_to_omml(node.chars)
    elif isinstance(node, (LatexGroupNode, LatexMathNode)):
        return "".join(_node_to_omml(n) for n in node.nodelist)
    elif isinstance(node, LatexMacroNode):
        mname = node.macroname
        if mname in ("text", "mathrm", "operatorname", "mbox"):
            text_val = ""
            if node.nodeargd and node.nodeargd.argnlist:
                arg0 = node.nodeargd.argnlist[0]
                text_val = "".join(_node_to_omml(n) for n in getattr(arg0, "nodelist", []))
            return f'<m:r><m:rPr><m:nor/></m:rPr><m:t>{text_val}</m:t></m:r>'
        elif mname == "frac":
            args = node.nodeargd.argnlist if node.nodeargd else []
            num_omml = "".join(_node_to_omml(n) for n in getattr(args[0], "nodelist", [])) if len(args) > 0 else ""
            den_omml = "".join(_node_to_omml(n) for n in getattr(args[1], "nodelist", [])) if len(args) > 1 else ""
            return f'<m:f><m:num>{num_omml}</m:num><m:den>{den_omml}</m:den></m:f>'
        elif mname == "sqrt":
            args = node.nodeargd.argnlist if node.nodeargd else []
            body_omml = "".join(_node_to_omml(n) for n in getattr(args[-1], "nodelist", [])) if args else ""
            return f'<m:rad><m:radPr><m:degHide/></m:radPr><m:e>{body_omml}</m:e></m:rad>'
        elif mname in GREEK_AND_MATH_SYMBOLS:
            sym = GREEK_AND_MATH_SYMBOLS[mname]
            return f'<m:r><m:t>{sym}</m:t></m:r>'
        elif mname in ("left", "right"):
            return ""
        else:
            return f'<m:r><m:t>{mname}</m:t></m:r>'
    return ""


def _chars_to_omml(chars: str) -> str:
    chars = chars.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if "_" not in chars and "^" not in chars:
        return f'<m:r><m:t>{chars}</m:t></m:r>'

    # Hỗ trợ cả ký tự Latin, số và ký tự Hy Lạp Unicode
    tokens = re.split(r'([A-Za-z0-9\u0370-\u03ff]+(?:_[A-Za-z0-9\u0370-\u03ff]+)?(?:\^[A-Za-z0-9\u0370-\u03ff]+)?)', chars)
    res = []
    for t in tokens:
        if not t:
            continue
        m_subsup = re.match(r'^([A-Za-z0-9\u0370-\u03ff]+)_([A-Za-z0-9\u0370-\u03ff]+)\^([A-Za-z0-9\u0370-\u03ff]+)$', t)
        m_sub = re.match(r'^([A-Za-z0-9\u0370-\u03ff]+)_([A-Za-z0-9\u0370-\u03ff]+)$', t)
        m_sup = re.match(r'^([A-Za-z0-9\u0370-\u03ff]+)\^([A-Za-z0-9\u0370-\u03ff]+)$', t)
        if m_subsup:
            b, s, p = m_subsup.groups()
            res.append(f'<m:sSubSup><m:e><m:r><m:t>{b}</m:t></m:r></m:e><m:sub><m:r><m:t>{s}</m:t></m:r></m:sub><m:sup><m:r><m:t>{p}</m:t></m:r></m:sup></m:sSubSup>')
        elif m_sub:
            b, s = m_sub.groups()
            res.append(f'<m:sSub><m:e><m:r><m:t>{b}</m:t></m:r></m:e><m:sub><m:r><m:t>{s}</m:t></m:r></m:sub></m:sSub>')
        elif m_sup:
            b, p = m_sup.groups()
            res.append(f'<m:sSup><m:e><m:r><m:t>{b}</m:t></m:r></m:e><m:sup><m:r><m:t>{p}</m:t></m:r></m:sup></m:sSup>')
        else:
            clean_t = t.replace("_", "").replace("^", "")
            res.append(f'<m:r><m:t>{clean_t}</m:t></m:r>')
    return "".join(res)


def latex_to_omml(latex_code: str):
    """Chuyển đổi công thức LaTeX ($...$ hoặc $$...$$) sang chuỗi OpenXML OMML hoàn chỉnh."""
    if not HAS_PYLATEXENC or not latex_code:
        return None
    code = latex_code.strip()
    if code.startswith("$$") and code.endswith("$$") and len(code) >= 4:
        code = code[2:-2].strip()
    elif code.startswith("$") and code.endswith("$") and len(code) >= 2:
        code = code[1:-1].strip()

    # Pre-processing để hỗ trợ tối đa các công thức thực tế trong hồ sơ kết cấu:
    # 1. R_{bt}, \sigma_{bt}, A_{s}, \eta_{max} -> chuẩn hóa _{...} và ^{...}
    code = re.sub(r'_\{([A-Za-z0-9\.\,]+)\}', r'_\1', code)
    code = re.sub(r'\^\{([A-Za-z0-9\.\,]+)\}', r'^\1', code)

    # 2. Thay thế ký tự Hy Lạp đứng trước _ hoặc ^ thành ký tự Unicode trực tiếp
    for k, v in GREEK_AND_MATH_SYMBOLS.items():
        code = re.sub(r'\\' + k + r'([_^\s\b])', v + r'\1', code)

    try:
        w = LatexWalker(code)
        nodelist, _, _ = w.get_latex_nodes(pos=0)
        inner_omml = "".join(_node_to_omml(n) for n in nodelist)
        if not inner_omml.strip():
            return None
        return f'<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">{inner_omml}</m:oMath>'
    except Exception:
        return None


def add_bookmark(paragraph, bookmark_name: str, bookmark_id: int):
    """Tạo bookmark trong paragraph để liên kết chéo nội bộ (Internal Cross-Reference)."""
    bm_start = parse_xml(r'<w:bookmarkStart %s w:id="%d" w:name="%s"/>' % (nsdecls("w"), bookmark_id, bookmark_name))
    bm_end = parse_xml(r'<w:bookmarkEnd %s w:id="%d"/>' % (nsdecls("w"), bookmark_id))
    paragraph._p.insert(0, bm_start)
    paragraph._p.append(bm_end)


def add_cross_ref_hyperlink(paragraph, text: str, bookmark_anchor: str, font_name: str, font_size: float):
    """Tạo liên kết chéo nội bộ (Internal Hyperlink) trỏ tới bookmark mục tiêu."""
    hyperlink = parse_xml(r'<w:hyperlink %s w:anchor="%s" w:history="1"/>' % (nsdecls("w"), bookmark_anchor))
    r = parse_xml(
        r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/><w:color w:val="0070C0"/><w:u w:val="single"/></w:rPr><w:t>%s</w:t></w:r>'
        % (nsdecls("w"), font_name, font_name, int(font_size * 2), text)
    )
    hyperlink.append(r)
    paragraph._p.append(hyperlink)


def add_field(paragraph, field_text: str, font_name="Times New Roman", font_size=10, bold=False, italic=False, color=None):
    run = paragraph.add_run()
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> %s </w:instrText>' % (nsdecls("w"), field_text))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    t = parse_xml(r"<w:t %s>1</w:t>" % nsdecls("w"))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(t)
    run._r.append(fldChar3)


def restart_section_page_numbering(section, start_at=1):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn("w:pgNumType"))
    if pgNumType is None:
        pgNumType = OxmlElement("w:pgNumType")
        sectPr.append(pgNumType)
    pgNumType.set(qn("w:start"), str(start_at))


def strip_existing_heading_number(text: str) -> str:
    """Loại bỏ tiền tố đánh số thủ công (VD: 'CHƯƠNG 1:', '1.', '1.1.', '2.1.3') để tránh lặp số."""
    cleaned = re.sub(r"^(?:CHƯƠNG|PHẦN|MỤC)\s+\d+[\.\:\-\s]*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", cleaned.strip())
    return cleaned.strip()


def extract_toc_items_from_markdown(md_text: str, appendices: list = None, style_key: str = "bktechs") -> list:
    """
    Trích xuất toàn bộ cấu trúc mục lục (Phần, Chương, Mục 1, Mục 2, Phụ lục)
    để tự động sinh Trang Mục Lục hoàn chỉnh kèm dòng chấm dot leader và liên kết chéo nội bộ.
    """
    dot = "." if style_key == "bktechs" else ""
    lines = md_text.splitlines()
    toc_items = []
    h_counts = [0, 0, 0]
    first_h1_skipped = False
    curr_main_page = 1
    bm_idx = 1

    pat_part = r"^(?:PHẦN\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\b|CÁC\s+PHỤ\s+LỤC)"
    pat_app = r"^(?:PHỤ\s+LỤC|APPENDIX)\s+\d+"
    is_under_app = False
    curr_app_num = 1

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if not m:
            continue
        level = len(m.group(1))
        raw = m.group(2).strip()

        # Bỏ qua dòng tiêu đề tài liệu nếu trùng ở đầu file
        if not first_h1_skipped:
            if level == 1 and any(k in raw.upper() for k in ["THUYẾT MINH", "BÁO CÁO", "TÍNH TOÁN KẾT CẤU"]):
                first_h1_skipped = True
                continue
            first_h1_skipped = True

        if any(raw.upper().startswith(k) for k in ["CÔNG TRÌNH:", "ĐỊA ĐIỂM:", "DỰ ÁN:", "CHỦ ĐẦU TƯ:"]):
            continue

        is_part = bool(re.match(pat_part, raw, flags=re.IGNORECASE))
        is_app = bool(re.match(pat_app, raw, flags=re.IGNORECASE))

        if is_part:
            h_counts = [0, 0, 0]
            is_under_app = False
            if "PHẦN I" in raw.upper():
                part_page = f"{curr_main_page}"
            elif "PHẦN II" in raw.upper() or "CÁC PHỤ LỤC" in raw.upper():
                part_page = "P1-1"
            elif "PHẦN III" in raw.upper():
                part_page = f"P{curr_app_num}-3" if curr_app_num > 1 else f"{curr_main_page}"
            else:
                part_page = f"{curr_main_page}"
            toc_items.append({
                "level": 1,
                "title": raw.upper(),
                "page": part_page,
                "bookmark": f"TOC_NAV_{bm_idx}",
                "is_part": True,
                "is_app": False,
            })
            bm_idx += 1
            continue

        if is_app:
            m_a = re.search(r'(?:PHỤ\s+LỤC|APPENDIX)\s+(\d+)', raw, flags=re.IGNORECASE)
            curr_app_num = int(m_a.group(1)) if m_a else 1
            is_under_app = True
            h_counts[0] = curr_app_num
            h_counts[1] = 0
            h_counts[2] = 0
            toc_items.append({
                "level": 2,
                "title": raw.upper(),
                "page": f"P{curr_app_num}-1",
                "bookmark": f"PHU_LUC_{curr_app_num}",
                "is_part": False,
                "is_app": True,
            })
            bm_idx += 1
            continue

        cleaned = strip_existing_heading_number(raw)
        if level == 1:
            h_counts[0] += 1
            h_counts[1] = 0
            h_counts[2] = 0
            disp = f"{h_counts[0]}{dot} {cleaned.upper()}"
            curr_main_page += 1
        elif level == 2:
            if h_counts[0] == 0:
                h_counts[0] = 1
            h_counts[1] += 1
            h_counts[2] = 0
            disp = f"{h_counts[0]}.{h_counts[1]}{dot} {cleaned}"
        else:
            if h_counts[0] == 0:
                h_counts[0] = 1
            if h_counts[1] == 0:
                h_counts[1] = 1
            h_counts[2] += 1
            disp = f"{h_counts[0]}.{h_counts[1]}.{h_counts[2]}{dot} {cleaned}"

        page_str = f"P{curr_app_num}-{max(1, h_counts[1])}" if is_under_app else f"{curr_main_page}"

        toc_items.append({
            "level": level,
            "title": disp,
            "page": page_str,
            "bookmark": f"TOC_NAV_{bm_idx}",
            "is_part": False,
            "is_app": False,
        })
        bm_idx += 1

    # Nếu có danh sách appendices truyền qua CLI cờ --appendices
    if appendices:
        if not any(it.get("is_part") and "PHẦN II" in it.get("title", "") for it in toc_items):
            toc_items.append({
                "level": 1,
                "title": "PHẦN II: CÁC PHỤ LỤC TÍNH TOÁN CHI TIẾT CẤU KIỆN",
                "page": "P1-1",
                "bookmark": f"TOC_NAV_{bm_idx}",
                "is_part": True,
                "is_app": False,
            })
            bm_idx += 1

        for a_idx, app_f in enumerate(appendices, 1):
            if os.path.exists(app_f):
                with open(app_f, "r", encoding="utf-8") as af:
                    content = af.read()
                f_h1, f_h2 = None, None
                for al in content.splitlines():
                    if not f_h1 and al.strip().startswith("# "):
                        f_h1 = al.strip()[2:].strip()
                    elif f_h1 and not f_h2 and al.strip().startswith("## "):
                        f_h2 = al.strip()[3:].strip()
                bname = os.path.splitext(os.path.basename(app_f))[0].replace("APPENDIX_", "").replace("_", " ").title()
                if f_h1 and f_h2:
                    atitle = f"PHỤ LỤC {a_idx}: {f_h2.upper()} ({f_h1})"
                elif f_h1:
                    atitle = f"PHỤ LỤC {a_idx}: {f_h1.upper()}"
                else:
                    atitle = f"PHỤ LỤC {a_idx}: {bname.upper()}"

                toc_items.append({
                    "level": 2,
                    "title": atitle,
                    "page": f"P{a_idx}-1",
                    "bookmark": f"PHU_LUC_{a_idx}",
                    "is_part": False,
                    "is_app": True,
                })
                bm_idx += 1

    return toc_items


def insert_auto_toc(doc, font_name="Times New Roman", toc_items: list = None, style_key: str = "bktechs"):
    """
    Tạo Trang Mục Lục hoàn chỉnh:
    - Kích hoạt trường Auto-TOC Word và cờ updateFields
    - Render toàn bộ Chương, Mục, Phụ lục kèm dòng chấm dot leader và hyperlinks điều hướng nội bộ
    """
    settings = doc.settings.element
    if settings.find(qn("w:updateFields")) is None:
        update_fields = OxmlElement("w:updateFields")
        update_fields.set(qn("w:val"), "true")
        settings.append(update_fields)

    if not toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run()
        run.font.name = font_name
        run.font.size = Pt(11)
        fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
        instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText>' % nsdecls("w"))
        fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
        t = parse_xml(
            r"<w:t %s>[Trường Mục lục tự động (Auto-TOC) — Nhấn chuột phải chọn 'Update Field' (hoặc F9) trong MS Word để cập nhật số trang tự động]</w:t>"
            % nsdecls("w")
        )
        fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
        run._r.append(t)
        run._r.append(fldChar3)
        return

    # Dòng tiêu đề cột phân cách (Nội dung ... Trang)
    p_header = doc.add_paragraph()
    p_header.paragraph_format.space_before = Pt(2)
    p_header.paragraph_format.space_after = Pt(6)
    pPr_h = p_header._p.get_or_add_pPr()
    pPr_h.append(parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="none" w:pos="9072"/></w:tabs>' % nsdecls("w")))
    rh1 = p_header.add_run("Nội dung Thuyết minh & Phụ lục")
    rh1.font.name = font_name
    rh1.font.size = Pt(10)
    rh1.font.bold = True
    rh1.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    p_header.add_run("\t")
    rh2 = p_header.add_run("Trang")
    rh2.font.name = font_name
    rh2.font.size = Pt(10)
    rh2.font.bold = True
    rh2.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    set_paragraph_bottom_border(p_header, color_hex="D9E1F2", sz="6")

    # Render danh sách Mục Lục chi tiết với tab stop dot leader
    for item in toc_items:
        lvl = item.get("level", 2)
        title = item.get("title", "")
        page_str = item.get("page", "")
        anchor = item.get("bookmark", "")
        is_part = item.get("is_part", False)

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6 if is_part else (3 if lvl in (1, 2) else 1))
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Cm(0 if is_part or lvl == 1 else (0.4 if lvl == 2 else 0.85))

        pPr = p._p.get_or_add_pPr()
        # Tab stop căn phải lề với dòng chấm dot leader tại 9072 twips (~16 cm)
        tab_xml = parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="dot" w:pos="9072"/></w:tabs>' % nsdecls("w"))
        pPr.append(tab_xml)

        if anchor:
            hl = parse_xml(r'<w:hyperlink %s w:anchor="%s" w:history="1"/>' % (nsdecls("w"), anchor))
        else:
            hl = parse_xml(r'<w:hyperlink %s w:history="1"/>' % nsdecls("w"))

        esc_title = html.escape(title)
        is_bold = (is_part or lvl in (1, 2))
        is_italic = (lvl == 3)
        font_size = 23 if is_part else (22 if lvl in (1, 2) else 20)
        text_color = "002060" if is_part else ("003399" if lvl in (1, 2) else "262626")

        r_title_xml = parse_xml(
            r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/>%s%s<w:color w:val="%s"/></w:rPr><w:t>%s</w:t></w:r>'
            % (
                nsdecls("w"),
                font_name,
                font_name,
                font_size,
                r"<w:b/>" if is_bold else "",
                r"<w:i/>" if is_italic else "",
                text_color,
                esc_title,
            )
        )
        hl.append(r_title_xml)

        # Tab dot leader
        hl.append(parse_xml(r"<w:r %s><w:tab/></w:r>" % nsdecls("w")))

        # Số trang bên phải
        r_page_xml = parse_xml(
            r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/><w:sz w:val="%d"/>%s<w:color w:val="%s"/></w:rPr><w:t>%s</w:t></w:r>'
            % (
                nsdecls("w"),
                font_name,
                font_name,
                22 if is_bold else 20,
                r"<w:b/>" if is_bold else "",
                "002060" if is_bold else "595959",
                page_str,
            )
        )
        hl.append(r_page_xml)
        p._p.append(hl)


# ==============================================================================
# XÂY DỰNG BÌA ĐÔI + MỤC LỤC + HEADER/FOOTER CHO BỘ CHUẨN 1: BKTECHS
# ==============================================================================
def setup_bktechs_template(doc, meta: dict, logo_path: str = None, preview_toc_items: list = None):
    cfg = STYLE_CONFIGS["bktechs"]
    font_name = cfg["font_family"]

    # Cấu hình Normal & Heading styles
    normal = doc.styles["Normal"]
    normal.font.name = font_name
    normal.font.size = Pt(cfg["body_size"])
    normal.font.color.rgb = cfg["body_color"]
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_before = Pt(2)
    normal.paragraph_format.space_after = Pt(4)

    # Bật kiểm soát dòng cô đơn / mồ côi (Widow/Orphan Control) toàn tài liệu
    pPr = normal._element.get_or_add_pPr()
    if pPr.find(qn("w:widowControl")) is None:
        pPr.append(parse_xml(r'<w:widowControl %s w:val="true"/>' % nsdecls("w")))

    for level, size, color in [
        (1, cfg["h1_size"], cfg["h1_color"]),
        (2, cfg["h2_size"], cfg["h2_color"]),
        (3, cfg["h3_size"], cfg["h3_color"]),
    ]:
        st = doc.styles[f"Heading {level}"]
        st.font.name = font_name
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.italic = (level == 3)
        st.font.color.rgb = color

    # --------------------------------------------------------------------------
    # SECTION 0: BÌA CHÍNH (TRANG 1) + BÌA PHỤ KÝ DUYỆT (TRANG 2) + MỤC LỤC (TRANG 3)
    # --------------------------------------------------------------------------
    sec0 = doc.sections[0]
    sec0.top_margin = Cm(1.5)
    sec0.bottom_margin = Cm(1.5)
    sec0.left_margin = Cm(2.54)
    sec0.right_margin = Cm(2.0)
    sec0.different_first_page_header_footer = True

    # Footer cho Trang 2 & Trang 3 trong Section 0 (Trang 1 ẩn nhờ different_first_page)
    f0 = sec0.footer
    fp0 = f0.paragraphs[0]
    fp0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_top_border(fp0, color_hex="BFBFBF", sz="6")
    r_org = fp0.add_run(meta.get("org_short", "BKTECHS"))
    r_org.font.name = font_name
    r_org.font.size = Pt(9.5)
    r_org.font.bold = True
    r_org.font.color.rgb = RGBColor(0x00, 0x33, 0x99)
    r_sep1 = fp0.add_run("  ||  ")
    r_sep1.font.name = font_name
    r_sep1.font.size = Pt(9.5)
    r_sep1.font.bold = True
    r_sep1.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)
    r_addr = fp0.add_run(meta.get("org_footer", "268 Lý Thường Kiệt, P.14, Q.10, TP.HCM  |  Tel: (028) 3864 7256"))
    r_addr.font.name = font_name
    r_addr.font.size = Pt(9.5)
    r_addr.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    r_sep2 = fp0.add_run("  ||")
    r_sep2.font.name = font_name
    r_sep2.font.size = Pt(9.5)
    r_sep2.font.bold = True
    r_sep2.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

    # --- TRANG 1: BÌA CHÍNH CHUẨN BKTECHS ---
    p_top1 = doc.add_paragraph()
    p_top1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top1.paragraph_format.space_before = Pt(0)
    p_top1.paragraph_format.space_after = Pt(2)
    r1 = p_top1.add_run(meta.get("parent_org", "TRƯỜNG ĐẠI HỌC BÁCH KHOA - ĐHQG TP.HCM (HCMUT)"))
    r1.font.name = font_name
    r1.font.size = Pt(12)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_top2 = doc.add_paragraph()
    p_top2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top2.paragraph_format.space_after = Pt(8)
    r2 = p_top2.add_run(meta.get("company_name", "CÔNG TY CỔ PHẦN KHOA HỌC CÔNG NGHỆ BÁCH KHOA TP.HCM - BKTECHS"))
    r2.font.name = font_name
    r2.font.size = Pt(12.5)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(0x00, 0x33, 0x99)

    # Thanh ribbon xanh đậm phía trên
    ribbon_top = doc.add_table(rows=1, cols=1)
    ribbon_top.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_rt = ribbon_top.cell(0, 0)
    set_cell_shading(c_rt, "002060")
    set_cell_margins(c_rt, top=40, bottom=40, left=80, right=80)
    p_rt = c_rt.paragraphs[0]
    p_rt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_rt = p_rt.add_run("STRUCTURAL & GEOTECHNICAL ENGINEERING CONSULTANCY")
    r_rt.font.name = font_name
    r_rt.font.size = Pt(9.5)
    r_rt.font.bold = True
    r_rt.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

    # Logo trung tâm
    if logo_path and os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(18)
        p_logo.paragraph_format.space_after = Pt(14)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.65))
    else:
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(24)
        p_logo.paragraph_format.space_after = Pt(18)
        rl = p_logo.add_run("[ LOGO ĐƠN VỊ TƯ VẤN / BKTECHS ]")
        rl.font.name = font_name
        rl.font.size = Pt(12)
        rl.font.bold = True
        rl.font.color.rgb = RGBColor(0x00, 0x33, 0x99)

    # Tên loại hồ sơ cỡ lớn
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(6)
    rt = p_title.add_run(meta.get("report_type", "THUYẾT MINH TÍNH TOÁN KẾT CẤU"))
    rt.font.name = font_name
    rt.font.size = Pt(24)
    rt.font.bold = True
    rt.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)
    set_paragraph_bottom_border(p_sub, color_hex="FFC000", sz="18")
    rsub = p_sub.add_run(f"GIAI ĐOẠN: {meta.get('phase', 'THIẾT KẾ BẢN VẼ THI CÔNG (BVTC)')}")
    rsub.font.name = font_name
    rsub.font.size = Pt(13)
    rsub.font.bold = True
    rsub.font.italic = True
    rsub.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    # Bảng thông tin Dự án / Hạng mục / Chủ đầu tư trên bìa
    info_tbl = doc.add_table(rows=5, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(info_tbl, color="D9E1F2", sz="6")
    cover_rows = [
        ("DỰ ÁN / CÔNG TRÌNH:", meta.get("project_name", "[Tên Dự án / Công trình]")),
        ("HẠNG MỤC TÍNH TOÁN:", meta.get("item_name", "[Tên Hạng mục Kết cấu / Biện pháp thi công]")),
        ("ĐỊA ĐIỂM XÂY DỰNG:", meta.get("location", "[Địa điểm xây dựng công trình]")),
        ("CHỦ ĐẦU TƯ:", meta.get("client_name", "[Tên Chủ đầu tư]")),
        ("MÃ HỒ SƠ / PHIÊN BẢN:", meta.get("doc_code", "BKTECHS-TMTT-2026 / Rev.00")),
    ]
    for idx, (label, val) in enumerate(cover_rows):
        row = info_tbl.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Cm(5.2)
        c1.width = Cm(11.2)
        set_cell_margins(c0, top=110, bottom=110, left=140, right=100)
        set_cell_margins(c1, top=110, bottom=110, left=140, right=140)
        set_cell_shading(c0, "F2F5F9")
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.name = font_name
        r0.font.size = Pt(11.5)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

        p1 = c1.paragraphs[0]
        r1_val = p1.add_run(val)
        r1_val.font.name = font_name
        r1_val.font.size = Pt(11.5)
        r1_val.font.bold = (idx in (0, 1))
        r1_val.font.italic = (idx == 1)
        r1_val.font.color.rgb = RGBColor(0x00, 0x33, 0x99) if idx == 0 else RGBColor(0x1A, 0x1A, 0x1A)

    # Chân bìa Trang 1
    p_city = doc.add_paragraph()
    p_city.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_city.paragraph_format.space_before = Pt(42)
    p_city.paragraph_format.space_after = Pt(6)
    rcity = p_city.add_run(meta.get("place_date", "TP. HỒ CHÍ MINH — NĂM 2026"))
    rcity.font.name = font_name
    rcity.font.size = Pt(12)
    rcity.font.bold = True
    rcity.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    ribbon_bot = doc.add_table(rows=1, cols=1)
    ribbon_bot.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_rb = ribbon_bot.cell(0, 0)
    set_cell_shading(c_rb, "002060")
    set_cell_margins(c_rb, top=35, bottom=35, left=80, right=80)
    p_rb = c_rb.paragraphs[0]
    p_rb.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_rb = p_rb.add_run("BACH KHOA HO CHI MINH CITY SCIENCE TECHNOLOGY JSC — QUALITY & RELIABILITY")
    r_rb.font.name = font_name
    r_rb.font.size = Pt(9.5)
    r_rb.font.bold = True
    r_rb.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # --- TRANG 2: BÌA PHỤ / TỜ KÝ DUYỆT TRÁCH NHIỆM CHUYÊN MÔN CHUẨN BKTECHS ---
    doc.add_page_break()

    p_sub1 = doc.add_paragraph()
    p_sub1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub1.paragraph_format.space_before = Pt(6)
    p_sub1.paragraph_format.space_after = Pt(2)
    rs1 = p_sub1.add_run(meta.get("parent_org", "TRƯỜNG ĐẠI HỌC BÁCH KHOA - ĐHQG TP.HCM (HCMUT)"))
    rs1.font.name = font_name
    rs1.font.size = Pt(11.5)
    rs1.font.bold = True
    rs1.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_sub2 = doc.add_paragraph()
    p_sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub2.paragraph_format.space_after = Pt(14)
    set_paragraph_bottom_border(p_sub2, color_hex="FFC000", sz="12")
    rs2 = p_sub2.add_run(meta.get("company_name", "CÔNG TY CỔ PHẦN KHOA HỌC CÔNG NGHỆ BÁCH KHOA TP.HCM - BKTECHS"))
    rs2.font.name = font_name
    rs2.font.size = Pt(12)
    rs2.font.bold = True
    rs2.font.color.rgb = RGBColor(0x00, 0x33, 0x99)

    p_stitle = doc.add_paragraph()
    p_stitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_stitle.paragraph_format.space_before = Pt(16)
    p_stitle.paragraph_format.space_after = Pt(4)
    rst = p_stitle.add_run(meta.get("report_type", "THUYẾT MINH TÍNH TOÁN KẾT CẤU"))
    rst.font.name = font_name
    rst.font.size = Pt(20)
    rst.font.bold = True
    rst.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_sitem = doc.add_paragraph()
    p_sitem.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sitem.paragraph_format.space_after = Pt(16)
    rsi = p_sitem.add_run(f"Hạng mục: {meta.get('item_name', '[Tên Hạng mục]')}\nDự án: {meta.get('project_name', '[Tên Dự án]')}")
    rsi.font.name = font_name
    rsi.font.size = Pt(12.5)
    rsi.font.bold = True
    rsi.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    # Bảng Kiểm soát chất lượng & Chữ ký 3 cột chuẩn BKTECHS (Thực hiện - Kiểm tra - Chủ trì)
    p_sig_lbl = doc.add_paragraph()
    p_sig_lbl.paragraph_format.space_before = Pt(8)
    p_sig_lbl.paragraph_format.space_after = Pt(6)
    r_sl = p_sig_lbl.add_run("BẢNG TRÁCH NHIỆM PHÁP LÝ & KIỂM SOÁT CHẤT LƯỢNG HỒ SƠ:")
    r_sl.font.name = font_name
    r_sl.font.size = Pt(11.5)
    r_sl.font.bold = True
    r_sl.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    sig_tbl = doc.add_table(rows=4, cols=3)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(sig_tbl, color="002060", sz="6")
    headers_sig = ["THỰC HIỆN TÍNH TOÁN\n(Prepared by)", "KIỂM TRA KỸ THUẬT\n(Checked by)", "CHỦ TRÌ THIẾT KẾ / THẨM TRA\n(Approved by)"]
    for idx, htext in enumerate(headers_sig):
        c = sig_tbl.cell(0, idx)
        set_cell_shading(c, "002060")
        set_cell_margins(c, top=100, bottom=100, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(htext)
        r.font.name = font_name
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Hàng khoảng trống ký tên
    for idx in range(3):
        c = sig_tbl.cell(1, idx)
        set_cell_margins(c, top=360, bottom=360, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("(Ký, ghi rõ họ tên)")
        r.font.name = font_name
        r.font.size = Pt(10)
        r.font.italic = True
        r.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)

    # Hàng Họ tên & Học vị
    roles_name = [
        meta.get("prepared_by", "KS. [Họ và tên Kỹ sư]"),
        meta.get("checked_by", "ThS.KS. [Họ và tên Người kiểm]"),
        meta.get("approved_by", "TS. / ThS. [Họ và tên Chủ trì]"),
    ]
    for idx, rname in enumerate(roles_name):
        c = sig_tbl.cell(2, idx)
        set_cell_shading(c, "F2F5F9")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(rname)
        r.font.name = font_name
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    # Hàng Số Chứng chỉ hành nghề (CCHN)
    cchn_list = [
        meta.get("prepared_cchn", "CCHN: [Số CCHN - Hạng ...]"),
        meta.get("checked_cchn", "CCHN: [Số CCHN - Hạng ...]"),
        meta.get("approved_cchn", "CCHN: [Số CCHN - Hạng I/II]"),
    ]
    for idx, cchn in enumerate(cchn_list):
        c = sig_tbl.cell(3, idx)
        set_cell_margins(c, top=70, bottom=70, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(cchn)
        r.font.name = font_name
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Khối đại diện pháp luật Đơn vị tư vấn & Chủ đầu tư
    p_rep_lbl = doc.add_paragraph()
    p_rep_lbl.paragraph_format.space_before = Pt(18)
    p_rep_lbl.paragraph_format.space_after = Pt(6)
    r_rl = p_rep_lbl.add_run("XÁC NHẬN PHÁP LÝ CỦA ĐƠN VỊ TƯ VẤN & CHỦ ĐẦU TƯ:")
    r_rl.font.name = font_name
    r_rl.font.size = Pt(11.5)
    r_rl.font.bold = True
    r_rl.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    rep_tbl = doc.add_table(rows=2, cols=2)
    rep_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(rep_tbl, color="BFBFBF", sz="6")
    for idx, title in enumerate(["ĐẠI DIỆN CHỦ ĐẦU TƯ", "ĐẠI DIỆN ĐƠN VỊ TƯ VẤN (BKTECHS)"]):
        c = rep_tbl.cell(0, idx)
        set_cell_shading(c, "D9E1F2")
        set_cell_margins(c, top=90, bottom=90, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title)
        r.font.name = font_name
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

        c_sign = rep_tbl.cell(1, idx)
        set_cell_margins(c_sign, top=420, bottom=120, left=100, right=100)
        ps = c_sign.paragraphs[0]
        ps.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rs = ps.add_run("(Ký tên, đóng dấu pháp nhân)")
        rs.font.name = font_name
        rs.font.size = Pt(10)
        rs.font.italic = True
        rs.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)

    # --- TRANG 3: MỤC LỤC (TABLE OF CONTENTS) ---
    doc.add_page_break()
    p_toc_title = doc.add_paragraph()
    p_toc_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_toc_title.paragraph_format.space_before = Pt(6)
    p_toc_title.paragraph_format.space_after = Pt(10)
    set_paragraph_bottom_border(p_toc_title, color_hex="0070C0", sz="12")
    rtoc = p_toc_title.add_run("MỤC LỤC NỘI DUNG & PHỤ LỤC")
    rtoc.font.name = font_name
    rtoc.font.size = Pt(16)
    rtoc.font.bold = True
    rtoc.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    insert_auto_toc(doc, font_name=font_name, toc_items=preview_toc_items, style_key="bktechs")

    # --------------------------------------------------------------------------
    # SECTION 1: NỘI DUNG THUYẾT MINH CHÍNH (ĐÁNH SỐ TRANG LẠI TỪ 1 | Page)
    # --------------------------------------------------------------------------
    sec1 = doc.add_section(WD_SECTION.NEW_PAGE)
    sec1.top_margin = Cm(2.5)
    sec1.bottom_margin = Cm(1.8)
    sec1.left_margin = Cm(2.54)
    sec1.right_margin = Cm(2.0)
    sec1.different_first_page_header_footer = False
    sec1.header.is_linked_to_previous = False
    sec1.footer.is_linked_to_previous = False
    restart_section_page_numbering(sec1, start_at=1)

    # Header Section 1: Tên đơn vị màu xanh + đường kẻ ngang màu vàng cam (#FFC000)
    h1 = sec1.header
    hp1 = h1.paragraphs[0]
    hp1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_bottom_border(hp1, color_hex="FFC000", sz="12")
    rh_org = hp1.add_run(
        f"{meta.get('company_name', 'BACH KHOA HO CHI MINH CITY SCIENCE TECHNOLOGY JSC - BKTECHS')}\n"
    )
    rh_org.font.name = font_name
    rh_org.font.size = Pt(9.5)
    rh_org.font.bold = True
    rh_org.font.color.rgb = RGBColor(0x00, 0x33, 0x99)
    rh_proj = hp1.add_run(
        f"Dự án: {meta.get('project_name', '[Tên Dự án]')}  —  Hạng mục: {meta.get('item_name', '[Tên Hạng mục]')}"
    )
    rh_proj.font.name = font_name
    rh_proj.font.size = Pt(9.5)
    rh_proj.font.italic = True
    rh_proj.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    # Footer Section 1: BKTECHS || Địa chỉ || 1 | Page
    f1 = sec1.footer
    fp1 = f1.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_top_border(fp1, color_hex="BFBFBF", sz="6")
    rf1 = fp1.add_run(meta.get("org_short", "BKTECHS"))
    rf1.font.name = font_name
    rf1.font.size = Pt(9.5)
    rf1.font.bold = True
    rf1.font.color.rgb = RGBColor(0x00, 0x33, 0x99)

    rf2 = fp1.add_run("  ||  ")
    rf2.font.name = font_name
    rf2.font.size = Pt(9.5)
    rf2.font.bold = True
    rf2.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

    rf3 = fp1.add_run(meta.get("org_footer", "268 Lý Thường Kiệt, P.14, Q.10, TP.HCM  |  Tel: (028) 3864 7256"))
    rf3.font.name = font_name
    rf3.font.size = Pt(9.5)
    rf3.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    rf4 = fp1.add_run("  ||  Trang ")
    rf4.font.name = font_name
    rf4.font.size = Pt(9.5)
    rf4.font.bold = True
    rf4.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

    add_field(fp1, "PAGE", font_name=font_name, font_size=9.5, bold=True, color=RGBColor(0x00, 0x20, 0x60))
    rf5 = fp1.add_run(" / ")
    rf5.font.name = font_name
    rf5.font.size = Pt(9.5)
    add_field(fp1, "SECTIONPAGES", font_name=font_name, font_size=9.5, bold=False, color=RGBColor(0x59, 0x59, 0x59))


# ==============================================================================
# XÂY DỰNG BÌA ĐÔI + MỤC LỤC + HEADER/FOOTER CHO BỘ CHUẨN 2: TVTK ĐA HẠNG MỤC
# ==============================================================================
def setup_tvtk_template(doc, meta: dict, preview_toc_items: list = None):
    cfg = STYLE_CONFIGS["tvtk"]
    font_name = cfg["font_family"]

    normal = doc.styles["Normal"]
    normal.font.name = font_name
    normal.font.size = Pt(cfg["body_size"])
    normal.font.color.rgb = cfg["body_color"]
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_before = Pt(2)
    normal.paragraph_format.space_after = Pt(4)

    # Bật kiểm soát dòng cô đơn / mồ côi (Widow/Orphan Control) toàn tài liệu
    pPr = normal._element.get_or_add_pPr()
    if pPr.find(qn("w:widowControl")) is None:
        pPr.append(parse_xml(r'<w:widowControl %s w:val="true"/>' % nsdecls("w")))

    for level, size, color in [
        (1, cfg["h1_size"], cfg["h1_color"]),
        (2, cfg["h2_size"], cfg["h2_color"]),
        (3, cfg["h3_size"], cfg["h3_color"]),
    ]:
        st = doc.styles[f"Heading {level}"]
        st.font.name = font_name
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.italic = (level == 3)
        st.font.color.rgb = color

    # --------------------------------------------------------------------------
    # SECTION 0: BÌA KHUNG VIỀN ĐÔI (TRANG 1) + BÌA LÓT PHÁP LÝ (TRANG 2) + MỤC LỤC (TRANG 3)
    # --------------------------------------------------------------------------
    sec0 = doc.sections[0]
    sec0.top_margin = Cm(1.8)
    sec0.bottom_margin = Cm(1.8)
    sec0.left_margin = Cm(2.5)
    sec0.right_margin = Cm(2.0)
    sec0.different_first_page_header_footer = True

    # --- TRANG 1: BÌA NGOÀI KHUNG VIỀN ĐÔI (DOUBLE-LINE BOX) ---
    outer_box = doc.add_table(rows=1, cols=1)
    outer_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(outer_box, color="002060", sz="18", val="double")
    c_box = outer_box.cell(0, 0)
    set_cell_margins(c_box, top=280, bottom=280, left=260, right=260)

    p_c1 = c_box.paragraphs[0]
    p_c1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_c1.paragraph_format.space_after = Pt(4)
    set_paragraph_bottom_border(p_c1, color_hex="002060", sz="12")
    rc1 = p_c1.add_run(
        f"{meta.get('company_name', 'CÔNG TY CỔ PHẦN TƯ VẤN THIẾT KẾ XÂY DỰNG [TÊN ĐƠN VỊ TVTK]')}\n"
    )
    rc1.font.name = font_name
    rc1.font.size = Pt(11)
    rc1.font.bold = True
    rc1.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    rc2 = p_c1.add_run(
        meta.get("org_footer", "Địa chỉ: [Địa chỉ Công ty Tư vấn Thiết kế]  |  Điện thoại: [Số ĐT]  |  Email: [Email]")
    )
    rc2.font.name = font_name
    rc2.font.size = Pt(9.5)
    rc2.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    p_type = c_box.add_paragraph()
    p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_type.paragraph_format.space_before = Pt(54)
    p_type.paragraph_format.space_after = Pt(8)
    rtype = p_type.add_run(meta.get("report_type", "THUYẾT MINH TÍNH TOÁN KẾT CẤU"))
    rtype.font.name = font_name
    rtype.font.size = Pt(22)
    rtype.font.bold = True
    rtype.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_phase = c_box.add_paragraph()
    p_phase.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_phase.paragraph_format.space_after = Pt(36)
    rph = p_phase.add_run(f"GIAI ĐOẠN: {meta.get('phase', 'THIẾT KẾ KỸ THUẬT / BẢN VẼ THI CÔNG')}")
    rph.font.name = font_name
    rph.font.size = Pt(12)
    rph.font.bold = True
    rph.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    # Thông tin công trình ở giữa khung bìa
    for lbl, val in [
        ("CÔNG TRÌNH:", meta.get("project_name", "[TÊN CÔNG TRÌNH / DỰ ÁN ĐẦU TƯ XÂY DỰNG]")),
        ("HẠNG MỤC:", meta.get("item_name", "KẾT CẤU (TỔNG HỢP CÁC HẠNG MỤC CÔNG TRÌNH)")),
        ("ĐỊA ĐIỂM XÂY DỰNG:", meta.get("location", "[Phường/Xã, Quận/Huyện, Tỉnh/Thành phố]")),
        ("CHỦ ĐẦU TƯ:", meta.get("client_name", "[TÊN CHỦ ĐẦU TƯ]")),
    ]:
        p_info = c_box.add_paragraph()
        p_info.paragraph_format.space_before = Pt(8)
        p_info.paragraph_format.space_after = Pt(8)
        rl = p_info.add_run(f"{lbl} ")
        rl.font.name = font_name
        rl.font.size = Pt(11.5)
        rl.font.bold = True
        rl.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
        rv = p_info.add_run(val)
        rv.font.name = font_name
        rv.font.size = Pt(11.5)
        rv.font.bold = (lbl == "CÔNG TRÌNH:")
        rv.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)

    p_bot = c_box.add_paragraph()
    p_bot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bot.paragraph_format.space_before = Pt(72)
    p_bot.paragraph_format.space_after = Pt(6)
    rbot = p_bot.add_run(meta.get("place_date", "THÀNH PHỐ HỒ CHÍ MINH — NĂM 2026"))
    rbot.font.name = font_name
    rbot.font.size = Pt(11.5)
    rbot.font.bold = True
    rbot.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    # --- TRANG 2: BÌA LÓT PHÁP LÝ (QUỐC HIỆU + KHỐI ĐÓNG DẤU 2 CỘT CĐT & TVTK) ---
    doc.add_page_break()

    p_qh1 = doc.add_paragraph()
    p_qh1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh1.paragraph_format.space_before = Pt(6)
    p_qh1.paragraph_format.space_after = Pt(2)
    rqh1 = p_qh1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    rqh1.font.name = font_name
    rqh1.font.size = Pt(12)
    rqh1.font.bold = True

    p_qh2 = doc.add_paragraph()
    p_qh2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh2.paragraph_format.space_after = Pt(28)
    rqh2 = p_qh2.add_run("Độc lập - Tự do - Hạnh phúc\n____________________")
    rqh2.font.name = font_name
    rqh2.font.size = Pt(11.5)
    rqh2.font.bold = True

    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_before = Pt(18)
    p_t2.paragraph_format.space_after = Pt(6)
    rt2 = p_t2.add_run(meta.get("report_type", "THUYẾT MINH THIẾT KẾ KỸ THUẬT (KẾT CẤU)"))
    rt2.font.name = font_name
    rt2.font.size = Pt(18)
    rt2.font.bold = True
    rt2.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_t2_sub = doc.add_paragraph()
    p_t2_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_sub.paragraph_format.space_after = Pt(28)
    rt2s = p_t2_sub.add_run(
        f"CÔNG TRÌNH: {meta.get('project_name', '[Tên Công trình]')}\n"
        f"ĐỊA ĐIỂM: {meta.get('location', '[Địa điểm xây dựng]')}"
    )
    rt2s.font.name = font_name
    rt2s.font.size = Pt(11.5)
    rt2s.font.bold = True

    # Bảng chữ ký 2 cột cân xứng: CHỦ ĐẦU TƯ — ĐƠN VỊ THIẾT KẾ
    sign_2col = doc.add_table(rows=3, cols=2)
    sign_2col.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(sign_2col, color="002060", sz="6")

    for idx, header_txt in enumerate(["CHỦ ĐẦU TƯ", "ĐƠN VỊ TƯ VẤN THIẾT KẾ"]):
        c = sign_2col.cell(0, idx)
        set_cell_shading(c, "B4C6E7")
        set_cell_margins(c, top=100, bottom=100, left=120, right=120)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(header_txt)
        r.font.name = font_name
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    for idx, org_txt in enumerate([
        meta.get("client_name", "[TÊN CHỦ ĐẦU TƯ]"),
        meta.get("company_name", "[TÊN ĐƠN VỊ TƯ VẤN THIẾT KẾ]"),
    ]):
        c = sign_2col.cell(1, idx)
        set_cell_margins(c, top=80, bottom=80, left=120, right=120)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(org_txt)
        r.font.name = font_name
        r.font.size = Pt(10.5)
        r.font.bold = True

        c_space = sign_2col.cell(2, idx)
        set_cell_margins(c_space, top=480, bottom=140, left=120, right=120)
        ps = c_space.paragraphs[0]
        ps.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rs = ps.add_run("(Ký tên, đóng dấu pháp nhân)")
        rs.font.name = font_name
        rs.font.size = Pt(10)
        rs.font.italic = True
        rs.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)

    # Khối danh sách Chủ trì & Thiết kế viên bên dưới
    p_team = doc.add_paragraph()
    p_team.paragraph_format.space_before = Pt(20)
    p_team.paragraph_format.space_after = Pt(6)
    rtm = p_team.add_run("NHÓM KỸ SƯ THỰC HIỆN HỒ SƠ THUYẾT MINH:")
    rtm.font.name = font_name
    rtm.font.size = Pt(11)
    rtm.font.bold = True
    rtm.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    team_tbl = doc.add_table(rows=4, cols=3)
    team_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(team_tbl, color="BFBFBF", sz="4")
    for idx, htxt in enumerate(["Chức danh", "Họ và tên / Số CCHN", "Chữ ký"]):
        c = team_tbl.cell(0, idx)
        set_cell_shading(c, "D9E1F2")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(htxt)
        r.font.name = font_name
        r.font.size = Pt(10.5)
        r.font.bold = True

    team_rows = [
        ("Chủ trì kết cấu", f"{meta.get('approved_by', 'ThS.KS. [Họ và tên]')} — {meta.get('approved_cchn', 'CCHN Hạng I')}", ""),
        ("Kiểm tra thiết kế", f"{meta.get('checked_by', 'KS. [Họ và tên]')} — {meta.get('checked_cchn', 'CCHN Hạng II')}", ""),
        ("Thiết kế / Tính toán", f"{meta.get('prepared_by', 'KS. [Họ và tên]')}", ""),
    ]
    for r_idx, (role_s, name_s, sig_s) in enumerate(team_rows, start=1):
        for c_idx, val in enumerate([role_s, name_s, sig_s]):
            c = team_tbl.cell(r_idx, c_idx)
            set_cell_margins(c, top=90, bottom=90, left=100, right=100)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = font_name
            r.font.size = Pt(10.5)
            r.font.bold = (c_idx == 0)

    # --- TRANG 3: MỤC LỤC TỰ ĐỘNG 3 CẤP ---
    doc.add_page_break()
    p_toc = doc.add_paragraph()
    p_toc.paragraph_format.space_before = Pt(6)
    p_toc.paragraph_format.space_after = Pt(10)
    set_paragraph_bottom_border(p_toc, color_hex="0070C0", sz="12")
    rtoc = p_toc.add_run("MỤC LỤC TỔNG HỢP & PHỤ LỤC")
    rtoc.font.name = font_name
    rtoc.font.size = Pt(15)
    rtoc.font.bold = True
    rtoc.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    insert_auto_toc(doc, font_name=font_name, toc_items=preview_toc_items, style_key="tvtk")

    # --------------------------------------------------------------------------
    # SECTION 1: NỘI DUNG CHÍNH (ĐÁNH SỐ LẠI TỪ Trang 1)
    # --------------------------------------------------------------------------
    sec1 = doc.add_section(WD_SECTION.NEW_PAGE)
    sec1.top_margin = Cm(2.2)
    sec1.bottom_margin = Cm(1.8)
    sec1.left_margin = Cm(2.5)
    sec1.right_margin = Cm(2.0)
    sec1.different_first_page_header_footer = False
    sec1.header.is_linked_to_previous = False
    sec1.footer.is_linked_to_previous = False
    restart_section_page_numbering(sec1, start_at=1)

    h1 = sec1.header
    hp1 = h1.paragraphs[0]
    hp1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_bottom_border(hp1, color_hex="002060", sz="8")
    rh = hp1.add_run(
        f"{meta.get('report_type', 'THUYẾT MINH TÍNH TOÁN KẾT CẤU')}  |  {meta.get('project_name', '[Tên Công trình]')}"
    )
    rh.font.name = font_name
    rh.font.size = Pt(9.5)
    rh.font.italic = True
    rh.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    f1 = sec1.footer
    fp1 = f1.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_top_border(fp1, color_hex="BFBFBF", sz="6")
    rf = fp1.add_run("Trang ")
    rf.font.name = font_name
    rf.font.size = Pt(9.5)
    rf.font.italic = True
    add_field(fp1, "PAGE", font_name=font_name, font_size=9.5, italic=True)
    rf_sep = fp1.add_run(" / ")
    rf_sep.font.name = font_name
    rf_sep.font.size = Pt(9.5)
    rf_sep.font.italic = True
    add_field(fp1, "SECTIONPAGES", font_name=font_name, font_size=9.5, italic=True)


# ==============================================================================
# PARSER MARKDOWN -> DOCX (TỰ ĐỘNG ĐÁNH SỐ HEADING 1-2-3 & ĐỊNH DẠNG BẢNG)
# ==============================================================================
def render_markdown_content(doc, md_text: str, style_key: str = "bktechs", nav_counter_start: int = 1) -> int:
    cfg = STYLE_CONFIGS[style_key]
    font_name = cfg["font_family"]
    dot = "." if cfg["dot_after_number"] else ""

    h_counts = [0, 0, 0]
    lines = md_text.splitlines()
    i = 0
    nav_counter = nav_counter_start

    pat_part = r"^(?:PHẦN\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\b|CÁC\s+PHỤ\s+LỤC)"
    pat_app = r"^(?:PHỤ\s+LỤC|APPENDIX)\s+\d+"

    while i < len(lines):
        line = lines[i].rstrip()

        # Bỏ qua dòng trống
        if not line.strip():
            i += 1
            continue

        # Bảng Markdown
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_str = lines[i].strip()
                # Bỏ qua dòng phân cách |---|---|
                if not re.match(r"^\|[\s\-\:\|]+\|$", row_str):
                    cells = [c.strip() for c in row_str.strip("|").split("|")]
                    table_lines.append(cells)
                i += 1
            if table_lines:
                ncols = max(len(r) for r in table_lines)
                tbl = doc.add_table(rows=len(table_lines), cols=ncols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, color="BFBFBF", sz="4")

                # Lặp lại header bảng khi qua trang + cố định chiều cao tối thiểu 360 twips
                header_tr = tbl.rows[0]._tr.get_or_add_trPr()
                header_tr.append(parse_xml(r"<w:tblHeader %s/>" % nsdecls("w")))
                header_tr.append(parse_xml(r'<w:trHeight %s w:val="360" w:hRule="atLeast"/>' % nsdecls("w")))

                for r_idx, row_vals in enumerate(table_lines):
                    row = tbl.rows[r_idx]
                    if r_idx > 0:
                        row._tr.get_or_add_trPr().append(parse_xml(r"<w:cantSplit %s/>" % nsdecls("w")))
                    row_joined = " ".join(row_vals).upper()
                    is_highlight = any(k in row_joined for k in ["KẾT LUẬN", "KIỂM TRA", "ĐẠT", "THỎA", "OK"])

                    for c_idx in range(ncols):
                        val = row_vals[c_idx] if c_idx < len(row_vals) else ""
                        cell = row.cells[c_idx]
                        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                        set_cell_margins(cell, top=75, bottom=75, left=110, right=110)

                        if r_idx == 0:
                            set_cell_shading(cell, cfg["table_header_fill"])
                        elif is_highlight:
                            set_cell_shading(cell, cfg["table_highlight_fill"])
                        elif r_idx % 2 == 1:
                            set_cell_shading(cell, cfg["table_alt_fill"])

                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        if r_idx == 0:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            p.paragraph_format.keep_with_next = True
                        elif c_idx == 0 and len(val) <= 12:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        clean_val = re.sub(r"\*\*(.*?)\*\*", r"\1", val)
                        r = p.add_run(clean_val)
                        r.font.name = font_name
                        r.font.size = Pt(cfg["table_size"])
                        if r_idx == 0:
                            r.font.bold = True
                            r.font.color.rgb = cfg["table_header_text"]
                        elif is_highlight or ("**" in val):
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
                        else:
                            r.font.color.rgb = cfg["body_color"]
            continue

        # Công thức toán hiển thị độc lập: $$ ... $$
        m_disp_math = re.match(r"^\$\$(.*?)\$\$$", line.strip())
        if m_disp_math:
            eq_code = m_disp_math.group(1).strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            omml_str = latex_to_omml(eq_code)
            if omml_str:
                try:
                    p._p.append(parse_xml(omml_str))
                except Exception:
                    _add_formatted_runs(p, f"$${eq_code}$$", font_name, cfg["body_size"], cfg["body_color"])
            else:
                _add_formatted_runs(p, f"$${eq_code}$$", font_name, cfg["body_size"], cfg["body_color"])
            i += 1
            continue

        # Headings (#, ##, ###)
        m_h = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if m_h:
            level = len(m_h.group(1))
            raw_text = m_h.group(2).strip()

            # Bỏ qua dòng tiêu đề tài liệu nếu trùng ở đầu Section 1
            if level == 1 and any(k in raw_text.upper() for k in ["THUYẾT MINH TÍNH TOÁN KẾT CẤU TỔNG THỂ", "BÁO CÁO THẨM TRA", "THUYẾT MINH TÍNH TOÁN KẾT CẤU"]):
                if i < 5:
                    i += 1
                    continue

            is_part = bool(re.match(pat_part, raw_text, flags=re.IGNORECASE))
            is_app = bool(re.match(pat_app, raw_text, flags=re.IGNORECASE))

            if is_part:
                h_counts = [0, 0, 0]
                display_title = raw_text.upper()
            elif is_app:
                m_a = re.search(r'(?:PHỤ\s+LỤC|APPENDIX)\s+(\d+)', raw_text, flags=re.IGNORECASE)
                a_num = int(m_a.group(1)) if m_a else 1
                h_counts[0] = a_num
                h_counts[1] = 0
                h_counts[2] = 0
                display_title = raw_text.upper()
            else:
                raw_title = strip_existing_heading_number(raw_text)
                if level == 1:
                    h_counts[0] += 1
                    h_counts[1] = 0
                    h_counts[2] = 0
                    num_prefix = f"{h_counts[0]}{dot}"
                    display_title = f"{num_prefix} {raw_title.upper()}"
                elif level == 2:
                    if h_counts[0] == 0:
                        h_counts[0] = 1
                    h_counts[1] += 1
                    h_counts[2] = 0
                    num_prefix = f"{h_counts[0]}.{h_counts[1]}{dot}"
                    display_title = f"{num_prefix} {raw_title}"
                else:
                    if h_counts[0] == 0:
                        h_counts[0] = 1
                    if h_counts[1] == 0:
                        h_counts[1] = 1
                    h_counts[2] += 1
                    num_prefix = f"{h_counts[0]}.{h_counts[1]}.{h_counts[2]}{dot}"
                    display_title = f"{num_prefix} {raw_title}"

            p = doc.add_paragraph(style=f"Heading {level}")
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_before = Pt(14 if (level == 1 or is_part) else (10 if level == 2 else 6))
            p.paragraph_format.space_after = Pt(6 if (level == 1 or is_part) else 4)
            if (level == 1 or is_part) and style_key == "bktechs":
                set_paragraph_bottom_border(p, color_hex="D9E1F2", sz="6")

            r = p.add_run(display_title)
            r.font.name = font_name
            r.font.size = Pt(cfg[f"h{level}_size"])
            r.font.bold = True
            r.font.italic = (level == 3)
            r.font.color.rgb = cfg[f"h{level}_color"]

            # Gán bookmark tự động:
            # 1. Bookmark theo Phụ lục
            m_app = re.search(r'(?:PHỤ LỤC|Phụ lục|APPENDIX)\s+(\d+)', raw_text, flags=re.IGNORECASE)
            if m_app:
                app_num = int(m_app.group(1))
                add_bookmark(p, f"PHU_LUC_{app_num}", 1000 + app_num)

            # 2. Bookmark điều hướng từ Mục lục (TOC_NAV_*)
            add_bookmark(p, f"TOC_NAV_{nav_counter}", 2000 + nav_counter)
            nav_counter += 1

            i += 1
            continue

        # Đường kẻ phân cách ngang (---)
        if re.match(r"^---+$", line.strip()):
            p_sep = doc.add_paragraph()
            p_sep.paragraph_format.space_before = Pt(6)
            p_sep.paragraph_format.space_after = Pt(6)
            set_paragraph_bottom_border(p_sep, color_hex="D9E1F2", sz="6")
            i += 1
            continue

        # Hình ảnh Markdown: ![caption](image_path)
        m_img = re.match(r"^!\[(.*?)\]\((.*?)\)$", line.strip())
        if m_img:
            cap = m_img.group(1).strip()
            raw_path = m_img.group(2).strip()
            clean_path = raw_path
            if clean_path.startswith("file:///"):
                clean_path = clean_path[8:]
            clean_path = os.path.normpath(clean_path)
            if os.path.exists(clean_path):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(2)
                p_img.add_run().add_picture(clean_path, width=Cm(14.5))
                if cap:
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_before = Pt(0)
                    p_cap.paragraph_format.space_after = Pt(8)
                    r_cap = p_cap.add_run(cap)
                    r_cap.font.name = font_name
                    r_cap.font.size = Pt(9.5)
                    r_cap.font.italic = True
                    r_cap.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
            else:
                p_err = doc.add_paragraph()
                p_err.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_err.paragraph_format.space_before = Pt(4)
                p_err.paragraph_format.space_after = Pt(6)
                r_err = p_err.add_run(f"[{cap if cap else 'Ảnh kỹ thuật'} — Chưa tìm thấy tệp ảnh: {clean_path}]")
                r_err.font.name = font_name
                r_err.font.size = Pt(9.5)
                r_err.font.italic = True
                r_err.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            i += 1
            continue

        # Trích dẫn / Khung ghi chú / Disclaimer (> text)
        if line.strip().startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            full_quote = " ".join(quote_lines)
            p_q = doc.add_paragraph()
            p_q.paragraph_format.left_indent = Cm(0.75)
            p_q.paragraph_format.right_indent = Cm(0.5)
            p_q.paragraph_format.space_before = Pt(4)
            p_q.paragraph_format.space_after = Pt(8)
            p_q.paragraph_format.line_spacing = 1.2
            set_paragraph_left_border(p_q, color_hex="002060" if style_key == "bktechs" else "0070C0", sz="18")
            set_paragraph_shading(p_q, color_hex="F2F5F9")
            _add_formatted_runs(p_q, full_quote, font_name, cfg["body_size"] - 0.5, cfg["body_color"], force_italic=True)
            continue

        # CẤP 2 DANH SÁCH: Dấu cộng đầu dòng (+) hoặc thụt lề cấp 2
        m_plus = re.match(r"^(\s*)\+\s+(.*)$", line)
        m_sub_dash = re.match(r"^(\s{2,})[\-\*]\s+(.*)$", line)
        if m_plus or m_sub_dash:
            text_content = m_plus.group(2) if m_plus else m_sub_dash.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27)
            p.paragraph_format.first_line_indent = -Cm(0.4)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("+   ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h2_color"]
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            i += 1
            continue

        # CẤP 3 DANH SÁCH: Dấu chấm tròn (•) hoặc thụt lề sâu >= 4 spaces
        m_dot = re.match(r"^(\s*)•\s+(.*)$", line)
        m_sub3 = re.match(r"^(\s{4,})[\-\*\+]\s+(.*)$", line)
        if m_dot or m_sub3:
            text_content = m_dot.group(2) if m_dot else m_sub3.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.9)
            p.paragraph_format.first_line_indent = -Cm(0.35)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("•   ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["body_color"]
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            i += 1
            continue

        # CẤP 1 DANH SÁCH: Gạch đầu dòng (-) hoặc (*)
        m_dash = re.match(r"^(\s*)[\-\*–—]\s+(.*)$", line)
        if m_dash:
            text_content = m_dash.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.63)
            p.paragraph_format.first_line_indent = -Cm(0.35)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("–   ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h1_color"]
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            i += 1
            continue

        # DANH SÁCH THỨ TỰ / ĐIỂM KHOẢN: 1., 1), a), b)
        m_enum = re.match(r"^(\s*)(\d+[\.\)]|[a-zA-Z][\.\)])\s+(.*)$", line)
        if m_enum:
            prefix = m_enum.group(2)
            text_content = m_enum.group(3)
            indent_len = len(m_enum.group(1))
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27 if indent_len >= 2 else 0.75)
            p.paragraph_format.first_line_indent = -Cm(0.45)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run(f"{prefix} ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h1_color"]
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            i += 1
            continue

        # Đoạn văn bản thường / Công thức
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.2
        _add_formatted_runs(p, line.strip(), font_name, cfg["body_size"], cfg["body_color"])
        i += 1

    return nav_counter


def _add_formatted_runs(p, text: str, font_name: str, font_size: float, color: RGBColor, force_italic: bool = False):
    # Chuẩn hóa ký hiệu kỹ thuật trước
    text = normalize_engineering_symbols(text)

    # Quét cross-reference: "Xem chi tiết tại Phụ lục X", "Xem Phụ lục X", "theo Phụ lục X"
    cross_ref_pat = r'(Xem\s+(?:chi\s+tiết\s+tại\s+)?Phụ\s+lục\s+\d+|theo\s+Phụ\s+lục\s+\d+)'
    segments = re.split(cross_ref_pat, text, flags=re.IGNORECASE)

    for seg in segments:
        if not seg:
            continue
        m_xref = re.search(r'Phụ\s+lục\s+(\d+)', seg, flags=re.IGNORECASE)
        if m_xref and re.match(r'^(?:Xem|theo)', seg.strip(), flags=re.IGNORECASE):
            app_id = m_xref.group(1)
            add_cross_ref_hyperlink(p, seg, f"PHU_LUC_{app_id}", font_name, font_size)
            continue

        # Tokenize: **bold**, *italic*, `code`, $$formula$$, $formula$
        pattern = r"(\*\*.*?\*\*|\*[^\*]+?\*|`[^`]+?`|\$\$.*?\$\$|\$[^\$]+?\$)"
        parts = re.split(pattern, seg)

        for part in parts:
            if not part:
                continue
            is_bold = False
            is_italic = force_italic
            run_font = font_name
            run_size = font_size
            run_color = color

            if part.startswith("**") and part.endswith("**") and len(part) >= 4:
                clean_txt = part[2:-2]
                is_bold = True
            elif part.startswith("*") and part.endswith("*") and len(part) >= 2 and not part.startswith("**"):
                clean_txt = part[1:-1]
                is_italic = True
            elif part.startswith("`") and part.endswith("`") and len(part) >= 2:
                clean_txt = part[1:-1]
                run_font = "Consolas"
                run_size = font_size - 0.5
                run_color = RGBColor(0x00, 0x20, 0x60)
            elif (part.startswith("$$") and part.endswith("$$") and len(part) >= 4) or (part.startswith("$") and part.endswith("$") and len(part) >= 2):
                clean_txt = part[2:-2].strip() if part.startswith("$$") else part[1:-1].strip()
                omml_str = latex_to_omml(clean_txt)
                if omml_str:
                    try:
                        p._p.append(parse_xml(omml_str))
                        continue
                    except Exception:
                        pass
                # Fallback nếu OMML không khả dụng
                r = p.add_run(clean_txt)
                r.font.name = "Cambria Math"
                r.font.size = Pt(run_size)
                r.font.italic = True
                r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
                continue
            else:
                clean_txt = part

            r = p.add_run(clean_txt)
            r.font.name = run_font
            r.font.size = Pt(run_size)
            r.font.bold = is_bold
            r.font.italic = is_italic

            # Tô màu nổi bật cho từ khóa đánh giá
            if "[ĐẠT]" in clean_txt or "[OK]" in clean_txt or "PASSED" in clean_txt:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0x27, 0x6A, 0x3C)
            elif "[KHÔNG ĐẠT]" in clean_txt or "[FAILED]" in clean_txt:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            else:
                r.font.color.rgb = run_color


def build_report_from_markdown(
    input_md_path: str,
    output_docx_path: str,
    style_key: str = "bktechs",
    meta: dict = None,
    logo_path: str = None,
    appendices: list = None,
):
    meta = meta or {}
    with open(input_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Trích xuất toàn bộ cấu trúc Mục lục từ nội dung Markdown và các file Phụ lục
    toc_items = extract_toc_items_from_markdown(md_text, appendices=appendices, style_key=style_key)

    doc = docx.Document()
    if style_key == "bktechs":
        setup_bktechs_template(doc, meta, logo_path=logo_path, preview_toc_items=toc_items)
    else:
        setup_tvtk_template(doc, meta, preview_toc_items=toc_items)

    # 1. Render nội dung chính của Thuyết minh (Section 1)
    nav_counter = render_markdown_content(doc, md_text, style_key=style_key, nav_counter_start=1)

    # 2. Xử lý các Phụ lục tính toán đi kèm (--appendices) với Section Break & Đánh số trang độc lập
    if appendices:
        cfg = STYLE_CONFIGS[style_key]
        font_name = cfg["font_family"]

        for idx, app_file in enumerate(appendices, 1):
            if not os.path.exists(app_file):
                print(f"[CẢNH BÁO]: Không tìm thấy file phụ lục: {app_file}")
                continue

            with open(app_file, "r", encoding="utf-8") as af:
                raw_content = af.read().strip()

            base_name = os.path.splitext(os.path.basename(app_file))[0]
            fallback_name = base_name.replace("APPENDIX_", "").replace("_", " ").title()

            lines_app = raw_content.splitlines()
            first_h1 = None
            first_h2 = None
            remaining_lines = []
            for l in lines_app:
                if not first_h1 and l.strip().startswith("# "):
                    first_h1 = l.strip()[2:].strip()
                elif first_h1 and not first_h2 and l.strip().startswith("## "):
                    first_h2 = l.strip()[3:].strip()
                else:
                    remaining_lines.append(l)

            if first_h1 and first_h2:
                app_title = f"PHỤ LỤC {idx}: {first_h2.upper()} ({first_h1})"
            elif first_h1:
                app_title = f"PHỤ LỤC {idx}: {first_h1.upper()}"
            else:
                app_title = f"PHỤ LỤC {idx}: {fallback_name.upper()}"

            app_body_md = f"# {app_title}\n\n" + "\n".join(remaining_lines).strip()

            # --- TẠO SECTION MỚI (PAGE BREAK + SECTION BREAK) CHO TỪNG PHỤ LỤC ---
            sec_app = doc.add_section(WD_SECTION.NEW_PAGE)
            sec_app.top_margin = Cm(2.2) if style_key == "tvtk" else Cm(2.5)
            sec_app.bottom_margin = Cm(1.8)
            sec_app.left_margin = Cm(2.5) if style_key == "tvtk" else Cm(2.54)
            sec_app.right_margin = Cm(2.0)
            sec_app.different_first_page_header_footer = False
            sec_app.header.is_linked_to_previous = False
            sec_app.footer.is_linked_to_previous = False

            # Khởi động lại đánh số trang độc lập từ 1 cho mỗi Phụ lục
            restart_section_page_numbering(sec_app, start_at=1)

            # Cấu hình Header riêng cho Phụ lục
            ha = sec_app.header
            hpa = ha.paragraphs[0]
            hpa.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if style_key == "bktechs":
                set_paragraph_bottom_border(hpa, color_hex="FFC000", sz="12")
                rha1 = hpa.add_run(
                    f"{meta.get('company_name', 'BACH KHOA HO CHI MINH CITY SCIENCE TECHNOLOGY JSC - BKTECHS')}\n"
                )
                rha1.font.name = font_name
                rha1.font.size = Pt(9.5)
                rha1.font.bold = True
                rha1.font.color.rgb = RGBColor(0x00, 0x33, 0x99)
                rha2 = hpa.add_run(
                    f"Dự án: {meta.get('project_name', '[Tên Dự án]')}  —  {app_title}"
                )
                rha2.font.name = font_name
                rha2.font.size = Pt(9.5)
                rha2.font.italic = True
                rha2.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)
            else:
                set_paragraph_bottom_border(hpa, color_hex="002060", sz="8")
                rha = hpa.add_run(
                    f"{app_title}  |  {meta.get('project_name', '[Tên Công trình]')}"
                )
                rha.font.name = font_name
                rha.font.size = Pt(9.5)
                rha.font.italic = True
                rha.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

            # Cấu hình Footer riêng cho Phụ lục
            fa = sec_app.footer
            fpa = fa.paragraphs[0]
            if style_key == "bktechs":
                fpa.alignment = WD_ALIGN_PARAGRAPH.LEFT
                set_paragraph_top_border(fpa, color_hex="BFBFBF", sz="6")
                rfa1 = fpa.add_run(meta.get("org_short", "BKTECHS"))
                rfa1.font.name = font_name
                rfa1.font.size = Pt(9.5)
                rfa1.font.bold = True
                rfa1.font.color.rgb = RGBColor(0x00, 0x33, 0x99)

                rfa2 = fpa.add_run("  ||  ")
                rfa2.font.name = font_name
                rfa2.font.size = Pt(9.5)
                rfa2.font.bold = True
                rfa2.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

                rfa3 = fpa.add_run(meta.get("org_footer", "268 Lý Thường Kiệt, P.14, Q.10, TP.HCM  |  Tel: (028) 3864 7256"))
                rfa3.font.name = font_name
                rfa3.font.size = Pt(9.5)
                rfa3.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

                rfa4 = fpa.add_run(f"  ||  Phụ lục {idx} — Trang ")
                rfa4.font.name = font_name
                rfa4.font.size = Pt(9.5)
                rfa4.font.bold = True
                rfa4.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

                add_field(fpa, "PAGE", font_name=font_name, font_size=9.5, bold=True, color=RGBColor(0x00, 0x20, 0x60))
                rfa5 = fpa.add_run(" / ")
                rfa5.font.name = font_name
                rfa5.font.size = Pt(9.5)
                add_field(fpa, "SECTIONPAGES", font_name=font_name, font_size=9.5, bold=False, color=RGBColor(0x59, 0x59, 0x59))
            else:
                fpa.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                set_paragraph_top_border(fpa, color_hex="BFBFBF", sz="6")
                rfa = fpa.add_run(f"Phụ lục {idx} — Trang ")
                rfa.font.name = font_name
                rfa.font.size = Pt(9.5)
                rfa.font.italic = True
                add_field(fpa, "PAGE", font_name=font_name, font_size=9.5, italic=True)
                rfa_sep = fpa.add_run(" / ")
                rfa_sep.font.name = font_name
                rfa_sep.font.size = Pt(9.5)
                rfa_sep.font.italic = True
                add_field(fpa, "SECTIONPAGES", font_name=font_name, font_size=9.5, italic=True)

            # Render nội dung phụ lục vào section mới
            nav_counter = render_markdown_content(doc, app_body_md, style_key=style_key, nav_counter_start=nav_counter)

    os.makedirs(os.path.dirname(os.path.abspath(output_docx_path)), exist_ok=True)
    doc.save(output_docx_path)
    return output_docx_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xuất Hồ sơ Thuyết minh Tính toán theo 2 Bộ Chuẩn (BKTECHS / TVTK)")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file Markdown đầu vào (.md)")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file Word đầu ra (.docx)")
    parser.add_argument(
        "--appendices",
        "-a",
        nargs="+",
        default=[],
        help="Danh sách các file Markdown Phụ lục tính toán (.md) cần tích hợp trực tiếp vào Thuyết minh",
    )
    parser.add_argument(
        "--style",
        "-s",
        choices=["bktechs", "tvtk"],
        default="bktechs",
        help="Chọn bộ chuẩn trình bày: 'bktechs' (Bộ 1 - Chuẩn BKTECHS) hoặc 'tvtk' (Bộ 2 - Chuẩn TVTK Đa Hạng mục)",
    )
    parser.add_argument("--project", "--cover", "-c", dest="project", default="[Tên Dự án / Công trình]", help="Tên Dự án / Công trình")
    parser.add_argument("--item", "--title", "-t", dest="item", default="[Tên Hạng mục Tính toán]", help="Tên Hạng mục")
    parser.add_argument("--client", "--owner", dest="client", default="[Tên Chủ đầu tư]", help="Tên Chủ đầu tư")
    parser.add_argument("--consultant", default=None, help="Tên Đơn vị Tư vấn Thiết kế / Thẩm tra")
    parser.add_argument("--location", default="[Địa điểm xây dựng]", help="Địa điểm xây dựng")
    parser.add_argument("--mode", choices=["full", "standard"], default="full", help="Chế độ tương thích ngược (full/standard)")
    parser.add_argument("--no-cover", action="store_true", help="Tùy chọn bỏ qua trang bìa")
    parser.add_argument("--logo", default=None, help="Đường dẫn ảnh Logo (tùy chọn)")
    args = parser.parse_args()

    default_logo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "bktechs_logo.png")
    logo_to_use = args.logo if args.logo else (default_logo if os.path.exists(default_logo) else None)

    meta_info = {
        "project_name": args.project,
        "item_name": args.item,
        "client_name": args.client,
        "location": args.location,
    }
    if args.consultant:
        meta_info["company_name"] = args.consultant
    out = build_report_from_markdown(
        args.input,
        args.output,
        style_key=args.style,
        meta=meta_info,
        logo_path=logo_to_use,
        appendices=args.appendices,
    )
    print(f"Đã xuất hồ sơ thuyết minh ({args.style.upper()}): {out}")
