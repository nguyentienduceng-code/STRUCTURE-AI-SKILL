import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_geostatic_stress.py — MODULE 1: Ứng suất & K0
# =============================================================================
# Version: 2.3.0
# Standard_Method: Terzaghi (1943), Jaky (1944), Alpan (1967), Mayne & Kulhawy (1982)
# Reference: QUY TRÌNH TÍNH PLAXIS.docx, Soil Investigation 1.xls Sheet 'Stress'
# =============================================================================

GAMMA_W = 9.81  # kN/m³


def calc_k0(is_cohesive, phi_prime_deg, PI=None, OCR=1.0):
    """
    Tính hệ số áp lực ngang K0 ở trạng thái nghỉ.

    Công thức:
    ─ Jaky (1944): K0(NC) = 1 - sin(φ')
    ─ Mayne & Kulhawy (1982): K0(OC) = K0(NC) × OCR^sin(φ')
    """
    if not is_cohesive:
        if phi_prime_deg:
            phi_rad = math.radians(phi_prime_deg)
            k0_nc = 1 - math.sin(phi_rad)
        else:
            k0_nc = 0.5
    else:
        if phi_prime_deg:
            phi_rad = math.radians(phi_prime_deg)
            k0_nc = 1 - math.sin(phi_rad)
        elif PI is not None:
            k0_nc = 0.44 + 0.0042 * PI
        else:
            k0_nc = 0.55

    if OCR > 1.0 and phi_prime_deg:
        k0_oc = k0_nc * (OCR ** math.sin(math.radians(phi_prime_deg)))
        kp = (1 + math.sin(math.radians(phi_prime_deg))) / (1 - math.sin(math.radians(phi_prime_deg)))
        k0 = min(k0_oc, kp)
        method = f"Mayne & Kulhawy (1982) — OC soil (OCR={OCR})"
    else:
        k0 = k0_nc
        method = "Jaky (1944) / Alpan (1967) — NC soil"

    return k0, method


def estimate_ocr_from_cpt(qt_kpa, sigma_v_kpa, sigma_v_eff_kpa, is_stiff_clay=False):
    """Tính OCR từ CPTu theo Kulhawy & Mayne (1990)"""
    if sigma_v_eff_kpa <= 0:
        return 1.0
    Qt = (qt_kpa - sigma_v_kpa) / sigma_v_eff_kpa
    k_factor = 0.45 if is_stiff_clay else 0.33
    ocr = k_factor * Qt
    return max(1.0, ocr)


def _sigma_v_at_z(layers, z_target, gwl_depth):
    """
    Tính σ_v tại cao độ z_target (âm) bằng tích phân từ mặt đất.

    Trả về (sigma_v, calculation_steps)
    """
    # Sort shallow → deep (ascending by depth, i.e. 0 > -1 > -2)
    sorted_layers = sorted(layers, key=lambda l: l["top_depth"])

    sigma_v = 0.0
    steps = []
    current_z = 0.0  # Start at ground surface

    for layer in sorted_layers:
        z_l_top = layer["top_depth"]    # shallower boundary of this layer
        z_l_bot = layer["bottom_depth"]  # deeper boundary of this layer

        # Target is above this layer → no contribution
        if z_target >= z_l_top:
            break

        # How deep into this layer do we go?
        seg_top = current_z
        if z_target > z_l_bot:
            seg_bot = z_target     # target within this layer
        else:
            seg_bot = z_l_bot       # target below this layer

        h_seg = seg_top - seg_bot   # positive: seg_top > seg_bot on depth axis
        if h_seg <= 0:
            continue

        # Select γ based on water table
        mid_z = (seg_top + seg_bot) / 2.0
        if mid_z > gwl_depth:
            gamma = layer.get("gamma_unsat", layer.get("gamma_sat", 18.0))
        else:
            gamma = layer.get("gamma_sat", layer.get("gamma_unsat", 18.0))

        contrib = gamma * h_seg
        sigma_v += contrib
        layer_id = layer.get("id", "?")
        steps.append(
            f"  σv({abs(seg_bot):.2f}m) += γ_{layer_id} × h"
            f" = {gamma:.2f} × {h_seg:.2f} = {contrib:.2f} kPa"
        )
        current_z = seg_bot

    return round(sigma_v, 2), steps


def calc_layer_boundary_stress(layers, gwl_depth, special_depths=None,
                               gamma_w=GAMMA_W):
    """
    Tính ứng suất tại CHÍNH XÁC các cao độ ranh giới lớp (v2.3.0).

    Parameters
    ----------
    layers : list of dict
        Mỗi lớp: {id, name, top_depth, bottom_depth, gamma_unsat, gamma_sat,
                   phi_prime_deg, Ip, OCR, is_cohesive}
    gwl_depth : float
        Cao độ mực nước ngầm (âm, VD: -2.0 m)
    special_depths : list of float or None
        Các cao độ đặc biệt cần tính (đáy hố đào, chân cừ, neo...)
    gamma_w : float
        Dung trọng nước

    Returns
    -------
    dict with layer_boundary_stress + Calculation_Logs
    """
    sorted_layers = sorted(layers, key=lambda l: l["top_depth"], reverse=True)

    # Thu thập tất cả cao độ ranh giới
    all_depths = set()
    for layer in sorted_layers:
        if layer["top_depth"] is not None:
            all_depths.add(layer["top_depth"])
        if layer["bottom_depth"] is not None:
            all_depths.add(layer["bottom_depth"])

    if special_depths:
        for d in special_depths:
            all_depths.add(d)

    all_depths = sorted(all_depths, reverse=True)

    boundary_stress = []
    calc_logs = []

    for z in all_depths:
        # Xác định lớp chứa z
        current_layer = None
        for layer in sorted_layers:
            if layer["top_depth"] >= z >= layer["bottom_depth"]:
                current_layer = layer
                break

        if current_layer is None:
            continue

        # Tính σ_v
        sigma_v, sigma_steps = _sigma_v_at_z(layers, z, gwl_depth)

        # Tính u
        if z <= gwl_depth:
            u = gamma_w * abs(z - gwl_depth)
        else:
            u = 0.0

        sigma_v_eff = sigma_v - u

        # Tính K0
        is_cohesive = current_layer.get("is_cohesive",
            current_layer.get("soil_type", "clay") in ("clay", "silt"))
        phi = current_layer.get("phi", current_layer.get("phi_prime_deg"))
        pi_val = current_layer.get("Ip", current_layer.get("plasticity_index"))
        ocr_val = current_layer.get("OCR", 1.0)

        k0, k0_method = calc_k0(is_cohesive, phi, pi_val, ocr_val)
        sigma_h_eff = round(k0 * sigma_v_eff, 2)

        # Xác định nhãn ranh giới
        label = ""
        if abs(abs(z) - abs(gwl_depth)) < 0.05:
            label = "Mực nước ngầm (GWT)"
        elif special_depths and z in special_depths:
            if z < 0:
                label = f"Điểm đặc biệt (z={z:.2f}m)"
        else:
            # Kiểm tra nếu z = đáy/đỉnh lớp
            for l in sorted_layers:
                if abs(z - l["top_depth"]) < 0.01:
                    label = f"Đỉnh Lớp {l.get('id', l.get('name',''))}"
                    break
                if abs(z - l["bottom_depth"]) < 0.01:
                    label = f"Đáy Lớp {l.get('id', l.get('name',''))}"
                    break

        # Tạo công thức bước tính
        calc_step = f"z = {z:.2f}m → σv = " + " + ".join([f"{round(gamma_w*h, 1) if False else ''}" for _ in sigma_steps])
        sigma_steps_str = "\n".join(sigma_steps) if sigma_steps else ""

        entry = {
            "z": round(z, 2),
            "label": label or "Ranh giới lớp",
            "layer_id": current_layer["id"],
            "layer_name": current_layer.get("name", ""),
            "sigma_v_kpa": sigma_v,
            "u_kpa": round(u, 2),
            "sigma_v_eff_kpa": round(sigma_v_eff, 2),
            "K0": round(k0, 4),
            "K0_method": k0_method,
            "sigma_h_eff_kpa": sigma_h_eff,
            "calculation_steps": sigma_steps_str,
            "gamma_w": gamma_w
        }
        boundary_stress.append(entry)

        calc_logs.append({
            "z": round(z, 2),
            "label": entry["label"],
            "sigma_v": sigma_v,
            "u": round(u, 2),
            "sigma_v_eff": round(sigma_v_eff, 2),
            "K0": round(k0, 4),
            "sigma_h_eff": sigma_h_eff,
            "steps": sigma_steps
        })

    return {
        "layer_boundary_stress": boundary_stress,
        "Calculation_Logs": [{
            "step": "Tính ứng suất hữu hiệu tại ranh giới lớp",
            "formula": "σv = Σ(γi × hi); u = γw × (z - z_GWT); σ'v = σv - u; σ'h = K0 × σ'v",
            "K0_method_nc": "Jaky (1944): K0 = 1 - sin(φ')",
            "K0_method_oc": "Mayne & Kulhawy (1982): K0(OC) = K0(NC) × OCR^sin(φ')",
            "layers_processed": len(layers),
            "gwl_depth": gwl_depth
        }],
        "Standard_Method": "Terzaghi (1943) + Jaky (1944) + Alpan (1967) + Mayne & Kulhawy (1982)"
    }


def calc_geostatic(layers, gwl_depth, depth_step=0.5, max_depth=None, gamma_w=GAMMA_W):
    """
    Tính ứng suất hữu hiệu theo chiều sâu (API cũ — giữ lại tương thích).
    """
    sorted_layers = sorted(layers, key=lambda l: l["top_depth"], reverse=True)

    if max_depth is None:
        max_depth = min(l["bottom_depth"] for l in sorted_layers)

    layer_k0 = {}
    layer_k0_methods = {}
    for layer in sorted_layers:
        is_cohesive = layer.get("is_cohesive",
            layer.get("soil_type", "clay") in ("clay", "silt"))
        phi = layer.get("phi", layer.get("phi_prime_deg"))
        pi_val = layer.get("Ip", layer.get("plasticity_index"))
        ocr_val = layer.get("OCR", 1.0)

        k0, method = calc_k0(is_cohesive, phi, pi_val, ocr_val)
        layer_k0[layer["id"]] = k0
        layer_k0_methods[layer["id"]] = method

    stress_profile = []
    z = 0.0

    while z >= max_depth:
        current_layer = None
        for layer in sorted_layers:
            if layer["top_depth"] >= z >= layer["bottom_depth"]:
                current_layer = layer
                break

        if current_layer is None:
            z = round(z - depth_step, 2)
            continue

        if z > gwl_depth:
            gamma = current_layer.get("gamma_unsat", current_layer.get("gamma_sat", 18.0))
        else:
            gamma = current_layer.get("gamma_sat", current_layer.get("gamma_unsat", 18.0))

        sigma_v, _ = _sigma_v_at_z(layers, z, gwl_depth)

        if z <= gwl_depth:
            u = gamma_w * abs(z - gwl_depth)
        else:
            u = 0.0

        sigma_z_eff = sigma_v - u
        k0 = layer_k0.get(current_layer["id"], 0.5)
        method = layer_k0_methods.get(current_layer["id"], "")
        sigma_x_eff = k0 * sigma_z_eff

        stress_profile.append({
            "z": round(z, 2),
            "layer_id": current_layer["id"],
            "layer_name": current_layer["name"],
            "gamma": round(gamma, 2),
            "sigma_z": round(sigma_v, 2),
            "u": round(u, 2),
            "sigma_z_eff": round(sigma_z_eff, 2),
            "K0": round(k0, 4),
            "K0_method": method,
            "sigma_x_eff": round(sigma_x_eff, 2)
        })

        z = round(z - depth_step, 2)

    return {
        "stress_profile": stress_profile,
        "layer_k0": {str(k): v for k, v in layer_k0.items()},
        "Calculation_Logs": [{
            "step": "Geostatic stress calculation (continuous profile)",
            "formula": "σv = Σ(γi × hi); u = γw × (z - gwl); σ'v = σv - u; σ'x = K0 × σ'v",
            "K0_method_clay": "Alpan (1967): K0 = 0.19 + 0.233 × log10(Ip)",
            "layers_processed": len(sorted_layers),
            "depth_range": f"0.0 to {max_depth} m",
            "gwl": gwl_depth
        }],
        "Standard_Method": "Terzaghi (1943) + Jaky (1944) + Alpan (1967) + Mayne & Kulhawy (1982)"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MODULE 1 v2.3: Tính ứng suất hữu hiệu")
    parser.add_argument("--input", required=True, help="Path to JSON input file")
    parser.add_argument("--output", help="Path to output JSON file (optional)")
    parser.add_argument("--boundary", action="store_true",
                       help="Tính ứng suất tại ranh giới lớp (mặc định: profile liên tục)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    special_depths = data.get("special_depths")

    if args.boundary:
        result = calc_layer_boundary_stress(
            layers=data["layers"],
            gwl_depth=data.get("gwl_depth", -2.0),
            special_depths=special_depths,
            gamma_w=data.get("gamma_w", GAMMA_W)
        )
    else:
        result = calc_geostatic(
            layers=data["layers"],
            gwl_depth=data.get("gwl_depth", -2.0),
            depth_step=data.get("depth_step", 0.5),
            max_depth=data.get("max_depth"),
            gamma_w=data.get("gamma_w", GAMMA_W)
        )

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
