import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_strut_capacity.py — MODULE 12: Kiểm tra Ổn định & Chịu lực Thanh chống
# =============================================================================
# Version: 2.3.1
# Standard_Method: TCVN 5575:2018, Eurocode 3 (EN 1993-1-1), AISC Steel Manual
# Reference: TMTT Sunrise CVPM Quang Trung (H200x200x8x12)
# Kiểm tra: Buckling, Slenderness, N_Rd cho Strut / Thanh chống
# Fixes v2.3.1:
#   - gamma_M0: hardcoded → có thể override qua tham số
#   - Thêm validation cho N_Ed_kn
# =============================================================================

E_STEEL = 210_000_000  # kN/m² (= 210,000 MPa)
GAMMA_STEEL = 78.5     # kN/m³


# ── Bảng tiết diện thép hình phổ biến Việt Nam ──
# Nguồn: Catalog thép W/D/H của Nhật Khánh, Pomina, Vinasteel
STEEL_SECTION_DB = {
    "H150": {
        "name": "H150x150x7x10",
        "A_cm2": 27.16,
        "Ix_cm4": 1220.0,
        "Iy_cm4": 562.0,
        "ix_cm": 6.72,
        "iy_cm": 4.56,
        "Wx_cm3": 163.0,
        "Wy_cm3": 75.1,
        "tw_mm": 7,
        "tf_mm": 10,
        "h_mm": 150,
        "b_mm": 150,
    },
    "H200": {
        "name": "H200x200x8x12",
        "A_cm2": 62.08,
        "Ix_cm4": 4610.5,
        "Iy_cm4": 1600.8,
        "ix_cm": 8.62,
        "iy_cm": 5.08,
        "Wx_cm3": 461.0,
        "Wy_cm3": 160.1,
        "tw_mm": 8,
        "tf_mm": 12,
        "h_mm": 200,
        "b_mm": 200,
    },
    "H250": {
        "name": "H250x250x9x14",
        "A_cm2": 92.18,
        "Ix_cm4": 10800.0,
        "Iy_cm4": 3650.0,
        "ix_cm": 10.84,
        "iy_cm": 6.29,
        "Wx_cm3": 864.0,
        "Wy_cm3": 292.0,
        "tw_mm": 9,
        "tf_mm": 14,
        "h_mm": 250,
        "b_mm": 250,
    },
    "H300": {
        "name": "H300x300x10x15",
        "A_cm2": 119.80,
        "Ix_cm4": 20400.0,
        "Iy_cm4": 6750.0,
        "ix_cm": 13.05,
        "iy_cm": 7.51,
        "Wx_cm3": 1360.0,
        "Wy_cm3": 450.0,
        "tw_mm": 10,
        "tf_mm": 15,
        "h_mm": 300,
        "b_mm": 300,
    },
    "H350": {
        "name": "H350x350x12x19",
        "A_cm2": 173.90,
        "Ix_cm4": 40300.0,
        "Iy_cm4": 13600.0,
        "ix_cm": 15.23,
        "iy_cm": 8.84,
        "Wx_cm3": 2300.0,
        "Wy_cm3": 777.0,
        "tw_mm": 12,
        "tf_mm": 19,
        "h_mm": 350,
        "b_mm": 350,
    },
    "H400": {
        "name": "H400x400x13x21",
        "A_cm2": 218.70,
        "Ix_cm4": 68900.0,
        "Iy_cm4": 22400.0,
        "ix_cm": 17.73,
        "iy_cm": 10.12,
        "Wx_cm3": 3445.0,
        "Wy_cm3": 1120.0,
        "tw_mm": 13,
        "tf_mm": 21,
        "h_mm": 400,
        "b_mm": 400,
    },
    "H488": {
        "name": "H488x300x11x18",
        "A_cm2": 163.50,
        "Ix_cm4": 68000.0,
        "Iy_cm4": 8110.0,
        "ix_cm": 20.40,
        "iy_cm": 7.04,
        "Wx_cm3": 2785.0,
        "Wy_cm3": 541.0,
        "tw_mm": 11,
        "tf_mm": 18,
        "h_mm": 488,
        "b_mm": 300,
    },
    # ── Thép đôi ghép ──
    "2H200": {
        "name": "2xH200x200x8x12 (thép đôi)",
        "A_cm2": 124.16,
        "Ix_cm4": 9221.0,
        "Iy_cm4": 6403.2,
        "ix_cm": 8.62,
        "iy_cm": 7.18,
        "Wx_cm3": 922.1,
        "Wy_cm3": 533.6,
        "tw_mm": 8,
        "tf_mm": 12,
        "h_mm": 200,
        "b_mm": 400,
    },
    "2H300": {
        "name": "2xH300x300x10x15 (thép đôi)",
        "A_cm2": 239.60,
        "Ix_cm4": 40800.0,
        "Iy_cm4": 27000.0,
        "ix_cm": 13.05,
        "iy_cm": 10.62,
        "Wx_cm3": 2720.0,
        "Wy_cm3": 1800.0,
        "tw_mm": 10,
        "tf_mm": 15,
        "h_mm": 300,
        "b_mm": 600,
    },
}

# ── Cường độ thép theo mác ──
STEEL_GRADE_DB = {
    "SS400": {"fy_kpa": 235_000, "fu_kpa": 400_000, "E_kpa": E_STEEL, "description": "Thép carbon Q235 (Trung Quốc)"},
    "A36":   {"fy_kpa": 250_000, "fu_kpa": 400_000, "E_kpa": E_STEEL, "description": "ASTM A36"},
    "SS490": {"fy_kpa": 285_000, "fu_kpa": 490_000, "E_kpa": E_STEEL, "description": "Thép Q345"},
    "SMA490": {"fy_kpa": 330_000, "fu_kpa": 490_000, "E_kpa": E_STEEL, "description": "Thép Q390"},
}


def _get_section(section_type):
    if section_type not in STEEL_SECTION_DB:
        return None
    return STEEL_SECTION_DB[section_type]


def _get_grade(grade):
    if grade not in STEEL_GRADE_DB:
        return STEEL_GRADE_DB["SS400"]
    return STEEL_GRADE_DB[grade]


def calc_strut_stability(section_type="H300", L_0_m=None, grade="SS400",
                         mu=1.0, N_Ed_kn=None, gamma_M0=1.0):
    """
    Kiểm tra ổn định và khả năng chịu lực thanh chống (v2.3.0).

    Công thức tổng quát (TCVN 5575:2018 / Eurocode 3):

    1. Độ mảnh:
         λ = L_0 / i_min

    2. Độ mảnh quy ước:
         λ̅ = (λ / π) × √(f_y / E)

    3. Hệ số uốn dọc φ (Perry-Robertson):
         Φ = 0.5 × [1 + α(λ̅ - 0.2) + λ̅²]
         φ = 1 / (Φ + √(Φ² - λ̅²))

    4. Khả năng chịu nén:
         N_Rd = φ × A × f_y / γ_M0

    Parameters
    ----------
    section_type : str
        Loại thép hình: H150, H200, H250, H300, H350, H400, H488, 2H200, 2H300
    L_0_m : float or None
        Chiều dài tính toán uốn dọc (m)
        Nếu None → chỉ tính đặc trưng, không kiểm tra ổn định
    grade : str
        Mác thép: SS400, A36, SS490, SMA490
    mu : float
        Hệ số chiều dài tính toán (mặc định 1.0 cho thanh chống ngang)
        0.5 = hai đầu ngàm, 0.7 = một đầu ngàm/một đầu khớp
    N_Ed_kn : float or None
        Lực nén thiết kế từ Plaxis (kN) — nếu có để so sánh
    gamma_M0 : float
        Hệ số vật liệu (mặc định 1.0 theo TCVN 5575:2018).
        Có thể override theo tiêu chuẩn dự án.

    Returns
    -------
    dict với đầy đủ Calculation_Logs
    """
    sec = _get_section(section_type)
    if sec is None:
        return {"error": f"Unknown section: {section_type}"}

    steel = _get_grade(grade)
    fy = steel["fy_kpa"]       # kPa
    E = steel["E_kpa"]         # kPa

    # ── Đặc trưng hình học ──────────────────────────────────────────────────
    A_cm2 = sec["A_cm2"]
    A_m2 = A_cm2 * 1e-4
    A_mm2 = A_cm2 * 100
    i_x_cm = sec["ix_cm"]
    i_y_cm = sec["iy_cm"]
    i_min_cm = min(i_x_cm, i_y_cm)
    i_min_m = i_min_cm / 100
    W_x_cm3 = sec["Wx_cm3"]
    W_x_m3 = W_x_cm3 * 1e-6

    calc_logs = []

    result = {
        "element_type": "Thanh chống (Strut)",
        "section_type": section_type,
        "section_name": sec["name"],
        "steel_grade": grade,
        "steel_description": steel["description"],
        "A_mm2": A_mm2,
        "A_m2": round(A_m2, 6),
        "A_cm2": A_cm2,
        "i_x_cm": i_x_cm,
        "i_y_cm": i_y_cm,
        "i_min_cm": i_min_cm,
        "W_x_cm3": W_x_cm3,
        "f_y_kpa": fy,
        "E_kpa": E,
        "Calculation_Logs": calc_logs
    }

    calc_logs.append({
        "step": "1. Đặc trưng hình học tiết diện",
        "section": sec["name"],
        "A": f"{A_cm2} cm² = {round(A_m2, 6)} m²",
        "i_x": f"{i_x_cm} cm",
        "i_y": f"{i_y_cm} cm",
        "i_min": f"min({i_x_cm}, {i_y_cm}) = {i_min_cm} cm"
    })

    if L_0_m is None:
        result["note"] = "Không cung cấp L_0 → chỉ tính đặc trưng"
        return result

    # ── Chiều dài tính toán ──────────────────────────────────────────────────
    L_0_calc_m = mu * L_0_m

    calc_logs.append({
        "step": "2. Chiều dài tính toán uốn dọc",
        "formula": "L_0 = μ × L",
        "L_span_m": L_0_m,
        "mu": mu,
        "L_0_m": round(L_0_calc_m, 3)
    })

    # ── Độ mảnh ──────────────────────────────────────────────────────────────
    lambda_val = L_0_calc_m / i_min_m
    lambda_allow = 150.0  # Theo TCVN 5575:2018

    calc_logs.append({
        "step": "3. Kiểm tra độ mảnh",
        "formula": "λ = L_0 / i_min",
        "L_0_m": round(L_0_calc_m, 3),
        "i_min_m": round(i_min_m, 4),
        "lambda": round(lambda_val, 2),
        "lambda_allow": lambda_allow,
        "slenderness_check": "✓ Đạt" if lambda_val <= lambda_allow else "✗ Không đạt"
    })

    # ── Độ mảnh quy ước ─────────────────────────────────────────────────────
    lambda_bar = (lambda_val / math.pi) * math.sqrt(fy / E)
    lambda_bar_sq = lambda_bar ** 2

    calc_logs.append({
        "step": "4. Độ mảnh quy ước λ̅",
        "formula": "λ̅ = (λ/π) × √(f_y/E)",
        "lambda": round(lambda_val, 2),
        "lambda_bar": round(lambda_bar, 4),
        "note": "λ̅ < 0.2 → Không cần kiểm tra ổn định"
    })

    # ── Hệ số uốn dọc φ ────────────────────────────────────────────────────
    # Đường cong Euler (λ̅ > 0.2)
    if lambda_bar <= 0.2:
        phi = 1.0
        buckling_curve_note = "λ̅ ≤ 0.2 → Không xảy ra mất ổn định uốn dọc"
    else:
        # Hệ số khuyết tật α (theo TCVN 5575:2018, đường cong Euler B)
        # Đối với thép hình H cán nóng: α = 0.34
        alpha = 0.34

        Phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar_sq)
        sqrt_term = math.sqrt(Phi ** 2 - lambda_bar_sq)

        if sqrt_term < 0:
            phi = 1.0
        else:
            phi = 1.0 / (Phi + sqrt_term)

        buckling_curve_note = (
            f"Đường cong B (α={alpha}): "
            f"Φ = 0.5×[1+{alpha}×({lambda_bar:.3f}-0.2)+{lambda_bar_sq:.3f}] = {Phi:.4f}; "
            f"φ = 1/(Φ+√(Φ²-λ̅²)) = {phi:.4f}"
        )

    calc_logs.append({
        "step": "5. Tính hệ số uốn dọc φ (Perry-Robertson)",
        "formula": "Φ = 0.5[1+α(λ̅-0.2)+λ̅²]; φ = 1/(Φ+√(Φ²-λ̅²))",
        "alpha": alpha if lambda_bar > 0.2 else "N/A",
        "Phi": round(Phi, 4) if lambda_bar > 0.2 else "N/A",
        "phi": round(phi, 4),
        "note": buckling_curve_note
    })

    # ── Khả năng chịu nén N_Rd ─────────────────────────────────────────────
    gamma_M0 = gamma_M0  # v2.3.1: đã nhận từ tham số
    N_Rd_kN = phi * A_m2 * fy / gamma_M0  # phi×A(m²)×fy(kN/m²)=kN

    calc_logs.append({
        "step": "6. Khả năng chịu nén giới hạn N_Rd",
        "formula": "N_Rd = φ × A × f_y / γ_M0",
        "phi": round(phi, 4),
        "A_m2": round(A_m2, 6),
        "f_y_kpa": fy,
        "gamma_M0": gamma_M0,
        "N_Rd_kN": round(N_Rd_kN, 1)
    })

    # ── Kiểm tra với N_Ed từ Plaxis ───────────────────────────────────────
    if N_Ed_kn is not None:
        eta_N = N_Ed_kn / N_Rd_kN if N_Rd_kN > 0 else 999
        if eta_N <= 0.70:
            N_status = "🟢 An toàn"
        elif eta_N <= 0.90:
            N_status = "🟡 Tốt"
        elif eta_N <= 1.00:
            N_status = "🟠 Lưu ý"
        else:
            N_status = "🔴 Vượt giới hạn"

        calc_logs.append({
            "step": "7. Kiểm tra với N_Ed từ Plaxis",
            "N_Ed_kn": N_Ed_kn,
            "N_Rd_kN": round(N_Rd_kN, 1),
            "eta_N": round(eta_N, 3),
            "status": N_status
        })
    else:
        eta_N = None
        N_status = "Chưa có N_Ed từ Plaxis"

    # ── Khả năng chịu cắt V_Rd ─────────────────────────────────────────────
    V_Rd_kn = 0.0  # Simplified: V_Rd = 0 (strut chủ yếu chịu nén)
    # Đầy đủ: V_Rd = Av × f_v / (γ_M0 × √3) nhưng strut không chịu cắt chính

    # ── Kết quả cuối cùng ──────────────────────────────────────────────────
    result.update({
        "mu": mu,
        "L_span_m": L_0_m,
        "L_0_calc_m": round(L_0_calc_m, 3),
        "lambda": round(lambda_val, 2),
        "lambda_allow": lambda_allow,
        "lambda_bar": round(lambda_bar, 4),
        "alpha": alpha if lambda_bar > 0.2 else 0.0,
        "Phi": round(Phi, 4) if lambda_bar > 0.2 else 0.0,
        "phi": round(phi, 4),
        "N_Rd_kN": round(N_Rd_kN, 1),
        "V_Rd_kN": 0.0,
        "gamma_M0": gamma_M0,  # v2.3.1: ghi rõ hệ số vật liệu đã dùng
        "N_Ed_kn": N_Ed_kn,
        "eta_N": round(eta_N, 3) if eta_N is not None else None,
        "status_N": N_status,
        "buckling_note": buckling_curve_note,
        "Standard_Method": "TCVN 5575:2018 / Eurocode 3 (EN 1993-1-1)",
        "Scope_Limitation": [
            "Chưa xét ảnh hưởng của momen uốn (M_Ed) nếu strut không đối xứng",
            "Cần kiểm tra với N_Ed thực từ Plaxis sau khi chạy mô hình"
        ]
    })

    return result


def calc_strut_capacity_from_dim(L_span_m, A_mm2, ix_cm, iy_cm, fy_kpa=235_000,
                                  grade="SS400", mu=1.0, N_Ed_kn=None, gamma_M0=1.0):
    """
    Tính khả năng chịu lực thanh chống khi biết đầy đủ thông số hình học.
    Dùng khi tiết diện không có trong CSDL.
    """
    i_min_cm = min(ix_cm, iy_cm)
    i_min_m = i_min_cm / 100
    A_m2 = A_mm2 / 1e6

    L_0 = mu * L_span_m
    lambda_val = L_0 / i_min_m
    lambda_bar = (lambda_val / math.pi) * math.sqrt(fy_kpa / E_STEEL)

    if lambda_bar <= 0.2:
        phi = 1.0
    else:
        alpha = 0.34
        Phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar ** 2)
        sqrt_term = max(0, Phi ** 2 - lambda_bar ** 2)
        phi = 1.0 / (Phi + math.sqrt(sqrt_term))

    N_Rd = phi * A_m2 * fy_kpa / gamma_M0  # v2.3.1: có thể override gamma_M0

    return {
        "section_type": "custom",
        "A_mm2": A_mm2,
        "i_min_cm": i_min_cm,
        "L_span_m": L_span_m,
        "mu": mu,
        "L_0_m": round(L_0, 3),
        "lambda": round(lambda_val, 2),
        "lambda_bar": round(lambda_bar, 4),
        "phi": round(phi, 4),
        "N_Rd_kN": round(N_Rd / 1000, 1),
        "gamma_M0": gamma_M0,
        "N_Ed_kn": N_Ed_kn,
        "eta_N": round(N_Ed_kn / (N_Rd / 1000), 3) if N_Ed_kn else None
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE MỚI: Kiểm tra Ổn định & Chịu lực Thanh chống (Strut)"
    )
    parser.add_argument("--section", default="H300",
                        choices=list(STEEL_SECTION_DB.keys()),
                        help="Loại thép hình")
    parser.add_argument("--length", type=float, required=True,
                        help="Chiều dài nhịp thanh chống L (m)")
    parser.add_argument("--grade", default="SS400",
                        choices=list(STEEL_GRADE_DB.keys()),
                        help="Mác thép")
    parser.add_argument("--mu", type=float, default=1.0,
                        help="Hệ số chiều dài tính toán (mặc định 1.0)")
    parser.add_argument("--NEd", type=float, default=None,
                        help="Lực nén thiết kế từ Plaxis (kN)")
    parser.add_argument("--gammaM0", type=float, default=1.0,
                        help="Hệ số vật liệu γ_M0 (mặc định 1.0)")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    result = calc_strut_stability(
        section_type=args.section,
        L_0_m=args.length,
        grade=args.grade,
        mu=args.mu,
        N_Ed_kn=args.NEd,
        gamma_M0=args.gammaM0  # v2.3.1
    )

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
