# Phân công nâng cấp CAD DCE v6

Mã: `09_DCE_CAD_BLOCK_SEMANTICS_V6`. Người giao: USER/CODEX. Mục tiêu: triển khai và kiểm chứng các nâng cấp đã phân tích, không dừng ở viết tài liệu. Chưa có agent nào được coi là đã nhận ca cho tới khi claim bus thành công.

## Điều phối và quyền sở hữu

Bus hiện có một `current_holder`: thực hiện tuần tự `GEMINI G1 → CLAUDE C1 → GEMINI G2 → CLAUDE C2 → CODEX A1`. Các brief bên dưới là nhiệm vụ đã giao; không tự claim thay người nhận. Agent giữ ca ghi báo cáo pha và bàn giao người tiếp theo qua `sync_bus.auto_handoff`, luôn truyền `project_code=09_DCE_CAD_BLOCK_SEMANTICS_V6`, đường dẫn kế hoạch này và mã pha. Không xóa/ghi đè kế hoạch khi tạo memo tự động. Nếu bị chặn, ghi nguyên nhân và bằng chứng, không đánh dấu nghiệm thu đạt.

| Người | Vai trò | Phạm vi ghi được |
|---|---|---|
| GEMINI | Kiến trúc dữ liệu, thư viện DCE/Steel, adapter | Các module mới `cad_integration/dce_block_catalog.py`, `dce_block_binding.py`, `cad_element_registry.py`, `dce_steel_adapter.py`; schema/fixtures/tests tương ứng; `memory/audits/cad_v6/gemini/` |
| CLAUDE | Renderer, tag placement, viewport, bộ tờ, tích hợp | `cad_integration/cad_plan_engine.py`, module mới `cad_tag_placement.py`, `cad_sheet_set.py`; tests tích hợp; `memory/audits/cad_v6/claude/` |
| CODEX | Kiểm định độc lập, regression và quyết nghị | `memory/audits/cad_v6/codex/`; biên bản nghiệm thu và cập nhật tài liệu kỹ năng cuối |

Các đường dẫn `cad_integration/` ở bảng thuộc `.agents/skills/Technical_Illustrator/`; tests ở `.agents/tests/`. Tệp engine chỉ CLAUDE sửa; module thư viện chỉ GEMINI sửa. Cần đổi interface thì ghi đề xuất trong báo cáo pha và bàn giao chủ sở hữu; không tự sửa tệp của bên kia. Thư viện `C:/Dce Pro` chỉ đọc, không sửa nguồn.

## Dữ liệu phải đọc

1. `.agents/skills/Technical_Illustrator/DCE_BLOCK_TAG_GUIDE.md`.
2. `.agents/skills/Technical_Illustrator/STRUCTURAL_SHEET_SET_GUIDE.md`.
3. `.agents/docs/DCE_STEEL_AND_INTERACTIVE_CAD_ANATOMY.md` (giới hạn đọc DWG/dynamic).
4. Ba DXF `KC-0*_v50_DA_SUA_KHUNG.dxf` trong `01_Projects/03_Sprint2_KetQua_NeChu_CAD/` và PDF Cát Lái tại `01_Projects/08_NHA_PHO_Q2/01_Input_CAD_PDF/`.

## GEMINI G1 — Nền dữ liệu và block

Trạng thái ban đầu: READY; người nhận bus đầu tiên: GEMINI.

- Kiểm kê block DCE từ các DXF nguồn: tên, ATTDEF, basepoint, units, geometry bbox, style/layer phụ thuộc, source hash. Ghi riêng độ tin cậy của Steel DWG và các tính năng chưa đọc được.
- Xây API catalog/binding nhập block và dependencies, xử lý trùng tên khác định nghĩa; semantic field ánh xạ đúng tag thật. Không đoán nghĩa `SOCAUKIEN`, `200`, `50` chỉ qua tên.
- Xây registry với element_id ổn định, beam_mark, span_id, floor_id, design_group_id, geometry_refs, tag_refs, schedule_refs và detail_ref. Không dùng tên hiển thị làm khóa duy nhất.
- Cung cấp interface và fixture cho CLAUDE: danh mục field/units, load/import/bind/register/update; mẫu dầm cùng mark nhiều nhịp, sàn hạ cốt, cột dừng. Giá trị fixture phải được ghi là dữ liệu thử, không phải thiết kế thi công.
- Kiểm thử thiếu tag, source conflict, bù basepoint, save/reopen ATTRIB, bảo toàn element_id khi đổi tên; xuất `G1_RESULT.md`, catalog JSON và test log trong vùng GEMINI.

Điều kiện bàn giao G1: modules chạy được và import được; fixture đủ cho C1; có bằng chứng đọc lại DXF. Bàn giao CLAUDE C1, không đánh dấu toàn dự án COMPLETED.

## CLAUDE C1 — Tích hợp sản phẩm KC-03 và đặt nhãn

Phụ thuộc G1 PASS. Đọc interface của GEMINI trước khi sửa renderer.

- Tích hợp binding/registry; loại gán cứng scale100/TL1:100, slab150, level+12.600, drop3000×3500 khỏi đường xuất tổng quát. Giá trị demo chỉ được tồn tại trong fixture/demo khai báo rõ.
- Thay fallback `except Exception → TEXT` bằng lỗi rõ/diagnostic; bản xuất suy giảm phải được ghi trạng thái và không nhận PASS.
- Tag dầm theo hướng và bbox chữ; tag sàn nằm trong đa giác ô và ngoài lỗ; có leader khi thiếu chỗ. Offset theo mm giấy, giữ chỉnh tay theo element_id/view_id.
- Tạo sản phẩm đối chứng mới trong vùng CLAUDE, không ghi đè ba DXF v5.0. Có DXF/PDF hoặc preview xuất thực và log nguồn dữ liệu.
- Fixture bắt buộc: dầm X/Y/xiên; nhiều nhịp cùng mark; cùng tiết diện khác thép; sàn có lỗ/hạ cốt; thay tên/tiết diện/scale và đọc lại entity.

Điều kiện bàn giao C1: ATTRIB khớp input, không tag sai ô/nhịp, không mất liên kết cấu kiện, hình học/thống kê liên quan cập nhật đúng. Xuất `C1_RESULT.md`, bàn giao GEMINI G2.

## GEMINI G2 — Adapter Steel và dữ liệu xuyên tờ

Phụ thuộc C1 đã cung cấp renderer fixture. Không sửa engine.

- Chọn ít nhất một họ tiết diện và một họ bu lông/bản mã từ catalog thực để tạo adapter; ghi rõ backend và năng lực hỗ trợ.
- Không kéo scale X/Y để giả lập tiết diện khác. Không tự ghi XData thương mại hoặc tuyên bố tương thích chỉnh sửa DCE khi chưa thử runtime.
- Kiểm chuẩn dữ liệu semantic/registry cho sheet set: mark theo tầng, group, detail target, quan hệ geometry/tag/schedule.
- Thử save/reopen block/attributes và hình học Steel. Nếu dynamic evaluation không có backend, ghi `UNSUPPORTED_BLOCK_BEHAVIOR`, giao static representation được khai báo rõ; không ghi dynamic PASS.
- Xuất `G2_RESULT.md` và fixture Steel, bàn giao CLAUDE C2.

## CLAUDE C2 — Bộ tờ và tích hợp cuối

Phụ thuộc G2; sử dụng module registry/binding đã chốt.

- Xây `SheetSetManifest`, template A3 dải phải, hai viewport thực có transform/scale/filter riêng; TOP/BOTTOM không trộn thép.
- Mục lục, title block, mã cấu kiện, bảng kê và detail_ref cùng nguồn; kiểm đích mặt cắt tồn tại.
- Tích hợp adapter Steel; kiểm không làm hỏng KC-01/02/03, người dùng giữ được chỉnh tay.
- Bổ sung test tích hợp vào runner hiện hữu, giữ đủ 31 suite cũ và chạy toàn bộ suite sau nâng cấp. Không yêu cầu tổng suite luôn bằng 31 nếu đã thêm suite mới.
- Xuất `C2_RESULT.md`, DXF và PDF/preview cho KC-03 cải tiến, sheet TOP/BOTTOM hai view và fixture Steel. Kèm số liệu collision, entity counts, hashes, test logs và giới hạn.

Bàn giao CODEX A1 để nghiệm thu độc lập. Không tự phê duyệt toàn sản phẩm.

## CODEX A1 — Nghiệm thu độc lập

Đọc DXF thực và render: đúng INSERT/ATTRIB, đúng giá trị thiết kế thử, bbox/leader, tag→element và liên kết xuyên tờ. Thử đổi tên dầm, tiết diện, chiều dày sàn, cao độ, tỷ lệ; kiểm đúng phần cập nhật và giữ chỉnh tay. Chạy compliance đúng profile với sidecar bound hash và full regression. Tách rõ static/native/dynamic capability.

Kết quả cuối phải có ma trận PASS/FAIL/UNVERIFIED theo từng năng lực. Chỉ kết thúc nâng cấp khi phạm vi đã cam kết đạt, hoặc ghi rõ phần còn bị chặn với người chịu trách nhiệm; không coi bus COMPLETED của một pha là phê duyệt toàn dự án.
