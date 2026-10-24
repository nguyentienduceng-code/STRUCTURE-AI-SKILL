# 📐 Hướng Dẫn Trình Bày Công Thức Toán Học

> **Phiên bản:** 1.0 — Cập nhật: 2026-10-13
> **Áp dụng cho:** Mọi thuyết minh tính toán, tờ trình, báo cáo

---

## 1. Nguyên Tắc Chung

| Nguyên tắc | Giải thích |
|-------------|-------------|
| **Công thức gốc → Số → Kết quả** | Mỗi bước trình bày đủ: `Công thức → Thế số → Kết quả` |
| **Đơn vị theo sau giá trị** | `180 kNm`, `14.5 MPa`, `560 mm` |
| **Làm tròn hợp lý** | Cường độ: 1 chữ số thập phân; Kích thước: 0 mm; Diện tích: 1 mm² |
| **η kèm %** | `η = 0.82 (82%)` hoặc `η = 78%` |

---

## 2. Bảng Tra Cứu Ký Hiệu

### 2.1 Ký Hiệu Hy Lạp (Greek Letters)

| LaTeX | Hiển thị | Ý nghĩa |
|-------|-----------|---------|
| `α` | α | Hệ số |
| `β` | β | Hệ số |
| `γ` | γ | Hệ số vật liệu |
| `δ` | δ | Độ dịch chuyển |
| `ε` | ε | Biến dạng |
| `ζ` | ζ | Tỷ số |
| `η` | η | Hệ số sử dụng |
| `θ` | θ | Góc |
| `λ` | λ | Hệ số mảnh |
| `μ` | μ | Hệ số ma sát |
| `ξ` | ξ | Tỷ số |
| `π` | π | Số Pi |
| `ρ` | ρ | Cường độ chịu kéo |
| `σ` | σ | Ứng suất |
| `φ` | φ | Đường kính |
| `ψ` | ψ | Hệ số |
| `ω` | ω | Tần số góc |

### 2.2 Chỉ Số Trên/Dưới

| LaTeX | Hiển thị | Ý nghĩa |
|-------|-----------|---------|
| `x²` | x² | Bình phương |
| `x³` | x³ | Lập phương |
| `x₀` | x₀ | Giá trị ban đầu |
| `x₁` | x₁ | Giá trị 1 |
| `xₛ` | xₛ | Của thép (steel) |
| `x_b` | xᵦ | Của bê tông |
| `A_s` | Aₛ | Diện tích cốt thép |
| `R_b` | Rᵦ | Cường độ chịu nén BT |
| `f_y` | fᵧ | Giới hạn chảy thép |

### 2.3 Ký Hiệu Toán

| LaTeX | Hiển thị | Ý nghĩa |
|-------|-----------|---------|
| `±` | ± | Dương trừ |
| `×` | × | Nhân |
| `÷` | ÷ | Chia |
| `·` | · | Nhân (dot) |
| `≤` | ≤ | Nhỏ hơn hoặc bằng |
| `≥` | ≥ | Lớn hơn hoặc bằng |
| `≠` | ≠ | Khác |
| `√` | √ | Căn bậc hai |
| `∑` | ∑ | Tổng |
| `∫` | ∫ | Tích phân |
| `∂` | ∂ | Đạo hàm riêng |
| `∞` | ∞ | Vô cùng |
| `≈` | ≈ | Xấp xỉ |
| `≡` | ≡ | Tương đương |

---

## 3. Template Trình Bày Công Thức

### 3.1 Template 1: Cơ Bản (Một Công Thức)

```markdown
**Tính chiều cao vùng nén:**

$$\alpha_f = \frac{M}{R_b \cdot b \cdot h_0^2}$$

Thế số:
- M = 180 kNm = 180×10⁶ Nmm
- R_b = 14.5 MPa = 14.5 N/mm²
- b = 300 mm
- h₀ = 560 mm

$$\alpha_f = \frac{180 \times 10^6}{14.5 \times 300 \times 560^2} = 0.245$$

**Kết luận:** ξ = 0.245 < ξ_R = 0.44 → **Đạt** ✅
```

### 3.2 Template 2: Bảng Log Tính Toán

```markdown
| Bước | Công thức | Thế số | Kết quả |
|------|-----------|--------|---------|
| 1 | ξ = α_f | Thế trực tiếp | ξ = 0.245 |
| 2 | η = ξ/ξ_R | 0.245/0.44 | η = 0.56 (56%) |
| 3 | A_s,min = 0.001×b×h | 0.001×300×600 | 180 mm² |
| 4 | A_s,yêu cầu = α_s×b×h₀×R_b/f_y | 0.238×300×560×14.5/280 | 1580 mm² |
```

### 3.3 Template 3: Kiểm Tra Điều Kiện

```markdown
### Kiểm tra hàm lượng cốt thép

**Điều kiện:** μ_min ≤ μ ≤ μ_max

Trong đó:
- μ = A_s/(b×h₀) = 1580/(300×560) = 0.0094 = 0.94%
- μ_min = 0.05% (TCVN 5574:2018, Điều 10.3.5)
- μ_max = 0.06×ξ_R×R_b/f_y = 0.06×0.44×14.5/280 = 0.024 = 2.4%

**Kết luận:** 0.05% ≤ 0.94% ≤ 2.4% → **Đạt** ✅

η = μ/μ_max = 0.94%/2.4% = 0.39 (39%) → 🟢 An toàn

> (*) **Ghi chú về α_R và ξ_R (TCVN 5574:2018):** Theo `STANDARDS_LOCK.md` §3.1 và TCVN 5574:2018, giá trị mặc định cho cốt thép CB400-V chuẩn là `α_R = 0.39` (với `ξ_R ≈ 0.493`). Giá trị `ξ_R = 0.44` hoặc `α_R = 0.44` trong ví dụ trên áp dụng cho các mác thép riêng biệt (như CB300-V hoặc khi xét điều kiện làm việc đặc biệt). Khi tính toán chính thức phải ưu tiên dùng `α_R = 0.39` mặc định cho CB400-V.
```

### 3.4 Template 4: So Sánh Phương Án

```markdown
| Phương án | Kích thước | A_s (mm²) | Thép | η | Kết luận |
|-----------|------------|-----------|------|---|----------|
| PA1 | 300×600 | 1580 | 3D18 | 56% | ✅ Đạt |
| PA2 | 250×550 | 1420 | 3D16 | 68% | ✅ Đạt |
| PA3 | 300×500 | 1650 | 4D18 | 82% | ⚠️ Sát ngưỡng |

**Khuyến nghị:** PA2 — η = 68% có dư an toàn + tiết kiệm 10% thép
```

---

## 4. Các Công Thức Phổ Biến

### 4.1 Bê Tông Cốt Thép (TCVN 5574:2018)

| Công thức | LaTeX |
|-----------|-------|
| Hệ số chuyển đổi | `α_f = M/(R_b × b × h₀²)` |
| Tỷ số cốt thép | `ξ = α_f` |
| Hệ số sử dụng | `η = ξ/ξ_R` |
| Diện tích cốt thép | `A_s = M/(ζ × f_y × h₀)` |
| Điều kiện hàm lượng | `μ_min ≤ A_s/(b×h₀) ≤ μ_max` |

### 4.2 Kết Cấu Thép (TCVN 5575:2024)

| Công thức | LaTeX |
|-----------|-------|
| Ứng suất pháp | `σ = N/A ± M/W` |
| Kiểm tra ổn định | `σ ≤ φ × f` |
| Hệ số uốn dọc | `φ = 1 - λ²/(3000)` |
| Độ võng | `f = 5qL⁴/(384EI)` |

### 4.3 Nền Móng

| Công thức | LaTeX |
|-----------|-------|
| Sức chịu tải cọc | `P_sct = Q_c + Q_s` |
| Ma sát bên | `Q_s = u × Σ(f_si × l_i)` |
| Đầu cọc | `Q_c = R × A` |
| Độ lún | `S = S_i + S_c` |

---

## 5. Ví Dụ Hoàn Chỉnh

### Ví dụ: Tính cốt thép dầm

```
═══════════════════════════════════════════════════════════════════
                        TÍNH CỐT THÉP DẦM D1
═══════════════════════════════════════════════════════════════════

Số liệu đầu vào:
┌─────────────────────────────────────────────────────────────────┐
│ Thông số              │ Giá trị    │ Đơn vị   │ Căn cứ        │
├───────────────────────┼────────────┼───────────┼───────────────│
│ Mô men tính toán (M)  │ 180        │ kNm       │ Từ ETABS      │
│ Cạnh b (b)            │ 300        │ mm        │ Bản vẽ       │
│ Cạnh h (h)            │ 600        │ mm        │ Bản vẽ       │
│ Chiều cao làm việc    │ 560        │ mm        │ h₀ = h - a    │
│ Cấp bê tông           │ B22.5      │ -         │ R_b = 14.5MPa │
│ Thép chịu kéo         │ CB300      │ -         │ f_y = 280MPa  │
│ Lớp bê tông bảo vệ   │ 25         │ mm        │ a = 35mm      │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

Bước 1: Xác định hệ số α_f

  Công thức:     α_f = M / (R_b × b × h₀²)

  Thế số:        α_f = 180×10⁶ / (14.5 × 300 × 560²)
                = 180,000,000 / (14.5 × 300 × 313,600)
                = 180,000,000 / 1,364,160,000
                = 0.132

  Kết quả:       α_f = 0.132

───────────────────────────────────────────────────────────────────

Bước 2: Xác định tỷ số ξ

  Tra bảng TCVN 5574:2018, Điều 6.1.2, với α_f = 0.132:

  ξ = 0.141

  Kiểm tra: ξ = 0.141 < ξ_R = 0.44 → Vùng nén không phá hoại giòn

───────────────────────────────────────────────────────────────────

Bước 3: Kiểm tra hệ số sử dụng

  Công thức:     η = ξ / ξ_R

  Thế số:        η = 0.141 / 0.44

  Kết quả:       η = 0.32 (32%)

  Màu:           🟢 An toàn (η < 0.70)

───────────────────────────────────────────────────────────────────

Bước 4: Tính diện tích cốt thép

  Công thức:     ζ = 1 - 0.5×ξ
                = 1 - 0.5×0.141
                = 0.930

  Công thức:     A_s = M / (ζ × f_y × h₀)

  Thế số:        A_s = 180×10⁶ / (0.930 × 280 × 560)
                = 180,000,000 / 145,766,400
                = 1235 mm²

  Kết quả:       A_s = 1235 mm²

───────────────────────────────────────────────────────────────────

Bước 5: Kiểm tra hàm lượng cốt thép

  Công thức:     μ = A_s / (b × h₀) × 100%

  Thế số:        μ = 1235 / (300 × 560) × 100%
                = 0.0073 × 100%
                = 0.73%

  Tra TCVN 5574:2018, Điều 10.3.5:
  - μ_min = 0.05%
  - μ_max = 2.4% (với ξ = 0.141)

  Kiểm tra:  0.05% ≤ 0.73% ≤ 2.4% → 🟢 Đạt

═══════════════════════════════════════════════════════════════════

KẾT LUẬN:

┌─────────────────────────────────────────────────────────────────┐
│  Cấu kiện: Dầm D1, tầng 3                                     │
│  Cốt thép yêu cầu: A_s = 1235 mm²                             │
│  Chọn: 3D22 → A_s,thực tế = 3 × 380 = 1140 mm²               │
│  Hệ số sử dụng: η = 92% → ⚠️ Gần ngưỡng (0.90-1.00)          │
│                                                                 │
│  Khuyến nghị: Tăng lên 3D25 → A_s = 3 × 490 = 1470 mm²       │
│               η = 84% → 🟡 Tối ưu hơn                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Mẫu Bảng Tổng Hợp cho Report

```markdown
| STT | Cấu kiện | M (kNm) | b×h (mm) | R_b (MPa) | α_f | ξ | η | A_s,yc (mm²) | A_s,chọn | Ghi chú |
|-----|-----------|----------|-----------|-----------|-----|---|---|---------------|----------|---------|
| 1 | Dầm D1-T3 | 180 | 300×600 | 14.5 | 0.132 | 0.141 | 32% | 1235 | 3D22 | OK |
| 2 | Dầm D2-T3 | 145 | 250×500 | 14.5 | 0.156 | 0.170 | 39% | 980 | 3D20 | OK |
| 3 | Cột C1-T3 | 280 | 400×400 | 14.5 | - | - | 45% | 2100 | 8D20 | OK |
```

---

## 7. Sử Dụng Trong Hệ Thống

### 7.1 Khi viết Markdown (.md)

```markdown
Tính hệ số α_f:

$$\alpha_f = \frac{M}{R_b \times b \times h_0^2}$$

Thế số:
- M = 180 kNm
- R_b = 14.5 MPa  
- b = 300 mm
- h₀ = 560 mm

$$\alpha_f = \frac{180 \times 10^6}{14.5 \times 300 \times 560^2} = 0.132$$
```

### 7.2 Khi xuất DOCX

```javascript
// Su dung math_renderer.js
const {render} = require('./math_renderer');

const formula = "\\alpha_f = \\frac{M}{R_b \\cdot b \\cdot h_0^2}";
const result = render(formula);

// Lay unicode cho hien thi
console.log(result.text); // α_f = M/(R_b·b·h₀²)
```

---

**Lưu ý:** Hệ thống hiện tại dùng **Unicode** để hiển thị ký hiệu toán học trong DOCX. Để có hình ảnh công thức đẹp hơn (như trong Word dùng Equation Editor), cần cài đặt thêm `pdflatex` và `ImageMagick`.

---

*Cập nhật: 2026-10-13*
