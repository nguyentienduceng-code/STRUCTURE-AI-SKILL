import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_rc_column.py — Tinh cot BTCT nen lech tam phang theo TCVN 5574:2018
# =============================================================================
# Phien ban: TCVN 5574:2018
# Reference: Dieu 8.1.2, Dieu 8.1.4, Phu luc E (uon doc)
# =============================================================================

# --- Cuong do vat lieu TCVN 5574:2018 (MPa) ---
RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
RSC_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 400}  # Cuong do nen cot thep

# Module dan hoi ban dau cua be tong (MPa) — TCVN 5574:2018 Bang 2.7
EB_MAP = {"B15": 24000, "B20": 27500, "B25": 30000, "B30": 32500, "B35": 34500, "B40": 36000}

ALPHA_R_DEFAULT = 0.39      # STANDARDS_LOCK.md muc 3 (CB400-V)
MU_MIN_PERCENT = 0.10       # Ham luong cot thep toi thieu cho cot (%)
MU_MAX_PERCENT = 3.0        # Ham luong cot thep toi da


def calc_rc_column(b=400, h=400, a=40, a_prime=40,
                   concrete="B25", rebar="CB400-V",
                   N_ed=1200, M_ed=120,
                   L0=4200, mu_type="cantilever",
                   alpha_R=ALPHA_R_DEFAULT,
                   gamma_b=1.0):
    """
    Kiem tra cot BTCT tiet dien chu nhat chiu nen lech tam phang
    theo TCVN 5574:2018.

    Args:
        b, h           : Kich thuoc tiet dien (mm). h theo phuong uon.
        a, a_prime     : Khoang cach tu mep den trong tam cot thep (mm)
        concrete       : Cap do ben be tong (B15..B40)
        rebar          : Loai cot thep doc
        N_ed           : Luc doc truc thiet ke (kN) — nen duong
        M_ed           : Momen uon thiet ke (kNm)
        L0             : Chieu dai tinh toan cot (mm)
        mu_type        : Loai lien ket ("cantilever", "pinned_both", "fixed_both", "fixed_pinned")
        alpha_R        : Gioi han alpha_m
        gamma_b        : He so dieu kien lam viec be tong (mac dinh 1.0)

    PHAM VI: Tiet dien chu nhat, cot doi xung, nen lech tam phang.
    CHUA kiem tra: nen lech tam xien, uon doc 2 phuong, xoan.
    """
    Rb = RB_MAP.get(concrete, 14.5) * gamma_b
    Rbt = RBT_MAP.get(concrete, 1.05) * gamma_b
    Rs = RS_MAP.get(rebar, 350)
    Rsc = RSC_MAP.get(rebar, 350)
    Eb = EB_MAP.get(concrete, 30000)

    h0 = h - a
    h0_prime = h - a_prime  # khong dung truc tiep, chi de ghi nhan
    za = h0 - a_prime       # khoang cach giua 2 lop thep

    logs = []
    warnings = []
    unverified = []

    # =========================================================================
    # 1. DO LECH TAM BAN DAU
    # =========================================================================
    e0 = (M_ed * 1e3) / N_ed if N_ed > 0 else float('inf')  # mm
    e_a = max(h / 30.0, L0 / 600.0, 10.0)  # Do lech tam ngau nhien

    logs.append({
        "Step": 1,
        "Description": "Xac dinh do lech tam ban dau e0",
        "Principle": "Do lech tam = M/N, cong them lech tam ngau nhien e_a.",
        "Formula": "e0 = M_Ed / N_Ed;  e_a = max(h/30, L0/600, 10mm)",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.4", "Bang_Hinh": "", "Trang": "70", "Trich_Yeu": "Độ lệch tâm tĩnh học và độ lệch tâm ngẫu nhiên"},
        "Substitution": f"M_Ed = {M_ed} kNm, N_Ed = {N_ed} kN",
        "Result": f"e0 = {e0:.1f} mm,  e_a = {e_a:.1f} mm"
    })

    # =========================================================================
    # 2. KIEM TRA UON DOC (he so eta)
    # =========================================================================
    # TCVN 5574:2018 Phu luc E — Phuong phap don gian hoa
    # Ty so do manh: lambda = L0 / h
    lam = L0 / h

    # He so uon doc eta theo cong thuc gan dung TCVN 5574:2018
    # Khi lambda <= 14: eta = 1.0
    # Khi 14 < lambda <= 46: eta tinh theo cong thuc
    if lam <= 14:
        eta = 1.0
        eta_method = "lambda <= 14 → eta = 1.0 (khong xet uon doc)"
    elif lam <= 46:
        # Cong thuc gan dung (TCVN 5574:2018 PL E)
        # Ncr = (pi^2 * D) / L0^2;  D = Eb*Ib / (1+phi) + Es*Is
        # Don gian hoa: eta = 1 / (1 - N_Ed/Ncr)
        phi_creep = 1.0  # He so tu bien (gia dinh phi = 1.0 — co the hoi User)
        Ib = b * h**3 / 12.0  # mm4 — momen quan tinh tiet dien
        D = Eb * Ib / (1 + phi_creep)  # Nmm2
        Ncr = (math.pi**2 * D) / (L0**2) * 1e-3  # kN

        if N_ed >= Ncr:
            eta = 999.0  # Mat on dinh
            eta_method = f"N_Ed >= N_cr → COT MAT ON DINH"
            warnings.append(f"N_Ed = {N_ed} kN >= N_cr = {Ncr:.1f} kN — cot mat on dinh!")
        else:
            eta = 1.0 / (1.0 - N_ed / Ncr)
            eta_method = f"eta = 1/(1-N/Ncr) = 1/(1-{N_ed}/{Ncr:.1f}) = {eta:.3f}"
        unverified.append(f"He so tu bien phi = {phi_creep} (gia dinh). Can kiem tra theo tai trong dai han thuc te.")
    else:
        eta = 999.0
        eta_method = f"lambda = {lam:.1f} > 46 → Vuot gioi han do manh. Phai tang tiet dien."
        warnings.append(f"Ty so do manh lambda = {lam:.1f} vuot gioi han 46!")

    logs.append({
        "Step": 2,
        "Description": "Kiem tra uon doc cot (he so eta)",
        "Principle": "Cot manh bi uon phu gia tang do lech tam thuc te. eta tang momen tinh toan.",
        "Formula": "lambda = L0/h;  Ncr = pi^2*D/L0^2;  eta = 1/(1 - N_Ed/Ncr)",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Phu luc E — Uon doc", "Bang_Hinh": "", "Trang": "165", "Trich_Yeu": "Hệ số uốn dọc eta của cấu kiện chịu nén"},
        "Substitution": f"L0 = {L0} mm, h = {h} mm, lambda = {lam:.1f}",
        "Result": eta_method
    })

    # =========================================================================
    # 3. DO LECH TAM THUC TE
    # =========================================================================
    e = eta * e0 + e_a  # mm — do lech tam tang cuong
    e_prime = e + h / 2.0 - a  # khoang cach tu N den As (cot keo)

    logs.append({
        "Step": 3,
        "Description": "Tinh do lech tam thuc te (sau uon doc + ngau nhien)",
        "Principle": "Do lech tam thuc te gom: lech tam ban dau × eta + lech tam ngau nhien.",
        "Formula": "e = eta * e0 + e_a;  e' = e + h/2 - a",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.4", "Bang_Hinh": "", "Trang": "71", "Trich_Yeu": "Xác định độ lệch tâm tính toán có xét đến uốn dọc"},
        "Substitution": f"eta = {eta:.3f}, e0 = {e0:.1f} mm, e_a = {e_a:.1f} mm",
        "Result": f"e = {e:.1f} mm,  e' = {e_prime:.1f} mm"
    })

    # =========================================================================
    # 4. PHAN BIET LECH TAM LON / NHO
    # =========================================================================
    # Lech tam nho khi: e' <= 0.3*h0  (vung nen chiem toan bo tiet dien)
    is_large_ecc = (e_prime > 0.3 * h0)

    logs.append({
        "Step": 4,
        "Description": "Phan biet nen lech tam lon hay nho",
        "Principle": "Lech tam lon: cot thep keo bi keo (chay), be tong 1 phia bi nen. Lech tam nho: ca 2 phia deu bi nen.",
        "Formula": "e' > 0.3*h0 → lech tam LON;  e' <= 0.3*h0 → lech tam NHO",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.2", "Bang_Hinh": "", "Trang": "64", "Trich_Yeu": "Phân biệt trường hợp nén lệch tâm lớn và nén lệch tâm bé"},
        "Substitution": f"e' = {e_prime:.1f} mm, 0.3*h0 = {0.3*h0:.1f} mm",
        "Result": f"{'NEN LECH TAM LON' if is_large_ecc else 'NEN LECH TAM NHO'}"
    })

    # =========================================================================
    # 5. TINH COT THEP
    # =========================================================================
    As_req = 0.0
    As_prime_req = 0.0

    if is_large_ecc:
        # ----- NEN LECH TAM LON -----
        # Gia thiet x <= alpha_R * h0  (vung nen khong qua lon)
        # Can bang: N = Rb*b*x + Rsc*As' - Rs*As
        # Momen tai trong tam As: N*e' = Rb*b*x*(h0 - x/2) + Rsc*As'*(h0 - a')
        # => As' = [N*e' - Rb*b*x*(h0-x/2)] / [Rsc*(h0-a')]  voi x = alpha_R*h0

        x_max = alpha_R * h0
        # Tu phuong trinh momen:
        M_bt = Rb * b * x_max * (h0 - x_max / 2.0) * 1e-6  # kNm — kha nang be tong
        M_total = N_ed * e_prime * 1e-3  # kNm — momen yeu cau tai As

        if M_total <= M_bt:
            # Khong can cot thep nen (As' = As_min)
            # Tinh x tu: N*e' = Rb*b*x*(h0 - x/2)
            # => Rb*b*x^2/2 - Rb*b*h0*x + N*e' = 0
            A_coeff = Rb * b / 2.0
            B_coeff = -Rb * b * h0
            C_coeff = N_ed * e_prime * 1e3  # Nmm
            disc = B_coeff**2 - 4 * A_coeff * C_coeff
            if disc >= 0:
                x = (-B_coeff - math.sqrt(disc)) / (2 * A_coeff)
                x = max(x, 0)
            else:
                x = x_max
            As_prime_req = 0.0
            As_req = (Rb * b * x - N_ed * 1e3) / Rs  # mm2  (can bang luc doc)
            As_req = max(As_req, 0)
        else:
            # Can cot thep nen
            x = x_max
            As_prime_req = (N_ed * e_prime * 1e3 - Rb * b * x * (h0 - x / 2.0)) / (Rsc * za)  # mm2
            As_prime_req = max(As_prime_req, 0)
            As_req = (Rb * b * x + Rsc * As_prime_req - N_ed * 1e3) / Rs  # mm2
            As_req = max(As_req, 0)

        logs.append({
            "Step": 5,
            "Description": "Tinh cot thep doc cho nen lech tam lon",
            "Principle": "Can bang luc va momen tren tiet dien. x <= alpha_R*h0 dam bao pha hoai deo.",
            "Formula": "N*e' = Rb*b*x*(h0 - x/2) + Rsc*As'*za;  N = Rb*b*x + Rsc*As' - Rs*As",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.2 — Cau kien chiu nen lech tam", "Bang_Hinh": "", "Trang": "65", "Trich_Yeu": "Tính toán cốt thép dọc cấu kiện nén lệch tâm lớn"},
            "Substitution": f"Rb={Rb} MPa, b={b} mm, h0={h0} mm, za={za} mm, Rs={Rs} MPa, Rsc={Rsc} MPa, x={x:.1f} mm",
            "Result": f"As_yeu_cau = {As_req:.1f} mm2,  As'_yeu_cau = {As_prime_req:.1f} mm2"
        })

    else:
        # ----- NEN LECH TAM NHO -----
        # Khi e' nho: ca 2 phia deu bi nen
        # Gia thiet x = h0 (toan bo tiet dien bi nen)
        # Can bang: N*e' = Rb*b*h0*(h0/2 - ...) + Rsc*As'*za
        # Don gian hoa: cot doi xung As = As'
        # N <= Rb*b*h + 2*Rsc*As
        # => As = (N - Rb*b*h) / (2*Rsc)

        N_bt = Rb * b * h * 1e-3  # kN — kha nang nen cua rieng be tong
        if N_ed > N_bt:
            As_total = (N_ed * 1e3 - Rb * b * h) / (2.0 * Rsc)  # mm2 — moi phia
            As_total = max(As_total, 0)
        else:
            As_total = 0
        As_req = As_total
        As_prime_req = As_total

        logs.append({
            "Step": 5,
            "Description": "Tinh cot thep doc cho nen lech tam nho",
            "Principle": "Toan bo tiet dien bi nen. Bo tri cot thep doi xung 2 phia.",
            "Formula": "As = As' = (N_Ed - Rb*b*h) / (2*Rsc)",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.2", "Bang_Hinh": "", "Trang": "67", "Trich_Yeu": "Tính toán cốt thép dọc cấu kiện nén lệch tâm bé"},
            "Substitution": f"N_Ed = {N_ed} kN, Rb*b*h = {N_bt:.1f} kN",
            "Result": f"As = As' = {As_total:.1f} mm2 (moi phia)"
        })

    # =========================================================================
    # 6. KIEM TRA HAM LUONG COT THEP
    # =========================================================================
    As_min = MU_MIN_PERCENT / 100.0 * b * h  # mm2 — tong ca 2 phia
    As_max = MU_MAX_PERCENT / 100.0 * b * h

    As_chon = max(As_req, As_min / 2.0)  # moi phia >= As_min/2
    As_prime_chon = max(As_prime_req, As_min / 2.0)
    As_total = As_chon + As_prime_chon

    mu_percent = As_total / (b * h) * 100.0

    if As_total > As_max:
        warnings.append(f"Ham luong cot thep {mu_percent:.2f}% vuot gioi han {MU_MAX_PERCENT}%. Tang tiet dien cot.")

    logs.append({
        "Step": 6,
        "Description": "Kiem tra ham luong cot thep",
        "Principle": "Dam bao cot thep >= toi thieu (chong nut do co ngot) va <= toi da (dam bao do bo be tong).",
        "Formula": "mu = (As + As') / (b*h) * 100%",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 10.3.1 — Yeu cau cau tao", "Bang_Hinh": "", "Trang": "112", "Trich_Yeu": "Hàm lượng cốt thép dọc tối thiểu và tối đa trong cột"},
        "Substitution": f"As_min,tong = {As_min:.1f} mm2 ({MU_MIN_PERCENT}%), As_max,tong = {As_max:.1f} mm2 ({MU_MAX_PERCENT}%)",
        "Result": f"As_chon = {As_chon:.1f} mm2,  As'_chon = {As_prime_chon:.1f} mm2,  Tong = {As_total:.1f} mm2,  mu = {mu_percent:.2f}%"
    })

    # =========================================================================
    # 7. KIEM TRA KHA NANG CHIU LUC
    # =========================================================================
    # Kha nang chiu luc cua tiet dien voi cot thep da chon
    if is_large_ecc:
        # Tinh lai x tu can bang luc: N = Rb*b*x + Rsc*As' - Rs*As
        x_check = (N_ed * 1e3 - Rsc * As_prime_chon + Rs * As_chon) / (Rb * b)
        x_check = max(x_check, 0)
        if x_check > alpha_R * h0:
            x_check = alpha_R * h0

        M_Rd = (Rb * b * x_check * (h0 - x_check / 2.0) + Rsc * As_prime_chon * za) * 1e-6  # kNm
        N_Rd_e = M_Rd / (e_prime * 1e-3) if e_prime > 0 else float('inf')  # kN
    else:
        N_Rd_e = (Rb * b * h + 2.0 * Rsc * As_chon) * 1e-3  # kN — kha nang nen
        M_Rd = N_Rd_e * e_prime * 1e-3  # kNm

    eta_N = N_ed / N_Rd_e if N_Rd_e > 0 else 999
    eta_overall = eta_N

    status = "PASSED" if eta_overall <= 1.0 else "FAILED"
    if eta_overall <= 0.70:
        rating = "GREEN"
    elif eta_overall <= 0.90:
        rating = "YELLOW"
    elif eta_overall <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    logs.append({
        "Step": 7,
        "Description": "Kiem tra kha nang chiu luc cua tiet dien",
        "Principle": "Cot thep da chon phai dam bao kha nang chiu luc >= noi luc thiet ke.",
        "Formula": "eta = N_Ed / N_Rd (quy doi ve luc doc)",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.2", "Bang_Hinh": "", "Trang": "66", "Trich_Yeu": "Kiểm tra độ bền tiết diện chịu nén lệch tâm"},
        "Substitution": f"N_Ed = {N_ed} kN, N_Rd = {N_Rd_e:.1f} kN",
        "Result": f"eta = {eta_overall:.3f} → {status}",
        "Utilization": f"eta = {eta_overall:.3f}"
    })

    # =========================================================================
    # 8. TONG HOP
    # =========================================================================
    return {
        "section": f"bxh = {b}x{h} mm",
        "concrete": concrete,
        "rebar": rebar,
        "Rb_MPa": Rb,
        "Rs_MPa": Rs,
        "Rsc_MPa": Rsc,
        "Eb_MPa": Eb,
        "h0_mm": h0,
        "za_mm": za,
        "N_ed_kN": N_ed,
        "M_ed_kNm": M_ed,
        "e0_mm": round(e0, 1),
        "e_a_mm": round(e_a, 1),
        "lambda": round(lam, 1),
        "eta_uon_doc": round(eta, 3),
        "e_mm": round(e, 1),
        "e_prime_mm": round(e_prime, 1),
        "eccentricity_type": "LARGE" if is_large_ecc else "SMALL",
        "As_req_mm2": round(As_req, 1),
        "As_prime_req_mm2": round(As_prime_req, 1),
        "As_chon_mm2": round(As_chon, 1),
        "As_prime_chon_mm2": round(As_prime_chon, 1),
        "As_total_mm2": round(As_total, 1),
        "mu_percent": round(mu_percent, 2),
        "N_Rd_kN": round(N_Rd_e, 1),
        "eta_N": round(eta_N, 3),
        "overall_eta": round(eta_overall, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": (
            "Tiet dien chu nhat, cot doi xung, nen lech tam phang. "
            "CHUA kiem tra: nen lech tam xien (2 phuong), xoan, "
            "tiet dien tron, tiet dien chu L/T."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_rc_column(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # Sample: Cot 400x400, B25, CB400-V, N=1200kN, M=120kNm, L0=4.2m
        sample = calc_rc_column(
            b=400, h=400, a=40, a_prime=40,
            concrete="B25", rebar="CB400-V",
            N_ed=1200, M_ed=120, L0=4200
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
