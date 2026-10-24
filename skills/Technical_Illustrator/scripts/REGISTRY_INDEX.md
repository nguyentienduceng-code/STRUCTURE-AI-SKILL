# REGISTRY INDEX — Technical_Illustrator Scripts

> **Phiên bản:** v2.0 — 2026-08-30
> **Mục đích:** Tra cứu nhanh script vẽ theo tình huống thực tế
> **Nguồn sự thật:** `scripts/registry.json` (registry v2.0.0)

---

## Bảng Tra Cứu Nhanh (Situation → Script)

| Tình huống cần vẽ | Script | Output | Ghi chú |
|---|---|---|---|
| **Dầm BTCT — mặt cắt + bố trí thép** | `draw_rc_beam_full.py` | PNG | Dầm đầy đủ: mặt cắt + cốt thép + đai |
| **Dầm thép — mặt cắt** | `draw_2d_section.py` | PNG | I, H, kênh, hộp — tham số hóa |
| **Cột BTCT — mặt cắt** | `draw_rc_column.py` | PNG | Vuông, tròn — tham số hóa |
| **Vách BTCT — mặt cắt + bố trí thép** | `draw_rc_wall.py` | PNG | Tường chắn — tham số hóa |
| **Bu lông liên kết** | `draw_bolt_connection.py` | PNG | Mặt bằng + mặt cắt — tham số hóa |
| **Chi tiết hàn** | `draw_weld_detail.py` | PNG | Bản mã, hàn góc, hàn butt — tham số hóa |
| **Móng đơn / Móng băng** | `draw_foundation.py` | PNG | `--type single\|strip` — tham số hóa |
| **Đài cọc** | `draw_pile_cap.py` | PNG | Nhiều loại đài cọc — tham số hóa |
| **Bố trí thép sàn** | `draw_slab_rebar.py` | PNG | Mặt bằng thép lưới, thanh — tham số hóa |
| **Biểu đồ nội lực (M, V, N)** | `draw_moment_diagram.py` | SVG/DXF | Biểu đồ moment, lực cắt, lực dọc — tham số hóa |
| **So sánh phương án** | `draw_comparison_chart.py` | PNG | Radar + Bar chart — JSON input |
| **Tích hợp CAD (DCE Pro)** | `dce_trigger.py` | DWG | AI → Excel → DCE Pro Add-In |

---

## Scripts THAM SỐ HÓA — ĐANG HOẠT ĐỘNG ✅

### Nhóm THÉP

| Script | Input chính | Output |
|--------|-------------|--------|
| `draw_2d_section.py` | `--h --b --tw --tf` | Mặt cắt dầm thép I |
| `draw_bolt_connection.py` | `--bolt_d --bolt_grade --n_rows --n_cols` | Chi tiết bu lông |
| `draw_weld_detail.py` | `--type --plate_t --weld_type` | Chi tiết hàn |

### Nhóm BTCT

| Script | Input chính | Output |
|--------|-------------|--------|
| `draw_rc_column.py` | `--type rect\|circular --width --depth --main_dia` | Cột BTCT |
| `draw_rc_beam_full.py` | `--type --b --h --main_dia --stirrup_dia` | Dầm BTCT đầy đủ |
| `draw_rc_wall.py` | `--type --t --rebar_dia --spacing` | Tường chắn BTCT |
| `draw_slab_rebar.py` | `--Lx --Ly --slab_t` | Bố trí thép sàn |

### Nhóm MÓNG

| Script | Input chính | Output |
|--------|-------------|--------|
| `draw_foundation.py` | `--type single\|strip --L --B --H` | Móng đơn/băng |
| `draw_pile_cap.py` | `--type --L --B --H --pile_d --n_piles` | Đài cọc |

### Nhóm BIỂU ĐỒ

| Script | Input chính | Output |
|--------|-------------|--------|
| `draw_comparison_chart.py` | `--json` | Radar + Bar chart |
| `draw_moment_diagram.py` | `--input --output` | SVG/DXF biểu đồ M, V, N |

---

## Scripts ĐÃ DI CHUYỂN sang `_deprecated/` ⚠️

**5 scripts dưới đây đã được DI CHUYỂN sang `scripts/_deprecated/`. KHÔNG sử dụng.**

| Script cũ | Lý do |
|-----------|-------|
| `draw_ap_luc_dat_bo_ke.py` | Fixed geometry — không nhận tham số |
| `draw_ke_buy_dung.py` | Fixed geometry — không nhận tham số |
| `draw_ke_pi_gieng.py` | Fixed geometry — không nhận tham số |
| `draw_pi_gieng_composite.py` | Fixed geometry — không nhận tham số |
| `draw_tham_da.py` | Fixed geometry — không nhận tham số |

---

## Tích hợp DCE Pro (CAD Integration)

Luồng hoạt động:
```
AI Agent (Claude Code)
       │
       ├── 1. Tính toán kết cấu
       │
       ├── 2. Gọi dce_writer.py → điền data vào Excel
       │
       ├── 3. DCE Pro Add-In đọc Excel → vẽ CAD
       │
       └── 4. Agent trích xuất PDF/DWG
```

Templates DCE Pro:
| Module | Template | Status |
|--------|----------|--------|
| Dầm BTCT | `09. DCE_Beam_2020.xlsm` | ✅ |
| Cột BTCT | `08. DCE_ColumnWall_2020.xlsm` | ✅ |
| Thép Dầm | `20. TCVN 5575 Steel Beam Design - Section I.xlsm` | ✅ |
| Thép Cột | `25. TCVN 5575 Steel Column Design - Section I.xlsm` | ✅ |
| Bu lông neo | `160. Chi tiet bu long neo.xlsm` | ✅ |

---

## Quy ước Đặt tên File Output

```
{ProjectCode}_{Element}_{View}_{Rev}.png
```

| Phần | Ví dụ | Ghi chú |
|------|-------|---------|
| ProjectCode | `ABC` | Mã dự án (3 ký tự) |
| Element | `B1`, `C2`, `FD` | Ký hiệu cấu kiện |
| View | `PLAN`, `SEC`, `3D` | LOẠI hình chiếu |
| Rev | `A`, `B`, `R1` | Bản revision |

**Ví dụ:**
- `ABC_B1_SEC_A.png` — Dầm B1, mặt cắt, revision A
- `XYZ_C2_PLAN_R0.png` — Cột C2, mặt bằng, revision 0
- `PQR_F1_3D_R1.png` — Móng F1, phối cảnh, revision 1

---

## MODE 2D vs MODE 3D

| MODE | Công cụ | Giá trị | Khi nào dùng |
|------|---------|---------|---------------|
| **MODE 2D** | Python/matplotlib | Bản vẽ kỹ thuật chính xác | MẶC ĐỊNH |
| **MODE 3D** | AI Render | Minh họa phối cảnh | CHỈ khi cần render 3D rõ ràng |

> ⚠️ **Lưu ý:** MODE 3D (AI render) không có giá trị kỹ thuật chính xác. KHÔNG dùng làm căn cứ thi công.

---

*Cập nhật: 2026-08-30 v2.0 — Đồng bộ với registry.json v2.0.0*
