import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_weld_tcvn.py — Tinh duong han goc va doi dau theo TCVN 5575:2024
# =============================================================================
# Phien ban: TCVN 5575:2024
# Reference: Dieu 11.2 (han goc), Dieu 11.1 (han doi dau), Bang 11.1–11.4
# =============================================================================

from pathlib import Path
for _p in Path(__file__).resolve().parents:
    if (_p / "_SHARED" / "standards" / "tables.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

try:
    from _SHARED.standards.tables import GAMMA_M0, GAMMA_MW
except ImportError:
    GAMMA_M0 = 1.05      # He so tin cay vat lieu (ben tiet dien)
    GAMMA_MW = 1.25       # He so tin cay moi han

# --- Cuong do tinh toan moi han goc (MPa) theo TCVN 5575:2024 Bang 11.2 ---
# Phu thuoc vao phuong phap han va cap do ben thep
# Gia tri theo: Cuong do chiu cat qua mat cat kim loai moi han (Rwf)
#               Cuong do chiu cat qua mat cat bien nong chay (Rwz)
RWF_MAP = {
    "C38": {"manual": 180, "auto": 180},
    "C42": {"manual": 180, "auto": 200},
    "C46": {"manual": 200, "auto": 215},
    "C50": {"manual": 215, "auto": 230},
    "C52": {"manual": 215, "auto": 240},
    "E42": {"manual": 180, "auto": 200},
    "E46": {"manual": 200, "auto": 215},
    "E50": {"manual": 215, "auto": 230},
}

# Cuong do tinh toan qua mat cat bien nong chay Rwz (MPa)
# Lay = 0.45*fu cua thep co ban (don gian hoa theo TCVN 5575:2024)
FU_STEEL_MAP = {
    "CT34": 340, "CT38": 380, "CT42": 420,
    "09G2S": 490, "10G2S1": 490, "14G2": 460,
    "CCT34": 340, "CCT38": 380, "CCT42": 420,
}

# He so chieu sau tinh toan moi han
BETA_F = 0.7   # He so beta_f — qua mat cat kim loai moi han
BETA_Z = 1.0   # He so beta_z — qua mat cat bien nong chay


def calc_fillet_weld(weld_type="fillet",
                     weld_length=200, weld_leg=6, n_welds=2,
                     F_ed=150, M_ed=0,
                     electrode="E42", welding_method="auto",
                     steel_grade="CT38",
                     beta_f=BETA_F, beta_z=BETA_Z):
    """
    Kiem tra duong han goc chiu luc theo TCVN 5575:2024.

    Args:
        weld_type       : "fillet" (han goc) hoac "butt" (han doi dau)
        weld_length     : Chieu dai duong han (mm) — chua tru 2*kf
        weld_leg        : Canh duong han kf (mm)
        n_welds         : So luong duong han (2 = 2 ben)
        F_ed            : Luc tac dung (kN) — cat hoac keo
        M_ed            : Momen (kNm) — neu co (tac dung len nhom han)
        electrode       : Que han (E42, E46, C42, ...)
        welding_method  : "manual" hoac "auto"
        steel_grade     : Mac thep co ban (CT34, CT38, 09G2S, ...)
        beta_f          : He so beta_f (mac dinh 0.7)
        beta_z          : He so beta_z (mac dinh 1.0)

    PHAM VI: Han goc chiu cat/keo doc truc hoac ngang.
    CHUA kiem tra: Han goc chiu luc phuc tap (cat + uon + xoan dong thoi),
                   han diem, han noi cap voi.
    """
    logs = []
    warnings = []
    unverified = []

    # =========================================================================
    # 1. XAC DINH CUONG DO MOI HAN
    # =========================================================================

    # Rwf — cuong do qua mat cat kim loai moi han
    electrode_key = electrode.upper()
    if electrode_key in RWF_MAP:
        Rwf = RWF_MAP[electrode_key].get(welding_method, 180)
    else:
        Rwf = 180
        unverified.append(f"Khong tim thay que han '{electrode}' trong bang. Dung Rwf = 180 MPa (thien ve an toan).")

    # Rwz — cuong do qua mat cat bien nong chay
    steel_key = steel_grade.upper()
    fu_steel = FU_STEEL_MAP.get(steel_key, 380)
    Rwz = 0.45 * fu_steel  # MPa — don gian hoa

    logs.append({
        "Step": 1,
        "Description": "Xac dinh cuong do tinh toan moi han",
        "Principle": "Kiem tra 2 mat cat: qua kim loai moi han (Rwf) va qua bien nong chay (Rwz).",
        "Formula": "Rwf tra bang theo que han;  Rwz = 0.45 * fu (thep co ban)",
        "Citation": {
            "Ma_TC": "TCVN 5575", "Nam": "2024",
            "Dieu_Muc": "Dieu 11.2", "Bang_Hinh": "Bang 11.2",
            "Trang": "158", "Trich_Yeu": "Cuong do tinh toan moi han goc"
        },
        "Substitution": f"Que han: {electrode} ({welding_method}), Thep: {steel_grade} (fu = {fu_steel} MPa)",
        "Result": f"Rwf = {Rwf} MPa,  Rwz = {Rwz:.0f} MPa"
    })

    # =========================================================================
    # 2. TINH DIEN TICH MAT CAT MOI HAN
    # =========================================================================

    # Chieu dai tinh toan: tru 2*kf (theo TCVN 5575:2024)
    Lw = weld_length - 2.0 * weld_leg  # mm
    if Lw < 40:
        Lw = max(Lw, 40)
        warnings.append(f"Chieu dai han tinh toan = {Lw:.0f} mm < 40 mm. Kiem tra lai chieu dai thuc te.")

    # Kiem tra chieu dai toi da (85*beta_f*kf)
    Lw_max = 85 * beta_f * weld_leg
    if Lw > Lw_max:
        warnings.append(f"Chieu dai han {Lw:.0f} mm vuot gioi han {Lw_max:.0f} mm (85*beta_f*kf). Can giam he so.")

    # Dien tich mat cat tinh toan
    Awf = beta_f * weld_leg * Lw * n_welds   # mm2 — qua KL moi han
    Awz = beta_z * weld_leg * Lw * n_welds   # mm2 — qua bien nong chay

    logs.append({
        "Step": 2,
        "Description": "Tinh dien tich mat cat tinh toan moi han",
        "Principle": "Chieu dai tinh toan tru 2*kf. Dien tich = beta * kf * Lw.",
        "Formula": "Lw = L_han - 2*kf;  Awf = beta_f * kf * Lw * n;  Awz = beta_z * kf * Lw * n",
        "Citation": {
            "Ma_TC": "TCVN 5575", "Nam": "2024",
            "Dieu_Muc": "Dieu 11.2.3", "Bang_Hinh": "",
            "Trang": "160", "Trich_Yeu": "Dien tich tinh toan duong han goc"
        },
        "Substitution": f"L_han = {weld_length} mm, kf = {weld_leg} mm, n = {n_welds}, beta_f = {beta_f}, beta_z = {beta_z}",
        "Result": f"Lw = {Lw:.0f} mm, Awf = {Awf:.1f} mm2, Awz = {Awz:.1f} mm2"
    })

    # =========================================================================
    # 3. KIEM TRA QUA MAT CAT KIM LOAI MOI HAN
    # =========================================================================
    tau_wf = (F_ed * 1e3) / Awf if Awf > 0 else 999  # MPa
    Rwf_design = Rwf / GAMMA_MW
    eta_wf = tau_wf / Rwf_design if Rwf_design > 0 else 999

    logs.append({
        "Step": 3,
        "Description": "Kiem tra ung suat qua mat cat kim loai moi han",
        "Principle": "Luc cat phan bo deu tren dien tich mat cat KL moi han.",
        "Formula": "tau_wf = F_Ed / Awf;  [tau] = Rwf / gamma_Mw",
        "Citation": {
            "Ma_TC": "TCVN 5575", "Nam": "2024",
            "Dieu_Muc": "Dieu 11.2.4", "Bang_Hinh": "",
            "Trang": "161", "Trich_Yeu": "Kiem tra ben moi han goc"
        },
        "Substitution": f"F_Ed = {F_ed} kN, Awf = {Awf:.1f} mm2, Rwf = {Rwf} MPa, gamma_Mw = {GAMMA_MW}",
        "Result": f"tau_wf = {tau_wf:.2f} MPa  vs  [tau] = {Rwf_design:.2f} MPa",
        "Utilization": f"eta_wf = {eta_wf:.3f} ({eta_wf*100:.1f}%)"
    })

    # =========================================================================
    # 4. KIEM TRA QUA MAT CAT BIEN NONG CHAY
    # =========================================================================
    tau_wz = (F_ed * 1e3) / Awz if Awz > 0 else 999  # MPa
    Rwz_design = Rwz / GAMMA_MW
    eta_wz = tau_wz / Rwz_design if Rwz_design > 0 else 999

    logs.append({
        "Step": 4,
        "Description": "Kiem tra ung suat qua mat cat bien nong chay",
        "Principle": "Be mat tiep xuc giua KL moi han va thep co ban cung co the bi pha hoai.",
        "Formula": "tau_wz = F_Ed / Awz;  [tau] = Rwz / gamma_Mw",
        "Citation": {
            "Ma_TC": "TCVN 5575", "Nam": "2024",
            "Dieu_Muc": "Dieu 11.2.4", "Bang_Hinh": "",
            "Trang": "161", "Trich_Yeu": "Kiem tra ben moi han goc qua bien nong chay"
        },
        "Substitution": f"F_Ed = {F_ed} kN, Awz = {Awz:.1f} mm2, Rwz = {Rwz:.0f} MPa, gamma_Mw = {GAMMA_MW}",
        "Result": f"tau_wz = {tau_wz:.2f} MPa  vs  [tau] = {Rwz_design:.2f} MPa",
        "Utilization": f"eta_wz = {eta_wz:.3f} ({eta_wz*100:.1f}%)"
    })

    # =========================================================================
    # 5. KIEM TRA CANH HAN TOI THIEU / TOI DA
    # =========================================================================
    # TCVN 5575:2024 Bang 11.4
    # kf_min phu thuoc t_max (be day lon nhat)
    # Don gian: kf >= 4mm khi t >= 4mm, kf <= 1.2*t_min
    kf_min = 4  # mm (mac dinh)
    kf_ok = weld_leg >= kf_min

    logs.append({
        "Step": 5,
        "Description": "Kiem tra canh han kf toi thieu",
        "Principle": "Canh han qua nho se khong dam bao chay thau. Qua lon se gay ung suat nhiet.",
        "Formula": "kf >= kf_min (tra bang theo be day ban thep)",
        "Citation": {
            "Ma_TC": "TCVN 5575", "Nam": "2024",
            "Dieu_Muc": "Dieu 11.2.1", "Bang_Hinh": "Bang 11.4",
            "Trang": "159", "Trich_Yeu": "Canh duong han goc toi thieu"
        },
        "Substitution": f"kf = {weld_leg} mm, kf_min = {kf_min} mm",
        "Result": f"{'DAT' if kf_ok else 'KHONG DAT — Tang kf'}"
    })

    if not kf_ok:
        warnings.append(f"Canh han kf = {weld_leg} mm < kf_min = {kf_min} mm")

    # =========================================================================
    # 6. KET LUAN
    # =========================================================================
    overall_eta = max(eta_wf, eta_wz)
    status = "PASSED" if overall_eta <= 1.0 else "FAILED"

    if overall_eta <= 0.70:
        rating = "GREEN"
    elif overall_eta <= 0.90:
        rating = "YELLOW"
    elif overall_eta <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    controlling = "mat_cat_KL_moi_han" if eta_wf >= eta_wz else "mat_cat_bien_nong_chay"

    return {
        "weld_type": weld_type,
        "electrode": electrode,
        "welding_method": welding_method,
        "steel_grade": steel_grade,
        "weld_length_mm": weld_length,
        "weld_leg_kf_mm": weld_leg,
        "n_welds": n_welds,
        "Lw_mm": round(Lw, 0),
        "Rwf_MPa": Rwf,
        "Rwz_MPa": round(Rwz, 0),
        "Awf_mm2": round(Awf, 1),
        "Awz_mm2": round(Awz, 1),
        "tau_wf_MPa": round(tau_wf, 2),
        "tau_wz_MPa": round(tau_wz, 2),
        "eta_wf": round(eta_wf, 3),
        "eta_wz": round(eta_wz, 3),
        "overall_eta": round(overall_eta, 3),
        "controlling_check": controlling,
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5575:2024",
        "Standard_Method": "TCVN 5575:2024",
        "Scope_Limitation": (
            "Han goc chiu cat/keo don. "
            "CHUA kiem tra: han doi dau, luc phuc tap (cat + uon + xoan dong thoi), "
            "han diem, han noi cap voi, moi (fatigue)."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_fillet_weld(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # Sample: Han goc 2 ben, kf=6mm, L=200mm, F=150kN
        sample = calc_fillet_weld(
            weld_length=200, weld_leg=6, n_welds=2,
            F_ed=150,
            electrode="E42", welding_method="auto",
            steel_grade="CT38"
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
