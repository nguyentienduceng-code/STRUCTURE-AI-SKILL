# AGENTS.md — Quy tắc Liên Skill Toàn bộ Bộ Kỹ năng Kết cấu

> **Phạm vi:** Áp dụng cho **MỌI skill** trong `.agents/skills/`.
> **Vị trí chuẩn:** `.agents/AGENTS.md` (đồng bộ tại `.agents/skills/AGENTS.md`).
> **Tham khảo nhanh:** Xem `skills/SKILL_INDEX.md` để biết mapping tình huống → skill → script.
> **P0 Infrastructure:** Xem `skills/SKILL_BRIDGE.md` (data contracts) và `skills/INTER_SKILL_TRIGGERS.md` (auto-invocation).
> **P1 Tools:** Xem `confidence_score.py`, `validate_handoff_schema.py`, `handoff_manager.py` trong `_SHARED/SHARED_CONTEXT/`.
> **Cập nhật:** 2026-11-20 — v7.5 (2D Cognitive Dispatcher v3.4 + Rules 0.1–0.3 + 14 Production Skills + Rules 12b–12e)

---

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

## 1. Đường dẫn Tuyệt đối (Absolute Paths)

- **LUÔN** sử dụng đường dẫn tuyệt đối cho mọi file input/output.
- Đúng: `g:\My Drive\Google AI Studio\01_Projects\DuAnX\output.docx`
- Sai: `./output.docx`, `output.docx`, `../DuAnX/output.docx`

---

## 2. Encoding UTF-8 trên Windows

- Mọi script Python phải có ở đầu file:

  ```python
  import sys
  if sys.stdout.encoding != 'utf-8':
      sys.stdout.reconfigure(encoding='utf-8')
  ```

- Khi chạy Node.js, đảm bảo file JSON input/output là UTF-8 BOM-free.

---

## 3. Review Gate (Cổng Kiểm duyệt) & Định nghĩa Xác nhận

- **BẮT BUỘC** trước khi xuất bất kỳ file `.docx` / `.pdf` / `.json` / `.md` chính thức nào:
  1. In tóm tắt ra chat: bảng chỉ số sử dụng η, các số liệu chốt, danh sách `UNVERIFIED`.
  2. Hỏi User: *"Anh/chị có đồng ý với kết quả này để xuất file không?"*
  3. Chỉ ghi file sau khi User xác nhận rõ ràng.
- **Định nghĩa "xác nhận rõ ràng":**
  - ĐỒNG Ý: "Đồng ý", "OK", "Xuất file", "Approved", "Được", "Duyệt".
  - KHÔNG ĐƯỢC COI LÀ XÁC NHẬN: User im lặng, "để tôi xem lại", "ok nhưng...", hỏi thêm thông tin mà không chốt. Nếu không rõ → HỎI LẠI, không tự suy diễn.
- Ngoại lệ: File scratch/test/debug không cần Review Gate.

---

## 4. No Hallucination — Không Bịa Số Liệu

- Thiếu dữ kiện → ghi rõ `Data Missing: [Tên Thông Số]`.
- **KHÔNG BAO GIỜ** tự đoán giá trị kỹ thuật (cường độ bê tông, tải trọng, kích thước cốt thép, v.v.).
- Khi tra tiêu chuẩn: trích dẫn chính xác số điều khoản, số bảng, năm ban hành.

---

## 5. Deterministic Math — Cấm Nhẩm Tay

- Nghiêm cấm AI tự nhẩm phép toán kỹ thuật. Phải gọi script trong `calculators/` (Design_Evaluation) hoặc `scripts/calc_*.py` (Structural_Design_Engineer) và đọc kết quả JSON từ stdout.
- Mọi script tính toán PHẢI trả về trường `Calculation_Logs` (mảng object) và `Standard_Method` (phiên bản tiêu chuẩn thực sự cài đặt). Nếu script không có `Calculation_Logs` → kết quả **KHÔNG** được đưa vào báo cáo.

---

## 6. Chỉ số Sử dụng (Utilization Ratio η)

Mọi kiểm tra định lượng phải quy về `η = Tác động / Khả năng`:

| η           | Mã màu | Kết luận                 | Hành động                                         |
| ------------ | -------- | -------------------------- | ---------------------------------------------------- |
| ≤ 0.70      | 🟢       | An toàn, có dư          | Đạt — xem xét Value Engineering (Cost_Estimator) |
| 0.70 – 0.90 | 🟡       | Đạt, hợp lý            | Đạt — thiết kế tối ưu                         |
| 0.90 – 1.00 | 🟠       | Đạt nhưng sát ngưỡng | Đạt — cảnh báo lưu ý                          |
| > 1.00       | 🔴       | KHÔNG ĐẠT               | Yêu cầu điều chỉnh tiết diện / giải pháp    |

Cấm dùng tỷ số của các hệ số trung gian và gọi đó là η.

> **Code-enforced:** Toàn bộ ngưỡng η và hành động kích hoạt được thực thi tự động qua Policy Engine tại `tools/policy_engine.py` (`decide_eta`). Xem chi tiết mã nguồn và test suite tại `tests/test_policy_engine.py`.

---

## 7. Nguồn Tiêu chuẩn — Version Lock

- Mọi trích dẫn tiêu chuẩn PHẢI lấy phiên bản từ **`STANDARDS_LOCK.md`** — nguồn sự thật duy nhất.
- LUÔN ghi kèm năm ban hành ngay sau mã số (VD: `TCVN 2737:2023`, `TCVN 5575:2024`, `TCVN 5574:2018`, `TCVN 9386:2025`).
- Citation Object hiển thị đủ 4 phần: `[Mã]:[Năm] — Điều/Bảng [số] — Trang [số] — [Trích yếu]`. Cấm rút gọn.
- Nếu script khai báo `Standard_Method` khác phiên bản chốt → PHẢI in cảnh báo rõ trong báo cáo, không tự đổi nhãn.
- **Cấm dùng đồng thời 2 phiên bản của cùng 1 tiêu chuẩn trong 1 phân tích.**

---

## 8. Trách nhiệm, Approval Matrix & Disclaimer Bắt buộc

- Mọi báo cáo/thuyết minh xuất ra PHẢI có bảng Trách nhiệm cuối văn bản, cột "Đề xuất" luôn ghi rõ: *"Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký"*.
- Mọi file thuyết minh tính toán / tờ trình xuất ra phải chèn dòng cuối:
  > *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
  >

---

## 9. Phân biệt Bản vẽ Kỹ thuật vs Ảnh Minh họa

- `Technical_Illustrator` **MODE 2D** (Python/matplotlib) = bản vẽ kỹ thuật, dùng được cho hồ sơ pháp lý/thiết kế.
- `Technical_Illustrator` **MODE 3D** (AI render) = minh họa khái niệm. Bắt buộc kèm caption cảnh báo: *"Hình minh họa khái niệm — không phải bản vẽ kỹ thuật chính xác, không dùng để thi công."*

---

## 10. Xác nhận File Output

- Sau khi tạo file (ảnh, .docx, .json):
  - Dùng `list_dir` hoặc `view_file` để xác nhận file thực sự tồn tại trước khi báo cáo hoàn thành.
  - Nếu nhúng ảnh vào artifact → copy file vào thư mục artifacts trước.

---

## 11. Xử lý Mâu thuẫn Giữa Các Module

Trước khi đưa nội dung qua Review Gate, nếu phát hiện số liệu hiển thị trong báo cáo/tờ trình KHÁC với số liệu gốc trong JSON handoff từ module tính toán → PHẢI dừng lại, báo rõ sự khác biệt cho User, KHÔNG tự động chọn 1 trong 2 số liệu.

---

## 12. Văn phong Kỹ thuật Chuẩn hóa (Plain Engineering Language)

Mọi output chính thức (báo cáo, tờ trình, thuyết minh) PHẢI tuân thủ:

- Câu ngắn (≤ 25 từ), chủ ngữ là đối tượng kỹ thuật (dầm, cột, tải), không phải khái niệm trừu tượng.
- Ưu tiên động từ hành động: "chịu", "vượt", "đạt", "cần tăng". Hạn chế bị động.
- Mỗi kết luận PHẢI kèm ít nhất 1 con số định lượng (η, f/L, σ, kN, mm).
- Thuật ngữ tiếng Anh lần đầu xuất hiện → giải nghĩa tiếng Việt trong ngoặc.
- Cấm các cụm từ rỗng: "nhìn chung", "xét về mặt", "trên cơ sở", "trong khuôn khổ", "một cách toàn diện", "qua quá trình phân tích và đánh giá".

---

## 12b. ZERO WHITE TEXT LOCK & Hệ Màu Gốc Khoáng (Bắt buộc cho Word .docx, Excel .xlsx, Ảnh Kỹ thuật)

> **Cơ sở pháp lý & In ấn**: Chuẩn in ấn đen trắng và photocopy hồ sơ kỹ thuật xây dựng Việt Nam. Nguồn sự thật duy nhất: `_SHARED/SHARED_CONTEXT/design_tokens.py`.

- **CẤM TUYỆT ĐỐI**: Dùng chữ màu trắng (`#FFFFFF` hoặc `RGBColor(255, 255, 255)`) trên nền tối trong bất kỳ bảng biểu nào của file Word (`.docx`), bảng tính Excel (`.xlsx`), nhãn ghi chú hay bản vẽ kỹ thuật (`matplotlib`/ảnh render).
- **Hệ quả khi vi phạm**: Khi in ấn mặc định trong Word (mặc định Word bỏ qua màu nền bảng/trang) hoặc photocopy đen trắng, chữ màu trắng trên nền tối sẽ biến thành **chữ trắng trên nền giấy trắng**, làm mất toàn bộ dữ liệu bảng biểu và thông số kỹ thuật.
- **Quy cách bảng biểu bắt buộc**:
  - **Header Bảng & Thanh Tiêu đề**: Nền sáng gốc khoáng **Xanh Đá Phiến Sương Nhạt (`#DCE4EC`)** hoặc **Đá Vôi Sáng (`#EAE6DF`)**, chữ in đậm màu tối **Xanh Thép Trầm (`#1E3246`)** hoặc **Mực Than Chì (`#1C1E21`)**.
  - **Dòng dữ liệu (Data rows)**: Chữ tối (`#1C1E21`), nền xen kẽ Trắng (`#FFFFFF`) và **Ngà Giấy Tự Nhiên (`#F8F7F4`)**, đường kẻ lưới mảnh `#D0CEC7`.
  - **Hình vẽ 2D / Biểu đồ**: Mọi nhãn text trong bounding box, callout hoặc pill tag phải dùng chữ tối màu (`#0F172A`, `#1E3246`, `#7F1D1D`) trên nền sáng (`#FEF08A`, `#FEE2E2`, `#F1F5F9`, `#FFFFFF`).

---

## 12c. Quy định Thực tế về Cấp độ Bền Bê tông tại Việt Nam (Concrete Grade Realism Lock)

> **Cơ sở thực tiễn**: Năng lực trạm trộn bê tông thương phẩm (Ready-mix concrete), kiểm soát nứt do nhiệt thủy hóa và thực tế thi công của các tổng thầu Top 1 tại Việt Nam (Coteccons, Ricons, Newtecons, Delta, Hòa Bình) theo TCVN 5574:2018.

- **Dầm & Sàn dân dụng cao tầng**:
  - Phổ biến & tối ưu nhất: **B25 (M350, $R_b = 14.5\text{ MPa}$)** đến **B30 (M400, $R_b = 17.0\text{ MPa}$)**.
  - Sàn ứng suất trước (PT slab): B30 đến tối đa B35.
  - **CẤM**: Không dùng quá B35 cho dầm sàn vì nguy cơ co ngót và nứt nhiệt diện rộng rất cao.
- **Cột & Vách Nhà cao tầng (kể cả 30 - 45 tầng)**:
  - **Tầng hầm, móng & Khối đế / Tầng thấp (T1 - T10)**: Bê tông **B35 (M450, $R_b = 19.5\text{ MPa}$)** hoặc tối đa **B40 (M500, $R_b = 22.0\text{ MPa}$)**.
  - **Tầng thân / Tầng điển hình (T11 - T25)**: Bê tông **B30 (M400, $R_b = 17.0\text{ MPa}$)** hoặc **B35 (M450, $R_b = 19.5\text{ MPa}$)**.
  - **Tầng trên cao (T26 - T40)**: Bê tông **B25 (M350)** hoặc **B30 (M400)**.
- **TUYỆT ĐỐI CẤM**:
  - Tự tiện gán cấp độ bền bê tông B45, B50, B60 cho nhà cao tầng dân dụng thông thường khi chưa có yêu cầu đặc thù bằng văn bản của Chủ đầu tư / TVTK. Tại Việt Nam, bê tông > B40 đòi hỏi phụ gia đặc chủng, đá cường độ cao, kiểm soát bảo dưỡng ngặt nghèo và làm giá thành tăng vọt, rất khó đồng đều chất lượng tại hiện trường.
  - Khi lực dọc nén uốn lớn: **Bắt buộc ưu tiên** giải pháp tăng kích thước tiết diện cột/vách, tăng hàm lượng thép dọc $\mu = 2.0\% - 3.0\%$ (thép CB500-V), áp dụng cột vách dẹt (wall-columns giấu trong tường ngăn) hoặc cột bọc thép hình (SRC/CFT) thay vì đẩy mác bê tông lên B50/B60!

---

## 12d. Quy chuẩn Đồ họa Bản vẽ Kỹ thuật CAD DCE Pro (CAD Drafting & Visual Quality Standards)

> **Cơ sở kỹ thuật**: Chuẩn bản vẽ thi công xây dựng Việt Nam và quốc tế, kế thừa hệ thống Drawing Template DCE Pro (`DCE_Master_Seed_Template.dxf` / `Dam_200x400_DCE.dxf` AC1021). Nguồn thực thi: `cad_plan_engine.py` và Bộ lọc 8 `dce_cad_compliance_checker.py`.

Mọi bản vẽ mặt bằng kết cấu (Mặt bằng định vị cột vách, Mặt bằng kết cấu dầm sàn) xuất ra tệp CAD (`.dxf` / `.dwg`) BẮT BUỘC tuân thủ 5 điều cấm và quy cách đồ họa sau:

1. **Khóa phân đoạn dầm (No Continuous Beam Line Lock)**:
   - Nghiêm cấm vẽ dầm chạy thẳng một mạch xuyên suốt toàn sàn qua các cột và lõi cứng. Dầm bắt buộc phân đoạn theo từng nhịp giữa 2 gối tựa (nút cột - vách).
   - Trên **Mặt bằng Định vị Cột Vách**: Tuyệt đối **KHÔNG ghi nhãn dầm** (`DCE_Name`). Dầm chỉ được hiển thị làm nét mờ tham chiếu trên layer `DCE_NetThay` (linetype `HIDDEN_DBIM`) để tránh loạn thị giác. Nhãn dầm thuộc riêng bản vẽ Mặt bằng Kết cấu Dầm Sàn.
2. **Khóa chống đè chữ & căn tâm cấu kiện (Anti-Collision & Centering Lock)**:
   - Block `TenCauKien` (Tên cột và tiết diện) phải được căn đúng tâm cấu kiện trong hệ tọa độ bản vẽ (World Coordinates), triệt tiêu hoàn toàn độ lệch $700\text{ mm}$ do basepoint block.
   - Nhãn ghi chú lõi cứng, buồng thang máy phải đặt trong không gian thông thoáng, không bao giờ đè ngang qua buồng thang hay lỗ kỹ thuật.
3. **Khóa 4 tầng biên ngoài chuẩn xây dựng (4-Tier Exterior Dimension Hierarchy)**:
   - Thứ tự từ mép công trình đi ra ngoài bắt buộc:
     1. *Mép sàn / Công trình* $\rightarrow$
     2. *Tầng 1*: Kích thước chi tiết cột & chuỗi neo định vị trắc đạc (`DCE_Setout`) $\rightarrow$
     3. *Tầng 2*: Kích thước khoảng cách liên trục từng bước (`DCE_Dim`, DimStyle `Dce_100MV`) $\rightarrow$
     4. *Tầng 3*: Kích thước phủ bì tổng thể công trình (`DCE_Dim`) $\rightarrow$
     5. *Tầng 4*: Bong bóng trục ngoài cùng (`Dce_KhTenTruc`, text căn giữa, đường tim trục vươn xuyên qua các tầng dim).
4. **Khóa Solid Hatch Bê tông (Solid Concrete Hatch Enforcer)**:
   - 100% cột và vách BTCT phải có Solid Hatch màu xám kỹ thuật (`color = 8`, layer `DCE_Hatch`) với lệnh gọi `set_pattern_fill("SOLID")`. Cấm để cấu kiện rỗng ruột (hollow wireframe).
5. **Khóa Khung bản vẽ tiêu chuẩn & Bảng thống kê (Drawing Frame & Schedule Table Lock)**:
   - Mọi bản vẽ phải được đóng khung tiêu chuẩn A1 ($84100 \times 59400\text{ mm}$ ở 1:100) hoặc A0, có khung viền trong (lề gáy $25\text{ mm}$, lề khác $10\text{ mm}$) và Khung tên đồ án chuẩn DCE Pro (`DCE_Frame`) góc dưới phải.
   - Bản vẽ định vị cột vách bắt buộc có **Bảng Thống kê Tiết diện & Cốt thép Cột Vách** (`DCE_Schedule`) đặt ở lề phải, liệt kê đầy đủ STT, Mã CK, Kích thước, Cấp bê tông B35, Thép dọc, Thép đai và Số lượng.
   - Ô mở thang máy phải thể hiện nét cửa mở (`DCE_GapOpen`) có dầm lanh tô (`DCE_Lanh_To`); lỗ rỗng xuyên sàn thang bộ / MEP shaft phải có 2 nét gạch chéo X (`DCE_VoidX`).
6. **Khóa Luồng CAD-first, MCP-first & Visual Gate (Bài học 2026-11-15)**:
   - Xuất **CAD (`.dxf`/`.dwg`) qua MCP `dce-cad`** là mục tiêu chính: **không mặc định xuất PDF (`export_pdf=False`)** khi User không yêu cầu.
   - Luôn dùng luồng chính `DcePlanEngine` (`v6=True`) + `DCE_Master_Seed_Template.dxf`, cấm vẽ song song từ đầu trên fixture giả.
   - Bắt buộc test 1 ca công trình thật + tự soi ảnh `render_preview` trước khi bàn giao Dual-Agent (`DUAL_AGENT_BUS.json`) hay chốt hoàn thành.

---

## 12e. Khóa Cứng Quy tắc Trình bày Văn bản, Sàn Cỡ Chữ & Toán học Word/Excel (Clean Typography, Font Floor ≥ 10pt & Math Lock)

> **Cơ sở chuẩn hóa**: Nghị định 30/2020/NĐ-CP & nguồn sự thật design tokens tại `_SHARED/SHARED_CONTEXT/design_tokens.py` (trước đây từng gọi là Rule 12c trong các bản nháp cũ; nay thống nhất mã hiệu là **Điều 12e** để tách biệt hoàn toàn với Điều 12c về Cấp độ bền bê tông).

1. **Sàn cỡ chữ tối thiểu (Typography Floor Lock ≥ 10.0pt)**:
   - Báo cáo `.docx` & bảng tính `.xlsx` bắt buộc đạt sàn cỡ chữ: thân bài $\ge 11\text{ pt}$ (hành chính $13\text{ pt}$), bảng biểu và chú thích $\ge 10\text{ pt}$. Tuyệt đối cấm dùng `Pt(7..9.5)` hoặc `Font(size < 10)` trong bảng dữ liệu Word/Excel (kiểm toán tự động bởi `tools/audit_zero_white_text.py`).
2. **Cấm tuyệt đối Double Bullet (`•  •` — Trùng lặp 2 dấu chấm đầu dòng)**:
   - Khi gán `style='List Bullet'` hoặc `bullet: { level: 0 }`, Word tự render 1 bullet glyph `•`. Mọi generator (`_docx_helpers.py`, `docx_generator.py`, `docx_generator_v2.py`, `document_renderer.py`, `md_to_docx_report.js`) bắt buộc auto-strip ký tự `•, -, –, —, *` đứng đầu mục danh sách trước khi xuất đoạn văn.
3. **Tách biệt hoàn toàn Danh sách Thứ tự & Chữ cái khỏi List Bullet**:
   - Danh sách đánh số (`1., 2., 3.`) hoặc chữ cái (`a), b), c)`) bắt buộc dùng paragraph thụt lề (`left_indent`) hoặc numbering riêng, nghiêm cấm gán `style='List Bullet'`.
4. **Cấm tuyệt đối để lộ mã thô LaTeX trong Word**:
   - Toàn bộ ký hiệu toán học/thủy văn (`$H_{max}$`, `$H_{tb}$`, `$H_{min}$`, `$Q_{cd}$`, `$A_{s,req}$`, `$\gamma_f$`, `m^2`, `m^3`) phải chuyển qua parser thành subscript/superscript thật hoặc Unicode (`⇒, ×, ≥, ≤, ≈, Δ`) và xóa 100% ký tự `$` thô trước khi ghi `.docx`.

---

## 13. Minimum Narrative Depth (Độ sâu Diễn giải Tối thiểu)

Mọi Tờ trình/Báo cáo chính thức (Mode 2: .docx, Mode 1: .md) khi xuất file PHẢI đạt tổng nội dung phần thuyết minh **≥ 800 từ** (không tính bảng, heading, caption, Approval Matrix).
Nếu bản nháp dưới ngưỡng → AI phải tự bổ sung diễn giải theo thứ tự ưu tiên:

1. Bối cảnh & Lý do trình duyệt (tại sao bây giờ?)
2. Đánh giá hiện trạng chi tiết (cái gì hư? hư đến mức nào?)
3. Phương án đã xem xét và loại bỏ (tại sao không chọn?)
4. Diễn giải chi tiết phương án đề xuất (làm gì? bằng gì? bao nhiêu?)

---

## 14. Mandatory Illustration Integration (Bắt buộc Hình ảnh Minh họa)

Mọi Tờ trình chính thức BẮT BUỘC đính kèm tối thiểu **2 hình ảnh minh họa**:

- **Hình 1**: Mặt cắt chi tiết 2D (MODE 2D — Python) hoặc ảnh hiện trạng.
- **Hình 2**: Phối cảnh thiết kế 3D (MODE 3D — AI Render) hoặc biểu đồ so sánh phương án.
- Mỗi hình phải có **số hiệu** (Hình 1, Hình 2...) và **caption** mô tả.
- Ngoại lệ: Tờ trình chỉ liên quan đến phê duyệt hành chính (không có nội dung kỹ thuật) thì không bắt buộc.

---

## 15. Định dạng Version Control cho File Output

Quy tắc đặt tên file output chính thức:
`[MãDA]_[LoạiVB]_[GiaiDoan]_v[N]_[YYYYMMDD].[đuôi file]`
Ví dụ: `DuAnA_ToTrinh_BVTC_v2_20260625.docx`

Khi xuất lại file đã tồn tại:

- KHÔNG ghi đè file cũ — luôn tạo version mới (v1 → v2 → v3...)
- Ghi 1 dòng vào file `_CHANGELOG.md` cùng thư mục, format:
  `[YYYY-MM-DD HH:MM] v[N] — [Lý do sửa] — [Người yêu cầu]`

---

## 16. Tiết kiệm Token — Lazy Load Protocol

**Chỉ đọc file phụ khi thực sự cần thiết:**

- Tra tiêu chuẩn: Dùng `grep_search` với từ khóa đặc thù trước khi đọc PDF lớn. Đọc `INDEX_QUICK.md` trước `INDEX.md`.
- Vẽ MODE 3D: Đọc `MODE_3D_GUIDE.md` — KHÔNG đọc `MODE_2D_GUIDE.md`.
- Vẽ MODE 2D: Đọc `MODE_2D_GUIDE.md` — KHÔNG đọc `MODE_3D_GUIDE.md`.
- Xuất báo cáo: Đọc `SKILL_REPORT.md` — KHÔNG đọc `SKILLKC.md`.
- Tính toán kỹ thuật: Đọc `SKILLKC.md` — KHÔNG đọc `SKILL_REPORT.md`.

---

## 17. Hệ thống Mã Lỗi Chuẩn hóa (Error Code System)

| Code | Ý nghĩa | Hành động |
| -------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `E001` | Input validation failed | Hiển thị usage + ví dụ tham số hợp lệ |
| `E002` | Missing required data | Liệt kê các field còn thiếu, ghi `Data Missing:` |
| `E003` | Calculation inconclusive | Ghi Scope Limitation, không kết luận ĐẠT |
| `E004` | Standard conflict detected | Kích hoạt SKILL_VERIFY xử lý mâu thuẫn tiêu chuẩn |
| `E005` | Handoff schema invalid | Reject handoff, yêu cầu source skill gửi lại (xem `SKILL_BRIDGE.md §4.3`) |
| `E006` | Handoff missing required field | Block execution, request data từ upstream skill |
| `E007` | Circular dependency detected | Block loop, notify User, log event |
| `W001` | Approaching threshold (>90%) | Cảnh báo sát giới hạn nhưng không block |
| `W002` | η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `W003` | Low confidence output | Đánh dấu `[PENDING_VERIFICATION]`, gửi SKILL_VERIFY |
| `I001` | Info — η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `I002` | Auto-trigger fired | Log trigger execution, notify next skill |

---

## 17b. Confidence Level Handling

| Level | Score Range | Meaning | Action |
| ---------- | ----------- | -------------------------- | --------------------------------------- |
| `HIGH` | ≥ 0.85 | Đầy đủ data, validated | Tiếp tục bình thường |
| `MEDIUM` | 0.60 - 0.84 | Thiếu một số data | AUTO gửi SKILL_VERIFY |
| `LOW` | < 0.60 | Thiếu critical data | **BLOCK** xuất file, notify User |

### Confidence Score Calculator

Tool: `_SHARED/SHARED_CONTEXT/confidence_score.py`

**5 Factors trọng số:**

| Factor | Weight | Check |
| --------------------------- | ------ | ------------------------------------------- |
| `data_completeness` | 25% | Required fields present |
| `input_quality` | 20% | Material grades, dimensions in valid ranges |
| `standard_compliance` | 20% | Standards properly cited |
| `calculation_consistency` | 20% | Internal consistency of logs |
| `source_reliability` | 15% | Data source (measured/calculated/estimated) |

**Usage:**

```bash
python _SHARED/SHARED_CONTEXT/confidence_score.py \
    --input design_output.json \
    --verbose \
    --output confidence_result.json
```

**Integration:**

- Mọi skill output khi export phải ghi `confidence_level` vào JSON
- Confidence được tự động check trước khi xuất file chính thức
- LOW confidence → block export → notify User

---

## 18. Hệ sinh thái Skill & Pipeline Điển hình (v2.0 — Agentic)

> **MỚI v5.8:** Pipeline giờ tự động gọi skill tiếp theo qua INTER_SKILL_TRIGGERS. Xem chi tiết tại `INTER_SKILL_TRIGGERS.md`.

### 18.1 Agentic Workflow Flowchart

```
User Request
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  DISPATCHER (AGENTS.md §0)                                    │
│  Xác định Primary Skill + Entry Point                        │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  PRIMARY SKILL executes                                       │
│  1. Hoàn thành task chính                                   │
│  2. Check post-completion triggers                          │
│  3. Nếu trigger satisfied → Produce handoff JSON            │
│  4. Write to SHARED_CONTEXT/_active/                        │
│  5. Call next skill                                         │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  NEXT SKILL (automatic)                                      │
│  1. Read handoff từ SHARED_CONTEXT/                       │
│  2. Validate schema (SKILL_BRIDGE.md)                       │
│  3. If valid → process + check own triggers                │
│  4. If invalid → REJECT + request supplemental             │
└───────────────────────────────────────────────────────────────┘
    │
    └────────────────────────▶ Loop until END_STATE
```

### 18.2 CRITICAL: Design Pipeline (BẮT BUỘC Verify)

```
Structural_Design_Engineer
    │
    ├─► SKILL_CALC (section design)
    │
    ├─► SKILL_CONNECTION (connection design)
    │
    ├─► Technical_Illustrator (MODE 2D) — nếu cần hình
    │
    ├─► [POST-DESIGN-01] SKILL_VERIFY ──► QA CHECK (BẮT BUỘC)
    │                                      ⚠️ BLOCK file export
    │                                      cho đến khi PASS
    │
    └─► SKILL_CALC_REPORT (xuất Thuyết minh)

    [+ Auto-trigger nếu η ≤ 0.70]
    └─► Cost_Estimator (VE opportunity)
```

### 18.3 GEOTECH Pipeline (Auto-Handoff)

```
SKILL_GEOTECH
    │
    ├─► MODULE 1-10 (analysis)
    │
    ├─► [POST-GEOTECH-01] ──► Structural_Design_Engineer
    │                          (foundation params JSON)
    │
    ├─► [POST-GEOTECH-02] ──► Design_Evaluation
    │                          (base heave review)
    │
    └─► [POST-GEOTECH-03] ──► SKILL_FORENSIC
                                (adverse conditions alert)
```

### 18.4 REVIEW Pipeline

```
Design_Evaluation
    │
    ├─► SKILLKC (analysis)
    │
    ├─► Technical_Illustrator (MODE 2D)
    │
    ├─► [POST-EVAL-01] ──► Cost_Estimator
    │                       (nếu high cost detected)
    │
    ├─► [POST-EVAL-02] ──► SKILL_VERIFY
    │                       (nếu standard conflict)
    │
    └─► SKILL_REPORT (output)
```

### 18.5 VERIFY Flow

```
SKILL_VERIFY receives handoff
    │
    ├─► Check math consistency
    │
    ├─► Check standard compliance
    │
    ├─► Check cross-reference
    │
    └─► Check variance threshold (>5%)
            │
            ├─► PASS ──► Notify source skill
            │             → ALLOW file export
            │
            └─► FAIL (>5%) ──► REJECT source output
                                 → Request recalculate
                                 → Notify User
```

### 18.6 Quy trình Thẩm tra 7 Cổng Kiểm soát Bắt buộc (7-Gate Interlocked Pipeline — Gate 0–6)

Khi thực hiện nhiệm vụ **Thẩm tra Thiết kế Kết cấu & Đa bộ môn** (`Design_Evaluation`), nghiêm cấm nhảy cóc từ bước đọc lướt thuyết minh sang xuất báo cáo. Hệ thống bắt buộc đi qua tuần tự **7 Cổng Kiểm soát (Stage Gates 0–6)**:

```text
Hồ sơ Đầu vào (TMB, Bản vẽ KT, Bản vẽ KC, Thuyết minh TMKC .docx/.pdf, Mô hình ETABS, Báo giá .xlsx)
 │
 ▼
[GATE 0] Design_Evaluation + STANDARDS_LOCK.md
 │ • Bóc tách Bảng cân bằng đất trên TMB (tách GFA giai đoạn cấp phép vs toàn khu).
 │ • Phân cấp công trình theo TT 34/2026/TT-BXD (max GFA, Nhịp L_max, Chiều cao H) & Cấp hậu quả QCVN 03:2022/BXD.
 │ • Kiểm tra 02 Hold Points tiên quyết: (1) Báo cáo khảo sát ĐCCT có dấu pháp nhân; (2) Thuyết minh chịu lửa QCVN 06:2022/BXD.
 ▼
[GATE 1] SKILL_VERIFY (EMF Deep Parser) + SKILL_BIM_COORDINATION
 │ • Giải nén word/media/image*.emf trong mọi file .docx -> Đọc 100% bản ghi UTF-16LE của bảng tính gốc.
 │ • Render 100% trang PDF bản vẽ -> Kiểm đếm tờ bản vẽ bị thiếu theo từng hạng mục & quét lỗi #VALUE!, #REF!.
 ▼
[GATE 2] SKILLKC — Thẩm tra Chuyên sâu Tải trọng & Phân tích Tải (TCVN 2737:2023)
 │ • Tĩnh tải: Tách D_permanent và D_Solar; truy vết 100% tải giàn thao tác treo / trần M&E / cầu trục trên bản vẽ (KC-12..15).
 │ • Hoạt tải: Hoạt tải mái >= 0.30 kN/m² (γf=1.3); hoạt tải xe PCCC trên nắp bể ngầm 20–30 kPa (tải trục 100–120 kN).
 │ • Tải gió: Tính Gf đúng Phụ lục E (nhà thép ζ=0.02, cấm công thức tự chế Gf=0.85+h/1010); bắt buộc tổ hợp ce với áp lực gió
 │   bên trong nhà ci (+0.2/-0.3 đến +0.6 khi bung cửa); bắt buộc kiểm toán xà gồ dưới tải gió bốc ngược (Up, cấm nhập Gió=0).
 │ • Áp lực đất tĩnh K0 = 1-sin(φ) tách rời áp lực nước ngầm; nhiệt độ & kháng chấn TCVN 9386:2025.
 ▼
[GATE 3] SKILLKC — Thẩm tra Tổ hợp Tải trọng Nghịch đảo & Cực đoan (ULS / SLS)
 │ • Tổ hợp Gió bốc / Nhổ cột / Lật móng / Đẩy nổi: Bắt buộc dùng 0.90 * D_permanent (TUYỆT ĐỐI KHÔNG cộng tải Solar chưa lắp!).
 │ • Tổ hợp Bể ngầm / Tầng hầm: Cấm gộp nước trong bể (HTN) và đất ngoài bể (TTĐ) tự triệt tiêu nhau; bắt buộc xét tổ hợp
 │   'Bể rỗng bảo trì + Đầy đất & Nước ngầm + Xe PCCC chạy trên nắp'.
 │ • Tổ hợp SLS: Xét từng hướng gió tiêu chuẩn (γf=1.0) riêng biệt, không dùng hàm bao ENVE.
 ▼
[GATE 4] SKILLKC — Phân tích Đường truyền lực 3D, Sơ đồ Tính & Ổn định Kết cấu
 │ • Tương thích Sơ đồ Chân cột (Khớp/Ngàm) với độ cứng bản đế và sự tách rời đáy móng (σ_min < 0 gây xoay móng θ làm vọt độ võng
 │   công son; khung mảnh μx > 2.0 phải xét hiệu ứng bậc 2 P-Delta).
 │ • Kiểm tra chiều dài tự do thực tế Lef của cánh dưới chịu nén tại vùng mô men âm nách kèo (có Flange Stay trên bản vẽ không?).
 │ • Kiểm tra độ mảnh bản bụng (λ_w, λ_uw) -> Bắt buộc vẽ sườn ngang và sườn dọc; kiểm tra đường truyền lực dọc nhà tại trục cột giữa
 │   và kiểm toán chống đẩy nổi Archimedes (K_đn >= 1.15).
 ▼
[GATE 5] SKILL_BIM_COORDINATION + SKILL_VERIFY (drawing_calc_crosscheck.py) — Đối soát 4 Chiều
 │ • Truy vết tọa độ nút chân cột trong bảng Joint Reactions của ETABS sang bảng tính móng (chống gán nhầm nút cột giữa/cột biên).
 │ • Đo độ lệch tâm cổ cột e0 trên Mặt bằng móng so với Mặt cắt; tính diện tích thép bản vẽ As_drawing >= As,tt.
 │ • Đối chiếu kích thước móng, cổ cột, dầm, xà gồ, số lượng cấu kiện và ký hiệu trục giữa KT ↔ MB ↔ MC/Chi tiết ↔ TMKC.
 ▼
[GATE 6] SKILL_RFI + SKILL_REPORT — Chế tài Kỹ thuật & Xuất bản Báo cáo Chuẩn Corporate
   • Phát hành Phiếu RFI-DES-YYYYMMDD-NNN và Biên bản đình chỉ NCR-DES-YYYYMMDD-NNN.
   • Kiểm toán công thức sống Excel (cấm gộp ô làm mất công thức liên kết) và xuất Báo cáo DOCX (Body >= 11pt, Table >= 10pt, 300 DPI).
```

---

## 19. Version Control for Skills

Mỗi skill file (`SKILL.md`) phải có frontmatter version. Xem `CHANGELOG.md` tại cấp `.agents/skills/` để theo dõi lịch sử thay đổi của toàn bộ bộ skills.

---

## Changelog

| Version | Date       | Changes                                                                                                                                                                                          |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 7.4     | 2026-11-11 | Comprehensive Ecosystem Audit: Hợp nhất SSOT `.agents/AGENTS.md` ↔ `.agents/skills/AGENTS.md`, tách Điều 12e (Typography Floor & Math Lock), chuẩn hóa 14 skills & 18+ suites                     |
| 7.3     | 2026-11-09 | CAD DCE Pro Graphic Standards (Điều 12d), Bộ lọc 8 Graphic Sanity Auditor, `cad_plan_engine.py` v3.0, `SKILL_DUAL_AGENT_BRIDGE` v3.1.0                                                             |
| 7.2     | 2026-11-05 | Zero White Text Lock (Điều 12b), Concrete Grade Realism Lock (Điều 12c), Clean Typography & Math Lock (nay là Điều 12e)                                                                          |
| 7.0–7.1 | 2026-11-02 | Master 7-Gate Interlocked Pipeline (Gate 0–6) & Enterprise Patches F01–F06                                                                                                                       |
| 6.1     | 2026-10-18 | Phase 1 Infrastructure + SKILL_TEMPWORKS                                                                                                                                                         |
| 6.0     | 2026-10-12 | Master Central Orchestrator: Tích hợp Global_Dispatcher, intent_classifier.py, keyword_database.json (220+ keywords), pipeline_builder.py                                                      |
| 5.9     | 2026-09-27 | P1: Handoff Validation & Confidence Score                                                                                                                                                        |
| 5.8     | 2026-09-25 | **P0:** Agentic Workflow Infrastructure — SKILL_BRIDGE.md + INTER_SKILL_TRIGGERS.md                                                                                                       |
| 5.7     | 2026-09-26 | Critical fixes: Version sync, Encoding fixes, Lazy load standardization                                                                                                                          |
| 5.6     | 2026-09-16 | Added SKILL_GEOTECH dispatcher rules                                                                                                                                                             |
| 5.5     | 2026-09-15 | Master Unified Release: Tích hợp đầy đủ Bảng Dispatcher, Error Codes, Quy tắc tính toán, Minimum Narrative Depth, Mandatory Illustration và sửa lỗi công thức cơ học kết cấu. |
| 5.4     | 2026-08-30 | Audit fixes: SKILL_INDEX v1.4 sync, REGISTRY_INDEX rewrite, registry.json v2.1.0; STANDARDS_LOCK v2.3.0                                                                                          |
| 5.3     | 2026-08-30 | Reorganized structure: _SYSTEM/,_CORE_SKILLS/,_SUPPORT_SKILLS/,_SHARED/; Created README.md entry point                                                                                        |
| 5.0     | 2026-08-25 | Đồng bộ version skills, cập nhật deprecated scripts path                                                                                                                                    |
| 1.0     | 2026-06-01 | Initial release                                                                                                                                                                                  |
