# SPEC P2 — MCP Perception Loop (bằng chứng bắt buộc trước Report Gate)

**Trạng thái:** KHÉP HỢP ĐỒNG (2026-11-20) — CLAUDE soạn, GEMINI (Antigravity) duyệt 100% + **nghiệm thu đạt** biên nhận `RECEIPT_CLAUDE_NEED_REVIEW_20261120-105415.json` (RCP_20261120-105415, APPROVED) · GEMINI tiếp quản mục 2 (4 trách nhiệm Antigravity) trong các ca CAD kế tiếp · **Căn cứ:** `DUAL_AGENT_ANTIGRAVITY_ORCHESTRATION_ANALYSIS.md` mục (5), `RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md`, SSOT `sync_bus.py` v3.3.

**Mục tiêu:** Loại bỏ bất đối xứng "một phía nhìn được kết quả". Cả 2 phía chạy **cùng 1 server MCP `dce-cad`** (13 tools, đã đăng ký trong `mcp_config.json`, clients = `Claude Code, Claude Desktop, Antigravity IDE, Cursor`) để **render → soi ảnh → sửa → tái validate** trong ca CAD/Visual; kết quả **bắt buộc** được bắt về đĩa (preview PNG + SHA-256) trước khi Report/Visual Gate cho phép đóng ca.

---

## 1. Interface server MCP chung — `.agents/tools/mcp_dce_cad_server.py`

Server tên `dce-cad`, chạy `python -B <abs>.../mcp_dce_cad_server.py` (env `ODA_FILE_CONVERTER` cho DWG). 13 tools public (`@_tool`):

| Nhóm | Tool (tham số chính) | Vai trò trong loop |
|---|---|---|
| Sinh CAD | `render_cad_plan(sheet_type, model_json_path, v6, dry_run)` · `auto_layout_and_scale_plan(json_model_path, target_sheet, render_preview_png, dry_run)` · `export_cad_sheet_set(model_json_path, sheet_types, render_preview)` | Tạo DXF chuẩn DCE Pro (khung A1, 4 tầng dim, hatch, sidecar `.dce_audit.json`) |
| **Perception (Vision)** | `render_preview(dxf_path, dpi=150–300, view_box)→preview_id` · `consume_preview(preview_id)→image` · `release_preview(preview_id)` | DXF→PNG độ nét cao; nạp ảnh vào response; tự dọn PNG (token 1 lần) |
| Validate | `validate_cad(dxf_path, profile=full/plan/physical)` | Bộ lọc 8 / 20 cổng G8.01–G8.20; trả `full_compliance_verified` (PASS/FAIL/NEEDS_REVIEW) |
| Sửa | `edit_entity(session_dir, handle, dx, dy, expected_revision, dry_run)` · `resolve_cad_collisions(dxf_path, dry_run)` | Dịch TEXT/DIM revision-locked; giải xung đột nhãn (Leader line) |
| Form | `open_form(project_dir, form_id)` · `diff_form(project_dir, form_id, baseline)` · `apply_agent_changes(project_dir, form_id, changes, commit, compliance)` | Đọc/so/merge Form DXF user (region-scoped, schema-gate) |
| Chuyển đổi | `convert_to_dwg(dxf_path, output_dwg_path, version)` | Chuyển đổi định dạng DXF sang DWG chuẩn AutoCAD (qua ODA/CAD CLI) |

**Chuẩn loop (≤3 vòng):** `render/auto_layout(dxf)` → `render_preview(dpi=150)` → `consume_preview(soi)` → `resolve_cad_collisions(dry_run=True)` + `edit_entity` (sổ) → `validate_cad(profile=full)` → (nếu FAIL) lặp; (nếu PASS) `release_preview` + **đóng băng bằng chứng (mục 3)**.

## 2. Trách nhiệm cụ thể phía Antigravity (GEMINI) cần implement

1. **Đăng ký server `dce-cad` vào Antigravity IDE** — bridge MCP phải expose **đủ 13 tools trên**, cùng 1 instance với Claude Code (không fork logic riêng).
2. **Chạy perception loop chuẩn** trong ca CAD/Visual — kết quả **không được để chỉ trong transcript** (điểm yếu đã ghi ở phân tích mục 4). Mỗi ca CAD phải chạy ≥1 vòng `render→consume_preview→validate_cad`.
3. **Bắt bằng chứng về đĩa cuối vòng** — ghi (a) preview PNG cuối + (b) audit JSON của `validate_cad` (`full_compliance_verified=true`) vào đường dẫn **trụ** (không dùng preview tạm bị TTL xóa), rồi truyền cả hai vào bus trường `next_action_for_partner.evidence_files`.
4. **Điền `RESULT.md` 5 mục** theo P1 (`--emit-report`, layout `audits/<project>/<agent>/<PHASE>_RESULT.md`) — mục `RESULTS` phải trích số liệu `validate_cad` (20 cổng, fill-ratio) + đường dẫn bằng chứng.

## 3. Contract bằng chứng BẮT BUỘC trước khi Report/Visual Gate cho phép đóng ca CAD/Visual

Ca `--action-type ∈ {CAD, DRAWING, DOCX, REPORT_VISUAL}` (GATED) **không đóng được** (`--complete`/`--need-review`/`--auto`) khi thiếu:

- **≥1 file ảnh preview** khớp `CAD_EVIDENCE_PATTERN` (`.png/.jpg/.jpeg/.webp/.preview.log/_verification.json`), và với `--check-evidence-on-disk` **phải THẬT SỰ TỒN TRÊN ĐĨA**;
- **Băm SHA-256** từng file bằng chứng → ghi vào `RECEIPTS/…json.evidence_hashes` + `bus_sha256` (cơ chế v3.3 đã code, receipt kèm chữ ký + lý do force khi bypass);
- **`report_file` (RESULT.md) tồn tại** (Report Gate P1).

**Nguồn của bằng chứng này = output của loop (mục 1):** preview PNG cuối + `validate_cad` JSON (chứng minh đã qua 20 cổng, không phải "tin lời" bus). Gate hiện enforce bằng `visual_gate_check(check_on_disk=True)` + `report_gate_check()` trong SSOT; P2 chỉ **bắt ca CAD phải sinh bằng chứng qua loop MCP chung** thay vì danh khai suông.

**Ngưỡng nghiệm thu P2:** một ca CAD chạy qua loop tạo đủ (preview PNG + audit JSON `full_compliance_verified=true` + RESULT.md đã điền) → bus đóng qua `--check-evidence-on-disk` + Report Gate, `receipt.evidence_hashes` có SHA-256 của PNG; **không** tồn tại ca CAD nào chỉ có kết quả trong transcript.

---
*Spec 1 trang · CLAUDE (chủ trì, đã code v3.3 gate) ↔ GEMINI/Antigravity (implement mục 2). Khi GEMINI nhận: chạy lại `--claim` → điền `G2_RESULT.md` theo P1 → hai bên đối soát loop trong sandbox `cad_v6` rồi mới bật trên ca thật.*
