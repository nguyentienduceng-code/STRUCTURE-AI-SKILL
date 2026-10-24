import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_anchorage_lap.py — Tinh chieu dai neo va noi chong cot thep
# =============================================================================
# Phien ban: TCVN 5574:2018
# Reference:
#   - Muc 10.3.5  : Neo cot thep
#     + CT (255)  : L_0,an = (R_s * A_s) / (R_bond * u_s) = (R_s * d_s) / (4 * R_bond)
#     + CT (256)  : R_bond = eta_1 * eta_2 * R_bt
#     + CT (257)  : L_an = alpha_an * L_0,an * (As_req / As_prov)
#     + CT (258)  : L_an >= max(0.3*L_0,an, 15*d_s, 200)
#   - Muc 10.3.6  : Noi chong cot thep
#     + CT (259)  : L_lap = alpha_lap * L_0,an * (As_req / As_prov) >= max(0.4*alpha_lap*L_0,an, 20*d_s, 250)
# =============================================================================

# --- Cuong do vat lieu TCVN 5574:2018 (MPa) ---
RB_MAP = {
    "B12.5": 7.5, "B15": 8.5, "B20": 11.5, "B22.5": 13.0,
    "B25": 14.5, "B30": 17.0, "B35": 19.5, "B40": 22.0,
    "B45": 25.0, "B50": 27.5, "B55": 30.0, "B60": 33.0
}
RBT_MAP = {
    "B12.5": 0.66, "B15": 0.75, "B20": 0.90, "B22.5": 1.00,
    "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40,
    "B45": 1.50, "B50": 1.60, "B55": 1.70, "B60": 1.80
}
RS_MAP = {
    "CB240-T": 210, "CB300-T": 260, "CB300-V": 260,
    "CB400-V": 350, "CB500-V": 435
}
RSC_MAP = {
    "CB240-T": 210, "CB300-T": 260, "CB300-V": 260,
    "CB400-V": 350, "CB500-V": 400
}

# --- He so eta_1 (TCVN 5574:2018 CT 256, Muc 10.3.5.2) ---
# eta_1: phu thuoc loai cot thep
ETA_1_DEFORMED = 2.5    # thep co gan (CB300-V, CB400-V, CB500-V)
ETA_1_SMOOTH = 1.5      # thep tron (CB240-T, CB300-T)

# --- He so eta_2 (TCVN 5574:2018 CT 256, Muc 10.3.5.2) ---
# eta_2: phu thuoc duong kinh thanh cot thep
ETA_2_LE_32 = 1.0        # d_s <= 32 mm
ETA_2_GT_32 = 0.9        # d_s = 36 mm hoac 40 mm

# --- He so alpha_an (TCVN 5574:2018 CT 257, Muc 10.3.5.3) ---
# alpha_an: phu thuoc trang thai chiu luc
ALPHA_AN = {
    "tension_deformed": 1.0,     # thep gan chiu keo
    "compression_deformed": 0.75, # thep gan chiu nen
    "tension_smooth": 1.0,       # thep tron chiu keo (tham chieu)
    "compression_smooth": 0.75,   # thep tron chiu nen (tham chieu)
}

# --- He so alpha_lap (TCVN 5574:2018 CT 259, Muc 10.3.6.3) ---
# alpha_lap: phu thuoc trang thai chiu luc va ty le noi chong (splice_ratio)
ALPHA_LAP = {
    "tension_deformed": 1.2,     # thep gan chiu keo (khi r_lap <= 50%)
    "compression_deformed": 0.9,  # thep gan chiu nen
    "tension_smooth": 1.2,       # thep tron chiu keo
    "compression_smooth": 0.9,    # thep tron chiu nen
}

# --- Gioi han duoi (TCVN 5574:2018 CT 258, CT 259, Muc 10.3.5-10.3.6) ---
# CT (258): L_an >= max(0.3 * L_0,an, 15 * d_s, 200 mm)
L_AN_MIN_FACTOR = 0.3
L_AN_MIN_D_FACTOR = 15          # * d_s
L_AN_MIN_ABS = 200             # mm

# CT (259): L_lap >= max(0.4 * alpha_lap * L_0,an, 20 * d_s, 250 mm)
L_LAP_MIN_FACTOR = 0.4
L_LAP_MIN_D_FACTOR = 20       # * d_s
L_LAP_MIN_ABS = 250            # mm


def _is_deformed(rebar):
    """Kiem tra cot thep co gai hay tron theo TCVN 5574:2018"""
    if "T" in str(rebar).upper():  # CB...-T: tron (T = tron)
        return False
    return True  # V = co gai (V = vân/gân)


def _get_eta_1(rebar):
    """He so eta_1: phu thuoc loai cot thep (CT 256)"""
    return ETA_1_DEFORMED if _is_deformed(rebar) else ETA_1_SMOOTH


def _get_eta_2(dia):
    """He so eta_2: phu thuoc duong kinh (CT 256)"""
    return ETA_2_LE_32 if dia <= 32 else ETA_2_GT_32


def _get_alpha_an(stress_type, rebar):
    """He so alpha_an (CT 257, Muc 10.3.5.3)"""
    deformed = _is_deformed(rebar)
    if stress_type == "tension":
        return ALPHA_AN["tension_deformed" if deformed else "tension_smooth"]
    else:
        return ALPHA_AN["compression_deformed" if deformed else "compression_smooth"]


def _get_alpha_lap(stress_type, rebar, splice_ratio=None):
    """
    He so alpha_lap (CT 259, Muc 10.3.6.3).
    Khi chiu keo:
      Neu splice_ratio duoc cung cap:
        r_lap <= 0.50: alpha_lap = 1.2
        r_lap >= 1.00: alpha_lap = 2.0
        0.50 < r_lap < 1.00: noi suy tuyen tinh tu 1.2 den 2.0 theo TCVN 5574:2018 Muc 10.3.6.2:
          alpha_lap = 1.2 + 0.8 * (r - 0.5) / 0.5
      Neu khong: mac dinh 1.2
    Khi chiu nen: alpha_lap = 0.9
    """
    deformed = _is_deformed(rebar)
    if stress_type == "tension":
        base_val = ALPHA_LAP["tension_deformed" if deformed else "tension_smooth"]
        if splice_ratio is not None:
            try:
                r = float(splice_ratio)
                if r > 1.0 and r <= 100.0:
                    r = r / 100.0
                if r <= 0.5:
                    return 1.2
                elif r >= 1.0:
                    return 2.0
                else:
                    return round(1.2 + 0.8 * (r - 0.5) / 0.5, 3)
            except (ValueError, TypeError):
                return base_val
        return base_val
    else:
        return ALPHA_LAP["compression_deformed" if deformed else "compression_smooth"]


def calc_anchorage_lap(dia=16, rebar="CB400-V", concrete="B25",
                       stress_type="tension",  # "tension" / "compression"
                       end_type="straight",    # "straight" / "hook"
                       As_req=None, As_prov=None,
                       # Tham so noi chong
                       lap_zone=None,          # "tension" / "compression" (None -> mac dinh theo stress_type)
                       lap_as_ratio=None,      # As_req/As_prov (mac dinh = 1.0)
                       splice_ratio=None,      # Ty le cot thep noi chong tai 1 tiet dien (0.2 -> 1.0)
                       seismic=False,          # Tinh toan xet den yeu cau khang chan TCVN 9386-1:2025
                       lap_class="Class_B"):    # deprecated, kept for backward compat
    """
    Tinh chieu dai neo (L_an) va chieu dai noi chong (L_lap)
    theo TCVN 5574:2018 Muc 10.3.5 (CT 255-258) va Muc 10.3.6 (CT 259).

    Args:
        dia           : Duong kinh cot thep (mm)
        rebar         : Loai cot thep (CB240-T, CB300-T, CB300-V, CB400-V, CB500-V)
        concrete      : Cap do ben be tong (B12.5..B60)
        stress_type   : "tension" (keo) / "compression" (nen)
        end_type      : "straight" (thang) / "hook" (moc uon)
        As_req        : Dien tich cot thep yeu cau (mm2) — de tinh as_ratio
        As_prov       : Dien tich cot thep thuc te (mm2)
        lap_zone      : Vung noi chong ("tension" / "compression", mac dinh theo stress_type)
        lap_as_ratio  : Ty le As_req/As_prov (mac dinh = 1.0)
        splice_ratio  : Ty le noi chong tai mot tiet dien (noi suy alpha_lap tu 1.2 den 2.0)
        seismic       : Yeu cau khang chan theo TCVN 9386-1:2025
    """
    Rb = RB_MAP.get(concrete, 14.5)
    Rbt = RBT_MAP.get(concrete, 1.05)

    if stress_type == "compression":
        Rs = RSC_MAP.get(rebar, RS_MAP.get(rebar, 350))
    else:
        Rs = RS_MAP.get(rebar, 350)

    deformed = _is_deformed(rebar)
    eta_1 = _get_eta_1(rebar)
    eta_2 = _get_eta_2(dia)

    if lap_zone is None:
        lap_zone = stress_type

    logs = []
    unverified = []
    warnings = []

    # Canh bao d > 40mm va thep tron tron chiu keo neo thang
    if dia > 40:
        warnings.append(
            f"Đường kính cốt thép d = {dia} mm > 40 mm vượt quá phạm vi áp dụng thông thường "
            f"của TCVN 5574:2018 (cần thí nghiệm kéo tuột hoặc chỉ dẫn thiết kế chuyên biệt)."
        )

    if not deformed and stress_type == "tension" and end_type == "straight":
        warnings.append(
            f"Cốt thép tròn trơn {rebar} chịu kéo neo thẳng không đáp ứng yêu cầu cấu tạo neo "
            f"theo TCVN 5574:2018 Mục 10.3.5.1 (bắt buộc phải uốn móc hoặc hàn chi tiết neo chặn)."
        )

    # =========================================================================
    # 1. CUONG DO BAM DINH TINH TOAN (CT 256)
    # =========================================================================
    R_bond = eta_1 * eta_2 * Rbt  # MPa

    logs.append({
        "Step": 1,
        "Description": "Cường độ bám dính tính toán (R_bond)",
        "Principle": "R_bond là cường độ bám dính của bê tông với thanh cốt thép; "
                      "phụ thuộc vào loại thép (eta_1) và đường kính (eta_2).",
        "Formula": "R_bond = eta_1 * eta_2 * R_bt",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.5.2",
            "Bang_Hinh": "CT (256)",
            "Trang": "139"
        },
        "Substitution": f"eta_1 = {eta_1} ({'thép có gân' if deformed else 'thép trơn'}), "
                        f"eta_2 = {eta_2} (d_s = {dia} mm), R_bt = {Rbt} MPa",
        "Result": f"R_bond = {eta_1} * {eta_2} * {Rbt} = {R_bond:.3f} MPa"
    })

    # =========================================================================
    # 2. CHIEU DAI NEO CO SO (CT 255)
    # =========================================================================
    L_0_an = (Rs * dia) / (4.0 * R_bond)  # mm

    logs.append({
        "Step": 2,
        "Description": "Chiều dài neo cơ sở (L_0,an)",
        "Principle": "Cân bằng lực kéo trong thanh cốt thép với lực dính kết bê tông quanh thanh.",
        "Formula": "L_0,an = (R_s * A_s) / (R_bond * u_s) = (R_s * d_s) / (4 * R_bond)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.5.2",
            "Bang_Hinh": "CT (255)",
            "Trang": "139"
        },
        "Substitution": f"R_s = {Rs} MPa, d_s = {dia} mm, R_bond = {R_bond:.3f} MPa",
        "Result": f"L_0,an = ({Rs} * {dia}) / (4 * {R_bond:.3f}) = {L_0_an:.1f} mm = {L_0_an/dia:.1f} * d_s"
    })

    # =========================================================================
    # 3. HE SO alpha_an (CT 257)
    # =========================================================================
    alpha_an = _get_alpha_an(stress_type, rebar)

    logs.append({
        "Step": 3,
        "Description": "Hệ số alpha_an",
        "Principle": "Phụ thuộc trạng thái chịu lực: chịu kéo cần alpha_an = 1.0, chịu nén alpha_an = 0.75.",
        "Formula": f"alpha_an = {alpha_an}",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.5.3",
            "Bang_Hinh": "CT (257)",
            "Trang": "140"
        },
        "Substitution": f"stress_type = {stress_type}, {'thép có gân' if deformed else 'thép trơn'}",
        "Result": f"alpha_an = {alpha_an}"
    })

    # =========================================================================
    # 4. CHIEU DAI NEO TINH TOAN (CT 257, CT 258)
    # =========================================================================
    if lap_as_ratio is not None:
        as_ratio = min(1.0, float(lap_as_ratio))
    elif As_req is not None and As_prov is not None and As_prov > 0:
        as_ratio = min(1.0, float(As_req) / float(As_prov))
    else:
        as_ratio = 1.0

    L_an = alpha_an * L_0_an * as_ratio  # mm

    # Gioi han duoi (CT 258)
    L_an_min_factor = max(L_AN_MIN_FACTOR * L_0_an,
                          L_AN_MIN_D_FACTOR * dia,
                          L_AN_MIN_ABS)
    L_an_final = max(L_an, L_an_min_factor)

    logs.append({
        "Step": 4,
        "Description": "Chiều dài neo tính toán (L_an)",
        "Principle": "L_an = alpha_an * L_0,an * (As_req/As_prov), không nhỏ hơn giới hạn dưới.",
        "Formula": "L_an = alpha_an * L_0,an * as_ratio  |  L_an >= max(0.3*L_0,an, 15*d_s, 200)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.5.3",
            "Bang_Hinh": "CT (257), CT (258)",
            "Trang": "140"
        },
        "Substitution": f"alpha_an = {alpha_an}, L_0,an = {L_0_an:.1f} mm, "
                        f"as_ratio = {as_ratio:.3f}",
        "Result": (
            f"L_an = {alpha_an} * {L_0_an:.1f} * {as_ratio:.3f} = {L_an:.1f} mm | "
            f"L_an,min = max(0.3*{L_0_an:.1f}, {L_AN_MIN_D_FACTOR}*{dia}, {L_AN_MIN_ABS}) "
            f"= {L_an_min_factor:.1f} mm | L_an_chon = {L_an_final:.1f} mm"
        )
    })

    # =========================================================================
    # 5. CHIEU DAI NOI CHONG (CT 259)
    # =========================================================================
    alpha_lap = _get_alpha_lap(lap_zone, rebar, splice_ratio=splice_ratio)

    L_lap = alpha_lap * L_0_an * as_ratio  # mm

    # Gioi han duoi (CT 259)
    L_lap_min_factor = max(
        L_LAP_MIN_FACTOR * alpha_lap * L_0_an,
        L_LAP_MIN_D_FACTOR * dia,
        L_LAP_MIN_ABS
    )
    L_lap_final = max(L_lap, L_lap_min_factor)

    logs.append({
        "Step": 5,
        "Description": "Chiều dài nối chồng (L_lap)",
        "Principle": "Nối chồng truyền 100% lực thép; L_lap = alpha_lap * L_0,an * as_ratio, "
                     "không nhỏ hơn giới hạn dưới. Hệ số alpha_lap nội suy từ 1.2 đến 2.0 theo tỷ lệ nối chồng.",
        "Formula": "L_lap = alpha_lap * L_0,an * as_ratio  |  L_lap >= max(0.4*alpha_lap*L_0,an, 20*d_s, 250)",
        "Citation": {
            "Ma_TC": "TCVN 5574:2018",
            "Dieu_Muc": "Mục 10.3.6.3",
            "Bang_Hinh": "CT (259)",
            "Trang": "141"
        },
        "Substitution": f"alpha_lap = {alpha_lap} (splice_ratio={splice_ratio}), L_0,an = {L_0_an:.1f} mm, "
                        f"as_ratio = {as_ratio:.3f}",
        "Result": (
            f"L_lap = {alpha_lap} * {L_0_an:.1f} * {as_ratio:.3f} = {L_lap:.1f} mm | "
            f"L_lap,min = max(0.4*{alpha_lap}*{L_0_an:.1f}, {L_LAP_MIN_D_FACTOR}*{dia}, {L_LAP_MIN_ABS}) "
            f"= {L_lap_min_factor:.1f} mm | L_lap_chon = {L_lap_final:.1f} mm"
        )
    })

    # =========================================================================
    # 6. XET KEO DAI KHI KHANG CHAN (TCVN 9386-1:2025)
    # =========================================================================
    if seismic:
        seismic_factor = 1.3
        L_an_final = round(L_an_final * seismic_factor, 1)
        L_lap_final = round(L_lap_final * seismic_factor, 1)
        logs.append({
            "Step": 6,
            "Description": "Gia tăng chiều dài neo/nối chồng theo yêu cầu kháng chấn",
            "Principle": "Theo TCVN 9386-1:2025, cấu kiện chịu động đất cần tăng chiều dài neo/nối chồng để đảm bảo độ dẻo.",
            "Formula": "L_an,seis = 1.3 * L_an; L_lap,seis = 1.3 * L_lap",
            "Citation": {
                "Ma_TC": "TCVN 9386-1:2025",
                "Dieu_Muc": "Mục 5.6",
                "Bang_Hinh": "Bảng yêu cầu cấu tạo kháng chấn",
                "Trang": "125"
            },
            "Substitution": f"gamma_seismic = {seismic_factor}",
            "Result": f"L_an,seis = {L_an_final} mm, L_lap,seis = {L_lap_final} mm"
        })

    # =========================================================================
    # 7. TONG HOP & KET LUAN
    # =========================================================================
    return {
        "dia_mm": dia,
        "rebar": rebar,
        "concrete": concrete,
        "Rb_MPa": Rb,
        "Rbt_MPa": Rbt,
        "Rs_MPa": Rs,
        "Rsc_MPa": RSC_MAP.get(rebar, Rs),
        "deformed_bar": deformed,
        "eta_1": eta_1,
        "eta_2": eta_2,
        "R_bond_MPa": round(R_bond, 4),
        "stress_type": stress_type,
        "alpha_an": alpha_an,
        "L_0_an_mm": round(L_0_an, 1),
        "as_ratio": round(as_ratio, 4),
        "splice_ratio": splice_ratio,
        "seismic": seismic,
        "L_an_mm": round(L_an_final, 1),
        "L_an_min_check_mm": round(L_an_min_factor, 1),
        "L_an_exceeds_min": L_an >= L_an_min_factor,
        "lap_zone": lap_zone,
        "alpha_lap": alpha_lap,
        "L_lap_mm": round(L_lap_final, 1),
        "L_lap_min_check_mm": round(L_lap_min_factor, 1),
        "L_lap_exceeds_min": L_lap >= L_lap_min_factor,
        "Standard": "TCVN 5574:2018",
        "Standard_Method": "TCVN 5574:2018",
        "Scope_Limitation": (
            "Thép cốt đơn, neo thẳng. "
            "CHƯA kiểm tra: neo hàn, neo cơ bắp, neo ép ống, thép nhiều lớp."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_anchorage_lap(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # Sample mac dinh (Φ16, CB400-V Rs=350MPa, B25 Rbt=1.05MPa, keo):
        # R_bond = 2.5 * 1.0 * 1.05 = 2.625 MPa
        # L_0,an = (350 * 16) / (4 * 2.625) = 5600 / 10.5 = 533.3 mm (~33.3 d_s)
        # L_an = 1.0 * 533.3 * 1.0 = 533.3 mm (~533 mm)
        # L_lap = 1.2 * 533.3 * 1.0 = 640.0 mm (40 d_s)
        sample = calc_anchorage_lap(
            dia=16, rebar="CB400-V", concrete="B25",
            stress_type="tension"
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))

