# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)

> **Dự án:** `SKILL_DUAL_AGENT_BRIDGE` — *Trien khai P2 MCP Perception Loop (mcp_dce_cad_server.py) va Visual Gate v3.3*  
> **Người gửi:** **GEMINI** ➔ **Người nhận:** **CLAUDE**  
> **Thời điểm bàn giao:** `2026-11-20T15:28:23.918346+07:00`  
> **Trạng thái bàn giao (handoff_status):** `NEED_REVIEW` *(Verification: `REVIEW_REQUIRED`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Linh hoạt tùy mục đích dự án  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `SKILL_DUAL_AGENT_BRIDGE`
- **Mục tiêu chính:** Trien khai P2 MCP Perception Loop (mcp_dce_cad_server.py) va Visual Gate v3.3
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

P2 KHEP VONG: Gemini da hoan thanh loop CAD perception, xuat PNG preview 300 DPI, JSON audit physical PASS, va dong bang bang chung SHA-256 tren dia theo dung SPEC P2.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.agents/_SHARED/SHARED_CONTEXT/_active/RECEIPTS`
2. `.agents/_SHARED/SHARED_CONTEXT/cad_layer_standard.py`
3. `.agents/_SHARED/data/CAD_Forms`
4. `.agents/_SHARED/data/DCE_LAYER_REFERENCE.md`
5. `.agents/_SHARED/data/DCE_Pro_And_Steel_Template.dxf`
6. `.agents/_SHARED/data/dce_layers_standard.json`
7. `.agents/_SHARED/data/model_schema.json`
8. `.agents/_SHARED/data/ncr_schema.json`
9. `.agents/docs/ARGON_AUDIT_DOSSIER_v7.5_CAD_SPECIAL.md`
10. `.agents/docs/MCP_DCE_CAD_CONTRACT.md`
11. `.agents/docs/RUNBOOK_P0_OPS_HYBRID_CAD.md`
12. `.agents/docs/SPEC_P2_MCP_PERCEPTION_LOOP.md`
13. `.agents/memory/CAD_UPGRADE_V6_TASK_PLAN.md`
14. `.agents/memory/CLAUDE_P0OPS_REVIEW_AND_P1_SPEC.md`
15. `.agents/memory/CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`
16. `.agents/memory/CLAUDE_RESPONSE_4FORM_AND_BLOCKS.md`
17. `.agents/memory/CLAUDE_STRATEGIC_RESPONSE_CAD_ROADMAP.md`
18. `.agents/memory/CLAUDE_STRATEGIC_REVIEW_CAD_ROADMAP.md`
19. `.agents/memory/DECISION_OPS_HYBRID_AUTHORING_20261116.md`
20. `.agents/memory/DISCUSSION_4FORM_EDITABLE_CAD_AND_DCE_BLOCKS.md`
21. `.agents/memory/DUAL_AGENT_ANTIGRAVITY_ORCHESTRATION_ANALYSIS.md`
22. `.agents/memory/DUAL_AGENT_BUS.json`
23. `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`
24. `.agents/memory/HANDOFF_CAD_ARCH_REVIEW_20261116.md`
25. `.agents/memory/PROPOSAL_DUAL_AGENT_V32_RESEARCH.md`
26. `.agents/memory/archive/bak_v46`
27. `.agents/memory/audits/AUDIT_REPORT_CAD_V50_CODEX.md`
28. `.agents/memory/audits/AUDIT_REPORT_CAD_V50_FINAL.md`
29. `.agents/memory/audits/BRIEF_CODEX_ANALYSIS_NHA_PHO_CAT_LAI.md`
30. `.agents/memory/audits/CODEX_ANALYSIS_NHA_PHO_CAT_LAI.md`
31. `.agents/memory/audits/archive/202611_sprint_logs`
32. `.agents/memory/audits/archive/foreign_workspaces`
33. `.agents/memory/audits/audit_cad_v50_geometry.json`
34. `.agents/memory/audits/audit_cad_v50_geometry.py`
35. `.agents/memory/audits/cad_v6`
36. `.agents/memory/audits/catlai_p11.png`
37. `.agents/memory/audits/catlai_p19.png`
38. `.agents/memory/audits/catlai_p22.png`
39. `.agents/memory/audits/catlai_p8.png`
40. `.agents/memory/audits/skill_dual_agent_bridge`
41. `.agents/memory/test_reports`
42. `.agents/skills/SKILL_VERIFY/scripts/cad_evidence_contract.py`
43. `.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py.bak_v46`
44. `.agents/skills/Technical_Illustrator/DCE_BLOCK_TAG_GUIDE.md`
45. `.agents/skills/Technical_Illustrator/STRUCTURAL_SHEET_SET_GUIDE.md`
46. `.agents/skills/Technical_Illustrator/cad_integration/bim_model_translator.py`
47. `.agents/skills/Technical_Illustrator/cad_integration/cad_block_adapters.py`
48. `.agents/skills/Technical_Illustrator/cad_integration/cad_defect_cropper.py`
49. `.agents/skills/Technical_Illustrator/cad_integration/cad_element_registry.py`
50. `.agents/skills/Technical_Illustrator/cad_integration/cad_form_contract.py`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `CLAUDE`
- **Nhiệm vụ cụ thể (Task Description):**
  > Nghiem thu P1 v3.3, xac nhan SPEC_P2_MCP_PERCEPTION_LOOP.md (1 trang), chuan bi dogfooding tren sandbox cad_v6

- **Tệp tin trọng tâm xử lý (Target Files):**
  - `.agents/docs/SPEC_P2_MCP_PERCEPTION_LOOP.md`
  - `.agents/tools/mcp_dce_cad_server.py`
  - `.agents/tools/sync_bus.py`

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 1. Chot SPEC P2 giu nguyen 1 trang khong tach nho tren bus
  - [ ] 2. Expose du 13 tools cua mcp_dce_cad_server.py
  - [ ] 3. Bao toan 39/39 tests PASS tren Windows
  - [ ] 4. Tach biet tuyet doi workspace G-drive khoi J-drive

- **Lệnh điều phối tương thích (Command):**
  > `Nghiem thu P1 v3.3, xac nhan SPEC_P2_MCP_PERCEPTION_LOOP.md (1 trang), chuan bi dogfooding tren sandbox cad_v6`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*