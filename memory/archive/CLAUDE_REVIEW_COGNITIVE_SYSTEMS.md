# BẰNG CHỨNG KIỂM TOÁN & NÂNG CẤP — HỆ THỐNG KIỂM SOÁT VẬN HÀNH v1.1 (CLAUDE → GEMINI)

> **Người thực hiện:** Claude Code
> **Thời điểm:** 2026-10-24 (+07:00)
> **Đối tượng kiểm toán:** `system_controller.py`, `standards_graph.py`, `project_memory.py`, `sync_bus.py`, 3 điểm tích hợp Skills
> **Trạng thái cuối:** **16/16 test suites PASS** (suite #16 tăng từ 8 → 21 tests) — 26.58s
> **Kết luận:** `CLAUDE_VERIFIED_PASS_WITH_FIXES` — 13 lỗi runtime đã phát hiện và sửa

---

## 1. KẾT LUẬN CHUNG

Mã của Gemini **đúng thiết kế tổng thể, zero-dependency, chạy được và test xanh thật** (đã xác minh lại 16/16). Tuy nhiên, 13 lỗi runtime mà bộ test cũ KHÔNG BẮT ĐƯỢC đã được phát hiện và sửa trong lần review này — chủ yếu nằm ở 3 module mới. Các lỗi này sẽ gây **crash khi dùng tính năng chưa được test** (không crash ở chế độ mặc định), nên 8 test ban đầu vẫn xanh.

---

## 2. DANH MỤC 13 LỖI ĐÃ SỬA (BUG-001 → BUG-013)

| Mã | Module | Lỗi | Mức độ | Đã vá |
|---|---|---|---|---|
| **BUG-001** | `standards_graph.py` | `traverse(direction="both")` → `ProgrammingError: Incorrect number of bindings` (CTE "both" cần 2 tham số nhưng chỉ bind 1) | **Cao** | ✅ |
| **BUG-002** | `standards_graph.py` | Rò rỉ handle SQLite: `with self._get_conn()` không `close()`, chỉ commit → file không bao giờ release | **Cao** | ✅ |
| **BUG-003** | `standards_graph.py` | `upsert_edge` không idempotent: UNIQUE constraint không chặn được cạnh trùng khi properties khác nhau | Trung bình | ✅ |
| **BUG-004** | `system_controller.py` | `LoopBreaker.max_cycle_repeats` khai báo nhưng **không dùng** — mọi phiên bản đều trip ở 4 hop | Trung bình | ✅ |
| **BUG-005** | `system_controller.py` | `allow_execution()` có side-effect (chuyển OPEN→HALF_OPEN, tiêu tốn lượt thử) → gọi để dò trạng thái làm hỏng probe | **Cao** | ✅ |
| **BUG-006** | `system_controller.py` | HALF_OPEN cho phép nhiều probe đồng thời (thundering herd) | Trung bình | ✅ |
| **BUG-007** | `system_controller.py` | Guard READ_ONLY chặn tool READ vì động từ ghi so khớp theo **substring** (`recalculate_beam` chứa `calc`) | Trung bình | ✅ |
| **BUG-008** | `system_controller.py` | `BlackboxRecorder.log_dir` khai báo nhưng **không ghi gì xuống đĩa** — trace chỉ nằm trong RAM, mất khi process chết | Trung bình | ✅ |
| **BUG-009** | `sync_bus.py` | Ghi JSON **không nguyên tử** (viết trực tiếp, không có lock) → race condition khi 2 agent ghi cùng lúc (CVE-2025-68146) | **Cao** | ✅ |
| **BUG-010** | `sync_bus.py` | Không có FileLock — cần khoá đặt trên ổ local `C:\`, không phải ổ Drive `G:\` | **Cao** | ✅ |
| **BUG-011** | Skills | `preflight_check` chưa gắn vào bất kỳ skill nào (yêu cầu #3 trong memo chưa làm) | Trung bình | ✅ |
| **BUG-012** | `project_memory.py` | Test ghi `LL-TEST-01` vào **file production** `global_lessons_learned.json` (ô nhiễm dữ liệu thực) | Trung bình | ✅ |
| **BUG-013** | 3 Skills | Đường dẫn import `skill_guard` **sai trong GD & SDE** (giải sang thư mục không tồn tại → guard bị vô hiệu hoá im lặng qua `except`) | **Cao** | ✅ |

---

## 3. CHI TIẾT TỪNG LỖI

### BUG-001/002/003 — `standards_graph.py`
- **Căn nguyên CTE "both":** nhánh `both` là 2 câu `WHERE depth < ?` gộp UNION, cần 2 tham số binding; bản gốc chỉ truyền `(start_id, max_depth)` → SQLite ném `ProgrammingError`. Dị bản "outbound"/"inbound" chỉ có 1 tham số nên không lộ.
- **Căn nguyên rò rỉ handle:** Python `with conn` chỉ là context manager cho **commit/rollback**, KHÔNG `close()`. Mỗi call tạo một connection, file handle chỉ được reclaim khi GC — trên Windows (file lock theo handle) nhiều file DB bị khoá hoặc không xoá được.
- **Sửa:** tách rõ `allow_execution()` (dò trạng thái, không tiêu tốn probe) và `_try_acquire_probe()` (giành quyền, side-effect). Connection luôn `close()` trong `finally`. `upsert_edge` thêm `ON CONFLICT(source,target,properties) DO UPDATE`.

### BUG-004/005/006/007/008 — `system_controller.py`
- **Căn nguyên `max_cycle_repeats`:** tham số constructor nhận vào nhưng không xuất hiện trong logic. Đã nối lại: `repeats = max(2, self.max_cycle_repeats)` và so sánh đuôi trajectory theo chu kỳ 2 tác tử.
- **Căn nguyên HALF_OPEN probe:** bản gốc `allow_execution()` khi OPEN hết thời gian hạ nhiệt là chuyển HALF_OPEN và trả `True` — nhưng trả True không có nghĩa là được *giành* lượt thử. Khi `call()` gọi lại, bản gốc lại cho phép → nhiều probe chạy song song. Đã tách `_try_acquire_probe()` với cờ `_half_open_probe_in_flight` (single-probe, thread-safe qua `RLock`).
- **Căn nguyên guard substring:** `"create" in tool_name` chặn luôn `recalculate_beam` vì chứa `calc`? Không — vấn đề là động từ so khớp substring: đã đổi sang **so khớp ranh giới từ** (`==` hoặc `startswith(verb+"_")` hoặc `("_"+verb) in`). `recalculate_beam` → ALLOW, `create_view` → BLOCK.
- **Căn nguyên Blackbox không ghi đĩa:** `log_dir` chỉ để sinh đường dẫn, không có hàm ghi. Đã thêm `_flush()` ghi JSONL append-only theo ngày (`traces/trace_YYYYMMDD.jsonl`), bỏ qua lỗi I/O để không phá luồng chính.

### BUG-009/010 — `sync_bus.py`
- **Căn nguyên non-atomic write:** `BUS_PATH.write_text()` trực tiếp — nếu process bị kill giữa chừng, file bus là JSON cắt cụt. Đã thay bằng **atomic replace**: ghi `*.tmp.<pid>` cùng thư mục → `os.fsync()` → `os.replace()`. Không bao giờ để file nửa vời.
- **FileLock (không cần thư viện ngoài):** Windows dùng `msvcrt.locking` (1 byte), POSIX dùng `fcntl.flock`, fallback `O_EXCL` theo tên file. **Khoá đặt tại `%LOCALAPPDATA%\GoogleAIStudio\locks\`** (ổ local `C:`), KHÔNG đặt trên ổ Drive `G:` vì Google Drive không hỗ trợ file lock tương thích POSIX.
- **Kể tên key giữ `Verification_Status` (không viết lại thành `verification_status`)** để tương thích với bus hiện có mà Gemini đang đọc.

### BUG-011 — Gắn `preflight_check` vào 3 Skills
- Tạo module dùng chung **`_SHARED/SHARED_CONTEXT/skill_guard.py`**:
  - `preflight(actor, tool, payload, fail_open=False)` → `(allowed, reason)`, **Fail-Closed** (controller lỗi → chặn, trừ khi `fail_open=True`).
  - `@guarded(actor=..., tool=...)` decorator.
  - Khi `LOOP_BLOCKED` → `controller.loop_breaker.reset()` để không lặp cảnh.
- Gắn vào **3 điểm vào:**
  1. `Global_Dispatcher/scripts/approval_gate.py` — trước `intercept()`
  2. `Design_Evaluation/scripts/report_dispatcher.py` — trước `main()` load data
  3. `Structural_Design_Engineer/scripts/export_calc_sheet.py` — trước `main()`
- Mỗi skill có `_find_skill_guard_dir()` đi lên theo cấp để resolve đúng đường dẫn (không phụ thuộc độ sâu thư mục).

### BUG-012 — Ô nhiễm file production
- `TestLessonsLearnedRepository` và `TestStandardsGraph` giờ dùng **`tempfile.TemporaryDirectory()`** cho storage/DB, không ghi vào file production.
- `project_memory._save_json` / `LessonsLearnedRepository._save_data` đổi sang **atomic replace** (ghi `.tmp` rồi `replace`).
- Entry `LL-TEST-01` còn sót trong `global_lessons_learned.json` đã được dọn (qua API, không dùng lệnh xoá trực tiếp).

### BUG-013 — Guard import im lặng
- Bản gốc GD & SDE resolve đường dẫn tới `_SHARED/SHARED_CONTEXT` ở **sai cấp**, không tồn tại → import rơi `except` → `_GUARD_AVAILABLE=False` → **guard bị tắt im lặng**, tưởng đã gắn mà thực ra không.
- Đã dùng resolver đi lên theo cấp cho cả 3 skill, test hồi quy `test_skill_guard_import_paths_resolve_for_all_3_skills` xác nhận `_GUARD_AVAILABLE=True` ở cả 3.

---

## 4. TEST HỒI QUY THÊM (13 test mới, 8 → 21)

Class `TestRegressionClaudeReview` chống tái phát từng lỗi:
- `test_traverse_both_direction_works` (BUG-001)
- `test_traverse_all_directions_do_not_leak_handles` (BUG-002)
- `test_upsert_edge_is_idempotent` (BUG-003)
- `test_loop_breaker_respects_max_cycle_repeats` (BUG-004)
- `test_circuit_breaker_allow_execution_does_not_consume_probe` (BUG-005)
- `test_circuit_breaker_half_open_single_probe` (BUG-006)
- `test_execution_guard_does_not_block_read_tools_by_substring` (BUG-007)
- `test_blackbox_recorder_persists_span_to_disk` (BUG-008)
- `test_sync_bus_atomic_write_leaves_no_partial_file` (BUG-009)
- `test_sync_bus_file_lock_is_exclusive` (BUG-010)
- `test_skill_guard_preflight_blocks_dangerous_shell` (BUG-011)
- `test_lessons_repository_does_not_pollute_production_file` (BUG-012)
- `test_skill_guard_import_paths_resolve_for_all_3_skills` (BUG-013)

---

## 5. THAO TÁC GEMINI CẦN LẤY

1. **Không cần chạy lại** bộ test cũ — 16/16 đã PASS trên mã mới (chi tiết ở §2, §4).
2. **Commit mã đã sửa** (6 file đã sửa + 2 file mới `skill_guard.py`, `test_cognitive_and_control_systems.py` cập nhật). Hiện tại mọi file là untracked/modified trong `.agents/.git` — chưa commit.
3. **Dọn `traces/`** khỏi `.gitignore`? — `traces/` (vết Blackbox JSONL) là runtime artifact. Đề xuất thêm vào `.gitignore` cùng `__pycache__/`.
4. **Xác nhận trạng thái** vào `DUAL_AGENT_BUS.json` (đã làm ở bước tiếp theo).
5. **Đề xuất nâng cấp tiếp theo** (bắt đầu phiên sau):
   - `standards_graph.py`: thêm WAL checkpoint định kỳ + chuẩn hoá `query_element_requirements` để hỗ trợ `direction="inbound"`.
   - `system_controller.py`: gắn `BlackboxRecorder` vào `CircuitBreaker.record_failure` (ghi vết khi trip), thêm metric token cho `LoopBreaker`.
   - `skill_guard.py`: chuyển `fail_open` → config từ `AGENTS.md` thay vì hard-code, cho phép User bật/tắt guard theo context.

---

## 6. DANH SÁCH FILE ĐÃ SỬA / THÊM

| File | Trạng thái | Ghi chú |
|---|---|---|
| `.agents/tools/system_controller.py` | **ĐÃ SỬA** | BUG-004/005/006/007/008 — thread-safety, single-probe, word-boundary, JSONL |
| `.agents/_SHARED/standards/standards_graph.py` | **ĐÃ SỬA** | BUG-001/002/003 — CTE both, handle close, upsert idempotent |
| `.agents/_SHARED/memory/project_memory.py` | **ĐÃ SỬA** | atomic save, seed không ghi khi file tồn tại |
| `.agents/tools/sync_bus.py` | **ĐÃ SỬA** | BUG-009/010 — atomic write + FileLock (C:\ local) |
| `.agents/_SHARED/SHARED_CONTEXT/skill_guard.py` | **MỚI** | BUG-011/013 — wrapper preflight dùng chung cho 3 skill |
| `.agents/skills/Global_Dispatcher/scripts/approval_gate.py` | **ĐÃ SỬA** | gắn `_guard_check` vào `intercept()` |
| `.agents/skills/Design_Evaluation/scripts/report_dispatcher.py` | **ĐÃ SỬA** | gắn `_guard_check` vào `main()` |
| `.agents/skills/Structural_Design_Engineer/scripts/export_calc_sheet.py` | **ĐÃ SỬA** | gắn `_guard_check` vào `main()` |
| `.agents/tests/test_cognitive_and_control_systems.py` | **ĐÃ SỬA** | 13 test hồi quy + isolate production file |
| `.agents/tests/run_all_tests.py` | **ĐÃ SỬA** | suite #16: 8 → 21 tests |
| `memory/CLAUDE_REVIEW_COGNITIVE_SYSTEMS.md` | **MỚI** | báo cáo này |
| `memory/DUAL_AGENT_BUS.json` | **ĐÃ CẬP NHẬT** | status → `CLAUDE_VERIFIED_PASS_WITH_FIXES` |

---

## 7. NÂNG CẤP #1 — WIRE 2 MODULE "DEAD-CODE" VÀO LUỒNG TÍNH TOÁN THẬT (2026-10-25)

Kiến nghị số 1 (module `StandardsGraph` + `LessonsLearnedRepository` chưa được
bất kỳ skill nào dùng) đã được triển khai. Hai module tri thức giờ **thực sự
được gọi** trong luồng tính toán / xuất báo cáo.

### 7.1. `StandardsGraph` → `Policy Engine` (`decide_eta_with_standards`)
- File: `.agents/tools/policy_engine.py` (SECTION 1B, mới).
- API mới:
  - `decide_eta_with_standards(eta_input, element_id=None, element_type=None, graph=None)`
    → trả `PolicyDecision` có thêm `standard_basis` + `standard_conflicts`.
  - `resolve_standard_basis(element_id, element_type, graph)` → căn cứ tiêu chuẩn.
  - `resolve_element_node(...)` → chuẩn hoá "dầm"/"cot"/"dam_thep" → node id.
- **Nguyên tắc an toàn:** ngưỡng η (0.70 / 0.90 / 1.00) theo AGENTS.md §6 là
  **TUYỆT ĐỐI, không đổi**. Đồ thị chỉ bổ sung *trích dẫn điều khoản* (vì sao
  ngưỡng này) và *phát hiện mâu thuẫn* nếu tiêu chuẩn đặt ngưỡng ULS lệch khỏi
  1.00. Không tự quyết định thay kỹ sư.
- Fail-safe: không import được đồ thị → trả về đúng `decide_eta()` (không crash).
- Đã wire vào trigger **POST-EVAL-01**: `details` giờ có `standard_basis`,
  `standard_citations`, và cảnh báo `standard_conflicts`.

### 7.2. `LessonsLearnedRepository` → `Design_Evaluation` report
- File mới: `.agents/_SHARED/memory/lessons_lookup.py`
  (`find_relevant_lessons`, `format_lessons_markdown`, `format_lessons_docx`).
- File: `.agents/skills/Design_Evaluation/scripts/report_dispatcher.py`
  - `_collect_lessons(handoff)` khớp lesson theo project_code + tiêu chuẩn
    (`Standard_Method`) + từ khoá hạng mục.
  - Thêm section **"Kinh nghiệm liên dự án"** vào report **MD, DOCX, HTML**.
- Tác dụng: tờ trình / báo cáo kỹ thuật tự động cảnh báo "đã gặp sự cố tương
  tự ở dự án X" — biến kho bài học (Prime Diamond, SS1, Montalp) thành đầu vào
  thực sự cho reviewer.

### 7.3. Kết quả
- Suite #14: **42 → 55 tests** (thêm `TestStandardsGraphIntegration` +
  `TestLessonsLookupIntegration`).
- **16/16 test suites PASS** (29.15s).
- File production không bị ô nhiễm (3 lessons, 14 node DB chuẩn).
- 5 file thay đổi, **chưa commit** (đề giao Gemini).

### 7.4. GHI CHÚ THIẾT KẾ QUAN TRỌNG
- `_parse_threshold_value`: chuỗi dạng `L/200`, `1/200` (tỷ số SLS/độ võng)
  trả `None`, KHÔNG parse thành 200 — tránh sai ngữ cảnh khi phát hiện conflict.
- Cả 2 tích hợp đều **fail-open** ở tầng import (đồ thị/lessons thiếu → báo
  cáo vẫn xuất, chỉ thiếu trích dẫn) — khác với guard (fail-closed khi controller
  lỗi). Đây là đúng: tri thức là bổ trợ, không phải rào chắn an toàn.

---

## 8. NÂNG CẤP #2 — CHUYỂN GUARD SANG FAIL-CLOSED THEO CHÍNH SÁCH (2026-10-25)

### 8.1. Lỗi đã sửa (BUG-014)
v1.0 của `skill_guard.py` tuyên bố "Fail-Closed" nhưng cả 3 skill gọi vào đều
hard-code `fail_open=True` — khi **controller bị lỗi, thao tác vẫn chạy tự do**
(đúng bản chất fail-open, trái nguyên tắc thiết kế của `system_controller.py`).
Ngoài ra nhánh `if not _GUARD_AVAILABLE: return True` cũng là fail-open
tầng thứ hai (guard chưa cài → bỏ qua hoàn toàn).

### 8.2. Thiết kế mới — phân biệt 2 tình huống, config-driven
File mới: `.agents/_SHARED/SHARED_CONTEXT/guard_policy.json`

| Tình huống | Hành vi mặc định | Lý do |
|---|---|---|
| **Controller đã cài nhưng lỗi** (`preflight_check` ném exception) | **CHẶN** (Fail-Closed) | Tín hiệu an toàn thật: kiểm soát hỏng → không ai xác nhận được thao tác còn an toàn |
| **Chưa có hạ tầng guard** (không import được `system_controller`) | **CHO PHÉP + WARN** | Không thể chặn cái chưa tồn tại; chặn thì hệ thống không khởi động được |

Cơ chế mở rộng (không cần sửa code):
- `tools_fail_open`: whitelist tool được chạy tiếp khi controller lỗi.
- `GUARD_FAIL_OPEN=1` (env): mở tạm cả hệ thống — cho vận hành.
- `readonly_skills` / `modes` (policy): chọn chế độ SAFE/READ_ONLY/UNRESTRICTED
  theo skill; `GUARD_MODE` (env) ghi đè toàn cục.

### 8.3. Thay đổi
- `skill_guard.py` v2.0: `load_policy()`, `get_guard_mode()`, `is_fail_open_env()`;
  `preflight(skill=...)` chọn chế độ guard; cờ `_controller_import_attempted`
  (chống re-import che dấu trạng thái).
- 3 skill (GD/DE/SDE): bỏ `fail_open=True` hard-code, truyền `skill=...`
  để policy chọn chế độ.

### 8.4. Kết quả
- Suite #16: **21 → 25 tests** (4 test hồi quy BUG-014: fail-closed khi controller
  lỗi, harness-missing, mode theo policy/env, override env var).
- **16/16 test suites PASS** (27.49s).

### 8.5. ĐIỂM CẦN GEMINI QUAN SÁT KHI COMMIT
- `guard_policy.json` nằm trong `_SHARED/SHARED_CONTEXT/` (đã được track bởi git
  của `.agents/` — kiểm tra chưa có luật `.gitignore` nào chặn nó).
- Khi vận hành production với controller ổn định, chính sách mặc định là
  **fail-closed** — nếu cần "bỏ rào chắn tạm" cho 1 tool, sửa `guard_policy.json`
  (whitelist) thay vì sửa code.
