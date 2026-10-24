# PHỤ LỤC TÍNH TOÁN KẾT CẤU
## TƯỜNG CHẮN ĐẤT BTCT

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|---------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Cấu kiện | Tường chắn đất |
| Tiêu chuẩn | TCVN 5574:2018, TCVN 9386:2025 |
| Người tính | {{calculator}} |
| Ngày tính | {{calc_date}} |

---

## 2. VẬT LIỆU

### 2.1 Bê tông

| Mác | R_b (MPa) | R_bt (MPa) | E_b (MPa) |
|-----|-----------|------------|-----------|
| B20 | 11.5 | 0.90 | 27500 |
| B25 | 14.5 | 1.05 | 30000 |
| B30 | 17.0 | 1.15 | 32500 |
| B35 | 19.5 | 1.30 | 34500 |

> Thiết kế: **{{concrete_grade}}** — R_b = {{Rb}} MPa, R_bt = {{Rbt}} MPa

### 2.2 Cốt thép

| Loại | R_s (MPa) | Ứng dụng |
|------|-----------|----------|
| CB300-V | 260 | Thép đai, cấu tạo |
| CB400-V | 350 | Thép chịu lực |
| CB500-V | 435 | Thép thanh lớn |

> Thiết kế: **{{steel_grade}}** — R_s = {{Rs}} MPa

### 2.3 Lớp bảo vệ

- Mặt trong (đất): a = 40 mm
- Mặt ngoài (không khí): a = 30 mm

---

## 3. HÌNH HỌC TƯỜNG CHẮN

### 3.1 Kích thước chính

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|-----------|----------|---------|---------|
| Chiều cao tường | H | {{H}} | m |
| Chiều dày thân | t | {{t}} | mm |
| Chiều rộng đế | B | {{B}} | m |
| Chiều dày đế | h_b | {{h_base}} | mm |
| Chiều rộng cánh mũi | B_m | {{B_toe}} | m |
| Chiều rộng cánh gót | B_g | {{B_heel}} | m |
| Độ nghiêng đỉnh | — | {{top_incline}} | ° |

### 3.2 Mặt cắt ngang

```
                    ▲
                   /│\  Đỉnh tường
                  / │ \
                 /  │  \  Thân tường
                /   │   \
               /    │    \
              /     │     \
─────────────/──────┴──────\─────────────── Mặt đất
             │    │   │     │
             │    │   │     │  Cánh gót
    Cánh mũi│    │   │     │
             │    │   │     │
    ═════════╧════╧═══╧═════╧══════════════  Đáy móng
    ◄── B_m ──►◄── t ──►◄── B_g ──►
    ◄────────── B = {{B}} m ──────────►
```

---

## 4. TẢI TRỌNG VÀ ÁP LỰC ĐẤT

### 4.1 Đặc tính đất

| Thông số | Giá trị | Đơn vị |
|----------|---------|---------|
| Trọng lượng riêng đất | γ_đ | {{gamma_soil}} kN/m³ |
| Góc ma sát trong | φ | {{phi}} ° |
| Lực dính | c | {{c}} kPa |
| Hệ số áp lực chủ động | K_a | {{K_a}} |
| Hệ số áp lực bị động | K_p | {{K_p}} |
| Hệ số áp lực đất tĩnh | K_0 | {{K_0}} |

### 4.2 Tải trọng bề mặt

| Loại | Giá trị | Ghi chú |
|------|---------|---------|
| Hoạt tải phía trên | q_s | {{q_surface}} kN/m² |
| Hoạt tải tập trung | P | {{P_point}} kN |

### 4.3 Áp lực đất lên tường

**Áp lực chủ động (phía sau tường):**

```
p_a = K_a × γ × z + K_a × q_s
    = {{K_a}} × {{gamma_soil}} × z + {{K_a}} × {{q_surface}}
```

**Phân bố áp lực:**

| Cao độ | z (m) | p_a (kN/m²) |
|--------|--------|--------------|
| Đỉnh (z=0) | 0 | {{p_a_top}} |
| Mặt đất (z=0) | 0 | {{p_a_surface}} |
| Chân tường (z=H) | {{H}} | {{p_a_base}} |

**Hợp lực áp lực chủ động:**

```
P_a = ½ × (p_a,top + p_a,base) × H
    = ½ × ({{p_a_top}} + {{p_a_base}}) × {{H}}
    = {{P_a}} kN/m

Điểm đặt: y = H/3 × (2×p_a,base + p_a,top) / (p_a,base + p_a,top) = {{y_Pa}} m
```

---

## 5. KIỂM TRA ỔN ĐỊNH TƯỜNG

### 5.1 Kiểm tra lật

**Bước 1:** Tính trọng lượng tường

```
W_tường = γ_bt × V_tường = {{gamma_concrete}} × {{V_wall}} = {{W_wall}} kN/m
W_đế = γ_bt × V_đế = {{gamma_concrete}} × {{V_base}} = {{W_base}} kN/m
W_đất_gót = γ_đ × V_đất_gót = {{gamma_soil}} × {{V_soil_heel}} = {{W_soil_heel}} kN/m
W_tổng = {{W_wall}} + {{W_base}} + {{W_soil_heel}} = {{W_total}} kN/m
```

**Bước 2:** Mô men chống lật

```
M_chống = Σ W_i × x_i
        = {{W_wall}} × {{x_wall}} + {{W_base}} × {{x_base}} + {{W_soil_heel}} × {{x_soil_heel}}
        = {{M_resist}} kNm/m
```

**Bước 3:** Mô men gây lật

```
M_lật = P_a × y_Pa + M_đất
       = {{P_a}} × {{y_Pa}} + {{M_soil}}
       = {{M_overturn}} kNm/m
```

**Bước 4:** Hệ số an toàn lật

```
FS_lật = M_chống / M_lật
        = {{M_resist}} / {{M_overturn}}
        = {{FS_overturning}} ≥ 1.5
```

→ **{{status_overturning}}**

### 5.2 Kiểm tra trượt

**Bước 1:** Lực chống trượt

```
F_chống = W_tổng × tan(δ) + c' × B
        = {{W_total}} × tan({{delta}}) + {{c_prime}} × {{B}}
        = {{F_resist}} kN/m
```

**Bước 2:** Lực gây trượt

```
F_gây = P_a × cos(α) + P_thẳng_đứng
       = {{P_a}} × {{cos_alpha}} + {{V_additional}}
       = {{F_drive}} kN/m
```

**Bước 3:** Hệ số an toàn trượt

```
FS_trượt = F_chống / F_gây
          = {{F_resist}} / {{F_drive}}
          = {{FS_sliding}} ≥ 1.3
```

→ **{{status_sliding}}**

### 5.3 Kiểm tra sức kháng nền

**Bước 1:** Tải trọng tính đổi

```
e = (M_resist - M_overturn) / W_total
  = ({{M_resist}} - {{M_overturn}}) / {{W_total}}
  = {{eccentricity}} m

Điều kiện: |e| ≤ B/6 = {{B}}/6 = {{e_allow}} m
```

**Bước 2:** Ứng suất dưới đế

```
σ_max = W_total / B × (1 + 6e/B)
      = {{W_total}} / {{B}} × (1 + 6 × {{eccentricity}} / {{B}})
      = {{sigma_max}} kPa

σ_min = W_total / B × (1 - 6e/B)
      = {{sigma_min}} kPa
```

**Bước 3:** So sánh với sức kháng nền

```
R_ft = {{R_ft}} kPa
η = σ_max / R_ft = {{sigma_max}} / {{R_ft}} = {{eta_foundation}}
```

→ **{{status_foundation}}**

---

## 6. TÍNH TOÁN CỐT THÉP

### 6.1 Thiết kế thân tường

**Sơ đồ tính:** Dầm công-xon ngàm tại chân tường

**Bước 1:** Mô men tại các tiết diện

| Cao độ | z (m) | M (kNm/m) | V (kN/m) |
|--------|--------|-----------|-----------|
| Chân tường (z=H) | {{H}} | {{M_base}} | {{V_base}} |
| 3/4 H | {{H*0.75}} | {{M_3_4}} | {{V_3_4}} |
| 1/2 H | {{H*0.5}} | {{M_1_2}} | {{V_1_2}} |
| 1/4 H | {{H*0.25}} | {{M_1_4}} | {{V_1_4}} |
| Đỉnh (z=0) | 0 | 0 | {{V_top}} |

**Bước 2:** Thiết kế cốt thép chịu mô men

**Tại chân tường (mặt trong - phía đất):**

```
M = {{M_base}} kNm/m
a = 40 mm
h_0 = {{t}} - 40 = {{h0_wall}} mm

α = M / (R_b × b × h_0²)
  = {{M_base}}×10⁶ / ({{Rb}} × 1000 × {{h0_wall}}²)
  = {{alpha}}

ζ = 0.5 × (1 + √(1 - 2α)) = {{zeta}}
A_s,req = M / (R_s × ζ × h_0)
        = {{As_req_wall}} mm²/m
```

**Chọn cốt thép:** {{rebar_wall_main}}

```
η = {{As_req_wall}} / {{As_prov_wall}} = {{eta_wall}}
```

→ **{{status_wall}}**

**Bước 3:** Kiểm tra cường độ trên tiết diện nghiêng

```
Q_b = 0.6 × R_bt × b × h_0
    = {{Q_b}} kN/m

V_max = {{V_base}} kN/m
η = {{V_base}} / {{Q_b}} = {{eta_shear}}
```

→ **{{status_shear}}**

### 6.2 Thiết kế đế móng

**Đế cánh mũi (mặt dưới - chịu phản lực đất):**

```
M_tại_mũi = σ_max × B_m² / 2
          = {{sigma_max}} × {{B_toe}}² / 2
          = {{M_toe}} kNm/m

A_s,req = {{M_toe}}×10⁶ / ({{Rs}} × 0.9 × {{h0_base}})
        = {{As_req_toe}} mm²/m

Chọn: {{rebar_toe}} → η = {{eta_toe}}
```

**Đế cánh gót (mặt trên - chịu áp lực đất):**

```
M_tại_gót = P_đất_gót × tay_đòn
           = {{P_soil_heel}} × {{arm_heel}}
           = {{M_heel}} kNm/m

A_s,req = {{M_heel}}×10⁶ / ({{Rs}} × 0.9 × {{h0_base}})
        = {{As_req_heel}} mm²/m

Chọn: {{rebar_heel}} → η = {{eta_heel}}
```

---

## 7. KIỂM TRA VÕNG VÀ NỨT

### 7.1 Kiểm tra võng

```
f = {{f}} mm
f_gh = H / 250 = {{H}}/250 = {{f_allow}} mm
η = {{f}} / {{f_allow}} = {{eta_deflection}}
```

→ **{{status_deflection}}**

### 7.2 Kiểm tra bề rộng vết nứt

```
a_cr = 0.6 × √(φ × σ_s / E_s) × φ / ρ_eff
     = {{a_cr}} mm
a_cr,gh = 0.3 mm (môi trường ngoài trời)
η = {{a_cr}} / 0.3 = {{eta_crack}}
```

→ **{{status_crack}}**

---

## 8. BẢNG TỔNG HỢP

### 8.1 Cốt thép thiết kế

| Vị trí | Loại | Thép chọn | A_s (mm²/m) | η |
|---------|------|-----------|-------------|---|
| Thân tường - Mặt trong | Chịu lực | {{rebar_wall_main}} | {{As_prov_wall}} | {{eta_wall}} |
| Thân tường - Mặt ngoài | Cấu tạo | {{rebar_wall_temp}} | {{As_prov_temp}} | — |
| Đế - Cánh mũi | Chịu lực | {{rebar_toe}} | {{As_prov_toe}} | {{eta_toe}} |
| Đế - Cánh gót | Chịu lực | {{rebar_heel}} | {{As_prov_heel}} | {{eta_heel}} |

### 8.2 Hệ số sử dụng

| Kiểm tra | Giá trị | Giới hạn | Trạng thái |
|----------|---------|----------|------------|
| Chống lật | FS = {{FS_overturning}} | ≥ 1.5 | 🟢 {{status_overturning}} |
| Chống trượt | FS = {{FS_sliding}} | ≥ 1.3 | 🟢 {{status_sliding}} |
| Sức kháng nền | η = {{eta_foundation}} | ≤ 1.0 | 🟢 {{status_foundation}} |
| Chịu uốn thân | η = {{eta_wall}} | ≤ 1.0 | 🟢 {{status_wall}} |
| Chịu cắt | η = {{eta_shear}} | ≤ 1.0 | 🟢 {{status_shear}} |
| Đế mũi | η = {{eta_toe}} | ≤ 1.0 | 🟢 |
| Đế gót | η = {{eta_heel}} | ≤ 1.0 | 🟢 |
| Võng | η = {{eta_deflection}} | ≤ 1.0 | 🟢 {{status_deflection}} |
| Nứt | η = {{eta_crack}} | ≤ 1.0 | 🟢 {{status_crack}} |

---

## 9. CHI TIẾT CỐT THÉP

### 9.1 Neo cốt thép

```
Thân tường - Mặt trong:
L_neo = {{L_neo_main}} × Ø ≥ {{L_neo_min}} mm
      = {{L_neo_required}} mm
```

### 9.2 Cấu tạo

```
        Thép cấu tạo
        ═══════════════════
┌───────┬─────────────────┬───────┐
│       │                 │       │
│       │     Thân tường  │       │
│       │                 │       │
│       │                 │       │
└───────┴─────────────────┴───────┘
        ▲
   Neo vào đế ≥ 40Ø
```

---

## 10. KẾT LUẬN

**Tường chắn đất BTCT đạt yêu cầu:**

✅ Chống lật (FS = {{FS_overturning}} ≥ 1.5)  
✅ Chống trượt (FS = {{FS_sliding}} ≥ 1.3)  
✅ Sức kháng nền (η = {{eta_foundation}} ≤ 1.0)  
✅ Cường độ thân tường (η = {{eta_wall}} ≤ 1.0)  
✅ Cường độ đế móng (η = {{eta_toe}} ≤ 1.0)  
✅ Võng (η = {{eta_deflection}} ≤ 1.0)  
✅ Chống nứt (η = {{eta_crack}} ≤ 1.0)  

---

## 11. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|---------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Người kiểm tra | {{reviewer}} | | |
| Người duyệt | {{approver}} | | |

---

*Tài liệu được tạo tự động bởi SKILL_PHULUC*
*Tiêu chuẩn: TCVN 5574:2018, TCVN 9386:2025*
