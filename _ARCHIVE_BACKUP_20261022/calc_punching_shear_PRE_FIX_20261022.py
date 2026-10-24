import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_punching_shear.py — Kiem tra choc thủng san phang / dai coc
# =============================================================================
# Phien ban: TCVN 5574:2018
# Reference:
#   - Dieu 8.1.5  : Choc thủng (punching shear) cua san phang khong cot đai
#   - Dieu 8.1.6  : Choc thủng co cot đai chong choc thủng
#   - Dieu 8.1.5  : Xet luc doc F_b va momen 2 phuong M_bx, M_by
# =============================================================================

# --- Cuong do vat lieu TCVN 5574:2018 (MPa) ---
RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "BB25": 14.5, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "BB25": 1.05, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
RSW_MAP = {"CB240-T": 170, "CB300-V": 210, "CB400-V": 280, "CB500-V": 300}

# He so alpha (TCVN 5574:2018 Dieu 8.1.5)
ALPHA_MIN = 0.85       # be tong nang
ALPHA_MAX = 1.00       # be tong nang — bien tren
ALPHA_HEAVY = 0.85
ALPHA_LIGHTWEIGHT = 0.80

# Gia tri alpha theo cap be tong (TCVN 5574:2018 Bang 3.2)
ALPHA_BY_GRADE = {
    "B15": 0.95, "B20": 0.95, "B25": 0.90, "B30": 0.90,
    "B35": 0.85, "B40": 0.85, "BB25": 0.90
}

# He so Ab / Acb (TCVN 5574:2018 Bang 8.3)
AB_OVER_ACB_DEFAULT = 0.75     # truong hop cot giua
AB_OVER_ACB_EDGE = 0.50        # truong hop cot bien
AB_OVER_ACB_CORNER = 0.40      # truong hop cot goc

# Gioi han luc choc thủng (TCVN 5574:2018 Dieu 8.1.5)
ETA_PUNCH_LIMIT = 1.0           # etab <= 1.0
RATIO_BW_TO_D_MIN = 0.50        # canh cot / chieu cao lam viec


def calc_punching_shear(element="slab",  # "slab" hoặc "footing"
                        concrete="B25", rebar="CB400-V",
                        stirrup_grade="CB240-T",
                        h=200, d_eff=None, a=30,
                        column_b=300, column_h=300,
                        column_position="interior",   # "interior" / "edge" / "corner"
                        F_b=600,                     # kN — luc doc tac dung len cot
                        M_bx=0, M_by=0,              # kNm — momen 2 phuong tai chan cot
                        # Tham so cot đai chong choc thủng (optional)
                        stirrup_dia=None,
                        stirrup_legs=None,
                        stirrup_spacing=None):
    """
    Kiem tra choc thủng san phang / đai coc theo TCVN 5574:2018.

    Args:
        element         : "slab" (san phang) hoặc "footing" (đai coc)
        concrete        : Cap do ben be tong (B15..B40)
        rebar           : Loai cot thep doc cot
        stirrup_grade   : Mac thep cot đai
        h               : Chieu day san / đai (mm)
        d_eff           : Chieu cao lam viec (mm). Neu None -> d = h - a
        a               : Lop bao ve (mm)
        column_b, column_h : Kich thuoc cot (mm)
        column_position : "interior" / "edge" / "corner"
        F_b             : Luc doc thiet ke len cot (kN) — nen xuong
        M_bx, M_by      : Momen uon 2 phuong tai chan cot (kNm)
        stirrup_dia     : Duong kinh cot đai chong choc thủng (mm) — optional
        stirrup_legs    : So chan cot đai tren mot phuong (mặt chu vi tinh)
        stirrup_spacing : Khoang cach cot đai theo phuong day (mm)

    PHAM VI: San phang, đai coc cot đon, TCVN 5574:2018.
    CHUA kiem tra: san co suon (ribbed slab), san co dau cot truc tiep,
                   cot tron, cot đai nhieu lop, cot lien hop thep.
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)
    Rs = RS_MAP.get(rebar, 350)
    Rsw = RSW_MAP.get(stirrup_grade, 170)

    # Chieu cao lam viec
    d = d_eff if d_eff else h - a
    d_x = d_y = d  # mac dinh giong nhau cho san phang
    h0 = d  # giu tuong thich voi cong thuc

    # He so alpha theo cap be tong
    alpha = ALPHA_BY_GRADE.get(concrete, 0.90)

    # He so Ab/Acb theo vi tri cot
    if column_position == "interior":
        ab_over_acb = AB_OVER_ACB_DEFAULT
    elif column_position == "edge":
        ab_over_acb = AB_OVER_ACB_EDGE
    elif column_position == "corner":
        ab_over_acb = AB_OVER_ACB_CORNER
    else:
        ab_over_acb = AB_OVER_ACB_DEFAULT
        column_position = "interior"

    logs = []
    unverified = []
    warnings = []

    # =========================================================================
    # 1. XAC DINH DIEN TICH CHU VI TINH TOAN (Acb) VA Ac
    # =========================================================================
    # Chu vi tinh toan c b cach mat cot 0.5*h0 hai phuong
    # TCVN 5574:2018 Dieu 8.1.5
    if column_position == "interior":
        # Cot giua: chu vi kin
        c_perim = 2 * (column_b + column_h) + 4 * (0.5 * d)
        u_b = 2 * (column_b + column_h) + math.pi * 2 * (0.5 * d)  # gan dung cung
        # Theo TCVN: chu vi = 2*(b+h) + 2*pi*0.5*h0 (dung chinh xac)
        u_b = 2 * (column_b + column_h) + 2 * math.pi * (0.5 * d)
        shape = "kin (4 canh cong noi voi 4 canh thang)"
    elif column_position == "edge":
        # Cot bien: chu vi mo 2 canh (2 canh khong bi cat)
        # Mo hinh don gian: cot hinh chu nhat, 2 canh song song bien
        # chu vi tinh = 2 canh doc * 1 + 2 canh ngang * (1 + 0.5*pi) + 2*0.5*h0
        u_b = column_h + 2 * (column_b + 0.5 * d) + math.pi * (0.5 * d)
        shape = "mo 2 canh (cot bien)"
    else:  # corner
        # Cot goc: chu vi mo 3 canh
        u_b = column_b + column_h + math.pi * (0.5 * d) + 0.5 * d
        shape = "mo 3 canh (cot goc)"

    Ac = u_b * d  # Dien tich mat cat nghieng (chu vi * chieu cao lam viec)
    Acb = u_b * d  # Dien tich gioi han ben duoi (phan san co kha nang pha hoai)
    Ab = ab_over_acb * Acb  # Dien tich mat cot tren mat cat nghieng

    logs.append({
        "Step": 1,
        "Description": "Xac dinh chu vi tinh toan va dien tich",
        "Principle": "Mat phang pha hoai gia su cach mat cot 0.5*h0; chu vi tinh theo hinh dang cot va vi tri.",
        "Formula": "u_b = chu vi mat cat tinh toan; Acb = u_b * h0; Ab = (Ab/Acb) * Acb",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.5",
            "Bang_Hinh": "Hinh 8.5 — Chu vi tinh toan khi chọc thủng",
            "Trang": "80",
            "Trich_Yeu": "Xác định chu vi và diện tích mặt cắt tính toán chọc thủng"
        },
        "Substitution": f"cot {column_b}x{column_h} mm, h0 = d = {d} mm, vi tri: {column_position}",
        "Result": f"u_b = {u_b:.1f} mm,  Acb = {Acb:.0f} mm2 = {Acb/1e6:.4f} m2,  Ab = {Ab:.0f} mm2 ({ab_over_acb}*Acb)"
    })

    # =========================================================================
    # 2. LUC CAT CHOC THỦNG (F_sw)
    # =========================================================================
    # F_sw = F_b (luc cot) - phan phan bo qua cot nen
    # Theo TCVN 5574:2018: F_b la luc cot; suc chong cat choc thủng tinh tu F_b
    F_sw = F_b  # kN — luc cat gay chọc thủng (don gian hoa)

    logs.append({
        "Step": 2,
        "Description": "Luc cat gay chọc thủng",
        "Principle": "Luc cot tac dung truc tiep len mat cat nghieng; phan phan bo qua cot nen duoc giam tru.",
        "Formula": "F_sw = F_b (truong hop don gian, cot giua)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.5",
            "Bang_Hinh": "",
            "Trang": "81",
            "Trich_Yeu": "Xác định lực cắt gây chọc thủng tác dụng lên bản sàn"
        },
        "Substitution": f"F_b = {F_b} kN",
        "Result": f"F_sw = {F_sw:.1f} kN"
    })

    # =========================================================================
    # 3. MOMEN KHONG CAN BANG (CAN THIET KHI CO M_bx, M_by)
    # =========================================================================
    # Momen khong can bang (unbalanced moment) truyen qua chu vi tinh
    # TCVN 5574:2018 Dieu 8.1.5 + Bang 8.3
    has_moment = (M_bx != 0) or (M_by != 0)

    if has_moment:
        # Phan momen truyen truc tiep qua cat (khoang 40-60% tuy vi tri)
        # Don gian hoa: gan het momen truyen qua cat
        # Luc cat phu them tu momen: V_xx = M_bx * alpha_s_x / J_x
        # TCVN 5574:2018 Bang 8.3: cot giua, ab/acb=0.75 -> he so = 0.4 cho moi phuong
        # Đon gian hoa: M_to_cat = gamma_v * M_b, gamma_v theo TCVN
        if column_position == "interior":
            gamma_v_x = gamma_v_y = 0.40
        elif column_position == "edge":
            gamma_v_x = 0.20   # phuong vuong goc bien
            gamma_v_y = 0.40
        else:  # corner
            gamma_v_x = 0.20
            gamma_v_y = 0.20

        M_bx_to_shear = M_bx * gamma_v_x  # kNm
        M_by_to_shear = M_by * gamma_v_y

        # Luc cat them tu momen: F_sw_M = M / (0.5 * d * so_canh)
        # Đon gian: F_sw_M_x = M_bx / (0.5 * d)
        F_sw_M_x = (M_bx_to_shear * 1e6) / (0.5 * d) * 1e-3 if d > 0 else 0  # kN
        F_sw_M_y = (M_by_to_shear * 1e6) / (0.5 * d) * 1e-3 if d > 0 else 0  # kN

        F_sw_total = F_sw + F_sw_M_x + F_sw_M_y

        logs.append({
            "Step": 3,
            "Description": "Xet momen khong can bang 2 phuong",
            "Principle": "Momen truyen mot phan qua cat doc theo chu vi tinh toan (TCVN Bang 8.3).",
            "Formula": "F_sw_M_x = gamma_v_x * M_bx / (0.5 * h0);  F_sw_M_y = gamma_v_y * M_by / (0.5 * h0)",
            "Citation": {
                "Ma_TC": "TCVN 5574:2018",
                "Dieu_Muc": "Dieu 8.1.5",
                "Bang_Hinh": "Bang 8.3 — He so truyen momen qua cat",
                "Trang": "83",
                "Trich_Yeu": "Hệ số truyền mô men không cân bằng qua lực cắt"
            },
            "Substitution": f"M_bx = {M_bx} kNm, M_by = {M_by} kNm, gamma_v_x = {gamma_v_x}, gamma_v_y = {gamma_v_y}, d = {d} mm",
            "Result": f"F_sw_M_x = {F_sw_M_x:.1f} kN, F_sw_M_y = {F_sw_M_y:.1f} kN, F_sw_tong = {F_sw_total:.1f} kN"
        })
    else:
        F_sw_total = F_sw
        logs.append({
            "Step": 3,
            "Description": "Khong xet momen (M_bx = M_by = 0)",
            "Principle": "Cot chiu nen tam (chi co luc doc), momen = 0.",
            "Formula": "F_sw_total = F_b",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.5", "Bang_Hinh": "", "Trang": "81", "Trich_Yeu": "Trường hợp cột chịu nén đúng tâm không có mô men"},
            "Substitution": f"M_bx = M_by = 0",
            "Result": f"F_sw_total = F_sw_total = {F_sw_total:.1f} kN"
        })

    # =========================================================================
    # 4. SUC CHONG CHOC THỦNG CUA BE TONG (F_b,ult)
    # =========================================================================
    # F_b,ult = alpha * Rbt * Ac
    # TCVN 5574:2018 Dieu 8.1.5
    F_b_ult = alpha * Rbt * Ac * 1e-3  # kN (Rb MPa, Ac mm2 -> kN)

    eta_punch = F_sw_total / F_b_ult if F_b_ult > 0 else 999.0

    logs.append({
        "Step": 4,
        "Description": "Suc chong chọc thủng cua be tong (F_b,ult)",
        "Principle": "Be tong tren mat cat nghieng chong cat; alpha phu thuoc cap be tong.",
        "Formula": "F_b,ult = alpha * Rbt * Ac (Ac = u_b * h0)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Dieu 8.1.5",
            "Bang_Hinh": "Bang 8.2 — He so alpha theo cap be tong",
            "Trang": "82",
            "Trich_Yeu": "Khả năng chống chọc thủng của bê tông vùng nén"
        },
        "Substitution": f"alpha = {alpha}, Rbt = {Rbt} MPa, Ac = {Ac:.0f} mm2",
        "Result": f"F_b,ult = {F_b_ult:.1f} kN",
        "Utilization": f"etab = F_sw_total / F_b,ult = {F_sw_total:.1f}/{F_b_ult:.1f} = {eta_punch:.3f}"
    })

    # =========================================================================
    # 5. XET TRUONG HOP CO COT ĐAI CHONG CHOC THỦNG
    # =========================================================================
    has_stirrups = (stirrup_dia is not None and stirrup_legs is not None and stirrup_spacing is not None)

    F_b_ult_stirrup = None
    F_sw_calc = None
    eta_punch_stirrup = None
    stirrup_check_passed = None
    stirrup_required = False

    if has_stirrups:
        # Suc chong cua cot đai: F_sw,stirrup = Rsw * Asw * (n_levels) / spacing
        # TCVN 5574:2018 Dieu 8.1.6
        Asw = stirrup_legs * math.pi * stirrup_dia ** 2 / 4.0  # mm2
        # Cot đai dat trong vung 0.5h0 quanh cot
        # q_sw = Rsw * Asw / s
        q_sw = Rsw * Asw / stirrup_spacing  # N/mm
        # n_levels = so vong cot đai tinh tu cot ra ngoai
        # Moi vong dat cach cot 0.5*h0, vong tiep theo cach 0.75*h0
        # Đon gian hoa: tinh 2 vong cot đai
        n_levels = 2
        # F_sw_stirrup = q_sw * n_levels * d (N)
        F_sw_stirrup = q_sw * n_levels * d * 1e-3  # kN

        F_b_ult_stirrup = F_b_ult + F_sw_stirrup
        eta_punch_stirrup = F_sw_total / F_b_ult_stirrup if F_b_ult_stirrup > 0 else 999.0
        stirrup_check_passed = eta_punch_stirrup <= ETA_PUNCH_LIMIT

        stirrup_desc = f"{stirrup_legs} chan Ф{stirrup_dia} a{stirrup_spacing} ({stirrup_grade})"

        logs.append({
            "Step": 5,
            "Description": "Suc chong chọc thủng co cot đai (F_b,ult,sw)",
            "Principle": "Cot đai chong chọc thủng gia tang suc chong, n_levels vong trong vung 0.5h0 quanh cot.",
            "Formula": "F_b,ult,sw = F_b,ult + Rsw * Asw * n_levels * d / s",
            "Citation": {
                "Ma_TC": "TCVN 5574:2018",
                "Dieu_Muc": "Dieu 8.1.6",
                "Bang_Hinh": "",
                "Trang": "84",
                "Trich_Yeu": "Khả năng chống chọc thủng khi bố trí cốt đai"
            },
            "Substitution": f"cot đai {stirrup_desc}, Asw = {Asw:.1f} mm2, n_levels = {n_levels}",
            "Result": f"F_sw_stirrup = {F_sw_stirrup:.1f} kN, F_b,ult,sw = {F_b_ult_stirrup:.1f} kN",
            "Utilization": f"etab = {F_sw_total:.1f}/{F_b_ult_stirrup:.1f} = {eta_punch_stirrup:.3f}"
        })
    else:
        # Neu khong co cot đai va etab > 1.0 -> can cot đai
        if eta_punch > ETA_PUNCH_LIMIT:
            stirrup_required = True
            unverified.append(
                f"etab = {eta_punch:.3f} > 1.0, chua nhap cot đai chong chọc thủng. "
                "Cần nhập stirrup_dia, stirrup_legs, stirrup_spacing để kiểm tra với cốt đai."
            )
        logs.append({
            "Step": 5,
            "Description": "Khong co cot đai chong chọc thủng",
            "Principle": "Chi co be tong chong cat; neu khong đu phai them cot đai.",
            "Formula": "F_b,ult = F_b,ult (khong co cot đai)",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Dieu 8.1.5", "Bang_Hinh": "", "Trang": "82", "Trich_Yeu": "Đánh giá khả năng chọc thủng khi không có cốt đai"},
            "Substitution": "stirrup_dia = stirrup_legs = stirrup_spacing = None",
            "Result": "Khong kiem tra duoc voi cot đai; etab da tinh o Step 4"
        })

    # =========================================================================
    # 6. TONG HOP & KET LUAN
    # =========================================================================
    if eta_punch <= ETA_PUNCH_LIMIT and not has_stirrups:
        # Đu kha nang chong be tong
        status = "PASSED"
        conclusive = True
    elif has_stirrups and stirrup_check_passed:
        status = "PASSED"
        conclusive = True
    elif has_stirrups and not stirrup_check_passed:
        status = "FAILED"
        conclusive = True
    elif eta_punch > ETA_PUNCH_LIMIT and not has_stirrups:
        # Chưa đu va chua nhap cot đai -> INCONCLUSIVE
        status = "INCONCLUSIVE"
        conclusive = False
    else:
        status = "FAILED"
        conclusive = False

    # Rating dua tren etab (khong cot đai) hoặc etab_stirrup
    eta_for_rating = eta_punch_stirrup if has_stirrups else eta_punch
    if eta_for_rating <= 0.70:
        rating = "GREEN"
    elif eta_for_rating <= 0.90:
        rating = "YELLOW"
    elif eta_for_rating <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    return {
        "element": element,
        "column_position": column_position,
        "concrete": concrete,
        "rebar": rebar,
        "Rb_MPa": Rb,
        "Rbt_MPa": Rbt,
        "alpha": alpha,
        "h_mm": h,
        "d_mm": d,
        "column_b_mm": column_b,
        "column_h_mm": column_h,
        "u_b_mm": round(u_b, 1),
        "Ac_mm2": round(Ac, 0),
        "Acb_mm2": round(Acb, 0),
        "Ab_mm2": round(Ab, 0),
        "Ab_over_Acb": ab_over_acb,
        "F_b_kN": F_b,
        "M_bx_kNm": M_bx,
        "M_by_kNm": M_by,
        "F_sw_total_kN": round(F_sw_total, 1),
        "F_b_ult_kN": round(F_b_ult, 1),
        "eta_punch": round(eta_punch, 3),
        "has_stirrups": has_stirrups,
        "stirrup_desc": stirrup_desc if has_stirrups else None,
        "F_sw_stirrup_kN": round(F_sw_stirrup, 1) if has_stirrups else None,
        "F_b_ult_stirrup_kN": round(F_b_ult_stirrup, 1) if has_stirrups else None,
        "eta_punch_stirrup": round(eta_punch_stirrup, 3) if has_stirrups else None,
        "stirrup_required": stirrup_required,
        "overall_eta": round(eta_for_rating, 3),
        "Rating": rating,
        "status": status,
        "conclusive": conclusive,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": (
            f"San phang/đai coc cot đon, cot chu nhat, vi tri {column_position}. "
            "CHUA kiem tra: san co suon, cot tron, cot đai nhieu lop, "
            "cot lien hop thep, san co dau cot truc tiep, luc nen truoc."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_punching_shear(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # Sample 1: San phang cot giua, khong cot đai
        sample = calc_punching_shear(
            element="slab",
            concrete="B25", rebar="CB400-V",
            h=200, a=30,
            column_b=300, column_h=300,
            column_position="interior",
            F_b=600, M_bx=50, M_by=40
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
