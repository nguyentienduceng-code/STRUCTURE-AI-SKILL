# -*- coding: utf-8 -*-
import sys
import json
import os
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# export_geotech_report.py — MODULE 10: Xuất Thuyết minh & Bảng tính Plaxis
# =============================================================================
# Version: 2.3.1
# Chuẩn: TCVN 9351:2012, CIRIA C760, Eurocode 7, Plaxis Material Models Manual
# Output: Excel đầy đủ 12 sheets + Markdown Thuyết minh mẫu
# Sheet mới: Sheet 12 "Phu luc Giai trinh" — Giải trình từng bước công thức
# =============================================================================

# ─── STYLE HELPERS ──────────────────────────────────────────────────────────

def _header_style(ws, row_idx, n_cols, bg="1F4E79"):
    fill = PatternFill("solid", fgColor=bg)
    font = Font(color="FFFFFF", bold=True, size=10, name="Calibri")
    align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = align
        cell.border = border

def _subheader_style(ws, row_idx, n_cols, bg="BDD7EE"):
    fill = PatternFill("solid", fgColor=bg)
    font = Font(bold=True, size=9, name="Calibri")
    align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = align
        cell.border = border

def _data_style(ws, row_idx, n_cols, even=False, alert=False, warning=False):
    if alert:
        bg = "FFE0E0"
    elif warning:
        bg = "FFFACD"
    else:
        bg = "E8F0FE" if even else "FFFFFF"
    font_color = "CC0000" if alert else ("8B6914" if warning else "000000")
    font = Font(size=9, name="Calibri", color=font_color)
    align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = PatternFill("solid", fgColor=bg)
        cell.font = font
        cell.alignment = align
        cell.border = border

def _set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

def _row(ws, row_idx, values):
    for col_idx, val in enumerate(values, start=1):
        ws.cell(row=row_idx, column=col_idx, value=val)


# ─── SHEET 1: KET QUA KSDC ─────────────────────────────────────────────────

def sheet_ksdc(wb, soil_layers):
    ws = wb.create_sheet("1_Ket qua KSDC")
    ws.sheet_properties.tabColor = "4472C4"

    headers = [
        "Lop", "Mo ta dia tang", "Cao do",
        "N_SPT", "Su (kPa)", "e0", "Cc", "Cs", "Ca",
        "Ip (%)", "gam_unsat", "gam_sat", "Loai dat"
    ]
    units = [
        "---", "---", "m",
        "bua/30cm", "kPa", "---", "---", "---", "---",
        "%", "kN/m3", "kN/m3", "---"
    ]

    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))
    _row(ws, 2, units)
    _subheader_style(ws, 2, len(units))

    for i, layer in enumerate(soil_layers, start=3):
        soil_type = layer.get("soil_type", layer.get("description", ""))
        _row(ws, i, [
            layer.get("layer_id", ""),
            layer.get("description", ""),
            f"{layer.get('top_depth', '')} ~ {layer.get('bottom_depth', '')}",
            layer.get("N_SPT", layer.get("spt_avg", "")),
            layer.get("Su", layer.get("Su_kpa", "")),
            layer.get("e0", ""),
            layer.get("Cc", ""),
            layer.get("Cs", ""),
            layer.get("Ca", ""),
            layer.get("Ip", layer.get("Ip_pct", "")),
            layer.get("gamma_unsat", ""),
            layer.get("gamma_sat", ""),
            soil_type[:30]
        ])
        _data_style(ws, i, len(headers), even=(i % 2 == 0))

    _set_widths(ws, [8, 36, 14, 10, 10, 8, 8, 8, 8, 8, 10, 10, 16])
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20
    ws.freeze_panes = "A3"
    return ws


# ─── SHEET 2: THONG SO DAT PLAXIS (TRANSPOSED) ─────────────────────────────

def sheet_plaxis_params(wb, soil_layers):
    ws = wb.create_sheet("2_Thong so Dat Plaxis")
    ws.sheet_properties.tabColor = "70AD47"

    headers_row1 = [
        "Thong so", "Don vi",
    ] + [f"Lop {l.get('layer_id', i+1)}" for i, l in enumerate(soil_layers)]
    headers_row2_note = [
        "---", "---",
    ] + [l.get('description', '')[:25] for l in soil_layers]

    _row(ws, 1, headers_row1)
    _header_style(ws, 1, len(headers_row1))
    _row(ws, 2, headers_row2_note)
    _subheader_style(ws, 2, len(headers_row2_note), bg="DDEBF7")

    n = len(soil_layers)
    rows = [
        ("Mo hinh", "---", *[l.get("model", "MC") for l in soil_layers]),
        ("Dieu kien thoat nuoc", "---", *[l.get("drainage_type", "---") for l in soil_layers]),
        ("gamma_unsat", "kN/m3", *[l.get("gamma_unsat_kn_m3", l.get("gamma_unsat", "")) for l in soil_layers]),
        ("gamma_sat", "kN/m3", *[l.get("gamma_sat_kn_m3", l.get("gamma_sat", "")) for l in soil_layers]),
        ("k_x", "m/day", *[l.get("k_x_m_per_day", "") for l in soil_layers]),
        ("k_y", "m/day", *[l.get("k_y_m_per_day", "") for l in soil_layers]),
        ("E50_ref", "kN/m2", *[l.get("E50_ref_kpa", "") for l in soil_layers]),
        ("Eoed_ref", "kN/m2", *[l.get("Eoed_ref_kpa", "") for l in soil_layers]),
        ("Eur_ref", "kN/m2", *[l.get("Eur_ref_kpa", "") for l in soil_layers]),
        ("m", "---", *[l.get("m", "") for l in soil_layers]),
        ("lambda*", "---", *[l.get("lambda_star", "") for l in soil_layers]),
        ("kappa*", "---", *[l.get("kappa_star", "") for l in soil_layers]),
        ("mu*", "---", *[l.get("mu_star", "") for l in soil_layers]),
        ("c_ref", "kN/m2", *[l.get("c_kpa", "") for l in soil_layers]),
        ("phi", "do", *[l.get("phi_deg", "") for l in soil_layers]),
        ("psi", "do", *[l.get("psi_deg", "") for l in soil_layers]),
        ("R_inter", "---", *[l.get("Rinter", "") for l in soil_layers]),
        ("nu_ur", "---", *[l.get("nu_ur", "") for l in soil_layers]),
        ("pref", "kN/m2", *[l.get("pref_kpa", 100) for l in soil_layers]),
    ]

    for i, r in enumerate(rows, start=3):
        _row(ws, i, r)
        _data_style(ws, i, len(r), even=(i % 2 == 0))

    _set_widths(ws, [20, 10] + [12] * n)
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20
    ws.freeze_panes = "C3"
    return ws


# ─── SHEET 3: UNG SUAT HUU HIEU ───────────────────────────────────────────

def sheet_stress_profile(wb, stress_data, gwl_depth=-2.0):
    ws = wb.create_sheet("3_Ung suat Huu hieu")
    ws.sheet_properties.tabColor = "FFC000"

    headers = [
        "Cao do (m)", "Chieu sau z (m)", "Ranh gioi",
        "Lop", "sigma_v", "u0", "sigma_v_eff",
        "K0", "sigma_x_eff", "Cong thuc tinh"
    ]
    units = [
        "m", "m", "---", "---",
        "kPa", "kPa", "kPa",
        "---", "kPa", "---"
    ]

    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))
    _row(ws, 2, units)
    _subheader_style(ws, 2, len(units))

    for i, point in enumerate(stress_data, start=3):
        z = point.get("z", 0)
        note = ""
        if abs(abs(z) - abs(gwl_depth)) < 0.1:
            note = "Muc nuoc ngam (GWT)"
        elif point.get("layer_name"):
            note = point.get("layer_name", "")

        _row(ws, i, [
            z,
            abs(z),
            note,
            point.get("layer_id", ""),
            point.get("sigma_z", ""),
            point.get("u", ""),
            point.get("sigma_z_eff", ""),
            point.get("K0", ""),
            point.get("sigma_x_eff", ""),
            point.get("K0_method", "")
        ])
        _data_style(ws, i, len(headers), even=(i % 2 == 0))

    _set_widths(ws, [12, 12, 26, 8, 12, 12, 12, 10, 12, 28])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A3"
    return ws


# ─── SHEET 4: BO SUNG - UNG SUAT RANH GIOI LOP (v2.3) ────────────────────

def sheet_boundary_stress(wb, boundary_stress, gwl_depth=-2.0):
    ws = wb.create_sheet("4_Ung suat Ran hgioi")
    ws.sheet_properties.tabColor = "FF9800"

    headers = [
        "Cao do (m)", "Ranh gioi", "Lop",
        "sigma_v (kPa)", "u0 (kPa)", "sigma_v_eff (kPa)",
        "K0", "sigma_h_eff (kPa)",
        "Cong thuc tinh"
    ]

    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    for i, pt in enumerate(boundary_stress, start=2):
        _row(ws, i, [
            pt.get("z", ""),
            pt.get("label", ""),
            pt.get("layer_id", ""),
            pt.get("sigma_v_kpa", ""),
            pt.get("u_kpa", ""),
            pt.get("sigma_v_eff_kpa", ""),
            pt.get("K0", ""),
            pt.get("sigma_h_eff_kpa", ""),
            pt.get("K0_method", "")
        ])
        is_gwt = "GWT" in (pt.get("label", "") or "")
        _data_style(ws, i, len(headers), even=(i % 2 == 0), warning=is_gwt)

    _set_widths(ws, [12, 28, 10, 14, 12, 16, 8, 16, 32])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 5: THONG SO KET CAU ─────────────────────────────────────────────

def sheet_structural(wb, structural_elements):
    ws = wb.create_sheet("5_Thong so Ket cau")
    ws.sheet_properties.tabColor = "5B9BD5"

    headers = [
        "Loai", "Ten phan tu", "Be day/Kieu",
        "A", "I", "E", "EA", "EI",
        "w", "nu", "He so nut", "Khoang cach",
        "N_Rd (kN)", "Lambda", "Phi",
        "Phan tu Plaxis"
    ]
    units = [
        "---", "---", "m/---",
        "m2/m", "m4/m", "kN/m2", "kN/m", "kNm2/m",
        "kN/m/m", "---", "---", "m",
        "kN", "---", "---",
        "---"
    ]

    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))
    _row(ws, 2, units)
    _subheader_style(ws, 2, len(units))

    for i, elem in enumerate(structural_elements, start=3):
        _row(ws, i, [
            elem.get("element_type", ""),
            elem.get("name", ""),
            elem.get("thickness_m", ""),
            elem.get("A_m2_per_m", ""),
            elem.get("I_m4_per_m", ""),
            elem.get("E_kpa", ""),
            elem.get("EA_kn_per_m", ""),
            elem.get("EI_knm2_per_m", ""),
            elem.get("w_kn_per_m2_per_m", ""),
            elem.get("nu", ""),
            elem.get("cracked_section_factor", ""),
            elem.get("spacing_m", ""),
            elem.get("N_Rd_kN", elem.get("N_Rd_or_M_Rd", "")),
            elem.get("lambda", ""),
            elem.get("phi", ""),
            elem.get("plaxis_element", "")
        ])
        _data_style(ws, i, len(headers), even=(i % 2 == 0))

    _set_widths(ws, [20, 24, 12, 12, 12, 14, 14, 14, 12, 8, 12, 12, 14, 12, 10, 18])
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A3"
    return ws


# ─── SHEET 6: BASE HEAVE CHECK (v2.3) ─────────────────────────────────────

def sheet_base_heave(wb, base_heave_data):
    ws = wb.create_sheet("6_Base Heave")
    ws.sheet_properties.tabColor = "C00000"

    if not base_heave_data or base_heave_data.get("error"):
        _row(ws, 1, ["Chua co du lieu Base Heave"])
        _header_style(ws, 1, 1)
        return ws

    headers = ["Thong so", "Gia tri", "Don vi", "Cong thuc/Ghi chu"]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    ex = base_heave_data.get("excavation_data", {})
    rows = [
        ("--- KICH THUOC HO DAO ---", "", "", ""),
        ("B (be rong)", ex.get("B_m", ""), "m", ""),
        ("L (chieu dai)", ex.get("L_m", ""), "m", ""),
        ("H_đao (chieu sau)", ex.get("H_exc_m", ""), "m", ""),
        ("D_ngam cu (neu co)", ex.get("D_pile_m", ""), "m", ""),
        ("--- TINH TOAN ---", "", "", ""),
        ("Nc", base_heave_data.get("Nc", ""), "---", "Nc = 5.14 × (1 + 0.2 × B/L)"),
        ("gamma_avg", base_heave_data.get("gamma_avg_kNm3", ""), "kN/m3", "Tinh phan lop tu mat dat den day ho"),
        ("Su", ex.get("Su_kpa", ""), "kPa", "Sức kháng cắt không thoát nước"),
        ("q (hoat tai)", ex.get("q_kpa", ""), "kPa", "Hoat tai tren mep ho"),
        ("sigma_v_base", base_heave_data.get("sigma_v_base_kpa", ""), "kPa", "σv = γ_avg × H + q"),
        ("--- KET QUA ---", "", "", ""),
        ("Fs", base_heave_data.get("Fs", ""), "---", "Fs = (Nc × Su) / σv_base"),
        ("Fs_cho phep", base_heave_data.get("Fs_allow", 1.50), "---", "Fs_min = 1.50"),
        ("eta = Fs/Fs_allow", base_heave_data.get("eta", ""), "---", "η ≤ 0.70: OK | 0.70-0.90: Tot | 0.90-1.0: Luu y | > 1.0: Vuot"),
        ("Trang thai", base_heave_data.get("status", ""), "---", base_heave_data.get("status_note", "")),
    ]

    for i, r in enumerate(rows, start=2):
        _row(ws, i, r)
        is_section = r[0].startswith("---")
        is_result = r[0] in ("Fs", "eta = Fs/Fs_allow", "Trang thai")
        _data_style(ws, i, len(headers), alert=is_result and base_heave_data.get("eta", 0) > 1.0)

    _set_widths(ws, [24, 16, 10, 48])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 7: STRUT CAPACITY (v2.3) ──────────────────────────────────────

def sheet_strut_capacity(wb, strut_data):
    ws = wb.create_sheet("7_Strut Capacity")
    ws.sheet_properties.tabColor = "7030A0"

    if not strut_data or strut_data.get("error"):
        _row(ws, 1, ["Chua co du lieu Strut"])
        _header_style(ws, 1, 1)
        return ws

    headers = ["Buoc", "Cong thuc / Thong so", "Gia tri", "Don vi", "Ghi chu"]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    rows = []
    for log in strut_data.get("Calculation_Logs", []):
        step = log.get("step", "")
        formula = log.get("formula", "")
        vals = []
        ghi_chu = ""

        if step == "1. Đặc trưng hình học":
            vals = [step, formula, strut_data.get("A_cm2", ""), "cm2", ""]
        elif step == "2. Chiều dài tính toán":
            vals = [step, formula, strut_data.get("L_0_calc_m", ""), "m", f"L_span={strut_data.get('L_span_m')}m, μ={strut_data.get('mu')}"]
        elif step == "3. Kiểm tra độ mảnh":
            vals = [step, formula, f"λ={strut_data.get('lambda', '')}", "---",
                    f"λ_allow=150 | {strut_data.get('slenderness_check', '')}"]
        elif step == "4. Độ mảnh quy ước":
            vals = [step, formula, strut_data.get("lambda_bar", ""), "---", ""]
        elif step == "5. Tính hệ số uốn dọc":
            vals = [step, formula, strut_data.get("phi", ""), "---", strut_data.get("buckling_note", "")]
        elif step == "6. Khả năng chịu nén":
            vals = [step, formula, strut_data.get("N_Rd_kN", ""), "kN",
                    f"f_y={strut_data.get('f_y_kpa', '')/1000:.0f} MPa, grade={strut_data.get('steel_grade', '')}"]
        elif step == "7. Kiểm tra với N_Ed":
            vals = [step, f"N_Ed={strut_data.get('N_Ed_kn','')}, N_Rd={strut_data.get('N_Rd_kN','')}",
                    f"η={strut_data.get('eta_N', '')}", "---", strut_data.get("status_N", "")]

        if vals:
            rows.append(vals)

    for i, r in enumerate(rows, start=2):
        _row(ws, i, r)
        is_over = strut_data.get("eta_N", 0) and float(strut_data.get("eta_N", 0)) > 1.0
        _data_style(ws, i, len(headers), alert=is_over)

    # Summary row
    summary_row = len(rows) + 2
    _row(ws, summary_row, [
        "KET QUA", f"N_Rd = {strut_data.get('N_Rd_kN', '')} kN",
        f"η = {strut_data.get('eta_N', 'N/A')}",
        "---", strut_data.get("status_N", "")
    ])
    _header_style(ws, summary_row, len(headers))

    _set_widths(ws, [28, 40, 14, 10, 40])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 8: KIEM CHUNG SLS ────────────────────────────────────────────────

def sheet_sls_check(wb, sls_checks):
    ws = wb.create_sheet("8_Kiem chung SLS")
    ws.sheet_properties.tabColor = "FF6B6B"

    headers = [
        "#", "Tieu chi kiem tra", "Gia tri Plaxis",
        "Gia tri cho phep", "He so (η)", "Trang thai", "Tieu chuan"
    ]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    for i, check in enumerate(sls_checks, start=2):
        eta = check.get("eta", 0)
        is_alert = eta and float(eta) > 1.0

        vals = [
            i - 1,
            check.get("name", ""),
            check.get("calculated", ""),
            check.get("allowable", ""),
            eta,
            check.get("status", ""),
            check.get("standard", "")
        ]
        _row(ws, i, vals)
        _data_style(ws, i, len(vals), even=(i % 2 == 0), alert=is_alert)

        eta_cell = ws.cell(row=i, column=5)
        try:
            eta_val = float(eta)
            if eta_val <= 0.70:
                eta_cell.fill = PatternFill("solid", fgColor="92D050")
            elif eta_val <= 0.90:
                eta_cell.fill = PatternFill("solid", fgColor="FFFF00")
            elif eta_val <= 1.00:
                eta_cell.fill = PatternFill("solid", fgColor="FF9900")
            else:
                eta_cell.fill = PatternFill("solid", fgColor="FF4444")
                eta_cell.font = Font(bold=True, color="FFFFFF")
        except (TypeError, ValueError):
            pass

    _set_widths(ws, [6, 32, 18, 18, 12, 32, 24])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 9: GROUND TRUTH COMPARISON (v2.3) ───────────────────────────────

def sheet_ground_truth(wb, soil_layers):
    ws = wb.create_sheet("9_Ground Truth")
    ws.sheet_properties.tabColor = "00B050"

    headers = [
        "Lop", "Loai dat", "SPT",
        "E50 tinh (kPa)", "Cong thuc", "Ke/alpha",
        "E50 GT (kPa)", "Du an tham chieu",
        "Deviance (%)", "Canh bao"
    ]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    for i, layer in enumerate(soil_layers, start=2):
        gt_check = layer.get("Ground_Truth_Check", {})
        status = gt_check.get("status", "")
        warnings = gt_check.get("warnings", [])
        gt_ref = gt_check.get("ground_truth_reference", {})

        is_warning = "WARNING" in status or "W001" in str(warnings)

        e50_calc = layer.get("E50_ref_kpa", "")
        e50_gt = gt_ref.get("parameters", {}).get("E50_ref_kpa", "") if gt_ref else ""
        deviance = ""
        if e50_calc and e50_gt:
            try:
                dev = abs(float(e50_calc) - float(e50_gt)) / float(e50_gt) * 100
                deviance = f"{dev:.1f}%"
            except:
                deviance = "N/A"

        Ke_data = layer.get("Ke_data", {})
        Alpha_data = layer.get("Alpha_data", {})
        if Ke_data:
            formula = f"E50 = Ke × Su"
            Ka = f"Ke={Ke_data.get('recommended', '')}"
        elif Alpha_data:
            formula = f"E50 = α × N_SPT"
            Ka = f"α={Alpha_data.get('recommended', '')}"
        else:
            formula = ""
            Ka = ""

        _row(ws, i, [
            layer.get("layer_id", ""),
            layer.get("description", "")[:30],
            layer.get("spt_input", layer.get("N_SPT", "")),
            e50_calc,
            formula,
            Ka,
            e50_gt,
            gt_ref.get("project", "") if gt_ref else "",
            deviance,
            status if is_warning else "OK"
        ])
        _data_style(ws, i, len(headers), even=(i % 2 == 0), warning=is_warning)

    _set_widths(ws, [8, 28, 8, 14, 16, 14, 14, 22, 12, 18])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 10: CALC LOGS MO RONG (v2.3) ──────────────────────────────────

def sheet_calc_logs(wb, soil_layers, calc_logs=None):
    ws = wb.create_sheet("10_Calc Logs")
    ws.sheet_properties.tabColor = "ED7D31"

    headers = ["Lop", "Buoc", "Cong thuc", "Thay so", "Ket qua", "Nguon", "Trang thai"]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    row_idx = 2
    for layer in soil_layers:
        layer_id = layer.get("layer_id", "")
        layer_logs = layer.get("Calculation_Logs", [])

        if not layer_logs:
            _row(ws, row_idx, [layer_id, "(khong co logs)", "", "", "", "", ""])
            _data_style(ws, row_idx, len(headers))
            row_idx += 1
            continue

        for log in layer_logs:
            formula = log.get("formula", "")
            result_val = log.get("result", log.get("E50_final", ""))

            # Format calculation details
            if log.get("E50_calc"):
                thay_so = f"Ke={log.get('Ke_selected', '')}, Su={log.get('Su_kpa', 'N/A')}"
                result_disp = f"E50={log.get('E50_final', '')} kPa"
            elif log.get("E50_calc") is not None and not isinstance(log.get("E50_calc"), str):
                thay_so = f"α={log.get('alpha_selected', '')}, N={log.get('spt_input', '')}"
                result_disp = f"E50={log.get('E50_final', '')} kPa"
            else:
                thay_so = str(log.get("inputs", ""))[:40]
                result_disp = str(result_val)[:30]

            status = ""
            if log.get("status") == "CẢNH BÁO":
                status = "⚠️ " + str(log.get("warnings", [""])[0])[:50]

            _row(ws, row_idx, [
                layer_id,
                log.get("step", ""),
                formula[:50],
                thay_so[:40],
                result_disp[:30],
                log.get("source", "")[:24],
                status
            ])
            _data_style(ws, row_idx, len(headers), even=(row_idx % 2 == 0),
                        warning="CẢNH BÁO" in status)
            row_idx += 1

    _set_widths(ws, [10, 24, 50, 40, 30, 24, 50])
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 11: HUONG DAN JSON ──────────────────────────────────────────────

def sheet_guide(wb):
    ws = wb.create_sheet("11_Huong dan JSON")
    ws.sheet_properties.tabColor = "808080"

    headers = ["Truong du lieu", "Mo ta & Don vi"]
    _row(ws, 1, headers)
    _header_style(ws, 1, len(headers))

    guide = [
        ("=== SO LIEU DIA CHAT (soil_layers[]) ===", ""),
        ("layer_id", "Ky hieu lop dat (VD: '1', '2a', 'II')"),
        ("description", "Mo ta lop dat"),
        ("soil_type", "Cat / Set / But / Set pha"),
        ("top_depth, bottom_depth", "Cao do dau va cuoi lop (m, am)"),
        ("N_SPT hoac spt_avg", "Chi so SPT trung binh (bua/30cm)"),
        ("Su_kpa", "Suc khang cat khong thoat nuoc (kPa) - CHO DAT DINH"),
        ("Ip_pct", "Chi so deo Ip (%) - de chon Ke chinh xac"),
        ("model", "Mohr-Coulomb | Hardening Soil | Soft Soil Creep"),
        ("drainage_type", "Drained | Undrained (A) | Undrained (B)"),
        ("gamma_unsat, gamma_sat", "Dung trong (kN/m3)"),
        ("e0, Cc, Cs, Ca", "Chi so oedometer (---)"),
        ("E50_ref_kpa", "Module cat tuyen tham chieu HS (kPa) - tu SPT/Lab"),
        ("m", "He so mu (---) - cho HS"),
        ("c_kpa, phi_deg, psi_deg", "Thong so cuong do (kPa, do)"),
        ("Rinter", "He so tuong tac dat-ket cau (---)"),
        ("k_x_m_per_day, k_y_m_per_day", "He so tham (m/day)"),
        ("", ""),
        ("=== KET CAU CHAN GIU (structural_elements[]) ===", ""),
        ("element_type", "Diaphragm Wall | Sheet Pile | Strut | Anchor"),
        ("thickness_m", "Be day (m)"),
        ("concrete_grade", "Mac BT (VD: B25)"),
        ("cracked_section_factor", "He so giam doc cung EI (0.5-0.7)"),
        ("", ""),
        ("=== KIEM TRA SLS (sls_checks[]) ===", ""),
        ("name", "Ten tieu chi (VD: 'Chuyen vi ngang cu max')"),
        ("calculated", "Gia tri tu Plaxis (VD: '15.2 mm')"),
        ("allowable", "Gia tri cho phep (VD: '19.75 mm')"),
        ("eta", "He so su dung = calculated/allowable"),
        ("standard", "Tieu chuan (VD: 'Clough & O'Rourke 1990')"),
        ("", ""),
        ("=== BASE HEAVE (excavation) ===", ""),
        ("B_m, L_m, H_exc_m", "Kich thuoc ho dao (m)"),
        ("Su_kpa", "Suc khang cat khong thoat nuoc (kPa)"),
        ("q_kpa", "Hoat tai mep ho (mac dinh 10 kPa)"),
        ("D_pile_m", "Chieu sau ngam cu duoi day ho (m)"),
    ]

    for i, (key, desc) in enumerate(guide, start=2):
        ws.cell(row=i, column=1, value=key)
        ws.cell(row=i, column=2, value=desc)
        if key.startswith("==="):
            _subheader_style(ws, i, 2, bg="E2EFDA")
        else:
            _data_style(ws, i, 2, even=(i % 2 == 0))

    _set_widths(ws, [36, 60])
    ws.freeze_panes = "A2"
    return ws


# ─── SHEET 12: PHU LUC GIAI TRINH CHI TIET (v2.3.1) ─────────────────────

def sheet_appendix(wb, soil_layers, calc_steps=None):
    """
    Sheet 12: Phụ lục Giải trình Chi tiết
    Theo yêu cầu Rule 7.1 — Bắt buộc giải trình từng bước công thức.
    """
    ws = wb.create_sheet("12_Phu luc Giai trinh")
    ws.sheet_properties.tabColor = "7030A0"

    # Title
    ws.cell(row=1, column=1, value="PHỤ LỤC GIẢI TRÌNH TÍNH TOÁN CHI TIẾT")
    _header_style(ws, 1, 1, bg="1F4E79")
    ws.merge_cells("A1:G1")
    ws.cell(row=1, column=1).font = Font(color="FFFFFF", bold=True, size=13)

    # Disclaimer
    ws.cell(row=2, column=1,
            value="Theo yêu cầu Rule 7.1 — Mọi kết quả quy đổi BẮT BUỘC đi kèm giải trình công thức gốc.")
    ws.cell(row=2, column=1).font = Font(italic=True, size=9, color="C00000")
    ws.merge_cells("A2:G2")

    row = 4
    for layer in soil_layers:
        layer_id = layer.get("layer_id", "?")
        is_cohesive = layer.get("is_cohesive", False)
        spt = layer.get("spt_input", layer.get("N_SPT", "?"))
        e50 = layer.get("E50_ref_kpa", "?")
        Ke_data = layer.get("Ke_data")
        Alpha_data = layer.get("Alpha_data")

        # ── Layer Header ──
        ws.cell(row=row, column=1,
                value=f"Lớp {layer_id}: {layer.get('description', '')}")
        _header_style(ws, row, 7, bg="2E75B6")
        ws.merge_cells(f"A{row}:G{row}")
        row += 1

        # ── Section: Co so ly thuyet ──
        ws.cell(row=row, column=1, value="I. CƠ SỞ LÝ THUYẾT")
        _subheader_style(ws, row, 7, bg="BDD7EE")
        ws.merge_cells(f"A{row}:G{row}")
        row += 1

        source = "Jamiolkowski et al. (1979); Stroud (1974); CIRIA C760" if is_cohesive \
                 else "Bowles (1997); Webb (1969); CIRIA C760"
        ws.cell(row=row, column=1, value=f"Nguồn: {source}")
        ws.merge_cells(f"A{row}:G{row}")
        row += 2

        # ── Section: Cong thuc tong quat ──
        ws.cell(row=row, column=1, value="II. CÔNG THỨC TỔNG QUÁT")
        _subheader_style(ws, row, 7, bg="BDD7EE")
        ws.merge_cells(f"A{row}:G{row}")
        row += 1

        if is_cohesive:
            formula_lines = [
                "ĐẤT DÍNH: E50ref = Ke × Su",
                "  Ke: Hệ số cứng, Ke = E50 / Su",
                "  Su: Sức kháng cắt không thoát nước [kPa]",
                "",
                "Bảng Ke theo Ip (CIRIA C760 / Jamiolkowski):",
                "  Ip < 15%  → Ke = 400 (sét mềm, bùn)",
                "  Ip 15-25% → Ke = 500 (sét dẻo mềm)",
                "  Ip 25-40% → Ke = 600 (sét trung bình)",
                "  Ip 40-60% → Ke = 710 (sét nửa cứng)",
                "  Ip > 60%   → Ke = 1000 (sét cứng)",
            ]
        else:
            formula_lines = [
                "ĐẤT RỜI: E50ref = α × N_SPT",
                "  α: Hệ số kinh nghiệm [kN/m² per SPT]",
                "  N_SPT: Chỉ số SPT đã hiệu chỉnh [búa/30cm]",
                "",
                "Bảng α theo loại cát (Bowles 1997 / CIRIA C760):",
                "  Cát mịn, rời         → α = 1,500 kPa/búa",
                "  Cát trung, chặt vừa  → α = 2,000 kPa/búa",
                "  Cát thô, chặt         → α = 2,500 kPa/búa",
                "  Cát sỏi, rất chặt    → α = 3,000 kPa/búa",
            ]

        for line in formula_lines:
            ws.cell(row=row, column=1, value=line)
            ws.cell(row=row, column=1).font = Font(name="Courier New", size=9)
            ws.merge_cells(f"A{row}:G{row}")
            row += 1
        row += 1

        # ── Section: The so va tinh toan ──
        ws.cell(row=row, column=1, value="III. THẾ SỐ VÀ TÍNH TOÁN")
        _subheader_style(ws, row, 7, bg="BDD7EE")
        ws.merge_cells(f"A{row}:G{row}")
        row += 1

        # Step-by-step from calc_logs
        calc_logs = layer.get("Calculation_Logs", [])
        if calc_logs:
            for log in calc_logs:
                step = log.get("step", "")
                formula = log.get("formula", "")
                result = log.get("E50_final", log.get("result", ""))
                source = log.get("source", "")

                ws.cell(row=row, column=1, value=step)
                ws.cell(row=row, column=1).font = Font(bold=True, size=9)
                ws.merge_cells(f"A{row}:G{row}")
                row += 1

                if formula:
                    ws.cell(row=row, column=1, value=f"  Công thức: {formula}")
                    ws.cell(row=row, column=1).font = Font(name="Courier New", size=9)
                    ws.merge_cells(f"A{row}:G{row}")
                    row += 1

                if result:
                    ws.cell(row=row, column=1, value=f"  Kết quả: {result}")
                    ws.cell(row=row, column=1).font = Font(name="Courier New", size=9, bold=True)
                    ws.merge_cells(f"A{row}:G{row}")
                    row += 1

                if source:
                    ws.cell(row=row, column=1, value=f"  Nguồn: {source}")
                    ws.cell(row=row, column=1).font = Font(italic=True, size=9)
                    ws.merge_cells(f"A{row}:G{row}")
                    row += 1

                row += 1
        else:
            # Fallback: generic step
            if is_cohesive and Ke_data:
                Ke = Ke_data.get("recommended", "?")
                Su = layer.get("Su_kpa", "?")
                ws.cell(row=row, column=1,
                        value=f"Bước 1: E50ref = Ke × Su = {Ke} × {Su} = {e50} kPa")
                ws.cell(row=row, column=1).font = Font(name="Courier New", size=9)
                ws.merge_cells(f"A{row}:G{row}")
                row += 1
            elif not is_cohesive and Alpha_data:
                alpha = Alpha_data.get("recommended", "?")
                ws.cell(row=row, column=1,
                        value=f"Bước 1: E50ref = α × N_SPT = {alpha} × {spt} = {e50} kPa")
                ws.cell(row=row, column=1).font = Font(name="Courier New", size=9)
                ws.merge_cells(f"A{row}:G{row}")
                row += 1

        # ── Section: Ket qua ──
        ws.cell(row=row, column=1, value="IV. KẾT QUẢ QUY ĐỔI — THÔNG SỐ ĐẦU VÀO PLAXIS")
        _subheader_style(ws, row, 7, bg="BDD7EE")
        ws.merge_cells(f"A{row}:G{row}")
        row += 1

        result_headers = [
            "E50_ref", "Eoed_ref", "Eur_ref", "m", "c'", "phi'", "psi"
        ]
        result_values = [
            layer.get("E50_ref_kpa", ""),
            layer.get("Eoed_ref_kpa", ""),
            layer.get("Eur_ref_kpa", ""),
            layer.get("m", ""),
            layer.get("c_kpa", ""),
            layer.get("phi_deg", ""),
            layer.get("psi_deg", ""),
        ]
        units = ["kN/m²", "kN/m²", "kN/m²", "—", "kN/m²", "°", "°"]

        for h, v, u in zip(result_headers, result_values, units):
            ws.cell(row=row, column=1, value=h)
            ws.cell(row=row, column=2, value=v)
            ws.cell(row=row, column=3, value=u)
            _data_style(ws, row, 7, even=(row % 2 == 0))
            row += 1

        # ── Section: Ground Truth ──
        gt = layer.get("Ground_Truth_Check", {})
        if gt and gt.get("status") != "NO_MATCH":
            row += 1
            ws.cell(row=row, column=1, value="V. KIỂM CHỨNG GROUND TRUTH")
            _subheader_style(ws, row, 7, bg="BDD7EE")
            ws.merge_cells(f"A{row}:G{row}")
            row += 1

            gt_ref = gt.get("ground_truth_reference", {})
            ws.cell(row=row, column=1,
                    value=f"Dự án tham chiếu: {gt_ref.get('project', '?')} — Lớp: {gt_ref.get('layer_name', '?')}")
            ws.merge_cells(f"A{row}:G{row}")
            row += 1

            status = gt.get("status", "")
            warnings = gt.get("warnings", [])
            if warnings:
                for w in warnings:
                    ws.cell(row=row, column=1, value=f"⚠ Cảnh báo: {w}")
                    ws.cell(row=row, column=1).font = Font(color="C00000", bold=True)
                    ws.merge_cells(f"A{row}:G{row}")
                    row += 1

        # ── Separator between layers ──
        row += 2

    # Footer disclaimer
    ws.cell(row=row, column=1,
            value="> Kết quả tính toán mang tính tham khảo. Kỹ sư CCHN phải rà soát trước khi sử dụng.")
    ws.cell(row=row, column=1).font = Font(italic=True, size=9, color="7F7F7F")
    ws.merge_cells(f"A{row}:G{row}")

    _set_widths(ws, [20, 16, 12, 12, 12, 12, 12])
    ws.row_dimensions[1].height = 22
    return ws


# ─── MAIN EXPORT FUNCTIONS ────────────────────────────────────────────────

def generate_excel(data, out_xlsx):
    wb = Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    soil_layers = data.get("soil_layers", [])
    stress_profile = data.get("stress_profile", [])
    boundary_stress = data.get("layer_boundary_stress", [])
    structural_elements = data.get("structural_elements", [])
    sls_checks = data.get("sls_checks", [])
    base_heave = data.get("base_heave_check", {})
    strut_data = data.get("strut_capacity", {})

    sheet_ksdc(wb, soil_layers)
    sheet_plaxis_params(wb, soil_layers)
    sheet_stress_profile(wb, stress_profile, data.get("gwl_depth", -2.0))
    if boundary_stress:
        sheet_boundary_stress(wb, boundary_stress, data.get("gwl_depth", -2.0))
    sheet_structural(wb, structural_elements)
    sheet_base_heave(wb, base_heave)
    sheet_strut_capacity(wb, strut_data)
    sheet_sls_check(wb, sls_checks)
    sheet_ground_truth(wb, soil_layers)
    sheet_calc_logs(wb, soil_layers)
    sheet_guide(wb)
    sheet_appendix(wb, soil_layers)  # Sheet 12: Phu luc Giai trinh (v2.3.1)

    wb.save(out_xlsx)
    print(f"-> Generated Excel: {out_xlsx}")
    return out_xlsx


# ─── MARKDOWN REPORT ───────────────────────────────────────────────────────

def generate_markdown_report(data, out_md):
    lines = []
    project_name = data.get("project_name", "Du an")
    author = data.get("author", "SKILL_GEOTECH v2.3")
    layers = data.get("soil_layers", [])

    lines.append("# THUYẾT MINH TÍNH TOÁN ĐỊA KỸ THUẬT & BIỆN PHÁP THI CÔNG HỐ ĐÀO")
    lines.append("")
    lines.append(f"## DỰ ÁN: {project_name}")
    lines.append(f"**Công cụ lập:** {author}")
    lines.append(f"**Phiên bản SKILL_GEOTECH:** v2.3.0")
    lines.append("")

    # === SECTION 1 ===
    lines.append("## 1. TỔNG QUAN QUY MÔ & ĐIỀU KIỆN ĐỊA HÌNH - ĐỊA CHẤT THỦY VĂN")
    lines.append("")
    if data.get("excavation_depth"):
        lines.append(f"- Chiều sâu hố đào: **H = {data.get('excavation_depth')} m**")
    if data.get("excavation_dimensions"):
        lines.append(f"- Kích thước mặt bằng hố đào: **{data.get('excavation_dimensions')}**")
    if data.get("retaining_system"):
        lines.append(f"- Hệ chắn giữ: {data.get('retaining_system')}")
    if data.get("gwl_depth"):
        lines.append(f"- Mực nước ngầm (GWT): **-{abs(data.get('gwl_depth', 0)):.2f} m**")
    lines.append("")

    # === SECTION 2: KSDC ===
    lines.append("## 2. KẾT QUẢ KHẢO SÁT ĐỊA CHẤT CÔNG TRÌNH")
    lines.append("")
    lines.append("| Lớp đất | Mô tả địa tầng | Cao độ (m) | $N_{SPT}$ | $S_u$ (kPa) | $\\gamma_{sat}$ | $\\gamma_{unsat}$ |")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
    for layer in layers:
        depth = f"{layer.get('top_depth', '')} ~ {layer.get('bottom_depth', '')}"
        lines.append(
            f"| {layer.get('layer_id','')} | {layer.get('description','')} | "
            f"{depth} | {layer.get('spt_input', layer.get('N_SPT',''))} | "
            f"{layer.get('Su_kpa', layer.get('Su', ''))} | "
            f"{layer.get('gamma_sat_kn_m3', layer.get('gamma_sat', ''))} | "
            f"{layer.get('gamma_unsat_kn_m3', layer.get('gamma_unsat', ''))} |"
        )
    lines.append("")

    # === SECTION 3: ỨNG SUẤT HỮU HIỆU ===
    bs = data.get("layer_boundary_stress", [])
    if bs:
        lines.append("## 3. BẢNG ỨNG SUẤT HỮU HIỆU TẠI RANH GIỚI LỚP (v2.3)")
        lines.append("")
        lines.append("| Cao độ (m) | Ranh giới | Lớp | $\\sigma_v$ (kPa) | $u_0$ (kPa) | $\\sigma'_v$ (kPa) | $K_0$ | $\\sigma'_h$ (kPa) |")
        lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
        for pt in bs:
            lines.append(
                f"| {pt.get('z','')} | {pt.get('label','')} | {pt.get('layer_id','')} | "
                f"{pt.get('sigma_v_kpa','')} | {pt.get('u_kpa','')} | {pt.get('sigma_v_eff_kpa','')} | "
                f"{pt.get('K0','')} | {pt.get('sigma_h_eff_kpa','')} |"
            )
        lines.append("")
    elif data.get("stress_profile"):
        lines.append("## 3. BẢNG ỨNG SUẤT HỮU HIỆU THEO CHIỀU SÂU")
        lines.append("")
        lines.append("| Cao độ (m) | Ranh giới | $\\sigma_v$ | $u_0$ | $\\sigma'_v$ | $K_0$ | $\\sigma'_h$ |")
        lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
        for pt in data.get("stress_profile", [])[:20]:
            lines.append(
                f"| {pt.get('z','')} | {pt.get('layer_name','')} | "
                f"{pt.get('sigma_z','')} | {pt.get('u','')} | {pt.get('sigma_z_eff','')} | "
                f"{pt.get('K0','')} | {pt.get('sigma_x_eff','')} |"
            )
        lines.append("")

    # === SECTION 4: PLAXIS PARAMS ===
    lines.append("## 4. BẢNG THÔNG SỐ ĐẦU VÀO MÔ HÌNH PLAXIS")
    if layers:
        n = len(layers)
        layer_ids = [l.get('layer_id', '') for l in layers]
        descs = [l.get('description', '')[:20] for l in layers]
        lines.append("")
        lines.append(f"| Thông số | Đơn vị | " + " | ".join(layer_ids) + " |")
        lines.append("|:---|:---:|" + ":---:|" * n)
        lines.append("| **Mô tả** | --- | " + " | ".join(descs) + " |")

        def mrow(label, unit, key, fmt=None):
            vals = []
            for l in layers:
                v = l.get(key, '')
                if v != '' and fmt:
                    try: v = fmt.format(float(v))
                    except: pass
                vals.append(str(v) if v != '' else '---')
            return f"| {label} | {unit} | " + " | ".join(vals) + " |"

        lines.append(mrow("$E_{50}^{ref}$", "kN/m²", "E50_ref_kpa"))
        lines.append(mrow("$E_{oed}^{ref}$", "kN/m²", "Eoed_ref_kpa"))
        lines.append(mrow("$E_{ur}^{ref}$", "kN/m²", "Eur_ref_kpa"))
        lines.append(mrow("$m$", "---", "m"))
        lines.append(mrow("$c'$", "kN/m²", "c_kpa"))
        lines.append(mrow("$\\phi'$", "°", "phi_deg"))
        lines.append(mrow("$\\psi$", "°", "psi_deg"))
        lines.append(mrow("$R_{inter}$", "---", "Rinter"))
        lines.append(mrow("$\\nu_{ur}$", "---", "nu_ur"))
    lines.append("")

    # === SECTION 5: GROUND TRUTH ===
    lines.append("## 5. KIỂM CHỨNG GROUND TRUTH (v2.3)")
    lines.append("")
    lines.append("| Lớp | Loại đất | $N_{SPT}$ | $E_{50}^{calc}$ | Công thức | $E_{50}^{GT}$ | Deviance |")
    lines.append("|:---:|:---|:---:|:---:|:---|:---:|:---:|")
    for layer in layers:
        gt = layer.get("Ground_Truth_Check", {})
        gt_ref = gt.get("ground_truth_reference", {})
        e50 = layer.get("E50_ref_kpa", '')
        e50gt = gt_ref.get("parameters", {}).get("E50_ref_kpa", '') if gt_ref else ''
        dev = ""
        if e50 and e50gt:
            try: dev = f"{abs(float(e50)-float(e50gt))/float(e50gt)*100:.1f}%"
            except: dev = "N/A"
        status_icon = "⚠️" if "WARNING" in gt.get("status", "") else "✓"
        lines.append(
            f"| {layer.get('layer_id','')} | {layer.get('description','')[:20]} | "
            f"{layer.get('spt_input','')} | {e50} | "
            f"{'Ke×Su' if layer.get('Ke_data') else 'α×N'} | {e50gt} | {status_icon} {dev} |"
        )
    lines.append("")

    # === SECTION 6: BASE HEAVE ===
    bh = data.get("base_heave_check", {})
    if bh and not bh.get("error"):
        lines.append("## 6. KIỂM TRA ỔN ĐỊNH ĐÁY HỐ ĐÀO (Base Heave)")
        lines.append("")
        ex = bh.get("excavation_data", {})
        lines.append(f"- Kích thước hố đào: $B \\times L = {ex.get('B_m','')} \\times {ex.get('L_m','')}$ m")
        lines.append(f"- Chiều sâu đào: $H = {ex.get('H_exc_m','')}$ m")
        lines.append(f"- $N_c = {bh.get('Nc','')}$")
        lines.append(f"- $\\gamma_{{avg}} = {bh.get('gamma_avg_kNm3','')}$ kN/m³")
        lines.append(f"- $S_u = {ex.get('Su_kpa','')}$ kPa")
        lines.append(f"- $F_s = {bh.get('Fs','')}$ (cho phép ≥ 1.50)")
        lines.append(f"- $\\eta = {bh.get('eta','')}$ — **{bh.get('status','')}**")
        if bh.get("recommendations"):
            lines.append("")
            lines.append("**Khuyến nghị:**")
            for rec in bh["recommendations"]:
                lines.append(f"- [{rec.get('priority','')}] {rec.get('action','')}: {rec.get('detail','')}")
        lines.append("")

    # === SECTION 7: SLS ===
    if data.get("sls_checks"):
        lines.append("## 7. KIỂM CHỨNG TRẠNG THÁI GIỚI HẠN SỬ DỤNG (SLS)")
        lines.append("")
        lines.append("| # | Tiêu chí | Tính toán | Cho phép | $\\eta$ | Kết luận | Tiêu chuẩn |")
        lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---|")
        for i, check in enumerate(data.get("sls_checks", []), 1):
            eta = check.get('eta', '')
            status = check.get('status', '')
            if status in ('PASSED', 'ĐẠT'):
                status_d = '🟢 ĐẠT'
            elif status in ('FAILED', 'KHÔNG ĐẠT'):
                status_d = '🔴 KHÔNG ĐẠT'
            elif 'Lưu ý' in status:
                status_d = '🟠 Lưu ý'
            else:
                status_d = status
            try:
                ev = float(eta)
                if ev <= 0.70: ed = f'🟢 **{ev:.2f}**'
                elif ev <= 0.90: ed = f'🟡 **{ev:.2f}**'
                elif ev <= 1.00: ed = f'🟠 **{ev:.2f}**'
                else: ed = f'🔴 **{ev:.2f}**'
            except: ed = f'**{eta}**'
            lines.append(
                f"| {i} | {check.get('name','')} | {check.get('calculated','')} | "
                f"{check.get('allowable','')} | {ed} | {status_d} | {check.get('standard','')} |"
            )
        lines.append("")

    # === DISCLAIMER ===
    lines.append("---")
    lines.append("> *Tài liệu do SKILL_GEOTECH v2.3 lập tự động. Kết quả tính toán mang tính tham khảo; kỹ sư có CCHN phải rà soát và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*")
    lines.append("")
    lines.append("## BẢNG PHÂN CÔNG & PHÊ DUYỆT")
    lines.append("")
    lines.append("| Vai trò | Thực hiện | Đề xuất | Ký & Ngày |")
    lines.append("|:---|:---|:---|:---|")
    lines.append(f"| Người lập | {author} | Trợ lý AI — cần Kỹ sư CCHN xác nhận | [Ngày] |")
    lines.append("| Kỹ sư kiểm tra | [Kỹ sư CCHN] | Kiểm tra và ký xác nhận | |")
    lines.append("| Chủ nhiệm dự án | [Họ tên] | Phê duyệt | |")

    with open(out_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"-> Generated Markdown: {out_md}")
    return out_md


# ─── CLI ENTRY POINT ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Xuất Thuyết minh & Bảng tính Plaxis v2.3 (Excel 11 sheets + Markdown)"
    )
    parser.add_argument("--input", required=True, help="File JSON input")
    parser.add_argument("--outdir", default=".", help="Thu muc xuat")
    parser.add_argument("--name", default="Bang_Tinh_Plaxis_v230", help="Ten file (khong duoi)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(args.outdir, exist_ok=True)
    base_path = os.path.join(args.outdir, args.name)

    out_xlsx = base_path + ".xlsx"
    out_md = base_path + "_ThuyetMinh.md"

    generate_excel(data, out_xlsx)
    generate_markdown_report(data, out_md)

    print("\n=> Hoan thanh! Cac file da tao:")
    print(f"   1. {out_xlsx}")
    print(f"   2. {out_md}")

if __name__ == "__main__":
    main()
