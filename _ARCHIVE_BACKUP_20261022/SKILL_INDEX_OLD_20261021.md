# SKILL_INDEX.md — Chỉ mục Tổng hợp Toàn bộ Bộ Skills

> **Mục đích:** Nguồn sự thật DUY NHẤT về cấu trúc, modules, và dependencies của toàn bộ hệ thống skill.
> **Cập nhật:** 2026-10-12 — v2.0 (Global Dispatcher & Central Orchestrator)
> **Thay thế:** Phần "Cấu trúc Thư mục" trong từng SKILL.md riêng lẻ.
> **Entry Point:** Xem `../README.md` trước!

---

---

## 🔴 P0 NEW: Agentic Workflow Infrastructure

**Ngày phát hành:** 2026-09-25 — Critical infrastructure cho agentic reasoning.

| File | Mục đích | Tầm quan trọng |
|------|-----------|----------------|
| `SKILL_BRIDGE.md` | Data contracts & handoff protocol giữa các skill | **P0** |
| `INTER_SKILL_TRIGGERS.md` | Quy tắc tự động gọi skill không cần user ra lệnh | **P0** |

**Vị trí:** `.agents/skills/` (Hạ tầng quy chuẩn cốt lõi liên-skill)

**SHARED_CONTEXT Directory:** `.agents/_SHARED/SHARED_CONTEXT/`
```
_SHARED/
└── SHARED_CONTEXT/
    ├── _active/              ← Handoff đang xử lý
    ├── _archive/             ← Đã xử lý xong
    ├── _rejected/            ← Bị từ chối (thiếu field)
    ├── samples/               ← Sample handoff JSON files
    ├── validate_handoff_schema.py  ← Schema validation script
    ├── confidence_score.py          ← Confidence level calculator
    └── handoff_manager.py          ← CLI cho handoff lifecycle
```

**Quick Reference:**
- **SKILL_BRIDGE.md** — Định nghĩa JSON schema cho 5 loại handoff:
  - `geotech_to_structural_*.json` — Foundation params
  - `structural_to_cost_*.json` — Design output for VE
  - `structural_to_verify_*.json` — QA check request
  - `design_eval_to_cost_*.json` — VE analysis request
  - `geotech_to_design_eval_*.json` — Geotech review request

- **INTER_SKILL_TRIGGERS.md** — 15 triggers tự động:
  - POST-GEOTECH-01/02/03: Soil params, Base heave, Adverse conditions
  - POST-DESIGN-01/02/03: Design complete (BẮT BUỘC verify), VE opportunity, Drawing needed
  - POST-EVAL-01/02: Review complete, Standard conflict
  - POST-VERIFY-01: Variance > 5% → Reject
  - POST-COST-01: VE potential → Alternative design

- **P1 Tools** (trong `_SHARED/SHARED_CONTEXT/`):
  - `validate_handoff_schema.py` — Validate JSON schema
  - `confidence_score.py` — Calculate confidence level (5 factors)
  - `handoff_manager.py` — CLI cho create/list/validate/archive/reject/receipt

---

## 0. NEW IN v1.5 — Reporting Upgrade

**Tính năng chính:** Unified Dispatcher + 5 Audience Profiles

### Files mới

| File | Mục đích |
|------|---------|
| `Design_Evaluation/scripts/_lib/` | 📦 **Foundation library** — DOCX helpers, charts, dashboard, audience profiles |
| `Design_Evaluation/scripts/report_dispatcher.py` | ⭐ **Unified CLI** — 1 JSON → nhiều format, audience-aware |
| `Design_Evaluation/scripts/xlsx_report.py` | Excel: BOQ/Calc/Comparison/Submittal |
| `SKILL_RFI/scripts/document_renderer.py` | SKILL_RFI DOCX/MD renderer |
| `Design_Evaluation/references/REPORT_FORMATS.md` | Catalogue 4 luồng reporting |

### 5 Audience Profiles

| Audience | Use Case | Sections đầy đủ |
|----------|----------|-----------------|
| `designer` | Tư vấn thiết kế | Cover + TOC + Dashboard + Logs + Citations + Charts |
| `engineer` | Kỹ sư tính toán | Cover + TOC + Logs + Charts |
| `contractor` | Nhà thầu thi công | Cover + TOC + Project Info + Charts + Approval |
| `owner` | Chủ đầu tư | Cover + Dashboard + Comparison + Charts |
| `authority` | Cơ quan quản lý | Cover + TOC + All sections + Full audit |

### Usage nhanh

```bash
# Xuất báo cáo unified
python Design_Evaluation/scripts/report_dispatcher.py \
    --handoff audit.json --audience designer --formats md,docx

# Xuất Excel BOQ
python Design_Evaluation/scripts/xlsx_report.py \
    --input audit.json --type boq --output boq.xlsx

# Render SKILL_RFI document
python SKILL_RFI/scripts/document_renderer.py \
    --input document_registry.json --all --format docx
```

---

## 1. TỔNG QUAN KIẾN TRÚC

```
.agents/skills/
│
├── Global_Dispatcher/         ← 🎯 BỘ ĐIỀU PHỐI TRUNG TÂM (Luôn đón tiếp User)
│   ├── SKILL.md
│   └── scripts/
│       ├── intent_classifier.py
│       ├── keyword_database.json
│       └── pipeline_builder.py
│
├── AGENTS.md                  ← 📖 ĐỌC TRƯỚC: Quy tắc liên-skill toàn hệ thống
├── SKILL_INDEX.md             ← Bản đồ điều phối & tra cứu nhanh (file này)
├── STANDARDS_LOCK.md          ← Khóa cứng phiên bản tiêu chuẩn chuẩn
├── SKILL_BRIDGE.md            ← Giao thức Data Contract & Handoff Schemas
├── INTER_SKILL_TRIGGERS.md    ← Ma trận tự động kích hoạt liên-skill
│
├── _CORE_SKILLS/             ← 🔧 SKILLS CHÍNH
│   ├── Design_Evaluation/    ← Review, QC/QA, Tờ trình
│   ├── Structural_Design_Engineer/ ← Tính toán, Thuyết minh
│   └── Technical_Illustrator/ ← Vẽ 2D
│
├── _SUPPORT_SKILLS/           ← 🔧 SKILLS HỖ TRỢ
│   ├── Cost_Estimator/       ← So sánh chi phí, VE
│   ├── SKILL_FORENSIC/       ← Điều tra sự cố
│   ├── SKILL_VERIFY/         ← Kiểm chứng kết quả
│   ├── SKILL_RFI/            ← Quản lý RFI với nhà thầu
│   ├── SKILL_PHULUC/         ← Phụ lục tính toán chuyên nghiệp
│   ├── SKILL_GEOTECH/        ← Địa kỹ thuật & Thông số Plaxis
│   ├── SKILL_TEMPWORKS/      ← 🟢 Thiết kế Cốp pha sàn & Cây chống (v0.2.0)
│   ├── Project_Manager/      ← 🟡 Quản lý dự án (Placeholder)
│   └── SKILL_BIM_COORDINATION/ ← 🟡 BIM Coordination (Placeholder)
│
├── _SHARED/shared/           ← 🔧 Shared utilities
│
└── CHANGELOG.md             ← Lịch sử thay đổi
```

### Skill Flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────────┐
            │ Design_   │   │Structural_│   │Technical_     │
            │Evaluation │   │Design_    │   │Illustrator    │
            │(Review/   │   │Engineer   │   │(Visualization)│
            │Thẩm tra) │   │(Tính toán)│   │               │
            └─────┬─────┘   └─────┬─────┘   └──────┬────────┘
                  │               │                │
                  └───────┬───────┴───────┬────────┘
                          ▼                │
                  ┌───────────────┐        │
                  │ Cost_Estimator│◄───────┘
                  │(Chi phí/VE)  │
                  └───────┬───────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌─────────────┐
    │SKILL_     │   │SKILL_     │   │SKILL_REPORT │
    │FORENSIC   │   │VERIFY     │   │(Xuất báo cáo)│
    │(Điều tra) │   │(QA/Check) │   │             │
    └───────────┘   └───────────┘   └─────────────┘
```

---

## 2. BẢNG PHÂN XỬ SKILL (Dispatcher)

| Câu hỏi phân xử | Đáp án | Skill kích hoạt |
|---|---|---|
| Yêu cầu bằng ngôn ngữ tự nhiên, chưa rõ skill hoặc cần chuỗi nhiều skill? | Có | `Global_Dispatcher` |
| Review/thẩm tra/thẩm định hồ sơ? | Có | `Design_Evaluation` |
| Tự tính ra tiết diện/cốt thép/bu lông? | Có | `Structural_Design_Engineer` |
| Tạo hình ảnh/bản vẽ/minh họa? | Có | `Technical_Illustrator` |
| So sánh chi phí/Value Engineering/Carbon? | Có | `Cost_Estimator` |
| Điều tra sự cố/nứt nghiêm trọng/back-calculation? | Có | `SKILL_FORENSIC` |
| Kiểm chứng chéo/cross-check/sai lệch? | Có | `SKILL_VERIFY` |
| Tạo RFI/theo dõi/đối chiếu với nhà thầu? | Có | `SKILL_RFI` |
| Phụ lục tính toán kết cấu step-by-step cho thẩm tra? | Có | `SKILL_PHULUC` |
| Phân tích địa chất/thông số Plaxis/SPT/CPT? | Có | `SKILL_GEOTECH` |
| Quản lý dự án/lộ trình pháp lý/tiến độ? | Có | `Project_Manager` |
| Xung đột kỹ thuật/clash detection/BIM? | Có | `SKILL_BIM_COORDINATION` |
| Thiết kế cốp pha/cây chống/biện pháp thi công? | Có | `SKILL_TEMPWORKS` |

**Tie-breaker:** Xem `AGENTS.md` mục 0.

---

## 3. DANH MỤC ĐẦY ĐỦ CÁC SKILL

### 3.0 Global_Dispatcher (v1.0.0)

**Vai trò:** Bộ Điều phối Trung tâm (Central Orchestrator)

**Entry Point:** `SKILL.md` → `scripts/intent_classifier.py` / `scripts/pipeline_builder.py`

| Thành phần | File | Chức năng |
|------------|------|-----------|
| **SKILL** | `SKILL.md` | Hướng dẫn phân loại intent, định tuyến, quản lý pipeline |
| **Intent Classifier** | `scripts/intent_classifier.py` | Phân tích prompt ngôn ngữ tự nhiên → Skill + Confidence score (15/15 test passed 100%) |
| **Keyword Database** | `scripts/keyword_database.json` | 220+ keywords, regex patterns, tie-breaker rules, pipeline templates |
| **Pipeline Builder** | `scripts/pipeline_builder.py` | Xây dựng pipeline tự động khi cần 2+ skills, xác định review gates và handoff schemas |

---

### 3.1 Design_Evaluation (v2.2.0)

**Vai trò:** Quản lý Thiết kế / Đại diện Chủ đầu tư

**Entry Point:** `SKILL.md` → `SKILLKC.md` hoặc `SKILL_REPORT.md`

| Sub-Module | File | Chức năng |
|------------|------|-----------|
| **SKILLKC** | `SKILLKC.md` | Phân tích kỹ thuật kết cấu (17 nhóm năng lực) |
| **SKILL_REPORT** | `SKILL_REPORT.md` | Xuất báo cáo: .md / .docx / .pdf |

**Sub-modules phụ (lazy-load):**
| File | Kích hoạt khi |
|------|---------------|
| `references/SKILLKC_PROTOCOLS.md` | Rule 11-16, Special Skills |
| `references/SKILLKC_OUTPUTS.md` | JSON handoff, Approval Matrix |
| `modules/audience_detector.py` | Phát hiện đối tượng đọc |
| `modules/forensic_analyzer.py` | Forensic review mode |
| `modules/standards_version_tracker.py` | Theo dõi phiên bản tiêu chuẩn |

**Scripts chính:**
| Script | Chức năng |
|--------|-----------|
| `calculators/rc_flexure_design.py` | Cốt thép dầm BTCT chịu uốn |
| `calculators/steel_member_check_v2024.py` | Ứng suất cấu kiện thép (TCVN 5575:2024) |
| `calculators/deflection_check.py` | Kiểm tra độ võng |
| `calculators/foundation_bearing.py` | Sức chịu tải nền |
| `calculators/wind_load_calc.py` | Tải trọng gió |
| `calculators/earthquake_load_calc.py` | Tải trọng động đất |
| `scripts/generate_report.py` | Bơm JSON vào Word template |
| `scripts/boq_extractor.py` | Đọc BOQ Excel/CSV → JSON |
| `scripts/auto_rfi_generator.py` | Tạo RFI tự động |
| `scripts/stage_gate_checklist.py` | Checklist theo giai đoạn |

---

### 3.2 Structural_Design_Engineer (v1.3.0)

**Vai trò:** Kỹ sư Thiết kế Độc lập

**Entry Point:** `SKILL.md` → `SKILL_CALC.md`, `SKILL_CONNECTION.md`, hoặc `SKILL_CALC_REPORT.md`

| Sub-Module | File | Chức năng |
|------------|------|-----------|
| **SKILL_CALC** | `SKILL_CALC.md` | Tính toán tiết diện & kết cấu (BTCT, Thép, Móng) |
| **SKILL_CONNECTION** | `SKILL_CONNECTION.md` | Thiết kế chi tiết liên kết |
| **SKILL_CALC_REPORT** | `SKILL_CALC_REPORT.md` | Xuất Thuyết minh tính toán |

**Scripts chính:**
| Script | Chức năng | Standard | Ghi chú |
|--------|-----------|----------|----------|
| `calc_steel_beam_tcvn.py` | Dầm thép: uốn + cắt + LTB + võng | **TCVN 5575:2024** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_steel_connection_tcvn.py` | Bu lông: cắt + ép mặt + kéo | **TCVN 5575:2024** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_weld_tcvn.py` | Đường hàn góc & đối đầu | **TCVN 5575:2024** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_rc_section.py` | Dầm BTCT: uốn + cắt | **TCVN 5574:2018** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_rc_column.py` | Cột BTCT: nén uốn lệch tâm | **TCVN 5574:2018** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_slab.py` | Sàn BTCT 2 phương: ULS + võng + nứt | **TCVN 5574:2018** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_crack_width.py` | Kiểm tra bề rộng khe nứt | **TCVN 5574:2018** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `calc_foundation_pile.py` | Sức chịu tải cọc ép/khoan nhồi | **TCVN 10304:2025** | ✅ DÙNG CHO HỒ SƠ MỚI |
| `export_calc_sheet.py` | Xuất Thuyết minh tính toán | — | — |

**⚠️ Scripts DEPRECATED (đã chuyển sang `_deprecated/`):**
| Script | Standard | Lý do |
|--------|----------|--------|
| `calc_steel_beam.py` | EN 1993-1-1 | Không đồng bộ với STANDARDS_LOCK |
| `calc_steel_connection.py` | EN 1993-1-8 | Không đồng bộ với STANDARDS_LOCK |

> **Quy tắc:** Chỉ dùng scripts có ✅ trong bảng trên. Scripts deprecated chỉ để tham khảo.

**References:**
| File | Chức năng |
|------|-----------|
| `references/STEEL_DESIGN_GUIDE.md` | Hướng dẫn thiết kế thép |
| `references/RC_DESIGN_GUIDE.md` | Hướng dẫn thiết kế BTCT |
| `references/FOUNDATION_DESIGN_GUIDE.md` | Hướng dẫn thiết kế móng |

---

### 3.3 Technical_Illustrator (v1.3.0)

**Vai trò:** Minh họa Kỹ thuật

**Entry Point:** `SKILL.md`

| Mode | Công cụ | Giá trị | Kích hoạt |
|------|---------|---------|------------|
| **MODE 2D** | Python/matplotlib | Bản vẽ kỹ thuật chính xác | MẶC ĐỊNH |
| **MODE 3D** | AI Render | Minh họa phối cảnh | CHỈ khi yêu cầu rõ |

**Scripts vẽ 2D (tham số hóa — hoạt động):**
| Script | Input chính | Output |
|--------|-------------|--------|
| `draw_2d_section.py` | `--h --b --tw --tf` | Mặt cắt dầm thép |
| `draw_bolt_connection.py` | `--bolt_d --bolt_grade --n_rows --n_cols` | Chi tiết bu lông |
| `draw_rc_column.py` | `--type --width --depth --main_dia` | Mặt cắt cột BTCT |
| `draw_foundation.py` | `--type --L --B --H` | Móng đơn/băng |
| `draw_slab_rebar.py` | `--Lx --Ly --slab_t` | Bố trí thép sàn |
| `draw_comparison_chart.py` | `--json` | Biểu đồ so sánh |
| `draw_rc_beam_full.py` | `--type --b --h --main_dia --stirrup_dia` | Dầm BTCT đầy đủ |
| `draw_rc_wall.py` | `--type --t --rebar_dia --spacing` | Tường chắn BTCT |
| `draw_pile_cap.py` | `--type --L --B --H --pile_d --n_piles` | Đài cọc |
| `draw_weld_detail.py` | `--type --plate_t --weld_type` | Chi tiết hàn |
| `draw_moment_diagram.py` | `--input --output` | Biểu đồ nội lực (M, V, N) SVG/DXF |
| `cad_integration/dce_dxf_generator.py` | DXF template | Bản vẽ CAD |

**Deprecated (di chuyển sang `_deprecated/`):**
| Script | Lý do | Thay thế |
|--------|-------|-----------|
| `draw_ap_luc_dat_bo_ke.py` | Fixed geometry | Cần viết lại parametric |
| `draw_ke_buy_dung.py` | Fixed geometry | Cần viết lại parametric |
| `draw_ke_pi_gieng.py` | Fixed geometry | Cần viết lại parametric |
| `draw_pi_gieng_composite.py` | Fixed geometry | Cần viết lại parametric |
| `draw_tham_da.py` | Fixed geometry | Cần viết lại parametric |

**References:**
| File | Chức năng |
|------|-----------|
| `references/MODE_2D_GUIDE.md` | Hướng dẫn vẽ 2D + Error handling |
| `references/MODE_3D_GUIDE.md` | Hướng dẫn render 3D |
| `references/PROMPT_TEMPLATES.md` | 8 prompt templates cho 3D |
| `scripts/REGISTRY_INDEX.md` | Tra nhanh: tình huống → script |

---

### 3.4 Cost_Estimator (v1.2.0)

**Vai trò:** Value Engineering / Phân tích Chi phí

**Entry Point:** `SKILL.md`

| Module | Script | Chức năng |
|--------|--------|-----------|
| **MODULE 1** | `boq_cost_analysis.py` | Tính chi phí từ BOQ |
| **MODULE 2** | `compare_structural_options.py` | So sánh phương án kết cấu |
| **MODULE 3** | `material_optimization.py` | Đề xuất giảm vật liệu (η ≤ 0.70) |
| **MODULE 4** | `carbon_calculator.py` | Tính Embodied Carbon |
| **MODULE 5** | `schedule_cost_impact.py` | Chi phí lãi vay ẩn |
| **MODULE 6** | `leed_credit_estimator.py` | Ước tính điểm LEED |
| **MODULE 7** | `update_prices.py` | Cập nhật đơn giá |

**Data files:**
| File | Nội dung |
|------|----------|
| `data/material_unit_prices.json` | Đơn giá vật liệu (Q2/2026) |
| `data/carbon_coefficients.json` | Hệ số Carbon |
| `data/labor_rates.json` | Đơn giá nhân công theo vùng |

---

### 3.5 SKILL_FORENSIC (v1.2.0)

**Vai trò:** Điều tra Sự cố Kết cấu

**Entry Point:** `SKILL.md` — 7-bước chuẩn

| Bước | Script | Chức năng |
|------|--------|-----------|
| **B1** | `evidence_checklist_generator.py` | Thu thập chứng cứ |
| **B2** | — | Mô hình hóa hiện trạng |
| **B3** | `back_calculation.py` | Tính toán ngược |
| **B4** | — | So sánh thiết kế vs thực tế |
| **B5** | `hypothesis_ranker.py` | Xếp hạng giả thuyết |
| **B6** | — | Đề xuất thí nghiệm |
| **B7** | `remedial_solution_generator.py` | Phương án xử lý |

**Scripts bổ sung:**
| Script | Chức năng |
|--------|-----------|
| `search_fm.py` | Tìm kiếm Failure Mode Database |

**References:**
| File | Chức năng |
|------|-----------|
| `references/RED_FLAG_TRIGGERS.md` | 18 triggers cụ thể, 4 cấp nguy hiểm |
| `references/failure_modes_database.json` | 50+ chế độ phá hoại |

---

### 3.6 SKILL_VERIFY (v1.2.0)

**Vai trò:** Quality Assurance / Kiểm chứng Chéo

**Entry Point:** `SKILL.md`

| Loại | Script | Chức năng |
|------|--------|-----------|
| **Loại 1** | `inter_module_verify.py` | So sánh SKILLKC vs Structural_Design_Engineer |
| **Loại 2** | `standard_conflict_checker.py` | Phát hiện xung đột phiên bản tiêu chuẩn |
| **Loại 3** | `calculation_logs_checker.py` | Kiểm tra nhất quán calculation logs |
| **Loại 4** | `compare_with_etabs.py` | So sánh với ETABS/SAP2000 |
| **Loại 5** | `report_consistency_check.py` | Kiểm tra báo cáo vs JSON handoff |
| **UNIFIED** | `verify_all.py` | Chạy đồng thời cả 5 loại |

**Thresholds chuẩn:**
| Loại | Ngưỡng Warning | Ngưỡng Critical |
|------|---------------|-----------------|
| Inter-module variance | 5% | 10% |
| Utilization ratio η | 3% | 5% |
| Diện tích cốt thép | 10% | 15% |

---

## 3.7 SKILL_RFI (v1.2.0)

**Vai trò:** Quản lý giao dịch kỹ thuật (RFI/NCR/Submittal/CO) với tất cả các bên

**Entry Point:** `SKILL.md` — 5-step RFI workflow

**Trigger Keywords:** "tạo RFI", "theo dõi RFI", "phản hồi RFI", "RFI quá hạn"

| Bước | Script | Chức năng |
|-------|---------|-----------|
| **B1** | `document_generator.py` | Tạo RFI/NCR/Submittal/CO/TQ |
| **B2** | `document_tracker.py` | Theo dõi tất cả tài liệu |
| **B3** | `rfi_dashboard.py` | Dashboard tổng quan |
| **B4** | — | Leo thang khi quá hạn |
| **B5** | — | Tích hợp phản hồi vào phân tích |

**Phân loại ưu tiên:**

| Mức | Ký hiệu | Trigger | Deadline |
|------|----------|---------|----------|
| 🔴 URGENT | An toàn/Kết cấu | "sập", "nguy hiểm", "sai tiết diện" | 24h |
| 🟠 HIGH | Tiến độ/Cost | "chậm", "phát sinh", "thay đổi" | 3 ngày |
| 🟡 NORMAL | Kỹ thuật | "thiếu thông tin", "cần xác nhận" | 7 ngày |
| 🟢 LOW | Hành chính | "làm rõ", "bổ sung" | 14 ngày |

**Integration với Design_Evaluation:**
```
Design_Evaluation phát hiện Data Missing:
    ↓
SKILL_RFI tạo RFI tự động
    ↓
Theo dõi deadline
    ↓
Khi có phản hồi → Cập nhật vào phân tích
```

---

## 3.8 SKILL_PHULUC (v1.0.0)

**Vai trò:** Phụ lục Tính toán Kết cấu Chuyên nghiệp

**Entry Point:** `SKILL.md` — Step-by-step calculation sheets cho thẩm tra

**Trigger Keywords:** "phụ lục tính toán", "thuyết minh chi tiết", "calculation sheet", "bảng tính kết cấu"

| Loại Template | File | Mô tả |
|---------------|------|--------|
| **TMTT Đầy đủ** | `TMTT_FULL.md` | Thuyết minh đầy đủ 12 chương |
| **TMTT Bê tông** | `PARTIAL_BE_TONG.md` | Phụ lục kết cấu BTCT |
| **TMTT Thép** | `PARTIAL_THEP.md` | Phụ lục kết cấu thép |
| **Dầm BTCT** | `APPENDIX_BEAM_RC.md` | Dầm bê tông cốt thép |
| **Cột BTCT** | `APPENDIX_COLUMN_RC.md` | Cột bê tông cốt thép |
| **Dầm thép** | `APPENDIX_STEEL_BEAM.md` | Dầm kết cấu thép |

**Điểm khác biệt với SKILL_CALC_REPORT:**
- SKILL_CALC_REPORT: Tóm tắt, internal review
- SKILL_PHULUC: Step-by-step đầy đủ, dùng cho **thẩm tra/chấp thuận**

---

## 3.9 SKILL_GEOTECH (v3.0.0)

**Vai trò:** Kỹ sư Địa kỹ thuật — Phân tích ĐCCT, thông số Plaxis

**Entry Point:** `SKILL.md` — Pipeline SPT/CPT → Plaxis parameters

**Trigger Keywords:** "phân tích địa chất", "thông số Plaxis", "SPT", "CPT", "CPTu", "Soft Soil Creep", "ứng suất hữu hiệu"

| Module | Script | Chức năng |
|--------|--------|-----------|
| **MODULE 1** | `calc_geostatic_stress.py` | Ứng suất hữu hiệu, K0, OCR |
| **MODULE 2** | `calc_soil_params_mc.py` | Thông số Mohr-Coulomb cho Plaxis |
| **MODULE 3** | `calc_soil_params_hs.py` | Thông số Hardening Soil cho Plaxis |
| **MODULE 4** | `calc_structural_elements.py` | DW/Cừ Larsen → EA, EI |
| **MODULE 5** | `calc_spt_correlations.py` | SPT → c, φ, E50, Su |
| **MODULE 6** | `calc_cpt_interpretation.py` | CPTu → qt, Bq, Su, SBT 2016 |
| **MODULE 7** | `calc_soil_params_ssc.py` | Soft Soil Creep parameters |
| **MODULE 8** | `calc_pile_load_test.py` | Davisson, Chin-Kondner |
| **MODULE 9** | `calc_psr.py` | Plane Strain Ratio |
| **VERIFY 1** | `verify_against_ground_truth.py` | Kiểm chứng với CSDL thực |
| **VERIFY 2** | `verify_serviceability_limits.py` | SLS check (Clough & O'Rourke) |
| **EXPORT** | `export_geotech_report.py` | Xuất Thuyết minh + Excel |

**References:**
| File | Chức năng |
|------|-----------|
| `references/GEOTECH_GUIDE.md` | Công thức gốc, bảng tương quan |
| `references/PLAXIS_MODEL_GUIDE.md` | Hướng dẫn nhập liệu Plaxis |
| `references/THUYET_MINH_TEMPLATE.md` | Template Thuyết minh BPTC chuẩn |

---

## 3.10 SKILL_TEMPWORKS (v0.2.0)

**Vai trò:** Kỹ sư Temporary Works AI — Thiết kế cốp pha sàn, cây chống, biện pháp thi công

**Entry Point:** `SKILL.md` → `calculators/calc_formwork_slab.py`

**Trigger Keywords:** "cốp pha", "coffa", "cây chống", "shoring", "bracing", "temporary works", "ván khuôn", "giàn giáo"

| Module | Script | Chức năng | Tiêu chuẩn |
|--------|--------|-----------|------------|
| **MODULE 1 (ACTIVE)** | `calc_formwork_slab.py` | Thiết kế cốp pha sàn (ván, dầm phụ, dầm chính, cây chống) | **ACI 347-04 / TCVN 4453:1995** |
| MODULE 2 (Planned) | `calc_formwork_column.py` | Thiết kế cốp pha cột | ACI 347-04 / TCVN 4453:1995 |
| MODULE 3 (Planned) | `calc_formwork_wall.py` | Thiết kế cốp pha tường & áp lực bê tông tươi | ACI 347-04 / TCVN 4453:1995 |
| MODULE 4 (Planned) | `calc_stability.py` | Kiểm tra ổn định tổng thể hệ chống & reshoring | ACI 347.2R-17 / TCVN 5575:2024 |

---

## 3.11 Các Skill Quản Lý & Phối Hợp (v0.5.0 Active)

**Vai trò:** Các module mở rộng quản lý dự án và phối hợp đa bộ môn

| Skill | Trạng thái | Chức năng | Trigger |
|-------|------------|-----------|---------|
| **Project_Manager** | ✅ v0.5.0 Active | Quản lý dự án, milestone, ma trận rủi ro, lộ trình pháp lý, ĐTM, PCCC | "lập tiến độ", "quản lý rủi ro", "tài liệu pháp lý", "risk matrix", "milestone" |
| **SKILL_BIM_COORDINATION** | ✅ v0.5.0 Active | Clash detection giữa kết cấu và cơ điện, phân tích IFC, kiểm tra lỗ mở dầm | "clash detection", "BIM review", "xung đột kỹ thuật", "phối hợp MEP", "lỗ mở dầm" |

---

## 4. DEPENDENCY GRAPH

```
User Request
    │
    ├─► Design_Evaluation
    │    ├─► Technical_Illustrator (MODE 2D) ─► Technical_Illustrator (MODE 3D) [optional]
    │    ├─► Cost_Estimator [auto khi η ≤ 0.70]
    │    ├─► SKILL_RFI [khi có Data Missing]
    │    ├─► SKILL_PHULUC [khi cần phụ lục step-by-step]
    │    └─► SKILL_VERIFY ─► SKILL_REPORT ─► File Output
    │
    ├─► Structural_Design_Engineer
    │    ├─► Technical_Illustrator (MODE 2D)
    │    ├─► Cost_Estimator [auto khi η ≤ 0.70]
    │    ├─► SKILL_PHULUC [khi cần phụ lục step-by-step]
    │    └─► SKILL_VERIFY ─► SKILL_CALC_REPORT ─► File Output
    │
    ├─► Technical_Illustrator (standalone)
    │    └─► Output Image
    │
    ├─► Cost_Estimator
    │    └─► Output Cost Analysis
    │
    ├─► SKILL_FORENSIC
    │    ├─► Technical_Illustrator (MODE 2D) [optional]
    │    └─► Forensic Report
    │
    ├─► SKILL_RFI
    │    ├─► RFI Generator (Data Missing)
    │    ├─► RFI Tracker (Status/Deadline)
    │    └─► RFI Dashboard
    │
    ├─► SKILL_PHULUC (standalone)
    │    ├─► Technical_Illustrator (MODE 2D) [optional]
    │    └─► Phụ lục Calculation Sheet
    │
    ├─► SKILL_GEOTECH (standalone)
    │    ├─► SKILL_VERIFY [optional]
    │    └─► Thuyết minh ĐCCT + Bảng tính Plaxis
    │
    └─► SKILL_VERIFY (standalone)
         └─► Verification Report
```

---

## 5. STANDARDS LOCK SUMMARY

| Lĩnh vực | Chuẩn (Hồ sơ mới) | Cũ (Đối chiếu) |
|-----------|-------------------|-----------------|
| Tải trọng | TCVN 2737:2023 | TCVN 2737:1995 |
| Động đất | TCVN 9386:2025 (P1+P5) | TCVN 9386:2012 |
| BTCT | TCVN 5574:2018 | TCVN 5574:2012 |
| Thép | TCVN 5575:2024 | TCVN 5575:2012 |
| Móng | TCVN 10304:2025 | TCVN 10304:2014 |

**Known Gaps (công thức chưa cập nhật):**
> ⚠️ **Đã xử lý 2026-08-30:** Các Eurocode scripts đã được chuyển sang `_deprecated/`.

| Script | Standard_Method | Trạng thái |
|--------|----------------|------------|
| `_deprecated/calc_steel_beam.py` | EN 1993-1-1 | ⚠️ DEPRECATED — Tham khảo đối chiếu |
| `_deprecated/calc_steel_connection.py` | EN 1993-1-8 | ⚠️ DEPRECATED — Tham khảo đối chiếu |

---

## 6. PIPELINE ĐIỂN HÌNH

### 6.1 Review Pipeline
```
SKILLKC phân tích → Technical_Illustrator vẽ → SKILLKC review → 
SKILL_VERIFY check → Review Gate (User approve) → SKILL_REPORT xuất file
```

### 6.2 Design Pipeline
```
SKILL_CALC tính → SKILL_CONNECTION thiết kế liên kết → 
Technical_Illustrator vẽ → SKILL_VERIFY check → 
SKILL_CALC_REPORT xuất Thuyết minh
```

### 6.3 Forensic Pipeline
```
SKILL_FORENSIC thu thập chứng cứ → back_calculation → 
hypothesis_ranker → remedial_solution → Forensic Report
```

---

## 7. SHARED UTILITIES (Phase 2 — 2026-08-30)

### 7.1 Standards MCP Server
**Vị trí:** `shared/standards_mcp/server.py`

**Chức năng:** Fast lookup cho tiêu chuẩn
- Search citation theo keyword
- Validate version với STANDARDS_LOCK
- Format citation tự động

**Cách dùng:**
```bash
cd shared/standards_mcp
python server.py --test
```

### 7.2 Project Memory Layer
**Vị trí:** `shared/memory/project_memory.py`

**Chức năng:** Lưu context dự án giữa các session
- Nhớ quyết định thiết kế đã duyệt
- Nhớ standards đã sử dụng
- Nhớ issues đã xử lý

**Cách dùng:**
```bash
cd shared/memory
python project_memory.py --project DUAN_A --action list
python project_memory.py --project DUAN_A --action create --name "Dự án A"
```

### 7.3 Parallel Review Workflow
**Vị trí:** `shared/workflows/parallel_review_workflow.py`

**Chức năng:** Review song song nhiều phần hồ sơ
- Dầm, cột, móng review cùng lúc
- Cross-verify tự động
- Synthesize thành báo cáo

**Cách dùng:**
```bash
cd shared/workflows
python parallel_review_workflow.py --project DUAN_A --scope "beam,column" --output report.json
```

---

## 8. ERROR CODES

| Code | Ý nghĩa | Hành động |
|------|---------|-----------|
| `E001` | Input validation failed | Hiển thị usage + ví dụ |
| `E002` | Missing required data | Liệt kê field còn thiếu |
| `E003` | Calculation inconclusive | Ghi Scope Limitation, không kết luận ĐẠT |
| `E004` | Standard conflict detected | Gọi SKILL_VERIFY Rule 2 |
| `W001` | Approaching threshold (>90%) | Cảnh báo nhưng không block |
| `W002` | η ≤ 70%, VE possible | Khuyến nghị Cost_Estimator |
| `I001` | Info — Debug data available | Log for troubleshooting |

---

## 8. QUICK REFERENCE

### Tình huống → Skill
| Tình huống | Skill |
|------------|-------|
| Review dầm B1 theo TCVN | `Design_Evaluation` |
| Tính cốt thép dầm | `Structural_Design_Engineer` |
| Vẽ mặt cắt dầm | `Technical_Illustrator` (MODE 2D) |
| So sánh BTCT vs Thép | `Cost_Estimator` |
| Điều tra vết nứt dầm | `SKILL_FORENSIC` |
| Check kết quả vs ETABS | `SKILL_VERIFY` |
| Phụ lục tính toán step-by-step | `SKILL_PHULUC` |
| Thông số Plaxis từ SPT/CPT | `SKILL_GEOTECH` |

### Tình huống → Script Calculator
| Tính toán | Script |
|-----------|--------|
| Cốt thép dầm BTCT | `calculators/rc_flexure_design.py` |
| Kiểm tra độ võng | `calculators/deflection_check.py` |
| Ứng suất dầm thép (2024) | `calculators/steel_member_check_v2024.py` |
| Dầm thép (TCVN 5575:2024) | `calc_steel_beam_tcvn.py` ✅ MỚI |
| Liên kết bu lông (TCVN 5575:2024) | `calc_steel_connection_tcvn.py` ✅ MỚI |
| Sức chịu tải móng | `calculators/foundation_bearing.py` |
| Tải trọng gió | `calculators/wind_load_calc.py` |
| Tải trọng động đất | `calculators/earthquake_load_calc.py` |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.9 | 2026-09-27 | Agentic Workflow Infrastructure P1 (Handoff Validation & Confidence Score) |
| 1.8 | 2026-09-26 | Agentic Workflow Infrastructure P0 + Added 3 placeholder skills |
| 1.7 | 2026-09-25 | Critical fixes: Version sync với SKILL.md thực tế, thêm Lazy Load, xóa deprecated references |
| 1.6 | 2026-09-20 | Added SKILL_PHULUC (v1.0.0) and SKILL_GEOTECH (v3.0.0); Updated dependency graph |
| 1.5 | 2026-08-31 | Reporting Upgrade v4.1 — Unified Dispatcher + 5 Audience Profiles |
| 1.1 | 2026-08-30 | Eurocode scripts moved to `_deprecated/`; Updated Standards Lock section; Added deprecated scripts table |
| 1.0 | 2026-08-25 | Initial release — tổng hợp toàn bộ skills |

