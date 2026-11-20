# Sprint 2 — Kế hoạch đóng các lỗi nghiệm thu

Phạm vi: `.agents` và scratch local. Giữ nguyên hai thư mục nguồn thương mại.

1. Gắn ý nghĩa đường bao sàn tại nguồn sinh CAD bằng XData riêng `DCE_SCENE`. Chỉ đường bao được đánh dấu mới được xử lý như nét; cột/vách kín vẫn là vùng đặc.
2. Dùng spatial grid để lọc sơ bộ, sau đó kiểm tra hình học chi tiết: đoạn, polygon và envelope chữ có hướng. DIM và nested Block được tách thành primitives để không cấm khoảng trống trong bbox.
3. Chuẩn hóa mọi khoảng cách vật lý sang drawing units; tìm ứng viên có giới hạn đến 7500 mm. Giữ nhãn khóa và báo xung đột khóa để xử lý, không coi việc không di chuyển là đã hết va chạm.
4. Lập bố trí nhãn trước, sau đó tìm đường leader trực tiếp hoặc dogleg có giới hạn. Leader tránh annotation và vùng cấu kiện đặc; cho phép cắt đường tham chiếu trục/biên sàn và tiếp xúc có chủ đích tại đầu nối.
5. Lưu identity của leader để đọc lại, kiểm tra va chạm và chạy lại không nhân bản. Khi thiếu mapping semantic, ghi rõ điểm nối là suy luận hình học, không chứng nhận liên kết mô hình.
6. Thêm hồi quy cho các lỗi trên; kiểm tra độc lập DXF sau lưu, bảo toàn các entity cố định và nguồn, idempotence, dry-run và cache local.
7. Đo mỗi mặt bằng 3 lần qua MCP, yêu cầu mọi lần < 2 giây, 0 va chạm nhãn và leader theo quy tắc đã công bố. Chạy đầy đủ 30 suites. Render trước/sau để kiểm tra trực quan bổ sung.
8. Viết ACCEPTANCE.md mới, giữ biên bản kiểm toán cũ làm lịch sử, rồi cập nhật IPC.

Không cam kết mọi DWG/Block không hỗ trợ hoặc mọi bố trí không có nghiệm đều tự giải được. Trường hợp đó phải trả lỗi hoặc NEEDS_REVIEW; không xóa chữ, đổi kích thước chữ hay bỏ qua vùng đặc để đạt chỉ tiêu.
