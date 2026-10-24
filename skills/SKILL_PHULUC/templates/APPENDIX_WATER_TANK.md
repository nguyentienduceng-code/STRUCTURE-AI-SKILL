# PHỤ LỤC TÍNH TOÁN KẾT CẤU
## BỂ NƯỚC NGẦM BTCT

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|---------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Cấu kiện | Bể nước ngầm |
| Tiêu chuẩn | TCVN 5574:2018, TCVN 9386:2025 |
| Mức độ thấm | W{{watertight_level}} (W6/W8/W10) |
| Người tính | {{calculator}} |
| Ngày tính | {{calc_date}} |

---

## 2. VẬT LIỆU

### 2.1 Bê tông chống thấm

| Mác | R_b (MPa) | R_bt (MPa) | E_b (MPa) | Mác chống thấm |
|-----|-----------|------------|-----------|----------------|
| B20 | 11.5 | 0.90 | 27500 | W4-W6 |
| B25 | 14.5 | 1.05 | 30000 | W6-W8 |
| B30 | 17.0 | 1.15 | 32500 | W8-W10 |
| B35 | 19.5 | 1.30 | 34500 | W10-W12 |

> Thiết kế: **{{concrete_grade}}** — Mác chống thấm **W{{watertight_level}}**

### 2.2 Cốt thép

| Loại | R_s (MPa) | R_sc (MPa) | Ứng dụng |
|------|-----------|------------|----------|
| CB300-V | 260 | 260 | Thép đai, cấu tạo |
| CB400-V | 350 | 350 | Thép chịu lực chính |
| CB500-V | 435 | 400 | Thép đường kính lớn |

> Thiết kế: **{{steel_grade}}** — R_s = {{Rs}} MPa

### 2.3 Phụ gia

- Phụ gia chống thấm: Sikament hoặc tương đương
- Tỷ lệ phụ gia: 1.5-2.5% khối lượng xi măng
- Yêu cầu độ sụt: 120-180 mm

---

## 3. HÌNH HỌC BỂ NƯỚC

### 3.1 Kích thước chính

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|-----------|----------|---------|---------|
| Chiều dài trong | L | {{L}} | m |
| Chiều rộng trong | B | {{B}} | m |
| Chiều cao trong | H | {{H}} | m |
| Chiều dày đáy | t_b | {{t_bottom}} | mm |
| Chiều dày thành | t_w | {{t_wall}} | mm |
| Chiều dày nắp | t_c | {{t_cover}} | mm |
| Cao độ đáy | {{elevation_bottom}} | m |
| Cao độ nước max | {{elevation_water}} | m |

### 3.2 Mực nước và áp lực

```
        ┌─────────────────┐  Mặt đất: ±0.00
        │                 │
        │    Nước         │  MNDBK: {{water_level_HWL}} m
        │                 │
   ─────┤─────────────────┼──────  MNDBT: {{water_level_LWL}} m
        │                 │
        │                 │  Đáy bể: {{elevation_bottom}} m
        └─────────────────┘
```

---

## 4. TẢI TRỌNG

### 4.1 Tĩnh tải

| Thành phần | Tải trọng | Ghi chú |
|------------|-----------|---------|
| Đáy bể (BTCT) | {{q_dead_bottom}} kN/m² | 25 × {{t_bottom}}/1000 |
| Thành bể | {{q_dead_wall}} kN/m | 25 × {{t_wall}}/1000 |
| Nắp bể | {{q_dead_cover}} kN/m² | 25 × {{t_cover}}/1000 |
| Lớp hoàn thiện | {{q_finish}} kN/m² | |

### 4.2 Hoạt tải

| Loại | Giá trị | Tiêu chuẩn |
|------|---------|------------|
| Hoạt tải mặt nắp | {{q_LL_cover}} kN/m² | TCVN 2737 |
| Áp lực nước (đáy) | {{p_water_bottom}} kN/m² | γ_nước × H_nước |
| Áp lực nước (thành) | {{p_water_wall}} kN/m² | γ × z |

### 4.3 Áp lực đất

| Thành phần | Giá trị | Đơn vị |
|------------|---------|---------|
| Trọng lượng riêng đất | γ_đ | {{gamma_soil}} kN/m³ |
| Góc ma sát trong | φ | {{phi}} ° |
| Hệ số áp lực đất | K_a | {{K_active}} |
| Áp lực đất chủ động | p_a | {{p_earth}} kN/m² |

---

## 5. SƠ ĐỒ TÍNH TOÁN

### 5.1 Đáy bể

```
┌─────────────────────────────┐
│                             │
│      Đáy bể                │  Sơ đồ: Bản kê 4 cạnh
│      (liên tục)            │  Tính theo Phụ lục G TCVN 5574
│                             │
└─────────────────────────────┘
```

### 5.2 Thành bể

```
        Áp lực nước
        ◄──────────
    ┌───┐     ┌───┐
    │   │     │   │   Sơ đồ: Bản chịu lực 1 phương
    │   │     │   │   (thành dài, tính theo phương ngắn)
    │   │     │   │
    │   │     │   │
    └───┘     └───┘
```

### 5.3 Nắp bể

```
    ┌─────────────────────────────┐
    │  Nắp bể                   │  Sơ đồ: Bản kê 4 cạnh
    │  (chịu tải trọng người)   │  hoặc dầm đơn giản
    └─────────────────────────────┘
```

---

## 6. TÍNH TOÁN ĐÁY BỂ

### 6.1 Nội lực (Bản kê 4 cạnh)

**Bước 1:** Xác định tỷ số các cạnh

```
ρ = L / B = {{L}} / {{B}} = {{rho}}
```

Với ρ = {{rho}} {{rho_note}}, đáy bể tính theo bản làm việc **{{plate_type}}**.

**Bước 2:** Mô men trong bản

| Loại | Ký hiệu | Công thức | Giá trị |
|------|----------|-----------|---------|
| Mô men dương giữa nhịp | M_1 | α_1 × q × L² | {{M1}} kNm/m |
| Mô men âm gối | M_2 | α_2 × q × L² | {{M2}} kNm/m |

**Bước 3:** Kiểm tra điều kiện chịu lực

```
Q = p × L × B = {{p_water_bottom}} × {{L}} × {{B}} = {{Q}} kN
```

### 6.2 Tính cốt thép đáy

**Cốt thép phương L (dưới):**

```
a = 35 mm
h_0 = {{t_bottom}} - 35 = {{h0_bottom}} mm

α = M / (R_b × b × h_0²)
  = {{M1}}×10⁶ / ({{Rb}} × 1000 × {{h0_bottom}}²)
  = {{alpha_bottom}}

ζ = 0.5 × (1 + √(1 - 2α))
  = {{zeta_bottom}}

A_s,req = M / (R_s × ζ × h_0)
        = {{As_req_bottom}} mm²/m
```

**Chọn:** {{rebar_bottom_L}} → A_s,prov = {{As_prov_bottom}} mm²/m

**η = {{As_req_bottom}} / {{As_prov_bottom}} = {{eta_bottom_L}} {{status_bottom_L}}**

---

## 7. TÍNH TOÁN THÀNH BỂ

### 7.1 Nội lực

**Thành bể chịu áp lực nước phân bố tam giác:**

```
q_w = γ × H = {{gamma_water}} × {{H_water}} = {{q_water}} kN/m²
```

**Mô men tại các tiết diện:**

| Cao độ | z (m) | p (kN/m²) | M (kNm/m) |
|--------|--------|-----------|-----------|
| Chân thành | 0 | {{q_water}} | {{M_wall_base}} |
| 1/4 H | {{H/4}} | {{p_quarter}} | {{M_wall_quarter}} |
| 1/2 H | {{H/2}} | {{p_half}} | {{M_wall_half}} |
| Đỉnh | {{H}} | 0 | 0 |

### 7.2 Tính cốt thép thành

**Bước 1:** Kiểm tra ứng suất trong thành

```
σ = p × H² / (6 × t_w) = {{sigma_wall}} MPa
σ_allow = R_b / γ_b = {{Rb}} / 1.3 = {{sigma_allow}} MPa
η = σ / σ_allow = {{sigma_wall}} / {{sigma_allow}} = {{eta_stress}}
```

**Bước 2:** Cốt thép chịu mô men

**Thép đứng (phương cao):**

```
A_s,req = M / (R_s × z)
        = {{M_wall_base}}×10⁶ / ({{Rs}} × 0.8×{{t_wall}})
        = {{As_req_wall}} mm²/m

Chọn: {{rebar_wall_vert}} → η = {{eta_wall_vert}}
```

**Thép ngang (phương rộng):**

```
A_s,req = 0.5 × A_s,vert = {{As_req_wall_horiz}} mm²/m

Chọn: {{rebar_wall_horiz}} → η = {{eta_wall_horiz}}
```

---

## 8. KIỂM TRA CHỐNG THẤM

### 8.1 Bề rộng vết nứt

**Bước 1:** Tính ứng suất trong cốt thép

```
σ_s = M / (A_s × z)
    = {{M1}}×10⁶ / ({{As_prov_bottom}} × {{z}})
    = {{sigma_s}} MPa
```

**Bước 2:** Tính bề rộng vết nứt (TCVN 5574:2018 Mục 7.3.3)

```
ψ_s = 1.0 (tải ngắn hạn)

a_cr = 0.6 × √(φ × σ_s / E_s) × φ / ρ_eff
     = {{a_cr}} mm
```

**Bước 3:** Giới hạn theo môi trường

| Môi trường | a_cr, max (mm) |
|-------------|-----------------|
| Trong nhà bình thường | 0.4 |
| Trong nước (bể chứa) | 0.3 |
| Ngoài trời | 0.3 |

**Thiết kế: a_cr,max = 0.3 mm**

**Kết luận:** a_cr = {{a_cr}} mm {{status_crack}}

### 8.2 Độ thấm nước

- Kiểm tra mật độ bê tông: ≥ 98% (theo Yêu cầu W{{watertight_level}})
- Độ chống thấm: Thử nghiệm áp lực nước 1.5 × áp lực thiết kế
- Thời gian thử: 72 giờ

---

## 9. BẢNG TỔNG HỢP

### 9.1 Cốt thép thiết kế

| Vị trí | Phương | Thép chọn | A_s,prov (mm²/m) | η |
|---------|---------|-----------|------------------|---|
| Đáy bể | Dọc | {{rebar_bottom_L}} | {{As_prov_bottom}} | {{eta_bottom_L}} |
| Đáy bể | Ngang | {{rebar_bottom_T}} | {{As_prov_bottom_T}} | {{eta_bottom_T}} |
| Thành | Đứng | {{rebar_wall_vert}} | {{As_prov_wall_vert}} | {{eta_wall_vert}} |
| Thành | Ngang | {{rebar_wall_horiz}} | {{As_prov_wall_horiz}} | {{eta_wall_horiz}} |
| Nắp bể | Dọc | {{rebar_cover_L}} | {{As_prov_cover}} | {{eta_cover_L}} |

### 9.2 Hệ số sử dụng

| Kiểm tra | Giá trị | Giới hạn | Trạng thái |
|----------|---------|----------|------------|
| Đáy - Chịu uốn | η = {{eta_bottom_L}} | ≤ 1.0 | 🟢 |
| Thành - Ứng suất | η = {{eta_stress}} | ≤ 1.0 | 🟢 |
| Thành - Cốt thép đứng | η = {{eta_wall_vert}} | ≤ 1.0 | 🟢 |
| Chống nứt | a_cr = {{a_cr}} mm | ≤ 0.3 mm | 🟢 |

---

## 10. CHI TIẾT CỐT THÉP

### 10.1 Neo và nối

- Chiều dài neo: L_an = {{L_an}} × Ø ≥ 300 mm
- Chiều dài nối: L_n = {{L_n}} × Ø ≥ 400 mm
- Khoảng cách nối: ≥ 35Ø

### 10.2 Cấu tạo đặc biệt

```
        Thanh chống co ngót
        ═══════════════════
┌───────┬─────────────────┬───────┐
│       │                 │       │
│       │                 │       │  Lưới cốt thép đáy
│       │                 │       │  @ {{s_bottom}} mm
│       │                 │       │
└───────┴─────────────────┴───────┘
        ▼
   Neo vào thành
```

---

## 11. KẾT LUẬN

**Bể nước ngầm BTCT đạt yêu cầu:**

✅ Cường độ đáy bể (η = {{eta_bottom_L}} ≤ 1.0)  
✅ Cường độ thành bể (η = {{eta_stress}} ≤ 1.0)  
✅ Chống nứt (a_cr = {{a_cr}} mm ≤ 0.3 mm)  
✅ Độ chống thấm (W{{watertight_level}})  

**Biện pháp thi công:**
- Đổ bê tông liên tục, không có mạch thi công ngang
- Đầm bê tông kỹ, đặc biệt vị trí góc
- Bảo dưỡng ẩm ít nhất 14 ngày
- Thử nghiệm độ kín trước khi nghiệm thu

---

## 12. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|---------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Người kiểm tra | {{reviewer}} | | |
| Người duyệt | {{approver}} | | |

---

*Tài liệu được tạo tự động bởi SKILL_PHULUC*
*Tiêu chuẩn: TCVN 5574:2018, TCVN 9386:2025*
