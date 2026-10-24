import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_base_heave.py — MODULE 11: Kiểm tra Ổn định Đáy Hố Đào
# =============================================================================
# Version: 2.3.2
# Standard_Method: Terzaghi (1943), Bjerrum-Eide (1956), CIRIA C760
# Reference: TMTT Sunrise CVPM Quang Trung (đã phê duyệt)
# Kiểm tra: Base Heave / Boiling / Piping cho hố đào trong đất dính
# Fixes v2.3.1: configurable constants (gamma_w, fs_allow, q_surcharge)
# Fixes v2.3.2: Bjerrum-Eide correction tự động cho đất sét yếu
# =============================================================================

# ── Cấu hình có thể override ──
DEFAULT_GAMMA_W = 9.81   # kN/m³ (nước ở 4°C)
DEFAULT_FS_ALLOW = 1.50  # Hệ số an toàn tối thiểu — theo CIRIA C760
DEFAULT_Q_SURCHARGE = 10.0  # kN/m² — hoạt tải thi công mặc định
DEFAULT_PIPING_ALLOW = 1.5  # Hệ số an toàn piping


def calc_Nc_from_BL(B, L):
    """
    Tính hệ số sức chịu tải Nc theo Terzaghi cho hố đào chữ nhật.

    Công thức: Nc = 5.14 × (1 + 0.2 × B/L)
    Nguồn: Terzaghi (1943), Skempton (1951)

    Parameters
    ----------
    B : float
        Bề rộng hố đào (m)
    L : float
        Chiều dài hố đào (m)

    Returns
    -------
    float: Hệ số Nc
    """
    ratio = B / L if L > 0 else 1.0
    Nc = 5.14 * (1 + 0.2 * ratio)
    return round(Nc, 2)


def calc_Nc_inclined(B, L, D=0.0):
    """
    Tính Nc có xét đến ảnh hưởng ngàm cừ/chân tường (Terzaghi).

    Hệ số điều chỉnh: Nc* = Nc × (1 + 0.2 × D/B)  (xấp xỉ)
    """
    Nc_base = calc_Nc_from_BL(B, L)
    if D > 0:
        Nc_adj = Nc_base * (1 + 0.2 * D / B)
        return round(Nc_adj, 2)
    return Nc_base


def calc_gamma_avg(layers, z_top, z_bottom, gwl_depth=-999.0):
    """
    Tính dung trọng trung bình phân lớp từ z_top đến z_bottom.

    Parameters
    ----------
    layers : list
        Danh sách lớp đất [{top_depth, bottom_depth, gamma_sat, gamma_unsat}]
    z_top : float
        Cao độ đỉnh (VD: 0.0)
    z_bottom : float
        Cao độ đáy (VD: -3.95)
    gwl_depth : float
        Cao độ mực nước ngầm (VD: -4.40). Mặc định -999 (luôn dùng gamma_sat).

    Returns
    -------
    float: γ_avg (kN/m³), list of layer contributions
    """
    contributions = []

    for layer in layers:
        # z_l_bot is the deeper boundary of the layer.
        # Limit the contribution to [z_top, z_bottom].
        z_l_top = layer["top_depth"]
        z_l_bot = max(layer["bottom_depth"], z_bottom)  # CAP at z_bottom

        overlap_h = max(0.0, z_l_top - z_l_bot)
        if overlap_h <= 0:
            continue

        # Use gamma_unsat for soil above GWT, gamma_sat for soil below GWT
        gamma_unsat = layer.get("gamma_unsat", layer.get("gamma_sat", 18.0))
        gamma_sat   = layer.get("gamma_sat", layer.get("gamma_unsat", 18.0))

        # Midpoint of the overlapping segment
        mid_z = (z_l_top + z_l_bot) / 2.0
        gamma = gamma_unsat if mid_z > gwl_depth else gamma_sat

        weight = gamma * overlap_h
        contributions.append({
            "layer_id": layer.get("id", layer.get("name", "")),
            "z_segment": f"{z_l_top:.2f}m → {z_l_bot:.2f}m",
            "h_m": round(overlap_h, 3),
            "gamma": round(gamma, 2),
            "weight_kN_m2": round(weight, 2)
        })

    total_weight = sum(c["weight_kN_m2"] for c in contributions)
    total_height = abs(z_bottom - z_top)  # positive height
    gamma_avg = total_weight / total_height if total_height > 1e-9 else 18.0

    return round(gamma_avg, 2), contributions, round(total_weight, 2)


def calc_bjerrum_eide_correction(Su_base_kpa, H_exc_m, B_m, D_pile_m=0.0):
    """
    Tính hệ số hiệu chỉnh Bjerrum-Eide (1956) cho base heave.

    Fix v2.3.2: Bổ sung correction để tính chính xác hơn cho đất sét yếu.

    Công thức:
        Fs_corrected = Fs × μ

    Trong đó μ (hệ số hiệu chỉnh) phụ thuộc vào H/B và D/B:

        μ = f(H/B, D/B)

    Bảng tra nhanh (theo Bjerrum 1973):

        H/B    | D/B=0  | D/B=0.5 | D/B=1.0 | D/B=2.0 |
        --------|--------|---------|---------|---------|
        0.5    | 1.00   | 1.00    | 1.00    | 1.00    |
        1.0    | 1.00   | 0.98    | 0.96    | 0.93    |
        2.0    | 1.00   | 0.93    | 0.87    | 0.79    |
        3.0    | 1.00   | 0.87    | 0.79    | 0.67    |
        4.0    | 1.00   | 0.81    | 0.72    | 0.58    |

    Phương pháp nội suy: song tuyến (bilinear) giữa các điểm grid.

    Tham khảo: Bjerrum & Eide (1956); CIRIA C760; Terzaghi et al. (1996)

    Parameters
    ----------
    Su_base_kpa : float
        Sức kháng cắt không thoát nước trung bình tại đáy hố (kPa)
    H_exc_m : float
        Chiều sâu hố đào (m)
    B_m : float
        Bề rộng hố đào (m)
    D_pile_m : float
        Chiều sâu ngàm cừ dưới đáy hố (m). Mặc định 0 (không ngàm).

    Returns
    -------
    dict: {
        "mu": float,           # Hệ số hiệu chỉnh Bjerrum-Eide
        "H_over_B": float,     # Tỷ số H/B
        "D_over_B": float,     # Tỷ số D/B
        "Su_corrected_kpa": float,  # Su đã hiệu chỉnh = Su / mu
        "note": str
    }
    """
    if B_m <= 0:
        return {
            "mu": 1.0,
            "H_over_B": 0.0,
            "D_over_B": 0.0,
            "Su_corrected_kpa": Su_base_kpa,
            "note": "B=0, không áp dụng hiệu chỉnh"
        }

    H_over_B = H_exc_m / B_m
    D_over_B = D_pile_m / B_m

    # ── Bảng grid Bjerrum-Eide ──
    # H/B values on rows, D/B values on columns
    hb_values = [0.5, 1.0, 2.0, 3.0, 4.0]
    db_values = [0.0, 0.5, 1.0, 2.0]
    mu_table = [
        [1.00, 1.00, 1.00, 1.00],   # H/B = 0.5
        [1.00, 0.98, 0.96, 0.93],   # H/B = 1.0
        [1.00, 0.93, 0.87, 0.79],   # H/B = 2.0
        [1.00, 0.87, 0.79, 0.67],   # H/B = 3.0
        [1.00, 0.81, 0.72, 0.58],   # H/B = 4.0
    ]

    def _bilinear_interp(x, y, x_vals, y_vals, z_table):
        """Nội suy song tuyến 2D."""
        n = len(x_vals)
        m = len(y_vals)

        # Tìm vị trí xen kẽ
        i = 0
        while i < n - 1 and x > x_vals[i + 1]:
            i += 1
        j = 0
        while j < m - 1 and y > y_vals[j + 1]:
            j += 1

        # Giới hạn
        i = min(i, n - 2)
        j = min(j, m - 2)

        x1, x2 = x_vals[i], x_vals[i + 1]
        y1, y2 = y_vals[j], y_vals[j + 1]
        z11 = z_table[i][j]
        z12 = z_table[i][j + 1]
        z21 = z_table[i + 1][j]
        z22 = z_table[i + 1][j + 1]

        # Nội suy song tuyến
        tx = (x - x1) / (x2 - x1) if x2 != x1 else 0.0
        ty = (y - y1) / (y2 - y1) if y2 != y1 else 0.0

        z = (1 - tx) * (1 - ty) * z11 + tx * (1 - ty) * z21 + \
            (1 - tx) * ty * z12 + tx * ty * z22

        return z

    mu = _bilinear_interp(H_over_B, D_over_B, hb_values, db_values, mu_table)

    Su_corrected = Su_base_kpa / mu if mu > 0 else Su_base_kpa

    if H_over_B <= 0.5:
        note = "H/B ≤ 0.5: Không cần hiệu chỉnh (μ = 1.00)"
    elif H_over_B > 4.0:
        note = f"H/B > 4.0: Ngoài phạm vi bảng Bjerrum-Eide (nội suy với H/B=4.0)"
        mu = _bilinear_interp(4.0, D_over_B, hb_values, db_values, mu_table)
        Su_corrected = Su_base_kpa / mu
    else:
        note = (
            f"H/B = {H_over_B:.2f}, D/B = {D_over_B:.2f}: "
            f"μ = {mu:.3f} (Bjerrum & Eide 1956)"
        )

    return {
        "mu": round(mu, 3),
        "H_over_B": round(H_over_B, 3),
        "D_over_B": round(D_over_B, 3),
        "Su_corrected_kpa": round(Su_corrected, 2),
        "note": note,
        "reference": "Bjerrum & Eide (1956); CIRIA C760; Terzaghi et al. (1996)"
    }


def calc_base_heave(excavation_data, layers, gamma_w=None, gwl_depth=-999.0,
                  fs_allow=None, q_surcharge=None):
    """
    Kiểm tra ổn định đáy hố đào (Base Heave Stability Check).

    Công thức tổng quát (Terzaghi 1943):
        Fs = (Nc × Su) / (γ_avg × H + q)

    Fix v2.3.1: Các hằng số có thể override qua config:
        - gamma_w: mặc định 9.81 kN/m³
        - fs_allow: mặc định 1.50 (CIRIA C760)
        - q_surcharge: mặc định 10.0 kN/m²

    Parameters
    ----------
    excavation_data : dict
        {"B_m", "L_m", "H_exc_m", "Su_kpa", "q_kpa", "D_pile_m"}
    layers : list
        Danh sách lớp đất từ mặt đất đến đáy hố
    gamma_w : float or None
        Dung trọng nước (kN/m³). Mặc định = 9.81.
    gwl_depth : float
        Cao độ mực nước ngầm (m, âm).
    fs_allow : float or None
        Hệ số an toàn cho phép. Mặc định = 1.50 (CIRIA C760).
    q_surcharge : float or None
        Hoạt tải mép hố mặc định (kN/m²). Mặc định = 10.0.

    Returns
    -------
    dict với đầy đủ Calculation_Logs
    """
    gw = gamma_w if gamma_w is not None else DEFAULT_GAMMA_W
    Fs_allow_cfg = fs_allow if fs_allow is not None else DEFAULT_FS_ALLOW
    q_default = q_surcharge if q_surcharge is not None else DEFAULT_Q_SURCHARGE
    B = excavation_data.get("B_m")
    L = excavation_data.get("L_m")
    H = excavation_data.get("H_exc_m")
    Su = excavation_data.get("Su_kpa")
    q = excavation_data.get("q_kpa", q_default)  # Fix v2.3.1
    D_pile = excavation_data.get("D_pile_m", 0.0)

    if None in (B, L, H, Su):
        return {"error": "Thiếu dữ liệu bắt buộc: B_m, L_m, H_exc_m, Su_kpa"}

    # ── Bước 1: Tính Nc ─────────────────────────────────────────────────────
    Nc = calc_Nc_from_BL(B, L)
    Nc_calc_steps = [
        f"B = {B} m, L = {L} m",
        f"Tỷ số B/L = {B}/{L} = {B/L:.3f}",
        f"Nc = 5.14 × (1 + 0.2 × {B/L:.3f}) = 5.14 × {1 + 0.2*B/L:.3f} = {Nc}"
    ]

    # ── Bước 2: Tính γ_avg ───────────────────────────────────────────────
    gamma_avg, layer_contribs, total_weight = calc_gamma_avg(
        layers, z_top=0.0, z_bottom=-H, gwl_depth=gwl_depth
    )

    gamma_calc_steps = [f"γ_avg = Σ(γi × hi) / H"]
    for c in layer_contribs:
        gamma_calc_steps.append(
            f"  + {c['layer_id']}: {c['gamma']} kN/m³ × {c['h_m']} m = {c['weight_kN_m2']} kN/m²"
        )
    gamma_calc_steps.append(
        f"  γ_avg = {total_weight:.2f} / {H} = {gamma_avg} kN/m³"
    )

    # ── Bước 3b: Hiệu chỉnh Bjerrum-Eide (Fix v2.3.2) ──────────────
    bjerrum = calc_bjerrum_eide_correction(Su, H, B, D_pile)

    bjerrum_steps = [
        f"Bước 3b: Hiệu chỉnh Bjerrum-Eide (1956)",
        f"  H/B = {bjerrum['H_over_B']:.3f}, D/B = {bjerrum['D_over_B']:.3f}",
        f"  μ = {bjerrum['mu']:.3f}",
        f"  Su đã hiệu chỉnh = {Su} / {bjerrum['mu']:.3f} = {bjerrum['Su_corrected_kpa']:.2f} kPa"
    ]

    Su_eff = bjerrum["Su_corrected_kpa"]

    # ── Bước 4: Tính σ_v tại đáy hố ─────────────────────────────────────
    sigma_v_base = total_weight
    sigma_calc_steps = [
        f"σ_v,base = γ_avg × H + q",
        f"        = {gamma_avg} × {H} + {q}",
        f"        = {sigma_v_base:.2f} + {q} = {sigma_v_base + q:.2f} kPa"
    ]

    sigma_v_base_with_q = sigma_v_base + q

    # ── Bước 5: Tính Fs ───────────────────────────────────────────────────
    Fs = (Nc * Su_eff) / sigma_v_base_with_q if sigma_v_base_with_q > 0 else 0.0
    Fs_allow = Fs_allow_cfg  # v2.3.1: có thể override qua config

    fs_calc_steps = [
        f"Fs = (Nc × Su_eff) / (γ_avg × H + q)",
        f"    = ({Nc} × {Su_eff:.2f}) / ({sigma_v_base_with_q:.2f})",
        f"    = {Nc * Su_eff:.2f} / {sigma_v_base_with_q:.2f}",
        f"    = {Fs:.3f}",
        f"",
        f"[Không hiệu chỉnh Bjerrum-Eide: Fs = {Nc * Su / sigma_v_base_with_q:.3f}]",
        f"[Su_eff = Su/μ = {Su}/{bjerrum['mu']:.3f} = {Su_eff:.2f} kPa]"
    ]

    # ── Bước 5: Đánh giá ──────────────────────────────────────────────────
    eta = Fs_allow / Fs
    if Fs >= 1.50:
        status = "ĐẠT"
        status_note = "Fs ≥ 1.50 — Ổn định đáy hố đào đảm bảo"
    elif Fs >= 1.25:
        status = "Lưu ý"
        status_note = f"1.25 ≤ Fs < 1.50 — Cần theo dõi và có biện pháp kiểm soát"
    else:
        status = "KHÔNG ĐẠT"
        status_note = f"Fs < 1.25 — Nguy cơ mất ổn định đáy hố. Cần tăng chiều sâu ngàm cừ hoặc gia cố đất."

    if eta <= 0.70:
        eta_status = "🟢 An toàn"
    elif eta <= 0.90:
        eta_status = "🟡 Tốt"
    elif eta <= 1.00:
        eta_status = "🟠 Lưu ý"
    else:
        eta_status = "🔴 Vượt giới hạn"

    # ── Bước 6: Biện pháp khuyến nghị ─────────────────────────────────────
    recommendations = []
    if Fs < 1.50:
        recommendations.append({
            "priority": "CAO",
            "action": "Giới hạn hoạt tải trên mép hố",
            "detail": f"Đảm bảo q ≤ {q} kPa. Không bố trí xe bồn, vật liệu nặng trong phạm vi 3m từ mép hố."
        })
        recommendations.append({
            "priority": "CAO",
            "action": "Đổ bê tông lót đáy hố ngay",
            "detail": "Sau khi đào đến đáy hố, cần đổ bê tông lót trong vòng 24 giờ để tạo bản cứng, triệt tiêu biến dạng trồi."
        })
    if D_pile > 0:
        Nc_adj = calc_Nc_inclined(B, L, D_pile)
        if Nc_adj > Nc:
            recommendations.append({
                "priority": "TRUNG BÌNH",
                "action": f"Xét ảnh hưởng ngàm cừ (D={D_pile}m)",
                "detail": f"Nc điều chỉnh ≈ {Nc_adj} (do lực kháng xuyên ngang của cừ). Fs thực tế có thể cao hơn."
            })

    calc_logs = [
        {
            "step": "1. Tính hệ số sức chịu tải Nc (Terzaghi)",
            "formula": "Nc = 5.14 × (1 + 0.2 × B/L)",
            "inputs": Nc_calc_steps,
            "result": f"Nc = {Nc}"
        },
        {
            "step": "2. Tính dung trọng trung bình γ_avg",
            "formula": "γ_avg = Σ(γi × hi) / H",
            "layers": layer_contribs,
            "inputs": gamma_calc_steps,
            "result": f"γ_avg = {gamma_avg} kN/m³"
        },
        {
            "step": "3a. Sức kháng cắt Su",
            "Su_kpa": Su,
            "note": "Từ dữ liệu đầu vào (Lab Test hoặc ước lượng)"
        },
        {
            "step": "3b. Hiệu chỉnh Bjerrum-Eide (v2.3.2)",
            "H_over_B": bjerrum["H_over_B"],
            "D_over_B": bjerrum["D_over_B"],
            "mu": bjerrum["mu"],
            "Su_eff_kpa": bjerrum["Su_corrected_kpa"],
            "formula": "Su_eff = Su / μ",
            "note": bjerrum["note"],
            "reference": "Bjerrum & Eide (1956); CIRIA C760; Terzaghi et al. (1996)"
        },
        {
            "step": "4. Tính ứng suất tại đáy hố",
            "formula": "σ_v,base = γ_avg × H + q",
            "inputs": sigma_calc_steps,
            "result": f"σ_v,base = {sigma_v_base_with_q:.2f} kPa"
        },
        {
            "step": "5. Tính hệ số an toàn Fs",
            "formula": "Fs = (Nc × Su_eff) / σ_v,base",
            "inputs": fs_calc_steps,
            "result": f"Fs = {Fs:.3f}"
        },
        {
            "step": "6. Đánh giá kết quả",
            "Fs": round(Fs, 3),
            "Fs_allow": Fs_allow,
            "eta": round(eta, 3),
            "status": status,
            "status_note": status_note,
            "eta_status": eta_status
        }
    ]

    return {
        "excavation_data": {
            "B_m": B,
            "L_m": L,
            "H_exc_m": H,
            "D_pile_m": D_pile,
            "Su_kpa": Su,
            "q_kpa": q
        },
        "Nc": Nc,
        "Bjerrum_Eide": {
            "H_over_B": bjerrum["H_over_B"],
            "D_over_B": bjerrum["D_over_B"],
            "mu": bjerrum["mu"],
            "Su_corrected_kpa": bjerrum["Su_corrected_kpa"]
        },
        "gamma_avg_kNm3": gamma_avg,
        "layer_contributions": layer_contribs,
        "sigma_v_base_kpa": round(sigma_v_base_with_q, 2),
        "Fs": round(Fs, 3),
        "Fs_allow": Fs_allow,
        "eta": round(eta, 3),
        "status": status,
        "status_note": status_note,
        "eta_status": eta_status,
        "recommendations": recommendations,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "Terzaghi (1943); Bjerrum-Eide (1956); CIRIA C760; v2.3.2",
        "Config_Constants": {
            "gamma_w": f"{gw} kN/m³",
            "fs_allow": f"{Fs_allow_cfg}",
            "q_surcharge_default": f"{DEFAULT_Q_SURCHARGE} kN/m²"
        },
        "Scope_Limitation": [
            "Terzaghi 2D — chưa xét hiệu ứng 3D và lực ma sát thành vách (dùng Plaxis xác nhận)",
            "Bjerrum-Eide: phạm vi H/B 0.5–4.0; ngoài phạm vi → extrapolate với H/B=4.0",
            "Chưa xét ảnh hưởng của neo và hệ giằng ngang"
        ]
    }


def calc_piping_check(layers, gwl_depth, D_pile_m, B_m, gamma_w=None):
    """
    Kiểm tra nguy cơ cát chảy (Piping / Boiling) tại chân cừ.

    Công thức: Fs_piping = (D_pile × γ') / (0.8 × B × i_cr)

    Fix v2.3.1: gamma_w có thể override.
    """
    gw = gamma_w if gamma_w is not None else DEFAULT_GAMMA_W
    # Tìm lớp cát dưới đáy hố
    sorted_layers = sorted(layers, key=lambda l: l["top_depth"], reverse=True)
    sand_layer = None
    for layer in sorted_layers:
        if layer["bottom_depth"] < D_pile_m and any(
            k in layer.get("description", "").lower()
            for k in ["cát", "sand", "sỏi", "gravel"]
        ):
            sand_layer = layer
            break

    if sand_layer is None:
        return {
            "piping_check": None,
            "note": "Không tìm thấy lớp cát dưới đáy hố — không cần kiểm tra piping"
        }

    gamma_sat = sand_layer.get("gamma_sat", 19.0)
    gamma_sub = max(gamma_sat - gw, 9.0)  # v2.3.1: dùng gw thay vì GAMMA_W

    # Gradien thủy lực xấp xỉ = 1 (phổ biến cho cát hạt mịn)
    i_avg = 1.0

    # Tính gradien thực tế tại chân cừ (xấp xỉ)
    # i = (h_w) / L_path, trong đó L_path ≈ 0.8 × B + D_pile
    L_path = 0.8 * B_m + D_pile_m
    i_actual = (gamma_w * D_pile_m) / (gamma_sub * L_path) if L_path > 0 else 0.0

    Fs_piping = (D_pile_m * gamma_sub) / (0.8 * B_m) if B_m > 0 else 999.0
    Fs_piping_allow = DEFAULT_PIPING_ALLOW  # v2.3.1: configurable

    if Fs_piping >= Fs_piping_allow:
        piping_status = "ĐẠT"
        piping_note = f"Fs_piping = {Fs_piping:.2f} ≥ 1.50 — Không có nguy cơ cát chảy"
    else:
        piping_status = "CẢNH BÁO"
        piping_note = f"Fs_piping = {Fs_piping:.2f} < 1.50 — Nguy cơ cát chảy. Cần tăng D_pile hoặc hạ mực nước ngầm."

    return {
        "piping_check": {
            "D_pile_m": D_pile_m,
            "B_m": B_m,
            "gamma_sub_kNm3": round(gamma_sub, 2),
            "L_path_m": round(L_path, 2),
            "i_actual": round(i_actual, 3),
            "Fs_piping": round(Fs_piping, 2),
            "Fs_piping_allow": Fs_piping_allow,
            "status": piping_status,
            "note": piping_note
        },
        "note": f"Kiểm tra piping cho lớp {sand_layer.get('id', '?')}"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE MỚI: Kiểm tra Ổn định Đáy Hố Đào (Base Heave)"
    )
    parser.add_argument("--input", required=True, help="Path to JSON input file")
    parser.add_argument("--output", help="Path to output JSON file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = calc_base_heave(
        excavation_data=data["excavation"],
        layers=data["layers"]
    )

    # Bổ sung piping check nếu có D_pile và B
    if data["excavation"].get("D_pile_m") and data["excavation"].get("B_m"):
        piping = calc_piping_check(
            layers=data["layers"],
            gwl_depth=data.get("gwl_depth", -2.0),
            D_pile_m=data["excavation"]["D_pile_m"],
            B_m=data["excavation"]["B_m"]
        )
        result["piping_check"] = piping.get("piping_check")
        result["piping_note"] = piping.get("note", "")

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
