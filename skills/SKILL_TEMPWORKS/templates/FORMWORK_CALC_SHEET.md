# FORMWORK_CALC_SHEET.md — Template Bảng Tính Cốp pha

> **Sử dụng cho:** SKILL_TEMPWORKS — Xuất bảng tính thiết bị công tác tạm
> **Template:** Bảng tính thiết kế cốp pha/shoring

---

# THUYẾT MINH TÍNH TOÁN THIẾT BỊ CÔNG TÁC TẠM

## I. THÔNG TIN CHUNG

| Thông tin | Nội dung |
|-----------|----------|
| **Dự án** | [Tên dự án] |
| **Công trình** | [Tên công trình] |
| **Hạng mục** | [Tên hạng mục thi công] |
| **Ký hiệu bản vẽ** | [Ký hiệu] |
| **Ngày lập** | [DD/MM/YYYY] |
| **Người lập** | [Họ tên, Chức vụ] |

---

## II. TIÊU CHUẨN VÀ TÀI LIỆU THIẾT KẾ

### Tiêu chuẩn áp dụng

| STT | Mã tiêu chuẩn | Tên tiêu chuẩn |
|-----|----------------|-----------------|
| 1 | TCVN 5575:2024 | Kết cấu thép |
| 2 | TCVN 5574:2018 | Kết cấu bê tông cốt thép |
| 3 | TCVN 2737:2023 | Tải trọng và tác động |
| 4 | ACI 347-04 | Guide to Formwork |

### Tài liệu tham khảo

- Bản vẽ thiết kế kết cấu: [Ký hiệu]
- Bản vẽ kiến trúc: [Ký hiệu]
- Hồ sơ khảo sát ĐCCT: [Số báo cáo]

---

## III. VẬT LIỆU VÀ ĐẶC TRƯNG

### III.1. Bê tông

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Mác bê tông | B[XX] | - |
| Cường độ chịu nén thiết kế | f'_c | MPa |
| Khối lượng riêng | γ_bt | kN/m³ |
| Modul đàn hồi | E_bt | MPa |

### III.2. Cốp pha

| Loại | Vật liệu | Đặc trưng |
|------|-----------|------------|
| Panel | [Gỗ/Thép] | t = [XX] mm |
| Đà | [Gỗ/Thép] | [Kích thước] |
| Cột chống | [Thép/Gỗ] | [Loại] |

### III.3. Thép cốt cốp pha

| Thông số | Giá trị | Đơn vị |
|-----------|----------|---------|
| Cường độ chảy | f_y | MPa |
| Modul đàn hồi | E | MPa |
| Hệ số an toàn | γ_M0 | - |

---

## IV. TẢI TRỌNG TÍNH TOÁN

### IV.1. Tĩnh tải

| Loại tải | Công thức | Giá trị | Đơn vị |
|-----------|-----------|---------|---------|
| Bê tông tươi | γ_bt × đ.dày sàn | [XX] | kN/m² |
| Cốt thép | ~0.5 - 1.0 | [XX] | kN/m² |
| Cốp pha | Tra bảng | [XX] | kN/m² |
| **Tổng dead load** | | **[XX]** | **kN/m²** |

### IV.2. Hoạt tải thi công

| Loại tải | Giá trị | Đơn vị |
|-----------|----------|---------|
| Người + dụng cụ | 1.5 | kN/m² |
| Đầm bê tông | 0.5 | kN/m² |
| **Tổng live load** | **[XX]** | **kN/m²** |

### IV.3. Tổ hợp tải trọng

```
q_design = γ_D × (q_bt + q_phan) + γ_L × q_tc
         = 1.2 × [XX] + 1.5 × [XX]
         = [XX] kN/m²
```

---

## V. TÍNH TOÁN PANEL CỐP PHA

### V.1. Sơ đồ tính

```
┌─────────────────────────────────────────────┐
│                 PANEL                        │
│  ←─────── S (khoảng cách đà) ──────────→ │
├────────────┬────────────┬────────────────────┤
│            │           │                    │
│   ĐÀ GỖ   │  ĐÀ GỖ   │     ĐÀ GỖ         │
│            │           │                    │
└────────────┴───────────┴────────────────────┘
```

### V.2. Kiểm tra uốn

**Moment tính toán:**
```
M_max = q × S² / 8
      = [XX] × [XX]² / 8
      = [XX] kNm/m
```

**Ứng suất uốn:**
```
σ = M / W ≤ f_m
  = [XX] × 10⁶ / [XX]
  = [XX] MPa ≤ [XX] MPa ✓
```

**Hệ số sử dụng:**
```
η_M = σ / f_m = [XX]%
```

### V.3. Kiểm tra cắt

**Lực cắt:**
```
V_max = q × S / 2
       = [XX] × [XX] / 2
       = [XX] kN/m
```

**Ứng suất cắt:**
```
τ = V × S / (2 × I × b) × Q / I ≤ f_v
  = [XX] MPa ≤ [XX] MPa ✓
```

**Hệ số sử dụng:**
```
η_V = τ / f_v = [XX]%
```

### V.4. Kiểm tra võng

**Độ võng:**
```
δ = 5 × q × S⁴ / (384 × E × I)
  = 5 × [XX] × [XX]⁴ / (384 × [XX] × [XX])
  = [XX] mm
```

**Độ võng cho phép:**
```
δ_allow = S / 270 = [XX] mm
```

**Hệ số sử dụng:**
```
η_f = δ / δ_allow = [XX]%
```

---

## VI. TÍNH TOÁN ĐÀ ĐỠ

### VI.1. Sơ đồ tính

**Tải trọng lên đà:**
```
q_joist = q_design × S_panel
        = [XX] × [XX]
        = [XX] kN/m
```

### VI.2. Kiểm tra uốn

**Moment tính toán:**
```
M_max = q_joist × L² / 8
      = [XX] × [XX]² / 8
      = [XX] kNm
```

**Ứng suất uốn:**
```
σ = M / W ≤ f_y / γ_M0
  = [XX] ≤ [XX] MPa ✓
```

**Hệ số sử dụng:**
```
η_M = [XX]%
```

### VI.3. Kiểm tra võng

**Độ võng:**
```
δ = 5 × q × L⁴ / (384 × E × I)
  = [XX] mm
```

**Độ võng cho phép:**
```
δ_allow = L / 360 = [XX] mm
```

**Hệ số sử dụng:**
```
η_f = [XX]%
```

---

## VII. TÍNH TOÁN CỘT CHỐNG (SHORE)

### VII.1. Tải trọng lên cột chống

```
P = q_design × S_joist × L_joist
  = [XX] × [XX] × [XX]
  = [XX] kN
```

### VII.2. Kiểm tra ổn định

**Chiều dài hiệu dụng:**
```
L_e = K × L
    = [XX] × [XX]
    = [XX] m
```

**Độ mảnh:**
```
λ = L_e / i ≤ λ_allow
```

**Kiểm tra:**
```
P / A + M / W × (1 / (1 - P/P_E)) ≤ f_y / γ_M0
```

---

## VIII. BẢNG TỔNG HỢP KẾT QUẢ

| Cấu kiện | Thông số | Giá trị | Cho phép | η | Kết luận |
|-----------|----------|---------|----------|---|-----------|
| **Panel** | σ_M (MPa) | [XX] | [XX] | [XX]% | ✓ ĐẠT |
| | τ_V (MPa) | [XX] | [XX] | [XX]% | ✓ ĐẠT |
| | δ_f (mm) | [XX] | [XX] | [XX]% | ✓ ĐẠT |
| **Đà** | σ_M (MPa) | [XX] | [XX] | [XX]% | ✓ ĐẠT |
| | δ_f (mm) | [XX] | [XX] | [XX]% | ✓ ĐẠT |
| **Shore** | P (kN) | [XX] | [XX] | [XX]% | ✓ ĐẠT |

---

## IX. KẾT LUẬN

Thiết bị công tác tạm (cốp pha, đà đỡ, cột chống) được thiết kế đảm bảo:
- An toàn chịu lực với hệ số sử dụng η ≤ 90%
- Độ võng trong giới hạn cho phép
- Đảm bảo ổn định trong thi công
- Thuận tiện cho thi công và tháo dỡ

---

## X. BIỆN PHÁP THI CÔNG

### X.1. Lắp dựng cốp pha

1. Lắp panel theo thiết kế
2. Kiểm tra cao độ, độ phẳng
3. Neo chằng theo thiết kế

### X.2. Đổ bê tông

1. Kiểm tra cốp pha trước khi đổ
2. Đổ bê tông theo lớp ≤ [XX] m
3. Đầm kỹ, không đầm vào cốp pha

### X.3. Tháo cốp pha

1. Chờ đạt cường độ theo yêu cầu
2. Tháo theo trình tự: side form → beam bottom → slab
3. Không tập trung tải trọng

---

## XI. BẢN VẼ ĐÍNH KÈM

| STT | Ký hiệu | Mô tả |
|-----|---------|--------|
| 1 | [XX] | Bản vẽ cốp pha sàn |
| 2 | [XX] | Bản vẽ cốp pha dầm |
| 3 | [XX] | Sơ đồ neo chằng |

---

## XII. PHỤ LỤC

### Phụ lục A: Bảng tra vật liệu

### Phụ lục B: Hệ số

### Phụ lục C: Kết quả tính toán chi tiết

---

**NGƯỜI LẬP**

```
Họ tên: _______________________
Chức vụ: Kỹ sư Kết cấu
Ký:     _______________________
Ngày:   _______________________
```

---

*Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
