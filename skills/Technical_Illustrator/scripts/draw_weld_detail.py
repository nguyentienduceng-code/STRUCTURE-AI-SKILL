# -*- coding: utf-8 -*-
"""
draw_weld_detail.py — Ve chi tiet lien ket han (weld connections)

Tinh nang:
- Ve cac loai moi han: fillet weld, butt weld, plug weld
- Ve mat cat va mat bang lien ket
- Danh kich thuoc day du
- Xuat PNG chat luong cao (300 DPI)

Su dung:
    python draw_weld_detail.py --out weld_detail.png \
        --type fillet --a 6 --L 200 \
        --t1 10 --t2 10

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


def draw_fillet_weld(
    output_path: str,
    a: float = 6,
    L: float = 200,
    t1: float = 10,
    t2: float = 10,
    weld_type: str = "fillet",
    position: str = "T-joint"
) -> None:
    """
    Ve chi tiet moi han goc (fillet weld).

    Args:
        output_path: Duong dan xuat file
        a: Kich thuoc han (leg size) (mm)
        L: Chieu dai han (mm)
        t1, t2: Day cac thanh thanh phan (mm)
        weld_type: "fillet" | "butt" | "plug"
        position: "T-joint" | "lap-joint" | "corner"
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # Scale for visibility
    scale = 5
    a_s = a * scale
    L_s = L * scale
    t1_s = t1 * scale
    t2_s = t2 * scale

    # === DRAW BASE METALS ===
    # Horizontal plate (bottom)
    plate1 = patches.Rectangle(
        (-50, -t2_s), 50 + L_s + 50, t2_s,
        linewidth=1.5,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(plate1)

    # Vertical plate (top/side)
    if position == "T-joint":
        plate2 = patches.Rectangle(
            (L_s/2 - t1_s/2, 0), t1_s, 50 + a_s + 50,
            linewidth=1.5,
            edgecolor='#2C3E50',
            facecolor='#D5DBDB',
            hatch='///',
            zorder=1
        )
        ax.add_patch(plate2)
    elif position == "lap-joint":
        plate2 = patches.Rectangle(
            (0, 0), 50 + L_s + 50, t1_s,
            linewidth=1.5,
            edgecolor='#2C3E50',
            facecolor='#D5DBDB',
            hatch='///',
            zorder=1
        )
        ax.add_patch(plate2)
    else:  # corner
        plate2 = patches.Rectangle(
            (0, -t2_s), 50 + L_s + 50, t1_s,
            linewidth=1.5,
            edgecolor='#2C3E50',
            facecolor='#D5DBDB',
            hatch='///',
            zorder=1
        )
        ax.add_patch(plate2)

    # === DRAW WELD SYMBOL ===
    if position == "T-joint":
        # Fillet weld triangle
        weld_x = L_s / 2 - t1_s / 2
        weld = patches.Polygon(
            [(weld_x, 0),
             (weld_x + t1_s, 0),
             (weld_x + t1_s, a_s)],
            closed=True,
            linewidth=2,
            edgecolor='#F39C12',
            facecolor='#F39C12',
            alpha=0.7,
            zorder=3
        )
        ax.add_patch(weld)

        # Second weld (mirror)
        weld2 = patches.Polygon(
            [(weld_x + t1_s, 0),
             (weld_x + t1_s, a_s),
             (weld_x, 0)],
            closed=True,
            linewidth=2,
            edgecolor='#F39C12',
            facecolor='#F39C12',
            alpha=0.7,
            zorder=3
        )
        ax.add_patch(weld2)

    # === WELD HATCH PATTERN ===
    # Draw weld lines
    n_lines = int(a_s / 4)
    for i in range(n_lines):
        y = i * 4
        ax.plot([0, a_s - y], [y, y + a_s],
               color='#F39C12', linewidth=0.5, alpha=0.5, zorder=2)

    # === DIMENSIONS ===
    dim_pad = 60

    # Weld size (leg)
    ax.annotate('',
        xy=(L_s/2 + t1_s/2, 0),
        xytext=(L_s/2 + t1_s/2 + a_s, 0),
        arrowprops=dict(arrowstyle='<->', color='#F39C12', lw=1.5))
    ax.text(L_s/2 + t1_s/2 + a_s/2, -20,
            f'a = {a}mm\n(leg size)',
            ha='center', va='top', fontsize=9, color='#F39C12', fontweight='bold')

    # Weld length
    ax.annotate('',
        xy=(0, -t2_s - dim_pad),
        xytext=(L_s, -t2_s - dim_pad),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(L_s/2, -t2_s - dim_pad - 15,
            f'L = {L}mm (weld length)',
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Plate thickness
    ax.annotate('',
        xy=(-dim_pad, -t2_s),
        xytext=(-dim_pad, 0),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(-dim_pad - 20, -t2_s/2,
            f't1 = {t1}mm',
            ha='center', va='center', fontsize=9, color='#27AE60', fontweight='bold',
            rotation=90)

    ax.annotate('',
        xy=(L_s + dim_pad, -t2_s),
        xytext=(L_s + dim_pad, 0),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(L_s + dim_pad + 20, -t2_s/2,
            f't2 = {t2}mm',
            ha='center', va='center', fontsize=9, color='#27AE60', fontweight='bold',
            rotation=90)

    # === SETUP ===
    padding = 100
    ax.set_xlim(-100, L_s + 200)
    ax.set_ylim(-t2_s - 150, max(t1_s, a_s) + 150)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'FILLET WELD DETAIL\n{position} - a={a}mm, L={L}mm',
                 fontsize=14, fontweight='bold', pad=20)

    # === ANNOTATION ===
    ax.annotate(f'Fillet weld\n'
               f'a = {a}mm\n'
               f'L = {L}mm',
               xy=(L_s, -t2_s - 50),
               xytext=(L_s + 100, -t2_s - 50),
               arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.5),
               fontsize=10, color='#E67E22', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E67E22'),
               zorder=10)

    # === TECHNICAL NOTES ===
    weld_area = a * L * 2  # Both sides for T-joint
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"1. Lien ket han goc (fillet weld), vi tri: {position}.\n"
        f"2. Kich thuoc han: a = {a}mm (leg size theo TCVN/EN).\n"
        f"3. Chieu dai han: L = {L}mm.\n"
        f"4. Dien tich han: A_w = {weld_area:.0f}mm2 (ca 2 mat).\n"
        f"5. Day day: t1 = {t1}mm, t2 = {t2}mm.\n"
        f"6. Vat lieu han: que han tuong thich voi vat lieu nen.\n"
        f"7. Tieu chuan: TCVN 5575:2012, EN 1993-1-8.\n"
        f"8. Kiem tra chat luong: UT/RT theo TCVN.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.14, 1, 0.95])
    export_figure(fig, output_path, dpi=300)


def draw_butt_weld(
    output_path: str,
    t: float = 20,
    L: float = 300,
    weld_type: str = "complete_penetration"
) -> None:
    """
    Ve chi tiet han but (butt weld).

    Args:
        output_path: Duong dan xuat file
        t: Day cac thanh (mm)
        L: Chieu dai han (mm)
        weld_type: "complete_penetration" | "partial_penetration"
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    scale = 5
    t_s = t * scale
    L_s = L * scale

    # === DRAW PLATES ===
    # Left plate
    plate1 = patches.Rectangle(
        (-100, 0), 100 + L_s/2, t_s,
        linewidth=2,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(plate1)

    # Right plate
    plate2 = patches.Rectangle(
        (L_s/2, 0), 100 + L_s/2, t_s,
        linewidth=2,
        edgecolor='#2C3E50',
        facecolor='#D5DBDB',
        hatch='///',
        zorder=1
    )
    ax.add_patch(plate2)

    # === DRAW WELD ===
    if weld_type == "complete_penetration":
        # Full penetration - weld fills the gap
        weld = patches.Rectangle(
            (L_s/2 - 5, -5), 10, t_s + 10,
            linewidth=2,
            edgecolor='#F39C12',
            facecolor='#F39C12',
            alpha=0.8,
            zorder=2
        )
        ax.add_patch(weld)

        # Weld hatching
        for i in range(int(t_s / 6)):
            y = i * 6
            ax.plot([L_s/2 - 15, L_s/2 + 15], [y, y],
                   color='#F39C12', linewidth=1, alpha=0.6, zorder=3)
    else:
        # Partial penetration
        weld = patches.Rectangle(
            (L_s/2 - 3, t_s * 0.2), 6, t_s * 0.6,
            linewidth=1.5,
            edgecolor='#F39C12',
            facecolor='#F39C12',
            alpha=0.8,
            zorder=2
        )
        ax.add_patch(weld)

    # === DIMENSIONS ===
    dim_pad = 40

    # Plate thickness
    ax.annotate('',
        xy=(-100 - dim_pad, 0),
        xytext=(-100 - dim_pad, t_s),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(-100 - dim_pad - 25, t_s/2,
            f't = {t}mm',
            ha='center', va='center', fontsize=10, color='#2980B9', fontweight='bold',
            rotation=90)

    # Weld length
    ax.annotate('',
        xy=(0, -dim_pad),
        xytext=(L_s, -dim_pad),
        arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(L_s/2, -dim_pad - 15,
            f'L = {L}mm',
            ha='center', va='top', fontsize=10, color='#27AE60', fontweight='bold')

    # === SETUP ===
    ax.set_xlim(-200, L_s + 200)
    ax.set_ylim(-80, t_s + 80)
    ax.set_aspect('equal')
    ax.axis('off')

    weld_desc = "Complete Pen. Weld" if weld_type == "complete_penetration" else "Partial Pen. Weld"
    ax.set_title(f'BUTT WELD DETAIL\n{weld_desc} - t={t}mm, L={L}mm',
                 fontsize=14, fontweight='bold', pad=20)

    # === NOTES ===
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"1. Han but (butt weld), loai: {weld_type}.\n"
        f"2. Day cac: t = {t}mm.\n"
        f"3. Chieu dai han: L = {L}mm.\n"
        f"4. Tieu chuan: TCVN 5575:2012, EN 1993-1-8.\n"
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.1, 1, 0.95])
    export_figure(fig, output_path, dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve chi tiet lien ket han",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  # Han goc T-joint
  python draw_weld_detail.py --out fillet.png --type fillet \\
      --a 6 --L 200 --t1 10 --t2 10 --position T-joint

  # Han but complete penetration
  python draw_weld_detail.py --out butt.png --type butt \\
      --t 20 --L 300
        """
    )

    parser.add_argument("--out", required=True, help="Duong dan xuat file")
    parser.add_argument("--type", choices=["fillet", "butt"], default="fillet",
                       help="Loai han")
    parser.add_argument("--a", type=float, default=6, help="Kich thuoc han (mm)")
    parser.add_argument("--L", type=float, default=200, help="Chieu dai han (mm)")
    parser.add_argument("--t1", type=float, default=10, help="Day day 1 (mm)")
    parser.add_argument("--t2", type=float, default=10, help="Day day 2 (mm)")
    parser.add_argument("--position", choices=["T-joint", "lap-joint", "corner"],
                       default="T-joint", help="Vi tri lien ket")
    parser.add_argument("--weld_type", choices=["complete_penetration", "partial_penetration"],
                       default="complete_penetration", help="Loai han but")

    args = parser.parse_args()

    if args.type == "fillet":
        draw_fillet_weld(
            args.out,
            a=args.a,
            L=args.L,
            t1=args.t1,
            t2=args.t2,
            position=args.position
        )
    else:
        draw_butt_weld(
            args.out,
            t=args.t1,  # t1 as main thickness
            L=args.L,
            weld_type=args.weld_type
        )

    print(f"[OK] Da xuat chi tiet han: {args.out}")
