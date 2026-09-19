import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_steel_connection_tcvn.py — Kiem tra lien ket bu long theo TCVN 5575:2024
# =============================================================================
# Phiên bản: TCVN 5575:2024
# Thay the: calc_steel_connection.py (EN 1993-1-8) cho hồ sơ mới
# Reference: TCVN 5575:2024, Bang 10, Dieu 10.2, 10.3
# =============================================================================

# --- Hang so theo TCVN 5575:2024 ---
GAMMA_M0 = 1.05      # He so tin cay vat lieu (ben)
GAMMA_M2 = 1.25      # He so tin cay lien ket (cho lien ket bu long)

# --- Cuong do keo dut bu long fub (MPa) theo TCVN 1916 / ISO 898-1 ---
FUB_MAP = {
    "4.6": 400.0,
    "5.6": 500.0,
    "6.8": 600.0,
    "8.8": 800.0,
    "10.9": 1000.0
}

# --- He so alpha_v theo TCVN 5575:2024 Bang 10 ---
# Khi mat cat qua phan ren cua bu long
ALPHA_V_MAP = {
    "4.6": 0.6,
    "5.6": 0.6,
    "6.8": 0.5,
    "8.8": 0.6,
    "10.9": 0.5
}

# --- Dien tich phan ren As (mm2) theo TCVN 1916 ---
AS_MAP = {
    10: 58.0,
    12: 84.3,
    14: 115.0,
    16: 157.0,
    18: 192.0,
    20: 245.0,
    22: 303.0,
    24: 353.0,
    27: 459.0,
    30: 561.0,
    33: 694.0,
    36: 817.0,
    42: 1120.0
}


def _norm_grade(grade):
    """Chuan hoa cap ben bu long ve chuoi."""
    if isinstance(grade, str):
        g = grade.strip()
    else:
        g = f"{float(grade):g}"
    if g not in FUB_MAP:
        raise ValueError(
            f"Cap ben bu long khong hop le: {grade!r}. "
            f"Chi chap nhan: {', '.join(FUB_MAP.keys())}"
        )
    return g


def _get_bolt_area(d):
    """Lay dien tich phan ren bu long (mm2)."""
    if d in AS_MAP:
        return AS_MAP[d]
    else:
        # Tinh theo cong thuc gan dung cho duong kinh bat ky
        return 0.78 * math.pi * (d ** 2) / 4.0


def calc_steel_connection_tcvn(bolt_d=20, grade="8.8", n_bolts=6, V_ed=180,
                                F_t_ed=0, t_plate=10, f_u_plate=400,
                                n_shear_planes=1,
                                e1=None, e2=None, p1=None, p2=None):
    """
    Kiem tra lien ket bu long chiu cat + keo + ep mat theo TCVN 5575:2024.

    Args:
        bolt_d        : Duong kinh bu long (mm)
        grade         : Cap ben — '4.6' / '5.6' / '6.8' / '8.8' / '10.9'
        n_bolts       : So luong bu long
        V_ed          : Luc cat thiet ke tac dung len nhom bu long (kN)
        F_t_ed        : Luc keo thiet ke tac dung len nhom bu long (kN)
        t_plate       : Be day ban ma mong nhat (mm)
        f_u_plate     : Cuong do keo dut cua thep ban ma (MPa)
        n_shear_planes: So mat cat chiu luc cua 1 bu long (1 = 1 mat, 2 = 2 mat)
        e1, e2, p1, p2: Khoang cach bo tri bu long (mm)
                        e1: khoang cach tu tam bu long bien den mat bi cat
                        e2: khoang cach tu tam bu long den mat cat ben
                        p1: khoang cach giua cac bu long theo phuong luc cat
                        p2: khoang cach giua cac bu long vuong goc phuong luc cat
                        Neu bo trong -> lay gia tri thien ve an toan.

    PHAM VI: Lien ket chiu ep mat (bearing type).
    CHUA kiem tra:
      - Lien ket ma sat truot gioi han (slip-resistant)
      - Pha hoai khoi (block tearing) - xem TCVN 5575:2024 Dieu 10.4.3
      - Kha nang chiu luc cua ban ma va bung dam

    Output:
        JSON voi day du Calculation_Logs

    Standard_Method tra ve: "TCVN 5575:2024"
    """
    g = _norm_grade(grade)
    fub = FUB_MAP[g]
    alpha_v = ALPHA_V_MAP[g]
    A_s = _get_bolt_area(int(bolt_d))
    d0 = bolt_d + 2.0  # Duong kinh lo bu long

    logs = []
    warnings = []
    unverified = []

    # =========================================================================
    # 1. KHA NANG CHIU CAT CU A NHOM BU LONG
    # =========================================================================
    # TCVN 5575:2024 - Dieu 10.2.4
    # Cong thuc: F_v,Rd = (alpha_v * fub * A_s / gamma_M2)

    F_v_Rd_1 = (alpha_v * fub * A_s * 1e-3) / GAMMA_M2  # kN (1 mat cat)
    F_v_Rd_total = F_v_Rd_1 * n_shear_planes * n_bolts  # kN
    eta_shear = V_ed / F_v_Rd_total if F_v_Rd_total > 0 else 999

    logs.append({
        "Step": 1,
        "Description": "Kha nang chiu cat cua nhom bu long",
        "Principle": "Than bu long bi cat dut tai mat truot giua cac ban thep.",
        "Formula": "F_v,Rd = alpha_v * f_ub * A_s / gamma_M2",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 10.2.4",
            "Bang_Hinh": "Bang 10.1",
            "Trang": "",
            "Trich_Yeu": "Cuong do tinh toan chiu cat cua bu long"
        },
        "Substitution": (
            f"alpha_v = {alpha_v} (cap {g}), f_ub = {fub} MPa, "
            f"A_s = {A_s:.1f} mm2, gamma_M2 = {GAMMA_M2}, "
            f"n_mat_cat = {n_shear_planes}, n = {n_bolts}"
        ),
        "Result": f"F_v,Rd,1 = {F_v_Rd_1:.2f} kN | Tong = {F_v_Rd_total:.2f} kN",
        "Utilization": f"eta_cat = {eta_shear:.3f} ({eta_shear*100:.1f}%)"
    })

    if eta_shear > 1.0:
        warnings.append("Tang so bu long hoac tang duong kinh bu long.")

    # =========================================================================
    # 2. KHA NANG CHIU EP MAT
    # =========================================================================
    # TCVN 5575:2024 - Dieu 10.2.5
    # Cong thuc: F_b,Rd = k1 * alpha_b * f_u * d * t / gamma_M2

    assumed_values = []
    if e1 is None:
        e1 = 1.5 * d0
        assumed_values.append("e1 = 1.5*d0 (mac dinh)")
    if e2 is None:
        e2 = 1.5 * d0
        assumed_values.append("e2 = 1.5*d0 (mac dinh)")
    if p1 is None:
        p1 = 2.5 * d0
        assumed_values.append("p1 = 2.5*d0 (mac dinh)")
    if p2 is None:
        p2 = 2.5 * d0
        assumed_values.append("p2 = 2.5*d0 (mac dinh)")

    # He so alpha_b (phan phu thuoc vao khoang cach e1 va p1)
    alpha_b = min(
        e1 / (3.0 * d0),
        p1 / (3.0 * d0) - 0.25,
        fub / f_u_plate,
        1.0
    )
    alpha_b = max(alpha_b, 0.0)

    # He so k1 (phan phu thuoc vao khoang cach e2 va p2)
    k1 = min(
        2.8 * e2 / d0 - 1.7,
        1.4 * p2 / d0 - 1.7,
        2.5
    )
    k1 = max(k1, 0.0)

    F_b_Rd_1 = (k1 * alpha_b * f_u_plate * bolt_d * t_plate * 1e-3) / GAMMA_M2  # kN
    F_b_Rd_total = F_b_Rd_1 * n_bolts
    eta_bearing = V_ed / F_b_Rd_total if F_b_Rd_total > 0 else 999

    logs.append({
        "Step": 2,
        "Description": "Kha nang chiu ep mat cua ban thep",
        "Principle": "Bu long ep vao thanh lo lam bien dang hoac xe rach ban thep.",
        "Formula": "F_b,Rd = k1 * alpha_b * f_u * d * t / gamma_M2",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Dieu 10.2.5",
            "Bang_Hinh": "Bang 10.2",
            "Trang": "",
            "Trich_Yeu": "Kha nang chiu ep mat cua ban thep"
        },
        "Substitution": (
            f"k1 = {k1:.3f}, alpha_b = {alpha_b:.3f}, f_u = {f_u_plate} MPa, "
            f"d = {bolt_d} mm, t = {t_plate} mm, d0 = {d0} mm, "
            f"e1 = {e1:.0f} mm, p1 = {p1:.0f} mm, e2 = {e2:.0f} mm, p2 = {p2:.0f} mm"
        ),
        "Result": f"F_b,Rd,1 = {F_b_Rd_1:.2f} kN | Tong = {F_b_Rd_total:.2f} kN",
        "Utilization": f"eta_ep_mat = {eta_bearing:.3f} ({eta_bearing*100:.1f}%)"
    })

    if assumed_values:
        unverified.append("Khoang cach bo tri bu long: " + "; ".join(assumed_values))

    if eta_bearing > 1.0:
        warnings.append("Tang khoang cach bo tri bu long hoac tang duong kinh bu long.")

    # =========================================================================
    # 3. KHA NANG CHIU KEO (Neu co F_t_ed)
    # =========================================================================
    if F_t_ed > 0:
        # TCVN 5575:2024 - Dieu 10.2.3
        F_t_Rd_1 = (0.9 * fub * A_s * 1e-3) / GAMMA_M2  # kN
        F_t_Rd_total = F_t_Rd_1 * n_bolts
        eta_tension = F_t_ed / F_t_Rd_total if F_t_Rd_total > 0 else 999

        logs.append({
            "Step": 3,
            "Description": "Kha nang chiu keo cua nhom bu long",
            "Principle": "Bu long bi keo dut tai phan ren.",
            "Formula": "F_t,Rd = 0.9 * f_ub * A_s / gamma_M2",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Dieu 10.2.3",
                "Bang_Hinh": "Bang 10.1",
                "Trang": "",
                "Trich_Yeu": "Cuong do tinh toan chiu keo cua bu long"
            },
            "Substitution": f"0.9 * {fub} MPa * {A_s:.1f} mm2 / {GAMMA_M2}",
            "Result": f"F_t,Rd,1 = {F_t_Rd_1:.2f} kN | Tong = {F_t_Rd_total:.2f} kN",
            "Utilization": f"eta_keo = {eta_tension:.3f} ({eta_tension*100:.1f}%)"
        })
    else:
        eta_tension = 0.0
        F_t_Rd_total = 0.0
        logs.append({
            "Step": 3,
            "Description": "Kha nang chiu keo cua nhom bu long",
            "Values": "Khong co luc keo (F_t_ed = 0)",
            "Result": "Khong kiem tra"
        })

    # =========================================================================
    # 4. TUONG TAC CAT - KEO
    # =========================================================================
    if F_t_ed > 0 and V_ed > 0:
        # TCVN 5575:2024 - Dieu 10.2.6
        interaction = (V_ed / F_v_Rd_total) + (F_t_ed / (1.4 * F_t_Rd_total))
        eta_interaction = interaction

        logs.append({
            "Step": 4,
            "Description": "Kiem tra tuong tac cat - keo dong thoi",
            "Principle": "Bu long dong thoi chiu cat va keo se suy giam kha nang chiu luc.",
            "Formula": "F_v,Ed/F_v,Rd + F_t,Ed/(1.4*F_t,Rd) <= 1.0",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Dieu 10.2.6",
                "Bang_Hinh": "",
                "Trang": "",
                "Trich_Yeu": "Tuong tac giua luc cat va luc keo"
            },
            "Substitution": (
                f"V_Ed = {V_ed} kN, F_v,Rd = {F_v_Rd_total:.2f} kN, "
                f"F_t,Ed = {F_t_ed} kN, F_t,Rd = {F_t_Rd_total:.2f} kN"
            ),
            "Result": f"Ty so tuong tac = {interaction:.3f}",
            "Utilization": f"eta_tuong_tac = {eta_interaction:.3f}"
        })

        if interaction > 1.0:
            warnings.append("Tuong tac cat-keo vuot 1.0. Phai giam luc cat hoac luc keo.")
    else:
        eta_interaction = 0.0
        logs.append({
            "Step": 4,
            "Description": "Kiem tra tuong tac cat - keo dong thoi",
            "Values": "Chi mot loai luc tac dung",
            "Result": "Khong can kiem tra"
        })

    # =========================================================================
    # 5. KET LUAN
    # =========================================================================
    etas = [eta_shear, eta_bearing]
    if F_t_ed > 0:
        etas.append(eta_tension)
    if F_t_ed > 0 and V_ed > 0:
        etas.append(eta_interaction)

    overall_eta = max(etas)

    if overall_eta <= 0.70:
        rating = "GREEN"
        remark = "Du tru > 30%. Co the xem xet giam so bu long (VE)."
    elif overall_eta <= 0.90:
        rating = "YELLOW"
        remark = "Dat, muc su dung hop ly."
    elif overall_eta <= 1.00:
        rating = "ORANGE"
        remark = "Sat nguong. Can kiem tra ky cac yeu to chua xet."
    else:
        rating = "RED"
        remark = "KHONG DAT. Tang so bu long hoac tang duong kinh."

    status = "PASSED" if overall_eta <= 1.0 else "FAILED"

    return {
        "bolt_type": f"M{bolt_d} cap {g}",
        "n_bolts": n_bolts,
        "n_shear_planes": n_shear_planes,
        "f_ub_MPa": fub,
        "alpha_v": alpha_v,
        "A_s_mm2": round(A_s, 1),
        "d0_mm": d0,
        "F_v_Rd_total_kN": round(F_v_Rd_total, 2),
        "F_b_Rd_total_kN": round(F_b_Rd_total, 2),
        "F_t_Rd_total_kN": round(F_t_Rd_total, 2),
        "eta_shear": round(eta_shear, 3),
        "eta_bearing": round(eta_bearing, 3),
        "eta_tension": round(eta_tension, 3),
        "eta_interaction": round(eta_interaction, 3),
        "overall_eta": round(overall_eta, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5575:2024",
        "Standard_Method": "TCVN 5575:2024",
        "Scope_Limitation": (
            "Lien ket chiu ep mat. "
            "CHUA kiem tra: ma sat truot gioi han, "
            "pha hoai khoi (block tearing), "
            "kha nang chiu luc cua ban ma va bung dam."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_steel_connection_tcvn(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_steel_connection_tcvn(
            bolt_d=20, grade="8.8", n_bolts=6,
            V_ed=180, F_t_ed=50,
            t_plate=12, f_u_plate=400
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
