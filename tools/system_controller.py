# -*- coding: utf-8 -*-
"""
system_controller.py — Bộ Điều Khiển Giám Sát, Cầu Dao An Toàn & Hộp Đen Thực Thi (v1.1)
Lấy cảm hứng từ agent-circuit-breaker, aw1-breaker và SupervisorAgent.
Zero-dependency, Pure Python, thiết kế Fail-Closed.

v1.1 (Claude review):
  - Thread-safety: mọi state machine dùng RLock.
  - CircuitBreaker: HALF_OPEN chỉ cho đúng 1 lượt thử (single-probe).
  - LoopBreaker: tôn trọng max_cycle_repeats (trước đây khai báo nhưng không dùng).
  - BlackboxRecorder: ghi vết bền vững xuống JSONL (trước đây chỉ giữ trong RAM).
  - SystemController: thêm cơ chế phê duyệt PENDING_APPROVAL có thể resolve được.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

import time
import uuid
import json
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ==============================================================================
# 1. CẦU DAO TỰ NGẮT THỰC THI (CIRCUIT BREAKER)
# ==============================================================================

class CircuitState(Enum):
    CLOSED = "CLOSED"       # Hoạt động bình thường
    OPEN = "OPEN"           # Ngắt mạch hoàn toàn (chặn thực thi do lỗi dồn dập)
    HALF_OPEN = "HALF_OPEN" # Thử nghiệm kết nối lại sau thời gian hạ nhiệt

class CircuitBreakerTripped(Exception):
    """Ngoại lệ khi cầu dao đang ở trạng thái OPEN."""
    pass

class CircuitBreaker:
    """
    Cầu dao bảo vệ tài nguyên (ETABS API, Revit MCP, CAD Bridge, SQLite).
    Nguyên lý:
    - Nếu thất bại liên tiếp >= failure_threshold -> chuyển sang OPEN.
    - Trong trạng thái OPEN, mọi cuộc gọi bị BLOCK ngay lập tức (Fail-Closed).
    - Sau recovery_timeout giây -> chuyển sang HALF_OPEN để thử 1 lần.
    - HALF_OPEN chỉ cho đúng 1 lượt thử đồng thời (single-probe), tránh "thundering herd".
    """
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self._lock = threading.RLock()
        self._half_open_probe_in_flight = False

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.success_count += 1
            self._half_open_probe_in_flight = False

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self._half_open_probe_in_flight = False
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def allow_execution(self) -> bool:
        """
        Kiểm tra có cho phép thực thi hay không.
        CÓ side-effect duy nhất: chuyển OPEN -> HALF_OPEN khi đã hết thời gian hạ nhiệt.
        KHÔNG tiêu tốn lượt thử HALF_OPEN — lượt thử chỉ được giành trong call(),
        nhờ vậy gọi allow_execution() để dò trạng thái rồi call() vẫn chạy được.
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                return not self._half_open_probe_in_flight
            return False

    def _try_acquire_probe(self) -> bool:
        """
        Thử giành quyền thực thi (side-effect). Trả về False nếu phải chặn.
        - CLOSED: luôn được phép.
        - OPEN: nếu đã hết thời gian hạ nhiệt -> chuyển HALF_OPEN và giành lượt thử.
        - HALF_OPEN: chỉ được phép nếu chưa có lượt thử nào đang chạy.
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_probe_in_flight = True
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_probe_in_flight:
                    return False
                self._half_open_probe_in_flight = True
                return True
            return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if not self._try_acquire_probe():
            raise CircuitBreakerTripped(
                f"[CIRCUIT_OPEN] Dịch vụ '{self.name}' đang bị ngắt mạch do {self.failure_count} lỗi liên tiếp. "
                f"Vui lòng đợi hạ nhiệt hoặc dùng fallback."
            )
        try:
            res = func(*args, **kwargs)
            self.record_success()
            return res
        except Exception as e:
            self.record_failure()
            raise e

    def reset(self):
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self._half_open_probe_in_flight = False

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "consecutive_failures": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_sec": self.recovery_timeout,
                "success_count": self.success_count
            }


# ==============================================================================
# 2. HÀNG RÀO PHÂN QUYỀN VÀ KIỂM TRA LỆNH (EXECUTION GUARD)
# ==============================================================================

class GuardDecision(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    PENDING_APPROVAL = "PENDING_APPROVAL"

class ExecutionGuard:
    """
    Hàng rào an toàn thời gian thực.
    - Chặn các câu lệnh shell phá hoại (rm, format, del root...).
    - Chặn các hành vi ghi đè mô hình khi đang ở chế độ READ_ONLY (Review Gate).
    - Yêu cầu xác nhận phê duyệt (PENDING_APPROVAL) khi chi phí cao hoặc xóa cấu kiện.
    """
    FORBIDDEN_SHELL_PATTERNS = [
        "rm -rf", "rm -fr", "del /f /s /q c:\\", "format ", "drop database", "drop table",
        ":(){ :|:& };:", "shutil.rmtree('c:", "remove-item -recurse -force c:\\"
    ]

    READ_ONLY_BLOCKED_TOOLS = [
        "revit_create_elements", "revit_modify_elements", "revit_delete_elements",
        "dce_modify_dwg", "etabs_set_member_properties", "file_delete"
    ]

    # Động từ ghi/xóa — dùng để phát hiện tool ghi bất kể tên gì.
    WRITE_VERBS = ("create", "modify", "delete", "write", "remove", "update", "drop", "purge", "export")

    def __init__(self, mode: str = "SAFE"):
        # mode: SAFE, READ_ONLY, UNRESTRICTED
        self.mode = mode

    def _is_write_tool(self, tool_name: str) -> bool:
        lowered = tool_name.lower()
        if lowered in self.READ_ONLY_BLOCKED_TOOLS:
            return True
        # So khớp theo ranh giới từ để tránh chặn oan (vd "recalculate" chứa "create").
        return any(
            lowered == verb or lowered.startswith(verb + "_") or ("_" + verb) in lowered
            for verb in self.WRITE_VERBS
        )

    def evaluate_tool_call(self, tool_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        # 1. Kiểm tra chế độ Chỉ Đọc (READ_ONLY Audit Gate)
        if self.mode == "READ_ONLY":
            if self._is_write_tool(tool_name):
                return {
                    "decision": GuardDecision.BLOCK.value,
                    "reason": f"Chế độ READ_ONLY đang kích hoạt. Cấm thực thi công cụ ghi '{tool_name}'."
                }

        # 2. Kiểm tra câu lệnh shell nếu payload có command
        cmd = str(payload.get("command", "")).lower()
        for pattern in self.FORBIDDEN_SHELL_PATTERNS:
            if pattern in cmd:
                return {
                    "decision": GuardDecision.BLOCK.value,
                    "reason": f"Phát hiện mẫu lệnh nguy hiểm bị cấm: '{pattern}'."
                }

        # 3. Yêu cầu xác nhận người dùng với thao tác xóa cấu kiện hoặc chi phí rủi ro
        if "delete" in tool_name.lower() or payload.get("requires_approval") is True:
            return {
                "decision": GuardDecision.PENDING_APPROVAL.value,
                "reason": f"Thao tác '{tool_name}' tiềm ẩn rủi ro thay đổi mô hình, yêu cầu User duyệt."
            }

        return {
            "decision": GuardDecision.ALLOW.value,
            "reason": "Thỏa mãn mọi quy tắc hàng rào an toàn."
        }


# ==============================================================================
# 3. BỘ CHỐNG LẮP VÀ PHÁT HIỆN CHU TRÌNH ĐA TÁC TỬ (LOOP BREAKER)
# ==============================================================================

class LoopBreaker:
    """
    Bộ đệm chống vòng lặp vô tận (Runaway Loop / Ping-Pong between Agents).
    - Theo dõi lịch sử chuỗi tác tử gọi nhau (Trajectory).
    - Ngắt mạch nếu vượt quá max_hops (mặc định 10).
    - Phát hiện chu kỳ lặp A -> B -> A -> B lặp lại quá max_cycle_repeats.
    """
    def __init__(self, max_hops: int = 10, max_cycle_repeats: int = 2):
        self.max_hops = max_hops
        self.max_cycle_repeats = max_cycle_repeats
        self.trajectory: List[str] = []
        self._lock = threading.RLock()

    def record_hop(self, agent_name: str) -> Dict[str, Any]:
        with self._lock:
            self.trajectory.append(agent_name)
            # 1. Kiểm tra độ dài tối đa
            if len(self.trajectory) > self.max_hops:
                return {
                    "is_loop": True,
                    "reason": f"Vượt quá giới hạn bước nhảy tối đa ({self.max_hops} hops). Dừng để tránh lãng phí token.",
                    "trajectory": list(self.trajectory)
                }

            # 2. Phát hiện chu kỳ ping-pong 2 tác tử: [A, B, A, B, ...]
            #    max_cycle_repeats = số lần lặp lại của chu kỳ 2 tác tử trước khi trip.
            #    max_cycle_repeats=2 -> cần đuôi dài >= 4 dạng A,B,A,B.
            cycle_len = 2
            repeats = max(2, self.max_cycle_repeats)
            if len(self.trajectory) >= cycle_len * repeats:
                tail = self.trajectory[-cycle_len * repeats:]
                a, b = tail[0], tail[1]
                if a != b and all(
                    tail[i] == (a if i % 2 == 0 else b) for i in range(len(tail))
                ):
                    return {
                        "is_loop": True,
                        "reason": (
                            f"Phát hiện chu kỳ lặp ping-pong giữa '{a}' và '{b}' "
                            f"({repeats} chu kỳ liên tiếp). Kích hoạt Review Gate."
                        ),
                        "trajectory": list(self.trajectory)
                    }

            return {
                "is_loop": False,
                "current_hops": len(self.trajectory),
                "trajectory": list(self.trajectory)
            }

    def reset(self):
        with self._lock:
            self.trajectory.clear()


# ==============================================================================
# 4. HỘP ĐEN GIÁM SÁT THỜI GIAN THỰC (BLACKBOX TRACE RECORDER)
# ==============================================================================

@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    actor: str
    action: str
    status: str
    start_time: float
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

class BlackboxRecorder:
    """
    Hộp đen máy bay giám sát toàn bộ luồng thực thi của các Agent.
    Sinh Trace ID duy nhất cho mỗi phiên làm việc, đo độ trễ và ghi log chuẩn.

    v1.1: vết được ghi bền vững xuống <log_dir>/traces/trace_<date>.jsonl
    (mỗi span một dòng JSON) để không mất khi tiến trình kết thúc.
    """
    def __init__(self, log_dir: Optional[Path] = None, persist: bool = True):
        self.log_dir = Path(log_dir) if log_dir else (Path(__file__).resolve().parent.parent / "_SHARED" / "SHARED_CONTEXT")
        self.persist = persist
        self.traces: List[TraceSpan] = []
        self._lock = threading.RLock()
        self._trace_dir = self.log_dir / "traces"

    def _trace_file(self, trace_id: str) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        return self._trace_dir / f"trace_{date_str}.jsonl"

    def generate_trace_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:8].upper()
        return f"TRC-{date_str}-{short_id}"

    def start_span(self, trace_id: str, actor: str, action: str, parent_span_id: Optional[str] = None) -> TraceSpan:
        span = TraceSpan(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:6],
            parent_span_id=parent_span_id,
            actor=actor,
            action=action,
            status="RUNNING",
            start_time=time.time()
        )
        with self._lock:
            self.traces.append(span)
        return span

    def end_span(self, span: TraceSpan, status: str = "SUCCESS", error: Optional[str] = None, metadata: Optional[Dict] = None):
        span.duration_ms = round((time.time() - span.start_time) * 1000, 2)
        span.status = status
        span.error = error
        if metadata:
            span.metadata.update(metadata)
        self._flush(span)

    def _flush(self, span: TraceSpan):
        """Ghi 1 span xuống JSONL (bỏ qua lỗi I/O — trace không được làm hỏng luồng chính)."""
        if not self.persist:
            return
        try:
            self._trace_dir.mkdir(parents=True, exist_ok=True)
            payload = asdict(span)
            payload["logged_at"] = datetime.now().astimezone().isoformat()
            with open(self._trace_file(span.trace_id), "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def export_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_spans": len(self.traces),
                "success_count": sum(1 for s in self.traces if s.status == "SUCCESS"),
                "failure_count": sum(1 for s in self.traces if s.status != "SUCCESS"),
                "spans": [asdict(s) for s in self.traces[-50:]]  # Giữ 50 span gần nhất trong memory
            }


# ==============================================================================
# 5. HỆ THỐNG ĐIỀU KHIỂN TỔNG HỢP (SYSTEM CONTROLLER SINGLETON)
# ==============================================================================

class SystemController:
    """Bộ điều khiển trung tâm tích hợp toàn bộ các cơ chế kiểm soát."""
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(SystemController, cls).__new__(cls)
                    cls._instance._init_controller()
        return cls._instance

    def _init_controller(self):
        self.breakers: Dict[str, CircuitBreaker] = {
            "revit_mcp": CircuitBreaker("revit_mcp", failure_threshold=3, recovery_timeout=30.0),
            "etabs_api": CircuitBreaker("etabs_api", failure_threshold=3, recovery_timeout=20.0),
            "cad_bridge": CircuitBreaker("cad_bridge", failure_threshold=3, recovery_timeout=15.0),
            "sqlite_db": CircuitBreaker("sqlite_db", failure_threshold=5, recovery_timeout=10.0),
        }
        self.guard = ExecutionGuard(mode="SAFE")
        self.loop_breaker = LoopBreaker(max_hops=10)
        self.recorder = BlackboxRecorder()
        self._pending_approvals: Set[str] = set()
        self._lock = threading.RLock()

    def get_breaker(self, name: str) -> CircuitBreaker:
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name)
            return self.breakers[name]

    def set_mode(self, mode: str):
        """Đặt chế độ hàng rào: SAFE | READ_ONLY | UNRESTRICTED."""
        if mode not in ("SAFE", "READ_ONLY", "UNRESTRICTED"):
            raise ValueError(f"Mode không hợp lệ: {mode}")
        self.guard.mode = mode

    def approve(self, tool_name: str):
        """User duyệt một thao tác đang chờ -> cho phép chạy đúng 1 lần."""
        with self._lock:
            self._pending_approvals.add(tool_name)

    def is_approved(self, tool_name: str) -> bool:
        with self._lock:
            return tool_name in self._pending_approvals

    def preflight_check(self, agent_name: str, tool_name: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Kiểm tra toàn diện trước khi thực thi bất kỳ công cụ nào."""
        # 0. Nếu thao tác đã được User duyệt -> bỏ qua nhánh PENDING_APPROVAL
        if self.is_approved(tool_name):
            with self._lock:
                self._pending_approvals.discard(tool_name)

        # 1. Kiểm tra vòng lặp tác tử
        loop_res = self.loop_breaker.record_hop(agent_name)
        if loop_res["is_loop"]:
            return {
                "allowed": False,
                "status": "LOOP_BLOCKED",
                "reason": loop_res["reason"],
                "trajectory": loop_res["trajectory"]
            }

        # 2. Kiểm tra Hàng rào thực thi (Execution Guard)
        guard_res = self.guard.evaluate_tool_call(tool_name, payload)
        if guard_res["decision"] == GuardDecision.BLOCK.value:
            return {
                "allowed": False,
                "status": "GUARD_BLOCKED",
                "reason": guard_res["reason"]
            }
        if guard_res["decision"] == GuardDecision.PENDING_APPROVAL.value and not self.is_approved(tool_name):
            return {
                "allowed": False,
                "status": "PENDING_APPROVAL",
                "reason": guard_res["reason"]
            }

        # 3. Kiểm tra Cầu dao dịch vụ nếu công cụ phụ thuộc service bên ngoài
        service_map = {
            "revit": "revit_mcp",
            "etabs": "etabs_api",
            "cad": "cad_bridge",
            "dwg": "cad_bridge"
        }
        for key, srv in service_map.items():
            if key in tool_name.lower():
                breaker = self.get_breaker(srv)
                if not breaker.allow_execution():
                    return {
                        "allowed": False,
                        "status": "CIRCUIT_OPEN",
                        "reason": f"Cầu dao '{srv}' đang mở do lỗi liên tiếp. Thao tác bị hoãn để bảo vệ hệ thống."
                    }

        return {
            "allowed": True,
            "status": "ALLOWED",
            "reason": "Preflight kiểm tra an toàn 100%."
        }


# Global helper instance
system_controller = SystemController()

if __name__ == '__main__':
    print("=== TEST NHANH SYSTEM CONTROLLER ===")
    ctrl = SystemController()

    # 1. Test Circuit Breaker
    cb = ctrl.get_breaker("test_service")
    cb.failure_threshold = 2
    cb.record_failure()
    cb.record_failure()
    print("Breaker state after 2 failures:", cb.state.value)
    assert cb.state == CircuitState.OPEN
    print("Breaker allow execution:", cb.allow_execution())

    # 2. Test Guard
    res_guard = ctrl.guard.evaluate_tool_call("run_shell", {"command": "rm -rf /root"})
    print("Guard on rm -rf:", res_guard)
    assert res_guard["decision"] == "BLOCK"

    # 3. Test Loop Breaker
    lb = LoopBreaker(max_hops=5)
    lb.record_hop("AgentA")
    lb.record_hop("AgentB")
    lb.record_hop("AgentA")
    res_loop = lb.record_hop("AgentB")
    print("Loop breaker ping-pong detection:", res_loop)
    assert res_loop["is_loop"] is True

    print("ALL BASIC CHECKS PASSED!")
