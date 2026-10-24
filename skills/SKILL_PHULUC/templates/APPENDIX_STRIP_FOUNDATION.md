# PHỤ LỤC TÍNH TOÁN KẾT CẤU
## MÓNG BĂNG BTCT

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|---------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Cấu kiện | Móng băng |
| Tiêu chuẩn | TCVN 5574:2018, TCVN 10304:2025 |
| Người tính | {{calculator}} |
| Ngày tính | {{calc_date}} |

---

## 2. VẬT LIỆU

### 2.1 Bê tông móng

| Mác | R_b (MPa) | R_bt (MPa) | E_b (MPa) |
|-----|-----------|------------|-----------|
| B15 | 8.5 | 0.75 | 24000 |
| B20 | 11.5 | 0.90 | 27500 |
| B25 | 14.5 | 1.05 | 30000 |
| B30 | 17.0 | 1.15 | 32500 |

> Thiết kế: **{{concrete_grade}}** — R_b = {{Rb}} MPa

### 2.2 Cốt thép

| Loại | R_s (MPa) | R_sc (MPa) | R_sw (MPa) |
|------|-----------|------------|------------|
| CB300-V | 260 | 260 | 210 |
| CB400-V | 350 | 350 | 280 |
| CB500-V | 435 | 400 | 300 |

> Thiết kế: **{{steel_grade}}** — R_s = {{Rs}} MPa

### 2.3 Lớp bảo vệ

- Đáy móng: a = 50 mm (tiếp xúc đất)
- Mặt trên: a = 35 mm

---

## 3. HÌNH HỌC MÓNG BĂNG

### 3.1 Kích thước mặt bằng

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|-----------|----------|---------|---------|
| Chiều dài móng | L_m | {{L_m}} | m |
| Chiều rộng móng | B_m | {{B_m}} | m |
| Chiều dày móng | h | {{h}} | mm |
| Chiều rộng chân cột | B_c | {{B_c}} | m |

### 3.2 Mặt bằng móng

```
    ┌─────────────────────────────────────────────┐
    │                                             │
    │             MÓNG BĂNG                      │
    │  ◄────────── B_m ──────────►              │
    │                                             │
    │   │                          │             │
    │   │      │        │         │             │
    │   │      │        │         │             │
    └─────────────────────────────────────────────┘
         ◄───── L_m ─────►
```

---

## 4. ĐIỀU KIỆN ĐỊA CHẤT

### 4.1 Số liệu địa chất

| Lớp | Độ sâu (m) | Loại đất | γ (kN/m³) | E (MPa) | φ (°) |
|------|------------|----------|-----------|---------|-------|
{{soil_layers}}

### 4.2 Sức kháng đất nền

| Thông số | Giá trị | Đơn vị |
|----------|---------|---------|
| Sức kháng nền thiết kế | R_ft | {{R_ft}} kPa |
| Sức kháng mũi | q_f | {{q_f}} kPa |
| Sức kháng thân | f_s | {{f_s}} kPa |

---

## 5. TẢI TRỌNG

### 5.1 Tải trọng từ kết cấu bên trên

| Loại tải | Giá trị | Đơn vị |
|----------|---------|---------|
| Lực dọc | N | {{N}} kN |
| Lực cắt | V | {{V}} kN |
| Mô men | M | {{M}} kNm |

### 5.2 Tổ hợp tải trọng

```
TH1: N_max, M_tương ứng
TH2: N_min (cho kiểm tra lật)
TH3: N_tb cho kiểm tra lún
```

### 5.3 Tải trọng tính đổi lên móng

```
q_tt = N / A + M × y / I
     = {{N}} / ({{L_m}} × {{B_m}}) + {{M}} × {{B_m}}/2 / ({{B_m}}³/12)
     = {{q_tt}} kPa
```

---

## 6. KIỂM TRA KÍCH THƯỚC MÓNG

### 6.1 Kiểm tra điều kiện bền

**Bước 1:** Ứng suất dưới đáy móng

```
σ_max = N / A + M / W
      = {{N}} / ({{L_m}} × {{B_m}}) + 6 × {{M}} / ({{L_m}} × {{B_m}}²)
      = {{sigma_max}} kPa

σ_min = N / A - M / W
      = {{sigma_min}} kPa
```

**Bước 2:** So sánh với sức kháng nền

```
R_ft = {{R_ft}} kPa
η = σ_max / R_ft = {{sigma_max}} / {{R_ft}} = {{eta_foundation}}
```

→ **{{status_foundation}}**

### 6.2 Kiểm tra lật

**Bước 1:** Tính mô men chống lật

```
M_chong = N × B_m / 2
        = {{N}} × {{B_m}} / 2
        = {{M_chong}} kNm
```

**Bước 2:** Hệ số an toàn lật

```
FS_lật = M_chong / M
        = {{M_chong}} / {{M}}
        = {{FS_overturning}} ≥ 1.5
```

→ **{{status_overturning}}**

### 6.3 Kiểm tra trượt

**Bước 1:** Lực chống trượt

```
F_chong = N × tan(δ) + c × A
        = {{N}} × tan({{delta}}) + {{c}} × {{L_m}} × {{B_m}}
        = {{F_chong}} kN
```

**Bước 2:** Hệ số an toàn trượt

```
FS_trượt = F_chong / V
          = {{F_chong}} / {{V}}
          = {{FS_sliding}} ≥ 1.3
```

→ **{{status_sliding}}**

---

## 7. TÍNH TOÁN NỘI LỰC MÓNG

### 7.1 Sơ đồ tính

```
    ┌───────────────────────────────┐
    │           Móng băng           │
    │  ────────────────────────────  │  → q_tt (phản lực đất nền)
    │  ↓ q_tt    ↓ q_tt    ↓ q_tt  │
    │                               │
    │   ↑ P_1    ↑ P_2    ↑ P_3    │  → Lực từ cột
    └───────────────────────────────┘
```

**Phương pháp:** Tính theo sơ đồ dầm trên nền đàn hồi (Winkler)

### 7.2 Tính nội lực

**Bước 1:** Xác định độ cứng tương đối

```
α = ⁴√(k × b / (4 × E × I))
  = ⁴√({{k}} × {{b}} / (4 × {{E}} × {{I}}))
  = {{alpha}} m⁻¹
```

**Bước 2:** Mô men và lực cắt

| Tiết diện | M (kNm/m) | V (kN/m) |
|-----------|-----------|-----------|
{{moment_shear_table}}

---

## 8. TÍNH TOÁN CỐT THÉP

### 8.1 Cốt thép chịu mô men (phương dài)

**Bước 1:** Thiết kế tại tiết diện nguy hiểm

```
M_max = {{M_max}} kNm/m
a = 50 mm
h_0 = {{h}} - 50 = {{h0}} mm

α = M / (R_b × b × h_0²)
  = {{M_max}}×10⁶ / ({{Rb}} × 1000 × {{h0}}²)
  = {{alpha}}
```

**Bước 2:** Tính diện tích cốt thép

```
ζ = 0.5 × (1 + √(1 - 2α)) = {{zeta}}
A_s,req = M / (R_s × ζ × h_0)
        = {{As_req_long}} mm²/m
```

**Bước 3:** Chọn cốt thép

| Đường kính | Diện tích 1 thanh | Số thanh | Khoảng cách |
|------------|-------------------|----------|-------------|
| Φ{{dia_long}} | {{A_bar}} mm² | {{n_long}} | {{s_long}} mm |

→ **Chọn: {{rebar_long}}**

**Bước 4:** Kiểm tra

```
A_s,prov = {{As_prov_long}} mm²/m
η = {{As_req_long}} / {{As_prov_long}} = {{eta_long}}
```

→ **{{status_long}}**

### 8.2 Cốt thép phân bố (phương ngắn)

**Bước 1:** Diện tích cốt thép phân bố

```
A_s,pb = 0.1 × A_s,chủ ≥ {{As_min}}
       = {{As_pb}} mm²/m
```

**Bước 2:** Chọn cốt thép

→ **Chọn: {{rebar_trans}}**

### 8.3 Kiểm tra cường độ trên tiết diện nghiêng

**Bước 1:** Khả năng chịu cắt của bê tông

```
Q_b = 0.3 × R_b × b × h_0
    = {{Q_b}} kN/m
```

**Bước 2:** So sánh

```
V_max = {{V_max}} kN/m
η = {{V_max}} / {{Q_b}} = {{eta_shear}}
```

→ **{{status_shear}}**

---

## 9. KIỂM TRA BIẾN DẠNG

### 9.1 Kiểm tra lún

**Bước 1:** Tải trọng gây lún

```
N_tt = {{N}} kN
q_tt = N_tt / A = {{q_tt}} kPa
σ_zp = α × q_tt = {{sigma_zp}} kPa
```

**Bước 2:** Tính lún

| Lớp | Độ dày (m) | σ_zp (kPa) | E (MPa) | Lún (mm) |
|------|------------|------------|---------|----------|
{{settlement_table}}

**Tổng lún: S = {{S}} mm ≤ S_gh = {{S_allow}} mm**

→ **{{status_settlement}}**

### 9.2 Kiểm tra võng

```
f = {{f}} mm
f_gh = L / 250 = {{L_m}}/250 = {{f_allow}} mm
η = {{f}} / {{f_allow}} = {{eta_deflection}}
```

→ **{{status_deflection}}**

---

## 10. BẢNG TỔNG HỢP

### 10.1 Cốt thép thiết kế

| Vị trí | Loại | Thép chọn | A_s (mm²/m) | η |
|---------|------|-----------|-------------|---|
| Đáy móng - Dọc | Chịu lực | {{rebar_long}} | {{As_prov_long}} | {{eta_long}} |
| Đáy móng - Ngang | Phân bố | {{rebar_trans}} | {{As_prov_trans}} | — |

### 10.2 Hệ số sử dụng

| Kiểm tra | Giá trị | Giới hạn | Trạng thái |
|----------|---------|----------|------------|
| Bền nền | η = {{eta_foundation}} | ≤ 1.0 | 🟢 {{status_foundation}} |
| Chống lật | FS = {{FS_overturning}} | ≥ 1.5 | 🟢 {{status_overturning}} |
| Chống trượt | FS = {{FS_sliding}} | ≥ 1.3 | 🟢 {{status_sliding}} |
| Chịu uốn | η = {{eta_long}} | ≤ 1.0 | 🟢 {{status_long}} |
| Chịu cắt | η = {{eta_shear}} | ≤ 1.0 | 🟢 {{status_shear}} |
| Lún | S = {{S}} mm | ≤ {{S_allow}} mm | 🟢 {{status_settlement}} |

---

## 11. KẾT LUẬN

**Móng băng BTCT đạt yêu cầu:**

✅ Kiểm tra bền nền (η = {{eta_foundation}} ≤ 1.0)  
✅ Kiểm tra lật (FS = {{FS_overturning}} ≥ 1.5)  
✅ Kiểm tra trượt (FS = {{FS_sliding}} ≥ 1.3)  
✅ Cường độ chịu uốn (η = {{eta_long}} ≤ 1.0)  
✅ Cường độ chịu cắt (η = {{eta_shear}} ≤ 1.0)  
✅ Biến dạng lún (S = {{S}} mm ≤ {{S_allow}} mm)  

---

## 12. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|---------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Người kiểm tra | {{reviewer}} | | |
| Người duyệt | {{approver}} | | |

---

*Tài liệu được tạo tự động bởi SKILL_PHULUC*
*Tiêu chuẩn: TCVN 5574:2018, TCVN 10304:2025*
