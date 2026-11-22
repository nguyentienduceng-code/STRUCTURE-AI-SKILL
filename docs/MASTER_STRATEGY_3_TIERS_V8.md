# KIẾN TRÚC CHIẾN LƯỢC TỔNG QUAN 3 TẦNG ĐỘC LẬP (`MASTER_STRATEGY_3_TIERS_V8`)

> **Phiên bản:** v8.0 (Khóa định hướng 2026-11-22)  
> **Phạm vi:** Toàn bộ hệ sinh thái `.agents/` (`g:\My Drive\Google AI Studio\.agents`)  
> **Nguyên tắc tối cao:** Hoàn thiện từng tầng theo thứ tự ưu tiên giá trị thực tế. **Hoàn thiện hoặc nâng cấp một tầng tuyệt đối không làm gãy hoặc thay đổi hợp đồng của các tầng còn lại.**

---

## 1. BỨC TRANH CHIẾN LƯỢC 3 TẦNG ĐỘC LẬP (DECOUPLED ARCHITECTURE)

Hệ sinh thái AI Kết cấu `.agents` được tổ chức thành **3 Tầng (Tier) độc lập**, giao tiếp qua hợp đồng dữ liệu JSON/Markdown chuẩn hóa trong `skills/SKILL_BRIDGE.md`:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1 (TRỤ CỘT CỐT LÕI — ƯU TIÊN SỐ 1, ĐÃ ĐẠT 100% PRODUCTION READY)       │
│ 1. Pháp lý & Tiêu chuẩn (STANDARDS_LOCK v3.3.0, StandardsGraph, Guard PDF)  │
│ 2. Đọc Bản vẽ Thẩm tra, Phụ lục & Hồ sơ Đa định dạng (TVTT & CĐT Ingestion) │
│ 3. Hệ thống 14 Skills Tính toán Cơ bản & Lập Phụ lục Xác định (122 scripts) │
│ 4. Phân tích Tư duy, Đối chiếu Chéo & Quyết định cho Chuyên viên TVTT & CĐT │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
          Hợp đồng Dữ liệu Độc lập (SKILL_BRIDGE.md / JSON Sidecar)
                 ┌─────────────────────┴─────────────────────┐
                 │                                           │
┌────────────────┴──────────────────────┐  ┌─────────────────┴────────────────┐
│ TẦNG 2 (MỞ RỘNG KỸ NĂNG VẼ — 2D/3D)  │  │ TẦNG 3 (KẾT HỢP ETABS/SAFE/SAP)  │
│ • 2D CAD (Technical_Illustrator DCE  │  │ • Trích xuất Nội lực kiểm chứng  │
│   Pro v5.0, mcp_dce_cad_server, 25    │  │   (M, N, V, Phản lực, Chuyển vị) │
│   cổng G8.01–G8.25, AutoCAD 2021)     │  │   từ ETABS 21 / SAP2000 22–25 /  │
│ • 3D Revit/BIM (SKILL_BIM_COORDINATION│  │   SAFE qua Excel/CSV/.e2k/OAPI   │
│   & OpenBIM/IFC read-only pilot)      │  │ • Truyền JSON về Tầng 1 kiểm tra │
└───────────────────────────────────────┘  └──────────────────────────────────┘
```

### Hợp đồng Cô lập Lỗi (Strict Modular Isolation Contract)
1. **Tầng 1 chạy 100% độc lập:** Không phụ thuộc AutoCAD, Revit, `ifcopenshell`, ETABS COM hay SAP2000 OAPI. Toàn bộ bài toán pháp lý, đọc bản vẽ DXF/PDF/Word/Excel, tính toán cấu kiện cơ bản, lập phụ lục thuyết minh và phân tích thẩm tra đều chạy bằng Python thuần trên dữ liệu hồ sơ tĩnh.
2. **Tầng 2 là lớp mở rộng trình bày 2D/3D:** Đọc kết quả từ Tầng 1 (hoặc dữ liệu hình học) để sinh bản vẽ `.dxf`/`.dwg` hoặc đối chiếu mô hình `.rvt`/`.ifc`. Sự cố ở AutoCAD/Revit hoặc nâng cấp thư viện đồ họa không được phép chạm tới logic tiêu chuẩn hay công thức Tầng 1.
3. **Tầng 3 là lớp lấy nội lực kiểm chứng từ phần mềm FEM chuyên dụng:** Không cạnh tranh với ETABS/SAFE/SAP2000 về giải ma trận $K \cdot U = F$. Tầng 3 chỉ trích xuất bảng nội lực, phản lực gối tựa và chuyển vị tầng rồi chuyển chuẩn hóa về Tầng 1 để chạy kiểm tra $\eta$, đối chiếu bản vẽ và lập báo cáo. Khi máy không mở ETABS/SAP2000, Tầng 1 vẫn hoạt động bình thường với bảng Excel/CSV xuất sẵn hoặc nhập tay có kiểm soát.

---

## 2. ĐẶC TẢ CHI TIẾT TẦNG 1: PHÁP LÝ — ĐỌC BẢN VẼ & PHỤ LỤC — TÍNH TOÁN — PHÂN TÍCH TƯ DUY (TVTT & CĐT)

Tầng 1 giải quyết **80% giá trị sử dụng hằng ngày**: hỗ trợ **Chuyên viên Tư vấn Thẩm tra (TVTT)** và **Chuyên viên Chủ đầu tư / QLTK (CĐT)** đọc hồ sơ bản vẽ/thuyết minh, kiểm toán lại các phép tính cơ bản bằng script xác định, phát hiện sai lệch tiêu chuẩn/hình học và ra quyết định có căn cứ pháp lý.

### 2.1. Bốn Khối Năng lực của Tầng 1

| Khối Năng lực | Thành phần Chính trong `.agents/` | Vai trò Nghiệp vụ |
|---|---|---|
| **1A. Pháp lý & Tiêu chuẩn** | `skills/STANDARDS_LOCK.md` (v3.3.0), `_SHARED/standards/standards_graph.py`, `tools/citation_grounding_auditor.py`, `skills/Project_Manager/scripts/project_grading.py`, `skills/SKILL_RFI/SKILL.md` | Khóa cứng phiên bản TCVN/QCVN (`2737:2023` gồm Phụ lục G Bảng G.1, `5574:2018`, `5575:2024`, `9386:2025`, `10304:2025`, `9362:2012`, `9363:2012`, `12041:2017`, `QCVN 03:2022/BXD`); phân cấp công trình & phát hiện xung đột tiêu chuẩn (`E004`); giữ dấu vết trích dẫn PDF thực tế. |
| **1B. Đọc Bản vẽ Thẩm tra, Phụ lục & Bảng tính** | `Design_Evaluation/scripts/cad_deep_reader.py` (`CAD_DEEP_READER`), `SKILL_VERIFY/scripts/drawing_calc_crosscheck.py` (EMF Vector Parser + Load/Combo + Reaction + Rebar Area + Formula Check), `SKILL_VERIFY/scripts/ingest_project_docs.py`, `SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`, `SKILL_BIM_COORDINATION/scripts/clash_detector.py`, `tools/doc_reader.py` | Bóc tách `.dxf`/`.dwg` (phẳng hóa Block lồng nhau `*U...` về WCS, giải mã tiếng Việt `TCVN3/VNI/SHX`, bắt lỗi sửa số Dim giả `> 2%`), trích xuất bảng tính nhúng `image*.emf` trong `.docx`, kiểm lỗi `#VALUE!/#REF!`, rà soát xung đột lưới trục — cao độ — mặt bằng ↔ mặt cắt ↔ tag thép. |
| **1C. Tính toán Cơ bản & Lập Phụ lục Xác định** | `Design_Evaluation/calculators/` (`6` calculators), `Structural_Design_Engineer/scripts/` (`16` scripts), `SKILL_PHULUC/` (`15` Markdown templates + `2` DOCX templates + `audit_phuluc_docx.py`), `SKILL_GEOTECH/` (`20` scripts), `SKILL_TEMPWORKS/` (`4` scripts), `Cost_Estimator/` (`8` scripts), `SKILL_FORENSIC/` (`5` scripts) | Thực thi công thức xác định theo Điều 5 `AGENTS.md` (mọi kết quả kèm `Calculation_Logs` và `Standard_Method`); tính kiểm tra uốn/cắt/nén/chọc thủng/võng/nứt BTCT, dầm & liên kết thép, sức chịu tải cọc, nền móng, thông số ĐCCT/hố đào, cốp pha/cây chống, BOQ/VE và điều tra sự cố. |
| **1D. Phân tích Tư duy & Hỗ trợ Ra Quyết định (TVTT & CĐT)** | `Design_Evaluation` (Quy trình 7 Cổng & `SKILLKC.md`), `tools/policy_engine.py`, `SKILL_RFI/scripts/` (`document_generator.py`, `document_tracker.py`), `Design_Evaluation/scripts/generate_clash_dossier.py`, `Global_Dispatcher/intent_classifier.py`, `tools/sync_bus.py` | Quy chuẩn đánh giá chỉ số sử dụng $\eta$ (`<=0.70` gợi ý VE, `0.70–0.90` đạt tối ưu, `0.90–1.00` cảnh báo sát ngưỡng, `>1.00` không đạt), phân loại lỗi `CRITICAL (Hold Point -> NCR) / MAJOR / MINOR (RFI)`, gán chế tài hợp đồng (`NĐ 37/2015/NĐ-CP`, `NĐ 217/2026/NĐ-CP` thay thế `NĐ 175/2024/NĐ-CP`) và xuất báo cáo chuẩn hóa. |

### 2.2. Quy trình Nghiệp vụ Đọc Bản vẽ & Phụ lục cho Chuyên viên TVTT và Chuyên viên CĐT/QLTK

```text
[HỒ SƠ ĐẦU VÀO CỦA TVTK: Bản vẽ .DXF/.DWG/.PDF + Thuyết minh/Phụ lục .DOCX/.XLSX]
                                       │
       ┌───────────────────────────────┴───────────────────────────────┐
       ▼                                                               ▼
[1. CỔNG ĐỌC BẢN VẼ THẨM TRA]                         [2. CỔNG ĐỌC PHỤ LỤC & TÍNH TOÁN]
• CAD_DEEP_READER (cad_deep_reader.py)                • doc_reader.py & EMF Parser
• SKILL_BIM_COORDINATION (Lớp 1–3)                    • Bộ lọc 2,3,4,6 (Tải, Phản lực,
• Bộ lọc 5 & 7 (Dim giả, Thép bản vẽ)                   As bản vẽ vs As tính toán, #REF!)
       │                                                               │
       └───────────────────────────────┬───────────────────────────────┘
                                       ▼
          [3. TÍNH TOÁN KIỂM CHỨNG ĐỘC LẬP & PHÂN TÍCH TƯ DUY (TẦNG 1)]
          • Policy Engine (η = Tác động / Khả năng) + StandardsGraph
          • Kiểm chứng lại cấu kiện điển hình bằng calculators TCVN mới nhất
          • Đối chiếu 4 chiều: Lưới trục ↔ Mặt bằng ↔ Mặt cắt ↔ Thuyết minh
                                       │
       ┌───────────────────────────────┴───────────────────────────────┐
       ▼                                                               ▼
[GÓC NHÌN CHUYÊN VIÊN TƯ VẤN THẨM TRA (TVTT)]   [GÓC NHÌN CHUYÊN VIÊN CHỦ ĐẦU TƯ (CĐT/QLTK)]
• Mục tiêu: Đúng TCVN/QCVN & An toàn chịu lực    • Mục tiêu: Tiến độ, Chi phí VE & Pháp lý HĐ
• Đầu ra:                                        • Đầu ra:
  - Báo cáo Kết quả Thẩm tra (SKILLKC / REPORT)    - Tờ trình Thẩm định & Quyết định CĐT
  - Phụ lục Tính toán Kiểm chứng (SKILL_PHULUC)    - Phân tích Tối ưu Ngân sách khi η ≤ 0.70
  - Hồ sơ Khoanh lỗi 1 Phiếu/Trang A4                (Cost_Estimator)
    (generate_clash_dossier.py)                    - Phiếu RFI / NCR + 4 Điều khoản Chế tài
                                                     (SKILL_RFI)
```

---

## 3. ĐẶC TẢ TẦNG 2 & TẦNG 3 (GIỮ RANH GIỚI RÕ RÀNG)

### 3.1. Tầng 2 — Mở rộng Kỹ năng Vẽ 2D CAD & 3D Revit/BIM
- **Phạm vi 2D CAD:** `Technical_Illustrator` (DCE Pro v5.0, `cad_plan_engine.py`, `cad_steel_peb_engine.py`, `cad_bptc_engine.py`), `mcp_dce_cad_server.py`, Bộ lọc 8 `dce_cad_compliance_checker.py` (25 cổng `G8.01–G8.25`), và `accoreconsole.exe` (AutoCAD 2021 hiện có trên máy).
- **Phạm vi 3D Revit/BIM:** Kết nối đọc-chỉ (`read-only`) cho Revit 2024 qua add-in pilot (`BIMwright rvt-mcp v1.2.2` hoặc `Horizun v4.0.1`) và đọc IFC mở (`IfcOpenShell` — chờ cài đặt khi triển khai Tầng 2). Không cho phép AI ghi đè trực tiếp mô hình Revit sản xuất khi chưa qua bước pilot kiểm định.
- **Hiện trạng công cụ trên máy trạm:** Đã xác nhận có AutoCAD 2021, Revit 2021, Revit 2024 (`0` third-party add-ins), `C:\Dce Pro`, `ezdxf 1.4.4`, `shapely 2.1.2`. Chưa cài `ifcopenshell`, ODA File Converter, pyRevit và SDK `.NET Framework 4.8` để biên dịch C#.

### 3.2. Tầng 3 — Kết hợp ETABS / SAFE / SAP2000 Lấy Nội lực Kiểm chứng
- **Nguyên tắc:** Chỉ trích xuất nội lực ($M, N, V$, phản lực gối, chuyển vị tầng) để nạp vào Tầng 1 kiểm tra cấu kiện và đối chiếu thuyết minh TVTK.
- **Phương thức kết nối:**
  1. Đọc bảng xuất chuẩn (`.xlsx`/`.csv`/`.txt`) và file văn bản mô hình (`.e2k`, `.f2k`, `.s2k`) — không phụ thuộc phiên bản COM đang chạy.
  2. Kết nối COM OAPI trực tiếp qua `tools/etabs_com_reader.py` trên máy có sẵn **ETABS 21** và **SAP2000 22 / 24 / 25**.

---

## 4. KIỂM KÊ TRẠNG THÁI HOÀN THIỆN TẦNG 1 & CÁC ĐIỂM CẦN MINH BẠCH

1. **Quy mô hệ thống đã kiểm chứng trên đĩa:**
   - **14/14 Domain Skills** ở trạng thái Production (`122` Python scripts được kiểm kê qua `tools/_collect_calculators.py`).
   - **50/50 Test Suites** qua `tests/run_all_tests.py --full` (`33` suite đăng ký tĩnh + `17` suite tự động đăng ký) và được đồng bộ vào `tools/_collect_tests.py`.
   - **Đồ thị Tiêu chuẩn (`_SHARED/standards/standards_graph.py`)** đồng bộ `STANDARDS_LOCK v3.3.0`, bao gồm cả nút kiểm toán võng mới `CLAUSE_2737_DEFLECTION` (`TCVN 2737:2023 Điều 11 & Phụ lục G, Bảng G.1`).
   - **Hệ thống Điều phối & Bus (`Global_Dispatcher` + `sync_bus.py`):** Khắc phục xong lỗ hổng tie-breaker P1-6 và đồng bộ trạng thái `work_ticket` / `lease_ttl_sec` P1-7.
2. **Trạng thái Hồ sơ Tiêu chuẩn & Pháp lý Gốc trên Đĩa (Cập nhật 2026-11-22):**
   - Toàn bộ tiêu chuẩn kỹ thuật (`TCVN 2737:2023`, `5574:2018`, `5575:2024`, `9386:2025`, `10304:2025`, `9362:2012`, `9363:2012`, `9346:2012`, `QCVN 02/03/04/06`) và 3 văn bản mới cập nhật (`TT 34/2026/TT-BXD`, `NĐ 217/2026/NĐ-CP` thay thế `NĐ 175/2024/NĐ-CP` từ 01/07/2026, và `QCVN 18:2021/BXD`) đã có đủ bản `.pdf` và `.docx` đồng bộ trong `Design_Evaluation/standards/QCVN/` và `00_Template_&_Standards/Tieu_Chuan_TCVN/TIEU CHUAN THUONG DUNG TRONG TKKCXD/`.
   - Các văn bản chưa có PDF riêng trên thư viện (`QCVN 01:2021/BXD`, `TCVN 12041:2017`, `TCVN 4419:1987`, văn bản gốc `Luật Xây dựng 135/2025/QH15`) vẫn phải giữ kỷ luật Điều 4 `AGENTS.md` (không suy diễn số trang PDF khi trích dẫn).
