## 12e. Khóa Cứng Quy tắc Trình bày Văn bản, Sàn Cỡ Chữ & Toán học Word/Excel (Clean Typography, Font Floor ≥ 10pt & Math Lock)

> **Cơ sở chuẩn hóa**: Nghị định 30/2020/NĐ-CP & nguồn sự thật design tokens tại `_SHARED/SHARED_CONTEXT/design_tokens.py` (trước đây từng gọi là Rule 12c trong các bản nháp cũ; nay thống nhất mã hiệu là **Điều 12e** để tách biệt hoàn toàn với Điều 12c về Cấp độ bền bê tông).

1. **Sàn cỡ chữ tối thiểu (Typography Floor Lock ≥ 10.0pt)**:
   - Báo cáo `.docx` & bảng tính `.xlsx` bắt buộc đạt sàn cỡ chữ: thân bài $\ge 11\text{ pt}$ (hành chính $13\text{ pt}$), bảng biểu và chú thích $\ge 10\text{ pt}$. Tuyệt đối cấm dùng `Pt(7..9.5)` hoặc `Font(size < 10)` trong bảng dữ liệu Word/Excel (kiểm toán tự động bởi `tools/audit_zero_white_text.py`).
2. **Cấm tuyệt đối Double Bullet (`•  •` — Trùng lặp 2 dấu chấm đầu dòng)**:
   - Khi gán `style='List Bullet'` hoặc `bullet: { level: 0 }`, Word tự render 1 bullet glyph `•`. Mọi generator (`_docx_helpers.py`, `docx_generator.py`, `docx_generator_v2.py`, `document_renderer.py`, `md_to_docx_report.js`) bắt buộc auto-strip ký tự `•, -, –, —, *` đứng đầu mục danh sách trước khi xuất đoạn văn.
3. **Tách biệt hoàn toàn Danh sách Thứ tự & Chữ cái khỏi List Bullet**:
   - Danh sách đánh số (`1., 2., 3.`) hoặc chữ cái (`a), b), c)`) bắt buộc dùng paragraph thụt lề (`left_indent`) hoặc numbering riêng, nghiêm cấm gán `style='List Bullet'`.
4. **Cấm tuyệt đối để lộ mã thô LaTeX trong Word**:
   - Toàn bộ ký hiệu toán học/thủy văn (`$H_{max}$`, `$H_{tb}$`, `$H_{min}$`, `$Q_{cd}$`, `$A_{s,req}$`, `$\gamma_f$`, `m^2`, `m^3`) phải chuyển qua parser thành subscript/superscript thật hoặc Unicode (`⇒, ×, ≥, ≤, ≈, Δ`) và xóa 100% ký tự `$` thô trước khi ghi `.docx`.

---
