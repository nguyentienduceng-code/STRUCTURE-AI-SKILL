#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_FORENSIC Bước 3: Back-Calculation
Tính toán ngược từ hiện trạng → tải trọng / ứng suất thực tế.

Hỗ trợ 4 loại back-calculation phổ biến:
1. Từ độ võng → tải phân bố
2. Từ bề rộng vết nứt → ứng suất thép
3. Từ chiều sâu vết nứt → moment
4. Từ biến dạng cột → tải dọc trục
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import json
import argparse
from datetime import datetime


def back_calc_deflection_to_load(delta_mm, L_mm, E_MPa, I_mm4, beam_type="simply_supported"):
    """
    Tính ngược tải trọng từ độ võng đo được.

    Args:
        delta_mm: Độ võng đo được (mm)
        L_mm: Chiều dài nhịp (mm)
        E_MPa: Mô đun đàn hồi (MPa)
        I_mm4: Moment quán tính (mm^4)
        beam_type: simply_supported / fixed_fixed / cantilever / propped
    """
    # Hệ số dạng tải (k)
    coefficients = {
        "simply_supported": {"uniform": 384, "point_center": 48},
        "fixed_fixed":      {"uniform": 384, "point_center": 192},
        "cantilever":       {"uniform": 8,   "point_end": 3},
        "propped":          {"uniform": 185, "point_center": 48}  # Gần đúng
    }

    if beam_type not in coefficients:
        return {"error": f"beam_type không hợp lệ: {beam_type}"}

    # Tải phân bố đều: δ = 5*q*L^4 / (384*E*I)
    q = (delta_mm * coefficients[beam_type]["uniform"] * E_MPa * I_mm4) / (5 * L_mm**4)
    # Đổi sang N/mm = N/m / 1000
    q_N_per_mm = q  # N/mm
    q_kN_per_m = q / 1000  # kN/m

    return {
        "Method": "Deflection_to_Load",
        "Inputs": {
            "delta_mm": delta_mm,
            "L_mm": L_mm,
            "E_MPa": E_MPa,
            "I_mm4": I_mm4,
            "beam_type": beam_type
        },
        "Formula": f"q = (384 × E × I × δ) / (5 × L⁴) cho simply supported",
        "Calculation": f"q = (384 × {E_MPa} × {I_mm4} × {delta_mm}) / (5 × {L_mm}⁴)",
        "Result": {
            "q_N_per_mm": round(q, 4),
            "q_kN_per_m": round(q_kN_per_m, 3)
        },
        "Standard_Method": "TCVN 5574:2018",
        "Calculation_Logs": [
            {
                "Step": 1,
                "Description": "Tính ngược tải trọng từ độ võng đo được",
                "Formula": "q = (384 × E × I × δ) / (5 × L⁴)",
                "Calculation": f"q = (384 × {E_MPa} × {I_mm4} × {delta_mm}) / (5 × {L_mm}⁴)",
                "Result": f"q = {round(q_kN_per_m, 3)} kN/m",
                "Citation": {
                    "code": "TCVN 5574:2018",
                    "clause": "Phụ lục F",
                    "page": "120",
                    "title": "Độ võng cấu kiện chịu uốn"
                }
            }
        ],
        "Citation": {
            "code": "TCVN 5574:2018",
            "year": "2018",
            "article": "Phụ lục F - Độ võng",
            "excerpt": "δ = 5qL⁴/(384EI) cho dầm đơn giản"
        }
    }


def back_calc_crack_to_steel_stress(w_crack_mm, spacing_mm, cover_mm, phi_bar_mm, E_s_MPa=200000):
    """
    Tính ngược ứng suất thép từ bề rộng vết nứt.

    Args:
        w_crack_mm: Bề rộng vết nứt đo được (mm)
        spacing_mm: Khoảng cách vết nứt (mm)
        cover_mm: Lớp bảo vệ (mm)
        phi_bar_mm: Đường kính cốt thép (mm)
        E_s_MPa: Mô đun đàn hồi thép (mặc định 200,000 MPa)
    """
    # Công thức Gergely-Lutz: w = 0.076 * beta * fs * (dc * A)^(1/3) / h1
    # Simplified: w ≈ beta * fs * delta_l / Es
    # delta_l = spacing (khoảng cách vết nứt)

    # Approximation: fs = w * Es / (beta * delta_l)
    beta = 1.0  # Hệ số tiêu chuẩn (1.0 cho đơn giản, 1.2 cho thực tế)
    delta_l = spacing_mm
    fs = (w_crack_mm * E_s_MPa) / (beta * delta_l)

    # So sánh với cường độ thiết kế
    fs_ratio = fs / 400  # CB400V có fy = 400 MPa

    return {
        "Method": "Crack_to_Steel_Stress",
        "Inputs": {
            "w_crack_mm": w_crack_mm,
            "spacing_mm": spacing_mm,
            "cover_mm": cover_mm,
            "phi_bar_mm": phi_bar_mm,
            "E_s_MPa": E_s_MPa
        },
        "Formula": "σs = (w_crack × Es) / (β × spacing)",
        "Calculation": f"σs = ({w_crack_mm} × {E_s_MPa}) / (1.0 × {spacing_mm})",
        "Result": {
            "fs_MPa": round(fs, 1),
            "fs_to_fy_ratio": round(fs_ratio, 3),
            "status": "YIELDING" if fs > 400 else "HIGH" if fs > 320 else "OK"
        },
        "Standard_Method": "TCVN 5574:2018",
        "Calculation_Logs": [
            {
                "Step": 1,
                "Description": "Tính ngược ứng suất thép từ bề rộng vết nứt",
                "Formula": "σs = (w_crack × Es) / (β × spacing)",
                "Calculation": f"σs = ({w_crack_mm} × {E_s_MPa}) / (1.0 × {spacing_mm})",
                "Result": f"σs = {round(fs, 1)} MPa (fs/fy = {round(fs_ratio, 3)})",
                "Citation": {
                    "code": "TCVN 5574:2018",
                    "clause": "Điều 7.4",
                    "page": "85",
                    "title": "Bề rộng vết nứt cấu kiện BTCT"
                }
            }
        ],
        "Citation": {
            "code": "TCVN 5574:2018",
            "year": "2018",
            "article": "Điều 7.4 - Bề rộng vết nứt",
            "excerpt": "w_max = 0.3mm cho cấu kiện BTCT thường"
        }
    }


def back_calc_crack_depth_to_moment(crack_depth_mm, h_mm, b_mm, fck_MPa, fy_MPa, cover_mm, As_mm2):
    """
    Tính ngược moment từ chiều sâu vết nứt (giả định vết nứt uốn).

    Nguyên lý: chiều sâu vết nứt ≈ trục trung hòa → cho biết vị trí trục trung hòa
    → suy ra moment bằng cách cân bằng lực trong tiết diện.
    """
    # Chiều sâu vùng nén: a ≈ crack_depth
    a = crack_depth_mm
    d = h_mm - cover_mm - 12  # Giả sử thép chính giữa, 12mm = nửa đường kính

    # Momen kháng (giản đơn, không xét phi):
    # M_Rd ≈ 0.85 * fck * b * a * (d - a/2)
    M_Rd = 0.85 * fck_MPa * b_mm * a * (d - a / 2) / 1e6  # kN.m

    # Kiểm tra cân bằng cốt thép
    # C = 0.85*fck*b*a
    C = 0.85 * fck_MPa * b_mm * a
    T_capacity = As_mm2 * fy_MPa
    T_ratio = T_capacity / C  # 1.0 = balanced, >1 = thép dư, <1 = BT chảy trước

    return {
        "Method": "Crack_Depth_to_Moment",
        "Inputs": {
            "crack_depth_mm": crack_depth_mm,
            "h_mm": h_mm,
            "b_mm": b_mm,
            "fck_MPa": fck_MPa,
            "fy_MPa": fy_MPa,
            "cover_mm": cover_mm,
            "As_mm2": As_mm2
        },
        "Formula": "M = 0.85 × fck × b × a × (d - a/2)",
        "Calculation": f"M = 0.85 × {fck_MPa} × {b_mm} × {a} × ({d} - {a}/2)",
        "Result": {
            "M_Rd_kNm": round(M_Rd, 2),
            "T_to_C_ratio": round(T_ratio, 3),
            "failure_mode": "DUCTILE" if T_ratio >= 0.8 else "BRITTLE"
        },
        "Standard_Method": "TCVN 5574:2018",
        "Calculation_Logs": [
            {
                "Step": 1,
                "Description": "Tính ngược moment từ chiều sâu vết nứt",
                "Formula": "M = 0.85 × fck × b × a × (d - a/2)",
                "Calculation": f"M = 0.85 × {fck_MPa} × {b_mm} × {a} × ({d} - {a}/2)",
                "Result": f"M = {round(M_Rd, 2)} kN.m",
                "Citation": {
                    "code": "TCVN 5574:2018",
                    "clause": "Điều 7.1",
                    "page": "62",
                    "title": "Momen cực hạn có cốt thép đơn"
                }
            }
        ],
        "Citation": {
            "code": "TCVN 5574:2018",
            "year": "2018",
            "article": "Điều 7.1 - Cấu kiện chịu uốn",
            "excerpt": "Momen cực hạn có cốt thép đơn"
        }
    }


def back_calc_column_deformation(delta_axial_mm, L_mm, E_MPa, A_mm2, P_max_estimated_kg=1000):
    """
    Tính ngược lực dọc từ biến dạng dọc trục của cột.

    Args:
        delta_axial_mm: Biến dạng dọc đo được (mm)
        L_mm: Chiều dài cột (mm)
        E_MPa: Mô đun đàn hồi
        A_mm2: Tiết diện cột
        P_max_estimated_kg: Ước tính tải max để validate (cho cảnh báo)
    """
    epsilon = delta_axial_mm / L_mm
    sigma = E_MPa * epsilon
    P_N = sigma * A_mm2
    P_kN = P_N / 1000

    return {
        "Method": "Column_Axial_Deformation",
        "Inputs": {
            "delta_axial_mm": delta_axial_mm,
            "L_mm": L_mm,
            "E_MPa": E_MPa,
            "A_mm2": A_mm2
        },
        "Formula": "ε = ΔL/L; σ = E×ε; P = σ×A",
        "Calculation": f"ε = {delta_axial_mm}/{L_mm} = {epsilon:.6f}; σ = {sigma:.2f} MPa; P = {P_kN:.1f} kN",
        "Result": {
            "strain": round(epsilon, 6),
            "stress_MPa": round(sigma, 2),
            "P_kN": round(P_kN, 1)
        },
        "Standard_Method": "TCVN 5574:2018",
        "Calculation_Logs": [
            {
                "Step": 1,
                "Description": "Tính ngược lực dọc từ biến dạng dọc trục cột",
                "Formula": "ε = ΔL/L; σ = E×ε; P = σ×A",
                "Calculation": f"ε = {delta_axial_mm}/{L_mm} = {epsilon:.6f}; σ = {sigma:.2f} MPa; P = {P_kN:.1f} kN",
                "Result": f"P = {round(P_kN, 1)} kN",
                "Citation": {
                    "code": "TCVN 5574:2018",
                    "clause": "Điều 6.1.3",
                    "page": "45",
                    "title": "Quan hệ ứng biến - ứng suất cấu kiện chịu nén"
                }
            }
        ],
        "Citation": {
            "code": "TCVN 5574:2018",
            "year": "2018",
            "article": "Điều 6.1.3 - Cấu kiện chịu nén",
            "excerpt": "Quan hệ ứng biến - ứng suất"
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Forensic Back-Calculation")
    parser.add_argument("--method", required=True,
                        choices=["deflection_to_load", "crack_to_steel_stress",
                                 "crack_depth_to_moment", "column_deformation"],
                        help="Phương pháp back-calculation")
    parser.add_argument("--input", help="JSON file input (chứa các tham số)")
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    # Load input params
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            params = json.load(f)
    else:
        # Demo
        params = {
            "delta_mm": 25, "L_mm": 6000, "E_MPa": 30000, "I_mm4": 1.4e9,
            "beam_type": "simply_supported"
        }

    if args.method == "deflection_to_load":
        result = back_calc_deflection_to_load(**params)
    elif args.method == "crack_to_steel_stress":
        result = back_calc_crack_to_steel_stress(**params)
    elif args.method == "crack_depth_to_moment":
        result = back_calc_crack_depth_to_moment(**params)
    elif args.method == "column_deformation":
        result = back_calc_column_deformation(**params)

    result["Generated_At"] = datetime.now().isoformat()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
