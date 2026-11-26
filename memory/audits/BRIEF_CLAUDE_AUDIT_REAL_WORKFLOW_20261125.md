# BRIEF THẨM TRA ĐỘC LẬP CHO CLAUDE — KIỂM TRA QUY TRÌNH THỰC TẾ HỆ THỐNG

- **Ngày phát hành brief:** 2026-11-25 21:42 (+07:00)
- **Từ:** Antigravity (Gemini) thay mặt Chủ trì kỹ thuật
- **Gửi:** Claude (Auditor Độc lập — Software Architect / DevOps)
- **Workspace:** `G:\My Drive\Google AI Studio`
- **File kết quả đề nghị Claude xuất:** `.agents/memory/audits/CLAUDE_AUDIT_REAL_WORKFLOW_RESULT_20261125.md`

---

## ⚠️ RÀNG BUỘC AN TOÀN BẮT BUỘC

1. **KHÔNG chỉnh sửa, claim hay ghi đè `.agents/memory/DUAL_AGENT_BUS.json`** (và `_CA_HIEN_TAI.md`). Bus hiện đang giữ ca `03_Sprint2_KetQua_NeChu_CAD` ở trạng thái `NEED_REVIEW` (chờ thẩm tra gói `Sprint3_Xref_Workbook_R2`).
2. **KHÔNG chỉnh sửa 9 tệp đang khóa SHA-256 trong `release/v1.0/manifest.json`**:
   - `.agents/hooks.json`
   - `.claude/settings.json`
   - `.agents/tools/claude_safety_hook.py`
   - `.agents/tools/antigravity_dual_bus_hook.py`
   - `.agents/tools/mcp_dce_cad_server.py`
   - `.agents/tools/mcp_config.json`
   - `.mcp.json`
   - `bootstrap/hook_bootstrap.cmd`
   - `release/manifest_tool.py`
3. **Chỉ chạy kiểm chứng thực tế trên máy trạm hiện tại** và báo cáo trung thực mọi kết quả `PASS` / `WARN` / `FAIL` quan sát được. Nếu phát hiện lỗi cần vá ở 9 tệp khóa, chỉ **liệt kê và đề xuất phạm vi cắt bản `release v1.1`**.

---

## MỤC TIÊU KIỂM TRA (6 HẠNG MỤC THỰC TẾ)

### 1. Lớp Bootstrap & Runtime Máy Trạm (`bootstrap/`)
- Chạy `powershell -ExecutionPolicy Bypass -File .\bootstrap\doctor.ps1 -FailClosed`.
- Xác nhận nội dung thực tế tại `%LOCALAPPDATA%\GoogleAIStudio\machine.json` và `%LOCALAPPDATA%\GoogleAIStudio\python_exe.cache` (hiện đang trỏ tới `Python 3.12.7`).
- Kiểm tra hành vi `fail-closed` thực tế của `bootstrap/hook_bootstrap.cmd` (exit `125` khi chỉ có stub `WindowsApps`, exit `0` khi có Python hợp lệ) và kiểm tra tốc độ thực thi hook.
- Đánh giá lại `bootstrap/setup_machine.ps1` và `bootstrap/repair.ps1` sau sửa lỗi `$WorkspaceRoot` trên PowerShell 5.1.

### 2. Thực tế Vận Hành Hook & MCP (`py -3` Python 3.14 vs `Python 3.12.7`)
- Kiểm chứng sự lệch phiên bản thực tế trên máy: `py -3` mặc định đang trỏ tới Python `3.14` (chỉ có `pip`, thiếu `mcp`, `ezdxf`, `shapely`, `matplotlib`, `pymupdf`), trong khi `Python 3.12.7` có đủ dependency.
- Thử thực tế các hook trong `.agents/hooks.json` và `.claude/settings.json` (hiện đang khóa ở `v1.0` và gọi `py -3` trực tiếp thay vì đi qua `bootstrap/hook_bootstrap.cmd`) để xác nhận tác động khi Claude Code hoặc Antigravity kích hoạt hook thật.
- Kiểm tra kênh MCP `dce-cad`:
  - Khả năng khởi động của `.mcp.json` / `.agents/tools/mcp_config.json` khi gọi bằng `py -3` vs `py -3.12`.
  - Trạng thái đăng ký MCP user-level cho Antigravity (`C:\Users\ADMIN\.gemini\antigravity\mcp_config.json` hiện chưa tồn tại do chưa chạy `setup_machine.ps1 -RegisterMcp`).

### 3. Release Manifest `v1.0` & Chuẩn bị `v1.1` (`release/`)
- Chạy `py -3 -B .\release\manifest_tool.py verify --release-id v1.0` (xác nhận `VERIFY PASS` + CRLF).
- Kiểm tra thực tế các lệnh khác của `release/manifest_tool.py` (`verify` không truyền `--release-id`, `make`, `bus-checksum --write`, `register-machine`) để xác nhận chính xác các lỗi logic cần đưa vào danh sách sửa cho `release v1.1`.
- Đối chiếu `release/machine_registry.json` (hiện vẫn còn bản ghi cũ `LAPTOPTIENDUC` `python_version: "3.11.9"`).

### 4. Chống Ô Nhiễm BUS / `_CA_HIEN_TAI.md` & Test Isolation
- Kiểm tra guard `is_relative_to` trong `.agents/tools/sync_bus.py` khi ghi `ACTIVE_POINTER_PATH` (`_CA_HIEN_TAI.md`).
- Chạy thử các bộ test từng gây ô nhiễm (`test_dual_agent_bridge.py`, `test_cognitive_and_control_systems.py`, `test_bootstrap_matrix.py`), sau đó kiểm chứng rằng:
  - `.agents/memory/_CA_HIEN_TAI.md` vẫn khớp byte với `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`.
  - `%LOCALAPPDATA%\GoogleAIStudio\python_exe.cache` vẫn tồn tại và không bị xóa.

### 5. Hậu quả Dọn dẹp Thư mục & Tính Liên Thông Hệ Thống
- Xác nhận sau đợt dọn dẹp 25/11/2026 (xóa `.pytest_cache/` gốc, `release/__pycache__/`, `74` `*.cpython-314.pyc`, `.agents/memory/audits/__pycache__/`; chuyển `Archive_Old_Reports`, `Prompt_Templates`, `Scripts_Tien_Ich` vào `00_Template_&_Standards/99_Archive/`):
  - Không làm gãy đường dẫn tới `CAD_Forms/`, `DU AN MAU/`, `THƯ MUC DCE/`, hoặc bất kỳ script/test nào.
  - Chạy `py -3.12 -B .agents/tests/run_all_tests.py --fast` (`27/60` suites) và đối chiếu `.agents/docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` (`60/60` suites, `1088 passed / 0 failed`, `0 stale-claims`).
  - Kiểm tra `py -3.12 -B .agents/tools/audit_zero_white_text.py .agents` (`0 warnings`).

### 6. Rà soát Thêm Vấn đề Tồn Đọng (Nếu có) & Kế Hoạch Chốt `v1.1`
- Kiểm tra `Global_Dispatcher/intent_classifier.py` (rule `.agents`), `cad_plan_engine.py` (guard khi thiếu `ezdxf`), và `tools/_collect_tests.py` (`60/60` suites parsed, `unparsed_suites: []`).
- Đưa ra kết luận rạch ròi theo 3 phần:
  1. **Những gì ĐÃ CHẠY THẬT ĐƯỢC NGAY trên quy trình thực tế**
  2. **Những điểm ĐANG TẮC / CẦN XỬ LÝ NGOÀI THỰC TẾ** (nhất là `py -3` 3.14 vs 3.12, đăng ký MCP, `manifest_tool.py`)
  3. **Checklist hành động tối thiểu để cắt `release v1.1` an toàn** (mà vẫn bảo toàn ca `03_Sprint2_KetQua_NeChu_CAD` trên Bus).
