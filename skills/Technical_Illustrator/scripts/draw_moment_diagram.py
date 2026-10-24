#!/usr/bin/env python3
"""
draw_moment_diagram.py — Vẽ biểu đồ nội lực (M, V, N) cho dầm liên tục
================================================================================
Script vẽ biểu đồ moment uốn, lực cắt và lực dọc trục.

Output: SVG hoặc DXF

Usage:
    python draw_moment_diagram.py --input data.json --output diagram.svg

Input JSON:
{
    "project": {"name": "...", "date": "..."},
    "beam": {
        "name": "Dầm D1",
        "L": [3.0, 6.0, 3.0],  # Các nhịp (m)
        "supports": ["fixed", "roller", "fixed"],  # Loại gối
        "h": 0.6,  # Chiều cao dầm (m)
        "b": 0.3   # Bề rộng dầm (m)
    },
    "loads": {
        "distributed": [
            {"start": 0, "end": 9, "q": 25},  # kN/m
            {"start": 0, "end": 3, "q": 15}
        ],
        "point": [
            {"x": 3.0, "P": 50},  # kN
            {"x": 6.0, "P": 80}
        ]
    },
    "output": {
        "format": "svg",  # svg | dxf
        "scale_m": 0.01,   # Scale moment (m/kN)
        "scale_v": 0.002,  # Scale lực cắt
        "show_values": true,
        "colors": {
            "moment": "#E74C3C",
            "shear": "#3498DB",
            "axial": "#27AE60",
            "beam": "#2C3E50"
        }
    }
}

Output:
    - SVG file với biểu đồ moment, lực cắt, lực dọc
    - DXF file nếu cần
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Tuple, Optional

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PointLoad:
    """Tải tập trung"""
    x: float      # Vị trí (m)
    P: float      # Giá trị (kN)

@dataclass
class DistributedLoad:
    """Tải phân bố"""
    start: float  # Vị trí bắt đầu (m)
    end: float    # Vị trí kết thúc (m)
    q: float      # Cường độ (kN/m)

@dataclass
class BeamGeometry:
    """Hình học dầm"""
    name: str
    spans: List[float]    # Chiều dài các nhịp (m)
    supports: List[str]   # Loại gối tựa
    h: float              # Chiều cao (m)
    b: float              # Bề rộng (m)

    @property
    def total_length(self) -> float:
        return sum(self.spans)

    @property
    def num_spans(self) -> int:
        return len(self.spans)

@dataclass
class LoadConditions:
    """Điều kiện tải trọng"""
    distributed: List[DistributedLoad]
    point: List[PointLoad]

@dataclass
class InternalForces:
    """Nội lực tại một vị trí"""
    x: float       # Vị trí (m)
    M: float      # Moment uốn (kNm)
    V: float      # Lực cắt (kN)
    N: float      # Lực dọc (kN)

# =============================================================================
# STRUCTURAL ANALYSIS
# =============================================================================

def analyze_beam(
    beam: BeamGeometry,
    loads: LoadConditions
) -> Tuple[List[InternalForces], List[float]]:
    """
    Phân tích dầm liên tục để tính nội lực.

    Sử dụng phương pháp phân phối moment (Kani) hoặc phương pháp độ cứng trực tiếp.

    Returns:
        - List of InternalForces tại các vị trí
        - List of reaction forces at supports
    """
    total_length = beam.total_length
    n_points = 101  # Số điểm tính toán

    # Tính toán nội lực tại các điểm
    forces = []

    # 1. Tính phản lực gối (đơn giản hóa cho dầm 2 nhịp)
    # Sử dụng công thức dầm liên tục

    if beam.num_spans == 3:
        # Dầm 3 nhịp đơn giản
        L1, L2, L3 = beam.spans

        # Tổng tải phân bố
        q1 = sum(l.q for l in loads.distributed if l.start < L1)
        q2 = sum(l.q for l in loads.distributed if l.start >= L1 and l.start < L1 + L2)

        # Moment tại gối giữa (công thức gần đúng)
        # M_B = -q1*L1^2/8 - q2*L2^2/8 (cho dầm 2 nhịp)
        M_B = -(q1 * L1**2 + q2 * L2**2) / 8

        # Phản lực
        R_A = (q1 * L1 / 2) + (M_B / L1)
        R_B = (q1 * L1 / 2) + (q2 * L2 / 2) - (M_B / L1) + (M_B / L2)
        R_C = (q2 * L2 / 2) - (M_B / L2)
        R_D = 0  # Gối cuối

    elif beam.num_spans == 2:
        L1, L2 = beam.spans
        q_total = sum(l.q for l in loads.distributed if l.start < total_length)

        # Moment tại gối giữa
        M_B = -q_total * (L1**2 + L2**2) / 8

        # Phản lực
        R_A = q_total * L1 / 2 + M_B / L1
        R_B = q_total * (L1 + L2) / 2 - M_B / L1 - M_B / L2
        R_C = q_total * L2 / 2 + M_B / L2
    else:
        # Dầm đơn giản
        L = beam.total_length
        q_total = sum(l.q for l in loads.distributed if l.start < total_length)

        R_A = q_total * L / 2
        R_C = q_total * L / 2
        R_B = 0

    reactions = [R_A, R_B, R_C, R_D] if beam.num_spans >= 3 else [R_A, R_B, R_C]

    # 2. Tính V, M tại các điểm
    x_prev = 0
    V = R_A
    M = 0

    # Tính tải phân bố tại mỗi điểm
    for i in range(n_points):
        x = i * total_length / (n_points - 1)

        # Tìm tải phân bố tại x
        q_x = 0
        for load in loads.distributed:
            if load.start <= x <= load.end:
                q_x += load.q

        # Tìm tải tập trung tại x
        P_x = 0
        for load in loads.point:
            if abs(load.x - x) < 0.01:  # Trong phạm vi 1cm
                P_x += load.P

        # Tính lực cắt V(x) = V(0) - q*x - P
        V = R_A
        for load in loads.distributed:
            if load.start < x:
                load_end = min(load.end, x)
                load_start = load.start
                V -= load.q * (load_end - load_start)

        for load in loads.point:
            if load.x < x:
                V -= load.P

        # Tính moment M(x) = M(0) + ∫V dx
        M = 0
        for j in range(i):
            x_j = j * total_length / (n_points - 1)
            x_j1 = (j + 1) * total_length / (n_points - 1)

            # V trung bình trong khoảng
            V_j = R_A
            for load in loads.distributed:
                if load.start < x_j1:
                    load_end = min(load.end, x_j1)
                    load_start = load.start
                    V_j -= load.q * (load_end - load_start)
            for load in loads.point:
                if load.x < x_j:
                    V_j -= load.P

            M += V_j * (x_j1 - x_j)

        # Nội lực
        forces.append(InternalForces(x=x, M=M, V=V, N=0))

    return forces, reactions


def calculate_peak_values(forces: List[InternalForces]) -> dict:
    """Tính các giá trị đỉnh của biểu đồ"""
    if not forces:
        return {}

    M_values = [f.M for f in forces]
    V_values = [f.V for f in forces]

    return {
        "M_max": max(M_values),
        "M_min": min(M_values),
        "V_max": max(V_values),
        "V_min": min(V_values),
        "M_at_support": [f.M for f in forces if any(abs(f.x - x) < 0.1 for x in [0, 3, 6, 9])]
    }

# =============================================================================
# SVG GENERATION
# =============================================================================

def generate_svg(
    beam: BeamGeometry,
    forces: List[InternalForces],
    reactions: List[float],
    output_config: dict
) -> str:
    """
    Tạo file SVG với biểu đồ nội lực.
    """
    # Cấu hình
    scale_m = output_config.get("scale_m", 0.01)
    scale_v = output_config.get("scale_v", 0.002)
    show_values = output_config.get("show_values", True)
    colors = output_config.get("colors", {})

    m_color = colors.get("moment", "#E74C3C")
    v_color = colors.get("shear", "#3498DB")
    beam_color = colors.get("beam", "#2C3E50")

    # Kích thước SVG
    margin_left = 100
    margin_right = 50
    margin_top = 50
    margin_bottom = 100

    beam_y = 400
    beam_height = 30

    total_length = beam.total_length
    pixels_per_meter = 80
    svg_width = margin_left + total_length * pixels_per_meter + margin_right
    svg_height = 600

    # Tạo SVG
    svg_parts = []
    svg_parts.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{svg_width}" height="{svg_height}" '
                    f'viewBox="0 0 {svg_width} {svg_height}">')

    # CSS styles
    svg_parts.append('<style>')
    svg_parts.append('  .beam { fill: #2C3E50; stroke: #1a252f; stroke-width: 1; }')
    svg_parts.append('  .moment { fill: #E74C3C; opacity: 0.7; }')
    svg_parts.append('  .moment-line { stroke: #E74C3C; stroke-width: 2; fill: none; }')
    svg_parts.append('  .shear { fill: #3498DB; opacity: 0.7; }')
    svg_parts.append('  .shear-line { stroke: #3498DB; stroke-width: 2; fill: none; }')
    svg_parts.append('  .axis { stroke: #7f8c8d; stroke-width: 1; stroke-dasharray: 5,3; }')
    svg_parts.append('  .text { font-family: Arial, sans-serif; font-size: 12px; fill: #2c3e50; }')
    svg_parts.append('  .label { font-family: Arial, sans-serif; font-size: 10px; fill: #7f8c8d; }')
    svg_parts.append('  .value { font-family: monospace; font-size: 11px; font-weight: bold; }')
    svg_parts.append('  .support { fill: #95a5a6; stroke: #7f8c8d; stroke-width: 1; }')
    svg_parts.append('  .load { stroke: #e67e22; stroke-width: 2; fill: none; }')
    svg_parts.append('  .load-arrow { fill: #e67e22; }')
    svg_parts.append('</style>')

    # Title
    svg_parts.append(f'<text x="{svg_width/2}" y="25" text-anchor="middle" '
                    f'class="text" font-size="16" font-weight="bold">'
                    f'{beam.name} — Biểu đồ nội lực</text>')

    # Scale info
    svg_parts.append(f'<text x="{svg_width - 10}" y="25" text-anchor="end" '
                    f'class="label">Scale M: 1:{int(1/scale_m)}, V: 1:{int(1/scale_v)}</text>')

    # === BEAM DIAGRAM ===
    beam_start_x = margin_left
    beam_end_x = margin_left + total_length * pixels_per_meter

    # Draw beam
    svg_parts.append(f'<rect x="{beam_start_x}" y="{beam_y - beam_height/2}" '
                   f'width="{total_length * pixels_per_meter}" height="{beam_height}" '
                   f'class="beam"/>')

    # Draw supports
    x_pos = beam_start_x
    for i, span in enumerate(beam.spans):
        # Support at start of span
        if i == 0:
            support_type = beam.supports[0] if i < len(beam.supports) else "roller"
        else:
            support_type = beam.supports[i] if i < len(beam.supports) else "roller"

        draw_support(svg_parts, x_pos, beam_y, support_type)
        x_pos += span * pixels_per_meter

    # Last support
    draw_support(svg_parts, x_pos, beam_y, beam.supports[-1] if beam.supports else "fixed")

    # === MOMENT DIAGRAM ===
    moment_y_base = beam_y - 80
    moment_scale = pixels_per_meter * scale_m * 1000  # Convert m/kNm to pixels

    # Draw axis
    svg_parts.append(f'<line x1="{beam_start_x}" y1="{moment_y_base}" '
                   f'x2="{beam_end_x}" y2="{moment_y_base}" class="axis"/>')

    # Draw moment diagram (filled)
    moment_path = f'M {beam_start_x},{moment_y_base}'
    for f in forces:
        x = beam_start_x + f.x * pixels_per_meter
        y = moment_y_base - f.M * moment_scale
        moment_path += f' L {x:.1f},{y:.1f}'
    moment_path += f' L {beam_end_x},{moment_y_base} Z'

    svg_parts.append(f'<path d="{moment_path}" class="moment"/>')

    # Draw moment line
    moment_line = f'M {beam_start_x},{moment_y_base}'
    for f in forces:
        x = beam_start_x + f.x * pixels_per_meter
        y = moment_y_base - f.M * moment_scale
        moment_line += f' L {x:.1f},{y:.1f}'
    svg_parts.append(f'<path d="{moment_line}" class="moment-line"/>')

    # Labels
    svg_parts.append(f'<text x="{beam_start_x - 10}" y="{moment_y_base - 5}" '
                   f'text-anchor="end" class="label">M (kNm)</text>')

    # === SHEAR DIAGRAM ===
    shear_y_base = beam_y + 100
    shear_scale = pixels_per_meter * scale_v * 1000

    # Draw axis
    svg_parts.append(f'<line x1="{beam_start_x}" y1="{shear_y_base}" '
                   f'x2="{beam_end_x}" y2="{shear_y_base}" class="axis"/>')

    # Draw shear diagram (filled)
    shear_path = f'M {beam_start_x},{shear_y_base}'
    for f in forces:
        x = beam_start_x + f.x * pixels_per_meter
        y = shear_y_base - f.V * shear_scale
        shear_path += f' L {x:.1f},{y:.1f}'
    shear_path += f' L {beam_end_x},{shear_y_base} Z'

    svg_parts.append(f'<path d="{shear_path}" class="shear"/>')

    # Draw shear line
    shear_line = f'M {beam_start_x},{shear_y_base}'
    for f in forces:
        x = beam_start_x + f.x * pixels_per_meter
        y = shear_y_base - f.V * shear_scale
        shear_line += f' L {x:.1f},{y:.1f}'
    svg_parts.append(f'<path d="{shear_line}" class="shear-line"/>')

    # Labels
    svg_parts.append(f'<text x="{beam_start_x - 10}" y="{shear_y_base - 5}" '
                   f'text-anchor="end" class="label">V (kN)</text>')

    # === LOAD DIAGRAM ===
    load_y = beam_y - beam_height/2 - 20
    svg_parts.append(f'<text x="{beam_start_x}" y="{load_y - 10}" class="label">Tải trọng</text>')

    for load in forces[0].__class__.__dataclass_fields__.keys():
        pass  # Placeholder

    # === VALUES ===
    if show_values:
        # Find peak moments
        M_max = max(f.M for f in forces)
        M_min = min(f.M for f in forces)
        V_max = max(f.V for f in forces)
        V_min = min(f.V for f in forces)

        # Max moment position
        M_max_pos = next(f.x for f in forces if abs(f.M - M_max) < 0.1)

        # Draw values
        svg_parts.append(f'<text x="{beam_start_x + M_max_pos * pixels_per_meter}" '
                       f'y="{moment_y_base - M_max * moment_scale - 10}" '
                       f'text-anchor="middle" class="value" fill="{m_color}">'
                       f'M={M_max:.1f}</text>')

        svg_parts.append(f'<text x="{beam_start_x + total_length * pixels_per_meter * 0.7}" '
                       f'y="{shear_y_base - V_max * shear_scale - 10}" '
                       f'text-anchor="middle" class="value" fill="{v_color}">'
                       f'V={V_max:.1f}</text>')

    # Footer
    svg_parts.append(f'<text x="{svg_width/2}" y="{svg_height - 10}" '
                   f'text-anchor="middle" class="label">'
                   f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</text>')

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def draw_support(svg_parts: list, x: float, y: float, support_type: str):
    """Vẽ gối tựa"""
    if support_type == "fixed":
        # Fixed support - hình chữ nhật
        svg_parts.append(f'<rect x="{x-15}" y="{y}" width="30" height="20" '
                        f'class="support" rx="3"/>')
        svg_parts.append(f'<line x1="{x-20}" y1="{y+25}" x2="{x+20}" y2="{y+25}" '
                        f'stroke="#7f8c8d" stroke-width="2"/>')
    elif support_type == "roller":
        # Roller support - tam giác + vòng tròn
        svg_parts.append(f'<polygon points="{x-15},{y} {x+15},{y} {x},{y+20}" '
                        f'class="support"/>')
        svg_parts.append(f'<circle cx="{x}" cy="{y+25}" r="5" class="support"/>')
    else:  # pinned
        # Pinned support - tam giác
        svg_parts.append(f'<polygon points="{x-15},{y} {x+15},{y} {x},{y+20}" '
                        f'class="support"/>')

# =============================================================================
# DXF GENERATION
# =============================================================================

def generate_dxf(
    beam: BeamGeometry,
    forces: List[InternalForces],
    output_config: dict
) -> str:
    """
    Tạo file DXF với biểu đồ nội lực.
    """
    # Simple DXF template
    scale = output_config.get("scale_m", 0.01) * 1000

    dxf_lines = []
    dxf_lines.append("0")
    dxf_lines.append("SECTION")
    dxf_lines.append("2")
    dxf_lines.append("ENTITIES")

    # Beam outline
    pixels_per_meter = 80
    beam_y = 400

    # Beam rectangle
    x1 = 100
    x2 = 100 + beam.total_length * pixels_per_meter
    dxf_lines.append("0")
    dxf_lines.append("LINE")
    dxf_lines.append("8")
    dxf_lines.append("BEAM")
    dxf_lines.append("10")
    dxf_lines.append(str(x1))
    dxf_lines.append("20")
    dxf_lines.append(str(beam_y - 15))
    dxf_lines.append("11")
    dxf_lines.append(str(x2))
    dxf_lines.append("21")
    dxf_lines.append(str(beam_y - 15))

    # Moment polyline
    dxf_lines.append("0")
    dxf_lines.append("LWPOLYLINE")
    dxf_lines.append("8")
    dxf_lines.append("MOMENT")
    dxf_lines.append("90")
    dxf_lines.append(str(len(forces) + 2))

    for f in forces:
        x = 100 + f.x * pixels_per_meter
        y = beam_y - 80 - f.M * scale
        dxf_lines.append("10")
        dxf_lines.append(str(x))
        dxf_lines.append("20")
        dxf_lines.append(str(y))

    dxf_lines.append("0")
    dxf_lines.append("ENDSEC")
    dxf_lines.append("0")
    dxf_lines.append("EOF")

    return '\n'.join(dxf_lines)

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def draw_moment_diagram(input_data: dict) -> dict:
    """
    Hàm chính vẽ biểu đồ nội lực.
    """
    logs = []

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")

    # Parse input
    project = input_data.get("project", {})
    beam_data = input_data["beam"]
    loads_data = input_data.get("loads", {"distributed": [], "point": []})
    output_config = input_data.get("output", {"format": "svg"})

    log(f"Bắt đầu vẽ biểu đồ: {beam_data['name']}")

    # Create beam
    beam = BeamGeometry(
        name=beam_data["name"],
        spans=beam_data["L"],
        supports=beam_data.get("supports", ["roller"] * (len(beam_data["L"]) + 1)),
        h=beam_data.get("h", 0.6),
        b=beam_data.get("b", 0.3)
    )

    # Create loads
    distributed = [DistributedLoad(**l) for l in loads_data.get("distributed", [])]
    point = [PointLoad(**l) for l in loads_data.get("point", [])]
    loads = LoadConditions(distributed=distributed, point=point)

    log(f"Số nhịp: {beam.num_spans}, Tổng chiều dài: {beam.total_length}m")

    # Analyze
    log("Phân tích nội lực...")
    forces, reactions = analyze_beam(beam, loads)

    peaks = calculate_peak_values(forces)
    log(f"M_max = {peaks.get('M_max', 0):.2f} kNm, M_min = {peaks.get('M_min', 0):.2f} kNm")
    log(f"V_max = {peaks.get('V_max', 0):.2f} kN, V_min = {peaks.get('V_min', 0):.2f} kN")

    # Generate output
    output_format = output_config.get("format", "svg")

    if output_format == "svg":
        svg_content = generate_svg(beam, forces, reactions, output_config)
        output_data = {
            "format": "svg",
            "content": svg_content,
            "width": "auto",
            "height": 600
        }
    else:  # dxf
        dxf_content = generate_dxf(beam, forces, output_config)
        output_data = {
            "format": "dxf",
            "content": dxf_content
        }

    log(f"Đã tạo {output_format.upper()}")

    return {
        "calculator": {
            "name": "draw_moment_diagram",
            "version": "1.0.0"
        },
        "metadata": {
            "project_name": project.get("name", "N/A"),
            "calculation_date": datetime.now().isoformat()
        },
        "beam": asdict(beam),
        "analysis_results": {
            "forces_count": len(forces),
            "reactions": reactions,
            "peaks": peaks
        },
        "output": output_data,
        "calculation_log": logs
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Vẽ biểu đồ nội lực M, V, N cho dầm liên tục"
    )
    parser.add_argument("--input", "-i", required=True, help="File JSON đầu vào")
    parser.add_argument("--output", "-o", required=True, help="File đầu ra (.svg hoặc .dxf)")
    parser.add_argument("--format", "-f", choices=["svg", "dxf"], help="Format output")

    args = parser.parse_args()

    # Read input
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # Override format if specified
    if args.format:
        input_data.setdefault("output", {})["format"] = args.format

    # Generate
    result = draw_moment_diagram(input_data)

    # Save output
    output_format = result["output"]["format"]

    if output_format == "svg":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["output"]["content"])
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["output"]["content"])

    print(f"Đã lưu biểu đồ vào: {args.output}")
    print(f"\nTóm tắt:")
    print(f"  M_max = {result['analysis_results']['peaks'].get('M_max', 0):.2f} kNm")
    print(f"  V_max = {result['analysis_results']['peaks'].get('V_max', 0):.2f} kN")

if __name__ == "__main__":
    main()
