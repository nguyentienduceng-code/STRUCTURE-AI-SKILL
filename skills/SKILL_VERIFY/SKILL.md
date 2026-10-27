---
name: SKILL_VERIFY
version: 3.2.0
updated: 2026-10-25
status: PRODUCTION_READY
description: >
  Hệ thống Kiểm chứng Độc lập 6 Bộ lọc (EMF Vector Extractor, Load & Combination Auditor,
  ETABS Joint Reaction Tracer, Rebar Area Calculator, Drawing Geometry Sync & Excel Formula Checker).
---

# SKILL_VERIFY — BỘ KIỂM CHỨNG ĐỘC LẬP 7 TẦNG (v3.2.0)

## 7 BỘ LỌC KIỂM CHỨNG TỰ ĐỘNG BẮT BUỘC (`drawing_calc_crosscheck.py`)
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
