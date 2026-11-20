# CODEX A1 — Tái kiểm định c2_remediated_v2

Ngày 2026-11-15. Dự án `09_DCE_CAD_BLOCK_SEMANTICS_V6`.

**Kết luận: PARTIAL PASS / CHƯA PHÊ DUYỆT SẢN PHẨM CUỐI.** Các sửa đổi entity/schema/linkage đã được xác minh đạt. Còn ba nhóm lỗi trình bày và liên kết dữ liệu thiết kế cần hoàn thiện. Không lặp lại các lỗi cũ đã được sửa.

## Phần đã đạt qua chạy mới

- Checker `physical`: PASS 5/5 DXF; `plan`: PASS 5/5, theo evidence.json.
- Scale thực tất cả view là 1:50; bbox dual không giao nhau; KC-04 có freeze REBAR_TOP/REBAR_BOTTOM tương ứng.
- Chạy lại validator: 8/8 cổng đạt gồm hash manifest, hash sidecar, handle tồn tại và strict three-way linkage. Log JSON: `linkage.json`.
- Tag bản đế, STEEL_PL_01, schedule handles, refs, định dạng SIZE và provenance đã sửa. Có 5 chữ ký hình học khác nhau.
- `test_dce_block_semantics.py`: 13/13; `test_cad_v6_c2.py`: 5/5 PASS. Full regression ghi riêng trong `regression/`.
- Full regression chạy mới: **33/33 suites PASS**, 154,58 giây. Các test hiện hữu chưa bao phủ ba nhóm lỗi dưới đây.

## V2-01 — Bảng kê tồn tại nhưng không nằm trên bản in

**P0, chủ trì GEMINI (đã tiếp nhận phần renderer).** Tất cả 62 entity layer DCE_Schedule trong modelspace mỗi tờ nằm ngoài vùng nhìn của mọi viewport. Bảng kê model có x từ 31.000 tới 41.000; giới hạn x phải của view lớn nhất là 28.750. Kết quả kiểm giao bbox: **0/62 entity bảng kê nhìn thấy trên mỗi view**.

| Tờ/view | Vùng nhìn model `[xmin,ymin,xmax,ymax]` |
|---|---|
| KC-02/04 dưới | `[8750,10750,18250,17250]` |
| KC-02/04 trên | `[8750,11750,18250,18250]` |
| KC-03 | `[9250,7375,26750,20625]` |
| KC-06/07 | `[11250,10375,28750,23625]` |

Paperspace chỉ có mục lục và chữ “GHI CHU & BANG KE” ở một số tờ, chưa có dòng dữ liệu bảng kê thay thế. Hai view KC-02 còn cùng floor-agnostic scene, khác tâm nhìn 1000 mm; cần filter tầng/phạm vi thật. Các trục/đầu cấu kiện ở ngoài cửa sổ cũng có nguy cơ bị cắt. Phải kiểm đủ bbox nội dung bắt buộc nằm trong vùng plot hoặc được thể hiện bằng view khác.

Yêu cầu sửa: bảng kê đặt paperspace hoặc có viewport riêng; fit view theo bbox hình học và annotations thực, vẫn giữ scale khóa. Thêm test kiểm dòng bảng kê thực xuất hiện trên giấy và không bị clip, không chỉ kiểm handle tồn tại.

## V2-02 — Preview không phản ánh layout DXF

**P1, GEMINI.** `render_sheet_set_previews()` vẽ modelspace lên một trục matplotlib với giới hạn cố định, không áp dụng transform/clip/frozen layer của từng paperspace viewport. Đã xem trực tiếp KC-04_preview.png: TOP và BOTTOM gộp chung một hình; danh sách hai viewport chỉ là chữ ở sidebar. PDF được dựng từ cùng figure nên không chứng minh hai view trên giấy. Kích thước figure 11,69×8,27 inch cũng là A4 ngang, không phải trang PDF A3 420×297 mm.

Đọc PDF bằng PyMuPDF xác nhận cả 5 trang có kích thước **296,93×210,06 mm**.

Yêu cầu sửa: preview/PDF đi từ layout thực hoặc pipeline tái hiện đúng từng viewport, filter và paper scale; PDF đúng A3. Test so khớp vị trí/visibility giữa DXF và preview, có hai vùng TOP/BOTTOM độc lập. Không dùng bản vẽ minh họa dựng lại làm bằng chứng plot CAD đã đạt.

## V2-03 — Chi tiết và thép còn gán cứng, chưa chứng minh thay đổi theo input

**P0, GEMINI; CODEX kiểm mutation sau sửa.** Hàm `_add_sheet_role_specific_geometry()` trong cad_sheet_set.py vẫn gán cứng:

- KC-03: hai slab tag `h=120` cùng tọa độ, không lấy chiều dày từ panel input.
- KC-06: nhãn `200x400`, `2D20+3D20`, `D8a150` và hình vẽ gán cứng. Mặt cắt được vẽ 600×1200 (phóng 3 lần trong model) nhưng viewport vẫn 1:50; chiều cao dầm ở elevation là 800 dù nhãn ghi 400. Chưa khai báo tỷ lệ chi tiết riêng tương ứng.
- KC-07: tiết diện cột và bản đế phóng 2–3 lần trong model; nhãn giữ kích thước thật, chưa có viewport scale riêng hoặc dimension override có căn cứ. Hình gusset ghi PL240x180x14 nhưng đa giác gán cứng 900×780.
- KC-04: hình dạng/thứ tự dải thép lấy từ idx và các tọa độ cố định; source fixture chỉ chứa face/direction/bar_spec/zone, không có hình học vùng/thanh đủ để xác nhận đúng vị trí thiết kế. Khối kiểm missing input chưa chặn tình huống thiếu hình học và thép chi tiết.

Yêu cầu sửa: bổ sung schema/fixture thiết kế thử có đủ geometry, thickness, rebar, cover, chiều dài và detail scale; dựng chi tiết 1:1 model rồi scale bằng view/block được ghi rõ. Thay section/thickness/rebar/scale trong input phải cập nhật hình và nhãn tương ứng. Thiếu input phải trả MISSING_INPUT. Các case demo cố định cần tách khỏi đường export tổng quát và không được cấp PASS như dữ liệu thiết kế đã liên kết.

## Bàn giao sửa tiếp

GEMINI giữ vai trò tích hợp sửa V2-01..03 theo bàn giao mới; phối hợp CLAUDE nếu cần. Giữ nguyên artifact v2, xuất thư mục mới. Sau sửa, chạy mutation tests và full regression, cung cấp DXF + PDF A3 từ layout thực; CODEX kiểm lại. Phạm vi static/native đã có tiến bộ; Dynamic Block và chỉnh sửa DCE runtime vẫn không được suy ra từ catalog/ATTRIB.
