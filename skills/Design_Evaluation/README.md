# 📘 Hướng Dẫn Sử Dụng — Bộ Skill AI Quản lý Thiết kế Kết cấu

> **Phiên bản:** v4.0 — Ngày cập nhật: 2026-08-18
> **6 Skill:** `Design_Evaluation` · `Structural_Design_Engineer` · `Technical_Illustrator` · `Cost_Estimator` · `SKILL_FORENSIC` · `SKILL_VERIFY`
>
> **Quy tắc chung 6 skill:** `../AGENTS.md` · **Phiên bản tiêu chuẩn:** `../STANDARDS_LOCK.md`

## 0. Chọn đúng Skill (quan trọng — 6 skill có keyword chồng nhau)

| Bạn đang làm gì? | Skill |
|---|---|
| Review / thẩm tra hồ sơ người khác, NCR, tờ trình, so sánh PA, bóc khối lượng | `Design_Evaluation` |
| Tự tính ra tiết diện / cốt thép / bu lông + xuất Thuyết minh tính toán | `Structural_Design_Engineer` |
| Chỉ cần vẽ hình / bản vẽ / biểu đồ | `Technical_Illustrator` |
| So sánh chi phí, Value Engineering, tính Carbon | `Cost_Estimator` |
| Điều tra sự cố / nứt nghiêm trọng / back-calculation | `SKILL_FORENSIC` |
| Kiểm chứng chéo kết quả, cross-check với ETABS | `SKILL_VERIFY` |

Bảng phân xử đầy đủ + tie-breaker: `../AGENTS.md` mục 0.

---

## 1. Bảng Lệnh Gọi Nhanh (Copy & Paste)

Thay `[...]` bằng thông số thực tế. Paste đường dẫn tuyệt đối nếu có file đính kèm.

### 🔵 PHÂN TÍCH KỸ THUẬT

| Tác vụ | Prompt mẫu |
|--------|-----------|
| **Check võng dầm** | `Check võng dầm [tên], nhịp [L]m, tiết diện [b×h], [mác BT], thép [n×Φd]` |
| **Tính tải gió** | `Tính tải gió nhà [N tầng], vùng gió [II]-[B], địa hình [B], H=[35]m` |
| **Kiểm tra cột** | `Check cột [tên], tiết diện [b×h], [mác BT], N=[kN], M=[kN.m]` |
| **Thiết kế móng cọc** | `Thiết kế móng cọc [tên], N=[kN], địa chất tại [đường dẫn file]` |
| **Review bản vẽ** | `Review bản vẽ KC tại [đường dẫn file PDF], giai đoạn [BVTC]` |
| **Tra tiêu chuẩn** | `Tra [TCVN 2737:2023]: [nội dung cần tra]. Chỉ giá trị + số điều khoản.` |
| **So sánh phương án** | `So sánh [PA1] vs [PA2] cho [hạng mục]. Lập bảng 8 tiêu chí.` |
| **Xử lý NCR** | `NCR: [mô tả sự cố]. Phân loại mức độ và đề xuất xử lý.` |

### 🟢 XUẤT BÁO CÁO

| Tác vụ | Prompt mẫu |
|--------|-----------|
| **DeepResearch** | `DeepResearch [chủ đề]. Đối tượng: [Tư vấn TK / CĐT / Thẩm tra]` |
| **Tờ trình Word** | `Xuất tờ trình Word gửi [GĐ Ban XD]. Lưu tại [đường dẫn thư mục]` |
| **Phân tích + Tờ trình** | `Phân tích [chủ đề] rồi xuất tờ trình gửi [người nhận]. Lưu tại [...]` |
| **MD → Word** | `Chuyển [đường dẫn .md] → Word tại [đường dẫn .docx]` |
| **MD → PDF** | `Chuyển [đường dẫn .md] → PDF tại [đường dẫn .pdf]` |

### 🟠 VẼ KỸ THUẬT (mặc định 2D — bản vẽ chính xác)

| Tác vụ | Prompt mẫu |
|--------|-----------|
| **Mặt cắt dầm thép** | `Vẽ mặt cắt dầm thép I: h=[mm], b=[mm], tw=[mm], tf=[mm]` |
| **Mặt cắt cột BTCT** | `Vẽ mặt cắt cột BTCT [b×h], thép [n×Φd], đai [Φd]a[s]` |
| **Chi tiết bu lông** | `Vẽ liên kết bu lông M[d], cấp [grade], [rows]×[cols]` |
| **Mặt cắt móng** | `Vẽ mặt cắt móng [đơn/băng], L=[mm], B=[mm], H=[mm]` |
| **Bố trí thép sàn** | `Vẽ bố trí thép sàn Lx=[mm], Ly=[mm], dày [mm]` |
| **Biểu đồ so sánh** | `Vẽ biểu đồ radar so sánh [PA1] vs [PA2] từ JSON: [...]` |
| **Render 3D** *(chỉ khi cần)* | `Render 3D phối cảnh [mô tả kết cấu/kiến trúc]` |

---

## 2. Quy tắc Vàng (Nhớ 5 điều)

| # | Quy tắc | Tại sao |
|---|---------|---------|
| ① | **Luôn paste đường dẫn tuyệt đối** | AI không tự tìm file |
| ② | **Chờ Review Gate** trước khi xuất file | An toàn số liệu |
| ③ | **SKILLKC tính → SKILL_REPORT xuất** | Đúng phân vai, không nhầm lẫn |
| ④ | **Gọi script có sẵn, không viết mới** | Tiết kiệm 3k–8k token |
| ⑤ | **Tách bước khi tác vụ phức tạp** | Dễ review từng bước |

---

## 3. Ví dụ Prompt Thực tế

### Ví dụ 1: Phân tích chuyên sâu + Tờ trình
```
Đánh giá ổn định vách lõi thang máy khi đục 2 lỗ mở 1.5×2m tại tầng hầm.
Bê tông B30, vách 250mm, tầng cao 3.5m.
Bản vẽ: g:\My Drive\DuAnA\KC-01.pdf
Sau khi tôi duyệt → xuất tờ trình Word gửi GĐ Ban XD.
Lưu tại: g:\My Drive\DuAnA\output\
```

### Ví dụ 2: NCR nhanh
```
NCR: Nhà thầu đổ sai mác BT cột C1 tầng 5 — thiết kế B30, thực tế B20.
Phân loại mức độ + đề xuất gia cường.
```

### Ví dụ 3: Vẽ kỹ thuật
```
Vẽ mặt cắt cột BTCT 400×600, thép 8Φ22, đai Φ10a150.
Lưu ảnh tại: g:\My Drive\DuAnA\hinhanh\col_C1.png
```

---

## 4. Cấu trúc Thư mục

```
Design_Evaluation/
├── SKILL.md               ← Điều phối (Dispatcher)
├── SKILLKC.md              ← 18 rules phân tích kỹ thuật
├── SKILL_REPORT.md         ← 11 rules xuất báo cáo
├── README.md               ← BẠN ĐANG ĐỌC ĐÂY
├── test_cases_backtest.md  ← Bộ test 5 kịch bản
├── calculators/            ← 5 engine tính toán Python
├── scripts/                ← 12 scripts xuất báo cáo/Word/PDF
├── modules/                ← 9 scripts phụ trợ
├── templates/              ← Form mẫu Word công ty
├── schemas/                ← JSON Schema validation
├── standards/              ← 72 file PDF tiêu chuẩn (TCVN/QCVN/Intl)
└── references/             ← Protocol chi tiết (lazy-load)

Technical_Illustrator/
├── SKILL.md               ← Điều phối vẽ
├── scripts/                ← 11 scripts vẽ 2D Python
└── references/             ← Hướng dẫn MODE 2D / MODE 3D
```

---

## 5. Những Lỗi Phổ Biến

| ❌ Sai | ✅ Đúng | Lý do |
|--------|---------|-------|
| Không paste đường dẫn file | Luôn dán path tuyệt đối | AI không tự tìm |
| Bỏ qua Review Gate | Dặn "tóm tắt trước khi xuất" | Bảo vệ số liệu |
| Bắt SKILL_REPORT tính toán | SKILLKC tính → REPORT xuất | Đúng phân vai |
| Nhờ viết lại script đã có | Gọi script theo tên sẵn | Tiết kiệm token |
| Dùng relative path cho output | Dùng absolute path | Script tìm không thấy file |
| Gộp tất cả vào 1 prompt dài | Tách: SKILLKC → TI → REPORT | Dễ review từng bước |
| Yêu cầu "vẽ đẹp" cho bản vẽ kỹ thuật | Nói rõ "vẽ mặt cắt 2D" | Tránh AI render 3D giả tạo |
| Chạy `npm install` trong thư mục skill | Cài ở ổ local rồi copy sang | npm lỗi EBADF trên Google Drive → file 0 byte |

---

## 6. Sự cố Môi trường Đã biết

### `npm install` KHÔNG chạy được trên Google Drive

Chạy `npm install` trực tiếp trong `Design_Evaluation/` báo lỗi `EBADF: bad file descriptor` và để lại các file **0 byte** trong `node_modules/`. Hậu quả: `require('docx')` crash với `Invalid package config` → **hỏng toàn bộ REPORT MODE 2 (Tờ trình Word)**.

**Cách cài lại gói Node:**

```bash
mkdir %TEMP%\docxstage && cd %TEMP%\docxstage
npm install docx@^9.7.1
xcopy /E /I /Y %TEMP%\docxstage\node_modules\docx "G:\My Drive\Google AI Studio\.agents\.npm\docx"
```

**Lưu ý:** Package `docx` hiện được lưu tại `.npm/docx/` (thay vì trong `Design_Evaluation/node_modules/`).

Script `scripts/_require_docx.js` tự phát hiện tình trạng này và in hướng dẫn sửa. Có thể trỏ biến môi trường `DOCX_PATH` tới một bản `docx` đang hoạt động để bỏ qua hoàn toàn.

### Xuất PDF không cần npm

`md_to_pdf_report.js` không dùng thư viện npm nào — nó render Markdown sang HTML rồi gọi Microsoft Edge / Chrome ở chế độ headless để in PDF. Nếu không tìm thấy trình duyệt, script vẫn xuất bản HTML khổ A4 để in tay.

---

*Tham khảo chi tiết rules: `SKILLKC.md`, `SKILL_REPORT.md`. Cẩm nang test: `test_cases_backtest.md`.*
