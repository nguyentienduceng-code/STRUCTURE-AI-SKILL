# -*- coding: utf-8 -*-
"""
draw_rc_beam_full.py — Ve mat cat dam BTCT day du voi cot thep

Tinh nang:
- Ve mat cat ngang dam BTCT chi tiet
- Hien thi: tiet dien be tong, cot thep doc, cot dai
- Bo tri thep: thanh ke, thanh am, cot dai
- Danh kich thuoc day du
- Xuat PNG chat luong cao (300 DPI)

Su dung:
    python draw_rc_beam_full.py --out dam_btct.png \
        --b 300 --h 700 --h0 650 \
        --top_bars "2D22+1D20" --bot_bars "3D22" \
        --stirrup_dia 10 --stirrup_spacing 150 \
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

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import argparse
import re


def parse_bar_string(bar_str: str) -> list:
    """
    Parse bar string like "2D22+1D20" or "3D22" into list of diameters.

    Returns:
        List of (count, diameter) tuples
    """
    results = []
    # Split by +
    parts = bar_str.replace(' ', '').split('+')
    for part in parts:
        # Match pattern like "2D22" or "D22"
        match = re.match(r'(\d*)D(\d+)', part, re.IGNORECASE)
        if match:
            count = int(match.group(1)) if match.group(1) else 1
            dia = int(match.group(2))
            results.append((count, dia))
    return results


def draw_rc_beam_section(
    output_path: str,
    b: float = 300,
    h: float = 700,
    h0: float = 650,
    top_bars: str = "2D22+1D20",
    bot_bars: str = "3D22",
    mid_bars: str = "",
    stirrup_dia: float = 10,
    stirrup_spacing: float = 150,
    cover: float = 25,
    concrete_grade: str = "B25",
    steel_grade: str = "CB400-V",
    show_half: bool = False
):
    """
    Ve mat cat dam BTCT day du.

    Args:
        output_path: Duong dan xuat file
        b: Chieu rong dam (mm)
        h: Chieu cao dam (mm)
        h0: Chieu cao lam viec (mm)
        top_bars: Thanh ke (VD: "2D22+1D20")
        bot_bars: Thanh am (VD: "3D22")
        mid_bars: Thanh giua (neu co)
        stirrup_dia: Duong kinh cot dai (mm)
        stirrup_spacing: Khoang cach cot dai (mm)
        cover: Lop bao ve (mm)
        concrete_grade: Cap be tong
        steel_grade: Loai thep
        show_half: Ve nua mat cat (symmetric)
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Parse bar strings
    top_bars_list = parse_bar_string(top_bars)
    bot_bars_list = parse_bar_string(bot_bars)
    mid_bars_list = parse_bar_string(mid_bars) if mid_bars else []

    # Calculate effective dimensions
    a = h - h0  # Distance from bottom to centroid of tension steel
    beam_half = b / 2 if show_half else b

    # === DRAW CONCRETE SECTION ===
    concrete = patches.Rectangle(
        (-beam_half, 0), b if not show_half else beam_half * 2, h,
        linewidth=2.5,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(concrete)

    # === DRAW STIRRUPS ===
    n_stirrups = int(h / stirrup_spacing) + 1
    for i in range(n_stirrups):
        y = i * stirrup_spacing
        if y <= h:
            # Stirrup line (full width or half)
            x_end = beam_half - cover if show_half else b - cover
            ax.plot([-x_end + cover, x_end - cover], [y, y],
                   color='#E74C3C', linewidth=1.5, linestyle='--', zorder=2)

    # Hook marks at ends
    hook_len = stirrup_dia * 6
    for x_pos in [-x_end + cover, x_end - cover]:
        ax.plot([x_pos, x_pos + (5 if x_pos < 0 else -5)],
               [y - hook_len/3, y],
               color='#E74C3C', linewidth=1.5, zorder=2)

    # === DRAW TOP BARS (tension in negative moment) ===
    # Calculate total diameter and spacing
    top_total = sum(c * d for c, d in top_bars_list)
    top_dias = []
    for count, dia in top_bars_list:
        top_dias.extend([dia] * count)

    # Calculate y position for top bars (from top)
    top_y = h - cover - stirrup_dia - top_total/len(top_dias) if top_dias else h - cover - 30

    # Position bars along width
    bar_spacing = (b - 2 * cover) / (len(top_dias) + 1) if len(top_dias) > 1 else 0
    for i, dia in enumerate(top_dias):
        x = -b/2 + cover + bar_spacing * (i + 1)
        if not show_half or x >= 0:
            bar = patches.Rectangle(
                (x - dia * 1.5, top_y - dia * 1.5),
                dia * 3, dia * 3,
                linewidth=0.5,
                edgecolor='#922B21',
                facecolor='#C0392B',
                zorder=4
            )
            ax.add_patch(bar)

    # === DRAW BOTTOM BARS (tension in positive moment) ===
    bot_total = sum(c * d for c, d in bot_bars_list)
    bot_dias = []
    for count, dia in bot_bars_list:
        bot_dias.extend([dia] * count)

    # Position for bottom bars
    bot_y = cover + stirrup_dia + bot_total/len(bot_dias) if bot_dias else cover + 30

    for i, dia in enumerate(bot_dias):
        x = -b/2 + cover + bar_spacing * (i + 1) if len(bot_dias) > 1 else 0
        bar = patches.Rectangle(
            (x - dia * 1.5, bot_y - dia * 1.5),
            dia * 3, dia * 3,
            linewidth=0.5,
            edgecolor='#922B21',
            facecolor='#C0392B',
            zorder=4
        )
        ax.add_patch(bar)

    # === DIMENSIONING ===
    dim_pad = 50

    # Beam width
    ax.annotate('',
        xy=(-b/2 if not show_half else 0, -dim_pad),
        xytext=(b/2, -dim_pad),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(0 if show_half else 0, -dim_pad - 15,
            f'b = {b}mm',
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Beam height
    ax.annotate('',
        xy=(-b/2 - dim_pad, 0),
        xytext=(-b/2 - dim_pad, h),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(-b/2 - dim_pad - 20, h/2,
            f'h = {h}mm',
            ha='center', va='center', fontsize=10, color='#27AE60', fontweight='bold',
            rotation=90)

    # Cover
    ax.annotate('',
        xy=(-b/2 + cover, 0),
        xytext=(-b/2 + cover, cover + 20),
        arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1))
    ax.text(-b/2 + cover, cover + 40,
            f'a = {cover}',
            ha='center', va='bottom', fontsize=8, color='#E67E22')

    # Working height
    ax.annotate('',
        xy=(-b/2 - dim_pad, h0),
        xytext=(-b/2 - dim_pad, 0),
        arrowprops=dict(arrowstyle='<->', color='#8E44AD', lw=1))
    ax.text(-b/2 - dim_pad - 20, h0/2,
            f'h0 = {h0}mm',
            ha='center', va='center', fontsize=9, color='#8E44AD', fontweight='bold',
            rotation=90)

    # === ANNOTATIONS ===
    # Top bars
    if top_bars_list:
        ax.annotate(f'Top: {top_bars} ({steel_grade})',
            xy=(0 if show_half else b/4, top_y),
            xytext=(b/2 + dim_pad * 2, top_y + 50),
            arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.5),
            fontsize=9, color='#C0392B', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'),
            zorder=10)

    # Bottom bars
    if bot_bars_list:
        ax.annotate(f'Bot: {bot_bars} ({steel_grade})',
            xy=(0 if show_half else b/4, bot_y),
            xytext=(b/2 + dim_pad * 2, bot_y - 50),
            arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.5),
            fontsize=9, color='#C0392B', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'),
            zorder=10)

    # Stirrups
    ax.annotate(f'stirrup d{stirrup_dia}@{stirrup_spacing}',
        xy=(0, h * 0.6),
        xytext=(b/2 + dim_pad * 2, h * 0.6),
        arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=1.5),
        fontsize=9, color='#E74C3C', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E74C3C'),
        zorder=10)

    # Symmetry line
    if show_half:
        ax.plot([0, 0], [0, h], color='#7F8C8D', linewidth=1, linestyle=':', zorder=1)
        ax.text(10, h - 20, 'CL', fontsize=8, color='#7F8C8D')

    # === SETUP AXES ===
    padding = 150
    x_lim = -b/2 - padding if not show_half else 0 - padding
    ax.set_xlim(x_lim, b/2 + padding * 2)
    ax.set_ylim(-padding, h + padding * 0.5)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    title_text = f'MAT CAT DAM BTCT\n{b}x{h}mm' + (' (Nua mat cat - doi xung)' if show_half else '')
    ax.set_title(title_text, fontsize=14, fontweight='bold', pad=20)

    # === TECHNICAL NOTES ===
    top_total_count = sum(c for c, d in top_bars_list)
    bot_total_count = sum(c for c, d in bot_bars_list)

    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"1. Dam BTCT {b}x{h}mm, h0={h0}mm, be tong {concrete_grade}.\n"
        f"2. Thep gian ke (top): {top_bars} ({steel_grade}) - {top_total_count} thanh.\n"
        f"3. Thep am (bot): {bot_bars} ({steel_grade}) - {bot_total_count} thanh.\n"
        f"4. Cot dai: d{stirrup_dia}@{stirrup_spacing}mm, loai CB240-T.\n"
        f"5. Lop bao ve: a = {cover}mm (TCVN 5574:2018, Dieu 10.3.1).\n"
        f"6. Tieu chuan: TCVN 5574:2018.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    # Export
    plt.tight_layout(rect=[0, 0.14, 1, 0.95])
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
        description="Ve mat cat dam BTCT day du",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_rc_beam_full.py --out dam.png --b 300 --h 700 --h0 650 \\
      --top_bars "2D22+1D20" --bot_bars "3D22" \\
      --stirrup_dia 10 --stirrup_spacing 150

  # Ve nua mat cat (doi xung)
  python draw_rc_beam_full.py --out dam_half.png --b 300 --h 700 \\
      --top_bars "2D22" --bot_bars "3D22" --show_half
        """
    )

    parser.add_argument("--out", required=True, help="Duong dan xuat file")
    parser.add_argument("--b", type=float, default=300, help="Chieu rong dam (mm)")
    parser.add_argument("--h", type=float, default=700, help="Chieu cao dam (mm)")
    parser.add_argument("--h0", type=float, default=650, help="Chieu cao lam viec (mm)")
    parser.add_argument("--top_bars", type=str, default="2D22", help="Thanh ke (VD: 2D22+1D20)")
    parser.add_argument("--bot_bars", type=str, default="3D22", help="Thanh am (VD: 3D22)")
    parser.add_argument("--mid_bars", type=str, default="", help="Thanh giua (neu co)")
    parser.add_argument("--stirrup_dia", type=float, default=10, help="Duong kinh cot dai (mm)")
    parser.add_argument("--stirrup_spacing", type=float, default=150, help="Khoang cach cot dai (mm)")
    parser.add_argument("--cover", type=float, default=25, help="Lop bao ve (mm)")
    parser.add_argument("--concrete", type=str, default="B25", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB400-V", help="Loai thep")
    parser.add_argument("--show_half", action="store_true", help="Ve nua mat cat (doi xung)")

    args = parser.parse_args()

    draw_rc_beam_section(
        args.out,
        b=args.b,
        h=args.h,
        h0=args.h0,
        top_bars=args.top_bars,
        bot_bars=args.bot_bars,
        mid_bars=args.mid_bars,
        stirrup_dia=args.stirrup_dia,
        stirrup_spacing=args.stirrup_spacing,
        cover=args.cover,
        concrete_grade=args.concrete,
        steel_grade=args.steel,
        show_half=args.show_half
    )

    print(f"[OK] Da xuat mat cat dam BTCT: {args.out}")
