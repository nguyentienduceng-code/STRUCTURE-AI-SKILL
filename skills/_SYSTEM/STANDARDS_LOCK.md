# STANDARDS_LOCK.md — Nguồn Sự thật Duy nhất về Phiên bản Tiêu chuẩn

> **Bắt buộc theo `AGENTS.md` điều 1 và điều 10.**
> Mọi skill, mọi script, mọi báo cáo PHẢI lấy phiên bản tiêu chuẩn từ bảng này.
> Không file nào khác được tự khai báo phiên bản riêng.
>
> **Cập nhật:** 2026-08-31 — v2.4.0 (Reporting Upgrade v4.1)
> **Thư mục PDF gốc:** `Design_Evaluation/standards/`

---

## 1. Bảng Chốt Phiên bản (Normative)

| Lĩnh vực | Phiên bản CHUẨN (dùng cho hồ sơ mới) | Phiên bản CŨ (chỉ đối chiếu hồ sơ cũ) | File PDF chuẩn |
|---|---|---|---|
| Tải trọng & tác động | **TCVN 2737:2023** | TCVN 2737:1995 | `TCVN/1. TCVN 2737-2023_...pdf` |
| Động đất | **TCVN 9386:2025** (P1 + P5) | TCVN 9386:2012 | `TCVN/2a.` + `TCVN/2b.` |
| Bê tông cốt thép | **TCVN 5574:2018** | TCVN 5574:2012 | `TCVN/10.TCVN 5574-2018_...pdf` |
| Kết cấu thép | **TCVN 5575:2024** | TCVN 5575:2012 | `TCVN/13. TCVN 5575-2024_...pdf` |
| Khối xây | **TCVN 5573:2025** | TCVN 5573:2011 | `TCVN/12. TCVN 5573 2025_...pdf` |
| Móng cọc | **TCVN 10304:2025** | TCVN 10304:2014 | `TCVN/6. TCVN 10304 2025_...pdf` |
| Nền nhà & công trình | **TCVN 9362:2012** | — | `TCVN/5. TCVN 9362-2012_...pdf` |
| Thi công & nghiệm thu BTCT | **TCVN 4453:1995** | — | `TCVN/11. TCVN 4453-1995_...pdf` |
| Phân cấp công trình | **QCVN 03:2022** + **TT 02/2025/TT-BXD** | TT 06/2021 | `QCVN/3.` + `QCVN/3a.` |
| Số liệu tự nhiên (vùng gió, động đất) | **QCVN 02:2022** | QCVN 02:2009 | `QCVN/2. QCVN02-2022_...pdf` |
| An toàn cháy | **QCVN 06:2022** + Sửa đổi 1 | — | `QCVN/6.` + `QCVN/6a.` |
| Nhà chung cư | **QCVN 04:2021** | — | `QCVN/4. QCVN 04-2021_...pdf` |
| Quy hoạch xây dựng | **QCVN 01:2012** | — | `QCVN/1. QCVN01-2012_...pdf` |
| Khảo sát ĐCCT | **TCVN 9351:2012** + **BS/ASTM** (tùy dự án) | — | — |
| Tương quan SPT | **Bowles (1997) + Database TP.HCM** | — | — |
| Phân loại đất CPT | **Robertson (1990) + Lunne et al. (1997)** | — | — |


**Quy ước đặt tên file:** tiền tố `TK` trong tên file (VD `13TK. TCVN 5575-2012`) = phiên bản **tham khảo/đã thay thế**. Không dùng cho hồ sơ mới.

---

## 2. ⚠ Khoảng cách giữa Tiêu chuẩn Chốt và Công thức trong Script (Known Gap)

Đây là mục **quan trọng nhất** của file này. Một số script hiện cài đặt công thức theo phiên bản **cũ**. Script sẽ tự khai báo qua trường `Standard_Method` trong JSON output. AI phải đọc trường này và ghi đúng vào báo cáo — **không được ghi tên phiên bản mới nếu script chạy công thức phiên bản cũ**.

| Script | `Standard_Method` thực tế | Phiên bản chốt | Trạng thái |
|---|---|---|---|
| `Design_Evaluation/calculators/wind_load_calc.py` | TCVN 2737:2023 | TCVN 2737:2023 | ✅ Khớp |
| `Design_Evaluation/calculators/earthquake_load_calc.py` | TCVN 9386:2025 (P1 + P5) | TCVN 9386:2025 | ✅ Khớp |
| `Design_Evaluation/calculators/rc_flexure_design.py` | TCVN 5574:2018 | TCVN 5574:2018 | ✅ Khớp |
| `Design_Evaluation/calculators/deflection_check.py` | TCVN 5574:2018 (PL M) | TCVN 5574:2018 | ✅ Khớp |
| `Design_Evaluation/calculators/steel_member_check.py` | TCVN 5575:2012 | TCVN 5575:2024 | ⚠ **Lệch** — dùng cho hồ sơ đối chiếu theo 2012 |
| `Design_Evaluation/calculators/steel_member_check_v2024.py` | TCVN 5575:2024 | TCVN 5575:2024 | ✅ Khớp — dùng cho hồ sơ mới (khuyến nghị) |
| `Design_Evaluation/calculators/foundation_bearing.py` | TCVN 9362:2012 Đ.4.6.9 | TCVN 9362:2012 | ✅ Khớp |
| `Structural_Design_Engineer/scripts/calc_rc_section.py` | TCVN 5574:2018 | TCVN 5574:2018 | ✅ Khớp |
| `Structural_Design_Engineer/scripts/calc_steel_beam.py` | **EN 1993-1-1** (Eurocode 3) | TCVN 5575:2024 | ⚠ **Eurocode** — dùng cho hồ sơ cũ/đối chiếu quốc tế, KHÔNG phải TCVN |
| `Structural_Design_Engineer/scripts/calc_steel_connection.py` | **EN 1993-1-8** (Eurocode 3 Part 1-8) | TCVN 5575:2024 | ⚠ **Eurocode** — dùng cho hồ sơ cũ/đối chiếu quốc tế, KHÔNG phải TCVN |
| `Structural_Design_Engineer/scripts/calc_steel_beam_tcvn.py` | **TCVN 5575:2024** | TCVN 5575:2024 | ✅ Khớp — thay thế calc_steel_beam.py cho hồ sơ mới |
| `Structural_Design_Engineer/scripts/calc_steel_connection_tcvn.py` | **TCVN 5575:2024** | TCVN 5575:2024 | ✅ Khớp — thay thế calc_steel_connection.py cho hồ sơ mới |

**Hướng dẫn chọn script:** Với hồ sơ mới (từ 2026) → dùng `steel_member_check_v2024.py`, `calc_steel_beam_tcvn.py`, `calc_steel_connection_tcvn.py`. Với hồ sơ cũ đối chiếu → dùng script Eurocode và ghi rõ đang dùng EN.

**Xử lý bắt buộc khi gặp ⚠ Lệch:**

1. Báo cáo ghi đúng phiên bản mà script cài đặt (đọc từ `Standard_Method`), kèm dòng cảnh báo:
   > *"Kết quả tính theo phương pháp TCVN 5575:2012. TCVN 5575:2024 đã thay thế — cần kỹ sư kiểm tra lại theo bản 2024 trước khi dùng cho hồ sơ chính thức."*
2. Đưa mục này vào danh sách `UNVERIFIED` tại Review Gate.
3. **Không** tự đổi nhãn thành `TCVN 5575:2024` khi công thức chưa được cập nhật.

### Known Gap — Audit 2026-08-25

| Issue | Mô tả | Ảnh hưởng | Priority | Trạng thái |
|-------|-------|-----------|----------|------------|
| EUROCODE-GAP-01 | `calc_steel_beam.py` dùng EN 1993-1-1 | Không dùng cho hồ sơ chính thức | HIGH | ✅ **FIXED** — `calc_steel_beam_tcvn.py` |
| EUROCODE-GAP-02 | `calc_steel_connection.py` dùng EN 1993-1-8 | Không dùng cho hồ sơ chính thức | HIGH | ✅ **FIXED** — `calc_steel_connection_tcvn.py` |

**Action items:**
- [x] Viết lại `calc_steel_beam.py` theo TCVN 5575:2024 → `calc_steel_beam_tcvn.py`
- [x] Viết lại `calc_steel_connection.py` theo TCVN 5575:2024 → `calc_steel_connection_tcvn.py`
- [x] Cập nhật `STANDARDS_LOCK.md` khi hoàn thành

---

## 3. Hằng số & Hệ số Thống nhất (chống mâu thuẫn giữa các file)

Các giá trị dưới đây trước đây bị khai báo khác nhau ở nhiều file. Đây là giá trị chốt:

| Ký hiệu | Giá trị | Ý nghĩa | Căn cứ |
|---|---|---|---|
| `γ_M0` (thép, bền tiết diện) | **1.05** | Hệ số tin cậy về vật liệu thép → `f = f_y / γ_M0` | TCVN 5575:2024 Bảng 3 |
| `γ_M1` (thép, kiểm tra ổn định) | **1.10** | Hệ số tin cậy khi kiểm tra ổn định tổng thể (LTB) | TCVN 5575:2024 Bảng 3 |
| `α_LT` (LTB, đường cong a) | **0.21** | Hệ số khuyết tật đường cong a (cán rộng I/H) | EN 1993-1-1 Bảng 6.3 / TCVN 5575:2024 |
| `γ_M2` (liên kết, EC3) | 1.25 | Chỉ dùng khi tính theo Eurocode 3 EN 1993-1-8 | EN 1993-1-8 §2.2 |
| `α_v` (bu lông chịu cắt) | 0.6 (cấp 4.6/5.6/8.8) · 0.5 (cấp 10.9) | Dùng **kèm** `γ_M2 = 1.25` theo EC3 | EN 1993-1-8 Bảng 3.4 |
| `γ_f` gió (TCVN 2737:2023) | **Khai báo tường minh, không mặc định** | Hệ số độ tin cậy tải trọng gió | TCVN 2737:2023 |
| `α_R` (BTCT, CB400-V) | 0.39 | Giới hạn `α_m` chống phá hoại giòn | TCVN 5574:2018 |
| `μ_min` (dầm BTCT) | 0.05 % | Hàm lượng cốt thép tối thiểu | TCVN 5574:2018 |
| `[f]` võng dầm | L/250 (mặc định) — L/400 với dầm đỡ tường/kính | Độ võng cho phép | TCVN 5574:2018 Phụ lục M |

> ⚠ **Về `γ_f` gió:** trước đây `wind_load_calc.py` mặc định `2.1` trong khi `SKILL_REPORT.md` nêu ví dụ `1.2` — hai giá trị này thuộc hai hệ quy đổi khác nhau và **không được lẫn lộn**. Script nay **bắt buộc** truyền `--gamma_f` tường minh kèm căn cứ tra cứu; không còn giá trị mặc định ngầm.

---

## 4. Quy trình Tra cứu (thay thế C1 cũ)

1. Đọc `Design_Evaluation/standards/INDEX_QUICK.md` → xác định đúng file PDF.
2. Nếu không thấy → đọc `INDEX.md` (danh mục đầy đủ).
3. Dùng `grep_search` với từ khóa đặc thù trên file PDF. **KHÔNG** đọc toàn bộ PDF lớn.
4. Ngay khi tìm thấy giá trị → tạo Citation Object đủ 6 trường:
   `Ma_Tieu_Chuan · Nam_Ban_Hanh · Dieu_Bang_Muc · Ten_Bang_Hinh · Trang_So · Trich_Yeu`
5. Nếu không tạo được Citation Object hợp lệ → đánh dấu `Citation_Status: UNVERIFIED`, liệt kê riêng ở cuối báo cáo.

---

## 5. Reporting Toolchain Dependencies (v2.4.0 — Reporting Upgrade)

Các thư viện Python bắt buộc cho việc xuất báo cáo (Reporting Upgrade v4.1, 2026-08-31).

| Library | Version tối thiểu | Mục đích | Scripts sử dụng |
|---------|-------------------|----------|------------------|
| `python-docx` | ≥ 0.8.11 | Tạo/sửa file `.docx` (cover, TOC, headers, tables, callouts) | `report_dispatcher.py`, `document_renderer.py`, 4 generator cũ |
| `openpyxl` | ≥ 3.0.10 | Tạo `.xlsx` với styling (PatternFill, Font, Border, charts) | `xlsx_report.py` |
| `matplotlib` | ≥ 3.5.0 | Render charts (radar, bar, progress, heatmap, cost breakdown) — Agg backend (non-interactive) | `_lib/_chart_inserter.py` |
| `Pillow` | ≥ 9.0 | Hỗ trợ matplotlib PNG export | `_lib/_chart_inserter.py` |
| `jinja2` | ≥ 3.0 | Template rendering (nếu dùng docxtpl) | `generate_report.py` (template path) |

### Quick Install

```bash
pip install python-docx openpyxl matplotlib Pillow jinja2
```

### Backward Compatibility

✅ Tất cả generator cũ (`generate_report.py`, `generate_to_trinh.js`, `md_to_docx_report.js`, `md_to_pdf_report.js`) vẫn hoạt động — không yêu cầu thêm dependency ngoài những gì đã có.

### Chart Engine

- **Backend:** `matplotlib.use('Agg')` (non-interactive, headless)
- **DPI:** 300 (print-quality)
- **Format:** PNG (universal DOCX compatibility)
- **Vietnamese fonts:** Mặc định dùng system font; nếu lỗi hiển thị → set `plt.rcParams['font.family'] = 'DejaVu Sans'`
