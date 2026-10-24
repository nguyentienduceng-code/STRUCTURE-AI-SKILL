import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse


def calculate_wind_load(w0, z, terrain_category, c, gamma_f, gamma_f_source="Data Missing: căn cứ tra cứu gamma_f"):
    """
    Tính thành phần tĩnh của tải trọng gió theo TCVN 2737:2023.

    w0        : Áp lực gió chuẩn theo vùng (daN/m2) — tra QCVN 02:2022 / TCVN 2737:2023
    z         : Độ cao điểm tính (m)
    terrain_category : Dạng địa hình 'A' / 'B' / 'C'
    c         : Hệ số khí động (tra theo sơ đồ công trình)
    gamma_f   : Hệ số độ tin cậy của tải trọng gió — BẮT BUỘC truyền tường minh
    gamma_f_source : Trích dẫn nguồn của gamma_f (điều/bảng/trang)

    ⚠ QUAN TRỌNG — gamma_f KHÔNG có giá trị mặc định:
    TCVN 2737:2023 và TCVN 2737:1995 dùng hai hệ quy đổi áp lực gió khác nhau,
    dẫn tới hai giá trị gamma_f hoàn toàn khác nhau. Truyền nhầm giá trị của hệ
    này vào hệ kia gây sai số rất lớn về phía thiếu an toàn hoặc thừa lãng phí.
    Người dùng PHẢI tra cứu và truyền gamma_f kèm căn cứ (--gamma_f_source).
    """
    # Tham so dang dia hinh
    terrain_params = {
        'A': {'alpha': 0.12, 'k10': 1.18, 'z_min': 2},
        'B': {'alpha': 0.16, 'k10': 1.00, 'z_min': 5},
        'C': {'alpha': 0.22, 'k10': 0.74, 'z_min': 10}
    }

    tc = terrain_category.upper()
    if tc not in terrain_params:
        tc = 'B'

    params = terrain_params[tc]
    z_eff = max(z, params['z_min'])

    k_z = params['k10'] * (z_eff / 10) ** (2 * params['alpha'])
    w_tc = w0 * k_z * c
    w_tt = w_tc * gamma_f

    logs = [
        {
            "Step": "Xác định tham số dạng địa hình",
            "Principle": "Độ nhám mặt đất quyết định biên dạng vận tốc gió theo cao độ.",
            "Formula": "Tra bảng dạng địa hình A/B/C",
            "Citation": {"Ma_TC": "TCVN 2737:2023", "Dieu_Muc": "Điều 10.2 - Dạng địa hình", "Bang_Hinh": "Bảng 6", "Trang": "38", "Trich_Yeu": "Phân loại dạng địa hình A, B, C theo độ nhám bề mặt"},
            "Values": f"Dạng địa hình: {tc}",
            "Result": f"alpha={params['alpha']}, k10={params['k10']}, z_min={params['z_min']} m"
        },
        {
            "Step": "Tính hệ số thay đổi áp lực gió theo cao độ k(z)",
            "Principle": "Áp lực gió tăng theo cao độ theo quy luật hàm mũ.",
            "Formula": "k(z) = k10 * (max(z, z_min) / 10)^(2*alpha)",
            "Citation": {"Ma_TC": "TCVN 2737:2023", "Dieu_Muc": "Điều 10.2.2 - Hệ số k(z)", "Bang_Hinh": "Bảng 7", "Trang": "39", "Trich_Yeu": "Hệ số kể đến sự thay đổi áp lực gió theo độ cao và dạng địa hình"},
            "Values": f"z={z} m, z_eff={z_eff} m, k10={params['k10']}, alpha={params['alpha']}",
            "Result": f"k(z) = {k_z:.3f}"
        },
        {
            "Step": "Tính áp lực gió tiêu chuẩn W_tc",
            "Principle": "Áp lực gió tác dụng lên bề mặt bằng áp lực vùng nhân hệ số cao độ và hệ số khí động.",
            "Formula": "W_tc = W0 * k(z) * c",
            "Values": f"W0={w0} daN/m2, k(z)={k_z:.3f}, c={c}",
            "Result": f"W_tc = {w_tc:.2f} daN/m2"
        },
        {
            "Step": "Tính áp lực gió tính toán W_tt",
            "Principle": "Nhân hệ số độ tin cậy để chuyển sang trạng thái giới hạn thứ nhất.",
            "Formula": "W_tt = W_tc * gamma_f",
            "Citation": {"Ma_TC": "TCVN 2737:2023", "Dieu_Muc": gamma_f_source, "Bang_Hinh": "", "Trang": "37", "Trich_Yeu": "Hệ số độ tin cậy của tải trọng gió gamma_f"},
            "Values": f"W_tc={w_tc:.2f} daN/m2, gamma_f={gamma_f} (nguồn: {gamma_f_source})",
            "Result": f"W_tt = {w_tt:.2f} daN/m2"
        }
    ]

    unverified = []
    if gamma_f_source.startswith("Data Missing"):
        unverified.append(f"gamma_f = {gamma_f} — chưa có căn cứ tra cứu (điều/bảng/trang)")

    return {
        "W0_input": w0,
        "z_input": z,
        "terrain": tc,
        "c": c,
        "gamma_f": gamma_f,
        "gamma_f_source": gamma_f_source,
        "k_z": round(k_z, 3),
        "W_tc": round(w_tc, 2),
        "W_tt": round(w_tt, 2),
        "Unit": "daN/m2",
        "Standard": "TCVN 2737:2023",
        "Standard_Method": "TCVN 2737:2023",
        "Scope_Limitation": "Chỉ tính THÀNH PHẦN TĨNH của tải gió. Nhà cao > 40 m hoặc có tần số dao động riêng thấp phải tính bổ sung thành phần động.",
        "Unverified_Items": unverified,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wind Load Calculator (TCVN 2737:2023) - thanh phan tinh")
    parser.add_argument("--w0", type=float, required=True, help="Áp lực gió chuẩn (daN/m2)")
    parser.add_argument("--z", type=float, required=True, help="Độ cao (m)")
    parser.add_argument("--terrain", type=str, required=True, choices=['A', 'B', 'C'], help="Dạng địa hình")
    parser.add_argument("--c", type=float, required=True, help="Hệ số khí động")
    parser.add_argument("--gamma_f", type=float, required=True,
                        help="Hệ số độ tin cậy tải gió - BẮT BUỘC, không có mặc định (xem STANDARDS_LOCK.md)")
    parser.add_argument("--gamma_f_source", type=str, default="Data Missing: căn cứ tra cứu gamma_f",
                        help="Trích dẫn nguồn gamma_f, VD: 'TCVN 2737:2023 Điều 10.2 Bảng 4 Tr.45'")
    args = parser.parse_args()

    result = calculate_wind_load(args.w0, args.z, args.terrain, args.c, args.gamma_f, args.gamma_f_source)
    print(json.dumps(result, indent=2, ensure_ascii=False))
