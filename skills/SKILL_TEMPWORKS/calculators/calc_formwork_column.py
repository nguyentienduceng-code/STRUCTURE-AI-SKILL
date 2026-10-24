#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_formwork_column.py — Thiết kế cốp pha cột (Column Formwork Design)
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
    "B15": {"gamma": 24.0, "f_ck": 12.5, "Ec": 24000, "temp_range": (5, 35)},
    "B20": {"gamma": 24.0, "f_ck": 16.5, "Ec": 27500, "temp_range": (5, 35)},
    "B25": {"gamma": 24.5, "f_ck": 19.0, "Ec": 30000, "temp_range": (5, 35)},
    "B30": {"gamma": 25.0, "f_ck": 22.5, "Ec": 32500, "temp_range": (5, 35)},
    "B35": {"gamma": 25.0, "f_ck": 26.0, "Ec": 34500, "temp_range": (5, 35)},
    "B40": {"gamma": 25.0, "f_ck": 30.0, "Ec": 36000, "temp_range": (5, 35)},
}

PLYWOOD_TYPES = {
    "15mm": {"t": 15, "E": 9000, "sigma": 10, "weight": 7.5},
    "18mm": {"t": 18, "E": 9000, "sigma": 10, "weight": 9.0},
    "21mm": {"t": 21, "E": 9000, "sigma": 10, "weight": 10.5},
}

TIE_RODS = {
    "TR15": {"d": 15, "A": 177, "capacity": 35, "pitch_min": 300, "pitch_max": 600},
    "TR17": {"d": 17, "A": 227, "capacity": 45, "pitch_min": 300, "pitch_max": 750},
    "TR20": {"d": 20, "A": 314, "capacity": 65, "pitch_min": 400, "pitch_max": 900},
    "TR22": {"d": 22, "A": 380, "capacity": 80, "pitch_min": 400, "pitch_max": 1000},
}

YOKE_BEAMS = {
    "H100x50": {"Ix": 3.56e-6, "Sx": 0.0000712, "W": 9.32, "h": 100, "bf": 50},
    "H150x75": {"Ix": 1.68e-5, "Sx": 0.000225, "W": 14.0, "h": 150, "bf": 75},
}

SAFETY_FACTORS = {
    "load_DL": 1.2,
    "load_LL": 1.5,
    "material_concrete": 1.5,
    "material_steel": 1.1,
    "stability": 2.0,
}


@dataclass
class ColumnFormworkResult:
    column_width: float
    column_height: float
    concrete_grade: str
    pour_rate: float
    concrete_temp: float
    max_lateral_pressure: float
    pressure_formula: str
    pressure_citation: str
    panel_thickness: int
    panel_spacing: float
    panel_stress: float
    panel_deflection: float
    eta_panel: float
    yoke_type: str
    yoke_spacing: float
    yoke_moment: float
    yoke_stress: float
    eta_yoke: float
    tie_rod_type: str
    tie_rod_capacity: float
    tie_rod_spacing: float
    tie_rod_force: float
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
        # [FIX BUG-STR-07b]: Bổ sung Calculation_Logs và Standard_Method ở root theo AGENTS.md §5
        d["Calculation_Logs"] = self.calculation_logs or []
        d["Standard_Method"] = self.standard_method
        return d


class ColumnFormworkDesigner:
    def __init__(self, column_width: float, column_height: float,
                 concrete_grade: str = "B30", pour_rate: float = 1.0,
                 concrete_temp: float = 25.0):
        self.column_width = column_width
        self.column_height = column_height
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

    def calculate_lateral_pressure(self) -> Dict[str, float]:
        """
        [FIX BUG-STR-07b]: Tính áp lực ngang tối đa của bê tông tươi lên cốp pha cột theo đúng ACI 347-04 Eq. (2.2):
          p_ACI = C_w * C_c * [7.2 + 785 * R / (T + 17.8)]  (kPa)
          Giới hạn: 30 * C_w <= p_max <= min(γ_c * H, 150 * C_w * C_c) (kPa)
        """
        step = 1
        gamma_c = CONCRETE_GRADES[self.concrete_grade]["gamma"]
        H_m = self.column_height / 1000.0 if self.column_height > 50.0 else self.column_height
        C_w = 1.0
        C_c = 1.0

        P_hydro = gamma_c * H_m
        self._log(step, "P_hydro = γ_c × H", f"{gamma_c} × {H_m:.2f}", P_hydro, "kN/m²", "TCVN 4453:1995")
        step += 1

        P_aci = C_w * C_c * (7.2 + (785.0 * self.pour_rate) / (self.concrete_temp + 17.8))
        self._log(step, "P_ACI = C_w × C_c × [7.2 + 785×R/(T + 17.8)]",
                  f"1.0 × 1.0 × [7.2 + 785×{self.pour_rate}/({self.concrete_temp} + 17.8)]", P_aci, "kN/m²", "ACI 347-04 Eq. (2.2)")
        step += 1

        P_max = min(P_hydro, max(30.0 * C_w, min(P_aci, 150.0 * C_w * C_c)))
        self._log(step, "P_max = min(γ_c×H, max(30×C_w, P_ACI))",
                  f"min({P_hydro:.2f}, max(30.0, {P_aci:.2f}))", P_max, "kN/m²", "ACI 347-04 / TCVN 4453:1995")

        return {
            "P_h": P_hydro, "P_v": P_aci, "P_w": 0.0, "P_max": P_max,
            "C_v": C_c, "C_w": C_w, "gamma_c": gamma_c, "H": H_m
        }

    def design_panel(self, P_max: float) -> Dict:
        step = 10
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

        self._log(step, "Panel bending moment", f"{q:.2f} × {L:.2f}² / 8", M, "kNm", "TCVN 4453")
        return {
            "thickness": t, "span": L, "moment": M, "stress": sigma,
            "deflection": delta_actual, "deflection_allow": L * 1000 / 270, "eta": eta
        }

    def design_yoke(self, P_max: float, panel_span: float) -> Dict:
        step = 20
        yoke = YOKE_BEAMS["H150x75"]
        E = 210e9
        I = yoke["Ix"]
        Z = yoke["Sx"]
        q = P_max * panel_span

        L = 0.8
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

        self._log(step, "Yoke load", f"{P_max:.2f} × {panel_span:.2f}", q, "kN/m", "TCVN 4453")
        return {
            "type": "H150x75", "span": L, "load": q, "moment": M,
            "stress": sigma, "deflection": delta_actual, "deflection_allow": L * 1000 / 400, "eta": eta
        }

    def design_tie_rod(self, P_max: float, yoke_span: float) -> Dict:
        step = 30
        tie_spacing = 0.5
        F = P_max * tie_spacing * yoke_span / 2
        self._log(step, "Tie rod force", f"{P_max:.2f} × {tie_spacing:.2f} × {yoke_span:.2f} / 2", F, "kN", "TCVN 4453:1995")

        selected_rod = None
        for name, rod in TIE_RODS.items():
            if F <= rod["capacity"] / SAFETY_FACTORS["material_steel"]:
                selected_rod = (name, rod)
                break
        if selected_rod is None:
            selected_rod = ("TR22", TIE_RODS["TR22"])
        name, rod = selected_rod
        eta = F / (rod["capacity"] / SAFETY_FACTORS["material_steel"])
        return {
            "type": name, "diameter": rod["d"], "area": rod["A"],
            "capacity": rod["capacity"] / SAFETY_FACTORS["material_steel"],
            "force": F, "spacing": tie_spacing, "eta": eta
        }

    def design(self) -> ColumnFormworkResult:
        pressure = self.calculate_lateral_pressure()
        P_max = pressure["P_max"]
        panel = self.design_panel(P_max)
        yoke = self.design_yoke(P_max, panel["span"])
        tie = self.design_tie_rod(P_max, yoke["span"])

        warnings = []
        recommendations = []
        all_eta = [("Panel", panel["eta"]), ("Yoke", yoke["eta"]), ("Tie Rod", tie["eta"])]
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

        return ColumnFormworkResult(
            column_width=self.column_width,
            column_height=self.column_height,
            concrete_grade=self.concrete_grade,
            pour_rate=self.pour_rate,
            concrete_temp=self.concrete_temp,
            max_lateral_pressure=round(P_max, 2),
            pressure_formula="P_max = min(γ_c×H, max(30×C_w, C_w×C_c×[7.2 + 785×R/(T+17.8)]))",
            pressure_citation="ACI 347-04 Eq. (2.2) / TCVN 4453:1995",
            panel_thickness=panel["thickness"],
            panel_spacing=panel["span"],
            panel_stress=round(panel["stress"], 3),
            panel_deflection=round(panel["deflection"], 3),
            eta_panel=round(panel["eta"], 3),
            yoke_type=yoke["type"],
            yoke_spacing=yoke["span"],
            yoke_moment=round(yoke["moment"], 4),
            yoke_stress=round(yoke["stress"], 3),
            eta_yoke=round(yoke["eta"], 3),
            tie_rod_type=tie["type"],
            tie_rod_capacity=round(tie["capacity"], 2),
            tie_rod_spacing=tie["spacing"],
            tie_rod_force=round(tie["force"], 2),
            eta_tie=round(tie["eta"], 3),
            all_pass=all_pass,
            warnings=warnings,
            recommendations=recommendations,
            standard_method="ACI 347-04 / TCVN 4453:1995",
            calculation_logs=self.logs
        )


def main():
    parser = argparse.ArgumentParser(description="Thiết kế cốp pha cột")
    parser.add_argument("--width", "-w", type=float, required=True)
    parser.add_argument("--depth", "-d", type=float, default=None)
    parser.add_argument("--height", "-H", type=float, required=True)
    parser.add_argument("--grade", "-g", default="B30")
    parser.add_argument("--rate", "-r", type=float, default=1.0)
    parser.add_argument("--temp", "-T", type=float, default=25.0)
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--output", "-o")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    designer = ColumnFormworkDesigner(
        column_width=args.width, column_height=args.height,
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
