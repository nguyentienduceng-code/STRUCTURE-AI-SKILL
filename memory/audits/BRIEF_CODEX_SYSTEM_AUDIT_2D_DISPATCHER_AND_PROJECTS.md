# HỒ SƠ TỔNG HỢP KIỂM ĐỊNH TOÀN DIỆN HỆ THỐNG & DỰ ÁN
## (COMPREHENSIVE AUDIT DOSSIER FOR CODEX)

**Mã hồ sơ:** `DOSSIER-CODEX-20261120-v3.4`  
**Ngày phát hành:** 2026-11-20  
**Kính gửi:** **Codex** (Chief Systems Auditor & Lead Technical Specialist)  
**Đơn vị trình:** **Gemini Antigravity** (Coordinator & Systems Architect)  
**Phê duyệt nội dung:** **Tổng Công Trình Sư**  
**Trạng thái:** SẴN SÀNG KIỂM ĐỊNH TOÀN DIỆN (READY FOR INDEPENDENT AUDIT)

---

## 1. MỤC ĐÍCH & PHẠM VI KIỂM ĐỊNH (EXECUTIVE AUDIT CHARTER)

Hồ sơ này tổng hợp toàn diện hiện trạng kỹ thuật, kiến trúc phân luồng, giao thức phối hợp giữa các Agent và dữ liệu sản phẩm dự án thực tế, nhằm đề nghị **Codex** tiến hành rà soát độc lập, đánh giá chuyên sâu và ban hành **Biên bản Kiểm định & Kiến nghị Kết luận**.

### Phạm vi rà soát gồm 4 trụ cột cốt lõi:
1. **Kiến trúc Nhận thức 2 Chiều (2D Cognitive Dispatcher v3.4):** Đánh giá tính khả thi, độ tin cậy của thuật toán phân luồng 2 chiều (Chuyên môn Kỹ thuật vs Chế độ Tác vụ) và cơ chế khóa cứng tại **Điều 0** (`AGENTS.md`).
2. **Quy trình Phối hợp Nhị nguyên (Gemini ↔ Claude Dual-Agent Synergy):** Đánh giá việc tái cấu trúc phân vai: **Gemini = Maker** vs **Claude = Chủ trì Thẩm tra / Lead Reviewer**, xử lý dứt điểm hiện tượng Claude bị "kẹt" trong vai DevOps (trả biệt ngữ lập trình và xuất nhầm thư mục).
3. **Hiện trạng Hợp đồng Kỹ thuật P2 (MCP Perception Loop & Visual Gate v3.3):** Đánh giá việc nghiệm thu P1/P2 giữa Claude và Gemini, giao tiếp qua MCP CAD Server (`mcp_dce_cad_server.py`) và cơ chế nghiệm thu dựa trên mã băm SHA-256 trên đĩa.
4. **Kiểm tra Mẫu Sản phẩm Dự án Thực tế (Benchmark Project: Cảng Liên Chiểu Đà Nẵng):** Đối chiếu các script sinh hồ sơ và tệp sản phẩm thực tế (`.docx`, `.pdf`, `.dxf`, `.xlsx`) tại `01_Projects/17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh/` với các tiêu chuẩn TCVN hiện hành và bộ quy chuẩn đồ họa Rules 12b–12e.

---

## 2. BỐI CẢNH NÂNG CẤP & HIỆN TRẠNG PHỐI HỢP GEMINI ↔ CLAUDE

### 2.1. Điểm nghẽn Cốt lõi Trước Nâng cấp
Trong quá trình vận hành trước đây, Tổng Công Trình Sư nhận thấy sự bất cập nghiêm trọng trong luồng công việc:
- **Claude có năng lực thẩm tra và tư duy cấu trúc rất cao**, nhưng khi nhận lệnh làm hồ sơ dự án, Claude lại bị "kẹt" trong vai trò DevOps/Kiểm thử hệ thống.
- **Biệt ngữ lập trình tràn ngập:** Báo cáo bàn giao của Claude liên tục chứa các thuật ngữ nội bộ (`RECEIPT`, `evidence_hashes`, `SHA-256`, `gate=PASS`, `action_type: META`, `sync_bus.py`).
- **Thất lạc tệp sản phẩm:** Thay vì xuất tệp `.docx`/`.pdf`/`.dxf` hoàn chỉnh vào thư mục hồ sơ của dự án (`04_Deliverables_ToTrinh/`), Claude lại lưu các phân tích vào thư mục nháp nội bộ (`.claude/memory/` hoặc `.agents/memory/audits/`).

### 2.2. Minh chứng Thực tế từ Phiên làm việc P2 của Claude (2026-11-20)
Tại ảnh chụp màn hình ghi nhận lúc 10:54 - 11:03 ngày 2026-11-20:
- Claude đã hoàn thành ca hợp đồng P2 (`SPEC_P2_MCP_PERCEPTION_LOOP.md`), tạo biên nhận `RCP_20261120_105415` với `action_type: META`, xác nhận 39/39 tests PASS, và chuyển bus sang trạng thái:
  ```json
  "handoff_status": "NEED_REVIEW",
  "current_holder": "IDLE",
  "target_agent": "GEMINI"
  ```
- Claude đặt điều kiện nghiệm thu cho lượt tiếp theo của Gemini: phải đăng ký MCP server, chạy sandbox `cad_v6`, xuất bằng chứng PNG + audit JSON lên đĩa, và viết `G2_RESULT.md`.
- **Nhận định:** Đây là minh chứng rõ rệt: Ở tác vụ hạ tầng (`SYSTEM_UPGRADE`), hành vi của Claude là chuẩn xác. Nhưng nếu Tổng Công Trình Sư yêu cầu làm một hồ sơ dự án (như thuyết minh hố khoan Liên Chiểu) mà Claude vẫn áp dụng nguyên xi luồng này thì sẽ gây tê liệt quy trình nghiệp vụ xây dựng.

---

## 3. KIẾN TRÚC ĐỘT PHÁ: 2D COGNITIVE DISPATCHER v3.4 (ĐIỀU 0 SSOT)

Để giải quyết tận gốc vấn đề trên, hệ thống đã ban hành **Điều 0** (SSOT Rule 0) trong `AGENTS.md` và triển khai bộ công cụ điều phối nhận thức 2 chiều:

### 3.1. Ma trận Phân luồng Nhận thức 2 Chiều
Mọi prompt của người dùng trước khi thực thi đều đi qua `Global_Dispatcher` (`intent_classifier.py` v3.4 + `project_target_resolver.py`):

```
                       PROMPT CỦA USER
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [CHIỀU 1: CHUYÊN MÔN]         [CHIỀU 2: CHẾ ĐỘ TÁC VỤ]
       1 trong 14 Domain Skills      ├─► PRODUCT_COLLAB (Làm Dự án)
       (Kết cấu, ĐCCT, CAD, PMO,     ├─► SYSTEM_UPGRADE (Làm Hệ thống)
        Thẩm tra, Định giá...)        └─► SOLO_EXECUTION (Tính nhanh 1 lượt)
```

| Chế độ (`engagement_mode`) | Phân vai AI | Thư mục trả hàng bắt buộc | Ngôn ngữ & Cổng kiểm duyệt |
| :--- | :--- | :--- | :--- |
| **`PRODUCT_COLLAB`** | **Gemini = Maker** (dựng mô hình, trích xuất dữ liệu, bản vẽ CAD thô, script build thô).<br>**Claude = Chủ trì Thẩm tra** (thẩm định TCVN & NĐ 30, kiểm toán chéo CAD ↔ Thuyết minh, **sửa trực tiếp script build và tự chạy lệnh xuất file cuối**). | `01_Projects/<Tên_DA>/04_Deliverables_ToTrinh/`<br>(Được phân giải tự động bởi `ProjectTargetResolver`) | **100% Tiếng Việt Kỹ thuật.**<br>Cấm tuyệt đối từ ngữ lập trình (`JargonLinter`).<br>Báo cáo đúng **3 ý** (Đã sửa gì? File ở đâu? Số liệu đạt hay không?).<br>Bắt buộc có file thật > 0 bytes (`ProductDeliverableGate`). |
| **`SYSTEM_UPGRADE`** | Cả **Gemini** và **Claude** đóng vai **Software Architect / DevOps**. | `.agents/tools/`, `.agents/skills/`, `.agents/memory/audits/` | Ngôn ngữ phần mềm chuẩn v3.3 (Bus IPC, RECEIPTS, SHA-256, Report Gate P1, `run_all_tests.py`). |
| **`SOLO_EXECUTION`** | AI nhận lệnh tự giải quyết dứt điểm trong 1 lượt (hỏi lý thuyết, tra TCVN, tính nhanh 1 cấu kiện). | Không bắt buộc. | **Tắt hoàn toàn Bus IPC** (không ghi `DUAL_AGENT_BUS.json`, triệt tiêu độ trễ và ping-pong token). |

### 3.2. Bộ Công cụ Lõi Đã Cài đặt và Kiểm thử:
1. `intent_classifier.py` (v3.4 `IntentClassifier2D`): Phân loại độc lập đồng thời `domain_skill` và `engagement_mode`. Hỗ trợ các cờ cưỡng bức `/prod`, `/sys`, `/solo`.
2. `project_target_resolver.py`: Quét đa rễ (`01_Projects/`, `01_Structural_Projects/`), sử dụng thuật toán chuẩn hóa tiếng Việt loại bỏ dấu (`normalize_vn`) và tính điểm tương đồng Jaccard.
3. `product_deliverable_gate.py`:
   - `ProductDeliverableGate`: Enforce sự tồn tại của tệp vật lý `.docx`, `.pdf`, `.dxf`, `.xlsx` với timestamp mới hơn thời điểm giao việc.
   - `JargonLinter`: Rà soát tự động danh sách cấm gồm 15 biệt ngữ lập trình (`SSOT`, `unpack`, `receipt`, `evidence_hashes`, `pytest`, `mock`...) trong báo cáo giao tiếp với Tổng Công Trình Sư.

---

## 4. DỮ LIỆU DỰ ÁN THỰC TẾ: BENCHMARK CẢNG LIÊN CHIỂU ĐÀ NẴNG

Thư mục dự án: `G:\My Drive\Google AI Studio\01_Projects\17_LIEN_CHIEU_DA_NANG\04_Deliverables_ToTrinh\`

### 4.1. Hồ sơ Kỹ thuật & Bối cảnh
- **Dự án:** Đầu tư Xây dựng Bến Cảng Liên Chiểu — Phần Cơ sở Hạ tầng Dùng chung (Đà Nẵng).
- **Hạng mục rà soát:** Đánh giá mạng lưới Khảo sát Địa chất Công trình (ĐCCT) và lập Tờ trình Thẩm tra / Thuyết minh Nhiệm vụ Khảo sát.
- **Tiêu chuẩn áp dụng:** TCVN 9363:2012, TCVN 4419:1987, TT 34/2026/TT-BXD, Nghị định 175/2024/NĐ-CP.

### 4.2. Danh mục Script Build & Tệp Sản phẩm Hiện hữu
Hệ thống đã triển khai sẵn các script build tự động để xuất bản hồ sơ:
1. `build_thuyetminh_lienchieu_6hk.py`: Xây dựng thuyết minh chi tiết nhiệm vụ khảo sát địa chất theo TCVN 9363:2012.
2. `build_perfect_totrinh_lienchieu.py`: Tạo Tờ trình thẩm tra cấp Trưởng phòng QLTK gửi Tổng Giám đốc / Ban QLDA.
3. `generate_cad_plan_4_boreholes_option_b.py`: Xuất bản vẽ CAD mặt bằng bố trí hố khoan (Option B - 4 hố khoan tối ưu) theo chuẩn DCE Pro.
4. **Các tệp sản phẩm vật lý đã xuất bản thành công:**
   - `BXD_PQLTK_LienChieu_ToTrinh_KhaoSatDiaChat_18.11.2026.docx` (3.84 MB) & `.pdf` (854 KB).
   - `ThuyetMinh_NhiemVu_KhaoSatDiaChat_8HK_LienChieu_DaNang.docx` (2.50 MB) & `.pdf` (615 KB).
   - `BangToaDo_VN2000_8_HoKhoan_DCCT_LienChieu_DaNang.xlsx` (13.2 KB).
   - `SoDo_MangLuoi_8_HoKhoan_PA_A_TKBVTC.dxf` (2.03 MB) & `.png` (1.35 MB).

---

## 5. BÁO CÁO HẠ TẦNG KỸ THUẬT & TRẠNG THÁI KIỂM THỬ (TEST BASELINE)

Hệ thống đã trải qua đợt kiểm thử hồi quy khắt khe trên môi trường Windows thực tế:

| Bộ Kiểm thử (Test Suite) | Số lượng Test Case | Trạng thái | Ghi chú & Khắc phục Kỹ thuật |
| :--- | :---: | :---: | :--- |
| `test_dispatcher_2d_modes.py` | 12 / 12 | **PASS (100%)** | Xác nhận phân loại chính xác 3 mode, cờ override, và bẫy dự án. |
| `run_all_tests.py --fast` | 24 / 24 Suites | **PASS (100%)** | Thời gian chạy 127.29s, toàn bộ suite lõi xanh sạch. |
| `test_dce_deep_integration.py` | 16 / 16 | **PASS (100%)** | Đã xử lý mở rộng hỗ trợ khổ A1 thực tế AutoCAD DCE Pro (`84100 mm`). |
| `integration_test.py` | 64 / 64 | **PASS (100%)** | Xác nhận đồng bộ byte-for-byte nội dung `AGENTS.md` (SSOT Rule 0). |
| `sync_bus.py --scan-conflicts` | Quét toàn bộ Bus | **0 Conflicts** | Dữ liệu bus sạch, không có xung đột khóa ghi. |

---

## 6. CÁC NỘI DUNG YÊU CẦU CODEX RÀ SOÁT, ĐÁNH GIÁ & KIẾN NGHỊ

Gemini Antigravity đề nghị **Codex** tập trung rà soát và đưa ra nhận định độc lập về 5 nhóm chuyên đề sau:

### Chuyên đề 1: Đánh giá Kiến trúc Phân luồng Nhận thức 2 Chiều (Rule 0)
- Thuật toán tại `intent_classifier.py` và `project_target_resolver.py` có lỗ hổng hoặc góc khuất (edge cases) nào có thể dẫn đến việc phân loại nhầm giữa `PRODUCT_COLLAB` và `SYSTEM_UPGRADE` không?
- Ngưỡng tin cậy `confidence_score = 0.35` để rẽ nhánh về `SOLO_EXECUTION` đã tối ưu chưa? Có nguy cơ làm rơi rụng các yêu cầu phức tạp của người dùng không?

### Chuyên đề 2: Đánh giá Tính Thực thi của Phân vai Gemini (Maker) ↔ Claude (Lead Reviewer)
- Việc quy định bắt buộc **Claude phải tự tay sửa script build và tự chạy lệnh sinh file cuối cùng** (`allow_script_patch = True`) có điểm nghẽn kỹ thuật nào khi phối hợp qua Google Drive không?
- Bộ lọc `ProductDeliverableGate` (kiểm tra file tồn tại trên đĩa > 0 bytes và quét `JargonLinter`) đã đủ chặt chẽ để triệt tiêu hoàn toàn tình trạng Claude trả file nháp vào `.claude/memory/` chưa?

### Chuyên đề 3: Đánh giá Hợp đồng Hạ tầng CAD P2 (MCP Perception Loop)
- Đánh giá thỏa thuận kỹ thuật tại `SPEC_P2_MCP_PERCEPTION_LOOP.md` và mã nguồn của `mcp_dce_cad_server.py` (13 tools).
- Quy trình nghiệm thu bằng mã băm SHA-256 trên đĩa của Claude có gây xung đột hay cản trở tiến độ khi áp dụng vào việc vẽ bản vẽ kỹ thuật thật cho các dự án xây dựng không?

### Chuyên đề 4: Đánh giá Chất lượng Hồ sơ Dự án Thực tế (Cảng Liên Chiểu)
- Rà soát các script build tại `01_Projects/17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh/`:
  * Script Word: Đã tuân thủ nghiêm ngặt **Rule 12b** (Zero White Text Lock - cấm tuyệt đối chữ trắng trên nền tối, áp dụng bảng màu gốc khoáng) chưa?
  * Script CAD: Bản vẽ DXF hố khoan có đáp ứng **Rule 12d** (Quy chuẩn đồ họa CAD DCE Pro: phân đoạn dầm, không đè chữ, 4 tầng kích thước biên ngoài) không?
  * Tính tương thích pháp lý: Đã chuẩn hóa thể thức theo Nghị định 30/2020/NĐ-CP và phân cấp công trình theo Thông tư 34/2026/TT-BXD chưa?

### Chuyên đề 5: Khuyến nghị Tối ưu Hóa Toàn Diện & Lộ trình Tiếp theo
- Codex kiến nghị những tinh chỉnh hoặc bổ sung cụ thể nào về mặt kiến trúc, công cụ hoặc quy trình vận hành?
- Thứ tự ưu tiên triển khai trong 48 giờ tới giữa: (1) Hoàn tất dogfooding ca P2 CAD MCP, (2) Xuất bản hoàn chỉnh bộ hồ sơ dự án Cảng Liên Chiểu, (3) Tối ưu hóa thêm bộ từ khóa của Dispatcher.

---

## 7. TIÊU CHÍ ĐẦU RA MONG ĐỢI TỪ CODEX

Đề nghị Codex cung cấp tài liệu kết luận chính thức:
1. **Tệp Báo cáo Độc lập:** Lưu tại `.agents/memory/audits/CODEX_AUDIT_REPORT_2D_DISPATCHER_AND_SYSTEM.md`.
2. **Cấu trúc Báo cáo yêu cầu:**
   - **Phần I:** Đánh giá Tổng quan Hệ thống (System Architecture Audit).
   - **Phần II:** Bảng Ma trận Kiểm toán Rủi ro & Góc khuất (Risk & GAP Matrix).
   - **Phần III:** Đánh giá Chi tiết Dự án Cảng Liên Chiểu Đà Nẵng.
   - **Phần IV:** Đánh giá Hợp đồng P2 MCP CAD Perception Loop.
   - **Phần V:** Kiến nghị Cụ thể & Kết luận Nghiệm thu (Final Recommendations & Disposition: PASS / CONDITIONAL PASS / FAIL).

---
*(Hồ sơ đã được ký điện tử và lưu trữ tại hệ thống quản lý tri thức Antigravity)*  
**Người lập hồ sơ:** Gemini Antigravity — Hệ thống Trợ lý Điều phối AI Chuyên ngành Xây dựng.
