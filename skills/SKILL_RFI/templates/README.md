# SKILL_RFI Templates

## Available Templates

| File | Mô tả | Dùng cho |
|------|--------|----------|
| `RFI_Template.docx` | Form RFI chuẩn | Tạo từ RFI JSON |
| `NCR_Template.docx` | Phiếu NCR chuẩn | Tạo từ NCR JSON |
| `Submittal_Log_Template.xlsx` | Excel log Submittal | Theo dõi submittal workflow |

## Cách tạo templates

Templates sử dụng docxtpl syntax (Jinja2). Các biến chính:

### RFI Template:
- `{{ doc_code }}` — Mã RFI
- `{{ issue_summary }}` — Tóm tắt vấn đề
- `{{ context }}` — Bối cảnh chi tiết
- `{{ from_party }}` / `{{ to_party }}` — Bên gửi/nhận
- `{{ deadline }}` — Hạn chót
- `{{ priority }}` — Mức ưu tiên
- `{{ impact }}` — Ảnh hưởng
- `{{ drawings }}` — Bản vẽ liên quan
- `{{ created_date }}` — Ngày tạo

### NCR Template:
- `{{ doc_code }}`
- `{{ ncr_classification }}` — CRITICAL / MAJOR / MINOR
- `{{ ncr_description }}` — Mô tả không phù hợp
- `{{ ncr_root_cause }}` — Nguyên nhân
- `{{ ncr_corrective_action }}` — Hành động khắc phục
- `{{ location }}` — Vị trí
- `{{ detection_date }}` — Ngày phát hiện

Updated: 2026-08-31 — Phase D of Reporting Upgrade v4.0