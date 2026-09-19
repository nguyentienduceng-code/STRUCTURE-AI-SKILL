# Bộ Test Cases — Backtest Hệ thống v2.1

> Ngày tạo: 01/07/2026  
> Mục đích: Kiểm tra end-to-end sau khi cập nhật Rule C18, Luận giải 4 tầng, Calculation Chain 6 bước.  
> Cách dùng: Copy prompt trong mỗi TC, paste vào chat AI, đánh giá output theo checklist.

---

## TC-01: Kiểm tra Văn phong (Rule C18)

**Prompt mẫu:**
> "Check võng dầm B1 nhịp 8m, tiết diện 300×600, bê tông B25, thép dọc 4Φ22. Hoạt tải sàn 2.0 kN/m²."

**Checklist đánh giá output:**

- [ ] Không có câu nào dài quá 25 từ
- [ ] Không có câu bị động kép ("kết quả cho thấy… được đánh giá là…")
- [ ] Không chứa cụm từ rỗng: "nhìn chung", "xét về mặt", "trên cơ sở", "trong khuôn khổ"
- [ ] Mỗi kết luận kèm ít nhất 1 con số (η, f/L, hoặc giá trị mm)
- [ ] Thuật ngữ tiếng Anh lần đầu có giải nghĩa tiếng Việt trong ngoặc
- [ ] Chủ ngữ các câu là đối tượng kỹ thuật (dầm, tiết diện, tải), không phải "vấn đề", "quá trình"

**Kết quả:** ☐ ĐẠT / ☐ KHÔNG ĐẠT  
**Ghi chú lỗi (nếu có):** ___

---

## TC-02: Kiểm tra Luận giải 4 tầng (DeepResearch Mode A)

**Prompt mẫu:**
> "DeepResearch đánh giá ổn định vách lõi thang máy khi đục 2 lỗ mở 1.5×2m tại tầng hầm. Bê tông B30, vách dày 250mm, chiều cao tầng 3.5m. Đối tượng báo cáo: Tư vấn Thiết kế."

**Checklist đánh giá output:**

- [ ] **Tầng 1 — Nguyên lý cơ học**: Có đoạn giải thích cơ chế ổn định cục bộ/tổng thể khi đục lỗ (1-3 câu, ngôn ngữ đơn giản)
- [ ] **Tầng 2 — Phân tích định lượng**: Có chuỗi tính toán đầy đủ (Công thức → Thế số → Kết quả), kèm Utilization Ratio η
- [ ] **Tầng 3 — Đối chiếu tiêu chuẩn**: Citation Object đầy đủ 4 thành phần (Mã — Năm — Điều/Bảng — Trích yếu)
- [ ] **Tầng 4 — Kết luận & giải pháp**: Kết luận Đạt/Không đạt kèm η; nếu cần → đề xuất gia cường cụ thể (số liệu, không chung chung)
- [ ] Không thiếu tầng nào trong 4 tầng
- [ ] Văn phong tuân thủ Rule C18 (câu ngắn, không bị động kép)

**Kết quả:** ☐ ĐẠT / ☐ KHÔNG ĐẠT  
**Ghi chú lỗi (nếu có):** ___

---

## TC-03: Kiểm tra Pipeline SKILLKC → SKILL_REPORT

**Prompt mẫu:**
> "Phân tích tải trọng gió nhà 10 tầng vùng II-B, địa hình B, chiều cao 35m. Sau đó xuất tờ trình Word gửi Ban QLTK."

**Checklist đánh giá output:**

- [ ] SKILLKC xuất phân tích có Calculation Chain **6 bước** (bao gồm bước 1 "Nguyên lý")
- [ ] Review Gate hiển thị tóm tắt trước khi hỏi xác nhận xuất file
- [ ] Tóm tắt tại Review Gate có liệt kê mục UNVERIFIED (nếu có)
- [ ] Tờ trình Word chứa Calculation Chain **đầy đủ, không bị nén**
- [ ] Bảng tra cứu tiêu chuẩn có cột "Vị trí tra cứu (Mục / Bảng / Trang)"
- [ ] Approval Matrix có đủ 3 cột: Đề xuất / Kiểm tra / Phê duyệt
- [ ] Mức độ kỹ thuật ở mức CAO (Tư vấn Thiết kế) — không bị hạ cấp

**Kết quả:** ☐ ĐẠT / ☐ KHÔNG ĐẠT  
**Ghi chú lỗi (nếu có):** ___

---

## TC-04: Kiểm tra MODE 2D ưu tiên

**Prompt mẫu:**
> "Vẽ minh họa mặt cắt cột BTCT 400×600, bố trí thép 8Φ22, đai Φ10a150."

**Checklist đánh giá output:**

- [ ] Hệ thống gọi script Python (`draw_rc_column.py`), KHÔNG gọi `generate_image`
- [ ] Ảnh output là bản vẽ kỹ thuật 2D (có kích thước, ký hiệu thép, tỷ lệ)
- [ ] KHÔNG xuất hiện ảnh 3D render kiểu AI
- [ ] Ảnh được nhúng bằng đường dẫn tuyệt đối
- [ ] File ảnh được xác nhận tồn tại (list_dir / view_file)

**Kết quả:** ☐ ĐẠT / ☐ KHÔNG ĐẠT  
**Ghi chú lỗi (nếu có):** ___

---

## TC-05: Kiểm tra NCR + Tờ trình kết hợp

**Prompt mẫu:**
> "Nhà thầu đổ sai mác BT cột tầng 5: thiết kế B30, thực tế đổ B20. Phân tích NCR và xuất tờ trình gửi GĐ Ban XD."

**Checklist đánh giá output:**

- [ ] Phân loại NCR đúng mức (CRITICAL/MAJOR/MINOR) với giải thích lý do
- [ ] **Tầng 1 — Nguyên lý**: Giải thích tại sao mác BT thấp hơn ảnh hưởng sức chịu nén cột (cơ chế phá hoại)
- [ ] **Tầng 2 — Định lượng**: Tính toán lại khả năng chịu lực cột với B20 vs B30, có η
- [ ] **Tầng 3 — Tiêu chuẩn**: Trích dẫn TCVN 5574 (hoặc tương đương) đầy đủ Citation Object
- [ ] **Tầng 4 — Giải pháp**: Đề xuất phương án xử lý cụ thể (VD: gia cường CFRP/thép bao, hoặc đập đổ) kèm cơ sở tính toán
- [ ] Tờ trình tuân thủ văn phong Rule C18
- [ ] Tờ trình có Approval Matrix
- [ ] Cảnh báo 3 bộ môn (Rule 12) nếu thay đổi tiết diện cột

**Kết quả:** ☐ ĐẠT / ☐ KHÔNG ĐẠT  
**Ghi chú lỗi (nếu có):** ___

---

## Bảng Tổng hợp Kết quả Backtest

| Test Case | Kết quả | Số mục ĐẠT / Tổng | Ghi chú |
|-----------|---------|---------------------|---------|
| TC-01 | ☐ | /6 | |
| TC-02 | ☐ | /6 | |
| TC-03 | ☐ | /7 | |
| TC-04 | ☐ | /5 | |
| TC-05 | ☐ | /8 | |
| **TỔNG** | | **/32** | |

**Ngưỡng chấp nhận:** ≥ 28/32 (87.5%) → Hệ thống sẵn sàng sử dụng.  
**Nếu < 28/32:** Liệt kê các mục KHÔNG ĐẠT, phân tích gốc rễ, sửa rule/script, chạy lại backtest.
