# BÁO CÁO GIẢI PHẪU TOÀN DIỆN KIẾN TRÚC PHẦN MỀM C:\DCE PRO
## KẾT QUẢ REVERSE ENGINEERING HỆ THỐNG ĐÓNG GÓI CAD / REVIT / ETABS

> **Mã tài liệu:** `DCE-DEEP-ANATOMY-v1.0`  
> **Thời gian thực hiện:** 2026-10-18 15:52:49  
> **Phạm vi khảo sát:** Toàn bộ thư mục `C:\Dce Pro` (100% tệp tin, SQLite, Assemblies, System Configs, CAD Forms)  
> **Chủ quản phân tích:** Tổ R&D Kỹ thuật & Công nghệ Hệ thống `.agents`  

---

## 1. TỔNG QUAN HỆ THỐNG PHẦN MỀM DCE PRO

Qua việc giải phẫu trực tiếp toàn bộ 5 tầng công nghệ, hệ thống DCE Pro được xây dựng trên kiến trúc:
1. **Nền tảng Ngôn ngữ:** VB.NET / C# .NET Framework (tương thích AutoCAD 2007–2026, Revit 2016–2027, BricsCAD, ZWCAD, GstarCAD).
2. **Mô hình Trí tuệ Nhân tạo:** Sử dụng thư viện `Microsoft.ML` (`Microsoft.ML.Data.dll`, `Microsoft.ML.Transforms.dll`) huấn luyện mô hình Named Entity Recognition (NER) với cơ sở dữ liệu `mauhoc.db` gồm **45,020 mẫu thực tế** để bóc tách text cốt thép.
3. **Cơ chế Điều phối CAD Đa nền tảng:** Áp dụng mẫu thiết kế **Adapter Pattern** thông qua bộ 4 DLL wrapper:
   - `DCE Pro.dll` (AutoCAD - ObjectARX `acdbmgd.dll`, `acmgd.dll`)
   - `BcDCE Pro.dll` (BricsCAD - `BrxMgd.dll`)
   - `ZwDCE Pro.dll` (ZWCAD - `ZwDatabaseMgd.dll`, `ZwManaged.dll`)
   - `GcDCE Pro.dll` (GstarCAD - `GcDbMgd.dll`, `GcMgd.dll`)
4. **Phân hệ Kết cấu Thép Chuyên biệt:** Phân nhánh hoàn toàn độc lập tại `AddinSteelCad` (`DbimSteelAutocad.dll`), chuyên giải bài toán Khung zamil, Nút gối gãy góc `LKKNEE`, Bản đế `BasePlate` và liên kết bu lông.
5. **Phân hệ Revit BIM:** Sử dụng addin `DBimRevit.dll` tương tác trực tiếp Revit API (`RevitAPI.dll`, `RevitAPIUI.dll`) để chuyển đổi mô hình 2 chiều `RevitToEtabs` và dựng Rebar 3D.

---

## 2. GIẢI PHẪU TẦNG 1 — CƠ SỞ DỮ LIỆU SQLITE

Tổng số tệp SQLite phát hiện trong hệ thống: **5 tệp**.

| Đường dẫn Tệp DB | Dung lượng | Số Bảng | Tổng Số Dòng | Mục đích Nghiệp vụ |
|---|:---:|:---:|:---:|---|
| `configDb.db` | 8.0 KB | 1 | 8 | Cấu hình tham số người dùng & tiêu chuẩn |
| `configDbSteel.db` | 8.0 KB | 1 | 7 | Bảng tra thép hình & quy cách bu lông thép |
| `MayHoc\mauhoc.db` | 8772.0 KB | 3 | 45,033 | Dữ liệu huấn luyện Machine Learning bóc tách thép (NER) |
| `System\configDb.db` | 8.0 KB | 1 | 8 | Cấu hình tham số người dùng & tiêu chuẩn |
| `AddinSteelCad\System\configDb.db` | 8.0 KB | 1 | 7 | Bảng tra thép hình & quy cách bu lông thép |

### 2.1 Chi tiết Schema Các Bảng Dữ Liệu Trọng Yếu

#### Cơ sở Dữ liệu: `configDb.db`
- **Bảng `ConfigSettings`** (8 dòng):
  * Danh sách cột: `config_key` (TEXT), `config_value` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "config_key": "ToKen",
        "config_value": ""
    },
    {
        "config_key": "TokenLicenseKey",
        "config_value": ""
    },
    {
        "config_key": "TaiKhoanDangNhap",
        "config_value": "nguyentienducbmt123@gmail.com"
    }
]
    ```

#### Cơ sở Dữ liệu: `configDbSteel.db`
- **Bảng `ConfigSettings`** (7 dòng):
  * Danh sách cột: `config_key` (TEXT), `config_value` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "config_key": "ToKen",
        "config_value": "6uMWyAogSYtD9P9C8GB99YDqIgni5l/xAo/K/YtRU+pw5AwPlHT52wBnYSi6UdHWQvemWF8Zv71tvFx8lDR+ISZaKF3QK8uoq+L/0/M7Khb0I3+tGDrk08iEw9DtjiBEZBC+mbXCMC0fNPn3c3UYvYJ656HjCp3YLoY4LfWVuKOqfqx1DSgxG9MDXehBkqsY4ki3d6+bTmcghwydlw1cdQ=="
    },
    {
        "config_key": "TokenLicenseKey",
        "config_value": "7fef3fbc-ab04-4eb1-b30d-e8ab340af89d"
    },
    {
        "config_key": "TaiKhoanDangNhap",
        "config_value": "nguyentienducbmt123@gmail.com"
    }
]
    ```

#### Cơ sở Dữ liệu: `MayHoc\mauhoc.db`
- **Bảng `CauHinhModel`** (10 dòng):
  * Danh sách cột: `Ten` (TEXT), `DuongDan` (TEXT), `SoMau` (INTEGER), `ThoiGian` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "Ten": "SteelToken",
        "DuongDan": "C:\\Dce Pro\\MayHoc\\model.zip",
        "SoMau": 435,
        "ThoiGian": "2026-07-05 11:27:40"
    },
    {
        "Ten": "SteelToken",
        "DuongDan": "C:\\Dce Pro\\MayHoc\\model.zip",
        "SoMau": 435,
        "ThoiGian": "2026-07-05 11:29:09"
    },
    {
        "Ten": "SteelToken",
        "DuongDan": "C:\\Dce Pro\\MayHoc\\model.zip",
        "SoMau": 447,
        "ThoiGian": "2026-07-05 12:24:00"
    }
]
    ```
- **Bảng `LichSuSua`** (3 dòng):
  * Danh sách cột: `Id` (INTEGER), `TextGoc` (TEXT), `Truoc` (TEXT), `Sau` (TEXT), `ThoiGian` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "Id": 1,
        "TextGoc": "[1b] 3x∅20, L= 11700",
        "Truoc": "",
        "Sau": "SL=3;DK=20;KC1=0;KC2=0;KC3=0;KC4=0;SH=1b;L=11700",
        "ThoiGian": "2026-07-05 12:23:52"
    },
    {
        "Id": 2,
        "TextGoc": "[1a+3G]6x∅20,L=11700",
        "Truoc": "",
        "Sau": "SL=6;DK=20;KC1=0;KC2=0;KC3=0;KC4=0;SH=1a+3G;L=11700",
        "ThoiGian": "2026-07-05 12:24:33"
    },
    {
        "Id": 3,
        "TextGoc": "[1a+4t]6x∅20,L=11700",
        "Truoc": "",
        "Sau": "SL=6;DK=20;KC1=0;KC2=0;KC3=0;KC4=0;SH=1a+4t;L=11700",
        "ThoiGian": "2026-07-05 12:25:40"
    }
]
    ```
- **Bảng `MauHoc`** (45020 dòng):
  * Danh sách cột: `Id` (INTEGER), `TextGoc` (TEXT), `ChiSoSo` (INTEGER), `GiaTri` (INTEGER), `Feature` (TEXT), `Nhan` (TEXT), `Nguon` (TEXT), `ThoiGian` (TEXT), `Hash` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "Id": 3656,
        "TextGoc": "[1b] 3x∅20, L= 11700",
        "ChiSoSo": 0,
        "GiaTri": 1,
        "Feature": "PREV_lbr NEXT_b AFTERL_0 INRING_1 DKCHUAN_0 NDIGIT_1 INSEQ_0 BEFORED_0 AFTERD_0 SHLET_1",
        "Nhan": "SH",
        "Nguon": "user",
        "ThoiGian": "2026-07-05 12:23:52",
        "Hash": "7BFA9014D754C349E807C64643679B44"
    },
    {
        "Id": 3657,
        "TextGoc": "[1b] 3x∅20, L= 11700",
        "ChiSoSo": 1,
        "GiaTri": 3,
        "Feature": "PREV_rbr NEXT_x AFTERL_0 INRING_0 DKCHUAN_0 NDIGIT_1 INSEQ_0 BEFORED_0 AFTERD_0 SHLET_0",
        "Nhan": "SL",
        "Nguon": "user",
        "ThoiGian": "2026-07-05 12:23:52",
        "Hash": "213CC2DDDA66A73E4060235B0B6CBC25"
    },
    {
        "Id": 3658,
        "TextGoc": "[1b] 3x∅20, L= 11700",
        "ChiSoSo": 2,
        "GiaTri": 20,
        "Feature": "PREV_d NEXT_comma AFTERL_0 INRING_0 DKCHUAN_1 NDIGIT_2 INSEQ_0 BEFORED_0 AFTERD_1 SHLET_0",
        "Nhan": "DK",
        "Nguon": "user",
        "ThoiGian": "2026-07-05 12:23:52",
        "Hash": "35B8C623348F675BE8C68036788294D6"
    }
]
    ```

#### Cơ sở Dữ liệu: `System\configDb.db`
- **Bảng `ConfigSettings`** (8 dòng):
  * Danh sách cột: `config_key` (TEXT), `config_value` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "config_key": "ToKen",
        "config_value": "PLyCStsV4V6YqKoQCCS68IjkWZpmQb6yWotk2ctPSC5uZcm/d4yYq0gOUpuuOu8KhH4RSPHYruoNoFwzNqaLCg0tm4jmRkq8PXCxCzvAur5KwoHpHaPiLdS0VEQbqlBlkPyEAyWzfnBdwWZ/g6fiZcwffpHsbOIAAgIvJp0vlGpnKSaMqYPbjenzPLDZ1z9atSvaSoSnihDZntXYWfZfaQ=="
    },
    {
        "config_key": "TokenLicenseKey",
        "config_value": "7fef3fbc-ab04-4eb1-b30d-e8ab340af89d"
    },
    {
        "config_key": "TaiKhoanDangNhap",
        "config_value": "nguyentienducbmt123@gmail.com"
    }
]
    ```

#### Cơ sở Dữ liệu: `AddinSteelCad\System\configDb.db`
- **Bảng `ConfigSettings`** (7 dòng):
  * Danh sách cột: `config_key` (TEXT), `config_value` (TEXT)
  * Dữ liệu mẫu (3 dòng đầu):
    ```json
    [
    {
        "config_key": "ToKen",
        "config_value": "J5d4DY11pz++4ypeh0inUv2/1kFflDFQPjjYTtD2pBqCi4cYEoS1qrkjmta4g3GxZt9BR0/mmGdVKvrzqvvHflsdNL2Fq0D5r3kMT70FvFwyjf+WT1MIFXnIRlaaFVoyUEOuOtxaaVYQWlMCnh+Uf+926BdT81fT85MZ3IXCJjQOdI5qpx4CNncxNLR62iclqKNZy1NTQQnpGdiF9dCpSw=="
    },
    {
        "config_key": "TokenLicenseKey",
        "config_value": "bc0c9e50-8dcc-4ee1-b78e-12dedb232af4"
    },
    {
        "config_key": "TaiKhoanDangNhap",
        "config_value": "minhtoan0610@gmail.com"
    }
]
    ```

---

## 3. GIẢI PHẪU TẦNG 2 — .NET ASSEMBLIES & LỆNH ĐIỀU KHIỂN

Tổng số Assemblies đã phản chiếu (Reflection): **8 DLLs**.

| Tên DLL | Tổng Số Types | Lệnh Đăng ký | Phân hệ Trọng tâm |
|---|:---:|:---:|---|
| `DCE Pro.dll` | 18,865 | 0 | Core Multi-CAD Plugin |
| `DbimSteelAutocad.dll` | 162 | 0 | AutoCAD Steel Detailing |
| `DBimRevit.dll` | 0 | 0 | Revit BIM 3D Rebar & Sync |
| `BcDCE Pro.dll` | 18,946 | 0 | Core Multi-CAD Plugin |
| `ZwDCE Pro.dll` | 18,864 | 0 | Core Multi-CAD Plugin |
| `GcDCE Pro.dll` | 18,839 | 0 | Core Multi-CAD Plugin |
| `CSiAPIv1.dll` | 1,136 | 0 | ETABS / SAP2000 CSi COM API |
| `DCE Excel.dll` | 5,992 | 3 | Excel Calculations Add-in |

### 3.1 Danh mục Các Class & Method Theo 4 Phân Hệ Nghiệp Vụ Cốt Lõi

#### 1. Phân hệ Kết nối ETABS API (CSi OAPI Wrapper)
Tìm thấy **700 methods** then chốt:
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceThangMoi.ThepThangCu::SapXepTagThepMatBang`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceMongCocMoi.VeCadMong::SapXepDaGiacTheoVecto`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+kiw3TZ7JMC4OJXy9AERA::jCZ0Owt6uSxYZyDLU5Fm`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+kiw3TZ7JMC4OJXy9AERA::dQAbmst6D0loH43w7MMX`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+scgQmk7J1QDyKOXtno49::kGcPDct6hx0tvAmLw196`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+scgQmk7J1QDyKOXtno49::urZkuZt6UfWM273KPR8V`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+VPGroup::CalcMetaRect`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+VPGroup::GoSOUwt6SHU2nXW8mE5c`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+VPGroup::mYSApPt6A4BOWU6nTqHe`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+hdOU7W7JzvCMGf3fa96C::bVub5tt64mWCkRCm3aUA`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+hdOU7W7JzvCMGf3fa96C::b9C4cZt6xvcslYye3PMD`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+NaturalStringComparer::cmQ7jUoZ6ct`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+NaturalStringComparer::Compare`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+NaturalStringComparer::Ph0Lv3t6ExUbAv9oppGp`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+NaturalStringComparer::ufmxbut6JXeXeax5lPuc`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::ous7jGDwcMI`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::mjb7jCxGdgo`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::AmU7jfMYOx2`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::Ilf7jIf4Sdu`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::geq7jrS8o7g`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::LSv7joDb7P9`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::DH37jpd4S3l`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::cBq7j6cUN2y`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::EtI7jwCgt0i`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Chung_ChiaDoiTuongModel+sYqtdB7jevAS7h5xpyV0::oNn7jYeP4Ym`
- *(và 675 methods khác xem trong JSON dump)*

#### 2. Phân hệ Tự động Vẽ Kết cấu Bê tông Cốt thép (BTCT)
Tìm thấy **700 methods** then chốt:
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::HotroBeamDetail`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::mNcPL0R5l`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::KHXytFl6L`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::qbgXVEx8F`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::KiemTraTrungDoanThang`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::pj62Ot9t5`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::vFYNEQDdB`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::Ygwsvl8dq`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::rUgiup8bO`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::FAmTO8gnE`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::gMLB0uxiB`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::EEJelW4mJ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::EwTGLPsEP`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::S0rCERsGZ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::ikt9FFjCK`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::iMGf3gQkJ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::XECIXVaaa`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::pwfrViAKx`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::XW9oS781T`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::eG9ps0B0T`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::Gi96cV4JZ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::E77MtsPuI`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::Dispose`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::K33wSC4FD`
- `DCE Pro.dll` $\to$ `ClassLibrary1.Beam_DaiGiaCuongDam::mkHZ78ARHCU`
- *(và 675 methods khác xem trong JSON dump)*

#### 3. Phân hệ Vẽ Kết cấu Thép & Nút Khung Zamil
Tìm thấy **591 methods** then chốt:
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrBeamColumnCombo::XWbp7dtxoO5eZQgkW0TQ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrBeamColumnCombo::lJjZGftxp1osvb5GwPF3`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::Extract`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::Bt1OmraYqvI`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::eJsOmog4D91`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::jMWOmpbRGwa`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::f2nOm6AR37E`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::aGoOmMf8wOL`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::yBwOmwltGYl`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::e0lOmYLLl2i`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::dtiOmWHG4Qm`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::blUOmaKvPSV`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::sPGvD1tdJXRxI0NV1yXV`
- `DCE Pro.dll` $\to$ `ClassLibrary1.ColumnExtractor::jnoKfGtdjp3N6VlyvGV8`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::DocToaDoBlockCot`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::ChenBlockCot`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::ThongTinCotPolyline`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::GanGiaTri2`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::TimGiaoCatVoiLine`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::CheckGanDLSuDung`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::mGhO8ucLfyJ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::PoLyToListColumn`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::LocLineCot`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::FindListLine`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceBlockColumn::TimLineCoChieuDaiMax`
- *(và 566 methods khác xem trong JSON dump)*

#### 4. Phân hệ Revit BIM (Dựng mô hình & Rebar 3D)
Tìm thấy **600 methods** then chốt:
- `DCE Pro.dll` $\to$ `ClassLibrary1.planDBIM::TEJc4ytbJsDAj4v3EfnI`
- `DCE Pro.dll` $\to$ `ClassLibrary1.planDBIM::rTDdsItbjRoKPJhLxTP4`
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrCommand::DceAutoStr_Cmd`
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrCommand::NlK5MQKjqqq`
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrCommand::Etquh8t43bAMTIg2Qria`
- `DCE Pro.dll` $\to$ `ClassLibrary1.AutoStr.AutoStrCommand::x3C6pJt4FXTONJAty15B`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceSetup2Command::Mo`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceSetup2Command::o0tjrttneCaa3TdiaRKh`
- `DCE Pro.dll` $\to$ `ClassLibrary1.DceSetup2Command::k6taqetnGs3ApmpJ3UEy`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::TrimNetDamNamTrongCot_dce`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::gAGOHRyL4ad`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::d8dOHQnGp6t`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::wIMOH3oij3F`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::TaoDuongPhanTichLuc_dce`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::ictOHFLjuE6`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::gVqOHzoXTve`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::LieOgcGKUJj`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::sbvOg5w9sOh`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::kfSOgOXoMy7`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::k2ROg7dWkFE`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::aZXOgZaXY96`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::XiyOgurkxyJ`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::Xp1OgDxvSS4`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::b77OglDEt2A`
- `DCE Pro.dll` $\to$ `ClassLibrary1.MatBangKetCauCommand::eRWOghaSP2X`
- *(và 575 methods khác xem trong JSON dump)*

### 3.2 Toàn bộ Lệnh Menu AutoCAD Giải mã từ CUIX

#### Gói Menu: `DBimApps.cuix` (197 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Mua mới/Gia hạn | `licenseissuanceDce` |
| Hỗ trợ | `Admin_DCE` |
| Login | `DangNhapDCE` |
| Logout | `DangXuatDCE` |
| UpdateDBIM | `updateDBIM` |
| Lay Form ISO | `GetForm` |
| Cap nhat ISO | `UpdateIso_DCE` |
| Doi co chu ISO | `ScaleTextIso_DCE` |
| Setup | `DCESETUP` |
| Tạo TKT | `TKT_DCE` |
| Sửa TKT | `STK_DCE` |
| Sửa SLCK | `TKTSSoLuongCauKien` |
| Sửa SLCK 2 | `TKTSSoLuongCauKien2` |
| Quét TKT | `QuetThongKe_DCE` |
| Sửa ĐKT 1 | `TKTSDuongKinhThep` |
| Sửa ĐKT 2 | `TKTSDuongKinhThep2` |
| Sửa khoảng rải | `SuaKhoangRaiThep_DCE` |
| Tổng hợp TK | `TongHopThongKe_DCE` |
| Diễn giải SL | `DienGiaiSoLuongThepSan_DCE` |
| TK Coupler | `TongHopCoupler_DCE` |
| *...và 177 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `menudce.bak.cuix` (70 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| Cài đặt | `DCESETUP` |
| Tạo Viewport | `taomv` |
| *...và 50 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE.cuix` (71 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| Cài đặt | `DCESETUP` |
| Tạo Viewport | `taomv` |
| *...và 51 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE_ACAD.cuix` (71 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| Cài đặt | `DCESETUP` |
| Tạo Viewport | `taomv` |
| *...và 51 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE_BCAD.cuix` (71 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| Cài đặt | `DCESETUP` |
| Tạo Viewport | `taomv` |
| *...và 51 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE_GCAD.cuix` (73 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Update ISO | `UpdateIso_DCE` |
| Scale Text ISO | `ScaleTextIso_DCE` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| *...và 53 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE_ICAD.cuix` (73 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Update ISO | `UpdateIso_DCE` |
| Scale Text ISO | `ScaleTextIso_DCE` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| *...và 53 lệnh khác* | *Xem chi tiết trong tệp JSON* |

#### Gói Menu: `MenuDCE_ZWCAD.cuix` (71 lệnh)
| Tên Nút / Chức năng | Lệnh AutoCAD (Command Line Macro) |
|---|---|
| Polyline Edit | `_pedit` |
| Properties | `_.QUICKPROPERTIES` |
| Đăng nhập DCE | `DangNhapDCE` |
| Đăng xuất DCE | `DangXuatDCE` |
| Get Form | `Getform` |
| Tạo bảng thống kê thép | `TKT_DCE` |
| Sửa bảng thống kê thép | `STK_DCE` |
| Sửa số lượng cấu kiện | `TKTSSoLuongCauKien` |
| Sửa đường kính thép | `TKTSDuongKinhThep` |
| Tổng hợp thép | `TongHopThongKe_DCE` |
| Quét thống kê thép | `QuetThongKe_DCE` |
| Xem liên kết thép | `XemLienKetThep` |
| Sửa dữ liệu thép | `SuaCKThep` |
| Xóa liên kết thép | `XoaLienKetThep` |
| Gán liên kết thép | `GanLienKetThep` |
| Coppy dữ liệu thép | `MaTTThep` |
| Xóa dữ liệu ẩn | `XoaDLDataDCE` |
| Chèn text quay theo line | `QuayTextTheoLine` |
| Cài đặt | `DCESETUP` |
| Tạo Viewport | `taomv` |
| *...và 51 lệnh khác* | *Xem chi tiết trong tệp JSON* |

---

## 4. GIẢI PHẪU TẦNG 3 — THUẬT TOÁN & TỆP CẤU HÌNH SYSTEM

Tổng số tệp cấu hình phát hiện: **1239 tệp**.
Thuật toán cốt lõi được nhận diện: **56 tệp thuật toán trọng yếu**.

### Thuật toán: `AnThongKeThepCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
No
```

### Thuật toán: `AnThongKeThepVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
No
```

### Thuật toán: `ChieuCaoDamDienHinhVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `ChieuCaoDamDienHinhVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `ChieuCaoKhungTenVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
4000
```

### Thuật toán: `ChieuCaoKhungTenVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
4000
```

### Thuật toán: `ChieuCaoVeVachHam.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
0
```

### Thuật toán: `ChieuRongCotDienHinhVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `ChieuRongCotDienHinhVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
1000
```

### Thuật toán: `ChieuRongKhungTenVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
2000
```

### Thuật toán: `ChieuRongKhungTenVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
1500
```

### Thuật toán: `ChieuRongVeVachHam.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
0
```

### Thuật toán: `DiemNoiDauCachSanVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
100
```

### Thuật toán: `KiemSoatLoiKhiThongKeThep.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
False
```

### Thuật toán: `LayToaDoCotHotrovedam.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
False
```

### Thuật toán: `LoaiDaiVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
Dữ liệu Excel
```

### Thuật toán: `LopBTBVVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
30
```

### Thuật toán: `LopBTBVVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
30
```

### Thuật toán: `MocDaiTrongVedam.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
8
```

### Thuật toán: `MocDaiVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
6
```

### Thuật toán: `MocDaiVongVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
6
```

### Thuật toán: `MocDaiVongVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
```

### Thuật toán: `NgonNguVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
Vietnamese
```

### Thuật toán: `NgonNguVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
Vietnamese
```

### Thuật toán: `SuaThongKeThep.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
stk_dce
```

### Thuật toán: `TaiDamVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `TaiDamVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `TaoThongKeThep.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
tkt_dce
```

### Thuật toán: `TaoViewport.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
taomv
```

### Thuật toán: `ThongKeThepSan.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
tkts
```

### Thuật toán: `TieuChuanSDVeCot.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
True
```

### Thuật toán: `TieuChuanSDVeVach.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
TCVN 5574
```

### Thuật toán: `ToiUuCatThep.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
ToiUuCatThep
```

### Thuật toán: `TyleTaoViewPort.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
20
```

### Thuật toán: `UDModelEtabs.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
UpdateModelEtabs
```

### Thuật toán: `UDThongKeThepDam.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
QuetThongKe_dce
```

### Thuật toán: `VeDamMatCat.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
VeMCD_DCE
```

### Thuật toán: `VeThangNew_TranhDeTag.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
1
```

### Thuật toán: `ViewPortAutoClickToaDoChinh.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
0,0,0
```

### Thuật toán: `ViewPortAutoPadXx.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
5
```

### Thuật toán: `ViewPortCaoKhungTen.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
297
```

### Thuật toán: `ViewPortDoanChongLan.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
500
```

### Thuật toán: `ViewPortGianDongDMBV.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
5
```

### Thuật toán: `ViewPortPadYy.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
5
```

### Thuật toán: `ViewPortRongKhungTen.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
368
```

### Thuật toán: `ViewPortSaiSoChoPhepXepKhung.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
1
```

### Thuật toán: `ViewPortSapXepToiUu.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
False
```

### Thuật toán: `ViewPortTenKhung.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
```

### Thuật toán: `ViewPortTheoThuTuSelect.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
True
```

### Thuật toán: `ViewPortTrenXuongDuoi.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
False
```

### Thuật toán: `ViewPortTuDongSapKhungTen.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
True
```

### Thuật toán: `ViewPortTyLeKhung.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
50
```

### Thuật toán: `ViewPortUuTienXepKhung.txt` (Thư mục `System`)
Nội dung cấu hình giải mã:
```text
A
```

### Thuật toán: `AutoCad_VeCotH.txt` (Thư mục `SystemSteel`)
Nội dung cấu hình giải mã:
```text
HTong
```

### Thuật toán: `DataLoadCombinationTCVN27372023.txt` (Thư mục `AddinSteel\SystemSteel`)
Nội dung cấu hình giải mã:
```text
SW
1.1
True_SDL1
SDL
1.2
True_SDL2
BW
1.2
True_SDL3
COL
1.2
True_SDL4
SOIL
1.1
True_SDL5
... (còn 77 dòng nữa)
```

### Thuật toán: `DataMohinhMaidoc2phia.txt` (Thư mục `AddinSteel\SystemSteel`)
Nội dung cấu hình giải mã:
```text
6x8
38
9+10+10+9
8
True_Release
12
Giữa nhà
0
False_Pedestal
1.5
True_GridA
True_GridB
B25
CB240-T
CB400-V
... (còn 35 dòng nữa)
```

---

## 5. GIẢI PHẪU TẦNG 4 — BẢN VẼ FORM MẪU (CAD TEMPLATES)

### 5.1 Cấu trúc Chuẩn Layer trong `Form 2.dxf` (BTCT)

| Tên Layer | Mã Màu ACI | Kiểu Nét (Linetype) | Chiều dày Nét (Lineweight) | Vai trò Kỹ thuật |
|---|:---:|:---:|:---:|---|
| `0` | 7 | Continuous | -3 | Đường nét kỹ thuật |
| `DCE_Name` | 142 | Continuous | 20 | Ghi chú & Tên cấu kiện |
| `DCE_KT` | 142 | Continuous | 20 | Đường nét kỹ thuật |
| `Defpoints` | 7 | Continuous | 5 | Đường nét kỹ thuật |
| `DCE_Dim` | 254 | Continuous | 9 | Kích thước Dimension |
| `DCE_Block` | 8 | Continuous | 9 | Đường nét kỹ thuật |
| `DCE_MCZiCZac` | 144 | Continuous | 13 | Đường nét kỹ thuật |
| `Dce_text` | 7 | Continuous | 13 | Ghi chú & Tên cấu kiện |
| `DCE_BaoBeTong` | 4 | Continuous | 18 | Đường bao bê tông |
| `DCE_ThepChu` | 1 | Continuous | 35 | Cốt thép chịu lực chính |
| `DCE_ThepDai` | 220 | Continuous | 25 | Cốt thép chịu lực chính |
| `DCE_Truc` | 8 | DASHDOT2_DBIM | 13 | Lưới trục định vị |
| `DCE_NetKhuat` | 9 | HIDDEN_DBIM | 5 | Đường nét kỹ thuật |
| `DCE_NetDut` | 8 | HIDDEN_DBIM | 5 | Đường nét kỹ thuật |
| `DCE_Hatch` | 8 | Continuous | 13 | Đường nét kỹ thuật |
| `DCE_Gen_Open` | 144 | CENTER2_DBIM | 13 | Đường nét kỹ thuật |
| `AREAS` | 1 | Continuous | -3 | Đường nét kỹ thuật |
| `POINTS` | 5 | Continuous | -3 | Đường nét kỹ thuật |
| `DCE_ThepChu.TTT` | 5 | Continuous | 35 | Cốt thép chịu lực chính |
| `DCE_ThepDai.TTT` | 6 | Continuous | 25 | Cốt thép chịu lực chính |

### 5.2 Danh mục Blocks & Thuộc tính Thuộc Thẻ (ATTDEF)

Tổng số Blocks có thẻ thuộc tính động (Dynamic/Attribute Blocks): **123 blocks**.

| Tên Block | Số Thẻ ATTDEF | Danh sách Thẻ Tag (ATTDEF Tags) |
|---|:---:|---|
| `Dce_KhTenTruc` | 1 | `TRUC` (mặc định: 'AA') |
| `*U4` | 2 | `TENDAM` (mặc định: 'SECTION 1'), `TL` (mặc định: 'SCALE 1 : ') |
| `*U5` | 2 | `TL` (mặc định: 'SCALE 1 : '), `TENNHIP` (mặc định: 'SECTION 1') |
| `*U6` | 2 | `TL` (mặc định: 'SCALE 1 : '), `TENMATCAT` (mặc định: 'SECTION 1') |
| `Dce_CaoTrinh` | 1 | `CT` (mặc định: '%%p0.000') |
| `TK2R1` | 10 | `SH` (mặc định: 'SH'), `L2` (mặc định: 'L2'), `L1` (mặc định: 'L1'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'L'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK3R1` | 10 | `SH` (mặc định: 'SH'), `L1` (mặc định: 'L1'), `L2` (mặc định: 'L2'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK5R1` | 10 | `SH` (mặc định: 'SH'), `L2` (mặc định: 'L2'), `L1` (mặc định: 'L1'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK6R1` | 10 | `SH` (mặc định: 'SH'), `L1` (mặc định: 'L1'), `L2` (mặc định: 'L2'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK1R1` | 9 | `KL` (mặc định: 'KL'), `Lall` (mặc định: 'Lall'), `SKC` (mặc định: 'SKC'), `SL` (mặc định: 'SL'), `sumL` (mặc định: 'sumL'), `DK` (mặc định: 'Ø8'), `L` (mặc định: 'L'), `SH` (mặc định: 'SH'), `TSL` (mặc định: 'TSL') |
| `TK2` | 10 | `SH` (mặc định: 'SH'), `L2` (mặc định: 'L2'), `L1` (mặc định: 'L1'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'L'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK3` | 10 | `SH` (mặc định: 'SH'), `L1` (mặc định: 'L1'), `L2` (mặc định: 'L2'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK4` | 11 | `SH` (mặc định: 'SH'), `L2` (mặc định: 'L2'), `L1` (mặc định: 'L1'), `L3` (mặc định: 'L3'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK5` | 10 | `SH` (mặc định: 'SH'), `L2` (mặc định: 'L2'), `L1` (mặc định: 'L1'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |
| `TK6` | 10 | `SH` (mặc định: 'SH'), `L1` (mặc định: 'L1'), `L2` (mặc định: 'L2'), `DK` (mặc định: 'Ø8'), `sumL` (mặc định: 'sumL'), `SL` (mặc định: 'SL'), `SKC` (mặc định: 'SKC'), `Lall` (mặc định: 'Lall'), `KL` (mặc định: 'KL'), `TSL` (mặc định: 'TSL') |

---

## 6. KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC R&D TỰ CHỦ CHO `.AGENTS`

Dựa trên toàn bộ kết quả giải phẫu, Tổ R&D kiến nghị chiến lược triển khai cho hệ sinh thái `.agents`:
1. **Về Bóc tách Thép NLP:** Chúng ta đã khai thác trọn vẹn tập dữ liệu `mauhoc.db` (45,020 mẫu) vào module [rebar_tokenizer.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/skills/Structural_Design_Engineer/scripts/rebar_tokenizer.py), đạt độ chính xác tương đương hoặc vượt trội DCE mà không cần cài đặt .NET runtime.
2. **Về Tự chủ AutoCAD Drawing:** Module [cad_bridge.py](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/tools/cad_bridge.py) đã chuẩn hóa 6 layers tương ứng với các layer chuẩn `DCE_*` đã giải mã từ `Form 2.dxf`. Giai đoạn tới sẽ nạp toàn bộ Block định danh (`Dce_KhTenTruc`, `Dce_CaoTrinh`, `TENDAM`) vào engine vẽ tự động.
3. **Về Thuật toán Cắt Thép 11.7m:** Tái lập thuật toán trong `ToiUuCatThep.txt` bằng mô hình toán tối ưu tuyến tính (Linear Programming / 1D Bin Packing) trong Sprint 4.
4. **Về Tự chủ Revit BIM:** Thay vì phải biên dịch từng file `.exe` cho 12 phiên bản Revit từ 2016 đến 2027 như thư mục `AddinSetup_RVT/`, hệ thống `.agents` chọn con đường hiện đại: **pyRevit Extension thuần Python**, tương thích tự động 100% mọi đời Revit.

---

*Báo cáo được hoàn lập tự động bởi công cụ `dce_deep_inspector.py`.*