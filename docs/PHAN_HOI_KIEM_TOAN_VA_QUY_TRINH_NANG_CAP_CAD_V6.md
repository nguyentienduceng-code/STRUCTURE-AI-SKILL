# PHẢN HỒI KIỂM TOÁN & QUY TRÌNH NÂNG CẤP HỆ THỐNG CAD AGENT (`.agents` v7.5 → CAD v6.0)

**Mã tài liệu:** `SPEC_CAD_V6_UPGRADE_20261124`  
**Ngày ban hành:** 24/11/2026  
**Tài liệu đầu vào được phản biện:** `d:\Users\ADMIN\Downloads\bao_cao_nang_cap_he_thong_cad_agent_v6.md`  
**Cơ sở đối chiếu thực địa:**
- Kho kỹ thuật `g:\My Drive\Google AI Studio\.agents` (v7.5: 14 Domain Skills, 50 bộ kiểm thử, `STANDARDS_LOCK.md` v3.3.0).
- Hồ sơ mẫu chuẩn văn phòng: `g:\My Drive\Google AI Studio\00_Template_&_Standards\DU AN MAU\02.DuAn` (32 bản vẽ, 3 tệp tham chiếu Xref, 7 Workbook DWG, `DuAn.dst`).
- Bộ sản phẩm thực nghiệm Cát Lái: `g:\My Drive\Google AI Studio\01_Projects\03_Sprint2_KetQua_NeChu_CAD\04_Deliverables_ToTrinh` (`KC-02` đến `KC-09`).
- Môi trường máy trạm thực tế: `C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe` và thư viện Block `DCE_Master_Seed_Template.dxf` (`1.946,8 KB`, 98 Block).

---

## PHẦN I. ĐÁNH GIÁ CHI TIẾT NHẬN XÉT CỦA BÁO CÁO KIỂM TOÁN

### 1.1. Năm nhận định chính xác 100% (Tiếp thu toàn phần)

1. **Chẩn đoán "chẻ đôi chất lượng" giữa nhánh Mặt bằng (`7,5/10`) và nhánh Chi tiết (`4,5/10`):**
   - Nhóm mặt bằng dựng nguyên bản (`KC-02`, `KC-05`, `KC-06`, `KC-07`) đạt `2,20 – 2,33 MB`, chứa `32 – 39` đối tượng `DIMENSION` (đường kích thước thật) và `64 – 120` `INSERT` (chèn Block), cho phép kỹ sư chỉnh sửa trực tiếp trong AutoCAD.
   - Nhóm chi tiết cốt thép tái lập vector từ PDF (`KC-03`, `KC-04`, `KC-08`, `KC-09`) nặng `2,91 – 4,86 MB`, vỡ thành `3.621 – 13.848` thực thể rời (`71,9% – 95,9%` là `LINE`), `DIMENSION = 0` và `INSERT = 1`. Cách xuất này chỉ phục vụ xem hình ảnh, không sửa được kích thước hay thống kê thép trong AutoCAD.

2. **Phình dung lượng do chưa dọn kho Block thừa từ bản mẫu:**
   - Tệp `DCE_Master_Seed_Template.dxf` nặng `1.946,8 KB` và chứa sẵn `98` Block định nghĩa (`TK1..TK44`, `Dce_DanhDauThep`, `Dce_CaoTrinh`, `Dce_KhTenTruc`). Do trình xuất DXF chưa chạy hàm `Purge` (xóa Block không dùng) trước khi lưu, mỗi tờ mặt bằng mang theo gần `2 MB` dữ liệu thừa.

3. **Các lỗi đồ họa cụ thể trên bộ bản vẽ `KC-02` đến `KC-08`:**
   - Trên `KC-02`: Nhãn dầm giằng `GMX.1`, `GMY.1`, `GMX.2` chạm nét đài/dầm; cột chữ `LOẠI CỌC` sát vạch phân ô bảng thống kê cọc.
   - Trên `KC-05`: Thiếu đường kích thước neo mép cột hai phương từ tim trục; bảng thống kê cột bên trái ở khung dưới (`T1–T2`) lặp nguyên cột `C4` dù cột này đã dừng.
   - Trên `KC-03` và `KC-08`: Ký tự `Ø` (Unicode) bị kết tụ thành chấm đen đặc (`●16a150`, `4●20`) khi render kích thước nhỏ thay vì dùng mã AutoCAD `%%c`; cao độ đỉnh `+10.400` và kích thước `750/640` sát mép khung trên; thiếu mặt cắt ngang thân cột và thiếu bảng thống kê thép (BBS — Bar Bending Schedule).

4. **Kiến trúc 4 lớp chuẩn văn phòng của dự án mẫu `02.DuAn`:**
   - Khảo sát thực địa thư mục `02.DuAn` xác nhận bộ 32 tờ chỉ nặng tổng cộng vài megabyte nhờ tách `Xreft luoi.dwg` (`288 KB`, kiểu `Attachment`), `Xreft Cot.dwg` (`303 KB`, kiểu `Overlay`), khung tên `Khung A3.dwg` (`284 KB`, chèn `1:1` ở PaperSpace — không gian giấy in) và `7` tệp DWG làm việc (`MBKC.dwg`, `Chi Tiet Mong.dwg`, `Mạt Bang Dinh Vi Cot.dwg`, `Chi Tiet Dam.dwg`, `Chi tiet thep san.dwg`, `CauThang.dwg`, `To Bia + GhiChuChung`).

5. **Điểm nghẽn an toàn ở `antigravity_dual_bus_hook.py` và `hooks.json`:**
   - Khối ngoại lệ tại dòng `289–292` của `.agents/tools/antigravity_dual_bus_hook.py` trả về `{}` khi lỗi đọc JSON, khiến bước `PreToolUse` rơi vào trạng thái `fail-open` (cho phép bỏ qua kiểm tra khi sự cố).
   - Tệp `.agents/hooks.json` dòng `6` và `18` vẫn gắn đường dẫn tuyệt đối `C:/Users/ADMIN/AppData/Local/Programs/Python/Python312/python.exe`.

---

### 1.2. Năm điểm Báo cáo nhận định lệch hiện trạng hoặc chứa bẫy kỹ thuật (Hiệu chỉnh)

| STT | Nội dung báo cáo nêu | Kết quả kiểm chứng trực tiếp mã nguồn | Phương án hiệu chỉnh kỹ thuật |
|:---:|---|---|---|
| 1 | `deflection_check.py` còn lỗi nội suy độ võng giới hạn Bảng G.1 (trích từ `CODEX_VERIFY_V75X_REPORT.md` ngày 22/11). | Hàm `get_tcvn_2737_2023_table_g1_limit_mm()` trong `deflection_check.py` (dòng 8–45) **đã sửa xong**, nội suy trực tiếp `f_u (mm)`. Ca nhịp `9 m` cho `f_u = 39,00 mm`, độ võng `39,48 mm` kết luận `FAIL` tại `test_deflection_check.py` (dòng 86–94). | **Đóng mục sửa `deflection_check.py`**; đính kèm bằng chứng mã nguồn và kết quả kiểm thử trong phản hồi. |
| 2 | Yêu cầu bổ sung ngay dim mép cột `DCE_Setout` vào tờ định vị cột `KC-05..07`. | Cổng kiểm toán `G8.06` tại `dce_cad_compliance_checker.py` (dòng 1026–1038) đang khóa luật: *"[KC.05] Đã tắt 100% Dim định vị cột trên DCE_Setout đúng quy chuẩn tách bạch mặt bằng"*. Nếu chỉ bật vẽ mà giữ luật cũ, cổng kiểm toán sẽ đánh `FAIL`. | **Sửa đồng bộ cả 2 nơi**: cập nhật luật cổng `G8.06` cho phép và bắt buộc `DCE_Setout` trên bản vẽ định vị cột, đồng thời bật sinh dim `DCE_Setout` 2 phương trong `cad_multiview_a3.py`. |
| 3 | Đề xuất xây mới nhiều module (`PaperSpace`, `Viewport`, `Generator` BTCT) gần như từ đầu. | Kho `cad_integration/` đã có sẵn `cad_paperspace_builder.py` (`27,1 KB`), `cad_sheet_set.py` (`86,7 KB`, có sẵn `Viewport.frozen_layers` tách `REBAR_TOP` / `REBAR_BOTTOM`), `dce_dxf_generator.py` (`19,8 KB`) và `calc_to_dxf.py` (`23,4 KB`). | **Không tạo nhánh mới song song**; hợp nhất `dce_dxf_generator.py` + `calc_to_dxf.py` thành bộ dựng chi tiết BTCT chuẩn và nâng cấp trực tiếp `cad_paperspace_builder.py`, `cad_sheet_set.py`. |
| 4 | Khẳng định `convert_to_dwg = UNAVAILABLE` là do thiếu phần mềm chuyển đổi trên máy. | `mcp_dce_cad_server.py` (dòng 79–82) báo `UNAVAILABLE` vì chỉ dò tìm `ODAFileConverter.exe`. Kiểm tra ổ đĩa máy trạm xác nhận **`C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe` đang cài sẵn**. | Nối thẳng `accoreconsole.exe` làm động cơ chuyển đổi `DXF → DWG` chính thức (chạy `AUDIT`, `-PURGE`, `SAVEAS`, `-PLOT` `.CTB`), giữ `ODAFileConverter` làm dự phòng. |
| 5 | Đề xuất Python tự giải mã/mã hóa `xor_add` để sinh trực tiếp tệp Sheet Set `DuAn.dst`. | Kiểm tra nhị phân tệp mẫu `DuAn.dst` (`57.292 bytes`, byte đầu `d0 cd 14 e3...`) xác nhận đây là định dạng nhị phân mã hóa nội bộ của `AcSmSheetSetMgr` (AutoCAD Sheet Set Manager), không phải XML thuần văn bản. | **Cấm tự đóng gói nhị phân `.dst` bằng Python** để tránh hỏng file hoặc treo AutoCAD. Sinh `sheet_set_manifest.json` rồi gọi **AutoCAD COM API (`AcSmSheetSetMgr`) / kịch bản AutoCAD 2021** tạo `.dst` chính tắc, chặn trùng mã tờ (`KC_11`) và đường dẫn tuyệt đối. |
| 6 | Đề xuất vẽ khung tên/vùng cứng mới bằng code, bỏ sót kho **4 Bộ Form Mẫu Mở DCE** sẵn có. | Thư mục `00_Template_&_Standards/CAD_Forms/` đang có sẵn `Form_01..Form_04.dxf` (`108` Block/Form, `DCE_TITLEBLOCK_*` gắn `ATTDEF`, các khung vùng `DCE_ZONE_*`) kèm `cad_form_contract.py` (tìm 3 tầng) và `cad_form_patcher.py` (giữ chỉnh sửa tay `DCE_AGENT_OWNED`). Vừa rồi `KC.02/05–07` chưa bật `template_mode="open"`, còn `Form_04` chưa có bộ dựng mặt cắt chi tiết để đổ vào 3 vùng của Form. | **Đặt Bộ 4 Form Mẫu Mở (`Form_01..Form_04`) làm trục xương sống:** mặc định `template_mode="open"` trên `Form_02` cho mặt bằng A3; lắp ruột `cad_rc_detail_engine.py` đổ trực tiếp vào `Form_04` (dùng sẵn `TK1..TK44`); nâng cấp `Form_02`/`Form_04` hỗ trợ `PaperSpace 1:1` đa tỷ lệ; giữ `108` Block trên tệp Form gốc và chỉ `Purge` trên tệp giao nộp. |

> **Ghi chú về đường dẫn trong `.agents/hooks.json`:** Đường dẫn trình thông dịch `Python312` trong `.agents/hooks.json` và `.claude/settings.json` được thiết kế có chủ đích nhằm giữ độ trễ khởi chạy `< 100 ms` và tránh sai thư mục làm việc khi kiểm thử độc lập; cần bổ sung kiểm tra tương thích môi trường đa máy trạm trong Giai đoạn 0 mà không làm chậm thời gian phản hồi.

---

## PHẦN II. PHƯƠNG ÁN PHẢN HỒI CHÍNH THỨC (8 QUYẾT ĐỊNH KỸ THUẬT)

| STT | Kiến nghị của Báo cáo Kiểm toán | Quyết định | Hành động triển khai tương ứng |
|:---:|---|:---:|---|
| 1 | Cấm nhánh `DETAIL_VECTOR_RECONSTRUCTED` cho bản vẽ giao nộp chính thức | **Đồng ý 100%** | Giáng cấp kịch bản tách PDF về vai trò trích xuất tham chiếu nội bộ; 100% tờ chi tiết giao nộp dựng từ thực thể CAD gốc đổ vào `Form_04`. |
| 2 | Dọn rác Block thừa (`Purge`) & sửa va chạm chữ mặt bằng (`KC-02/05`) | **Đồng ý 100%** | Áp dụng **Purge 2 tầng**: giữ đủ `108` Block trên Form mẫu gốc `CAD_Forms/`, chạy `purge_unused_blocks()` riêng cho tệp giao nộp (`< 500 KB/tờ`); đẩy nhãn `GMX/GMY` né đài/giằng; co chữ ô `LOẠI CỌC`; lọc bảng cột theo tầng. |
| 3 | Bổ sung dim định vị mép cột `DCE_Setout` trên `KC-05..07` | **Đồng ý có điều chỉnh** | Bổ sung dim `DCE_Setout` 2 phương và cập nhật luật cổng `G8.06` trong `SKILL_VERIFY` để không tự đánh rớt. |
| 4 | Chuẩn hóa ký tự `%%c`, khóa biên an toàn & tự sinh 4 tờ BBS | **Đồng ý 100%** | Xuất thép bằng `%%c` trong DXF/DWG (render PNG quy đổi nét mảnh thay chấm đặc `●`); khóa khoảng hở mép khung `≥ 8 mm` giấy; gọi Block `TK1..TK44` sẵn trong `Form_04` xuất BBS khớp 100% chi tiết. |
| 5 | Áp dụng kiến trúc `3 Xref + 7 Workbook PaperSpace` chuẩn `02.DuAn` | **Đồng ý (Kế thừa sẵn có)** | Nâng cấp trên `cad_paperspace_builder.py` và `cad_sheet_set.py`; thêm `cad_xref_builder.py` gắn `Xreft_Luoi` (`Attachment`) và `Xreft_Cot` (`Overlay`) theo đường dẫn tương đối tại gốc `(0,0,0)`. |
| 6 | Tích hợp `accoreconsole.exe` xuất `.DWG`/PDF `.CTB` & tạo `DuAn.dst` | **Đồng ý có điều chỉnh** | Kết nối trực tiếp `AutoCAD 2021 accoreconsole.exe` trên máy; tạo `.dst` qua COM `AcSmSheetSetMgr` từ JSON manifest, kiểm tra 0 trùng mã tờ và 0 đường dẫn ổ đĩa cứng. |
| 7 | Vá lỗi P0: `antigravity_dual_bus_hook.py`, `hooks.json` & `deflection_check.py` | **Chấp thuận 2/3 · Đóng 1/3** | Vá `PreToolUse` sang `fail-closed` và chuẩn hóa kiểm thử `hooks.json`. Đóng yêu cầu sửa `deflection_check.py` vì đã hoàn thành và có test kiểm chứng. |
| 8 | Bảo toàn tùy biến người dùng bằng **Bộ 4 Form Mẫu Mở DCE** *(Bổ sung cốt lõi)* | **Khẳng định bắt buộc** | Bật mặc định `template_mode="open"` trên `Form_01..Form_04` (`00_Template_&_Standards/CAD_Forms/`); bảo toàn 100% chỉnh sửa tay khung tên, màu layer, dimstyle qua cờ `DCE_AGENT_OWNED` (`cad_form_patcher.py`). |

---

## PHẦN III. QUY TRÌNH NÂNG CẤP HỆ THỐNG CAD AGENT v6.0 (LỘ TRÌNH 4 SPRINT)

Mỗi Sprint thực hiện theo vòng khép kín trên Dual-Agent Bus: **Gemini (Dựng mã & chạy xuất thử Cát Lái) ➔ Kiểm thử Tự động + `accoreconsole AUDIT` ➔ Claude (Thẩm tra độc lập & ký nhận DoD)**.

### 3.1. Giai đoạn 0 — Khóa an toàn hạ tầng & Mở khóa AutoCAD 2021 (`0,5 ngày`)

- **Tệp tác động:** `.agents/tools/antigravity_dual_bus_hook.py`, `.agents/hooks.json`, `.agents/tools/accoreconsole_adapter.py` (mới), `.agents/tools/mcp_dce_cad_server.py`.
- **Trình tự thực hiện:**
  1. Đổi nhánh `except Exception` trong `antigravity_dual_bus_hook.py` để trả về `{"decision": "deny"}` riêng cho sự kiện `PreToolUse` (`fail-closed`), giữ `fail-open` chỉ cho `PreInvocation`.
  2. Thay đường dẫn cứng `Python312` trong `.agents/hooks.json` bằng lệnh tương thích đa máy trạm (`python` hoặc bộ định vị tương đối kèm kiểm thử).
  3. Xây `accoreconsole_adapter.py` bọc lệnh gọi `C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe` chạy trên thư mục tạm cô lập: nạp `.dxf`, chạy `-PURGE ALL`, `AUDIT Y`, xuất `.dwg` (AC1032) và xuất PDF theo `.CTB`. Tích hợp vào công cụ `convert_to_dwg` của `mcp_dce_cad_server.py`, giữ nguyên khóa bảo vệ cấm sửa `.dwg` gốc dự án.
- **Tiêu chí hoàn thành (DoD):** Bộ kiểm thử hook PASS 100%; chuyển đổi thử nghiệm thành công tệp `KC-02_MatBangKetCauNgam.dxf` sang `.dwg` và PDF `.CTB` với `0` lỗi `AUDIT`.

### 3.2. Giai đoạn 1 — Bật Form Mở `Form_02` & Chuẩn hóa Mặt bằng Native lên ≥ 9,2/10 (`1,5 ngày`)

- **Tệp tác động:** `cad_block_adapters.py`, `cad_multiview_a3.py`, `cad_plan_engine.py`, `dce_cad_compliance_checker.py` (Cổng `G8.06`), `build_catlai_plans_native.py`.
- **Trình tự thực hiện:**
  1. Bật mặc định `template_mode="open", form_id="FORM_02_MULTIVIEW_A3_BTCT"` nạp từ `00_Template_&_Standards/CAD_Forms/Form_02_MultiView_A3_BTCT.dxf`, giữ nguyên khung tên `DCE_TITLEBLOCK_A3` (`ATTDEF`) và mọi chỉnh sửa tay của kỹ sư.
  2. Bổ sung `purge_unused_blocks(doc)` chạy theo cơ chế **Purge 2 tầng** riêng trên bản xuất trước `saveas` (tuyệt đối không ghi đè tệp Form gốc 108 Block).
  3. Mở rộng `cad_multiview_a3.py`: né nhãn dầm `GMX/GMY` khỏi vùng đài móng/vách; tăng đệm biên ô bảng thống kê; tự lọc bảng cột động theo tầng (bỏ `C4` đã dừng ở `T1–T2`); đồng bộ cổng `G8.06` và bật tự sinh dim định vị mép cột 2 phương trên `DCE_Setout`.
- **Tiêu chí hoàn thành (DoD):** Tái xuất `KC-02`, `KC-05`, `KC-06`, `KC-07` qua `Form_02` đạt dung lượng **`< 500 KB/tờ`**, giữ đủ `ATTDEF` khung tên thật, có dim `DCE_Setout` 2 phương, 0 va chạm chữ nhãn dầm/bảng, chuyển sang `.dwg` AC1032 với `0` lỗi `AUDIT`.

### 3.3. Giai đoạn 2 — Lắp Ruột Chi tiết BTCT Tham số + BBS vào `Form_04` (`3,0 ngày`)

- **Tệp tác động:** Hợp nhất `dce_dxf_generator.py` + `calc_to_dxf.py` → `cad_rc_detail_engine.py`, nối vào `export_with_open_form(..., form_id="FORM_04_CHITIET_COC_DAM_COT")` tại `cad_paperspace_builder.py`, cập nhật `cad_block_adapters.py` và bộ render ảnh kiểm tra PNG.
- **Trình tự thực hiện:**
  1. Đổ cấu kiện gốc 1:1 trực tiếp vào 3 vùng động của `Form_04_ChiTiet_Coc_Dam_Cot.dxf`:
     - **Vùng `DCE_ZONE_DETAIL_1`:** Mặt bằng đài cọc (`KC-03/04`) hoặc mặt đứng dọc thân cột (`KC-08/09`), chèn Block `Dce_DanhDauThep`, `Dce_CaoTrinh` nằm sẵn trong `Form_04`.
     - **Vùng `DCE_ZONE_DETAIL_2`:** Hai mặt cắt vuông góc đài móng / dầm giằng (`1/25`) hoặc mặt cắt ngang thân cột (`1/25`), chèn Block `DCE_MatCatA`, `Dce_McThepChu`.
     - **Vùng `DCE_ZONE_TABLE`:** Tự động chèn bảng **Thống kê Thép (BBS)** dùng chính hệ Block `TKTitle` + `TK1..TK44` có sẵn trong `Form_04`, bảo đảm sai số giữa chi tiết và bảng thống kê bằng `0%`.
  2. Chuẩn hóa 100% ký hiệu đường kính thép sang mã `%%c` trong DXF/DWG; cấu hình bộ render PNG đổi `%%c → Ø` nét mảnh, loại bỏ chấm đen `●`.
  3. Áp dụng khóa biên an toàn `Safe Margin Box` (khoảng hở `≥ 8 mm` giấy tới khung tên và mép Viewport) cho mọi cao độ (`+10.400`, `+20.200`) và chuỗi dim (`750/640`).
- **Tiêu chí hoàn thành (DoD):** Tái xuất `KC-03, KC-04, KC-08, KC-09` từ `Form_04` kèm tờ BBS Móng và BBS Cột (0% dùng tách vector PDF), đạt **`< 600 KB/tờ`**, **`LINE < 50%`**, **`DIMENSION ≥ 25`**, **`INSERT ≥ 30`**, **0 chấm đen `●`**, **0 cắt mép khung**.

### 3.4. Giai đoạn 3 — Form Mở `PaperSpace 1:1` + 3 Xref + Workbook + Sheet Set `.dst` + Cổng `G8.26–G8.28` (`2,5 ngày`)

- **Tệp tác động:** `cad_form_contract.py`, `cad_form_generator.py`, `cad_xref_builder.py` (mới), `cad_paperspace_builder.py`, `cad_sheet_set.py`, `sheet_set_dst_builder.py` (mới), `dce_cad_compliance_checker.py`.
- **Trình tự thực hiện:**
  1. Mở rộng `Form_01..Form_04` hỗ trợ `source_space: "PAPER"` (`420×297 mm` hoặc `841×594 mm` tỷ lệ `1:1`) trong `cad_form_contract.py` để kỹ sư vừa kéo giãn khung `VIEWPORT` đa tỷ lệ (`1/50` + `1/25`) ngay trên Form mẫu, vừa giữ nguyên toàn bộ bản vẽ ModelSpace ở tỷ lệ thật `1:1 (mm)`.
  2. Xây `cad_xref_builder.py` sinh 3 tệp nền `1:1 (mm)` tại gốc `(0,0,0)`: `Xreft_Luoi.dwg` (`Attachment`), `Xreft_Cot.dwg` (`Overlay` phân layer theo từng tầng), `Khung_A3.dwg` (chèn `1:1` trên PaperSpace).
  3. Nâng cấp `cad_paperspace_builder.py` và `cad_sheet_set.py` sang chế độ `dbim_workbooks`: gom nhiều PaperSpace Layout (`2–8` tờ/tệp) vào các Workbook `.dwg` chuyên môn theo cấu trúc `02.DuAn`; sử dụng `Viewport.frozen_layers` tách thép sàn trên/dưới trên cùng 1 nền ModelSpace.
  4. Xây `sheet_set_dst_builder.py` sinh `sheet_set_manifest.json` sạch (chặn trùng mã tờ như `KC_11` và cấm đường dẫn ổ đĩa cứng), gọi AutoCAD 2021 COM `AcSmSheetSetMgr` đóng gói `DuAn.dst` + điền bảng Danh mục bản vẽ `DMBanVe`.
  5. Bổ sung 3 cổng kiểm toán cứng vào `dce_cad_compliance_checker.py`:
     - **`G8.26` (`NATIVE_DETAIL_ENTITY_GATE`):** Cấm nhánh `DETAIL_VECTOR_RECONSTRUCTED` trong hồ sơ giao nộp; cấm `LINE > 60%` hoặc `DIMENSION == 0` ở bản vẽ chi tiết.
     - **`G8.27` (`PAPERSPACE_XREF_WORKBOOK_GATE`):** Kiểm `PaperSpace_Layouts ≥ 1` ở chế độ Workbook, 100% Xref dùng đường dẫn tương đối tại `(0,0,0)`, `unused_blocks == 0`, và tuân thủ `DCE_AGENT_OWNED` khi re-export qua Form Mở.
     - **`G8.28` (`GLYPH_MARGIN_AND_BBS_SYNC_GATE`):** Quét lỗi chấm đen `●`/font hỏng, kiểm bao `BoundingBox` toàn bộ chữ nằm trong `Safe Margin Box`, và đối soát khối lượng thép chi tiết khớp `100%` với tờ BBS.

---

### 3.5. Bảng Chỉ tiêu Định lượng Mục tiêu (KPI Trước vs. Sau Nâng cấp)

| Chỉ số đo lường (KPI) | Hiện trạng (24/11/2026) | Chuẩn tham chiếu (`02.DuAn`) | Mục tiêu CAD v6.0 |
|---|---|---|---|
| Dung lượng tệp bản vẽ | `2.200 – 4.862 KB / 1 tờ` | `284 – 599 KB / 3–8 tờ` | **`< 600 KB / Workbook (đa tờ)`** |
| Tỷ lệ thực thể `LINE` (bản vẽ chi tiết) | `71,9% – 95,9%` (`13.285 LINE`) | Thấp (ưu tiên Polyline/Block/Hatch) | **`< 50%`** |
| Số `DIMENSION` thật (bản vẽ chi tiết) | `0` (vỡ thành đoạn rời) | Đầy đủ Dim gốc sửa được | **`≥ 25 Dim gốc / bản vẽ`** |
| Số Block `INSERT` (bản vẽ chi tiết) | `1` (chỉ khung tên) | Đầy đủ Block thép, cao trình, TK | **`≥ 30 Block / bản vẽ`** |
| Số lượng `PaperSpace Layout` | `0` (vẽ 100% ModelSpace) | `2 – 8 Layout / Workbook` | **`100% trình bày trên PaperSpace`** |
| Lỗi ký tự `Ø → ●` & cắt mép khung | Có lỗi trên `KC-03`, `KC-08` | `0` lỗi | **`0` lỗi (khóa bởi `G8.28`)** |
| Bảng Thống kê Thép (BBS) đồng bộ | Chưa có | `4` tờ BBS riêng (Móng/Cột/Dầm/Sàn) | **`4` tờ BBS tự sinh, sai số `0%`** |
| Chất lượng Mặt bằng / Chi tiết | `7,5/10` · `4,5/10` | `9,5/10` | **`≥ 9,2/10` · `≥ 9,0/10`** |

---

### 3.6. Danh mục Kiểm tra Nghiệm thu 3 Tầng (Bắt buộc Trước Bàn giao Dual-Agent)

1. **Tầng 1 — Kiểm toán Thực thể CAD Tự động (`SKILL_VERIFY` `G8.01–G8.28`):**
   - `0` tệp sinh từ `DETAIL_VECTOR_RECONSTRUCTED`; `0` thực thể kết cấu rơi vào Layer `0`.
   - `unused_blocks == 0`; `LINE < 50%`, `DIMENSION ≥ 25`, `INSERT ≥ 30` trên mọi tờ chi tiết.
   - `PaperSpace_Layouts ≥ 1`; 100% Xref dùng `Relative Path` chèn đúng tọa độ `(0, 0, 0)`.
2. **Tầng 2 — Kiểm toán Hình học & Trực quan `180 DPI` (Visual Gate):**
   - `0` ký tự `●` lỗi font (100% mã `%%c` hiển thị đúng `Ø`); `0` phần tử chạm hoặc cắt mép khung tên.
   - `0` va chạm nhãn dầm/đài/bảng; bảng cột/móng lọc đúng tầng; đủ dim `DCE_Setout` 2 phương và đủ mặt cắt ngang cột/móng.
3. **Tầng 3 — Kiểm toán Mở Thật & In Ấn trên AutoCAD 2021 (`Production Gate`):**
   - Chuyển đổi `DXF → DWG` qua `accoreconsole.exe` đạt `0` lỗi `AUDIT`/`RECOVER`.
   - Mở `DuAn.dst` trên AutoCAD 2021 đạt `0` liên kết gãy, `0` trùng mã hiệu tờ, bảng `DMBanVe` khớp `100%`.
   - Bấm *Publish* trọn bộ Sheet Set ra PDF A3 bằng `.CTB` chuẩn với độ đậm nhạt nét chính/phụ/hatch rõ ràng.

---

## PHẦN IV. BẢNG PHÂN ĐỊNH TRÁCH NHIỆM (APPROVAL MATRIX)

| Vai trò | Đề xuất | Nhân sự / Thực thể | Tình trạng |
|---|---|---|---|
| **Tổng hợp & Thiết kế Quy trình Nâng cấp** | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Gemini (System Architect) | Đã hoàn tất đặc tả v6.0 |
| **Thực thi nâng cấp mã & Thử nghiệm Cát Lái** | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Gemini (Maker) · Claude (Lead Auditor) | Chờ phê duyệt khởi chạy Sprint 0 |
| **Phê duyệt Quy chuẩn CAD Văn phòng** | Kỹ sư Chủ trì Kết cấu có chứng chỉ hành nghề | Kỹ sư phụ trách | Chờ xác nhận Điều 3 |

---

> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
