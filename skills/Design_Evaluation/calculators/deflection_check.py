import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse


def get_tcvn_2737_2023_table_g1_limit_mm(
    L_m: float,
    room_height_le_6m: bool = True,
    cantilever: bool = False,
) -> float:
    """
    Nội suy tuyến tính độ võng đứng giới hạn f_u (mm) theo TCVN 2737:2023
    (Bảng G.1 Mục 2a, Chú thích 1-3, trang 80-81; thay thế Phụ lục M TCVN 5574:2018).
    """
    if L_m <= 0:
        raise ValueError("Nhịp L_m phải dương (> 0).")
    L_eff_m = 2.0 * float(L_m) if cantilever else float(L_m)
    points = (
        [
            (1.0, 1000.0 / 120.0),
            (3.0, 3000.0 / 150.0),
            (6.0, 6000.0 / 200.0),
            (12.0, 12000.0 / 250.0),
            (24.0, 24000.0 / 300.0),
        ]
        if room_height_le_6m
        else [
            (1.0, 1000.0 / 120.0),
            (3.0, 3000.0 / 150.0),
            (6.0, 6000.0 / 200.0),
            (24.0, 24000.0 / 250.0),
            (36.0, 36000.0 / 300.0),
        ]
    )
    if L_eff_m <= points[0][0]:
        return round((L_eff_m * 1000.0) / 120.0, 4)
    if L_eff_m >= points[-1][0]:
        return round((L_eff_m * 1000.0) / 300.0, 4)
    for (x0, fu0), (x1, fu1) in zip(points[:-1], points[1:]):
        if x0 <= L_eff_m <= x1:
            return round(fu0 + (fu1 - fu0) * (L_eff_m - x0) / (x1 - x0), 4)
    return round((L_eff_m * 1000.0) / 300.0, 4)


def get_tcvn_2737_2023_table_g1_limit_ratio(
    L_m: float,
    room_height_le_6m: bool = True,
    cantilever: bool = False,
) -> float:
    """
    Trả về mẫu số quy đổi tương đương L_eff / f_u từ độ võng giới hạn f_u (mm) theo Bảng G.1.
    """
    L_eff_m = 2.0 * float(L_m) if cantilever else float(L_m)
    f_u_mm = get_tcvn_2737_2023_table_g1_limit_mm(
        L_m,
        room_height_le_6m=room_height_le_6m,
        cantilever=cantilever,
    )
    return round((L_eff_m * 1000.0) / f_u_mm, 2)


def calculate_deflection(
    L,
    M,
    E,
    I_eff,
    long_term_coeff=2.0,
    limit_ratio=None,
    standard_mode="TCVN_2737_2023",
    room_height_le_6m=True,
    cantilever=False,
):
    """
    Tính kiểm tra độ võng đàn hồi (Dầm 2 gối hoặc công xôn chịu tải phân bố đều).
    L: Nhịp dầm hoặc chiều dài vươn công xôn (m)
    M: Mô men uốn lớn nhất do tải phân bố đều (kN.m): qL^2/8 (dầm 2 gối) hoặc qL^2/2 tại ngàm (công xôn)
    E: Mô đun đàn hồi bê tông (kPa)
    I_eff: Mô men quán tính hiệu dụng (m4)
    long_term_coeff: Hệ số xét đến từ biến dài hạn
    standard_mode: "TCVN_2737_2023" (hồ sơ mới, mặc định) | "TCVN_5574_2018_LEGACY" (đối chiếu hồ sơ cũ)
    """
    if standard_mode not in ("TCVN_2737_2023", "TCVN_5574_2018_LEGACY"):
        raise ValueError(f"standard_mode không hợp lệ: {standard_mode}")

    L_lookup_m = float(L) / 1000.0 if float(L) > 100.0 else float(L)
    L_eff_m = (2.0 * L_lookup_m) if cantilever else L_lookup_m
    if limit_ratio is not None:
        eff_limit_ratio = float(limit_ratio)
        allowable_deflection_mm = (L_eff_m * 1000.0) / eff_limit_ratio
        limit_source = "user_override"
    elif standard_mode == "TCVN_2737_2023":
        allowable_deflection_mm = get_tcvn_2737_2023_table_g1_limit_mm(
            L_lookup_m,
            room_height_le_6m=room_height_le_6m,
            cantilever=cantilever,
        )
        eff_limit_ratio = (L_eff_m * 1000.0) / allowable_deflection_mm
        limit_source = "TCVN 2737:2023 Bảng G.1 Mục 2a"
    else:
        eff_limit_ratio = 250.0
        allowable_deflection_mm = (L_eff_m * 1000.0) / eff_limit_ratio
        limit_source = "TCVN 5574:2018 Phụ lục M (Legacy)"

    if cantilever:
        # Công xôn chịu tải phân bố đều: M_max = qL^2/2 -> delta_e = qL^4/(8EI) = M*L^2/(4EI)
        delta_e = (1.0 / 4.0) * (M * L**2) / (E * I_eff)
        step1_formula = "delta_e = (1/4) * (M * L^2) / (E * I_eff) [công xôn]"
        scope_note = ("Cấu kiện công xôn chiều dài vươn L, tải phân bố đều (M = qL^2/2 tại ngàm), "
                      "giới hạn tra Bảng G.1 với L_eff = 2L theo Chú thích 1 TCVN 2737:2023.")
    else:
        # Võng đàn hồi giữa nhịp dầm đơn giản phân bố đều: delta_e = (5/48) * (M * L^2) / (E * I)
        delta_e = (5.0 / 48.0) * (M * L**2) / (E * I_eff)
        step1_formula = "delta_e = (5/48) * (M * L^2) / (E * I_eff)"
        scope_note = ("Dầm đơn giản 2 gối, tải phân bố đều, tiết diện không nứt (I_eff nhập vào). "
                      "Hệ số từ biến là giá trị ước lượng do người dùng nhập, không tra từ tiêu chuẩn — "
                      "cần kiểm tra lại theo TCVN 5574:2018 & TCVN 2737:2023 với cấu kiện quan trọng.")
    delta_e_mm = delta_e * 1000.0

    delta_long_term_mm = delta_e_mm * long_term_coeff

    status = "PASS" if delta_long_term_mm <= allowable_deflection_mm else "FAIL"
    eta = delta_long_term_mm / allowable_deflection_mm
    rating = "GREEN" if eta <= 0.70 else "YELLOW" if eta <= 0.90 else "ORANGE" if eta <= 1.0 else "RED"

    if standard_mode == "TCVN_2737_2023":
        standard_label = "TCVN 2737:2023"
        standard_method = "TCVN 2737:2023 (Điều 11 & Phụ lục G, Bảng G.1)"
        citation = {
            "Ma_TC": "TCVN 2737:2023",
            "Dieu_Muc": "Điều 11 & Phụ lục G (G.2.1)",
            "Bang_Hinh": "Bảng G.1 (Mục 2a)",
            "Trang": "80-81",
            "Trich_Yeu": "Độ võng đứng giới hạn f_u nội suy tuyến tính theo Chú thích 1-3 (thay thế Phụ lục M TCVN 5574:2018 theo Lời nói đầu trang 5)",
        }
        legacy_warning = None
    else:
        standard_label = "TCVN 5574:2018"
        standard_method = "TCVN 5574:2018 (Phụ lục M — LEGACY COMPARISON)"
        citation = {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Phụ lục M - Độ võng giới hạn (Đã thay thế bởi TCVN 2737:2023)",
            "Bang_Hinh": "Bảng M.1",
            "Trang": "178",
            "Trich_Yeu": "Độ võng giới hạn cho phép của cấu kiện uốn (đối chiếu hồ sơ cũ)",
        }
        legacy_warning = (
            "Phụ lục M TCVN 5574:2018 đã bị thay thế bởi Điều 11 & Phụ lục G TCVN 2737:2023; "
            "chỉ dùng đối chiếu hồ sơ cũ."
        )

    logs = [
        {
            "Step": "Tính độ võng đàn hồi tức thời",
            "Formula": step1_formula,
            "Values": f"M={M}, L={L}, E={E:.1e}, I_eff={I_eff:.2e}, cantilever={cantilever}",
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
            "Formula": "nội suy tuyến tính f_u theo Bảng G.1" if limit_source.startswith("TCVN 2737") else f"delta_allowable = L_eff / {eff_limit_ratio:g}",
            "Citation": citation,
            "Values": f"L_eff={L_eff_m*1000:g} mm, tỷ số quy đổi = 1/{eff_limit_ratio:.2f} ({limit_source})",
            "Result": f"[f] = {allowable_deflection_mm:.2f} mm  vs  f = {delta_long_term_mm:.2f} mm",
            "Utilization": f"eta = {eta:.3f} ({eta * 100:.1f}%)",
            "Rating": rating,
            "Remark": "ĐẠT" if status == "PASS" else "KHÔNG ĐẠT — tăng chiều cao tiết diện hoặc tăng cốt thép."
        }
    ]

    out = {
        "L_input": L,
        "L_eff_m": round(L_eff_m, 3),
        "M_input": M,
        "E_input": E,
        "I_eff_input": I_eff,
        "cantilever": bool(cantilever),
        "limit_ratio": round(eff_limit_ratio, 2),
        "Limit_Source": limit_source,
        "Standard_Mode": standard_mode,
        "Deflection_mm": round(delta_long_term_mm, 2),
        "Allowable_mm": round(allowable_deflection_mm, 2),
        "utilization_ratio": round(eta, 3),
        "Rating": rating,
        "Status": status,
        "Standard": standard_label,
        "Standard_Method": standard_method,
        "Scope_Limitation": scope_note,
        "Calculation_Logs": logs
    }
    if legacy_warning:
        out["Legacy_Warning"] = legacy_warning
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deflection Check Calculator (TCVN 2737:2023 Điều 11 & Phụ lục G)")
    parser.add_argument("--L", type=float, required=True, help="Nhịp dầm (m)")
    parser.add_argument("--M", type=float, required=True, help="Moment giữa nhịp (kN.m)")
    parser.add_argument("--E", type=float, required=True, help="Mô đun đàn hồi (kPa)")
    parser.add_argument("--I_eff", type=float, required=True, help="Mô men quán tính (m4)")
    parser.add_argument("--coeff", type=float, default=2.0, help="Hệ số từ biến (mặc định 2.0)")
    parser.add_argument("--limit_ratio", type=float, default=None,
                        help="Mẫu số tỷ số võng ghi đè (vd 250 / 400); mặc định tự nội suy theo Bảng G.1 TCVN 2737:2023")
    parser.add_argument("--standard-mode", choices=("TCVN_2737_2023", "TCVN_5574_2018_LEGACY"),
                        default="TCVN_2737_2023",
                        help="Chế độ tiêu chuẩn (mặc định TCVN_2737_2023)")
    parser.add_argument("--room-height-gt-6m", action="store_true",
                        help="Chiều cao phòng > 6 m (Chú thích 3 Bảng G.1)")
    parser.add_argument("--cantilever", action="store_true",
                        help="Cấu kiện công xôn (Chú thích 1 Bảng G.1: L_eff = 2*L)")
    args = parser.parse_args()

    result = calculate_deflection(
        args.L,
        args.M,
        args.E,
        args.I_eff,
        args.coeff,
        args.limit_ratio,
        standard_mode=args.standard_mode,
        room_height_le_6m=not args.room_height_gt_6m,
        cantilever=args.cantilever,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
