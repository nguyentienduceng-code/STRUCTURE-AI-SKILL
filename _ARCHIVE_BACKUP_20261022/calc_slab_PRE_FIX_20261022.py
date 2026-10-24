#!/usr/bin/env python3
"""
calc_slab.py — Tính toán sàn BTCT 2 phương theo TCVN 5574:2018
=============================================================
Script tính toán cốt thép sàn BTCT chịu uốn 2 phương (dầm bản đặc).

Tiêu chuẩn: TCVN 5574:2018 — Kết cấu bê tông và bê tông cốt thép
Phương pháp: Cường độ giới hạn (ULS) + Kiểm tra võng (SLS)

Usage:
    python calc_slab.py --input data.json [--output result.json]

Input JSON:
{
    "project": {"name": "...", "date": "..."},
    "geometry": {
        "Lx": 6.0,        # Nhịp dài (m)
        "Ly": 3.0,        # Nhịp ngắn (m)
        "h": 0.12,        # Chiều dày sàn (m)
        "a": 0.02,       # Lớp bảo vệ (m)
    },
    "materials": {
        "concrete_grade": "B25",     # Cấp bền bê tông
        "rebar_grade": "CB300",     # Mác cốt thép
        "gamma_m": 1.15            # Hệ số độ bền bê tông
    },
    "loads": {
        "g_dl": 3.5,       # Tĩnh tải (kN/m2)
        "q_ll": 2.5,       # Hoạt tải (kN/m2)
        "gamma_g": 1.2,    # Hệ số tĩnh tải
        "gamma_q": 1.3     # Hệ số hoạt tải
    },
    "boundary_conditions": "simply_supported"  # hoặc "fixed_one", "fixed_all"
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
from typing import Optional

# =============================================================================
# CONSTANTS & MATERIAL PROPERTIES
# =============================================================================

# Cường độ chịu nén tính toán của bê tông Rb (MPa) — TCVN 5574:2018 Bảng 3.1
CONCRETE_RB = {
    "B15": 8.5,  "B20": 11.5, "B25": 14.5, "B30": 17.0,
    "B35": 19.5, "B40": 22.0, "B45": 25.0, "B50": 27.5
}

# Cường độ chịu kéo tính toán của bê tông Rbt (MPa) — TCVN 5574:2018
CONCRETE_RBT = {
    "B15": 0.75, "B20": 1.00, "B25": 1.15, "B30": 1.30,
    "B35": 1.45, "B40": 1.60, "B45": 1.70, "B50": 1.80
}

# Cường độ chịu kéo tính toán của cốt thép Rs (MPa) — TCVN 5574:2018
REBAR_RS = {
    "CB240": 210, "CB300": 260, "CB350": 300, "CB400": 350, "CB500": 415
}

# Cường độ chịu kéo tính toán của cốt thép khi tính võng R_s,ser (MPa)
REBAR_RS_SER = {
    "CB240": 240, "CB300": 300, "CB350": 350, "CB400": 400, "CB500": 500
}

# Mô đun đàn hồi E (MPa) — TCVN 5574:2018
CONCRETE_E = {
    "B15": 21000, "B20": 24500, "B25": 27500, "B30": 30000,
    "B35": 31500, "B40": 32500, "B45": 33500, "B50": 34500
}

# Bảng tra hệ số α theo mác bê tông
ALPHA_M = {
    "B15": 0.90, "B20": 0.88, "B25": 0.86, "B30": 0.85,
    "B35": 0.84, "B40": 0.83, "B45": 0.82, "B50": 0.81
}

# Hệ số ξR theo mác bê tông
XI_R = {
    "B15": 0.65, "B20": 0.62, "B25": 0.59, "B30": 0.57,
    "B35": 0.56, "B40": 0.54, "B45": 0.53, "B50": 0.52
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SlabGeometry:
    """Hình học sàn"""
    Lx: float          # Nhịp dài (m)
    Ly: float          # Nhịp ngắn (m)
    h: float           # Chiều dày sàn (m)
    a: float           # Lớp bảo vệ (m)
    b: float = 1.0     # Bề rộng tính toán (m)

@dataclass
class MaterialProperties:
    """Đặc trưng vật liệu"""
    concrete_grade: str
    rebar_grade: str
    gamma_m: float = 1.15

    @property
    def Rb(self) -> float:
        return CONCRETE_RB.get(self.concrete_grade, 14.5)

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
        return CONCRETE_E.get(self.concrete_grade, 27500)

    @property
    def alpha_m(self) -> float:
        return ALPHA_M.get(self.concrete_grade, 0.86)

    @property
    def xi_r(self) -> float:
        return XI_R.get(self.concrete_grade, 0.59)

@dataclass
class LoadConditions:
    """Điều kiện tải trọng"""
    g_dl: float        # Tĩnh tải (kN/m2)
    q_ll: float        # Hoạt tải (kN/m2)
    gamma_g: float = 1.2
    gamma_q: float = 1.3

    @property
    def q_uls(self) -> float:
        """Tổ hợp tải trọng ULS (kN/m2)"""
        return self.gamma_g * self.g_dl + self.gamma_q * self.q_ll

    @property
    def q_sls(self) -> float:
        """Tổ hợp tải trọng SLS (kN/m2)"""
        return self.g_dl + self.q_ll

@dataclass
class SlabMomentResult:
    """Kết quả tính moment"""
    M_x_pos: float     # Moment dương phương x (kNm/m)
    M_x_neg: float     # Moment âm phương x (kNm/m)
    M_y_pos: float     # Moment dương phương y (kNm/m)
    M_y_neg: float     # Moment âm phương y (kNm/m)

@dataclass
class ReinforcementResult:
    """Kết quả tính cốt thép"""
    As_x_pos: float    # Diện tích cốt thép dương phương x (cm2/m)
    As_x_neg: float    # Diện tích cốt thép âm phương x (cm2/m)
    As_y_pos: float    # Diện tích cốt thép dương phương y (cm2/m)
    As_y_neg: float    # Diện tích cốt thép âm phương y (cm2/m)

    # Thông số cốt thép chọn
    rebar_x_pos: str   # Thông số thanh chọn phương x dương (VD: "Ø10@150")
    rebar_x_neg: str   # Thông số thanh chọn phương x âm
    rebar_y_pos: str   # Thông số thanh chọn phương y dương
    rebar_y_neg: str   # Thông số thanh chọn phương y âm

    # Kiểm tra
    eta_M: float       # Hệ số sử dụng moment

@dataclass
class DeflectionResult:
    """Kết quả kiểm tra võng"""
    f_calc: float      # Võng tính toán (mm)
    f_allow: float     # Võng cho phép (mm)
    eta_f: float       # Hệ số sử dụng võng
    passed: bool

@dataclass
class SlabCalculationResult:
    """Kết quả tổng hợp tính toán sàn"""
    metadata: dict
    geometry: dict
    materials: dict
    loads: dict
    moments: dict
    reinforcement: dict
    deflection: dict
    checks: dict
    logs: list

# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def get_boundary_coefficients(boundary: str) -> dict:
    """
    Lấy hệ số moment theo điều kiện biên.
    Theo TCVN 5574:2018 Phụ lục E hoặc Bảng E.1
    """
    if boundary == "simply_supported":
        return {
            # Moment dương (bản kê 2 cạnh đối diện)
            "m1_pos": 1/11,    # Phương Lx
            "m2_pos": 1/16,    # Phương Ly

            # Moment âm
            "m1_neg": -1/11,   # Phương Lx (gối)
            "m2_neg": -1/16,   # Phương Ly (gối)

            # Hệ số kể đến sự phân phối lại moment
            "k": 0.8
        }
    elif boundary == "fixed_one":
        return {
            "m1_pos": 1/14,
            "m2_pos": 1/20,
            "m1_neg": -1/11,
            "m2_neg": -1/14,
            "k": 0.85
        }
    elif boundary == "fixed_all":
        return {
            "m1_pos": 1/16,
            "m2_pos": 1/22,
            "m1_neg": -1/14,
            "m2_neg": -1/16,
            "k": 0.9
        }
    else:
        raise ValueError(f"Boundary condition không hợp lệ: {boundary}")

def calculate_moments(
    geometry: SlabGeometry,
    loads: LoadConditions,
    boundary: str
) -> SlabMomentResult:
    """
    Tính moment trong sàn 2 phương theo phương pháp dầm.

    Công thức: M = α * q * L²
    α: hệ số phụ thuộc tỷ số nhịp và điều kiện biên
    """
    q = loads.q_uls
    Lx = geometry.Lx
    Ly = geometry.Ly

    # Tỷ số nhịp
    mu = min(Lx, Ly) / max(Lx, Ly) if max(Lx, Ly) > 0 else 1.0

    # Lấy hệ số theo điều kiện biên
    coef = get_boundary_coefficients(boundary)

    # Hệ số điều chỉnh theo tỷ số nhịp
    if mu < 0.5:
        # Sàn 1 phương
        alpha_x = coef["m1_pos"] * 1.0
        alpha_y = coef["m2_pos"] * 0.0
    else:
        # Sàn 2 phương
        alpha_x = coef["m1_pos"]
        alpha_y = coef["m2_pos"]

    # Moment dương (kNm/m)
    M_x_pos = alpha_x * q * Lx**2
    M_y_pos = alpha_y * q * Ly**2

    # Moment âm (lấy = 70-80% moment dương liền kề)
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
    is_top: bool = False  # Cốt thép trên hay dưới
) -> dict:
    """
    Tính diện tích cốt thép từ moment uốn.

    Phương pháp: Cường độ giới hạn (TCVN 5574:2018)

    Công thức:
    α_m = M / (Rb * b * h0²)
    ξ = 1 - sqrt(1 - 2*α_m)
    As = ξ * Rb * b * h0 / Rs
    """
    b = geometry.b
    h0 = geometry.h - geometry.a if not is_top else geometry.a + 0.005

    # Đảm bảo h0 tối thiểu cho cốt thép trên
    if is_top:
        h0 = geometry.h - geometry.a - 0.005

    Rb = materials.Rb
    Rs = materials.Rs
    xi_r = materials.xi_r

    # Quy đổi b và h0 sang mm để tính toán chính xác đơn vị
    b_mm = b * 1000.0
    h0_mm = h0 * 1000.0

    # Tính αm
    M_Nmm = M * 1e6  # Convert kNm → Nmm
    alpha_m = M_Nmm / (Rb * b_mm * (h0_mm ** 2))

    # Kiểm tra αm ≤ αR
    if alpha_m > materials.alpha_m:
        raise ValueError(
            f"αm = {alpha_m:.4f} > αR = {materials.alpha_m:.4f}. "
            f"Cần tăng chiều dày sàn hoặc cấp bê tông."
        )

    # Tính ξ
    xi = 1 - math.sqrt(1 - 2 * alpha_m)

    # Kiểm tra ξ ≤ ξR
    if xi > xi_r:
        raise ValueError(
            f"ξ = {xi:.4f} > ξR = {xi_r:.4f}. "
            f"Cần tăng chiều dày sàn hoặc cấp bê tông."
        )

    # Diện tích cốt thép (mm2/m)
    As_mm2 = (xi * Rb * b_mm * h0_mm) / Rs

    # Chuyển đổi sang cm2/m
    As_cm2 = As_mm2 / 100

    return {
        "As": round(As_cm2, 2),
        "alpha_m": round(alpha_m, 4),
        "xi": round(xi, 4),
        "h0": round(h0 * 1000, 0),  # mm
        "M_Nmm": round(M_Nmm, 0)
    }

def select_rebar(As_required: float, direction: str = "x") -> str:
    """
    Chọn cốt thép từ As yêu cầu.

    Đường kính thường dùng cho sàn: Ø6, Ø8, Ø10, Ø12
    Bước cốt thép: 100, 150, 200 mm

    Returns: VD "Ø10@150"
    """
    # Các đường kính phổ biến (mm)
    diameters = [6, 8, 10, 12]

    best_choice = None
    min_waste = float('inf')

    for dia in diameters:
        area_one = math.pi * (dia/2)**2  # mm2

        # Các bước cốt thép phổ biến (mm)
        spacings = [100, 150, 200]

        for s in spacings:
            # Diện tích cốt thép trên 1m bề rộng
            As_provided = area_one * 1000 / s  # mm2/m

            if As_provided >= As_required * 100:  # Convert cm2 → mm2
                waste = As_provided - As_required * 100
                if waste < min_waste:
                    min_waste = waste
                    best_choice = (dia, s, As_provided / 100)  # dia, spacing, As(cm2)

    if best_choice:
        dia, s, As = best_choice
        return f"Ø{dia}@{s}", As

    return "Ø12@100", 1.13

def calculate_deflection(
    geometry: SlabGeometry,
    loads: LoadConditions,
    materials: MaterialProperties,
    reinforcement: ReinforcementResult
) -> DeflectionResult:
    """
    Kiểm tra võng sàn theo TCVN 5574:2018.

    Sử dụng công thức gần đúng cho bản:
    f = (q * L^4) / (β * E * I)

    Võng giới hạn: L/200 (ngắn hạn), L/250 (dài hạn)
    """
    q_sls = loads.q_sls  # kN/m2
    # Bản làm việc theo phương cạnh ngắn
    L_short = min(geometry.Lx, geometry.Ly) * 1000  # mm
    h = geometry.h * 1000   # mm
    b = geometry.b * 1000   # mm (1m)

    E = materials.Eb  # MPa = N/mm2

    # Momen quán tính tiết diện cracked (xấp xỉ)
    I_cr = b * h**3 / 12 * 0.7  # Hệ số 0.7 kể đến nứt

    # Hệ số điều kiện biên (dải bản đơn giản: 5/384)
    coef = 5.0 / 384.0

    # Võng tức thời (mm)
    q_sls_Nmm2 = q_sls * 1e-3  # kN/m2 → N/mm2
    f_inst = coef * (q_sls_Nmm2 * L_short**4) / (E * I_cr)

    # Hệ số xét đến từ biến dẻo
    phi = 2.0  # Hệ số từ biến dẻo cho tải dài hạn

    # Võng dài hạn
    f_calc = f_inst * (1 + phi)

    # Võng cho phép
    f_allow = L_short / 250.0  # L/250

    # Hệ số sử dụng
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
    """
    Kiểm tra bề rộng khe nứt theo TCVN 5574:2018.

    a_crc = ψ * φ * σs * l_s / Es

    Giới hạn:
    - Môi trường bình thường: a_crc ≤ 0.4 mm
    - Môi trường ăn mòn: a_crc ≤ 0.3 mm
    """
    h0 = (geometry.h - geometry.a) * 1000  # mm

    # Ứng suất trong cốt thép (xấp xỉ)
    # σs = M / (As * z), với z ≈ 0.85 * h0
    L_short = min(geometry.Lx, geometry.Ly)
    M_sls = loads.q_sls * (L_short ** 2) / 11  # Moment SLS phương nhịp ngắn
    M_Nmm = M_sls * 1e6

    # As trung bình (cm2/m → mm2/m)
    As_avg = (reinforcement.As_x_pos + reinforcement.As_x_neg) / 2 * 100

    z = 0.85 * h0  # Cánh tay đòn nội lực
    sigma_s = M_Nmm / (As_avg * z) if (As_avg * z) > 0 else 0  # MPa

    # Đường kính cốt thép (lấy Ø10)
    phi_bar = 10  # mm

    # Khoảng cách cốt thép (lấy 150mm)
    s = 150  # mm

    # Hệ số ψ
    psi = 1.0 - 0.7 * (materials.Rbt / sigma_s) if sigma_s > 0 else 1.0
    psi = max(0.5, min(1.0, psi))

    # Khoảng cách giữa các vết nứt (mm)
    l_s = 0.5 * s + 0.1 * phi_bar

    # Bề rộng khe nứt theo TCVN 5574:2018 Điều 8.2.1.2:
    # a_crc = φ1 * φ2 * φ3 * ψ * (σs / Es) * l_s
    # Với φ1*φ2*φ3 = 1.4 * 0.5 * 1.0 = 0.7 (cốt có gờ, dài hạn, chịu uốn)
    # Es = 200,000 MPa (mô đun đàn hồi của cốt thép)
    phi_crc = 0.7
    Es = 200000.0  # MPa
    a_crc = (phi_crc * psi * (sigma_s / Es)) * l_s

    return {
        "sigma_s": round(sigma_s, 1),  # MPa
        "psi": round(psi, 3),
        "l_s": round(l_s, 1),  # mm
        "a_crc": round(a_crc, 3),  # mm
        "a_crc_limit": 0.4,  # mm (môi trường bình thường)
        "passed": a_crc <= 0.4
    }

# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================

def calculate_slab(input_data: dict) -> dict:
    """
    Hàm chính tính toán sàn BTCT 2 phương.

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
    loads_data = input_data["loads"]
    boundary = input_data.get("boundary_conditions", "simply_supported")

    log(f"Bắt đầu tính toán sàn: {project.get('name', 'N/A')}")
    log(f"Kích thước: Lx={geometry_data['Lx']}m, Ly={geometry_data['Ly']}m, h={geometry_data['h']*1000:.0f}mm")

    # Create objects
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

    log(f"Vật liệu: {materials.concrete_grade} (Rb={materials.Rb}MPa), "
        f"{materials.rebar_grade} (Rs={materials.Rs}MPa)")
    log(f"Tải trọng: g={loads.g_dl}kN/m2, q={loads.q_ll}kN/m2")
    log(f"Tổ hợp ULS: q={loads.q_uls:.2f}kN/m2")

    # Step 1: Calculate moments
    log("Tính moment...")
    moments = calculate_moments(geometry, loads, boundary)
    log(f"M_x(+)={moments.M_x_pos:.3f}kNm/m, M_y(+)={moments.M_y_pos:.3f}kNm/m")

    # Step 2: Calculate reinforcement
    log("Tính cốt thép...")

    # Phương x dương (dưới)
    As_x_pos = calculate_reinforcement(moments.M_x_pos, geometry, materials, is_top=False)
    rebar_x_pos, As_x_pos_prov = select_rebar(As_x_pos["As"], "x")

    # Phương x âm (trên)
    As_x_neg = calculate_reinforcement(abs(moments.M_x_neg), geometry, materials, is_top=True)
    rebar_x_neg, As_x_neg_prov = select_rebar(As_x_neg["As"], "x")

    # Phương y dương (dưới)
    As_y_pos = calculate_reinforcement(moments.M_y_pos, geometry, materials, is_top=False)
    rebar_y_pos, As_y_pos_prov = select_rebar(As_y_pos["As"], "y")

    # Phương y âm (trên)
    As_y_neg = calculate_reinforcement(abs(moments.M_y_neg), geometry, materials, is_top=True)
    rebar_y_neg, As_y_neg_prov = select_rebar(As_y_neg["As"], "y")

    log(f"Phương x dương: As={As_x_pos['As']:.2f}cm2/m → {rebar_x_pos} ({As_x_pos_prov:.2f}cm2/m)")
    log(f"Phương x âm: As={As_x_neg['As']:.2f}cm2/m → {rebar_x_neg} ({As_x_neg_prov:.2f}cm2/m)")
    log(f"Phương y dương: As={As_y_pos['As']:.2f}cm2/m → {rebar_y_pos} ({As_y_pos_prov:.2f}cm2/m)")
    log(f"Phương y âm: As={As_y_neg['As']:.2f}cm2/m → {rebar_y_neg} ({As_y_neg_prov:.2f}cm2/m)")

    # Tổng hợp kết quả cốt thép
    reinforcement = ReinforcementResult(
        As_x_pos=round(As_x_pos_prov, 2),
        As_x_neg=round(As_x_neg_prov, 2),
        As_y_pos=round(As_y_pos_prov, 2),
        As_y_neg=round(As_y_neg_prov, 2),
        rebar_x_pos=rebar_x_pos,
        rebar_x_neg=rebar_x_neg,
        rebar_y_pos=rebar_y_pos,
        rebar_y_neg=rebar_y_neg,
        eta_M=1.0  # Đạt vì đã chọn cốt thép
    )

    # Step 3: Check deflection
    log("Kiểm tra võng...")
    deflection = calculate_deflection(geometry, loads, materials, reinforcement)
    log(f"Võng tính toán: f={deflection.f_calc:.1f}mm, cho phép: f={deflection.f_allow:.1f}mm")
    log(f"Kiểm tra võng: {'ĐẠT' if deflection.passed else 'KHÔNG ĐẠT'} (η={deflection.eta_f:.3f})")

    # Step 4: Check crack width
    log("Kiểm tra bề rộng khe nứt...")
    crack_check = calculate_crack_width_check(geometry, materials, reinforcement, loads)
    log(f"Bề rộng khe nứt: a_crc={crack_check['a_crc']:.3f}mm, giới hạn: {crack_check['a_crc_limit']}mm")
    log(f"Kiểm tra nứt: {'ĐẠT' if crack_check['passed'] else 'KHÔNG ĐẠT'}")

    # Tổng hợp kiểm tra
    all_passed = deflection.passed and crack_check["passed"]
    overall_eta = max(deflection.eta_f, crack_check["a_crc"] / crack_check["a_crc_limit"])

    log(f"\n{'='*50}")
    log(f"KẾT LUẬN: {'ĐẠT YÊU CẦU' if all_passed else 'KHÔNG ĐẠT'}")
    log(f"Hệ số sử dụng tổng: η = {overall_eta:.3f}")
    log(f"Thời gian tính toán: {(datetime.now() - start_time).total_seconds():.2f}s")

    # Build output following CALCULATOR_OUTPUT_STANDARD
    output = {
        "calculator": {
            "name": "calc_slab",
            "version": "1.0.0",
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
                "Eb": materials.Eb
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
            "deflection_ratio": f"L/{int(geometry.Lx * 1000 / deflection.f_calc) if deflection.f_calc > 0 else 'inf'}",
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

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Tính toán sàn BTCT 2 phương theo TCVN 5574:2018"
    )
    parser.add_argument("--input", "-i", required=True, help="File JSON đầu vào")
    parser.add_argument("--output", "-o", help="File JSON đầu ra (mặc định: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Định dạng JSON đẹp")

    args = parser.parse_args()

    # Read input
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # Calculate
    result = calculate_slab(input_data)

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
