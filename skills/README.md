# 🎯 SKILLS HỆ THỐNG KỸ SƯ KẾT CẤU

> **Bắt đầu đọc từ đây!**

---

## 📁 CẤU TRÚC

```
.agents/skills/
│
├── _SYSTEM/                    ← 📖 ĐỌC TRƯỚC
│   ├── AGENTS.md              ← Quy tắc chung
│   ├── SKILL_INDEX.md          ← Chỉ mục & tra cứu nhanh
│   ├── STANDARDS_LOCK.md       ← Tiêu chuẩn chuẩn
│   └── CHANGELOG.md           ← Lịch sử thay đổi
│
├── _CORE_SKILLS/              ← 🔧 SKILLS CHÍNH
│   ├── Design_Evaluation/      ← Review, QC/QA, Tờ trình
│   ├── Structural_Design_Engineer/ ← Tính toán, Thuyết minh
│   └── Technical_Illustrator/  ← Vẽ 2D
│
├── _SUPPORT_SKILLS/           ← 🔧 SKILLS HỖ TRỢ
│   ├── Cost_Estimator/        ← So sánh chi phí, VE
│   ├── SKILL_FORENSIC/       ← Điều tra sự cố
│   └── SKILL_VERIFY/          ← Kiểm chứng kết quả
│
├── _SHARED/                   ← 🔧 UTILITIES CHUNG
│   ├── standards_mcp/         ← MCP Server tra cứu tiêu chuẩn
│   ├── memory/                ← Lưu context dự án
│   ├── workflows/             ← Workflow templates
│   └── README.md             ← Hướng dẫn sử dụng
│
├── _archive/                  ← 📦 File cũ
└── (bạn đang ở đây)
```

---

## 🚀 BẮT ĐẦU NHANH

### 1. Đọc `_SYSTEM/`

```
1. AGENTS.md      — Hiểu quy tắc chung
2. SKILL_INDEX.md — Biết skill nào cho việc gì
3. STANDARDS_LOCK — Biết tiêu chuẩn nào dùng
```

### 2. Chọn Skill

| Bạn cần | Dùng skill |
|----------|------------|
| Review hồ sơ | `_CORE_SKILLS/Design_Evaluation` |
| Tính cốt thép/dầm | `_CORE_SKILLS/Structural_Design_Engineer` |
| Vẽ mặt cắt/chi tiết | `_CORE_SKILLS/Technical_Illustrator` |
| So sánh chi phí | `_SUPPORT_SKILLS/Cost_Estimator` |
| Điều tra vết nứt/sự cố | `_SUPPORT_SKILLS/SKILL_FORENSIC` |
| Kiểm chứng kết quả | `_SUPPORT_SKILLS/SKILL_VERIFY` |

### 3. Luồng làm việc

```
User Request
    │
    ├─► SKILL phù hợp (xem bảng trên)
    │    │
    │    └─► Tính toán → Vẽ ảnh → Review → Báo cáo
    │
    └─► Output: .docx / .pdf / .md
```

---

## 📋 QUY TẮC VÀNG

| # | Quy tắc | Ví dụ |
|---|---------|-------|
| **1** | Cấm nhẩm tay | Luôn gọi script tính toán |
| **2** | Citation đủ 4 phần | `TCVN 2737:2023 — Điều 10.2 — Trang 45 — Hệ số tin cậy` |
| **3** | η ≤ 1.0 = Đạt | η = 0.85 ✅, η = 1.05 ❌ |
| **4** | Review Gate | Hiển thị kết quả, chờ User duyệt TRƯỚC khi xuất file |
| **5** | Deprecated = Không dùng | Kiểm tra `_CORE_SKILLS/.../_deprecated/` |

---

## 🔧 TOOLS HỖ TRỢ

### Validation Scripts
```bash
# Validate Technical_Illustrator registry
cd _CORE_SKILLS/Design_Evaluation/scripts
python validate_registry.py

# Validate SKILLKC JSON handoff
python validate_handoff.py <file.json>
```

### Standards MCP Server
```bash
cd _SHARED/standards_mcp
python server.py --test
```

### Project Memory
```bash
cd _SHARED/memory
python project_memory.py --project DUAN_A --action list
```

---

## ❓ CẦN HỖ TRỢ?

1. **Không biết dùng skill nào?** → Đọc `SKILL_INDEX.md` mục 8 (Quick Reference)
2. **Citation không rõ?** → Xem `STANDARDS_LOCK.md`
3. **Script lỗi?** → Kiểm tra có trong `_deprecated/` không
4. **Thay đổi gần đây?** → Xem `_SYSTEM/CHANGELOG.md`

---

## 📝 VERSION INFO

| File | Version |
|------|---------|
| AGENTS.md | v5.4 |
| SKILL_INDEX.md | v1.5 (Reporting Upgrade) |
| STANDARDS_LOCK.md | v2.4.0 (Reporting Upgrade) |
| Design_Evaluation | v2.2.0 (Reporting Upgrade) |
| Structural_Design_Engineer | v1.3.0 |
| Technical_Illustrator | v1.3.0 |
| SKILL_RFI | v1.2.0 |
| registry.json | v2.1.0 |

**Cập nhật:** 2026-08-31 — Reporting Upgrade v4.1 (Unified Dispatcher + 5 Audience Profiles)

### 🎨 Reporting Upgrade Highlights

⭐ **New: Unified Dispatcher** — `report_dispatcher.py` xuất 1 JSON → nhiều format (MD/DOCX/HTML) cho 5 audiences:

| Audience | Báo cáo cho |
|----------|-------------|
| `designer` | Tư vấn thiết kế (đầy đủ kỹ thuật + citations) |
| `engineer` | Kỹ sư tính toán (logs + charts) |
| `contractor` | Nhà thầu (thực tiễn + approval) |
| `owner` | Chủ đầu tư (dashboard + comparison) |
| `authority` | Cơ quan quản lý (official + full audit) |

```bash
python _CORE_SKILLS/Design_Evaluation/scripts/report_dispatcher.py \
    --handoff audit.json --audience designer --formats md,docx
```

Xem chi tiết: `_CORE_SKILLS/Design_Evaluation/references/REPORT_FORMATS.md`
