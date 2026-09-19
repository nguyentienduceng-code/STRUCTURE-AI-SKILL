# Party Matrix — Ma trận Trách nhiệm các Bên liên quan

> **Version:** 1.0 — 2026-08-30
> **Purpose:** Xác định rõ vai trò, trách nhiệm và luồng giao dịch giữa các bên

---

## 1. Các Bên liên quan trong Dự án Xây dựng

| Bên | Vai trò | Ký hiệu | Mô tả |
|------|---------|----------|--------|
| **Owner** | Chủ đầu tư | OWN | Chủ sở hữu dự án, quyết định cuối cùng |
| **Designer** | Đơn vị Thiết kế | DES | Lập hồ sơ thiết kế, trả lời RFI |
| **CSHT** | Tư vấn Giám sát | CSHT | Giám sát thi công, duyệt Submittal |
| **Contractor** | Nhà thầu | CNT | Thi công, gửi Shop Drawing |
| **QC/QA** | Ban Quản lý CL | QC | Kiểm tra chất lượng |
| **Subcontractor** | Nhà thầu phụ | SUB | Thi công phần việc chuyên môn |

---

## 2. Ma trận Gửi/Nhận

| Bên gửi ↓ / Nhận → | Owner | Designer | CSHT | Contractor | QC |
|---------------------|-------|----------|------|------------|-----|
| **Owner** | — | Design approval | Directive | Notice to Proceed | — |
| **Designer** | Design submission | — | Clarification | RFI response | — |
| **CSHT** | Observation report | RFI, TQ | — | NCR, Directive | Inspection req |
| **Contractor** | CO, Payment app | Shop Drawing, Submittal | RFI, Progress | — | Test request |
| **QC** | Quality report | — | Test results | NCR | — |

---

## 3. Ma trận Trách nhiệm theo Loại Tài liệu

### 3.1 RFI (Request for Information)

| Ai gửi? | Gửi đến? | Trách nhiệm của người nhận |
|----------|------------|---------------------------|
| Designer | Designer | Trả lời RFI trong 7 ngày |
| CSHT | Designer | Cung cấp clarification |
| Contractor | Designer/CSHT | Yêu cầu làm rõ thiết kế |
| QC | Contractor | Yêu cầu làm rõ vấn đề chất lượng |

### 3.2 NCR (Non-Conformance Report)

| Ai gửi? | Gửi đến? | Trách nhiệm của người nhận |
|----------|------------|---------------------------|
| CSHT | Contractor | Khắc phục theo đề xuất |
| QC | Contractor | Thực hiện test bổ sung |
| CSHT | Owner | Báo cáo NCR nghiêm trọng |

### 3.3 Submittal (Shop Drawing / Material)

| Ai gửi? | Gửi đến? | Trách nhiệm của người nhận |
|----------|------------|---------------------------|
| Contractor | CSHT/Designer | Duyệt trong 14 ngày |
| Designer | Contractor | Review và ghi chú |
| CSHT | Designer | Forward nếu cần design review |

### 3.4 Change Order (CO)

| Ai gửi? | Gửi đến? | Trách nhiệm của người nhận |
|----------|------------|---------------------------|
| Contractor | CSHT/Owner | Đánh giá ảnh hưởng |
| Designer | Owner | Support justification |
| Owner | Contractor | Phê duyệt/từ chối |

---

## 4. Luồng Giao dịch Chi tiết

### 4.1 RFI Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              RFI FLOW                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Phát hiện vấn đề                                                   │
│     └─► Xác định cần làm rõ gì                                         │
│                                                                          │
│  2. Tạo RFI                                                            │
│     └─► Xác định bên gửi và bên nhận                                   │
│     └─► Gán priority                                                      │
│     └─► Đăng ký vào registry                                             │
│                                                                          │
│  3. Theo dõi                                                            │
│     └─► Nhắc nhở trước deadline 2 ngày                                │
│     └─► Leo thang nếu quá hạn                                           │
│                                                                          │
│  4. Nhận phản hồi                                                       │
│     └─► Kiểm tra đã đủ thông tin chưa                                  │
│     └─► Nếu chưa → Tạo RFI tiếp theo hoặc leo thang                   │
│                                                                          │
│  5. Đóng RFI                                                            │
│     └─► Cập nhật registry                                               │
│     └─► Tích hợp vào phân tích                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 NCR Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NCR FLOW                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Phát hiện không phù hợp                                            │
│     └─► Xác định mức độ nghiêm trọng                                   │
│                                                                          │
│  2. Tạo NCR                                                            │
│     └─► Minor → Contractor tự sửa                                      │
│     └─► Major → Đề xuất + chờ duyệt                                   │
│     └─► Critical → Dừng ngay + báo Owner                                │
│                                                                          │
│  3. Contractor phản hồi                                                │
│     └─► Đề xuất khắc phục                                              │
│     └─► Hoặc giải thích                                                 │
│                                                                          │
│  4. CSHT/QC duyệt                                                      │
│     └─► Đồng ý → Cho phép tiếp tục                                     │
│     └─► Không đồng ý → Yêu cầu sửa lại                               │
│                                                                          │
│  5. Thực hiện khắc phục                                                │
│     └─► Kiểm tra lại                                                    │
│     └─► Đóng NCR                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Thời hạn Phản hồi Chuẩn

| Loại | Gửi → Nhận | Thời hạn | Ghi chú |
|------|-------------|-----------|---------|
| RFI | Contractor → Designer | 7 ngày | Có thể gia hạn |
| RFI | CSHT → Designer | 5 ngày | CSHT có thể clarify trước |
| NCR | CSHT → Contractor | 24h (Critical) | Ngay lập tức cho Critical |
| Submittal | Contractor → CSHT | 14 ngày | Designer review thêm 7 ngày |
| CO | Contractor → Owner | 3 ngày | Cần phê duyệt sớm |
| TQ | CSHT → Designer | 5 ngày | Cần phân tích |

---

## 6. Cấp Leo thang theo Loại

### RFI Escalation Chain

```
Level 1: Designer PM
    ↓ Không phản hồi trong 7 ngày
Level 2: CSHT PM
    ↓ Không phản hồi trong 3 ngày
Level 3: Owner PM
    ↓ Không phản hồi trong 3 ngày
Final: Owner escalate to Designer management
```

### NCR Escalation Chain

```
Level 1: Contractor PM
    ↓ Không khắc phục trong thời hạn
Level 2: CSHT PM → Report to Owner
Level 3: Owner → Potential stop work
```

---

## 7. Contact Template

```json
{
  "parties": {
    "Owner": {
      "name": "",
      "company": "",
      "contact_person": "",
      "email": "",
      "phone": "",
      "role": "Chủ đầu tư (Owner)"
    },
    "Designer": {
      "name": "",
      "company": "",
      "contact_person": "",
      "email": "",
      "phone": "",
      "role": "Đơn vị Thiết kế (Designer)"
    },
    "CSHT": {
      "name": "",
      "company": "",
      "contact_person": "",
      "email": "",
      "phone": "",
      "role": "Tư vấn Giám sát (CSHT)"
    },
    "Contractor": {
      "name": "",
      "company": "",
      "contact_person": "",
      "email": "",
      "phone": "",
      "role": "Nhà thầu Thi công (Contractor)"
    }
  }
}
```

---

*Cập nhật: 2026-08-30*
