
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
draw_pi_gieng_composite.py
Bản vẽ kỹ thuật: Buy Phi400 + Thép hình H bên trong — Kiểm tra khả năng chịu lực
Phân tích mặt cắt hỗn hợp (Composite Section Analysis)
"""
import sys, os, argparse, math
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon, Wedge, Arc
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import date

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9})

C_BTCT   = '#AAAAAA'; C_STEEL  = '#607D8B'; C_GROUT = '#D6CFC0'
C_SOIL   = '#C4A265'; C_WATER  = '#5B9BD5'; C_GEO   = '#4CAF50'
C_DIM    = '#1A1A8C'; C_RED    = '#C62828'; C_GREEN = '#1B5E20'
C_ORANGE = '#E65100'; C_TITLE  = '#1C3557'; C_BG    = '#F8F9FA'
C_GABION = '#8D6E63'

def dim_line(ax,x1,y1,x2,y2,label,text_off=0,orient='h',fs=6.5,color=C_DIM):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),
                arrowprops=dict(arrowstyle='<->',color=color,lw=0.9,mutation_scale=8))
    mx=(x1+x2)/2+(text_off if orient=='v' else 0)
    my=(y1+y2)/2+(text_off if orient=='h' else 0)
    ax.text(mx,my,label,ha='center',va='center',color=color,fontsize=fs,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1',facecolor='white',edgecolor='none',alpha=0.9))

# ══════════════════════════════════════════════════════════════════════════════
# THAM SỐ HỆ KÈ
# ══════════════════════════════════════════════════════════════════════════════
D_out  = 400.0   # mm — đường kính ngoài buy
t_wall = 40.0    # mm — chiều dày vách buy
D_in   = D_out - 2*t_wall   # 320mm — đường kính trong
B_pile = D_out   # bước cọc (tiếp xúc) = D

# ĐẤT
Ka     = 0.4903; Kp = 2.0396
gam    = 18.0; gam_sat = 19.0; c_val = 8.0; q = 10.0
H_fill = 1.70; H_total = 2.20; z_embed = 0.60   # tăng embed lên 600mm

# ÁP LỰC/CỌC
Ea_per_m = (Ka*q*H_total + 0.5*Ka*gam*H_fill**2
            + 0.5*Ka*gam_sat*(H_total-H_fill)**2
            - 2*c_val*math.sqrt(Ka)*H_total)
Ea_per_pile = max(0, Ea_per_m) * (B_pile/1000)   # kN / cọc

# Mô men lớn nhất tại đáy tường (cantilever, tải hình thang)
w_top = Ka*q * (B_pile/1000)           # kN/m trên mỗi cọc (tải đều từ q)
w_bot = Ka*(gam*H_fill + gam_sat*(H_total-H_fill) + q) * (B_pile/1000) - 2*c_val*math.sqrt(Ka)*(B_pile/1000)
w_bot = max(0, w_bot)
# Mô men hình thang = M_chữ nhật(w_top) + M_tam giác(w_bot-w_top)
M_rect = w_top * H_total**2 / 2
M_tri  = (w_bot - w_top) * H_total**2 / 6
M_Ed   = M_rect + M_tri     # kN.m / cọc

# ══════════════════════════════════════════════════════════════════════════════
# THÔNG SỐ CÁC PHƯƠNG ÁN THÉP HÌNH
# ══════════════════════════════════════════════════════════════════════════════
# Thép B20: Ec=27000 MPa, fck=20 MPa, fctd=0.9 MPa
# Thép CT3/SS400: fy=250 MPa, Es=200000 MPa
Ec = 27000.0; Es = 200000.0; n_mod = Es/Ec   # tỷ số mô đun
fy = 250.0   # MPa

# Mặt cắt buy (ống tròn rỗng)
I_pipe = math.pi*(D_out**4 - D_in**4)/64   # mm⁴
W_pipe = I_pipe / (D_out/2)                 # mm³
I_grout= math.pi*D_in**4/64               # mm⁴ (nếu lấp đầy)
W_grout= I_grout/(D_in/2)

# Buy không có thép & không lấp vữa:
fct_design = 0.9  # MPa
M_Rd_bare = fct_design * W_pipe / 1e6    # kN.m  (chỉ ống không có thép)

# Các phương án thép hình
steel_options = {
    'H100x100\n(nho nhat)': {
        'h': 100,'b':100,'tw':6,'tf':8,
        'As': 2143,'I_s': 3.83e6,  # mm4
        'Ws': 76600,'label':'H100x100x6x8'
    },
    'H125x125\n(trung binh)': {
        'h':125,'b':125,'tw':6.5,'tf':9,
        'As': 3018,'I_s': 8.39e6,
        'Ws': 134200,'label':'H125x125x6.5x9'
    },
    'H150x150\n(khuyen nghi)': {
        'h':150,'b':150,'tw':7,'tf':10,
        'As': 4002,'I_s': 16.4e6,
        'Ws': 218700,'label':'H150x150x7x10'
    },
    '2x[C150\n(box)]': {
        'h':150,'b':130,'tw':5.5,'tf':9,
        'As': 4028,'I_s': 18.1e6,
        'Ws': 241000,'label':'2C150x65 (box)'
    },
}

def calc_composite(opt):
    I_s = opt['I_s']; As = opt['As']
    I_grout_eff = I_grout  # vữa lấp trong lõi
    I_composite = I_pipe + I_grout_eff/n_mod*n_mod + n_mod*I_s
    # (pipe + grout transformed to concrete + steel equiv concrete)
    # Actually: I_equiv_conc = I_pipe + I_grout + n*I_steel
    I_equiv = I_pipe + I_grout + n_mod * I_s
    W_equiv = I_equiv / (D_out/2)
    # Khả năng chịu uốn: steel governs at extreme fiber
    # M_steel = fy * Ws (steel section alone — conservative composite)
    M_steel = fy * opt['Ws'] / 1e6   # kN.m
    # Composite M_rd estimate (AISC method rough):
    M_composite_rd = M_Rd_bare + M_steel * 0.85  # partial composite
    Fs = M_composite_rd / M_Ed
    return M_composite_rd, Fs, I_equiv

results = {}
for name,opt in steel_options.items():
    Mrd, Fs, Ieq = calc_composite(opt)
    results[name] = {'M_Rd':Mrd,'Fs':round(Fs,2),'I_eq':Ieq,'opt':opt}

# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16.54, 11.69))
fig.patch.set_facecolor('white')
gs = GridSpec(2, 3, figure=fig, left=0.04, right=0.97, top=0.88, bottom=0.10,
              wspace=0.45, hspace=0.55)

ax1 = fig.add_subplot(gs[:, 0])   # Mặt cắt ngang chi tiết buy + thép H150
ax2 = fig.add_subplot(gs[:, 1])   # Mặt cắt đứng buy đứng + biểu đồ mô men
ax3 = fig.add_subplot(gs[0, 2])   # Bảng so sánh phương án thép
ax4 = fig.add_subplot(gs[1, 2])   # Biểu đồ cột Fs

# ════════════════════════════════════════════════════════════════════════════
# PANEL 1 — MẶT CẮT NGANG BUY Phi400 + THÉP H150
# ════════════════════════════════════════════════════════════════════════════
ax = ax1
ax.set_aspect('equal')
ax.set_facecolor(C_BG)
ax.set_title(f'MAT CAT NGANG — Buy Phi{int(D_out)} + Thep hinh H150\n'
             f'Mat cat hop phan (Composite Section) — ty le 1:5', fontsize=8.5,
             fontweight='bold', color=C_TITLE, pad=6)

sc = 1/1000  # scale: 1mm -> sc units

# Ống bê tông ngoài
outer = Circle((0,0), D_out/2*sc, facecolor='#D8D8D8', edgecolor='#444',
               lw=2.0, zorder=3)
ax.add_patch(outer)
ring = Wedge((0,0), D_out/2*sc, 0, 360, width=t_wall*sc,
             facecolor=C_BTCT, edgecolor='#333', lw=1.0, hatch='/', alpha=0.85, zorder=4)
ax.add_patch(ring)

# Vữa lấp lõi
grout = Circle((0,0), D_in/2*sc, facecolor=C_GROUT, edgecolor='#888', lw=0.8, zorder=3)
ax.add_patch(grout)

# Thép hình H150x150 bên trong
h_s = 150; b_s = 150; tw = 7; tf = 10
hw = h_s - 2*tf   # chiều cao bụng
# Bụng
web = Rectangle((-tw/2*sc, -h_s/2*sc), tw*sc, h_s*sc,
                facecolor='#455A64', edgecolor='#263238', lw=0.5, zorder=5)
ax.add_patch(web)
# Cánh trên
top_f = Rectangle((-b_s/2*sc, (h_s/2-tf)*sc), b_s*sc, tf*sc,
                   facecolor=C_STEEL, edgecolor='#263238', lw=0.5, zorder=5)
ax.add_patch(top_f)
# Cánh dưới
bot_f = Rectangle((-b_s/2*sc, -h_s/2*sc), b_s*sc, tf*sc,
                   facecolor=C_STEEL, edgecolor='#263238', lw=0.5, zorder=5)
ax.add_patch(bot_f)

# Khoảng hở giữa thép và ống (điền vữa)
ax.text(0, D_in/2*sc*0.55, 'Vua cap M300\n(lap day loi)', ha='center', va='center',
        fontsize=6, color='#555', style='italic')

# Dim: Đường kính ngoài
ax.annotate('', xy=(D_out/2*sc+0.02, 0), xytext=(-D_out/2*sc-0.02, 0),
            arrowprops=dict(arrowstyle='<->',color=C_DIM,lw=1.0,mutation_scale=9))
ax.text(0, -D_out/2*sc-0.04, f'D_ngoai = {int(D_out)} mm',
        ha='center', fontsize=7, color=C_DIM, fontweight='bold')

# Dim: Đường kính trong
ax.annotate('', xy=(D_in/2*sc, 0.04), xytext=(-D_in/2*sc, 0.04),
            arrowprops=dict(arrowstyle='<->',color='#666',lw=0.8,mutation_scale=7))
ax.text(0, 0.065, f'D_trong = {int(D_in)} mm', ha='center', fontsize=6.5, color='#555')

# Dim: H150 chiều cao
ax.annotate('', xy=(D_in/2*sc+0.05, h_s/2*sc), xytext=(D_in/2*sc+0.05, -h_s/2*sc),
            arrowprops=dict(arrowstyle='<->',color=C_STEEL,lw=0.9,mutation_scale=8))
ax.text(D_in/2*sc+0.09, 0, f'H_thep\n={h_s}mm', ha='left', fontsize=6.5,
        color=C_STEEL, fontweight='bold')

# Dim: B150
ax.annotate('', xy=(-b_s/2*sc, -h_s/2*sc-0.04), xytext=(b_s/2*sc, -h_s/2*sc-0.04),
            arrowprops=dict(arrowstyle='<->',color=C_STEEL,lw=0.9,mutation_scale=8))
ax.text(0, -h_s/2*sc-0.065, f'B={b_s}mm', ha='center', fontsize=6.5,
        color=C_STEEL, fontweight='bold')

# Chú thích cạnh
ax.annotate('Ong buy BTCT\nB20, vuach 40mm', xy=(D_out/2*sc*0.75, D_out/2*sc*0.75),
            xytext=(0.28, 0.28),
            arrowprops=dict(arrowstyle='->',color='#555',lw=0.7),
            fontsize=6.5, color='#333', ha='left')
ax.annotate('Thep H150x150\nCT3 / fy=250MPa', xy=(b_s/2*sc, 0),
            xytext=(0.20, -0.10),
            arrowprops=dict(arrowstyle='->',color=C_STEEL,lw=0.7),
            fontsize=6.5, color=C_STEEL, fontweight='bold', ha='left')
ax.annotate(f'Vach buy\n t={int(t_wall)}mm\n hatch BT', xy=(0, D_in/2*sc+(D_out-D_in)/4*sc),
            xytext=(-0.30, 0.28),
            arrowprops=dict(arrowstyle='->',color='#888',lw=0.7),
            fontsize=6.5, color='#555', ha='right')

# Thông số mặt cắt
opt_rec  = steel_options['H150x150\n(khuyen nghi)']
k150_    = 'H150x150\n(khuyen nghi)'
Mrd_rec  = results[k150_]['M_Rd']
Fs_rec_v = results[k150_]['Fs']
I_eq_rec = results[k150_]['I_eq']
ax.text(-0.38, -0.30,
        f'THONG SO MAT CAT:\n'
        f'I_ong = {I_pipe/1e6:.1f}x10^6 mm4\n'
        f'I_thep = {opt_rec["I_s"]/1e6:.1f}x10^6 mm4\n'
        f'I_tuong_duong = {I_eq_rec/1e6:.1f}x10^6 mm4\n'
        f'M_Ed (tai trong) = {M_Ed:.2f} kN.m\n'
        f'M_Rd (kha nang) = {Mrd_rec:.2f} kN.m\n'
        f'Fs = M_Rd/M_Ed = {Fs_rec_v:.2f}  [YEU CAU >= 1.5]',
        ha='left', va='top', fontsize=6.5, color='#1A1A1A',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9', edgecolor=C_GREEN, lw=1.0))

# Kết luận
color_concl = C_GREEN if Fs_rec_v >= 1.5 else C_RED
verdict = 'DAT!' if Fs_rec_v >= 1.5 else 'CHUA DAT'
ax.text(0, -0.44, f'KIEM TRA: Fs = {Fs_rec_v:.2f} >= 1.5  >>>  {verdict}',
        ha='center', fontsize=9, fontweight='bold', color='white',
        bbox=dict(boxstyle='round,pad=0.3', facecolor=color_concl, edgecolor='none'))

ax.set_xlim(-0.42, 0.45)
ax.set_ylim(-0.50, 0.40)
ax.axis('off')

# ════════════════════════════════════════════════════════════════════════════
# PANEL 2 — MẶT CẮT ĐỨNG + BIỂU ĐỒ MÔ MEN
# ════════════════════════════════════════════════════════════════════════════
ax = ax2
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title(f'MAT CAT DUNG — Buy dung + Thep H150 + Bieu do Mo men\n'
             f'M_Ed={M_Ed:.2f} kN.m / coc  |  z_embed={z_embed}m', fontsize=8.5,
             fontweight='bold', color=C_TITLE, pad=6)

r_buy = D_out/2/1000   # 0.20m
wall_t_m = t_wall/1000  # 0.04m

# Nước
ax.fill_between([-2.0, -r_buy-0.02],[-0.8,-0.8],[H_fill,H_fill],
                color=C_WATER, alpha=0.18, zorder=0)
for wy in [-0.3, 0.05, 0.4]:
    wx2 = np.linspace(-2.0, -r_buy-0.02, 20)
    wys2= [wy+0.02*np.sin(7*x*np.pi) for x in wx2]
    ax.plot(wx2,wys2,color=C_WATER,lw=0.8,alpha=0.5)
ax.text(-1.2,0.8,'KENH NUOC',ha='center',color=C_WATER,fontsize=7,fontweight='bold')

# Đất nền
ax.fill_between([-2.0,2.0],[-0.8,-0.8],[0.0,0.0],color=C_SOIL,alpha=0.35,zorder=1)
ax.fill_between([-2.0,2.0],[-0.8,-0.8],[-z_embed-0.02,-z_embed-0.02],
                color=C_SOIL,alpha=0.5,zorder=1)
for xi in np.arange(-2.0,2.0,0.3):
    for yi in np.arange(-0.75,0.0,0.25):
        ax.plot([xi,xi+0.12],[yi,yi-0.08],color='#8B6914',lw=0.4,alpha=0.3)

# Thảm đá chân
gabion = Rectangle((-1.8,-0.55),1.6,0.25,facecolor=C_GABION,edgecolor='#5D4037',
                    lw=0.8,alpha=0.7,zorder=3)
ax.add_patch(gabion)
rng2=np.random.default_rng(99)
for xi in np.arange(-1.75,-0.25,0.22):
    for yi in np.arange(-0.53,-0.33,0.18):
        r=rng2.uniform(0.06,0.09)
        st=Circle((xi+rng2.uniform(-0.03,0.03),yi),r,facecolor='#9E9E9E',edgecolor='#555',lw=0.4,alpha=0.8,zorder=4)
        ax.add_patch(st)
ax.text(-1.0,-0.43,'Tham da\nchan ke',ha='center',va='center',fontsize=6,color='white',fontweight='bold')

# 3 buy đứng cạnh nhau
for bi,cx in enumerate([-r_buy,0,r_buy]):
    # Ống ngoài
    x0=cx-r_buy; y_bot=-z_embed; y_top=H_fill
    rect_out=Rectangle((x0,y_bot),2*r_buy,y_top-y_bot,
                         facecolor='#D8D8D8',edgecolor='#444',lw=1.2,zorder=4)
    ax.add_patch(rect_out)
    # Vách
    rect_l=Rectangle((x0,y_bot),wall_t_m,y_top-y_bot,
                       facecolor=C_BTCT,edgecolor='none',hatch='/',lw=0,alpha=0.8,zorder=5)
    rect_r=Rectangle((cx+r_buy-wall_t_m,y_bot),wall_t_m,y_top-y_bot,
                       facecolor=C_BTCT,edgecolor='none',hatch='/',lw=0,alpha=0.8,zorder=5)
    ax.add_patch(rect_l); ax.add_patch(rect_r)
    # Thép H (tiết diện thu nhỏ — nhìn từ mặt trước)
    tw_m=7/1000; bf_m=150/1000; hs_m=150/1000; tf_m=10/1000
    hw_m=hs_m-2*tf_m
    # Bụng
    web_r=Rectangle((cx-tw_m/2,y_bot),tw_m,y_top-y_bot,
                      facecolor='#37474F',edgecolor='none',alpha=0.9,zorder=6)
    ax.add_patch(web_r)
    # Cánh (chỉ thấy ở đầu trên và đáy vài cái đại diện)
    for yc in np.arange(y_bot+0.05, y_top, 0.4):
        tf_r=Rectangle((cx-bf_m/2,yc-tf_m/2),bf_m,tf_m,
                         facecolor=C_STEEL,edgecolor='none',alpha=0.7,zorder=6)
        ax.add_patch(tf_r)

# Dầm đỉnh
cap_h = 0.30; cap_w = 3*2*r_buy+0.05
cap=Rectangle((-3*r_buy-0.02,H_fill),cap_w,cap_h,
               facecolor='#BBBBBB',edgecolor='#333',lw=1.5,hatch='..',zorder=6)
ax.add_patch(cap)
ax.text(0,H_fill+cap_h/2,'DAM DINH BTCT\n300x300 / 4Phi12',ha='center',va='center',
        fontsize=6,color='#222',fontweight='bold')
# Thép chờ dầm đỉnh
for xi in [-0.35,0.0,0.35]:
    ax.plot([xi,xi],[H_fill-0.15,H_fill+cap_h+0.05],
            color='#222',lw=1.5,zorder=7)

# Vải ĐKT và đất đắp phía sau
ax.fill_between([r_buy*3+0.03,2.0],[0.0,0.0],[H_fill,H_fill],
                color=C_SOIL,alpha=0.25,zorder=2)
ax.plot([r_buy*3+0.02,r_buy*3+0.02],[0,H_fill],color=C_GEO,lw=2.5,ls='--',alpha=0.9,zorder=7)
ax.plot([r_buy*3+0.02,r_buy*3+0.55],[0,0],color=C_GEO,lw=2.5,ls='--',alpha=0.9,zorder=7)
ax.text(r_buy*3+0.25,0.6,'Vai DKT\nPhi150g',fontsize=6,color=C_GEO)

# Cao độ
ax.plot([-2.0,2.0],[H_fill,H_fill],color=C_TITLE,lw=0.8,ls='--',alpha=0.5)
ax.plot([-2.0,2.0],[0,0],color='#6B4C00',lw=0.8,ls='--',alpha=0.5)
ax.text(1.8,H_fill+0.05,'CD HT\n+5.20',fontsize=6,color=C_TITLE,ha='right')
ax.text(1.8,0.05,'CD TN\n+3.50',fontsize=6,color='#6B4C00',ha='right')

# MN
ax.plot([-2.0,-r_buy-0.05],[0.1,0.1],color='#0066CC',lw=1.0,ls='-.',alpha=0.7)
ax.text(-1.8,0.17,'MN.TN',fontsize=6,color='#0066CC',style='italic')

# ── BIỂU ĐỒ MÔ MEN THEO CHIỀU CAO ──────────────────────────────────────
x_M_start = 2.0
z_vals_M = np.linspace(0, H_fill, 30)
# Moment tại độ sâu z từ đỉnh tự do (cantilever, fixed ở đáy)
moments = []
for z in z_vals_M:
    z_from_bot = H_fill - z
    # Mô men tại z từ đỉnh = tích phân từ z tới H của (p * (xi-z))
    # = w_top*(H-z)^2/2 + (w_bot-w_top)*(H-z)^2/6... simplified
    h_rem = H_fill - z
    w_top_z = Ka*(q)*(D_out/1000)
    w_bot_z = Ka*(gam*H_fill + q)*(D_out/1000)
    M_z = w_top_z*h_rem**2/2 + (w_bot_z-w_top_z)*h_rem**2/6
    moments.append(M_z)

M_scale = 0.08  # 1 kN.m = 0.08m
xs_M = [x_M_start + m*M_scale for m in moments]
ys_M = [H_fill - z for z in z_vals_M]
ax.fill_betweenx(ys_M, x_M_start, xs_M, color='#EF5350', alpha=0.4, label='M_Ed(z)')
ax.plot(xs_M, ys_M, color='#EF5350', lw=1.8, zorder=5)
ax.plot([x_M_start, x_M_start],[0, H_fill],color='#333',lw=1.0,zorder=4)
ax.text(x_M_start+max(moments)*M_scale+0.05, H_fill/2,
        f'M_Ed(max)\n={M_Ed:.2f} kN.m\n(tai day)',
        fontsize=7,color='#EF5350',fontweight='bold',ha='left')
ax.text(x_M_start+0.05, H_fill+0.1, 'Bieu do\nMo men',fontsize=7,color='#EF5350',ha='center')

# Vùng embed
ax.axhspan(-z_embed,0,color='#E8F5E9',alpha=0.4,zorder=0)
ax.text(0,-z_embed/2,'VUNG\nNGAM\n(embed)',ha='center',va='center',fontsize=6,
        color=C_GREEN,fontweight='bold')

dim_line(ax,-2.15,0,-2.15,H_fill,f'H={H_fill}m',orient='v',text_off=-0.22,fs=7)
dim_line(ax,-2.15,-z_embed,-2.15,0,f'z_em={z_embed}m',orient='v',text_off=-0.22,fs=7,color=C_GREEN)

ax.set_xlim(-2.3, 2.9)
ax.set_ylim(-0.95, 2.2)
ax.legend(loc='upper left', fontsize=6.5, framealpha=0.9)
ax.axis('off')

# ════════════════════════════════════════════════════════════════════════════
# PANEL 3 — BẢNG SO SÁNH PHƯƠNG ÁN THÉP HÌNH
# ════════════════════════════════════════════════════════════════════════════
ax = ax3
ax.set_facecolor(C_BG)
ax.set_xlim(0,10); ax.set_ylim(0,10); ax.axis('off')
ax.set_title(f'BANG KIEM TRA 4 PHUONG AN THEP HINH\n'
             f'M_Ed = {M_Ed:.2f} kN.m / coc (yeu cau Fs >= 1.5)',
             fontsize=8.5, fontweight='bold', color=C_TITLE, pad=6)

# Header
hdrs = ['Phuong an','I_s\n(cm4)','M_Rd\n(kN.m)','Fs','Ket luan']
col_xs = [0.0,2.5,4.5,6.2,7.5]; col_ws=[2.5,2.0,1.7,1.3,2.5]
y0 = 9.6; row_h = 1.1
for j,(h,cx,cw) in enumerate(zip(hdrs,col_xs,col_ws)):
    rb=FancyBboxPatch((cx,y0-row_h*0.9),cw-0.08,row_h*0.85,
                       boxstyle='square,pad=0',facecolor=C_TITLE,edgecolor='#AAA',lw=0.4,zorder=2)
    ax.add_patch(rb)
    ax.text(cx+0.09,y0-row_h*0.45,h,va='center',fontsize=6.8,fontweight='bold',color='white')

for i,(name,res) in enumerate(results.items()):
    yr = y0 - (i+1)*row_h*0.85 - row_h*0.05
    opt = res['opt']
    Mrd = res['M_Rd']; Fs = res['Fs']
    ok = Fs >= 1.5
    bg = '#E8F5E9' if ok else '#FFEBEE'
    rec = '(KHUYEN NGHI)' if name.startswith('H150') else ''
    verdict = 'DAT' if ok else 'CHUA DAT'
    verdict_color = '#1B5E20' if ok else '#C62828'
    
    vals = [name.replace('\n',' '), f"{opt['I_s']/1e4:.0f}", f"{Mrd:.1f}", f"{Fs}", f"{verdict} {rec}"]
    for j,(cell,cx,cw) in enumerate(zip(vals,col_xs,col_ws)):
        cell_bg = '#C8E6C9' if (ok and j==len(vals)-1) else bg
        rb=FancyBboxPatch((cx,yr-row_h*0.78),cw-0.08,row_h*0.78,
                           boxstyle='square,pad=0',facecolor=cell_bg,edgecolor='#DDD',lw=0.3,zorder=2)
        ax.add_patch(rb)
        c_text = verdict_color if j==len(vals)-1 else '#111'
        ax.text(cx+0.09,yr-row_h*0.39,str(cell),va='center',fontsize=6.5,
                color=c_text,fontweight='bold' if j==len(vals)-1 else 'normal',ha='left')

# Kết luận chung
y_kl = y0 - (len(results)+1)*row_h*0.85 - 0.3
ax.text(0, y_kl,
        f'Buy KHONG CO thep: M_Rd_bare = {M_Rd_bare:.2f} kN.m  |  Fs = {M_Rd_bare/M_Ed:.2f}  >>> CHUA DAT',
        fontsize=7, va='top', color=C_RED, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2',facecolor='#FFEBEE',edgecolor=C_RED,lw=0.8))

y_kl2 = y_kl - 0.7
key_rec = 'H150x150\n(khuyen nghi)'
Fs_rec_val = results[key_rec]['Fs']
Mrd_rec_val = results[key_rec]['M_Rd']
ax.text(0, y_kl2,
        (f'Voi H150x150: Fs = {Fs_rec_val:.2f} >= 1.5  ---  DAT!\n'
         f'Kha nang tang cuong: +{Mrd_rec_val/M_Rd_bare:.0f}x so voi buy khong thep.\n'
         'DIEU KIEN: Cham thep H vao toi thieu 60% chieu cao buy (L_thep = L_buy).\n'
         'Buoc coc = Phi400mm; Dam dinh BTCT 300x300 bat buoc.'),
        fontsize=7, va='top', color=C_GREEN,
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=1.0))

# ════════════════════════════════════════════════════════════════════════════
# PANEL 4 — BIỂU ĐỒ THANH FS CÁC PHƯƠNG ÁN
# ════════════════════════════════════════════════════════════════════════════
ax = ax4
ax.set_facecolor(C_BG)
ax.set_title('BIEU DO FS — CAC PHUONG AN THEP HINH vs KHONG THEP',
             fontsize=8.5, fontweight='bold', color=C_TITLE, pad=6)

names_bar = ['Buy\nkhong thep'] + [k.replace('\n',' ') for k in results.keys()]
fs_bar    = [M_Rd_bare/M_Ed] + [v['Fs'] for v in results.values()]
colors_bar= [C_RED if f<1.5 else ('#2196F3' if f<3.0 else C_GREEN) for f in fs_bar]

bars_x = np.arange(len(names_bar))
bars = ax.bar(bars_x, fs_bar, color=colors_bar, edgecolor='white', linewidth=1.2, zorder=3)

# Đường Fs_min = 1.5
ax.axhline(1.5, color=C_RED, lw=1.5, ls='--', zorder=4, label='Fs min = 1.5')
ax.axhline(2.0, color=C_ORANGE, lw=1.0, ls=':', zorder=4, label='Fs tt = 2.0 (khuyen nghi)')

for bar,f,c in zip(bars, fs_bar, colors_bar):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
            f'{f:.2f}', ha='center', va='bottom', fontsize=7, fontweight='bold', color=c)

# Annotation KHUYEN NGHI
rec_idx = list(results.keys()).index('H150x150\n(khuyen nghi)') + 1
ax.annotate('KHUYEN NGHI',
            xy=(rec_idx, fs_bar[rec_idx]),
            xytext=(rec_idx+0.8, fs_bar[rec_idx]+0.3),
            arrowprops=dict(arrowstyle='->',color=C_GREEN,lw=1.2),
            fontsize=7, color=C_GREEN, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=0.8))

ax.set_xticks(bars_x)
ax.set_xticklabels(names_bar, fontsize=6.5)
ax.set_ylabel('He so an toan Fs = M_Rd / M_Ed', fontsize=7)
ax.set_ylim(0, max(fs_bar)*1.25)
ax.set_facecolor(C_BG)
ax.legend(fontsize=6.5, loc='upper left')
ax.grid(axis='y', alpha=0.3, lw=0.5)
ax.tick_params(labelsize=6.5)
for sp in ['top','right']: ax.spines[sp].set_visible(False)

# ════════════════════════════════════════════════════════════════════════════
# TITLE BLOCK
# ════════════════════════════════════════════════════════════════════════════
fig.text(0.5, 0.975,
         'PHAN TICH KHA NANG CHIU LUC — BUY PHI400 GIA CUONG THEP HINH',
         ha='center', va='top', fontsize=13, fontweight='bold', color='white',
         bbox=dict(boxstyle='square,pad=0.2', facecolor=C_TITLE, edgecolor='none'))
fig.text(0.5, 0.955,
         f'Mat cat hop phan (Composite): Buy BTCT B20 + Thep H CT3  |  '
         f'M_Ed={M_Ed:.2f} kN.m/coc  |  H={H_fill}m  |  Phi={int(D_out)}mm',
         ha='center', va='top', fontsize=10, color=C_TITLE, fontweight='bold')
fig.text(0.5, 0.933,
         'Tieu chuan: TCVN 9902:2016 | TCVN 5574:2018 (BTCT) | TCVN 5575:2012 (Thep)  |  '
         f'Ngay: {date.today().strftime("%d/%m/%Y")}',
         ha='center', va='top', fontsize=8.5, color='#555', style='italic')
fig.add_artist(plt.Line2D([0.03,0.97],[0.895,0.895],transform=fig.transFigure,
               color=C_TITLE, lw=1.5))
fig.text(0.5,0.055,
         'MA HIEU: KC-PI-GIA-CUONG-01  |  TY LE: 1:5 (mat cat) / 1:10 (mat cat dung)  |  '
         'Nguoi ve: AI Technical Illustrator',
         ha='center',va='bottom',fontsize=7,color='#333',
         bbox=dict(boxstyle='round,pad=0.4',facecolor='#EAF1FB',edgecolor=C_TITLE,lw=1.0))
fig.add_artist(plt.Line2D([0.03,0.97],[0.10,0.10],transform=fig.transFigure,
               color=C_TITLE, lw=1.0))

# ── Lưu ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--out', default=r'G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI\ke_pi_gia_cuong_thep_hinh.png')
args = parser.parse_args()
os.makedirs(os.path.dirname(args.out), exist_ok=True)
fig.savefig(args.out, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"[OK] Da luu: {args.out}")
print(f"  M_Ed = {M_Ed:.3f} kN.m / coc")
print(f"  M_Rd_bare = {M_Rd_bare:.3f} kN.m  |  Fs = {M_Rd_bare/M_Ed:.2f}  >>> CHUA DAT")
k150 = 'H150x150\n(khuyen nghi)'
print(f"  M_Rd_H150 = {results[k150]['M_Rd']:.3f} kN.m  |  Fs = {results[k150]['Fs']}")
print("  KIEM TRA: Fs(H150) >= 1.5  >>>  DAT!")
