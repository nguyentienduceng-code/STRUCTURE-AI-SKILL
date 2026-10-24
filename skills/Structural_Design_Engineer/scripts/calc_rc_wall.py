import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_rc_wall.py — Tính toán vách cứng BTCT chịu nén lệch tâm và kiểm tra cắt
# =============================================================================
# Phiên bản: TCVN 5574:2018 (Mục 8.1.2, 8.1.3)
# =============================================================================

RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
RSC_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 400}
RSW_MAP = {"CB240-T": 170, "CB300-V": 210, "CB400-V": 280, "CB500-V": 300}
EB_MAP = {"B15": 24000, "B20": 27500, "B25": 30000, "B30": 32500, "B35": 34500, "B40": 36000}

WALL_THICKNESS_MIN = 100
WALL_LW_BW_MIN = 4.0  # Chiều dài mặt cắt vách lw / bw >= 4 thì là vách, < 4 thì tính như cột
WALL_REINFORCEMENT_MIN = 0.0015
WALL_REINFORCEMENT_MAX = 0.04
SLENDERNESS_LIMIT = 30
SLENDERNESS_TRANSITION = 20


def _slenderness_factor(L0, h_buckling, b_width, N_ed, concrete="B25"):
    """
    [FIX BUG-STR-03a]: Hệ số uốn dọc η theo TCVN 5574:2018 Mục 8.1.2.4.2 CT (29):
      η = 1 / (1 - N / N_cr) >= 1.0  (KHUẾCH ĐẠI mô men bậc 2, tuyệt đối KHÔNG phải < 1.0 làm giảm mô men!)
    Khi độ mảnh λ = L0 / h_buckling <= 14 (tiết diện chữ nhật): η = 1.0.
    Khi λ > 14: tính N_cr = π² * D / L0² với độ cứng quy đổi D ≈ 0.15 * Eb * I_b (kể đến từ biến và nứt).
    """
    lam = L0 / h_buckling if h_buckling > 0 else 0.0
    if lam <= 14.0 or N_ed <= 0:
        return 1.0, lam, None

    Eb = EB_MAP.get(concrete, 30000)  # MPa = N/mm²
    I_b = (b_width * (h_buckling ** 3)) / 12.0  # mm⁴
    # Độ cứng chống uốn hiệu dụng theo TCVN 5574:2018 Mục 8.1.2.4.3 (xấp xỉ an toàn D = 0.18 * Eb * I_b)
    D_eff = 0.18 * Eb * I_b  # N.mm²
    N_cr_kN = (math.pi ** 2 * D_eff / (L0 ** 2)) * 1e-3 if L0 > 0 else 1e9

    if N_ed >= 0.95 * N_cr_kN:
        eta = 5.0  # Mất ổn định uốn dọc
    else:
        eta = 1.0 / (1.0 - N_ed / N_cr_kN)
    return round(max(1.0, eta), 3), lam, round(N_cr_kN, 1)


def calc_rc_wall(bw=200, hw=3000, tw=None,
                 a=30, a_prime=30,
                 concrete="B25", rebar="CB400-V",
                 stirrup_grade="CB240-T",
                 N_ed=500, M_ed=200, V_ed=0.0,
                 L0=3000,
                 bending_plane="in_plane",  # "in_plane" (uốn trong mặt phẳng vách h=hw, b=bw) hoặc "out_of_plane" (uốn ngoài mặt phẳng h=bw, b=hw)
                 As_total=None,
                 stirrup_dia=None,
                 stirrup_spacing=None,
                 stirrup_legs=None):
    """
    Kiểm tra vách cứng BTCT chịu nén lệch tâm phẳng và lực cắt theo TCVN 5574:2018.
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)
    Rs = RS_MAP.get(rebar, 350)
    Rsc = RSC_MAP.get(rebar, 350)
    Rsw = RSW_MAP.get(stirrup_grade, 170)
    Eb = EB_MAP.get(concrete, 30000)

    # [FIX BUG-STR-03b]: Phân biệt rõ kích thước tiết diện theo mặt phẳng uốn
    # Với vách cứng chịu tải ngang trong mặt phẳng (in_plane): bề rộng b = bw (bề dày vách), chiều cao tiết diện h = hw (chiều dài vách).
    # Tuy nhiên uốn dọc ngoài mặt phẳng (out-of-plane buckling) luôn kiểm tra theo phương mảnh nhất bw!
    if bending_plane == "out_of_plane":
        b = hw
        h = bw
    else:
        b = bw
        h = hw

    h0 = h - a
    logs = []
    unverified = []
    warnings = []

    # 1. KIỂM TRA HÌNH DẠNG VÁCH
    ratio_hw_bw = hw / bw if bw > 0 else 0
    if bw < WALL_THICKNESS_MIN:
        warnings.append(f"Bề dày vách bw = {bw} mm < {WALL_THICKNESS_MIN} mm.")
    if ratio_hw_bw < WALL_LW_BW_MIN:
        warnings.append(f"Tỷ lệ hw/bw = {ratio_hw_bw:.2f} < {WALL_LW_BW_MIN}: cấu kiện làm việc như cột.")

    logs.append({
        "Step": 1,
        "Description": "Kiểm tra kích thước hình học vách cứng",
        "Principle": "Vách cứng có tỷ số chiều dài / bề dày mặt cắt hw/bw >= 4, bề dày bw >= 100 mm.",
        "Formula": "bw >= 100 mm; hw/bw >= 4.0",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Điều 8.1.2.4",
            "Bang_Hinh": "",
            "Trang": "65",
            "Trich_Yeu": "Kích thước hình học tiết diện vách BTCT"
        },
        "Substitution": f"bw = {bw} mm, hw = {hw} mm, hw/bw = {ratio_hw_bw:.2f}, mặt phẳng uốn: {bending_plane} (b={b}mm, h={h}mm)",
        "Result": f"bw={bw} mm, hw={hw} mm, h0={h0} mm"
    })

    # 2. XÉT UỐN DỌC (SLENDERNESS AMPLIFICATION η >= 1.0)
    # Độ mảnh ngoài mặt phẳng tính theo bề dày bw; độ mảnh trong mặt phẳng tính theo h
    h_buckling = bw
    b_buckling = hw
    eta_slenderness, lam, N_cr_kN = _slenderness_factor(L0, h_buckling, b_buckling, N_ed, concrete)

    if lam > SLENDERNESS_LIMIT:
        warnings.append(f"Độ mảnh ngoài mặt phẳng λ = L0/bw = {lam:.2f} > {SLENDERNESS_LIMIT}: cần tăng bề dày vách bw hoặc giảm L0.")

    e_a = max(L0 / 600.0, h / 30.0, 10.0)
    e0 = (M_ed * 1e6) / (N_ed * 1e3) if N_ed > 0 else 0.0
    e_initial = e0 + e_a
    # Mô men tính toán đã khuếch đại do uốn dọc: M_ed_calc = M_ed * eta_slenderness
    M_ed_calc = M_ed * eta_slenderness
    e = e_initial * eta_slenderness

    logs.append({
        "Step": 2,
        "Description": "Xét uốn dọc (Slenderness P-Delta Amplification)",
        "Principle": "Uốn dọc bậc 2 làm TĂNG độ lệch tâm và mô men uốn theo hệ số η = 1 / (1 - N/N_cr) >= 1.0.",
        "Formula": "λ = L0/bw; η = 1 / (1 - N_ed / N_cr) >= 1.0; M_ed,calc = η * M_ed",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.2.4.2 CT (29)",
            "Bang_Hinh": "",
            "Trang": "65",
            "Trich_Yeu": "Hệ số kể đến ảnh hưởng uốn dọc η >= 1.0 của cấu kiện chịu nén"
        },
        "Substitution": f"L0 = {L0} mm, bw = {bw} mm -> λ = {lam:.2f}, N_cr = {N_cr_kN} kN, N_ed = {N_ed} kN",
        "Result": f"η = {eta_slenderness:.3f} (>= 1.0), M_ed,calc = {M_ed_calc:.2f} kNm"
    })

    logs.append({
        "Step": 3,
        "Description": "Độ lệch tâm tĩnh học và ngẫu nhiên (e0, ea, e)",
        "Principle": "Độ lệch tâm tính toán gồm lệch tâm tĩnh học e0 và lệch tâm ngẫu nhiên ea nhân với η.",
        "Formula": "e0 = M_ed/N_ed; ea = max(L0/600, h/30, 10); e = η * (e0 + ea)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.2.2",
            "Bang_Hinh": "",
            "Trang": "55",
            "Trich_Yeu": "Độ lệch tâm ngẫu nhiên ea của cấu kiện chịu nén"
        },
        "Substitution": f"M_ed = {M_ed} kNm, N_ed = {N_ed} kN -> e0 = {e0:.1f} mm, ea = {e_a:.1f} mm, η = {eta_slenderness:.3f}",
        "Result": f"e = {e:.1f} mm"
    })

    # 4. HÀM LƯỢNG CỐT THÉP DỌC
    area_bh0 = b * h0
    if As_total is None:
        alpha_n_tmp = (N_ed * 1e3) / (Rb * area_bh0) if (Rb * area_bh0) > 0 else 0
        mu_est = 0.003 if alpha_n_tmp < 0.5 else 0.005
        As_total = mu_est * area_bh0
        warnings.append(f"Chưa nhập As_total: tạm lấy As_total = {As_total:.1f} mm² (μ = {mu_est*100:.2f}%).")
        unverified.append("As_total chưa được nhập tường minh.")

    mu_total = As_total / area_bh0 if area_bh0 > 0 else 0.0
    mu_min = WALL_REINFORCEMENT_MIN
    mu_max = WALL_REINFORCEMENT_MAX
    mu_check = "OK"
    if mu_total < mu_min:
        mu_check = "DUOI TOI THIEU"
        warnings.append(f"Hàm lượng cốt thép dọc μ = {mu_total*100:.2f}% < μ_min = {mu_min*100:.2f}%.")
    elif mu_total > mu_max:
        mu_check = "VUOT TOI DA"
        warnings.append(f"Hàm lượng cốt thép dọc μ = {mu_total*100:.2f}% > μ_max = {mu_max*100:.2f}%.")

    logs.append({
        "Step": 4,
        "Description": "Kiểm tra hàm lượng cốt thép dọc của vách",
        "Formula": "μ = As_total / (b * h0), 0.15% <= μ <= 4.0%",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.3",
            "Bang_Hinh": "",
            "Trang": "135",
            "Trich_Yeu": "Hàm lượng cốt thép dọc tối thiểu và tối đa"
        },
        "Substitution": f"As_total = {As_total:.1f} mm², b = {b} mm, h0 = {h0} mm",
        "Result": f"μ = {mu_total*100:.2f}% ({mu_check})"
    })

    # 5. KIỂM TRA KHẢ NĂNG CHỊU NÉN UỐN (N_ed, M_ed_calc)
    alpha_n = (N_ed * 1e3) / (Rb * area_bh0) if (Rb * area_bh0) > 0 else 0.0
    alpha_R_max = 0.55
    eta_compress = alpha_n / alpha_R_max

    # Khả năng chịu mô men của tiết diện vách đối xứng (As_edge ≈ 0.5 * As_total)
    x_comp = (N_ed * 1e3) / (Rb * b) if (Rb * b) > 0 else 0.0
    x_eff = min(x_comp, 0.55 * h0)
    M_cap_Nmm = Rb * b * x_eff * (h0 - 0.5 * x_eff) + 0.5 * As_total * Rs * (h0 - a_prime)
    M_cap_kNm = M_cap_Nmm * 1e-6
    eta_flexure = M_ed_calc / M_cap_kNm if M_cap_kNm > 0 else 999.0

    logs.append({
        "Step": 5,
        "Description": "Kiểm tra khả năng chịu nén lệch tâm phẳng (N_ed, M_ed,calc)",
        "Formula": "α_n = N_ed / (Rb*b*h0) <= α_R; M_ed,calc <= M_Rd = Rb*b*x*(h0 - 0.5*x) + 0.5*As*Rs*(h0 - a')",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.2.3",
            "Bang_Hinh": "",
            "Trang": "58",
            "Trich_Yeu": "Tính toán cấu kiện chịu nén lệch tâm tiết diện chữ nhật"
        },
        "Substitution": f"N_ed={N_ed} kN -> α_n={alpha_n:.3f}; M_ed,calc={M_ed_calc:.1f} kNm vs M_Rd={M_cap_kNm:.1f} kNm",
        "Result": f"η_nén = {eta_compress:.3f}, η_uốn = {eta_flexure:.3f}",
        "Utilization": f"max(η_nén, η_uốn) = {max(eta_compress, eta_flexure):.3f}"
    })

    # 6. KIỂM TRA CẮT
    Qb = 0.5 * Rbt * bw * (hw - a) * 1e-3  # Sức kháng cắt trong mặt phẳng vách (bw * hw0)
    Q_max_strip = 0.3 * Rb * bw * (hw - a) * 1e-3
    eta_shear = V_ed / Qb if (Qb > 0 and V_ed > 0) else 0.0

    logs.append({
        "Step": 6,
        "Description": "Kiểm tra khả năng chịu cắt của vách (Qb)",
        "Formula": "Qb,min = 0.5 * Rbt * bw * h0w; Q_max = 0.3 * Rb * bw * h0w",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.3",
            "Bang_Hinh": "",
            "Trang": "69",
            "Trich_Yeu": "Khả năng chịu cắt của bê tông"
        },
        "Substitution": f"Rbt = {Rbt} MPa, bw = {bw} mm, h0w = {hw - a} mm, V_ed = {V_ed} kN",
        "Result": f"Qb = {Qb:.1f} kN, Q_max = {Q_max_strip:.1f} kN, η_cắt = {eta_shear:.3f}"
    })

    # [FIX BUG-STR-03b]: Tách hệ số khuếch đại uốn dọc η >= 1.0 khỏi hệ số sử dụng (utilization ratio)
    eta_slenderness_ratio = lam / SLENDERNESS_LIMIT
    etas = [eta_compress, eta_flexure, eta_shear, eta_slenderness_ratio]
    if mu_check != "OK":
        etas.append(1.2)

    overall = max(etas)

    if overall > 1.0 or mu_check != "OK" or lam > SLENDERNESS_LIMIT:
        status = "FAILED"
    else:
        status = "PASSED"

    if overall <= 0.70:
        rating = "GREEN"
    elif overall <= 0.90:
        rating = "YELLOW"
    elif overall <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    return {
        "bw_mm": bw,
        "hw_mm": hw,
        "tw_mm": tw if tw is not None else bw,
        "bending_plane": bending_plane,
        "h_mm": h,
        "h0_mm": h0,
        "b_mm": b,
        "concrete": concrete,
        "rebar": rebar,
        "stirrup_grade": stirrup_grade,
        "Rb_MPa": Rb,
        "Rbt_MPa": Rbt,
        "Rs_MPa": Rs,
        "Eb_MPa": Eb,
        "N_ed_kN": N_ed,
        "M_ed_kNm": M_ed,
        "V_ed_kN": V_ed,
        "L0_mm": L0,
        "lambda": round(lam, 2),
        "N_cr_kN": N_cr_kN,
        "eta_slenderness": round(eta_slenderness, 3),
        "eta_slenderness_ratio": round(eta_slenderness_ratio, 3),
        "M_ed_calc_kNm": round(M_ed_calc, 2),
        "M_Rd_kNm": round(M_cap_kNm, 2),
        "e0_mm": round(e0, 2),
        "ea_mm": round(e_a, 2),
        "e_mm": round(e, 2),
        "As_total_mm2": round(As_total, 1),
        "mu_percent": round(mu_total * 100, 2),
        "mu_check": mu_check,
        "alpha_n": round(alpha_n, 4),
        "alpha_R_max": alpha_R_max,
        "eta_compress": round(eta_compress, 3),
        "eta_flexure": round(eta_flexure, 3),
        "eta_shear": round(eta_shear, 3),
        "Qb_kN": round(Qb, 2),
        "Q_max_strip_kN": round(Q_max_strip, 2),
        "ratio_hw_bw": round(ratio_hw_bw, 2),
        "overall_eta": round(overall, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": (
            "Vách cứng BTCT tiết diện chữ nhật, nén lệch tâm phẳng. "
            "CHƯA kiểm tra: vách có lỗ mở, dầm nối coupling beam, vách chịu xoắn."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_rc_wall(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_rc_wall(
            bw=200, hw=3000,
            a=30, a_prime=30,
            concrete="B25", rebar="CB400-V",
            N_ed=1500, M_ed=600, V_ed=180, L0=3000,
            As_total=3000
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
