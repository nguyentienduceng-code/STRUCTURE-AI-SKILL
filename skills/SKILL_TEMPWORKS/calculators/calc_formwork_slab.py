#!/usr/bin/env python3
"""
calc_formwork_slab.py — Thiết kế cốp pha sàn (Slab Formwork Design)

Tiêu chuẩn:
- TCVN 4453:1995 - Công tác bê tông và BTCT
- ACI 347-04 - Formwork for Concrete

Hệ thống cốp pha:
1. Plywood deck (ván khuôn đáy)
2. Secondary beam / joist (dầm phụ - gỗ hoặc thép)
3. Primary beam / bearer (dầm chính)
4. Shore / prop (cây chống)

Usage:
    python calc_formwork_slab.py --thickness 250 --span 6.0 --grade B30
    python calc_formwork_slab.py --thickness 200 --span 5.0 --grade B25 --json
"""

import sys
import json
import math
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

for _p in Path(__file__).resolve().parents:
    if (_p / "_SHARED" / "standards" / "tables.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

try:
    from _SHARED.standards.tables import GAMMA_M0
except ImportError:
    GAMMA_M0 = 1.05


# ============================================================================
# CONFIGURATION
# ============================================================================

# Vietnamese Concrete Grades (TCVN)
CONCRETE_GRADES = {
    "B15": {"gamma": 24.0, "f_ck": 12.5, "Ec": 27000, "name": "B15"},
    "B20": {"gamma": 24.0, "f_ck": 16.5, "Ec": 29500, "name": "B20"},
    "B25": {"gamma": 24.5, "f_ck": 19.0, "Ec": 30000, "name": "B25"},
    "B30": {"gamma": 25.0, "f_ck": 22.5, "Ec": 32500, "name": "B30"},
    "B35": {"gamma": 25.0, "f_ck": 26.0, "Ec": 34000, "name": "B35"},
    "B40": {"gamma": 25.0, "f_ck": 30.0, "Ec": 35500, "name": "B40"},
}

# Plywood Properties (mm)
PLYWOOD_TYPES = {
    "15mm": {"t": 15, "E": 9000, "sigma": 10, "weight": 7.5, "I": 281.25, "Z": 37.5},
    "18mm": {"t": 18, "E": 9000, "sigma": 10, "weight": 9.0, "I": 437.4, "Z": 48.6},
    "21mm": {"t": 21, "E": 9000, "sigma": 10, "weight": 10.5, "I": 648.3, "Z": 61.7},
}

# Steel I-beam catalog (approximate properties)
STEEL_BEAMS = {
    "H100x50": {"Ix": 3.56e-6, "Sx": 0.0000712, "W": 9.32, "h": 100, "bf": 50},
    "H150x75": {"Ix": 1.68e-5, "Sx": 0.000225, "W": 14.0, "h": 150, "bf": 75},
    "H200x100": {"Ix": 4.78e-5, "Sx": 0.000478, "W": 21.3, "h": 200, "bf": 100},
    "H250x125": {"Ix": 1.09e-4, "Sx": 0.000876, "W": 29.6, "h": 250, "bf": 125},
}

# Timber beam properties
TIMBER_BEAMS = {
    "50x100": {"b": 0.05, "h": 0.10, "E": 9000, "sigma": 12},  # MPa
    "80x160": {"b": 0.08, "h": 0.16, "E": 9000, "sigma": 12},
    "100x200": {"b": 0.10, "h": 0.20, "E": 9000, "sigma": 12},
}

# Safety factors
SAFETY_FACTORS = {
    "load_DL": 1.2,
    "load_LL": 1.5,
    "material": 1.5,
    "stability": 2.0,
}

# Deflection limits
DEFLECTION_LIMITS = {
    "good_appearance": "L/360",
    "structural": "L/250",
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FormworkDesignResult:
    """Kết quả thiết kế cốp pha sàn"""

    # Input
    slab_thickness: float
    slab_span: float
    concrete_grade: str
    formwork_type: str
    plywood_thickness: int

    # Calculated loads
    concrete_load: float      # kN/m²
    formwork_weight: float    # kN/m²
    construction_load: float   # kN/m²
    total_load_DL: float     # kN/m²
    total_load: float         # kN/m²

    # Plywood design
    plywood_span: float       # m (joist spacing)
    plywood_stress: float     # MPa
    plywood_deflection: float # mm
    eta_plywood: float

    # Secondary beam (joist) design
    joist_type: str
    joist_span: float        # m (between primary beams)
    joist_spacing: float     # m
    joist_stress: float      # MPa
    joist_deflection: float  # mm
    eta_joist: float

    # Primary beam design
    primary_beam_type: str
    primary_beam_span: float # m (between shores)
    primary_beam_stress: float
    primary_beam_deflection: float
    eta_primary: float

    # Shore design
    shore_spacing_transverse: float  # m
    shore_spacing_longitudinal: float # m
    shore_area: float         # m² per shore
    shore_load: float        # kN
    shore_capacity: float    # kN
    eta_shore: float
    num_shores: int

    # Summary
    all_pass: bool
    warnings: List[str]
    recommendations: List[str]

    # Metadata
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


# ============================================================================
# CORE CALCULATIONS
# ============================================================================

class SlabFormworkDesigner:
    """Thiết kế cốp pha sàn"""

    def __init__(self, slab_thickness: float, slab_span: float,
                 concrete_grade: str = "B30",
                 formwork_type: str = "plywood",
                 plywood_thickness: int = 18,
                 construction_load: float = 1.5):
        self.slab_thickness = slab_thickness
        self.slab_span = slab_span
        self.concrete_grade = concrete_grade
        self.formwork_type = formwork_type
        self.plywood_thickness = plywood_thickness
        self.construction_load = construction_load
        self.logs = []

        if concrete_grade not in CONCRETE_GRADES:
            raise ValueError(f"Unknown concrete grade: {concrete_grade}")

    def _log(self, step: int, formula: str, substitution: str, result: float,
              unit: str, citation: str = ""):
        self.logs.append({
            "step": step,
            "formula": formula,
            "substitution": substitution,
            "result": round(result, 4),
            "unit": unit,
            "citation": citation
        })

    def calculate_loads(self) -> Dict[str, float]:
        """Tính toán tải trọng"""
        step = 1

        conc = CONCRETE_GRADES[self.concrete_grade]
        gamma_c = conc["gamma"]
        h = self.slab_thickness / 1000

        q_concrete = gamma_c * h
        self._log(step, "q_concrete = γ_c × h", f"= {gamma_c} × {h}", q_concrete, "kN/m²", "TCVN 2737:2023")
        step += 1

        ply_data = PLYWOOD_TYPES.get(f"{self.plywood_thickness}mm", PLYWOOD_TYPES["18mm"])
        q_formwork = ply_data["weight"] * 10 / 1000
        self._log(step, "q_formwork = weight × g", f"≈ {q_formwork:.2f} kN/m²", q_formwork, "kN/m²", "ACI 347-04")
        step += 1

        q_construction = self.construction_load
        self._log(step, "q_construction", f"= {q_construction} kN/m²", q_construction, "kN/m²", "TCVN 4453:1995")
        step += 1

        q_DL = q_concrete + q_formwork
        self._log(step, "q_DL = q_concrete + q_formwork", f"= {q_DL:.2f} kN/m²", q_DL, "kN/m²", "TCVN 2737:2023")
        step += 1

        q_total = q_DL * SAFETY_FACTORS["load_DL"] + q_construction * SAFETY_FACTORS["load_LL"]
        self._log(step, "q_total = 1.2×q_DL + 1.5×q_construction", f"= {q_total:.2f} kN/m²", q_total, "kN/m²", "TCVN 2737:2023")

        return {
            "q_concrete": q_concrete,
            "q_formwork": q_formwork,
            "q_construction": q_construction,
            "q_DL": q_DL,
            "q_total": q_total
        }

    def design_plywood(self, q: float) -> Dict:
        """Thiết kế plywood"""
        ply_data = PLYWOOD_TYPES.get(f"{self.plywood_thickness}mm", PLYWOOD_TYPES["18mm"])
        E = ply_data["E"] * 1e6  # Pa
        sigma_allow = ply_data["sigma"] * 1e6  # Pa
        # [FIX BUG-STR-07a]: I_table = 437.4 (10^3 mm^4 = 10^-9 m^4), q đổi từ kN/m sang N/m (* 1000)
        I = ply_data["I"] * 1e-9  # m⁴
        Z = ply_data["Z"] * 1e-6  # m³

        # Optimize span based on deflection: δ = 5*(q*1000)*L⁴/(384*E*I) [m] ≤ L/360 [m]
        L = 0.6  # Start with 0.6m
        for _ in range(50):
            delta_m = 5 * (q * 1000.0) * L**4 / (384 * E * I)
            if delta_m <= L / 360:
                break
            L *= 0.95

        L = round(L, 2)

        # Calculate actual stress (MPa) and deflection (mm)
        M = q * L**2 / 8  # kNm/m
        sigma = (M * 1000.0) / Z / 1e6  # MPa (quy đổi M từ kNm sang Nm)
        delta = 5 * (q * 1000.0) * L**4 / (384 * E * I) * 1000.0  # mm
        delta_allow = L * 1000 / 360

        eta = max(sigma / (sigma_allow/1e6), delta / delta_allow)

        return {
            "span": L,
            "stress": sigma,
            "deflection": delta,
            "deflection_allow": delta_allow,
            "eta": eta
        }

    def design_joist(self, q: float, joist_span: float) -> Dict:
        """Thiết kế dầm phụ (joist) - giảm span bằng primary beams"""
        # Joist được đỡ bởi primary beams
        # Joist span = khoảng cách giữa các primary beams

        # Chọn joist_span tối ưu dựa trên deflection limit
        # Timber 50x100mm với L/360 limit
        prop = TIMBER_BEAMS["50x100"]
        E = prop["E"] * 1e6  # Pa
        b = prop["b"]
        h = prop["h"]
        I = b * h**3 / 12
        Z = b * h**2 / 6

        # Plywood spacing = joist span
        joist_spacing = self.optimize_plywood_span(q)

        # Tính joist_span tối ưu cho deflection
        # δ = 5qL⁴/(384EI) ≤ L/360
        # Giải ra: L³ = 384EI/(180q×joist_spacing)
        q_joist = q * joist_spacing  # kN/m

        # Iterate to find optimal span
        optimal_span = 0.9  # Start with 0.9m
        for _ in range(50):
            delta = 5 * q_joist * 1000 * optimal_span**4 / (384 * E * I) * 1000  # mm
            delta_allow = optimal_span * 1000 / 360
            if delta <= delta_allow:
                break
            optimal_span *= 0.95

        # Use 2x timber 50x100 for better performance
        I = 2 * I
        Z = 2 * Z

        joist_span = round(min(optimal_span, 1.5), 2)

        q_joist = q * joist_spacing  # kN/m

        M = q_joist * joist_span**2 / 8  # kNm
        sigma = (M * 1000.0) / Z / 1e6  # MPa [FIX BUG-STR-07a]

        delta = 5 * q_joist * 1000 * joist_span**4 / (384 * E * I) * 1000  # mm
        delta_allow = joist_span * 1000 / 360

        eta = max(sigma / prop["sigma"], delta / delta_allow)

        return {
            "type": "2×Timber 50x100mm (ghép)",
            "span": joist_span,
            "spacing": joist_spacing,
            "stress": sigma,
            "deflection": delta,
            "deflection_allow": delta_allow,
            "eta": eta
        }

    def design_primary_beam(self, q: float, beam_span: float) -> Dict:
        """Thiết kế dầm chính (primary beam)"""
        # Steel I-beam H150x75
        prop = STEEL_BEAMS["H150x75"]
        E = 210e9  # Pa
        I = prop["Ix"]
        Z = prop["Sx"]
        sigma_allow = 210e6  # Pa

        # [FIX BUG-STR-07a]: Tải phân bố trên dầm chính q_beam = q * beam_spacing (kN/m)
        beam_spacing = 1.2  # typical primary beam spacing (m)
        q_beam = q * beam_spacing  # kN/m

        M = q_beam * beam_span**2 / 8  # kNm
        sigma = (M * 1000.0) / Z / 1e6  # MPa

        delta = 5 * q_beam * 1000 * beam_span**4 / (384 * E * I) * 1000  # mm
        delta_allow = beam_span * 1000 / 360

        eta = max(sigma / 210, delta / delta_allow)

        return {
            "type": "Steel H150x75",
            "span": beam_span,
            "stress": sigma,
            "deflection": delta,
            "deflection_allow": delta_allow,
            "eta": eta
        }

    def optimize_plywood_span(self, q: float) -> float:
        """Tối ưu khoảng cách joist"""
        ply_data = PLYWOOD_TYPES.get(f"{self.plywood_thickness}mm", PLYWOOD_TYPES["18mm"])
        E = ply_data["E"] * 1e6
        I = ply_data["I"] * 1e-9

        L = 0.6
        for _ in range(50):
            delta = 5 * (q * 1000.0) * L**4 / (384 * E * I)
            if delta <= L / 360:
                break
            L *= 0.95
        return round(L, 2)

    def design_shores(self, q_total: float, floor_height: float = 3.0) -> Dict:
        """Thiết kế cây chống"""
        # Primary beam spacing determines shore spacing
        shore_spacing_trans = 1.2  # m
        shore_spacing_long = 1.8    # m

        shore_area = shore_spacing_trans * shore_spacing_long
        P_shore = q_total * shore_area

        # Acrow prop capacity based on height
        if floor_height <= 3.0:
            capacity = 35.0
        elif floor_height <= 3.5:
            capacity = 30.0
        elif floor_height <= 4.0:
            capacity = 22.0
        else:
            capacity = 15.0

        eta = P_shore / capacity

        # Number of shores for 1m² of slab
        num_per_m2 = 1 / shore_area

        return {
            "spacing_transverse": shore_spacing_trans,
            "spacing_longitudinal": shore_spacing_long,
            "area_per_shore": shore_area,
            "load_per_shore": P_shore,
            "capacity": capacity,
            "eta": eta,
            "shores_per_m2": round(num_per_m2, 2)
        }

    def design(self) -> FormworkDesignResult:
        """Chạy thiết kế hoàn chỉnh"""

        loads = self.calculate_loads()
        q = loads["q_total"]

        # Plywood design
        ply_result = self.design_plywood(q)

        # Joist design (spans between primary beams)
        # design_joist calculates optimal span internally
        joist_result = self.design_joist(q, 1.0)  # dummy value - joist calculates its own span

        # Primary beam span = joist_span from joist_result
        primary_span = joist_result["span"]
        primary_result = self.design_primary_beam(q, primary_span)

        # Shore design
        shore_result = self.design_shores(q)

        # Compile results
        warnings = []
        recommendations = []

        all_eta = [
            ("Plywood", ply_result["eta"]),
            ("Joist", joist_result["eta"]),
            ("Primary beam", primary_result["eta"]),
            ("Shore", shore_result["eta"])
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

        return FormworkDesignResult(
            slab_thickness=self.slab_thickness,
            slab_span=self.slab_span,
            concrete_grade=self.concrete_grade,
            formwork_type=self.formwork_type,
            plywood_thickness=self.plywood_thickness,
            concrete_load=loads["q_concrete"],
            formwork_weight=loads["q_formwork"],
            construction_load=loads["q_construction"],
            total_load_DL=loads["q_DL"],
            total_load=loads["q_total"],
            plywood_span=ply_result["span"],
            plywood_stress=ply_result["stress"],
            plywood_deflection=ply_result["deflection"],
            eta_plywood=ply_result["eta"],
            joist_type=joist_result["type"],
            joist_span=joist_result["span"],
            joist_spacing=joist_result["spacing"],
            joist_stress=joist_result["stress"],
            joist_deflection=joist_result["deflection"],
            eta_joist=joist_result["eta"],
            primary_beam_type=primary_result["type"],
            primary_beam_span=primary_result["span"],
            primary_beam_stress=primary_result["stress"],
            primary_beam_deflection=primary_result["deflection"],
            eta_primary=primary_result["eta"],
            shore_spacing_transverse=shore_result["spacing_transverse"],
            shore_spacing_longitudinal=shore_result["spacing_longitudinal"],
            shore_area=shore_result["area_per_shore"],
            shore_load=shore_result["load_per_shore"],
            shore_capacity=shore_result["capacity"],
            eta_shore=shore_result["eta"],
            num_shores=shore_result["shores_per_m2"],
            all_pass=all_pass,
            warnings=warnings,
            recommendations=recommendations,
            standard_method="ACI 347-04 / TCVN 4453:1995",
            calculation_logs=self.logs
        )

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
    """Slab formwork parametric calculator and multi-spacing optimizer"""

    MATERIALS = {
        "plywood_18mm": {
            "E": 9000,
            "f_m": 12,
            "f_v": 1.5,
            "I": 437.4,
            "W": 48.6,
            "weight": 0.18 * 7.5,
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
            "E": 10000,
            "f_m": 12,
            "f_v": 1.5,
            "gamma": 5.5,
        },
        "steel_i150": {
            "E": 210000,
            "f_y": 250,
            "I_x": 1273.7,
            "W_x": 170.7,
            "S_x": 194.1,
            "A": 19.14,
            "t_w": 4.5,
            "h": 150,
            "weight": 15.0,
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

    GAMMA_DEAD = 1.2
    GAMMA_LIVE = 1.5

    LIMITS = {
        "panel": "L/270",
        "joist": "L/360",
        "soldier": "L/400",
        "shore": "L/500"
    }

    def __init__(self, thickness_mm: float, span_m: float, concrete_grade: str,
                 construction_load: float = 1.5, timber_spacing: Optional[List[float]] = None):
        self.thickness_mm = thickness_mm
        self.span_m = span_m
        self.concrete_grade = concrete_grade
        self.construction_load = construction_load
        self.timber_spacing = timber_spacing or [450, 600, 750, 900]
        self.gamma_concrete = 25.0
        self.f_c = self._get_concrete_strength(concrete_grade)
        self.logs: List[CalcLog] = []

    def _get_concrete_strength(self, grade: str) -> float:
        grade_map = {
            "B15": 12.5, "B20": 17.0, "B25": 21.0, "B30": 26.0,
            "B35": 30.0, "B40": 34.0, "B45": 39.0, "B50": 44.0
        }
        return grade_map.get(grade, 21.0)

    def _log(self, step: int, desc: str, formula: str,
             inputs: dict, result: float, unit: str, standard: str = "TCVN 5575:2024"):
        self.logs.append(CalcLog(step, desc, formula, inputs, result, unit, standard))

    def calculate_panel_load(self) -> dict:
        step = 1
        q_dead = self.gamma_concrete * self.thickness_mm / 1000
        q_plywood = self.MATERIALS["plywood_18mm"]["weight"]

        self._log(
            step, "Dead load on panel",
            "q_dead = γ_bt × t + γ_plywood",
            {"γ_bt": self.gamma_concrete, "t_mm": self.thickness_mm, "γ_plywood": q_plywood},
            q_dead, "kN/m²"
        )

        q_live = self.construction_load
        self._log(
            step + 1, "Construction load",
            "q_live = 1.5 kN/m² (default)",
            {"q_tc": q_live},
            q_live, "kN/m²"
        )

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
        step = 10
        mat = self.MATERIALS[f"plywood_{thickness_mm}mm"]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        q_N_mm = q / 1000
        L = span_mm
        M = q_N_mm * L**2 / 8

        t = thickness_mm
        Z = t**2 / 6
        sigma = M / Z * 1000

        self._log(
            step, "Plywood bending stress",
            "σ = M / Z",
            {"M": M, "Z": Z, "L_mm": L},
            sigma, "MPa"
        )

        f_m = mat["f_m"]
        eta_bending = sigma / f_m

        V = q_N_mm * L / 2
        I = t**3 / 12
        Q = t**2 / 8
        tau = V * Q / (I * t) * 1000

        self._log(
            step + 1, "Plywood shear stress",
            "τ = V × Q / (I × t)",
            {"V": V, "Q": Q, "I": I},
            tau, "MPa"
        )

        f_v = mat["f_v"]
        eta_shear = tau / f_v

        E = mat["E"]
        I_mm = t**3 / 12
        delta = 5 * q_N_mm * L**4 / (384 * E * I_mm)

        self._log(
            step + 2, "Plywood deflection",
            "δ = 5qL⁴ / (384EI)",
            {"q": q, "L": L, "E": E, "I": I_mm},
            delta, "mm"
        )

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
        step = 20
        mat = self.MATERIALS["timber_joist"]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        w = q * spacing_mm / 1000

        self._log(
            step, "Load on timber joist",
            "w = q × S",
            {"q": q, "S": spacing_mm},
            w, "kN/m"
        )

        b, h = joist_size_mm
        L = span_m * 1000

        M = w * span_m / 8 * 1000
        Z = b * h**2 / 6
        sigma = M / Z
        f_m = mat["f_m"]
        eta_bending = sigma / f_m

        self._log(
            step + 1, "Timber joist bending",
            "σ = M / Z",
            {"M_Nmm": M, "Z": Z},
            sigma, "MPa"
        )

        V = w * span_m / 2
        A = b * h
        tau = V * 1000 / A
        f_v = mat["f_v"]
        eta_shear = tau / f_v

        self._log(
            step + 2, "Timber joist shear",
            "τ = V / A",
            {"V": V * 1000, "A": A},
            tau, "MPa"
        )

        E = mat["E"]
        I = b * h**3 / 12
        w_N_mm = w * 1000 / 1000
        L_mm = L

        delta = 5 * w_N_mm * L_mm**4 / (384 * E * I)
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
        step = 30
        mat = self.MATERIALS[steel_type]
        loads = self.calculate_panel_load()
        q = loads["q_design"]

        w = q * spacing_mm / 1000

        self._log(
            step, "Load on soldier beam",
            "w = q × S",
            {"q": q, "S": spacing_mm},
            w, "kN/m"
        )

        L = span_m
        M = w * L**2 / 8
        W_x = mat["W_x"] * 1000
        f_y = mat["f_y"]
        gamma_M0 = GAMMA_M0
        f = f_y / gamma_M0

        sigma = M * 1e6 / W_x

        self._log(
            step + 1, "Steel soldier bending",
            "σ = M / W_x ≤ f_y/γ_M0",
            {"M": M, "W_x": W_x, "f": f},
            sigma, "MPa"
        )

        eta_bending = sigma / f

        V = w * L / 2
        A = mat["A"] * 100
        t_w = mat["t_w"]

        tau = V * 1000 / (mat["h"] * t_w)
        f_v = 0.58 * f_y / gamma_M0

        self._log(
            step + 2, "Steel soldier shear",
            "τ = V / (h × t_w)",
            {"V": V, "h": mat["h"], "t_w": t_w},
            tau, "MPa"
        )

        eta_shear = tau / f_v

        E = mat["E"]
        I_x = mat["I_x"] * 1e4

        delta = 5 * w * 1000 * (L * 1000)**3 / (384 * E * I_x) / 1000
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

        for spacing in self.timber_spacing:
            check = self.check_plywood_panel(spacing_mm=spacing, span_mm=spacing)
            check["spacing_mm"] = spacing
            results["panel_check"][str(spacing)] = check

            for size in [(50, 100), (50, 150), (80, 120)]:
                joist_check = self.check_timber_joist(
                    spacing_mm=spacing,
                    joist_size_mm=size,
                    span_m=self.span_m
                )
                joist_check["joist_size_mm"] = size
                results["joist_checks"].append(joist_check)

        for spacing in [1200, 1500, 1800, 2100]:
            for steel in ["steel_i150", "steel_i200"]:
                soldier_check = self.check_steel_soldier(
                    spacing_mm=spacing,
                    steel_type=steel,
                    span_m=self.span_m
                )
                soldier_check["spacing_mm"] = spacing
                results["soldier_checks"].append(soldier_check)

        recommended = self._find_recommended(results)
        results["recommended"] = recommended
        results["calculation_logs"] = [asdict(log) for log in self.logs]
        results["Calculation_Logs"] = results["calculation_logs"]
        results["Standard_Method"] = "ACI 347-04 / TCVN 4453:1995"
        return results

    def _find_recommended(self, results: dict) -> dict:
        passing_joists = [
            j for j in results["joist_checks"]
            if j["bending"]["status"] == "PASS"
            and j["shear"]["status"] == "PASS"
            and j["deflection"]["status"] == "PASS"
        ]

        if passing_joists:
            best_joist = min(passing_joists, key=lambda x: x["bending"]["eta"])
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


def calc_slab_formwork(thickness: float = 200, span: float = 5.0,
                       grade: str = "B25", plywood: int = 18,
                       construction_load: float = 1.5) -> dict:
    """Wrapper function cho thiết kế cốp pha sàn."""
    designer = SlabFormworkDesigner(
        slab_thickness=thickness,
        slab_span=span,
        concrete_grade=grade.upper(),
        plywood_thickness=plywood,
        construction_load=construction_load
    )
    result = designer.design()
    return result.to_dict()


# ============================================================================
# CLI
# ============================================================================

def print_result(result: FormworkDesignResult, verbose: bool = False):
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ORANGE = "\033[38;5;214m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{'=' * 70}")
    print(f"{BOLD}THIẾT KẾ CỐP PHA SÀN{RESET}")
    print(f"{'─' * 70}")

    status_color = GREEN if result.all_pass else RED
    status_text = "✅ ĐẠT YÊU CẦU" if result.all_pass else "❌ KHÔNG ĐẠT"

    print(f"\nTrạng thái: {status_color}{status_text}{RESET}")
    print(f"Tiêu chuẩn: {result.standard_method}")

    print(f"\n{BOLD}📥 ĐẦU VÀO:{RESET}")
    print(f"  Sàn dày: {result.slab_thickness} mm")
    print(f"  Nhịp sàn: {result.slab_span} m")
    print(f"  Mác bê tông: {result.concrete_grade}")

    print(f"\n{BOLD}📐 TẢI TRỌNG:{RESET}")
    print(f"  Tĩnh tải bê tông: {result.concrete_load:.2f} kN/m²")
    print(f"  Tĩnh tải cốp pha: {result.formwork_weight:.2f} kN/m²")
    print(f"  Hoạt tải thi công: {result.construction_load:.2f} kN/m²")
    print(f"  Tổng tải trọng: {result.total_load:.2f} kN/m²")

    print(f"\n{BOLD}📊 KẾT QUẢ THIẾT KẾ:{RESET}")

    def print_eta(name, eta):
        c = GREEN if eta <= 0.7 else (YELLOW if eta <= 0.9 else (ORANGE if eta <= 1.0 else RED))
        return f"  {c}η = {eta:.3f}{RESET}"

    print(f"\n  Plywood ({result.plywood_thickness}mm):")
    print(f"    Khoảng cách joist: {result.plywood_span:.2f} m")
    print(f"    Ứng suất: {result.plywood_stress:.3f} MPa")
    print(f"    Độ võng: {result.plywood_deflection:.2f} / {result.plywood_span*1000/360:.2f} mm")
    print(f"    {print_eta('Plywood', result.eta_plywood)}")

    print(f"\n  Joist ({result.joist_type}):")
    print(f"    Nhịp: {result.joist_span:.2f} m")
    print(f"    Cự ly: {result.joist_spacing:.2f} m")
    print(f"    Ứng suất: {result.joist_stress:.2f} MPa")
    print(f"    Độ võng: {result.joist_deflection:.2f} / {result.joist_span*1000/360:.2f} mm")
    print(f"    {print_eta('Joist', result.eta_joist)}")

    print(f"\n  Dầm chính ({result.primary_beam_type}):")
    print(f"    Nhịp: {result.primary_beam_span:.2f} m")
    print(f"    Ứng suất: {result.primary_beam_stress:.2f} MPa")
    print(f"    Độ võng: {result.primary_beam_deflection:.2f} / {result.primary_beam_span*1000/360:.2f} mm")
    print(f"    {print_eta('Primary', result.eta_primary)}")

    print(f"\n  Cây chống:")
    print(f"    Cự ly (ngang×dọc): {result.shore_spacing_transverse}×{result.shore_spacing_longitudinal} m")
    print(f"    Tải/shore: {result.shore_load:.2f} kN")
    print(f"    Công suất: {result.shore_capacity:.1f} kN")
    print(f"    Số lượng: ~{result.num_shores:.1f} cái/m²")
    print(f"    {print_eta('Shore', result.eta_shore)}")

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
    parser = argparse.ArgumentParser(description="Thiết kế cốp pha sàn (Slab Formwork Design & Optimization)")
    parser.add_argument("--thickness", "-t", type=float, required=True, help="Chiều dày sàn (mm)")
    parser.add_argument("--span", "-s", type=float, required=True, help="Nhịp sàn / joist span (m)")
    parser.add_argument("--grade", "-g", default="B30", help="Mác bê tông")
    parser.add_argument("--plywood", "-p", type=int, default=18, help="Chiều dày plywood (mm)")
    parser.add_argument("--construction-load", "-c", type=float, default=1.5, help="Hoạt tải thi công (kN/m²)")
    parser.add_argument("--optimize", action="store_true", help="Chạy quét tối ưu đa phương án sườn & dầm")
    parser.add_argument("--spacing", nargs="+", type=float, help="Danh sách cự ly sườn kiểm tra (mm)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Chi tiết")

    args = parser.parse_args()

    if args.optimize:
        calc = SlabFormworkCalculator(
            thickness_mm=args.thickness,
            span_m=args.span,
            concrete_grade=args.grade.upper(),
            construction_load=args.construction_load,
            timber_spacing=args.spacing
        )
        opt_results = calc.optimize()
        if args.json or args.output:
            json_str = json.dumps(opt_results, indent=2, ensure_ascii=False)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(json_str)
                print(f"✓ Kết quả lưu: {args.output}")
            if args.json or not args.output:
                print(json_str)
        else:
            print("\n" + "="*60)
            print("KẾT QUẢ QUÉT TỐI ƯU CỐP PHA SÀN")
            print("="*60)
            rec = opt_results.get("recommended", {})
            if rec.get("type") != "FAIL":
                print(f"✓ Phương án tối ưu: {rec.get('type')}")
                print(f"  Tiết diện sườn: {rec.get('joist_size_mm')}")
                print(f"  Khoảng cách: {rec.get('spacing_mm')} mm")
                print(f"  Hệ số η: {rec.get('eta_overall', 0):.3f}")
            else:
                print("❌ Không tìm thấy cấu hình thỏa mãn")
        return

    designer = SlabFormworkDesigner(
        slab_thickness=args.thickness,
        slab_span=args.span,
        concrete_grade=args.grade.upper(),
        plywood_thickness=args.plywood,
        construction_load=args.construction_load
    )
    result = designer.design()

    if args.json:
        json_str = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"✓ Kết quả lưu: {args.output}")
        else:
            print(json_str)
    else:
        print_result(result, verbose=args.verbose)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

