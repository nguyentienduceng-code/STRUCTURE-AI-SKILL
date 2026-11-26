---
name: cad-v6-c2-v2-to-v3-remediation
description: Trạng thái sửa V2-01/02/03 của C2 v6 Block Semantics — v3 artifacts + kết quả validation
metadata:
  type: project
---

**Ngày 2026-07-10 — C2 v6 Block Semantics (project `09_DCE_CAD_BLOCK_SEMANTICS_V6`):**

CODEX A1 recheck v2 (`codex/recheck_v2/A1_V2_RECHECK_REPORT.md`) kết luận **PARTIAL — chưa phê duyệt**, mở 3 lỗi:
- **V2-01 (P0)**: bảng kê BOM 12 dòng chỉ nằm model-space (X 31000–41000), ngoài mọi viewport → 0 dòng in trên giấy A3.
- **V2-02 (P1)**: preview không đúng layout/A3 — **đã được source sửa sẵn** (PDF 5×A3 420×297, render per-viewport + frozen layer).
- **V2-03 (P0)**: chi tiết KC-03/04/06/07 gán cứng (`h=120`, `200x400/2D20+3D20`, `PL240x180x14`, rebar index-based), không chạy theo input.

**Đã sửa (CLAUDE, scope file C2):**
- `cad_sheet_set.py`: thêm `_emit_paperspace_schedule()` (vẽ BOM thật lên Layout1, band không chạm viewport, ghi `ps_schedule_handles` vào sidecar); `_add_sheet_role_specific_geometry()` giờ đọc `detail_design` (slab_panels/beam/steel_details + `detail_scale`) và `rebar_strips.region/bars/spacing_mm/cover_mm`; `_sheet_missing_inputs` chặn thiếu → `MISSING_INPUT`.
- Fixture `g2_steel_and_sheet_fixture.json` (test data): thêm block `detail_design` + các trường rebar.
- Tests mới: `test_08` (V2-01, 36/36 dòng giấy không clip) + `test_09` (V2-03, mutation input ⇒ geometry/label đổi, missing ⇒ MISSING_INPUT).

**Kết quả:**
- `c2_remediated_v3` (thư mục mới, giữ v2 nguyên): 8/8 gates validator độc lập PASS (`gemini/a1_06_linkage_validation_v3.json`), re-measure: 36/36 BOM paper rows on-sheet × 5 tờ, PDF A3, KC-06 label `MC-BM-D1A (200x400) | 2D20+3D20+D8a150 | B25`.
- `test_cad_v6_c2.py` 9/9, `test_dce_block_semantics.py` 13/13.

Báo cáo bàn giao: `cad_v6/claude/V2_REMEDIATION_REPORT_V3.md`. Trạng thái: chờ CODEX/GEMINI kiểm lại (không self-close bus).
