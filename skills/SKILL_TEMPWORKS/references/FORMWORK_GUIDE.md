# FORMWORK_GUIDE.md — Hướng dẫn Thiết kế Cốp pha

> **Phạm vi:** Thiết kế cốp pha sàn, tường, coffers
> **Tiêu chuẩn:** ACI 347-04, TCVN 5575:2024

---

## 1. Tải trọng Thiết kế Cốp pha

### 1.1 Tải trọng Thẳng đứng

| Loại tải | Ký hiệu | Giá trị | Đơn vị |
|-----------|----------|---------|--------|
| Bê tông tươi | q_bt | γ_bt × độ dày sàn | kN/m² |
| Cốt thép + phụ kiện | q_st | ~0.5 - 1.0 | kN/m² |
| Tải thi công | q_tc | 1.5 (người + dụng cụ) | kN/m² |
| Áp lực bê tông tươi | p_bt | γ_bt × chiều cao đổ | kN/m² |

### 1.2 Hệ số Tải trọng (TCVN 2737:2023)

| Loại tải | Hệ số γ |
|-----------|----------|
| Tĩnh tải (bê tông, cốp pha) | 1.2 |
| Hoạt tải thi công | 1.5 |

### 1.3 Tổ hợp Tải trọng

```
q_design = 1.2 × (q_bt + q_st) + 1.5 × q_tc
```

---

## 2. Thiết kế Panel Cốp pha

### 2.1 Panel Gỗ

**Kiểm tra uốn:**
```
σ = M / W ≤ f_m
```
- M = moment tính toán (kNm)
- W = moment chống uốn = b × h² / 6 (cm³)
- f_m = cường độ chịu uốn thiết kế (~12 MPa cho gỗ ván)

**Kiểm tra cắt:**
```
τ = V × S / (I × b) ≤ f_v
```
- f_v = cường độ chịu cắt (~1.5 MPa)

**Kiểm tra độ võng:**
```
δ = 5 × q × L⁴ / (384 × E × I) ≤ L/270
```

### 2.2 Panel Thép (Giác múi)

**Thép tấm (Mild steel):**
| Thông số | Giá trị |
|-----------|----------|
| f_y | 250 MPa |
| γ_M0 | 1.05 |
| f_y/γ_M0 | 238 MPa |

**Moment chống uốn tiết diện đã khoét lỗ:**
```
Z_eff = (b × t² / 6) - (Σ a × d² / (2 × s))
```
- b = chiều rộng bản
- t = chiều dày
- a = tổng chiều rộng lỗ trên 1 nhịp
- d = khoảng cách lỗ đến mép
- s = khoảng cách lỗ

---

## 3. Thiết kế Đà đỡ (Joist, Soldier Beam)

### 3.1 Đà gỗ

**Nhịp đơn giản:**
```
M_max = q × L² / 8
V_max = q × L / 2
```

**Tải trọng đầu mút:**
```
P = q × S (S = khoảng cách đà)
```

### 3.2 Đà thép (I, H)

**Kiểm tra ứng suất:**
```
σ = M / W_x + V × Q / (I × t) ≤ f_y / γ_M0
```

**Kiểm tra LTB:**
```
M_cr = C₁ × π² × E × I_y / L² × √(I_w / I_y + L² × G × J / (π² × E × I_y))
```

**Đà liên tục (3 nhịp trở lên):**
```
M_支 = -q × L² / 10
M_跨 = +q × L² / 16
```

---

## 4. Thiết kế Đà Chính (Primary Beam)

### 4.1 Soldier Beam (Thép hình)

**Tải trọng tác dụng:**
```
q = q_panel × S_panel + q_joist × S_joist
```

**Kiểm tra:**
```
σ = M / W_x ≤ f_y / γ_M0
τ = V / (h × t_w) ≤ f_v / γ_M0
δ = 5 × q × L⁴ / (384 × E × I_x) ≤ L/400
```

### 4.2 Shore (Cột chống điều chỉnh)

**Tải trọng dọc trục:**
```
P = Σ (q × A_col) + trọng lượng bản thân
```

**Chiều dài hiệu dụng:**
```
L_e = K × L
K = 1.0 (đầu dưới neo, đầu trên tự do xoay)
K = 0.7 (đầu dưới ngàm, đầu trên tự do xoay)
```

**Kiểm tra ổn định:**
```
P / A + (M / W) × (1 / (1 - P / P_E)) ≤ f_y / γ_M0
P_E = π² × E × I / (K × L)²
```

---

## 5. Thiết kế Cốp pha Tường

### 5.1 Áp lực Bê tông tươi

**Công thức Prowell:**
```
p_max = γ_bt × H_c
H_c = √(2 × q × C) / γ_bt
```
- q = tốc độ đổ bê tông (m/h)
- C = hệ số cohesion (thường = 0.3)

**Công thức đơn giản hóa:**
```
p_max = γ_bt × h_đổ ≤ 150 kN/m² (cho BT thường)
```

### 5.2 Stud (Thanh đứng)

**Khoảng cách tối đa:**
```
L_max = √(8 × f_b × S × I / (p × S²))
```
- f_b = cường độ chịu uốn stud
- I = moment quán tính stud
- p = áp lực bê tông

### 5.3 Wales (Đà ngang)

**Kiểm tra uốn + nén:**
```
σ = M / W + N / A ≤ f_y / γ_M0
```

---

## 6. Thiết kế Cốp pha Coffer (Bán trụ)

### 6.1 Hệ thống Coffer

```
┌─────────────────────────────────────────┐
│           PANEL (Thép/Gỗ)               │
├──────────┬──────────┬──────────┬──────────┤
│          │          │          │          │
│  STUD    │  STUD    │  STUD    │  STUD    │
│          │          │          │          │
├──────────┴──────────┴──────────┴──────────┤
│              WALE (Đà ngang)              │
├──────────────────────────────────────────┤
│              YOKE (Gông)                  │
└──────────────────────────────────────────┘
```

### 6.2 Tính toán Yoke

**Áp lực tác dụng lên Yoke:**
```
P = p × S_panel × S_stud
```

**Kiểm tra:**
```
σ = M / W ≤ f_y / γ_M0
τ = V × S / (I × t) ≤ f_v / γ_M0
```

### 6.3 Khoảng cách Yoke

**Thiết kế để đạt δ ≤ L/500:**
```
S_yoke = √(120 × E × I × f_y / (γ_bt × h²))
```

---

## 7. Tháo Cốp pha Sớm

### 7.1 Cường độ Yêu cầu

| Thời gian | Cường độ tối thiểu | Ứng dụng |
|------------|---------------------|----------|
| 12-24h | f_c' ≥ 5 MPa | Tháo side form |
| 24-48h | f_c' ≥ 10 MPa | Tháo beam bottom |
| 3-7 ngày | f_c' ≥ 15-20 MPa | Tháo slab bottom |

### 7.2 Kiểm tra Cylinder Test

```
f_c_test = P / A ≥ f_c_required
```

### 7.3 Điều kiện Tháo Sớm

**Sàn (Slab):**
```
f_c' ≥ 75% × f_c' thiết kế (cho simply supported)
f_c' ≥ 85% × f_c' thiết kế (cho continuous)
```

**Dầm (Beam):**
```
f_c' ≥ 70% × f_c' thiết kế (để tháo shoring)
```

---

## 8. Bảng Tra Nhanh

### 8.1 Khoảng cách Đà Gỗ (mm)

| Độ dày sàn (mm) | q < 5 kN/m² | q = 5-10 kN/m² | q > 10 kN/m² |
|------------------|-------------|-----------------|---------------|
| 100 | 900 | 750 | 600 |
| 150 | 750 | 600 | 450 |
| 200 | 600 | 450 | 300 |
| 250 | 450 | 300 | 225 |

### 8.2 Khoảng cách Soldier Beam (mm)

| Loại thép | Nhịp 1.8m | Nhịp 2.4m | Nhịp 3.0m |
|-----------|-----------|-----------|-----------|
| H150×75 | 1800 | 1500 | 1200 |
| H200×100 | 2400 | 2100 | 1800 |
| H250×125 | 3000 | 2700 | 2400 |

### 8.3 Chiều cao Đổ Bê tông Tối đa

| Nhiệt độ | Tốc độ đổ | Chiều cao tối đa |
|-----------|-----------|------------------|
| > 25°C | ≤ 1.5 m/h | 1.5 m |
| 15-25°C | ≤ 1.0 m/h | 2.0 m |
| < 15°C | ≤ 0.8 m/h | 3.0 m |

---

## 9. Deflection Giới hạn

| Loại cấu kiện | Giới hạn δ |
|----------------|------------|
| Panel (gỗ/thép) | L/270 |
| Joist (đà second) | L/360 |
| Soldier beam (đà primary) | L/400 |
| Shore (cột chống) | L/500 |

---

## 10. Checklist Thiết kế

- [ ] Xác định tải trọng (bê tông, steel, thi công)
- [ ] Chọn loại cốp pha (gỗ, thép, hệ thống)
- [ ] Tính panel (uốn, cắt, võng)
- [ ] Tính joist/đà
- [ ] Tính soldier beam / shore
- [ ] Kiểm tra ổn định
- [ ] Kiểm tra deflection
- [ ] Thiết kế neo và giằng
- [ ] Lập bản vẽ thi công
