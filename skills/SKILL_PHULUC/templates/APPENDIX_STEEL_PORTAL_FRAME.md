# PHỤ LỤC KHUNG THÉP TIỀN CHẾ & LIÊN KẾT BU LÔNG
## TÍNH TOÁN THIẾT KẾ KHUNG ZAMIL, XÀ GỒ VÀ LIÊN KẾT NÁCH KHUNG THEO TCVN 5575:2024

---

## A. THÔNG TIN HÌNH HỌC & QUY MÔ CÔNG TRÌNH

| Thông số | Ký hiệu | Giá trị thiết kế | Đơn vị | Ghi chú kỹ thuật |
|:---|:---:|:---:|:---:|:---|
| **Nhịp khung nhà xưởng** | $L$ | ___ | m | Khoảng cách giữa 2 tim cột |
| **Bước khung điển hình** | $B$ | ___ | m | Khoảng cách giữa 2 trục khung ngang |
| **Chiều cao cột đến mép mái** | $H_{cot}$ | ___ | m | Cao độ chân cột đến đỉnh đầu cột |
| **Độ dốc mái tôn** | $i$ | ___ | % | Thường từ $10\% - 15\%$ |
| **Khoảng cách xà gồ mái** | $a_{xg}$ | ___ | m | Bước bố trí xà gồ ($1.2 - 1.5\text{ m}$) |
| **Loại xà gồ mái** | — | Xà gồ thép mạ kẽm C/Z | mm | Tiết diện C/Z $200 \times 65 \times 20 \times 2.0$ |
| **Vật liệu thép kết cấu** | — | Thép tấm / hình Q345B (kèo, cột) | — | $f_y = 345\text{ MPa}$, $f_u = 470\text{ MPa}$ |
| **Bu lông liên kết nách/nóc** | — | Bu lông cường độ cao cấp bền **8.8 / 10.9** | — | Đường kính M20 / M24 / M27 |

---

## B. ĐẶC TRƯNG CƠ LÝ VẬT LIỆU THEO TCVN 5575:2024

### B.1 Thép Kết cấu (TCVN 5575:2024 Bảng 1 & 3)
- Cột & Kèo thép tổ hợp hàn: Mác thép **Q345B** ($f_y = 345.0\text{ MPa}$, $f = 310.0\text{ MPa}$, $f_v = 180.0\text{ MPa}$, $E = 206.000\text{ MPa}$).
- Xà gồ, hệ giằng: Thép dập nguội **G450** hoặc **SS400** ($f_y = 235.0 - 450.0\text{ MPa}$).
- Hệ số điều kiện làm việc: $\gamma_c = 1.0$; Hệ số độ tin cậy vật liệu: $\gamma_{M0} = 1.05$, $\gamma_{M1} = 1.10$.

### B.2 Bu lông Cường độ cao Cấp bền 8.8 / 10.9 (TCVN 5575:2024 Mục 14.2)
- Cấp bền 8.8: Giới hạn bền $f_{ub} = 800\text{ MPa}$, giới hạn chảy $f_{yb} = 640\text{ MPa}$.
- Khả năng chịu kéo tính toán của bu lông:
$$N_{tb,Rd} = \frac{0.9 \cdot f_{ub} \cdot A_s}{\gamma_{M2}} \quad (\gamma_{M2} = 1.25)$$
- Khả năng chịu cắt tính toán của 1 mặt cắt:
$$V_{tb,Rd} = \frac{\alpha_v \cdot f_{ub} \cdot A}{\gamma_{M2}} \quad (\alpha_v = 0.6 \text{ cho cấp 8.8})$$

---

## C. TẢI TRỌNG & TỔ HỢP TẢI TRỌNG (TCVN 2737:2023)

### C.1 Tải trọng Tác dụng
1. **Tĩnh tải ($G$)**: Trọng lượng bản thân kết cấu thép, tôn mái ($5.0\text{ daN/m}^2$), trần/MEP ($10.0\text{ daN/m}^2$), xà gồ ($5.0\text{ daN/m}^2$).
2. **Hoạt tải sửa chữa mái ($Q_r$)**: Theo TCVN 2737:2023 Bảng 4, hoạt tải mái dốc không sử dụng là $30.0\text{ daN/m}^2$ ($\gamma_f = 1.3$).
3. **Tải trọng gió ($W$)**: Áp lực gió cơ sở $W_0$, dạng địa hình B, hệ số khí động $c$ đón gió, hút gió theo Phụ lục F TCVN 2737:2023.

### C.2 Tổ hợp Nội lực Tính toán
- **TH1 (Tĩnh tải + Hoạt tải mái)**: $1.2 G + 1.3 Q_r$ (chi phối mô men dương lớn nhất giữa nhịp kèo).
- **TH2 (Tĩnh tải + Gió ngang nhà)**: $1.0 G + 1.2 W_{ngang}$ (chi phối chuyển vị ngang đỉnh cột và mô men nách khung).
- **TH3 (Tĩnh tải tối thiểu + Gió hút bốc mái)**: $0.9 G + 1.2 W_{boc}$ (chi phối nhổ chân cột và nén bản cánh dưới kèo).

---

## D. TÍNH TOÁN THIẾT KẾ CẤU KIỆN THEO TCVN 5575:2024

### D.1 Kiểm tra Cột Khung Vát Chịu Nén Uốn (TCVN 5575:2024 Mục 7.2)
- Chiều dài tính toán trong mặt phẳng khung: $L_{cr,x} = \mu_x \cdot H_{cot}$.
- Độ mảnh quy ước: $\bar{\lambda}_x = \frac{\lambda_x}{\pi} \sqrt{\frac{f_y}{E}}$.
- Điều kiện ổn định nén uốn trong mặt phẳng:
$$\frac{N_{Ed}}{\chi_x \cdot A \cdot f_y / \gamma_{M1}} + \frac{k_x \cdot M_{y,Ed}}{W_{y} \cdot f_y / \gamma_{M0}} \le 1.00$$
- Điều kiện ổn định ngoài mặt phẳng (uốn - xoắn):
$$\frac{N_{Ed}}{\chi_y \cdot A \cdot f_y / \gamma_{M1}} + \frac{k_{LT} \cdot M_{y,Ed}}{\chi_{LT} \cdot W_{y} \cdot f_y / \gamma_{M1}} \le 1.00$$

### D.2 Kiểm tra Xà gồ Mái Dập Nguội C/Z (Uốn xiên 2 phương)
Tải trọng tác dụng phân rã vuông góc ($q_y$) và song song mặt mái ($q_x$):
$$\sigma_{xg} = \frac{M_x}{W_x} + \frac{M_y}{W_y} \le f; \quad f_y \le \frac{L_{xg}}{200}$$

### D.3 Thiết kế Chi tiết Liên kết Nách Khung (Rafter-to-Column Haunch Joint)
Liên kết nách khung chịu mô men uốn $M_{Ed}$, lực cắt $V_{Ed}$ và lực dọc $N_{Ed}$:
- **Phân bố lực kéo trong các bu lông cường độ cao**:
$$T_{b,max} = \frac{M_{Ed} \cdot y_{max}}{\sum y_i^2} - \frac{N_{Ed}}{n_b} \le N_{tb,Rd}$$
- **Kiểm tra tương tác Kéo - Cắt đồng thời (TCVN 5575:2024 Điều 14.2.3)**:
$$\frac{V_{Ed,b}}{V_{tb,Rd}} + \frac{T_{b,max}}{1.4 \cdot N_{tb,Rd}} \le 1.00$$
- **Kiểm tra chiều dày bản mã nách khung**: Chống uốn cục bộ bản mã theo đường chảy dẻo (Yield-line theory) $t_{plate} \ge t_{min}$.
- **Kiểm tra đường hàn góc bản cánh và bản bụng**:
$$\tau_w = \frac{V_{Ed}}{A_{wf}} \le f_{wv} = 180.0\text{ MPa}; \quad \sigma_{wf} = \frac{M_{Ed}}{W_{wf}} \le f_{wf}$$

---

## E. BẢNG TỔNG HỢP SCORECARD KIỂM TRA KHUNG THÉP TIỀN CHẾ

| STT | Cấu kiện / Liên kết | Nội lực thiết kế | Khả năng chịu lực | Chỉ số $\eta$ | Kết luận |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | Ổn định cột khung trong MP | $N= \text{___ kN}, M= \text{___ kNm}$ | $N_{Rd}, M_{Rd}$ | **___** | **ĐẠT** |
| 2 | Ổn định cột khung ngoài MP | $L_{cr,y} = \text{___ m}$ | $\chi_{LT} \cdot M_{Rd}$ | **___** | **ĐẠT** |
| 3 | Khả năng chịu uốn nén kèo | $M_{kèo} = \text{___ kNm}$ | $M_{Rd}$ | **___** | **ĐẠT** |
| 4 | Chuyển vị ngang đỉnh cột | $\Delta_x = \text{___ mm}$ | $[\Delta] = H/100$ | **___** | **ĐẠT** |
| 5 | Độ võng đỉnh nóc kèo | $f = \text{___ mm}$ | $[f] = L/250$ | **___** | **ĐẠT** |
| 6 | Bu lông nách khung (cấp 8.8) | $T_{max} = \text{___ kN}$ | $N_{tb,Rd} = \text{___ kN}$ | **___** | **ĐẠT** |
| 7 | Tương tác Kéo - Cắt bu lông | $\eta_{V} + \eta_{N}$ | $\le 1.00$ | **___** | **ĐẠT** |
| 8 | Đường hàn góc nách khung | $\tau_{w} = \text{___ MPa}$ | $f_{wv} = 180.0\text{ MPa}$ | **___** | **ĐẠT** |
| 9 | Ứng suất xà gồ Z (uốn xiên) | $\sigma_{xg} = \text{___ MPa}$ | $f = 235.0\text{ MPa}$ | **___** | **ĐẠT** |

