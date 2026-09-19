import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_steel_beam_tcvn.py — Kiem tra dam thep theo TCVN 5575:2024
# =============================================================================
# Phiên bản: TCVN 5575:2024
# Thay the: calc_steel_beam.py (EN 1993-1-1) cho hồ sơ mới
# Reference: TCVN 5575:2024, Bang 3, Dieu 5.2, 6.2, 6.3
# =============================================================================

# --- Hang so theo TCVN 5575:2024 Bang 3 ---
GAMMA_M0 = 1.05  # He so tin cay vat lieu (ben tiet dien)
GAMMA_M1 = 1.10  # He so tin cay vat lieu (kiem tra on dinh)

# --- Cac he so khac ---
E_STEEL = 210000.0   # MPa - Module dan hoi
G_STEEL = 81000.0    # MPa - Module cat

# Duong cong mat on dinh (theo TCVN 5575:2024 / EN 1993-1-1)
# Bang 6.3 - Phu thuoc loai tiet dien
ALPHA_LT_CURVE = {
    "a": 0.21,   # Can rong I/H doi xung, duong cong a
    "b": 0.34,   # UC, duong cong b
    "c": 0.49,   # O, duong cong c
    "d": 0.76    # Hhep, duong cong d
}


def _section_properties(h, b, tw, tf):
    """
    Dac trung hinh hoc tiet dien chu I doi xung kep (mm).
    Tinh theo cong thuc chuan.
    Don vi dau vao: mm.
    Don vi dau ra: mm, mm2, mm3, mm4, mm6.
    """
    hw = h - 2.0 * tf                      # Chieu cao ban bung (mm)

    # Dien tich (mm2)
    A = 2.0 * b * tf + hw * tw

    # Moment quan tinh chinh Ix (mm4)
    Ix = (b * h ** 3 - (b - tw) * hw ** 3) / 12.0

    # Moment khang uon (mm3)
    Wel = Ix / (h / 2.0)
    Wpl = b * tf * (h - tf) + tw * hw ** 2 / 4.0

    # Moment quan tinh yeu Iz (mm4) - quanh truc yeu z (thang dung qua tam bung)
    # Tiet dien chu I doi xung kep: khoang cach doi truc d = 0
    # Iz = 2 * (tf * b^3 / 12) + (hw * tw^3 / 12)
    Iz = (tf * b ** 3) / 6.0 + (hw * tw ** 3) / 12.0

    # Moment xoan It (mm4) - St. Venant torsion
    It = (2.0 * b * tf ** 3 + (h - tf) * tw ** 3) / 3.0

    # Moment xoan cong song Iw (mm6) - cho tiep dien I doi xung
    # Cong thuc gan dung:
    Iw = (Iz * (h - tf) ** 2) / 4.0

    return {
        "hw": hw,
        "A": A,      # mm2
        "Ix": Ix,    # mm4
        "Wel": Wel,  # mm3
        "Wpl": Wpl,  # mm3
        "Iz": Iz,    # mm4
        "It": It,    # mm4
        "Iw": Iw     # mm6
    }


def _section_classification(h, b, tw, tf, fy):
    """
    Phan loai tiet dien theo TCVN 5575:2024 Dieu 5.3.
    Tra ve: (class, eps, r_flange, r_web)
    """
    eps = math.sqrt(235.0 / fy)
    c_flange = (b - tw) / 2.0
    c_web = h - 2.0 * tf
    r_flange = c_flange / tf
    r_web = c_web / tw

    # Gioi han theo bang 5.3 TCVN 5575:2024
    if r_flange <= 9 * eps and r_web <= 72 * eps:
        cls = 1
    elif r_flange <= 10 * eps and r_web <= 83 * eps:
        cls = 2
    elif r_flange <= 14 * eps and r_web <= 124 * eps:
        cls = 3
    else:
        cls = 4

    return cls, eps, r_flange, r_web


def _ltb_critical_moment(Iz, It, Iw, E, G, L):
    """
    Tinh momen ron bat ky (M_cr) cho dam khong duoc giang ngang.
    Cong thuc day du theo EN 1993-1-1 Dieu 6.3.1.3 / TCVN 5575:2024.

    M_cr = C1 * (pi^2*E*Iz/L^2) * sqrt(Iw/Iz + L^2*G*It/(pi^2*E*Iz))

    Gia thiet:
      - Goi don (simply supported) ca hai dau
      - Tai phan bo deu tac dung tai tam chua (conservative)
      - C1 = 1.13 (he so cho tai phan bo deu)

    Don vi:
      Iz (mm4), It (mm4), Iw (mm6), E (MPa), G (MPa), L (mm)
      Ket qua: kN.m
    """
    C1 = 1.13  # He so bieu do momen (1.13 = phan bo deu toan nhip)

    EIz_pi2_L2 = math.pi**2 * E * Iz / L**2   # N/mm = N.mm / mm2 * mm2/mm2 ... luong goc N.mm/mm

    # Kiem tra don vi:
    # Iw/Iz: mm6/mm4 = mm2
    # L^2*G*It/(pi^2*E*Iz): mm2 * N/mm2 * mm4 / (1 * N/mm2 * mm4) = mm2
    # => can bac 2 = mm -> EIz_pi2_L2 * sqrt(...) = N.mm^2 / mm ... SAI
    # 
    # Cong thuc chuan:
    # M_cr = C1/L * sqrt(E*Iz * (G*It + pi^2*E*Iw/L^2))
    # Don vi: 1/mm * sqrt(N/mm2 * mm4 * (N/mm2 * mm4 + N/mm2 * mm6 / mm2))
    #       = 1/mm * sqrt(N.mm2 * N.mm2)
    #       = 1/mm * N.mm2 = N.mm -> / 1e6 = kN.m
    M_cr_Nmm = C1 / L * math.sqrt(E * Iz * (G * It + math.pi**2 * E * Iw / L**2))
    M_cr = M_cr_Nmm / 1e6  # kN.m

    return M_cr, C1


def calc_steel_beam_tcvn(h, b, tw, tf, M_ed, V_ed, fy=345, L_span=6000,
                          L_b=None, lateral_support=True, M_ser=None,
                          lateral_curve="a"):
    """
    Kiem tra dam thep I chiu uon + cat + mat on dinh uon xoan (LTB) + vong.

    PHIEN BAN TIEU CHUAN: TCVN 5575:2024

    Args:
        h, b, tw, tf : Kich thuoc tiet dien (mm)
        M_ed, V_ed   : Noi luc thiet ke ULS (kNm, kN)
        fy           : Gioi han chay (MPa) - mac dinh 345 cho thep CCT38
        L_span       : Nhip dam (mm)
        L_b          : Chieu dai doan khong giang ngang (mm).
                       None -> lay bang L_span (thien ve an toan).
                       0 -> dam duoc giang ngang lien tuc, bo qua LTB.
        lateral_support: Co giang ngang lien tuc hay khong (True/False)
        M_ser        : Momen SLS (kNm) de kiem tra vong.
                       BAT BUOC truyen tuong minh.
        lateral_curve: Duong cong mat on dinh ('a', 'b', 'c', 'd')

    Output:
        JSON voi day du Calculation_Logs

    Standard_Method tra ve: "TCVN 5575:2024"
    """
    sp = _section_properties(h, b, tw, tf)
    cls, eps, r_flange, r_web = _section_classification(h, b, tw, tf, fy)
    alpha_LT = ALPHA_LT_CURVE.get(lateral_curve, 0.21)

    logs = []
    warnings = []
    unverified = []

    # =========================================================================
    # 1. PHAN LOAI TIET DIEN
    # =========================================================================
    W_used = sp["Wpl"] if cls in (1, 2) else sp["Wel"]
    W_name = "Wpl" if cls in (1, 2) else "Wel"

    logs.append({
        "Step": 1,
        "Description": "Phan loai tiet dien theo TCVN 5575:2024",
        "Principle": "Tiết diện mảnh mất ổn định cục bộ trước khi đạt cường độ chảy.",
        "Formula": "c/t so voi gioi han Class 1/2/3, eps = sqrt(235/fy)",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 5.3",
            "Bang_Hinh": "Bang 5.3",
            "Trang": "",
            "Trich_Yeu": "Phan loai tiet dien theo do manh cu/t"
        },
        "Substitution": f"eps = sqrt(235/{fy}) = {eps:.3f}, c/t canh = {r_flange:.2f}, c/t bung = {r_web:.2f}",
        "Result": f"Class {cls} -> dung {W_name} = {W_used/1e3:.1f} cm3"
    })

    # =========================================================================
    # 2. CUONG DO TINH TOAN
    # =========================================================================
    f_design = fy / GAMMA_M0  # MPa

    logs.append({
        "Step": 2,
        "Description": "Xac dinh cuong do tinh toan",
        "Principle": "Cuong do tinh toan = Gioi han chay / He so tin cay vat lieu.",
        "Formula": "f = fy / gamma_M0",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 5.2.1",
            "Bang_Hinh": "Bang 3",
            "Trang": "",
            "Trich_Yeu": "He so tin cay vat lieu gamma_M0 = 1.05"
        },
        "Substitution": f"fy = {fy} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"f = {f_design:.1f} MPa"
    })

    # =========================================================================
    # 3. KIEM TRA BEN UON (MOMENT CAPACITY)
    # =========================================================================
    # Cong thuc: M_c,Rd = W * fy / gamma_M0
    # Don vi: W (mm3) * f_design (MPa = N/mm2) = N.mm
    #         N.mm / 1e6 = kN.m
    # LUU Y: f_design = fy / GAMMA_M0 da bao gom GAMMA_M0.
    #        KHONG chia them GAMMA_M0 lan nua.

    M_c_Rd = W_used * f_design * 1e-6  # kNm  [FIX-04: bo /GAMMA_M0 du thua]
    eta_M = M_ed / M_c_Rd if M_c_Rd > 0 else 999

    logs.append({
        "Step": 3,
        "Description": "Kiem tra ben uon tiet dien (ULS)",
        "Principle": "Tiết diện đạt khả năng chịu uốn khi momen danh giá vượt momen thiết kế.",
        "Formula": f"M_c,Rd = {W_name} * fy / gamma_M0",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 6.2.5",
            "Bang_Hinh": "",
            "Trang": "",
            "Trich_Yeu": "Kha nang chiu uon cua tiet dien"
        },
        "Substitution": f"{W_name} = {W_used/1e3:.1f} cm3, fy = {fy} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"M_c,Rd = {M_c_Rd:.2f} kNm  vs  M_Ed = {M_ed} kNm",
        "Utilization": f"eta_M = {eta_M:.3f} ({eta_M*100:.1f}%)"
    })

    if eta_M > 1.0:
        warnings.append("M_c,Rd < M_Ed: Tang tiet dien hoac tang cap thep.")

    # =========================================================================
    # 4. KIEM TRA CAT (SHEAR CAPACITY)
    # =========================================================================
    # Dien tich chiu cat A_v (ban bung)
    # Cong thuc: V_pl,Rd = A_v * fy / (sqrt(3) * gamma_M0) = A_v * f_design / sqrt(3)
    # Don vi: A_v (mm2) * f_v (MPa) / 1000 = kN
    # LUU Y: f_v = f_design / sqrt(3) da bao gom GAMMA_M0.
    #         KHONG chia them GAMMA_M0 lan nua.
    Av = sp["hw"] * tw
    f_v = f_design / math.sqrt(3.0)  # Ung suat cat tinh toan (MPa)

    V_pl_Rd = Av * f_v * 1e-3  # kN  [FIX-04: bo /GAMMA_M0 du thua]
    eta_V = V_ed / V_pl_Rd if V_pl_Rd > 0 else 999

    logs.append({
        "Step": 4,
        "Description": "Kiem tra ben cat (ULS)",
        "Principle": "Bản bụng chịu toàn bộ lực cắt theo lý thuyết von Mises.",
        "Formula": "V_pl,Rd = Av * fy/(sqrt(3)*gamma_M0)",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 6.2.6",
            "Bang_Hinh": "",
            "Trang": "",
            "Trich_Yeu": "Kha nang chiu cat cua ban bung"
        },
        "Substitution": f"Av = {Av:.0f} mm2, fy = {fy} MPa, f_v = {f_v:.1f} MPa",
        "Result": f"V_pl,Rd = {V_pl_Rd:.2f} kN  vs  V_Ed = {V_ed} kN",
        "Utilization": f"eta_V = {eta_V:.3f} ({eta_V*100:.1f}%)"
    })

    # =========================================================================
    # 5. KIEM TRA ON DINH UON XOAN (LTB)
    # =========================================================================
    L_unbraced = L_span if L_b is None else L_b

    if L_unbraced > 0 and not lateral_support:
        # Tinh momen ron bat ky M_cr - cong thuc day du theo TCVN 5575:2024 / EN 1993-1-1 D.6.3.1.3
        # M_cr = C1/L * sqrt(E*Iz*(G*It + pi^2*E*Iw/L^2))
        # Kiem tra don vi:
        #   E (N/mm2), Iz (mm4), G (N/mm2), It (mm4), Iw (mm6), L (mm)
        #   sqrt(N/mm2*mm4 * N/mm2*mm4) = sqrt(N2.mm4) = N.mm2
        #   N.mm2 / L(mm) = N.mm -> / 1e6 = kN.m  [FIX-04]
        C1 = 1.13  # He so bieu do momen cho phan bo deu, goi don 2 dau
        M_cr_Nmm = C1 / L_unbraced * math.sqrt(
            E_STEEL * sp["Iz"] * (
                G_STEEL * sp["It"] +
                math.pi**2 * E_STEEL * sp["Iw"] / L_unbraced**2
            )
        )
        M_cr = M_cr_Nmm / 1e6  # kN.m  [FIX-04]

        # Do manh uon xoan
        # lambda_LT = sqrt(M_c_Rd / M_cr)
        # lambda_LT = sqrt(W_pl * fy / gamma_M0 / M_cr)
        lambda_LT = math.sqrt(M_c_Rd / M_cr) if M_cr > 0 else 999

        # He so giam chi_LT (duong cong a/b/c/d)
        phi_LT = 0.5 * (1 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2)
        sqrt_term = max(phi_LT ** 2 - lambda_LT ** 2, 0.0)
        chi_LT = min(1.0, 1.0 / (phi_LT + math.sqrt(sqrt_term)))

        # Momen tinh toan sau khi giam
        M_b_Rd = chi_LT * W_used * f_design * 1e-6 / GAMMA_M1  # kNm
        eta_ltb = M_ed / M_b_Rd if M_b_Rd > 0 else 999

        ltb_note = f"Khong giang ngang, L_b = {L_unbraced:.0f} mm"

        logs.append({
            "Step": 5,
            "Description": "Kiem tra on dinh uon xoan (LTB) - TCVN 5575:2024",
            "Principle": "Dầm cao và hẹp không được giằng ngang có thể oằn ngang kèm xoắn trước khi tiết diện chảy dẻo.",
            "Formula": "M_b,Rd = chi_LT * W * fy / gamma_M1",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Dieu 6.3.2",
                "Bang_Hinh": "Bang 6.3",
                "Trang": "",
                "Trich_Yeu": f"He so giam chi_LT theo duong cong '{lateral_curve}'"
            },
            "Substitution": f"C1 = {C1}, L_b = {L_unbraced:.0f} mm, alpha_LT = {alpha_LT}, M_cr = {M_cr:.2f} kNm, lambda_LT = {lambda_LT:.3f}, chi_LT = {chi_LT:.3f}",
            "Result": f"M_b,Rd = {M_b_Rd:.2f} kNm  vs  M_Ed = {M_ed} kNm",
            "Utilization": f"eta_LTB = {eta_ltb:.3f} ({eta_ltb*100:.1f}%)"
        })

        if eta_ltb > 0.9:
            warnings.append(f"LTB: eta_LTB = {eta_ltb*100:.1f}% > 90%. De xuat: tang giang ngang hoac tang tiet dien.")
    else:
        # Dam duoc giang ngang lien tuc
        M_b_Rd = M_c_Rd
        eta_ltb = eta_M
        chi_LT = 1.0
        lambda_LT = 0.0
        M_cr = None

        logs.append({
            "Step": 5,
            "Description": "Kiem tra on dinh uon xoan (LTB)",
            "Principle": "Dầm được giằng ngang liên tục — bỏ qua kiểm tra LTB.",
            "Formula": "M_b,Rd = M_c,Rd (chi_LT = 1.0)",
            "Values": "Giang ngang lien tuc hoac L_b = 0",
            "Result": f"M_b,Rd = {M_b_Rd:.2f} kNm (bo qua LTB)"
        })

    # =========================================================================
    # 6. KIEM TRA VONG (SLS)
    # =========================================================================
    if M_ser is None:
        eta_f = None
        f_calc = None
        f_allow = L_span / 250.0
        unverified.append("Chua kiem tra vong: can truyen M_ser (momen SLS)")

        logs.append({
            "Step": 6,
            "Description": "Kiem tra do vong (SLS)",
            "Values": "Data Missing: M_ser",
            "Result": "BO QUA — chua co momen SLS"
        })
    else:
        # Chuyen momen SLS thanh tai phan bo deu tuong duong
        q_ser = (8.0 * M_ser * 1e6) / (L_span ** 2)  # N/mm
        f_calc = (5.0 * q_ser * L_span ** 4) / (384.0 * E_STEEL * sp["Ix"])
        f_allow = L_span / 250.0
        eta_f = f_calc / f_allow

        logs.append({
            "Step": 6,
            "Description": "Kiem tra do vong (SLS)",
            "Principle": "Võng quá lớn gây nứt hoàn thiện và cảm giác rung không an toàn.",
            "Formula": "f = 5*q*L^4/(384*E*I) <= L/250",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Dieu 7.2",
                "Bang_Hinh": "Phu luc M",
                "Trang": "",
                "Trich_Yeu": "Gioi han do vong L/250"
            },
            "Substitution": f"M_ser = {M_ser} kNm, q_ser = {q_ser:.3f} N/mm, E = {E_STEEL} MPa, Ix = {sp['Ix']/1e4:.0f} cm4, L = {L_span} mm",
            "Result": f"f = {f_calc:.2f} mm  vs  [f] = {f_allow:.2f} mm",
            "Utilization": f"eta_f = {eta_f:.3f} ({eta_f*100:.1f}%)"
        })

        if eta_f > 1.0:
            warnings.append(f"Vong: f = {f_calc:.1f} mm > [f] = {f_allow:.1f} mm. Tang do cung hoac giam nhip.")

    # =========================================================================
    # 7. KET LUAN
    # =========================================================================
    etas = [eta_M, eta_V, eta_ltb]
    if eta_f is not None:
        etas.append(eta_f)

    overall_eta = max(etas)

    if overall_eta <= 0.70:
        rating = "GREEN"
        remark = "Du tru an toàn > 30%. Co the xem xet giam tiet dien (VE)."
    elif overall_eta <= 0.90:
        rating = "YELLOW"
        remark = "Dat, muc su dung hop ly."
    elif overall_eta <= 1.00:
        rating = "ORANGE"
        remark = "Sat nguong (η > 90%). Can kiem tra ky cac yeu to chua xet."
    else:
        rating = "RED"
        remark = "KHONG DAT (η > 100%). Yeu cau tang tiet dien hoac tang cap thep."

    status = "PASSED" if overall_eta <= 1.0 else "FAILED"

    return {
        "section": f"I{h}x{b}x{tw}x{tf}",
        "section_class": cls,
        "A_cm2": round(sp["A"] / 1e2, 2),
        "Ix_cm4": round(sp["Ix"] / 1e4, 2),
        "Wel_cm3": round(sp["Wel"] / 1e3, 2),
        "Wpl_cm3": round(sp["Wpl"] / 1e3, 2),
        "Iz_cm4": round(sp["Iz"] / 1e4, 2),
        "It_cm4": round(sp["It"] / 1e4, 2),
        "M_ed_kNm": M_ed,
        "M_c_Rd_kNm": round(M_c_Rd, 2),
        "eta_M": round(eta_M, 3),
        "V_ed_kN": V_ed,
        "V_pl_Rd_kN": round(V_pl_Rd, 2),
        "eta_V": round(eta_V, 3),
        "chi_LT": round(chi_LT, 3),
        "lambda_LT": round(lambda_LT, 3),
        "M_cr_kNm": round(M_cr, 2) if M_cr else None,
        "M_b_Rd_kNm": round(M_b_Rd, 2),
        "eta_LTB": round(eta_ltb, 3),
        "f_calc_mm": round(f_calc, 2) if f_calc is not None else None,
        "f_allow_mm": round(f_allow, 2),
        "eta_f": round(eta_f, 3) if eta_f is not None else None,
        "overall_eta": round(overall_eta, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5575:2024",
        "Standard_Method": "TCVN 5575:2024",
        "Scope_Limitation": (
            "Tiet dien I doi xung kep, uon quanh truc khoe. "
            "CHUA kiem tra: on dinh cuc bo ban bung (patch load), "
            "tuong tac M-V khi V_Ed > 0.5*V_pl_Rd, xoan, tiet dien Class 4."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_steel_beam_tcvn(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_steel_beam_tcvn(
            h=400, b=200, tw=8, tf=13,
            M_ed=220, V_ed=150,
            fy=345, L_span=6000,
            lateral_support=False,  # Khong giang ngang
            M_ser=160
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
