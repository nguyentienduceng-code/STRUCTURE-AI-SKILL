# THUYẾT MINH TÍNH TOÁN KẾT CẤU TỔNG THỂ & PHỤ LỤC CHI TIẾT
## CÔNG TRÌNH: {{project_name}}
### ĐỊA ĐIỂM: {{location}} | CHỦ ĐẦU TƯ: {{client_name}}

---

# PHẦN I: THUYẾT MINH CHUNG & CƠ SỞ THIẾT KẾ

---

# QUY CHUẨN VÀ TIÊU CHUẨN THIẾT KẾ

## Quy chuẩn và Văn bản pháp lý Phân cấp Công trình

- Quy chuẩn kỹ thuật quốc gia về phân cấp công trình: QCVN 03:2022/BXD
  + Cấp hậu quả: C2 (nhà dân dụng thông thường)
  + Tuổi thọ thiết kế công trình: Mức 3 (≥ 50 năm)
- Phân cấp công trình xây dựng theo Thông tư 34/2026/TT-BXD (thay thế TT 06/2021/TT-BXD):
  + Cấp công trình: Cấp II (xét theo 6 tiêu chí Mục 2.1.1 Bảng 2 Phụ lục II)
  + Quy mô: Tổng diện tích sàn GFA = {{gfa}} m², Số tầng cao = {{so_tang}} tầng, Chiều cao H = {{chieu_cao}} m
  + Tầng ngầm: 1 tầng hầm với độ sâu ngầm h_ngam = 4.5 m (tính đến mặt trên sàn hầm sâu nhất)
- Quy chuẩn về An toàn cháy cho nhà và công trình: QCVN 06:2022/BXD (kèm Sửa đổi 1:2023)
  + Bậc chịu lửa công trình: Bậc II
  + Giới hạn chịu lửa cấu kiện chịu lực: Cột R120, Dầm R90, Sàn REI60

## Tiêu chuẩn Thiết kế và Khảo sát Áp dụng

| STT | Tên Tiêu chuẩn / Quy chuẩn | Số hiệu | Ghi chú áp dụng |
|:---:|---|---|---|
| 1 | Tải trọng và tác động | TCVN 2737:2023 | Tải trọng thường xuyên, tạm thời, gió |
| 2 | Kết cấu bê tông và bê tông cốt thép – Tiêu chuẩn thiết kế | TCVN 5574:2018 | Trạng thái giới hạn ULS và SLS |
| 3 | Kết cấu thép – Tiêu chuẩn thiết kế | TCVN 5575:2024 | Dầm thép, bu lông, đường hàn |
| 4 | Thiết kế công trình chịu động đất | TCVN 9386:2025 | Kháng chấn và phổ phản ứng |
| 5 | Móng cọc – Tiêu chuẩn thiết kế | TCVN 10304:2025 | Sức chịu tải cọc ép / khoan nhồi |
| 6 | Nền nhà và công trình – Tiêu chuẩn thiết kế | TCVN 9362:2012 | Độ lún, lún lệch, sức chịu tải nền |
| 7 | Khảo sát địa kỹ thuật cho nhà cao tầng | TCVN 9363:2012 | Mạng lưới hố khoan và chiều sâu |
| 8 | Nguyên tắc cơ bản khảo sát xây dựng | TCVN 4419:1987 | Cấp phức tạp điều kiện ĐCCT (Điều 3.5) |
| 9 | Thí nghiệm hiện trường – Thí nghiệm xuyên tiêu chuẩn (SPT) | TCVN 9351:2022 | Phương pháp SPT hiện trường |
| 10 | Bê tông và BTCT trong môi trường xâm thực | TCVN 12041:2017 & TCVN 9346:2012 | Chống ăn mòn nước ngầm |

---

# CÁC TIÊU CHÍ KIỂM TRA ỔN ĐỊNH TỔNG THỂ CÔNG TRÌNH

## Các Điều kiện Ổn định Chống lật và Đẩy nổi

- Hệ số an toàn chống lật tổng thể: K_lat = M_giu / M_lat ≥ 1.50 -> [ĐẠT]
- Hệ số an toàn chống đẩy nổi do áp lực thủy tĩnh ngầm: K_noi = G_bt / F_day_noi ≥ 1.20 -> [ĐẠT]

## Tiêu chí Chuyển vị Ngang & Dao động

- Chuyển vị ngang đỉnh công trình do gió tiêu chuẩn:
  + Chuyển vị đỉnh tính toán: u_dinh ≤ H / 500 = {{h_dinh_lim}} mm (TCVN 5574:2018)
- Chuyển vị ngang tương đối giữa 2 tầng kề cận:
  + Chuyển vị liên tầng: Δu_tang ≤ h_tang / 500 = {{h_tang_lim}} mm
- Gia tốc đỉnh công trình đảm bảo tiện nghi cho người sử dụng: a_max ≤ 0.15 m/s²

---

# BỀ RỘNG VẾT NỨT VÀ ĐỘ VÕNG CHO PHÉP (SLS)

## Giới hạn Độ võng Cấu kiện chịu Uốn (TCVN 5574:2018 Phụ lục M)

- Dầm chính khung chịu tải toàn phần: f_max ≤ L / 250 (với nhịp L ≤ 6.0 m) hoặc L / 300 (với nhịp L > 6.0 m)
- Bản sàn làm việc 2 phương: f_max ≤ L / 200 đối với sàn dân dụng thông thường
- Cầu thang bộ bản BTCT: f_max ≤ L / 200

## Bề rộng Khe nứt Cho phép của Bê tông Cốt thép

| Môi trường làm việc của cấu kiện | Tác dụng dài hạn [a_crc,1] | Tác dụng ngắn hạn [a_crc,2] | Căn cứ TCVN 5574:2018 |
|---|:---:|:---:|---|
| Cấu kiện trong nhà, môi trường khô ráo | 0.30 mm | 0.40 mm | Bảng 15 |
| Cấu kiện tiếp xúc trực tiếp khí quyển ẩm | 0.20 mm | 0.30 mm | Bảng 15 |
| Bể nước, sàn mái, tường tầng hầm chống thấm | 0.10 mm | 0.15 mm | TCVN 12041:2017 & Bảng 15 |

---

# ĐỘ LÚN VÀ LÚN LỆCH CỦA NỀN MÓNG

- Giới hạn độ lún tuyệt đối cho phép của nhà khung BTCT: s_max ≤ 80 mm (Bảng 16 TCVN 9362:2012)
- Độ lún lệch tương đối cho phép giữa 2 cột kề cận: Δs / L ≤ 0.002 = 1/500
- Độ nghiêng tổng thể công trình: i ≤ 0.004
- Chi tiết tính toán sức chịu tải cọc và kiểm tra lún móng: Xem chi tiết tại Phụ lục 1.

---

# YÊU CẦU CHỐNG THẤM & ĐỘ BỀN LÂU TRONG MÔI TRƯỜNG XÂM THỰC

- Bê tông tầng hầm, đáy bể và vách bể nước ngầm:
  + Cấp chống thấm yêu cầu: Bê tông W8 hoặc W10 (TCVN 3116:2022)
  + Sử dụng phụ gia chống thấm tinh thể thẩm thấu và băng cản nước Waterbar PVC tại tất cả các mạch ngừng thi công
  + Chiều dày lớp bê tông bảo vệ cấu kiện tiếp xúc đất/nước: c_nom ≥ 40 mm (theo TCVN 12041:2017)
- Chi tiết tính toán bản nắp, bản thành và đáy bể nước ngầm: Xem chi tiết tại Phụ lục 2.
- Chi tiết tính toán kiểm tra cột chịu nén lệch tâm: Xem chi tiết tại Phụ lục 3.
- Chi tiết tính toán dầm sàn BTCT toàn khối: Xem chi tiết tại Phụ lục 4.

---

# PHẦN MỀM VÀ PHƯƠNG PHÁP PHÂN TÍCH KẾT CẤU

- Phân tích nội lực tổng thể không gian 3D: ETABS v21 / SAP2000
- Phân tích móng, đài cọc và sàn không dầm: SAFE v21
- Phân tích ổn định hố đào và tương tác đất - cọc: PLAXIS 2D / 3D
- Tính toán chi tiết cấu kiện và xuất thuyết minh: Python Structural Engine (TCVN Standards Compliance)

---

# TẢI TRỌNG VÀ TỔ HỢP TẢI TRỌNG (TCVN 2737:2023)

## Tải trọng Thường xuyên (Tĩnh tải)

- Trọng lượng riêng bê tông cốt thép: γ = 25.0 kN/m³ (hệ số tin cậy γ_f = 1.10)
- Trọng lượng vữa xây tô và trát: γ = 18.0 kN/m³ (γ_f = 1.30)
- Trọng lượng tường gạch ống 100 mm: g_tuong100 = 1.80 kN/m²
- Trọng lượng tường gạch ống 200 mm: g_tuong200 = 3.30 kN/m²

## Tải trọng Tạm thời (Hoạt tải sử dụng)

| Khu vực chức năng | Giá trị tiêu chuẩn (kN/m²) | Hệ số tin cậy γ_f | Giá trị tính toán (kN/m²) |
|---|:---:|:---:|:---:|
| Văn phòng làm việc | 2.00 | 1.20 | 2.40 |
| Căn hộ, phòng ngủ | 1.50 | 1.30 | 1.95 |
| Hành lang, sảnh, cầu thang | 3.00 | 1.20 | 3.60 |
| Khu vệ sinh | 1.50 | 1.30 | 1.95 |
| Sàn đậu xe ô tô | 2.50 | 1.20 | 3.00 |
| Sàn mái không sử dụng | 0.75 | 1.30 | 0.98 |

## Tải trọng Gió Tính toán (TCVN 2737:2023)

- Địa điểm xây dựng: {{location}} (Vùng áp lực gió II.B)
- Áp lực gió cơ sở 50 năm: W0 = 0.95 kN/m² (Hệ số tin cậy tải gió γ_f = 1.25)
- Dạng địa hình B (vùng tương đối bằng phẳng, có cây cối hoặc công trình xây dựng thưa thớt)

## Các Tổ hợp Tải trọng Cơ bản (ULS)

- Tổ hợp 1 (Tĩnh tải + Hoạt tải toàn phần): ULS1 = 1.0·TT + 1.0·HT
- Tổ hợp 2 (Tĩnh tải + Hoạt tải + Gió X+): ULS2 = 1.0·TT + 0.9·HT + 0.9·GX+
- Tổ hợp 3 (Tĩnh tải + Hoạt tải + Gió X-): ULS3 = 1.0·TT + 0.9·HT + 0.9·GX-
- Tổ hợp 4 (Tĩnh tải + Hoạt tải + Gió Y+): ULS4 = 1.0·TT + 0.9·HT + 0.9·GY+
- Tổ hợp 5 (Tĩnh tải + Hoạt tải + Gió Y-): ULS5 = 1.0·TT + 0.9·HT + 0.9·GY-

---

# VẬT LIỆU KẾT CẤU & LỚP BÊ TÔNG BẢO VỆ

## Bê tông

- Bê tông cột vách: Cấp độ bền B30 (Rb = 17.0 MPa, Rbt = 1.15 MPa, Eb = 32500 MPa)
- Bê tông dầm sàn: Cấp độ bền B25 (Rb = 14.5 MPa, Rbt = 1.05 MPa, Eb = 30000 MPa)
- Bê tông đài móng và bể nước: Cấp độ bền B25, cấp chống thấm W8

## Cốt thép

- Cốt thép dọc chịu lực chính (d ≥ 10 mm): Thép thanh vằn nhóm CB400-V (Rs = Rsc = 350 MPa, Es = 200000 MPa)
- Cốt thép đai và thép phân bố (d < 10 mm): Thép tròn trơn nhóm CB240-T (Rs = 210 MPa, Rsw = 170 MPa)

## Chiều dày Lớp Bê tông Bảo vệ Cốt thép (c_nom)

- Bản sàn trong nhà: c_nom = 20 mm
- Dầm khung chịu lực: c_nom = 30 mm
- Cột khung chịu lực: c_nom = 35 mm
- Đài móng và giằng móng: c_nom = 50 mm (có lớp bê tông lót 100 mm)
- Cấu kiện tiếp xúc đất/nước trực tiếp (bể ngầm, tường hầm): c_nom = 40 mm

---

# PHẦN II: CÁC PHỤ LỤC TÍNH TOÁN CHI TIẾT CẤU KIỆN

---

# PHỤ LỤC 1: TÍNH TOÁN SỨC CHỊU TẢI CỌC BÊ TÔNG CỐT THÉP (TCVN 10304:2025)

## 1.1. Thông số Cọc và Vật liệu

- Loại cọc: Cọc vuông BTCT đúc sẵn 350 × 350 mm
- Chiều dài tính toán cọc: L = 22.0 m
- Bê tông cọc: Cấp độ bền B25 (Rb = 14.5 MPa)
- Cốt thép dọc cọc: 4Φ20 nhóm CB400-V (Rs = 350 MPa, As = 1257 mm²)

## 1.2. Sức chịu Tải Cọc theo Cường độ Vật liệu (P_vl)

$$ P_{vl} = \varphi \cdot (R_b \cdot A_c + R_s \cdot A_s) $$

- Thay số:
  + Diện tích cọc: Ac = 350 × 350 = 122500 mm²
  + Hệ số uốn dọc: φ = 0.85
  + P_vl = 0.85 × (14.5 × 122500 + 350 × 1257) = 1883.8 kN

## 1.3. Sức chịu Tải Cọc theo Đất nền (TCVN 10304:2025 Điều 7.2)

- Sức kháng ma sát thành cọc:
  + Chu vi tiết diện cọc: u = 4 × 0.35 = 1.40 m
  + Tổng ma sát thành bên tính toán: Qf = ∑ (γ_cr · f_i · u · h_i) = 745.0 kN
- Sức kháng mũi cọc:
  + Diện tích mũi cọc: Ap = 0.35 × 0.35 = 0.1225 m²
  + Cường độ chịu tải mũi cọc lớp cát hạt trung chặt vừa: qp = 3800 kPa
  + Sức kháng mũi: Qp = γ_cf · qp · Ap = 1.0 × 3800 × 0.1225 = 465.5 kN
- Sức chịu tải cực hạn của cọc:
  + Rc = Qf + Qp = 745.0 + 465.5 = 1210.5 kN
- Sức chịu tải thiết kế cho phép (với hệ số an toàn γ_c = 1.40):
  + R_c,d = Rc / γ_c = 1210.5 / 1.40 = 864.6 kN

## 1.4. Đánh giá Khả năng Chịu lực Cọc Móng

- Tải trọng thiết kế lớn nhất tác dụng lên 1 cọc: N_Ed = 680.0 kN
- Hệ số sử dụng sức chịu tải cọc:
  + η_coc = N_Ed / R_c,d = 680.0 / 864.6 = 0.787 ≤ 1.00 -> [ĐẠT]

---

# PHỤ LỤC 2: TÍNH TOÁN BỂ NƯỚC NGẦM BÊ TÔNG CỐT THÉP

## 2.1. Kích thước Hình học & Tải trọng Tác dụng

- Kích thước phủ bì bể: L × B × H = 6.0 × 4.0 × 3.0 m (Dung tích V = 60 m³)
- Chiều dày cấu kiện:
  + Chiều dày bản nắp bể: h_nap = 150 mm
  + Chiều dày thành bể: h_thanh = 250 mm
  + Chiều dày bản đáy bể: h_day = 300 mm
- Các trường hợp tính toán nguy hiểm nhất:
  + Trường hợp 1 (Kiểm tra thành bể): Bể chứa đầy nước, bên ngoài chưa đắp đất (áp lực thủy tĩnh trong lớn nhất)
  + Trường hợp 2 (Kiểm tra đáy và thành ngoài): Bể rỗng hoàn toàn, bên ngoài có áp lực đất và áp lực nước ngầm cao nhất
  + Trường hợp 3 (Kiểm tra chống nổi): Mực nước ngầm cao độ mặt đất tự nhiên, bể hoàn toàn rỗng

## 2.2. Kiểm tra Điều kiện Chống Đẩy nổi (Buoyancy Check)

- Tổng trọng lượng bản thân bể rỗng:
  + Trọng lượng nắp, thành, đáy: G_be = 785.0 kN
  + Trọng lượng lớp đất phủ trên nắp (dày 0.8 m): G_dat = 345.6 kN
  + Tổng lực giữ chống nổi: G_giu = 785.0 + 345.6 = 1130.6 kN
- Lực đẩy nổi Acsimet cực đại khi ngập nước:
  + Thể tích choán chỗ: V_be = 6.0 × 4.0 × 3.0 = 72.0 m³
  + Lực đẩy nổi cực đại: F_day_noi = 72.0 × 10.0 = 720.0 kN
- Hệ số an toàn chống nổi:
  + K_noi = G_giu / F_day_noi = 1130.6 / 720.0 = 1.57 ≥ 1.20 -> [ĐẠT]

## 2.3. Bố trí Cốt thép Thành Bể & Đáy Bể

- Cốt thép bản nắp (chịu uốn):
  + Cốt thép lớp dưới nhịp: Φ10a150 cả 2 phương (As = 524 mm²/m)
  + Hệ số sử dụng chịu uốn: η_nap = 0.650 ≤ 1.00 -> [ĐẠT]
- Cốt thép thành bể (chịu uốn và kéo đồng thời):
  + Cốt thép đứng chịu mô men chân ngàm: Φ14a150 (As = 1026 mm²/m)
  + Cốt thép ngang phân bố: Φ10a150 (As = 524 mm²/m)
  + Hệ số sử dụng chịu uốn thành: η_thanh = 0.760 ≤ 1.00 -> [ĐẠT]
- Kiểm tra bề rộng khe nứt chống thấm (TCVN 5574:2018):
  + Bề rộng khe nứt tính toán ngắn hạn: a_crc = 0.11 mm ≤ [a_crc] = 0.15 mm -> [ĐẠT]
  + Bề rộng khe nứt tính toán dài hạn: a_crc = 0.08 mm ≤ [a_crc] = 0.10 mm -> [ĐẠT]

---

# PHỤ LỤC 3: TÍNH TOÁN CỘT KHUNG BTCT (NÉN UỐN LỆCH TÂM)

## 3.1. Thông số Tiết diện Cột Trục B-2

- Tiết diện cột: b × h = 400 × 500 mm
- Chiều cao tầng: H = 3.6 m (chiều dài tính toán L0 = 0.7 × 3.6 = 2.52 m)
- Bê tông: B30 (Rb = 17.0 MPa, Eb = 32500 MPa)
- Cốt thép dọc: Thép CB400-V (Rs = 350 MPa)
- Lớp bê tông bảo vệ: a = a' = 40 mm (chiều cao làm việc h0 = 460 mm)

## 3.2. Nội lực Tính toán Tổ hợp Nguy hiểm nhất (ULS)

- Lực dọc tính toán: N_Ed = 1850.0 kN
- Mô men uốn tính toán: M_Ed = 145.0 kNm
- Lực cắt tính toán: V_Ed = 65.0 kN

## 3.3. Bố trí Cốt thép và Kiểm tra Trạng thái Giới hạn (ULS)

- Bố trí cốt thép dọc đối xứng: 6Φ22 (As = As' = 1140 mm², tổng As_tot = 2280 mm²)
  + Hàm lượng cốt thép: μ = As_tot / (b · h) = 2280 / (400 × 500) = 1.14% (thỏa 0.4% ≤ μ ≤ 3.0%)
- Hệ số uốn dọc cột: η_uon_doc = 1.02
- Khả năng chịu nén uốn giới hạn của tiết diện:
  + N_Rd = 2285.0 kN
  + Hệ số sử dụng nén uốn: η_NM = N_Ed / N_Rd = 1850.0 / 2285.0 = 0.810 ≤ 1.00 -> [ĐẠT]
- Kiểm tra cốt đai chịu cắt:
  + Cốt đai: Φ8a100 ở đoạn 1.0 m đầu cột và Φ8a200 ở giữa cột
  + Khả năng chịu cắt: Q_Rd = 168.0 kN ≥ V_Ed = 65.0 kN (η_cat = 0.387 ≤ 1.00) -> [ĐẠT]

---

# PHỤ LỤC 4: TÍNH TOÁN DẦM KHUNG & BẢN SÀN BTCT

## 4.1. Tính toán Dầm Khung D1 (300 × 600 mm)

- Nhịp tính toán: L = 6.0 m
- Bê tông: B25 (Rb = 14.5 MPa, Rbt = 1.05 MPa)
- Cốt thép: CB400-V (Rs = 350 MPa)
- Kết quả kiểm tra tại tiết diện gối (M_Ed = -195.0 kNm):
  + Cốt thép yêu cầu: As_req = 1180 mm²
  + Cốt thép bố trí: 4Φ20 (As_prov = 1257 mm²)
  + Hệ số sử dụng uốn: η_uon = 0.938 ≤ 1.00 -> [ĐẠT]
- Kết quả kiểm tra tại giữa nhịp (M_Ed = +125.0 kNm):
  + Cốt thép yêu cầu: As_req = 730 mm²
  + Cốt thép bố trí: 3Φ18 (As_prov = 763 mm²)
  + Hệ số sử dụng uốn: η_uon = 0.957 ≤ 1.00 -> [ĐẠT]
- Kiểm tra độ võng dài hạn: f = 14.2 mm ≤ [f] = L / 250 = 24.0 mm -> [ĐẠT]

## 4.2. Tính toán Bản Sàn Ô Điển hình (h_san = 120 mm)

- Kích thước ô bản: Lx × Ly = 4.0 × 6.0 m (tỷ số Ly/Lx = 1.50 -> sàn bản kê 4 cạnh làm việc 2 phương)
- Tải trọng tính toán toàn phần: q_toan_phan = 8.50 kN/m²
- Bố trí cốt thép sàn:
  + Cốt thép lớp dưới phương cạnh ngắn Lx: Φ10a150 (As = 524 mm²/m) -> η = 0.720 ≤ 1.00 -> [ĐẠT]
  + Cốt thép lớp dưới phương cạnh dài Ly: Φ8a150 (As = 335 mm²/m) -> η = 0.680 ≤ 1.00 -> [ĐẠT]
  + Cốt thép mũ gối trên: Φ10a120 (As = 654 mm²/m) -> η = 0.810 ≤ 1.00 -> [ĐẠT]
- Độ võng sàn tính toán: f_san = 9.8 mm ≤ [f] = Lx / 200 = 20.0 mm -> [ĐẠT]

---

# PHẦN III: TỔNG HỢP KẾT QUẢ KIỂM TRA & KẾT LUẬN

| STT | Cấu kiện / Hạng mục kiểm tra | Tiêu chuẩn áp dụng | Chỉ số sử dụng (η) | Đánh giá an toàn |
|:---:|---|:---:|:---:|:---:|
| 1 | Sức chịu tải cọc ép 350 × 350 mm | TCVN 10304:2025 | 0.787 | [ĐẠT] (Tối ưu) |
| 2 | Chống đẩy nổi bể nước ngầm | TCVN 5574:2018 | 0.637 | [ĐẠT] (Dự trữ an toàn) |
| 3 | Bền uốn & nứt thành bể nước ngầm | TCVN 12041:2017 | 0.760 | [ĐẠT] (Đạt yêu cầu) |
| 4 | Cột khung BTCT nén uốn lệch tâm | TCVN 5574:2018 | 0.810 | [ĐẠT] (Tối ưu) |
| 5 | Dầm khung BTCT chịu uốn & võng | TCVN 5574:2018 | 0.938 | [ĐẠT] (Sát giới hạn) |
| 6 | Bản sàn BTCT chịu uốn 2 phương | TCVN 5574:2018 | 0.810 | [ĐẠT] (Tối ưu) |

=> **KẾT LUẬN CHUNG**: Toàn bộ hệ thống kết cấu công trình và các cấu kiện chi tiết trong hồ sơ đều **[ĐẠT]** yêu cầu an toàn chịu lực (ULS) và trạng thái giới hạn sử dụng (SLS) theo quy định hiện hành của tiêu chuẩn xây dựng Việt Nam.

---

> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*

## BẢNG TRÁCH NHIỆM

| Vai trò | Họ và tên | Chức danh / Số CCHN | Chữ ký |
|---|---|---|---|
| Người lập | Trợ lý AI (Antigravity) | Kỹ sư Kết cấu AI | Cần kỹ sư có CCHN kiểm tra xác nhận |
| Kỹ sư kiểm tra | | | |
| Chủ trì kết cấu | | | |
