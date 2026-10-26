---
name: SKILLKC
parent: Design_Evaluation
version: 3.2.0
updated: 2026-10-26
description: >
  Chuyên gia Thẩm tra Chuyên sâu Kết cấu (Principal Structural Engineering Auditor) theo TCVN 2737:2023,
  TCVN 5575:2024, TCVN 5574:2018, TCVN 9362:2012, TCVN 9386:2025, TCVN 12041:2017. Bản v3.2.0 tích hợp
  bộ kiểm toán Phân tích Tải trọng, Tổ hợp Nghịch đảo, Đường truyền lực 3D, Đọng nước Sập mái (Ponding Collapse)
  và Kiểm toán Chống ăn mòn Môi trường Công nghiệp theo khuyến nghị của Argon Benchmark.
---

# SKILLKC — CHUYÊN GIA THẨM TRA CHUYÊN SÂU KẾT CẤU CẤP CHỦ TRÌ (v3.2.0)

## 1. BỘ KIỂM TOÁN CHUYÊN SÂU TẢI TRỌNG & TỔ HỢP TẢI TRỌNG (TCVN 2737:2023)
1. **Kiểm toán Công thức Tải trọng Gió & Áp lực Khí động Trong nhà ($c_i$):**
   $$W = W_{3s,20} \cdot k(z_e) \cdot G_f \cdot (c_e - c_i) \cdot \gamma_f \cdot \gamma_n$$
   - Kiểm tra $G_f$ theo đúng Phụ lục E TCVN 2737:2023 (bác bỏ mọi công thức tự chế $G_f = 0.85 + h/1010$).
   - Kiểm tra tổ hợp dấu bất lợi nhất giữa $c_e$ và $c_i \in [-0.3, +0.2]$ (hoặc $[-0.5, +0.6]$ khi có độ mở vách đón gió/khuất gió $>5\%$).
2. **Kiểm toán Tổ hợp Đảo dấu Nội lực (Gió bốc / Nhổ cột / Lật móng / Đẩy nổi):**
   - Bắt buộc áp dụng $\gamma_{f,\text{tĩnh tải giữ}} = 0.90$ và loại bỏ toàn bộ phần tải trọng lắp đặt sau (như Pin mặt trời Solar) ra khỏi thành phần giữ ổn định.
3. **Kiểm toán Tổ hợp Cực đoan Bể chứa Ngầm (Cấm Tự Triệt Tiêu Áp Lực Ngang):**
   - Kiểm tra độc lập 2 trạng thái: (a) Bể đầy nước + Không đất/nước ngầm ngoài; và (b) Bể rỗng bảo trì + Đầy đất ($K_0$) + Nước ngầm dâng ngập + Hoạt tải xe chữa cháy ($20 \div 30\text{ kPa}$) trên nắp bể.
4. **Kiểm toán Tác động Đọng Nước Mưa & Nguy cơ Sập Mái (Ponding Collapse Audit — Điều 10.3 TCVN 2737:2023):**
   - Với nhà xưởng khẩu độ lớn nhịp $\ge 20\text{ m}$ và độ dốc mái $i \le 10\%$, bắt buộc kiểm toán khả năng tích tụ nước mưa khi sê nô máng xối biên bị nghẽn cục bộ hoặc lượng mưa mưa bão cực đoan vượt quá khả năng thoát nước của ống đứng.
   - Kiểm toán độ cứng chống biến dạng tích lũy (Progressive Ponding Instability) của kèo mái và hệ xà gồ biên giáp sê nô; yêu cầu bắt buộc bố trí tay đỡ thép hình (bracket) định hình cho máng xối Inox và tính dự phòng ống tràn khẩn cấp (Emergency Overflow Scupper).

## 2. BỘ KIỂM TOÁN ĐƯỜNG TRUYỀN LỰC, SƠ ĐỒ TÍNH & ĐỘ CỨNG LIÊN KẾT
1. **Kiểm tra Tương thích Sơ đồ Chân cột — Móng — Nền đất:**
   - Với hệ kết cấu tĩnh định (như Khung 1 hàng cột công son Nhà để xe), nếu đáy móng xuất hiện ứng suất kéo ($\sigma_{\min} < 0$) hoặc $e > L/6$, kết luận ngay liên kết chân cột mất khả năng ngàm cứng và tính độ võng bổ sung đầu mút công son do xoay móng: $\Delta_{\text{total}} = \Delta_{\text{elastic}} + \theta_{\text{foundation}} \cdot L_{\text{cantilever}}$.
   - Với khung nhiều nhịp chân khớp có $\mu_x > 2.0$, bắt buộc yêu cầu phân tích bậc 2 ($P-\Delta$).
2. **Kiểm tra Điều kiện Biên Ổn định Tổng thể Ngoài mặt phẳng (LTB — $L_{ef}$):**
   - Đối chiếu giá trị $L_{ef}$ khai báo trong bảng tính dầm/kèo chữ I với khoảng cách thực tế của **Thanh chống cánh dưới (Flange Stay)** trên bản vẽ tại vùng mô men âm (nách kèo) và dưới tổ hợp gió bốc.
3. **Kiểm tra Ổn định Cục bộ Bản bụng mảnh ($\bar{\lambda}_w, \bar{\lambda}_{uw}$) & Lỗi nội suy `#VALUE!`:**
   - Kiểm tra cả ngưỡng sườn ngang ($\bar{\lambda}_w > 2.3$ hoặc $3.2$) và ngưỡng sườn dọc ($\bar{\lambda}_w > [\bar{\lambda}_{uw}]$). Quét toàn bộ các ô `#VALUE!` trong bảng nội suy $C_{cr}$ khi $m_x = 0$.
4. **Kiểm tra Đường truyền lực Không gian 3D, Hệ Giằng & Chi tiết Nút cứng:**
   - Kiểm tra tính liên tục của hệ thanh chống dọc (Strut Tube) và hệ giằng cột dọc nhà tại cả trục biên lẫn trục cột giữa.
   - Kiểm tra chi tiết liên kết nách kèo và đỉnh cột giữa: bắt buộc kiểm toán đường hàn góc/đối đầu cánh kèo và bản mã ốp nối cánh trên chịu kéo ($PL$) chống nguy cơ xé toạc bản mã đỉnh cột.
5. **Kiểm toán Độ Bền Lâu Dài & Chống Ăn Mòn Công Nghiệp (TCVN 12041:2017 & TCVN 9346:2012):**
   - Kiểm tra môi trường ăn mòn đặc thù (hơi axit, dung môi lưu hóa cao su khuôn đúc, nhiệt độ). Cấm tuyệt đối sơn chống rỉ alkyd mỏng ($70 \div 80\text{ µm}$) cho bản bụng siêu mỏng ($5\text{ mm}$); bắt buộc chỉ định hệ sơn Epoxy bảo vệ 3 lớp (chiều dày màng sơn khô $\ge 210\text{ µm}$).
   - Kiểm tra quy cách chiều cao đường hàn $h_f$, que hàn $E43/E50$ và tỷ lệ siêu âm mối hàn Cấp I/II theo TCVN 9974:2013 trên bản vẽ gia công.

