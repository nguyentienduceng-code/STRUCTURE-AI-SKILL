---
name: SKILL_GEOTECH
version: 3.1.0
last_updated: 2026-10-21
description: "Kỹ sư Địa kỹ thuật AI: Đánh giá mạng lưới Khảo sát ĐCCT theo TCVN 9363:2012 & TCVN 4419:1987, phân cấp công trình theo TT 34/2026/TT-BXD & QCVN 03:2022/BXD, đánh giá ăn mòn nước ngầm theo TCVN 12041:2017 & TCVN 9346:2012, quy đổi thông số Plaxis, kiểm tra Base Heave, Strut, Waling Beam. Tích hợp Module 17 quy đổi tải trọng Plaxis sang ETABS, Module 18 định dạng bảng ETABS Design Summary."
---

# SKILL_GEOTECH v3.1.0 — Phân tích Địa chất, Đánh giá KSĐC & Thiết kế BPTC (Full TMTT Automation)

## ⚠ ĐỌC TRƯỚC: Đây có đúng là skill cần dùng không?

Skill này đóng vai **Kỹ sư Địa kỹ thuật** — đánh giá hồ sơ Khảo sát địa chất công trình (KSĐC) theo tiêu chuẩn quốc gia và xử lý số liệu thô từ khảo sát ĐCCT thành thông số đầu vào cho phần mềm mô phỏng Plaxis / SAFE / ETABS.

**Nếu User muốn:**
- REVIEW hồ sơ BPTC, lập tờ trình → dùng `Design_Evaluation`
- TÍNH TOÁN kết cấu tường vây, shoring, kiểm tra khả năng chịu lực → dùng `Structural_Design_Engineer`
- ĐIỀU TRA sự cố hố đào → dùng `SKILL_FORENSIC`

Bảng phân xử đầy đủ: `../AGENTS.md` mục 0.

---

## Tổng quan

**SKILL_GEOTECH v3.1.0** tự động hóa toàn bộ quy trình đánh giá KSĐC và chuyển đổi số liệu thí nghiệm sang **thông số đầu vào trực tiếp cho Plaxis**:

1. **Đánh giá Hồ sơ Khảo sát Địa chất (KSĐC) & Phân cấp Công trình (MỚI v3.1):**
   - Phân cấp công trình xây dựng theo **Thông tư 34/2026/TT-BXD** (hiệu lực 01/07/2026, đối chiếu chuyển tiếp **Thông tư 06/2021/TT-BXD**) và phân cấp phục vụ thiết kế (Cấp hậu quả `C1, C2, C3`, Thời hạn sử dụng `Mức 1–4`) theo **QCVN 03:2022/BXD** & **TCVN 2737:2023 (Bảng H.1)**.
   - Xác định Cấp phức tạp điều kiện địa chất công trình (`Cấp I, II, III`) theo **Điều 3.5 & Phụ lục 2 TCVN 4419:1987**.
   - Kiểm tra mật độ, khoảng cách, chiều sâu hố khoan và tỷ lệ hố khoan khống chế ($\ge 1/3$) theo **TCVN 9363:2012** (Bước TKCS: Điều 5.2.4.2 & Phụ lục C; Bước TKKT: Điều 5.3.6, Phụ lục D & Bảng D.1).
   - Đánh giá mức độ ăn mòn hóa học của nước ngầm đối với bê tông và BTCT theo **TCVN 12041:2017** và **TCVN 9346:2012** *(thay thế TCVN 3994:1985 đã hết hiệu lực)*.
2. Xử lý dữ liệu thô SPT/CPT/CPTu từ báo cáo khảo sát ĐCCT.
3. Tính ứng suất hữu hiệu, K0 (kể cả đất quá cố kết OCR) theo Mayne & Kulhawy.
4. **Tương quan E50 tối ưu:**
   - Đất dính: `E50 = Ke × Su` (Ke theo Ip, nguồn Jamiolkowski/CIRIA C760)
   - Đất rời: `E50 = α × N_SPT` (Bowles 1997/CIRIA C760)
5. Xuất thông số cho mô hình Mohr-Coulomb, Hardening Soil, và Soft Soil Creep.
6. **Kiểm tra ổn định đáy hố đào (Base Heave)** theo Terzaghi + Bjerrum-Eide với bước tính số cụ thể.
7. **Kiểm tra ổn định thanh chống (Strut Buckling)** với Lambda, Phi, N_Rd.
8. Quy đổi kết cấu chắn giữ (có xét Stiffness Degradation).
9. Kiểm chứng Ground Truth với bảng so sánh % deviance.
10. Kiểm chứng giới hạn chuyển vị (SLS - Clough & O'Rourke).
11. Phân tích sức chịu tải cọc (Davisson, Chin-Kondner).

**Tiêu chuẩn áp dụng chuẩn xác:**
- **Thông tư 34/2026/TT-BXD** (hiệu lực 01/07/2026, thay thế TT 06/2021/TT-BXD & TT 02/2025/TT-BXD) — Quy định chi tiết về cấp công trình xây dựng
- **QCVN 03:2022/BXD** — Phân cấp công trình phục vụ thiết kế xây dựng (Cấp hậu quả C1–C3, Thời hạn sử dụng Mức 1–4)
- **TCVN 9363:2012** — Khảo sát cho xây dựng – Khảo sát địa kỹ thuật cho nhà cao tầng
- **TCVN 4419:1987** — Khảo sát cho xây dựng – Nguyên tắc cơ bản
- **TCVN 9351:2022** (thay thế TCVN 9351:2012) — Đất xây dựng – Phương pháp thí nghiệm hiện trường – Thí nghiệm xuyên tiêu chuẩn (SPT)
- **TCVN 12041:2017 & TCVN 9346:2012** (thay thế TCVN 3994:1985) — Bảo vệ chống ăn mòn cho kết cấu bê tông và BTCT
- **TCVN 9362:2012, TCVN 10304:2025, TCVN 2737:2023, TCVN 5574:2018, TCVN 5575:2024, Eurocode 7, CIRIA C760**

---

## QUY CHUẨN BẮT BUỘC KHI ĐÁNH GIÁ HỒ SƠ KSĐC & PHÂN CẤP CÔNG TRÌNH (MỚI v3.1.0)

> **CẢNH BÁO CHỐNG SAI LỆCH PHÁP LÝ:** Mọi báo cáo đánh giá KSĐC, đề cương khảo sát bổ sung và thuyết minh địa kỹ thuật BẮT BUỘC tuân thủ chính xác các điều khoản và con số dưới đây (nghiêm cấm tự suy diễn tên bảng/điều khoản):

### A. Phân cấp Công trình Xây dựng & Cấp Hậu quả Thiết kế
1. **Cấp công trình phục vụ quản lý hoạt động xây dựng (`Thông tư 34/2026/TT-BXD` & `Thông tư 06/2021/TT-BXD`)**:
   - Tra theo **Phụ lục I** (quy mô công suất/tầm quan trọng) và **Bảng 2 Phụ lục II** (quy mô kết cấu — **Phụ lục II chỉ có Bảng 2**, tuyệt đối không ghi *"Bảng 1 Phụ lục II"*).
   - Đối với **Nhà, Kết cấu dạng nhà (Mục 2.1.1 Bảng 2 Phụ lục II)**:
     - **a) Chiều cao (m)**: Đặc biệt `> H*` (`150m` hoặc `200m`) | Cấp I `> 75 ÷ H*` | Cấp II `> 28 ÷ 75` | Cấp III `> 6 ÷ 28` | Cấp IV `≤ 6`.
     - **b) Số tầng cao**: Đặc biệt `> 50` | Cấp I `25 ÷ 50` | Cấp II `8 ÷ 24` | Cấp III `2 ÷ 7` | Cấp IV `1`.
     - **c) Tổng diện tích sàn GFA (nghìn m²)**: Cấp I **`> 30`** (`> 30,000 m²`, **không phải ngưỡng 100,000 m²**) | Cấp II `> 10 ÷ 30` | Cấp III `1 ÷ 10` | Cấp IV `< 1`.
     - **d) Nhịp kết cấu lớn nhất (m)**: Đặc biệt `> 200` | Cấp I `100 ÷ 200` | Cấp II `50 ÷ < 100` | Cấp III `15 ÷ < 50` | Cấp IV `< 15`.
     - **đ) Độ sâu ngầm (m)** *(tính từ cốt mặt đất đặt công trình tới **mặt trên của sàn tầng hầm sâu nhất**, theo điểm k Ghi chú Bảng 2 Phụ lục II)*: Cấp I `> 18` | Cấp II **`6 ÷ 18`** | Cấp III `< 6` *(Lưu ý: Tuyệt đối không trích dẫn nhầm sang Bảng 1.2 Phụ lục I vì Bảng 1.2 là Công trình sản xuất công nghiệp)*.
     - **e) Số tầng ngầm**: Cấp I `≥ 5` | Cấp II `2 ÷ 4` | Cấp III `1`.
2. **Phân cấp phục vụ thiết kế xây dựng (`QCVN 03:2022/BXD` & `TCVN 2737:2023`)**:
   - **Cấp hậu quả (`C1` thấp, `C2` trung bình, `C3` cao)**: Quy định tại **Mục 2.1 và Phụ lục A QCVN 03:2022/BXD** (không có *"Bảng 1.1 QCVN 03:2022/BXD"*) và **Bảng H.1 Phụ lục H TCVN 2737:2023** ($\gamma_n = 0.87$ cho C1; $1.00$ cho C2; $1.15$ cho C3). Tuyệt đối dùng ký hiệu **`C1, C2, C3`**, không dùng `CC1, CC2, CC3` (ký hiệu của Eurocode). Trung tâm thương mại có tổng diện tích sàn kinh doanh `> 30,000 m²` thuộc cấp **`C3`** theo **Mục A.1.1.3 Phụ lục A QCVN 03:2022/BXD**.
   - **Thời hạn sử dụng theo thiết kế (Tuổi thọ thiết kế)**: Quy định tại **Mục 2.2.2 Bảng 1 QCVN 03:2022/BXD**:
     - **Mức 1 (`< 25 năm`)**: Công trình tạm (Mục A.2 Phụ lục A).
     - **Mức 2 (`≥ 25 năm`)**: Công trình chịu tác động trực tiếp của môi trường xâm thực mạnh (hóa chất, biển).
     - **Mức 3 (`≥ 50 năm`)**: **Các công trình dân dụng, công nghiệp, hạ tầng kỹ thuật thông thường** (không thuộc Mức 1, 2, 4).
     - **Mức 4 (`≥ 100 năm`)**: Chỉ bắt buộc đối với nhà và công trình độc đáo, có giá trị kiến trúc hoặc mang ý nghĩa biểu tượng quan trọng (Bảo tàng quốc gia, sân vận động quốc gia/quốc tế, nhà hát quốc gia, công trình điểm nhấn đặc biệt...) hoặc khi Chủ đầu tư quy định riêng trong Nhiệm vụ thiết kế.

### B. Tiêu chuẩn Khảo sát Địa kỹ thuật (`TCVN 9363:2012` & `TCVN 4419:1987`)
1. **Tên chuẩn của `TCVN 9363:2012`**: *"Khảo sát cho xây dựng – Khảo sát địa kỹ thuật cho nhà cao tầng"* (không có cụm từ *"và công trình ngầm"*).
2. **Cấp mức độ phức tạp điều kiện địa chất công trình (`Cấp I` - Đơn giản, `Cấp II` - Trung bình, `Cấp III` - Phức tạp)**:
   - Quy định tại **Điều 3.5 và Phụ lục 2 `TCVN 4419:1987`**, được dẫn chiếu tại **Chú thích Điều 5.2.4.1 `TCVN 9363:2012`** (không phải Điều 4.2 TCVN 9363:2012 — Điều 4.2 chỉ quy định các giai đoạn khảo sát).
   - Nguyên tắc bố trí điểm thăm dò theo các trục chính hoặc chu vi công trình ở bước TKKT/BVTC nằm tại **Điều 3.19 `TCVN 4419:1987`** (không phải Điều 3.4 & Bảng 2).
3. **Quy định mạng lưới, khoảng cách và chiều sâu hố khoan theo `TCVN 9363:2012`**:
   - **Giai đoạn Thiết kế cơ sở (TKCS)**:
     - **Khoảng cách điểm khảo sát (Điều 5.2.4.2)**: Thường dao động từ **`50 m đến 200 m`** (không phải khống chế cứng `50m – 100m`, và không có *"Bảng 1"* trong TCVN 9363:2012).
     - **Chiều sâu điểm thăm dò (Điều 5.2.5 & Phụ lục C)**: Với điều kiện địa chất phức tạp, công trình quan trọng quy mô lớn (**Mục C.1**): nếu gặp đất yếu phải khoan qua đất yếu, **1/2 số điểm khoan vào đất tốt ít nhất 3 m ($N_{SPT} > 30$)**; mỗi hạng mục/đơn nguyên có ít nhất 1 hố khoan khống chế.
   - **Giai đoạn Thiết kế kỹ thuật (TKKT)**:
     - **Khoảng cách điểm thăm dò (Điều 5.3.6, Phụ lục D & Bảng D.1)**:
       - **Mục D.1 Phụ lục D** (Điều kiện địa chất phức tạp - Cấp III, công trình quan trọng nhạy cảm lún/lún lệch): Khoảng cách khoan thông thường từ **`20 m đến 30 m`**; có thể bổ sung xuyên tĩnh cách nhau trung bình `10 m`; trường hợp đặc biệt khoanh vùng đất yếu/karst có thể `< 20 m`; tối thiểu 3 điểm cho 1 nhà riêng rẽ và 3–5 điểm cho 1 cụm công trình.
       - **Bảng D.1 Phụ lục D**: Với điều kiện địa chất Cấp III, lưới khoan là **`30m × 30m`** (nhà dưới 9 tầng hoặc dưới 16 tầng tải cột $\le 2,000\text{ T}$, tối thiểu 3–4 hố/nhà) hoặc **`20m × 20m`** (nhà 16–28 tầng hoặc công trình có tải cột khung $> 2,000\text{ T}$, tối thiểu 5 hố/nhà).
     - **Tỷ lệ hố khoan khống chế bắt buộc (Điều 5.3.6.3)**: Số lượng điểm khảo sát khống chế **không được ít hơn 1/3 (`33.3%`)** tổng số điểm khảo sát! *(Khi lập đề cương khoan bổ sung bước TKKT, bắt buộc kiểm tra: $\text{Tổng số hố khống chế (cũ + mới)} \ge \frac{1}{3} \times \text{Tổng số hố khảo sát (cũ + mới)}$)*.
     - **Tỷ lệ điểm khoan lấy mẫu và thí nghiệm hiện trường (Điều 5.3.6.4)**: Không ít hơn **2/3 (`66.7%`)** tổng số điểm khảo sát.
     - **Chiều sâu và phạm vi khảo sát cho hố đào sâu (Điều 5.3.7.6)**: Độ sâu thăm dò lấy từ **`2 đến 3 lần` chiều sâu hố đào**; phạm vi mặt bằng khảo sát rộng hơn phạm vi hố đào từ `2 đến 3 lần` chiều sâu hố đào.
4. **Đánh giá tính ăn mòn / xâm thực của nước ngầm đối với bê tông và BTCT**:
   - Bắt buộc viện dẫn **`TCVN 12041:2017`** (*Kết cấu bê tông và bê tông cốt thép - Yêu cầu chung về thiết kế độ bền lâu và tuổi thọ trong môi trường xâm thực*) và **`TCVN 9346:2012`** *(thay thế hoàn toàn `TCVN 3994:1985` đã hết hiệu lực)*.

---

## Khi Cần Protocol Chi Tiết — Lazy Load

| Nhu cầu | File cần đọc |
|---------|-------------|
| Công thức gốc, bảng Ke/α, tương quan SPT & chuẩn KSĐC TCVN 9363:2012 | `references/GEOTECH_GUIDE.md` |
| Hướng dẫn nhập liệu Plaxis chi tiết | `references/PLAXIS_MODEL_GUIDE.md` |
| Template TMTT BPTC chuẩn | `references/THUYET_MINH_TEMPLATE.md` |
| Hướng dẫn mô hình ETABS cho hệ Shoring | `references/ETABS_SHORING_GUIDE.md` |
| Phụ lục giải trình từng bước | `SKILL_SOIL_PARAMS.md` |

---

| Module | File | Chức năng |
|--------|------|-----------|
| **MODULE 1** | `calc_geostatic_stress.py` | Tính σ_v, u, σ'_v, K0, σ'_h; bổ sung `calc_layer_boundary_stress()` cho ranh giới lớp |
| **MODULE 2** | `calc_soil_params_mc.py` | Xuất bộ thông số Mohr-Coulomb |
| **MODULE 3** | `calc_soil_params_hs.py` | Xuất bộ thông số Hardening Soil |
| **MODULE 4** | `calc_structural_elements.py` | Quy đổi DW/Cừ/Strut → EA, EI |
| **MODULE 5** | `calc_spt_correlations.py` | Tương quan SPT → c, φ, E50 (**v2.3: tách Ke×Su cho đất dính, α×N cho đất rời**) |
| **MODULE 6** | `calc_cpt_interpretation.py` | Phân tích CPTu → qt, Bq, Su, SBT 2016, Nkt |
| **MODULE 7** | `calc_soil_params_ssc.py` | Quy đổi Oedometer → Soft Soil Creep (λ*, κ*, μ*) |
| **MODULE 8** | `calc_pile_load_test.py` | Phân tích nén tĩnh cọc (Davisson, Chin-Kondner) |
| **MODULE 9** | `calc_psr.py` | Tính Plane Strain Ratio (PSR) cho hố đào 3D |
| **MODULE 10** | `SKILL_SOIL_PARAMS.md` | Phụ lục giải trình từng bước — Template đầy đủ theo Rule 7.1 |
| **MODULE 11** | `calc_base_heave.py` | Kiểm tra ổn định đáy hố đào (Terzaghi + Bjerrum-Eide) |
| **MODULE 12** | `calc_strut_capacity.py` | Kiểm tra ổn định thanh chống thẳng (Lambda, Phi, N_Rd) |
| **MODULE 12b** | `calc_waling_beam_capacity.py` | Kiểm tra khả năng chịu uốn Dầm bo (Waling Beam) — nhịp tự do, M_max, η, L_max_safe |
| **MODULE 13** | `assess_excavation_geometry.py` | Phân tích hình học mặt bằng hố đào — xác định cạnh nguy hiểm nhất, tính nhịp tự do từng cạnh |
| **MODULE 15** | `calc_corner_brace.py` | Tính toán hệ chống góc xiên (Corner Brace/Raking Strut) |
| **MODULE 16** | `calc_plaxis_model_geometry.py` | Tính toán kích thước mô hình Plaxis (Bounding Box, ảnh hưởng biên CIRIA C760) |
| **MODULE 17** | `plaxis_to_etabs_handoff.py` | Quy đổi nội lực từ Plaxis sang tải phân bố $q$ (kN/m) cho ETABS |
| **MODULE 18** | `format_etabs_output.py` | Định dạng bảng ETABS Design Summary → Markdown/Word |
| **VERIFY 1** | `verify_against_ground_truth.py` | So sánh E50 với Ground Truth, cảnh báo W001 |
| **VERIFY 2** | `verify_serviceability_limits.py` | Kiểm tra chuyển vị ngang hố đào (SLS - Clough & O'Rourke) |
| **EXPORT** | `export_geotech_report.py` | Xuất Thuyết minh (MD) + Bảng tính Plaxis (XLSX 12 sheets) |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **3.1.0** | **2026-10-21** | **Chuẩn hóa Pháp lý Phân cấp & Khảo sát ĐCCT**: Cập nhật Thông tư 34/2026/TT-BXD (Bảng 2 Phụ lục II), QCVN 03:2022/BXD (Cấp hậu quả C1–C3, Niên hạn Mức 1–4 tại Bảng 1), TCVN 9363:2012 (Điều 5.2.4.2 cự ly TKCS 50–200m; Điều 5.3.6 & Phụ lục D cự ly TKKT 20–30m; Điều 5.3.6.3 tỷ lệ hố khống chế ≥ 1/3), TCVN 4419:1987 (Điều 3.5 & Phụ lục 2; Điều 3.19), TCVN 9351:2022 và TCVN 12041:2017 / TCVN 9346:2012 (thay thế TCVN 3994:1985). |
| **3.0.0** | **2026-09-19** | **Full TMTT Automation** — Nâng cấp toàn diện `THUYET_MINH_TEMPLATE.md` thành Template 6 Chương + Phụ lục A bắt buộc + MODULE 18. |
| 2.4.0 | 2026-09-18 | Urban Excavation Upgrade — MODULE 12b (Waling Beam), MODULE 13 (Geometry), MODULE 15 (Corner Brace). |
