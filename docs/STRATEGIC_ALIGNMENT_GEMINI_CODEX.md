# BẢN ĐỒNG THUẬN CHIẾN LƯỢC KIẾN TRÚC HỆ SINH THÁI .AGENTS
## CUỘC HỌP THẢO LUẬN ĐỊNH HÌNH DỰ ÁN GIỮA GEMINI VÀ CODEX

> **Thời gian:** 2026-11-14 09:42 (Giờ địa phương)  
> **Chủ trì định hướng:** User / Giám đốc Kỹ thuật  
> **Các bên tham vấn kiến trúc:** 
> - **GEMINI:** Trưởng nhóm Điều phối Hệ thống & Trực quan hóa (System Coordinator & Visual/Review Lead)
> - **CODEX:** Kỹ sư Trưởng Kiến trúc Hệ thống (Chief Systems Architect)
> **Mã hồ sơ:** `STRATEGIC-ALIGNMENT-20261114-V1`

---

## 1. BỐI CẢNH & NGUYÊN NHÂN CẦN BƯỚC ĐỒNG THUẬN NÀY

Trong các phiên làm việc vừa qua, Codex đã thực hiện hai đợt giải phẫu kỹ thuật xuất sắc (Vòng 1 và Vòng 2) mổ xẻ mã nguồn `C:\Dce Pro`, `D:\DCE_MCP_CAD_Revit_Starter_Kit_v5.0` và phân tích sâu các tầng assembly .NET, XData, LISP, SQLite.

Tuy nhiên, trước khi bước vào triển khai các Sprint tiếp theo, **User (Giám đốc Kỹ thuật) đã đưa ra một định hướng chiến lược then chốt mang tính sống còn để định hình toàn bộ dự án**. Nếu hai tác tử không thống nhất triết lý này ngay từ bây giờ, dự án sẽ dễ bị sa đà vào việc "tự viết lại bánh xe lịch sử" một cách lãng phí và kém hiệu quả.

---

## 2. TRIẾT LÝ CỐT LÕI: ĐỊNH VỊ RANH GIỚI GIỮA AI AGENT VÀ PHẦN MỀM CHUYÊN DỤNG

### 2.1 Ranh giới Không thể Thay thế của Phần mềm Chuyên dụng (FEM / Geotech Solvers)
- **Tuyên bố dứt khoát:** Hệ thống AI Agent của chúng ta **KHÔNG BAO GIỜ có mục tiêu thay thế ETABS, SAP2000, SAFE hay Plaxis**.
- **Cơ sở khoa học & thực tiễn:**
  - Các công trình phức tạp (nhà cao tầng, tải trọng gió động, phân tích phổ phản ứng động đất theo TCVN 9386, tầng hầm sâu hố đào Plaxis 2D/3D) đòi hỏi ma trận độ cứng $K \cdot U = F$, tích phân thời gian phi tuyến và mô hình ứng suất hữu hiệu đất nền.
  - Các phần mềm chuyên dụng như ETABS và Plaxis là kết tinh hàng chục năm kiểm chứng cơ học và có giá trị pháp lý tuyệt đối trước các cơ quan Thẩm tra / Bộ Xây dựng. Việc cố gắng dùng AI để "nhẩm" hay viết lại solver FEM phức tạp là phi thực tế và cực kỳ rủi ro.

### 2.2 Sứ mệnh Thực sự của Hệ sinh thái AI Agent (`.agents`)
AI Agent không phải là solver tính kết cấu, mà AI Agent đóng vai trò là **"BỘ NÃO TRỢ LÝ KỸ SƯ CẤP CAO & HỆ THỐNG TỰ ĐỘNG HÓA HẬU KỲ" (Senior Structural Co-Pilot & End-to-End Delivery Engine)**.

Sứ mệnh của Agent tập trung giải quyết triệt để 4 điểm nghẽn mà kỹ sư mất 80% thời gian nhưng lại dễ sai sót nhất:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   4 TRỤ CỘT CHIẾN LƯỢC CỦA AI AGENT                    │
└────────────────────────────────────────────────────────────────────────┘
  [TRỤ CỘT 1] TƯ DUY PHÂN TÍCH SỐ LIỆU & TỐI ƯU HÓA (DATA INTELLIGENCE)
     ├── Kết nối lấy nội lực ETABS / SAP / SAFE qua CSiAPI tự động
     ├── Đánh giá chỉ số sử dụng η (Utilization Ratio) theo TCVN 5574/5575
     └── Vòng lặp khép kín: Tự động phát hiện cấu kiện thiếu tải -> Tăng tiết diện

  [TRỤ CỘT 2] TỰ ĐỘNG HÓA LẬP THUYẾT MINH KỸ THUẬT (CALCULATION SHEETS)
     ├── Tự động lập Thuyết minh chi tiết A4 (.docx) in sẵn nộp cơ quan thẩm tra
     └── Trình bày minh bạch công thức step-by-step theo đúng chuẩn SKILL_PHULUC

  [TRỤ CỘT 3] TỰ ĐỘNG HÓA RA BẢN VẼ KỸ THUẬT (CAD & BIM DETAILING)
     ├── Dàn trang tự động 60 – 70 bản vẽ CAD (.dxf/.dwg) chuẩn A1/A0
     ├── Kế thừa mô hình Semantics First, quản lý 4 tầng kích thước, bảng thống kê thép
     └── Tự động phát hiện va chạm chữ và né chữ (Anti-Collision Engine)

  [TRỤ CỘT 4] KIỂM SOÁT HỒ SƠ, THẨM TRA & KIỂM ĐỊNH ĐỘC LẬP (AUDIT & COMPLIANCE)
     ├── Kiểm tra chéo 4 chiều: Mô hình ETABS ↔ Thuyết minh ↔ Bản vẽ CAD ↔ ĐCCT
     └── Phát hiện sai lệch và tự động phát hành Phiếu RFI / Biên bản NCR chuẩn pháp lý
```

---

## 3. TỔNG HỢP TINH HOA TỪ DBIM & DCE ĐỂ PHỤC VỤ 4 TRỤ CỘT TRÊN

Sau khi đối chiếu tài liệu [tu-dong-hoa-trien-khai-ket-cau-dbim.md] và báo cáo giải phẫu Vòng 2 [DCE_STEEL_AND_INTERACTIVE_CAD_ANATOMY.md], Gemini và Codex thống nhất tiếp thu 5 giải pháp công nghệ sau:

### 1. Mô hình Chuỗi 25 Bước "2-Click" của DBim:
- **Click 1:** Đọc hiểu kiến trúc (nhận diện tầng, công năng phòng ngủ/khách/WC để gán hoạt tải; bóc tách cửa để áp thuật toán giảm tải tường hệ số $0.7$).
- **Click 2:** Chuỗi tự động hóa điều phối giữa ETABS $\rightarrow$ tính thép $\rightarrow$ vẽ CAD $\rightarrow$ xuất thuyết minh.

### 2. Thuật toán Vòng lặp Khép kín Tự Tối ưu (Closed-Loop Optimization):
- **Cột:** Nếu $\eta > 1.0 \rightarrow$ tự tăng cấp kích thước tiết diện $\rightarrow$ update ETABS $\rightarrow$ phân tích lại $\rightarrow$ đạt mới vẽ chi tiết thép cột.
- **Móng cọc:** Nếu đài cọc không đủ sức chịu tải $\rightarrow$ tự tăng số lượng cọc trong đài (từ đài 2 cọc lên 3, 4 cọc) $\rightarrow$ kiểm tra lại đạt mới vẽ đài móng và dằng móng.

### 3. Kiến trúc Bản vẽ "Semantics First" (Ý nghĩa trước, hình học sau):
- Định nghĩa cấu kiện qua `FeatureGraph` (mép dầm, tim cột, lỗ bu lông). Đường DIM neo vào Feature.
- Khi ETABS đổi tiết diện, chỉ cần tính lại tọa độ Feature, đường DIM tự co giãn theo, **không bao giờ xóa đi vẽ lại toàn bộ bản vẽ**.

### 4. Nguyên tắc "Bảo toàn Lớp Tùy chỉnh của Kỹ sư" (User Overrides Layer):
- Tách bạch 3 tầng: Thông số tính toán $\rightarrow$ Hình học AI sinh $\rightarrow$ Tùy chỉnh của người dùng (vị trí dời nhãn, đường dim đã chỉnh tay).
- Khi AI chạy lại nội lực hoặc cập nhật bản vẽ, **bảo toàn 100% các điểm nhãn mà kỹ sư đã dời**, không bao giờ reset đè lên công sức của họ.

### 5. Giao tiếp Event Coalescing chống Lag CAD:
- Lắng nghe AutoCAD qua `CommandEnded`, gom các thay đổi lại rồi mới đồng bộ sang mô hình tính toán, đảm bảo môi trường vẽ của kỹ sư luôn mượt mà.

---

## 4. PHÂN CÔNG PHỐI HỢP DUAL-AGENT TIẾP THEO

| Hạng mục công việc | Tác tử phụ trách chính | Tác tử phối hợp & Thẩm tra |
| :--- | :--- | :--- |
| **Thuật toán Né Chữ CAD (Sprint 2 Anti-Collision)** | **CODEX:** Viết `cad_scene_index.py` & `cad_collision_solver.py` (R-tree spatial) | **GEMINI:** Tích hợp Vision render preview PNG và nghiệm thu Suite 18 |
| **Pipeline 2-Click Tự Động Hóa Hậu Kỳ** | **GEMINI:** Xây dựng luồng điều phối liên skill (Dispatcher $\rightarrow$ ETABS $\rightarrow$ CAD $\rightarrow$ Docx) | **CODEX:** Thiết kế API contracts và cơ chế Event Coalescing |
| **Cầu nối Revit Live Sync (Sprint 3)** | **CODEX:** Tối ưu lõi C# `Revit.Async` + TCP 8080 (Dầm, Vách, Sàn) | **GEMINI:** Kiểm toán mô hình bằng chuẩn buildingSMART IDS 1.0 |
| **Kiểm soát Hồ sơ Thẩm tra & NCR/RFI** | **GEMINI:** Điều phối `SKILL_VERIFY` và `SKILL_RFI` đối chiếu 4 chiều | **CODEX:** Trích xuất ma trận sai lệch từ XData CAD và ETABS model |

---

## 5. KẾT LUẬN ĐỒNG THUẬN

Cả hai tác tử (Gemini & Codex) hoàn toàn nhất trí với định hướng của User:
> **"Không cạnh tranh với ETABS/Plaxis về giải phương trình cơ học phức tạp. Thay vào đó, tập trung biến hệ thống AI Agent thành Công cụ Trợ lý Kỹ thuật số 1 Việt Nam về Tư duy Phân tích Số liệu, Tự động Lập Thuyết minh, Dàn trang Bản vẽ Kỹ thuật và Kiểm soát Thẩm tra Hồ sơ."**

---

## 6. CẬP NHẬT ĐỊNH HƯỚNG CHIẾN LƯỢC 3 TẦNG ĐỘC LẬP (2026-11-22 — v8.0)

Theo chỉ đạo trực tiếp của Giám đốc Kỹ thuật ngày 2026-11-22, toàn bộ kiến trúc phát triển hệ thống `.agents` được tổ chức thành **3 Tầng (Tier) độc lập, cô lập lỗi tuyệt đối** (chi tiết tại [`docs/MASTER_STRATEGY_3_TIERS_V8.md`](./MASTER_STRATEGY_3_TIERS_V8.md)):

1. **Tầng 1 (Trụ cột Cốt lõi — Hoàn thiện & Khóa cứng Trước):**
   - **Pháp lý & Tiêu chuẩn:** `STANDARDS_LOCK v3.3.0`, `StandardsGraph`, kiểm soát dẫn chứng PDF và phân cấp công trình (`TT 34/2026/TT-BXD`, `QCVN 03:2022/BXD`).
   - **Đọc Bản vẽ Thẩm tra & Phụ lục Hồ sơ:** Đọc `.dxf`/`.dwg` (`CAD_DEEP_READER`), trích xuất bảng `EMF` nhúng trong `.docx`, kiểm lỗi công thức Excel, đối chiếu lưới trục — mặt bằng — mặt cắt — tag thép (`SKILL_BIM_COORDINATION` + `SKILL_VERIFY`).
   - **Hệ thống Skills Tính toán Cơ bản & Lập Phụ lục Xác định:** 14 Skills Production (`122` Python scripts) thực thi tính toán có log xác định và xuất Phụ lục thuyết minh (`SKILL_PHULUC`).
   - **Phân tích Tư duy & Hỗ trợ Ra Quyết định cho Chuyên viên TVTT và CĐT/QLTK:** Tách bạch luồng kiểm chứng tiêu chuẩn + hồ sơ khoanh lỗi (TVTT) với luồng tối ưu chi phí VE + Tờ trình + Phiếu RFI/NCR & 4 điều khoản chế tài hợp đồng (CĐT).
2. **Tầng 2 (Mở rộng Kỹ năng Vẽ — 2D CAD & 3D Revit/BIM):** Sinh bản vẽ CAD 2D DCE Pro (`Technical_Illustrator`, 25 cổng `G8.01–G8.25`, `accoreconsole.exe`) và kết nối đọc-chỉ mô hình 3D Revit/IFC (`BIMwright` / `Horizun` read-only pilot, `IfcOpenShell`), cô lập hoàn toàn khỏi nhân Tầng 1.
3. **Tầng 3 (Kết hợp ETABS / SAFE / SAP2000):** Chỉ thực hiện trích xuất nội lực ($M, N, V$, phản lực, chuyển vị) qua bảng xuất hoặc COM OAPI (`tools/etabs_com_reader.py`) truyền chuẩn hóa về Tầng 1 kiểm chứng.


