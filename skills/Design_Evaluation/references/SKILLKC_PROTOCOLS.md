<!-- REFERENCE FILE — Chỉ đọc khi cần protocol cụ thể. KHÔNG đọc mặc định. -->
<!-- Kích hoạt: Khi User yêu cầu phân tích NCR, so sánh phương án, phân tích tải trọng chi tiết, tích hợp hình ảnh. -->

# SKILLKC — Protocols Chi Tiết

## Rule 11: NCR Auto-Classification (Phân loại Sự cố Tự động)
Khi phát hiện sai lệch thi công, bắt buộc phân loại ngay:
- `CRITICAL`: Ảnh hưởng trực tiếp đến an toàn kết cấu → **Yêu cầu dừng thi công, báo cáo khẩn ngay**.
- `MAJOR`: Không phù hợp tiêu chuẩn nhưng chưa nguy hiểm tức thời → Yêu cầu phương án xử lý trong 48h.
- `MINOR`: Sai lệch trong phạm vi dung sai cho phép → Ghi nhận, chấp nhận có điều kiện.

---

## Rule 12: 3-Discipline Warning Protocol (Cảnh báo 3 Bộ môn)
Khi đề xuất thay đổi tiết diện dầm, vách, cột, hoặc cao độ sàn:
- ⚠️ `[KC→KT]` Kiểm tra: Chiều cao thông thủy phòng/không gian có bị ảnh hưởng không?
- ⚠️ `[KC→MEP]` Kiểm tra: Không gian đi ống/máng cáp điện có đủ sau khi thay đổi không?
- ⚠️ `[KC→Kiến trúc]` Kiểm tra: Hoàn thiện nội thất, mặt tiền có bị ảnh hưởng về cao độ/hình thức không?

---

## Rule 13: Mandatory Quantitative Analysis Protocol

**a) Input Data Table** — Trước khi tính toán, lập bảng:
```
| Thông số         | Ký hiệu | Giá trị | Đơn vị | Nguồn dữ liệu          |
|------------------|---------|---------|--------|-------------------------|
| Chiều dài nhịp   | L       | 6000    | mm     | Bản vẽ KC-01 Rev.02     |
| Cấp bê tông      | B       | B25     | -      | Thuyết minh trang 15    |
| Hoạt tải sàn     | p       | 2.0     | kN/m²  | TCVN 2737:2023, Bảng 3  |
```

**b) Calculation Chain** — Mỗi kiểm tra trình bày đủ 6 bước:
1. **Nguyên lý** (giải thích bằng 1-2 câu tại sao cần kiểm tra mục này, cơ chế phá hoại là gì — VD: "Dầm có thể phá hoại do uốn khi moment tác dụng vượt khả năng chịu của tiết diện thép chịu kéo.")
2. **Công thức** (ghi rõ tên công thức, điều khoản tiêu chuẩn)
3. **Thay số** (thay giá trị cụ thể vào công thức, kèm đơn vị)
4. **Kết quả** (giá trị tính được)
5. **So sánh** (giá trị tính vs giá trị cho phép)
6. **Kết luận** (✅ ĐẠT / ❌ KHÔNG ĐẠT, kèm η và nhận xét ngắn về dự trữ an toàn hoặc cần thiết kế lại)

**c) Utilization Ratio** — Bắt buộc tính `η = Giá trị tính / Giá trị cho phép × 100%`:
- `η ≤ 70%`: 🟢 An toàn, có dư (xem xét VE tối ưu)
- `70% < η ≤ 90%`: 🟡 Đạt, hợp lý
- `90% < η ≤ 100%`: 🟠 Đạt nhưng sát ngưỡng — cần lưu ý
- `η > 100%`: 🔴 KHÔNG ĐẠT — yêu cầu điều chỉnh thiết kế

---

## Rule 14: Step-by-Step Load Analysis (Phân tích Tải trọng Từng bước)

**a) Bảng Tổ hợp Tải trọng** theo TCVN 2737:2023:
```
| Tổ hợp | Tĩnh tải (γ×G) | Hoạt tải (γ×Q) | Gió (γ×W) | Động đất (γ×E) | Ghi chú            |
|--------|----------------|----------------|-----------|----------------|---------------------|
| TH1    | 1.1×G          | 1.2×Q          | -         | -              | TTGH I - Cơ bản     |
| TH2    | 1.1×G          | 0.9×Q          | 1.3×W     | -              | TTGH I - Gió kết hợp|
| TH3    | 1.0×G          | 0.8×Q          | -         | 1.0×E          | TTGH I - Động đất   |
| TH4    | 1.0×G          | 1.0×Q          | -         | -              | TTGH II - Sử dụng   |
```

**b)** Highlight tổ hợp bất lợi nhất.

**c)** Dùng Mermaid hoặc gọi `Technical_Illustrator` vẽ biểu đồ M, V, N. Nếu dầm liên tục → vẽ moment envelope.

**d) Động đất** (khi áp dụng — TCVN 9386:2012):
- Xác định `agR`, `γI`, loại nền đất.
- Phổ phản ứng `Sd(T)` theo Điều 3.2.2.5.
- Kiểm tra tỷ số khối lượng tham gia ≥ 90%.

---

## Rule 15: Image Integration Protocol

**Trường hợp BẮT BUỘC gọi Technical_Illustrator:**

| Loại phân tích | MODE | Loại ảnh yêu cầu |
|---|---|---|
| Chi tiết liên kết (bu lông, hàn, neo) | MODE 2D (Python) | Mặt cắt 2D chi tiết |
| Bố trí cốt thép (cột, dầm, sàn) | MODE 2D (Python) | Mặt cắt + mặt bằng bố trí |
| Phương án tổng thể (khung, giàn) | MODE 3D (AI Render) | Phối cảnh 3D |
| So sánh phương án | MODE 2D (Python) | Biểu đồ radar + bar chart |
| Biện pháp thi công | MODE 3D (AI Render) | Sơ đồ minh họa thi công |

**Quy tắc nhúng ảnh:**
1. Sau khi tạo ảnh → BẮT BUỘC kiểm tra `list_dir` / `view_file`.
2. Dùng ĐƯỜNG DẪN TUYỆT ĐỐI: `![Hình X.Y — Mô tả](g:/full/path/file.png)`.
3. Nếu đưa vào artifact `.md` → PHẢI copy vào thư mục artifacts trước.
4. KHÔNG BAO GIỜ dùng đường dẫn tương đối.
5. Mỗi ảnh phải có Figure Number và Caption.

---

## Rule 16: Detailed Comparison Matrix (So sánh Phương án)

**a) Tối thiểu 8 tiêu chí đánh giá:**
```
| STT | Tiêu chí              | Trọng số | PA 1 (★) | PA 2 (★) | PA 3 (★) |
|-----|----------------------|----------|----------|----------|----------|
| 1   | Khả năng chịu lực    | 20%      | ★★★★☆    | ★★★★★    | ★★★☆☆    |
| 2   | Chi phí vật liệu     | 15%      | ★★★☆☆    | ★★★★☆    | ★★★★★    |
| 3   | Chi phí nhân công    | 10%      | ★★★★☆    | ★★★☆☆    | ★★★★★    |
| 4   | Tiến độ thi công     | 15%      | ★★★★☆    | ★★★☆☆    | ★★★★★    |
| 5   | Rủi ro thi công      | 10%      | ★★★★☆    | ★★★☆☆    | ★★★★☆    |
| 6   | Bảo trì vận hành     | 10%      | ★★★★☆    | ★★★★★    | ★★★☆☆    |
| 7   | Mỹ quan kiến trúc    | 10%      | ★★★☆☆    | ★★★★★    | ★★★★☆    |
| 8   | Phù hợp TCVN         | 10%      | ★★★★★    | ★★★★★    | ★★★★★    |
|     | **TỔNG (gia quyền)** |          | **3.75** | **4.05** | **4.00** |
```

**b)** Gọi `Technical_Illustrator` → `draw_comparison_chart.py` → input JSON:
```json
{
  "categories": ["Chịu lực", "CP vật liệu", "CP nhân công", "Tiến độ", "Rủi ro", "Bảo trì", "Mỹ quan", "TCVN"],
  "plans": { "PA1": [4,3,4,4,4,4,3,5], "PA2": [5,4,3,3,3,5,5,5], "PA3": [3,5,5,5,4,3,4,5] }
}
```

**c)** Kết luận: *"Căn cứ kết quả đánh giá đa tiêu chí, Phương án [X] được KHUYẾN NGHỊ với tổng điểm gia quyền [Y]/5.0, vượt trội ở các tiêu chí [Z1, Z2, Z3]."*

---

## Special Skills Chi tiết

### 🔍 Forensic Structural Review (Giám định Kết Cấu Pháp lý)
Khi xử lý tranh chấp kỹ thuật, thực hiện đủ 4 bước:
1. Trích dẫn chính xác điều khoản tiêu chuẩn áp dụng (số điều, số bảng, năm ban hành).
2. Lập bảng so sánh: **"Thiết kế gốc | Thực tế thi công | Yêu cầu tiêu chuẩn"**.
3. Kết luận rõ ràng: ai có lỗi, mức độ ảnh hưởng, hướng bồi thường/xử lý.
4. Tuyệt đối không thiên vị — chỉ căn cứ số liệu và tiêu chuẩn.

### 📊 Phased Risk Intelligence (Cảnh báo Rủi ro Theo Giai đoạn)
Output bắt buộc dạng bảng:
```
| Giai đoạn   | Rủi ro nhận diện                        | Xác suất    | Hậu quả      | Biện pháp phòng ngừa                  |
|-------------|------------------------------------------|-------------|--------------|---------------------------------------|
| Thiết kế    | Thiếu kiểm tra tổ hợp tải trọng bất lợi | Cao         | Nghiêm trọng | Bổ sung Load Combination theo TCVN    |
| Thi công    | Sụt lún móng do thi công mùa mưa        | Trung bình  | Nghiêm trọng | Gia tải thử và quan trắc lún liên tục |
| Khai thác   | Nứt bê tông cột tầng hầm do co ngót     | Trung bình  | Trung bình   | Bố trí khe co giãn + kiểm tra định kỳ |
```

### 📚 Cross-Standard Reconciliation (Đối chiếu Đa tiêu chuẩn Tự động)
Tự động tra cứu **đồng thời** TCVN + Eurocode + ACI, so sánh kết quả, khuyến nghị tiêu chuẩn nào phù hợp nhất. Trình bày bảng 3 cột.

### 📣 Adaptive Reporting Mode
Xem chi tiết: `SKILL_REPORT.md — Rule: Adaptive Reporting`.
