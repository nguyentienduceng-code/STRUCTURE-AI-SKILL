---
name: Technical_Illustrator
version: 1.7.0
last_updated: 2026-11-15
description: "Kỹ sư Minh họa Kỹ thuật & Tiến độ PMO AI chuyên sinh bản vẽ mặt cắt 2D chính xác (Python), Biểu đồ Tiến độ chuẩn Microsoft Project (ms_project_gantt.py 300 DPI Split View 8 cột + CPM + Landscape Word Section Break) và ảnh mô phỏng 3D (AI Render). Kích hoạt khi nhắc đến: vẽ minh họa, vẽ mặt cắt, vẽ chi tiết thép, vẽ biểu đồ tiến độ, sơ đồ Gantt, timeline dự án, sơ đồ biện pháp thi công."
---
# Technical Illustrator — SKILL Entry Point (v1.7.0)

## Tổng quan

### Lập bộ bản vẽ kết cấu nhiều tờ

Khi yêu cầu là **bộ hồ sơ kết cấu** thay vì một mặt bằng đơn, đọc [quy trình lập bộ tờ](STRUCTURAL_SHEET_SET_GUIDE.md) trước khi xuất CAD. Lập `SheetSetManifest`, đối chiếu coverage theo phạm vi dự án, kiểm liên kết giữa mặt bằng và chi tiết, rồi mới chọn khổ/tỷ lệ/view. Ba tờ CAD v5.0 hiện tại là sản phẩm mặt bằng mẫu; không suy ra đã có đủ móng, thép sàn và chi tiết cấu kiện. `DUAL_VERTICAL_VIEWPORT` trong fitter mới là quyết định bố cục; phải kiểm DXF/PDF có **hai view thực**. `TOP`/`BOTTOM` trong dữ liệu thép chưa chứng minh đã xuất hai view lọc riêng.

### CAD MCP và điều kiện nghiệm thu

Trước khi tạo nhãn dầm/sàn, ký hiệu cấu kiện hoặc chi tiết Steel, đọc [hướng dẫn block và tag DCE](DCE_BLOCK_TAG_GUIDE.md). Tra block nguồn và ATTDEF trước khi dựng ký hiệu mới; ánh xạ dữ liệu thiết kế vào tag thực, kiểm lại sau save/reopen. Không gán cứng scale, chiều dày hay cao độ; không tự đổi lỗi INSERT thành TEXT mà bỏ qua cảnh báo. Phân biệt block nhãn, block hình học và block thống kê; hỗ trợ import ATTRIB không đồng nghĩa hỗ trợ Dynamic Block hoặc khả năng sửa bằng DCE.

Dùng 10 tools trong `mcp_dce_cad_server.py` ([cấu hình MCP](../../tools/mcp_config.json) và [hợp đồng MCP CAD](../../docs/MCP_DCE_CAD_CONTRACT.md)):
`render_cad_plan` (v6=True mặc định), `auto_layout_and_scale_plan`, `export_cad_sheet_set` (mặc định **CAD-first**: chỉ xuất DXF + sidecar + registry, **KHÔNG tự động xuất PDF/PNG** trừ khi ghi chú `export_pdf=True` / `render_preview=True`), `render_preview`, `consume_preview`, `release_preview`, `validate_cad`, `edit_entity`, `resolve_cad_collisions`, `convert_to_dwg`.
`render_cad_plan`, `export_cad_sheet_set` và `resolve_cad_collisions` trả đường dẫn DXF local thực tế;
không suy ra đường dẫn output từ tham số gợi ý. `pdf_path` trên `render_cad_plan` là PDF đầu vào đọc
vector kiến trúc, không phải nơi xuất PDF. `dry_run` của generator dùng cùng
đầu vào như lần ghi nhưng không lưu DXF.

Gọi `validate_cad` sau thay đổi. Mặc định `profile=full` yêu cầu đủ bằng chứng.
DXF từ `DcePlanEngine` kế thừa seed có thể đạt physical nhưng thiếu metadata
để nghiệm thu full. Không đổi NEEDS_REVIEW thành PASS. Dùng `profile=physical`
chỉ khi phạm vi được xác định là kiểm tra DXF vật lý và ghi rõ giới hạn đó.
Generator V4 xuất sidecar gắn SHA256; sidecar cũ không chứng minh DXF đã sửa.
Nhánh V4.7.1 cần ezdxf và xuất DIMENSION/ATTRIB/HATCH native, kiểm tra lại
sau save. Metadata không được dùng thay cho sự hiện diện của entity CAD thật.

Vòng Vision: render_preview → consume_preview; nếu đọc file trực tiếp thì
release_preview. Khi sửa entity, truyền revision nhận từ inspect. Thiếu revision
hoặc revision cũ không được phép commit. Giữ lớp tùy chỉnh nhãn của kỹ sư.
Layer DCE_Leader được solver quản lý và chuẩn hóa về màu 250 khi commit.

> **Nhắc nhở chống sai luồng (Bài học 2026-11-15):**
> 1. **Single Canonical Pipeline:** Mọi bản vẽ mặt bằng thật đi qua `DcePlanEngine` (`v6=True`) + `DCE_Master_Seed_Template.dxf` (chi tiết tại `cad_integration/README.md`). Cấm tự viết hàm vẽ khung/layer song song.
> 2. **CAD-first (Không mặc định PDF):** Mặc định chỉ xuất `.dxf` + metadata; chỉ bật `export_pdf=True` khi người dùng ghi chú yêu cầu PDF.
> 3. **Real-Model + Visual Gate:** Không đánh giá đạt chỉ qua fixture test nhỏ; luôn kiểm 1 ca công trình thật và soi ảnh `render_preview` (chống tràn chữ/lệch khung) trước khi bàn giao hoặc kết luận hoàn thành.

### Chỉnh sửa CAD theo phiên (DXF, bản nháp)

Dùng `../../tools/cad_edit_workbench.py` cho vòng lặp đọc/chọn handle → sửa vị trí
TEXT/MTEXT hoặc dimension thẳng → đọc lại kiểm chứng → xem SVG → sửa tiếp/hoàn tác.
Hướng dẫn và giới hạn: `../../tools/CAD_EDIT_WORKBENCH.md`. Đây là backend chỉnh sửa
DXF trên bản sao; chưa hỗ trợ sửa DWG trực tiếp hoặc chọn đối tượng bằng giao diện.

**Technical_Illustrator** là Trợ lý AI chuyên **trực quan hóa kỹ thuật & quản trị dự án** bằng hệ thống script Python chuẩn xác (MODE 2D — Mặc định) và mô phỏng phối cảnh (MODE 3D).

> **Nguồn sự thật duy nhất về thư viện script:** `scripts/registry.json` (registry v2.2.0 — 12 Active Parametric Scripts).
> Tra cứu nhanh tình huống → script: xem `scripts/REGISTRY_INDEX.md`.

## ⚡ Image Output Guarantee & Zero White Text Lock (Quy tắc TUYỆT ĐỐI)

1. Xác định đường dẫn output **TUYỆT ĐỐI** trước khi vẽ.
2. Tạo ảnh bằng script Python tham số hóa (`300 DPI`).
3. **Xác nhận** file ảnh tồn tại trước khi nhúng vào báo cáo.
4. **ZERO WHITE TEXT LOCK (Điều 12b AGENTS.md)**: Tuyệt đối không dùng chữ màu trắng trên nền tối trong bảng biểu hoặc nhãn biểu đồ để bảo vệ chất lượng in ấn đen trắng.

## Phân luồng Nhiệm vụ (Dispatcher Logic)

### → MODE 2D (2D Technical Drawing & PMO Gantt Chart) — MẶC ĐỊNH
- **Công cụ**: Script Python (`matplotlib`) chạy nội bộ, xuất ảnh `300 DPI`.
- **Thư viện 12 Scripts Tham Số Hóa Đang Hoạt Động**:

| Script | Loại | Input chính | Output |
|---|---|---|---|
| `ms_project_gantt.py` | **Tiến độ PMO** | `--input-json --output --docx-out --title` | **Biểu đồ Tiến độ chuẩn MS Project (Split View 8 cột WBS + Gantt CPM 300 DPI + Landscape DOCX)** |
| `draw_2d_section.py` | Mặt cắt | `--h --b --tw --tf` | Dầm thép chữ I |
| `draw_bolt_connection.py` | Chi tiết | `--bolt_d --bolt_grade --n_rows --n_cols` | Liên kết bu lông |
| `draw_rc_column.py` | Mặt cắt | `--type rect\|circular --width --depth --main_dia` | Cột BTCT |
| `draw_foundation.py` | Mặt cắt | `--type single\|strip --L --B --H` | Móng đơn/băng |
| `draw_slab_rebar.py` | Bố trí | `--Lx --Ly --slab_t` | Sàn BTCT |
| `draw_comparison_chart.py` | Biểu đồ | `--json` | Radar + Bar chart |
| `draw_rc_beam_full.py` | Bố trí | `--type --b --h --main_dia --stirrup_dia` | Dầm BTCT đầy đủ |
| `draw_rc_wall.py` | Bố trí | `--type --t --rebar_dia --spacing` | Tường chắn BTCT |
| `draw_pile_cap.py` | Mặt cắt | `--type --L --B --H --pile_d --n_piles` | Đài cọc |
| `draw_weld_detail.py` | Chi tiết | `--type --plate_t --weld_type` | Chi tiết hàn |
| `draw_moment_diagram.py` | Biểu đồ | `--input --output` | Biểu đồ nội lực M, V, N |
| `cad_plan_engine.py` | **Mặt bằng CAD** | `cad_integration/cad_plan_engine.py` | **Bản vẽ CAD Mặt bằng Định vị Cột Vách chuẩn DCE Pro A1 (7 Gap) & KC-03 v6** |

- **Hạ tầng Kiến trúc CAD DCE v6 (`cad_integration/`)**:

| Module | Vai trò | API / Đầu ra chính |
|---|---|---|
| `dce_block_catalog.py` | Danh mục Block & ATTDEF + SHA-256 | `DceBlockCatalog`, `load_steel_dwg_catalog()` (`132` blocks, `34` Steel `PARTIAL_DWG_WASM_READ_76`) |
| `dce_block_binding.py` | Ánh xạ & Ràng buộc Semantic ATTRIB | `bind_block_attributes()`, `extract_semantic_values()` (chữ tối `0x1E3246`, chống chữ trắng Rule 12b) |
| `cad_element_registry.py` | Danh tính Cấu kiện Bất biến & Kiểm chuẩn Xuyên tờ | `CadElementRegistry`, `validate_sheet_set_semantics()` (5 cổng), `filter_rebar_strips_by_face()` |
| `dce_steel_adapter.py` | Adapter Kết cấu Thép 1:1 mm | `render_steel_components_to_dxf()`, `verify_steel_dxf_roundtrip()`, `validate_uniform_block_scale()`, ma trận `STATIC_2D_ACCURATE` vs `UNSUPPORTED_BLOCK_BEHAVIOR` |
| `cad_tag_placement.py` | Lập lịch Đặt Nhãn & Chống Đè | `TagPlacementPlanner` (giữ manual override `element_id`/`view_id`, tự bật `leader` khi vướng lỗ/vật cản) |
| `cad_sheet_set.py` | Bộ Tờ A3 & Viewport Kép TOP/BOTTOM | `SheetSetManifest`, `export_sheet_set()` (kiểm 5 cổng trước xuất, PaperSpace `VP_TOP`/`VP_BOTTOM` tách lớp) |

## Hướng dẫn Gọi Engine Biểu đồ Tiến độ Chuẩn Microsoft Project (`scripts/ms_project_gantt.py`)

Khi người dùng hoặc các Skill (`Project_Manager`, `SKILL_PHULUC`, `Design_Evaluation`) yêu cầu vẽ biểu đồ tiến độ dự án (Master Schedule / Timeline / Gantt Chart), **tuyệt đối cấm vẽ horizontal bar chart đơn giản**. Bắt buộc gọi `scripts/ms_project_gantt.py` (v1.1.0) với đủ 8 đặc tính chuẩn Microsoft Project:
```bash
python ".agents/skills/Technical_Illustrator/scripts/ms_project_gantt.py" \
  --demo yen_quang \
  --output "MS_Project_Schedule_300DPI.png" \
  --docx-out "Bao_Cao_Tien_Do_Landscape.docx"
```
- Khi nhúng vào báo cáo Word (`.docx`), gọi hàm `embed_gantt_in_docx_landscape(doc, image_path)` để tự động ngắt `Section Break` sang **01 trang A4 Xoay Ngang (Landscape `29.7 x 21.0 cm`)** nhúng ảnh 300 DPI sắc nét, sau đó tự động trả về khổ **A4 Dọc (Portrait `21.0 x 29.7 cm`)**.

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **1.7.0** | **2026-11-15** | Đối chiếu block/ATTRIB thực trong KC-03 và Form 2; bổ sung định danh dầm/sàn, catalog/binding, bố trí tag, tích hợp Steel và điều kiện kiểm thử. |
| **1.6.0** | **2026-11-15** | Bổ sung quy trình bộ tờ kết cấu, ma trận coverage, đối chiếu PDF Cát Lái với 3 DXF v5.0, hợp đồng dữ liệu viewport/thép sàn và cổng nghiệm thu xuyên tờ. |
| **1.5.0** | **2026-11-14** | Đồng bộ 8 MCP tools, output local, revision bắt buộc và phạm vi nghiệm thu physical/plan/full. |
| **1.4.0** | **2026-11-03** | Tích hợp chính thức Engine Biểu đồ Tiến độ chuẩn Microsoft Project (`scripts/ms_project_gantt.py` v1.1.0) với 8 đặc tính PMO và cơ chế nhúng tự động trang A4 Landscape 300 DPI vào Word (`.docx`). |
| 1.3.0 | 2026-09-27 | Đồng bộ `registry.json` v2.1.0 và hướng dẫn MODE 2D/3D. |
