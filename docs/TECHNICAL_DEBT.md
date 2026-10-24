# SỔ ĐĂNG KÝ NỢ KỸ THUẬT HỆ THỐNG (SYSTEM TECHNICAL DEBT REGISTER)
## HỆ THỐNG AGENTIC ĐIỀU PHỐI & TÍNH TOÁN KẾT CẤU `.AGENTS`

> **Phiên bản:** v1.0.0 — Post Sprint 1 & 2 Release  
> **Cập nhật ngày:** 2026-10-18  
> **Phạm vi quản lý:** Toàn bộ hệ sinh thái `.agents/` (13 skills, 95 calculators, Policy Engine, Handoff Infrastructure)  
> **Mục tiêu:** Định lượng, phân loại, đánh giá rủi ro và xác định lộ trình xử lý nợ kỹ thuật (technical debt) sau các đợt phát triển để bảo đảm tính ổn định, mở rộng và sẵn sàng cho môi trường doanh nghiệp.

---

## 1. MA TRẬN TỔNG QUAN NỢ KỸ THUẬT (TECHNICAL DEBT MATRIX)

```mermaid
quadrantChart
    title Ma trận Nợ Kỹ thuật & Mức độ Ưu tiên
    x-axis Độ phức tạp Thực hiện (Thấp --> Cao)
    y-axis Mức độ Ảnh hưởng Nghiệp vụ (Thấp --> Cao)
    quadrant-1 Ưu tiên Cao nhất (Sprint 3)
    quadrant-2 Kế hoạch Trung hạn (Sprint 4)
    quadrant-3 Cải tiến Nhỏ (Continuous)
    quadrant-4 Triển khai Nhanh (Quick Wins)
    "TD-03: Hoàn thiện 3 Skills Placeholder": [0.40, 0.88]
    "TD-02: Parser IFC/BIM Trực tiếp": [0.65, 0.85]
    "TD-05: Mở rộng Template SKILL_PHULUC": [0.25, 0.55]
    "TD-07: Mở rộng Coverage 95 Calculators": [0.35, 0.65]
    "TD-01: Concurrency / Message Queue": [0.70, 0.60]
    "TD-04: Module Phi tuyến / P-Delta": [0.80, 0.70]
    "TD-06: ETABS OAPI Direct Sync": [0.85, 0.80]
```

### Bảng Thống kê Phân loại Nợ Kỹ thuật

| Mã Nợ | Lĩnh vực | Tên Hạng mục Nợ Kỹ thuật | Mức độ Nghiêm trọng | Độ Phức tạp | Kế hoạch Xử lý | Trạng thái |
|:---:|:---:|---|:---:|:---:|:---:|:---:|
| **TD-01** | Architecture | Handoff trung gian qua local JSON files (Chưa tối ưu multi-tenant concurrent) | Medium | Trung bình | Sprint 4 | 🟡 Logged |
| **TD-02** | Integration | Parser hồ sơ CAD/BIM phụ thuộc dữ liệu JSON trích xuất trung gian | High | Trung bình | Sprint 3 | 🟢 Resolved (Phase 2) |
| **TD-03** | Coverage | 3 Skills đang ở trạng thái Placeholder (`TEMPWORKS`, `BIM`, `PM`) | High | Thấp - TB | Sprint 3 | 🟢 Resolved (TD-03.A done) |
| **TD-04** | Calculation | Chưa có module giải tích phi tuyến bậc cao (P-Delta) & móng bè đàn hồi | Medium | Cao | Sprint 4 | 🟡 Logged |
| **TD-05** | Delivery | Thiếu template Thuyết minh phụ lục cho bể ngầm, cầu thang bộ, móng băng | Low | Thấp | Sprint 3 | 🟢 Resolved (Phase 1) |
| **TD-06** | Integration | Chưa có module kết nối trực tiếp OAPI hai chiều với ETABS/SAFE | Medium | Cao | Roadmap 2027 | 🔵 Partial (etabs_com_reader v1 done) |
| **TD-07** | Quality Assurance | Độ phủ Unit Test tự động mới bao quát 23/95 calculator scripts | Medium | Thấp - TB | Sprint 3 | 🔵 In Progress (Phase 2: +61 tests) |

---

## 2. CHI TIẾT TỪNG KHOẢN NỢ KỸ THUẬT

### TD-01: Giao tiếp Handoff Trung gian qua Local JSON Files
- **Mô tả hiện trạng:**  
  Các Skill trao đổi dữ liệu thông qua cơ chế ghi/đọc file JSON vật lý trong thư mục `_SHARED/SHARED_CONTEXT/_active/`.
- **Rủi ro & Tác động:**  
  - Trong môi trường đơn người dùng (local pair programming CLI): Hệ thống hoạt động hoàn hảo và ổn định.  
  - Trong môi trường nhiều người dùng (multi-tenant / concurrent cloud API): Tiềm ẩn nguy cơ xung đột ghi file (file write lock conflict), race conditions và nghẽn I/O ổ đĩa.
- **Giải pháp mục tiêu:**  
  1. Xây dựng lớp trừu tượng `ContextStore` (Interface).  
  2. Triển khai backend lưu trữ kép: Local File Storage (mặc định) và Redis / In-Memory Buffer (cho API deployment).  
  3. Thêm cơ chế file locking (filelock) an toàn khi chạy đa tiến trình.
- **Dự kiến thời gian xử lý:** Sprint 4 (Tuần 3–4 Tháng 11/2026).

---

### TD-02: Bộ nạp Dữ liệu Bản vẽ (CAD/BIM) Phụ thuộc File JSON Trung gian
- **Mô tả hiện trạng:**  
  Hàm `parse_drawing_metadata` trong `ingest_project_docs.py` hiện đọc cấu trúc hình học và siêu dữ liệu bản vẽ từ file JSON đã được trích xuất từ trước bằng plugin CAD/Revit.
- **Rủi ro & Tác động:**  
  Kỹ sư phải thực hiện bước xuất trung gian thủ công từ AutoCAD / Revit ra file JSON trước khi có thể chạy kiểm tra xung đột chéo 8 luật (`CDC-01` đến `CDC-08`).
- **Giải pháp mục tiêu:**  
  1. Tích hợp thư viện mã nguồn mở `ifcopenshell` để đọc trực tiếp file mô hình `.ifc`.  
  2. Tích hợp parser định dạng `.dxf` / text table từ CAD để đọc trực tiếp danh mục dầm, cột, cao độ mà không cần file JSON đệm.
- **Dự kiến thời gian xử lý:** Sprint 3 (Mục tiêu hoàn thành trong 1 tuần tới).

---

### TD-03: Hoàn thiện 3 Skills Placeholder lên Trạng thái Production (🟢)
- **Mô tả hiện trạng:**  
  Hiện tại hệ sinh thái có 10 skills Production và 3 skills Placeholder:
  - `SKILL_TEMPWORKS` (v0.2.0): Mới có `calc_formwork_slab.py`, thiếu tính toán cốp pha cột, cốp pha vách và hệ giằng chống giáo nêm/ringlock.
  - `SKILL_BIM_COORDINATION` (v0.5.0): Chưa có engine tính ma trận va chạm (clash matrix) tự động.
  - `Project_Manager` (v0.5.0): Chưa hoàn thiện module tự động cập nhật tiến độ từ RFI/NCR.
- **Rủi ro & Tác động:**  
  Khi người dùng gọi các yêu cầu chuyên sâu về biện pháp thi công vách hầm hoặc clash detection trực tiếp, hệ thống phải fallback hoặc chưa cung cấp đầy đủ calculation logs.
- **Giải pháp mục tiêu:**  
  1. **Sprint 3:** Triển khai `calc_formwork_column.py`, `calc_formwork_wall.py` và `calc_shoring_system.py` cho `SKILL_TEMPWORKS`, nâng cấp lên v1.0.0 Production.  
  2. **Sprint 3:** Triển khai `clash_matrix_checker.py` cho `SKILL_BIM_COORDINATION`.  
  3. **Sprint 4:** Hoàn thiện `Project_Manager` v1.0.0.
- **Dự kiến thời gian xử lý:** Sprint 3 & Sprint 4.

---

### TD-04: Thiếu Module Giải tích Phi tuyến Bậc cao & Móng Bè Đàn hồi
- **Mô tả hiện trạng:**  
  95 scripts tính toán hiện tại giải quyết xuất sắc các bài toán kiểm tra độ bền, ổn định và biến dạng của cấu kiện riêng rẽ (dầm, cột, móng đơn, móng cọc đài thấp, vách phẳng, liên kết thép, neo nối thép).
- **Rủi ro & Tác động:**  
  Khi gặp các công trình cao tầng có chuyển vị lớn cần xét hiệu ứng $P-\Delta$, hoặc công trình có tầng hầm sâu dùng móng bè cọc (piled raft) trên nền đàn hồi tương tác đất - cọc - móng phức tạp, hệ thống vẫn phải dựa vào kết quả giải nội lực của ETABS/SAFE mà chưa tự giải độc lập để đối chiếu.
- **Giải pháp mục tiêu:**  
  Xây dựng module `calc_p_delta_effects.py` theo TCVN 5574:2018 Phụ lục D và `calc_raft_springs.py` tính toán hệ số nền Winkler/Pasternak từ thông số địa chất của `SKILL_GEOTECH`.
- **Dự kiến thời gian xử lý:** Sprint 4.

---

### TD-05: Mở rộng Thư viện Template Thuyết minh Tính toán (SKILL_PHULUC)
- **Mô tả hiện trạng:**  
  `SKILL_PHULUC` và `generator_full.py` hiện sở hữu 3 template chính: `TMTT_FULL.md`, `PARTIAL_BE_TONG.md`, `PARTIAL_THEP.md` tập trung vào dầm, cột, sàn, móng cọc và cừ larsen.
- **Rủi ro & Tác động:**  
  Khi hồ sơ thiết kế đòi hỏi thuyết minh chi tiết cho các cấu kiện phụ trợ phổ biến (cầu thang bộ BTCT 2 vế/3 vế, bể nước ngầm, bể phốt, móng băng), hệ thống phải ghép nội dung thủ công thay vì sinh tự động bằng template chuẩn hóa.
- **Giải pháp mục tiêu:**  
  Bổ sung 4 templates mới vào `SKILL_PHULUC/templates/`:
  - `PARTIAL_STAIRCASE.md` (Tính toán bản thang, dầm thang).
  - `PARTIAL_WATER_TANK.md` (Tính toán thành bể, đáy bể, nắp bể chịu áp lực nước & đất).
  - `PARTIAL_STRIP_FOOTING.md` (Tính toán móng băng dưới tường/cột).
  - `PARTIAL_RETAINING_WALL.md` (Tính toán tường chắn đất trọng lực / BTCT).
- **Dự kiến thời gian xử lý:** Sprint 3.

---

### TD-06: Chưa có Giao thức Kết nối Trực tiếp OAPI Hai chiều với ETABS/SAFE
- **Mô tả hiện trạng:**  
  Dữ liệu nội lực và chuyển vị từ ETABS hiện được nạp qua file xuất bảng text/Excel/JSON.
- **Rủi ro & Tác động:**  
  Quy trình thẩm tra hoặc thiết kế tối ưu tiết diện (Value Engineering) vẫn đòi hỏi kỹ sư mở ETABS, bấm xuất bảng và lưu file vào thư mục dự án.
- **Giải pháp mục tiêu:**  
  Xây dựng bridge script `etabs_oapi_bridge.py` kết nối trực tiếp với tiến trình ETABS đang mở trên Windows qua COM Interface:
  - Tự động trích xuất nội lực bao ($M_{max}$, $N_{tuong\_ung}$, $V_{max}$) của toàn bộ story.
  - Tự động cập nhật lại kích thước tiết diện dầm/cột tối ưu vào ETABS model.
- **Dự kiến thời gian xử lý:** Roadmap 2027 (Enterprise Integration).

---

### TD-07: Tăng cường Độ phủ Unit Test Tự động cho Toàn bộ 95 Calculators
- **Mô tả hiện trạng:**  
  Hiện tại bộ kiểm thử hồi quy tự động trong `run_all_tests.py` tích hợp:
  - Suite 2 (`test_runner.py`): 13 core calculators.
  - Suite 6 (`Design_Evaluation/.../run_tests.py`): 10 DE calculators.
  - Tổng số calculator có regression suite tự động riêng là 23/95 scripts. Các script còn lại được kiểm tra gián tiếp qua Integration Test (Suite 1) hoặc test độc lập từng skill.
- **Rủi ro & Tác động:**  
  Tiềm ẩn nguy cơ khi refactor hoặc cập nhật tiêu chuẩn mới cho các calculator ít dùng (VD: liên kết thép đặc thù, lún cố kết dài hạn ĐCCT), lỗi có thể không bị bắt ngay lập tức tại `run_all_tests.py`.
- **Giải pháp mục tiêu:**  
  Mở rộng `test_runner.py` quét tự động và chạy smoke test + value assertion cho toàn bộ 95/95 scripts tính toán với test vectors chuẩn.
- **Dự kiến thời gian xử lý:** Sprint 3 (Ưu tiên cùng đợt phát triển).

---

## 3. LỘ TRÌNH THỰC THI & PHÂN BỔ TRÁCH NHIỆM (ACTIONABLE SPRINT PLAN)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 3 (Dự kiến: 24/10 - 07/11/2026) — TẬP TRUNG GIẢI QUYẾT NỢ ƯU TIÊN CAO│
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. [TD-03] Hoàn thiện SKILL_TEMPWORKS v1.0 (Cột, Vách, Cây chống)            │
│ 2. [TD-02] Tích hợp Parser IFC trực tiếp qua ifcopenshell                   │
│ 3. [TD-05] Thêm 4 Templates SKILL_PHULUC (Cầu thang, Bể ngầm, Móng băng)   │
│ 4. [TD-07] Mở rộng Unit Test Coverage từ 23 lên 95/95 Calculators          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 4 (Dự kiến: 10/11 - 24/11/2026) — NÂNG CAO KIẾN TRÚC & PHI TUYẾN     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. [TD-01] Nâng cấp ContextStore hỗ trợ Concurrent Lock & In-Memory Redis    │
│ 2. [TD-03] Hoàn thiện SKILL_BIM_COORDINATION v1.0 & Project_Manager v1.0    │
│ 3. [TD-04] Triển khai Module P-Delta & Móng Bè trên nền đàn hồi             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROADMAP 2027 — TÍCH HỢP DOANH NGHIỆP TẬP ĐOÀN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. [TD-06] Giao thức ETABS / SAFE OAPI Two-Way Automation                    │
│ 2. Đóng gói Container Docker Multi-Tenant Enterprise Backend                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. QUY TRÌNH QUẢN TRỊ NỢ KỸ THUẬT (GOVERNANCE POLICY)

1. **Nguyên tắc "Debt Ceiling" (Trần Nợ Kỹ thuật):**
   - Không được phép có quá 2 nợ kỹ thuật mức **High** tồn tại quá 2 Sprints.
   - Mọi nợ kỹ thuật mới phát sinh trong quá trình phát triển tính năng mới bắt buộc phải được ghi nhận vào tài liệu này trong vòng 24 giờ kể từ khi nghiệm thu tính năng.
2. **Review Gate & Tiêu chí Đóng Nợ (Debt Retirement Criteria):**
   - Một khoản nợ chỉ được chuyển trạng thái sang `🟢 Resolved` khi:
     + Mã nguồn đã được implement và có unit test tương ứng trong `run_all_tests.py`.
     + Đạt 100% PASS trong bộ kiểm tra hồi quy.
     + Tài liệu hướng dẫn sử dụng và changelog liên quan đã được cập nhật đồng bộ.

---

*Tài liệu được phê chuẩn bởi Hội đồng Kỹ thuật & Công nghệ Hệ thống `.agents`.*
