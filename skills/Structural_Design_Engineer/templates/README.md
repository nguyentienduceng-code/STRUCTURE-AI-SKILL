# templates/ — Form mẫu Thuyết minh Tính toán

Thư mục này chứa form mẫu Word cho Thuyết minh tính toán kết cấu (Calculation Sheet).

## Trạng thái hiện tại

**Chưa có form mẫu `.docx` riêng cho Thuyết minh tính toán.**

Trước đây `SKILL.md` khai báo thư mục này nhưng nó không tồn tại — mọi tham chiếu tới
"form mẫu Thuyết minh" đều dẫn tới ngõ cụt. Thư mục nay được tạo cùng ghi chú này để
tránh lặp lại lỗi đó.

## Quy trình xuất Thuyết minh khi chưa có form mẫu

1. Chạy `scripts/export_calc_sheet.py` → sinh file `.md` theo cấu trúc 6 phần
   quy định tại `SKILL_CALC_REPORT.md`.
2. Chuyển sang Word hoặc PDF bằng script của `Design_Evaluation`:

   ```bash
   node "../../Design_Evaluation/scripts/md_to_docx_report.js" input.md output.docx
   node "../../Design_Evaluation/scripts/md_to_pdf_report.js"  input.md output.pdf
   ```

3. Đặt tên file theo chuẩn: `[MãDA]_ThuyetMinh_KC_v[N]_[YYYYMMDD].docx`

## Khi bổ sung form mẫu

Đặt file `.docx` vào thư mục này, dùng cú pháp tag `{{TenTruong}}`, rồi quét tag bằng:

```bash
python "../../Design_Evaluation/scripts/generate_report.py" --scan "templates/<ten_form>.docx"
```

Sau đó cập nhật bảng mapping JSON → tag vào `SKILL_CALC_REPORT.md`.
