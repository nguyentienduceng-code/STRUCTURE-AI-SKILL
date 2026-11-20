# HANDOFF BRIEF — ĐÁNH GIÁ KIẾN TRÚC & ĐỀ XUẤT TỐI ƯU HỆ THỐNG CAD (DCE PRO v6 + MCP)

> **Bàn giao:** `GEMINI` ➔ `CLAUDE` (Task Review Kiến trúc — mở session mới tiết kiệm token)  
> **Phạm vi đọc tiết kiệm token:** Chỉ đọc file này và kiểm tra các đoạn code/line range được trỏ bên dưới. **Không** quét các thư mục `memory/audits/` lịch sử trừ `A1_V2_RECHECK_REPORT.md` khi cần đối chiếu mục 4.

---

## 1. Trạng thái Hệ thống CAD Đã Hoàn thành & Kiểm chứng

1. **Chuẩn Layer SSOT Đa thiết bị (`cad_layer_standard.py`):**
   - Hợp nhất **86 layer** trong `.agents/_SHARED/data/dce_layers_standard.json` (`46` Form 2.dxf + `16` DCE STEEL từ `DbimSteelAutocad.DceLayerName` & `VN_LayerThepGc.txt` + `16` mặt bằng/khung + `8` compat aliases) với 2 profile `dce_native` và `light_bg_plot`.
   - Sinh template `.agents/_SHARED/data/DCE_Pro_And_Steel_Template.dxf` (`78` layers, `18` DimStyles `Dce_*MV`, `176` blocks, `ezdxf.audit()` = `0 errors / 0 fixes`).
   - Đã đấu nối vào `cad_plan_engine.py`, `cad_multiview_a3.py`, `dce_steel_adapter.py`, `dce_cad_compliance_checker.py`.
2. **Luồng Vẽ CAD-first & A3 Đa Khung nhìn (`CUSTOM_MULTIVIEW`):**
   - `cad_multiview_a3.py` dựng khung A3 ngang `42000×29700 mm`, 2 viewport `TOP`/`BOT`, khung tên dọc phải, `KEY PLAN`, bảng `GHI CHÚ`, bảng thống kê gọn; đã đấu nối vào `cad_plan_engine.export_dce_plan` và `mcp_dce_cad_server.render_cad_plan` (mặc định `export_pdf=False`).
   - Test thực chiến Cát Lái (`01_Projects/03_Sprint2_KetQua_NeChu_CAD/CatLai_KC13_KC15_CAD/KC-{13,14,15}.dxf`): cả 3 đạt `ezdxf.audit()` `0/0`, `validate_cad(profile="physical") == PASS`, `resolve_cad_collisions(dry_run=True)` `0/0`, `v6_status = OK_V6`, và đã qua soi ảnh 220 DPI.
3. **MCP Server (`mcp_dce_cad_server.py`) & Regression:**
   - Đủ 10 tools CAD-first; R-tree collision solver (`cad_collision_solver.py`); Virtual Drive Guard (`dce_virtual_drive_guard.py`).
   - Toàn bộ **13 suite CAD/MCP**: **`180 passed, 13 subtests passed`** (`0 failed, 0 skipped`).

---

## 2. Năm Điểm Nghẽn / Nợ Kỹ thuật Cần Claude Phản biện & Đề xuất

1. **Vênh giữa `profile="physical"` và `profile="full"` (20 cổng G8):**
   - `DcePlanEngine.save_v6()` ghi `.dce_audit.json` theo schema v6 (`v6_status`, `provenance`, `element_registry`), khác với schema V4 mà `DCECADComplianceCheckerV4._run_metadata_gates()` (`.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py`) yêu cầu (`scale`, `mode`, `entities_log`, `blocks_defined`, `dimstyles_defined`, `layers_defined`), dẫn tới `gate_status = NOT_RUN` trên `KC-13..15`.
   - `cad_multiview_a3.py` dùng `TEXT` thuần cho nhãn dầm/cột nên `blocks.member_tags = 0` và `has_setting_out_dims = False` trong `validate_cad`.
2. **Phân mảnh trong `cad_plan_engine.py` (~3,585 dòng) & `cad_sheet_set.py`:**
   - `cad_plan_engine.py` vẫn giữ song song nhánh legacy string-writer `DCEProCADPlanEngineV4` và `DcePlanEngine` (`ezdxf`).
   - `cad_sheet_set.py#L15-L42` (`REQUIRED_DCE_LAYERS`, `EXTRA_C2_LAYERS`) vẫn giữ màu riêng, chưa đọc từ `cad_layer_standard.py`; đồng thời còn tồn đọng các hạng mục V2-01..03 từ Codex (`.agents/memory/audits/cad_v6/codex/recheck_v2/A1_V2_RECHECK_REPORT.md`).
3. **Hardcode theo dự án Cát Lái trong `cad_multiview_a3.py`:**
   - Địa chỉ khung tên (`#L776-L777`, `#L792-L793`) và vùng né cầu thang (`if vp_id != "MT":` `#L393-L396`) cần tham số hóa 100% vào Model JSON.
4. **Preview Crop, Plot Style `.ctb` & DWG (`ODA`):**
   - `dce_render_preview.py` chế độ `_render_crop(..., view_box=...)` bỏ sót text của anonymous `*D` DIMENSION blocks (chỉ `qsave` toàn tờ mới hiện chữ dim).
   - Chưa đồng bộ file `.ctb` in ấn đi kèm `dce_layers_standard.json`, và `ODAFileConverter.exe` chưa có trên máy (`convert_to_dwg` trả `UNAVAILABLE`).
5. **Độ phủ Bộ Hồ sơ TKTC (`.agents/skills/Technical_Illustrator/STRUCTURAL_SHEET_SET_GUIDE.md`):**
   - Cần lộ trình gọn từ mặt bằng (đã chạy ổn) sang: mục lục tự động, móng/cọc, thép sàn `TOP`/`BOTTOM` dữ liệu thật, và chi tiết dầm/cột (`KC.32`) kèm kiểm chuẩn `G1–G6`.

---

## 3. Đầu ra Mong muốn từ Claude (Task Review & Upgrade Plan)

Claude vui lòng đọc nhanh các tệp trọng tâm trên và trả về **Báo cáo Nhận xét & Phương án Tối ưu / Nâng cấp** (không cần sửa code vội trừ khi được duyệt, ưu tiên giải pháp ít rủi ro gãy 180 tests):
1. **Kiến trúc hợp nhất v6 + Bộ lọc 8 (`G8.01–G8.20`):** Cách nâng cấp `validate_cad(profile="full")` hỗ trợ trực tiếp `.dce_audit.json` v6 + `ATTRIB` block mà không lệ thuộc nhánh V4 cũ.
2. **Kế hoạch Refactor `cad_plan_engine.py` & `cad_sheet_set.py`:** Tách module sạch, đồng bộ `cad_sheet_set.py` về `cad_layer_standard.py`, tham số hóa `cad_multiview_a3.py`.
3. **Xử lý Preview Crop (`*D` dims), CTB in ấn đa thiết bị & chiến lược DWG/ODA.**
4. **Lộ trình Sprint nâng cấp (P0 → P2)** theo độ ưu tiên chi phí/hiệu quả, giữ trọn `180/180` tests xanh.
