# ĐIỀU 0: MA TRẬN PHÂN LUỒNG NHẬN THỨC 2 CHIỀU (2D COGNITIVE DISPATCHER)

> **Hiệu lực:** Quy tắc tối cao (SSOT Rule 0) áp dụng bắt buộc cho cả **Gemini**, **Claude**, toàn bộ **14 Domain Skills** và giao thức **Dual-Agent Bus v3.4**. Mọi tác vụ trước khi thực thi đều phải đi qua `Global_Dispatcher` (`intent_classifier.py` + `project_target_resolver.py`) để xác định đồng thời **2 chiều độc lập**:
>
> 1. **Chiều 1 — Chuyên môn Kỹ thuật (`domain_skill`):** 1 trong 14 kỹ năng chuyên ngành (Kết cấu, Địa chất, Thép, CAD, BPTC, Thẩm tra, Hệ thống...).
>
> 2. **Chiều 2 — Chế độ Tác vụ (`engagement_mode`):** `PRODUCT_COLLAB` | `SYSTEM_UPGRADE` | `SOLO_EXECUTION`.

## 0.1. Ma trận Phân luồng 2 Chiều & Phân vai Bất khả xâm phạm

| Chế độ (`engagement_mode`) | Tín hiệu kích hoạt | Phân vai AI | Thư mục trả hàng bắt buộc | Giao thức Bus & Ngôn ngữ báo cáo | 
| ----- | ----- | ----- | ----- | ----- | 
| **`PRODUCT_COLLAB`** *(Phối hợp Làm Sản phẩm Dự án)* | Nhắc tên/mã dự án (`01_Projects/`, `01_Structural_Projects/`) hoặc yêu cầu *tờ trình, thuyết minh, bản vẽ, xuất hồ sơ Word/PDF/DXF/Excel* (kể cả khi cần sửa script build cục bộ của dự án) | **Gemini = Maker** (dựng mô hình, trích xuất số liệu, bản vẽ CAD, script build thô). **Claude = Chủ trì Thẩm tra** (thẩm định TCVN & Nghị định 30, đối chiếu chéo CAD ↔ Thuyết minh, **sửa trực tiếp script build và tự chạy lệnh xuất file cuối**) | `01_Projects/<Tên_DA>/04_Deliverables_ToTrinh/` hoặc `01_Structural_Projects/<Tên_DA>/04_Deliverables_ToTrinh/` | **Tách 2 lớp:** Khóa nguyên tử, receipt, SHA-256 chạy ngầm trong `bus_meta`. Báo cáo người dùng **100% tiếng Việt kỹ thuật**, cấm biệt ngữ lập trình | 
| **`SYSTEM_UPGRADE`** *(Nâng cấp Hệ thống / Công cụ)* | Nhắc `.agents/`, `SKILL.md`, `sync_bus.py`, `MCP`, `test_`, nâng cấp skill, bus IPC, validator, kiểm thử tự động | Cả **Gemini** và **Claude** đóng vai **Software Architect / DevOps** | `.agents/tools/`, `.agents/skills/`, `.agents/memory/audits/` | Áp dụng đầy đủ v3.3 (Report Gate P1, RECEIPTS, SHA-256, `run_all_tests.py`). Cho phép thuật ngữ lập trình | 
| **`SOLO_EXECUTION`** *(Làm việc Độc lập 1 lượt)* | Hỏi đáp lý thuyết, tra cứu TCVN, tính nhanh 1 cấu kiện, hoặc điểm tin cậy phân loại nhỏ hơn `0.35` | AI nhận lệnh tự xử lý dứt điểm trong 1 lượt | Không bắt buộc (trừ khi người dùng chỉ định) | **Tắt Bus IPC** (không ghi `DUAL_AGENT_BUS.json`, triệt tiêu độ trễ và ping-pong token) | 

## 0.2. Thứ tự Ưu tiên Phân loại (Xử lý Prompt Lai)

1. **Cờ cưỡng bức tường minh:** `/prod` → `PRODUCT_COLLAB`, `/sys` → `SYSTEM_UPGRADE`, `/solo` → `SOLO_EXECUTION`.

2. **Đường dẫn lõi hệ thống:** Prompt nhắc trực tiếp `.agents/`, `.claude/`, `sync_bus.py`, `mcp_dce_cad_server.py`, `AGENTS.md` → luôn vào `SYSTEM_UPGRADE`.

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