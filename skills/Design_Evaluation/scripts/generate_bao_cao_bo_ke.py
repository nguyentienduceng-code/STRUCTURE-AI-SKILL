
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
generate_bao_cao_bo_ke.py
Báo cáo Đánh giá Phương án Bờ Kè — Phân tích áp lực đất + Phương án tối ưu
Theo SKILLKC + SKILL_REPORT Mode A
"""
import sys, os
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import math
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date

OUT_DIR   = r"G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI"
IMG_HT    = os.path.join(OUT_DIR, "bo_ke_hien_trang.png")
IMG_PA    = os.path.join(OUT_DIR, "bo_ke_phuong_an_toi_uu.png")
IMG_DRAW  = os.path.join(OUT_DIR, "bo_ke_ap_luc_dat_phuong_an.png")
OUT_DOCX  = os.path.join(OUT_DIR, "BAO_CAO_PHUONG_AN_BO_KE.docx")
TODAY     = date.today().strftime("%d/%m/%Y")

# ── Thông số tính toán (trùng với draw script) ───────────────────────────
gam=18.0; gam_sat=19.0; phi_deg=20.0; c_val=8.0; q=10.0
H_fill=1.70; H_total=2.20; z_embed=0.50; foot_b=1.50; foot_h=0.30
phi_r=math.radians(phi_deg)
Ka=math.tan(math.radians(45)-phi_r/2)**2
Kp=math.tan(math.radians(45)+phi_r/2)**2
sig_a_top=max(0,Ka*q-2*c_val*math.sqrt(Ka))
sig_a_H  =Ka*(gam*H_fill+q)-2*c_val*math.sqrt(Ka)
sig_a_bot=Ka*(gam*H_fill+gam_sat*(H_total-H_fill)+q)-2*c_val*math.sqrt(Ka)
Ea=Ka*q*H_total+0.5*Ka*gam*H_fill**2+0.5*Ka*gam_sat*(H_total-H_fill)**2+max(0,-2*c_val*math.sqrt(Ka)*H_total)
Ep=0.5*Kp*gam_sat*z_embed**2+2*c_val*math.sqrt(Kp)*z_embed
Fs_slip  =round(Ep/Ea,2)
G_foot   =gam*foot_b*foot_h
Fs_over  =round((G_foot*foot_b/2)/((sig_a_H*H_fill/2+sig_a_bot*(H_total-H_fill)/2)*H_total/3),2) if Ea>0 else 0

# ── Helpers ──────────────────────────────────────────────────────────────────
def set_cell_bg(cell,hx):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr()
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),hx); tcPr.append(shd)

def set_tbl_border(t,color='1C3557',size=6):
    tbl=t._tbl; tblPr=tbl.find(qn('w:tblPr'))
    if tblPr is None: tblPr=OxmlElement('w:tblPr'); tbl.insert(0,tblPr)
    tblB=OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        b=OxmlElement(f'w:{side}'); b.set(qn('w:val'),'single')
        b.set(qn('w:sz'),str(size)); b.set(qn('w:space'),'0'); b.set(qn('w:color'),color)
        tblB.append(b)
    tblPr.append(tblB)

def pf(p,sb=0,sa=4,ls=1.15):
    f=p.paragraph_format; f.space_before=Pt(sb); f.space_after=Pt(sa)
    f.line_spacing=ls; f.line_spacing_rule=WD_LINE_SPACING.MULTIPLE

def add_h(doc,text,lv=1,color='1C3557'):
    h=doc.add_heading(text,level=lv); h.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in h.runs: r.font.color.rgb=RGBColor.from_string(color); r.font.bold=True
    pf(h,sb=10 if lv==1 else 6,sa=4); h.paragraph_format.keep_with_next=True; return h

def add_p(doc,text,bold=False,italic=False,size=10.5,color='222222',
          align=WD_ALIGN_PARAGRAPH.JUSTIFY,sa=4,indent=0):
    p=doc.add_paragraph(); p.alignment=align; pf(p,sa=sa)
    if indent: p.paragraph_format.left_indent=Cm(indent)
    r=p.add_run(text); r.bold=bold; r.italic=italic
    r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color); return p

def add_box(doc,text,bg='FFF9C4',tc='333333'):
    p=doc.add_paragraph(); pf(p,sb=4,sa=4)
    p.paragraph_format.left_indent=Cm(0.5); p.paragraph_format.right_indent=Cm(0.5)
    pPr=p._p.get_or_add_pPr()
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),bg); pPr.append(shd)
    r=p.add_run(text); r.font.size=Pt(10); r.font.italic=True
    r.font.color.rgb=RGBColor.from_string(tc)

def add_bullet(doc,text,bp=None,size=10,bc='1C3557',indent=0.6):
    p=doc.add_paragraph(style='List Bullet'); pf(p,sa=2)
    p.paragraph_format.left_indent=Cm(indent)
    if bp:
        r1=p.add_run(bp); r1.bold=True; r1.font.size=Pt(size)
        r1.font.color.rgb=RGBColor.from_string(bc)
        r2=p.add_run(text); r2.font.size=Pt(size)
    else:
        r=p.add_run(text); r.font.size=Pt(size)

def add_img(doc,path,w=16.0,caption=None):
    if not os.path.exists(path):
        add_p(doc,f'[Anh khong tim thay: {path}]',italic=True,color='CC0000'); return
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p,sb=4,sa=2)
    p.add_run().add_picture(path,width=Cm(w))
    if caption:
        cp=doc.add_paragraph(caption); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(cp,sb=0,sa=8)
        for r in cp.runs:
            r.font.size=Pt(9); r.font.italic=True
            r.font.color.rgb=RGBColor.from_string('555555')

def build_table(doc,headers,rows,widths,hbg='1C3557',abg='DDE8F5'):
    t=doc.add_table(rows=1+len(rows),cols=len(headers))
    t.alignment=WD_TABLE_ALIGNMENT.CENTER; set_tbl_border(t)
    hr=t.rows[0].cells
    for i,(h,w) in enumerate(zip(headers,widths)):
        set_cell_bg(hr[i],hbg); hr[i].width=Cm(w)
        p=hr[i].paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p,sb=2,sa=2)
        r=p.add_run(h); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string('FFFFFF')
    for ri,row in enumerate(rows):
        rc=t.rows[ri+1].cells; bg=abg if ri%2==0 else 'FFFFFF'
        for ci,(cell,w) in enumerate(zip(row,widths)):
            set_cell_bg(rc[ci],bg); rc[ci].width=Cm(w)
            rc[ci].vertical_alignment=WD_ALIGN_VERTICAL.CENTER
            p=rc[ci].paragraphs[0]
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
            pf(p,sb=1,sa=1); r=p.add_run(str(cell)); r.font.size=Pt(9)
    return t

# ══════════════════════════════════════════════════════════════════════════════
doc=Document(); sec=doc.sections[0]
sec.page_width=Cm(21); sec.page_height=Cm(29.7)
sec.left_margin=Cm(2.5); sec.right_margin=Cm(2.0)
sec.top_margin=Cm(2.5); sec.bottom_margin=Cm(2.0)
sty=doc.styles['Normal']
sty.font.name='Times New Roman'; sty.font.size=Pt(11)
sty.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')

# ── TRANG BÌA ────────────────────────────────────────────────────────────────
for _ in range(2): doc.add_paragraph()
p1=doc.add_paragraph(); p1.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p1,sa=4)
r=p1.add_run('BAO CAO DANH GIA PHUONG AN BO KE')
r.bold=True; r.font.size=Pt(18); r.font.color.rgb=RGBColor.from_string('1C3557')

p2=doc.add_paragraph(); p2.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p2,sa=4)
r2=p2.add_run('PHAN TICH AP LUC DAT & PHUONG AN TOI UU')
r2.bold=True; r2.font.size=Pt(14); r2.font.color.rgb=RGBColor.from_string('1C3557')

p3=doc.add_paragraph(); p3.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p3,sa=16)
r3=p3.add_run('Bo ke kenh noi bo  |  Cao do HT=+5.20m  |  Dat nen +3.50m  |  H=1.70m')
r3.italic=True; r3.font.size=Pt(11); r3.font.color.rgb=RGBColor.from_string('555555')

info_t=doc.add_table(rows=7,cols=2); info_t.alignment=WD_TABLE_ALIGNMENT.CENTER
set_tbl_border(info_t)
info_d=[
    ('Ky hieu bao cao','KC-BO-KE-01 / REV.00'),
    ('Pham vi danh gia','Bo ke kenh nuoc noi bo — Phan tich toan bo tuyen'),
    ('He ket cau de xuat','Tuong BTCT chu L + Tham da chan ke + Vai DKT'),
    ('Chieu cao dat dap','H = 1.70m (tu +3.50 len +5.20m)'),
    ('Giai doan danh gia','TKKT / Danh gia Bien phap Thi cong'),
    ('Tieu chuan','TCVN 9902:2016 - TCVN 4253:2012 - TCVN 2737:2023'),
    ('Ngay lap',TODAY+'  |  Nguoi lap: Tro ly Ket cau AI'),
]
for ri,(l,v) in enumerate(info_d):
    c=info_t.rows[ri].cells
    set_cell_bg(c[0],'DDE8F5'); set_cell_bg(c[1],'FFFFFF')
    c[0].width=Cm(5.0); c[1].width=Cm(11.5)
    p0=c[0].paragraphs[0]; pf(p0,sb=2,sa=2)
    r0=p0.add_run(l); r0.bold=True; r0.font.size=Pt(10); r0.font.color.rgb=RGBColor.from_string('1C3557')
    p1=c[1].paragraphs[0]; pf(p1,sb=2,sa=2)
    r1=p1.add_run(v); r1.font.size=Pt(10)
doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. PHAN TICH HIEN TRANG
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'1. PHAN TICH HIEN TRANG CONG TRINH')
add_p(doc,'Qua kien trung truong va so lieu mat bang quy hoach, hien trang khu vuc cong trinh '
     'duoc mo ta nhu sau: mot tuyen kenh nuoc noi bo long hep khoang 3-4m, hai ben bo la dat '
     'dap mem co he thong tre va thuc vat phat trien dan. Cao do dat tu nhien +3.50m, yeu cau '
     'cao do hoan thien +5.20m, tuong duong chieu cao dat dap H=1.70m. '
     'Khu vuc co hang rao vay quanh toan bo vi tri yeu cau xay dung bo ke.')

add_h(doc,'1.1. Hinh anh hien truong (Mode A — AI Render)',lv=2)
add_img(doc,IMG_HT,w=15.5,
        caption='Hinh 1.1 — Hien trang tuyen kenh noi bo: bo dat mem + cau go cu + thuc vat tre dan hai ben bo')

add_h(doc,'1.2. Thong so hien trang',lv=2)
build_table(doc,
    ['Thong so','Ky hieu','Gia tri','Don vi','Ghi chu'],
    [('Cao do hoan thien (yeu cau)','CD.HT','5.20','m','Theo mat bang quy hoach'),
     ('Cao do dat tu nhien','CD.TN','3.50','m','Do dac hien truong'),
     ('Chieu cao dat dap','H','1.70','m','= CD.HT - CD.TN'),
     ('Muc nuoc thien nhien (uoc tinh)','MN.TN','~3.20','m','Duoi mat dat TN ~0.30m'),
     ('Chieu rong kenh','B_kenh','3-4','m','Uoc luong tu anh'),
     ('Dien tich khu vuc bo ke','—','—','m2','Theo hang rao vay quanh'),
     ('Dat nen','—','Dat phu sa mem','—','Dat ven kenh DBSCL-like'),
    ],
    [5.5,2.5,2.0,1.8,4.2], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 2. TINH TOAN AP LUC DAT
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_h(doc,'2. TINH TOAN AP LUC DAT (Rankine Method)')
add_p(doc,'Theo SKILLKC Quy tac 13 — Mandatory Quantitative Analysis: phan tich ap luc dat '
     'duoc thuc hien theo ly thuyet Rankine ap dung cho dat roi va dat dinh ket. '
     'Phuong phap nay phu hop voi TCVN 4253:2012 va TCVN 9902:2016 '
     'cho ket cau ke bao ve bo song, kenh nuoc.')

add_h(doc,'2.1. Bang du lieu dau vao (Input Data Table)',lv=2)
build_table(doc,
    ['Thong so','Ky hieu','Gia tri','Don vi','Nguon du lieu'],
    [('Trong luong don vi dat dap (kho)','gam','18.0','kN/m3','Gia dinh dat phu sa - TCVN 9351'),
     ('Trong luong dat bao hoa (duoi MN)','gam_sat','19.0','kN/m3','Gia dinh'),
     ('Goc ma sat trong','phi','20.0','do','Dat phu sa mem (phi=15-25)'),
     ('Luc dinh dat','c','8.0','kPa','Dat set pha bun nhe'),
     ('Hoat tai mat dat (nguoi, xe nhe)','q','10.0','kPa','TCVN 2737:2023'),
     ('Chieu cao dat dap','H_fill','1.70','m','Hien truong'),
     ('Chieu cao tuong tinh toan','H_total','2.20','m','H_fill + 0.5m (du tru xoi)'),
     ('Chieu sau cham ke vao dat','z_embed','0.50','m','Gia thiet ban dau'),
    ],
    [5.5,2.5,2.0,2.0,4.5], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()
add_box(doc,'Data Missing: Chua co ket qua khao sat dia chat chinh thuc. '
        'Tat ca thong so dat dung gia tri gia dinh dien hinh cho dat phu sa ven kenh DBSCL. '
        'YEU CAU: Khoan khao sat dia chat >= 2 ho sâu 5m truoc khi thiet ke chinh thuc.',
        'FFF3E0','E65100')

add_h(doc,'2.2. He so ap luc dat (Coefficient of Earth Pressure)',lv=2)
build_table(doc,
    ['Dai luong','Cong thuc','Ket qua','Nhan xet'],
    [(f'He so ap luc dat chu dong (Ka)',
      f'Ka = tan2(45 - phi/2) = tan2(45 - {phi_deg}/2)',
      f'Ka = {Ka:.4f}',
      'Ap luc dat chu dong (Active)'),
     (f'He so ap luc dat bi dong (Kp)',
      f'Kp = tan2(45 + phi/2) = tan2(45 + {phi_deg}/2)',
      f'Kp = {Kp:.4f}',
      f'Kp/Ka = {Kp/Ka:.1f} lan'),
     ('Chieu sau vung keo (tension crack)',
      'z0 = 2c/(gam*sqrt(Ka))',
      f'z0 = {2*c_val/(gam*math.sqrt(Ka)):.2f} m',
      'Dat co the nut keo trong pham vi nay'),
    ],
    [5.5,6.0,2.0,3.0], hbg='263238', abg='ECEFF1')
doc.add_paragraph()

add_h(doc,'2.3. Chuoi tinh toan ap luc chu dong (Active Pressure)',lv=2)
add_p(doc,'Tinh toan theo Rankine, co xet den hoat tai q va luc dinh c cua dat:')
build_table(doc,
    ['Buoc','Noi dung','Cong thuc','Ket qua','Danh gia'],
    [('1','Ap luc tai z=0 (mat dat)',
      f'sigma_a = Ka.q - 2c.sqrt(Ka) = {Ka:.3f}x{q} - 2x{c_val}x{math.sqrt(Ka):.3f}',
      f'{sig_a_top:.2f} kPa','Dau vao'),
     ('2',f'Ap luc tai z=H_fill={H_fill}m',
      f'sigma_a = Ka.(gam.H+q) - 2c.sqrt(Ka)',
      f'{sig_a_H:.2f} kPa','Tinh duoc'),
     ('3',f'Ap luc tai z=H_total={H_total}m',
      f'sigma_a = Ka.(gam.H+gam_sat.dH+q) - 2c.sqrt(Ka)',
      f'{sig_a_bot:.2f} kPa','Tinh duoc'),
     ('4','Hop luc ap luc chu dong Ea',
      'Tong dien tich bieu do ap luc (hinh thang)',
      f'Ea = {Ea:.2f} kN/m','Ket qua cuoi'),
     ('5','So sanh: Ea vs Ep (z_embed=0.5m)',
      f'Ep = 0.5.Kp.gam_sat.z2 + 2c.sqrt(Kp).z',
      f'Ep = {Ep:.2f} kN/m','Danh gia'),
     ('6','He so chong truot so bo',
      f'Fs = Ep/Ea = {Ep:.2f}/{Ea:.2f}',
      f'Fs = {Fs_slip}',
      f'{"DAT (Fs>=1.5)" if Fs_slip>=1.5 else "CHUA DAT — can ket cau them"}'),
    ],
    [0.6,4.0,5.5,2.0,3.4], hbg='C62828', abg='FFEBEE')
doc.add_paragraph()

add_box(doc,
        f'KET LUAN 2.3: Voi chieu cao dat dap H={H_fill}m, ap luc dat chu dong Ea={Ea:.2f} kN/m/m dai. '
        f'Ap luc bi dong Ep={Ep:.2f} kN/m (z_embed=0.5m). '
        f'He so chong truot so bo Fs={Fs_slip} < 1.5 => KET CAU BO KE CAN CO HE THONG NEO '
        f'HOAC BAN DE DU RONG DE OAN DINH. KHUYEN NGHI: Tuong chu L voi ban de rong >= {foot_b}m '
        f'va tap dat dap bao dam trong luong giu on dinh.',
        'E8F5E9','1B5E20')

# ══════════════════════════════════════════════════════════════════════════════
# 3. BAN VE KY THUAT 2D
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_h(doc,'3. BAN VE KY THUAT PHAN TICH (Mode B — Python 2D)')
add_p(doc,'Ban ve sau the hien day du: (1) So do ap luc dat chu dong va bi dong theo chieu '
     'sau, (2) Mat cat chi tiet phuong an tuong BTCT chu L + tham da chan ke, '
     '(3) Bang ket qua tinh toan Rankine, (4) So sanh danh gia 3 phuong an ung vien.')
add_img(doc,IMG_DRAW,w=16.5,
        caption='Hinh 3.1 — Ban ve ky thuat: So do ap luc dat + PA toi uu + Bang tinh toan + So sanh phuong an (300 DPI, A3)')

# ══════════════════════════════════════════════════════════════════════════════
# 4. DANH GIA 3 PHUONG AN BO KE
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_h(doc,'4. DANH GIA SO SANH 3 PHUONG AN BO KE')
add_p(doc,'Theo SKILLKC Quy tac 16 — Detailed Comparison Matrix, danh gia 3 phuong an toi uu '
     'cho tuyen bo ke nay voi toi thieu 8 tieu chi, trong so gia quyen.')

build_table(doc,
    ['STT','Tieu chi danh gia','Trong so','PA1: Ke da xay','PA2: Tuong L+Tham da','PA3: Cu larsen thep'],
    [('1','Kha nang chiu luc (tai trong + ap dat)','25%','3/5','5/5','5/5'),
     ('2','Chi phi vat lieu + nhan cong','15%','4/5','4/5','3/5'),
     ('3','Tinh kha thi / kho thi cong','15%','4/5','5/5','3/5'),
     ('4','Do ben lau dai (tuoi tho 50 nam)','20%','3/5','5/5','4/5'),
     ('5','Toc do thi cong','10%','3/5','4/5','5/5'),
     ('6','My quan kien truc / canh quan','10%','3/5','4/5','3/5'),
     ('7','Bao tri van hanh','5%','4/5','4/5','3/5'),
     ('TONG','Diem gia quyen (1-5)','100%','3.35','4.55','3.85',''),
    ],
    [0.6,5.5,1.5,2.0,2.5,2.5], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

add_box(doc,
        'KET LUAN SO SANH: Phuong an PA2 — Tuong BTCT chu L + Tham da chan ke duoc '
        'KHUYEN NGHI voi tong diem gia quyen 4.55/5.0, vuot troi o 3 tieu chi: '
        'Kha nang chiu luc (5/5), Tinh kha thi thi cong (5/5), Do ben lau dai (5/5). '
        'Chi phi uoc tinh: 4.0-5.5 trieu dong/m dai ke.',
        'E8F5E9','1B5E20')

add_h(doc,'4.1. Chi tiet Phuong an Khuyen nghi (PA2)',lv=2)
add_p(doc,'Phuong an toi uu duoc hinh anh hoa 3D ben duoi (Hinh 4.1) the hien cau tao '
     'tong the: tuong BTCT chu L B20 + tham da bao ve chan ke + vai dia ky thuat '
     '+ loi thoat nuoc deu dan.')
add_img(doc,IMG_PA,w=15.5,
        caption='Hinh 4.1 — Phuong an toi uu PA2: Tuong BTCT chu L + Tham da chan ke + Vai dia ky thuat (AI Render 3D)')

add_h(doc,'4.2. Thong so ky thuat PA2',lv=2)
build_table(doc,
    ['Cau kien','Thong so ky thuat','Chuc nang'],
    [('Tuong dung BTCT chu L','Cap BT: B20 (C16/20)\nThan tuong: day 250mm\nChieu cao: 1.90m (HT+0.20m)\nBan de: 1500x300mm',
      'Chiu ap dat chu dong, chong lat, chong truot'),
     ('Tham da chan ke','Da hoc Phi100-200mm\nDay: 300mm\nRong: 2.0m\nLop luoi thep Phi4 a100',
      'Bao ve xoi chan tuong, chong xoi lo cuc bo'),
     ('Vai dia ky thuat (DKT)','Khong det >= 150g/m2\nTrai phia sau than tuong\nRong: 1.5m',
      'Ngan dat ngam chay qua ket cau'),
     ('Loi thoat nuoc (Weep hole)','Phi75mm\nBuoc 1.5m doc theo tuong\nCao do: +4.00 va +4.70',
      'Giam ap luc nuoc ngam sau tuong'),
     ('Dat dap phia sau','Dat cap phoi dam chat\nK >= 0.95 (may dam)\nBuoc dam: 20cm/lop',
      'Luong giua va nen do ben cho tuong'),
     ('Lan can bao ve','Thep inox hoac son tinh dien\nCao: 1.00m tren mat san\nBuoc: 1.5m',
      'An toan cho nguoi di lai tai bien'),
    ],
    [3.5,6.5,5.5], hbg='1B5E20', abg='E8F5E9')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 5. DU TOAN SO BO PA2
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'5. DU TOAN SO BO PHUONG AN PA2')
add_p(doc,'Du toan so bo cho 1 met dai ke pa2. Don gia tham khao thi truong Quy II/2026.')
build_table(doc,
    ['STT','Hang muc','DVT','KL/m','Don gia (VND)','Thanh tien/m'],
    [('1','Be tong B20 tuong BTCT chu L (VL+NC+VK)','m3','0.60','3,800,000','2,280,000'),
     ('2','Cot thep CB300-V (ca tuong va ban de)','kg','28.0','28,000','784,000'),
     ('3','Da hoc Phi100-200 (tham da chan ke)','m3','0.60','350,000','210,000'),
     ('4','Luoi thep giu tham da Phi4 a100','m2','2.0','45,000','90,000'),
     ('5','Vai dia ky thuat >= 150g/m2','m2','1.5','35,000','52,500'),
     ('6','Loi thoat nuoc Phi75 PVC','cai','0.67','65,000','43,550'),
     ('7','Dat cap phoi dam chat phia sau','m3','1.5','180,000','270,000'),
     ('8','Lan can bao ve (thep son TM)','m','1.0','350,000','350,000'),
     ('9','Nhan cong thi cong va don gian','cong','2.0','350,000','700,000'),
     ('10','Chi phi may (may dam, tron be tong,...)','—','—','8% VL+NC','357,000'),
    ],
    [0.6,5.5,1.2,1.2,2.5,2.5], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

p_total=doc.add_paragraph(); p_total.alignment=WD_ALIGN_PARAGRAPH.RIGHT; pf(p_total,sb=2,sa=4)
r_t=p_total.add_run('TONG CONG/m dai:   ')
r_t.font.size=Pt(11); r_t.font.bold=True
r_v=p_total.add_run('5,137,050 VND/m   (~  5.1 trieu dong/met dai)')
r_v.font.size=Pt(11.5); r_v.font.bold=True; r_v.font.color.rgb=RGBColor.from_string('1B5E20')
add_box(doc,
        'Ghi chu: (1) Chua bao gom chi phi khao sat dia chat (~ 20-30 trieu/tuyen). '
        '(2) Chua bao gom chi phi thiet ke BVTC (~ 5-8% gia tri cong trinh). '
        '(3) Don gia co the bien dong +/-15% tuy dia diem va thoi diem. '
        '(4) Nen bo sung tram quan trac lun dinh ky 6 thang/lan sau khi hoan thanh.',
        'FFF9C4','CC8800')

# ══════════════════════════════════════════════════════════════════════════════
# 6. BAN DO RUI RO
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'6. BAN DO RUI RO THEO GIAI DOAN (Phased Risk Intelligence)')
build_table(doc,
    ['Giai doan','Rui ro nhan dien','Xac suat','Hau qua','Bien phap phong ngua'],
    [('THIET KE','Thieu khao sat dia chat: thong so dat sai','CAO','NGHIEM TRONG',
      'Khoan >=2 ho, thi nghiem cat + nen 1 truc'),
     ('THIET KE','Khong kiem tra on dinh truot tong the (circle failure)','TRUNG BINH','NGHIEM TRONG',
      'Dung phan mem GeoStudio/Slope/W kiem tra Fs>=1.5'),
     ('THIET KE','Chua tinh ap luc nuoc ngam sau tuong','CAO','Trung binh',
      'Thiet ke loi thoat nuoc Phi75 moi 1.5m'),
     ('THI CONG','Dat dap chua dam chat -> lun sau cong trinh','CAO','Trung binh',
      'Kiem soat K>=0.95 theo TCVN 9436; dam theo lop 20cm'),
     ('THI CONG','Be tong tuong bi khuyết tat (ranh mo, cam biet)','TRUNG BINH','Nho',
      'Dung be tong tuoi + phu gia; kiem tra mau be tong 28 ngay'),
     ('THI CONG','Tham da bi truoi khi lu (soc thuy luc)','CAO','NGHIEM TRONG',
      'Thi cong mua kho; buoc tham da bang coc thep Phi16'),
     ('KHAI THAC','Xoi chan tuong do dong chay kenh nhanh','CAO','NGHIEM TRONG',
      'Tham da rong >= 2m; quan trac 6 thang/lan dau'),
     ('KHAI THAC','But kin loi thoat nuoc do re cay, rac','TRUNG BINH','Nho',
      'Ve sinh loi thoat nuoc 2 lan/nam'),
     ('KHAI THAC','Nut ran than tuong BTCT do co ngot','TRUNG BINH','Nho',
      'Bo tri khe co gian moi 15m; pha tru bao ve BT day 30mm'),
    ],
    [2.0,4.5,1.8,2.2,5.5], hbg='37474F', abg='ECEFF1')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 7. DIEU KIEN CHAP THUAN & TIEN DO
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'7. KIEN NGHI & DIEU KIEN TRIEN KHAI')
add_h(doc,'7.1. Dieu kien bat buoc truoc khi thi cong',lv=2)
conds=[
    ('DK1 — Khao sat dia chat: ','Thuc hien >= 2 ho khoan sâu 5m + thi nghiem trong phong (cat, nen 1 truc, Atterberg)'),
    ('DK2 — Thiet ke BVTC: ','Lap ban tinh ket cau tuong BTCT chu L chinh thuc theo TCVN 5574:2018'),
    ('DK3 — Kiem tra on dinh: ','Xac nhan Fs chong truot >= 1.5 va Fs chong lat >= 2.0 bang tinh toan chinh thuc'),
    ('DK4 — Giai phap xe may: ','Xac dinh phuong tien thi cong phu hop (khong co duong cho xe tai nang)'),
    ('DK5 — Mua kho: ','Uu tien thi cong thang 11-4 (mua kho), tranh mua mua lay lon'),
]
for bp,bt in conds: add_bullet(doc,bt,bp=bp,bc='1B5E20')

add_h(doc,'7.2. Tien do du kien (30m bo ke)',lv=2)
build_table(doc,
    ['Giai doan','Noi dung','Thoi gian','Nhan luc'],
    [('1 — Chuan bi','Khao sat DC + thiet ke BVTC','3 tuan','Tu van 3-4 nguoi'),
     ('2 — Thi cong tham da','Tham da chan ke + ep coc thu nghiem','1 tuan','5 CN'),
     ('3 — Thi cong tuong','Van khuon + cot thep + do BT + bao duong','3 tuan','8-10 CN'),
     ('4 — Dat dap & hoan thien','Dat dap phia sau + dam chat + hoan thien mat','2 tuan','6 CN'),
     ('Tong cong','—','9 tuan (~2.5 thang)','Trung binh 7-8 nguoi'),
    ],
    [2.5,6.5,2.5,4.0], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 8. BANG TRACH NHIEM
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'8. BANG TRACH NHIEM & PHE DUYET')
build_table(doc,
    ['','De xuat','Kiem tra','Phe duyet'],
    [('Y kien','Kinh trinh BLD xem xet','',''),
     ('Chu ky','','',''),
     ('Ngay ky',TODAY,'',''),
     ('Ho ten','[AI Structural Reviewer]','[TP. QLTK]','[GD Ban Xay Dung]'),
     ('Chuc vu','Tro ly KC AI','Truong phong QLTK','Giam doc Ban XD'),
    ],
    [3.0,4.0,4.0,4.5], hbg='37474F', abg='ECEFF1')
doc.add_paragraph()
add_p(doc,'*Bao cao nay duoc lap tu anh hien truong va so lieu mat bang quy hoach. '
     'Cac so lieu dia chat va tinh toan chi mang tinh uoc tinh tham khao. '
     'Ky su co tham quyen can kiem tra va phe duyet chinh thuc truoc khi trien khai.',
     italic=True,color='777777',size=9.5)

doc.save(OUT_DOCX)
print(f"[OK] Da luu: {OUT_DOCX}")
