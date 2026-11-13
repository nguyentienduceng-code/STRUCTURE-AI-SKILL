# HỆ THỐNG BỘ NHỚ TRUNG TÂM (CENTRAL AGENT MEMORY)
## HỆ ĐIỀU HÀNH KỸ SƯ KẾT CẤU & QUẢN TRỊ DỰ ÁN CẤP ENTERPRISE

> **Không gian làm việc:** `G:\My Drive\Google AI Studio`  
> **Cơ chế tương tác:** Song hành Đa Tác Nhân (Dual-Agent Collaboration): **Gemini Antigravity** & **Claude Code**  
> **Kênh đồng bộ bus:** `memory/DUAL_AGENT_BUS.json` | **Giao ban:** `memory/DUAL_AGENT_HANDOFF_MEMO.md`  
> **Kho mã nguồn & Lưu trữ Git Upstream:** [`STRUCTURE-AI-SKILL` (GitHub)](https://github.com/nguyentienduceng-code/STRUCTURE-AI-SKILL)  
> **Phiên bản hệ sinh thái:** v7.3 (Unified Master Architecture)  
> **Cập nhật ngày:** 06/11/2026

---

## 1. QUY HOẠCH CẤU TRÚC THƯ MỤC KHÔNG GIAN LÀM VIỆC (WORKSPACE ARCHITECTURE)

```text
G:\My Drive\Google AI Studio\
├── 00_Management_QLTK/             ◄── TRUNG TÂM ĐIỀU HÀNH PMO (5 PHÂN HỆ QUẢN TRỊ)
│   ├── 01_Tien_Do_&_PendingList/   (Master Tracking, Gantt MS Project, Archive tuần cũ)
│   ├── 02_Ke_Hoach_San_Xuat_&_KPI/ (Kế hoạch sản xuất tháng, KPI cá nhân & phòng ban, Scripts)
│   ├── 03_Hop_Dong_&_Bao_Gia/      (HĐ tư vấn MontAlp, Báo giá TVTK, Nghiệm thu thanh toán)
│   ├── 04_Bien_Ban_Hop_MOM/        (Biên bản họp Space Ship One, Studio GA...)
│   └── 05_Giao_Nhan_Ho_So_&_Van_Ban/ (BBBG hồ sơ SS1, RFI/NCR, Bảng vật liệu mẫu)
│
├── 00_Template_&_Standards/        ◄── KHO TÀI LIỆU GỐC & GIÁO TRÌNH (978 MB)
│   ├── Tieu_Chuan_TCVN/           (Kho PDF chuẩn duy nhất: TCVN, Eurocode, AISC...)
│   ├── Chuyen_De_BPTC/            (Hồ sơ biện pháp thi công mẫu)
│   ├── Chuyen_De_Coppha/          (Chuyên đề tính toán ván khuôn, cây chống shoring)
│   └── Sach_Giao_Trinh/           (Giáo trình kết cấu thép, bê tông, nền móng)
│
├── 01_Projects/                    ◄── 14 DỰ ÁN KỸ THUẬT XÂY DỰNG ĐÃ ĐÁNH SỐ THỨ TỰ
│   ├── 00_Management_QLTK/        (Liên kết PMO Hub)
│   ├── 01_MONTALP/                (Dự án trọng điểm #1 — Căn hộ cao cấp & Sales Gallery)
│   ├── 02_SS1/                    (Dự án trọng điểm #2 — Space Ship One)
│   ├── 03_TAN_HY/                 (Cụm nhà xưởng CN3–CN6 Tân Hỷ — Đã đổi từ BAO GIA)
│   ├── 04_LEEMAN_TREE/            (Dự án Leeman Tree)
│   ├── 05_NHA_AN_HITECH/          (Dự án Nhà An Hitech)
│   ├── 06_HO_YEN_QUANG/           (Dự án Hồ Yên Quang)
│   ├── 07_IHOME/                  (Khu nhà ở / Chung cư iHome)
│   ├── 08_NHA_PHO_Q2/             (Nhà phố liền kề Quận 2)
│   ├── 09_48-52_HA_LONG_VUNG_TAU/ (Khách sạn Hạ Long Vũng Tàu)
│   ├── 10_FREELANCER_Sale_Gallery/(Khu Sales Gallery)
│   ├── 11_PRIME_DIAMOND/          (Dự án Prime Diamond)
│   ├── 12_MINH_CHAU/              (Công trình Minh Châu)
│   ├── 13_NHA_BAN_NGUYEN/         (Nhà ở Bản Nguyên)
│   ├── 14_NHA_THEP_BMT/           (Kết cấu thép BMT)
│   └── 99_Archived/               (Thư mục lưu trữ dự án đóng)
│
├── 02_Web_Applications/            ◄── ỨNG DỤNG WEB (Structure-Hub, Market Dashboard...)
├── .agents/                        ◄── HỆ ĐIỀU HÀNH AGENTIC (Git Remote: nguyentienduceng-code/STRUCTURE-AI-SKILL)
├── memory/                         ◄── BỘ NHỚ LIÊN TÁC NHÂN (BUS & ACTIVE HANDOFF)
│   ├── DUAL_AGENT_BUS.json        (Trạng thái Bus thời gian thực)
│   ├── DUAL_AGENT_HANDOFF_MEMO.md (Biên bản bàn giao ca trực hiện hành)
│   ├── MEMORY.md                  (File này — Quy tắc & Ký ức toàn hệ thống)
│   └── archive/                   (Lưu trữ toàn bộ các file bus và memo lịch sử cũ)
└── scratch/                        ◄── THƯ MỤC NHÁP TẠM THỜI (Tự động dọn dẹp hàng tuần)
```

---

## 2. NGUYÊN TẮC QUẢN TRỊ & KỸ THUẬT BẮT BUỘC (HARD RULES)

Mọi tác tử AI (Gemini / Claude / Subagents) khi hoạt động trong không gian này **BẮT BUỘC** tuân thủ:

1. **Deterministic First (Cấm Nhẩm Tay):**
   - Tuyệt đối không tự suy diễn số liệu kỹ thuật. 100% phép tính phải gọi qua Python scripts trong `calculators/` và trả về trường JSON `Calculation_Logs`.
2. **Zero White Text Lock (Điều 12b AGENTS.md):**
   - Tuyệt đối cấm gán chữ màu trắng (`#FFFFFF` hoặc `RGBColor(255,255,255)`) trong mọi bảng biểu Word (`.docx`) và Excel (`.xlsx`).
   - Bắt buộc dùng **Natural Print Palette v4.4**: Nền sáng `#DCE4EC`, `#EAE6DF` đi cùng chữ tối `#1E3246`, `#1C1E21`.
3. **Excel Sanity & Anti-[Repaired] (v2.1):**
   - Trước khi `wb.save()`, bắt buộc chạy `sanitize_workbook()`.
   - Cấm emoji trò chuyện (`🟢`, `🔴`, `🚨`) trong dữ liệu bảng tính. Khóa in Landscape `fitToWidth = 1`.
4. **PMO MS Project Gantt Engine (v1.1.0):**
   - Biểu đồ tiến độ xuất dạng Split View 8 cột, đường găng CPM đỏ, stepped dependency arrows, tự động ngắt Section Break sang khổ A4 Landscape 300 DPI trong Word.
5. **Tiêu Chuẩn Locked (21 Tiêu chuẩn Hiện hành):**
   - Tải trọng: **TCVN 2737:2023** | Thép: **TCVN 5575:2024** | BTCT: **TCVN 5574:2018** | Động đất: **TCVN 9386:2025**.
   - Phân cấp công trình: **Thông tư 34/2026/TT-BXD** & **QCVN 03:2022/BXD** | An toàn cháy: **QCVN 06:2022/BXD**.
6. **Review Gate (Cổng Kiểm Duyệt An Toàn):**
   - Chỉ xuất file chính thức sau khi in tóm tắt chỉ số sử dụng $\eta$, số liệu chốt và được User xác nhận rõ ràng.

---

## 3. GIAO THỨC ĐỒNG BỘ DUAL-AGENT & PHÂN VIỆC LINH HOẠT THEO DỰ ÁN (v3.0 - ENTERPRISE AUTONOMOUS)

1. **Nguyên tắc Phân việc Linh hoạt Theo Mục đích Dự án (Dynamic Project-Driven Role Allocation):**
   - **Tuyệt đối KHÔNG cố định vai trò cho Gemini hay Claude:** Vai trò và trách nhiệm giữa hai hệ Modal được điều chỉnh linh hoạt dựa trên mục tiêu, tính chất kỹ thuật và tiến độ của từng dự án cụ thể.
   - Tùy theo dự án, bất kỳ Agent nào cũng có thể đóng vai trò Kỹ sư Thiết kế chính, Kỹ sư Thẩm tra phản biện, Kỹ sư Lập tiến độ PMO, Kỹ sư Định giá chi phí, hoặc Kỹ sư Kiểm toán mã nguồn & Thuật toán.
   - Khi bàn giao, trường `role_distribution` trong `project_context` ghi rõ sự phân công cụ thể cho dự án đó.

2. **Cờ Trạng thái Vòng đời Ca trực & Chống Lệch nhịp (State Machine & Software Mutex):**
   - **4 Trạng thái chuẩn:** `PENDING` (chờ nhận việc), `IN_PROGRESS` (đang thực thi), `COMPLETED` (đã xong tiêu chí), `NEED_REVIEW` (chờ phê duyệt/kiểm tra chéo).
   - **Quy tắc Khóa Thi hành (Lock on Working):** Khi tác tử đối tác (ví dụ Claude) đang chạy lệnh và bus có `handoff_status: "IN_PROGRESS"`, tác tử còn lại (Gemini) **BẮT BUỘC KHÔNG ĐƯỢC GHI ĐÈ BUS HOẶC THAY ĐỔI CÁC FILE TRỌNG TÂM DANG DỞ**.
   - **Lệnh tiếp nhận / hoàn thành:**
     - Bắt đầu ca: `python .agents/tools/sync_bus.py --claim --agent <TÊN_AGENT>`
     - Kết thúc ca: `python .agents/tools/sync_bus.py --complete --agent <TÊN_AGENT> --summary "..."`
     - Yêu cầu review: `python .agents/tools/sync_bus.py --need-review --agent <TÊN_AGENT>`

3. **Chuẩn hóa Đường dẫn Tương đối (POSIX Relative Paths):**
   - Toàn bộ danh mục `artifacts_modified` và `target_files` bắt buộc dùng **đường dẫn tương đối từ Workspace Root** với ký tự gạch chéo xuôi `/` (ví dụ: `.agents/tools/sync_bus.py`, `memory/DUAL_AGENT_BUS.json`).
   - Cấm dùng đường dẫn tuyệt đối chứa `G:\My Drive\...` hay ký tự `\\` trong JSON bus để tiết kiệm >75% token context window và triệt tiêu lỗi escape string trên Windows.

4. **Cấu trúc Lệnh & Tiêu chí Nghiệm thu (Acceptance Criteria Definition):**
   - Không giao việc bằng câu văn tự nhiên chung chung. Mọi lượt bàn giao phải gồm:
     - `task_description`: Nhiệm vụ kỹ thuật cụ thể.
     - `target_files`: Danh sách tệp tin mục tiêu cần can thiệp.
     - `acceptance_criteria`: Danh sách điều kiện đạt định lượng (Pass/Fail criteria).
   - Tự động sinh danh sách Checklist tương tác (`- [ ]`) tại `memory/DUAL_AGENT_HANDOFF_MEMO.md`.

5. **Phòng ngừa & Xử lý Xung đột Đồng bộ Google Drive (Anti-Conflict Protocol):**
   - File bus được ghi nguyên tử qua file tạm ẩn dạng `.{stem}.tmp.{pid}` và fsync trước khi replace, đồng thời tự dọn dẹp các bản sao xung đột cùng thư mục.
   - Khi phát hiện tệp rác có đuôi `(1)`, `(2)`, sử dụng bộ xử lý thông minh `resolve_gdrive_conflicts` (`--clean-conflicts`): Tự động so sánh hash/mtime; nếu bản `(1)` mới hơn bản gốc, hệ thống sẽ tự động sao lưu bản cũ và nâng cấp bản mới lên làm tệp chính, tuyệt đối không xóa mù quáng gây mất mã nguồn.

---

## 4. HỆ THỐNG KHO LƯU TRỮ MÃ NGUỒN TRUNG TÂM (GIT UPSTREAM REPOSITORY)

- **Kho lưu trữ chính thức (Official Remote):** [`STRUCTURE-AI-SKILL` (GitHub)](https://github.com/nguyentienduceng-code/STRUCTURE-AI-SKILL)
- **Thư mục cục bộ liên kết:** `G:\My Drive\Google AI Studio\.agents`
- **Nhánh vận hành (Default Branch):** `main`
- **Phạm vi lưu trữ:** Toàn bộ hệ sinh thái Agentic (13 Skills chuyên sâu, 111 Calculators kỹ thuật, 17 Test Suites kiểm định, Hệ thống bảo vệ Circuit Breaker & Blackbox Recorder, và Engine Cầu nối Điều phối `sync_bus.py`).
- **Quy tắc Đẩy mã nguồn (Push Protocol):** Bắt buộc chạy toàn bộ bộ kiểm thử Suite #16 đạt 39/39 PASS trước khi đồng bộ hoặc commit lên kho lưu trữ đám mây.
