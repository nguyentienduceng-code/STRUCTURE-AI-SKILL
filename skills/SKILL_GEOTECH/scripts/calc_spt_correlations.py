import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_spt_correlations.py — MODULE 5: Tương quan SPT → thông số cơ lý đất
# =============================================================================
# Version: 2.3.0
# Standard_Method: Bowles (1997) + Jamiolkowski/Stroud/CIRIA C760 + Database TP.HCM
# Reference: Tinh toan CU LARSEN.xls Sheet 'Tinh E',
#            HLH-PKT Sheet 'Table LAB TEST',
#            QUY TRÌNH TÍNH PLAXIS.docx
# Hỗ trợ: TCVN 9351:2012 + BS/ASTM (tùy dự án)
# Tích hợp: Ground Truth Verification + Ke × Su correlation
# =============================================================================

import verify_against_ground_truth as vgt

# ── Bảng tương quan SPT kinh nghiệm từ 15+ dự án TP.HCM ──
SPT_CORRELATION_DB = {
    # ── ĐẤT DÍNH (CLAY / SILT) ──
    "clay_very_soft": {
        "spt_range": [0, 2],
        "description": "Bùn sét, sét hữu cơ, rất mềm",
        "drainage": "Undrained",
        "gamma_unsat": [14.0, 15.5],
        "gamma_sat": [15.0, 16.0],
        "e": [1.5, 2.5],
        "c_kpa": [5, 10],
        "phi_deg": [3, 5],
        "E50_kpa": [3500, 5000],
        "k_m_per_day": [0.0001, 0.001],
        "nu": 0.35,
        "Rinter_dw": [0.6, 0.7],
        "Rinter_sp": [0.5, 0.6],
        "m_hs": [0.8, 0.9],
        "Ke_range": [300, 500],      # Ke = E50/Su cho sét mềm
        "Ip_range": [15, 40],
        "projects": ["Fosco Q1", "Lexington Q2"]
    },
    "clay_soft": {
        "spt_range": [2, 5],
        "description": "Sét pha, dẻo mềm - dẻo chảy",
        "drainage": "Undrained",
        "gamma_unsat": [16.0, 18.0],
        "gamma_sat": [17.0, 18.5],
        "e": [0.9, 1.5],
        "c_kpa": [10, 20],
        "phi_deg": [8, 12],
        "E50_kpa": [8000, 12000],
        "k_m_per_day": [0.0001, 0.01],
        "nu": 0.35,
        "Rinter_dw": [0.7, 0.75],
        "Rinter_sp": [0.55, 0.65],
        "m_hs": [0.7, 0.8],
        "Ke_range": [400, 600],
        "Ip_range": [12, 30],
        "projects": ["Lexington Q2", "VP Long Biên"]
    },
    "clay_medium": {
        "spt_range": [5, 15],
        "description": "Sét pha, dẻo cứng - nửa cứng",
        "drainage": "Undrained",
        "gamma_unsat": [18.0, 20.0],
        "gamma_sat": [19.0, 20.5],
        "e": [0.6, 0.9],
        "c_kpa": [15, 35],
        "phi_deg": [12, 18],
        "E50_kpa": [10000, 25000],
        "k_m_per_day": [0.001, 0.05],
        "nu": 0.35,
        "Rinter_dw": [0.75, 0.8],
        "Rinter_sp": [0.6, 0.7],
        "m_hs": [0.65, 0.75],
        "Ke_range": [500, 800],
        "Ip_range": [10, 25],
        "projects": ["C.T Plaza Q3", "Chùa Pháp Vân Tân Phú", "Báo SG-GP Q3"]
    },
    "clay_stiff": {
        "spt_range": [15, 30],
        "description": "Sét cứng - rất cứng, sét pha laterit",
        "drainage": "Undrained",
        "gamma_unsat": [19.0, 20.5],
        "gamma_sat": [20.0, 21.0],
        "e": [0.5, 0.75],
        "c_kpa": [25, 85],
        "phi_deg": [15, 17],
        "E50_kpa": [20000, 35000],
        "k_m_per_day": [0.001, 0.05],
        "nu": 0.35,
        "Rinter_dw": [0.8, 0.85],
        "Rinter_sp": [0.65, 0.75],
        "m_hs": [0.7, 0.8],
        "Ke_range": [600, 1000],
        "Ip_range": [8, 20],
        "projects": ["Sói Kình Lâm Q5", "Chùa Pháp Vân Tân Phú"]
    },
    # ── ĐẤT RỜI (SAND / GRAVEL) ──
    "sand_loose": {
        "spt_range": [4, 10],
        "description": "Cát mịn đến trung, rời - kém chặt",
        "drainage": "Drained",
        "gamma_unsat": [17.5, 19.0],
        "gamma_sat": [18.5, 19.5],
        "e": [0.65, 0.85],
        "c_kpa": [3, 8],
        "phi_deg": [20, 25],
        "E50_kpa": [12000, 20000],
        "k_m_per_day": [1.0, 5.0],
        "nu": 0.30,
        "Rinter_dw": [0.75, 0.8],
        "Rinter_sp": [0.65, 0.7],
        "m_hs": [0.55, 0.65],
        "alpha_range": [1500, 2000],   # alpha = E50/N_SPT cho cát rời
        "projects": ["Fosco Q1", "Báo SG-GP Q3"]
    },
    "sand_medium": {
        "spt_range": [10, 30],
        "description": "Cát pha, cát bụi, chặt vừa",
        "drainage": "Drained",
        "gamma_unsat": [19.0, 20.5],
        "gamma_sat": [20.0, 21.0],
        "e": [0.5, 0.7],
        "c_kpa": [4, 15],
        "phi_deg": [22, 30],
        "E50_kpa": [18000, 33000],
        "k_m_per_day": [1.0, 6.0],
        "nu": 0.30,
        "Rinter_dw": [0.8, 0.85],
        "Rinter_sp": [0.7, 0.8],
        "m_hs": [0.5, 0.6],
        "alpha_range": [2000, 2700],
        "projects": ["Chùa Pháp Vân Tân Phú", "Fusion Suite Đà Nẵng", "Lexington Q2"]
    },
    "sand_dense": {
        "spt_range": [30, 50],
        "description": "Cát chặt - rất chặt",
        "drainage": "Drained",
        "gamma_unsat": [19.5, 21.0],
        "gamma_sat": [20.5, 21.5],
        "e": [0.45, 0.65],
        "c_kpa": [5, 20],
        "phi_deg": [28, 35],
        "E50_kpa": [30000, 45000],
        "k_m_per_day": [1.0, 10.0],
        "nu": 0.30,
        "Rinter_dw": [0.85, 0.9],
        "Rinter_sp": [0.75, 0.85],
        "m_hs": [0.5, 0.55],
        "alpha_range": [2500, 3000],
        "projects": ["Chùa Pháp Vân Tân Phú"]
    },
    # ── ĐẤT SAN LẤP ──
    "fill": {
        "spt_range": [5, 15],
        "description": "Đất san lấp (cát, sỏi sạn, phế thải XD)",
        "drainage": "Drained",
        "gamma_unsat": [17.0, 19.5],
        "gamma_sat": [18.0, 20.0],
        "e": [0.65, 0.75],
        "c_kpa": [4, 6],
        "phi_deg": [25, 30],
        "E50_kpa": [15000, 22000],
        "k_m_per_day": [2.0, 10.0],
        "nu": 0.30,
        "Rinter_dw": [0.7, 0.8],
        "Rinter_sp": [0.6, 0.7],
        "m_hs": [0.55, 0.65],
        "alpha_range": [2000, 2500],
        "projects": ["Fosco Q1", "VP Long Biên"]
    }
}


# ── BẢNG HỆ SỐ Ke = E50/Su THEO Ip (CIRIA C760 / Jamiolkowski / Stroud) ──
# Nguồn: Jamiolkowski et al. (1979), Stroud (1974), CIRIA C760 (Table 5.3)
# Áp dụng: Đất dính, Su xác định từ UU test hoặc cắt cánh hiện trường
Ke_TABLE = {
    # Ip (%)     : [Ke_min, Ke_max, Ke_recommended]
    "very_low":    [300, 500, 400],   # Ip < 15%: Sét mềm, bùn
    "low":         [400, 600, 500],   # Ip 15-25%: Sét dẻo mềm
    "medium":      [500, 700, 600],   # Ip 25-40%: Sét trung bình
    "high":        [600, 900, 710],   # Ip 40-60%: Sét nửa cứng
    "very_high":   [800, 1200, 1000], # Ip > 60%: Sét cứng - rất cứng
}

# ── BẢNG HỆ SỐ α = E50/N_SPT THEO LOẠI ĐẤT RỜI (Bowles 1997 + CIRIA C760) ──
ALPHA_TABLE = {
    # Loại cát                          : [alpha_min, alpha_max, alpha_recommended]
    "sand_fine_loose":       [1500, 2000, 1500],  # Cát mịn, rời
    "sand_medium":            [2000, 2700, 2000],  # Cát trung, chặt vừa
    "sand_coarse_dense":     [2500, 3000, 2500],  # Cát thô, chặt
    "sand_gravel_dense":     [3000, 4000, 3000],  # Cát sỏi, rất chặt
}


def select_Ke(Ip_pct=None, soil_class=None):
    """
    Chọn hệ số Ke = E50/Su dựa trên Ip hoặc loại đất dính.

    Nguồn: CIRIA C760, Jamiolkowski et al. (1979), Stroud (1974)

    Parameters
    ----------
    Ip_pct : float or None
        Chỉ số dẻo Ip (%)
    soil_class : str or None
        Key trong SPT_CORRELATION_DB (nếu có)

    Returns
    -------
    dict {min, max, recommended}
    """
    if Ip_pct is not None:
        if Ip_pct < 15:
            cat = "very_low"
        elif Ip_pct < 25:
            cat = "low"
        elif Ip_pct < 40:
            cat = "medium"
        elif Ip_pct < 60:
            cat = "high"
        else:
            cat = "very_high"
        return {
            "min": Ke_TABLE[cat][0],
            "max": Ke_TABLE[cat][1],
            "recommended": Ke_TABLE[cat][2],
            "category": cat,
            "Ip_pct": Ip_pct
        }

    # Fallback: dựa vào soil_class
    if soil_class in SPT_CORRELATION_DB:
        Ke_range = SPT_CORRELATION_DB[soil_class].get("Ke_range", [400, 700])
        return {
            "min": Ke_range[0],
            "max": Ke_range[1],
            "recommended": (Ke_range[0] + Ke_range[1]) / 2,
            "category": "from_soil_class",
            "soil_class": soil_class
        }

    return {"min": 400, "max": 700, "recommended": 500}


def select_alpha(soil_class=None, description=None):
    """
    Chọn hệ số α = E50/N_SPT dựa trên loại đất rời.

    Nguồn: Bowles (1997), Webb (1969), CIRIA C760

    Parameters
    ----------
    soil_class : str or None
        Key trong SPT_CORRELATION_DB
    description : str or None
        Mô tả lớp đất (để phân biệt cát mịn/thô)

    Returns
    -------
    dict {min, max, recommended}
    """
    # Ưu tiên từ mô tả
    if description:
        d = description.lower()
        if any(k in d for k in ["thô", "sỏi", "gravel", "coarse"]):
            cat = "sand_coarse_dense"
        elif any(k in d for k in ["chặt", "dense", "very"]):
            cat = "sand_coarse_dense"
        elif any(k in d for k in ["mịn", "fine", "bụi", "silt"]):
            cat = "sand_fine_loose"
        elif any(k in d for k in ["trung", "medium", "pha"]):
            cat = "sand_medium"
        else:
            cat = "sand_medium"
        return {
            "min": ALPHA_TABLE[cat][0],
            "max": ALPHA_TABLE[cat][1],
            "recommended": ALPHA_TABLE[cat][2],
            "category": cat
        }

    # Fallback: từ soil_class
    if soil_class in SPT_CORRELATION_DB:
        alpha_range = SPT_CORRELATION_DB[soil_class].get("alpha_range", [2000, 2700])
        return {
            "min": alpha_range[0],
            "max": alpha_range[1],
            "recommended": (alpha_range[0] + alpha_range[1]) / 2,
            "category": "from_soil_class",
            "soil_class": soil_class
        }

    return {"min": 2000, "max": 2700, "recommended": 2000}


def classify_soil(spt_value, soil_description="", is_cohesive=None):
    """
    Phân loại đất dựa vào SPT và mô tả.
    Returns key in SPT_CORRELATION_DB.
    """
    desc_lower = soil_description.lower() if soil_description else ""

    cohesive_keywords = ["sét", "bùn", "clay", "silt", "hữu cơ", "organic", "dẻo", "mềm", "cứng"]
    granular_keywords = ["cát", "sand", "sỏi", "gravel", "sạn", "chặt"]
    fill_keywords = ["san lấp", "fill", "đắp", "phế thải"]

    if is_cohesive is None:
        is_cohesive = any(k in desc_lower for k in cohesive_keywords)
        is_granular = any(k in desc_lower for k in granular_keywords)
        is_fill = any(k in desc_lower for k in fill_keywords)
    else:
        is_granular = not is_cohesive
        is_fill = False

    if is_fill or any(k in desc_lower for k in fill_keywords):
        return "fill"

    if is_cohesive:
        if spt_value <= 2:
            return "clay_very_soft"
        elif spt_value <= 5:
            return "clay_soft"
        elif spt_value <= 15:
            return "clay_medium"
        else:
            return "clay_stiff"
    else:
        if spt_value < 10:
            return "sand_loose"
        elif spt_value < 30:
            return "sand_medium"
        else:
            return "sand_dense"


def _interp(db_entry, spt_value, key):
    """Nội suy tuyến tính trong khoảng SPT của lớp đất."""
    spt_min, spt_max = db_entry["spt_range"]
    if spt_max == spt_min:
        ratio = 0.5
    else:
        ratio = min(1.0, max(0.0, (spt_value - spt_min) / (spt_max - spt_min)))
    range_list = db_entry.get(key)
    if isinstance(range_list, list) and len(range_list) == 2:
        return round(range_list[0] + ratio * (range_list[1] - range_list[0]), 2)
    return range_list


def correlate_spt(spt_value, soil_class=None, soil_description="",
                  is_cohesive=None, wall_type="dw",
                  Su_kpa=None, Ip_pct=None):
    """
    Tương quan SPT → thông số cơ lý đất (v2.3.0).

    CÔNG THỨC CHÍNH:
    ─ ĐẤT DÍNH:  E50 = Ke × Su
      (Nguồn: Jamiolkowski 1979, Stroud 1974, CIRIA C760)
    ─ ĐẤT RỜI:   E50 = α × N_SPT
      (Nguồn: Bowles 1997, Webb 1969, CIRIA C760)

    Parameters
    ----------
    spt_value : float
        Giá trị SPT trung bình
    soil_class : str or None
        Key trong SPT_CORRELATION_DB (nếu biết trước)
    soil_description : str
        Mô tả loại đất tiếng Việt
    is_cohesive : bool or None
        True = đất dính, False = đất rời
    wall_type : str
        'dw' = tường vây, 'sp' = cừ Larsen
    Su_kpa : float or None
        Sức kháng cắt không thoát nước (kPa)
        Nếu có → dùng công thức E50 = Ke × Su
    Ip_pct : float or None
        Chỉ số dẻo Ip (%) để chọn Ke chính xác hơn

    Returns
    -------
    dict with soil parameters and Calculation_Logs
    """
    if soil_class is None:
        soil_class = classify_soil(spt_value, soil_description, is_cohesive)

    db_entry = SPT_CORRELATION_DB.get(soil_class)
    if db_entry is None:
        return {"error": f"Unknown soil class: {soil_class}"}

    is_clay = db_entry["drainage"] == "Undrained"
    calc_logs = []

    # ── BƯỚC 1: Tính E50ref ──────────────────────────────────────────────────
    if is_clay:
        # ĐẤT DÍNH: E50 = Ke × Su
        Ke_data = select_Ke(Ip_pct=Ip_pct, soil_class=soil_class)
        Ke = Ke_data["recommended"]

        if Su_kpa is not None and Su_kpa > 0:
            E50_formula = f"E50 = Ke × Su = {Ke} × {Su_kpa}"
            E50_calc = Ke * Su_kpa
            E50_source = "Ke × Su (Lab/Field Test)"
            Ke_note = f"Ke={Ke} từ bảng Ke theo Ip={Ip_pct or 'db'}%"
        else:
            # Fallback: ước lượng Su từ SPT (Terzaghi & Peck)
            Su_estimate = spt_value * 4.5  # kPa (ước lượng sơ bộ)
            E50_formula = f"E50 ≈ Ke × (N×4.5) = {Ke} × ({spt_value}×4.5)"
            E50_calc = Ke * Su_estimate
            E50_source = "Ke × Su (ước lượng từ SPT — cần Lab Test để xác nhận)"
            Ke_note = f"Ke={Ke}; Su ước tính = {Su_estimate:.1f} kPa"

        E50 = round(E50_calc, -3)  # Làm tròn đến 1000 gần nhất
        E50_note = f"{E50_source} | {Ke_note}"

        calc_logs.append({
            "step": "Tính E50ref — ĐẤT DÍNH",
            "formula": "E50 = Ke × Su",
            "source": "Jamiolkowski et al. (1979); Stroud (1974); CIRIA C760",
            "Su_kpa": Su_kpa,
            "Ke_data": Ke_data,
            "Ke_selected": Ke,
            "E50_calc": round(E50_calc, 1),
            "E50_final": E50,
            "note": E50_note
        })
    else:
        # ĐẤT RỜI: E50 = α × N_SPT
        alpha_data = select_alpha(soil_class=soil_class, description=soil_description)
        alpha = alpha_data["recommended"]

        E50_formula = f"E50 = α × N_SPT = {alpha} × {spt_value}"
        E50_calc = alpha * spt_value
        E50 = round(E50_calc, -3)
        E50_source = f"α × N_SPT = {alpha} × {spt_value}"

        # Cross-check với database
        E50_db = _interp(db_entry, spt_value, "E50_kpa")
        E50_check = (E50_calc + E50_db) / 2  # Trung bình giữa công thức và DB
        if abs(E50_check - E50) > E50 * 0.15:
            E50 = round(E50_check, -3)  # Điều chỉnh nếu lệch > 15%

        calc_logs.append({
            "step": "Tính E50ref — ĐẤT RỜI",
            "formula": f"E50 = α × N_SPT = {alpha} × {spt_value}",
            "source": "Bowles (1997); Webb (1969); CIRIA C760",
            "alpha_data": alpha_data,
            "alpha_selected": alpha,
            "E50_calc": E50_calc,
            "E50_db_check": E50_db,
            "E50_final": E50,
            "note": "Lấy trung bình công thức và DB nếu lệch < 15%"
        })

    # ── BƯỚC 2: Tính Eoedref và Eurref ─────────────────────────────────────
    Eoed = E50  # ≈ E50ref (Plaxis Manual)
    Eur = round(3 * E50, -3)

    calc_logs.append({
        "step": "Tính Eoedref và Eurref",
        "Eoedref": f"≈ E50ref = {Eoed}",
        "Eurref": f"= 3 × E50ref = {Eur}",
        "reference": "Plaxis Material Models Manual (Brinkgreve et al.)"
    })

    # ── BƯỚC 3: Tra bảng m, Rinter, k ──────────────────────────────────────
    Rinter_key = f"Rinter_{wall_type}"
    Rinter = _interp(db_entry, spt_value,
                      Rinter_key if Rinter_key in db_entry else "Rinter_dw")
    m_val = _interp(db_entry, spt_value, "m_hs")
    k_val = _interp(db_entry, spt_value, "k_m_per_day")

    calc_logs.append({
        "step": "Tra bảng thông số phụ",
        "m": m_val,
        "Rinter": Rinter,
        "k_m_day": k_val,
        "wall_type": wall_type,
        "source": "Database TP.HCM (15+ dự án)"
    })

    # ── GROUND TRUTH VERIFICATION ──────────────────────────────────────────────
    gt_check = None
    try:
        gt_check = vgt.verify_parameters(
            {"E50_ref_kpa": E50, "c_kpa": _interp(db_entry, spt_value, "c_kpa"),
             "phi_deg": _interp(db_entry, spt_value, "phi_deg")},
            spt_value, is_cohesive
        )
    except Exception:
        pass

    result = {
        "soil_class": soil_class,
        "description": db_entry["description"],
        "drainage_type": db_entry["drainage"],
        "is_cohesive": is_clay,
        "gamma_unsat": _interp(db_entry, spt_value, "gamma_unsat"),
        "gamma_sat": _interp(db_entry, spt_value, "gamma_sat"),
        "void_ratio_e": _interp(db_entry, spt_value, "e"),
        "c_kpa": _interp(db_entry, spt_value, "c_kpa"),
        "phi_deg": _interp(db_entry, spt_value, "phi_deg"),
        "E50_ref_kpa": E50,
        "Eoed_ref_kpa": Eoed,
        "Eur_ref_kpa": Eur,
        "m": m_val,
        "pref_kpa": 100.0,
        "nu_ur": 0.2,
        "nu_mc": db_entry["nu"],
        "psi_deg": 0.0,
        "k_m_per_day": k_val,
        "Rinter": Rinter,
        "Ke_data": select_Ke(Ip_pct=Ip_pct, soil_class=soil_class) if is_clay else None,
        "Alpha_data": select_alpha(soil_class=soil_class, description=soil_description) if not is_clay else None,
        "reference_projects": db_entry.get("projects", []),
        "spt_input": spt_value,
        "Su_kpa_provided": Su_kpa,
        "Ip_pct_provided": Ip_pct,
        "Calculation_Logs": calc_logs,
        "Ground_Truth_Check": gt_check,
        "Standard_Method": "Bowles (1997) + Jamiolkowski/Stroud + Database TP.HCM",
        "Scope_Limitation": [
            "Ke phụ thuộc Ip — nên cung cấp Ip_pct và Su_kpa từ Lab Test",
            "α cho đất rời: nên hiệu chỉnh theo kết quả nén 3 trục nếu có",
            "E50 cho đất dính: ước lượng từ SPT nếu không có Su"
        ]
    }

    return result


def process_borehole(layers_data, wall_type="dw"):
    """
    Xử lý toàn bộ hố khoan — tương quan SPT cho từng lớp.
    """
    results = []
    for layer in layers_data:
        r = correlate_spt(
            spt_value=layer["spt_avg"],
            soil_description=layer.get("description", ""),
            is_cohesive=layer.get("is_cohesive"),
            wall_type=wall_type,
            Su_kpa=layer.get("Su_kpa"),
            Ip_pct=layer.get("Ip_pct")
        )
        r["layer_id"] = layer["id"]
        r["layer_name"] = layer["name"]
        r["top_depth"] = layer.get("top_depth")
        r["bottom_depth"] = layer.get("bottom_depth")
        results.append(r)

    return {
        "layers": results,
        "Standard_Method": "Bowles (1997) + Jamiolkowski/Stroud + Database TP.HCM",
        "wall_type": wall_type
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 5 v2.3: Tương quan SPT → thông số cơ lý đất"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Path to JSON input file (multi-layer)")
    group.add_argument("--spt", type=float, help="Single SPT value")

    parser.add_argument("--soil-type", default="", help="Soil description")
    parser.add_argument("--cohesive", type=bool, default=None, help="Is cohesive soil?")
    parser.add_argument("--wall", default="dw", choices=["dw", "sp"],
                        help="Wall type: dw=Diaphragm Wall, sp=Sheet Pile")
    parser.add_argument("--Su", type=float, default=None, help="Su (kPa) — cho đất dính")
    parser.add_argument("--Ip", type=float, default=None, help="Ip (%) — cho đất dính")
    parser.add_argument("--output", help="Path to output JSON file")
    args = parser.parse_args()

    if args.spt is not None:
        result = correlate_spt(
            spt_value=args.spt,
            soil_description=args.soil_type,
            is_cohesive=args.cohesive,
            wall_type=args.wall,
            Su_kpa=args.Su,
            Ip_pct=args.Ip
        )
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = process_borehole(data["layers"], wall_type=args.wall)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
