## 12b. ZERO WHITE TEXT LOCK & Hệ Màu Gốc Khoáng (Bắt buộc cho Word .docx, Excel .xlsx, Ảnh Kỹ thuật)

> **Cơ sở pháp lý & In ấn**: Chuẩn in ấn đen trắng và photocopy hồ sơ kỹ thuật xây dựng Việt Nam. Nguồn sự thật duy nhất: `_SHARED/SHARED_CONTEXT/design_tokens.py`.

- **CẤM TUYỆT ĐỐI**: Dùng chữ màu trắng (`#FFFFFF` hoặc `RGBColor(255, 255, 255)`) trên nền tối trong bất kỳ bảng biểu nào của file Word (`.docx`), bảng tính Excel (`.xlsx`), nhãn ghi chú hay bản vẽ kỹ thuật (`matplotlib`/ảnh render).
- **Hệ quả khi vi phạm**: Khi in ấn mặc định trong Word (mặc định Word bỏ qua màu nền bảng/trang) hoặc photocopy đen trắng, chữ màu trắng trên nền tối sẽ biến thành **chữ trắng trên nền giấy trắng**, làm mất toàn bộ dữ liệu bảng biểu và thông số kỹ thuật.
- **Quy cách bảng biểu bắt buộc**:
  - **Header Bảng & Thanh Tiêu đề**: Nền sáng gốc khoáng **Xanh Đá Phiến Sương Nhạt (`#DCE4EC`)** hoặc **Đá Vôi Sáng (`#EAE6DF`)**, chữ in đậm màu tối **Xanh Thép Trầm (`#1E3246`)** hoặc **Mực Than Chì (`#1C1E21`)**.
  - **Dòng dữ liệu (Data rows)**: Chữ tối (`#1C1E21`), nền xen kẽ Trắng (`#FFFFFF`) và **Ngà Giấy Tự Nhiên (`#F8F7F4`)**, đường kẻ lưới mảnh `#D0CEC7`.
  - **Hình vẽ 2D / Biểu đồ**: Mọi nhãn text trong bounding box, callout hoặc pill tag phải dùng chữ tối màu (`#0F172A`, `#1E3246`, `#7F1D1D`) trên nền sáng (`#FEF08A`, `#FEE2E2`, `#F1F5F9`, `#FFFFFF`).

---
