# Quy trình lập bộ bản vẽ kết cấu DCE Pro

**Phiên bản:** 1.0 — 2026-11-15. **Phạm vi:** Hồ sơ bản vẽ kết cấu nhiều tờ. Tài liệu này mở rộng hướng dẫn CAD trong `SKILL.md`; không thay thế kiểm toán tính toán kết cấu.

## 1. Bằng chứng và giới hạn

- **Hồ sơ tham chiếu:** `01_Projects/08_NHA_PHO_Q2/01_Input_CAD_PDF/NHA PHO Q2 CAT LAI 13.09.2026.pdf`, 38 trang A3 ngang. Trang 2 có danh mục `GCC.01–04`, `KC.01–32`; trang 8 `KC.02` có hai view cọc/hầm; trang 11 `KC.05` có hai view cột; trang 19 `KC.13` có hai view dầm sàn; trang 22 `KC.16` có view thép trên và dưới **trên cùng tờ**; trang 38 `KC.32` có chi tiết dầm. Thứ tự mã là đặc điểm của hồ sơ tham chiếu, không phải quy tắc bắt buộc cho mọi dự án.
- **Lỗi mục lục cần tránh:** Trang 2 ghi `GCC.03 = GHI CHÚ CHUNG 04` và `GCC.04 = GHI CHÚ CHUNG 03` theo text trích xuất. Cần kiểm trực quan/tờ gốc trước khi kết luận đây là lỗi phát hành; dù vậy, manifest một nguồn sẽ loại được kiểu không khớp mã/tên này trong sản phẩm Agent.
- **Sản phẩm Agent đối chiếu:** `01_Projects/03_Sprint2_KetQua_NeChu_CAD/KC-01_TongMatBang_v50_DA_SUA_KHUNG.dxf`, `KC-02_DinhViCotVach_v50_DA_SUA_KHUNG.dxf`, `KC-03_KetCauDamSan_v50_DA_SUA_KHUNG.dxf`. Đây là 3 tờ minh họa/tầng điển hình A1, **không phải** một bộ TKTC 38 tờ. Không gắn nhãn “đã đủ hồ sơ thi công” cho bộ ba này.
- **Nguồn thực thi:** `cad_integration/cad_plan_engine.py` có `SheetLayoutFitter`, `ColumnSpec.status`, `SlabRebarStripSpec.layer_pos`, native DIMENSION/HATCH/ATTRIB. Hiện chưa chứng minh khả năng phát hành bộ tờ A3 hai view, thép trên/dưới thành hai view độc lập hay mục lục tự động.

## 2. Ma trận nội dung phải có theo phạm vi thiết kế

| Nhóm tờ | Nội dung cần thể hiện | Dữ liệu đầu vào tối thiểu | Điểm kiểm tra trước phát hành |
|---|---|---|---|
| Bìa, mục lục | Danh mục mã tờ, tên tờ, revision, Key Plan nếu có | Sheet manifest, vị trí công trình | Mã tờ duy nhất; tên trên mục lục khớp title block; không bỏ tờ. |
| Ghi chú chung | Vật liệu, cấp bền, lớp bảo vệ, ký hiệu, quy tắc neo/nối và quy chiếu | Thuyết minh, tiêu chuẩn áp dụng, chỉ định kỹ sư | Không tự điền cấp vật liệu hay chiều dài neo; ghi nguồn/quyết định thiết kế. |
| Móng/ngầm | Định vị cọc/đài, dầm móng, mặt bằng ngầm, cao độ, bảng kê và chi tiết | Khảo sát, thiết kế móng, trục/ranh đất | Tọa độ cọc/đài và mã cấu kiện khớp bảng kê/chi tiết; cao độ có mốc. |
| Cột/vách | Mặt bằng theo phạm vi tầng; trạng thái cột dừng/đi tiếp; kích thước, định vị và bảng kê | Trục, cấu kiện, tầng bắt đầu/kết thúc, tiết diện/thép | Không mất cột qua tầng, không vẽ cột dừng như liên tục; nhãn và legend khớp. |
| Dầm/sàn | Mặt bằng theo tầng, mã dầm, ô sàn, lỗ mở, cao độ, chiều dày, chi tiết tham chiếu | Lưới trục, dầm phân nhịp, slab panels, openings | Không nối dầm xuyên gối; không bỏ lỗ mở; mã dầm liên kết đúng chi tiết. |
| Thép sàn | View lớp trên và view lớp dưới, phương, mã thanh, đường kính/bước và vùng đặt thép | Rebar strips theo tầng, `face=TOP/BOTTOM`, geometry sàn | Hai view lọc đúng lớp; chung hệ trục; không lặp mã thanh; legend theo view. |
| Chi tiết cột/dầm/móng | Mặt cắt, thép dọc/đai, vị trí thay đổi, kích thước, cao độ, mã đối chiếu | Thiết kế cấu kiện đã duyệt | Mã/tiết diện/thép khớp mặt bằng và bảng kê; thiếu dữ liệu phải báo `UNVERIFIED`. |

**Quy tắc phạm vi:** Một dự án chỉ yêu cầu các nhóm phù hợp với thiết kế thực tế. Mọi nhóm bị loại khỏi bộ tờ phải được ghi là `NOT_APPLICABLE` kèm lý do; nhóm cần thiết nhưng chưa có là `MISSING`, không được tính PASS.

## 3. Quy tắc trình bày theo vai trò

1. **Tổ chức từ tổng quát đến chi tiết:** mục lục → chỉ dẫn → móng → cột/vách → dầm/sàn → thép sàn → chi tiết. Mã tờ có thể cấu hình theo dự án. Danh mục và title block phải lấy từ cùng `SheetSetManifest`, không gõ hai lần.
2. **Chọn khổ và số view từ bbox đầy đủ:** đo hình học sau khi xoay, cộng khoảng cho nhãn, dim, bong bóng, tiêu đề, legend. A3 ngang và hai view xếp trên/dưới là một *layout mode*; A1 một view cũng hợp lệ. Quyết định bằng fit và độ đọc được, không bằng tỷ lệ hình học `W/L` đơn lẻ.
3. **Mỗi view là một đối tượng độc lập:** có `view_id`, `floor_id`, `discipline`, `scale`, góc xoay, bbox trên giấy, layer filter, tiêu đề và legend. Hai view có thể chia sẻ nguồn hình học nhưng không chia sẻ vị trí chữ/khung chú giải.
4. **Phân cấp kích thước:** `LOCAL/SETOUT`, `GRID_SPAN`, `OVERALL`; bong bóng trục là tầng chú thích ngoài cùng. Chỉ render local ở nơi cần định vị. DIMENSION phải là native và mang DimStyle theo scale. Không đoán kích thước từ ảnh PDF khi đã có dữ liệu thiết kế gốc.
5. **Khung tên/Key Plan:** tạo template riêng theo khổ và dự án. A3 dải phải khoảng 50–55 mm trong hồ sơ Cát Lái là *mốc tham khảo*, không phải chuẩn cứng. Key Plan cần nguồn vị trí được duyệt, không phát sinh hình giả.
6. **Text và plot:** chiều cao chữ kiểm theo mm trên giấy; màu và nét kiểm sau khi xuất DXF/PDF. Giữ Rule 12b/12d, nhưng không áp cỡ chữ point của Word/Excel (Rule 12e) trực tiếp cho CAD. Bản PDF tham chiếu không xác nhận tính đúng của màu layer hoặc CAD native vì không có DXF nguồn.

## 4. Đối chiếu ba tờ v5.0 của Agent

| Năng lực | KC-01 tổng mặt bằng | KC-02 cột/vách | KC-03 dầm/sàn | Tình trạng bộ tờ |
|---|---|---|---|---|
| Khung, trục, DIMENSION native, bảng kê | Có | Có | Có | Đạt ở cấp tờ; phải kiểm lại theo file phát hành. |
| Định vị ranh đất/đường | Có | Không thuộc phạm vi tờ | Không thuộc phạm vi tờ | Có trong tổng mặt bằng. |
| Cột/vách hatch, nhãn | Có cấu kiện | Có | Có cấu kiện tham chiếu | Không thay được chi tiết cột theo tầng. |
| Dầm phân nhịp/ô sàn | Không thuộc phạm vi tờ | Dầm tham chiếu mờ | Có | Có mặt bằng điển hình; thiếu mặt bằng các tầng nếu yêu cầu bộ TKTC. |
| Móng/cọc và chi tiết | Không | Không | Không | `MISSING` đối với dự án có móng/cọc. |
| Thép sàn TOP/BOTTOM thành hai view | Không | Không | Không có layer thép sàn trong DXF này | `MISSING` đối với dự án có sàn BTCT cần triển khai thép. |
| Chi tiết dầm/cột | Không | Không | Không | `MISSING` đối với bộ TKTC. |
| Mục lục, revision, Key Plan trong title block | Không có bộ mục lục | Không | Không | Chưa có sheet-set workflow. |
| A3 hai view/tờ | Không (A1) | Không (A1) | Không (A1) | Chưa có bằng chứng phát hành thực tế. |

## 5. Hợp đồng dữ liệu cần bổ sung

```text
SheetSetManifest: project_id, issue, revision, sheets[]
Sheet: sheet_id, code, title, paper, title_block_template, viewports[], notes[], source_refs[]
Viewport: view_id, view_kind, floor_id, scale, rotation, paper_bbox, model_transform,
          layer_filter, content_face [TOP|BOTTOM|BOTH|null], title, legend_ids[]
Element: stable_id, type, floor_range, geometry, material_ref, detail_ref, source_ref
RebarStrip: stable_id, floor_id, face [TOP|BOTTOM], direction, geometry, bar_mark,
            diameter, spacing, length, source_ref
```

**Thiếu input thì dừng đúng chỗ:** Không tự suy thép sàn, mác bê tông, chi tiết móng, số lượng cấu kiện từ PDF tham chiếu. Đưa trường thiếu vào `MISSING_INPUT` và chỉ xuất bản nháp có watermark/metadata rõ trạng thái.

## 6. Cổng nghiệm thu bộ tờ

- **G0 — Input:** nguồn thiết kế và phạm vi tờ được xác nhận; đánh dấu N/A có lý do.
- **G1 — Coverage:** sheet manifest bao phủ các nhóm cần thiết; tờ không trùng mã; mục lục/title block khớp.
- **G2 — Cross-sheet:** mã cấu kiện, cao độ, trục, tầng, trạng thái cột và chi tiết tham chiếu nhất quán.
- **G3 — View/layout:** bbox mọi view, text, dim, bubble, legend nằm trong canvas; không va chạm view/khung tên/sidebar.
- **G4 — Rebar:** TOP/BOTTOM lọc đúng lớp, không lặp/thiếu strip; số liệu khớp thiết kế.
- **G5 — DXF/PDF:** native entity, scale, plot readability, màu chữ, hatch, frame và checker profile theo phạm vi.
- **G6 — Regression:** bộ test hệ thống PASS; kết quả test không thay cho coverage hay kiểm toán kỹ thuật.

## 7. Lộ trình triển khai

P0: `SheetSetManifest`, template A3 dải phải, hai viewport thực và filter thép TOP/BOTTOM; thêm fixture KC.02/KC.16 kiểu Cát Lái bằng dữ liệu được phép dùng. P1: cross-sheet checker, Key Plan, legend theo viewport và semantic dim tiers. P2: các generator chi tiết móng/cột/dầm và phát hành mục lục tự động. Mỗi năng lực chỉ được ghi là *implemented* khi có DXF/PDF mẫu, kiểm entity và kiểm bản in; tên enum hoặc metadata đơn thuần chưa đủ.
