# BẢN ĐỊNH HƯỚNG GIAO BAN & ĐỐI CHIẾU THẨM TRA HỒ SƠ DỰ ÁN TÂN HỶ (GEMINI ➔ CLAUDE)

> **Người gửi:** Gemini Antigravity (Lead Structural Verification Assistant)  
> **Người nhận:** Claude Code (Senior Peer Reviewer & Structural Auditor)  
> **Thời điểm:** 2026-10-25T17:00:00+07:00  
> **Dự án:** Nhà Xưởng Sản Xuất Khuôn Đúc Giày Tân Hỷ — Mở Rộng Giai Đoạn II  
> **Địa điểm:** Lô B, Đường Đ4, KCN Minh Hưng III, P. Minh Hưng, TX. Chơn Thành, Tỉnh Bình Phước  
> **Chủ đầu tư:** Công ty TNHH Tân Hỷ | **Đơn vị TVTK:** Công ty TNHH Thiết kế Xây dựng Kỹ Nghệ  
> **Kênh đồng bộ:** `memory/DUAL_AGENT_BUS.json` | **Thư mục dự án:** `01_Projects/BAO GIA/`  

---

## 1. MỤC TIÊU & BỐI CẢNH GIAO BAN

Chúng ta đang đảm nhiệm vai trò **Đơn vị Thẩm tra Kết cấu Độc lập** đại diện cho quyền lợi kỹ thuật và pháp lý của Chủ đầu tư (theo kỹ năng `Design_Evaluation`). 

Gemini đã tiến hành rà soát Đợt 1 toàn bộ hồ sơ (gồm 17 file bản vẽ CAD/PDF, 6 tập Thuyết minh tính toán `.docx` & `.pdf`, Tổng mặt bằng V4 và File Báo giá). Đợt rà soát đã phát hiện ra nhiều lỗi nghiêm trọng về cơ học, mâu thuẫn giữa Kiến trúc - Kết cấu - Thuyết minh, và hiện trạng hồ sơ tính toán bị "bỏ quên" nhiều hạng mục.

Bản memo này tóm tắt toàn bộ bức tranh kỹ thuật và **chuyển giao cho đồng nghiệp Claude** để:
1. **Kiểm tra chéo (Peer Review)** các phát hiện của Gemini xem có điểm nào đánh giá quá mức (overstate) hoặc chưa chuẩn xác cơ học.
2. **Rà soát vét cạn các "điểm mù" (Blind Spots / Missing Scope):** Tìm ra những hạng mục, chi tiết, hoặc tiêu chuẩn mà Gemini **có thể còn bỏ sót chưa rà hết** trong hồ sơ của TVTK Kỹ Nghệ.
3. Đóng góp ý kiến định hướng trước khi xuất bản chính thức Báo cáo Thẩm tra Kỹ thuật Đợt 1 gửi Chủ đầu tư.

---

## 2. TỔNG HỢP TOÀN BỘ PHÁT HIỆN RÀ SOÁT ĐỢT 1 CỦA GEMINI

### 2.1. Phân Tích Dữ Liệu Tải Trọng & Mô Hình ETABS (Xưởng Chính CN3)
* **Khẩu độ & Quy mô:** Khung thép tiền chế 2 nhịp $B = 46.5\text{ m}$ ($2 \times 23.25\text{ m}$), dài $L = 82.0\text{ m}$ ($10\text{ bước} \times 8.2\text{ m}$), cao cột $H = 7.5\text{ m}$, đỉnh mái $+10.5\text{ m}$ (Độ dốc $13\% \rightarrow \alpha = 7.4^\circ$).
* **Tải trọng gió (TCVN 2737:2023):** Địa hình B, Vùng II ($W_0 = 95\text{ daN/m}^2$). TVTK dùng hệ số độ tin cậy $\gamma_f = 2.1$, hệ số giật $G_f = 0.86$. Áp lực hút cục bộ mép mái vùng F là $-2.23\text{ kN/m}^2$, tính toán lên tới $-4.68\text{ kN/m}^2$.
* **Nghi vấn về kiểm tra độ võng (SLS):** Thuyết minh đưa ra độ võng đỉnh kèo $f_v = 85.0\text{ mm} \le [f_v] = 93.0\text{ mm}$ ($\eta = 91.4\%$). Cần làm rõ giá trị này lấy từ tổ hợp nào. Nếu là SLS với $\gamma_f = 1.0$ mà đã võng $85\text{ mm}$ thì mái rất dễ bị võng đọng nước.
* **Tải Solar Rooftop:** Khai báo $0.12\text{ kN/m}^2$ ($\gamma_f = 1.1 \rightarrow 0.13\text{ kN/m}^2$), tương đương $12\text{ kg/m}^2$ là mức tối thiểu, chưa tính khung ray nhôm và phụ kiện.
* **BỎ SÓT TẢI TRỌNG GIÀN TREO $+6.000$:** Bản vẽ KC-13 có bố trí hệ giàn treo thép hộp $\square\text{-50}\times 100\times 1.5$ treo vào xà gồ/kèo mái toàn xưởng, nhưng trong mô hình ETABS khung K1 hoàn toàn không gán tải trọng của giàn này!

### 2.2. Xung Đột Hệ Lưới Trục: Kiến Trúc $\longleftrightarrow$ Kết Cấu
* **Kiến trúc (KT-01, 04, 05, 06):** Chia lưới trục ngang thành **7 trục: Y1, Y2, Y3, Y4, Y5, Y6, Y7** với khoảng cách đều nhau **$7.750\text{ mm}$** ($6 \times 7.750 = 46.500\text{ mm}$). Cột giữa xưởng nằm tại **Trục Y4**.
* **Kết cấu (KC-01 Mặt bằng móng):** Chỉ có **3 trục: Y1, Y2, Y3** với 2 nhịp $23.250\text{ mm} + 23.250\text{ mm}$. Cột giữa xưởng nằm tại **Trục Y2**!
* **Mâu thuẫn nội bộ Kết cấu:** Bản vẽ Móng (KC-01) ghi Y1, Y2, Y3; nhưng bản vẽ Đà kiềng (KC-04) và Giàn treo (KC-13) lại vẽ các đường gióng $6 \times 7.750\text{ mm}$ giống Kiến trúc nhưng không đánh số trục $\rightarrow$ Rủi ro định vị trắc đạc móng và bu lông neo ngoài hiện trường cực kỳ cao!

### 2.3. Mâu Thuẫn Tiết Diện Cấu Kiện: Bản Vẽ $\longleftrightarrow$ Thuyết Minh
* **Kèo giữa FR2:** Bản vẽ KC-07 ghi tiết diện $I\text{-400}\times 210 \times \mathbf{5\times 6}$ (bụng $5\text{ mm}$, cánh $6\text{ mm}$). Trong khi Thuyết minh (trang 22, 39) lại kiểm tra tiết diện $I\text{-400}\times 210 \times \mathbf{6\times 10}$ (bụng $6\text{ mm}$, cánh $10\text{ mm}$). Sai lệch làm giảm $W_x$ hơn $38\%$.
* **Độ mảnh bản bụng & Sườn tăng cứng:** Thuyết minh (trang 27) chỉ ra độ mảnh quy ước bản bụng cột C1 $\bar{\lambda}_w = 5.57 > [\bar{\lambda}_{uw}] = 2.3$ (Mục 9.4.4 TCVN 5575:2024), kết luận bắt buộc phải gia cường sườn tăng cứng. Nhưng trên bản vẽ KC-07, KC-08 hoàn toàn không thể hiện bước sườn tăng cứng ngang trên thân cột C1 và kèo FR1-FR3.
* **Xà gồ mái:** Bản vẽ bố trí 4 loại xà gồ ($Z-200\times 2.3, 2.0, 1.5$ và $C-200\times 1.5$), nhưng Thuyết minh chỉ tính 1 loại $Z-200\times 1.5$ tra bảng sơ sài.

### 2.4. Bất Hợp Lý Về Cơ Học Móng Nông
* **Nghịch lý lực dọc:** Móng cột biên M1 (diện truyền tải $95.3\text{ m}^2$) có $N_{0,tt} = \mathbf{15.8\text{ T}}$. Móng cột giữa M2 (diện truyền tải $190.65\text{ m}^2$, gấp đôi biên) lại có $N_{0,tt} = \mathbf{10.0\text{ T}}$!
* **Tự giả định địa chất:** TVTK tự giả định $R_{tc} = 18\text{ T/m}^2$ ($180\text{ kPa}$) mà không tính toán hiệu chỉnh từ chỉ tiêu cơ lý hay SPT theo TCVN 9362:2012. Chạy tính toán tất định theo $d = 1.5\text{ m} < 2.0\text{ m}$ thì $R$ hiệu chỉnh chỉ còn $163.0\text{ kPa}$. Thuyết minh móng M2, M3, M4 còn bị lỗi đánh máy ghi $R_{tc} = 18\text{ T/cm}^2$.
* **Bỏ qua kiểm tra nhổ móng:** Chưa có tổ hợp kiểm tra chống nhổ/chống lật móng dưới tác dụng của gió hút cực đại Vùng II.

### 2.5. Các Hạng Mục Bị Bỏ Quên Trong Thuyết Minh (Incompleteness)
1. **Khung thép Nhà để xe (DV5 - 408m²):** Bản vẽ có cột thép $H250\times 164$, kèo $H400\times 164$, liên kết 8M20. Nhưng Thuyết minh chỉ tính móng và đà kiềng; phần xà gồ báo lỗi bookmark; khung thép chính bị bỏ trống 100%!
2. **Kiểm toán nứt Bể PCCC 300m³:** Thuyết minh hoàn toàn không kiểm toán bề rộng khe nứt $a_{crc} \le 0.2\text{ mm}$ theo TCVN 5574:2018 (SLS), không tính tải trọng xe chữa cháy nắp bể.
3. **Nhà bơm PCCC (HT7 - 30m²):** Khung thép $\square\text{-60}\times 120\times 3$ đặt trên nắp bể ngầm hoàn toàn không được tính toán.
4. **Nền nhà xưởng:** Bản vẽ thể hiện bê tông dày $120 \sim 200\text{ mm}$, thép $\Phi 8$, nhưng không có thuyết minh tính toán chịu tải trọng xe nâng hàng.
5. **Chi tiết liên kết:** Không có bất kỳ bảng tính nào về bu lông neo chân cột (4M24), bu lông liên kết nách kèo (10M24/14M24), đường hàn hay bản mã.

---

## 3. CÁC NỘI DUNG NHỜ CLAUDE RÀ SOÁT BỔ SUNG ("ĐIỂM MÙ" CÓ THỂ BỎ SÓT)

Nhờ Claude kiểm tra và cho ý kiến sâu về các khía cạnh kỹ thuật sau:

1. **Hệ giằng không gian & Hệ giằng xà gồ (Sag rods / Flange stays / Bracing):**
   * Bản vẽ KC-06 thể hiện hệ cáp giằng mái $\Phi 14$ và thanh chống dọc. TVTK đã kiểm tra khả năng ổn định ngoài mặt phẳng của cánh dưới kèo khi chịu gió hút (cánh dưới chịu nén) chưa? Có bố trí thanh chống cánh (flange stay / ty giằng xà gồ vào cánh dưới) không?
   * Khoảng cách giằng cột và giằng mái đã đủ để truyền tải trọng gió đầu hồi theo TCVN 5575:2024 chưa?
2. **Khung đầu hồi K2 và Tải trọng gió đầu hồi:**
   * Khung đầu hồi gồm các cột C3, C4 ($I\text{-300}\times 184\times 5\times 5$) bước $7.75\text{ m}$. Cột đầu hồi chịu tải trọng gió trực diện tác dụng vào vách đầu hồi truyền lên mái như thế nào? Thuyết minh có tính toán cột đầu hồi C3, C4 chưa hay chỉ tính khung giữa K1?
3. **Chi tiết Mái đón Canopy (KC-11):**
   * Canopy vươn công son bao nhiêu mét? Bản vẽ KC-11 có thể hiện chi tiết liên kết bu lông và thanh treo canopy không? Gió bốc tác dụng lên mái đón đã được tính toán chưa?
4. **Yêu cầu PCCC & Sơn chống cháy theo QCVN 06:2022/BXD:**
   * Nhà xưởng sản xuất khuôn giày (ngành giày/nhựa/cao su) thuộc bậc chịu lửa mấy?
   * Các cấu kiện cột C1, kèo FR1-FR3 có bị yêu cầu bậc chịu lửa R30, R45 hay R60 không? Nếu TVTK không tính giải pháp bọc bảo vệ/sơn chống cháy thì hồ sơ có đủ điều kiện thẩm duyệt PCCC hay không?
5. **Tải trọng Động đất (TCVN 9386:2025):**
   * Khu vực TX. Chơn Thành, Tỉnh Bình Phước có gia tốc nền $a_g$ bao nhiêu? Có thuộc trường hợp được miễn trừ tính toán động đất cho kết cấu thép nhẹ 1 tầng không?
6. **Móng tường bao che (M5 $1.0\times 1.0\text{ m}$) & Đà kiềng:**
   * Các móng M5 đặt xen kẽ giữa móng chính M1-M4. Sự chênh lệch lún giữa móng cột chịu tải lớn ($1.7\times 2.0\text{ m}$) và móng tường ($1.0\times 1.0\text{ m}$) có gây nứt tường gạch xây cao $2.5\text{ m}$ hay nứt đà kiềng không?

---

## 4. HÀNH ĐỘNG TIẾP THEO

* **Claude phản hồi:** Vui lòng đưa ra các nhận xét phản biện, bổ sung thêm các điểm hở trong hồ sơ mà Gemini chưa nêu, và đề xuất phân loại các vấn đề theo mức độ ưu tiên: **Critical (Chặn thi công/pháp lý) / Major (Rủi ro an toàn/kinh tế) / Minor (Lỗi hoàn thiện bản vẽ)**.
* **Gemini sẽ tổng hợp:** Tích hợp toàn bộ phản hồi của Claude vào **Báo Cáo Thẩm Tra Kỹ Thuật Đợt 1 (.DOCX)** và bộ **Danh Mục RFI / NCR** để trình duyệt Chủ đầu tư Tân Hỷ.
