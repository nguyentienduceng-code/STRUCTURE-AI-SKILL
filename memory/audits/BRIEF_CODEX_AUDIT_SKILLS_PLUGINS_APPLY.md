# YÊU CẦU RÀ SOÁT TÀI NGUYÊN SKILL - PLUGIN (DÀNH CHO CODEX)

> **Mục tiêu duy nhất:** Kiểm tra, đánh giá chi tiết các tài nguyên Skill - Plugin bên ngoài vừa tải về từ mục `skill-plugin` tại thư mục `.agents/references/anhkysuai_skill_plugin/`.  
> **Phạm vi kiểm tra:** CHỈ tập trung vào các tài nguyên được tải về, KHÔNG rà soát hay can thiệp vào bộ 14 kỹ năng nội bộ của hệ thống.

---

## 1. VỊ TRÍ TÀI NGUYÊN CẦN RÀ SOÁT

Toàn bộ tài nguyên đã được lưu tại:
`g:\My Drive\Google AI Studio\.agents\references\anhkysuai_skill_plugin\`

Gồm các thư mục:
1. `01_Nhom_1_Ap_Dung_Ngay/`:
   - `anthropics-skills`: Bộ skill mẫu chính thức từ Anthropic.
   - `awesome-claude-code`: Tổng hợp cấu hình, hooks, commands cho Claude Code.
   - `obra-superpowers`: Quy trình kỹ thuật agentic skills, TDD, subagent review.
   - `garrytan-gstack`: Bộ lệnh phân vai kỹ sư bằng slash commands.
2. `02_Nhom_2_Tham_Khao_Chon_Loc/`:
   - `awesome-claude-skills-composio` & `awesome-claude-skills-travisvn`: Thư viện kỹ năng mở rộng.
   - `frontend-slides`: Mẫu sinh slide thuyết trình.
   - `prompt-engineering-guide`: Tài liệu kỹ thuật prompt & reasoning từ DAIR.AI.
3. `03_Nhom_3_Doi_Chieu_CAD_AEC/`:
   - `autocad-mcp`: Dự án CAD MCP mã nguồn mở.
4. `04_Tham_Chieu_MCP_Noi_Bo_Archived/`:
   - Các gói MCP lưu trữ: `horizun-revit-mcp.zip`, `rvt-mcp.zip`, `agent-circuit-breaker.zip`, `rule-engine.zip`, `pyconcrete.zip`, `simple-graph.zip`.

---

## 2. NỘI DUNG CODEX CẦN THỰC HIỆN

Codex chỉ cần trả lời 3 câu hỏi thực tế sau:

1. **Khảo sát & Phân loại:**
   - Trong các tài nguyên trên, những công cụ / skill / script nào hoạt động thực sự và có mã nguồn hoàn chỉnh?
   - Những tài nguyên nào chỉ là danh sách liên kết (curated links) hoặc tài liệu đọc tham khảo?

2. **Đánh giá Giá trị Thực tế:**
   - Những thành phần nào hữu ích, có thể trích xuất dùng được ngay cho quy trình làm việc của Claude Code (ví dụ: các đoạn code Hook, cấu hình settings, mẫu slash commands)?
   - Những thành phần nào không phù hợp, cồng kềnh hoặc không cần bận tâm?

3. **Báo cáo Tóm tắt Gọn gàng:**
   - Xuất danh sách đánh giá ngắn gọn, thực dụng (không dài dòng lý thuyết) vào file:
     `.agents/memory/audits/CODEX_DANH_GIA_SKILL_PLUGIN.md`

---
*Yêu cầu tập trung 100% vào tài nguyên trong references/anhkysuai_skill_plugin, không mở rộng sang các file khác.*
