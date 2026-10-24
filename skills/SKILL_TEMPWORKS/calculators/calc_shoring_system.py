#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_shoring_system.py — Thiết kế hệ thống cây chống (Shoring System Design)
Tiêu chuẩn: TCVN 4453:1995 / ACI 347-04 / EN 1993-1-1
"""

import sys
import json
import math
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, List

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ACROW_PROPS = {
    "SP100": {"min_H": 0.5, "max_H": 1.0, "capacity": 35, "adjust": 1.0},
    "SP150": {"min_H": 0.9, "max_H": 1.5, "capacity": 30, "adjust": 1.0},
    "SP200": {"min_H": 1.4, "max_H": 2.0, "capacity": 25, "adjust": 1.0},
    "SP250": {"min_H": 1.8, "max_H": 2.5, "capacity": 20, "adjust": 1.0},
    "SP300": {"min_H": 2.4, "max_H": 3.0, "capacity": 15, "adjust": 1.0},
    "SP350": {"min_H": 3.0, "max_H": 3.5, "capacity": 12, "adjust": 1.0},
    "SP400": {"min_H": 3.5, "max_H": 4.0, "capacity": 8, "adjust": 1.0},
}

SCAFFOLD_TUBE = {
    "outer_d": 48.3, "wall_t": 3.2, "A": 453, "I": 1.19e5,
    "r": 16.2, "E": 210000, "fy": 250, "capacity_axial": 75,
}

RINGLOCK = {
    "standard_height": 2.0, "bay_width": 1.5, "ledger_vertical": 1.5,
    "capacity_per_leg": 50, "slenderness_limit": 200,
}

SAFETY_FACTORS = {
    "shoring_steel": 1.5, "shoring_timber": 1.8, "buckling": 1.5, "stability": 2.0,
}


@dataclass
class ShoringDesignResult:
    height: float
    load_per_prop: float
    system_type: str
    shore_spacing: float
    selected_prop: str
    prop_capacity: float
    effective_capacity: float
    number_of_props: int
    slenderness_ratio: float
    slenderness_limit: float
    buckling_check: str
    stability_check: str
    all_pass: bool
    warnings: List[str]
    recommendations: List[str]
    standard_method: str = "TCVN 4453:1995 / ACI 347-04"
    calculation_logs: List[Dict] = None

    def __post_init__(self):
        if self.calculation_logs is None:
            self.calculation_logs = []

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["Calculation_Logs"] = self.calculation_logs or []
        d["Standard_Method"] = self.standard_method
        return d


class ShoringSystemDesigner:
    def __init__(self, height: float, load_per_prop: float,
                 system_type: str = "acrow", shore_spacing: float = 0.9):
        self.height = height
        self.load_per_prop = load_per_prop
        self.system_type = system_type
        self.shore_spacing = shore_spacing
        self.logs = []

    def _log(self, step, formula, substitution, result, unit, citation=""):
        self.logs.append({
            "step": step, "formula": formula, "substitution": substitution,
            "result": round(float(result), 4), "unit": unit, "citation": citation
        })

    def select_acrow_prop(self) -> Dict:
        selected = None
        for name, prop in ACROW_PROPS.items():
            if prop["min_H"] <= self.height <= prop["max_H"]:
                selected = (name, prop)
                break
        if selected is None:
            selected = ("SP400", ACROW_PROPS["SP400"])
        name, prop = selected
        capacity = prop["capacity"] / SAFETY_FACTORS["shoring_steel"]
        eta = self.load_per_prop / capacity
        self._log(1, "Acrow prop selection", f"{name} - H:{prop['min_H']:.1f}-{prop['max_H']:.1f}m", prop["capacity"], "kN", "TCVN 4453")
        return {
            "type": name, "height_range": (prop["min_H"], prop["max_H"]),
            "gross_capacity": prop["capacity"], "effective_capacity": capacity,
            "load": self.load_per_prop, "eta": eta, "status": "PASS" if eta <= 1.0 else "FAIL"
        }

    def check_stability_acrow(self, prop_type: str) -> Dict:
        H = self.height
        K = 1.0
        r = 25.4
        I = math.pi * r ** 4 / 4
        lambda_ratio = K * H * 1000 / r
        lambda_limit = 200
        E = 210000
        P_Euler_kN = (math.pi ** 2 * E * I / (K * H * 1000) ** 2) / 1000
        self._log(10, "Slenderness ratio", f"{K} × {H*1000:.0f} / {r}", lambda_ratio, "-", "TCVN 4453")
        stability_pass = lambda_ratio <= lambda_limit
        buckling_pass = self.load_per_prop <= P_Euler_kN / SAFETY_FACTORS["buckling"]
        return {
            "slenderness_ratio": lambda_ratio, "slenderness_limit": lambda_limit,
            "euler_load": P_Euler_kN, "stability_status": "PASS" if stability_pass else "FAIL",
            "buckling_status": "PASS" if buckling_pass else "FAIL",
            "stability_pass": stability_pass, "buckling_pass": buckling_pass
        }

    def design_ringlock_tower(self) -> Dict:
        H = self.height
        bay_w = RINGLOCK["bay_width"]
        std_h = RINGLOCK["standard_height"]
        n_levels = math.ceil(H / std_h)
        tower_height = n_levels * std_h
        n_bays = max(1, round(bay_w / self.shore_spacing))
        # Chiều dài tính toán uốn dọc của chân giáo Ringlock bằng khoảng cách tầng giằng ngang ledger_vertical (1.5m), không phải toàn bộ chiều cao tháp!
        L_eff = min(H, RINGLOCK["ledger_vertical"]) * 1000.0
        r = SCAFFOLD_TUBE["r"]
        lambda_ratio = L_eff / r
        self._log(20, "Ringlock slenderness (unbraced ledger step)", f"λ = {L_eff:.0f}/{r} = {lambda_ratio:.1f}", lambda_ratio, "-", "EN 1993-1-1")
        capacity = RINGLOCK["capacity_per_leg"] / SAFETY_FACTORS["shoring_steel"]
        eta = self.load_per_prop / capacity
        return {
            "type": "Ringlock Tower", "height": tower_height, "n_levels": n_levels,
            "bay_width": bay_w, "n_bays": n_bays, "capacity_per_leg": capacity,
            "load": self.load_per_prop, "slenderness": lambda_ratio, "eta": eta,
            "status": "PASS" if eta <= 1.0 else "FAIL"
        }

    def design_tower_system(self) -> Dict:
        A_shore = self.shore_spacing ** 2
        P_total = self.load_per_prop * A_shore
        capacity = RINGLOCK["capacity_per_leg"] / SAFETY_FACTORS["shoring_steel"]
        n_shores = math.ceil(P_total / capacity)
        return {"shore_area": A_shore, "total_load": P_total, "capacity_per_shore": capacity, "number_of_shores": n_shores, "spacing": self.shore_spacing}

    def design(self) -> ShoringDesignResult:
        warnings, recommendations = [], []
        if self.system_type == "acrow":
            prop_result = self.select_acrow_prop()
            stability_result = self.check_stability_acrow(prop_result["type"])
            all_pass = prop_result["eta"] <= 1.0 and stability_result["stability_pass"] and stability_result["buckling_pass"]
            tower_result = None
        elif self.system_type in ["tower", "ringlock"]:
            ringlock_result = self.design_ringlock_tower()
            tower_result = self.design_tower_system()
            prop_result = {"type": ringlock_result["type"], "effective_capacity": ringlock_result["capacity_per_leg"], "eta": ringlock_result["eta"]}
            stability_result = {
                "slenderness_ratio": ringlock_result["slenderness"],
                "stability_pass": ringlock_result["slenderness"] <= RINGLOCK["slenderness_limit"],
                "buckling_pass": ringlock_result["eta"] <= 1.0
            }
            all_pass = ringlock_result["eta"] <= 1.0 and stability_result["stability_pass"]
        else:
            raise ValueError(f"Unknown system type: {self.system_type}")

        return ShoringDesignResult(
            height=self.height, load_per_prop=self.load_per_prop, system_type=self.system_type,
            shore_spacing=self.shore_spacing, selected_prop=prop_result["type"],
            prop_capacity=round(prop_result["effective_capacity"], 2),
            effective_capacity=round(prop_result["effective_capacity"], 2),
            number_of_props=tower_result["number_of_shores"] if tower_result else 1,
            slenderness_ratio=round(stability_result["slenderness_ratio"], 2),
            slenderness_limit=200,
            buckling_check="PASS" if stability_result["buckling_pass"] else "FAIL",
            stability_check="PASS" if stability_result["stability_pass"] else "FAIL",
            all_pass=all_pass, warnings=warnings, recommendations=recommendations,
            standard_method="TCVN 4453:1995 / ACI 347-04", calculation_logs=self.logs
        )


def main():
    parser = argparse.ArgumentParser(description="Thiết kế hệ thống cây chống")
    parser.add_argument("--height", "-H", type=float, required=True)
    parser.add_argument("--load", "-L", type=float, required=True)
    parser.add_argument("--system", "-s", default="acrow", choices=["acrow", "tower", "ringlock"])
    parser.add_argument("--spacing", type=float, default=0.9)
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    designer = ShoringSystemDesigner(height=args.height, load_per_prop=args.load, system_type=args.system, shore_spacing=args.spacing)
    result = designer.design()
    json_str = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
    print(json_str)


if __name__ == "__main__":
    main()
