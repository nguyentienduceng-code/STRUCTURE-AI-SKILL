import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Hang so chot theo STANDARDS_LOCK.md muc 3 ---
GAMMA_M2 = 1.25          # He so tin cay lien ket theo EN 1993-1-8
# Cuong do keo dut bu long fub (MPa) theo cap ben
FUB_MAP = {"4.6": 400.0, "5.6": 500.0, "6.8": 600.0, "8.8": 800.0, "10.9": 1000.0}
# alpha_v theo EN 1993-1-8 Bang 3.4 (mat cat qua phan ren)
ALPHA_V_MAP = {"4.6": 0.6, "5.6": 0.6, "6.8": 0.5, "8.8": 0.6, "10.9": 0.5}
# Dien tich phan ren As (mm2) theo TCVN 1916 / ISO 898-1
AS_MAP = {12: 84.3, 16: 157.0, 20: 245.0, 22: 303.0, 24: 353.0, 27: 459.0, 30: 561.0, 36: 817.0}


def _norm_grade(grade):
    """Chuan hoa cap ben bu long ve chuoi. Chap nhan 8.8 (float), '8.8', '10.9'."""
    if isinstance(grade, str):
        g = grade.strip()
    else:
        g = f"{float(grade):g}"
    if g not in FUB_MAP:
        raise ValueError(
            f"Cap ben bu long khong hop le: {grade!r}. Chi chap nhan: {', '.join(FUB_MAP)}"
        )
    return g


def calc_bolt_connection(bolt_d=20, grade="8.8", n_bolts=6, V_ed=180, F_t_ed=50,
                         t_plate=10, f_u_plate=400, n_shear_planes=1,
                         e1=None, e2=None, p1=None, p2=None):
    """
    Kiem tra lien ket bu long chiu cat + keo theo EN 1993-1-8 (Eurocode 3 Part 1-8).

    bolt_d        : Duong kinh bu long (mm)
    grade         : Cap ben — '4.6' / '5.6' / '6.8' / '8.8' / '10.9'
    n_bolts       : So luong bu long
    V_ed          : Luc cat thiet ke tac dung len nhom bu long (kN)
    F_t_ed        : Luc keo thiet ke tac dung len nhom bu long (kN)
    t_plate       : Be day ban ma mong nhat (mm)
    f_u_plate     : Cuong do keo dut cua thep ban ma (MPa)
    n_shear_planes: So mat cat chiu luc cua 1 bu long (1 = 1 mat, 2 = 2 mat)
    e1, e2, p1, p2: Khoang cach bo tri bu long (mm) — dung tinh he so ep mat alpha_b, k1.
                    Neu bo trong -> lay gia tri thien ve an toan.

    PHAM VI: Lien ket chiu ep mat (bearing type). KHONG kiem tra:
      - Lien kite ma sat truot gioi han (slip-resistant)
      - Pha hoai khoi (block tearing)
      - Kha nang chiu luc cua ban ma va bung dam
    Cac kiem tra tren phai lam rieng truoc khi ket luan lien ket DAT.
    """
    g = _norm_grade(grade)
    fub = FUB_MAP[g]
    alpha_v = ALPHA_V_MAP[g]
    A_s = AS_MAP.get(int(bolt_d), 0.78 * math.pi * (bolt_d ** 2) / 4.0)

    logs = []

    # 1. Kha nang chiu cat cua nhom bu long
    V_b_rd_1 = (alpha_v * fub * A_s * 1e-3) / GAMMA_M2 * n_shear_planes  # kN
    V_b_rd_total = V_b_rd_1 * n_bolts
    eta_shear = V_ed / V_b_rd_total
    logs.append({
        "Step": "Khả năng chịu cắt của nhóm bu lông",
        "Principle": "Thân bu lông bị cắt đứt tại mặt trượt giữa các bản thép.",
        "Formula": "F_v,Rd = alpha_v * f_ub * A_s / gamma_M2  (x số mặt cắt x số bu lông)",
        "Citation": {"Ma_TC": "EN 1993-1-8", "Dieu_Muc": "Bảng 3.4", "Bang_Hinh": "Table 3.4", "Trang": ""},
        "Values": f"alpha_v={alpha_v} (cấp {g}), f_ub={fub} MPa, A_s={A_s:.1f} mm2, gamma_M2={GAMMA_M2}, n_mặt_cắt={n_shear_planes}, n={n_bolts}",
        "Result": f"F_v,Rd,1 = {V_b_rd_1:.2f} kN | Tổng = {V_b_rd_total:.2f} kN",
        "Utilization": f"eta_cắt = {eta_shear:.3f}"
    })

    # 2. Kha nang chiu ep mat — phu thuoc khoang cach bo tri
    # alpha_b = min(e1/(3*d0), p1/(3*d0) - 0.25, fub/fu, 1.0)
    # k1      = min(2.8*e2/d0 - 1.7, 1.4*p2/d0 - 1.7, 2.5)
    d0 = bolt_d + 2.0  # duong kinh lo bu long
    ep_assumed = []
    if e1 is None:
        e1 = 1.2 * d0
        ep_assumed.append("e1 = 1.2*d0 (tối thiểu cho phép)")
    if e2 is None:
        e2 = 1.2 * d0
        ep_assumed.append("e2 = 1.2*d0 (tối thiểu cho phép)")
    if p1 is None:
        p1 = 2.2 * d0
        ep_assumed.append("p1 = 2.2*d0 (tối thiểu cho phép)")
    if p2 is None:
        p2 = 2.4 * d0
        ep_assumed.append("p2 = 2.4*d0 (tối thiểu cho phép)")

    alpha_b = min(e1 / (3.0 * d0), p1 / (3.0 * d0) - 0.25, fub / f_u_plate, 1.0)
    k1 = min(2.8 * e2 / d0 - 1.7, 1.4 * p2 / d0 - 1.7, 2.5)
    alpha_b = max(alpha_b, 0.0)
    k1 = max(k1, 0.0)

    F_b_rd_1 = (k1 * alpha_b * f_u_plate * bolt_d * t_plate * 1e-3) / GAMMA_M2  # kN
    F_b_rd_total = F_b_rd_1 * n_bolts
    eta_bearing = V_ed / F_b_rd_total if F_b_rd_total > 0 else float("inf")
    logs.append({
        "Step": "Khả năng chịu ép mặt của bản thép",
        "Principle": "Bu lông ép vào thành lỗ làm biến dạng/xé rách bản thép.",
        "Formula": "F_b,Rd = k1 * alpha_b * f_u * d * t / gamma_M2",
        "Citation": {"Ma_TC": "EN 1993-1-8", "Dieu_Muc": "Bảng 3.4", "Bang_Hinh": "Table 3.4", "Trang": ""},
        "Values": f"k1={k1:.2f}, alpha_b={alpha_b:.3f}, f_u={f_u_plate} MPa, d={bolt_d} mm, t={t_plate} mm, d0={d0} mm",
        "Result": f"F_b,Rd,1 = {F_b_rd_1:.2f} kN | Tổng = {F_b_rd_total:.2f} kN",
        "Utilization": f"eta_ép_mặt = {eta_bearing:.3f}"
    })

    # 3. Kha nang chiu keo
    F_t_rd_1 = (0.9 * fub * A_s * 1e-3) / GAMMA_M2  # kN
    F_t_rd_total = F_t_rd_1 * n_bolts
    eta_tension = F_t_ed / F_t_rd_total
    logs.append({
        "Step": "Khả năng chịu kéo của nhóm bu lông",
        "Principle": "Bu lông bị kéo đứt tại phần ren.",
        "Formula": "F_t,Rd = 0.9 * f_ub * A_s / gamma_M2",
        "Citation": {"Ma_TC": "EN 1993-1-8", "Dieu_Muc": "Bảng 3.4", "Bang_Hinh": "Table 3.4", "Trang": ""},
        "Values": f"f_ub={fub} MPa, A_s={A_s:.1f} mm2, gamma_M2={GAMMA_M2}, n={n_bolts}",
        "Result": f"F_t,Rd,1 = {F_t_rd_1:.2f} kN | Tổng = {F_t_rd_total:.2f} kN",
        "Utilization": f"eta_kéo = {eta_tension:.3f}"
    })

    # 4. Tuong tac cat - keo
    interaction = (V_ed / V_b_rd_total) + (F_t_ed / (1.4 * F_t_rd_total))
    logs.append({
        "Step": "Kiểm tra tương tác cắt - kéo đồng thời",
        "Principle": "Bu lông chịu đồng thời cắt và kéo suy giảm khả năng chịu lực theo cả hai phương.",
        "Formula": "F_v,Ed/F_v,Rd + F_t,Ed/(1.4*F_t,Rd) <= 1.0",
        "Citation": {"Ma_TC": "EN 1993-1-8", "Dieu_Muc": "Bảng 3.4", "Bang_Hinh": "Table 3.4", "Trang": ""},
        "Values": f"V_Ed={V_ed} kN, F_v,Rd={V_b_rd_total:.2f} kN, F_t,Ed={F_t_ed} kN, F_t,Rd={F_t_rd_total:.2f} kN",
        "Result": f"Tỷ số tương tác = {interaction:.3f}",
        "Utilization": f"eta_tương_tác = {interaction:.3f}"
    })

    overall_eta = max(eta_shear, eta_bearing, eta_tension, interaction)
    status = "PASSED" if overall_eta <= 1.0 else "FAILED"
    rating = "GREEN" if overall_eta <= 0.70 else "YELLOW" if overall_eta <= 0.90 else "ORANGE" if overall_eta <= 1.0 else "RED"

    unverified = []
    if ep_assumed:
        unverified.append("Khoảng cách bố trí bu lông chưa được nhập: " + "; ".join(ep_assumed))

    return {
        "bolt_type": f"M{bolt_d} cấp {g}",
        "n_bolts": n_bolts,
        "n_shear_planes": n_shear_planes,
        "f_ub_MPa": fub,
        "alpha_v": alpha_v,
        "A_s_mm2": round(A_s, 1),
        "V_b_rd_total_kN": round(V_b_rd_total, 2),
        "F_b_rd_total_kN": round(F_b_rd_total, 2),
        "F_t_rd_total_kN": round(F_t_rd_total, 2),
        "eta_shear": round(eta_shear, 3),
        "eta_bearing": round(eta_bearing, 3),
        "eta_tension": round(eta_tension, 3),
        "interaction_ratio": round(interaction, 3),
        "overall_eta": round(overall_eta, 3),
        "Rating": rating,
        "status": status,
        "Standard": "EN 1993-1-8 (Eurocode 3 Part 1-8)",
        "Standard_Method": "EN 1993-1-8",
        "Scope_Limitation": ("Liên kết chịu ép mặt. CHƯA kiểm tra: ma sát trượt giới hạn, "
                             "phá hoại khối (block tearing), khả năng chịu lực của bản mã và bụng dầm."),
        "Unverified_Items": unverified,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_bolt_connection(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_bolt_connection(bolt_d=20, grade="8.8", n_bolts=6, V_ed=180,
                                      F_t_ed=50, t_plate=12, f_u_plate=400)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
