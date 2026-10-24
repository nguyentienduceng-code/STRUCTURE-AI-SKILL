"""
calc_isolated_footing.py — Isolated Footing Analysis & Design per TCVN 5574:2018
=================================================================================
Sprint 5 · Pillar 3

Mục đích:
    Tính toán kiểm tra móng đơn bê tông cốt thép nông:
    1. Kiểm tra áp lực đất dưới đáy móng (P_tb <= R_tc, P_max <= 1.2 R_tc, P_min >= 0)
    2. Kiểm tra khả năng chống đâm thủng của bê tông đài móng (TCVN 5574:2018 Điều 8.1.33)
    3. Tính toán diện tích cốt thép đáy móng chịu uốn hai phương Asx, Asy

Tiêu chuẩn:
    - Tải trọng & Tổ hợp: TCVN 2737:2023
    - Nền móng nhà và công trình: TCVN 9362:2012 / TCVN 10304:2014
    - Kết cấu Bê tông cốt thép: TCVN 5574:2018
"""

import sys
import os
import math
import json
import argparse
from typing import Dict, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Bảng cường độ bê tông TCVN 5574:2018 Bảng 6, 7 (MPa)
CONCRETE_PROPS = {
    "B15": {"Rb": 8.5,  "Rbt": 0.75, "Eb": 23000},
    "B20": {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500},
    "B25": {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000},
    "B30": {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500},
    "C20/25": {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500},
    "C25/30": {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000},
}

# Bảng cường độ thép TCVN 5574:2018 Bảng 13 (MPa)
STEEL_PROPS = {
    "CB240-T": {"Rs": 210, "Rsc": 210, "Es": 200000},
    "CB300-T": {"Rs": 260, "Rsc": 260, "Es": 200000},
    "CB300-V": {"Rs": 260, "Rsc": 260, "Es": 200000},
    "CB400-V": {"Rs": 350, "Rsc": 350, "Es": 200000},
    "CB500-V": {"Rs": 435, "Rsc": 435, "Es": 200000},
}


def calc_isolated_footing(
    B: float = 2.0,
    L: float = 2.4,
    H: float = 0.6,
    Df: float = 1.5,
    b_col: float = 0.3,
    h_col: float = 0.4,
    N_tc: float = 600.0,
    M_tc: float = 60.0,
    V_tc: float = 15.0,
    N_tt: Optional[float] = None,
    M_tt: Optional[float] = None,
    V_tt: Optional[float] = None,
    R_tc: float = 200.0,
    gamma_tb: float = 20.0,
    concrete: str = "B20",
    rebar: str = "CB300-V",
    a_cover: float = 0.05,
) -> dict:
    """
    Thẩm tra & thiết kế móng đơn BTCT.
    Đơn vị: kích thước (m), tải trọng (kN, kNm), ứng suất (kPa = kN/m2).
    """
    if N_tt is None:
        N_tt = N_tc * 1.15
    if M_tt is None:
        M_tt = M_tc * 1.15
    if V_tt is None:
        V_tt = V_tc * 1.15

    c_props = CONCRETE_PROPS.get(concrete, CONCRETE_PROPS["B20"])
    s_props = STEEL_PROPS.get(rebar, STEEL_PROPS["CB300-V"])

    Rb = c_props["Rb"]       # MPa
    Rbt = c_props["Rbt"]     # MPa
    Rs = s_props["Rs"]       # MPa

    h0 = H - a_cover         # m

    logs = []
    step = 1

    # 1. Trọng lượng bản thân móng và đất phủ
    G_tc = gamma_tb * B * L * Df
    N_tc_sum = N_tc + G_tc
    M_tc_sum = M_tc + V_tc * H

    e = M_tc_sum / N_tc_sum
    W = (B * (L ** 2)) / 6.0
    F_area = B * L

    P_tb = N_tc_sum / F_area
    delta_P = M_tc_sum / W

    if e <= L / 6.0:
        P_max = P_tb + delta_P
        P_min = P_tb - delta_P
    else:
        # Biểu đồ ứng suất tam giác (tách mép)
        P_max = (2.0 * N_tc_sum) / (3.0 * B * (L / 2.0 - e))
        P_min = 0.0

    eta_P_tb = P_tb / R_tc
    eta_P_max = P_max / (1.2 * R_tc)
    passed_soil = (eta_P_tb <= 1.0) and (eta_P_max <= 1.0) and (P_min >= 0.0)

    logs.append({
        "Step": step,
        "Description": "Kiểm tra áp lực đất dưới đáy móng (TCVN 9362:2012)",
        "Formula": "P_tb = N_tc_sum / (B*L) <= R_tc, P_max <= 1.2 * R_tc, P_min >= 0",
        "Substitution": f"N_tc_sum={N_tc_sum:.1f} kN, P_tb={P_tb:.1f} kPa, P_max={P_max:.1f} kPa, R_tc={R_tc} kPa",
        "Result": f"eta_P_tb = {eta_P_tb:.3f}, eta_P_max = {eta_P_max:.3f}, P_min = {P_min:.1f} kPa",
        "Citation": {
            "Ma_TC": "TCVN 9362:2012",
            "Dieu_Muc": "Điều 4.6.1",
            "Bang_Hinh": "",
            "Trang": "32",
            "Trich_Yeu": "Kiểm tra áp lực đất dưới đáy móng"
        },
    })
    step += 1

    # 2. Kiểm tra đâm thủng móng (TCVN 5574:2018 Điều 8.1.33)
    # Tháp đâm thủng đáy nghiêng 45 độ
    b_t = b_col + 2.0 * h0
    h_t = h_col + 2.0 * h0

    # Nếu đáy tháp vượt quá kích thước móng thì giới hạn bằng kích thước móng
    b_t_eff = min(b_t, B)
    h_t_eff = min(h_t, L)

    u_tb = 2.0 * (b_col + h_col + 2.0 * h0)  # chu vi trung bình tháp đâm thủng
    P_tt_tb = N_tt / F_area

    # Lực đâm thủng tính toán: F_punch = N_tt - diện tích đáy tháp * P_tt_tb
    F_punch = N_tt - P_tt_tb * (b_t_eff * h_t_eff)
    F_punch = max(0.0, F_punch)

    # Khả năng chống đâm thủng của bê tông F_bu = 0.75 * Rbt * h0 * u_tb (kN)
    # Rbt (MPa = 1e3 kPa), h0 (m), u_tb (m) -> kN
    F_bu = 0.75 * (Rbt * 1e3) * h0 * u_tb
    eta_punch = F_punch / F_bu if F_bu > 0 else 0.0
    passed_punch = eta_punch <= 1.0

    logs.append({
        "Step": step,
        "Description": "Kiểm tra chống đâm thủng của bê tông đài móng",
        "Formula": "F_punch = N_tt - P_tt_tb * b_t * h_t <= F_bu = 0.75 * Rbt * h0 * u_tb",
        "Substitution": f"F_punch={F_punch:.1f} kN, F_bu={F_bu:.1f} kN, u_tb={u_tb:.2f} m, h0={h0:.2f} m",
        "Result": f"eta_punch = {eta_punch:.3f} ({'ĐẠT' if passed_punch else 'KHÔNG ĐẠT'})",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Điều 8.1.33",
            "Bang_Hinh": "",
            "Trang": "82",
            "Trich_Yeu": "Kiểm tra chống đâm thủng của bê tông đài móng"
        },
    })
    step += 1

    # 3. Tính toán cốt thép đáy móng chịu uốn (TCVN 5574:2018)
    # Mặt cắt I-I tại mép cột theo phương L:
    # Nhịp chìa: c_L = (L - h_col) / 2
    c_L = (L - h_col) / 2.0
    c_B = (B - b_col) / 2.0

    P_tt_max = (N_tt + gamma_tb * 1.15 * B * L * Df) / F_area + (M_tt + V_tt * H) / W
    P_tt_tb_tot = (N_tt + gamma_tb * 1.15 * B * L * Df) / F_area

    # Áp lực ròng tác dụng lên cánh móng (trừ tải bản thân)
    p_net = N_tt / F_area

    # Mô men tại mép cột theo phương L:
    M_I = (p_net * (c_L ** 2) / 2.0) * B       # kNm
    # Mô men tại mép cột theo phương B:
    M_II = (p_net * (c_B ** 2) / 2.0) * L      # kNm

    # Diện tích cốt thép: As = M / (0.9 * h0 * Rs)
    # Rs (MPa = 1e3 kPa)
    As_x = (M_I * 1e6) / (0.9 * (h0 * 1e3) * Rs)  # mm2 (phương L)
    As_y = (M_II * 1e6) / (0.9 * (h0 * 1e3) * Rs) # mm2 (phương B)

    # Hàm lượng tối thiểu mu_min = 0.1%
    As_min_x = 0.001 * (B * 1e3) * (h0 * 1e3)
    As_min_y = 0.001 * (L * 1e3) * (h0 * 1e3)

    As_x_prov = max(As_x, As_min_x)
    As_y_prov = max(As_y, As_min_y)

    logs.append({
        "Step": step,
        "Description": "Tính toán diện tích cốt thép đáy móng chịu uốn hai phương",
        "Formula": "M_I = p_net * c_L^2 / 2 * B; As_x = M_I / (0.9 * h0 * Rs)",
        "Substitution": f"M_I={M_I:.1f} kNm, M_II={M_II:.1f} kNm, h0={h0:.2f} m, Rs={Rs} MPa",
        "Result": f"As_x = {As_x_prov:.1f} mm2 (phương L); As_y = {As_y_prov:.1f} mm2 (phương B)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Điều 8.1.2",
            "Bang_Hinh": "",
            "Trang": "64",
            "Trich_Yeu": "Tính toán diện tích cốt thép đáy móng chịu uốn hai phương"
        },
    })

    overall_eta = max(eta_P_tb, eta_P_max, eta_punch)
    status = "PASSED" if overall_eta <= 1.0 else "FAILED"

    result = {
        "status": status,
        "element": f"Móng đơn BTCT {B}x{L}x{H}m",
        "geometry": {
            "B_m": B, "L_m": L, "H_m": H, "Df_m": Df,
            "b_col_m": b_col, "h_col_m": h_col, "h0_m": round(h0, 3)
        },
        "materials": {
            "concrete": concrete, "rebar": rebar, "Rb_MPa": Rb, "Rbt_MPa": Rbt, "Rs_MPa": Rs
        },
        "soil_pressures": {
            "P_tb_kPa": round(P_tb, 1),
            "P_max_kPa": round(P_max, 1),
            "P_min_kPa": round(P_min, 1),
            "R_tc_kPa": R_tc,
            "eta_P_tb": round(eta_P_tb, 3),
            "eta_P_max": round(eta_P_max, 3),
        },
        "punching_shear": {
            "F_punch_kN": round(F_punch, 1),
            "F_bu_kN": round(F_bu, 1),
            "eta_punch": round(eta_punch, 3),
            "status": "PASS" if passed_punch else "FAIL",
        },
        "reinforcement": {
            "M_x_kNm": round(M_I, 1),
            "M_y_kNm": round(M_II, 1),
            "As_x_req_mm2": round(As_x_prov, 1),
            "As_y_req_mm2": round(As_y_prov, 1),
        },
        "eta_P_tb": round(eta_P_tb, 3),
        "eta_P_max": round(eta_P_max, 3),
        "eta_punch": round(eta_punch, 3),
        "overall_eta": round(overall_eta, 3),
        "Calculation_Logs": logs,
        "Standard_Method": "TCVN 5574:2018 / TCVN 9362:2012",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="calc_isolated_footing — Isolated Footing Calculator (TCVN 5574:2018 / TCVN 9362:2012)")
    parser.add_argument("-B", type=float, default=2.0, help="Bề rộng móng (m)")
    parser.add_argument("-L", type=float, default=2.4, help="Chiều dài móng (m)")
    parser.add_argument("-H", "--height", type=float, default=0.6, help="Chiều cao móng (m)")
    parser.add_argument("--df", type=float, default=1.5, help="Chiều sâu chôn móng (m)")
    parser.add_argument("--bcol", type=float, default=0.3, help="Bề rộng cột (m)")
    parser.add_argument("--hcol", type=float, default=0.4, help="Chiều cao cột (m)")
    parser.add_argument("--ntc", type=float, default=600.0, help="Lực dọc tiêu chuẩn N_tc (kN)")
    parser.add_argument("--mtc", type=float, default=60.0, help="Mô men tiêu chuẩn M_tc (kNm)")
    parser.add_argument("--vtc", type=float, default=15.0, help="Lực ngang tiêu chuẩn V_tc (kN)")
    parser.add_argument("--rtc", type=float, default=200.0, help="Sức chịu tải đất nền R_tc (kPa)")
    parser.add_argument("--concrete", default="B20", help="Cấp độ bền bê tông")
    parser.add_argument("--rebar", default="CB300-V", help="Nhóm cốt thép")
    args = parser.parse_args()

    res = calc_isolated_footing(
        B=args.B, L=args.L, H=args.height, Df=args.df,
        b_col=args.bcol, h_col=args.hcol,
        N_tc=args.ntc, M_tc=args.mtc, V_tc=args.vtc,
        R_tc=args.rtc, concrete=args.concrete, rebar=args.rebar,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
