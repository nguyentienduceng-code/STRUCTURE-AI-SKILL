
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
draw_ke_buy_dung.py — Bản Vẽ So Sánh: BUY ĐỨNG DỌC (Cọc Vây) vs BUY NẰM NGANG (Phương án TK)
Phân tích sai lệch thi công — NCR Review
"""
import sys, os, argparse
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon, Arc, Wedge
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import date

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,
                     'axes.linewidth':0.8,'axes.titlesize':9,'axes.titleweight':'bold'})

C_CONCRETE = '#AAAAAA'
C_STEEL    = '#2F2F2F'
C_SOIL     = '#C4A265'
C_WATER    = '#5B9BD5'
C_GEO      = '#4CAF50'
C_DIM      = '#1A1A8C'
C_RED      = '#CC0000'
C_GREEN    = '#1B5E20'
C_ORANGE   = '#E65100'
C_TITLE    = '#1C3557'
C_BG       = '#F9F9F9'
C_GROUT    = '#D8D0B8'

def dim_line(ax,x1,y1,x2,y2,label,text_off=0,orient='h',fs=7,color=C_DIM):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),
                arrowprops=dict(arrowstyle='<->',color=color,lw=0.9,mutation_scale=8))
    mx=(x1+x2)/2+(text_off if orient=='v' else 0)
    my=(y1+y2)/2+(text_off if orient=='h' else 0)
    ax.text(mx,my,label,ha='center',va='center',color=color,fontsize=fs,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1',facecolor='white',edgecolor='none',alpha=0.9))

@with_error_handling
def draw_buy_circle(ax, cx, cy, r=0.20, wall_t=0.04, fill_color=C_GROUT):
    """Buy tròn BTCT — mặt cắt ngang"""
    outer = Circle((cx,cy), r, facecolor=fill_color, edgecolor='#555', linewidth=0.8, zorder=3)
    ax.add_patch(outer)
    ring = Wedge((cx,cy), r, 0, 360, width=wall_t,
                 facecolor=C_CONCRETE, edgecolor='#444', linewidth=1.0, hatch='/', alpha=0.85, zorder=4)
    ax.add_patch(ring)

@with_error_handling
def draw_buy_vertical_side(ax, cx, y_top, y_bottom, r=0.20, wall_t=0.04):
    """Buy đứng dọc — nhìn mặt trước (hình chữ nhật)"""
    # Thành ngoài
    rect = Rectangle((cx-r, y_bottom), 2*r, y_top-y_bottom,
                      facecolor=C_GROUT, edgecolor='#555', linewidth=1.0, zorder=3)
    ax.add_patch(rect)
    # Vách BTCT hai bên
    left  = Rectangle((cx-r, y_bottom), wall_t, y_top-y_bottom,
                       facecolor=C_CONCRETE, edgecolor='#444', linewidth=0.5, hatch='/', alpha=0.8, zorder=4)
    right = Rectangle((cx+r-wall_t, y_bottom), wall_t, y_top-y_bottom,
                       facecolor=C_CONCRETE, edgecolor='#444', linewidth=0.5, hatch='/', alpha=0.8, zorder=4)
    ax.add_patch(left); ax.add_patch(right)

# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16.54,11.69))
fig.patch.set_facecolor('white')
gs = GridSpec(2,3,figure=fig,left=0.04,right=0.97,top=0.88,bottom=0.11,
              wspace=0.42,hspace=0.52)

ax1 = fig.add_subplot(gs[:,0])    # THỰC TẾ: Buy đứng — mặt cắt đứng
ax2 = fig.add_subplot(gs[:,1])    # THIẾT KẾ: Buy nằm — mặt cắt đứng
ax3 = fig.add_subplot(gs[0,2])    # Mặt bằng cọc vây (plan view)
ax4 = fig.add_subplot(gs[1,2])    # Bảng so sánh NCR

# ════════════════════════════════════════════════════════════════════════════
# PANEL 1 — THỰC TẾ: BUY ĐỨNG DỌC (Cọc Vây)
# ════════════════════════════════════════════════════════════════════════════
ax = ax1
ax.set_facecolor('#FFF8F0')  # Nền cam nhạt — cảnh báo
ax.set_aspect('equal')
ax.set_title('THỰC TẾ THI CÔNG\n(Buy đứng dọc — Dạng cọc vây tiếp xúc)', fontsize=8.5,
             fontweight='bold', color=C_RED, pad=6)

r_buy = 0.20
wall_t = 0.04

# Nước phía trước
water_patch = Rectangle((-1.5, -1.2), 1.4, 2.8, facecolor=C_WATER, alpha=0.20, zorder=0)
ax.add_patch(water_patch)
for wy in [-0.2, 0.0, 0.2]:
    wx = np.linspace(-1.5, -0.2, 25)
    wys = [wy + 0.02*np.sin(8*x*np.pi) for x in wx]
    ax.plot(wx, wys, color=C_WATER, lw=0.9, alpha=0.7)
ax.text(-0.85, 0.8, 'NƯỚC\nSÔNG', ha='center', color=C_WATER, fontsize=7, fontweight='bold')

# Đất nền
soil = Rectangle((-1.5,-1.2), 3.5, 1.2, facecolor=C_SOIL, edgecolor='#8B6914',
                  lw=0.5, alpha=0.5, zorder=1)
ax.add_patch(soil)
for xi in np.arange(-1.5, 2.0, 0.2):
    ax.plot([xi,xi+0.1],[-1.2,-1.0],color='#8B6914',lw=0.5,alpha=0.4)

# Mực nước kênh (MN TN)
ax.plot([-1.5, -0.2],[0.1, 0.1], color='#0066CC', lw=1.2, ls='-.', alpha=0.8)
ax.text(-1.4, 0.18, 'MN.TN', color='#0066CC', fontsize=6.5, style='italic')

# Buy đứng dọc — 3 buy kề nhau mặt nhìn
buy_cx_list = [-0.42, 0.0, 0.42]  # 3 buy, khoảng cách ~Φ
buy_top    = 1.6   # cao 1.6m so với đất
buy_bottom = -0.8  # cắm sâu ~0.8m dưới đáy (nếu có)

for i, cx in enumerate(buy_cx_list):
    draw_buy_vertical_side(ax, cx, buy_top, buy_bottom, r=r_buy, wall_t=wall_t)
    # Đường ngăn cách giữa các buy
    ax.plot([cx+r_buy, cx+r_buy],[buy_bottom,buy_top],
            color='#333', lw=1.5, zorder=6, alpha=0.7)

# Dầm đỉnh (capping beam)
cap_h = 0.20
cap_beam = Rectangle((-0.62, buy_top), 1.24, cap_h,
                      facecolor='#C0C0C0', edgecolor='#444', lw=1.5,
                      hatch='..', zorder=5)
ax.add_patch(cap_beam)
ax.text(0, buy_top+cap_h/2, 'DẦM ĐỈNH BTCT', ha='center', va='center',
        fontsize=6.5, color='#222', fontweight='bold')

# Rào thép trên đỉnh
for xi in [-0.5, -0.2, 0.1, 0.4]:
    ax.plot([xi, xi],[buy_top+cap_h, buy_top+cap_h+0.4],
            color='#555', lw=1.0, zorder=5)
ax.plot([-0.55, 0.5],[buy_top+cap_h+0.35, buy_top+cap_h+0.35],
        color='#555', lw=0.8, ls='--', alpha=0.7)
ax.text(0, buy_top+cap_h+0.5, 'Hàng rào thép', ha='center', fontsize=6, color='#555')

# VÙNG NGUY HIỂM — buy không cắm sâu đủ
danger_zone = Rectangle((-0.62, -0.8), 1.24, 0.8,
                          facecolor=C_RED, edgecolor=C_RED, lw=0.5, alpha=0.12, zorder=2)
ax.add_patch(danger_zone)
ax.text(0, -0.4, '⚠ CHIỀU SÂU\nCẮM BUY\nVÀO ĐẤT\nCHƯA RÕ', ha='center', va='center',
        fontsize=6.5, color=C_RED, fontweight='bold')

# Kích thước
dim_line(ax, -0.62, buy_bottom-0.25, 0.62, buy_bottom-0.25, 'B=3×Φ400=1.26m',
         orient='h', text_off=-0.1, fs=6.5)
dim_line(ax, 0.72, buy_bottom, 0.72, buy_top, 'H≈2.4m',
         orient='v', text_off=0.18, fs=7)
dim_line(ax, 0.72, 0.0, 0.72, buy_top, 'H phần nổi\n≈1.6m',
         orient='v', text_off=0.22, fs=6.5, color='#CC0000')
dim_line(ax, 0.72, buy_bottom, 0.72, 0.0, 'H phần ngầm\n≈0.8m???',
         orient='v', text_off=0.22, fs=6.5, color='#CC0000')

# ĐỘ SÂU CHÔN BUY — Cảnh báo
ax.annotate('BUY KHÔNG CÓ\nMŨI CỌC!\nDễ bị nhổ bật', xy=(0.22,-0.4),
            xytext=(1.0,-0.1),
            arrowprops=dict(arrowstyle='->',color=C_RED,lw=1.0),
            fontsize=7, color=C_RED, fontweight='bold', ha='left',
            bbox=dict(boxstyle='round,pad=0.2',facecolor='#FFEBEE',edgecolor=C_RED,lw=0.8))

# Thiếu cọc V100
ax.text(0, -0.9, '✗  Không thấy cọc thép V100 neo giữ', ha='center',
        fontsize=7, color=C_RED, fontweight='bold')
ax.text(0, -1.05, '✗  Không có giằng BTCT Pi neo phía sau', ha='center',
        fontsize=7, color=C_RED, fontweight='bold')

ax.set_xlim(-1.65, 1.5)
ax.set_ylim(-1.35, 2.4)
ax.axis('off')

# Viền đỏ cảnh báo
for spine in ['top','bottom','left','right']:
    ax.spines[spine].set_visible(False)
ax.patch.set_edgecolor(C_RED)
ax.patch.set_linewidth(2.5)

# Nhãn góc
ax.text(-1.60, 2.25, '⚠ SAI', fontsize=16, color=C_RED, fontweight='black',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEBEE', edgecolor=C_RED, lw=2.0))


# ════════════════════════════════════════════════════════════════════════════
# PANEL 2 — THIẾT KẾ: BUY NẰM NGANG (xếp chồng)
# ════════════════════════════════════════════════════════════════════════════
ax = ax2
ax.set_facecolor('#F0FFF4')  # Nền xanh nhạt — đúng thiết kế
ax.set_aspect('equal')
ax.set_title('THIẾT KẾ GỐC\n(Buy nằm ngang — Xếp chồng + Cọc V100 + Giằng neo)', fontsize=8.5,
             fontweight='bold', color=C_GREEN, pad=6)

# Nước
water2 = Rectangle((-1.5,-0.9), 1.3, 2.5, facecolor=C_WATER, alpha=0.20, zorder=0)
ax.add_patch(water2)
for wy in [-0.3, 0.0, 0.3, 0.6]:
    wx2 = np.linspace(-1.5,-0.25,25)
    wys2 = [wy+0.02*np.sin(8*x*np.pi) for x in wx2]
    ax.plot(wx2,wys2,color=C_WATER,lw=0.9,alpha=0.7)
ax.text(-0.87,0.9,'NƯỚC\nSÔNG',ha='center',color=C_WATER,fontsize=7,fontweight='bold')

# Đất nền
soil2 = Rectangle((-1.5,-0.9),3.5,0.9,facecolor=C_SOIL,edgecolor='#8B6914',lw=0.5,alpha=0.5,zorder=1)
ax.add_patch(soil2)

# MN TN
ax.plot([-1.5,-0.22],[0.15,0.15],color='#0066CC',lw=1.2,ls='-.',alpha=0.8)
ax.text(-1.4,0.22,'MN.TN',color='#0066CC',fontsize=6.5,style='italic')

# 4 hàng buy nằm ngang
buy_sp2 = 0.42
for row in range(4):
    cy = row * buy_sp2 + r_buy
    draw_buy_circle(ax, 0.0, cy, r=r_buy, wall_t=wall_t, fill_color=C_GROUT)
    if row == 1:
        ax.annotate('Buy nằm ngang\n(4 hàng xếp chồng)',
                    xy=(r_buy, cy),
                    xytext=(0.6, cy+0.3),
                    arrowprops=dict(arrowstyle='->',color='#333',lw=0.7),
                    fontsize=6.5, ha='left', color='#333')

# Vữa trong lòng buy
ax.text(0, r_buy, 'Vữa XM\n1 bao/buy', ha='center', va='center',
        fontsize=5.5, color='#555', style='italic')

# Cọc thép V100
coc_x = 0.45
ax.plot([coc_x, coc_x],[-0.8, 4*buy_sp2+0.3],
        color=C_STEEL, lw=3.0, zorder=7, solid_capstyle='round')
ax.text(coc_x+0.05, 2*buy_sp2+r_buy, 'Cọc V100\nL=6m',
        ha='left', va='center', fontsize=6.5, color=C_STEEL, fontweight='bold')

# Giằng BTCT neo
gang_y = buy_sp2*2
ax.add_patch(Rectangle((coc_x-0.01, gang_y-0.07), 1.8, 0.14,
                         facecolor='#D3D3D3', edgecolor='#555', lw=0.8, hatch='..', zorder=5))
ax.text(coc_x+0.9, gang_y+0.12, 'Giằng BTCT Neo\n300×300 / L≥3÷4m',
        ha='center', va='bottom', fontsize=6, color=C_ORANGE, fontweight='bold')

# V50 frame
ax.plot([0.22, coc_x],[gang_y, gang_y],color='#1A237E',lw=2.5,zorder=6)
ax.text(0.32, gang_y+0.07, 'Cụm V50\n(100×100)',ha='center',fontsize=5.5,color='#1A237E')

# Vải ĐKT
ax.plot([0.22, 0.22],[0,1.5],color=C_GEO,lw=2.0,ls='--',alpha=0.8)
ax.plot([0.22, 1.8],[1.5,1.5],color=C_GEO,lw=2.0,ls='--',alpha=0.8)
ax.text(1.0, 1.6, 'Vải ĐKT', ha='center', color=C_GEO, fontsize=6)

# Vữa lót đáy
ax.add_patch(Rectangle((-0.22,-0.15),0.44,0.15,
                         facecolor='#E0D8C0',edgecolor='#888',lw=0.5,alpha=0.8,zorder=3))
ax.text(0,-0.07,'Vữa lót tạo phẳng',ha='center',va='center',fontsize=5.5,color='#555')

# Kích thước
dim_line(ax,-0.55,0,-0.55,4*buy_sp2,'H=1.68m\n(4 buy)',orient='v',text_off=-0.2,fs=7)

ax.set_xlim(-1.65,2.35)
ax.set_ylim(-1.1,2.4)
ax.axis('off')
ax.text(-1.60,2.25,'✅ ĐÚNG',fontsize=16,color=C_GREEN,fontweight='black',
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=2.0))


# ════════════════════════════════════════════════════════════════════════════
# PANEL 3 — MẶT BẰNG CỌC VÂY BUY ĐỨNG
# ════════════════════════════════════════════════════════════════════════════
ax = ax3
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title('MẶT BẰNG — Buy đứng dọc tiếp xúc\n(Kiểu Contiguous Pile Wall)', fontsize=8.5,
             fontweight='bold', color=C_RED, pad=6)

n_buy = 8
for i in range(n_buy):
    cx_plan = i * 2*r_buy
    # Buy tròn nhìn từ trên
    outer = Circle((cx_plan, 0), r_buy, facecolor=C_GROUT, edgecolor='#444', lw=1.0, zorder=3)
    ring  = Wedge((cx_plan,0), r_buy, 0, 360, width=wall_t,
                  facecolor=C_CONCRETE, edgecolor='#555', lw=0.5, hatch='/', alpha=0.8, zorder=4)
    ax.add_patch(outer); ax.add_patch(ring)

# Dầm đỉnh (mặt bằng)
cap_plan = Rectangle((-r_buy, -r_buy-0.08), n_buy*2*r_buy, 0.08,
                      facecolor='#BBBBBB', edgecolor='#333', lw=0.8, alpha=0.8, zorder=5)
ax.add_patch(cap_plan)
ax.text(n_buy*r_buy-r_buy, -r_buy-0.04, 'Dầm đỉnh', ha='center', va='center',
        fontsize=5.5, color='#333')

# Kích thước tổng
dim_line(ax, -r_buy, -r_buy-0.22, n_buy*2*r_buy-r_buy, -r_buy-0.22,
         f'{n_buy}×Φ400 = {n_buy*2*r_buy*1000:.0f}mm/cụm',
         orient='h', text_off=-0.1, fs=6.5)

# Khe hở giữa buy (vấn đề)
ax.annotate('KHE HỞ\ngiữa buy\n(nguy cơ\nxói đất)',
            xy=(2*r_buy, 0),
            xytext=(2*r_buy+0.05, 0.55),
            arrowprops=dict(arrowstyle='->',color=C_RED,lw=0.9),
            fontsize=6.5, ha='center', color=C_RED,
            bbox=dict(boxstyle='round,pad=0.2',facecolor='#FFEBEE',edgecolor=C_RED,lw=0.7))

# Ký hiệu phía nước
ax.text(n_buy*r_buy-r_buy, 0.6, '← PHÍA SÔNG', ha='center', color=C_WATER, fontsize=7)
ax.text(n_buy*r_buy-r_buy, -0.6, 'PHÍA ĐẤT →', ha='center', color='#8B6914', fontsize=7)

# Khe hở thực tế giữa buy
gap_xs = [r_buy*2*i + r_buy for i in range(n_buy-1)]
for gx in gap_xs:
    ax.plot(gx, 0, 'x', color=C_RED, ms=4, mew=1.5, zorder=7)

ax.set_xlim(-0.35, n_buy*2*r_buy+0.15)
ax.set_ylim(-0.55, 0.85)
ax.axis('off')


# ════════════════════════════════════════════════════════════════════════════
# PANEL 4 — BẢNG SO SÁNH NCR + PHÂN LOẠI
# ════════════════════════════════════════════════════════════════════════════
ax = ax4
ax.set_facecolor(C_BG)
ax.set_title('PHÂN LOẠI NCR & BẢNG SO SÁNH', fontsize=9, fontweight='bold', color=C_TITLE, pad=6)
ax.set_xlim(0,10); ax.set_ylim(0,10); ax.axis('off')

# NCR Header
ncr_box = FancyBboxPatch((0,8.5), 10, 1.3, boxstyle='round,pad=0.1',
                          facecolor=C_RED, edgecolor='none', zorder=2)
ax.add_patch(ncr_box)
ax.text(5, 9.15, 'NCR — MAJOR', ha='center', va='center',
        fontsize=11, fontweight='bold', color='white')
ax.text(5, 8.75, 'Sai lệch hướng thi công (Phương đứng vs Phương ngang)', ha='center',
        va='center', fontsize=7.5, color='white', style='italic')

# Bảng so sánh
headers = ['Tiêu chí', 'THIẾT KẾ (Buy ngang)', 'THỰC TẾ (Buy đứng)']
rows_cmp = [
    ('Phương đặt buy',  'Nằm ngang — xếp chồng 4 hàng',  'Đứng dọc — sát nhau'),
    ('Sơ đồ chịu lực',  'Tường trọng lực (Gravity wall)',  'Cọc vây tiếp xúc\n(Contiguous pile)'),
    ('Chiều sâu cắm',   'Vữa lót đáy + đất nền', 'Cắm sâu vào đất\n(chưa rõ chiều sâu)'),
    ('Cọc V100',        '✅ Bắt buộc mỗi 4 buy',  '❌ Không thấy'),
    ('Giằng Pi neo',    '✅ L≥3÷4m / bước 5÷7m',  '❌ Không thấy'),
    ('Dầm đỉnh',        '❌ Không có',            '✅ Có dầm đỉnh BTCT'),
    ('Vải ĐKT',         '✅ 0.4×2.4m phía sau',   '❓ Chưa xác nhận'),
    ('Khe hở tường',    'Kín (buy chồng lên nhau)','⚠ Có khe hở giữa buy'),
    ('Ổn định chống lật','Neo vào cọc V100+giằng', 'Phụ thuộc chiều sâu cắm'),
]
col_xs   = [0.0, 3.8, 7.2]
col_ws   = [3.8, 3.4, 2.8]
col_hdrs = headers
row_h = 0.62
y0    = 8.2

# Header
for j,(h,cw,cx) in enumerate(zip(col_hdrs,col_ws,col_xs)):
    rb = FancyBboxPatch((cx, y0-row_h*0.9), cw-0.08, row_h*0.85,
                         boxstyle='square,pad=0', facecolor=C_TITLE, edgecolor='#999', lw=0.4, zorder=2)
    ax.add_patch(rb)
    ax.text(cx+0.08, y0-row_h*0.45, h, va='center', fontsize=6.5,
            fontweight='bold', color='white')

for i,row in enumerate(rows_cmp):
    yr = y0 - (i+1)*row_h*0.85 - row_h*0.1
    # Màu hàng
    if '❌' in str(row[2]):
        bg2 = '#FFEBEE'
    elif '⚠' in str(row[2]) or '❓' in str(row[2]):
        bg2 = '#FFF8E1'
    else:
        bg2 = '#E8F5E9'
    bg1 = '#F5F5F5' if i%2==0 else 'white'

    for j,(cell,cw,cx) in enumerate(zip(row,col_ws,col_xs)):
        bg = bg2 if j==2 else bg1
        rb = FancyBboxPatch((cx, yr-row_h*0.78), cw-0.08, row_h*0.78,
                             boxstyle='square,pad=0', facecolor=bg, edgecolor='#CCC',
                             lw=0.3, zorder=2)
        ax.add_patch(rb)
        ax.text(cx+0.1, yr-row_h*0.39, str(cell), va='center',
                fontsize=6.0, color='#1A1A1A', ha='left' if j==0 else 'center')

# Kết luận
y_kl = y0 - len(rows_cmp)*row_h*0.85 - 0.6
ax.text(0, y_kl, 'PHÂN LOẠI: NCR MAJOR — Sai lệch phương thi công',
        fontsize=7.5, fontweight='bold', color=C_RED, va='top')
ax.text(0, y_kl-0.4,
        'YÊU CẦU XỬ LÝ trong 48h:\n'
        '1. Đo đạc chiều sâu cắm buy vào đất (min. 1.5D = 600mm)\n'
        '2. Xác nhận có/không có cọc thép V100 — nếu không phải bổ sung\n'
        '3. Kiểm tra khe hở giữa buy — cần bịt kín bằng vữa lấp\n'
        '4. Tính lại ổn định chống lật theo sơ đồ cọc vây mới',
        fontsize=6.5, va='top', color='#333',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor=C_ORANGE, lw=0.8))

# ════════════════════════════════════════════════════════════════════════════
# TITLE BLOCK
# ════════════════════════════════════════════════════════════════════════════
fig.text(0.5, 0.975, 'PHÂN TÍCH SAI LỆCH THI CÔNG — NCR REVIEW',
         ha='center', va='top', fontsize=13, fontweight='bold', color='white',
         bbox=dict(boxstyle='square,pad=0.2', facecolor=C_RED, edgecolor='none'))
fig.text(0.5, 0.955, 'KÈ PI GIẾNG — BUY ĐỨNG DỌC (Thực tế) vs BUY NẰM NGANG (Thiết kế gốc)',
         ha='center', va='top', fontsize=10, color=C_TITLE, fontweight='bold')
fig.text(0.5, 0.933, f'Ngày phát hiện: {date.today().strftime("%d/%m/%Y")}  |  '
         'Phân loại: NCR MAJOR  |  Phản hồi yêu cầu trong 48h',
         ha='center', va='top', fontsize=8.5, color=C_RED, style='italic', fontweight='bold')
fig.add_artist(plt.Line2D([0.03,0.97],[0.895,0.895],transform=fig.transFigure,
               color=C_RED, lw=2.0))
fig.text(0.5, 0.055,
         'KÝ HIỆU: NCR-PI-01  |  GIAI ĐOẠN: THI CÔNG  |  PHÂN LOẠI: MAJOR  |  '
         f'NGÀY: {date.today().strftime("%d/%m/%Y")}  |  AI Technical Reviewer',
         ha='center', va='bottom', fontsize=7, color='#333',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF3E0', edgecolor=C_RED, lw=1.0))
fig.add_artist(plt.Line2D([0.03,0.97],[0.10,0.10],transform=fig.transFigure,
               color=C_RED, lw=1.0))

# ── Lưu ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--out', default=r'G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI\NCR_ke_buy_dung_vs_thietke.png')
args = parser.parse_args()
os.makedirs(os.path.dirname(args.out), exist_ok=True)
fig.savefig(args.out, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"[OK] Da luu: {args.out}")
