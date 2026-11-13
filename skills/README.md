# 🎯 SKILLS HỆ THỐNG KỸ SƯ KẾT CẤU

> **Bắt đầu đọc từ đây!**
> **Hướng dẫn chi tiết:** Xem `../USER_GUIDE.md` để biết cách vận hành toàn bộ hệ thống.

---

## 📁 CẤU TRÚC

```
.agents/
├── AGENTS.md                  <- Quy tac cot loi toan he thong
├── USER_GUIDE.md             <- Huong dan su dung chi tiet
├── .gitignore
├── .npm/                     <- Node.js packages (docx)
├── _SHARED/                  <- Shared infrastructure
│   ├── SHARED_CONTEXT/        <- Handoff JSON giua cac skill
│   ├── memory/                <- Luu context du an
│   └── workflows/             <- Template workflow
├── docs/                      <- Bao cao ky thuat
├── tests/                    <- Test suites
├── _archive/                 <- Luu tru file cu
├── _deprecated/              <- Code khong dung nua
│
└── skills/                    <- HE SINH THAI KY NANG (14 Skills)
    ├── Global_Dispatcher/     <- BO DIEU PHOI TRUNG TAM (Entry Point)
    ├── Design_Evaluation/     <- Review, Tham tra, To trinh
    ├── Structural_Design_Engineer/ <- Tinh toan ket cau
    ├── Technical_Illustrator/ <- Ve ky thuat 2D & Render 3D
    ├── SKILL_GEOTECH/        <- Dia ky thuat, Plaxis
    ├── SKILL_TEMPWORKS/      <- Cop pha, Van khuon
    ├── SKILL_VERIFY/         <- Kiem chung cheo
    ├── Cost_Estimator/       <- Du toan, VE, Carbon
    ├── SKILL_FORENSIC/       <- Giam dinh su co
    ├── SKILL_PHULUC/         <- Phu luc tinh toan
    ├── SKILL_RFI/            <- Quan ly RFI, NCR
    ├── Project_Manager/       <- Quan ly du an, MS Project Gantt & TT 34/2026
    ├── SKILL_BIM_COORDINATION/<- BIM Coordination & CAD Clash Audit
    ├── SKILL_DUAL_AGENT_BRIDGE/ <- Dieu phoi Dual-Agent Gemini <-> Claude
    ├── AGENTS.md             <- Quy tac lien-skill SSOT (v7.4)
    ├── SKILL_INDEX.md        <- Chi muc tra cuu
    ├── STANDARDS_LOCK.md     <- Khoa tieu chuan
    ├── SKILL_BRIDGE.md       <- Giao thuc data
    ├── INTER_SKILL_TRIGGERS.md<- Kich hoat tu dong
    └── CHANGELOG.md          <- Lich su phat trien
```

---

## 🚀 BẮT ĐẦU NHANH

### 1. Chọn Skill hoặc Dùng Global Dispatcher (Khuyến nghị)

> **MỚI:** Không cần nhớ từng skill! Global Dispatcher tự động phân tích prompt và định tuyến:
> ```bash
> python "Global_Dispatcher/scripts/intent_classifier.py" --prompt "<Yêu cầu của bạn>"
> ```

| Bạn cần | Dùng skill |
|----------|------------|
| Tự động phân loại / Multi-step pipeline | `Global_Dispatcher` |
| Review hồ sơ / Lập tờ trình | `Design_Evaluation` |
| Tính cốt thép / Thuyết minh dầm cột | `Structural_Design_Engineer` |
| Vẽ mặt cắt/chi tiết | `Technical_Illustrator` |
| So sánh chi phí / Value Engineering | `Cost_Estimator` |
| Điều tra vết nứt / Sự cố | `SKILL_FORENSIC` |
| Kiểm chứng kết quả / Check chéo ETABS | `SKILL_VERIFY` |
| Quản lý giao dịch RFI / Submittal / NCR | `SKILL_RFI` |
| Phụ lục tính toán step-by-step | `SKILL_PHULUC` |
| Địa kỹ thuật / SPT / CPT / Plaxis | `SKILL_GEOTECH` |
| Thiết kế cốp pha / Ván khuôn | `SKILL_TEMPWORKS` |
| Lập tiến độ MS Project Gantt & Phân cấp TT 34/2026 | `Project_Manager` |
| Rà soát xung đột BIM / Lưới trục / Cao độ thông thủy | `SKILL_BIM_COORDINATION` |
| Bàn giao ca & thẩm tra đối kháng Gemini ↔ Claude | `SKILL_DUAL_AGENT_BRIDGE` |

### 2. Luồng làm việc (Agentic Orchestration)

```
User Request (Ngôn ngữ tự nhiên)
    │
    ▼
Global_Dispatcher (intent_classifier.py + pipeline_builder.py)
    │
    ├─► Single Skill (Confidence >= 0.85) ──► Thực thi trực tiếp
    │
    └─► Multi-Skill Pipeline ─────────────► Chaining tuần tự qua Handoff JSON
         (Ví dụ: SDE tính ──► Review Gate ──► DE xuất tờ trình)
```

---

## 📋 QUY TẮC VÀNG

| # | Quy tắc | Ví dụ |
|---|---------|--------|
| **1** | Cấm nhẩm tay | Luôn gọi script tính toán |
| **2** | Citation đủ 4 phần | `TCVN 2737:2023 — Điều 10.2 — Trang 45` |
| **3** | η <= 1.0 = Đạt | η = 0.85 OK, η = 1.05 NOT OK |
| **4** | Review Gate | Hiển thị kết quả, chờ User duyệt TRƯỚC khi xuất file |
| **5** | Deprecated = Không dùng | Kiểm tra `_deprecated/` |

---

## 🔧 TOOLS HỖ TRỢ

```bash
# Chạy toàn bộ bộ kiểm thử tự động (.agents/tests/run_all_tests.py)
python ../tests/run_all_tests.py

# Standards Graph & Lookup
python ../_SHARED/standards/standards_graph.py --help

# Project Memory
cd ../_SHARED/memory
python project_memory.py --project DUAN_A --action list

# Đồng bộ báo cáo hệ sinh thái
python ../tools/sync_report.py --dry-run
```

---

## ❓ CẦN HỖ TRỢ?

1. **Không biết dùng skill nào?** -> Gửi cho Global_Dispatcher
2. **Citation không rõ?** -> Xem `STANDARDS_LOCK.md`
3. **Hướng dẫn chi tiết?** -> Xem `../USER_GUIDE.md`

---

## 📝 VERSION INFO

| File | Version |
|------|---------|
| USER_GUIDE.md | v2.0 |
| AGENTS.md | v7.4 |
| SKILL_INDEX.md | v2.2 |
| STANDARDS_LOCK.md | v3.3.0 |
| Global_Dispatcher | v2.0.0 |
| Design_Evaluation | v3.4.0 |
| Structural_Design_Engineer | v1.3.0 |
| Technical_Illustrator | v1.4.0 |
| Cost_Estimator | v1.4.0 |
| SKILL_FORENSIC | v1.2.0 |
| SKILL_VERIFY | v3.3.0 |
| SKILL_RFI | v1.4.0 |
| SKILL_PHULUC | v3.1.0 |
| SKILL_GEOTECH | v3.1.0 |
| SKILL_TEMPWORKS | v1.0.0 |
| Project_Manager | v2.0.0 |
| SKILL_BIM_COORDINATION | v1.4.0 |
| SKILL_DUAL_AGENT_BRIDGE | v3.1.0 |

**Cập nhật:** 2026-11-13 — Đồng bộ toàn diện 14 Production Skills (v7.5)
