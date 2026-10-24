#!/usr/bin/env python3
"""
earthquake_load_calc.py — Tính tải trọng động đất theo TCVN 9386:2025
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import math
from dataclasses import dataclass, asdict

IMPORTANCE_FACTORS = {
    1.0: [("Nhà ở", "Khách sạn", "Văn phòng", "Thương mại")],
    1.2: [("Bệnh viện", "Trường học", "TT hành chính")],
    1.3: [("Công trình công cộng lớn", "TT văn hóa")],
    1.5: [("Công trình nguy hiểm cao")],
}

BEHAVIOR_FACTORS = {
    ("MRF", "ductile"): 5.0,
    ("MRF", "medium"): 3.5,
    ("SMF", "ductile"): 8.0,
    ("OMF", "medium"): 4.0,
    ("BRB", "special"): 7.0,
    ("CBF", "普通"): 2.0,
    ("WSD", "ductile"): 6.0,
    ("SW", "medium"): 3.0,
    ("RMIX", "medium"): 4.5,
}

SOIL_TYPES = {
    "A": {"Sd": 1.00, "S1": 1.00, "TB": 0.15, "TC": 0.40, "TD": 2.0, "type": "Đá"},
    "B": {"Sd": 1.20, "S1": 1.20, "TB": 0.15, "TC": 0.50, "TD": 2.0, "type": "Đất rắn"},
    "C": {"Sd": 1.15, "S1": 1.15, "TB": 0.20, "TC": 0.60, "TD": 2.0, "type": "Đất trung bình"},
    "D": {"Sd": 1.35, "S1": 1.35, "TB": 0.20, "TC": 0.80, "TD": 2.0, "type": "Đất mềm"},
    "E": {"Sd": 1.40, "S1": 1.40, "TB": 0.15, "TC": 0.50, "TD": 2.0, "type": "Đất rất mềm"},
}

ZONES_PGA = {
    "IA": 0.04,
    "IB": 0.08,
    "II": 0.13,
    "III": 0.20,
    "IV": 0.28,
    "V": 0.36,
    "VI": 0.45,
    "VII": 0.54,
    "VIII": 0.63,
}


@dataclass
class EarthquakeResult:
    Standard: str = "TCVN 9386:2025"
    Method: str = "Response Spectrum"
    BuildingType: str = ""
    Location: str = ""
    Height_m: float = 0.0
    Floors: int = 0
    SoilType: str = "C"
    ImportanceFactor: float = 1.0
    StructuralSystem: str = "MRF"
    Ductility: str = "medium"
    SeismicZone: str = ""
    PGA: float = 0.0
    SDS: float = 0.0
    SD1: float = 0.0
    SDs: float = 0.0
    SD1_calc: float = 0.0
    T_B: float = 0.0
    T_C: float = 0.0
    T_D: float = 0.0
    T: float = 0.0
    R: float = 0.0
    I: float = 1.0
    C_s: float = 0.0
    V_base: float = 0.0
    F_total: float = 0.0
    FloorForces_kn: list = None
    StoryShears_kn: list = None
    Status: str = "OK"
    Error: str = ""
    Calculation_Logs: list = None

    def __post_init__(self):
        if self.FloorForces_kn is None:
            self.FloorForces_kn = []
        if self.StoryShears_kn is None:
            self.StoryShears_kn = []
        if self.Calculation_Logs is None:
            self.Calculation_Logs = []


def get_behavior_factor(system: str, ductility: str) -> float:
    key = (system.upper(), ductility.lower())
    return BEHAVIOR_FACTORS.get(key, 3.5)


def estimate_period(Ct: float, hn: float, x: float = 0.75) -> float:
    return Ct * (hn ** x)


def response_spectrum(ag_S: float, T: float, TB: float, TC: float, TD: float) -> float:
    """
    [FIX BUG-STR-08]: Phổ phản ứng đàn hồi Se(T)/g theo TCVN 9386:2025.
    Đầu vào `ag_S = a_g * S` (chưa nhân 2.5) để tránh nhân trùng 2.5 hai lần!
    """
    if T < 0:
        return 0.0
    if T < TB:
        return ag_S * (1.0 + (2.5 - 1.0) * T / TB)
    elif T <= TC:
        return ag_S * 2.5
    elif T <= TD:
        return ag_S * 2.5 * TC / T
    else:
        return ag_S * 2.5 * TC * TD / (T ** 2)


def lateral_force_distribution(V: float, wi_hi: list) -> list:
    total = sum(wi * hi for wi, hi in wi_hi)
    if total == 0:
        return [0.0] * len(wi_hi)
    return [V * (wi * hi / total) for wi, hi in wi_hi]


def calc_earthquake(args) -> EarthquakeResult:
    res = EarthquakeResult(
        BuildingType=args.building,
        Location=args.location,
        Height_m=args.height,
        Floors=args.floors,
        SoilType=args.soil,
        ImportanceFactor=args.importance,
        StructuralSystem=args.system,
        Ductility=args.ductility,
        Method=args.method,
    )

    logs = []
    zone = ZONES_PGA.get(args.zone, 0.20)
    res.SeismicZone = args.zone
    res.PGA = round(zone, 3)
    logs.append({
        "Step": 1, "Formula": "a_gR = f(vùng động đất)",
        "Substitution": f"a_gR = {zone} g (vùng {args.zone})",
        "Result": f"PGA = {zone} g"
    })

    soil = SOIL_TYPES.get(args.soil.upper(), SOIL_TYPES["C"])
    Sd = soil["Sd"]
    S1 = soil["S1"]
    ag_S = zone * Sd
    res.SDS = round(ag_S * 2.5, 4)
    res.SD1 = round(zone * S1, 4)
    logs.append({
        "Step": 2, "Formula": "S_DS = a_gR × S × 2.5",
        "Substitution": f"S_DS = {zone} × {Sd} × 2.5",
        "Result": f"S_DS = {res.SDS} g"
    })

    res.T_B = soil.get("TB", round(0.05 * S1 / Sd, 3))
    res.T_C = soil.get("TC", round(0.20 * S1 / Sd, 3))
    res.T_D = soil.get("TD", 2.0)
    logs.append({
        "Step": 3,
        "Formula": "Chu kỳ đặc trưng phổ phản ứng TB, TC, TD theo nền đất",
        "Substitution": f"Loại đất {args.soil.upper()} ({soil['type']})",
        "Result": f"TB={res.T_B}s, TC={res.T_C}s, TD={res.T_D}s"
    })

    Ct = 0.075 if args.system.upper() == "MRF" else 0.050 if args.system.upper() in ("WSD", "SW") else 0.075
    res.T = round(estimate_period(Ct, args.height), 3)
    res.T = round(min(res.T, 4.0 * res.T_C, 2.0), 3)
    logs.append({
        "Step": 4,
        "Formula": "T_1 = Ct × H^0.75 (TCVN 9386:2025 §4.3.3.2.2)",
        "Substitution": f"T_1 = {Ct} × {args.height}^0.75",
        "Result": f"T_1 = {res.T} s"
    })

    R = get_behavior_factor(args.system, args.ductility)
    res.R = R
    logs.append({
        "Step": 5,
        "Formula": "q = f(hệ thống kết cấu, cấp độ dẻo)",
        "Substitution": f"q = {R} ({args.system}, {args.ductility})",
        "Result": f"q = {R}"
    })

    res.I = args.importance
    logs.append({
        "Step": 6,
        "Formula": "γ_I = f(cấp hậu quả công trình)",
        "Substitution": f"γ_I = {args.importance}",
        "Result": f"γ_I = {args.importance}"
    })

    # [FIX BUG-STR-08]: Truyền ag_S (chưa nhân 2.5) vào response_spectrum và giữ Cs_calc trong hàm max(...)!
    spec_acc = response_spectrum(ag_S, res.T, res.T_B, res.T_C, res.T_D)
    Cs_calc = (spec_acc / R) * args.importance
    Cs_min = max(0.20 * zone * args.importance, 0.01)
    Cs = max(Cs_calc, Cs_min)
    res.C_s = round(Cs, 4)
    logs.append({
        "Step": 7,
        "Formula": "C_s = max(S_e(T_1) / q × γ_I, 0.20 × a_gR × γ_I)",
        "Substitution": f"S_e(T_1) = {round(spec_acc, 4)} g, q = {R}, γ_I = {args.importance} -> Cs_calc = {Cs_calc:.4f}, Cs_min = {Cs_min:.4f}",
        "Result": f"C_s = {res.C_s}"
    })

    W = args.weight_kn
    V = round(res.C_s * W, 1)
    res.V_base = V
    logs.append({
        "Step": 8,
        "Formula": "F_b = C_s × W",
        "Substitution": f"F_b = {res.C_s} × {W} kN",
        "Result": f"F_b = {V} kN"
    })

    h_avg = args.height / args.floors if args.floors else 4.0
    hi_list = [h_avg * (i + 1) for i in range(args.floors)]
    wi_list = [W / args.floors] * args.floors
    Fi_list = lateral_force_distribution(V, list(zip(wi_list, hi_list)))
    res.FloorForces_kn = [round(f, 1) for f in Fi_list]
    res.F_total = V
    logs.append({
        "Step": 9,
        "Formula": "F_i = F_b × (w_i × z_i / Σ w_j × z_j)",
        "Substitution": f"Floors={args.floors}, H={args.height}m",
        "Result": f"F_b={V}kN"
    })

    story_shears = []
    cumulative = 0.0
    for f in reversed(res.FloorForces_kn):
        cumulative += f
        story_shears.insert(0, round(cumulative, 1))
    res.StoryShears_kn = story_shears
    res.Calculation_Logs = logs
    return res


def main():
    parser = argparse.ArgumentParser(description="Tính tải trọng động đất theo TCVN 9386:2025")
    parser.add_argument("--building", type=str, required=True)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--floors", type=int, required=True)
    parser.add_argument("--zone", type=str, required=True, choices=["IA","IB","II","III","IV","V","VI","VII","VIII"])
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--soil", type=str, default="C", choices=["A","B","C","D","E"])
    parser.add_argument("--importance", type=float, default=1.0)
    parser.add_argument("--system", type=str, default="MRF", choices=["MRF","SMF","OMF","BRB","CBF","WSD","SW","RMIX"])
    parser.add_argument("--ductility", type=str, default="medium", choices=["ductile","medium","普通"])
    parser.add_argument("--weight_kn", type=float, required=True)
    parser.add_argument("--method", type=str, default="RESPONSE_SPECTRUM", choices=["RESPONSE_SPECTRUM","EQUIVALENT_LATERAL"])
    parser.add_argument("--output", type=str)
    args = parser.parse_args()

    result = calc_earthquake(args)
    output = {"Standard_Method": "TCVN 9386:2025", **asdict(result)}
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
