# DCE block, tên cấu kiện và biểu diễn bản vẽ

Ngày khảo sát: 2026-11-15. Nguồn trực tiếp: DXF KC-03 v5.0 trong thư mục bàn giao; `cad_plan_engine.py`; thư viện `C:/Dce Pro/Cad/Form 2.dxf`. Nguồn Steel: báo cáo khảo sát có bằng chứng `../../docs/DCE_STEEL_AND_INTERACTIVE_CAD_ANATOMY.md`; DWG Steel đã được đọc một phần, chưa xác nhận toàn bộ dynamic actions chạy được khi import.

## 1. Hiện trạng được xác minh

KC-03 chứa 108 INSERT: 58 `Dce_KhTenDam`, 30 `Dce_KhTenTruc`, 14 `DCE_Slab tag`, 2 `Dce_KhMatCat`, 2 `DCE_Drop mark`, 1 `DCE_Plan header 1`, 1 `Dce_CaoTrinh`. Vì vậy hệ thống **đã dùng** block thuộc tính cho nhãn; hạn chế là biểu diễn cấu kiện và ánh xạ dữ liệu còn rời rạc.

Đọc riêng `C:/Dce Pro/Cad/Form 2.dxf` xác nhận `Dce_CaoTrinh`, `TenCauKien`, `TK1`, `TK9` và ATTDEF; không tìm thấy các tên chính xác `Dce_KhTenDam`, `DCE_Slab tag`, `DCE_Drop mark` trong Form này dù chúng có trong DXF sản phẩm. Catalog phải phân biệt nguồn/template, không giả định mọi Form có cùng block. TK1 có các tag `KL,Lall,SKC,SL,sumL,DK,L,SH,TSL`; TK9 có thêm trường hình dạng như `L1,L2,M`. Ý nghĩa/đơn vị của từng tag cần xác minh qua mẫu dùng thật trước khi ánh xạ dữ liệu.

| Block đang dùng | ATTDEF đọc từ DXF | Cách engine điền hiện tại | Vấn đề |
|---|---|---|---|
| `Dce_KhTenDam` | `TENDAM`, `TL` | Chuỗi `D1A (400x800)`, TL=`1/100` | Gộp mã và kích thước vào một chuỗi; scale gán cứng; một tên được lặp cho nhiều nhịp nhưng không có định danh nhịp trong nhãn. |
| `DCE_Slab tag` | `200` | Luôn `'150'` | Không lấy chiều dày từ ô sàn; tag tên `200` chỉ là tên thuộc tính của thư viện, không phải giá trị thiết kế. |
| `DCE_Drop mark` | `50` | Lấy `s['drop']` | Có ánh xạ nhưng hình chữ nhật vùng hạ cốt bị cố định 3000×3500; chưa bám biên ô thực. |
| `Dce_CaoTrinh` | `CT` | Luôn `+12.600` | Không lấy cao độ của tầng/ô sàn. |
| `Dce_KhMatCat` | `TL`, `TENMATCAT` | `1-1`, `2-2`, TL=`1/20` | Chưa chứng minh liên kết tới tờ/mặt cắt đích; dễ tạo ký hiệu có tên nhưng không có chi tiết tương ứng. |
| `TenCauKien` | `SOCAUKIEN`, `TENCAUKIEN` | Tên và kích thước trong nhánh KC-02 | Phải xác minh ý nghĩa trường từ block mẫu; tên tag `SOCAUKIEN` không tự chứng minh đây là trường kích thước. |

`_add_beam_tag` đặt block scale 100, ghi TL 1/100; các dầm X/Y được đặt lệch 600 mm hoặc 500 mm, dầm Y chưa dùng `rot_deg` tại lời gọi. Ngoại lệ bất kỳ bị đổi thành TEXT rời mà không báo mất block. `render_columns_walls_supports` dựng polyline+hatch; `_draw_beam_double_line` dựng hai LINE. Đây là đường xuất hình học tĩnh, chưa tạo đối tượng cấu kiện có dữ liệu để sửa/đếm/liên kết.

## 2. Mô hình tên dầm: tách định danh, nhóm thiết kế và chữ hiển thị

Không dùng chuỗi tên trên giấy làm khóa dữ liệu duy nhất. Mỗi dầm cần:

- `element_id`: định danh bất biến của cấu kiện; không đổi khi kỹ sư đổi nhãn.
- `floor_id`, `grid_start`, `grid_end`, `span_id`: vị trí và phạm vi nhịp.
- `beam_mark`: tên xuất bản như D1, D1A, DG1, BMX.1; quy ước tiền tố do dự án cấu hình, không suy công năng chỉ từ chữ cái.
- `design_group_id`: nhóm cấu kiện cùng chi tiết/thép được kỹ sư cho phép dùng chung. Cùng kích thước b×h chưa đủ để gom nhóm.
- `section_ref`, `rebar_detail_ref`, `sheet_ref`: tham chiếu tiết diện, thép và tờ chi tiết.
- `display_text`: được sinh từ các trường trên theo template; không parse ngược chuỗi để làm nguồn thiết kế.

Ví dụ một dầm liên tục mang mã D1 qua ba nhịp có thể có ba `span_id` và một tên nhóm D1. Mỗi nhịp vẫn cần hình học và thép riêng; tên D1 lặp lại không tự động là lỗi trùng. Nếu hai dầm cùng mã nhưng khác chi tiết mà không có phạm vi tầng/nhóm giải thích, checker phải báo xung đột. Mã dầm trên mặt bằng, mặt cắt và bảng kê lấy cùng một nguồn.

## 3. Tag ô sàn và trạng thái cấu kiện

Ô sàn cần `panel_id`, `floor_id`, biên đa giác, chiều dày, cao độ trên sàn kết cấu, trạng thái dốc/hạ cốt và tập lỗ mở. Tag chính hiển thị mã ô và chiều dày; cao độ dùng block cao độ phù hợp. Hạ cốt phải nêu rõ độ chênh so với mốc nào; không suy từ tên block `50`. Hai view thép trên/dưới dùng chung panel_id nhưng filter thép riêng.

Cột/vách cần mã, tiết diện, tầng bắt đầu/kết thúc, trạng thái dừng/đi tiếp và tham chiếu chi tiết. Hình học, hatch bê tông, nhãn và ký hiệu trạng thái là các thành phần cùng một cấu kiện. Hatch vẫn cần cho mặt cắt bê tông; block thuộc tính bổ sung định danh và khả năng sửa dữ liệu, không tự thay mọi đường bao hoặc hatch.

## 4. Nguyên tắc sử dụng thư viện DCE/DCE Steel

**Bắt buộc tra catalog trước khi tự dựng ký hiệu đã có thư viện.** Catalog ghi đường dẫn nguồn, hash, tên block, basepoint, đơn vị, bbox, ATTDEF, style/layer phụ thuộc, trạng thái dynamic và mức hỗ trợ import. Import block cùng dependencies; không ghi đè định nghĩa trùng tên khác hash mà không xử lý xung đột. Bản nguồn thư viện giữ nguyên; thử nghiệm trên bản sao.

Phân biệt ba loại: block nhãn, block hình học tham số và block dòng thống kê. `Dce_KhTenDam` là nhãn, không đủ thay toàn bộ hình dầm. `TK1/TK9` là dòng thống kê thanh, không phải cấu kiện. Thư viện Steel được khảo sát có các họ `Dce_IWeb`, `Dce_IFlange`, `Dce_BeamI1`, `Dce_PlanI`, `DCE_SectHop`, `DCE_SectOng`, `Dce_Bolt`, `Dce_AnchorL/J`; cần đối chiếu chính xác từng Form trước khi sử dụng.

Không kéo giãn một block tiết diện thép bằng scale X/Y để giả lập mọi profile: cách đó làm sai bề dày bụng/cánh và bán kính. Với Dynamic Block, chỉ công bố hỗ trợ khi backend CAD thực sự gán được tham số và đánh giá lại hình học. Headless ezdxf có thể nhập block/ATTRIB nhưng chưa đủ chứng minh chạy dynamic actions hoặc lệnh DCE thương mại. Khi không hỗ trợ, báo `UNSUPPORTED_BLOCK_BEHAVIOR`; có thể xuất hình học tĩnh từ dữ liệu tiết diện được duyệt và ghi rõ giới hạn.

Không giả mạo XData của DCE để tuyên bố DCE sửa được cấu kiện. Agent dùng app-id riêng cùng stable element_id; chỉ thêm adapter tương thích DCE sau khi đã kiểm schema và thao tác sửa thật. Báo cáo Steel trước đây cho thấy payload XData có dạng chuỗi; tên block/ATTDEF không thay thế payload nghiệp vụ này.

## 5. Quy tắc đặt nhãn theo hình học

1. Tính vị trí theo đường tâm/biên cấu kiện trong world coordinates rồi chuyển qua transform của view; luôn bù basepoint thư viện.
2. Ưu tiên tên dầm tại khoảng trống giữa nhịp; hướng chữ theo quy ước dự án, đọc được từ dưới/phải. Thử các vị trí song song dầm và hai phía dầm bằng bbox chữ thực; không dùng offset 600 mm cố định cho mọi tỷ lệ.
3. Tránh biên cột/vách, vùng lỗ mở, nhãn ô sàn, thép, dim và ký hiệu mặt cắt. Nếu không còn chỗ, đưa nhãn ra ngoài với leader có neo vào đúng cấu kiện. Không chuyển nhãn sang ô bên cạnh chỉ vì còn chỗ.
4. Giữ cao độ/thickness trong ô sàn chứa điểm neo. Các panel nhỏ hoặc méo dùng leader; không đặt tag giữa bbox nếu điểm đó nằm ngoài đa giác.
5. Kích thước chữ, khoảng hở và scale block lấy từ thông số giấy/view. TL trong block phải khớp tỷ lệ view hoặc bị ẩn theo cấu hình block, không lặp tỷ lệ mặc định cạnh mọi dầm.
6. Lưu offset chỉnh tay của kỹ sư theo element_id/view_id; khi tái sinh, kiểm va chạm lại và bảo toàn chỉnh tay còn hợp lệ.

## 6. Nâng cấp cụ thể cho Agent

| Ưu tiên | Thay đổi | Điều kiện nghiệm thu |
|---|---|---|
| P0 | `DceBlockCatalog` quét DXF nguồn và ghi block/ATTDEF/basepoint/hash; Steel DWG qua adapter CAD được hỗ trợ | Catalog có nguồn và mức tin cậy; không coi kết quả đọc DWG một phần là đầy đủ. |
| P0 | `BlockBinding` ánh xạ semantic field → tag thực, ví dụ `slab.thickness_mm → '200'`, `level → CT` | Giá trị ATTRIB đọc lại đúng input; thiếu field/tag phải báo lỗi, không nuốt exception thành TEXT. |
| P0 | Bỏ scale 100, TL 1/100, thickness 150, level +12.600 và vùng drop cố định trong nhánh xuất tổng quát | Fixture thay scale/tầng/thickness làm đúng entity, không chỉ metadata. |
| P0 | `ElementRegistry` nối hình học, tag, hatch, schedule, detail bằng element_id | Đổi tiết diện/tên cập nhật đúng thành phần liên quan; không đổi cấu kiện khác. |
| P1 | Tag placement theo bbox, hướng dầm, polygon sàn, leader và view | Không tag nằm sai ô/nhịp; tồn tại liên kết tag→element; giữ chỉnh tay. |
| P1 | Profile adapter Steel: member/section/bolt/baseplate/bracing | Profile và số lượng bu lông đúng input; đúng đơn vị; dynamic behavior được kiểm trong CAD nếu sử dụng. |
| P1 | Cross-sheet mark checker | Mọi mặt cắt/detail_ref có đích; mã trong mặt bằng và bảng kê đồng nhất; nhóm cùng tên không khác thiết kế ngoài ngoại lệ. |

## 7. Kiểm thử bắt buộc trước khi tuyên bố đã tích hợp thư viện

Fixture phải bao gồm dầm X/Y/xiên, dầm nhiều nhịp cùng mark, hai dầm cùng tiết diện khác thép, sàn có lỗ/hạ cốt, cột dừng, và một cấu kiện Steel thực từ catalog. Kiểm sau save/reopen: INSERT còn đúng block, ATTRIB đúng tag và giá trị, block transform đúng, bbox chữ không va chạm, mối liên kết registry còn đầy đủ. Kiểm sửa tên/tiết diện/tầng làm đổi đúng tag/bảng kê/detail. Bản render chỉ chứng minh cách trình bày; khả năng sửa bằng DCE phải được kiểm riêng trong phần mềm CAD tương thích.
