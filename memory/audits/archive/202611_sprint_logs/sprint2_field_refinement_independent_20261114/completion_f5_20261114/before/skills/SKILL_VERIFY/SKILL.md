---
name: SKILL_VERIFY
version: 3.3.0
last_updated: 2026-11-09
updated: 2026-11-09
status: PRODUCTION_READY
description: >
  Hệ thống Kiểm chứng Độc lập 8 Bộ lọc (EMF Vector Extractor, Load & Combination Auditor,
  ETABS Joint Reaction Tracer, Rebar Area Calculator, Drawing Geometry Sync, Excel Formula Checker,
  CAD Graph Reader & DCE Pro CAD Compliance Auditor).
---

# SKILL_VERIFY — BỘ KIỂM CHỨNG ĐỘC LẬP 8 TẦNG (v3.3.0)

## 8 BỘ LỌC KIỂM CHỨNG TỰ ĐỘNG BẮT BUỘC (`drawing_calc_crosscheck.py` & `dce_cad_compliance_checker.py`)
1. **Bộ lọc 1 — Trích xuất Dữ liệu Gốc từ Bảng tính EMF/Vector (`EMF Deep Parser`):** Giải nén `word/media/image*.emf` trong toàn bộ file thuyết minh `.docx` để đọc 100% chuỗi văn bản UTF-16LE từ Excel / Young Steel / Ketcausoft.
2. **Bộ lọc 2 — Kiểm toán Tải trọng & Tổ hợp Tải trọng (`Load & Combination Auditor`):**
   - Phát hiện công thức gió tự chế ($G_f = 0.85+h/1010$), thiếu áp lực gió trong nhà ($c_i$), nhập `Gió = 0` trong bảng tính xà gồ, dùng $\gamma_f = 1.1$ kèm tải Solar khi tính gió bốc, hoặc tổ hợp bể ngầm tự triệt tiêu áp lực nước và đất.
3. **Bộ lọc 3 — Kiểm toán Sơ đồ Tính & Điều kiện Biên (`Mechanics & Boundary Auditor`):**
   - So sánh giả định `Chân khớp / Chân ngàm`, chiều dài tính toán $L_x, L_y, L_{ef}$ (`Liên kết cánh chịu nén: Có`) và sườn tăng cứng trong bảng tính với cấu tạo thực tế trên bản vẽ.
4. **Bộ lọc 4 — Truy vết Phản lực Nút ETABS (`Joint Reactions`) sang Bảng tính Móng:**
   - Kiểm tra chéo $F_z, M_x, M_y$ tại nút chân cột giữa và cột biên với giá trị nhập vào bảng tính móng; kiểm tra điều kiện khử ứng suất kéo đáy móng ($\sigma_{\min} \ge 0$) và chống đẩy nổi Archimedes ($K_{\text{đn}} \ge 1.15$).
5. **Bộ lọc 5 — Đối soát Hàm lượng Cốt thép & Kích thước Hình học 4 Chiều (`4-Way Drawing-Tag-Calc Sync`):**
   - Tự động tính diện tích cốt thép trên bản vẽ $A_{s,\text{drawing}}$ so với $A_{s,tt}$ yêu cầu; kiểm tra độ lệch tâm cổ cột $e_0$ trên Mặt bằng vs Mặt cắt; kiểm đếm tờ bản vẽ bị thiếu.
6. **Bộ lọc 6 — Quét Lỗi Công thức Bảng tính (`Formula & Merged-Cell Integrity Check`):**
   - Bắt mọi lỗi `#VALUE!`, `#REF!`, ô gộp làm mất công thức liên kết giữa các sheet và lỗi lệch số tiền bằng số — bằng chữ.
7. **Bộ lọc 7 — Kiểm chứng Đồ thị Không gian CAD & Bắt lỗi Sửa Số Kích thước Giả (`cad_deep_reader.py` v1.1.0):**
   - Giải mã trực tiếp file `.dwg/.dxf` (phẳng hóa Block lồng nhau `*U...` bằng ma trận $4\times 4$ về WCS, chuyển mã `TCVN3 / VNI / SHX` sang UTF-8), tự động đo độ lệch tâm hình học thực tế $e_0$ của đài móng/cổ cột từ tọa độ đỉnh đa giác và bắt sống lỗi gõ đè số kích thước giả (`Dimension Text Override`: $|\text{Dim\_Text} - \text{Actual\_Measurement}| > 2\%$).
8. **Bộ lọc 8 — Kiểm toán Tuân thủ Chuẩn CAD DCE Pro & Graphic Sanity Auditor (`dce_cad_compliance_checker.py` v2.0.0 — Điều 12d AGENTS.md):**
   - Kiểm toán toàn diện file `.dxf` xuất xưởng:
     + Chặn đứng 100% layer tự chế phi chuẩn (`0_TRUC`, `0_COT`, `0_VACH`, `0_DAM`, `0_DIM`...). Bắt buộc toàn bộ cấu kiện nằm trên hệ layer `DCE_*` (`DCE_Truc`, `DCE_BaoBeTong`, `DCE_Hatch`, `DCE_Beam`, `DCE_Dim`, `DCE_Name`, `Dce_text`, `DCE_Frame`, `DCE_Schedule`, `DCE_Setout`...).
     + Kiểm tra Khối thuộc tính (Attribute Blocks): Bong bóng trục bắt buộc là Block `Dce_KhTenTruc` / `Dce_TenTruc` (ATTDEF `TRUC`); tên cấu kiện bắt buộc là Block `TenCauKien` / `DCE_Name`; tiêu đề bắt buộc là Block `DCE_Plan header 1` / `TKTitle`. Cấm vẽ primitives vòng tròn/text trần.
     + Kiểm tra Thứ nguyên DimStyle: Đường kích thước phải dùng DimStyle chuẩn `Dce_*MV` (như `Dce_100MV`) với mũi tên kiến trúc `_ArchTick`.
     + Kiểm toán Đồ họa Kỹ thuật (Graphic Sanity): Quét lỗi dầm chạy xuyên suốt mặt bằng / đâm xuyên qua buồng thang máy, bắt buộc Solid Hatch bê tông xám cho 100% cột/vách, kiểm tra thứ tự 4 tầng biên ngoài và sự hiện diện của Khung bản vẽ A1 + Bảng thống kê cột vách.
     + Kiểm toán Audit Cú pháp: Đảm bảo 0 lỗi syntax / undefined linetypes, ngăn chặn 100% lỗi AutoCAD từ chối mở (`Drawing Discarded`).
