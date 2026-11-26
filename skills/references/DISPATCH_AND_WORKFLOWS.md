# ĐIỀU 0: MA TRẬN PHÂN LUỒNG NHẬN THỨC 2 CHIỀU (2D COGNITIVE DISPATCHER)

> **Hiệu lực:** Quy tắc tối cao (SSOT Rule 0) áp dụng bắt buộc cho cả **Gemini**, **Claude**, toàn bộ **14 Domain Skills** và giao thức **Dual-Agent Bus v3.4**. Mọi tác vụ trước khi thực thi đều phải đi qua `Global_Dispatcher` (`intent_classifier.py` + `project_target_resolver.py`) để xác định đồng thời **2 chiều độc lập**:
>
> 1. **Chiều 1 — Chuyên môn Kỹ thuật (`domain_skill`):** 1 trong 14 kỹ năng chuyên ngành (Kết cấu, Địa chất, Thép, CAD, BPTC, Thẩm tra, Hệ thống...).
>
> 2. **Chiều 2 — Chế độ Tác vụ (`engagement_mode`):** `PRODUCT_COLLAB` | `SYSTEM_UPGRADE` | `SOLO_EXECUTION`.

## 0.1. Ma trận Phân luồng 2 Chiều & Phân vai Bất khả xâm phạm

### Chọn tác tử cho từng ca

Chọn tác tử độc lập với chuyên môn và chế độ công việc. Lựa chọn trong ca ưu tiên hơn mặc định dự án. Mặc định chung là AUTO.

| Lựa chọn | Phân việc |
| --- | --- |
| AUTO | Một tác tử cho việc độc lập. Áp dụng bảng phân vai dưới đây cho việc phối hợp. |
| CLAUDE_ONLY hoặc GEMINI_ONLY | Tác tử được chọn thực hiện toàn bộ chuỗi skill. Bỏ bước giao cho đối tác và ghi bus liên tác tử. |
| DUAL | Gemini và Claude phối hợp theo đầu ra và quan hệ phụ thuộc ghi trong phiếu. |

Chế độ một tác tử giữ nguyên yêu cầu xác nhận dự án, số liệu gốc, Điều 3 trước khi xuất và kiểm tra bản cuối. Khi thiếu công cụ, báo bước bị chặn. Chỉ đổi tác tử khi người dùng chọn lại. Phân biệt tự kiểm với kiểm tra độc lập. Người kiểm tra độc lập xác nhận đúng mã băm của tệp cuối. Mọi thay đổi của tệp cần kiểm lại. Ca cần kỹ sư ký phải chuyển người có thẩm quyền.

Lệnh giao việc ghi rõ tệp đích được phép sửa. Chỉ sửa script dự án khi được giao quyền. Quy tắc phân vai trong bảng sau áp dụng cho phần việc có hai tác tử.

| Chế độ (`engagement_mode`) | Tín hiệu kích hoạt | Phân vai AI | Thư mục trả hàng bắt buộc | Giao thức Bus & Ngôn ngữ báo cáo |
| ----- | ----- | ----- | ----- | ----- |
| **`PRODUCT_COLLAB`** *(Phối hợp Làm Sản phẩm Dự án)* | Nhắc tên/mã dự án (`01_Projects/`, `01_Structural_Projects/`) hoặc yêu cầu *tờ trình, thuyết minh, bản vẽ, xuất hồ sơ Word/PDF/DXF/Excel* (kể cả khi cần sửa script build cục bộ của dự án) | **Gemini = Maker** (dựng mô hình, trích xuất số liệu, bản vẽ CAD, script build thô). **Claude = Chủ trì Thẩm tra** (thẩm định TCVN & Nghị định 30, đối chiếu chéo CAD ↔ Thuyết minh, **sửa script build khi được giao quyền và chạy lệnh xuất file cuối**) | `01_Projects/<Tên_DA>/04_Deliverables_ToTrinh/` hoặc `01_Structural_Projects/<Tên_DA>/04_Deliverables_ToTrinh/` | **Tách 2 lớp:** Khóa nguyên tử, receipt, SHA-256 chạy ngầm trong `bus_meta`. Báo cáo người dùng **100% tiếng Việt kỹ thuật**, cấm biệt ngữ lập trình |
| **`SYSTEM_UPGRADE`** *(Nâng cấp Hệ thống / Công cụ)* | Nhắc `.agents/`, `SKILL.md`, `sync_bus.py`, `MCP`, `test_`, nâng cấp skill, bus IPC, validator, kiểm thử tự động | Cả **Gemini** và **Claude** đóng vai **Software Architect / DevOps** | `.agents/tools/`, `.agents/skills/`, `.agents/memory/audits/` | Áp dụng đầy đủ v3.3 (Report Gate P1, RECEIPTS, SHA-256, `run_all_tests.py`). Cho phép thuật ngữ lập trình |
| **`SOLO_EXECUTION`** *(Làm việc Độc lập 1 lượt)* | Hỏi đáp lý thuyết, tra cứu TCVN, tính nhanh 1 cấu kiện, hoặc điểm tin cậy phân loại nhỏ hơn `0.35` | AI nhận lệnh tự xử lý dứt điểm trong 1 lượt | Không bắt buộc (trừ khi người dùng chỉ định) | **Tắt Bus IPC** (không ghi `DUAL_AGENT_BUS.json`, triệt tiêu độ trễ và ping-pong token) |

## 0.2. Thứ tự Ưu tiên Phân loại (Xử lý Prompt Lai)

1. **Cờ cưỡng bức tường minh:** `/prod` → `PRODUCT_COLLAB`, `/sys` → `SYSTEM_UPGRADE`, `/solo` → `SOLO_EXECUTION`.

2. **Đường dẫn lõi hệ thống:** Yêu cầu thao tác trực tiếp lên `.agents/`, `.claude/`, `sync_bus.py`, `mcp_dce_cad_server.py`, `AGENTS.md` → vào `SYSTEM_UPGRADE`. Đường dẫn chỉ dùng để tham khảo giữ nguyên mục tiêu của yêu cầu.

3. **Prompt lai gắn với dự án:** Prompt yêu cầu sửa script build cục bộ để khắc phục lỗi trình bày/số liệu và xuất lại hồ sơ dự án → vẫn vào `PRODUCT_COLLAB` với cờ `allow_script_patch = True`.

4. **Khóa xác nhận dự án:** Ở chế độ `PRODUCT_COLLAB`, nếu `ProjectTargetResolver` khớp **0 dự án** hoặc **từ 2 dự án trở lên** (`AMBIGUOUS`), bắt buộc dừng ở trạng thái `NEEDS_PROJECT_CONFIRMATION` và hỏi xác nhận đúng 1 câu; **tuyệt đối không đoán bừa thư mục đích**.

5. **Chốt rơi an toàn:** Điểm tin cậy nhỏ hơn `0.35` → mặc định về `SOLO_EXECUTION`, không tự ý mở Bus IPC.

## 0.3. Cổng Nghiệm thu Hồ sơ & Quy tắc Báo cáo 3 Ý (`PRODUCT_COLLAB`)

Mọi ca làm việc ở chế độ `PRODUCT_COLLAB` chỉ được phép chuyển sang `COMPLETED` khi vượt qua đồng thời 2 cổng cứng trong `ProductDeliverableGate`:

1. **Cổng Hồ sơ Vật lý (`BLOCKED_MISSING_DELIVERABLE`):** Phải có ít nhất 1 tệp sản phẩm thật (`.docx`, `.pdf`, `.dxf`, `.xlsx`, dung lượng lớn hơn 0, thời gian cập nhật sau thời điểm giao việc) nằm trong đúng thư mục `04_Deliverables_ToTrinh/` của dự án. Mọi trường hợp chỉ xuất file nháp `.md` vào `.agents/memory/audits/` hoặc `.claude/memory/` đều bị từ chối đóng ca.

2. **Cổng Ngôn ngữ Kỹ thuật (`BLOCKED_JARGON_VIOLATION`):** Cấm tuyệt đối các thuật ngữ lập trình/hạ tầng (`SSOT`, `unpack`, `receipt`, `SHA-256`, `evidence_hashes`, `action_type`, `gate=PASS`, `force=False`, `mock`, `IPC`, `POSIX`, `bus_meta`, `pytest`, `refactor`) trong bản báo cáo gửi Tổng Công Trình Sư. Báo cáo bắt buộc ngắn gọn đúng **3 ý**:

   * **1. Đã sửa gì?** (Nêu rõ hạng mục kỹ thuật, tiêu chuẩn TCVN hoặc lỗi trình bày đã khắc phục.)

   * **2. File ở đâu?** (Ghi chính xác đường dẫn Windows tới tệp `.docx`/`.pdf`/`.dxf`/`.xlsx` trong `04_Deliverables_ToTrinh/`.)

   * **3. Số liệu đạt hay không?** (Kết luận dứt khoát Đạt / Chưa đạt theo TCVN và Nghị định 30/2020/NĐ-CP.)

## 0.4 Bảng Tra cứu Nhanh 14 Domain Skills (Manual Dispatcher Table)

Khi không cần chạy script phân loại, tra bảng này để xác định skill chính. **Không nạp 2 skill cùng lúc** trừ khi quy trình yêu cầu nối tiếp.

| Câu hỏi phân xử | Trả lời | Skill kích hoạt | Entry point |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ---------------------------------------- | ---------------------------------------------------------- |
| User đưa yêu cầu chung, chưa rõ skill hoặc cần chuỗi hành động? | Có | **`Global_Dispatcher`** | SKILL.md / intent_classifier.py |
| Đại diện Chủ đầu tư / QLTK — *review, thẩm tra, nghiệm thu, xử lý NCR, lập tờ trình, so sánh phương án, bóc khối lượng, đối chiếu tiêu chuẩn*? | Có | **`Design_Evaluation`** | SKILLKC.md / SKILL_REPORT.md |
| Đóng vai đơn vị thiết kế — *tự tính ra tiết diện / cốt thép / bu lông / đường hàn, xuất Thuyết minh tính toán*? | Có | **`Structural_Design_Engineer`** | SKILL_CALC.md / SKILL_CONNECTION.md / SKILL_CALC_REPORT.md |
| Tạo phụ lục tính toán chi tiết step-by-step đầy đủ cho đơn vị tư vấn thiết kế? | Có | **`SKILL_PHULUC`** | templates/TMTT_FULL.md / templates/PARTIAL_*.md |
| Yêu cầu **chỉ** là tạo hình ảnh / bản vẽ / biểu đồ? | Có | **`Technical_Illustrator`** | MODE 2D (default) / MODE 3D |
| So sánh chi phí, Value Engineering, tính Carbon, tối ưu ngân sách? | Có | **`Cost_Estimator`** | MODULE 1–5 |
| Điều tra sự cố / phân tích nguyên nhân hư hỏng, nứt nghiêm trọng, back-calculation? | Có | **`SKILL_FORENSIC`** | 7-step protocol |
| Kiểm chứng chéo kết quả, phát hiện mâu thuẫn tiêu chuẩn, cross-check với ETABS? | Có | **`SKILL_VERIFY`** | 5 loại kiểm chứng |
| Quản lý giao dịch kỹ thuật RFI, NCR, Submittal, Change Order với các bên? | Có | **`SKILL_RFI`** | Document Lifecycle |
| Phân tích ĐCCT, tính thông số Plaxis, tương quan SPT/CPT, ứng suất hữu hiệu, quy đổi DW/Strut? | Có | **`SKILL_GEOTECH`** | SKILL_SOIL_PARAMS.md |
| Thiết kế cốp pha sàn, cốp pha cột, cốp pha tường, cây chống, hệ giằng, kiểm tra ổn định thi công? | Có | **`SKILL_TEMPWORKS`** | Phase 1: calc_formwork_slab.py |
| Lập tiến độ Master Schedule MS Project (Gantt 8 cột + CPM + XML), phân cấp công trình (TT 34/2026), EVM/CPM, KPI ISO? | Có | **`Project_Manager`** | project_grading.py / msproject_bridge.py |
| Rà soát xung đột lưới trục, cao độ thông thủy 3D và đối chiếu nội bộ bản vẽ KT ↔ KC ↔ MEP? | Có | **`SKILL_BIM_COORDINATION`** | 4-Tier Spatial & Blueprint Clash Audit |
| Phối hợp, bàn giao ca hoặc thẩm tra đối kháng giữa Gemini và Claude qua `DUAL_AGENT_BUS.json`? | Có | **`SKILL_DUAL_AGENT_BRIDGE`** | sync_bus.py / claim_task.py / handover_task.py |

**Tie-breaker (phá vỡ thế hòa):**

1. Có keyword **"thuyết minh tính toán", "calculation sheet", "tính liên kết", "tính bu lông", "tính đường hàn", "tính bản mã", "chiều dài neo"** → `Structural_Design_Engineer` **thắng tuyệt đối**.
2. Có keyword **"review", "thẩm tra", "NCR", "tờ trình", "trình duyệt", "bóc tách khối lượng", "so sánh phương án", "hoàn công"** → `Design_Evaluation` **thắng tuyệt đối**.
3. Cả (1) và (2) cùng xuất hiện (VD: *"tính lại dầm rồi lập tờ trình"*) → chạy nối tiếp:
   `Structural_Design_Engineer` (tính) → **Review Gate** → `Design_Evaluation / SKILL_REPORT` (xuất tờ trình).
4. Có keyword **"thông số đất", "SPT", "CPT", "Plaxis input", "E50", "Hardening Soil", "tường vây EA EI", "ứng suất hữu hiệu", "phân tích địa chất", "ĐCCT", "hố đào sâu", "biện pháp thi công hầm"** → `SKILL_GEOTECH` **thắng tuyệt đối**.
5. Có keyword **"cốp pha", "coffa", "ván khuôn", "cây chống", "shoring", "bracing", "temporary works", "ván định hình", "tường chắn thi công"** → `SKILL_TEMPWORKS` **thắng tuyệt đối**.
6. Không khớp rõ → **HỎI User**, không tự đoán.

**`Technical_Illustrator` không bao giờ là skill chính** khi yêu cầu có nội dung tính toán — luôn được gọi bởi `Design_Evaluation` hoặc `Structural_Design_Engineer`.

---
