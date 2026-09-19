import sys
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_soil_params_hs.py — MODULE 3: Thông số Hardening Soil cho Plaxis
# =============================================================================
# Version: 2.3.1
# Standard_Method: Hardening Soil Model + CIRIA C760 (Rinter) + Ke/α v2.3
# Fixes v2.3.1:
#   - Sửa formula trong calc_logs: 450×Su → Ke×Su (đất dính)
#   - Sửa Rinter mặc định cho DW: 1.0 → 0.67 (CIRIA C760)
#   - Tích hợp Ke/α v2.3 vào calc_logs
# Reference: HLH-PKT Sheet 'Ket qua tinh' + 'Table LAB TEST',
#            QUY TRÌNH TÍNH PLAXIS.docx Bước 1-7
# =============================================================================

from calc_spt_correlations import correlate_spt, select_Ke, select_alpha


# ── Bảng Rinter mặc định theo CIRIA C760 (v2.3.1 FIX) ──
# Nguồn: CIRIA C760 (Table 6.2), Plaxis Material Models Manual
DEFAULT_RINTER = {
    "dw": {
        "sandy": 0.67,       # Tường vây BTCT trong cát — CIRIA C760
        "silty": 0.70,       # Tường vây BTCT trong silt
        "clay_stiff": 0.70,   # Tường vây BTCT trong sét cứng
        "clay_soft": 0.60,    # Tường vây BTCT trong sét mềm
        "default": 0.67
    },
    "sp": {
        "sandy": 0.67,       # Cừ Larsen trong cát
        "silty": 0.60,       # Cừ Larsen trong silt
        "clay": 0.55,        # Cừ Larsen trong sét
        "default": 0.67
    },
    "secant": {
        "default": 0.80     # Cọc Secant
    }
}


def _get_rinter(wall_type, soil_description):
    """
    Xác định Rinter theo CIRIA C760.
    Fix v2.3.1: Không còn dùng 1.0 cho DW nữa.
    """
    n = (soil_description or "").lower()

    # Xác định loại đất
    if any(k in n for k in ["cát", "sand", "cat"]):
        soil_key = "sandy"
    elif any(k in n for k in ["sét", "clay", "bùn"]):
        if any(k in n for k in ["mềm", "soft", "dẻo"]):
            soil_key = "clay_soft"
        else:
            soil_key = "clay_stiff"
    elif any(k in n for k in ["silt", "bụi", "pha"]):
        soil_key = "silty"
    else:
        soil_key = "default"

    rinter_db = DEFAULT_RINTER.get(wall_type, DEFAULT_RINTER["dw"])
    return rinter_db.get(soil_key, rinter_db["default"])


def build_hs_params(layer_data, wall_type="dw"):
    """
    Xây dựng bộ thông số Hardening Soil cho 1 lớp đất (v2.3.1).

    Fixes v2.3.1:
      - Rinter mặc định: dw → 0.67 (CIRIA C760), không còn 1.0
      - Formula trong calc_logs: dùng Ke×Su / α×N
      - Ke/α được trích xuất từ MODULE 5 và ghi rõ trong logs

    Parameters
    ----------
    layer_data : dict
        Thông số lớp đất. Ưu tiên (nếu có từ Lab Test):
        - E50_ref_kpa: Module cát tuyến tham chiếu
        - Eoed_ref_kpa: Module tiếp tuyến từ Oedometer
        - Eur_ref_kpa: Module dỡ tải-gia tải lại
        - m: Hệ số mũ phụ thuộc ứng suất
        - pref_kpa: Áp lực tham chiếu
        - c_kpa, phi_deg, psi_deg: Thông số cường độ
        - nu_ur: Poisson unloading-reloading
        Nếu thiếu → dùng SPT correlation tự động (MODULE 5).
    wall_type : str
        'dw' (Diaphragm Wall), 'sp' (Sheet Pile), 'secant'

    Returns
    -------
    dict: HS parameters ready for Plaxis
    """
    spt = layer_data.get("spt_avg")
    desc = layer_data.get("description", "")
    is_cohesive_override = layer_data.get("is_cohesive")

    # ── Lấy correlation data từ MODULE 5 ──
    corr = {}
    if spt is not None:
        corr = correlate_spt(
            spt,
            soil_description=desc,
            is_cohesive=is_cohesive_override,
            wall_type=wall_type,
            Su_kpa=layer_data.get("Su_kpa"),
            Ip_pct=layer_data.get("Ip_pct")
        )

    def get_val(key, corr_key=None):
        v = layer_data.get(key)
        if v is not None:
            return v
        return corr.get(corr_key or key)

    drainage = get_val("drainage_type")
    if drainage is None:
        drainage = corr.get("drainage_type", "Drained")

    is_clay = (drainage == "Undrained")

    gamma_unsat = get_val("gamma_unsat")
    gamma_sat = get_val("gamma_sat")

    # ── E50, Eoed, Eur — v2.3.1: Lấy từ MODULE 5 ──
    E50 = get_val("E50_ref_kpa")
    Eoed = get_val("Eoed_ref_kpa")
    Eur = get_val("Eur_ref_kpa")

    # Lấy Ke/α data từ MODULE 5 để ghi vào calc_logs
    if is_clay:
        Ke_data = corr.get("Ke_data") or select_Ke(
            Ip_pct=layer_data.get("Ip_pct"),
            soil_class=corr.get("soil_class")
        )
        Ke = Ke_data.get("recommended", "?")
        formula_label = f"Ke × Su"
        formula_note = (
            f"Ke={Ke} (Ip={layer_data.get('Ip_pct', 'db')}% → "
            f"CIRIA C760 / Jamiolkowski)"
        )
    else:
        Alpha_data = corr.get("Alpha_data") or select_alpha(
            soil_class=corr.get("soil_class"),
            description=desc
        )
        alpha = Alpha_data.get("recommended", "?")
        formula_label = f"α × N_SPT"
        formula_note = f"α={alpha} (Bowles 1997 / CIRIA C760)"

    e50_source = "User input (Lab Test)" if layer_data.get("E50_ref_kpa") else "MODULE 5: SPT correlation"

    # Default relationships v2.3.1
    if E50 is not None:
        if Eoed is None:
            Eoed = E50  # ≈ E50ref (Plaxis Manual)
        if Eur is None:
            Eur = 3 * E50

    # ── Cường độ ──
    c = get_val("c_kpa")
    phi = get_val("phi_deg")
    psi = get_val("psi_deg") or 0.0

    # ── Các hệ số khác ──
    m = get_val("m", "m")
    pref = get_val("pref_kpa") or 100.0

    nu_ur = get_val("nu_ur")
    if nu_ur is None:
        if is_clay and E50 is not None and E50 < 10000:
            nu_ur = 0.15
        else:
            nu_ur = 0.2

    k = get_val("k_m_per_day")

    # ── Rinter v2.3.1: Dùng CIRIA C760 thay vì hardcode 1.0 ──
    Rinter = get_val("Rinter")
    if Rinter is None:
        Rinter = _get_rinter(wall_type, desc)

    missing = []
    if gamma_unsat is None: missing.append("gamma_unsat")
    if E50 is None: missing.append("E50_ref_kpa")
    if c is None: missing.append("c_kpa")
    if phi is None: missing.append("phi_deg")
    if m is None: missing.append("m")

    # ── Calculation Logs v2.3.1: Đầy đủ Ke/α formula ──
    calc_logs = [
        {
            "step": "Bước 1: Dung trọng γ",
            "gamma_unsat": gamma_unsat,
            "gamma_sat": gamma_sat,
            "source": "Lab Test" if layer_data.get("gamma_sat") else "SPT correlation"
        },
        {
            "step": "Bước 2: Module E50ref (v2.3.1)",
            "formula_label": formula_label,
            "formula_detail": formula_note,
            "E50_ref_kpa": E50,
            "spt_input": spt,
            "Su_kpa_provided": layer_data.get("Su_kpa"),
            "Ip_pct_provided": layer_data.get("Ip_pct"),
            "source": e50_source
        },
        {
            "step": "Bước 3: Eoedref và Eurref",
            "Eoed_ref_kpa": Eoed,
            "Eur_ref_kpa": Eur,
            "relationship": "Eoed ≈ E50ref; Eur = 3 × E50ref",
            "reference": "Plaxis Material Models Manual"
        },
        {
            "step": "Bước 4: Hệ số mũ m",
            "m": m,
            "source": "Bảng tra theo loại đất (SKILL_SOIL_PARAMS.md Bước 4)"
        },
        {
            "step": "Bước 5: Hệ số Rinter (v2.3.1 FIX)",
            "Rinter": Rinter,
            "wall_type": wall_type,
            "soil_description": desc[:50],
            "note": "Theo CIRIA C760 — Không còn dùng Rinter=1.0 cho DW nữa",
            "reference": "CIRIA C760 Table 6.2"
        },
        {
            "step": "Bước 6: Poisson ν_ur",
            "nu_ur": nu_ur,
            "note": "Mặc định 0.2 cho mô hình HS"
        },
        {
            "step": "Bước 7: Hệ số thấm kx, ky",
            "k_m_per_day": k,
            "unit": "m/ngày"
        }
    ]

    result = {
        "layer_id": layer_data.get("id"),
        "layer_name": layer_data.get("name", ""),
        "description": desc,
        "model": "Hardening Soil",
        "drainage_type": drainage,
        "gamma_unsat_kn_m3": gamma_unsat,
        "gamma_sat_kn_m3": gamma_sat,
        "E50_ref_kpa": E50,
        "Eoed_ref_kpa": Eoed,
        "Eur_ref_kpa": Eur,
        "m": m,
        "pref_kpa": pref,
        "nu_ur": nu_ur,
        "c_kpa": c,
        "phi_deg": phi,
        "psi_deg": psi,
        "k_x_m_per_day": k,
        "k_y_m_per_day": k,
        "Rinter": Rinter,
        # Metadata cho export và debug
        "Ke_data": corr.get("Ke_data") if is_clay else None,
        "Alpha_data": corr.get("Alpha_data") if not is_clay else None,
        "Ground_Truth_Check": corr.get("Ground_Truth_Check"),
        "data_missing": missing if missing else None,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "Hardening Soil (Schanz et al., 1999) + CIRIA C760 + Ke/α v2.3",
        "Scope_Limitation": [
            "Chưa xét OCR (giả thiết NC soil, OCR = 1)",
            "Chưa xét anisotropy (đẳng hướng)",
            "Rinter mặc định theo CIRIA C760 — kiểm tra với điều kiện thực tế"
        ]
    }

    return result


def process_all_layers(layers_data, wall_type="dw"):
    """
    Xử lý toàn bộ các lớp đất → HS parameters.
    Fix v2.3.1: Bổ sung Ke_data và Alpha_data vào summary.
    """
    results = [build_hs_params(l, wall_type) for l in layers_data]

    summary_table = []
    for r in results:
        summary_table.append({
            "Lớp": r["layer_id"],
            "Mô tả": r["layer_name"],
            "Model": r["model"],
            "Type": r["drainage_type"],
            "γ_unsat": r["gamma_unsat_kn_m3"],
            "γ_sat": r["gamma_sat_kn_m3"],
            "E50ref": r["E50_ref_kpa"],
            "Eoedref": r["Eoed_ref_kpa"],
            "Eurref": r["Eur_ref_kpa"],
            "m": r["m"],
            "c'": r["c_kpa"],
            "φ'": r["phi_deg"],
            "ψ": r["psi_deg"],
            "ν_ur": r["nu_ur"],
            "Rinter": r["Rinter"],
            "kx (m/ngày)": r["k_x_m_per_day"],
            "Ke": (r.get("Ke_data") or {}).get("recommended", None) if r["drainage_type"] == "Undrained" else None,
            "α": (r.get("Alpha_data") or {}).get("recommended", None) if r["drainage_type"] == "Drained" else None,
        })

    return {
        "model": "Hardening Soil",
        "layers": results,
        "summary_table": summary_table,
        "Standard_Method": "Hardening Soil (Schanz et al., 1999) + CIRIA C760 + Ke/α v2.3"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 3 v2.3.1: Thông số Hardening Soil — Đã sửa Ke/α và Rinter"
    )
    parser.add_argument("--input", required=True, help="JSON input file")
    parser.add_argument("--wall", default="dw", choices=["dw", "sp", "secant"],
                        help="Loại tường chắn (dw=Diaphragm Wall, sp=Sheet Pile)")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = process_all_layers(data["layers"], args.wall)
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
