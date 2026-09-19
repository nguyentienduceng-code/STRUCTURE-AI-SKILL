<!-- REFERENCE FILE — Chỉ đọc khi dùng MODE 3D (generate_image). KHÔNG đọc khi chỉ dùng MODE 2D (Python). -->

# MODE 3D: Ảnh Render AI — Hướng dẫn Chi tiết

> **Thuật ngữ:** MODE 3D = tên gọi chính thức (trước đây gọi là "MODE A"). MODE 2D = trước đây gọi là "MODE B".
> **Nhắc lại:** ảnh MODE 3D là **minh họa khái niệm**, không có giá trị kỹ thuật. Bắt buộc kèm caption cảnh báo khi đưa vào báo cáo (AGENTS.md điều 9).

## ⚡ IMAGE OUTPUT GUARANTEE PROTOCOL (Quy tắc Đảm bảo Ảnh)

**Quy tắc TUYỆT ĐỐI** — áp dụng cho MỌI ảnh tạo ra:

1. **XÁC ĐỊNH** đường dẫn output **TUYỆT ĐỐI** trước khi vẽ.
   → KHÔNG BAO GIỜ dùng đường dẫn tương đối.
2. **TẠO** ảnh bằng `generate_image` → ảnh tự lưu vào artifacts.
3. **XÁC NHẬN** file ảnh đã tồn tại bằng `list_dir` / `view_file`.
   → Nếu file KHÔNG tồn tại → debug lỗi và chạy lại.
4. **NHÚNG** ảnh bằng ĐƯỜNG DẪN TUYỆT ĐỐI:
   → Đúng: `![Hình 3.1 — Mô tả](g:/full/path/to/file.png)`
   → Sai: `![Hình 3.1](file.png)` hoặc `![Hình 3.1](./output/file.png)`
5. **NẾU** ảnh cần đưa vào artifact `.md`:
   → PHẢI copy file vào thư mục artifacts trước rồi mới nhúng.

---

## 🎨 Khi nào sử dụng MODE A

- Cần ảnh đẹp để đưa vào báo cáo trình Chủ đầu tư, slide thuyết trình.
- Mô tả **biện pháp thi công tổng thể** tại hiện trường.
- Mô tả phương án kiến trúc kết cấu kết hợp.

## Prompt Engineering

> 📖 **Đọc `PROMPT_TEMPLATES.md`** (cùng thư mục) để lấy:
>
> - Framework 5 yếu tố bắt buộc (Subject, Material, Scale, Lighting, Camera)
> - 8 Prompt Templates cho kết cấu phổ biến
> - Negative Prompt chống lỗi ảnh

**Quy tắc nhanh:**

- Prompt PHẢI có đủ 5 yếu tố: Chủ thể + Vật liệu + Tỷ lệ người + Ánh sáng + Góc nhìn.
- Thêm Negative Prompt: *"Avoid: text overlays, watermarks, distorted proportions, cartoon style."*

---

## 🔄 Quy trình Nâng cao — Tạo ảnh 3D từ Bản vẽ 2D Chi tiết

### Decompose Drawing Protocol (Phân tách Bản vẽ)

Khi User cung cấp bản vẽ kỹ thuật 2D kèm yêu cầu render 3D, BẮT BUỘC thực hiện:

1. **Đọc bản vẽ 2D** → Liệt kê từng lớp cấu kiện:
   - (a) **Kết cấu chịu lực**: Thép hình (L, H, C), bê tông, gỗ — ghi rõ mác/kích thước.
   - (b) **Lớp hoàn thiện**: Sơn (màu gì?), mạ kẽm, gỗ tự nhiên, bê tông trần.
   - (c) **Phụ kiện**: Bu lông, ghim neo, bản mã, thanh giằng — kích thước, vị trí.
   - (d) **Cảnh quan**: Loại cỏ, cây trồng, mặt nước, taluy đất.
   - (e) **Bối cảnh**: Công trình kề, đường, cầu, hàng rào liền kề.

2. **Viết prompt phân lớp** (Layer-by-Layer) theo Template 9 trong `PROMPT_TEMPLATES.md`.

3. **Liệt kê MUST NOT** — Ghi rõ ràng những chi tiết KHÔNG được xuất hiện trong ảnh.

### Multi-pass Iteration Protocol (Lặp Tinh chỉnh)

Nếu ảnh lần 1 chưa đúng yêu cầu của User:

| Lần | Hành động |
|-----|-----------|
| 1 | Tạo ảnh ban đầu theo prompt phân lớp |
| 2 | User phản hồi → Phân tích sai ở **layer nào** → Tinh chỉnh **chỉ layer đó** → Tạo ảnh lần 2 |
| 3 | Nếu vẫn chưa đạt → Tinh chỉnh lần cuối. Nếu sau 3 lần vẫn không đạt → báo User giới hạn của AI Render |

### Reference Image Protocol (Ảnh Tham chiếu Hiện trạng & Scene Replacement)

Khi User cung cấp **ảnh hiện trạng** và yêu cầu "thay vào phối cảnh", "chèn vào ảnh", BẮT BUỘC áp dụng **Scene Replacement Protocol**.
Đọc kỹ `references/SCENE_REPLACEMENT.md` để thực hiện quy trình chuẩn:
1. Phân tích ảnh hiện trạng (Góc, sáng, tone màu, tiền/trung/hậu cảnh).
2. Lập bản đồ khu vực KEEP (giữ) và REPLACE (thay).
3. Check 10 yếu tố Photorealism (Weathering, Ground Contact, Edge Blending...).
4. Dùng cấu trúc Prompt Scene Replacement (PRESERVE EXACTLY / REPLACE / ADD NEW / STYLE).
5. Lấy từ vựng chân thực từ Material Reality Library.
6. Pass ảnh hiện trạng vào `ImagePaths` của `generate_image` để model bám sát bối cảnh gốc.
