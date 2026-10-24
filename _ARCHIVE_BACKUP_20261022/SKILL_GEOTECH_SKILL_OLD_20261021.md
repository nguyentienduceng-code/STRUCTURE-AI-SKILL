---
name: SKILL_GEOTECH
version: 3.0.0
last_updated: 2026-09-27
description: "Kỹ sư Địa kỹ thuật AI: Phân tích số liệu khảo sát ĐCCT, quy đổi thông số Plaxis. Kiểm tra Base Heave, Strut, Waling Beam. Tích hợp Module 17 quy đổi tải trọng từ Plaxis sang ETABS, Module 18 định dạng bảng ETABS Design Summary. Tự động sinh TMTT BPTC đầy đủ 6 Chương + Phụ lục A bắt buộc. Cung cấp bộ thông số Cừ thép chuẩn JIS A 5528."
---

# SKILL_GEOTECH v3.0.0 — Phân tích Địa chất & Thiết kế BPTC (Full TMTT Automation)

## ⚠ ĐỌC TRƯỚC: Đây có đúng là skill cần dùng không?

Skill này đóng vai **Kỹ sư Địa kỹ thuật** — xử lý số liệu thô từ khảo sát ĐCCT và quy đổi thành thông số đầu vào cho phần mềm mô phỏng Plaxis.

**Nếu User muốn:**
- REVIEW hồ sơ BPTC, lập tờ trình → dùng `Design_Evaluation`
- TÍNH TOÁN kết cấu tường vây, shoring, kiểm tra khả năng chịu lực → dùng `Structural_Design_Engineer`
- ĐIỀU TRA sự cố hố đào → dùng `SKILL_FORENSIC`

Bảng phân xử đầy đủ: `../AGENTS.md` mục 0.

---

## Tổng quan

**SKILL_GEOTECH v3.0.0** tự động hóa toàn bộ quy trình chuyển đổi từ số liệu thí nghiệm sang **thông số đầu vào trực tiếp cho Plaxis**, bao gồm:

1. Xử lý dữ liệu thô SPT/CPT/CPTu từ báo cáo khảo sát ĐCCT.
2. Tính ứng suất hữu hiệu, K0 (kể cả đất quá cố kết OCR) theo Mayne & Kulhawy.
3. **Tương quan E50 tối ưu:**
   - Đất dính: `E50 = Ke × Su` (Ke theo Ip, nguồn Jamiolkowski/CIRIA C760)
   - Đất rời: `E50 = α × N_SPT` (Bowles 1997/CIRIA C760)
4. Xuất thông số cho mô hình Mohr-Coulomb, Hardening Soil, và Soft Soil Creep.
5. **Kiểm tra ổn định đáy hố đào (Base Heave)** theo Terzaghi với bước tính số cụ thể.
6. **Kiểm tra ổn định thanh chống (Strut Buckling)** với Lambda, Phi, N_Rd.
7. Quy đổi kết cấu chắn giữ (có xét Stiffness Degradation).
8. Kiểm chứng Ground Truth với bảng so sánh % deviance.
9. Kiểm chứng giới hạn chuyển vị (SLS - Clough & O'Rourke).
10. Phân tích sức chịu tải cọc (Davisson, Chin-Kondner).

**Tiêu chuẩn:** TCVN 9351:2012, Eurocode 7, CIRIA C760, ASTM D1143, TCVN 5575:2024.

## Khi Cần Protocol Chi Tiết — Lazy Load

> **KHÔNG đọc ngay** — Chỉ đọc khi thực sự cần:

| Nhu cầu | File cần đọc |
|---------|-------------|
| Công thức gốc, bảng Ke/α, tương quan SPT | `references/GEOTECH_GUIDE.md` |
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
| **MODULE 12b** | `calc_waling_beam_capacity.py` | **MỚI v2.4:** Kiểm tra khả năng chịu uốn Dầm bo (Waling Beam) — nhịp tự do, M_max, η, L_max_safe |
| **MODULE 13** | `assess_excavation_geometry.py` | **MỚI v2.4:** Phân tích hình học mặt bằng hố đào — xác định cạnh nguy hiểm nhất, tính nhịp tự do từng cạnh, hình học thanh chống góc |
| **MODULE 15** | `calc_corner_brace.py` | **MỚI v2.4:** Tính toán hệ chống góc xiên (Corner Brace/Raking Strut) — chiều dài, góc, phân giải lực, kiểm tra buckling |
| **MODULE 16** | `calc_plaxis_model_geometry.py` | **MỚI v2.4:** Tính toán kích thước mô hình Plaxis (Bounding Box, ảnh hưởng biên CIRIA C760) |
| **MODULE 17** | `plaxis_to_etabs_handoff.py` | **MỚI v2.5:** Quy đổi nội lực từ Plaxis sang tải phân bố $q$ (kN/m) cho ETABS. Hướng dẫn thiết lập ETABS Shoring |
| **MODULE 18** | `format_etabs_output.py` | **MỚI v3.0:** Định dạng bảng ETABS Design Summary → Markdown/Word cẩn đẹ, tô màu Ratio, kết luận tự động |
| **VERIFY 1** | `verify_against_ground_truth.py` | So sánh E50 với Ground Truth, cảnh báo W001 |
| **VERIFY 2** | `verify_serviceability_limits.py` | Kiểm tra chuyển vị ngang hố đào (SLS - Clough & O'Rourke) |
| **EXPORT** | `export_geotech_report.py` | Xuất Thuyết minh (MD) + Bảng tính Plaxis (XLSX 12 sheets với Sheet 12 Phụ lục) |

---

## Quy tắc Điều phối (Dispatcher Logic)

### → Kích hoạt MODULE 5 + MODULE 1 + MODULE 2/3 (Full Pipeline) khi:
- User cung cấp bảng số liệu SPT đầy đủ từ hố khoan và muốn ra "bộ thông số Plaxis".
- Keywords: *phân tích địa chất, thông số đất cho Plaxis, input Plaxis, tương quan SPT*

### → Kích hoạt MODULE 11 (Base Heave) khi:
- User cần kiểm tra ổn định đáy hố đào.
- Keywords: *Base Heave, ổn định đáy hố, Terzaghi, Fs đáy hố*

### → Kích hoạt MODULE 12 (Strut Capacity) khi:
- User cần kiểm tra khả năng chịu lực thanh chống.
- Keywords: *Strut, thanh chống, buckling, N_Rd, lambda, kiểm tra ổn định*

### → Kích hoạt MODULE 6 khi:
- User có dữ liệu CPT (qc, fs theo chiều sâu).
- Keywords: *CPT, xuyên tĩnh, cone penetration, qc, fs*

### → Kích hoạt MODULE 12b (Waling Beam Check) khi:
- User hỏi về khả năng chịu lực dầm bo, nhịp dầm bo, waling beam gãy.
- Keywords: *dầm bo, waling beam, nhịp tự do dầm bo, M dầm bo, dầm bo gãy, I200 gãy*

### → Kích hoạt MODULE 13 (Geometry Assessment) — BẮT BUỘC KHI DỰ ÁN MỚI:
- Trigger tự động: Ngay khi User cung cấp kích thước hố đào (L × W) và mô tả các cạnh.
- Keywords: *mặt bằng hố đào, các cạnh hố đào, vách hiện hữu, giáp ranh, sát tòa nhà*
- **Bắt buộc chạy trước MODULE 12 và 12b.**

### → Kích hoạt MODULE 15 (Corner Brace) khi:
- User hỏi về thanh chống góc xiên, raking strut, mở rộng góc chống.
- Keywords: *chống góc, corner brace, raking strut, thanh xiên, góc chống, chiều dài thanh chống góc*

### → Kích hoạt MODULE 17 (ETABS Handoff) khi:
- User hỏi cách mô hình ETABS cho dầm bo, thanh chống, hỏi cách chuyển lực từ Plaxis sang ETABS, hoặc cách gán liên kết ngàm/khớp trong ETABS.
- Keywords: *ETABS, gán tải ETABS, chuyển Plaxis sang ETABS, khóa liên kết, release ETABS, ngàm khớp thanh chống*

### → Kích hoạt MODULE 18 (ETABS Design Summary Format) khi:
- User cần xuất bảng kết quả Design Summary từ ETABS ra báo cáo, hoặc dán bảng ETABS vào TMTT.
- Keywords: *bảng ETABS, Design Summary, PMM Ratio, D/C Ratio, kết quả kiểm tra thép ETABS*

### → Kích hoạt ADJACENT STRUCTURE PROTOCOL (Giao thức Công trình Lân cận) khi:
- Có vách, móng, cọc hiện hữu trong phạm vi 2H từ mép hố đào.
- Keywords: *sát tòa nhà, giáp ranh, vách hiện hữu, móng cọc lân cận, lún nhà bên cạnh, không ép được cừ*
- Quy trình bắt buộc:
  1. Chạy MODULE 13 (Geometry Assessment) — xác định cạnh nào bị ảnh hưởng.
  2. Kiểm tra setback distance: Nếu khoảng cách < H (chiều sâu hố đào) → cảnh báo Zone of Influence.
  3. Đánh giá từng cạnh: Vách bê tông hiện hữu → loại bỏ ngay rủi ro cạnh đó. Cọc/đài hiện hữu → cảnh báo không ép cừ được, đề xuất biện pháp thay thế.

### → Full Pipeline (khi User cung cấp báo cáo ĐCCT đầy đủ):
```
Input ĐCCT + Kích thước hố đào
  → MODULE 13 (Geometry Assessment — BẮT BUỘC ĐẦU TIÊN)
  → MODULE 5 (tương quan SPT với Ke×Su / α×N)
  → Ground Truth Verification (Check W001)
  → MODULE 1 (ứng suất ranh giới lớp)
  → MODULE 11 (Base Heave check)
  → MODULE 2 hoặc 3 (thông số đất)
  → MODULE 4 (kết cấu)
  → MODULE 12 (Strut capacity — chống thẳng)
  → MODULE 12b (Waling Beam — SONG SONG với MODULE 12)
  → MODULE 15 (Corner Brace — nếu có hệ chống góc)
  → JSON Output → Review Gate → Bảng tổng hợp
```

---

## Cấu trúc Thư mục

```
SKILL_GEOTECH/
├── SKILL.md                              ← BẠN ĐANG Ở ĐÂY (Entry Point)
├── SKILL_SOIL_PARAMS.md                  ← Quy trình tính thông số đất + PHỤ LỤC GIẢI TRÌNH (Section 6)
├── references/
│   ├── GEOTECH_GUIDE.md                 ← Công thức gốc, bảng Ke/α, nguồn tham khảo (v2.3 mở rộng)
│   ├── PLAXIS_MODEL_GUIDE.md            ← Hướng dẫn nhập liệu Plaxis chi tiết
│   └── THUYET_MINH_TEMPLATE.md          ← Template Thuyết minh BPTC (8 mục)
├── scripts/
│   ├── calc_geostatic_stress.py           ← MODULE 1: Ứng suất hữu hiệu + boundary stress
│   ├── calc_soil_params_mc.py            ← MODULE 2: Mohr-Coulomb params
│   ├── calc_soil_params_hs.py             ← MODULE 3: Hardening Soil params
│   ├── calc_structural_elements.py         ← MODULE 4: DW/Cừ/Strut (v2.5: Thư viện Cừ JIS A 5528)
│   ├── calc_spt_correlations.py           ← MODULE 5: SPT correlations
│   ├── calc_cpt_interpretation.py        ← MODULE 6: CPT interpretation
│   ├── calc_soil_params_ssc.py            ← MODULE 7: Soft Soil Creep params
│   ├── calc_pile_load_test.py             ← MODULE 8: Pile load test analysis
│   ├── calc_psr.py                        ← MODULE 9: Plane Strain Ratio
│   ├── calc_base_heave.py                 ← MODULE 11: Base Heave check
│   ├── calc_strut_capacity.py             ← MODULE 12: Strut buckling
│   ├── calc_waling_beam_capacity.py       ← MODULE 12b: Waling Beam uốn ngang
│   ├── assess_excavation_geometry.py      ← MODULE 13: Geometry Assessment
│   ├── calc_corner_brace.py               ← MODULE 15: Corner Brace
│   ├── plaxis_to_etabs_handoff.py         ← MODULE 17: ETABS Handoff
│   ├── format_etabs_output.py            ← MODULE 18: ETABS Design Summary Format [MỚI v3.0]
│   ├── verify_against_ground_truth.py      ← VERIFY 1: Ground Truth check
│   ├── verify_serviceability_limits.py        ← VERIFY 2: SLS check
│   └── export_geotech_report.py            ← EXPORT v2.3: 12 sheets Excel + Markdown
└── data/
    └── ground_truth_db.json               ← DB dữ liệu thực từ hồ sơ TMTT
```

---

## Quy tắc Kỹ thuật Bắt buộc

1. **Deterministic Math:** Mọi phép toán PHẢI chạy qua script Python, AI KHÔNG nhẩm tay.
2. **Calculation_Logs:** Mọi script trả về `Calculation_Logs` (mảng bước tính) và `Standard_Method`.
3. **Step-by-step:** Hiển thị công thức tổng quát → thế số → kết quả cho từng lớp đất.
4. **Review Gate:** Trước khi xuất bảng tổng hợp chính thức, in tóm tắt và chờ User xác nhận.
5. **No Hallucination:** Thiếu dữ kiện → ghi `Data Missing: [Tên Thông Số]`. KHÔNG tự đoán.
6. **Dual Standard:** Ghi rõ nguồn tương quan đang dùng (TCVN / Bowles / Jamiolkowski / CIRIA C760).
7. **Mandatory Formulation Explanation (Giải trình Toán học Chi tiết):** Mọi kết quả quy đổi thông số đất và kết cấu BẮT BUỘC phải đi kèm diễn giải chi tiết công thức gốc. Viết rõ công thức tổng quát, hệ số lựa chọn, phép thế số và kết quả cuối cùng (giống như Phụ lục Giải trình trong thuyết minh mẫu Sunrise HK3). Tuyệt đối không chỉ đưa ra bảng kết quả trống không.

### 7.1. Cấu trúc Thuyết minh Giải trình Bắt buộc (v2.3)

```
PHẦN THUYẾT MINH GIẢI TRÌNH
├── I. CƠ SỞ LÝ THUYẾT
│   ├── 1.1. Nguồn tiêu chuẩn, tài liệu tham khảo
│   ├── 1.2. Giả định tính toán
│   └── 1.3. Giới hạn áp dụng
│
├── II. CÔNG THỨC TỔNG QUÁT
│   ├── 2.1. E50 cho đất dính: E50 = Ke × Su
│   ├── 2.2. E50 cho đất rời: E50 = α × N_SPT
│   ├── 2.3. Ứng suất hữu hiệu: σ'v = σv - u
│   ├── 2.4. Base Heave: Fs = (Nc × Su) / (γ_avg × H + q)
│   └── 2.5. Strut: λ = L0/im ; φ = f(λ̅) ; N_Rd = φ × A × fy
│
├── III. THẾ SỐ VÀ TÍNH TOÁN
│   ├── 3.1. Bảng số liệu đầu vào
│   ├── 3.2. Từng bước tính (step-by-step) — ĐẦY ĐỦ SỐ CỤ THỂ
│   └── 3.3. Bảng kết quả trung gian
│
├── IV. KẾT QUẢ QUY ĐỔI
│   ├── 4.1. Bảng tổng hợp thông số đầu vào Plaxis (transpose)
│   └── 4.2. Kiểm chứng Ground Truth (bảng deviance)
│
├── V. KIỂM TRA ỔN ĐỊNH
│   ├── 5.1. Base Heave check (Fs, η, khuyến nghị)
│   └── 5.2. Strut capacity check (λ, φ, N_Rd)
│
└── VI. KIỂM CHỨNG SLS
    └── 6.1. Chuyển vị ngang, độ lún (η, màu 🟢🟡🟠🔴)
```

### 7.2. Reference Documents cho Thuyết minh

| File | Mục đích |
|------|----------|
| `references/GEOTECH_GUIDE.md` | Công thức gốc, bảng Ke/α, nguồn tham khảo |
| `references/PLAXIS_MODEL_GUIDE.md` | Hướng dẫn nhập liệu Plaxis chi tiết |
| `references/THUYET_MINH_TEMPLATE.md` | **Template TMTT BPTC 6 Chương + Phụ lục A (BẮT BUỘC GIỮ)** |
| `references/ETABS_SHORING_GUIDE.md` | Hướng dẫn mô hình, gán tải trọng, liên kết ETABS cho hệ Shoring |

### 7.3. Tiêu chuẩn viện dẫn bắt buộc

```
• TCVN 9351:2012 — Khảo sát địa kỹ thuật
• TCVN 5575:2012 / TCVN 5574:2018 — Kết cấu thép / BTCT
• TCVN 2737:2023 — Tải trọng và tác động
• CIRIA C760 — Design of deep basements
• Eurocode 7 (BS EN 1997-1) — Geotechnical design
• Bowles (1997) — Foundation Analysis and Design, Eq. 3-12
• Jamiolkowski et al. (1979), Stroud (1974) — E50/Su correlation
• Terzaghi (1943) — Base Heave stability
• TCVN 5575:2018 — Kiểm tra ổn định thanh chống (Lambda, Phi, N_Rd)
• Plaxis Material Models Manual (Brinkgreve et al.)
```

---

## Lịch sử và Lộ trình phát triển (Roadmap)

**Giai đoạn 1 (v1.0.0):**
- Xây dựng Pipeline chuẩn từ SPT/CPT → MC/HS parameters.
- Tích hợp 15+ báo cáo TMTT vào CSDL tương quan.
- Quy đổi kết cấu cơ bản (Tường vây, cừ Larsen, hệ giằng).

**Giai đoạn 2 (v2.0.0):**
- **Động hóa (Dynamic):** CPTu (áp lực lỗ rỗng), Nkt động dựa trên Bq/Ip, tính OCR từ CPTu.
- **Tiêu chuẩn Quốc tế:** Tích hợp Eurocode 7 & CIRIA C760. Phân loại đất SBT 2016.
- **Mô hình Nâng cao:** Bổ sung Soft Soil Creep (SSC), Stiffness Degradation cho tường vây.
- **Kiểm định:** Module kiểm chứng SLS (Clough & O'Rourke) và diễn dịch sức chịu tải cọc.
- **Xuất báo cáo:** Module xuất Thuyết minh (MD) + Bảng tính Plaxis (XLSX).

**Giai đoạn 2.1 (v2.2.0):**
- Thêm references/GEOTECH_GUIDE.md, PLAXIS_MODEL_GUIDE.md, THUYET_MINH_TEMPLATE.md
- Viết lại export_geotech_report.py với 8 sheets Excel đầy đủ

**Giai đoạn 2.3 (v2.3.0):**
- **MODULE 5 nâng cấp:** Tách riêng E50 cho đất dính (`E50 = Ke × Su`) và đất rời (`E50 = α × N_SPT`). Bổ sung bảng Ke theo Ip (CIRIA C760 / Jamiolkowski / Stroud).
- **MODULE 1 nâng cấp:** Thêm `calc_layer_boundary_stress()` — bảng ứng suất tại ranh giới lớp chính xác với diễn giải bước tính số.
- **MODULE 11 MỚI:** `calc_base_heave.py` — Kiểm tra ổn định đáy hố đào theo Terzaghi.
- **MODULE 12 MỚI:** `calc_strut_capacity.py` — Kiểm tra ổn định thanh chống: độ mảnh Lambda, hệ số uốn dọc Phi (TCVN 5575:2018 / EC3), khả năng chịu nén N_Rd.

**Giai đoạn 3 (v3.0.0) — PHIÊN BẢN HIỆN TẠI:**
- **Full TMTT Automation:** Tự động hóa toàn diện Thuyết minh BPTC 6 Chương + Phụ lục A bắt buộc.
- **Tích hợp ETABS & Plaxis:** MODULE 17 quy đổi tải trọng Plaxis sang ETABS, MODULE 18 `format_etabs_output.py` tự động định dạng bảng ETABS Design Summary.
- **CSDL Cừ thép:** Bộ thông số cừ thép Larsen chuẩn JIS A 5528.

**Giai đoạn tiếp theo (Roadmap Tương lai - v3.5.0 / v4.0.0):**
| Item | Mô tả | Ưu tiên |
|------|--------|----------|
| Machine Learning | Huấn luyện mô hình hồi quy phi tuyến từ Ground Truth thay cho hệ số tương quan tĩnh | Cao |
| Plaxis API Hook | Script Python trực tiếp kết nối Plaxis 2D Remote Scripting API | Cao |
| HSS Model | Thông số Hardening Soil with Small-Strain Stiffness (G0, γ_0.7) | Trung bình |
| Nhập liệu tự động | Đọc trực tiếp file Excel/PDF báo cáo ĐCCT (OCR Vision) thay vì JSON Handoff | Rất Cao |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **3.0.0** | **2026-09-19** | **Full TMTT Automation** — Nâng cấp toàn diện `THUYET_MINH_TEMPLATE.md` thành Template 6 Chương + Phụ lục A bắt buộc (giải trình step-by-step E50/Eur/K0/Rinter từng lớp + bảng Ground Truth). Tạo MODULE 18 `format_etabs_output.py` tự động định dạng bảng ETABS Design Summary thành Markdown đẹ với màu đánh giá và kết luận tự động. |
| 2.4.0 | 2026-09-18 | Urban Excavation Upgrade — MODULE 12b (Waling Beam), MODULE 13 (Geometry), MODULE 15 (Corner Brace). |
| 2.3.2 | 2026-09-21 | Fix #1-7: calc_soil_params_hs, verify_ground_truth, calc_soil_params_mc, calc_base_heave (Bjerrum-Eide), calc_strut_capacity, calc_cpt_interpretation (SBT 2016, Nkt động). |
| 2.3.0 | 2026-09-20 | MODULE 5: Tách Ke×Su / α×N. MODULE 11: Base Heave. MODULE 12: Strut Capacity. EXPORT: 12 sheets Excel. |
| 2.2.0 | 2026-09-20 | Thêm references GEOTECH_GUIDE, PLAXIS_MODEL_GUIDE, THUYET_MINH_TEMPLATE. |
| 2.1.0 | 2026-09-17 | Rule 7: Mandatory Formulation Explanation. |
| 2.0.0 | 2026-09-16 | Tích hợp SSC, CPTu (SBT 2016), Nkt động, K0 (Mayne & Kulhawy), Rinter (CIRIA C760), SLS, Pile Load Test. |
| 1.0.0 | 2026-09-16 | Initial release — 6 modules, MC & HS support. |
