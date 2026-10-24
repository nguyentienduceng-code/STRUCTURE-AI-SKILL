#!/usr/bin/env python3
"""
calc_slab.py — Tính toán sàn BTCT 2 phương theo TCVN 5574:2018
=============================================================
Script tính toán cốt thép sàn BTCT chịu uốn 2 phương (bản kê 4 cạnh).

Tiêu chuẩn: TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép
Phương pháp: Cường độ giới hạn (ULS) + Kiểm tra võng & nứt (SLS)
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
# CONSTANTS & MATERIAL PROPERTIES (TCVN 5574:2018 Bảng 7, Bảng 11, Bảng 13)
# =============================================================================

# Cường độ chịu nén tính toán của bê tông Rb (MPa) — TCVN 5574:2018 Bảng 7
CONCRETE_RB = {
    "B15": 8.5, "B20": 11.5, "B25": 14.5, "B30": 17.0,
    "B35": 19.5, "B40": 22.0, "B45": 25.0, "B50": 27.5
}

# [FIX BUG-STR-01a]: Cường độ chịu kéo tính toán Rbt (MPa) đúng theo TCVN 5574:2018 Bảng 7
CONCRETE_RBT = {
    "B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15,
    "B35": 1.30, "B40": 1.40, "B45": 1.50, "B50": 1.60
}

# Cường độ chịu kéo tiêu chuẩn Rbt,ser (MPa) — TCVN 5574:2018 Bảng 6 (dùng kiểm tra SLS nứt)
CONCRETE_RBT_SER = {
    "B15": 1.10, "B20": 1.35, "B25": 1.55, "B30": 1.75,
    "B35": 1.95, "B40": 2.10, "B45": 2.25, "B50": 2.45
}

# [FIX BUG-STR-01a]: Cường độ chịu kéo tính toán của cốt thép Rs (MPa) — TCVN 5574:2018 Bảng 13
# Hỗ trợ cả ký hiệu có và không có hậu tố -T / -V, sửa CB500 = 435 MPa
REBAR_RS = {
    "CB240": 210, "CB240-T": 210,
    "CB300": 260, "CB300-T": 260, "CB300-V": 260,
    "CB350": 300,
    "CB400": 350, "CB400-V": 350,
    "CB500": 435, "CB500-V": 435,
}

# Cường độ chịu kéo tiêu chuẩn của cốt thép Rs,ser (MPa) — TCVN 5574:2018 Bảng 12
REBAR_RS_SER = {
    "CB240": 240, "CB240-T": 240,
    "CB300": 300, "CB300-T": 300, "CB300-V": 300,
    "CB350": 350,
    "CB400": 400, "CB400-V": 400,
    "CB500": 500, "CB500-V": 500,
}

# [FIX BUG-STR-01a]: Mô đun đàn hồi ban đầu của bê tông Eb (MPa) — TCVN 5574:2018 Bảng 11
CONCRETE_E = {
    "B15": 24000, "B20": 27500, "B25": 30000, "B30": 32500,
    "B35": 34500, "B40": 36000, "B45": 37000, "B50": 38000
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SlabGeometry:
    """Hình học sàn"""
    Lx: float       # Nhịp theo phương x (m)
    Ly: float       # Nhịp theo phương y (m)
    h: float        # Chiều dày sàn (m)
    a: float        # Lớp bảo vệ (m)
    b: float = 1.0  # Bề rộng dải bản tính toán (m)


@dataclass
class MaterialProperties:
    """Đặc trưng vật liệu theo TCVN 5574:2018"""
    concrete_grade: str
    rebar_grade: str
    gamma_m: float = 1.15

    @property
    def Rb(self) -> float:
        return CONCRETE_RB.get(self.concrete_grade, 14.5)

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
        return CONCRETE_E.get(self.concrete_grade, 30000)

    @property
    def xi_r(self) -> float:
        """
        [FIX BUG-STR-01a]: Chiều cao tương đối giới hạn vùng nén ξR theo TCVN 5574:2018 Mục 8.1.2.2.3:
        ξR = ω / (1 + ε_s,el / ε_b2), với ω = 0.8 (bê tông nặng cấp <= B60), ε_b2 = 0.0035, Es = 200000 MPa.
        """
        omega = 0.8
        eps_s_el = self.Rs / 200000.0
        eps_b2 = 0.0035
        return round(omega / (1.0 + eps_s_el / eps_b2), 4)

    @property
    def alpha_m(self) -> float:
        """
        [FIX BUG-STR-01a]: Hệ số giới hạn αR = ξR * (1 - 0.5 * ξR) theo TCVN 5574:2018 (~0.39 - 0.44).
        (Khắc phục lỗi cũ gán αR = 0.86 gây nguy cơ phá hoại giòn).
        """
        xi = self.xi_r
        return round(xi * (1.0 - 0.5 * xi), 4)


@dataclass
class LoadConditions:
    """Điều kiện tải trọng"""
    g_dl: float
    q_ll: float
    gamma_g: float = 1.2
    gamma_q: float = 1.3

    @property
    def q_uls(self) -> float:
        return self.gamma_g * self.g_dl + self.gamma_q * self.q_ll

    @property
    def q_sls(self) -> float:
        return self.g_dl + self.q_ll


@dataclass
class SlabMomentResult:
    """Kết quả tính moment"""
    M_x_pos: float
    M_x_neg: float
    M_y_pos: float
    M_y_neg: float


@dataclass
class ReinforcementResult:
    """Kết quả tính cốt thép"""
    As_x_pos: float
    As_x_neg: float
    As_y_pos: float
    As_y_neg: float
    rebar_x_pos: str
    rebar_x_neg: str
    rebar_y_pos: str
    rebar_y_neg: str
    eta_M: float


@dataclass
class DeflectionResult:
    """Kết quả kiểm tra võng"""
    f_calc: float
    f_allow: float
    eta_f: float
    passed: bool


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def get_boundary_coefficients(boundary: str) -> dict:
    if boundary == "simply_supported":
        return {"m1_pos": 1/11, "m2_pos": 1/16, "m1_neg": -1/11, "m2_neg": -1/16, "k": 0.8}
    elif boundary == "fixed_one":
        return {"m1_pos": 1/14, "m2_pos": 1/20, "m1_neg": -1/11, "m2_neg": -1/14, "k": 0.85}
    elif boundary == "fixed_all":
        return {"m1_pos": 1/16, "m2_pos": 1/22, "m1_neg": -1/14, "m2_neg": -1/16, "k": 0.9}
    else:
        raise ValueError(f"Boundary condition không hợp lệ: {boundary}")


def calculate_moments(
    geometry: SlabGeometry,
    loads: LoadConditions,
    boundary: str
) -> SlabMomentResult:
    """
    [FIX BUG-STR-01b]: Tính moment trong sàn 2 phương đúng cơ học bản kê 4 cạnh.
    Mọi moment bản 2 phương đều tỷ lệ với bình phương nhịp ngắn L_short^2 (L1 = min(Lx, Ly)):
      - Phương nhịp ngắn (L1): chịu moment lớn hơn M1 = m1 * q * L1^2
      - Phương nhịp dài (L2): chịu moment nhỏ hơn M2 = m2 * (L1/L2) * q * L1^2
    Nếu Lx <= Ly thì phương x là nhịp ngắn; nếu Ly < Lx thì phương y là nhịp ngắn.
    """
    q = loads.q_uls
    Lx = geometry.Lx
    Ly = geometry.Ly

    L_short = min(Lx, Ly)
    L_long = max(Lx, Ly)
    mu = L_short / L_long if L_long > 0 else 1.0

    coef = get_boundary_coefficients(boundary)

    if mu < 0.5:
        # Bản làm việc 1 phương theo phương nhịp ngắn
        M_short_pos = (1.0 / 8.0 if boundary == "simply_supported" else coef["m1_pos"]) * q * (L_short ** 2)
        M_long_pos = 0.20 * M_short_pos  # Cốt thép cấu tạo chịu phân phối (20% M_short)
    else:
        # Bản làm việc 2 phương
        M_short_pos = coef["m1_pos"] * q * (L_short ** 2)
        M_long_pos = coef["m2_pos"] * mu * q * (L_short ** 2)

    if Lx <= Ly:
        M_x_pos = M_short_pos
        M_y_pos = M_long_pos
    else:
        M_x_pos = M_long_pos
        M_y_pos = M_short_pos

    M_x_neg = coef["k"] * abs(M_x_pos)
    M_y_neg = coef["k"] * abs(M_y_pos)

    return SlabMomentResult(
        M_x_pos=round(M_x_pos, 3),
        M_x_neg=round(-M_x_neg, 3),
        M_y_pos=round(M_y_pos, 3),
        M_y_neg=round(-M_y_neg, 3)
    )


def calculate_reinforcement(
    M: float,
    geometry: SlabGeometry,
    materials: MaterialProperties,
    is_top: bool = False
) -> dict:
    """
    Tính diện tích cốt thép từ moment uốn theo TCVN 5574:2018.
    """
    b = geometry.b
    h0 = geometry.h - geometry.a if not is_top else geometry.h - geometry.a - 0.005

    Rb = materials.Rb
    Rs = materials.Rs
    xi_r = materials.xi_r

    b_mm = b * 1000.0
    h0_mm = h0 * 1000.0

    M_Nmm = abs(M) * 1e6
    alpha_m = M_Nmm / (Rb * b_mm * (h0_mm ** 2)) if (Rb * b_mm * h0_mm) > 0 else 0.0

    if alpha_m > materials.alpha_m:
        raise ValueError(
            f"αm = {alpha_m:.4f} > αR = {materials.alpha_m:.4f}. "
            f"Cần tăng chiều dày sàn hoặc cấp bê tông."
        )

    xi = 1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * alpha_m))

    if xi > xi_r:
        raise ValueError(
            f"ξ = {xi:.4f} > ξR = {xi_r:.4f}. "
            f"Cần tăng chiều dày sàn hoặc cấp bê tông."
        )

    As_mm2 = (xi * Rb * b_mm * h0_mm) / Rs
    # Kiểm tra hàm lượng cốt thép tối thiểu μ_min = 0.1% cho bản sàn (TCVN 5574:2018 Mục 10.3.3)
    As_min_mm2 = 0.001 * b_mm * h0_mm
    As_req_mm2 = max(As_mm2, As_min_mm2)
    As_cm2 = As_req_mm2 / 100.0

    return {
        "As": round(As_cm2, 2),
        "As_calc_cm2": round(As_mm2 / 100.0, 2),
        "alpha_m": round(alpha_m, 4),
        "xi": round(xi, 4),
        "h0": round(h0_mm, 0),
        "M_Nmm": round(M_Nmm, 0)
    }


def select_rebar(As_required: float, direction: str = "x") -> Tuple[str, float]:
    diameters = [6, 8, 10, 12]
    best_choice = None
    min_waste = float('inf')

    for dia in diameters:
        area_one = math.pi * (dia / 2) ** 2
        spacings = [100, 150, 200]
        for s in spacings:
            As_provided = area_one * 1000 / s
            if As_provided >= As_required * 100:
                waste = As_provided - As_required * 100
                if waste < min_waste:
                    min_waste = waste
                    best_choice = (dia, s, As_provided / 100)

    if best_choice:
        dia, s, As = best_choice
        return f"Ø{dia}@{s}", As

    # Fallback Ø12@100 = 11.31 cm2/m
    return "Ø12@100", round(math.pi * (12 / 2) ** 2 * 1000 / 100 / 100, 2)


def calculate_deflection(
    geometry: SlabGeometry,
    loads: LoadConditions,
    materials: MaterialProperties,
    reinforcement: ReinforcementResult
) -> DeflectionResult:
    q_sls = loads.q_sls
    L_short = min(geometry.Lx, geometry.Ly) * 1000
    h = geometry.h * 1000
    b = geometry.b * 1000

    E = materials.Eb
    I_cr = b * h ** 3 / 12 * 0.7
    coef = 5.0 / 384.0

    # q_sls: kN/m² (áp phẳng). Quy đổi sang tải tuyến w [N/mm]:
    #   w = q_sls [kN/m²] × b_m [m] = kN/m = N/mm  (b ở đây tính bằng mm)
    # Nếu thiếu nhân b, kết quả độ võng bị nhỏ hơn thực tế ~b lần.
    w_Nmm = q_sls * b / 1000.0
    f_inst = coef * (w_Nmm * L_short ** 4) / (E * I_cr)
    phi = 2.0
    f_calc = f_inst * (1 + phi)
    f_allow = L_short / 250.0
    eta_f = f_calc / f_allow

    return DeflectionResult(
        f_calc=round(f_calc, 1),
        f_allow=round(f_allow, 1),
        eta_f=round(eta_f, 3),
        passed=eta_f <= 1.0
    )


def calculate_crack_width_check(
    geometry: SlabGeometry,
    materials: MaterialProperties,
    reinforcement: ReinforcementResult,
    loads: LoadConditions
) -> dict:
    h0 = (geometry.h - geometry.a) * 1000
    L_short = min(geometry.Lx, geometry.Ly)
    M_sls = loads.q_sls * (L_short ** 2) / 11
    M_Nmm = M_sls * 1e6

    # Lấy cốt thép nhịp ngắn để kiểm tra nứt
    As_short_pos = reinforcement.As_x_pos if geometry.Lx <= geometry.Ly else reinforcement.As_y_pos
    As_short_neg = reinforcement.As_x_neg if geometry.Lx <= geometry.Ly else reinforcement.As_y_neg
    As_avg = (As_short_pos + As_short_neg) / 2 * 100

    z = 0.85 * h0
    sigma_s = M_Nmm / (As_avg * z) if (As_avg * z) > 0 else 0

    phi_bar = 10
    s = 150

    psi = 1.0 - 0.7 * (materials.Rbt_ser / sigma_s) if sigma_s > 0 else 1.0
    psi = max(0.5, min(1.0, psi))

    l_s = 0.5 * s + 0.1 * phi_bar
    phi_crc = 0.7
    Es = 200000.0
    a_crc = (phi_crc * psi * (sigma_s / Es)) * l_s

    return {
        "sigma_s": round(sigma_s, 1),
        "psi": round(psi, 3),
        "l_s": round(l_s, 1),
        "a_crc": round(a_crc, 3),
        "a_crc_limit": 0.4,
        "passed": a_crc <= 0.4
    }


def calculate_slab(input_data: dict) -> dict:
    start_time = datetime.now()
    logs = []

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")

    project = input_data.get("project", {})
    geometry_data = input_data["geometry"]
    materials_data = input_data["materials"]
    loads_data = input_data["loads"]
    boundary = input_data.get("boundary_conditions", "simply_supported")

    log(f"Bắt đầu tính toán sàn: {project.get('name', 'N/A')}")
    log(f"Kích thước: Lx={geometry_data['Lx']}m, Ly={geometry_data['Ly']}m, h={geometry_data['h']*1000:.0f}mm")

    geometry = SlabGeometry(
        Lx=geometry_data["Lx"],
        Ly=geometry_data["Ly"],
        h=geometry_data["h"],
        a=geometry_data.get("a", 0.02)
    )

    materials = MaterialProperties(
        concrete_grade=materials_data.get("concrete_grade", "B25"),
        rebar_grade=materials_data.get("rebar_grade", "CB300"),
        gamma_m=materials_data.get("gamma_m", 1.15)
    )

    loads = LoadConditions(
        g_dl=loads_data["g_dl"],
        q_ll=loads_data["q_ll"],
        gamma_g=loads_data.get("gamma_g", 1.2),
        gamma_q=loads_data.get("gamma_q", 1.3)
    )

    log(f"Vật liệu: {materials.concrete_grade} (Rb={materials.Rb}MPa, Rbt={materials.Rbt}MPa, Eb={materials.Eb}MPa), "
        f"{materials.rebar_grade} (Rs={materials.Rs}MPa, ξR={materials.xi_r}, αR={materials.alpha_m})")
    log(f"Tải trọng: g={loads.g_dl}kN/m2, q={loads.q_ll}kN/m2 -> ULS q={loads.q_uls:.2f}kN/m2")

    log("Tính moment bản 2 phương theo nhịp ngắn L_short = min(Lx, Ly)...")
    moments = calculate_moments(geometry, loads, boundary)
    log(f"M_x(+)={moments.M_x_pos:.3f}kNm/m, M_y(+)={moments.M_y_pos:.3f}kNm/m")

    log("Tính cốt thép...")
    As_x_pos = calculate_reinforcement(moments.M_x_pos, geometry, materials, is_top=False)
    rebar_x_pos, As_x_pos_prov = select_rebar(As_x_pos["As"], "x")

    As_x_neg = calculate_reinforcement(abs(moments.M_x_neg), geometry, materials, is_top=True)
    rebar_x_neg, As_x_neg_prov = select_rebar(As_x_neg["As"], "x")

    As_y_pos = calculate_reinforcement(moments.M_y_pos, geometry, materials, is_top=False)
    rebar_y_pos, As_y_pos_prov = select_rebar(As_y_pos["As"], "y")

    As_y_neg = calculate_reinforcement(abs(moments.M_y_neg), geometry, materials, is_top=True)
    rebar_y_neg, As_y_neg_prov = select_rebar(As_y_neg["As"], "y")

    # [FIX BUG-STR-01c]: Tính hệ số sử dụng thực tế eta_M = max(As_req / As_prov) thay vì gán cứng 1.0
    eta_M_actual = max(
        As_x_pos["As"] / As_x_pos_prov if As_x_pos_prov > 0 else 0.0,
        As_x_neg["As"] / As_x_neg_prov if As_x_neg_prov > 0 else 0.0,
        As_y_pos["As"] / As_y_pos_prov if As_y_pos_prov > 0 else 0.0,
        As_y_neg["As"] / As_y_neg_prov if As_y_neg_prov > 0 else 0.0,
    )

    reinforcement = ReinforcementResult(
        As_x_pos=round(As_x_pos_prov, 2),
        As_x_neg=round(As_x_neg_prov, 2),
        As_y_pos=round(As_y_pos_prov, 2),
        As_y_neg=round(As_y_neg_prov, 2),
        rebar_x_pos=rebar_x_pos,
        rebar_x_neg=rebar_x_neg,
        rebar_y_pos=rebar_y_pos,
        rebar_y_neg=rebar_y_neg,
        eta_M=round(eta_M_actual, 3)
    )

    deflection = calculate_deflection(geometry, loads, materials, reinforcement)
    crack_check = calculate_crack_width_check(geometry, materials, reinforcement, loads)

    all_passed = (eta_M_actual <= 1.0) and deflection.passed and crack_check["passed"]
    overall_eta = max(eta_M_actual, deflection.eta_f, crack_check["a_crc"] / crack_check["a_crc_limit"])

    L_short_m = min(geometry.Lx, geometry.Ly)
    output = {
        "calculator": {
            "name": "calc_slab",
            "version": "1.1.0",
            "standard": "TCVN 5574:2018",
            "method": "Cường độ giới hạn (ULS) + Kiểm tra SLS"
        },
        "metadata": {
            "project_name": project.get("name", "N/A"),
            "calculation_date": datetime.now().isoformat(),
            "designer": project.get("designer", "N/A"),
            "notes": project.get("notes", "")
        },
        "input_summary": {
            "geometry": asdict(geometry),
            "materials": {
                "concrete_grade": materials.concrete_grade,
                "rebar_grade": materials.rebar_grade,
                "Rb": materials.Rb,
                "Rbt": materials.Rbt,
                "Rs": materials.Rs,
                "Eb": materials.Eb,
                "xi_R": materials.xi_r,
                "alpha_R": materials.alpha_m,
            },
            "loads": asdict(loads),
            "boundary_conditions": boundary
        },
        "results": {
            "moments": asdict(moments),
            "reinforcement": asdict(reinforcement),
            "deflection": asdict(deflection),
            "crack_check": crack_check
        },
        "summary": {
            "slab_thickness": f"{geometry.h * 1000:.0f}mm",
            "concrete_volume": f"{geometry.Lx * geometry.Ly * geometry.h:.4f}m3",
            "rebar_x_area": f"{(reinforcement.As_x_pos + reinforcement.As_x_neg) * geometry.Lx:.2f}cm2",
            "rebar_y_area": f"{(reinforcement.As_y_pos + reinforcement.As_y_neg) * geometry.Ly:.2f}cm2",
            "deflection_ratio": f"L/{int(L_short_m * 1000 / deflection.f_calc) if deflection.f_calc > 0 else 'inf'}",
            "passed": all_passed,
            "overall_utilization": round(overall_eta, 3)
        },
        "conclusion": {
            "status": "PASSED" if all_passed else "FAILED",
            "message": "Sàn đạt yêu cầu về cường độ, võng và bề rộng khe nứt."
                       if all_passed else "Sàn không đạt một hoặc nhiều điều kiện. Cần điều chỉnh thiết kế.",
            "recommendations": [
                f"Cốt thép phương x dưới: {rebar_x_pos}",
                f"Cốt thép phương x trên: {rebar_x_neg}",
                f"Cốt thép phương y dưới: {rebar_y_pos}",
                f"Cốt thép phương y trên: {rebar_y_neg}"
            ]
        },
        "Calculation_Logs": [
            {
                "Step": i + 1,
                "Description": msg,
                "Formula": "TCVN 5574:2018 ULS/SLS",
                "Result": "OK"
            }
            for i, msg in enumerate(logs)
        ] if logs else [],
        "Standard_Method": "TCVN 5574:2018",
        "calculation_log": logs,
        "standard_references": [
            "TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép",
            "TCVN 2737:2023 — Tải trọng và tác động"
        ]
    }
    return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tính toán sàn BTCT 2 phương theo TCVN 5574:2018")
    parser.add_argument("--input", "-i", required=True, help="File JSON đầu vào")
    parser.add_argument("--output", "-o", help="File JSON đầu ra (mặc định: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Định dạng JSON đẹp")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    result = calculate_slab(input_data)
    json_str = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
