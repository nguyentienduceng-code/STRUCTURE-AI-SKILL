# -*- coding: utf-8 -*-
"""
draw_rc_wall.py — Ve mat cat va chan BTCT

Tinh nang:
- Ve mat cat ngang va chan BTCT
- Hien thi cot thep doc va cot dai
- Danh kich thuoc day du
- Xuat PNG chat luong cao (300 DPI)

Su dung:
    python draw_rc_wall.py --out matcat_vach.png \
        --thickness 200 --height 3000 \
        --n_bars 12 --bar_dia 18 \
        --stirrup_dia 10 --stirrup_spacing 200 \
        --cover 25

Author: AI Assistant
Version: 1.0.0
"""

import sys
import os

# Add project root to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
tech_illustrator_dir = os.path.dirname(scripts_dir)
modules_dir = os.path.join(tech_illustrator_dir, 'modules')
for d in [tech_illustrator_dir, modules_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

from drawing_standards import DrawingStandards, export_figure

# Fix Unicode for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import argparse
import math


def draw_rc_wall_section(
    output_path: str,
    thickness: float = 200,
    height: float = 3000,
    n_bars: int = 12,
    bar_dia: float = 18,
    stirrup_dia: float = 10,
    stirrup_spacing: float = 200,
    cover: float = 25,
    wall_length: float = 1000,
    concrete_grade: str = "B25",
    steel_grade: str = "CB400-V",
    show_coupling_beams: bool = False
):
    """
    Ve mat cat va chan BTCT.

    Args:
        output_path: Duong dan xuat file
        thickness: Day va chan (mm)
        height: Chieu cao va chan (mm)
        n_bars: So thanh cot thep doc tren mat cat
        bar_dia: Duong kinh cot thep doc (mm)
        stirrup_dia: Duong kinh cot dai (mm)
        stirrup_spacing: Khoang cach cot dai (mm)
        cover: Lop bao ve be tong (mm)
        wall_length: Chieu dai hien thi (mm)
        concrete_grade: Cap be tong
        steel_grade: Loai thep
        show_coupling_beams: Hien thi dam lien ket (coupling beams)
    """
    # Setup figure
    fig, ax = plt.subplots(figsize=(12, 10))

    # Calculate dimensions
    t = thickness / 2  # Half thickness for center-line drawing
    half_length = wall_length / 2

    # === DRAW CONCRETE WALL ===
    concrete_rect = patches.Rectangle(
        (-t, 0), thickness, height,
        linewidth=2,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(concrete_rect)

    # === DRAW VERTICAL REBARS ===
    # Calculate bar spacing
    available_length = wall_length - 2 * cover
    bar_spacing = available_length / (n_bars - 1) if n_bars > 1 else available_length

    for i in range(n_bars):
        x = -half_length + cover + i * bar_spacing
        # Check if within wall thickness
        if -t + cover <= x <= t - cover:
            # Draw rebar as rectangle (section view)
            bar_width = bar_dia * 3  # Scale for visibility
            bar_height = height
            bar = patches.Rectangle(
                (x - bar_width/2, 0),
                bar_width, bar_height,
                linewidth=0.5,
                edgecolor='#922B21',
                facecolor='#C0392B',
                zorder=3
            )
            ax.add_patch(bar)

    # === DRAW STIRRUPS (horizontal lines representing ties) ===
    n_stirrups = int(height / stirrup_spacing) + 1
    for i in range(n_stirrups):
        y = i * stirrup_spacing
        if y <= height:
            ax.plot([-t + cover, t - cover], [y, y],
                   color='#E74C3C', linewidth=1.5, linestyle='--', zorder=2)

    # === DIMENSIONING ===
    dim_offset = 50

    # Wall thickness
    ax.annotate('',
        xy=(-t, -dim_offset),
        xytext=(t, -dim_offset),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(0, -dim_offset - 15,
            f't = {thickness}mm',
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Wall height
    ax.annotate('',
        xy=(-t - dim_offset, 0),
        xytext=(-t - dim_offset, height),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(-t - dim_offset - 15, height/2,
            f'H = {height}mm',
            ha='center', va='center', fontsize=10, color='#27AE60', fontweight='bold',
            rotation=90)

    # Wall length (if showing partial)
    if wall_length < 2000:
        ax.annotate('',
            xy=(-half_length, -dim_offset),
            xytext=(half_length, -dim_offset),
            arrowprops=dict(arrowstyle='<->', color='#8E44AD', lw=1.5))
        ax.text(0, -dim_offset - 15,
                f'L shown = {wall_length}mm',
                ha='center', va='top', fontsize=9, color='#8E44AD')

    # Cover dimension
    ax.annotate('',
        xy=(-t, cover),
        xytext=(-t + cover, cover),
        arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1))
    ax.text(-t + cover/2, cover + 20,
            f'a={cover}',
            ha='center', va='bottom', fontsize=8, color='#E67E22')

    # === ANNOTATIONS ===
    # Rebar annotation
    ax.annotate(f'{n_bars}xd{bar_dia} ({steel_grade})\nVertical bars',
        xy=(half_length - cover, height/2),
        xytext=(half_length + 150, height/2),
        arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.5),
        fontsize=10, color='#C0392B', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'),
        zorder=10
    )

    # Stirrup annotation
    ax.annotate(f'd{stirrup_dia}@{stirrup_spacing} ties',
        xy=(half_length - cover, height * 0.75),
        xytext=(half_length + 150, height * 0.75),
        arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=1.5),
        fontsize=9, color='#E74C3C',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E74C3C'),
        zorder=10
    )

    # === SETUP AXES ===
    padding = 200
    ax.set_xlim(-t - padding, half_length + padding * 3)
    ax.set_ylim(-padding, height + padding * 0.5)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.set_title(f'MAT CAT VA CHAN BTCT\nt={thickness}mm x H={height}mm',
                  fontsize=14, fontweight='bold', pad=20)

    # === TECHNICAL NOTES ===
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"1. Va chan BTCT day {thickness}mm, cao {height}mm, be tong {concrete_grade}.\n"
        f"2. Cot thep doc: {n_bars} thanh d{bar_dia}mm, loai {steel_grade} (Rs={get_rs(steel_grade)}MPa).\n"
        f"3. Cot dai: d{stirrup_dia}@{stirrup_spacing}mm, loai CB240-T.\n"
        f"4. Lop bao ve: a = {cover}mm (theo TCVN 5574:2018, Dieu 10.3.1).\n"
        f"5. Khoang cach cot thep doc: {bar_spacing:.0f}mm (co the tinh toan theo moment).\n"
        f"6. Tieu chuan ap dung: TCVN 5574:2018.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    # Export
    plt.tight_layout(rect=[0, 0.15, 1, 0.95])
    export_figure(fig, output_path, dpi=300)


def draw_rc_wall_plan(
    output_path: str,
    thickness: float = 200,
    wall_length: float = 6000,
    n_bars: int = 30,
    bar_dia: float = 18,
    cover: float = 25,
    concrete_grade: str = "B25",
    steel_grade: str = "CB400-V"
):
    """
    Ve mat bang va chan BTCT (plan view).

    Args:
        output_path: Duong dan xuat file
        thickness: Day va chan (mm)
        wall_length: Chieu dai va chan (mm)
        n_bars: So thanh cot thep doc
        bar_dia: Duong kinh cot thep doc (mm)
        cover: Lop bao ve (mm)
    """
    fig, ax = plt.subplots(figsize=(14, 4))

    half_length = wall_length / 2

    # === DRAW WALL OUTLINE ===
    wall_rect = patches.Rectangle(
        (0, 0), wall_length, thickness,
        linewidth=2.5,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(wall_rect)

    # === DRAW VERTICAL REBARS ===
    available_length = wall_length - 2 * cover
    bar_spacing = available_length / (n_bars - 1) if n_bars > 1 else available_length

    for i in range(n_bars):
        x = cover + i * bar_spacing
        if cover <= x <= wall_length - cover:
            # Draw rebar as circle (plan view)
            bar = plt.Circle((x, thickness/2), bar_dia * 2,
                            fill=True, facecolor='#C0392B',
                            edgecolor='#922B21', linewidth=0.5, zorder=3)
            ax.add_patch(bar)

    # === DIMENSIONING ===
    dim_offset = 40

    # Wall length
    ax.annotate('',
        xy=(0, -dim_offset),
        xytext=(wall_length, -dim_offset),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(wall_length/2, -dim_offset - 15,
            f'L = {wall_length}mm',
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Wall thickness
    ax.annotate('',
        xy=(wall_length + dim_offset, 0),
        xytext=(wall_length + dim_offset, thickness),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(wall_length + dim_offset + 15, thickness/2,
            f't = {thickness}mm',
            ha='left', va='center', fontsize=10, color='#27AE60', fontweight='bold',
            rotation=90)

    # Bar spacing
    if n_bars > 1:
        ax.annotate('',
            xy=(cover, thickness + dim_offset),
            xytext=(cover + bar_spacing, thickness + dim_offset),
            arrowprops=dict(arrowstyle='<->', color='#8E44AD', lw=1))
        ax.text(cover + bar_spacing/2, thickness + dim_offset + 10,
                f's = {bar_spacing:.0f}',
                ha='center', va='bottom', fontsize=8, color='#8E44AD')

    # === ANNOTATION ===
    ax.annotate(f'{n_bars}xd{bar_dia}\n({steel_grade})',
        xy=(wall_length/2, thickness/2),
        xytext=(wall_length + 150, thickness/2),
        arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.5),
        fontsize=10, color='#C0392B', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'),
        zorder=10)

    # === SETUP ===
    ax.set_xlim(-100, wall_length + 250)
    ax.set_ylim(-100, thickness + 200)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'MAT BANG VA CHAN BTCT - L={wall_length}mm',
                 fontsize=14, fontweight='bold', pad=20)

    # Export
    plt.tight_layout()
    export_figure(fig, output_path, dpi=300)


def get_rs(steel_grade: str) -> int:
    """Tra cuu Rs theo loai thep."""
    rs_map = {
        "CB300-V": 270,
        "CB400-V": 350,
        "CB500-V": 415,
        "CB240-T": 215,
    }
    return rs_map.get(steel_grade, 350)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve mat cat va chan BTCT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_rc_wall.py --out vach_section.png --thickness 200 --height 3000
  python draw_rc_wall.py --out vach_plan.png --plan --wall_length 6000
        """
    )

    parser.add_argument("--out", required=True, help="Duong dan xuat file")
    parser.add_argument("--plan", action="store_true", help="Ve mat bang (plan) thay vi mat cat")
    parser.add_argument("--thickness", type=float, default=200, help="Day va chan (mm)")
    parser.add_argument("--height", type=float, default=3000, help="Chieu cao va chan (mm)")
    parser.add_argument("--wall_length", type=float, default=1000, help="Chieu dai hien thi (mm)")
    parser.add_argument("--n_bars", type=int, default=12, help="So thanh cot thep doc")
    parser.add_argument("--bar_dia", type=float, default=18, help="Duong kinh cot thep doc (mm)")
    parser.add_argument("--stirrup_dia", type=float, default=10, help="Duong kinh cot dai (mm)")
    parser.add_argument("--stirrup_spacing", type=float, default=200, help="Khoang cach cot dai (mm)")
    parser.add_argument("--cover", type=float, default=25, help="Lop bao ve (mm)")
    parser.add_argument("--concrete", type=str, default="B25", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB400-V", help="Loai thep")

    args = parser.parse_args()

    if args.plan:
        draw_rc_wall_plan(
            args.out,
            thickness=args.thickness,
            wall_length=args.wall_length,
            n_bars=args.n_bars,
            bar_dia=args.bar_dia,
            cover=args.cover,
            concrete_grade=args.concrete,
            steel_grade=args.steel
        )
    else:
        draw_rc_wall_section(
            args.out,
            thickness=args.thickness,
            height=args.height,
            wall_length=args.wall_length,
            n_bars=args.n_bars,
            bar_dia=args.bar_dia,
            stirrup_dia=args.stirrup_dia,
            stirrup_spacing=args.stirrup_spacing,
            cover=args.cover,
            concrete_grade=args.concrete,
            steel_grade=args.steel
        )

    print(f"[OK] Da xuat va chan BTCT: {args.out}")
