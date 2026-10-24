
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
draw_foundation.py — Ve mat cat mong don / mong bang BTCT

Su dung:
  # Mong don
  python draw_foundation.py --out mong_don.png --type single --L 2000 --B 2000 --H 600 --h_lot 100 --col_w 400 --col_d 400 --bot_dia 16 --bot_spacing 150 --cover 50

  # Mong bang
  python draw_foundation.py --out mong_bang.png --type strip --L 6000 --B 1200 --H 500 --h_lot 100 --col_w 300 --col_d 300 --bot_dia 14 --bot_spacing 200 --cover 50

Tinh nang:
  - Ve mat cat dung mong BTCT chi tiet
  - Hien thi: dat nen, lop lot be tong, dai mong, cot thep day, thep cho cot
  - Danh kich thuoc day du, ghi chu ky thuat theo TCVN 5574:2018
  - Xuat file .png chat luong cao (300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import argparse
import sys

# Fix Unicode issue on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


@with_error_handling
def draw_foundation(output_path, ftype="single",
                    L=2000, B=2000, H=600, h_lot=100,
                    col_w=400, col_d=400,
                    bot_dia=16, bot_spacing=150, cover=50,
                    depth_embed=1200, concrete_grade="B20",
                    steel_grade="CB300-V"):
    """
    Ve mat cat dung mong BTCT.

    Args:
        ftype: "single" (mong don) hoac "strip" (mong bang)
        L, B: Kich thuoc mat bang mong (mm)
        H: Chieu cao dai mong (mm)
        h_lot: Chieu day lop lot be tong (mm)
        col_w, col_d: Kich thuoc cot (mm)
        bot_dia: Duong kinh thep day mong (mm)
        bot_spacing: Khoang cach thep day (mm)
        cover: Lop bao ve (mm)
        depth_embed: Chieu sau chon mong (mm)
    """

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_aspect('equal')

    # Scale factor — hien thi mat cat theo chieu rong L
    # Goc toa do: tam mat bang mong, mat tren = 0

    # --- Ve nen dat ---
    soil_depth = depth_embed + 200  # hien thi dat sau hon mong
    soil_top_y = 0  # mat dat = 0

    # Dat tu nhien (ben ngoai mong)
    soil_left = patches.Rectangle((-L/2 - 300, -soil_depth), 300, soil_depth,
                                   linewidth=0, facecolor='#F5DEB3', zorder=0)
    soil_right = patches.Rectangle((L/2, -soil_depth), 300, soil_depth,
                                    linewidth=0, facecolor='#F5DEB3', zorder=0)
    ax.add_patch(soil_left)
    ax.add_patch(soil_right)

    # Dat backfill (2 ben mong)
    backfill_h = depth_embed - H - h_lot
    if backfill_h > 0:
        bf_left = patches.Rectangle((-L/2 - 50, -backfill_h), 50 + (L/2 - col_w/2), backfill_h,
                                     linewidth=0, facecolor='#FDEBD0', hatch='..', zorder=1)
        bf_right = patches.Rectangle((col_w/2, -backfill_h), (L/2 - col_w/2) + 50, backfill_h,
                                      linewidth=0, facecolor='#FDEBD0', hatch='..', zorder=1)
        ax.add_patch(bf_left)
        ax.add_patch(bf_right)

    # Mat dat (duong ngang)
    ax.plot([-L/2 - 300, L/2 + 300], [0, 0], color='#8B4513', linewidth=2.5, zorder=5)
    ax.text(L/2 + 310, 0, "±0.000", fontsize=9, va='center', ha='left', color='#8B4513', fontweight='bold')

    # --- Lop lot be tong ---
    lot_y = -(depth_embed)
    lot = patches.Rectangle((-L/2 - 50, lot_y), L + 100, h_lot,
                             linewidth=1.5, edgecolor='#7F8C8D', facecolor='#BDC3C7',
                             hatch='\\\\', zorder=2)
    ax.add_patch(lot)
    ax.text(L/2 + 60, lot_y + h_lot/2, f"Lot BT B7.5\nh={h_lot}",
            fontsize=8, va='center', ha='left', color='#7F8C8D', style='italic')

    # --- Dai mong ---
    dai_y = lot_y + h_lot
    dai = patches.Rectangle((-L/2, dai_y), L, H,
                             linewidth=2.5, edgecolor='#2C3E50', facecolor='#D5DBDB',
                             hatch='...', zorder=3)
    ax.add_patch(dai)

    # --- Cot (hien thi 1 doan nho phia tren dai mong) ---
    col_vis_h = min(col_w * 2, 500)  # Chieu cao cot hien thi
    col_y = dai_y + H
    col_rect = patches.Rectangle((-col_w/2, col_y), col_w, col_vis_h,
                                  linewidth=2, edgecolor='#2C3E50', facecolor='#AEB6BF',
                                  hatch='...', zorder=3)
    ax.add_patch(col_rect)

    # --- Cot thep day mong ---
    n_bars_show = int(L / bot_spacing) + 1
    rebar_y = dai_y + cover + bot_dia/2
    for i in range(min(n_bars_show, 25)):
        rx = -L/2 + cover + i * bot_spacing
        if rx > L/2 - cover:
            break
        bar = plt.Circle((rx, rebar_y), bot_dia/2 * 3,  # scale up de nhin thay
                         fill=True, facecolor='#C0392B', edgecolor='#922B21',
                         linewidth=0.5, zorder=4)
        ax.add_patch(bar)

    # --- Thep cho cot (thep doc cot xuong mong) ---
    col_bar_spacing = (col_w - 2 * 50) / 3 if col_w > 200 else col_w / 2
    for i in range(4):
        cbx = -col_w/2 + 50 + i * col_bar_spacing if col_w > 200 else -col_w/4 + i * col_w/2
        if cbx > col_w/2 - 30:
            break
        # Thep thang tu cot xuong mong (neo cong)
        col_bar_top = col_y + col_vis_h - 50
        col_bar_bot = dai_y + cover + bot_dia + 10
        ax.plot([cbx, cbx], [col_bar_top, col_bar_bot], color='#2980B9', linewidth=2, zorder=4)
        # Neo cong (L-hook)
        hook_len = bot_dia * 10 * 3  # scaled
        ax.plot([cbx, cbx + (hook_len if cbx < 0 else -hook_len) * 0.15], [col_bar_bot, col_bar_bot],
                color='#2980B9', linewidth=2, zorder=4)

    # --- DANH KICH THUOC ---
    dim_pad = max(L, H) * 0.08

    # Chieu rong mong L
    dim_y = dai_y - dim_pad * 2
    ax.annotate('', xy=(-L/2, dim_y), xytext=(L/2, dim_y),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(0, dim_y - dim_pad * 0.5, f"L = {L:.0f}",
            ha='center', va='top', fontsize=10, color='#2980B9', fontweight='bold')

    # Chieu cao mong H
    dim_x = L/2 + dim_pad * 1.5
    ax.annotate('', xy=(dim_x, dai_y), xytext=(dim_x, dai_y + H),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax.text(dim_x + dim_pad * 0.5, dai_y + H/2, f"H = {H:.0f}",
            ha='left', va='center', fontsize=10, color='#E74C3C', fontweight='bold', rotation=90)

    # Chieu sau chon
    dim_x2 = -L/2 - dim_pad * 1.5
    ax.annotate('', xy=(dim_x2, 0), xytext=(dim_x2, lot_y),
                arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5))
    ax.text(dim_x2 - dim_pad * 0.5, -depth_embed/2, f"Df = {depth_embed:.0f}",
            ha='right', va='center', fontsize=10, color='#27AE60', fontweight='bold', rotation=90)

    # Kich thuoc cot
    ax.annotate('', xy=(-col_w/2, col_y + col_vis_h + dim_pad * 0.5),
                xytext=(col_w/2, col_y + col_vis_h + dim_pad * 0.5),
                arrowprops=dict(arrowstyle='<->', color='#8E44AD', lw=1.2))
    ax.text(0, col_y + col_vis_h + dim_pad, f"Cot {col_w:.0f}x{col_d:.0f}",
            ha='center', va='bottom', fontsize=9, color='#8E44AD', fontweight='bold')

    # Lop bao ve
    ax.annotate(f"a={cover}", xy=(-L/2 + cover, rebar_y),
                xytext=(-L/2 - dim_pad * 2, rebar_y),
                arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1),
                fontsize=8, color='#E67E22',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#FDEBD0', edgecolor='#E67E22'))

    # Ghi chu thep day
    mid_bar_x = 0
    ax.annotate(f"\u03d5{bot_dia}@{bot_spacing}\n({steel_grade})",
                xy=(mid_bar_x, rebar_y),
                xytext=(L/2 + dim_pad * 3, dai_y + H * 0.3),
                arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.2),
                fontsize=9, fontweight='bold', color='#C0392B',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'))

    # --- Title ---
    type_name = "MONG DON" if ftype == "single" else "MONG BANG"
    ax.set_title(f"MAT CAT {type_name} ({L:.0f}x{B:.0f}x{H:.0f})",
                 fontsize=14, fontweight='bold', pad=15)

    # Gioi han
    x_pad = L * 0.4
    y_top = col_y + col_vis_h + L * 0.15
    y_bot = lot_y - L * 0.15
    ax.set_xlim(-L/2 - x_pad, L/2 + x_pad)
    ax.set_ylim(y_bot, y_top)
    ax.axis('off')

    # --- Bang ghi chu ky thuat ---
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"  1. {type_name} {L:.0f}x{B:.0f}x{H:.0f}mm, be tong {concrete_grade}.\n"
        f"  2. Lop lot be tong B7.5, day {h_lot:.0f}mm.\n"
        f"  3. Thep day mong: \u03d5{bot_dia}@{bot_spacing}, loai {steel_grade} (2 phuong).\n"
        f"  4. Lop bao ve: a = {cover:.0f}mm (theo TCVN 5574:2018, Dieu 10.3.1).\n"
        f"  5. Chieu sau chon mong: Df = {depth_embed:.0f}mm.\n"
        f"  6. Cot {col_w:.0f}x{col_d:.0f}mm, thep cho neo vao mong >= 30d.\n"
        f"  7. Tieu chuan ap dung: TCVN 5574:2018, TCVN 10304:2025."
    )
    fig.text(0.05, 0.01, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.13, 1, 0.95])
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\u2705 Da xuat mat cat mong: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve mat cat mong BTCT (mong don / mong bang)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_foundation.py --out mong.png --type single --L 2000 --B 2000 --H 600
  python draw_foundation.py --out mong.png --type strip --L 6000 --B 1200 --H 500
        """
    )
    parser.add_argument("--out", required=True, help="Duong dan xuat file anh (.png)")
    parser.add_argument("--type", choices=["single", "strip"], default="single", help="Loai mong")
    parser.add_argument("--L", type=float, default=2000, help="Chieu dai mong (mm)")
    parser.add_argument("--B", type=float, default=2000, help="Chieu rong mong (mm)")
    parser.add_argument("--H", type=float, default=600, help="Chieu cao dai mong (mm)")
    parser.add_argument("--h_lot", type=float, default=100, help="Chieu day lop lot (mm)")
    parser.add_argument("--col_w", type=float, default=400, help="Chieu rong cot (mm)")
    parser.add_argument("--col_d", type=float, default=400, help="Chieu sau cot (mm)")
    parser.add_argument("--bot_dia", type=float, default=16, help="Duong kinh thep day (mm)")
    parser.add_argument("--bot_spacing", type=float, default=150, help="Khoang cach thep day (mm)")
    parser.add_argument("--cover", type=float, default=50, help="Lop bao ve (mm)")
    parser.add_argument("--depth_embed", type=float, default=1200, help="Chieu sau chon mong (mm)")
    parser.add_argument("--concrete", type=str, default="B20", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB300-V", help="Loai thep")

    args = parser.parse_args()

    draw_foundation(
        args.out, ftype=args.type,
        L=args.L, B=args.B, H=args.H, h_lot=args.h_lot,
        col_w=args.col_w, col_d=args.col_d,
        bot_dia=args.bot_dia, bot_spacing=args.bot_spacing, cover=args.cover,
        depth_embed=args.depth_embed, concrete_grade=args.concrete,
        steel_grade=args.steel
    )
