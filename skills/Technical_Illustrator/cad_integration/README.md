# CAD Integration — Single Canonical Structural Drawing Pipeline (DCE Pro v6)

Tài liệu kiến trúc chuẩn cho hệ thống xuất bản vẽ kết cấu tự động (`ezdxf` + `DCE_Master_Seed_Template.dxf` + Render kiểm tra PNG/PDF).

---

## 1. Luồng Sản xuất Chuẩn Duy nhất (Single Canonical Pipeline)

Mọi bản vẽ kết cấu thật (nhà cao tầng, nhà phố nhiều tờ) **BẮT BUỘC** đi qua một lõi duy nhất, không vẽ tay rời rạc bằng các hình hộp giả lập:

```text
Structural Model JSON / build_structural_model()
        │
        ├──► cad_element_registry.CadElementRegistry (Element ID bất biến)
        ├──► sheet_scale_fitter.SheetScaleSolver (Chọn khổ A2/A1/A0 & TCVN 1:S)
        ▼
cad_plan_engine.export_dce_plan(..., v6=True)  [DcePlanEngine + DCE_Master_Seed_Template.dxf]
        │  ├── dce_block_binding.py / dce_block_catalog.py  (Binding thuộc tính & catalog block)
        │  ├── cad_tag_placement.py / cad_collision_solver.py (Né chữ hình học + chống đè)
        │  └── dce_steel_adapter.py                         (Cấu kiện thép I/H/Box/Pipe/Bản mã)
        ▼
Output DXF + .dce_audit.json sidecar (OK_V6)
        │
        ├──► Single-sheet MCP CAD: tools/mcp_dce_cad_server.py -> render_cad_plan(v6=True) / auto_layout_and_scale_plan()
        └──► Multi-sheet CAD Set: cad_sheet_set.export_project_a3_sheets() / MCP export_cad_sheet_set()
                   └── KC-02_DinhViCotVach.dxf + KC-03_KetCauDamSan.dxf + project_element_registry.json
                   └── (PNG / PDF A3 chi xuat khi ghi ro render_previews=True / export_pdf=True)
```

---

## 2. Phân tầng Module & Chức năng Đang Giữ lại

### A. Production Plan Engine (Lõi Xuất Mặt bằng Kết cấu)
| File | Vai trò chính | Ghi chú |
|------|---------------|---------|
| `cad_plan_engine.py` | `DcePlanEngine`, `export_dce_plan()`, `build_structural_model()` | Sử dụng `templates/DCE_Master_Seed_Template.dxf`, tự wrap ghi chú & fit chữ bảng thống kê không tràn khung |
| `templates/DCE_Master_Seed_Template.dxf` | Template gốc chuẩn DCE Pro (layer, DimStyle `Dce_*MV`, block cột/trục/cao độ) | Nguồn block chuẩn duy nhất |
| `dce_steel_adapter.py` | Vẽ cấu kiện thép tổ hợp (`I/H/Box/Pipe`, bản mã `BD-01/02`, sườn gia cường) | Phục vụ công trình thép / nhà xưởng / kết hợp |

### B. Semantic, Tagging & Anti-Collision (Các Nâng cấp Giá trị Từ v4.7 – v6)
| File | Vai trò chính |
|------|---------------|
| `cad_element_registry.py` | `CadElementRegistry` + `StructuralElement` — định danh `element_id` bất biến, audit liên kết hình học/tag/bảng thống kê/cross-sheet |
| `dce_block_catalog.py` & `dce_block_binding.py` | Chuẩn hóa ngữ nghĩa & binding thuộc tính vào block `INSERT`/`ATTRIB` (`DCE_BLOCK_TAG_GUIDE.md`) |
| `cad_tag_placement.py` | Đặt nhãn né vùng trống theo hình học cấu kiện & hỗ trợ `tag_overrides` |
| `cad_sheet_set.py` | `export_project_a3_sheets()` xuất bộ DXF công trình thật + registry (mặc định **không xuất PDF** khi không ghi chú `export_pdf=True`); `export_sheet_set()` dùng cho Paperspace `Layout1` + tách lớp `REBAR_BOTTOM` / `REBAR_TOP` |
| `cad_paperspace_builder.py` | **P3 Multi-Layout PaperSpace & 4-Form Open Runner**: `export_single_file_multilayout_dxf()` (1 file DXF chung ModelSpace + nhiều Layout PaperSpace A3/A1) và `export_with_open_form()` (chạy open-mode cho đủ 4 Form `FORM_01`..`FORM_04`) |
| `cad_form_contract.py` & `cad_block_adapters.py` | Khai báo contract vùng (`ZONE_*`) cho 4 Form mở (`FORM_01`..`FORM_04`), vùng sở hữu `DCE_AGENT_OWNED`, block native `DCE_COL_*`, `DCE_Pile_*`, `Dce_KhTenTruc`, `DCE_TITLEBLOCK_*` |
| `cad_vector_renderer.py` | Render 300 DPI không phụ thuộc AutoCAD (đọc `.dce_audit.json` / inline audit) |

### C. Shared CAD Tools (`.agents/tools/`)
| File | Vai trò chính |
|------|---------------|
| `cad_collision_solver.py` & `cad_scene_index.py` | Giải quyết va chạm chữ/dim bằng R-tree không gian (`Sprint 2`) |
| `sheet_scale_fitter.py` | `SheetScaleSolver` — tính Fill Ratio 65–85% & tự nâng khổ A2 → A1 → A0 |
| `dce_render_preview.py` | `render_dxf_to_png()` — render DXF sang PNG an toàn trong local scratch (Virtual Drive Guard) |
| `mcp_dce_cad_server.py` | MCP Server `dce-cad` (13 tools CAD-first: `render_cad_plan`, `auto_layout_and_scale_plan`, `export_cad_sheet_set`, `render_preview`, `consume_preview`, `release_preview`, `validate_cad`, `edit_entity`, `resolve_cad_collisions`, `convert_to_dwg`, `open_form`, `diff_form`, `apply_agent_changes`) |
| `dce_rules_registry.py` | Nguồn quy chuẩn kiểm toán CAD (Bộ lọc 8 `test_dce_cad_compliance.py`) |

### D. Tiện ích Mặt cắt Đơn lẻ & Di sản / Fixture Kiểm thử
| Thành phần | Trạng thái | Mục đích |
|------------|------------|----------|
| `calc_to_dxf.py`, `dce_dxf_generator.py`, `analyze_dxf.py` | Utility (v1) | Sinh nhanh mặt cắt dầm BTCT/Thép đơn lẻ (`RCCalculatorToDXF`, `SteelCalculatorToDXF`) và đọc thông số DXF |
| `DCEProCADPlanEngineV4` (trong `cad_plan_engine.py`) | **Legacy** | Chỉ giữ tương thích ngược cho `build_sample_40_story_tower_plan(..., mode="COLUMN_WALL_SETOUT")`; bản vẽ mới dùng `DcePlanEngine` |
| `fixtures/c1_sample_model.json`, `fixtures/g2_steel_and_sheet_fixture.json` | **Test Fixture** | Chỉ dùng để chạy unit test `test_cad_v6_c1.py`, `test_cad_v6_c2.py`, không dùng cho hồ sơ dự án |

---

## 3. Ví dụ Sử dụng Nhanh

### Xuất bộ bản vẽ CAD công trình thật (mặc định CHỈ xuất DXF + Registry, không tự xuất PDF)

```python
from pathlib import Path
from cad_sheet_set import export_project_a3_sheets

# Mặc định: xuất DXF + .dce_audit.json + registry (không xuất PDF/PNG)
res = export_project_a3_sheets(
    output_dir=Path(r"G:\My Drive\Google AI Studio\01_Projects\DuAnX\CAD"),
    model_json_path=None,  # Hoặc đường dẫn JSON mô hình công trình
)
print(res["status"], [s["dxf_filename"] for s in res["sheets"]], res["registry_total_elements"])

# Chỉ truyền export_pdf=True khi người dùng ghi chú cần xuất PDF A3 Landscape (420x297 mm)
```

### Sinh mặt cắt đơn lẻ từ kết quả tính toán (`calc_to_dxf.py`)

```python
import sys
sys.path.insert(0, '../Structural_Design_Engineer/scripts')
sys.path.insert(0, '.')

from calc_rc_section import calc_rc_beam
from calc_to_dxf import RCCalculatorToDXF

rc_d1 = calc_rc_beam(
    b=300, h=600, a=40,
    concrete="B25", rebar="CB400-V",
    M_ed=250, V_ed=120,
    stirrup_dia=8, stirrup_legs=2, stirrup_spacing=150
)
RCCalculatorToDXF(rc_d1).generate("G:/My Drive/Google AI Studio/output/DA01_MC-D1_01.dxf")
```

---

## 4. DCE PRO LAYERS & LỆNH THAM KHẢO

| Layer | Color | Mô tả |
|-------|-------|-------|
| `DCE_BaoBeTong` | 4 | Bê tông |
| `DCE_ThepChu` | 1 | Thép chủ |
| `DCE_ThepDai` | 220 | Thép đai |
| `DCE_Dim` | 254 | Kích thước |
| `Dce_text` | 7 | Text |
| `DCE_Truc` | 8 | Đường trục |
| `DCE_Block` | 8 | Block |

```autolisp
; Trong AutoCAD:
vd                   ; Ve dam
ShopDrawingBeam      ; Shop drawing dam
vc                   ; Ve cot
ImportKichThuocCot   ; Import kich thuoc cot
tkt_dce              ; Thong ke thep
```

---

---

## 5. Thư viện 4 Bộ Form Tùy Biến Mở & Block Adapters (`template_mode="open"`)

| Tệp / Thư mục | Vai trò |
| :--- | :--- |
| `00_Template_&_Standards/CAD_Forms/` | 4 Form DXF + manifest cho kỹ sư mở AutoCAD chỉnh sửa (`Form_01`..`Form_04`) |
| `.agents/_SHARED/data/CAD_Forms/` | Bộ gốc SSOT fallback khi dự án chưa ghi đè |
| `cad_form_contract.py` | 3-tier resolver (`project > user > ssot`), validator read-only (`E002`, `E003`, `W003`), manifest refresher |
| `cad_block_adapters.py` | `DCE_TITLEBLOCK_A1/A3` `ATTDEF` update tại chỗ, `DCE_Pile_*`, `DCE_COL_*`, `Dce_KhTenTruc`, XData `DCE_AGENT_OWNED` |
| `cad_form_generator.py` | Sinh đồng bộ bộ 4 Form + `README_HUONG_DAN_SUA_FORM_AUTOCAD.md` |

*Cập nhật lần cuối: 2026-11-16 — Added Open 4-Form Editable Library (`template_mode="open"`) & DCE Native Block Adapters.*
