# PHỤ LỤC TÍNH TOÁN KẾT CẤU BÊ TÔNG CỐT THÉP

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|----------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Hạng mục | {{item_name}} |
| Tiêu chuẩn | TCVN 5574:2018 |

### 1.1 Tiêu chuẩn áp dụng

| STT | Tên tiêu chuẩn | Số hiệu |
|:---:|---|---|
| 1 | Kết cấu bê tông và bê tông cốt thép | TCVN 5574:2018 |
| 2 | Tải trọng và tác động | TCVN 2737:2023 |
| 3 | Cốt thép thanh vằn | TCVN 1651-2:2018 |

---

## 2. VẬT LIỆU

### 2.1 Bê tông

| Thông số | Giá trị | Đơn vị | Ghi chú |
|-----------|----------|---------|---------|
| Mác bê tông | {{concrete_grade}} | - | |
| Cấp độ bền | C{{concrete_class}} | - | |
| R<sub>b</sub> | {{Rb}} | MPa | |
| R<sub>bt</sub> | {{Rbt}} | MPa | |
| γ<sub>c</sub> | 1.3 | - | Hệ số an toàn |
| E<sub>b</sub> | {{Eb}} | MPa | |

### 2.2 Cốt thép

| Thông số | Giá trị | Đơn vị | Ghi chú |
|-----------|----------|---------|---------|
| Thép < Φ10 | CB240-T | - | TCVN 1651-1:2018 |
| Thép ≥ Φ10 | CB400-V | - | TCVN 1651-2:2018 |
| f<sub>y</sub> | 400 | MPa | |
| f<sub>yk</sub> | 400 | MPa | |
| γ<sub>s</sub> | 1.15 | - | Hệ số an toàn |

---

## 3. TẢI TRỌNG

### 3.1 Tĩnh tải

| STT | Loại tải | Giá trị | Đơn vị |
|:---:|---|---:|:---:|
| 1 | Hoàn thiện sàn | {{g_san}} | kN/m² |
| 2 | Trần, MEP | {{g_tran}} | kN/m² |
| 3 | Dầm | {{g_dam}} | kN/m |

### 3.2 Hoạt tải

| STT | Loại tải | Giá trị | Đơn vị | Căn cứ |
|:---:|---|---:|:---:|---|---|
| 1 | Sàn văn phòng | {{q_van_phong}} | kN/m² | TCVN 2737 |
| 2 | Ban công | {{q_ban_cong}} | kN/m² | TCVN 2737 |

---

## 4. TỔ HỢP TẢI TRỌNG

### 4.1 Tổ hợp TTGH-I (ULS)

| STT | Tổ hợp | Hệ số |
|:---:|---|---:|
| 1 | 1.0G + 1.0Q | TH1 |
| 2 | 1.0G + 0.9Q | TH2 |

### 4.2 Tổ hợp TTGH-II (SLS)

| STT | Tổ hợp | Hệ số |
|:---:|---|---:|
| 1 | 1.0G + 1.0Q | Tĩnh tải + Hoạt tải |

---

## 5. NỘI LỰC TÍNH TOÁN

### 5.1 Bảng tổng hợp nội lực

| STT | Tiết diện | M (kNm) | V (kN) | N (kN) | Tổ hợp |
|:---:|---|---:|---:|---:|---|
{{#each forces}}
| {{stt}} | {{section}} | {{M}} | {{V}} | {{N}} | {{combo}} |
{{/each}}

---

## 6. TÍNH TOÁN CHI TIẾT

{{#each elements}}
### 6.{{order}} {{element_name}}

#### 6.{{order}}.1 Sơ đồ kết cấu

```
{{diagram}}
```

#### 6.{{order}}.2 Thông số hình học

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Tiết diện | {{b}} × {{h}} | mm |
| Chiều dài | {{L}} | m |
| a | {{a}} | mm |
| d | {{d}} | mm |

#### 6.{{order}}.3 Tính cốt thép

**Bước 1:** Giả thiết chiều cao vùng nén
```
a = {{a_calc}} mm
```

**Bước 2:** Tính cánh tay đòn nội lực
```
z = d - a/2 = {{d}} - {{a_calc}}/2 = {{z_calc}} mm
```

**Bước 3:** Tính A<sub>s,yêu cầu</sub>
```
A_s,req = M_ed / (f_y/γ_s × z)
        = {{M_ed}} × 10⁶ / ({{fy_over_gamma}} × {{z_calc}})
        = {{As_req}} mm²
```

**Bước 4:** Kiểm tra chiều cao vùng nén
```
x = A_s × f_y / (0.85 × f_c × b)
  = {{As_req}} × {{fy}} / (0.85 × {{fc}} × {{b}})
  = {{x_calc}} mm
```

**Bước 5:** Chọn cốt thép
```
Chọn: {{rebar_choice}}
A_s,prov = {{As_prov}} mm²
η_M = A_s,req / A_s,prov = {{As_req}} / {{As_prov}} = {{eta_M}} ≤ 1.0 ✓
```

#### 6.{{order}}.4 Kiểm tra cốt đai

```
V_ed = {{V_ed}} kN
V_c = 0.3 × φ × f_ct × b × d
    = 0.3 × 0.9 × {{fct}} × {{b}} × {{d}} / 10³
    = {{Vc}} kN

V_sw = V_ed - V_c = {{V_ed}} - {{Vc}} = {{Vsw}} kN

Chọn đai: φ{{stirrup_dia}}a{{stirrup_s}} (4 nhánh)
A_sw = {{A_sw}} mm²
η_V = {{V_ed}} / ({{Vc}} + {{Vsw}}) = {{eta_V}} ≤ 1.0 ✓
```

#### 6.{{order}}.5 Kiểm tra độ võng

```
f = {{f_calc}} mm
f_gh = L/{{span_limit}} = {{L}} / {{span_limit}} = {{f_limit}} mm
η_f = f / f_gh = {{f_calc}} / {{f_limit}} = {{eta_f}} ≤ 1.0 ✓
```

{{/each}}

---

## 7. BẢNG TỔNG HỢP KẾT QUẢ

### 7.1 Cốt thép đã chọn

| STT | Cấu kiện | Thép chịu lực | A<sub>s</sub> (mm²) | Thép đai | η_M | η_V |
|:---:|---|---:|---:|---:|---:|---:|
{{#each summary}}
| {{stt}} | {{name}} | {{rebar}} | {{As}} | {{stirrup}} | {{eta_M}} | {{eta_V}} |
{{/each}}

### 7.2 Bảng kiểm tra

| STT | Cấu kiện | η<sub>M</sub> | η<sub>V</sub> | η<sub>f</sub> | Trạng thái |
|:---:|---|---:|---:|---:|---|
{{#each check}}
| {{stt}} | {{name}} | {{eta_M}} | {{eta_V}} | {{eta_f}} | {{status}} |
{{/each}}

---

## 8. KẾT LUẬN

{{conclusion}}

---

## 9. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|--------|---------|---------|------|
| Người tính | {{calculator}} | | {{calc_date}} |
| Kiểm tra | {{reviewer}} | | {{review_date}} |
| Duyệt | {{approver}} | | {{approve_date}} |
