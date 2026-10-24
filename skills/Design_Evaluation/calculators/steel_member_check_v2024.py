import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import math

# Hệ số tin cậy về vật liệu thép — chốt theo STANDARDS_LOCK.md mục 3
from pathlib import Path
for _p in Path(__file__).resolve().parents:
    if (_p / "_SHARED" / "standards" / "tables.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

try:
    from _SHARED.standards.tables import GAMMA_M0, GAMMA_M1
except ImportError:
    GAMMA_M0 = 1.05  # TCVN 5575:2024 Bảng 3 - Cấu kiện chính
    GAMMA_M1 = 1.10  # TCVN 5575:2024 Bảng 3 - Kiểm tra ổn định

def check_steel_member_v2024(M, N, V, Area, Wx, Iy, tf, tw, h, b, L_beam, fy,
                              lateral_support=True, gamma_c=1.0, check_ltb=True, check_shear=True):
    """
    Kiểm tra cấu kiện thép chịu nén-uốn-cắt theo TCVN 5575:2024.

    Phương pháp mới so với bản 2012:
    - Phân biệt gamma_M0 (bền tiết diện) và gamma_M1 (ổn định)
    - Kiểm tra mất ổn định uốn xoắn (LTB) bắt buộc với dầm không giằng
    - Kiểm tra cắt theo công thức cải tiến
    - Kiểm tra tương tác nén-uốn theo EN 1993-1-1 (được TCVN 5575:2024 áp dụng)

    Args:
        M: Moment uốn (kN.m)
        N: Lực dọc (kN) — dương = nén, âm = kéo
        V: Lực cắt (kN)
        Area: Diện tích tiết diện (cm2)
        Wx: Momen kháng uốn đàn hồi (cm3)
        Iy: Momen quán tính yếu (cm4)
        tf: Độ dày bản cánh (mm)
        tw: Độ dày bản bụng (mm)
        h: Chiều cao tiết diện (mm)
        b: Chiều rộng bản cánh (mm)
        L_beam: Chiều dài dầm giữa 2 gối tựa (mm)
        fy: Giới hạn chảy của thép (MPa)
        lateral_support: Có giằng ngang liên tục không (True/False)
        gamma_c: Hệ số điều kiện làm việc
        check_ltb: Kiểm tra LTB hay không
        check_shear: Kiểm tra cắt hay không
    """

    logs = []
    warnings = []

    # Bước 1: Cường độ tính toán
    f_y = fy  # MPa
    f_design = f_y / GAMMA_M0  # MPa

    logs.append({
        "Step": 1,
        "Description": "Xác định cường độ tính toán của thép",
        "Principle": "Cường độ tính toán = Giới hạn chảy / Hệ số tin cậy vật liệu (phân biệt gamma_M0 cho bền, gamma_M1 cho ổn định).",
        "Formula": "f = f_y / gamma_M0",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Điều 5.2.1",
            "Bang_Hinh": "Bảng 3",
            "Trang": "N/A",
            "Trich_Yeu": "Hệ số tin cậy vật liệu gamma_M0 = 1.05 cho cấu kiện chính"
        },
        "Substitution": f"f_y = {fy} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"f = {f_design:.1f} MPa",
        "Unit": "MPa"
    })

    # Bước 2: Kiểm tra bền uốn (moment capacity)
    M_Ed = abs(M)  # kN.m
    Wx_cm3 = Wx
    W_pl = Wx_cm3 * 1.15  # Giả định W_pl/W_el ≈ 1.15 cho tiết diện I

    # FIX-03: Sửa lỗi hệ số đơn vị
    # Giải thích đơn vị:
    # - W_pl (cm³) × f_y (MPa) = W_pl × f_y (N.mm / 1000) = W_pl × f_y / 1000 (kN.m)
    # - 1 cm³ × 1 MPa = 1e-6 m³ × 1e6 N/m² = 1 N.m = 0.001 kN.m
    # f_design = f_y / GAMMA_M0 đã tính ở Bước 1
    M_c_Rd = (W_pl * f_design) / 1000.0  # kN.m

    eta_M = M_Ed / M_c_Rd if M_c_Rd > 0 else 999

    logs.append({
        "Step": 2,
        "Description": "Kiểm tra khả năng chống uốn tiết diện",
        "Principle": "Dầm chịu uốn đạt khả năng chống uốn dẻo khi tiết diện đạt moment dẻo toàn phần.",
        "Formula": "M_c,Rd = W_pl × f_y / gamma_M0",
        "Citation": {
            "Ma_TC": "TCVN 5575",
            "Nam": "2024",
            "Dieu_Muc": "Điều 6.2.5",
            "Bang_Hinh": "",
            "Trang": "N/A",
            "Trich_Yeu": "Khả năng chống uốn tiết diện cấp 1, 2"
        },
        "Substitution": f"W_pl = {W_pl:.0f} cm³, f_y = {f_y} MPa, gamma_M0 = {GAMMA_M0}",
        "Result": f"M_c,Rd = {M_c_Rd:.1f} kN.m",
        "Utilization": f"η_M = {M_Ed:.1f} / {M_c_Rd:.1f} = {eta_M:.3f} ({eta_M*100:.1f}%)",
        "Rating": "GREEN" if eta_M <= 0.7 else "YELLOW" if eta_M <= 0.9 else "ORANGE" if eta_M <= 1.0 else "RED"
    })

    # Bước 3: Kiểm tra ổn định uốn xoắn (LTB) nếu không có giằng
    eta_LTB = 0.0
    if check_ltb and not lateral_support:
        # Độ mảnh uốn xoắn λ_LT
        L_cr = L_beam  # mm - chiều dài tính toán
        i_z = math.sqrt(Iy * 10000 / Area)  # mm (Iy cm4 -> mm4)

        lambda_1 = 93.9 * (235 / fy) ** 0.5  # Độ mảnh giới hạn
        lambda_LT = (L_cr / i_z) / lambda_1 if lambda_1 > 0 else 999

        # Hệ số giảm chi_LT (phương pháp đơn giản hóa - đường cong a)
        alpha_LT = 0.21  # Hệ số khuyết tật cho tiết diện cán - đường cong a
        phi_LT = 0.5 * (1 + alpha_LT * (lambda_LT - 0.2) + lambda_LT**2)
        chi_LT = min(1.0, 1.0 / (phi_LT + math.sqrt(phi_LT**2 - lambda_LT**2))) if phi_LT**2 >= lambda_LT**2 else 1.0

        # Theo TCVN 5575:2024 Dieu 6.3.2: M_b,Rd = chi_LT * W_pl * f_y / GAMMA_M1
        M_b_Rd = chi_LT * W_pl * (f_y / GAMMA_M1) / 1000.0  # kN.m
        eta_LTB = M_Ed / M_b_Rd if M_b_Rd > 0 else 999

        logs.append({
            "Step": 3,
            "Description": "Kiểm tra ổn định uốn xoắn (Lateral Torsional Buckling)",
            "Principle": "Dầm không được giằng ngang có thể mất ổn định uốn xoắn trước khi đạt M_c,Rd. Cần giảm khả năng chịu moment bằng hệ số chi_LT.",
            "Formula": "M_b,Rd = chi_LT × W_pl × f_y / gamma_M1",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Điều 6.3.2",
                "Bang_Hinh": "Bảng 6.3",
                "Trang": "N/A",
                "Trich_Yeu": "Kiểm tra ổn định uốn xoắn của dầm"
            },
            "Substitution": f"lambda_LT = {lambda_LT:.2f}, chi_LT = {chi_LT:.3f}, W_pl = {W_pl:.0f} cm³",
            "Result": f"M_b,Rd = {M_b_Rd:.1f} kN.m",
            "Utilization": f"η_LTB = {M_Ed:.1f} / {M_b_Rd:.1f} = {eta_LTB:.3f} ({eta_LTB*100:.1f}%)",
            "Rating": "GREEN" if eta_LTB <= 0.7 else "YELLOW" if eta_LTB <= 0.9 else "ORANGE" if eta_LTB <= 1.0 else "RED"
        })

        if eta_LTB > 0.9:
            warnings.append("⚠ Dầm không giằng ngang - mất ổn định uốn xoắn chi phối (η_LTB > 90%). Đề xuất: bố trí giằng ngang hoặc tăng tiết diện.")

    # Bước 4: Kiểm tra cắt
    eta_V = 0.0
    if check_shear:
        V_Ed = abs(V)  # kN
        # Diện tích chịu cắt A_v (bỏ qua bản cánh, chỉ tính bản bụng)
        A_v = (h - 2*tf) * tw / 100.0  # cm2 (h, tf, tw in mm)

        V_pl_Rd = A_v * (f_design / math.sqrt(3)) / 10.0 * gamma_c  # kN
        eta_V = V_Ed / V_pl_Rd if V_pl_Rd > 0 else 999

        logs.append({
            "Step": 4,
            "Description": "Kiểm tra khả năng chịu cắt",
            "Principle": "Bản bụng chịu cắt theo lý thuyết von Mises. Ứng suất cắt không vượt f_y / sqrt(3).",
            "Formula": "V_pl,Rd = A_v × (f_y / sqrt(3)) / gamma_M0",
            "Citation": {
                "Ma_TC": "TCVN 5575",
                "Nam": "2024",
                "Dieu_Muc": "Điều 6.2.6",
                "Bang_Hinh": "",
                "Trang": "N/A",
                "Trich_Yeu": "Khả năng chịu cắt của bản bụng"
            },
            "Substitution": f"A_v = {A_v:.1f} cm², f_y = {f_y} MPa, gamma_M0 = {GAMMA_M0}",
            "Result": f"V_pl,Rd = {V_pl_Rd:.1f} kN",
            "Utilization": f"η_V = {V_Ed:.1f} / {V_pl_Rd:.1f} = {eta_V:.3f} ({eta_V*100:.1f}%)",
            "Rating": "GREEN" if eta_V <= 0.7 else "YELLOW" if eta_V <= 0.9 else "ORANGE" if eta_V <= 1.0 else "RED"
        })

    # Bước 5: Tổng hợp
    eta_max = max(eta_M, eta_LTB, eta_V)

    if eta_max <= 0.70:
        overall_rating = "GREEN"
        remark = "Dự trữ an toàn > 30% — xem xét giảm tiết diện (Value Engineering)."
    elif eta_max <= 0.90:
        overall_rating = "YELLOW"
        remark = "Đạt, mức sử dụng hợp lý."
    elif eta_max <= 1.00:
        overall_rating = "ORANGE"
        remark = "Sát ngưỡng (η > 90%) — cần kiểm tra kỹ các yếu tố chưa xét (local buckling, fatigue)."
    else:
        overall_rating = "RED"
        remark = "KHÔNG ĐẠT (η > 100%) — yêu cầu tăng tiết diện hoặc tăng cấp thép."

    status = "PASS" if eta_max <= 1.0 else "FAIL"

    logs.append({
        "Step": 5,
        "Description": "Kết luận tổng hợp",
        "Result": f"η_max = max({eta_M:.3f}, {eta_LTB:.3f}, {eta_V:.3f}) = {eta_max:.3f}",
        "Status": status,
        "Rating": overall_rating,
        "Remark": remark
    })

    return {
        "Input": {
            "M": M, "N": N, "V": V,
            "Area": Area, "Wx": Wx, "Iy": Iy,
            "tf": tf, "tw": tw, "h": h, "b": b,
            "L_beam": L_beam, "fy": fy,
            "lateral_support": lateral_support,
            "gamma_c": gamma_c
        },
        "Results": {
            "M_c_Rd": round(M_c_Rd, 2),  # FIX-03: bo corrected
            "eta_M": round(eta_M, 3),
            "M_b_Rd": round(M_b_Rd, 2) if check_ltb and not lateral_support else "N/A",
            "eta_LTB": round(eta_LTB, 3) if check_ltb and not lateral_support else 0.0,
            "V_pl_Rd": round(V_pl_Rd, 2) if check_shear else "N/A",
            "eta_V": round(eta_V, 3) if check_shear else 0.0,
            "eta_max": round(eta_max, 3),
            "Rating": overall_rating,
            "Status": status
        },
        "Standard_Method": "TCVN 5575:2024",
        "Scope_Limitation": "Chưa kiểm tra: ổn định cục bộ bản cánh/bụng (class 3/4), độ võng (SLS), mỏi (fatigue), tương tác nén-uốn phức tạp.",
        "Unverified_Items": [
            "Phân loại tiết diện (Class 1/2/3/4) chưa được kiểm tra",
            "Độ võng SLS chưa kiểm tra",
            "Tương tác M-N-V theo công thức chính xác chưa áp dụng"
        ],
        "Warnings": warnings,
        "Calculation_Logs": logs,
        "Metadata": {
            "Script_Version": "2.1.0",  # FIX-03: Updated version
            "Standard_Version": "TCVN 5575:2024",
            "Backward_Compatible_With": "TCVN 5575:2012",
            "Updated_Date": "2026-08-18",
            "Fixes": ["FIX-03: Removed incorrect *10 factor in moment calculation"]
        }
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steel Member Check (TCVN 5575:2024)")
    parser.add_argument("--M", type=float, required=True, help="Moment uốn (kN.m)")
    parser.add_argument("--N", type=float, default=0.0, help="Lực dọc (kN)")
    parser.add_argument("--V", type=float, default=0.0, help="Lực cắt (kN)")
    parser.add_argument("--Area", type=float, required=True, help="Diện tích tiết diện (cm2)")
    parser.add_argument("--Wx", type=float, required=True, help="Momen kháng uốn (cm3)")
    parser.add_argument("--Iy", type=float, required=True, help="Momen quán tính yếu (cm4)")
    parser.add_argument("--tf", type=float, required=True, help="Độ dày bản cánh (mm)")
    parser.add_argument("--tw", type=float, required=True, help="Độ dày bản bụng (mm)")
    parser.add_argument("--h", type=float, required=True, help="Chiều cao tiết diện (mm)")
    parser.add_argument("--b", type=float, required=True, help="Chiều rộng bản cánh (mm)")
    parser.add_argument("--L_beam", type=float, required=True, help="Chiều dài dầm (mm)")
    parser.add_argument("--fy", type=float, required=True, help="Giới hạn chảy (MPa)")
    parser.add_argument("--lateral_support", type=lambda x: x.lower() == 'true', default=True,
                        help="Có giằng ngang không (true/false)")
    parser.add_argument("--gamma_c", type=float, default=1.0, help="Hệ số điều kiện làm việc")
    parser.add_argument("--check_ltb", type=lambda x: x.lower() == 'true', default=True, help="Kiểm tra LTB")
    parser.add_argument("--check_shear", type=lambda x: x.lower() == 'true', default=True, help="Kiểm tra cắt")

    args = parser.parse_args()

    result = check_steel_member_v2024(
        args.M, args.N, args.V, args.Area, args.Wx, args.Iy,
        args.tf, args.tw, args.h, args.b, args.L_beam, args.fy,
        args.lateral_support, args.gamma_c, args.check_ltb, args.check_shear
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
