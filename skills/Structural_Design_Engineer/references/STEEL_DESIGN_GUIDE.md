# Hướng dẫn Thiết kế Kết cấu Thép theo TCVN 5575:2024

> **Phiên bản:** 1.0.1
> **Cập nhật:** 2026-09-27
> **Tiêu chuẩn:** TCVN 5575:2024 — Kết cấu Thép

---

## 1. PHẠM VI ÁP DỤNG

Tiêu chuẩn này áp dụng cho thiết kế kết cấu thép các công trình xây dựng dân dụng và công nghiệp.

### 1.1 Các bộ phận kết cấu

| Loại | Phạm vi | Ví dụ |
|------|---------|-------|
| **Dầm** | Uốn | Dầm sàn, dầm cầu trục |
| **Cột** | Nén, Nén-Uốn | Cột khung, cột giàn |
| **Giằng** | Kéo, Nén | Giằng mái, giằng tường |
| **Liên kết** | Bu lông, Hàn | Nối dầm-cột, neo ghép |

---

## 2. VẬT LIỆU

### 2.1 Thép cán

| Mác thép | Giới hạn chảy f_y (MPa) | Cường độ kéo f_u (MPa) |
|----------|------------------------|------------------------|
| **SS400** | 250 | 400 |
| **SM490** | 325 | 490 |
| **ASTM A36** | 250 | 400 |
| **ASTM A572 Gr50** | 345 | 450 |

### 2.2 Bu lông

| Cấp bền | f_ub (MPa) | Ứng dụng |
|----------|-----------|-----------|
| **8.8** | 800 | Liên kết thông thường |
| **10.9** | 1000 | Liên kết chịu lực cao |

---

## 3. TÍNH TOÁN TIẾT DIỆN

### 3.1 Phân loại tiết diện

| Loại | Điều kiện | Kiểm tra |
|------|-----------|-----------|
| **Compact** | λ_p | M_p = W_p × f_y |
| **Non-compact** | λ_p < λ ≤ λ_r | M_u = W_e × f_y |
| **Slender** | λ > λ_r | Kiểm tra ổn định cục bộ |

### 3.2 Công thức cơ bản

**Độ bền uốn danh nghĩa:**
$$M_n = M_p \quad \text{(compact)}$$

**Độ bền cắt danh nghĩa:**
$$V_n = 0.6 \times f_y \times A_w / \gamma_M0$$

**Diện tích chống cắt:**
$$A_w = d \times t_w \quad \text{(cho tiết diện I)}$$

---

## 4. KIỂM TRA ỔN ĐỊNH TỔNG THỂ (LTB)

### 4.1 Hệ số giảm khả năng chịu mô men

$$\chi_{LT} = \frac{1}{\phi_{LT} + \sqrt{\phi_{LT}^2 - \lambda_{LT}^2}} \leq 1.0$$

Trong đó:
- $\phi_{LT} = 0.5 \times (1 + \alpha_{LT} \times (\lambda_{LT} - 0.2) + \lambda_{LT})$
- $\alpha_{LT}$ = hệ số imperfection

### 4.2 Độ mảnh giới hạn

$$λ_{LT} = \sqrt{\frac{M_p}{M_{cr}}}$$

**Độ mảnh cần thiết:**
$$λ_{p,LT} = 0.5 \times \sqrt{\frac{1}{C_{b}}}$$

---

## 5. LIÊN KẾT HÀN

### 5.1 Đường hàn góc

**Cường độ chịu cắt của đường hàn:**
$$f_{vw} = 0.6 \times f_u / \gamma_{MW}$$

| Loại | a (mm) | Ứng dụng |
|------|--------|----------|
| **Nhỏ** | 3-5 | Liên kết phụ |
| **Trung bình** | 6-8 | Liên kết chính |
| **Lớn** | 10-12 | Chịu lực cao |

### 5.2 Công thức kiểm tra

**Đường hàn góc:**
$$τ_f = \frac{V}{0.707 \times a \times l_w} \leq f_{vw}$$

**Đường hàn đối đầu:**
$$σ_f = \frac{N}{l_w \times t} \leq 0.7 \times f_u / \gamma_{MW}$$

---

## 6. LIÊN KẾT BU LÔNG

### 6.1 Các dạng phá hoại

| Dạng | Công thức |
|------|-----------|
| **Cắt bulong** | $V_n = 0.6 \times f_{ub} \times A_b$ |
| **Ép mặt** | $R_n = 2.4 \times d \times t \times f_u$ |
| **Kéo bulong** | $T_n = 0.75 \times f_{ub} \times A_b$ |

### 6.2 Khoảng cách và cự ly

| Thông số | Giá trị tối thiểu |
|-----------|-------------------|
| **Khoảng cách Lỗ** | $p \geq 2.5d$ |
| **Cự ly mép** | $e \geq 1.5d$ |
| **Bước bu lông** | $p \leq 200mm$ |

---

## 7. VÍ DỤ TÍNH TOÁN

### 7.1 Ví dụ: Kiểm tra dầm I

**Input:**
- Dầm I 300×150×6.5×9
- L = 6m, đầu ngàm-đầu tự do
- q = 15 kN/m
- Thép SS400

**Tính toán:**

1. **Đặc trưng tiết diện:**
   - A = 46.78 cm²
   - I_x = 7210 cm⁴
   - W_x = 481 cm³
   - W_p,x = 540 cm³

2. **Nội lực:**
   - M_max = qL²/3 = 15×36/3 = 180 kNm
   - V_max = qL = 90 kN

3. **Kiểm tra:**
   - η_M = M/S = 180/(481×10⁻³×250) = 1.49 > 1.0 ❌

**Kết luận:** Dầm không đạt → Tăng tiết diện hoặc giảm nhịp

---

## 8. BẢNG TRA TIẾT DIỆN

### 8.1 Thép hình chữ I (H)

| Ký hiệu | h×b×t_w×t_f | A (cm²) | W_x (cm³) | M_p (kNm) |
|---------|--------------|---------|-----------|-----------|
| H200×100 | 200×100×5.6×8 | 21.3 | 383 | 25.4 |
| H300×150 | 300×150×6.5×9 | 46.8 | 721 | 47.8 |
| H400×200 | 400×200×8×13 | 72.2 | 1360 | 90.2 |

### 8.2 Thép hình chữ C (U)

| Ký hiệu | h×b×t_w×t_f | A (cm²) | I_x (cm⁴) |
|---------|--------------|---------|-----------|
| U100×50 | 100×50×5×7.5 | 10.6 | 191 |
| U150×75 | 150×75×6.5×10 | 18.4 | 561 |
| U200×80 | 200×80×7.5×11 | 23.4 | 1040 |

---

## 9. PHỤ LỤC

### 9.1 Hệ số điều kiện làm việc γ_c

| Điều kiện | γ_c |
|-----------|-----|
| Dầm sàn | 1.0 |
| Dầm cầu trục | 0.9 |
| Giằng đỡ tải trọng động | 0.85 |

### 9.2 Hệ số độ tin cậy γ_M

| Thông số | γ_M |
|---------|-----|
| γ_M0 | 1.025 |
| γ_M1 | 1.050 |
| γ_M2 | 1.100 |

---

## 10. TÀI LIỆU THAM KHẢO

- TCVN 5575:2024 — Kết cấu Thép
- AISC 360-22 — Specification for Structural Steel Buildings
- EN 1993-1-1 — Eurocode 3: Design of steel structures
