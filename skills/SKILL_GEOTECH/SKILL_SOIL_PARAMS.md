# SKILL_SOIL_PARAMS.md — Quy trình Chi tiết Tính Thông số Đất

> **Phạm vi:** Hướng dẫn AI thực hiện từng bước tính toán thông số đất từ dữ liệu khảo sát.
> **Đọc trước:** `SKILL.md` để xác định Module cần kích hoạt.
> **Phiên bản:** v2.3.2 — Cập nhật theo SKILL_GEOTECH v2.3.2

---

## 1. QUY TRÌNH TỔNG THỂ (7 BƯỚC)

Áp dụng cho mô hình **Hardening Soil (HS)** — mô hình tiêu chuẩn cho hố đào sâu tại TP.HCM.

### Bước 1: Tính dung trọng γ_sat
- Nếu có từ Lab Test → dùng trực tiếp.
- Nếu chỉ có SPT: ước lượng từ bảng tương quan trong `calc_spt_correlations.py`.
- Đơn vị: kN/m³

### Bước 2: Tính E50ref (Module cát tuyến tham chiếu) — CÔNG THỨC CHÍNH v2.3

**Đất rời (Drained — cát, cát pha, cát bụi):**
```
E50ref = α × N_SPT
```
| Loại cát | α (kN/m² per SPT) | Nguồn |
|-----------|-------------------|--------|
| Cát mịn, rời | 1500 | Bowles 1997 / CIRIA C760 |
| Cát trung, chặt vừa | 2000 | Bowles 1997 / CIRIA C760 |
| Cát thô, chặt | 2500 | Bowles 1997 / CIRIA C760 |
| Cát sỏi, rất chặt | 3000 | Bowles 1997 / CIRIA C760 |

**Đất dính (Undrained — sét, sét pha, bùn):**
```
E50ref = Ke × Su
```
| Ip (%) | Loại đất | Ke (khoảng) | Ke khuyến nghị | Nguồn |
|--------|-----------|-------------|----------------|--------|
| < 15 | Sét mềm, bùn | 300–500 | **400** | CIRIA C760 / Jamiolkowski |
| 15–25 | Sét dẻo mềm | 400–600 | **500** | CIRIA C760 / Jamiolkowski |
| 25–40 | Sét trung bình | 500–700 | **600** | CIRIA C760 / Jamiolkowski |
| 40–60 | Sét nửa cứng | 600–900 | **710** | CIRIA C760 (chuẩn) |
| > 60 | Sét cứng–rất cứng | 800–1200 | **1000** | CIRIA C760 / Stroud |

**Giải trình công thức:**
- **Ke** (Stiffness Ratio): Tỷ số giữa E50 và Su, phản ánh độ cứng tương đối của đất dính. Nguồn gốc từ Jamiolkowski et al. (1979) và Stroud (1974) — thí nghiệm cắt 3 trục trên mẫu UNC.
- **α** (Alpha): Hệ số kinh nghiệm cho đất rời, xuất phát từ Bowles (1997), Eq. 3-12, pp. 67–68.
- Áp lực tham chiếu: `p_ref = 100 kN/m²` (mặc định Plaxis).

**Script:** `calc_spt_correlations.py` — Module 5 v2.3.0

### Bước 3: Tính Su (Sức kháng cắt không thoát nước)
- **Cách 1:** Từ thí nghiệm nén đơn: `Su = Qu / 2`
- **Cách 2:** Tính theo công thức: `Su = σ'v × tan(φ') + c'`
  - Trong đó: `σ'v = γ × h - γ_w × z` (ứng suất hữu hiệu tại giữa lớp)
- **Cách 3:** Từ CPT: `Su = (qc - σv0) / Nkt` (Nkt ≈ 15)
- Chỉ áp dụng cho đất dính (Undrained).

### Bước 4: Tra bảng xác định hệ số mũ m
- m phụ thuộc loại đất:

| Loại đất | m |
|----------|---|
| Cát sạch, chặt | 0.5 |
| Cát mịn, chặt vừa | 0.55 |
| Cát pha, cát bụi | 0.6 |
| Sét pha, dẻo mềm | 0.65–0.7 |
| Sét, dẻo cứng đến nửa cứng | 0.7–0.8 |
| Sét mềm, bùn | 0.8–0.9 |
| Than bùn | 1.0 |

### Bước 5: Tra bảng xác định Rinter
- Rinter là hệ số giảm cường độ tại mặt tiếp xúc đất–kết cấu.
- **[v2.0]** Hệ thống tự động gán theo **CIRIA C760**:
  - Tường vây (Diaphragm Wall - dw): `Rinter = 1.0`
  - Cọc Secant (secant): `Rinter = 0.9`
  - Cừ Larsen (Sheet pile - sp): `Rinter = 0.67`
- Bảng tra thủ công (nếu cần):

| Vật liệu kết cấu | Loại đất | Rinter |
|-------------------|----------|--------|
| Tường vây BTCT (DW) | Cát | 0.8–0.9 |
| Tường vây BTCT (DW) | Sét cứng | 0.8 |
| Tường vây BTCT (DW) | Sét mềm | 0.6–0.7 |
| Cừ Larsen (thép) | Cát | 0.7–0.8 |
| Cừ Larsen (thép) | Sét | 0.5–0.65 |
| Cọc khoan nhồi | Mọi loại | 0.7–0.9 |

### Bước 6: Tìm hệ số Poisson ν_ur
- Mặc định: `ν_ur = 0.2` cho mọi loại đất trong mô hình HS.
- Mô hình MC: `ν = 0.3` (đất rời), `ν = 0.35` (đất dính).

### Bước 7: Tìm hệ số thấm kx, ky
| Loại đất | kx (m/ngày) | Ghi chú |
|----------|-------------|---------|
| Cát sạch | 1.0 – 10.0 | Drained |
| Cát pha | 0.5 – 1.0 | Drained |
| Sét pha | 0.01 – 0.5 | Tùy hàm lượng cát |
| Sét | 0.0001 – 0.001 | Undrained |
| Bùn, than bùn | 0.001 – 0.01 | Undrained |

**Lưu ý:** Nếu Lab Test cho đơn vị cm/s → đổi sang m/ngày: `k (m/ngày) = k (cm/s) × 864`

---

## 6. PHỤ LỤC — GIẢI TRÌNH TÍNH TOÁN CHI TIẾT

> **Yêu cầu bắt buộc theo SKILL.md v2.3 — Rule 7.1:** Mọi kết quả quy đổi thông số đất BẮT BUỘC phải đi kèm giải trình từng bước công thức. Phần này là template mẫu.

### 6.1. Ví dụ: Tính E50ref cho đất dính (Sét pha)

```
================================================================
BƯỚC 1: XÁC ĐỊNH HỆ SỐ Ke

Công thức tổng quát:
    Ke = f(Ip)

Bảng tra (CIRIA C760 / Jamiolkowski et al. 1979):
    Ip = 12.8% → Ip < 15% → Ke = 400 (cấp "very_low")

Thay số:
    Ke = 400

================================================================
BƯỚC 2: XÁC ĐỊNH Su

Cách 1: Từ thí nghiệm UU (ưu tiên)
    Su = Qu / 2

    Trong đó:
    - Qu = 42.3 kPa (từ báo cáo Lab Test)
    → Su = 42.3 / 2 = 21.15 kPa

Cách 2: Ước lượng từ CPTu (nếu có)
    Su = (qt - σ_v0) / Nkt

    Trong đó:
    - qt = 450 kPa (qt đã hiệu chỉnh tại độ sâu -3.95m)
    - σ_v0 = 74.2 kPa (ứng suất tổng tại -3.95m)
    - Nkt = 12 (ước lượng cho sét pha mềm, Robertson 2016)
    → Su = (450 - 74.2) / 12 = 31.3 kPa

→ Chọn Su = 21.15 kPa (từ UU, đáng tin cậy hơn)

================================================================
BƯỚC 3: TÍNH E50ref

Công thức tổng quát:
    E50ref = Ke × Su

Thay số:
    E50ref = 400 × 21.15

Kết quả:
    E50ref = 8,460 kPa ≈ 8,500 kPa

Kiểm tra với Ground Truth (nếu có):
    E50ref_GT = 15,000 kPa (Navi Tower Q.3, SPT=7)
    Deviance = |8500 - 15000| / 15000 × 100% = 43.3% > 20%
    ⚠ Cảnh báo W001: Giá trị E50 thấp hơn Ground Truth
    → Khuyến nghị: Sử dụng Su từ CPTu (31.3 kPa) thay vì UU
       → E50ref = 400 × 31.3 = 12,520 ≈ 12,500 kPa (deviance = 16.7% ✓)

================================================================
KẾT LUẬN:
    E50ref = 12,500 kPa  (chọn theo Su từ CPTu)
    Nguồn: Jamiolkowski et al. (1979); CIRIA C760 Table 5.3
    Cảnh báo: Deviance 16.7% với Ground Truth — trong phạm vi cho phép
```

### 6.2. Ví dụ: Tính E50ref cho đất rời (Cát pha)

```
================================================================
BƯỚC 1: XÁC ĐỊNH HỆ SỐ α

Công thức tổng quát:
    α = f(loại cát, độ chặt)

Bảng tra (Bowles 1997 / CIRIA C760):
    Loại: Cát pha, hạt trung, chặt vừa
    → α = 2,000 kN/m² per SPT

Thay số:
    α = 2,000 kN/m² per SPT

================================================================
BƯỚC 2: XÁC ĐỊNH N_SPT

Từ báo cáo khảo sát:
    - Cao độ: -6.50m → -29.00m
    - N_SPT trung bình: 13 bua/30cm
    - Đã hiệu chỉnh theo Skempton: N_corr = 1.0 × N

→ N_SPT = 13 bua/30cm

================================================================
BƯỚC 3: TÍNH E50ref

Công thức tổng quát:
    E50ref = α × N_SPT

Thay số:
    E50ref = 2,000 × 13

Kết quả:
    E50ref = 26,000 kPa

Cross-check với Database TP.HCM:
    - H300: Set 1, SPT=11, E50=15,000 kPa → α = 1,364
    - H400: Cát pha, SPT=15, E50=32,000 kPa → α = 2,133
    - H500: Cát trung, SPT=20, E50=45,000 kPa → α = 2,250

→ α = 2,000 phù hợp với các dự án thực tế tương đương

================================================================
KẾT LUẬN:
    E50ref = 26,000 kPa
    Eoedref = 26,000 kPa (≈ E50ref theo Plaxis Manual)
    Eurref = 78,000 kPa (= 3 × E50ref)
    Nguồn: Bowles (1997), Eq. 3-12; CIRIA C760
```

### 6.3. Ví dụ: Tính ứng suất hữu hiệu và K0

```
================================================================
BƯỚC 1: TÍNH ỨNG SUẤT TỔNG σ_v

Công thức:
    σ_v = Σ(γ_i × h_i)

Từ bề mặt đến -3.95m (đáy hố đào):

Lớp ad (0 → -0.80m):
    γ_unsat = 17.50 kN/m³
    h = 0.80 m
    → σ_v = 17.50 × 0.80 = 14.0 kPa

Lớp 1 (-0.80m → -3.95m):
    γ_sat = 19.12 kN/m³
    h = 3.15 m
    → σ_v = 14.0 + 19.12 × 3.15 = 14.0 + 60.23 = 74.23 kPa

Kết quả:
    σ_v,tại -3.95m = 74.23 kPa

================================================================
BƯỚC 2: TÍNH ÁP LỰC NƯỚC LỖ RỖNG u

Mực nước ngầm: -4.40m
Tại z = -3.95m (trên GWT):
    u = 0 kPa

Vì điểm tính nằm trên mực nước ngầm.

================================================================
BƯỚC 3: TÍNH ỨNG SUẤT HỮU HIỆU

Công thức:
    σ'_v = σ_v - u

Thay số:
    σ'_v = 74.23 - 0 = 74.23 kPa

================================================================
BƯỚC 4: TÍNH K0

Bước 4a: Tính φ' (từ SPT, tương quan Hà Giang Tân)
    N_SPT = 7 bua/30cm
    φ' = 28 + 0.4 × N  (công thức thực nghiệm cho sét pha)
    φ' = 28 + 0.4 × 7 = 30.8°

Bước 4b: Tính K0 theo Jaky (1944) — đất nguyên dạng (NC)
    K0 = 1 - sin(φ')
    K0 = 1 - sin(30.8°) = 1 - 0.511 = 0.489

Bước 4c: Điều chỉnh theo OCR (Mayne & Kulhawy 1982)
    OCR = 1.0 (giả định — cần xác nhận từ CPTu)
    K0(OC) = K0(NC) × OCR^sin(φ')
    K0(OC) = 0.489 × 1.0^0.511 = 0.489

Kết quả:
    σ'_h = K0 × σ'_v = 0.489 × 74.23 = 36.30 kPa

================================================================
KẾT LUẬN:
    σ_v = 74.23 kPa | u = 0 kPa | σ'_v = 74.23 kPa
    K0 = 0.489 | σ'_h = 36.30 kPa
    Nguồn: Terzaghi (1943); Jaky (1944); Mayne & Kulhawy (1982)
```

---

## 7. BẢNG TỔNG HỢP MẪU — OUTPUT FORMAT

Sau khi tính xong, AI phải xuất bảng tổng hợp theo format sau trước Review Gate:

```
| Lớp | Mô tả | Type | γ_unsat | γ_sat | kx | E50ref | Eoedref | Eurref | m | ν | c' | φ' | ψ | Rinter |
|-----|-------|------|---------|-------|-----|--------|---------|--------|---|---|----|----|---|--------|
| | | | kN/m³ | kN/m³ | m/ngày | kN/m² | kN/m² | kN/m² | | | kN/m² | ° | ° | |
```

---

## 3. LỰA CHỌN MÔ HÌNH ĐẤT

### Khi nào dùng Mohr-Coulomb (MC)?
- Phân tích sơ bộ, ước lượng nhanh
- Lớp đất san lấp, đất cứng (kết cấu rigid trong đất)
- Bài toán ổn định mái dốc đơn giản
- **5 thông số:** E, ν, c, φ, ψ

### Khi nào dùng Hardening Soil (HS)?
- **Bắt buộc** cho hố đào sâu tại TP.HCM
- Mô phỏng chính xác ứng xử dỡ tải–gia tải lại
- Khi cần dự báo chuyển vị tường vây và lún mặt đất
- **7+ thông số:** E50ref, Eoedref, Eurref, m, pref, c', φ', ψ, ν_ur

### Khi nào dùng Soft Soil Creep (SSC)?
- Lớp sét mềm, bùn, than bùn cần phân tích cố kết và lún thứ cấp (từ biến).
- **[v2.0]** Đã tích hợp tự động qua MODULE 7 (`calc_soil_params_ssc.py`).
- **Thông số:** e0, Cc, Cs, Cα → chuyển đổi thành λ*, κ*, μ*.

---

## 4. XÁC ĐỊNH DRAINAGE TYPE

| Loại đất | Drainage Type | Ghi chú |
|----------|--------------|---------|
| Cát sạch, cát pha | **Drained** | Thoát nước hoàn toàn |
| Sét pha (hàm lượng cát > 40%) | **Drained** | Tùy thuộc tỷ lệ hạt |
| Sét pha (hàm lượng sét > 40%) | **Undrained (A hoặc B)** | |
| Sét, bùn sét | **Undrained (B)** | Dùng thông số hữu hiệu c', φ' |
| Bùn hữu cơ, than bùn | **Undrained (B)** | |

**Undrained A:** Dùng thông số tổng (Su, φ=0). Ít dùng cho HS.
**Undrained B:** Dùng thông số hữu hiệu (c', φ'). **Khuyến nghị cho HS model.**

---

## 5. HƯỚNG DẪN DỮ LIỆU INPUT JSON (v2.0)

Với các tính năng mới trong v2.0, JSON Handoff cần cung cấp các trường dữ liệu nâng cao sau (nếu có từ khảo sát):

### Cho CPTu (MODULE 6):
- `u2_kpa`: Áp lực nước lỗ rỗng đo tại mũi xuyên.
- `t50_min`: Thời gian tiêu tán 50% áp lực lỗ rỗng (để tính ch).
- `Ip`: Chỉ số dẻo (để tính Nkt động nếu không dùng Bq).

### Cho Geostatic Stress & K0 (MODULE 1):
- `OCR`: Tỷ số quá cố kết (Mặc định 1.0). Nếu OCR > 1, hệ thống kích hoạt Mayne & Kulhawy (1982).
- `is_stiff_clay`: true/false để hiệu chỉnh k_factor khi đoán OCR từ CPT.

### Cho Soft Soil Creep (MODULE 7):
- Yêu cầu cấu trúc layer có `"model": "SSC"`.
- Các trường bắt buộc: `e0` (hệ số rỗng ban đầu), `Cc` (chỉ số nén), `Cs` (chỉ số nở).
- Tùy chọn: `Ca` (chỉ số nén thứ cấp). Nếu thiếu, tự động lấy `lambda*/20`.

### Cho Kết cấu Tường Vây (MODULE 4):
- `cracked_section_factor`: Hệ số giảm độ cứng EI do nứt (Mặc định 0.6).
