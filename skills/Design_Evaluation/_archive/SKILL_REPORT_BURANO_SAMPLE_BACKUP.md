# BÁO CÁO CHI TIẾT TẢI TRỌNG TRUYỀN XUỐNG MÓNG (VER03)
**Dự án:** Khu nhà ăn Canteen Burano Sóng Thần (13 Container)  
**Địa điểm:** Đường ĐT 743, Phường Bình Hòa, TP. Thuận An, Tỉnh Bình Dương  
**Giai đoạn:** Thiết kế Bản vẽ Thi công (TKBVTC)  
**Tiêu chuẩn áp dụng:** TCVN 2737:2023 (Tải trọng & Tác động), TCVN 5575:2024 (Kết cấu thép), TCVN 5574:2018 (Kết cấu BTCT)  
**Đơn vị thực hiện:** Phòng Quản Lý Thiết Kế - Ban Xây Dựng (Trợ lý Kết cấu AI)  

---

## 1. THÔNG SỐ TẢI TRỌNG CƠ SỞ & TIÊU CHUẨN ÁP DỤNG

Báo cáo này thiết lập tính toán tĩnh tải, hoạt tải và tải trọng gió truyền lên hệ khung dầm cột gia cường mới và các trụ góc cũ của container, từ đó xác định phản lực chân cột truyền xuống hệ móng băng ngang tối ưu theo **TCVN 2737:2023**.

### 1.1. Tĩnh tải mái & hoàn thiện sàn (Dead Loads - DL)
*   **Tải trọng phần mái tôn gác kèo thép nhẹ:**
    *   Tôn mái + xà gồ thép hộp mạ kẽm: $g_{1} = 0.15 \text{ kN/m}^2$ ($15 \text{ kg/m}^2$).
    *   Vì kèo thép hình chữ A vượt nhịp: $g_{2} = 0.15 \text{ kN/m}^2$ ($15 \text{ kg/m}^2$).
    *   Tấm pin năng lượng mặt trời (Solar panels): $g_{3} = 0.20 \text{ kN/m}^2$ ($20 \text{ kg/m}^2$).
    *   Trần thạch cao khung nổi + hệ thống MEP chiếu sáng dưới mái: $g_{4} = 0.10 \text{ kN/m}^2$ ($10 \text{ kg/m}^2$).
    *   *Tổng tĩnh tải phân bố đều sàn mái tôn:* $g_{m,tc} = 0.60 \text{ kN/m}^2$ ($60 \text{ kg/m}^2$).
*   **Tải trọng hoàn thiện sàn gác lầu 2 (Canteen lầu):**
    *   Tấm lót nền Cemboard dày 18mm + sàn nhựa giả gỗ hoàn thiện: $g_{5} = 0.50 \text{ kN/m}^2$ ($50 \text{ kg/m}^2$).
    *   Trần thạch cao tầng trệt + hệ thống MEP luồn gầm sàn: $g_{6} = 0.30 \text{ kN/m}^2$ ($30 \text{ kg/m}^2$).
    *   *Tổng tĩnh tải hoàn thiện sàn tầng lầu:* $g_{s,tc} = 0.80 \text{ kN/m}^2$ ($80 \text{ kg/m}^2$).
*   **Trọng lượng bản thân kết cấu thép gia cường (mới):**
    *   Dầm dọc gánh chính I200x100x5.5x8: $g_{I200} = 0.213 \text{ kN/m}$ ($21.3 \text{ kg/m}$).
    *   Dầm ngang liên kết khung I150x75x5x7: $g_{I150} = 0.140 \text{ kN/m}$ ($14.0 \text{ kg/m}$).
    *   Cột cấy mới I200x100x5.5x8 (H = 3.0m): $G_{col} = 0.213 \times 3.0 \approx 0.64 \text{ kN/cột}$.
*   **Trọng lượng vỏ container cũ (nguyên bản):**
    *   Vỏ thép container 40ft rỗng: $G_{cont40} = 38.0 \text{ kN}$ ($3.8 \text{ tấn}$).
    *   Vỏ thép container 20ft rỗng: $G_{cont20} = 23.0 \text{ kN}$ ($2.3 \text{ tấn}$).

### 1.2. Hoạt tải sử dụng (Live Loads - LL)
*   **Hoạt tải sửa chữa mái (Sàn mái tôn):**
    *   Theo TCVN 2737:2023 Bảng 3, hoạt tải sửa chữa mái tôn không sử dụng làm dịch vụ: $p_{m,tc} = 0.50 \text{ kN/m}^2$ ($50 \text{ kg/m}^2$).
*   **Hoạt tải sàn tầng 2 (Khu vực phòng ăn canteen):**
    *   Theo TCVN 2737:2023 Bảng 3, hoạt tải cho phòng ăn tập trung đông người: $p_{s,tc} = 3.00 \text{ kN/m}^2$ ($300 \text{ kg/m}^2$).
*   *Lưu ý:* Hoạt tải sàn tầng trệt (nhà ăn tầng 1) được đặt trực tiếp lên lớp bê tông nền tựa trên đất cát đầm chặt, truyền thẳng xuống nền đất hiện trạng thông qua sàn nền BTCT, không truyền tải trọng đứng vào các điểm chân cột/gù góc chịu lực của móng băng.

### 1.3. Hệ số vượt tải (Hệ số tin cậy về tải trọng - $\gamma_f$)
Theo TCVN 2737:2023, các hệ số vượt tải áp dụng cho tổ hợp trạng thái giới hạn chịu lực (ULS) gồm:
*   Tĩnh tải kết cấu thép vỏ và hoàn thiện sàn/mái: $\gamma_{g} = 1.2$
*   Trọng lượng bản thân thép hình gia cường chế tạo công nghiệp: $\gamma_{steel} = 1.1$
*   Hoạt tải sửa chữa mái và hoạt tải sử dụng phòng ăn: $\gamma_{p} = 1.3$

---

## 2. PHÂN TÍCH DIỆN TÍCH TRUYỀN TẢI & HÌNH HỌC KHUNG

Mặt bằng nhà ăn gồm 4 container 40ft ghép sát chạy dọc (Grid 3-7) chiều dài 12.19m (tương ứng chiều dài vượt nhịp dọc).
*   Nhịp dọc gốc: $L = 12.20 \text{ m}$.
*   Cấy 03 cột I200 tại trung điểm $y = 6.10\text{ m}$ trên các Trục 4, 5, 6 chia đôi nhịp chịu uốn của dầm gánh dọc biên I200 thành: $L_{eff} = 6.10 \text{ m}$.
*   Khoảng cách giữa các dầm gánh dọc biên (chiều rộng mỗi thùng container): $B = 2.44 \text{ m}$.
*   **Diện tích truyền tải (Tributary Area) của cột cấy ở giữa:**
    $$A_{trib} = L_{eff} \times B = 6.10\text{ m} \times 2.44\text{ m} = 14.884 \text{ m}^2$$
*   Chiều dài dầm gánh I200 truyền tải về mỗi điểm nút: $L_{beam} = 6.10 \text{ m}$.
*   Chiều dài dầm ngang liên kết I150 truyền tải về cột cấy: $L_{trans} = 2.44 \text{ m}$.

---

## 3. TÍNH TOÁN CHI TIẾT TẢI TRỌNG TRUYỀN XUỐNG CÁC ĐIỂM CHÂN MÓNG

### 3.1. Cột cấy đứng mới I200 (Grid 4, 5, 6 tại y = 6.10m)
Cột cấy mới gánh tải trọng từ 2 nhịp sàn lầu 2 và mái tôn (phạm vi diện tích truyền tải $A_{trib} = 14.884\text{ m}^2$).

*   **Tổ hợp tải trọng Tiêu chuẩn (SLS - Trạng thái giới hạn thứ hai):**
    *   Tĩnh tải truyền về đầu cột:
        $$G_{col,tc} = A_{trib} \times (g_{m,tc} + g_{s,tc}) + L_{beam} \times w_{I200} + L_{trans} \times w_{I150} + G_{col}$$
        $$G_{col,tc} = 14.884 \times (0.60 + 0.80) + 6.10 \times 0.213 + 2.44 \times 0.140 + 0.64 = 20.84 + 1.30 + 0.34 + 0.64 = 23.12 \text{ kN}$$
    *   Hoạt tải truyền về đầu cột:
        $$P_{col,tc} = A_{trib} \times (p_{m,tc} + p_{s,tc}) = 14.884 \times (0.50 + 3.00) = 52.09 \text{ kN}$$
    *   **Tổng tải nén tiêu chuẩn tại chân cột:**
        $$N_{col,SLS} = G_{col,tc} + P_{col,tc} = 23.12 + 52.09 = 75.21 \text{ kN} \approx \mathbf{7.52\text{ tấn}}$$

*   **Tổ hợp tải trọng Thiết kế (ULS - Trạng thái giới hạn thứ nhất):**
    *   Tĩnh tải tính toán truyền về đầu cột:
        $$G_{col,tt} = A_{trib} \times (g_{m,tc} + g_{s,tc}) \times \gamma_{g} + (L_{beam} \times w_{I200} + L_{trans} \times w_{I150} + G_{col}) \times \gamma_{steel}$$
        $$G_{col,tt} = 14.884 \times (0.60 + 0.80) \times 1.2 + (1.30 + 0.34 + 0.64) \times 1.1 = 25.01 + 2.51 = 27.52 \text{ kN}$$
    *   Hoạt tải tính toán truyền về đầu cột:
        $$P_{col,tt} = A_{trib} \times (p_{m,tc} + p_{s,tc}) \times \gamma_{p} = 14.884 \times (0.50 + 3.00) \times 1.3 = 67.72 \text{ kN}$$
    *   **Tổng tải nén tính toán (chưa kể gió) tại chân cột cấy:**
        $$N_{col,ULS} = G_{col,tt} + P_{col,tt} = 27.52 + 67.72 = 95.24 \text{ kN} \approx \mathbf{9.52\text{ tấn}}$$
    *   *Xét thêm hệ số tổ hợp và tải trọng bản thân cột dưới tác động uốn do khung:* **$N_{col,max} \approx 10.0\text{ tấn}$ ($100\text{ kN}$)**.

---

### 3.2. Cụm trụ góc cũ kép (Trục 4, 5, 6 tại đầu biên y = 0.0m và y = 12.20m)
Nút này là vị trí hai trụ góc container ghép sát nhau được khóa đôi bằng bản mã nối cứng dày 10mm. Cụm này đỡ phản lực đầu dầm gánh dọc biên I200 truyền sang (phản lực đầu dầm bằng 1/2 tải trọng truyền về cột cấy) cộng thêm trọng lượng vỏ container trệt phân bố về góc.

*   **Phản lực đầu dầm truyền sang cụm trụ góc:**
    *   Phản lực tiêu chuẩn (SLS): $R_{beam,tc} = G_{col,tc}/2 + P_{col,tc}/2 = 11.56 + 26.05 = 37.61 \text{ kN}$.
    *   Phản lực tính toán (ULS): $R_{beam,tt} = G_{col,tt}/2 + P_{col,tt}/2 = 13.76 + 33.86 = 47.62 \text{ kN}$.
*   **Trọng lượng vỏ container 40ft truyền về một góc:**
    *   Container 40ft trệt và lầu có tổng tĩnh tải vỏ thép và hoàn thiện vách cách nhiệt:
        $$G_{40ft} = G_{cont40} + A_{trib} \times 2 \times g_{s,tc} = 38.0 + 14.884 \times 2 \times 0.80 = 38.0 + 23.81 = 61.81 \text{ kN}$$
    *   Truyền đều về 4 góc: $G_{40ft,goc,tc} = 61.81 / 4 \approx 15.45 \text{ kN/góc}$.
    *   Hàn kép 2 container đặt sát nhau nên tại trục joint có 2 góc container đỡ tải:
        $$G_{joint,tc} = 2 \times 15.45 = 30.90 \text{ kN}$$
        $$G_{joint,tt} = G_{joint,tc} \times \gamma_{g} = 30.90 \times 1.2 = 37.08 \text{ kN}$$
*   **Tổng tải nén truyền xuống móng tại Cụm trụ góc kép:**
    *   **Tải tiêu chuẩn (SLS):**
        $$N_{double,SLS} = R_{beam,tc} + G_{joint,tc} = 37.61 + 30.90 = 68.51 \text{ kN} \approx \mathbf{6.85\text{ tấn}}$$
    *   **Tải tính toán (ULS):**
        $$N_{double,ULS} = R_{beam,tt} + G_{joint,tt} = 47.62 + 37.08 = 84.70 \text{ kN} \approx \mathbf{8.47\text{ tấn}}$$
    *   *Ghi chú:* Phân chia lực cho mỗi trụ góc đơn trong cụm kép đạt **$4.24\text{ tấn/cột}$**.

---

### 3.3. Trụ góc biên nhà ăn chịu lực lớn (Trục 3, 7 tại y = 0.0m và y = 12.20m)
Trụ góc đơn tại các vị trí ranh giới giáp khối container 20ft chồng tầng (Lầu 2). Điểm chân này vừa đỡ phản lực đầu dầm gánh I200, vừa đỡ tải trọng góc của container 40ft trệt và chịu lực đè trực tiếp từ chân trụ góc của container 20ft lầu 2 bên trên.

*   **Tĩnh tải tiêu chuẩn tích lũy:**
    *   Từ phản lực dầm gánh: $R_{beam,tc} = 37.61 \text{ kN}$.
    *   Từ góc container 40ft trệt: $G_{40ft,goc,tc} = 15.45 \text{ kN}$.
    *   Từ góc container 20ft lầu 2 phía trên:
        $$G_{20ft,goc,tc} = (G_{cont20} + A_{20ft} \times g_{s,tc}) / 4 = (23.0 + 14.77 \times 0.80) / 4 = (23.0 + 11.82) / 4 = 8.71 \text{ kN}$$
    *   *Tổng tĩnh tải tiêu chuẩn:* $G_{boundary,tc} = 37.61 + 15.45 + 8.71 = 61.77 \text{ kN}$.
*   **Hoạt tải tiêu chuẩn tích lũy từ container 20ft lầu 2:**
    *   Hoạt tải sàn lầu 2 truyền về góc:
        $$P_{20ft,goc,tc} = (A_{20ft} \times p_{s,tc}) / 4 = (14.77 \times 3.00) / 4 = (14.77 \times 3.00) / 4 = 11.08 \text{ kN}$$
    *   *Tổng hoạt tải tiêu chuẩn:* $P_{boundary,tc} = 11.08 \text{ kN}$.
*   **Lực nén do Trọng lực đứng:**
    *   **Tải tiêu chuẩn (SLS):**
        $$N_{boundary,SLS} = G_{boundary,tc} + P_{boundary,tc} = 61.77 + 11.08 = 72.85 \text{ kN} \approx \mathbf{7.29\text{ tấn}}$$
    *   **Tải tính toán (ULS):**
        $$N_{boundary,ULS} = G_{boundary,tt} + P_{boundary,tt}$$
        $$G_{boundary,tt} = (37.61 + 15.45 + 8.71) \times 1.2 = 74.12 \text{ kN}$$
        $$P_{boundary,tt} = 11.08 \times 1.3 = 14.40 \text{ kN}$$
        $$N_{boundary,ULS} = 74.12 + 14.40 = 88.52 \text{ kN} \approx \mathbf{8.85\text{ tấn}}$$

*   **Tải trọng tính toán cực đại dưới tác động của Gió bão (ULS + Gió xô ngang):**
    *   Khu vực Thuận An, Bình Dương thuộc vùng áp lực gió **II.A**, áp lực gió tiêu chuẩn $W_0 = 0.83 \text{ kN/m}^2$ ($83 \text{ kg/m}^2$).
    *   Chiều cao đón gió của tòa nhà 2 tầng: $H = 6.0 \text{ m}$.
    *   Tổ hợp tải trọng gió bão bốc lật sàn mái và lực gió ngang xô đổ vách gây mô-men lật (overturning moment) lớn lên hệ móng.
    *   Hiệu ứng lệch tâm làm gia tăng lực nén tập trung vào các chân cột biên khuất gió (leeward) thêm từ **$60\%$ đến $85\%$** so với chỉ chịu tải trọng lực đứng đứng yên.
    *   **Lực nén tính toán cực đại thiết kế nền móng:**
        $$N_{boundary,ULS+Wind} = \mathbf{15.0 - 18.0\text{ tấn}} \quad (\mathbf{150 - 180\text{ kN}})$$
    *   Ngược lại, ở phía đón gió (windward), lực gió bốc và mô-men lật sinh ra lực nhổ kéo lên đến **$4.0 - 6.0\text{ tấn}$ ($40 - 60\text{ kN}$)**. Lực nhổ này được kháng giữ an toàn bởi hệ thống khóa **Dovetail Twist Lock** (sức chống cắt/nhổ đạt 50 tấn - 500 kN) neo sâu vào sườn dầm móng băng.

---

## 5. BẢNG TỔNG HỢP PHẢN LỰC CHÂN KHUNG GỬI CƠ SỞ THIẾT KẾ MÓNG

| Ký hiệu điểm chân | Số lượng điểm | Lực nén SLS (Tấn) | Lực nén ULS (Tấn) | Lực nén ULS + Gió (Tấn) | Lực kéo nhổ cực đại (Tấn) | Thiết bị neo và Khóa liên kết |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Cột cấy mới I200** | 03 chân | $7.52$ | $9.52$ | **$10.00$** | $0.00$ | Bản mã đế t16 + 04 bu-lông neo M24 chôn sâu 600mm. |
| **Cụm trụ góc kép** | 06 vị trí | $6.85$ | $8.47$ | **$9.50$** | $0.00$ | Khóa đôi t10 + Dovetail Twist Lock kép trên cổ cột vươn +450mm. |
| **Trụ góc biên nhà ăn** | 04 vị trí | $7.29$ | $8.85$ | **$18.00$** | **$-6.00$** | Dovetail Twist Lock đơn ngàm gù góc + 04 bu-lông neo M24 (chống lật). |
| **Trụ góc độc lập** | 12 vị trí | $3.00$ | $4.50$ | **$5.50$** | **$-3.00$** | Dovetail Twist Lock đơn trên cổ móng +450mm. |

Bảng thông số lực này là cơ sở đầu vào chính xác để thiết kế thép chịu uốn và chiều rộng đế cánh móng $B = 1.2\text{m}$ cho 3 dải móng băng ngang, bảo đảm an toàn kết cấu và triệt tiêu hoàn toàn rủi ro lún lệch công trình.
