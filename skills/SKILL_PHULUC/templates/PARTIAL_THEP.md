# PHỤ LỤC TÍNH TOÁN KẾT CẤU THÉP

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|----------|
| Công trình | {{project_name}} |
| Mã số | {{project_code}} |
| Hạng mục | {{item_name}} |
| Tiêu chuẩn | TCVN 5575:2024 |

### 1.1 Tiêu chuẩn áp dụng

| STT | Tên tiêu chuẩn | Số hiệu |
|:---:|---|---|
| 1 | Kết cấu thép | TCVN 5575:2024 |
| 2 | Tải trọng và tác động | TCVN 2737:2023 |
| 3 | Specification for Structural Steel Buildings | AISC 360-10 |

---

## 2. VẬT LIỆU

### 2.1 Thép cán

| STT | Mác thép | f<sub>y</sub> (MPa) | f<sub>u</sub> (MPa) | E (MPa) |
|:---:|---|---:|---:|---:|
| 1 | SS400 | 235 | 400 | 210000 |
| 2 | SM490 | 315 | 490 | 210000 |
| 3 | Q345 | 345 | 470 | 206000 |

{{#if steel_grade}}
**Thép sử dụng:** {{steel_grade}}
- f<sub>y</sub> = {{fy}} MPa
- f<sub>u</sub> = {{fu}} MPa
- γ<sub>M0</sub> = 1.0 (kiểm tra bền)
- γ<sub>M1</sub> = 1.1 (kiểm tra mất ổn định)
{{/if}}

### 2.2 Bu lông liên kết

| STT | Cấp bền | f<sub>ub</sub> (MPa) | f<sub>v</sub> (MPa) |
|:---:|---|---:|---:|
| 1 | 8.8 | 800 | 400 |
| 2 | 10.9 | 1000 | 500 |

{{#if bolt_grade}}
**Bu lông sử dụng:** {{bolt_grade}}
- f<sub>ub</sub> = {{fub}} MPa
{{/if}}

### 2.3 Que hàn

| STT | Loại que hàn | f<sub>wf</sub> (MPa) |
|:---:|---|---:|
| 1 | E60 | 180 |
| 2 | E70 | 200 |

---

## 3. TẢI TRỌNG VÀ NỘI LỰC

### 3.1 Tải trọng tác dụng

| STT | Loại tải | Giá trị | Đơn vị | Ghi chú |
|:---:|---|---:|---:|---|---|
| 1 | Tĩnh tải | {{g}} | kN/m | |
| 2 | Hoạt tải mái | {{q}} | kN/m | |
| 3 | Tải trọng gió | {{w}} | kN/m | |

### 3.2 Nội lực tính toán

| STT | Vị trí | M (kNm) | V (kN) | N (kN) | Tổ hợp |
|:---:|---|---:|---:|---:|---|
{{#each forces}}
| {{stt}} | {{location}} | {{M}} | {{V}} | {{N}} | {{combo}} |
{{/each}}

---

## 4. SƠ ĐỒ KẾT CẤU

```
{{diagram}}
```

---

## 5. TÍNH TOÁN CHI TIẾT

{{#each members}}
### 5.{{order}} {{member_name}}

#### 5.{{order}}.1 Thông số tiết diện

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Loại tiết diện | {{section_type}} | - |
| Ký hiệu | {{section_name}} | - |
| h × b × t<sub>w</sub> × t<sub>f</sub> | {{h}} × {{b}} × {{tw}} × {{tf}} | mm |
| A | {{A}} | cm² |
| I<sub>x</sub> | {{Ix}} | cm⁴ |
| W<sub>x</sub> | {{Wx}} | cm³ |
| i<sub>x</sub> | {{ix}} | cm |

#### 5.{{order}}.2 Kiểm tra bền

**Kiểm tra tiết diện theo phân loại:**

| Thông số | Giá trị | Giới hạn | Phân loại |
|-----------|----------|-----------|-----------|
| c/t<sub>f</sub> | {{c_tf}} | ≤ {{limit_tf}}ε | {{class_tf}} |
| h<sub>w</sub>/t<sub>w</sub> | {{hw_tw}} | ≤ {{limit_hw}}ε | {{class_hw}} |

**Phân loại tiết diện: {{section_class}}**

**Kiểm tra khả năng chịu uốn:**
```
M_c,Rd = W_pl × f_y / γ_M0
       = {{W_pl}} × 10⁻⁶ × {{fy}} / {{gamma_M0}}
       = {{M_cRd}} kNm

η_M = M_ed / M_c,Rd = {{M_ed}} / {{M_cRd}} = {{eta_M}} ≤ 1.0 ✓
```

**Kiểm tra khả năng chịu cắt:**
```
V_pl,Rd = A_v × f_y / (√3 × γ_M0)
         = {{Av}} × 10⁻⁴ × {{fy_SI}} / (1.732 × {{gamma_M0}})
         = {{V_plRd}} kN

η_V = V_ed / V_pl,Rd = {{V_ed}} / {{V_plRd}} = {{eta_V}} ≤ 1.0 ✓
```

#### 5.{{order}}.3 Kiểm tra ổn định tổng thể (LTB)

```
λ_LT = √(W_pl × f_y / M_cr)
     = √({{W_pl}} × {{fy_SI}} / {{M_cr}})
     = {{lambda_LT}}

Φ_LT = 0.5 × [1 + α_LT × (λ_LT - 0.2) + λ_LT²]
     = {{Phi_LT}}

χ_LT = 1 / (Φ_LT + √(Φ_LT² - λ_LT²))
     = {{chi_LT}}

M_b,Rd = χ_LT × W_pl × f_y / γ_M1
        = {{chi_LT}} × {{W_pl}} × {{fy_SI}} / {{gamma_M1}}
        = {{M_bRd}} kNm

η_LTB = M_ed / M_b,Rd = {{M_ed}} / {{M_bRd}} = {{eta_LTB}} ≤ 1.0 ✓
```

#### 5.{{order}}.4 Kiểm tra độ võng

```
f = {{f_calc}} mm
f_gh = L/{{L_limit}} = {{L}} / {{L_limit}} = {{f_limit}} mm
η_f = f / f_gh = {{f_calc}} / {{f_limit}} = {{eta_f}} ≤ 1.0 ✓
```

{{/each}}

---

## 6. LIÊN KẾT

{{#each connections}}
### 6.{{order}} Liên kết {{connection_name}}

#### 6.{{order}}.1 Sơ đồ liên kết

```
{{diagram}}
```

#### 6.{{order}}.2 Kiểm tra bu lông

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Số bu lông | {{n_bolt}} | - |
| Đường kính | Φ{{d_bolt}} | mm |
| Lực cắt thiết kế | V<sub>Ed</sub> = {{V_ed}} | kN |

```
V_Ed,bolt = V_Ed / n = {{V_ed}} / {{n_bolt}} = {{V_bolt}} kN
η_V = V_Ed,bolt / V_Rd = {{V_bolt}} / {{V_Rd}} = {{eta_V}} ≤ 1.0 ✓
```

{{#if has_weld}}
#### 6.{{order}}.3 Kiểm tra đường hàn

```
l_w = {{l_w}} mm
a_w = {{a_w}} mm
V_w,Rd = β × f_wd × l_w × a_w
       = {{beta}} × {{f_wd}} × {{l_w}} × {{a_w}} / 10³
       = {{V_wRd}} kN

η_w = V_Ed / V_w,Rd = {{V_ed}} / {{V_wRd}} = {{eta_w}} ≤ 1.0 ✓
```
{{/if}}

{{/each}}

---

## 7. BẢNG TỔNG HỢP

### 7.1 Kiểm tra cấu kiện

| STT | Cấu kiện | η<sub>M</sub> | η<sub>V</sub> | η<sub>LTB</sub> | η<sub>f</sub> | Trạng thái |
|:---:|---|---:|---:|---:|---:|---|
{{#each summary}}
| {{stt}} | {{name}} | {{eta_M}} | {{eta_V}} | {{eta_LTB}} | {{eta_f}} | {{status}} |
{{/each}}

### 7.2 Kiểm tra liên kết

| STT | Liên kết | η<sub>V</sub> | η<sub>w</sub> | Trạng thái |
|:---:|---|---:|---:|---|
{{#each conn_summary}}
| {{stt}} | {{name}} | {{eta_V}} | {{eta_w}} | {{status}} |
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
