# Phân tích độc lập hồ sơ kết cấu Nhà phố Cát Lái Q2

**Mã nhiệm vụ:** `08_PRACTICAL_CAD_ANALYSIS_CAT_LAI`  
**Nguồn kiểm:** `01_Projects/08_NHA_PHO_Q2/01_Input_CAD_PDF/NHA PHO Q2 CAT LAI 13.09.2026.pdf` (38 trang, 1191 × 842 pt, xấp xỉ A3 ngang); brief của Gemini; mã `cad_plan_engine.py` hiện tại.  
**Phạm vi:** Bố cục và kiến trúc CAD; không kiểm toán tính toán chịu lực hoặc sự đầy đủ pháp lý của hồ sơ.

## Nhận định từ PDF gốc

1. **Mục lục theo trình tự thi công dễ tra cứu.** Trang 2 liệt kê GCC.01–04 và KC.01–32. Trang 3–6 là chỉ dẫn chung; 7–10 móng/ngầm; 11–18 cột; 19–21 mặt bằng dầm sàn; 22–28 mặt bằng thép sàn; 29–38 chi tiết dầm. Đây là một cấu trúc hợp lý cho công trình này, nhưng không nên coi mã `GCC`/`KC` hoặc thứ tự đó là một yêu cầu tự thân của ISO 128, AIA hay BS 1192. Engine cần cho phép cấu hình mã tờ và bảng mục lục, giữ tham chiếu chéo ổn định.
2. **Hai mặt bằng trên một tờ A3 ngang.** Trang 8 (`KC.02`) ghép định vị cọc với kết cấu hầm; trang 11 (`KC.05`) ghép hai giai đoạn cột; trang 19 (`KC.13`) ghép tầng 1 với lửng. Mỗi hình có tên và tỷ lệ riêng, ngăn bằng đường phân vùng ngang. Chiều dài nhà 18.000 mm được đặt theo chiều ngang tờ, bề rộng 5.000 mm theo chiều đứng. Quy tắc nên dựa trên kích thước đã xoay và bbox chú thích thực, không chỉ tỷ số W/L của hình gốc.
3. **Thép trên/dưới là hai hình riêng trên cùng tờ.** Trang 22 (`KC.16`) thể hiện lớp trên ở nửa trên và lớp dưới ở nửa dưới; trang 23–28 tiếp tục mô hình này. Brief mô tả “hai bản vẽ riêng biệt”; cần hiểu là hai *view* độc lập, không phải hai tờ giấy riêng. Hai view có cùng lưới trục để đối chiếu nhưng chỉ render nhãn/thanh thép của lớp tương ứng; mỗi view có ghi chú riêng.
4. **Khung tên dọc bên phải.** Trên các trang đại diện 8, 11, 19, 22, dải phải chứa Key Plan, thông tin ký duyệt, tên tờ, mã tờ. Bề rộng ước tính khoảng 50–55 mm trên A3 từ tỷ lệ ảnh PDF; đây là phép đo xấp xỉ, không phải kích thước CAD gốc.
5. **Kích thước và ký hiệu.** Trang 8/11 có chuỗi kích thước tim trục từng nhịp (3.000, 3.700, 3.500...), tổng 18.000, cùng kích thước định vị chi tiết ở chỗ cần thiết. Trang 11 có chú giải cột liên tục/cột dừng. Đề nghị coi ba lớp thông tin này là vai trò ngữ nghĩa, không bắt buộc tất cả xuất hiện trên mọi cạnh và mọi tờ.

## Ma trận GAP: Hồ sơ thực tế và Engine v5.0

| Chủ đề | Bằng chứng hồ sơ | Engine hiện tại | Chênh lệch và mức ưu tiên |
|---|---|---|---|
| Khổ tờ & khung tên | A3 ngang, dải phải ~50–55 mm trên trang 8/22 | `SheetLayoutFitter` có A3 trong danh sách khổ nhưng dùng sidebar 200 mm cho mọi khổ ngoài A1; xuất frame/title block còn gắn logic A1 | **P0:** cấu hình khung tên theo khổ; 200 mm không khả thi với A3 rộng 420 mm. |
| Hai view/tờ | Trang 8, 11, 19, 22 | Fitter có nhãn `DUAL_VERTICAL_VIEWPORT` theo điều kiện chiều cao, nhưng luồng render mặt bằng vẫn là một plan và một `plan_x0/plan_y0` | **P0:** tạo hai `ViewportSpec` độc lập, fit và collision riêng. Nhãn mode chưa đủ chứng minh DXF đã có 2 view. |
| Thép sàn trên/dưới | Trang 22–28, hai view cùng tờ | `SlabRebarStripSpec.layer_pos` đã có `TOP`/`BOTTOM`; dữ liệu demo chứa cả hai | **P0:** filter mỗi view theo `layer_pos`; chống trộn thép, nhãn và chú giải. |
| Key Plan | Góc trên sidebar trang 22 | Không thấy block `DCE_KeyPlan` trong engine | **P1:** block có bbox riêng và tham chiếu bản đồ/ảnh theo project metadata. |
| Cột dừng/đi tiếp | Chú giải trang 11 | `ColumnSpec.status` đã có `STOPPED`/`CONTINUOUS`, block riêng | **P1:** tự sinh legend khi cả hai trạng thái có mặt; kiểm quy tắc nhất quán giữa các tầng. |
| Ba vai trò kích thước | Nhịp, tổng, định vị cục bộ trên trang 8/11 | Fitter có 4 tier gồm bubble; builder có nhịp và tổng, setout có logic riêng | **P1:** hợp nhất thành semantic `LOCAL/GRID/OVERALL` + `BUBBLE`, thuật toán tránh va chạm theo từng view. |
| Chỉ dẫn cạnh view | Legend thép riêng ở cả hai nửa trang 22 | Schedule/notes chủ yếu gắn canvas toàn tờ/sidebar | **P1:** `ViewportNoteSpec`, neo theo bbox view. |
| Mục lục và mã tờ | GCC.01–04, KC.01–32 trang 2 | Engine tập trung xuất tờ đơn | **P2:** `SheetSetManifest` sinh mục lục, kiểm mã duy nhất, số trang và revision. |

## Đề xuất spec cho Sprint tiếp theo

### 1. Multi-Viewport Layout

- `SheetSpec(paper='A3', orientation='LANDSCAPE', scale=100, title_block='RIGHT_STRIP', sidebar_width_paper_mm=55, left_margin_paper_mm=10, other_margin_paper_mm=5)`; các giá trị là **đề xuất mặc định**, cần hiệu chỉnh bằng template được chủ đầu tư duyệt.
- `ViewportSpec(id, source_plan_id, rotation_deg, layer_filter, title, scale, note_ids, bbox_paper_mm)`; hỗ trợ `SINGLE` và `STACKED_2` (hai view trên/dưới). Dùng tọa độ giấy cho chia khung, transform model→paper riêng cho từng view; giữ DXF modelspace hoặc paperspace theo một quy ước xuyên suốt.
- Thử hai phương án xoay 0°/90°, rồi fit theo bbox mở rộng gồm hình học, 3 tier kích thước, bong bóng, tên view và ghi chú. Chọn phương án có scale khóa đạt fit và ít diện tích trống hơn. Với `STACKED_2`, yêu cầu hai bbox không giao nhau sau khi nới mỗi bbox thêm **5 mm giấy**; 5 mm là tham số đề xuất, không phải số đo từ PDF.
- Mỗi view có clipping/collision domain riêng. Kiểm `min_clearance(view_1, view_2) >= 5 mm giấy` cho **toàn bộ** geometry + text + bubble + dimension. Với S=100, 5 mm giấy tương đương 500 mm model trong layout modelspace nhân tỷ lệ.
- Chỉ chọn `STACKED_2` nếu cả hai view khóa tỷ lệ mong muốn đều fit và tổng diện tích sử dụng tốt hơn `SINGLE`; nếu không, tách tờ. Không dùng duy nhất ngưỡng `W/L` vì nhà 5×18 m chỉ thành mặt bằng ngang hiệu quả sau khi xoay.

### 2. Top/Bottom Slab Rebar

- `RebarViewSpec(floor_id, face='TOP'|'BOTTOM', source_geometry_id, scale, legend_id)`. Mỗi strip/thanh phải có `face` bắt buộc; `TOP` chỉ render thép lớp trên, `BOTTOM` chỉ render lớp dưới. Cho phép `BOTH` chỉ ở view tổng hợp được khai báo rõ.
- Sinh `KC.xx` gồm hai view cùng một tờ theo cấu hình `TOP_OVER_BOTTOM` hoặc `BOTTOM_OVER_TOP`; ảnh trang 22 dùng top trên, bottom dưới, nhưng thứ tự khác có thể cấu hình.
- Lưới trục, dầm, lỗ mở và biên sàn dùng chung nguồn geometry để hai view đăng ký trùng tọa độ. Mã thép, chiều dài neo, khoảng cách và legend lấy từ dữ liệu kết cấu; kiểm cùng một strip không bị render hai lần do lọc lớp.
- Bộ kiểm tối thiểu: `face_mismatch=0`, `duplicate_strip_id=0`, bbox text/steel không giao nhau ngoài ngoại lệ ghi rõ, hai view cùng floor và cùng scale trừ khi metadata giải thích.

### 3. Title Block, dims và sheet set

- Thêm `DCE_TitleBlock_A3_Right` và `DCE_KeyPlan` với vùng riêng cho Key Plan, chữ ký, tên bản vẽ, mã tờ; không co block A1 xuống A3. Kiểm các vùng con không chồng lên nhau sau xuất DXF/PDF.
- Dim tiers biểu diễn bằng dữ liệu `LOCAL/GRID/OVERALL`; bubble là annotation riêng. Khoảng cách tier theo mm giấy và scale, có thể giảm tier khi tờ chật nhưng phải giữ phép đo cần thiết. Kích thước xuất bằng `DIMENSION` native.
- `SheetSetManifest` gồm `sheet_code`, `title`, `discipline`, `sequence`, `revision`, `viewport_ids`; tự sinh mục lục và kiểm liên kết tên trên tờ.

## Tương thích Rule 12b–12e

Rule 12b (màu chữ dễ đọc) và 12d (đồ họa CAD) có thể áp dụng cho DXF mới; cần kiểm màu *sau khi xuất* theo ACI/true color và cấu hình plot style. Rule 12c về cấp bê tông là ràng buộc dữ liệu thiết kế, không thể suy ra chỉ từ bố cục PDF. Rule 12e về cỡ chữ Word/Excel không nên áp cứng cho chữ CAD theo đơn vị point; CAD cần chiều cao chữ **trên giấy in** theo từng loại chú thích. Hồ sơ gốc dùng nhiều mức chữ và nét; mục tiêu của engine là giữ tính phân cấp, không sao chép nguyên trạng mọi chi tiết thủ công.

## Kết luận

Ưu tiên triển khai A3 right-sidebar và hai viewport thật trước. Tiếp theo tách filter thép TOP/BOTTOM, legend/notes theo viewport và bộ kiểm collision. Mục lục tự động và Key Plan là bước hoàn thiện bộ hồ sơ. Các ngưỡng 55 mm sidebar, 5 mm giữa view là đề xuất thiết kế, cần thử bằng bộ tờ thực tế và render in A3 để chốt.
