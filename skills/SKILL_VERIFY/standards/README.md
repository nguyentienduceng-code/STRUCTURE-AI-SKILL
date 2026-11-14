# SKILL_VERIFY — Thư mục Chuẩn Kiểm Toán (Standards)

> Nguồn sự thật cho các file chuẩn dùng làm đầu vào kiểm tra, tách riêng khỏi code Python
> để đúng nguyên tắc "chuẩn là dữ liệu, code là bộ thực thi".

## File

| File | Chuẩn | Nguồn gốc | Trạng thái |
|---|---|---|---|
| `DCE_Structural_BIM_Audit.ids` | buildingSMART IDS 1.0 (IFC4) — kiểm tra `LoadBearing = true` cho IFC4 COLUMN & WALL (Gate_BIM_01/02) | Import từ `D:\DCE_MCP_CAD_Revit_Starter_Kit_v5.0` (đã phân tích tại RFC `RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md` §6.2D) | **TÀI SẢN — CHƯA KÍCH HOẠT LOGIC.** Chỉ kích hoạt khi IFC toolchain (`ifcopenshell`/`ifctester`) được cài; hiện máy chưa có (RFC §6.1). |

## Ghi chú tích hợp (Giai đoạn 3 — Revit 2D→3D)

- Khi có IFC toolchain, thêm bộ lọc mới (Bộ lọc 9) vào `SKILL_VERIFY` gọi `ifctester --ids DCE_Structural_BIM_Audit.ids model.ifc`.
- File `.ids` này là **file bên ngoài import về** (không phải code của hệ sinh thái `.agents/`), nên KHÔNG tự động chạy; mọi kích hoạt phải qua RFC/đồng thuận.
- Không sửa nội dung file này mà không ghi rõ nguồn trong CHANGELOG (nguyên tắc traceability).
