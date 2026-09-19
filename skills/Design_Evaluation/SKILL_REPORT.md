---
name: SKILL_REPORT
version: 2.2.0
last_updated: 2026-08-31
description: "Module xuất báo cáo/tờ trình/Word/PDF/HTML/Excel: 4 luồng — DeepResearch report (.md), tờ trình Word theo template (.docx), MD→DOCX/PDF, **Unified Dispatcher** (5 audience profiles, MD/DOCX/HTML). Kích hoạt khi: xuất báo cáo, tờ trình, xuất Word, export PDF, xuất Excel, audience-aware report."
---

# SKILL_REPORT — Kỹ năng Xuất Báo cáo & Tờ Trình

<!-- MODULE REFERENCE FILE — Đọc khi User yêu cầu xuất báo cáo/tờ trình/Word. -->
<!-- KHÔNG đọc file này khi chỉ cần phân tích kỹ thuật (dùng SKILLKC.md). -->

## Tổng quan

**SKILL_REPORT** là module **chỉ xuất báo cáo** — không tự tính toán lại. Nhận dữ liệu từ SKILLKC (qua JSON handoff hoặc từ User) và đóng gói thành:

| Mode | Output | Trigger |
|------|--------|---------|
| **REPORT MODE 1 — DeepResearch** | File `.md` báo cáo Markdown chuyên sâu | *"báo cáo, DeepResearch, phân tích chuyên sâu"* |
| **REPORT MODE 2 — Tờ Trình Word** | File `.docx` theo form mẫu công ty | *"tờ trình, xuất Word, trình duyệt, gửi sếp"* |
| **REPORT MODE 3 — Trình chiếu PDF** | File `.pdf` chuyên nghiệp | *"xuất PDF, in báo cáo, trình chiếu"* |
| **REPORT MODE 4 — Unified Dispatcher** ⭐ | `.md` / `.docx` / `.html` — **audience-aware** | *"báo cáo đầy đủ", "xuất nhiều format", "cho chủ đầu tư/kỹ sư/nhà thầu"* |

---

## REPORT MODE 1: DeepResearch Report (.md)

### Cấu trúc báo cáo Markdown bắt buộc

| Mục | Yêu cầu độ sâu tối thiểu (bắt buộc) |
|---|---|
| 1. Tóm tắt Điều hành | ≤ 5 dòng (giữ nguyên — mục duy nhất cố ý ngắn) |
| 2. Thông tin Dự án | Đầy đủ: tên dự án, hạng mục, giai đoạn TK, ngày, đơn vị thiết kế/thẩm tra nếu có |
| 3. Cơ sở Pháp lý & Tiêu chuẩn | Liệt kê dạng bảng: mỗi tiêu chuẩn 1 dòng — Mã + Năm + Phạm vi áp dụng trong hồ sơ này (không gộp chung 1 câu) |
| 4. Bảng Tổng hợp & Tra cứu Tiêu chuẩn Thiết kế (Standard Traceability Matrix) | BẮT BUỘC sử dụng format bảng dưới đây cho MỌI thông số thiết kế, tải trọng, và vật liệu. Khai báo rõ "Toạ độ tra cứu" để kỹ sư thẩm tra dễ kiểm chứng. |
| 5. Luận giải kỹ thuật (Bắt buộc 4 tầng) | Mỗi kết luận quan trọng PHẢI trình bày đủ 4 tầng theo thứ tự dưới đây. KHÔNG được bỏ tầng nào. Xem chi tiết bên dưới bảng. |
| 6. Đánh giá Rủi ro | Mỗi rủi ro nêu: mô tả, mức độ (Minor/Major/Critical), nguyên nhân, đề xuất xử lý — dạng bảng, không gộp 1 câu |
| 7. Khuyến nghị & Kết luận | Có thể ngắn, nhưng phải tham chiếu lại đúng số liệu đã nêu ở mục 4-5, không lặp nguyên văn |
| 8. Bảng Trách nhiệm & Phê duyệt | Giữ nguyên theo mẫu hiện tại |

**Cấu trúc 4 tầng Luận giải Kỹ thuật (Bắt buộc cho Mục 5):**

- **Tầng 1 — NGUYÊN LÝ CƠ HỌC**: Giải thích bằng ngôn ngữ đơn giản cơ chế làm việc vật lý của cấu kiện/hệ kết cấu. VD: "Dầm liên tục 3 nhịp phân phối moment âm tại gối trung gian lớn hơn moment dương giữa nhịp → thép chịu kéo tập trung ở mặt trên gối." Viết ngắn gọn theo Rule C18 (SKILLKC.md), tối đa 3 câu.
- **Tầng 2 — PHÂN TÍCH ĐỊNH LƯỢNG**: Trình bày chuỗi tính toán theo Rule C15 (Công thức gốc → Thế số → Kết quả & η). Nếu dùng Deterministic Math Engine (Rule C14), dẫn trực tiếp kết quả từ `Calculation_Logs`.
- **Tầng 3 — ĐỐI CHIẾU TIÊU CHUẨN**: Dẫn chiếu Citation Object đầy đủ 4 thành phần (Mã — Năm — Điều/Bảng — Trích yếu). Nếu có mâu thuẫn giữa các tiêu chuẩn → nêu rõ sự khác biệt và lý do chọn tiêu chuẩn nào.
- **Tầng 4 — KẾT LUẬN & GIẢI PHÁP TỐI ƯU**: Kết luận Đạt/Không đạt kèm η. Nếu η > 90% → đề xuất biện pháp cải thiện. Nếu η ≤ 70% → đề xuất Value Engineering giảm tiết diện/vật liệu. Nếu có nhiều phương án → giải thích tại sao loại các phương án khác bằng số liệu cụ thể, không bằng nhận xét chung chung.

**Format Bảng Tra Cứu (Mẫu Bắt Buộc cho SKILL_REPORT):**

| Thông số / Hạng mục kiểm tra | Giá trị thiết kế | Công thức áp dụng / Căn cứ | Tiêu chuẩn / Quy chuẩn | Vị trí tra cứu (Mục / Bảng / Trang) | Kết luận |
|------------------------------|------------------|-----------------------------|------------------------|-------------------------------------|----------|
| Hệ số tin cậy gió (γ_f) | 1.2 | W_c = γ_f × W_tc | TCVN 2737:2023 | Điều 10.2, Bảng 4, Tr. 45 | Đạt |
| Cường độ chịu nén BT (R_b) | 14.5 MPa | Cấp độ bền B22.5 | TCVN 5574:2018 | Bảng 7, Trang 23 | Hợp lệ |
| Độ võng cho phép (f/L) | 1/250 | Δ ≤ [Δ] | TCVN 5575:2024 | Điều 8.3, Bảng 12, Tr. 50 | Đạt (η=82%) |

*Quy tắc Bảng:* Nếu thiếu thông tin số Trang hoặc Bảng, AI phải điền "N/A" hoặc "Cần user bổ sung", tuyệt đối không tự chế số trang.

### Rule: Adaptive Reporting Mode

Tự động điều chỉnh mức độ kỹ thuật theo đối tượng nhận:

| Đối tượng | Mức độ kỹ thuật | Trọng tâm |
|---|---|---|
| **Chủ đầu tư / Ban lãnh đạo** | Thấp — tóm tắt rủi ro, chi phí, tiến độ | Executive Summary, Khuyến nghị |
| **Tư vấn Thiết kế** | Cao — công thức, điều khoản, số liệu đầy đủ | Calculation Chain, Cross-Standard |
| **Nhà thầu Thi công** | Trung bình — biện pháp xử lý, quy trình | Constructability, NCR |
| **Cơ quan Thẩm tra / Nhà nước** | Rất cao — trích dẫn đầy đủ điều khoản | Compliance, Legal Reference |

**Lưu ý**: Dù điều chỉnh mức độ kỹ thuật theo đối tượng nhận, số liệu gốc (Utilization Ratio, kết quả tính toán) PHẢI giữ nguyên giá trị ở mọi phiên bản báo cáo — chỉ thay đổi cách trình bày/diễn giải, không làm tròn khác nhau giữa các bản gửi cho đối tượng khác nhau.

**Bắt buộc với Báo cáo Chủ đầu tư / Ban lãnh đạo**: Phải có **Executive Dashboard (Bảng điều khiển vĩ mô)** ở ngay đầu trang 1, bao gồm:
1. **Delta Chi phí (Variance):** Tăng/giảm bao nhiêu tỷ VNĐ so với Budget được duyệt ban đầu.
2. **Tác động Tiến độ (Schedule Impact):** Chậm/nhanh bao nhiêu ngày (Critical Path).
3. **Chỉ số NLA Efficiency:** Tỷ lệ Diện tích sử dụng / Diện tích sàn xây dựng (%).
4. **Quyết định Yêu cầu (Call to Action):** Cần GĐ Ban XD hoặc Tổng GĐ ký duyệt những điểm mấu chốt nào? (Yes/No rõ ràng).

**Quy tắc nhận diện tự động**:
- Khi User yêu cầu xuất báo cáo nhưng KHÔNG nói rõ đối tượng nhận, **MẶC ĐỊNH dùng mức độ kỹ thuật CAO NHẤT (Tư vấn Thiết kế / Cơ quan Thẩm tra)**.
- KHÔNG gọi script `audience_detector.py` trừ khi User yêu cầu rõ "viết cho người ngoài ngành" hoặc "viết cho chủ đầu tư". Điều này đảm bảo báo cáo luôn chi tiết tối đa.

---

## REPORT MODE 2: Tờ Trình Word (.docx)

### Script sử dụng

| Script | Chức năng | Lệnh |
|--------|-----------|------|
| `generate_to_trinh.js` | Tạo Word từ đầu (dữ liệu JSON) — **Luồng 2** | `node scripts/generate_to_trinh.js data.json output.docx` |
| `generate_report.py` | Bơm JSON vào template Word có sẵn — **Luồng 1** | `python scripts/generate_report.py --template templates/BXD-TTTK KT- TO TRINH MAU.docx --data data.json --out output.docx` |
| `md_to_docx_report.js` | Chuyển file .md đã viết → .docx | `node scripts/md_to_docx_report.js input.md output.docx` |

### Cấu trúc Nội dung Tờ Trình BẮT BUỘC (Mode 2)

Phần "Nội dung Tờ trình" trong file Word PHẢI được chia thành các sub-heading rõ ràng (bold, viết hoa) và đạt độ sâu tối thiểu:

| Mục trong Tờ trình | Yêu cầu tối thiểu |
|---------------------|-------------------|
| **1. MỤC TIÊU ĐỀ XUẤT** | ≥ 1 đoạn văn: Quy hoạch tổng thể, mục tiêu chính của phương án |
| **2. BỐI CẢNH & LÝ DO TRÌNH DUYỆT** | ≥ 2 đoạn văn: (1) Tình hình hiện trạng, (2) Lý do cần giải quyết ngay |
| **3. ĐÁNH GIÁ HIỆN TRẠNG** | ≥ 1 bảng phân đoạn (theo vị trí/khu vực), mỗi đoạn có: Hiện trạng + Vấn đề + Mức độ |
| **4. CƠ SỞ TIÊU CHUẨN VÀ QUY CHUẨN THIẾT KẾ** | Bảng ≥ 3 dòng: Mã TC + Năm + Phạm vi áp dụng cụ thể |
| **5. PHƯƠNG ÁN ĐÃ XEM XÉT VÀ LOẠI BỎ** *(mới)* | ≥ 1 đoạn/PA: Mô tả PA + Lý do loại bỏ bằng số liệu (không bằng nhận xét chung) |
| **6. GIẢI PHÁP THIẾT KẾ ĐỀ XUẤT** | ≥ 3 đoạn: (1) Giải pháp kiến trúc, (2) Giải pháp kết cấu/địa kỹ thuật, (3) Thông số vật liệu |
| **7. THUYẾT MINH TÍNH TOÁN** *(nếu có)* | Tách riêng từng cấu kiện, mỗi cấu kiện theo chuỗi 6 bước (Rule C15 mới) |
| **8. HÌNH ẢNH MINH HỌA** | BẮT BUỘC ≥ 2 hình: (1) Mặt cắt chi tiết 2D hoặc ảnh hiện trạng, (2) Phối cảnh 3D hoặc biểu đồ |
| **9. LƯU Ý THI CÔNG** | ≥ 2-3 câu: Các điểm cần giám sát đặc biệt khi thi công |
| **10. KẾT LUẬN VÀ ĐỀ XUẤT** | ≥ 1 đoạn kết luận kỹ thuật + ≥ 1 đoạn đề xuất hành động tiếp theo |

---

## REPORT MODE 3: Trình chiếu PDF (.pdf)

| Script | Chức năng | Lệnh |
|--------|-----------|------|
| `md_to_pdf_report.js` | Chuyển Markdown sang PDF | `node scripts/md_to_pdf_report.js input.md output.pdf` |

### Scan tags của template

```bash
python scripts/generate_report.py --scan "templates/BXD-TTTK KT- TO TRINH MAU.docx"
```

### Mapping JSON → Template Tags (các field bắt buộc)

| JSON Field | Template Tag | Mô tả |
|---|---|---|
| `Ten_Du_An` | `{{TenDuAn}}` | Tên đầy đủ dự án |
| `Hang_Muc` | `{{HangMuc}}` | Hạng mục cụ thể |
| `Giai_Doan_TK` | `{{GiaiDoan}}` | TKCS / TKKT / BVTC / Hoàn công |
| `Ngay` | `{{Ngay}}` | Ngày lập tờ trình |
| `Kien_Nghi` | `{{KienNghi}}` | Nội dung khuyến nghị |
| `Doi_Chieu_Tieu_Chuan_*` | Tùy theo template | Kết quả đối chiếu TCVN |

---

## Approval Matrix (Bắt buộc ở cuối mọi báo cáo)

```
| Trách nhiệm  | Đề xuất              | Kiểm tra          | Phê duyệt           |
|--------------|----------------------|-------------------|---------------------|
| Ý kiến        | Kính trình BLĐ       |                   |                     |
| Chữ ký       |                      |                   |                     |
| Ngày ký      | {{Ngay}}             |                   |                     |
| Họ tên       | [AI / Kỹ sư QLTK]   | [TP. QLTK]        | [GĐ Ban XD]         |
| Chức vụ      | Trợ lý TK AI         | Trưởng phòng QLTK | Giám đốc Ban XD     |
```

**Quy tắc:**

- **Đề xuất**: Luôn ghi rõ "Trợ lý AI — cần người kiểm tra xác nhận trước khi ký".
- **Kiểm tra**: TP.QLTK hoặc chuyên gia kỹ thuật chịu trách nhiệm kỹ thuật.
- **Phê duyệt**: Cấp quản lý có thẩm quyền quyết định.

---

## Rules bắt buộc

1. **Review Gate trước khi xuất**: In tóm tắt kết quả tính toán ra chat → hỏi User: *"Anh/chị có đồng ý với số liệu này để xuất Tờ trình không?"* → Chỉ xuất file khi được xác nhận.
2. **Không tính lại**: SKILL_REPORT **không tự tính toán** — chỉ trích xuất từ JSON handoff của SKILLKC.
3. **Đường dẫn tuyệt đối**: File output phải lưu tại đường dẫn tuyệt đối do User chỉ định.
4. **Xác nhận file tồn tại**: Sau khi chạy script → dùng `list_dir` / `view_file` xác nhận file .docx/.pdf đã xuất thành công.
5. **Tự động hóa Chèn Biểu đồ (Visual Automation)**: Nếu có ảnh từ Technical_Illustrator → chèn bằng đường dẫn tuyệt đối vào báo cáo. Đặc biệt, nếu phát hiện tham số so sánh phương án trong JSON Handoff, AI tự động kích hoạt `Technical_Illustrator` chạy script `draw_comparison_chart.py` để lấy biểu đồ Radar/Bar Chart và nhúng thẳng vào file Word/MD/PDF.
6. **Validate JSON trước khi map vào Template**:
   - Kiểm tra ĐỦ tất cả field bắt buộc trong Handoff JSON trước khi bơm vào template.
   - Nếu thiếu field nào → KHÔNG xuất file. Báo ngay:
     "Thiếu trường dữ liệu: [tên field] — không thể xuất tờ trình."
   - KHÔNG tự điền giá trị mặc định, KHÔNG để trống ô template mà không báo.
7. **Caption Bắt buộc cho Ảnh MODE 3D (AI Render)**:
   - Mọi ảnh nhận từ Technical_Illustrator MODE 3D khi chèn vào báo cáo PHẢI kèm caption:
     "Hình minh họa khái niệm — không phải bản vẽ kỹ thuật chính xác, không dùng để thi công."
   - Ảnh từ MODE 2D (Python script) không cần caption này — được coi là bản vẽ kỹ thuật chính thức.
8. **Cấm nén Calculation Chain (Bắt buộc Tối đa hóa Chi tiết)**: SKILL_REPORT tuyệt đối không được tự tóm tắt hay rút gọn Calculation Chain nhận từ JSON Handoff của SKILLKC. Nếu JSON Handoff cung cấp chuỗi tính toán đầy đủ từng bước, báo cáo PHẢI trình bày đủ toàn bộ công thức, tham số và kết quả của từng bước đó. Không được áp dụng bất kỳ hình thức nén nào kể cả với báo cáo cấp cao.
9. **Hiển thị Citation đầy đủ, không rút gọn**: Mọi tham chiếu tiêu chuẩn trong báo cáo phải hiển thị đủ 4 phần (Mã — Năm — Điều/Bảng — Trích yếu) theo Citation Object gốc từ JSON Handoff, đúng theo C12 (SKILLKC.md). Nếu Citation_Status = UNVERIFIED, phải in kèm cảnh báo: "⚠ Số liệu chưa xác minh được căn cứ tiêu chuẩn cụ thể — cần kỹ sư kiểm tra lại trước khi dùng cho hồ sơ chính thức."
10. **Tích hợp Log Tính Toán (Calculation Logs Integration)**: Bắt buộc báo cáo phải render trực tiếp mảng `Calculation_Logs` (được sinh ra từ các script Python của Engine tính toán) vào mục Phụ lục hoặc phần Luận giải kỹ thuật. KHÔNG thông qua bước LLM tự tóm tắt lại.
    - Script `generate_report.py` và `generate_to_trinh.js` tự động tạo 1 bảng ghi nhận chi tiết Tên Bước, Công thức, Thay số, và Kết quả từ mảng này đính kèm vào cuối văn bản.
11. **Hỗ trợ Đa ngôn ngữ (Bilingual Reporting)**: Khi tạo báo cáo song ngữ (Anh - Việt) hoặc thuần Tiếng Anh, AI sẽ tự động dịch các trường nội dung trong JSON Handoff trước khi tiến hành xuất file, nhằm tương thích với các template quốc tế.
12. **Narrative Depth Minimum (Độ sâu Diễn giải Tối thiểu)**: Mọi Tờ trình (Mode 2) BẮT BUỘC phải có tổng nội dung phần "Nội dung Tờ trình" ≥ **800 từ** (không tính bảng, heading, caption). Nếu bản nháp dưới ngưỡng → AI phải tự bổ sung diễn giải theo thứ tự ưu tiên:
    - (a) Bối cảnh & Lý do trình duyệt (tại sao bây giờ?)
    - (b) Đánh giá hiện trạng chi tiết (cái gì hư? hư đến mức nào?)
    - (c) Phương án đã xem xét và loại bỏ (tại sao không chọn?)
    - (d) Diễn giải chi tiết phương án đề xuất (làm gì? bằng gì? bao nhiêu?)
13. **Exemplar-Guided Writing (Viết theo Mẫu)**: Trước khi viết Tờ trình, AI BẮT BUỘC kiểm tra thư mục `templates/` và `_archive/` để tìm file Tờ trình mẫu (Exemplar) cùng loại hạng mục. Nếu tìm thấy:
    - Đọc cấu trúc và văn phong của Exemplar.
    - Áp dụng cùng mức độ chi tiết (không ngắn hơn Exemplar).
    - Giữ nguyên format bảng, heading, và cách đánh số mục của Exemplar.
14. **Structured Heading Injection (Cấu trúc Sub-heading Bắt buộc)**: Phần "Nội dung Tờ trình" trong file Word PHẢI được chia thành các sub-heading rõ ràng theo bảng cấu trúc Mode 2 ở trên. KHÔNG được viết nội dung dạng 1 đoạn văn liên tục không có heading.
15. **Auto-Illustration Trigger (Tự động Gọi Vẽ Ảnh)**: Khi AI viết tờ trình mà phát hiện nội dung thuộc 1 trong các trường hợp sau, BẮT BUỘC tự động gọi `Technical_Illustrator` tạo ảnh kèm theo:
    - Mô tả mặt cắt cấu kiện → Gọi MODE 2D vẽ mặt cắt.
    - Mô tả phối cảnh tổng thể → Gọi MODE 3D render.
    - So sánh ≥ 2 phương án → Gọi `draw_comparison_chart.py`.

---

## REPORT MODE 4: Unified Dispatcher (Audience-Aware, Multi-Format) �

### Khái niệm

Thay vì chọn 1 format cố định, **Mode 4** cho phép xuất **1 lần nhiều format**, với **sections** được chọn lọc theo **đối tượng độc giả (audience)**.

### 5 Audience Profiles

| Audience | Use Case | Sections đầy đủ | Tone |
|----------|----------|----------------|------|
| `designer` | Tư vấn thiết kế | Cover + TOC + Dashboard + Logs + Citations + Charts | Formal technical |
| `engineer` | Kỹ sư tính toán | Cover + TOC + Logs + Charts | Technical precise |
| `contractor` | Nhà thầu thi công | Cover + TOC + Project Info + Charts + Approval | Practical |
| `owner` | Chủ đầu tư | Cover + Dashboard + Comparison + Charts | Business friendly |
| `authority` | Cơ quan quản lý | Cover + TOC + All sections + Full audit | Official formal |

### Cách sử dụng

**Bước 1:** SKILLKC xuất JSON handoff → `audit.json`

**Bước 2:** Gọi dispatcher với audience mong muốn:

```bash
# Báo cáo đầy đủ cho designer (kỹ thuật)
python scripts/report_dispatcher.py \
    --handoff audit.json \
    --audience designer \
    --formats md,docx

# Báo cáo executive cho owner (có Dashboard, Comparison, charts)
python scripts/report_dispatcher.py \
    --handoff audit.json \
    --audience owner \
    --formats docx \
    --include-charts

# Xuất 1 lần 3 format cho 3 đối tượng khác nhau
python scripts/report_dispatcher.py \
    --handoff audit.json \
    --formats md,docx,html \
    --audience designer \
    --output "G:/Projects/Reports/"
```

### Tính năng tự động

| Tính năng | Mô tả |
|-----------|--------|
| **Cover page** | Logo, project name, title, version, date (cho DOCX) |
| **Header/Footer** | Project name + Page X/Y field codes |
| **Executive Dashboard** | KPI table, status banner, top risks, CTA (Owner/Contractor) |
| **Calculation logs** | Step + η + Rating có màu (Designer/Engineer) |
| **Citations** | Format 4-tuple đầy đủ (Designer/Authority) |
| **Charts auto** | Radar/bar/progress/heatmap 300 DPI (khi có Comparison data) |
| **Approval Matrix** | 3-column signature table |
| **Disclaimer** | Bắt buộc ở cuối mỗi báo cáo |

### Output paths mặc định

```
[handoff_dir]/
├── [project_name]_designer.md
├── [project_name]_designer.docx
├── [project_name]_designer.html
└── _charts/
    ├── comparison_radar.png
    ├── progress_bar.png
    └── eta_heatmap.png
```

### Khi nào dùng Mode 4?

✅ Khi cần xuất **1 báo cáo cho nhiều đối tượng** (Owner + Designer + Contractor cùng lúc)

✅ Khi cần báo cáo **executive** (dashboard, KPI, CTA) cho ban lãnh đạo

✅ Khi muốn báo cáo **đa format** (MD cho web/intranet, DOCX cho in ấn, HTML cho email)

✅ Khi cần **audience-aware** sections (loại bỏ chi tiết kỹ thuật khi gửi cho Owner)

❌ Khi chỉ cần 1 format cụ thể, dùng Mode 1/2/3 (đơn giản hơn)

---

## Báo cáo Excel (.xlsx)

### 4 Loại báo cáo Excel

| Type | Use Case | Generator |
|------|----------|-----------|
| `boq` | Bảng Khối Lượng (Bill of Quantities) | `xlsx_report.py --type boq` |
| `calc` | Calculation Sheet với η/Rating màu | `xlsx_report.py --type calc` |
| `comparison` | Ma trận So sánh Phương án + Chart | `xlsx_report.py --type comparison` |
| `submittal` | Submittal Log cho SKILL_RFI | `xlsx_report.py --type submittal` |

### Usage

```bash
python scripts/xlsx_report.py \
    --input audit.json \
    --type calc \
    --output calc_sheet.xlsx
```

### Tính năng styling

- Header với background màu PRIMARY
- Zebra striping cho data rows
- Rating cells có màu: RED=F5B7B1, ORANGE=FAD7A0, YELLOW=FCF3CF, GREEN=D5F5E3
- BarChart auto-insert cho comparison matrix
- Number formatting: `#,##0.00`, `#,##0`, currency

---

## Handoff JSON (Nhận từ SKILLKC)

File handoff: `[MãDA]_analysis_data.json` — cấu trúc tối thiểu:

```json
{
  "Ten_Du_An": "...",
  "Hang_Muc": "...",
  "Giai_Doan_TK": "BVTC",
  "Ngay": "DD/MM/YYYY",
  "Doi_Chieu_Tieu_Chuan_Tai_Trong": {
    "Ket_Qua": "Đạt, η = 87%",
    "Citations": [
      {
        "Ma_Tieu_Chuan": "TCVN 2737",
        "Nam_Ban_Hanh": "2023",
        "Dieu_Bang_Muc": "Điều 10.2",
        "Trang_So": "Trang 45",
        "Ten_Bang_Hinh": "Bảng 3 - Hệ số độ tin cậy",
        "Trich_Yeu": "Hệ số tin cậy tải trọng gió",
        "Nguon_File": "TCVN 2737-2023.pdf"
      }
    ],
    "Citation_Status": "VERIFIED"
  },
  "Calculation_Logs": [
    {
      "Step": "Tính hệ số k_z",
      "Formula": "k_z = k_base * (z/10)^0.2",
      "Values": "k_base = 1.0, z = 15",
      "Result": "1.084"
    }
  ],
  "Calculation_Details": [
    {
      "Thong_So": "Hệ số tin cậy tải trọng gió (γ_f)",
      "Gia_Tri_Thiet_Ke": "1.2",
      "Cong_Thuc_Kiem_Tra": "W_c = γ_f * W_tc",
      "Tieu_Chuan_Tham_Chieu": {
        "Ma_TC": "TCVN 2737:2023",
        "Dieu_Muc": "Điều 10.2",
        "Bang_Hinh": "Bảng 4",
        "Trang": "Trang 45"
      },
      "Danh_Gia": "Đạt"
    }
  ],
  "Constructability_Risk": "MINOR — nút giao thép dày, khuyến nghị tăng khoảng hở",
  "Kien_Nghi": "Chấp thuận phương án cọc D400 theo TCVN 10304:2025"
}
```

---

## Ví dụ báo cáo mẫu (Tham khảo)
>
> Xem `_archive/SKILL_REPORT_BURANO_SAMPLE_BACKUP.md` — báo cáo tính toán tải trọng thực tế dự án Canteen Burano Sóng Thần làm tài liệu tham khảo format số liệu.
