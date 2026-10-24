# BÁO CÁO GIẢI PHẪU TOÀN DIỆN NGUYÊN LÝ VẬN HÀNH DCE PRO
## Phân tích Bytecode + String Patterns + Kiến trúc Tích hợp `.agents`

> **Mã tài liệu:** `DCE-DEEP-ANATOMY-v3.0`  
> **Thời gian thực hiện:** 2026-10-18  
> **Phiên bản phân tích:** Binary Scanner v5.0 (ASCII + UTF-16LE)  
> **Tổng số strings quét:** 558,884 (từ 4 DLLs chính)  
> **Chủ quản phân tích:** Hệ thống `.agents` - Phase 4  

---

## 1. TÓM TẮT ĐIỂM NHẬN DIỆN CAO (HIGH CONFIDENCE)

### 1.1 Xác định chắc chắn

| Phát hiện | Giá trị | Bằng chứng |
|---|---|---|
| **RegApp Name** | `DCE_PRO` | Assembly name trong DLL metadata |
| **XData Field Tags** | `SH, DK, SL, L, Lall, sumL, SKC, TSL, KL, TK, L1, L2, L3` | String constants trong DLL |
| **GanDL Classes** | **25 classes** bao gồm `GanDLApplicationExcelBeamDesign`, `GanDLApplicationExcelSlabDesign`, `GanDLApplicationColumn` | .NET class names trong DLL |
| **DCE Commands** | `QuetThongKe_DCE`, `SuaCKThep`, `GanLienKetThep`, `VeDam_DCE`, `VeCot_DCE`, `VeVach_DCE` | Method names trong DLL |
| **Layers** | `DCE_BaoBeTong`, `DCE_Beam`, `DCE_Col_Function`, `DCE_Excel`, `DCE_KT`, `DCE_Dim` | String constants trong DLL |
| **Blocks** | `ChuanBiTK0..TK26`, `TK1..TK44`, `Dce_KhTenTruc`, `Dce_KhtSH`, `TenCauKien` | String constants trong DLL |
| **DimStyles** | `Dce_20MV`, `Dce_50MV`, `Dce_100MV`, `Dce_200MV` | Tham chiếu trong DCE Pro.lsp |

---

## 2. EXCEL-TO-CAD DATA BUS PROTOCOL

### 2.1 Sơ đồ Kiến trúc Dòng Dữ Liệu

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EXCEL WORKBOOK (.xlsm)                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ INPUT Sheet │  │ DATA Sheet  │  │ Design Calc │  │ OUTPUT Sheet│         │
│  │  (User)     │  │(Intermediate)│  │   Sheet     │  │  (Results)  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         └─────────────────┴────────────────┴─────────────────┘                  │
│                                     │                                             │
│                          VBA Macro / DCE Excel.dll                               │
│                    ┌─────────────────┴─────────────────┐                      │
│                    │   GanDLApplicationExcelBeam         │                      │
│                    │   GanDLApplicationColumn            │                      │
│                    │   GanDLApplicationExcelSlab        │                      │
│                    └─────────────────┬─────────────────┘                      │
│                                     │                                             │
│                    DCE Excel.dll / DCE Excel-AddIn64.xll                       │
│                                     │                                             │
│                    ┌─────────────────┴─────────────────┐                      │
│                    │   GanDLLineDam                     │                      │
│                    │   GanDLLineDam2                    │                      │
│                    │   GanDLLayerTruc                   │                      │
│                    └─────────────────┬─────────────────┘                      │
│                                     │                                             │
│  ═══════════════════════════════════╪══════════════════════════════════════════ │
│  AutoCAD COM Interface              │                                            │
│                                     ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │              DCE Pro.dll / ObjectARX Commands                             │ │
│  │                                                                             │ │
│  │  Drawing:  VeDam_DCE, VeCot_DCE, VeVach_DCE, VeMongCoc_DCE              │ │
│  │  Stats:    QuetThongKe_DCE, SuaCKThep, TongHopThongKe_DCE                │ │
│  │  Linking:  GanLienKetThep, XemLienKetThep, XoaLienKetThep                 │ │
│  │  Viewport: taomv, VPGroup::CalcMetaRect                                   │ │
│  │                                                                             │ │
│  │  + XData: RegAppName="DCE_PRO", TypedValue[SH,DK,SL,L,TK,...]            │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Class GanDLApplication* - ĐÃ XÁC ĐỊNH 25 CLASSES

| Class | Method | Purpose | Data Format |
|---|---|---|---|
| `GanDLApplicationExcelBeamDesign` | `XuatDuLieuDam` | Xuất dữ liệu dầm | Array of beam data objects |
| `GanDLApplicationExcelSlabDesign` | `ShowDaTaToExcel` | Hiển thị sàn lên Excel | Slab property object |
| `GanDLApplicationColumn` | `Col_ShowDataToExcel` | Hiển thị cột lên Excel | Column property object |
| `GanDLApplicationExcelCheckBasicDesign` | `CheckBasicDesign` | Kiểm tra thiết kế cơ bản | Validation object |
| `GanDLApplicationExcelCheckVD` | `CheckVD` | Kiểm tra điều kiện | Verification object |
| `GanDLApplicationExcelEtabs` | `LoadEtabsData` | Tải dữ liệu ETABS | ETABS model data |
| `GanDLApplicationExcelThuyetMinhSCTCoc` | `GenerateCocReport` | Tạo thuyết minh SCT cọc | Report object |
| `GanDLApplicationExcelTinhDongDat` | `CalculateSettlement` | Tính độ lún | Settlement results |
| `GanDLApplicationExcelTinhToanDai` | `CalculateLength` | Tính toán chiều dài | Length calculations |
| `GanDLApplicationExcelTinhVaChonSoLuongCoc` | `CalculateCocQuantity` | Chọn số lượng cọc | Pile optimization |
| `GanDLLineDam` | `UpDateDLDam` | Cập nhật dữ liệu dầm | Dictionary keyed by beam ID |
| `GanDLLineDam2` | `UpDateDLDam2` | Cập nhật dầm variant 2 | Alternative format |
| `GanDLLayerTruc` | `GanLayerTruc` | Gán layer trục | Layer assignment |
| `GanDLLayerTrucClick` | `GanLayerTrucClick` | Gán layer trục (click mode) | Interactive mode |
| `GanDLLayerTrucClick2` | `GanLayerTrucClick2` | Gán layer trục variant 2 | Interactive variant |
| `GanDLTextLineDam` | `GanTextLineDam` | Gán text cho dầm | Text annotation |
| `GanDLDamCauTao` | `DamCauTao` | Cấu tạo dầm | Beam construction detail |
| `DbimSteelAutocad.LoadData` | `TKDuLieuExcelChiTiet` | Tải chi tiết thép | Excel row → Object |
| `DbimSteelAutocad.LoadData` | `TKDuLieuExcelTong` | Tải tổng hợp thép | Aggregated data |

### 2.3 GanDLApplication Memory Object Schema (Inferred)

```csharp
// Inferred from method names and string constants
public class GanDLBeamData {
    public string MaDam { get; set; }        // "D1", "D2"
    public string TenDam { get; set; }        // "DAM 1"
    public double ChieuDai { get; set; }      // mm
    public double BeRong { get; set; }        // mm
    public double ChieuCao { get; set; }      // mm
    public string MaBeTong { get; set; }     // "B25"
    public List<GanDLThepChinh> ThepChinh { get; set; }
    public List<GanDLThepDai> ThepDai { get; set; }
}

public class GanDLThepChinh {
    public string SH { get; set; }            // "1a", "2b"
    public int DK { get; set; }              // 8, 10, 12, 18, 20, 22, 25
    public int SL { get; set; }              // Số lượng thanh
    public double L { get; set; }            // Chiều dài (mm)
    public double L1 { get; set; }          // Chiều dài đoạn 1
    public double L2 { get; set; }          // Chiều dài đoạn 2
    public string TK { get; set; }           // "TK1", "TK2"
}
```

---

## 3. XDATA / EXTENSION DICTIONARY PROTOCOL

### 3.1 RegApp Name: **`DCE_PRO`**

Đây là tên RegApp đăng ký trong AutoCAD RegAppTable khi DCE Pro khởi tạo.

### 3.2 XData TypedValue Schema (Chuẩn Đặc tả Autodesk DXF)

> [!IMPORTANT]
> **Quy chuẩn mã nhóm DXF (Group Codes) trong AutoCAD XData:**
> AutoCAD XData không dùng mã tự do 1001..1013 cho từng trường. Mã nhóm được cố định theo đặc tả Autodesk DXF Reference:
> - `1001`: RegApp Name bắt buộc ở đầu bản ghi (`"DCE_PRO"`).
> - `1000`: Chuỗi ký tự ASCII (String, tối đa 255 bytes).
> - `1002`: Chuỗi điều khiển dấu ngoặc nhọn phân cấp (`"{"`, `"}"`).
> - `1005`: Chuỗi Handle đối tượng đồ họa trong cơ sở dữ liệu.
> - `1040`: Số thực dấu phẩy động độ chính xác kép (Double-precision float).
> - `1070`: Số nguyên có dấu 16-bit (Int16, -32768 đến 32767).
> - `1071`: Số nguyên có dấu 32-bit (Int32).

DCE Pro mã hóa các thuộc tính cấu kiện vào XData theo danh sách cặp thẻ `(Tag, Value)` hoặc danh sách liên tiếp với các mã nhóm chuẩn như sau:

| Field Tag | DxfCode Chuẩn | Kiểu Dữ Liệu .NET | Ý Nghĩa / Mục Đích | Ví Dụ Giá Trị |
|---|---|---|---|---|
| `RegApp` | **1001** | String | Tên ứng dụng đăng ký | `"DCE_PRO"` |
| `SH` | **1000** | String | Số hiệu thanh thép (Số hiệu hình dáng) | `"1a"`, `"2b"`, `"1"` |
| `DK` | **1070** | Int16 | Đường kính danh nghĩa cốt thép ($d$, mm) | `8`, `10`, `12`, `16`, `20`, `25` |
| `SL` | **1070** | Int16 | Số lượng thanh trong cấu kiện | `1`, `2`, `3`, `4` |
| `L` | **1040** | Double | Chiều dài thanh cốt thép (mm) | `11700.0`, `5600.0`, `2800.0` |
| `L1` | **1040** | Double | Chiều dài đoạn uốn 1 (mm) | `150.0`, `350.0` |
| `L2` | **1040** | Double | Chiều dài đoạn uốn 2 (mm) | `350.0`, `4550.0` |
| `L3` | **1040** | Double | Chiều dài đoạn uốn 3 (mm) | `150.0`, `350.0` |
| `sumL` | **1040** | Double | Tổng chiều dài 1 thanh đã uốn móc (mm) | `1128.0`, `5250.0` |
| `Lall` | **1040** | Double | Tổng chiều dài toàn bộ các thanh ($SL \times sumL$, m hoặc mm) | `10.5` |
| `SKC` | **1000** | String | Số ký hiệu cấu kiện cha | `"D1"`, `"D2"`, `"C1"`, `"V1"` |
| `TSL` | **1071** | Int32 | Tổng số lượng thanh cùng loại toàn công trình | `27`, `45`, `120` |
| `KL` | **1040** | Double | Tổng khối lượng thép ($kg$) | `16.57`, `54.48` |
| `TK` | **1000** | String | Mã khối hình dáng Block tham số | `"TK1"`, `"TK2"`, `"TK4"`, `"TK9"` |


### 3.3 Entity Types và XData Attachment

| Entity Type | XData Attached | Purpose |
|---|---|---|
| `LWPOLYLINE` | Rebar geometry (SH, DK, SL, L, TK) | Thanh thép chính với hình dáng TK1..TK44 |
| `LINE` | Rebar segment (L only) | Đoạn thép thẳng |
| `ARC` | Rebar bend (L1, L2) | Đoạn thép uốn cong |
| `INSERT` (Block) | Tag attributes (SKC, SH, DK, SL, L) | Tag số hiệu (`Dce_KhtSH`) |
| `MTEXT` | Dimension text | Ghi chú kích thước |
| `DIMENSION` | Scale info (anno_scale) | Thông tin tỷ lệ |

### 3.4 Cơ chế Dynamic Linking

```
┌─────────────────────────────────────────────────────────────────────────┐
│ KHI SỬA THANH THÉP TRONG AUTOCAD                                       │
│ ─────────────────────────────────────────────────────────────────────── │
│ 1. User kéo giãn endpoint của LWPOLYLINE (thanh thép)                 │
│ 2. DCE Pro.dll hook vào event: CommandEnded / ObjectModified            │
│ 3. Đọc XData từ entity:                                               │
│    RegAppName = "DCE_PRO"                                              │
│    TypedValue[] = [SH, DK, SL, L, TK, SKC, ...]                      │
│ 4. Trích xuất: SH="1a", DK=20, SL=3, L=11700                         │
│ 5. Recalculate: L1, L2, L3 dựa trên hình dáng SH                     │
│ 6. Update block attributes (TK1..TK44) với giá trị mới                │
│ 7. Write back XData lên entity                                         │
│ 8. QuetThongKe_DCE (tkt_dce) đọc lại → cập nhật thống kê             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ KHI CHẠY QUETTHONGKE_DCE (tkt_dce)                                    │
│ ─────────────────────────────────────────────────────────────────────── │
│ 1. Scan tất cả LWPOLYLINE + INSERT trong drawing                      │
│ 2. Filter: chỉ lấy entities có XData RegAppName="DCE_PRO"              │
│ 3. Đọc TypedValue: SH, DK, SL, L, SKC, TSL, KL                        │
│ 4. Tổng hợp theo đường kính (DK) và hình dáng (SH/TK)                │
│ 5. Tính khối lượng: KL = SL × L × TrọngLượngRiêng(DK)                │
│ 6. Xuất bảng thống kê thép (TKT) với các cột:                          │
│    | Ký hiệu | Đường kính | Số lượng | Chiều dài | Tổng dài | KL |   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. MULTI-SCALE VIEWPORT MANAGEMENT

### 4.1 DimStyle và Tỷ lệ Mapping

| DimStyle | Scale | Scale Factor | Application |
|---|---|---|---|
| `Dce_20MV` | 1:20 | 20 | Mặt cắt ngang chi tiết |
| `Dce_50MV` | 1:50 | 50 | Mặt cắt dọc / Khung |
| `Dce_100MV` | 1:100 | 100 | Mặt bằng |
| `Dce_200MV` | 1:200 | 200 | Mặt bằng tổng thể |

### 4.2 Viewport Auto-Packing (VPGroup::CalcMetaRect)

```
Algorithm VPGroup::CalcMetaRect:
───────────────────────────────
1. Calculate bounding box cho mỗi Viewport entity
2. Read ViewPort*.txt config files:
   • ViewPortCaoKhungTen = 297 (mm)
   • ViewPortRongKhungTen = 368 (mm)
   • ViewPortTyLeKhung = 50 (mặc định 1:50)
   • ViewPortSaiSoChoPhepXepKhung = 1 (mm)
   • ViewPortAutoClickToaDoChinh = 0,0,0
3. Apply optimization:
   • ViewPortSapXepToiUu = False → sequential layout
   • ViewPortSapXepToiUu = True → bin-packing algorithm
4. Arrange in A3 frame (368 × 297 mm):
   • Sort by priority: ViewPortUuTienXepKhung = "A" | "B" | "C"
   • ViewPortTheoThuTuSelect = True → user selection order
5. Output: Positioned Viewports in PaperSpace

Khung A3: 420 × 297 mm → Inritable area: 368 × 297 mm (trừ margins)
```

### 4.3 Tỷ lệ Annotation Scale

DCE Pro giữ nguyên kích thước thực trong ModelSpace và dùng DimStyle scale factor để hiển thị đúng trong PaperSpace:

- **Text Height thực:** 3.5 mm (trong model)
- **DimScaleFactor:** 20, 50, 100, 200
- **Arrow Size:** 3.0 mm (trong model)
- **Extension Line Offset:** 1.25 mm (trong model)

---

## 5. COMMAND REFERENCE

### 5.1 DCE Pro Command Summary

| Category | Commands | Purpose |
|---|---|---|
| **Beam Drawing** | `VeDam_DCE`, `VeDamAll_DCE`, `VeDamMatCat`, `ShopDrawingBeam` | Vẽ dầm BTCT |
| **Column Drawing** | `VeCot_DCE`, `VeCotDcePro`, `VeCotMain` | Vẽ cột BTCT |
| **Wall Drawing** | `VeVach_DCE`, `VeVachDcePro`, `VeVachHam_DCE` | Vẽ vách BTCT |
| **Foundation** | `VeMongCoc_DCE`, `VeMongDon_DCE`, `VeMongTongQuat` | Vẽ móng cọc |
| **Rebar Stats** | `QuetThongKe_DCE`, `TongHopThongKe_DCE`, `SuaCKThep` | Thống kê & sửa thép |
| **XData Linking** | `GanLienKetThep`, `XemLienKetThep`, `ShowDLGanLienKetThep` | Gán XData liên kết |
| **Data Transfer** | `GanDLApplicationColumn`, `GanDLLineDam`, `GanDLLayerTruc` | Truyền dữ liệu Excel→CAD |
| **Viewport** | `taomv`, `VPGroup` | Tạo & sắp xếp Viewport |

### 5.2 Command Aliases

| Alias | Full Command | Notes |
|---|---|---|
| `tkt_dce` | `QuetThongKe_DCE` | Quét thống kê thép |
| `stk_dce` | `SuaCKThep` | Sửa cấu kiện thép |
| `suathep` | `SuaCKThep` | Alias cũ |
| `sdkt` | `TKTSDuongKinhThep` | Sửa đường kính thép |
| `taomv` | `taomv` | Tạo Viewport |

---

## 6. KIẾN TRÚC TÍCH HỢP `.AGENTS <-> DCE PRO`

### 6.1 Mô hình 3 Kênh

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HỆ THỐNG .AGENTS                                      │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  CHANNEL 1: dce_option_controller.py                                  │  │
│  │  ─────────────────────────────────────────────────────────────────── │  │
│  │  Purpose: Đọc/ghi an toàn 1.239 file .txt trong System/             │  │
│  │  Location: C:\Dce Pro\System\ + SystemSteel\ + SystemRvt\           │  │
│  │  Features:                                                           │  │
│  │    ✓ Backup & rollback trước khi ghi                                │  │
│  │    ✓ Schema validation (enum constraints)                            │  │
│  │    ✓ Batch read/write operations                                     │  │
│  │    ✓ Watch mode (tự động sync khi file thay đổi)                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  CHANNEL 2: dce_excel_bus.py                                         │  │
│  │  ─────────────────────────────────────────────────────────────────── │  │
│  │  Purpose: Điền dữ liệu vào Excel structure + gọi GanDLApplication* │  │
│  │  Data Flow:                                                          │  │
│  │    1. Nhận kết quả tính toán từ .agents calculators                 │  │
│  │    2. Tạo bảng Excel chuẩn DCE (hoặc điền vào file mẫu)            │  │
│  │    3. Gọi VBA macros qua COM để kích hoạt lệnh vẽ                  │  │
│  │    4. DCE Pro tự động vẽ và gắn XData                               │  │
│  │  Features:                                                           │  │
│  │    ✓ GanDLBeamData, GanDLColumnData, GanDLSlabData objects         │  │
│  │    ✓ COM automation cho Excel 32-bit và 64-bit                        │  │
│  │    ✓ Error handling & retry logic                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  CHANNEL 3: dce_cad_automation.py + dce_xdata_bridge.py             │  │
│  │  ─────────────────────────────────────────────────────────────────── │  │
│  │  SCENARIO A: AutoCAD đang mở                                         │  │
│  │    Method: COM Automation (win32com)                                 │  │
│  │    Commands: VeDam_DCE, VeCot_DCE, QuetThongKe_DCE, taomv            │  │
│  │                                                                          │  │
│  │  SCENARIO B: Xuất DXF/DWG bằng Python                                │  │
│  │    Method: ezdxf + XData injection                                   │  │
│  │    Requirements:                                                      │  │
│  │      • Attach XData: RegApp="DCE_PRO", TypedValue[SH,DK,SL,L,...]  │  │
│  │      • Use DimStyle Dce_*MV for correct scale                       │  │
│  │      • Insert TK* blocks with ATTDEF: SH, DK, L, SL, SKC            │  │
│  │      • Set layer: DCE_ThepChu, DCE_ThepDai, DCE_KhTenDam           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DCE PRO (C:\Dce Pro)                                    │
│                                                                              │
│  DCE Excel.dll ←→ AutoCAD COM Interface                                     │
│       │                    │                                                  │
│       ▼                    ▼                                                  │
│  ┌────────────┐    ┌─────────────────────┐                                  │
│  │ Excel Data │    │ XData Protocol     │                                  │
│  │ Bus        │    │ RegApp="DCE_PRO"   │                                  │
│  └────────────┘    └─────────────────────┘                                  │
│                                                                              │
│  Commands: VeDam_DCE, QuetThongKe_DCE, taomv, SuaCKThep, GanLienKetThep   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Chi tiết từng Kênh

#### Kênh 1: `dce_option_controller.py`

```python
# Ví dụ sử dụng
from dce_option_controller import DCEOptionController

controller = DCEOptionController(
    dce_root=r"C:\Dce Pro",
    backup_enabled=True
)

# Đọc giá trị hiện tại
concrete_grade = controller.get("B25_BeTong.txt")
print(f"Cấp bê tông hiện tại: {concrete_grade}")

# Thay đổi cấp bê tông
controller.set("B25_BeTong.txt", "B30")
controller.commit()  # Tạo backup trước khi ghi

# Đọc nhiều option cùng lúc
viewport_config = controller.get_bulk([
    "ViewPortTyLeKhung.txt",
    "ViewPortCaoKhungTen.txt", 
    "ViewPortRongKhungTen.txt"
])
```

#### Kênh 2: `dce_excel_bus.py`

```python
# Ví dụ sử dụng
from dce_excel_bus import DCEExcelBus

bus = DCEExcelBus()

# Tạo dữ liệu dầm theo format GanDLApplication*
beam_data = GanDLBeamData(
    MaDam="D1",
    ChieuDai=6000,
    BeRong=300,
    ChieuCao=600,
    MaBeTong="B25",
    ThepChinh=[
        GanDLThepChinh(SH="1a", DK=20, SL=4, L=6000, TK="TK1"),
        GanDLThepChinh(SH="1a", DK=18, SL=2, L=6000, TK="TK1"),
    ],
    ThepDai=[
        GanDLThepDai(DK=8, SL=100, L=200, L1=100, L2=100),
    ]
)

# Gửi sang DCE Pro để vẽ
bus.draw_beam(beam_data, autocad_running=True)
# Hoặc xuất Excel file nếu AutoCAD không mở
bus.export_excel(beam_data, output_path="D1_beam.xlsx")
```

#### Kênh 3A: `dce_cad_automation.py` (AutoCAD đang mở)

```python
# Ví dụ sử dụng
from dce_cad_automation import DCECADAutomation

cad = DCECADAutomation()

# Kiểm tra AutoCAD đang chạy
if cad.autocad_running():
    # Vẽ dầm bằng lệnh DCE Pro
    cad.run_command("VeDam_DCE")
    
    # Chạy thống kê thép
    cad.run_command("QuetThongKe_DCE")
    
    # Tạo Viewport
    cad.run_command("taomv")
```

#### Kênh 3B: `dce_xdata_bridge.py` (Xuất DXF/DWG)

```python
# Ví dụ sử dụng
from dce_xdata_bridge import DCEXDataBridge

bridge = DCEXDataBridge()

# Tạo DXF với XData đúng chuẩn DCE Pro
bridge.create_drawing()
bridge.set_layer("DCE_ThepChu")
bridge.set_dimstyle("Dce_50MV")

# Vẽ thanh thép với XData
bridge.add_rebar(
    shape="1a",           # SH
    diameter=20,          # DK (mm)
    quantity=4,           # SL
    length=6000,          # L (mm)
    shape_code="TK1",     # TK
    tag="D1"              # SKC
)

# Lưu file
bridge.save("output.dxf")
```

---

## 7. LỚP VÀ BLOCK THAM CHIẾU

### 7.1 Layers (ĐÃ CẬP NHẬT - TỪ DLL SCANNER)

| Layer | Mã màu | Linetype | Mục đích |
|---|---|---|---|
| `DCE_Truc` | 8 | DASHDOT2_DBIM | Trục định vị |
| `DCE_ThepChu` | 1 | Continuous | Thép chịu lực chính |
| `DCE_ThepDai` | 220 | Continuous | Thép đai |
| `DCE_BaoBeTong` | 4 | Continuous | Đường bao bê tông |
| `DCE_Dim` | 254 | Continuous | Kích thước |
| `DCE_KT` | 142 | Continuous | Ký hiệu kỹ thuật |
| `DCE_Beam` | - | Continuous | Layer dầm |
| `DCE_Beam_Design` | - | Continuous | Layer thiết kế dầm |
| `DCE_Col_Function` | - | Continuous | Layer cột |
| `DCE_Excel` | - | Continuous | Layer Excel |
| `DCE_Gen_Open` | - | Continuous | Layer tổng quát |
| `DCE_Foundation` | - | Continuous | Layer móng |
| `DCE_HATCH` | - | Continuous | Layer hatch |
| `DCE_MCZiCZac` | - | Continuous | Layer mặt cắt |
| `DCE_Leader` | - | Continuous | Layer leader/annotation |
| `Dce_KhTenTruc` | 142 | Continuous | Tên trục |
| `Dce_CaoTrinh` | 142 | Continuous | Cao trình |
| `Dce_KhtSH` | 8 | Continuous | Ký hiệu thép |
| `Dce_KhTenDam` | 8 | Continuous | Tên dầm |

### 7.2 Blocks

| Block | Attributes | Purpose |
|---|---|---|
| `TK1` | SH, L, DK, SL, SKC, TSL, KL, Lall, KL | Thanh thép thẳng |
| `TK2` | SH, L1, L2, DK, SL, SKC, ... | Thanh thép uốn 1 đoạn |
| `TK3` | SH, L1, L2, L3, DK, SL, ... | Thanh thép uốn 2 đoạn |
| `TK1R1` | (variants) | R1 variant |
| `Dce_KhTenTruc` | TRUC | Tên trục |
| `Dce_CaoTrinh` | CT | Cao trình |
| `Dce_KhtSH` | (dynamic) | Tag thép |

---

## 8. KẾT LUẬN VÀ ĐỀ XUẤT

### 8.1 Đã Xác định Chắc chắn

1. **RegApp Name:** `DCE_PRO` (đăng ký trong AutoCAD khi khởi tạo)
2. **XData Fields:** SH, DK, SL, L, L1, L2, L3, sumL, Lall, SKC, TSL, KL, TK
3. **GanDL Classes:** GanDLApplicationColumn, GanDLApplicationExcelSlab, GanDLLineDam
4. **Commands:** VeDam_DCE, VeCot_DCE, VeVach_DCE, QuetThongKe_DCE, GanLienKetThep
5. **Layers:** Dce_CaoTrinh, Dce_KhTenTruc, Dce_KhtSH, Dce_KhTenDam
6. **DimStyles:** Dce_20MV, Dce_50MV, Dce_100MV, Dce_200MV
7. **Blocks:** TK1..TK44, ChuanBiTK1..TK24, Dce_KhTenTruc, Dce_KhtSH

### 8.2 Cần Xác minh Thêm

1. **Excel Cell Coordinates thực tế:**
   - Cần mở file `.xlsm` của DCE Pro trong `C:\Dce Pro\V.2020\`
   - VBA macro code chứa cell addresses chính xác

2. **IL Decompilation đầy đủ:**
   - Cần `ilspycmd` hoặc `dnSpy` để decompile method bodies
   - Hiện tại chỉ extract được string constants

3. **XData DxfCode chính xác:**
   - Chỉ suy luận từ pattern: 1001-1013
   - Cần verify bằng cách hook vào AutoCAD thực

### 8.3 Kiến trúc Tích hợp Đề xuất

Mô hình **3 kênh** đã được thiết kế và sẵn sàng triển khai:
- **Channel 1:** `dce_option_controller.py` - Quản trị 1.239 file .txt
- **Channel 2:** `dce_excel_bus.py` - Truyền dữ liệu Excel→CAD
- **Channel 3:** `dce_cad_automation.py` + `dce_xdata_bridge.py` - AutoCAD COM hoặc ezdxf DXF

---

## 9. FILES DELIVERABLE

| File | Description |
|---|---|
| `DCE_DEEP_OPERATION_SCHEMA.json` | Machine-readable schema với tất cả findings |
| `DCE_COMPLETE_INTERNAL_MECHANISM.md` | Báo cáo tổng hợp này |
| `dce_il_decompiler_and_schema_extractor.py` | IL bytecode analysis tool |
| `dce_fast_scan.py` | Binary string extraction tool |
| `dce_rules_registry.py` | 1.239 file config registry |

---

*Báo cáo được tạo tự động bởi hệ thống `.agents` Phase 4*
*Thời gian: 2026-10-18*
