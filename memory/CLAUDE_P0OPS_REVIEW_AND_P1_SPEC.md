# REVIEW P0-OPS & SPEC P1 (SCHEMA-GATE AUTHORING)

> **Từ:** CLAUDE (review ca bàn giao của GEMINI)  
> **Ngày:** 2026-11-16  
> **Phạm vi:** phản biện P0-OPS + đề xuất P1. Chưa sửa code; P1 do GEMINI triển khai sau khi User duyệt.

---

## 1. VERDICT P0

P0 vững về kiến trúc: workspace chuẩn, model versioning + revisions, lineage append-only,
4 lệnh runbook, NCR diff-regen đúng (chỉ tái sinh tờ chứa element — đã xác nhận qua
`test_05`: KC-03 giữ nguyên SHA256). 5/5 test P0 xanh.

Nhưng có **1 điểm quá lời về compliance** và **2 bug schema tiềm ẩn** nên chốt trước khi P1:

| # | Mức | Vấn đề | Vị trí |
|---|---|---|---|
| F1 | 🔴 High | `build_project_dossier` chạy `audit(profile="physical")` rồi báo `audit_status=PASS`, runbook gọi "**PASS Bộ lọc 8**". `physical` = gate `NOT_RUN` (chỉ kiểm DXF vật lý). Đây là **overclaim** — 20 gate logic chưa chạy. | `project_ops_manager.py:507` + runbook |
| F2 | 🟠 Med | `model_schema.json` hard-code đúng 5 mã TCVN làm `required` → gắn cứng schema vào version `STANDARDS_LOCK`; ép 5 chuẩn lên cả dự án đơn giản. | `model_schema.json` (standards_ref) |
| F3 | 🟠 Med | `anyOf` top-level trỏ `L_total`/`B_total` sai tầng (thực ra trong `project`) → nhánh chết, "chặn thiếu kích thước" mà thật ra không chặn. | `model_schema.json` (anyOf) |
| F4 | 🟡 Low | `BLOCK_CATALOG_VERSION` là chuỗi cứng, không đọc từ catalog SSOT → lineage under-claim. | `project_ops_manager.py:67` |
| F5 | 🟡 Low | Model + NCR có versioning, nhưng **Form không có revision** (`set-layer` sửa in-place, chỉ re-hash lock). | `project_ops_manager.py` runbook_set_layer |
| F6 | 🟡 Low | Hai chỗ trích element-id tách biệt (NCR matching vs `_collect_sheet_element_ids`) → rủi ro lệch. | `project_ops_manager.py` |
| F7 | 🟡 Low | Fallback khi thiếu `jsonschema` chỉ kiểm 4 key gốc → schema-gate vô răng mà im lặng. Nên hard-require / raise. | `project_ops_manager.py:139` |

**Điểm cộng:** atomic write (tmp+fsync+replace), NCR schema-gate trước khi ghi revision,
SSOT guard layer, zone/UCS/DXF-version checks trong `validate_open_form`, block_catalog_lock.

---

## 2. SPEC P1 (THEO THỨ TỰ TRIỂN KHAI)

### Khối 1 — P0-hardening (làm đầu, rẻ, KHÔNG đụng 194 test)
1. **F1 (bắt buộc):** dossier builder giữ `physical` nhưng đổi nhãn thành
   `DXF_INTEGRITY_PASS` (cấm dùng cụm "Bộ lọc 8" cho profile=physical).
   Thêm flag `--compliance {physical,plan,full}`; khi chọn full/plan, báo
   `NEEDS_REVIEW` trung thực nếu có gate UNVERIFIED (không gán PASS).
2. **F2:** nới `standards_ref` — thay `required` 5 key bằng `minProperties>=1` +
   validate chéo version với `STANDARDS_LOCK.md` khi load (không bake version vào schema).
3. **F3:** sửa `anyOf` về tầng `project` (tham chiếu `project.L_total`/`project.B_total`)
   hoặc bỏ if redundant.
4. **F4:** đọc `BLOCK_CATALOG_VERSION` từ catalog SSOT (một hằng/đọc file), không hard-code.
5. **F7:** thiếu `jsonschema` → raise `ImportError` rõ (không fallback vô răng).
6. **F5/F6 (nên làm cùng lúc):** thêm form revision (form_v00N) trong `forms/` +
   gộp 2 chỗ trích element-id thành 1 hàm dùng chung.

### Khối 2 — Schema-Gate Authoring (sườn P1 đã chốt, cơ chế (C) HYBRID)
Mục tiêu: User sửa Form trong AutoCAD (trục/layer/khung tên) → agent đọc ngược →
**chỉ commit vào model (version+1) khi hợp lệ**, không ghi đè hình học User.

- **`model_diff.py`** (cad_integration):
  - `extract_form_diff(form_dxf, manifest, baseline=ssot|prev_rev) -> FormDiff`
    diff semantic: trục dịch, layer đổi (color/lw), titleblock ATTRIB đổi, zone bbox dịch.
    Mỗi entry ánh xạ tới **model-field path** (`project.grid_x[i][1]`, `project.project_name`, …) + confidence.
  - `apply_form_diff_to_model(model, diff) -> candidate` → **`validate_model_dict` (schema-gate)**
    → sai thì `E005/E006` + diff, **không tự sửa model**; đúng thì commit version+1.
- **3 merge-lane MCP tools** (trong `mcp_dce_cad_server.py`):
  - `open_form(project_dir, form_id)` — đọc form User đã save, audit theo manifest (read-only,
    trả inventory + tier + roundtrip_status). Không copy/overwrite.
  - `diff_form(project_dir, form_id, baseline="ssot")` — chạy `extract_form_diff`, trả list thay đổi
    nhóm theo layer / titleblock / zone / axes kèm model-field mapping.
  - `apply_agent_changes(project_dir, form_id, changes, commit=True)` — **region-scoped**:
    chỉ chạm entity appid `DCE_AGENT_OWNED`; áp vào model (version+1) qua schema-gate;
    tái sinh chỉ tờ ảnh hưởng (tận dụng NCR diff-regen). Không đụng hình học User.

### Khối 3 — "Bộ lọc 8 thật sự PASS" (thưởng, mở rộng P0 evidence; có giá trị thật)
- Mở `DcePlanEngine._v6_derive_v4_claims()` phát đủ semantic claims:
  `entities_log` (tier/base/bbox/insert), `blocks_defined` (has_solid_hatch/attdefs),
  dimstyles (dimtxt/dimscale/arrow), layers (lineweight>0) — đúng shape 20 gate cần.
- Gated `full_evidence: bool = False`; khi ON, `audit(profile="full")` có thể PASS thật
  (thay vì NEEDS_REVIEW). Default OFF + test riêng → giữ 194 test xanh.
- Đây là nơi "PASS Bộ lọc 8" thật sự đạt được cho tờ vẽ sinh ra — nối tiếp P0 evidence-contract.

### TEST P1 (~10 test mới, không sửa test cũ)
- diff extraction (trục/layer/titleblock/zone), schema-gate reject 1 form edit sai,
  apply + regen chỉ tờ ảnh hưởng, region-scope (không chạm User geometry),
  multi-viewport cùng `element_id`, missing-zone fail, `full_evidence` off/on,
  form revision tăng, BLOCK_CATALOG_VERSION đọc từ SSOT.

---

## 3. GUARDRAIL
- Giữ 194/194 (16 suites) xanh ở mọi bước; chỉ THÊM test.
- Không refactor legacy `cad_plan_engine`/`cad_multiview_a3` trong P1; mọi chế độ mới qua flag.
- Cấm gán `full_compliance_verified=true` khi thiếu native block/ATTRIB + zone evidence (đúng P0 evidence).
- Mỗi khối bàn giao qua Bus + 1 ca thật + soi `render_preview` (Rule 12d.6).

## 4. ĐIỂM CẦN USER/GEMINI CHỐT TRƯỚC KHI CODE P1
- **F1:** đồng ý đổi nhãn `physical → DXF_INTEGRITY` và thêm flag `--compliance` chưa? (khuyến nghị: có)
- **Khối 3:** có bật `full_evidence` (làm Bộ lọc 8 PASS thật) trong P1 luôn, hay để P2? (khuyến nghị: P1, default off)
- **Region-scoping:** appid `DCE_AGENT_OWNED` đã có; xác nhận dùng nó làm biên giới engine/user geometry.
