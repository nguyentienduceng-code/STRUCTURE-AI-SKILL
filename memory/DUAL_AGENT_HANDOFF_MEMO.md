# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)

> **Dự án:** `SKILL_CAD_DCE_PRO` — *Nang cap he thong ve CAD tham so DCE Pro v4.7 len v5.0 (PEB Thep & BPTC)*  
> **Người gửi:** **GEMINI** ➔ **Người nhận:** **CLAUDE**  
> **Thời điểm bàn giao:** `2026-11-22T14:30:08.975747+07:00`  
> **Trạng thái bàn giao (handoff_status):** `COMPLETED` *(Verification: `CONFIRMED_AND_HANDED_OFF`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Gemini: Maker / Software Architect; Claude: Lead Auditor / Verifier  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `SKILL_CAD_DCE_PRO`
- **Mục tiêu chính:** Nang cap he thong ve CAD tham so DCE Pro v4.7 len v5.0 (PEB Thep & BPTC)
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

Hoàn tất DCE Pro v5.0 và 5 hạng mục backlog K1-K5 (evidence-based G8.21/22/25, DXF byte SHA-256 sidecar, đồng bộ SPEC lineweight, parse_steel_profile 2U/warning, weld lw toàn bộ), cập nhật SKILL_INDEX và metrics hệ thống.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.agents/_SHARED/data/dce_layers_standard.json`
2. `.agents/_SHARED/SHARED_CONTEXT/cad_layer_standard.py`
3. `.agents/skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`
4. `.agents/skills/Technical_Illustrator/cad_integration/cad_steel_primitives.py`
5. `.agents/skills/Technical_Illustrator/cad_integration/cad_bptc_engine.py`
6. `.agents/skills/Technical_Illustrator/cad_integration/cad_steel_peb_engine.py`
7. `.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py`
8. `.agents/skills/Design_Evaluation/scripts/cad_deep_reader.py`
9. `.agents/skills/Technical_Illustrator/references/SPEC_DCE_PRO_V5.md`
10. `.agents/skills/Technical_Illustrator/SKILL.md`
11. `.agents/tests/test_cad_composite_grid.py`
12. `.agents/tests/test_cad_steel_primitives.py`
13. `.agents/tests/test_cad_bptc_engine.py`
14. `.agents/tests/test_cad_steel_peb_engine.py`
15. `.agents/memory/audits/skill_dual_agent_bridge/gemini/G_RESULT_CAD_V5.md`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `CLAUDE`
- **Nhiệm vụ cụ thể (Task Description):**
  > Thẩm tra kiến trúc và mã nguồn DCE Pro v5.0 (cad_steel_primitives.py, cad_bptc_engine.py, cad_steel_peb_engine.py, dce_cad_compliance_checker.py), nghiệm thu 25 cổng G8.01-G8.25 và đóng ca nâng cấp.

- **Tệp tin trọng tâm xử lý (Target Files):**
  - `.agents/skills/Technical_Illustrator/cad_integration/cad_steel_primitives.py`
  - `.agents/skills/Technical_Illustrator/cad_integration/cad_bptc_engine.py`
  - `.agents/skills/Technical_Illustrator/cad_integration/cad_steel_peb_engine.py`
  - `.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py`
  - `.agents/skills/Technical_Illustrator/references/SPEC_DCE_PRO_V5.md`

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 1. 100% test suites run_all_tests.py --fast PASS không hồi quy 20 cổng BTCT
  - [ ] 2. 16/16 unit tests CAD mới PASS
  - [ ] 3. Tuân thủ tiêu chuẩn TCVN 5575:2024, QCVN 18:2021/BXD và Điều 12b AGENTS.md (Zero White Text Lock)
  - [ ] 4. Đối soát 25/25 cổng G8.01-G8.25 đạt chuẩn full_compliance_verified

- **Lệnh điều phối tương thích (Command):**
  > `python .agents/tests/run_all_tests.py --fast`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*