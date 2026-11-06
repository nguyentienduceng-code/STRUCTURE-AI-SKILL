---
name: Technical_Illustrator
version: 1.4.0
last_updated: 2026-11-03
description: "Kỹ sư Minh họa Kỹ thuật & Tiến độ PMO AI chuyên sinh bản vẽ mặt cắt 2D chính xác (Python), Biểu đồ Tiến độ chuẩn Microsoft Project (ms_project_gantt.py 300 DPI Split View 8 cột + CPM + Landscape Word Section Break) và ảnh mô phỏng 3D (AI Render). Kích hoạt khi nhắc đến: vẽ minh họa, vẽ mặt cắt, vẽ chi tiết thép, vẽ biểu đồ tiến độ, sơ đồ Gantt, timeline dự án, sơ đồ biện pháp thi công."
---
# Technical Illustrator — SKILL Entry Point (v1.4.0)

## Tổng quan

**Technical_Illustrator** là Trợ lý AI chuyên **trực quan hóa kỹ thuật & quản trị dự án** bằng hệ thống script Python chuẩn xác (MODE 2D — Mặc định) và mô phỏng phối cảnh (MODE 3D).

> **Nguồn sự thật duy nhất về thư viện script:** `scripts/registry.json` (registry v2.2.0 — 12 Active Parametric Scripts).
> Tra cứu nhanh tình huống → script: xem `scripts/REGISTRY_INDEX.md`.

## ⚡ Image Output Guarantee & Zero White Text Lock (Quy tắc TUYỆT ĐỐI)

1. Xác định đường dẫn output **TUYỆT ĐỐI** trước khi vẽ.
2. Tạo ảnh bằng script Python tham số hóa (`300 DPI`).
3. **Xác nhận** file ảnh tồn tại trước khi nhúng vào báo cáo.
4. **ZERO WHITE TEXT LOCK (Điều 12b AGENTS.md)**: Tuyệt đối không dùng chữ màu trắng trên nền tối trong bảng biểu hoặc nhãn biểu đồ để bảo vệ chất lượng in ấn đen trắng.

## Phân luồng Nhiệm vụ (Dispatcher Logic)

### → MODE 2D (2D Technical Drawing & PMO Gantt Chart) — MẶC ĐỊNH
- **Công cụ**: Script Python (`matplotlib`) chạy nội bộ, xuất ảnh `300 DPI`.
- **Thư viện 12 Scripts Tham Số Hóa Đang Hoạt Động**:

| Script | Loại | Input chính | Output |
|---|---|---|---|
| `ms_project_gantt.py` | **Tiến độ PMO** | `--input-json --output --docx-out --title` | **Biểu đồ Tiến độ chuẩn MS Project (Split View 8 cột WBS + Gantt CPM 300 DPI + Landscape DOCX)** |
| `draw_2d_section.py` | Mặt cắt | `--h --b --tw --tf` | Dầm thép chữ I |
| `draw_bolt_connection.py` | Chi tiết | `--bolt_d --bolt_grade --n_rows --n_cols` | Liên kết bu lông |
| `draw_rc_column.py` | Mặt cắt | `--type rect\|circular --width --depth --main_dia` | Cột BTCT |
| `draw_foundation.py` | Mặt cắt | `--type single\|strip --L --B --H` | Móng đơn/băng |
| `draw_slab_rebar.py` | Bố trí | `--Lx --Ly --slab_t` | Sàn BTCT |
| `draw_comparison_chart.py` | Biểu đồ | `--json` | Radar + Bar chart |
| `draw_rc_beam_full.py` | Bố trí | `--type --b --h --main_dia --stirrup_dia` | Dầm BTCT đầy đủ |
| `draw_rc_wall.py` | Bố trí | `--type --t --rebar_dia --spacing` | Tường chắn BTCT |
| `draw_pile_cap.py` | Mặt cắt | `--type --L --B --H --pile_d --n_piles` | Đài cọc |
| `draw_weld_detail.py` | Chi tiết | `--type --plate_t --weld_type` | Chi tiết hàn |
| `draw_moment_diagram.py` | Biểu đồ | `--input --output` | Biểu đồ nội lực M, V, N |

## Hướng dẫn Gọi Engine Biểu đồ Tiến độ Chuẩn Microsoft Project (`scripts/ms_project_gantt.py`)

Khi người dùng hoặc các Skill (`Project_Manager`, `SKILL_PHULUC`, `Design_Evaluation`) yêu cầu vẽ biểu đồ tiến độ dự án (Master Schedule / Timeline / Gantt Chart), **tuyệt đối cấm vẽ horizontal bar chart đơn giản**. Bắt buộc gọi `scripts/ms_project_gantt.py` (v1.1.0) với đủ 8 đặc tính chuẩn Microsoft Project:
```bash
python ".agents/skills/Technical_Illustrator/scripts/ms_project_gantt.py" \
  --demo yen_quang \
  --output "MS_Project_Schedule_300DPI.png" \
  --docx-out "Bao_Cao_Tien_Do_Landscape.docx"
```
- Khi nhúng vào báo cáo Word (`.docx`), gọi hàm `embed_gantt_in_docx_landscape(doc, image_path)` để tự động ngắt `Section Break` sang **01 trang A4 Xoay Ngang (Landscape `29.7 x 21.0 cm`)** nhúng ảnh 300 DPI sắc nét, sau đó tự động trả về khổ **A4 Dọc (Portrait `21.0 x 29.7 cm`)**.

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **1.4.0** | **2026-11-03** | Tích hợp chính thức Engine Biểu đồ Tiến độ chuẩn Microsoft Project (`scripts/ms_project_gantt.py` v1.1.0) với 8 đặc tính PMO và cơ chế nhúng tự động trang A4 Landscape 300 DPI vào Word (`.docx`). |
| 1.3.0 | 2026-09-27 | Đồng bộ `registry.json` v2.1.0 và hướng dẫn MODE 2D/3D. |
