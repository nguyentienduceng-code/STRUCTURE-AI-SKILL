# Biên bản nghiệm thu Virtual Drive Guard — v1 — 2026-11-14

- Dự án: `01_ARCHITECTURE_MCP_DCE_CAD_ADAPTER`.
- Ca trực: GEMINI bàn giao, CODEX nhận và triển khai.
- Phạm vi: lớp I/O tạm của MCP CAD; không sửa engine CAD hay logic tiêu chuẩn.
- Kết luận: **PASS cho cơ chế cô lập I/O tạm trong phạm vi adapter**.

## Đối chiếu tiêu chí bàn giao

| Tiêu chí | Bằng chứng | Kết quả |
| --- | --- | --- |
| PNG preview/cache/scratch chỉ ghi trên C:/D: local | Guard kiểm tra ổ fixed NTFS/ReFS, đường dẫn sau resolve, junction, UNC và thư mục cloud; TEMP/TMP/MPLCONFIGDIR được chuyển local trước import thư viện | PASS |
| Loại bỏ nguồn Google Drive lock do scratch MCP CAD | Preview được cấp UUID local kể cả caller truyền G:; phiên edit trên Drive ánh xạ sang local; không ghi PNG cạnh DXF | PASS trong phạm vi scratch được quản lý |
| Auto-cleanup preview | MCP consume trả nội dung ảnh rồi giải phóng file; Python context manager dọn trong finally; release cho client đọc trực tiếp; TTL 24 giờ khi cấp ảnh mới | PASS |
| Suite 18 đạt 14/14 | `cad_guard/suite_18.log`: Ran 14 tests, OK, exit_code=0 | PASS |
| Fast Tier đạt 17/17 suite | `fast/timings.json`: selected_suites=17, all_passed=true | PASS |
| Có biên bản kiểm toán | File này, log từng suite, timings và `evidence.json` | PASS |

## Kết quả chạy kiểm chứng

| Nhóm | Số lượng | Thời gian wall-clock của runner |
| --- | --- | --- |
| Fast Tier | 17/17 suite | 11.69 giây |
| Suite 18 CAD Compliance | 14/14 test | 10.77 giây |
| Suite 28 Virtual Drive Guard | 18/18 test | 5.46 giây |

Runner vẫn giữ nhãn lịch sử “9 tests” cho Suite 18; log unittest thực tế xác
nhận 14 test. Không thay bộ test CAD đang có hoặc sửa assertion để lấy PASS.
Suite 28 được đăng ký vào runner; danh sách Fast Tier vẫn gồm 17 suite cũ.

Suite 28 chạy render PNG thật toàn layout và crop; kiểm tra byte signature PNG;
DXF nguồn giữ nguyên byte; ảnh không ghi đè đường dẫn caller yêu cầu. Phiên sửa
được tạo trên local, mở lại bằng alias hoặc đường dẫn thực, giữ revision lock.
Test MCP thực khởi động tiến trình server, initialize, list_tools, render_preview
và consume_preview qua stdio. Response chứa ImageContent hợp lệ và file PNG
không còn tồn tại sau consume. TEMP và MPLCONFIGDIR cố tình trỏ G: được chuyển
về root local trước khi server render.

Các tình huống lỗi gồm UNC/device path/traversal/ADS, junction thật, volume chưa
xác minh, không có fallback an toàn, renderer ghi dở rồi lỗi, Vision ném exception,
khóa local thoáng qua hoặc kéo dài, token cleanup không hợp lệ và file không do
guard sở hữu. Có 16 lượt cấp preview đồng thời không trùng đường dẫn. TTL không
xóa lượt đang render hay lịch sử phiên CAD. Figure được đóng khi render lỗi.

## Thay đổi vận hành

- `out_png` không còn là vị trí ghi trực tiếp; caller đọc `output_png` thực tế.
- Luồng MCP khuyến nghị: `render_preview` → `consume_preview`. Ảnh trong response
  vẫn dùng được sau khi PNG local đã bị xóa.
- Client đọc file trực tiếp gọi `release_preview` sau khi xem xong; CLI dùng
  `--release <preview_id>`; Python dùng `preview_for_vision`.
- Phiên edit trả `session_dir` và `revision`; nhập source tạo bản sao local nên
  `file_written` phản ánh đúng thao tác này, kể cả chưa commit MOVE.
- Hướng dẫn: `.agents/docs/DCE_VIRTUAL_DRIVE_GUARD.md`.

## Phạm vi và giới hạn xác nhận

“Triệt tiêu Google Drive lock” được xác nhận cho **việc ghi scratch của adapter**,
không phải cam kết không có mọi WinError 32 trên máy. DXF đầu vào/đầu ra lâu dài
trên Drive, ứng dụng khác giữ file local và cấu hình sync tùy chỉnh ngoài các root
đã nhận diện vẫn có thể phát sinh lỗi. Guard không phải sandbox hệ điều hành và
không chống tiến trình có quyền thay mount/junction trong khoảng kiểm tra–ghi.
Ổ fixed NTFS/ReFS được xác minh; loại phần cứng SSD chưa được kiểm chứng.

MCP không có tín hiệu “Vision đã suy luận xong”. Việc tự dọn diễn ra sau khi ảnh
đã được nạp đủ vào response; caller đọc đường dẫn trực tiếp có trách nhiệm release.
TTL chỉ quét khi có yêu cầu preview mới. Thư mục render dang dở do process bị kill
không tự bị TTL xóa. Khóa local dai dẳng trả CLEANUP_PENDING để có thể thử lại.
Phiên chỉnh sửa được giữ để bảo toàn revision và khả năng tiếp tục công việc.

Fast Tier cùng các suite chọn lọc đã chạy; không tuyên bố toàn bộ 28 suite PASS.
Các sửa đổi có sẵn ở `cad_plan_engine.py`, `test_dce_cad_compliance.py`, tài liệu RFC
và starter kit được giữ nguyên. Trong ca xuất hiện thêm
`tests/test_mcp_dce_cad_server.py` từ bên ngoài; CODEX không sửa hay tính file đó
vào bằng chứng nghiệm thu này.

Quét conflict Drive trước nhận ca: 0 file xung đột. Kết quả quét cuối ca và
hash SHA-256 các file triển khai nằm trong `evidence.json`.
