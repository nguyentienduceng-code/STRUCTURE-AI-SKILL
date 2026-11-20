# HƯỚNG DẪN TÙY BIẾN 4 BỘ FORM CAD TRỰC TIẾP TRONG AUTOCAD

Thư mục này chứa **4 Bộ Form Mẫu Mở** đồng bộ trên Google Drive để kỹ sư tự mở bằng AutoCAD chỉnh sửa giao diện, khung tên, màu layer, dimstyle và bố cục khung nhìn. Khi Agent xuất bản vẽ ở chế độ `template_mode="open"`, toàn bộ chỉnh sửa của bạn sẽ được **giữ nguyên 100%**.

## 1. Danh mục 4 Bộ Form

| Tệp Form | Khổ giấy | Công dụng | Block Khung tên |
| :--- | :---: | :--- | :--- |
| `Form_01_MatBang_A1_BTCT.dxf` | A1 | Mặt bằng định vị cột-vách, dầm sàn BTCT | `DCE_TITLEBLOCK_A1` |
| `Form_02_MultiView_A3_BTCT.dxf` | A3 | Bản vẽ triển khai nhiều khung nhìn (`KC.02`, `KC.13–15`...) | `DCE_TITLEBLOCK_A3` |
| `Form_03_KetCau_Thep_Steel.dxf` | A1 | Mặt bằng & liên kết Kết cấu Thép (`DCE STEEL`) | `DCE_TITLEBLOCK_A1` |
| `Form_04_ChiTiet_Coc_Dam_Cot.dxf` | A3 | Chi tiết cọc, đài móng, cột, dầm, thống kê thép `TK*` | `DCE_TITLEBLOCK_A3` |

## 2. Thứ tự ưu tiên tìm Form

Khi chạy cho một dự án, Agent tự động tìm theo 3 tầng:
1. `<Thư mục dự án>/CAD_Forms/` *(mẫu riêng từng công trình)*
2. `00_Template_&_Standards/CAD_Forms/` *(thư mục chuẩn công ty — chính là thư mục này)*
3. `.agents/_SHARED/data/CAD_Forms/` *(bộ gốc dự phòng bất biến của Agent)*

## 3. Bạn được sửa gì trong AutoCAD?

1. **Sửa Khung tên (`BEDIT` Block `DCE_TITLEBLOCK_A3` hoặc `DCE_TITLEBLOCK_A1`):**
   - Chèn logo công ty, đổi kiểu khung, thêm dòng chữ cố định, đổi Font `Dce_Text`, đổi vị trí/cỡ chữ các ô.
   - **Lưu ý giữ nguyên các Tag thuộc tính (`ATTDEF`) bắt buộc:** `TEN_CONG_TRINH`, `TEN_BAN_VE`, `KY_HIEU`, `TY_LE` (có thể thêm Tag riêng của công ty — Agent sẽ giữ nguyên không xóa).
2. **Sửa Màu Layer, Nét vẽ, DimStyle (`Dce_*MV`), TextStyle:**
   - Mở `LA` (Layer Manager) hoặc `D` (DimStyle) để chỉnh màu nét in, chiều cao chữ, mũi tên dim theo chuẩn riêng của bạn -> Save (`Ctrl+S`).
3. **Kéo giãn / Dời vị trí vùng vẽ (`DCE_ZONE_*`):**
   - Các khung chữ nhật trên layer `DCE_ZONE_VIEWPORT_TOP`, `DCE_ZONE_VIEWPORT_BOTTOM`, `DCE_ZONE_TABLE`, `DCE_ZONE_NOTE`, `DCE_ZONE_KEYPLAN` là layer không in (`No Plot`). Bạn dùng lệnh `Stretch` kéo to/nhỏ hoặc dời vị trí khung nhìn; Agent sẽ tự căn chỉnh bản vẽ lọt vào đúng khung mới.
4. **Lưu file:**
   - Lưu dưới định dạng **AutoCAD 2007 DXF (`AC1021`)** hoặc cao hơn để đảm bảo tương thích. Tránh xóa mất các khung `DCE_ZONE_*` hoặc đổi UCS khỏi `World`.

## 4. Kho Block DCE chuẩn tích hợp sẵn trong mọi Form

- Trục định vị: `Dce_KhTenTruc` (`TRUC`), `Dce_TenTruc`
- Cột & Tên cấu kiện: `DCE_COL_*` (hình học chuẩn từng tiết diện không méo hatch) + `TenCauKien` (`TENCAUKIEN`, `SOCAUKIEN`), `DCE_CL_REC1_`, `DCE_CL_Circle_`
- Cọc: `DCE_Pile_SQ_TYPE1/2/3_250_X`, `DCE_Pile_CIR_TYPE1_D300` (`PILE_ID`, `D`, `L`, `Q`)
- Cao trình / Sàn / Dầm / Thống kê thép: `Dce_CaoTrinh` (`CT`), `DCE_Slab tag` (`200`), `DCE_Drop mark` (`50`), `DCE_Plan header 1`, `DCE_Beam2`, `Dce_KhTenDam`, `TK1`..`TK44`
