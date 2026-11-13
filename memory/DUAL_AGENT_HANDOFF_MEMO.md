# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.0)

> **Dự án:** `00_SYSTEM_STRUCTURE_AGENT_STANDALONE` — *Kiem toan doc lap he thong sau tai cau truc bo Agent Structure khep kin*  
> **Người gửi:** **CODEX** ➔ **Người nhận:** **GEMINI**  
> **Thời điểm bàn giao:** `2026-11-13T22:26:28.244856+07:00`  
> **Trạng thái bàn giao (handoff_status):** `COMPLETED` *(Verification: `FIXES_VERIFIED_PASS`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Linh hoạt tùy mục đích dự án  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `00_SYSTEM_STRUCTURE_AGENT_STANDALONE`
- **Mục tiêu chính:** Kiem toan doc lap he thong sau tai cau truc bo Agent Structure khep kin
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

Fixed F01-F05. Recovered 663 rvt-mcp ZIP entries; 7/7 archives CRC verified. Ownership race/holder guards pass. Root/memory paths corrected. Fixed absolute CLI defaults and CAD registry. Full 27/27 PASS (89.46s), fast 17/17 PASS (11.57s). Historical pre-archive completeness is unknown; original damaged ZIP preserved.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.agents/tools/sync_bus.py`
2. `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py`
3. `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/SKILL.md`
4. `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/templates/DUAL_AGENT_HANDOFF_MEMO_TEMPLATE.md`
5. `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/tests/test_dual_agent_bridge.py`
6. `.agents/tests/run_all_tests.py`
7. `.agents/skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`
8. `.agents/skills/Technical_Illustrator/cad_integration/dce_dxf_generator.py`
9. `.agents/skills/Project_Manager/scripts/msproject_bridge.py`
10. `.agents/skills/Technical_Illustrator/scripts/registry.json`
11. `.agents/skills/Design_Evaluation/scripts/validate_registry.py`
12. `.agents/skills/Design_Evaluation/modules/script_discovery.py`
13. `.agents/_references_archived/rvt-mcp.zip`
14. `.agents/_references_archived/rvt-mcp.manifest.json`
15. `.agents/_references_archived/verified_manifest.json`
16. `.agents/_references_archived/README.md`
17. `.agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/REPORT.md`
18. `.agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/summary.json`
19. `.agents/memory/DUAL_AGENT_BUS.json`
20. `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `GEMINI`
- **Nhiệm vụ cụ thể (Task Description):**
  > F01-F05 repaired and verified. Optional independent review of repair report; archive manifest certifies present contents only, not historical repository completeness.

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] All seven reference ZIPs pass CRC and have a verified source manifest
  - [ ] A different agent cannot claim an IN_PROGRESS bus
  - [ ] Workspace and bus paths resolve correctly from root, nested and external working directories
  - [ ] No project-specific fixed absolute defaults remain in the identified CAD/Project entrypoints
  - [ ] Registry validator reports no missing CAD files
  - [ ] Independent full runner remains 27/27 PASS

- **Lệnh điều phối tương thích (Command):**
  > `Read .agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/REPORT.md`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.0 dưới cơ chế khóa nguyên tử FileLock & Anti-Collision Mutex.*