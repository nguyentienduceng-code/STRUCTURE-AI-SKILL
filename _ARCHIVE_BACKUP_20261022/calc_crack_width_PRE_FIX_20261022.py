#!/usr/bin/env python3
"""
calc_crack_width.py — Kiểm tra bề rộng khe nứt BTCT theo TCVN 5574:2018
======================================================================
Script kiểm tra bề rộng khe nứt cho cấu kiện BTCT chịu uốn, kéo lệch tâm.

Tiêu chuẩn: TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép
Phụ lục: Phụ lục F — Tính toán bề rộng khe nứt

Usage:
    python calc_crack_width.py --input data.json [--output result.json]

Input JSON:
{
    "project": {"name": "...", "date": "..."},
    "geometry": {
        "b": 200,        # Bề rộng tiết diện (mm)
        "h": 500,        # Chiều cao tiết diện (mm)
        "a_bottom": 35,  # Lớp bảo vệ cốt thép dưới (mm)
        "a_top": 35      # Lớp bảo vệ cốt thép trên (mm)
    },
    "materials": {
        "concrete_grade": "B25",
        "rebar_grade": "CB300"
    },
    "reinforcement": {
        "As_bottom": 628,    # Diện tích cốt thép dưới (mm2)
        "As_top": 0,         # Diện tích cốt thép trên (mm2)
        "rebar_bottom": "2Ø20",  # Thông số cốt thép dưới
        "rebar_top": ""      # Thông số cốt thép trên
    },
    "loads": {
        "M_service": 120,    # Moment tại SLS (kNm)
        "N_service": 0       # Lực dọc tại SLS (kN)
    },
    "environment": {
        "type": "normal",    # normal | corrosive | very_corrosive
        "humidity": 60       # Độ ẩm tương đối (%)
    }
}

Output JSON: xem CALCULATOR_OUTPUT_STANDARD.md
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Tuple

# =============================================================================
# CONSTANTS & MATERIAL PROPERTIES
# =============================================================================

# Cường độ chịu kéo tính toán của bê tông Rbt (MPa) — TCVN 5574:2018 Bảng 3.1
CONCRETE_RBT = {
    "B15": 0.75, "B20": 1.00, "B25": 1.15, "B30": 1.30,
    "B35": 1.45, "B40": 1.60, "B45": 1.70, "B50": 1.80
}

# Cường độ chịu kéo tính toán của cốt thép Rs (MPa)
REBAR_RS = {
    "CB240": 210, "CB300": 260, "CB350": 300, "CB400": 350, "CB500": 415
}

# Cường độ chịu kéo tiêu chuẩn R_s,ser (MPa)
REBAR_RS_SER = {
    "CB240": 240, "CB300": 300, "CB350": 350, "CB400": 400, "CB500": 500
}

# Mô đun đàn hồi bê tông Eb (MPa)
CONCRETE_EB = {
    "B15": 21000, "B20": 24500, "B25": 27500, "B30": 30000,
    "B35": 31500, "B40": 32500, "B45": 33500, "B50": 34500
}

# Giới hạn bề rộng khe nứt a_crc (mm) — TCVN 5574:2018 Bảng 6.1
CRACK_WIDTH_LIMITS = {
    "normal": 0.4,         # Môi trường bình thường
    "corrosive": 0.3,      # Môi trường ăn mòn nhẹ
    "very_corrosive": 0.2, # Môi trường ăn mòn mạnh
    "indoor_normal": 0.4,  # Trong nhà, độ ẩm trung bình
    "indoor_wet": 0.3,    # Trong nhà, độ ẩm cao
    "outdoor": 0.3,        # Ngoài trời
    "chemical": 0.2        # Môi trường hóa chất
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SectionGeometry:
    """Hình học tiết diện"""
    b: float           # Bề rộng (mm)
    h: float           # Chiều cao (mm)
    a_bottom: float    # Lớp bảo vệ cốt thép dưới (mm)
    a_top: float       # Lớp bảo vệ cốt thép trên (mm)

    @property
    def h0_bottom(self) -> float:
        """Chiều cao làm việc cốt thép dưới"""
        return self.h - self.a_bottom

    @property
    def h0_top(self) -> float:
        """Chiều cao làm việc cốt thép trên"""
        return self.h - self.a_top

@dataclass
class MaterialProperties:
    """Đặc trưng vật liệu"""
    concrete_grade: str
    rebar_grade: str

    @property
    def Rbt(self) -> float:
        return CONCRETE_RBT.get(self.concrete_grade, 1.15)

    @property
    def Rs(self) -> float:
        return REBAR_RS.get(self.rebar_grade, 260)

    @property
    def Rs_ser(self) -> float:
        return REBAR_RS_SER.get(self.rebar_grade, 300)

    @property
    def Eb(self) -> float:
        return CONCRETE_EB.get(self.concrete_grade, 27500)

@dataclass
class ReinforcementInfo:
    """Thông tin cốt thép"""
    As_bottom: float       # Diện tích cốt thép dưới (mm2)
    As_top: float          # Diện tích cốt thép trên (mm2)
    rebar_bottom: str      # Thông số thanh dưới
    rebar_top: str         # Thông số thanh trên
    phi_eff: float = 20.0  # Đường kính tương đương (mm)

@dataclass
class LoadConditions:
    """Điều kiện tải trọng"""
    M_service: float   # Moment tại SLS (kNm)
    N_service: float    # Lực dọc tại SLS (kN)

@dataclass
class CrackWidthResult:
    """Kết quả kiểm tra bề rộng khe nứt"""
    a_crc: float           # Bề rộng khe nứt tính toán (mm)
    a_crc_limit: float     # Bề rộng giới hạn (mm)
    passed: bool
    utilization: float     # Hệ số sử dụng η = a_crc / a_crc_limit

    # Chi tiết tính toán
    sigma_s: float         # Ứng suất trong cốt thép (MPa)
    l_s: float             # Khoảng cách giữa các vết nứt (mm)
    psi: float             # Hệ số phân bố ứng suất
    mu_eff: float          # Hàm lượng cốt thép hiệu quả

# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def get_crack_limit(environment: str, humidity: float = 60) -> float:
    """
    Xác định giới hạn bề rộng khe nứt theo môi trường.

    Theo TCVN 5574:2018 Bảng 6.1
    """
    # Nếu environment là một trong các giá trị định nghĩa sẵn
    if environment in CRACK_WIDTH_LIMITS:
        return CRACK_WIDTH_LIMITS[environment]

    # Xác định theo độ ẩm
    if humidity >= 75:
        return 0.3  # Môi trường ẩm
    elif humidity >= 60:
        return 0.4  # Môi trường bình thường
    else:
        return 0.4  # Môi trường khô

def parse_rebar_diameter(rebar_str: str) -> Tuple[float, int]:
    """
    Phân tích chuỗi cốt thép.

    Input: "2Ø20" hoặc "Ø20@150" hoặc "2-D20"
    Returns: (đường kính mm, số lượng)
    """
    import re

    if not rebar_str:
        return 0.0, 0

    # Tìm đường kính
    dia_match = re.search(r'[ØφΦD]?\s*(\d+)', rebar_str)
    if dia_match:
        dia = float(dia_match.group(1))
    else:
        dia = 0.0

    # Tìm số lượng
    num_match = re.search(r'^(\d+)', rebar_str.strip())
    if num_match:
        num = int(num_match.group(1))
    else:
        num = 1

    return dia, num

def calculate_effective_reinforcement_ratio(
    As: float,
    b: float,
    h0: float,
    a: float
) -> float:
    """
    Tính hàm lượng cốt thép hiệu quả.

    μ_eff = As / (b * h_eff)

    Trong đó h_eff là chiều cao vùng kéo hiệu quả
    """
    h_eff = min(2.5 * a + 0.1 * h0, 0.5 * h0 + 0.1 * h0) if h0 > 0 else 0
    h_eff = min(h_eff, h0)

    if b * h_eff > 0:
        return As / (b * h_eff)
    return 0

def calculate_crack_width(
    sigma_s: float,
    phi_eff: float,
    l_s: float,
    Es: float = 200000
) -> dict:
    """
    Tính bề rộng khe nứt theo công thức TCVN 5574:2018.

    a_crc = ψ * φ_eff * σs * l_s / Es

    Trong đó:
    - ψ: Hệ số tính đến sự phân bố ứng suất trong cốt thép
    - φ_eff: Đường kính tương đương của cốt thép
    - σs: Ứng suất trong cốt thép
    - l_s: Khoảng cách giữa các vết nứt
    - Es: Mô đun đàn hồi cốt thép
    """
    # Hệ số ψ (TCVN 5574:2018 F.2)
    # ψ = 1.0 - 0.7 * (Rbt / σs) khi có nhiều thanh
    # ψ = 1.0 khi chỉ có 1-2 thanh
    if sigma_s > 0:
        psi = 1.0 - 0.7 * (1.15 / sigma_s)  # Giả định Rbt = 1.15 MPa cho B25
        psi = max(0.5, min(1.0, psi))
    else:
        psi = 1.0

    # Bề rộng khe nứt
    a_crc = (psi * phi_eff * sigma_s * l_s) / Es

    return {
        "psi": round(psi, 3),
        "a_crc": round(a_crc, 3),
        "phi_eff": phi_eff,
        "l_s": round(l_s, 1)
    }

def calculate_stress_in_steel(
    M: float,
    N: float,
    As: float,
    As_prime: float,
    b: float,
    h0: float,
    a_prime: float,
    Rb: float,
    Rs: float
) -> float:
    """
    Tính ứng suất trong cốt thép chịu kéo.

    Phương pháp gần đúng:
    σs = M / (As * z) + N / As

    Trong đó z = 0.85 * h0 là cánh tay đòn nội lực
    """
    z = 0.85 * h0  # Cánh tay đòn (mm)

    # Chuyển M từ kNm → Nmm
    M_Nmm = M * 1e6

    # Ứng suất từ moment
    sigma_M = M_Nmm / (As * z) if As > 0 else 0

    # Ứng suất từ lực dọc
    N_N = N * 1000  # kN → N
    sigma_N = N_N / As if As > 0 else 0

    return sigma_M + sigma_N

def calculate_crack_spacing(
    phi_eff: float,
    s: float,
    a: float,
    h: float,
    mu_eff: float
) -> float:
    """
    Tính khoảng cách giữa các vết nứt.

    l_s = 0.5 * s + 0.1 * φ_eff * (1 + 2 * a / h) / μ_eff

    Trong đó:
    - s: Bước cốt thép (mm)
    - a: Lớp bảo vệ (mm)
    - μ_eff: Hàm lượng cốt thép hiệu quả
    """
    # Hệ số kể đến lớp bảo vệ
    k1 = 1 + 2 * a / h if h > 0 else 1

    # Khoảng cách vết nứt
    if mu_eff > 0:
        l_s = 0.5 * s + 0.1 * phi_eff * k1 / mu_eff
    else:
        l_s = s  # Không có cốt thép, khoảng cách = bước cốt thép

    # Giới hạn khoảng cách
    l_s = min(l_s, 400)  # Không vượt quá 400mm

    return l_s

# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================

def calculate_crack_width_check(input_data: dict) -> dict:
    """
    Hàm chính kiểm tra bề rộng khe nứt.

    Returns: Dict theo CALCULATOR_OUTPUT_STANDARD
    """
    start_time = datetime.now()
    logs = []

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")

    # Parse input
    project = input_data.get("project", {})
    geometry_data = input_data["geometry"]
    materials_data = input_data["materials"]
    reinforcement_data = input_data["reinforcement"]
    loads_data = input_data["loads"]
    environment_data = input_data.get("environment", {})

    log(f"Bắt đầu kiểm tra bề rộng khe nứt: {project.get('name', 'N/A')}")

    # Create objects
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

    # Parse rebar info
    rebar_bottom = reinforcement_data.get("rebar_bottom", "")
    rebar_top = reinforcement_data.get("rebar_top", "")

    # Đường kính tương đương
    dia_bottom, num_bottom = parse_rebar_diameter(rebar_bottom)
    dia_top, num_top = parse_rebar_diameter(rebar_top)

    # Diện tích cốt thép
    As_bottom = reinforcement_data.get("As_bottom", num_bottom * math.pi * (dia_bottom/2)**2)
    As_top = reinforcement_data.get("As_top", num_top * math.pi * (dia_top/2)**2)

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

    # Môi trường
    env_type = environment_data.get("type", "normal")
    humidity = environment_data.get("humidity", 60)

    log(f"Tiết diện: b={geometry.b}mm, h={geometry.h}mm")
    log(f"Vật liệu: {materials.concrete_grade} (Rbt={materials.Rbt}MPa), "
        f"{materials.rebar_grade} (Rs={materials.Rs}MPa)")
    log(f"Cốt thép dưới: {rebar_bottom}, As={As_bottom:.1f}mm2")
    log(f"Moment SLS: M={loads.M_service}kNm, N={loads.N_service}kN")

    # Step 1: Calculate steel stress
    log("Tính ứng suất trong cốt thép...")

    sigma_s = calculate_stress_in_steel(
        M=loads.M_service,
        N=loads.N_service,
        As=As_bottom,
        As_prime=As_top,
        b=geometry.b,
        h0=geometry.h0_bottom,
        a_prime=geometry.a_top,
        Rb=materials.Rbt * 10,  # MPa → daN/cm2 (cho công thức)
        Rs=materials.Rs
    )

    log(f"Ứng suất cốt thép: σs = {sigma_s:.1f} MPa")

    # Step 2: Calculate effective reinforcement ratio
    log("Tính hàm lượng cốt thép hiệu quả...")

    mu_eff = calculate_effective_reinforcement_ratio(
        As=As_bottom,
        b=geometry.b,
        h0=geometry.h0_bottom,
        a=geometry.a_bottom
    )

    log(f"Hàm lượng cốt thép hiệu quả: μ_eff = {mu_eff:.4f} ({mu_eff*100:.2f}%)")

    # Step 3: Calculate crack spacing
    log("Tính khoảng cách giữa các vết nứt...")

    # Bước cốt thép (ước tính)
    if num_bottom > 0 and geometry.b > 0:
        s = geometry.b / num_bottom
    else:
        s = 150  # Mặc định 150mm

    l_s = calculate_crack_spacing(
        phi_eff=reinforcement.phi_eff,
        s=s,
        a=geometry.a_bottom,
        h=geometry.h,
        mu_eff=mu_eff
    )

    log(f"Khoảng cách vết nứt: ls = {l_s:.1f} mm")

    # Step 4: Calculate crack width
    log("Tính bề rộng khe nứt...")

    crack_result = calculate_crack_width(
        sigma_s=sigma_s,
        phi_eff=reinforcement.phi_eff,
        l_s=l_s,
        Es=200000  # MPa
    )

    log(f"Hệ số ψ = {crack_result['psi']:.3f}")
    log(f"Bề rộng khe nứt: a_crc = {crack_result['a_crc']:.3f} mm")

    # Step 5: Check against limit
    a_crc_limit = get_crack_limit(env_type, humidity)

    log(f"Giới hạn bề rộng khe nứt: [{a_crc_limit}] mm (môi trường: {env_type})")

    passed = crack_result['a_crc'] <= a_crc_limit
    utilization = crack_result['a_crc'] / a_crc_limit if a_crc_limit > 0 else 0

    log(f"\n{'='*50}")
    log(f"KẾT LUẬN: {'ĐẠT' if passed else 'KHÔNG ĐẠT'}")
    log(f"Bề rộng khe nứt: {crack_result['a_crc']:.3f} mm ≤ {a_crc_limit} mm")
    log(f"Hệ số sử dụng: η = {utilization:.3f}")
    log(f"Thời gian tính toán: {(datetime.now() - start_time).total_seconds():.2f}s")

    # Build output
    output = {
        "calculator": {
            "name": "calc_crack_width",
            "version": "1.0.0",
            "standard": "TCVN 5574:2018",
            "method": "Phụ lục F — Tính toán bề rộng khe nứt"
        },
        "metadata": {
            "project_name": project.get("name", "N/A"),
            "calculation_date": datetime.now().isoformat(),
            "designer": project.get("designer", "N/A"),
            "notes": project.get("notes", "")
        },
        "input_summary": {
            "geometry": {
                "b": geometry.b,
                "h": geometry.h,
                "a_bottom": geometry.a_bottom,
                "a_top": geometry.a_top,
                "h0_bottom": geometry.h0_bottom,
                "h0_top": geometry.h0_top
            },
            "materials": {
                "concrete_grade": materials.concrete_grade,
                "rebar_grade": materials.rebar_grade,
                "Rbt": materials.Rbt,
                "Rs": materials.Rs,
                "Eb": materials.Eb
            },
            "reinforcement": {
                "As_bottom": As_bottom,
                "As_top": As_top,
                "rebar_bottom": rebar_bottom,
                "rebar_top": rebar_top,
                "phi_eff": reinforcement.phi_eff
            },
            "loads": asdict(loads),
            "environment": {
                "type": env_type,
                "humidity": humidity
            }
        },
        "results": {
            "stress": {
                "sigma_s": round(sigma_s, 1),
                "unit": "MPa"
            },
            "crack_parameters": {
                "mu_eff": round(mu_eff, 5),
                "l_s": round(l_s, 1),
                "psi": crack_result['psi']
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
            "utilization": f"{utilization*100:.1f}%"
        },
        "conclusion": {
            "status": "PASSED" if passed else "FAILED",
            "message": f"Bề rộng khe nứt {crack_result['a_crc']:.3f}mm "
                      f"{'nhỏ hơn' if passed else 'lớn hơn'} giới hạn {a_crc_limit}mm. "
                      f"Kiểm tra {'đạt' if passed else 'không đạt'} yêu cầu.",
            "recommendations": [
                f"Ứng suất cốt thép: {sigma_s:.1f}MPa",
                f"Cần giảm ứng suất bằng cách tăng As hoặc tăng h"
                    if not passed and sigma_s > 200 else "Ứng suất cốt thép trong giới hạn cho phép",
                f"Cốt thép hiện tại: {rebar_bottom}"
            ]
        },
        "calculation_log": logs,
        "standard_references": [
            "TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép",
            "TCVN 5574:2018 Phụ lục F — Tính toán bề rộng khe nứt"
        ]
    }

    return output

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Kiểm tra bề rộng khe nứt BTCT theo TCVN 5574:2018"
    )
    parser.add_argument("--input", "-i", required=True, help="File JSON đầu vào")
    parser.add_argument("--output", "-o", help="File JSON đầu ra (mặc định: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Định dạng JSON đẹp")

    args = parser.parse_args()

    # Read input
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # Calculate
    result = calculate_crack_width_check(input_data)

    # Output
    json_str = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Đã lưu kết quả vào: {args.output}")
    else:
        print(json_str)

if __name__ == "__main__":
    main()
