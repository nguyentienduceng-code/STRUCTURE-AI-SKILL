# THUYẾT MINH TÍNH TOÁN BIỆN PHÁP THI CÔNG HỐ ĐÀO (BPTC) & ĐÁNH GIÁ KHẢO SÁT ĐỊA KỸ THUẬT
# Template v3.1.0 — Cấu trúc chuẩn 6 Chương + PHỤ LỤC A (BẮT BUỘC GIỮ)
# Áp dụng: SKILL_GEOTECH v3.1.0 — Sunrise HK3 Pattern & TCVN 9363:2012 Compliance
# Tiêu chuẩn: TT 06/2021 & TT 34/2026/TT-BXD, QCVN 03:2022/BXD, TCVN 9363:2012, TCVN 4419:1987, TCVN 9351:2022, TCVN 12041:2017

---

## MỤC LỤC

1. GIỚI THIỆU & PHÂN CẤP CÔNG TRÌNH
 1.1. Tổng quan & Phân cấp công trình (TT 06/2021 & TT 34/2026/TT-BXD, QCVN 03:2022/BXD)
 1.2. Phương án thi công
 1.3. Cơ sở thiết kế
 1.4. Tiêu chuẩn áp dụng

2. THÔNG SỐ ĐẦU VÀO & ĐÁNH GIÁ KHẢO SÁT ĐỊA CHẤT (TCVN 9363:2012)
 2.1. Mặt cắt địa chất & Đánh giá khối lượng khảo sát (TCVN 9363:2012, TCVN 4419:1987)
 2.2. Thông số địa chất sử dụng trong mô hình
 2.3. Thông số địa chất thủy văn & Đánh giá ăn mòn nước ngầm (TCVN 12041:2017, TCVN 9346:2012)
 2.4. Thông số cừ vây / tường vây
 2.5. Hệ giằng chống thép hình
 2.6. Phụ tải mặt đất

3. KẾT QUẢ MÔ HÌNH TÍNH TOÁN
 3.1. Mặt cắt 1-1
 3.1.1. Chuyển vị
 3.1.2. Lún nền
 3.1.3. Nội lực cừ vây
 3.1.4. Nội lực hệ giằng
 3.1.5. Hệ số ổn định tổng thể
 3.2. Mặt cắt 2-2 *(nếu có nhiều hơn 1 mặt cắt bất lợi)*

4. KIỂM TRA KHẢ NĂNG CHỊU LỰC
 4.1. Cừ vây [Loại cừ]
 4.2. Chuyển vị ngang và lún nền công trình lân cận
 4.3. Hệ số ổn định tổng thể

5. TÍNH TOÁN, KIỂM TRA HỆ GIẰNG
 5.1. Mô hình tính toán (ETABS)
 5.2. Kết quả kiểm tra (Bảng ETABS Design Summary)

6. KẾT LUẬN
 6.1. Kết luận

**PHỤ LỤC A: GIẢI TRÌNH TÍNH TOÁN CHI TIẾT THÔNG SỐ ĐẤT** *(BẮT BUỘC KHÔNG ĐƯỢC BỎ)*
 A.1. Cơ sở lý thuyết và phương pháp xác định thông số
 A.2. Quy đổi thông số từng lớp đất
 A.3. Bảng kiểm chứng so sánh với Ground Truth

---

## CHƯƠNG 1: GIỚI THIỆU & PHÂN CẤP CÔNG TRÌNH

### 1.1. Tổng quan & Phân cấp công trình

**Dự án:** [TÊN DỰ ÁN — điền tên đầy đủ]
**Địa điểm:** [ĐỊA CHỈ XÂY DỰNG]
**Quy mô hạng mục:** [Số tầng nổi, số tầng hầm, tổng diện tích sàn GFA m², chiều cao m, chiều sâu ngầm m đến mặt trên sàn tầng hầm sâu nhất]

- **Cấp công trình xây dựng** (theo **Thông tư 06/2021/TT-BXD** và **Thông tư 34/2026/TT-BXD**, Phụ lục I & Mục 2.1.1 Bảng 2 Phụ lục II): **Cấp [Đặc biệt / I / II / III]** *(xét đồng thời 6 tiêu chí: chiều cao, số tầng cao, tổng diện tích sàn GFA, nhịp kết cấu lớn nhất, độ sâu ngầm tính đến mặt trên sàn tầng hầm sâu nhất, số tầng ngầm; lấy cấp cao nhất)*.
- **Cấp hậu quả & Tuổi thọ thiết kế** (theo **QCVN 03:2022/BXD**, Mục 2.1 Bảng 1 & Phụ lục A): Cấp hậu quả **[C1 / C2 / C3]**, Tuổi thọ thiết kế **[Mức 3: Tối thiểu 50 năm / Mức 4: Tối thiểu 100 năm theo yêu cầu CĐT]**.
- **Cấp phức tạp điều kiện địa chất công trình** (theo **Điều 3.5 và Phụ lục 2 TCVN 4419:1987**, dẫn chiếu tại **Chú thích Điều 5.2.4.1 TCVN 9363:2012**): **Cấp [I - Đơn giản / II - Trung bình / III - Phức tạp]**.

### 1.2. Phương án thi công

Thi công phần hầm công trình theo phương án **đào mở - hệ giằng** (hoặc **Semi Top-down / Bottom-up với tường vây BTCT**).

### 1.3. Cơ sở thiết kế

- Báo cáo khảo sát địa chất do chủ đầu tư cung cấp
- Bản vẽ và Nhiệm vụ thiết kế do Chủ đầu tư cung cấp
- Khảo sát hiện trạng xung quanh công trình

### 1.4. Tiêu chuẩn áp dụng

| Tiêu chuẩn / Quy chuẩn | Nội dung |
|:---|:---|
| **Thông tư 34/2026/TT-BXD** (và **TT 06/2021/TT-BXD**) | Quy định về phân cấp công trình xây dựng và hướng dẫn áp dụng trong quản lý hoạt động đầu tư xây dựng (hiệu lực từ 01/07/2026, thay thế TT 06/2021 và TT 02/2025) |
| **QCVN 03:2022/BXD** | Quy chuẩn kỹ thuật quốc gia về phân cấp công trình phục vụ thiết kế xây dựng (Cấp hậu quả C1–C3, Tuổi thọ thiết kế Bảng 1) |
| **TCVN 9363:2012** | Khảo sát cho xây dựng — Khảo sát địa kỹ thuật cho nhà cao tầng (Điều 5.2 TKCS, Điều 5.3.6 & Phụ lục D TKKT, Điều 5.4 BVTC) |
| **TCVN 4419:1987** | Khảo sát cho xây dựng — Nguyên tắc cơ bản (Điều 3.5 & Phụ lục 2: Phân cấp mức độ phức tạp điều kiện ĐCCT) |
| **TCVN 9351:2022** | Đất xây dựng — Phương pháp thí nghiệm hiện trường — Thí nghiệm xuyên tiêu chuẩn (SPT) (thay thế TCVN 9351:2012) |
| **TCVN 12041:2017** & **TCVN 9346:2012** | Thiết kế độ bền lâu và bảo vệ chống ăn mòn cho kết cấu bê tông và BTCT trong môi trường xâm thực (thay thế TCVN 3994:1985 đã hết hiệu lực) |
| **TCVN 5574:2018** | Kết cấu bê tông và bê tông cốt thép — Tiêu chuẩn thiết kế |
| **TCVN 5575:2024** | Kết cấu thép — Tiêu chuẩn thiết kế |
| **TCVN 2737:2023** | Tải trọng và tác động — Tiêu chuẩn thiết kế |
| **TCVN 10304:2025** | Móng cọc — Tiêu chuẩn thiết kế (thay thế TCVN 10304:2014) |
| **CIRIA C760:2017** | Guidance on embedded retaining wall design |
| **Eurocode 7 (EN 1997-1)** | Geotechnical design |

---

## CHƯƠNG 2: THÔNG SỐ ĐẦU VÀO & ĐÁNH GIÁ KHẢO SÁT ĐỊA CHẤT (TCVN 9363:2012)

### 2.1. Mặt cắt địa chất & Đánh giá khối lượng khảo sát theo TCVN 9363:2012

Công tác khảo sát địa chất do [Đơn vị khảo sát] thực hiện với [X] hố khoan, chiều sâu khảo sát [Y]m. Đối chiếu quy định của **TCVN 9363:2012**:
- **Khoảng cách / Mật độ hố khoan**:
  - Giai đoạn Thiết kế cơ sở (TKCS): yêu cầu khoảng cách **`50 m – 200 m`** (**Điều 5.2.4.2 TCVN 9363:2012**).
  - Giai đoạn Thiết kế kỹ thuật (TKKT): yêu cầu khoảng cách **`20 m – 30 m`** hoặc lưới `20m×20m` đến `30m×30m` cho ĐCCT Cấp III (**Điều 5.3.6.2, Phụ lục D Mục D.1 & Bảng D.1 TCVN 9363:2012**).
- **Tỷ lệ hố khoan khống chế (Control Boreholes)**: Số điểm thăm dò khống chế phải đạt **tối thiểu 1/3 (`>= 33.3%`) tổng số điểm thăm dò** (**Điều 5.3.6.3 TCVN 9363:2012**).
- **Chiều sâu hố khoan TKKT**: Sâu dưới mũi cọc thiết kế tối thiểu `5 m` (hoặc `3d – 5d` đối với nhóm cọc) và xuyên vào lớp đất tốt / đá phong hóa có `N_SPT >= 30 – 50` tối thiểu `3 m – 6 m` (**Điều 5.3.6.4, Điều 5.3.6.5 & Phụ lục D TCVN 9363:2012**).

### 2.2. Thông số địa chất sử dụng trong mô hình

*(Xem chi tiết cơ sở xác định từng thông số tại **PHỤ LỤC A** — bắt buộc đính kèm)*

| Thông số | Đơn vị | Lớp san lấp | Lớp 1: Sét pha | Lớp 2: Cát |
|:---|:---:|:---:|:---:|:---:|
| Mô hình | — | MC | HS | HS |
| Thoát nước | — | Drained | Undrained (B) | Drained |
| γ_unsat | kN/m³ | [X] | [X] | [X] |
| γ_sat | kN/m³ | [X] | [X] | [X] |
| E50_ref | kPa | [X] | [X] | [X] |
| Eoed_ref | kPa | [X] | [X] | [X] |
| Eur_ref | kPa | [X] | [X] | [X] |
| m | — | [X] | [X] | [X] |
| c' | kPa | [X] | [X] | [X] |
| φ' | ° | [X] | [X] | [X] |
| R_inter | — | [X] | [X] | [X] |
| K0 | — | [X] | [X] | [X] |

### 2.3. Thông số địa chất thủy văn & Đánh giá ăn mòn nước ngầm

- Mực nước ngầm ổn định ở mức **[X.X]m** so với mặt đất tự nhiên.
- Đánh giá tính ăn mòn của nước dưới đất đối với bê tông và BTCT theo **TCVN 12041:2017** và **TCVN 9346:2012** *(ghi chú: TCVN 3994:1985 đã hết hiệu lực, chỉ dùng đối chiếu tham khảo)*.

### 2.4. Thông số cừ vây / tường vây
### 2.5. Hệ giằng chống thép hình
### 2.6. Phụ tải mặt đất

---

## CHƯƠNG 3: KẾT QUẢ MÔ HÌNH TÍNH TOÁN
### 3.1. Mặt cắt 1-1
### 3.2. Mặt cắt 2-2

---

## CHƯƠNG 4: KIỂM TRA KHẢ NĂNG CHỊU LỰC
### 4.1. Cừ vây / Tường vây
### 4.2. Chuyển vị ngang và lún nền công trình lân cận (Rankin 1988 & Clough-O'Rourke 1990)
### 4.3. Hệ số ổn định tổng thể

---

## CHƯƠNG 5: TÍNH TOÁN, KIỂM TRA HỆ GIẰNG
### 5.1. Mô hình tính toán
### 5.2. Kết quả kiểm tra

---

## CHƯƠNG 6: KẾT LUẬN
### 6.1. Kết luận

---

# PHỤ LỤC A: GIẢI TRÌNH TÍNH TOÁN CHI TIẾT THÔNG SỐ ĐẤT
## *(BẮT BUỘC GIỮ LẠI — Cơ sở kiểm soát số liệu đầu vào)*

### A.1. Cơ sở Lý thuyết và Phương pháp Xác định Thông số
- Đất dính (Jamiolkowski et al. 1979, Stroud 1974, CIRIA C760): `E50_ref = Ke × Su`
- Đất rời (Bowles 1997, CIRIA C760, TCVN 9351:2022): `E50_ref = α × N_SPT`
- Mô đun tải lại-dỡ tải: `Eur_ref = 3 × E50_ref`
- Hệ số áp lực đất nghỉ: `K0 = 1 - sin(φ')` (Jaky 1944)

### A.2. Tính toán Chi tiết Từng Lớp Đất
### A.3. Bảng Kiểm chứng So sánh Thông số với Ground Truth
### A.4. Thông số Kết cấu Chắn giữ

> *Tài liệu do trợ lý AI (SKILL_GEOTECH v3.1.0) lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế.*
