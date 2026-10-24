# PHỤ LỤC MÓNG CỌC
## TÍNH TOÁN SỨC CHỊU TẢI CỌC

---

## A. THÔNG TIN CHUNG

| Thông số | Giá trị |
|----------|---------|
| **Ký hiệu** | ĐM-01 |
| **Loại cọc** | Cọc BTCT đúc sẵn / Cọc khoan nhồi |
| **Đường kính/Tiết diện** | d/b = ___ mm |
| **Chiều dài cọc** | L = ___ m |
| **Mũi cọc cao độ** | -___ m |
| **Sức chịu tải thiết kế** | P = ___ kN |

---

## B. SỐ LIỆU ĐỊA CHẤT

| Lớp | Độ sâu (m) | Chiều dày (m) | Loại đất | SPT N | q_si (kPa) | q_p (kPa) |
|------|-------------|----------------|----------|-------|-------------|------------|
| 1 | 0 ÷ ___ | ___ | ___ | ___ | ___ | — |
| 2 | ___ ÷ ___ | ___ | ___ | ___ | ___ | — |
| 3 | ___ ÷ ___ | ___ | ___ | ___ | ___ | — |
| 4 | ___ ÷ ___ | ___ | ___ | ___ | ___ | ___ |
| 5 | ___ ÷ ___ | ___ | ___ | ___ | ___ | ___ |

---

## C. ĐẶC TRƯNG CỌC

| Thông số | Giá trị |
|----------|---------|
| **Loại cọc** | ___ |
| **Chiều dài** | L = ___ m |
| **Tiết diện** | A_c = ___ × 10⁴ mm² |
| **Chu vi** | u = ___ mm |
| **Diện tích mũi** | A_p = ___ × 10⁶ mm² |
| **Mô men quán tính** | I = ___ × 10⁸ mm⁴ |
| **Bê tông mác** | ___ (R_b = ___ MPa) |

---

## D. TÍNH SỨC CHỊU TẢI CỌC

### D.1. Theo vật liệu

$$P_{vl} = φ \times (R_b \times A_c + R_s \times A_s)$$

| Thông số | Giá trị |
|-----------|---------|
| R_b | ___ MPa |
| A_c | ___ mm² |
| R_s | ___ MPa |
| A_s | ___ mm² |
| φ | 0.85 |
| **P_vl** | **___ kN** |

### D.2. Theo đất nền

#### Sức kháng thân cọc

$$Q_s = u \times \sum(q_{si} \times l_i)$$

| Lớp | q_si (kPa) | l_i (m) | Q_si (kN) |
|------|-------------|----------|------------|
| 1 | ___ | ___ | ___ |
| 2 | ___ | ___ | ___ |
| 3 | ___ | ___ | ___ |
| 4 | ___ | ___ | ___ |
| 5 | ___ | ___ | ___ |
| **Tổng Q_s** | | | **___** |

#### Sức kháng mũi cọc

$$Q_p = q_p \times A_p$$

| Thông số | Giá trị |
|-----------|---------|
| q_p | ___ kPa |
| A_p | ___ m² |
| **Q_p** | **___ kN** |

#### Sức chịu tải giới hạn

$$P_{ult} = Q_s + Q_p = \_\_\_ + \_\_\_ = \_\_\_ \text{ kN}$$

#### Sức chịu tải cho phép

$$P_{allow} = \frac{P_{ult}}{F} = \frac{\_\_\_}{2.5} = \_\_\_ \text{ kN}$$

### D.3. Kết luận

| Chỉ tiêu | Giá trị (kN) |
|-----------|--------------|
| Theo vật liệu (P_vl) | ___ |
| Theo đất nền (P_allow) | ___ |
| **Sức chịu tải thiết kế** | **min(P_vl, P_allow) = ___** |

---

## E. KIỂM TRA ĐÀI CỌC

### E.1. Thông số đài

| Thông số | Giá trị |
|-----------|---------|
| Kích thước đài | B × L = ___ × ___ m |
| Chiều dày đài | h = ___ m |
| Số cọc | n = ___ |
| Khoảng cách cọc | a = ___ m |

### E.2. Kiểm tra đài

#### Lực dọc truyền xuống đài

$$N = \_\_\_ \text{ kN}$$

#### Moment tại đáy đài

$$M_x = \_\_\_ \text{ kNm}$$
$$M_y = \_\_\_ \text{ kNm}$$

#### Phản lực lên cọc

**Cọc góc (xa nhất):**

$$P_{max} = \frac{N}{n} + \frac{M_x \times y_{max}}{\sum y_i^2} + \frac{M_y \times x_{max}}{\sum x_i^2}$$

$$= \frac{\_\_\_}{\_\_\_} + \frac{\_\_\_ \times \_\_\_}{\_\_\_} + \frac{\_\_\_ \times \_\_\_}{\_\_\_} = \_\_\_ \text{ kN}$$

#### Kiểm tra

$$P_{max} \leq 1.2 \times P_{allow} = 1.2 \times \_\_\_ = \_\_\_ \text{ kN}$$

$$\eta = \frac{P_{max}}{P_{allow}} = \_\_\_ \leq 1.0 \quad \textbf{✅/❌}$$

### E.3. Kiểm tra đâm thủng

$$Q_{dt} = N - q \times A_{dt}$$

| Thông số | Giá trị |
|-----------|---------|
| N | ___ kN |
| q | ___ kN/m² |
| A_dt | ___ m² |
| **Q_dt** | **___ kN** |

$$Q_{bt} = 0.75 \times R_{bt} \times u_{dt} \times h_0$$

| Thông số | Giá trị |
|-----------|---------|
| R_bt | ___ MPa |
| u_dt | ___ m |
| h_0 | ___ m |
| **Q_bt** | **___ kN** |

$$\eta = \frac{Q_{dt}}{Q_{bt}} = \_\_\_ \leq 1.0 \quad \textbf{✅/❌}$$

---

## F. KIỂM TRA LÚN

### F.1. Lún đàn hồi đỉnh cọc

$$S_e = \frac{P \times L}{E_p \times A_c} = \frac{\_\_\_ \times \_\_\_ \times 10^3}{\_\_\_ \times \_\_\_} = \_\_\_ \text{ mm}$$

### F.2. Lún của nhóm cọc

$$S = S_e + S_s$$

| Thành phần | Giá trị (mm) |
|-----------|--------------|
| Lún đàn hồi | ___ |
| Lún do nén đất | ___ |
| **Tổng lún** | **___** |

### F.3. Kiểm tra

$$S_{calc} = \_\_\_ \text{ mm} \leq S_{allow} = 50 \text{ mm} \quad \textbf{✅/❌}$$

---

## G. BẢNG TỔNG HỢP

| Thông số | Giá trị |
|-----------|---------|
| Loại cọc | ___ |
| Kích thước | ___ |
| Chiều dài cọc | ___ m |
| Sức chịu tải cọc đơn | ___ kN |
| Số lượng cọc | ___ |
| Kích thước đài | ___ × ___ m |
| Lún tính toán | ___ mm |
| Lún cho phép | 50 mm |

---

## H. GHI CHÚ

1. Cọc được hạ đến cao độ mũi cọc thiết kế
2. Kiểm tra độ sâu chôn cọc trong đài ≥ 1.5d (hoặc theo thiết kế)
3. Đầu cọc phá bê tông đầu cọc, để lộ cốt thép neo vào đài ≥ 30d
4. Thí nghiệm nén tĩnh ít nhất 1 cọc/500 cọc
5. Siêu âm kiểm tra chất lượng cọc khoan nhồi

---

## I. BẢN VẼ THAM CHIẾU

- Bản vẽ MC-01: Sơ đồ bố trí cọc
- Bản vẽ MC-02: Chi tiết đài cọc ĐM-01
- Bản vẽ MC-03: Chi tiết nối cọc
