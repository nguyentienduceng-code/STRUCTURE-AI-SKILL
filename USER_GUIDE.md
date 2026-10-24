# 🎯 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG SKILLS KỸ SƯ KẾT CẤU

> **Phiên bản:** 1.0 — Cập nhật: 2026-10-13
> **Dành cho:** Kỹ sư kết cấu, Quản lý dự án, Chủ đầu tư, Nhà thầu

---

## MỤC LỤC
1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc & Luồng Hoạt Động](#2-kiến-trúc--luồng-hoạt-động)
3. [Danh Sách Skills](#3-danh-sách-skills)
4. [Hướng Dẫn Sử Dụng Nhanh](#4-hướng-dẫn-sử-dụng-nhanh)
5. [Quy Tắc Bắt Buộc](#5-quy-tắc-bắt-buộc)
6. [Workflows Phổ Biến](#6-workflows-phổ-biến)
7. [Xử Lý Sự Cố](#7-xử-lý-sự-cố)

---

## 1. TỔNG QUAN HỆ THỐNG

### 1.1 Hệ Thống Là Gì?

Đây là **hệ sinh thái AI kỹ sư kết cấu** gồm 14 kỹ năng chuyên trách, hoạt động như một đội ngũ kỹ sư ảo:

- **Thiết kế** kết cấu bê tông, thép, móng
- **Review & Thẩm tra** hồ sơ theo tiêu chuẩn TCVN/QCVN/Eurocode/ACI
- **Vẽ kỹ thuật** mặt cắt, chi tiết liên kết
- **Quản lý giao dịch** RFI, NCR, Submittal
- **Dự toán chi phí** và tối ưu Value Engineering
- **Phân tích địa kỹ thuật** hố đào sâu, móng cọc

### 1.2 Mô Hình Hoạt Động

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Kỹ sư)                             │
│                    Yêu cầu bằng ngôn ngữ tự nhiên              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   🎯 GLOBAL DISPATCHER                           │
│              (Bộ điều phối trung tâm - Entry Point)            │
│    • Phân tích yêu cầu                                          │
│    • Xác định skill phù hợp                                     │
│    • Xây dựng pipeline nếu cần nhiều bước                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  Structural    │ │  Design       │ │  SKILL_GEOTECH│
    │  Design       │ │  Evaluation   │ │  (Địa kỹ     │
    │  Engineer     │ │  (Review)     │ │   thuật)      │
    │               │ │               │ │               │
    │ Tính toán    │ │ Thẩm tra      │ │ Phân tích     │
    │ thiết kế      │ │ hồ sơ        │ │ móng, hố đào  │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │ Handoff JSON
                              ▼
    ┌───────────────────────────────────────────────────────────┐
    │                  📋 REVIEW GATE                           │
    │         (User xem kết quả → XÁC NHẬN trước khi xuất file)│
    └─────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │ Technical     │
                          │ Illustrator   │
                          │ (Vẽ hình)    │
                          └───────────────┘
```

---

## 2. KIẾN TRÚC & LUỒNG HOẠT ĐỘNG

### 2.1 Cấu Trúc Thư Mục

```
.agents/
├── AGENTS.md                    ← Quy tắc VÀNG (Đọc trước!)
├── _SHARED/                     ← Dữ liệu dùng chung giữa các skill
│   ├── SHARED_CONTEXT/          ← Handoff JSON giữa các skill
│   ├── memory/                  ← Lưu context dự án
│   └── workflows/               ← Template workflow
├── skills/                      ← 14 kỹ năng chuyên trách
│   ├── Global_Dispatcher/       ← Entry point - phân loại yêu cầu
│   ├── Design_Evaluation/       ← Review, thẩm tra, tờ trình
│   ├── Structural_Design_Engineer/ ← Tính toán kết cấu
│   ├── SKILL_GEOTECH/           ← Địa kỹ thuật
│   ├── Technical_Illustrator/    ← Vẽ kỹ thuật
│   └── [8 skills khác...]
├── _archive/                    ← Lưu trữ file cũ
└── docs/                        ← Tài liệu hệ thống
```

### 2.2 Luồng Xử Lý Yêu Cầu

```
1. USER gửi yêu cầu
       │
2. GLOBAL DISPATCHER phân tích
       │
       ├── Confidence ≥ 85% → Chạy skill ngay
       │
       ├── Confidence 60-85% → Hỏi User xác nhận
       │
       └── Confidence < 60% → Gợi ý 3 lựa chọn
       
3. SKILL thực hiện tính toán
       │
4. 📋 REVIEW GATE: Hiển thị kết quả
       │
5. USER xác nhận (Đồng ý / Chỉnh sửa)
       │
6. Technical_Illustrator vẽ hình (nếu cần)
       │
7. Xuất file (.docx, .md, .xlsx)
```

---

## 3. DANH SÁCH SKILLS

### 3.1 Core Skills (Kỹ năng cốt lõi)

| Skill | Vai trò | Khi nào dùng |
|-------|---------|--------------|
| **Global_Dispatcher** | Bộ điều phối | **LUÔN BẮT ĐẦU TỪ ĐÂY** — Phân tích và định tuyến yêu cầu |
| **Design_Evaluation** | Quản lý thiết kế / Đại diện Chủ đầu tư | Review bản vẽ, thẩm tra hồ sơ, lập tờ trình, xử lý NCR, bóc khối lượng |
| **Structural_Design_Engineer** | Đơn vị thiết kế | Tính cốt thép dầm/cột, kiểm tra tiết diện, tính bu lông/đường hàn, xuất thuyết minh |
| **Technical_Illustrator** | Kỹ thuật vẽ | Vẽ mặt cắt, chi tiết liên kết, biểu đồ nội lực (2D/3D) |

### 3.2 Specialist Skills (Kỹ năng chuyên sâu)

| Skill | Vai trò | Khi nào dùng |
|-------|---------|--------------|
| **SKILL_GEOTECH** | Địa kỹ thuật | Phân tích SPT/CPT, tính lún, thiết kế móng cọc, hố đào sâu |
| **SKILL_TEMPWORKS** | Cốp pha & Ván khuôn | Thiết kế cốp pha sàn/cột, kiểm tra ổn định thi công |
| **SKILL_VERIFY** | Kiểm chứng | Cross-check kết quả với ETABS, phát hiện mâu thuẫn tiêu chuẩn |
| **Cost_Estimator** | Dự toán | Ước lượng chi phí, Value Engineering, tính Carbon |

### 3.3 Support Skills (Kỹ năng hỗ trợ)

| Skill | Vai trò | Khi nào dùng |
|-------|---------|--------------|
| **SKILL_FORENSIC** | Giám định sự cố | Điều tra nguyên nhân nứt, hư hỏng, back-calculation |
| **SKILL_PHULUC** | Phụ lục tính toán | Tạo phụ lục step-by-step cho tư vấn thiết kế |
| **SKILL_RFI** | Quản lý giao dịch | Quản lý RFI, NCR, Submittal, Change Order |
| **Project_Manager** | Quản lý dự án | Theo dõi tiến độ, resource allocation |
| **SKILL_BIM_COORDINATION** | BIM Coordination | Clash detection, model review |

---

## 4. HƯỚNG DẪN SỬ DỤNG NHANH

### 4.1 Cách 1: Qua Global Dispatcher (Khuyến nghị)

Chỉ cần mô tả yêu cầu bằng ngôn ngữ tự nhiên:

```
USER: "Tôi có bản vẽ thiết kế dầm sàn tầng 3, 
       hãy review và lập tờ trình trình duyệt"

AI sẽ tự:
1. Phân loại → Design_Evaluation
2. Tạo pipeline: Review → Xuất tờ trình
3. Thực hiện và chờ bạn xác nhận
```

### 4.2 Cách 2: Gọi Skill Trực Tiếp

Gọi skill cụ thể khi đã biết mình cần gì:

```
USER: @Design_Evaluation Review bản vẽ kết cấu tầng 3

USER: @Structural_Design_Engineer Tính cốt thép dầm D1

USER: @SKILL_GEOTECH Kiểm tra khả năng chịu tải của móng cọc
```

### 4.3 Bảng Tra Cứu Nhanh

| Bạn cần... | Skill | Ví dụ prompt |
|------------|-------|--------------|
| Review hồ sơ, lập tờ trình | `Design_Evaluation` | "Review thiết kế dầm sàn theo TCVN 5574:2018" |
| Tính cốt thép, xuất thuyết minh | `Structural_Design_Engineer` | "Tính cốt thép dầm 300x600, M=180kNm" |
| Vẽ mặt cắt, chi tiết | `Technical_Illustrator` | "Vẽ mặt cắt dầm D1" |
| Phân tích móng, SPT/CPT | `SKILL_GEOTECH` | "Tính sức chịu tải cọc D400" |
| Thiết kế cốp pha | `SKILL_TEMPWORKS` | "Thiết kế cốp pha sàn dày 120mm" |
| Dự toán chi phí | `Cost_Estimator` | "Ước lượng chi phí khung thép 5 tầng" |
| Kiểm chứng kết quả | `SKILL_VERIFY` | "Cross-check với ETABS" |
| Điều tra sự cố | `SKILL_FORENSIC` | "Điều tra nguyên nhân nứt tường" |

---

## 5. QUY TẮC BẮT BUỘC

### 5.1 5 Quy Tắc Vàng

| # | Quy tắc | Giải thích |
|---|---------|------------|
| **1** | **Cấm nhẩm tay** | Mọi tính toán phải qua script Python → đọc kết quả JSON |
| **2** | **Citation đủ 4 phần** | `[Mã]:[Năm] — Điều/Bảng [số] — Trang [số] — [Trích yếu]` |
| **3** | **η ≤ 1.0 = Đạt** | η = Tác động / Khả năng. 🟢 ≤0.70, 🟡 0.70-0.90, 🟠 0.90-1.00, 🔴 >1.00 |
| **4** | **Review Gate** | AI hiển thị kết quả → **BẠN xác nhận** → mới xuất file |
| **5** | **Đường dẫn tuyệt đối** | Luôn dùng `g:\My Drive\...`, không dùng `./` hoặc `../` |

### 5.2 Quy Tắc Xác Nhận (Review Gate)

**BẮT BUỘC** trước khi xuất file:
1. AI in tóm tắt kết quả (bảng η, số liệu chốt)
2. AI hỏi: *"Anh/chị có đồng ý để xuất file không?"*
3. **CHỈ** ghi file sau khi bạn nói: Đồng ý / OK / Duyệt / Approved

**KHÔNG phải xác nhận:** Im lặng, "để tôi xem lại", "ok nhưng..."

### 5.3 Tiêu Chuẩn Áp Dụng

Các tiêu chuẩn được khóa cứng trong `STANDARDS_LOCK.md`:

| Lĩnh vực | Tiêu chuẩn |
|----------|-------------|
| Tải trọng | TCVN 2737:2023 |
| Bê tông cốt thép | TCVN 5574:2018 |
| Kết cấu thép | TCVN 5575:2024 |
| Móng cọc | TCVN 10304:2025 |
| Chịu động đất | TCVN 9386:2025 |

---

## 6. WORKFLOWS PHỔ BIẾN

### 6.1 Workflow 1: Review → Tờ Trình (Phổ biến nhất)

```
User: "Review bản vẽ KC và lập tờ trình trình duyệt"

AI Flow:
1. Design_Evaluation → Review hồ sơ
2. Hiển thị bảng phát hiện
3. Review Gate: Bạn xác nhận
4. SKILL_REPORT → Xuất tờ trình .docx
5. Technical_Illustrator → Vẽ hình minh họa
6. Review Gate: Bạn duyệt lần cuối
7. Xuất file final
```

### 6.2 Workflow 2: Thiết Kế → Review

```
User: "Tính cốt thép dầm D1 rồi review"

AI Flow:
1. Structural_Design_Engineer → Tính toán
2. Review Gate: Bạn xác nhận kết quả
3. Design_Evaluation → Review thiết kế
4. Review Gate: Bạn xác nhận
5. Technical_Illustrator → Vẽ mặt cắt dầm
```

### 6.3 Workflow 3: Địa Kỹ Thuật → Móng → Kết Cấu

```
User: "Phân tích địa chất và thiết kế móng cọc"

AI Flow:
1. SKILL_GEOTECH → Phân tích SPT/CPT, tính SCT cọc
2. Review Gate: Bạn xác nhận
3. Structural_Design_Engineer → Thiết kế đài móng
4. Review Gate: Bạn xác nhận
5. SKILL_REPORT → Xuất thuyết minh móng
```

### 6.4 Workflow 4: Value Engineering

```
User: "Tối ưu chi phí cho khung thép 5 tầng"

AI Flow:
1. Structural_Design_Engineer → Thiết kế ban đầu
2. Review Gate
3. Cost_Estimator → Phân tích chi phí + VE
4. Review Gate
5. Xuất báo cáo so sánh phương án
```

---

## 7. XỬ LÝ SỰ CỐ

### 7.1 Không Biết Dùng Skill Nào

→ Gửi yêu cầu cho **Global_Dispatcher** — nó sẽ phân tích và định tuyến

### 7.2 Script Tính Toán Lỗi

1. Kiểm tra file có trong `_deprecated/` không (đã ngừng hỗ trợ)
2. Kiểm tra đường dẫn tuyệt đối trong script
3. Kiểm tra encoding UTF-8

### 7.3 Kết Quả Không Như Mong Đợi

1. **Review Gate** cho phép bạn xem và yêu cầu chỉnh sửa TRƯỚC khi xuất file
2. Nếu phát hiện mâu thuẫn → gọi **SKILL_VERIFY** để kiểm chứng

### 7.4 Cần Tra Cứu Tiêu Chuẩn

→ Dùng `grep_search` với từ khóa đặc thù trước khi đọc PDF lớn
→ Xem `standards/INDEX_QUICK.md` trước

---

## 📞 LIÊN HỆ & HỖ TRỢ

| Cần hỗ trợ | Xem |
|------------|-----|
| Quy tắc toàn hệ thống | `AGENTS.md` |
| Tra cứu nhanh skill | `skills/SKILL_INDEX.md` |
| Khóa phiên bản tiêu chuẩn | `skills/STANDARDS_LOCK.md` |
| Giao thức trao đổi dữ liệu | `skills/SKILL_BRIDGE.md` |
| Thay đổi gần đây | `skills/CHANGELOG.md` |

---

## 📝 CAM KẾT

> *Hệ thống này là công cụ hỗ trợ. Mọi kết quả tính toán phải được **kỹ sư có chứng chỉ hành nghề** kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*

---

**Cập nhật lần cuối:** 2026-10-13
**Phiên bản hệ thống:** v6.1
