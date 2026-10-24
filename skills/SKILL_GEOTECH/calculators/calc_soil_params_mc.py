import sys
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_soil_params_mc.py — MODULE 2: Thông số Mohr-Coulomb cho Plaxis
# =============================================================================
# Version: 2.3.1
# Standard_Method: Mohr-Coulomb Model + CIRIA C760 (Rinter) + Ke/α v2.3
# Fixes v2.3.1:
#   - Thêm Eoed vào output (thiếu trước đó)
#   - Sửa Rinter mặc định cho DW: 1.0 → 0.67 (CIRIA C760)
#   - Thêm logic psi tự động: psi = max(0, phi - 30) theo Plaxis Manual
#   - Tích hợp Ke/α v2.3 vào calc_logs
# Reference: Tinh toan CU LARSEN.xls Sheet 'Input 4 Plaxis'
# =============================================================================

from calc_spt_correlations import correlate_spt


# ── Bảng Rinter mặc định theo CIRIA C760 (v2.3.1 FIX) ──
DEFAULT_RINTER = {
    "dw": {
        "sandy": 0.67,
        "silty": 0.70,
        "clay_stiff": 0.70,
        "clay_soft": 0.60,
        "default": 0.67
    },
    "sp": {
        "sandy": 0.67,
        "silty": 0.60,
        "clay": 0.55,
        "default": 0.67
    },
    "secant": {
        "default": 0.80
    }
}


def _get_rinter(wall_type, soil_description):
    """Xác định Rinter theo CIRIA C760. Fix v2.3.1."""
    n = (soil_description or "").lower()

    if any(k in n for k in ["cát", "sand", "cat"]):
        soil_key = "sandy"
    elif any(k in n for k in ["sét", "clay", "bùn"]):
        soil_key = "clay_soft" if any(k in n for k in ["mềm", "soft", "dẻo"]) else "clay_stiff"
    elif any(k in n for k in ["silt", "bụi", "pha"]):
        soil_key = "silty"
    else:
        soil_key = "default"

    rinter_db = DEFAULT_RINTER.get(wall_type, DEFAULT_RINTER["dw"])
    return rinter_db.get(soil_key, rinter_db["default"])


def _estimate_psi(phi_deg):
    """
    Ước lượng góc nở dilation psi.
    Fix v2.3.1: Không còn hardcode psi=0.
    Theo Plaxis Manual: ψ ≈ φ' - 30° cho đất cứng; ψ ≈ 0 cho đất mềm.
    """
    if phi_deg is None:
        return 0.0
    psi = phi_deg - 30.0
    return max(0.0, round(psi, 1))


def build_mc_params(layer_data, wall_type="dw"):
    """
    Xây dựng bộ thông số Mohr-Coulomb cho 1 lớp đất (v2.3.1).

    Fixes v2.3.1:
      - Thêm Eoed_ref_kpa (thiếu trước đó)
      - Rinter mặc định: dw → 0.67 (CIRIA C760), không còn 1.0
      - psi: tự động tính = max(0, φ - 30)
      - Calc_logs đầy đủ Ke/α

    Parameters
    ----------
    layer_data : dict
        {id, name, spt_avg, description, is_cohesive, gamma_unsat, gamma_sat,
         c_kpa, phi_deg, E_kpa, nu, k_m_per_day, Rinter, Eoed_ref_kpa}
        Nếu thiếu thông số → dùng SPT correlation để bổ sung.
    wall_type : str
        'dw', 'sp', hoặc 'secant'

    Returns
    -------
    dict: MC parameters ready for Plaxis
    """
    spt = layer_data.get("spt_avg")
    desc = layer_data.get("description", "")

    # Get correlation data từ MODULE 5
    corr = {}
    if spt is not None:
        corr = correlate_spt(
            spt,
            soil_description=desc,
            is_cohesive=layer_data.get("is_cohesive"),
            wall_type=wall_type,
            Su_kpa=layer_data.get("Su_kpa"),
            Ip_pct=layer_data.get("Ip_pct")
        )

    def get_val(key, corr_key=None):
        v = layer_data.get(key)
        if v is not None:
            return v
        ck = corr_key or key
        return corr.get(ck)

    drainage = get_val("drainage_type", "drainage_type")
    if drainage is None:
        drainage = "Undrained" if corr.get("drainage_type") == "Undrained" else "Drained"

    is_clay = (drainage == "Undrained")

    gamma_unsat = get_val("gamma_unsat")
    gamma_sat = get_val("gamma_sat")
    c = get_val("c_kpa")
    phi = get_val("phi_deg")

    # ── Eoed: Fix v2.3.1 — bổ sung Eoed_ref_kpa ──
    Eoed = get_val("Eoed_ref_kpa")
    E = get_val("E_kpa") or get_val("E50_ref_kpa")

    if Eoed is None and E is not None:
        Eoed = E  # ≈ Eref (Plaxis MC dùng E thay vì E50)

    # ── psi: Fix v2.3.1 — tự động tính theo Plaxis Manual ──
    psi = get_val("psi_deg")
    if psi is None or psi == 0.0:
        psi = _estimate_psi(phi)

    # ── nu ──
    nu = get_val("nu") or get_val("nu_mc") or (0.35 if is_clay else 0.30)

    k = get_val("k_m_per_day")

    # ── Rinter: Fix v2.3.1 — CIRIA C760 thay vì 1.0 ──
    Rinter = get_val("Rinter")
    if Rinter is None:
        Rinter = _get_rinter(wall_type, desc)

    # ── Ke/α metadata ──
    if is_clay:
        Ke_data = corr.get("Ke_data")
        formula_label = "Ke × Su (đất dính)"
        formula_note = f"Ke={Ke_data.get('recommended','?')} (CIRIA C760)" if Ke_data else "Từ MODULE 5"
    else:
        Alpha_data = corr.get("Alpha_data")
        formula_label = "α × N_SPT (đất rời)"
        formula_note = f"α={Alpha_data.get('recommended','?')} (Bowles 1997)" if Alpha_data else "Từ MODULE 5"

    missing = []
    if gamma_unsat is None: missing.append("gamma_unsat")
    if gamma_sat is None: missing.append("gamma_sat")
    if c is None: missing.append("c_kpa")
    if phi is None: missing.append("phi_deg")
    if E is None: missing.append("E_kpa (Eref)")

    calc_logs = [
        {
            "step": "Bước 1: Xác định điều kiện thoát nước",
            "drainage_type": drainage,
            "is_cohesive": is_clay
        },
        {
            "step": "Bước 2: Dung trọng γ",
            "gamma_unsat": gamma_unsat,
            "gamma_sat": gamma_sat,
            "source": "Lab Test" if layer_data.get("gamma_sat") else "SPT correlation"
        },
        {
            "step": "Bước 3: Module đàn hồi Eref",
            "Eref_kpa": E,
            "Eoed_ref_kpa": Eoed,
            "note": "MC dùng E thay vì E50; Eoed bổ sung cho phép nén một chiều",
            "formula": formula_label,
            "formula_detail": formula_note
        },
        {
            "step": "Bước 4: Thông số cường độ",
            "c_kpa": c,
            "phi_deg": phi,
            "psi_deg": psi,
            "psi_note": "ψ = max(0, φ - 30) theo Plaxis Manual"
        },
        {
            "step": "Bước 5: Hệ số Poisson ν",
            "nu": nu
        },
        {
            "step": "Bước 6: Hệ số Rinter (v2.3.1 FIX)",
            "Rinter": Rinter,
            "wall_type": wall_type,
            "note": "Theo CIRIA C760 — Không còn dùng Rinter=1.0 cho DW",
            "reference": "CIRIA C760 Table 6.2"
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
        "model": "Mohr-Coulomb",
        "drainage_type": drainage,
        "gamma_unsat_kn_m3": gamma_unsat,
        "gamma_sat_kn_m3": gamma_sat,
        "Eref_kpa": E,
        "Eoed_ref_kpa": Eoed,          # Fix v2.3.1: bổ sung
        "nu": nu,
        "c_kpa": c,
        "phi_deg": phi,
        "psi_deg": psi,
        "k_x_m_per_day": k,
        "k_y_m_per_day": k,
        "Rinter": Rinter,
        "Ke_data": corr.get("Ke_data") if is_clay else None,
        "Alpha_data": corr.get("Alpha_data") if not is_clay else None,
        "data_missing": missing if missing else None,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "Mohr-Coulomb Model (Plaxis Manual) + CIRIA C760 + Ke/α v2.3",
        "Scope_Limitation": [
            "MC không mô tả được ứng xử dỡ tải-gia tải lại",
            "Phù hợp cho phân tích sơ bộ, đất san lấp, hoặc bài toán ổn định mái dốc",
            "Với hố đào sâu → khuyến nghị dùng Hardening Soil (MODULE 3)"
        ]
    }

    return result


def process_all_layers(layers_data, wall_type="dw"):
    """Xử lý toàn bộ các lớp đất → MC parameters."""
    results = [build_mc_params(l, wall_type) for l in layers_data]
    return {
        "model": "Mohr-Coulomb",
        "layers": results,
        "Standard_Method": "Mohr-Coulomb Model (Plaxis Manual) + CIRIA C760 + Ke/α v2.3"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 2 v2.3.1: Thông số Mohr-Coulomb — Đã sửa Rinter và bổ sung Eoed"
    )
    parser.add_argument("--input", required=True, help="JSON input file")
    parser.add_argument("--wall", default="dw", choices=["dw", "sp", "secant"])
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
