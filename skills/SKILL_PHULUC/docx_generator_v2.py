#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX GENERATOR V2.1 (R&D PUBLICATION EDITION) — BỘ ENGINE XUẤT HỒ SƠ THUYẾT MINH TÍNH TOÁN KẾT CẤU & ĐỊA KỸ THUẬT
Hỗ trợ lựa chọn 2 Bộ Chuẩn Trình Bày & Bố Trí Chapter trích xuất từ `THUYET MINH MAU`:
  1. `--style bktechs` : BỘ CHUẨN 1 — Phong cách BKTECHS (Viện - Trường / Thẩm tra / TMTT Chuyên sâu)
  2. `--style tvtk`    : BỘ CHUẨN 2 — Phong cách TVTK Đa Hạng Mục (9 Chương Cơ sở Chung + N Chương Phụ lục Hạng mục)

Nâng cấp v2.1 (2026-10-22):
  - Khổ giấy chuẩn ISO A4 (21.00 x 29.70 cm) & Lề đóng gáy Hồ sơ Xây dựng Việt Nam (Trái 2.8 cm, Phải 1.8 cm, Vùng in 16.4 cm).
  - Căn đều 2 lề (Justify) cho văn bản thuyết minh & danh sách đa cấp; chống ngắt dòng vô lý giữa số - đơn vị và mũi tên `→ [ĐẠT]`.
  - Hạ chỉ số dưới tự động (Subscript) cho ký hiệu cơ học kết cấu (R_b, R_bt, M_Ed, N_Ed, γ_f, c_nom, η_coc...) và chỉ tô xanh đậm riêng nhãn `[ĐẠT]`.
  - Bộ biên dịch LaTeX sang Native Word OMML (`<m:oMath>`) thuần Python không phụ thuộc cứng vào `pylatexenc`.
  - Tôn trọng căn lề cột bảng Markdown (`:---:`, `---:`, `:---`) và sửa lỗi tô vàng tràn bảng / căn giữa nhầm cột 0.
  - Bố trí Chapter / Phần / Phụ lục tự động ngắt trang / phân khu Section Break và sửa lỗi đánh số trùng dưới Phần III.
  - Trang Mục lục động tích hợp trường `PAGEREF` thực tế kèm `right_indent` chống tràn chữ đè số trang.
"""

import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
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
        "table_size": 10.5,
        "h1_color": RGBColor(0x00, 0x20, 0x60),      # Xanh Navy đậm (#002060)
        "h2_color": RGBColor(0x00, 0x70, 0xC0),      # Xanh Lam sáng (#0070C0)
        "h3_color": RGBColor(0x1F, 0x4E, 0x79),      # Xanh đậm (#1F4E79)
        "body_color": RGBColor(0x1A, 0x1A, 0x1A),
        "table_header_fill": "002060",               # Nền xanh Navy đậm, chữ trắng
        "table_header_text": RGBColor(0xFF, 0xFF, 0xFF),
        "table_alt_fill": "F4F7FA",
        "table_highlight_fill": "FFF2CC",            # Vàng nhạt cho dòng Tổng kết bảng
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
        "table_header_fill": "B4C6E7",               # Nền xanh lam nhạt chuẩn mẫu TVTK
        "table_header_text": RGBColor(0x00, 0x20, 0x60),
        "table_alt_fill": "F9FAFC",
        "table_highlight_fill": "E2EFDA",            # Xanh lá nhạt cho dòng Tổng kết bảng
        "dot_after_number": False,                   # 1 / 1.1 / 1.1.1
    },
}

# Khổ giấy A4 chuẩn ISO 216 (21.00 x 29.70 cm) & Lề đóng gáy Hồ sơ Kỹ thuật Việt Nam
A4_WIDTH_CM = 21.0
A4_HEIGHT_CM = 29.7
MARGIN_LEFT_CM = 2.80    # Chừa gáy đóng hồ sơ 2.80 cm
MARGIN_RIGHT_CM = 1.80   # Lề phải 1.80 cm -> Bề rộng vùng in thực tế = 16.40 cm (9298 twips)
PRINT_WIDTH_TWIPS = 9298


# ==============================================================================
# CÁC HÀM TIỆN ÍCH OPENXML (BORDERS, SHADING, PAGE FIELDS, A4 GEOMETRY)
# ==============================================================================
def apply_a4_geometry(section, top_cm=2.4, bottom_cm=1.8, left_cm=MARGIN_LEFT_CM, right_cm=MARGIN_RIGHT_CM):
    """Áp đặt chuẩn khổ giấy ISO A4 (21.0 x 29.7 cm) và khoảng cách Header/Footer chuẩn in ấn."""
    section.page_width = Cm(A4_WIDTH_CM)
    section.page_height = Cm(A4_HEIGHT_CM)
    section.top_margin = Cm(top_cm)
    section.bottom_margin = Cm(bottom_cm)
    section.left_margin = Cm(left_cm)
    section.right_margin = Cm(right_cm)
    section.header_distance = Cm(1.1)
    section.footer_distance = Cm(1.1)


def set_east_asia_font(style_or_run, font_name: str):
    """Đảm bảo tiếng Việt & ký hiệu kỹ thuật hiển thị đồng nhất trên mọi phiên bản MS Word / LibreOffice."""
    rPr = style_or_run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:eastAsia"), font_name)
    rFonts.set(qn("w:cs"), font_name)


def set_cell_shading(cell, color_hex: str):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def set_cell_margins(cell, top=90, bottom=90, left=130, right=130):
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


def set_table_full_width(table, width_twips=PRINT_WIDTH_TWIPS):
    """Cố định chiều rộng bảng phủ vừa khít vùng in 16.40 cm của trang A4."""
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(width_twips))
    tblW.set(qn("w:type"), "dxa")


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


def interpolate_meta_placeholders(md_text: str, meta: dict) -> str:
    """Thay thế các biến mẫu {{project_name}}, {{location}}, {{client_name}}, {{item_name}} trong Markdown."""
    if not md_text or not meta:
        return md_text
    replacements = {
        "project_name": meta.get("project_name", ""),
        "item_name": meta.get("item_name", ""),
        "client_name": meta.get("client_name", ""),
        "location": meta.get("location", ""),
        "company_name": meta.get("company_name", "BKTECHS"),
        "gfa": meta.get("gfa", "24.500"),
        "so_tang": meta.get("so_tang", "25"),
        "chieu_cao": meta.get("chieu_cao", "85.5"),
        "h_dinh_lim": meta.get("h_dinh_lim", "171.0"),
        "h_tang_lim": meta.get("h_tang_lim", "7.2"),
    }
    for k, v in replacements.items():
        if v and not str(v).startswith("["):
            md_text = re.sub(r"\{\{\s*" + re.escape(k) + r"\s*\}\}", str(v), md_text)
    return md_text


def normalize_engineering_symbols(text: str) -> str:
    """
    Chuẩn hóa ký hiệu kỹ thuật, toán học và gắn Non-Breaking Space (\u00A0)
    để chống rớt dòng giữa con số - đơn vị và mũi tên kết luận `→ [ĐẠT]`.
    """
    if not text:
        return text

    # Thay thế đường kính thép: %%c, Phi, phi, fi trước số -> Φ
    text = re.sub(r"(?:%%c|[Pp]hi|fi)\s*([0-9]+(?:\.[0-9]+)?)", r"Φ\1", text)

    # Chuẩn hóa trạng thái kiểm tra trước khi xử lý mũi tên
    text = re.sub(r"\[(?:OK|DAT|ĐẠT)\]", "[ĐẠT]", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:FAIL|FAILED|KHONG DAT|KHÔNG ĐẠT)\]", "[KHÔNG ĐẠT]", text, flags=re.IGNORECASE)

    # Mũi tên suy ra / kết luận: -> và => chuyển thành → / ⇒ kèm Non-Breaking Space trước [ĐẠT]
    text = re.sub(r"\s*->\s*(\[(?:ĐẠT|KHÔNG ĐẠT)\])", " \u00A0→\u00A0\\1", text)
    text = re.sub(r"\s*=>\s*(\[(?:ĐẠT|KHÔNG ĐẠT)\])", " \u00A0⇒\u00A0\\1", text)
    text = re.sub(r"^=>\s*", "⇒ ", text)
    text = re.sub(r"\s*->\s*", " → ", text)
    text = re.sub(r"\s*=>\s*", " ⇒ ", text)

    # Toán học & so sánh
    text = re.sub(r"<=\s*", "≤ ", text)
    text = re.sub(r">=\s*", "≥ ", text)
    text = re.sub(r"\+-\s*", "±", text)
    text = re.sub(r"\\le\b", "≤", text)
    text = re.sub(r"\\ge\b", "≥", text)
    text = re.sub(r"\\pm\b", "±", text)
    text = re.sub(r"\\times\b", "×", text)

    # Đơn vị kỹ thuật xây dựng (kèm Non-Breaking Space giữa số và đơn vị)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kN/?m2\b", "\\1\u00A0kN/m²", text)
    text = re.sub(r"\bkN/?m2\b", "kN/m²", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kN/?m3\b", "\\1\u00A0kN/m³", text)
    text = re.sub(r"\bkN/?m3\b", "kN/m³", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*daN/?cm2\b", "\\1\u00A0daN/cm²", text)
    text = re.sub(r"\bdaN/?cm2\b", "daN/cm²", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kN\.?m/m\b", "\\1\u00A0kN.m/m", text)
    text = re.sub(r"\bkNm/m\b", "kN.m/m", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kN\.?m\b", "\\1\u00A0kN.m", text)
    text = re.sub(r"\bkNm\b", "kN.m", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*MPa\b", "\\1\u00A0MPa", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kPa\b", "\\1\u00A0kPa", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kN\b", "\\1\u00A0kN", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mm2\b", "\\1\u00A0mm²", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*cm2\b", "\\1\u00A0cm²", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*m2\b", "\\1\u00A0m²", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*m3\b", "\\1\u00A0m³", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mm3\b", "\\1\u00A0mm³", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*cm3\b", "\\1\u00A0cm³", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mm\b", "\\1\u00A0mm", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*cm\b", "\\1\u00A0cm", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*m\b", "\\1\u00A0m", text)

    # Kích thước tiết diện: 200x400 hoặc 200*400 -> 200 × 400
    text = re.sub(r"(\d+)\s*[xX]\s*(\d+)", r"\1 × \2", text)
    text = re.sub(r"(\d+)\s*\*\s*(\d+)", r"\1 × \2", text)

    # Góc / độ
    text = re.sub(r"(\d+)\s*(?:độ|\^o|\\circ)\s*C\b", r"\1°C", text)
    text = re.sub(r"(\d+)\s*(?:độ|\^o|\\circ)\b", r"\1°", text)

    # Ký hiệu thẻ sub / sup trong markdown
    text = re.sub(r"<sup>2</sup>", "²", text)
    text = re.sub(r"<sup>3</sup>", "³", text)

    # Ký tự Hy Lạp thông dụng
    greek_replacements = [
        (r"\b[Ee]ta\b", "η"),
        (r"\b[Ee]ta_([A-Za-z0-9_]+)", r"η_\1"),
        (r"\b[Ss]igma\b", "σ"),
        (r"\b[Tt]au\b", "τ"),
        (r"\b[Gg]amma\b", "γ"),
        (r"\b[Aa]lpha\b", "α"),
        (r"\b[Bb]eta\b", "β"),
        (r"\b[Dd]elta\b", "δ"),
        (r"\b[Dd]elta_([A-Za-z0-9_]+)", r"δ_\1"),
        (r"\bphi\s*=", "φ ="),
        (r"\\eta\b", "η"),
        (r"\\sigma\b", "σ"),
        (r"\\tau\b", "τ"),
        (r"\\gamma\b", "γ"),
        (r"\\alpha\b", "α"),
        (r"\\beta\b", "β"),
        (r"\\delta\b", "δ"),
        (r"\\Delta\b", "Δ"),
        (r"\\varphi\b", "φ"),
        (r"\\phi\b", "φ"),
        (r"\\Phi\b", "Φ"),
    ]
    for pattern, rep in greek_replacements:
        text = re.sub(pattern, rep, text)

    return text


# ==============================================================================
# BỘ CHUYỂN ĐỔI CÔNG THỨC TOÁN LATEX SANG NATIVE WORD OMML (PURE PYTHON + FALLBACK)
# ==============================================================================
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
    "degree": "°", "circ": "°", "prime": "′", "rightarrow": "→", "Rightarrow": "⇒",
}


def _extract_braced_group(s: str, pos: int):
    """Đọc nội dung trong cặp ngoặc nhọn { ... } cân bằng bắt đầu tại vị trí pos."""
    while pos < len(s) and s[pos].isspace():
        pos += 1
    if pos >= len(s):
        return "", pos
    if s[pos] != "{":
        # Nếu không có ngoặc nhọn, lấy 1 ký tự hoặc 1 macro
        if s[pos] == "\\":
            m = re.match(r"^\\[A-Za-z]+", s[pos:])
            if m:
                return m.group(0), pos + len(m.group(0))
        return s[pos], pos + 1
    depth = 0
    start = pos + 1
    i = pos
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return s[start:], len(s)


def _pure_latex_to_omml_inner(expr: str) -> str:
    """Bộ phân tích cú pháp LaTeX đệ quy thuần Python sang chuỗi OpenXML OMML (không cần pylatexenc)."""
    s = expr.strip()
    out = []
    i = 0

    def make_run(txt: str, normal_text: bool = False) -> str:
        if not txt:
            return ""
        esc = html.escape(txt)
        if normal_text:
            return f"<m:r><m:rPr><m:nor/></m:rPr><m:t>{esc}</m:t></m:r>"
        return f"<m:r><m:t>{esc}</m:t></m:r>"

    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue

        # Xử lý lệnh LaTeX \macro
        if ch == "\\":
            m = re.match(r"^\\([A-Za-z]+)", s[i:])
            if m:
                cmd = m.group(1)
                i += len(m.group(0))
                if cmd in ("left", "right", "displaystyle", "quad", "qquad"):
                    if cmd in ("quad", "qquad"):
                        out.append(make_run("  ", normal_text=True))
                    continue
                if cmd == "frac":
                    num_s, i = _extract_braced_group(s, i)
                    den_s, i = _extract_braced_group(s, i)
                    node_xml = f"<m:f><m:num>{_pure_latex_to_omml_inner(num_s)}</m:num><m:den>{_pure_latex_to_omml_inner(den_s)}</m:den></m:f>"
                elif cmd == "sqrt":
                    # Bỏ qua tham số tùy chọn [n] nếu có
                    while i < len(s) and s[i].isspace():
                        i += 1
                    deg_xml = "<m:radPr><m:degHide w:val=\"1\"/></m:radPr><m:deg/>"
                    if i < len(s) and s[i] == "[":
                        end_b = s.find("]", i)
                        if end_b != -1:
                            deg_str = s[i+1:end_b]
                            deg_xml = f"<m:deg>{_pure_latex_to_omml_inner(deg_str)}</m:deg>"
                            i = end_b + 1
                    rad_s, i = _extract_braced_group(s, i)
                    node_xml = f"<m:rad>{deg_xml}<m:e>{_pure_latex_to_omml_inner(rad_s)}</m:e></m:rad>"
                elif cmd in ("text", "mathrm", "operatorname", "mbox", "textbf"):
                    txt_s, i = _extract_braced_group(s, i)
                    node_xml = make_run(txt_s, normal_text=True)
                elif cmd in GREEK_AND_MATH_SYMBOLS:
                    node_xml = make_run(GREEK_AND_MATH_SYMBOLS[cmd])
                else:
                    node_xml = make_run(cmd)
            else:
                # Ký tự đặc biệt sau dấu \ như \, \; \%
                if i + 1 < len(s):
                    node_xml = make_run(s[i+1])
                    i += 2
                else:
                    i += 1
                    continue
        elif ch == "{":
            grp_s, i = _extract_braced_group(s, i)
            node_xml = _pure_latex_to_omml_inner(grp_s)
        else:
            # Đọc 1 token cơ sở (chữ cái, con số, hoặc toán tử đơn)
            m_tok = re.match(r"^([A-Za-z0-9\u0370-\u03ff\.]+|[^A-Za-z0-9\u0370-\u03ff\s\\\{\}_\^])", s[i:])
            if m_tok:
                tok = m_tok.group(1)
                i += len(tok)
                node_xml = make_run(tok)
            else:
                i += 1
                continue

        # Kiểm tra xem ngay sau node_xml có chỉ số dưới (_) hoặc số mũ (^) không
        while i < len(s) and s[i].isspace():
            i += 1
        sub_xml, sup_xml = None, None
        for _ in range(2):
            while i < len(s) and s[i].isspace():
                i += 1
            if i < len(s) and s[i] == "_":
                i += 1
                sub_s, i = _extract_braced_group(s, i)
                sub_xml = _pure_latex_to_omml_inner(sub_s)
            elif i < len(s) and s[i] == "^":
                i += 1
                sup_s, i = _extract_braced_group(s, i)
                sup_xml = _pure_latex_to_omml_inner(sup_s)
        if sub_xml is not None and sup_xml is not None:
            node_xml = f"<m:sSubSup><m:e>{node_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>"
        elif sub_xml is not None:
            node_xml = f"<m:sSub><m:e>{node_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>"
        elif sup_xml is not None:
            node_xml = f"<m:sSup><m:e>{node_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>"

        out.append(node_xml)

    return "".join(out)


def latex_to_omml(latex_code: str, display_mode: bool = False):
    """Chuyển đổi công thức LaTeX ($...$ hoặc $$...$$) sang chuỗi OpenXML OMML hoàn chỉnh."""
    if not latex_code:
        return None
    code = latex_code.strip()
    if code.startswith("$$") and code.endswith("$$") and len(code) >= 4:
        code = code[2:-2].strip()
    elif code.startswith("$") and code.endswith("$") and len(code) >= 2:
        code = code[1:-1].strip()

    try:
        inner_omml = _pure_latex_to_omml_inner(code)
        if not inner_omml.strip():
            return None
        ns_m = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        if display_mode:
            return f"<m:oMathPara {ns_m}><m:oMath>{inner_omml}</m:oMath></m:oMathPara>"
        return f"<m:oMath {ns_m}>{inner_omml}</m:oMath>"
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
        r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s"/><w:sz w:val="%d"/><w:color w:val="0070C0"/><w:u w:val="single"/></w:rPr><w:t>%s</w:t></w:r>'
        % (nsdecls("w"), font_name, font_name, font_name, int(font_size * 2), html.escape(text))
    )
    hyperlink.append(r)
    paragraph._p.append(hyperlink)


def add_field(paragraph, field_text: str, default_val: str = "1", font_name="Times New Roman", font_size=10, bold=False, italic=False, color=None):
    run = paragraph.add_run()
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    set_east_asia_font(run, font_name)
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> %s </w:instrText>' % (nsdecls("w"), field_text))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    t = parse_xml(r"<w:t %s>%s</w:t>" % (nsdecls("w"), html.escape(str(default_val))))
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
    cleaned = re.sub(r"^(?:CHƯƠNG|MỤC)\s+\d+[\.\:\-\s]*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", cleaned.strip())
    return cleaned.strip()


def is_redundant_frontmatter_heading(line_idx: int, level: int, raw_text: str) -> bool:
    """Nhận diện các dòng tiêu đề phụ lặp lại thông tin bìa ở 8 dòng đầu file Markdown."""
    if line_idx > 10:
        return False
    up = raw_text.upper().strip()
    if level == 1 and any(k in up for k in ["THUYẾT MINH TÍNH TOÁN", "BÁO CÁO THẨM TRA", "THUYẾT MINH BIỆN PHÁP"]):
        return True
    if any(up.startswith(k) for k in ["CÔNG TRÌNH:", "ĐỊA ĐIỂM:", "DỰ ÁN:", "CHỦ ĐẦU TƯ:", "HẠNG MỤC:"]):
        return True
    return False


def extract_toc_items_from_markdown(md_text: str, appendices: list = None, style_key: str = "bktechs") -> list:
    """
    Trích xuất toàn bộ cấu trúc mục lục (Phần, Chương, Mục 1, Mục 2, Phụ lục)
    để tự động sinh Trang Mục Lục hoàn chỉnh kèm trường PAGEREF động và liên kết chéo nội bộ.
    """
    dot = "." if style_key == "bktechs" else ""
    lines = md_text.splitlines()
    toc_items = []
    h_counts = [0, 0, 0]
    bm_idx = 1

    pat_part = r"^(?:PHẦN\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\b|CÁC\s+PHỤ\s+LỤC)"
    pat_app = r"^(?:PHỤ\s+LỤC|APPENDIX)\s+\d+"
    curr_part_roman = ""
    is_under_app = False
    curr_app_num = 1
    content_line_counter = 0

    for idx_line, line in enumerate(lines):
        if line.strip():
            content_line_counter += 1
        m = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if not m:
            continue
        level = len(m.group(1))
        raw = m.group(2).strip()

        if is_redundant_frontmatter_heading(idx_line, level, raw):
            continue

        is_part = bool(re.match(pat_part, raw, flags=re.IGNORECASE))
        is_app = bool(re.match(pat_app, raw, flags=re.IGNORECASE))

        if is_part:
            m_rom = re.match(r"^PHẦN\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", raw.strip(), flags=re.IGNORECASE)
            curr_part_roman = m_rom.group(1).upper() if m_rom else ""
            h_counts = [0, 0, 0]
            is_under_app = False
            est_page = max(1, (content_line_counter // 38) + 1)
            toc_items.append({
                "level": 1,
                "title": raw.upper(),
                "page": str(est_page),
                "bookmark": f"TOC_NAV_{bm_idx}",
                "is_part": True,
                "is_app": False,
            })
            bm_idx += 1
            continue

        if is_app:
            m_a = re.search(r"(?:PHỤ\s+LỤC|APPENDIX)\s+(\d+)", raw, flags=re.IGNORECASE)
            curr_app_num = int(m_a.group(1)) if m_a else 1
            is_under_app = True
            h_counts[0] = curr_app_num
            h_counts[1] = 0
            h_counts[2] = 0
            est_page = max(1, (content_line_counter // 36) + 1)
            toc_items.append({
                "level": 2,
                "title": raw.upper(),
                "page": str(est_page),
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
        elif level == 2:
            if curr_part_roman == "III" and not is_under_app:
                h_counts[1] += 1
                h_counts[2] = 0
                disp = f"III.{h_counts[1]}{dot} {cleaned}"
            else:
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

        est_page = max(1, (content_line_counter // 36) + 1)
        toc_items.append({
            "level": level,
            "title": disp,
            "page": str(est_page),
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
    Tạo Trang Mục Lục hoàn chỉnh chuẩn xuất bản:
    - Bật cờ updateFields="true" trong settings.xml
    - Render từng mục lục kèm right_indent=1.1cm (chống tràn chữ đè lên số trang),
      tab stop dot-leader tại 9298 twips (16.40 cm) và trường PAGEREF động trỏ tới Bookmark thực tế.
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
        add_field(p, 'TOC \\o "1-3" \\h \\z \\u', default_val="[Nhấn chuột phải chọn Update Field (F9) để cập nhật Mục lục]", font_name=font_name, font_size=11)
        return

    # Dòng tiêu đề cột phân cách (Nội dung ... Trang)
    p_header = doc.add_paragraph()
    p_header.paragraph_format.space_before = Pt(2)
    p_header.paragraph_format.space_after = Pt(6)
    pPr_h = p_header._p.get_or_add_pPr()
    pPr_h.append(parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="none" w:pos="%d"/></w:tabs>' % (nsdecls("w"), PRINT_WIDTH_TWIPS)))
    rh1 = p_header.add_run("Đề mục Chương / Nội dung Thuyết minh & Phụ lục")
    rh1.font.name = font_name
    rh1.font.size = Pt(10.5)
    rh1.font.bold = True
    rh1.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
    set_east_asia_font(rh1, font_name)
    p_header.add_run("\t")
    rh2 = p_header.add_run("Trang")
    rh2.font.name = font_name
    rh2.font.size = Pt(10.5)
    rh2.font.bold = True
    rh2.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
    set_east_asia_font(rh2, font_name)
    set_paragraph_bottom_border(p_header, color_hex="0070C0", sz="8")

    # Render danh sách Mục Lục chi tiết với tab stop dot leader và trường PAGEREF động
    for item in toc_items:
        lvl = item.get("level", 2)
        title = normalize_engineering_symbols(item.get("title", ""))
        page_str = item.get("page", "1")
        anchor = item.get("bookmark", "")
        is_part = item.get("is_part", False)
        is_app = item.get("is_app", False)

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6 if is_part else (3 if (lvl == 1 or is_app) else 1.5))
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Cm(0 if is_part or lvl == 1 else (0.45 if lvl == 2 else 0.90))
        # Ngắt dòng tiêu đề sớm trước cột số trang 1.15 cm để không bao giờ dính chữ vào số trang
        p.paragraph_format.right_indent = Cm(0.0)

        pPr = p._p.get_or_add_pPr()
        # Đặt 1 tab dừng dot leader tại sát lề phải 16.40 cm (9298 twips)
        tab_xml = parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="dot" w:pos="%d"/></w:tabs>' % (nsdecls("w"), PRINT_WIDTH_TWIPS))
        pPr.append(tab_xml)

        if anchor:
            hl = parse_xml(r'<w:hyperlink %s w:anchor="%s" w:history="1"/>' % (nsdecls("w"), anchor))
        else:
            hl = parse_xml(r'<w:hyperlink %s w:history="1"/>' % nsdecls("w"))

        esc_title = html.escape(title)
        is_bold = (is_part or is_app or lvl == 1)
        is_italic = (lvl == 3)
        font_size_half_pt = 22 if is_part else (21 if (lvl == 1 or is_app) else 20)
        text_color = "002060" if is_part else ("003399" if (lvl == 1 or is_app) else "1A1A1A")

        r_title_xml = parse_xml(
            r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s"/><w:sz w:val="%d"/>%s%s<w:color w:val="%s"/></w:rPr><w:t>%s</w:t></w:r>'
            % (
                nsdecls("w"),
                font_name,
                font_name,
                font_name,
                font_size_half_pt,
                r"<w:b/>" if is_bold else "",
                r"<w:i/>" if is_italic else "",
                text_color,
                esc_title,
            )
        )
        hl.append(r_title_xml)

        # Tab dot leader
        hl.append(parse_xml(r"<w:r %s><w:tab/></w:r>" % nsdecls("w")))

        # Trường PAGEREF động trỏ tới Bookmark để MS Word / LibreOffice tự động điền đúng số trang thực
        if anchor and not str(page_str).startswith("P"):
            fld_pageref = parse_xml(
                r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s"/><w:sz w:val="%d"/>%s<w:color w:val="%s"/></w:rPr>'
                r'<w:fldChar w:fldCharType="begin"/></w:r>'
                % (nsdecls("w"), font_name, font_name, font_name, 22 if is_bold else 21, r"<w:b/>" if is_bold else "", "002060" if is_bold else "333333")
            )
            fld_instr = parse_xml(
                r'<w:r %s><w:instrText xml:space="preserve"> PAGEREF %s \h </w:instrText></w:r>' % (nsdecls("w"), anchor)
            )
            fld_sep = parse_xml(r'<w:r %s><w:fldChar w:fldCharType="separate"/></w:r>' % nsdecls("w"))
            fld_val = parse_xml(
                r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s"/><w:sz w:val="%d"/>%s<w:color w:val="%s"/></w:rPr><w:t>%s</w:t></w:r>'
                % (nsdecls("w"), font_name, font_name, font_name, 22 if is_bold else 21, r"<w:b/>" if is_bold else "", "002060" if is_bold else "333333", html.escape(str(page_str)))
            )
            fld_end = parse_xml(r'<w:r %s><w:fldChar w:fldCharType="end"/></w:r>' % nsdecls("w"))
            hl.append(fld_pageref)
            hl.append(fld_instr)
            hl.append(fld_sep)
            hl.append(fld_val)
            hl.append(fld_end)
        else:
            r_page_xml = parse_xml(
                r'<w:r %s><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s"/><w:sz w:val="%d"/>%s<w:color w:val="%s"/></w:rPr><w:t>%s</w:t></w:r>'
                % (
                    nsdecls("w"),
                    font_name,
                    font_name,
                    font_name,
                    22 if is_bold else 21,
                    r"<w:b/>" if is_bold else "",
                    "002060" if is_bold else "333333",
                    html.escape(str(page_str)),
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
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_before = Pt(2)
    normal.paragraph_format.space_after = Pt(5)
    set_east_asia_font(normal, font_name)

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
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_east_asia_font(st, font_name)

    # --------------------------------------------------------------------------
    # SECTION 0: BÌA CHÍNH (TRANG 1) + BÌA PHỤ KÝ DUYỆT (TRANG 2) + MỤC LỤC (TRANG 3)
    # --------------------------------------------------------------------------
    sec0 = doc.sections[0]
    apply_a4_geometry(sec0, top_cm=1.6, bottom_cm=1.6, left_cm=MARGIN_LEFT_CM, right_cm=MARGIN_RIGHT_CM)
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
    set_table_full_width(ribbon_top)
    c_rt = ribbon_top.cell(0, 0)
    set_cell_shading(c_rt, "002060")
    set_cell_margins(c_rt, top=45, bottom=45, left=80, right=80)
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
        p_logo.paragraph_format.space_before = Pt(20)
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
    p_title.paragraph_format.space_before = Pt(14)
    p_title.paragraph_format.space_after = Pt(6)
    rt = p_title.add_run(meta.get("report_type", "THUYẾT MINH TÍNH TOÁN KẾT CẤU"))
    rt.font.name = font_name
    rt.font.size = Pt(24)
    rt.font.bold = True
    rt.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(20)
    set_paragraph_bottom_border(p_sub, color_hex="FFC000", sz="18")
    rsub = p_sub.add_run(f"GIAI ĐOẠN: {meta.get('phase', 'THIẾT KẾ BẢN VẼ THI CÔNG (BVTC)')}")
    rsub.font.name = font_name
    rsub.font.size = Pt(13)
    rsub.font.bold = True
    rsub.font.italic = True
    rsub.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)

    # Bảng thông tin Dự án / Hạng mục / Chủ đầu tư trên bìa (Rộng 5.2 + 11.2 = 16.4 cm vừa khít vùng in A4)
    info_tbl = doc.add_table(rows=5, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(info_tbl)
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
        set_cell_margins(c0, top=115, bottom=115, left=140, right=100)
        set_cell_margins(c1, top=115, bottom=115, left=140, right=140)
        set_cell_shading(c0, "F2F5F9")
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r0 = p0.add_run(label)
        r0.font.name = font_name
        r0.font.size = Pt(11.5)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1_val = p1.add_run(val)
        r1_val.font.name = font_name
        r1_val.font.size = Pt(11.5)
        r1_val.font.bold = (idx in (0, 1))
        r1_val.font.italic = (idx == 1)
        r1_val.font.color.rgb = RGBColor(0x00, 0x33, 0x99) if idx == 0 else RGBColor(0x1A, 0x1A, 0x1A)

    # Chân bìa Trang 1
    p_city = doc.add_paragraph()
    p_city.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_city.paragraph_format.space_before = Pt(48)
    p_city.paragraph_format.space_after = Pt(6)
    rcity = p_city.add_run(meta.get("place_date", "TP. HỒ CHÍ MINH — NĂM 2026"))
    rcity.font.name = font_name
    rcity.font.size = Pt(12)
    rcity.font.bold = True
    rcity.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    ribbon_bot = doc.add_table(rows=1, cols=1)
    ribbon_bot.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(ribbon_bot)
    c_rb = ribbon_bot.cell(0, 0)
    set_cell_shading(c_rb, "002060")
    set_cell_margins(c_rb, top=40, bottom=40, left=80, right=80)
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

    p_sig_lbl = doc.add_paragraph()
    p_sig_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sig_lbl.paragraph_format.space_before = Pt(8)
    p_sig_lbl.paragraph_format.space_after = Pt(6)
    r_sl = p_sig_lbl.add_run("BẢNG TRÁCH NHIỆM PHÁP LÝ & KIỂM SOÁT CHẤT LƯỢNG HỒ SƠ:")
    r_sl.font.name = font_name
    r_sl.font.size = Pt(11.5)
    r_sl.font.bold = True
    r_sl.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    sig_tbl = doc.add_table(rows=4, cols=3)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(sig_tbl)
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

    p_rep_lbl = doc.add_paragraph()
    p_rep_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_rep_lbl.paragraph_format.space_before = Pt(18)
    p_rep_lbl.paragraph_format.space_after = Pt(6)
    r_rl = p_rep_lbl.add_run("XÁC NHẬN PHÁP LÝ CỦA ĐƠN VỊ TƯ VẤN & CHỦ ĐẦU TƯ:")
    r_rl.font.name = font_name
    r_rl.font.size = Pt(11.5)
    r_rl.font.bold = True
    r_rl.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    rep_tbl = doc.add_table(rows=2, cols=2)
    rep_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(rep_tbl)
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
    p_toc_title.paragraph_format.space_before = Pt(4)
    p_toc_title.paragraph_format.space_after = Pt(8)
    set_paragraph_bottom_border(p_toc_title, color_hex="0070C0", sz="12")
    rtoc = p_toc_title.add_run("MỤC LỤC NỘI DUNG & PHỤ LỤC")
    rtoc.font.name = font_name
    rtoc.font.size = Pt(16)
    rtoc.font.bold = True
    rtoc.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    insert_auto_toc(doc, font_name=font_name, toc_items=preview_toc_items, style_key="bktechs")

    # --------------------------------------------------------------------------
    # SECTION 1: NỘI DUNG THUYẾT MINH CHÍNH (ĐÁNH SỐ TRANG LẠI TỪ Trang 1)
    # --------------------------------------------------------------------------
    sec1 = doc.add_section(WD_SECTION.NEW_PAGE)
    apply_a4_geometry(sec1, top_cm=2.4, bottom_cm=1.8, left_cm=MARGIN_LEFT_CM, right_cm=MARGIN_RIGHT_CM)
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

    # Footer Section 1: BKTECHS || Địa chỉ || Trang [PAGE]
    f1 = sec1.footer
    fp1 = f1.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_top_border(fp1, color_hex="BFBFBF", sz="6")
    pPr_f1 = fp1._p.get_or_add_pPr()
    pPr_f1.append(parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="none" w:pos="%d"/></w:tabs>' % (nsdecls("w"), PRINT_WIDTH_TWIPS)))

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

    fp1.add_run("\t")
    rf4 = fp1.add_run("||  Trang ")
    rf4.font.name = font_name
    rf4.font.size = Pt(9.5)
    rf4.font.bold = True
    rf4.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

    add_field(fp1, "PAGE", default_val="1", font_name=font_name, font_size=9.5, bold=True, color=RGBColor(0x00, 0x20, 0x60))


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
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_before = Pt(2)
    normal.paragraph_format.space_after = Pt(5)
    set_east_asia_font(normal, font_name)

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
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_east_asia_font(st, font_name)

    # --------------------------------------------------------------------------
    # SECTION 0: BÌA KHUNG VIỀN ĐÔI (TRANG 1) + BÌA LÓT PHÁP LÝ (TRANG 2) + MỤC LỤC (TRANG 3)
    # --------------------------------------------------------------------------
    sec0 = doc.sections[0]
    apply_a4_geometry(sec0, top_cm=1.8, bottom_cm=1.8, left_cm=MARGIN_LEFT_CM, right_cm=MARGIN_RIGHT_CM)
    sec0.different_first_page_header_footer = True

    # --- TRANG 1: BÌA NGOÀI KHUNG VIỀN ĐÔI (DOUBLE-LINE BOX) ---
    outer_box = doc.add_table(rows=1, cols=1)
    outer_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(outer_box)
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

    for lbl, val in [
        ("CÔNG TRÌNH:", meta.get("project_name", "[TÊN CÔNG TRÌNH / DỰ ÁN ĐẦU TƯ XÂY DỰNG]")),
        ("HẠNG MỤC:", meta.get("item_name", "KẾT CẤU (TỔNG HỢP CÁC HẠNG MỤC CÔNG TRÌNH)")),
        ("ĐỊA ĐIỂM XÂY DỰNG:", meta.get("location", "[Phường/Xã, Quận/Huyện, Tỉnh/Thành phố]")),
        ("CHỦ ĐẦU TƯ:", meta.get("client_name", "[TÊN CHỦ ĐẦU TƯ]")),
    ]:
        p_info = c_box.add_paragraph()
        p_info.alignment = WD_ALIGN_PARAGRAPH.LEFT
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

    # --- TRANG 2: BÌA LÓT PHÁP LÝ ---
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

    sign_2col = doc.add_table(rows=3, cols=2)
    sign_2col.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(sign_2col)
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

    p_team = doc.add_paragraph()
    p_team.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_team.paragraph_format.space_before = Pt(20)
    p_team.paragraph_format.space_after = Pt(6)
    rtm = p_team.add_run("NHÓM KỸ SƯ THỰC HIỆN HỒ SƠ THUYẾT MINH:")
    rtm.font.name = font_name
    rtm.font.size = Pt(11)
    rtm.font.bold = True
    rtm.font.color.rgb = RGBColor(0x00, 0x20, 0x60)

    team_tbl = doc.add_table(rows=4, cols=3)
    team_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_full_width(team_tbl)
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
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = font_name
            r.font.size = Pt(10.5)
            r.font.bold = (c_idx == 0)

    # --- TRANG 3: MỤC LỤC TỰ ĐỘNG 3 CẤP ---
    doc.add_page_break()
    p_toc = doc.add_paragraph()
    p_toc.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_toc.paragraph_format.space_before = Pt(4)
    p_toc.paragraph_format.space_after = Pt(8)
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
    apply_a4_geometry(sec1, top_cm=2.2, bottom_cm=1.8, left_cm=MARGIN_LEFT_CM, right_cm=MARGIN_RIGHT_CM)
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
    add_field(fp1, "PAGE", default_val="1", font_name=font_name, font_size=9.5, italic=True)


# ==============================================================================
# PARSER MARKDOWN -> DOCX (TỰ ĐỘNG ĐÁNH SỐ HEADING, PHÂN KHU CHAPTER & BẢNG)
# ==============================================================================
def _parse_md_table_alignments(sep_row_str: str, ncols: int) -> list:
    """Đọc dòng phân cách |:---:|---:|---| của bảng Markdown để trả về danh sách alignment cho từng cột."""
    raw_cols = [c.strip() for c in sep_row_str.strip().strip("|").split("|")]
    aligns = []
    for idx in range(ncols):
        spec = raw_cols[idx] if idx < len(raw_cols) else ""
        if spec.startswith(":") and spec.endswith(":"):
            aligns.append(WD_ALIGN_PARAGRAPH.CENTER)
        elif spec.endswith(":"):
            aligns.append(WD_ALIGN_PARAGRAPH.RIGHT)
        elif spec.startswith(":"):
            aligns.append(WD_ALIGN_PARAGRAPH.LEFT)
        else:
            aligns.append(None)
    return aligns


def render_markdown_content(doc, md_text: str, style_key: str = "bktechs", nav_counter_start: int = 1, chapter_page_break: bool = False) -> int:
    cfg = STYLE_CONFIGS[style_key]
    font_name = cfg["font_family"]
    dot = "." if cfg["dot_after_number"] else ""

    h_counts = [0, 0, 0]
    lines = md_text.splitlines()
    i = 0
    nav_counter = nav_counter_start

    pat_part = r"^(?:PHẦN\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\b|CÁC\s+PHỤ\s+LỤC)"
    pat_app = r"^(?:PHỤ\s+LỤC|APPENDIX)\s+\d+"
    curr_part_roman = ""
    is_under_app = False
    has_rendered_any_body = False
    just_rendered_heading = False

    while i < len(lines):
        line = lines[i].rstrip()

        # Bỏ qua dòng trống
        if not line.strip():
            i += 1
            continue

        # Bảng Markdown
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines = []
            col_aligns = None
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_str = lines[i].strip()
                if re.match(r"^\|[\s\-\:\|]+\|$", row_str):
                    col_aligns_raw = row_str
                else:
                    cells = [c.strip() for c in row_str.strip("|").split("|")]
                    table_lines.append(cells)
                i += 1
            if table_lines:
                ncols = max(len(r) for r in table_lines)
                if "col_aligns_raw" in locals() and col_aligns_raw:
                    col_aligns = _parse_md_table_alignments(col_aligns_raw, ncols)
                    col_aligns_raw = None
                else:
                    col_aligns = [None] * ncols

                # Kiểm tra nếu cột 0 có tiêu đề là STT / TT / Mục
                col0_header = table_lines[0][0].strip().upper() if table_lines[0] else ""
                col0_is_stt = col0_header in ("STT", "TT", "NO", "NO.", "MỤC", "CHƯƠNG / MỤC")

                tbl = doc.add_table(rows=len(table_lines), cols=ncols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_full_width(tbl)
                set_table_borders(tbl, color="BFBFBF", sz="4")

                # Lặp lại header bảng khi qua trang + cố định chiều cao tối thiểu 380 twips
                header_tr = tbl.rows[0]._tr.get_or_add_trPr()
                header_tr.append(parse_xml(r"<w:tblHeader %s/>" % nsdecls("w")))
                header_tr.append(parse_xml(r'<w:trHeight %s w:val="380" w:hRule="atLeast"/>' % nsdecls("w")))

                for r_idx, row_vals in enumerate(table_lines):
                    row = tbl.rows[r_idx]
                    if r_idx > 0:
                        row._tr.get_or_add_trPr().append(parse_xml(r"<w:cantSplit %s/>" % nsdecls("w")))

                    first_cell_upper = (row_vals[0].strip().upper() if row_vals else "")
                    # Chỉ tô nền vàng nguyên dòng nếu là dòng Tổng cộng / Kết luận tổng hợp cuối bảng
                    is_summary_row = r_idx > 0 and any(first_cell_upper.startswith(k) for k in ["TỔNG", "KẾT LUẬN", "TRUNG BÌNH", "CỘNG"])

                    for c_idx in range(ncols):
                        val = row_vals[c_idx] if c_idx < len(row_vals) else ""
                        cell = row.cells[c_idx]
                        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                        set_cell_margins(cell, top=80, bottom=80, left=115, right=115)

                        if r_idx == 0:
                            set_cell_shading(cell, cfg["table_header_fill"])
                        elif is_summary_row:
                            set_cell_shading(cell, cfg["table_highlight_fill"])
                        elif r_idx % 2 == 1:
                            set_cell_shading(cell, cfg["table_alt_fill"])

                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        p.paragraph_format.line_spacing = 1.12

                        if r_idx == 0:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            p.paragraph_format.keep_with_next = True
                        elif col_aligns and col_aligns[c_idx] is not None:
                            p.alignment = col_aligns[c_idx]
                        elif c_idx == 0 and col0_is_stt:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        else:
                            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                        if r_idx == 0:
                            clean_val = re.sub(r"\*\*(.*?)\*\*", r"\1", normalize_engineering_symbols(val))
                            _emit_text_with_subscripts_and_badges(
                                p,
                                clean_val,
                                font_name,
                                cfg["table_size"],
                                cfg["table_header_text"],
                                is_bold=True,
                                is_italic=False,
                            )
                        else:
                            _add_formatted_runs(
                                p,
                                val,
                                font_name,
                                cfg["table_size"],
                                RGBColor(0x00, 0x20, 0x60) if is_summary_row else cfg["body_color"],
                                force_bold=is_summary_row,
                            )

                has_rendered_any_body = True
                just_rendered_heading = False
            continue

        # Công thức toán hiển thị độc lập: $$ ... $$
        m_disp_math = re.match(r"^\$\$(.*?)\$\$$", line.strip())
        if m_disp_math:
            eq_code = m_disp_math.group(1).strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            omml_str = latex_to_omml(eq_code, display_mode=True)
            if omml_str:
                try:
                    p._p.append(parse_xml(omml_str))
                except Exception:
                    _add_formatted_runs(p, eq_code, font_name, cfg["body_size"], cfg["h1_color"], force_italic=True)
            else:
                _add_formatted_runs(p, eq_code, font_name, cfg["body_size"], cfg["h1_color"], force_italic=True)
            has_rendered_any_body = True
            just_rendered_heading = False
            i += 1
            continue

        # Headings (#, ##, ###)
        m_h = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if m_h:
            level = len(m_h.group(1))
            raw_text = m_h.group(2).strip()

            # Bỏ qua các dòng tiêu đề tài liệu / metadata trùng ở đầu file
            if is_redundant_frontmatter_heading(i, level, raw_text):
                i += 1
                continue

            is_part = bool(re.match(pat_part, raw_text, flags=re.IGNORECASE))
            is_app = bool(re.match(pat_app, raw_text, flags=re.IGNORECASE))

            if is_part:
                m_rom = re.match(r"^PHẦN\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", raw_text.strip(), flags=re.IGNORECASE)
                curr_part_roman = m_rom.group(1).upper() if m_rom else ""
                h_counts = [0, 0, 0]
                is_under_app = False
                display_title = normalize_engineering_symbols(raw_text.upper())
            elif is_app:
                m_a = re.search(r"(?:PHỤ\s+LỤC|APPENDIX)\s+(\d+)", raw_text, flags=re.IGNORECASE)
                a_num = int(m_a.group(1)) if m_a else 1
                is_under_app = True
                h_counts[0] = a_num
                h_counts[1] = 0
                h_counts[2] = 0
                display_title = normalize_engineering_symbols(raw_text.upper())
            else:
                raw_title = normalize_engineering_symbols(strip_existing_heading_number(raw_text))
                if level == 1:
                    h_counts[0] += 1
                    h_counts[1] = 0
                    h_counts[2] = 0
                    num_prefix = f"{h_counts[0]}{dot}"
                    display_title = f"{num_prefix} {raw_title.upper()}"
                elif level == 2:
                    if curr_part_roman == "III" and not is_under_app:
                        h_counts[1] += 1
                        h_counts[2] = 0
                        num_prefix = f"III.{h_counts[1]}{dot}"
                        display_title = f"{num_prefix} {raw_title}"
                    else:
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
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = True

            # Quy tắc ngắt trang cho Đại phân khu (PHẦN II, PHẦN III) và Phụ lục (PHỤ LỤC 1..N)
            if has_rendered_any_body and (is_part or is_app or (chapter_page_break and level == 1)):
                # Nếu ngay trước PHỤ LỤC 1 là tiêu đề PHẦN II (vừa mới ngắt trang), không ngắt trang lần 2 để tránh trang trắng chỉ có 1 dòng PHẦN II
                if not (is_app and just_rendered_heading):
                    p.paragraph_format.page_break_before = True

            if is_part:
                p.paragraph_format.space_before = Pt(8 if not has_rendered_any_body else 14)
                p.paragraph_format.space_after = Pt(8)
                set_paragraph_shading(p, color_hex="D9E1F2" if style_key == "tvtk" else "E8EEF5")
                set_paragraph_left_border(p, color_hex="002060", sz="24")
                set_paragraph_bottom_border(p, color_hex="002060", sz="8")
            elif is_app:
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                set_paragraph_bottom_border(p, color_hex="FFC000" if style_key == "bktechs" else "0070C0", sz="12")
            else:
                p.paragraph_format.space_before = Pt(14 if level == 1 else (10 if level == 2 else 6))
                p.paragraph_format.space_after = Pt(6 if level == 1 else 4)
                if level == 1 and style_key == "bktechs":
                    set_paragraph_bottom_border(p, color_hex="D9E1F2", sz="6")

            _emit_text_with_subscripts_and_badges(
                p,
                display_title,
                font_name,
                cfg["h1_size"] + 0.5 if is_part else cfg[f"h{level}_size"],
                cfg[f"h{level}_color"],
                is_bold=True,
                is_italic=(level == 3),
            )

            # Gán bookmark tự động:
            m_app = re.search(r"(?:PHỤ LỤC|Phụ lục|APPENDIX)\s+(\d+)", raw_text, flags=re.IGNORECASE)
            if m_app:
                app_num = int(m_app.group(1))
                add_bookmark(p, f"PHU_LUC_{app_num}", 1000 + app_num)

            add_bookmark(p, f"TOC_NAV_{nav_counter}", 2000 + nav_counter)
            nav_counter += 1

            has_rendered_any_body = True
            just_rendered_heading = True
            i += 1
            continue

        # Đường kẻ phân cách ngang (---) -> Bỏ qua nếu ngay sau hoặc ngay trước Heading để tránh đường kẻ kép rối mắt
        if re.match(r"^---+$", line.strip()):
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
                p_img.paragraph_format.keep_with_next = True
                p_img.add_run().add_picture(clean_path, width=Cm(14.5))
                if cap:
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_before = Pt(2)
                    p_cap.paragraph_format.space_after = Pt(8)
                    r_cap = p_cap.add_run(normalize_engineering_symbols(cap))
                    r_cap.font.name = font_name
                    r_cap.font.size = Pt(10)
                    r_cap.font.italic = True
                    r_cap.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
                    set_east_asia_font(r_cap, font_name)
            else:
                p_err = doc.add_paragraph()
                p_err.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_err.paragraph_format.space_before = Pt(4)
                p_err.paragraph_format.space_after = Pt(6)
                r_err = p_err.add_run(f"[{cap if cap else 'Ảnh kỹ thuật'} — Chưa tìm thấy tệp ảnh: {clean_path}]")
                r_err.font.name = font_name
                r_err.font.size = Pt(10)
                r_err.font.italic = True
                r_err.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            has_rendered_any_body = True
            just_rendered_heading = False
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
            p_q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_q.paragraph_format.left_indent = Cm(0.75)
            p_q.paragraph_format.right_indent = Cm(0.4)
            p_q.paragraph_format.space_before = Pt(6)
            p_q.paragraph_format.space_after = Pt(8)
            p_q.paragraph_format.line_spacing = 1.2
            set_paragraph_left_border(p_q, color_hex="002060" if style_key == "bktechs" else "0070C0", sz="18")
            set_paragraph_shading(p_q, color_hex="F2F5F9")
            _add_formatted_runs(p_q, full_quote, font_name, cfg["body_size"] - 0.5, cfg["body_color"], force_italic=True)
            has_rendered_any_body = True
            just_rendered_heading = False
            continue

        # CẤP 2 DANH SÁCH: Dấu cộng đầu dòng (+) hoặc thụt lề cấp 2
        m_plus = re.match(r"^(\s*)\+\s+(.*)$", line)
        m_sub_dash = re.match(r"^(\s{2,})[\-\*]\s+(.*)$", line)
        if m_plus or m_sub_dash:
            text_content = m_plus.group(2) if m_plus else m_sub_dash.group(2)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(1.30)
            p.paragraph_format.first_line_indent = -Cm(0.42)
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("+  ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h2_color"]
            set_east_asia_font(r_sym, font_name)
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            has_rendered_any_body = True
            just_rendered_heading = False
            i += 1
            continue

        # CẤP 3 DANH SÁCH: Dấu chấm tròn (•) hoặc thụt lề sâu >= 4 spaces
        m_dot = re.match(r"^(\s*)•\s+(.*)$", line)
        m_sub3 = re.match(r"^(\s{4,})[\-\*\+]\s+(.*)$", line)
        if m_dot or m_sub3:
            text_content = m_dot.group(2) if m_dot else m_sub3.group(2)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(1.95)
            p.paragraph_format.first_line_indent = -Cm(0.38)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("•  ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["body_color"]
            set_east_asia_font(r_sym, font_name)
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            has_rendered_any_body = True
            just_rendered_heading = False
            i += 1
            continue

        # CẤP 1 DANH SÁCH: Gạch đầu dòng (-) hoặc (*)
        m_dash = re.match(r"^(\s*)[\-\*–—]\s+(.*)$", line)
        if m_dash:
            text_content = m_dash.group(2)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(0.65)
            p.paragraph_format.first_line_indent = -Cm(0.38)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run("–  ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h1_color"]
            set_east_asia_font(r_sym, font_name)
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            has_rendered_any_body = True
            just_rendered_heading = False
            i += 1
            continue

        # DANH SÁCH THỨ TỰ / ĐIỂM KHOẢN: 1., 1), a), b)
        m_enum = re.match(r"^(\s*)(\d+[\.\)]|[a-zA-Z][\.\)])\s+(.*)$", line)
        if m_enum:
            prefix = m_enum.group(2)
            text_content = m_enum.group(3)
            indent_len = len(m_enum.group(1))
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(1.30 if indent_len >= 2 else 0.75)
            p.paragraph_format.first_line_indent = -Cm(0.45)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            r_sym = p.add_run(f"{prefix} ")
            r_sym.font.name = font_name
            r_sym.font.size = Pt(cfg["body_size"])
            r_sym.font.bold = True
            r_sym.font.color.rgb = cfg["h1_color"]
            set_east_asia_font(r_sym, font_name)
            _add_formatted_runs(p, text_content, font_name, cfg["body_size"], cfg["body_color"])
            has_rendered_any_body = True
            just_rendered_heading = False
            i += 1
            continue

        # Đoạn văn bản thường / Công thức
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.2
        _add_formatted_runs(p, line.strip(), font_name, cfg["body_size"], cfg["body_color"])
        has_rendered_any_body = True
        just_rendered_heading = False
        i += 1

    return nav_counter


def _emit_text_with_subscripts_and_badges(p, text_str: str, font_name: str, font_size: float, color: RGBColor, is_bold: bool = False, is_italic: bool = False):
    """
    Phân tách chuỗi văn bản để:
    1) Chỉ tô màu xanh lá đậm riêng cho nhãn `[ĐẠT]` / `[OK]` và đỏ đậm cho `[KHÔNG ĐẠT]` (không làm lem màu ra cả câu).
    2) Tự động chuyển các ký hiệu cơ học có dấu gạch dưới như `R_b`, `R_bt`, `M_Ed`, `N_Ed`, `γ_f`, `c_nom`, `a_crc,1`, `η_coc`
       thành chỉ số dưới (`subscript`) thật trong Word thay vì in dấu `_` thô.
    """
    # Tách nhãn trạng thái [ĐẠT] / [KHÔNG ĐẠT]
    badge_pat = r"(\[(?:ĐẠT|KHÔNG ĐẠT|OK|PASSED|FAILED)\](?:\s*\([^\)]+\))?)"
    chunks = re.split(badge_pat, text_str)

    for chunk in chunks:
        if not chunk:
            continue
        if re.match(badge_pat, chunk):
            is_fail = any(k in chunk.upper() for k in ["KHÔNG ĐẠT", "FAIL"])
            r = p.add_run(chunk)
            r.font.name = font_name
            r.font.size = Pt(font_size)
            r.font.bold = True
            r.font.italic = is_italic
            r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00) if is_fail else RGBColor(0x1E, 0x6B, 0x3A)
            set_east_asia_font(r, font_name)
            continue

        # Tách các ký hiệu kỹ thuật có chỉ số dưới: VD R_b, R_bt, As_req, F_day_noi, q_toan_phan, M_Ed, N_Ed, γ_f, c_nom, a_crc,1, η_coc
        sub_pat = r"(\b(?:[A-Za-z]{1,3}|[α-ωΑ-Ω]|Δu|Δs)_(?:[A-Za-z0-9]+(?:[,_][A-Za-z0-9]+)*))"
        sub_tokens = re.split(sub_pat, chunk)
        for st in sub_tokens:
            if not st:
                continue
            m_sub = re.match(r"^([A-Za-zα-ωΑ-Ω]{1,3}|Δu|Δs)_([A-Za-z0-9]+(?:[,_][A-Za-z0-9]+)*)$", st)
            if m_sub:
                base_s, sub_s = m_sub.group(1), m_sub.group(2).replace("_", ",")
                rb = p.add_run(base_s)
                rb.font.name = font_name
                rb.font.size = Pt(font_size)
                rb.font.bold = is_bold
                rb.font.italic = is_italic
                rb.font.color.rgb = color
                set_east_asia_font(rb, font_name)

                rs = p.add_run(sub_s)
                rs.font.name = font_name
                rs.font.size = Pt(font_size)
                rs.font.bold = is_bold
                rs.font.italic = is_italic
                rs.font.subscript = True
                rs.font.color.rgb = color
                set_east_asia_font(rs, font_name)
            else:
                r = p.add_run(st)
                r.font.name = font_name
                r.font.size = Pt(font_size)
                r.font.bold = is_bold
                r.font.italic = is_italic
                r.font.color.rgb = color
                set_east_asia_font(r, font_name)


def _add_formatted_runs(p, text: str, font_name: str, font_size: float, color: RGBColor, force_italic: bool = False, force_bold: bool = False):
    # Tách riêng các biểu thức LaTeX ($...$ hoặc $$...$$) trước khi normalize ký hiệu văn bản thường
    math_split_pat = r"(\$\$.*?\$\$|\$[^\$]+?\$)"
    top_chunks = re.split(math_split_pat, text)

    for top_c in top_chunks:
        if not top_c:
            continue
        if (top_c.startswith("$$") and top_c.endswith("$$") and len(top_c) >= 4) or (top_c.startswith("$") and top_c.endswith("$") and len(top_c) >= 2):
            clean_math = top_c[2:-2].strip() if top_c.startswith("$$") else top_c[1:-1].strip()
            omml_str = latex_to_omml(clean_math, display_mode=False)
            if omml_str:
                try:
                    p._p.append(parse_xml(omml_str))
                    continue
                except Exception:
                    pass
            # Fallback nếu OMML gặp lỗi
            _emit_text_with_subscripts_and_badges(p, normalize_engineering_symbols(clean_math), font_name, font_size, RGBColor(0x1F, 0x4E, 0x79), is_bold=force_bold, is_italic=True)
            continue

        norm_seg = normalize_engineering_symbols(top_c)

        # Quét cross-reference: "Xem chi tiết tại Phụ lục X", "Xem Phụ lục X", "theo Phụ lục X"
        cross_ref_pat = r"(Xem\s+(?:chi\s+tiết\s+tại\s+)?Phụ\s+lục\s+\d+|theo\s+Phụ\s+lục\s+\d+)"
        segments = re.split(cross_ref_pat, norm_seg, flags=re.IGNORECASE)

        for seg in segments:
            if not seg:
                continue
            m_xref = re.search(r"Phụ\s+lục\s+(\d+)", seg, flags=re.IGNORECASE)
            if m_xref and re.match(r"^(?:Xem|theo)", seg.strip(), flags=re.IGNORECASE):
                app_id = m_xref.group(1)
                add_cross_ref_hyperlink(p, seg, f"PHU_LUC_{app_id}", font_name, font_size)
                continue

            # Tokenize: **bold**, *italic*, `code`
            pattern = r"(\*\*.*?\*\*|\*[^\*]+?\*|`[^`]+?`)"
            parts = re.split(pattern, seg)

            for part in parts:
                if not part:
                    continue
                is_bold = force_bold
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
                else:
                    clean_txt = part

                _emit_text_with_subscripts_and_badges(p, clean_txt, run_font, run_size, run_color, is_bold=is_bold, is_italic=is_italic)


def build_report_from_markdown(
    input_md_path: str,
    output_docx_path: str,
    style_key: str = "bktechs",
    meta: dict = None,
    logo_path: str = None,
    appendices: list = None,
    chapter_page_break: bool = False,
):
    meta = meta or {}
    with open(input_md_path, "r", encoding="utf-8") as f:
        raw_md_text = f.read()

    # Nội suy biến mẫu {{project_name}}, {{location}}, {{client_name}}...
    md_text = interpolate_meta_placeholders(raw_md_text, meta)

    # Trích xuất toàn bộ cấu trúc Mục lục từ nội dung Markdown và các file Phụ lục
    toc_items = extract_toc_items_from_markdown(md_text, appendices=appendices, style_key=style_key)

    doc = docx.Document()
    if style_key == "bktechs":
        setup_bktechs_template(doc, meta, logo_path=logo_path, preview_toc_items=toc_items)
    else:
        setup_tvtk_template(doc, meta, preview_toc_items=toc_items)

    # 1. Render nội dung chính của Thuyết minh (Section 1)
    nav_counter = render_markdown_content(
        doc,
        md_text,
        style_key=style_key,
        nav_counter_start=1,
        chapter_page_break=chapter_page_break,
    )

    # 2. Xử lý các Phụ lục tính toán đi kèm (--appendices) với Section Break & Đánh số trang độc lập
    if appendices:
        cfg = STYLE_CONFIGS[style_key]
        font_name = cfg["font_family"]

        for idx, app_file in enumerate(appendices, 1):
            if not os.path.exists(app_file):
                print(f"[CẢNH BÁO]: Không tìm thấy file phụ lục: {app_file}")
                continue

            with open(app_file, "r", encoding="utf-8") as af:
                raw_content = interpolate_meta_placeholders(af.read().strip(), meta)

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
            apply_a4_geometry(
                sec_app,
                top_cm=2.2 if style_key == "tvtk" else 2.4,
                bottom_cm=1.8,
                left_cm=MARGIN_LEFT_CM,
                right_cm=MARGIN_RIGHT_CM,
            )
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
                pPr_fa = fpa._p.get_or_add_pPr()
                pPr_fa.append(parse_xml(r'<w:tabs %s><w:tab w:val="right" w:leader="none" w:pos="%d"/></w:tabs>' % (nsdecls("w"), PRINT_WIDTH_TWIPS)))

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

                fpa.add_run("\t")
                rfa4 = fpa.add_run(f"||  Phụ lục {idx} — Trang ")
                rfa4.font.name = font_name
                rfa4.font.size = Pt(9.5)
                rfa4.font.bold = True
                rfa4.font.color.rgb = RGBColor(0xFF, 0xC0, 0x00)

                add_field(fpa, "PAGE", default_val="1", font_name=font_name, font_size=9.5, bold=True, color=RGBColor(0x00, 0x20, 0x60))
            else:
                fpa.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                set_paragraph_top_border(fpa, color_hex="BFBFBF", sz="6")
                rfa = fpa.add_run(f"Phụ lục {idx} — Trang ")
                rfa.font.name = font_name
                rfa.font.size = Pt(9.5)
                rfa.font.italic = True
                add_field(fpa, "PAGE", default_val="1", font_name=font_name, font_size=9.5, italic=True)

            # Render nội dung phụ lục vào section mới
            nav_counter = render_markdown_content(doc, app_body_md, style_key=style_key, nav_counter_start=nav_counter)

    os.makedirs(os.path.dirname(os.path.abspath(output_docx_path)), exist_ok=True)
    doc.save(output_docx_path)
    return output_docx_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xuất Hồ sơ Thuyết minh Tính toán theo 2 Bộ Chuẩn (BKTECHS / TVTK) - v2.1")
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
    parser.add_argument("--chapter-break", action="store_true", help="Tự động ngắt trang mới trước mỗi Chương lớn (Heading 1)")
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
        chapter_page_break=args.chapter_break,
    )
    print(f"Đã xuất hồ sơ thuyết minh ({args.style.upper()} v2.1): {out}")
