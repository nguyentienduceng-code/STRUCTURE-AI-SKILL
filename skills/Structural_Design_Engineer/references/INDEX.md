# REFERENCES INDEX — Structural_Design_Engineer

> **Phiên bản:** v1.0 — 2026-08-19
> **Mục đích:** Tra cứu nhanh file hướng dẫn theo chủ đề

---

## 1. Thiết kế Bê tông Cốt thép (BTCT)

| File | Phạm vi | Tiêu chuẩn |
|------|---------|------------|
| `RC_DESIGN_GUIDE.md` | Thiết kế uốn, cắt, nén, cột, dầm, sàn | **TCVN 5574:2018** |

**Script chính:** `../scripts/calc_rc_section.py`

---

## 2. Thiết kế Kết cấu Thép

| File | Phạm vi | Tiêu chuẩn |
|------|---------|------------|
| `STEEL_DESIGN_GUIDE.md` | Tiết diện, ổn định, LTB, liên kết bulông/hàn | **TCVN 5575:2024** (khuyến nghị) hoặc 2012 |

**Script chính:**
- Hồ sơ mới (từ 2026): `../../Design_Evaluation/calculators/steel_member_check_v2024.py`
- Hồ sơ cũ đối chiếu: `../../Design_Evaluation/calculators/steel_member_check.py`

---

## 3. Thiết kế Móng

| File | Phạm vi | Tiêu chuẩn |
|------|---------|------------|
| `FOUNDATION_DESIGN_GUIDE.md` | Móng đơn, băng, cọc — sức chịu tải, thiết kế cọc | **TCVN 10304:2025**, **TCVN 9362:2012** |

**Script chính:** `../../Design_Evaluation/calculators/foundation_bearing.py`

---

## 4. Tra cứu Tiêu chuẩn (chung)

| File | Mục đích |
|------|----------|
| `../../STANDARDS_LOCK.md` | Nguồn sự thật DUY NHẤT về phiên bản tiêu chuẩn |
| `../../Design_Evaluation/standards/INDEX_QUICK.md` | Tra nhanh file PDF theo chủ đề |

---

## 5. Quick Reference

```
Muốn thiết kế...        → Dùng script                 → Theo tiêu chuẩn
─────────────────────────────────────────────────────────────────────
Dầm / sàn BTCT          → calc_rc_section.py          → TCVN 5574:2018
Thanh thép chịu lực     → steel_member_check_v2024.py → TCVN 5575:2024
Liên kết bulông          → calc_steel_connection.py   → TCVN 5575:2024
Móng nông (đơn/băng)    → foundation_bearing.py      → TCVN 9362:2012
Móng cọc                → Tính tay + verify          → TCVN 10304:2025
Kiểm tra võng            → deflection_check.py         → TCVN 5574:2018
```

---

*Lưu ý: Các script trong `../../Design_Evaluation/calculators/` được gọi chung, không cần copy riêng vào thư mục này.*
