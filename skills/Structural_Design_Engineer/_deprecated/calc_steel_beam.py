import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# WARNING: SCRIPT NAY DUNG EN 1993-1-1 (EUROCODE 3)
# =============================================================================
# Theo STANDARDS_LOCK.md, hồ sơ mới từ 2026 phải dùng TCVN 5575:2024.
# Script nay duoc SU DUNG CHO:
#   - Hồ sơ cũ (Truoc 2026) can doi chieu EN 1993-1-1
#   - So sanh quoc te (AISC, Eurocode)
# CHO HỒ SƠ MỚI: Dung steel_member_check_v2024.py thay vi script nay
# =============================================================================

# --- Hang so chot theo STANDARDS_LOCK.md muc 3 ---
GAMMA_M0 = 1.05      # He so tin cay vat lieu thep (ben tiet dien) - EN 1993-1-1 Table 3.1
GAMMA_M1 = 1.10      # He so tin cay khi kiem tra on dinh - EN 1993-1-1 Table 3.1
                      # FIX-01: gamma_M1 = 1.10 (truoc do = 1.05, SAI)
E_STEEL = 210000.0   # MPa
G_STEEL = 81000.0    # MPa
ALPHA_LT = 0.21      # Duong cong mat on dinh a - EN 1993-1-1 Table 6.3
                      # FIX-02: alpha_LT = 0.21 (truoc do = 0.34, SAI)
                      # Chi tiet: 0.21 = duong cong a (cho tiep dien can rong I/H)
                      #           0.34 = duong cong b (cho h va UC)


def _section_properties(h, b, tw, tf):
    """Dac trung hinh hoc tiet dien chu I doi xung kep (mm)."""
    hw = h - 2.0 * tf                      # chieu cao ban bung
    A = 2.0 * b * tf + hw * tw
    Ix = (b * h ** 3 - (b - tw) * hw ** 3) / 12.0
    Wel = Ix / (h / 2.0)
    # Momen khang uon deo chinh xac cho tiet dien I doi xung kep
    Wpl = b * tf * (h - tf) + tw * hw ** 2 / 4.0
    Iz = 2.0 * tf * b ** 3 / 12.0 + hw * tw ** 3 / 12.0
    It = (2.0 * b * tf ** 3 + (h - tf) * tw ** 3) / 3.0
    Iw = Iz * (h - tf) ** 2 / 4.0
    return dict(hw=hw, A=A, Ix=Ix, Wel=Wel, Wpl=Wpl, Iz=Iz, It=It, Iw=Iw)


def _section_class(h, b, tw, tf, fy):
    """Phan loai tiet dien theo EN 1993-1-1 Bang 5.2 (chiu uon thuan tuy)."""
    eps = math.sqrt(235.0 / fy)
    c_flange = (b - tw) / 2.0 - 0.0     # do vuon canh (bo qua ban kinh luon)
    c_web = h - 2.0 * tf
    r_flange = c_flange / tf
    r_web = c_web / tw
    if r_flange <= 9 * eps and r_web <= 72 * eps:
        cls = 1
    elif r_flange <= 10 * eps and r_web <= 83 * eps:
        cls = 2
    elif r_flange <= 14 * eps and r_web <= 124 * eps:
        cls = 3
    else:
        cls = 4
    return cls, r_flange, r_web, eps


def calc_steel_beam(h, b, tw, tf, M_ed, V_ed, fy=345, L_span=6000,
                    L_b=None, C1=1.13, M_ser=None):
    """
    Kiem tra dam thep I chiu uon + cat + mat on dinh uon xoan (LTB) + vong.

    PHIÊN BẢN TIÊU CHUẨN: EN 1993-1-1:2005 (Eurocode 3 Part 1-1)
    ⚠️ LƯU Ý QUAN TRỌNG:
       - Hồ sơ mới từ 2026: Sử dụng TCVN 5575:2024 → chạy steel_member_check_v2024.py
       - Script này: Dùng cho hồ sơ cũ (trước 2026) hoặc đối chiếu quốc tế

    Args:
    h, b, tw, tf : Kich thuoc tiet dien (mm)
    M_ed, V_ed   : Noi luc thiet ke ULS (kNm, kN)
    fy           : Gioi han chay (MPa)
    L_span       : Nhip dam (mm)
    L_b          : Chieu dai doan khong giang ngang (mm).
                   None -> lay bang L_span (thien ve an toan, dam khong giang).
                   Truyen 0 -> dam duoc giang ngang lien tuc, bo qua LTB.
    C1           : He so bieu do momen (1.0 momen deu; 1.13 tai phan bo deu)
    M_ser        : Momen tieu chuan SLS (kNm) de kiem tra vong.
                   BAT BUOC truyen tuong minh — script khong tu suy ra tu M_ed.

    PHAM VI: Tiet dien chu I doi xung kep, uon quanh truc khoe.
    CHUA kiem tra: on dinh cuc bo ban bung duoi tai tap trung (patch load),
    tuong tac M-V khi V_Ed > 0.5*V_Rd, xoan, va tiet diei Class 4.

    Standard_Method tra ve: "EN 1993-1-1" (khong phai TCVN)
    """
    sp = _section_properties(h, b, tw, tf)
    cls, r_flange, r_web, eps = _section_class(h, b, tw, tf, fy)

    logs = []

    # --- 1. Phan loai tiet dien ---
    W_used = sp["Wpl"] if cls in (1, 2) else sp["Wel"]
    W_name = "Wpl" if cls in (1, 2) else "Wel"
    logs.append({
        "Step": "Phân loại tiết diện",
        "Principle": "Tiết diện mảnh mất ổn định cục bộ trước khi đạt cường độ chảy, không huy động được momen dẻo.",
        "Formula": "c/t so với giới hạn Class 1/2/3, eps = sqrt(235/fy)",
        "Citation": {"Ma_TC": "EN 1993-1-1", "Dieu_Muc": "Bảng 5.2", "Bang_Hinh": "Table 5.2", "Trang": ""},
        "Values": f"eps={eps:.3f}, c/t cánh={r_flange:.1f}, c/t bụng={r_web:.1f}",
        "Result": f"Class {cls} → dùng {W_name} = {W_used/1e3:.1f} cm3"
    })

    # --- 2. Ben uon tiet dien (ULS) ---
    M_c_rd = (W_used * fy * 1e-6) / GAMMA_M0     # kNm
    eta_M = M_ed / M_c_rd
    logs.append({
        "Step": "Kiểm tra bền uốn tiết diện",
        "Principle": "Tiết diện chảy dẻo hoàn toàn khi momen đạt khả năng chịu uốn.",
        "Formula": f"M_c,Rd = {W_name} * fy / gamma_M0",
        "Citation": {"Ma_TC": "EN 1993-1-1", "Dieu_Muc": "Điều 6.2.5", "Bang_Hinh": "", "Trang": ""},
        "Values": f"{W_name}={W_used:.0f} mm3, fy={fy} MPa, gamma_M0={GAMMA_M0}",
        "Result": f"M_c,Rd = {M_c_rd:.2f} kNm  vs  M_Ed = {M_ed} kNm",
        "Utilization": f"eta_M = {eta_M:.3f}"
    })

    # --- 3. Ben cat (ULS) ---
    Av = sp["hw"] * tw
    V_rd = (Av * (fy / math.sqrt(3.0)) * 1e-3) / GAMMA_M0   # kN
    eta_V = V_ed / V_rd
    logs.append({
        "Step": "Kiểm tra bền cắt",
        "Principle": "Bản bụng chịu toàn bộ lực cắt, chảy dẻo theo tiêu chuẩn von Mises.",
        "Formula": "V_c,Rd = Av * (fy / sqrt(3)) / gamma_M0",
        "Citation": {"Ma_TC": "EN 1993-1-1", "Dieu_Muc": "Điều 6.2.6", "Bang_Hinh": "", "Trang": ""},
        "Values": f"Av={Av:.0f} mm2, fy={fy} MPa",
        "Result": f"V_c,Rd = {V_rd:.2f} kN  vs  V_Ed = {V_ed} kN",
        "Utilization": f"eta_V = {eta_V:.3f}"
    })

    # --- 4. On dinh uon xoan (LTB) ---
    L_unbraced = L_span if L_b is None else L_b
    if L_unbraced and L_unbraced > 0:
        Iz, It, Iw = sp["Iz"], sp["It"], sp["Iw"]
        M_cr = (C1 * math.pi ** 2 * E_STEEL * Iz / L_unbraced ** 2) * math.sqrt(
            Iw / Iz + (L_unbraced ** 2 * G_STEEL * It) / (math.pi ** 2 * E_STEEL * Iz)
        ) * 1e-6  # kNm
        lam_lt = math.sqrt((W_used * fy * 1e-6) / M_cr)
        phi_lt = 0.5 * (1.0 + ALPHA_LT * (lam_lt - 0.2) + lam_lt ** 2)
        chi_lt = min(1.0 / (phi_lt + math.sqrt(max(phi_lt ** 2 - lam_lt ** 2, 0.0))), 1.0)
        M_b_rd = chi_lt * W_used * fy * 1e-6 / GAMMA_M1
        eta_LTB = M_ed / M_b_rd
        ltb_note = f"L_b = {L_unbraced:.0f} mm"
    else:
        M_cr = None
        lam_lt = 0.0
        chi_lt = 1.0
        M_b_rd = M_c_rd
        eta_LTB = eta_M
        ltb_note = "Dầm được giằng ngang liên tục — bỏ qua LTB"

    logs.append({
        "Step": "Kiểm tra ổn định uốn xoắn tổng thể (LTB)",
        "Principle": "Dầm cao và hẹp có thể oằn ngang kèm xoắn trước khi tiết diện chảy dẻo.",
        "Formula": "M_b,Rd = chi_LT * W * fy / gamma_M1;  chi_LT theo đường cong mất ổn định",
        "Citation": {"Ma_TC": "EN 1993-1-1", "Dieu_Muc": "Điều 6.3.2", "Bang_Hinh": "", "Trang": ""},
        "Values": (f"{ltb_note}, C1={C1}, alpha_LT={ALPHA_LT}, "
                   f"M_cr={'%.2f kNm' % M_cr if M_cr else 'N/A'}, lambda_LT={lam_lt:.3f}, chi_LT={chi_lt:.3f}"),
        "Result": f"M_b,Rd = {M_b_rd:.2f} kNm  vs  M_Ed = {M_ed} kNm",
        "Utilization": f"eta_LTB = {eta_LTB:.3f}"
    })

    # --- 5. Vong (SLS) ---
    unverified = []
    if M_ser is None:
        eta_f = None
        f_calc = None
        f_allow = L_span / 250.0
        unverified.append("Chưa kiểm tra võng: cần truyền M_ser (momen tổ hợp tiêu chuẩn SLS)")
        logs.append({
            "Step": "Kiểm tra độ võng (SLS)",
            "Formula": "f = 5 * q_ser * L^4 / (384 * E * Ix)",
            "Values": "Data Missing: M_ser",
            "Result": "BỎ QUA — chưa có momen tổ hợp tiêu chuẩn SLS",
            "Remark": "Script không tự suy M_ser từ M_Ed. Người dùng phải cung cấp tổ hợp SLS thực tế."
        })
    else:
        q_ser = (8.0 * M_ser * 1e6) / (L_span ** 2)     # N/mm
        f_calc = (5.0 * q_ser * L_span ** 4) / (384.0 * E_STEEL * sp["Ix"])
        f_allow = L_span / 250.0
        eta_f = f_calc / f_allow
        logs.append({
            "Step": "Kiểm tra độ võng (SLS)",
            "Principle": "Võng quá lớn gây nứt hoàn thiện và cảm giác rung không an toàn.",
            "Formula": "f = 5 * q_ser * L^4 / (384 * E * Ix) <= L/250",
            "Citation": {"Ma_TC": "EN 1993-1-1", "Dieu_Muc": "Điều 7.2", "Bang_Hinh": "", "Trang": ""},
            "Values": f"M_ser={M_ser} kNm, q_ser={q_ser:.3f} N/mm, Ix={sp['Ix']/1e4:.0f} cm4, L={L_span} mm",
            "Result": f"f = {f_calc:.2f} mm  vs  [f] = {f_allow:.2f} mm",
            "Utilization": f"eta_f = {eta_f:.3f}"
        })

    etas = [eta_M, eta_V, eta_LTB] + ([eta_f] if eta_f is not None else [])
    overall = max(etas)
    status = "PASSED" if overall <= 1.0 else "FAILED"
    rating = "GREEN" if overall <= 0.70 else "YELLOW" if overall <= 0.90 else "ORANGE" if overall <= 1.0 else "RED"

    return {
        "section": f"I{h}x{b}x{tw}x{tf}",
        "section_class": cls,
        "A_cm2": round(sp["A"] / 1e2, 2),
        "Ix_cm4": round(sp["Ix"] / 1e4, 2),
        "Wel_cm3": round(sp["Wel"] / 1e3, 2),
        "Wpl_cm3": round(sp["Wpl"] / 1e3, 2),
        "M_ed_kNm": M_ed,
        "M_c_rd_kNm": round(M_c_rd, 2),
        "eta_M": round(eta_M, 3),
        "V_ed_kN": V_ed,
        "V_rd_kN": round(V_rd, 2),
        "eta_V": round(eta_V, 3),
        "chi_LT": round(chi_lt, 3),
        "M_b_rd_kNm": round(M_b_rd, 2),
        "eta_LTB": round(eta_LTB, 3),
        "f_calc_mm": round(f_calc, 2) if f_calc is not None else None,
        "f_allow_mm": round(f_allow, 2),
        "eta_f": round(eta_f, 3) if eta_f is not None else None,
        "overall_eta": round(overall, 3),
        "Rating": rating,
        "status": status,
        "Standard": "EN 1993-1-1 (Eurocode 3 Part 1-1)",
        "Standard_Method": "EN 1993-1-1",
        "Scope_Limitation": ("Tiết diện I đối xứng kép, uốn quanh trục khoẻ. CHƯA kiểm tra: ổn định cục bộ "
                             "bản bụng dưới tải tập trung, tương tác M-V khi V_Ed > 0.5*V_Rd, xoắn, tiết diện Class 4."),
        "Unverified_Items": unverified,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_steel_beam(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_steel_beam(h=400, b=200, tw=8, tf=13, M_ed=220, V_ed=150,
                                 fy=345, L_span=6000, M_ser=160)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
