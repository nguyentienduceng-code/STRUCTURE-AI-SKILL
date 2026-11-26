# BÁO CÁO PHÂN TÍCH & MA TRẬN XẾP HẠNG MỤC CÁC MCP THAM KHẢO LƯU TRỮ (_REFERENCES_ARCHIVED)

> **Vị trí lưu trữ gốc:** `g:\My Drive\Google AI Studio\.agents\_references_archived\`  
> **Trạng thái lưu trữ:** Nén dạng 7 file `.zip` (2.969 files con) nhằm tối ưu I/O, chống nghẽn đường truyền đồng bộ Google Drive.  
> **Mục đích:** Phân loại chuyên sâu các MCP & thư viện nền tảng, định vị chính xác vai trò trong 4 Trụ cột Kỹ năng của hệ thống và lập lộ trình tái sử dụng không gây phình ngữ cảnh.

---

## 1. BẢNG MA TRẬN ĐỐI CHIẾU & XẾP HẠNG MỤC HỆ THỐNG

| Tên Gói Zip / Tài nguyên | Dung lượng & Số File | Công nghệ & Nguồn gốc | Xếp vào Trụ cột & Skill của Hệ thống | Vai trò Kỹ thuật & Giá trị Tái sử dụng |
|---|---|---|---|---|
| **`horizun-revit-mcp.zip`** | 10.1 MB (1.928 files) | C# / Python / Windows Add-in (Revit 2023-2027), Horizun Group | **Trụ cột III:** `SKILL_BIM_COORDINATION` & `Tầng 2C (Revit Pilot)` | **Kho công cụ BIM đồ sộ nhất (125 tools, 481 subops):** Bóc khối lượng, kiểm toán mô hình, CAD-to-BIM, rehearsal & post-commit verification. Cung cấp schema chuẩn cho Tầng 2C Read-Only. |
| **`rvt-mcp.zip`** | 1.94 MB (663 files) | C# .NET / TypeScript MCP Gateway (Revit 2022-2027), Bimwright | **Trụ cột III:** `SKILL_BIM_COORDINATION` & `Technical_Illustrator` | **Cổng kết nối MCP gọn nhẹ cho Revit (237 tools):** Đã có sẵn tài liệu Tiếng Việt (`README.vi.md`). Cung cấp cơ chế truy vấn tham số hình học (Query Parameters/Geometry) nhanh. |
| **`agent-circuit-breaker.zip`** | 377 KB (218 files) | Python, Local-first AI Safety, Sagar Chhatrala | **Trụ cột IV & Hệ thống:** `Global_Dispatcher` & `Claude Code Hooks` | **Chốt chặn an toàn tự động (Circuit Breaker):** Cơ chế `ALLOW`, `BLOCK`, `PENDING_APPROVAL` kiểm soát tool call rủi ro cao. Đây chính là xương sống để cài đặt Hook bảo vệ file DWG và cưỡng chế Review Gate Điều 3! |
| **`rule-engine.zip`** | 333 KB (89 files) | Python Expression Grammar, zeroSteiner | **Trụ cột IV & II:** `SKILL_VERIFY` & `SKILL_RFI` | **Bộ máy đánh giá quy tắc (Rule Engine):** Đánh giá chuỗi biểu thức logic phức tạp, dùng để phân loại mức độ nghiêm trọng NCR (Critical/Major/Minor) và kiểm tra ngưỡng an toàn eta. |
| **`pyconcrete.zip`** | 57 KB (51 files) | Python RC Detailing, Ebrahim Raeyat | **Trụ cột I & III:** `Structural_Design_Engineer` & `Technical_Illustrator` | **Thuật toán sinh hình học cốt thép BTCT:** Vẽ và bố trí cốt đai, cốt dọc, neo uốn dầm cột bê tông cốt thép, bổ trợ trực tiếp cho module vẽ CAD tham số `cad_plan_engine.py`. |
| **`simple-graph.zip`** | 6.4 KB (19 files) | SQLite Graph Database & CTE Path Traversal | **Trụ cột IV & I:** `SKILL_VERIFY` & `Design_Evaluation (Module 3)` | **Mô hình đồ thị quan hệ nút khung:** Biểu diễn sơ đồ truyền lực công trình (Dầm phụ -> Dầm chính -> Cột -> Móng) dưới dạng Nodes/Edges SQLite, phục vụ kiểm toán đường truyền lực tự động. |
| **`verdict-rules.zip`** | 985 B (1 file) | JSON Eval Benchmark | **Trụ cột IV:** `SKILL_VERIFY` | **Bộ test-case mẫu kiểm thử quy tắc phán quyết:** Tham khảo phương pháp viết Eval đánh giá độ chính xác của AI. |

---

## 2. PHÂN TÍCH CHI TIẾT THEO 3 CỤM NĂNG LỰC

### Cụm 1: Hạ tầng BIM & Revit MCP Gateway (`horizun-revit-mcp` + `rvt-mcp`)
- **Hiện trạng hệ thống ta:** Ta vừa hoàn thành Tầng 2A (Mapper tham số Revit và chuyển dịch mô hình BIM sang cấu trúc dữ liệu phẳng) và Tầng 2B (AutoCAD 2021 Core Console Snapshot & Visual Diff an toàn chỉ-đọc).
- **Hạng mục xếp vào:** **Trụ cột III — CAD Tham số & BIM Coordination**.
- **Giá trị khai thác:**
  - `horizun-revit-mcp` sở hữu kiến trúc giao dịch rất chặt chẽ: `Rehearsal` (thử nghiệm trước khi ghi) và `Post-commit verification` (kiểm chứng sau khi áp dụng). Khi ta mở rộng sang **Tầng 2C (Revit Read-Only Pilot)**, ta hoàn toàn kế thừa schema parameter của 2 bộ MCP này mà không cần tự phát minh lại bánh xe.
  - `rvt-mcp` có bản dịch Tiếng Việt và cấu trúc server gọn, là tài liệu đối chiếu tuyệt vời cho cộng đồng kỹ sư BIM tại Việt Nam.

### Cụm 2: Cơ chế An toàn Tự động & Chốt Chặn Lệnh (`agent-circuit-breaker` + `rule-engine`)
- **Hiện trạng hệ thống ta:** Các quy tắc tối thượng trong `AGENTS.md` (Điều 3 Review Gate, Điều 12b cấm chữ trắng, cấm sửa file DWG dự án gốc) hiện vẫn dựa trên năng lực prompt compliance của AI.
- **Hạng mục xếp vào:** **Trụ cột IV — Kiểm chứng & Điều phối AI** kết hợp trực tiếp với **Nhóm 1 Hooks của Claude Code**.
- **Giá trị khai thác:**
  - Logic cốt lõi của `agent-circuit-breaker` với 5 trạng thái phán quyết:
    ```
    Action -> [Circuit Breaker Evaluator] -> ALLOW (Thực thi)
                                          -> BLOCK (Chặn ngay, VD: ghi đè file .dwg)
                                          -> PENDING_APPROVAL (Dừng lại hỏi Review Gate)
    ```
  - Thay vì chỉ dựa vào AI tự nhắc, ta đóng gói logic này thành một script Python gọn nhẹ làm **PostToolUse / PreToolUse Hook** trong `.claude/settings.json`, biến toàn bộ quy tắc `AGENTS.md` thành rào chắn cơ học không thể bị vi phạm.

### Cụm 3: Đồ họa Kết cấu & Đồ thị Đường truyền lực (`pyconcrete` + `simple-graph`)
- **Hiện trạng hệ thống ta:** Ta đang sở hữu `cad_plan_engine.py` (vẽ mặt bằng dầm sàn, lưới trục) và 122 script tính toán tất định.
- **Hạng mục xếp vào:** **Trụ cột I (Thiết kế Kết cấu)** và **Trụ cột III (CAD DCE Pro)**.
- **Giá trị khai thác:**
  - `pyconcrete` cung cấp giải thuật toán học tính tọa độ uốn móc đai 135 độ, khoảng cách rải thép theo vùng dẻo (h/4, 2h) theo tiêu chuẩn hình học.
  - `simple-graph` giải bài toán đường truyền lực bằng SQLite CTE (truy vấn đệ quy cây kết cấu). Khi người dùng hỏi: *"Nếu dầm D1 bị gãy, những dầm và sàn nào sụp đổ theo?"*, truy vấn đồ thị này sẽ trả lời chính xác trong 0.01 giây mà không cần quét toàn bộ mô hình!

---

## 3. PHƯƠNG ÁN QUẢN LÝ VẬT LÝ & LỘ TRÌNH KHAI THÁC

1. **Giữ nguyên trạng thái nén `.zip` tại `_references_archived/`:**
   - Tuyệt đối **không giải nén đồng loạt** vào workspace để tránh tạo ra gần 3.000 file I/O làm nghẽn đồng bộ Google Drive.
2. **Khai thác chọn lọc theo nhu cầu (On-Demand Extraction):**
   - Khi triển khai **Bộ Hooks an toàn (Nhóm 1 đề xuất)**: chỉ trích xuất module `rules` từ `agent-circuit-breaker.zip`.
   - Khi chuẩn bị **Tầng 2C (Revit Read-Only Pilot)**: chỉ trích xuất tệp manifest và contract API từ `horizun-revit-mcp.zip`.
3. **Đồng bộ vào Hồ sơ Tri thức Cộng đồng:**
   - Bản báo cáo phân tích này đã được lưu vào thư mục Showcase và thư mục Tham chiếu để kỹ sư trong team có thể tra cứu nhanh bất cứ lúc nào.

---
© 2026 Vietnam Civil & Structural AI Engineering Team.
