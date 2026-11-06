#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iso_kpi_exporter.py — Engine Chuẩn Hóa Biểu Mẫu Kế Hoạch & Kết Quả SXKD / Đánh Giá KPI Cá Nhân (v1.0)
=======================================================================================================
Thuộc Skill: `Project_Manager` (.agents/skills/Project_Manager/scripts/iso_kpi_exporter.py)
 Chuẩn hóa theo Biểu mẫu ISO Ban Xây dựng - Phòng Quản lý Thiết kế (`ISO-MAU KH VA KQ SXKD`),
 tích hợp Hệ màu Khoáng vật Tự nhiên (`design_tokens.py` v4.2) và Công thức Excel Sống (`=G*D/E`, `=SUM(...)`).
"""

import os
import sys
from typing import Optional, Dict, Any

import openpyxl
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


def standardize_iso_kpi_workbook(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Chuẩn hóa file biểu mẫu ISO Kế hoạch & Kết quả SXKD / KPI Cá nhân (`T11.26-KH`, `T10.26-KQ`)
    sang bảng màu khoáng vật tự nhiên (Natural Mineral Palette v4.2), bảo toàn 100% công thức `=G7*D7/E7` và `=SUM(...)`.
    """
    out_path = output_path or input_path
    wb = openpyxl.load_workbook(input_path, data_only=False)

    font_family = dt.FONT_EXCEL_GRID  # "Arial"
    f_title = Font(name=font_family, size=16.0, bold=True, color=dt.INK_PRIMARY)
    f_sub = Font(name=font_family, size=11.5, bold=True, color=dt.INK_TERTIARY)
    f_hdr_main = Font(name=font_family, size=11.0, bold=True, color=dt.INK_PRIMARY)
    f_hdr_plan = Font(name=font_family, size=11.0, bold=True, color=dt.SAFE_TEXT)
    f_hdr_res = Font(name=font_family, size=11.0, bold=True, color=dt.OPTIMAL_TEXT)
    f_sec = Font(name=font_family, size=12.0, bold=True, color=dt.INK_PRIMARY)

    f_body = Font(name=font_family, size=11.0, bold=False, color=dt.TEXT_BODY)
    f_bold = Font(name=font_family, size=11.0, bold=True, color=dt.TEXT_BODY)
    f_weight = Font(name=font_family, size=11.0, bold=True, color=dt.INK_PRIMARY)
    f_total = Font(name=font_family, size=12.0, bold=True, color=dt.CRITICAL_TEXT)
    f_note = Font(name=font_family, size=10.5, italic=True, color=dt.TEXT_MUTED)

    fill_white = PatternFill("solid", fgColor=dt.WHITE)
    fill_hdr_main = PatternFill("solid", fgColor=dt.SURFACE_HEADER_TINT)
    fill_hdr_plan = PatternFill("solid", fgColor=dt.SAFE_BG)
    fill_hdr_res = PatternFill("solid", fgColor=dt.OPTIMAL_BG)
    fill_sec = PatternFill("solid", fgColor=dt.SURFACE_SECTION_BG)
    fill_total = PatternFill("solid", fgColor=dt.SURFACE_SUMMARY)

    s_hair = Side(style="thin", color=dt.BORDER_GRID)
    s_med = Side(style="medium", color=dt.INK_PRIMARY)
    s_bronze = Side(style="medium", color=dt.ACCENT_BRONZE)
    b_data = Border(left=s_hair, right=s_hair, top=s_hair, bottom=s_hair)
    b_hdr = Border(left=s_hair, right=s_hair, top=s_med, bottom=s_med)
    b_sec = Border(left=s_hair, right=s_hair, top=s_hair, bottom=s_bronze)

    for ws in wb.worksheets:
        ws.conditional_formatting._cf_rules.clear()
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                cell = ws.cell(r, c)
                val_str = str(cell.value or "").strip()
                fg = str(getattr(cell.fill.start_color, "rgb", "") or "")[-6:].upper()

                if r == 1:
                    cell.font = f_title
                    cell.fill = fill_white
                elif r in (2, 3, 4) and ws.cell(5, 1).value == "STT":
                    cell.font = f_sub
                    cell.fill = fill_white
                elif fg in ("F8CBAD", "1E3246"):
                    if r in (5, 6, 3, 4):
                        cell.font = f_hdr_main
                        cell.fill = fill_hdr_main
                        cell.border = b_hdr
                    else:
                        cell.font = f_sec
                        cell.fill = fill_sec
                        cell.border = b_sec
                elif fg in ("A9D08E", "A9D18E", "EBF3ED"):
                    cell.font = f_hdr_plan
                    cell.fill = fill_hdr_plan
                    cell.border = b_hdr
                elif fg in ("B4C6E7", "B4C7E7", "EDF3F5"):
                    cell.font = f_hdr_res
                    cell.fill = fill_hdr_res
                    cell.border = b_hdr
                elif fg in ("FFD966", "E6E2DA"):
                    cell.font = f_sec
                    cell.fill = fill_sec
                    cell.border = b_sec
                else:
                    if "TỶ LỆ ĐẠT" in val_str.upper() or str(ws.cell(r, 2).value or "").strip().upper() == "TỶ LỆ ĐẠT":
                        cell.font = f_total
                        cell.fill = fill_total
                        cell.border = b_sec
                    elif "GHI CHÚ" in val_str.upper() and r >= 45:
                        cell.font = f_note
                    elif cell.value is not None or cell.border.left.style:
                        is_b = bool(cell.font and cell.font.bold)
                        cell.font = f_weight if (c == 4 and isinstance(cell.value, (int, float))) else (f_bold if is_b else f_body)
                        if fg not in ("000000", ""):
                            cell.fill = fill_white
                        cell.border = b_data

        ws.freeze_panes = "A7" if ws.cell(5, 1).value == "STT" else "A5"
        ws.print_title_rows = "1:6" if ws.cell(5, 1).value == "STT" else "1:4"

    if wb._fonts:
        wb._fonts[0] = Font(name=font_family, size=11.0, color=dt.TEXT_BODY)

    xvs.sanitize_workbook(wb, zoom=100, reset_top_left=True, reset_gridlines=True, ensure_print_fit=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    _enforce_zero_white_text_and_dark_fill(wb)
    wb.save(out_path)
    ok_xml, issues = xvs.validate_xlsx_file(out_path)
    return {"output_path": out_path, "xml_valid": ok_xml, "issues": issues, "sheets": wb.sheetnames}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python iso_kpi_exporter.py <input.xlsx> [output.xlsx]")
        sys.exit(1)
    in_p = sys.argv[1]
    out_p = sys.argv[2] if len(sys.argv) > 2 else in_p
    res = standardize_iso_kpi_workbook(in_p, out_p)
    print(f"[OK ISO KPI] {res['output_path']} | Sheets={res['sheets']} | XML={res['xml_valid']}")


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
