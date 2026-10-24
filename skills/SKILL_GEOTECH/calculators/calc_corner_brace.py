"""
MODULE 15: calc_corner_brace.py
SKILL_GEOTECH v2.4.0 -- Urban Excavation Upgrade
Tinh toan he thong chong goc xien (Corner Brace / Raking Strut) trong ho dao.
Tieu chuan: TCVN 5575:2024 / EC3 EN 1993-1-1
Usage:
  python calc_corner_brace.py --section H200 --x 5.5 --y 4.5 --q_long 60 --q_short 60
"""
import sys, json, math, argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SECTION_DB = {
    "I150": {"Wy": 91.8,  "A_cm2": 17.9, "iy_cm": 6.20, "label": "I150x75x7x5"},
    "I200": {"Wy": 214.0, "A_cm2": 28.5, "iy_cm": 8.67, "label": "I200x100x8.5x5.6"},
    "H200": {"Wy": 472.0, "A_cm2": 63.5, "iy_cm": 8.62, "label": "H200x200x12x8"},
    "H250": {"Wy": 861.0, "A_cm2": 91.4, "iy_cm": 10.80,"label": "H250x250x14x9"},
    "H300": {"Wy": 1360,  "A_cm2": 119,  "iy_cm": 13.10,"label": "H300x300x15x10"},
}

from pathlib import Path
for _p in Path(__file__).resolve().parents:
    if (_p / "_SHARED" / "standards" / "tables.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

try:
    from _SHARED.standards.tables import GAMMA_M0
except ImportError:
    GAMMA_M0 = 1.05

def calc_corner_brace(section_name, x, y, q_long, q_short, fy=250, gamma_M0=GAMMA_M0, E=206000):
    """
    x: khoang cach diem ty tren canh dai (m)
    y: khoang cach diem ty tren canh ngan (m)
    q_long: ap luc dat ngang phan bo canh dai (kN/m)
    q_short: ap luc dat ngang phan bo canh ngan (kN/m)
    """
    logs = []
    if section_name not in SECTION_DB:
        return {"error": f"E001: Section '{section_name}' not in DB. Valid: {list(SECTION_DB.keys())}"}

    sec = SECTION_DB[section_name]
    L_brace = math.sqrt(x**2 + y**2)
    angle_deg = math.degrees(math.atan(y / x))
    angle_rad = math.atan(y / x)

    logs.append({"step": "Hinh hoc thanh chong goc", "formula": "L = sqrt(x^2 + y^2)", "x_m": x, "y_m": y, "L_brace_m": round(L_brace,3), "angle_deg": round(angle_deg,1)})

    # Luc phan tai tu dam bo vao diem ty
    R_long = q_long * x     # Phan luc tu canh dai (kN)
    R_short = q_short * y   # Phan luc tu canh ngan (kN)
    logs.append({"step": "Phan luc tai diem ty", "R_long_kN": round(R_long,1), "R_short_kN": round(R_short,1), "note": "R = q x khoang_canh_tai"})

    # Luc nen doc truc thanh chong goc (phoi hop 2 phan luc)
    N_brace = math.sqrt(R_long**2 + R_short**2)
    logs.append({"step": "Luc nen doc truc", "formula": "N = sqrt(R_long^2 + R_short^2)", "value": f"N = sqrt({R_long:.1f}^2 + {R_short:.1f}^2) = {N_brace:.1f} kN"})

    # Kiem tra on dinh (Buckling) - EC3 / TCVN 5575:2024
    A_mm2 = sec["A_cm2"] * 100
    iy_mm = sec["iy_cm"] * 10
    L0_mm = L_brace * 1000  # chieu dai uon doc (ca bung)

    lambda_ratio = L0_mm / iy_mm
    lambda_1 = math.pi * math.sqrt(E / fy)  # ~ 93 voi E=206000, fy=250
    lambda_bar = (lambda_ratio / lambda_1)   # Do manh tuong doi

    # He so uon doc Phi theo duong cong b (TCVN 5575 / EC3)
    alpha = 0.34  # duong cong b
    phi_val = 0.5 * (1 + alpha*(lambda_bar - 0.2) + lambda_bar**2)
    chi = min(1.0, 1.0 / (phi_val + math.sqrt(phi_val**2 - lambda_bar**2)))

    N_Rd = chi * A_mm2 * fy / (gamma_M0 * 1000)  # kN
    eta_brace = round(N_brace / N_Rd, 3)
    logs.append({"step": "Kiem tra buckling", "lambda_ratio": round(lambda_ratio,1), "lambda_bar": round(lambda_bar,3), "chi": round(chi,3), "N_Rd_kN": round(N_Rd,1), "N_Ed_kN": round(N_brace,1), "eta": eta_brace})

    color_map = lambda e: "XANH" if e<=0.70 else ("VANG" if e<=0.90 else ("CAM" if e<=1.0 else "DO_KHONG_DAT"))

    return {
        "Standard_Method": "TCVN 5575:2024 / EC3 EN 1993-1-1 (duong cong b, alpha=0.34)",
        "section": sec["label"],
        "Brace_Geometry": {"x_m": x, "y_m": y, "L_brace_m": round(L_brace,3), "angle_deg": round(angle_deg,1)},
        "Forces": {"R_long_kN": round(R_long,1), "R_short_kN": round(R_short,1), "N_Ed_kN": round(N_brace,1)},
        "Buckling_Check": {"lambda_ratio": round(lambda_ratio,1), "lambda_bar": round(lambda_bar,3), "chi": round(chi,3), "N_Rd_kN": round(N_Rd,1)},
        "eta": eta_brace,
        "color": color_map(eta_brace),
        "ket_luan": "DAT" if eta_brace <= 1.0 else "KHONG DAT -- tang tiet dien",
        "Calculation_Logs": logs
    }

def main():
    p = argparse.ArgumentParser(description="MODULE 15: Corner Brace Capacity Check")
    p.add_argument("--section", required=True)
    p.add_argument("--x", type=float, required=True, help="Khoang ty tren canh dai (m)")
    p.add_argument("--y", type=float, required=True, help="Khoang ty tren canh ngan (m)")
    p.add_argument("--q_long", type=float, required=True, help="Ap luc dat canh dai (kN/m)")
    p.add_argument("--q_short", type=float, required=True, help="Ap luc dat canh ngan (kN/m)")
    p.add_argument("--fy", type=float, default=250)
    p.add_argument("--gamma_M0", type=float, default=1.05)
    args = p.parse_args()
    result = calc_corner_brace(args.section, args.x, args.y, args.q_long, args.q_short, args.fy, args.gamma_M0)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
