# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)

> **Dự án:** `MASTER_SYSTEM` — *Chuan hoa da may tram (user vs ADMIN), don cau hinh cu & tich hop MCP/Codex*  
> **Người gửi:** **CODEX** ➔ **Người nhận:** **CODEX**  
> **Thời điểm bàn giao:** `2026-11-25T17:22:47.045965+07:00`  
> **Trạng thái bàn giao (handoff_status):** `COMPLETED` *(Verification: `CONFIRMED_AND_HANDED_OFF`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Năng lực môi trường (v3.6):** `accoreconsole.exe`=CÓ (`C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe`) | chỉ-đọc: `python .agents/tools/accoreconsole_adapter.py --audit-only <path.dwg>` | `native_dst=False`  
> **Chế độ phân việc:** Linh hoạt tùy mục đích dự án  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `MASTER_SYSTEM`
- **Mục tiêu chính:** Chuan hoa da may tram (user vs ADMIN), don cau hinh cu & tich hop MCP/Codex
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

Hoàn tất 5 hạng mục MASTER_SYSTEM. Đã dọn quyền trỏ máy cũ, xóa bản sao hook, chuyển 3 script DCE sang thư mục tạm cục bộ, đăng ký dce-cad qua py -3 và đồng bộ CODEX_ONLY. Kiểm thử đạt Antigravity 8/8, Claude safety 7/7, dispatcher 22/22, bus v3.6 3/3, fast 24/24 suite. Kết nối MCP thật liệt kê đủ 15 công cụ.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.claude/settings.json`
2. `.claude/settings.local.json`
3. `.agents/memory/audits/dce_round2_20261114/analysis_tools/dce_round2_scan.py`
4. `.agents/memory/audits/dce_round2_20261114/analysis_tools/dce_round2_precision.py`
5. `.agents/memory/audits/dce_round2_20261114/analysis_tools/dce_round2_finalize.py`
6. `.agents/tools/mcp_config.json`
7. `.agents/tools/setup_dce_cad_mcp.py`
8. `.agents/skills/Global_Dispatcher/agent_selection.py`
9. `.agents/skills/Global_Dispatcher/dispatch_task.py`
10. `.agents/skills/Global_Dispatcher/intent_classifier.py`
11. `.agents/skills/Global_Dispatcher/product_deliverable_gate.py`
12. `.agents/skills/Global_Dispatcher/scripts/intent_classifier.py`
13. `.agents/tools/sync_bus.py`
14. `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/handover_task.py`
15. `.agents/tests/test_dispatcher_2d_modes.py`
16. `.agents/tests/test_mcp_dce_cad_server.py`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `CODEX`
- **Nhiệm vụ cụ thể (Task Description):**
  > Fix cac ton dong da may tram tren .agents/ va .claude/: (1) Don whitelist/duong dan cung C:\Users\ADMIN, C:\dev, D:\booktok-app, D:\AI VIDEO trong .claude/settings.json & settings.local.json va xoa .agents/hooks.json.recovery-backup; (2) Thay C:/Users/ADMIN/AppData/Local/Temp trong dce_round2_*.py bang tempfile.gettempdir() hoac archive; (3) Cap nhat .agents/tools/mcp_config.json chuan da may tram (py -3) + script setup MCP dce-cad cho may moi (C:\Users\user\.gemini\antigravity\mcp_config.json chua co); (4) Dong bo CODEX vao agent_selection.py / dispatch_task.py neu phu hop; (5) Chay test hook + dispatcher + run_all_tests --fast truoc khi dong ca (--complete --agent CODEX).

- **Tệp tin trọng tâm xử lý (Target Files):**
  - `.claude/settings.json`
  - `.claude/settings.local.json`
  - `.agents/hooks.json`
  - `.agents/tools/mcp_config.json`
  - `.agents/skills/Global_Dispatcher/agent_selection.py`
  - `.agents/skills/Global_Dispatcher/dispatch_task.py`
  - `.agents/memory/audits/dce_round2_20261114/analysis_tools/dce_round2_precision.py`

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 0 con hardcode C:/Users/ADMIN trong .claude/settings.json va active tools
  - [ ] Xoa .agents/hooks.json.recovery-backup
  - [ ] Cap nhat mcp_config.json + script setup MCP may moi
  - [ ] test_antigravity_dual_bus_hook.py + test_workspace_claude_safety_hook.py + test_dispatcher_2d_modes.py + run_all_tests --fast PASS 100%

- **Lệnh điều phối tương thích (Command):**
  > `Fix cac ton dong da may tram tren .agents/ va .claude/: (1) Don whitelist/duong dan cung C:\Users\ADMIN, C:\dev, D:\booktok-app, D:\AI VIDEO trong .claude/settings.json & settings.local.json va xoa .agents/hooks.json.recovery-backup; (2) Thay C:/Users/ADMIN/AppData/Local/Temp trong dce_round2_*.py bang tempfile.gettempdir() hoac archive; (3) Cap nhat .agents/tools/mcp_config.json chuan da may tram (py -3) + script setup MCP dce-cad cho may moi (C:\Users\user\.gemini\antigravity\mcp_config.json chua co); (4) Dong bo CODEX vao agent_selection.py / dispatch_task.py neu phu hop; (5) Chay test hook + dispatcher + run_all_tests --fast truoc khi dong ca (--complete --agent CODEX).`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*