<!-- REFERENCE FILE — Chỉ đọc khi dùng MODE 2D (Python scripts). KHÔNG đọc khi chỉ dùng MODE 3D. -->

# MODE 2D: Bản vẽ Kỹ thuật bằng Python — Hướng dẫn Chi tiết

> **Thuật ngữ:** MODE 2D = tên gọi chính thức (trước đây gọi là "MODE B"). MODE 3D = trước đây gọi là "MODE A".

## 📐 Khi nào sử dụng MODE 2D

- Yêu cầu độ chính xác tuyệt đối về hình học (mặt cắt, chi tiết).
- Trình bày chi tiết bố trí bu lông, đường hàn, cốt thép.
- Cần xuất file `.png` sắc nét cho Thuyết minh tính toán.
- Vẽ biểu đồ so sánh phương án (radar chart, bar chart).

## ⚡ Image Output Protocol

1. **XÁC ĐỊNH** đường dẫn output **TUYỆT ĐỐI** trước khi vẽ.
2. **CHẠY** script: `run_command python scripts/<tên>.py --out "đường_dẫn_tuyệt_đối.png"`.
3. **XÁC NHẬN** file ảnh đã tồn tại bằng `list_dir` / `view_file`.
4. **NHÚNG** ảnh bằng ĐƯỜNG DẪN TUYỆT ĐỐI.

---

## Quy tắc Code Python

1. Luôn dùng `ax.set_aspect('equal')` để tỷ lệ không bị méo.
2. Đánh kích thước rõ ràng bằng `ax.annotate` + mũi tên.
3. Thêm Hatch cho vật liệu (gạch chéo: thép, chấm bi: bê tông).
4. Ghi chú kỹ thuật (Technical Notes) **bắt buộc** ở cuối hình.
5. Output path PHẢI là **đường dẫn tuyệt đối**.
6. Font Unicode: `sys.stdout.reconfigure(encoding='utf-8')` ở đầu script.
7. **DPI tối thiểu 300** khi `savefig`.

---

## Thư viện Script Có sẵn

> ⚠️ **LUÔN kiểm tra bảng này trước khi viết script mới** — tiết kiệm 3,000–8,000 token.

### Nhóm cơ bản

| Script | Chức năng | Lệnh |
|--------|-----------|------|
| `draw_2d_section.py` | Mặt cắt dầm thép I | `--h --b --tw --tf` |
| `draw_bolt_connection.py` | Liên kết bu lông (Plan + Section) | `--bolt_d --bolt_grade --n_rows --n_cols` |
| `draw_rc_column.py` | Mặt cắt cột BTCT (rect/circular) | `--type --width --depth --main_dia` |
| `draw_foundation.py` | Mặt cắt móng đơn/băng | `--type --L --B --H` |
| `draw_slab_rebar.py` | Bố trí thép sàn | `--Lx --Ly --slab_t --bot_dia_x` |
| `draw_comparison_chart.py` | Biểu đồ radar + bar chart | `--json data.json` |

### Nhóm chuyên dụng — Thủy lực & Đất nền

> ⛔ **CẢNH BÁO QUAN TRỌNG — 5 script dưới đây KHÔNG nhận tham số hình học.**
> Chúng chỉ nhận `--out`. Toàn bộ kích thước, cao độ, thông số vật liệu đều **hardcode**
> theo dự án gốc mà script được viết ra.
>
> **Hệ quả:** nếu dự án hiện tại có số liệu khác mà vẫn chạy nguyên script, bản vẽ sẽ
> **mâu thuẫn với thuyết minh tính toán** — lỗi nghiêm trọng trong hồ sơ kỹ thuật.
>
> **Bắt buộc trước khi dùng:** mở script, đối chiếu hằng số hình học với số liệu dự án
> hiện tại. Nếu khác → sửa hằng số trong script (hoặc copy ra bản mới) rồi mới chạy.
> Nếu không thể đối chiếu → báo User, KHÔNG xuất bản vẽ.

| Script | Chức năng | Tham số |
|--------|-----------|---------|
| `draw_ap_luc_dat_bo_ke.py` | Biểu đồ áp lực đất bờ kè | `--out` (hình học cố định) |
| `draw_ke_buy_dung.py` | Mặt cắt kè bu dựng (buy + giằng neo) | `--out` (hình học cố định) |
| `draw_ke_pi_gieng.py` | Mặt cắt kè pi giếng | `--out` (hình học cố định) |
| `draw_pi_gieng_composite.py` | Pi giếng composite (thép + BTCT) | `--out` (hình học cố định) |
| `draw_tham_da.py` | Tường chắn rọ đá / thảm đá | `--out` (hình học cố định) |

> 💡 Với **nhóm cơ bản** (6 script trên): gõ `python scripts/<tên_script>.py --help` để xem đầy đủ tham số.
> Danh mục đầy đủ kèm `cli_args` của cả 11 script: `scripts/registry.json`.

---

## Multi-panel Layout

Khi cần nhiều mặt cắt trên 1 figure:

- Dùng `plt.subplots(2, 2)` → 4 subplot grid 2×2.
- Mỗi subplot có title riêng (VD: "Mặt cắt A-A").
- `fig.suptitle()` cho tiêu đề chung.
- Xuất 1 file `.png` duy nhất.

## Title Block (Khung Bản Vẽ)

Khi cần bản vẽ chính thức, thêm khung ở cuối figure:

```python
fig.text(0.5, 0.01,
    f"DỰ ÁN: {project_name} | HẠNG MỤC: {item} | "
    f"TỶ LỆ: {scale} | NGÀY: {date} | NGƯỜI VẼ: AI Assistant",
    ha='center', fontsize=8,
    bbox=dict(boxstyle='round', facecolor='#F0F0F0', edgecolor='black'))
```

---

## Script Error Handling

| Lỗi | Nguyên nhân | Giải pháp |
|------|-------------|-----------|
| `ModuleNotFoundError: matplotlib` | Chưa cài thư viện | `pip install matplotlib` |
| Ký tự Unicode lỗi trên Windows | Encoding stdout | Thêm `sys.stdout.reconfigure(encoding='utf-8')` |
| Path sai / không tìm thấy file | Dùng `\` thay vì `/` | Dùng `os.path.abspath()` + raw string |
| Font không hiển thị tiếng Việt | Thiếu font Unicode | Thêm `plt.rcParams['font.family'] = 'DejaVu Sans'` |
| Ảnh bị méo tỷ lệ | Thiếu `set_aspect` | Luôn dùng `ax.set_aspect('equal')` |
