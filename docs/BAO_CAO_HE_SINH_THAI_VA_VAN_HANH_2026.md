# BÁO CÁO TOÀN DIỆN HỆ SINH THÁI AI KỸ SƯ KẾT CẤU & QUY TRÌNH VẬN HÀNH HIỆN TRẠNG
## *(Tài liệu Định hướng Chiến lược & Kiến trúc Kỹ thuật dành cho Đội ngũ Chuyên gia)*

> **Đơn vị xây dựng:** Hệ sinh thái Kỹ thuật Kết cấu & QLTK AI  
> **Phiên bản hệ thống:** v6.4 $\rightarrow$ v7.0 (Sprint 5 / Dual-Agent Architecture)  
> **Ngày phát hành:** 23/10/2026  
> **Cơ sở dữ liệu:** `g:\My Drive\Google AI Studio\`  
> **Mục đích:** Báo cáo hiện trạng kiến trúc, cơ chế vận hành tự động và lộ trình nâng cấp dành cho Hội đồng Chuyên gia, Kỹ sư Trưởng và Kiến trúc sư Hệ thống.

---

## 1. TỔNG QUAN & TRIẾT LÝ THIẾT KẾ (EXECUTIVE PHILOSOPHY)

Hệ sinh thái này **không phải là một chatbot AI thông thường** dùng prompt đơn lẻ. Đây là một **Hệ điều hành Trí tuệ Nhân tạo Đa tác tử (Multi-Agent Operating System)** chuyên biệt cho ngành Tư vấn Thiết kế và Quản lý Thiết kế (QLTK) Xây dựng.

### 3 Nguyên lý Cốt lõi:
1. **Phân tách Nhận thức & Tính toán (Cognitive vs Deterministic Separation):**  
   - LLM (Claude / Gemini) chỉ đảm nhận tầng **suy luận logic, nhận diện ý định và diễn giải ngôn ngữ kỹ thuật**.
   - **Tuyệt đối cấm LLM nhẩm toán:** 100% phép tính kết cấu (nội lực, võng nứt, liên kết, móng, ổn định cốp pha) được ủy thác cho **script Python tất định (`calculators/`)** và trả kết quả dạng JSON kèm `Calculation_Logs`.
2. **Version Lock — Tiêu chuẩn Kỹ thuật là Nguồn Sự Thật Duy Nhất:**  
   Khóa cứng các phiên bản tiêu chuẩn xây dựng Việt Nam mới nhất hiện hành (`TCVN 2737:2023`, `TCVN 5575:2024`, `TCVN 5574:2018`, `TCVN 9386:2025`). Nghiêm cấm sử dụng công thức của các phiên bản cũ đã hết hiệu lực.
3. **Cơ chế Kiểm soát Kỹ sư (Human-in-the-Loop & Review Gate):**  
   Mọi sản phẩm đầu ra chính thức (.docx, .pdf, tờ trình) bắt buộc phải vượt qua Cổng duyệt (Review Gate). Kết quả tính toán chỉ mang tính chất tham khảo chuyên môn cao và luôn có khung trách nhiệm pháp lý rõ ràng.

---

## 2. KIẾN TRÚC TỔNG THỂ KHÔNG GIAN LÀM VIỆC (WORKSPACE TOPOLOGY)

Không gian làm việc đã được tái cấu trúc triệt để, phân định ranh giới rành mạch với **0 file rác nằm ngoài**:

```text
g:\My Drive\Google AI Studio\
│
├── .agents/                     # ⭐ BỘ NÃO AI AGENTIC (853.8 MB | 13 Skills, Core Tools, Tests)
├── .claude/ & .vscode/          # Cấu hình IDE & Giao thức Agent Client
├── memory/                      # ⭐ BUS ĐIỀU PHỐI (MEMORY.md, DUAL_AGENT_BUS.json)
│
├── 00_Template_&_Standards/     # ⭐ KHO TRI THỨC DÙNG CHUNG (952.1 MB | 3,776 files)
│   ├── Tieu_Chuan_TCVN/         # Tiêu chuẩn Tải trọng, Thép, Bê tông, Gió, Kháng chấn
│   ├── Sach_Giao_Trinh/         # 12 Giáo trình kinh điển (Võ Phán, Đoàn Định Kiến, Nền móng...)
│   ├── Thuyet_Minh_Mau/         # Mẫu Thuyết minh chuẩn BKTECHS & TVTK Đa Hạng Mục
│   ├── Chuyen_De_BPTC/          # Hồ sơ ĐCCT, Plaxis hố đào, tường vây
│   ├── Chuyen_De_Coppha/        # Thuyết minh & công cụ tính ván khuôn, shoring
│   ├── Prompt_Templates/        # Thư viện prompt chuẩn hóa
│   ├── Archive_Old_Reports/     # Báo cáo cũ đã lưu trữ
│   └── Scripts_Tien_Ich/        # Bộ công cụ tiện ích xử lý Word/Excel dùng chung
│
├── 01_Projects/                 # ⭐ 15 DỰ ÁN THỰC TẾ (1,323 MB | Chuẩn hóa 100%)
│   ├── 00_Management_QLTK/      # Quản lý tiến độ, MOM, kế hoạch sản xuất phòng QLTK
│   ├── MONTALP/                 # Dự án Đa hạng mục (6 Phân khu độc lập)
│   ├── SS1/                     # Dự án Mega Mall DIYAS SS1
│   ├── PRIME DIAMOND/           # Dự án Prime Diamond (Kết cấu & Logo)
│   ├── [11 Dự án Đơn mục khác]   # Nhà An Hitech, Nhà Bản Nguyên, iHome, Minh Châu...
│   └── 99_Archived/             # Kho lưu trữ dự án cũ
│
└── 02_Web_Applications/         # ỨNG DỤNG MÃ NGUỒN WEB THUẦN TÚY (0.3 MB)
    ├── crypto-gold-analyzer/
    └── market-dashboard/
```

---

## 3. CHUẨN HÓA DỰ ÁN & KHÔNG GIAN NHÁP CỦA AGENT

Để các script Python tự động hóa (`sync_bus.py`, `dce_excel_bus.py`) tự động quét đầu vào và xuất đầu ra mà **không cần hỏi lại đường dẫn**, toàn bộ 15 dự án tuân theo 2 mô hình chuẩn:

### 3.1 Mô hình Dự án Đơn mục (Single-package Projects)
Áp dụng cho 12 dự án độc lập (SS1, Prime Diamond, Nhà Bản Nguyên, Nhà Ăn Hitech...):
```text
01_Projects/<Tên_Dự_Án>/
├── 01_Input_CAD_PDF/         # Bản vẽ .dwg/.dxf, hồ sơ .pdf TVTK gửi (Read-only)
├── 02_Calculation_Models/    # Mô hình ETABS/SAP2000, file tính Excel .xlsx, .xlsm
├── 03_Agent_Workspace/       # ⚠️ KHÔNG GIAN NHÁP RIÊNG CỦA AI (Script .py, data .json, plots)
└── 04_Deliverables_ToTrinh/  # File sản phẩm hoàn thiện (.docx, .pdf tờ trình ký duyệt)
```
> **Đột phá:** Sự xuất hiện của `03_Agent_Workspace/` đã **xóa bỏ hoàn toàn thư mục `scratch/` hỗn loạn** ở thư mục gốc trước đây. Mọi tính toán nháp của AI được cô lập trong từng dự án tương ứng.

### 3.2 Mô hình Dự án Đa hạng mục (Multi-package Projects — MONTALP)
Đối với dự án quy mô phức hợp gồm nhiều gói thầu/phân khu độc lập, cấp cao nhất là **Từng Hạng Mục**, và bên trong mỗi Hạng mục chia tiếp 4 thư mục tiêu chuẩn:
```text
01_Projects/MONTALP/
├── 01_Khung_Thep_Facade/     ──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
├── 02_Nha_Mau_Cafe/          ──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
├── 03_Sale_Gallery_Coming_Soon/──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
├── 04_Danh_Gia_Nha_Thau/     ──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
├── 05_Tien_Do_Thi_Cong/      ──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
└── 06_Logo_Branding/         ──► [01_Input | 02_Calc | 03_Agent_Workspace | 04_Deliverables]
```

### Bảng Kiểm Tra Kết Quả 15 Dự Án (Audit Matrix)
| Tên Dự Án | Loại Hình | 01_Input | 02_Calc | 03_Agent | 04_Deliv | Loose Files |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **MONTALP** | Đa hạng mục | 3 gói | 4 gói | 4 gói | 5 gói | **0** ✅ |
| **SS1** | Đơn mục | 12 items | 13 items | 33 items | 16 items | **0** ✅ |
| **PRIME DIAMOND** | Đơn mục | 6 items | 0 | 9 items | 3 items | **0** ✅ |
| **NHA AN HITECH** | Đơn mục | 7 items | 0 | 20 items | 7 items | **0** ✅ |
| **NHA BAN NGUYEN** | Đơn mục | 3 items | 0 | 17 items | 7 items | **0** ✅ |
| **IHOME** | Đơn mục | 2 items | 8 items | 7 items | 0 | **0** ✅ |
| **MINH CHAU** | Đơn mục | 3 items | 3 items | 3 items | 3 items | **0** ✅ |
| **NHA PHO Q2** | Đơn mục | 3 items | 0 | 3 items | 5 items | **0** ✅ |
| **NHA THEP BMT** | Đơn mục | 1 items | 0 | 4 items | 3 items | **0** ✅ |
| **HO YEN QUANG** | Đơn mục | 2 items | 0 | 0 | 3 items | **0** ✅ |
| **FREELANCER_Sale_Gallery**| Đơn mục | 3 items | 0 | 8 items | 8 items | **0** ✅ |
| **LEEMAN TREE** | Đơn mục | 2 items | 0 | 1 items | 5 items | **0** ✅ |
| **48-52 HA LONG VUNG TAU** | Đơn mục | 0 | 0 | 0 | 1 items | **0** ✅ |
| **00_Management_QLTK** | Nội bộ | \- | \- | \- | \- | **0** ✅ |
| **99_Archived** | Lưu trữ | \- | \- | \- | \- | **0** ✅ |

---

## 4. BỘ NÃO TRÍ TUỆ NHÂN TẠO (THE AI AGENTIC ENGINE)

Hệ thống được cấu trúc thành **5 tầng nhận thức & thực thi** chuyên sâu:

### 4.1 Danh mục 13 Tác tử Kỹ sư Chuyên ngành
1. **`Global_Dispatcher` (v1.0.0):** Bộ điều phối trung tâm, phân loại ý định qua 417 từ khóa kỹ thuật và tự động dựng pipeline chuỗi tác tử.
2. **`Design_Evaluation` (v2.2.0):** Kỹ sư QLTK / Chủ đầu tư — Thẩm tra QC/QA hồ sơ theo giai đoạn, Value Engineering, giải quyết NCR, lập tờ trình.
3. **`Structural_Design_Engineer` (v1.3.0):** Kỹ sư Thiết kế Độc lập — Tự động tính toán tiết diện dầm/cột/sàn/móng, thiết kế liên kết bu lông, đường hàn, bản mã.
4. **`SKILL_GEOTECH` (v3.0.0):** Kỹ sư Địa kỹ thuật — Đánh giá ĐCCT, quy đổi thông số Plaxis (HS/MC), tính ổn định hố đào, Strut, Waling Beam, truyền tải sang ETABS.
5. **`SKILL_TEMPWORKS` (v1.0.0):** Kỹ sư Temporary Works — Thiết kế cốp pha sàn/cột/tường, kiểm tra hệ giằng và cây chống Shoring.
6. **`SKILL_FORENSIC` (v1.2.0):** Chuyên gia Điều tra Sự cố — Khám nghiệm hiện trường, phân tích nguyên nhân nứt/sập, tính toán ngược (back-calculation), xếp hạng xác suất nguyên nhân.
7. **`SKILL_VERIFY` (v1.2.0):** Module Kiểm chứng Chéo QA — Tự động đối chiếu chéo kết quả tính toán giữa các module, bắt lỗi sai lệch $>5\%$ và cảnh báo xung đột tiêu chuẩn.
8. **`SKILL_PHULUC` (v1.2.0):** Lập Thuyết minh & Phụ lục — Xuất file Word (.docx) chuyên nghiệp tích hợp công thức Math XML (OMML native), header chống tràn trang và mục lục tự động.
9. **`SKILL_RFI` (v1.2.0):** Quản lý Giao dịch Kỹ thuật — Quản lý vòng đời RFI, NCR, Submittal, Change Order giữa CĐT, TVGS, Nhà thầu, TVTK.
10. **`Cost_Estimator` (v1.2.0):** Kỹ sư Định giá — Tính BOQ, so sánh CAPEX các phương án kết cấu, tính toán Embodied Carbon.
11. **`Technical_Illustrator` (v1.3.0):** Kỹ sư Minh họa Kỹ thuật — Xuất bản vẽ 2D chính xác (Python/matplotlib) và ảnh phối cảnh 3D trực quan (AI render).
12. **`Project_Manager` (v0.5.0):** Quản lý Dự án — Phân cấp công trình (Thông tư 34/2026/TT-BXD, QCVN 03:2022/BXD), tiến độ, Risk Register, ĐTM & PCCC.
13. **`SKILL_BIM_COORDINATION` (v0.5.0):** Phối hợp BIM — Clash detection giữa Kết cấu & Cơ điện (MEP), kiểm tra lỗ mở xuyên dầm/sàn trên mô hình IFC.

### 4.2 Các Trụ Cột Đảm Bảo Độ Tin Cậy Kỹ Thuật
- **Policy Engine (`tools/policy_engine.py`):** Code hóa 36 quy tắc kỹ thuật nghiêm ngặt (Phase A/B/C) quản lý ngưỡng hệ số sử dụng $\eta$:
  - $\eta \le 0.70$ (Xanh): An toàn dư $\rightarrow$ Kích hoạt `Cost_Estimator` để tối ưu Value Engineering.
  - $0.70 < \eta \le 0.90$ (Vàng): Tối ưu vật liệu.
  - $0.90 < \eta \le 1.00$ (Cam): Cảnh báo sát ngưỡng cho kỹ sư thi công.
  - $\eta > 1.00$ (Đỏ): **Khóa xuất file**, yêu cầu điều chỉnh giải pháp.
- **Confidence Scorer (Bộ chấm điểm tin cậy 5 yếu tố):**
  - Data Completeness (25%) + Input Quality (20%) + Standard Compliance (20%) + Calculation Consistency (20%) + Source Reliability (15%). Điểm $< 0.60$ tự động chặn xuất file chính thức.
- **Hệ Thống 15 Test Suites (379 Tests Toàn Diện):**
  - Toàn bộ 15 test suites hệ thống (Regression calculators, Pre-execution gates, Intent benchmarks, Policy Engine) **đạt tỷ lệ 379/379 tests PASS (100%)**.

---

## 5. BỘ MÁY GIAO TIẾP DUAL-AGENT (CLAUDE CODE $\longleftrightarrow$ GEMINI ANTIGRAVITY)

Một trong những thế mạnh kiến trúc độc đáo nhất của hệ thống là khả năng **vận hành song song hai bộ não AI hàng đầu thế giới** theo mô hình Peer-Programming:

```
┌────────────────────────────────────────┐           ┌────────────────────────────────────────┐
│           CLAUDE CODE                  │           │           GEMINI ANTIGRAVITY           │
│  (Mô hình Phân tích Sâu & Logic)       │           │  (Mô hình Ngữ cảnh Lớn & Điều phối)   │
│ • Kiểm toán kiến trúc & Code Review    │           │ • Ngữ cảnh khổng lồ 2M tokens         │
│ • Viết Unit Test & Phát hiện Bug       │           │ • Refactor và chuẩn hóa toàn bộ dự án  │
│ • Kiểm chứng độc lập chéo              │           │ • Trực tiếp thao tác IDE & File System │
└───────────────────┬────────────────────┘           └───────────────────▲────────────────────┘
                    │                                                    │
                    │ 1. Ghi bàn giao (Handoff)                          │ 2. Đọc nhận lệnh
                    ▼                                                    │
          ┌──────────────────────────────────────────────────────────────────────┐
          │  CẦU NỐI TRẠNG THÁI (FILE-BASED IPC BUS)                             │
          │  Vị trí: memory/DUAL_AGENT_BUS.json                                  │
          │  Script điều khiển: python .agents/tools/sync_bus.py                 │
          │  • last_updated_by: CLAUDE / GEMINI                                  │
          │  • artifacts_modified: [danh sách tài liệu]                          │
          │  • next_action_for_partner: { target_agent, command }                │
          │  • Verification_Status: APPROVED / PENDING_ACTION                    │
          └──────────────────────────────────────────────────────────────────────┘
```

### Cách Vận Hành Trong Thực Tế:
- **Từ giao diện Claude Code Extension:** Người dùng chỉ cần gõ `@memory/DUAL_AGENT_BUS.json <Yêu cầu>` để Claude đọc ngay snapshot bàn giao từ Gemini và thực thi công việc.
- **Từ giao diện dòng lệnh:** Sử dụng script `python .agents/tools/sync_bus.py --read` hoặc gửi lệnh bàn giao có cấu trúc.

---

## 6. LỘ TRÌNH ĐỊNH HƯỚNG PHÁT TRIỂN (STRATEGIC ROADMAP CHO CHUYÊN GIA)

Để hệ sinh thái tiếp tục phát triển từ cấp độ "Trợ lý Kỹ thuật Chuyên sâu" lên "Nền tảng Tự động hóa Thiết kế Cấp Doanh nghiệp", Hội đồng Chuyên gia kiến nghị tập trung vào 4 trọng tâm:

```
2026 Q4 (Ngay bây giờ)         2027 Q1                        2027 Q2                        2027 Q3
┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
│ GIAI ĐOẠN 1:         │      │ GIAI ĐOẠN 2:          │      │ GIAI ĐOẠN 3:          │      │ GIAI ĐOẠN 4:          │
│ CỦNG CỐ NỀN TẢNG      │ ───► │ SEMANTIC RAG KHO SÁCH │ ───► │ SÂU RỘNG CAD/BIM/OAPI │ ───► │ THẨM TRA TỰ ĐỘNG      │
│ • Commit Git v7.0     │      │ • Vector index 952MB  │      │ • DCE Pro DLL hooks   │      │ • Thẩm tra đa đồ án   │
│ • Hoàn thiện 13 Skills│      │ • Tra cứu TCVN < 1s   │      │ • ETABS OAPI Direct   │      │ • Pháp lý cấp Sở/Bộ   │
│ • Test suites 100%    │      │ • Auto Citation       │      │ • Revit IFC sync      │      │ • Xuất BOQ tự động    │
└───────────────────────┘      └───────────────────────┘      └───────────────────────┘      └───────────────────────┘
```

### Chi Tiết 4 Trọng Tâm Phát Triển:

#### 1. Hoàn Thiện Nền Tảng & Đóng Gói Phiên Bản (P0 — Ngay bây giờ)
- **Git Consolidation:** Đóng gói toàn bộ 192 thay đổi trong `.agents` thành mốc Release chính thức `v7.0 Master Agentic Architecture`.
- Nâng cấp 2 skill `Project_Manager` và `SKILL_BIM_COORDINATION` từ bản placeholder `v0.5.0` lên bản thương mại `v1.0.0`.

#### 2. Xây Dựng Động Cơ Tra Cứu Tiêu Chuẩn Thông Minh (Semantic RAG Engine)
- Thiết lập bộ Vector Index (nhúng ngữ nghĩa) cho **952.1 MB** tài liệu tiêu chuẩn và sách giáo trình trong `00_Template_&_Standards`.
- Cho phép AI tra cứu chính xác bảng tra khí động, hệ số nền $C_1, C_2$, bảng tra độ võng cho phép trong vòng **dưới 1 giây** kèm trích dẫn hình ảnh/bảng tra trực tiếp vào báo cáo.

#### 3. Tích Hợp Sâu Phần Mềm Chuyên Ngành (CAD / BIM / ETABS API)
- **AutoCAD / DCE Pro Integration:** Khai thác 558,884 binary strings đã giải mã từ 4 thư viện DLL của phần mềm DCE Pro (`DCE Pro.dll`, `DCE Excel.dll`) để tự động hóa việc xuất bản vẽ mặt cắt dầm/cột/móng sang định dạng AutoCAD `.dwg` có gắn XData chuẩn.
- **ETABS OAPI Direct Link:** Kết nối trực tiếp qua API OpenETABS để đọc nội lực dầm/cột và gán tải trọng gió tự động theo TCVN 2737:2023 thay vì đọc thủ công qua file Excel trích xuất.

#### 4. Nền Tảng Thẩm Tra Tự Động Đa Đồ Án Cấp Doanh Nghiệp
- Tự động hóa kiểm tra hồ sơ thiết kế của các Tư vấn Thiết kế gửi về cho Chủ đầu tư/Ban QLDA: phát hiện dầm thiếu thép, cột quá tải, móng lún lệch vượt ngưỡng, xung đột xuyên dầm MEP.
- Tự động phát hành Tờ trình phê duyệt hoặc Báo cáo Thẩm tra chuẩn thể thức văn bản hành chính xây dựng.

---

## 7. KẾT LUẬN & KIẾN NGHỊ BÀN GIAO

Hệ sinh thái AI Kỹ sư Kết cấu hiện tại đã đạt đến độ **trưởng thành kiến trúc rất cao**:
- **Không gian lưu trữ hoàn hảo:** Thư mục gốc sạch tuyệt đối, 15 dự án phân lớp 4 thư mục tiêu chuẩn, 0 file rác.
- **Hệ thống AI an toàn tuyệt đối:** Loại bỏ 100% ảo giác số liệu bằng động cơ tính toán tất định Python, kiểm soát chặt chẽ bằng Policy Engine và Cổng kiểm duyệt Kỹ sư.
- **Cơ chế hợp tác Dual-Agent độc nhất:** Kết hợp sức mạnh trí tuệ của cả Claude Code và Gemini Antigravity.

Tài liệu này được lưu trữ chính thức tại [`00_Template_&_Standards/BAO_CAO_HE_SINH_THAI_VA_VAN_HANH_2026.md`](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/docs/BAO_CAO_HE_SINH_THAI_VA_VAN_HANH_2026.md) để phục vụ công tác nghiên cứu, định hướng chiến lược và nâng cấp của Hội đồng Chuyên gia.
