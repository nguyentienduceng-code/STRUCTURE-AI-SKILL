# -*- coding: utf-8 -*-
"""
design_tokens.py — Nguồn Sự Thật Duy Nhất về Form Trình Bày, Cỡ Chữ & Phối Màu Kỹ Thuật Tự Nhiên (v4.5)
========================================================================================================
Triết lý thiết kế (Anti-AI-Cliché Architectural, Engineering & PMO Print System v4.5):
1. ZERO WHITE TEXT LOCK (Điều 12b AGENTS.md):
   - Tuyệt đối cấm dùng chữ màu trắng (#FFFFFF / RGBColor(255, 255, 255)) trong mọi bảng biểu Word (.docx),
     bảng tính Excel (.xlsx) và biểu đồ kỹ thuật.
2. TYPOGRAPHY & MARGIN FLOOR LOCK (Điều 12c AGENTS.md — Chuẩn Nghị định 30/2020/NĐ-CP & TCVN 7284/7285):
   - Phông chữ chuẩn văn bản pháp lý & thuyết minh kỹ thuật: `Times New Roman` (Unicode TCVN 6909:2001).
   - Định lề trang A4 Dọc (21.0 x 29.7 cm): Lề trái 3.0 cm (chừa gáy đóng hồ sơ), Lề phải 1.8 cm,
     Lề trên 2.0 cm, Lề dưới 2.0 cm (vùng in thực tế = 16.2 cm = 9185 twips).
   - Profile A (Văn bản hành chính, Tờ trình, Báo cáo thẩm định, Kế hoạch PMO):
     Lời văn 13.0pt, H1 14.0pt Bold IN HOA, H2 13.5pt Bold, H3 13.0pt Bold Italic,
     Header bảng 11.5pt Bold, Dữ liệu bảng 11.0pt, Chú thích 11.0pt Italic.
   - Profile B (Thuyết minh tính toán & Phụ lục chi tiết SKILL_PHULUC):
     Lời văn 12.0pt–12.5pt, Header bảng 11.0pt–11.5pt Bold, Dữ liệu bảng 10.5pt–11.0pt (Sàn tối thiểu 10.5pt).
   - Bảng tính Excel (.xlsx): Tiêu đề 16.0pt Bold, Phân khu 12.0pt Bold, Header cột 11.5pt Bold,
     Dữ liệu bảng 11.0pt, Ghi chú/Trạng thái 10.5pt–11.0pt (Tuyệt đối cấm cỡ chữ < 10.0pt).
"""

from typing import Dict, Any, Optional

# 1. MÀU MỰC CHỮ & TIÊU ĐỀ (TYPOGRAPHY INK)
INK_PRIMARY = "1E3246"          # Xanh Thép Trầm (Deep Prussian Slate) — H1, Table Header Text, Summary Text
INK_SECONDARY = "2E4A62"        # Xanh Đá Phiến Trầm (Muted Steel Slate) — H2, Subheadings, Links
INK_TERTIARY = "4A5D6E"         # Xám Chì Ấm (Warm Pewter) — H3, Captions, Metadata
INK_BODY = "1C1E21"             # Mực Than Chì In Ấn (Charcoal Press Ink) — 100% Body & Data Cell Text
INK_MUTED = "5A626A"            # Xám Tro Kỹ Thuật (Technical Ash Grey) — Ghi chú phụ, N/A

# 2. MÀU NỀN BẢNG BIỂU IN ẤN TỰ NHIÊN (NATURAL PRINT SURFACES — LUMA > 88%)
SURFACE_WHITE = "FFFFFF"        # Nền Trắng Giấy In
SURFACE_HEADER_TINT = "DCE4EC"  # Nền Header Bảng Chính: Xanh Đá Phiến Sương Nhạt (Soft Mineral Slate Tint)
SURFACE_HEADER_LIME = "EAE6DF"  # Nền Header Bảng Phụ / TVTK: Đá Vôi Sáng (Warm Limestone)
SURFACE_SUBHDR_TINT = "E8EEF3"  # Nền Sub-header: Sương Lam Nhạt
SURFACE_ZEBRA = "F8F7F4"        # Nền Dòng Dữ Liệu Xen Kẽ: Ngà Giấy Tự Nhiên (Natural Ivory Paper)
SURFACE_SECTION_BG = "EFECE6"   # Nền Dải Phân Khu (Section Banner): Xám Cát Ấm
SURFACE_SUMMARY_BG = "F2EFE9"   # Nền Dòng Tổng Kết / Cột Nhãn: Xám Khoáng Ấm (Warm Alabaster)
SURFACE_SUMMARY_OK = "EBF3ED"   # Nền Dòng Tổng Kết Đạt: Xô Thơm Nhạt (Soft Sage Tint)
SURFACE_TOTAL_BG = "ECEAE4"     # Nền Dòng Tổng Cộng Kế Toán

# Aliases tương thích ngược
PRIMARY_SLATE = INK_PRIMARY
SECONDARY_SLATE = INK_SECONDARY
TERTIARY_PEWTER = INK_TERTIARY
BODY_CHARCOAL = INK_BODY
MUTED_GREY = INK_MUTED
HEADER_BG_SLATE = SURFACE_HEADER_TINT
HEADER_BG_LIMESTONE = SURFACE_HEADER_LIME
HEADER_TEXT_DARK = INK_PRIMARY
ZEBRA_IVORY = SURFACE_ZEBRA
LABEL_ALABASTER = SURFACE_SUMMARY_BG

WHITE = SURFACE_WHITE
TEXT_BODY = INK_BODY
TEXT_MUTED = INK_MUTED
SURFACE_META_BANNER = SURFACE_HEADER_LIME
SURFACE_SUMMARY = SURFACE_SUMMARY_BG
BORDER_GRID = "D0CEC7"
ACCENT_BRONZE = "A67C37"

# 3. ĐƯỜNG KẺ KHUNG & LƯỚI BẢNG (ARCHITECTURAL BORDERS)
BORDER_OUTER_DARK = "1E3246"    # Viền bao ngoài & viền đôi chân Header
BORDER_ACCENT_OCHRE = "A67C37"  # Viền nhấn Đồng Thau Trầm (Bronze Ochre)
BORDER_GRID_STONE = "D0CEC7"    # Đường lưới mảnh Xám Đá Tự Nhiên (Warm Stone Rule)
BORDER_GRID_LIGHT = "D9D6CE"    # Đường lưới phụ

# 4. NHÃN TRẠNG THÁI GỐC KHOÁNG (MINERAL SEMANTIC PILLS — ZERO NEON)
STATUS_PASS_TEXT = "1E5631"     # Xanh Rừng Thông (Forest Pine)
STATUS_PASS_BG = "EBF3ED"       # Nền Xô Thơm Nhạt (Soft Sage)
STATUS_WARN_TEXT = "8F5314"     # Nâu Hổ Phách Đất (Raw Umber Ochre)
STATUS_WARN_BG = "FBF3E4"       # Nền Cát Ấm (Warm Sand)
STATUS_FAIL_TEXT = "8C261E"     # Đỏ Gạch Nung (Carmine Brick)
STATUS_FAIL_BG = "F9EBE8"       # Nền Đất Nung Nhạt (Terracotta Tint)
STATUS_INFO_TEXT = "1F4E5B"     # Xanh Lam Khoáng (Deep Slate Teal)
STATUS_INFO_BG = "EDF3F5"       # Nền Sương Đá (Mineral Ice)
STATUS_NA_TEXT = "7F8A96"       # Xám Đá Trung Tính
STATUS_NA_BG = "F3F4F6"         # Nền Xám Mờ

SAFE_TEXT = STATUS_PASS_TEXT
SAFE_BG = STATUS_PASS_BG
MAJOR_TEXT = STATUS_WARN_TEXT
MAJOR_BG = STATUS_WARN_BG
CRITICAL_TEXT = STATUS_FAIL_TEXT
CRITICAL_BG = STATUS_FAIL_BG
OPTIMAL_TEXT = STATUS_INFO_TEXT
OPTIMAL_BG = STATUS_INFO_BG
EMPTY_TEXT = STATUS_NA_TEXT
EMPTY_BG = STATUS_NA_BG

# 5. QUY CÁCH PHÔNG CHỮ, CỠ CHỮ & ĐỊNH LỀ CHUẨN NGHỊ ĐỊNH 30/2020/NĐ-CP & TCVN 7285:2003
FONT_WORD_LEGAL = "Times New Roman"
FONT_EXCEL_GRID = "Times New Roman"

# Định lề trang A4 Dọc (21.0 x 29.7 cm) theo Phụ lục I Nghị định 30/2020/NĐ-CP
MARGIN_TOP_CM = 2.0             # Cách mép trên 20–25 mm
MARGIN_BOTTOM_CM = 2.0          # Cách mép dưới 20–25 mm (nâng từ 1.8 cm lên 2.0 cm)
MARGIN_LEFT_CM = 3.0            # Cách mép trái 30–35 mm (nâng từ 2.8 cm lên 3.0 cm để đóng gáy)
MARGIN_RIGHT_CM = 1.8           # Cách mép phải 15–20 mm
PRINT_WIDTH_CM = 16.2           # 21.0 - 3.0 - 1.8 = 16.2 cm (9185 twips)
PRINT_WIDTH_TWIPS = 9185

# Profile A — Văn bản Pháp lý / Tờ trình / Báo cáo Thẩm định / Kế hoạch PMO (NĐ 30/2020/NĐ-CP)
WORD_LEGAL_TITLE_PT = 16.0
WORD_LEGAL_H1_PT = 14.0
WORD_LEGAL_H2_PT = 13.5
WORD_LEGAL_H3_PT = 13.0
WORD_LEGAL_BODY_PT = 13.0
WORD_LEGAL_TBL_HDR_PT = 11.5
WORD_LEGAL_TBL_BODY_PT = 11.0
WORD_LEGAL_CAPTION_PT = 11.0
WORD_LEGAL_HF_PT = 10.0

# Profile B — Thuyết minh Tính toán Kỹ thuật & Phụ lục Chi tiết (SKILL_PHULUC)
WORD_TECH_BODY_PT = 12.5
WORD_TECH_TBL_HDR_PT = 11.0
WORD_TECH_TBL_BODY_PT = 10.5
WORD_MIN_TABLE_FLOOR_PT = 10.5
WORD_MIN_CAPTION_FLOOR_PT = 10.0

# Cỡ chữ chuẩn cho Bảng tính Excel (.xlsx — Times New Roman)
EXCEL_TITLE_PT = 16.0
EXCEL_SUBTITLE_PT = 11.0
EXCEL_SEC_HDR_PT = 12.0
EXCEL_COL_HDR_PT = 11.5
EXCEL_BODY_PT = 11.0
EXCEL_NOTE_PT = 10.5
EXCEL_KPI_VAL_PT = 14.0
EXCEL_KPI_LBL_PT = 10.5

# 6. BẢNG MÀU BIỂU ĐỒ KỸ THUẬT & MS PROJECT GANTT (PMO STANDARD)
CHART_PALETTE = ["#1E3246", "#2E4A62", "#A67C37", "#1E5631", "#8F5314", "#8C261E"]
GANTT_SUMMARY_BAR = "#1E3246"
GANTT_CRITICAL_BAR = "#D32F2F"
GANTT_STANDARD_BAR = "#1976D2"
GANTT_MILESTONE = "#263238"
GANTT_ARROW = "#455A64"
GANTT_HOLIDAY_BG = "#FFEBEE"
GANTT_HOLIDAY_EDGE = "#EF9A9A"


def _hex_luminance(hex_str: str) -> float:
    """Tính độ sáng cảm nhận (Perceived Luminance 0..255) của mã màu HEX."""
    clean = str(hex_str or "").strip().lstrip("#").upper()
    if len(clean) == 8:
        clean = clean[-6:]
    if len(clean) != 6:
        return 255.0
    try:
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b
    except Exception:
        return 255.0


def _iter_all_docx_tables(parent):
    """Duyệt đệ quy toàn bộ bảng biểu trong Document, Section Header/Footer và Nested Cells."""
    for tbl in getattr(parent, "tables", []):
        yield tbl
        for row in tbl.rows:
            for cell in row.cells:
                yield from _iter_all_docx_tables(cell)


def add_legal_appendix_header(
    doc,
    appendix_roman: str = "I",
    appendix_title: str = "BẢNG TỔNG HỢP KẾ HOẠCH TIẾN ĐỘ & PHÂN TÍCH ĐƯỜNG GĂNG (CPM)",
    parent_doc_ref: str = "(Kèm theo Báo cáo/Hồ sơ Kế hoạch Quản lý Dự án của Ban Quản lý Dự án)",
):
    """
    Khởi tạo Khối Tiêu Đề Đầu Trang Phụ Lục chuẩn Phụ lục I Nghị định 30/2020/NĐ-CP:
      - Dòng 1: "Phụ lục I" (chữ in thường, số La Mã, canh giữa, 14pt Bold, kiểu chữ đứng).
      - Dòng 2: TÊN PHỤ LỤC (chữ IN HOA, canh giữa, 14pt Bold, kiểu chữ đứng).
      - Dòng 3: Thông tin chỉ dẫn kèm theo văn bản (chữ thường nghiêng, canh giữa, 13pt Italic).
    """
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    p_num = doc.add_paragraph()
    p_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_num.paragraph_format.space_before = Pt(6)
    p_num.paragraph_format.space_after = Pt(2)
    p_num.paragraph_format.keep_with_next = True
    r_num = p_num.add_run(f"Phụ lục {appendix_roman}".strip())
    r_num.font.name = FONT_WORD_LEGAL
    r_num.font.size = Pt(14)
    r_num.font.bold = True
    r_num.font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_before = Pt(0)
    p_tit.paragraph_format.space_after = Pt(2)
    p_tit.paragraph_format.keep_with_next = True
    r_tit = p_tit.add_run(appendix_title.upper())
    r_tit.font.name = FONT_WORD_LEGAL
    r_tit.font.size = Pt(14)
    r_tit.font.bold = True
    r_tit.font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    if parent_doc_ref:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(8)
        p_ref.paragraph_format.keep_with_next = True
        r_ref = p_ref.add_run(parent_doc_ref)
        r_ref.font.name = FONT_WORD_LEGAL
        r_ref.font.size = Pt(13)
        r_ref.font.italic = True
        r_ref.font.color.rgb = RGBColor(0x1C, 0x1E, 0x21)

    return p_tit


def sanitize_docx_table_colors(
    doc,
    default_header_text_hex: str = INK_PRIMARY,
    default_body_text_hex: str = INK_BODY,
    default_header_bg_hex: str = SURFACE_HEADER_TINT,
    enforce_font_floor: bool = True,
) -> Dict[str, int]:
    """
    MODULE TỰ ĐỘNG KIỂM TOÁN & SỬA LỖI BẢNG BIỂU & CỠ CHỮ WORD (AUTO-LINTER — ĐIỀU 12B & 12C AGENTS.MD):
    Trước khi thực hiện `doc.save()`, tự động quét 100% các `run` và ô (`tcPr/shd`) trong toàn bộ văn bản:
      1. Chốt chặn Chữ Trắng (`FFFFFF`): Tự động ghi đè về `#1E3246` (Header) hoặc `#1C1E21` (Data).
      2. Chốt chặn Nền Tối (`Luminance < 140`): Tự động chuyển về `#DCE4EC` (Xanh Đá Phiến Sương Nhạt).
      3. Chốt chặn Sàn Cỡ Chữ (`enforce_font_floor=True`):
         - Trong bảng biểu: Mọi `run` có cỡ chữ `< 10.5pt` được nâng tự động lên `10.5pt` (hoặc `11.0pt` nếu là dòng Header).
         - Ngoài bảng biểu (Body/Captions): Mọi `run` có cỡ chữ `< 10.0pt` được nâng tự động lên `10.5pt`.
    """
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn

    stats = {
        "white_runs_fixed": 0,
        "dark_cells_fixed": 0,
        "small_fonts_fixed": 0,
        "tables_scanned": 0,
    }
    seen_tc = set()

    containers = [doc]
    for sec in getattr(doc, "sections", []):
        for hf_attr in ("header", "footer", "first_page_header", "first_page_footer", "even_page_header", "even_page_footer"):
            hf = getattr(sec, hf_attr, None)
            if hf is not None:
                containers.append(hf)

    for container in containers:
        for tbl in _iter_all_docx_tables(container):
            stats["tables_scanned"] += 1
            for r_idx, row in enumerate(tbl.rows):
                for cell in row.cells:
                    tc_id = id(cell._tc)
                    if tc_id not in seen_tc:
                        seen_tc.add(tc_id)
                        tcPr = cell._tc.find(qn("w:tcPr"))
                        if tcPr is not None:
                            for shd in tcPr.findall(qn("w:shd")):
                                fill_val = (shd.get(qn("w:fill")) or "").strip().upper()
                                if fill_val and fill_val not in ("AUTO", "NONE", "FFFFFF"):
                                    if _hex_luminance(fill_val) < 140.0:
                                        shd.set(qn("w:fill"), default_header_bg_hex)
                                        stats["dark_cells_fixed"] += 1

                    for p in cell.paragraphs:
                        pPr = p._p.find(qn("w:pPr"))
                        if pPr is not None:
                            for p_shd in pPr.findall(qn("w:shd")):
                                p_fill = (p_shd.get(qn("w:fill")) or "").strip().upper()
                                if p_fill and p_fill not in ("AUTO", "NONE", "FFFFFF"):
                                    if _hex_luminance(p_fill) < 140.0:
                                        p_shd.set(qn("w:fill"), default_header_bg_hex)
                                        stats["dark_cells_fixed"] += 1

                        for run in p.runs:
                            is_white = False
                            try:
                                if run.font and run.font.color and run.font.color.rgb:
                                    if str(run.font.color.rgb).upper() == "FFFFFF":
                                        is_white = True
                            except Exception:
                                pass

                            rPr = run._r.find(qn("w:rPr"))
                            if rPr is not None:
                                c_elem = rPr.find(qn("w:color"))
                                if c_elem is not None:
                                    c_val = (c_elem.get(qn("w:val")) or "").strip().upper()
                                    if c_val == "FFFFFF":
                                        is_white = True

                            if is_white:
                                target_hex = default_header_text_hex if (run.bold or r_idx == 0) else default_body_text_hex
                                run.font.color.rgb = RGBColor.from_string(target_hex)
                                stats["white_runs_fixed"] += 1

                            if enforce_font_floor and container is doc:
                                try:
                                    if run.font and run.font.size is not None:
                                        cur_pt = run.font.size.pt
                                        min_pt = 11.0 if r_idx == 0 else WORD_MIN_TABLE_FLOOR_PT
                                        if 0 < cur_pt < min_pt:
                                            run.font.size = Pt(min_pt)
                                            stats["small_fonts_fixed"] += 1
                                except Exception:
                                    pass

                        for r_elem in p._p.iter(qn("w:r")):
                            rPr = r_elem.find(qn("w:rPr"))
                            if rPr is not None:
                                c_elem = rPr.find(qn("w:color"))
                                if c_elem is not None:
                                    c_val = (c_elem.get(qn("w:val")) or "").strip().upper()
                                    if c_val == "FFFFFF":
                                        c_elem.set(qn("w:val"), default_header_text_hex if r_idx == 0 else default_body_text_hex)
                                        stats["white_runs_fixed"] += 1

    # Quét các đoạn văn bản ngoài bảng trong body chính để nâng các chú thích < 10.0pt lên 10.5pt
    if enforce_font_floor:
        for p in getattr(doc, "paragraphs", []):
            for run in p.runs:
                try:
                    if run.font and run.font.size is not None:
                        cur_pt = run.font.size.pt
                        if 0 < cur_pt < WORD_MIN_CAPTION_FLOOR_PT:
                            run.font.size = Pt(10.5)
                            stats["small_fonts_fixed"] += 1
                except Exception:
                    pass

    return stats
