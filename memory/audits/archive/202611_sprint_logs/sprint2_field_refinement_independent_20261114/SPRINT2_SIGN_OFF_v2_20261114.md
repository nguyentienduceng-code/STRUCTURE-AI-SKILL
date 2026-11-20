# Biên bản hoàn thiện Sprint 2 — F1–F5, MCP và SKILL

Ngày: 14/11/2026. Thực hiện: CODEX — sửa mã nguồn và kiểm chứng tự động.

**Kết luận: hoàn thành sửa lỗi phần mềm và tích hợp trong phạm vi Task.** F1–F4 đạt lại các phản ví dụ gốc. F5 đã được sửa ở API, CLI và MCP. Full regression đạt **30/30 suites PASS**, thời gian **115,40 giây**. Hai bản vẽ thực chiến giữ nguyên sản phẩm, không có va chạm và ảnh khớp 0 pixel diff.

Đây là biên bản hoàn thiện sau sửa của CODEX, không tuyên bố có một người kiểm toán độc lập khác đã phê duyệt mã mới. Việc xác nhận tính toán chi tiết kết cấu cần đầu vào tương ứng. Không tự xác nhận đủ 20 cổng khi thiếu bản vẽ chi tiết. Không commit hoặc push GitHub.

## 1. F5 đã được giải quyết như thế nào

Lỗi cũ xuất hiện khi API lấy trạng thái physical audit rồi bỏ qua kết quả của các cổng ngữ nghĩa. Kết quả tổng có thể là PASS trong khi chỉ 5/20 cổng đạt. Bốn cổng chi tiết còn tự báo PASS dù không có bản vẽ dầm, cột hoặc vách đầu vào.

API mới sử dụng schema 2.0 và ba phạm vi rõ ràng. `physical` chỉ kiểm tra DXF vật lý. `plan` kiểm tra 16 cổng mặt bằng và ghi bốn cổng chi tiết là NOT_APPLICABLE. `full` là mặc định, yêu cầu đủ 20 cổng cùng bằng chứng bản vẽ chi tiết. Mỗi phạm vi có trạng thái và số lượng cổng riêng.

Cổng bắt buộc FAIL làm kết quả tổng FAIL. Thiếu bằng chứng làm cổng UNVERIFIED và trạng thái tổng NEEDS_REVIEW. Các thông tin này được đưa vào `issues`; không còn bị bỏ khỏi kết quả. Chỉ full PASS đủ 20 cổng mới có `full_compliance_verified=true`. Một physical PASS không được diễn giải thành nghiệm thu toàn bộ hồ sơ.

Metadata không còn được suy đoán từ tên layer rồi tự gán mode và scale. Sidecar phải có `provenance.dxf_sha256` khớp DXF. Sửa DXF làm bằng chứng cũ mất hiệu lực. Sidecar sai JSON, thiếu trường hoặc sai hash được báo rõ. CLI và MCP gọi chung API để không tạo hai cách hiểu trạng thái.

Hash xác nhận metadata gắn đúng phiên bản file, không chứng minh mọi khai báo đều đúng. Vì vậy checker còn đối chiếu trực tiếp DIMENSION, DimStyle, ATTDEF, hatch block cột và lineweight. Test xóa DIMENSION rồi cập nhật lại hash vẫn bị FAIL tại G8.06. Metadata không được dùng để che lỗi hình học native.

## 2. Sửa đầu ra generator v4.7

Khi kiểm tra API mới, CODEX phát hiện nhánh generator V4 tự khai báo có DIMENSION, thuộc tính và solid hatch, nhưng một số phần chỉ được vẽ bằng primitive. File raw DXF còn cần hiệu chỉnh cấu trúc khi đọc lại. Việc chỉ sửa dòng trạng thái API sẽ giữ lại nguyên nhân gây kết quả thiếu tin cậy này.

Nhánh V4.7.1 hiện tạo DIMENSION, ATTDEF/ATTRIB và HATCH bằng ezdxf. Dimension dùng phép đo thật và không gõ đè số bằng text rời. Nhãn gắn vào block bằng thuộc tính. Cột có hatch xám và đường bao; vách có hatch khi dữ liệu nguồn yêu cầu. Các đường/text dimension thay thế cũ không còn được xuất cùng dimension native.

Sau khi tạo entity, generator sửa cấu trúc của tài liệu đang sinh, lưu DXF rồi mở lại. Chỉ khi lần mở lại không có lỗi hoặc audit fixes mới tạo sidecar gắn hash. Quá trình này chỉ tác động tới file mới sinh, không sửa các sản phẩm người dùng đã bàn giao.

| Chế độ | Native DIMENSION | Cổng mặt bằng đạt | Cổng chi tiết ngoài phạm vi | Physical audit |
|---|---:|---:|---:|---|
| COLUMN_WALL_SETOUT | 161 | 16/16 | 4 | PASS, 0 fixes |
| BEAM_SLAB_FRAMING | 14 | 16/16 | 4 | PASS, 0 fixes |
| SLAB_REBAR_PLAN | 14 | 16/16 | 4 | PASS, 0 fixes |
| FOUNDATION_LAYOUT | 50 | 16/16 | 4 | PASS, 0 fixes |

Bốn bộ DXF và sidecar mới được lưu riêng tại [generated_native](completion_f5_20261114/generated_native/). Chúng là mẫu kiểm chứng generator. Khi yêu cầu profile full cho các bộ này, hệ thống trả NEEDS_REVIEW vì chưa có chi tiết dầm/cột/vách; đây là hành vi đúng của hợp đồng mới.

## 3. Kiểm tra MCP và SKILL liên quan

Đã kiểm tra đủ **8 tools** của server DCE CAD và đối chiếu với cấu hình mẫu. Một phiên MCP stdio thật đã thực hiện initialize, list_tools, sinh DXF và validate. Suite guard còn kiểm tra vòng render-preview/consume qua stdio với biến TEMP trỏ về Drive. Kết quả xác nhận hoạt động của server và schema, không chỉ import được module Python.

`render_cad_plan` hiện trả DXF UUID trong scratch local. Đường dẫn caller truyền chỉ là gợi ý; caller phải đọc `output_dxf` thực tế. Sheet không hợp lệ hoặc đường dẫn model/template/PDF không tồn tại được từ chối. Dry-run và lần ghi dùng cùng hàm dựng bản vẽ. `pdf_path` được giữ đúng vai trò PDF đầu vào đọc vector, không biến thành nơi xuất PDF.

Log của generator được chuyển sang stderr để không làm hỏng stdout JSON-RPC. Module import thất bại được loại khỏi cache để lần gọi sau không dùng module khởi tạo dở. `edit_entity` không còn tự dùng revision mới nhất khi caller bỏ qua `expected_revision`; commit yêu cầu handle và revision rõ ràng. Các kiểm tra revision cũ và bảo toàn nguồn vẫn đạt.

`resolve_cad_collisions` tiếp tục ghi output local và giữ nguyên nguồn. Preview dùng token một lần, có consume/release và cleanup. `convert_to_dwg` được kiểm tra nhánh UNAVAILABLE khi không có ODA; không cài đặt hoặc chạy installer. Máy này không có executable ODA tại đường dẫn cấu hình mặc định, nên không tuyên bố đã kiểm thử chuyển DWG thật.

Các cấu hình client Codex và Claude Desktop được đọc ở mức tên server liên quan, không xuất thông tin bí mật. Chưa có đăng ký DCE CAD trong hai cấu hình được tìm thấy; cấu hình Antigravity tại vị trí kiểm tra không tồn tại. Không tự thay cấu hình toàn cục của client. Server đã được kiểm chứng bằng subprocess stdio, cấu hình mẫu local đã cập nhật đầy đủ để đăng ký khi triển khai client.

`SKILL_VERIFY` đã lên 3.4.0; `Technical_Illustrator` lên 1.5.0. SKILL_INDEX, changelog, RFC và tài liệu Virtual Drive Guard đã được đồng bộ. Hợp đồng dùng chung nằm tại [MCP_DCE_CAD_CONTRACT.md](../../../docs/MCP_DCE_CAD_CONTRACT.md). Quy trình Bus tiếp tục dùng SKILL_DUAL_AGENT_BRIDGE và khóa FileLock local.

## 4. F1–F4 và regression

Các phản ví dụ gốc đã chạy lại: ca thiếu source không còn leader ngắn; lỗi tạo DCE_Leader trả NEEDS_REVIEW và không tạo leader; dry-run không thêm layer; layer sai màu được chuẩn hóa về 250. Các trường hợp này hiện có test trong Suite 30, thay vì chỉ nằm trong script audit rời.

Đã bổ sung kiểm tra ranh giới 99,9/100/100,1 mm sau khi rút ngắn leader. Mỗi đoạn LINE trong dogleg cũng phải đạt ngưỡng tối thiểu khi chọn route. Khi tạo layer thất bại, APPID không được thêm trước khi quyết định commit. Test leader ban đầu đã được siết về DCE_Leader, không còn chấp nhận fallback DCE_Name.

| Bộ kiểm tra | Kết quả |
|---|---|
| Full regression | 30/30 suites PASS, 115,4019317 giây |
| Suite 18 — compliance và Zero White Text | 25 tests PASS |
| Suite 28 — Virtual Drive Guard và MCP preview | 18 tests PASS |
| Suite 29 — MCP DCE CAD | 12 tests PASS |
| Suite 30 — collision solver | 35 tests PASS |
| Bốn probes audit gốc | 4/4 PASS |

Các test physical trước đây được chuyển sang chọn `profile=physical` rõ ràng, giữ nguyên assertion hình học. Đồng thời thêm test mặc định full phải trả NEEDS_REVIEW khi thiếu metadata. Như vậy không hạ cổng full để giữ số lượng suite PASS. Test failure injection, CLI/API parity, stale hash và native damage bảo vệ trực tiếp nguyên nhân của F5.

## 5. Sản phẩm thực chiến và hiệu năng

| Chỉ tiêu | KC-01 | KC-02 |
|---|---:|---:|
| Va chạm còn lại | 0 | 0 |
| Xung đột leader | 0 | 0 |
| Số leader | 25 | 8 |
| Độ dài min–max, mm | 264,0935–689,4048 | 157,6603–704,7565 |
| Micro-leader dưới 100 mm | 0 | 0 |
| Leader sai layer/màu | 0 | 0 |
| Pixel khác ảnh render lại | 0 | 0 |
| Benchmark lớn nhất trong 3 lượt | 0,8946 giây | 1,1288 giây |

Benchmark tính cả đọc baseline, giải va chạm và lưu bản DXF mới local. Cả sáu lượt đều dưới 2 giây. Ảnh được so sánh RGB với crop, DPI và layout giống vòng trước. Kết quả pixel không được dùng thay phép đo vector toàn bản vẽ.

Toàn bộ **17 tệp** trong thư mục sản phẩm giữ nguyên SHA256 và mtime so với đầu ca. Các file mới sinh được giữ ở scratch hoặc thư mục bằng chứng riêng. Hai DXF cũ vẫn đạt physical audit, nhưng không có sidecar chứng minh các cổng ngữ nghĩa nên profile full trả NEEDS_REVIEW đúng thiết kế.

Định nghĩa khoảng cách 100 mm vẫn phân biệt đoạn leader/envelope có padding với khoảng cách biên chữ chưa padding. Biên bản không đổi kết luận lịch sử về 33 nhãn thành một công bố hình học khác. Không sửa sản phẩm cũ chỉ để làm thay đổi con số đã nghiệm thu.

## 6. Bằng chứng và bàn giao

Bằng chứng vòng hoàn thiện nằm tại [completion_f5_20261114](completion_f5_20261114/): `full_tests/`, `product_verification.json`, `native_generator_checks.json`, `preview_comparison.json`, `adversarial_probes.json`, `product_integrity.json`, `verdict.json` và manifest. `before/` giữ bản nguồn trước sửa. Các lần test mục tiêu thất bại trong quá trình phát triển được giữ lại; `full_tests/` là lần nghiệm thu cuối.

Lỗi thử nghiệm ban đầu gồm tương thích tên field SDK MCP 2.x và thao tác ghi lại DXF raw. Đã sửa harness tương thích SDK và sửa generator native. Các lần chạy sau đã đạt, không loại bỏ test thất bại để làm đẹp thống kê. Thay đổi sau lần full PASS chỉ là đồng bộ mô tả tài liệu/comment, không thay thuật toán đã kiểm tra.

Kết luận phần mềm: **F5 CLOSED; các MCP/SKILL liên quan đã đồng bộ và kiểm chứng; Task COMPLETE ở máy cục bộ.** Full detail certification vẫn phụ thuộc hồ sơ chi tiết thực tế. Không phát hành một chứng nhận thiếu dữ liệu để thay cho việc hoàn thành sửa lỗi phần mềm.

| Trách nhiệm | Chủ thể | Kết quả |
|---|---|---|
| Sửa lỗi và kiểm chứng tự động | CODEX | Hoàn thành trong phạm vi biên bản |
| Đề xuất nghiệm thu phần mềm | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký hồ sơ thiết kế | Kết quả phần mềm và phạm vi đã ghi rõ |
| Phê duyệt triển khai, phát hành/GitHub | User — Kỹ sư Trưởng | Chưa thực hiện push |
