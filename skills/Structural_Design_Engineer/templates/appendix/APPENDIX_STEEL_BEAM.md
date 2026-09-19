# PHỤ LỤC TÍNH TOÁN KẾT CẤU — DẦM THÉP
## Cấu kiện: {{beam_name}}

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị | Đơn vị |
|-----------|----------|---------|
| Công trình | {{project_name}} | - |
| Mã số | {{project_code}} | - |
| Giai đoạn | {{stage}} | - |
| Cấu kiện | {{beam_name}} | - |
| Tiêu chuẩn | TCVN 5575:2024 | - |

### 1.1 Tiêu chuẩn áp dụng

| Tiêu chuẩn | Số hiệu | Nội dung |
|-------------|----------|----------|
| Kết cấu thép | TCVN 5575:2024 | Thiết kế kết cấu thép |
| Tải trọng | TCVN 2737:2023 | Tải trọng và tác động |
| Bu lông | TCVN 5575:2024 Điều 6 | Liên kết bu lông |

---

## 2. VẬT LIỆU

### 2.1 Thép cán

| Thông số | Giá trị | Đơn vị | Căn cứ |
|-----------|----------|---------|---------|
| Mác thép | {{steel_grade}} | - | TCVN 5575:2024 Bảng 1 |
| f_y | {{fy}} | MPa | Giới hạn chảy |
| f_u | {{fu}} | MPa | Cường độ kéo đứt |
| γ_M0 | 1.0 | - | Hệ số an toàn (thép cán) |
| γ_M1 | 1.1 | - | Hệ số an toàn (mất ổn định) |
| E | 210000 | MPa | Modun đàn hồi |

### 2.2 Tiết diện

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Loại tiết diện | {{section_type}} | - |
| Ký hiệu | {{section_name}} | - |
| h × b × t_w × t_f | {{h}} × {{b}} × {{tw}} × {{tf}} | mm × mm × mm × mm |
| A | {{A}} | cm² | Diện tích mặt cắt |
| I_x | {{Ix}} | cm⁴ | Momen quán tính |
| W_x | {{Wx}} | cm³ | Momen chống uốn |
| S_x | {{Sx}} | cm³ | Momen tĩnh |
| i_x | {{ix}} | cm | Bán kính quán tính |
| i_y | {{iy}} | cm | Bán kính quán tính |

---

## 3. TẢI TRỌNG VÀ NỘI LỰC

### 3.1 Tải trọng

| Loại | Giá trị | Đơn vị | Ghi chú |
|------|----------|---------|---------|
| Tĩnh tải | g = {{g}} | kN/m | |
| Hoạt tải | q = {{q}} | kN/m | |
| Tổng tải | p = g + q = {{p}} | kN/m | |

### 3.2 Nội lực tính toán

| Loại | Giá trị | Đơn vị | Vị trí |
|------|----------|---------|---------|
| Mô men | M_ed = {{M_ed}} | kNm | Nhịp giữa |
| Lực cắt | V_ed = {{V_ed}} | kN | Gối |
| Lực dọc | N_ed = {{N_ed}} | kN | (nếu có) |

---

## 4. SƠ ĐỒ KẾT CẤU

### 4.1 Sơ đồ tính

```
    p = {{p}} kN/m
    ┌─────────────────────────────────┐
────┤                                 ├──
   M₁         M₂                M₃    M₄
    └─────────────────────────────────┘
         L₁ = {{L1}}m      L₂ = {{L2}}m

Điều kiện biên: {{boundary_condition}}
Chiều dài tính toán: L = {{L}} m
```

---

## 5. TÍNH TOÁN CHI TIẾT

### 5.1 Kiểm tra khả năng chịu uốn

**Bước 1:** Kiểm tra tiết diện theo phân loại

| Thông số | Giá trị | Giới hạn | Phân loại |
|-----------|----------|-----------|------------|
| c/t_f | {{c_tf}} | ≤ 9ε | {{class_tf}} |
| h_w/t_w | {{hw_tw}} | ≤ 72ε | {{class_hw}} |

**Phân loại tiết diện: {{section_class}}**

**Bước 2:** Tính khả năng chịu uốn

```
W_pl = {{W_pl}} cm³ = {{W_pl_SI}} × 10⁻⁶ m³
M_c,Rd = W_pl × f_y / γ_M0 = {{W_pl_SI}} × 10⁻⁶ × {{fy_SI}} / {{gamma_M0}}
       = {{M_cRd}} kNm
```

**Bước 3:** Kiểm tra

```
η_M = M_ed / M_c,Rd = {{M_ed}} / {{M_cRd}} = {{eta_M}} ≤ 1.0 ✓
```

### 5.2 Kiểm tra khả năng chịu cắt

**Bước 1:** Kiểm tra panel bụng

```
V_ed = {{V_ed}} kN
V_pl,Rd = A_v × f_y / (√3 × γ_M0)
         = {{Av}} × 10⁻⁴ × {{fy_SI}} / (1.732 × {{gamma_M0}})
         = {{V_plRd}} kN
```

**Bước 2:** Kiểm tra

```
η_V = V_ed / V_pl,Rd = {{V_ed}} / {{V_plRd}} = {{eta_V}} ≤ 1.0 ✓
```

### 5.3 Kiểm tra ổn định tổng thể (LTB)

**Bước 1:** Xác định độ mảnh

```
λ_LT = √(W_pl × f_y / M_cr)
     = √({{W_pl_SI}} × 10⁻⁶ × {{fy_SI}} / {{M_cr_SI}})
     = {{lambda_LT}}
```

**Bước 2:** Xác định hệ số χ_LT

```
α_LT = {{alpha_LT}} (đường cong {{curve_LT}})
Φ_LT = 0.5 × [1 + α_LT × (λ_LT - 0.2) + λ_LT²]
     = 0.5 × [1 + {{alpha_LT}} × ({{lambda_LT}} - 0.2) + {{lambda_LT}}²]
     = {{Phi_LT}}

χ_LT = 1 / (Φ_LT + √(Φ_LT² - λ_LT²))
     = 1 / ({{Phi_LT}} + √({{Phi_LT}}² - {{lambda_LT}}²))
     = {{chi_LT}}

χ_LT,mod = {{chi_LT_mod}} (nếu dùng phương pháp giảm chiều dài)
```

**Bước 3:** Kiểm tra

```
M_b,Rd = χ_LT,mod × W_pl × f_y / γ_M1
        = {{chi_LT_mod}} × {{W_pl_SI}} × 10⁻⁶ × {{fy_SI}} / {{gamma_M1}}
        = {{M_bRd}} kNm

η_LTB = M_ed / M_b,Rd = {{M_ed}} / {{M_bRd}} = {{eta_LTB}} ≤ 1.0 ✓
```

### 5.4 Kiểm tra độ võng

**Bước 1:** Tính độ võng do tải trọng

```
I_x = {{Ix}} cm⁴ = {{Ix_SI}} × 10⁻⁸ m⁴
f = 5 × p × L⁴ / (384 × E × I)
  = 5 × {{p_SI}} × {{L_SI}}⁴ / (384 × {{E}} × {{Ix_SI}} × 10⁻⁸)
  = {{f_calc}} m = {{f_mm}} mm
```

**Bước 2:** Kiểm tra

```
f_gh = L / {{L_limit}} = {{L_SI}} / {{L_limit}} = {{f_gh}} mm
η_f = f / f_gh = {{f_mm}} / {{f_gh}} = {{eta_f}} ≤ 1.0 ✓
```

---

## 6. BẢNG TỔNG HỢP KẾT QUẢ

### 6.1 Kiểm tra η

| Kiểm tra | Nội lực | Khả năng | η_tính_toán | Giới hạn | Trạng thái |
|----------|----------|-----------|--------------|-----------|------------|
| Chịu uốn | M_ed = {{M_ed}} kNm | M_c,Rd = {{M_cRd}} kNm | {{eta_M}} | ≤ 1.0 | {{status_M}} |
| Chịu cắt | V_ed = {{V_ed}} kN | V_pl,Rd = {{V_plRd}} kN | {{eta_V}} | ≤ 1.0 | {{status_V}} |
| Ổn định LTB | M_ed = {{M_ed}} kNm | M_b,Rd = {{M_bRd}} kNm | {{eta_LTB}} | ≤ 1.0 | {{status_LTB}} |
| Độ võng | f = {{f_mm}} mm | f_gh = {{f_gh}} mm | {{eta_f}} | ≤ 1.0 | {{status_f}} |

---

## 7. LIÊN KẾT

### 7.1 Liên kết tại {{connection_location}}

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Loại liên kết | {{connection_type}} | - |
| Bu lông | {{bolt_grade}} | - |
| Số bu lông | n = {{n_bolt}} | - |
| Lực cắt | V_ed = {{V_conn}} | kN |
| Mô men | M_ed = {{M_conn}} | kNm |

### 7.2 Kiểm tra bu lông

```
V_ed,bolt = V_conn / n = {{V_conn}} / {{n_bolt}} = {{V_bolt}} kN
η_V = V_bolt / V_Rd = {{V_bolt}} / {{V_Rd}} = {{eta_V_bolt}} ≤ 1.0 ✓
```

---

## 8. KẾT LUẬN

### 8.1 Kết quả kiểm tra

| Hạng mục | Kết quả |
|-----------|---------|
| Chịu uốn | {{result_M}} |
| Chịu cắt | {{result_V}} |
| Ổn định LTB | {{result_LTB}} |
| Độ võng | {{result_f}} |
| Liên kết | {{result_conn}} |

### 8.2 Đánh giá chung

{{conclusion}}

---

## 9. PHỤ LỤC

### 9.1 Đặc tính tiết diện {{section_name}}

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| A | {{A}} | cm² |
| I_x | {{Ix}} | cm⁴ |
| I_y | {{Iy}} | cm⁴ |
| W_x,pl | {{Wx_pl}} | cm³ |
| W_x,el | {{Wx_el}} | cm³ |
| W_y,pl | {{Wy_pl}} | cm³ |
| i_x | {{ix}} | cm |
| i_y | {{iy}} | cm |
| S_x | {{Sx}} | cm³ |

### 9.2 Đường cong LTB theo TCVN 5575:2024

| Đường cong | a | b | c | d |
|------------|---|---|---|---|
| Mặt cắt cán | - | - | - | - |
| Hình chữ I cán | 0.21 | 0.34 | 0.49 | 0.76 |
| Hình hộp | 0.21 | 0.34 | 0.49 | 0.76 |

---

## 10. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|--------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Kiểm tra | {{reviewer}} | | {{review_date}} |
| Duyệt | {{approver}} | | {{approve_date}} |

---

*Mẫu phụ lục tính toán kết cấu — Dầm thép*
*Generated by AI Structural Engineer — v1.0*
