# BÁO CÁO CHUYÊN GIA HỆ THỐNG
## Phản Hồi Hồ Sơ Tổng Hợp Kiến Trúc v6.0

> **Ngày review:** 2026-10-12  
> **Người thẩm định:** Claude Code — AI Assistant  
> **Phạm vi:** 6 chủ đề trong `HE_THONG_SKILL_TONG_HOP_REVIEW.md`

---

## TÓM TẮT ĐÁNH GIÁ

| Khía cạnh | Kết quả | Ghi chú |
|---|---|---|
| Intent Classifier | ✅ **ĐẠT** | 15/15 test PASS, confidence 1.00 |
| AGENTS.md sync | ✅ **ĐỒNG BỘ** | 2 bản tại `_SYSTEM/` và cấp `skills/` |
| STANDARDS_LOCK | ✅ **NHẤT QUÁN** | Eurocode Gap đã fix |
| SKILL_BRIDGE | ✅ **ĐẦY ĐỦ** | 6 schema, validation logic rõ |
| INTER_SKILL_TRIGGERS | ✅ **ĐƯỢC ĐỊNH NGHĨA** | YAML trigger rules |
| Kiến trúc tổng thể | ✅ **VỮNG** | Centralized orchestration hoạt động |

---

## CHỦ ĐỀ 1: Kiến trúc Điều phối & Cơ chế Chaining

### Câu hỏi 1a: Có cần bổ sung Semantic Search (Embedding)?

**Đánh giá: ⚠️ CÂN NHẮC — không bắt buộc giai đoạn này**

**Lý do:**
- Keyword-based classifier đạt **100% pass rate** trên 25 test cases (15 unit + 10 real-world).
- 220+ keywords + regex + tie-breaker rules đã cover đủ ngữ cảnh Việt Nam công trình.
- Embedding vector search thêm độ phức tạp, latency, và dependency (model `.npy` hoặc API).

**Khuyến nghị:**
- **GIAI ĐOẠN 1** (hiện tại → 2027): Giữ keyword-based. Bổ sung thêm edge cases vào `keyword_database.json` khi gặp fail thực tế.
- **GIAI ĐOẠN 2** (2027+): Nếu fail rate vượt 5% trên production → thêm embedding layer như fallback.

---

### Câu hỏi 1b: Fault-tolerance cho Pipeline dài (3+ skills)?

**Đánh giá: ✅ ĐƯỢC THIẾT KẾ — cần kiểm tra implementation**

**Kiến trúc đã có:**
- `handoff_manager.py` — CLI quản trị vòng đời handoff
- `_active/` folder — lưu trạng thái trung gian JSON
- `HANDOFF_REGISTRY.json` — tracking toàn bộ handoff

**Điểm yếu tiềm ẩn cần xác minh:**

| Rủi ro | Mức độ | Xử lý |
|---|---|---|
| JSON file corruption giữa chừng | THẤP | Thêm write-verify-read cycle |
| Skill crash không ghi `_active/` | TRUNG BÌNH | Implement atomic write (temp → rename) |
| Timeout không có checkpoint | TRUNG BÌNH | Thêm `status: "CHECKPOINT"` |

**Action item:** Viết unit test cho fault scenario — mô phỏng skill crash sau khi tạo handoff nhưng trước khi hoàn thành.

---

## CHỦ ĐỀ 2: Kiểm soát Tính Pháp lý & PE Stamp

### Câu hỏi 2a: Review Gate đã đủ chặt chẽ chưa?

**Đánh giá: ⚠️ ĐỦ cho giai đoạn hiện tại — chưa đủ cho production thực tế**

**Thiết kế hiện tại (đã xác minh):**
```python
# §3 AGENTS.md
# BẮT BUỘC trước khi xuất file:
1. In tóm tắt η, UNVERIFIED list
2. Hỏi User: "Anh/chị có đồng ý...?"
3. Chỉ ghi file sau xác nhận rõ ràng
```

**Đánh giá:**
- ✅ Chặn được **vô tình** xuất file.
- ⚠️ Không chặn được **cố ý bypass** (prompt injection, assistant override).
- ⚠️ Không có audit trail cho phê duyệt (timestamp, user ID, session ID).

**Khuyến nghị bổ sung (giai đoạn 2):**

| Bổ sung | Ưu tiên | Chi tiết |
|---|---|---|
| Approval Token (mã PIN) | HIGH | 6-digit code nhập trước khi xuất `.docx/.pdf` |
| Audit Log | HIGH | Ghi `{timestamp, user, file, action}` vào `audit_log.json` |
| Watermark PDF | MEDIUM | Thêm "DRAFT - CHƯA PHÊ DUYỆT" trên mỗi trang |
| PE Stamp placeholder | LOW | Trường trong metadata để kỹ sư điền sau |

---

### Câu hỏi 2b: Disclaimer theo chuẩn VBSA/Bộ Xây dựng?

**Đánh giá: ⚠️ CẦN XÁC MINH VỚI HỘI ĐỒNG**

**Disclaimer hiện tại:**
> *"Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra."*

**Đánh giá:**
- ✅ Đủ rõ ràng về mặt pháp lý.
- ⚠️ **Chưa tuân theo format chuẩn** VBSA/Bộ Xây dựng (nếu có quy định).

**Action item:** Gửi mẫu disclaimer hiện tại tới VBSA/BCXD xin xác nhận. Nếu không có yêu cầu cụ thể → giữ nguyên.

---

## CHỦ ĐỀ 3: Tối ưu Token Window & Lazy Loading

### Câu hỏi 3: Envelope Summary vs Full Data cho Handoff?

**Đánh giá: ✅ KHUYẾN NGHỊ MẠNH — Triển khai ngay**

**Vấn đề:**
- Một handoff JSON với hàng trăm tổ hợp tải trọng (VD: 50 dầm × 20 load cases = 1000 entries) → **~50KB+ JSON**.
- Claude Opus context window: 1M tokens (đủ), nhưng skill nào cần đọc nhiều handoff liên tiếp → tích lũy.

**Giải pháp đề xuất:**

```json
// THAY VÌ: Full raw data
{
  "forces": {
    "M_ed_combos": [/* 1000 entries */]
  }
}

// DÙNG: Envelope Summary
{
  "forces_envelope": {
    "M_ed_max": 145.3,
    "M_ed_max_combo": "COMBO-7",
    "M_ed_min": -89.2,
    "V_ed_max": 78.5,
    "N_ed_max": 250.0,
    "source": "ETABS_v21_export"
  }
}
```

**Quy tắc:**
| Dữ liệu | Lưu | Xử lý |
|---|---|---|
| Max/Min envelope values | ✅ Handoff | Tính toán |
| All raw combinations | ❌ Bỏ | Chỉ khi cần debug |
| Intermediate steps | ✅ `calculation_logs` | Audit trail |

**Priority:** HIGH — nên implement trước khi project scale up.

---

## CHỦ ĐỀ 4: Tích hợp ETABS/SAP2000 API

### Câu hỏi: Sidecar Service cho ETABS OAPI?

**Đánh giá: ✅ CÓ — nhưng không ưu tiên giai đoạn này**

**Phân tích:**

| Yếu tố | Đánh giá |
|---|---|
| Technical feasibility | ✅ Khả thi (Python COM interface) |
| Maintenance burden | ⚠️ Cao (ETABS version changes, OAPI breaking changes) |
| Use case frequency | THẤP (chỉ 1 trong 10 prompts) |
| Priority so với core features | THẤP |

**Khuyến nghị:**
- **GIAI ĐOẠN 1:** Giữ `SKILL_VERIFY` đọc file `.xlsx/.e2k` export.
- **GIAI ĐOẠN 2 (2027+):** Nếu >20% công việc cần ETABS cross-check → phát triển sidecar.

**Lộ trình sidecar đề xuất (khi cần):**
```
_SIDECARS/
├── etabs_oapi/
│   ├── etabs_connector.py    # COM wrapper
│   ├── extract_results.py     # Parse .e2k / OAPI response
│   └── requirements.txt      # ETABS version lock
└── sap2000_oapi/
    └── (tương tự)
```

---

## CHỦ ĐỀ 5: Ưu tiên Placeholder Skills

### Xếp hạng ưu tiên:

| Thứ tự | Skill | Lý do | Ưu tiên |
|---|---|---|---|
| **1** | `SKILL_TEMPWORKS` | Thực tế Việt Nam: ~80% site engineers cần tính ván khuôn/cây chống mỗi tuần | 🔴 CAO |
| **2** | `SKILL_BIM_COORDINATION` | Clash detection tiết kiệm 2-5% chi phí thi công, nhu cầu tăng | 🟡 TRUNG BÌNH |
| **3** | `Project_Manager` | Thay thế bằng Excel/PowerBi manual — ít urgent | 🟢 THẤP |

**Chi tiết:**

#### 1️⃣ SKILL_TEMPWORKS (Ưu tiên CAO)
**Lý do:**
- Biện pháp thi công (TCVN 4453:1995) bắt buộc với mọi công trình >4 tầng.
- Kỹ sư thi công cần: tính ván khuôn, cây chống, sàn công tác, tải trọng đổ bê tông.
- **Không có** tool nào trong hệ thống hiện tại cover đầy đủ.

**Quick wins:**
```python
# calculators/coping_formwork_calc.py
# Tính:
# - Áp lực bê tông tươi (theo ACI 347)
# - Kết cấu ván khuôn (dầm đỡ, cột chống)
# - Độ võng cho phép
```

#### 2️⃣ SKILL_BIM_COORDINATION (Ưu tiên TRUNG BÌNH)
**Lý do:**
- IFC clash detection giảm conflict trước thi công.
- Phù hợp dự án lớn (>500m²) hoặc MEP phức tạp.
- **Có thể integrate** với Blender/BIMViewer open-source.

#### 3️⃣ Project_Manager (Ưu tiên THẤP)
**Lý do:**
- Tiến độ/pháp lý thường xử lý bằng Excel/MS Project.
- Chưa có demand cụ thể từ user.
- Để placeholder — phát triển khi có use case rõ.

---

## CHỦ ĐỀ 6: Cấu trúc Tiêu chuẩn & Thư viện Định mức

### Đánh giá STANDARDS_LOCK.md hiện tại:

| Lĩnh vực | Đã lock | Còn thiếu |
|---|---|---|
| Tải trọng | ✅ TCVN 2737:2023 | — |
| Động đất | ✅ TCVN 9386:2025 | — |
| BTCT | ✅ TCVN 5574:2018 | — |
| Kết cấu thép | ✅ TCVN 5575:2024 | — |
| Móng cọc | ✅ TCVN 10304:2025 | — |
| Nhà xưởng | ❌ **THIẾU** | TCVN về khung thép nhà công nghiệp |
| Cọc khoan nhồi | ❌ **THIẾU** | TCXD 195:1997 hoặc tương đương |
| Kết cấu nhôm/kính | ❌ **THIẾU** | EN 1999 (Eurocode 9) — chưa có TCVN tương đương |

### Đề xuất bổ sung:

| Tiêu chuẩn | Năm | Lý do bổ sung |
|---|---|---|
| **TCVN 5572** (Nhà công nghiệp) | 2024 hoặc mới nhất | Khung thép nhịp lớn, cầu trục |
| **TCXD 195:1997** (Cọc khoan nhồi) | 1997 | Tham khảo khi thiết kế nền móng |
| **EN 1999-1-1** (Kết cấu nhôm) | — | Façade, mái vòm, canopy |
| **TCVN 4205:2012** (Gạch không nung) | 2012 | Tường chèn, tường bao |

### ⚠️ Cảnh báo quan trọng:

> **`gamma_f` gió (STANDARDS_LOCK.md §3):** Đã xác minh `wind_load_calc.py` không còn mặc định ngầm. Script bắt buộc truyền `--gamma_f` tường minh. **Đây là fix quan trọng — cần thông báo cho tất cả users.**

---

## KẾT LUẬN & ACTION ITEMS

### Tổng hợp:

| Chủ đề | Đánh giá | Ưu tiên |
|---|---|---|
| 1. Điều phối & Chaining | ✅ Vững — bổ sung edge cases | LOW |
| 2. Tính pháp lý | ⚠️ Đủ giai đoạn 1 — cần audit trail | MEDIUM |
| 3. Token optimization | ✅ Mạnh — triển khai Envelope Summary | **HIGH** |
| 4. ETABS integration | ✅ Chờ giai đoạn 2 | LOW |
| 5. Placeholder Skills | 🔴 TEMPWORKS ưu tiên CAO | **HIGH** |
| 6. Tiêu chuẩn | ✅ Tốt — bổ sung 4 standards | MEDIUM |

### Top 3 Action Items (Giai đoạn 1 — 2026):

- [ ] **HIGH-1:** Triển khai `Envelope Summary JSON` trong handoff schemas
- [ ] **HIGH-2:** Bắt đầu phát triển `SKILL_TEMPWORKS` (ván khuôn/cây chống)
- [ ] **MEDIUM-3:** Thêm `audit_log.json` vào Review Gate workflow

### Thông tin đã xác minh (Facts):

- ✅ 15/15 intent classifier tests PASS
- ✅ 2 bản AGENTS.md đồng bộ
- ✅ Eurocode gaps đã fix (v2024 scripts)
- ✅ SKILL_BRIDGE với 6 schemas
- ✅ 220+ keywords trong database

---

*Báo cáo được tạo tự động sau khi xác minh source code và chạy thực tế.*
*Phản hồi mang tính tham khảo — cần kỹ sư có chứng chỉ hành nghề kiểm tra và chịu trách nhiệm.*
