"""
calc_continuous_beam.py — Continuous Beam Analysis & Design per TCVN 5574:2018
"""

import sys
import math
import json
import argparse
from typing import List, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

CONCRETE_PROPS = {
    "B15": {"Rb": 8.5, "Rbt": 0.75, "Eb": 24000},
    "B20": {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500},
    "B25": {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000},
    "B30": {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500},
    "B35": {"Rb": 19.5, "Rbt": 1.30, "Eb": 34500},
    "B40": {"Rb": 22.0, "Rbt": 1.40, "Eb": 36000},
    "C20/25": {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500},
    "C25/30": {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000},
    "C30/37": {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500},
}

STEEL_PROPS = {
    "CB240-T": {"Rs": 210, "Rsc": 210, "Es": 200000},
    "CB300-T": {"Rs": 260, "Rsc": 260, "Es": 200000},
    "CB300-V": {"Rs": 260, "Rsc": 260, "Es": 200000},
    "CB400-V": {"Rs": 350, "Rsc": 350, "Es": 200000},
    "CB500-V": {"Rs": 435, "Rsc": 435, "Es": 200000},
    "B500B": {"Rs": 435, "Rsc": 435, "Es": 200000},
}


def solve_continuous_beam(
    spans: List[float],
    q_loads: List[float],
    E: float,
    I: float,
) -> Tuple[List[float], List[float], List[float]]:
    n_spans = len(spans)
    if n_spans == 1:
        L = spans[0]
        q = q_loads[0]
        return [0.0, 0.0], [round(q * (L ** 2) / 8.0, 2)], [round(q * L / 2.0, 2)]

    k = n_spans - 1
    A = [[0.0] * k for _ in range(k)]
    B = [0.0] * k

    for i in range(k):
        L_left = spans[i]
        L_right = spans[i + 1]
        q_left = q_loads[i]
        q_right = q_loads[i + 1]

        A[i][i] = 2.0 * (L_left + L_right)
        if i > 0:
            A[i][i - 1] = L_left
        if i < k - 1:
            A[i][i + 1] = L_right
        B[i] = -(q_left * (L_left ** 3) / 4.0 + q_right * (L_right ** 3) / 4.0)

    for i in range(k):
        pivot = A[i][i] if abs(A[i][i]) >= 1e-9 else 1e-9
        for j in range(i, k):
            A[i][j] /= pivot
        B[i] /= pivot
        for row in range(k):
            if row != i and abs(A[row][i]) > 1e-9:
                factor = A[row][i]
                for col in range(i, k):
                    A[row][col] -= factor * A[i][col]
                B[row] -= factor * B[i]

    M_supports = [0.0] + B + [0.0]
    M_spans = []
    V_max_spans = []

    for i in range(n_spans):
        L = spans[i]
        q = q_loads[i]
        M_left = M_supports[i]
        M_right = M_supports[i + 1]

        V_left = q * L / 2.0 + (M_right - M_left) / L
        V_right = q * L - V_left

        if q > 0:
            x0 = V_left / q
            if 0 < x0 < L:
                M_max_span = V_left * x0 - q * (x0 ** 2) / 2.0 + M_left
            else:
                M_max_span = max(M_left, M_right, q * (L ** 2) / 8.0)
        else:
            M_max_span = max(M_left, M_right)

        M_spans.append(round(M_max_span, 2))
        V_max_spans.append(round(max(abs(V_left), abs(V_right)), 2))

    return [round(m, 2) for m in M_supports], M_spans, V_max_spans


def calc_continuous_beam(
    spans: List[float],
    b: float,
    h: float,
    q_dead: float = 12.0,
    q_live: float = 8.0,
    concrete: str = "B25",
    rebar: str = "CB400-V",
    a_cover: float = 35.0,
) -> dict:
    c_props = CONCRETE_PROPS.get(concrete, CONCRETE_PROPS["B25"])
    s_props = STEEL_PROPS.get(rebar, STEEL_PROPS["CB400-V"])

    Rb = c_props["Rb"]
    Rbt = c_props["Rbt"]
    Eb = c_props["Eb"]
    Rs = s_props["Rs"]
    Es = s_props["Es"]

    h0 = h - a_cover
    I_beam = (b * (h ** 3)) / 12.0 * 1e-12
    E_beam = Eb * 1e3

    q_total = q_dead + q_live
    q_loads = [q_total] * len(spans)

    M_supports, M_spans, V_max_spans = solve_continuous_beam(spans, q_loads, E_beam, I_beam)

    omega = 0.8
    epsilon_s_el = Rs / Es
    xi_R = omega / (1.0 + (epsilon_s_el / 0.0035))
    alpha_R = xi_R * (1.0 - 0.5 * xi_R)

    logs = []
    step = 1

    logs.append({
        "Step": step,
        "Description": "Xác định tổ hợp tải trọng tính toán tác dụng lên dầm",
        "Formula": "q_total = q_dead + q_live",
        "Substitution": f"q = {q_dead} + {q_live}",
        "Result": f"{q_total:.2f} kN/m",
        "Citation": {"Ma_TC": "TCVN 2737:2023", "Dieu_Muc": "Điều 5.1", "Bang_Hinh": "", "Trang": "15", "Trich_Yeu": "Tổ hợp tải trọng"},
    })
    step += 1

    logs.append({
        "Step": step,
        "Description": "Giải nội lực dầm liên tục (Three-Moment Equation)",
        "Formula": "M_{i-1} L_i + 2 M_i (L_i + L_{i+1}) + M_{i+1} L_{i+1} = - (q_i L_i^3 + q_{i+1} L_{i+1}^3)/4",
        "Substitution": f"Nhịp: {spans} m, q = {q_total} kN/m",
        "Result": f"M_gối: {M_supports} kNm; M_nhịp: {M_spans} kNm",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 5.2", "Bang_Hinh": "", "Trang": "28", "Trich_Yeu": "Phương trình ba mô men giải dầm liên tục"},
    })
    step += 1

    design_sections = []
    eta_M_list = []

    max_M_support = max([abs(m) for m in M_supports] or [0.0])
    if max_M_support > 0:
        alpha_m_sup = (max_M_support * 1e6) / (Rb * b * (h0 ** 2))
        eta_M_sup = alpha_m_sup / alpha_R
        eta_M_list.append(eta_M_sup)
        zeta_sup = 0.5 * (1.0 + math.sqrt(max(0.0, 1.0 - 2.0 * min(alpha_m_sup, alpha_R))))
        As_sup = (max_M_support * 1e6) / (Rs * zeta_sup * h0)
        design_sections.append({
            "location": "Gối tựa nguy hiểm nhất",
            "M_kNm": round(max_M_support, 2),
            "type": "Mô men âm (cốt thép lớp trên)",
            "alpha_m": round(alpha_m_sup, 3),
            "eta_M": round(eta_M_sup, 3),
            "As_req_mm2": round(As_sup, 1),
            "status": "PASS" if eta_M_sup <= 1.0 else "FAIL",
        })

    max_M_span = max(M_spans)
    alpha_m_span = (max_M_span * 1e6) / (Rb * b * (h0 ** 2))
    eta_M_span = alpha_m_span / alpha_R
    eta_M_list.append(eta_M_span)
    zeta_span = 0.5 * (1.0 + math.sqrt(max(0.0, 1.0 - 2.0 * min(alpha_m_span, alpha_R))))
    As_span = (max_M_span * 1e6) / (Rs * zeta_span * h0)
    design_sections.append({
        "location": "Giữa nhịp nguy hiểm nhất",
        "M_kNm": round(max_M_span, 2),
        "type": "Mô men dương (cốt thép lớp dưới)",
        "alpha_m": round(alpha_m_span, 3),
        "eta_M": round(eta_M_span, 3),
        "As_req_mm2": round(As_span, 1),
        "status": "PASS" if eta_M_span <= 1.0 else "FAIL",
    })

    # [FIX BUG-STR-06a]: Kiểm tra dải bê tông nghiêng theo đúng TCVN 5574:2018 Mục 8.1.3.2 CT (81):
    # Q <= phi_b1 * Rb * b * h0 = 0.3 * Rb * b * h0, đồng thời tính Q_b,max = 2.5 * Rbt * b * h0
    max_V = max(V_max_spans)
    Q_strip_ult = 0.3 * Rb * b * h0 * 1e-3  # kN
    Q_b_max = 2.5 * Rbt * b * h0 * 1e-3     # kN
    Q_b_min = 0.5 * Rbt * b * h0 * 1e-3     # kN
    eta_V = max_V / Q_strip_ult if Q_strip_ult > 0 else 999.0

    logs.append({
        "Step": step,
        "Description": "Tính toán khả năng chịu uốn và diện tích cốt thép yêu cầu",
        "Formula": "alpha_m = M / (Rb * b * h0^2) <= alpha_R, As = M / (Rs * zeta * h0)",
        "Substitution": f"M_span={max_M_span} kNm, alpha_m={alpha_m_span:.3f}, alpha_R={alpha_R:.3f}",
        "Result": f"As_span = {As_span:.1f} mm2, As_gối = {design_sections[0]['As_req_mm2'] if design_sections else 0} mm2",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Mục 8.1.2", "Bang_Hinh": "", "Trang": "62", "Trich_Yeu": "Tính toán cốt thép chịu uốn"},
    })
    step += 1

    logs.append({
        "Step": step,
        "Description": "Kiểm tra khả năng chịu cắt trên dải bê tông nghiêng",
        "Formula": "Q_max <= phi_b1 * Rb * b * h0 = 0.3 * Rb * b * h0",
        "Substitution": f"V_max = {max_V} kN, Q_strip_ult = {Q_strip_ult:.1f} kN (Q_b,min = {Q_b_min:.1f} kN, Q_b,max = {Q_b_max:.1f} kN)",
        "Result": f"eta_V = {eta_V:.3f}",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Mục 8.1.3.2 CT (81)", "Bang_Hinh": "", "Trang": "68", "Trich_Yeu": "Điều kiện bền dải bê tông giữa các vết nứt nghiêng"},
    })

    eta_M_max = max(eta_M_list) if eta_M_list else 0.0
    overall_eta = max(eta_M_max, eta_V)

    return {
        "status": "PASSED" if overall_eta <= 1.0 else "FAILED",
        "element": f"Dầm liên tục {len(spans)} nhịp",
        "geometry": {"spans_m": spans, "b_mm": b, "h_mm": h, "h0_mm": h0},
        "materials": {"concrete": concrete, "rebar": rebar, "Rb_MPa": Rb, "Rbt_MPa": Rbt, "Rs_MPa": Rs},
        "loads": {"q_dead_kNm": q_dead, "q_live_kNm": q_live, "q_total_kNm": q_total},
        "internal_forces": {
            "M_supports_kNm": M_supports,
            "M_spans_kNm": M_spans,
            "V_max_spans_kN": V_max_spans,
        },
        "shear_checks": {
            "V_max_kN": max_V,
            "Q_strip_ult_kN": round(Q_strip_ult, 1),
            "Q_b_min_kN": round(Q_b_min, 1),
            "Q_b_max_kN": round(Q_b_max, 1),
            "stirrups_required": max_V > Q_b_min,
        },
        "critical_sections": design_sections,
        "eta_M": round(eta_M_max, 3),
        "eta_V": round(eta_V, 3),
        "overall_eta": round(overall_eta, 3),
        "Calculation_Logs": logs,
        "Standard_Method": "TCVN 5574:2018",
    }


def main():
    parser = argparse.ArgumentParser(description="calc_continuous_beam")
    parser.add_argument("--spans", nargs="+", type=float, default=[5.0, 6.0, 5.0])
    parser.add_argument("-b", type=float, default=250)
    parser.add_argument("-H", "--height", type=float, default=500)
    parser.add_argument("--qd", type=float, default=12.0)
    parser.add_argument("--ql", type=float, default=8.0)
    parser.add_argument("--concrete", default="B25")
    parser.add_argument("--rebar", default="CB400-V")
    args = parser.parse_args()

    res = calc_continuous_beam(
        spans=args.spans, b=args.b, h=args.height,
        q_dead=args.qd, q_live=args.ql,
        concrete=args.concrete, rebar=args.rebar,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
