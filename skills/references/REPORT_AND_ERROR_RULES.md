## 13. Minimum Narrative Depth (Độ sâu Diễn giải Tối thiểu)

Mọi Tờ trình/Báo cáo chính thức (Mode 2: .docx, Mode 1: .md) khi xuất file PHẢI đạt tổng nội dung phần thuyết minh **≥ 800 từ** (không tính bảng, heading, caption, Approval Matrix).
Nếu bản nháp dưới ngưỡng → AI phải tự bổ sung diễn giải theo thứ tự ưu tiên:

1. Bối cảnh & Lý do trình duyệt (tại sao bây giờ?)
2. Đánh giá hiện trạng chi tiết (cái gì hư? hư đến mức nào?)
3. Phương án đã xem xét và loại bỏ (tại sao không chọn?)
4. Diễn giải chi tiết phương án đề xuất (làm gì? bằng gì? bao nhiêu?)

---

## 14. Mandatory Illustration Integration (Bắt buộc Hình ảnh Minh họa)

Mọi Tờ trình chính thức BẮT BUỘC đính kèm tối thiểu **2 hình ảnh minh họa**:

- **Hình 1**: Mặt cắt chi tiết 2D (MODE 2D — Python) hoặc ảnh hiện trạng.
- **Hình 2**: Phối cảnh thiết kế 3D (MODE 3D — AI Render) hoặc biểu đồ so sánh phương án.
- Mỗi hình phải có **số hiệu** (Hình 1, Hình 2...) và **caption** mô tả.
- Ngoại lệ: Tờ trình chỉ liên quan đến phê duyệt hành chính (không có nội dung kỹ thuật) thì không bắt buộc.

---

## 15. Định dạng Version Control cho File Output

Quy tắc đặt tên file output chính thức:
`[MãDA]_[LoạiVB]_[GiaiDoan]_v[N]_[YYYYMMDD].[đuôi file]`
Ví dụ: `DuAnA_ToTrinh_BVTC_v2_20260625.docx`

Khi xuất lại file đã tồn tại:

- KHÔNG ghi đè file cũ — luôn tạo version mới (v1 → v2 → v3...)
- Ghi 1 dòng vào file `_CHANGELOG.md` cùng thư mục, format:
  `[YYYY-MM-DD HH:MM] v[N] — [Lý do sửa] — [Người yêu cầu]`

---

## 16. Tiết kiệm Token — Lazy Load Protocol

**Chỉ đọc file phụ khi thực sự cần thiết:**

- Tra tiêu chuẩn: Dùng `grep_search` với từ khóa đặc thù trước khi đọc PDF lớn. Đọc `INDEX_QUICK.md` trước `INDEX.md`.
- Vẽ MODE 3D: Đọc `MODE_3D_GUIDE.md` — KHÔNG đọc `MODE_2D_GUIDE.md`.
- Vẽ MODE 2D: Đọc `MODE_2D_GUIDE.md` — KHÔNG đọc `MODE_3D_GUIDE.md`.
- Xuất báo cáo: Đọc `SKILL_REPORT.md` — KHÔNG đọc `SKILLKC.md`.
- Tính toán kỹ thuật: Đọc `SKILLKC.md` — KHÔNG đọc `SKILL_REPORT.md`.

---

## 17. Hệ thống Mã Lỗi Chuẩn hóa (Error Code System)

| Code | Ý nghĩa | Hành động |
| -------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `E001` | Input validation failed | Hiển thị usage + ví dụ tham số hợp lệ |
| `E002` | Missing required data | Liệt kê các field còn thiếu, ghi `Data Missing:` |
| `E003` | Calculation inconclusive | Ghi Scope Limitation, không kết luận ĐẠT |
| `E004` | Standard conflict detected | Kích hoạt SKILL_VERIFY xử lý mâu thuẫn tiêu chuẩn |
| `E005` | Handoff schema invalid | Reject handoff, yêu cầu source skill gửi lại (xem `SKILL_BRIDGE.md §4.3`) |
| `E006` | Handoff missing required field | Block execution, request data từ upstream skill |
| `E007` | Circular dependency detected | Block loop, notify User, log event |
| `W001` | Approaching threshold (>90%) | Cảnh báo sát giới hạn nhưng không block |
| `W002` | η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `W003` | Low confidence output | Đánh dấu `[PENDING_VERIFICATION]`, gửi SKILL_VERIFY |
| `I001` | Info — η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `I002` | Auto-trigger fired | Log trigger execution, notify next skill |

---

## 17b. Confidence Level Handling

| Level | Score Range | Meaning | Action |
| ---------- | ----------- | -------------------------- | --------------------------------------- |
| `HIGH` | ≥ 0.85 | Đầy đủ data, validated | Tiếp tục bình thường |
| `MEDIUM` | 0.60 - 0.84 | Thiếu một số data | AUTO gửi SKILL_VERIFY |
| `LOW` | < 0.60 | Thiếu critical data | **BLOCK** xuất file, notify User |

### Confidence Score Calculator

Tool: `_SHARED/SHARED_CONTEXT/confidence_score.py`

**5 Factors trọng số:**

| Factor | Weight | Check |
| --------------------------- | ------ | ------------------------------------------- |
| `data_completeness` | 25% | Required fields present |
| `input_quality` | 20% | Material grades, dimensions in valid ranges |
| `standard_compliance` | 20% | Standards properly cited |
| `calculation_consistency` | 20% | Internal consistency of logs |
| `source_reliability` | 15% | Data source (measured/calculated/estimated) |

**Usage:**

```bash
python _SHARED/SHARED_CONTEXT/confidence_score.py \
    --input design_output.json \
    --verbose \
    --output confidence_result.json
```

**Integration:**

- Mọi skill output khi export phải ghi `confidence_level` vào JSON
- Confidence được tự động check trước khi xuất file chính thức
- LOW confidence → block export → notify User

---

