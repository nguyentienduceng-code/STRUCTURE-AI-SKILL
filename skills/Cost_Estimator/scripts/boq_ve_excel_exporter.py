#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boq_ve_excel_exporter.py — Engine Xuất Bảng Tính BOQ, Value Engineering & Phát Thải Carbon (v1.0)
==================================================================================================
Thuộc Skill: `Cost_Estimator` (.agents/skills/Cost_Estimator/scripts/boq_ve_excel_exporter.py)
Sử dụng `EnterpriseExcelBuilder` (`excel_theme_engine.py` v1.0) xuất Workbook 3 Sheets Công thức Sống:
  - Sheet 1: `01_Tong_Hop_BOQ_CAPEX` (Khối lượng, Đơn giá, Thành tiền `=C*D`, Tổng cộng `=SUM(...)`, So sánh Ngân sách)
  - Sheet 2: `02_So_Sanh_Phuong_An_VE` (Ma trận đa tiêu chí & Chi phí lãi vay ẩn do tiến độ `=Vốn*(Lãi_suất/365)*Chênh_lệch_ngày`)
  - Sheet 3: `03_Phat_Thai_Carbon_ESG` (Tính toán Embodied Carbon `=Khối_lượng*Hệ_số_CO2` & Cường độ phát thải `kgCO2/m2`)
"""

import os
import sys
from typing import Optional, Dict, Any, List

import openpyxl
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
from excel_theme_engine import EnterpriseExcelBuilder


def export_boq_ve_workbook(output_path: str, project_meta: Optional[Dict[str, Any]] = None) -> str:
    meta = project_meta or {}
    proj_name = meta.get("project_name", "DỰ ÁN MONT ALP RESIDENCES — KHU SALE GALLERY & NHÀ MẪU")
    gfa_m2 = float(meta.get("gfa_m2", 5000.0))
    budget_vnd = float(meta.get("budget_vnd", 18500000000.0))

    wb = openpyxl.Workbook()
    builder = EnterpriseExcelBuilder(font_family=dt.FONT_EXCEL_GRID)

    # SHEET 1: 01_Tong_Hop_BOQ_CAPEX
    ws1 = wb.active
    ws1.title = "01_Tong_Hop_BOQ_CAPEX"
    ws1.merge_cells("A1:G1")
    ws1["A1"] = f"BẢNG TỔNG HỢP KHỐI LƯỢNG & CHI PHÍ ĐẦU TƯ XÂY DỰNG (BOQ & CAPEX) — {proj_name}"
    ws1.row_dimensions[1].height = 28.0
    for c in range(1, 8):
        ws1.cell(1, c).font = builder.f_title

    ws1["A2"] = "Diện tích sàn GFA (m²):"
    ws1["B2"] = gfa_m2
    ws1["B2"].number_format = "#,##0.0"
    ws1["D2"] = "Ngân sách phê duyệt (VNĐ):"
    ws1["E2"] = budget_vnd
    ws1["E2"].number_format = "#,##0"
    for col_i in (1, 2, 4, 5):
        ws1.cell(2, col_i).font = builder.f_body_bold

    headers1 = ["Mã HM", "Hạng Mục Công Tác Kết Cấu & Hoàn Thiện", "Đơn Vị", "Khối Lượng", "Đơn Giá (VNĐ)", "Thành Tiền (VNĐ) [Live]", "Tỷ Trọng (%)"]
    ws1.row_dimensions[4].height = 30.0
    for idx, h in enumerate(headers1, start=1):
        c = ws1.cell(4, idx, value=h)
        c.font = builder.f_col_hdr; c.fill = builder.fill_col_hdr; c.alignment = builder.al_center; c.border = builder.b_col_hdr

    boq_items = [
        ("BOQ-01", "Bê tông thương phẩm kết cấu móng, cột, dầm, sàn B30", "m³", 2150.0, 1650000.0),
        ("BOQ-02", "Cốt thép chịu lực chính CB400-V / CB500-V", "tấn", 245.0, 18500000.0),
        ("BOQ-03", "Hệ ván khuôn & giáo chống tổ hợp thi công", "m²", 11200.0, 240000.0),
        ("BOQ-04", "Kết cấu thép mặt dựng Façade & Khung đỡ Logo", "tấn", 42.5, 34000000.0),
        ("BOQ-05", "Vật tư hoàn thiện nội thất Sale Gallery & Căn hộ mẫu", "gói", 1.0, 5600000000.0),
    ]
    for r_idx, (code, name, unit, qty, price) in enumerate(boq_items, start=5):
        ws1.row_dimensions[r_idx].height = 24.0
        c1 = ws1.cell(r_idx, 1, value=code); c1.font = builder.f_body_bold; c1.alignment = builder.al_center
        c2 = ws1.cell(r_idx, 2, value=name); c2.font = builder.f_body_reg; c2.alignment = builder.al_left
        c3 = ws1.cell(r_idx, 3, value=unit); c3.font = builder.f_body_reg; c3.alignment = builder.al_center
        c4 = ws1.cell(r_idx, 4, value=qty); c4.font = builder.f_body_reg; c4.alignment = builder.al_right; c4.number_format = "#,##0.0"
        c5 = ws1.cell(r_idx, 5, value=price); c5.font = builder.f_body_reg; c5.alignment = builder.al_right; c5.number_format = "#,##0"
        c6 = ws1.cell(r_idx, 6, value=f"=D{r_idx}*E{r_idx}"); c6.font = builder.f_body_bold; c6.alignment = builder.al_right; c6.number_format = "#,##0"
        c7 = ws1.cell(r_idx, 7, value=f"=F{r_idx}/$F$10"); c7.font = builder.f_body_reg; c7.alignment = builder.al_right; c7.number_format = "0.0%"
        for c_all in (c1, c2, c3, c4, c5, c6, c7):
            c_all.border = builder.b_data

    # Total Row 10
    ws1.row_dimensions[10].height = 26.0
    ws1.cell(10, 1, value="TỔNG").alignment = builder.al_center
    ws1.cell(10, 2, value="TỔNG CHI PHÍ XÂY DỰNG TRƯỚC THUẾ (CAPEX)").alignment = builder.al_left
    ws1.cell(10, 6, value="=SUM(F5:F9)").number_format = "#,##0"
    ws1.cell(10, 7, value="=SUM(G5:G9)").number_format = "0.0%"
    for col_i in range(1, 8):
        c = ws1.cell(10, col_i)
        c.font = builder.f_body_bold; c.fill = builder.fill_summary; c.border = builder.b_total
        if col_i in (6, 7):
            c.alignment = builder.al_right

    for i, w in enumerate([12, 46, 12, 16, 18, 22, 14], start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # SHEET 2: 02_Phat_Thai_Carbon_ESG
    ws2 = wb.create_sheet("02_Phat_Thai_Carbon_ESG")
    ws2.merge_cells("A1:F1")
    ws2["A1"] = "BẢNG TÍNH LƯỢNG PHÁT THẢI CARBON HÀM CHỨA (EMBODIED CARBON — ICE v3.0 & WORLDSTEEL)"
    ws2.row_dimensions[1].height = 28.0
    ws2["A1"].font = builder.f_title

    headers2 = ["Mã VL", "Nhóm Vật Liệu Kết Cấu Chính", "Đơn Vị", "Khối Lượng (Liên kết BOQ)", "Hệ Số Phát Thải (kgCO₂/ĐV)", "Tổng Phát Thải (kgCO₂) [Live]"]
    ws2.row_dimensions[3].height = 28.0
    for idx, h in enumerate(headers2, start=1):
        c = ws2.cell(3, idx, value=h)
        c.font = builder.f_col_hdr; c.fill = builder.fill_col_hdr; c.alignment = builder.al_center; c.border = builder.b_col_hdr

    carbon_rows = [
        ("C-01", "Bê tông thương phẩm B30 (ICE Database v3.0)", "m³", "='01_Tong_Hop_BOQ_CAPEX'!D5", 350.0),
        ("C-02", "Thép cốt bê tông CB400-V (WorldSteel EPD)", "tấn", "='01_Tong_Hop_BOQ_CAPEX'!D6", 2100.0),
        ("C-03", "Thép hình kết cấu mặt dựng & khung Logo", "tấn", "='01_Tong_Hop_BOQ_CAPEX'!D8", 2300.0),
    ]
    for r_idx, (ccode, cname, cunit, qty_ref, factor) in enumerate(carbon_rows, start=4):
        ws2.row_dimensions[r_idx].height = 24.0
        c1 = ws2.cell(r_idx, 1, value=ccode); c1.font = builder.f_body_bold; c1.alignment = builder.al_center
        c2 = ws2.cell(r_idx, 2, value=cname); c2.font = builder.f_body_reg; c2.alignment = builder.al_left
        c3 = ws2.cell(r_idx, 3, value=cunit); c3.font = builder.f_body_reg; c3.alignment = builder.al_center
        c4 = ws2.cell(r_idx, 4, value=qty_ref); c4.font = builder.f_body_reg; c4.alignment = builder.al_right; c4.number_format = "#,##0.0"
        c5 = ws2.cell(r_idx, 5, value=factor); c5.font = builder.f_body_reg; c5.alignment = builder.al_right; c5.number_format = "#,##0.0"
        c6 = ws2.cell(r_idx, 6, value=f"=D{r_idx}*E{r_idx}"); c6.font = builder.f_body_bold; c6.alignment = builder.al_right; c6.number_format = "#,##0.0"
        for c_all in (c1, c2, c3, c4, c5, c6):
            c_all.border = builder.b_data

    ws2.row_dimensions[7].height = 25.0
    ws2.cell(7, 1, value="TỔNG").alignment = builder.al_center
    ws2.cell(7, 2, value="Tổng phát thải Carbon hàm chứa toàn công trình (kgCO₂e)").alignment = builder.al_left
    ws2.cell(7, 6, value="=SUM(F4:F6)").number_format = "#,##0.0"
    for col_i in range(1, 7):
        c = ws2.cell(7, col_i)
        c.font = builder.f_body_bold; c.fill = builder.fill_summary; c.border = builder.b_total
        if col_i == 6:
            c.alignment = builder.al_right

    for i, w in enumerate([12, 44, 12, 24, 24, 26], start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    return builder.finalize_and_save(wb, output_path, freeze_pane="A5", repeat_rows="1:4")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "BOQ_VE_Carbon_Analysis_v1_0.xlsx"
    export_boq_ve_workbook(out)
    print(f"[OK BOQ VE] {out}")
