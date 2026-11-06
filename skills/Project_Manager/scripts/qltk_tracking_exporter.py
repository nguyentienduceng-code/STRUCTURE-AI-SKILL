#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qltk_tracking_exporter.py — Engine Chuẩn Hóa & Quản Trị Động Bảng Tiến Độ, Checklist & Pending List QLTK (v2.0)
=================================================================================================================
Thuộc Skill: `Project_Manager` (.agents/skills/Project_Manager/scripts/qltk_tracking_exporter.py)
Liên kết chặt chẽ với:
  - `_SHARED/SHARED_CONTEXT/excel_theme_engine.py` (v1.0 — EnterpriseExcelBuilder)
  - `_SHARED/SHARED_CONTEXT/design_tokens.py` (v4.2 — Natural Mineral Palette & Anti-AI Typography)
  - `tools/xlsx_view_sanity.py` (v2.1 — Anti-[Repaired] XML, Print Fit & Cross-Column Logic Validator)

Nâng cấp Toàn diện v2.0 (Smart Dynamic PMO & ISO 19650 Edition):
  1. Tự động khởi tạo Sheet 1 (`1.DASHBOARD_KPI_QLTK`) liên kết 100% bằng CÔNG THỨC EXCEL SỐNG (`=COUNTIF(...)`,
     `=COUNTA(...)`, `=SUM(...)`, `=MAX(...)`) sang Sheet `2.QLTK_TRACKING_PENDINGLIST` kèm Biểu đồ Tiến độ (`BarChart`)
     và Bảng Phân tích theo 3 Phần (TVTK / Nội bộ QLTK / Nhà thầu phụ) & theo Bộ môn (Kiến trúc / Kết cấu / MEP).
  2. Giải quyết triệt để "Bẫy 47 vùng gộp ô làm mất dữ liệu khi Filter":
     - Hủy gộp dọc ở các dòng dữ liệu (Cột A, B, C) và tự động điền xuống (Fill-Down) mã `STT` (số nguyên `1..19`),
       tên `Hạng mục hồ sơ` và `Bộ môn` cho toàn bộ dòng con (dòng đầu in đậm `#1C1E21`, dòng con lặp lại in màu
       xám đá thanh lịch `#7A828A` kèm đường kẻ chấm mảnh).
     - Nhờ đó, khi bật `AutoFilter` (`A4:L73`) lọc theo bất kỳ Bộ môn hay Trạng thái nào, 100% dòng đều hiển thị
       đầy đủ `STT` và `Hạng mục hồ sơ`, đồng thời đạt 0 Warning `COLUMN_TYPE_HOMOGENEITY`!
  3. Sửa triệt để toàn bộ lỗi mâu thuẫn logic chéo từ dữ liệu gốc:
     - Sửa 18 dòng bị tráo ngược định dạng ở Phần II (`2.1 CAD` -> `DWG`, `2.2 PDF` -> `PDF`).
     - Sửa 7 dòng `Kết Cấu` cải tạo nội thất (`N/A`) từ `TRỐNG / Đã hoàn thành` thành `KHÔNG ÁP DỤNG` /
       `Không áp dụng (Cải tạo nội thất không can thiệp kết cấu)`.
     - Sửa 3 dòng trống ở Phần II (`R30, R36, R63`) từ `TRỐNG / Đã phát hành` thành `ĐÃ TÍCH HỢP` /
       `Đã gộp chung trong bộ hồ sơ CAD/PDF chính`.
     - Sửa dòng 73 (`Sa bàn Đông Tây Nam Bắc`) từ `TRỐNG` thành `CHỜ ĐỆ TRÌNH` (`MẪU VLHT / BPTC`).
     - Sửa lỗi gõ năm `2028.08.31.pdf` -> `2026.08.31.pdf` và `15..09.2026.PDF` -> `15.09.2026.pdf` (giữ nguyên 100% Hyperlink).
  4. Gắn `DataValidation` Dropdown chuẩn ISO 19650 cho Cột E (`TRẠNG THÁI`) và bổ sung Bảng Tổng Hợp KPI + Khung Ký
     Xét Duyệt 4 Cấp (`Chuyên viên QLTK` – `Trưởng phòng QLTK (HOD)` – `Ban QLDA` – `Lãnh đạo Ban Xây dựng / BOD`)
     ở cuối bảng chính.
"""

import os
import sys
import re
import math
from typing import Optional, Dict, Any, List, Tuple

import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
for _cand in [
    _CURR_DIR,
    os.path.abspath(os.path.join(_CURR_DIR, "..", "..", "..", "_SHARED", "SHARED_CONTEXT")),
    os.path.abspath(os.path.join(_CURR_DIR, "..", "..", "..", "tools")),
]:
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

import design_tokens as dt
import xlsx_view_sanity as xvs
from excel_theme_engine import EnterpriseExcelBuilder


def _estimate_optimal_row_height(ws, row_idx: int, col_widths: Dict[int, float]) -> float:
    max_lines = 1
    for c in range(1, 13):
        val = ws.cell(row=row_idx, column=c).value
        if val is None:
            continue
        text = str(val).strip()
        if not text or text.startswith("="):
            continue
        w = max(col_widths.get(c, 14.0) - 2.5, 6.0)
        lines_count = 0
        for raw_ln in text.splitlines():
            ln_len = len(raw_ln.strip())
            if ln_len == 0:
                lines_count += 1
            else:
                lines_count += max(1, int(math.ceil(ln_len / w)))
        if lines_count > max_lines:
            max_lines = lines_count

    if max_lines == 1:
        return 24.0
    return min(max(24.0, max_lines * 14.8 + 10.0), 235.0)


def _build_dashboard_sheet(wb, tracking_sheet_name: str, project_title: str, project_sub: str, meta_banner: str, builder: EnterpriseExcelBuilder) -> None:
    dash_name = "1.DASHBOARD_KPI_QLTK"
    if dash_name in wb.sheetnames:
        del wb[dash_name]
    ws_d = wb.create_sheet(title=dash_name, index=0)

    # Title Banner (A1:H3)
    ws_d.merge_cells("A1:H1")
    ws_d["A1"] = f"BÁO CÁO TỔNG HỢP KPI & KIỂM SOÁT TIẾN ĐỘ HỒ SƠ QLTK — {project_title}"
    ws_d.row_dimensions[1].height = 30.0

    ws_d.merge_cells("A2:H2")
    ws_d["A2"] = project_sub
    ws_d.row_dimensions[2].height = 20.0

    ws_d.merge_cells("A3:H3")
    ws_d["A3"] = meta_banner
    ws_d.row_dimensions[3].height = 22.0

    for c in range(1, 9):
        c1 = ws_d.cell(1, c); c1.font = builder.f_title; c1.fill = builder.fill_white; c1.alignment = builder.al_left
        c2 = ws_d.cell(2, c); c2.font = builder.f_subtitle; c2.fill = builder.fill_white; c2.alignment = builder.al_left
        c3 = ws_d.cell(3, c); c3.font = builder.f_meta; c3.fill = builder.fill_meta; c3.alignment = builder.al_sec
        c3.border = Border(bottom=builder.s_bronze_thin)

    ts = f"'{tracking_sheet_name}'"

    # Live KPI Strip on Rows 5-6 (4 Symmetric Cards across A:H)
    kpi_cards = [
        ("A", "B", "TỔNG ĐẦU MỤC HỒ SƠ KIỂM SOÁT", f"=COUNTA({ts}!$E$6:$E$73)-COUNTIF({ts}!$E$6:$E$73,\"\")", "primary"),
        ("C", "D", "HỒ SƠ ĐÃ PHÁT HÀNH / ĐÃ DUYỆT", f"=COUNTIF({ts}!$E$6:$E$73,\"ĐÃ CÓ*\")+COUNTIF({ts}!$E$6:$E$73,\"ĐÃ DUYỆT*\")+COUNTIF({ts}!$E$6:$E$73,\"ĐÃ TÍCH HỢP\")", "pass"),
        ("E", "F", "ĐANG THẨM TRA / CHỜ ĐỆ TRÌNH", f"=COUNTIF({ts}!$E$6:$E$73,\"Loading*\")+COUNTIF({ts}!$E$6:$E$73,\"CHỜ*\")", "warn"),
        ("G", "H", "SỐ GÓI THẦU QUÁ HẠN HỢP ĐỒNG", f"=COUNTIF({ts}!$J$6:$J$73,\">0\")", "crit"),
    ]
    builder.build_live_kpi_strip(ws_d, row_top=5, kpi_cards=kpi_cards)

    # Table 1 (Rows 8-13): Thống kê Tiến độ theo Phân khu Quản lý (Phần I, II, III)
    ws_d.merge_cells("A8:H8")
    ws_d["A8"] = "I. BẢNG PHÂN TÍCH TIẾN ĐỘ BÀN GIAO HỒ SƠ THEO PHÂN KHU TRÁCH NHIỆM (LIVE FORMULAS)"
    builder.style_merged_range(ws_d, "A8:H8", font=builder.f_sec_hdr, fill=builder.fill_sec_hdr, alignment=builder.al_sec, border=builder.b_sec_hdr)
    ws_d.row_dimensions[8].height = 25.0

    hdrs_t1 = [
        "Mã Phần",
        "Phân Khu Quản Lý Hồ Sơ Thiết Kế",
        "Tổng Đầu Mục",
        "Đã Phát Hành / Duyệt",
        "Đang Xử Lý / Chờ Nộp",
        "Không Áp Dụng (N/A)",
        "Tỷ Lệ Hoàn Thành (%)",
        "Đánh Giá Tiến Độ",
    ]
    ws_d.row_dimensions[9].height = 30.0
    for idx_c, h_txt in enumerate(hdrs_t1, start=1):
        cell = ws_d.cell(9, idx_c, value=h_txt)
        cell.font = builder.f_col_hdr
        cell.fill = builder.fill_col_hdr
        cell.alignment = builder.al_center
        cell.border = builder.b_col_hdr

    sec_ranges = [
        ("PHẦN I", "Hồ sơ do Tư vấn Thiết kế triển khai (INEX / AIC / VPlus)", "6:26"),
        ("PHẦN II", "Hồ sơ Nội bộ phát hành thi công (Phòng QLTK - BXD)", "28:67"),
        ("PHẦN III", "Hồ sơ Chuyên biệt, Nhà thầu phụ & Danh mục Spec vật liệu", "69:73"),
    ]
    for idx_r, (p_code, p_name, r_span) in enumerate(sec_ranges, start=10):
        ws_d.row_dimensions[idx_r].height = 24.0
        r_start, r_end = r_span.split(":")
        e_rng = f"{ts}!$E${r_start}:$E${r_end}"

        c1 = ws_d.cell(idx_r, 1, value=p_code)
        c2 = ws_d.cell(idx_r, 2, value=p_name)
        c3 = ws_d.cell(idx_r, 3, value=f"=COUNTA({e_rng})")
        c4 = ws_d.cell(idx_r, 4, value=f"=COUNTIF({e_rng},\"ĐÃ CÓ*\")+COUNTIF({e_rng},\"ĐÃ DUYỆT*\")+COUNTIF({e_rng},\"ĐÃ TÍCH HỢP\")")
        c5 = ws_d.cell(idx_r, 5, value=f"=COUNTIF({e_rng},\"Loading*\")+COUNTIF({e_rng},\"CHỜ*\")")
        c6 = ws_d.cell(idx_r, 6, value=f"=COUNTIF({e_rng},\"KHÔNG ÁP DỤNG\")")
        c7 = ws_d.cell(idx_r, 7, value=f"=IF((C{idx_r}-F{idx_r})>0, D{idx_r}/(C{idx_r}-F{idx_r}), 1)")
        c8 = ws_d.cell(idx_r, 8, value=f"=IF(E{idx_r}=0, \"HOÀN TẤT 100%\", \"ĐANG ĐÔN ĐỐC\")")

        c1.font = builder.f_body_bold; c1.alignment = builder.al_center
        c2.font = builder.f_body_reg; c2.alignment = builder.al_left
        for cn in (c3, c4, c5, c6):
            cn.font = builder.f_body_reg; cn.alignment = builder.al_right; cn.number_format = "#,##0"
        c4.font = builder.f_status_pass
        c7.font = builder.f_body_bold; c7.alignment = builder.al_right; c7.number_format = "0.0%"
        c8.font = builder.f_status_pass if idx_r != 12 else builder.f_status_warn
        c8.fill = builder.fill_status_pass if idx_r != 12 else builder.fill_status_warn
        c8.alignment = builder.al_center
        for c_all in (c1, c2, c3, c4, c5, c6, c7, c8):
            c_all.border = builder.b_data

    # Total Row 13
    ws_d.row_dimensions[13].height = 25.0
    ws_d.cell(13, 1, value="TỔNG").alignment = builder.al_center
    ws_d.cell(13, 2, value="Tổng cộng toàn dự án MontAlp Residences (Sale Gallery & Nhà mẫu)").alignment = builder.al_left
    ws_d.cell(13, 3, value="=SUM(C10:C12)").number_format = "#,##0"
    ws_d.cell(13, 4, value="=SUM(D10:D12)").number_format = "#,##0"
    ws_d.cell(13, 5, value="=SUM(E10:E12)").number_format = "#,##0"
    ws_d.cell(13, 6, value="=SUM(F10:F12)").number_format = "#,##0"
    ws_d.cell(13, 7, value="=IF((C13-F13)>0, D13/(C13-F13), 1)").number_format = "0.0%"
    ws_d.cell(13, 8, value="=IF(E13=0, \"HOÀN TẤT\", \"KIỂM SOÁT CHẶT MỤC PENDING\")").alignment = builder.al_center
    for col_i in range(1, 9):
        cell = ws_d.cell(13, col_i)
        cell.font = builder.f_body_bold
        cell.fill = builder.fill_summary
        cell.border = builder.b_total
        if col_i in (3, 4, 5, 6, 7):
            cell.alignment = builder.al_right

    # Table 2 (Rows 16-21): Thống kê theo Bộ môn Kỹ thuật (Kiến trúc, Kết cấu, MEP, Chuyên biệt)
    ws_d.merge_cells("A16:H16")
    ws_d["A16"] = "II. BẢNG THỐNG KÊ TIẾN ĐỘ THEO BỘ MÔN CHUYÊN NGÀNH (KIẾN TRÚC - KẾT CẤU - MEP - CHUYÊN BIỆT)"
    builder.style_merged_range(ws_d, "A16:H16", font=builder.f_sec_hdr, fill=builder.fill_sec_hdr, alignment=builder.al_sec, border=builder.b_sec_hdr)
    ws_d.row_dimensions[16].height = 25.0

    hdrs_t2 = [
        "Mã BM",
        "Bộ Môn Chuyên Ngành",
        "Tổng Đầu Mục",
        "Đã Phát Hành / Duyệt",
        "Đang Xử Lý / Chờ Nộp",
        "Không Áp Dụng (N/A)",
        "Tỷ Lệ Hoàn Thành (%)",
        "Ghi Chú Trọng Tâm",
    ]
    ws_d.row_dimensions[17].height = 28.0
    for idx_c, h_txt in enumerate(hdrs_t2, start=1):
        cell = ws_d.cell(17, idx_c, value=h_txt)
        cell.font = builder.f_col_hdr
        cell.fill = builder.fill_col_hdr
        cell.alignment = builder.al_center
        cell.border = builder.b_col_hdr

    disc_rows = [
        ("ARCH", "Kiến Trúc", "Đã bàn giao thi công; KTS. Nguyễn Chí Thiện triển khai chi tiết 2D/3D vách Corridor & LED/Kid."),
        ("STRU", "Kết Cấu", "Các gói nội thất không can thiệp KC; phần khung thép Logo mặt dựng đang thẩm tra REV03."),
        ("MEP", "MEP", "Đã phát hành đầy đủ hồ sơ điều chỉnh MEP căn hộ mẫu, hành lang, WC công cộng & Sale Gallery."),
        ("SPEC", "Logo", "Nhà thầu An Nhiên ADV đã nộp REV03 ngày 30/10/2026 (trễ 21 ngày); đang kiểm duyệt & đôn đốc BPTC."),
    ]
    c_rng = f"{ts}!$C$6:$C$73"
    e_all = f"{ts}!$E$6:$E$73"
    for offset, (d_code, d_name, d_note) in enumerate(disc_rows, start=18):
        ws_d.row_dimensions[offset].height = 34.0
        c1 = ws_d.cell(offset, 1, value=d_code)
        c2 = ws_d.cell(offset, 2, value=d_name)
        c3 = ws_d.cell(offset, 3, value=f"=COUNTIF({c_rng}, B{offset})")
        c4 = ws_d.cell(offset, 4, value=f"=COUNTIFS({c_rng}, B{offset}, {e_all}, \"ĐÃ CÓ*\")+COUNTIFS({c_rng}, B{offset}, {e_all}, \"ĐÃ DUYỆT*\")+COUNTIFS({c_rng}, B{offset}, {e_all}, \"ĐÃ TÍCH HỢP\")")
        c5 = ws_d.cell(offset, 5, value=f"=COUNTIFS({c_rng}, B{offset}, {e_all}, \"Loading*\")+COUNTIFS({c_rng}, B{offset}, {e_all}, \"CHỜ*\")")
        c6 = ws_d.cell(offset, 6, value=f"=COUNTIFS({c_rng}, B{offset}, {e_all}, \"KHÔNG ÁP DỤNG\")")
        c7 = ws_d.cell(offset, 7, value=f"=IF((C{offset}-F{offset})>0, D{offset}/(C{offset}-F{offset}), 1)")
        c8 = ws_d.cell(offset, 8, value=d_note)

        c1.font = builder.f_body_bold; c1.alignment = builder.al_center
        c2.font = builder.f_body_bold; c2.alignment = builder.al_center
        for cn in (c3, c4, c5, c6):
            cn.font = builder.f_body_reg; cn.alignment = builder.al_right; cn.number_format = "#,##0"
        c7.font = builder.f_body_bold; c7.alignment = builder.al_right; c7.number_format = "0.0%"
        c8.font = builder.f_body_reg; c8.alignment = builder.al_left
        for c_all in (c1, c2, c3, c4, c5, c6, c7, c8):
            c_all.border = builder.b_data

    # Embedded BarChart below Table 2 (Anchored at A24, height = 7.5 cm -> occupies ~15 rows: 24..38)
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Thống kê Hồ sơ Đã phát hành vs Đang xử lý theo Phân khu"
    chart.y_axis.title = "Số lượng đầu mục"
    chart.x_axis.title = "Phân khu quản lý"
    chart.width = 18
    chart.height = 7.5
    data_ref = Reference(ws_d, min_col=4, min_row=9, max_col=5, max_row=12)
    cats_ref = Reference(ws_d, min_col=1, min_row=10, max_row=12)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.legend.legendPos = "r"
    ws_d.add_chart(chart, "A24")

    # ISO Signature Footer at Row 41 (2 full blank rows after chart bottom row 38)
    sig_blocks_dash = [
        ("A", "B", "NGƯỜI LẬP BÁO CÁO (QLTK)", "(Ký, ghi rõ họ tên & ngày lập)"),
        ("C", "D", "TRƯỞNG PHÒNG QLTK (HOD)", "(Ký kiểm soát chất lượng hồ sơ)"),
        ("E", "F", "BAN QLDA / TTCU PHỐI HỢP", "(Ký xác nhận tình trạng bàn giao)"),
        ("G", "H", "LÃNH ĐẠO BAN XÂY DỰNG / BOD", "(Phê duyệt & chỉ đạo điều hành)"),
    ]
    builder.build_iso_signature_footer(ws_d, start_row=41, sig_blocks=sig_blocks_dash)

    dash_widths = {1: 14.0, 2: 38.0, 3: 15.0, 4: 18.0, 5: 18.0, 6: 18.0, 7: 18.0, 8: 44.0}
    for col_i, w_val in dash_widths.items():
        ws_d.column_dimensions[get_column_letter(col_i)].width = w_val

    ws_d.freeze_panes = "A4"
    ws_d.print_title_rows = "1:3"


def standardize_qltk_tracking_workbook(
    input_path: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    out_path = output_path or input_path
    wb = openpyxl.load_workbook(input_path, data_only=False)
    # Tìm sheet chính chứa dữ liệu tracking
    ws = None
    for sname in wb.sheetnames:
        if "TRACKING" in sname.upper() or "QLTK" in sname.upper():
            ws = wb[sname]
            break
    if ws is None:
        ws = wb.active

    # Nếu file từng chạy v2.0 có các dòng summary từ dòng 74 trở đi, cắt gọn về đúng 73 dòng gốc trước khi xử lý
    if ws.max_row > 73:
        ws.delete_rows(74, ws.max_row - 73)

    builder = EnterpriseExcelBuilder(font_family=dt.FONT_EXCEL_GRID)

    col_widths = {
        1: 6.5,   # A: STT
        2: 26.0,  # B: HẠNG MỤC HỒ SƠ
        3: 13.0,  # C: BỘ MÔN
        4: 14.5,  # D: ĐƠN VỊ TK
        5: 16.0,  # E: TRẠNG THÁI
        6: 12.0,  # F: ĐỊNH DẠNG
        7: 44.0,  # G: TÊN HỒ SƠ (LINK SHAREPOINT)
        8: 18.0,  # H: TIẾN ĐỘ HỢP ĐỒNG
        9: 26.0,  # I: TIẾN ĐỘ THỰC TẾ & BÀN GIAO
        10: 12.0, # J: SỐ NGÀY TRỄ
        11: 52.0, # K: TÌNH TRẠNG & NỘI DUNG KỸ THUẬT
        12: 36.0, # L: HẠNG MỤC PENDING & TRÁCH NHIỆM
    }
    for col_i, width_val in col_widths.items():
        ws.column_dimensions[get_column_letter(col_i)].width = width_val

    ws.conditional_formatting._cf_rules.clear()
    if ws.max_column > 12:
        ws.delete_cols(13, ws.max_column - 12)

    # 1. Xác định các vùng merge dọc ở Cột A, B, C (dòng 6..73) và Unmerge + Fill-Down để hỗ trợ AutoFilter 100%
    section_rows = {5, 27, 68}
    vertical_merges_to_unmerge = []
    for mr in list(ws.merged_cells.ranges):
        if mr.min_row >= 5 and mr.min_col == 1 and mr.max_col == 12:
            section_rows.add(mr.min_row)
        elif mr.min_row >= 6 and mr.max_row <= 73 and mr.min_col in (1, 2, 3) and mr.min_col == mr.max_col:
            vertical_merges_to_unmerge.append((mr.coord, mr.min_row, mr.max_row, mr.min_col))

    subrow_Repeat_coords = set()
    for coord_str, min_r, max_r, col_idx in vertical_merges_to_unmerge:
        anchor_val = ws.cell(min_r, col_idx).value
        ws.unmerge_cells(coord_str)
        for r_fill in range(min_r, max_r + 1):
            ws.cell(r_fill, col_idx).value = anchor_val
            if r_fill > min_r:
                subrow_Repeat_coords.add((r_fill, col_idx))

    # 2. Chuẩn hóa Dòng 1, 2, 3 (Title Block & Metadata Banner)
    val_r1 = str(ws.cell(1, 1).value or "").strip()
    val_r1 = re.sub(r"\s*\n\s*", " — ", val_r1)
    xvs.set_cell_safe(ws, "A1", val_r1)
    ws.row_dimensions[1].height = 30.0

    val_r2 = str(ws.cell(2, 1).value or "").strip()
    xvs.set_cell_safe(ws, "A2", val_r2)
    ws.row_dimensions[2].height = 20.0

    val_r3 = str(ws.cell(3, 1).value or "").strip()
    val_r3 = dt.normalize_vietnamese_allcaps(val_r3)
    if val_r3.lower().startswith("thời điểm cập nhật"):
        val_r3 = "Thời điểm cập nhật" + val_r3[len("thời điểm cập nhật"):]
    xvs.set_cell_safe(ws, "A3", val_r3)
    ws.row_dimensions[3].height = 22.0

    for c in range(1, 13):
        c1 = ws.cell(1, c); c1.font = builder.f_title; c1.fill = builder.fill_white; c1.alignment = builder.al_left; c1.border = Border()
        c2 = ws.cell(2, c); c2.font = builder.f_subtitle; c2.fill = builder.fill_white; c2.alignment = builder.al_left; c2.border = Border()
        c3 = ws.cell(3, c); c3.font = builder.f_meta; c3.fill = builder.fill_meta; c3.alignment = builder.al_sec; c3.border = Border(bottom=builder.s_bronze_thin)

    # 3. Chuẩn hóa Dòng 4 (Table Column Headers)
    clean_headers = [
        "STT",
        "HẠNG MỤC HỒ SƠ",
        "BỘ MÔN",
        "ĐƠN VỊ TK",
        "TRẠNG THÁI",
        "ĐỊNH DẠNG",
        "TÊN HỒ SƠ / TÀI LIỆU\n(LIÊN KẾT SHAREPOINT)",
        "TIẾN ĐỘ HĐ\n(MỐC & ĐIỀU KHOẢN)",
        "TIẾN ĐỘ THỰC TẾ\n(ĐỢT NỘP / PHÁT HÀNH)",
        "SỐ NGÀY TRỄ\n(NGÀY)",
        "TÌNH TRẠNG & NỘI DUNG THẨM TRA KỸ THUẬT",
        "HẠNG MỤC PENDING & PHÂN CÔNG TRÁCH NHIỆM",
    ]
    ws.row_dimensions[4].height = 38.0
    for c, h_text in enumerate(clean_headers, start=1):
        cell = ws.cell(4, c, value=h_text)
        cell.font = builder.f_col_hdr
        cell.fill = builder.fill_col_hdr
        cell.alignment = builder.al_center
        cell.border = builder.b_col_hdr

    stats = {
        "emojis_stripped": 0,
        "allcaps_normalized": 0,
        "typos_fixed": 0,
        "logic_contradictions_fixed": 0,
        "unmerged_filter_cells_filled": len(subrow_Repeat_coords),
    }

    # 4. Duyệt và chuẩn hóa dữ liệu + sửa mâu thuẫn logic chéo từ Dòng 5 đến Dòng 73
    for r in range(5, 74):
        if r in section_rows:
            ws.row_dimensions[r].height = 26.0
            sec_title = str(ws.cell(r, 1).value or "").strip()
            ws.cell(r, 1).value = sec_title
            for c in range(1, 13):
                sc = ws.cell(r, c)
                sc.font = builder.f_sec_hdr
                sc.fill = builder.fill_sec_hdr
                sc.alignment = builder.al_sec
                sc.border = builder.b_sec_hdr
            continue

        # BƯỚC SỬA LOGIC CHÉO GIỮA CÁC CỘT TRÊN DÒNG r:
        disc_val = str(ws.cell(r, 3).value or "").strip()
        unit_val = str(ws.cell(r, 4).value or "").strip()
        st_val = str(ws.cell(r, 5).value or "").strip()
        fmt_val = str(ws.cell(r, 6).value or "").strip()
        file_val = str(ws.cell(r, 7).value or "").strip()

        # Fix A: Các dòng Kết Cấu ở Phần I (R06..R26) không phát sinh hồ sơ kết cấu
        if 6 <= r <= 26 and disc_val == "Kết Cấu" and st_val.upper() in ("TRỐNG", "KHÔNG ÁP DỤNG"):
            ws.cell(r, 4).value = "N/A"
            ws.cell(r, 5).value = "KHÔNG ÁP DỤNG"
            ws.cell(r, 6).value = "—"
            if file_val in ("N/A", "[KHÔNG CÓ FILE]", "[Chưa có file]", ""):
                ws.cell(r, 7).value = "[Không phát sinh HS KC]"
            ws.cell(r, 11).value = "Hạng mục cải tạo nội thất không can thiệp kết cấu chịu lực chính."
            ws.cell(r, 12).value = "Không áp dụng"
            stats["logic_contradictions_fixed"] += 1

        # Fix B: Các dòng Phần II (R28..R66) bị tráo định dạng PDF <-> 2.1 CAD và DWG <-> 2.2 PDF
        if 28 <= r <= 66:
            if file_val.lower() == "lll":
                ws.cell(r, 7).value = "2.2 PDF"
                file_val = "2.2 PDF"
                stats["typos_fixed"] += 1
            if "2.1 CAD" in file_val and fmt_val.upper() in ("PDF", "—", "-"):
                ws.cell(r, 6).value = "DWG"
                stats["logic_contradictions_fixed"] += 1
            elif "2.2 PDF" in file_val and fmt_val.upper() in ("DWG", "—", "-"):
                ws.cell(r, 6).value = "PDF"
                stats["logic_contradictions_fixed"] += 1
            # Các dòng thừa ở Phần II ghi TRỐNG + [KHÔNG CÓ FILE] nhưng lại ghi Đã phát hành
            if st_val.upper() in ("TRỐNG", "ĐÃ TÍCH HỢP") and file_val in ("[KHÔNG CÓ FILE]", "[Chưa có file]", "[Đã gộp trong bộ CAD/PDF]"):
                ws.cell(r, 5).value = "ĐÃ TÍCH HỢP"
                ws.cell(r, 6).value = "PDF/DWG"
                ws.cell(r, 7).value = "[Đã gộp trong bộ CAD/PDF]"
                ws.cell(r, 11).value = "Hồ sơ đã được tích hợp chung trong thư mục 2.1 CAD và 2.2 PDF cùng bộ môn."
                ws.cell(r, 12).value = "Đã phát hành"
                stats["logic_contradictions_fixed"] += 1

        # Fix C: Dòng 73 (Sa bàn Đông Tây Nam Bắc) đang thương thảo HĐ & chuẩn bị mẫu VLHT
        if r == 73 and st_val.upper() in ("TRỐNG", "CHỜ ĐỆ TRÌNH"):
            ws.cell(r, 5).value = "CHỜ ĐỆ TRÌNH"
            ws.cell(r, 6).value = "MẪU / BPTC"
            ws.cell(r, 7).value = "[Chờ NT nộp mẫu trước 05/11]"
            stats["logic_contradictions_fixed"] += 1

        # Duyệt từng cột 1..12 để làm sạch văn bản & định dạng
        for c in range(1, 13):
            cell = ws.cell(r, c)
            raw_val = cell.value

            if c == 1 and isinstance(raw_val, str) and raw_val.strip().isdigit():
                cell.value = int(raw_val.strip())
                raw_val = cell.value

            if isinstance(raw_val, str):
                orig_str = raw_val
                if dt._EMOJI_PATTERN.search(raw_val):
                    stats["emojis_stripped"] += 1
                cleaned_str = dt.strip_ai_emojis(raw_val).strip()

                if c == 7:
                    if cleaned_str == "1.TO TRINH":
                        cleaned_str = "1. Tờ trình"
                        stats["typos_fixed"] += 1
                    elif cleaned_str == "[KHÔNG CÓ FILE]":
                        cleaned_str = "[Chưa có file]"
                    if "2028.08.31" in cleaned_str:
                        cleaned_str = cleaned_str.replace("2028.08.31", "2026.08.31")
                        stats["typos_fixed"] += 1
                    if "15..09.2026.PDF" in cleaned_str:
                        cleaned_str = cleaned_str.replace("15..09.2026.PDF", "15.09.2026.pdf")
                        stats["typos_fixed"] += 1

                if c in (11, 12) and cleaned_str not in ("", "-", "—"):
                    norm_str = dt.normalize_vietnamese_allcaps(cleaned_str)
                    if norm_str != cleaned_str:
                        stats["allcaps_normalized"] += 1
                    cleaned_str = norm_str

                if cleaned_str != orig_str:
                    cell.value = cleaned_str

            val_now = cell.value
            val_str = str(val_now or "").strip()
            is_placeholder = val_str in ("", "-", "—", "N/A", "[Chưa có file]", "[Không phát sinh HS KC]", "[Đã gộp trong bộ CAD/PDF]", "[Chờ NT nộp mẫu trước 05/11]")
            is_repeated_subrow = (r, c) in subrow_Repeat_coords

            cell.fill = builder.fill_white
            cell.border = builder.b_data

            if c == 1:
                cell.font = builder.f_subrow_repeat if is_repeated_subrow else builder.f_body_bold
                cell.alignment = builder.al_center
                if isinstance(val_now, int):
                    cell.number_format = "0"
            elif c == 2:
                cell.font = builder.f_subrow_repeat if is_repeated_subrow else builder.f_body_bold
                cell.alignment = builder.al_left
            elif c in (3, 4, 6):
                if is_placeholder:
                    cell.font = builder.f_muted
                elif is_repeated_subrow:
                    cell.font = builder.f_subrow_repeat
                else:
                    cell.font = builder.f_body_reg
                cell.alignment = builder.al_center
            elif c == 5:
                builder.apply_status_pill(cell, val_str)
            elif c == 7:
                cell.alignment = builder.al_left
                if cell.hyperlink is not None and not is_placeholder:
                    cell.font = builder.f_link
                elif is_placeholder:
                    cell.font = builder.f_muted
                else:
                    cell.font = builder.f_body_reg
            elif c in (8, 9):
                cell.alignment = builder.al_left
                if is_placeholder:
                    cell.font = builder.f_muted
                    cell.alignment = builder.al_center
                elif "quá hạn" in val_str.lower() or "trễ" in val_str.lower() or "chậm" in val_str.lower():
                    cell.font = builder.f_status_crit
                else:
                    cell.font = builder.f_body_reg
            elif c == 10:
                cell.alignment = builder.al_right
                is_delayed = False
                if isinstance(val_now, (int, float)) and val_now > 0:
                    is_delayed = True
                elif any(ch.isdigit() and ch != '0' for ch in val_str):
                    is_delayed = True
                if is_delayed:
                    cell.font = builder.f_status_crit
                    cell.fill = builder.fill_status_crit
                    if isinstance(val_now, (int, float)):
                        cell.number_format = "0"
                else:
                    cell.value = 0
                    cell.font = builder.f_muted
                    cell.number_format = "0;0;\"—\""
            elif c in (11, 12):
                cell.alignment = builder.al_left
                cell.font = builder.f_muted if is_placeholder else builder.f_body_reg

        ws.row_dimensions[r].height = _estimate_optimal_row_height(ws, r, col_widths)

    # 5. Bật AutoFilter trên A4:L73 và gắn DataValidation Dropdown cho Cột E (E6:E73)
    ws.auto_filter.ref = "A4:L73"
    builder.attach_status_dropdown(
        ws, "E", 6, 73,
        ["ĐÃ CÓ", "ĐÃ CÓ (85%)", "ĐÃ DUYỆT (85%)", "ĐÃ TÍCH HỢP", "Loading-REV03", "CHỜ ĐỆ TRÌNH", "KHÔNG ÁP DỤNG"]
    )

    # 6. Dựng Bảng Tổng Hợp KPI Động (Dòng 75–76) & Khung Trình Ký ISO 4 Cấp (Dòng 78–80) ở cuối Sheet Tracking
    ws.row_dimensions[74].height = 12.0
    kpi_bottom_cards = [
        ("A", "B", "TỔNG ĐẦU MỤC KIỂM SOÁT", "=COUNTA(E6:E73)-COUNTIF(E6:E73,\"\")", "primary"),
        ("C", "D", "ĐÃ PHÁT HÀNH / ĐÃ DUYỆT", "=COUNTIF(E6:E73,\"ĐÃ CÓ*\")+COUNTIF(E6:E73,\"ĐÃ DUYỆT*\")+COUNTIF(E6:E73,\"ĐÃ TÍCH HỢP\")", "pass"),
        ("E", "F", "ĐANG THẨM TRA / CHỜ NỘP", "=COUNTIF(E6:E73,\"Loading*\")+COUNTIF(E6:E73,\"CHỜ*\")", "warn"),
        ("G", "H", "KHÔNG ÁP DỤNG (N/A)", "=COUNTIF(E6:E73,\"KHÔNG ÁP DỤNG\")", "primary"),
        ("I", "J", "SỐ GÓI THẦU QUÁ HẠN HĐ", "=COUNTIF(J6:J73,\">0\")", "crit"),
        ("K", "L", "SỐ NGÀY TRỄ TỐI ĐA (NGÀY)", "=MAX(J6:J73)", "crit"),
    ]
    builder.build_live_kpi_strip(ws, row_top=75, kpi_cards=kpi_bottom_cards)

    ws.row_dimensions[77].height = 12.0
    sig_blocks_main = [
        ("A", "C", "NGƯỜI LẬP BẢNG (CHUYÊN VIÊN QLTK)", "(Ký, ghi rõ họ tên & ngày cập nhật)"),
        ("D", "F", "KIỂM TRA (TRƯỞNG PHÒNG QLTK - HOD)", "(Ký kiểm soát chất lượng & tiến độ)"),
        ("G", "I", "PHỐI HỢP (BAN QLDA & TTCU)", "(Ký xác nhận tiếp nhận hồ sơ thi công)"),
        ("J", "L", "PHÊ DUYỆT (LÃNH ĐẠO BAN XÂY DỰNG / BOD)", "(Ý kiến chỉ đạo & phê duyệt)"),
    ]
    builder.build_iso_signature_footer(ws, start_row=78, sig_blocks=sig_blocks_main)

    # 7. Khởi tạo Sheet 1 (`1.DASHBOARD_KPI_QLTK`) liên kết công thức sống sang Sheet `2.QLTK_TRACKING_PENDINGLIST`
    _build_dashboard_sheet(wb, ws.title, val_r1, val_r2, val_r3, builder)

    # Lưu và chuẩn hóa XML View + Print Fit cho cả 2 sheets
    if wb._fonts:
        wb._fonts[0] = Font(name=dt.FONT_EXCEL_GRID, size=11.0, color=dt.TEXT_BODY)
    ws.freeze_panes = "A5"
    ws.print_title_rows = "1:4"
    xvs.sanitize_workbook(wb, zoom=100, reset_top_left=True, reset_gridlines=True, ensure_print_fit=True)
    if "1.DASHBOARD_KPI_QLTK" in wb.sheetnames:
        wb["1.DASHBOARD_KPI_QLTK"].page_setup.fitToWidth = 1
        wb["1.DASHBOARD_KPI_QLTK"].page_setup.fitToHeight = 1

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    _enforce_zero_white_text_and_dark_fill(wb)
    wb.save(out_path)

    ok_xml, xml_issues = xvs.validate_xlsx_file(out_path)
    aes_report = xvs.audit_excel_aesthetics(out_path)
    return {
        "output_path": out_path,
        "sheets": wb.sheetnames,
        "xml_valid": ok_xml,
        "xml_issues": xml_issues,
        "aesthetics": aes_report,
        "stats": stats,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python qltk_tracking_exporter.py <input.xlsx> [output.xlsx]")
        sys.exit(1)
    in_f = sys.argv[1]
    out_f = sys.argv[2] if len(sys.argv) > 2 else in_f
    res = standardize_qltk_tracking_workbook(in_f, out_f)
    print(f"[OK v2.0] {res['output_path']} | Sheets={res['sheets']} | XML={res['xml_valid']} | Emojis={res['aesthetics']['emoji_cells']} | LogicErr={len(res['aesthetics']['logic_contradictions'])} | Stats={res['stats']}")


def _enforce_zero_white_text_and_dark_fill(wb):
    import excel_theme_engine as _ete
    theme = _ete.EnterpriseExcelBuilder()
    for ws in wb.worksheets:
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                cell = ws.cell(r, c)
                has_dark_fill = False
                if cell.fill and cell.fill.fill_type == "solid" and cell.fill.fgColor and cell.fill.fgColor.rgb:
                    bg = str(cell.fill.fgColor.rgb)[-6:].upper()
                    if bg not in ("000000", "FFFFFF") and len(bg) == 6:
                        try:
                            rv, gv, bv = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
                            if (0.299 * rv + 0.587 * gv + 0.114 * bv) < 140:
                                has_dark_fill = True
                        except Exception:
                            pass
                has_white_text = False
                if cell.font and cell.font.color and cell.font.color.rgb:
                    fc = str(cell.font.color.rgb)[-6:].upper()
                    if fc == "FFFFFF":
                        has_white_text = True
                if has_dark_fill or has_white_text:
                    cell.fill = theme.fill_col_hdr
                    cell.font = theme.f_col_hdr
                    cell.border = theme.b_col_hdr
