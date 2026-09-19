# PHỤ LỤC TÍNH TOÁN KẾT CẤU — CỘT BTCT
## Cấu kiện: {{column_name}}

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị | Đơn vị |
|-----------|----------|---------|
| Công trình | {{project_name}} | - |
| Mã số | {{project_code}} | - |
| Giai đoạn | {{stage}} | - |
| Cấu kiện | {{column_name}} | - |
| Tiêu chuẩn | TCVN 5574:2018 | - |

### 1.1 Tiêu chuẩn áp dụng

| Tiêu chuẩn | Số hiệu | Nội dung |
|-------------|----------|----------|
| Tải trọng | TCVN 2737:2023 | Tải trọng và tác động |
| Bê tông cốt thép | TCVN 5574:2018 | Thiết kế BTCT |
| Cốt thép | TCVN 1651-2:2018 | Thép thanh vằn |

---

## 2. VẬT LIỆU

### 2.1 Bê tông

| Thông số | Giá trị | Đơn vị | Căn cứ |
|-----------|----------|---------|---------|
| Cấp độ bền | {{concrete_grade}} | - | TCVN 5574:2018 Điều 5.2 |
| f_c | {{fc}} | MPa | R_b = f_c × 0.76 |
| f_ct | {{fct}} | MPa | R_bt = f_ct × 0.76 |
| γ_c | 1.3 | - | Hệ số an toàn |
| E_c | {{Ec}} | MPa | Modun đàn hồi |

### 2.2 Cốt thép

| Thông số | Giá trị | Đơn vị | Căn cứ |
|-----------|----------|---------|---------|
| Loại thép | {{steel_grade}} | - | TCVN 1651-2:2018 |
| f_y | {{fy}} | MPa | Cường độ chịu kéo |
| f_yk | {{fyk}} | MPa | Cường độ chảy đặc trưng |
| γ_s | 1.15 | - | Hệ số an toàn |
| E_s | 200000 | MPa | Modun đàn hồi |

### 2.3 Đặc tính tiết diện

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| b × h | {{b}} × {{h}} | mm × mm |
| Chiều cao tầng | H = {{H}} | mm |
| Chiều dày lớp bảo vệ | a = {{a}} | mm |
| d = h - a | {{d}} | mm |

---

## 3. TẢI TRỌNG VÀ NỘI LỰC

### 3.1 Nội lực tính toán (tổ hợp bất lợi nhất)

| Loại | Giá trị | Đơn vị | Vị trí |
|------|----------|---------|---------|
| Lực nén | N_ed = {{N_ed}} | kN | Chân cột |
| Mô men | M_ed = {{M_ed}} | kNm | Đỉnh/chân cột |
| Lực cắt | V_ed = {{V_ed}} | kN | Toàn cột |

### 3.2 Tổ hợp tải trọng

| Tổ hợp | Loại | Mô tả |
|---------|------|-------|
| TH1 | ULS | 1.0G + 1.0Q |
| TH2 | ULS | 1.0G + 0.9Q + 1.0EX |
| TH3 | SLS | G + Q (dài hạn) |

---

## 4. SƠ ĐỒ KẾT CẤU

### 4.1 Sơ đồ tính

```
        M_top = {{M_top}} kNm
    ─────┼─────
    │           │
    │           │
    │  N = {{N_ed}} kN    │
    │           │
    │           │
    ─────┼─────
        M_bot = {{M_bot}} kNm

Điều kiện biên: {{boundary_condition}}
Chiều cao tính toán: H_ef = {{H_ef}} mm
```

### 4.2 Kích thước hình học

| Thông số | Giá trị |
|-----------|----------|
| Tiết diện | b × h = {{b}} × {{h}} mm |
| Chiều cao tầng | H = {{H}} mm |
| Chiều cao tính toán | H_ef = {{H_ef}} mm |

---

## 5. TÍNH TOÁN CHI TIẾT

### 5.1 Kiểm tra cốt thép đối xứng (phương pháp gần đúng)

**Bước 1:** Xác định độ lệch tâm ban đầu
```
e₀ = M_ed / N_ed = {{M_ed}} × 10³ / {{N_ed}} = {{e0}} mm
```

**Bước 2:** Độ lệch tâm ngẫu nhiên
```
e_a = max(H/30, 20) = max({{H}}/30, 20) = {{ea}} mm
```

**Bước 3:** Độ lệch tâm tính toán
```
e = e₀ + e_a = {{e0}} + {{ea}} = {{e}} mm
```

**Bước 4:** Xác định chiều cao vùng nén (giả thiết α = 0.1)
```
a = 40 mm (giả thiết ban đầu)
d' = a = 40 mm
d = h - a = {{h}} - 40 = {{d}} mm
h₀ = h - 2a = {{h}} - 80 = {{h0}} mm
```

**Bước 5:** Tính lực nén cân bằng
```
N_b = φ × f_c × b × h₀
    = 0.9 × {{fc}} × {{b}} × {{h0}} / 10³
    = {{Nb}} kN
```

**Bước 6:** So sánh N_ed với N_b

| Kiểm tra | Giá trị | N_b | Kết luận |
|----------|---------|-----|----------|
| N_ed = {{N_ed}} kN | ≤ | N_b = {{Nb}} kN | {{check_Nb}} |

**Nếu N_ed > N_b:** Tiết diện cốt thép đối xứng
**Nếu N_ed < N_b:** Tiết diện cốt thép không đối xứng

**Bước 7:** Tính cốt thép yêu cầu (trường hợp N_ed > N_b)

```
ξ = N_ed × 10³ / (φ × f_c × b × h₀)
  = {{N_ed}} × 10³ / (0.9 × {{fc}} × {{b}} × {{h0}})
  = {{xi_calc}}

ζ = 1 - 0.5 × ξ = 1 - 0.5 × {{xi_calc}} = {{zeta_calc}}
```

**Tính M₁:**
```
M₁ = N_ed × (e - ζ × h₀/2) = {{N_ed}} × ({{e}} - {{zeta_calc}} × {{h0}}/2)
    = {{M1}} kNm
```

**Tính A_s,req:**
```
A_s,req = M₁ × 10⁶ / (f_y/γ_s × ζ × h₀)
        = {{M1}} × 10⁶ / ({{fy_over_gamma}} × {{zeta_calc}} × {{h0}})
        = {{As_req}} mm²
```

**Bước 8:** Chọn cốt thép

| Thông số | Giá trị |
|-----------|----------|
| A_s,req | {{As_req}} mm² |
| A'_s,req | {{As_req}} mm² (đối xứng) |
| A_s,prov | {{As_prov}} mm² |
| η_M = A_s,req / A_s,prov | {{eta_M}} |

### 5.2 Kiểm tra cốt thép chịu cắt

**Tại vị trí có V_max = {{V_ed}} kN**

**Bước 1:** Kiểm tra bê tông
```
V_c = 0.3 × φ × f_ct × b × h₀
    = 0.3 × 0.9 × {{fct}} × {{b}} × {{h0}} / 10³
    = {{Vc}} kN
```

**Bước 2:** Xác định đai yêu cầu
```
V_sw = V_ed - V_c = {{V_ed}} - {{Vc}} = {{Vsw}} kN
```

**Bước 3:** Chọn đai φ{{stirrup_dia}}
```
A_sw = 4 × {{A_stirrup}} = {{A_sw}} mm² (4 nhánh)
s = A_sw × f_yw × h₀ / (V_sw × 10³)
  = {{A_sw}} × {{fyw}} × {{h0}} / ({{Vsw}} × 10³)
  = {{s_calc}} mm
```

**Kiểm tra:**
```
η_V = V_ed / (V_c + V_sw)
    = {{V_ed}} / ({{Vc}} + {{Vsw}})
    = {{eta_V}} < 1.0 ✓
```

---

## 6. BẢNG TỔNG HỢP KẾT QUẢ

### 6.1 Cốt thép đã chọn

| Loại | Thép | Số thanh | A (mm²) |
|------|------|----------|----------|
| Thép góc | {{corner_bar}} | {{n_corner}} | {{A_corner}} |
| Thép bên | {{side_bar}} | {{n_side}} | {{A_side}} |
| Tổng | - | - | {{A_total}} |

### 6.2 Kiểm tra η

| Kiểm tra | η_tính_toán | Giới hạn | Trạng thái |
|----------|--------------|-----------|------------|
| Chịu nén lệch tâm | {{eta_M}} | ≤ 1.0 | {{status_M}} |
| Chịu cắt | {{eta_V}} | ≤ 1.0 | {{status_V}} |
| Hàm lượng thép | {{rho}}% | 0.5-5% | {{status_rho}} |

---

## 7. KẾT LUẬN

### 7.1 Kết quả kiểm tra

| Hạng mục | Kết quả |
|-----------|---------|
| Chịu nén lệch tâm | {{result_M}} |
| Chịu cắt | {{result_V}} |
| Hàm lượng thép | {{result_rho}} |

### 7.2 Đánh giá chung

{{conclusion}}

---

## 8. PHỤ LỤC

### 8.1 Hệ số uốn dọc φ

| λ = l₀/h | φ |
|-----------|-----|
| ≤ 8 | 1.00 |
| 10 | 0.98 |
| 12 | 0.96 |
| 14 | 0.94 |
| 16 | 0.92 |
| 18 | 0.90 |
| 20 | 0.88 |
| 22 | 0.86 |
| 24 | 0.84 |
| 26 | 0.82 |
| 28 | 0.80 |
| 30 | 0.78 |

---

## 9. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|--------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Kiểm tra | {{reviewer}} | | {{review_date}} |
| Duyệt | {{approver}} | | {{approve_date}} |

---

*Mẫu phụ lục tính toán kết cấu — Cột BTCT*
*Generated by AI Structural Engineer — v1.0*
