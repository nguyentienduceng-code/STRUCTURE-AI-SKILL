# Biên bản kiểm định độc lập CAD v5.0

**Mã:** `07_INDEPENDENT_AUDIT_CAD_V50`  
**Ngày:** 2026-11-15  
**Đơn vị kiểm định:** Codex  
**Kết luận:** **CHƯA ĐẠT NGHIỆM THU CUỐI**. Khung và khoảng hở công trình đạt; các cổng 1, 4, 5 không đạt theo tiêu chí nguyên văn; profile `plan` chưa xác minh do thiếu sidecar.

## Phạm vi và phương pháp

Đọc trực tiếp modelspace của ba DXF bằng `ezdxf 1.4.4`. Tọa độ dưới đây tính bằng mm. Mã đo và JSON kết quả nằm cạnh biên bản: `audit_cad_v50_geometry.py`, `audit_cad_v50_geometry.json`. Bounding box thực thể được tính bằng `ezdxf.bbox.extents`; khoảng hở bảng kê lấy mép trái bảng kê trừ mép phải ngoài cùng của các layer công trình, trục, block nhãn và kích thước.

| Bản vẽ | Khung ngoài `[xmin,ymin,xmax,ymax]` | Khung trong | Khung tên | Bảng kê / ghi chú (bbox) |
|---|---|---|---|---|
| KC-01 | `[2000,2000,128150,91100]` | `[5750,3500,126650,89600]` | `[99650,3500,126650,11750]` | `[94400,77750,110900,88100]`; `[94400,61850,110900,73100]` |
| KC-02 | `[2000,2000,128150,91100]` | `[5750,3500,126650,89600]` | `[99650,3500,126650,11750]` | `[94400,75350,110300,88100]`; `[94400,61100,110300,72350]` |
| KC-03 | `[2000,2000,128150,91100]` | `[5750,3500,126650,89600]` | `[99650,3500,126650,11750]` | `[94400,77750,111800,88100]`; `[94400,61850,111800,73100]` |

| Bản vẽ | Đầu dưới trục 11 − mép trên khung tên | Mép phải công trình/kích thước | Khoảng hở bảng kê | Giao trục/khung tên | Giao trục/bảng kê | LINE/TEXT/DIMENSION trong khung tên |
|---|---:|---:|---:|---:|---:|---:|
| KC-01 | 10.300 | 87.282,955 (DIMENSION) | 7.117,045 | 0 | 0 | 4 TEXT |
| KC-02 | 10.300 | 82.400 (block trục) | 12.000 | 0 | 0 | 4 TEXT |
| KC-03 | 10.300 | 82.400 (block trục) | 12.000 | 0 | 0 | 4 TEXT |

Khoảng cách trục 10/11 tới khung tên vượt 1.500 mm. Bốn TEXT giao khung tên trên mỗi tờ là nội dung tiêu đề/khung tên. Theo điều kiện **0 entity bất kể vai trò**, cổng 1 không đạt; nếu loại trừ nội dung chủ ý của khung tên thì phần va chạm trục đạt. Khoảng hở bảng kê đều vượt 2.250 mm; không có LINE trục chạm bảng kê.

## Kết quả 7 cổng

| Cổng | Kết quả | Bằng chứng |
|---|---|---|
| 1. Khung tên | **FAIL theo tiêu chí 0 entity** | 4 TEXT trong bbox mỗi tờ; 0 LINE trục giao; khoảng trục 11 là 10.300 mm. |
| 2. Sidebar | **PASS** | Clearance thấp nhất 7.117,045 mm; 0 trục giao bảng kê. |
| 3. Dynamic frame | **PASS** | Ngoài 126.150 × 89.100; lề trái/dưới/phải/trên = 3.750/1.500/1.500/1.500. |
| 4. Native entity | **FAIL** | DIMENSION native: 19/15/15 nhưng 49/49 dùng `Dce_100MV`, không phải `Dce_150MV`. HATCH solid trên `DCE_Hatch`: 54/54/54, tất cả color 7 thay vì 8. Block `TenCauKien` có ATTDEF căn tâm `(halign=1,valign=2)`; KC-02 có 82 ATTRIB căn tâm và 3 ATTRIB của title block không căn tâm. |
| 5. Rule 12b | **FAIL** | Text/attribute hiện diện: 111/205/259; không có true color trắng `#FFFFFF`; mỗi tờ có 32 thực thể `color=2`. Tiêu đề tiếng Anh KC-02/03 mang `true_color=#1E3246` nhưng đồng thời có `color=2`, trái điều kiện cấm ACI 2. |
| 6. Compliance checker 2.0 | **PARTIAL / NEEDS_REVIEW** | `physical`: PASS cả 3. `plan`: NEEDS_REVIEW cả 3; 16/16 cổng áp dụng G8.01–G8.12, G8.17–G8.20 trả `UNVERIFIED` vì thiếu tệp `.dce_audit.json` gắn với mỗi DXF. Không thể ghi PASS 16/16. |
| 7. Regression | **PASS** | `python tests/run_all_tests.py`: 31/31 suite PASS, 163,36 giây; log và JSON trong `memory/audits/cad_v50_tests`. |

### Số lượng thực thể gốc

| Bản vẽ | Tổng modelspace | DIMENSION | HATCH | INSERT | ATTRIB gắn INSERT | ATTDEF trong định nghĩa block |
|---|---:|---:|---:|---:|---:|---:|
| KC-01 | 294 | 19 | 55 (54 `DCE_Hatch` + 1 `DCE_Symbol`) | 31 | 33 | 847 |
| KC-02 | 430 | 15 | 54 | 57 | 85 | 847 |
| KC-03 | 491 | 15 | 54 | 108 | 170 | 847 |

## Quyết nghị

Đề nghị Gemini sửa DimStyle sang `Dce_150MV`, màu HATCH bê tông sang 8, loại ACI màu 2 khỏi text/attribute, cung cấp sidecar audit đúng hash/nội dung cho mỗi DXF và xác định ngoại lệ hợp lý cho TEXT thuộc chính khung tên. Sau đó chạy lại cả 7 cổng. Kết quả `physical PASS` và 31/31 test suite không thay thế được nghiệm thu sản phẩm theo các tiêu chí còn lỗi.
