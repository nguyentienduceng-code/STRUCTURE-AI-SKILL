# Khắc phục F01–F05 — CODEX

Ngày: 2026-11-13T22:26:28.244856+07:00

Đã sửa năm lỗi trong biên bản STRUCTURE_CODEX_20261113. Full PASS 27/27
(89.46s), fast PASS 17/17 (11.57s).

| Lỗi | Cách sửa | Kiểm chứng |
|---|---|---|
| F01 — ZIP hỏng | Dựng lại bảng chỉ mục rvt-mcp.zip từ 663 local entries | Toàn bộ byte đầu vào được xử lý; CRC và SHA-256 từng entry khớp; 7/7 ZIP hiện đọc được |
| F02 — nhận đè ca | Kiểm holder bên trong FileLock trước claim/complete/review | Tác tử khác bị từ chối, cùng holder được nhận lại; hai subprocess tranh ca chỉ một bên thắng |
| F03 — root/memory | Dò project root chứa .agents, dùng get_bus_paths cho quét memory, sinh đường dẫn memo động | Cả hai entry points cho cùng root và .agents/memory/DUAL_AGENT_BUS.json; test cwd lồng nhau, bên ngoài và layout legacy |
| F04 — đường dẫn ổ G cố định | CAD yêu cầu input/output rõ ràng, template theo __file__; demo MS Project yêu cầu output rõ ràng | Không còn 8 literal workspace trong ba entrypoints; CLI thiếu output thoát 2 và không tạo file |
| F05 — registry CAD | Thêm path tương đối, validator và discovery cùng dùng path, khai báo module nội bộ | Registry 0 lỗi/0 cảnh báo; đường dẫn discovery tồn tại |

## ZIP có cần thiết không?

Các ZIP là mã nguồn tham khảo lưu trữ, không cần cho hoạt động hiện tại của tools
production hoặc bộ 27 suites. Không cần giải nén để chạy hệ thống. Giữ lại giúp
tra cứu/tích hợp Revit sau này và bảo toàn lịch sử; chúng không phải bản cài Revit
đã được kích hoạt. Lượt sửa này không cài đặt hay chạy code trong các ZIP.

Bản rvt-mcp bị thiếu central directory/EOCD. Tất cả 663 local entries còn trong
1.877.086 byte đều giải nén và kiểm CRC được. Đã tái tạo ZIP, đọc lại từng entry
và kiểm SHA-256. Bản gốc được giữ tại `rvt-mcp.original.damaged`, không bị xóa.
SHA-256 bản phục hồi: `26729ac2b5d28bd374f30ec8dbc551f5f2df0476c03e6c29c82a177f9a21aa81`.

Manifest `.agents/_references_archived/rvt-mcp.manifest.json` ghi từng entry và checksum. Manifest chuẩn tại
`.agents/_references_archived/verified_manifest.json` ghi cả 7 ZIP hiện tại.
Tổng kiểm kê hiện tại là 2.969 file; không đủ bằng chứng để xác nhận con số 3.739
của lần nén trước. Không đánh đồng khôi phục mọi entry còn hiện diện với khôi
phục đầy đủ repository trước khi nén. README lưu trữ đã ghi rõ giới hạn này.

## Kiểm thử và phạm vi

- Suite 19 tăng từ 3 lên 7 tests, bổ sung kiểm quyền sở hữu, race hai tiến trình,
  workspace mới và đường dẫn legacy; vẫn nằm trong bộ 27 suites.
- `full/` lưu log từng suite và timings.json. `fast/` lưu lần xác nhận fast.
- `structure_evidence.json`: 14 skills, 222 nguồn Python không lỗi cú pháp,
  archive CRC, root resolver và rà literal đường dẫn.
- `bus_registry_evidence.json`: tái hiện lại lỗi cũ đã sửa trên bus tạm.
- `entrypoints.json`: CLI từ cwd ngoài dự án, không ghi vào dự án mẫu.

Smoke CLI phát hiện thêm import không dùng `import_from_msproject_xml` trỏ tới
hàm không tồn tại. Đã bỏ import này. Full được chạy trước sửa import nhỏ cuối
cùng; CLI smoke và fast được chạy lại sau đó. Không chạy pipeline MS Project
có tạo MPP qua COM vì yêu cầu kiểm thử hiện tại không cần mở ứng dụng GUI.
Các API XML/export đang dùng được giữ nguyên; không tuyên bố bổ sung chức năng
import XML vốn chưa được engine triển khai.

Bus/memo được cập nhật nguyên tử cho trạng thái COMPLETED và trỏ báo cáo này.
Những giới hạn hiệu năng từ ca tối ưu trước không nằm trong năm lỗi của lượt
sửa này và không được ngầm đánh dấu là đã giải quyết.
