import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_structural_elements.py — MODULE 4: Quy đổi kết cấu → Plaxis
# =============================================================================
# Version: 2.0.0
# Standard_Method: Plaxis Material Models Manual + TCVN 5574:2018 (BTCT) + Stiffness Degradation
# Reference: Tinh toan CU LARSEN.xls Sheet 'Input 4 Plaxis' + Sheet 'Vat lieu'
#            HLH-PKT Sheet 'Sheet2'
# =============================================================================

# ── Cơ sở dữ liệu vật liệu ──

CONCRETE_DB = {
    "B15": {"Rb": 8.5, "Rbt": 0.75, "Eb": 23000, "Mac": "M200"},
    "B20": {"Rb": 11.5, "Rbt": 0.9, "Eb": 27000, "Mac": "M250"},
    "B22.5": {"Rb": 13.0, "Rbt": 1.05, "Eb": 28500, "Mac": "M300"},
    "B25": {"Rb": 14.5, "Rbt": 1.1, "Eb": 30000, "Mac": "M350"},
    "B30": {"Rb": 17.0, "Rbt": 1.2, "Eb": 32500, "Mac": "M400"},
    "B35": {"Rb": 19.5, "Rbt": 1.3, "Eb": 34500, "Mac": "M450"},
    "B40": {"Rb": 22.0, "Rbt": 1.4, "Eb": 36000, "Mac": "M500"},
    "B45": {"Rb": 25.0, "Rbt": 1.45, "Eb": 37500, "Mac": "M600"},
    "B50": {"Rb": 27.5, "Rbt": 1.55, "Eb": 39000, "Mac": "M700"},
}  # Rb, Rbt: MPa; Eb: MPa

STEEL_SECTION_DB = {
    "H250": {"name": "H250x250x9x14", "A_cm2": 92.2, "Iy_cm4": 4050, "iy_cm": 6.63},
    "H300": {"name": "H300x300x10x15", "A_cm2": 119.8, "Iy_cm4": 6750, "iy_cm": 7.51},
    "H350": {"name": "H350x350x12x19", "A_cm2": 173.9, "Iy_cm4": 13600, "iy_cm": 8.84},
    "H400": {"name": "H400x400x13x21", "A_cm2": 218.7, "Iy_cm4": 22400, "iy_cm": 10.12},
    "2H300": {"name": "2H300x300x10x15", "A_cm2": 239.6, "Iy_cm4": 13500, "iy_cm": 7.51},
    "2H350": {"name": "2H350x350x12x19", "A_cm2": 347.8, "Iy_cm4": 27200, "iy_cm": 8.84},
    "2H400": {"name": "2H400x400x13x21", "A_cm2": 437.4, "Iy_cm4": 44800, "iy_cm": 10.12},
}

SHEET_PILE_DB = {
    "SP_III_w": {
        "name": "Larssen SP III w (Hyundai Steel)",
        "A_m2_per_m": 0.02425,
        "I_m4_per_m": 0.000386,
        "W_m3_per_m": 0.001930,  # approximate
        "E_kpa": 200_000_000,
        "fy_kpa": 295_000,       # SY295
        "fv_kpa": 170_000,
    },
    "SP_IV": {
        "name": "Larssen SP IV",
        "A_m2_per_m": 0.0293,
        "I_m4_per_m": 0.000596,
        "W_m3_per_m": 0.002270,
        "E_kpa": 200_000_000,
        "fy_kpa": 295_000,
        "fv_kpa": 170_000,
    },
    "C250x50x6": {
        "name": "Trench Sheet Pile C250x50x6 (JIS A 5528)",
        "A_m2_per_m": 0.03244,
        "I_m4_per_m": 0.0002508,
        "W_m3_per_m": 0.002004,
        "E_kpa": 210_000_000,
        "fy_kpa": 235_000,       # SS400
        "fv_kpa": 135_700,
    },
}

E_STEEL = 210_000_000  # kN/m² (= 210,000 MPa)
GAMMA_CONCRETE = 25.0  # kN/m³


def calc_diaphragm_wall(thickness_m, concrete_grade="B25", underwater=False, cracked_section_factor=0.6):
    """
    Tính thông số Plaxis cho tường vây (Diaphragm Wall) — dạng Plate element.

    Parameters
    ----------
    thickness_m : float
        Bề dày tường vây (m), VD: 0.5, 0.6, 0.7, 0.8, 1.0
    concrete_grade : str
        Mác bê tông, VD: "B25", "B30"
    underwater : bool
        True nếu bê tông đổ dưới nước (giảm Rb theo kinh nghiệm)
    cracked_section_factor : float
        Hệ số giảm độ cứng uốn (EI) do nứt. Mặc định 0.6 (60% tiết diện nguyên).

    Returns
    -------
    dict with Plaxis plate parameters
    """
    if concrete_grade not in CONCRETE_DB:
        return {"error": f"Unknown concrete grade: {concrete_grade}. Available: {list(CONCRETE_DB.keys())}"}

    concrete = CONCRETE_DB[concrete_grade]
    E_concrete = concrete["Eb"] * 1000  # MPa → kN/m² (kPa)

    b = 1.0  # m/m (per meter run)
    h = thickness_m

    A = b * h                    # m²/m
    I = b * h ** 3 / 12.0        # m⁴/m
    W = I / (h / 2.0)            # m³/m (Moment khang uon)

    EA = E_concrete * A          # kN/m
    EI_uncracked = E_concrete * I
    EI = EI_uncracked * cracked_section_factor  # kNm²/m (Stiffness Degradation)
    w = GAMMA_CONCRETE * h       # kN/m²/m (trọng lượng)
    nu = 0.15                    # Poisson bê tông

    reduction_note = ""
    if underwater:
        reduction_note = "Bê tông đổ dưới nước — cường độ giảm theo kinh nghiệm. EA/EI dùng Eb tiêu chuẩn, Rb kiểm tra giảm 15-30%."

    calc_logs = [
        {
            "step": "Đặc trưng tiết diện tường vây",
            "b": f"{b} m/m",
            "h": f"{h} m",
            "A": f"b × h = {b} × {h} = {A} m²/m",
            "I_nguyen": f"b × h³/12 = {b} × {h}³/12 = {round(I, 6)} m⁴/m"
        },
        {
            "step": "Thông số Plaxis (Plate)",
            "E_concrete": f"{E_concrete} kN/m² ({concrete_grade}, Eb = {concrete['Eb']} MPa)",
            "EA": f"E × A = {E_concrete} × {A} = {EA} kN/m",
            "EI_nứt": f"EI_uncracked × {cracked_section_factor} = {round(EI_uncracked, 2)} × {cracked_section_factor} = {round(EI, 2)} kNm²/m",
            "w": f"γ_c × h = {GAMMA_CONCRETE} × {h} = {w} kN/m²/m",
            "nu": nu
        }
    ]

    return {
        "element_type": "Diaphragm Wall (Plate)",
        "thickness_m": h,
        "concrete_grade": concrete_grade,
        "A_m2_per_m": A,
        "I_m4_per_m": round(I, 8),
        "W_m3_per_m": round(W, 8),
        "E_kpa": E_concrete,
        "EA_kn_per_m": EA,
        "EI_knm2_per_m": round(EI, 2),
        "w_kn_per_m2_per_m": w,
        "nu": nu,
        "underwater_note": reduction_note,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "TCVN 5574:2018 + Plaxis Material Models Manual",
        "Scope_Limitation": []
    }


def calc_sheet_pile(pile_type="SP_III_w"):
    """
    Tính thông số Plaxis cho cừ thép — dạng Plate element.
    """
    if pile_type not in SHEET_PILE_DB:
        return {"error": f"Unknown sheet pile type: {pile_type}. Available: {list(SHEET_PILE_DB.keys())}"}

    sp = SHEET_PILE_DB[pile_type]
    E = sp["E_kpa"]
    A = sp["A_m2_per_m"]
    I = sp["I_m4_per_m"]
    W = sp.get("W_m3_per_m", 0)
    fy = sp.get("fy_kpa", 235000)
    fv = sp.get("fv_kpa", 135700)

    EA = E * A
    EI = E * I
    w = 78.5 * A  # γ_steel ≈ 78.5 kN/m³ (approximate per meter run)
    nu = 0.3
    
    # Capacity
    M_rd = W * fy  # kNm/m
    # Use approximate V_rd if exact web area is unknown (from user context for C250x50x6 it is 1523.9)
    if pile_type == "C250x50x6":
        V_rd = 1523.9
    else:
        V_rd = (A * 0.5) * fv  # Rough approximation for web

    d_equiv = math.sqrt(12 * I / A)  # Bề dày tương đương

    return {
        "element_type": f"Sheet Pile ({sp['name']})",
        "pile_type": pile_type,
        "A_m2_per_m": A,
        "I_m4_per_m": I,
        "W_m3_per_m": W,
        "E_kpa": E,
        "EA_kn_per_m": EA,
        "EI_knm2_per_m": EI,
        "w_kn_per_m2_per_m": round(w, 4),
        "nu": nu,
        "d_equiv_m": round(d_equiv, 4),
        "M_rd_knm_per_m": round(M_rd, 2),
        "V_rd_kn_per_m": round(V_rd, 2),
        "Calculation_Logs": [{
            "step": "Cừ Thép → Plaxis Plate & Capacity",
            "section": sp["name"],
            "EA": f"E × A = {E} × {A} = {EA} kN/m",
            "EI": f"E × I = {E} × {I} = {EI} kNm²/m",
            "d_equiv": f"√(12I/A) = √(12×{I}/{A}) = {round(d_equiv, 4)} m",
            "w": f"A × γ_steel = {A} × 78.5 = {round(w, 4)} kN/m/m",
            "M_rd": f"W × fy = {W} × {fy} = {round(M_rd, 2)} kNm/m",
            "nu": f"{nu} (Thép kết cấu)"
        }],
        "Standard_Method": "JIS A 5528 + Plaxis Material Models Manual",
        "Scope_Limitation": []
    }


def calc_strut(section_type="H350", spacing_m=None):
    """
    Tính thông số Plaxis cho thanh chống (Strut) — dạng Node-to-Node Anchor.

    Parameters
    ----------
    section_type : str
        Loại thép hình, VD: "H300", "H350", "H400", "2H350"
    spacing_m : float or None
        Khoảng cách strut (m). Nếu có → tính EA/m.
    """
    if section_type not in STEEL_SECTION_DB:
        return {"error": f"Unknown section: {section_type}. Available: {list(STEEL_SECTION_DB.keys())}"}

    sec = STEEL_SECTION_DB[section_type]
    A_m2 = sec["A_cm2"] * 1e-4  # cm² → m²

    EA_per_strut = E_STEEL * A_m2  # kN

    result = {
        "element_type": f"Strut ({sec['name']})",
        "section_type": section_type,
        "A_m2": round(A_m2, 6),
        "A_cm2": sec["A_cm2"],
        "Iy_cm4": sec["Iy_cm4"],
        "iy_cm": sec["iy_cm"],
        "E_kpa": E_STEEL,
        "EA_per_strut_kn": round(EA_per_strut, 0),
        "Calculation_Logs": [{
            "step": "Strut → Plaxis Anchor",
            "section": sec["name"],
            "A": f"{sec['A_cm2']} cm² = {round(A_m2, 6)} m²",
            "EA": f"E × A = {E_STEEL} × {round(A_m2, 6)} = {round(EA_per_strut, 0)} kN"
        }],
        "Standard_Method": "Plaxis Material Models Manual",
        "Scope_Limitation": []
    }

    if spacing_m is not None:
        EA_per_m = EA_per_strut / spacing_m
        result["spacing_m"] = spacing_m
        result["EA_per_m_kn_per_m"] = round(EA_per_m, 0)
        result["Calculation_Logs"].append({
            "step": "Quy đổi EA/m",
            "formula": f"EA/m = EA / spacing = {round(EA_per_strut, 0)} / {spacing_m} = {round(EA_per_m, 0)} kN/m"
        })

    return result


def calc_concrete_slab(thickness_mm, concrete_grade="B25"):
    """
    Tính thông số Plaxis cho sàn hầm BTCT (dùng như strut level).
    """
    if concrete_grade not in CONCRETE_DB:
        return {"error": f"Unknown concrete grade: {concrete_grade}"}

    h_m = thickness_mm / 1000.0
    E = CONCRETE_DB[concrete_grade]["Eb"] * 1000  # kPa

    A = 1.0 * h_m
    I = 1.0 * h_m ** 3 / 12.0
    EA = E * A
    EI = E * I

    return {
        "element_type": f"Concrete Slab ({thickness_mm}mm, {concrete_grade})",
        "thickness_mm": thickness_mm,
        "concrete_grade": concrete_grade,
        "EA_kn_per_m": EA,
        "EI_knm2_per_m": round(EI, 2),
        "Calculation_Logs": [{
            "step": f"Sàn BTCT {thickness_mm}mm → Plaxis Plate",
            "h": f"{thickness_mm} mm = {h_m} m",
            "E": f"{E} kN/m² ({concrete_grade})",
            "EA": f"{EA} kN/m",
            "EI": f"{round(EI, 2)} kNm²/m"
        }],
        "Standard_Method": "TCVN 5574:2018 + Plaxis Manual",
        "Scope_Limitation": []
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 4: Quy đổi kết cấu chắn giữ → thông số Plaxis"
    )
    parser.add_argument("--type", required=True,
                        choices=["dw", "sp", "strut", "slab"],
                        help="Loại kết cấu: dw/sp/strut/slab")
    parser.add_argument("--thickness", type=float, help="Bề dày DW (m) hoặc sàn (mm)")
    parser.add_argument("--concrete", default="B25", help="Mác bê tông")
    parser.add_argument("--section", default="H350", help="Loại thép hình cho strut")
    parser.add_argument("--pile-type", default="SP_III_w", help="Loại cừ Larsen")
    parser.add_argument("--spacing", type=float, help="Khoảng cách strut (m)")
    parser.add_argument("--cracked", type=float, default=0.6, help="Hệ số nứt (EI reduction) cho DW")
    parser.add_argument("--underwater", action="store_true", help="BT đổ dưới nước")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    if args.type == "dw":
        if args.thickness is None:
            print("Error: --thickness required for DW type")
            sys.exit(1)
        result = calc_diaphragm_wall(args.thickness, args.concrete, args.underwater, args.cracked)
    elif args.type == "sp":
        result = calc_sheet_pile(args.pile_type)
    elif args.type == "strut":
        result = calc_strut(args.section, args.spacing)
    elif args.type == "slab":
        if args.thickness is None:
            print("Error: --thickness required for slab type (in mm)")
            sys.exit(1)
        result = calc_concrete_slab(args.thickness, args.concrete)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
