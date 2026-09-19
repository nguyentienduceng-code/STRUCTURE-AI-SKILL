
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
draw_ke_pi_gieng.py — Bản Vẽ Kỹ Thuật Chi Tiết: KÈ PI GIẾNG (Buy BTCT + Cọc Thép Neo)
Phương án Nhà Thầu Tấn Khoa — Phân Đoạn C
Output: PNG 300 DPI, A3 ngang
"""
import sys, os, argparse, math
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon, Arc
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import date

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,
                     'axes.linewidth':0.8,'axes.titlesize':9,'axes.titleweight':'bold'})

# ── Màu sắc ──────────────────────────────────────────────────────────────────
C_CONCRETE = '#B0B0B0'   # BTCT buy
C_STEEL    = '#3A3A3A'   # Thép hình
C_SOIL     = '#C4A265'   # Đất
C_WATER    = '#5B9BD5'   # Nước
C_GEO      = '#4CAF50'   # Vải địa kỹ thuật
C_GROUT    = '#E8E0D0'   # Vữa lấp trong buy
C_DIM      = '#1A1A8C'   # Kích thước
C_RED      = '#CC0000'   # Cảnh báo
C_TITLE    = '#1C3557'   # Tiêu đề
C_ANCHOR   = '#8B4513'   # Giằng neo
C_BG       = '#F9F9F9'

def dim_line(ax, x1,y1,x2,y2,label,text_off=0,orient='h',fs=7,color=C_DIM):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),
                arrowprops=dict(arrowstyle='<->',color=color,lw=0.9,mutation_scale=8))
    mx=(x1+x2)/2+(text_off if orient=='v' else 0)
    my=(y1+y2)/2+(text_off if orient=='h' else 0)
    ax.text(mx,my,label,ha='center',va='center',color=color,fontsize=fs,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1',facecolor='white',edgecolor='none',alpha=0.9))

@with_error_handling
def draw_buy(ax, cx, cy, r=0.20, wall_t=0.04, grout=True):
    """Vẽ buy BTCT tròn mặt cắt (hình vành khuyên + vữa trong)"""
    outer = Circle((cx,cy), r, facecolor=C_GROUT if grout else C_CONCRETE,
                   edgecolor=C_CONCRETE, linewidth=1.5, zorder=4)
    inner_wall = Circle((cx,cy), r, facecolor='none',
                        edgecolor='#666666', linewidth=2.0, zorder=5)
    # Vách bê tông (hatch)
    ring = matplotlib.patches.Wedge((cx,cy), r, 0, 360, width=wall_t,
                                    facecolor=C_CONCRETE, edgecolor='#555555',
                                    linewidth=1.0, hatch='/', alpha=0.8, zorder=6)
    ax.add_patch(outer)
    ax.add_patch(ring)

@with_error_handling
def draw_steel_V100(ax, cx, y_bottom, height, color=C_STEEL, lw=2.5):
    """Vẽ cọc thép V100 (I-section đơn giản hóa)"""
    w=0.05; tw=0.008; tf=0.010
    # Web (thân)
    web = Rectangle((cx-tw/2, y_bottom), tw, height,
                    facecolor=color, edgecolor='black', linewidth=0.5, zorder=7)
    ax.add_patch(web)
    # Flanges
    for y in [y_bottom, y_bottom+height]:
        fl = Rectangle((cx-w/2, y-tf/2), w, tf,
                        facecolor=color, edgecolor='black', linewidth=0.5, zorder=7)
        ax.add_patch(fl)

@with_error_handling
def draw_V50_frame(ax, x1, x2, y, color=C_STEEL, lw=2.0):
    """Vẽ cụm neo V50 ngang"""
    size=0.025
    ax.plot([x1,x2],[y,y],color=color,lw=lw,zorder=6)
    for x in [x1,x2]:
        sq = Rectangle((x-size/2,y-size/2), size, size,
                        facecolor=color, edgecolor='black', linewidth=0.5, zorder=7)
        ax.add_patch(sq)

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16.54,11.69))
fig.patch.set_facecolor('white')
gs = GridSpec(2,3,figure=fig,left=0.04,right=0.97,top=0.88,bottom=0.11,
              wspace=0.38,hspace=0.48)

ax1 = fig.add_subplot(gs[:,  :2])   # Mặt cắt chi tiết kè — chiếm 2/3 trái
ax2 = fig.add_subplot(gs[0,   2])   # Chi tiết giằng BTCT neo
ax3 = fig.add_subplot(gs[1,   2])   # Chi tiết cụm neo V50 + bảng vật liệu

# ════════════════════════════════════════════════════════════════════════════
# PANEL 1 — MẶT CẮT CHI TIẾT KÈ (Tỷ lệ 1:25)
# ════════════════════════════════════════════════════════════════════════════
ax = ax1
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title('MẶT CẮT CHI TIẾT KÈ PI GIẾNG — Tỷ lệ 1:25\n'
             'Phương án Nhà Thầu Tấn Khoa — Phân Đoạn C', fontsize=9,
             fontweight='bold', color=C_TITLE, pad=6)

# Tham số hình học (đơn vị: m)
buy_r   = 0.20        # Bán kính buy Φ400
buy_row = 4           # 4 hàng buy (cao trung bình)
buy_sp  = 0.42        # khoảng cách tâm buy theo đứng
wall_base_y = 0.0
wall_top_y  = wall_base_y + buy_row * buy_sp   # ≈ 1.68m ~ gần 1.7m chiều cao
V100_h  = 2.5         # Chiều dài cọc thép V100 (phần trên mặt đất)
V100_embed = 1.7      # Cắm sâu vào đất 1.5÷2m → lấy 1.7m

# Vị trí x
x_wall   = 0.0        # Tim tường buy
x_soil_L = -2.0       # Mép trái (phía sông)
x_soil_R =  4.5       # Mép phải (phía đất đắp)

# ── Nước (phía sông) ─────────────────────────────────────────────────────────
water = Rectangle((x_soil_L, -0.8), 1.8, 2.8, facecolor=C_WATER, alpha=0.25, zorder=0)
ax.add_patch(water)
for wy in [0.1, 0.4, 0.7, 1.0, 1.3]:
    wx = np.linspace(x_soil_L, x_soil_L+1.8, 20)
    wys = [wy + 0.03*np.sin(5*x*np.pi) for x in wx]
    ax.plot(wx, wys, color=C_WATER, lw=1.0, alpha=0.6)
ax.text(x_soil_L+0.9, 1.5, 'PHÍA\nSÔNG', ha='center', va='center',
        color=C_WATER, fontsize=8, fontweight='bold', alpha=0.8)

# ── Đất nền (phía dưới và đắp) ───────────────────────────────────────────────
soil_base = Rectangle((x_soil_L, -0.8), x_soil_R-x_soil_L+0.5, 0.8,
                       facecolor=C_SOIL, edgecolor='#8B6914', lw=0.8, alpha=0.5, zorder=1)
ax.add_patch(soil_base)
# Đất đắp phía sau
soil_fill = Rectangle((x_wall+0.25, 0.0), x_soil_R-0.75, wall_top_y+0.5,
                        facecolor=C_SOIL, edgecolor='none', alpha=0.3, zorder=1)
ax.add_patch(soil_fill)
# Ký hiệu đất đắp
for xi in np.arange(0.6, x_soil_R, 0.5):
    for yi in np.arange(0.2, wall_top_y, 0.5):
        ax.plot([xi, xi+0.15],[yi,yi-0.12],color='#8B6914',lw=0.5,alpha=0.35)
ax.text(2.5, wall_top_y/2+0.1, 'ĐẤT ĐẮP', ha='center', va='center',
        color='#6B4C00', fontsize=8, fontweight='bold', alpha=0.7, style='italic')

# ── Vải địa kỹ thuật ─────────────────────────────────────────────────────────
geo_xs = [x_wall+0.21, x_wall+0.21, x_wall+0.21+2.4]
geo_ys = [0.0, 1.2, 1.2]
ax.plot(geo_xs, geo_ys, color=C_GEO, lw=2.5, ls='--', label='Vải ĐKT', zorder=5)
ax.text(x_wall+1.6, 1.28, 'Vải ĐKT\n0.4×2.4m', ha='center', color=C_GEO, fontsize=6.5)

# ── Lớp vữa lót tạo phẳng (>1m) ─────────────────────────────────────────────
grout_lining = Rectangle((x_wall-0.22, -0.15), 0.44, 0.15,
                           facecolor='#E0D8C0', edgecolor='#888', lw=0.7, alpha=0.8, zorder=3)
ax.add_patch(grout_lining)
ax.text(x_wall, -0.07, 'Vữa lót\ntạo phẳng', ha='center', va='center',
        fontsize=6, color='#555555')

# ── Cọc thép V100 ─────────────────────────────────────────────────────────────
# Vẽ 1 cọc tại x_wall (phần nhìn thấy trong mặt cắt)
# Phần ngầm dưới đất
draw_steel_V100(ax, x_wall+0.40, -V100_embed, V100_embed, color='#2F4F4F', lw=2.5)
# Phần trên mặt đất
draw_steel_V100(ax, x_wall+0.40, 0.0, wall_top_y+0.30, color=C_STEEL, lw=2.5)

# Mũi tên + ghi chú cọc thép
ax.annotate('Thép cọc neo V100\nL=6m (cắm sâu 1.5÷2m)',
            xy=(x_wall+0.40, 1.2),
            xytext=(x_wall+0.40+0.8, 1.8),
            arrowprops=dict(arrowstyle='->',color=C_STEEL,lw=0.9),
            fontsize=6.5, ha='left', color=C_STEEL, fontweight='bold')

# ── Vẽ 4 hàng buy BTCT ───────────────────────────────────────────────────────
for row in range(buy_row):
    cy = wall_base_y + buy_r + row * buy_sp
    draw_buy(ax, x_wall, cy, r=buy_r, wall_t=0.04, grout=True)
    # Ghi chú vữa trong buy
    if row == 1:
        ax.annotate('Vữa trong lòng buy\n(1 bao XM/buy)',
                    xy=(x_wall, cy),
                    xytext=(x_wall-0.8, cy+0.4),
                    arrowprops=dict(arrowstyle='->',color='#555',lw=0.8),
                    fontsize=6.5, ha='center', color='#444444')

# ── Cụm neo buy thép V50 (ngang) ─────────────────────────────────────────────
for row in [1, 3]:  # tại hàng 2 và 4
    cy = wall_base_y + buy_r + row * buy_sp
    draw_V50_frame(ax, x_wall+0.21, x_wall+0.55, cy, color='#1A237E', lw=2.5)
ax.annotate('Cụm neo buy\nthép V50\n(100×100mm)',
            xy=(x_wall+0.4, wall_base_y+buy_r+buy_sp),
            xytext=(x_wall+0.4+1.0, wall_base_y+buy_r+buy_sp-0.3),
            arrowprops=dict(arrowstyle='->',color='#1A237E',lw=0.9),
            fontsize=6.5, ha='left', color='#1A237E', fontweight='bold')

# ── Giằng BTCT neo (Pi neo) ───────────────────────────────────────────────────
# Giằng ngang tại cao độ 1.0m
gang_y   = 1.0
gang_x1  = x_wall + 0.40   # liên kết vào cọc V100
gang_x2  = x_soil_R - 0.2  # kéo vào đất 3÷4m
gang_h   = 0.15             # 0.3m → thu nhỏ
gang_beam = Rectangle((gang_x1, gang_y-gang_h/2), gang_x2-gang_x1, gang_h,
                       facecolor='#D3D3D3', edgecolor='#555', lw=1.0,
                       hatch='..', alpha=0.85, zorder=4)
ax.add_patch(gang_beam)
# Thép trong giằng (điểm tròn nhỏ)
for xi in np.linspace(gang_x1+0.1, gang_x2-0.1, 4):
    for yi in [gang_y-gang_h*0.3, gang_y+gang_h*0.3]:
        dot = Circle((xi,yi), 0.015, facecolor='black', zorder=8)
        ax.add_patch(dot)

ax.annotate('Giằng BTCT NEO\n300×300mm / 4Φ12\nΦ6a300\nL≥3÷4m',
            xy=((gang_x1+gang_x2)/2, gang_y+gang_h/2),
            xytext=((gang_x1+gang_x2)/2, gang_y+0.5),
            arrowprops=dict(arrowstyle='->',color=C_ANCHOR,lw=0.9),
            fontsize=6.5, ha='center', color=C_ANCHOR, fontweight='bold')

# ── Đường kích thước ─────────────────────────────────────────────────────────
# Chiều cao tường buy (4 hàng)
dim_line(ax, x_soil_L+0.2, 0, x_soil_L+0.2, buy_row*buy_sp,
         f'H≈{buy_row*buy_sp:.2f}m\n(4 buy)', orient='v', text_off=-0.2, fs=7)
ax.plot([x_soil_L+0.12,x_soil_L+0.28],[0,0], color=C_DIM, lw=0.8)
ax.plot([x_soil_L+0.12,x_soil_L+0.28],[buy_row*buy_sp,buy_row*buy_sp], color=C_DIM, lw=0.8)

# Đường kính buy
dim_line(ax, x_wall-buy_r, wall_top_y+0.25, x_wall+buy_r, wall_top_y+0.25,
         'Φ400', orient='h', text_off=0.10, fs=7)

# Chiều sâu cọc ngầm
dim_line(ax, x_wall+0.65, 0, x_wall+0.65, -V100_embed,
         'L=1.5÷2m\n(cắm đất)', orient='v', text_off=0.25, fs=6.5)

# Bước neo a=5÷7m (chiều vào)
dim_line(ax, gang_x1, gang_y-0.45, gang_x2, gang_y-0.45,
         'L≥3÷4m', orient='h', text_off=-0.12, fs=7)
ax.plot([gang_x1,gang_x1],[gang_y-0.40,gang_y-0.50],color=C_DIM,lw=0.8)
ax.plot([gang_x2,gang_x2],[gang_y-0.40,gang_y-0.50],color=C_DIM,lw=0.8)

# Ghi chú Pi neo a=5÷7m
ax.text(x_soil_R+0.05, gang_y, 'Pi neo\na=5÷7m', ha='left', va='center',
        color='#CC0000', fontsize=7, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2',facecolor='#FFF9C4',edgecolor='#CC0000',lw=0.8))

# Mực nước thiên nhiên
mwl_y = 0.7
ax.plot([x_soil_L, x_wall-0.22], [mwl_y, mwl_y], color='#0066CC', lw=1.0, ls='-.', alpha=0.8)
ax.text(x_soil_L+0.05, mwl_y+0.07, 'MN TN', color='#0066CC', fontsize=6.5, style='italic')

ax.set_xlim(x_soil_L-0.15, x_soil_R+0.5)
ax.set_ylim(-1.1, 2.5)
ax.axis('off')

# Mũi tên chú thích mặt cắt
ax.text(-0.95, 2.35, 'KÈ PHÍA SÔNG  ←', ha='center', color='#0066CC',
        fontsize=8, fontweight='bold')
ax.text(2.0, 2.35, '→  PHÍA ĐẤT', ha='center', color='#6B4C00',
        fontsize=8, fontweight='bold')

# ════════════════════════════════════════════════════════════════════════════
# PANEL 2 — CHI TIẾT GIẰNG BTCT NEO (Cross-section)
# ════════════════════════════════════════════════════════════════════════════
ax = ax2
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title('CHI TIẾT GIẰNG BTCT NEO\n300×300mm — Tỷ lệ 1:10', fontsize=9,
             fontweight='bold', color=C_TITLE, pad=6)

# Tiết diện 300×300 → vẽ tỷ lệ 1m = 1 unit
s = 1.0   # scale 300mm → 1.0 unit
cx0, cy0 = 0, 0

# BTCT
btct = Rectangle((-s/2, -s/2), s, s, facecolor='#D3D3D3', edgecolor='#444',
                 lw=1.5, hatch='..', zorder=2)
ax.add_patch(btct)

# Lớp bảo vệ (30mm → 0.1 unit)
cover = 0.10
# 4Φ12 tại 4 góc
rebar_pos = [(-s/2+cover, -s/2+cover),
             ( s/2-cover, -s/2+cover),
             ( s/2-cover,  s/2-cover),
             (-s/2+cover,  s/2-cover)]
for (rx,ry) in rebar_pos:
    rb = Circle((rx,ry), 0.04, facecolor='black', edgecolor='black', zorder=4)
    ax.add_patch(rb)

# Đai Φ6a300
stirrup = Rectangle((-s/2+cover-0.02, -s/2+cover-0.02),
                    s-2*(cover-0.02), s-2*(cover-0.02),
                    facecolor='none', edgecolor='#333', lw=1.2,
                    linestyle='--', zorder=3)
ax.add_patch(stirrup)

# Kích thước
dim_line(ax, -s/2, -s/2-0.18, s/2, -s/2-0.18, '300', orient='h', text_off=-0.08, fs=7.5)
ax.plot([-s/2,-s/2],[-s/2-0.13,-s/2-0.23],color=C_DIM,lw=0.8)
ax.plot([s/2,s/2],[-s/2-0.13,-s/2-0.23],color=C_DIM,lw=0.8)

dim_line(ax, s/2+0.18, -s/2, s/2+0.18, s/2, '300', orient='v', text_off=0.12, fs=7.5)
ax.plot([s/2+0.13,s/2+0.23],[-s/2,-s/2],color=C_DIM,lw=0.8)
ax.plot([s/2+0.13,s/2+0.23],[s/2,s/2],color=C_DIM,lw=0.8)

# Ghi chú thép
ax.annotate('4Φ12', xy=(-s/2+cover, -s/2+cover),
            xytext=(-s/2-0.28, -s/2+cover),
            arrowprops=dict(arrowstyle='->',color='black',lw=0.7),
            fontsize=7, ha='right', color='black')
ax.annotate('Φ6a300', xy=(s/2-cover, -s/2+cover+0.05),
            xytext=(s/2+0.28, -s/2+0.3),
            arrowprops=dict(arrowstyle='->',color='#333',lw=0.7),
            fontsize=7, ha='left', color='#333')
ax.annotate('a=30mm', xy=(-s/2, -s/2+cover),
            xytext=(-s/2-0.28, -s/2+cover+0.35),
            arrowprops=dict(arrowstyle='->',color=C_DIM,lw=0.7),
            fontsize=7, ha='right', color=C_DIM)

# Ghi chú chữ
ax.text(0, 0.05, 'BTCT\nB20', ha='center', va='center',
        fontsize=8, color='#333', fontweight='bold')

ax.set_xlim(-1.0, 1.2)
ax.set_ylim(-0.9, 0.9)
ax.axis('off')

# ════════════════════════════════════════════════════════════════════════════
# PANEL 3 — CHI TIẾT V50 + BẢNG VẬT LIỆU
# ════════════════════════════════════════════════════════════════════════════
ax = ax3
ax.set_facecolor(C_BG)
ax.set_title('CỤM NEO V50 & BẢNG VẬT LIỆU', fontsize=9,
             fontweight='bold', color=C_TITLE, pad=6)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# ── Chi tiết cụm V50 ─────────────────────────────────────────────────────────
# Vẽ chi tiết mặt cắt cụm neo V50
# Buy (nhìn từ trên xuống — mặt bằng)
buy_plan = Circle((2.5, 7.8), 0.9, facecolor=C_GROUT, edgecolor=C_CONCRETE,
                   linewidth=1.5, zorder=3)
buy_wall_plan = matplotlib.patches.Wedge((2.5,7.8), 0.9, 0, 360, width=0.18,
                                          facecolor=C_CONCRETE, edgecolor='#555',
                                          linewidth=1.0, hatch='/', zorder=4)
ax.add_patch(buy_plan)
ax.add_patch(buy_wall_plan)

# V100 mặt bằng (chữ I)
v100_pts = np.array([[1.85,7.70],[2.15,7.70],[2.15,7.77],[2.02,7.77],
                      [2.02,7.83],[2.15,7.83],[2.15,7.90],[1.85,7.90],
                      [1.85,7.83],[1.98,7.83],[1.98,7.77],[1.85,7.77]])
v100_poly = Polygon(v100_pts, facecolor='#2F4F4F', edgecolor='black', lw=0.7, zorder=5)
ax.add_patch(v100_poly)

# V50 ngang
v50 = Rectangle((3.4, 7.73), 1.0, 0.14, facecolor='#1A237E', edgecolor='black',
                 lw=0.7, zorder=5)
ax.add_patch(v50)

# Kích thước 108×100
ax.annotate('', xy=(1.85,7.60), xytext=(2.15,7.60),
            arrowprops=dict(arrowstyle='<->',color=C_DIM,lw=0.9,mutation_scale=8))
ax.text(2.0, 7.54, '108', ha='center', color=C_DIM, fontsize=6.5, fontweight='bold')

ax.annotate('', xy=(1.78,7.70), xytext=(1.78,7.90),
            arrowprops=dict(arrowstyle='<->',color=C_DIM,lw=0.9,mutation_scale=8))
ax.text(1.60, 7.80, '100', ha='center', color=C_DIM, fontsize=6.5, fontweight='bold',
        rotation=90)

# Ghi chú
ax.text(2.5, 6.80, 'Mặt bằng: Cụm neo V50\ntrên cọc V100 (108×100mm)',
        ha='center', fontsize=6.5, color='#333', style='italic')

ax.annotate('V50\n(100×100)', xy=(4.4,7.80),
            xytext=(5.0,7.40),
            arrowprops=dict(arrowstyle='->',color='#1A237E',lw=0.7),
            fontsize=6.5, ha='left', color='#1A237E')

ax.annotate('Cọc V100', xy=(1.85,7.80),
            xytext=(0.3,7.40),
            arrowprops=dict(arrowstyle='->',color='#2F4F4F',lw=0.7),
            fontsize=6.5, ha='left', color='#2F4F4F')

ax.annotate('Buy Φ400\n(BTCT đúc sẵn)', xy=(2.5+0.9*0.7,7.8+0.9*0.7),
            xytext=(5.2,9.0),
            arrowprops=dict(arrowstyle='->',color='#666',lw=0.7),
            fontsize=6.5, ha='left', color='#666')

# ── Bảng vật liệu / dự toán sơ bộ ───────────────────────────────────────────
ax.text(0, 6.3, 'BẢNG VẬT LIỆU CHÍNH (Cho 1m dài kè)', fontsize=8,
        fontweight='bold', color=C_TITLE, va='top')

col_hdrs = ['Vật liệu', 'Q.cách', 'SL/m dài', 'Đơn vị']
col_xs   = [0.0, 3.0, 6.2, 8.0]
col_ws   = [3.0, 3.2, 1.8, 1.8]
rows_mat = [
    ('Buy BTCT đúc sẵn',  'Φ400',        '4.0',   'viên'),
    ('Vữa XM trong buy',  'M100 1bag/buy','4.0',   'bao 50kg'),
    ('Cọc thép V100',     'L=6m',         '0.25',  'cây/m'),
    ('Thép V50 ngang',    '100×100mm',    '0.5',   'm/m'),
    ('Giằng BTCT',        '300×300 B20', '0.14',   'm³/m'),
    ('Thép giằng 4Φ12',  'CB300-V',      '0.33',  'kg/m'),
    ('Vải ĐKT',           '0.4×2.4m',    '0.4',   'm²/m'),
    ('Vữa lót đáy',       'M75',          '0.05',  'm³/m'),
]

y_start = 6.0
row_h   = 0.42
# Header
for j,(h,x,w) in enumerate(zip(col_hdrs, col_xs, col_ws)):
    rb = FancyBboxPatch((x, y_start-row_h), w-0.05, row_h,
                         boxstyle='square,pad=0', facecolor=C_TITLE,
                         edgecolor='#AAAAAA', lw=0.4, zorder=2)
    ax.add_patch(rb)
    ax.text(x+0.08, y_start-row_h/2, h, va='center', fontsize=6.5,
            fontweight='bold', color='white')
# Data
for i,row in enumerate(rows_mat):
    yr = y_start - (i+1)*row_h - row_h
    bg = '#EAF1FB' if i%2==0 else 'white'
    for j,(cell,x,w) in enumerate(zip(row, col_xs, col_ws)):
        rb = FancyBboxPatch((x, yr), w-0.05, row_h,
                             boxstyle='square,pad=0', facecolor=bg,
                             edgecolor='#BBBBBB', lw=0.3, zorder=2)
        ax.add_patch(rb)
        ax.text(x+0.08, yr+row_h/2, cell, va='center', fontsize=6.3, color='#1A1A1A',
                ha='center' if j>0 else 'left')

# ════════════════════════════════════════════════════════════════════════════
# TITLE BLOCK
# ════════════════════════════════════════════════════════════════════════════
fig.text(0.5, 0.975, 'BẢN VẼ KỸ THUẬT CHI TIẾT — KÈ PI GIẾNG (KÈ BUY BTCT)',
         ha='center', va='top', fontsize=13, fontweight='bold', color='white',
         bbox=dict(boxstyle='square,pad=0.2', facecolor=C_TITLE, edgecolor='none'))
fig.text(0.5, 0.955, 'Phương án Nhà Thầu Tấn Khoa — Phân Đoạn C  |  'f'Ngày: {date.today().strftime("%d/%m/%Y")}',
         ha='center', va='top', fontsize=10, color=C_TITLE, fontweight='bold')
fig.text(0.5, 0.935, 'Tiêu chuẩn: TCVN 4116:1985 · TCVN 9902:2016 · TCVN 5574:2018',
         ha='center', va='top', fontsize=8.5, color='#555555', style='italic')
fig.add_artist(plt.Line2D([0.03,0.97],[0.895,0.895],transform=fig.transFigure,
               color=C_TITLE, lw=1.5))
fig.text(0.5, 0.055,
         'KÝ HIỆU: KC-PI-01  |  TỶ LỆ: 1:25 & 1:10  |  '
         'TIÊU CHUẨN: TCVN 9902:2016 / TCVN 5574:2018  |  NGƯỜI VẼ: AI Technical Illustrator',
         ha='center', va='bottom', fontsize=7, color='#333',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#F0F4FA', edgecolor=C_TITLE, lw=1.0))
fig.add_artist(plt.Line2D([0.03,0.97],[0.10,0.10],transform=fig.transFigure,
               color=C_TITLE, lw=1.0))

# ── Lưu ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--out', default=r'G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI\ke_pi_gieng_technical_drawing.png')
args = parser.parse_args()
os.makedirs(os.path.dirname(args.out), exist_ok=True)
fig.savefig(args.out, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"[OK] Da luu: {args.out}")
