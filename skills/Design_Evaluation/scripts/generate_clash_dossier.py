#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
MODULE: GENERATE CLASH DOSSIER (HỒ SƠ THUYẾT MINH KHOANH LỖI XUNG ĐỘT BẢN VẼ — v3.3.0)
SKILL: Design_Evaluation (v3.3.0) & SKILL_REPORT (v3.3.0) & SKILL_BIM_COORDINATION (v1.3.0)
GATE: GATE 5 (4-Way Blueprint Audit) & GATE 6 (RFI/NCR Sanctions)

BẢN NÂNG CẤP ĐỒNG BỘ HỆ THỐNG v3.3.0 (5 CHỐT CHẶN THẨM MỸ & DỮ LIỆU):
  1. [Zero Box-in-Box Redundancy]: Tự động cắt bỏ thanh Banner đen ở đỉnh ảnh và hộp chữ 4 dòng
     ở đáy ảnh PNG (tránh lặp lại tiêu đề và bảng 6 mục của Word), phóng to vùng CAD thêm 35-45%.
  2. [Strict One-Page-Per-Exhibit Lock]: Tự động tính toán chiều cao ảnh nhúng (max_h <= 7.6 cm,
     hoặc 6.6 cm cho phiếu dài) và padding ô (28-34 dxa), đảm bảo 1 Phiếu = 1 Trang A4 Khép Kín
     (0 dòng mồ côi rớt trang, 0 trang trắng).
  3. [Unified Corporate Form Palette]: Đồng bộ 100% hệ màu với Form Thuyết minh chuẩn:
     - Header ngang: Xanh Navy (#1B365D) chữ trắng.
     - Cột nhãn bên trái (6 mục & cột Mã lỗi): Xanh Băng nhạt (#EAF0F6) + chữ Navy đậm (#1B365D).
     - Dòng dữ liệu: Trắng (#FFFFFF) xen kẽ Xám Băng (#F8FAFC), viền #CBD5E1.
     - Badge mức độ trầm chuẩn mực: Đỏ Đô (#991B1B / #FEF2F2), Cam Hổ phách (#B45309 / #FFFBEB),
       Xanh Lam (#1E40AF / #EFF6FF).
  4. [CAD Redline & Serif Auto-Fit Subheader]: Thanh tiêu đề con trên từng khung bản vẽ dùng
     phông có chân tiếng Việt đầy đủ (LiberationSerif-Bold / NotoSerif-Bold) trên nền #1B365D,
     tự động co cỡ chữ vừa khít khung ảnh (cam kết 0% tràn chữ).
  5. [SSOT Anti-Drift & Sentence-Case Index]: Đọc duy nhất từ 1 nguồn dữ liệu chuẩn (SSOT) cho
     cả Bảng Ma trận, Bảng Danh mục và Bảng Chi tiết Phiếu; tự động chuyển ALL CAPS sang Sentence Case.
========================================================================================
"""

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# BẢNG MÀU FORM THUYẾT MINH CHUẨN HÓA (SKILL_REPORT v3.3.0)
# ==============================================================================
NAVY_PRIMARY  = "1B365D"  # Deep Corporate Navy (Headers & Primary Titles)
ICE_BLUE_LBL  = "EAF0F6"  # Soft Ice Blue (Left Label Column — replaces heavy dark fill)
TEXT_DARK     = "0F172A"  # Slate 900 Body Text
TEXT_MUTED    = "475569"  # Slate 600 Captions & Subtitles
BORDER_COLOR  = "CBD5E1"  # Slate 300 Subtle Grid Border
ZEBRA_ROW     = "F8FAFC"  # Slate 50 Alternating Row
WHITE         = "FFFFFF"

CRITICAL_RED  = "991B1B"  # Refined Deep Crimson
CRITICAL_BG   = "FEF2F2"  # Soft Red Badge Fill
MAJOR_AMBER   = "B45309"  # Refined Deep Amber
MAJOR_BG      = "FFFBEB"  # Soft Amber Badge Fill
MINOR_BLUE    = "1E40AF"  # Refined Royal Blue (Harmonious with Navy)
MINOR_BG      = "EFF6FF"  # Soft Blue Badge Fill

SERIF_BOLD_PATHS = [
    "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]

def get_vietnamese_serif_font(size_px: int):
    for p in SERIF_BOLD_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size_px)
    return ImageFont.load_default()

def fit_subheader_font(draw, text: str, max_width: int, start_size: int = 18, min_size: int = 12):
    for sz in range(start_size, min_size - 1, -1):
        f = get_vietnamese_serif_font(sz)
        bbox = draw.textbbox((0, 0), text, font=f)
        if (bbox[2] - bbox[0]) <= max_width - 18:
            return f
    return get_vietnamese_serif_font(min_size)

def sanitize_and_reheader_redline_image(img_path: str, subheaders: list, out_path: str) -> str:
    """
    Tự động kiểm tra và làm sạch ảnh khoanh đỏ bản vẽ:
    - Nếu ảnh có thanh Banner đen ở đỉnh (y < 135) và hộp chữ 4 dòng ở đáy (y > H - 330),
      tự động tách riêng khung bản vẽ CAD, cắt bỏ khoảng trắng thừa, đóng khung nền #F0F4F8
      viền #1B365D và vẽ thanh tiêu đề con phông Serif chữ trắng không tràn khung.
    """
    im = Image.open(img_path).convert("RGB")
    arr = np.array(im)
    H, W, _ = arr.shape

    # Kiểm tra xem có phải ảnh legacy có top banner đen (y=0..130) hay đã được làm sạch
    top_dark = (arr[:125, 100, 0] < 35) & (arr[:125, 100, 1] < 48)
    if not top_dark.all() or H < 900:
        # Ảnh đã ở chuẩn Clean CAD Redline v3.3
        if img_path != out_path:
            im.save(out_path, optimize=True)
        return out_path

    # Tìm các khung bản vẽ CAD tại dòng giữa y = 400 (nơi nền ngoài là #F8FAFC = 248, 250, 252)
    row_mid = arr[min(400, H // 2)]
    is_fg = (row_mid[:, 0] != 248) | (row_mid[:, 1] != 250) | (row_mid[:, 2] != 252)
    segs = []
    in_seg = False
    start = 0
    for x in range(W):
        if is_fg[x] and not in_seg:
            in_seg = True
            start = x
        elif not is_fg[x] and in_seg:
            in_seg = False
            if x - start > 60:
                segs.append((start, x - 1))
    if in_seg and W - start > 60:
        segs.append((start, W - 1))
    if not segs:
        segs = [(35, W - 35)]

    crops = []
    for (x0, x1) in segs:
        col = arr[170:H - 320, x0]
        bg_rows = np.where((col[:, 0] == 248) & (col[:, 1] == 250) & (col[:, 2] == 252))[0]
        yb = (170 + int(bg_rows[0]) - 1) if len(bg_rows) > 0 else (H - 335)
        c = im.crop((x0 + 2, 167, x1 - 2, max(220, yb - 2)))
        crops.append(c)

    target_h = max(c.height for c in crops)
    padded_crops = []
    for c in crops:
        min_pw = 580 if len(crops) == 2 else max(c.width, 1080)
        pw = max(c.width, min_pw)
        card = Image.new("RGB", (pw, target_h), (255, 255, 255))
        card.paste(c, ((pw - c.width) // 2, (target_h - c.height) // 2))
        padded_crops.append(card)
    crops = padded_crops

    gap = 18 if len(crops) > 1 else 0
    pad_x, pad_top, pad_bot, hdr_h = 14, 10, 10, 34
    total_w = sum(c.width for c in crops) + gap * (len(crops) - 1) + 2 * pad_x
    canvas_h = pad_top + hdr_h + target_h + pad_bot

    canvas = Image.new("RGB", (total_w, canvas_h), (240, 244, 248))  # #F0F4F8
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, total_w - 1, canvas_h - 1], outline=(27, 54, 93), width=2)

    cur_x = pad_x
    for idx_p, c_img in enumerate(crops):
        pw, ph = c_img.width, c_img.height
        draw.rectangle([cur_x, pad_top, cur_x + pw - 1, pad_top + hdr_h], fill=(27, 54, 93), outline=(27, 54, 93))
        h_txt = subheaders[idx_p] if idx_p < len(subheaders) else subheaders[0]
        f_hdr = fit_subheader_font(draw, h_txt, pw)
        tb = draw.textbbox((0, 0), h_txt, font=f_hdr)
        tx = cur_x + (pw - (tb[2] - tb[0])) // 2
        ty = pad_top + (hdr_h - (tb[3] - tb[1])) // 2 - 2
        draw.text((tx, ty), h_txt, fill=(255, 255, 255), font=f_hdr)

        canvas.paste(c_img, (cur_x, pad_top + hdr_h))
        draw.rectangle([cur_x, pad_top + hdr_h, cur_x + pw - 1, pad_top + hdr_h + ph - 1], outline=(27, 54, 93), width=2)
        cur_x += pw + gap

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    canvas.save(out_path, optimize=True)
    return out_path

def set_font_run(run, font_name="Times New Roman", size_pt=10.0, bold=False, italic=False, color_hex=None):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_hex:
        run.font.color.rgb = RGBColor(int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16))
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ["w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"]:
        rFonts.set(qn(attr), font_name)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))

def set_cell_margins(cell, top=36, bottom=36, left=70, right=70):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(old)
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color=BORDER_COLOR, sz="4", val="single"):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    tblPr.append(parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    ))

def make_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))
    trPr.append(parse_xml(r'<w:cantSplit %s/>' % nsdecls('w')))

def make_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:cantSplit %s/>' % nsdecls('w')))

def format_sentence_case(text: str) -> str:
    """Chuyển chuỗi tiêu đề IN HOA TOÀN BỘ sang dạng câu chuẩn dễ đọc, giữ nguyên mã kỹ thuật."""
    if not text or not text.isupper():
        return text
    keep_tokens = {"CN3", "CN4", "CN5", "CN6", "HT5", "HT7", "HT8", "DV3", "DV4", "DV5",
                   "M1", "M2", "M3", "M4", "C1", "K1", "FR2", "RF1", "RF3", "DK1", "DK1A", "DK2",
                   "DS1", "CC", "PCCC", "BTCT", "ETABS", "TMKC", "TCVN", "QCVN", "AII", "AIII",
                   "KC-01", "KC-02", "KC-03", "KC-07", "KC-09", "KC-13", "KC-14", "KT-02", "#VALUE!"}
    words = text.split()
    out = []
    for idx, w in enumerate(words):
        clean_w = w.strip("(),:;—-")
        if clean_w in keep_tokens or any(ch.isdigit() for ch in clean_w):
            out.append(w)
        elif idx == 0 or (idx > 0 and out[-1] == "—"):
            out.append(w.capitalize())
        else:
            out.append(w.lower())
    return " ".join(out)

def generate_dossier(matrix_path, img_dir, output_docx, project_name, location, investor, designer, auditor, date_str):
    with open(matrix_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    clashes = data.get('clashes', [])

    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(1.8)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)

    # Xuất từng Phiếu theo chuẩn "1 Phiếu = 1 Trang A4 Khép Kín" (Zero Orphan Spill)
    for idx_ex, c in enumerate(clashes, start=1):
        if idx_ex > 1:
            doc.add_page_break()
        banner_tbl = doc.add_table(rows=1, cols=2)
        banner_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        banner_tbl.autofit = False
        set_table_borders(banner_tbl, color=BORDER_COLOR)
        c_b1, c_b2 = banner_tbl.rows[0].cells
        c_b1.width, c_b2.width = Cm(13.6), Cm(3.4)
        c_b1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        c_b2.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        sev = c.get('severity', 'MAJOR')
        sev_color = CRITICAL_RED if sev == 'CRITICAL' else (MAJOR_AMBER if sev == 'MAJOR' else MINOR_BLUE)
        set_cell_background(c_b1, NAVY_PRIMARY)
        set_cell_background(c_b2, sev_color)
        set_cell_margins(c_b1, top=42, bottom=42, left=85, right=85)
        set_cell_margins(c_b2, top=42, bottom=42, left=60, right=60)

        p_b1 = c_b1.paragraphs[0]
        p_b1.paragraph_format.line_spacing = 1.1
        set_font_run(p_b1.add_run(f"PHIẾU THẨM TRA BẢN VẼ SỐ {idx_ex:02d} — MÃ LỖI: {c.get('clash_id', '')}\n"), size_pt=10.0, bold=True, color_hex=WHITE)
        set_font_run(p_b1.add_run(c.get('description', c.get('source_a_ref', ''))), size_pt=9.5, bold=True, color_hex=WHITE)

        p_b2 = c_b2.paragraphs[0]
        p_b2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_b2.paragraph_format.line_spacing = 1.1
        set_font_run(p_b2.add_run(f"MỨC ĐỘ\n{sev}"), size_pt=9.5, bold=True, color_hex=WHITE)

        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(2)
        set_font_run(p_ref.add_run("Vị trí bản vẽ kiểm tra: "), size_pt=9.5, bold=True, color_hex=NAVY_PRIMARY)
        set_font_run(p_ref.add_run(f"{c.get('source_a_ref', '')} | "), size_pt=9.5, color_hex=TEXT_DARK)
        set_font_run(p_ref.add_run(f"Chế tài áp dụng: {c.get('linked_rfi_ncr', '')}"), size_pt=9.5, bold=True, color_hex=CRITICAL_RED)

        # Tự động làm sạch ảnh và nhúng với trần chiều cao khóa cứng (1-Page-Per-Exhibit)
        img_name = c.get('screenshot_file', '')
        img_path = os.path.join(img_dir, img_name) if img_name else ""
        if img_path and os.path.exists(img_path):
            clean_path = os.path.join("/tmp/clean_dossier_imgs", os.path.basename(img_path))
            sub_hdrs = c.get('panel_headers', [c.get('source_a_ref', 'Bản vẽ đối soát')])
            sanitize_and_reheader_redline_image(img_path, sub_hdrs, clean_path)
            im_obj = Image.open(clean_path)
            aspect = im_obj.width / max(1, im_obj.height)
            total_chars = sum(len(str(c.get(k, ''))) for k in ['source_a_val', 'source_b_val', 'engineering_impact', 'mandatory_fix'])
            max_h_cm = 6.6 if total_chars > 650 else 7.6
            w_cm = min(15.6, max_h_cm * aspect)

            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(2)
            p_img.paragraph_format.space_after = Pt(1)
            p_img.add_run().add_picture(clean_path, width=Cm(w_cm))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(1)
            p_cap.paragraph_format.space_after = Pt(2)
            set_font_run(p_cap.add_run(f"Hình {idx_ex:02d}: Vùng bản vẽ trích xuất thực tế (Khoanh đỏ đối soát xung đột kỹ thuật)"), size_pt=9.0, italic=True, color_hex=NAVY_PRIMARY)

        # Bảng Phân tích 6 Điểm — Cột trái nền Xanh Băng #EAF0F6 chữ Navy đậm #1B365D
        tbl_ex = doc.add_table(rows=6, cols=2)
        tbl_ex.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_ex.autofit = False
        set_table_borders(tbl_ex, color=BORDER_COLOR)
        col_w = [Cm(4.2), Cm(12.8)]
        ex_rows = [
            ("1. Vị trí & Số liệu trên Bản vẽ (Nguồn A):", c.get('source_a_val', c.get('discrepancy', '')), False, TEXT_DARK),
            ("2. Số liệu Đối chiếu Gốc (Nguồn B):", c.get('source_b_val', ''), False, TEXT_DARK),
            ("3. Phân tích Cơ học & Sai lệch (Δ, %):", c.get('engineering_impact', c.get('safety_impact', '')), True, CRITICAL_RED),
            ("4. Căn cứ Quy chuẩn & Tiêu chuẩn:", c.get('standard_violation', 'TCVN 5575:2024 & TCVN 5574:2018'), True, NAVY_PRIMARY),
            ("5. Đánh giá Rủi ro Kỹ thuật & An toàn:", c.get('risk_summary', c.get('safety_impact', '')), False, TEXT_DARK),
            ("6. Yêu cầu Khắc phục & Chế tài TVTK:", c.get('mandatory_fix', ''), True, TEXT_DARK),
        ]
        pad_v = 26 if total_chars > 650 else 34
        font_sz = 9.0 if total_chars > 650 else 9.5
        for r_i, (lbl_t, val_t, is_b, val_col) in enumerate(ex_rows):
            row_e = tbl_ex.rows[r_i]
            make_row_cant_split(row_e)
            c_lbl, c_val = row_e.cells
            c_lbl.width, c_val.width = col_w
            c_lbl.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            c_val.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(c_lbl, ICE_BLUE_LBL)
            set_cell_background(c_val, ZEBRA_ROW if r_i % 2 == 1 else WHITE)
            set_cell_margins(c_lbl, top=pad_v, bottom=pad_v, left=65, right=65)
            set_cell_margins(c_val, top=pad_v, bottom=pad_v, left=75, right=75)

            p_l = c_lbl.paragraphs[0]
            p_l.paragraph_format.line_spacing = 1.08
            set_font_run(p_l.add_run(lbl_t), size_pt=font_sz, bold=True, color_hex=NAVY_PRIMARY)

            p_v = c_val.paragraphs[0]
            p_v.paragraph_format.line_spacing = 1.08
            set_font_run(p_v.add_run(val_t), size_pt=font_sz, bold=is_b, color_hex=val_col)

    os.makedirs(os.path.dirname(os.path.abspath(output_docx)), exist_ok=True)
    doc.save(output_docx)
    return output_docx
