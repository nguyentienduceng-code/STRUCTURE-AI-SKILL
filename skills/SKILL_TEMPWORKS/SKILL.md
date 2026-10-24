---
name: SKILL_TEMPWORKS
version: 1.0.0
last_updated: 2026-10-18
description: "Kỹ sư Temporary Works AI: Thiết kế cốp pha sàn (slab formwork), cốp pha cột, cốp pha tường, hệ thống cây chống (shoring), kiểm tra ổn định thi công. Kích hoạt khi: cốp pha, coffa, cây chống, shoring, bracing, temporary works, ván khuôn."
status: PRODUCTION
roadmap: "v1.0.0 — Full Production (Sprint 3)"
depends_on: ["Structural_Design_Engineer", "SKILL_GEOTECH", "Cost_Estimator"]
---

# SKILL_TEMPWORKS — Temporary Works Design

> **Phiên bản:** v1.0.0 PRODUCTION
> **Mục đích:** Thiết kế và kiểm tra các kết cấu tạm thời phục vụ thi công
> **Tiêu chuẩn:** ACI 347-04, TCVN 4453:1995
> **Cập nhật:** 2026-10-18 — v1.0.0 Production (Sprint 3)

---

## 1. TỔNG QUAN

**SKILL_TEMPWORKS** thiết kế và kiểm tra các kết cấu tạm thời phục vụ thi công: cốp pha (formwork), cây chống (shoring), hệ giằng (bracing).

### 1.1 Các Module Đã Triển Khai

| Module | Trạng thái | Mô tả |
|--------|-------------|--------|
| **Slab Formwork** | ✅ v0.2.0 | Thiết kế cốp pha sàn |
| **Column Formwork** | ✅ **v1.0.0** | Thiết kế cốp pha cột |
| **Wall Formwork** | ✅ **v1.0.0** | Thiết kế cốp pha tường |
| **Shoring System** | ✅ **v1.0.0** | Thiết kế hệ thống cây chống |
| Stability Analysis | ⏳ Planned | Kiểm tra ổn định |
| Cost Estimate | ⏳ Planned | Dự toán chi phí |

### 1.2 Entry Points

```
calculators/
├── calc_formwork_slab.py       ← Module 1: Cốp pha sàn ✅
├── calc_formwork_column.py     ← Module 2: Cốp pha cột ✅ v1.0.0
├── calc_formwork_wall.py       ← Module 3: Cốp pha tường ✅ v1.0.0
├── calc_shoring_system.py       ← Module 4: Hệ thống cây chống ✅ v1.0.0
└── calc_stability.py           ← Module 5: Kiểm tra ổn định (Planned)
```

---

## 2. SỬ DỤNG

### 2.1 Cốp pha sàn (Slab Formwork)

```bash
python calculators/calc_formwork_slab.py --thickness 250 --span 6.0 --grade B30
python calculators/calc_formwork_slab.py -t 200 -s 5.0 -g B25 --verbose --json
```

### 2.2 Cốp pha cột (Column Formwork)

```bash
python calculators/calc_formwork_column.py --width 400 --height 3000 --grade B30 --rate 1.0
python calculators/calc_formwork_column.py -w 500 -h 4000 -g B25 -r 2.0 --json
```

### 2.3 Cốp pha tường (Wall Formwork)

```bash
python calculators/calc_formwork_wall.py --height 3000 --thickness 200 --grade B30 --rate 1.0
python calculators/calc_formwork_wall.py -h 4000 -t 250 -g B25 -r 2.0 --json
```

### 2.4 Hệ thống cây chống (Shoring System)

```bash
python calculators/calc_shoring_system.py --height 3.0 --load 50 --system acrow
python calculators/calc_shoring_system.py -H 4.0 -L 80 -s ringlock --json
```

---

## 3. THAM SỐ CHUNG

### 3.1 Cốp pha sàn

| Tham số | Viết tắt | Mặc định | Mô tả |
|---------|-----------|-----------|--------|
| `--thickness` | `-t` | **BẮT BUỘC** | Chiều dày sàn (mm) |
| `--span` | `-s` | **BẮT BUỘC** | Nhịp sàn (m) |
| `--grade` | `-g` | `B30` | Mác bê tông |
| `--plywood` | `-p` | `18` | Chiều dày plywood (mm) |
| `--construction-load` | `-c` | `1.5` | Tải trọng thi công (kN/m²) |

### 3.2 Cốp pha cột

| Tham số | Viết tắt | Mặc định | Mô tả |
|---------|-----------|-----------|--------|
| `--width` | `-w` | **BẮT BUỘC** | Bề rộng cột (mm) |
| `--height` | `-h` | **BẮT BUỘC** | Chiều cao cột (mm) |
| `--grade` | `-g` | `B30` | Mác bê tông |
| `--rate` | `-r` | `1.0` | Tốc độ đổ (m/h) |
| `--temp` | `-t` | `25` | Nhiệt độ bê tông (°C) |

### 3.3 Cốp pha tường

| Tham số | Viết tắt | Mặc định | Mô tả |
|---------|-----------|-----------|--------|
| `--height` | `-h` | **BẮT BUỘC** | Chiều cao tường (mm) |
| `--thickness` | `-t` | **BẮT BUỘC** | Bề dày tường (mm) |
| `--grade` | `-g` | `B30` | Mác bê tông |
| `--rate` | `-r` | `1.0` | Tốc độ đổ (m/h) |

### 3.4 Hệ thống cây chống

| Tham số | Viết tắt | Mặc định | Mô tả |
|---------|-----------|-----------|--------|
| `--height` | `-H` | **BẮT BUỘC** | Chiều cao cây chống (m) |
| `--load` | `-L` | **BẮT BUỘC** | Tải trọng (kN) |
| `--system` | `-s` | `acrow` | Loại: acrow, tower, ringlock |
| `--spacing` | — | `0.9` | Cự ly cây chống (m) |

---

## 4. ĐẦU RA (OUTPUT)

### 4.1 JSON Structure

```json
{
  "slab_thickness": 250,
  "slab_span": 6.0,
  "concrete_grade": "B30",
  "total_load": 8.25,
  "plywood_span": 0.65,
  "eta_plywood": 0.68,
  "eta_beam": 0.72,
  "eta_shore": 0.45,
  "all_pass": true,
  "warnings": [],
  "recommendations": ["Plywood η=0.68 ≤ 0.7 — Có thể tối ưu"],
  "standard_method": "ACI 347-04 / TCVN 4453:1995",
  "calculation_logs": [...]
}
```

### 4.2 Chỉ số Sử dụng (η)

| η | Mã màu | Kết luận | Hành động |
|---|---|---|---|
| ≤ 0.70 | 🟢 | An toàn, có dư | Đạt — xem xét Value Engineering |
| 0.70 – 0.90 | 🟡 | Đạt, hợp lý | Đạt — thiết kế tối ưu |
| 0.90 – 1.00 | 🟠 | Đạt nhưng sát ngưỡng | Cảnh báo lưu ý |
| > 1.00 | 🔴 | KHÔNG ĐẠT | Yêu cầu tăng tiết diện |

---

## 5. TÍCH HỢP VỚI SKILLS KHÁC

### 5.1 Data Flow

```
User: "Thiết kế cốp pha sàn tầng 3"
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  SKILL_TEMPWORKS                                             │
│  - Parse input (thickness, span, grade)                     │
│  - Calculate loads                                          │
│  - Design plywood, beams, shores                           │
│  - Return η and recommendations                            │
└───────────────────────────────────────────────────────────────┘
    │
    ├─► Cost_Estimator (tính chi phí cốp pha)
    │
    ├─► Technical_Illustrator (vẽ sơ đồ bố trí)
    │
    └─► SKILL_RFI (xin phê duyệt tempworks)
```

---

## 6. TIÊU CHUẨN ÁP DỤNG

| Tiêu chuẩn | Năm | Phạm vi |
|---|---|---|
| TCVN 4453 | 1995 | Công tác bê tông và BTCT |
| TCVN 2737 | 2023 | Tải trọng và tác động |
| ACI 347 | 2004 | Formwork for Concrete |
| ACI 318 | 2019 | Concrete Structures |
| Eurocode 2 | 2004 | Concrete Structures |
| Eurocode 3 | 2005 | Steel Structures |

---

## 7. CÁC CÔNG THỨC CHÍNH

### 7.1 Áp lực bê tông tươi (Lateral Pressure)

```
P_max = γ_c × h + C_v × V/t + C_w × γ_c × w
```
- γ_c = 24-25 kN/m³ (tỷ trọng bê tông)
- h = chiều cao cột bê tông đã đổ
- V = tốc độ đổ (m/h)
- t = nhiệt độ bê tông (°C)
- C_v = 1.0 cho V < 2m/h, 1.5 cho V ≥ 2m/h
- C_w = 1.0 cho w ≥ 100mm

### 7.2 Độ võng plywood

```
δ = 5qL⁴ / (384EI)
δ_allow = L/270 (cho bề mặt đẹp)
δ_allow = L/360 (cho kết cấu)
```

### 7.3 Tải trọng cây chống

```
P_shore = q_total × A_shore
η = P_shore / P_capacity
```

### 7.4 Kiểm tra ổn định (Euler Buckling)

```
P_E = π²EI / (KL)²
FS = P_capacity / P_actual ≥ 1.5
```

---

## 8. ROADMAP

### Phase 1 (v0.2.0) ✅ HOÀN THÀNH
- [x] Slab formwork design
- [x] Plywood deflection check
- [x] Beam spacing optimization
- [x] Shore load calculation

### Phase 2 (v1.0.0) ✅ **SPRINT 3 - HOÀN THÀNH**
- [x] Column formwork design (calc_formwork_column.py)
- [x] Wall formwork design (calc_formwork_wall.py)
- [x] Shoring system design (calc_shoring_system.py)
- [x] Lateral pressure calculation
- [x] Tie rod design

### Phase 3 (v1.1.0) — Q1/2027
- [ ] Shoring system design (Advanced)
- [ ] Bracing analysis
- [ ] Construction sequence

### Phase 4 (v1.5.0) — Q2/2027
- [ ] Cost integration
- [ ] Drawing generation
- [ ] RFI generation

---

## CHANGELOG

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-18 | Sprint 3: Column, Wall, Shoring modules production |
| 0.2.0 | 2026-10-12 | Phase 1 Active: Slab formwork design module |
| 0.1.0 | 2026-09-25 | Initial placeholder |
