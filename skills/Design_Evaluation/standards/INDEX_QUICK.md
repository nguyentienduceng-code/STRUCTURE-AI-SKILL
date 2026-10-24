# Tiêu chuẩn Kỹ thuật - Tra cứu nhanh (Phiên bản Markdown)

> **Phiên bản tiêu chuẩn nào là chuẩn?** → Xem `../../STANDARDS_LOCK.md` (nguồn sự thật duy nhất).
> Thư mục này chứa cả bản mới và bản cũ; tên file có tiền tố `TK` = **bản đã bị thay thế**, chỉ dùng đối chiếu hồ sơ cũ.
>
> **Cách tra cứu:** dùng `grep_search` với từ khóa đặc thù trực tiếp trên file PDF. KHÔNG đọc toàn bộ PDF lớn.

## QCVN & Thông tư Phân cấp (Bắt buộc áp dụng) — `standards/QCVN/`

| Mã | Keyword & Phạm vi chính xác | File PDF / Ghi chú |
|----|-----------------------------|--------------------|
| **Thông tư 34/2026/TT-BXD** | cấp công trình (**Đặc biệt, Cấp I, II, III, IV**), quy mô công suất (Phụ lục I), quy mô kết cấu (**Bảng 2 Phụ lục II**: GFA Cấp I `> 30,000 m²`, độ sâu ngầm Cấp II `6 ÷ 18m` tính tới mặt trên sàn hầm sâu nhất) | Hiệu lực từ **01/07/2026**, thay thế `TT 06/2021/TT-BXD` và `TT 02/2025/TT-BXD` (`3a. Thong tu 02-2025_TT-BXD...pdf`) |
| **QCVN 03:2022/BXD** | phân cấp phục vụ thiết kế: **Cấp hậu quả (`C1, C2, C3` — Mục 2.1 & Phụ lục A, KHÔNG dùng ký hiệu CC1-CC3)**, **Thời hạn sử dụng theo thiết kế (`Mức 1: <25 năm, Mức 2: ≥25 năm, Mức 3: ≥50 năm dân dụng thông thường, Mức 4: ≥100 năm công trình biểu tượng` — Mục 2.2.2 Bảng 1)**, phân loại kỹ thuật về cháy | `3. QCVN 03-2022_PHAN CAP CONG TRINH.pdf` *(Lưu ý: QCVN 03:2022 KHÔNG phân cấp I, II, III, IV)* |
| **QCVN 01:2021/BXD** | quy hoạch, khoảng lùi, mật độ xây dựng | ⚠ Chưa có PDF 2021 trong thư viện — chỉ có bản đối chiếu `1. QCVN01-2012_QUY HOACH XAY DUNG.pdf` (bản cũ đối chiếu: `QCVN 01:2012`) |
| **QCVN 02:2022/BXD** | vùng gió, vùng động đất, mưa, nhiệt độ | `2. QCVN02-2022_SO LIEU DIEU KIEN TU NHIEN...pdf` |
| **QCVN 06:2022/BXD + Sửa đổi 1:2023** | PCCC, khoang cháy, thoát nạn, bậc chịu lửa (kèm Sửa đổi 1:2023) | `6. QCVN 06-2022_AN TOAN VE CHAY CHO NHA VA CONG TRINH.pdf` + `6a. SUA DOI BO SUNG QCVN 06-2022.pdf` |

## TCVN — `standards/TCVN/`

| Mã | Keyword & Điều khoản cốt lõi | File PDF |
|----|------------------------------|----------|
| **TCVN 2737:2023** | tải trọng, hoạt tải, gió, tĩnh tải, hệ số tầm quan trọng $\gamma_n$ theo Cấp hậu quả C1 (0.87), C2 (1.00), C3 (1.15) tại **Phụ lục H (Bảng H.1)** | `1. TCVN 2737-2023_TAI TRONG VA TAC DONG.pdf` |
| **TCVN 9386:2025** | động đất mới (P1 + P5), phân vùng gia tốc nền mới | `2a. TCVN 9386-2025 P1_...pdf` + `2b.` (Bản cũ: `TCVN 9386:2012`) |
| **TCVN 9363:2012** | khảo sát ĐKT nhà cao tầng (tên đúng: *Khảo sát cho xây dựng - Khảo sát địa kỹ thuật cho nhà cao tầng*): cự ly hố khoan **TKCS `50m – 200m` (Điều 5.2.4.2)**; cự ly **TKKT `20m – 30m` (Điều 5.3.6, Mục D.1 & Bảng D.1 Phụ lục D)**; **số hố khống chế $\ge 1/3$ tổng số điểm (Điều 5.3.6.3)** | `4.TCVN 9363-2012_KHAO SAT DIA DIA KY THUAT CHO NHA CAO TANG.pdf` |
| **TCVN 4419:1987** | nguyên tắc khảo sát xây dựng: **phân 3 cấp phức tạp ĐCCT (Cấp I, II, III) tại Điều 3.5 & Phụ lục 2**; bố trí điểm thăm dò TKKT tại **Điều 3.19** | Văn bản gốc TCVN 4419:1987 |
| **TCVN 9362:2012** | thiết kế nền nhà và công trình, sức chịu tải quy ước $R_0$, độ lún giới hạn | `5. TCVN 9362-2012_...pdf` |
| **TCVN 10304:2025** | móng cọc, sức chịu tải cọc đơn và nhóm cọc | `6. TCVN 10304 2025_...pdf` |
| **TCVN 9351:2022** | thí nghiệm xuyên tiêu chuẩn SPT | `6b.TCVN9351-2022_...pdf` |
| **TCVN 12041:2017 & TCVN 9346:2012** | thiết kế độ bền lâu, đánh giá **ăn mòn / xâm thực nước ngầm** đối với bê tông và BTCT *(thay thế `TCVN 3994:1985` đã hết hiệu lực)* | `16. TCVN 9346-2012_...pdf` |
| **TCVN 5574:2018** | BTCT, uốn, cắt, nén, nứt, võng | `10.TCVN 5574-2018_...pdf` |
| **TCVN 5575:2024** | kết cấu thép, ổn định, liên kết | `13. TCVN 5575-2024_...pdf` |
| **TCVN 5573:2025** | khối xây, tường gạch | `12. TCVN 5573 2025_...pdf` |
| **TCVN 4453:1995** | thi công BTCT, nghiệm thu | `11. TCVN 4453-1995_...pdf` |

## Quốc tế — `standards/International/`

| Mã | Keyword | File PDF |
|----|---------|----------|
| AISC 360-10 | thép Mỹ, steel design | `AISC 360-10.pdf` |
| ASCE 7-10 | tải trọng Mỹ, gió, động đất | `ASCE 7-10.pdf` |
| MBMA 2012 | nhà thép tiền chế | `MBMA 2012.pdf` |
| Eurocode 2 | BTCT châu Âu | `TCEC0001-Eurocode 2-TiengViet.pdf` |

> 📖 **Cần danh sách đầy đủ 75+ tiêu chuẩn?** → Đọc `INDEX.md`
