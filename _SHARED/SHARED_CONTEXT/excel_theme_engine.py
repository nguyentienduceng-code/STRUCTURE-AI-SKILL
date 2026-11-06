#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
excel_theme_engine.py — Engine Dựng Bảng Tính Excel Chuẩn Tư Vấn & PMO Hạng Nhất (v1.0)
=======================================================================================
Đặt tại: `.agents/_SHARED/SHARED_CONTEXT/excel_theme_engine.py`
Mục đích:
  Cung cấp lớp `EnterpriseExcelBuilder` thống nhất cho toàn bộ 13 Skills trong hệ thống `.agents`
  (Project_Manager, Design_Evaluation, Structural_Design_Engineer, Cost_Estimator, SKILL_GEOTECH,
  SKILL_TEMPWORKS, SKILL_BIM_COORDINATION), đảm bảo 100% bảng tính `.xlsx` xuất ra:
    1. Tuân thủ tuyệt đối Hệ màu Khoáng vật Tự nhiên (`design_tokens.py` v4.2).
    2. Sử dụng phông không chân kỹ thuật `Arial` sắc nét, mực đơn sắc `#1C1E21` cho toàn bộ cột nội dung.
    3. Tích hợp sẵn Dải Thẻ KPI Công thức Sống (`build_live_kpi_strip`), Thanh Tiêu đề (`apply_table_header`),
       Dải Phân khu (`apply_section_banner`), Nhãn Trạng thái Khoáng vật (`apply_status_pill`),
       Danh mục chọn (`attach_status_dropdown`) và Khung Ký Duyệt Pháp Lý ISO 4 Cấp (`build_iso_signature_footer`).
    4. Tự động chạy `xlsx_view_sanity.sanitize_workbook()` khóa cấu hình in Landscape `fitToPage = True`
       và ngăn chặn vĩnh viễn lỗi Excel báo `[Repaired]`.
"""

import os
import sys
from typing import List, Tuple, Dict, Any, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.datavalidation import DataValidation

_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
for _cand in [
    _CURR_DIR,
    os.path.abspath(os.path.join(_CURR_DIR, "..", "..", "tools")),
]:
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

import design_tokens as dt
import xlsx_view_sanity as xvs


class EnterpriseExcelBuilder:
    """Bộ khung dựng bảng tính Excel chuẩn PMO & Tư vấn Kỹ thuật (Zero-AI Styling)."""

    def __init__(self, font_family: str = dt.FONT_EXCEL_GRID):
        self.font_family = font_family
        # Fonts
        self.f_title = Font(name=font_family, size=16.0, bold=True, color=dt.INK_PRIMARY)
        self.f_subtitle = Font(name=font_family, size=11.0, bold=False, color=dt.INK_TERTIARY)
        self.f_meta = Font(name=font_family, size=10.5, italic=True, color=dt.INK_PRIMARY)
        self.f_col_hdr = Font(name=font_family, size=11.5, bold=True, color=dt.INK_PRIMARY)
        self.f_sec_hdr = Font(name=font_family, size=12.0, bold=True, color=dt.INK_PRIMARY)

        self.f_kpi_lbl = Font(name=font_family, size=10.5, bold=True, color=dt.INK_TERTIARY)
        self.f_kpi_val = Font(name=font_family, size=14.0, bold=True, color=dt.INK_PRIMARY)
        self.f_kpi_pass = Font(name=font_family, size=14.0, bold=True, color=dt.SAFE_TEXT)
        self.f_kpi_warn = Font(name=font_family, size=14.0, bold=True, color=dt.MAJOR_TEXT)
        self.f_kpi_crit = Font(name=font_family, size=14.0, bold=True, color=dt.CRITICAL_TEXT)

        self.f_body_reg = Font(name=font_family, size=11.0, bold=False, color=dt.TEXT_BODY)
        self.f_body_bold = Font(name=font_family, size=11.0, bold=True, color=dt.TEXT_BODY)
        self.f_subrow_repeat = Font(name=font_family, size=10.5, bold=False, color="7A828A")
        self.f_muted = Font(name=font_family, size=10.5, italic=True, color=dt.TEXT_MUTED)
        self.f_link = Font(name=font_family, size=10.5, bold=False, color=dt.INK_SECONDARY, underline="single")

        self.f_status_pass = Font(name=font_family, size=10.5, bold=True, color=dt.SAFE_TEXT)
        self.f_status_warn = Font(name=font_family, size=10.5, bold=True, color=dt.MAJOR_TEXT)
        self.f_status_crit = Font(name=font_family, size=11.0, bold=True, color=dt.CRITICAL_TEXT)
        self.f_status_empty = Font(name=font_family, size=10.5, bold=False, color=dt.EMPTY_TEXT)

        # Fills
        self.fill_white = PatternFill("solid", fgColor=dt.WHITE)
        self.fill_meta = PatternFill("solid", fgColor=dt.SURFACE_META_BANNER)
        self.fill_kpi_bg = PatternFill("solid", fgColor="F8F7F4")
        self.fill_col_hdr = PatternFill("solid", fgColor=dt.SURFACE_HEADER_TINT)
        self.fill_sec_hdr = PatternFill("solid", fgColor=dt.SURFACE_SECTION_BG)
        self.fill_summary = PatternFill("solid", fgColor=dt.SURFACE_SUMMARY)

        self.fill_status_pass = PatternFill("solid", fgColor=dt.SAFE_BG)
        self.fill_status_warn = PatternFill("solid", fgColor=dt.MAJOR_BG)
        self.fill_status_crit = PatternFill("solid", fgColor=dt.CRITICAL_BG)
        self.fill_status_empty = PatternFill("solid", fgColor=dt.EMPTY_BG)

        # Borders
        self.s_hair = Side(style="thin", color=dt.BORDER_GRID)
        self.s_dotted = Side(style="dotted", color=dt.BORDER_GRID)
        self.s_primary_med = Side(style="medium", color=dt.INK_PRIMARY)
        self.s_primary_double = Side(style="double", color=dt.INK_PRIMARY)
        self.s_bronze_med = Side(style="medium", color=dt.ACCENT_BRONZE)
        self.s_bronze_thin = Side(style="thin", color=dt.ACCENT_BRONZE)

        self.b_data = Border(left=self.s_hair, right=self.s_hair, top=self.s_hair, bottom=self.s_hair)
        self.b_col_hdr = Border(left=self.s_hair, right=self.s_hair, top=self.s_primary_med, bottom=self.s_primary_double)
        self.b_sec_hdr = Border(left=self.s_hair, right=self.s_hair, top=self.s_bronze_thin, bottom=self.s_bronze_med)
        self.b_kpi_top = Border(left=self.s_hair, right=self.s_hair, top=self.s_bronze_thin)
        self.b_kpi_bot = Border(left=self.s_hair, right=self.s_hair, bottom=self.s_bronze_med)
        self.b_total = Border(left=self.s_hair, right=self.s_hair, top=self.s_hair, bottom=self.s_primary_double)

        # Alignments
        self.al_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.al_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.al_right = Alignment(horizontal="right", vertical="center", wrap_text=True)
        self.al_sec = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)

    @staticmethod
    def style_merged_range(ws, cell_range: str, font=None, fill=None, alignment=None, border=None):
        min_col, min_row, max_col, max_row = range_boundaries(cell_range)
        for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
            for cell in row:
                if font:
                    cell.font = font
                if fill:
                    cell.fill = fill
                if alignment:
                    cell.alignment = alignment
                if border:
                    cell.border = border

    def build_live_kpi_strip(
        self,
        ws,
        row_top: int,
        kpi_cards: List[Tuple[str, str, str, str, str]],
    ) -> None:
        """
        Dựng dải thẻ KPI công thức sống trên 2 dòng (`row_top` và `row_top + 1`).
        Mỗi phần tử trong `kpi_cards` là:
          (col_start_letter, col_end_letter, label_text, formula_str, semantic_tone)
        trong đó `semantic_tone` thuộc {"primary", "pass", "warn", "crit"}.
        """
        r_lbl = row_top
        r_val = row_top + 1
        ws.row_dimensions[r_lbl].height = 17.0
        ws.row_dimensions[r_val].height = 24.0

        for c_start, c_end, lbl, formula_str, tone in kpi_cards:
            rng_lbl = f"{c_start}{r_lbl}:{c_end}{r_lbl}"
            rng_val = f"{c_start}{r_val}:{c_end}{r_val}"
            if c_start != c_end:
                ws.merge_cells(rng_lbl)
                ws.merge_cells(rng_val)

            ws[f"{c_start}{r_lbl}"] = lbl
            ws[f"{c_start}{r_val}"] = formula_str

            fill_card = self.fill_kpi_bg
            val_font = self.f_kpi_val
            if tone == "pass":
                fill_card = self.fill_status_pass
                val_font = self.f_kpi_pass
            elif tone == "warn":
                fill_card = self.fill_status_warn
                val_font = self.f_kpi_warn
            elif tone == "crit":
                fill_card = self.fill_status_crit
                val_font = self.f_kpi_crit

            self.style_merged_range(ws, rng_lbl, font=self.f_kpi_lbl, fill=fill_card, alignment=self.al_center, border=self.b_kpi_top)
            self.style_merged_range(ws, rng_val, font=val_font, fill=fill_card, alignment=self.al_center, border=self.b_kpi_bot)
            ws[f"{c_start}{r_val}"].number_format = "#,##0"

    def apply_status_pill(self, cell, status_text: str) -> None:
        cell.alignment = self.al_center
        up_v = (status_text or "").strip().upper()
        if "ĐÃ CÓ" in up_v or "ĐÃ DUYỆT" in up_v or "ĐÃ PHÁT HÀNH" in up_v or "HOÀN THÀNH" in up_v:
            cell.font = self.f_status_pass
            cell.fill = self.fill_status_pass
        elif "LOADING" in up_v or "ĐANG" in up_v or "CHỜ" in up_v:
            cell.font = self.f_status_warn
            cell.fill = self.fill_status_warn
        elif "QUÁ HẠN" in up_v or "TRỄ" in up_v or "KHÔNG ĐẠT" in up_v:
            cell.font = self.f_status_crit
            cell.fill = self.fill_status_crit
        else:
            cell.font = self.f_status_empty
            cell.fill = self.fill_status_empty

    @staticmethod
    def attach_status_dropdown(ws, col_letter: str, min_row: int, max_row: int, options: List[str]) -> None:
        formula_list = '"' + ",".join(options) + '"'
        dv = DataValidation(type="list", formula1=formula_list, allow_blank=True)
        dv.promptTitle = "Chọn Trạng Thái Chuẩn QLTK"
        dv.prompt = "Chọn trạng thái chuẩn từ danh mục để tự động cập nhật KPI."
        ws.add_data_validation(dv)
        dv.add(f"{col_letter}{min_row}:{col_letter}{max_row}")

    def build_iso_signature_footer(
        self,
        ws,
        start_row: int,
        sig_blocks: List[Tuple[str, str, str, str]],
    ) -> int:
        """
        Dựng khung trình ký & phê duyệt chuẩn ISO ở cuối bảng tính.
        Mỗi phần tử trong `sig_blocks` là: (col_start, col_end, role_title, subtitle_note).
        Trả về dòng cuối cùng của khung ký.
        """
        r_hdr = start_row
        r_sub = start_row + 1
        r_space = start_row + 2
        ws.row_dimensions[r_hdr].height = 22.0
        ws.row_dimensions[r_sub].height = 18.0
        ws.row_dimensions[r_space].height = 52.0

        for c_start, c_end, role_title, sub_note in sig_blocks:
            rng_h = f"{c_start}{r_hdr}:{c_end}{r_hdr}"
            rng_s = f"{c_start}{r_sub}:{c_end}{r_sub}"
            rng_p = f"{c_start}{r_space}:{c_end}{r_space}"
            if c_start != c_end:
                ws.merge_cells(rng_h)
                ws.merge_cells(rng_s)
                ws.merge_cells(rng_p)

            ws[f"{c_start}{r_hdr}"] = role_title
            ws[f"{c_start}{r_sub}"] = sub_note
            ws[f"{c_start}{r_space}"] = ""

            self.style_merged_range(ws, rng_h, font=self.f_sec_hdr, fill=self.fill_sec_hdr, alignment=self.al_center, border=self.b_sec_hdr)
            self.style_merged_range(ws, rng_s, font=self.f_muted, fill=self.fill_white, alignment=self.al_center, border=self.b_data)
            self.style_merged_range(ws, rng_p, font=self.f_body_reg, fill=self.fill_white, alignment=self.al_center, border=self.b_data)

        return r_space

    def finalize_and_save(
        self,
        wb,
        output_path: str,
        freeze_pane: str = "A7",
        repeat_rows: str = "1:6",
    ) -> str:
        if wb._fonts:
            wb._fonts[0] = Font(name=self.font_family, size=11.0, color=dt.TEXT_BODY)
        for ws in wb.worksheets:
            if freeze_pane:
                ws.freeze_panes = freeze_pane
            if repeat_rows:
                ws.print_title_rows = repeat_rows
        xvs.sanitize_workbook(wb, zoom=100, reset_top_left=True, reset_gridlines=True, ensure_print_fit=True)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb.save(output_path)
        return output_path
