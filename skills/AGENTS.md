# AGENTS.md — Quy tắc vận hành Agent kết cấu

Các đường dẫn trong chỉ mục tính từ gốc workspace. Ba bản AGENTS.md ở gốc, trong .agents và trong .agents/skills dùng cùng nội dung.

## Điều 0. Phân luồng và phân vai

Global_Dispatcher xác định đồng thời skill chuyên môn và chế độ công việc. Ưu tiên cờ /prod, /sys, /solo rồi xét mục đích sử dụng đường dẫn. Khi cần xác định dự án mà có nhiều kết quả hoặc thiếu kết quả, dừng ở NEEDS_PROJECT_CONFIRMATION. Chọn tác tử cho từng ca ưu tiên hơn mặc định dự án.

| Chế độ | Phân vai và đầu ra |
|---|---|
| PRODUCT_COLLAB | Khi phối hợp, Gemini lập sản phẩm, Claude thẩm tra và xuất đúng 04_Deliverables_ToTrinh của dự án. Chỉ sửa script khi được giao quyền. Cổng hồ sơ kiểm tra tệp thật lớn hơn 0 byte, cập nhật sau giao việc và đúng thư mục đích. Báo cáo cho kỹ sư dùng tiếng Việt chuyên ngành, tránh thuật ngữ hạ tầng và có đúng ba ý gồm hạng mục đã sửa, vị trí tệp, kết luận và căn cứ. |
| SYSTEM_UPGRADE | Bảo trì hạ tầng, skill, MCP. Dùng kiểm thử, mã băm và bằng chứng bàn giao theo phạm vi sửa. |
| SOLO_EXECUTION | Một tác tử làm việc độc lập, tắt bus. Giữ nguyên kiểm tra nguồn, xác nhận trước xuất và kiểm tra tệp cuối. |

AUTO theo phân vai của ca. CLAUDE_ONLY hoặc GEMINI_ONLY giao một tác tử. DUAL phối hợp theo phụ thuộc trên phiếu. Phân biệt tự kiểm và kiểm tra độc lập đúng mã băm. Ca cần ký chuyển người có thẩm quyền. Xem bảng phân xử prompt lai và các cổng chi tiết trong .agents/skills/references/DISPATCH_AND_WORKFLOWS.md.

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

Khi vừa tính vừa lập tờ trình, tính trước rồi qua Review Gate và chuyển Design_Evaluation. Khi thiếu căn cứ chọn skill, hỏi người dùng. Điểm phân loại dưới 0.35 mặc định SOLO_EXECUTION. Khi đã xác định dự án và người dùng giao quyền, sửa script cục bộ để xuất lại hồ sơ vẫn là PRODUCT_COLLAB.

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

## Tra quy tắc theo tác vụ

Mở tệp tương ứng trong .agents/skills/references/ khi xử lý tác vụ.

- Màu chữ và bảng biểu — RULE_12B_ZERO_WHITE_TEXT.md
- Cấp bền bê tông — RULE_12C_CONCRETE_GRADE_REALISM.md
- Quy chuẩn đồ họa CAD — RULE_12D_CAD_DRAFTING_STANDARDS.md
- Điều 12e gốc về trình bày Word/Excel — RULE_12E_TYPOGRAPHY.md
- Mô hình hóa và đối chiếu Revit BIM — RULE_12E_REVIT_MODELING_STANDARDS.md
- Điều 0 chi tiết và phân xử prompt lai — DISPATCH_AND_WORKFLOWS.md
- Điều 13–17, lưu phiên bản hồ sơ, mã lỗi và độ tin cậy — REPORT_AND_ERROR_RULES.md
- Điều 18–19, bàn giao, thẩm tra 7 cổng và phiên bản skill — VERIFICATION_WORKFLOWS.md
- Lịch sử sửa quy tắc — AGENTS_CHANGELOG.md
