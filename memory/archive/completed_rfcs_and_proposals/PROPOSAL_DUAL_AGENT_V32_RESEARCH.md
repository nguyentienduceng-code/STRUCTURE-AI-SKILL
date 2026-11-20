# ĐỀ XUẤT NGHIÊN CỨU & NÂNG CẤP KIẾN TRÚC DUAL-AGENT SYSTEM (v3.2.0)

> **Người lập:** Gemini (Antigravity)  
> **Người tiếp nhận:** Claude (Claude Code / Desktop)  
> **Thời điểm lập:** 2026-11-19  
> **Tài liệu nền tảng:** [SKILL_DUAL_AGENT_BRIDGE/SKILL.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/SKILL_DUAL_AGENT_BRIDGE/SKILL.md) & [DUAL_AGENT_BUS.json](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/memory/DUAL_AGENT_BUS.json)

---

## 1. Bối cảnh & Kết quả Kiểm toán Hiện trạng (Baseline v3.1.0)

Hệ thống điều phối liên tác tử đã đạt các mốc kiểm soát chất lượng quan trọng:
1. **Khóa nguyên tử ngoài Cloud (Local FileLock):** Đặt tại `%LOCALAPPDATA%\GoogleAIStudio\locks\dual_agent_bus.lock`, triệt tiêu rủi ro deadlock do trễ mạng Google Drive.
2. **Quy trình ghi an toàn (Atomic Write):** Ghi qua file ẩn tạm `.{stem}.tmp.{pid}` + `os.fsync()` + `os.replace()`, đã bổ sung `_atomic_write_text()` cho file `.md`.
3. **Phòng chống TOCTOU:** Đã di chuyển bước thẩm định cờ `IN_PROGRESS` vào sâu bên trong khối lock.
4. **Kiểm thử tự động:** `test_dual_agent_bridge.py` đạt **7/7 PASS (100%)**.

---

## 2. Bốn Điểm Trọng tâm Đề xuất Claude Nghiên cứu & Cải tiến (v3.2.0)

### 📌 Trọng tâm 1: Khử trùng lặp mã nguồn (Single Source of Truth - SSOT)
- **Hiện trạng:** Tồn tại song song 2 file mã nguồn lớn:
  - `.agents/tools/sync_bus.py` (49.7 KB)
  - `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py` (49.7 KB)
  Khi bảo trì dễ phát sinh hiện tượng một bên được vá lỗi nhưng bên kia bị bỏ quên.
- **Đề xuất nghiên cứu:**
  - Lựa chọn 1 tệp làm SSOT duy nhất (khuyến nghị `.agents/tools/sync_bus.py` hoặc đưa vào `.agents/_SHARED/`).
  - Biến file trong `scripts/` thành thin wrapper (chỉ import và gọi `main()` từ module SSOT).

### 📌 Trọng tâm 2: Cơ chế Heartbeat / Lease Timeout (Chống Treo Ca khi Crash)
- **Hiện trạng:** Nếu một Agent nhận ca (`IN_PROGRESS`), nhưng tiến trình bị ngắt đột ngột (crash, đóng cửa sổ chat, hết quota), trạng thái `IN_PROGRESS` và `current_holder` sẽ khóa vĩnh viễn cho đến khi Agent khác phải dùng cờ `--force`.
- **Đề xuất nghiên cứu:**
  - Bổ sung trường `lease_expire_at` hoặc `last_heartbeat` (ISO-8601) vào `DUAL_AGENT_BUS.json`.
  - Mặc định thời gian thuê ca (lease duration) là 60 phút. Sau thời hạn này nếu không có heartbeat, Agent đối tác được phép auto-claim mà không cần `--force`.

### 📌 Trọng tâm 3: Chuẩn hóa Đường dẫn tương đối theo Project Scope (Project-Scoped Resolver)
- **Hiện trạng:** Khi một Agent chạy từ thư mục con (ví dụ `01_Projects/16.BPTC Q12/...`), danh sách `artifacts_modified` đôi khi ghi tên file cục bộ thay vì POSIX relative path từ Workspace Root.
- **Đề xuất nghiên cứu:**
  - Hoàn thiện hàm `to_relative_path` để luôn tự động chuẩn hóa mọi tệp về gốc workspace `Path(workspace_root)`.
  - Hỗ trợ cờ `--project-dir <path>` để tự động gom nhóm các artifacts theo đúng dự án đang thực hiện.

### 📌 Trọng tâm 4: Tích hợp Visual Gate & Bằng chứng Nghiệm thu (Rule 12d Enforcer)
- **Hiện trạng:** Theo quy tắc Điều 12d (Bài học 2026-11-15), trước khi bàn giao ca (đặc biệt là công việc CAD / bản vẽ / báo cáo DOCX), bên bàn giao bắt buộc phải tạo ảnh preview (`render_preview`) hoặc báo cáo nghiệm thu thật.
- **Đề xuất nghiên cứu:**
  - Tích hợp một hook kiểm tra trong `sync_bus.py --auto` hoặc `handover_task.py`: Nếu task thuộc nhóm CAD/Drawing, kiểm tra xem có ít nhất 1 file `.png` preview hoặc log nghiệm thu đính kèm trong `artifacts_modified` trước khi chuyển sang `PENDING`.

---

## 3. Tiêu chí Nghiệm thu (Acceptance Criteria Checklist cho Claude)

- [ ] **Tiêu chí 1:** Đánh giá phương án refactor khử trùng lặp file giữa `tools/` và `skills/`.
- [ ] **Tiêu chí 2:** Thiết kế đặc tả cơ chế Lease Timeout / Heartbeat chống treo ca.
- [ ] **Tiêu chí 3:** Nâng cấp cơ chế Path Resolver theo phạm vi dự án.
- [ ] **Tiêu chí 4:** Bảo toàn 100% kết quả kiểm thử trên Windows (`python -m unittest discover -s .agents/skills/SKILL_DUAL_AGENT_BRIDGE/tests`).
- [ ] **Tiêu chí 5:** Cập nhật biên bản giao ban `DUAL_AGENT_HANDOFF_MEMO.md` và tài liệu hướng dẫn khi hoàn thành.
