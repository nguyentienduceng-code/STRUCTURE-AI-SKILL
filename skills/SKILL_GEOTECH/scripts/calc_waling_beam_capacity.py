"""
MODULE 12b: calc_waling_beam_capacity.py
SKILL_GEOTECH v2.4.0 -- Urban Excavation Upgrade
Kiem tra kha nang chiu uon cua Dam bo (Waling Beam) theo phuong ngang.
Tieu chuan: TCVN 5575:2018, EC3 EN 1993-1-1
Usage:
  python calc_waling_beam_capacity.py --section H200 --q 60 --spans 2.0,3.5,3.5
  python calc_waling_beam_capacity.py --section I200 --q 60 --spans 2.0,10.5 --scheme simple
"""
import sys, json, math, argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SECTION_DB = {
    "I150": {"Wy": 91.8,  "label": "I150x75x7x5"},
    "I200": {"Wy": 214.0, "label": "I200x100x8.5x5.6"},
    "I250": {"Wy": 410.0, "label": "I250x125x9.7x6"},
    "H150": {"Wy": 219.0, "label": "H150x150x10x7"},
    "H200": {"Wy": 472.0, "label": "H200x200x12x8"},
    "H250": {"Wy": 861.0, "label": "H250x250x14x9"},
    "H300": {"Wy": 1360,  "label": "H300x300x15x10"},
    "H350": {"Wy": 2300,  "label": "H350x350x19x12"},
    "2H200":{"Wy": 944.0, "label": "2xH200x200x12x8 (doi)"},
    "2H300":{"Wy": 2720,  "label": "2xH300x300x15x10 (doi)"},
}

def eta_color(eta):
    if eta <= 0.70: return "XANH_LA (du)"
    elif eta <= 0.90: return "VANG (hop_ly)"
    elif eta <= 1.00: return "CAM (sat_nguong)"
    else: return "DO (KHONG_DAT)"

def check_waling_beam(section_name, q_lateral, spans, fy=250, gamma_M0=1.0, scheme="simple"):
    logs = []
    if section_name not in SECTION_DB:
        return {"error": f"E001: Section '{section_name}' not found. Valid: {list(SECTION_DB.keys())}"}
    sec = SECTION_DB[section_name]
    M_Rd = (fy / gamma_M0) * sec["Wy"] * 1e3 / 1e6
    coeff = 8.0 if scheme == "simple" else 10.0
    scheme_label = "dam don gian (M=qL2/8)" if scheme == "simple" else "dam lien tuc (M=qL2/10)"
    L_max = math.sqrt(M_Rd * coeff / q_lateral)
    logs.append({"step": "M_Rd", "formula": "M_Rd = (fy/gM0) x Wy", "value": f"{M_Rd:.1f} kNm", "source": "TCVN 5575:2018"})
    logs.append({"step": "So do tinh", "value": scheme_label})
    logs.append({"step": "L_max_safe", "formula": f"L_max = sqrt(M_Rd x {coeff:.0f} / q)", "value": f"{L_max:.2f} m"})
    results = []
    critical_eta = 0
    for i, L in enumerate(spans):
        M_max = q_lateral * L**2 / coeff
        eta = round(M_max / M_Rd, 3)
        results.append({"nhip": i+1, "L_m": L, "M_max_kNm": round(M_max,1), "M_Rd_kNm": round(M_Rd,1), "eta": eta, "color": eta_color(eta), "ket_luan": "DAT" if eta<=1.0 else "KHONG DAT"})
        logs.append({"step": f"Nhip {i+1} L={L}m", "formula": f"M_max=q*L^2/{coeff:.0f}", "value": f"M_max={M_max:.1f} kNm, eta={eta}"})
        critical_eta = max(critical_eta, eta)
    recommendation = []
    if critical_eta > 1.0:
        Lc = max(spans)
        M_req = q_lateral * Lc**2 / coeff
        Wy_req = M_req * 1e6 / ((fy/gamma_M0) * 1e3)
        for sname, sdata in SECTION_DB.items():
            if sdata["Wy"] >= Wy_req:
                recommendation.append(f"Tiet dien de xuat: {sdata['label']} (Wy={sdata['Wy']} cm3 >= {Wy_req:.0f} cm3 can thiet)")
                break
    else:
        recommendation.append("Tat ca nhip dat yeu cau. Khong can doi tiet dien.")
    return {"Standard_Method": "TCVN 5575:2018 / EC3 EN 1993-1-1", "section": sec["label"], "M_Rd_kNm": round(M_Rd,1), "q_lateral_kNm": q_lateral, "scheme": scheme_label, "L_max_safe_m": round(L_max,2), "Span_Results": results, "Critical_eta": round(critical_eta,3), "Critical_Color": eta_color(critical_eta), "Overall": "DAT" if critical_eta<=1.0 else "KHONG DAT", "Recommendation": recommendation, "Calculation_Logs": logs}

def main():
    p = argparse.ArgumentParser(description="MODULE 12b: Waling Beam Capacity Check")
    p.add_argument("--section", required=True, help="Section code e.g. H200, I200")
    p.add_argument("--q", type=float, required=True, help="Lateral earth pressure (kN/m)")
    p.add_argument("--spans", required=True, help="Free spans comma-separated (m) e.g. 2.0,3.5,3.5")
    p.add_argument("--fy", type=float, default=250)
    p.add_argument("--gamma_M0", type=float, default=1.0)
    p.add_argument("--scheme", choices=["simple","continuous"], default="simple")
    args = p.parse_args()
    spans = [float(x) for x in args.spans.split(",")]
    result = check_waling_beam(args.section, args.q, spans, args.fy, args.gamma_M0, args.scheme)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
