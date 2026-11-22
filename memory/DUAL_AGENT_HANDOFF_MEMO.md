# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)

> **Dự án:** `MASTER_STRATEGY_V8_STANDARDS_SYNC_20261122` — *Đồng bộ Chiến lược Kiến trúc 3 Tầng v8.0, hoàn thiện Tầng 1 (TVTT/CĐT, /sys dispatch, IFC CDC-04, Cross-Doc CDC-01/06, ClashDetector, RFI/NCR G8.21-25) và cập nhật thư viện tiêu chuẩn/pháp lý 2026 (TT 34/2026/TT-BXD, NĐ 217/2026/NĐ-CP, QCVN 18:2021/BXD)*  
> **Người gửi:** **CLAUDE** ➔ **Người nhận:** **CLAUDE**  
> **Thời điểm bàn giao:** `2026-11-22T21:43:27.646845+07:00`  
> **Trạng thái bàn giao (handoff_status):** `COMPLETED` *(Verification: `CONFIRMED_AND_HANDED_OFF`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Gemini: Triển khai Chiến lược v8.0, cập nhật STANDARDS_LOCK v3.3.0 / standards_graph.py và vá dứt điểm các lỗi Tầng 1; Claude: Chủ trì Thẩm định Kiến trúc & Kiểm toán Độc lập 50/50 suites trước khi chốt commit  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `MASTER_STRATEGY_V8_STANDARDS_SYNC_20261122`
- **Mục tiêu chính:** Đồng bộ Chiến lược Kiến trúc 3 Tầng v8.0, hoàn thiện Tầng 1 (TVTT/CĐT, /sys dispatch, IFC CDC-04, Cross-Doc CDC-01/06, ClashDetector, RFI/NCR G8.21-25) và cập nhật thư viện tiêu chuẩn/pháp lý 2026 (TT 34/2026/TT-BXD, NĐ 217/2026/NĐ-CP, QCVN 18:2021/BXD)
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

Đã kiểm toán bản cập nhật Gemini: 5 vá Tầng 1 xác nhận; E004 bắt đúng NĐ 175/2024 và QCVN 18:2014; audit_zero_white_text 0 warnings; run_all_tests.py --full 50/50 PASS trong 303.17s.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.agents/_SHARED/standards/standards_graph.py`
2. `.agents/docs/DEEPRESEARCH_CONTEXT_HE_THONG_VA_CAD_REVIT_V8.md`
3. `.agents/docs/MASTER_STRATEGY_3_TIERS_V8.md`
4. `.agents/docs/STRATEGIC_ALIGNMENT_GEMINI_CODEX.md`
5. `.agents/docs/TECHNICAL_DEBT.md`
6. `.agents/skills/Design_Evaluation/standards/INDEX.md`
7. `.agents/skills/Design_Evaluation/standards/INDEX_QUICK.md`
8. `.agents/skills/Design_Evaluation/standards/QCVN/3b. Thong tu 34-2026_TT-BXD_Phan cap cong trinh.pdf`
9. `.agents/skills/Design_Evaluation/standards/QCVN/3c. Nghi dinh 217-2026_ND-CP_Quan ly hoat dong xay dung.pdf`
10. `.agents/skills/Design_Evaluation/standards/QCVN/7. QCVN 18-2021_AN TOAN TRONG THI CONG XAY DUNG.pdf`
11. `.agents/skills/Global_Dispatcher/intent_classifier.py`
12. `.agents/skills/Global_Dispatcher/sync_bus_2d_patch.py`
13. `.agents/skills/SKILL_BIM_COORDINATION/scripts/clash_detector.py`
14. `.agents/skills/SKILL_INDEX.md`
15. `.agents/skills/SKILL_RFI/SKILL.md`
16. `.agents/skills/SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`
17. `.agents/skills/STANDARDS_LOCK.md`
18. `.agents/tools/_collect_tests.py`
19. `.agents/tools/ifc_parser.py`
20. `.agents/tools/rfi_ncr_bridge.py`
21. `.agents/tools/sync_bus.py`
22. `.agents/memory/DUAL_AGENT_BUS.json`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `CLAUDE`
- **Nhiệm vụ cụ thể (Task Description):**
  > /sys Nhận ca kiểm toán chéo & làm việc chung trên bản hoàn thiện Tầng 1 (Chiến lược 3 Tầng v8.0) và Cập nhật Tiêu chuẩn Pháp lý 2026: (1) Rà soát các file mới/đã sửa trong working tree (bao gồm cả 5 bản vá Tầng 1 mới cập nhật); (2) Kiểm chứng PDF Citation Grounding (S23), R&D Patches (S21), Phase 2 Tools (Suite 9), Sprint 2 Conflict Control (Suite 8), P4 RFI/NCR, Dispatcher 2D Modes và chạy full regression run_all_tests.py --full (50/50 suites); (3) Xác nhận COMPLETED hoặc NEED_REVIEW để chốt git commit.

- **Tệp tin trọng tâm xử lý (Target Files):**
  - `.agents/skills/Global_Dispatcher/sync_bus_2d_patch.py`
  - `.agents/skills/SKILL_BIM_COORDINATION/scripts/clash_detector.py`
  - `.agents/tools/ifc_parser.py`
  - `.agents/skills/SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`
  - `.agents/tools/rfi_ncr_bridge.py`
  - `.agents/skills/STANDARDS_LOCK.md`
  - `.agents/_SHARED/standards/standards_graph.py`
  - `.agents/docs/MASTER_STRATEGY_3_TIERS_V8.md`
  - `.agents/docs/DEEPRESEARCH_CONTEXT_HE_THONG_VA_CAD_REVIT_V8.md`

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 1. Xác nhận 3 PDF tiêu chuẩn/pháp lý mới trong standards/QCVN/ (3b TT 34/2026, 3c NĐ 217/2026, 7 QCVN 18:2021) VERIFIED qua CitationGroundingAuditor và StandardsGraph bắt đúng E004
  - [ ] 2. Kiểm chứng 5 điểm vá Tầng 1 (sync_bus_2d_patch /sys, clash_detector --input/--ifc, ifc_parser CDC-04 tầng hầm, cross_doc_conflict_checker CDC-01/CDC-06, rfi_ncr_bridge G8.21..G8.25)
  - [ ] 3. Chạy full regression run_all_tests.py --full đạt 50/50 PASS và audit_zero_white_text.py = 0 warnings

- **Lệnh điều phối tương thích (Command):**
  > `python .agents/tools/sync_bus.py --claim --agent CLAUDE`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*