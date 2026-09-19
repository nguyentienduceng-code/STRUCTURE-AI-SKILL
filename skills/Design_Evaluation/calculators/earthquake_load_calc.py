#!/usr/bin/env python3
"""
earthquake_load_calc.py — Tính tải trọng động đất theo TCVN 9386:2025

Chế độ: Thiết kế kháng chấn (Performance-Based / Capacity Design)
Tiêu chuẩn: TCVN 9386:2025 (P1: Thiết kế công trình theo động đất)
             Kết hợp TCVN 9386:2025 P5 (Phương pháp phổ phản ứng)

Usage:
    python earthquake_load_calc.py --building "Nhà chung cư" --height 45 --floors 15 \\
        --location "Ho Chi Minh" --soil C -- Importance 1.0 \\
        --method RESPONSE_SPECTRUM

Output: JSON (stdout)
"""

import argparse
import json
import sys
import math
from dataclasses import dataclass, asdict

# ─── Constants from TCVN 9386:2025 ──────────────────────────────────────────

# Bảng 3-1: Hệ số tầm quan trọng theo QCVN 03:2022
IMPORTANCE_FACTORS = {
    1.0: [("Nhà ở", "Khách sạn", "Văn phòng", "Thương mại")],
    1.2: [("Bệnh viện", "Trường học", "TT hành chính")],
    1.3: [("Công trình công cộng lớn", "TT văn hóa")],
    1.5: [("Công trình nguy hiểm cao")],
}

# Bảng 3-2: Hệ số ứng xử q (hệ số Behavior Factor)
BEHAVIOR_FACTORS = {
    # (hệ thống kết cấu, loại động đất)
    ("MRF", "ductile"): 5.0,          # Khung BTCT chịu mômen, dẻo cao
    ("MRF", "medium"): 3.5,            # Khung BTCT, dẻo trung bình
    ("SMF", "ductile"): 8.0,           # Khung thép dẻo cao
    ("OMF", "medium"): 4.0,            # Khung thép, dẻo trung bình
    ("BRB", "special"): 7.0,           # Hệ giằng chống BRB
    ("CBF", "普通"): 2.0,              # Giằng đồng trục thông thường
    ("WSD", "ductile"): 6.0,          # Tường cắt BTCT dẻo cao
    ("SW", "medium"): 3.0,             # Tường cắt BTCT dẻo trung bình
    ("RMIX", "medium"): 4.5,          # Hệ lai (khung + vách)
}

# Bảng 4-3: Hệ số Lo (Chiều cao tầng)
FLOOR_HEIGHT_FACTOR = {
    3.0: (0.0, 0.4),
    3.5: (0.0, 0.5),
    4.0: (0.0, 0.6),
    5.0: (0.0, 0.8),
}

# Loại đất nền: TCVN 9386:2025 Bảng 3-3
SOIL_TYPES = {
    "A": {"Sd": 1.50, "S1": 1.30, "type": "Đá"},      # Đá
    "B": {"Sd": 1.35, "S1": 1.15, "type": "Đất rắn"}, # Đất rắn
    "C": {"Sd": 1.15, "S1": 1.00, "type": "Đất trung bình"}, # Đất trung bình
    "D": {"Sd": 1.00, "S1": 0.90, "type": "Đất mềm"},  # Đất mềm
    "E": {"Sd": 0.90, "S1": 0.70, "type": "Đất rất mềm"}, # Đất rất mềm
}

# Vùng động đất theo QCVN 02:2022 → SDS, SD1 map
ZONES_PGA = {
    "IA": 0.04,  # Thấp
    "IB": 0.08,
    "II":  0.13,
    "III": 0.20, # Trung bình
    "IV":  0.28,
    "V":   0.36, # Cao
    "VI":  0.45,
    "VII": 0.54,
    "VIII": 0.63,
}

# Vùng gió (nhanh để chuyển sang vùng động đất — ước lượng)
WIND_ZONE_TO_SEISMIC = {
    "II-B": "II",
    "II-A": "II",
    "III-A": "III",
    "III-B": "III",
}

# ─── Core calculation ────────────────────────────────────────────────────────

@dataclass
class EarthquakeResult:
    Standard: str = "TCVN 9386:2025"
    Method: str = "Response Spectrum"
    # Input
    BuildingType: str = ""
    Location: str = ""
    Height_m: float = 0.0
    Floors: int = 0
    SoilType: str = "C"
    ImportanceFactor: float = 1.0
    StructuralSystem: str = "MRF"
    Ductility: str = "medium"
    # Output
    SeismicZone: str = ""
    PGA: float = 0.0      # Peak Ground Acceleration (g)
    SDS: float = 0.0      # Design spectral acceleration at 0.2s
    SD1: float = 0.0     # Design spectral acceleration at 1.0s
    SDs: float = 0.0     # Short-period design spectral
    SD1_calc: float = 0.0 # 1-second period design spectral
    T_B: float = 0.0     # Lower limit of constant spectral accel branch
    T_C: float = 0.0     # Upper limit of constant spectral accel branch
    T_D: float = 0.0     # Beginning of constant displacement branch
    T: float = 0.0        # Fundamental period of vibration
    R: float = 0.0        # Response modification factor
    I: float = 1.0        # Importance factor
    C_s: float = 0.0     # Seismic response coefficient
    V_base: float = 0.0  # Base shear force (kN)
    F_total: float = 0.0 # Total lateral seismic force
    # Per-floor distribution
    FloorForces_kn: list = None
    StoryShears_kn: list = None
    # Metadata
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


def estimate_period(Ta: float, hn: float, Ct: float = 0.0731, x: float = 0.75) -> float:
    """TCVN 9386:2025 §4.5.3.2: T = Ct * hn^x (khung BTCT)"""
    return Ct * (hn ** x)


def response_spectrum(Sa: float, T: float, TB: float, TC: float, TD: float) -> float:
    """Phổ phản ứng gia tốc theo TCVN 9386:2025"""
    if T < 0:
        return 0.0
    if T < TB:
        return Sa * (1 + (2.5 - 1) * T / TB)
    elif T <= TC:
        return Sa * 2.5
    elif T <= TD:
        return Sa * 2.5 * TC / T
    else:
        return Sa * 2.5 * TC * TD / (T ** 2)


def lateral_force_distribution(V: float, wi_hi: list) -> list:
    """Phân bố lực ngang theo chiều cao TCVN 9386:2025 §4.5.3.3"""
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

    # 1. Xác định vùng động đất
    zone = ZONES_PGA.get(args.zone, 0.20)
    res.SeismicZone = args.zone
    res.PGA = round(zone, 3)
    logs.append({
        "Step": 1, "Formula": "PGA = f(vùng động đất)",
        "Substitution": f"PGA = {zone} g (vùng {args.zone})",
        "Result": f"PGA = {zone} g"
    })

    # 2. Hệ số đất nền
    soil = SOIL_TYPES.get(args.soil.upper(), SOIL_TYPES["C"])
    Sd = soil["Sd"]
    S1 = soil["S1"]
    logs.append({
        "Step": 2, "Formula": "SDS = PGA × S × 2.5",
        "Substitution": f"SDS = {zone} × {Sd} × 2.5",
        "Result": f"SDS = {round(zone * Sd * 2.5, 3)} g"
    })
    res.SDS = round(zone * Sd * 2.5, 4)
    res.SD1 = round(zone * S1, 4)

    # 3. Giới hạn chu kỳ (TB, TC, TD)
    res.T_B = round(0.05 * S1 / Sd, 3)
    res.T_C = round(0.20 * S1 / Sd, 3)
    res.T_D = 1.6
    logs.append({
        "Step": 3,
        "Formula": "T_C = 0.20 × S1 / Sd",
        "Substitution": f"T_C = 0.20 × {S1} / {Sd} = {res.T_C} s",
        "Result": f"TB={res.T_B}s, TC={res.T_C}s, TD={res.T_D}s"
    })

    # 4. Chu kỳ dao động cơ bản
    Ct = 0.0731 if args.system.upper() == "MRF" else 0.0488 if args.system.upper() == "WSD" else 0.0731
    res.T = round(estimate_period(Ct, args.height), 3)
    res.T = min(res.T, 1.4 * 1.4 * res.T_C)  # Giới hạn trên
    logs.append({
        "Step": 4,
        "Formula": "T = Ct × hn^0.75 (TCVN 9386:2025 §4.5.3.2)",
        "Substitution": f"T = {Ct} × {args.height}^0.75",
        "Result": f"T = {res.T} s (giới hạn trên)"
    })

    # 5. Hệ số ứng xử R
    R = get_behavior_factor(args.system, args.ductility)
    res.R = R
    logs.append({
        "Step": 5,
        "Formula": "R = f(hệ thống kết cấu, độ dẻo)",
        "Substitution": f"R = {R} ({args.system}, {args.ductility})",
        "Result": f"R = {R}"
    })

    # 6. Hệ số tầm quan trọng
    res.I = args.importance
    logs.append({
        "Step": 6,
        "Formula": "I = f(cấp công trình, QCVN 03:2022)",
        "Substitution": f"I = {args.importance}",
        "Result": f"I = {args.importance}"
    })

    # 7. Hệ số phản ứng động đất Cs
    Sa = res.SDS
    spec_acc = response_spectrum(Sa, res.T, res.T_B, res.T_C, res.T_D)
    Cs_calc = spec_acc / R * args.importance
    # Giới hạn Cs min/max
    Cs = max(0.044 * spec_acc * args.importance, 0.01)  # min
    if args.soil.upper() in ("D", "E"):
        Cs = max(Cs, 0.5 * res.SD1 * args.importance / res.T)
    res.C_s = round(Cs, 4)
    logs.append({
        "Step": 7,
        "Formula": "Cs = Sa(T) / R × I",
        "Substitution": f"Cs = {round(spec_acc,4)} / {R} × {args.importance}",
        "Result": f"Cs = {res.C_s}"
    })

    # 8. Lực cắt đáy
    W = args.weight_kn  # Tổng tải trọng (kN) — cần truyền vào
    V = round(res.C_s * W, 1)
    res.V_base = V
    logs.append({
        "Step": 8,
        "Formula": "V = Cs × W (base shear)",
        "Substitution": f"V = {res.C_s} × {W} kN",
        "Result": f"V = {V} kN"
    })

    # 9. Phân bố lực theo chiều cao
    h_avg = args.height / args.floors if args.floors else 4.0
    hi_list = [h_avg * (i + 1) for i in range(args.floors)]
    wi_list = [W / args.floors] * args.floors  # Giả định phân bố đều
    Fi_list = lateral_force_distribution(V, list(zip(wi_list, hi_list)))
    res.FloorForces_kn = [round(f, 1) for f in Fi_list]
    res.F_total = V
    logs.append({
        "Step": 9,
        "Formula": "Fi = V × (wi×hi / Σwi×hi)",
        "Substitution": f"Floors={args.floors}, H={args.height}m",
        "Result": f"V={V}kN, phân bố: {res.FloorForces_kn}"
    })

    # Story shears (từ dưới lên)
    story_shears = []
    cumulative = 0.0
    for f in reversed(res.FloorForces_kn):
        cumulative += f
        story_shears.insert(0, round(cumulative, 1))
    res.StoryShears_kn = story_shears

    res.Calculation_Logs = logs
    return res


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tính tải trọng động đất theo TCVN 9386:2025",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
    python earthquake_load_calc.py --building "Chung cư 15 tầng" \\
        --height 45 --floors 15 --zone III --location "HCM" \\
        --soil C --importance 1.0 --system MRF --ductility ductile \\
        --weight_kn 90000

Đối với nhà cao tầng ≥ 7 tầng: bắt buộc TCVN 9386:2025 P1 + P5.
        """
    )
    parser.add_argument("--building", type=str, required=True, help="Mô tả công trình")
    parser.add_argument("--height", type=float, required=True, help="Chiều cao (m)")
    parser.add_argument("--floors", type=int, required=True, help="Số tầng")
    parser.add_argument("--zone", type=str, required=True,
                        choices=["IA","IB","II","III","IV","V","VI","VII","VIII"],
                        help="Vùng động đất theo QCVN 02:2022")
    parser.add_argument("--location", type=str, default="", help="Địa điểm")
    parser.add_argument("--soil", type=str, default="C",
                        choices=["A","B","C","D","E"],
                        help="Loại đất nền (TCVN 9386:2025 Bảng 3-3)")
    parser.add_argument("--importance", type=float, default=1.0,
                        help="Hệ số tầm quan trọng I (QCVN 03:2022)")
    parser.add_argument("--system", type=str, default="MRF",
                        choices=["MRF","SMF","OMF","BRB","CBF","WSD","SW","RMIX"],
                        help="Hệ thống kết cấu kháng chấn")
    parser.add_argument("--ductility", type=str, default="medium",
                        choices=["ductile","medium","普通"],
                        help="Cấp độ dẻo")
    parser.add_argument("--weight_kn", type=float, required=True,
                        help="Tổng tải trọng W (kN) = tổng tĩnh tải + một phần hoạt tải")
    parser.add_argument("--method", type=str, default="RESPONSE_SPECTRUM",
                        choices=["RESPONSE_SPECTRUM","EQUIVALENT_LATERAL"],
                        help="Phương pháp tính")
    parser.add_argument("--output", type=str, help="Lưu JSON ra file")
    args = parser.parse_args()

    result = calc_earthquake(args)
    output = {
        "Standard_Method": "TCVN 9386:2025",
        **asdict(result)
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"[I001] Kết quả lưu tại: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
