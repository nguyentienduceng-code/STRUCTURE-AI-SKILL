# CHANGELOG — Toan bo Bo Skills Ky Nang Ket Cau

> **Pham vi:** Ghi nhan thay doi cua **MOI skill** trong `.agents/skills/`.
> **Cap nhat lon nhat:** 2026-10-13 (v6.3 / Clean Architecture & De-clutter)

---

## 2026-10-15 — v6.4: Tối Ưu Hóa & Đồng Bộ Toàn Bộ Hệ Thống (System Optimization & Sync)

### Tong quan

- **Đồng bộ SSOT 100%:** Đồng bộ byte-for-byte giữa `.agents/AGENTS.md` và `.agents/skills/AGENTS.md` (giải quyết triệt để version drift từ v5.5 lên v6.1).
- **Vá Fallback Loader `_require_docx.js`:** Tự động nạp gói `docx` từ vendor dự phòng `.agents/.npm/docx/docx` khi chạy trên Google Drive, đảm bảo xuất báo cáo Word qua Node.js luôn thông suốt.
- **Chuẩn hóa Git & .gitignore:** Bổ sung `.npm/` vào `.gitignore`, loại bỏ hoàn toàn các file tracking dư thừa.
- **Sửa đường dẫn `SKILL_INDEX.md`:** Cập nhật vị trí chuẩn của `SKILL_BRIDGE.md` và `INTER_SKILL_TRIGGERS.md` về `skills/`.
- **Dọn dẹp & Tinh gọn Workspace:** Di chuyển 5 script vẽ cũ về `.agents/_deprecated/technical-illustrator-scripts/`, xóa bỏ thư mục `_deprecated` rỗng ngoài root, chuẩn hóa root chỉ còn đúng 10 thư mục chức năng.
- **Kiểm thử hệ thống:** 6/6 test suites đạt 100% PASS (thời gian: 1.29s).

---

## 2026-10-13 — v6.3: Tái Cấu Trúc Khoa Học & Chuẩn Hóa Kiến Trúc Hệ Sinh Thái (Clean Architecture)

### Tong quan

Giải quyết triệt để vấn đề lộn xộn, tệp tin rác và nhân bản file vô tội vạ:
- **Tạo thư mục `.agents/tests/`:** Tập trung toàn bộ test runner và suites (`run_all_tests.py`, `integration_test.py`, `test_runner.py`), xóa bỏ các file test rơi rớt ở root và `skills/`.
- **Tạo thư mục `.agents/docs/`:** Tập trung các báo cáo kỹ thuật và đề án phát triển (`BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md`, `SYSTEM_REVIEW_RESPONSE.md`).
- **Xóa bỏ triệt để thư mục clone thừa thãi `skills/_SYSTEM/`:** Loại bỏ 4 bản sao duplicate không cần thiết.
- **Xóa các bản sao trùng lặp trong `_SHARED/`:** `SKILL_BRIDGE.md` và `INTER_SKILL_TRIGGERS.md` nay chỉ lưu 1 bản duy nhất tại `skills/`.
- **Xóa bản clone `SKILL_INDEX.md` ở root:** Chỉ giữ 1 bản SSOT duy nhất tại `skills/SKILL_INDEX.md`.
- **Dọn sạch rác, cache, output tạm:** Dọn dẹp toàn bộ 30+ thư mục `__pycache__`, xóa các thư mục rỗng `test_output`, `.claude`, chuẩn hóa `.gitignore`.

### Files moi & Thay doi

| File / Folder | Mo ta |
|---------------|-------|
| `.agents/tests/run_all_tests.py` | Master Test Runner chạy toàn bộ 6 test suites trong 1 lệnh |
| `.agents/tests/integration_test.py` | Di chuyển từ root sang tests/, 67 checks passed |
| `.agents/tests/test_runner.py` | Di chuyển từ skills/ sang tests/, 13 calculators passed |
| `.agents/docs/` | Thư mục tập trung báo cáo đề án & tài liệu kiến trúc |
| `.agents/skills/_SYSTEM/` | Đã xóa bỏ hoàn toàn (không còn file clone thừa) |
| `.agents/.gitignore` | Chuẩn hóa, bổ sung loại bỏ cache, artifacts tạm thời |

---

## 2026-10-13 — v6.2: Đồng bộ Toàn diện & Trích xuất Thực thể Kỹ thuật (Entity Extraction)

### Tong quan

Hoàn thiện rà soát tổng hợp hệ thống và triển khai các nhiệm vụ trọng tâm:
- **Đồng bộ SSOT 100%:** Đồng bộ byte-for-byte các văn bản cốt lõi (`SKILL_INDEX.md`, `CHANGELOG.md`, `AGENTS.md`) tại cả 3 vị trí (`.agents/`, `skills/`, `_SYSTEM/`).
- **Nâng cấp `INTEGRATION_TEST.py`:** Bổ sung `Global_Dispatcher` và 3 scripts điều phối trung tâm (`intent_classifier.py`, `pipeline_builder.py`, `approval_gate.py`) $\rightarrow$ Đạt **67/67 checks passed (100%)**.
- **Cài đặt `EntityExtractor` (P1 Slot Filling):** Tích hợp vào `intent_classifier.py` để bóc tách tự động hình học ($b, h, L$, chiều dày sàn), vật liệu chuẩn TCVN, nội lực ($M, V, N, q$), và tự động sinh các giả định kỹ thuật (`ASSUMED`).
- **Hoàn thiện Guardrails trong `pipeline_builder.py`:** Bổ sung cờ `requires_pre_approval = True` cho multi-stage pipelines và chốt hạn mức `max_repair_iterations = 3`.

### Files moi & Cap nhat

| File | Mo ta |
|------|-------|
| `SKILL_INDEX.md` (root) | Cập nhật v2.0 đồng bộ với `skills/SKILL_INDEX.md` |
| `_SYSTEM/CHANGELOG.md` | Cập nhật đồng bộ với `skills/CHANGELOG.md` |
| `INTEGRATION_TEST.py` | Bổ sung Global_Dispatcher và 3 core scripts điều phối (67 checks) |
| `Global_Dispatcher/scripts/intent_classifier.py` | Bổ sung class `EntityExtractor` cho slot filling kỹ thuật |
| `Global_Dispatcher/scripts/pipeline_builder.py` | Bổ sung `requires_pre_approval` và `max_repair_iterations = 3` |

---

## 2026-10-12 — Global Dispatcher: Bộ Điều phối Trung tâm (Central Orchestrator)

### Tong quan

Giải quyết vấn đề cognitive load khi hệ thống có 12 skills riêng lẻ:
- Tạo skill `Global_Dispatcher` với vai trò Central Orchestrator
- Python Intent Classifier phân tích prompt ngôn ngữ tự nhiên thành skill và confidence score (100% test pass)
- Database 220+ keywords, regex patterns, anti-keywords và tie-breaker rules
- Multi-skill Pipeline Builder tự động chuỗi hóa các workflow phức tạp (ví dụ: SDE → Review Gate → DE)
- Đồng bộ toàn diện `AGENTS.md` (v6.0), `SKILL_INDEX.md` (v2.0), và `README.md`

### Files moi & Cap nhat

| File | Mo ta |
|------|-------|
| `Global_Dispatcher/SKILL.md` | Instruction chính: Quy trình phân loại intent, định tuyến, và quản lý pipeline |
| `Global_Dispatcher/scripts/intent_classifier.py` | CLI phân tích prompt, tính confidence score, áp dụng tie-breakers, phát hiện pipeline |
| `Global_Dispatcher/scripts/keyword_database.json` | CSDL 220+ keywords phân theo 12 skills, regex patterns, tie-breaker rules, pipeline templates |
| `Global_Dispatcher/scripts/pipeline_builder.py` | CLI tự động xây dựng stage pipeline, liên kết handoff schema, thiết lập review gates |
| `AGENTS.md` (3 vi tri) | Nâng cấp v6.0: Bổ sung mục 0.1 Global Dispatcher tự động |
| `SKILL_INDEX.md` | Nâng cấp v2.0: Bổ sung Global_Dispatcher vào cây kiến trúc và danh mục skill |
| `README.md` | Cập nhật hướng dẫn khởi đầu nhanh với Global Dispatcher |

---

## 2026-09-27 — P1: Agentic Workflow Infrastructure

### Tong quan

Trien khai day du Agentic Workflow Infrastructure (Phan 1):

1. **Confidence Score Calculator** — 5-factor model
2. **Validation Scripts** — Schema validation
3. **Handoff Manager** — CLI cho lifecycle management

### Files moi (P1)

| File | Mo ta |
|------|-------|
| `_SHARED/SHARED_CONTEXT/validate_handoff_schema.py` | Validate JSON schema, check required fields, version compatibility |
| `_SHARED/SHARED_CONTEXT/confidence_score.py` | Calculate confidence level (5 factors, weighted) |
| `_SHARED/SHARED_CONTEXT/handoff_manager.py` | CLI: create/list/validate/archive/reject/receipt |
| `_SHARED/SHARED_CONTEXT/samples/geotech_to_structural_sample.json` | Sample foundation params handoff |
| `_SHARED/SHARED_CONTEXT/samples/structural_to_verify_sample.json` | Sample QA check request |
| `_SHARED/SHARED_CONTEXT/trigger_log.json` | Template cho trigger logging |

### Confidence Score Model

**5 Factors (weighted sum):**
| Factor | Weight | Check |
|--------|--------|-------|
| `data_completeness` | 25% | Required fields present |
| `input_quality` | 20% | Material grades, dimensions valid |
| `standard_compliance` | 20% | Standards properly cited |
| `calculation_consistency` | 20% | Internal log consistency |
| `source_reliability` | 15% | Measured/Calculated/Estimated |

**Thresholds:**
- HIGH: score ≥ 0.85
- MEDIUM: 0.60 - 0.84 → Auto-send to SKILL_VERIFY
- LOW: < 0.60 → **BLOCK** file export

### Handoff Manager CLI

```bash
# Create handoff
python handoff_manager.py create foundation_params PROJ001 \
    --source SKILL_GEOTECH --target Structural_Design_Engineer \
    --data data.json --confidence HIGH

# List handoffs
python handoff_manager.py list --status active

# Validate handoff
python handoff_manager.py validate geotech_to_structural_PROJ001_xxx.json

# Create receipt
python handoff_manager.py receipt handoff.json --processor SKILL_VERIFY

# Archive completed
python handoff_manager.py archive handoff.json

# Reject with reason
python handoff_manager.py reject handoff.json --reason "Missing phi_deg field"
```

### Versions

| File | Truoc | Sau |
|------|-------|-----|
| AGENTS.md | v5.7 | **v5.9** |
| SKILL_INDEX.md | v1.7 | **v1.9** |

---

## 2026-09-26 — P0: Agentic Workflow Infrastructure

### Tong quan

Trien khai 2 file P0 giai quyet blind spots trong he thong hien tai:
1. **SKILL_BRIDGE.md** — Data contracts & handoff protocol
2. **INTER_SKILL_TRIGGERS.md** — Quy tac tu dong goi skill

### Files moi

| File | Mo ta |
|------|-------|
| `SKILL_BRIDGE.md` | Data contracts JSON schema + validation + receipt protocol |
| `INTER_SKILL_TRIGGERS.md` | 15 triggers tu dong, error handling, circular dependency prevention |
| `_SHARED/SHARED_CONTEXT/README.md` | Huong dan su dung SHARED_CONTEXT directory |
| `_SHARED/SHARED_CONTEXT/_active/` | Thu muc handoff dang xu ly |
| `_SHARED/SHARED_CONTEXT/_archive/` | Thu muc handoff da xu ly |
| `_SHARED/SHARED_CONTEXT/_rejected/` | Thu muc handoff bi tu choi |

### Data Contracts (SKILL_BRIDGE.md)

5 JSON schema cho inter-skill handoff:

| Schema | From | To | Content |
|--------|------|----|---------|
| `geotech_to_structural` | SKILL_GEOTECH | Structural_Design_Engineer | Foundation params |
| `structural_to_verify` | Structural_Design_Engineer | SKILL_VERIFY | QA check request |
| `structural_to_cost` | Structural_Design_Engineer | Cost_Estimator | Design output for VE |
| `design_eval_to_cost` | Design_Evaluation | Cost_Estimator | VE analysis request |
| `geotech_to_design_eval` | SKILL_GEOTECH | Design_Evaluation | Foundation review |

### Auto-Invocations (INTER_SKILL_TRIGGERS.md)

15 triggers chia 3 categories:

**Post-Completion Triggers (AUTO):**
| Trigger | Source | Target | Condition |
|---------|--------|--------|-----------|
| POST-GEOTECH-01 | SKILL_GEOTECH | Structural_Design | Soil params complete |
| POST-GEOTECH-02 | SKILL_GEOTECH | Design_Evaluation | Base heave complete |
| POST-GEOTECH-03 | SKILL_GEOTECH | SKILL_FORENSIC | Adverse conditions |
| POST-DESIGN-01 | Structural_Design | SKILL_VERIFY | Design complete (BAT BUOC) |
| POST-DESIGN-02 | Structural_Design | Cost_Estimator | η ≤ 0.70 |
| POST-DESIGN-03 | Structural_Design | Technical_Illustrator | Need drawing |
| POST-EVAL-01 | Design_Evaluation | Cost_Estimator | High cost detected |
| POST-EVAL-02 | Design_Evaluation | SKILL_VERIFY | Standard conflict |
| POST-VERIFY-01 | SKILL_VERIFY | Source Skill | Variance > 5% |
| POST-COST-01 | Cost_Estimator | Structural_Design | VE potential |

**Escalation Triggers (BLOCKING):**
| Trigger | Condition | Action |
|---------|-----------|--------|
| ESC-001 | Missing Data (E002) | Block + request upstream |
| ESC-002 | Standard Conflict (E004) | Escalate SKILL_VERIFY |
| ESC-003 | Low Confidence | Block file export |
| ESC-004 | Safety Issue | Escalate SKILL_FORENSIC |

### Key Improvements

1. **Loai bo thao thong tin** — Schema validation bat buoc
2. **Tu dong orchestration** — Skills goi nhau khong can User ra lenh
3. **Block halluncination** — POST-DESIGN-01 BAT BUOC verify truoc xuat file
4. **Circular dependency prevention** — Max depth = 5

### Versions

| File | Truoc | Sau |
|------|-------|-----|
| AGENTS.md | v5.7 | **v5.8** |
| SKILL_INDEX.md | v1.7 | **v1.8** |

---

## 2026-09-25 — Critical Fixes

### Tong quan

Sua cac loi nghiem trong duoc phat hien qua audit toan bo he thong.

### Fixes

| File | Van de | Fix |
|------|-------|-----|
| `STANDARDS_LOCK.md` | Version outdate (v2.4.0) | Cap nhat len v3.0.0 |
| `SKILL_INDEX.md` | Version mismatch | Dong bo: DE v2.2.0, GEOTECH v3.0.0 |
| `AGENTS.md` | Version header loi | Cap nhat len v5.7 |
| `Design_Evaluation/SKILL.md` | Deprecated script reference | Sua steel_member_check.py → steel_member_check_v2024.py |
| `CHANGELOG.md` | Encoding loi | Viet lai UTF-8 |
| `SKILL_GEOTECH` | Missing lazy load section | Them muc Lazy Load |

### Versions moi

| File | Truoc | Sau |
|------|-------|-----|
| AGENTS.md | v5.6 | **v5.7** |
| SKILL_INDEX.md | v1.6 | **v1.7** |
| STANDARDS_LOCK.md | v2.4.0 | **v3.0.0** |

---

## 2026-09-20 - SKILL_GEOTECH v3.0.0 - Full TMTT Automation

### Tong quan

Nang cap toan dien `THUYET_MINH_TEMPLATE.md` thanh Template 6 Chuong + Phu luc A bat buoc (giai trinh step-by-step E50/Eur/K0/Rinter tung lop + bang Ground Truth). Tao MODULE 18 `format_etabs_output.py` tu dong dinh dang bang ETABS Design Summary thanh Markdown dep voi mau danh gia va ket luan tu dong.

### Files moi

| File | Mo ta |
|------|-------|
| `format_etabs_output.py` | MODULE 18: Dinh dang bang ETABS Design Summary |
| `references/ETABS_SHORING_GUIDE.md` | Huong dan mo hinh ETABS cho he Shoring |

### Changes

- MODULE 18: Tu dong dinh dang PMM Ratio, D/C Ratio voi mau tu dong
- Thuyet minh BPTC: 6 Chuong + Phu luc A bat buoc

### Versions

| File | Truoc | Sau |
|------|-------|-----|
| SKILL_GEOTECH | v2.4.0 | **v3.0.0** |

---

## 2026-09-20 - SKILL_GEOTECH v2.4.0 - Urban Excavation Upgrade

### Tong quan

Them cac module cho hoi dao trong thanh pho.

### Tinh nang moi

| Module | File | Mo ta |
|--------|------|-------|
| MODULE 12b | `calc_waling_beam_capacity.py` | Kiem tra kha nang chiu uon Dam bo (Waling Beam) |
| MODULE 13 | `assess_excavation_geometry.py` | Phan tich hinh hoc mat bang hoi dao |
| MODULE 15 | `calc_corner_brace.py` | Tinh toan he chong goc xien |
| MODULE 16 | `calc_plaxis_model_geometry.py` | Tinh kich thuoc mo hinh Plaxis |

### Versions

| File | Truoc | Sau |
|------|-------|-----|
| SKILL_GEOTECH | v2.3.0 | **v2.4.0** |

---

## 2026-09-16 - SKILL_GEOTECH v2.0.0 - Tich hop CPTu, SSC, SLS, Pile Load Test

### Tinh nang moi

| Tinh nang | Mo ta |
|-----------|-------|
| **CPTu Support** | Ap luc lo rong, Nkt dong dua tren Bq/Ip, OCR tu CPTu |
| **Soft Soil Creep (SSC)** | Thong so lambda*, kappa*, mu* tu Oedometer |
| **Eurocode 7 & CIRIA C760** | Tich hop de chon Rinter, SBT 2016 |
| **Stiffness Degradation** | Suy giam do cung cho tuong vay (cracked section) |
| **SLS Check** | Kiem chung chuyen vi ngang (Clough & O'Rourke) |
| **Pile Load Test** | Dien dich thi nghiem nen tinh coc (Davisson, Chin-Kondner) |

---

## 2026-09-01 — PHULUC Upgrade (v4.2) — Phu Luc Tinh Toan Chuyen Nghiep

### Tao

| File | Mo ta |
|------|-------|
| `SKILL_PHULUC/SKILL.md` | Skill entry point |
| `SKILL_PHULUC/references/MATERIAL_TABLES.md` | Bang tra vat lieu |
| `templates/appendix/APPENDIX_BEAM_RC.md` | Template dam BTCT |
| `templates/appendix/APPENDIX_COLUMN_RC.md` | Template cot BTCT |
| `templates/appendix/APPENDIX_STEEL_BEAM.md` | Template dam thep |

### Cau truc Phu luc (Step-by-Step)

1. THONG TIN CHUNG
2. VAT LIEU (day du bang tra)
3. TAI TRONG (tinh tai, hoat tai, to hop)
4. SO DO KET CAU (hinh ve)
5. NOI LUC (bang chi tiet)
6. TINH TOAN CHI TIET
   - Buoc 1: ...
   - Buoc 2: ...
   - Kiem tra: η = ...
7. BANG TONG HOP
8. KET LUAN
9. PHU LUC (bang tra, he so)
10. CHU KY XAC NHAN

---

## 2026-08-31 — Reporting Upgrade (v4.1)

### Tinh nang chinh

Unified Dispatcher + 5 Audience Profiles

### Files moi

| File | Mo ta |
|------|-------|
| `scripts/_lib/_docx_helpers.py` | DOCX helpers: cover page, TOC, headers |
| `scripts/_lib/_report_utils.py` | Formatters: η, citation, currency |
| `scripts/_lib/_chart_inserter.py` | Charts: radar, bar, progress |
| `scripts/_lib/_executive_dashboard.py` | Dashboard cho Owner |
| `scripts/_lib/_audience_profiles.py` | 5 profiles |
| `scripts/report_dispatcher.py` | Unified CLI |
| `scripts/xlsx_report.py` | Excel: BOQ, Calc, Comparison |
| `SKILL_RFI/scripts/document_renderer.py` | RFI DOCX/MD renderer |

### 5 Audience Profiles

| Audience | Use Case | Sections day du |
|----------|----------|-----------------|
| `designer` | Tu van thiet ke | Cover + TOC + Dashboard + Logs + Citations + Charts |
| `engineer` | Ky su tinh toan | Cover + TOC + Logs + Charts |
| `contractor` | Nha thau thi cong | Cover + TOC + Project Info + Charts + Approval |
| `owner` | Chu dau tu | Cover + Dashboard + Comparison + Charts |
| `authority` | Co quan quan ly | Cover + TOC + All sections + Full audit |

---

## 2026-08-31 — Final Audit & Validator Fix (v4.0)

### Van de da sua

| Issue | Mo ta | Fix |
|-------|-------|-----|
| **VALIDATOR-BROKEN** | `validate_registry.py` khong bao gio chay duoc | Rewrite de dung `name` field |
| **DASHBOARD-FORMAT-MISMATCH** | `rfi_dashboard.py` chi doc field `rfis` cu | Rewrite de iterate qua `documents.{type}` |
| **REGISTRY-MISSING-DCE** | 5 DCE scripts khong co trong registry.json | Them DCE scripts voi `status: ACTIVE` |

### Audit ket qua

- 89 Python scripts
- 7 SKILL.md files (dong bo version)
- 77 .md references
- 5 _deprecated/ scripts
- 6 loai documents trong registry

---

## 2026-08-30 — SKILL_RFI Extended (v3.9)

### Cac loai tai lieu

| Loai | Ma | Mo ta |
|------|-----|-------|
| **RFI** | Request for Information | Yeu cau lam ro thong tin |
| **NCR** | Non-Conformance Report | Bao cao khong phu hop |
| **Submittal** | Shop Drawing/Material | Ban ve thi cong |
| **Change Order** | CO | Yeu cau thay doi khoi luong |
| **Tech Query** | TQ | Cau hoi ky thuat chuyen sau |
| **Pre-Bid RFI** | PB-RFI | Lam ro truoc dau thau |

---

## 2026-08-30 — Audit Fixes & Standards Synchronization (v3.7)

### Van de da sua

| Issue | Mo ta | Fix |
|-------|-------|-----|
| REGISTRY_INDEX-SCRIPT-NAMES | Script names khong khop voi files thuc te | Viet lai REGISTRY_INDEX.md |
| SKILL_INDEX-VERSION-MISMATCH | SKILL_INDEX ghi version cu cho 2 skills | Cap nhat: SDE v1.3.0, TI v1.3.0, DE v2.1.1 |
| REGISTRY_JSON-DEPRECATED | Deprecated scripts khong co `status` | Them `status: "DEPRECATED"` |

---

## 2026-08-30 — DCE Pro Integration (v3.6)

### Luong hoat dong

```
AI Agent (Claude Code)
     |
     +-- 1. Tinh toan ket cau
     +-- 2. Goi dce_writer.py --> dieu data vao Excel
     +-- 3. DCE Pro Add-In doc Excel --> ve CAD
     +-- 4. Agent trich xuat PDF/DWG
```

### Templates duoc ho tro

| Module | Template DCE |
|--------|-------------|
| Dam BTCT | `09. DCE_Beam_2020.xlsm` |
| Cot BTCT | `08. DCE_ColumnWall_2020.xlsm` |
| Thep Dam | `20. TCVN 5575 Steel Beam Design - Section I.xlsm` |
| Thep Cot | `25. TCVN 5575 Steel Column Design - Section I.xlsm` |
| Bu long neo | `160. Chi tiet bu long neo.xlsm` |

---

## 2026-08-30 — Reorganization (v3.5)

### Cau truc moi

```
.agents/skills/
|
+-- _SYSTEM/
|   +-- AGENTS.md
|   +-- SKILL_INDEX.md
|   +-- STANDARDS_LOCK.md
|
+-- _CORE_SKILLS/
|   +-- Design_Evaluation/
|   +-- Structural_Design_Engineer/
|   +-- Technical_Illustrator/
|
+-- _SUPPORT_SKILLS/
|   +-- Cost_Estimator/
|   +-- SKILL_FORENSIC/
|   +-- SKILL_VERIFY/
|   +-- SKILL_RFI/
|   +-- SKILL_PHULUC/
|   +-- SKILL_GEOTECH/
|
+-- _SHARED/
+-- README.md
+-- CHANGELOG.md
```

---

## 2026-08-30 — Phase 1 Quick Wins (v3.2)

### Scripts moi

| Script | Mo ta |
|--------|-------|
| `validate_registry.py` | Kiem tra consistency giua registry.json va actual files |
| `validate_handoff.py` | Validate JSON handoff tu SKILLKC → SKILL_REPORT |

### Eurocode Scripts da xu ly

| Script | Hanh dong | Trang thai |
|--------|----------|-----------|
| `calc_steel_beam.py` | Di chuyen → `_deprecated/` | Hoan thanh |
| `calc_steel_connection.py` | Di chuyen → `_deprecated/` | Hoan thanh |

---

## 2026-08-25 — Complete Fixes & TCVN 5575:2024 Scripts (v3.1)

### Scripts moi — TCVN 5575:2024

| Script | Mo ta |
|--------|-------|
| `calc_steel_beam_tcvn.py` | Kiem tra dam thep: uon + cat + LTB + vong |
| `calc_steel_connection_tcvn.py` | Kiem tra lien ket bu long: cat + ep mat + keo |

**Verification:**
- `calc_steel_beam_tcvn.py`: I400x200x8x13, M_ed=220kNm → eta_M=54.7%, eta_V=27.7%, eta_LTB=57.3%, eta_f=51.8% → PASS
- `calc_steel_connection_tcvn.py`: M20 cap 8.8, 6 bu long → eta_shear=31.9%, eta_bearing=43.4%, eta_tension=5.9% → PASS

---

## 2026-08-25 — Critical Cleanup & Governance Fixes (v3.0)

### Deprecated Scripts da di chuyen

5 script fixed-geometry da duoc di chuyen sang `scripts/_deprecated/`:

| Script | Ly do |
|--------|-------|
| `draw_ap_luc_dat_bo_ke.py` | Fixed geometry |
| `draw_ke_buy_dung.py` | Fixed geometry |
| `draw_ke_pi_gieng.py` | Fixed geometry |
| `draw_pi_gieng_composite.py` | Fixed geometry |
| `draw_tham_da.py` | Fixed geometry |

---

## 2026-08-18 — Critical Bug Fixes & Standards Cleanup (v2.1.1)

### Critical Fixes

| Bug ID | File | Issue | Fix |
|--------|------|-------|-----|
| BUG-01 | `calc_steel_beam.py` | `GAMMA_M1 = 1.05` (sai) | Changed to `GAMMA_M1 = 1.10` |
| BUG-02 | `calc_steel_beam.py` | `ALPHA_LT = 0.34` (sai) | Changed to `ALPHA_LT = 0.21` |
| BUG-03 | `steel_member_check_v2024.py` | `M_c_Rd * 10` (vo nghia) | Removed `* 10` |

---

## 2026-08-18 — Major Cleanup & Synchronization (v2.0)

Dong bo toan bo 6 skills, tao CHANGELOG tap trung.

---

## 2026-07-28 — AGENTS.md v3.0 & STANDARDS_LOCK v1.0

- Them van phong ky thuat chuan hoa
- Them version control cho file output
- Tao STANDARDS_LOCK.md lam nguon su that duy nhat ve tieu chuan
- Bo sung Citation Object 6 truong

---

## 2026-07-15 — Deterministic Math v2.0

- Bat buoc goi script tinh toan, cam nham tay
- Yeu cau moi script tra ve `Calculation_Logs` + `Standard_Method`
- Mo rong Standards Version Lock

---

## 2026-06-01 — Initial Release

- 3 skills ban dau: Design_Evaluation, Structural_Design_Engineer, Technical_Illustrator
- AGENTS.md v1.0 voi 11 dieu
