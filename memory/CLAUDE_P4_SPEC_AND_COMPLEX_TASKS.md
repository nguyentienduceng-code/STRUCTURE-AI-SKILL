# CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md
# ĐẶC TẢ KỸ THUẬT VÀ PHÂN GIAO CÁC TÁC VỤ PHỨC TẠP SPRINT P4 CHO CLAUDE

> **Trạng thái:** ACTIVE / ASSIGNED TO CLAUDE  
> **Thời điểm cập nhật:** 2026-11-17  
> **Người giao việc (Coordinator):** Gemini (Antigravity)  
> **Người nhận bàn giao (Lead Systems Architect & Core Developer):** Claude (Claude Code / Desktop)  
> **Kênh giao tiếp IPC:** `.agents/memory/DUAL_AGENT_BUS.json` & `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`  
> **Bộ quy tắc bắt buộc:** `AGENTS.md` (Điều 12b Zero White Text, Điều 12c Cấp bê tông $\le$ B35/B40, Điều 12d CAD Quality Locks, Điều 12e Typography Floor $\ge 10\text{ pt}$ & Math Lock).

---

## 1. BỐI CẢNH VÀ KẾT QUẢ ĐÃ CHỐT (EXECUTIVE SUMMARY)

Sau phiên thẩm định chiến lược kiến trúc CAD (`CLAUDE_STRATEGIC_REVIEW_CAD_ROADMAP.md` và phản hồi độc lập đạt 40/50 điểm của Claude tại `CLAUDE_STRATEGIC_RESPONSE_CAD_ROADMAP.md`), User đã ra chỉ thị chính thức:
> *"Đồng ý và đưa các việc phức tạp hệ thống cho Claude thực hiện để phát triển."*

Toàn bộ 5 câu hỏi chiến lược (Q1–Q5) đã được thống nhất 100%:
1. **Q1 (Layer SSOT):** Áp dụng **Phương án 1B (Hybrid Extension)**. Giữ các layer ngữ nghĩa `DCE_CouplingBeam`, `DCE_Boundary_Zone`. Khóa 1 file JSON SSOT duy nhất (`dce_layers_standard.json`, 86 layers) và định hình các profile thông qua bộ lọc động (`cad_layer_standard.py`).
2. **Q2 (Không gian trình bày):** Giữ **ModelSpace làm mặc định** (`--layout-mode model`), đồng thời bảo lưu cấu trúc PaperSpace đa layout kèm bảng ghi chú CTB và hướng dẫn in 3 dòng trên layer `DCE_Note`.
3. **Q3 (Vòng lặp Re-import & Sửa Form):** Thống nhất mô hình tách bạch giữa Vỏ trình bày (Presentation Shell) và Dữ liệu kỹ thuật gốc (Engineering SSOT). Chuẩn hóa mã lỗi theo taxonomy `E002`, `E003`, `E005`, `E006`. Fallback 3 tầng: Project Local $\rightarrow$ Workspace Forms $\rightarrow$ Frozen SSOT Templates.
4. **Q4 (Giao diện Kép MCP/CLI):** Giữ MCP làm thin-wrapper không chứa business logic.
5. **Q5 (Lộ trình Sprint P4):** Thứ tự ưu tiên triển khai:
   $$\mathbf{P4.1} \text{ (Interactive Form Modification)} \longrightarrow \mathbf{P4.2} \text{ (Round-Trip RFI/NCR Generator)} \longrightarrow \mathbf{P4.3} \text{ (BIM/Revit Family Translation)}$$

---

## 2. NỀN TẢNG KỸ THUẬT ĐÃ ĐƯỢC GEMINI DỌN SẠCH & KHÓA AN TOÀN

Trước khi bàn giao các hạng mục phát triển phức tạp cho Claude, Gemini đã hoàn thành triệt để các chốt chặn an ninh và tính tương thích của hệ thống:

### 2.1. Đóng lỗ hổng An ninh Subprocess trong `convert_to_dwg`
- **Tệp:** `.agents/tools/mcp_dce_cad_server.py:325-390`
- **Hiện trạng xử lý:** Đã áp dụng `managed_dir("temp")` từ `dce_virtual_drive_guard.py`. 
  - Mọi file `.dxf` đầu vào được kiểm tra hợp lệ, sau đó cô lập vào thư mục scratch riêng biệt trên ổ đĩa cố định cục bộ NTFS (`C:` hoặc `D:`).
  - Lệnh gọi ODA File Converter (`subprocess.run([ODA_EXE, ...])`) tuyệt đối chỉ tương tác trong vùng scratch cô lập, không bao giờ nhận đường dẫn trực tiếp từ Google Drive hay đường dẫn ngoài kiểm soát.
  - Sau khi chuyển đổi thành công, file `.dwg` được kiểm tra kích thước (`stat().st_size > 0`) và dọn dẹp thư mục tạm an toàn.

### 2.2. Xóa bỏ Hardcoded Tuples — Chuyển sang Dynamic Profile Selectors (Option 1B)
- **Tệp:** `.agents/_SHARED/SHARED_CONTEXT/cad_layer_standard.py` & `.agents/skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`
- **Hiện trạng xử lý:**
  - Thêm `BTCT_CORE_LAYER_NAMES` (15 layers) và `STEEL_CORE_LAYER_NAMES` (16 layers) vào `cad_layer_standard.py`.
  - Bổ sung hàm `get_profile_layer_matrix(profile_name)` nạp thông số màu, đường nét, độ dày từ `dce_layers_standard.json`.
  - Refactor `DCE_BTCT_CORE` và `DCESTEEL_CORE` trong `cad_plan_engine.py` thành các selector động nạp từ SSOT, có fallback an toàn nếu chạy độc lập. Triệt tiêu hoàn toàn nguy cơ phân mảnh dữ liệu layer.

### 2.3. Bảng Kiểm Thử Toàn Diện (Zero Regressions)
- `test_dce_cad_compliance.py`: **26/26 PASS** (Bộ lọc 8, 20 Cổng kiểm soát chất lượng CAD).
- `test_cad_layer_standard.py`: **5/5 PASS** (Đồng bộ SSOT Layer).
- `test_cad_v6_c1.py` & `test_cad_v6_c2.py`: **13/13 PASS** (Tag Placement & Registry).
- `test_sheet_scale_fitter.py`: **11/11 PASS** (Dynamic Scale Governor).
- `test_mcp_dce_cad_server.py`: **13/13 PASS** (Toàn bộ 8 công cụ MCP CAD).

---

## 3. PHÂN GIAO CHI TIẾT CÁC TÁC VỤ PHỨC TẠP SPRINT P4 CHO CLAUDE

Claude nhận trách nhiệm chủ trì thiết kế kiến trúc và viết mã nguồn cho 3 module kỹ thuật cao sau:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SPRINT P4 ROADMAP PIPELINE                      │
├────────────────────────────────────────────────────────────────────────┤
│  [P4.1] INTERACTIVE FORM MODIFICATION ENGINE                           │
│  ├─ cad_form_contract.py (Standard Taxonomy E002, E003, E005, E006)    │
│  ├─ model_diff.py (DXF Diff Extractor & Geometry Delta Inspector)      │
│  └─ non_destructive_patcher.py (Selective Sheet Regenerator)           │
│                                  │                                     │
│                                  ▼                                     │
│  [P4.2] ROUND-TRIP RFI/NCR REPORT ENGINE                               │
│  ├─ rfi_ncr_bridge.py (20-Gate Filter 8 Audit -> Legal Findings)       │
│  ├─ cad_defect_cropper.py (dce_render_preview.py BBox Visual Injection)│
│  └─ rfi_ncr_docx_generator.py (Rule 12b Zero White Text & Rule 12e)    │
│                                  │                                     │
│                                  ▼                                     │
│  [P4.3] BIM / REVIT FAMILY TRANSLATION ENGINE                          │
│  ├─ bim_model_translator.py (model.json -> IFC4 / Structural Families) │
│  └─ revit_family_parameter_mapper.py (Column/Beam/Wall Param Sync)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

### TÁC VỤ P4.1: INTERACTIVE FORM MODIFICATION ENGINE (ƯU TIÊN SỐ 1)

#### 1. Bài toán Kỹ thuật
Khi kỹ sư mở file DXF Form (ví dụ `FORM_02_MULTIVIEW_A3_BTCT.dxf`), chỉnh sửa vị trí thép, thêm kích thước hoặc sửa nhãn trong AutoCAD/BricsCAD/ZWCAD rồi lưu lại:
Hệ thống **không được phép** ghi đè trực tiếp hay nuốt mất các thực thể mà người dùng đã vẽ thêm, đồng thời **không được phép** nhận các thay đổi vi phạm quy chuẩn kết cấu.

#### 2. Kiến trúc & Luồng Thực thi
1. **`open_form` (Read-only Inspection):**
   - Đọc form người dùng lưu trong thư mục dự án (`project_dir/forms/`).
   - Kiểm toán tính nguyên vẹn theo catalog manifest.
2. **`diff_form` (So sánh Sai biệt):**
   - Tệp phụ trách: `.agents/skills/Technical_Illustrator/cad_integration/model_diff.py`.
   - Trích xuất sai biệt giữa DXF hiện tại và baseline (SSOT gốc hoặc revision trước).
   - Phát hiện các thực thể bị di dời (`MOVE`), đổi nội dung (`TEXT_EDIT`), xóa (`DELETE`), thêm mới (`INSERT`).
3. **`schema_gate` (Cổng Kiểm soát Kỹ thuật Kết cấu):**
   - Kiểm tra ràng buộc kỹ thuật bắt buộc:
     - Cấp độ bền bê tông $\le \text{B35}$ (hoặc B40 theo Điều 12c `AGENTS.md`).
     - Hàm lượng cốt thép dầm/cột $\mu \in [0.1\%, 3.0\%]$.
     - Kích thước tiết diện không được âm hoặc nhỏ hơn $100\text{ mm}$.
   - Nếu vi phạm $\rightarrow$ từ chối merge, trả về mã lỗi `E006_SCHEMA_GATE_REJECTED`.
4. **`apply_agent_changes` (Merge Phân làn An toàn):**
   - Phân làn thực thể:
     - `DCE_AGENT_OWNED`: Vùng thuộc quyền agent quản lý (khung tên, bảng thống kê tự động).
     - `USER_EDITED`: Vùng người dùng can thiệp (bố trí dầm, nhãn thép bổ sung).
   - Cập nhật SSOT `model.json` lên phiên bản mới ($v \rightarrow v+1$) và lưu snapshot vào `model/revisions/model_v{N}.json`.
   - Kích hoạt tái sinh cục bộ **chỉ những tờ bản vẽ bị ảnh hưởng** (Selective Regeneration), bảo toàn nguyên vẹn các tờ khác.

#### 3. Bảng Mã Lỗi Chuẩn Hóa Bắt Buộc (Error Taxonomy Contract)
Claude cần đảm bảo toàn bộ mã lỗi trả về khớp 100% với taxonomy chuẩn sau:
- **`E001_FILE_NOT_FOUND`**: Không tìm thấy file DXF hoặc Model SSOT.
- **`E002_TEMPLATE_ZONE_MISSING`**: Người dùng vô tình xóa mất khung bao viền bản vẽ hoặc vùng giới hạn khung nhìn (Template Zone / Viewport Boundary).
- **`E003_TITLEBLOCK_ATTDEF_MISSING`**: Người dùng xóa mất các biến thuộc tính bắt buộc của Khung tên (`TENCAUKIEN`, `SOCAUKIEN`, `SCALE`, `REV`).
- **`E005_INVALID_DIFF`**: File DXF bị lỗi hình học không xác định, tự cắt chéo hoặc không khớp hệ tọa độ cơ sở.
- **`E006_SCHEMA_GATE_REJECTED`**: Thay đổi bị từ chối do vi phạm quy chuẩn kết cấu hoặc Điều 12c `AGENTS.md`.

---

### TÁC VỤ P4.2: ROUND-TRIP RFI/NCR REPORT ENGINE (ƯU TIÊN SỐ 2)

#### 1. Bài toán Kỹ thuật
Khi Bộ lọc 8 (`dce_cad_compliance_checker.py`) chạy kiểm toán 20 Cổng và phát hiện lỗi (ví dụ: vi phạm 4 tầng kích thước G8.04, đè chữ nhãn G8.10, thiếu vùng biên vách G8.09):
Hệ thống cần tự động phát hành **Hồ sơ RFI / Biên bản NCR chuẩn Pháp lý Xây dựng Việt Nam** (Nghị định 175/2024/NĐ-CP, Thông tư 34/2026/TT-BXD, Thông lệ Hợp đồng FIDIC White Book) dưới dạng tài liệu Word (`.docx`) và PDF chất lượng cao.

#### 2. Yêu cầu Thiết kế Chi tiết
1. **Phân loại Nghiêm trọng Tự động (Severity Mapping):**
   - **Critical / Major $\rightarrow$ Phát hành Biên bản NCR (Non-Conformance Report):**
     - Áp dụng cho: Cột vách rỗng ruột (thiếu Solid Hatch), đè chữ nghiêm trọng không đọc được, vi phạm hệ trục trần, thiếu vùng biên kháng chấn.
     - Kèm điều khoản chế tài hợp đồng TVTK theo mẫu quy định của `SKILL_RFI`.
   - **Minor $\rightarrow$ Phát hành Phiếu RFI (Request for Information):**
     - Áp dụng cho: Kích thước tầng 1 thiếu chi tiết định vị, thiếu ghi chú CTB, tên cấu kiện chưa căn giữa.
2. **Trích xuất Bằng chứng Trực quan CAD (Visual Evidence Crop):**
   - Sử dụng `dce_render_preview.py` để crop ảnh cận cảnh đúng bounding box của vị trí lỗi.
   - Nhúng trực tiếp ảnh minh họa vào bảng mô tả lỗi của file Word (kích thước ảnh rõ nét, độ phân giải 300 DPI, tỷ lệ hiển thị cân đối).
3. **Tuân thủ Tuyệt đối Bộ Khóa Định dạng Word (Rules 12b & 12e):**
   - **Điều 12b (Zero White Text Lock):**
     - Header bảng biểu: Nền sáng gốc khoáng **Xanh Đá Phiến Sương Nhạt (`#DCE4EC`)** hoặc **Đá Vôi Sáng (`#EAE6DF`)**.
     - Chữ tiêu đề: Chữ in đậm màu tối **Xanh Thép Trầm (`#1E3246`)** hoặc **Mực Than Chì (`#1C1E21`)**.
     - Dòng dữ liệu: Chữ tối (`#1C1E21`), nền xen kẽ Trắng (`#FFFFFF`) và Ngà Giấy Tự Nhiên (`#F8F7F4`), viền lưới mảnh `#D0CEC7`.
     - **CẤM TUYỆT ĐỐI** chữ màu trắng trên nền tối để đảm bảo in ấn đen trắng/photocopy không bị mất chữ.
   - **Điều 12e (Sàn cỡ chữ $\ge 10.0\text{ pt}$ & Khóa Toán học):**
     - Sàn cỡ chữ: Thân bài $\ge 11\text{ pt}$, bảng biểu $\ge 10\text{ pt}$. Cấm dùng cỡ chữ nhỏ hơn 10pt.
     - Triệt tiêu Double Bullet (`•  •`): Luôn strip ký tự bullet trước khi add vào list item.
     - Khóa toán học: Chuyển toàn bộ ký hiệu LaTeX ($A_{s}$, $R_b$, $\gamma_f$) thành Unicode / sub-superscript thật, xóa 100% ký tự `$` thô.

---

### TÁC VỤ P4.3: BIM / REVIT STRUCTURAL TRANSLATION ENGINE (ƯU TIÊN SỐ 3)

#### 1. Bài toán Kỹ thuật
Kết nối dữ liệu hình học và phi hình học từ `model.json` của DCE Plan Engine sang mô hình BIM OpenBIM (IFC4) hoặc bảng thông số Revit Family (`.rfa`).

#### 2. Yêu cầu Thiết kế Chi tiết
1. Ánh xạ phần tử kết cấu:
   - Cột (`columns`): Tiết diện, chiều cao tầng, cấp bê tông, thép dọc, thép đai $\rightarrow$ `IfcColumn` / Structural Column Family.
   - Vách (`walls`): Chiều dày, chiều dài, tọa độ tim $\rightarrow$ `IfcWallStandardCase` / Structural Wall Family.
   - Dầm (`beams`): Chiều rộng, chiều cao, cao độ đáy $\rightarrow$ `IfcBeam` / Structural Framing Family.
   - Sàn (`slabs`): Chiều dày, cao độ hoàn thiện $\rightarrow$ `IfcSlab`.
2. Xuất dữ liệu trung gian: JSON Schema trung gian chuẩn hóa cho phép import trực tiếp vào pyRevit hoặc Dynamo Script.

---

## 4. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

Mỗi tác vụ khi Claude hoàn thành cần đáp ứng các điều kiện nghiệm thu nghiêm ngặt sau:

| Tác vụ | File cần sinh / cập nhật | Bộ Test bắt buộc | Tiêu chuẩn thành công |
|---|---|---|---|
| **P4.1** | `cad_form_contract.py`<br>`model_diff.py`<br>`cad_form_patcher.py` | `.agents/tests/test_p4_interactive_form.py` | 100% PASS; phát hiện đúng sai biệt; chặn đứng vi phạm schema; mã lỗi chuẩn `E002-E006`. |
| **P4.2** | `rfi_ncr_bridge.py`<br>`rfi_ncr_docx_generator.py` | `.agents/tests/test_p4_rfi_ncr_generator.py` | Sinh file `.docx` đúng mẫu Nghị định 175; nhúng ảnh crop lỗi CAD; kiểm toán `audit_zero_white_text.py` đạt 0 lỗi. |
| **P4.3** | `bim_model_translator.py` | `.agents/tests/test_bim_translator.py` | Chuyển đổi chính xác 100% tọa độ và tiết diện cột/dầm/vách sang schema BIM trung gian. |

---

## 5. THỦ TỤC BÀN GIAO & CẬP NHẬT TRẠNG THÁI IPC BUS

1. **Trạng thái Bus:**
   - File: `.agents/memory/DUAL_AGENT_BUS.json`
   - `last_updated_by`: `"GEMINI"`
   - `target_agent`: `"CLAUDE"`
   - `current_holder`: `"CLAUDE"`
   - `handoff_status`: `"PENDING"`
   - `active_task`: `"SPRINT_P4_COMPLEX_TASKS"`
   - `spec_file`: `.agents/memory/CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`

2. **Chỉ dẫn cho Claude:**
   - Đọc kỹ tài liệu này và file `DUAL_AGENT_HANDOFF_MEMO.md`.
   - Bắt đầu triển khai từ **Tác vụ P4.1**, tạo file test `test_p4_interactive_form.py` trước hoặc song song với code.
   - Sau khi hoàn thành P4.1 và P4.2, chạy kiểm toán toàn diện và cập nhật trạng thái lên `DUAL_AGENT_BUS.json`.
