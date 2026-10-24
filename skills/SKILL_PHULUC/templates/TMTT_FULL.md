# THUYẾT MINH TÍNH TOÁN KẾT CẤU
## CÔNG TRÌNH: {{project_name}}

---

# QUY CHUẨN VÀ TIÊU CHUẨN THIẾT KẾ

## Quy chuẩn và Văn bản pháp lý phân cấp công trình

| STT | Tên Quy chuẩn / Văn bản pháp lý | Số hiệu | Phạm vi áp dụng chuẩn xác |
|:---:|---|---|---|
| 1 | Quy chuẩn kỹ thuật quốc gia – Số liệu điều kiện tự nhiên dùng cho thiết kế | QCVN 02:2022/BXD | Phân vùng gió, khí hậu, địa hình |
| 2 | Quy chuẩn kỹ thuật quốc gia về an toàn cháy cho nhà và công trình (kèm Sửa đổi 1:2023) | QCVN 06:2022/BXD | Bậc chịu lửa, giới hạn chịu lửa REI |
| 3 | Quy chuẩn kỹ thuật quốc gia về phân cấp công trình phục vụ thiết kế xây dựng | QCVN 03:2022/BXD | Cấp hậu quả (`C1, C2, C3` - Phụ lục A) & Tuổi thọ thiết kế (`Bảng 1`: Mức 3 ≥ 50 năm cho nhà dân dụng/TTTM thông thường; Mức 4 ≥ 100 năm cho công trình biểu tượng) |
| 4 | Thông tư quy định về phân cấp công trình xây dựng và hướng dẫn áp dụng trong quản lý hoạt động đầu tư xây dựng | **Thông tư 34/2026/TT-BXD** *(hiệu lực từ 01/07/2026, thay thế TT 06/2021/TT-BXD và TT 02/2025/TT-BXD)* | Xác định **Cấp công trình (`Đặc biệt, Cấp I, II, III, IV`)** theo Phụ lục I và **6 tiêu chí Mục 2.1.1 Bảng 2 Phụ lục II** (Chiều cao, Số tầng cao, Tổng diện tích sàn GFA, Nhịp lớn nhất, Độ sâu ngầm đến mặt trên sàn hầm sâu nhất, Số tầng ngầm) |
| 5 | Quy định chi tiết một số điều và biện pháp thi hành Luật Xây dựng | NĐ 175/2024/NĐ-CP | Quản lý dự án và thẩm định thiết kế xây dựng |

## Tiêu chuẩn thiết kế và khảo sát

| STT | Tên Tiêu chuẩn | Số hiệu Tiêu chuẩn |
|:---:|---|---|
| 1 | Tải trọng và tác động | TCVN 2737:2023 |
| 2 | Kết cấu bê tông và bê tông cốt thép – Tiêu chuẩn thiết kế | TCVN 5574:2018 |
| 3 | Kết cấu thép – Tiêu chuẩn thiết kế | TCVN 5575:2024 |
| 4 | Thiết kế công trình chịu động đất | TCVN 9386:2025 |
| 5 | Móng cọc – Tiêu chuẩn thiết kế | TCVN 10304:2025 |
| 6 | Tiêu chuẩn thiết kế nền nhà và công trình | TCVN 9362:2012 |
| 7 | Kết cấu xây dựng và nền – Nguyên tắc cơ bản về tính toán | TCVN 9379:2012 |
| 8 | Khảo sát cho xây dựng – Khảo sát địa kỹ thuật cho nhà cao tầng | TCVN 9363:2012 |
| 9 | Khảo sát cho xây dựng – Nguyên tắc cơ bản (Phân cấp phức tạp ĐCCT Điều 3.5 & Phụ lục 2) | TCVN 4419:1987 |
| 10 | Đất xây dựng – Phương pháp thí nghiệm hiện trường – Thí nghiệm xuyên tiêu chuẩn (SPT) | TCVN 9351:2022 |
| 11 | Kết cấu bê tông và BTCT – Yêu cầu chung về thiết kế độ bền lâu và tuổi thọ trong môi trường xâm thực (thay thế TCVN 3994:1985) | TCVN 12041:2017 & TCVN 9346:2012 |
| 12 | Specification for Structural Steel Buildings | AISC 360-10 |
| 13 | Minimum Design Loads and Associated Criteria for Buildings and Other Structures | ASCE 7-10 |

---

# CÁC TIÊU CHÍ KIỂM TRA ỔN ĐỊNH TỔNG THỂ CÔNG TRÌNH

## Các điều kiện chống lật, đẩy nổi

- Hệ số an toàn chống lật: ≥ 1.5
- Hệ số an toàn chống đẩy nổi do áp lực thủy tĩnh: ≥ 1.2

## Chuyển vị đối với kết cấu bê tông cốt thép

### Chuyển vị theo phương ngang

- Chuyển vị đỉnh do tải trọng gió tiêu chuẩn: ≤ H<sub>c.trình</sub>/500 | TCVN 5574:2018
- Chuyển vị ngang tương đối giữa các tầng do tải trọng gió: ≤ h<sub>tầng</sub>/500 | TCVN 5574:2018

### Chuyển vị theo phương đứng

Xem bảng giới hạn độ võng trong Phụ Lục Tính Toán.

## Chuyển vị đối với kết cấu thép

| Loại kết cấu | Tải trọng và chuyển vị | Tải trọng và chuyển vị | Ghi chú |
|---|---|---|---|
| **I/ Kèo (Chuyển vị đứng)** | Hoạt tải | Tĩnh tải + Hoạt tải | |
| a/ Treo trần thạch cao | L/360 | L/240 | |
| b/ Treo trần khác trần thạch cao | L/240 | L/180 | |
| c/ Không treo trần | L/180 | L/120 | |
| **II/ Cột (Chuyển vị ngang)** | Tĩnh tải + Tải trọng gió | Tĩnh tải + Tải trọng gió | Gió 10 năm |
| | H/60 | H/60 | Gió 10 năm |
| **III/ Kết cấu sàn (Chuyển vị đứng)** | Hoạt tải | Tĩnh tải + Hoạt tải | |
| Dầm chính, Dầm phụ, Tấm Decking, Tấm Checker | L/360 | L/240 | |

---

# BỀ RỘNG VẾT NỨT CHO PHÉP

{{noi_dung_ve_net}}

---

# ĐỘ LÚN CỦA MÓNG

- Độ lún cho phép của móng: 80mm (hoặc 10cm theo Bảng 16 TCVN 9362:2012 cho nhà khung BTCT) | TCVN 9362:2012
- Độ lún lệch cho phép của móng: 1/1000 (hoặc 0.002 theo Bảng 16 TCVN 9362:2012) | TCVN 9362:2012

---

# CÁC YÊU CẦU VỀ CHỐNG THẤM & ĐỘ BỀN LÂU TRONG MÔI TRƯỜNG XÂM THỰC (TCVN 12041:2017)

{{noi_dung_chong_tham}}

---

# PHẦN MỀM PHÂN TÍCH VÀ TÍNH TOÁN

| STT | Phần mềm | Chức năng |
|:---:|---|---|
| 1 | ETABS | Phân tích kết cấu BTCT, Thép |
| 2 | SAP2000 | Phân tích kết cấu |
| 3 | SAFE | Phân tích và thiết kế móng, sàn |
| 4 | PLAXIS 2D / 3D | Phân tích địa kỹ thuật và tường vây hố đào |
| 5 | Excel, Python | Tính toán chi tiết các cấu kiện |

---

# TẢI TRỌNG VÀ TỔ HỢP TẢI TRỌNG

## Trọng lượng riêng của các loại vật liệu

| STT | Loại vật liệu | Trọng lượng riêng | Đơn vị |
|:---:|---|---:|:---:|
| 1 | Bê tông cốt thép | 25.0 | kN/m³ |
| 2 | Bê tông bình thường | 24.0 | kN/m³ |
| 3 | Thép xây dựng | 78.5 | kN/m³ |
| 4 | Gạch nặng | 18.0 | kN/m³ |
| 5 | Vữa xây tô | 18.0 | kN/m³ |
| 6 | Nước | 10.0 | kN/m³ |
| 7 | Đất sét pha cát | 18.0 | kN/m³ |
| 8 | Đất sét | 17.0 | kN/m³ |

## Tải trọng tạm thời dài hạn và ngắn hạn

Tải trọng tạm thời dài hạn và ngắn hạn tuân thủ theo TCVN 2737:2023.

## Tải trọng thường xuyên

Tải trọng thường xuyên tuân thủ theo TCVN 2737:2023.

## Tải trọng đặc biệt

Tải trọng đặc biệt tuân thủ theo TCVN 2737:2023 và TCVN 9386:2025.

## Tải trọng gió

{{noi_dung_tai_trong_gio}}

## Tổ hợp tải trọng - TCVN 2737:2023

{{to_hop_tai_trong_tcvn}}

{{to_hop_tai_trong_sls}}

---

# VẬT LIỆU KẾT CẤU

## Bê tông

{{vat_lieu_be_tong}}

## Cốt thép

- Φ < 10: CB240-T (TCVN 1651-1:2018) có f<sub>y</sub> = 240 MPa
- Φ ≥ 10: CB400-V hoặc CB500-V (TCVN 1651-2:2018) có f<sub>y</sub> = 400 / 500 MPa

## Kết cấu thép

{{vat_lieu_thep_can}}

---

# CHIỀU DÀY LỚP BÊ TÔNG BẢO VỆ

{{lop_be_tong_bao_ve}}

---

# PHỤ LỤC TÍNH TOÁN

{{#each phu_luc_items}}
## PHỤ LỤC TÍNH TOÁN {{ten_hang_muc}}

{{#if has_mo_hinh}}
### Mô hình tính toán
{{mo_hinh_mo_ta}}
{{/if}}

{{#if has_tai_trong}}
### Tải trọng tác dụng
{{tai_trong_mo_ta}}
{{/if}}

{{#if has_tai_trong_gio}}
### Tải trọng gió
{{tai_trong_gio_mo_ta}}
{{/if}}

{{#if has_mong}}
### Tính toán đài móng
{{mong_mo_ta}}
{{/if}}

{{#if has_khung}}
### Tính toán khung kèo thép
{{khung_mo_ta}}
{{/if}}

{{#if has_xa_go}}
### Tính toán xà gồ
{{xa_go_mo_ta}}
{{/if}}

{{#if has_lien_ket}}
### Tính toán liên kết
{{lien_ket_mo_ta}}
{{/if}}

---
{{/each}}

---

## BẢNG TỔNG HỢP KIỂM TRA

{{bang_tong_hop}}

---

# CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---|---|---|---|
| Người tính | {{nguoi_tinh}} | | {{ngay_tinh}} |
| Người kiểm tra | {{nguoi_kiem_tra}} | | {{ngay_kiem_tra}} |
| Người duyệt | {{nguoi_duyet}} | | {{ngay_duyet}} |
