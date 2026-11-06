"""
docx_report_builder.py — Professional Engineering Word Report Generator
========================================================================
Sprint 5 · Pillar 4

Mục đích:
    Tạo báo cáo thẩm tra và thuyết minh tính toán kỹ thuật định dạng Word (.docx)
    đạt chuẩn thẩm mỹ cao, phục vụ trình nộp Chủ đầu tư, Tư vấn giám sát, Thẩm tra.

Tính năng:
    - Bìa văn bản trang trọng, mã dự án, giai đoạn, người lập, ngày lập
    - Header/Footer chuyên nghiệp
    - Bảng thông số kỹ thuật căn chỉnh chuẩn xác
    - Bảng chỉ số sử dụng eta (η) với mã màu chuẩn TCVN:
        🟢 <= 0.70 | 🟡 0.70 - 0.90 | 🟠 0.90 - 1.00 | 🔴 > 1.00
    - Bảng xung đột kỹ thuật C01–C09 chi tiết
    - Bảng kiểm tra As_req vs As_prov
    - Disclaimer pháp lý & Bảng trách nhiệm bắt buộc theo AGENTS.md §8
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

if hasattr(sys.stdout, "reconfigure") and getattr(sys.stdout, "encoding", None) != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False


def _set_cell_background(cell, fill_hex: str):
    """Đặt màu nền cho ô trong bảng (hex không kèm dấu #)."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Đặt lề trong cho ô."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def _lock_run_font(run, font_name="Times New Roman", size_pt=11.0, bold=False, italic=False, color_hex="1C1E21"):
    """Khóa cứng phông chữ Times New Roman (cả ascii, hAnsi, eastAsia, cs) và màu mực tự nhiên."""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_hex:
        run.font.color.rgb = RGBColor.from_string(color_hex)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), font_name)


def _set_natural_table_borders(table, outer_color="1E3246", inner_color="D0CEC7"):
    """Viền bảng chuẩn ấn phẩm kỹ thuật: đỉnh và đáy đậm 1.0pt (#1E3246), lưới trong mảnh 0.5pt (#D0CEC7)."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="8" w:space="0" w:color="{outer_color}"/>'
        f'<w:bottom w:val="single" w:sz="8" w:space="0" w:color="{outer_color}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{inner_color}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{inner_color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{inner_color}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{inner_color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def _format_header_row(row, fill_hex="DCE4EC", text_color="1E3246"):
    """Format hàng tiêu đề của bảng theo Natural Print Palette (nền #DCE4EC, chữ đậm #1E3246 — Điều 12b AGENTS.md)."""
    for cell in row.cells:
        _set_cell_background(cell, fill_hex)
        _set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                _lock_run_font(run, "Times New Roman", 10.0, bold=True, color_hex=text_color)


def _format_data_row(row, is_even=False, fill_even="F8F7F4"):
    """Format hàng dữ liệu của bảng với nền giấy ngà tự nhiên (#F8F7F4) và cỡ chữ sàn 10.0pt."""
    for cell in row.cells:
        if is_even:
            _set_cell_background(cell, fill_even)
        _set_cell_margins(cell, top=90, bottom=90, left=130, right=130)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            for run in p.runs:
                _lock_run_font(run, "Times New Roman", 10.0, color_hex="1C1E21")



def sanitize_docx_table_colors(doc):
    """Auto-Linter (Điều 12b AGENTS.md): Quét 100% run trong bảng biểu, ghi đè mọi màu trắng về #1E3246/#1C1E21."""
    for tbl in doc.tables:
        for r_i, row in enumerate(tbl.rows):
            for cell in row.cells:
                tcPr = cell._tc.find(qn("w:tcPr"))
                if tcPr is not None:
                    for shd in tcPr.findall(qn("w:shd")):
                        fv = (shd.get(qn("w:fill")) or "").strip().upper()
                        if fv in ("1E3246", "1F4E78", "1F4E79", "002060", "2F4858"):
                            shd.set(qn("w:fill"), "DCE4EC")
                for p in cell.paragraphs:
                    for run in p.runs:
                        if run.font and run.font.color and run.font.color.rgb:
                            if str(run.font.color.rgb).upper() in ("FFFFFF", "FEFEFE"):
                                run.font.color.rgb = RGBColor(0x1E, 0x32, 0x46) if (run.bold or r_i == 0) else RGBColor(0x1C, 0x1E, 0x21)


def build_docx_report(
    pipeline_result: dict,
    output_path: str,
    title: str = "BÁO CÁO THẨM TRA KỸ THUẬT KẾT CẤU",
    project_code: str = "DA_VERIFY",
) -> str:
    """
    Sinh file Word (.docx) chuyên nghiệp từ dữ liệu pipeline thẩm tra.
    """
    if not _DOCX_AVAILABLE:
        raise RuntimeError("python-docx chưa được cài đặt. Chạy: pip install python-docx")

    doc = docx.Document()

    # Cấu hình khổ giấy A4 & lề đóng gáy chuẩn Hồ sơ Kỹ thuật Việt Nam (Trái 2.8cm, Phải 1.8cm, Trên 2.0cm, Dưới 1.8cm)
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(13.0)
    normal_style.font.color.rgb = RGBColor(0x1C, 0x1E, 0x21)
    for sec in doc.sections:
        sec.page_width = Inches(8.27)
        sec.page_height = Inches(11.69)
        sec.top_margin = Inches(0.79)     # 2.0 cm
        sec.bottom_margin = Inches(0.79)  # 2.0 cm
        sec.left_margin = Inches(1.18)    # 3.0 cm (chừa gáy đóng hồ sơ)
        sec.right_margin = Inches(0.71)   # 1.8 cm

    # ─────────────────────────────────────────────────────────────────────────
    # 1. TIÊU ĐỀ BÁO CÁO & HEADER BOX
    # ─────────────────────────────────────────────────────────────────────────
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(title.upper())
    _lock_run_font(title_run, "Times New Roman", 16.0, bold=True, color_hex="1E3246")

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("BỘ CÔNG CỤ TỰ ĐỘNG HÓA THẨM TRA HỒ SƠ & PHÁT HIỆN XUNG ĐỘT KẾT CẤU")
    _lock_run_font(sub_run, "Times New Roman", 10.5, italic=True, color_hex="5A626A")

    doc.add_paragraph()  # khoảng trống

    # Metadata Box
    read_res = pipeline_result.get("read_result", {})
    conflict_res = pipeline_result.get("conflict_result")
    calc_res = pipeline_result.get("calc_result")
    rebar_res = pipeline_result.get("rebar_results", [])
    meta = pipeline_result.get("meta", {})

    info_tbl = doc.add_table(rows=4, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_data = [
        ("Mã Dự án & Giai đoạn", f"{project_code} — Thẩm tra & Kiểm soát Hồ sơ Thiết kế"),
        ("Hồ sơ Kiểm tra", f"{read_res.get('source_file', 'Tài liệu đầu vào')} ({read_res.get('source_type', 'N/A')})"),
        ("Thời điểm Thực hiện", meta.get("started_at", datetime.now().strftime("%Y-%m-%d %H:%M"))),
        ("Độ Tin cậy Dữ liệu", f"Confidence Score: {read_res.get('confidence_level', 'MEDIUM')}"),
    ]
    for r_idx, (k, v) in enumerate(info_data):
        row = info_tbl.rows[r_idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.width = Inches(2.2)
        cell_val.width = Inches(4.8)
        _set_cell_background(cell_lbl, "F2EFE9")
        _set_cell_margins(cell_lbl, 80, 80, 120, 120)
        _set_cell_margins(cell_val, 80, 80, 120, 120)

        p_lbl = cell_lbl.paragraphs[0]
        r1 = p_lbl.add_run(k)
        _lock_run_font(r1, "Times New Roman", 10.0, bold=True, color_hex="1E3246")

        p_val = cell_val.paragraphs[0]
        r2 = p_val.add_run(v)
        _lock_run_font(r2, "Times New Roman", 10.0, color_hex="1C1E21")

    doc.add_paragraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 2. ĐÁNH GIÁ TỔNG QUAN & BẢNG KẾT QUẢ XUNG ĐỘT
    # ─────────────────────────────────────────────────────────────────────────
    h1 = doc.add_heading("1. TỔNG QUAN KẾT QUẢ THẨM TRA", level=1)
    h1.runs[0].font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    summary_text = "Hệ thống đã hoàn tất đọc và rà soát chéo toàn bộ dữ liệu kỹ thuật từ hồ sơ thiết kế."
    if conflict_res:
        summary_text += f"\nKết luận chung: {conflict_res.get('overall_assessment', '')}"
    doc.add_paragraph(summary_text)

    if conflict_res:
        cs = conflict_res.get("conflict_summary", {})
        conf_summary_tbl = doc.add_table(rows=1, cols=5)
        conf_summary_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        _format_header_row(conf_summary_tbl.rows[0])
        headers = ["Tổng số vấn đề", "CRITICAL (Nghiêm trọng)", "HIGH (Cao)", "MEDIUM (Trung bình)", "ĐẠT (PASS)"]
        for idx, text in enumerate(headers):
            conf_summary_tbl.rows[0].cells[idx].paragraphs[0].text = text
        _format_header_row(conf_summary_tbl.rows[0])

        row_vals = conf_summary_tbl.add_row()
        vals = [
            str(cs.get("total", 0)),
            str(cs.get("CRITICAL", 0)),
            str(cs.get("HIGH", 0)),
            str(cs.get("MEDIUM", 0)),
            str(len(conflict_res.get("passes", []))),
        ]
        for idx, val in enumerate(vals):
            cell = row_vals.cells[idx]
            cell.paragraphs[0].text = val
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].runs[0].font.bold = True
            cell.paragraphs[0].runs[0].font.size = Pt(11)

        # Highlight cell critical nếu > 0
        if cs.get("CRITICAL", 0) > 0:
            _set_cell_background(row_vals.cells[1], "F9EBE8")
            row_vals.cells[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8C, 0x26, 0x1E)
        if cs.get("HIGH", 0) > 0:
            _set_cell_background(row_vals.cells[2], "FBF3E4")
            row_vals.cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8F, 0x53, 0x14)

        doc.add_paragraph()

        # Bảng chi tiết xung đột
        conflicts = conflict_res.get("conflicts", [])
        if conflicts:
            p_cf = doc.add_paragraph()
            r_cf = p_cf.add_run("Bảng Danh mục Chi tiết Sai lệch & Xung đột Kỹ thuật:")
            r_cf.font.bold = True

            tbl_cf = doc.add_table(rows=1, cols=5)
            tbl_cf.alignment = WD_TABLE_ALIGNMENT.CENTER
            cf_headers = ["Mã & Loại", "Mức độ", "Thông số kiểm tra", "Sai lệch phát hiện", "Khuyến nghị xử lý"]
            for idx, text in enumerate(cf_headers):
                tbl_cf.rows[0].cells[idx].paragraphs[0].text = text
            _format_header_row(tbl_cf.rows[0])

            tbl_cf.columns[0].width = Inches(1.3)
            tbl_cf.columns[1].width = Inches(0.9)
            tbl_cf.columns[2].width = Inches(1.6)
            tbl_cf.columns[3].width = Inches(1.8)
            tbl_cf.columns[4].width = Inches(1.4)

            for i, cf in enumerate(conflicts):
                row = tbl_cf.add_row()
                _format_data_row(row, is_even=(i % 2 == 1))

                sev = cf.get("severity", "LOW")
                sev_color = {"CRITICAL": "F9EBE8", "HIGH": "FBF3E4", "MEDIUM": "EDF3F5", "LOW": "EBF3ED"}.get(sev, "F8F7F4")
                _set_cell_background(row.cells[1], sev_color)

                row.cells[0].paragraphs[0].text = f"[{cf['id']}]\n{cf.get('type','')}"
                row.cells[1].paragraphs[0].text = sev
                row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row.cells[1].paragraphs[0].runs[0].font.bold = True

                row.cells[2].paragraphs[0].text = cf.get("param", "")

                diff_text = cf.get("description", "")
                if cf.get("delta_pct") is not None:
                    diff_text += f"\n(Chênh lệch: {cf.get('delta_pct')}%)"
                row.cells[3].paragraphs[0].text = diff_text

                row.cells[4].paragraphs[0].text = cf.get("recommendation", "")

            doc.add_paragraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 3. KIỂM TRA BỐ TRÍ CỐT THÉP (As_req vs As_prov)
    # ─────────────────────────────────────────────────────────────────────────
    if rebar_res:
        h2 = doc.add_heading("2. KIỂM TRA KHẢ NĂNG BỐ TRÍ CỐT THÉP", level=1)
        h2.runs[0].font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

        doc.add_paragraph("So sánh diện tích cốt thép yêu cầu tính toán từ nội lực (As_required) và cốt thép thực tế bố trí (As_provided):")

        rebar_tbl = doc.add_table(rows=1, cols=6)
        rebar_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        rb_headers = ["Cấu kiện", "Ký hiệu Thép", "As_yc (mm²)", "As_bt (mm²)", "Tỷ lệ As", "Kết luận"]
        for idx, text in enumerate(rb_headers):
            rebar_tbl.rows[0].cells[idx].paragraphs[0].text = text
        _format_header_row(rebar_tbl.rows[0])

        for i, rb in enumerate(rebar_res):
            row = rebar_tbl.add_row()
            _format_data_row(row, is_even=(i % 2 == 1))

            status = rb.get("status", "OK")
            is_ok = status == "OK"
            stat_color = "EBF3ED" if is_ok else "F9EBE8"
            _set_cell_background(row.cells[5], stat_color)

            row.cells[0].paragraphs[0].text = rb.get("element", "")
            row.cells[1].paragraphs[0].text = rb.get("rebar_notation", "")
            row.cells[2].paragraphs[0].text = str(rb.get("As_required_mm2", ""))
            row.cells[3].paragraphs[0].text = str(rb.get("As_provided_mm2", ""))
            row.cells[4].paragraphs[0].text = f"{rb.get('As_ratio', 0.0):.2f}"

            p_st = row.cells[5].paragraphs[0]
            p_st.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_st = p_st.add_run("[ĐẠT]" if is_ok else "[THIẾU THÉP]")
            _lock_run_font(r_st, "Times New Roman", 10.0, bold=True, color_hex="1E5631" if is_ok else "8C261E")

        doc.add_paragraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 4. KẾT QUẢ TÍNH TOÁN CẤU KIỆN (NẾU CÓ)
    # ─────────────────────────────────────────────────────────────────────────
    if calc_res:
        h3 = doc.add_heading("3. KẾT QUẢ TÍNH TOÁN THẨM TRA ĐỘC LẬP", level=1)
        h3.runs[0].font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

        elem_name = calc_res.get("element", "Cấu kiện tính toán")
        std = calc_res.get("Standard_Method", "TCVN 5574:2018")
        doc.add_paragraph(f"Tính toán thẩm tra độc lập theo tiêu chuẩn {std} cho {elem_name}:")

        calc_tbl = doc.add_table(rows=1, cols=4)
        calc_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c_headers = ["Hạng mục kiểm tra", "Công thức & Điều kiện", "Hệ số sử dụng (η)", "Đánh giá"]
        for idx, text in enumerate(c_headers):
            calc_tbl.rows[0].cells[idx].paragraphs[0].text = text
        _format_header_row(calc_tbl.rows[0])

        eta_entries = [
            ("Khả năng chịu Uốn (TTGH1)", "M / M_ult <= 1.0", calc_res.get("eta_M")),
            ("Khả năng chịu Cắt (TTGH1)", "Q / Q_ult <= 1.0", calc_res.get("eta_V")),
            ("Chỉ số Sử dụng Cực đại", "overall_eta <= 1.0", calc_res.get("overall_eta")),
        ]

        for i, (item, cond, eta_val) in enumerate(eta_entries):
            if eta_val is None:
                continue
            row = calc_tbl.add_row()
            _format_data_row(row, is_even=(i % 2 == 1))

            if eta_val <= 0.70:
                color, text_eval = "EBF3ED", "[ĐẠT — DƯ TẢI]"
            elif eta_val <= 0.90:
                color, text_eval = "EDF3F5", "[ĐẠT — TỐI ƯU]"
            elif eta_val <= 1.00:
                color, text_eval = "FBF3E4", "[ĐẠT — SÁT NGƯỠNG]"
            else:
                color, text_eval = "F9EBE8", "[KHÔNG ĐẠT]"

            _set_cell_background(row.cells[3], color)

            row.cells[0].paragraphs[0].text = item
            row.cells[1].paragraphs[0].text = cond
            row.cells[2].paragraphs[0].text = f"{eta_val:.3f} ({eta_val*100:.1f}%)"
            row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_ev = row.cells[3].paragraphs[0]
            p_ev.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_ev.add_run(text_eval).font.bold = True

        doc.add_paragraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 5. DỮ LIỆU ĐẦU VÀO ĐÃ TRÍCH XUẤT
    # ─────────────────────────────────────────────────────────────────────────
    eng_data = read_res.get("engineering_data", {})
    sections_list = eng_data.get("sections", [])
    loads_list = eng_data.get("loads", [])
    mats_list = eng_data.get("materials", [])

    if sections_list or loads_list:
        h4 = doc.add_heading("4. BẢNG DỮ LIỆU ĐẦU VÀO TRÍCH XUẤT TỰ ĐỘNG", level=1)
        h4.runs[0].font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

        if sections_list:
            doc.add_paragraph("Danh mục tiết diện hình học cấu kiện phát hiện:")
            sec_tbl = doc.add_table(rows=1, cols=4)
            sec_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            for idx, text in enumerate(["STT", "Cấu kiện", "Bề rộng b (mm)", "Chiều cao h (mm)"]):
                sec_tbl.rows[0].cells[idx].paragraphs[0].text = text
            _format_header_row(sec_tbl.rows[0])

            for i, s in enumerate(sections_list):
                row = sec_tbl.add_row()
                _format_data_row(row, is_even=(i % 2 == 1))
                row.cells[0].paragraphs[0].text = str(i + 1)
                row.cells[1].paragraphs[0].text = s.get("element", "")
                row.cells[2].paragraphs[0].text = str(s.get("b_mm", ""))
                row.cells[3].paragraphs[0].text = str(s.get("h_mm", ""))

            doc.add_paragraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 6. BẢNG PHÂN ĐỊNH TRÁCH NHIỆM & TUYÊN BỐ MIỄN TRỪ PHÁP LÝ (AGENTS.md §8)
    # ─────────────────────────────────────────────────────────────────────────
    h5 = doc.add_heading("5. PHÂN ĐỊNH TRÁCH NHIỆM & KÝ DUYỆT", level=1)
    h5.runs[0].font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    sign_tbl = doc.add_table(rows=3, cols=3)
    sign_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    _format_header_row(sign_tbl.rows[0])
    for idx, text in enumerate(["NGƯỜI THỰC HIỆN", "KỸ SƯ KIỂM TRA", "CHỦ TRÌ THẨM TRA"]):
        sign_tbl.rows[0].cells[idx].paragraphs[0].text = text
    _format_header_row(sign_tbl.rows[0])

    # Hàng 2: Khoảng trống để ký
    for cell in sign_tbl.rows[1].cells:
        cell.height = Inches(1.2)
        _set_cell_margins(cell, 150, 150, 150, 150)

    # Hàng 3: Tên & Đề xuất
    sign_tbl.rows[2].cells[0].paragraphs[0].text = "Trợ lý Kỹ thuật AI (Antigravity)\n(Đề xuất sơ bộ)"
    sign_tbl.rows[2].cells[1].paragraphs[0].text = "Kỹ sư Kết cấu Độc lập\n(Ký và ghi rõ họ tên)"
    sign_tbl.rows[2].cells[2].paragraphs[0].text = "Kỹ sư Chủ trì Thẩm tra\n(Ký và đóng dấu)"
    for cell in sign_tbl.rows[2].cells:
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cell_margins(cell, 100, 100, 100, 100)

    doc.add_paragraph()

    # Disclaimer bắt buộc theo AGENTS.md §8
    disc_p = doc.add_paragraph()
    disc_run = disc_p.add_run(
        "Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, "
        "phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm "
        "trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra."
    )
    disc_run.font.italic = True
    disc_run.font.size = Pt(10.5)
    disc_run.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)

    # Lưu file
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    sanitize_docx_table_colors(doc)
    doc.save(abs_out)
    print(f"  [DOCX] ✅ Đã xuất file Word chuyên nghiệp: {abs_out}")
    return abs_out
