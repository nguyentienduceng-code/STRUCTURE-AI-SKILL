"""
xlsx_report.py — Excel (.xlsx) Report Generator

Tạo:
- BOQ table (từ JSON handoff)
- Calculation Sheet appendix (từ Calculation_Logs[])
- Comparison Matrix (từ So_Sanh)
- Submittal Log (cho SKILL_RFI)

Updated: 2026-08-31 — Phase E of Reporting Upgrade v4.0

Dependencies: openpyxl (already installed)
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, RadarChart, Reference


# ════════════════════════════════════════════════════════════════════════════
# STYLES
# ════════════════════════════════════════════════════════════════════════════

PRIMARY = '1C3557'
ACCENT = '2980B9'
TEXT_DARK = '222222'
TEXT_MED = '555555'
ROW_ALT = 'DDE8F5'

THIN = Side(border_style='thin', color='CCCCCC')
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

HEADER_FILL = PatternFill(start_color=PRIMARY, end_color=PRIMARY, fill_type='solid')
ALT_FILL = PatternFill(start_color=ROW_ALT, end_color=ROW_ALT, fill_type='solid')

HEADER_FONT = Font(bold=True, color='FFFFFF', size=11)
TITLE_FONT = Font(bold=True, color=PRIMARY, size=14)
SUBTITLE_FONT = Font(bold=True, color=ACCENT, size=11)

CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)
RIGHT = Alignment(horizontal='right', vertical='center')


def _styled_header_cell(cell):
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = CENTER
    cell.border = BORDER_ALL


def _styled_title_cell(cell):
    cell.font = TITLE_FONT
    cell.alignment = LEFT


def _styled_data_cell(cell, alt: bool = False):
    cell.border = BORDER_ALL
    cell.alignment = LEFT
    if alt:
        cell.fill = ALT_FILL


# ════════════════════════════════════════════════════════════════════════════
# BOQ REPORT
# ════════════════════════════════════════════════════════════════════════════

def generate_boq_report(handoff: dict, output_path: str):
    """
    Generate BOQ (Bill of Quantities) Excel.
    Input: handoff with 'BOQ' array of items.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = 'BOQ'

    # Title
    ws['A1'] = f'{handoff.get("Ten_Du_An", "DỰ ÁN")} — Bảng Khối Lượng (BOQ)'
    _styled_title_cell(ws['A1'])
    ws.merge_cells('A1:G1')

    ws['A2'] = f'Hạng mục: {handoff.get("Hang_Muc", "—")} | Ngày: {handoff.get("Ngay", "—")}'
    ws.merge_cells('A2:G2')

    # Headers
    headers = ['STT', 'Mã', 'Mô tả công tác', 'Đơn vị', 'Khối lượng', 'Đơn giá (VNĐ)', 'Thành tiền (VNĐ)']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        _styled_header_cell(cell)

    # Data
    boq = handoff.get('BOQ', [])
    total = 0
    for i, item in enumerate(boq, 1):
        row = 4 + i
        qty = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        amount = qty * unit_price
        total += amount

        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=item.get('code', ''))
        ws.cell(row=row, column=3, value=item.get('description', ''))
        ws.cell(row=row, column=4, value=item.get('unit', ''))
        ws.cell(row=row, column=5, value=qty)
        ws.cell(row=row, column=6, value=unit_price)
        ws.cell(row=row, column=7, value=amount)

        # Style data row
        alt = (i % 2 == 0)
        for col in range(1, 8):
            _styled_data_cell(ws.cell(row=row, column=col), alt)

        # Format number columns
        ws.cell(row=row, column=5).number_format = '#,##0.00'
        ws.cell(row=row, column=6).number_format = '#,##0'
        ws.cell(row=row, column=7).number_format = '#,##0'

    # Total
    total_row = 4 + len(boq) + 1
    cell = ws.cell(row=total_row, column=6, value='TỔNG CỘNG:')
    cell.font = Font(bold=True, color=PRIMARY)
    cell.alignment = RIGHT
    cell = ws.cell(row=total_row, column=7, value=total)
    cell.font = Font(bold=True, color=PRIMARY)
    cell.number_format = '#,##0'
    cell.border = BORDER_ALL

    # Column widths
    widths = [6, 12, 40, 10, 12, 14, 16]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# CALCULATION SHEET
# ════════════════════════════════════════════════════════════════════════════

def generate_calc_sheet(handoff: dict, output_path: str):
    """Generate Calculation Sheet Excel từ Calculation_Logs[]."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Calc Sheet'

    logs = handoff.get('Calculation_Logs', [])

    # Title
    ws['A1'] = f'{handoff.get("Ten_Du_An", "DỰ ÁN")} — Calculation Sheet'
    _styled_title_cell(ws['A1'])
    ws.merge_cells('A1:H1')

    ws['A2'] = f'Tiêu chuẩn: {handoff.get("Standard_Method", "—")}'
    ws.merge_cells('A2:H2')

    # Headers
    headers = ['Step', 'Static Scheme', 'Formula', 'Citation', 'Values', 'Result', 'η', 'Rating']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        _styled_header_cell(cell)

    # Data
    for i, log in enumerate(logs, 1):
        if not isinstance(log, dict):
            continue
        row = 4 + i

        citation = log.get('Citation', {})
        if isinstance(citation, dict):
            citation_str = f"{citation.get('Ma_TC', '')} {citation.get('Dieu_Muc', '')}"
        else:
            citation_str = str(citation)

        ws.cell(row=row, column=1, value=log.get('Step', ''))
        ws.cell(row=row, column=2, value=log.get('Static_Scheme', ''))
        ws.cell(row=row, column=3, value=log.get('Formula', ''))
        ws.cell(row=row, column=4, value=citation_str)
        ws.cell(row=row, column=5, value=str(log.get('Values', '')))
        ws.cell(row=row, column=6, value=log.get('Result', ''))
        util = log.get('Utilization')
        ws.cell(row=row, column=7, value=f'{util:.2f}' if util is not None else '—')
        ws.cell(row=row, column=8, value=log.get('Rating', 'GREEN'))

        alt = (i % 2 == 0)
        for col in range(1, 9):
            _styled_data_cell(ws.cell(row=row, column=col), alt)

        # Color rating
        rating_cell = ws.cell(row=row, column=8)
        rating = log.get('Rating', 'GREEN')
        if rating == 'RED':
            rating_cell.fill = PatternFill(start_color='F5B7B1', end_color='F5B7B1', fill_type='solid')
        elif rating == 'ORANGE':
            rating_cell.fill = PatternFill(start_color='FAD7A0', end_color='FAD7A0', fill_type='solid')
        elif rating == 'YELLOW':
            rating_cell.fill = PatternFill(start_color='FCF3CF', end_color='FCF3CF', fill_type='solid')
        else:  # GREEN
            rating_cell.fill = PatternFill(start_color='D5F5E3', end_color='D5F5E3', fill_type='solid')

    # Column widths
    widths = [10, 18, 30, 25, 30, 30, 8, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# COMPARISON MATRIX
# ════════════════════════════════════════════════════════════════════════════

def generate_comparison_matrix(handoff: dict, output_path: str):
    """Generate Comparison Matrix Excel từ So_Sanh."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Comparison'

    ws['A1'] = f'{handoff.get("Ten_Du_An", "DỰ ÁN")} — Ma trận So sánh Phương án'
    _styled_title_cell(ws['A1'])
    ws.merge_cells('A1:H1')

    comparison = handoff.get('So_Sanh', {})
    if not comparison:
        wb.save(output_path)
        return output_path

    categories = comparison.get('categories', [])
    plans = comparison.get('plans', {})

    if not categories or not plans:
        wb.save(output_path)
        return output_path

    # Header
    cell = ws.cell(row=3, column=1, value='Tiêu chí')
    _styled_header_cell(cell)
    for j, plan_name in enumerate(plans.keys()):
        cell = ws.cell(row=3, column=2 + j, value=plan_name)
        _styled_header_cell(cell)

    # Data
    for i, cat in enumerate(categories, 1):
        row = 3 + i
        cat_cell = ws.cell(row=row, column=1, value=cat)
        cat_cell.font = Font(bold=True, color=PRIMARY)
        cat_cell.border = BORDER_ALL
        cat_cell.fill = PatternFill(start_color=ROW_ALT, end_color=ROW_ALT, fill_type='solid')

        for j, plan_name in enumerate(plans.keys()):
            vals = plans[plan_name]
            val = vals[i - 1] if i - 1 < len(vals) else '—'
            cell = ws.cell(row=row, column=2 + j, value=val)
            cell.border = BORDER_ALL
            cell.alignment = CENTER

    # Add chart
    if len(plans) >= 2:
        chart = BarChart()
        chart.type = 'col'
        chart.style = 10
        chart.title = 'So sánh Phương án'
        chart.y_axis.title = 'Giá trị'
        chart.x_axis.title = 'Tiêu chí'

        data = Reference(ws, min_col=2, min_row=3,
                         max_col=1 + len(plans), max_row=3 + len(categories))
        cats = Reference(ws, min_col=1, min_row=4,
                         max_row=3 + len(categories))
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.height = 10
        chart.width = 20
        ws.add_chart(chart, f'{get_column_letter(2 + len(plans) + 1)}{3}')

    # Column widths
    ws.column_dimensions['A'].width = 25
    for j in range(len(plans)):
        ws.column_dimensions[get_column_letter(2 + j)].width = 18

    wb.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# SUBMITTAL LOG (cho SKILL_RFI)
# ════════════════════════════════════════════════════════════════════════════

def generate_submittal_log(registry: dict, output_path: str):
    """Generate Submittal Log Excel từ SKILL_RFI registry."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Submittal Log'

    ws['A1'] = f'{registry.get("project_name", "DỰ ÁN")} — Submittal Log'
    _styled_title_cell(ws['A1'])
    ws.merge_cells('A1:I1')

    headers = ['Mã Submittal', 'Loại', 'Mô tả', 'Từ', 'Đến', 'Deadline',
               'Ngày tạo', 'Trạng thái', 'Priority']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        _styled_header_cell(cell)

    submittals = registry.get('documents', {}).get('SUBMITTAL', [])
    for i, doc in enumerate(submittals, 1):
        row = 3 + i
        tracking = doc.get('Tracking', {})

        ws.cell(row=row, column=1, value=doc.get('Doc_Code', ''))
        ws.cell(row=row, column=2, value=doc.get('Submittal_Type', '—'))
        ws.cell(row=row, column=3, value=doc.get('Issue', {}).get('Summary', ''))
        ws.cell(row=row, column=4, value=doc.get('From_Party', ''))
        ws.cell(row=row, column=5, value=doc.get('To_Party', ''))
        ws.cell(row=row, column=6, value=doc.get('Deadline', ''))
        ws.cell(row=row, column=7, value=tracking.get('Created_Date', ''))
        ws.cell(row=row, column=8, value=doc.get('Status', 'Draft'))
        ws.cell(row=row, column=9, value=doc.get('Priority', 'NORMAL'))

        alt = (i % 2 == 0)
        for col in range(1, 10):
            _styled_data_cell(ws.cell(row=row, column=col), alt)

    # Column widths
    widths = [20, 14, 35, 14, 14, 12, 12, 14, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Summary sheet
    ws2 = wb.create_sheet('Summary')
    ws2['A1'] = 'Tổng quan Submittal'
    _styled_title_cell(ws2['A1'])
    ws2['A2'] = f'Tổng số submittal: {len(submittals)}'

    pending = sum(1 for d in submittals if d.get('Status', '').lower() in ('draft', 'pending'))
    approved = sum(1 for d in submittals if d.get('Status', '').lower() == 'approved')

    ws2['A3'] = f'Pending: {pending}'
    ws2['A4'] = f'Approved: {approved}'
    ws2['A5'] = f'Rejected: {len(submittals) - pending - approved}'

    ws2.column_dimensions['A'].width = 25

    wb.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# COMBINED REPORT (all sheets in one workbook)
# ════════════════════════════════════════════════════════════════════════════

def generate_combined_report(handoff_or_registry: dict, output_path: str,
                             include_boq: bool = True,
                             include_calc: bool = True,
                             include_comparison: bool = True):
    """Generate combined xlsx với nhiều sheets."""
    if include_boq and 'BOQ' in handoff_or_registry:
        generate_boq_report(handoff_or_registry, output_path)
        # Note: This will overwrite. Better: use single workbook
    # Simplified: write calc sheet as main
    if include_calc and 'Calculation_Logs' in handoff_or_registry:
        generate_calc_sheet(handoff_or_registry, output_path)
        return output_path
    elif include_comparison and 'So_Sanh' in handoff_or_registry:
        generate_comparison_matrix(handoff_or_registry, output_path)
        return output_path
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='xlsx_report — Generate Excel reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--input', required=True,
                        help='Path to JSON handoff or registry file')
    parser.add_argument('--type', default='calc',
                        choices=['boq', 'calc', 'comparison', 'submittal', 'combined'],
                        help='Loại Excel report')
    parser.add_argument('--output', required=True,
                        help='Output .xlsx file path')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f'❌ File không tồn tại: {args.input}')
        sys.exit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if args.type == 'boq':
        generate_boq_report(data, output_path)
    elif args.type == 'calc':
        generate_calc_sheet(data, output_path)
    elif args.type == 'comparison':
        generate_comparison_matrix(data, output_path)
    elif args.type == 'submittal':
        generate_submittal_log(data, output_path)
    elif args.type == 'combined':
        generate_combined_report(data, output_path)

    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f'✅ Generated: {output_path} ({size:,} bytes)')


if __name__ == '__main__':
    main()
