# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.0)

> **Dự án:** `00_GENERAL` — *Nghiém thu Planned Upgrade Cycle v13.0*  
> **Người gửi:** **CLAUDE** ➔ **Người nhận:** **GEMINI**  
> **Thời điểm bàn giao:** `2026-11-19T21:06:14.332759+07:00`  
> **Trạng thái bàn giao (handoff_status):** `PENDING` *(Verification: `CONFIRMED_AND_HANDED_OFF`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Linh hoạt tùy mục đích dự án  
> **Kênh bus nguyên tử:** `memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `00_GENERAL`
- **Mục tiêu chính:** Nghiém thu Planned Upgrade Cycle v13.0
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

v13.0 nâng cấp hoàn tất: A-E sạch, 50/50 tests PASS, 0 hardcode ô thuế quan trọng (riêng B2 đã báo cáo)

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
12. `.agents/memory/CAD_UPGRADE_V6_TASK_PLAN.md`
13. `.agents/memory/CLAUDE_P0OPS_REVIEW_AND_P1_SPEC.md`
14. `.agents/memory/CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`
15. `.agents/memory/CLAUDE_RESPONSE_4FORM_AND_BLOCKS.md`
16. `.agents/memory/CLAUDE_STRATEGIC_RESPONSE_CAD_ROADMAP.md`
17. `.agents/memory/CLAUDE_STRATEGIC_REVIEW_CAD_ROADMAP.md`
18. `.agents/memory/DECISION_OPS_HYBRID_AUTHORING_20261116.md`
19. `.agents/memory/DISCUSSION_4FORM_EDITABLE_CAD_AND_DCE_BLOCKS.md`
20. `.agents/memory/DUAL_AGENT_ANTIGRAVITY_ORCHESTRATION_ANALYSIS.md`
21. `.agents/memory/HANDOFF_CAD_ARCH_REVIEW_20261116.md`
22. `.agents/memory/PROPOSAL_DUAL_AGENT_V32_RESEARCH.md`
23. `.agents/memory/archive/bak_v46`
24. `.agents/memory/audits/AUDIT_REPORT_CAD_V50_CODEX.md`
25. `.agents/memory/audits/AUDIT_REPORT_CAD_V50_FINAL.md`
26. `.agents/memory/audits/BRIEF_CODEX_ANALYSIS_NHA_PHO_CAT_LAI.md`
27. `.agents/memory/audits/CODEX_ANALYSIS_NHA_PHO_CAT_LAI.md`
28. `.agents/memory/audits/archive/202611_sprint_logs`
29. `.agents/memory/audits/audit_cad_v50_geometry.json`
30. `.agents/memory/audits/audit_cad_v50_geometry.py`
31. `.agents/memory/audits/cad_v6`
32. `.agents/memory/audits/catlai_p11.png`
33. `.agents/memory/audits/catlai_p19.png`
34. `.agents/memory/audits/catlai_p22.png`
35. `.agents/memory/audits/catlai_p8.png`
36. `.agents/memory/audits/skill_dual_agent_bridge`
37. `.agents/memory/test_reports`
38. `.agents/skills/SKILL_VERIFY/scripts/cad_evidence_contract.py`
39. `.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py.bak_v46`
40. `.agents/skills/Technical_Illustrator/DCE_BLOCK_TAG_GUIDE.md`
41. `.agents/skills/Technical_Illustrator/STRUCTURAL_SHEET_SET_GUIDE.md`
42. `.agents/skills/Technical_Illustrator/cad_integration/bim_model_translator.py`
43. `.agents/skills/Technical_Illustrator/cad_integration/cad_block_adapters.py`
44. `.agents/skills/Technical_Illustrator/cad_integration/cad_defect_cropper.py`
45. `.agents/skills/Technical_Illustrator/cad_integration/cad_element_registry.py`
46. `.agents/skills/Technical_Illustrator/cad_integration/cad_form_contract.py`
47. `.agents/skills/Technical_Illustrator/cad_integration/cad_form_generator.py`
48. `.agents/skills/Technical_Illustrator/cad_integration/cad_form_patcher.py`
49. `.agents/skills/Technical_Illustrator/cad_integration/cad_multiview_a3.py`
50. `.agents/skills/Technical_Illustrator/cad_integration/cad_paperspace_builder.py`
51. `memory/DUAL_AGENT_BUS.json`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `GEMINI`
- **Nhiệm vụ cụ thể (Task Description):**
  > Review & ngiệm thu v13.0: (1) chạy lại 50/50 tax + 6/6 dual-agent tests; (2) xác nhận 14/20 invariants - 6 cái INV_04/10/11/12/14/15 là cache-dependent (thiếu LibreOffice/Excel formula cache trên máy này, pre-existing, không phải regression); (3) đọc CLAUDE_UPGRADE_BRIEF_v13.md §6 checklist + 3 ghi chú bổ sung; (4) xác nhận gap protocol CLI sync_bus --summary/--status.

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 50/50 Unit Tests PASS
  - [ ] 14/20 Invariants (6 cache-dependent)
  - [ ] 0% chữ trắng canonical workpapers
  - [ ] C3 18/18 DK live
  - [ ] D1+D2 v3.2.0 hoạt động

- **Lệnh điều phối tương thích (Command):**
  > `Review & ngiệm thu v13.0: (1) chạy lại 50/50 tax + 6/6 dual-agent tests; (2) xác nhận 14/20 invariants - 6 cái INV_04/10/11/12/14/15 là cache-dependent (thiếu LibreOffice/Excel formula cache trên máy này, pre-existing, không phải regression); (3) đọc CLAUDE_UPGRADE_BRIEF_v13.md §6 checklist + 3 ghi chú bổ sung; (4) xác nhận gap protocol CLI sync_bus --summary/--status.`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.0 dưới cơ chế khóa nguyên tử FileLock & Anti-Collision Mutex.*