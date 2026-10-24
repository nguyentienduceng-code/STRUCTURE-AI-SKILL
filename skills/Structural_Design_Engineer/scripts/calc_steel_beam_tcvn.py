import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_steel_beam_tcvn.py — Kiểm tra dầm thép theo TCVN 5575:2024
# =============================================================================

from pathlib import Path
for _p in Path(__file__).resolve().parents:
    if (_p / "_SHARED" / "standards" / "tables.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

try:
    from _SHARED.standards.tables import GAMMA_M0, GAMMA_M1
except ImportError:
    GAMMA_M0 = 1.05  # Hệ số tin cậy vật liệu (bền tiết diện)
    GAMMA_M1 = 1.10  # Hệ số tin cậy vật liệu (kiểm tra ổn định tổng thể LTB)

E_STEEL = 210000.0
G_STEEL = 81000.0

ALPHA_LT_CURVE = {
    "a": 0.21,
    "b": 0.34,
    "c": 0.49,
    "d": 0.76
}


def _section_properties(h, b, tw, tf):
    hw = h - 2.0 * tf
    A = 2.0 * b * tf + hw * tw
    Ix = (b * h ** 3 - (b - tw) * hw ** 3) / 12.0
    Wel = Ix / (h / 2.0)
    Wpl = b * tf * (h - tf) + tw * hw ** 2 / 4.0
    Iz = (tf * b ** 3) / 6.0 + (hw * tw ** 3) / 12.0
    It = (2.0 * b * tf ** 3 + (h - tf) * tw ** 3) / 3.0
    Iw = (Iz * (h - tf) ** 2) / 4.0
    return {
        "hw": hw, "A": A, "Ix": Ix, "Wel": Wel, "Wpl": Wpl,
        "Iz": Iz, "It": It, "Iw": Iw
    }


def _section_classification(h, b, tw, tf, fy):
    eps = math.sqrt(235.0 / fy)
    c_flange = (b - tw) / 2.0
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
    return cls, eps, r_flange, r_web


def calc_steel_beam_tcvn(h, b, tw, tf, M_ed, V_ed, fy=345, L_span=6000,
                         L_b=None, lateral_support=True, M_ser=None,
                         lateral_curve="a"):
    sp = _section_properties(h, b, tw, tf)
    cls, eps, r_flange, r_web = _section_classification(h, b, tw, tf, fy)
    alpha_LT = ALPHA_LT_CURVE.get(lateral_curve, 0.21)

    logs = []
    warnings = []
    unverified = []

    W_used = sp["Wpl"] if cls in (1, 2) else sp["Wel"]
    W_name = "Wpl" if cls in (1, 2) else "Wel"

    logs.append({
        "Step": 1,
        "Description": "Phân loại tiết diện theo TCVN 5575:2024",
        "Formula": "c/t so với giới hạn Class 1/2/3, eps = sqrt(235/fy)",
        "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 5.3", "Bang_Hinh": "Bảng 5.3", "Trang": "42", "Trich_Yeu": "Phân loại tiết diện"},
        "Substitution": f"eps = sqrt(235/{fy}) = {eps:.3f}, c/t cánh = {r_flange:.2f}, c/t bụng = {r_web:.2f}",
        "Result": f"Class {cls} -> dùng {W_name} = {W_used/1e3:.1f} cm3"
    })

    f_design = fy / GAMMA_M0
    logs.append({
        "Step": 2,
        "Description": "Xác định cường độ tính toán",
        "Formula": "f = fy / gamma_M0",
        "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 5.2.1", "Bang_Hinh": "Bảng 3", "Trang": "38", "Trich_Yeu": "Hệ số tin cậy vật liệu gamma_M0 = 1.05"},
        "Substitution": f"fy = {fy} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"f = {f_design:.1f} MPa"
    })

    M_c_Rd = W_used * f_design * 1e-6
    eta_M = M_ed / M_c_Rd if M_c_Rd > 0 else 999

    logs.append({
        "Step": 3,
        "Description": "Kiểm tra bền uốn tiết diện (ULS)",
        "Formula": f"M_c,Rd = {W_name} * fy / gamma_M0",
        "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 6.2.5", "Bang_Hinh": "", "Trang": "52", "Trich_Yeu": "Khả năng chịu uốn của tiết diện"},
        "Substitution": f"{W_name} = {W_used/1e3:.1f} cm3, fy = {fy} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"M_c,Rd = {M_c_Rd:.2f} kNm vs M_Ed = {M_ed} kNm",
        "Utilization": f"eta_M = {eta_M:.3f} ({eta_M*100:.1f}%)"
    })
    if eta_M > 1.0:
        warnings.append("M_c,Rd < M_Ed: Tăng tiết diện hoặc tăng cấp thép.")

    Av = sp["hw"] * tw
    f_v = f_design / math.sqrt(3.0)
    V_pl_Rd = Av * f_v * 1e-3
    eta_V = V_ed / V_pl_Rd if V_pl_Rd > 0 else 999

    logs.append({
        "Step": 4,
        "Description": "Kiểm tra bền cắt (ULS)",
        "Formula": "V_pl,Rd = Av * fy / (sqrt(3) * gamma_M0)",
        "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 6.2.6", "Bang_Hinh": "", "Trang": "55", "Trich_Yeu": "Khả năng chịu cắt của bản bụng"},
        "Substitution": f"Av = {Av:.0f} mm2, fy = {fy} MPa, f_v = {f_v:.1f} MPa",
        "Result": f"V_pl,Rd = {V_pl_Rd:.2f} kN vs V_Ed = {V_ed} kN",
        "Utilization": f"eta_V = {eta_V:.3f} ({eta_V*100:.1f}%)"
    })

    L_unbraced = L_span if L_b is None else L_b
    if L_unbraced > 0 and not lateral_support:
        C1 = 1.13
        M_cr_Nmm = C1 / L_unbraced * math.sqrt(
            E_STEEL * sp["Iz"] * (
                G_STEEL * sp["It"] +
                math.pi ** 2 * E_STEEL * sp["Iw"] / L_unbraced ** 2
            )
        )
        M_cr = M_cr_Nmm / 1e6

        # [FIX BUG-STR-04]: Độ mảnh quy ước lambda_LT = sqrt(W_y * fy / M_cr) (không chia gamma_M0)
        # và M_b,Rd = chi_LT * W_used * (fy / GAMMA_M1) * 1e-6 (không chia kép cả GAMMA_M0 lẫn GAMMA_M1!)
        M_y_char = W_used * fy * 1e-6
        lambda_LT = math.sqrt(M_y_char / M_cr) if M_cr > 0 else 999
        phi_LT = 0.5 * (1 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2)
        sqrt_term = max(phi_LT ** 2 - lambda_LT ** 2, 0.0)
        chi_LT = min(1.0, 1.0 / (phi_LT + math.sqrt(sqrt_term)))

        M_b_Rd = chi_LT * W_used * (fy / GAMMA_M1) * 1e-6
        eta_ltb = M_ed / M_b_Rd if M_b_Rd > 0 else 999

        logs.append({
            "Step": 5,
            "Description": "Kiểm tra ổn định uốn xoắn (LTB) - TCVN 5575:2024",
            "Formula": "M_b,Rd = chi_LT * W * fy / gamma_M1 (với gamma_M1 = 1.10)",
            "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 6.3.2", "Bang_Hinh": "Bảng 6.3", "Trang": "62", "Trich_Yeu": f"Hệ số giảm chi_LT theo đường cong '{lateral_curve}'"},
            "Substitution": f"C1 = {C1}, L_b = {L_unbraced:.0f} mm, alpha_LT = {alpha_LT}, M_cr = {M_cr:.2f} kNm, lambda_LT = {lambda_LT:.3f}, chi_LT = {chi_LT:.3f}, gamma_M1 = {GAMMA_M1}",
            "Result": f"M_b,Rd = {M_b_Rd:.2f} kNm vs M_Ed = {M_ed} kNm",
            "Utilization": f"eta_LTB = {eta_ltb:.3f} ({eta_ltb*100:.1f}%)"
        })
        if eta_ltb > 0.9:
            warnings.append(f"LTB: eta_LTB = {eta_ltb*100:.1f}% > 90%. Đề xuất: tăng giằng ngang hoặc tăng tiết diện.")
    else:
        M_b_Rd = M_c_Rd
        eta_ltb = eta_M
        chi_LT = 1.0
        lambda_LT = 0.0
        M_cr = None
        logs.append({
            "Step": 5,
            "Description": "Kiểm tra ổn định uốn xoắn (LTB)",
            "Formula": "M_b,Rd = M_c,Rd (chi_LT = 1.0)",
            "Result": f"M_b,Rd = {M_b_Rd:.2f} kNm (bỏ qua LTB)"
        })

    if M_ser is None:
        eta_f = None
        f_calc = None
        f_allow = L_span / 250.0
        unverified.append("Chưa kiểm tra võng: cần truyền M_ser (momen SLS)")
        logs.append({
            "Step": 6,
            "Description": "Kiểm tra độ võng (SLS)",
            "Result": "BỎ QUA — chưa có momen SLS"
        })
    else:
        q_ser = (8.0 * M_ser * 1e6) / (L_span ** 2)
        f_calc = (5.0 * q_ser * L_span ** 4) / (384.0 * E_STEEL * sp["Ix"])
        f_allow = L_span / 250.0
        eta_f = f_calc / f_allow
        logs.append({
            "Step": 6,
            "Description": "Kiểm tra độ võng (SLS)",
            "Formula": "f = 5*q*L^4/(384*E*I) <= L/250",
            "Citation": {"Ma_TC": "TCVN 5575", "Nam": "2024", "Dieu_Muc": "Điều 7.2", "Bang_Hinh": "Phụ lục M", "Trang": "85", "Trich_Yeu": "Giới hạn độ võng L/250"},
            "Substitution": f"M_ser = {M_ser} kNm, q_ser = {q_ser:.3f} N/mm, E = {E_STEEL} MPa, Ix = {sp['Ix']/1e4:.0f} cm4, L = {L_span} mm",
            "Result": f"f = {f_calc:.2f} mm vs [f] = {f_allow:.2f} mm",
            "Utilization": f"eta_f = {eta_f:.3f} ({eta_f*100:.1f}%)"
        })
        if eta_f > 1.0:
            warnings.append(f"Võng: f = {f_calc:.1f} mm > [f] = {f_allow:.1f} mm.")

    etas = [eta_M, eta_V, eta_ltb]
    if eta_f is not None:
        etas.append(eta_f)
    overall_eta = max(etas)

    if overall_eta <= 0.70:
        rating = "GREEN"
    elif overall_eta <= 0.90:
        rating = "YELLOW"
    elif overall_eta <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

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
            "Tiết diện I đối xứng kép, uốn quanh trục khỏe. "
            "CHƯA kiểm tra: ổn định cục bộ bản bụng (patch load), tương tác M-V khi V_Ed > 0.5*V_pl_Rd, xoắn, tiết diện Class 4."
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
            lateral_support=False,
            M_ser=160
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
