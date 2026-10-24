# PHỤ LỤC CỘT BTCT
## TÍNH TOÁN CỐT THÉP CỘT

---

## A. THÔNG TIN CHUNG

| Thông số | Giá trị |
|----------|---------|
| **Ký hiệu** | C1 |
| **Tầng** | Tầng 1 |
| **Tiết diện** | b×h = ___ × ___ mm |
| **Chiều cao** | H = ___ m |
| **Chiều dài tính toán** | l₀ = ___ m |

---

## B. VẬT LIỆU

| Vật liệu | Đặc trưng | Giá trị |
|-----------|-----------|---------|
| Bê tông | Mác/Cấp bền | ___ / C___ |
| | Cường độ chịu nén R_b | ___ MPa |
| | Cường độ chịu kéo R_bt | ___ MPa |
| Cốt thép dọc | Mác | CB___ |
| | Cường độ R_s | ___ MPa |
| Cốt thép đai | Mác | CB___ |
| | Đường kính φ | ___ mm |

---

## C. TẢI TRỌNG VÀ NỘI LỰC

### C.1. Tổ hợp tải trọng

| Tổ hợp | N (kN) | M_x (kNm) | M_y (kNm) |
|---------|---------|------------|------------|
| TH1: 1.2G + 1.3Q | ___ | ___ | ___ |
| TH2: 1.35G | ___ | ___ | ___ |
| TH3: G + Q + E/1.5 | ___ | ___ | ___ |

### C.2. Nội lực tính toán (lớn nhất)

$$N_{max} = \_\_\_ \text{ kN}$$
$$M_{x,max} = \_\_\_ \text{ kNm}$$
$$M_{y,max} = \_\_\_ \text{ kNm}$$

---

## D. TÍNH TOÁN

### D.1. Kiểm tra lệch tâm

$$e_0 = \frac{M}{N} = \frac{\_\_\_}{_\_\_} = \_\_\_ \text{ m} = \_\_\_ \text{ mm}$$

$$e_a = \frac{l_0}{400} = \frac{\_\_\_}{400} = \_\_\_ \text{ mm}$$

$$e = e_0 + e_a + \frac{h}{2} - a = \_\_\_ + \_\_\_ + \_\_\_ - \_\_\_ = \_\_\_ \text{ mm}$$

### D.2. Xác định chiều cao vùng nén

Giả thiết x = 0.5 × h₀ = ___ mm

$$\xi = \frac{x}{h_0} = \_\_\_$$

$$\xi_R = \_\_\_ \text{ (tra bảng theo mác bê tông) }$$

### D.3. Tính cốt thép đối xứng

$$A_{s1} = A_{s2} = \frac{N \times e - R_b \times b \times x \times (h_0 - 0.5x)}{R_{sc} \times (h_0 - a')}$$

$$= \frac{\_\_\_ \times \_\_\_ - \_\_\_ \times \_\_\_ \times \_\_\_ \times (\_\_\_ - 0.5 \times \_\_\_)}{\_\_\_ \times (\_\_\_ - \_\_\_)} = \_\_\_ \text{ mm}^2$$

### D.4. Kiểm tra hàm lượng

$$\mu = \frac{A_{s1} + A_{s2}}{b \times h} \times 100\% = \frac{2 \times \_\_\_}{\_\_\_ \times \_\_\_} \times 100\% = \_\_\_\%$$

| Điều kiện | Yêu cầu | Kết quả |
|-----------|----------|---------|
| μ_min | ≥ 0.8% | ✅ |
| μ_max | ≤ 4.0% | ✅ |

### D.5. Chọn cốt thép

| Vị trí | Diện tích yêu cầu (mm²) | Thép chọn | Diện tích thực (mm²) |
|---------|------------------------|------------|----------------------|
| As1 (dưới) | ___ | ___Ø___ | ___ |
| As2 (trên) | ___ | ___Ø___ | ___ |

---

## E. KIỂM TRA CỐT THÉP ĐAI

### E.1. Lực cắt

$$Q_{max} = \_\_\_ \text{ kN}$$

### E.2. Kiểm tra điều kiện

$$Q_{b,min} = 0.5 \times R_{bt} \times b \times h_0 \times \alpha_b$$

$$= 0.5 \times \_\_\_ \times \_\_\_ \times \_\_\_ \times \_\_\_ = \_\_\_ \text{ kN}$$

Nếu Q ≤ Q_b,min → Không cần tính cốt đai

### E.3. Bước cốt đai

$$s \leq \frac{h}{4} = \frac{\_\_\_}{4} = \_\_\_ \text{ mm}$$

$$s \leq 300 \text{ mm}$$

**Chọn:** φ___@___ mm

---

## F. BẢNG TỔNG HỢP

| Thông số | Kết quả |
|-----------|---------|
| Tiết diện | b×h = ___×___ mm |
| Chiều dài tính toán | l₀ = ___ m |
| Nội lực tính toán | N = ___ kN, M = ___ kNm |
| Cốt thép dọc | ___Ø___ (As = ___ mm²) |
| Cốt thép đai | φ___@___ mm |
| Hàm lượng cốt thép | μ = ___% |

---

## G. GHI CHÚ

1. Cốt thép dọc được bố trí đều trên chu vi tiết diện
2. Đai được đặt theo cấu tạo vùng đầu cột và giữa cột
3. Tại vùng nối buộc, đai được đặt dày hơn với bước s/2

---

## H. BẢN VẼ THAM CHIẾU

- Bản vẽ KC-01: Sơ đồ kết cấu tầng 1
- Bản vẽ KC-02: Chi tiết cột tầng 1
