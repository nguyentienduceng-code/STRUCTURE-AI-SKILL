# SỔ ĐĂNG KÝ NỢ KỸ THUẬT HỆ THỐNG (SYSTEM TECHNICAL DEBT REGISTER)
## HỆ THỐNG AGENTIC ĐIỀU PHỐI & TÍNH TOÁN KẾT CẤU `.AGENTS`

> **Phiên bản:** v2.0.0 — Tầng 1 Lock-In & 3-Tier Architecture Alignment  
> **Cập nhật ngày:** 2026-11-22  
> **Phạm vi quản lý:** Toàn bộ hệ sinh thái `.agents/` (14 Production Skills, 122 Python scripts kiểm kê qua `_collect_calculators.py`, 50 Test Suites, Policy Engine, Dual-Agent Bus v3.4, `STANDARDS_LOCK v3.3.0`)  
> **Chiến lược tổng quan:** Phân tách 3 tầng độc lập theo [`MASTER_STRATEGY_3_TIERS_V8.md`](./MASTER_STRATEGY_3_TIERS_V8.md) (Tầng 1: Pháp lý/Tiêu chuẩn/Đọc bản vẽ-phụ lục thẩm tra/Tính toán cơ bản/Phân tích tư duy TVTT & CĐT; Tầng 2: Vẽ 2D CAD & 3D Revit/BIM; Tầng 3: Kết hợp ETABS/SAFE/SAP2000 lấy nội lực kiểm chứng).

---

## 1. MA TRẬN TỔNG QUAN NỢ KỸ THUẬT (TECHNICAL DEBT MATRIX)

```mermaid
quadrantChart
    title Ma trận Nợ Kỹ thuật & Phân tầng Ưu tiên (v2.0)
    x-axis Độ phức tạp Thực hiện (Thấp --> Cao)
    y-axis Mức độ Ảnh hưởng Nghiệp vụ (Thấp --> Cao)
    quadrant-1 Mở rộng Tầng 2 & Tầng 3 (Ưu tiên Kế tiếp)
    quadrant-2 Kế hoạch Enterprise / Nâng cao
    quadrant-3 Cải tiến Nhỏ (Continuous)
    quadrant-4 Tầng 1 Đã Khóa (Resolved Core)
    "TD-03: 14/14 Skills Production": [0.40, 0.88]
    "TD-02: CAD DXF & BIM 3D IFC": [0.65, 0.85]
    "TD-05: 15+ Templates SKILL_PHULUC": [0.25, 0.55]
    "TD-07: 50/50 Test Suites Full CI": [0.35, 0.65]
    "TD-01: Local Bus v3.4 vs Cloud": [0.70, 0.60]
    "TD-04: Fiber P-Mx-My vs P-Delta/Raft": [0.80, 0.70]
    "TD-06: ETABS/SAP OAPI (Tầng 3)": [0.85, 0.80]
```

### Bảng Thống kê Phân loại Nợ Kỹ thuật

| Mã Nợ | Tầng | Lĩnh vực | Tên Hạng mục Nợ Kỹ thuật | Mức độ Nghiêm trọng | Độ Phức tạp | Kế hoạch Xử lý | Trạng thái |
|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|
| **TD-01** | Tầng 1 | Architecture | Handoff JSON & Bus v3.4 trên Local/Google Drive vs Multi-tenant Cloud API | Medium | Trung bình | Local Done / Cloud 2027 | 🟢 Resolved (Local Bus v3.4) / 🟡 Cloud Roadmap |
| **TD-02** | Tầng 1 & 2 | Integration | Đọc bản vẽ 2D `.dxf/.dwg` trực tiếp vs Parser 3D `.ifc`/Revit (`ifcopenshell`) | High | Trung bình | Tầng 1 Done / Tầng 2 Next | 🟢 Tầng 1 Resolved / 🔵 Tầng 2 Pending `ifcopenshell` |
| **TD-03** | Tầng 1 | Coverage | Hoàn thiện 3 Skills Placeholder (`TEMPWORKS`, `BIM`, `PM`) lên Production | High | Thấp - TB | Completed | 🟢 Resolved (14/14 Production Skills) |
| **TD-04** | Tầng 1 & 3 | Calculation | Giải tích phi tuyến tiết diện 3D (`P-Mx-My`) vs P-Delta tổng thể & móng bè đàn hồi | Medium | Cao | Tầng 1 3D Fiber / Tầng 3 FEA | 🔵 Partial (`calc_rc_section_pm_3d.py` done; P-Delta/Raft chưa tách script) |
| **TD-05** | Tầng 1 | Delivery | Mở rộng thư viện template Thuyết minh phụ lục (`SKILL_PHULUC`) | Low | Thấp | Completed | 🟢 Resolved (15 MD + 2 DOCX templates) |
| **TD-06** | Tầng 3 | Integration | Trích xuất nội lực kiểm chứng hai chiều với ETABS / SAFE / SAP2000 | Medium | Cao | Tầng 3 | 🔵 Partial (`etabs_com_reader.py` v1 done) |
| **TD-07** | Tầng 1 | Quality Assurance | Đồng bộ Test Coverage trên toàn bộ `run_all_tests.py` & `_collect_tests.py` | Medium | Thấp - TB | Completed | 🟢 Resolved (50/50 Test Suites Full CI) |
| **TD-08** | Tầng 2 | Integration (BIM) | **Tầng 2C: Revit 2024 Read-Only Connector + IFC (IfcOpenShell) — pilot chưa triển khai** | Medium | Trung bình - Cao | Tầng 2 (pending) | 🟡 Logged (solo 2B đã xong; 2C để làm sau) |

---

## 2. CHI TIẾT TỪNG KHOẢN NỢ KỸ THUẬT


### TD-01: Giao tiếp Handoff Trung gian qua Local JSON Files
- **Trạng thái hiện tại:** 🟢 **Resolved cho môi trường Local/Google Drive** qua Dual-Agent Bus v3.4 (`sync_bus.py`: `FileLock` nguyên tử, Lease/Heartbeat, Project-Scoped Resolver, SHA-256 Receipts, ProductDeliverableGate, Clean-Checkout Zero-Mutation). Phần mở rộng Multi-tenant Cloud API (Redis / In-Memory Broker) giữ tại Roadmap 2027.

---

### TD-02: Bộ nạp Dữ liệu Bản vẽ (CAD/BIM) Phụ thuộc File JSON Trung gian
- **Trạng thái hiện tại:** 🟢 **Resolved ở Tầng 1** — Đọc trực tiếp bản vẽ 2D `.dxf/.dwg` (`CAD_DEEP_READER` trong `Design_Evaluation/scripts/cad_deep_reader.py`), trích xuất bảng `EMF` nhúng trong `.docx`, quét xung đột qua `SKILL_BIM_COORDINATION/scripts/clash_detector.py` và `SKILL_VERIFY`.
- **Phần Tầng 2 (Mở rộng 3D Revit/IFC):** Tích hợp `ifcopenshell` đọc trực tiếp file `.ifc` và kết nối read-only Revit 2024 (`BIMwright` / `Horizun` pilot) sẽ triển khai ở **Tầng 2** (hiện `ifcopenshell` chưa cài trên máy trạm).

---

### TD-03: Hoàn thiện 3 Skills Placeholder lên Trạng thái Production (🟢)
- **Trạng thái hiện tại:** 🟢 **Resolved 100%** — Toàn bộ **14/14 Skills** đã đạt trạng thái Production (`0` placeholder):
  - `SKILL_TEMPWORKS` (v1.0.0): Đã hoàn thiện cả 4 calculators (`calc_formwork_slab.py`, `calc_formwork_column.py`, `calc_formwork_wall.py`, `calc_shoring_system.py`).
  - `SKILL_BIM_COORDINATION` (v1.4.0): Production với `scripts/clash_detector.py` và quy trình kiểm soát xung đột 3 lớp hình học + `CAD_DEEP_READER`.
  - `Project_Manager` (v2.0.0): Production với 8 scripts (`project_grading.py`, `evm_cpm_calculator.py`, `ms_project_gantt.py`, `msproject_xml_engine.py`, `msproject_bridge.py`, `iso_kpi_exporter.py`, `qltk_tracking_exporter.py`, `project_roadmap.py`).

---

### TD-04: Module Giải tích Phi tuyến Bậc cao & Móng Bè Đàn hồi
- **Trạng thái hiện tại:** 🔵 **Partial (Tầng 1 có tiết diện phi tuyến 3D; Tầng 3 xử lý bài toán khung P-Delta/Móng bè)**
- **Đã có:** `Structural_Design_Engineer/scripts/calc_rc_section_pm_3d.py` (Suite 24 — `test_rc_section_pm_3d.py`, 23 tests) tính tiết diện BTCT phi tuyến 3D $P-M_x-M_y$.
- **Chưa tách script độc lập (🟡 Logged):** Chưa có script độc lập cho phân tích bậc 2 $P-\Delta$ toàn khung hay hệ số nền Winkler/Pasternak; với công trình cao tầng hoặc móng bè cọc phức tạp, theo Chiến lược 3 Tầng (`MASTER_STRATEGY_3_TIERS_V8.md`), phần giải tích tổng thể sử dụng ETABS/SAFE/SAP2000 và trích xuất nội lực ở **Tầng 3** về Tầng 1 kiểm chứng.

---

### TD-05: Mở rộng Thư viện Template Thuyết minh Tính toán (SKILL_PHULUC)
- **Trạng thái hiện tại:** 🟢 **Resolved 100%** — `SKILL_PHULUC/templates/` hiện có **15 Markdown templates + 2 Word DOCX templates** (`APPENDIX_STAIR_RC.md`, `APPENDIX_WATER_TANK.md`, `APPENDIX_STRIP_FOUNDATION.md`, `APPENDIX_RETAINING_WALL.md`, `APPENDIX_PILE_FOUNDATION.md`, `APPENDIX_COLUMN_RC.md`, `APPENDIX_SLAB_RC.md`, `APPENDIX_HOIST_CRANE.md`, `APPENDIX_FORMWORK_SHORING.md`, `APPENDIX_STEEL_PORTAL_FRAME.md`, `PARTIAL_BE_TONG.md`, `PARTIAL_THEP.md`, `TMTT_STANDARD.md`, `TMTT_FULL.md`, `TMTT_FULL_INTEGRATED.md`, cùng 2 mẫu DOCX Bộ 1 BKTECHS / Bộ 2 TVTK) và 8 cổng kiểm toán tại `SKILL_PHULUC/scripts/audit_phuluc_docx.py`.

---

### TD-06: Giao thức Kết nối Trực tiếp OAPI với ETABS/SAFE/SAP2000 (**Phân loại Tầng 3**)
- **Trạng thái hiện tại:** 🔵 **Partial (`tools/etabs_com_reader.py` v1 đã có; tách riêng vào lộ trình Tầng 3)**
- **Định hướng theo Chiến lược 3 Tầng:** Giao tiếp với ETABS 21 / SAP2000 22–25 / SAFE là nhiệm vụ chuyên biệt của **Tầng 3** nhằm trích xuất nội lực kiểm chứng ($M, N, V$, phản lực gối, chuyển vị) truyền qua JSON contract về Tầng 1, bảo đảm hoàn toàn không làm phình hay mất ổn định Tầng 1.

---

### TD-07: Đồng bộ Độ phủ Kiểm thử Tự động trên Toàn bộ Hệ sinh thái
- **Trạng thái hiện tại:** 🟢 **Resolved 100%** — Bộ kiểm thử `tests/run_all_tests.py --full` chạy **50/50 Test Suites** (`33` suite đăng ký tĩnh + `17` suite tự động đăng ký) và `tools/_collect_tests.py` đã đồng bộ thu thập đầy đủ toàn bộ `50` suites trên `122` Python scripts thuộc 14 skills.

---

### TD-08: Tầng 2C — Revit 2024 Read-Only Connector + IFC (IfcOpenShell) (🟡 Logged, chưa triển khai)
- **Bối cảnh:** Tầng 2B (AutoCAD 2021 Native DWG + Snapshot Diff D1/D1A) đã được Claude triển khai **độc lập (solo)** và cam kết: `tools/native_dwg_snapshot.py` (bản chụp chính tắc đơn vị chuẩn mm + fingerprint SHA-256), `tools/native_dwg_diff.py` (ghép **chỉ theo** `element_id`, không bao giờ tự ghép theo mark/hình học), `tools/autocad_snapshot_bridge.py` (worker 1 DWG/1 tiến trình, read-only, staging + SHA bất biến, `UNAVAILABLE` trung thực, `native_accept`), `tools/dce_snapshot_plugin.cs` (nguồn plugin .NET read-only `DCE_SNAPSHOT`, đọc `DCE_ELEMENT_ID` + regapp `DCE_BEAM`), bộ test `tests/test_tier2_phase2b_snapshot_diff.py` (17/17 PASS), 2 tool MCP `native_dwg_snapshot`/`native_dwg_diff`. **Nghiệm thu native đã chứng minh trên AutoCAD 2021 thật** (plugin build OK, snapshot read-only DWG thật `immutability_ok=true`).
- **Phạm vi nợ 2C (đúng theo `memory/audits/TIER2_PHASE2A_REVIEW_2B_2C_ARCHITECTURE.md` §3):**
  1. **Pilot 10 ngày trên BẢN SAO RVT 2024** (cấm file sản xuất, cấm bridge ghi): connector read-only qua **BIMwright `rvt-mcp v1.2.2`** là ứng viên đầu; benchmark dự phòng **Horizun v4.0.1** trên đúng cùng model + bộ đáp án; chỉ duyệt add-in C# Revit 2024 read-only nếu cả hai thiếu trường thiết yếu.
  2. **Canonical BIM snapshot + interface 6 hàm** (open readonly → list → batch elements → batch types → fingerprint → close); ghi document identity/build/transform/expected-returned counts. Nguyên tắc: `UniqueId ≠ IfcGlobalId ≠ element_id`; chỉ `element_id` đã duyệt là khóa xuyên CAD↔Revit.
  3. **IFC là kênh cross-check độc lập với thuật toán diff**: IfcOpenShell cài **version-pinned** trong môi trường cô lập; ghi hash IFC + schema + exporter + timestamp + unit assignments + placement + GlobalId mapping; IfcDiff chỉ là phép kiểm phụ, không coi GlobalId ổn định giữa các lần xuất.
  4. **5 ca acceptance 2C** (bài thi 2 dầm D1, B–C đổi 250×500→250×600 + đổi D1A, type dùng chung, tag sai, dầm chéo 3-4-5) + chứng minh read-only (danh sách tool/capability, quyền chỉ đọc trên bản sao, hash trước-sau + audit/log).
- **Tiêu chí đóng nợ (Debt Retirement):** có connector read-only + canonical schema + 5 ca acceptance PASS trên bản sao RVT 2024 thật (đã ẩn dữ liệu), IfcOpenShell pinned và IFC thực cross-check; `element_id` xuyên CAD↔Revit được audit; kỹ sư độc lập ký kết quả. Cấm mở rộng sang ghi Revit trong phase này.
- **Giới hạn trần nợ (Debt Ceiling):** TD-08 là nợ **Medium**, không làm vượt quá 2 nợ High. **Handoff 2B→2C:** điều kiện khởi động = "2B được nghiệm thu native (reopen/plot DWG trên AutoCAD 2021)" — **ĐÃ ĐẠT** (2026-11-23): plugin `DCE_SNAPSHOT` build OK, snapshot read-only DWG thật `immutability_ok=true`, `native_accept` PASS. 2C (nợ này) chờ tài nguyên: **RVT 2024 bản sao + IfcOpenShell version-pinned + thời gian pilot** (kỹ sư CAD/Revit cung cấp), không chặn vì 2B.

---

## 3. LỘ TRÌNH THỰC THI 3 TẦNG (TIERED EXECUTION PLAN)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1 — HOÀN THIỆN & KHÓA CỨNG (LOCKED 100% — 2026-11-22)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Pháp lý & Tiêu chuẩn: STANDARDS_LOCK v3.3.0 + StandardsGraph TCVN 2737 G1 │
│ • Đọc Bản vẽ & Phụ lục Thẩm tra (TVTT & CĐT): CAD_DEEP_READER + EMF + BIM   │
│ • Tính toán Cơ bản & Thuyết minh: 14 Production Skills (122 scripts)         │
│ • Kiểm thử & Điều phối: 50/50 Test Suites + Dispatcher 2D & Bus v3.4        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2 — MỞ RỘNG KỸ NĂNG VẼ (2D CAD & 3D REVIT/BIM PILOT)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ • 2D CAD: Kiểm định bản vẽ DWG/PDF qua AutoCAD 2021 accoreconsole & 25 cổng │
│ • 3D BIM: Cài ifcopenshell + pilot read-only BIMwright/Horizun trên RVT2024 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3 — KẾT HỢP ETABS / SAFE / SAP2000 LẤY NỘI LỰC KIỂM CHỨNG              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Chuẩn hóa Adapter lấy nội lực (Excel/.e2k/.s2k & COM OAPI ETABS21/SAP25)  │
│ • Bơm JSON nội lực về Tầng 1 kiểm tra ULS/SLS và xuất Phụ lục Thẩm tra      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. QUY TRÌNH QUẢN TRỊ NỢ KỸ THUẬT (GOVERNANCE POLICY)

1. **Nguyên tắc "Debt Ceiling" (Trần Nợ Kỹ thuật):**
   - Không được phép có quá 2 nợ kỹ thuật mức **High** tồn tại quá 2 Sprints.
   - Mọi nợ kỹ thuật mới phát sinh trong quá trình phát triển tính năng mới bắt buộc phải được ghi nhận vào tài liệu này trong vòng 24 giờ kể từ khi nghiệm thu tính năng.
2. **Review Gate & Tiêu chí Đóng Nợ (Debt Retirement Criteria):**
   - Một khoản nợ chỉ được chuyển trạng thái sang `🟢 Resolved` khi:
     + Mã nguồn đã được implement và có unit test tương ứng trong `run_all_tests.py`.
     + Đạt 100% PASS trong bộ kiểm tra hồi quy.
     + Tài liệu hướng dẫn sử dụng và changelog liên quan đã được cập nhật đồng bộ.

---

*Tài liệu được phê chuẩn bởi Hội đồng Kỹ thuật & Công nghệ Hệ thống `.agents`.*
