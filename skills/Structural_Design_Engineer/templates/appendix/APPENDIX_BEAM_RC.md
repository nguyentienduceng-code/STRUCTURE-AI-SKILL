# PHỤ LỤC TÍNH TOÁN KẾT CẤU — DẦM BTCT
## Cấu kiện: {{beam_name}}

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị | Đơn vị |
|-----------|----------|---------|
| Công trình | {{project_name}} | - |
| Mã số | {{project_code}} | - |
| Giai đoạn | {{stage}} | - |
| Cấu kiện | {{beam_name}} | - |
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
| Chiều dài nhịp | {{L}} | mm |
| Chiều dày lớp bảo vệ | a = {{a}} | mm |
| Chiều cao tính toán | d = h - a = {{d}} | mm |

---

## 3. TẢI TRỌNG

### 3.1 Tĩnh tải

| Loại | Giá trị | Đơn vị | Ghi chú |
|------|----------|---------|----------|
| Tĩnh tải sàn | g_san = {{g_san}} | kN/m² | |
| Trọng lượng bản thân | g_bt = {{b}} × {{h}} × 25 / 10⁶ = {{g_bt}} | kN/m | |
| Tổng tĩnh tải | g = {{g_san}} × {{beam_width}} + {{g_bt}} = {{g_total}} | kN/m | |

### 3.2 Hoạt tải

| Loại | Giá trị | Đơn vị | Ghi chú |
|------|----------|---------|----------|
| Hoạt tải sử dụng | q = {{q}} | kN/m² | TCVN 2737:2023 |
| Hoạt tải lên dầm | q_ql = q × {{load_width}} = {{q_load}} | kN/m | |

### 3.3 Tổ hợp tải trọng (TCVN 2737:2023 Điều 4.3)

| Tổ hợp | Công thức | Hệ số |
|---------|-----------|-------|
| TH1 (ULS) | G + Q | γ_G = 1.0, γ_Q = 1.0 |
| TH2 (ULS) | G + Q | γ_G = 1.0, γ_Q = 0.9 |

---

## 4. SƠ ĐỒ KẾT CẤU

### 4.1 Sơ đồ tính

```
    q = {{q_total}} kN/m
    ┌─────────────────────────────────┐
────┤                                 ├──
   M₁         M₂                M₃    M₄
    └─────────────────────────────────┘
         L₁ = {{L1}}m      L₂ = {{L2}}m

Điều kiện biên: {{boundary_condition}}
```

### 4.2 Kích thước hình học

| Thông số | Giá trị |
|-----------|----------|
| Số nhịp | {{num_spans}} |
| Chiều dài nhịp 1 | {{L1}} m |
| Chiều dài nhịp 2 | {{L2}} m |
| Tiết diện | b × h = {{b}} × {{h}} mm |

---

## 5. NỘI LỰC

### 5.1 Tổ hợp tải trọng

| Tổ hợp | p = g + q = {{g_total}} + {{q_load}} = {{p}} kN/m |
|---------|---------------------------------------------------|

### 5.2 Nội lực tại các tiết diện đặc trưng

| Tiết diện | M (kNm) | V (kN) | Ghi chú |
|-----------|----------|---------|---------|
| Gối A (M₁⁻) | {{M_A}} | {{V_A}} | |
| Nhịp 1 (M₂⁺) | {{M_span1}} | 0 | M max |
| Gối B (M₂⁻) | {{M_B}} | {{V_B}} | |
| Nhịp 2 (M₃⁺) | {{M_span2}} | 0 | M max |
| Gối C (M₃⁻) | {{M_C}} | {{V_C}} | |

### 5.3 Kiểm tra nội lực

| Kiểm tra | Giá trị | Ghi chú |
|-----------|---------|---------|
| M_max | {{M_max}} kNm | |
| V_max | {{V_max}} kN | |

---

## 6. TÍNH TOÁN CHI TIẾT

### 6.1 Kiểm tra cốt thép chịu uốn

#### a) Tại gối B (M = {{M_B}} kNm) — Tiết diện chịu mô men âm (thép trên)

**Bước 1:** Giả thiết chiều cao vùng nén
```
α_m = 0.45 (giả thiết, điều kiện giới hạn)
a = α_m × d = 0.45 × {{d}} = {{a_calc}} mm
```

**Bước 2:** Tính cánh tay đòn nội lực
```
z = d - a/2 = {{d}} - {{a_calc}}/2 = {{z_calc}} mm
```

**Bước 3:** Tính diện tích cốt thép yêu cầu
```
A_s,req = M_ed / (f_y/γ_s × z)
        = {{M_B}} × 10⁶ / ({{fy}}/1.15 × {{z_calc}})
        = {{M_B}} × 10⁶ / ({{fy_over_gamma}})
        = {{As_req}} mm²
```

**Bước 4:** Kiểm tra chiều cao vùng nén
```
α = A_s × f_y / (b × f_c)
  = {{As_req}} × {{fy}} / ({{b}} × {{fc}})
  = {{alpha_calc}}
x = α × d / β₁
  = {{alpha_calc}} × {{d}} / 0.85
  = {{x_calc}} mm
a = β₁ × x = 0.85 × {{x_calc}} = {{a_check}} mm

Kiểm tra: |a_check - a_calc| / a_calc = {{a_diff}}% ≤ 5% ✓
```

**Bước 5:** Chọn cốt thép

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Thép yêu cầu | A_s,req = {{As_req}} | mm² |
| Thép chọn | {{rebar_top_choice}} | - |
| A_s,prov | {{As_prov}} | mm² |
| η_M = A_s,req / A_s,prov | {{eta_M}} | - |

#### b) Tại nhịp 1 (M = {{M_span1}} kNm) — Tiết diện chịu mô men dương (thép dưới)

**Bước 1:** Giả thiết chiều cao vùng nén
```
a = {{a_calc_nhip1}} mm
z = {{z_calc_nhip1}} mm
```

**Bước 2:** Tính A_s,req
```
A_s,req = {{M_span1}} × 10⁶ / ({{fy_over_gamma}})
        = {{As_req_nhip1}} mm²
```

**Bước 3:** Chọn cốt thép

| Thông số | Giá trị |
|-----------|----------|
| Thép yêu cầu | {{As_req_nhip1}} mm² |
| Thép chọn | {{rebar_bot_choice}} |
| A_s,prov | {{As_prov_nhip1}} mm² |
| η_M | {{eta_M_nhip1}} |

### 6.2 Kiểm tra cốt thép chịu cắt

#### a) Tại gối B (V = {{V_B}} kN)

**Bước 1:** Kiểm tra điều kiện nén xiên
```
V_max = φ × 0.3 × f_c × b × d
      = 0.9 × 0.3 × {{fc}} × {{b}} × {{d}} / 1000
      = {{V_max}} kN

Kiểm tra: V_ed = {{V_B}} kN ≤ V_max = {{V_max}} kN ✓
```

**Bước 2:** Kiểm tra cốt đai yêu cầu
```
V_sw = V_ed - V_c = {{V_B}} - {{V_c}} = {{V_sw_calc}} kN
```

**Bước 3:** Chọn cốt đai

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Đường kính đai | φ{{stirrup_dia}} | mm |
| Số nhánh | 2 | nhánh |
| A_sw = n × A_φ | 2 × {{A_stirrup}} = {{A_sw}} | mm² |
| Bước đai vùng 1 | s₁ = {{s1}} | mm |
| Bước đai vùng 2 | s₂ = {{s2}} | mm |

**Bước 4:** Kiểm tra khả năng chịu cắt
```
V_sw1 = A_sw × f_yw × d / s₁
      = {{A_sw}} × {{fyw}} × {{d}} / {{s1}} / 1000
      = {{V_sw1}} kN

η_V = V_ed / (V_c + V_sw1)
    = {{V_B}} / ({{V_c}} + {{V_sw1}})
    = {{eta_V}} < 1.0 ✓
```

### 6.3 Kiểm tra độ võng (SLS)

**Bước 1:** Tính độ cứng
```
I = b × h³ / 12 = {{b}} × {{h}}³ / 12 = {{I_calc}} mm⁴
E × I = {{Ec}} × {{I_calc}} = {{EI_calc}} N·mm²
```

**Bước 2:** Tính độ võng do tải trọng ngắn hạn
```
f₁ = 5 × p × L⁴ / (384 × E × I)
    = 5 × {{p}} × {{L_max}}⁴ / (384 × {{Ec}} × {{I_calc}}) × 10⁶
    = {{f1}} mm
```

**Bước 2:** Tính độ võng do tải trọng dài hạn (ψ₂ × p)
```
ψ₂ = 0.45 (hệ số dài hạn)
f₂ = 5 × ψ₂ × p × L⁴ / (384 × E × I)
    = {{f2}} mm
```

**Bước 3:** Độ võng tổng cộng
```
f = f₁ + f₂ = {{f1}} + {{f2}} = {{f_total}} mm
f_gh = L / {{span_limit}} = {{L_max}} / {{span_limit}} = {{f_limit}} mm
η_f = f / f_gh = {{f_total}} / {{f_limit}} = {{eta_f}} < 1.0 ✓
```

---

## 7. BẢNG TỔNG HỢP KẾT QUẢ

### 7.1 Cốt thép đã chọn

| Vị trí | Thép chịu lực | A_s,prov (mm²) | Thép đai |
|---------|----------------|----------------|----------|
| Gối A | {{rebar_top_A}} | {{As_A}} | {{stirrup_A}} |
| Nhịp 1 | {{rebar_bot_1}} | {{As_1}} | {{stirrup_1}} |
| Gối B | {{rebar_top_B}} | {{As_B}} | {{stirrup_B}} |
| Nhịp 2 | {{rebar_bot_2}} | {{As_2}} | {{stirrup_2}} |
| Gối C | {{rebar_top_C}} | {{As_C}} | {{stirrup_C}} |

### 7.2 Kiểm tra η (Hệ số sử dụng)

| Kiểm tra | Vị trí | η_yêu_cầu | η_tính_toán | Trạng thái |
|----------|--------|-------------|--------------|------------|
| Chịu uốn | Gối A | ≤ 1.0 | {{eta_M_A}} | {{status_M_A}} |
| Chịu uốn | Nhịp 1 | ≤ 1.0 | {{eta_M_1}} | {{status_M_1}} |
| Chịu uốn | Gối B | ≤ 1.0 | {{eta_M_B}} | {{status_M_B}} |
| Chịu cắt | Gối A | ≤ 1.0 | {{eta_V_A}} | {{status_V_A}} |
| Chịu cắt | Gối B | ≤ 1.0 | {{eta_V_B}} | {{status_V_B}} |
| Độ võng | Nhịp 1 | ≤ 1.0 | {{eta_f_1}} | {{status_f_1}} |
| Độ võng | Nhịp 2 | ≤ 1.0 | {{eta_f_2}} | {{status_f_2}} |

---

## 8. KẾT LUẬN

### 8.1 Kết quả kiểm tra

| Hạng mục | Kết quả |
|-----------|---------|
| Chịu uốn | {{result_M}} |
| Chịu cắt | {{result_V}} |
| Độ võng | {{result_f}} |
| Hàm lượng thép | {{result_rho}} |

### 8.2 Đánh giá chung

{{conclusion}}

---

## 9. PHỤ LỤC

### 9.1 Đặc tính cốt thép (TCVN 1651-2:2018)

| Đường kính | Diện tích (mm²) | Khối lượng (kg/m) | Chu vi (mm) |
|------------|------------------|-------------------|-------------|
| φ6 | 28.3 | 0.222 | 18.8 |
| φ8 | 50.3 | 0.395 | 25.1 |
| φ10 | 78.5 | 0.617 | 31.4 |
| φ12 | 113.1 | 0.888 | 37.7 |
| φ14 | 153.9 | 1.208 | 44.0 |
| φ16 | 201.1 | 1.578 | 50.3 |
| φ18 | 254.5 | 1.998 | 56.5 |
| φ20 | 314.2 | 2.466 | 62.8 |
| φ22 | 380.1 | 2.984 | 69.1 |
| φ25 | 490.9 | 3.853 | 78.5 |
| φ28 | 615.8 | 4.834 | 87.9 |
| φ30 | 706.9 | 5.549 | 94.2 |
| φ32 | 804.2 | 6.313 | 100.5 |

### 9.2 Hệ số β₁ theo TCVN 5574:2018

| f_c (MPa) | ≤ C50 | C55 | C60 | C65 | C70 | C75 | C80 |
|-----------|-------|-----|-----|-----|-----|-----|-----|
| β₁ | 0.85 | 0.83 | 0.81 | 0.79 | 0.77 | 0.75 | 0.73 |

### 9.3 Hệ số dài hạn ψ₂ (TCVN 5574:2018)

| Loại tải trọng | ψ₂ |
|----------------|-----|
| Tĩnh tải | 0.45 |
| Hoạt tải | 0.45 |
| Tải trọng gió | 0.20 |
| Tải trọng nhiệt | 0.30 |

---

## 10. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|--------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Kiểm tra | {{reviewer}} | | {{review_date}} |
| Duyệt | {{approver}} | | {{approve_date}} |

---

*Mẫu phụ lục tính toán kết cấu — Dầm BTCT*
*Generated by AI Structural Engineer — v1.0*
