#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_shoring_system.py — Thiết kế hệ thống cây chống (Shoring System Design)

Tiêu chuẩn:
- TCVN 4453:1995 - Công tác bê tông và BTCT
- ACI 347-04 - Formwork for Concrete
- Eurocode 3 (EN 1993-1-1) — Steel scaffolding

Hệ thống cây chống:
1. Acrow props (cây chống đơn)
2. Slab formwork shores (cây chống sàn)
3. Tower systems (hệ thống tháp chống)
4. Bracing systems (hệ giằng)

Usage:
    python calc_shoring_system.py --height 3.0 --load 50 --system acrow
    python calc_shoring_system.py -H 4.0 -L 80 -s tower --json
"""

import sys
import json
import math
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# STANDARD PROPERTIES DATABASE
# ============================================================================

# Acrow prop capacities (kN) theo chiều cao
ACROW_PROPS = {
    "SP100": {
        "min_H": 0.5, "max_H": 1.0,
        "capacity": 35, "adjust": 1.0
    },
    "SP150": {
        "min_H": 0.9, "max_H": 1.5,
        "capacity": 30, "adjust": 1.0
    },
    "SP200": {
        "min_H": 1.4, "max_H": 2.0,
        "capacity": 25, "adjust": 1.0
    },
    "SP250": {
        "min_H": 1.8, "max_H": 2.5,
        "capacity": 20, "adjust": 1.0
    },
    "SP300": {
        "min_H": 2.4, "max_H": 3.0,
        "capacity": 15, "adjust": 1.0
    },
    "SP350": {
        "min_H": 3.0, "max_H": 3.5,
        "capacity": 12, "adjust": 1.0
    },
    "SP400": {
        "min_H": 3.5, "max_H": 4.0,
        "capacity": 8, "adjust": 1.0
    },
}

# Steel scaffold tube properties (48.3mm OD, 3.2mm wall)
SCAFFOLD_TUBE = {
    "outer_d": 48.3,  # mm
    "wall_t": 3.2,    # mm
    "A": 453,          # mm²
    "I": 1.19e5,      # mm⁴
    "r": 16.2,         # mm (radius of gyration)
    "E": 210000,       # MPa
    "fy": 250,         # MPa
    "capacity_axial": 75,  # kN (with safety factor)
}

# Ringlock scaffold properties
RINGLOCK = {
    "standard_height": 2.0,  # m
    "bay_width": 1.5,       # m
    "ledger_vertical": 1.5,  # m
    "capacity_per_leg": 50,  # kN
    "slenderness_limit": 200,
}

# Safety factors
SAFETY_FACTORS = {
    "shoring_steel": 1.5,
    "shoring_timber": 1.8,
    "buckling": 1.5,
    "stability": 2.0,
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ShoringDesignResult:
    """Kết quả thiết kế hệ thống chống"""

    # Input
    height: float           # m
    load_per_prop: float   # kN
    system_type: str        # acrow | tower | ringlock
    shore_spacing: float    # m x m

    # System design
    selected_prop: str
    prop_capacity: float    # kN
    effective_capacity: float
    number_of_props: int

    # Stability check
    slenderness_ratio: float
    slenderness_limit: float
    buckling_check: str     # PASS | FAIL
    stability_check: str

    # Summary
    all_pass: bool
    warnings: List[str]
    recommendations: List[str]

    standard_method: str = "TCVN 4453:1995 / ACI 347-04"
    calculation_logs: List[Dict] = None

    def __post_init__(self):
        if self.calculation_logs is None:
            self.calculation_logs = []

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# CORE CALCULATIONS
# ============================================================================

class ShoringSystemDesigner:
    """Thiết kế hệ thống cây chống"""

    def __init__(self, height: float, load_per_prop: float,
                 system_type: str = "acrow",
                 shore_spacing: float = 0.9):
        self.height = height
        self.load_per_prop = load_per_prop
        self.system_type = system_type
        self.shore_spacing = shore_spacing
        self.logs = []

    def _log(self, step, formula, substitution, result, unit, citation=""):
        self.logs.append({
            "step": step,
            "formula": formula,
            "substitution": substitution,
            "result": round(float(result), 4),
            "unit": unit,
            "citation": citation
        })

    def select_acrow_prop(self) -> Dict:
        """Chọn và kiểm tra acrow prop phù hợp"""
        step = 1

        # Tìm prop phù hợp với chiều cao
        selected = None
        for name, prop in ACROW_PROPS.items():
            if prop["min_H"] <= self.height <= prop["max_H"]:
                selected = (name, prop)
                break

        if selected is None:
            # Fallback to largest
            selected = ("SP400", ACROW_PROPS["SP400"])

        name, prop = selected

        # Capacity với hệ số an toàn
        capacity = prop["capacity"] / SAFETY_FACTORS["shoring_steel"]
        eta = self.load_per_prop / capacity

        self._log(step, "Acrow prop selection",
                   f"{name} - H:{prop['min_H']:.1f}-{prop['max_H']:.1f}m",
                   prop["capacity"], "kN", "TCVN 4453")
        step += 1

        self._log(step, "Effective capacity",
                   f"{prop['capacity']} / {SAFETY_FACTORS['shoring_steel']}", capacity, "kN", "TCVN 4453:1995")

        return {
            "type": name,
            "height_range": (prop["min_H"], prop["max_H"]),
            "gross_capacity": prop["capacity"],
            "effective_capacity": capacity,
            "load": self.load_per_prop,
            "eta": eta,
            "status": "PASS" if eta <= 1.0 else "FAIL"
        }

    def check_stability_acrow(self, prop_type: str) -> Dict:
        """Kiểm tra ổn định cho acrow prop"""
        step = 10

        prop = ACROW_PROPS[prop_type]
        H = self.height

        # Effective length factor ( pinned-pinned = 1.0)
        K = 1.0

        # Slenderness ratio
        r = 25.4  # mm (typical acrow prop radius)
        I = math.pi * r**4 / 4
        A = math.pi * r**2

        lambda_ratio = K * H * 1000 / r
        lambda_limit = 200  # Giới hạn theo TCVN

        self._log(step, "Slenderness ratio",
                   f"{K} × {H*1000:.0f} / {r}", lambda_ratio, "-", "TCVN 4453")
        step += 1

        # Euler buckling load
        E = 210000  # MPa
        P_Euler = math.pi**2 * E * I / (K * H * 1000)**2  # N
        P_Euler_kN = P_Euler / 1000

        self._log(step, "Euler buckling load",
                   "π²EI/(KL)²", P_Euler_kN, "kN", "Eurocode 3")

        # Slenderness ratio check
        stability_pass = lambda_ratio <= lambda_limit
        buckling_pass = self.load_per_prop <= P_Euler_kN / SAFETY_FACTORS["buckling"]

        return {
            "slenderness_ratio": lambda_ratio,
            "slenderness_limit": lambda_limit,
            "euler_load": P_Euler_kN,
            "stability_status": "PASS" if stability_pass else "FAIL",
            "buckling_status": "PASS" if buckling_pass else "FAIL",
            "stability_pass": stability_pass,
            "buckling_pass": buckling_pass
        }

    def design_ringlock_tower(self) -> Dict:
        """Thiết kế tháp ringlock"""
        step = 20

        H = self.height
        bay_w = RINGLOCK["bay_width"]
        std_h = RINGLOCK["standard_height"]

        # Số tầng tiêu chuẩn
        n_levels = math.ceil(H / std_h)

        # Chiều cao tháp
        tower_height = n_levels * std_h

        # Số bước giằng ngang
        n_bays = max(1, round(bay_w / self.shore_spacing))

        self._log(step, "Tower configuration",
                   f"{n_levels} levels × {std_h}m = {tower_height}m",
                   tower_height, "m", "Eurocode 3")
        step += 1

        # Slenderness
        L_eff = K * tower_height * 1000 if 'K' in dir() else tower_height * 1000
        r = SCAFFOLD_TUBE["r"]
        lambda_ratio = L_eff / r

        self._log(step, "Ringlock slenderness",
                   f"λ = {lambda_ratio:.1f}", lambda_ratio, "-", "EC3")

        # Capacity per leg
        capacity = RINGLOCK["capacity_per_leg"] / SAFETY_FACTORS["shoring_steel"]
        eta = self.load_per_prop / capacity

        return {
            "type": "Ringlock Tower",
            "height": tower_height,
            "n_levels": n_levels,
            "bay_width": bay_w,
            "n_bays": n_bays,
            "capacity_per_leg": capacity,
            "load": self.load_per_prop,
            "slenderness": lambda_ratio,
            "eta": eta,
            "status": "PASS" if eta <= 1.0 else "FAIL"
        }

    def design_tower_system(self) -> Dict:
        """Thiết kế hệ thống tháp chống"""
        step = 30

        H = self.height
        P = self.load_per_prop

        # Diện tích phục vụ mỗi cây chống
        A_shore = self.shore_spacing ** 2

        # Tổng tải
        P_total = P * A_shore

        self._log(step, "Load per shore area",
                   f"{P:.2f} × {A_shore:.2f}", P_total, "kN", "TCVN 4453")
        step += 1

        # Số lượng cây chống cần thiết
        if self.system_type == "acrow":
            prop = self.select_acrow_prop()
            capacity = prop["effective_capacity"]
        else:
            capacity = RINGLOCK["capacity_per_leg"] / SAFETY_FACTORS["shoring_steel"]

        n_shores = math.ceil(P_total / capacity)

        self._log(step, "Number of shores",
                   f"{P_total:.2f} / {capacity:.2f}", n_shores, "cây", "TCVN 4453")

        return {
            "shore_area": A_shore,
            "total_load": P_total,
            "capacity_per_shore": capacity,
            "number_of_shores": n_shores,
            "spacing": self.shore_spacing
        }

    def design(self) -> ShoringDesignResult:
        """Chạy thiết kế hoàn chỉnh"""

        warnings = []
        recommendations = []

        if self.system_type == "acrow":
            prop_result = self.select_acrow_prop()
            stability_result = self.check_stability_acrow(prop_result["type"])

            all_pass = (
                prop_result["eta"] <= 1.0 and
                stability_result["stability_pass"] and
                stability_result["buckling_pass"]
            )

            if prop_result["eta"] > 0.9:
                warnings.append(f"Acrow prop {prop_result['type']}: η = {prop_result['eta']:.3f} > 0.9 — Sát ngưỡng")

            tower_result = None
            slenderness = stability_result["slenderness_ratio"]

        elif self.system_type in ["tower", "ringlock"]:
            ringlock_result = self.design_ringlock_tower()
            tower_result = self.design_tower_system()

            prop_result = {
                "type": ringlock_result["type"],
                "effective_capacity": ringlock_result["capacity_per_leg"],
                "eta": ringlock_result["eta"]
            }

            stability_result = {
                "slenderness_ratio": ringlock_result["slenderness"],
                "stability_pass": ringlock_result["slenderness"] <= RINGLOCK["slenderness_limit"],
                "buckling_pass": ringlock_result["eta"] <= 1.0
            }

            slenderness = ringlock_result["slenderness"]
            all_pass = ringlock_result["eta"] <= 1.0

        else:
            raise ValueError(f"Unknown system type: {self.system_type}")

        # Warnings
        if stability_result["slenderness_ratio"] > 150:
            warnings.append(f"Độ mảnh λ = {stability_result['slenderness_ratio']:.1f} cao — kiểm tra độ võng")

        if prop_result["eta"] <= 0.7:
            recommendations.append(f"{prop_result['type']}: η = {prop_result['eta']:.3f} ≤ 0.7 — Có thể tối ưu")

        if all_pass:
            recommendations.append("Thiết kế đạt yêu cầu")

        return ShoringDesignResult(
            height=self.height,
            load_per_prop=self.load_per_prop,
            system_type=self.system_type,
            shore_spacing=self.shore_spacing,
            selected_prop=prop_result["type"],
            prop_capacity=prop_result["effective_capacity"],
            effective_capacity=prop_result["effective_capacity"],
            number_of_props=tower_result["number_of_shores"] if tower_result else 1,
            slenderness_ratio=stability_result["slenderness_ratio"],
            slenderness_limit=200,
            buckling_check="PASS" if stability_result["buckling_pass"] else "FAIL",
            stability_check="PASS" if stability_result["stability_pass"] else "FAIL",
            all_pass=all_pass,
            warnings=warnings,
            recommendations=recommendations,
            standard_method="TCVN 4453:1995 / ACI 347-04",
            calculation_logs=self.logs
        )


# ============================================================================
# CLI
# ============================================================================

def print_result(result: ShoringDesignResult):
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{'=' * 70}")
    print(f"{BOLD}THIẾT KẾ HỆ THỐNG CÂY CHỐNG{RESET}")
    print(f"{'─' * 70}")

    status_color = GREEN if result.all_pass else RED
    status_text = "✅ ĐẠT YÊU CẦU" if result.all_pass else "❌ KHÔNG ĐẠT"
    print(f"\nTrạng thái: {status_color}{status_text}{RESET}")
    print(f"Tiêu chuẩn: {result.standard_method}")

    print(f"\n{BOLD}📥 ĐẦU VÀO:{RESET}")
    print(f"  Chiều cao: {result.height} m")
    print(f"  Tải trọng: {result.load_per_prop} kN/cây")
    print(f"  Loại hệ thống: {result.system_type}")
    print(f"  Cự ly cây chống: {result.shore_spacing} m")

    print(f"\n{BOLD}📊 KẾT QUẢ THIẾT KẾ:{RESET}")
    print(f"  Loại cây chống: {result.selected_prop}")
    print(f"  Công suất hiệu dụng: {result.prop_capacity:.2f} kN")
    print(f"  Số lượng cần thiết: {result.number_of_props} cây")
    print(f"  Hệ số η = {result.load_per_prop / result.prop_capacity:.3f}")

    print(f"\n{BOLD}📐 KIỂM TRA ỔN ĐỊNH:{RESET}")
    sl_color = GREEN if result.slenderness_ratio <= result.slenderness_limit else RED
    print(f"  Độ mảnh λ = {result.slenderness_ratio:.1f} / {result.slenderness_limit}")
    print(f"  Ổn định: {sl_color}{result.stability_check}{RESET}")
    print(f"  Buckling: {GREEN if result.buckling_check == 'PASS' else RED}{result.buckling_check}{RESET}")

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
    parser = argparse.ArgumentParser(description="Thiết kế hệ thống cây chống")
    parser.add_argument("--height", "-H", type=float, required=True, help="Chiều cao cây chống (m)")
    parser.add_argument("--load", "-L", type=float, required=True, help="Tải trọng trên mỗi cây chống (kN)")
    parser.add_argument("--system", "-s", default="acrow",
                       choices=["acrow", "tower", "ringlock"],
                       help="Loại hệ thống chống")
    parser.add_argument("--spacing", type=float, default=0.9, help="Cự ly cây chống (m)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    designer = ShoringSystemDesigner(
        height=args.height,
        load_per_prop=args.load,
        system_type=args.system,
        shore_spacing=args.spacing
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
