---
name: SKILL_REPORT
parent: Design_Evaluation
version: 3.3.0
updated: 2026-10-26
description: >
  Chuẩn xuất bản Báo cáo Thẩm tra Kỹ thuật & Hồ sơ Thuyết minh Khoanh Lỗi Bản vẽ (.docx) cấp độ Corporate Engineering.
  Bản nâng cấp v3.3.0 khóa cứng Hệ Màu sắc Đồng bộ Form Thuyết minh (#1B365D / #EAF0F6),
  kiến trúc "1 Phiếu = 1 Trang A4 Khép Kín", cấm trùng lặp Hộp-trong-Hộp trên ảnh PNG và khóa dữ liệu nguồn đơn nhất (SSOT).
---

# SKILL_REPORT — QUY CHUẨN XUẤT BẢN BÁO CÁO THẨM TRA & HỒ SƠ KHOANH LỖI (.DOCX) (v3.3.0)

## 1. QUY TẮC TYPOGRAPHY & BẢNG MÀU ĐỒNG BỘ FORM THUYẾT MINH (UNIFIED CORPORATE FORM PALETTE)
1. **Phông chữ & Sàn cỡ chữ (Typography Lock):**
   - Toàn bộ văn bản Word bắt buộc dùng **`Times New Roman`** (Văn bản thân bài `>= 11pt`, Bảng biểu `9.5pt – 10.5pt`).
   - Toàn bộ tiêu đề con vẽ trên ảnh trích xuất bản vẽ (`.png`) bắt buộc dùng phông có chân hỗ trợ đầy đủ tiếng Việt (**`Liberation Serif Bold`** hoặc **`Noto Serif Bold`**) để đồng nhất 100% với `Times New Roman` của thuyết minh — **tuyệt đối cấm dùng phông không chân (`Arial / DejaVu Sans`) hoặc phông lỗi dấu tiếng Việt trên ảnh**.
2. **Bảng màu Chuẩn hóa Đồng bộ giữa Báo cáo Thẩm tra, Thuyết minh Tính toán và Hồ sơ Khoanh lỗi:**
   - **Thanh Header Bảng & Thanh Tiêu đề Phiếu:** Nền **Xanh Navy đậm (`#1B365D`)**, chữ trắng (`#FFFFFF`) in đậm.
   - **Cột Nhãn Bên Trái (Left Label Column — 6 mục của Phiếu thẩm tra, Bảng thông tin bìa & Cột Mã lỗi):** Bắt buộc tô nền **Xanh Băng nhạt (`#EAF0F6`)** đi kèm chữ **Xanh Navy đậm (`#1B365D`)** in đậm. **Tuyệt đối cấm tô nền Xanh Đen đặc (`#1B365D`) chữ trắng cho toàn bộ cột nhãn bên trái** (gây mảng tối nặng nề, xung đột với thanh Banner trên đầu và gây bết mực khi in).
   - **Các Ô Dữ Liệu (Data Cells):** Tô nền xen kẽ Trắng (`#FFFFFF`) và Xám Băng (`#F8FAFC`), chữ Xám Đen (`#0F172A`), đường viền đơn mảnh `#CBD5E1` (`sz="4"`).
   - **Hệ Màu Phân Tầng Mức Độ Nghiêm Trọng (Refined Semantic Badges):**
     + `CRITICAL`: Chữ/Banner **Đỏ Đô trầm (`#991B1B`)**, nền ô badge **Hồng nhạt (`#FEF2F2`)**.
     + `MAJOR`: Chữ/Banner **Cam Hổ phách trầm (`#B45309`)**, nền ô badge **Vàng Kem (`#FFFBEB`)**.
     + `MINOR`: Chữ/Banner **Xanh Lam đậm (`#1E40AF`)**, nền ô badge **Xanh Lam nhạt (`#EFF6FF`)** (hài hòa hoàn toàn với tông Navy chủ đạo).

## 2. 05 QUY TẮC BẮT BUỘC KHI XUẤT HỒ SƠ KHOANH LỖI BẢN VẼ (`generate_clash_dossier.py` v3.3.0)
1. **Quy tắc 1 — Cấm Trùng lặp "Hộp trong Hộp" (`Zero Box-in-Box Redundancy`):**
   - Bên trong bức ảnh trích xuất bản vẽ (`.png`) **tuyệt đối KHÔNG được vẽ lặp lại thanh Banner tiêu đề phiếu ở đỉnh ảnh** và **KHÔNG được vẽ lặp lại hộp chữ 4 dòng ở đáy ảnh** (do đã có thanh Header và Bảng 6 mục của Word đảm nhiệm).
   - Bức ảnh `.png` chỉ được chứa khung bản vẽ CAD khoanh đỏ đặt trên nền `#F0F4F8` viền `#1B365D` (`2px`) kèm thanh tiêu đề con (`#1B365D`) ngay trên đỉnh mỗi khung cắt bản vẽ, giúp vùng bản vẽ CAD phóng to thêm **35%–45%**.
2. **Quy tắc 2 — Khóa cứng Bố cục "1 Phiếu = 1 Trang A4 Khép Kín" (`Strict One-Page-Per-Exhibit Lock`):**
   - Mỗi Phiếu thẩm tra bản vẽ (gồm: Thanh Banner + Dòng vị trí/chế tài + Ảnh khoanh đỏ + Bảng 6 mục) bắt buộc phải nằm gọn **100% trên 01 trang A4 đơn**.
   - Hàm nhúng ảnh phải tự động tính tỷ lệ khung hình (`aspect = W / H`) và khóa trần chiều cao ảnh `max_h_cm <= 7.6 cm` (`6.6 cm` đối với phiếu có tổng ký tự > 650), lề trang `Top 1.6 cm / Bottom 1.5 cm`, padding ô `26–34 dxa`. **Tuyệt đối cấm để rớt 1–2 dòng mồ côi sang trang kế tiếp hoặc tạo trang trắng xen giữa các phiếu.**
3. **Quy tắc 3 — Tự động Co Cỡ Chữ Tiêu Đề Khung Ảnh (`Auto-Fit Subheader — Zero Text Overflow`):**
   - Khi vẽ thanh tiêu đề con trên đầu mỗi khung bản vẽ CAD, bắt buộc gọi hàm `fit_subheader_font()` để đo chiều rộng chuỗi (`draw.textbbox`) và tự động giảm cỡ chữ từ `18px` xuống `12px` sao cho luôn nhỏ hơn chiều rộng khung bản vẽ tối thiểu `18px`. Tuyệt đối không để chữ tràn ra ngoài hộp nền xanh Navy.
4. **Quy tắc 4 — Cân đối Độ rộng Cột & Cấm `ALL CAPS` trong Bảng Danh mục (Bảng 2 & Bảng 3):**
   - Cột mô tả tên phiếu và nội dung xung đột trong Bảng Danh mục phải viết bằng **chữ thường chuẩn câu (Sentence Case)** (giữ nguyên viết hoa cho mã hiệu kỹ thuật `CN3, KC-02, M1, DK2, Ø10a150`), phân bổ độ rộng 5 cột cân đối (`1.8 | 1.8 | 2.1 | 7.5 | 3.8 cm`) để không bị gãy dòng vụn vặt.
5. **Quy tắc 5 — Khóa Dữ liệu Nguồn Đơn nhất (`Single-Source-of-Truth Anti-Drift Lock`):**
   - Mọi con số đưa vào Bảng Ma trận (Bảng 2), Bảng Danh mục (Bảng 3), Bảng Chi tiết 6 mục của từng Phiếu và nhãn khoanh đỏ bắt buộc truy xuất từ cùng một danh sách đối tượng `ClashRecord` duy nhất trong `drawing_calc_crosscheck.py` / `clash_registry_ssot.json`. Cấm gõ tay số liệu riêng lẻ ở từng bảng gây lệch số liệu (Data Drift).
