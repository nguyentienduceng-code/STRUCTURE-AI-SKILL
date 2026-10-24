#!/usr/bin/env python3
"""
calc_crack_width.py — Kiểm tra bề rộng khe nứt BTCT theo TCVN 5574:2018
======================================================================
Script kiểm tra bề rộng khe nứt cho cấu kiện BTCT chịu uốn, kéo lệch tâm.

Tiêu chuẩn: TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép (Mục 8.2.2)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Tuple

# [FIX BUG-STR-02b]: Bảng cường độ chịu kéo tính toán Rbt (MPa) & tiêu chuẩn Rbt,ser (MPa) đúng TCVN 5574:2018 Bảng 6 & 7
CONCRETE_RBT = {
    "B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15,
    "B35": 1.30, "B40": 1.40, "B45": 1.50, "B50": 1.60
}

CONCRETE_RBT_SER = {
    "B15": 1.10, "B20": 1.35, "B25": 1.55, "B30": 1.75,
    "B35": 1.95, "B40": 2.10, "B45": 2.25, "B50": 2.45
}

REBAR_RS = {
    "CB240": 210, "CB240-T": 210,
    "CB300": 260, "CB300-T": 260, "CB300-V": 260,
    "CB350": 300,
    "CB400": 350, "CB400-V": 350,
    "CB500": 435, "CB500-V": 435,
}

REBAR_RS_SER = {
    "CB240": 240, "CB240-T": 240,
    "CB300": 300, "CB300-T": 300, "CB300-V": 300,
    "CB350": 350,
    "CB400": 400, "CB400-V": 400,
    "CB500": 500, "CB500-V": 500,
}

CONCRETE_EB = {
    "B15": 24000, "B20": 27500, "B25": 30000, "B30": 32500,
    "B35": 34500, "B40": 36000, "B45": 37000, "B50": 38000
}

CRACK_WIDTH_LIMITS = {
    "normal": 0.4,
    "corrosive": 0.3,
    "very_corrosive": 0.2,
    "indoor_normal": 0.4,
    "indoor_wet": 0.3,
    "outdoor": 0.3,
    "chemical": 0.2
}


@dataclass
class SectionGeometry:
    b: float
    h: float
    a_bottom: float
    a_top: float

    @property
    def h0_bottom(self) -> float:
        return self.h - self.a_bottom

    @property
    def h0_top(self) -> float:
        return self.h - self.a_top


@dataclass
class MaterialProperties:
    concrete_grade: str
    rebar_grade: str

    @property
    def Rbt(self) -> float:
        return CONCRETE_RBT.get(self.concrete_grade, 1.05)

    @property
    def Rbt_ser(self) -> float:
        return CONCRETE_RBT_SER.get(self.concrete_grade, 1.55)

    @property
    def Rs(self) -> float:
        return REBAR_RS.get(self.rebar_grade, 260)

    @property
    def Rs_ser(self) -> float:
        return REBAR_RS_SER.get(self.rebar_grade, 300)

    @property
    def Eb(self) -> float:
        return CONCRETE_EB.get(self.concrete_grade, 30000)


@dataclass
class ReinforcementInfo:
    As_bottom: float
    As_top: float
    rebar_bottom: str
    rebar_top: str
    phi_eff: float = 20.0


@dataclass
class LoadConditions:
    M_service: float
    N_service: float


def get_crack_limit(environment: str, humidity: float = 60) -> float:
    if environment in CRACK_WIDTH_LIMITS:
        return CRACK_WIDTH_LIMITS[environment]
    if humidity >= 75:
        return 0.3
    return 0.4


def parse_rebar_diameter(rebar_str: str) -> Tuple[float, int]:
    import re
    if not rebar_str:
        return 0.0, 0
    dia_match = re.search(r'[ØφΦD]?\s*(\d+)', rebar_str)
    dia = float(dia_match.group(1)) if dia_match else 0.0
    num_match = re.search(r'^(\d+)', rebar_str.strip())
    num = int(num_match.group(1)) if num_match else 1
    return dia, num


def calculate_effective_reinforcement_ratio(As: float, b: float, h0: float, a: float) -> float:
    h_eff = min(2.5 * a + 0.1 * h0, 0.5 * h0) if h0 > 0 else 0
    h_eff = max(min(h_eff, h0), 2.0 * a)
    if b * h_eff > 0:
        return As / (b * h_eff)
    return 0.0


def calculate_crack_width(
    sigma_s: float,
    phi_eff: float,
    l_s: float,
    Rbt_ser: float = 1.55,
    rebar_grade: str = "CB300-V",
    Es: float = 200000,
    long_term: bool = True,
) -> dict:
    """
    [FIX BUG-STR-02a]: Tính bề rộng khe nứt theo TCVN 5574:2018 Mục 8.2.2.2 Công thức (175):
      a_crc = φ1 * φ2 * φ3 * ψ_s * (σ_s / E_s) * L_s
    Trong đó:
      - φ1 = 1.4 (tác dụng dài hạn) hoặc 1.0 (ngắn hạn)
      - φ2 = 0.5 (cốt thép có gờ) hoặc 0.8 (cốt thép tròn trơn CB240-T)
      - φ3 = 1.0 (chịu uốn, kéo lệch tâm) hoặc 1.2 (chịu kéo đúng tâm)
      - ψ_s = 1 - 0.8 * (σ_s,crc / σ_s) ≈ 1.0 - 0.7 * (Rbt,ser / σ_s), giới hạn [0.2, 1.0]
    Khắc phục triệt để lỗi nhân nhầm với đường kính thanh thép φ_eff (mm) làm a_crc bị phóng đại 20 lần!
    """
    phi1 = 1.4 if long_term else 1.0
    phi2 = 0.8 if ("240" in rebar_grade or rebar_grade.endswith("-T")) else 0.5
    phi3 = 1.0

    if sigma_s > 0:
        psi = 1.0 - 0.7 * (Rbt_ser / sigma_s)
        psi = max(0.2, min(1.0, psi))
    else:
        psi = 1.0

    a_crc = phi1 * phi2 * phi3 * psi * (sigma_s / Es) * l_s

    return {
        "psi": round(psi, 3),
        "phi1": phi1,
        "phi2": phi2,
        "phi3": phi3,
        "a_crc": round(a_crc, 3),
        "phi_eff": phi_eff,
        "l_s": round(l_s, 1)
    }


def calculate_stress_in_steel(
    M: float, N: float, As: float, As_prime: float,
    b: float, h0: float, a_prime: float, Rb: float, Rs: float
) -> float:
    z = 0.85 * h0
    M_Nmm = M * 1e6
    sigma_M = M_Nmm / (As * z) if (As * z) > 0 else 0
    N_N = N * 1000
    sigma_N = N_N / As if As > 0 else 0
    return max(0.0, sigma_M + sigma_N)


def calculate_crack_spacing(
    phi_eff: float, s: float, a: float, h: float, mu_eff: float, As: float, b: float, h0: float
) -> float:
    """
    Tính khoảng cách cơ sở giữa các vết nứt L_s theo TCVN 5574:2018 Mục 8.2.2.2.3 CT (180):
      L_s = 0.5 * (A_bt / A_s) * d_s = 0.5 * d_s / μ_eff, giới hạn trong [10*d_s, 40*d_s] và [100mm, 400mm].
    """
    if mu_eff > 0 and phi_eff > 0:
        l_s = 0.5 * phi_eff / mu_eff
        l_s = max(l_s, 10.0 * phi_eff, 100.0)
        l_s = min(l_s, 40.0 * phi_eff, 400.0)
    else:
        l_s = min(max(s, 100.0), 400.0)
    return l_s


def calculate_crack_width_check(input_data: dict) -> dict:
    start_time = datetime.now()
    logs = []
    structured_logs = []

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")

    project = input_data.get("project", {})
    geometry_data = input_data["geometry"]
    materials_data = input_data["materials"]
    reinforcement_data = input_data["reinforcement"]
    loads_data = input_data["loads"]
    environment_data = input_data.get("environment", {})

    geometry = SectionGeometry(
        b=geometry_data["b"],
        h=geometry_data["h"],
        a_bottom=geometry_data.get("a_bottom", 35),
        a_top=geometry_data.get("a_top", 35)
    )

    materials = MaterialProperties(
        concrete_grade=materials_data.get("concrete_grade", "B25"),
        rebar_grade=materials_data.get("rebar_grade", "CB300")
    )

    rebar_bottom = reinforcement_data.get("rebar_bottom", "")
    rebar_top = reinforcement_data.get("rebar_top", "")
    dia_bottom, num_bottom = parse_rebar_diameter(rebar_bottom)
    dia_top, num_top = parse_rebar_diameter(rebar_top)

    As_bottom = reinforcement_data.get("As_bottom", num_bottom * math.pi * (dia_bottom / 2) ** 2)
    As_top = reinforcement_data.get("As_top", num_top * math.pi * (dia_top / 2) ** 2)

    reinforcement = ReinforcementInfo(
        As_bottom=As_bottom,
        As_top=As_top,
        rebar_bottom=rebar_bottom,
        rebar_top=rebar_top,
        phi_eff=dia_bottom if dia_bottom > 0 else 20.0
    )

    loads = LoadConditions(
        M_service=loads_data["M_service"],
        N_service=loads_data.get("N_service", 0)
    )

    env_type = environment_data.get("type", "normal")
    humidity = environment_data.get("humidity", 60)

    sigma_s = calculate_stress_in_steel(
        M=loads.M_service, N=loads.N_service, As=As_bottom, As_prime=As_top,
        b=geometry.b, h0=geometry.h0_bottom, a_prime=geometry.a_top,
        Rb=materials.Rbt * 10, Rs=materials.Rs
    )
    structured_logs.append({
        "Step": 1,
        "Description": "Tính ứng suất trong cốt thép chịu kéo σ_s (SLS)",
        "Formula": "σ_s = M_ser / (A_s * 0.85 * h_0) + N_ser / A_s",
        "Substitution": f"M={loads.M_service} kNm, As={As_bottom:.1f} mm², h0={geometry.h0_bottom} mm",
        "Result": f"σ_s = {sigma_s:.1f} MPa",
        "Citation": "TCVN 5574:2018 Mục 8.2.2.2.2"
    })

    mu_eff = calculate_effective_reinforcement_ratio(
        As=As_bottom, b=geometry.b, h0=geometry.h0_bottom, a=geometry.a_bottom
    )
    s = geometry.b / num_bottom if (num_bottom > 0 and geometry.b > 0) else 150.0
    l_s = calculate_crack_spacing(
        phi_eff=reinforcement.phi_eff, s=s, a=geometry.a_bottom,
        h=geometry.h, mu_eff=mu_eff, As=As_bottom, b=geometry.b, h0=geometry.h0_bottom
    )
    structured_logs.append({
        "Step": 2,
        "Description": "Tính khoảng cách cơ sở giữa các vết nứt L_s",
        "Formula": "L_s = 0.5 * (A_bt / A_s) * d_s, giới hạn [10*d_s, 40*d_s] & [100, 400] mm",
        "Substitution": f"d_s={reinforcement.phi_eff} mm, μ_eff={mu_eff:.4f}",
        "Result": f"L_s = {l_s:.1f} mm",
        "Citation": "TCVN 5574:2018 Mục 8.2.2.2.3 CT (180)"
    })

    crack_result = calculate_crack_width(
        sigma_s=sigma_s,
        phi_eff=reinforcement.phi_eff,
        l_s=l_s,
        Rbt_ser=materials.Rbt_ser,
        rebar_grade=materials.rebar_grade,
        Es=200000
    )
    a_crc_limit = get_crack_limit(env_type, humidity)
    passed = crack_result['a_crc'] <= a_crc_limit
    utilization = crack_result['a_crc'] / a_crc_limit if a_crc_limit > 0 else 0

    structured_logs.append({
        "Step": 3,
        "Description": "Tính bề rộng vết nứt a_crc theo TCVN 5574:2018 CT (175)",
        "Formula": "a_crc = φ1 * φ2 * φ3 * ψ_s * (σ_s / E_s) * L_s <= [a_crc]",
        "Substitution": f"φ1={crack_result['phi1']}, φ2={crack_result['phi2']}, φ3={crack_result['phi3']}, ψ_s={crack_result['psi']}, σ_s={sigma_s:.1f} MPa, L_s={l_s:.1f} mm",
        "Result": f"a_crc = {crack_result['a_crc']:.3f} mm vs [a_crc] = {a_crc_limit} mm (η = {utilization:.3f})",
        "Citation": "TCVN 5574:2018 Mục 8.2.2.2.1 CT (175)"
    })

    log(f"Tiết diện: b={geometry.b}mm, h={geometry.h}mm; σ_s={sigma_s:.1f}MPa; L_s={l_s:.1f}mm -> a_crc={crack_result['a_crc']:.3f}mm <= {a_crc_limit}mm ({'ĐẠT' if passed else 'KHÔNG ĐẠT'})")

    output = {
        "calculator": {
            "name": "calc_crack_width",
            "version": "1.1.0",
            "standard": "TCVN 5574:2018",
            "method": "Mục 8.2.2 — Tính toán chiều rộng vết nứt thẳng góc"
        },
        "metadata": {
            "project_name": project.get("name", "N/A"),
            "calculation_date": datetime.now().isoformat(),
            "designer": project.get("designer", "N/A"),
            "notes": project.get("notes", "")
        },
        "input_summary": {
            "geometry": {
                "b": geometry.b, "h": geometry.h,
                "a_bottom": geometry.a_bottom, "a_top": geometry.a_top,
                "h0_bottom": geometry.h0_bottom, "h0_top": geometry.h0_top
            },
            "materials": {
                "concrete_grade": materials.concrete_grade,
                "rebar_grade": materials.rebar_grade,
                "Rbt": materials.Rbt,
                "Rbt_ser": materials.Rbt_ser,
                "Rs": materials.Rs,
                "Eb": materials.Eb
            },
            "reinforcement": {
                "As_bottom": As_bottom, "As_top": As_top,
                "rebar_bottom": rebar_bottom, "rebar_top": rebar_top,
                "phi_eff": reinforcement.phi_eff
            },
            "loads": asdict(loads),
            "environment": {"type": env_type, "humidity": humidity}
        },
        "results": {
            "stress": {"sigma_s": round(sigma_s, 1), "unit": "MPa"},
            "crack_parameters": {
                "mu_eff": round(mu_eff, 5),
                "l_s": round(l_s, 1),
                "psi": crack_result['psi'],
                "phi1": crack_result['phi1'],
                "phi2": crack_result['phi2'],
                "phi3": crack_result['phi3'],
            },
            "crack_width": {
                "a_crc": crack_result['a_crc'],
                "a_crc_limit": a_crc_limit,
                "passed": passed,
                "utilization": round(utilization, 3)
            }
        },
        "summary": {
            "conclusion": "ĐẠT" if passed else "KHÔNG ĐẠT",
            "crack_width": f"{crack_result['a_crc']:.3f} mm",
            "crack_limit": f"{a_crc_limit} mm",
            "utilization": f"{utilization * 100:.1f}%"
        },
        "conclusion": {
            "status": "PASSED" if passed else "FAILED",
            "message": f"Bề rộng khe nứt {crack_result['a_crc']:.3f}mm {'nhỏ hơn hoặc bằng' if passed else 'lớn hơn'} giới hạn {a_crc_limit}mm.",
            "recommendations": [
                f"Ứng suất cốt thép: {sigma_s:.1f}MPa",
                "Cần giảm ứng suất bằng cách tăng As hoặc tăng h" if not passed else "Ứng suất cốt thép và bề rộng vết nứt trong giới hạn cho phép",
                f"Cốt thép hiện tại: {rebar_bottom}"
            ]
        },
        # [FIX BUG-STR-02c]: Bổ sung Calculation_Logs và Standard_Method ở root theo AGENTS.md §5
        "Calculation_Logs": structured_logs,
        "Standard_Method": "TCVN 5574:2018",
        "calculation_log": logs,
        "standard_references": [
            "TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép (Mục 8.2.2)"
        ]
    }
    return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Kiểm tra bề rộng khe nứt BTCT theo TCVN 5574:2018")
    parser.add_argument("--input", "-i", required=True, help="File JSON đầu vào")
    parser.add_argument("--output", "-o", help="File JSON đầu ra (mặc định: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Định dạng JSON đẹp")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    result = calculate_crack_width_check(input_data)
    json_str = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
