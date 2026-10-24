#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_formwork_column.py — Thiết kế cốp pha cột (Column Formwork Design)

Tiêu chuẩn:
- TCVN 4453:1995 - Công tác bê tông và BTCT
- ACI 347-04 - Formwork for Concrete
- Eurocode 2 (EN 1992-1-1) — Lateral pressure formula

Hệ thống cốp pha cột:
1. Panel (ván khuôn)
2. Yoke/Stiffener (thanh ghì/cững)
3. Tie rod (bu lông neo cốp pha)
4. Brace (thanh chống ngang)

Usage:
    python calc_formwork_column.py --width 400 --height 3000 --grade B30 --rate 1.0
    python calc_formwork_column.py -w 500 -h 4000 -g B25 -r 2.0 --json
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
# MATERIAL & STANDARD DATABASE
# ============================================================================

CONCRETE_GRADES = {
    "B15": {"gamma": 24.0, "f_ck": 12.5, "Ec": 27000, "temp_range": (5, 35)},
    "B20": {"gamma": 24.0, "f_ck": 16.5, "Ec": 29500, "temp_range": (5, 35)},
    "B25": {"gamma": 24.5, "f_ck": 19.0, "Ec": 30000, "temp_range": (5, 35)},
    "B30": {"gamma": 25.0, "f_ck": 22.5, "Ec": 32500, "temp_range": (5, 35)},
    "B35": {"gamma": 25.0, "f_ck": 26.0, "Ec": 34000, "temp_range": (5, 35)},
    "B40": {"gamma": 25.0, "f_ck": 30.0, "Ec": 35500, "temp_range": (5, 35)},
}

# Plywood properties (mm)
PLYWOOD_TYPES = {
    "15mm": {"t": 15, "E": 9000, "sigma": 10, "weight": 7.5},
    "18mm": {"t": 18, "E": 9000, "sigma": 10, "weight": 9.0},
    "21mm": {"t": 21, "E": 9000, "sigma": 10, "weight": 10.5},
}

# Steel tie rod catalog
TIE_RODS = {
    "TR15": {"d": 15, "A": 177, "capacity": 35, "pitch_min": 300, "pitch_max": 600},
    "TR17": {"d": 17, "A": 227, "capacity": 45, "pitch_min": 300, "pitch_max": 750},
    "TR20": {"d": 20, "A": 314, "capacity": 65, "pitch_min": 400, "pitch_max": 900},
    "TR22": {"d": 22, "A": 380, "capacity": 80, "pitch_min": 400, "pitch_max": 1000},
}

# Yoke/stiffener I-beam catalog
YOKE_BEAMS = {
    "H100x50": {"Ix": 3.56e-6, "Sx": 0.0000712, "W": 9.32, "h": 100, "bf": 50},
    "H150x75": {"Ix": 1.68e-5, "Sx": 0.000225, "W": 14.0, "h": 150, "bf": 75},
}

# Safety factors
SAFETY_FACTORS = {
    "load_DL": 1.2,
    "load_LL": 1.5,
    "material_concrete": 1.5,
    "material_steel": 1.1,
    "stability": 2.0,
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ColumnFormworkResult:
    """Kết quả thiết kế cốp pha cột"""

    # Input
    column_width: float        # mm
    column_height: float       # mm
    concrete_grade: str
    pour_rate: float          # m/h
    concrete_temp: float       # °C

    # Pressure calculation
    max_lateral_pressure: float   # kN/m²
    pressure_formula: str
    pressure_citation: str

    # Panel design
    panel_thickness: int      # mm
    panel_spacing: float       # m (yoke spacing)
    panel_stress: float       # MPa
    panel_deflection: float    # mm
    eta_panel: float

    # Yoke design
    yoke_type: str
    yoke_spacing: float        # m
    yoke_moment: float         # kNm
    yoke_stress: float        # MPa
    eta_yoke: float

    # Tie rod design
    tie_rod_type: str
    tie_rod_capacity: float    # kN
    tie_rod_spacing: float     # m
    tie_rod_force: float       # kN
    eta_tie: float

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
        return asdict(self)


# ============================================================================
# CORE CALCULATIONS
# ============================================================================

class ColumnFormworkDesigner:
    """Thiết kế cốp pha cột"""

    def __init__(self, column_width: float, column_height: float,
                 concrete_grade: str = "B30", pour_rate: float = 1.0,
                 concrete_temp: float = 25.0):
        self.column_width = column_width
        self.column_height = column_height
        self.concrete_grade = concrete_grade
        self.pour_rate = pour_rate      # m/h
        self.concrete_temp = concrete_temp  # °C
        self.logs = []

        if concrete_grade not in CONCRETE_GRADES:
            raise ValueError(f"Unknown concrete grade: {concrete_grade}")

    def _log(self, step, formula, substitution, result, unit, citation=""):
        self.logs.append({
            "step": step,
            "formula": formula,
            "substitution": substitution,
            "result": round(float(result), 4),
            "unit": unit,
            "citation": citation
        })

    def calculate_lateral_pressure(self) -> Dict[str, float]:
        """
        Tính áp lực ngang tối đa của bê tông tươi lên cốp pha cột.

        Theo ACI 347-04:
        P_max = γ_c × h + C_v × V/t + C_w × γ_c × w

        Đơn giản hóa cho TCVN 4453:1995:
        P_max = min(γ_c × H, γ_c × H_0)

        Trong đó:
        - γ_c = trọng lượng riêng bê tông (kN/m³)
        - H = chiều cao cột bê tông đã đổ (m)
        - V = tốc độ đổ (m/h)
        - t = nhiệt độ bê tông (°C)
        - C_v = 1.0 cho V < 2m/h, 1.5 cho V >= 2m/h
        - C_w = 1.0 cho w >= 100mm, 1+0.7*(100-w)/(100) cho w < 100mm
        """
        step = 1
        gamma_c = CONCRETE_GRADES[self.concrete_grade]["gamma"]
        H = min(self.column_height / 1000, 2.0)  # Chiều cao cột đã đổ (giới hạn 2m)

        # Hệ số tốc độ đổ
        if self.pour_rate < 2.0:
            C_v = 1.0
        else:
            C_v = 1.5

        # Hệ số kích thước cột
        w = self.column_width / 1000  # chuyển mm -> m
        if w >= 0.1:
            C_w = 1.0
        else:
            C_w = 1.0 + 0.7 * (0.1 - w) / 0.1

        # Áp lực tĩnh: γ_c × H
        P_h = gamma_c * H
        self._log(step, "P_h = γ_c × H",
                  f"{gamma_c} × {H:.2f}", P_h, "kN/m²", "TCVN 4453:1995")
        step += 1

        # Áp lực do tốc độ đổ: C_v × V/t
        P_v = C_v * self.pour_rate / self.concrete_temp
        self._log(step, "P_v = C_v × V / t",
                  f"{C_v} × {self.pour_rate} / {self.concrete_temp}", P_v, "kN/m²", "ACI 347-04")
        step += 1

        # Áp lực do kích thước cột
        P_w = C_w * gamma_c * (0.1 - w) if w < 0.1 else 0
        if P_w > 0:
            self._log(step, "P_w = C_w × γ_c × (0.1 - w)",
                      f"{C_w:.2f} × {gamma_c} × {0.1-w:.3f}", P_w, "kN/m²", "ACI 347-04")
            step += 1

        # Tổng áp lực
        P_max = P_h + P_v + P_w
        self._log(step, "P_max = P_h + P_v + P_w",
                  f"{P_h:.2f} + {P_v:.2f} + {P_w:.2f}", P_max, "kN/m²", "ACI 347-04 / TCVN 4453")

        return {
            "P_h": P_h,
            "P_v": P_v,
            "P_w": P_w,
            "P_max": P_max,
            "C_v": C_v,
            "C_w": C_w,
            "gamma_c": gamma_c,
            "H": H
        }

    def design_panel(self, P_max: float) -> Dict:
        """
        Thiết kế panel (ván khuôn) cột.
        Panel chịu áp lực ngang như dầm đơn giản giữa 2 yoke.
        """
        step = 10

        # Chọn plywood 18mm
        ply = PLYWOOD_TYPES["18mm"]
        t = ply["t"]
        E = ply["E"] * 1e6  # Pa
        sigma_allow = ply["sigma"] * 1e6  # Pa
        I = t**3 / 12 * 1e-12  # m⁴
        Z = t**2 / 6 * 1e-6   # m³

        # Khoảng cách yoke = panel span
        # Quy đổi áp lực về kN/m²
        q = P_max  # kN/m²

        # Giải ra span tối ưu dựa trên độ võng L/270
        # δ = 5qL⁴/(384EI) ≤ L/270
        # → L³ ≤ 144EI/(5q)
        L = 0.5  # Start value
        for _ in range(50):
            delta = 5 * (q * 1000) * L**4 / (384 * E * I) * 1000  # mm
            delta_allow = L * 1000 / 270
            if delta <= delta_allow:
                break
            L *= 0.95

        L = round(L, 2)

        # Tính ứng suất thực tế
        M = q * L**2 / 8
        sigma = (M * 1000) / Z / 1e6  # MPa
        delta_actual = 5 * (q * 1000) * L**4 / (384 * E * I) * 1000  # mm

        eta = max(sigma / (sigma_allow/1e6), delta_actual / (L*1000/270))

        self._log(step, "Panel bending moment",
                  f"{q:.2f} × {L:.2f}² / 8", M, "kNm", "TCVN 4453")
        step += 1

        self._log(step, "Panel span (from deflection)",
                  f"L = {L:.2f} m", L, "m", "ACI 347-04")
        step += 1

        return {
            "thickness": t,
            "span": L,
            "moment": M,
            "stress": sigma,
            "deflection": delta_actual,
            "deflection_allow": L * 1000 / 270,
            "eta": eta
        }

    def design_yoke(self, P_max: float, panel_span: float) -> Dict:
        """
        Thiết kế yoke (thanh cững) chịu áp lực từ panel.
        Yoke chịu uốn giữa 2 tie rods.
        """
        step = 20

        # Chọn H150x75 làm yoke
        yoke = YOKE_BEAMS["H150x75"]
        E = 210e9  # Pa
        I = yoke["Ix"]
        Z = yoke["Sx"]
        sigma_allow = 210e6  # Pa

        # Khoảng cách tie rods = yoke span
        # Áp lực truyền từ panel = q × panel_span
        q = P_max * panel_span  # kN/m

        # Giải span tối ưu cho deflection L/400
        # δ = 5qL⁴/(384EI) ≤ L/400
        L = 0.8
        for _ in range(50):
            delta = 5 * q * 1000 * L**4 / (384 * E * I) * 1000  # mm
            delta_allow = L * 1000 / 400
            if delta <= delta_allow:
                break
            L *= 0.95

        L = round(L, 2)

        # Tính moment và ứng suất
        M = q * L**2 / 8
        sigma = M / Z / 1e6  # MPa
        delta_actual = 5 * q * 1000 * L**4 / (384 * E * I) * 1000

        eta = max(sigma / 210, delta_actual / (L*1000/400))

        self._log(step, "Yoke load",
                  f"{P_max:.2f} × {panel_span:.2f}", q, "kN/m", "TCVN 4453")
        step += 1

        self._log(step, "Yoke span",
                  f"L = {L:.2f} m", L, "m", "ACI 347-04")
        step += 1

        return {
            "type": "H150x75",
            "span": L,
            "load": q,
            "moment": M,
            "stress": sigma,
            "deflection": delta_actual,
            "deflection_allow": L * 1000 / 400,
            "eta": eta
        }

    def design_tie_rod(self, P_max: float, yoke_span: float) -> Dict:
        """
        Thiết kế tie rod (bu lông neo) chịu lực kéo.
        Lực kéo = P_max × yoke_spacing × yoke_span / 2
        """
        step = 30

        # Tính lực kéo trên mỗi tie rod
        # Tie rod nằm ở giữa yoke → mỗi tie chịu 1/2 tải
        tie_spacing = 0.5  # m (mặc định)
        F = P_max * tie_spacing * yoke_span / 2  # kN

        self._log(step, "Tie rod force",
                  f"{P_max:.2f} × {tie_spacing:.2f} × {yoke_span:.2f} / 2", F, "kN", "TCVN 4453:1995")
        step += 1

        # Chọn tie rod phù hợp
        selected_rod = None
        for name, rod in TIE_RODS.items():
            if F <= rod["capacity"] / SAFETY_FACTORS["material_steel"]:
                selected_rod = (name, rod)
                break

        if selected_rod is None:
            # Fallback to largest
            selected_rod = ("TR22", TIE_RODS["TR22"])

        name, rod = selected_rod
        eta = F / (rod["capacity"] / SAFETY_FACTORS["material_steel"])

        self._log(step, "Tie rod selection",
                  f"{name} - Cap: {rod['capacity']/SAFETY_FACTORS['material_steel']:.1f} kN",
                  rod["capacity"], "kN", "TCVN 4453")

        return {
            "type": name,
            "diameter": rod["d"],
            "area": rod["A"],
            "capacity": rod["capacity"] / SAFETY_FACTORS["material_steel"],
            "force": F,
            "spacing": tie_spacing,
            "eta": eta
        }

    def design(self) -> ColumnFormworkResult:
        """Chạy thiết kế hoàn chỉnh"""

        # 1. Tính áp lực ngang
        pressure = self.calculate_lateral_pressure()
        P_max = pressure["P_max"]

        # 2. Thiết kế panel
        panel = self.design_panel(P_max)

        # 3. Thiết kế yoke
        yoke = self.design_yoke(P_max, panel["span"])

        # 4. Thiết kế tie rod
        tie = self.design_tie_rod(P_max, yoke["span"])

        # 5. Compile warnings & recommendations
        warnings = []
        recommendations = []

        all_eta = [
            ("Panel", panel["eta"]),
            ("Yoke", yoke["eta"]),
            ("Tie Rod", tie["eta"])
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

        # Cảnh báo pour rate cao
        if self.pour_rate > 2.0:
            warnings.append(f"Tốc độ đổ {self.pour_rate} m/h cao — cần theo dõi áp lực cốp pha")

        return ColumnFormworkResult(
            column_width=self.column_width,
            column_height=self.column_height,
            concrete_grade=self.concrete_grade,
            pour_rate=self.pour_rate,
            concrete_temp=self.concrete_temp,
            max_lateral_pressure=P_max,
            pressure_formula="P_max = γ_c×H + C_v×V/t + C_w×γ_c×(0.1-w)",
            pressure_citation="ACI 347-04 / TCVN 4453:1995",
            panel_thickness=panel["thickness"],
            panel_spacing=panel["span"],
            panel_stress=panel["stress"],
            panel_deflection=panel["deflection"],
            eta_panel=panel["eta"],
            yoke_type=yoke["type"],
            yoke_spacing=yoke["span"],
            yoke_moment=yoke["moment"],
            yoke_stress=yoke["stress"],
            eta_yoke=yoke["eta"],
            tie_rod_type=tie["type"],
            tie_rod_capacity=tie["capacity"],
            tie_rod_spacing=tie["spacing"],
            tie_rod_force=tie["force"],
            eta_tie=tie["eta"],
            all_pass=all_pass,
            warnings=warnings,
            recommendations=recommendations,
            standard_method="ACI 347-04 / TCVN 4453:1995",
            calculation_logs=self.logs
        )


# ============================================================================
# CLI
# ============================================================================

def print_result(result: ColumnFormworkResult):
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ORANGE = "\033[38;5;214m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{'=' * 70}")
    print(f"{BOLD}THIẾT KẾ CỐP PHA CỘT{RESET}")
    print(f"{'─' * 70}")

    status_color = GREEN if result.all_pass else RED
    status_text = "✅ ĐẠT YÊU CẦU" if result.all_pass else "❌ KHÔNG ĐẠT"
    print(f"\nTrạng thái: {status_color}{status_text}{RESET}")
    print(f"Tiêu chuẩn: {result.standard_method}")

    print(f"\n{BOLD}📥 ĐẦU VÀO:{RESET}")
    print(f"  Tiết diện cột: {result.column_width} mm")
    print(f"  Chiều cao cột: {result.column_height} mm")
    print(f"  Mác bê tông: {result.concrete_grade}")
    print(f"  Tốc độ đổ: {result.pour_rate} m/h")
    print(f"  Nhiệt độ BT: {result.concrete_temp}°C")

    print(f"\n{BOLD}📊 ÁP LỰC NGANG:{RESET}")
    print(f"  P_max = {result.max_lateral_pressure:.2f} kN/m²")
    print(f"  Công thức: {result.pressure_formula}")

    def print_eta(name, eta):
        c = GREEN if eta <= 0.7 else (YELLOW if eta <= 0.9 else (ORANGE if eta <= 1.0 else RED))
        return f"  {c}η = {eta:.3f}{RESET}"

    print(f"\n{BOLD}📐 THIẾT KẾ PANEL:{RESET}")
    print(f"  Chiều dày: {result.panel_thickness}mm")
    print(f"  Cự ly yoke: {result.panel_spacing:.2f} m")
    print(f"  Ứng suất: {result.panel_stress:.3f} MPa")
    print(f"  Độ võng: {result.panel_deflection:.2f} / {result.panel_spacing*1000/270:.2f} mm")
    print(print_eta("Panel", result.eta_panel))

    print(f"\n{BOLD}📐 THIẾT KẾ YOKE:{RESET}")
    print(f"  Loại: {result.yoke_type}")
    print(f"  Cự ly tie rod: {result.yoke_spacing:.2f} m")
    print(f"  Moment: {result.yoke_moment:.4f} kNm")
    print(f"  Ứng suất: {result.yoke_stress:.3f} MPa")
    print(print_eta("Yoke", result.eta_yoke))

    print(f"\n{BOLD}🔩 THIẾT KẾ TIE ROD:{RESET}")
    print(f"  Loại: {result.tie_rod_type} (Ø{TIE_RODS[result.tie_rod_type]['d']}mm)")
    print(f"  Cự ly: {result.tie_rod_spacing:.2f} m")
    print(f"  Lực kéo: {result.tie_rod_force:.2f} kN")
    print(f"  Công suất: {result.tie_rod_capacity:.1f} kN")
    print(print_eta("Tie Rod", result.eta_tie))

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
    parser = argparse.ArgumentParser(description="Thiết kế cốp pha cột")
    parser.add_argument("--width", "-w", type=float, required=True, help="Bề rộng cột (mm)")
    parser.add_argument("--height", "-H", type=float, required=True, help="Chiều cao cột (mm)")
    parser.add_argument("--grade", "-g", default="B30", help="Mác bê tông")
    parser.add_argument("--rate", "-r", type=float, default=1.0, help="Tốc độ đổ (m/h)")
    parser.add_argument("--temp", "-T", type=float, default=25.0, help="Nhiệt độ bê tông (°C)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Chi tiết")

    args = parser.parse_args()

    designer = ColumnFormworkDesigner(
        column_width=args.width,
        column_height=args.height,
        concrete_grade=args.grade.upper(),
        pour_rate=args.rate,
        concrete_temp=args.temp
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
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
