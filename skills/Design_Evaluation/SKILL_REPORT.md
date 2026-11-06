---
name: SKILL_REPORT
parent: Design_Evaluation
version: 3.5.0
last_updated: 2026-11-03
updated: 2026-11-03
description: >
  Chuẩn xuất bản Báo cáo Thẩm tra Kỹ thuật & Hồ sơ Thuyết minh Khoanh Lỗi Bản vẽ (.docx) cấp độ Viện Thiết kế & Tư vấn Quốc tế.
  Bản nâng cấp v3.5.0 thực thi khóa cứng Điều 12b AGENTS.md (ZERO WHITE TEXT LOCK) và Natural Print Palette
  (Header #DCE4EC / #EAE6DF + Chữ đậm #1E3246, Auto-Linter sanitize_docx_table_colors), loại bỏ 100% rủi ro mất chữ khi in ấn.
---

# SKILL_REPORT — QUY CHUẨN XUẤT BẢN BÁO CÁO THẨM TRA & HỒ SƠ KHOANH LỖI (.DOCX) (v3.5.0)

## 1. TRIẾT LÝ TRÌNH BÀY & HỆ MÀU BẢNG BIỂU IN ẤN TỰ NHIÊN (NATURAL PRINT PALETTE — ĐIỀU 12B)

1. **Phông chữ & Sàn cỡ chữ (Typography Lock):**
   - Toàn bộ văn bản Word bắt buộc dùng **`Times New Roman`** (khóa đồng bộ cả 4 trường `w:ascii`, `w:hAnsi`, `w:eastAsia`, `w:cs`; Văn bản thân bài `11.5pt – 12.0pt`, Bảng biểu `10.0pt – 10.5pt`, Chú thích `9.5pt`).
   - **Cấm tuyệt đối Emoji mạng xã hội trong văn bản Word/Excel pháp lý**: Sử dụng nhãn kỹ thuật chuẩn in ấn `[ĐẠT]`, `[ĐẠT — TỐI ƯU]`, `[CẢNH BÁO — SÁT NGƯỠNG]`, `[KHÔNG ĐẠT]`, `[CRITICAL]`, `[MAJOR]`, `[MINOR]`.

2. **Khóa Cứng Điều 12b (ZERO WHITE TEXT LOCK) & Hệ Màu Gốc Khoáng (`_SHARED/SHARED_CONTEXT/design_tokens.py` v4.4):**
   - **ZERO WHITE TEXT LOCK:** Tuyệt đối cấm dùng chữ màu trắng trong mọi bảng biểu của file Word (`.docx`). Khi in ấn mặc định (Word bỏ qua màu nền trang) hoặc photocopy đen trắng, chữ màu trắng trên nền tối sẽ biến thành chữ trắng trên giấy trắng gây mất toàn bộ dữ liệu bảng.
   - **Header Bảng & Thanh Tiêu đề Phiếu:** Bắt buộc dùng nền sáng gốc khoáng **Xanh Đá Phiến Sương Nhạt (`#DCE4EC`)** hoặc **Đá Vôi Sáng (`#EAE6DF`)** đi kèm chữ đậm **Xanh Thép Trầm (`#1E3246`)** hoặc **Mực Than Chì (`#1C1E21`)**.
   - **Dòng dữ liệu (Data rows):** Chữ tối (`#1C1E21`), nền xen kẽ Trắng và **Ngà Giấy Tự Nhiên (`#F8F7F4`)**, đường kẻ lưới mảnh **Xám Đá (`#D0CEC7`)** (`sz="4"`), viền đỉnh và đáy bảng `#1E3246` (`sz="8"`).
   - **Dòng Tổng kết & Cột Nhãn Bên Trái (Summary rows & Left Label Column):** Chữ tối `#1E3246` in đậm, nền **Xám Khoáng Ấm (`#F2EFE9`)** hoặc **Xô Thơm Nhạt (`#EBF3ED`)**.
   - **Cơ chế Chặn Tự Động (`sanitize_docx_table_colors(doc)`):** Mọi script xuất Word bắt buộc kích hoạt `sanitize_docx_table_colors(doc)` trước `doc.save()` để tự động quét 100% các `run` trong bảng biểu và ghi đè mọi màu chữ sáng/trắng về `#1E3246` / `#1C1E21`.

3. **Cơ chế Nhúng Biểu đồ Tiến độ Chuẩn Microsoft Project (`add_landscape_gantt_section`):**
   - Khi báo cáo đính kèm Biểu đồ Tiến độ Tổng thể (`ms_project_gantt.py`), bắt buộc ngắt Section Break sang **01 trang A4 Xoay Ngang (Landscape `29.7 x 21.0 cm`)** riêng biệt để nhúng ảnh ở độ phân giải **300 DPI** (`width = 25.4 cm`), sau đó tự động trả về khổ **A4 Dọc (Portrait `21.0 x 29.7 cm`)** cho các trang nội dung còn lại.
