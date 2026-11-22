# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)

> **Dự án:** `TIER2_PHASE2A_REVIEW_AND_2B_DESIGN_20261122` — *Kiểm toán độc lập Tầng 2 — Giai đoạn 2A (Xương sống dữ liệu, XData element_id/role, MCP 5 profiles, BIM/Revit mapper) và đề xuất giải pháp tối ưu của Claude cho Giai đoạn 2B (AutoCAD 2021 Native DWG + Snapshot Diff) & 2C (Revit 2024 Read-Only Pilot + IFC)*  
> **Người gửi:** **CLAUDE** ➔ **Người nhận:** **CLAUDE**  
> **Thời điểm bàn giao:** `2026-11-22T22:17:27.855987+07:00`  
> **Trạng thái bàn giao (handoff_status):** `COMPLETED` *(Verification: `CONFIRMED_AND_HANDED_OFF`)*  
> **Tác tử giữ ca (current_holder):** `IDLE`  
> **Chế độ phân việc:** Gemini: Triển khai Tầng 2 Giai đoạn 2A & đẩy mốc Tầng 1 lên GitHub (b0614d0); Claude: Chủ trì Kiểm toán Độc lập Giai đoạn 2A (51/51 suites) & Đề xuất Giải pháp Kiến trúc Tối ưu cho Tầng 2B/2C  
> **Kênh bus nguyên tử:** `.agents/memory/DUAL_AGENT_BUS.json`  

---

## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG

- **Mã dự án:** `TIER2_PHASE2A_REVIEW_AND_2B_DESIGN_20261122`
- **Mục tiêu chính:** Kiểm toán độc lập Tầng 2 — Giai đoạn 2A (Xương sống dữ liệu, XData element_id/role, MCP 5 profiles, BIM/Revit mapper) và đề xuất giải pháp tối ưu của Claude cho Giai đoạn 2B (AutoCAD 2021 Native DWG + Snapshot Diff) & 2C (Revit 2024 Read-Only Pilot + IFC)
- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.

---

## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN

Đã kiểm tra 8 tệp Tầng 2A, suite riêng 6/6 PASS, full regression 51/51 PASS trong 313.06s, audit_zero_white_text 0 warnings. Đề xuất 2B/2C chi tiết đã lưu tại memory/audits/TIER2_PHASE2A_REVIEW_2B_2C_ARCHITECTURE.md.

---

## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)

1. `.agents/docs/MCP_DCE_CAD_CONTRACT.md`
2. `.agents/skills/Global_Dispatcher/sync_bus_2d_patch.py`
3. `.agents/skills/Technical_Illustrator/cad_integration/bim_model_translator.py`
4. `.agents/skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`
5. `.agents/skills/Technical_Illustrator/cad_integration/revit_family_parameter_mapper.py`
6. `.agents/tools/dce_xdata_bridge.py`
7. `.agents/tools/mcp_dce_cad_server.py`
8. `.agents/tests/test_tier2_phase2a_foundation.py`
9. `.agents/memory/DUAL_AGENT_BUS.json`

---

## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

- **Tác tử tiếp nhận:** `CLAUDE`
- **Nhiệm vụ cụ thể (Task Description):**
  > /sys Kiểm toán độc lập 8 tệp Tầng 2 Giai đoạn 2A (mcp_dce_cad_server.py, MCP_DCE_CAD_CONTRACT.md, cad_plan_engine.py, dce_xdata_bridge.py, bim_model_translator.py, revit_family_parameter_mapper.py, sync_bus_2d_patch.py, test_tier2_phase2a_foundation.py), chạy run_all_tests.py --full & audit_zero_white_text.py, đồng thời đưa ra phản biện kỹ thuật và giải pháp tối ưu nhất của Claude cho Tầng 2B (AutoCAD 2021 accoreconsole.exe Native DWG + Snapshot Diff D1/D1A) và Tầng 2C (Revit 2024 Read-Only Pilot + IFC) trước khi triển khai 2B

- **Tệp tin trọng tâm xử lý (Target Files):**
  - `.agents/tools/mcp_dce_cad_server.py`
  - `.agents/tools/dce_xdata_bridge.py`
  - `.agents/skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`
  - `.agents/skills/Technical_Illustrator/cad_integration/bim_model_translator.py`
  - `.agents/skills/Technical_Illustrator/cad_integration/revit_family_parameter_mapper.py`
  - `.agents/skills/Global_Dispatcher/sync_bus_2d_patch.py`
  - `.agents/tests/test_tier2_phase2a_foundation.py`

- **Tiêu chí nghiệm thu (Checklist Verification):**
  - [ ] 1. Xác nhận 8 tệp Tầng 2A không gây hồi quy Tầng 1 và đạt 100% PASS trên run_all_tests.py --full (51/51 suites) + audit_zero_white_text.py (0 warnings)
  - [ ] 2. Đánh giá trực diện thiết kế XData DCE_ELEMENT_ID (element_id, role), Canonical Model và bim_model_translator/revit_family_parameter_mapper (chỉ rõ điểm cần tối ưu thêm nếu có)
  - [ ] 3. Đề xuất giải pháp kiến trúc tối ưu cụ thể cho Tầng 2B (AutoCAD 2021 accoreconsole.exe Native DWG + Snapshot Diff D1/D1A) và Tầng 2C (Revit 2024 Read-Only + IFC) kèm phân công Gemini-Claude

- **Lệnh điều phối tương thích (Command):**
  > `python .agents/tools/sync_bus.py --claim --agent CLAUDE`

---

*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*