import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import math

# Gioi han alpha_R chong pha hoai gion - chot theo STANDARDS_LOCK.md muc 3
ALPHA_R_DEFAULT = 0.39
# Ham luong cot thep toi thieu (TCVN 5574:2018)
MU_MIN_PERCENT = 0.05


def design_rc_flexure(M, b, h0, Rb, Rs, alpha_R=ALPHA_R_DEFAULT):
    """
    Tính diện tích cốt thép chịu uốn dầm chữ nhật đặt cốt đơn theo TCVN 5574:2018.
    M : Momen tính toán (kN.m)
    b : Bề rộng tiết diện (m)
    h0: Chiều cao làm việc (m)
    Rb: Cường độ chịu nén tính toán của bê tông (MPa)
    Rs: Cường độ chịu kéo tính toán của cốt thép (MPa)
    alpha_R: Giới hạn alpha_m (0.39 với CB400-V; 0.44 với CB300-V)

    PHẠM VI: Tiết diện chữ nhật, cốt đơn, chịu uốn thuần tuý.
    KHÔNG áp dụng cho tiết diện chữ T, cốt kép, hoặc cấu kiện chịu nén-uốn.
    """
    # Đổi đơn vị
    M_Nmm = M * 1e6
    b_mm = b * 1000
    h0_mm = h0 * 1000

    alpha_m = M_Nmm / (Rb * b_mm * h0_mm**2)
    eta = alpha_m / alpha_R  # Chi so tan dung kha nang tiet dien be tong vung nen

    logs = [
        {
            "Step": "Tính hệ số alpha_m",
            "Principle": "alpha_m đặc trưng mức huy động vùng bê tông chịu nén. Vượt alpha_R thì bê tông vỡ trước khi thép chảy (phá hoại giòn).",
            "Formula": "alpha_m = M / (Rb * b * h0^2)",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Điều 8.1 - Cấu kiện chịu uốn", "Bang_Hinh": "", "Trang": ""},
            "Values": f"M={M_Nmm} N.mm, Rb={Rb} MPa, b={b_mm} mm, h0={h0_mm} mm",
            "Result": f"alpha_m = {alpha_m:.3f}  (giới hạn alpha_R = {alpha_R})"
        }
    ]

    if alpha_m > alpha_R:
        status = f"FAIL: alpha_m = {alpha_m:.3f} > alpha_R = {alpha_R} — phá hoại giòn. Cần tăng tiết diện, tăng cấp bê tông hoặc đặt cốt kép."
        As = 0
        mu = 0
    else:
        zeta = 0.5 * (1 + math.sqrt(1 - 2*alpha_m))
        As = M_Nmm / (Rs * zeta * h0_mm) # mm2
        mu = (As / (b_mm * h0_mm)) * 100 # %
        status = "PASS"
        logs.extend([
            {
                "Step": "Tính hệ số zeta",
                "Formula": "zeta = 0.5 * (1 + sqrt(1 - 2*alpha_m))",
                "Values": f"alpha_m={alpha_m:.3f}",
                "Result": f"zeta = {zeta:.3f}"
            },
            {
                "Step": "Tính diện tích cốt thép (As)",
                "Formula": "As = M / (Rs * zeta * h0)",
                "Values": f"M={M_Nmm}, Rs={Rs}, zeta={zeta:.3f}, h0={h0_mm}",
                "Result": f"As = {As:.2f} mm2"
            },
            {
                "Step": "Kiểm tra hàm lượng cốt thép (mu)",
                "Principle": "Hàm lượng dưới mức tối thiểu khiến dầm phá hoại đột ngột ngay khi bê tông nứt.",
                "Formula": "mu = (As / (b * h0)) * 100 >= mu_min",
                "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Hàm lượng cốt thép tối thiểu", "Bang_Hinh": "", "Trang": ""},
                "Values": f"As={As:.2f} mm2, b={b_mm} mm, h0={h0_mm} mm, mu_min={MU_MIN_PERCENT}%",
                "Result": f"mu = {mu:.3f}%  ({'ĐẠT' if mu >= MU_MIN_PERCENT else 'KHÔNG ĐẠT - đặt theo mu_min'})"
            }
        ])

    rating = "GREEN" if eta <= 0.70 else "YELLOW" if eta <= 0.90 else "ORANGE" if eta <= 1.0 else "RED"
    As_min = MU_MIN_PERCENT / 100.0 * b_mm * h0_mm
    As_final = max(As, As_min) if status == "PASS" else 0.0

    logs.append({
        "Step": "Kết luận kiểm tra tiết diện",
        "Formula": "eta = alpha_m / alpha_R",
        "Values": f"alpha_m={alpha_m:.3f}, alpha_R={alpha_R}",
        "Result": f"eta = {eta:.3f}",
        "Utilization": f"eta = {eta:.3f} ({eta * 100:.1f}%)",
        "Rating": rating,
        "Remark": ("Dự trữ lớn — xem xét giảm tiết diện (Value Engineering)." if eta <= 0.70
                   else "Sát ngưỡng phá hoại giòn — cân nhắc tăng tiết diện." if 0.90 < eta <= 1.0
                   else "KHÔNG ĐẠT." if eta > 1.0 else "Đạt, mức sử dụng hợp lý.")
    })

    return {
        "M_input": M,
        "b_input": b,
        "h0_input": h0,
        "Rb_input": Rb,
        "Rs_input": Rs,
        "alpha_R": alpha_R,
        "alpha_m": round(alpha_m, 4),
        "As_tinh_toan_mm2": round(As, 1),
        "As_min_mm2": round(As_min, 1),
        "As_chon_mm2": round(As_final, 1),
        "mu_percent": round(mu, 3),
        "utilization_ratio": round(eta, 3),
        "Rating": rating,
        "Status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": "Tiết diện chữ nhật, cốt đơn, chịu uốn thuần tuý. Chưa kiểm tra cắt, võng và bề rộng khe nứt.",
        "Calculation_Logs": logs
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RC Flexure Calculator (TCVN 5574:2018)")
    parser.add_argument("--M", type=float, required=True, help="Momen (kN.m)")
    parser.add_argument("--b", type=float, required=True, help="Bề rộng (m)")
    parser.add_argument("--h0", type=float, required=True, help="Chiều cao làm việc (m)")
    parser.add_argument("--Rb", type=float, required=True, help="Rb (MPa)")
    parser.add_argument("--Rs", type=float, required=True, help="Rs (MPa)")
    parser.add_argument("--alpha_R", type=float, default=ALPHA_R_DEFAULT, help="Giới hạn alpha_R (0.39 CB400-V)")
    args = parser.parse_args()

    result = design_rc_flexure(args.M, args.b, args.h0, args.Rb, args.Rs, args.alpha_R)
    print(json.dumps(result, indent=2, ensure_ascii=False))
