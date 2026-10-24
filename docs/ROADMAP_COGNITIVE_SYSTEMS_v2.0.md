# ROADMAP V2.0 — HỆ THỐNG ĐỒ THỊ TRI THỨC TIÊU CHUẨN & HỘP ĐEN CẦU DAO TỰ ĐỘNG

> **Tác giả:** Gemini Antigravity (Đồng hành: Claude Code)  
> **Thời điểm lập:** 2026-10-24 (+07:00)  
> **Mục tiêu:** Nâng cấp hệ thống nhận thức (Cognitive Engine) và kiểm soát thực thi (Execution Control) từ v1.1 lên v2.0, chuẩn bị cho kết nối diện rộng Revit MCP, AutoCAD DCE Pro và ETABS/PLAXIS API.  
> **Trạng thái nền tảng v1.1:** 16/16 test suites PASS 100%, commit hash `9ee35d3`.

---

## 1. TỔNG QUAN NÂNG CẤP V2.0

Sau khi hoàn tất đợt kiểm toán và sửa 13 lỗi runtime ở phiên bản v1.1, hệ thống đã đạt:
- **Thread-safety hoàn chỉnh** qua `threading.RLock`.
- **Chống race condition** qua FileLock liên tiến trình (bảo vệ trên ổ cứng local `C:\` thay vì ổ đám mây `G:\`).
- **Ghi bền vững JSONL** cho hộp đen `BlackboxRecorder`.
- **Hàng rào an toàn `skill_guard`** cắm chốt tại 3 skill trọng yếu.

Giai đoạn v2.0 tập trung giải quyết 3 bài toán kiến trúc sâu hơn:
1. **StandardsGraph v2.0:** Tối ưu hóa lưu trữ SQLite WAL, tự động phát hiện mâu thuẫn tiêu chuẩn (Conflict Detection), và truy vấn hai chiều (Bidirectional / Inverse Queries).
2. **CircuitBreaker & Blackbox Integration:** Tự động ghi vết sự kiện ngắt mạch (Tripped/Probe/Recovery Spans) vào Hộp đen mà không phụ thuộc vào tầng gọi bên ngoài.
3. **LoopBreaker & Guard Policy Engine:** Mở rộng từ đếm bước nhảy (Hop-based) sang giám sát ngân sách Token / Chi phí, cho phép nạp policy động từ `AGENTS.md`.

---

## 2. KẾ HOẠCH NÂNG CẤP CHI TIẾT

### 2.1. Module `standards_graph.py` (v2.0)

#### A. WAL Checkpoint & Quản lý Bộ nhớ
- **Vấn đề:** Khi đồ thị tiêu chuẩn mở rộng và thực hiện hàng ngàn phép upsert/traverse, file WAL (`standards_graph.db-wal`) trên Windows có xu hướng phình to nếu không được checkpoint chủ động.
- **Giải pháp v2.0:**
  - Thêm phương thức `checkpoint(mode: str = "PASSIVE" | "FULL" | "RESTART" | "TRUNCATE")`.
  - Tự động gọi `PRAGMA wal_checkpoint(TRUNCATE)` khi đóng tiến trình hoặc sau mỗi chu kỳ cập nhật dữ liệu hàng loạt.
  - Thiết lập `PRAGMA synchronous = NORMAL` và `PRAGMA cache_size = -64000` (64MB) để tăng tốc độ truy vấn traversal đồ thị đệ quy.

#### B. Mở rộng Truy vấn Đồ thị Đa chiều (Bidirectional & Inverse Retrieval)
- **Vấn đề:** Hiện tại `query_element_requirements` chỉ hỗ trợ duyệt xuôi (`outbound`: Cấu kiện -> Tiêu chuẩn -> Điều khoản). Chưa hỗ trợ duyệt ngược (`inbound`: Từ Tiêu chuẩn -> Xem cấu kiện nào bị ảnh hưởng).
- **Giải pháp v2.0:**
  - Bổ sung `query_standard_impact(standard_or_clause_id: str) -> Dict[str, Any]`:
    - Truy vấn toàn bộ cấu kiện, công thức và liên kết chịu tác động khi một tiêu chuẩn thay đổi hoặc cập nhật phiên bản.
    - Hỗ trợ phân tích tác động (Impact Analysis) khi chuyển đổi tiêu chuẩn thiết kế (ví dụ từ TCVN 2737:1995 sang TCVN 2737:2023).

#### C. Tự động Phát hiện Mâu thuẫn Phiên bản Tiêu chuẩn (Standard Conflict Detector)
- Khóa cứng với `STANDARDS_LOCK.md`:
  - Khi một node tiêu chuẩn được nạp vào đồ thị, tự động đối chiếu với danh mục khóa phiên bản duy nhất trong `STANDARDS_LOCK.md`.
  - Nếu phát hiện dự án sử dụng đồng thời 2 phiên bản của cùng 1 tiêu chuẩn trong cùng một chuỗi liên kết (ví dụ dầm dùng TCVN 5574:2012 còn cột dùng TCVN 5574:2018), đồ thị lập tức tạo quan hệ cạnh `CONFLICT_WITH` và kích hoạt mã lỗi `E004` (Standard Conflict Detected).

---

### 2.2. Module `system_controller.py` (v2.0)

#### A. Gắn kết Trực tiếp `BlackboxRecorder` vào `CircuitBreaker`
- **Vấn đề:** Khi một service (ETABS API, Revit MCP, CAD Bridge) bị lỗi liên tiếp và cầu dao chuyển sang `OPEN`, hiện tại chỉ có log ngoại lệ tức thời trong hàm gọi mà Blackbox chưa tự động ghi lại trạng thái ngắt mạch hệ thống.
- **Giải pháp v2.0:**
  - Trong `CircuitBreaker.record_failure()`: Khi `self.failure_count >= self.failure_threshold`, tự động phát sinh một TraceSpan chuyên biệt:
    ```python
    recorder.start_span(
        trace_id=active_trace_id,
        actor="CircuitBreaker",
        action=f"TRIP_CIRCUIT:{self.name}",
        metadata={
            "consecutive_failures": self.failure_count,
            "threshold": self.failure_threshold,
            "cooldown_seconds": self.recovery_timeout,
            "next_retry_after": datetime.fromtimestamp(self.last_failure_time + self.recovery_timeout).isoformat()
        }
    )
    ```
  - Trong `CircuitBreaker.record_success()`: Khi phục hồi từ `HALF_OPEN` về `CLOSED`, ghi nhận sự kiện `CIRCUIT_RECOVERED`.

#### B. LoopBreaker v2.0 — Token & Budget Throttling
- **Vấn đề:** LoopBreaker hiện tại mới dừng ở việc đếm số hops (max 10) và phát hiện ping-pong lặp lại (A -> B -> A -> B). Tuy nhiên, một vòng lặp gồm nhiều agent khác nhau (A -> B -> C -> A -> B -> C) hoặc mỗi hop sinh context quá lớn vẫn có thể làm cạn kiệt ngân sách token.
- **Giải pháp v2.0:**
  - Tích hợp theo dõi `cumulative_token_estimate` trong Trajectory.
  - Cung cấp ngưỡng cảnh báo mềm (Soft Limit at 40k tokens) và ngắt cứng (Hard Limit at 80k tokens) để kích hoạt Review Gate trước khi gây lãng phí chi phí LLM.

#### C. `skill_guard.py` v2.0 — Policy-Driven Dynamic Guarding
- **Vấn đề:** Tham số `fail_open` hiện phải chỉ định cứng tại điểm gọi.
- **Giải pháp v2.0:**
  - Cho phép đọc cấu hình chế độ vận hành từ biến môi trường hoặc file cấu hình `AGENTS.md`:
    - `MODE=STRICT`: Luôn Fail-Closed (100% an toàn cho môi trường chạy thực tế).
    - `MODE=AUDIT`: Cho phép thực thi các lệnh read-only nhưng tự động log chi tiết vào trace.
    - `MODE=DEVELOPMENT_TEST`: Cho phép mock/pass qua một số guard trong môi trường test cô lập.

---

## 3. LỘ TRÌNH TRIỂN KHAI (MILESTONES)

| Sprint | Thời gian dự kiến | Nội dung triển khai | Kết quả bàn giao |
|---|---|---|---|
| **Sprint 2.1** | Tuần 1 | Triển khai WAL Checkpoint + Bidirectional Traversal cho `standards_graph.py` | `standards_graph.py` v2.0 + Test Suite mở rộng |
| **Sprint 2.2** | Tuần 2 | Gắn `BlackboxRecorder` vào `CircuitBreaker` + Token Tracking cho `LoopBreaker` | `system_controller.py` v2.0 + JSONL Trace Schema |
| **Sprint 2.3** | Tuần 3 | Tích hợp Policy Engine vào `skill_guard.py` + Đấu nối hoàn chỉnh với Revit MCP & AutoCAD | Bộ test E2E thực chiến trên mô hình thật |

---

## 4. XÁC NHẬN ĐỒNG HÀNH LIÊN TÁC TỬ

- **Claude Code:** Đã hoàn thành kiểm toán độc lập, vá 13 lỗi runtime, bổ sung 13 tests hồi quy, xác nhận 16/16 test suites đạt 100%.
- **Gemini Antigravity:** Đã rà soát thread-safety/bảo mật, dọn dẹp gitignore, đóng gói commit toàn vẹn `9ee35d3`, và hoàn thiện Roadmap v2.0.
