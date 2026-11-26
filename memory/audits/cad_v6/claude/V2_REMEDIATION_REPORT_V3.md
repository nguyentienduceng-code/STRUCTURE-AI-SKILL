# V2 REMEDIATION REPORT — c2_remediated_v3 (CLAUDE)

Ngày 2026-07-10. Dự án `09_DCE_CAD_BLOCK_SEMANTICS_V6`. Task C2 (v6 Block Semantics).

## Tóm tắt

Trả lời 3 lỗi của CODEX recheck v2 (`codex/recheck_v2/A1_V2_RECHECK_REPORT.md`):

| Lỗi | Trạng thái | Bằng chứng |
|---|---|---|
| V2-01 (P0) bảng kê không in trên giấy | **ĐÃ SỬA** | BOM 12 dòng thật (36 TEXT) vẽ trên `Layout1`, 36/36 resolve on-sheet không clip × 5 tờ |
| V2-02 (P1) preview không đúng layout/A3 | **ĐÃ SỬA (source đã có)** | PDF 5 trang = 420.0×297.0 mm đúng A3; render per-viewport + frozen layer |
| V2-03 (P0) chi tiết/thép gán cứng | **ĐÃ SỬA** | chi tiết/rebar dựng theo input; mutation test chứng minh input đổi ⇒ hình+label đổi; thiếu input ⇒ `MISSING_INPUT` |

## 1. Nội dung sửa (phạm vi file C2 của CLAUDE)

### `cad_sheet_set.py`
- **V2-01**: thêm `_emit_paperspace_schedule()` — vẽ BOM thật (12 phần tử × 3 ô: ký hiệu / tiết diện / tham chiếu) lên paperspace `Layout1` trong band không chạm viewport:
  - sheet 2 viewport (KC-02, KC-04): panel phải `[212..365]` (panel sẵn có).
  - sheet 1 viewport (KC-03/06/07): co viewport chính về `[15..300]` (scale view giữ nguyên, vẫn 1:50 — chỉ thay đổi kích thước khung view, view window model được fit lại), BOM vào band phải `[305..365]`.
  - Mỗi dòng ghi `ps_schedule_handles` (3 handle TEXT) vào `entity_map[element_id]` của sidecar → strict 3-way linkage vẫn resolve schedule trên **giấy**, không chỉ model.
- **V2-03**: `_add_sheet_role_specific_geometry()` thành hàm của input:
  - KC-03: slab panels đọc `detail_design.KC-03.slab_panels[]` (panel_id, thickness_mm, rebar, region) thay vì `h=120` + tọa độ cứng.
  - KC-04: rebar đọc `rebar_strips[].region/bars/spacing_mm/cover_mm` (vẽ đúng N thanh theo `bars`, vị trí theo `region`) thay vì index-based + hook cứng 120mm. Mặt TOP/BOTTOM giữ disjoint qua viewport freeze (KC-04).
  - KC-06: dầm đọc `detail_design.KC-06.beam` (mark, width/height, main_rebar, stirrup, grade, length); mặt cắt phóng `50/detail_scale`. Label tự sinh: `MC-BM-D1A (200x400) | 2D20+3D20+D8a150 | B25`.
  - KC-07: chi tiết thép đọc `detail_design.KC-07.steel_details[]` (plate spec parse, bolt_rows/bolt_cols, kind: BASEPLATE/CONCRETE_COLUMN/GUSSET_PLATE); hệ số phóng từ `detail_scale`.
  - `_sheet_missing_inputs()`: chặn thiếu `rebar_strips`/`region` (KC-04), `detail_design.KC-06.beam`, `detail_design.KC-07.steel_details`, `detail_design.KC-03.slab_panels` → `MISSING_INPUT`, không PASS.
- Preview: sheet 1-viewport render band BOM `[305..365]` khớp đúng paperspace (trung thành layout DXF).

### Fixture (test data — không dùng cho thi công)
- `g2_steel_and_sheet_fixture.json`: thêm block `detail_design` (KC-03/04/06/07) + các trường `region`, `bars`, `spacing_mm`, `cover_mm` cho `rebar_strips`.

### Tests mới (`.agents/tests/test_cad_v6_c2.py`)
- `test_08` (V2-01): 12 phần tử BOM mỗi phần tử đúng 3 handle paperspace; handle resolve thành TEXT thật trên `DCE_Schedule`, nằm trong khung A3 `[10..415]×[5..292]`; không phần tử nào nằm trong viewport; rebar strips (không có schedule_refs) không in BOM.
- `test_09` (V2-03): mutation (a) đổi beam input `250x500/4D24+D10a200/B30` ⇒ label+box đổi, không còn `200x400`; (b) đổi `bar_spec=d14a200` ⇒ label rebar đổi; (c) xóa `region`+`detail_design` ⇒ `MISSING_INPUT`, cả KC-04/06/07 nằm trong `missing_inputs`.

## 2. Bằng chứng trên đĩa (artifact `c2_remediated_v3`, thư mục mới — v2 giữ nguyên)

- **Validator độc lập 8 cổng** (`gemini/validate_a1_06_c2_remediated.py`): **PASS 8/8** — `gemini/a1_06_linkage_validation_v3.json` (sha manifest, sha sidecar ×5, handles resolve ×5, viewport nonoverlap, KC-04 disjoint freeze, strict 3-way ×5, compliance physical ×5, compliance plan ×5).
- **Re-measure độc lập**: BOM 36/36 paper rows resolve on-sheet không clip trên cả 5 DXF; KC-06 label khớp fixture; KC-04 có 4 thanh REBAR_TOP + 4 thanh REBAR_BOTTOM (từ `region/bars` fixture); PDF 5×A3; 5 PNG preview.
- **Test**: `test_cad_v6_c2.py` = **9/9 OK** (7 cũ + 2 mới); `test_dce_block_semantics.py` = **13/13 OK**.
- **Regression 7 suites**: xem log (chạy `unittest` — môi trường không có pytest).

## 3. Ràng buộc/limitation (khai báo trung thực)

- Fixture `g2_steel_and_sheet_fixture.json` là **dữ liệu thiết kế THỬ** (thực hư cấu hình), chỉ dùng để chứng minh semantic/3-way linkage — không phải hồ sơ thi công thật.
- Tỷ lệ phóng detail (`50/detail_scale`) và hệ toạ độ grid chi tiết (2×2) vẫn là quy ước bố cục của engine; phần *kích thước/thông số* đã chạy theo input. CODEX có thể kiểm mutation tiếp.
- Dynamic Block & DCE runtime block edit không nằm trong scope static C2 (giữ nguyên, chưa suy ra từ catalog/ATTRIB).

## 4. Bàn giao

- CODEX/GEMINI kiểm lại: chạy `validate_a1_06_c2_remediated.py --c2-dir .../c2_remediated_v3` + mutation tests theo spec V2-03.
- **Bus: giữ mở, KHÔNG tự close.** Chờ review đối tác trước khi `--complete`.
