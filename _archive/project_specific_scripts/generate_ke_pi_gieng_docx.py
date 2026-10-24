
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
generate_ke_pi_gieng_docx.py
Báo cáo Đánh giá Kỹ thuật — Phương án Kè Pi Giếng Nhà Thầu Tấn Khoa
Theo SKILLKC + SKILL_REPORT — Mode A (Chuyên gia kết cấu)
"""
import sys, os
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date

# ── Đường dẫn mặc định ────────────────────────────────────────────────────────
OUT_DIR   = r"G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI"
IMG_3D    = os.path.join(OUT_DIR, "ke_pi_gieng_phoi_canh_3d.png")
IMG_TC    = os.path.join(OUT_DIR, "ke_pi_gieng_thi_cong.png")
IMG_DRAW  = os.path.join(OUT_DIR, "ke_pi_gieng_technical_drawing.png")
OUT_DOCX  = os.path.join(OUT_DIR, "BAO_CAO_DANH_GIA_KE_PI_GIENG.docx")
TODAY     = date.today().strftime("%d/%m/%Y")

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS (giống generate_tham_da_docx.py)
# ══════════════════════════════════════════════════════════════════════════════
def set_cell_bg(cell, hex_color):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
    shd.set(qn('w:fill'), hex_color); tcPr.append(shd)

def set_tbl_border(table, color='1C3557', size=6):
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None: tblPr = OxmlElement('w:tblPr'); tbl.insert(0,tblPr)
    tblBorders = OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'),'single'); b.set(qn('w:sz'),str(size))
        b.set(qn('w:space'),'0'); b.set(qn('w:color'),color)
        tblBorders.append(b)
    tblPr.append(tblBorders)

def pf(para, sb=0, sa=4, ls=1.15):
    p = para.paragraph_format
    p.space_before=Pt(sb); p.space_after=Pt(sa)
    p.line_spacing=ls; p.line_spacing_rule=WD_LINE_SPACING.MULTIPLE

def add_h(doc, text, lv=1, color='1C3557'):
    h = doc.add_heading(text, level=lv)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in h.runs:
        r.font.color.rgb = RGBColor.from_string(color); r.font.bold=True
    pf(h, sb=10 if lv==1 else 6, sa=4)
    h.paragraph_format.keep_with_next = True
    return h

def add_p(doc, text, bold=False, italic=False, size=10.5, color='222222',
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=0, sa=4):
    p = doc.add_paragraph(); p.alignment=align; pf(p,sa=sa)
    if indent: p.paragraph_format.left_indent=Cm(indent)
    r = p.add_run(text); r.bold=bold; r.italic=italic
    r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color)
    return p

def add_bullet(doc, text, bp=None, size=10, indent=0.6):
    p = doc.add_paragraph(style='List Bullet'); pf(p,sa=2)
    p.paragraph_format.left_indent=Cm(indent)
    if bp:
        r1=p.add_run(bp); r1.bold=True; r1.font.size=Pt(size)
        r1.font.color.rgb=RGBColor.from_string('1C3557')
        r2=p.add_run(text); r2.font.size=Pt(size)
    else:
        r=p.add_run(text); r.font.size=Pt(size)
    return p

def add_box(doc, text, bg='FFF9C4', border='CC8800'):
    p=doc.add_paragraph(); pf(p,sb=4,sa=4)
    p.paragraph_format.left_indent=Cm(0.5); p.paragraph_format.right_indent=Cm(0.5)
    pPr=p._p.get_or_add_pPr()
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),bg); pPr.append(shd)
    r=p.add_run(text); r.font.size=Pt(10); r.font.italic=True
    r.font.color.rgb=RGBColor.from_string('333333')

def add_img(doc, path, w=15.0, caption=None):
    if not os.path.exists(path):
        add_p(doc, f'[Ảnh không tìm thấy: {path}]', italic=True, color='CC0000'); return
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pf(p,sb=4,sa=2)
    p.add_run().add_picture(path, width=Cm(w))
    if caption:
        cp=doc.add_paragraph(caption); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf(cp,sb=0,sa=8)
        for r in cp.runs:
            r.font.size=Pt(9); r.font.italic=True
            r.font.color.rgb=RGBColor.from_string('555555')

def build_table(doc, headers, rows, widths, hbg='1C3557', abg='DDE8F5'):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.alignment=WD_TABLE_ALIGNMENT.CENTER; set_tbl_border(t)
    hr = t.rows[0].cells
    for i,(h,w) in enumerate(zip(headers,widths)):
        set_cell_bg(hr[i],hbg); hr[i].width=Cm(w)
        p=hr[i].paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf(p,sb=2,sa=2); r=p.add_run(h)
        r.bold=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string('FFFFFF')
    for ri,row in enumerate(rows):
        rc=t.rows[ri+1].cells
        bg=abg if ri%2==0 else 'FFFFFF'
        for ci,(cell,w) in enumerate(zip(row,widths)):
            set_cell_bg(rc[ci],bg); rc[ci].width=Cm(w)
            rc[ci].vertical_alignment=WD_ALIGN_VERTICAL.CENTER
            p=rc[ci].paragraphs[0]
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
            pf(p,sb=1,sa=1); r=p.add_run(str(cell)); r.font.size=Pt(9)
    return t

# ══════════════════════════════════════════════════════════════════════════════
doc = Document()
section=doc.sections[0]
section.page_width=Cm(21); section.page_height=Cm(29.7)
section.left_margin=Cm(2.5); section.right_margin=Cm(2.0)
section.top_margin=Cm(2.5); section.bottom_margin=Cm(2.0)
style=doc.styles['Normal']
style.font.name='Times New Roman'; style.font.size=Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')

# ══════════════════════════════════════════════════════════════════════════════
# TRANG BÌA
# ══════════════════════════════════════════════════════════════════════════════
for _ in range(2): doc.add_paragraph()

# Header dải màu
p_top=doc.add_paragraph(); p_top.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p_top.add_run('BÁO CÁO ĐÁNH GIÁ KỸ THUẬT — KẾT CẤU')
r.bold=True; r.font.size=Pt(18); r.font.color.rgb=RGBColor.from_string('1C3557')
pf(p_top,sa=6)

p_sub=doc.add_paragraph(); p_sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
r2=p_sub.add_run('PHƯƠNG ÁN KÈ PI GIẾNG (KÈ BUY BÊ TÔNG)')
r2.bold=True; r2.font.size=Pt(14); r2.font.color.rgb=RGBColor.from_string('1C3557')
pf(p_sub,sa=4)

p_nt=doc.add_paragraph(); p_nt.alignment=WD_ALIGN_PARAGRAPH.CENTER
r3=p_nt.add_run('Nhà Thầu Tấn Khoa — Phân Đoạn C  |  Chống xói lở bờ sông / Kè chắn đất')
r3.italic=True; r3.font.size=Pt(11); r3.font.color.rgb=RGBColor.from_string('555555')
pf(p_nt,sa=18)

info_t=doc.add_table(rows=7,cols=2); info_t.alignment=WD_TABLE_ALIGNMENT.CENTER
set_tbl_border(info_t)
info_data=[
    ('Ký hiệu báo cáo',   'KC-DANH-GIA-PI-01 / REV.00'),
    ('Phạm vi đánh giá',  'Phương án kè Pi Giếng — Phân Đoạn C'),
    ('Hệ kết cấu',        'Buy BTCT Φ400 + Cọc thép V100 + Giằng BTCT neo'),
    ('Chiều cao kè',      '≈ 1.68÷2.0m (4 hàng buy, cao TB)'),
    ('Giai đoạn',         'Đánh giá Biện pháp Thi công / TKKT'),
    ('Tiêu chuẩn áp dụng','TCVN 9902:2016 · TCVN 5574:2018 · TCVN 2737:2023'),
    ('Ngày lập',          TODAY + '  |  Người lập: Trợ lý Kết cấu AI'),
]
for ri,(lbl,val) in enumerate(info_data):
    c=info_t.rows[ri].cells
    set_cell_bg(c[0],'DDE8F5'); set_cell_bg(c[1],'FFFFFF')
    c[0].width=Cm(5.5); c[1].width=Cm(11.0)
    p0=c[0].paragraphs[0]; pf(p0,sb=2,sa=2)
    r0=p0.add_run(lbl); r0.bold=True; r0.font.size=Pt(10)
    r0.font.color.rgb=RGBColor.from_string('1C3557')
    p1=c[1].paragraphs[0]; pf(p1,sb=2,sa=2)
    r1=p1.add_run(val); r1.font.size=Pt(10)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. MÔ TẢ PHƯƠNG ÁN
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'1. MÔ TẢ PHƯƠNG ÁN KÈ PI GIẾNG',lv=1)
add_p(doc,'Phương án kè Pi Giếng do Nhà Thầu Tấn Khoa đề xuất áp dụng cho Phân Đoạn C '
     'là hệ kết cấu kè chắn đất chống xói lở bờ sông kết hợp giữa:'
     ' (1) Tường chắn bằng buy bê tông đúc sẵn xếp chồng,'
     ' (2) Hệ thống cọc thép định hình neo giữ tường,'
     ' (3) Giằng BTCT neo dạng deadman kéo sâu vào nền đất.'
     ' Đây là giải pháp thi công linh hoạt, không cần thiết bị hạng nặng, phù hợp điều kiện '
     'bờ sông có mực nước dao động, nhân công phổ thông.')

add_h(doc,'1.1. Các Cấu Kiện Chính',lv=2)
build_table(doc,
    ['#','Cấu kiện','Thông số kỹ thuật','Chức năng'],
    [('1','Buy BTCT đúc sẵn','Φ400mm · BTCT B20 · đúc sẵn\nXếp chồng 4 hàng (H≈1.68m)\nTrong lòng đổ vữa 1 bao XM/buy','Tạo mặt tường chắn chịu áp đất và sóng'),
     ('2','Cọc thép neo V100','Thép V100 (I-section 100mm)\nL=6m · cắm sâu đất 1.5÷2m\nKhoảng cách trung bình mỗi 4 buy','Neo giữ tường buy, chịu lực ngang'),
     ('3','Cụm neo V50','Thép hộp V50 · 100×100mm\nHàn vào cọc V100','Liên kết tường buy vào cọc thép'),
     ('4','Giằng BTCT neo (Pi neo)','300×300mm · 4Φ12 / Φ6a300 · B20\nL≥3÷4m · Bước neo a=5÷7m\nMĩ kéo sâu vào nền đất đắp','Deadman anchor — chống lật toàn bộ tường'),
     ('5','Vải địa kỹ thuật','0.4×2.4m · Không dệt ≥150g/m²\nĐặt sau lưng tường buy','Ngăn đất ngầm chảy qua khe mối buy'),
     ('6','Lớp vữa lót đáy','Vữa M75 · dày >1m tạo phẳng','Phân bố đều áp lực đáy tường lên nền'),
    ],
    [1.0,3.5,6.0,4.0], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 2. HÌNH ẢNH PHỐI CẢNH 3D
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'2. HÌNH ẢNH PHỐI CẢNH PHƯƠNG ÁN',lv=1)
add_p(doc,'Hình 2.1 mô phỏng trực quan phương án kè Pi Giếng hoàn chỉnh tại '
     'công trình gia cố bờ sông, thể hiện cấu trúc không gian 3 chiều của hệ tường '
     'buy BTCT, cọc thép neo và giằng neo ăn sâu vào phía đất đắp.')
add_img(doc, IMG_3D, w=15.5,
        caption='Hình 2.1 — Phối cảnh 3D tổng thể phương án kè Pi Giếng Nhà Thầu Tấn Khoa — Phân Đoạn C')

add_p(doc,'Hình 2.2 thể hiện quy trình thi công theo trình tự 4 giai đoạn trên công trường '
     'thực tế: chuẩn bị nền → đóng cọc thép → xếp buy → kết nối cụm neo V50.')
add_img(doc, IMG_TC, w=15.5,
        caption='Hình 2.2 — Cảnh thi công thực tế phương án kè Pi Giếng theo trình tự 4 bước')

# ══════════════════════════════════════════════════════════════════════════════
# 3. BẢN VẼ KỸ THUẬT 2D CHI TIẾT
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_h(doc,'3. BẢN VẼ KỸ THUẬT CHI TIẾT 2D',lv=1)
add_p(doc,'Bản vẽ kỹ thuật bên dưới (Hình 3.1) thể hiện đầy đủ: mặt cắt chi tiết kè '
     'tỷ lệ 1:25 (trái), chi tiết tiết diện giằng BTCT neo 300×300mm tỷ lệ 1:10 (trên phải), '
     'chi tiết cụm neo V50 mặt bằng và bảng vật liệu chính (dưới phải).')
add_img(doc, IMG_DRAW, w=16.5,
        caption='Hình 3.1 — Bản vẽ kỹ thuật chi tiết kè Pi Giếng A3 (Tỷ lệ 1:25 & 1:10) — 300 DPI')

# ══════════════════════════════════════════════════════════════════════════════
# 4. ĐÁNH GIÁ KỸ THUẬT (SKILLKC)
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_h(doc,'4. ĐÁNH GIÁ KỸ THUẬT CHUYÊN SÂU',lv=1)
add_p(doc,'Đánh giá theo SKILLKC — Quy tắc 13: Mandatory Quantitative Analysis Protocol '
     'và Quy tắc 9: Constructability Check.')

add_h(doc,'4.1. Bảng Dữ Liệu Đầu Vào (Input Data Table)',lv=2)
build_table(doc,
    ['Thông số','Ký hiệu','Giá trị','Đơn vị','Nguồn'],
    [('Chiều cao tường buy','H','1.68 (4 hàng)','m','Bản vẽ NT.01'),
     ('Đường kính buy BTCT','D_buy','400','mm','Bản vẽ NT.01'),
     ('Số hàng buy xếp chồng','n','4','hàng','Bản vẽ NT.01'),
     ('Chiều dài cọc thép V100','L_coc','6.0','m','Bản vẽ NT.01'),
     ('Chiều sâu cắm đất','L_embed','1.5÷2.0','m','Bản vẽ NT.01'),
     ('Tiết diện giằng BTCT','b×h','300×300','mm','CT. giằng'),
     ('Cốt thép giằng','—','4Φ12 / Φ6a300','—','CT. giằng'),
     ('Bước neo Pi neo','a','5÷7','m','Bản vẽ NT.01'),
     ('Chiều dài giằng neo','L_gang','≥ 3÷4','m','Bản vẽ NT.01'),
     ('Cấp bê tông giằng','B','B20 (C16/20)','—','Bản vẽ NT.01'),
     ('Trọng lượng đơn vị đất','γ_d','18.0','kN/m³','Giả định điển hình'),
     ('Góc ma sát trong','φ','20°','deg','Data Missing — cần kết quả ĐC'),
     ('Lực dính đất','c','10','kPa','Data Missing — cần kết quả ĐC'),
    ],
    [5.0,2.5,2.5,2.0,3.5], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

add_box(doc,
        '⚠ Data Missing: Chua co ket qua khao sat dia chat (DC). '
        'Cac thong so y, phi, c dung gia tri gia dinh dien hinh cho dat ven song '
        'vung DBSCL. YEU CAU bo sung ho so khao sat DC truoc khi phe duyet PA chinh thuc.',
        'FFF3E0', 'E65100')

add_h(doc,'4.2. Kiểm Tra Ổn Định Chống Lật (Overturning Check)',lv=2)
add_p(doc,'Kiểm tra cơ bản điều kiện chống lật của tường buy quanh chân tường, '
     'với giả định tải trọng áp lực đất tĩnh theo lý thuyết Rankine/Coulomb.')

build_table(doc,
    ['Nội dung kiểm tra','Công thức/Giá trị','Kết quả','Đánh giá'],
    [('Chiều cao chịu áp đất','H = 1.68m (4 buy)','H = 1.68m','Đầu vào'),
     ('Áp lực đất chủ động Ka','Ka = tan²(45°-φ/2) = tan²35° = 0.49','Ka = 0.49','Đầu vào'),
     ('Hợp lực áp đất ngang','Ea = ½·γ·H²·Ka = ½×18×1.68²×0.49','Ea = 12.5 kN/m','Tính được'),
     ('Mô-men lật (quanh chân)','Ml = Ea × H/3 = 12.5 × 0.56','Ml = 7.0 kN.m/m','Tính được'),
     ('Trọng lượng tường buy/m','G = n × π×R²×γ_bt×1m = 4×π×0.04×25×1','G ≈ 12.6 kN/m','Tính được'),
     ('Mô-men giữ','Mg = G × D/2 = 12.6 × 0.2','Mg = 2.5 kN.m/m','Tính được'),
     ('Hệ số chống lật (không neo)','Fs = Mg/Ml = 2.5/7.0','Fs = 0.36 < 1.5','🔴 KHÔNG ĐẠT'),
     ('Lực neo cần thiết từ cọc V100','T_neo = (Ml - Mg)/H × FSmin','T_neo ≈ 5.4 kN/m','Yêu cầu neo'),
     ('Lực neo cung cấp bởi cọc V100','Phụ thuộc chiều sâu cắm 1.5÷2m và đất','Cần kiểm tra chi tiết','⚠ Kiểm tra thêm'),
     ('Hệ số chống lật (CÓ cọc neo V100)','Fs ≥ 1.5 khi cọc đủ sức chịu ngang','Phụ thuộc ĐC','🟡 Cần xác nhận'),
    ],
    [5.5,6.0,2.5,2.5], hbg='C62828', abg='FFEBEE')
doc.add_paragraph()

add_box(doc,'📌 KẾT LUẬN 4.2: Không có cọc thép neo V100, tường buy BTCT KHÔNG ổn định '
        'chống lật (Fs=0.36). Cọc thép V100 là cấu kiện SỐNG CÒN của phương án này. '
        'Cần kiểm tra chi tiết sức chịu tải ngang của cọc V100 theo TCVN 9362:2012.')

add_h(doc,'4.3. Kiểm Tra Hệ Thống Giằng Neo Pi Neo',lv=2)
build_table(doc,
    ['Thông số','Công thức','Giá trị','Đánh giá'],
    [('Lực neo yêu cầu mỗi Pi neo','T = T_neo × a = 5.4 × 6','T_yc = 32.4 kN','Yêu cầu'),
     ('Sức chịu kéo giằng 4Φ12 B20','Nt = As×fy = 4×113×300 MPa','Nt = 135.6 kN','✅ Đủ sức chịu'),
     ('Kiểm tra tiết diện giằng (nén)','σ = N/A ≈ 32.4/(0.3×0.3)×10³','σ = 360 kPa << 16 MPa','✅ Rất nhỏ'),
     ('Chiều dài neo cần thiết','L_min theo lý thuyết pullout','≥ 2.5m','🟡 L=3÷4m ĐẠT'),
     ('Bước neo a=5÷7m','Theo kinh nghiệm công trình tương tự','Hợp lý','✅ Chấp nhận'),
     ('Nguy cơ nhổ bật deadman','Phụ thuộc độ sâu đặt và chiều dài','Cần kiểm tra mùa lũ','⚠ Lưu ý'),
    ],
    [5.5,5.5,2.5,3.0], hbg='2E7D32', abg='E8F5E9')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 5. BẢN ĐỒ RỦI RO (PHASED RISK INTELLIGENCE)
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'5. BẢN ĐỒ RỦI RO THEO GIAI ĐOẠN',lv=1)
add_p(doc,'Theo SKILLKC — Kỹ năng Đặc biệt 2: Phased Risk Intelligence '
     '(Cảnh báo Rủi ro theo 3 giai đoạn: Thiết kế → Thi công → Khai thác).')
build_table(doc,
    ['Giai đoạn','Rủi ro nhận diện','Xác suất','Hậu quả','Biện pháp phòng ngừa'],
    [('THIẾT KẾ','Thiếu kết quả khảo sát ĐC → giả định thông số đất sai','CAO','NGHIÊM TRỌNG',
      'BẮT BUỘC có hố khoan ĐC trước khi phê duyệt PA'),
     ('THIẾT KẾ','Chưa tính toán sức chịu tải ngang cọc V100 theo TCVN 9362','CAO','NGHIÊM TRỌNG',
      'Tính toán p-y curve hoặc Broms method cho cọc H-section'),
     ('THIẾT KẾ','Buy Φ400 BTCT đúc sẵn: chưa rõ mác bê tông, tiêu chuẩn sản xuất','TRUNG BÌNH','Trung bình',
      'Yêu cầu nhà cung cấp cung cấp CO/CQ + thí nghiệm nén mẫu'),
     ('THI CÔNG','Cọc V100 bị cong vênh khi đóng thủ công vào đất bùn sét','CAO','Trung bình',
      'Dùng ống dẫn hướng hoặc máy đóng cọc mini; kiểm tra độ thẳng đứng'),
     ('THI CÔNG','Buy bị xoay hoặc lệch tim khi xếp chồng','TRUNG BÌNH','Nhỏ',
      'Dùng cọc thép làm định vị trước khi xếp buy; kiểm tra sau mỗi hàng'),
     ('THI CÔNG','Giằng BTCT neo bị trôi hoặc nổi khi mực nước lên cao mùa lũ','CAO','NGHIÊM TRỌNG',
      'Thi công vào mùa khô; đổ bê tông giằng trước khi thi công tường buy'),
     ('THI CÔNG','Vữa trong lòng buy chưa đủ cường độ đã chịu áp đất','TRUNG BÌNH','Trung bình',
      'Đảm bảo vữa đạt 70% cường độ (≥7 ngày) mới lấp đất phía sau'),
     ('KHAI THÁC','Ăn mòn cọc thép V100 do môi trường ven sông','CAO','Nghiêm trọng LT',
      'Phủ sơn chống gỉ Epoxy 3 lớp; kiểm tra định kỳ 2 năm/lần'),
     ('KHAI THÁC','Buy bị rơi / xô đẩy khi tàu thuyền va chạm','THẤP','Trung bình',
      'Đặt phao tiêu bảo vệ; nghiên cứu thêm tấm đan phủ mặt'),
     ('KHAI THÁC','Xói cục bộ dưới chân tường khi lũ','CAO','NGHIÊM TRỌNG',
      'Bổ sung thảm đá bảo vệ chân kè rộng ≥2m tại cao độ đáy buy'),
    ],
    [2.5,5.0,1.8,2.2,5.0], hbg='37474F', abg='ECEFF1')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 6. DỰ TOÁN SƠ BỘ
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'6. DỰ TOÁN SƠ BỘ PHƯƠNG ÁN',lv=1)
add_p(doc,'Dự toán sơ bộ cho 1 mét dài kè và tổng cho Phân Đoạn C (giả định dài 30m). '
     'Đơn giá tham khảo thị trường tỉnh Tiền Giang / Bến Tre (Quý II/2026).')

build_table(doc,
    ['STT','Hạng mục','ĐVT','Khối lượng/m','Đơn giá (VNĐ)','Thành tiền/m','T.Tiền 30m'],
    [('1','Buy BTCT Φ400 đúc sẵn (vật liệu+vận chuyển)','viên','4.0','180,000','720,000','21,600,000'),
     ('2','Vữa XM trong lòng buy (1 bao 50kg/buy)','bao','4.0','75,000','300,000','9,000,000'),
     ('3','Nhân công xếp buy + vữa','công','0.5','350,000','175,000','5,250,000'),
     ('4','Cọc thép V100 L=6m (mua + phủ sơn EP)','cây','0.25','1,800,000','450,000','13,500,000'),
     ('5','Nhân công đóng cọc thép V100','công','0.3','350,000','105,000','3,150,000'),
     ('6','Thép V50 (100×100) + hàn liên kết','kg','3.5','28,000','98,000','2,940,000'),
     ('7','Giằng BTCT neo 300×300 B20 (VL+NC+đổ)','m³','0.14','3,800,000','532,000','15,960,000'),
     ('8','Thép giằng 4Φ12/Φ6a300 (CB300-V)','kg','0.45','28,000','12,600','378,000'),
     ('9','Vải địa kỹ thuật 0.4×2.4m/m dài','m²','0.4','35,000','14,000','420,000'),
     ('10','Vữa lót đáy M75 (VL+NC)','m²','1.0','120,000','120,000','3,600,000'),
     ('11','Sơn chống gỉ Epoxy cọc V100','m²','0.5','85,000','42,500','1,275,000'),
     ('12','Chi phí khác (dụng cụ, ván khuôn...)','%','—','5% VL+NC','127,905','3,837,150'),
    ],
    [0.6,5.0,1.0,1.8,2.3,2.3,2.5], hbg='1C3557', abg='EAF1FB')
doc.add_paragraph()

# Tổng cộng
p_total=doc.add_paragraph(); p_total.alignment=WD_ALIGN_PARAGRAPH.RIGHT
pf(p_total,sb=2,sa=4)
r_total=p_total.add_run('TỔNG CHI PHÍ DỰ TOÁN SƠ BỘ (30m kè):   ')
r_total.font.size=Pt(11); r_total.font.bold=True
r_val=p_total.add_run('≈  80,910,150 VNĐ   (~  80.9 triệu đồng / 30m)')
r_val.font.size=Pt(11.5); r_val.font.bold=True
r_val.font.color.rgb=RGBColor.from_string('CC0000')

p_dvt=doc.add_paragraph(); p_dvt.alignment=WD_ALIGN_PARAGRAPH.RIGHT
pf(p_dvt,sb=0,sa=6)
r_dvt=p_dvt.add_run('Đơn giá trung bình:   ≈  2,697,000 VNĐ / mét dài kè')
r_dvt.font.size=Pt(10); r_dvt.italic=True
r_dvt.font.color.rgb=RGBColor.from_string('555555')

add_box(doc,'📌 Lưu ý dự toán: (1) Chưa bao gồm chi phí khảo sát địa chất (≈ 15÷25 triệu). '
        '(2) Chưa bao gồm chi phí thảm đá bảo vệ chân kè (khuyến nghị bổ sung thêm ~30÷40 triệu). '
        '(3) Đơn giá biến động ±15% tùy địa điểm và thời điểm thi công. '
        '(4) Tổng khi có đủ các hạng mục bổ sung: ≈ 125÷140 triệu đồng/30m.')

# ══════════════════════════════════════════════════════════════════════════════
# 7. KẾT LUẬN VÀ KIẾN NGHỊ
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'7. KẾT LUẬN VÀ KIẾN NGHỊ',lv=1)
add_p(doc,'Căn cứ kết quả phân tích kỹ thuật theo SKILLKC, phương án Kè Pi Giếng '
     'của Nhà Thầu Tấn Khoa được đánh giá như sau:')

add_h(doc,'7.1. Ưu điểm',lv=2)
pros=[
    ('Thi công nhanh, đơn giản: ','Không cần thiết bị hạng nặng, nhân công phổ thông có thể thực hiện'),
    ('Vật tư phổ biến: ','Buy BTCT Φ400, cọc thép V100, vữa xi măng đều sẵn có tại địa phương'),
    ('Chi phí thấp: ','≈ 2.7 triệu/m — thấp hơn đáng kể so với kè cừ bản thép (≥5÷7 triệu/m)'),
    ('Độ linh hoạt cao: ','Có thể điều chỉnh số hàng buy tùy chiều cao cần thiết'),
    ('Thoát nước tốt: ','Khe hở giữa các buy + vải ĐKT ngăn xói ngầm, cho phép thoát nước'),
]
for bp,bt in pros: add_bullet(doc,bt,bp=bp)

add_h(doc,'7.2. Nhược điểm / Hạn chế',lv=2)
cons=[
    ('Thiếu tính toán định lượng: ','Hồ sơ chưa có kết quả khảo sát ĐC và tính toán cụ thể sức chịu tải cọc V100'),
    ('Rủi ro ổn định cao: ','Tường buy KHÔNG ổn định nếu cọc thép V100 bị lỏng hoặc gãy do xói lở'),
    ('Dễ bị hỏng mùa lũ: ','Buy rời rạc, không liên kết cứng → dễ bị xô đẩy khi lũ mạnh'),
    ('Ăn mòn dài hạn: ','Cọc thép V100 trong môi trường ven sông cần bảo vệ chống gỉ nghiêm ngặt'),
    ('Chiều cao giới hạn: ','Phù hợp H ≤ 2.0m, không nên dùng cho kè cao hơn'),
]
for bp,bt in cons: add_bullet(doc,bt,bp=bp)

add_h(doc,'7.3. Điều Kiện Chấp Thuận',lv=2)
add_box(doc,'✅ PHƯƠNG ÁN CÓ THỂ CHẤP THUẬN với điều kiện bắt buộc:\n'
        '1. Cung cấp kết quả khảo sát địa chất (ít nhất 2 hố khoan sâu 5m/đoạn 30m);\n'
        '2. Tính toán sức chịu tải ngang cọc V100 theo TCVN 9362:2012 — Broms Method;\n'
        '3. Bổ sung thảm đá bảo vệ chân kè Φ100÷200mm, rộng ≥ 2m;\n'
        '4. Kiểm tra buy BTCT đầu vào (CO/CQ nhà sản xuất + thí nghiệm nén 3 mẫu/lô);\n'
        '5. Thi công trong mùa khô, hoàn thành trước tháng 5.')

# ══════════════════════════════════════════════════════════════════════════════
# 8. BẢNG TRÁCH NHIỆM PHÊ DUYỆT (MISS-01)
# ══════════════════════════════════════════════════════════════════════════════
add_h(doc,'8. BẢNG TRÁCH NHIỆM & PHÊ DUYỆT',lv=1)
build_table(doc,
    ['','Đề xuất','Kiểm tra','Phê duyệt'],
    [('Ý kiến','Kính trình BLĐ xem xét','',''),
     ('Chữ ký','','',''),
     ('Ngày ký',TODAY,'',''),
     ('Họ tên','[AI Technical Illustrator]','[TP. QLTK]','[GĐ Ban Xây Dựng]'),
     ('Chức vụ','Trợ lý Kết cấu AI','Trưởng phòng QLTK','Giám đốc Ban XD'),
    ],
    [3.0,4.0,4.0,4.5], hbg='37474F', abg='ECEFF1')

# Chú thích cuối
doc.add_paragraph()
add_p(doc,'Lưu ý: Báo cáo này được lập bởi Trợ lý Kết cấu AI dựa trên thông tin '
     'bản vẽ phương án do Nhà Thầu Tấn Khoa cung cấp. Người kiểm tra kỹ thuật '
     'có trách nhiệm xác nhận lại các số liệu tính toán trước khi phê duyệt chính thức.',
     italic=True, color='777777', size=9.5)

# ══════════════════════════════════════════════════════════════════════════════
doc.save(OUT_DOCX)
print(f"[OK] Da luu: {OUT_DOCX}")
