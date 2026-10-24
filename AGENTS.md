# AGENTS.md — Quy tắc Liên Skill Toàn bộ Bộ Kỹ năng Kết cấu

> **Phạm vi:** Áp dụng cho **MỌI skill** trong `.agents/skills/`.
> **Vị trí chuẩn:** `.agents/AGENTS.md` (đồng bộ tại `.agents/skills/AGENTS.md`).
> **Tham khảo nhanh:** Xem `skills/SKILL_INDEX.md` để biết mapping tình huống → skill → script.
> **P0 Infrastructure:** Xem `skills/SKILL_BRIDGE.md` (data contracts) và `skills/INTER_SKILL_TRIGGERS.md` (auto-invocation).
> **P1 Tools:** Xem `confidence_score.py`, `validate_handoff_schema.py`, `handoff_manager.py` trong `_SHARED/SHARED_CONTEXT/`.
> **Cập nhật:** 2026-10-12 — v6.1 (Phase 1 Infrastructure + SKILL_TEMPWORKS)

---

## 0. Bảng Điều phối Liên-Skill (Dispatcher — ĐỌC TRƯỚC TIÊN)

### 0.1 Điều phối Tự động qua Global Dispatcher (Khuyến nghị)
Khi nhận yêu cầu từ User bằng ngôn ngữ tự nhiên và chưa rõ dùng skill nào, chạy công cụ điều phối trung tâm:
```bash
python "g:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/scripts/intent_classifier.py" \
    --prompt "<YÊU CẦU CỦA USER>" --top 3
```
- Nếu `confidence >= 0.85` (HIGH): Nạp `SKILL.md` của `primary_skill` và thực thi ngay.
- Nếu `is_pipeline == true`: Sử dụng `pipeline_builder.py` để chuỗi hóa các skills theo đúng thứ tự handoff.
- Nếu `confidence < 0.60` (LOW): Trình bày top 3 lựa chọn và hỏi User xác nhận.

### 0.2 Bảng Tra cứu Nhanh (Manual Dispatcher Table)
Khi không cần chạy script phân loại, tra bảng này để xác định skill chính. **Không nạp 2 skill cùng lúc** trừ khi quy trình yêu cầu nối tiếp.

| Câu hỏi phân xử | Trả lời | Skill kích hoạt | Entry point |
|---|---|---|---|
| User đưa yêu cầu chung, chưa rõ skill hoặc cần chuỗi hành động? | Có | **`Global_Dispatcher`** | SKILL.md / intent_classifier.py |
| Đại diện Chủ đầu tư / QLTK — *review, thẩm tra, nghiệm thu, xử lý NCR, lập tờ trình, so sánh phương án, bóc khối lượng, đối chiếu tiêu chuẩn*? | Có | **`Design_Evaluation`** | SKILLKC.md / SKILL_REPORT.md |
| Đóng vai đơn vị thiết kế — *tự tính ra tiết diện / cốt thép / bu lông / đường hàn, xuất Thuyết minh tính toán*? | Có | **`Structural_Design_Engineer`** | SKILL_CALC.md / SKILL_CONNECTION.md / SKILL_CALC_REPORT.md |
| Tạo phụ lục tính toán chi tiết step-by-step đầy đủ cho đơn vị tư vấn thiết kế? | Có | **`SKILL_PHULUC`** | TMTT_FULL.md / PARTIAL_*.md |
| Yêu cầu **chỉ** là tạo hình ảnh / bản vẽ / biểu đồ? | Có | **`Technical_Illustrator`** | MODE 2D (default) / MODE 3D |
| So sánh chi phí, Value Engineering, tính Carbon, tối ưu ngân sách? | Có | **`Cost_Estimator`** | MODULE 1–5 |
| Điều tra sự cố / phân tích nguyên nhân hư hỏng, nứt nghiêm trọng, back-calculation? | Có | **`SKILL_FORENSIC`** | 7-step protocol |
| Kiểm chứng chéo kết quả, phát hiện mâu thuẫn tiêu chuẩn, cross-check với ETABS? | Có | **`SKILL_VERIFY`** | 5 loại kiểm chứng |
| Quản lý giao dịch kỹ thuật RFI, NCR, Submittal, Change Order với các bên? | Có | **`SKILL_RFI`** | Document Lifecycle |
| Phân tích ĐCCT, tính thông số Plaxis, tương quan SPT/CPT, ứng suất hữu hiệu, quy đổi DW/Strut? | Có | **`SKILL_GEOTECH`** | SKILL_SOIL_PARAMS.md |
| Thiết kế cốp pha sàn, cốp pha cột, cốp pha tường, cây chống, hệ giằng, kiểm tra ổn định thi công? | Có | **`SKILL_TEMPWORKS`** | Phase 1: calc_formwork_slab.py |

**Tie-breaker (phá vỡ thế hòa):**

1. Có keyword **"thuyết minh tính toán", "calculation sheet", "tính liên kết", "tính bu lông", "tính đường hàn", "tính bản mã", "chiều dài neo"** → `Structural_Design_Engineer` **thắng tuyệt đối**.
2. Có keyword **"review", "thẩm tra", "NCR", "tờ trình", "trình duyệt", "bóc tách khối lượng", "so sánh phương án", "hoàn công"** → `Design_Evaluation` **thắng tuyệt đối**.
3. Cả (1) và (2) cùng xuất hiện (VD: *"tính lại dầm rồi lập tờ trình"*) → chạy nối tiếp:
   `Structural_Design_Engineer` (tính) → **Review Gate** → `Design_Evaluation / SKILL_REPORT` (xuất tờ trình).
4. Có keyword **"thông số đất", "SPT", "CPT", "Plaxis input", "E50", "Hardening Soil", "tường vây EA EI", "ứng suất hữu hiệu", "phân tích địa chất", "ĐCCT", "hố đào sâu", "biện pháp thi công hầm"** → `SKILL_GEOTECH` **thắng tuyệt đối**.
5. Có keyword **"cốp pha", "coffa", "ván khuôn", "cây chống", "shoring", "bracing", "temporary works", "ván định hình", "tường chắn thi công"** → `SKILL_TEMPWORKS` **thắng tuyệt đối**.
6. Không khớp rõ → **HỎI User**, không tự đoán.

**`Technical_Illustrator` không bao giờ là skill chính** khi yêu cầu có nội dung tính toán — luôn được gọi bởi `Design_Evaluation` hoặc `Structural_Design_Engineer`.

---

## 1. Đường dẫn Tuyệt đối (Absolute Paths)

- **LUÔN** sử dụng đường dẫn tuyệt đối cho mọi file input/output.
- Đúng: `g:\My Drive\Google AI Studio\01_Projects\DuAnX\output.docx`
- Sai: `./output.docx`, `output.docx`, `../DuAnX/output.docx`

---

## 2. Encoding UTF-8 trên Windows

- Mọi script Python phải có ở đầu file:
  ```python
  import sys
  if sys.stdout.encoding != 'utf-8':
      sys.stdout.reconfigure(encoding='utf-8')
  ```
- Khi chạy Node.js, đảm bảo file JSON input/output là UTF-8 BOM-free.

---

## 3. Review Gate (Cổng Kiểm duyệt) & Định nghĩa Xác nhận

- **BẮT BUỘC** trước khi xuất bất kỳ file `.docx` / `.pdf` / `.json` / `.md` chính thức nào:
  1. In tóm tắt ra chat: bảng chỉ số sử dụng η, các số liệu chốt, danh sách `UNVERIFIED`.
  2. Hỏi User: *"Anh/chị có đồng ý với kết quả này để xuất file không?"*
  3. Chỉ ghi file sau khi User xác nhận rõ ràng.
- **Định nghĩa "xác nhận rõ ràng":**
  - ĐỒNG Ý: "Đồng ý", "OK", "Xuất file", "Approved", "Được", "Duyệt".
  - KHÔNG ĐƯỢC COI LÀ XÁC NHẬN: User im lặng, "để tôi xem lại", "ok nhưng...", hỏi thêm thông tin mà không chốt. Nếu không rõ → HỎI LẠI, không tự suy diễn.
- Ngoại lệ: File scratch/test/debug không cần Review Gate.

---

## 4. No Hallucination — Không Bịa Số Liệu

- Thiếu dữ kiện → ghi rõ `Data Missing: [Tên Thông Số]`.
- **KHÔNG BAO GIỜ** tự đoán giá trị kỹ thuật (cường độ bê tông, tải trọng, kích thước cốt thép, v.v.).
- Khi tra tiêu chuẩn: trích dẫn chính xác số điều khoản, số bảng, năm ban hành.

---

## 5. Deterministic Math — Cấm Nhẩm Tay

- Nghiêm cấm AI tự nhẩm phép toán kỹ thuật. Phải gọi script trong `calculators/` (Design_Evaluation) hoặc `scripts/calc_*.py` (Structural_Design_Engineer) và đọc kết quả JSON từ stdout.
- Mọi script tính toán PHẢI trả về trường `Calculation_Logs` (mảng object) và `Standard_Method` (phiên bản tiêu chuẩn thực sự cài đặt). Nếu script không có `Calculation_Logs` → kết quả **KHÔNG** được đưa vào báo cáo.

---

## 6. Chỉ số Sử dụng (Utilization Ratio η)

Mọi kiểm tra định lượng phải quy về `η = Tác động / Khả năng`:

| η | Mã màu | Kết luận | Hành động |
|---|---|---|---|
| ≤ 0.70 | 🟢 | An toàn, có dư | Đạt — xem xét Value Engineering (Cost_Estimator) |
| 0.70 – 0.90 | 🟡 | Đạt, hợp lý | Đạt — thiết kế tối ưu |
| 0.90 – 1.00 | 🟠 | Đạt nhưng sát ngưỡng | Đạt — cảnh báo lưu ý |
| > 1.00 | 🔴 | KHÔNG ĐẠT | Yêu cầu điều chỉnh tiết diện / giải pháp |

Cấm dùng tỷ số của các hệ số trung gian và gọi đó là η.

> **Code-enforced:** Toàn bộ ngưỡng η và hành động kích hoạt được thực thi tự động qua Policy Engine tại `tools/policy_engine.py` (`decide_eta`). Xem chi tiết mã nguồn và test suite tại `tests/test_policy_engine.py`.

---

## 7. Nguồn Tiêu chuẩn — Version Lock

- Mọi trích dẫn tiêu chuẩn PHẢI lấy phiên bản từ **`STANDARDS_LOCK.md`** — nguồn sự thật duy nhất.
- LUÔN ghi kèm năm ban hành ngay sau mã số (VD: `TCVN 2737:2023`, `TCVN 5575:2024`, `TCVN 5574:2018`, `TCVN 9386:2025`).
- Citation Object hiển thị đủ 4 phần: `[Mã]:[Năm] — Điều/Bảng [số] — Trang [số] — [Trích yếu]`. Cấm rút gọn.
- Nếu script khai báo `Standard_Method` khác phiên bản chốt → PHẢI in cảnh báo rõ trong báo cáo, không tự đổi nhãn.
- **Cấm dùng đồng thời 2 phiên bản của cùng 1 tiêu chuẩn trong 1 phân tích.**

---

## 8. Trách nhiệm, Approval Matrix & Disclaimer Bắt buộc

- Mọi báo cáo/thuyết minh xuất ra PHẢI có bảng Trách nhiệm cuối văn bản, cột "Đề xuất" luôn ghi rõ: *"Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký"*.
- Mọi file thuyết minh tính toán / tờ trình xuất ra phải chèn dòng cuối:
  > *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*

---

## 9. Phân biệt Bản vẽ Kỹ thuật vs Ảnh Minh họa

- `Technical_Illustrator` **MODE 2D** (Python/matplotlib) = bản vẽ kỹ thuật, dùng được cho hồ sơ pháp lý/thiết kế.
- `Technical_Illustrator` **MODE 3D** (AI render) = minh họa khái niệm. Bắt buộc kèm caption cảnh báo: *"Hình minh họa khái niệm — không phải bản vẽ kỹ thuật chính xác, không dùng để thi công."*

---

## 10. Xác nhận File Output

- Sau khi tạo file (ảnh, .docx, .json):
  - Dùng `list_dir` hoặc `view_file` để xác nhận file thực sự tồn tại trước khi báo cáo hoàn thành.
  - Nếu nhúng ảnh vào artifact → copy file vào thư mục artifacts trước.

---

## 11. Xử lý Mâu thuẫn Giữa Các Module

Trước khi đưa nội dung qua Review Gate, nếu phát hiện số liệu hiển thị trong báo cáo/tờ trình KHÁC với số liệu gốc trong JSON handoff từ module tính toán → PHẢI dừng lại, báo rõ sự khác biệt cho User, KHÔNG tự động chọn 1 trong 2 số liệu.

---

## 12. Văn phong Kỹ thuật Chuẩn hóa (Plain Engineering Language)

Mọi output chính thức (báo cáo, tờ trình, thuyết minh) PHẢI tuân thủ:
- Câu ngắn (≤ 25 từ), chủ ngữ là đối tượng kỹ thuật (dầm, cột, tải), không phải khái niệm trừu tượng.
- Ưu tiên động từ hành động: "chịu", "vượt", "đạt", "cần tăng". Hạn chế bị động.
- Mỗi kết luận PHẢI kèm ít nhất 1 con số định lượng (η, f/L, σ, kN, mm).
- Thuật ngữ tiếng Anh lần đầu xuất hiện → giải nghĩa tiếng Việt trong ngoặc.
- Cấm các cụm từ rỗng: "nhìn chung", "xét về mặt", "trên cơ sở", "trong khuôn khổ", "một cách toàn diện", "qua quá trình phân tích và đánh giá".

---

## 13. Minimum Narrative Depth (Độ sâu Diễn giải Tối thiểu)

Mọi Tờ trình/Báo cáo chính thức (Mode 2: .docx, Mode 1: .md) khi xuất file PHẢI đạt tổng nội dung phần thuyết minh **≥ 800 từ** (không tính bảng, heading, caption, Approval Matrix).
Nếu bản nháp dưới ngưỡng → AI phải tự bổ sung diễn giải theo thứ tự ưu tiên:
1. Bối cảnh & Lý do trình duyệt (tại sao bây giờ?)
2. Đánh giá hiện trạng chi tiết (cái gì hư? hư đến mức nào?)
3. Phương án đã xem xét và loại bỏ (tại sao không chọn?)
4. Diễn giải chi tiết phương án đề xuất (làm gì? bằng gì? bao nhiêu?)

---

## 14. Mandatory Illustration Integration (Bắt buộc Hình ảnh Minh họa)

Mọi Tờ trình chính thức BẮT BUỘC đính kèm tối thiểu **2 hình ảnh minh họa**:
- **Hình 1**: Mặt cắt chi tiết 2D (MODE 2D — Python) hoặc ảnh hiện trạng.
- **Hình 2**: Phối cảnh thiết kế 3D (MODE 3D — AI Render) hoặc biểu đồ so sánh phương án.
- Mỗi hình phải có **số hiệu** (Hình 1, Hình 2...) và **caption** mô tả.
- Ngoại lệ: Tờ trình chỉ liên quan đến phê duyệt hành chính (không có nội dung kỹ thuật) thì không bắt buộc.

---

## 15. Định dạng Version Control cho File Output

Quy tắc đặt tên file output chính thức:
`[MãDA]_[LoạiVB]_[GiaiDoan]_v[N]_[YYYYMMDD].[đuôi file]`
Ví dụ: `DuAnA_ToTrinh_BVTC_v2_20260625.docx`

Khi xuất lại file đã tồn tại:
- KHÔNG ghi đè file cũ — luôn tạo version mới (v1 → v2 → v3...)
- Ghi 1 dòng vào file `_CHANGELOG.md` cùng thư mục, format:
  `[YYYY-MM-DD HH:MM] v[N] — [Lý do sửa] — [Người yêu cầu]`

---

## 16. Tiết kiệm Token — Lazy Load Protocol

**Chỉ đọc file phụ khi thực sự cần thiết:**
- Tra tiêu chuẩn: Dùng `grep_search` với từ khóa đặc thù trước khi đọc PDF lớn. Đọc `INDEX_QUICK.md` trước `INDEX.md`.
- Vẽ MODE 3D: Đọc `MODE_3D_GUIDE.md` — KHÔNG đọc `MODE_2D_GUIDE.md`.
- Vẽ MODE 2D: Đọc `MODE_2D_GUIDE.md` — KHÔNG đọc `MODE_3D_GUIDE.md`.
- Xuất báo cáo: Đọc `SKILL_REPORT.md` — KHÔNG đọc `SKILLKC.md`.
- Tính toán kỹ thuật: Đọc `SKILLKC.md` — KHÔNG đọc `SKILL_REPORT.md`.

---

## 17. Hệ thống Mã Lỗi Chuẩn hóa (Error Code System)

| Code | Ý nghĩa | Hành động |
|---|---|---|
| `E001` | Input validation failed | Hiển thị usage + ví dụ tham số hợp lệ |
| `E002` | Missing required data | Liệt kê các field còn thiếu, ghi `Data Missing:` |
| `E003` | Calculation inconclusive | Ghi Scope Limitation, không kết luận ĐẠT |
| `E004` | Standard conflict detected | Kích hoạt SKILL_VERIFY xử lý mâu thuẫn tiêu chuẩn |
| `E005` | Handoff schema invalid | Reject handoff, yêu cầu source skill gửi lại (xem `SKILL_BRIDGE.md §4.3`) |
| `E006` | Handoff missing required field | Block execution, request data từ upstream skill |
| `E007` | Circular dependency detected | Block loop, notify User, log event |
| `W001` | Approaching threshold (>90%) | Cảnh báo sát giới hạn nhưng không block |
| `W002` | η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `W003` | Low confidence output | Đánh dấu `[PENDING_VERIFICATION]`, gửi SKILL_VERIFY |
| `I001` | Info — η ≤ 70%, VE possible | Khuyến nghị tối ưu Value Engineering |
| `I002` | Auto-trigger fired | Log trigger execution, notify next skill |

---

## 17b. Confidence Level Handling

| Level | Score Range | Meaning | Action |
|-------|------------|---------|--------|
| `HIGH` | ≥ 0.85 | Đầy đủ data, validated | Tiếp tục bình thường |
| `MEDIUM` | 0.60 - 0.84 | Thiếu một số data | AUTO gửi SKILL_VERIFY |
| `LOW` | < 0.60 | Thiếu critical data | **BLOCK** xuất file, notify User |

### Confidence Score Calculator

Tool: `_SHARED/SHARED_CONTEXT/confidence_score.py`

**5 Factors trọng số:**
| Factor | Weight | Check |
|--------|--------|-------|
| `data_completeness` | 25% | Required fields present |
| `input_quality` | 20% | Material grades, dimensions in valid ranges |
| `standard_compliance` | 20% | Standards properly cited |
| `calculation_consistency` | 20% | Internal consistency of logs |
| `source_reliability` | 15% | Data source (measured/calculated/estimated) |

**Usage:**
```bash
python _SHARED/SHARED_CONTEXT/confidence_score.py \
    --input design_output.json \
    --verbose \
    --output confidence_result.json
```

**Integration:**
- Mọi skill output khi export phải ghi `confidence_level` vào JSON
- Confidence được tự động check trước khi xuất file chính thức
- LOW confidence → block export → notify User

---

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

---

## 19. Version Control for Skills

Mỗi skill file (`SKILL.md`) phải có frontmatter version. Xem `CHANGELOG.md` tại cấp `.agents/skills/` để theo dõi lịch sử thay đổi của toàn bộ bộ skills.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 6.0 | 2026-10-12 | Master Central Orchestrator: Tích hợp Global_Dispatcher, intent_classifier.py, keyword_database.json (220+ keywords), pipeline_builder.py |
| 5.9 | 2026-09-27 | P1: Handoff Validation & Confidence Score |
| 5.8 | 2026-09-25 | **P0:** Agentic Workflow Infrastructure — SKILL_BRIDGE.md + INTER_SKILL_TRIGGERS.md |
| 5.7 | 2026-09-26 | Critical fixes: Version sync, Encoding fixes, Lazy load standardization |
| 5.6 | 2026-09-16 | Added SKILL_GEOTECH dispatcher rules |
| 5.5 | 2026-09-15 | Master Unified Release: Tích hợp đầy đủ Bảng Dispatcher, Error Codes, Quy tắc tính toán, Minimum Narrative Depth, Mandatory Illustration và sửa lỗi công thức cơ học kết cấu. |
| 5.4 | 2026-08-30 | Audit fixes: SKILL_INDEX v1.4 sync, REGISTRY_INDEX rewrite, registry.json v2.1.0; STANDARDS_LOCK v2.3.0 |
| 5.3 | 2026-08-30 | Reorganized structure: _SYSTEM/, _CORE_SKILLS/, _SUPPORT_SKILLS/, _SHARED/; Created README.md entry point |
| 5.0 | 2026-08-25 | Đồng bộ version skills, cập nhật deprecated scripts path |
| 1.0 | 2026-06-01 | Initial release |
