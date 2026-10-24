# Hướng dẫn Thiết kế Bê tông Cốt thép theo TCVN 5574:2018

> **Phiên bản:** 1.1.0
> **Cập nhật:** 2026-09-27
> **Tiêu chuẩn:** TCVN 5574:2018 — Kết cấu Bê tông và Bê tông Cốt thép

---

## 1. PHẠM VI ÁP DỤNG

Thiết kế các cấu kiện BTCT chịu uốn, nén, kéo, cắt và xoắn.

### 1.1 Phân loại cấu kiện

| Loại | Tiết diện | Chiều dài | Ví dụ |
|------|-----------|-----------|--------|
| **Dầm** | Chữ nhật, chữ T, chữ L | L/h ≥ 4 | Dầm sàn, dầm cầu |
| **Cột** | Chữ nhật, tròn, vuông | L/h ≤ 4 | Cột khung, cột lõi |
| **Sàn** | Bản mỏng | L/h ≥ 30 | Sàn toàn khối |

---

## 2. VẬT LIỆU

### 2.1 Bê tông

| Mác/ Cấp bền | R_b (MPa) | R_bt (MPa) | E_b (MPa) |
|-------------|-----------|-------------|-----------|
| **B15 / C12/15** | 8.5 | 0.75 | 21000 |
| **B20 / C16/20** | 11.5 | 1.00 | 24500 |
| **B25 / C20/25** | 14.5 | 1.15 | 27500 |
| **B30 / C25/30** | 17.0 | 1.30 | 30000 |
| **B35 / C30/37** | 19.5 | 1.45 | 31500 |
| **B40 / C32/40** | 22.0 | 1.60 | 32500 |

### 2.2 Cốt thép

| Mác | R_s (MPa) | R_sc (MPa) | R_s,ser (MPa) |
|-----|-----------|------------|---------------|
| **CB240-T** | 210 | 210 | 240 |
| **CB300-V** | 260 | 300 | 300 |
| **CB350-V** | 300 | 350 | 350 |
| **CB400-V** | 350 | 400 | 400 |
| **CB500-V** | 415 | 500 | 500 |

### 2.3 Hệ số

| Hệ số | Giá trị |
|--------|---------|
| γ_b | 1.3 |
| γ_s | 1.15 |
| α_R | Xem bảng theo mác |

---

## 3. THIẾT KẾ CHỊU UỐN

### 3.1 Tiết diện chữ nhật

**Chiều cao vùng nén:**
$$x = \frac{R_s \times A_s}{R_b \times b}$$

**Kiểm tra điều kiện:**
$$\xi = \frac{x}{h_0} \leq \xi_R$$

**Mô men chịu lực:**
$$M_R = R_b \times b \times x \times (h_0 - 0.5x)$$

### 3.2 Hệ số ξ_R theo mác

| Mác bê tông | ξ_R | α_R |
|-------------|-----|------|
| B15 | 0.65 | 0.90 |
| B20 | 0.62 | 0.88 |
| B25 | 0.59 | 0.86 |
| B30 | 0.57 | 0.85 |
| B35 | 0.56 | 0.84 |
| B40 | 0.54 | 0.83 |

### 3.3 Thiết kế cốt thép

$$A_s = \frac{R_b \times b \times h_0}{R_s} \times \xi$$

**Diện tích tối thiểu:**
$$A_{s,min} = 0.001 \times b \times h_0$$

---

## 4. THIẾT KẾ CHỊU NÉN LỆCH TÂM

### 4.1 Lệch tâm lớn (ξ ≤ ξ_R)

$$N \leq \frac{R_b \times b \times x}{γ_b} + \frac{R_{sc} \times A_s'}{γ_s}$$

$$M \leq [R_b \times b \times x \times (h_0 - 0.5x) + R_{sc} \times A_s' \times (h_0 - a')]/γ_b$$

### 4.2 Lệch tâm bé (ξ > ξ_R)

Sử dụng biểu đồ tương tác hoặc phương pháp gần đúng.

---

## 5. KIỂM TRA CẮT

### 5.1 Cốt đai đứng

$$Q_{b} = 0.5 \times R_{bt} \times b \times h_0 \times \alpha_b$$

**Trong đó:**
$$\alpha_b = \frac{1}{1 + \phi}$$

### 5.2 Cốt xiên

$$Q_{sw} = 0.8 \times q_{sw} \times c_0 \times \sin\alpha$$

### 5.3 Tổng khả năng chịu cắt

$$Q_u = Q_b + Q_{sw} + Q_{inc}$$

**Điều kiện:**
$$\eta_Q = \frac{Q}{Q_u} \leq 1.0$$

---

## 6. KIỂM TRA VÕNG

### 6.1 Độ võng giới hạn

| Cấu kiện | [f/L] |
|----------|--------|
| Dầm sàn | 1/250 |
| Dầm cầu | 1/400 |
| Sàn mái | 1/200 |

### 6.2 Công thức tính võng

**Cho dầm đơn giản:**
$$f = \frac{5qL^4}{384EI} \times \beta$$

**Hệ số β:**
- Tĩnh tải: β = 1
- Dài hạn: β = 2.0
- Ngắn hạn: β = 1.5

---

## 7. KIỂM TRA BỀ RỘNG KHE NỨT

### 7.1 Giới hạn

| Môi trường | a_crc (mm) |
|------------|------------|
| Trong nhà, độ ẩm bình thường | 0.4 |
| Trong nhà, độ ẩm cao | 0.3 |
| Ngoài trời | 0.3 |
| Môi trường ăn mòn | 0.2 |

### 7.2 Công thức

$$a_{crc} = \psi \times \phi \times \sigma_s \times \frac{l_s}{E_s}$$

**Trong đó:**
- ψ = 1.0 - 0.7 × (R_{bt}/σ_s)
- l_s = 0.5s + 0.1φ/μ_eff

---

## 8. SÀN BTCT 2 PHƯƠNG

### 8.1 Moment trong sàn

$$M_x = \alpha_x \times q \times L_x^2$$

$$M_y = \alpha_y \times q \times L_y^2$$

### 8.2 Hệ số α

| Loại sàn | α_x | α_y |
|----------|------|------|
| 4 cạnh tự do | 1/11 | 1/16 |
| 4 cạnh ngàm | 1/16 | 1/22 |
| 1 cạnh tự do | 1/14 | 1/20 |

---

## 9. BẢNG TRA

### 9.1 Hàm lượng cốt thép

| Vị trí | ρ_min (%) | ρ_max (%) |
|---------|----------|-----------|
| Dầm uốn | 0.05 | 4.0 |
| Sàn | 0.10 | 4.0 |
| Cột nén | 0.80 | 4.0 |
| Cấu kiện lanh tô | 0.25 | 4.0 |

### 9.2 Lớp bảo vệ

| Điều kiện | c (mm) |
|-----------|--------|
| Trong nhà, bình thường | 20 |
| Ngoài trời | 25 |
| Tiếp xúc đất | 30 |
| Môi trường biển | 40 |

---

## 10. VÍ DỤ TÍNH TOÁN

### 10.1 Ví dụ: Dầm chữ nhật

**Input:**
- b×h = 200×400 mm
- h₀ = 365 mm
- B25 (R_b = 14.5 MPa)
- CB300 (R_s = 260 MPa)
- M = 120 kNm

**Tính:**

1. ξ = M/(R_b×b×h₀²) = 120×10⁶/(14.5×200×365²) = 0.31

2. Kiểm tra: ξ_R(B25) = 0.59 → 0.31 < 0.59 ✓

3. x = ξ × h₀ = 0.31 × 365 = 113 mm

4. A_s = ξ × R_b × b × h₀ / R_s = 0.31 × 14.5 × 200 × 365 / 260
   = 1268 mm² → **3Ø25 (1473 mm²)**

---

## 11. TÀI LIỆU THAM KHẢO

- TCVN 5574:2018 — Kết cấu Bê tông và BTCT
- TCVN 2737:2023 — Tải trọng và tác động
- ACI 318-19 — Building Code for Structural Concrete
- EN 1992-1-1 — Eurocode 2: Design of concrete structures
