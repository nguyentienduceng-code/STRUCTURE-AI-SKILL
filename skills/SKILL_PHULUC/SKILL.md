---
name: SKILL_PHULUC
version: 1.0.0
last_updated: 2026-09-01
description: "Skill Phụ lục Tính toán chuyên nghiệp: Tạo phụ lục tính toán kết cấu đầy đủ theo chuẩn của đơn vị tư vấn thiết kế độc lập. Kích hoạt khi nhắc đến: phụ lục tính toán, thuyết minh chi tiết, bảng tính, giải trình kỹ thuật, báo cáo kỹ thuật đầy đủ, calculation sheet."
---

# SKILL_PHULUC — Phụ lục Tính toán Kết cấu Chuyên nghiệp

## Tổng quan

**SKILL_PHULUC** tạo **Phụ lục Tính toán Kết cấu** đầy đủ theo chuẩn của đơn vị tư vấn thiết kế độc lập. Khác với SKILL_CALC_REPORT (tóm tắt), SKILL_PHULUC xuất phụ lục với **step-by-step** đầy đủ.

---

## Sự khác biệt với SKILL_CALC_REPORT

| Tiêu chí | SKILL_CALC_REPORT | SKILL_PHULUC |
|-----------|-------------------|---------------|
| **Độ chi tiết** | Tóm tắt | Step-by-step đầy đủ |
| **Intermediate values** | Không | Có tất cả |
| **Công thức trung gian** | Chỉ kết quả | Đầy đủ từng bước |
| **Bảng tra vật liệu** | Ngắn gọn | Đầy đủ |
| **Phụ lục kỹ thuật** | Không | Có |
| **Dùng cho** | Internal review | **Thẩm tra/chấp thuận** |

---

## Các loại Phụ lục được hỗ trợ

| Loại | File template | Mô tả |
|------|---------------|--------|
| **TMTT Đầy đủ** | `TMTT_FULL.md` | Thuyết minh đầy đủ 12 chương |
| **TMTT Bê tông** | `PARTIAL_BE_TONG.md` | Phụ lục kết cấu BTCT |
| **TMTT Thép** | `PARTIAL_THEP.md` | Phụ lục kết cấu thép |
| **Dầm BTCT** | `APPENDIX_BEAM_RC.md` | Dầm bê tông cốt thép |
| **Cột BTCT** | `APPENDIX_COLUMN_RC.md` | Cột bê tông cốt thép |
| **Dầm thép** | `APPENDIX_STEEL_BEAM.md` | Dầm kết cấu thép |
| **Kết cấu thép** | `APPENDIX_STEEL_MEMBER.md` | Cấu kiện thép tổng hợp |
| **Móng** | `APPENDIX_FOUNDATION.md` | Móng đơn, băng, cọc |
| **Liên kết** | `APPENDIX_CONNECTION.md` | Liên kết bu lông, hàn |

### Templates đặc biệt

| Template | Mục đích | Đặc điểm |
|---------|-----------|-----------|
| `TMTT_FULL.md` | Thuyết minh toàn bộ | 12 chương + PHỤ LỤC theo hạng mục |
| `PARTIAL_*.md` | Phụ lục 1 hạng mục | Format chuẩn TCVN, step-by-step |
| `APPENDIX_*.md` | Phụ lục 1 cấu kiện | Chi tiết từng bước tính |

### Font chuẩn

| Element | Font | Size | Style |
|---------|------|------|-------|
| Normal text | **Arial** | 12pt | Normal |
| Heading 1 | Arial | 14pt | Bold |
| Heading 2 | Arial | 13pt | Bold |
| Heading 3 | Arial | 12pt | Bold |
| Table text | Arial | 11pt | Normal |
| Code/Formula | Courier New | 10pt | Normal |

### Công thức chuẩn

Xem: `references/FORMULA_GUIDE.md`

```markdown
# Ví dụ công thức:
A_s,req = M_ed / (f_y/γ_s × z)

η = A_s,req / A_s,prov ≤ 1.0

χ_LT = 1 / (Φ_LT + √(Φ_LT² - λ_LT²))
```

### Generator DOCX

```bash
python docx_generator.py \
    --input TMTT.md \
    --output TMTT.docx \
    --cover "Công trình ABC" \
    --title "Thuyết minh Kết cấu"
```

---

## Cấu trúc Phụ lục (Standard)

Mỗi phụ lục có cấu trúc chuẩn:

```
1. THÔNG TIN CHUNG
   └── Tiêu chuẩn áp dụng

2. VẬT LIỆU
   ├── Bê tông
   ├── Cốt thép
   └── Đặc tính tiết diện

3. TẢI TRỌNG
   ├── Tĩnh tải
   ├── Hoạt tải
   └── Tổ hợp

4. SƠ ĐỒ KẾT CẤU
   └── Hình vẽ sơ đồ

5. NỘI LỰC
   └── Bảng nội lực

6. TÍNH TOÁN CHI TIẾT
   ├── Step 1: ...
   ├── Step 2: ...
   └── Step N: ...

7. BẢNG TỔNG HỢP
   ├── Cốt thép đã chọn
   └── Kiểm tra η

8. KẾT LUẬN

9. PHỤ LỤC
   ├── Bảng tra vật liệu
   ├── Hệ số
   └── Biểu đồ

10. CHỮ KÝ XÁC NHẬN
```

---

## Luồng làm việc

### 1. Nhận yêu cầu

```
User: "Tạo phụ lục tính toán cho dầm B1"
```

### 2. Xác định loại cấu kiện

```
→ beam_rc (Dầm BTCT)
→ column_rc (Cột BTCT)
→ steel_beam (Dầm thép)
→ foundation (Móng)
→ connection (Liên kết)
```

### 3. Thu thập dữ liệu

Đọc từ:
- Kết quả tính toán của SKILL_CALC
- JSON data từ calculator scripts
- ETABS/SAFE output
- Thông tin user cung cấp

### 4. Điền Template

Sử dụng `appendix_generator.py`:

```bash
python appendix_generator.py \
    --type beam_rc \
    --input calc_result.json \
    --output PHULUC_Dam_B1.md
```

### 5. Review Gate

**HIỂN THỊ** phụ lục đầy đủ:
- Tất cả bước tính toán
- Bảng tổng hợp
- Hình vẽ sơ đồ

**HỎI** User:
> *"Phụ lục đã đầy đủ chưa? Anh/chị muốn điều chỉnh gì không?"*

### 6. Xuất file

- **.md** — Thuyết minh gốc
- **.docx** — Báo cáo Word
- **.pdf** — Bản in

---

## Quy tắc quan trọng

### 1. Step-by-Step bắt buộc

Mỗi bước tính toán phải có:
```
Bước N: [Tên bước]
Giả thiết/Cho trước: [giá trị]
Công thức: [công thức]
Thế số: [thế giá trị]
Kết quả: [kết quả]
Kiểm tra: [pass/fail]
```

### 2. Units consistency

- **Lực**: kN
- **Momen**: kNm
- **Chiều dài**: mm (tính toán), m (sơ đồ)
- **Ứng suất**: MPa
- **Diện tích**: mm²

### 3. Citation đầy đủ

Mỗi công thức phải có citation:
```
M_rd = f_y × A_s × z    [TCVN 5574:2018 — Công thức 5.1]
```

### 4. Tất cả giá trị phải có ý nghĩa

❌ Không được để placeholder trống
✅ Tất cả giá trị phải được tính hoặc lấy từ input

---

## Cau truc thu muc

```
SKILL_PHULUC/
├── SKILL.md                    <- Entry Point
├── generator.py               <- Generator script
├── references/
|   ├── MATERIAL_TABLES.md    <- Bang tra vat lieu
|   └── FORMULA_GUIDE.md      <- Huong dan cong thuc
└── templates/                <- Templates (placeholder - thuc te su dung tu Structural_Design_Engineer)
```

**Luu y:** Templates thuc te nam tai `Structural_Design_Engineer/templates/appendix/`:
```
Structural_Design_Engineer/templates/appendix/
├── APPENDIX_BEAM_RC.md       <- Dau BTCT
├── APPENDIX_COLUMN_RC.md      <- Cot BTCT
├── APPENDIX_STEEL_BEAM.md    <- Dam thep
├── APPENDIX_STEEL_MEMBER.md  <- Cau kien thep
├── APPENDIX_FOUNDATION.md     <- Mong
└── APPENDIX_CONNECTION.md     <- Lien ket
```

---

## Input JSON format (TMTT Đầy đủ)

```json
{
  "project_name": "Công trình ABC",
  "project_code": "ABC-2024",

  "vat_lieu_be_tong": "Bê tông B30: R_b=17.0 MPa, R_bt=1.2 MPa",
  "vat_lieu_thep_can": "Thép SS400: f_y=235 MPa, f_u=400 MPa",
  "lop_be_tong_bao_ve": "Lớp bảo vệ: 30mm (thành, trần), 40mm (đáy)",
  "noi_dung_ve_net": "Bề rộng vết nứt: a_max = 0.3mm cho môi trường III",
  "noi_dung_chong_tham": "Mác chống thấm: W6 cho bể nước",

  "phu_luc_items": [
    {
      "ten_hang_muc": "NHÀ TRÌNH BÀY",
      "has_mo_hinh": true,
      "has_tai_trong": true,
      "has_mong": true,
      "has_khung": true,
      "has_xa_go": true,
      "has_lien_ket": true
    },
    {
      "ten_hang_muc": "BỂ NƯỚC NGẦM",
      "has_mo_hinh": true,
      "has_tai_trong": true,
      "has_mong": true,
      "has_khung": false,
      "has_xa_go": false,
      "has_lien_ket": false
    }
  ],

  "calculator": "Nguyen Van A",
  "nguoi_tinh": "Nguyễn Văn A",
  "nguoi_kiem_tra": "Trần Văn B",
  "nguoi_duyet": "Lê Văn C"
}
```

## Input JSON format (Phụ lục Bê tông)

```json
{
  "project_name": "Công trình ABC",
  "project_code": "ABC-2024",
  "item_name": "Dầm B1",

  "concrete_grade": "B30",
  "steel_grade_rc": "CB400",

  "geometry": {
    "b": 200,
    "h": 400,
    "L": 6000,
    "a": 35
  },

  "forces": [
    {"section": "Gối A", "M": -45.2, "V": 85.5, "N": 0, "combo": "TH1"},
    {"section": "Nhịp 1", "M": 62.8, "V": 0, "N": 0, "combo": "TH1"},
    {"section": "Gối B", "M": -78.5, "V": 125.3, "N": 0, "combo": "TH1"}
  ],

  "rebar": {
    "top": {"n": 3, "dia": 20},
    "bottom": {"n": 2, "dia": 20},
    "stirrup": {"dia": 8, "s1": 100, "s2": 200}
  },

  "calculator": "Nguyen Van A",
  "calc_date": "01/09/2024"
}
```

---

## Ví dụ Output

```markdown
# PHỤ LỤC TÍNH TOÁN KẾT CẤU
## Cấu kiện: DẦM B1

---

## 1. THÔNG TIN CHUNG

| Thông tin | Giá trị |
|-----------|---------|
| Công trình | Công trình ABC |
| Mã số | ABC-2024 |
| Tiêu chuẩn | TCVN 5574:2018 |

---

## 6. TÍNH TOÁN CHI TIẾT

### 6.1 Kiểm tra cốt thép chịu uốn

**Bước 1:** Giả thiết chiều cao vùng nén
```
α = 0.45
a = α × d = 0.45 × 365 = 164 mm
```

**Bước 2:** Tính A_s,yêu cầu
```
A_s,req = M_ed / (f_y/γ_s × z)
        = 78.5 × 10⁶ / (340/1.15 × 283)
        = 78500 / 295.65 × 10³
        = 265.5 mm²
```

**Kiểm tra:** η = 265.5 / 763 = 0.348 < 1.0 ✓

---

## 10. CHỮ KÝ XÁC NHẬN

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|---------|---------|------|
| Người tính | Nguyen Van A | | 01/09/2024 |
| Kiểm tra | | | |
| Duyệt | | | |
```

---

## Integration với các skill khác

### Với SKILL_CALC

SKILL_PHULUC nhận input từ SKILL_CALC:
- Kết quả tính toán
- Nội lực
- Cốt thép đã chọn

### Với SKILL_REPORT

SKILL_PHULUC xuất output qua SKILL_REPORT:
- Định dạng .docx
- Header/Footer chuẩn
- Số trang

### Với Technical_Illustrator

SKILL_PHULUC nhúng hình vẽ từ Technical_Illustrator:
- Sơ đồ kết cấu
- Mặt cắt tiết diện
- Chi tiết liên kết

---

## Lưu ý quan trọng

1. **SKILL_PHULUC không thay thế SKILL_CALC_REPORT**
   - SKILL_CALC_REPORT: Tóm tắt nhanh, internal use
   - SKILL_PHULUC: Đầy đủ chi tiết, external submission

2. **Phụ lục phải do kỹ sư có chứng chỉ ký**
   - AI chỉ hỗ trợ tạo draft
   - Con người phải kiểm tra và ký

3. **Citation phải đầy đủ**
   - Mỗi công thức cần citation
   - Mỗi hệ số cần nguồn

---

**Version:** 1.0.0
**Last Updated:** 2026-09-01
