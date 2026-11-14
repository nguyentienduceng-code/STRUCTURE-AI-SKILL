# TÀI LIỆU KỸ THUẬT: DCE_MCP_CAD_Revit_Starter_Kit_v5.0 (DIGEST CHO CLAUDE / CODEX)

> **Mã hồ sơ:** DOC-DCE-MCP-V5-DIGEST  
> **Nguồn gốc tài liệu:** Thư mục vật lý `D:\DCE_MCP_CAD_Revit_Starter_Kit_v5.0`  
> **Mục đích:** Cung cấp toàn bộ đặc tả kỹ thuật, mã nguồn trích yếu và hướng dẫn tích hợp để Claude / Codex phân tích ứng dụng vào hệ sinh thái `.agents/`.

---

## 1. Cấu Trúc Tổng Thể Thư Mục Nguồn

Thư mục `D:\DCE_MCP_CAD_Revit_Starter_Kit_v5.0` gồm 5 module cốt lõi:

```text
D:\DCE_MCP_CAD_Revit_Starter_Kit_v5.0\
├── 01_Auto_Downloader_Installer/
│   └── Install-All-MCP-CAD-Revit.ps1         (7.9 KB — Script tự động kéo 6 repo MCP, cài đặt C# addin & Python deps)
├── 02_IDE_MCP_Configs/
│   ├── antigravity_mcp_config.json           (1.3 KB — File cấu hình mẫu cho Antigravity IDE / Claude Desktop / Cursor)
│   └── register_claude_codex_mcp.bat         (1.0 KB — Batch script 1-click đăng ký MCP server vào Claude CLI & Codex)
├── 03_DCE_RevitBridge_CSharp_Addin/
│   ├── DCE.RevitBridge.addin                 (XML manifest đăng ký plugin với Revit 2024-2026)
│   ├── DCE.RevitBridge.csproj                (Project file đa target: .NET 4.8 cho Revit 2024 & .NET 8.0 cho Revit 2025/2026)
│   └── DCERevitExternalApp.cs                (11.3 KB — Lõi C# bất đồng bộ Revit.Async + TCP Server cổng 8080)
├── 04_DCE_CAD_BIM_MCP_Server_Python/
│   ├── dce_cad_bim_mcp_server.py             (5.3 KB — Máy chủ MCP Server stdio JSON-RPC điều phối 6 Pinned Tools)
│   └── DCE_Structural_BIM_Audit.ids          (1.9 KB — Chuẩn kiểm toán BIM IFC4 buildingSMART IDS 1.0)
└── 05_Documentation/
    └── README_HUONG_DAN_CAI_DAT_TOAN_TAP.md  (2.8 KB — Hướng dẫn cài đặt và bảng tra cứu 6 bộ MCP tốt nhất)
```

---

## 2. Các Đoạn Mã Nguồn Hạt Nhân Cần Phân Tích

### A. Tầng Điều Phối MCP Server (`dce_cad_bim_mcp_server.py`)
Máy chủ MCP giao tiếp qua `stdio` (chuẩn Anthropic MCP), expose 6 Pinned Tools kết nối hệ thống CAD/BIM:
- `mcp:sync_etabs_to_ssot`: Đồng bộ nội lực/tiết diện ETABS sang `us_ssot_model.json`.
- `mcp:generate_dce_cad_drawings`: Gọi engine xuất bản vẽ AutoCAD `.dxf` chuẩn AC1021.
- `mcp:push_ssot_to_revit_bim`: Đẩy mô hình sang Revit (`live_tcp` cổng :8080 hoặc `headless_ifc` qua IfcOpenShell).
- `mcp:pull_revit_changes_to_ssot`: Trích xuất thay đổi từ Revit về JSON SSOT.
- `mcp:run_4way_bim_cad_audit`: Kiểm tra chéo 4 chiều CAD - Revit - ETABS - Thuyết minh.
- `mcp:publish_tmtt_and_clash_dossier`: Xuất Thuyết minh `.docx` và Hồ sơ khoanh lỗi A4.

**Thuật toán quy đổi tâm cột CAD $\rightarrow$ Revit Internal Feet:**
```python
def compute_column_revit_center(col: Dict[str, Any]) -> Dict[str, float]:
    """Quy đổi độ lệch tâm mép cột CAD (mm) sang tâm hình học Revit (Feet)."""
    x_g = float(col.get("grid_x_mm", 0.0))
    y_g = float(col.get("grid_y_mm", 0.0))
    B = float(col.get("B_mm", 1000.0))
    H = float(col.get("H_mm", 1000.0))
    a_left = float(col.get("a_left_mm", B / 2.0))
    b_bot = float(col.get("b_bot_mm", H / 2.0))

    # X_c = X_g + (B/2 - a_left) | Y_c = Y_g + (H/2 - b_bot)
    x_c_mm = x_g + (B / 2.0 - a_left)
    y_c_mm = y_g + (H / 2.0 - b_bot)
    return {
        "x_center_mm": round(x_c_mm, 1),
        "y_center_mm": round(y_c_mm, 1),
        "x_center_ft": round(x_c_mm / 304.8, 6),
        "y_center_ft": round(y_c_mm / 304.8, 6)
    }
```

---

### B. Tầng Revit Add-in Bất Đồng Bộ (`DCERevitExternalApp.cs`)
- **Vấn đề giải quyết:** Revit API là đơn luồng (Single-Threaded), không cho phép socket thread gọi trực tiếp API.
- **Giải pháp:** Sử dụng thư viện `Revit.Async` (`RevitTask.RunAsync`) nhận request từ socket cổng `8080` và xếp hàng vào Revit Main Thread Event Loop an toàn tuyệt đối.
- **Khóa định danh Extensible Storage:**
  ```csharp
  private static readonly Guid SSOT_SCHEMA_GUID = new Guid("A4E9C8B1-2D3F-4A5B-8C7E-9F0A1B2C3D4E");
  ```
  Gắn trực tiếp `SSOT_UUID` vào FamilyInstance trong Revit. Khi sync lại, chỉ cập nhật vị trí thay vì tạo mới, bảo toàn 100% kích thước và ghi chú của kỹ sư.
- **Hỗ trợ `dryRun`:** Có cờ `dryRun: true` $\rightarrow$ thực thi trong transaction rồi tự động `tx.RollBack()`, trả về số lượng cột `wouldCreateColumns` / `wouldUpdateColumns` phục vụ AI thẩm tra trước khi ghi thật.

---

### C. Tiêu Chuẩn Thẩm Tra BIM Quốc Tế (`DCE_Structural_BIM_Audit.ids`)
- Chuẩn buildingSMART IDS 1.0 (Information Delivery Specification) cho mô hình kết cấu IFC4:
  - Bắt buộc kiểm tra `IFCCOLUMN` có `Pset_ColumnCommon.LoadBearing = true`.
  - Bắt buộc kiểm tra `IFCWALL` có `Pset_WallCommon.LoadBearing = true`.
- Cho phép chạy thẩm tra tự động headless qua `ifctester` trên máy không cài đặt Autodesk Revit.

---

## 3. Bản Đồ Ghép Nối Với Hệ Sinh Thái `.agents/` Hiện Tại

| Module trong Starter Kit v5.0 | File hiện có trong `.agents/` | Nhiệm vụ ghép nối cần phân tích |
| :--- | :--- | :--- |
| `04_.../dce_cad_bim_mcp_server.py` | `.agents/tools/cad_plan_engine.py`<br>`.agents/tools/cad_edit_workbench.py` | Bọc làm MCP Server `mcp-dce-cad` theo đúng [RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md](file:///G:/My%20Drive/Google%20AI%20Studio/.agents/docs/RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md). Bổ sung tool `render_preview` (PNG 300 DPI). |
| `compute_column_revit_center` | `skills/Technical_Illustrator/cad_integration/cad_plan_engine.py` | Nhập logic căn tâm này vào block `TenCauKien` để chuẩn hóa tọa độ dầm/cột. |
| `03_.../DCERevitExternalApp.cs` | `skills/SKILL_BIM_COORDINATION` | Dùng làm cầu nối khi phát sinh yêu cầu dựng/sửa mô hình Revit 3D từ xa. |
| `04_.../DCE_Structural_BIM_Audit.ids` | `skills/SKILL_VERIFY` | Tích hợp vào Bộ lọc 8 làm chuẩn kiểm toán mô hình BIM IFC. |

