
# Auto-injected Error Handler
import sys
import os
agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)
try:
    from modules.error_handler import with_error_handling
except ImportError:
    # Dummy decorator if module not found
    def with_error_handling(func):
        return func

"""
draw_rc_column.py — Ve mat cat cot BTCT (chu nhat + tron)

Su dung:
  # Cot chu nhat
  python draw_rc_column.py --out cot_rect.png --type rect --width 400 --depth 600 --main_dia 22 --n_bars_w 4 --n_bars_d 6 --stirrup_dia 10 --cover 30

  # Cot tron
  python draw_rc_column.py --out cot_tron.png --type circular --diameter 500 --main_dia 22 --n_bars 10 --stirrup_dia 10 --cover 30

Tinh nang:
  - Ve mat cat cot BTCT chi tiet: tiet dien be tong, thep doc, cot dai
  - Ho tro 2 loai: cot chu nhat (rect) va cot tron (circular)
  - Tu dong tinh khoang cach thep, lop bao ve
  - Danh kich thuoc day du, ghi chu ky thuat theo TCVN 5574:2018
  - Xuat file .png chat luong cao (300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import argparse
import math
import sys

# Fix Unicode issue on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


@with_error_handling
def draw_rect_column(ax, width, depth, main_dia, n_bars_w, n_bars_d,
                     stirrup_dia, cover, concrete_grade="B25", steel_grade="CB400-V"):
    """Ve mat cat cot chu nhat."""
    ax.set_aspect('equal')

    # --- Ve tiet dien be tong ---
    concrete = patches.Rectangle((-width/2, -depth/2), width, depth,
                                  linewidth=2.5, edgecolor='#2C3E50',
                                  facecolor='#D5DBDB', hatch='...', zorder=1)
    ax.add_patch(concrete)

    # --- Ve cot dai (stirrup) ---
    stirrup_offset = cover + stirrup_dia / 2
    stirrup_w = width - 2 * stirrup_offset
    stirrup_d = depth - 2 * stirrup_offset
    stirrup = patches.Rectangle((-stirrup_w/2, -stirrup_d/2), stirrup_w, stirrup_d,
                                 linewidth=1.8, edgecolor='#E74C3C',
                                 facecolor='none', linestyle='--', zorder=2)
    ax.add_patch(stirrup)

    # Hook goc dai (135 do)
    hook_len = stirrup_dia * 6  # 6d theo TCVN
    corners = [(-stirrup_w/2, -stirrup_d/2), (stirrup_w/2, -stirrup_d/2),
               (stirrup_w/2, stirrup_d/2), (-stirrup_w/2, stirrup_d/2)]
    hook_dirs = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for (cx, cy), (dx, dy) in zip(corners, hook_dirs):
        ax.plot([cx, cx + dx * hook_len * 0.3], [cy, cy + dy * hook_len * 0.3],
                color='#E74C3C', linewidth=1.5, zorder=3)

    # --- Bo tri thep doc ---
    bar_center_offset = cover + stirrup_dia + main_dia / 2
    bar_positions = []

    # Thep canh tren va duoi (theo width)
    for i in range(n_bars_w):
        if n_bars_w > 1:
            x = -width/2 + bar_center_offset + i * (width - 2 * bar_center_offset) / (n_bars_w - 1)
        else:
            x = 0
        bar_positions.append((x, depth/2 - bar_center_offset))   # Top row
        bar_positions.append((x, -depth/2 + bar_center_offset))  # Bottom row

    # Thep canh trai va phai (theo depth, khong tinh goc)
    if n_bars_d > 2:
        for i in range(1, n_bars_d - 1):
            y = -depth/2 + bar_center_offset + i * (depth - 2 * bar_center_offset) / (n_bars_d - 1)
            bar_positions.append((-width/2 + bar_center_offset, y))  # Left
            bar_positions.append((width/2 - bar_center_offset, y))   # Right

    # Ve cac thanh thep
    for (bx, by) in bar_positions:
        bar = plt.Circle((bx, by), main_dia/2, fill=True,
                         facecolor='#2C3E50', edgecolor='black',
                         linewidth=0.8, zorder=4)
        ax.add_patch(bar)

    total_bars = len(bar_positions)

    # --- Danh kich thuoc ---
    pad = max(width, depth) * 0.12

    # Chieu rong (width)
    ax.annotate('', xy=(-width/2, -depth/2 - pad), xytext=(width/2, -depth/2 - pad),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(0, -depth/2 - pad - 8, f"b = {width:.0f}",
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Chieu sau (depth)
    ax.annotate('', xy=(width/2 + pad, -depth/2), xytext=(width/2 + pad, depth/2),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(width/2 + pad + 8, 0, f"h = {depth:.0f}",
            ha='left', va='center', fontsize=10, color='#2980B9', fontweight='bold', rotation=90)

    # Lop bao ve (cover)
    cv_x = -width/2
    cv_y = depth/2 - bar_center_offset
    ax.annotate(f"a = {cover}", xy=(cv_x, cv_y),
                xytext=(cv_x - pad * 1.5, cv_y),
                arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=1),
                fontsize=8, color='#8E44AD', ha='right', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#F5EEF8', edgecolor='#8E44AD'))

    # Ghi chu thep doc
    if len(bar_positions) > 0:
        bx0, by0 = bar_positions[0]
        ax.annotate(f"{total_bars}\u03d5{main_dia:.0f}\n({steel_grade})",
                    xy=(bx0, by0), xytext=(width/2 + pad * 2, depth/2 - pad),
                    arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.2),
                    fontsize=9, fontweight='bold', color='#C0392B',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'))

    # Ghi chu cot dai
    ax.annotate(f"\u03d5{stirrup_dia:.0f}@{150}\n(dai kin)",
                xy=(-stirrup_w/2, 0), xytext=(-width/2 - pad * 2.5, -depth/4),
                arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2),
                fontsize=9, fontweight='bold', color='#E67E22',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E67E22'))

    # Tieu de
    ax.set_title(f"MAT CAT COT {width:.0f}x{depth:.0f} (BTCT)",
                 fontsize=13, fontweight='bold', pad=15)

    # Gioi han
    total_pad = max(width, depth) * 0.5
    ax.set_xlim(-width/2 - total_pad, width/2 + total_pad)
    ax.set_ylim(-depth/2 - total_pad, depth/2 + total_pad)
    ax.axis('off')

    return total_bars, concrete_grade, steel_grade


@with_error_handling
def draw_circular_column(ax, diameter, main_dia, n_bars,
                         stirrup_dia, cover, concrete_grade="B25", steel_grade="CB400-V"):
    """Ve mat cat cot tron."""
    ax.set_aspect('equal')
    R = diameter / 2

    # --- Ve tiet dien be tong (tron) ---
    concrete = plt.Circle((0, 0), R, linewidth=2.5, edgecolor='#2C3E50',
                           facecolor='#D5DBDB', hatch='...', zorder=1)
    ax.add_patch(concrete)

    # --- Ve cot dai (vong tron) ---
    stirrup_R = R - cover - stirrup_dia / 2
    stirrup = plt.Circle((0, 0), stirrup_R, linewidth=1.8, edgecolor='#E74C3C',
                          facecolor='none', linestyle='--', zorder=2)
    ax.add_patch(stirrup)

    # --- Bo tri thep doc (deu tren vong tron) ---
    bar_R = R - cover - stirrup_dia - main_dia / 2
    bar_positions = []
    for i in range(n_bars):
        angle = 2 * math.pi * i / n_bars
        bx = bar_R * math.cos(angle)
        by = bar_R * math.sin(angle)
        bar_positions.append((bx, by))
        bar = plt.Circle((bx, by), main_dia/2, fill=True,
                         facecolor='#2C3E50', edgecolor='black',
                         linewidth=0.8, zorder=4)
        ax.add_patch(bar)

    # --- Danh kich thuoc ---
    pad = diameter * 0.12

    # Duong kinh
    ax.annotate('', xy=(-R, -R - pad), xytext=(R, -R - pad),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(0, -R - pad - 8, f"D = {diameter:.0f}",
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Lop bao ve
    ax.annotate(f"a = {cover}", xy=(0, R),
                xytext=(0, R + pad * 2),
                arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=1),
                fontsize=8, color='#8E44AD', ha='center', va='bottom',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#F5EEF8', edgecolor='#8E44AD'))

    # Ghi chu thep doc
    if len(bar_positions) > 0:
        bx0, by0 = bar_positions[0]
        ax.annotate(f"{n_bars}\u03d5{main_dia:.0f}\n({steel_grade})",
                    xy=(bx0, by0), xytext=(R + pad * 2.5, R - pad),
                    arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.2),
                    fontsize=9, fontweight='bold', color='#C0392B',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'))

    # Ghi chu cot dai
    ax.annotate(f"\u03d5{stirrup_dia:.0f}@{150}\n(dai xoan)",
                xy=(-stirrup_R * 0.7, -stirrup_R * 0.7),
                xytext=(-R - pad * 2.5, -R + pad),
                arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2),
                fontsize=9, fontweight='bold', color='#E67E22',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E67E22'))

    # Tieu de
    ax.set_title(f"MAT CAT COT TRON D{diameter:.0f} (BTCT)",
                 fontsize=13, fontweight='bold', pad=15)

    # Gioi han
    total_pad = diameter * 0.55
    ax.set_xlim(-total_pad, total_pad)
    ax.set_ylim(-total_pad, total_pad)
    ax.axis('off')

    return n_bars, concrete_grade, steel_grade


def main():
    parser = argparse.ArgumentParser(
        description="Ve mat cat cot BTCT (chu nhat hoac tron)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  # Cot chu nhat 400x600
  python draw_rc_column.py --out cot.png --type rect --width 400 --depth 600 --main_dia 22 --n_bars_w 4 --n_bars_d 6

  # Cot tron D500
  python draw_rc_column.py --out cot.png --type circular --diameter 500 --main_dia 22 --n_bars 10
        """
    )
    parser.add_argument("--out", required=True, help="Duong dan xuat file anh (.png)")
    parser.add_argument("--type", choices=["rect", "circular"], default="rect", help="Loai cot")

    # Cot chu nhat
    parser.add_argument("--width", type=float, default=400, help="Chieu rong cot (mm) - rect only")
    parser.add_argument("--depth", type=float, default=600, help="Chieu sau cot (mm) - rect only")
    parser.add_argument("--n_bars_w", type=int, default=4, help="So thanh thep canh rong - rect only")
    parser.add_argument("--n_bars_d", type=int, default=6, help="So thanh thep canh sau - rect only")

    # Cot tron
    parser.add_argument("--diameter", type=float, default=500, help="Duong kinh cot (mm) - circular only")
    parser.add_argument("--n_bars", type=int, default=10, help="So thanh thep doc - circular only")

    # Chung
    parser.add_argument("--main_dia", type=float, default=22, help="Duong kinh thep doc (mm)")
    parser.add_argument("--stirrup_dia", type=float, default=10, help="Duong kinh cot dai (mm)")
    parser.add_argument("--cover", type=float, default=30, help="Lop bao ve be tong (mm)")
    parser.add_argument("--concrete", type=str, default="B25", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB400-V", help="Loai thep")

    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=(10, 10))

    if args.type == "rect":
        total_bars, conc, steel = draw_rect_column(
            ax, args.width, args.depth, args.main_dia,
            args.n_bars_w, args.n_bars_d, args.stirrup_dia, args.cover,
            args.concrete, args.steel
        )
        col_desc = f"{args.width:.0f}x{args.depth:.0f}"
    else:
        total_bars, conc, steel = draw_circular_column(
            ax, args.diameter, args.main_dia, args.n_bars,
            args.stirrup_dia, args.cover, args.concrete, args.steel
        )
        col_desc = f"D{args.diameter:.0f}"

    # Bang ghi chu ky thuat
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"  1. Cot {col_desc}, be tong {conc} (Rb theo TCVN 5574:2018).\n"
        f"  2. Thep doc: {total_bars} thanh \u03d5{args.main_dia:.0f}, loai {steel} (Rs=350-400MPa).\n"
        f"  3. Cot dai: \u03d5{args.stirrup_dia:.0f}@150, loai CB240-T. Gia day tai vung noi thep.\n"
        f"  4. Lop bao ve: a = {args.cover:.0f}mm (theo TCVN 5574:2018, Dieu 10.3.1).\n"
        f"  5. Noi thep doc: noi buoc hoac han, chieu dai noi >= 30d = {30*args.main_dia:.0f}mm.\n"
        f"  6. Tieu chuan ap dung: TCVN 5574:2018, TCVN 2737:2023."
    )
    fig.text(0.05, 0.02, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.14, 1, 0.95])
    plt.savefig(args.out, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\u2705 Da xuat mat cat cot BTCT: {args.out}")


if __name__ == "__main__":
    main()
