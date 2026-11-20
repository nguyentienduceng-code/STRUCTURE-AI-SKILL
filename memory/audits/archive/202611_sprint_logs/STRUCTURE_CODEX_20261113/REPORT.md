# Kiểm toán độc lập sau tái cấu trúc Agent Structure

Thời điểm: 2026-11-13T22:18:23.657716+07:00 — người kiểm tra: CODEX.

**Kết luận: NEED_REVIEW. 27/27 suites PASS nhưng chưa đạt toàn bộ tiêu chí bàn giao.**

## Phạm vi và phương pháp

Đã nhận ca từ `.agents/memory/DUAL_AGENT_BUS.json` qua bridge với workspace chỉ định rõ. Đọc tiêu chí, kiểm 14 skill entry points, parse 222 file Python production, đối chiếu ba bản AGENTS.md, kiểm ZIP, chạy registry validator và thử quyền sở hữu trên bus tạm. Không sửa mã production trong lượt rà soát. SHA-256 của toàn bộ 222 nguồn được kiểm lại trước khi xuất báo cáo.
Kiểm tra cấu trúc không thay thế kiểm thử mọi đường thực thi, thiết kế kết cấu hoặc integration với phần mềm có giấy phép. Không có manifest nguồn trước khi nén để chứng minh đủ 3.739 tệp; CRC của ZIP còn đọc được chỉ xác nhận nội dung hiện có, không chứng minh archive đầy đủ.

## Các phát hiện cần xử lý

### P1 — F01: Archive rvt-mcp.zip không hợp lệ

Vị trí: `.agents/_references_archived/rvt-mcp.zip`.

1,877,086 bytes; hai lần đọc cùng SHA-256 b135a0190e40c3b7936f3c3ec93c42f4037035d72b6f5f1333abcd52a60ce073; không có EOCD; zipfile.BadZipFile.

Ảnh hưởng: Không thể xác nhận phục hồi toàn bộ thư viện đã nén hoặc xác minh con số 3.739 tệp.

Khuyến nghị: Khôi phục từ nguồn/backup tin cậy, tạo ZIP mới, kiểm CRC và manifest từng tệp trước khi thay thế bản hiện tại.

### P1 — F02: Nhận ca có thể ghi đè tác tử đang giữ ca

Vị trí: `.agents/tools/sync_bus.py:732 và bản sao trong skill bridge`.

Bus thử nghiệm tách biệt đang IN_PROGRESS/CODEX; claim_task(GEMINI) thành công và đổi holder thành GEMINI.

Ảnh hưởng: FileLock bảo vệ thao tác ghi đồng thời nhưng không bảo vệ quyền sở hữu ca. Lỗi hiện hữu; chưa xác định được thời điểm phát sinh.

Khuyến nghị: Trong cùng FileLock, từ chối holder khác; cho phép nhận lại cùng holder; thêm test cạnh tranh và kiểm tra quyền complete/review.

### P2 — F03: Dò workspace và metadata bàn giao chưa theo vị trí memory mới

Vị trí: `.agents/tools/sync_bus.py:171,351,508 và bản sao trong skill bridge`.

Không truyền workspace: root bị nhận là .agents và relative bus thành memory/DUAL_AGENT_BUS.json. Truyền workspace đúng: .agents/memory/DUAL_AGENT_BUS.json. Cả 18 artifacts trong bus nhận bàn giao vẫn dùng đường dẫn cũ không tồn tại.

Ảnh hưởng: Bus vật lý đọc được nhưng đường dẫn artifact, phát hiện file dự án và memo có thể sai; chưa đạt tiêu chí hoạt động ổn định.

Khuyến nghị: Thống nhất root resolver, đường dẫn memory và memo; kiểm từ project root, .agents và thư mục ngoài; giữ fallback legacy có kiểm soát.

### P2 — F04: Còn 8 literal đường dẫn cố định tới workspace ổ G:

Vị trí: `cad_plan_engine.py:1336–1338; dce_dxf_generator.py:214–215; msproject_bridge.py:113–115`.

AST tìm thấy 8 literal workspace trong 3 file runtime/CLI. Ba đường dẫn demo MS Project không tồn tại tại vị trí ghi cứng; các đường dẫn CAD tồn tại trên máy này nhưng không portable.

Ảnh hưởng: Di chuyển gói sang máy/ổ khác chưa bảo đảm độc lập; mặc định CLI vẫn trỏ dự án cụ thể.

Khuyến nghị: Suy ra template theo __file__; yêu cầu hoặc cấu hình input/output. Không xóa các đường dẫn dò executable hệ điều hành hợp lệ.

### P2 — F05: Registry và trình kiểm tra CAD không thống nhất đường dẫn

Vị trí: `.agents/skills/Technical_Illustrator/scripts/registry.json; Design_Evaluation/scripts/validate_registry.py`.

Validator báo MISSING_FILE cho cad_plan_engine.py, dce_dxf_generator.py, calc_to_dxf.py. Cả ba thực tế nằm trong cad_integration/, không phải scripts/. Ngoài ra có 5 cảnh báo orphan.

Ảnh hưởng: Không phải mất ba file nguồn, nhưng công cụ xác minh registry hiện không PASS và dễ điều hướng sai entry point.

Khuyến nghị: Bổ sung đường dẫn tương đối rõ ràng trong registry và cho validator/consumer dùng cùng quy ước.

## Kiểm chứng đạt

- 14/14 SKILL.md tồn tại và có version; các Markdown link literal được kiểm không thiếu đích.
- 222 file Python production parse thành công, 0 lỗi cú pháp. Không quét code trong archive/references/standards như code production.
- AGENTS.md ở root, .agents và .agents/skills có SHA-256 giống nhau. Đồng nhất nội dung chưa đồng nghĩa mọi ví dụ đường dẫn đều portable.
- Sáu ZIP đọc được, tất cả member qua CRC, không có đường dẫn member nguy hiểm; tổng 2.306 file trong sáu ZIP này. ZIP thứ bảy không đọc được.
- Đã chạy đủ 27 suites độc lập, không bỏ suite, không thay đổi mã production để làm test PASS.

## Hiệu năng

| Bộ chạy | Gemini bàn giao | CODEX kiểm chứng | Kết quả |
|---|---:|---:|---|
| Fast | 12,45s | 11.58s | 17/17 PASS |
| Full, lượt đo riêng | 80,06s | 93.84s | 27/27 PASS |

Lượt full đầu 93.73s chạy cùng một số lượt đọc kiểm kê I/O nên không dùng làm phép so sánh hiệu năng chính. Lượt full thứ hai chạy sau các phép quét nặng. Số Gemini là số khai báo trong bàn giao, không phải baseline cùng điều kiện được tái tạo. Biến động một vài lượt không đủ chứng minh hồi quy hiệu năng.

Mỗi suite lưu đầy đủ stdout, stderr, mã thoát và thời gian tại `full_isolated/`. `fast/` và `full/` giữ các lượt còn lại.

| Suite | Giây | Kết quả |
|---|---:|---|
| 1. Integration Test (64 checks) | 0.29 | PASS |
| 2. Regression Calculator Test (13 calculators) | 0.22 | PASS |
| 3. Pre-Execution Approval Gate (32 tests) | 0.21 | PASS |
| 4. Intent Classifier Benchmark (17 tests) | 0.15 | PASS |
| 5. E2E Pipeline Workflow | 0.16 | PASS |
| 6. DE Calculators Unit Tests (10 tests) | 0.13 | PASS |
| 7. Sprint 1 Reporting & TCVN Tests (4 tests) | 1.08 | PASS |
| 8. Sprint 2 Cross-Doc Conflict Control Tests (3 tests) | 0.16 | PASS |
| 9. Sprint 3 Phase 2 CAD/BIM/ETABS Tools (61 tests) | 0.23 | PASS |
| 10. Sprint 3 Phase 3 DCE Pro Integration Tests (19 tests) | 2.81 | PASS |
| 11. Sprint 3.4 DCE Deep Integration Tests (16 tests) | 2.14 | PASS |
| 12. Sprint 4 Document Intelligence & Conflict Detection (70 tests) | 0.87 | PASS |
| 13. Sprint 5 Comprehensive Verification & Reporting (17 tests) | 0.66 | PASS |
| 14. Policy Engine & Multi-Trigger Rules (55 tests) | 1.70 | PASS |
| 15. Sync Report System Consistency (14 tests) | 0.53 | PASS |
| 16. Cognitive & System Control Engine (40 tests) | 5.81 | PASS |
| 17. XLSX View Sanity — Anti-[Repaired] (regression openpyxl sheetViews/MergedCell) | 0.58 | PASS |
| 18. DCE CAD Compliance & Zero White Text Lock (9 tests) | 5.78 | PASS |
| 19. Dual-Agent Bridge & Bus IPC (3 tests) | 0.15 | PASS |
| 20. Cognitive Brain v2.0 Benchmark (10 tests) | 0.31 | PASS |
| 21. R&D & Structural TCVN Regression Patches (20 checks) | 1.18 | PASS |
| 22. Cognitive Architecture v2 — Dynamic DAG, Cycles, Budget & JSONL (47 tests) | 0.65 | PASS |
| 23. PDF Citation Grounding & Input Provenance Guard (62 tests) | 2.71 | PASS |
| 24. Nonlinear RC Fiber Section P-Mx-My 3D (23 tests) | 2.60 | PASS |
| 25. Project Data Adapter & E2E Batch Pipeline (34 tests) | 19.44 | PASS |
| 26. Durable Project Orchestration & Agent Roles (39 tests) | 41.22 | PASS |
| 27. CAD Edit Workbench (9 tests) | 1.86 | PASS |

## Tiêu chí nghiệm thu

| Tiêu chí | Đánh giá |
|---|---|
| Bus ở vị trí mới hoạt động ổn định | Đọc/nhận ca được; chưa đạt do F02, F03 |
| Không còn hardcoded path sai | Chưa đạt: F03, F04 |
| 27/27 suites PASS độc lập | Đạt |
| Báo cáo tại .agents/memory/audits | Đạt |

F01 và F05 là phát hiện bổ sung về toàn vẹn lưu trữ và registry. Không coi PASS của 27 suites là bằng chứng cho những nhánh chưa có test này.

## Bằng chứng và bàn giao

- `structure_evidence.json`: inventory, version/hash, AST literals, archive CRC/SHA-256 và root resolver.
- `archive_recheck.json`: hai lần đọc độc lập rvt-mcp.zip, chữ ký và kết quả EOCD.
- `bus_registry_evidence.json`, `registry.log`: test ownership trên bus tạm và lỗi registry.
- `full_isolated/timings.json`, `fast/timings.json`: số đo máy đọc được.
- `incoming_bus.json`: snapshot bus trước khi bàn giao kết quả kiểm toán.
Bus chuyển NEED_REVIEW cho GEMINI với các hành động khắc phục cụ thể. Không đánh dấu COMPLETED hoặc tự xác nhận các tiêu chí chưa đạt.
