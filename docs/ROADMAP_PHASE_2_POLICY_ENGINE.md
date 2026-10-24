# ROADMAP — KIẾN NGHỊ #2: POLICY ENGINE (MD → CODE)

> **Lưu trữ:** `memory/ROADMAP_PHASE_2_POLICY_ENGINE.md`  
> **Ngày tạo:** 2026-10-17  
> **Trạng thái:** ✅ ALL_PHASES_COMPLETED (Phase A, B, C Hoàn Thành Trọn Vẹn)  
> **Tạo bởi:** Claude | **Hoàn thành toàn bộ Phase A, B, C:** Gemini (2026-10-17)

---

## 1. BỐI CẢNH

### Kiến nghị #1 (sync_report.py) đã hoàn thành

- 10 file mới trong `tools/` + `tests/test_sync_report.py` (14/14 tests pass)
- Phát hiện **9 ERROR + 1 WARNING** stale-claims trong báo cáo v2.0 cũ
- Báo cáo mới tại `docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` đã được verify từ code thực tế
- Test 14/14 PASS trong 0.297s

### Vấn đề cần giải quyết bằng Kiến nghị #2

Hiện tại **3 nguồn quy tắc nghiệp vụ** nằm trong `.md`:

| Quy tắc | Vị trí hiện tại |
|---|---|
| 15 inter-skill triggers (POST-SDE-01, POST-GEOTECH-02...) | `skills/INTER_SKILL_TRIGGERS.md` |
| Value Engineering threshold η ≤ 0.70 | `skills/Design_Evaluation/SKILL.md` (mục 18.2) |
| 18 Red Flag triggers (FORENSIC) | `skills/SKILL_FORENSIC/references/RED_FLAG_TRIGGERS.md` |
| Failure-mode priority + repair rules | Chỉ mới đề xuất code trong báo cáo v2.0 §3.4 |
| 3 cấp priority URGENT/HIGH/NORMAL/LOW | `skills/SKILL_RFI/SKILL.md` |
| 5-factor confidence score weights | `_SHARED/SHARED_CONTEXT/confidence_score.py` (đã code) |

**Vấn đề cốt lõi:** Agent phải đọc `.md` → hiểu → áp dụng. Dễ bỏ sót, dễ hiểu sai ranh giới (η = 0.71 có trigger VE không?), không thể viết test.

---

## 2. LỢI ÍCH (đã phân tích chi tiết với user)

### 🥇 Tier 1 — Trực tiếp giải quyết vấn đề hiện tại

1. **Có thể viết unit test** cho từng rule (0 quy tắc có test hiện tại → hàng chục case biên sau khi chuyển)
2. **Tránh hiểu sai ranh giới** của agent: code rõ ràng `eta <= 0.70` vs `< 0.70`
3. **Phát hiện xung đột quy tắc** tự động qua consistency test

### 🥈 Tier 2 — Vận hành

4. **Cổng enforcement tự động** (không thể bypass như MD)
5. **Audit trail tự động** (log mỗi quyết định của policy)
6. **Tốc độ load nhanh hơn** (~30-50% token savings)

### 🥉 Tier 3 — Dài hạn

7. **Mở đường cho Evals Suite tự động** (kiến nghị #3)
8. **Tinh chỉnh quy tắc an toàn** (sửa 1 số + test, không sợ agent lỡ snapshot cũ)
9. **Khả chuyển** sang dự án khác

---

## 3. RỦI RO (đã phân tích chi tiết với user)

### 🔴 Tier 1 — Nghiêm trọng (BẮT BUỘC mitigation)

| ID | Rủi ro | Mitigation bắt buộc |
|---|---|---|
| R1.1 | Trở thành "second source of truth" gây drift ngược | Xóa rule khỏi MD sau khi code hóa. Để 1 dòng cảnh báo. Dùng `sync_report.py` verify mỗi build. |
| R1.2 | Tăng độ phức tạp cho contributor mới | Docstring đầy đủ cho mỗi rule (lý do, nguồn, ví dụ). Giữ `POLICY_DECISIONS.md` ghi rationale. |
| R1.3 | Khó thay đổi nhanh khi cần | Chỉ code hóa rule **thực sự hay trigger sai/mơ hồ**. Giữ MD cho best practice mềm. |

### 🟡 Tier 2 — Trung bình

| ID | Rủi ro | Mitigation |
|---|---|---|
| R2.1 | Performance overhead (vài ms × 100 calls) | Cache kết quả `decide()` trong session |
| R2.2 | Test coverage thành vanity metric | Chỉ tính "covered" khi rule được gọi từ entry point thật |
| R2.3 | Phiên bản Python (Pydantic/Enum cần 3.10+) | Dùng `from __future__ import annotations` + type hints đơn giản |

### 🟢 Tier 3 — Nhỏ

- Phải maintain test song song với code
- Khi rule thay đổi, phải update test
- Có thể gây "analysis paralysis" nếu code hóa quá nhiều

---

## 4. ĐÁNH GIÁ TỔNG THỂ

| Khía cạnh | Kết luận |
|---|---|
| Tốc độ áp dụng quy tắc | ✅ Lợi nhiều hơn |
| Độ tin cậy | ⚠️ Cần mitigation kỹ (R1.1) |
| Khả bảo trì | ✅ Tương đương |
| Khả đọc | ⚠️ Phụ thuộc docstring |
| Mở rộng | ✅ Tốt nếu kỷ luật |
| Token efficiency | ✅ Lợi ~20-30% |

**Kết luận cuối:** Lợi ích vượt trội rủi ro **nếu** đáp ứng 3 điều kiện:
1. Xóa rule khỏi MD (không để song song)
2. Docstring đầy đủ cho mỗi rule
3. Test integration chứng minh rule được gọi từ pipeline thật

---

## 5. ĐỀ XUẤT TRIỂN KHAI 3 PHASE

| Phase | Nhóm quy tắc | Effort | Thời gian | Risk |
|---|---|---|---|---|
| **Phase A** | Value Engineering (η ≤ 0.70) + Repair (η > 1.0) | 1-2 ngày | 1 tuần | Thấp |
| **Phase B** | 15 inter-skill triggers | 3-4 ngày | 1-2 tuần | Trung bình |
| **Phase C** | 18 Red Flag triggers + RFI priority | 2-3 ngày | 1 tuần | Trung bình |

### Quy trình mỗi phase (lặp lại)

1. Tạo `tools/policy_engine.py` module
2. Chuyển rule từ MD sang code + docstring
3. Viết test ≥ 80% coverage
4. Xóa rule khỏi MD (chỉ giữ link "xem policy_engine.py")
5. Chạy `tools/sync_report.py` để verify không phát hiện stale-claim mới
6. Commit riêng từ phase để dễ rollback

---

## 6. TRẠNG THÁI TRIỂN KHAI

| Hạng mục | Trạng thái |
|---|---|
| ✅ Phân tích lợi ích/rủi ro | Hoàn thành 2026-10-17 (Claude) |
| ✅ User duyệt Phase A | Duyệt ngày 2026-10-17 ("các yêu cầu và hoàn thiện") |
| ✅ Tạo tools/policy_engine.py (Phase A) | Hoàn thành 2026-10-17 (Gemini) — 2 rules VE & Repair + docstring + typed dataclass |
| ✅ Viết test 16 cases (Phase A) | Hoàn thành 2026-10-17 (Gemini) — 16/16 tests PASS |
| ✅ User duyệt Phase B | Duyệt ngày 2026-10-17 ("Triển khai tiếp Phase B") |
| ✅ Mở rộng policy_engine.py (Phase B) | Hoàn thành 2026-10-17 (Gemini) — 15 Inter-Skill Triggers registry & evaluator |
| ✅ Viết test 14 cases mới (Phase B) | Hoàn thành 2026-10-17 (Gemini) — Tổng cộng 30/30 tests PASS |
| ✅ User duyệt Phase C | Duyệt ngày 2026-10-17 ("Tiến hành tiếp Phase C") |
| ✅ Mở rộng policy_engine.py (Phase C) | Hoàn thành 2026-10-17 (Gemini) — 18 Red Flag triggers (FORENSIC) + Phân loại ưu tiên RFI 5 cấp |
| ✅ Viết test 12 cases mới (Phase C) | Hoàn thành 2026-10-17 (Gemini) — Tổng cộng 42/42 tests PASS trong test_policy_engine.py |
| ✅ Tích hợp vào sync_report | Hoàn thành 2026-10-17 (Gemini) — Hiển thị trong §1 TỔNG QUAN (36 active rules), 0 stale-claims |
| ✅ Chuyển giao rule MD → Code | Hoàn thành 2026-10-17 (Gemini) — Dẫn chiếu Code-enforced tại AGENTS.md §6, SKILLKC.md, INTER_SKILL_TRIGGERS.md, RED_FLAG_TRIGGERS.md, SKILL_RFI.md |
| 🎉 Hoàn tất toàn bộ Roadmap | Hệ sinh thái Policy Engine v3.0.0 hoàn chỉnh và vận hành xuất sắc! |

---

## 7. LỆNH TIẾP THEO

**Cho Gemini (đối tác):**
- Đọc file này để nắm kế hoạch
- Chờ user quyết định: triển khai Phase A / dừng tại đây / chỉnh sửa phạm vi

**Nếu user duyệt Phase A, Claude sẽ:**
1. Tạo `tools/policy_engine.py` (~80 LOC) với 2 rule:
   - `decide_eta(eta: dict) -> Action` (PASS | REPAIR | TRIGGER_VE)
   - Với docstring đầy đủ (lý do, nguồn, ví dụ)
2. Tạo `tests/test_policy_engine.py` (~10 test cases, ≥ 80% coverage)
3. Tích hợp vào `tools/sync_report.py` — thêm `policy_status` section vào §1 TỔNG QUAN
4. Xóa rule "η ≤ 0.70" khỏi `skills/Design_Evaluation/SKILL.md` (chỉ giữ link)
5. Chạy `python tools/sync_report.py` để verify report mới tự dùng policy engine
6. Commit riêng: `feat(policy-engine): code hóa VE + Repair threshold (Phase A)`

**Cấm làm trước khi user duyệt:**
- KHÔNG tạo file mới
- KHÔNG sửa MD
- KHÔNG thay đổi sync_report

---

## 8. LIÊN KẾT

- **DUAL_AGENT_BUS.json** — bus ngắn, link tới file này
- **tools/sync_report.py** — kiến nghị #1 đã hoàn thành, dùng để verify drift
- **BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md** — báo cáo v2.0 cũ (đã được sync_report ghi đè)
- **CLAUDE.md** — dual-agent protocol
- **AGENTS.md** — quy tắc liên-skill

---

*File này là canonical source cho kế hoạch Kiến nghị #2. Nếu cần cập nhật, sửa tại đây và cập nhật lại DUAL_AGENT_BUS.json.*
