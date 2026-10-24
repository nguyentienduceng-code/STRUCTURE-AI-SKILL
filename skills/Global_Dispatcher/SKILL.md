---
name: Global_Dispatcher
version: 1.0.0
last_updated: 2026-10-12
description: "Bộ điều phối trung tâm — Tự động phân loại yêu cầu người dùng và định tuyến đến đúng Skill phù hợp nhất. Giảm cognitive load cho User: chỉ cần nói yêu cầu bằng ngôn ngữ tự nhiên."
triggers:
  - "Mọi yêu cầu mới từ User khi chưa rõ Skill nào"
  - "User không chỉ định Skill cụ thể"
  - "Yêu cầu phức tạp cần nhiều Skill"
---

# 🎯 GLOBAL DISPATCHER — Bộ Điều phối Trung tâm

> **Vai trò:** Entry point DUY NHẤT cho mọi yêu cầu kỹ thuật. Phân loại, định tuyến, và quản lý pipeline.  
> **Nguyên tắc:** User chỉ cần nói yêu cầu bằng ngôn ngữ tự nhiên → Dispatcher tự xử lý phần còn lại.  
> **Version:** 1.0.0 — 2026-10-12

---

## 0. KHI NÀO KÍCH HOẠT GLOBAL DISPATCHER

| Tình huống | Hành động |
|-----------|-----------|
| User gửi yêu cầu mới, KHÔNG chỉ định skill | ✅ KÍCH HOẠT — Phân loại và định tuyến |
| User gửi yêu cầu mới, CÓ chỉ định skill (`@SkillName`) | ❌ BỎQUA — Chuyển thẳng đến skill được chỉ định |
| Đang ở giữa pipeline (skill đang chạy) | ❌ BỎQUA — Tiếp tục pipeline hiện tại |
| User nói "chuyển skill" hoặc "dùng skill khác" | ✅ KÍCH HOẠT — Re-classify |

---

## 1. QUY TRÌNH PHÂN LOẠI (Classification Flow)

### 1.1 Bước 1: Chạy Intent Classifier

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/scripts/intent_classifier.py" \
    --prompt "<PROMPT CỦA USER>" \
    --top 3 \
    --verbose
```

**Đọc output JSON** và xác định:
- `primary_skill` — Skill được chọn
- `confidence` — Mức tin cậy (0.0 → 1.0)
- `confidence_level` — HIGH / MEDIUM / LOW
- `is_pipeline` — Có cần chạy nhiều skill không
- `pipeline` — Nếu là pipeline, thứ tự chạy

### 1.2 Bước 2: Quyết định Hành động

```
┌─────────────────────────────────────────────────────┐
│               CLASSIFICATION RESULT                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│   confidence ≥ 0.85 (HIGH)                          │
│     └─► TIẾN HÀNH — Đọc SKILL.md của primary_skill │
│         và thực thi ngay lập tức.                   │
│         Thông báo: "Tôi sẽ dùng [Skill] vì [lý do]"│
│                                                      │
│   0.60 ≤ confidence < 0.85 (MEDIUM)                │
│     └─► XÁC NHẬN — Hỏi User:                       │
│         "Tôi hiểu yêu cầu này thuộc về [Skill].    │
│          Anh/chị xác nhận để tôi tiến hành?"        │
│         Nếu User đồng ý → TIẾN HÀNH                │
│         Nếu User chỉnh sửa → RE-CLASSIFY            │
│                                                      │
│   confidence < 0.60 (LOW)                           │
│     └─► HỎI LẠI — Trình bày top 3 lựa chọn:       │
│         "Yêu cầu này có thể thuộc về:               │
│          1. [Skill A] — [mô tả]                     │
│          2. [Skill B] — [mô tả]                     │
│          3. [Skill C] — [mô tả]                     │
│          Anh/chị muốn tôi xử lý theo hướng nào?"   │
│                                                      │
│   is_pipeline == true                                │
│     └─► THÔNG BÁO PIPELINE:                         │
│         "Yêu cầu này cần chạy nhiều bước:          │
│          Step 1: [Skill A] — [mô tả]               │
│          Step 2: [Skill B] — [mô tả]               │
│          Tôi sẽ bắt đầu từ Step 1."                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 1.3 Bước 3: Thực thi

Sau khi xác định skill → **ĐỌC SKILL.md** của skill đó và làm theo hướng dẫn.

**QUAN TRỌNG:** Global Dispatcher KHÔNG thực thi logic kỹ thuật. Nó CHỈ phân loại và định tuyến. Sau khi routing xong → chuyển hoàn toàn quyền kiểm soát cho skill đích.

---

## 2. BẢNG PHÂN LOẠI NHANH (Quick Reference)

> Bảng này là phiên bản tối giản của Intent Classifier. Dùng khi KHÔNG thể chạy script Python.

### 2.1 Phân loại theo Vai trò

| Vai trò User | Skill | Dấu hiệu nhận biết |
|-----------|-------|---------------------|
| **Chủ đầu tư / QLTK** — Cần ai đó review, thẩm tra, lập tờ trình | `Design_Evaluation` | "review", "thẩm tra", "tờ trình", "bóc khối lượng" |
| **Đơn vị thiết kế** — Cần tự tính toán, xuất thuyết minh | `Structural_Design_Engineer` | "tính dầm", "tính bu lông", "calculation sheet" |
| **Cần phụ lục đầy đủ** — Phục vụ thẩm tra/chấp thuận | `SKILL_PHULUC` | "phụ lục tính toán", "step-by-step" |
| **Cần hình ảnh** — Chỉ vẽ, không tính | `Technical_Illustrator` | "vẽ mặt cắt", "render 3D" |
| **Cần so sánh chi phí** — VE, carbon, ngân sách | `Cost_Estimator` | "so sánh chi phí", "value engineering" |
| **Có sự cố** — Nứt, sập, hư hỏng | `SKILL_FORENSIC` | "sự cố", "nứt nghiêm trọng", "điều tra" |
| **Cần kiểm chứng** — Cross-check, so sánh ETABS | `SKILL_VERIFY` | "cross-check", "verify", "so sánh kết quả" |
| **Giao dịch kỹ thuật** — RFI, NCR, Submittal | `SKILL_RFI` | "tạo RFI", "submittal", "change order" |
| **Địa kỹ thuật** — Đất, Plaxis, SPT/CPT | `SKILL_GEOTECH` | "SPT", "Plaxis", "hố đào sâu", "ĐCCT" |

### 2.2 Phân loại theo Keyword Ưu tiên Tuyệt đối

Khi gặp các keyword sau → **KHÔNG CẦN** chạy classifier, skill đã xác định:

| Keyword | Skill | Lý do |
|---------|-------|-------|
| "thuyết minh tính toán" | `Structural_Design_Engineer` | TB-01 trong AGENTS.md |
| "calculation sheet" | `Structural_Design_Engineer` | TB-01 |
| "tính liên kết / bu lông / đường hàn / bản mã" | `Structural_Design_Engineer` | TB-01 |
| "review" / "thẩm tra" | `Design_Evaluation` | TB-02 |
| "tờ trình" / "trình duyệt" | `Design_Evaluation` | TB-02 |
| "bóc tách khối lượng" | `Design_Evaluation` | TB-02 |
| "SPT" / "CPT" / "Plaxis" / "ĐCCT" | `SKILL_GEOTECH` | TB-04 |
| "sự cố" / "sập" / "nứt nghiêm trọng" | `SKILL_FORENSIC` | Unique domain |

### 2.3 Phát hiện Multi-Intent (Pipeline)

| Pattern trong prompt | Pipeline |
|---------------------|----------|
| "tính ... rồi lập tờ trình" | `SDE → DE` |
| "tính ... rồi review" | `SDE → DE` |
| "phân tích đất ... rồi thiết kế móng" | `GEO → SDE` |
| "thiết kế xong tính chi phí" | `SDE → CE` |
| "review toàn diện" / "thẩm tra đầy đủ" | `DE → VERIFY → CE` |
| "tính ... rồi vẽ mặt cắt" | `SDE → TI` |

---

## 3. XÂY DỰNG PIPELINE (Khi cần 2+ Skills)

### 3.1 Chạy Pipeline Builder

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/scripts/pipeline_builder.py" \
    --skills "Structural_Design_Engineer,Design_Evaluation" \
    --context "Tính dầm B1 rồi lập tờ trình"
```

### 3.2 Pipeline Execution Protocol

```
Stage 1: [Skill A]
    │
    ├── Đọc SKILL.md → Thực thi → Thu thập output
    │
    ├── ⚠️ REVIEW GATE (nếu có)
    │   └── Trình bày kết quả → Chờ User duyệt
    │
    ├── Tạo Handoff JSON theo SKILL_BRIDGE.md
    │
    ▼
Stage 2: [Skill B]
    │
    ├── Đọc Handoff JSON → Validate schema
    ├── Đọc SKILL.md → Thực thi với context từ Stage 1
    │
    └── Output cuối cùng
```

### 3.3 Quy tắc Pipeline

1. **Mỗi stage = 1 skill.** Không chạy 2 skill cùng lúc.
2. **Review Gate bắt buộc** sau SDE, DE, FORENSIC (theo AGENTS.md Rule 3).
3. **Handoff JSON** phải tuân thủ schema trong `SKILL_BRIDGE.md`.
4. **Nếu stage fail** → DỪNG pipeline, báo User, KHÔNG tự skip.
5. **User có quyền** skip stage, thay đổi thứ tự, hoặc hủy pipeline.

---

## 4. GIAO TIẾP VỚI USER

### 4.1 Thông báo Routing (Luôn làm)

Sau khi phân loại, LUÔN thông báo cho User trước khi thực thi:

**Template 1 — Single Skill (HIGH confidence):**
```
🎯 Tôi nhận diện yêu cầu này thuộc về **[Skill Name]** ([lý do ngắn]).
Bắt đầu xử lý...
```

**Template 2 — Single Skill (MEDIUM confidence):**
```
🎯 Tôi nhận diện yêu cầu này có thể thuộc về **[Skill Name]** ([lý do]).
Anh/chị xác nhận để tôi tiến hành?
```

**Template 3 — Pipeline:**
```
🎯 Yêu cầu này cần xử lý qua **[N] bước**:
  ① **[Skill A]** — [mô tả ngắn]
  ② **[Skill B]** — [mô tả ngắn]
Tôi sẽ bắt đầu từ bước 1. Sau mỗi bước sẽ trình bày kết quả để anh/chị duyệt.
```

**Template 4 — Ambiguous (LOW confidence):**
```
❓ Yêu cầu này có thể xử lý theo nhiều hướng:
  1️⃣ **[Skill A]** — [mô tả] (phù hợp [X]%)
  2️⃣ **[Skill B]** — [mô tả] (phù hợp [Y]%)
  3️⃣ **[Skill C]** — [mô tả] (phù hợp [Z]%)
Anh/chị muốn tôi xử lý theo hướng nào?
```

### 4.2 Override bằng @mention

User có thể ghi đè routing bằng cách chỉ định trực tiếp:
- `@Design_Evaluation review dầm B1` → Bỏ qua classifier, chạy thẳng DE
- `@SDE tính cốt thép` → Bỏ qua classifier, chạy thẳng SDE
- `@SKILL_GEOTECH phân tích SPT` → Bỏ qua classifier, chạy thẳng GEOTECH

**Shorthand aliases:**

| Alias | Skill |
|-------|-------|
| `@DE` hoặc `@QLTK` | Design_Evaluation |
| `@SDE` hoặc `@TK` | Structural_Design_Engineer |
| `@TI` hoặc `@VẼ` | Technical_Illustrator |
| `@CE` hoặc `@CHIPHI` | Cost_Estimator |
| `@FOR` hoặc `@SUCO` | SKILL_FORENSIC |
| `@VER` hoặc `@CHECK` | SKILL_VERIFY |
| `@RFI` | SKILL_RFI |
| `@GEO` hoặc `@DAT` | SKILL_GEOTECH |
| `@PL` hoặc `@PHULUC` | SKILL_PHULUC |

---

## 5. TÍCH HỢP VỚI HỆ SINH THÁI

### 5.1 Liên kết với AGENTS.md

Global Dispatcher **thay thế** logic dispatcher thủ công trong AGENTS.md §0. 
Tuy nhiên, AGENTS.md §0 vẫn được giữ làm **fallback** khi không thể chạy script Python.

### 5.2 Liên kết với INTER_SKILL_TRIGGERS.md

Khi pipeline đang chạy, Global Dispatcher **KHÔNG can thiệp** vào trigger tự động giữa các skill.
Ví dụ: Nếu SDE xong → POST-SDE-001 tự động gọi DE → Dispatcher KHÔNG cần routing lại.

### 5.3 Liên kết với SKILL_BRIDGE.md

Mọi handoff JSON được tạo bởi pipeline_builder.py tuân thủ schema trong SKILL_BRIDGE.md.

---

## 6. LAZY LOAD PROTOCOL (Tiết kiệm Token)

**QUAN TRỌNG:** Global Dispatcher tuân thủ AGENTS.md Rule 16.

1. **Chỉ đọc file cần thiết:**
   - Bước 1: Chạy `intent_classifier.py` (script nhẹ, không cần đọc SKILL.md nào)
   - Bước 2: Sau khi xác định skill → CHỈ đọc SKILL.md của skill đó
   - Bước 3: Đọc sub-modules theo yêu cầu cụ thể

2. **KHÔNG ĐỌC:**
   - Không đọc toàn bộ 12 SKILL.md cùng lúc
   - Không đọc SKILL_INDEX.md khi đã có classifier
   - Không đọc MODE_2D nếu skill chính là SDE (không phải TI)

---

## 7. ERROR HANDLING

| Tình huống | Hành động |
|-----------|-----------|
| Script `intent_classifier.py` lỗi | Fallback: Dùng Bảng §2 (Quick Reference) |
| Skill chọn là PLACEHOLDER | Thông báo: "Skill [X] đang phát triển. Bạn có muốn dùng [Y] thay thế?" |
| Pipeline bị gián đoạn giữa chừng | Lưu state, hỏi User muốn tiếp tục hay reset |
| User không đồng ý với routing | Re-classify hoặc cho User chọn manual |

---

## 8. FILES TRONG SKILL NÀY

```
Global_Dispatcher/
├── SKILL.md                          ← (file này)
└── scripts/
    ├── intent_classifier.py          ← Core classifier (200+ keywords)
    ├── keyword_database.json         ← Keyword → Skill mapping database
    └── pipeline_builder.py           ← Multi-skill pipeline builder
```

---

## 9. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-12 | Initial release — Intent Classifier, Pipeline Builder, 200+ keywords |
