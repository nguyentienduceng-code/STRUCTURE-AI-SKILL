# Hướng dẫn Mô hình Hệ Shoring (Hố đào sâu) trong ETABS 3D

Tài liệu này cung cấp tiêu chuẩn thao tác gán liên kết (Releases & Restraints) và tải trọng khi mô phỏng hệ giằng chống hố đào từ kết quả Plaxis sang ETABS.

## 1. Bản chất sự khác biệt giữa Plaxis và ETABS
- **Plaxis (Địa kỹ thuật):** Mô phỏng tương tác đất - nền. Kết quả lực dọc trong thanh chống (Strut/Anchor) là **Nội lực (Result)**.
- **ETABS (Kết cấu):** Mô phỏng ứng xử của hệ khung thép không gian. Phải dùng tải trọng đất đè lên khung để sinh ra nội lực. KHÔNG lấy nội lực của Plaxis gán làm tải trọng trong ETABS.

## 2. Quy đổi tải trọng (MODULE 17)
Tải trọng gán vào hệ Dầm bo (Waling Beam) trong ETABS là **Tải phân bố đều $q$ (kN/m)**.
Công thức: `q = F_anchor / L_spacing`
Trong đó:
- `F_anchor`: Lực dọc thanh chống đọc từ Plaxis (kN).
- `L_spacing`: Khoảng cách các thanh chống (hoặc nhịp neo) khai báo trong Plaxis (m).

**Tổ hợp tải trọng trong ETABS:**
Áp lực đất từ Plaxis thường là tải tiêu chuẩn (Service Load). Khi thiết kế cấu kiện thép theo LRFD (ví dụ TCVN 5575 hoặc AISC), phải nhân hệ số vượt tải:
`Combo = 1.2 DL + 1.6 ALD` (Active Lateral Earth Pressure).

## 3. Khai báo Liên kết Thanh (Frame Releases)

**A. Thanh chống (Strut / Corner Brace):**
- **Bản chất:** Chịu nén dọc trục, không truyền momen uốn để thiên về an toàn.
- **Thao tác ETABS:** Chọn các phần tử thanh chống $\rightarrow$ `Assign > Frame > Releases/Partial Fixity`.
- **Thiết lập:** Tick giải phóng (Release) **Moment 22 (Minor)** và **Moment 33 (Major)** tại cả 2 đầu (Start và End).

**B. Dầm bo (Waling Beam):**
- **Bản chất:** Là vành đai cứng liên tục truyền lực uốn và cắt.
- **Thao tác ETABS:** **TUYỆT ĐỐI KHÔNG RELEASE** tại các điểm nối dọc dầm bo hoặc tại góc hố đào. Mặc định là ngàm (Continuous).

## 4. Khai báo Gối tựa (Joint Restraints) - Chống trôi mô hình

Để tránh lỗi *Ill-conditioned* hoặc *Instability* do khung lơ lửng, cần gán các gối tựa sau:

**A. Chống rơi phương đứng (UZ):**
- **Thao tác:** Chọn tất cả các nút dọc theo dầm bo $\rightarrow$ `Assign > Joint > Restraints` $\rightarrow$ Khóa **UZ**.
- **Ý nghĩa:** Mô phỏng các "con bọ" (brackets) đỡ hệ khung trên tường vây/cừ.

**B. Chống trôi phương ngang (UX, UY):**
- **Thao tác:** Chọn tối thiểu **2 điểm nút ở góc chéo nhau** của hố đào $\rightarrow$ Khóa **UX, UY** (Kết hợp với UZ thành gối Pinned).
- **Ý nghĩa:** Giữ cho hệ khung nằm yên khi chịu tải trọng ngang (do tải 4 mặt không cân bằng tuyệt đối).
- **LƯU Ý CỰC KỲ QUAN TRỌNG:** KHÔNG khóa UX, UY tại các nút giao giữa Dầm bo và Thanh chống. Nếu khóa, dầm bo sẽ không thể biến dạng đẩy vào thanh chống, dẫn đến nội lực thanh chống bằng 0. Chỉ khóa UX, UY tại các góc hố đào.

## 5. Kiểm tra kết quả ETABS
Sau khi chạy giải tích, so sánh **Lực dọc (Axial Force)** của thanh chống trong ETABS với con số $F_{anchor}$ ban đầu của Plaxis. Nếu chênh lệch < 10%, mô hình ETABS đã phản ánh đúng ứng xử đất nền.
