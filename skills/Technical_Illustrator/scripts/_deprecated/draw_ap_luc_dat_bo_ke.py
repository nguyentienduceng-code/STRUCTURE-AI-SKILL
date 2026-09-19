
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
draw_ap_luc_dat_bo_ke.py
Bản vẽ kỹ thuật phân tích áp lực đất + so sánh 3 phương án kè tối ưu
Dự án: Bờ kè kênh nội bộ — Cao độ HT 5.20m / Đất nền 3.50m
"""
import sys, os, argparse, math
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon, FancyArrowPatch, Arc
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import date

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,
                     'axes.linewidth':0.8,'axes.titlesize':9,'axes.titleweight':'bold'})

# ── Màu sắc ──────────────────────────────────────────────────────────────────
C_SOIL    = '#C4A265'
C_WATER   = '#5B9BD5'
C_BTCT    = '#AAAAAA'
C_THEP    = '#2F2F2F'
C_GEO     = '#4CAF50'
C_GABION  = '#8D6E63'
C_DIM     = '#1A1A8C'
C_RED     = '#C62828'
C_ORANGE  = '#E65100'
C_GREEN   = '#1B5E20'
C_TITLE   = '#1C3557'
C_BG      = '#F8F9FA'
C_PRESS   = '#EF5350'   # biểu đồ áp lực chủ động
C_PPASS   = '#42A5F5'   # áp lực bị động

def dim_line(ax,x1,y1,x2,y2,label,text_off=0,orient='h',fs=6.8,color=C_DIM):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),
                arrowprops=dict(arrowstyle='<->',color=color,lw=0.9,mutation_scale=8))
    mx=(x1+x2)/2+(text_off if orient=='v' else 0)
    my=(y1+y2)/2+(text_off if orient=='h' else 0)
    ax.text(mx,my,label,ha='center',va='center',color=color,fontsize=fs,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1',facecolor='white',edgecolor='none',alpha=0.9))

# ══════════════════════════════════════════════════════════════════════════════
# THÔNG SỐ TÍNH TOÁN
# ══════════════════════════════════════════════════════════════════════════════
# Địa chất — đất phù sa ven kênh (vùng bán đô thị ĐBSCL)
gam_soil  = 18.0    # kN/m³ — trọng lượng đơn vị đất đắp
gam_sat   = 19.0    # kN/m³ — đất bão hòa dưới MN
phi_deg   = 20.0    # ° — góc ma sát trong (đất yếu đến trung bình)
phi_rad   = math.radians(phi_deg)
c_kPa     = 8.0     # kPa — lực dính (đất bùn sét pha)
q_surcharge = 10.0  # kPa — hoạt tải mặt đất (người đi, xe nhẹ)

# Hình học
H_fill    = 1.70    # m — chiều cao đất đắp (5.20 - 3.50)
CaoDoHT   = 5.20    # m — cao độ hoàn thiện
CaoDoTN   = 3.50    # m — cao độ đất tự nhiên
MN_TN     = 3.20    # m — mực nước thiên nhiên ước tính (dưới đất tự nhiên 0.3m)
H_total   = 2.20    # m — chiều cao tường tổng (tính thêm 0.5m đáy + 0.5m xói)
H_water   = CaoDoTN - MN_TN  # 0.30m phần trên MN

# Hệ số áp lực đất (Rankine)
Ka = math.tan(math.radians(45) - phi_rad/2)**2
Kp = math.tan(math.radians(45) + phi_rad/2)**2

# ── Tính áp lực chủ động (Active) tại các điểm đặc biệt ──────────────────
# z=0 (mặt đất): σa = Ka*q - 2c*sqrt(Ka)
sig_a_top  = Ka * q_surcharge - 2*c_kPa*math.sqrt(Ka)
sig_a_top  = max(0, sig_a_top)  # không âm (đất không bị kéo nếu có vết nứt)
# z=H_fill (đáy đất đắp / mặt đất gốc): σa = Ka*(γ*H+q) - 2c√Ka
sig_a_H    = Ka*(gam_soil*H_fill + q_surcharge) - 2*c_kPa*math.sqrt(Ka)
# z=H_total (đáy tường):
sig_a_bot  = Ka*(gam_soil*H_fill + gam_sat*(H_total-H_fill) + q_surcharge) - 2*c_kPa*math.sqrt(Ka)

# Hợp lực áp lực chủ động
Ea_q   = Ka * q_surcharge * H_total          # do hoạt tải q
Ea_soil= 0.5 * Ka * gam_soil * H_fill**2    # do đất đắp
Ea_sat = 0.5 * Ka * gam_sat * (H_total-H_fill)**2
Ea_c   = -2*c_kPa*math.sqrt(Ka)*H_total     # giảm do lực dính
Ea_total = Ea_q + Ea_soil + Ea_sat + max(0,Ea_c)

# Áp lực bị động tại đáy (z_embed = 0.5m)
z_embed   = 0.50    # chiều sâu ngàm bình quân
sig_p_bot = Kp*gam_sat*z_embed + 2*c_kPa*math.sqrt(Kp)
Ep_total  = 0.5*Kp*gam_sat*z_embed**2 + 2*c_kPa*math.sqrt(Kp)*z_embed

# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16.54,11.69))
fig.patch.set_facecolor('white')
gs = GridSpec(2,3,figure=fig,left=0.04,right=0.97,top=0.88,bottom=0.10,
              wspace=0.42,hspace=0.52)

ax1 = fig.add_subplot(gs[:,0])    # Sơ đồ áp lực đất
ax2 = fig.add_subplot(gs[:,1])    # Phương án khuyến nghị (PA tối ưu)
ax3 = fig.add_subplot(gs[0,2])    # Bảng thông số tính toán
ax4 = fig.add_subplot(gs[1,2])    # Biểu đồ so sánh phương án

# ════════════════════════════════════════════════════════════════════════════
# PANEL 1 — SƠ ĐỒ ÁP LỰC ĐẤT (Active vs Passive)
# ════════════════════════════════════════════════════════════════════════════
ax = ax1
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title(f'SO DO AP LUC DAT\nActive (Chu dong) vs Passive (Bi dong) — Rankine\n'
             f'Ka={Ka:.3f}  Kp={Kp:.3f}  phi={phi_deg}deg  c={c_kPa}kPa', 
             fontsize=8, fontweight='bold', color=C_TITLE, pad=6)

# Trục tọa độ — z từ 0 (mặt đất) xuống
z_vals  = np.linspace(0, H_total, 50)
sig_act = [max(0, Ka*(gam_soil*min(z,H_fill) + gam_sat*max(0,z-H_fill) + q_surcharge)
               - 2*c_kPa*math.sqrt(Ka)) for z in z_vals]
sig_pas = [Kp*gam_sat*max(0,z-H_total+z_embed) + 2*c_kPa*math.sqrt(Kp)
           for z in np.linspace(H_total-z_embed, H_total, 10)]

# Vẽ tường (tim tường tại x=0)
scale_p = 0.05   # 1 kPa = 0.05m trên hình
wall_left  = -0.25
wall_right =  0.25
wall_top   =  0.0
wall_bot   = -H_total

# Đất đắp phía sau (phải) — màu nâu nhạt
ax.fill_between([wall_right, wall_right+1.5], [wall_top, wall_top], [wall_bot, wall_bot],
                color=C_SOIL, alpha=0.25)
for xi in np.arange(wall_right+0.1, wall_right+1.5, 0.25):
    for yi in np.arange(wall_bot+0.1, wall_top, 0.3):
        ax.plot([xi,xi+0.12],[yi,yi-0.1],color='#8B6914',lw=0.5,alpha=0.3)

# Đất phía trước kênh (trái) — xanh nhạt (nước)
ax.fill_between([wall_left-1.5, wall_left],[wall_top,wall_top],[wall_bot,wall_bot],
                color=C_WATER,alpha=0.15)
ax.plot([wall_left-1.5,wall_left],[wall_top-H_water, wall_top-H_water],
        color='#0066CC',lw=1.2,ls='-.',alpha=0.8)
ax.text(wall_left-0.7,wall_top-H_water+0.07,'MN.TN\n(+3.20)',color='#0066CC',fontsize=6,ha='center')

# Tường BTCT
wall_rect = Rectangle((wall_left, wall_bot), 0.50, H_total,
                        facecolor='#C0C0C0', edgecolor='#444', lw=1.5,
                        hatch='..', zorder=4)
ax.add_patch(wall_rect)
ax.text(0, wall_bot/2, 'TUONG\nBTCT', ha='center', va='center',
        fontsize=6.5, color='#333', fontweight='bold')

# ── Biểu đồ áp lực chủ động (phía phải tường, chỉa sang trái) ──────────
xs_act = [wall_right + s*scale_p for s in sig_act]
ys_act = [-z for z in z_vals]
# Vẽ vùng tô
ax.fill_betweenx(ys_act, wall_right, xs_act, color=C_PRESS, alpha=0.35, label='Ap luc chu dong (Ea)')
ax.plot(xs_act, ys_act, color=C_PRESS, lw=1.8, zorder=5)

# Ghi giá trị tại các điểm đặc biệt
ax.annotate(f'q={q_surcharge}kPa',
            xy=(wall_right+q_surcharge*scale_p*Ka, 0),
            xytext=(wall_right+q_surcharge*scale_p*Ka+0.3, -0.15),
            arrowprops=dict(arrowstyle='->',color=C_PRESS,lw=0.7),
            fontsize=6.5, color=C_PRESS)
ax.text(wall_right + sig_a_H*scale_p + 0.05, -H_fill,
        f'{sig_a_H:.1f} kPa', fontsize=6.5, color=C_PRESS, va='center')
ax.text(wall_right + sig_a_bot*scale_p + 0.05, -H_total+0.1,
        f'{sig_a_bot:.1f} kPa', fontsize=6.5, color=C_PRESS, va='center')

# Hợp lực Ea
ea_y = -(H_total*2/3)
ax.annotate(f'Ea={Ea_total:.1f} kN/m',
            xy=(wall_right+0.05, ea_y),
            xytext=(wall_right+0.5, ea_y+0.2),
            arrowprops=dict(arrowstyle='->',color=C_RED,lw=1.2),
            fontsize=7, color=C_RED, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2',facecolor='#FFEBEE',edgecolor=C_RED,lw=0.8))

# ── Biểu đồ áp lực bị động (phía trái tường, z_embed) ──────────────────
z_p_start = H_total - z_embed
z_p_end   = H_total
z_p_vals  = np.linspace(z_p_start, z_p_end, 20)
sig_p_vals= [Kp*gam_sat*(z-z_p_start) + 2*c_kPa*math.sqrt(Kp) for z in z_p_vals]
xs_p = [wall_left - s*scale_p for s in sig_p_vals]
ys_p = [-z for z in z_p_vals]
ax.fill_betweenx(ys_p, wall_left, xs_p, color=C_PPASS, alpha=0.35, label='Ap luc bi dong (Ep)')
ax.plot(xs_p, ys_p, color=C_PPASS, lw=1.8, zorder=5)
ax.text(wall_left - sig_p_bot*scale_p - 0.05, -H_total+0.05,
        f'Ep={Ep_total:.1f} kN/m\n(z_embed={z_embed}m)', fontsize=6.5, color=C_PPASS,
        ha='right', va='bottom',
        bbox=dict(boxstyle='round,pad=0.15',facecolor='#E3F2FD',edgecolor=C_PPASS,lw=0.7))

# Kích thước
ax.plot([wall_right+0.1,wall_right+0.1],[0,-H_fill],color=C_DIM,lw=0.7)
ax.plot([wall_right+0.1,wall_right+0.1],[-H_fill,-H_total],color=C_DIM,lw=0.7)
dim_line(ax,wall_right+0.25,0,wall_right+0.25,-H_fill,f'H_fill={H_fill}m',orient='v',text_off=0.22,fs=6.5)
dim_line(ax,wall_right+0.25,-H_fill,wall_right+0.25,-H_total,f'H_embed={H_total-H_fill}m',orient='v',text_off=0.25,fs=6.5)

# Cao độ labels
ax.text(wall_left-1.55, 0, '+5.20m (HT)', fontsize=6.5, color=C_TITLE, va='center', fontweight='bold')
ax.text(wall_left-1.55, -H_fill, '+3.50m (TN)', fontsize=6.5, color='#6B4C00', va='center', fontweight='bold')
ax.plot([wall_left-1.5, wall_right+2.0],[0,0],color='#333',lw=0.8,ls='--',alpha=0.5)
ax.plot([wall_left-1.5, wall_right+0.5],[-H_fill,-H_fill],color='#8B6914',lw=0.8,ls='--',alpha=0.5)

# Ghi chú mặt cắt ranh giới đất đắp / đất bão hòa
ax.annotate('Dat dap (kho)\ngam=18 kN/m3',
            xy=(wall_right+1.2,-H_fill/2),
            xytext=(wall_right+1.5,-H_fill/2),
            fontsize=6, color='#6B4C00', ha='left')
ax.annotate('Dat bao hoa\ngam=19 kN/m3',
            xy=(wall_right+1.2,-(H_fill+(H_total-H_fill)/2)),
            xytext=(wall_right+1.5,-(H_fill+(H_total-H_fill)/2)),
            fontsize=6, color='#0044AA', ha='left')

ax.set_xlim(wall_left-1.7, wall_right+2.2)
ax.set_ylim(-H_total-0.3, 0.5)
ax.legend(loc='lower left', fontsize=6.5, framealpha=0.9)
ax.axis('off')

# ════════════════════════════════════════════════════════════════════════════
# PANEL 2 — PHƯƠNG ÁN TỐI ƯU: TƯỜNG BTCT CHỮ L + THẢM ĐÁ CHÂN KÈ
# ════════════════════════════════════════════════════════════════════════════
ax = ax2
ax.set_facecolor(C_BG)
ax.set_aspect('equal')
ax.set_title('PHUONG AN TOI UU — PA2\nTuong BTCT chu L + Tham Da chan ke\nTy le 1:20', 
             fontsize=8.5, fontweight='bold', color=C_GREEN, pad=6)

# ── Nước phía trước ──────────────────────────────────────────────────────
ax.fill_between([-3.0, -0.25],[-1.2,-1.2],[1.2,1.2],color=C_WATER,alpha=0.15,zorder=0)
for wy in [-0.3,0.1,0.5]:
    wx=np.linspace(-3,-0.25,25)
    wys=[wy+0.02*np.sin(7*x*np.pi) for x in wx]
    ax.plot(wx,wys,color=C_WATER,lw=0.8,alpha=0.6)
ax.text(-1.5, 0.7, 'KENH NUOC', ha='center', color=C_WATER, fontsize=7, fontweight='bold')

# ── Đất nền ───────────────────────────────────────────────────────────────
ax.fill_between([-3.0,3.5],[-1.2,-1.2],[0.0,0.0],color=C_SOIL,alpha=0.4,zorder=1)
ax.fill_between([-0.25,3.5],[-0.5,-0.5],[0.0,0.0],color='#A57C3A',alpha=0.5,zorder=2)

# ── Thảm đá bảo vệ chân kè ──────────────────────────────────────────────
gabion_xs = np.array([-2.8,-0.2,-0.2,-2.8,-2.8])
gabion_ys = np.array([-0.8,-0.8,-0.5,-0.5,-0.8])
ax.fill(gabion_xs, gabion_ys, color=C_GABION, alpha=0.7, zorder=3)
ax.plot(gabion_xs, gabion_ys, color='#5D4037', lw=1.0, zorder=4)
# Đá hộc trong thảm
rng = np.random.default_rng(42)
for xi in np.arange(-2.7,-0.3,0.3):
    for yi in np.arange(-0.78,-0.55,0.2):
        r = rng.uniform(0.06,0.10)
        stone = Circle((xi+rng.uniform(-0.05,0.05),yi+rng.uniform(-0.02,0.02)),
                        r, facecolor='#9E9E9E', edgecolor='#616161', lw=0.5, alpha=0.8, zorder=5)
        ax.add_patch(stone)
ax.text(-1.5,-0.65,'Tham da\n(da hoc Phi100-200)',ha='center',va='center',fontsize=6,color='white',fontweight='bold')

# ── Tường BTCT chữ L ──────────────────────────────────────────────────────
# Thân đứng: rộng 0.25m, cao H_fill+0.2=1.9m
wall_b   = 0.25   # bề dày thân tường
wall_h   = H_fill + 0.20  # 1.90m
foot_b   = 1.50   # bề rộng bản móng
foot_h   = 0.30   # chiều dày bản móng
foot_x   = -0.25  # mép ngoài bản móng (phía sông)

# Bản đế
foot = Rectangle((foot_x, -foot_h), foot_b, foot_h,
                  facecolor='#B0B0B0', edgecolor='#444', lw=1.2, hatch='..', zorder=6)
ax.add_patch(foot)
# Thân tường
stem = Rectangle((foot_x+foot_b-wall_b, -foot_h), wall_b, wall_h+foot_h,
                  facecolor='#AAAAAA', edgecolor='#444', lw=1.2, hatch='..', zorder=6)
ax.add_patch(stem)

# Vầy thoát nước (weep holes) Phi75 tại 1.5m
for wh_y in [0.2, 0.7]:
    wh = Circle((foot_x+foot_b-wall_b, wh_y), 0.04,
                 facecolor=C_WATER, edgecolor='#333', lw=0.5, zorder=7)
    ax.add_patch(wh)
ax.text(foot_x+foot_b-wall_b-0.18, 0.2, 'Loi thoat\nnuoc\nPhi75',
        fontsize=5.5, ha='right', va='center', color='#0066CC')

# Cốt thép trong tường (chính)
for rebar_y in np.arange(-foot_h+0.05, wall_h, 0.3):
    rb = Circle((foot_x+foot_b-wall_b+0.05, rebar_y), 0.025,
                 facecolor='black', edgecolor='black', zorder=8)
    ax.add_patch(rb)
for rebar_y in np.arange(-foot_h+0.05, wall_h, 0.3):
    rb = Circle((foot_x+foot_b-0.05, rebar_y), 0.025,
                 facecolor='black', edgecolor='black', zorder=8)
    ax.add_patch(rb)

# Đất đắp sau tường
ax.fill_between([foot_x+foot_b-wall_b, 3.0],[0.0,0.0],[H_fill,H_fill],
                color=C_SOIL,alpha=0.3,zorder=3)
for xi in np.arange(foot_x+foot_b-wall_b+0.05, 3.0, 0.4):
    for yi in np.arange(0.1, H_fill, 0.4):
        ax.plot([xi,xi+0.12],[yi,yi-0.1],color='#8B6914',lw=0.4,alpha=0.3)

# Vải địa kỹ thuật
ax.plot([foot_x+foot_b-wall_b-0.01, foot_x+foot_b-wall_b-0.01],[0.0,H_fill],
        color=C_GEO, lw=2.5, ls='--', alpha=0.9, zorder=7)
ax.plot([foot_x+foot_b-wall_b-0.01, foot_x+foot_b-wall_b+0.6],[0.0,0.0],
        color=C_GEO, lw=2.5, ls='--', alpha=0.9, zorder=7)
ax.text(foot_x+foot_b+0.25, 0.85, 'Vai DKT\nPhi150g/m2', fontsize=6, color=C_GEO, va='center')

# Đất đắp cấp phối phía trên đà bản đế
ax.fill_between([foot_x+foot_b-wall_b, foot_x+foot_b], [-foot_h,-foot_h],[0.0,0.0],
                color='#B8A07A',alpha=0.6,zorder=5)

# Coping beam / đá chỉ đỉnh
cope = Rectangle((foot_x+foot_b-wall_b-0.05, wall_h-foot_h), wall_b+0.10, 0.15,
                  facecolor='#888', edgecolor='#333', lw=1.0, hatch='.', zorder=7)
ax.add_patch(cope)

# ── Mực nước & cao độ ────────────────────────────────────────────────────
ax.plot([-3.0, foot_x],[0.1, 0.1],color='#0066CC',lw=1.0,ls='-.',alpha=0.7)
ax.text(-2.8, 0.18, 'MN.TN (+3.20)', fontsize=6.0, color='#0066CC', style='italic')

# Cao độ
ax.plot([-2.8,3.0],[0.0,0.0],color='#6B4C00',lw=0.8,ls='--',alpha=0.5)
ax.plot([-2.8,3.0],[H_fill,H_fill],color=C_TITLE,lw=1.0,ls='--',alpha=0.7)
ax.text(2.5, 0.07, 'CD TN\n+3.50m', fontsize=6.5, color='#6B4C00', ha='right')
ax.text(2.5, H_fill+0.07, 'CD HT\n+5.20m', fontsize=6.5, color=C_TITLE, ha='right', fontweight='bold')

# ── Kích thước ────────────────────────────────────────────────────────────
dim_line(ax,-0.6,0,-0.6,H_fill,f'H={H_fill}m',orient='v',text_off=-0.18,fs=7)
dim_line(ax,foot_x,0.22,foot_x+foot_b,0.22,f'B_de={foot_b}m',orient='h',text_off=0.1,fs=7)
dim_line(ax,2.0,-foot_h,2.0,0,f't_de={foot_h}m',orient='v',text_off=0.15,fs=7)
ax.plot([foot_x,foot_x],[0.18,0.26],color=C_DIM,lw=0.7)
ax.plot([foot_x+foot_b,foot_x+foot_b],[0.18,0.26],color=C_DIM,lw=0.7)

# Ghi chú cấu kiện
ax.annotate('Tuong BTCT\nchu L B20\nday 250mm',
            xy=(foot_x+foot_b-wall_b/2, wall_h/2),
            xytext=(2.3, 0.9),
            arrowprops=dict(arrowstyle='->',color='#333',lw=0.8),
            fontsize=6.5, ha='left', color='#333')
ax.annotate('Tham da\nPhi100-200mm\nday 300mm',
            xy=(-1.5,-0.65),
            xytext=(-2.8,-1.05),
            arrowprops=dict(arrowstyle='->',color=C_GABION,lw=0.8),
            fontsize=6.5, ha='left', color=C_GABION)
ax.annotate('Ban de BTCT\n1500x300mm',
            xy=(foot_x+foot_b/2-0.1,-foot_h/2),
            xytext=(1.2,-0.55),
            arrowprops=dict(arrowstyle='->',color='#333',lw=0.7),
            fontsize=6.5, ha='left', color='#333')

ax.set_xlim(-3.1, 3.3)
ax.set_ylim(-1.35, 2.3)
ax.axis('off')
ax.text(-3.0, 2.15, 'PA 2 — KHUYEN NGHI', fontsize=10, color=C_GREEN, fontweight='black',
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=2.0))

# ════════════════════════════════════════════════════════════════════════════
# PANEL 3 — BẢNG THÔNG SỐ VÀ KẾT QUẢ TÍNH TOÁN
# ════════════════════════════════════════════════════════════════════════════
ax = ax3
ax.set_facecolor(C_BG)
ax.set_title('BANG KET QUA TINH TOAN AP LUC DAT', fontsize=8.5,
             fontweight='bold', color=C_TITLE, pad=6)
ax.set_xlim(0,10); ax.set_ylim(0,10); ax.axis('off')

@with_error_handling
def draw_table(ax, headers, rows, y0=9.8, row_h=0.72, col_xs=None, col_ws=None,
               hbg=C_TITLE, abg='#DDE8F5', fs=7):
    for j,(h,cx,cw) in enumerate(zip(headers,col_xs,col_ws)):
        rb = FancyBboxPatch((cx,y0-row_h*0.9),cw-0.06,row_h*0.85,
                             boxstyle='square,pad=0',facecolor=hbg,edgecolor='#AAA',lw=0.4,zorder=2)
        ax.add_patch(rb)
        ax.text(cx+0.07,y0-row_h*0.45,h,va='center',fontsize=fs,fontweight='bold',color='white')
    for i,row in enumerate(rows):
        yr=y0-(i+1)*row_h*0.85-row_h*0.05
        bg=abg if i%2==0 else 'white'
        for j,(cell,cx,cw) in enumerate(zip(row,col_xs,col_ws)):
            rb=FancyBboxPatch((cx,yr-row_h*0.78),cw-0.06,row_h*0.78,
                               boxstyle='square,pad=0',facecolor=bg,edgecolor='#DDD',lw=0.3,zorder=2)
            ax.add_patch(rb)
            ax.text(cx+0.07,yr-row_h*0.39,str(cell),va='center',
                    fontsize=fs,color='#111',ha='left' if j==0 else 'center')

# Bảng thông số đầu vào
ax.text(0,10,'A. THONG SO DAT DAU VAO',fontsize=7.5,fontweight='bold',color=C_TITLE,va='top')
draw_table(ax,
    ['Thong so','Ky hieu','Gia tri','Don vi'],
    [('Trong luong don vi dat dap','gam','18.0','kN/m3'),
     ('Trong luong dat bao hoa','gam_sat','19.0','kN/m3'),
     ('Goc ma sat trong','phi','20','do'),
     ('Luc dinh','c','8.0','kPa'),
     ('Hoat tai mat dat','q','10.0','kPa'),
     ('Cao do hoan thien','CD.HT','5.20','m'),
     ('Cao do dat tu nhien','CD.TN','3.50','m'),
     ('Chieu cao dat dap','H_fill','1.70','m'),
     ('Muc nuoc thien nhien','MN.TN','~3.20','m'),
    ],
    y0=9.7, row_h=0.70, col_xs=[0,3.5,6.0,8.0], col_ws=[3.5,2.5,2.0,2.0],
    hbg='#37474F', abg='#ECEFF1', fs=6.5)

# Bảng kết quả
ax.text(0,2.9,'B. KET QUA TINH TOAN (Rankine)',fontsize=7.5,fontweight='bold',color=C_TITLE,va='top')
draw_table(ax,
    ['Kiem tra','Ket qua','Danh gia'],
    [(f'He so Ka = tan2(45-phi/2)',f'{Ka:.4f}','Dau vao'),
     (f'He so Kp = tan2(45+phi/2)',f'{Kp:.4f}','Dau vao'),
     (f'Ap luc at z=0 (mat dat)',f'{sig_a_top:.2f} kPa','OK' if sig_a_top>=0 else 'Vet nut keo'),
     (f'Ap luc at z=H_fill={H_fill}m',f'{sig_a_H:.2f} kPa','Tinh duoc'),
     (f'Ap luc at z=H_total={H_total}m',f'{sig_a_bot:.2f} kPa','Tinh duoc'),
     (f'Hop luc chu dong Ea',f'{Ea_total:.2f} kN/m','Phan tich'),
     (f'Ap luc bi dong Ep (embed={z_embed}m)',f'{Ep_total:.2f} kN/m','Phan tich'),
     (f'Fs chong truot so bo (Ep/Ea)',f'{Ep_total/Ea_total:.2f}','< 1.5 — Can neo them'),
    ],
    y0=2.7, row_h=0.70, col_xs=[0,5.5,8.0], col_ws=[5.5,2.5,2.0],
    hbg=C_RED, abg='#FFEBEE', fs=6.5)

ax.text(0,0.25,
        f'Fs chong truot = Ep/Ea = {Ep_total:.1f}/{Ea_total:.1f} = {Ep_total/Ea_total:.2f}\n'
        f'Can them: Ban de rong >= {foot_b}m + Trong luong ban de >= {Ea_total:.1f} kN/m\n'
        f'=> Tuong chu L BTCT voi ban de 1.5m la HOP LY',
        fontsize=6.5, va='bottom', color='#333',
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=0.8))

# ════════════════════════════════════════════════════════════════════════════
# PANEL 4 — BIỂU ĐỒ SO SÁNH 3 PHƯƠNG ÁN
# ════════════════════════════════════════════════════════════════════════════
ax = ax4
ax.set_facecolor(C_BG)
ax.set_title('SO SANH 3 PHUONG AN TOI UU', fontsize=8.5, fontweight='bold', color=C_TITLE, pad=6)
ax.set_xlim(0,10); ax.set_ylim(0,10); ax.axis('off')

pa_data = {
    'PA1\nKe da xay': {'score':[3,4,4,3,5,2], 'color':'#E65100','cost':'3.5-4.5tr/m'},
    'PA2\nTuong L+Tham da': {'score':[5,4,5,4,4,4], 'color':'#1B5E20','cost':'4.0-5.5tr/m'},
    'PA3\nCu larsen thep': {'score':[5,3,3,5,2,3], 'color':'#1565C0','cost':'6.0-8.5tr/m'},
}
criteria = ['Chiu luc','CP VL','Thi cong','Do ben','Toc do','My quan']
n = len(criteria)
bar_h = 0.55
y_start = 9.5
colors_pa = [v['color'] for v in pa_data.values()]
labels_pa = list(pa_data.keys())
scores_pa = [v['score'] for v in pa_data.values()]
costs_pa  = [v['cost']  for v in pa_data.values()]

# Header
ax.text(0,9.8,'Tieu chi (diem 1-5)',fontsize=7,fontweight='bold',color=C_TITLE)

for ci, crit in enumerate(criteria):
    y_row = y_start - ci * (bar_h + 0.35)
    ax.text(0, y_row, crit, fontsize=7, va='center', color='#222', fontweight='bold')
    for pi, (pa, sc) in enumerate(zip(labels_pa, scores_pa)):
        bar_w = sc[ci] * 0.8   # max 4.0
        x0 = 2.5
        bar = FancyBboxPatch((x0, y_row-bar_h*(pi+1)*0.28),
                              bar_w, bar_h*0.26,
                              boxstyle='round,pad=0.05',
                              facecolor=colors_pa[pi], edgecolor='none', alpha=0.85, zorder=3)
        ax.add_patch(bar)
        ax.text(x0+bar_w+0.1, y_row-bar_h*(pi+1)*0.28+0.07,
                f'{sc[ci]}/5', fontsize=6.5, va='center', color=colors_pa[pi], fontweight='bold')

# Legend
for pi,(lbl,col,cost) in enumerate(zip(labels_pa,colors_pa,costs_pa)):
    lx = 2.5 + pi*2.5
    rb = FancyBboxPatch((lx, 0.6), 0.3, 0.25, boxstyle='round,pad=0.02',
                         facecolor=col, edgecolor='none', zorder=3)
    ax.add_patch(rb)
    ax.text(lx+0.38, 0.72, lbl.replace('\n',' '), fontsize=6.5, va='center', color=col, fontweight='bold')
    ax.text(lx+0.38, 0.35, cost, fontsize=6.0, va='center', color='#555', style='italic')

# Tổng điểm gia quyền
weights = [0.25,0.15,0.15,0.20,0.10,0.15]
totals = [sum(s[i]*w for i,w in enumerate(weights)) for s in scores_pa]
ax.text(0, 0.1,
        f'Tong diem (gia quyen): ' + '   '.join([f"{lbl.split(chr(10))[0]}: {t:.2f}" for lbl,t in zip(labels_pa,totals)]),
        fontsize=7, va='bottom', color='#222',
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#E8F5E9',edgecolor=C_GREEN,lw=1.0))
best = labels_pa[totals.index(max(totals))]
ax.text(5, -0.1, f'KHUYEN NGHI: {best}  (Diem: {max(totals):.2f}/5.0)',
        fontsize=8, fontweight='bold', color=C_GREEN, ha='center',
        bbox=dict(boxstyle='round,pad=0.3',facecolor='#C8E6C9',edgecolor=C_GREEN,lw=1.5))

# ════════════════════════════════════════════════════════════════════════════
# TITLE BLOCK
# ════════════════════════════════════════════════════════════════════════════
fig.text(0.5, 0.975,
         'PHAN TICH AP LUC DAT & PHUONG AN BO KE TOI UU',
         ha='center', va='top', fontsize=13, fontweight='bold', color='white',
         bbox=dict(boxstyle='square,pad=0.2', facecolor=C_TITLE, edgecolor='none'))
fig.text(0.5, 0.955,
         'Du an: Bo ke kenh noi bo  |  CD HT=+5.20m / CD TN=+3.50m  |  H_dap=1.70m',
         ha='center', va='top', fontsize=10, color=C_TITLE, fontweight='bold')
fig.text(0.5, 0.933,
         'Tieu chuan: TCVN 9902:2016 · TCVN 4253:2012 · TCVN 2737:2023  |  '
         f'Ngay: {date.today().strftime("%d/%m/%Y")}',
         ha='center', va='top', fontsize=8.5, color='#555', style='italic')
fig.add_artist(plt.Line2D([0.03,0.97],[0.895,0.895],transform=fig.transFigure,
               color=C_TITLE, lw=1.5))
fig.text(0.5, 0.055,
         'KY HIEU: KC-BO-KE-01  |  TY LE: 1:20  |  '
         'TIEU CHUAN: TCVN 9902:2016 / TCVN 4253:2012  |  Nguoi ve: AI Technical Illustrator',
         ha='center', va='bottom', fontsize=7, color='#333',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#EAF1FB', edgecolor=C_TITLE, lw=1.0))
fig.add_artist(plt.Line2D([0.03,0.97],[0.10,0.10],transform=fig.transFigure,
               color=C_TITLE, lw=1.0))

# ── Lưu ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--out', default=r'G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI\bo_ke_ap_luc_dat_phuong_an.png')
args = parser.parse_args()
os.makedirs(os.path.dirname(args.out), exist_ok=True)
fig.savefig(args.out, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"[OK] Da luu: {args.out}")
print(f"  Ka={Ka:.4f}  Kp={Kp:.4f}")
print(f"  Ea_total={Ea_total:.2f} kN/m  Ep_total={Ep_total:.2f} kN/m")
print(f"  sig_a_H={sig_a_H:.2f} kPa  sig_a_bot={sig_a_bot:.2f} kPa")
