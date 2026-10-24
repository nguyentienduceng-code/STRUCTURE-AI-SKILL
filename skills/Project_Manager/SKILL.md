---
name: Project_Manager
version: 0.6.0
last_updated: 2026-10-21
description: "Kỹ sư Quản lý Dự án AI: Phân cấp công trình chuẩn Thông tư 34/2026/TT-BXD (và TT 06/2021/TT-BXD) kèm QCVN 03:2022/BXD, quản lý vòng đời dự án, theo dõi tiến độ & milestone, kiểm soát lộ trình pháp lý, ma trận rủi ro (Risk Register), ĐTM và PCCC. Kích hoạt khi: phân cấp công trình, lập tiến độ, theo dõi milestone, quản lý rủi ro, tài liệu pháp lý, risk matrix, legal checklist."
status: ACTIVE
roadmap: "v0.6.0 — Updated Legal Grading Engine (TT 34/2026/TT-BXD & QCVN 03:2022/BXD)"
---

# Project_Manager — Quản Lý Dự Án, Phân Cấp Công Trình & Lộ Trình Pháp Lý

> **Phiên bản:** v0.6.0 (Active)
> **Mục đích:** Phân cấp công trình chính xác theo quy định mới nhất, quản lý vòng đời dự án, milestone tiến độ, ma trận rủi ro và hồ sơ pháp lý dự án
> **Cập nhật:** 2026-10-21 — v0.6.0 (Cập nhật `project_grading.py` theo Thông tư 34/2026/TT-BXD, Thông tư 06/2021/TT-BXD & QCVN 03:2022/BXD)

---

## 1. TỔNG QUAN

**Project_Manager** là skill quản lý dự án toàn diện — phối hợp các skill kỹ thuật và quản lý vòng đời dự án xây dựng từ giai đoạn concept đến hoàn công.

### 1.1 Phạm vi hoạt động

| Phạm vi | Trạng thái | Ghi chú |
|----------|------------|---------|
| Phân cấp công trình & Thẩm quyền pháp lý | ✅ ACTIVE (v0.6) | Xét đủ 6 tiêu chí quy mô kết cấu (Bảng 2 PL II TT 34/2026 & TT 06/2021) + Cấp hậu quả C1–C3 & Tuổi thọ thiết kế (QCVN 03:2022/BXD) |
| Quản lý tiến độ & Milestone | ✅ ACTIVE | Theo dõi các giai đoạn TKCS → TKKT → BVTC → Nghiệm thu |
| Quản lý rủi ro (Risk Matrix) | ✅ ACTIVE | Phân loại rủi ro kỹ thuật, tiến độ, chi phí, pháp lý |
| Lộ trình pháp lý & Giấy phép | ✅ ACTIVE | Checklist GPXD, ĐTM, thẩm duyệt PCCC, thông báo khởi công |

---

## 2. CÁC CÔNG CỤ CLI ĐÃ KÍCH HOẠT (ACTIVE CLI TOOLS)

### 2.1 Xác định Cấp Công trình & Cấp Hậu quả (`project_grading.py` v2.0)
Xác định cấp công trình phục vụ quản lý hoạt động xây dựng theo **Bảng 2 Phụ lục II Thông tư 34/2026/TT-BXD** (hiệu lực từ 01/07/2026, đối chiếu chuyển tiếp **Thông tư 06/2021/TT-BXD**), đồng thời xác định **Cấp hậu quả (`C1, C2, C3`)**, hệ số tầm quan trọng $\gamma_n$ và **Thời hạn sử dụng theo thiết kế (`Mức 1–4`)** theo **QCVN 03:2022/BXD** và **TCVN 2737:2023 (Bảng H.1)**.

```bash
# Ví dụ Dự án Tổ hợp Thương mại SS1: 9 tầng nổi, cao 40m, GFA = 450,189.56 m², 1 hầm sâu 6.0m
python scripts/project_grading.py --type civil --height 40 --stories 9 --gfa 450189.56 --underground_depth 6.0 --underground_stories 1 --commercial_area 125049
```

**Tham số đầy đủ (Xét trọn vẹn 6 tiêu chí tại Mục 2.1.1 Bảng 2 Phụ lục II):**
- `--type`: Loại công trình (`civil` hoặc `marine`, mặc định `civil`)
- `--height`: Chiều cao công trình (m) — Đặc biệt `>200m (hoặc H*=150m)`, Cấp I `>75÷200m`, Cấp II `>28÷75m`, Cấp III `>6÷28m`, Cấp IV `≤6m`
- `--stories`: Số tầng cao trên mặt đất — Đặc biệt `>50`, Cấp I `25÷50`, Cấp II `8÷24`, Cấp III `2÷7`, Cấp IV `1`
- `--gfa`: Tổng diện tích sàn xây dựng kể cả hầm (m²) — **Cấp I `> 30,000 m²`**, Cấp II `> 10,000 ÷ 30,000 m²`, Cấp III `1,000 ÷ 10,000 m²`, Cấp IV `< 1,000 m²`
- `--span`: Nhịp kết cấu lớn nhất (m) — Đặc biệt `>200m`, Cấp I `100÷200m`, Cấp II `50÷<100m`, Cấp III `15÷<50m`, Cấp IV `<15m`
- `--underground_depth`: Độ sâu ngầm tính từ mặt đất đặt công trình tới **mặt trên của sàn tầng hầm sâu nhất** (m) — Cấp I `>18m`, Cấp II `6÷18m`, Cấp III `<6m`
- `--underground_stories`: Số tầng ngầm — Cấp I `≥5`, Cấp II `2÷4`, Cấp III `1`
- `--commercial_area`: Diện tích sàn kinh doanh thương mại (m²) — nếu `> 30,000 m²` thì thuộc Cấp hậu quả **`C3`** theo Mục A.1.1.3 Phụ lục A QCVN 03:2022/BXD
- `--iconic`: Cờ đánh dấu công trình có kiến trúc độc đáo / biểu tượng quốc gia (áp dụng Tuổi thọ thiết kế Mức 4 `≥ 100 năm`; mặc định công trình dân dụng/công nghiệp thông thường thuộc **Mức 3 `≥ 50 năm`** theo Bảng 1 Mục 2.2.2 QCVN 03:2022/BXD)

### 2.2 Sinh Biểu đồ Lộ trình Dự án (`project_roadmap.py`)
Sinh mã biểu đồ Mermaid cho Lộ trình Pháp lý Dự án theo Luật Xây dựng Việt Nam.

```bash
python scripts/project_roadmap.py --type private --grade I
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| **0.6.0** | **2026-10-21** | Cập nhật `project_grading.py` và `SKILL.md` theo Thông tư 34/2026/TT-BXD (hiệu lực 01/07/2026), bổ sung đầy đủ tiêu chí Tổng diện tích sàn GFA (`> 30,000 m²` Cấp I), Độ sâu ngầm, Số tầng ngầm (Mục 2.1.1 Bảng 2 Phụ lục II), và tích hợp Cấp hậu quả `C1–C3` + Thời hạn sử dụng `Mức 1–4` theo QCVN 03:2022/BXD & TCVN 2737:2023. |
| 0.5.0 | 2026-10-17 | Kích hoạt module theo dõi tiến độ milestone, ma trận rủi ro và legal checklist. |
