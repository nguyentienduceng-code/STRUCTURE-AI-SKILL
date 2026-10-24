# PHỤ LỤC SÀN BTCT
## TÍNH TOÁN CỐT THÉP SÀN

---

## A. THÔNG TIN CHUNG

| Thông số | Giá trị |
|----------|---------|
| **Ký hiệu** | S1 |
| **Vị trí** | Tầng ___ |
| **Loại sàn** | Toàn khối / Đổ sẵn |
| **Kích thước** | Lx × Ly = ___ × ___ m |
| **Chiều dày** | h = ___ mm |
| **Lớp bảo vệ** | a = ___ mm |

---

## B. VẬT LIỆU

| Vật liệu | Đặc trưng | Giá trị |
|-----------|-----------|---------|
| Bê tông | Mác/Cấp bền | ___ / C___ |
| | Cường độ R_b | ___ MPa |
| | Cường độ R_bt | ___ MPa |
| Cốt thép | Mác | CB___ |
| | Cường độ R_s | ___ MPa |

---

## C. TẢI TRỌNG

| Loại tải | Giá trị (kN/m²) |
|-----------|------------------|
| Tĩnh tải (g) | |
| - Trọng lượng bản thân | ___ (h × 25) |
| - Lớp hoàn thiện | ___ |
| - Vật liệu khác | ___ |
| **Tổng tĩnh tải g** | **___** |
| Hoạt tải (q) | ___ |

---

## D. TỔ HỢP TẢI TRỌNG

| Tổ hợp | Công thức | q (kN/m²) |
|---------|-----------|------------|
| ULS (thiết kế) | 1.2g + 1.3q | ___ |
| SLS (sử dụng) | g + q | ___ |

---

## E. TÍNH NỘI LỰC

### E.1. Sàn 2 phương

$$μ = \frac{L_{min}}{L_{max}} = \frac{\min(L_x, L_y)}{\max(L_x, L_y)} = \frac{\_\_\_}{\_\_\_} = \_\_\_$$

### E.2. Moment tại nhịp

| Vị trí | Hệ số α | Moment (kNm/m) |
|---------|---------|----------------|
| M_x (+) | ___ | M = α × q × Lx² = ___ × ___ × ___² = **___** |
| M_y (+) | ___ | M = α × q × Ly² = ___ × ___ × ___² = **___** |

### E.3. Moment tại gối

| Vị trí | Hệ số | Moment (kNm/m) |
|---------|--------|----------------|
| M_x (-) | ___ | **___** |
| M_y (-) | ___ | **___** |

---

## F. TÍNH CỐT THÉP

### F.1. Phương x

**Nhịp giữa (dưới):**

$$α_m = \frac{M}{R_b \times b \times h_0^2} = \frac{\_\_\_}{\_\_\_ \times 1000 \times \_\_\_^2} = \_\_\_$$

$$ξ = 1 - \sqrt{1 - 2α_m} = \_\_\_$$

$$A_s = ξ \times \frac{R_b}{R_s} \times b \times h_0 = \_\_\_ \times \frac{\_\_\_}{\_\_\_} \times 1000 \times \_\_\_ = \_\_\_ \text{ mm}^2/\text{m}$$

| Thông số | Giá trị |
|-----------|---------|
| As yêu cầu | ___ mm²/m |
| Chọn thép | **Ø___ @ ___** |
| As thực | ___ mm²/m |
| Kiểm tra | η = As_req/As_prov = ___ ≤ 1.0 |

**Gối (trên):**

Tương tự tính với M(-) = ___ kNm/m

### F.2. Phương y

Tính tương tự với M_y = ___ kNm/m

---

## G. KIỂM TRA VÕNG

$$f = \frac{q_{SLS} \times L_x^4}{β \times E \times I}$$

| Thông số | Giá trị |
|-----------|---------|
| q_SLS | ___ kN/m² |
| E_b | ___ MPa |
| I | b × h³/12 = ___ mm⁴ |
| f_tính | ___ mm |
| f_cho phép | L/250 = ___/250 = ___ mm |
| **Kết luận** | **✅/❌** |

---

## H. KIỂM TRA NỨT

$$a_{crc} = ψ × φ × σ_s × \frac{l_s}{E_s}$$

| Thông số | Giá trị |
|-----------|---------|
| σ_s | ___ MPa |
| φ | ___ mm |
| l_s | ___ mm |
| a_crc tính | ___ mm |
| a_crc cho phép | 0.4 mm |
| **Kết luận** | **✅/❌** |

---

## I. BẢNG TỔNG HỢP CỐT THÉP

| Vị trí | M (kNm/m) | As (mm²/m) | Chọn thép | As_prov |
|---------|------------|------------|-----------|----------|
| Nhịp x | ___ | ___ | Ø___@___ | ___ |
| Gối x | ___ | ___ | Ø___@___ | ___ |
| Nhịp y | ___ | ___ | Ø___@___ | ___ |
| Gối y | ___ | ___ | Ø___@___ | ___ |

---

## J. GHI CHÚ THI CÔNG

1. Thép lớp trên đặt trên, thép lớp dưới đặt dưới
2. Khoảng cách giữa 2 lớp thép: ___ mm
3. Thép cấu tạo: φ___@___ mm
4. Neo thép vào dầm: ___d, uốn góc 90°

---

## K. BẢN VẼ THAM CHIẾU

- Bản vẽ KC-__: Sơ đồ cốt thép sàn tầng ___
- Bản vẽ KC-__: Chi tiết thép sàn
