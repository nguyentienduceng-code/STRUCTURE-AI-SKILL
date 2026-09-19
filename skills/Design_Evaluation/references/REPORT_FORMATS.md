# REPORT_FORMATS.md — Catalogue Định dạng Báo cáo

> **Mục đích:** Hướng dẫn chọn format và generator phù hợp cho từng tình huống.
> **Cập nhật:** 2026-08-31 — v1.0 (Phase F of Reporting Upgrade v4.0)

---

## Tổng quan — 4 Luồng Output

| Luồng | Generator | Format | Use Case |
|-------|-----------|--------|----------|
| **Luồng 1** | `generate_report.py` | `.docx` (template-based) | Tờ trình theo template công ty |
| **Luồng 2** | `generate_to_trinh.js` | `.docx` (from-scratch) | Tờ trình không cần template |
| **Luồng 3** | `md_to_docx_report.js` / `md_to_pdf_report.js` | `.md` → `.docx` / `.pdf` | Chuyển MD sang Word/PDF |
| **Luồng 4** ⭐ | **`report_dispatcher.py`** | `.md`, `.docx`, `.html`, `.xlsx` | **Unified, audience-aware** |

---

## Luồng 4 — Unified Dispatcher (Khuyến nghị)

### Audience Profiles

| Audience | Sections đầy đủ | Tone |
|----------|----------------|------|
| `designer` | Cover + TOC + Dashboard + Logs + Citations + Charts | Formal technical |
| `engineer` | Cover + TOC + Logs + Charts (no Dashboard) | Technical precise |
| `contractor` | Cover + TOC + Project Info + Charts + Approval | Practical |
| `owner` | Cover + Dashboard + Comparison + Charts | Business friendly |
| `authority` | Cover + TOC + All sections + Full audit | Official formal |

### Usage Examples

```bash
# 1. Xuất MD cho cho designer
python report_dispatcher.py \
    --handoff audit.json \
    --format md \
    --audience designer

# 2. Xuất DOCX cho owner (executive)
python report_dispatcher.py \
    --handoff audit.json \
    --format docx \
    --audience owner \
    --include-charts

# 3. Xuất nhiều format cùng lúc
python report_dispatcher.py \
    --handoff audit.json \
    --formats md,docx,html \
    --audience designer \
    --include-charts \
    --output "G:/Projects/Reports/"

# 4. List audiences
python report_dispatcher.py --list-audiences
```

### Input Schema (SKILLKC Handoff)

Xem: [SKILLKC_OUTPUTS.md](SKILLKC_OUTPUTS.md)

Key fields:
- `Ten_Du_An`, `Hang_Muc`, `Giai_Doan_TK`, `Ngay`
- `Loai_Phan_Tich`
- `Calculation_Logs[]` (Step, Static_Scheme, Formula, Citation, Values, Result, Utilization, Rating)
- `So_Sanh` (categories[], plans{})
- `Citations[]`
- `Unverified_Items[]`
- `Kien_NGhi`
- `Standard_Method`

---

## Luồng 5 — Excel (.xlsx) Reports

### Generator: `xlsx_report.py`

| Type | Use Case |
|------|----------|
| `boq` | Bảng Khối Lượng (Bill of Quantities) |
| `calc` | Calculation Sheet với η/Rating màu |
| `comparison` | Ma trận So sánh Phương án + Chart |
| `submittal` | Submittal Log cho SKILL_RFI |

### Usage

```bash
# Calculation Sheet
python xlsx_report.py \
    --input audit.json \
    --type calc \
    --output calc_sheet.xlsx

# Comparison Matrix (có chart)
python xlsx_report.py \
    --input audit.json \
    --type comparison \
    --output comparison.xlsx

# Submittal Log (SKILL_RFI)
python xlsx_report.py \
    --input _data/document_registry.json \
    --type submittal \
    --output submittal_log.xlsx
```

---

## SKILL_RFI Document Renderer

### Generator: `document_renderer.py`

Render JSON documents ra file chuyên nghiệp.

| Doc Type | Format | Use Case |
|----------|--------|----------|
| RFI / PBRFI | `.docx`, `.md` | Form RFI chuẩn |
| NCR | `.docx` (color-coded by severity) | Phiếu NCR |
| SUBMITTAL | `.docx` | Log bản vẽ thi công |
| CO / TQ | `.docx`, `.md` | Change Order, Tech Query |

### Usage

```bash
# Render 1 document
python document_renderer.py \
    --input _data/document_registry.json \
    --code RFI-GEN-20260831-001 \
    --format docx

# Render tất cả
python document_renderer.py \
    --input _data/document_registry.json \
    --all \
    --output _output/

# Filter theo type
python document_renderer.py \
    --input _data/document_registry.json \
    --all \
    --type NCR
```

---

## Quyết định: Chọn Generator nào?

```
Cần báo cáo tổng hợp (cover, TOC, charts)?
├─ Có audience cụ thể (Owner, Designer, Contractor)?
│  ├─ CÓ → report_dispatcher.py ⭐
│  └─ KHÔNG → generate_report.py (template) hoặc generate_to_trinh.js
└─ KHÔNG → md_to_docx_report.js hoặc md_to_pdf_report.js

Cần xuất Excel?
├─ BOQ → xlsx_report.py --type boq
├─ Calc Sheet → xlsx_report.py --type calc
└─ Comparison → xlsx_report.py --type comparison

Cần xuất SKILL_RFI documents?
└─ document_renderer.py
```

---

## Output Quality Checklist

Mỗi báo cáo xuất ra phải có:

- [ ] **Cover page** (cho `.docx` từ dispatcher): logo, project name, title, version, date
- [ ] **Header/Footer**: project name + page X/Y
- [ ] **Executive Dashboard** (cho audience owner/contractor): KPIs, status, risks, CTA
- [ ] **Calculation logs** (cho designer/engineer): Step, η, Rating có màu
- [ ] **Citations** (cho designer/authority): format 4-tuple đầy đủ
- [ ] **Charts** (khi có Comparison data): radar/bar tự động
- [ ] **Approval Matrix**: 3-column signature table
- [ ] **Disclaimer**: bắt buộc ở cuối mỗi báo cáo

---

## Files Liên quan

| File | Mục đích |
|------|----------|
| `_lib/_docx_helpers.py` | Shared DOCX helpers (cover, TOC, headers) |
| `_lib/_report_utils.py` | Citation/η/Unicode rendering |
| `_lib/_chart_inserter.py` | Chart auto-insert + generators |
| `_lib/_executive_dashboard.py` | Dashboard cho Owner/Management |
| `_lib/_audience_profiles.py` | 5 audience profile configs |
| `report_dispatcher.py` | Unified dispatcher (entry point) |
| `xlsx_report.py` | Excel generators |
| `_SUPPORT_SKILLS/SKILL_RFI/scripts/document_renderer.py` | SKILL_RFI DOCX/MD |

Updated: 2026-08-31