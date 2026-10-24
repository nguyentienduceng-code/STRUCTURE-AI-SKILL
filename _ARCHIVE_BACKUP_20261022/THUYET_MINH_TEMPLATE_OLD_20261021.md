# THUYẾT MINH TÍNH TOÁN BIỆN PHÁP THI CÔNG HỐ ĐÀO (BPTC)
# Template v3.0.0 — Cấu trúc chuẩn 6 Chương + PHỤ LỤC A (BẮT BUỘC GIỮ)
# Áp dụng: SKILL_GEOTECH v3.0.0 — Sunrise HK3 Pattern
# Tiêu chuẩn: TCVN, Plaxis, AISC 360-10, Rankin 1988

---

## MỤC LỤC

1. GIỚI THIỆU
   1.1. Tổng quan
   1.2. Phương án thi công
   1.3. Cơ sở thiết kế
   1.4. Tiêu chuẩn áp dụng

2. THÔNG SỐ ĐẦU VÀO
   2.1. Mặt cắt địa chất
   2.2. Thông số địa chất sử dụng trong mô hình
   2.3. Thông số địa chất thủy văn
   2.4. Thông số cừ vây
   2.5. Hệ giằng chống thép hình
   2.6. Phụ tải mặt đất

3. KẾT QUẢ MÔ HÌNH TÍNH TOÁN
   3.1. Mặt cắt 1-1
      3.1.1. Chuyển vị
      3.1.2. Lún nền
      3.1.3. Nội lực cừ vây
      3.1.4. Nội lực hệ giằng
      3.1.5. Hệ số ổn định tổng thể
   3.2. Mặt cắt 2-2 *(nếu có nhiều hơn 1 mặt cắt bất lợi)*
      3.2.1. Chuyển vị
      3.2.2. Lún nền
      3.2.3. Nội lực cừ vây
      3.2.4. Nội lực hệ giằng
      3.2.5. Hệ số ổn định tổng thể

4. KIỂM TRA KHẢ NĂNG CHỊU LỰC
   4.1. Cừ vây [Loại cừ]
   4.2. Chuyển vị ngang và lún nền công trình lân cận
   4.3. Hệ số ổn định tổng thể

5. TÍNH TOÁN, KIỂM TRA HỆ GIẰNG
   5.1. Mô hình tính toán (ETABS)
   5.2. Kết quả kiểm tra (Bảng ETABS Design Summary)

6. KẾT LUẬN
   6.1. Kết luận

**PHỤ LỤC A: GIẢI TRÌNH TÍNH TOÁN CHI TIẾT THÔNG SỐ ĐẤT** *(BẮT BUỘC KHÔNG ĐƯỢC BỎ)*
   A.1. Cơ sở lý thuyết và phương pháp xác định thông số
   A.2. Quy đổi thông số từng lớp đất
   A.3. Bảng kiểm chứng so sánh với Ground Truth

---

## CHƯƠNG 1: GIỚI THIỆU

### 1.1. Tổng quan

**Dự án:** [TÊN DỰ ÁN — điền tên đầy đủ]
**Địa điểm:** [ĐỊA CHỈ XÂY DỰNG]
**Quy mô hạng mục:** [Bể nước ngầm / Tầng hầm / Hố móng — Diện tích X m², Thể tích Y m³]

[Hình 1: Vị trí dự án — gán ảnh vệ tinh hoặc bản đồ vị trí]

Trong báo cáo này, chúng tôi trình bày tính toán phương pháp thi công phần hầm theo biện pháp đào mở - hệ giằng, sử dụng phần mềm tính Plaxis 2D phiên bản V21. Báo cáo này được thiết lập dựa trên báo cáo khảo sát địa chất và bản vẽ do chủ đầu tư cung cấp.

**Kích thước hình học chính:**
- Mặt bằng hố đào: [L × W] m
- Chiều sâu hố đào: [H] m (đến cao độ [±X.XXm] MĐTN)

[Hình 2: Mặt cắt 1-1 và 2-2 thể hiện kích thước hố đào]

### 1.2. Phương án thi công

Thi công phần hầm công trình theo phương án **đào mở - hệ giằng**.

Hệ chắn đất sử dụng **cừ vây [C250x50x6 / Larsen III / Loại khác]** như hình:

[Hình 3: Mặt bằng cừ vây]

Hệ giằng sử dụng 1 hệ bao gồm: hệ giằng 1 (tiết diện H200) được lắp ở cao độ **-[X.X]m MĐTN**.

**Trình tự thi công mô phỏng trong Plaxis:**

| Bước | Cao độ | Hành động |
|:---:|:---:|:---|
| 1 | -[X.X]m | Đào taluy mở miệng hố đào tới cao độ |
| 2 | — | Thi công ép cừ [loại] dài [X]m |
| 3 | -[X.X]m | Đào đất tới cao độ |
| 4 | -[X.X]m | Thi công hệ giằng H200 |
| 5 | -[X.X]m | Đào đất xuống đến đáy hố |
| 6 | — | Thi công móng / đáy bể |

[Hình 4: Mặt cắt mô hình trong Plaxis]

### 1.3. Cơ sở thiết kế

- Báo cáo khảo sát địa chất do chủ đầu tư cung cấp
- Bản vẽ do Chủ đầu tư cung cấp
- Khảo sát hiện trạng xung quanh công trình

### 1.4. Tiêu chuẩn áp dụng

| Tiêu chuẩn | Nội dung |
|:---|:---|
| TCVN 5574:2024 | Kết cấu bê tông và bê tông cốt thép - Tiêu chuẩn thiết kế |
| TCVN 2737:2023 | Tải trọng và tác động |
| TCVN 10304:2025 | Tiêu chuẩn thiết kế móng cọc |
| TCVN 9351:2012 | Khảo sát địa kỹ thuật |
| CIRIA C760:2017 | Design of deep basements |
| Eurocode 7 (EN 1997-1) | Geotechnical design |

---

## CHƯƠNG 2: THÔNG SỐ ĐẦU VÀO

### 2.1. Mặt cắt địa chất

Công tác khảo sát địa chất do [Đơn vị khảo sát] thực hiện với [X] hố khoan, chiều sâu khảo sát hố khoan [HKX] ([Y]m) vị trí gần nhất địa điểm thi công.

Nhận thấy nền đất trong khu vực xây dựng được cấu tạo từ các lớp đất chính như sau:

[Hình 5: Mặt cắt địa chất hố khoan HKX]

### 2.2. Thông số địa chất sử dụng trong mô hình

Từ phân tích mặt cắt địa chất như trên, dựa vào báo cáo địa chất kết hợp với phương pháp bán kinh nghiệm (sử dụng thông số SPT, thông số sức chống cắt không thoát nước), chúng tôi đưa ra các thông số địa chất sử dụng trong mô hình tính toán như trong bảng sau:

*(Xem chi tiết cơ sở xác định từng thông số tại **PHỤ LỤC A** — bắt buộc đính kèm)*

| Thông số | Đơn vị | Lớp san lấp | Lớp 1: Sét pha | Lớp 2: Cát |
|:---|:---:|:---:|:---:|:---:|
| Mô hình | — | MC | HS | HS |
| Thoát nước | — | Drained | Undrained (B) | Drained |
| γ_unsat | kN/m³ | [X] | [X] | [X] |
| γ_sat | kN/m³ | [X] | [X] | [X] |
| k_x = k_y | m/day | [X] | [X] | [X] |
| E₅₀_ref | kPa | [X] | [X] | [X] |
| Eoed_ref | kPa | [X] | [X] | [X] |
| Eur_ref | kPa | [X] | [X] | [X] |
| m | — | [X] | [X] | [X] |
| c' | kPa | [X] | [X] | [X] |
| φ' | ° | [X] | [X] | [X] |
| ψ | ° | 0.0 | 0.0 | [X] |
| ν_ur | — | [X] | [X] | [X] |
| R_inter | — | [X] | [X] | [X] |
| K₀ | — | [X] | [X] | [X] |

### 2.3. Thông số địa chất thủy văn

Theo báo cáo khảo sát địa chất, mực nước ngầm trong hố khoan ổn định ở mức **[X.X]m** so với mặt đất tự nhiên.

### 2.4. Thông số cừ vây

Cừ vây được mô hình dưới dạng plate và xem như dầm dẻo tuyến tính (elastic beam).

**Các thông số của cừ [C250x50x6 / Larsen / Loại khác] cho tính toán Plaxis:**

| Thành phần | Thông số | Trị số | Đơn vị |
|:---|:---:|:---:|:---:|
| Loại mô hình | Material type | Elastic | — |
| Độ cứng dọc trục | EA | [X] | kN/m |
| Độ cứng chống uốn | EI | [X] | kNm²/m |
| Trọng lượng | w | [X] | kN/m/m |

*(Cơ sở tính toán EA, EI: Xem PHỤ LỤC A — Mục A.4)*

### 2.5. Hệ giằng chống thép hình

Mặt bằng hệ giằng chống thép hình H[X] của hệ giằng 1.

[Hình 6: Mặt bằng hệ giằng chống]

**Các thông số của thanh chống H[X] cho tính toán Plaxis:**

| Thành phần | Thông số | Trị số | Đơn vị |
|:---|:---:|:---:|:---:|
| Loại mô hình | Material type | Elastic | — |
| Độ cứng dọc trục | EA | [X] | kN |
| Khoảng cách t.bình | L_spacing | [X] | m |

### 2.6. Phụ tải mặt đất

Qua khảo sát hiện trạng:

| Loại tải | Giá trị |
|:---|:---:|
| Tải nhà dân lân cận | [X] kN/m² |
| Tải vỉa hè / đường nội bộ | [X] kN/m² |
| Tải khu vực thi công | [X] kN/m² |

---

## CHƯƠNG 3: KẾT QUẢ MÔ HÌNH TÍNH TOÁN

### 3.1. Mặt cắt 1-1

[Hình 7: Mặt cắt 1-1 giai đoạn đào xuống đáy]

#### 3.1.1. Chuyển vị

[Hình 8: Chuyển vị tổng /U/ = X.XX mm]

[Hình 9: Chuyển vị ngang cừ vây /Ux/ = X.XX mm]

#### 3.1.2. Lún nền

[Hình 10: Chuyển vị lún Uy = X.XX mm]

#### 3.1.3. Nội lực cừ vây

[Hình 11: Biểu đồ lực bao moment (kNm/m)]

[Hình 12: Biểu đồ lực cắt (kN/m)]

[Hình 13: Biểu đồ lực dọc (kN/m)]

#### 3.1.4. Nội lực hệ giằng

[Hình 14: Nội lực trong hệ giằng — F_max = X.XX kN]

#### 3.1.5. Hệ số ổn định tổng thể

[Hình 15: Hệ số ổn định tổng thể — FS = X.XXX]

---

### 3.2. Mặt cắt 2-2

[Hình 16: Mặt cắt 2-2 giai đoạn đào xuống đáy]

#### 3.2.1. Chuyển vị

[Hình 17: Chuyển vị tổng /U/ = X.XX mm]

[Hình 18: Chuyển vị ngang cừ vây /Ux/ = X.XX mm]

#### 3.2.2. Lún nền

[Hình 19: Chuyển vị lún Uy = X.XX mm]

#### 3.2.3. Nội lực cừ vây

[Hình 20: Biểu đồ lực bao moment (kNm/m)]

[Hình 21: Biểu đồ lực cắt (kN/m)]

[Hình 22: Biểu đồ lực dọc (kN/m)]

#### 3.2.4. Nội lực hệ giằng

[Hình 23: Nội lực trong hệ giằng — F_max = X.XX kN]

#### 3.2.5. Hệ số ổn định tổng thể

[Hình 24: Hệ số ổn định tổng thể — FS = X.XXX]

---

## CHƯƠNG 4: KIỂM TRA KHẢ NĂNG CHỊU LỰC

### 4.1. Cừ vây [Loại cừ]

**Bảng tổng hợp giá trị nội lực lớn nhất (Phase đào đáy hố):**

| Mặt cắt | M (kNm/m) | Q (kN/m) |
|:---:|:---:|:---:|
| MC 1-1 | [X] | [X] |
| MC 2-2 | [X] | [X] |

**Bảng kiểm tra khả năng chịu lực cừ [C250x50x6 / Loại khác]** *(Theo Catalog JIS A 5528 / Nhà sản xuất)*:

| THÔNG SỐ | KÝ HIỆU | GIÁ TRỊ | ĐƠN VỊ / GHI CHÚ |
|:---|:---:|:---:|:---|
| **I. THÔNG SỐ HÌNH HỌC (1 CÂY CỪ)** | | | Theo Catalog |
| Bề rộng bụng | b_w | [X] | mm |
| Chiều sâu cánh | b_f | [X] | mm |
| Chiều dày | t | [X] | mm |
| Diện tích 1 cây | A_1 | [X] | cm² |
| Momen quán tính trục x (chính) | I_x1 | [X] | cm⁴ |
| Momen chống uốn trục x | W_x1 | [X] | cm³ |
| **II. QUY ĐỔI 1 MÉT DÀI ([N] CÂY)** | | | |
| Số cây trên 1m dài | n | [X] | cây/m |
| Diện tích 1m tường | A* | [X] | cm²/m |
| Momen quán tính 1m | I* | [X] | cm⁴/m |
| Momen chống uốn 1m | W* | [X] | cm³/m |
| **III. THÔNG SỐ VẬT LIỆU** | | | Thép SS400 |
| Mô đun đàn hồi | E | 210,000 | MPa |
| Cường độ chảy (SS400) | f_y | 235 | MPa |
| Cường độ chịu cắt | f_v | 135.7 | MPa |
| **IV. KHẢ NĂNG CHỊU LỰC** | | | |
| Khả năng chịu uốn | [M] | [X] | kNm/m |
| Khả năng chịu cắt | [V] | [X] | kN/m |
| **V. KIỂM TRA (Lấy MC bất lợi nhất)** | | | |
| Momen lớn nhất | M_max | [X] | kNm/m |
| Lực cắt lớn nhất | Q_max | [X] | kN/m |
| **KẾT LUẬN** | | **ĐẠT** | Cừ đảm bảo khả năng chịu lực |

### 4.2. Chuyển vị ngang và lún nền công trình lân cận

Chiều sâu hố đào H = [X.X] m (= [X,XXX] mm).

**Bảng tổng hợp chuyển vị ngang và lún nền:**

| Mặt cắt | Chuyển vị ngang cừ $U_{max}$ (mm) | Lún nền $S$ (mm) |
|:---:|:---:|:---:|
| 1-1 | [X] | [X] |
| 2-2 | [X] | [X] |

**Đánh giá mức độ ảnh hưởng công trình lân cận theo Rankin (1988):**

| Mặt cắt tính toán | Vị trí tiếp giáp | $U_x$ (mm) | $[U_x/H]$ (%) | $S$ (mm) | Đánh giá |
|:---|:---|:---:|:---:|:---:|:---|
| MC 1-1 | [Vị trí] | [X] | [X] | [X] | Ảnh hưởng nhẹ |
| MC 2-2 | [Vị trí] | [X] | [X] | [X] | Ảnh hưởng nhẹ |

> Tác động của chuyển vị ngang và lún nền lên khu vực lân cận ảnh hưởng nhẹ trong độ cho phép.

### 4.3. Hệ số ổn định tổng thể

Hệ số ổn định tổng thể tương ứng giai đoạn tức thời với các kết cấu tạm được quy định là **1.2**. Giai đoạn lâu dài là **1.4**.
*(Theo "Design of Retaining Wall and Support Systems for Deep Basement Construction")*

| Mặt cắt | Hệ số ổn định FS | Hệ số ổn định cho phép |
|:---:|:---:|:---:|
| 1-1 | [X.XXX] | 1.2 |
| 2-2 | [X.XXX] | 1.2 |

> **Vậy, biện pháp thi công đảm bảo hệ số ổn định tổng thể cho phép.**

---

## CHƯƠNG 5: TÍNH TOÁN, KIỂM TRA HỆ GIẰNG

### 5.1. Mô hình tính toán

[Hình 25: Mô hình tính toán 3D ETABS]

**Quy đổi tải trọng từ Plaxis sang ETABS:**

| Mặt cắt | Lực nén thanh chống Plaxis ($F_{max}$) | Spacing | Tải phân bố Dầm bo ($q = F/s$) |
|:---:|:---:|:---:|:---:|
| MC 1-1 | [X] kN | [X] m | [X] kN/m |
| MC 2-2 | [X] kN | [X] m | [X] kN/m |

[Hình 26: Tải trọng ALD lên hệ giằng (kN/m)]

[Hình 27: Biểu đồ lực dọc (kN)]

[Hình 28: Biểu đồ moment M2-2 (kNm)]

[Hình 29: Biểu đồ moment M3-3 (kNm)]

### 5.2. Kết quả kiểm tra

Các tổ hợp tải trọng dùng cho việc thiết kế kết cấu theo ASCE 7-10:

| STT | COMBO | SW | ALD |
|:---:|:---|:---:|:---:|
| 1 | 1.2DL + 1.6ALD | 1.2 | 1.6 |

[Hình 30: Biểu đồ tỷ số ứng suất (D/C Ratio)]

Với D/C = Nội lực nguy hiểm nhất / Khả năng chịu lực của cấu kiện. **Ratio ≤ 1** → Cấu kiện đủ khả năng chịu lực.

**Bảng Kết quả Kiểm tra Chi tiết (ETABS Steel Frame Design — AISC 360-10):**

| Label | Tiết diện | Loại | Combo | PMM Ratio | P Ratio | Kết luận |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| B11 | H200 | Beam | ACI LRSD(C) | **0.161** 🟢 | 0.058 | **ĐẠT** |
| B30 | H200 | Beam | ACI LRSD(C) | **0.161** 🟢 | 0.058 | **ĐẠT** |
| B31 | H200 | Beam | (T) | **0.223** 🟢 | 0.007 | **ĐẠT** |
| B32 | H200 | Beam | ACI LRSD(C) | **0.242** 🟢 | 0.027 | **ĐẠT** |
| B10 | H200 | Beam | (T) | **0.705** 🟢 | 0.023 | **ĐẠT** |
| B12 | H200 | Beam | ACI LRSD(C) | **0.737** 🟢 | 0.054 | **ĐẠT** |
| B13 | H200 | Beam | (T) | **0.705** 🟢 | 0.023 | **ĐẠT** |

> **Kết luận tổng hợp:** PMM Ratio lớn nhất = **0.737**. Tất cả cấu kiện hệ giằng H200 đều ĐẠT khả năng chịu lực.

---

## CHƯƠNG 6: KẾT LUẬN

### 6.1. Kết luận

Biện pháp thi công đảm bảo an toàn:
- Cừ vây [Loại] đảm bảo khả năng chịu lực.
- Chuyển vị cừ và lún nền nằm trong giới hạn cho phép, mức độ ảnh hưởng nhẹ đến công trình lân cận.
- Hệ giằng chống và các liên kết đảm bảo khả năng chịu lực.
- Hệ số ổn định tổng thể đảm bảo theo yêu cầu.

---

# PHỤ LỤC A: GIẢI TRÌNH TÍNH TOÁN CHI TIẾT THÔNG SỐ ĐẤT
## *(BẮT BUỘC GIỮ LẠI — Cơ sở kiểm soát số liệu đầu vào)*

> **Mục đích:** Cung cấp đầy đủ cơ sở tính toán và nguồn gốc của từng thông số địa chất được nhập vào Plaxis. Người kiểm tra có thể truy vết và kiểm chứng lại toàn bộ số liệu.

### A.1. Cơ sở Lý thuyết và Phương pháp Xác định Thông số

**A.1.1. Mô đun biến dạng E₅₀_ref**

**Đối với đất dính (Sét, Sét pha):**
Theo Jamiolkowski et al. (1979), Stroud (1974) và CIRIA C760:
$$E_{50}^{ref} = K_e \times S_u$$

Trong đó:
- $K_e$: Hệ số kinh nghiệm, phụ thuộc Chỉ số dẻo $I_p$
- $S_u$: Sức kháng cắt không thoát nước [kPa]

| Ip (%) | < 10 | 10–20 | 20–30 | 30–50 | > 50 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Ke | 1000 | 800 | 700 | 600 | 500 |

**Đối với đất rời (Cát, Cát pha):**
Theo Bowles (1997) và CIRIA C760:
$$E_{50}^{ref} = \alpha \times N_{SPT}$$

| Loại đất | α (kPa/búa) |
|:---|:---:|
| Cát hạt mịn | 2,000–3,000 |
| Cát hạt trung | 3,000–4,000 |
| Cát hạt thô | 4,000–5,000 |

**A.1.2. Mô đun tải lại-dỡ tải Eur_ref**
$$E_{ur}^{ref} = 3 \times E_{50}^{ref}$$
*(Theo Plaxis Material Models Manual, Brinkgreve et al.)*

**A.1.3. Hệ số K₀ (Áp lực đất nghỉ)**
$$K_0 = 1 - \sin\varphi'$$
*(Jaky 1944 — cho đất bình thường cố kết, OCR ≈ 1)*

**A.1.4. Hệ số tương tác Rinter**
| Điều kiện | Rinter |
|:---|:---:|
| Cừ thép trong đất dính mềm | 0.50–0.65 |
| Cừ thép trong đất cát chặt vừa | 0.65–0.80 |
| Tường BTCT trong đất tốt | 0.80–1.00 |

---

### A.2. Tính toán Chi tiết Từng Lớp Đất

#### A.2.1. Lớp san lấp / Đất đắp (Mohr-Coulomb)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LỚP SAN LẤP — Mohr-Coulomb (Drained)
Chiều sâu: 0.00 → [X.XX]m | N_SPT trung bình: [X] búa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Mô đun biến dạng (Mohr-Coulomb):
    Phương pháp: E_ref = α × N_SPT (Bowles 1997)
    α = [X] kPa/búa (cát pha đất lẫn xà bần)
    N_SPT = [X] búa
    ► E_ref = [X] × [X] = [X,XXX] kPa

[2] Góc ma sát trong: φ' = [XX]°
    (Theo tương quan SPT / kết quả thí nghiệm)

[3] Lực dính: c' = [X] kPa

[4] Hệ số K₀ = 1 - sin([XX]°) = [X.XXX]

[5] Rinter = [X.XX] (tường cừ-đất đắp tơi xốp)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### A.2.2. Lớp [X]: Sét pha (Hardening Soil — Undrained B)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LỚP [X]: SÉT PHA — Hardening Soil (Undrained B)
Chiều sâu: [X.XX] → [X.XX]m | N_SPT trung bình: [X] búa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Sức kháng cắt không thoát nước Su:
    Su = [X] kPa (từ thí nghiệm cắt cánh / UU)

[2] Chỉ số dẻo: Ip = [X]% → Ke = [X]
    (Theo CIRIA C760 Bảng 5.2)

[3] Mô đun biến dạng E50ref:
    E50ref = Ke × Su = [X] × [X] = [X,XXX] kPa

[4] Kiểm chứng Ground Truth:
    Giá trị tham chiếu khu vực TP.HCM: [X,XXX] – [X,XXX] kPa
    Deviance = |[X,XXX] - [X,XXX]| / [X,XXX] × 100% = [X]%
    Kết luận: [Trong phạm vi chấp nhận / Cần xem xét]

[5] Eoedref = E50ref = [X,XXX] kPa
    Eurref  = 3 × E50ref = [X,XXX] kPa

[6] Thông số bền: c' = [X] kPa, φ' = [XX.XX]°
[7] K₀ = 1 - sin([XX.XX]°) = [X.XXX]
[8] Rinter = [X.XX]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### A.2.3. Lớp [X]: Cát (Hardening Soil — Drained)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LỚP [X]: CÁT — Hardening Soil (Drained)
Chiều sâu: [X.XX] → [X.XX]m | N_SPT trung bình: [X] búa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Mô đun biến dạng E50ref:
    Phương pháp: α × N_SPT (Bowles 1997)
    α = [X,XXX] kPa/búa (cát hạt nhỏ→trung, bão hòa)
    N_SPT = [X] búa
    ► E50ref = [X,XXX] × [X] = [XX,XXX] kPa

[2] Kiểm chứng Ground Truth:
    Giá trị tham chiếu: [XX,XXX] – [XX,XXX] kPa
    Deviance = [X]% — [Trong phạm vi chấp nhận]

[3] Eoedref = E50ref = [XX,XXX] kPa
    Eurref  = 3 × E50ref = [XX,XXX] kPa

[4] Thông số bền: c' = [X] kPa, φ' = [XX.XX]°
[5] K₀ = 1 - sin([XX.XX]°) = [X.XXX]
[6] Rinter = [X.XX]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### A.3. Bảng Kiểm chứng So sánh Thông số với Ground Truth

| Lớp | Thông số | Giá trị sử dụng | Dải tham chiếu khu vực | Deviance | Đánh giá |
|:---|:---:|:---:|:---:|:---:|:---:|
| San lấp | E_ref | [X,XXX] kPa | [X,XXX]–[X,XXX] | [X]% | 🟢 OK |
| Sét pha | E50ref | [X,XXX] kPa | [X,XXX]–[X,XXX] | [X]% | 🟢 OK |
| Cát | E50ref | [XX,XXX] kPa | [XX,XXX]–[XX,XXX] | [X]% | 🟢 OK |

---

### A.4. Thông số Kết cấu Chắn giữ

**A.4.1. Cừ thép [Loại] — Quy đổi thông số Plaxis:**

Theo Catalog [JIS A 5528 / Nhà sản xuất]:

| Thông số | Ký hiệu | 1 Cây | Quy đổi 1m tường ([n] cây/m) |
|:---|:---:|:---:|:---:|
| Diện tích tiết diện | A | [X] cm² | [X] cm²/m |
| Momen quán tính (trục chính) | I_x | [X] cm⁴ | [X] cm⁴/m |
| Momen chống uốn (trục chính) | W_x | [X] cm³ | [X] cm³/m |

Thông số Plaxis:
- $EA = E \times A^* = [X] \text{ MPa} \times [X] \text{ cm}^2/m = [X] \text{ kN/m}$
- $EI = E \times I^* = [X] \text{ MPa} \times [X] \text{ cm}^4/m = [X] \text{ kNm}^2/m$

---

> *Tài liệu do trợ lý AI (SKILL_GEOTECH v3.0.0) lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
