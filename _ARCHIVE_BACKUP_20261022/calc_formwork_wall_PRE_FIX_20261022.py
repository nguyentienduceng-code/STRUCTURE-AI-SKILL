#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_formwork_wall.py — Thiết kế cốp pha tường (Wall Formwork Design)

Tiêu chuẩn:
- TCVN 4453:1995 - Công tác bê tông và BTCT
- ACI 347-04 - Formwork for Concrete

Hệ thống cốp pha tường:
1. Panel / Sheathing (ván khuôn)
2. Studs / Vertical studs (thanh đứng)
3. Wales / Horizontal runners (thanh ngang)
4. Ties / Through bolts (bu lông xuyên)
5. Braces (thanh chống)

Usage:
    python calc_formwork_wall.py --height 3000 --thickness 200 --grade B30 --rate 1.0
    python calc_formwork_wall.py -h 4000 -t 250 -g B25 -r 2.0 --json
"""

import sys
import json
import math
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, List

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# MATERIAL & STANDARD DATABASE
# ============================================================================

CONCRETE_GRADES = {
    "B15": {"gamma": 24.0, "f_ck": 12.5},
    "B20": {"gamma": 24.0, "f_ck": 16.5},
    "B25": {"gamma": 24.5, "f_ck": 19.0},
    "B30": {"gamma": 25.0, "f_ck": 22.5},
    "B35": {"gamma": 25.0, "f_ck": 26.0},
    "B40": {"gamma": 25.0, "f_ck": 30.0},
}

# Plywood properties
PLYWOOD_TYPES = {
    "15mm": {"t": 15, "E": 9000, "sigma": 10, "weight": 7.5},
    "18mm": {"t": 18, "E": 9000, "sigma": 10, "weight": 9.0},
    "21mm": {"t": 21, "E": 9000, "sigma": 10, "weight": 10.5},
}

# Timber stud properties
TIMBER_STUDS = {
    "50x100": {"b": 0.05, "h": 0.10, "E": 9000, "sigma": 12},
    "50x150": {"b": 0.05, "h": 0.15, "E": 9000, "sigma": 12},
    "80x150": {"b": 0.08, "h": 0.15, "E": 9000, "sigma": 12},
    "80x200": {"b": 0.08, "h": 0.20, "E": 9000, "sigma": 12},
}

# Steel wale properties
STEEL_WALES = {
    "H100x50": {"Ix": 3.56e-6, "Sx": 0.0000712, "W": 9.32},
    "H150x75": {"Ix": 1.68e-5, "Sx": 0.000225, "W": 14.0},
    "H200x100": {"Ix": 4.78e-5, "Sx": 0.000478, "W": 21.3},
}

# Tie rod catalog
TIE_RODS = {
    "TR15": {"d": 15, "A": 177, "capacity": 35, "pitch_min": 300, "pitch_max": 600},
    "TR17": {"d": 17, "A": 227, "capacity": 45, "pitch_min": 300, "pitch_max": 750},
    "TR20": {"d": 20, "A": 314, "capacity": 65, "pitch_min": 400, "pitch_max": 900},
    "TR22": {"d": 22, "A": 380, "capacity": 80, "pitch_min": 400, "pitch_max": 1000},
}

SAFETY_FACTORS = {
    "load_DL": 1.2,
    "load_LL": 1.5,
    "material_steel": 1.1,
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class WallFormworkResult:
    """Kết quả thiết kế cốp pha tường"""

    # Input
    wall_height: float        # mm
    wall_thickness: float    # mm
    concrete_grade: str
    pour_rate: float         # m/h
    concrete_temp: float     # °C

    # Pressure calculation
    max_lateral_pressure: float
    pressure_formula: str

    # Panel design
    panel_thickness: int
    stud_spacing: float      # m
    panel_stress: float      # MPa
    panel_deflection: float   # mm
    eta_panel: float

    # Stud design
    stud_type: str
    stud_span: float         # m
    wale_spacing: float      # m
    stud_stress: float       # MPa
    eta_stud: float

    # Wale design
    wale_type: str
    wale_span: float         # m (between tie rods)
    tie_spacing: float       # m
    wale_stress: float       # MPa
    eta_wale: float

    # Tie rod design
    tie_rod_type: str
    tie_rod_capacity: float
    tie_force: float
    eta_tie: float

    # Summary
    all_pass: bool
    warnings: List[str]
    recommendations: List[str]

    standard_method: str = "ACI 347-04 / TCVN 4453:1995"
    calculation_logs: List[Dict] = None

    def __post_init__(self):
        if self.calculation_logs is None:
            self.calculation_logs = []

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# CORE CALCULATIONS
# ============================================================================

class WallFormworkDesigner:
    """Thiết kế cốp pha tường"""

    def __init__(self, wall_height: float, wall_thickness: float,
                 concrete_grade: str = "B30", pour_rate: float = 1.0,
                 concrete_temp: float = 25.0):
        self.wall_height = wall_height
        self.wall_thickness = wall_thickness
        self.concrete_grade = concrete_grade
        self.pour_rate = pour_rate
        self.concrete_temp = concrete_temp
        self.logs = []

        if concrete_grade not in CONCRETE_GRADES:
            raise ValueError(f"Unknown concrete grade: {concrete_grade}")

    def _log(self, step, formula, substitution, result, unit, citation=""):
        self.logs.append({
            "step": step,
            "formula": formula,
            "substitution": substitution,
            "result": round(float(result), 4),
            "unit": unit,
            "citation": citation
        })

    def calculate_pressure(self) -> Dict:
        """Tính áp lực ngang tường"""
        step = 1
        gamma_c = CONCRETE_GRADES[self.concrete_grade]["gamma"]
        H = min(self.wall_height / 1000, 2.0)

        if self.pour_rate < 2.0:
            C_v = 1.0
        else:
            C_v = 1.5

        w = self.wall_thickness / 1000
        if w >= 0.1:
            C_w = 1.0
        else:
            C_w = 1.0 + 0.7 * (0.1 - w) / 0.1

        P_h = gamma_c * H
        P_v = C_v * self.pour_rate / self.concrete_temp
        P_max = P_h + P_v

        self._log(step, "P_max",
                  f"{gamma_c}×{H:.2f} + {C_v}×{self.pour_rate}/{self.concrete_temp}", P_max, "kN/m²", "ACI 347-04")

        return {
            "P_h": P_h,
            "P_v": P_v,
            "P_max": P_max,
            "C_v": C_v,
            "C_w": C_w,
            "gamma_c": gamma_c,
            "H": H
        }

    def design_panel(self, P_max: float) -> Dict:
        """Thiết kế panel (ván khuôn)"""
        step = 10

        ply = PLYWOOD_TYPES["18mm"]
        t = ply["t"]
        E = ply["E"] * 1e6
        sigma_allow = ply["sigma"] * 1e6
        I = t**3 / 12 * 1e-12
        Z = t**2 / 6 * 1e-6

        q = P_max

        # Span = stud spacing
        L = 0.5
        for _ in range(50):
            delta = 5 * (q * 1000) * L**4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 270:
                break
            L *= 0.95
        L = round(L, 2)

        M = q * L**2 / 8
        sigma = (M * 1000) / Z / 1e6
        delta_actual = 5 * (q * 1000) * L**4 / (384 * E * I) * 1000

        eta = max(sigma / (sigma_allow/1e6), delta_actual / (L*1000/270))

        self._log(step, "Panel span",
                  f"L = {L:.2f} m", L, "m", "ACI 347-04")

        return {
            "thickness": t,
            "span": L,
            "moment": M,
            "stress": sigma,
            "deflection": delta_actual,
            "deflection_allow": L * 1000 / 270,
            "eta": eta
        }

    def design_stud(self, P_max: float, stud_span: float) -> Dict:
        """Thiết kế studs (thanh đứng)"""
        step = 20

        # Timber 50x100mm
        stud = TIMBER_STUDS["50x100"]
        E = stud["E"] * 1e6
        b = stud["b"]
        h = stud["h"]
        I = b * h**3 / 12
        Z = b * h**2 / 6

        # Load = P_max × panel span
        q = P_max * stud_span

        # Span = wale spacing
        L = 1.0
        for _ in range(50):
            delta = 5 * q * 1000 * L**4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 360:
                break
            L *= 0.95
        L = round(L, 2)

        M = q * L**2 / 8
        sigma = M / Z / 1e6
        delta_actual = 5 * q * 1000 * L**4 / (384 * E * I) * 1000

        eta = max(sigma / stud["sigma"], delta_actual / (L*1000/360))

        self._log(step, "Stud span",
                  f"L = {L:.2f} m", L, "m", "TCVN 4453")

        return {
            "type": "50x100mm",
            "span": L,
            "load": q,
            "moment": M,
            "stress": sigma,
            "deflection": delta_actual,
            "deflection_allow": L * 1000 / 360,
            "eta": eta
        }

    def design_wale(self, P_max: float, wale_span: float) -> Dict:
        """Thiết kế wale (thanh ngang)"""
        step = 30

        # H150x75
        wale = STEEL_WALES["H150x75"]
        E = 210e9
        I = wale["Ix"]
        Z = wale["Sx"]

        # Load = P_max × wale span
        q = P_max * wale_span

        L = 1.2
        for _ in range(50):
            delta = 5 * q * 1000 * L**4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 400:
                break
            L *= 0.95
        L = round(L, 2)

        M = q * L**2 / 8
        sigma = M / Z / 1e6
        delta_actual = 5 * q * 1000 * L**4 / (384 * E * I) * 1000

        eta = max(sigma / 210, delta_actual / (L*1000/400))

        self._log(step, "Wale span",
                  f"L = {L:.2f} m", L, "m", "ACI 347-04")

        return {
            "type": "H150x75",
            "span": L,
            "load": q,
            "moment": M,
            "stress": sigma,
            "deflection": delta_actual,
            "deflection_allow": L * 1000 / 400,
            "eta": eta
        }

    def design_tie(self, P_max: float, tie_span: float) -> Dict:
        """Thiết kế tie rod (bu lông xuyên)"""
        step = 40

        # Lực kéo = P_max × spacing ngang × spacing dọc / 2
        F = P_max * tie_span * tie_span / 2

        self._log(step, "Tie rod force",
                  f"{P_max:.2f} × {tie_span:.2f}² / 2", F, "kN", "TCVN 4453:1995")

        # Chọn tie rod
        selected = None
        for name, rod in TIE_RODS.items():
            if F <= rod["capacity"] / SAFETY_FACTORS["material_steel"]:
                selected = (name, rod)
                break

        if selected is None:
            selected = ("TR22", TIE_RODS["TR22"])

        name, rod = selected
        eta = F / (rod["capacity"] / SAFETY_FACTORS["material_steel"])

        return {
            "type": name,
            "diameter": rod["d"],
            "capacity": rod["capacity"] / SAFETY_FACTORS["material_steel"],
            "force": F,
            "spacing": tie_span,
            "eta": eta
        }

    def design(self) -> WallFormworkResult:
        """Chạy thiết kế hoàn chỉnh"""

        # 1. Tính áp lực
        pressure = self.calculate_pressure()
        P_max = pressure["P_max"]

        # 2. Panel
        panel = self.design_panel(P_max)

        # 3. Stud
        stud = self.design_stud(P_max, panel["span"])

        # 4. Wale
        wale = self.design_wale(P_max, stud["span"])

        # 5. Tie rod
        tie = self.design_tie(P_max, wale["span"])

        # Compile
        warnings = []
        recommendations = []

        all_eta = [
            ("Panel", panel["eta"]),
            ("Stud", stud["eta"]),
            ("Wale", wale["eta"]),
            ("Tie Rod", tie["eta"])
        ]

        all_pass = True
        for name, eta in all_eta:
            if eta > 1.0:
                warnings.append(f"{name}: η = {eta:.3f} > 1.0 — FAIL")
                all_pass = False
            elif eta > 0.9:
                warnings.append(f"{name}: η = {eta:.3f} > 0.9 — Sát ngưỡng")
            elif eta <= 0.7:
                recommendations.append(f"{name}: η = {eta:.3f} ≤ 0.7 — Có thể tối ưu")

        if all_pass:
            recommendations.append("Thiết kế đạt yêu cầu")

        if self.pour_rate > 2.0:
            warnings.append(f"Tốc độ đổ {self.pour_rate} m/h cao — theo dõi áp lực")

        return WallFormworkResult(
            wall_height=self.wall_height,
            wall_thickness=self.wall_thickness,
            concrete_grade=self.concrete_grade,
            pour_rate=self.pour_rate,
            concrete_temp=self.concrete_temp,
            max_lateral_pressure=P_max,
            pressure_formula="P_max = γ_c×H + C_v×V/t",
            panel_thickness=panel["thickness"],
            stud_spacing=panel["span"],
            panel_stress=panel["stress"],
            panel_deflection=panel["deflection"],
            eta_panel=panel["eta"],
            stud_type=stud["type"],
            stud_span=stud["span"],
            wale_spacing=stud["span"],
            stud_stress=stud["stress"],
            eta_stud=stud["eta"],
            wale_type=wale["type"],
            wale_span=wale["span"],
            tie_spacing=wale["span"],
            wale_stress=wale["stress"],
            eta_wale=wale["eta"],
            tie_rod_type=tie["type"],
            tie_rod_capacity=tie["capacity"],
            tie_force=tie["force"],
            eta_tie=tie["eta"],
            all_pass=all_pass,
            warnings=warnings,
            recommendations=recommendations,
            standard_method="ACI 347-04 / TCVN 4453:1995",
            calculation_logs=self.logs
        )


# ============================================================================
# CLI
# ============================================================================

def print_result(result: WallFormworkResult):
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ORANGE = "\033[38;5;214m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{'=' * 70}")
    print(f"{BOLD}THIẾT KẾ CỐP PHA TƯỜNG{RESET}")
    print(f"{'─' * 70}")

    status_color = GREEN if result.all_pass else RED
    status_text = "✅ ĐẠT YÊU CẦU" if result.all_pass else "❌ KHÔNG ĐẠT"
    print(f"\nTrạng thái: {status_color}{status_text}{RESET}")
    print(f"Tiêu chuẩn: {result.standard_method}")

    print(f"\n{BOLD}📥 ĐẦU VÀO:{RESET}")
    print(f"  Chiều cao tường: {result.wall_height} mm")
    print(f"  Bề dày tường: {result.wall_thickness} mm")
    print(f"  Mác bê tông: {result.concrete_grade}")
    print(f"  Tốc độ đổ: {result.pour_rate} m/h")

    print(f"\n{BOLD}📊 ÁP LỰC NGANG:{RESET}")
    print(f"  P_max = {result.max_lateral_pressure:.2f} kN/m²")

    def print_eta(name, eta):
        c = GREEN if eta <= 0.7 else (YELLOW if eta <= 0.9 else (ORANGE if eta <= 1.0 else RED))
        return f"  {c}η = {eta:.3f}{RESET}"

    print(f"\n{BOLD}📐 PANEL:{RESET}")
    print(f"  Chiều dày: {result.panel_thickness}mm")
    print(f"  Cự ly stud: {result.stud_spacing:.2f} m")
    print(f"  Ứng suất: {result.panel_stress:.3f} MPa")
    print(print_eta("Panel", result.eta_panel))

    print(f"\n{BOLD}📐 STUDS:{RESET}")
    print(f"  Loại: {result.stud_type}")
    print(f"  Cự ly wale: {result.stud_span:.2f} m")
    print(f"  Ứng suất: {result.stud_stress:.3f} MPa")
    print(print_eta("Stud", result.eta_stud))

    print(f"\n{BOLD}📐 WALES:{RESET}")
    print(f"  Loại: {result.wale_type}")
    print(f"  Cự ly tie: {result.wale_span:.2f} m")
    print(f"  Ứng suất: {result.wale_stress:.3f} MPa")
    print(print_eta("Wale", result.eta_wale))

    print(f"\n{BOLD}🔩 TIE RODS:{RESET}")
    print(f"  Loại: {result.tie_rod_type}")
    print(f"  Cự ly: {result.tie_spacing:.2f} m")
    print(f"  Lực kéo: {result.tie_force:.2f} kN")
    print(f"  Công suất: {result.tie_rod_capacity:.1f} kN")
    print(print_eta("Tie", result.eta_tie))

    if result.warnings:
        print(f"\n{BOLD}⚠️ CẢNH BÁO:{RESET}")
        for w in result.warnings:
            print(f"  • {w}")

    if result.recommendations:
        print(f"\n{BOLD}💡 KHUYẾN NGHỊ:{RESET}")
        for r in result.recommendations:
            print(f"  • {r}")

    print(f"\n{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(description="Thiết kế cốp pha tường")
    parser.add_argument("--height", "-H", type=float, required=True, help="Chiều cao tường (mm)")
    parser.add_argument("--thickness", "-t", type=float, required=True, help="Bề dày tường (mm)")
    parser.add_argument("--grade", "-g", default="B30", help="Mác bê tông")
    parser.add_argument("--rate", "-r", type=float, default=1.0, help="Tốc độ đổ (m/h)")
    parser.add_argument("--temp", "-T", type=float, default=25.0, help="Nhiệt độ bê tông (°C)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    designer = WallFormworkDesigner(
        wall_height=args.height,
        wall_thickness=args.thickness,
        concrete_grade=args.grade.upper(),
        pour_rate=args.rate,
        concrete_temp=args.temp
    )
    result = designer.design()

    if args.json or args.output:
        json_str = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"✓ Kết quả lưu: {args.output}")
        if args.json:
            print(json_str)
    else:
        print_result(result)


if __name__ == "__main__":
    main()
