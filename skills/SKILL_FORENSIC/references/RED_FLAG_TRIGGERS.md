# RED FLAG TRIGGERS — SKILL_FORENSIC

> **Phiên bản:** v1.0 — 2026-08-19
> **Mục đích:** Tự động phát hiện dấu hiệu nguy hiểm → kích hoạt leo thang khẩn cấp
> **Phạm vi:** Mọi phân tích SKILL_FORENSIC phải chạy checklist này trước

---

## Cấp độ Nguy hiểm

| Mức | Ký hiệu | Hành động | Thời hạn |
|-----|---------|-----------|----------|
| 🔴 **CRITICAL** | `LEAVE_SITE` | Rời khỏi công trình, báo cáo ngay | **Ngay lập tức** |
| 🟠 **HIGH** | `EVACUATE` | Sơ tán, chống đỡ tạm, gọi chuyên gia | **Trong 2 giờ** |
| 🟡 **MEDIUM** | `INVESTIGATE` | Tăng cường giám sát, lên kế hoạch xử lý | **Trong 48 giờ** |
| 🟢 **LOW** | `MONITOR` | Ghi nhận, theo dõi xu hướng | **Trong 1 tuần** |

---

## 🔴 RED FLAGS — Rời khỏi & Báo cáo Ngay

### RCF-01: Sập / Gãy Cấu kiện
- **Trigger:** Cấu kiện bị phá hoại toàn phần (thanh cột gãy, dầm đứt)
- **Hành động:** LEAVE_SITE → Gọi 113 / CĐT / Chủ đầu tư
- **Lý do:** Nguy hiểm đến tính mạng, cần sơ tán toàn bộ khu vực

### RCF-02: Võng Quá Mức Thấy Được
- **Trigger:** Độ võng dầm/sàn nhìn thấy bằng mắt thường (≥ L/50)
- **Hành động:** LEAVE_SITE → Đánh dấu vị trí, đo đạc ngay
- **Lý do:** Dấu hiệu phá hoại cấu trúc nghiêm trọng

### RCF-03: Tiếng Động Lạ / Nổ
- **Trigger:** Tiếng nổ, kẹt, rắc rắc từ kết cấu
- **Hành động:** LEAVE_SITE → Dừng ngay mọi hoạt động thi công
- **Lý do:** Có thể là tín hiệu phá hoại cấu kiện

### RCF-04: Vết nứt Xuyên Thấu Kết cấu
- **Trigger:** Vết nứt xuyên qua tiết diện cột, dầm, vách (bề rộng ≥ 3mm)
- **Hành động:** LEAVE_SITE → Đo, chụp ảnh, báo cáo
- **Lý do:** Mất khả năng chịu lực cục bộ

### RCF-05: Vết nứt Động (Di Chuyển)
- **Trigger:** Vết nứt mở rộng theo thời gian trong ca kiểm tra
- **Hành động:** LEAVE_SITE → Đánh dấu + đo + ghi thời gian
- **Lý do:** Cấu kiện đang mất ổn định

---

## 🟠 HIGH FLAGS — Sơ tán & Xử lý Khẩn

### RHF-01: Vết nứt Chéo Lớn trên Cột
- **Trigger:** Vết nứt xiên 45° trên cột, bề rộng ≥ 1.5mm
- **Hành động:** EVACUATE → Chống đỡ tạm → Gọi kỹ sư kết cấu
- **Lý do:** Đặc trưng phá hoại cắt-gãy cột

### RHF-02: Vết nứt Kết hợp Trên Sàn (Vết nứt Bảng)
- **Trigger:** Vết nứt hình mắt cá lưới trên sàn, kèm võng
- **Hành động:** EVACUATE → Giới hạn tải trọng → Gọi chuyên gia
- **Lý do:** Dấu hiệu punching shear hoặc quá tải

### RHF-03: Lún Không Đều Gây Nghiêng
- **Trigger:** Cao độ chênh lệch ≥ 1/200 giữa 2 điểm lân cận
- **Hành động:** EVACUATE → Đo đạc ngay → Báo cáo
- **Lý do:** Có thể gây lật hoặc mất ổn định toàn công trình

### RHF-04: Liên kết Bu lông / Hàn Bị Lỏng
- **Trigger:** Bu lông lỏng, đai biến dạng, mối hàn nứt
- **Hành động:** EVACUATE → Tạm dừng thi công → Kiểm tra toàn bộ
- **Lý do:** Mất khả năng chịu lực liên kết

### RHF-05: Bê tông Phong hóa / Rỗng
- **Trigger:** Bê tông bị phong hóa, rỗng, bong tróc (có thể bấm tay thủng)
- **Hành động:** EVACUATE → Core test → Xác định mác thực tế
- **Lý do:** Cường độ bê tông có thể thấp hơn thiết kế rất nhiều

### RHF-06: Cốt Thép Gỉ Ăn Thủng
- **Trigger:** Thép gỉ đến mức giảm tiết diện nhìn thấy được
- **Hành động:** EVACUATE → Đo giảm tiết diện → Tính lại
- **Lý do:** Giảm đáng kể khả năng chịu lực

---

## 🟡 MEDIUM FLAGS — Tăng cường Giám sát

### RMF-01: Vết nứt Uốn Thông thường trên Dầm
- **Trigger:** Vết nứt thẳng đứng tại giữa nhịp, bề rộng < 1mm
- **Hành động:** INVESTIGATE → Đo + theo dõi trong 48h
- **Lý do:** Có thể chấp nhận được nhưng cần theo dõi

### RMF-02: Vết nứt Co ngót ở Sàn
- **Trigger:** Vết nứt mắt cá lưới mịn (< 0.3mm) tại bề mặt sàn
- **Hành động:** INVESTIGATE → Kiểm tra chiều dày lớp bảo vệ
- **Lý do:** Thường do co ngót, không nguy hiểm nhưng ảnh hưởng bền vững

### RMF-03: Lún Nhỏ Đều Đặn
- **Trigger:** Tốc độ lún ≤ 5mm/tháng, không tăng tốc
- **Hành động:** INVESTIGATE → Bố trí mốc đo lún → Đọc hàng tuần
- **Lý do:** Có thể là lún cố kết bình thường

### RMF-04: Neo Cốt Thép Trượt
- **Trigger:** Neo thép bị trượt khỏi vị trí thiết kế > 10mm
- **Hành động:** INVESTIGATE → Xem xét lại thiết kế neo
- **Lý do:** Giảm hiệu quả neo, có thể gây nứt lan rộng

---

## 🟢 LOW FLAGS — Theo dõi Định kỳ

### RLF-01: Vết nứt Nhiệt ở Bề mặt
- **Trigger:** Vết nứt mạng nhện trên bề mặt bê tông do co nhiệt
- **Hành động:** MONITOR → Ghi nhận vào nhật ký
- **Lý do:** Thẩm mỹ, ảnh hưởng bền vững thấp

### RLF-02: Ống Kỹ thuật Xuyên Sàn
- **Trigger:** Ống kỹ thuật đi xuyên qua dầm/sàn mà không có chi tiết
- **Hành động:** MONITOR → Kiểm tra ảnh hưởng (thường không đáng kể)
- **Lý do:** Thường không ảnh hưởng kết cấu nếu ≤ 1/4 bề rộng dầm

### RLF-03: Thay đổi Công năng Nhỏ
- **Trigger:** CĐT thay đổi hoạt tải nhưng không thông báo
- **Hành động:** MONITOR → Yêu cầu báo cáo tải trọng thực tế
- **Lý do:** Tích lũy có thể gây quá tải về lâu dài

---

## Checklist Kích hoạt (Tự động khi bắt đầu phân tích)

```
SKILL_FORENSIC khởi động
  │
  ├── [ ] Kiểm tra RED FLAGS (RCF-01 → RCF-05) — BẮT BUỘC trước
  │       └── Nếu có bất kỳ RCF nào → DỪNG, báo CRITICAL, không tiếp tục phân tích
  │
  ├── [ ] Kiểm tra HIGH FLAGS (RHF-01 → RHF-06)
  │       └── Nếu có → LEVELL_UP, báo HIGH, gọi chuyên gia
  │
  ├── [ ] Kiểm tra MEDIUM FLAGS (RMF-01 → RMF-04)
  │       └── Nếu có → Đưa vào giả thuyết ưu tiên cao
  │
  └── [ ] Kiểm tra LOW FLAGS (RLF-01 → RLF-03)
          └── Nếu có → Ghi nhận, đưa vào báo cáo
```

---

## Mẫu Báo cáo Khẩn (Emergency Report)

```markdown
## 🔴 BÁO CÁO KHẨN — [Ngày giờ]

**Công trình:** [Tên]
**Địa điểm:** [Địa chỉ]
**Người phát hiện:** [Họ tên]
**Mức nguy hiểm:** 🔴 CRITICAL

**RED FLAG phát hiện:** RCF-[XX]
**Mô tả:** [Chi tiết hiện trạng]
**Nguy hiểm:** [Tại sao nguy hiểm]
**Hành động đã thực hiện:** [Đã làm gì]
**Hành động yêu cầu:** [Cần làm gì]
```

---

*Đây là danh sách không đầy đủ — luôn dùng kiến thức kỹ thuật + kinh nghiệm thực tế để nhận định. Khi nghi ngờ, luôn báo mức cao hơn.*
