# AGENTS.md — Quy tắc Liên Skill Toàn bộ Bộ Kỹ năng Kết cấu (v7.0 — 7-Gate Master Audit Architecture)

> **Phạm vi:** Áp dụng cho **MỌI skill** trong `.agents/skills/` và hệ thống Dual-Agent (Gemini Antigravity ↔ Claude Code).
> **Vị trí chuẩn:** `.agents/AGENTS.md` (đồng bộ tại `.agents/skills/AGENTS.md`).
> **Cập nhật:** 2026-10-26 — **v7.0 (Nâng cấp Toàn diện Quy trình Thẩm tra 7 Cổng Kiểm soát Ban Xây dựng Cao cấp & 20 Hard-Rules Thực chiến Dự án Tân Hỷ)**

---

## 0. Bảng Điều phối Liên-Skill (Dispatcher — ĐỌC TRƯỚC TIÊN)

| Câu hỏi phân xử | Trả lời | Skill kích hoạt | Entry point & Công cụ bắt buộc |
|---|---|---|---|
| Đại diện Chủ đầu tư / Ban Xây dựng Cao cấp — *thẩm tra thiết kế, review bản vẽ KT/KC, phân tích tải trọng/tổ hợp/đường truyền lực, xử lý RFI/NCR, xuất Báo cáo Thẩm tra*? | Có | **`Design_Evaluation` (v3.1)** | `SKILL.md` -> `SKILLKC.md` -> `SKILL_BIM_COORDINATION` -> `SKILL_VERIFY` (`drawing_calc_crosscheck.py`) -> `SKILL_RFI` -> `SKILL_REPORT.md` |
| Đóng vai đơn vị thiết kế — *tự tính tiết diện / cốt thép / bu lông / đường hàn, xuất Thuyết minh tính toán*? | Có | **`Structural_Design_Engineer`** | `SKILL_CALC.md` / `SKILL_CONNECTION.md` / `SKILL_CALC_REPORT.md` |
| Tạo phụ lục tính toán chi tiết step-by-step hoặc xuất Word theo 2 Bộ Chuẩn (BKTECHS / TVTK)? | Có | **`SKILL_PHULUC` (`skill-phuluc-tmtt` v3.0)** | `SKILL.md` / `scripts/docx_generator_v2.py` |
| Rà soát xung đột lưới trục, cao độ thông thủy 3D và xung đột nội bộ bản vẽ (Mặt bằng ↔ Mặt cắt ↔ Chi tiết ↔ Tag thép)? | Có | **`SKILL_BIM_COORDINATION` (v1.1)** | `SKILL.md` (3-Tier Spatial & Blueprint Clash Audit) |
| Kiểm chứng chéo 6 tầng (Giải mã EMF/Vector gốc, quét lỗi `#VALUE!`, truy vết `Joint Reactions` ETABS, tính diện tích cốt thép $A_{s,\text{drawing}} \ge A_{s,tt}$)? | Có | **`SKILL_VERIFY` (v3.1)** | `SKILL.md` / `scripts/drawing_calc_crosscheck.py` |
| Quản lý giao dịch kỹ thuật, phân tầng rủi ro Critical/Major/Minor và phát hành phiếu `RFI-DES-YYYYMMDD-NNN`, `NCR-DES-YYYYMMDD-NNN`? | Có | **`SKILL_RFI` (v1.3)** | `SKILL.md` (6-Field Legal & Technical Enforcement) |

---

## 1. QUY TRÌNH THẨM TRA 7 CỔNG KIỂM SOÁT BẮT BUỘC (7-GATE INTERLOCKED PIPELINE — MỚI V7.0)

Khi thực hiện nhiệm vụ **Thẩm tra Thiết kế Kết cấu & Đa bộ môn**, nghiêm cấm nhảy cóc từ bước đọc lướt thuyết minh sang xuất báo cáo. Hệ thống bắt buộc đi qua tuần tự **7 Cổng Kiểm Soát (Stage Gates 0–6)**:

```
Hồ sơ Đầu vào (TMB, Bản vẽ KT, Bản vẽ KC, Thuyết minh TMKC .docx/.pdf, Mô hình ETABS, Báo giá .xlsx)
 │
 ▼
[GATE 0] Design_Evaluation + STANDARDS_LOCK.md
 │ • Bóc tách Bảng cân bằng đất trên TMB (tách GFA giai đoạn cấp phép vs toàn khu).
 │ • Phân cấp công trình theo TT 34/2026/TT-BXD (max GFA, Nhịp L_max, Chiều cao H) & Cấp hậu quả QCVN 03:2022/BXD.
 │ • Kiểm tra 02 Hold Points tiên quyết: (1) Báo cáo khảo sát ĐCCT có dấu pháp nhân; (2) Thuyết minh chịu lửa QCVN 06:2022/BXD.
 ▼
[GATE 1] SKILL_VERIFY (EMF Deep Parser) + SKILL_BIM_COORDINATION
 │ • Giải nén word/media/image*.emf trong mọi file .docx -> Đọc 100% bản ghi UTF-16LE của bảng tính gốc.
 │ • Render 100% trang PDF bản vẽ -> Kiểm đếm tờ bản vẽ bị thiếu theo từng hạng mục & quét lỗi #VALUE!, #REF!.
 ▼
[GATE 2] SKILLKC — Thẩm tra Chuyên sâu Tải trọng & Phân tích Tải (TCVN 2737:2023)
 │ • Tĩnh tải: Tách D_permanent và D_Solar; truy vết 100% tải giàn thao tác treo / trần M&E / cầu trục trên bản vẽ (KC-12..15).
 │ • Hoạt tải: Hoạt tải mái >= 0.30 kN/m² (γf=1.3); hoạt tải xe PCCC trên nắp bể ngầm 20–30 kPa (tải trục 100–120 kN).
 │ • Tải gió: Tính Gf đúng Phụ lục E (nhà thép ζ=0.02, cấm công thức tự chế Gf=0.85+h/1010); bắt buộc tổ hợp ce với áp lực gió
 │   bên trong nhà ci (+0.2/-0.3 đến +0.6 khi bung cửa); bắt buộc kiểm toán xà gồ dưới tải gió bốc ngược (Up, cấm nhập Gió=0).
 │ • Áp lực đất tĩnh K0 = 1-sin(φ) tách rời áp lực nước ngầm; nhiệt độ & kháng chấn TCVN 9386:2025.
 ▼
[GATE 3] SKILLKC — Thẩm tra Tổ hợp Tải trọng Nghịch đảo & Cực đoan (ULS / SLS)
 │ • Tổ hợp Gió bốc / Nhổ cột / Lật móng / Đẩy nổi: Bắt buộc dùng 0.90 * D_permanent (TUYỆT ĐỐI KHÔNG cộng tải Solar chưa lắp!).
 │ • Tổ hợp Bể ngầm / Tầng hầm: Cấm gộp nước trong bể (HTN) và đất ngoài bể (TTĐ) tự triệt tiêu nhau; bắt buộc xét tổ hợp
 │   'Bể rỗng bảo trì + Đầy đất & Nước ngầm + Xe PCCC chạy trên nắp'.
 │ • Tổ hợp SLS: Xét từng hướng gió tiêu chuẩn (γf=1.0) riêng biệt, không dùng hàm bao ENVE.
 ▼
[GATE 4] SKILLKC — Phân tích Đường truyền lực 3D, Sơ đồ Tính & Ổn định Kết cấu
 │ • Tương thích Sơ đồ Chân cột (Khớp/Ngàm) với độ cứng bản đế và sự tách rời đáy móng (σ_min < 0 gây xoay móng θ làm vọt độ võng
 │   công son; khung mảnh μx > 2.0 phải xét hiệu ứng bậc 2 P-Delta).
 │ • Kiểm tra chiều dài tự do thực tế Lef của cánh dưới chịu nén tại vùng mô men âm nách kèo (có Flange Stay trên bản vẽ không?).
 │ • Kiểm tra độ mảnh bản bụng (λ_w, λ_uw) -> Bắt buộc vẽ sườn ngang và sườn dọc; kiểm tra đường truyền lực dọc nhà tại trục cột giữa
 │   và kiểm toán chống đẩy nổi Archimedes (K_đn >= 1.15).
 ▼
[GATE 5] SKILL_BIM_COORDINATION + SKILL_VERIFY (drawing_calc_crosscheck.py) — Đối soát 4 Chiều
 │ • Truy vết tọa độ nút chân cột trong bảng Joint Reactions của ETABS sang bảng tính móng (chống gán nhầm nút cột giữa/cột biên).
 │ • Đo độ lệch tâm cổ cột e0 trên Mặt bằng móng so với Mặt cắt; tính diện tích thép bản vẽ As_drawing >= As,tt.
 │ • Đối chiếu kích thước móng, cổ cột, dầm, xà gồ, số lượng cấu kiện và ký hiệu trục giữa KT ↔ MB ↔ MC/Chi tiết ↔ TMKC.
 ▼
[GATE 6] SKILL_RFI + SKILL_REPORT — Chế tài Kỹ thuật & Xuất bản Báo cáo Chuẩn Corporate
   • Phát hành Phiếu RFI-DES-YYYYMMDD-NNN và Biên bản đình chỉ NCR-DES-YYYYMMDD-NNN.
   • Kiểm toán công thức sống Excel (cấm gộp ô làm mất công thức liên kết) và xuất Báo cáo DOCX (Body >= 11pt, Table >= 10pt, 300 DPI).
```

---

## 2. Các Quy tắc Cốt lõi Khác (Giữ nguyên & Khóa cứng)
- **Đường dẫn Tuyệt đối & UTF-8:** Luôn dùng đường dẫn tuyệt đối; mọi script Python phải cấu hình `utf-8`.
- **No Hallucination & Deterministic Math:** Không tự nhẩm phép toán kỹ thuật; mọi kết luận phải kèm chỉ số định lượng ($\eta = D/C$, $A_{s,\text{drawing}}$ vs $A_{s,tt}$, $K_{\text{đn}}$, $\sigma_{\min}$).
- **Typography & Visual Standards:** Báo cáo `.docx` bắt buộc đạt sàn cỡ chữ thân bài $\ge 11\text{pt}$, bảng biểu $\ge 10\text{pt}$, có tối thiểu 2–3 biểu đồ phân tích định lượng 300 DPI.

---

## Changelog
| Version | Date | Changes |
|---|---|---|
| **7.0** | **2026-10-26** | **Master 7-Gate Construction Board Release:** Tích hợp dây chuyền 7 Cổng Kiểm soát (Gate 0–6), giải mã nhị phân EMF (`EMF Deep Parser`), đối soát 4 chiều (`drawing_calc_crosscheck.py`) và 20 Hard-Rules chuyên sâu về Tải trọng, Tổ hợp nghịch đảo & Đường truyền lực 3D từ thực chiến Dự án Tân Hỷ. |
| 6.1 | 2026-10-12 | Phase 1 Infrastructure + SKILL_TEMPWORKS |
