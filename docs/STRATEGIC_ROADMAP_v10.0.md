# MASTER STRATEGIC ROADMAP v10.0 — HỆ SINH THÁI AGENTIC .AGENTS
## LỘ TRÌNH CHIẾN LƯỢC TÁI CẤU TRÚC TOÀN DIỆN (CHẶNG 1 ĐẾN CHẶNG 4)
> **Phiên bản:** v10.0 Master Production  
> **Cập nhật ngày:** 2026-10-18  
> **Cơ sở kỹ thuật:** Kế thừa toàn bộ tài sản v9.2 (226/226 tests PASS) + Kho tri thức giải phẫu C:\Dce Pro (v4.0.0 IL Bytecode Opcode 0x72)  
> **Mục tiêu tối thượng:** Đưa hệ sinh thái .agents thành Hệ điều hành Kết cấu AI tự chủ 100%: Từ Prompt -> ETABS -> Tính toán TCVN -> Tối ưu cắt thép 11.7m -> Bản vẽ CAD/BIM -> Thuyết minh Word hoàn tất trong 45 giây.

---

## 1. TỔNG KIỂM KÊ TÀI SẢN KỸ THUẬT HIỆN HỮU (SYSTEM ASSET INVENTORY)

Hệ sinh thái hiện đã hoàn tất 4 trụ cột cốt lõi với độ tin cậy tuyệt đối (10/10 Suites PASS, 226/226 checks):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   HỆ SINH THÁI ĐIỀU PHỐI KẾT CẤU AI .AGENTS (v9.2)                      │
├──────────────────────────┬──────────────────────────┬──────────────────────────────────┤
│ TRỤ CỘT 1: LÕI ĐIỀU PHỐI │ TRỤ CỘT 2: 13 SKILLS     │ TRỤ CỘT 3: CÔNG CỤ TỰ CHỦ       │
│ • AGENTS.md + Hiến pháp   │ • 100 Calculators        │ • cad_bridge.py (DXF/AutoCAD)    │
│ • STANDARDS_LOCK (15 TCVN)│ • 38 Thiết kế BTCT/Thép  │ • rebar_cutting_optimizer (11.7m)│
│ • intent_classifier (417) │ • 30 Thẩm tra / CDC      │ • etabs_com_reader.py (OAPI 2-way│
│ • policy_engine (36 luật) │ • 24 Thuyết minh / BOQ   │ • ifc_parser.py (OpenBIM IFC)    │
│ • confidence_score (VETO) │ • 2 Skills Placeholder   │ • rebar_tokenizer.py (45k mẫu)   │
├──────────────────────────┴──────────────────────────┴──────────────────────────────────┤
│ TRỤ CỘT 4: KHO TRI THỨC GIẢI MÃ SÂU DCE PRO (REVERSE-ENGINEERING KNOWLEDGE BASE)       │
│ • dce_engineering_rules.json (1.239 file cấu hình, catalog I/U/V/P, bu lông M12..M36) │
│ • Form 2.dxf Template (46 layers DCE_*, 18 DimStyles, 44 Block hình dáng TK1..TK44)   │
│ • DCE_DEEP_OPERATION_SCHEMA.json v4.0.0 (5.244 chuỗi hằng số IL 0x72 từ 828 methods)  │
│ • Sơ đồ 7 bộ bảng tính Excel cốt lõi (Column Detail, Wall Detail, BanVe, SctCoc 10304) │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. RÀ SOÁT KHOẢNG TRỐNG (GAP ANALYSIS)

1. **4 Module Điều khiển DCE chưa thành file vật lý**:
   Mới tồn tại ở dạng mã mô tả mẫu trong `DCE_COMPLETE_INTERNAL_MECHANISM.md`, cần vật lý hóa thành 4 module độc lập trong `.agents/tools/`:
   `dce_xdata_bridge.py`, `dce_excel_bus.py`, `dce_option_controller.py`, `dce_cad_automation.py`.
2. **Sai lệch DxfCode tại Mục 3.2**:
   Bảng XData TypedValue Schema trước đây đánh số sai thành `1001..1013`, cần chuẩn hóa lại theo đặc tả kỹ thuật Autodesk DXF (`1001` RegApp, `1000` String, `1002` Control, `1005` Handle, `1040` Double, `1070` Int16, `1071` Int32).
3. **Phạm vi tự động vẽ của cad_bridge.py**:
   Hiện mới tự động vẽ Dầm BTCT + Bảng thống kê thép; cần mở rộng sang Cột, Vách, Đài cọc và Khung kết cấu thép.
4. **Nợ kỹ thuật TD-07 (100/100 Calculators Smoke Test) & Pipeline 1-Click**:
   Mới kiểm thử trực tiếp 23/100 calculators qua Suite 2 & 6; cần nâng lên 100/100 và đấu nối luồng End-to-End 1-Click.
5. **Nâng cấp Placeholder & Giải tích bậc cao**:
   Nâng cấp `SKILL_BIM_COORDINATION` và `Project_Manager` lên Production (v1.0.0); xây dựng $P-\Delta$, nền đàn hồi và Viewport Packing A3.

---

## 3. LỘ TRÌNH 4 GIAI ĐOẠN TÁI CẤU TRÚC CHIẾN LƯỢC (MASTER ROADMAP v10.0)

| Giai đoạn | Trọng tâm Chiến lược | Hạng mục Công việc | Đầu ra Nghiệm thu |
|---|---|---|---|
| **CHẶNG 1: Sprint 3.4** *(Ngay lập tức)* | **Hoàn tất Cầu nối Thực thi DCE & Chuẩn hóa XData/Excel Bus** | 1. Tạo 4 tools: `dce_xdata_bridge.py`, `dce_excel_bus.py`, `dce_option_controller.py`, `dce_cad_automation.py`<br>2. Sửa bảng DxfCode Mục 3.2 `DCE_COMPLETE_INTERNAL_MECHANISM.md`<br>3. Tạo Test Suite 11 (`test_dce_deep_integration.py`) | • 4 file .py chạy độc lập & COM<br>• File DXF kèm XData pass `ezdxf.audit()`<br>• **11/11 Test Suites ALL PASS** |
| **CHẶNG 2: Sprint 3.5** *(Ngắn hạn)* | **Mở rộng Đa Cấu Kiện cad_bridge, Pipeline 1-Click & Đóng nợ TD-07** | 1. Bổ sung vẽ Cột, Vách, Đài cọc, Liên kết thép vào `cad_bridge.py`<br>2. Xây dựng `tools/end_to_end_pipeline.py`<br>3. Mở rộng `test_runner.py` phủ đủ 100/100 calculators | • 1 Click: Thuyết minh .docx + Bản vẽ .dxf + Cắt thép 11.7m<br>• 100/100 calculators PASS kiểm thử |
| **CHẶNG 3: Sprint 4** *(Trung hạn)* | **Dàn trang Tự động A3, 13/13 Skills Production & Giải tích Nâng cao** | 1. Xây dựng `tools/viewport_auto_packer.py` (VPGroup::CalcMetaRect A3 368x297mm)<br>2. Nâng cấp `BIM_COORDINATION` & `Project_Manager` lên v1.0.0 Production<br>3. `calc_p_delta_effects.py` & `calc_raft_springs.py` (TD-04) + ContextStore (TD-01) | • DXF tự động sinh PaperSpace Layout A3 xếp gọn cấu kiện<br>• 13/13 Skills đạt Production<br>• Đóng dứt điểm TD-01, TD-03, TD-04 |
| **CHẶNG 4: Sprint 5 & 2027** *(Dài hạn)* | **Tự chủ Revit 3D Rebar, C# Micro-Adapter & Cloud Enterprise** | 1. Xây dựng `pyRevit/AgenticStructural.extension` dựng thép 3D trực tiếp trong Revit<br>2. Biên dịch `AgenticCAD.dll` (C# Micro-Adapter ~80KB)<br>3. Đóng gói FastAPI + Docker Multi-Tenant Backend | • Chu trình 1-Click Prompt $\rightarrow$ ETABS $\rightarrow$ Word $\rightarrow$ CAD A3 $\rightarrow$ Revit 3D $\le 45\text{s}$ |
