# PHỤ LỤC BIỆN PHÁP THI CÔNG VÁN KHUÔN & HỆ GIÁO CHỐNG SHORING
## TÍNH TOÁN KIỂM TRA KHẢ NĂNG CHỊU LỰC, ĐỘ VÕNG VÀ ỔN ĐỊNH HỆ CHỐNG SÀN/DẦM/CỘT

---

## A. THÔNG TIN CHUNG & QUY MÔ HẠNG MỤC

| Thông số | Ký hiệu | Giá trị thiết kế | Đơn vị | Ghi chú kỹ thuật |
|:---|:---:|:---:|:---:|:---|
| **Vị trí sàn thi công** | — | Sàn Tầng ___ (+___ m) | — | Chiều cao thông thủy tầng $H = \text{___ m}$ |
| **Bề dày bản sàn bê tông** | $h_s$ | ___ | mm | Bê tông B25–B30 ($25.0\text{ kN/m}^3$) |
| **Kích thước dầm chính** | $b \times h$ | ___ $\times$ ___ | mm | Tiết diện dầm khung điển hình |
| **Loại ván khuôn mặt** | — | Ván ép phủ phim Birch/Keo chịu nước | mm | Bề dày $t = 12/15/18\text{ mm}$ |
| **Hệ sườn phụ (đỡ ván)** | — | Thép hộp kẽm $50 \times 50 \times 1.4\text{ mm}$ | — | Khoảng cách bước sườn $a = 250 - 350\text{ mm}$ |
| **Hệ dầm chính (đỡ sườn)** | — | Thép hộp kẽm $50 \times 100 \times 2.0\text{ mm}$ | — | Khoảng cách dầm chính $b = 900 - 1200\text{ mm}$ |
| **Hệ thống cây chống** | — | Giàn giáo Ringlock / Nêm Ø48.3×2.5 mm | — | Lưới cột chống $L_x \times L_y = 1.2 \times 1.2\text{ m}$ |

---

## B. ĐẶC TRƯNG CƠ LÝ VẬT LIỆU (TCVN 4453:1995 & TCVN 5575:2024)

### B.1 Ván Ép Phủ Phim (Plywood)
- Cường độ chịu uốn tính toán: $f_{b,ply} = 15.0 - 25.0\text{ MPa}$.
- Cường độ chịu cắt lăn: $f_{v,ply} = 1.2 - 1.8\text{ MPa}$.
- Mô đun đàn hồi uốn: $E_{ply} = 5.000 - 8.000\text{ MPa}$.
- Giới hạn độ võng cho phép: $[f] = L / 400$ (không vượt quá $3\text{ mm}$).

### B.2 Sườn Thép Hộp & Dầm Chính (Thép SS400 / Q235)
- Giới hạn chảy: $f_y = 235.0\text{ MPa}$; Cường độ chịu kéo/nén tính toán: $f = 210.0\text{ MPa}$.
- Cường độ chịu cắt tính toán: $f_v = 120.0\text{ MPa}$.
- Mô đun đàn hồi: $E_s = 210.000\text{ MPa}$.
- Giới hạn độ võng cho phép: $[f] = L / 400$.

### B.3 Cây Chống Thép Ringlock / Nêm (Ống Thép Ø48.3×2.5 mm)
- Diện tích mặt cắt: $A = 359.7\text{ mm}^2$.
- Bán kính quán tính: $i = 16.2\text{ mm}$.
- Sức chịu tải nén danh định đơn vị của 1 trụ giáo theo kiểm định: $P_{allow} = 25.0 - 35.0\text{ kN/cột}$.

---

## C. TẢI TRỌNG THI CÔNG TÁC DỤNG LÊN HỆ VÁN KHUÔN

Theo **TCVN 4453:1995** (hoặc BS EN 12812 / ACI 347R):
1. **Trọng lượng bản thân ván khuôn & sườn ($G_1$)**: $q_1 = 0.30 - 0.50\text{ kN/m}^2$ ($\gamma_f = 1.1$).
2. **Trọng lượng bê tông cốt thép mới đổ ($G_2$)**: $q_2 = 25.0 \times h_s\text{ kN/m}^2$ ($\gamma_f = 1.2$).
3. **Hoạt tải công nhân, thiết bị đi lại ($Q_1$)**: $p_1 = 2.50\text{ kN/m}^2$ khi tính bền, $1.50\text{ kN/m}^2$ khi tính võng ($\gamma_f = 1.3$).
4. **Tải trọng đầm rung và đổ bê tông ($Q_2$)**:
   - Đổ bằng bơm/máy đổ: $p_2 = 2.0 - 4.0\text{ kN/m}^2$ ($\gamma_f = 1.3$).

$$\text{Tổng tải trọng ULS tính bền: } q_{ULS} = 1.1 G_1 + 1.2 G_2 + 1.3 (Q_1 + Q_2)$$
$$\text{Tổng tải trọng SLS tính võng: } q_{SLS} = 1.0 G_1 + 1.0 G_2 + 1.0 Q_1$$

---

## D. TÍNH TOÁN KIỂM TRA TỪNG TẦNG CẤU KIỆN

### D.1 Kiểm tra Ván Mặt Phủ Phim (Nhịp liên tục qua các sườn phụ khoảng cách $a$)
- **Mô men uốn lớn nhất**:
$$M_{max} = 0.105 \cdot q_{ULS} \cdot a^2; \quad \sigma_b = \frac{M_{max}}{W_{ply}} \le f_{b,ply}$$
- **Ứng suất cắt lăn**:
$$V_{max} = 0.60 \cdot q_{ULS} \cdot a; \quad \tau = \frac{1.5 \cdot V_{max}}{b \cdot t} \le f_{v,ply}$$
- **Độ võng lớn nhất**:
$$f_{max} = \frac{0.677 \cdot q_{SLS} \cdot a^4}{100 \cdot E_{ply} \cdot I_{ply}} \le [f] = \frac{a}{400}$$

### D.2 Kiểm tra Sườn Phụ Thép Hộp (Nhịp liên tục qua các dầm chính khoảng cách $b$)
- Tải trọng phân bố trên 1 thanh sườn: $q_{suon} = q \cdot a$.
- **Mô men uốn**:
$$M_{suon} = 0.10 \cdot q_{suon,ULS} \cdot b^2; \quad \sigma = \frac{M_{suon}}{\gamma_c \cdot W_x} \le f$$
- **Độ võng sườn phụ**:
$$f_{suon} = \frac{0.677 \cdot q_{suon,SLS} \cdot b^4}{100 \cdot E \cdot I_x} \le [f] = \frac{b}{400}$$

### D.3 Kiểm tra Dầm Chính Thép Hộp (Gối tựa lên các đầu cây chống Ringlock khoảng cách $L_x$)
- Tải trọng tập trung hoặc phân bố truyền từ các sườn phụ: $q_{chinh} = q \cdot b$.
- **Mô men uốn & Ứng suất**:
$$M_{chinh} = 0.10 \cdot q_{chinh,ULS} \cdot L_x^2; \quad \sigma = \frac{M_{chinh}}{\gamma_c \cdot W_{chinh}} \le f$$
- **Độ võng dầm chính**:
$$f_{chinh} = \frac{0.677 \cdot q_{chinh,SLS} \cdot L_x^4}{100 \cdot E \cdot I_{chinh}} \le [f] = \frac{L_x}{400}$$

### D.4 Kiểm tra Khả năng Chịu tải & Ổn định Hệ Cây Chống Ringlock (TCVN 5575:2024)
- Lực nén lớn nhất truyền xuống 1 chân cột chống:
$$N_{cot} = q_{ULS} \cdot (L_x \cdot L_y)$$
- Chiều dài tính toán uốn nọc: $L_{cr} = \mu \cdot h_{tang\\_giang}$ (với $h_{tang\\_giang} = 1.0 - 1.5\text{ m}$ là bước giằng ngang).
$$\lambda = \frac{L_{cr}}{i_{min}} \le 150; \quad N_{b,Rd} = \chi \cdot A \cdot \frac{f_y}{\gamma_{M1}}$$
$$\eta_{shoring} = \frac{N_{cot}}{N_{b,Rd}} \le 1.00$$

---

## E. BẢNG TỔNG HỢP SCORECARD KIỂM TRA HỆ VÁN KHUÔN SÀN

| STT | Cấu kiện kiểm tra | Đại lượng | Giá trị tính toán | Giới hạn cho phép | Chỉ số $\eta$ | Kết luận |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | Ván mặt phủ phim | Ứng suất uốn $\sigma_b$ | ___ MPa | $f_b = 20.0\text{ MPa}$ | **___** | **ĐẠT** |
| 2 | Ván mặt phủ phim | Ứng suất cắt $\tau$ | ___ MPa | $f_v = 1.5\text{ MPa}$ | **___** | **ĐẠT** |
| 3 | Ván mặt phủ phim | Độ võng $f$ | ___ mm | $[f] = a/400$ | **___** | **ĐẠT** |
| 4 | Sườn phụ hộp kẽm | Ứng suất uốn $\sigma$ | ___ MPa | $f = 210.0\text{ MPa}$ | **___** | **ĐẠT** |
| 5 | Sườn phụ hộp kẽm | Độ võng $f$ | ___ mm | $[f] = b/400$ | **___** | **ĐẠT** |
| 6 | Dầm chính hộp kẽm | Ứng suất uốn $\sigma$ | ___ MPa | $f = 210.0\text{ MPa}$ | **___** | **ĐẠT** |
| 7 | Dầm chính hộp kẽm | Độ võng $f$ | ___ mm | $[f] = L_x/400$ | **___** | **ĐẠT** |
| 8 | Cột chống Ringlock | Lực nén $N_{cot}$ | ___ kN | $N_{b,Rd} = \text{___ kN}$ | **___** | **ĐẠT** |

