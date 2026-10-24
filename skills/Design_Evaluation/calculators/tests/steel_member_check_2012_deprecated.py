import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse

# Hệ số tin cậy về vật liệu thép — chốt theo STANDARDS_LOCK.md muc 3
GAMMA_M = 1.05


def check_steel_member(M, N, Area, Wx, fy, gamma_c=1.0, gamma_M=GAMMA_M):
    """
    Kiểm tra ứng suất pháp cấu kiện thép chịu nén-uốn theo TCVN 5575:2012.

    M      : Momen uốn (kN.m)
    N      : Lực dọc (kN) — dương = nén, âm = kéo (lấy trị tuyệt đối)
    Area   : Diện tích tiết diện (cm2)
    Wx     : Momen kháng uốn đàn hồi (cm3)
    fy     : Giới hạn chảy của thép (MPa)
    gamma_c: Hệ số điều kiện làm việc (TCVN 5575 Bảng 6)
    gamma_M: Hệ số tin cậy vật liệu (1.05)

    LƯU Ý PHẠM VI: Đây là kiểm tra BỀN (strength) theo ứng suất pháp.
    Script KHÔNG kiểm tra ổn định tổng thể (mất ổn định uốn xoắn - LTB)
    và KHÔNG kiểm tra ổn định cục bộ bản bụng/bản cánh.
    Với cấu kiện chịu nén hoặc dầm không được giằng ngang liên tục,
    BẮT BUỘC kiểm tra bổ sung ổn định trước khi kết luận ĐẠT.
    """
    # Đổi đơn vị sang hệ kN-cm
    M_kcm = M * 100.0            # kN.cm
    Wx_cm3 = Wx
    Area_cm2 = Area

    # Cường độ tính toán f = fy / gamma_M  (1 MPa = 0.1 kN/cm2)
    f_design_MPa = fy / gamma_M
    f_design = f_design_MPa / 10.0   # kN/cm2

    sigma_N = abs(N) / Area_cm2
    sigma_M = abs(M_kcm) / Wx_cm3
    sigma_max = sigma_N + sigma_M

    f_allow = f_design * gamma_c
    utilization_ratio = sigma_max / f_allow

    status = "PASS" if utilization_ratio <= 1.0 else "FAIL"

    if utilization_ratio <= 0.70:
        rating = "GREEN"
    elif utilization_ratio <= 0.90:
        rating = "YELLOW"
    elif utilization_ratio <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    logs = [
        {
            "Step": "Xác định cường độ tính toán của thép (f)",
            "Principle": "Cường độ tính toán bằng giới hạn chảy chia hệ số tin cậy vật liệu.",
            "Formula": "f = fy / gamma_M",
            "Citation": {"Ma_TC": "TCVN 5575:2012", "Dieu_Muc": "Bảng hệ số tin cậy vật liệu", "Bang_Hinh": "Bảng 1", "Trang": "22", "Trich_Yeu": "Hệ số tin cậy vật liệu của thép"},
            "Values": f"fy={fy} MPa, gamma_M={gamma_M}",
            "Result": f"f = {f_design_MPa:.1f} MPa = {f_design:.2f} kN/cm2"
        },
        {
            "Step": "Tính ứng suất do lực dọc",
            "Principle": "Lực dọc phân bố đều trên toàn tiết diện.",
            "Formula": "sigma_N = |N| / A",
            "Values": f"N={N} kN, A={Area_cm2} cm2",
            "Result": f"sigma_N = {sigma_N:.2f} kN/cm2"
        },
        {
            "Step": "Tính ứng suất do momen uốn",
            "Principle": "Ứng suất pháp lớn nhất tại thớ biên tiết diện.",
            "Formula": "sigma_M = |M| / Wx",
            "Values": f"M={M} kN.m = {M_kcm} kN.cm, Wx={Wx_cm3} cm3",
            "Result": f"sigma_M = {sigma_M:.2f} kN/cm2"
        },
        {
            "Step": "Kiểm tra bền theo ứng suất pháp",
            "Principle": "Tổng ứng suất nén-uốn không vượt cường độ tính toán.",
            "Formula": "sigma_max = sigma_N + sigma_M <= f * gamma_c",
            "Citation": {"Ma_TC": "TCVN 5575:2012", "Dieu_Muc": "Điều 5.2 - Cấu kiện chịu nén uốn", "Bang_Hinh": "", "Trang": "38", "Trich_Yeu": "Kiểm tra bền cấu kiện thép chịu nén uốn"},
            "Values": f"sigma_N={sigma_N:.2f}, sigma_M={sigma_M:.2f}, f={f_design:.2f}, gamma_c={gamma_c}",
            "Result": f"sigma_max = {sigma_max:.2f} kN/cm2 vs [f] = {f_allow:.2f} kN/cm2",
            "Utilization": f"eta = {utilization_ratio:.3f} ({utilization_ratio * 100:.1f}%)",
            "Rating": rating,
            "Remark": ("Dự trữ an toàn còn lớn — xem xét giảm tiết diện (Value Engineering)."
                       if utilization_ratio <= 0.70 else
                       "Sát ngưỡng — cần kiểm tra kỹ ổn định tổng thể." if utilization_ratio > 0.90 and utilization_ratio <= 1.0 else
                       "KHÔNG ĐẠT — tăng tiết diện hoặc tăng mác thép." if utilization_ratio > 1.0 else
                       "Đạt, mức sử dụng hợp lý.")
        }
    ]

    return {
        "M_input": M,
        "N_input": N,
        "Area_input": Area,
        "Wx_input": Wx,
        "fy_input": fy,
        "gamma_M": gamma_M,
        "gamma_c": gamma_c,
        "f_design_MPa": round(f_design_MPa, 1),
        "sigma_max": round(sigma_max, 2),
        "f_allow": round(f_allow, 2),
        "utilization_ratio": round(utilization_ratio, 3),
        "Rating": rating,
        "Status": status,
        "Unit": "kN/cm2",
        "Standard": "TCVN 5575:2012",
        "Standard_Method": "TCVN 5575:2012",
        "Scope_Limitation": "Chỉ kiểm tra BỀN theo ứng suất pháp. CHƯA kiểm tra ổn định tổng thể (LTB) và ổn định cục bộ.",
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steel Member Check (TCVN 5575:2012)")
    parser.add_argument("--M", type=float, required=True, help="Momen (kN.m)")
    parser.add_argument("--N", type=float, required=True, help="Lực dọc (kN)")
    parser.add_argument("--Area", type=float, required=True, help="Diện tích (cm2)")
    parser.add_argument("--Wx", type=float, required=True, help="Momen kháng uốn (cm3)")
    parser.add_argument("--fy", type=float, required=True, help="Giới hạn chảy (MPa)")
    parser.add_argument("--gamma_c", type=float, default=1.0, help="Hệ số điều kiện làm việc (mặc định 1.0)")
    args = parser.parse_args()

    result = check_steel_member(args.M, args.N, args.Area, args.Wx, args.fy, args.gamma_c)
    print(json.dumps(result, indent=2, ensure_ascii=False))
