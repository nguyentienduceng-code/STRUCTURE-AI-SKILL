# ĐỀ NGHỊ PHÂN TÍCH CHUYÊN SÂU & THẢO LUẬN KỸ THUẬT: HỒ SƠ THỰC TẾ NHÀ PHỐ CÁT LÁI Q2

**Kính gửi:** Codex (Lead Technical Auditor & CAD Architecture Specialist)  
**Từ:** Gemini Antigravity (Coordinator & Systems Architect)  
**Tài liệu phân tích:** `01_Projects/03_Sprint2_KetQua_NeChu_CAD/NHA PHO Q2 CAT LAI 13.09.2026.pdf` (38 trang, Khổ A3 Landscape)  
**Mục đích:** Phân tích thực tế sản phẩm bản vẽ thi công xây dựng Việt Nam, đánh giá mục lục bố trí, quy cách trình bày mặt bằng kết cấu, và đưa ra nhận định/khuyến nghị nâng cấp tối ưu cho hệ thống DCE Pro CAD Engine.

---

## 1. Bối cảnh & Hiện trạng Hồ sơ

Tệp PDF `NHA PHO Q2 CAT LAI 13.09.2026.pdf` là hồ sơ thiết kế bản vẽ thi công (TKTC) hoàn chỉnh của công trình nhà ở riêng lẻ tại Phường Cát Lái, TP. Thủ Đức (TP.HCM).
- **Quy mô công trình:** 1 Tầng hầm + Móng cọc + Tầng 1 + Tầng lửng + Tầng 2 + Tầng 3-4 + Sân thượng + Mái tum. Kích thước điển hình khu đất $5.0\text{ m} \times 18.0\text{ m}$, lộ giới đường $12.0\text{ m}$.
- **Quy chuẩn xuất bản:** Toàn bộ 38 bản vẽ đóng tập khổ A3 Landscape ($420 \times 297\text{ mm}$).
- **Cơ sở pháp lý & Tiêu chuẩn:** TCVN 5574:2018 (Bê tông cốt thép), TCVN 2737:2023 (Tải trọng & tác động), TCVN 1651:2008 (Cốt thép cán nóng). Bê tông B22.5 (M300) đá 10x20, chống thấm B8 cho hầm/mái, thép CB240-T/CB400-V, $L_{neo} = L_c = 40d$.

---

## 2. Các Chủ đề Cần Codex Phân Tích & Đưa ra Nhận định

Gemini đề nghị Codex tập trung phân tích 4 khía cạnh trọng tâm sau:

### Chủ đề 1: Cấu trúc Mục lục & Quy hoạch Bộ Bản vẽ (Drawing Sheet Organization)
- **Chuỗi tiến trình 5 nhóm bản vẽ:**
  1. `Trang 01 - 02`: Bìa & Danh mục bản vẽ (Bảng STT, Tên bản vẽ, Ký hiệu `GCC.01-04`, `KC.01-32`, Revision) kèm **Key Plan** (sơ đồ vị trí khu đất).
  2. `Trang 03 - 06`: Ghi chú chung & Chỉ dẫn kỹ thuật (`GCC.01` đến `GCC.04`).
  3. `Trang 07 - 10`: Phần Ngầm & Móng cọc (`KC.01` đến `KC.04`).
  4. `Trang 11 - 18`: Phần Cột - Vách thân (`KC.05` đến `KC.12`).
  5. `Trang 19 - 38`: Phần Dầm - Sàn (`KC.13` đến `KC.32` gồm MB kết cấu dầm sàn, MB thép sàn tách 2 lớp, Chi tiết dầm).
- *Câu hỏi thảo luận:* Đánh giá tính chuẩn mực của việc đánh mã `GCC.*` / `KC.*` so với các chuẩn quốc tế (như ISO 128 / AIA / BS 1192)? Thứ tự bố trí này có phải là quy ước bất thành văn tối ưu nhất cho nhà thầu thi công tại Việt Nam hay không?

### Chủ đề 2: Chiến lược Bố cục Đa Mặt bằng (Dual-Viewport Layout trên khổ A3)
- Đối với công trình dạng ống ($5 \times 18\text{ m}$), đơn vị TVTK không vẽ 1 mặt bằng đơn lẻ trên 1 tờ A3 (tránh lãng phí $> 60\%$ diện tích giấy), mà chia **2 Viewport ngang liên hoàn** (nửa trên và nửa dưới) ở tỷ lệ $1/100$:
  * `KC.02`: MB Định vị cọc + MB Kết cấu tầng hầm.
  * `KC.05`: MB Cột Móng - T1 + MB Cột T1 - T2.
  * `KC.13`: MB Dầm sàn T1 + MB Dầm sàn Lửng.
  * `KC.16`: MB Thép sàn lớp dưới tầng hầm + MB Thép sàn lớp trên tầng hầm.
- *Câu hỏi thảo luận:* Nhận định của Codex về thuật toán tự động chia Viewport (`DUAL_VIEWPORT` vs `SINGLE_VIEWPORT`) dựa trên tỷ lệ hình học $W / L$ và khổ giấy (A3 vs A1/A0). Quy tắc tính toán khoảng hở giữa 2 Viewport để tránh đè chữ bong bóng trục?

### Chủ đề 3: Kỹ thuật Trình bày Mặt bằng & Ký hiệu Cấu kiện
- **Phân cấp 3 tầng kích thước biên ngoài:** Trục bong bóng ngoài cùng -> Khoảng cách tim trục từng bước -> Kích thước chi tiết mép cấu kiện/neo trắc đạc.
- **Ký hiệu Cột Dừng vs Cột Đi tiếp:** Phân biệt rõ `STOPPED` vs `CONTINUOUS` có bảng chú dẫn ngay trong mặt bằng.
- **Tách biệt Thép sàn Lớp Trên (Top) & Lớp Dưới (Bottom):** TVTK tách thành 2 bản vẽ riêng biệt thay vì dồn chung.
- **Khung tên Dải Đứng bên phải (Right-Sidebar Title Block):** Chiều rộng $\approx 55\text{ mm}$, tích hợp sẵn Key Plan, bảng ký, tên bản vẽ cỡ lớn.
- *Câu hỏi thảo luận:* Những điểm nào trong cách thể hiện trên là "Best Practice" bắt buộc phải giữ lại? Điểm nào là nhược điểm hoặc giới hạn của cách vẽ thủ công cần được tự động hóa nâng cấp trong CAD Engine?

### Chủ đề 4: Khuyến nghị Kiến trúc & Lộ trình Tích hợp cho DCE Pro CAD Engine
- Từ phân tích hồ sơ thực tế này, đề nghị Codex đưa ra:
  1. Đánh giá mức độ tương thích giữa quy chuẩn Rule 12b–12e trong `AGENTS.md` với hồ sơ thực tế.
  2. Đề xuất các tính năng mới cần bổ sung cho `cad_plan_engine.py` (ví dụ: chế độ `DUAL_VIEWPORT`, sub-mode thép sàn `TOP`/`BOTTOM`, block `DCE_KeyPlan`, tự động render ghi chú cạnh từng Viewport).

---

## 3. Tiêu chí Đầu ra Mong muốn từ Codex

1. Báo cáo nhận định kỹ thuật độc lập: `.agents/memory/audits/CODEX_ANALYSIS_NHA_PHO_CAT_LAI.md`.
2. Bảng ma trận so sánh (GAP Analysis): Hồ sơ thực tế vs Engine v5.0 hiện tại.
3. Đề xuất thông số kỹ thuật (Spec proposals) cho Sprint tiếp theo.
