# Hồ Sơ Ngữ Cảnh Hệ Thống Kết Cấu AI (`.agents` v7.5.x → v8.0+) — Tài Liệu Đầu Vào Cho DeepResearch

> **Mục đích tài liệu:** Cung cấp bức tranh toàn diện, trung thực và có số liệu thực đo về kiến trúc phần mềm, hiện trạng mã nguồn CAD/BIM/Revit/IFC, dữ liệu thực chiến của 20 dự án, cùng phương án Codex vừa đề xuất — làm căn cứ để DeepResearch thực hiện thẩm định độc lập trên dữ liệu thị trường AEC/BIM/MCP toàn cầu và đề xuất chiến lược phát triển tối ưu nhất.

---

## 1. Bối Cảnh Doanh Nghiệp & Mô Hình Hoạt Động Thực Tế

- **Lĩnh vực:** Tư vấn Thiết kế Kết cấu & Quản lý Thiết kế (QLTK / Thẩm tra Thiết kế) công trình dân dụng, công nghiệp (BTCT, Kết cấu thép tiền chế PEB, Biện pháp thi công BPTC, Địa kỹ thuật) tại Việt Nam.
- **Môi trường vận hành thực tế (đã kiểm tra trên máy trạm):**
  - Hệ điều hành: Windows (lưu trữ làm việc đồng bộ qua Google Drive).
  - Phần mềm kỹ thuật đã cài trên máy đích: **AutoCAD 2021** (`R24.0.47.0.0`), **Revit 2021** (`20200220_1100(x64)`), **Revit 2024** (`20230308_1635(x64)`), **Python 3.12.7** (`ezdxf 1.4.4`, `shapely 2.1.2`, `mcp`, `pywin32/win32com`; **chưa cài `ifcopenshell`**).
- **Hệ tiêu chuẩn áp dụng bắt buộc (Version-Locked):** TCVN 2737:2023 (tải trọng & độ võng Điều 11/Bảng G.1), TCVN 5574:2018 (BTCT), TCVN 5575:2024 (Thép), TCVN 9386:2025 (Động đất), TCVN 10304:2025 (Móng cọc), TCVN 9362:2012 (Nền móng), TT 34/2026/TT-BXD (Phân cấp công trình), NĐ 217/2026/NĐ-CP (Quản lý hoạt động XD, thay thế NĐ 175/2024/NĐ-CP), QCVN 03:2022/BXD, QCVN 18:2021/BXD (An toàn thi công).
- **Nguyên tắc kiến trúc cốt lõi của hệ thống:**
  - **AI không thay thế phần mềm FEM/Địa kỹ thuật (ETABS, SAP2000, SAFE, Plaxis)** và **AI không tự nhẩm phép toán hoặc tự phán xét Đạt/Không đạt**.
  - Mọi phép kiểm tra kỹ thuật, tính toán chỉ số sử dụng ($\eta = \text{Tác động} / \text{Khả năng}$), kiểm tra bản vẽ đều phải chạy bằng **script xác định (Deterministic Code)** có log tính toán (`Calculation_Logs`) và trích dẫn điều khoản tiêu chuẩn (Citation Grounding); có **Review Gate** bắt buộc kỹ sư chủ trì xác nhận trước khi xuất hồ sơ chính thức.

---

## 2. Hiện Trạng Kiến Trúc Hệ Thống `.agents` (Git HEAD `1903d1f`, 22/11/2026)

### 2.1. Quy mô & Sức khỏe tổng thể
- **14 Production Skills (0 placeholder):** Điều phối trung tâm (`Global_Dispatcher` v3.0.0), Thẩm tra QLTK (`Design_Evaluation` v3.4.0), Thiết kế kết cấu (`Structural_Design_Engineer` v1.3.0), Phụ lục thuyết minh Word (`SKILL_PHULUC` v3.1.0), Bản vẽ CAD DCE Pro v5.0 (`Technical_Illustrator` v5.0.0), Kiểm chứng độc lập (`SKILL_VERIFY` v3.4.0), Địa kỹ thuật (`SKILL_GEOTECH` v3.1.0), Biện pháp thi công (`SKILL_TEMPWORKS` v1.0.0), Điều tra sự cố (`SKILL_FORENSIC` v1.2.0), Định giá/VE/Carbon (`Cost_Estimator` v1.4.0), RFI/NCR (`SKILL_RFI` v1.4.0), Quản lý tiến độ/EVM/MS Project (`Project_Manager` v2.0.0), Điều phối BIM (`SKILL_BIM_COORDINATION` v1.4.0 — **mới chỉ có 1 script `clash_detector.py`**), Cầu nối đa tác tử Gemini–Claude/Codex (`SKILL_DUAL_AGENT_BRIDGE` v3.4.0).
- **122 scripts tính toán & xử lý nghiệp vụ**, **23 dòng tiêu chuẩn khóa phiên bản (22 mã tiêu chuẩn/quy chuẩn/thông tư độc lập)**, hệ thống kiểm thử tự động **50/50 suites PASS (`303.54s`)**, `0` rò rỉ dữ liệu vận hành khi chạy test, `0` lỗi in ấn trắng/cỡ chữ nhỏ (Điều 12b & 12e).
- **Hạ tầng điều phối:** Bộ định tuyến nhận thức 2 chiều (`PRODUCT_COLLAB` / `SYSTEM_UPGRADE` / `SOLO_EXECUTION`), Đồ thị tri thức tiêu chuẩn SQLite (`StandardsGraph`), bộ bảo vệ trích dẫn PDF thật (`citation_grounding_auditor.py`), và Dual-Agent Bus v3.4 khóa nguyên tử + `RECEIPTS` SHA-256.

### 2.2. Năng lực CAD / BIM / Revit / IFC / MCP hiện có trong mã nguồn
**A. Những thành phần CAD đã hoạt động thực tế & có test kiểm chứng:**
1. **MCP CAD Server nội bộ (`dce-cad` — `tools/mcp_dce_cad_server.py`, 825 dòng, stdio):** Có **13 công cụ MCP** (`render_cad_plan`, `render_preview`, `consume_preview`, `release_preview`, `validate_cad`, `edit_entity`, `resolve_cad_collisions`, `convert_to_dwg`, `auto_layout_and_scale_plan`, `export_cad_sheet_set`, `open_form`, `diff_form`, `apply_agent_changes`), có sandbox Virtual Drive Guard tránh ghi nhầm lên Google Drive. `convert_to_dwg` hiện phụ thuộc ODA File Converter (trả về `UNAVAILABLE` nếu chưa cài).
2. **Engine vẽ tham số & dàn trang đa tỷ lệ (`cad_plan_engine.py`, `cad_steel_peb_engine.py`, `cad_bptc_engine.py`, `cad_sheet_set.py`):** Sinh bản vẽ DXF AC1021 (BTCT, Kết cấu thép PEB, BPTC), bố cục `COMPOSITE_DETAIL_GRID` đa tỷ lệ trong cùng ModelSpace, xuất sidecar `.json` gắn SHA-256 byte DXF thật.
3. **Bộ kiểm toán 20/25 cổng dựa trên bằng chứng DXF (`dce_cad_compliance_checker.py`, 1.673 dòng):** Kiểm tra cú pháp `ezdxf.audit()`, ma trận 87 layer SSOT (`cad_layer_standard.py`), kiểm va chạm chữ, kiểm xâm lấn khung tên/sidebar, kiểm khoảng cách/mép bu lông (`2.5 d0` / `1.5 d0`), ký hiệu hàn TCVN, đối chiếu tổng khối lượng BOM trên DXF vs JSON, và kiểm toán tọa độ vùng an toàn BPTC.
4. **Sổ đăng ký cấu kiện & kiểm chứng handle 3 chiều (`cad_element_registry.py`, 1.478 dòng):** Kiểm tra tính nhất quán liên bản vẽ (cột ngưng tầng, nhóm thiết kế, tách thép lớp trên/dưới) và mở lại DXF kiểm liên kết `handle ↔ tag ↔ dòng thống kê ↔ SHA-256`.
5. **Bàn chỉnh sửa DXF khóa phiên bản (`tools/cad_edit_workbench.py`, 223 dòng):** Khóa `.lock` nguyên tử, `HEAD.json` optimistic locking, lấy dấu vân tay DXF tag-level (`TagCollector.dxftags`) để chứng minh phần ngoài vùng sửa không bị biến đổi, hỗ trợ `undo()` (hiện chỉ áp dụng cho `TEXT`, `MTEXT`, `DIMENSION` phẳng).
6. **Chỉ mục không gian & chống đè chữ (`tools/cad_scene_index.py`, `cad_collision_solver.py`):** Dùng `ezdxf.disassemble` + `shapely 2.1.2`, đọc hệ số `$INSUNITS`, tôn trọng vùng kỹ sư đã sửa tay qua XData `DCE_USER_OVERRIDE`, leader gắn handle `DCE_COLLISION`.
7. **Làn trộn Form mở không phá hủy (`cad_form_contract.py`, `model_diff.py`, `cad_form_patcher.py`, `project_ops_manager.py`, `cad_block_adapters.py`):** Phân cấp form 3 tầng (Dự án → Chuẩn người dùng → SSOT), kiểm tra cổng schema (cấm bê tông > B35/B40 ngoài quy định, tiết diện >= 100 mm, hàm lượng thép 0.1–3.0%), lưu lịch sử `lineage.jsonl`, chỉ xóa/vẽ lại thực thể có XData `DCE_AGENT_OWNED`.
8. **Cầu nối XData thép (`tools/dce_xdata_bridge.py`, 550 dòng):** Đóng gói/đọc XData nhóm `1002` (RegApp `DCE_PRO`) và group code `1005 LINK_HANDLE` liên kết 2 chiều giữa nét cốt thép và block thống kê `TK1..TK44`.

**B. Những điểm yếu, lỗ hổng & nợ kỹ thuật vừa bị bóc tách qua kiểm toán mã nguồn:**
1. **Phân mảnh 3 Schema mô hình kết cấu không tương thích:**
   - *Schema A* (`model_schema.json` / `bim_model_translator.py`): dữ liệu lồng bên trong `sheets[*].viewports[*]`, dầm không có `element_id`, cột không có `floor_id`. Một dầm xuất hiện ở 2 viewport sẽ bị bóc thành **2 dầm trùng lặp**.
   - *Schema B* (`cad_plan_engine.py`): từ điển phẳng dùng đơn vị mét (`bx, by`), còn cấm cột lệch tâm âm (`0 <= off_x <= bx_mm` tại dòng 2554 — xung đột với cột Revit thật).
   - *Schema C* (`cad_element_registry.py` C1/v6): cấu trúc ngữ nghĩa đúng (có `element_id`, `floor_id`, `b_mm`, `h_mm`, tọa độ mm) nhưng chưa làm đầu vào thống nhất cho mọi nơi.
2. **Định danh cấu kiện chưa bền vững qua nhiều lần xuất/sửa CAD:**
   - `cad_element_registry.py` tự sinh UUID ngẫu nhiên mới nếu thiếu `element_id`; `cad_plan_engine.py` rơi về `BM_{idx:03d}`; các thực thể kết cấu trong `cad_plan_engine.py` **chưa nhúng `element_id` vào XData** (`DCE_AGENT_OWNED` mới chỉ ghi mỗi chuỗi `"GEOM"`).
   - Khi thử gắn XData `TEST-001` lên block ở `BEAM_SLAB_FRAMING.dxf` và sao chép bằng `ezdxf entity.copy()`, cả hai handle `13C` và `435` đều giữ nguyên `TEST-001` — chứng tỏ nếu không có trường **`role`** (vai trò đại diện chính vs tag/chi tiết) và luật bắt trùng owner, lệnh `COPY`/`WBLOCK` sẽ làm hỏng bảng đối chiếu.
3. **Lớp chuyển đổi BIM/Revit hiện tại mới là nguyên mẫu sơ khai & có nhiều bug:**
   - `bim_model_translator.py` (không được `mcp_dce_cad_server.py` hay `cad_element_registry.py` gọi) mặc định dầm nằm theo phương X, tính nhịp theo 1 trục (sai với dầm chéo/dốc), tạo `bim_id = f"BEAM-{ctx}-{mark}"` (trùng khóa khi 2 nhịp cùng ký hiệu `D1`), **lệch đơn vị 1000×** ở nhánh đọc tọa độ `x0/x1` của cột (mm vs mét), thiếu tầng/cao độ/góc xoay của cột, thiếu điểm cuối/chiều cao của vách, thiếu đa giác biên/lỗ mở của sàn.
   - `revit_family_parameter_mapper.py` chỉ xuất `SSOT_UUID` cho cột (bỏ dầm/vách/sàn), chưa map sang `BuiltInParameter` hay Shared Parameter GUID thật, và có bug gán nhầm `"TargetFamily": "StructuralColumnFamily"` lên cả Dầm, Vách, Sàn.
4. **Lệch hợp đồng MCP & `ifc_parser.py` rủi ro cao:**
   - `MCP_DCE_CAD_CONTRACT.md` mới ghi 8/13 tools và 20/25 cổng; `mcp_dce_cad_server.py:244` vẫn khóa `validate_cad` ở 3 profile cũ (chặn `steel_peb`/`bptc` qua MCP); đồng thời `render_cad_plan` gọi xuất `v6=True, full_evidence=False` khiến sidecar thiếu `semantic_log_format="v4"` và bị checker đánh `NEEDS_REVIEW`.
   - `ifc_parser.py` khi thiếu `ifcopenshell` vẫn rơi về regex thô hoặc `_demo_payload()` (sẽ xử lý dứt điểm khi triển khai Tầng 2 cài `ifcopenshell`); riêng lỗi `CDC-04` báo lỗi giả tầng hầm có cao độ `< 0` đã được khắc phục ở bản khóa Tầng 1.
5. **Nợ quản trị hệ thống Tầng 1 & ghi chú kiến trúc:**
   - **Đã khắc phục trong bản khóa Tầng 1 (22/11/2026):** `standards_graph.py` đã bổ sung nút `CLAUSE_2737_DEFLECTION`, `ND_217_2026_CP` và `QCVN_18_2021` theo `STANDARDS_LOCK v3.3.0`; `_collect_tests.py` đã tự động quét đủ `50/50` suites; `intent_classifier.py` & `sync_bus_2d_patch.py` đã sửa lỗi tie-breaker/skill `/sys` (P1-6); `sync_bus.py` đã đồng bộ `work_ticket.status` và `lease_ttl_sec` (P1-7). Khóa `FileLock` tại `%LOCALAPPDATA%` được giữ nguyên cho mô hình vận hành 1 máy trạm Windows đơn lẻ.

---

## 3. Dữ Liệu Thực Chiến Từ 20 Dự Án Thật (`01_Projects/` & `00_Template_&_Standards/`)

Kiểm đếm toàn bộ **1.836 tệp** trong 20 thư mục dự án (`01_Projects/`) và thư viện chuẩn (`00_Template_&_Standards/`):

| Loại tệp / Nền tảng | `01_Projects` (20 dự án) | `00_Template_&_Standards` | Nhận xét thực tế |
|---|---:|---:|---|
| **Revit / openBIM** (`.rvt`, `.ifc`, `.rfa`, `.rte`, `.nwc`) | **0** | **0** | **Không có bất kỳ tệp Revit hay IFC nào** trong toàn bộ kho dự án hiện hữu. |
| **AutoCAD Native** (`.dwg`) | **8** (`03_TAN_HY`: 2, `15.TEST`: 1, `16.BPTC Q12`: 5) | **25** (trọn bộ `DU AN MAU` kết cấu + Xref) | Có ở các dự án kết cấu & BPTC thật (`3–20 MB`/tệp). |
| **DXF** (`.dxf`) | **60** (8 thư mục) | **4** (`CAD_Forms`) | Convert `.dwg` sang `.dxf` làm phình dung lượng **5.4×–7.1×** (`19.97 MB → 141.06 MB` ở `16.BPTC Q12`; `11.65 MB → 62.66 MB` ở `03_TAN_HY`; `4.04 MB → 24.69 MB` ở `15.TEST`). |
| **ETABS / SAFE / Plaxis** | **0** *(chỉ xuất bảng Excel)* | **2 `.edb`**, **2 `.e2k`**, **4 `.$et`** | Dự án thực tế trao đổi Excel/PDF từ ETABS (`Bang_Quy_Tai_ETABS...xlsx`) chứ ít giao `.edb` gốc; `DU AN MAU` có đủ cặp DWG + `.edb`/`.e2k` + `.xlsm`. |
| **Word** (`.docx` + `.doc`) | **222 (+8)** *(177 ở `04_Deliverables_ToTrinh`)* | **28 (+12)** | **Sản phẩm đầu ra thu tiền chủ lực** (Thuyết minh, Tờ trình thẩm tra, BPTC). |
| **Excel** (`.xlsx` + `.xlsm`) | **91 (+3)** | **13 (+11)** | Bảng tính kiểm toán, BOQ thép và QLTK Checklist (`41 .xlsx` ở `00_Management_QLTK`). |
| **PDF & Ảnh kỹ thuật** | **157 `.pdf`**, **836 ảnh** | **95 `.pdf`** | Đầu vào khách hàng nhiều nhất là **90 `.pdf` + 93 ảnh** ở `01_Input_CAD_PDF`. |

---

## 4. Tóm Tắt Phương Án Codex Đề Xuất & 4 Câu Hỏi Lớn Cần DeepResearch Giải Đáp

### 4.1. Phương án Codex vừa đề xuất (`CAD_REVIT_MCP_MARKET_REVIEW.md`, 22/11/2026)
- **Không viết mới từ đầu plugin C# Revit hay bỏ `dce-cad`.**
- **Phía CAD:** Giữ `dce-cad` + `ezdxf`, tích hợp thêm thuật toán so snapshot (học từ `C48H74/autocad-mcp`), gắn XData `(ID, role)` và kiểm chứng native AutoCAD 2021 DWG/PDF plot.
- **Phía Revit 2024:** Chạy **pilot 10 ngày chỉ đọc** bằng **BIMwright `rvt-mcp` v1.2.2** (Apache-2.0; đọc được `UniqueId`, tọa độ 2 đầu dầm theo mm, tham số có kiểu dữ liệu phân biệt Type/Instance). Phương án dự phòng #1 là **Horizun `revit-mcp` v4.0.1** (`ModelDiffReader` snapshot hàng loạt); dự phòng #2 mới là tự viết lệnh C# xuất snapshot (học `ExternalEventManager` của `revit-mcp-plugin`). Không chọn Autodesk Revit MCP chính hãng vì mới là Tech Preview cho **Revit 2027.2**; cảnh giác `sharafutdinovdi/revit-model-mcp v2.1.0` có thao tác ghi nếu không khóa policy.
- **Bài thi quyết định (Pilot Decision Test):** Tầng 2 có 2 dầm cùng mark `D1` (nhịp A–B và B–C); revision mới đổi riêng B–C sang `250 × 600` và đổi tên `D1A`. Hệ thống phải chỉ ra đúng từng dầm sai/đúng, tag, dòng thống kê và phát hiện trường hợp sửa nhầm ở Revit `Type` dùng chung hoặc thay đổi bù trừ tổng khối lượng.

### 4.2. Các điểm Hội đồng nội bộ đang phản biện & cần DeepResearch kiểm chứng rộng
1. **Hiệu quả thực tế của các MCP Server cộng đồng:** `BIMwright rvt-mcp v1.2.2`, `Horizun v4.0.1`, `revit-model-mcp v2.1.0`, `C48H74/autocad-mcp`, `Autodesk Assistant MCP`, và các lựa chọn AEC 2025–2026 khác (như `pyRevit`, `Speckle MCP`, `RevitPythonShell / Dynamo / APS`) ngoài đời thực có vấn đề gì về tốc độ đọc hàng nghìn cấu kiện, tọa độ Link/Shared Coordinates, Family biến thể Việt Nam, Unicode UTF-8 và khóa read-only thực sự không?
2. **Chiến lược AutoCAD 2021 Native DWG tối ưu (tránh bloat DXF 141 MB):** So sánh chuyên sâu giữa **AutoCAD Core Console (`accoreconsole.exe`) + AutoLISP/.NET headless**, **Out-of-process COM (`win32com`)**, **ODA SDK / Teigha**, **Aspose/CADSharp**, và **Autodesk Platform Services (Forge)** để giải bài toán đọc/sửa/gắn XData/tách Xref/in PDF hàng loạt từ `.dwg` gốc 15–20 MB.
3. **Chuẩn hóa định danh bất biến xuyên CAD ↔ Revit ↔ ETABS ↔ Word:** Thực hành tốt nhất trong công nghiệp để giữ `element_id` sống sót qua AutoCAD `COPY`/`WBLOCK`/`AUDIT`, qua Revit `UniqueId` / `IfcGuid` / `Worksharing` / `Group` / `Copy-Monitor`, và qua bảng xuất ETABS/Excel mà không vỡ liên kết khi đổi mark cấu kiện.
4. **Phân bổ nguồn lực & ROI (`AutoCAD 2021 + Word/ETABS` vs `Revit 2024`):** Với thực tế 20 dự án hiện tại có `0 .rvt` nhưng có nhiều `.dwg`/`.docx`/`.xlsx`/`.pdf`, lộ trình phân bổ nguồn lực (70–80% cho CAD Native DWG + Khép vòng ETABS/Word vs 20–30% PoC Revit 2024 chỉ đọc) có hợp lý không? Cần mốc kích hoạt nào để chuyển sang đầu tư mạnh cho Revit / OpenBIM?
