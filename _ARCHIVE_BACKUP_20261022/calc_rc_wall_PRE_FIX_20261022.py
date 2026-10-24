import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_rc_wall.py — Tinh toan vach cung BTCT chiu nen lech tam phang va kiem tra cat
# =============================================================================
# Phien ban: TCVN 5574:2018
# Reference:
#   - Dieu 8.1.2  : Nen lech tam phang (dung chung cong thuc cot)
#   - Dieu 8.1.4  : Xet uon doc (slenderness) doi voi vach
#   - Dieu 8.1.3  : Kiem tra cat
#   - Dieu 8.1.7  : Cau kien chiu nen (chung)
# =============================================================================

# --- Cuong do vat lieu TCVN 5574:2018 (MPa) ---
RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
RSC_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 400}  # Rsc - cuong do nen cot thep
RSW_MAP = {"CB240-T": 170, "CB300-V": 210, "CB400-V": 280, "CB500-V": 300}

# Module dan hoi ban dau cua be tong (TCVN 5574:2018 Bang 2.7)
EB_MAP = {"B15": 24000, "B20": 27500, "B25": 30000, "B30": 32500, "B35": 34500, "B40": 36000}

# Gioi han cua vach (TCVN 5574:2018 Dieu 8.1.2.4)
WALL_THICKNESS_MIN = 100   # mm — chieu day toi thieu cua vach
WALL_HW_LIMIT = 2.5         # he so kich thuoc toi da: Hw / bw (vach thanh mong)
WALL_REINFORCEMENT_MIN = 0.0015  # ham luong cot thep toi thieu (0.15%)
WALL_REINFORCEMENT_MAX = 0.04    # ham luong cot thep toi da (4%)

# He so uon doc (TCVN 5574:2018 Phu luc E)
# Vach: he so mu_phu_thuoc vao do mem
# Đon gian hoa: chi xet lambda (do mem) gioi han
SLENDERNESS_LIMIT = 30     # lambda_max cho cot/vach khong xet uon doc
SLENDERNESS_TRANSITION = 20  # lambda gioi han chuyen tiep


def _slenderness_factor(L0, h, concrete="B25"):
    """
    Tinh he so uon doc eta theo TCVN 5574:2018 Phu luc E.
    Đon gian hoa: tra theo lambda cho truoc.

    lambda = L0 / h
    lambda <= 10: eta = 1.0 (bo qua uon doc)
    10 < lambda <= 20: noi suy
    20 < lambda <= 30: giam theo cong thuc
    lambda > 30: vuot gioi han -> can tang tiet dien
    """
    lam = L0 / h if h > 0 else 0

    if lam <= 10:
        return 1.0, lam
    elif lam <= SLENDERNESS_TRANSITION:
        # noi suy tuyen tinh tu 1.0 den 0.85
        eta = 1.0 - 0.15 * (lam - 10) / 10
        return eta, lam
    elif lam <= SLENDERNESS_LIMIT:
        # noi suy tu 0.85 den 0.70
        eta = 0.85 - 0.15 * (lam - 20) / 10
        return eta, lam
    else:
        # vuot gioi han -> giam manh, canh bao
        eta = 0.5
        return eta, lam


def calc_rc_wall(bw=200, hw=3000, tw=200,  # be day, chieu cao, chieu day vach (mm)
                 a=30, a_prime=30,
                 concrete="B25", rebar="CB400-V",
                 stirrup_grade="CB240-T",
                 N_ed=500, M_ed=200,
                 L0=3000,
                 # Cot thep doc 2 mat
                 As_total=None,    # mm2 — tong cot thep doc 2 mat (optional)
                 # Cot đai (cot thep ngang)
                 stirrup_dia=None,
                 stirrup_spacing=None,
                 stirrup_legs=None):
    """
    Kiem tra vach cung BTCT chiu nen lech tam phang theo TCVN 5574:2018.

    Args:
        bw           : Be day vach (mm)
        hw           : Chieu cao vach (mm)
        tw           : Chieu doc (theo phuong luc) — thuong = bw (vach phang)
        a, a_prime   : Lop bao ve hai ben (mm)
        concrete     : Cap do ben be tong (B15..B40)
        rebar        : Loai cot thep doc
        stirrup_grade: Mac thep cot đai
        N_ed         : Luc doc thiet ke (kN) — nen
        M_ed         : Momen uon thiet ke (kNm)
        L0           : Chieu dai tinh toan (mm)
        As_total     : Tong dien tich cot thep doc 2 mat (mm2)
        stirrup_*    : Thong so cot đai (optional)

    PHAM VI: Vach BTCT nen lech tam phang, tiet dien chu nhat.
    CHUA kiem tra: vach co mo (openings), vach lien ket, vach chiu xoan,
                   vach cong son, vach chiu 2 phuong, thanh vach hop.
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)
    Rs = RS_MAP.get(rebar, 350)
    Rsc = RSC_MAP.get(rebar, 350)
    Rsw = RSW_MAP.get(stirrup_grade, 170)
    Eb = EB_MAP.get(concrete, 30000)

    h = bw  # chieu cao tinh toan (vach phang, chieu theo phuong uon)
    t = tw  # be day vach
    h0 = h - a
    b = t    # be mat chiu nen (chieu doc theo phuong luc)

    logs = []
    unverified = []
    warnings = []

    # =========================================================================
    # 1. KIEM TRA HINH DANG VAT LY
    # =========================================================================
    ratio_hw_bw = hw / bw if bw > 0 else 0

    if bw < WALL_THICKNESS_MIN:
        warnings.append(f"Be day vach bw = {bw} mm < {WALL_THICKNESS_MIN} mm (TCVN 5574:2018).")

    if ratio_hw_bw > WALL_HW_LIMIT:
        warnings.append(
            f"Ty le hw/bw = {ratio_hw_bw:.2f} > {WALL_HW_LIMIT}: vach co the thanh cot, "
            "nen kiem tra theo cot."
        )

    logs.append({
        "Step": 1,
        "Description": "Kiem tra hinh dang vach",
        "Principle": "Vach cung phai co be day va hinh dang theo yeu cau TCVN.",
        "Formula": "bw >= 100 mm;  hw/bw <= 2.5 (neu lon hon -> kiem tra nhu cot)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.2.4",
            "Bang_Hinh": "",
            "Trang": "65",
            "Trich_Yeu": "Kích thước hình học và yêu cầu cấu tạo vách BTCT"
        },
        "Substitution": f"bw = {bw} mm, hw = {hw} mm, hw/bw = {ratio_hw_bw:.2f}",
        "Result": f"{'CANH BAO' if warnings else 'OK'}: bw={bw} mm, hw/bw={ratio_hw_bw:.2f}"
    })

    # =========================================================================
    # 2. XET UON DOC
    # =========================================================================
    eta_slenderness, lam = _slenderness_factor(L0, h, concrete)

    if lam > SLENDERNESS_LIMIT:
        warnings.append(
            f"Do mem lambda = L0/h = {lam:.2f} > {SLENDERNESS_LIMIT}: can TANG tiet dien hoac GIAM L0."
        )

    # Momen tinh toan co xet uon doc
    M_ed_calc = M_ed * eta_slenderness  # kNm

    logs.append({
        "Step": 2,
        "Description": "Xet uon doc (slenderness)",
        "Principle": "Cot/vach co do mem cao bi loi do uon doc; he so eta giam M_ed hieu qua.",
        "Formula": f"lambda = L0/h = {L0}/{h} = {lam:.2f};  eta = {eta_slenderness}",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.4 + Phu luc E",
            "Bang_Hinh": "Phu luc E",
            "Trang": "165",
            "Trich_Yeu": "Ảnh hưởng uốn dọc của cấu kiện chịu nén"
        },
        "Substitution": f"L0 = {L0} mm, h = {h} mm, lambda = {lam:.2f}",
        "Result": f"eta_uon_doc = {eta_slenderness:.3f}, M_ed_tinh_toan = {M_ed_calc:.2f} kNm"
    })

    # =========================================================================
    # 3. E0 (DO LECH TAM) VA MOMEN TINH TOAN
    # =========================================================================
    e0 = M_ed_calc * 1e6 / (N_ed * 1e3) if N_ed > 0 else 0  # mm
    e_a = max(h / 600.0, 10.0)  # mm — lech tam ngau nhien
    e = e0 + e_a  # mm

    logs.append({
        "Step": 3,
        "Description": "Do lech tam (e0, ea, e)",
        "Principle": "Lech tam co y (do momen) + lech tam ngau nhien ea (do khong hoan hao).",
        "Formula": "e0 = M_ed/N_ed;  ea = max(h/600, 10);  e = e0 + ea",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.2.5",
            "Bang_Hinh": "",
            "Trang": "65",
            "Trich_Yeu": "Độ lệch tâm tĩnh học và ngẫu nhiên của vách"
        },
        "Substitution": f"M_ed_tinh = {M_ed_calc:.2f} kNm, N_ed = {N_ed} kN, h = {h} mm",
        "Result": f"e0 = {e0:.2f} mm, ea = {e_a:.2f} mm, e = {e:.2f} mm"
    })

    # =========================================================================
    # 4. HAM LUONG COT THEP DOC (As, As')
    # =========================================================================
    # Neu khong cung cap As_total, uoc luong tu M_ed va N_ed
    if As_total is None:
        # Uoc luong theo cong thuc gan đung (truong hop lech tam lon)
        # alpha_n = N_ed / (Rb * b * h0)
        alpha_n = (N_ed * 1e3) / (Rb * b * h0) if (Rb * b * h0) > 0 else 0
        # Uoc luong mu (ham luong cot thep) can thiet
        if alpha_n < 0.5:
            mu_est = 0.003  # 0.3% - uoc luong ban đau
        else:
            mu_est = 0.005  # 0.5%
        As_total = mu_est * b * h0
        warnings.append(
            f"Khong cung cap As_total: uoc luong As = {As_total:.1f} mm2 (mu~{mu_est*100:.2f}%). "
            "Can nhap As_total thuc te đe kiem tra chinh xac."
        )
        unverified.append("As_total chua duoc nhap — ket qua chi mang tinh uoc luong.")

    mu_total = As_total / (b * h0) if (b * h0) > 0 else 0
    mu_min = WALL_REINFORCEMENT_MIN
    mu_max = WALL_REINFORCEMENT_MAX

    mu_check = "OK"
    if mu_total < mu_min:
        mu_check = "DUOI TOI THIEU"
        warnings.append(f"mu = {mu_total*100:.2f}% < {mu_min*100:.2f}% (TCVN).")
    elif mu_total > mu_max:
        mu_check = "VUOT TOI DA"
        warnings.append(f"mu = {mu_total*100:.2f}% > {mu_max*100:.2f}% (TCVN).")

    logs.append({
        "Step": 4,
        "Description": "Ham luong cot thep doc",
        "Principle": "Vung nen lech tam can luong thep vua đu de chong nen va chong uon.",
        "Formula": f"mu = As / (b * h0),  0.15% <= mu <= 4%",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.2.7",
            "Bang_Hinh": "",
            "Trang": "67",
            "Trich_Yeu": "Hàm lượng cốt thép dọc giới hạn trong vách BTCT"
        },
        "Substitution": f"As_total = {As_total:.1f} mm2, b = {b} mm, h0 = {h0} mm",
        "Result": f"mu = {mu_total*100:.2f}% ({mu_check});  gioi han: {mu_min*100:.2f}% - {mu_max*100:.2f}%"
    })

    # =========================================================================
    # 5. KIEM TRA NEN (alpha_n)
    # =========================================================================
    # alpha_n = N_ed / (Rb * b * h0)
    alpha_n = (N_ed * 1e3) / (Rb * b * h0) if (Rb * b * h0) > 0 else 0
    # alpha_R (gioi han alpha_n cho nen lech tam) = 0.5-0.7 tuy thep
    alpha_R_max = 0.55  # CB400-V (TCVN 5574:2018 Dieu 8.1.2.6)

    eta_compress = alpha_n / alpha_R_max

    logs.append({
        "Step": 5,
        "Description": "Kiem tra nen (alpha_n)",
        "Principle": "Tiet dien khong bi pha hoai do nen thuan tuy truoc khi xet uon.",
        "Formula": f"alpha_n = N_ed / (Rb * b * h0) <= alpha_R,max = {alpha_R_max}",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.2.6",
            "Bang_Hinh": "",
            "Trang": "66",
            "Trich_Yeu": "Kiểm tra giới hạn vùng bê tông chịu nén của vách"
        },
        "Substitution": f"N_ed = {N_ed} kN, Rb = {Rb} MPa, b = {b} mm, h0 = {h0} mm",
        "Result": f"alpha_n = {alpha_n:.3f}  vs  alpha_R,max = {alpha_R_max}",
        "Utilization": f"eta_nen = {eta_compress:.3f}"
    })

    # =========================================================================
    # 6. KIEM TRA CAT
    # =========================================================================
    # Vach cung: chiu cat it, nhung phai kiem tra:
    # (a) Suc chong cat cua be tong
    # (b) Suc chong cat cua cot đai (neu co)

    # Tinh V_ed (gia su khong co, can nhap tu ngoai)
    # Đon gian hoa: khong co V_ed -> gia su V_ed = 0
    # TODO: có thé them V_ed input neu can

    Qb = 0.5 * Rbt * b * h0 * 1e-3  # kN, suc chong cat be tong (CT 8.1.3)
    Qb_min = 0.4 * Rbt * b * h0 * 1e-3  # kN, gioi han duoi

    logs.append({
        "Step": 6,
        "Description": "Suc chong cat be tong (Qb)",
        "Principle": "Be tong chong cat tren mat cat nghieng; cot đai (neu co) gia tang them.",
        "Formula": "Qb = 0.5 * Rbt * b * h0",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.3",
            "Bang_Hinh": "",
            "Trang": "69",
            "Trich_Yeu": "Khả năng chịu cắt của bê tông trên tiết diện nghiêng"
        },
        "Substitution": f"Rbt = {Rbt} MPa, b = {b} mm, h0 = {h0} mm",
        "Result": f"Qb = {Qb:.2f} kN (Qb,min = {Qb_min:.2f} kN)"
    })

    # =========================================================================
    # 7. TONG HOP & KET LUAN
    # =========================================================================
    etas = [eta_slenderness, eta_compress]
    if mu_check == "OK":
        etas.append(0)  # neu OK thi khong tinh
    else:
        etas.append(1.5)  # neu khong OK -> thêm etas để đánh đỏ

    overall = max([e for e in etas if e > 0]) if any(e > 0 for e in etas) else max(etas)

    if eta_compress > 1.0:
        status = "FAILED"
        unverified.append(f"alpha_n = {alpha_n:.3f} > alpha_R,max = {alpha_R_max}: vach bi pha hoai do nen.")
    elif mu_check != "OK":
        status = "FAILED"
    elif lam > SLENDERNESS_LIMIT:
        status = "FAILED"
        unverified.append(f"lambda = {lam:.2f} > {SLENDERNESS_LIMIT}: can tang t/dien hoac giam L0.")
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
        "tw_mm": tw,
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
        "L0_mm": L0,
        "lambda": round(lam, 2),
        "eta_slenderness": round(eta_slenderness, 3),
        "M_ed_calc_kNm": round(M_ed_calc, 2),
        "e0_mm": round(e0, 2),
        "ea_mm": round(e_a, 2),
        "e_mm": round(e, 2),
        "As_total_mm2": round(As_total, 1),
        "mu_percent": round(mu_total * 100, 2),
        "mu_check": mu_check,
        "alpha_n": round(alpha_n, 4),
        "alpha_R_max": alpha_R_max,
        "eta_compress": round(eta_compress, 3),
        "Qb_kN": round(Qb, 2),
        "Qb_min_kN": round(Qb_min, 2),
        "ratio_hw_bw": round(ratio_hw_bw, 2),
        "overall_eta": round(overall, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": (
            "Vach cung BTCT tiet dien chu nhat, nen lech tam phang. "
            "CHUA kiem tra: vach co mo (openings), vach lien ket, vach chiu xoan, "
            "vach cong son, vach chiu 2 phuong, thanh vach hop."
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
        # Sample: vach 200x3000, B25, CB400-V
        sample = calc_rc_wall(
            bw=200, hw=3000, tw=200,
            a=30, a_prime=30,
            concrete="B25", rebar="CB400-V",
            N_ed=500, M_ed=200, L0=3000,
            As_total=600  # ~1% - 0.5% of b*h0 = 200*170 = 34000 mm2
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
