#!/usr/bin/env python3
"""
calc_slab_formwork.py — Slab Formwork Design Calculator

Calculates panel, joist, and soldier beam spacing for concrete slab formwork.

Usage:
    python calc_slab_formwork.py --thickness 200 --span 2.4 --concrete_grade B25 [options]

Output: JSON with design results and calculation logs
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import math
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class CalcLog:
    step: int
    description: str
    formula: str
    input_values: dict
    result: float
    unit: str
    standard: str


class SlabFormworkCalculator:
    """Slab formwork design calculator"""

    # Material properties
    MATERIALS = {
        "plywood_18mm": {
            "E": 9000,  # MPa (lywood modulus)
            "f_m": 12,   # MPa (bending)
            "f_v": 1.5,  # MPa (shear)
            "I": 437.4,  # cm^4 (for 1m width, t=18mm)
            "W": 48.6,   # cm^3 (for 1m width)
            "weight": 0.18 * 7.5,  # kN/m² (18mm × 7.5 kN/m³)
        },
        "plywood_15mm": {
            "E": 8500,
            "f_m": 11,
            "f_v": 1.3,
            "I": 281.25,
            "W": 37.5,
            "weight": 0.15 * 7.5,
        },
        "timber_joist": {
            "E": 10000,  # MPa
            "f_m": 12,   # MPa
            "f_v": 1.5,
            "gamma": 5.5,  # kN/m³
        },
        "steel_i150": {
            "E": 210000,
            "f_y": 250,
            "I_x": 1273.7,  # cm^4
            "W_x": 170.7,   # cm³
            "S_x": 194.1,   # cm³
            "A": 19.14,     # cm²
            "t_w": 4.5,     # mm
            "h": 150,       # mm
            "weight": 15.0,  # kg/m
        },
        "steel_i200": {
            "E": 210000,
            "f_y": 250,
            "I_x": 2213.6,
            "W_x": 221.4,
            "S_x": 252.4,
            "A": 26.81,
            "t_w": 5.6,
            "h": 200,
            "weight": 21.1,
        },
    }

    # Load combinations (TCVN 2737:2023)
    GAMMA_DEAD = 1.2
    GAMMA_LIVE = 1.5

    # Deflection limits
    LIMITS = {
        "panel": "L/270",
        "joist": "L/360",
        "soldier": "L/400",
        "shore": "L/500"
    }

    def __init__(self, thickness_mm: float, span_m: float, concrete_grade: str,
                 construction_load: float = 1.5, timber_spacing: Optional[List[float]] = None):
        """
        Initialize calculator.

        Args:
            thickness_mm: Slab thickness in mm
            span_m: Joist span in meters
            concrete_grade: Concrete grade (B15, B20, B25, etc.)
            construction_load: Construction load in kN/m² (default 1.5)
            timber_spacing: List of possible timber spacings to check
        """
        self.thickness_mm = thickness_mm
        self.span_m = span_m
        self.concrete_grade = concrete_grade
        self.construction_load = construction_load
        self.timber_spacing = timber_spacing or [450, 600, 750, 900]

        # Concrete density
        self.gamma_concrete = 25.0  # kN/m³ (normal weight)

        # Get concrete strength
        self.f_c = self._get_concrete_strength(concrete_grade)

        # Calculation logs
        self.logs: List[CalcLog] = []

    def _get_concrete_strength(self, grade: str) -> float:
        """Get concrete compressive strength in MPa"""
        grade_map = {
            "B15": 12.5, "B20": 17.0, "B25": 21.0, "B30": 26.0,
            "B35": 30.0, "B40": 34.0, "B45": 39.0, "B50": 44.0
        }
        return grade_map.get(grade, 21.0)

    def _log(self, step: int, desc: str, formula: str,
             inputs: dict, result: float, unit: str, standard: str = "TCVN 5575:2024"):
        """Add calculation log entry"""
        self.logs.append(CalcLog(step, desc, formula, inputs, result, unit, standard))

    def calculate_panel_load(self) -> dict:
        """Calculate design load on panel"""
        step = 1

        # Dead load: concrete + plywood weight
        q_dead = self.gamma_concrete * self.thickness_mm / 1000  # kN/m²
        q_plywood = self.MATERIALS["plywood_18mm"]["weight"]

        self._log(
            step, "Dead load on panel",
            "q_dead = γ_bt × t + γ_plywood",
            {"γ_bt": self.gamma_concrete, "t_mm": self.thickness_mm,
             "γ_plywood": q_plywood},
            q_dead, "kN/m²"
        )

        # Construction load
        q_live = self.construction_load
        self._log(
            step + 1, "Construction load",
            "q_live = 1.5 kN/m² (default)",
            {"q_tc": q_live},
            q_live, "kN/m²"
        )

        # Design load
        q_design = self.GAMMA_DEAD * (q_dead + q_plywood) + self.GAMMA_LIVE * q_live
        self._log(
            step + 2, "Design load combination",
            "q_d = γ_D × (q_bt + q_ply) + γ_L × q_tc",
            {"γ_D": self.GAMMA_DEAD, "γ_L": self.GAMMA_LIVE,
             "q_bt+q_ply": q_dead + q_plywood, "q_tc": q_live},
            q_design, "kN/m²"
        )

        return {
            "q_dead": q_dead,
            "q_plywood": q_plywood,
            "q_live": q_live,
            "q_design": q_design
        }

    def check_plywood_panel(self, spacing_mm: float, span_mm: float,
                           thickness_mm: int = 18) -> dict:
        """
        Check plywood panel deflection and stress.

        Args:
            spacing_mm: Joist spacing in mm
            span_mm: Panel span (joist spacing) in mm
            thickness_mm: Plywood thickness

        Returns:
            dict with check results
        """
        step = 10
        mat = self.MATERIALS[f"plywood_{thickness_mm}mm"]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        # Convert to N/mm² and mm
        q_N_mm = q / 1000  # kN/m² → N/mm²

        # Maximum moment (simply supported, 1m width)
        L = span_mm
        M = q_N_mm * L**2 / 8  # N·mm per mm width

        # Bending stress
        t = thickness_mm
        Z = t**2 / 6  # mm³ per mm width
        sigma = M / Z * 1000  # MPa

        self._log(
            step, "Plywood bending stress",
            "σ = M / Z",
            {"M": M, "Z": Z, "L_mm": L},
            sigma, "MPa"
        )

        # Allowable stress
        f_m = mat["f_m"]
        eta_bending = sigma / f_m

        # Shear check
        V = q_N_mm * L / 2  # N per mm width
        I = t**3 / 12  # mm⁴ per mm width
        Q = t**2 / 8  # mm³ per mm width
        tau = V * Q / (I * t) * 1000  # MPa

        self._log(
            step + 1, "Plywood shear stress",
            "τ = V × Q / (I × t)",
            {"V": V, "Q": Q, "I": I},
            tau, "MPa"
        )

        f_v = mat["f_v"]
        eta_shear = tau / f_v

        # Deflection check
        E = mat["E"]
        I_mm = t**3 / 12

        # δ = 5qL⁴ / (384EI)
        delta = 5 * q_N_mm * L**4 / (384 * E * I_mm)

        self._log(
            step + 2, "Plywood deflection",
            "δ = 5qL⁴ / (384EI)",
            {"q": q, "L": L, "E": E, "I": I_mm},
            delta, "mm"
        )

        # Allowable deflection
        delta_allow = L / 270
        eta_deflection = delta / delta_allow

        return {
            "bending": {
                "sigma_MPa": round(sigma, 3),
                "f_m_MPa": f_m,
                "eta": round(eta_bending, 3),
                "status": "PASS" if eta_bending <= 1.0 else "FAIL"
            },
            "shear": {
                "tau_MPa": round(tau, 3),
                "f_v_MPa": f_v,
                "eta": round(eta_shear, 3),
                "status": "PASS" if eta_shear <= 1.0 else "FAIL"
            },
            "deflection": {
                "delta_mm": round(delta, 2),
                "allowable_mm": round(delta_allow, 2),
                "ratio": "L/270",
                "eta": round(eta_deflection, 3),
                "status": "PASS" if eta_deflection <= 1.0 else "FAIL"
            }
        }

    def check_timber_joist(self, spacing_mm: float, joist_size_mm: tuple,
                          span_m: float) -> dict:
        """
        Check timber joist.

        Args:
            spacing_mm: Joist spacing
            joist_size_mm: (width, height) tuple
            span_m: Joist span in meters
        """
        step = 20
        mat = self.MATERIALS["timber_joist"]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        # Load on joist
        w = q * spacing_mm / 1000  # kN/m

        self._log(
            step, "Load on timber joist",
            "w = q × S",
            {"q": q, "S": spacing_mm},
            w, "kN/m"
        )

        b, h = joist_size_mm
        L = span_m * 1000  # mm

        # Moment
        M = w * span_m / 8 * 1000  # kNm → Nmm

        # Section modulus
        Z = b * h**2 / 6  # mm³

        sigma = M / Z  # MPa
        f_m = mat["f_m"]
        eta_bending = sigma / f_m

        self._log(
            step + 1, "Timber joist bending",
            "σ = M / Z",
            {"M_Nmm": M, "Z": Z},
            sigma, "MPa"
        )

        # Shear
        V = w * span_m / 2  # kN
        A = b * h  # mm²
        tau = V * 1000 / A  # MPa

        f_v = mat["f_v"]
        eta_shear = tau / f_v

        self._log(
            step + 2, "Timber joist shear",
            "τ = V / A",
            {"V": V * 1000, "A": A},
            tau, "MPa"
        )

        # Deflection
        E = mat["E"]
        I = b * h**3 / 12  # mm⁴

        # Convert w to N/mm
        w_N_mm = w * 1000 / 1000  # kN/m → N/mm
        L_mm = L

        delta = 5 * w_N_mm * L_mm**4 / (384 * E * I)  # mm

        delta_allow = L_mm / 360
        eta_deflection = delta / delta_allow

        self._log(
            step + 3, "Timber joist deflection",
            "δ = 5wL⁴ / (384EI)",
            {"w_Nmm": w_N_mm, "L": L_mm, "E": E, "I": I},
            delta, "mm"
        )

        return {
            "bending": {
                "sigma_MPa": round(sigma, 3),
                "f_m_MPa": f_m,
                "eta": round(eta_bending, 3),
                "status": "PASS" if eta_bending <= 1.0 else "FAIL"
            },
            "shear": {
                "tau_MPa": round(tau, 3),
                "f_v_MPa": f_v,
                "eta": round(eta_shear, 3),
                "status": "PASS" if eta_shear <= 1.0 else "FAIL"
            },
            "deflection": {
                "delta_mm": round(delta, 2),
                "allowable_mm": round(delta_allow, 2),
                "ratio": "L/360",
                "eta": round(eta_deflection, 3),
                "status": "PASS" if eta_deflection <= 1.0 else "FAIL"
            }
        }

    def check_steel_soldier(self, spacing_mm: float, steel_type: str,
                           span_m: float) -> dict:
        """
        Check steel soldier beam.

        Args:
            spacing_mm: Soldier spacing
            steel_type: 'steel_i150' or 'steel_i200'
            span_m: Span in meters
        """
        step = 30
        mat = self.MATERIALS[steel_type]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        # Load on soldier
        w = q * spacing_mm / 1000  # kN/m

        self._log(
            step, "Load on soldier beam",
            "w = q × S",
            {"q": kPa, "S": spacing_mm},
            w, "kN/m"
        )

        L = span_m

        # Moment
        M = w * L**2 / 8  # kNm

        # Bending stress
        W_x = mat["W_x"] * 1000  # mm³
        f_y = mat["f_y"]
        gamma_M0 = 1.05
        f = f_y / gamma_M0

        sigma = M * 1e6 / W_x  # MPa

        self._log(
            step + 1, "Steel soldier bending",
            "σ = M / W_x ≤ f_y/γ_M0",
            {"M": M, "W_x": W_x, "f": f},
            sigma, "MPa"
        )

        eta_bending = sigma / f

        # Shear
        V = w * L / 2  # kN
        A = mat["A"] * 100  # mm²
        t_w = mat["t_w"]

        tau = V * 1000 / (mat["h"] * t_w)  # MPa
        f_v = 0.58 * f_y / gamma_M0

        self._log(
            step + 2, "Steel soldier shear",
            "τ = V / (h × t_w)",
            {"V": V, "h": mat["h"], "t_w": t_w},
            tau, "MPa"
        )

        eta_shear = tau / f_v

        # Deflection
        E = mat["E"]
        I_x = mat["I_x"] * 1e4  # mm⁴

        delta = 5 * w * 1000 * (L * 1000)**3 / (384 * E * I_x) / 1000  # mm

        delta_allow = L * 1000 / 400
        eta_deflection = delta / delta_allow

        self._log(
            step + 3, "Steel soldier deflection",
            "δ = 5wL⁴ / (384EI)",
            {"L": L, "E": E, "I": I_x},
            delta, "mm"
        )

        return {
            "section": steel_type,
            "bending": {
                "sigma_MPa": round(sigma, 3),
                "f_MPa": round(f, 3),
                "eta": round(eta_bending, 3),
                "status": "PASS" if eta_bending <= 1.0 else "FAIL"
            },
            "shear": {
                "tau_MPa": round(tau, 3),
                "f_v_MPa": round(f_v, 3),
                "eta": round(eta_shear, 3),
                "status": "PASS" if eta_shear <= 1.0 else "FAIL"
            },
            "deflection": {
                "delta_mm": round(delta, 2),
                "allowable_mm": round(delta_allow, 2),
                "ratio": "L/400",
                "eta": round(eta_deflection, 3),
                "status": "PASS" if eta_deflection <= 1.0 else "FAIL"
            }
        }

    def optimize(self) -> dict:
        """
        Run full optimization to find optimal spacing.

        Returns:
            dict with all results
        """
        results = {
            "input": {
                "slab_thickness_mm": self.thickness_mm,
                "span_m": self.span_m,
                "concrete_grade": self.concrete_grade,
                "construction_load_kPa": self.construction_load,
            },
            "loads": self.calculate_panel_load(),
            "panel_check": {},
            "joist_checks": [],
            "soldier_checks": [],
            "recommended": None,
            "calculation_logs": []
        }

        # Check plywood at different spacings
        for spacing in self.timber_spacing:
            check = self.check_plywood_panel(spacing_mm=spacing, span_mm=spacing)
            check["spacing_mm"] = spacing
            results["panel_check"][str(spacing)] = check

            # Timber joist checks
            for size in [(50, 100), (50, 150), (80, 120)]:
                joist_check = self.check_timber_joist(
                    spacing_mm=spacing,
                    joist_size_mm=size,
                    span_m=self.span_m
                )
                joist_check["joist_size_mm"] = size
                results["joist_checks"].append(joist_check)

        # Steel soldier checks
        for spacing in [1200, 1500, 1800, 2100]:
            for steel in ["steel_i150", "steel_i200"]:
                soldier_check = self.check_steel_soldier(
                    spacing_mm=spacing,
                    steel_type=steel,
                    span_m=self.span_m
                )
                soldier_check["spacing_mm"] = spacing
                results["soldier_checks"].append(soldier_check)

        # Find recommended solution
        recommended = self._find_recommended(results)
        results["recommended"] = recommended

        # Convert logs to dict
        results["calculation_logs"] = [asdict(log) for log in self.logs]

        return results

    def _find_recommended(self, results: dict) -> dict:
        """Find optimal recommended solution"""
        # Find minimum η joist that passes
        passing_joists = [
            j for j in results["joist_checks"]
            if j["bending"]["status"] == "PASS"
            and j["shear"]["status"] == "PASS"
            and j["deflection"]["status"] == "PASS"
        ]

        if passing_joists:
            # Sort by bending eta (lower is better)
            best_joist = min(passing_joists, key=lambda x: x["bending"]["eta"])

            # Find corresponding panel check
            panel_spacing = best_joist["joist_size_mm"][0] if isinstance(best_joist.get("joist_size_mm"), tuple) else 600
            panel_check = results["panel_check"].get(str(panel_spacing), {})

            return {
                "type": "timber_joist",
                "joist_size_mm": best_joist["joist_size_mm"],
                "spacing_mm": panel_spacing,
                "max_span_m": self.span_m,
                "panel_thickness_mm": 18,
                "eta_overall": max(
                    best_joist["bending"]["eta"],
                    best_joist["shear"]["eta"],
                    best_joist["deflection"]["eta"]
                ),
                "checks": {
                    "panel": panel_check,
                    "joist": best_joist
                }
            }

        return {"type": "FAIL", "message": "No passing configuration found"}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Slab Formwork Design Calculator")
    parser.add_argument("--thickness", "-t", type=float, required=True,
                       help="Slab thickness in mm")
    parser.add_argument("--span", "-s", type=float, required=True,
                       help="Joist span in meters")
    parser.add_argument("--grade", "-g", default="B25",
                       help="Concrete grade (B15, B20, B25, etc.)")
    parser.add_argument("--construction-load", "-c", type=float, default=1.5,
                       help="Construction load in kN/m²")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--spacing", nargs="+", type=float,
                       help="Timber spacings to check (mm)")

    args = parser.parse_args()

    # Calculate
    calc = SlabFormworkCalculator(
        thickness_mm=args.thickness,
        span_m=args.span,
        concrete_grade=args.grade,
        construction_load=args.construction_load,
        timber_spacing=args.spacing
    )

    results = calc.optimize()

    # Print summary
    print("\n" + "="*60)
    print("SLAB FORMWORK DESIGN RESULTS")
    print("="*60)
    print(f"\nInput:")
    print(f"  Slab thickness: {args.thickness} mm")
    print(f"  Span: {args.span} m")
    print(f"  Concrete grade: {args.grade}")
    print(f"  Construction load: {args.construction_load} kN/m²")

    print(f"\nLoads:")
    print(f"  Dead load (concrete): {results['loads']['q_dead']:.2f} kN/m²")
    print(f"  Construction load: {results['loads']['q_live']:.2f} kN/m²")
    print(f"  Design load: {results['loads']['q_design']:.2f} kN/m²")

    rec = results["recommended"]
    if rec["type"] != "FAIL":
        print(f"\n✓ RECOMMENDED SOLUTION:")
        print(f"  Joist size: {rec['joist_size_mm'][0]}×{rec['joist_size_mm'][1]} mm")
        print(f"  Spacing: {rec['spacing_mm']} mm")
        print(f"  Panel: {rec['panel_thickness_mm']} mm plywood")
        print(f"  Overall η: {rec['eta_overall']:.1%}")
        print(f"  Status: PASS")
    else:
        print(f"\n✗ {rec['message']}")

    # Output JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results written to {args.output}")

    # Exit code
    if rec["type"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
