---
name: Project_Manager
version: 0.5.0
last_updated: 2026-10-17
description: "Kỹ sư Quản lý Dự án AI: Quản lý vòng đời dự án, theo dõi tiến độ & milestone, kiểm soát lộ trình pháp lý, ma trận rủi ro (Risk Register), đánh giá tác động môi trường (ĐTM) và phòng cháy chữa cháy (PCCC). Kích hoạt khi: lập tiến độ, theo dõi milestone, quản lý rủi ro, tài liệu pháp lý, risk matrix, legal checklist."
status: ACTIVE
roadmap: "v0.5.0 — Phase 1 & 2 Active: Milestone & Risk Management"
---

# Project_Manager — Quản Lý Dự Án & Lộ Trình Pháp Lý

> **Phiên bản:** v0.5.0 (Active)
> **Mục đích:** Quản lý vòng đời dự án, milestone tiến độ, ma trận rủi ro và hồ sơ pháp lý dự án
> **Cập nhật:** 2026-10-17 — v0.5.0 (Active Modules: Milestones & Risk Register)

---

## 1. TỔNG QUAN

**Project_Manager** là skill quản lý dự án toàn diện — phối hợp các skill kỹ thuật và quản lý vòng đời dự án xây dựng từ giai đoạn concept đến hoàn công.

### 1.1 Mục tiêu

- Quản lý tiến độ và milestone
- Theo dõi văn bản pháp lý (GPXD, PCCC, ĐTM, Hợp đồng, Thông báo)
- Quản lý ma trận rủi ro dự án (Risk Register)
- Điều phối giao dịch kỹ thuật giữa các bên

### 1.2 Scope

| Phạm vi | Trạng thái | Ghi chú |
|----------|------------|---------|
| Quản lý tiến độ & Milestone | ✅ ACTIVE | Theo dõi các giai đoạn TKCS → TKKT → BVTC → Nghiệm thu |
| Quản lý rủi ro (Risk Matrix) | ✅ ACTIVE | Phân loại rủi ro kỹ thuật, tiến độ, chi phí, pháp lý |
| Lộ trình pháp lý & Giấy phép | ✅ ACTIVE | Checklist GPXD, ĐTM, thẩm duyệt PCCC, thông báo khởi công |
| ĐTM integration | 🔄 In Progress | Phối hợp dữ liệu với SKILL_GEOTECH |
| PCCC integration | 🔄 In Progress | Phối hợp kiểm tra an toàn cháy với Design_Evaluation |
| Tiến độ Gantt / MS Project | ⏳ Planned | Tích hợp định dạng xuất Gantt chart |

---

## 2. INTEGRATION VỚI CÁC SKILL KHÁC

### 2.1 Skill Dependencies

```
Project_Manager (planned)
├── Dependencies:
│   ├── Design_Evaluation (for technical milestones)
│   ├── SKILL_RFI (for document management)
│   └── Cost_Estimator (for budget tracking)
│
└── Will trigger:
    ├── Design_Evaluation (at design milestones)
    ├── SKILL_RFI (for legal documents)
    └── Cost_Estimator (for budget reviews)
```

### 2.2 Data Flow

```markdown
User Request
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  Project_Manager                                             │
│  - Parse project context                                     │
│  - Identify current phase                                    │
│  - Determine required skills                                 │
└───────────────────────────────────────────────────────────────┘
    │
    ├─► Design_Evaluation (if review phase)
    │
    ├─► SKILL_RFI (if document needed)
    │
    └─► Cost_Estimator (if budget check needed)
```

---

## 3. CÁC CÔNG CỤ CLI ĐÃ KÍCH HOẠT (ACTIVE CLI TOOLS)

### 3.1 Xác định Cấp Công trình (`project_grading.py`)
Xác định cấp công trình theo Thông tư 06/2021/TT-BXD, số bước thiết kế bắt buộc và thẩm quyền thẩm định (Bộ Xây dựng / Sở Xây dựng).

```bash
# Công trình dân dụng: chiều cao 45m, 12 tầng, nhịp lớn nhất 24m
python scripts/project_grading.py --type civil --height 45 --stories 12 --span 24

# Công trình trên mặt nước / công trình biển: sức chứa 600 người
python scripts/project_grading.py --type marine --capacity 600
```

**Tham số:**
- `--type`: Loại công trình (`civil` hoặc `marine`, mặc định `civil`)
- `--height`: Chiều cao công trình (m)
- `--stories`: Số tầng công trình
- `--span`: Nhịp kết cấu lớn nhất (m)
- `--capacity`: Sức chứa (người)

**Đầu ra mẫu (JSON):**
```json
{
  "Project_Grade": "Cấp II",
  "Determining_Factors": [
    "Số tầng 12 (8-24) hoặc Chiều cao 45.0 (28-75) hoặc Nhịp 24.0 (50-100)"
  ],
  "Design_Steps_Required": 2,
  "Appraisal_Authority": "Sở Xây dựng (Tỉnh/Thành phố)"
}
```

### 3.2 Sinh Biểu đồ Lộ trình Dự án (`project_roadmap.py`)
Sinh mã biểu đồ Mermaid cho Lộ trình Pháp lý Dự án theo Luật Xây dựng Việt Nam (Luật Đầu tư 2020, Luật Xây dựng, NĐ 15/2021, NĐ 06/2021, NĐ 136/2020 PCCC).

```bash
# Dự án vốn tư nhân, công trình Cấp II
python scripts/project_roadmap.py --type private --grade II

# Dự án đầu tư công, công trình Cấp I
python scripts/project_roadmap.py --type public --grade I
```

**Tham số:**
- `--type`: Loại vốn đầu tư (`private` tư nhân, `public` đầu tư công)
- `--grade`: Cấp công trình (`Đặc biệt`, `I`, `II`, `III`, `IV`)

**Đầu ra:** Đoạn mã Mermaid Flowchart 3 giai đoạn (Chuẩn bị → Thực hiện → Kết thúc) kèm đánh dấu các bước quan trọng trên đường găng (Critical Path: ĐTM, PCCC, Thẩm định TKCS).

---

## 4. CÁC MODULE DỰ KIẾN (PLANNED MODULES)

### MODULE 1: Project Lifecycle Manager
**Chức năng:** Theo dõi các giai đoạn dự án

```
Các giai đoạn:
├── 1. Concept & Pre-design
│   ├── Feasibility study
│   ├── Preliminary design
│   └── Environmental assessment (ĐTM)
│
├── 2. Design & Approval
│   ├── Detailed design (BVTC)
│   ├── Technical review
│   ├── Fire safety (PCCC) approval
│   └── Permit acquisition
│
├── 3. Tendering & Contracting
│   ├── Bid evaluation
│   ├── Contract negotiation
│   └── Contract award
│
├── 4. Construction
│   ├── Shop drawing review
│   ├── Progress monitoring
│   └── Quality control
│
└── 5. Completion & Handover
    ├── Testing & commissioning
    ├── Final inspection
    └── As-built documentation
```

### MODULE 2: Legal Document Tracker
**Chức năng:** Theo dõi văn bản pháp lý

```
Document Types:
├── Giấy phép (Permits)
│   ├── GP XD (Giấy phép xây dựng)
│   ├── PCCC (Phòng cháy chữa cháy)
│   └── Môi trường (ĐTM)
│
├── Hợp đồng (Contracts)
│   ├── Hợp đồng thiết kế
│   ├── Hợp đồng thi công
│   └── Hợp đồng giám sát
│
└── Thông báo (Notices)
    ├── Notice to Proceed
    ├── Variation orders
    └── Completion certificate
```

### MODULE 3: Risk Manager
**Chức năng:** Quản lý rủi ro dự án

```
Risk Categories:
├── Kỹ thuật (Technical)
│   ├── Design changes
│   ├── Soil conditions
│   └── Material availability
│
├── Tài chính (Financial)
│   ├── Cost overrun
│   ├── Payment delays
│   └── Currency fluctuation
│
├── Pháp lý (Legal)
│   ├── Permit delays
│   ├── Contract disputes
│   └── Regulatory changes
│
└── Môi trường (Environmental)
    ├── Weather impacts
    └── Contamination discovery
```

### MODULE 4: Milestone Tracker
**Chức năng:** Theo dõi milestone và deadline

```
Milestone Types:
├── Design Milestones
│   ├── BVTC completion
│   ├── PCCC approval
│   └── ĐTM approval
│
├── Construction Milestones
│   ├── Foundation complete
│   ├── Structure complete
│   └── Handover
│
└── Financial Milestones
    ├── Payment schedule
    └── Final settlement
```

---

## 4. PLANNED SCRIPTS

```
Project_Manager/
├── SKILL.md                           ← BẠN ĐANG Ở ĐÂY (Placeholder)
├── scripts/
│   ├── project_phase_detector.py      ← Xác định giai đoạn hiện tại
│   ├── milestone_tracker.py            ← Theo dõi milestone
│   ├── risk_matrix_generator.py        ← Tạo ma trận rủi ro
│   ├── document_registry.py            ← Registry văn bản pháp lý
│   └── timeline_generator.py           ← Tạo timeline/Gantt
├── templates/
│   ├── project_charter.docx           ← Template khởi đầu dự án
│   ├── risk_register.xlsx             ← Đăng ký rủi ro
│   └── milestone_report.docx          ← Báo cáo milestone
└── data/
    └── legal_checklist.json           ← Checklist pháp lý
```

---

## 5. INTERFACE VỚI NGƯỜI DÙNG

### 5.1 Planned Commands

```
User: "Dự án đang ở giai đoạn nào?"
→ Project_Manager: "Dự án đang ở giai đoạn Thiết kế BVTC, milestone tiếp theo: PCCC approval"

User: "Cập nhật tiến độ dự án"
→ Project_Manager: "Vui lòng cung cấp % hoàn thành cho các hạng mục:
   - Thiết kế: XX%
   - Giấy phép: XX%
   - Thi công: XX%"

User: "Tạo báo cáo rủi ro"
→ Project_Manager: "Đang tạo Risk Register..."

User: "Checklist pháp lý còn thiếu gì?"
→ Project_Manager: "Các văn bản pháp lý còn thiếu:
   - [ ] PCCC approval
   - [ ] ĐTM certificate
   - [ ] Hợp đồng GĐVT"
```

### 5.2 Integration Prompts

```
Khi Design_Evaluation hoàn thành:
→ Project_Manager: "Design milestone đạt. Cập nhật vào project timeline."

Khi SKILL_RFI tạo NCR:
→ Project_Manager: "NCR mới được tạo - thêm vào Risk Register."

Khi Cost_Estimator phát hiện vượt budget:
→ Project_Manager: "Budget alert - cập nhật Risk Register và thông báo PM."
```

---

## 6. ROADMAP

### Phase 1 & 2 (v0.5.0) ✅ ACTIVE
- [x] Phase detector & Milestone tracking
- [x] Risk Matrix & Risk Register protocol
- [x] Legal checklist & Permit tracker

### Phase 3 (v0.8.0) — Q4/2026
- [ ] Automated ĐTM / Geotech coordination
- [ ] PCCC compliance cross-check with Design_Evaluation
- [ ] Weekly progress report generator

### Phase 4 (v1.0.0) — Q1/2027
- [ ] MS Project / Gantt chart sync
- [ ] Real-time project KPI dashboard

---

## 7. NOTES

### 7.1 Vai trò & Trách nhiệm
- Skill này bổ trợ quản lý tiến độ và rủi ro dự án, phối hợp với các skill tính toán kỹ thuật.
- Hỗ trợ PM và Chủ đầu tư theo dõi toàn diện các mốc phê duyệt và văn bản pháp lý.

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | 2026-10-17 | Nâng cấp từ Placeholder lên v0.5.0 Active: Kích hoạt module theo dõi tiến độ milestone, ma trận rủi ro và legal checklist |
| 0.1.0 | 2026-09-25 | Initial placeholder |
