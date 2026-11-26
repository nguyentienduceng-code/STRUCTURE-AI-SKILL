# BÁO CÁO NÂNG CẤP CẦU NỐI GEMINI ↔ CLAUDE v3.6 (`DUAL_BRIDGE_V36_RESULT`)

## 1. Tóm tắt ca
- Khắc phục triệt để 4 lỗi giao tiếp phát hiện trong ca phản biện của Claude:
  1. Đóng kênh treo `IN_PROGRESS` bằng luồng trả ca chuẩn `--need-review --blocked-return --blocking-questions "..."` tự mở khóa `current_holder=IDLE` và được Auto-Pickup Hook nạp tự động cả ở trạng thái `NEED_REVIEW`.
  2. Bổ sung `environment_capabilities` vào `DUAL_AGENT_BUS.json`, `DUAL_AGENT_HANDOFF_MEMO.md` và `_CA_HIEN_TAI.md` để cả Gemini và Claude thấy cùng một trạng thái máy (`accoreconsole.exe`, `sheet_set_manager_native_dst`, `live_peer_messaging_between_tabs=False`).
  3. Bổ sung chế độ chỉ-đọc `python .agents/tools/accoreconsole_adapter.py --audit-only <file.dwg>` (sao chép sang `%TEMP%`, không bao giờ sửa DWG gốc) và mở ngoại lệ an toàn tương ứng trong `claude_safety_hook.py`.
  4. Bảo toàn `work_ticket` cùng dự án khi gọi `sync_bus.py --auto`, bổ sung 5 trạng thái vòng đời `--lifecycle-state` (`DESIGN_PROPOSAL..ENGINEER_APPROVED`), đồng bộ `CLAUDE.md`, `/nhan-ca`, `/ban-giao`, `dual-agent-bridge/SKILL.md`, và dọn bỏ thư mục nháp `SPRINT3_DRAFT/` (giữ nguyên 8/8 DXF + 8/8 DWG + 8/8 PNG Sprint 2 trong `04_Deliverables_ToTrinh/`).

## 2. Sản phẩm & Đường dẫn thật
- `g:\My Drive\Google AI Studio\.agents\tools\accoreconsole_adapter.py`
- `g:\My Drive\Google AI Studio\.agents\tools\claude_safety_hook.py`
- `g:\My Drive\Google AI Studio\.agents\tools\sync_bus.py`
- `g:\My Drive\Google AI Studio\.agents\tools\antigravity_dual_bus_hook.py`
- `g:\My Drive\Google AI Studio\.claude\CLAUDE.md`
- `g:\My Drive\Google AI Studio\.claude\commands\nhan-ca.md` & `g:\My Drive\Google AI Studio\.claude\commands\ban-giao.md`
- `C:\Users\ADMIN\.gemini\config\skills\dual-agent-bridge\SKILL.md`, `.../nhan-ca/SKILL.md`, `.../ban-giao/SKILL.md`
- `g:\My Drive\Google AI Studio\.agents\tests\test_dual_bus_v36_communication.py`

## 3. Kết quả Kiểm định & Test
- Xem kết quả chạy thực tế bên dưới (`6` bộ unit test + kiểm tra `accoreconsole_adapter.py --audit-only` trên `KC-03_ChiTietMong_1.dwg` + `audit_zero_white_text.py`).

## 4. Sai sót / Lưu ý mở
- Chế độ tạo tệp nhị phân `DuAn.dst` native bằng AutoCAD Sheet Set Manager GUI/COM vẫn chưa tự động hóa (`sheet_set_manager_native_dst=False`); Sprint 3 chỉ khởi tạo khi người dùng chốt `8 vs 7 Workbook` và hình thức `DuAn.dst`.

## 5. Phạm vi đề nghị Claude xác nhận ở ca kiểm tra này
- Chỉ thực hiện **1 mục tiêu duy nhất (`SYSTEM_UPGRADE` / `CODE`)**: kiểm tra cầu nối Dual-Agent Bridge v3.6 (`NEED_REVIEW` / `environment_capabilities`), chạy thử `python .agents/tools/accoreconsole_adapter.py --audit-only` trên 4 DWG chi tiết `KC-03, KC-04, KC-08, KC-09`, và xác nhận toàn bộ test suite PASS.
