import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Cuong do vat lieu TCVN 5574:2018 (MPa) ---
RB_MAP = {"B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0, "B35": 19.5, "B40": 22.0}
RBT_MAP = {"B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40}
RS_MAP = {"CB240-T": 210, "CB300-V": 260, "CB400-V": 350, "CB500-V": 435}
# Cuong do tinh toan cot thep ngang Rsw (TCVN 5574:2018) — KHONG phai 0.8*Rs
RSW_MAP = {"CB240-T": 170, "CB300-V": 210, "CB400-V": 280, "CB500-V": 300}

ALPHA_R_DEFAULT = 0.39      # STANDARDS_LOCK.md muc 3 (CB400-V)
MU_MIN_PERCENT = 0.05       # Ham luong cot thep doc toi thieu


def calc_rc_beam(b=300, h=600, a=40, concrete="B25", rebar="CB400-V",
                 M_ed=250, V_ed=120, alpha_R=ALPHA_R_DEFAULT,
                 stirrup_grade="CB240-T", stirrup_dia=None, stirrup_legs=2, stirrup_spacing=None):
    """
    Kiem tra dam BTCT tiet dien chu nhat chiu uon + cat theo TCVN 5574:2018.

    b, h, a        : Be rong, chieu cao, lop bao ve den trong tam cot thep (mm)
    concrete       : Cap do ben be tong (B15..B40)
    rebar          : Loai cot thep doc
    M_ed, V_ed     : Noi luc thiet ke (kNm, kN)
    alpha_R        : Gioi han alpha_m
    stirrup_*      : Thong so cot dai. Neu KHONG truyen dia/spacing -> script
                     KHONG gia dinh, chi bao cao luong cot dai YEU CAU.

    PHAM VI: Tiet dien chu nhat, cot don, uon phang.
    CHUA kiem tra: vong, be rong khe nut, xoan, tiet dien chu T, cot kep.
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)
    Rs = RS_MAP.get(rebar, 350)
    Rsw = RSW_MAP.get(stirrup_grade, 170)

    h0 = h - a
    logs = []
    unverified = []

    # ================= 1. CHIU UON =================
    alpha_m = (M_ed * 1e6) / (Rb * b * h0 ** 2)
    eta_M = alpha_m / alpha_R

    logs.append({
        "Step": "Kiểm tra vùng bê tông chịu nén (alpha_m)",
        "Principle": "Vượt alpha_R thì bê tông vùng nén vỡ trước khi cốt thép kéo chảy — phá hoại giòn, không báo trước.",
        "Formula": "alpha_m = M_Ed / (Rb * b * h0^2) <= alpha_R",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1 - Cấu kiện chịu uốn", "Bang_Hinh": "", "Trang": "62", "Trich_Yeu": "Tính toán độ bền tiết diện thẳng góc cấu kiện chịu uốn"},
        "Values": f"M_Ed={M_ed} kNm, Rb={Rb} MPa, b={b} mm, h0={h0} mm, alpha_R={alpha_R}",
        "Result": f"alpha_m = {alpha_m:.4f}  vs  alpha_R = {alpha_R}",
        "Utilization": f"eta_M = {eta_M:.3f}"
    })

    if alpha_m > alpha_R:
        status_uon = "FAILED — phá hoại giòn. Tăng tiết diện, tăng cấp bê tông hoặc đặt cốt kép."
        As_req = 0.0
        As_min = MU_MIN_PERCENT / 100.0 * b * h0
        As_chon = 0.0
        mu_percent = 0.0
    else:
        status_uon = "PASSED"
        zeta = 0.5 * (1.0 + math.sqrt(1.0 - 2.0 * alpha_m))
        As_req = (M_ed * 1e6) / (zeta * h0 * Rs)
        As_min = MU_MIN_PERCENT / 100.0 * b * h0
        As_chon = max(As_req, As_min)
        mu_percent = As_chon / (b * h0) * 100.0
        logs.append({
            "Step": "Tính diện tích cốt thép dọc chịu kéo",
            "Principle": "Cặp ngẫu lực giữa hợp lực kéo trong thép và hợp lực nén trong bê tông cân bằng momen ngoài.",
            "Formula": "zeta = 0.5*(1 + sqrt(1 - 2*alpha_m));  As = M_Ed / (zeta * h0 * Rs)",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1 - Tính toán cốt thép dọc", "Bang_Hinh": "", "Trang": "64", "Trich_Yeu": "Xác định diện tích cốt thép dọc chịu kéo theo mô men uốn"},
            "Values": f"alpha_m={alpha_m:.4f}, zeta={zeta:.4f}, h0={h0} mm, Rs={Rs} MPa",
            "Result": f"As_yêu_cầu = {As_req:.1f} mm2 | As_min = {As_min:.1f} mm2 | As_chọn = {As_chon:.1f} mm2 (mu = {mu_percent:.2f}%)"
        })

    # ================= 2. CHIU CAT =================
    # 2a. Kiem tra dai be tong vung nen giua cac vet nut xien
    V_strut = 0.3 * Rb * b * h0 * 1e-3   # kN
    eta_strut = V_ed / V_strut
    logs.append({
        "Step": "Kiểm tra ứng suất nén chính bản bụng (dải bê tông xiên)",
        "Principle": "Lực cắt quá lớn ép vỡ dải bê tông nghiêng giữa các vết nứt xiên — cốt đai không cứu được.",
        "Formula": "V_Ed <= 0.3 * Rb * b * h0",
        "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1.3 - Tính toán theo dải nghiêng", "Bang_Hinh": "", "Trang": "68", "Trich_Yeu": "Độ bền dải bê tông nghiêng giữa các vết nứt xiên"},
        "Values": f"Rb={Rb} MPa, b={b} mm, h0={h0} mm",
        "Result": f"V_giới_hạn = {V_strut:.2f} kN  vs  V_Ed = {V_ed} kN",
        "Utilization": f"eta_dải_nén = {eta_strut:.3f}"
    })

    # 2b. Kha nang chiu cat cua rieng be tong (tiet dien nghieng c = 2*h0)
    Qb = 0.75 * Rbt * b * h0 * 1e-3      # kN, ung voi c = 2*h0
    Qb_min = 0.5 * Rbt * b * h0 * 1e-3   # kN, gioi han duoi

    if stirrup_dia and stirrup_spacing:
        Asw = stirrup_legs * math.pi * stirrup_dia ** 2 / 4.0
        q_sw = Rsw * Asw / stirrup_spacing          # N/mm
        Qsw = 0.75 * q_sw * (2.0 * h0) * 1e-3       # kN
        Q_rd = Qb + Qsw
        eta_V = V_ed / Q_rd
        stirrup_desc = f"{stirrup_legs} nhánh Φ{stirrup_dia} a{stirrup_spacing} ({stirrup_grade})"
        logs.append({
            "Step": "Kiểm tra khả năng chịu cắt trên tiết diện nghiêng",
            "Principle": "Bê tông và cốt đai cùng gánh lực cắt trên vết nứt xiên.",
            "Formula": "Q_Rd = Q_b + Q_sw;  Q_b = 0.75*Rbt*b*h0;  Q_sw = 0.75*q_sw*c, c = 2*h0;  q_sw = Rsw*Asw/s",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1.3 - Tiết diện nghiêng", "Bang_Hinh": "", "Trang": "69", "Trich_Yeu": "Độ bền tiết diện nghiêng chịu lực cắt với cốt đai"},
            "Values": f"Cốt đai {stirrup_desc}, Asw={Asw:.1f} mm2, Rsw={Rsw} MPa, q_sw={q_sw:.2f} N/mm, Qb={Qb:.2f} kN, Qsw={Qsw:.2f} kN",
            "Result": f"Q_Rd = {Q_rd:.2f} kN  vs  V_Ed = {V_ed} kN",
            "Utilization": f"eta_V = {eta_V:.3f}"
        })
    else:
        # KHONG gia dinh cot dai — bao cao luong yeu cau
        Qsw_req = max(V_ed - Qb, 0.0)
        q_sw_req = Qsw_req * 1e3 / (0.75 * 2.0 * h0) if Qsw_req > 0 else 0.0
        Q_rd = None
        eta_V = None
        stirrup_desc = "Chưa nhập"
        unverified.append(
            f"Chưa nhập thông số cốt đai (stirrup_dia, stirrup_spacing) — chưa kết luận được khả năng chịu cắt. "
            f"Yêu cầu tối thiểu q_sw >= {q_sw_req:.2f} N/mm."
        )
        logs.append({
            "Step": "Kiểm tra khả năng chịu cắt trên tiết diện nghiêng",
            "Principle": "Bê tông và cốt đai cùng gánh lực cắt trên vết nứt xiên.",
            "Formula": "Q_Rd = Q_b + Q_sw;  q_sw_yêu_cầu = (V_Ed - Q_b) / (0.75 * c), c = 2*h0",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1.3 - Yêu cầu cốt đai", "Bang_Hinh": "", "Trang": "69", "Trich_Yeu": "Xác định lượng cốt đai yêu cầu khi chịu lực cắt"},
            "Values": f"Q_b = {Qb:.2f} kN (Q_b,min = {Qb_min:.2f} kN), V_Ed = {V_ed} kN",
            "Result": f"CHƯA KẾT LUẬN — cần cốt đai với q_sw >= {q_sw_req:.2f} N/mm",
            "Remark": "Script không tự giả định cốt đai. Nhập stirrup_dia và stirrup_spacing để kiểm tra."
        })

    # ================= 3. TONG HOP =================
    etas = [eta_M, eta_strut] + ([eta_V] if eta_V is not None else [])
    overall = max(etas)
    conclusive = (eta_V is not None) and (status_uon == "PASSED")
    if not conclusive:
        status = "INCONCLUSIVE" if overall <= 1.0 else "FAILED"
    else:
        status = "PASSED" if overall <= 1.0 else "FAILED"
    rating = "GREEN" if overall <= 0.70 else "YELLOW" if overall <= 0.90 else "ORANGE" if overall <= 1.0 else "RED"

    return {
        "section": f"bxh = {b}x{h} mm",
        "concrete": concrete,
        "rebar": rebar,
        "Rb_MPa": Rb, "Rbt_MPa": Rbt, "Rs_MPa": Rs, "Rsw_MPa": Rsw,
        "h0_mm": h0,
        "M_ed_kNm": M_ed,
        "alpha_m": round(alpha_m, 4),
        "alpha_R": alpha_R,
        "As_req_mm2": round(As_req, 1),
        "As_min_mm2": round(As_min, 1),
        "As_chon_mm2": round(As_chon, 1),
        "mu_percent": round(mu_percent, 2),
        "eta_M": round(eta_M, 3),
        "status_uon": status_uon,
        "V_ed_kN": V_ed,
        "V_strut_limit_kN": round(V_strut, 2),
        "eta_strut": round(eta_strut, 3),
        "Qb_kN": round(Qb, 2),
        "stirrup": stirrup_desc,
        "Q_rd_kN": round(Q_rd, 2) if Q_rd is not None else None,
        "eta_V": round(eta_V, 3) if eta_V is not None else None,
        "overall_eta": round(overall, 3),
        "Rating": rating,
        "status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": ("Tiết diện chữ nhật, cốt đơn, uốn phẳng. CHƯA kiểm tra: độ võng, "
                             "bề rộng khe nứt, xoắn, tiết diện chữ T, cốt kép."),
        "Unverified_Items": unverified,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_rc_beam(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        sample = calc_rc_beam(b=300, h=600, a=40, concrete="B25", rebar="CB400-V",
                              M_ed=250, V_ed=120,
                              stirrup_dia=8, stirrup_legs=2, stirrup_spacing=150)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
