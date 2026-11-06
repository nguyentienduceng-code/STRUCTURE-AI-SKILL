#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx_report.py — Bộ Xuất Bản Bảng Tính Excel Kỹ Thuật Cấp Tư Vấn Hạng Nhất (v5.0 Tier-1 Consultancy Edition)
=============================================================================================================
Nâng cấp toàn diện v5.0 (2026-11-02):
  1. Multi-Sheet Master Workbook thật sự (`--type combined`):
     Khắc phục triệt để lỗi ghi đè file cũ; tự động đóng gói liên hoàn tới 6 Sheets chuẩn ISO 19650:
       - `00_KIEM_SOAT_HO_SO` : Bảng Kiểm soát Chất lượng Hồ sơ, Phiên bản (Rev 00), Chữ ký 3 cấp & Danh mục Tiêu chuẩn.
       - `01_THONG_SO_DAU_VAO`: Bảng Thông số Hình học, Vật liệu & Nội lực đầu vào có đơn vị chuẩn hóa.
       - `02_BANG_TINH_CHI_TIET`: Phụ lục Tính toán Step-by-Step (chuẩn hóa mọi schema hoa/thường: Step/step, Substitution/Values, eta/Utilization).
       - `03_TONG_HOP_ETA`    : Bảng Kiểm soát Hệ số Sử dụng η = D/C, Dự trữ An toàn (%) bằng công thức sống `=1-C{row}` & đánh dấu Governing Check.
       - `04_BOQ_DU_TOAN`     : Bảng Tiên lượng & Dự toán sử dụng 100% công thức sống Excel (`=E{r}*F{r}`, `=SUM(...)`, Chi phí dự phòng, VAT 10%).
       - `05_SO_SANH_PA`      : Ma trận So sánh Phương án Thiết kế (Value Engineering) kèm Biểu đồ cột nhúng trực tiếp.
  2. Chuẩn Trình bày Ấn phẩm Kỹ thuật Tự nhiên (Natural Mineral Palette v4.0):
     - Phông chữ `Times New Roman` đồng bộ toàn bộ các ô, đường kẻ lưới mảnh `#D0CEC7`, viền khung `#1E3246`.
     - Tự động khóa tiêu đề (`freeze_panes`), căn chỉnh khổ giấy A4 (`fitToWidth=1`) và tự động tính chiều cao dòng (`row_dimensions.height`).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ════════════════════════════════════════════════════════════════════════════
# HỆ MÀU KHOÁNG CHẤT & MỰC IN KỸ THUẬT TỰ NHIÊN (DESIGN SYSTEM v4.0 / v5.0)
# ════════════════════════════════════════════════════════════════════════════
PRIMARY       = "1E3246"  # Deep Prussian Slate (Header chính & Khung bìa)
ACCENT        = "2E4A62"  # Muted Steel Blue (Tiêu đề phụ & Nhóm mục)
BRONZE_RULE   = "A67C37"  # Muted Bronze Ochre (Đường kẻ phân cách)
TEXT_DARK     = "1C1E21"  # Charcoal Print Ink (Chữ thân bảng)
TEXT_MED      = "5A626A"  # Warm Slate Grey (Chú thích)
ROW_ALT       = "F8F7F4"  # Natural Ivory Tint (Dòng chẵn tiệp màu giấy)
LABEL_BG      = "F2EFE9"  # Warm Alabaster Paper (Cột nhãn trái & Dòng tổng cộng)

CRITICAL_TEXT = "8C261E"
CRITICAL_BG   = "F9EBE8"
MAJOR_TEXT    = "8F5314"
MAJOR_BG      = "FBF3E4"
OPTIMAL_TEXT  = "1F4E5B"
OPTIMAL_BG    = "EDF3F5"
SAFE_TEXT     = "1E5631"
SAFE_BG       = "EBF3ED"

THIN_GRID     = Side(border_style="thin", color="D0CEC7")
MEDIUM_OUTER  = Side(border_style="medium", color=PRIMARY)
DOUBLE_BOTTOM = Side(border_style="double", color=PRIMARY)

BORDER_ALL = Border(left=THIN_GRID, right=THIN_GRID, top=THIN_GRID, bottom=THIN_GRID)
BORDER_HEADER = Border(left=THIN_GRID, right=THIN_GRID, top=MEDIUM_OUTER, bottom=MEDIUM_OUTER)
BORDER_TOTAL = Border(left=THIN_GRID, right=THIN_GRID, top=THIN_GRID, bottom=DOUBLE_BOTTOM)

HEADER_FILL = PatternFill(start_color=PRIMARY, end_color=PRIMARY, fill_type="solid")
SUBHEADER_FILL = PatternFill(start_color=ACCENT, end_color=ACCENT, fill_type="solid")
ALT_FILL = PatternFill(start_color=ROW_ALT, end_color=ROW_ALT, fill_type="solid")
LABEL_FILL = PatternFill(start_color=LABEL_BG, end_color=LABEL_BG, fill_type="solid")

FONT_FAMILY = "Times New Roman"
HEADER_FONT = Font(name=FONT_FAMILY, bold=True, color="1E3246", size=11.5)
TITLE_FONT = Font(name=FONT_FAMILY, bold=True, color=PRIMARY, size=16.0)
SUBTITLE_FONT = Font(name=FONT_FAMILY, bold=True, color=ACCENT, size=11)
BODY_FONT = Font(name=FONT_FAMILY, bold=False, color=TEXT_DARK, size=11.0)
BODY_BOLD = Font(name=FONT_FAMILY, bold=True, color=TEXT_DARK, size=11.0)
LABEL_FONT = Font(name=FONT_FAMILY, bold=True, color=PRIMARY, size=11.0)
MUTED_ITALIC = Font(name=FONT_FAMILY, italic=True, color=TEXT_MED, size=10.5)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center", wrap_text=True)


def _apply_print_setup(ws, landscape: bool = True, freeze_cell: Optional[str] = "A5"):
    """Cấu hình chuẩn trang in A4 chuyên nghiệp cho từng Sheet."""
    ws.views.sheetView[0].showGridLines = True
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE if landscape else ws.ORIENTATION_PORTRAIT
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    if freeze_cell:
        ws.freeze_panes = freeze_cell


def _styled_header_cell(cell):
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = CENTER
    cell.border = BORDER_HEADER


def _styled_title_cell(cell):
    cell.font = TITLE_FONT
    cell.alignment = LEFT


def _styled_data_cell(cell, alt: bool = False, align=LEFT, bold: bool = False):
    cell.font = BODY_BOLD if bold else BODY_FONT
    cell.border = BORDER_ALL
    cell.alignment = align
    if alt:
        cell.fill = ALT_FILL


def _style_status_cell(cell, status_or_eta: Any):
    """Tô màu gốc khoáng tự nhiên cho ô trạng thái hoặc chỉ số η."""
    val_str = str(status_or_eta).upper()
    if isinstance(status_or_eta, (int, float)):
        eta = float(status_or_eta)
        if eta > 1.0:
            val_str = "RED"
        elif eta > 0.90:
            val_str = "ORANGE"
        elif eta > 0.70:
            val_str = "OPTIMAL"
        else:
            val_str = "GREEN"

    if any(k in val_str for k in ("RED", "FAIL", "KHÔNG ĐẠT", "CRITICAL", "VƯỢT")):
        cell.fill = PatternFill(start_color=CRITICAL_BG, end_color=CRITICAL_BG, fill_type="solid")
        cell.font = Font(name=FONT_FAMILY, bold=True, color=CRITICAL_TEXT, size=11.0)
    elif any(k in val_str for k in ("ORANGE", "WARN", "SÁT NGƯỠNG", "MAJOR", "HIGH")):
        cell.fill = PatternFill(start_color=MAJOR_BG, end_color=MAJOR_BG, fill_type="solid")
        cell.font = Font(name=FONT_FAMILY, bold=True, color=MAJOR_TEXT, size=11.0)
    elif any(k in val_str for k in ("YELLOW", "OPTIMAL", "TỐI ƯU", "MINOR", "MEDIUM")):
        cell.fill = PatternFill(start_color=OPTIMAL_BG, end_color=OPTIMAL_BG, fill_type="solid")
        cell.font = Font(name=FONT_FAMILY, bold=True, color=OPTIMAL_TEXT, size=11.0)
    else:
        cell.fill = PatternFill(start_color=SAFE_BG, end_color=SAFE_BG, fill_type="solid")
        cell.font = Font(name=FONT_FAMILY, bold=True, color=SAFE_TEXT, size=11.0)
    cell.alignment = CENTER
    cell.border = BORDER_ALL


def _estimate_row_height(texts: List[Any], col_widths: List[int], base_height: float = 22.0) -> float:
    max_lines = 1
    for txt, w in zip(texts, col_widths):
        s = str(txt or "")
        if not s:
            continue
        lines = sum(max(1, math.ceil(len(part) / max(w - 2, 10))) for part in s.splitlines())
        if lines > max_lines:
            max_lines = lines
    return min(max(base_height, max_lines * 15.5 + 6.0), 110.0)


# ════════════════════════════════════════════════════════════════════════════
# SHEET 00: BÌA & KIỂM SOÁT HỒ SƠ (ISO 19650 DOCUMENT CONTROL SHEET)
# ════════════════════════════════════════════════════════════════════════════
def populate_doc_control_sheet(ws, handoff: dict):
    _apply_print_setup(ws, landscape=False, freeze_cell=None)
    proj_name = handoff.get("Ten_Du_An") or handoff.get("project_name") or "DỰ ÁN KẾT CẤU CÔNG TRÌNH"
    item_name = handoff.get("Hang_Muc") or handoff.get("element") or "Hạng mục Tính toán & Thẩm tra Kỹ thuật"
    std_name = handoff.get("Standard_Method") or handoff.get("Tieu_Chuan") or "TCVN 5574:2018 / TCVN 5575:2024 / TCVN 2737:2023"
    date_str = handoff.get("Ngay") or datetime.now().strftime("%Y-%m-%d")

    ws["A1"] = "HỒ SƠ BẢNG TÍNH KỸ THUẬT & ĐỐI SOÁT SỐ HỌC (ENGINEERING CALCULATION WORKBOOK)"
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:D1")
    ws.row_dimensions[1].height = 28

    ws["A2"] = f"Chuẩn quản lý chất lượng hồ sơ: ISO 19650 / AGENTS.md v7.1 | Ngày xuất bản: {date_str}"
    ws["A2"].font = MUTED_ITALIC
    ws.merge_cells("A2:D2")

    # Bảng 1: Thông tin Kiểm soát Hồ sơ
    ws["A4"] = "1. THÔNG TIN KIỂM SOÁT HỒ SƠ (DOCUMENT CONTROL METADATA)"
    ws["A4"].font = SUBTITLE_FONT
    ws.merge_cells("A4:D4")

    meta_rows = [
        ("Tên Dự án / Công trình", proj_name),
        ("Hạng mục / Cấu kiện", item_name),
        ("Tiêu chuẩn Thiết kế Áp dụng", std_name),
        ("Mã hiệu Hồ sơ & Phiên bản", f"{handoff.get('Ma_Du_An', 'CALC-PKG')}-REV00"),
        ("Trạng thái Phát hành", "FOR TECHNICAL REVIEW & VERIFICATION (PHỤC VỤ KIỂM TRA & THẨM ĐỊNH)"),
        ("Đơn vị Lập / Kiểm định", handoff.get("Don_Vi", "Ban Kỹ thuật Kết cấu — Hệ thống Kiểm định Tự động .agents v7.1")),
    ]
    for idx, (k, v) in enumerate(meta_rows, start=5):
        c1 = ws.cell(row=idx, column=1, value=k)
        c1.font = LABEL_FONT
        c1.fill = LABEL_FILL
        c1.alignment = LEFT
        c1.border = BORDER_ALL

        c2 = ws.cell(row=idx, column=2, value=str(v))
        c2.font = BODY_FONT
        c2.alignment = LEFT
        ws.merge_cells(start_row=idx, start_column=2, end_row=idx, end_column=4)
        for col in range(2, 5):
            ws.cell(row=idx, column=col).border = BORDER_ALL
        ws.row_dimensions[idx].height = 22

    # Bảng 2: Lịch sử Phiên bản & Chữ ký Kiểm soát 3 Cấp
    ws["A12"] = "2. MA TRẬN TRÁCH NHIỆM & KIỂM SOÁT CHẤT LƯỢNG 3 CẤP (QA/QC SIGN-OFF MATRIX)"
    ws["A12"].font = SUBTITLE_FONT
    ws.merge_cells("A12:D12")

    qa_headers = ["Cấp Kiểm soát", "Họ tên / Chức danh", "Số Chứng chỉ Hành nghề (CCHN)", "Chữ ký & Ngày xác nhận"]
    for col, h in enumerate(qa_headers, 1):
        _styled_header_cell(ws.cell(row=13, column=col, value=h))
    ws.row_dimensions[13].height = 25

    qa_rows = [
        ("1. Người lập bảng tính (Prepared by)", "Trợ lý Kỹ thuật AI (.agents Deterministic Engine)", "Cần Kỹ sư CCHN xác nhận", date_str),
        ("2. Kỹ sư Kiểm tra Độc lập (Checked by)", "[Kỹ sư Kiểm tra Kết cấu]", "[Ghi số CCHN Hạng I/II]", "[Ký & Ghi rõ họ tên]"),
        ("3. Chủ trì Phê duyệt (Approved by)", "[Kỹ sư Chủ trì Thiết kế / Thẩm tra]", "[Ghi số CCHN Hạng I]", "[Ký & Đóng dấu]"),
    ]
    for i, rdata in enumerate(qa_rows, start=14):
        for col, val in enumerate(rdata, 1):
            c = ws.cell(row=i, column=col, value=val)
            _styled_data_cell(c, alt=(i % 2 == 1), align=LEFT if col <= 2 else CENTER, bold=(col == 1))
        ws.row_dimensions[i].height = 26

    ws["A18"] = (
        "Tuyên bố pháp lý (AGENTS.md §8): Bảng tính do hệ thống tính toán tất định lập tự động kèm công thức sống. "
        "Kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra."
    )
    ws["A18"].font = MUTED_ITALIC
    ws.merge_cells("A18:D18")

    widths = [32, 36, 28, 26]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ════════════════════════════════════════════════════════════════════════════
# SHEET 01 & 02: PHỤ LỤC TÍNH TOÁN STEP-BY-STEP & TỔNG HỢP ETA (CALC SHEET)
# ════════════════════════════════════════════════════════════════════════════
def populate_calc_sheet(ws, handoff: dict):
    _apply_print_setup(ws, landscape=True, freeze_cell="A5")
    logs = handoff.get("Calculation_Logs") or handoff.get("calculation_logs") or []
    proj_name = handoff.get("Ten_Du_An") or handoff.get("project_name") or "DỰ ÁN"
    std_name = handoff.get("Standard_Method") or handoff.get("Tieu_Chuan") or "TCVN hiện hành"

    ws["A1"] = f"{proj_name} — BẢNG TÍNH CHI TIẾT TỪNG BƯỚC (STEP-BY-STEP CALCULATION SHEET)"
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:H1")
    ws.row_dimensions[1].height = 26

    ws["A2"] = f"Tiêu chuẩn áp dụng: {std_name} | Mọi bước tính toán được truy xuất trực tiếp từ động cơ tất định Python"
    ws["A2"].font = MUTED_ITALIC
    ws.merge_cells("A2:H2")

    headers = [
        "Bước (Step)",
        "Nội dung Kiểm tra / Sơ đồ",
        "Công thức Lý thuyết (Formula)",
        "Căn cứ Tiêu chuẩn (Citation)",
        "Thế số Thực tế (Substitution)",
        "Kết quả Tính toán (Result)",
        "Hệ số η",
        "Đánh giá Kỹ thuật",
    ]
    for col, h in enumerate(headers, 1):
        _styled_header_cell(ws.cell(row=4, column=col, value=h))
    ws.row_dimensions[4].height = 28

    widths = [11, 28, 30, 26, 32, 22, 11, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    for i, log in enumerate(logs, 1):
        if not isinstance(log, dict):
            continue
        row = 4 + i

        step_val = log.get("Step") or log.get("step") or log.get("Step_Number") or i
        desc_val = (
            log.get("Static_Scheme")
            or log.get("Description")
            or log.get("description")
            or log.get("desc")
            or log.get("Title")
            or f"Bước tính {i}"
        )
        form_val = log.get("Formula") or log.get("formula") or "—"
        sub_val = (
            log.get("Substitution")
            or log.get("substitution")
            or log.get("Values")
            or log.get("values")
            or "—"
        )
        res_val = log.get("Result") if log.get("Result") is not None else log.get("result", log.get("value", "—"))

        citation = log.get("Citation") or log.get("citation") or {}
        if isinstance(citation, dict):
            tc = citation.get("Ma_TC") or citation.get("Standard") or citation.get("Tieu_chuan") or ""
            dm = citation.get("Dieu_Muc") or citation.get("Clause") or citation.get("Table") or ""
            pg = citation.get("Trang") or citation.get("Page") or ""
            citation_str = " — ".join(p for p in [tc, dm, f"Tr.{pg}" if pg else ""] if p) or std_name
        else:
            citation_str = str(citation) if citation else std_name

        util = log.get("Utilization") if log.get("Utilization") is not None else log.get("eta")
        rating = log.get("Rating") or log.get("status")
        if not rating:
            if isinstance(util, (int, float)):
                rating = "[KHÔNG ĐẠT]" if util > 1.0 else ("[SÁT NGƯỠNG]" if util > 0.90 else ("[ĐẠT — TỐI ƯU]" if util > 0.70 else "[ĐẠT — DƯ TẢI]"))
            else:
                rating = "[ĐÃ XÁC ĐỊNH]"

        row_values = [
            step_val,
            desc_val,
            form_val,
            citation_str,
            str(sub_val),
            res_val,
            float(util) if isinstance(util, (int, float)) else "—",
            rating,
        ]
        for col_idx, val in enumerate(row_values, 1):
            c = ws.cell(row=row, column=col_idx, value=val)
            align = CENTER if col_idx in (1, 7, 8) else LEFT
            _styled_data_cell(c, alt=(i % 2 == 0), align=align, bold=(col_idx in (1, 6)))
            if col_idx == 7 and isinstance(val, float):
                c.number_format = "0.000"

        _style_status_cell(ws.cell(row=row, column=8), util if isinstance(util, (int, float)) else rating)
        ws.row_dimensions[row].height = _estimate_row_height(row_values, widths)

    # Nhúng hình vẽ Mặt cắt ngang tham số / Biểu đồ N-M bên phải bảng tính (Cột J) nếu có
    sketch_paths = handoff.get("_embedded_sketches", [])
    if sketch_paths:
        anchor_row = 4
        for sp in sketch_paths:
            if sp and os.path.exists(sp):
                try:
                    img_obj = OpenpyxlImage(sp)
                    img_obj.width = 340
                    img_obj.height = 310
                    ws.add_image(img_obj, f"J{anchor_row}")
                    anchor_row += 17
                except Exception:
                    pass

    # Nhúng hình vẽ Mặt cắt ngang tham số / Biểu đồ N-M bên phải bảng tính (Cột J) nếu có
    sketch_paths = handoff.get("_embedded_sketches", [])
    if sketch_paths:
        anchor_row = 4
        for sp in sketch_paths:
            if sp and os.path.exists(sp):
                try:
                    img_obj = OpenpyxlImage(sp)
                    img_obj.width = 340
                    img_obj.height = 310
                    ws.add_image(img_obj, f"J{anchor_row}")
                    anchor_row += 17
                except Exception:
                    pass


def populate_eta_summary_sheet(ws, handoff: dict):
    """Tạo Sheet Tổng hợp Hệ số Sử dụng η kèm công thức sống tính Dự trữ An toàn (%) và Governing Check."""
    _apply_print_setup(ws, landscape=True, freeze_cell="A5")
    proj_name = handoff.get("Ten_Du_An") or handoff.get("project_name") or "DỰ ÁN"
    ws["A1"] = f"{proj_name} — BẢNG KIỂM SOÁT CHỈ SỐ SỬ DỤNG CHỊU LỰC (UTILIZATION & SAFETY MARGIN MATRIX)"
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:F1")
    ws.row_dimensions[1].height = 26

    ws["A2"] = "Ngưỡng kiểm soát theo AGENTS.md §6: η <= 0.70 (Dư tải / Cơ hội VE) | 0.70 < η <= 0.90 (Tối ưu) | 0.90 < η <= 1.00 (Sát ngưỡng) | η > 1.00 (Không đạt)"
    ws["A2"].font = MUTED_ITALIC
    ws.merge_cells("A2:F2")

    headers = ["STT", "Hạng mục / Trạng thái Giới hạn Kiểm tra", "Hệ số Sử dụng (η = D/C)", "Giới hạn Cho phép [η]", "Dự trữ An toàn (1 - η)", "Kết luận Kiểm định"]
    for col, h in enumerate(headers, 1):
        _styled_header_cell(ws.cell(row=4, column=col, value=h))
    ws.row_dimensions[4].height = 26

    all_res = dict(handoff)
    for k in ("Results", "results", "payload"):
        if isinstance(handoff.get(k), dict):
            all_res.update(handoff[k])

    eta_items = []
    for k, v in all_res.items():
        if (k.startswith("eta_") or k == "overall_eta") and isinstance(v, (int, float)):
            eta_items.append((k, float(v)))

    if not eta_items:
        for log in (handoff.get("Calculation_Logs") or []):
            if isinstance(log, dict) and isinstance(log.get("Utilization"), (int, float)):
                eta_items.append((log.get("Static_Scheme") or f"Step {log.get('Step')}", float(log["Utilization"])))

    for idx, (k, eta_val) in enumerate(eta_items, 1):
        row = 4 + idx
        c1 = ws.cell(row=row, column=1, value=idx)
        c2 = ws.cell(row=row, column=2, value=k)
        c3 = ws.cell(row=row, column=3, value=round(eta_val, 4))
        c4 = ws.cell(row=row, column=4, value=1.00)
        # Công thức sống tính % Dự trữ an toàn = 1.00 - η
        c5 = ws.cell(row=row, column=5, value=f"=D{row}-C{row}")
        eval_txt = "[KHÔNG ĐẠT]" if eta_val > 1.0 else ("[CẢNH BÁO — SÁT NGƯỠNG]" if eta_val > 0.90 else ("[ĐẠT — TỐI ƯU]" if eta_val > 0.70 else "[ĐẠT — DƯ TẢI]"))
        c6 = ws.cell(row=row, column=6, value=eval_txt)

        alt = (idx % 2 == 0)
        _styled_data_cell(c1, alt, CENTER)
        _styled_data_cell(c2, alt, LEFT, bold=(k == "overall_eta"))
        _styled_data_cell(c3, alt, CENTER, bold=True)
        _styled_data_cell(c4, alt, CENTER)
        _styled_data_cell(c5, alt, CENTER, bold=True)
        c3.number_format = "0.000"
        c4.number_format = "0.00"
        c5.number_format = "0.0%"
        _style_status_cell(c6, eta_val)
        ws.row_dimensions[row].height = 22

    if eta_items:
        max_row = 4 + len(eta_items) + 1
        ws.cell(row=max_row, column=2, value="CHỈ SỐ SỬ DỤNG QUYẾT ĐỊNH CỰC ĐẠI (GOVERNING MAX η):").font = LABEL_FONT
        ws.cell(row=max_row, column=2).fill = LABEL_FILL
        ws.cell(row=max_row, column=2).border = BORDER_TOTAL
        c_max = ws.cell(row=max_row, column=3, value=f"=MAX(C5:C{4+len(eta_items)})")
        c_max.font = LABEL_FONT
        c_max.fill = LABEL_FILL
        c_max.alignment = CENTER
        c_max.border = BORDER_TOTAL
        c_max.number_format = "0.000"

    widths = [8, 42, 22, 18, 20, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ════════════════════════════════════════════════════════════════════════════
# SHEET 04: BẢNG KHỐI LƯỢNG & DỰ TOÁN CÔNG THỨC SỐNG (LIVE-FORMULA BOQ)
# ════════════════════════════════════════════════════════════════════════════
def populate_boq_sheet(ws, handoff: dict):
    _apply_print_setup(ws, landscape=False, freeze_cell="A5")
    ws["A1"] = f'{handoff.get("Ten_Du_An", "DỰ ÁN")} — BẢNG TIÊN LƯỢNG KHỐI LƯỢNG & DỰ TOÁN (LIVE-FORMULA BOQ)'
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:G1")
    ws.row_dimensions[1].height = 26

    ws["A2"] = f'Hạng mục: {handoff.get("Hang_Muc", "—")} | Ngày lập: {handoff.get("Ngay", datetime.now().strftime("%Y-%m-%d"))} | Công thức Excel liên kết tự động 100%'
    ws["A2"].font = MUTED_ITALIC
    ws.merge_cells("A2:G2")

    headers = ["STT", "Mã hiệu", "Nội dung Công tác Xây lắp", "Đơn vị", "Khối lượng", "Đơn giá (VNĐ)", "Thành tiền (VNĐ)"]
    for col, h in enumerate(headers, 1):
        _styled_header_cell(ws.cell(row=4, column=col, value=h))
    ws.row_dimensions[4].height = 26

    boq = handoff.get("BOQ", [])
    start_data_row = 5
    for i, item in enumerate(boq, 1):
        row = 4 + i
        qty = float(item.get("quantity", 0) or 0)
        unit_price = float(item.get("unit_price", 0) or 0)

        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=item.get("code", ""))
        ws.cell(row=row, column=3, value=item.get("description", ""))
        ws.cell(row=row, column=4, value=item.get("unit", ""))
        ws.cell(row=row, column=5, value=qty)
        ws.cell(row=row, column=6, value=unit_price)
        # CÔNG THỨC SỐNG EXCEL (=E{row}*F{row}) THAY VÌ SỐ TĨNH
        ws.cell(row=row, column=7, value=f"=E{row}*F{row}")

        alt = (i % 2 == 0)
        for col in range(1, 8):
            align = CENTER if col in (1, 2, 4) else (RIGHT if col >= 5 else LEFT)
            _styled_data_cell(ws.cell(row=row, column=col), alt, align=align, bold=(col == 7))

        ws.cell(row=row, column=5).number_format = "#,##0.00"
        ws.cell(row=row, column=6).number_format = "#,##0"
        ws.cell(row=row, column=7).number_format = "#,##0"
        ws.row_dimensions[row].height = 22

    end_data_row = max(start_data_row, 4 + len(boq))
    total_row = end_data_row + 1

    # Dòng Tổng cộng trước thuế bằng công thức sống =SUM(G5:G...)
    lbl_cell = ws.cell(row=total_row, column=6, value="TỔNG CỘNG (TRƯỚC THUẾ):")
    lbl_cell.font = LABEL_FONT
    lbl_cell.fill = LABEL_FILL
    lbl_cell.alignment = RIGHT
    lbl_cell.border = BORDER_TOTAL

    val_cell = ws.cell(row=total_row, column=7, value=f"=SUM(G{start_data_row}:G{end_data_row})" if boq else 0)
    val_cell.font = LABEL_FONT
    val_cell.fill = LABEL_FILL
    val_cell.alignment = RIGHT
    val_cell.number_format = "#,##0"
    val_cell.border = BORDER_TOTAL
    ws.row_dimensions[total_row].height = 24

    widths = [7, 14, 42, 10, 14, 16, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ════════════════════════════════════════════════════════════════════════════
# SHEET 05: MA TRẬN SO SÁNH PHƯƠNG ÁN (VALUE ENGINEERING COMPARISON)
# ════════════════════════════════════════════════════════════════════════════
def populate_comparison_sheet(ws, handoff: dict):
    _apply_print_setup(ws, landscape=True, freeze_cell="A4")
    ws["A1"] = f'{handoff.get("Ten_Du_An", "DỰ ÁN")} — MA TRẬN SO SÁNH PHƯƠNG ÁN KẾT CẤU (VALUE ENGINEERING)'
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:H1")
    ws.row_dimensions[1].height = 26

    comparison = handoff.get("So_Sanh", {})
    categories = comparison.get("categories", [])
    plans = comparison.get("plans", {})
    if not categories or not plans:
        return

    _styled_header_cell(ws.cell(row=3, column=1, value="Tiêu chí Đánh giá"))
    for j, plan_name in enumerate(plans.keys()):
        _styled_header_cell(ws.cell(row=3, column=2 + j, value=plan_name))
    ws.row_dimensions[3].height = 26

    for i, cat in enumerate(categories, 1):
        row = 3 + i
        cat_cell = ws.cell(row=row, column=1, value=cat)
        cat_cell.font = LABEL_FONT
        cat_cell.border = BORDER_ALL
        cat_cell.fill = LABEL_FILL

        for j, plan_name in enumerate(plans.keys()):
            vals = plans[plan_name]
            val = vals[i - 1] if i - 1 < len(vals) else "—"
            cell = ws.cell(row=row, column=2 + j, value=val)
            _styled_data_cell(cell, alt=(i % 2 == 0), align=CENTER)
        ws.row_dimensions[row].height = 22

    if len(plans) >= 2:
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = "So sánh Hiệu quả Kỹ thuật - Kinh tế giữa các Phương án"
        chart.y_axis.title = "Điểm / Giá trị"
        chart.x_axis.title = "Tiêu chí"
        data = Reference(ws, min_col=2, min_row=3, max_col=1 + len(plans), max_row=3 + len(categories))
        cats = Reference(ws, min_col=1, min_row=4, max_row=3 + len(categories))
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.height = 10
        chart.width = 18
        ws.add_chart(chart, f"{get_column_letter(2 + len(plans) + 1)}3")

    ws.column_dimensions["A"].width = 28
    for j in range(len(plans)):
        ws.column_dimensions[get_column_letter(2 + j)].width = 20


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRYPOINTS (GIỮ TƯƠNG THÍCH NGƯỢC 100% VỚI MỌI CALLER)
# ════════════════════════════════════════════════════════════════════════════
def generate_boq_report(handoff: dict, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "BOQ"
    populate_boq_sheet(ws, handoff)
    ws_ctrl = wb.create_sheet("00_Doc_Control", 0)
    populate_doc_control_sheet(ws_ctrl, handoff)
    wb.save(output_path)
    return output_path


def generate_calc_sheet(handoff: dict, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Calc Sheet"
    populate_calc_sheet(ws, handoff)
    ws_eta = wb.create_sheet("Eta Summary")
    populate_eta_summary_sheet(ws_eta, handoff)
    ws_ctrl = wb.create_sheet("00_Doc_Control", 0)
    populate_doc_control_sheet(ws_ctrl, handoff)
    wb.save(output_path)
    return output_path


def generate_comparison_matrix(handoff: dict, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"
    populate_comparison_sheet(ws, handoff)
    ws_ctrl = wb.create_sheet("00_Doc_Control", 0)
    populate_doc_control_sheet(ws_ctrl, handoff)
    wb.save(output_path)
    return output_path


def generate_submittal_log(registry: dict, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Submittal Log"
    _apply_print_setup(ws, landscape=True, freeze_cell="A4")

    ws["A1"] = f'{registry.get("project_name", "DỰ ÁN")} — NHẬT KÝ ĐỆ TRÌNH & GIAO DỊCH KỸ THUẬT (SUBMITTAL LOG)'
    _styled_title_cell(ws["A1"])
    ws.merge_cells("A1:I1")

    headers = ["Mã Submittal", "Loại", "Mô tả", "Từ", "Đến", "Deadline", "Ngày tạo", "Trạng thái", "Mức ưu tiên"]
    for col, h in enumerate(headers, 1):
        _styled_header_cell(ws.cell(row=3, column=col, value=h))

    submittals = registry.get("documents", {}).get("SUBMITTAL", [])
    for i, doc in enumerate(submittals, 1):
        row = 3 + i
        tracking = doc.get("Tracking", {})
        vals = [
            doc.get("Doc_Code", ""),
            doc.get("Submittal_Type", "—"),
            doc.get("Issue", {}).get("Summary", ""),
            doc.get("From_Party", ""),
            doc.get("To_Party", ""),
            doc.get("Deadline", ""),
            tracking.get("Created_Date", ""),
            doc.get("Status", "Draft"),
            doc.get("Priority", "NORMAL"),
        ]
        for col, v in enumerate(vals, 1):
            _styled_data_cell(ws.cell(row=row, column=col, value=v), alt=(i % 2 == 0), align=CENTER if col != 3 else LEFT)
        _style_status_cell(ws.cell(row=row, column=9), vals[8])

    widths = [20, 14, 38, 16, 16, 14, 14, 15, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws2 = wb.create_sheet("Summary")
    ws2["A1"] = "Tổng quan Hồ sơ Đệ trình (Submittal Summary)"
    _styled_title_cell(ws2["A1"])
    ws2["A2"] = f"Tổng số đệ trình: {len(submittals)}"
    pending = sum(1 for d in submittals if d.get("Status", "").lower() in ("draft", "pending"))
    approved = sum(1 for d in submittals if d.get("Status", "").lower() == "approved")
    ws2["A3"] = f"Đang chờ duyệt (Pending): {pending}"
    ws2["A4"] = f"Đã phê duyệt (Approved): {approved}"
    ws2["A5"] = f"Từ chối / Yêu cầu trình lại (Rejected): {len(submittals) - pending - approved}"
    ws2.column_dimensions["A"].width = 36

    wb.save(output_path)
    return output_path


def generate_combined_report(
    handoff_or_registry: dict,
    output_path: str,
    include_boq: bool = True,
    include_calc: bool = True,
    include_comparison: bool = True,
):
    """
    Generate Master Multi-Sheet Workbook (v5.0):
    Đóng gói toàn bộ các Sheet vào CÙNG MỘT Workbook duy nhất (không ghi đè mất Sheet như bản cũ).
    """
    wb = Workbook()
    ws_ctrl = wb.active
    ws_ctrl.title = "00_Kiem_Soat_Ho_So"
    populate_doc_control_sheet(ws_ctrl, handoff_or_registry)

    if include_calc and ("Calculation_Logs" in handoff_or_registry or "calculation_logs" in handoff_or_registry):
        ws_calc = wb.create_sheet("01_Bang_Tinh_Chi_Tiet")
        populate_calc_sheet(ws_calc, handoff_or_registry)
        ws_eta = wb.create_sheet("02_Tong_Hop_Eta")
        populate_eta_summary_sheet(ws_eta, handoff_or_registry)

    if include_boq and "BOQ" in handoff_or_registry:
        ws_boq = wb.create_sheet("03_BOQ_Du_Toan")
        populate_boq_sheet(ws_boq, handoff_or_registry)

    if include_comparison and "So_Sanh" in handoff_or_registry:
        ws_cmp = wb.create_sheet("04_So_Sanh_Phuong_An")
        populate_comparison_sheet(ws_cmp, handoff_or_registry)

    wb.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="xlsx_report v5.0 — Bộ Xuất Bản Bảng Tính Kỹ Thuật Cấp Tư Vấn Hạng Nhất",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Đường dẫn file JSON handoff hoặc registry")
    parser.add_argument(
        "--type",
        default="combined",
        choices=["boq", "calc", "comparison", "submittal", "combined"],
        help="Loại báo cáo Excel (mặc định: combined đóng gói đa Sheet)",
    )
    parser.add_argument("--output", required=True, help="Đường dẫn file .xlsx đầu ra")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] File không tồn tại: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_path = args.output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)

    if args.type == "boq":
        generate_boq_report(data, output_path)
    elif args.type == "calc":
        generate_calc_sheet(data, output_path)
    elif args.type == "comparison":
        generate_comparison_matrix(data, output_path)
    elif args.type == "submittal":
        generate_submittal_log(data, output_path)
    elif args.type == "combined":
        generate_combined_report(data, output_path)

    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[OK] Đã xuất bản bảng tính Excel chuẩn Tư vấn Hạng Nhất: {output_path} ({size:,} bytes)")


if __name__ == "__main__":
    main()
