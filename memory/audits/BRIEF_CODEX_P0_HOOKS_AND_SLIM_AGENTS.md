# PHIẾU GIAO VIỆC TRIỂN KHAI CẶP ĐÔI P0 (DÀNH CHO CODEX)
## CÀI ĐẶT BỘ HOOKS AN TOÀN CHO CLAUDE CODE & TINH GỌN AGENTS.MD (PROGRESSIVE DISCLOSURE)

> **Người giao việc:** GEMINI (System Coordinator)  
> **Người nhận thi hành:** CODEX (Chief Systems Architect / Lead Auditor)  
> **Mã nhiệm vụ:** `TASK-P0-HOOKS-SLIM-AGENTS-20261123`  
> **Chế độ tác vụ:** `SYSTEM_UPGRADE`  
> **Mục tiêu tối thượng:** Bảo vệ an toàn tuyệt đối cho hồ sơ dự án thật & Giảm tải token, triệt tiêu lỗi cắt cụt 24 KB mỗi turn.

---

## 1. NHIỆM VỤ P0.1: CÀI ĐẶT BỘ HOOKS AN TOÀN TRONG `.claude/settings.json`

### Yêu cầu kỹ thuật:
1. Viết một script hook Python nội bộ siêu nhẹ, phản hồi nhanh (< 50ms) tại `.agents/tools/claude_safety_hook.py`:
   - **Chốt chặn 1 (`PreToolUse`):** Kiểm tra lệnh chuẩn bị chạy. Nếu có thao tác ghi/sửa trực tiếp vào tệp `.dwg` trong `01_Projects/` $	o$ Chặn ngay lập tức (`exit code 1` kèm thông báo lỗi tiếng Việt). Chỉ cho phép xuất file vào `04_Deliverables_ToTrinh/` hoặc chạy AutoCAD Core Console chỉ-đọc.
   - **Chốt chặn 2 (`PostToolUse`):** Tự động kích hoạt script `audit_zero_white_text.py` ngay khi AI vừa sửa các file `.py` hoặc tạo file `.docx`/báo cáo trong workspace.
   - **Chốt chặn 3 (`PreToolUse`):** Cảnh báo dừng lại và bắt buộc xác nhận Review Gate trước khi thực thi `git push`.
   - **Lưu ý quan trọng từ phát hiện của Codex:** Phải có whitelist cho các lệnh đọc an toàn thông thường (`git status`, `git diff`, `pytest`, `python ...`) để tránh lỗi trả `UNKNOWN` như của `agent-circuit-breaker`.
2. Cấu hình khai báo hook hợp lệ trong `.claude/settings.json` (hoặc `.claude/settings.local.json`).
3. Viết test kiểm chứng: test ca lệnh hợp lệ (`ALLOW`) và ca vi phạm (`BLOCK`).

---

## 2. NHIỆM VỤ P0.2: TINH GỌN `AGENTS.md` THEO MẪU PROGRESSIVE DISCLOSURE

### Yêu cầu kỹ thuật:
1. File `AGENTS.md` hiện tại nặng **48,033 bytes (594 dòng)** và bị hệ thống cắt cụt mất 24,042 bytes mỗi turn.
2. Rút gọn file `AGENTS.md` gốc xuống **≤ 12–15 KB**:
   - Giữ lại phần lõi: Rule 0 Ma trận phân luồng, Rule 1 Đường dẫn tuyệt đối, Rule 2 UTF-8, Rule 3 Review Gate, Rule 4 No hallucination, Rule 5 Deterministic math, Rule 6 Chỉ số eta, Rule 7 Standards Lock, Rule 8 Disclaimer, Rule 10 Xác nhận file, Rule 12 Văn phong kỹ thuật, và Bảng 14 skills.
3. Tách các bảng quy chuẩn kỹ thuật rất dài sang các file chuyên biệt trong `.agents/skills/references/`:
   - `RULE_12B_ZERO_WHITE_TEXT.md`: Bảng màu gốc khoáng & quy định cấm chữ trắng.
   - `RULE_12C_CONCRETE_GRADE_REALISM.md`: Quy định cấp bền bê tông dầm sàn B25-B35, cột vách B35-B40.
   - `RULE_12D_CAD_DRAFTING_STANDARDS.md`: Quy chuẩn phân đoạn dầm, dim, text của CAD DCE Pro.
   - `RULE_12E_REVIT_MODELING_STANDARDS.md`: Quy tắc mô hình hóa Revit BIM.
4. Đồng bộ file rút gọn sang `AGENTS.md` ở thư mục gốc và `.agents/AGENTS.md`.
5. Chạy bộ kiểm thử Suite 1 (`integration_test.py`) và Suite 15 (`test_sync_report.py`) bảo đảm đạt 100% PASS, không lỗi hồi quy.

---

## 3. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

1. Hook an toàn hoạt động mượt mà, chặn được lệnh ghi đè `.dwg` gốc mà không làm chậm Claude Code.
2. Dung lượng `AGENTS.md` gốc giảm xuống ≤ 15 KB (không còn bị cắt cụt).
3. Suite 1 (64 checks) và Suite 15 (14 tests) chạy đạt 100% PASS.
4. Xuất báo cáo nghiệm thu tại `.agents/memory/audits/CODEX_P0_IMPLEMENTATION_REPORT.md`.

---
*Phiếu giao việc phát hành qua Dual-Agent Bridge v3.4.*
