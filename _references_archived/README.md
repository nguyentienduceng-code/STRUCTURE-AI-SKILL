# Thư Viện Tham Khảo Lưu Trữ (_references_archived)

Thư mục này chứa các mã nguồn tham khảo bên ngoài đã được đóng gói dạng nén (.zip) nhằm:
1. Giảm thiểu số lượng file I/O trên Google Drive ảo (từ 3,739 files xuống còn 7 file zip).
2. Tối ưu tốc độ đồng bộ và tránh nghẽn I/O khi quét thư mục workspace.

Khi cần tra cứu mã nguồn tham khảo, kỹ sư hoặc Agent có thể giải nén file zip tương ứng.

## Kiểm chứng và phục hồi ngày 2026-11-13

Các ZIP này là mã nguồn tham khảo, không phải dependency mà các tools production
hiện tại nạp khi chạy. Không cần giải nén để chạy bộ kiểm thử 27 suites.

`rvt-mcp.zip` đã được dựng lại bảng chỉ mục từ 663 local entries còn nguyên,
kiểm tra CRC và SHA-256 từng entry. Bản hỏng được giữ tại
`../memory/audits/STRUCTURE_REPAIR_CODEX_20261113/rvt-mcp.original.damaged`.
Manifest phục hồi: `rvt-mcp.manifest.json`.

Kiểm kê hiện tại: 7 ZIP hợp lệ, chứa tổng cộng 2.969 file. Con số 3.739 ở trên
là ghi nhận lịch sử của lần dọn dẹp, chưa có manifest nguồn trước khi nén để
đối chiếu. Phục hồi thành công toàn bộ dữ liệu còn trong ZIP hỏng không chứng
minh đầy đủ nội dung repository trước lần nén ban đầu.
