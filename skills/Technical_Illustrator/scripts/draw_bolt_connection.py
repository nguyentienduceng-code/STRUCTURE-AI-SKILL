
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
draw_bolt_connection.py — Ve chi tiet lien ket bu long ky thuat

Su dung:
  python draw_bolt_connection.py --out lienket.png
  python draw_bolt_connection.py --out lienket.png --bolt_d 24 --bolt_grade 8.8 --plate_t 16 --n_rows 2 --n_cols 2 --beam_h 300 --beam_b 150 --beam_tw 6.5 --beam_tf 9

Tinh nang:
  - Ve mat bang bo tri bu long (Plan View) va mat cat ngang (Section View) tren cung 1 hinh
  - Tu dong tinh khoang cach min theo TCVN 5575:2024 (3d, 2d, 1.5d)
  - Hien thi dung ghi chu ky thuat (Bolt grade, torque, duong han, kich thuoc ban ma)
  - Xuat file .png chat luong cao (300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np
import argparse
import math
import sys

# Fix Unicode issue on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


@with_error_handling
def draw_bolt_connection(output_path,
                         bolt_d=24, bolt_grade="8.8", plate_t=16,
                         n_rows=2, n_cols=2,
                         beam_h=300, beam_b=150, beam_tw=6.5, beam_tf=9,
                         weld_hf=8):
    """
    Ve chi tiet lien ket bu long dam thep vao ban ma / cot.
    
    Args:
        bolt_d: Duong kinh bu long (mm)
        bolt_grade: Cap ben bu long (VD: "8.8", "10.9")
        plate_t: Do day ban ma (mm)
        n_rows: So hang bu long (doc theo dam)
        n_cols: So cot bu long (ngang)
        beam_h/b/tw/tf: Kich thuoc dam thep
        weld_hf: Chieu cao duong han goc (mm)
    """
    
    # --- Tinh toan thong so theo TCVN 5575:2024 ---
    bolt_hole = bolt_d + 2  # Lo bu long = d + 2mm (lo tieu chuan)
    e_min = 2 * bolt_d      # Khoang cach min tu tam bu long den mep ban ma (>= 2d)
    p_min = 3 * bolt_d      # Buoc bu long min (>= 3d)
    
    # Kich thuoc ban ma
    plate_w = 2 * e_min + (n_cols - 1) * p_min
    plate_h_total = 2 * e_min + (n_rows - 1) * p_min
    
    # Suc khang cat 1 bu long (cap ben 8.8)
    bolt_grades = {
        "4.6": {"fub": 400, "fyb": 240},
        "5.6": {"fub": 500, "fyb": 300},
        "8.8": {"fub": 800, "fyb": 640},
        "10.9": {"fub": 1000, "fyb": 900},
    }
    grade_info = bolt_grades.get(bolt_grade, bolt_grades["8.8"])
    fub = grade_info["fub"]
    fyb = grade_info["fyb"]
    A_bolt = math.pi * (bolt_d ** 2) / 4  # mm2
    
    # === TAO HINH VE 2 PANEL ===
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
    fig.suptitle(f"CHI TIET LIEN KET BU LONG M{bolt_d} (Cap ben {bolt_grade})",
                 fontsize=16, fontweight='bold', y=0.98)
    
    # ================================================================
    # PANEL 1: MAT BANG BO TRI BU LONG (PLAN VIEW)
    # ================================================================
    ax1.set_aspect('equal')
    ax1.set_title("a) MAT BANG BO TRI BU LONG", fontsize=12, fontweight='bold', pad=15)
    
    # Ve ban ma (Gusset Plate)
    plate = patches.Rectangle((-plate_w/2, -plate_h_total/2), plate_w, plate_h_total,
                               linewidth=2, edgecolor='#333333', facecolor='#D4E6F1', zorder=1)
    ax1.add_patch(plate)
    
    # Ve ban bung dam (duong net dut)
    web_rect = patches.Rectangle((-beam_tw/2, -plate_h_total/2 - 10), beam_tw, plate_h_total + 20,
                                  linewidth=1.5, edgecolor='blue', facecolor='#AED6F1',
                                  linestyle='--', zorder=2, alpha=0.5)
    ax1.add_patch(web_rect)
    ax1.text(0, -plate_h_total/2 - 15, f"Ban bung tw={beam_tw}",
             ha='center', va='top', fontsize=8, color='blue', style='italic')
    
    # Ve cac bu long
    for row in range(n_rows):
        for col in range(n_cols):
            cx = -plate_w/2 + e_min + col * p_min
            cy = -plate_h_total/2 + e_min + row * p_min
            
            # Lo bu long (vong tron rong)
            hole = plt.Circle((cx, cy), bolt_hole/2, fill=False,
                             edgecolor='#333333', linewidth=1.5, zorder=3)
            ax1.add_patch(hole)
            
            # Than bu long (vong tron day)
            bolt_body = plt.Circle((cx, cy), bolt_d/2, fill=True,
                                  facecolor='#2C3E50', edgecolor='black',
                                  linewidth=0.5, zorder=4)
            ax1.add_patch(bolt_body)
            
            # Dau cheo (ky hieu bu long cao cap)
            cross_r = bolt_d / 2 * 0.7
            ax1.plot([cx - cross_r, cx + cross_r], [cy - cross_r, cy + cross_r],
                    color='white', linewidth=1, zorder=5)
            ax1.plot([cx - cross_r, cx + cross_r], [cy + cross_r, cy - cross_r],
                    color='white', linewidth=1, zorder=5)
    
    # --- DANH KICH THUOC ---
    # Khoang cach mep (e)
    e_y = -plate_h_total/2
    bolt_x0 = -plate_w/2 + e_min
    dim_offset = plate_h_total/2 + 25
    
    # Buoc bu long p (ngang)
    if n_cols > 1:
        ax1.annotate('', xy=(bolt_x0, dim_offset), xytext=(bolt_x0 + p_min, dim_offset),
                    arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax1.text(bolt_x0 + p_min/2, dim_offset + 8, f"p = {p_min}",
                ha='center', va='bottom', fontsize=9, color='red', fontweight='bold')
    
    # Khoang cach mep e (ngang)
    ax1.annotate('', xy=(-plate_w/2, dim_offset + 25), xytext=(bolt_x0, dim_offset + 25),
                arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1.5))
    ax1.text((-plate_w/2 + bolt_x0)/2, dim_offset + 33, f"e = {e_min}",
            ha='center', va='bottom', fontsize=9, color='#E67E22', fontweight='bold')
    
    # Tong chieu rong ban ma
    ax1.annotate('', xy=(-plate_w/2, -dim_offset - 10), xytext=(plate_w/2, -dim_offset - 10),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
    ax1.text(0, -dim_offset - 2, f"W = {plate_w:.0f}",
            ha='center', va='bottom', fontsize=9, color='green', fontweight='bold')
    
    # Duong han goc (2 ben)
    for sign in [-1, 1]:
        weld_x = sign * beam_tw / 2
        weld_y_start = -plate_h_total / 2
        weld_y_end = plate_h_total / 2
        ax1.plot([weld_x, weld_x], [weld_y_start, weld_y_end],
                color='red', linewidth=3, zorder=6, alpha=0.6)
    ax1.text(beam_tw/2 + 5, 0, f"hf={weld_hf}", fontsize=8, color='red',
            va='center', ha='left', rotation=90, style='italic')
    
    padding1 = max(plate_w, plate_h_total) * 0.45
    ax1.set_xlim(-plate_w/2 - padding1, plate_w/2 + padding1)
    ax1.set_ylim(-plate_h_total/2 - padding1, plate_h_total/2 + padding1)
    ax1.axis('off')
    
    # ================================================================
    # PANEL 2: MAT CAT NGANG (SECTION VIEW)
    # ================================================================
    ax2.set_aspect('equal')
    ax2.set_title("b) MAT CAT LIEN KET (Section A-A)", fontsize=12, fontweight='bold', pad=15)
    
    # --- Ve dam thep (phia trai) ---
    beam_draw_w = 80  # Chieu rong hien thi phan dam
    beam_x0 = -beam_draw_w
    
    # Ban bung dam
    ax2.add_patch(patches.Rectangle((beam_x0, -beam_h/2 + beam_tf), beam_draw_w, beam_h - 2*beam_tf,
                                     linewidth=1.5, edgecolor='blue', facecolor='#AED6F1', hatch='//'))
    # Canh tren
    ax2.add_patch(patches.Rectangle((beam_x0 - (beam_b - beam_draw_w)/2, beam_h/2 - beam_tf),
                                     beam_b, beam_tf,
                                     linewidth=1.5, edgecolor='blue', facecolor='#AED6F1', hatch='//'))
    # Canh duoi
    ax2.add_patch(patches.Rectangle((beam_x0 - (beam_b - beam_draw_w)/2, -beam_h/2),
                                     beam_b, beam_tf,
                                     linewidth=1.5, edgecolor='blue', facecolor='#AED6F1', hatch='//'))
    
    # --- Ve ban ma (2 tam doi xung) ---
    gap = beam_tw + 2  # Khe ho giua 2 ban ma
    gusset_draw_w = 60
    
    for sign_y in [1, -1]:
        y_offset = gap / 2 if sign_y == 1 else -(gap / 2 + plate_t)
        gusset = patches.Rectangle((0, y_offset), gusset_draw_w, plate_t,
                                    linewidth=1.5, edgecolor='#333333', facecolor='#F5B041', zorder=3)
        ax2.add_patch(gusset)
    
    # --- Ve bu long (mat cat doc) ---
    bolt_len = gap + 2 * plate_t + 10  # Chieu dai bu long hien thi
    bolt_center_x = gusset_draw_w / 2
    
    # Than bu long
    ax2.add_patch(patches.Rectangle((bolt_center_x - bolt_d/4, -(bolt_len/2)),
                                     bolt_d/2, bolt_len,
                                     linewidth=1, edgecolor='#2C3E50', facecolor='#5D6D7E', zorder=4))
    
    # Dau bu long (hex - phia tren)
    head_w = bolt_d * 1.5
    head_h = bolt_d * 0.6
    ax2.add_patch(patches.Rectangle((bolt_center_x - head_w/2, bolt_len/2),
                                     head_w, head_h,
                                     linewidth=1.5, edgecolor='#2C3E50', facecolor='#2C3E50', zorder=5))
    
    # Oc (Nut - phia duoi)
    nut_h = bolt_d * 0.8
    ax2.add_patch(patches.Rectangle((bolt_center_x - head_w/2, -(bolt_len/2 + nut_h)),
                                     head_w, nut_h,
                                     linewidth=1.5, edgecolor='#2C3E50', facecolor='#34495E', zorder=5))
    
    # Long den (Washer - tren va duoi)
    washer_w = bolt_d * 2
    washer_h = 3
    ax2.add_patch(patches.Rectangle((bolt_center_x - washer_w/2, bolt_len/2 - washer_h),
                                     washer_w, washer_h,
                                     linewidth=0.5, edgecolor='gray', facecolor='#BDC3C7', zorder=4))
    ax2.add_patch(patches.Rectangle((bolt_center_x - washer_w/2, -(bolt_len/2)),
                                     washer_w, washer_h,
                                     linewidth=0.5, edgecolor='gray', facecolor='#BDC3C7', zorder=4))
    
    # --- GHI CHU KY THUAT (Leader Lines) ---
    note_x = gusset_draw_w + 30
    
    # Ghi chu bu long
    ax2.annotate(f"Bu long M{bolt_d}\nCap ben {bolt_grade}\nfub = {fub} MPa",
                xy=(bolt_center_x, 0), xytext=(note_x + 20, 60),
                arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.2),
                fontsize=8.5, fontweight='bold', color='#C0392B',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FADBD8', edgecolor='#C0392B'))
    
    # Ghi chu ban ma
    ax2.annotate(f"Ban ma PL{plate_t}\nSS400 (fy=235MPa)",
                xy=(gusset_draw_w/2, gap/2 + plate_t), xytext=(note_x + 20, gap/2 + plate_t + 40),
                arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2),
                fontsize=8.5, fontweight='bold', color='#E67E22',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEBD0', edgecolor='#E67E22'))
    
    # Ghi chu duong han
    ax2.annotate(f"Duong han goc\nhf = {weld_hf}mm\nN42 (fwu=410MPa)",
                xy=(0, 0), xytext=(-beam_draw_w - 60, -60),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
                fontsize=8.5, fontweight='bold', color='red',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE0E0', edgecolor='red'))
    
    # Ghi chu dam thep
    ax2.annotate(f"Dam I-{beam_h}x{beam_b}x{beam_tw}x{beam_tf}",
                xy=(beam_x0 + beam_draw_w/2, beam_h/2 - beam_tf/2),
                xytext=(beam_x0 - 30, beam_h/2 + 40),
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.2),
                fontsize=8.5, fontweight='bold', color='blue',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#D6EAF8', edgecolor='blue'))
    
    # Danh kich thuoc plate_t
    dim_x = gusset_draw_w + 10
    ax2.annotate('', xy=(dim_x, gap/2), xytext=(dim_x, gap/2 + plate_t),
                arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=1.2))
    ax2.text(dim_x + 3, gap/2 + plate_t/2, f"t={plate_t}", fontsize=8,
            color='#E67E22', va='center', ha='left')
    
    sec_padding = max(beam_h, plate_w) * 0.5
    ax2.set_xlim(-beam_draw_w - beam_b/2 - 80, gusset_draw_w + 130)
    ax2.set_ylim(-beam_h/2 - sec_padding, beam_h/2 + sec_padding)
    ax2.axis('off')
    
    # ================================================================
    # BANG GHI CHU KY THUAT (o cuoi hinh)
    # ================================================================
    note_text = (
        f"GHI CHU KY THUAT:\n"
        f"  1. Bu long M{bolt_d}, Cap ben {bolt_grade} (fub={fub}MPa, fyb={fyb}MPa). "
        f"Ma kem nhung nong.\n"
        f"  2. Ban ma thep PL{plate_t}, vat lieu SS400/Q235B (fy=235MPa).\n"
        f"  3. Duong han goc hf={weld_hf}mm, que han N42 (fwu=410MPa).\n"
        f"  4. Lo bu long d0={bolt_hole}mm (lo tieu chuan). "
        f"Khoang cach mep e>={e_min}mm, buoc p>={p_min}mm (TCVN 5575:2024).\n"
        f"  5. Siet bu long bang co le luc, mo-men xiet theo bang 43 TCVN 5575:2024.\n"
        f"  6. Long den phang + long den vong duoi oc (theo TCVN 1916:1995)."
    )
    fig.text(0.05, 0.01, note_text, fontsize=8, family='monospace',
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='#F9F9F9', edgecolor='#CCCCCC'))
    
    plt.tight_layout(rect=[0, 0.12, 1, 0.95])
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Đã xuất chi tiết liên kết bu lông: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve chi tiet lien ket bu long (Plan + Section)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_bolt_connection.py --out lienket_M24.png
  python draw_bolt_connection.py --out lienket_M20.png --bolt_d 20 --bolt_grade 10.9 --n_rows 3 --n_cols 2
        """
    )
    parser.add_argument("--out", required=True, help="Duong dan xuat file anh (.png)")
    parser.add_argument("--bolt_d", type=float, default=24, help="Duong kinh bu long (mm)")
    parser.add_argument("--bolt_grade", type=str, default="8.8", help="Cap ben (4.6/5.6/8.8/10.9)")
    parser.add_argument("--plate_t", type=float, default=16, help="Do day ban ma (mm)")
    parser.add_argument("--n_rows", type=int, default=2, help="So hang bu long")
    parser.add_argument("--n_cols", type=int, default=2, help="So cot bu long")
    parser.add_argument("--beam_h", type=float, default=300, help="Chieu cao dam")
    parser.add_argument("--beam_b", type=float, default=150, help="Chieu rong canh dam")
    parser.add_argument("--beam_tw", type=float, default=6.5, help="Do day ban bung")
    parser.add_argument("--beam_tf", type=float, default=9, help="Do day ban canh")
    parser.add_argument("--weld_hf", type=float, default=8, help="Chieu cao duong han goc (mm)")
    args = parser.parse_args()
    
    draw_bolt_connection(
        args.out,
        bolt_d=args.bolt_d, bolt_grade=args.bolt_grade, plate_t=args.plate_t,
        n_rows=args.n_rows, n_cols=args.n_cols,
        beam_h=args.beam_h, beam_b=args.beam_b, beam_tw=args.beam_tw, beam_tf=args.beam_tf,
        weld_hf=args.weld_hf
    )
