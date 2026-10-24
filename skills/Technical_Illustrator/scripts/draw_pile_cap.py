# -*- coding: utf-8 -*-
"""
draw_pile_cap.py — Ve mat cat & mat bang dai coc

Tinh nang:
- Ve mat cat A-A va B-B cua dai coc
- Ve mat bang dai coc (plan view)
- Hien thi coc, cot thep coc, cot thep dai
- Danh kich thuoc day du
- Xuat PNG chat luong cao (300 DPI)

Su dung:
    python draw_pile_cap.py --out dai_coc.png \
        --L 4000 --B 3000 --H 1200 \
        --pile_diameter 600 --n_piles_x 3 --n_piles_y 2 \
        --pile_spacing_x 1500 --pile_spacing_y 1500 \
        --main_rebar_dia 25 --main_rebar_spacing 150 \
        --cover 75

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

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import argparse


def draw_pile_cap_section(
    output_path: str,
    L: float = 4000,
    B: float = 3000,
    H: float = 1200,
    pile_diameter: float = 600,
    n_piles_x: int = 3,
    n_piles_y: int = 2,
    pile_spacing_x: float = 1500,
    pile_spacing_y: float = 1500,
    pile_cover: float = 75,
    main_rebar_dia: float = 25,
    main_rebar_spacing: float = 150,
    cover: float = 50,
    col_width: float = 600,
    col_depth: float = 600,
    concrete_grade: str = "B25",
    steel_grade: str = "CB400-V",
    view: str = "A-A"
):
    """
    Ve mat cat dai coc.

    Args:
        output_path: Duong dan xuat file
        L: Chieu dai dai coc (mm)
        B: Chieu rong dai coc (mm)
        H: Chieu cao dai coc (mm)
        pile_diameter: Duong kinh coc (mm)
        n_piles_x: So coc theo phuong x
        n_piles_y: So coc theo phuong y
        pile_spacing_x: Khoang cach coc theo x (mm)
        pile_spacing_y: Khoang cach coc theo y (mm)
        pile_cover: Khoang cach tu mat coc den canh dai (mm)
        main_rebar_dia: Duong kinh cot thep chinh (mm)
        main_rebar_spacing: Khoang cach cot thep chinh (mm)
        cover: Lop bao ve (mm)
        col_width, col_depth: Kich thuoc cot (mm)
        concrete_grade: Cap be tong
        steel_grade: Loai thep
        view: "A-A" hoac "B-B"
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Calculate pile positions
    pile_R = pile_diameter / 2

    if view == "A-A":
        # Section A-A: view along x-axis (show y direction)
        # Pile positions along y
        pile_y_positions = []
        offset_y = (B - (n_piles_y - 1) * pile_spacing_y) / 2
        for i in range(n_piles_y):
            y = offset_y + i * pile_spacing_y
            pile_y_positions.append(y)

        # Draw foundation
        foundation = patches.Rectangle(
            (0, 0), B, H,
            linewidth=2.5,
            edgecolor='#2C3E50',
            facecolor='#D5DBDB',
            hatch='///',
            zorder=1
        )
        ax.add_patch(foundation)

        # Draw piles (as circles in section)
        for y in pile_y_positions:
            pile = plt.Circle((B/2, pile_cover + pile_R), pile_R,
                            fill=True, facecolor='#AEB6BF',
                            edgecolor='#2C3E50', linewidth=2,
                            zorder=2)
            ax.add_patch(pile)

            # Rebar in pile (as small circles)
            n_rebars = int(pile_diameter / main_rebar_spacing)
            for j in range(n_rebars):
                angle = 2 * np.pi * j / n_rebars
                rx = B/2 + (pile_R - pile_cover) * np.cos(angle)
                ry = pile_cover + pile_R + (pile_R - pile_cover) * np.sin(angle)
                if pile_cover <= rx <= B - pile_cover and pile_cover + pile_R - (pile_R - pile_cover) <= ry <= pile_cover + pile_R + (pile_R - pile_cover):
                    reb = plt.Circle((rx, ry), main_rebar_dia / 2 * 3,
                                   fill=True, facecolor='#C0392B',
                                   edgecolor='#922B21', linewidth=0.5, zorder=3)
                    ax.add_patch(reb)

        # Column
        col = patches.Rectangle(
            (B/2 - col_width/2, H), col_width, 300,
            linewidth=2,
            edgecolor='#2C3E50',
            facecolor='#AEB6BF',
            hatch='...',
            zorder=3
        )
        ax.add_patch(col)

        # Dimension x (B direction)
        dim_y = -50
        ax.annotate('',
            xy=(0, dim_y), xytext=(B, dim_y),
            arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
        ax.text(B/2, dim_y - 15, f'B = {B}mm',
                ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

        # Dimension y (pile spacing)
        if len(pile_y_positions) > 1:
            sp = pile_y_positions[1] - pile_y_positions[0]
            mid_y = (pile_y_positions[0] + pile_y_positions[1]) / 2
            ax.annotate('',
                xy=(B + 50, pile_y_positions[0]),
                xytext=(B + 50, pile_y_positions[1]),
                arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
            ax.text(B + 80, mid_y, f'sp={sp:.0f}',
                    ha='left', va='center', fontsize=9, color='#27AE60', fontweight='bold')

        # Height dimension
        ax.annotate('',
            xy=(-60, 0), xytext=(-60, H),
            arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
        ax.text(-80, H/2, f'H = {H}mm',
                ha='center', va='center', fontsize=10, color='#E74C3C', fontweight='bold',
                rotation=90)

        ax.set_xlim(-100, B + 200)
        ax.set_ylim(-100, H + 400)
        ax.set_title(f'MAT CAT A-A: DAI COC {B}x{L}x{H}mm ({n_piles_y}x{n_piles_x} coc)',
                     fontsize=14, fontweight='bold', pad=20)

    else:  # B-B
        # Section B-B: view along y-axis
        pile_x_positions = []
        offset_x = (L - (n_piles_x - 1) * pile_spacing_x) / 2
        for i in range(n_piles_x):
            x = offset_x + i * pile_spacing_x
            pile_x_positions.append(x)

        # Draw foundation
        foundation = patches.Rectangle(
            (0, 0), L, H,
            linewidth=2.5,
            edgecolor='#2C3E50',
            facecolor='#D5DBDB',
            hatch='///',
            zorder=1
        )
        ax.add_patch(foundation)

        # Draw piles
        for x in pile_x_positions:
            pile = plt.Circle((x, pile_cover + pile_R), pile_R,
                            fill=True, facecolor='#AEB6BF',
                            edgecolor='#2C3E50', linewidth=2,
                            zorder=2)
            ax.add_patch(pile)

        # Column
        col = patches.Rectangle(
            (L/2 - col_depth/2, H), col_depth, 300,
            linewidth=2,
            edgecolor='#2C3E50',
            facecolor='#AEB6BF',
            hatch='...',
            zorder=3
        )
        ax.add_patch(col)

        # Dimensions
        ax.annotate('',
            xy=(0, -50), xytext=(L, -50),
            arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
        ax.text(L/2, -65, f'L = {L}mm',
                ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

        ax.annotate('',
            xy=(-60, 0), xytext=(-60, H),
            arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
        ax.text(-80, H/2, f'H = {H}mm',
                ha='center', va='center', fontsize=10, color='#E74C3C', fontweight='bold',
                rotation=90)

        ax.set_xlim(-100, L + 200)
        ax.set_ylim(-100, H + 400)
        ax.set_title(f'MAT CAT B-B: DAI COC {L}x{B}x{H}mm ({n_piles_x}x{n_piles_y} coc)',
                     fontsize=14, fontweight='bold', pad=20)

    ax.set_aspect('equal')
    ax.axis('off')

    # Pile count annotation
    ax.annotate(f'{n_piles_x * n_piles_y} coc x D{pile_diameter}mm\n(plan layout)',
        xy=(L/2 if view == "B-B" else B/2, H/2),
        xytext=(L/2 + 150 if view == "B-B" else B/2 + 150, H/2),
        arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=1.5),
        fontsize=10, color='#8E44AD', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8', edgecolor='#8E44AD'),
        zorder=10)

    # Technical notes
    total_piles = n_piles_x * n_piles_y
    note_text = (
        f"GHI CHU KY THUAT - MAT CAT {view}:\n"
        f"1. Dai coc {L}x{B}x{H}mm, be tong {concrete_grade}.\n"
        f"2. Coc: {total_piles} coc x D{pile_diameter}mm, khoang cach {pile_spacing_x}x{pile_spacing_y}mm.\n"
        f"3. Cot thep coc: d{main_rebar_dia}@{main_rebar_spacing}mm, loai {steel_grade}.\n"
        f"4. Lop bao ve: a = {cover}mm (TCVN 5574:2018, Dieu 10.3.1).\n"
        f"5. Tieu chuan: TCVN 5574:2018, TCVN 10304:2025.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.12, 1, 0.95])
    export_figure(fig, output_path, dpi=300)


def draw_pile_cap_plan(
    output_path: str,
    L: float = 4000,
    B: float = 3000,
    pile_diameter: float = 600,
    n_piles_x: int = 3,
    n_piles_y: int = 2,
    pile_spacing_x: float = 1500,
    pile_spacing_y: float = 1500,
    col_width: float = 600,
    col_depth: float = 600,
    pile_cover: float = 75,
    main_rebar_dia: float = 25,
    cover: float = 50,
    concrete_grade: str = "B25",
    steel_grade: str = "CB400-V"
):
    """
    Ve mat bang dai coc (plan view).

    Args:
        output_path: Duong dan xuat file
        (cac tham so khac nhu draw_pile_cap_section)
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    pile_R = pile_diameter / 2

    # Draw foundation outline
    foundation = patches.Rectangle(
        (0, 0), L, B,
        linewidth=2.5,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(foundation)

    # Calculate pile positions
    pile_x_offset = (L - (n_piles_x - 1) * pile_spacing_x) / 2
    pile_y_offset = (B - (n_piles_y - 1) * pile_spacing_y) / 2

    pile_positions = []
    for i in range(n_piles_x):
        for j in range(n_piles_y):
            x = pile_x_offset + i * pile_spacing_x
            y = pile_y_offset + j * pile_spacing_y
            pile_positions.append((x, y))

            # Draw pile
            pile = plt.Circle((x, y), pile_R,
                           fill=True, facecolor='#AEB6BF',
                           edgecolor='#2C3E50', linewidth=2,
                           zorder=2)
            ax.add_patch(pile)

            # Rebar in pile (small circles)
            n_rebars = 8
            for k in range(n_rebars):
                angle = 2 * np.pi * k / n_rebars
                rx = x + (pile_R - pile_cover) * np.cos(angle) * 0.7
                ry = y + (pile_R - pile_cover) * np.sin(angle) * 0.7
                reb = plt.Circle((rx, ry), main_rebar_dia / 2 * 2.5,
                               fill=True, facecolor='#C0392B',
                               edgecolor='#922B21', linewidth=0.5, zorder=3)
                ax.add_patch(reb)

    # Draw column
    col = patches.Rectangle(
        (L/2 - col_width/2, B/2 - col_depth/2),
        col_width, col_depth,
        linewidth=2,
        edgecolor='#2C3E50',
        facecolor='#7F8C8D',
        hatch='...',
        zorder=3
    )
    ax.add_patch(col)

    # === DIMENSIONS ===
    dim_offset = 80

    # Foundation dimensions
    ax.annotate('',
        xy=(0, -dim_offset), xytext=(L, -dim_offset),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(L/2, -dim_offset - 20, f'L = {L}mm',
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    ax.annotate('',
        xy=(-dim_offset, 0), xytext=(-dim_offset, B),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(-dim_offset - 20, B/2, f'B = {B}mm',
            ha='center', va='center', fontsize=10, color='#27AE60', fontweight='bold',
            rotation=90)

    # Pile spacing
    if n_piles_x > 1:
        ax.annotate('',
            xy=(pile_x_offset, -dim_offset/2),
            xytext=(pile_x_offset + pile_spacing_x, -dim_offset/2),
            arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1))
        ax.text(pile_x_offset + pile_spacing_x/2, -dim_offset/2 - 15,
                f'sx={pile_spacing_x:.0f}',
                ha='center', va='top', fontsize=8, color='#E67E22')

    if n_piles_y > 1:
        ax.annotate('',
            xy=(-dim_offset/2, pile_y_offset),
            xytext=(-dim_offset/2, pile_y_offset + pile_spacing_y),
            arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1))
        ax.text(-dim_offset/2 - 15, pile_y_offset + pile_spacing_y/2,
                f'sy={pile_spacing_y:.0f}',
                ha='center', va='center', fontsize=8, color='#E67E22',
                rotation=90)

    # === ANNOTATIONS ===
    total_piles = n_piles_x * n_piles_y
    ax.annotate(f'{total_piles} coc x D{pile_diameter}mm\n'
               f'({n_piles_x} x {n_piles_y})\n'
               f'Cot thep: d{main_rebar_dia}@{main_rebar_dia*6}mm',
        xy=(L/2, B/2),
        xytext=(L + 150, B/2),
        arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.5),
        fontsize=9, color='#C0392B', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'),
        zorder=10)

    # === SETUP ===
    ax.set_xlim(-200, L + 350)
    ax.set_ylim(-200, B + 200)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'MAT BANG DAI COC: {L}x{B}mm ({n_piles_x}x{n_piles_y} coc)',
                 fontsize=14, fontweight='bold', pad=20)

    # === NOTES ===
    note_text = (
        f"GHI CHU KY THUAT - MAT BANG:\n"
        f"1. Dai coc {L}x{B}mm (mat bang), be tong {concrete_grade}.\n"
        f"2. Coc: {total_piles} coc x D{pile_diameter}mm, bo tri ({n_piles_x}x{n_piles_y}),\n"
        f"   khoang cach sx={pile_spacing_x}mm, sy={pile_spacing_y}mm.\n"
        f"3. Cot thep doc coc: d{main_rebar_dia}mm, loai {steel_grade}.\n"
        f"4. Cot cot: {col_width}x{col_depth}mm (xem mat cat A-A, B-B).\n"
        f"5. Tieu chuan: TCVN 5574:2018, TCVN 10304:2025.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.12, 1, 0.95])
    export_figure(fig, output_path, dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve dai coc: mat cat A-A, B-B va mat bang",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  # Mat cat A-A
  python draw_pile_cap.py --out section_A.png --view A-A \\
      --L 4000 --B 3000 --H 1200

  # Mat bang
  python draw_pile_cap.py --out plan.png --plan \\
      --L 4000 --B 3000 --n_piles_x 3 --n_piles_y 2
        """
    )

    parser.add_argument("--out", required=True, help="Duong dan xuat file")
    parser.add_argument("--view", choices=["A-A", "B-B", "plan"], default="A-A",
                       help="Loai hinh chieu: A-A, B-B, hoac plan (mat bang)")
    parser.add_argument("--L", type=float, default=4000, help="Chieu dai dai (mm)")
    parser.add_argument("--B", type=float, default=3000, help="Chieu rong dai (mm)")
    parser.add_argument("--H", type=float, default=1200, help="Chieu cao dai (mm)")
    parser.add_argument("--pile_diameter", type=float, default=600, help="Duong kinh coc (mm)")
    parser.add_argument("--n_piles_x", type=int, default=3, help="So coc theo x")
    parser.add_argument("--n_piles_y", type=int, default=2, help="So coc theo y")
    parser.add_argument("--pile_spacing_x", type=float, default=1500, help="Khoang cach coc x (mm)")
    parser.add_argument("--pile_spacing_y", type=float, default=1500, help="Khoang cach coc y (mm)")
    parser.add_argument("--pile_cover", type=float, default=75, help="Khoang cach mat coc den canh dai (mm)")
    parser.add_argument("--main_rebar_dia", type=float, default=25, help="Duong kinh cot thep coc (mm)")
    parser.add_argument("--cover", type=float, default=50, help="Lop bao ve (mm)")
    parser.add_argument("--col_width", type=float, default=600, help="Chieu rong cot (mm)")
    parser.add_argument("--col_depth", type=float, default=600, help="Chieu sau cot (mm)")
    parser.add_argument("--concrete", type=str, default="B25", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB400-V", help="Loai thep")

    args = parser.parse_args()

    if args.view == "plan":
        draw_pile_cap_plan(
            args.out,
            L=args.L, B=args.B,
            pile_diameter=args.pile_diameter,
            n_piles_x=args.n_piles_x, n_piles_y=args.n_piles_y,
            pile_spacing_x=args.pile_spacing_x, pile_spacing_y=args.pile_spacing_y,
            col_width=args.col_width, col_depth=args.col_depth,
            pile_cover=args.pile_cover,
            main_rebar_dia=args.main_rebar_dia,
            cover=args.cover,
            concrete_grade=args.concrete,
            steel_grade=args.steel
        )
    else:
        draw_pile_cap_section(
            args.out,
            L=args.L, B=args.B, H=args.H,
            pile_diameter=args.pile_diameter,
            n_piles_x=args.n_piles_x, n_piles_y=args.n_piles_y,
            pile_spacing_x=args.pile_spacing_x, pile_spacing_y=args.pile_spacing_y,
            pile_cover=args.pile_cover,
            main_rebar_dia=args.main_rebar_dia,
            cover=args.cover,
            col_width=args.col_width, col_depth=args.col_depth,
            concrete_grade=args.concrete,
            steel_grade=args.steel,
            view=args.view
        )

    print(f"[OK] Da xuat dai coc ({args.view}): {args.out}")
