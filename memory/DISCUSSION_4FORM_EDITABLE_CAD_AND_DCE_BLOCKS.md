# THẢO LUẬN KIẾN TRÚC CAD: THƯ VIỆN 4 BỘ FORM TÙY BIẾN MỞ & TÁI SỬ DỤNG HỆ BLOCK MẪU DCE

> **Ngày:** 2026-11-16  
> **Khởi tạo bởi:** GEMINI (theo yêu cầu trực tiếp của User)  
> **Mời phản biện & đồng thiết kế:** CLAUDE (`SKILL_DUAL_AGENT_BRIDGE`)  
> **Tính chất ca:** Thảo luận kiến trúc & chốt spec trước khi code (KHÔNG tự ý refactor lớn khi chưa thống nhất với User & Gemini).

---

## 1. BÀI TOÁN USER ĐẶT RA

1. **Thư viện 4 bộ Form mẫu có thể mở trực tiếp bằng AutoCAD để kỹ sư tự sửa:**
   - User muốn có hệ thống mẫu tương tự tư duy các bộ `Form 1`..`Form 5` (+ `_Steel`) của DCE Pro nhưng **mở & dễ tùy biến hơn**: mở file `.dxf` trực tiếp trong AutoCAD -> sửa Khung tên, Logo, Màu Layer, DimStyle, Font chữ, bố cục khung nhìn, ghi chú chuẩn công ty -> lưu lại (`Ctrl+S`), và từ đó mọi thiết bị đồng bộ Google Drive đều xuất CAD theo đúng mẫu vừa sửa mà **không phải sửa code Python**.
2. **Nghiên cứu tái sử dụng tối đa bộ Block mẫu DCE (kèm mở rộng cho Block thiếu):**
   - Tận dụng các Block thực sự có trong kho DCE (`Block trục`, `Block cột`, `Block dầm`, `Block bảng thống kê thép TK*`, `Block cao trình`, `Block nhãn`) và bổ sung chuẩn cho các đối tượng chưa có block riêng như `Block cọc (Pile)`, `Block khung tên ATTDEF`.

---

## 2. HIỆN TRẠNG ĐÃ KIỂM CHỨNG TRONG CODEBASE

### 2.1 Vì sao kỹ sư mở template sửa hiện tại KHÔNG có tác dụng?
1. Chỉ có 1 template BTCT active là `skills/Technical_Illustrator/cad_integration/templates/DCE_Master_Seed_Template.dxf` (clone từ `Form 2.dxf`) và 1 template dictionary SSOT mới tạo là `_SHARED/data/DCE_Pro_And_Steel_Template.dxf` (78 layer, 18 DimStyle, 98 user block + anonymous blocks).
2. `cad_plan_engine.py`: `DcePlanEngine.setup()` chạy `for e in list(self.msp): self.msp.delete_entity(e)` (line 2033–2034), xóa sạch ModelSpace của template rồi vẽ lại khung A1/A0 và bảng biểu bằng tọa độ cứng trong Python.
3. `cad_multiview_a3.py`: `render_multiview_a3_sheet()` cũng xóa trắng ModelSpace rồi gọi `_render_a3_frame_title_and_keyplan()` vẽ cứng khung A3 (`42000x29700`), đường chia ngang (`y=14850`) và khung tên dọc (`tb_x0=36858.0`) từ code Python.

### 2.2 Kiểm kê Block thực tế trong `DCE_Master_Seed_Template.dxf` & `DCE_Pro_And_Steel_Template.dxf`

| Nhóm đối tượng | Block có sẵn đã đọc được | Cấu trúc / ATTDEF thực tế | Tình trạng sử dụng hiện tại & Vấn đề kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Trục (Grid Bubble)** | `Dce_KhTenTruc`, `Dce_TenTruc` | `2 CIRCLE`, `4 LINE`, `1 ATTDEF (TRUC)` | `cad_plan_engine.py` đã dùng `Dce_KhTenTruc`; `cad_multiview_a3.py` chưa tận dụng thống nhất hoặc scale chưa chuẩn mọi khổ |
| **Cột (Column)** | `DCE_CL_REC1_`, `DCE_CL_Circle_`, `TenCauKien` | `DCE_CL_REC1_` lồng 5 Dynamic Block `*U135..*U139` (`HATCH DCE_Hatch`, `LWPOLYLINE`, `POINT Defpoints`, `ATTDEF DCE_SUB-COLN_T---`, `DCE_SUB-COLN_S---`); `DCE_CL_Circle_` lồng `*U89`; `TenCauKien` có `SOCAUKIEN`, `TENCAUKIEN` | Hiện tại cột/lõi vẽ rời bằng `LWPOLYLINE` + `HATCH` trong Python thay vì `INSERT` Block cột. **Lưu ý:** Dynamic Block `*U*` của DCE phụ thuộc AutoCAD Action nên chỉnh tham số động trực tiếp từ `ezdxf` headless rất hạn chế -> cần bàn giải pháp |
| **Dầm / Lanh tô** | `DCE_Beam2`, `DCE_LanhTo2`, `DCE_Name`, `Dce_KhTenDam`, `Dce_KhTenNhip` | `DCE_Beam2` lồng `*U111` có `WIPEOUT` (`DCE_WIPEOUT`), `LINE` (`DCE_GoiDam`), `ATTDEF` (`DCE_TenNhip`, `DCE_KT`, `DCE_Name`, `DCE_CDD`); `DCE_Name` có `MARK` | Mới dùng một phần `DCE_Name` / text rời; chưa khai thác đồng bộ `Dce_KhTenDam`, `Dce_KhTenNhip` |
| **Cọc (Pile)** | **CHƯA CÓ** trong `DCE_Master_Seed_Template.dxf` (`Form 2.dxf`) | Không thấy `DCE_Pile` / `DCE_Coc` trong `Form 1..5` (cần kiểm chứng thêm `System/` hoặc tạo block chuẩn mới) | `cad_multiview_a3.py` đang vẽ cọc rời bằng `CIRCLE` + `LINE` cross; chưa đóng thành Block + `ATTDEF` (`PILE_ID`, `D`, `L`) |
| **Tiêu đề / Sàn / Thép / Cao trình** | `DCE_Plan header 1`, `DCE_Slab tag`, `DCE_Drop mark`, `Dce_CaoTrinh`, `DCE_MatCatA`, `Dce_KhMatCat`, `Dce_DanhDauThep`, `Dce_KhtMcThepChu`, `Dce_KhtThepDai`, `TK1`..`TK44` | Có `ATTDEF` đầy đủ (`SCALE_1:100`, `DRAWING-VN`, `DRAWING-E`, `CT`, `SH`, `DK`, `SL`, `KL`...) | Hiện hầu hết tiêu đề view (`MẶT BẰNG ĐỊNH VỊ CỌC`), nhãn sàn, bảng thống kê thép đang vẽ bằng `TEXT`/`LINE` rời |
| **Khung tên (Title Block)** | `TKTitle`, `TKTitleE`, `Khung A3` (trống trong `Form 2`) | `TKTitle` chứa `LWPOLYLINE + LINE + TEXT tĩnh` (chưa có `ATTDEF`) | Chưa có Block Khung tên `ATTDEF` chuẩn cho A1 và A3 để User sửa tự do trong AutoCAD |
| **Kho mẫu tổng hợp & Steel** | `Block_ALL` (106 `INSERT` bên trong); `Form 1_Steel.dwg` / `Form 2_Steel.dwg` có thêm 109–115 block (`BOLTS`, `BMB.Nut`, `CL`, `DCE_BTKCK`, `DCE_BangThongKe`, `DCE_SectionMark`, `DCE_TH1..`) | Lưu trong `cad_integration/templates/` & `C:\Dce Pro\Cad\` | Chưa có Form DXF riêng cho Steel và Chi tiết |

---

## 3. KIẾN TRÚC ĐỀ XUẤT ĐỂ THẢO LUẬN VỚI CLAUDE

### Đề xuất A — Thư viện **4 Bộ Form Mẫu Mở** (User-Editable DXF Forms)
1. `Form_01_MatBang_A1_BTCT.dxf` — Mặt bằng định vị cột-vách / dầm-sàn khổ A1/A0 (1 viewport chính + sidebar bảng thống kê).
2. `Form_02_MultiView_A3_BTCT.dxf` — Hồ sơ A3 ngang nhiều khung nhìn (`TOP`/`BOT` như `KC.02`, `KC.13–15` + Key Plan + Ghi chú).
3. `Form_03_KetCau_Thep_Steel.dxf` — Kết cấu thép (`DCE STEEL` 16 layer + block bu lông/bản mã/mặt cắt thép).
4. `Form_04_ChiTiet_Coc_Dam_Cot.dxf` — Chi tiết móng cọc, mặt cắt cột/dầm/sàn/thang + bảng thống kê thép `TK1..TK44`.

### Đề xuất B — Hợp đồng Mẫu Mở (Non-Destructive Form Contract)
- **KHÔNG xóa ModelSpace (`msp.delete_entity`)** khi dùng Form mở. Thay vào đó:
  - Phân tách **Shell Layer (do User sửa trong AutoCAD)** vs **Zone Marker Layer (hình chữ nhật quy ước trên layer `DCE_ZONE_VIEWPORT`, `DCE_ZONE_TABLE`, `DCE_ZONE_NOTE`, `DCE_ZONE_KEYPLAN`)** -> Engine đọc `bbox` của các Zone Marker đó để scale & đặt hình học vào đúng khung bạn muốn.
  - **Khung tên đóng thành `Block + ATTDEF`** (`DCE_TITLEBLOCK_A1`, `DCE_TITLEBLOCK_A3`) với danh sách tag chuẩn (`TEN_CONG_TRINH`, `CHU_DAU_TU`, `TEN_BAN_VE`, `KY_HIEU`, `TY_LE`, `NGAY_VE`, `GIAM_DOC`, `CHU_TRI`, `THE_HIEN`, `DIA_CHI`, ...). User sửa kiểu chữ, đường kẻ, logo thoải mái trong Block Editor -> Engine chỉ cập nhật `ATTRIB.text`.
  - **Kế thừa Style từ Form (`Inherit-from-Form`)**: Nếu Layer / DimStyle / TextStyle đã có trong file Form User vừa sửa, Engine **tuyệt đối không ghi đè màu/ltype**, trừ khi thiếu layer mới bổ sung từ SSOT (`dce_layers_standard.json`).

### Đề xuất C — Chiến lược Tái sử dụng Block DCE & Xử lý Dynamic Block trong `ezdxf`
Cần Claude cùng phân tích sâu 4 điểm sau:
1. **Dynamic Block DCE (`DCE_CL_REC1_`, `DCE_CL_Circle_`, `DCE_Beam2`) dùng `*U...` trên headless `ezdxf`:**
   - Nếu `INSERT` nguyên bản Dynamic Block rồi non-uniform scale (`xscale=B/ref, yscale=H/ref`), Hatch/Text bên trong có bị méo chữ `ATTDEF` và méo dày nét hatch không?
   - Hay tốt hơn nên dùng **Block-per-Type (Generated Named Block)** theo chuẩn lớp/style DCE — ví dụ sinh `DCE_BLOCK_COL_300x500` (chứa outline `DCE_Col` + solid hatch `DCE_Hatch` + `ATTDEF TENCAUKIEN` chuẩn tỷ lệ chữ 1:1 không bị scale méo), `DCE_BLOCK_PILE_D300` (`CIRCLE` + cross + `ATTDEF PILE_ID`), hoặc tách phần hình học (scale được) khỏi `ATTDEF` nhãn (Block `TenCauKien` riêng không bị méo)?
2. **Chuẩn hóa Block Trục (`Dce_KhTenTruc` / `Dce_TenTruc`), Block Cao trình (`Dce_CaoTrinh`), Block Header (`DCE_Plan header 1`), Block Sàn (`DCE_Slab tag`)**:
   - Những Block này đã có `ATTDEF` chuẩn 1:1 -> chỉ cần chọn `scale` theo tỷ lệ viewport (`S = 100` hoặc từ `DimStyle`), chèn `INSERT` + điền `ATTRIB` là hoạt động ngay cả headless lẫn AutoCAD live!
3. **Thư mục đặt 4 Form (`00_Template_&_Standards/CAD_Forms/` vs `.agents/...`) và chế độ Override theo dự án:**
   - Có nên để bộ chuẩn gốc ở `.agents/` (fallback/SSOT) và thư mục User sửa hàng ngày ở `00_Template_&_Standards/CAD_Forms/` (hoặc 1 nơi duy nhất dễ mở, đồng bộ Drive) + ưu tiên `project_dir/CAD_Forms/` nếu dự án có mẫu riêng?
4. **Cơ chế nâng cấp `dce_cad_compliance_checker.py` & `cad_evidence_contract.py`:**
   - Khi chuyển cột/cọc/trục/khung tên sang `INSERT Block + ATTRIB`, cần đảm bảo Bộ lọc 8 Compliance Checker đọc được tọa độ/text từ `INSERT` + `ATTRIB` (không chỉ `LWPOLYLINE`/`MTEXT` rời), tránh gãy 184 test hiện có.

---

## 4. CÂU HỎI GỬI CLAUDE THẢO LUẬN & ĐỀ XUẤT

Claude vui lòng đọc các tệp liên quan và đưa ra **đánh giá phản biện + phương án thiết kế chi tiết** (chưa cần sửa code sản xuất trong lượt thảo luận này, hoặc chỉ đề xuất rõ kiến trúc + lộ trình từng bước để User chốt):
1. Đánh giá mô hình **4 Bộ Form Mở** (bố cục Zone Marker + `DCE_TITLEBLOCK` `ATTDEF` + `Inherit-from-Form`): có lỗ hổng gì khi User kéo dãn/chỉnh tay trong AutoCAD (VD: User xóa nhầm Zone Marker, chỉnh `UCS`, lưu đè DWG/DXF version mới AC1027/AC1032, đặt khung tên ở PaperSpace Layout vs ModelSpace)?
2. Đề xuất **kiến trúc chuẩn nhất để dùng Block Cột, Block Trục, Block Cọc, Block Dầm, Block Tiêu đề** từ kho DCE trong bối cảnh vừa chạy headless `ezdxf` vừa tương thích 100% AutoCAD thật (giải quyết bài toán Dynamic Block `*U*` và chữ `ATTRIB` không bị méo khi scale khác `1:1`).
3. Thống nhất **cách chia Phase triển khai nhỏ, regression-safe** với `cad_plan_engine.py` + `cad_multiview_a3.py` + `dce_cad_compliance_checker.py` (không làm vỡ 184 test hiện có).

Ghi phản hồi thảo luận của Claude vào `.agents/memory/CLAUDE_RESPONSE_4FORM_AND_BLOCKS.md` (hoặc cập nhật bus bàn giao về lại `GEMINI` kèm nhận xét).
