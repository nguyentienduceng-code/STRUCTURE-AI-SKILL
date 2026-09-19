
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
draw_slab_rebar.py — Ve so do bo tri cot thep san BTCT

Su dung:
  python draw_slab_rebar.py --out san.png --Lx 6000 --Ly 4000 --slab_t 120 --bot_dia_x 12 --bot_sp_x 200 --bot_dia_y 10 --bot_sp_y 200 --top_dia 12 --top_sp 150 --top_ext 1500

Tinh nang:
  - Ve 2 panel: Mat bang bo tri thep + Mat cat ngang san
  - Hien thi thep lop duoi (2 phuong), thep mu (top bars tai goi)
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
def draw_slab_rebar(output_path,
                    Lx=6000, Ly=4000, slab_t=120,
                    bot_dia_x=12, bot_sp_x=200,
                    bot_dia_y=10, bot_sp_y=200,
                    top_dia=12, top_sp=150, top_ext=1500,
                    cover=20, concrete_grade="B25", steel_grade="CB300-V"):
    """
    Ve so do bo tri cot thep san BTCT (mat bang + mat cat).

    Args:
        Lx, Ly: Kich thuoc nhip san (mm)
        slab_t: Chieu day san (mm)
        bot_dia_x/y: Duong kinh thep lop duoi phuong X/Y (mm)
        bot_sp_x/y: Khoang cach thep lop duoi phuong X/Y (mm)
        top_dia: Duong kinh thep mu (mm)
        top_sp: Khoang cach thep mu (mm)
        top_ext: Chieu dai thep mu tu mep goi (mm)
        cover: Lop bao ve (mm)
    """

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 16),
                                    gridspec_kw={'height_ratios': [2, 1]})
    fig.suptitle(f"BO TRI COT THEP SAN BTCT (NHIP {Lx:.0f}x{Ly:.0f}, DAY {slab_t:.0f}mm)",
                 fontsize=14, fontweight='bold', y=0.98)

    # Scale cho mat bang (hien thi theo mm, nhung proportional)
    beam_w = 300  # Chieu rong dam bien hien thi

    # ================================================================
    # PANEL 1: MAT BANG BO TRI THEP (PLAN VIEW)
    # ================================================================
    ax1.set_aspect('equal')
    ax1.set_title("a) MAT BANG BO TRI COT THEP", fontsize=12, fontweight='bold', pad=10)

    # Ve san (vung san)
    slab_rect = patches.Rectangle((0, 0), Lx, Ly,
                                   linewidth=1.5, edgecolor='#95A5A6',
                                   facecolor='#FAFAFA', zorder=0)
    ax1.add_patch(slab_rect)

    # Ve dam bien (4 canh)
    beam_color = '#BDC3C7'
    # Dam trai
    ax1.add_patch(patches.Rectangle((-beam_w, 0), beam_w, Ly,
                                     linewidth=2, edgecolor='#2C3E50', facecolor=beam_color, hatch='///'))
    # Dam phai
    ax1.add_patch(patches.Rectangle((Lx, 0), beam_w, Ly,
                                     linewidth=2, edgecolor='#2C3E50', facecolor=beam_color, hatch='///'))
    # Dam duoi
    ax1.add_patch(patches.Rectangle((-beam_w, -beam_w), Lx + 2*beam_w, beam_w,
                                     linewidth=2, edgecolor='#2C3E50', facecolor=beam_color, hatch='///'))
    # Dam tren
    ax1.add_patch(patches.Rectangle((-beam_w, Ly), Lx + 2*beam_w, beam_w,
                                     linewidth=2, edgecolor='#2C3E50', facecolor=beam_color, hatch='///'))

    # --- Thep lop duoi phuong X (ngang — mau do) ---
    n_bot_x = int((Ly - 2 * cover) / bot_sp_y) + 1
    for i in range(min(n_bot_x, 30)):
        y = cover + i * bot_sp_y
        if y > Ly - cover:
            break
        ax1.plot([cover, Lx - cover], [y, y], color='#E74C3C', linewidth=1.2, zorder=2)

    # Nhan thep phuong X
    ax1.text(Lx/2, Ly * 0.15, f"\u03d5{bot_dia_x}@{bot_sp_x} (phuong X)\nLOP DUOI",
             ha='center', va='center', fontsize=9, color='#E74C3C', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#E74C3C', alpha=0.9),
             zorder=5)

    # --- Thep lop duoi phuong Y (doc — mau xanh) ---
    n_bot_y = int((Lx - 2 * cover) / bot_sp_x) + 1
    for i in range(min(n_bot_y, 30)):
        x = cover + i * bot_sp_x
        if x > Lx - cover:
            break
        ax1.plot([x, x], [cover, Ly - cover], color='#2980B9', linewidth=0.8,
                 linestyle='--', zorder=1)

    # Nhan thep phuong Y
    ax1.text(Lx * 0.15, Ly/2, f"\u03d5{bot_dia_y}@{bot_sp_y}\n(phuong Y)\nLOP DUOI",
             ha='center', va='center', fontsize=9, color='#2980B9', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#D6EAF8', edgecolor='#2980B9', alpha=0.9),
             zorder=5, rotation=90)

    # --- Thep mu (top bars) tai goi trai va phai ---
    top_color = '#8E44AD'
    # Goi trai
    for i in range(min(int((Ly - 2*cover) / top_sp) + 1, 30)):
        y = cover + i * top_sp
        if y > Ly - cover:
            break
        ax1.plot([0, min(top_ext, Lx/2)], [y, y], color=top_color, linewidth=1.8,
                 zorder=3, alpha=0.7)
    # Goi phai
    for i in range(min(int((Ly - 2*cover) / top_sp) + 1, 30)):
        y = cover + i * top_sp
        if y > Ly - cover:
            break
        ax1.plot([max(Lx - top_ext, Lx/2), Lx], [y, y], color=top_color, linewidth=1.8,
                 zorder=3, alpha=0.7)

    # Nhan thep mu
    ax1.text(top_ext/2, Ly * 0.85, f"\u03d5{top_dia}@{top_sp}\nTHEP MU",
             ha='center', va='center', fontsize=9, color=top_color, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8', edgecolor=top_color, alpha=0.9),
             zorder=5)

    # Danh kich thuoc nhip
    dim_y_bot = -beam_w - Ly * 0.08
    ax1.annotate('', xy=(0, dim_y_bot), xytext=(Lx, dim_y_bot),
                arrowprops=dict(arrowstyle='<->', color='#2C3E50', lw=1.5))
    ax1.text(Lx/2, dim_y_bot - Ly * 0.03, f"Lx = {Lx:.0f}",
            ha='center', va='top', fontsize=10, color='#2C3E50', fontweight='bold')

    dim_x_left = -beam_w - Lx * 0.06
    ax1.annotate('', xy=(dim_x_left, 0), xytext=(dim_x_left, Ly),
                arrowprops=dict(arrowstyle='<->', color='#2C3E50', lw=1.5))
    ax1.text(dim_x_left - Lx * 0.03, Ly/2, f"Ly = {Ly:.0f}",
            ha='right', va='center', fontsize=10, color='#2C3E50', fontweight='bold', rotation=90)

    # Chieu dai thep mu
    dim_y_top = Ly + beam_w + Ly * 0.05
    ax1.annotate('', xy=(0, dim_y_top), xytext=(top_ext, dim_y_top),
                arrowprops=dict(arrowstyle='<->', color=top_color, lw=1.2))
    ax1.text(top_ext/2, dim_y_top + Ly * 0.02, f"L_mu = {top_ext:.0f}",
            ha='center', va='bottom', fontsize=9, color=top_color, fontweight='bold')

    pad1 = max(Lx, Ly) * 0.15
    ax1.set_xlim(-beam_w - pad1, Lx + beam_w + pad1)
    ax1.set_ylim(-beam_w - pad1, Ly + beam_w + pad1)
    ax1.axis('off')

    # ================================================================
    # PANEL 2: MAT CAT NGANG SAN (SECTION VIEW)
    # ================================================================
    ax2.set_aspect('equal')
    ax2.set_title("b) MAT CAT NGANG SAN", fontsize=12, fontweight='bold', pad=10)

    # Scale cho mat cat — hien thi chieu day san chi tiet
    sec_L = Lx  # Chieu dai mat cat
    sec_H = slab_t  # Chieu day san

    # Ve san (mat cat)
    slab_sec = patches.Rectangle((0, 0), sec_L, sec_H,
                                  linewidth=2, edgecolor='#2C3E50',
                                  facecolor='#D5DBDB', hatch='...', zorder=1)
    ax2.add_patch(slab_sec)

    # Ve dam bien (2 dau)
    beam_sec_h = sec_H + 200  # Dam cao hon san
    ax2.add_patch(patches.Rectangle((-beam_w, -(beam_sec_h - sec_H), ), beam_w, beam_sec_h,
                                     linewidth=2, edgecolor='#2C3E50', facecolor='#BDC3C7',
                                     hatch='///', zorder=2))
    ax2.add_patch(patches.Rectangle((sec_L, -(beam_sec_h - sec_H)), beam_w, beam_sec_h,
                                     linewidth=2, edgecolor='#2C3E50', facecolor='#BDC3C7',
                                     hatch='///', zorder=2))

    # Thep lop duoi (hien thi bang cac vong tron)
    bar_scale = max(slab_t * 0.06, bot_dia_x * 1.5)  # Scale de nhin thay
    rebar_bot_y = cover + bot_dia_x / 2
    n_show = min(int(sec_L / bot_sp_x) + 1, 30)
    for i in range(n_show):
        rx = cover + i * bot_sp_x
        if rx > sec_L - cover:
            break
        bar = plt.Circle((rx, rebar_bot_y), bar_scale,
                         fill=True, facecolor='#E74C3C', edgecolor='#922B21',
                         linewidth=0.5, zorder=3)
        ax2.add_patch(bar)

    # Thep lop tren (thep mu — chi o 2 dau)
    rebar_top_y = sec_H - cover - top_dia / 2
    for i in range(min(int(top_ext / top_sp) + 1, 15)):
        rx = cover + i * top_sp
        if rx > top_ext:
            break
        bar = plt.Circle((rx, rebar_top_y), bar_scale,
                         fill=True, facecolor='#8E44AD', edgecolor='#6C3483',
                         linewidth=0.5, zorder=3)
        ax2.add_patch(bar)
    for i in range(min(int(top_ext / top_sp) + 1, 15)):
        rx = sec_L - cover - i * top_sp
        if rx < sec_L - top_ext:
            break
        bar = plt.Circle((rx, rebar_top_y), bar_scale,
                         fill=True, facecolor='#8E44AD', edgecolor='#6C3483',
                         linewidth=0.5, zorder=3)
        ax2.add_patch(bar)

    # Danh kich thuoc chieu day san
    dim_x_sec = sec_L + beam_w + sec_L * 0.05
    ax2.annotate('', xy=(dim_x_sec, 0), xytext=(dim_x_sec, sec_H),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax2.text(dim_x_sec + sec_L * 0.02, sec_H/2, f"h = {slab_t:.0f}",
            ha='left', va='center', fontsize=10, color='#E74C3C', fontweight='bold')

    # Lop bao ve
    ax2.annotate(f"a={cover}", xy=(sec_L * 0.1, cover),
                xytext=(sec_L * 0.1, -sec_H * 0.8),
                arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1),
                fontsize=8, color='#E67E22',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#FDEBD0', edgecolor='#E67E22'))

    # Ghi chu thep
    ax2.annotate(f"\u03d5{bot_dia_x}@{bot_sp_x} (lop duoi)",
                xy=(sec_L * 0.5, rebar_bot_y),
                xytext=(sec_L * 0.5, -sec_H * 1.2),
                arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.2),
                fontsize=9, fontweight='bold', color='#C0392B',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'))

    ax2.annotate(f"\u03d5{top_dia}@{top_sp} (thep mu)",
                xy=(top_ext * 0.5, rebar_top_y),
                xytext=(top_ext * 0.5, sec_H * 2),
                arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=1.2),
                fontsize=9, fontweight='bold', color='#8E44AD',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8', edgecolor='#8E44AD'))

    sec_pad_x = sec_L * 0.15
    sec_pad_y = max(sec_H * 3, beam_sec_h * 0.8)
    ax2.set_xlim(-beam_w - sec_pad_x, sec_L + beam_w + sec_pad_x)
    ax2.set_ylim(-sec_pad_y, sec_H + sec_pad_y * 0.6)
    ax2.axis('off')

    # --- Bang ghi chu ky thuat ---
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"  1. San BTCT day {slab_t:.0f}mm, nhip {Lx:.0f}x{Ly:.0f}mm, be tong {concrete_grade}.\n"
        f"  2. Thep lop duoi phuong X: \u03d5{bot_dia_x}@{bot_sp_x}, loai {steel_grade}.\n"
        f"  3. Thep lop duoi phuong Y: \u03d5{bot_dia_y}@{bot_sp_y}, loai {steel_grade}.\n"
        f"  4. Thep mu (lop tren tai goi): \u03d5{top_dia}@{top_sp}, dai {top_ext:.0f}mm tu mep goi.\n"
        f"  5. Lop bao ve: a = {cover:.0f}mm (theo TCVN 5574:2018, Dieu 10.3.1).\n"
        f"  6. Tieu chuan ap dung: TCVN 5574:2018, TCVN 2737:2023."
    )
    fig.text(0.05, 0.01, note_text, fontsize=8.5, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.09, 1, 0.95])
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\u2705 Da xuat bo tri thep san: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve so do bo tri cot thep san BTCT (mat bang + mat cat)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_slab_rebar.py --out san.png --Lx 6000 --Ly 4000 --slab_t 120
  python draw_slab_rebar.py --out san.png --Lx 8000 --Ly 5000 --slab_t 150 --bot_dia_x 14 --bot_sp_x 150
        """
    )
    parser.add_argument("--out", required=True, help="Duong dan xuat file anh (.png)")
    parser.add_argument("--Lx", type=float, default=6000, help="Nhip san phuong X (mm)")
    parser.add_argument("--Ly", type=float, default=4000, help="Nhip san phuong Y (mm)")
    parser.add_argument("--slab_t", type=float, default=120, help="Chieu day san (mm)")
    parser.add_argument("--bot_dia_x", type=float, default=12, help="Duong kinh thep duoi phuong X (mm)")
    parser.add_argument("--bot_sp_x", type=float, default=200, help="Khoang cach thep duoi phuong X (mm)")
    parser.add_argument("--bot_dia_y", type=float, default=10, help="Duong kinh thep duoi phuong Y (mm)")
    parser.add_argument("--bot_sp_y", type=float, default=200, help="Khoang cach thep duoi phuong Y (mm)")
    parser.add_argument("--top_dia", type=float, default=12, help="Duong kinh thep mu (mm)")
    parser.add_argument("--top_sp", type=float, default=150, help="Khoang cach thep mu (mm)")
    parser.add_argument("--top_ext", type=float, default=1500, help="Chieu dai thep mu tu mep goi (mm)")
    parser.add_argument("--cover", type=float, default=20, help="Lop bao ve (mm)")
    parser.add_argument("--concrete", type=str, default="B25", help="Cap be tong")
    parser.add_argument("--steel", type=str, default="CB300-V", help="Loai thep")

    args = parser.parse_args()

    draw_slab_rebar(
        args.out,
        Lx=args.Lx, Ly=args.Ly, slab_t=args.slab_t,
        bot_dia_x=args.bot_dia_x, bot_sp_x=args.bot_sp_x,
        bot_dia_y=args.bot_dia_y, bot_sp_y=args.bot_sp_y,
        top_dia=args.top_dia, top_sp=args.top_sp, top_ext=args.top_ext,
        cover=args.cover, concrete_grade=args.concrete, steel_grade=args.steel
    )
