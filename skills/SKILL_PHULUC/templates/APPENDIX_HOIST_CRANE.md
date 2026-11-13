# PHỤ LỤC BIỆN PHÁP THI CÔNG VẬN THĂNG & CẨU THÁP

> BIỂU MẪU CHƯA ĐIỀN: Không dùng làm kết luận nghiệm thu. Phải biên dịch dữ liệu dự án trước khi phát hành.
## TÍNH TOÁN KIỂM TRA KHẢ NĂNG CHỊU LỰC, ỔN ĐỊNH VÀ NỀN MÓNG

---

## A. THÔNG TIN THIẾT BỊ & ĐIỀU KIỆN HIỆN TRƯỜNG

| Thông số | Ký hiệu | Giá trị thiết kế | Đơn vị | Ghi chú kỹ thuật |
|:---|:---:|:---:|:---:|:---|
| **Chủng loại thiết bị** | — | Vận thăng lồng đơn/đôi hoặc Cẩu tháp | — | Theo Catalogue xuất xưởng |
| **Số đốt tiêu chuẩn** | $n$ | ___ | đốt | Chiều dài mỗi đốt $L_{sec} = 1.508\text{ m}$ |
| **Chiều cao tháp tối đa** | $H$ | ___ | m | Tính từ đỉnh chân đế đến đỉnh tháp |
| **Số tầng gông neo** | $n_{tie}$ | ___ | tầng | Khoảng cách gông $6.0 - 9.0\text{ m}$ |
| **Vươn công xôn đỉnh** | $L_{cant}$ | ___ | m | Vượt trên tầng gông trên cùng |
| **Tải trọng nâng lồng** | $Q$ | ___ | kg/lồng | Tải trọng danh định của thiết bị |
| **Kích thước bản đài móng** | $L \times B \times H$ | ___ $\times$ ___ $\times$ ___ | m | Bê tông cốt thép B25–B30 |

---

## B. ĐẶC TRƯNG CƠ LÝ VẬT LIỆU & NỀN ĐẤT

### B.1 Bê tông và Cốt thép Đài móng (TCVN 5574:2018)
- Cấp độ bền bê tông đài: **B30** ($R_b = 17.0\text{ MPa}$, $R_{bt} = 1.15\text{ MPa}$, $E_b = 32.500\text{ MPa}$).
- Nhóm cốt thép chịu lực: **CB400-V** ($R_s = 350.0\text{ MPa}$, $R_{sc} = 350.0\text{ MPa}$).

### B.2 Kết cấu Thép và Bu lông Neo (TCVN 5575:2024)
- Ống tháp và thanh giằng: Thép **Q345B** ($f_y = 345\text{ MPa}$) hoặc **SS400** ($f_y = 235\text{ MPa}$).
- Bu lông neo gông: Bu lông cường độ cao cấp bền **8.8** hoặc bu lông cấy hóa chất Ramset/Hilti.

### B.3 Địa kỹ thuật & Đệm Đất Đầm Chặt K95 (TCVN 9362:2012 & TCVN 4447:2012)
- Độ chặt đầm lèn: $K \ge 0.95$.
- Dung trọng đất đắp: $\gamma_{II} = 18.5\text{ kN/m}^3$.
- Góc ma sát trong tính toán: $\varphi_{II} \ge 20^\circ$.
- Lực dính đơn vị tính toán: $c_{II} \ge 8.0\text{ kPa}$.
- Mô đun biến dạng: $E_0 \ge 15.0\text{ MPa}$.

---

## C. TẢI TRỌNG & TỔ HỢP TÍNH TOÁN

### C.1 Tải trọng Gió Bão theo TCVN 2737:2023
- Vùng áp lực gió: Vùng II ($W_0 = 95\text{ daN/m}^2$), Vùng III ($W_0 = 125\text{ daN/m}^2$).
- Áp lực gió giật $3\text{s}$ chu kỳ 10 năm cho trạng thái vận hành: $W_{3s,10} = W_0 \times \gamma_{f,10} \times k(z)$.
- Hệ số khí động khung tháp giàn hở:
$$\varphi_{solidity} = \frac{A_{net}}{A_{gross}}; \quad \eta_s = (1 - \varphi_{solidity})^2; \quad c_{x,net} = c_{f1} \cdot (1 + \eta_s)$$

### C.2 Tổ hợp Tải trọng Tính toán
1. **Tổ hợp 1 (TH1 - Vận hành ULS/SLS)**: Thiết bị nâng đầy tải + Gió vận hành cấp 6 ($v \le 12\text{ m/s}$).
2. **Tổ hợp 2 (TH2 - Bão cực hạn ULS/SLS)**: Thiết bị dừng ở chân + Bão thiết kế cực hạn chu kỳ 20–50 năm.

---

## D. NỘI LỰC FEM VÀ PHÂN PHỐI LỰC CHÂN ĐẾ

### D.1 Mô hình Dầm Liên tục 1D Euler-Bernoulli
Giải hệ dầm liên tục đa gối tựa (chân đế ngàm đàn hồi + các tầng gông neo) chịu tải trọng gió hình thang:
$$\mathbf{K}_{mast} \cdot \mathbf{u} = \mathbf{F}_{wind} \implies R_{gong, i}, \quad M_{0, base}, \quad V_{0, base}$$

### D.2 Phân phối Lực xuống 4 Chân Khung Đế Thép
Theo phương trình cân bằng mô men 2 phương có xét độ lệch tâm điểm đặt tải:
$$M_{x,frame} = M_x - N \cdot y_{shift}; \quad M_{y,frame} = M_y - N \cdot x_{shift}$$
$$P_{i} = \frac{N}{4} \pm \frac{M_{x,frame} \cdot y_i}{\sum y^2} \pm \frac{M_{y,frame} \cdot x_i}{\sum x^2}$$

---

## E. KIỂM TRA KHẢ NĂNG CHỊU LỰC & ĐÁNH GIÁ AN TOÀN

### E.1 Kiểm tra Ổn định Thanh Gông Neo (TCVN 5575:2024 Điều 7.1)
$$\lambda = \frac{L_{cr}}{i_{min}} \le [\lambda] = 150; \quad \bar{\lambda} = \frac{\lambda}{\pi \sqrt{E / f_y}}$$
$$N_{b,Rd} = \chi \cdot \frac{A \cdot f_y}{\gamma_{M1}}; \quad \eta_{buckling} = \frac{N_{Ed}}{N_{b,Rd}} \le 1.00$$

### E.2 Kiểm tra Bu lông Neo Gông vào Dầm Sàn (TCVN 5575:2024 & ETAG 001)
$$\left(\frac{N_{Ed}}{N_{Rd}}\right)^2 + \left(\frac{V_{Ed}}{V_{Rd}}\right)^2 \le 1.00$$

### E.3 Kiểm tra Khả năng Chịu tải Nền Đất Đầm Chặt K95 (TCVN 9362:2012 Điều 4.6.13)
$$R_{K95} = \frac{m_1 m_2}{k_{tc}} \cdot \left(A \cdot b \cdot \gamma + B \cdot h \cdot \gamma' + D \cdot c\right)$$
$$p_{tb} \le R_{K95}; \quad p_{max} \le 1.2 \cdot R_{K95}; \quad \eta_{soil} = \frac{p_{max}}{1.2 R_{K95}} \le 1.00$$

### E.4 Kiểm tra Bản Móng BTCT (Tấm Mindlin Q4 trên Nền Winkler)
- **Mô men uốn dải 1.0 m**: $\bar{M}_{Ed} \le M_{Rd} = R_s \cdot A_s \cdot (h_0 - 0.5 x)$.
- **Khả năng chọc thủng tổng thể và cục bộ 1 chân**: $F_{Ed} \le F_{b,ult} = \alpha \cdot R_{bt} \cdot u_m \cdot h_0$.
- **Bề rộng khe nứt SLS**: $a_{crc} \le [a_{crc}] = 0.30\text{ mm}$.

---

## F. BẢNG TỔNG HỢP SCORECARD ĐÁNH GIÁ AN TOÀN

| STT | Hạng mục kiểm tra | Giá trị tính toán | Giới hạn cho phép | Chỉ số $\eta$ | Kết luận |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | Ổn định thanh giằng gông | $N_{Ed} = \text{___ kN}$ | $N_{b,Rd} = \text{___ kN}$ | **___** | **CHƯA XÁC MINH** |
| 2 | Độ mảnh thanh gông | $\lambda = \text{___}$ | $[\lambda] = 150$ | **___** | **CHƯA XÁC MINH** |
| 3 | Bu lông neo dầm BTCT | $N_1 = \text{___ kN}$ | $N_{rec} = \text{___ kN}$ | **___** | **CHƯA XÁC MINH** |
| 4 | Áp lực nền đất K95 | $p_{max} = \text{___ kPa}$ | $1.2 R = \text{___ kPa}$ | **___** | **CHƯA XÁC MINH** |
| 5 | Áp lực đất yếu bên dưới | $p_{L1,max} = \text{___ kPa}$ | $1.2 R_{L1} = \text{___ kPa}$ | **___** | **CHƯA XÁC MINH** |
| 6 | Uốn bản đài BTCT (dải 1m) | $M_{Ed} = \text{___ kNm/m}$ | $M_{Rd} = \text{___ kNm/m}$ | **___** | **CHƯA XÁC MINH** |
| 7 | Chọc thủng bản đài móng | $F_{eq} = \text{___ kN}$ | $F_{ult} = \text{___ kN}$ | **___** | **CHƯA XÁC MINH** |
| 8 | Bề rộng khe nứt bản đài | $a_{crc} = \text{___ mm}$ | $[a_{crc}] = 0.30\text{ mm}$ | **___** | **CHƯA XÁC MINH** |

