#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_formwork_wall.py — Thiết kế cốp pha tường (Wall Formwork Design)
Tiêu chuẩn: TCVN 4453:1995 & ACI 347-04
"""

import sys
import json
import math
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, List

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CONCRETE_GRADES = {
    "B15": {"gamma": 24.0, "f_ck": 12.5},
    "B20": {"gamma": 24.0, "f_ck": 16.5},
    "B25": {"gamma": 24.5, "f_ck": 19.0},
    "B30": {"gamma": 25.0, "f_ck": 22.5},
    "B35": {"gamma": 25.0, "f_ck": 26.0},
    "B40": {"gamma": 25.0, "f_ck": 30.0},
}

PLYWOOD_TYPES = {
    "15mm": {"t": 15, "E": 9000, "sigma": 10, "weight": 7.5},
    "18mm": {"t": 18, "E": 9000, "sigma": 10, "weight": 9.0},
    "21mm": {"t": 21, "E": 9000, "sigma": 10, "weight": 10.5},
}

TIMBER_STUDS = {
    "50x100": {"b": 0.05, "h": 0.10, "E": 9000, "sigma": 12},
    "50x150": {"b": 0.05, "h": 0.15, "E": 9000, "sigma": 12},
    "80x150": {"b": 0.08, "h": 0.15, "E": 9000, "sigma": 12},
    "80x200": {"b": 0.08, "h": 0.20, "E": 9000, "sigma": 12},
}

STEEL_WALES = {
    "H100x50": {"Ix": 3.56e-6, "Sx": 0.0000712, "W": 9.32},
    "H150x75": {"Ix": 1.68e-5, "Sx": 0.000225, "W": 14.0},
    "H200x100": {"Ix": 4.78e-5, "Sx": 0.000478, "W": 21.3},
}

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


@dataclass
class WallFormworkResult:
    wall_height: float
    wall_thickness: float
    concrete_grade: str
    pour_rate: float
    concrete_temp: float
    max_lateral_pressure: float
    pressure_formula: str
    panel_thickness: int
    stud_spacing: float
    panel_stress: float
    panel_deflection: float
    eta_panel: float
    stud_type: str
    stud_span: float
    wale_spacing: float
    stud_stress: float
    eta_stud: float
    wale_type: str
    wale_span: float
    tie_spacing: float
    wale_stress: float
    eta_wale: float
    tie_rod_type: str
    tie_rod_capacity: float
    tie_force: float
    eta_tie: float
    all_pass: bool
    warnings: List[str]
    recommendations: List[str]
    standard_method: str = "ACI 347-04 / TCVN 4453:1995"
    calculation_logs: List[Dict] = None

    def __post_init__(self):
        if self.calculation_logs is None:
            self.calculation_logs = []

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["Calculation_Logs"] = self.calculation_logs or []
        d["Standard_Method"] = self.standard_method
        return d


class WallFormworkDesigner:
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
            "step": step, "formula": formula, "substitution": substitution,
            "result": round(float(result), 4), "unit": unit, "citation": citation
        })

    def calculate_pressure(self) -> Dict:
        """
        [FIX BUG-STR-07b]: Áp lực ngang của bê tông tươi lên cốp pha tường theo ACI 347-04 Eq. (2.3a/2.3b):
          - Khi R < 2.1 m/h và H <= 4.2m: P_aci = C_w * C_c * [7.2 + 785 * R / (T + 17.8)]
          - Khi R >= 2.1 m/h (hoặc H > 4.2m): P_aci = C_w * C_c * [7.2 + 1156 / (T + 17.8) + 244 * R / (T + 17.8)]
          Giới hạn: 30 * C_w <= P_max <= min(γ_c * H, 100 * C_w * C_c) (kPa).
        """
        step = 1
        gamma_c = CONCRETE_GRADES[self.concrete_grade]["gamma"]
        H_m = self.wall_height / 1000.0 if self.wall_height > 50.0 else self.wall_height
        C_w = 1.0
        C_c = 1.0
        P_hydro = gamma_c * H_m

        if self.pour_rate < 2.1 and H_m <= 4.2:
            P_aci = C_w * C_c * (7.2 + (785.0 * self.pour_rate) / (self.concrete_temp + 17.8))
        else:
            P_aci = C_w * C_c * (7.2 + (1156.0 + 244.0 * self.pour_rate) / (self.concrete_temp + 17.8))

        P_max = min(P_hydro, max(30.0 * C_w, min(P_aci, 100.0 * C_w * C_c)))
        self._log(step, "P_max = min(γ_c×H, max(30×C_w, P_ACI_wall))",
                  f"min({P_hydro:.2f}, max(30.0, {P_aci:.2f}))", P_max, "kN/m²", "ACI 347-04 Eq. (2.3)")

        return {"P_h": P_hydro, "P_v": P_aci, "P_max": P_max, "C_v": C_c, "C_w": C_w, "gamma_c": gamma_c, "H": H_m}

    def design_panel(self, P_max: float) -> Dict:
        ply = PLYWOOD_TYPES["18mm"]
        t = ply["t"]
        E = ply["E"] * 1e6
        sigma_allow = ply["sigma"] * 1e6
        I = 1.0 * (t / 1000.0) ** 3 / 12  # m⁴ cho dải 1m bề rộng
        Z = t ** 2 / 6 * 1e-6
        q = P_max

        L = 0.5
        for _ in range(50):
            delta = 5 * (q * 1000) * L ** 4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 270:
                break
            L *= 0.95
        L = round(L, 2)
        M = q * L ** 2 / 8
        sigma = (M * 1000) / Z / 1e6
        delta_actual = 5 * (q * 1000) * L ** 4 / (384 * E * I) * 1000
        eta = max(sigma / (sigma_allow / 1e6), delta_actual / (L * 1000 / 270))
        self._log(10, "Panel span", f"L = {L:.2f} m", L, "m", "ACI 347-04")
        return {"thickness": t, "span": L, "moment": M, "stress": sigma, "deflection": delta_actual, "eta": eta}

    def design_stud(self, P_max: float, stud_span: float) -> Dict:
        stud = TIMBER_STUDS["50x100"]
        E = stud["E"] * 1e6
        b, h = stud["b"], stud["h"]
        I = b * h ** 3 / 12
        Z = b * h ** 2 / 6
        q = P_max * stud_span

        L = 1.0
        for _ in range(50):
            delta = 5 * q * 1000 * L ** 4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 360:
                break
            L *= 0.95
        L = round(L, 2)
        M = q * L ** 2 / 8
        sigma = (M * 1000.0) / Z / 1e6
        delta_actual = 5 * q * 1000 * L ** 4 / (384 * E * I) * 1000
        eta = max(sigma / stud["sigma"], delta_actual / (L * 1000 / 360))
        self._log(20, "Stud span", f"L = {L:.2f} m", L, "m", "TCVN 4453")
        return {"type": "50x100mm", "span": L, "load": q, "moment": M, "stress": sigma, "deflection": delta_actual, "eta": eta}

    def design_wale(self, P_max: float, wale_span: float) -> Dict:
        wale = STEEL_WALES["H150x75"]
        E = 210e9
        I, Z = wale["Ix"], wale["Sx"]
        q = P_max * wale_span

        L = 1.2
        for _ in range(50):
            delta = 5 * q * 1000 * L ** 4 / (384 * E * I) * 1000
            if delta <= L * 1000 / 400:
                break
            L *= 0.95
        L = round(L, 2)
        M = q * L ** 2 / 8
        sigma = (M * 1000.0) / Z / 1e6
        delta_actual = 5 * q * 1000 * L ** 4 / (384 * E * I) * 1000
        eta = max(sigma / 210, delta_actual / (L * 1000 / 400))
        self._log(30, "Wale span", f"L = {L:.2f} m", L, "m", "ACI 347-04")
        return {"type": "H150x75", "span": L, "load": q, "moment": M, "stress": sigma, "deflection": delta_actual, "eta": eta}

    def design_tie(self, P_max: float, tie_span: float) -> Dict:
        F = P_max * tie_span * tie_span / 2
        self._log(40, "Tie rod force", f"{P_max:.2f} × {tie_span:.2f}² / 2", F, "kN", "TCVN 4453:1995")
        selected = None
        for name, rod in TIE_RODS.items():
            if F <= rod["capacity"] / SAFETY_FACTORS["material_steel"]:
                selected = (name, rod)
                break
        if selected is None:
            selected = ("TR22", TIE_RODS["TR22"])
        name, rod = selected
        eta = F / (rod["capacity"] / SAFETY_FACTORS["material_steel"])
        return {"type": name, "diameter": rod["d"], "capacity": rod["capacity"] / SAFETY_FACTORS["material_steel"], "force": F, "spacing": tie_span, "eta": eta}

    def design(self) -> WallFormworkResult:
        pressure = self.calculate_pressure()
        P_max = pressure["P_max"]
        panel = self.design_panel(P_max)
        stud = self.design_stud(P_max, panel["span"])
        wale = self.design_wale(P_max, stud["span"])
        tie = self.design_tie(P_max, wale["span"])

        warnings, recommendations = [], []
        all_eta = [("Panel", panel["eta"]), ("Stud", stud["eta"]), ("Wale", wale["eta"]), ("Tie Rod", tie["eta"])]
        all_pass = True
        for name, eta in all_eta:
            if eta > 1.0:
                warnings.append(f"{name}: η = {eta:.3f} > 1.0 — FAIL")
                all_pass = False
            elif eta > 0.9:
                warnings.append(f"{name}: η = {eta:.3f} > 0.9 — Sát ngưỡng")
        if all_pass:
            recommendations.append("Thiết kế đạt yêu cầu")

        return WallFormworkResult(
            wall_height=self.wall_height, wall_thickness=self.wall_thickness,
            concrete_grade=self.concrete_grade, pour_rate=self.pour_rate, concrete_temp=self.concrete_temp,
            max_lateral_pressure=round(P_max, 2),
            pressure_formula="P_max = min(γ_c×H, max(30×C_w, P_ACI_wall))",
            panel_thickness=panel["thickness"], stud_spacing=panel["span"],
            panel_stress=round(panel["stress"], 3), panel_deflection=round(panel["deflection"], 3), eta_panel=round(panel["eta"], 3),
            stud_type=stud["type"], stud_span=stud["span"], wale_spacing=stud["span"],
            stud_stress=round(stud["stress"], 3), eta_stud=round(stud["eta"], 3),
            wale_type=wale["type"], wale_span=wale["span"], tie_spacing=wale["span"],
            wale_stress=round(wale["stress"], 3), eta_wale=round(wale["eta"], 3),
            tie_rod_type=tie["type"], tie_rod_capacity=round(tie["capacity"], 2),
            tie_force=round(tie["force"], 2), eta_tie=round(tie["eta"], 3),
            all_pass=all_pass, warnings=warnings, recommendations=recommendations,
            standard_method="ACI 347-04 / TCVN 4453:1995", calculation_logs=self.logs
        )


def main():
    parser = argparse.ArgumentParser(description="Thiết kế cốp pha tường")
    parser.add_argument("--height", "-H", type=float, required=True)
    parser.add_argument("--length", "-l", type=float, default=6.0)
    parser.add_argument("--thickness", "-t", type=float, required=True)
    parser.add_argument("--grade", "-g", default="B30")
    parser.add_argument("--rate", "-r", type=float, default=1.0)
    parser.add_argument("--temp", "-T", type=float, default=25.0)
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    designer = WallFormworkDesigner(
        wall_height=args.height, wall_thickness=args.thickness,
        concrete_grade=args.grade.upper(), pour_rate=args.rate, concrete_temp=args.temp
    )
    result = designer.design()
    json_str = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
    print(json_str)


if __name__ == "__main__":
    main()
