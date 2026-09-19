
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
draw_tham_da.py — Bản Vẽ Kỹ Thuật Chi Tiết: THẢM ĐÁ (Gabion Mattress / Reno Mattress)
Thư viện: matplotlib, numpy
Output : PNG 300 DPI, 420×297mm (A3 ngang)
"""

import sys
import os
import argparse
import math

# ── Unicode Fix ──────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle, Polygon, FancyBboxPatch
import matplotlib.lines as mlines
import numpy as np

# ── Font cài đặt ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family'     : 'DejaVu Sans',
    'font.size'       : 8,
    'axes.linewidth'  : 0.8,
    'axes.titlesize'  : 9,
    'axes.titleweight': 'bold',
})

# ═══════════════════════════════════════════════════════════════════════════════
# THÔNG SỐ THẢM ĐÁ TIÊU CHUẨN
# Kích thước (mm): 4000 x 2000 x 300
# Lưới: Lục giác xoắn kép Φ2.7 mạ kẽm, mắt lưới 60x80mm
# Đá hộc: Φ100–200mm, cường độ ≥ 60 MPa
# ═══════════════════════════════════════════════════════════════════════════════

# Màu sắc hệ thống
C_WIRE    = '#4A4A4A'   # Lưới thép
C_STONE   = '#8B7355'   # Đá hộc (fill)
C_STONE_E = '#5C4A2A'   # Đá hộc (edge)
C_CONCRETE= '#C8C8C8'   # Bê tông
C_SOIL    = '#8B6914'   # Đất nền
C_DIM     = '#1A1A8C'   # Màu đường kích thước
C_RED     = '#CC0000'   # Màu chú thích quan trọng
C_WATER   = '#4A90D9'   # Màu nước
C_GRID_BG = '#F8F8F8'   # Nền grid nhạt
C_TITLE   = '#1C3557'   # Tiêu đề

def dim_line(ax, x1, y1, x2, y2, label, offset=0.2, color=C_DIM, fontsize=7.5,
             orient='h', text_offset=0.0):
    """Vẽ đường kích thước với mũi tên 2 đầu"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='<->', color=color,
                                lw=0.9, mutation_scale=8))
    mid_x = (x1 + x2) / 2 + (text_offset if orient == 'v' else 0)
    mid_y = (y1 + y2) / 2 + (text_offset if orient == 'h' else 0)
    ax.text(mid_x, mid_y, label, ha='center', va='center',
            color=color, fontsize=fontsize, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                      edgecolor='none', alpha=0.9))

def tick_line(ax, x, y1, y2, color=C_DIM, lw=0.7):
    ax.plot([x, x], [y1, y2], color=color, lw=lw)

@with_error_handling
def draw_wire_mesh_pattern(ax, x0, y0, width, height, color='#555555',
                           alpha=0.35, lw=0.4, mesh_w=0.08, mesh_h=0.06):
    """Vẽ pattern lưới lục giác đơn giản hóa bằng đường kẻ zig-zag"""
    # Kẻ đường ngang
    y = y0
    while y <= y0 + height:
        ax.plot([x0, x0 + width], [y, y], color=color, lw=lw, alpha=alpha)
        y += mesh_h
    # Kẻ đường chéo phải
    x = x0
    while x <= x0 + width + height:
        x_start = max(x0, x - height)
        x_end   = min(x0 + width, x)
        y_start = min(y0 + height, y0 + (x - x_start))
        y_end   = max(y0, y0 + height - (x_end - x0 + 1e-9))
        # Vẽ đường chéo
        ax.plot([x_start, x_end], [y0 + height - (x_start - max(x0, x - height)), 
                                    y0 + height - (x_end - max(x0, x - height))],
                color=color, lw=lw, alpha=alpha)
        x += mesh_w
    # Kẻ đường chéo trái
    x = x0
    while x <= x0 + width + height:
        ax.plot([], [], color=color, lw=lw, alpha=alpha)
        x += mesh_w

@with_error_handling
def draw_stones_in_cell(ax, x0, y0, width, height, n_stones=12, seed=42):
    """Vẽ đá hộc ngẫu nhiên trong ô thảm đá (mặt cắt)"""
    rng = np.random.default_rng(seed)
    margin = 0.02
    radii_pool = [0.04, 0.05, 0.06, 0.07, 0.08, 0.045, 0.055]
    # Lọc radii phù hợp với kích thước ô
    max_r = min(width, height) / 2 - margin - 0.005
    radii_pool = [r for r in radii_pool if r <= max_r]
    if not radii_pool:
        radii_pool = [max_r * 0.8]
    placed = []
    attempts = 0
    while len(placed) < n_stones and attempts < 500:
        r = float(rng.choice(radii_pool))
        lo_x = x0 + margin + r
        hi_x = x0 + width - margin - r
        lo_y = y0 + margin + r
        hi_y = y0 + height - margin - r
        if hi_x <= lo_x or hi_y <= lo_y:
            attempts += 1
            continue
        cx = rng.uniform(lo_x, hi_x)
        cy = rng.uniform(lo_y, hi_y)
        # Kiểm tra không chồng lên nhau
        ok = True
        for (px, py, pr) in placed:
            if math.hypot(cx - px, cy - py) < r + pr + 0.01:
                ok = False
                break
        if ok:
            # Vẽ đá hộc dạng đa giác bất quy tắc
            n_sides = rng.integers(6, 10)
            angles = np.sort(rng.uniform(0, 2 * np.pi, n_sides))
            rx = r * rng.uniform(0.85, 1.15, n_sides)
            ry = r * rng.uniform(0.75, 1.05, n_sides)
            xs = cx + rx * np.cos(angles)
            ys = cy + ry * np.sin(angles)
            poly = Polygon(list(zip(xs, ys)),
                           facecolor=C_STONE,
                           edgecolor=C_STONE_E,
                           linewidth=0.6, alpha=0.88)
            ax.add_patch(poly)
            placed.append((cx, cy, r))
        attempts += 1

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE CHÍNH: A3 Ngang
# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16.54, 11.69))  # A3 in inch
fig.patch.set_facecolor('white')

# ── Lưới layout: 2 hàng × 3 cột ─────────────────────────────────────────────
from matplotlib.gridspec import GridSpec
gs = GridSpec(2, 3, figure=fig,
              left=0.05, right=0.97,
              top=0.88, bottom=0.12,
              wspace=0.35, hspace=0.50)

ax1 = fig.add_subplot(gs[0, :2])   # Hàng trên, 2 cột: Mặt bằng
ax2 = fig.add_subplot(gs[1, :2])   # Hàng dưới, 2 cột: Mặt cắt dọc A-A
ax3 = fig.add_subplot(gs[0, 2])    # Hàng trên, cột 3: Mặt cắt ngang B-B
ax4 = fig.add_subplot(gs[1, 2])    # Hàng dưới, cột 3: Chi tiết lưới + ghi chú


# ════════════════════════════════════════════════════════════════════════════
# PANEL 1 — MẶT BẰNG (Plan View) — Tỷ lệ 1:50
# ════════════════════════════════════════════════════════════════════════════
ax = ax1
ax.set_facecolor(C_GRID_BG)
ax.set_aspect('equal')
ax.set_title('MẶT BẰNG — THẢM ĐÁ   (Tỷ lệ 1:50)', fontsize=9, fontweight='bold',
             color=C_TITLE, pad=6)

# Kích thước vẽ (đơn vị: m, scale 1:50)
L = 4.0   # Dài 4m
W = 2.0   # Rộng 2m
H = 0.30  # Cao 0.3m

# Viền ngoài
outer = Rectangle((0, 0), L, W, linewidth=2.0, edgecolor=C_WIRE,
                   facecolor='#E8E4DC', zorder=2)
ax.add_patch(outer)

# Vách ngăn (3 vách chia 4 ô) — cách nhau 1m
for i in [1, 2, 3]:
    ax.plot([i, i], [0, W], color=C_WIRE, lw=1.8, zorder=3)

# Dây buộc nắp (spiral ties) — ký hiệu × tại các góc ô
for xi in [0.5, 1.5, 2.5, 3.5]:
    for yi in [0.25, 0.75, 1.25, 1.75]:
        ax.plot(xi, yi, 'x', color=C_WIRE, ms=4, mew=0.8, alpha=0.6, zorder=4)

# Pattern lưới (tự vẽ đơn giản)
for xi in np.arange(0, L, 0.10):
    ax.plot([xi, xi], [0, W], color='#777777', lw=0.25, alpha=0.3, zorder=1)
for yi in np.arange(0, W, 0.08):
    ax.plot([0, L], [yi, yi], color='#777777', lw=0.25, alpha=0.3, zorder=1)

# Nhãn ô
for i, label in enumerate(['Ô 1', 'Ô 2', 'Ô 3', 'Ô 4']):
    ax.text(i + 0.5, W/2, label, ha='center', va='center',
            fontsize=7.5, color='#333333', alpha=0.7, zorder=5)

# Vị trí cắt A-A và B-B
# A-A (dọc, qua giữa)
ax.plot([-0.4, L+0.4], [W/2, W/2], color=C_RED, lw=0.8, ls='--', zorder=6)
ax.text(-0.5, W/2, 'A', ha='center', va='center', color=C_RED, fontsize=9, fontweight='bold')
ax.text(L+0.5, W/2, "A'", ha='center', va='center', color=C_RED, fontsize=9, fontweight='bold')

# B-B (ngang, qua giữa)
ax.plot([L/2, L/2], [-0.3, W+0.3], color='#006600', lw=0.8, ls='--', zorder=6)
ax.text(L/2, -0.45, 'B', ha='center', va='center', color='#006600', fontsize=9, fontweight='bold')
ax.text(L/2, W+0.4, "B'", ha='center', va='center', color='#006600', fontsize=9, fontweight='bold')

# ── Đường kích thước ─────────────────────────────────────────────────────────
# Chiều dài tổng
dim_line(ax, 0, -0.25, L, -0.25, 'L = 4000 mm', offset=0.12, orient='h', text_offset=-0.1)
ax.plot([0, 0], [-0.25-0.08, -0.25+0.08], color=C_DIM, lw=0.8)
ax.plot([L, L], [-0.25-0.08, -0.25+0.08], color=C_DIM, lw=0.8)

# Khoảng cách vách ngăn
for xi in [0, 1, 2, 3]:
    dim_line(ax, xi, W+0.2, xi+1, W+0.2, '1000', orient='h', text_offset=0.1, fontsize=6.5)
    ax.plot([xi, xi], [W+0.12, W+0.28], color=C_DIM, lw=0.7)
ax.plot([4, 4], [W+0.12, W+0.28], color=C_DIM, lw=0.7)

# Chiều rộng
dim_line(ax, -0.35, 0, -0.35, W, 'B = 2000 mm', orient='v', text_offset=-0.1)
ax.plot([-0.35-0.07, -0.35+0.07], [0, 0], color=C_DIM, lw=0.8)
ax.plot([-0.35-0.07, -0.35+0.07], [W, W], color=C_DIM, lw=0.8)

ax.set_xlim(-0.7, 5.0)
ax.set_ylim(-0.6, 2.8)
ax.axis('off')

# Ghi chú panel
ax.text(L/2, -0.55, 'Ghi chú: Vách ngăn cách đều 1m (4 ô/thảm). Dây liên kết Φ2.2 mạ kẽm.',
        ha='center', va='top', fontsize=6.5, color='#444444', style='italic')


# ════════════════════════════════════════════════════════════════════════════
# PANEL 2 — MẶT CẮT DỌC A-A (Longitudinal Section)
# ════════════════════════════════════════════════════════════════════════════
ax = ax2
ax.set_facecolor(C_GRID_BG)
ax.set_aspect('equal')
ax.set_title('MẶT CẮT DỌC A-A   (Tỷ lệ 1:50)', fontsize=9, fontweight='bold',
             color=C_TITLE, pad=6)

# Đất nền
soil = Rectangle((-0.3, -0.25), L+0.6, 0.25, facecolor='#B8860B',
                  edgecolor='#8B6914', lw=0.8, alpha=0.5)
ax.add_patch(soil)
for xi in np.arange(-0.3, L+0.3, 0.15):
    ax.plot([xi, xi+0.08], [-0.25, -0.05], color='#8B6914', lw=0.6, alpha=0.4)

# Thảm đá: khung ngoài
frame = Rectangle((0, 0), L, H, linewidth=2.0, edgecolor=C_WIRE,
                   facecolor='none', zorder=3)
ax.add_patch(frame)

# Đáy và nắp — lưới hatch
bottom_mesh = Rectangle((0, 0), L, 0.02, linewidth=0.5, edgecolor=C_WIRE,
                          facecolor='#888888', zorder=4, alpha=0.5)
ax.add_patch(bottom_mesh)
top_mesh = Rectangle((0, H-0.02), L, 0.02, linewidth=0.5, edgecolor=C_WIRE,
                       facecolor='#888888', zorder=4, alpha=0.5)
ax.add_patch(top_mesh)

# Đá hộc trong thảm
for i in range(4):
    draw_stones_in_cell(ax, i*1.0 + 0.02, 0.02, 0.96, H-0.04,
                         n_stones=8, seed=i*17+5)

# Vách ngăn
for xi in [1, 2, 3]:
    vach = Rectangle((xi-0.015, 0), 0.03, H, linewidth=1.0, edgecolor=C_WIRE,
                      facecolor='#AAAAAA', zorder=5, alpha=0.7)
    ax.add_patch(vach)

# ── Kích thước ─────────────────────────────────────────────────────────────
# Tổng chiều dài
dim_line(ax, 0, -0.38, L, -0.38, 'L = 4000 mm', orient='h', text_offset=-0.12)
ax.plot([0, 0], [-0.38-0.06, -0.38+0.06], color=C_DIM, lw=0.8)
ax.plot([L, L], [-0.38-0.06, -0.38+0.06], color=C_DIM, lw=0.8)

# Từng ô 1m
for xi in range(4):
    dim_line(ax, xi, H+0.12, xi+1, H+0.12, '1000', orient='h', text_offset=0.08, fontsize=6.5)
    ax.plot([xi, xi], [H+0.05, H+0.19], color=C_DIM, lw=0.7)
ax.plot([4, 4], [H+0.05, H+0.19], color=C_DIM, lw=0.7)

# Chiều cao
dim_line(ax, L+0.2, 0, L+0.2, H, 'H = 300', orient='v', text_offset=0.15)
ax.plot([L+0.13, L+0.27], [0, 0], color=C_DIM, lw=0.8)
ax.plot([L+0.13, L+0.27], [H, H], color=C_DIM, lw=0.8)

# Mũi tên A-A
ax.annotate('A', xy=(0, H/2), xytext=(-0.4, H/2),
            arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.0),
            color=C_RED, fontsize=9, fontweight='bold', va='center')
ax.annotate("A'", xy=(L, H/2), xytext=(L+0.35, H/2),
            arrowprops=dict(arrowstyle='<-', color=C_RED, lw=1.0),
            color=C_RED, fontsize=9, fontweight='bold', va='center')

# Chú thích đất nền
ax.text(L/2, -0.12, '  Đất nền', ha='center', va='center',
        fontsize=7, color='#6B4C00', style='italic')

# Chú thích vách ngăn
ax.annotate('Vách ngăn\n(Diaphragm)', xy=(2.0, H*0.8),
            xytext=(2.6, H+0.28),
            arrowprops=dict(arrowstyle='->', color='#333333', lw=0.8),
            fontsize=6.5, ha='center', color='#333333')

# Chú thích đá hộc
ax.annotate('Đá hộc Φ100÷200', xy=(0.5, H*0.5),
            xytext=(-0.3, H+0.35),
            arrowprops=dict(arrowstyle='->', color='#333333', lw=0.8),
            fontsize=6.5, ha='center', color='#333333')

# Chú thích lưới
ax.annotate('Lưới thép mạ kẽm\nxoắn kép Φ2.7', xy=(2.0, H),
            xytext=(1.4, H+0.42),
            arrowprops=dict(arrowstyle='->', color=C_WIRE, lw=0.8),
            fontsize=6.5, ha='center', color=C_WIRE)

ax.set_xlim(-0.6, 5.2)
ax.set_ylim(-0.55, 0.85)
ax.axis('off')

# Nước bên phải (biểu tượng)
water_x = [4.3, 4.35, 4.4, 4.45, 4.5, 4.55, 4.6, 4.65, 4.7]
for wy in [0.05, 0.12, 0.19]:
    water_ys = [wy + 0.015*np.sin(3*x*np.pi) for x in water_x]
    ax.plot(water_x, water_ys, color=C_WATER, lw=1.5, alpha=0.7)
ax.text(4.5, 0.22, 'Nước', ha='center', color=C_WATER, fontsize=7, style='italic')


# ════════════════════════════════════════════════════════════════════════════
# PANEL 3 — MẶT CẮT NGANG B-B (Cross Section)
# ════════════════════════════════════════════════════════════════════════════
ax = ax3
ax.set_facecolor(C_GRID_BG)
ax.set_aspect('equal')
ax.set_title('MẶT CẮT NGANG B-B\n(Tỷ lệ 1:25)', fontsize=9, fontweight='bold',
             color=C_TITLE, pad=6)

# Đất nền
soil3 = Rectangle((-0.3, -0.20), W+0.6, 0.20, facecolor='#B8860B',
                   edgecolor='#8B6914', lw=0.8, alpha=0.5)
ax.add_patch(soil3)
for xi in np.arange(-0.3, W+0.3, 0.12):
    ax.plot([xi, xi+0.07], [-0.20, -0.04], color='#8B6914', lw=0.6, alpha=0.4)

# Khung thảm đá (mặt cắt ngang: rộng 2m x cao 0.3m)
frame3 = Rectangle((0, 0), W, H, linewidth=2.0, edgecolor=C_WIRE,
                    facecolor='none', zorder=3)
ax.add_patch(frame3)

# Đáy lưới
bottom3 = Rectangle((0, 0), W, 0.02, linewidth=0.5, edgecolor=C_WIRE,
                      facecolor='#888888', zorder=4, alpha=0.5)
ax.add_patch(bottom3)
# Nắp lưới
top3 = Rectangle((0, H-0.02), W, 0.02, linewidth=0.5, edgecolor=C_WIRE,
                   facecolor='#888888', zorder=4, alpha=0.5)
ax.add_patch(top3)

# Đá hộc
draw_stones_in_cell(ax, 0.02, 0.02, W-0.04, H-0.04, n_stones=16, seed=99)

# Thành bên trái và phải (lưới dày hơn)
left_wall  = Rectangle((0, 0), 0.02, H, facecolor='#666666', edgecolor=C_WIRE, lw=0.5, zorder=4, alpha=0.6)
right_wall = Rectangle((W-0.02, 0), 0.02, H, facecolor='#666666', edgecolor=C_WIRE, lw=0.5, zorder=4, alpha=0.6)
ax.add_patch(left_wall)
ax.add_patch(right_wall)

# ── Kích thước ─────────────────────────────────────────────────────────────
# Chiều rộng
dim_line(ax, 0, -0.3, W, -0.3, 'B = 2000 mm', orient='h', text_offset=-0.1)
ax.plot([0, 0], [-0.3-0.05, -0.3+0.05], color=C_DIM, lw=0.8)
ax.plot([W, W], [-0.3-0.05, -0.3+0.05], color=C_DIM, lw=0.8)

# Chiều cao
dim_line(ax, W+0.2, 0, W+0.2, H, 'H = 300', orient='v', text_offset=0.12)
ax.plot([W+0.13, W+0.27], [0, 0], color=C_DIM, lw=0.8)
ax.plot([W+0.13, W+0.27], [H, H], color=C_DIM, lw=0.8)

# Mũi tên B-B
ax.text(-0.4, H/2 + 0.01, 'B', ha='center', va='bottom', color='#006600',
        fontsize=9, fontweight='bold')
ax.text(-0.4, H/2 - 0.01, '▲', ha='center', va='top', color='#006600', fontsize=7)
ax.text(W+0.5, H/2 + 0.01, "B'", ha='center', va='bottom', color='#006600',
        fontsize=9, fontweight='bold')

# Chú thích lưới thành
ax.annotate('Lưới thành\n(Side mesh)\nΦ2.7mm', xy=(0.01, H*0.5),
            xytext=(-0.35, H*0.8),
            arrowprops=dict(arrowstyle='->', color=C_WIRE, lw=0.7),
            fontsize=6, ha='center', color=C_WIRE)

# Chú thích dây buộc
ax.annotate('Dây xoắn\nbuộc nắp\nΦ2.2mm', xy=(W*0.3, H),
            xytext=(W*0.05, H+0.18),
            arrowprops=dict(arrowstyle='->', color='#444444', lw=0.7),
            fontsize=6, ha='center', color='#444444')

# Chú thích đáy lưới
ax.annotate('Lưới đáy\n(Bottom mesh)', xy=(W*0.6, 0.01),
            xytext=(W*0.7, -0.14),
            arrowprops=dict(arrowstyle='->', color='#444444', lw=0.7),
            fontsize=6, ha='center', color='#444444')

ax.set_xlim(-0.6, 2.85)
ax.set_ylim(-0.50, 0.80)
ax.axis('off')


# ════════════════════════════════════════════════════════════════════════════
# PANEL 4 — CHI TIẾT LƯỚI + BẢNG THÔNG SỐ KỸ THUẬT
# ════════════════════════════════════════════════════════════════════════════
ax = ax4
ax.set_facecolor(C_GRID_BG)
ax.set_title('CHI TIẾT LƯỚI & THÔNG SỐ KỸ THUẬT', fontsize=9, fontweight='bold',
             color=C_TITLE, pad=6)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# ── Vẽ chi tiết mắt lưới lục giác xoắn kép ──────────────────────────────
@with_error_handling
def draw_hex_mesh(ax, cx, cy, scale=0.8):
    """Vẽ 2 ô lưới lục giác để minh họa"""
    # Mắt lưới: 60mm × 80mm  →  vẽ đại diện
    w, h = 0.8 * scale, 0.6 * scale
    for dx in [0, w]:
        pts = np.array([
            [cx + dx,         cy + h*0.5],
            [cx + dx + w*0.2, cy + h],
            [cx + dx + w*0.8, cy + h],
            [cx + dx + w,     cy + h*0.5],
            [cx + dx + w*0.8, cy],
            [cx + dx + w*0.2, cy],
            [cx + dx,         cy + h*0.5],
        ])
        ax.plot(pts[:, 0], pts[:, 1], color=C_WIRE, lw=1.5, zorder=5)
    # Đường xoắn kép (giả lập bằng 2 đường song song gần nhau)
    for seg_y in [cy, cy + h*0.5, cy + h]:
        for dx in [0, w]:
            ax.plot([cx + dx + w*0.15, cx + dx + w*0.85],
                    [seg_y, seg_y],
                    color=C_WIRE, lw=0.8, alpha=0.5)

# Vẽ mắt lưới minh họa
draw_hex_mesh(ax, 0.5, 6.5, scale=1.0)

# Chú thích mắt lưới
ax.annotate('', xy=(0.5, 7.1), xytext=(2.3, 7.1),
            arrowprops=dict(arrowstyle='<->', color=C_DIM, lw=0.9, mutation_scale=8))
ax.text(1.4, 7.25, '80mm', ha='center', va='bottom', color=C_DIM, fontsize=7, fontweight='bold')

ax.annotate('', xy=(0.5, 6.5), xytext=(0.5, 7.1),
            arrowprops=dict(arrowstyle='<->', color=C_DIM, lw=0.9, mutation_scale=8))
ax.text(0.22, 6.8, '60mm', ha='right', va='center', color=C_DIM, fontsize=7, fontweight='bold',
        rotation=90)

ax.text(1.4, 6.1, '  Lưới lục giác xoắn kép\n  (Double-twisted hex mesh)', ha='center',
        fontsize=6.5, color='#333333', style='italic')

# Ghi chú dây thép
ax.annotate('Dây thép Φ2.7mm\nmạ kẽm ≥ 240g/m²', xy=(2.3, 7.1),
            xytext=(3.5, 7.5),
            arrowprops=dict(arrowstyle='->', color=C_WIRE, lw=0.7),
            fontsize=6, color=C_WIRE, ha='left')

# ── Bảng thông số kỹ thuật ───────────────────────────────────────────────
table_data = [
    ('THÔNG SỐ', 'GIÁ TRỊ', 'TIÊU CHUẨN'),
    ('Kích thước (D×R×H)', '4000×2000×300 mm', 'EN 10223-3'),
    ('Kích thước mắt lưới', '60 × 80 mm', 'EN 10223-3'),
    ('Đường kính dây lưới', 'Φ 2.7 mm', 'EN 10218-2'),
    ('Mạ kẽm dây lưới', '≥ 240 g/m²', 'EN 10244-2'),
    ('Dây biên (Edge wire)', 'Φ 3.4 mm', 'EN 10218-2'),
    ('Dây buộc (Tie wire)', 'Φ 2.2 mm', 'EN 10218-2'),
    ('Cấp thép dây', 'Thép carbon thấp', 'EN 10016'),
    ('Đá hộc (D hạt)', '100 ÷ 200 mm', 'TCVN 8219'),
    ('Cường độ đá', 'Rc ≥ 60 MPa', 'TCVN 7572'),
    ('Độ hao mòn đá', 'Los Angeles ≤ 35%', 'TCVN 7572'),
]

x0_t, y0_t = 0.0, 5.5
col_widths = [3.8, 3.6, 2.4]
row_h = 0.38

for row_idx, row in enumerate(table_data):
    y_row = y0_t - row_idx * row_h
    # Màu nền
    if row_idx == 0:
        bg = C_TITLE
        fc = 'white'
        fw = 'bold'
        fs = 7.5
    elif row_idx % 2 == 0:
        bg = '#DDE8F5'
        fc = '#1A1A1A'
        fw = 'normal'
        fs = 7
    else:
        bg = 'white'
        fc = '#1A1A1A'
        fw = 'normal'
        fs = 7

    x_col = x0_t
    for col_idx, (cell, cw) in enumerate(zip(row, col_widths)):
        rect = FancyBboxPatch((x_col, y_row - row_h), cw, row_h,
                               boxstyle='square,pad=0',
                               facecolor=bg, edgecolor='#AAAAAA', lw=0.5, zorder=2)
        ax.add_patch(rect)
        ax.text(x_col + 0.08, y_row - row_h/2, cell,
                ha='left', va='center', fontsize=fs, color=fc, fontweight=fw)
        x_col += cw

# ── Ghi chú áp dụng ──────────────────────────────────────────────────────
y_note = 5.5 - len(table_data) * row_h - 0.2
ax.text(0, y_note,
        '* Áp dụng theo: TCVN 8289:2009, EN 10223-3:2013\n'
        '* Bảo vệ chống ăn mòn: Mạ kẽm nóng hoặc PVC phủ ngoài\n'
        '* Dùng trong công trình: Gia cố bờ sông, đê biển, taluy mái đường',
        va='top', fontsize=6.5, color='#444444', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFFDE8',
                  edgecolor='#CCAA00', lw=0.7))

ax.set_xlim(-0.1, 10)
ax.set_ylim(-1.0, 10)


# ════════════════════════════════════════════════════════════════════════════
# TIÊU ĐỀ CHÍNH (TITLE BLOCK)
# ════════════════════════════════════════════════════════════════════════════
# Header band
fig.add_axes([0, 0.89, 1, 0.11]).axis('off')

# Tiêu đề lớn
fig.text(0.5, 0.975, 'BẢN VẼ KỸ THUẬT CHI TIẾT',
         ha='center', va='top', fontsize=14, fontweight='bold', color='white',
         bbox=dict(boxstyle='square,pad=0', facecolor=C_TITLE, edgecolor='none'))

fig.text(0.5, 0.955, 'THẢM ĐÁ  —  GABION MATTRESS / RENO MATTRESS',
         ha='center', va='top', fontsize=12, fontweight='bold', color=C_TITLE)

fig.text(0.5, 0.932, 'Ứng dụng: Gia cố bờ sông, bờ biển, taluy mái đường, chống xói lở',
         ha='center', va='top', fontsize=9, color='#555555', style='italic')

# Dải thông tin phía dưới (Title Block)
from datetime import date
today = date.today().strftime('%d/%m/%Y')
fig.text(0.5, 0.05,
         f'DỰ ÁN: Công trình gia cố bờ sông điển hình  |  HẠNG MỤC: Thảm đá bảo vệ taluy  |  '
         f'KÝ HIỆU: TD-01  |  TỶ LỆ: 1:50 & 1:25  |  NGÀY: {today}  |  '
         f'TIÊU CHUẨN: TCVN 8289:2009 / EN 10223-3:2013  |  NGƯỜI VẼ: AI Technical Illustrator',
         ha='center', va='bottom', fontsize=7, color='#333333',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#F0F4FA',
                   edgecolor='#1C3557', lw=1.0))

# Đường kẻ phân cách tiêu đề
fig.add_artist(plt.Line2D([0.03, 0.97], [0.895, 0.895],
                           transform=fig.transFigure, color=C_TITLE, lw=1.5))
fig.add_artist(plt.Line2D([0.03, 0.97], [0.10, 0.10],
                           transform=fig.transFigure, color=C_TITLE, lw=1.0))

# ════════════════════════════════════════════════════════════════════════════
# LƯU FILE
# ════════════════════════════════════════════════════════════════════════════
parser = argparse.ArgumentParser()
parser.add_argument('--out', default=r'G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI\tham_da_technical_drawing.png')
args = parser.parse_args()

out_path = args.out
os.makedirs(os.path.dirname(out_path), exist_ok=True)
fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white',
            metadata={'Title': 'Ban Ve Ky Thuat Tham Da', 'Author': 'AI Technical Illustrator'})
plt.close(fig)
print(f"[OK] Da luu ban ve: {out_path}")
