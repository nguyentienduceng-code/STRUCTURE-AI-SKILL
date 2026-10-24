import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_punching_shear.py — Kiểm tra chọc thủng sàn phẳng / đài cọc
# =============================================================================
# Phiên bản: TCVN 5574:2018 (Mục 8.1.6)
# =============================================================================

RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "BB25": 14.5, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "BB25": 1.05, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
RSW_MAP = {"CB240-T": 170, "CB300-V": 210, "CB400-V": 280, "CB500-V": 300}

ALPHA_BY_GRADE = {
    "B15": 1.00, "B20": 1.00, "B25": 1.00, "B30": 1.00,
    "B35": 1.00, "B40": 1.00, "BB25": 1.00
}

AB_OVER_ACB_DEFAULT = 0.75
AB_OVER_ACB_EDGE = 0.50
AB_OVER_ACB_CORNER = 0.40
ETA_PUNCH_LIMIT = 1.0


def calc_punching_shear(element="slab",
                        concrete="B25", rebar="CB400-V",
                        stirrup_grade="CB240-T",
                        h=200, d_eff=None, a=30,
                        column_b=300, column_h=300,
                        column_position="interior",
                        F_b=600,
                        M_bx=0, M_by=0,
                        stirrup_dia=None,
                        stirrup_legs=None,
                        stirrup_spacing=None):
    """
    [FIX BUG-STR-05]: Kiểm tra chọc thủng sàn phẳng / đài cọc theo TCVN 5574:2018 Mục 8.1.6:
      - Chu vi đường bao tính toán cách mép cột h0/2:
          * Cột giữa (interior): Lx = b_c + h0, Ly = h_c + h0 -> u_b = 2*(Lx + Ly) = 2*(b_c + h_c + 2*h0)
          * Cột biên (edge): Lx = b_c + 0.5*h0, Ly = h_c + h0 -> u_b = 2*Lx + Ly
          * Cột góc (corner): Lx = b_c + 0.5*h0, Ly = h_c + 0.5*h0 -> u_b = Lx + Ly
      - Mô đun chống uốn của đường bao tính toán W_bx, W_by (TCVN 5574:2018 Mục 8.1.6.2.2 CT 199-203):
          * W_bx = Ly * (Ly / 3 + Lx)  (đối với cột giữa uốn quanh trục x, cánh tay đòn theo phương y)
          * W_by = Lx * (Lx / 3 + Ly)
          * M_bx,ult = Rbt * W_bx * h0; M_by,ult = Rbt * W_by * h0
      - Điều kiện bền khi có lực tập trung F và mô men hai phương (CT 198):
          F / F_b,ult + M_bx / M_bx,ult + M_by / M_by,ult <= 1.0
          (trong đó tỉ số(M_bx/M_bx,ult + M_by/M_by,ult) lấy không lớn hơn 0.5 * (F / F_b,ult) theo Mục 8.1.6.1).
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)
    Rs = RS_MAP.get(rebar, 350)
    Rsw = RSW_MAP.get(stirrup_grade, 170)

    d = d_eff if d_eff else h - a
    h0 = d
    alpha = ALPHA_BY_GRADE.get(concrete, 1.00)

    if column_position == "interior":
        ab_over_acb = AB_OVER_ACB_DEFAULT
        Lx = column_b + d
        Ly = column_h + d
        u_b = 2.0 * (Lx + Ly)
        W_bx = Ly * (Ly / 3.0 + Lx)
        W_by = Lx * (Lx / 3.0 + Ly)
    elif column_position == "edge":
        ab_over_acb = AB_OVER_ACB_EDGE
        Lx = column_b + 0.5 * d
        Ly = column_h + d
        u_b = 2.0 * Lx + Ly
        W_bx = Ly * (Ly / 6.0 + Lx)
        W_by = Lx * (Lx / 3.0 + 0.5 * Ly)
    else:
        column_position = "corner"
        ab_over_acb = AB_OVER_ACB_CORNER
        Lx = column_b + 0.5 * d
        Ly = column_h + 0.5 * d
        u_b = Lx + Ly
        W_bx = Ly * (Ly / 6.0 + 0.5 * Lx)
        W_by = Lx * (Lx / 6.0 + 0.5 * Ly)

    Ac = u_b * d
    Acb = Ac
    Ab = ab_over_acb * Acb

    logs = []
    unverified = []
    warnings = []

    logs.append({
        "Step": 1,
        "Description": "Xác định chu vi đường bao tính toán u_b và mô đun kháng uốn đường bao W_bx, W_by",
        "Principle": "Đường bao tiết diện tính toán cách mép diện truyền tải một khoảng h0/2 (TCVN 5574:2018 Hình 16).",
        "Formula": "u_b = 2*(b_c + h_c + 2*h0) (cột giữa); Ac = u_b * h0; W_bx = Ly*(Ly/3 + Lx)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.6.2",
            "Bang_Hinh": "Hình 16",
            "Trang": "81",
            "Trich_Yeu": "Chu vi và mô đun chống uốn đường bao tính toán chọc thủng"
        },
        "Substitution": f"cột {column_b}x{column_h} mm, h0 = {d} mm, vị trí: {column_position} -> Lx={Lx:.0f}mm, Ly={Ly:.0f}mm",
        "Result": f"u_b = {u_b:.1f} mm, Ac = {Ac:.0f} mm², W_bx = {W_bx/1e3:.1f} cm², W_by = {W_by/1e3:.1f} cm²"
    })

    F_sw = F_b
    F_b_ult = alpha * Rbt * Ac * 1e-3  # kN
    M_bx_ult = alpha * Rbt * W_bx * d * 1e-6  # kNm
    M_by_ult = alpha * Rbt * W_by * d * 1e-6  # kNm

    logs.append({
        "Step": 2,
        "Description": "Khả năng chịu lực chọc thủng và mô men giới hạn của bê tông (F_b,ult, M_bx,ult, M_by,ult)",
        "Formula": "F_b,ult = Rbt * u_b * h0; M_bx,ult = Rbt * W_bx * h0; M_by,ult = Rbt * W_by * h0",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 8.1.6.2 CT (195), (199)",
            "Bang_Hinh": "",
            "Trang": "82",
            "Trich_Yeu": "Lực chọc thủng giới hạn và mô men chọc thủng giới hạn"
        },
        "Substitution": f"Rbt = {Rbt} MPa, u_b = {u_b:.1f} mm, h0 = {d} mm",
        "Result": f"F_b,ult = {F_b_ult:.1f} kN, M_bx,ult = {M_bx_ult:.1f} kNm, M_by,ult = {M_by_ult:.1f} kNm"
    })

    has_moment = (M_bx != 0) or (M_by != 0)
    eta_F = F_sw / F_b_ult if F_b_ult > 0 else 999.0

    if has_moment:
        eta_M_raw = (abs(M_bx) / M_bx_ult if M_bx_ult > 0 else 0.0) + (abs(M_by) / M_by_ult if M_by_ult > 0 else 0.0)
        # Theo TCVN 5574:2018 Mục 8.1.6.1: Tác dụng của mô men uốn lấy không lớn hơn một nửa tác dụng của lực tập trung F
        eta_M_capped = min(eta_M_raw, 0.5 * eta_F)
        eta_punch = eta_F + eta_M_capped
        # Quy đổi ra lực cắt tương đương F_sw_total để tương thích ngược với schema output
        F_sw_M_x = (abs(M_bx) * 1e6 * u_b / W_bx) * 1e-3 if W_bx > 0 else 0.0
        F_sw_M_y = (abs(M_by) * 1e6 * u_b / W_by) * 1e-3 if W_by > 0 else 0.0
        F_sw_total = eta_punch * F_b_ult

        logs.append({
            "Step": 3,
            "Description": "Kiểm tra điều kiện bền chọc thủng đồng thời chịu lực tập trung và mô men 2 phương",
            "Formula": "η_punch = F / F_b,ult + min(M_bx/M_bx,ult + M_by/M_by,ult, 0.5 * F/F_b,ult) <= 1.0",
            "Citation": {
                "Ma_TC": "TCVN 5574:2018",
                "Dieu_Muc": "Mục 8.1.6.1 CT (198)",
                "Bang_Hinh": "",
                "Trang": "82",
                "Trich_Yeu": "Kiểm tra chọc thủng khi có lực tập trung và mô men uốn theo hai phương"
            },
            "Substitution": f"F/F_b,ult = {eta_F:.3f}, M_bx/M_bx,ult + M_by/M_by,ult = {eta_M_raw:.3f} (giới hạn 0.5*η_F = {0.5*eta_F:.3f})",
            "Result": f"η_punch = {eta_punch:.3f}, F_sw,tương_đương = {F_sw_total:.1f} kN"
        })
    else:
        eta_punch = eta_F
        F_sw_total = F_sw
        logs.append({
            "Step": 3,
            "Description": "Kiểm tra chọc thủng đúng tâm (M_bx = M_by = 0)",
            "Formula": "η_punch = F_b / F_b,ult <= 1.0",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Mục 8.1.6.1 CT (194)", "Bang_Hinh": "", "Trang": "80", "Trich_Yeu": "Chọc thủng do lực tập trung"},
            "Substitution": f"F_b = {F_b} kN, F_b,ult = {F_b_ult:.1f} kN",
            "Result": f"η_punch = {eta_punch:.3f}"
        })

    has_stirrups = (stirrup_dia is not None and stirrup_legs is not None and stirrup_spacing is not None)
    F_b_ult_stirrup = None
    F_sw_stirrup = None
    eta_punch_stirrup = None
    stirrup_check_passed = None
    stirrup_required = False
    stirrup_desc = None

    if has_stirrups:
        Asw = stirrup_legs * math.pi * stirrup_dia ** 2 / 4.0
        q_sw = Rsw * Asw / stirrup_spacing
        # Theo TCVN 5574:2018 Mục 8.1.6.3 CT (205): F_sw,ult = 0.8 * q_sw * u_b
        F_sw_stirrup = 0.8 * q_sw * d * 2.0 * 1e-3
        # Giới hạn tối đa có cốt đai không vượt quá 2.0 * F_b,ult
        F_b_ult_stirrup = min(F_b_ult + F_sw_stirrup, 2.0 * F_b_ult)
        eta_punch_stirrup = F_sw_total / F_b_ult_stirrup if F_b_ult_stirrup > 0 else 999.0
        stirrup_check_passed = eta_punch_stirrup <= ETA_PUNCH_LIMIT
        stirrup_desc = f"{stirrup_legs} nhánh Φ{stirrup_dia}a{stirrup_spacing} ({stirrup_grade})"

        logs.append({
            "Step": 4,
            "Description": "Khả năng chống chọc thủng khi bố trí cốt đai (F_b,ult,sw)",
            "Formula": "F_b,ult,sw = min(F_b,ult + 0.8 * q_sw * u_sw, 2.0 * F_b,ult)",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Mục 8.1.6.3 CT (204)-(205)", "Bang_Hinh": "", "Trang": "84", "Trich_Yeu": "Tính toán chọc thủng có cốt thép ngang"},
            "Substitution": f"cốt đai {stirrup_desc}, Asw = {Asw:.1f} mm²",
            "Result": f"F_sw,stirrup = {F_sw_stirrup:.1f} kN, F_b,ult,sw = {F_b_ult_stirrup:.1f} kN, η = {eta_punch_stirrup:.3f}"
        })
    else:
        if eta_punch > ETA_PUNCH_LIMIT:
            stirrup_required = True
            unverified.append(f"η_punch = {eta_punch:.3f} > 1.0, cần bố trí cốt đai chống chọc thủng hoặc mũ cột.")

    if eta_punch <= ETA_PUNCH_LIMIT and not has_stirrups:
        status = "PASSED"
        conclusive = True
    elif has_stirrups and stirrup_check_passed:
        status = "PASSED"
        conclusive = True
    elif has_stirrups and not stirrup_check_passed:
        status = "FAILED"
        conclusive = True
    elif eta_punch > ETA_PUNCH_LIMIT and not has_stirrups:
        status = "INCONCLUSIVE"
        conclusive = False
    else:
        status = "FAILED"
        conclusive = False

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
        "W_bx_cm2": round(W_bx / 1e2, 1),
        "W_by_cm2": round(W_by / 1e2, 1),
        "Ac_mm2": round(Ac, 0),
        "Acb_mm2": round(Acb, 0),
        "Ab_mm2": round(Ab, 0),
        "Ab_over_Acb": ab_over_acb,
        "F_b_kN": F_b,
        "M_bx_kNm": M_bx,
        "M_by_kNm": M_by,
        "F_sw_total_kN": round(F_sw_total, 1),
        "F_b_ult_kN": round(F_b_ult, 1),
        "M_bx_ult_kNm": round(M_bx_ult, 1),
        "M_by_ult_kNm": round(M_by_ult, 1),
        "eta_punch": round(eta_punch, 3),
        "has_stirrups": has_stirrups,
        "stirrup_desc": stirrup_desc,
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
            f"Sàn phẳng/đài cọc cột đơn chữ nhật, vị trí {column_position}. "
            "CHƯA kiểm tra: sàn có sườn, cột tròn, ứng lực trước."
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
        sample = calc_punching_shear(
            element="slab",
            concrete="B25", rebar="CB400-V",
            h=200, a=30,
            column_b=300, column_h=300,
            column_position="interior",
            F_b=400, M_bx=30, M_by=20
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
