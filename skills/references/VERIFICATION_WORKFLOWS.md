## 18. Hệ sinh thái Skill & Pipeline Điển hình (v2.0 — Agentic)

> **MỚI v5.8:** Pipeline giờ tự động gọi skill tiếp theo qua INTER_SKILL_TRIGGERS. Xem chi tiết tại `INTER_SKILL_TRIGGERS.md`.

### 18.1 Agentic Workflow Flowchart

```
User Request
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  DISPATCHER (AGENTS.md §0)                                    │
│  Xác định Primary Skill + Entry Point                        │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  PRIMARY SKILL executes                                       │
│  1. Hoàn thành task chính                                   │
│  2. Check post-completion triggers                          │
│  3. Nếu trigger satisfied → Produce handoff JSON            │
│  4. Write to SHARED_CONTEXT/_active/                        │
│  5. Call next skill                                         │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  NEXT SKILL (automatic)                                      │
│  1. Read handoff từ SHARED_CONTEXT/                       │
│  2. Validate schema (SKILL_BRIDGE.md)                       │
│  3. If valid → process + check own triggers                │
│  4. If invalid → REJECT + request supplemental             │
└───────────────────────────────────────────────────────────────┘
    │
    └────────────────────────▶ Loop until END_STATE
```

### 18.2 CRITICAL: Design Pipeline (BẮT BUỘC Verify)

```
Structural_Design_Engineer
    │
    ├─► SKILL_CALC (section design)
    │
    ├─► SKILL_CONNECTION (connection design)
    │
    ├─► Technical_Illustrator (MODE 2D) — nếu cần hình
    │
    ├─► [POST-DESIGN-01] SKILL_VERIFY ──► QA CHECK (BẮT BUỘC)
    │                                      ⚠️ BLOCK file export
    │                                      cho đến khi PASS
    │
    └─► SKILL_CALC_REPORT (xuất Thuyết minh)

    [+ Auto-trigger nếu η ≤ 0.70]
    └─► Cost_Estimator (VE opportunity)
```

### 18.3 GEOTECH Pipeline (Auto-Handoff)

```
SKILL_GEOTECH
    │
    ├─► MODULE 1-10 (analysis)
    │
    ├─► [POST-GEOTECH-01] ──► Structural_Design_Engineer
    │                          (foundation params JSON)
    │
    ├─► [POST-GEOTECH-02] ──► Design_Evaluation
    │                          (base heave review)
    │
    └─► [POST-GEOTECH-03] ──► SKILL_FORENSIC
                                (adverse conditions alert)
```

### 18.4 REVIEW Pipeline

```
Design_Evaluation
    │
    ├─► SKILLKC (analysis)
    │
    ├─► Technical_Illustrator (MODE 2D)
    │
    ├─► [POST-EVAL-01] ──► Cost_Estimator
    │                       (nếu high cost detected)
    │
    ├─► [POST-EVAL-02] ──► SKILL_VERIFY
    │                       (nếu standard conflict)
    │
    └─► SKILL_REPORT (output)
```

### 18.5 VERIFY Flow

```
SKILL_VERIFY receives handoff
    │
    ├─► Check math consistency
    │
    ├─► Check standard compliance
    │
    ├─► Check cross-reference
    │
    └─► Check variance threshold (>5%)
            │
            ├─► PASS ──► Notify source skill
            │             → ALLOW file export
            │
            └─► FAIL (>5%) ──► REJECT source output
                                 → Request recalculate
                                 → Notify User
```

### 18.6 Quy trình Thẩm tra 7 Cổng Kiểm soát Bắt buộc (7-Gate Interlocked Pipeline — Gate 0–6)

Khi thực hiện nhiệm vụ **Thẩm tra Thiết kế Kết cấu & Đa bộ môn** (`Design_Evaluation`), nghiêm cấm nhảy cóc từ bước đọc lướt thuyết minh sang xuất báo cáo. Hệ thống bắt buộc đi qua tuần tự **7 Cổng Kiểm soát (Stage Gates 0–6)**:

```text
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

## 19. Version Control for Skills

Mỗi skill file (`SKILL.md`) phải có frontmatter version. Xem `CHANGELOG.md` tại cấp `.agents/skills/` để theo dõi lịch sử thay đổi của toàn bộ bộ skills.

---

