
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
generate_ncr_ke_buy_dung.py
Phiếu NCR — Sai lệch thi công: Buy đứng dọc vs Thiết kế buy nằm ngang
"""
import sys, os
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date

OUT_DIR  = r"G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI"
IMG_NCR  = os.path.join(OUT_DIR, "NCR_ke_buy_dung_vs_thietke.png")
OUT_DOCX = os.path.join(OUT_DIR, "NCR_KE_BUY_DUNG_DOC.docx")
TODAY    = date.today().strftime("%d/%m/%Y")

# ── Helpers ──────────────────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr()
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),hex_color); tcPr.append(shd)

def set_tbl_border(table, color='1C3557', size=6):
    tbl=table._tbl; tblPr=tbl.find(qn('w:tblPr'))
    if tblPr is None: tblPr=OxmlElement('w:tblPr'); tbl.insert(0,tblPr)
    tblB=OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        b=OxmlElement(f'w:{side}'); b.set(qn('w:val'),'single')
        b.set(qn('w:sz'),str(size)); b.set(qn('w:space'),'0')
        b.set(qn('w:color'),color); tblB.append(b)
    tblPr.append(tblB)

def pf(p,sb=0,sa=4,ls=1.15):
    pf2=p.paragraph_format; pf2.space_before=Pt(sb); pf2.space_after=Pt(sa)
    pf2.line_spacing=ls; pf2.line_spacing_rule=WD_LINE_SPACING.MULTIPLE

def add_h(doc,text,lv=1,color='1C3557'):
    h=doc.add_heading(text,level=lv); h.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in h.runs: r.font.color.rgb=RGBColor.from_string(color); r.font.bold=True
    pf(h,sb=10 if lv==1 else 6,sa=4); h.paragraph_format.keep_with_next=True
    return h

def add_p(doc,text,bold=False,italic=False,size=10.5,color='222222',
          align=WD_ALIGN_PARAGRAPH.JUSTIFY,sa=4):
    p=doc.add_paragraph(); p.alignment=align; pf(p,sa=sa)
    r=p.add_run(text); r.bold=bold; r.italic=italic
    r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color)
    return p

def add_box(doc,text,bg='FFF9C4',border_color='CC8800',text_color='333333'):
    p=doc.add_paragraph(); pf(p,sb=4,sa=4)
    p.paragraph_format.left_indent=Cm(0.4); p.paragraph_format.right_indent=Cm(0.4)
    pPr=p._p.get_or_add_pPr()
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),bg); pPr.append(shd)
    r=p.add_run(text); r.font.size=Pt(10); r.font.italic=True
    r.font.color.rgb=RGBColor.from_string(text_color)

def add_bullet(doc,text,bp=None,size=10,color='1C3557',indent=0.6):
    p=doc.add_paragraph(style='List Bullet'); pf(p,sa=2)
    p.paragraph_format.left_indent=Cm(indent)
    if bp:
        r1=p.add_run(bp); r1.bold=True; r1.font.size=Pt(size)
        r1.font.color.rgb=RGBColor.from_string(color)
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
        p=hr[i].paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf(p,sb=2,sa=2); r=p.add_run(h)
        r.bold=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string('FFFFFF')
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
doc=Document()
sec=doc.sections[0]
sec.page_width=Cm(21); sec.page_height=Cm(29.7)
sec.left_margin=Cm(2.5); sec.right_margin=Cm(2.0)
sec.top_margin=Cm(2.5); sec.bottom_margin=Cm(2.0)
sty=doc.styles['Normal']
sty.font.name='Times New Roman'; sty.font.size=Pt(11)
sty.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')

# ══════════════════════════════════════════════════════════════════════════════
# HEADER NCR
# ══════════════════════════════════════════════════════════════════════════════
p_ncr=doc.add_paragraph(); p_ncr.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p_ncr,sa=3)
r=p_ncr.add_run('PHIEU BAO CAO KHONG PHU HOP (NCR)')
r.bold=True; r.font.size=Pt(18); r.font.color.rgb=RGBColor.from_string('B71C1C')

p_ncr2=doc.add_paragraph(); p_ncr2.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p_ncr2,sa=3)
r2=p_ncr2.add_run('NON-CONFORMANCE REPORT — NCR-PI-01')
r2.bold=True; r2.font.size=Pt(13); r2.font.color.rgb=RGBColor.from_string('B71C1C')

# Thông tin NCR cơ bản
ncr_info=doc.add_table(rows=6,cols=4)
ncr_info.alignment=WD_TABLE_ALIGNMENT.CENTER; set_tbl_border(ncr_info,color='B71C1C')
ncr_fields=[
    ('So NCR:','NCR-PI-01','Ngay phat hien:',TODAY),
    ('Hang muc:','Ke Pi Gieng — Phan Doan C','Giai doan:','Thi cong'),
    ('Nha thau:','Cty TNHH XD & TI Tan Khoa','Phan loai:','MAJOR'),
    ('Nguoi phat hien:','AI Technical Reviewer','Hanh dong yeu cau:','Xu ly trong 48h'),
    ('Chung tu tham chieu:','Ban ve KC-PI-01 REV.00','Tieu chuan:','TCVN 9902:2016'),
    ('Mo ta ngan gon:','Buy BTCT dat dung doc (co vay) thay vi nam ngang (xep chong) theo thiet ke','',''),
]
for ri,(l1,v1,l2,v2) in enumerate(ncr_fields):
    c=ncr_info.rows[ri].cells
    set_cell_bg(c[0],'FFCDD2'); set_cell_bg(c[1],'FFFFFF')
    set_cell_bg(c[2],'FFCDD2'); set_cell_bg(c[3],'FFFFFF')
    for ci,txt in enumerate([l1,v1,l2,v2]):
        p=c[ci].paragraphs[0]; pf(p,sb=2,sa=2)
        rr=p.add_run(txt); rr.font.size=Pt(9.5)
        rr.bold=(ci%2==0); 
        if ci%2==0: rr.font.color.rgb=RGBColor.from_string('B71C1C')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 1. MÔ TẢ SAI LỆCH
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'1. MO TA SAI LECH THI CONG',lv=1,color='B71C1C')
add_p(doc,'Qua anh hien truong ngay '+TODAY+', nhan thay cac buy BTCT (co duong kinh Phi400mm) '
     'dang duoc thi cong dung dung doc sat nhau, tao thanh mot hang tuong kieu COC VAY TIEP XUC '
     '(Contiguous Pile Wall). Day la phuong phap KHAC HOAN TOAN so voi thiet ke goc yeu cau '
     'buy phai xep nam ngang, chong len nhau 4 hang (phuong an ke pi gieng truyen thong).')

add_box(doc,'THIET KE GOC (Ban ve KC-PI-01): Buy nam ngang — xep chong 4 hang (H=1.68m) '
        '+ Coc thep neo V100 + Giang BTCT Pi neo L>=3-4m.\n'
        'THUC TE THI CONG: Buy dung dung — sat nhau kieu coc vay tiep xuc + Dam dinh BTCT tren dinh. '
        'CHUA THAY co coc V100 va giang neo Pi neo.',
        'FFEBEE','B71C1C','B71C1C')

# ══════════════════════════════════════════════════════════════════════════════
# 2. BAN VE PHAN TICH
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'2. BAN VE PHAN TICH SO SANH',lv=1,color='B71C1C')
add_img(doc,IMG_NCR,w=16.0,
        caption='Hinh 2.1 — So sanh: Buy dung doc (thuc te / NCR MAJOR) vs Buy nam ngang (thiet ke goc) '
                '— Phan tich mat cat + mat bang + bang so sanh')

# ══════════════════════════════════════════════════════════════════════════════
# 3. PHAN TICH KY THUAT TUONG DUNG DOC
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'3. PHAN TICH KY THUAT — CAU KIEN BUY DUNG DOC',lv=1)
add_p(doc,'Neu chap nhan buy dung doc nhu thuc te, can danh gia lai hoan toan so do '
     'chiu luc vi day la he KHAC BIET co ban:')

add_h(doc,'3.1. So do chiu luc moi (Contiguous Pile Wall)',lv=2)
add_bullet(doc,'Moi buy dung la MOT COC don lap, chiu uon nhu console ngam trong dat phia duoi','Co che: ')
add_bullet(doc,'Luc ngang (ap luc dat + song) => Uon buy xung quanh truc doc (yeu - buy hinh tron it chiu uon)','Luc ngang: ')
add_bullet(doc,'Dam dinh tren cung chiu uon ngang, truyen luc ve cac coc','Dam dinh: ')
add_bullet(doc,'Khe ho giua cac buy => DAT PHIA SAU CO THE CHAY QUA => xoi ngam','Khe ho: ')

add_h(doc,'3.2. Kiem tra dieu kien chiu luc buy dung (so bo)',lv=2)
build_table(doc,
    ['Kiem tra','Cong thuc/Tham so','Ket qua','Danh gia'],
    [('Momen uon tai chan buy',
      'M = Ea x H/3 = 12.5 x 0.56',
      'M = 7.0 kN.m/buy',
      'Can kiem tra'),
     ('Suc chiu uon buy Phi400 tuong',
      'Wu = (pi/32)x(D4-d4)/D x fct\n'
      'BTCT B20: fct=1.05 MPa',
      'Wu = ~0.4 kN.m (khong co thep doc)\n'
      '~2.5 kN.m (co thep doc 6Phi12)',
      'KHONG DAT neu khong co thep doc'),
     ('Chieu sau ngam can thiet (Broms)',
      'L_ngam >= 1.5 x H = 1.5 x 1.6',
      'L_ngam >= 2.4m',
      'CHUA RO chieu sau thuc te'),
     ('Khe ho giua buy',
      'Gap = 0 (ly thuyet tiep xuc)\n'
      'Thuc te: co khe 5-20mm',
      'Dat co the chay qua khe',
      'NGUY HIEM - can bit kin'),
     ('On dinh chong lat toan tuong',
      'Phu thuoc dam dinh + ket noi',
      'Chua co tinh toan',
      'YEU CAU tinh toan lai'),
    ],
    [4.5,5.5,3.0,3.0], hbg='B71C1C', abg='FFEBEE')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 4. BANG SO SANH HAI PHUONG AN
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'4. BANG SO SANH: THIET KE vs THUC TE',lv=1)
build_table(doc,
    ['Tieu chi','THIET KE GOC (Buy nam)\n[Dung]','THUC TE (Buy dung)\n[Sai lech]','Muc do anh huong'],
    [('Phuong dat buy','Nam ngang — xep chong 4 hang','Dung doc — sat nhau kieu coc','CRITICAL thay doi'),
     ('Chieu cao tuong','H = 4 buy x 0.42m = 1.68m','H = 1.6-2.0m (phan noi)','Tuong duong'),
     ('So do chiu luc','Tuong trong luc (Gravity wall)','Coc vay tiep xuc','KHAC HOAN TOAN'),
     ('Chieu sau nen','Vua lot day + dat nen','Cam buy vao dat (chua ro sau)','Can xac nhan'),
     ('Coc thep V100','Bat buoc - moi 4 buy x 1 coc','KHONG THAY tren hien truong','NGUY HIEM'),
     ('Giang BTCT Pi neo','Bat buoc - L>=3-4m, a=5-7m','KHONG THAY','NGUY HIEM'),
     ('Dam dinh','Khong co','CO dam dinh BTCT phia tren','Bo sung them'),
     ('Vai dia ky thuat','Co - 0.4x2.4m phia sau','Chua xac nhan','Kiem tra them'),
     ('Khe ho tuong','Kin (buy chong nhau)','Co khe ho giua cac buy','Nguy co xoi ngam'),
     ('Chi phi uoc tinh','2.7 trieu/m (goc)','2.2-3.0 trieu/m (uoc tinh)','Tuong duong'),
    ],
    [4.0,4.0,4.0,3.5], hbg='37474F', abg='ECEFF1')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 5. DANH GIA NGUY CO
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'5. DANH GIA NGUY CO DAC THU — BUY DUNG DOC',lv=1)
build_table(doc,
    ['#','Nguy co','Muc do','Bien phap xu ly'],
    [('1','Buy bi lat khi ap dat lon (khong co coc V100)\nFs chong lat co the < 1.0','DO',
      'Kiem tra ngay chieu sau cam buy\nBo sung coc V100 neu thieu'),
     ('2','Xoi ngam qua khe ho giua buy\nDat phia sau chay ra phia song','DO',
      'Bit kin khe ho bang vua xi mang\nBosung vai DKT phia sau'),
     ('3','Buy bi nhoi bat khi muc nuoc that nuoc nhanh\n(ap luc nuoc nguoc)','CAO',
      'Dam bao chieu sau ngam >= 1.5D = 600mm\nKiem tra tai hien truong'),
     ('4','Dam dinh khong du kha nang truyen luc\nngang ve he neo (neu khong co coc V100)','CAO',
      'Tinh kiem tra dam dinh\nHoan chinh ban tinh ket cau dam dinh'),
     ('5','An mon coc thep V100 (neu co) trong moi truong nuoc\nKhong duoc son chong gi','TRUNG BINH',
      'Kiem tra co/khong co coc\nYeu cau son Epoxy 3 lop neu co'),
    ],
    [0.6,5.5,2.0,7.4], hbg='B71C1C', abg='FFEBEE')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 6. YEU CAU XU LY
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'6. YEU CAU XU LY (TRONG 48H)',lv=1,color='B71C1C')
add_box(doc,
        'HANH DONG YEU CAU NGAY:\n'
        '1. DUNG THI CONG phan con lai chua thuc hien — cho den khi co phuong an ky thuat duoc duyet lai.\n'
        '2. Do dac chieu sau cam buy hien tai: can >= 600mm (1.5D) vao dat nen co dinh.\n'
        '3. Xac nhan tren hien truong: co hay khong co coc thep V100? Neu khong — YEU CAU bo sung.\n'
        '4. Bit kin khe ho giua cac buy hien tai bang vua M200 truoc khi de dat phia sau.\n'
        '5. Nha thau Tan Khoa cung cap "Ban tinh ket cau tuong buy dung doc" de AI review ky thuat.\n'
        '6. Chup anh hien truong toan doan — lap ho so hoan cong phan da thi cong.',
        'FFEBEE','B71C1C','B71C1C')

add_h(doc,'6.1. Phuong an chap nhan co dieu kien (neu buy dung da thi cong)',lv=2)
add_p(doc,'Neu khong the thi cong lai toan bo, co the chap nhan buy dung voi cac DIEU KIEN bat buoc:')
conds=[
    ('DK1 — Chieu sau cam: ','Tat ca buy phai cam sau >= 600mm (1.5D) vao dat nen on dinh phia duoi muc xoi'),
    ('DK2 — Coc neo bac sau: ','Bo sung coc thep V100 xuyen qua khe giua cac buy, cham sau 1.5-2m, buoc 2.0m'),
    ('DK3 — Giang neo: ','Bo sung giang BTCT neo (300x300 / 4Phi12) phia sau, L>=2.5m, buoc 4m'),
    ('DK4 — Bit kin khe: ','But toan bo khe ho giua buy bang vua xi mang mac cao M300'),
    ('DK5 — Dam dinh du manh: ','Dam dinh hien tai can kiem tra va co the phai tang tiet dien len 300x400mm'),
    ('DK6 — Ban tinh phe duyet: ','Bat buoc co ban tinh ket cau coc vay moi duoc thi cong tiep'),
]
for bp,bt in conds:
    add_bullet(doc,bt,bp=bp,color='B71C1C')

# ══════════════════════════════════════════════════════════════════════════════
# 7. BANG PHAN TICH KINH TE (THAM KHAO)
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'7. DU TOAN BO SUNG (neu chap nhan buy dung voi dieu kien)',lv=1)
build_table(doc,
    ['STT','Hang muc bo sung','DVT','SL/m','Don gia (VND)','Thanh tien/m'],
    [('1','Coc thep V100 bo sung (cam qua khe buy)','cay/m','0.5','1,800,000','900,000'),
     ('2','Nhan cong dong coc V100 bo sung','cong','0.5','350,000','175,000'),
     ('3','Vua bit kin khe giua buy M300','lit/m','8.0','15,000','120,000'),
     ('4','Giang BTCT neo 300x300 B20 (bo sung)','m3/m','0.09','3,800,000','342,000'),
     ('5','Thep giang 4Phi12/Phi6a300 bo sung','kg/m','0.3','28,000','8,400'),
     ('6','Vai dia ky thuat phia sau (neu chua co)','m2/m','0.5','35,000','17,500'),
     ('7','Nhan cong kiem tra + do dac chieu sau buy','cong/m','0.2','350,000','70,000'),
    ],
    [0.6,6.0,1.2,1.2,2.5,3.0], hbg='37474F', abg='ECEFF1')
doc.add_paragraph()

p_total=doc.add_paragraph(); p_total.alignment=WD_ALIGN_PARAGRAPH.RIGHT; pf(p_total,sb=2,sa=4)
r_total=p_total.add_run('TONG CHI PHI BO SUNG (moi met dai):   ')
r_total.font.size=Pt(11); r_total.font.bold=True
r_val=p_total.add_run('~  1,632,900 VND/m   (them vao gia goc ~2.7 trieu/m)')
r_val.font.size=Pt(11.5); r_val.font.bold=True; r_val.font.color.rgb=RGBColor.from_string('B71C1C')

p_tong=doc.add_paragraph(); p_tong.alignment=WD_ALIGN_PARAGRAPH.RIGHT; pf(p_tong,sa=6)
r_tong=p_tong.add_run('=> Tong chi phi cua phuong an ke dung sau khi bo sung:   ~4.3 trieu/m  x  30m  =  ~129 trieu dong')
r_tong.font.size=Pt(10); r_tong.italic=True; r_tong.font.color.rgb=RGBColor.from_string('555555')

# ══════════════════════════════════════════════════════════════════════════════
# 8. BANG TRACH NHIEM
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'8. BANG TRACH NHIEM & THEO DOI NCR',lv=1)
build_table(doc,
    ['','De xuat xu ly','Ky thuat kiem tra','Nha thau thuc hien','Phe duyet'],
    [('Y kien','Trinh BJD xem xet','Ky thuat XN ket qua','NT Tan Khoa xu ly',''),
     ('Chu ky','','','',''),
     ('Ngay ky',TODAY,'','',''),
     ('Ho ten','[AI Technical Reviewer]','[TP.QLTK]','[Giam doc NT Tan Khoa]','[GD Ban XD]'),
     ('Chuc vu','Tro ly KC AI','Truong phong QLTK','Nha thau chiu trach nhiem','Giam doc Ban XD'),
    ],
    [3.0,3.5,3.0,3.5,3.5], hbg='B71C1C', abg='FFEBEE')

doc.add_paragraph()
add_p(doc,'*Bao cao NCR nay duoc lap tu phan tich anh chup hien truong ngay '+TODAY+'. '
     'Ket luan ky thuat can duoc xac nhan lai boi ky su co tham quyen khi kiem tra truc tiep '
     'tai cong truong truoc khi ban hanh chinh thuc.',
     italic=True,color='777777',size=9.5)

doc.save(OUT_DOCX)
print(f"[OK] Da luu: {OUT_DOCX}")
