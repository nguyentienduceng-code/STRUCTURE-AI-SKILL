
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
generate_tham_da_docx.py
Xuất file Word (.docx) — Báo cáo Kỹ thuật Chi tiết Thảm Đá (Gabion Mattress)
Thư viện: python-docx, Pillow
"""

import sys, os
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date
import copy

# ── Đường dẫn ────────────────────────────────────────────────────────────────
OUT_DIR   = r"G:\My Drive\Google AI Studio\01_Projects\0.0 REPORT AI"
IMG_3D    = os.path.join(OUT_DIR, "tham_da_phoi_canh_3d.png")
IMG_DRAW  = os.path.join(OUT_DIR, "tham_da_technical_drawing.png")
OUT_DOCX  = os.path.join(OUT_DIR, "BAO_CAO_KY_THUAT_THAM_DA.docx")
TODAY     = date.today().strftime("%d/%m/%Y")

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def set_cell_bg(cell, hex_color: str):
    """Tô màu nền ô bảng"""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_border(table, top='single', bottom='single', left='single', right='single', size=6, color='1C3557'):
    """Kẻ đường viền bảng"""
    tbl  = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), str(size))
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    tblPr.append(tblBorders)

def para_format(para, space_before=0, space_after=6, line_spacing=1.15):
    pf = para.paragraph_format
    pf.space_before    = Pt(space_before)
    pf.space_after     = Pt(space_after)
    pf.line_spacing    = line_spacing
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE

def add_heading(doc, text, level=1, color='1C3557', keep_with_next=True):
    """Thêm heading có màu tuỳ chỉnh"""
    h = doc.add_heading(text, level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in h.runs:
        run.font.color.rgb = RGBColor.from_string(color)
        run.font.bold = True
    if keep_with_next:
        h.paragraph_format.keep_with_next = True
    para_format(h, space_before=10 if level==1 else 6, space_after=4)
    return h

def add_para(doc, text, bold=False, italic=False, size=10.5, indent=0,
             color='222222', align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=4):
    p = doc.add_paragraph()
    p.alignment = align
    para_format(p, space_after=space_after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size  = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    return p

def add_bullet(doc, text, bold_prefix=None, size=10, indent=0.5):
    """Bullet tùy chỉnh"""
    p = doc.add_paragraph(style='List Bullet')
    para_format(p, space_after=2)
    p.paragraph_format.left_indent = Cm(indent)
    if bold_prefix:
        r1 = p.add_run(bold_prefix)
        r1.bold = True
        r1.font.size = Pt(size)
        r1.font.color.rgb = RGBColor.from_string('1C3557')
        r2 = p.add_run(text)
        r2.font.size = Pt(size)
    else:
        r = p.add_run(text)
        r.font.size = Pt(size)
    return p

def add_info_box(doc, text, bg='F0F4FA', border_color='1C3557'):
    """Hộp thông tin màu nền nhạt"""
    p = doc.add_paragraph()
    para_format(p, space_before=4, space_after=4)
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), bg)
    pPr.append(shd)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = RGBColor.from_string('1A3557')
    return p

def add_image_centered(doc, img_path, width_cm=15.0, caption=None):
    """Chèn ảnh căn giữa + caption"""
    if not os.path.exists(img_path):
        add_para(doc, f'[Ảnh không tìm thấy: {img_path}]', italic=True, color='CC0000')
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_format(p, space_before=4, space_after=2)
    run = p.add_run()
    run.add_picture(img_path, width=Cm(width_cm))
    # Caption
    if caption:
        cp = doc.add_paragraph(caption)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para_format(cp, space_before=0, space_after=8)
        for run in cp.runs:
            run.font.size  = Pt(9)
            run.font.italic = True
            run.font.color.rgb = RGBColor.from_string('555555')


def build_table(doc, headers, rows, col_widths_cm, header_bg='1C3557',
                alt_row_bg='DDE8F5', border_color='1C3557'):
    """Tạo bảng đẹp có header màu + zebra stripe"""
    n_cols = len(headers)
    table  = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_cell_border(table, color=border_color)

    # Header row
    hdr_cells = table.rows[0].cells
    for i, (h, w) in enumerate(zip(headers, col_widths_cm)):
        cell = hdr_cells[i]
        set_cell_bg(cell, header_bg)
        cell.width = Cm(w)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para_format(p, space_before=2, space_after=2)
        run = p.add_run(h)
        run.bold = True
        run.font.size  = Pt(9)
        run.font.color.rgb = RGBColor.from_string('FFFFFF')

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg = alt_row_bg if r_idx % 2 == 0 else 'FFFFFF'
        for c_idx, (cell_text, w) in enumerate(zip(row_data, col_widths_cm)):
            cell = row_cells[c_idx]
            set_cell_bg(cell, bg)
            cell.width = Cm(w)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            para_format(p, space_before=1, space_after=1)
            run = p.add_run(str(cell_text))
            run.font.size = Pt(9)
    return table


# ══════════════════════════════════════════════════════════════════════════════
# TẠO DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
doc = Document()

# ── Page Setup A4 đứng ───────────────────────────────────────────────────────
section = doc.sections[0]
section.page_width      = Cm(21.0)
section.page_height     = Cm(29.7)
section.left_margin     = Cm(2.5)
section.right_margin    = Cm(2.0)
section.top_margin      = Cm(2.5)
section.bottom_margin   = Cm(2.0)

# ── Default font ─────────────────────────────────────────────────────────────
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

# ══════════════════════════════════════════════════════════════════════════════
# TRANG BÌA
# ══════════════════════════════════════════════════════════════════════════════

# Dải tiêu đề phía trên (giả lập banner)
for _ in range(3):
    doc.add_paragraph()

p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p_title.add_run('BÁO CÁO KỸ THUẬT CHI TIẾT')
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = RGBColor.from_string('1C3557')
para_format(p_title, space_after=6)

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p_sub.add_run('THẢM ĐÁ — GABION MATTRESS / RENO MATTRESS')
r2.bold = True
r2.font.size = Pt(15)
r2.font.color.rgb = RGBColor.from_string('1C3557')
para_format(p_sub, space_after=4)

p_app = doc.add_paragraph()
p_app.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p_app.add_run('Ứng dụng: Gia cố bờ sông · Bảo vệ taluy mái đường · Chống xói lở bờ biển')
r3.italic = True
r3.font.size = Pt(11)
r3.font.color.rgb = RGBColor.from_string('555555')
para_format(p_app, space_after=20)

# Bảng thông tin dự án
info_table = doc.add_table(rows=6, cols=2)
info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
set_cell_border(info_table, color='1C3557')
info_table.columns[0].width = Cm(5.5)
info_table.columns[1].width = Cm(11.0)

info_data = [
    ('Ký hiệu bản vẽ',  'TD-01 / REV.00'),
    ('Tiêu chuẩn',       'TCVN 8289:2009  ·  EN 10223-3:2013  ·  ASTM A975'),
    ('Kích thước',       '4000 × 2000 × 300 mm  (D × R × H)'),
    ('Lưới thép',        'Lục giác xoắn kép Φ2.7mm, mạ kẽm ≥ 240 g/m²'),
    ('Đá nhồi',          'Đá hộc Φ100÷200mm, Rc ≥ 60 MPa, LA ≤ 35%'),
    ('Ngày lập',         TODAY + '  |  Người lập: Trợ lý Kỹ thuật AI'),
]
for r_idx, (label, value) in enumerate(info_data):
    cells = info_table.rows[r_idx].cells
    set_cell_bg(cells[0], 'DDE8F5')
    set_cell_bg(cells[1], 'FFFFFF')
    cells[0].width = Cm(5.5)
    cells[1].width = Cm(11.0)
    p0 = cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para_format(p0, space_before=2, space_after=2)
    r0 = p0.add_run(label)
    r0.bold = True; r0.font.size = Pt(10)
    r0.font.color.rgb = RGBColor.from_string('1C3557')

    p1 = cells[1].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para_format(p1, space_before=2, space_after=2)
    r1 = p1.add_run(value)
    r1.font.size = Pt(10)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. TỔNG QUAN VÀ CẤU TẠO
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '1. TỔNG QUAN VÀ ĐỊNH NGHĨA', level=1)

add_para(doc,
    'Thảm đá (Gabion Mattress hoặc Reno Mattress) là cấu kiện bảo vệ bề mặt dạng tấm '
    'dẹt, hình hộp chữ nhật, cấu tạo từ lưới thép mạ kẽm hình lục giác xoắn kép, '
    'được nhồi đầy đá hộc chọn lọc. Đây là giải pháp kỹ thuật phổ biến, kinh tế và '
    'bền vững trong các công trình gia cố bờ sông, kênh thoát lũ, taluy mái đường '
    'và bảo vệ chân đê, bờ biển khỏi xói lở.')

add_info_box(doc,
    '⚠  Phân biệt với Rọ đá (Gabion Box): Thảm đá có H = 0.17÷0.30m (rất thấp, '
    'dùng để phủ bề mặt), trong khi Rọ đá có H = 0.5÷1.0m (dùng làm kè đứng chịu lực).')

add_heading(doc, '1.1. Nguyên Lý Làm Việc', level=2)
add_para(doc,
    'Thảm đá làm việc theo nguyên lý kết hợp giữa trọng lực của đá nhồi và tính '
    'mềm dẻo của lưới thép. Toàn bộ hệ thống có khả năng biến dạng thích nghi '
    'theo hình dạng địa hình mà không bị nứt gãy, đồng thời lỗ rỗng giữa các '
    'viên đá tạo điều kiện thoát nước và phát triển thực vật, giảm áp lực thấm.')

# ══════════════════════════════════════════════════════════════════════════════
# 2. CẤU TẠO CHI TIẾT
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '2. CẤU TẠO CHI TIẾT CÁC BỘ PHẬN', level=1)

add_para(doc, 'Một tấm thảm đá tiêu chuẩn gồm 7 bộ phận chính được minh họa và mô tả dưới đây:')

# Bảng cấu tạo bộ phận
headers_cauTao = ['#', 'Bộ phận', 'Vật liệu / Đặc điểm kỹ thuật', 'Chức năng']
rows_cauTao = [
    ('1', 'Thân lưới (Body mesh)',     'Thép carbon thấp Φ2.7mm mạ kẽm ≥ 240g/m²\nLưới lục giác xoắn kép, mắt lưới 60×80mm',                     'Vỏ bọc chính giữ đá, 4 thành + đáy'),
    ('2', 'Đáy lưới (Bottom mesh)',    'Cùng thân lưới — tiếp xúc nền đất',                                                                          'Truyền áp lực lên nền, lọc nước'),
    ('3', 'Nắp lưới (Lid/Top mesh)',   'Cùng thân lưới — đậy sau khi nhồi đá',                                                                       'Giữ đá, bảo vệ bề mặt trên'),
    ('4', 'Dây biên (Edge wire)',      'Thép Φ3.4mm mạ kẽm — gia cường 4 cạnh biên',                                                                 'Tăng cứng, chống biến dạng biên'),
    ('5', 'Vách ngăn (Diaphragm)',     '3 vách cách đều 1m, chia thành 4 ô\nCùng vật liệu thân lưới',                                               'Chống phình ra mặt bên, ổn định hình dạng'),
    ('6', 'Dây buộc (Lacing wire)',    'Thép Φ2.2mm mạ kẽm\nDây xoắn liên kết chu vi nắp + vách ngăn',                                             'Khoá nắp, liên kết tấm kề nhau'),
    ('7', 'Đá nhồi (Stone fill)',      'Đá hộc/cuội Φ100÷200mm\nRc ≥ 60 MPa · LA ≤ 35% · Hút nước ≤ 1.5%',                                        'Tạo trọng lượng, chống trôi, thoát nước'),
]
t1 = build_table(doc, headers_cauTao, rows_cauTao,
                 col_widths_cm=[1.0, 3.5, 7.0, 4.5],
                 header_bg='1C3557', alt_row_bg='EAF1FB')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 3. ẢNH PHỐI CẢNH 3D
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '3. HÌNH ẢNH PHỐI CẢNH THỰC TẾ THI CÔNG', level=1)
add_para(doc,
    'Hình dưới đây mô phỏng trực quan một tấm thảm đá Gabion Mattress đang được '
    'thi công tại công trường gia cố bờ sông. Có thể thấy lưới thép lục giác mạ kẽm, '
    'đá hộc đang được đổ vào từng ô, và công nhân đang thực hiện hoàn thiện nắp đậy.')

add_image_centered(doc, IMG_3D, width_cm=15.5,
    caption='Hình 3.1 — Phối cảnh 3D thi công thảm đá Gabion Mattress tại công trình gia cố bờ sông')

# ══════════════════════════════════════════════════════════════════════════════
# 4. BẢN VẼ KỸ THUẬT 2D
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, '4. BẢN VẼ KỸ THUẬT CHI TIẾT 2D', level=1)

add_para(doc,
    'Bản vẽ kỹ thuật dưới đây thể hiện đầy đủ 4 góc nhìn kỹ thuật của thảm đá '
    'theo tỷ lệ tiêu chuẩn:')

bullets_draw = [
    ('Panel 1 — Mặt bằng (1:50): ', 'Thể hiện tổng thể 4 ô, 3 vách ngăn, đường cắt A-A và B-B'),
    ('Panel 2 — Mặt cắt dọc A-A (1:50): ', 'Thể hiện bố trí đá hộc, vách ngăn, lớp lưới đáy/nắp'),
    ('Panel 3 — Mặt cắt ngang B-B (1:25): ', 'Thể hiện chiều cao H=300mm, lưới thành, lưới đáy'),
    ('Panel 4 — Chi tiết lưới & Bảng TSKT: ', 'Kích thước mắt lưới 60×80mm và bảng thông số đầy đủ'),
]
for bp, bt in bullets_draw:
    add_bullet(doc, bt, bold_prefix=bp)

doc.add_paragraph()
add_image_centered(doc, IMG_DRAW, width_cm=16.0,
    caption='Hình 4.1 — Bản vẽ kỹ thuật chi tiết thảm đá A3 (Tỷ lệ 1:50 & 1:25) — 300 DPI')

# ══════════════════════════════════════════════════════════════════════════════
# 5. THÔNG SỐ KỸ THUẬT
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, '5. THÔNG SỐ KỸ THUẬT ĐẦY ĐỦ', level=1)

add_heading(doc, '5.1. Thông Số Lưới Thép', level=2)
headers_luoi = ['Thông số', 'Giá trị', 'Tiêu chuẩn']
rows_luoi = [
    ('Loại lưới',                'Lục giác xoắn kép (Double-twisted hex)',  'EN 10223-3'),
    ('Kích thước mắt lưới',      '60 × 80 mm',                              'EN 10223-3'),
    ('Đường kính dây thân',      'Φ 2.7 mm',                                'EN 10218-2'),
    ('Đường kính dây biên',      'Φ 3.4 mm',                                'EN 10218-2'),
    ('Đường kính dây buộc',      'Φ 2.2 mm',                                'EN 10218-2'),
    ('Lớp mạ kẽm tối thiểu',    '≥ 240 g/m²',                              'EN 10244-2'),
    ('Cấp thép dây',             'Thép carbon thấp, Rm ≥ 380 MPa',          'EN 10016'),
    ('Độ dãn dài tối thiểu',     '≥ 10%',                                   'EN 10218-2'),
    ('Độ cứng dây (Hardness)',   '≤ 170 HV',                                'EN 10218-2'),
]
build_table(doc, headers_luoi, rows_luoi,
            col_widths_cm=[6.0, 6.5, 3.5],
            header_bg='1C3557', alt_row_bg='EAF1FB')
doc.add_paragraph()

add_heading(doc, '5.2. Thông Số Đá Nhồi', level=2)
headers_da = ['Thông số chất lượng', 'Yêu cầu tối thiểu', 'Tiêu chuẩn kiểm tra']
rows_da = [
    ('Cỡ hạt đá (Grain size)',        'D = 100 ÷ 200 mm',     'TCVN 8219:2009'),
    ('Cường độ nén 1 trục',           'Rc ≥ 60 MPa',           'TCVN 7572-10:2006'),
    ('Độ hao mòn Los Angeles',        'LA ≤ 35%',              'TCVN 7572-12:2006'),
    ('Độ hút nước',                   '≤ 1.5%',               'TCVN 7572-4:2006'),
    ('Khối lượng thể tích đá',        '≥ 2.60 T/m³',          'TCVN 7572-4:2006'),
    ('Hệ số rỗng sau khi nhồi',       '30 ÷ 40%',             'EN 12251'),
    ('Hàm lượng silic/thạch anh',     '≤ 10% (tránh phản ứng alkali)', 'TCVN 7572-14'),
    ('Tính kháng phong hoá',          'Không phong hoá, không mủn',    'Kiểm tra trực quan'),
]
build_table(doc, headers_da, rows_da,
            col_widths_cm=[6.5, 5.0, 4.5],
            header_bg='2E7D32', alt_row_bg='E8F5E9')
doc.add_paragraph()

add_heading(doc, '5.3. Đặc Tính Kỹ Thuật Tổng Hợp', level=2)
headers_tc = ['Thông số tổng hợp', 'Giá trị điển hình']
rows_tc = [
    ('Khối lượng thảm rỗng (lưới không đá)',    '≈ 35 ÷ 40 kg/tấm'),
    ('Khối lượng thảm đầy đá',                  '≈ 2.5 ÷ 3.0 Tấn/tấm'),
    ('Hệ số nhám Manning (n)',                   '0.024 ÷ 0.030'),
    ('Vận tốc dòng chảy cho phép (Vmax)',        'V ≤ 4.5 m/s (mái 1:2)'),
    ('Tuổi thọ thiết kế (môi trường nước ngọt)','≥ 50 năm'),
    ('Tuổi thọ thiết kế (môi trường biển mặn)', '≥ 30 năm (khuyến nghị dùng lưới mạ Galfan)'),
    ('Độ rỗng trung bình (porosity)',            '30 ÷ 40%'),
    ('Diện tích 1 tấm (4m×2m)',                 '8.0 m²/tấm'),
]
build_table(doc, headers_tc, rows_tc,
            col_widths_cm=[9.0, 7.0],
            header_bg='5D4037', alt_row_bg='FFF3E0')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# 6. PHẠM VI ỨNG DỤNG
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '6. PHẠM VI ỨNG DỤNG VÀ LỰA CHỌN GIẢI PHÁP', level=1)

add_heading(doc, '6.1. Phạm Vi Ứng Dụng Phù Hợp', level=2)
apps = [
    ('Gia cố mái kênh/sông: ',    'Độ dốc mái m = 1:1.5 ÷ 1:3, vận tốc V ≤ 4.5 m/s'),
    ('Bảo vệ đáy kênh thoát lũ: ','Vùng dòng chảy có bùn cát thấp đến trung bình'),
    ('Gia cố taluy mái đường: ',   'Khu vực đầu cầu, cống hộp, cửa vào cống'),
    ('Bảo vệ chân đê/bờ biển: ',  'Kết hợp với rọ đá tường đứng phía dưới'),
    ('Đập tràn thấp (H < 2.0m): ','Lớp phủ chống xói hạ lưu tràn bậc thang'),
]
for bp, bt in apps:
    add_bullet(doc, bt, bold_prefix=bp)

add_heading(doc, '6.2. Hạn Chế và Lưu Ý Thay Thế', level=2)
limits = [
    'Không dùng khi có tải trọng phương tiện trực tiếp lên thảm đá',
    'Không dùng ở vùng dòng chảy bùn cát lớn (khuyến nghị dùng rọ đá tường đứng)',
    'Không dùng ở mái có độ dốc > 1:1.5 (thay bằng rọ đá cài lẫn nhau)',
    'Khi môi trường biển mặn: bắt buộc dùng lưới mạ Galfan (Zn-Al) hoặc bọc PVC',
]
for l in limits:
    add_bullet(doc, l)

# ══════════════════════════════════════════════════════════════════════════════
# 7. QUY TRÌNH THI CÔNG
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '7. QUY TRÌNH THI CÔNG (TCVN 8289:2009)', level=1)

steps = [
    ('Bước 1 — Chuẩn bị nền: ',
     'San phẳng, lu lèn mái taluy đạt độ chặt K ≥ 0.90; kiểm tra độ dốc thiết kế; '
     'phát cỏ và bóc lớp đất hữu cơ phía trên.'),
    ('Bước 2 — Trải vải địa kỹ thuật: ',
     'Lớp lọc địa kỹ thuật (Geotextile) loại không dệt ≥ 200 g/m², '
     'chồng mép tối thiểu 0.30m giữa các tấm; neo mép bằng đinh U.'),
    ('Bước 3 — Trải thảm đá (trạng thái rỗng): ',
     'Căng phẳng thảm theo đúng hướng mái; buộc liên kết giữa các tấm kề nhau '
     'bằng dây xoắn Φ2.2mm, khoảng cách buộc ≤ 200mm.'),
    ('Bước 4 — Nhồi đá: ',
     'Đổ đá hộc đã kiểm tra chất lượng vào từng ô; san phẳng thủ công đến cao '
     'độ đầy thảm; tránh để đá nhô cao hơn thành lưới.'),
    ('Bước 5 — Đóng nắp và buộc hoàn chỉnh: ',
     'Kéo tấm nắp lưới, buộc xoắn toàn bộ chu vi mép nắp và dọc theo vách ngăn '
     'bằng dây Φ2.2mm, khoảng cách buộc ≤ 150mm.'),
    ('Bước 6 — Kiểm tra nghiệm thu: ',
     'Kiểm tra độ đầy đá, độ căng lưới, chất lượng mối buộc; '
     'chụp ảnh hiện trạng từng vị trí; lập biên bản nghiệm thu công đoạn.'),
]
for bp, bt in steps:
    add_bullet(doc, bt, bold_prefix=bp, size=10)

add_info_box(doc,
    '⚠  Lưu ý kiểm soát chất lượng đặc biệt: Đá nhồi phải đồng đều kích thước, '
    'không dùng đá phong hoá. Tránh để lưới bị xoắn hoặc biến dạng trước khi nhồi đá. '
    'Kiểm tra chứng chỉ xuất xứ lưới thép và kết quả thí nghiệm đá tại phòng thí nghiệm '
    'được kiểm định trước khi đưa vào sử dụng.')

# ══════════════════════════════════════════════════════════════════════════════
# 8. TIÊU CHUẨN ÁP DỤNG
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '8. HỆ THỐNG TIÊU CHUẨN ÁP DỤNG', level=1)
standards = [
    ('TCVN 8289:2009', 'Công trình thuỷ lợi — Yêu cầu kỹ thuật thi công và nghiệm thu thảm đá'),
    ('EN 10223-3:2013', 'Steel wire and wire products — Hexagonal steel wire mesh for engineering purposes'),
    ('EN 10218-2:2012', 'Steel wire and wire products — Wire — Dimensions and tolerances'),
    ('EN 10244-2:2009', 'Zinc or zinc alloy coatings on steel wire — Hot dip galvanized coatings'),
    ('ASTM A975-97',   'Standard Specification for Double-Twisted Hexagonal Mesh Gabions and Revet Mattresses'),
    ('TCVN 7572:2006',  'Cốt liệu cho bê tông và vữa — Phương pháp thử (kiểm tra chất lượng đá)'),
    ('TCVN 8219:2009',  'Hỗn hợp đầm nén trong phòng thí nghiệm — Đặc tính cốt liệu đá hộc'),
]
headers_std = ['Tiêu chuẩn', 'Phạm vi áp dụng']
rows_std = [(s, d) for s, d in standards]
build_table(doc, headers_std, rows_std,
            col_widths_cm=[4.5, 11.5],
            header_bg='37474F', alt_row_bg='ECEFF1')
doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# LƯU FILE
# ══════════════════════════════════════════════════════════════════════════════
doc.save(OUT_DOCX)
print(f"[OK] Da luu file Word: {OUT_DOCX}")
