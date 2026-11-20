# GEMINI G2 RESULT — Adapter Steel & Kiểm chuẩn Dữ liệu Xuyên tờ (`09_DCE_CAD_BLOCK_SEMANTICS_V6`)

> **Trạng thái G2:** HOÀN THÀNH & ĐÃ KIỂM CHỨNG ĐỘC LẬP
> **Tác tử thực hiện:** GEMINI (Antigravity)
> **Bước tiếp theo:** Bàn giao sang **CLAUDE Phase C2** (`cad_sheet_set.py`, tích hợp bộ sheet KC-01..KC-07 & dual-viewport A3 `TOP`/`BOTTOM`)
> **Ghi chú dữ liệu:** Toàn bộ fixture và file DXF kiểm chứng dùng **Test Fixture Data** (không dùng để thi công thực tế).

---

## 1. Steel Block Catalog & Semantic Bindings (`Form 2_Steel.dwg`)

1. **`dce_block_catalog.py`** ([dce_block_catalog.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Technical_Illustrator/cad_integration/dce_block_catalog.py)):
   - Bổ sung `DceBlockCatalog.load_steel_dwg_catalog()` đọc metadata từ `g:\My Drive\Google AI Studio\.agents\memory\audits\dce_round2_20261114\template_catalog.json` (`Form 2_Steel.dwg`, `reader_warning=76`, `dynamic_dictionary_keys=7`).
   - Gắn nhãn tin cậy trung thực **`PARTIAL_DWG_WASM_READ_76`** (không ghi đè block đã có `VERIFIED_DXF`) và tích hợp tự động vào `scan_default_suite()`.
   - Tổng số block sau mở rộng trong `g:\My Drive\Google AI Studio\.agents\memory\audits\cad_v6\gemini\dce_block_catalog.json`: **132 blocks** (gồm **34 Steel blocks**).
2. **`dce_block_binding.py`** ([dce_block_binding.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Technical_Illustrator/cad_integration/dce_block_binding.py)):
   - Đăng ký Semantic Bindings khớp đúng ATTDEF thật trong `Form 2_Steel.dwg`:
     - `Dce-ThepTam`, `Dce-Tangcung`: `plate_thickness -> B`, `quantity -> SL`, `member_mark -> TENCK`, `shape_desc -> HINHDANG`, `chamfer_desc -> VATCANH`.
     - `Dce_BP_Pin4`, `Dce_BP_Pin6`, `Dce_BP_Fix6`, `Dce_BP_Fix8`, `Dce_BP_Fix10`, `Dce_BP_Fix12`: `baseplate_mark -> TenBanDe`, `thickness_mm -> ChieuDay`.
     - `Dce_AnchorExpansion`: `bolt_count -> SL`.
     - `Dce_PlanI`: `column_mark -> TENCOT`.
   - Áp dụng **Zero White Text Lock (Rule 12b)**: mọi `ATTRIB` ép `true_color=0x1E3246`, tránh màu trắng `ACI 7` / `#FFFFFF`.

---

## 2. Steel Adapter 1:1 mm DXF, Ma trận Năng lực & Khóa Tỷ lệ Đồng nhất

**Module:** [dce_steel_adapter.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Technical_Illustrator/cad_integration/dce_steel_adapter.py)

### 2.1 Mở rộng Hình học & Tiện ích
- Bổ sung `STEEL_CHANNEL_PROFILES` (`U100`..`U200`, `C150`), `STEEL_PIPE_PROFILES` (`D114`..`D323`), `STEEL_BASEPLATE_PRESETS` (`Pin4/6`, `Fix6/8/10/12`).
- Bổ sung `get_channel_profile_polygon()`, `get_pipe_profile_circles()`, `validate_uniform_block_scale(xscale, yscale)` (cấm tuyệt đối méo tỷ lệ X/Y; sai khác `|xscale - yscale| > 1e-6` raise `ValueError: UNIFORM_SCALE_VIOLATION`).
- Bổ sung `render_steel_components_to_dxf()` và `verify_steel_dxf_roundtrip()` kiểm chứng save/reopen 1:1 mm bằng `ezdxf`.

### 2.2 Ma trận Năng lực Thực tế (Headless Python + ezdxf vs AutoCAD Dynamic/XData)

| Yêu cầu đầu vào | Trạng thái (`capability_status`) | Hành vi thực tế trong G2 |
| --- | --- | --- |
| Vẽ mặt cắt `I` / `H` / `BOX` / `CHANNEL` / `PIPE`, bản đế `Dce_BP_*`, thép tấm `Dce-ThepTam` (`STATIC_2D`) | `STATIC_2D_ACCURATE` | Kết xuất hình học vector `LWPOLYLINE`/`CIRCLE` 1:1 mm, chèn block với `xscale == yscale == 1.0`, bind `ATTRIB` tối màu. |
| Yêu cầu đánh giá hành động Dynamic Block (`requested_mode="DYNAMIC"`) | `UNSUPPORTED_BLOCK_BEHAVIOR` | **Từ chối giả lập PASS**. Ghi log cảnh báo `UNSUPPORTED_BLOCK_BEHAVIOR` do thiếu ObjectARX/`AcDbEvalGraph`, fallback sang hình học tĩnh `STATIC_2D_ACCURATE` (0 anonymous `*U` block refs). |
| Yêu cầu ghi XData thương mại (`write_commercial_xdata=True`) | `UNSUPPORTED_COMMERCIAL_XDATA_DISABLED` | Chặn không ghi `DceSteelRebar` / `SYS_XData_App` vào DXF (`commercial_xdata_written=false`, `commercial_xdata_count=0`), ghi cảnh báo rõ ràng. |

---

## 3. Kiểm chuẩn Ngữ nghĩa Xuyên tờ & Tách lớp Thép sàn (`cad_element_registry.py`)

**Module:** [cad_element_registry.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Technical_Illustrator/cad_integration/cad_element_registry.py)

1. **`CadElementRegistry.validate_sheet_set_semantics(sheet_manifest, rebar_strips)`** kiểm tra 5 cổng độc lập:
   - `floor_and_column_continuity`: Phát hiện cột đã `STOPPED`/`TERMINATED` ở tầng dưới nhưng xuất hiện `CONTINUOUS`/`ACTIVE`/`TYPICAL` ở tầng cao hơn; phát hiện trùng `mark` lệch tiết diện cùng tầng hoặc tầng chưa khai báo.
   - `design_group_consistency`: Kiểm tra mọi phần tử cùng `design_group_id` phải đồng nhất `category` và `section_profile`.
   - `detail_target_resolution`: Xác minh `detail_ref.target_exists == True` và `sheet_number` / `drawing_id` khớp `detail_targets` hoặc `viewports` trong `sheet_manifest`.
   - `linkage_completeness`: Kiểm tra liên kết 3 chiều đầy đủ `geometry_refs` + `tag_refs` + `schedule_refs` cho từng cấu kiện kết cấu.
   - `rebar_top_bottom_separation`: Đảm bảo mọi dải thép có `face in ("TOP", "BOTTOM")`, không trùng ID chéo mặt, và viewport có `content_face="TOP"` / `"BOTTOM"` không bị trộn lẫn dải thép mặt đối diện.
2. **`filter_rebar_strips_by_face(rebar_strips, face, floor_id=None)`**: Hàm lọc chuẩn tách biệt tuyệt đối `"TOP"` và `"BOTTOM"` phục vụ layout viewport kép A3 của Phase C2.

---

## 4. Kết quả Kiểm chứng Artifact & Toàn bộ Regression Test Suites

### 4.1 Kết quả Round-trip DXF G2
- **Fixture:** `g:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration\fixtures\g2_steel_and_sheet_fixture.json` (Test Fixture Data)
- **DXF xuất ra:** `g:\My Drive\Google AI Studio\.agents\memory\audits\cad_v6\gemini\g2_steel_verification.dxf`
- **Audit log:** `g:\My Drive\Google AI Studio\.agents\memory\audits\cad_v6\gemini\g2_steel_verification_audit.json`
- **Số liệu kiểm chứng đọc lại từ file DXF:**
  - `sections_count = 5`, `baseplates_count = 2`, `plates_count = 1`.
  - `uniform_scale_ok = true`, `scale_violations = []`, `dynamic_block_refs_count = 0`, `commercial_xdata_count = 0`.
  - `geometry_checks = 7/7 matched`: `SC1` (300×300), `SB1` (175×350), `SBX1` (200×200), `SU1` (64×160), `SP1` (219×219), `BD-01` (400×400), `BD-02` (560×420).
  - `extracted_blocks = 6/6 matched`: `Dce_PlanI` (`TENCOT=SC1`), `Dce_BP_Pin4` (`TenBanDe=BD-01`, `ChieuDay=20`), `Dce_AnchorExpansion` (`SL=4`), `Dce_BP_Fix8` (`TenBanDe=BD-02`, `ChieuDay=28`), `Dce_AnchorExpansion` (`SL=8`), `Dce-ThepTam` (`B=14`, `SL=4`, `TENCK=GUSSET-01`, `HINHDANG=TRAPEZOID`, `VATCANH=V45-10`).
  - `capability_warnings`: `['UNSUPPORTED_BLOCK_BEHAVIOR', 'UNSUPPORTED_COMMERCIAL_XDATA_DISABLED']`.
  - `semantic_audit`: `is_valid = true`, `total_elements = 12`, `rebar_top_count = 2`, `rebar_bottom_count = 2`, cả 5 checks `= true`, `violations = {}`.

### 4.2 Kết quả Chạy Test Suite (sau chỉnh sửa cuối cùng)
- `python "g:\My Drive\Google AI Studio\.agents\tests\test_dce_block_semantics.py"`: **Ran 10 tests in 3.069s — OK** (7 tests G1 + 3 tests mới G2: `test_g2_steel_catalog_and_block_bindings`, `test_g2_steel_dxf_save_reopen_no_xy_scale_and_capability`, `test_g2_cross_sheet_semantic_and_registry_validation`).
- `python "g:\My Drive\Google AI Studio\.agents\tests\test_cad_v6_c1.py"`: **Ran 6 tests in 3.331s — OK**.
- `python "g:\My Drive\Google AI Studio\.agents\tests\run_all_tests.py"`: **32/32 suites PASS (Tổng thời gian: 144.78s)**.

---

## 5. Hợp đồng Giao diện Bàn giao sang CLAUDE Phase C2

CLAUDE kế thừa nguyên vẹn các API và dữ liệu đã khóa chuẩn dưới đây để triển khai `cad_sheet_set.py` và hoàn thiện bộ hồ sơ `KC-01`..`KC-07`:

1. **Gọi kiểm chuẩn xuyên tờ trước khi xuất PaperSpace/Viewports:**
   - `registry.validate_sheet_set_semantics(sheet_manifest=..., rebar_strips=...)` -> phải đạt `is_valid == True` trước khi xuất bộ tờ chính thức (hoặc gắn cờ `checks` vào JSON chẩn đoán).
2. **Tách lớp thép sàn trên Viewport kép (A3 Landscape `KC-04`):**
   - Dùng `filter_rebar_strips_by_face(rebar_strips, face="BOTTOM", floor_id=...)` cho viewport lớp dưới và `filter_rebar_strips_by_face(rebar_strips, face="TOP", floor_id=...)` cho viewport lớp trên, đảm bảo `content_face` khớp tuyệt đối.
3. **Fixture tham chiếu chuẩn cho C2:**
   - Sử dụng `g:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration\fixtures\g2_steel_and_sheet_fixture.json` (chứa sẵn `sheet_set_preview_manifest` cho `KC-02`, `KC-03`, `KC-04` dual viewport TOP/BOTTOM, `KC-06`, `KC-07`, danh sách `concrete_elements`, `steel_sections`, `baseplates`, `steel_plates`, và `rebar_strips`) kết hợp `c1_sample_model.json`.
4. **Ràng buộc sở hữu file:**
   - GEMINI không chỉnh sửa bất kỳ file nào thuộc quyền sở hữu của CLAUDE (`cad_plan_engine.py`, `cad_tag_placement.py`, `cad_sheet_set.py`, `test_cad_v6_c1.py`).

---

*Tài liệu do trợ lý AI lập tự động. Kết quả kiểm chứng và cấu hình fixture mang tính tham khảo kỹ thuật phần mềm, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
