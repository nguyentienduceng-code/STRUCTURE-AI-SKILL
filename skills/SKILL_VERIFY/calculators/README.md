# SKILL_VERIFY Calculators

> SKILL_VERIFY không có calculators riêng. Skill này kiểm chứng kết quả từ:
> - `Structural_Design_Engineer/calculators/` — tính toán kết cấu
> - `SKILL_GEOTECH/calculators/` — phân tích địa kỹ thuật

## Flow
1. Nhận JSON handoff từ skill nguồn
2. Gọi calculator gốc để tái tính
3. So sánh kết quả (tolerance: ±5%)
4. Báo cáo variance

## Validation Scripts
- `validate_handoff_schema.py` — (shared via `_SHARED/`)
- `confidence_score.py` — (shared via `_SHARED/`)

---
*Cập nhật: 2026-10-13*
