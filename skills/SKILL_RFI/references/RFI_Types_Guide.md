# RFI Types Guide — Phân loại Request for Information

> **Version:** 1.0 — 2026-08-30
> **Purpose:** Hướng dẫn phân loại và xử lý RFI theo từng loại

---

## 1. RFI Classification Matrix

| Loại | Sub-type | Priority | Deadline | Xử lý |
|-------|----------|----------|----------|--------|
| **Thiếu Thông tin** | Vật liệu | 🟡 NORMAL | 7 ngày | Cung cấp thông số |
| | Kích thước | 🟡 NORMAL | 7 ngày | Đo/xác nhận |
| | Tải trọng | 🟠 HIGH | 3 ngày | Cung cấp TC |
| **Mâu thuẫn** | Bản vẽ vs Bản vẽ | 🟠 HIGH | 3 ngày | Xác nhận cuối cùng |
| | Bản vẽ vs Thực tế | 🔴 URGENT | 24h | Đo lại ngay |
| **Xác nhận** | Thay đổi thiết kế | 🟠 HIGH | 3 ngày | Duyệt/ Từ chối |
| | Phương pháp thi công | 🟡 NORMAL | 7 ngày | Đồng ý/ Đề xuất |
| **Kỹ thuật** | Phương pháp tính | 🟡 NORMAL | 7 ngày | Thống nhất TC |
| | Chi tiết liên kết | 🟡 NORMAL | 7 ngày | Cung cấp CAD |

---

## 2. Chi tiết từng loại

### 2.1 Thiếu Thông tin

#### 2.1.1 Thiếu vật liệu
**Ví dụ:**
- "Mác bê tông cột tầng 3?"
- "Loại thép thanh ren?"
- "Cấp độ bền bu lông?"

**Câu hỏi mẫu:**
1. Thông số vật liệu thiết kế là gì?
2. Có yêu cầu đặc biệt (chịu nước biển, chịu axit)?
3. Căn cứ tiêu chuẩn nào?

**Template:**
```
RFI về: Thiếu thông số vật liệu
├── Loại vật liệu: [Bê tông / Thép / Bu lông]
├── Vị trí: [Cấu kiện cụ thể]
├── Thông tin cần: [Thông số kỹ thuật]
└── Căn cứ: [Tiêu chuẩn áp dụng]
```

#### 2.1.2 Thiếu kích thước
**Ví dụ:**
- "Chiều dài cọc ép?"
- "Chiều cao tầng?"
- "Đường kính cọc khoan nhồi?"

**Câu hỏi mẫu:**
1. Kích thước thiết kế là bao nhiêu?
2. Có ghi chú đặc biệt nào không?
3. Kích thước thực tế đo được là bao nhiêu?

#### 2.1.3 Thiếu tải trọng
**Ví dụ:**
- "Tải trọng sàn văn phòng?"
- "Tải trọng tường ngăn?"
- "Hệ số tổ hợp?"

**Câu hỏi mẫu:**
1. Giá trị tải trọng thiết kế?
2. Tổ hợp tải trọng đã sử dụng?
3. Căn cứ theo tiêu chuẩn nào?

---

### 2.2 Mâu thuẫn Tài liệu

#### 2.2.1 Bản vẽ vs Thuyết minh
**Ví dụ:**
- "Bản vẽ ghi tiết diện 400x700, thuyết minh ghi 400x800"
- "Bản vẽ ghi thép 6Ø22, thuyết minh ghi 6Ø25"

**Xử lý:**
1. Liệt kê mâu thuẫn cụ thể
2. Yêu cầu xác nhận giá trị đúng
3. Yêu cầu cập nhật tài liệu còn lại

**Câu hỏi mẫu:**
1. Giá trị nào là đúng theo thiết kế cuối cùng?
2. Cần cập nhật bản vẽ hay thuyết minh?
3. Ai chịu trách nhiệm cập nhật?

#### 2.2.2 Bản vẽ vs Thực tế thi công
**Ví dụ:**
- "Kích thước cột thực tế khác bản vẽ"
- "Thép cột thiếu 2 thanh so với bản vẽ"

**Xử lý:**
1. Đo xác nhận kích thước thực tế
2. Đánh giá ảnh hưởng đến khả năng chịu lực
3. Đề xuất biện pháp xử lý

**⚠️ URGENT:** Nếu ảnh hưởng đến kết cấu → báo ngay cho TVGS và CSHT.

---

### 2.3 Yêu cầu Xác nhận

#### 2.3.1 Thay đổi thiết kế
**Ví dụ:**
- "Thay đổi tiết diện dầm từ 400x700 lên 450x750"
- "Thay đổi mác bê tông từ B25 xuống B30"

**Xử lý:**
1. Nêu rõ thay đổi
2. Đánh giá ảnh hưởng
3. Yêu cầu phê duyệt

**Template:**
```
ĐỀ XUẤT THAY ĐỔI THIẾT KẾ
├── Nội dung thay đổi: [...]
├── Lý do: [...]
├── Ảnh hưởng kỹ thuật: [...]
├── Ảnh hưởng tiến độ: [...]
└── Yêu cầu phê duyệt: [Đồng ý / Không đồng ý]
```

#### 2.3.2 Phương pháp thi công
**Ví dụ:**
- "Thi công 2 ca thay vì 1 ca"
- "Đổ bê tông liên tục qua đêm"

---

### 2.4 RFI Kỹ thuật

#### 2.4.1 Phương pháp tính toán
**Ví dụ:**
- "Có đồng ý dùng TCVN 5575:2024 thay vì 2012?"
- "Hệ số tổ hợp tải trọng có đúng không?"

**Xử lý:**
1. Nêu tiêu chuẩn đang dùng
2. Nêu tiêu chuẩn được yêu cầu
3. Đề xuất thống nhất

#### 2.4.2 Chi tiết liên kết
**Ví dụ:**
- "Bu lông M20 hay M24?"
- "Chiều dài đường hàn bao nhiêu?"

---

## 3. RFI Response Checklist

Khi nhận phản hồi RFI, kiểm tra:

- [ ] Đã trả lời tất cả câu hỏi cụ thể?
- [ ] Có đủ căn cứ tiêu chuẩn?
- [ ] Thông tin mới có mâu thuẫn với tài liệu khác?
- [ ] Cần cập nhật tài liệu nào?
- [ ] Ai chịu trách nhiệm cập nhật?

---

## 4. RFI Closure Criteria

RFI được đóng khi:

1. **Đủ thông tin:** Tất cả câu hỏi đã được trả lời
2. **Đã xác nhận:** Người có thẩm quyền đã duyệt
3. **Đã cập nhật:** Tài liệu liên quan đã được sửa (nếu cần)
4. **Đã thông báo:** Các bên liên quan đã biết

---

*Cập nhật: 2026-08-30*
