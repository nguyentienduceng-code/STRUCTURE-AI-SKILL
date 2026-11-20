# BÁO CÁO KỸ THUẬT & YÊU CẦU NÂNG CẤP HỆ THỐNG
## TÁI CẤU TRÚC BỘ NÃO PHÂN LUỒNG TRUNG TÂM (2-DIMENSIONAL COGNITIVE DISPATCHER) & QUY TRÌNH PHỐI HỢP DUAL-AGENT

> **Kính gửi:** Neon — Chuyên gia Kiến trúc Hệ thống Multi-Agent  
> **Người lập:** Gemini (Antigravity) theo chỉ đạo của Tổng Công Trình Sư (USER)  
> **Thời điểm lập:** 2026-11-20  
> **Tài liệu tham chiếu:** [AGENTS.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/AGENTS.md), [Global_Dispatcher/SKILL.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Global_Dispatcher/SKILL.md), [SPEC_P2_MCP_PERCEPTION_LOOP.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/docs/SPEC_P2_MCP_PERCEPTION_LOOP.md)

---

## 1. TỔNG QUAN VẤN ĐỀ VẬN HÀNH THỰC TẾ (PROBLEM STATEMENT)

Sau khi hoàn tất nâng cấp giao thức hạ tầng Dual-Agent Bridge lên v3.3 (khóa nguyên tử, Report Gate P1, MCP Perception Loop P2, 39/39 tests PASS), trong quá trình đưa vào phối hợp tác vụ hàng ngày giữa **Gemini** và **Claude**, người dùng (Product Owner) ghi nhận **điểm nghẽn nghiêm trọng**:

1. **Chưa tận dụng được "bộ não" tư duy sâu của Claude:**
   - Thay vì đóng vai trò *Chủ trì Thẩm tra / Red-Team / Rà soát Tiêu chuẩn TCVN & Văn phong Pháp lý*, Claude liên tục bị sa đà vào vai trò *DevOps / Software Engineer*, phản hồi toàn các thuật ngữ lập trình trừu tượng (`SSOT, unpack, receipt, action_type: META, gate=PASS, force=False, SHA-256 evidence_hashes...`) khiến người dùng kỹ thuật không thể nắm bắt nhanh.
2. **Không xuất file vào đúng thư mục hồ sơ dự án:**
   - Các kết quả của Claude chủ yếu sinh ra các file nháp markdown (`.md`) nằm phân tán trong thư mục hệ thống `.agents/memory/audits/` hoặc `.claude/memory/`, **hoàn toàn không xuất các file hồ sơ thực tế (`.docx`, `.pdf`, `.dxf`, `.xlsx`) vào đúng thư mục đích của dự án** (`01_Projects/<Tên_Dự_Án>/04_Deliverables_ToTrinh/`).

---

## 2. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE ANALYSIS - RCA)

Vấn đề **không nằm ở năng lực của AI**, mà nằm ở **Bộ não Điều phối Phân luồng Trung tâm (`Global_Dispatcher`)**:

### RCA 1: Bộ phân loại chỉ xử lý 1 Chiều (Thiếu Tầng Engagement Modality)
- Hiện tại, `intent_classifier.py` chỉ phân luồng theo 1 chiều: **Chuyên môn kỹ thuật (Domain Skill)** — Kết cấu, Địa kỹ thuật, Cốp pha, Dự án...
- Hoàn toàn thiếu chiều thứ hai: **Chế độ Tác vụ (Engagement Mode)**:
  - *Thực nghiệm 1:* Khi prompt yêu cầu *"Rà soát tờ trình và thuyết minh khảo sát địa chất Liên Chiểu Đà Nẵng xuất hồ sơ hoàn chỉnh"*, hệ thống bắt đúng `SKILL_GEOTECH` nhưng **không nhận biết đây là Tác vụ Sản phẩm Dự án**, không map tới folder `01_Projects/17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh`, và không gán vai trò Chủ trì Thẩm tra cho Claude.
  - *Thực nghiệm 2:* Khi prompt yêu cầu *"Nâng cấp hệ thống Dual Agent lên v3.3 thêm tính năng kiểm tra tự động"*, hệ thống trả về `Confidence: 0.0` (thất bại hoàn toàn) vì từ điển chỉ tìm cấu kiện xây dựng mà không có khái niệm nâng cấp công cụ!

### RCA 2: Cào bằng quy trình giao việc giữa Làm Sản Phẩm và Nâng Cấp Hệ Thống
- Khi chuyển việc qua kênh Bus IPC (`DUAL_AGENT_BUS.json`), dù là sửa hồ sơ cho Chủ đầu tư hay nâng cấp script Python nội bộ, hệ thống đều áp dụng chung một khuôn mẫu kỹ thuật hạ tầng, dẫn đến việc Claude tiếp cận mọi bài toán dưới góc nhìn viết mã và kiểm thử thay vì thẩm tra đồ án.

---

## 3. KIẾN TRÚC GIẢI PHÁP ĐỀ XUẤT (PROPOSED 2D DISPATCHER ARCHITECTURE)

Đề xuất Neon hỗ trợ tái cấu trúc `Global_Dispatcher` thành **Bộ Điều phối 2 Chiều**:

```
INPUT PROMPT ──► [2D DISPATCHER]
                     ├── Chiều 1: Domain Skill (14 Skills: Kết cấu, Địa chất, CAD, PMO...)
                     └── Chiều 2: Engagement Mode (3 Chế độ Tác vụ độc lập)
```

### 3 Chế độ Tác vụ Độc lập (Engagement Modes):

#### 🏢 Chế độ 1: `PRODUCT_COLLAB` (Phối hợp Làm Sản phẩm Dự án)
* **Điều kiện kích hoạt:** Prompt nhắc đến dự án cụ thể (`01_Projects/...`, `17_LIEN_CHIEU`, `SUNRISE`...) hoặc từ khóa sản phẩm (*tờ trình, thuyết minh, bản vẽ, xuất hồ sơ, tính dầm cột dự án*).
* **Quy tắc phân vai bất khả xâm phạm:**
  * **Gemini = Thợ Triển Khai (Maker):** Dựng mô hình, trích xuất dữ liệu, sinh bản vẽ CAD DXF, code script build DOCX/PDF thô.
  * **Claude = Chủ Trì Thẩm Tra (Lead Auditor / Senior Reviewer):** Thẩm định chuyên sâu theo TCVN, bắt lỗi chéo giữa CAD ↔ Thuyết minh, chuốt văn phong chuẩn Nghị định 30, **sửa trực tiếp vào script build và tự chạy lệnh để xuất file `.docx`/`.pdf`/`.dxf` hoàn chỉnh cuối cùng**.
* **Khóa cứng thư mục trả hàng:** BẮT BUỘC nằm tại `01_Projects/<Tên_Dự_Án>/04_Deliverables_ToTrinh/`. Mọi file nằm ngoài folder này đều coi là chưa đạt.
* **Ngôn ngữ giao tiếp:** 100% tiếng Việt kỹ thuật. Cấm biệt ngữ dev (*SSOT, unpack, mock, bus, receipt...*). Báo cáo ngắn gọn 3 ý: (1) Đã sửa gì? (2) File ở đâu? (3) Số liệu đạt hay không?

#### ⚙️ Chế độ 2: `SYSTEM_UPGRADE` (Nâng cấp Hệ thống / Công cụ)
* **Điều kiện kích hoạt:** Prompt nhắc đến *nâng cấp skill, sửa bus IPC, viết tool, tối ưu script, kiểm thử tự động, MCP server*.
* **Quy tắc phân vai:** Cả hai AI đóng vai Software Architects / DevOps. Dùng quy trình v3.3 (Report Gate, RECEIPTS, SHA-256, 39 tests).
* **Thư mục trả hàng:** `.agents/tools/`, `.agents/skills/`, `.agents/memory/audits/`.
* **Ngôn ngữ giao tiếp:** Chấp nhận và khuyến khích biệt ngữ kỹ thuật lập trình (architecture, tests, diff, POSIX paths).

#### ⚡ Chế độ 3: `SOLO_EXECUTION` (Làm việc Độc lập / Trực tiếp)
* **Điều kiện kích hoạt:** Prompt hỏi đáp lý thuyết, tra cứu tiêu chuẩn, tính toán nhanh 1 cấu kiện, hoặc làm việc trực tiếp với 1 AI mà người dùng không yêu cầu chuyển ca.
* **Quy tắc phân vai:** AI đang nhận prompt tự giải quyết từ A-Z trong 1 lượt (Single-turn). **KHÔNG kích hoạt Bus IPC** để triệt tiêu độ trễ và tránh ping-pong token.

---

## 4. DANH MỤC HẠNG MỤC CỤ THỂ CẦN NEON HỖ TRỢ (ACTION ITEMS)

1. **Nâng cấp `intent_classifier.py` & `keyword_database.json` (`Global_Dispatcher`):**
   - Bổ sung trường phân loại `engagement_mode`: `PRODUCT_COLLAB` | `SYSTEM_UPGRADE` | `SOLO_EXECUTION`.
   - Bổ sung module `ProjectTargetResolver`: Tự động nhận diện tên dự án và trích xuất đường dẫn tuyệt đối/POSIX tới `01_Projects/<Tên_DA>/04_Deliverables_ToTrinh/`.
   - Bổ sung bộ từ khóa cho nhánh `SYSTEM_UPGRADE` để khắc phục lỗi chấm điểm 0.0 hiện tại.
2. **Cập nhật Giao thức Handoff Bus (`sync_bus.py` / `handover_task.py`):**
   - Khi `action_type` là `PRODUCT_COLLAB`, hệ thống tự động:
     - Gán `deliverable_dir = "01_Projects/<Project>/04_Deliverables_ToTrinh"`.
     - Tự động sinh template chỉ thị cho Claude với tư cách là *Chủ trì Thẩm tra* (Lead Auditor), ép buộc output là `.docx`, `.pdf`, `.dxf`, `.xlsx`.
3. **Cập nhật Điều 0 trong `AGENTS.md` (SSOT Rules):**
   - Đưa ma trận phân luồng 2 chiều (Domain × Engagement Mode) vào Quy tắc tối cao để toàn bộ các skill và 2 tác tử đều tuân thủ vô điều kiện.
4. **Bổ sung Test Suite Kiểm thử Phân luồng:**
   - Viết bài kiểm thử `test_dispatcher_2d_modes.py` đảm bảo kiểm thử chính xác cả 3 chế độ tác vụ.
