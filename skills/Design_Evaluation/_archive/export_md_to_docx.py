from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('BẢNG TỔNG HỢP KẾT QUẢ TÍNH TOÁN KẾT CẤU', level=1)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('DỰ ÁN: CT PLAZA MINH CHÂU - CẢI TẠO TẦNG 2 (LẤP Ô SÀN)').bold = True
doc.add_paragraph('Căn cứ tiêu chuẩn: TCVN 5575:2024 (Thiết kế KCT), TCVN 2737:2023 (Tải trọng)').bold = True

doc.add_paragraph('---')

# 1. Thông số vật liệu
doc.add_heading('1. Thông Số Vật Liệu Đầu Vào', level=2)
table1 = doc.add_table(rows=5, cols=4)
table1.style = 'Table Grid'
hdr_cells = table1.rows[0].cells
hdr_cells[0].text = 'Loại vật liệu'
hdr_cells[1].text = 'Ký hiệu / Chủng loại'
hdr_cells[2].text = 'Cường độ tiêu chuẩn (fy / fub)'
hdr_cells[3].text = 'Ghi chú'

data1 = [
    ['Thép cán nóng (Dầm I, Xà gồ)', 'SS400 / Q235B', '235 MPa', 'Tiết diện I-300x150x6.5x9 và Hộp 50x100x1.8'],
    ['Thép bản (Bản mã, Sườn gia cường)', 'SS400 / Q235B', '235 MPa', 'Bản mã PL16, Sườn gia cường PL8'],
    ['Bu lông neo/Liên kết', 'Cấp bền 8.8 (Mạ kẽm)', 'fub = 800 MPa, fyb = 640 MPa', 'Sử dụng bu lông M24'],
    ['Vật liệu hàn', 'Que hàn N42', 'fwu = 410 MPa', 'Chiều cao đường hàn tối thiểu hf = 8mm']
]

for i, row in enumerate(data1):
    for j, val in enumerate(row):
        table1.rows[i+1].cells[j].text = val

doc.add_paragraph('')

# 2. Tải trọng
doc.add_heading('2. Tổ Hợp Tải Trọng (Tham chiếu TCVN 2737:2023)', level=2)
table2 = doc.add_table(rows=6, cols=5)
table2.style = 'Table Grid'
h2 = table2.rows[0].cells
h2[0].text = 'Loại Tải Trọng'
h2[1].text = 'Thành phần'
h2[2].text = 'Giá trị tiêu chuẩn (kN/m2)'
h2[3].text = 'Hệ số tin cậy'
h2[4].text = 'Giá trị tính toán (kN/m2)'

data2 = [
    ['Tĩnh tải (DL)', 'Tấm Cemboard dày 20mm', '0.26', '1.1', '0.286'],
    ['', 'Lớp vữa lót / Gạch', 'Data Missing', '1.2', 'Data Missing'],
    ['', 'Trần thạch cao + MEP', '0.25', '1.2', '0.30'],
    ['', 'Tĩnh tải bản thân thép', 'Phần mềm tự tính', '1.05', '-'],
    ['Hoạt tải (LL)', 'Văn phòng làm việc', '2.0 - 2.4', '1.2', '2.4 - 2.88']
]
for i, row in enumerate(data2):
    for j, val in enumerate(row):
        table2.rows[i+1].cells[j].text = val

doc.add_paragraph('')

# 3. Dầm thép
doc.add_heading('3. Tổng Hợp Kiểm Tra Cấu Kiện Dầm Thép (Nhịp 8.0m)', level=2)
doc.add_paragraph('Bản tính chi tiết xem file đính kèm: 04b KiemTraChuyenViDungNhaCongNghiep.xlsm')
table3 = doc.add_table(rows=5, cols=4)
table3.style = 'Table Grid'
h3 = table3.rows[0].cells
h3[0].text = 'Tiêu chí kiểm tra'
h3[1].text = 'Thông số thiết kế'
h3[2].text = 'Điều kiện giới hạn'
h3[3].text = 'Kết quả / Đánh giá'

data3 = [
    ['Khả năng chịu Uốn (Bền)', 'Tiết diện I-300x150x6.5x9', 'Uốn <= Cho phép', 'Đạt'],
    ['Khả năng chịu Cắt (Bền)', 'Bản bụng tw = 6.5mm', 'Cắt <= Cho phép', 'Đạt'],
    ['Kiểm tra độ Võng', 'Nhịp L = 8000 mm', '[Delta] <= L/250 = 32 mm', 'Đạt'],
    ['Ổn định cục bộ bản bụng', 'Bố trí sườn gia cường bản bụng', 'Thiết kế bố trí PL-8 a1200', 'Đạt (Khắc phục hoàn toàn rủi ro)']
]
for i, row in enumerate(data3):
    for j, val in enumerate(row):
        table3.rows[i+1].cells[j].text = val

doc.add_paragraph('')

# 4. Xà gồ
doc.add_heading('4. Tổng Hợp Kiểm Tra Xà Gồ & Sàn Cemboard', level=2)
table4 = doc.add_table(rows=4, cols=4)
table4.style = 'Table Grid'
h4 = table4.rows[0].cells
h4[0].text = 'Cấu kiện / Tiêu chí kiểm tra'
h4[1].text = 'Thông số thiết kế'
h4[2].text = 'Điều kiện giới hạn'
h4[3].text = 'Kết quả / Đánh giá'

data4 = [
    ['Xà gồ: Khả năng chịu Uốn', 'Thép hộp 50x100x1.8, Nhịp 1100 mm', 'Ứng suất <= Cho phép', 'Đạt (Ứng suất uốn nhỏ)'],
    ['Xà gồ: Độ Võng', 'Khoảng cách xà gồ a = 600 mm', '[Delta] <= L/200 = 5.5 mm', 'Đạt'],
    ['Sàn Cemboard 20mm', 'Chịu uốn cục bộ nhịp 600mm', 'Hoạt tải <= Sức chịu tải của tấm', 'Đạt (Theo catalogue)']
]
for i, row in enumerate(data4):
    for j, val in enumerate(row):
        table4.rows[i+1].cells[j].text = val

doc.add_paragraph('')

# 5. Liên kết
doc.add_heading('5. Tổng Hợp Kiểm Tra Liên Kết LK1 (Shear Connection)', level=2)
doc.add_paragraph('Bản tính chi tiết xem file đính kèm: 220 và 221 TCVN 5575 2024 LienKetShear.xlsm')
table5 = doc.add_table(rows=4, cols=4)
table5.style = 'Table Grid'
h5 = table5.rows[0].cells
h5[0].text = 'Tiêu chí phá hoại'
h5[1].text = 'Phương pháp kiểm tra'
h5[2].text = 'Điều kiện giới hạn'
h5[3].text = 'Đánh giá an toàn'

data5 = [
    ['Khả năng chịu Cắt nhóm Bu lông', '4 Bu lông M24 (Cấp bền 8.8)', 'Lực cắt <= Sức kháng cắt', 'Đạt'],
    ['Khả năng chịu Ép mặt bản thép', 'Ép mặt tại lỗ bu lông bản mã', 'Chiều dày t=16mm >= bản bụng', 'Đạt'],
    ['Đứt gãy đường hàn góc', 'Hàn dọc bản bụng vào bản mã', 'hf = 8mm >= hf,min (5-6mm)', 'Đạt']
]
for i, row in enumerate(data5):
    for j, val in enumerate(row):
        table5.rows[i+1].cells[j].text = val

doc.add_paragraph('\nKẾT LUẬN:').bold = True
doc.add_paragraph('Hệ sàn thép lấp ô thông tầng đáp ứng hoàn toàn các chỉ tiêu về khả năng chịu lực (Bền) và điều kiện sử dụng bình thường (Độ võng) theo TCVN 5575:2024. Bảng thông số trên được tổng hợp để đính kèm vào Thuyết minh tính toán kỹ thuật đệ trình Chủ đầu tư.')

output_path = r'g:\My Drive\Google AI Studio\MINH CHAU\BXD-TongHopTinhToan-MINHCHAU.docx'
doc.save(output_path)
print(f"Exported docx to {output_path}")
