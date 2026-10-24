---
name: SKILL_FORENSIC
version: 1.2.0
last_updated: 2026-09-27
description: "Chuyên gia Điều tra Sự cố Kết cấu AI: Phân tích nguyên nhân sự cố (sập, nứt, lún, biến dạng), tính toán ngược để xác định tải trọng thực tế, so sánh với thiết kế ban đầu, đưa ra giả thuyết nguyên nhân xếp hạng theo xác suất, đề xuất thí nghiệm kiểm chứng và phương án xử lý. Kích hoạt khi: sự cố, sập, nứt nghiêm trọng, điều tra nguyên nhân, NCR nghiêm trọng, phân tích hư hỏng, back-calculation."
---

# SKILL_FORENSIC — Điều tra Sự cố Kết cấu

## Tổng quan

**SKILL_FORENSIC** là module chuyên sâu cho **Structural Forensic Engineering** (Kỹ thuật Điều tra Kết cấu) — phân tích nguyên nhân gốc rễ của sự cố kết cấu theo phương pháp khoa học hình sự.

Khác với `Design_Evaluation` (review thiết kế) và `Structural_Design_Engineer` (tính toán thiết kế mới), module này **làm việc ngược** (reverse engineering) từ hiện trạng hư hỏng để tìm nguyên nhân.

---

## Kích hoạt (Trigger Keywords)

- **"sự cố"**, **"sập"**, **"nứt nghiêm trọng"**, **"điều tra nguyên nhân"**
- **"NCR cấp nghiêm trọng"**, **"phân tích hư hỏng"**, **"back-calculation"**
- **"tại sao ... bị ..."**, **"đánh giá hiện trạng sau sự cố"**
- **"lún bất thường"**, **"biến dạng quá mức"**, **"phá hoại"**

---

## Quy trình Chuẩn (7 Bước)

### BƯỚC 1: Thu thập Chứng cứ (Evidence Collection)

**Checklist bắt buộc:**
- [ ] Ảnh hiện trường (góc chụp đủ: toàn cảnh, cận cảnh vết nứt, chi tiết liên kết)
- [ ] Kích thước vết nứt (mm), hướng, mô hình phân bố
- [ ] Đo đạc biến dạng (độ võng, độ lệch, độ mở khe)
- [ ] Bản vẽ thiết kế gốc (nếu có)
- [ ] Mẫu vật liệu (bê tông, thép) nếu khả thi
- [ ] Nhật ký thi công (phương pháp đổ bê tông, trình tự tháo dỡ giàn giáo)
- [ ] Điều kiện môi trường (thời tiết, nhiệt độ, tải trọng lúc sự cố xảy ra)

**Script hỗ trợ:** `scripts/evidence_checklist_generator.py`

---

### BƯỚC 2: Mô hình hóa Hiện trạng (As-Built Modeling)

**Mục tiêu:** Dựng lại mô hình kết cấu thực tế (không phải theo thiết kế)

**Công cụ:**
- Đo đạc thực tế tiết diện (có thể nhỏ hơn thiết kế)
- Kiểm tra cốt thép bằng máy dò (số lượng, đường kính, lớp bảo vệ)
- Lấy mẫu bê tông (mác thực tế có thể thấp hơn thiết kế)

**Output:** File ETABS/SAP2000 hoặc JSON chứa geometry thực tế

---

### BƯỚC 3: Back-Calculation (Tính toán ngược)

**Nguyên lý:** Từ vết nứt/biến dạng đo được → suy ra tải trọng/ứng suất thực tế gây ra

**Phương pháp:**

#### 3.1. Từ độ võng → Tải trọng
```
Công thức dầm đơn giản:
δ = (5 × q × L⁴) / (384 × E × I)

→ q = (384 × E × I × δ) / (5 × L⁴)
```

**Ví dụ:**
- Đo được: δ = 25mm (dầm L=6m)
- E = 30000 MPa (bê tông B25), I = 1.4×10⁹ mm⁴
- → q_thực_tế = 28.5 kN/m
- Thiết kế ban đầu: q_thiết_kế = 20 kN/m
- **→ Kết luận: Quá tải 42.5%**

#### 3.2. Từ bề rộng khe nứt → Ứng suất thép
```
w_crack = β × (σ_s / E_s) × Δ_l

→ σ_s = (w_crack × E_s) / (β × Δ_l)
```

**Script:** `scripts/back_calculation.py`

---

### BƯỚC 4: So sánh với Thiết kế ban đầu (Design vs Actual)

Lập bảng so sánh:

| Thông số | Thiết kế | Thực tế đo | Chênh lệch | Ảnh hưởng |
|----------|----------|------------|------------|-----------|
| Tiết diện dầm | 400×700 | 380×680 | -5.7% | Giảm M_Rd 11% |
| Số thanh thép | 6Φ22 | 6Φ20 | -17.4% diện tích | Giảm khả năng chịu uốn |
| Mác bê tông | B25 | B20 (mẫu khoan) | -20% R_b | Giảm bền nén |
| Tải trọng sử dụng | 5 kPa | 8.5 kPa (ước tính) | +70% | Vượt thiết kế |

---

### BƯỚC 5: Giả thuyết Nguyên nhân (Hypotheses Ranking)

Liệt kê TẤT CẢ nguyên nhân có thể, xếp hạng theo **xác suất** (dựa trên chứng cứ):

**Mẫu Output:**

```json
{
  "Hypotheses": [
    {
      "Rank": 1,
      "Cause": "Quá tải do chất hàng vượt thiết kế",
      "Probability": "85%",
      "Evidence": [
        "Back-calculation cho q = 28.5 kN/m (thiết kế 20 kN/m)",
        "Nhân chứng xác nhận chất hàng nặng 1 tuần trước sự cố",
        "Vết nứt tại giữa nhịp (đặc trưng quá tải uốn)"
      ],
      "Contradictions": []
    },
    {
      "Rank": 2,
      "Cause": "Bê tông không đạt mác thiết kế",
      "Probability": "60%",
      "Evidence": [
        "Mẫu khoan cho f_c = 18 MPa (thiết kế 25 MPa)",
        "Nhật ký thi công thiếu báo cáo thí nghiệm mẫu"
      ],
      "Contradictions": [
        "Nếu chỉ do bê tông yếu, nứt sẽ xuất hiện trước đó"
      ]
    },
    {
      "Rank": 3,
      "Cause": "Tháo giàn giáo quá sớm",
      "Probability": "30%",
      "Evidence": [
        "Nhật ký ghi tháo giàn giáo ngày 18 (14 ngày tuổi bê tông)"
      ],
      "Contradictions": [
        "TCVN yêu cầu 28 ngày, nhưng 14 ngày vẫn đạt ~80% cường độ, không gây sập nếu không quá tải"
      ]
    }
  ],
  "Most_Likely_Scenario": "Kết hợp Hypothesis #1 (quá tải chính) + #2 (bê tông yếu phụ) → Hiệp đồng gây sập."
}
```

**Quy tắc phân tích:**
- Nguyên nhân có xác suất > 70% → **Nguyên nhân chính**
- Nguyên nhân 40-70% → **Nguyên nhân góp phần**
- Nguyên nhân < 40% → **Loại trừ** nếu có mâu thuẫn

---

### BƯỚC 6: Đề xuất Thí nghiệm Kiểm chứng (Validation Tests)

Mỗi giả thuyết phải đi kèm **thí nghiệm xác minh**:

| Giả thuyết | Thí nghiệm đề xuất | Chi phí ước tính | Thời gian |
|------------|-------------------|------------------|-----------|
| Bê tông không đạt mác | Khoan mẫu core test (5 vị trí) | 15M VNĐ | 7 ngày |
| Cốt thép thiếu/sai vị trí | GPR scan toàn bộ dầm | 25M VNĐ | 3 ngày |
| Quá tải | Cân đo thiết bị hiện có | 2M VNĐ | 1 ngày |
| Chất lượng hàn kém | UT/RT kiểm tra mối hàn | 18M VNĐ | 5 ngày |

**Ưu tiên:** Làm thí nghiệm chi phí thấp, thời gian nhanh trước

---

### BƯỚC 7: Phương án Xử lý (Remedial Solutions)

**3 cấp độ xử lý:**

#### Cấp 1: Khẩn cấp (Emergency)
- **Mục tiêu:** Ngăn sập hoàn toàn, bảo vệ sinh mạng
- **Biện pháp:** Chống đỡ tạm, giảm tải, cấm người ra vào
- **Thời gian:** Trong vòng 24h

#### Cấp 2: Tạm thời (Temporary)
- **Mục tiêu:** Duy trì khả năng sử dụng hạn chế
- **Biện pháp:** Tăng cường cục bộ (dầm phụ, cột chống), giới hạn tải trọng
- **Thời gian:** 1-2 tuần

#### Cấp 3: Vĩnh viễn (Permanent)
- **Mục tiêu:** Phục hồi toàn bộ khả năng chịu lực
- **Biện pháp:** 
  - Dán thép, dán FRP
  - Tăng tiết diện (bê tông phun, bọc thép)
  - Thay thế cấu kiện
- **Thời gian:** 1-3 tháng

**Script:** `scripts/remedial_solution_generator.py`

---

## Cấu trúc Thư mục

```
SKILL_FORENSIC/
├── SKILL.md                            ← BẠN ĐANG Ở ĐÂY
├── scripts/
│   ├── evidence_checklist_generator.py ← Bước 1
│   ├── back_calculation.py             ← Bước 3
│   ├── hypothesis_ranker.py            ← Bước 5
│   └── remedial_solution_generator.py  ← Bước 7
├── templates/
│   ├── forensic_report_template.docx   ← Báo cáo điều tra sự cố
│   └── NCR_critical_template.docx      ← NCR cấp nghiêm trọng
├── references/
│   ├── failure_modes_database.json     ← Database 50+ chế độ phá hoại
│   └── case_studies/                   ← 20 vụ sự cố thực tế đã phân tích
└── README.md
```

---

## Failure Modes Database (Cơ sở dữ liệu Chế độ Phá hoại)

**50+ chế độ phá hoại phổ biến**, mỗi chế độ có:
- Mô tả
- Đặc điểm vết nứt
- Nguyên nhân thường gặp
- Ảnh minh họa
- Phương pháp xử lý

**Ví dụ:**

### FM-01: Flexural Failure (Phá hoại uốn)
- **Vết nứt:** Dọc, vuông góc trục dầm, tại giữa nhịp, mở rộng từ đáy lên
- **Nguyên nhân:** Quá tải uốn, thiếu cốt thép
- **Xử lý:** Dán thép đáy dầm, giảm tải

### FM-05: Punching Shear (Phá hoại đục thủng)
- **Vết nứt:** Hình nón 45° quanh cột, xuyên suốt bản
- **Nguyên nhân:** Tải trọng tập trung lớn, bản mỏng
- **Xử lý:** Tăng cường bản bằng vòng thép hoặc CFRP

---

## Quy tắc Đặc biệt

### Rule 1: No Speculation Without Evidence
Nghiêm cấm đưa ra kết luận không có chứng cứ. Mọi giả thuyết phải liệt kê **Evidence** cụ thể.

### Rule 2: Multiple Hypotheses Mandatory
Bắt buộc đưa ra **tối thiểu 3 giả thuyết** nguyên nhân, kể cả khi 1 nguyên nhân có vẻ rõ ràng. Mục đích: tránh confirmation bias.

### Rule 3: Contradictions Must Be Addressed
Nếu giả thuyết có **Contradictions** (mâu thuẫn với chứng cứ khác), phải giải thích hoặc hạ xếp hạng.

### Rule 4: Legal Disclaimer
Mọi báo cáo forensic phải có disclaimer:

> *Báo cáo này mang tính tham khảo kỹ thuật. Kết luận cuối cùng về nguyên nhân sự cố phải được xác định bởi Hội đồng Giám định độc lập có thẩm quyền. Trợ lý AI không chịu trách nhiệm pháp lý.*

---

## Workflow End-to-End Example

**User:** *"Dầm B1 bị nứt nghiêm trọng sau 2 tháng sử dụng. Vết nứt dọc, giữa nhịp, rộng 2mm. Có ảnh đính kèm."*

**AI:**
1. Kích hoạt `SKILL_FORENSIC`
2. Chạy `evidence_checklist_generator.py` → Hỏi User bổ sung: bản vẽ gốc? nhật ký thi công? tải trọng hiện tại?
3. User cung cấp: Bản vẽ có, tải trọng 25 kN/m (thiết kế 20 kN/m)
4. Chạy `back_calculation.py` từ độ võng (nếu có đo)
5. So sánh: Tải trọng thực tế > thiết kế 25%
6. Chạy `hypothesis_ranker.py`:
   - Hypothesis #1 (85%): Quá tải
   - Hypothesis #2 (50%): Bê tông yếu
   - Hypothesis #3 (20%): Sai tiết diện thi công
7. Đề xuất thí nghiệm: Core test (7 ngày, 15M)
8. Đề xuất xử lý:
   - Khẩn cấp: Chống đỡ tạm, giảm tải xuống 15 kN/m
   - Vĩnh viễn: Dán thép đáy dầm, tăng cường khả năng 30%
9. Xuất `forensic_report_template.docx`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-04 | Initial release - 7 bước chuẩn + 50 failure modes |
