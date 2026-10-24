---
name: Design_Evaluation
version: 2.2.0
last_updated: 2026-09-27
description: "Kỹ sư QLTK Kết Cấu AI toàn năng: Tính toán & thiết kế kết cấu (BTCT, thép, tiền chế, container); Review QC/QA hồ sơ theo giai đoạn (TKCS→TKKT→BVTC→Hoàn công); Kiểm soát pháp lý theo TCVN/Eurocode/ACI; Phối hợp đa bộ môn (KC-MEP-KT); Value Engineering; Xử lý NCR & sự cố thi công; Lập BOQ; Soạn thảo báo cáo chuyên nghiệp đa định dạng (MD/DOCX/HTML/XLSX) với 5 audience profiles. Kích hoạt khi nhắc đến các keyword/tiếng lóng: review bản vẽ KC, tính lún, check võng, giải nội lực, check thép, bóc tách khối lượng, xuất dự toán, kiểm tra TCVN, xử lý RFI, đánh giá biện pháp thi công, thiết kế móng, lập tờ trình, xuất Word, soạn báo cáo, trình duyệt, xuất Excel."
---

# Design Evaluation & Structural Assistant — SKILL Entry Point

## ⚠ ĐỌC TRƯỚC: Đây có đúng là skill cần dùng không?

Skill này đóng vai **Quản lý Thiết kế / đại diện Chủ đầu tư** — review, thẩm tra, NCR, tờ trình, so sánh phương án, bóc khối lượng.

**Nếu User muốn TỰ TÍNH RA tiết diện / cốt thép / bu lông và xuất Thuyết minh tính toán → dùng `Structural_Design_Engineer`, KHÔNG dùng skill này.**

Bảng phân xử đầy đủ giữa 3 skill: `../AGENTS.md` mục 0.

## Tổng quan

Bộ skill **Design_Evaluation** cung cấp 2 năng lực chính cho Kỹ sư Quản lý Thiết kế Kết cấu:

| Module | File | Chức năng |
|--------|------|-----------|
| **SKILLKC** | `SKILLKC.md` | Phân tích kỹ thuật kết cấu: 17 nhóm năng lực + 4 kỹ năng đặc biệt |
| **SKILL_REPORT** | `SKILL_REPORT.md` | Xuất báo cáo: 4 luồng — Mode A (.md DeepResearch), Mode B (.docx Tờ Trình), Mode C (.docx/.pdf từ MD), Mode D (Unified Dispatcher — MD/DOCX/HTML, 5 audience profiles) |

## Quy tắc Điều phối (Dispatcher Logic)

Khi nhận yêu cầu từ User, AI phải xác định module phù hợp:

### → Kích hoạt SKILLKC khi

- User yêu cầu **phân tích, tính toán, review, đánh giá** kết cấu
- Các từ khóa: *tính lún, check võng, giải nội lực, check thép, kiểm tra TCVN, xử lý RFI, NCR, đánh giá biện pháp thi công, thiết kế móng, review bản vẽ KC, đối chiếu tiêu chuẩn*
- Khi cần tra cứu tiêu chuẩn trong thư mục `standards/` → dùng `grep_search` (xem `standards/INDEX_QUICK.md`)

### → Kích hoạt SKILL_REPORT khi

- User yêu cầu **viết báo cáo, lập tờ trình, xuất Word, soạn email dự án**
- Các từ khóa: *báo cáo, tờ trình, trình duyệt, xuất Word, form mẫu, gửi sếp, DeepResearch*

### → Kích hoạt CẢ HAI khi

- User yêu cầu *"phân tích rồi lập tờ trình"*, *"báo cáo đầy đủ"*, *"cả hai"*
- Quy trình: SKILLKC phân tích → Review Gate (User duyệt) → SKILL_REPORT xuất báo cáo

### → FALLBACK khi không khớp keyword

- **KHÔNG** tự đoán và nạp cả hai module.
- Hỏi User: *"Ảnh/chị cần hỗ trợ về **phân tích kỹ thuật kết cấu** (SKILLKC) hay **xuất báo cáo/tờ trình** (SKILL_REPORT)?"*

## Cấu trúc Thư mục

```text
.agents/skills/
├── AGENTS.md                       ← Quy tắc chung 3 skill + Bảng phân xử liên-skill
├── STANDARDS_LOCK.md               ← Chốt phiên bản tiêu chuẩn (nguồn sự thật duy nhất)
└── Design_Evaluation/
    ├── SKILL.md                    ← BẠN ĐANG Ở ĐÂY (Entry Point)
    ├── SKILLKC.md                  ← Năng lực phân tích kỹ thuật
    ├── SKILL_REPORT.md             ← Năng lực xuất báo cáo (3 mode: .md / .docx / .pdf)
    ├── README.md                   ← Cẩm nang sử dụng nhanh + Lỗi phổ biến
    ├── test_cases_backtest.md      ← Bộ test 5 kịch bản end-to-end
    ├── calculators/                ← ENGINE TÍNH TOÁN (bắt buộc gọi, cấm nhẩm tay)
    │   ├── rc_flexure_design.py    ← Cốt thép dầm BTCT chịu uốn
    │   ├── deflection_check.py     ← Kiểm tra độ võng
    │   ├── steel_member_check_v2024.py ← ✅ Ứng suất cấu kiện thép (TCVN 5575:2024)
    │   ├── foundation_bearing.py   ← Sức chịu tải nền (hiệu chỉnh R0)
    │   ├── wind_load_calc.py       ← Tải trọng gió tĩnh
    │   └── earthquake_load_calc.py  ← Tải trọng động đất (TCVN 9386:2025)
    ├── scripts/                    ← Xuất báo cáo & trích xuất dữ liệu
    │   ├── generate_report.py      ← Bơm JSON vào template Word
    │   ├── generate_to_trinh.js    ← Tạo Word từ đầu (docx-js)
    │   ├── md_to_docx_report.js    ← Chuyển .md → .docx
    │   ├── md_to_pdf_report.js     ← Chuyển .md → .pdf (không cần npm install)
    │   ├── report_dispatcher.py    ← ⭐ Unified dispatcher (5 audiences, MD/DOCX/HTML) — v4.0
    │   ├── xlsx_report.py          ← Excel: BOQ/Calc/Comparison/Submittal — v4.0
    │   ├── boq_extractor.py        ← Đọc file BOQ Excel/CSV → JSON
    │   ├── validate_handoff.py     ← ✅ Validate JSON handoff theo schema (2026-08-30)
│   ├── validate_registry.py     ← ✅ Validate Technical_Illustrator registry (2026-08-30)
    │   └── generate_*.py           ← 4 generator .docx chuyên dụng (bờ kè, pi giếng, NCR, thấm đá)
    │   └── _lib/                    ← 📦 Shared utilities (v4.0) — used by report_dispatcher.py
    │       ├── _docx_helpers.py     ← DOCX helpers: cover, TOC, headers, table styling, callouts
    │       ├── _report_utils.py     ← Formatters: η, currency, citation, Vietnamese-safe filename
    │       ├── _chart_inserter.py   ← Charts: radar, bar, progress, heatmap, cost breakdown
    │       ├── _executive_dashboard.py ← Dashboard cho Owner audience (KPI, status, CTA)
    │       └── _audience_profiles.py   ← 5 audience configs: designer/engineer/contractor/owner/authority
    ├── modules/                    ← Tiện ích phụ trợ (audience, forensic, version tracker…)
    ├── schemas/                    ← JSON Schema validate handoff
    ├── templates/                  ← Form mẫu Word của công ty
    ├── standards/                  ← 72 file PDF tiêu chuẩn
    │   ├── INDEX_QUICK.md          ← Tra nhanh — ĐỌC TRƯỚC
    │   └── INDEX.md                ← Danh mục đầy đủ (lazy-load)
    ├── references/                 ← Protocol chi tiết (lazy-load)
    └── _archive/                   ← File cũ (không dùng)
```

## Quy tắc Chung (Áp dụng cho mọi module)

> Quy tắc đầy đủ và có hiệu lực cao nhất: **`../AGENTS.md`**. Mục dưới là bản rút gọn.

1. **No Hallucination**: Thiếu dữ liệu → ghi `Data Missing: [...]`, không bịa.
2. **Review Gate**: Trước khi xuất file Word/PDF/JSON → tóm tắt ra chat, chờ User xác nhận.
3. **Handoff Protocol**: SKILLKC xuất JSON → validate theo `schemas/analysis_handoff.schema.json` → SKILL_REPORT nhận JSON → xuất báo cáo.
4. **Approval Matrix**: Mọi báo cáo phải có bảng Trách nhiệm (Đề xuất / Kiểm tra / Phê duyệt).
5. **grep_search first**: Khi tra tiêu chuẩn PDF, dùng `grep_search` với từ khóa, KHÔNG đọc toàn bộ file.
6. **Deterministic Math**: Cấm nhẩm tay. Gọi script trong `calculators/`, đọc JSON từ stdout.
7. **Standards Lock**: Phiên bản tiêu chuẩn lấy từ `../STANDARDS_LOCK.md`. Nếu script khai báo `Standard_Method` khác phiên bản chốt → phải in cảnh báo trong báo cáo, không tự đổi nhãn.
