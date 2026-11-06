---
name: Project_Manager
version: 2.0.0
last_updated: 2026-11-03
description: "Giám đốc Quản lý Dự án Đầu tư Xây dựng (PMO Director). Chuyên lập Kế hoạch Tổng thể (Master Schedule), vẽ Biểu đồ Tiến độ chuẩn Microsoft Project (ms_project_gantt.py 300 DPI Split View 8 cột + CPM + Landscape Word Section Break), xuất/nhập file dữ liệu tiến độ chuẩn Microsoft Project XML (msproject_xml_engine.py MSPDI Schema) và chuyển đổi sang .mpp, phân cấp công trình (TT 06/2021), tính toán EVM/CPM, kiểm soát hồ sơ QLTK và KPI ISO 9001:2015."
---

# Project_Manager — Giám đốc Quản lý Dự án Đầu tư Xây dựng (v2.0.0 — Unified Microsoft Project Ecosystem)

## 1. Vai trò & Năng lực Cốt lõi
**Project_Manager** đóng vai trò **Giám đốc Quản lý Dự án (PMO Director)** & **Trưởng Ban Quản lý Thiết kế (QLTK)**, vận hành trên 6 trụ cột:
1. **Engine Dữ liệu Tiến độ Microsoft Project XML & MPP (`scripts/msproject_xml_engine.py` v1.0.0)**:
   - Xuất dữ liệu tiến độ sang chuẩn mở quốc tế **MSPDI XML (Microsoft Project Data Interchange Schema)**, tương thích 100% với Microsoft Project 2016, 2019, 2021 và Microsoft 365.
   - Hỗ trợ đầy đủ: Lịch làm việc chuẩn Standard Vietnam (8h/ngày), cấu trúc phân rã WBS đa cấp, quan hệ tiền nhiệm phụ thuộc (FS, SS, FF, SF), tính toán đường găng Critical Path, mốc bàn giao Milestone, và dải ngoại lệ nghỉ Lễ/Tết Nguyên Đán.
   - Hỗ trợ đọc ngược file XML cập nhật từ MS Project để phân tích phương sai tiến độ (Schedule Slippage) và tái kết xuất báo cáo tự động.
2. **Engine Biểu đồ Tiến độ Chuẩn Microsoft Project (`scripts/ms_project_gantt.py` v1.1.0)**:
   - Xuất bản biểu đồ tiến độ 300 DPI với giao diện đôi (Split View: Bảng WBS 8 cột bên trái + Gantt Canvas 2 tầng thời gian bên phải), thanh tổng hợp Summary Brackets (`#1E3246`), đường găng CPM (`#D32F2F`), mũi tên liên kết phụ thuộc zic-zac (`FS/SS`), mốc kiểm soát Milestone (`0d`), dải cách ly nghỉ lễ (`#FFEBEE`) và cơ chế tự động ngắt Section Break sang trang **A4 Xoay Ngang (Landscape)** khi nhúng vào văn bản Word (`.docx`).
3. **Kiểm toán Tiến độ & Giá trị Thu được (`scripts/evm_cpm_calculator.py`)**: Tính toán định lượng `CPI`, `SPI`, `EAC`, `VAC`, `TCPI` và đường găng `CPM`.
4. **Phân cấp Công trình & Lộ trình Pháp lý (`scripts/project_grading.py` & `scripts/project_roadmap.py`)**: Phân cấp theo Thông tư 06/2021/TT-BXD, Luật Xây dựng và Nghị định 175/2024/NĐ-CP.
5. **Chuẩn hóa Báo cáo Tracking Hồ sơ Thiết kế (`scripts/qltk_tracking_exporter.py` v2.1)**: Tái cấu trúc bảng Tracking/Pendinglist QLTK theo chuẩn in ấn kỹ thuật.
6. **Chuẩn hóa Biểu mẫu KPI ISO 9001:2015 (`scripts/iso_kpi_exporter.py` v1.1)**: Liên kết công thức sống `SUM` giữa kế hoạch và kết quả thực hiện.

---

## 2. Hướng dẫn Sử dụng Động cơ Xuất / Nhập File Microsoft Project XML (`scripts/msproject_xml_engine.py`)

### 2.1. Cú pháp Xuất File Dữ liệu Tiến độ XML
```python
from msproject_xml_engine import export_to_msproject_xml

# Xuất danh sách công việc sang file XML chuẩn Microsoft Project
export_to_msproject_xml(
    tasks=tasks_data,
    output_xml_path=r"g:\My Drive\Google AI Studio\01_Projects\HO YEN QUANG\04_Deliverables_ToTrinh\YenQuang_TienDo_MSProject.xml",
    project_name="TIẾN ĐỘ THỰC HIỆN CÁC GÓI TƯ VẤN - DỰ ÁN HỒ YÊN QUANG",
    company_name="TẬP ĐOÀN C.T GROUP",
    start_date="2026-11-10",
    finish_date="2027-05-31",
    holidays=[
        {"start": "2027-01-26", "end": "2027-02-05", "label": "Nghỉ Tết Nguyên Đán Đinh Mùi 2027"}
    ]
)
```

### 2.2. Cú pháp Đọc Ngược File XML từ Microsoft Project vào AI
```python
from msproject_xml_engine import import_from_msproject_xml

# Đọc file XML đã được PM / Kỹ sư cập nhật trên phần mềm MS Project
tasks_updated = import_from_msproject_xml(r"g:\My Drive\Google AI Studio\01_Projects\DuAn\tiendo_capnhat.xml")
for t in tasks_updated:
    print(f"Task {t['wbs']}: {t['name']} - % Xong: {t.get('percent_complete', 0)}%")
```

---

## 3. Hướng dẫn Gọi Lệnh Engine Biểu đồ Tiến độ Chuẩn Microsoft Project (`scripts/ms_project_gantt.py` v1.1.0)

### 3.1. Cú pháp dòng lệnh (CLI)
```bash
# 1. Chạy Demo chuẩn PMO xuất ảnh 300 DPI và tự động nhúng vào trang A4 Landscape Word (.docx)
python ".agents/skills/Project_Manager/scripts/ms_project_gantt.py" \
  --demo yen_quang \
  --output "MS_Project_Master_Schedule_PMO.png" \
  --docx-out "Ke_Hoach_Tien_Do_PMO.docx"

# 2. Vẽ biểu đồ tiến độ từ dữ liệu JSON dự án thực tế
python ".agents/skills/Project_Manager/scripts/ms_project_gantt.py" \
  --input-json "project_schedule_wbs.json" \
  --output "Project_Schedule_MSProject_300DPI.png" \
  --title "TIẾN ĐỘ TỔNG THỂ DỰ ÁN (MASTER SCHEDULE)" \
  --subtitle "Giai đoạn Thiết kế & Thi công — Kiểm soát Đường găng CPM"
```

### 3.2. Cú pháp gọi trực tiếp trong Python & Nhúng vào Word (`.docx`)
```python
from ms_project_gantt import draw_ms_project_gantt, embed_gantt_in_docx_landscape

# Bước 1: Kết xuất biểu đồ tiến độ chuẩn MS Project (300 DPI)
draw_ms_project_gantt(
    tasks=tasks_list,
    output_path="schedule_ms_project.png",
    title="KẾ HOẠCH TIẾN ĐỘ TỔNG THỂ DỰ ÁN",
    subtitle="Phân tích Đường găng CPM & Kiểm soát Mốc Bàn giao",
    holidays=[("2027-01-26", "2027-02-05", "Nghỉ Tết Nguyên Đán 2027")],
    status_date="2026-12-25",
    dpi=300,
)

# Bước 2: Nhúng thông minh vào trang A4 Xoay Ngang (Landscape Section Break) rồi tự trả về A4 Dọc
embed_gantt_in_docx_landscape(
    doc=doc,
    image_path="schedule_ms_project.png",
    section_title="BIỂU ĐỒ TIẾN ĐỘ TỔNG THỂ DỰ ÁN (CHUẨN MICROSOFT PROJECT — 300 DPI)",
    figure_caption="Hình 1: Biểu đồ Tiến độ Tổng thể (Split View 8 cột WBS & Đường găng CPM)",
    width_cm=25.4,
    restore_portrait=True,
)
```

---

## 4. 08 Đặc tính Kỹ thuật Bắt buộc của `ms_project_gantt.py`
1. **Giao diện đôi (Split View)**: Nửa trái là Bảng Task Sheet 8 cột (`ID` | `WBS` | `Tên công việc thụt lề theo cấp bậc` | `Thời lượng (d)` | `Bắt đầu` | `Kết thúc` | `Tiền nhiệm (Pred)` | `Tài nguyên/Đơn vị (Resources)`); nửa phải là Biểu đồ Gantt Canvas đồng bộ 100% cao độ Y.
2. **Thanh Tổng hợp Tiến độ (Summary Brackets)**: Thanh bao bọc màu than sẫm `#1E3246` có hai mỏ neo tam giác chúc xuống ở 2 đầu.
3. **Phân tầng Đường găng CPM**: Công tác găng tô màu Đỏ Găng (`#D32F2F`); công tác thường tô màu xanh chuyên ngành (`#1976D2`, `#0288D1`, `#2E7D32`).
4. **Mũi tên Liên kết Phụ thuộc (`FS` / `SS` Stepped Arrows)**: Đường zic-zac vuông góc kèm đầu mũi tên chỉ hướng.
5. **Mốc Kiểm soát (Milestones)**: Hình thoi đặc (Diamond marker) kèm nhãn ngày tháng tại thời lượng `0d`.
6. **Thước đo Thời gian 2 Tầng (Dual-tier Timescale at Top)**: Đặt tại đỉnh biểu đồ ngang hàng Header bảng Task Sheet, hiển thị Tháng/Năm (Tầng 1 — nền `#DCE4EC` chữ `#1E3246`) và Tuần/Ngày đầu tuần (Tầng 2 — nền `#EAE6DF` chữ `#1E3246`).
7. **Dải Cách ly Ngày Nghỉ Lễ**: Dải sọc chéo hồng nhạt `#FFEBEE` viền `#EF9A9A`.
8. **Nhúng Thông minh vào Trang A4 Landscape Word (`.docx`)**: Tự động ngắt Section Break sang 01 trang A4 Xoay Ngang (`29.7 x 21.0 cm`) riêng biệt để nhúng ảnh 300 DPI, sau đó tự động trả về khổ A4 Dọc (`21.0 x 29.7 cm`).

---

## 5. Quy tắc Trình bày Bảng biểu In ấn Tự nhiên (Natural Print Palette — Điều 12b AGENTS.md)
- **ZERO WHITE TEXT LOCK**: Tuyệt đối không dùng chữ màu trắng trong bất kỳ bảng biểu Word (`.docx`), bảng tính Excel (`.xlsx`) hay nhãn biểu đồ nào.
- **Header Bảng**: Nền Xanh Đá Phiến Sương Nhạt (`#DCE4EC`) hoặc Đá Vôi Sáng (`#EAE6DF`), chữ đậm Xanh Thép Trầm (`#1E3246`).
- **Dòng dữ liệu**: Chữ Mực Than Chì (`#1C1E21`), nền xen kẽ Trắng và Ngà Giấy Tự Nhiên (`#F8F7F4`).
- **Dòng Tổng kết**: Chữ đậm `#1E3246`, nền Xám Khoáng Ấm (`#F2EFE9`) hoặc Xô Thơm Nhạt (`#EBF3ED`).
