import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse

def calculate_deflection(L, M, E, I_eff, long_term_coeff=2.0, limit_ratio=250.0):
    """
    Tính kiểm tra độ võng đàn hồi đơn giản (Dầm đơn giản chịu tải phân bố đều).
    L: Nhịp dầm (m)
    M: Moment tĩnh max ở giữa nhịp (kN.m) => tương đương qL^2/8
    E: Mô đun đàn hồi bê tông (kPa)
    I_eff: Moment quán tính hiệu dụng (m4)
    long_term_coeff: Hệ số xét đến từ biến dài hạn
    """
    # Võng đàn hồi giữa nhịp dầm đơn giản phân bố đều: delta_e = (5/48) * (M * L^2) / (E * I)
    delta_e = (5 / 48) * (M * L**2) / (E * I_eff)
    delta_e_mm = delta_e * 1000
    
    delta_long_term_mm = delta_e_mm * long_term_coeff
    
    allowable_deflection_mm = (L * 1000) / limit_ratio

    status = "PASS" if delta_long_term_mm <= allowable_deflection_mm else "FAIL"
    eta = delta_long_term_mm / allowable_deflection_mm
    rating = "GREEN" if eta <= 0.70 else "YELLOW" if eta <= 0.90 else "ORANGE" if eta <= 1.0 else "RED"

    logs = [
        {
            "Step": "Tính độ võng đàn hồi tức thời",
            "Formula": "delta_e = (5/48) * (M * L^2) / (E * I_eff)",
            "Values": f"M={M}, L={L}, E={E:.1e}, I_eff={I_eff:.2e}",
            "Result": f"delta_e = {delta_e_mm:.2f} mm"
        },
        {
            "Step": "Xét ảnh hưởng dài hạn (từ biến)",
            "Formula": "delta_long_term = delta_e * coeff",
            "Values": f"delta_e={delta_e_mm:.2f}, coeff={long_term_coeff}",
            "Result": f"delta_long_term = {delta_long_term_mm:.2f} mm"
        },
        {
            "Step": "Kiểm tra giới hạn độ võng",
            "Principle": "Võng vượt giới hạn gây nứt lớp hoàn thiện và cảm giác không an toàn cho người sử dụng.",
            "Formula": f"delta_allowable = L / {limit_ratio:.0f}",
            "Citation": {"Ma_TC": "TCVN 5574:2018", "Dieu_Muc": "Phụ lục M - Độ võng giới hạn", "Bang_Hinh": "Bảng M.1", "Trang": "178", "Trich_Yeu": "Độ võng giới hạn cho phép của cấu kiện uốn"},
            "Values": f"L={L*1000} mm, tỷ số giới hạn = 1/{limit_ratio:.0f}",
            "Result": f"[f] = {allowable_deflection_mm:.1f} mm  vs  f = {delta_long_term_mm:.2f} mm",
            "Utilization": f"eta = {eta:.3f} ({eta * 100:.1f}%)",
            "Rating": rating,
            "Remark": "ĐẠT" if status == "PASS" else "KHÔNG ĐẠT — tăng chiều cao tiết diện hoặc tăng cốt thép."
        }
    ]

    return {
        "L_input": L,
        "M_input": M,
        "E_input": E,
        "I_eff_input": I_eff,
        "limit_ratio": limit_ratio,
        "Deflection_mm": round(delta_long_term_mm, 2),
        "Allowable_mm": round(allowable_deflection_mm, 2),
        "utilization_ratio": round(eta, 3),
        "Rating": rating,
        "Status": status,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018 (Phụ lục M)",
        "Scope_Limitation": ("Dầm đơn giản 2 gối, tải phân bố đều, tiết diện không nứt (I_eff nhập vào). "
                             "Hệ số từ biến là giá trị ước lượng do người dùng nhập, không tra từ tiêu chuẩn — "
                             "cần kiểm tra lại theo TCVN 5574:2018 với cấu kiện quan trọng."),
        "Calculation_Logs": logs
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deflection Check Calculator (TCVN 5574:2018)")
    parser.add_argument("--L", type=float, required=True, help="Nhịp dầm (m)")
    parser.add_argument("--M", type=float, required=True, help="Moment giữa nhịp (kN.m)")
    parser.add_argument("--E", type=float, required=True, help="Mô đun đàn hồi (kPa)")
    parser.add_argument("--I_eff", type=float, required=True, help="Mô men quán tính (m4)")
    parser.add_argument("--coeff", type=float, default=2.0, help="Hệ số từ biến (mặc định 2.0)")
    parser.add_argument("--limit_ratio", type=float, default=250.0,
                        help="Mẫu số tỷ số võng cho phép: 250 (thường) / 400 (dầm đỡ tường, kính)")
    args = parser.parse_args()

    result = calculate_deflection(args.L, args.M, args.E, args.I_eff, args.coeff, args.limit_ratio)
    print(json.dumps(result, indent=2, ensure_ascii=False))
