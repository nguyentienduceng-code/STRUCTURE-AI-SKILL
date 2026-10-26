---
name: SKILL_RFI
version: 1.4.0
updated: 2026-10-26
status: PRODUCTION_READY
description: >
  Hệ thống Phân loại Mức độ Nghiêm trọng (Critical / Major / Minor), Phát hành Phiếu Yêu cầu Làm rõ (RFI),
  Biên bản Không phù hợp (NCR) & Bộ 4 Điều khoản Chế tài Hợp đồng TVTK chuẩn Pháp lý Xây dựng Việt Nam
  (Nghị định 175/2024/NĐ-CP, TT 34/2026/TT-BXD, Nghị định 37/2015/NĐ-CP & Thông lệ FIDIC White Book).
---

# SKILL_RFI — QUẢN TRỊ PHIẾU RFI, BIÊN BẢN NCR & KHUNG CHẾ TÀI HỢP ĐỒNG (v1.4.0)

## 1. QUY TẮC ĐÁNH MÃ SỐ ĐỊNH DANH THỐNG NHẤT (MANDATORY ID FORMAT)
Mọi báo cáo thẩm tra và bảng tổng hợp khi gọi `SKILL_RFI` bắt buộc phải xuất đúng mã định danh chuẩn:
- **Phiếu Yêu cầu Làm rõ Kỹ thuật:** `RFI-DES-YYYYMMDD-NNN` (Ví dụ: `RFI-DES-20261025-001` đến `RFI-DES-20261025-016`).
- **Biên bản Không phù hợp (Hold Point):** `NCR-DES-YYYYMMDD-NNN` (Ví dụ: `NCR-DES-20261025-001` đến `NCR-DES-20261025-009`).
*(Tuyệt đối không dùng mã viết tắt sơ sài `RFI-01`, `NCR-01` thiếu ngày tháng và phân hệ).*

## 2. CẤU TRÚC BẮT BUỘC CỦA MỖI PHIẾU RFI / NCR (6 TRƯỜNG THÔNG TIN)
1. **Mã định danh & Mức độ nghiêm trọng:** `CRITICAL (Hold Point)` / `MAJOR` / `MINOR`.
2. **Tọa độ hồ sơ tham chiếu chính xác:** Ghi rõ tên file, số hiệu bản vẽ (`KC-02`, `KC-07`, `KT-02`), số trang PDF và tọa độ trục (`Trục Y4, Trục X1–X11`).
3. **Mô tả bằng chứng xung đột định lượng (Nguồn A vs Nguồn B):** Nêu rõ con số trên Bản vẽ Mặt bằng vs Mặt cắt vs Tag thép vs Thuyết minh tính toán (ví dụ: `Bản vẽ KC-02 vẽ 2Ø16 (As = 4.02 cm²) < TMKC 02 trang 17 yêu cầu As,tt = 4.23 cm² (chọn 3Ø16 = 6.03 cm²)`).
4. **Phân tích hậu quả cơ học & rủi ro pháp lý:** Nêu rõ nguy cơ mất ổn định, lật móng, nứt thấm hoặc bị từ chối cấp phép xây dựng / thẩm duyệt PCCC.
5. **Yêu cầu hành động khắc phục bắt buộc (Mandatory Corrective Action):** Đưa ra thông số kỹ thuật cụ thể buộc TVTK phải tính lại và sửa bản vẽ.
6. **Thời hạn phản hồi (SLA) & Điều kiện mở khóa (Release Condition):** Thời hạn phản hồi bắt buộc là **05 ngày làm việc** (SLA 5 Working Days) và hồ sơ TVTK phải nộp lại đầy đủ (Văn bản giải trình + Bản vẽ Rev.01 + Thuyết minh hiệu đính) để đóng NCR.

## 3. KHUNG CHẾ TÀI HỢP ĐỒNG 4 ĐIỀU KHOẢN DÀNH CHO CHỦ ĐẦU TƯ (ARGON BENCHMARK)
Để Chủ đầu tư nắm quyền kiểm soát tuyệt đối và khóa chặt trách nhiệm của đơn vị Tư vấn Thiết kế, `SKILL_RFI` tích hợp 04 điều khoản chế tài hợp đồng mẫu:
1. **Điều khoản 1 — Chặn điểm nghiệm thu (Milestone Hold Point):**
   - *Quy tắc:* Khi hồ sơ thiết kế tồn tại bất kỳ lỗi `CRITICAL (Hold Point)` nào chưa được TVTK giải trình và khắc phục đạt yêu cầu của Đơn vị Thẩm tra, Chủ đầu tư có quyền **từ chối ký Biên bản Nghiệm thu Hồ sơ Thiết kế** của giai đoạn tương ứng.
2. **Điều khoản 2 — Phạt vi phạm chất lượng thiết kế (Design Quality Penalty):**
   - *Quy tắc:* Nếu tỷ lệ sai lệch nội lực/thép giữa Bản vẽ và Thuyết minh vượt quá 5% hoặc số lượng lỗi Critical vượt quá 03 lỗi, TVTK chịu phạt vi phạm hợp đồng từ **2% đến 5% giá trị hợp đồng tư vấn thiết kế** theo Điều 146 Luật Xây dựng và Điều 34 Nghị định 37/2015/NĐ-CP.
3. **Điều khoản 3 — Khấu trừ chi phí thẩm tra lại vào phí tư vấn (Backcharge of Re-Audit Fees):**
   - *Quy tắc:* Trường hợp hồ sơ thiết kế bị Đơn vị Thẩm tra độc lập đánh giá "KHÔNG ĐẠT" và phải tiến hành thẩm tra lại (Re-Audit) từ lần thứ 2 trở đi do lỗi chủ quan của TVTK, **toàn bộ chi phí thẩm tra lại sẽ được khấu trừ trực tiếp (Backcharge)** vào đợt thanh toán tiếp theo của TVTK.
4. **Điều khoản 4 — Bảo lưu quyền tạm dừng thanh toán và bồi thường thiệt hại (Indemnity & Withholding):**
   - *Quy tắc:* Căn cứ Khoản 2 Điều 85 Luật Xây dựng và Điều 28 Nghị định 37/2015/NĐ-CP, Chủ đầu tư có quyền **tạm đình chỉ giải ngân đợt thanh toán kế tiếp** cho đến khi TVTK bàn giao toàn bộ Hồ sơ Bản vẽ hiệu đính Rev.01 và Thuyết minh cập nhật có xác nhận "ĐẠT" của Đơn vị Thẩm tra.

