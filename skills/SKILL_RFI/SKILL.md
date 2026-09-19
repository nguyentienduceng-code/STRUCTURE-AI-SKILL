---
name: SKILL_RFI
version: 1.2.0
last_updated: 2026-08-30
description: "Kỹ sư Quản lý Giao dịch Kỹ thuật AI: Quản lý toàn bộ RFI, NCR, Submittal, Shop Drawing, Change Order và các tài liệu giao dịch với Chủ đầu tư (Owner), Tư vấn Giám sát (CSHT), Nhà thầu (Contractor), và Đơn vị Thiết kế (Designer). Tự động phân loại mức độ ưu tiên, theo dõi deadline, leo thang khi quá hạn, và tích hợp phản hồi vào phân tích kỹ thuật. Kích hoạt khi: tạo RFI/NCR/Submittal, theo dõi, phản hồi, đối chiếu với các bên liên quan."
---

# SKILL_RFI — Quản lý Giao dịch Kỹ thuật (Technical Document Management)

## Tổng quan

**SKILL_RFI** là module quản lý giao dịch kỹ thuật toàn diện — quản lý RFI, NCR, Submittal, Shop Drawing, Change Order và các tài liệu giao dịch với tất cả các bên trong dự án xây dựng.

Khác với module đơn lẻ, SKILL_RFI quản lý **vòng đời đầy đủ** của tất cả các loại giao dịch:
- Tạo tài liệu từ Data Missing hoặc phát hiện sự cố
- Theo dõi trạng thái & deadline theo từng loại
- Leo thang khi quá hạn
- Đối chiếu phản hồi với yêu cầu ban đầu

---

## Các Loại Giao dịch (Document Types)

| Loại | Mã | Mô tả | Gửi cho | Deadline |
|------|------|--------|---------|----------|
| **RFI** | Request for Information | Yêu cầu làm rõ thông tin | Designer/CSHT | 7 ngày |
| **NCR** | Non-Conformance Report | Báo cáo không phù hợp | Contractor | 24h |
| **Submittal** | Material/Shop Drawing | Bản vẽ thi công/mẫu vật liệu | Designer/CSHT | 14 ngày |
| **Change Order** | CO | Yêu cầu thay đổi khối lượng | Owner | 3 ngày |
| **Tech Query** | TQ | Câu hỏi kỹ thuật chuyên sâu | Designer | 5 ngày |
| **Pre-Bid RFI** | PB-RFI | Làm rõ trước đấu thầu | Owner | 3 ngày |

---

## Ma trận Giao dịch theo Bên (Party Matrix)

### Các bên liên quan trong dự án:

| Bên | Vai trò | Nhận từ | Gửi đến |
|------|---------|----------|----------|
| **Owner** (Chủ đầu tư) | Chủ sở hữu dự án | CO, Final Submittal | Approval |
| **Designer** (Đơn vị TK) | Thiết kế bản vẽ | RFI, TQ, Shop Drawing | RFI Response, Design Clarification |
| **CSHT** (Tư vấn GS) | Giám sát thi công | RFI, NCR, Submittal | Approval, Observation Report |
| **Contractor** (Nhà thầu) | Thi công | RFI, NCR, Observation | Shop Drawing, CO, NCR Response |
| **QC/QA** (Ban QLDA) | Quản lý chất lượng | Inspection Report, Test Result | Directive |

### Luồng giao dịch:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CÁC BÊN LIÊN QUAN                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    Owner ◄───────► Designer ◄───────► CSHT ◄───────► Contractor       │
│      │              │              │              │                      │
│      │   CO/Approval│  Design     │   Directive │   Shop Drawing      │
│      │              │  Clarific.   │   /RFI      │   /Submittal       │
│      ▼              ▼              ▼              ▼                      │
│   (Approval)   (RFI Resp)   (Inspection)   (NCR if issue)              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quy trình Chuẩn (5 Bước)

### BƯỚC 1: Tạo Giao dịch (Document Creation)

**Tự động khi:**
- `Design_Evaluation` phát hiện `Data Missing: [...]` → Tạo RFI
- Phát hiện sự cố/NCR → Tạo NCR
- Nhà thầu gửi Shop Drawing → Tạo Submittal log
- Thay đổi khối lượng → Tạo Change Order

**Mã giao dịch chuẩn:**
```
{Loại}-{Bên gửi}-{YYYYMMDD}-{NNN}
VD: RFI-DES-20260830-001  (RFI từ Designer)
VD: NCR-CNT-20260830-001  (NCR từ Contractor)
VD: SUB-CNT-20260830-001  (Submittal từ Contractor)
```

**Phân loại ưu tiên:**

| Mức | Ký hiệu | Trigger | Deadline | Action |
|------|----------|---------|----------|--------|
| 🔴 CRITICAL | An toàn/Kết cấu | "sập", "nguy hiểm", "sai tiết diện" | 24h | Dừng thi công |
| 🟠 URGENT | Ảnh hưởng tiến độ | "chậm", "phát sinh", "thay đổi" | 3 ngày | Leo thang ngay |
| 🟡 HIGH | Kỹ thuật quan trọng | "thiếu thông tin", "không rõ" | 7 ngày | Theo dõi |
| 🟢 NORMAL | Kỹ thuật thông thường | "cần xác nhận", "làm rõ" | 14 ngày | Standard |
| 🔵 ROUTINE | Hành chính | "bổ sung", "cập nhật" | 21 ngày | Batch review |

---

### BƯỚC 2: Theo dõi Giao dịch (Document Tracking)

**Theo dõi các trạng thái:**

```
Draft → Submitted → Under Review → Approved / Rejected / Revised → Closed
```

**Trường theo dõi:**
| Trường | Mô tả |
|--------|--------|
| `Doc_Code` | Mã giao dịch duy nhất |
| `Doc_Type` | Loại: RFI/NCR/Submittal/CO/TQ |
| `From_Party` | Bên gửi |
| `To_Party` | Bên nhận |
| `Status` | Trạng thái hiện tại |
| `Days_Open` | Số ngày đã mở |
| `Days_To_Deadline` | Số ngày đến deadline |
| `Overdue` | Boolean: đã quá hạn chưa |
| `Escalation_Level` | Cấp leo thang (0-3) |

**Script:** `scripts/document_tracker.py`

---

### BƯỚC 3: Leo thang Tự động (Escalation)

**Quy trình leo thang:**

```
Level 0: Mới tạo (0-7 ngày)
    ↓ Days_To_Deadline ≤ 2
Level 1: Cảnh báo sắp quá hạn → Email notification
    ↓ Không phản hồi sau 3 ngày
Level 2: Leo thang lên TP.BQLDA
    ↓ Không phản hồi sau 3 ngày
Level 3: Leo thang lên Ban Giám đốc → Đình chỉ công việc liên quan
```

**Script:** `scripts/rfi_escalation.py`

---

### BƯỚC 4: Xử lý Phản hồi (Response Handling)

**Khi nhận phản hồi:**
1. Đọc nội dung phản hồi
2. Kiểm tra đã trả lời đủ câu hỏi chưa
3. Đánh giá chất lượng phản hồi
4. Nếu đủ → đánh dấu `Approved`
5. Nếu chưa đủ → tạo RFI tiếp theo hoặc leo thang
6. Đối chiếu với `Data Missing` ban đầu

**Script:** `scripts/rfi_response_handler.py`

---

### BƯỚC 5: Tích hợp vào Phân tích (Integration)

**Sau khi được Approved:**
1. Trích xuất dữ liệu từ phản hồi
2. Cập nhật vào phân tích kỹ thuật
3. Tính toán lại với dữ liệu mới
4. Đánh dấu `Verified` nếu kết quả hợp lý
5. Xuất báo cáo cập nhật

**Script:** `scripts/rfi_integration.py`

---

## Chi tiết từng Loại Giao dịch

### 1. RFI (Request for Information)

**Mục đích:** Yêu cầu làm rõ thông tin thiết kế/kỹ thuật

**Luồng:**
```
Designer/CSHT gửi RFI → Designer nhận → Trả lời trong 7 ngày → Đóng RFI
```

**Template câu hỏi:**
1. Thông tin cần làm rõ là gì?
2. Bối cảnh phát hiện vấn đề?
3. Ảnh hưởng nếu không làm rõ?
4. Bản vẽ/tài liệu liên quan?

---

### 2. NCR (Non-Conformance Report)

**Mục đích:** Báo cáo khi phát hiện công việc không phù hợp thiết kế/TCVN

**Mức độ nghiêm trọng:**
| Cấp | Ký hiệu | Trigger | Hành động |
|------|----------|---------|-----------|
| 1 | Minor | Sai lệch nhỏ, khắc phục được | Sửa và kiểm tra |
| 2 | Major | Ảnh hưởng chất lượng | Dừng, đề xuất, chờ duyệt |
| 3 | Critical | Ảnh hưởng kết cấu/an toàn | Dừng ngay, báo cáo Owner |

**Template NCR:**
```
1. Mô tả không phù hợp (What)
2. Vị trí cụ thể (Where)
3. Thời điểm phát hiện (When)
4. Nguyên nhân dự kiến (Why)
5. Ảnh hưởng tiềm ẩn (Impact)
6. Đề xuất khắc phục (Proposal)
7. Phản hồi của Contractor
8. Đóng NCR khi đã xử lý xong
```

---

### 3. Submittal (Shop Drawing / Material)

**Mục đích:** Nhà thầu gửi bản vẽ thi công/mẫu vật liệu để được duyệt

**Loại Submittal:**
| Loại | Mô tả | Deadline duyệt |
|------|--------|-----------------|
| Shop Drawing | Bản vẽ thi công chi tiết | 14 ngày |
| Material Sample | Mẫu vật liệu | 7 ngày |
| Product Data | Catalogs, specs | 10 ngày |
| Mockup | Mẫu thử nghiệm | 21 ngày |
| Test Report | Kết quả thí nghiệm | 5 ngày |

**Trạng thái duyệt:**
- **Approved** ✅: Có thể thi công theo bản vẽ
- **Approved as Noted** ⚠️: Thi công theo ghi chú kèm theo
- **Revise and Resubmit** 🔄: Cần sửa và gửi lại
- **Rejected** ❌: Không được phép thi công

---

### 4. Change Order (CO)

**Mục đích:** Yêu cầu thay đổi khối lượng/thiết kế ảnh hưởng đến cost

**Thông tin bắt buộc:**
| Trường | Mô tả |
|--------|--------|
| `CO_Number` | Số CO |
| `Reference` | Số RFI/NCR liên quan |
| `Description` | Mô tả thay đổi |
| `Quantity_Change` | Thay đổi KL (+/-) |
| `Unit_Price` | Đơn giá |
| `Total_Cost_Impact` | Tổng ảnh hưởng chi phí |
| `Time_Impact` | Ảnh hưởng tiến độ (ngày) |
| `Justification` | Căn cứ thay đổi |

---

### 5. Tech Query (TQ)

**Mục đích:** Câu hỏi kỹ thuật chuyên sâu cần phân tích

**Khác với RFI:**
- TQ: Câu hỏi phức tạp, cần tính toán/phân tích
- RFI: Câu hỏi đơn giản, cần xác nhận thông tin

**Luồng:**
```
TQ gửi đi → Designer nghiên cứu → Trả lời chi tiết → Cập nhật thiết kế nếu cần
```

---

## Cấu trúc Thư mục

```
SKILL_RFI/
├── SKILL.md                           ← BẠN ĐANG Ở ĐÂY
├── scripts/
│   ├── document_generator.py        ← Tạo RFI/NCR/Submittal/CO/TQ
│   ├── document_tracker.py          ← Theo dõi trạng thái
│   ├── rfi_escalation.py            ← Leo thang tự động
│   ├── rfi_response_handler.py      ← Xử lý phản hồi
│   ├── rfi_integration.py           ← Tích hợp vào phân tích
│   └── rfi_dashboard.py            ← Dashboard tổng quan
├── templates/
│   ├── RFI_Template.docx           ← Template RFI chuẩn
│   ├── NCR_Template.docx            ← Template NCR chuẩn
│   ├── Submittal_Log_Template.xlsx ← Bảng theo dõi Submittal
│   └── CO_Template.docx           ← Template Change Order
├── data/
│   ├── document_registry.json      ← Registry tất cả tài liệu
│   └── party_contacts.json         ← Danh bạ các bên liên quan
└── references/
    ├── Document_Types_Guide.md     ← Chi tiết từng loại
    ├── Party_Matrix.md            ← Ma trận trách nhiệm
    └── Escalation_Protocol.md      ← Quy trình leo thang
```

---

## Document Registry (document_registry.json)

**Cấu trúc registry:**
```json
{
  "project_name": "Tên Dự án",
  "last_updated": "2026-08-30",
  "parties": {
    "Owner": { "name": "...", "contact": "..." },
    "Designer": { "name": "...", "contact": "..." },
    "CSHT": { "name": "...", "contact": "..." },
    "Contractor": { "name": "...", "contact": "..." }
  },
  "documents": {
    "RFI": [...],
    "NCR": [...],
    "Submittal": [...],
    "CO": [...],
    "TQ": [...]
  },
  "statistics": {
    "rfi": { "total": 15, "open": 3, "overdue": 1 },
    "ncr": { "total": 5, "open": 2, "critical": 1 },
    "submittal": { "total": 50, "pending": 10, "approved": 35 }
  }
}
```

---

## Dashboard Template

**Hiển thị khi User hỏi "Document status":**

```
╔══════════════════════════════════════════════════════════════════╗
║           TECHNICAL DOCUMENT DASHBOARD — {Project Name}        ║
╠══════════════════════════════════════════════════════════════════╣
║  RFI: 15 (3 Open, 1 Overdue)                              ║
║  NCR: 5 (2 Open, 1 Critical)                               ║
║  Submittal: 50 (10 Pending, 35 Approved)                    ║
║  Change Order: 3 (1 Pending Approval)                      ║
╠══════════════════════════════════════════════════════════════════╣
║  🔴 CRITICAL ITEMS                                         ║
║  ├─ NCR-CNT-20260830-001: Vết nứt cột tầng 3 (2 ngày)   ║
║  └─ RFI-DES-20260829-005: Xác nhận thép cột (quá hạn!)  ║
╠══════════════════════════════════════════════════════════════════╣
║  🟠 URGENT (chờ phản hồi)                                ║
║  ├─ RFI-DES-20260830-002: Tải trọng sàn tầng 5 (1 ngày) ║
║  └─ CO-20260828-001: Thay đổi khối lượng móng (3 ngày)   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-08-30 | Mở rộng: NCR, Submittal, Change Order, Tech Query, Party Matrix |
| 1.0.0 | 2026-08-30 | Initial RFI-only release |
