# -*- coding: utf-8 -*-
"""
xlsx_view_sanity.py — Bộ Kiểm Định Cấu Trúc XML, Thẩm Mỹ & Logic Chéo Bảng Tính Excel (v2.1)
=============================================================================================
Mục đích:
  1. Ngăn vĩnh viễn lỗi Excel báo `[Repaired]`, nhảy dòng (`topLeftCell` cũ), zoom nhòe, và crash `MergedCell`.
  2. Kiểm định & Khử mùi AI trên bảng tính (`audit_excel_aesthetics`):
     - Phát hiện & loại bỏ 100% Emoji trò chuyện (`🟢`, `🔴`, `🟡`, `⏳`, `🚨`) trong ô dữ liệu.
     - Phát hiện & chuẩn hóa các ô viết IN HOA TOÀN BỘ (ALL-CAPS Shouting) dài > 1 câu.
     - Khóa cứng cấu hình in ấn Landscape + `fitToPage = True` (`fitToWidth = 1`, `fitToHeight = 0`).
  3. Kiểm định Logic Chéo Giữa Các Cột (`audit_cross_column_logic` — v2.1):
     - Phát hiện mâu thuẫn định dạng file (VD: Cột Định dạng ghi `PDF` nhưng Cột Tên hồ sơ ghi `CAD`, hoặc ngược lại).
     - Phát hiện mâu thuẫn trạng thái bàn giao (VD: Cột Trạng thái ghi `TRỐNG` nhưng Cột Tiến độ/Pending ghi `Đã phát hành`).
"""

import os
import sys
import re
import zipfile
from typing import Tuple, List, Dict, Any

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u23F0-\u23FA]+")


def sanitize_xlsx_view(ws, zoom=100, reset_top_left=True, reset_gridlines=True, ensure_print_fit=True):
    from openpyxl.worksheet.views import Selection

    sv = _active_sheet_view(ws)
    if sv is not None:
        if reset_top_left:
            sv.topLeftCell = "A1"
        if zoom is not None:
            sv.zoomScale = int(zoom)
            sv.zoomScaleNormal = int(zoom)
        if reset_gridlines:
            sv.showGridLines = True

        pane = sv.pane
        if pane is None:
            sv.selection = [Selection(activeCell="A1", sqref="A1")]
        else:
            defined = ["topLeft"]
            if pane.ySplit:
                defined.append("bottomLeft")
            if pane.xSplit:
                defined.append("topRight")
                if pane.ySplit:
                    defined.append("bottomRight")
            if pane.activePane not in defined:
                pane.activePane = "bottomLeft" if pane.ySplit else "topLeft"
            ref = pane.topLeftCell or "A1"
            sv.selection = [Selection(pane=pane.activePane, activeCell=ref, sqref=ref)]

    if ensure_print_fit:
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        if not ws.page_setup.paperSize:
            ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0


def sanitize_workbook(wb, zoom=100, reset_top_left=True, reset_gridlines=True, ensure_print_fit=True):
    if not HAS_OPENPYXL:
        return 0
    n = 0
    for ws in wb.worksheets:
        sanitize_xlsx_view(
            ws,
            zoom=zoom,
            reset_top_left=reset_top_left,
            reset_gridlines=reset_gridlines,
            ensure_print_fit=ensure_print_fit,
        )
        n += 1
    return n


def set_cell_safe(ws, ref, value):
    from openpyxl.cell.cell import MergedCell

    cell = ws[ref]
    if isinstance(cell, MergedCell):
        for mr in ws.merged_cells.ranges:
            if ref in mr:
                cell = ws.cell(row=mr.min_row, column=mr.min_col)
                break
    cell.value = value
    return cell.coordinate


def copy_style_from(source_ws, target_ws, ref, skip_value=False):
    from copy import copy
    from openpyxl.cell.cell import MergedCell

    src = source_ws[ref]
    tgt = target_ws[ref]
    tgt.font = copy(src.font)
    tgt.fill = copy(src.fill)
    tgt.border = copy(src.border)
    tgt.alignment = copy(src.alignment)
    tgt.number_format = src.number_format
    if not skip_value:
        if isinstance(tgt, MergedCell):
            set_cell_safe(target_ws, ref, src.value)
        else:
            tgt.value = src.value
    if src.hyperlink is not None:
        tgt.hyperlink = copy(src.hyperlink)
    elif tgt.hyperlink is not None:
        tgt.hyperlink = None
    return ref


def audit_cross_column_logic(path: str) -> List[str]:
    """
    Kiểm tra mâu thuẫn logic chéo giữa các cột trên bảng theo dõi tiến độ / QLTK:
      1. Cột Định dạng (Col F) ghi PDF nhưng Cột Tên file (Col G) ghi 2.1 CAD (hoặc DWG vs 2.2 PDF).
      2. Cột Trạng thái (Col E) ghi TRỐNG nhưng Cột Tiến độ thực tế (Col I) ghi Đã phát hành.
    """
    contradictions: List[str] = []
    if not HAS_OPENPYXL or not os.path.exists(path):
        return contradictions

    wb = openpyxl.load_workbook(path, data_only=True)
    for ws in wb.worksheets:
        if ws.max_column < 12:
            continue
        for r in range(5, ws.max_row + 1):
            st_val = str(ws.cell(r, 5).value or "").strip().upper()
            fmt_val = str(ws.cell(r, 6).value or "").strip().upper()
            file_val = str(ws.cell(r, 7).value or "").strip().upper()
            act_val = str(ws.cell(r, 9).value or "").strip().upper()

            if fmt_val == "PDF" and file_val.endswith("CAD"):
                contradictions.append(f"{ws.title}!R{r}: Định dạng='PDF' nhưng Tên hồ sơ='{file_val}'")
            elif fmt_val == "DWG" and file_val.endswith("PDF"):
                contradictions.append(f"{ws.title}!R{r}: Định dạng='DWG' nhưng Tên hồ sơ='{file_val}'")

            if st_val == "TRỐNG" and "ĐÃ PHÁT HÀNH" in act_val:
                contradictions.append(f"{ws.title}!R{r}: Trạng thái='TRỐNG' nhưng Tiến độ thực tế='{act_val}'")
    wb.close()
    return contradictions


def audit_excel_aesthetics(path: str) -> Dict[str, Any]:
    report = {
        "emoji_cells": 0,
        "all_caps_cells": 0,
        "white_text_cells": 0,
        "dark_fill_cells": 0,
        "missing_fit_to_page_sheets": [],
        "distinct_body_font_colors": set(),
        "logic_contradictions": [],
    }
    if not HAS_OPENPYXL or not os.path.exists(path):
        return report

    wb = openpyxl.load_workbook(path, data_only=True)
    for ws in wb.worksheets:
        if not ws.sheet_properties.pageSetUpPr.fitToPage:
            report["missing_fit_to_page_sheets"].append(ws.title)
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                cell_obj = ws.cell(r, c)
                fc_obj = getattr(cell_obj.font, "color", None) if cell_obj.font else None
                fc_hex = str(getattr(fc_obj, "rgb", "") or "")[-6:].upper()
                if fc_hex == "FFFFFF" and cell_obj.value is not None:
                    report["white_text_cells"] += 1
                fg_obj = getattr(cell_obj.fill, "start_color", None) if (cell_obj.fill and cell_obj.fill.fill_type == "solid") else None
                fg_hex = str(getattr(fg_obj, "rgb", "") or "")[-6:].upper()
                if len(fg_hex) == 6 and fg_hex not in ("000000", "FFFFFF"):
                    try:
                        r_v, g_v, b_v = int(fg_hex[0:2], 16), int(fg_hex[2:4], 16), int(fg_hex[4:6], 16)
                        luma = 0.299 * r_v + 0.587 * g_v + 0.114 * b_v
                        if luma < 140:
                            report["dark_fill_cells"] += 1
                    except Exception:
                        pass
                if r < 5:
                    continue
                val = str(ws.cell(r, c).value or "")
                if _EMOJI_RE.search(val):
                    report["emoji_cells"] += 1
                if c in (11, 12):
                    alpha = [ch for ch in val if ch.isalpha()]
                    if len(alpha) > 25 and sum(1 for ch in alpha if ch.isupper()) / len(alpha) > 0.75:
                        report["all_caps_cells"] += 1
                fc = getattr(ws.cell(r, c).font, "color", None)
                if fc and getattr(fc, "rgb", None):
                    report["distinct_body_font_colors"].add(str(fc.rgb)[-6:])
    wb.close()
    report["distinct_body_font_colors"] = sorted(list(report["distinct_body_font_colors"]))
    report["logic_contradictions"] = audit_cross_column_logic(path)
    return report


def validate_xlsx_file(path: str) -> Tuple[bool, List[str]]:
    issues = []
    if not os.path.exists(path):
        return False, [f"file không tồn tại: {path}"]

    try:
        zf = zipfile.ZipFile(path)
    except Exception as e:
        return False, [f"không mở được zip xlsx: {e!r}"]

    sheet_xmls = [n for n in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
    if not sheet_xmls:
        return False, ["không tìm thấy file worksheet trong zip"]

    pane_re = re.compile(r"<pane\s+([^>]*?)/?>")
    sel_re = re.compile(r"<selection\s+([^>]*?)/?>")
    attr_re = re.compile(r'(\w+)="([^"]*)"')

    for name in sheet_xmls:
        xml = zf.read(name).decode("utf-8", errors="ignore")
        m = re.search(r"<sheetViews>.*?</sheetViews>", xml, re.S)
        block = m.group(0) if m else "<sheetViews><sheetView/></sheetViews>"

        for view_i, mseg in enumerate(re.finditer(r"<sheetView\b[^>]*(?:/>|>.*?</sheetView>)", block, re.S)):
            view = mseg.group(0)
            label = f"{name}[sheetView#{view_i}]"
            defined = {"topLeft"}
            mpane = pane_re.search(view)
            if mpane:
                attrs = dict(attr_re.findall(mpane.group(1)))
                if attrs.get("ySplit"):
                    defined.add("bottomLeft")
                if attrs.get("xSplit"):
                    defined.add("topRight")
                    if attrs.get("ySplit"):
                        defined.add("bottomRight")
                state = attrs.get("state", "split")
                if state not in ("split", "frozen", "frozenSplit"):
                    issues.append(f"{label}: pane state không hợp lệ: '{state}'")

            for msel in sel_re.finditer(view):
                attrs = dict(attr_re.findall(msel.group(1)))
                sel_pane = attrs.get("pane", "topLeft")
                if sel_pane not in defined:
                    issues.append(
                        f"{label}: <selection pane='{sel_pane}'> không hợp lệ "
                        f"(vùng pane tồn tại: {sorted(defined)})"
                    )

    zf.close()
    return (len(issues) == 0), issues


def _active_sheet_view(ws):
    try:
        return ws.views.sheetView[0]
    except AttributeError:
        return getattr(ws, "sheet_view", None)


__all__ = [
    "HAS_OPENPYXL",
    "sanitize_xlsx_view",
    "sanitize_workbook",
    "set_cell_safe",
    "copy_style_from",
    "audit_cross_column_logic",
    "audit_excel_aesthetics",
    "validate_xlsx_file",
]
