# REGISTRY INDEX — Technical_Illustrator Scripts (v2.2.0)

> **Phiên bản:** v2.2.0 — 2026-11-03
> **Mục đích:** Tra cứu nhanh script vẽ kỹ thuật 2D & biểu đồ tiến độ chuẩn PMO theo tình huống thực tế
> **Nguồn sự thật:** `scripts/registry.json` (registry v2.2.0)

## Bảng Tra Cứu Nhanh (Situation → Script)

| Tình huống cần vẽ | Script | Output | Ghi chú |
|---|---|---|---|
| **Biểu đồ Tiến độ Dự án chuẩn Microsoft Project (PMO)** | `ms_project_gantt.py` | **PNG 300 DPI + Landscape DOCX** | **Split View 8 cột WBS + Gantt CPM + Summary Brackets + FS Arrows + Nghỉ lễ** |
| **Dầm BTCT — mặt cắt + bố trí thép** | `draw_rc_beam_full.py` | PNG 300 DPI | Dầm đầy đủ: mặt cắt + cốt thép + đai |
| **Dầm thép — mặt cắt** | `draw_2d_section.py` | PNG 300 DPI | I, H, kênh, hộp — tham số hóa |
| **Cột BTCT — mặt cắt** | `draw_rc_column.py` | PNG 300 DPI | Vuông, tròn — tham số hóa |
| **Vách BTCT — mặt cắt + bố trí thép** | `draw_rc_wall.py` | PNG 300 DPI | Tường chắn — tham số hóa |
| **Bu lông liên kết** | `draw_bolt_connection.py` | PNG 300 DPI | Mặt bằng + mặt cắt — tham số hóa |
| **Chi tiết hàn** | `draw_weld_detail.py` | PNG 300 DPI | Bản mã, hàn góc, hàn butt — tham số hóa |
| **Móng đơn / Móng băng** | `draw_foundation.py` | PNG 300 DPI | `--type single\\|strip` — tham số hóa |
| **Đài cọc** | `draw_pile_cap.py` | PNG 300 DPI | Nhiều loại đài cọc — tham số hóa |
| **Bố trí thép sàn** | `draw_slab_rebar.py` | PNG 300 DPI | Mặt bằng thép lưới, thanh — tham số hóa |
| **Biểu đồ nội lực (M, V, N)** | `draw_moment_diagram.py` | SVG/DXF | Biểu đồ moment, lực cắt, lực dọc — tham số hóa |
| **So sánh phương án** | `draw_comparison_chart.py` | PNG 300 DPI | Radar + Bar chart — JSON input |
