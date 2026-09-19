# DEPRECATED — Eurocode Scripts

## Ngày: 2026-08-30

## Lý do deprecation:
Các script này sử dụng tiêu chuẩn Eurocode thay vì TCVN.
**KHÔNG ĐƯỢC sử dụng cho hồ sơ thiết kế chính thức.**
Chỉ giữ lại để đối chiếu tham khảo.

## Scripts trong thư mục này:

| Script | Standard | Trạng thái | Thay thế |
|--------|----------|------------|----------|
| `calc_steel_beam.py` | EN 1993-1-1 | ❌ DEPRECATED | `calc_steel_beam_tcvn.py` (TCVN 5575:2024) |
| `calc_steel_connection.py` | EN 1993-1-8 | ❌ DEPRECATED | `calc_steel_connection_tcvn.py` (TCVN 5575:2024) |

## Cách sử dụng:

**KHÔNG DÙNG cho công việc mới.** Nếu cần đối chiếu:
```bash
# Xem script cũ để tham khảo
python _deprecated/calc_steel_beam.py --help
```

## Chính sách Version Control:

- Script trong `_deprecated/` không được cập nhật
- Script mới trong `scripts/` phải dùng TCVN theo `STANDARDS_LOCK.md`
- Mọi phát hiện bug trong scripts cũ → báo cáo nhưng KHÔNG sửa

## Nguồn tham khảo:

- `STANDARDS_LOCK.md` — Xác định tiêu chuẩn chuẩn
- `SKILL_INDEX.md` — Script mới nhất
