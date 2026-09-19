import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse

# TCVN 9362:2012 - Hieu chinh ap luc tieu chuan quy uoc R0
# b1 = 1.0 m (be rong quy uoc), h1 = 2.0 m (do sau quy uoc)
B1_REF = 1.0
H1_REF = 2.0

# k1, k2 tra theo loai dat (TCVN 9362:2012 Phu luc - Bang hieu chinh)
SOIL_COEFF = {
    "cat": {"k1": 0.125, "k2": 0.25, "ten": "Đất cát (trừ cát bụi)"},
    "set": {"k1": 0.050, "k2": 0.20, "ten": "Đất sét, á sét, á cát, cát bụi"},
}


def calculate_bearing_capacity(R0, b, d, gamma_II, soil_type="set", N_tt=None, A_mong=None):
    """
    Hiệu chỉnh áp lực tiêu chuẩn quy ước R0 của nền đất theo TCVN 9362:2012.

    R0        : Áp lực tiêu chuẩn quy ước tra bảng (kPa)
    b         : Bề rộng móng (m)
    d         : Độ sâu chôn móng tính từ cốt quy hoạch (m)
    gamma_II  : Dung trọng trung bình của đất từ đáy móng trở lên (kN/m3)
    soil_type : 'cat' hoặc 'set' — quyết định hệ số k1, k2
    N_tt      : (tuỳ chọn) Tải trọng tiêu chuẩn truyền xuống đáy móng (kN) — để tính eta
    A_mong    : (tuỳ chọn) Diện tích đáy móng (m2) — để tính eta

    PHẠM VI: Đây là bài toán HIỆU CHỈNH R0 tra bảng, KHÔNG phải tính sức chịu tải
    giới hạn theo lý thuyết cân bằng giới hạn (Terzaghi / Vesic). Chỉ áp dụng cho
    móng nông, nền đồng nhất, tải đúng tâm. Không dùng cho móng chịu tải lệch tâm
    lớn, nền nhiều lớp, hoặc gần mái dốc.
    """
    st = soil_type.lower().strip()
    if st not in SOIL_COEFF:
        st = "set"  # Thiên về an toàn: k1, k2 nhỏ hơn
    k1 = SOIL_COEFF[st]["k1"]
    k2 = SOIL_COEFF[st]["k2"]

    logs = []

    # Buoc 1: Hieu chinh theo be rong mong (b1 = 1.0 m)
    R_b = R0 * (1.0 + k1 * (b - B1_REF) / B1_REF)
    logs.append({
        "Step": "Hiệu chỉnh theo bề rộng móng b",
        "Principle": "Móng rộng hơn bề rộng quy ước 1 m huy động được vùng đất chịu lực lớn hơn.",
        "Formula": "R_b = R0 * [1 + k1 * (b - b1) / b1],  b1 = 1.0 m",
        "Citation": {"Ma_TC": "TCVN 9362:2012", "Dieu_Muc": "Hiệu chỉnh áp lực quy ước R0", "Bang_Hinh": f"k1 = {k1} ({SOIL_COEFF[st]['ten']})", "Trang": ""},
        "Values": f"R0={R0} kPa, b={b} m, k1={k1}",
        "Result": f"R_b = {R_b:.2f} kPa"
    })

    # Buoc 2: Hieu chinh theo do sau chon mong (h1 = 2.0 m)
    if d >= H1_REF:
        R = R_b + k2 * gamma_II * (d - H1_REF)
        logs.append({
            "Step": "Hiệu chỉnh theo độ sâu chôn móng d (d >= 2 m)",
            "Principle": "Đất phủ trên đáy móng tạo áp lực hông, tăng sức chịu tải nền.",
            "Formula": "R = R_b + k2 * gamma_II * (d - h1),  h1 = 2.0 m",
            "Citation": {"Ma_TC": "TCVN 9362:2012", "Dieu_Muc": "Hiệu chỉnh áp lực quy ước R0", "Bang_Hinh": f"k2 = {k2}", "Trang": ""},
            "Values": f"R_b={R_b:.2f} kPa, d={d} m, gamma_II={gamma_II} kN/m3, k2={k2}",
            "Result": f"R = {R:.2f} kPa"
        })
    else:
        R = R_b * (d + H1_REF) / (2.0 * H1_REF)
        logs.append({
            "Step": "Hiệu chỉnh theo độ sâu chôn móng d (d < 2 m)",
            "Principle": "Móng nông hơn độ sâu quy ước 2 m bị giảm sức chịu tải theo tỷ lệ.",
            "Formula": "R = R_b * (d + h1) / (2 * h1),  h1 = 2.0 m",
            "Citation": {"Ma_TC": "TCVN 9362:2012", "Dieu_Muc": "Hiệu chỉnh áp lực quy ước R0", "Bang_Hinh": "", "Trang": ""},
            "Values": f"R_b={R_b:.2f} kPa, d={d} m",
            "Result": f"R = {R:.2f} kPa"
        })

    result = {
        "R0_input": R0,
        "b_input": b,
        "d_input": d,
        "gamma_II_input": gamma_II,
        "soil_type": st,
        "k1": k1,
        "k2": k2,
        "R_kPa": round(R, 2),
        "Unit": "kPa",
        "Standard": "TCVN 9362:2012",
        "Standard_Method": "TCVN 9362:2012",
        "Scope_Limitation": "Hiệu chỉnh R0 tra bảng cho móng nông, nền đồng nhất, tải đúng tâm. Không áp dụng cho tải lệch tâm lớn, nền nhiều lớp, móng gần mái dốc.",
    }

    # Buoc 3 (tuy chon): Kiem tra ung suat day mong -> eta
    if N_tt is not None and A_mong:
        p_tb = N_tt / A_mong
        eta = p_tb / R
        rating = "GREEN" if eta <= 0.70 else "YELLOW" if eta <= 0.90 else "ORANGE" if eta <= 1.0 else "RED"
        logs.append({
            "Step": "Kiểm tra áp lực đáy móng",
            "Principle": "Áp lực trung bình dưới đáy móng không vượt sức chịu tải hiệu chỉnh của nền.",
            "Formula": "p_tb = N_tc / A <= R",
            "Values": f"N_tc={N_tt} kN, A={A_mong} m2, R={R:.2f} kPa",
            "Result": f"p_tb = {p_tb:.2f} kPa vs R = {R:.2f} kPa",
            "Utilization": f"eta = {eta:.3f} ({eta * 100:.1f}%)",
            "Rating": rating,
            "Remark": "ĐẠT" if eta <= 1.0 else "KHÔNG ĐẠT — cần mở rộng đáy móng hoặc hạ sâu cốt móng."
        })
        result.update({
            "p_tb_kPa": round(p_tb, 2),
            "utilization_ratio": round(eta, 3),
            "Rating": rating,
            "Status": "PASS" if eta <= 1.0 else "FAIL"
        })

    result["Calculation_Logs"] = logs
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Foundation Bearing Capacity (TCVN 9362:2012)")
    parser.add_argument("--R0", type=float, required=True, help="Áp lực tiêu chuẩn quy ước (kPa)")
    parser.add_argument("--b", type=float, required=True, help="Bề rộng móng (m)")
    parser.add_argument("--d", type=float, required=True, help="Độ sâu chôn móng (m)")
    parser.add_argument("--gamma_II", type=float, required=True, help="Dung trọng đất (kN/m3)")
    parser.add_argument("--soil", type=str, default="set", choices=["cat", "set"], help="Loại đất: cat / set")
    parser.add_argument("--N_tt", type=float, default=None, help="Tải tiêu chuẩn xuống đáy móng (kN) - tuỳ chọn")
    parser.add_argument("--A_mong", type=float, default=None, help="Diện tích đáy móng (m2) - tuỳ chọn")
    args = parser.parse_args()

    result = calculate_bearing_capacity(args.R0, args.b, args.d, args.gamma_II,
                                        args.soil, args.N_tt, args.A_mong)
    print(json.dumps(result, indent=2, ensure_ascii=False))
