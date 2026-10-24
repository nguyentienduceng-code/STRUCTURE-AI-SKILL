# PHỤ LỤC TÍNH TOÁN KẾT CẤU
## CẦU THANG BỘ BTCT

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|---------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Cấu kiện | Cầu thang bộ |
| Tiêu chuẩn | TCVN 5574:2018, TCVN 4453:1995 |
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

| Loại | Mác | R_s (MPa) | R_sc (MPa) | R_sw (MPa) |
|------|-----|-----------|------------|------------|
| CB300-V | CI, CII | 260 | 260 | 210 |
| CB400-V | CIII | 350 | 350 | 280 |
| CB500-V | CIV | 435 | 400 | 300 |

> Thiết kế: **{{steel_grade}}** — R_s = {{Rs}} MPa

### 2.3 Lớp bảo vệ

- Mặt trên (mặt đi): a = 20 mm
- Mặt dưới (mặt khuất): a = 25 mm
- Thanh thép đai: a = 15 mm

---

## 3. HÌNH HỌC CẦU THANG

### 3.1 Sơ đồ kích thước

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|-----------|----------|---------|---------|
| Chiều cao tầng | H | {{H}} | m |
| Số bậc | n | {{n_steps}} | bậc |
| Chiều cao mỗi bậc | h | {{h}} | mm |
| Chiều rộng mặt bậc | b | {{b}} | mm |
| Chiều dài đoạn dốc | L_d | {{L_d}} | m |
| Chiều dài chiếu nghỉ | L_cn | {{L_cn}} | m |
| Chiều dày bản thang | t | {{t}} | mm |
| Góc nghiêng | α | {{alpha}} | ° |

### 3.2 Bảng tra bậc thang

| Bậc | Cao độ (m) | Cấu hình |
|------|-----------|----------|
{{stair_table}}

---

## 4. TẢI TRỌNG

### 4.1 Tĩnh tải

| Thành phần | Tải trọng (kN/m²) | Ghi chú |
|------------|-------------------|---------|
| Bản BTCT (t = {{t}} mm) | {{q_concrete}} | 25 × {{t}}/1000 |
| Lớp hoàn thiện mặt | {{q_finish}} | Đá granit 30mm |
| Lan can + tay vịn | {{q_rail}} | ≈ 0.1 kN/m |
| **Tổng tĩnh tải** | **{{q_DL}}** | |

### 4.2 Hoạt tải

| Loại | Giá trị (kN/m²) | Tiêu chuẩn |
|------|-----------------|------------|
| Hoạt tải sử dụng | {{q_LL}} | TCVN 2737:2023 |
| Hoạt tải tập trung (1 điểm) | {{P_point}} | Kiểm tra bản thang |

### 4.3 Tổ hợp tải trọng

```
TH1: 1.2 × Tĩnh tải + 1.5 × Hoạt tải
TH2: 1.0 × Tĩnh tải + 1.0 × Hoạt tải
```

---

## 5. SƠ ĐỒ KẾT CẤU

```
        ↑ Tay vịn
    ═══════════════
   /                \
  /                  \
 /  Bản thang       \  Chiếu nghỉ
/                    \──────────
───────────────────────────────
      Mặt bằng cầu thang
```

**Sơ đồ tính toán:** Dầm đơn giản có gối tựa tại đầu thang và chân thang

---

## 6. NỘI LỰC

### 6.1 Mô men uốn

**Bước 1:** Tính phản lực gối

```
ΣM_A = 0
R_B × L - q × L²/2 = 0
R_B = q × L / 2
R_A = q × L / 2
```

Với L = {{L_d}} m, q = {{q_total}} kN/m² × {{b}} m = {{q_lin}} kN/m

→ R_A = R_B = {{R_AB}} kN

**Bước 2:** Mô men giữa nhịp

```
M_max = q × L² / 8
      = {{q_lin}} × {{L_d}}² / 8
      = {{M_max}} kNm/m
```

### 6.2 Lực cắt

```
V_max = q × L / 2
      = {{q_lin}} × {{L_d}} / 2
      = {{V_max}} kN/m
```

### 6.3 Bảng nội lực

| Tiết diện | M (kNm/m) | V (kN/m) |
|-----------|-----------|----------|
| Gối A | 0 | {{V_max}} |
| 1/4 nhịp | {{M_quarter}} | {{V_quarter}} |
| Giữa nhịp | {{M_max}} | 0 |
| 3/4 nhịp | {{M_quarter}} | {{V_quarter}} |
| Gối B | 0 | {{V_max}} |

---

## 7. TÍNH TOÁN CỐT THÉP

### 7.1 Thiết kế cốt thép chịu uốn

**Bước 1:** Xác định cạnh làm việc

```
h_0 = h - a
    = {{h}} - 25
    = {{h0}} mm
```

**Bước 2:** Kiểm tra chiều cao vùng nén

```
α = M / (R_b × b × h_0²)
  = {{M_max}}×10⁶ / ({{Rb}} × 1000 × {{h0}}²)
  = {{alpha_calc}}

ξ = 0.8 - √(0.64 - 2α)
  = {{xi}}
```

**Bước 3:** Tính diện tích cốt thép yêu cầu

```
A_s,req = M / (R_s × ζ × h_0)
        = {{M_max}}×10⁶ / ({{Rs}} × {{zeta}} × {{h0}})
        = {{As_req}} mm²/m
```

**Bước 4:** Chọn cốt thép

| Đường kính | Diện tích 1 thanh | Số thanh | Khoảng cách |
|------------|-------------------|----------|-------------|
| Φ{{dia_top}} | {{A_bar}} mm² | {{n_top}} | {{s_top}} mm |

→ **Chọn: {{rebar_choice}}**

**Bước 5:** Kiểm tra

```
A_s,prov = {{As_prov}} mm²
η = A_s,req / A_s,prov = {{As_req}} / {{As_prov}} = {{eta}}
```

→ **{{status_eta}}**

### 7.2 Kiểm tra cường độ trên tiết diện nghiêng

**Bước 1:** Khả năng chịu cắt của bê tông

```
Q_b = 0.6 × R_bt × b × h_0
    = 0.6 × {{Rbt}} × 1000 × {{h0}}
    = {{Q_b}} kN/m
```

**Bước 2:** So sánh

```
V_max = {{V_max}} kN/m
η = V_max / Q_b = {{V_max}} / {{Q_b}} = {{eta_shear}}
```

→ **{{status_shear}}**

### 7.3 Kiểm tra độ võng

**Bước 1:** Độ cứng

```
B = 0.85 × E_b × I
  = 0.85 × {{Eb}} × {{I}}
  = {{B}} kNm²
```

**Bước 2:** Độ võng

```
f = 5 × q × L⁴ / (384 × B)
  = 5 × {{q_lin}} × {{L_d}}⁴ / (384 × {{B}})
  = {{f}} mm
```

**Bước 3:** Giới hạn

```
f_allow = L / 250 = {{L_d}}/250 = {{f_allow}} mm
η = f / f_allow = {{f}} / {{f_allow}} = {{eta_defl}}
```

→ **{{status_defl}}**

---

## 8. BẢNG TỔNG HỢP

### 8.1 Cốt thép chịu lực

| Phương | Thép đáy | Thép trên | Khoảng cách |
|--------|----------|----------|-------------|
| Bản thang chính | {{rebar_bottom}} | {{rebar_top}} | {{s_main}} mm |
| Thép phân bố | {{rebar_dist}} | — | {{s_dist}} mm |

### 8.2 Hệ số sử dụng

| Kiểm tra | Giá trị | Giới hạn | Trạng thái |
|----------|---------|----------|------------|
| Chịu uốn | η = {{eta}} | ≤ 1.0 | 🟢 {{status_eta}} |
| Chịu cắt | η = {{eta_shear}} | ≤ 1.0 | 🟢 {{status_shear}} |
| Độ võng | η = {{eta_defl}} | ≤ 1.0 | 🟢 {{status_defl}} |

---

## 9. CHI TIẾT CỐT THÉP

### 9.1 Neo cốt thép

- Chiều dài neo: L_an = {{L_an}} × Ø (TCVN 5574:2018 Mục 10.3.5)
- Đoạn uốn móc: 12Ø cho thanh tròn

### 9.2 Nối cốt thép

- Nối buộc: L_n = {{L_n}} × Ø
- Không nối tại vị trí mô men max
- Khoảng cách nối: ≥ 35Ø

### 9.3 Cốt thép cấu tạo

- Thép giá: Φa{{dia_stirrup}} @ {{s_stirrup}} mm
- Thép phân bố: ≥ 20% A_s chịu lực

---

## 10. KẾT LUẬN

**Cầu thang bộ BTCT đạt yêu cầu về:**

✅ Cường độ chịu uốn (η = {{eta}} ≤ 1.0)  
✅ Cường độ chịu cắt (η = {{eta_shear}} ≤ 1.0)  
✅ Độ võng (η = {{eta_defl}} ≤ 1.0)  

**Cốt thép thiết kế:**

- Bản thang chính: **{{rebar_main_summary}}**
- Thép phân bố: **{{rebar_dist_summary}}**

---

## 11. PHỤ LỤC

### Bảng tra nội lực đầy đủ

| x (m) | M (kNm) | V (kN) |
|-------|---------|---------|
{{full_internal_table}}

### Bảng tra vật liệu

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|----------|----------|---------|---------|
| Cường độ chịu nén | R_b | {{Rb}} | MPa |
| Cường độ chịu kéo | R_bt | {{Rbt}} | MPa |
| Mô đun đàn hồi | E_b | {{Eb}} | MPa |
| Cường độ chịu kéo cốt thép | R_s | {{Rs}} | MPa |

---

## 12. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|---------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Người kiểm tra | {{reviewer}} | | |
| Người duyệt | {{approver}} | | |

---

*Tài liệu được tạo tự động bởi SKILL_PHULUC — Phụ lục Tính toán Kết cấu Chuyên nghiệp*
*Tiêu chuẩn: TCVN 5574:2018, TCVN 4453:1995*
