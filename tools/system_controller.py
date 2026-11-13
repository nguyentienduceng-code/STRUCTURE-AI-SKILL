# -*- coding: utf-8 -*-
"""
system_controller.py — Bộ Điều Khiển Giám Sát, Cầu Dao An Toàn & Hộp Đen Thực Thi (v2.0)
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
import os
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
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0,
                 recorder: Optional['BlackboxRecorder'] = None):
        import math
        if isinstance(failure_threshold, bool) or not isinstance(failure_threshold, int) or failure_threshold < 1:
            raise ValueError('failure_threshold must be a positive integer')
        if isinstance(recovery_timeout, bool) or not isinstance(recovery_timeout, (int, float)) or not math.isfinite(recovery_timeout) or recovery_timeout < 0:
            raise ValueError('recovery_timeout must be finite and non-negative')
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self._generation = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self._lock = threading.RLock()
        self._half_open_probe_in_flight = False
        self.recorder = recorder if recorder is not None else BlackboxRecorder()

    def record_success(self, trace_id: Optional[str] = None):
        with self._lock:
            prev_state = self.state
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.success_count += 1
            self._half_open_probe_in_flight = False
            if prev_state == CircuitState.HALF_OPEN and self.recorder:
                try:
                    active_trace_id = trace_id or self.recorder.generate_trace_id()
                    span = self.recorder.start_span(
                        trace_id=active_trace_id,
                        actor="CircuitBreaker",
                        action=f"CIRCUIT_RECOVERED:{self.name}"
                    )
                    self.recorder.end_span(
                        span,
                        status="SUCCESS",
                        metadata={
                            "circuit_name": self.name,
                            "event": "CIRCUIT_RECOVERED",
                            "success_count": self.success_count,
                            "recovery_time": datetime.now().astimezone().isoformat()
                        }
                    )
                except Exception:
                    pass

    def record_failure(self, trace_id: Optional[str] = None, error: Optional[str] = None):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self._half_open_probe_in_flight = False
            prev_state = self.state
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                if prev_state != CircuitState.OPEN:
                    self._generation += 1
                if prev_state != CircuitState.OPEN and self.recorder:
                    try:
                        active_trace_id = trace_id or self.recorder.generate_trace_id()
                        span = self.recorder.start_span(
                            trace_id=active_trace_id,
                            actor="CircuitBreaker",
                            action=f"TRIP_CIRCUIT:{self.name}"
                        )
                        next_retry = datetime.fromtimestamp(
                            self.last_failure_time + self.recovery_timeout
                        ).astimezone().isoformat()
                        self.recorder.end_span(
                            span,
                            status="CIRCUIT_OPEN",
                            error=error or f"Circuit '{self.name}' tripped after {self.failure_count} consecutive failures",
                            metadata={
                                "circuit_name": self.name,
                                "event": "TRIP_CIRCUIT",
                                "consecutive_failures": self.failure_count,
                                "threshold": self.failure_threshold,
                                "cooldown_seconds": self.recovery_timeout,
                                "next_retry_after": next_retry
                            }
                        )
                    except Exception:
                        pass

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
                if self.last_failure_time is not None and (time.time() - self.last_failure_time >= self.recovery_timeout):
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
                if self.last_failure_time is not None and (time.time() - self.last_failure_time >= self.recovery_timeout):
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
        return self.call_traced(None, func, *args, **kwargs)

    def call_traced(self, trace_id, func, *args, **kwargs):
        trace_id = trace_id or self.recorder.generate_trace_id()
        with self._lock:
            admitted = self._try_acquire_probe()
            generation = self._generation
        if not admitted:
            span = self.recorder.start_span(trace_id, "CircuitBreaker", f"CIRCUIT_BLOCKED:{self.name}")
            self.recorder.end_span(span, status="CIRCUIT_OPEN", metadata={"circuit_name": self.name})
            raise CircuitBreakerTripped(f"[CIRCUIT_OPEN] Service '{self.name}' is open")
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            with self._lock:
                if generation == self._generation:
                    self.record_failure(trace_id=trace_id, error=repr(error))
            raise
        with self._lock:
            # A success from an older CLOSED window must not close a newly tripped circuit.
            if generation == self._generation:
                self.record_success(trace_id=trace_id)
        return result

    def reset(self):
        with self._lock:
            self._generation += 1
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

class TokenBudget:
    """Atomic admission accounting in tokens. Configure per session; no monetary estimates."""
    def __init__(self, limit=None, throttle_ratio=0.8, throttle_fraction=0.1):
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise ValueError('Token limit must be a non-negative integer or None')
        if not 0 < throttle_ratio < 1 or not 0 < throttle_fraction <= 1:
            raise ValueError('Invalid throttle ratios')
        self.limit, self.used = limit, 0
        self.throttle_ratio, self.throttle_fraction = throttle_ratio, throttle_fraction
        self._lock = threading.RLock()

    def reserve(self, tokens=0):
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
            raise ValueError('Token cost must be a non-negative integer')
        with self._lock:
            before = self.status()
            allowed = self.limit is None or (before['remaining_tokens'] > 0 and
                tokens <= before['remaining_tokens'] and tokens <= before['max_tokens_per_call'])
            if allowed:
                self.used += tokens
            return {**self.status(), 'allowed': allowed, 'reserved_tokens': tokens if allowed else 0,
                    'decision': 'ALLOWED' if allowed else
                        ('BUDGET_THROTTLED' if before['state'] == 'THROTTLED' and
                         tokens <= before['remaining_tokens'] else 'BUDGET_EXHAUSTED')}

    def status(self):
        with self._lock:
            remaining = None if self.limit is None else max(0, self.limit-self.used)
            state = 'NORMAL' if self.limit is None else ('EXHAUSTED' if remaining == 0 else
                'THROTTLED' if self.used >= self.limit*self.throttle_ratio else 'NORMAL')
            cap = remaining
            if state == 'THROTTLED':
                cap = min(remaining, max(1, int(self.limit*self.throttle_fraction)))
            return {'state': state, 'used_tokens': self.used, 'limit_tokens': self.limit,
                    'remaining_tokens': remaining, 'max_tokens_per_call': cap,
                    'recommended_parallel_calls': 1 if state == 'THROTTLED' else None}


class LoopBreaker:
    """v2: repeated multi-agent suffixes, cycle evidence and a sticky hop/cycle breaker.

    max_cycle_repeats preserves v1 semantics (ABAB trips at two periods).
    ABCA already reports cycle_detected; ABCABC trips at two full periods.
    Consecutive calls by a single actor are not treated as multi-agent loops.
    """
    def __init__(self, max_hops=10, max_cycle_repeats=2, token_budget=None):
        for value in (max_hops, max_cycle_repeats):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError('Hop/repeat limits must be positive integers')
        self.max_hops, self.max_cycle_repeats = max_hops, max_cycle_repeats
        self.trajectory = []
        self.budget = TokenBudget(token_budget)
        self._lock = threading.RLock()
        self._tripped = None

    def record_hop(self, agent_name, tokens_used=0):
        if not isinstance(agent_name, str) or not agent_name.strip():
            raise ValueError('Agent name must be non-empty')
        if isinstance(tokens_used, bool) or not isinstance(tokens_used, int) or tokens_used < 0:
            raise ValueError('Token cost must be a non-negative integer')
        with self._lock:
            if self._tripped:
                return {**self._tripped, 'trajectory': list(self.trajectory)}
            budget = self.budget.reserve(tokens_used)
            if not budget['allowed']:
                return {'is_loop': False, 'budget_blocked': True, 'budget': budget,
                        'reason': budget['decision'], 'trajectory': list(self.trajectory)}
            self.trajectory.append(agent_name)
            path = []
            for previous in range(len(self.trajectory)-2, -1, -1):
                if self.trajectory[previous] == agent_name:
                    candidate = self.trajectory[previous:]
                    if len(set(candidate)) > 1:
                        path = candidate
                    break
            result = {'is_loop': False, 'current_hops': len(self.trajectory),
                      'trajectory': list(self.trajectory), 'cycle_detected': bool(path),
                      'cycle_path': path, 'budget': budget}
            if path and self.max_cycle_repeats == 1:
                result.update(is_loop=True, reason=f'Multi-agent cycle: {path}',
                              code='MULTI_AGENT_CYCLE', cycle_length=len(path)-1, cycle_repeats=1)
            if len(self.trajectory) > self.max_hops:
                result.update(is_loop=True, reason=f'Maximum hops exceeded ({self.max_hops})', code='MAX_HOPS')
            else:
                repeats = max(2, self.max_cycle_repeats)
                for size in range(2, len(self.trajectory)//repeats+1):
                    tail = self.trajectory[-size*repeats:]
                    unit = tail[:size]
                    if len(set(unit)) > 1 and tail == unit*repeats:
                        result.update(is_loop=True, cycle_detected=True,
                            cycle_path=unit+[unit[0]], cycle_length=size, cycle_repeats=repeats,
                            reason=f"Repeated {'ping-pong' if size == 2 else 'multi-agent'} cycle: {unit} ({repeats} periods)", code='MULTI_AGENT_CYCLE')
                        break
            if result['is_loop']:
                self._tripped = dict(result)
            return result

    def reset(self, reset_budget=True):
        with self._lock:
            self.trajectory.clear()
            self._tripped = None
            if reset_budget:
                self.budget = TokenBudget(self.budget.limit, self.budget.throttle_ratio,
                                          self.budget.throttle_fraction)


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
    _io_lock = threading.RLock()
    """
    Hộp đen máy bay giám sát toàn bộ luồng thực thi của các Agent.
    Sinh Trace ID duy nhất cho mỗi phiên làm việc, đo độ trễ và ghi log chuẩn.

    v1.1: vết được ghi bền vững xuống <log_dir>/traces/trace_<date>.jsonl
    (mỗi span một dòng JSON) để không mất khi tiến trình kết thúc.
    """
    def __init__(self, log_dir: Optional[Path] = None, persist: bool = True, max_trace_files: int = 30):
        self.log_dir = Path(log_dir) if log_dir else (Path(__file__).resolve().parent.parent / "_SHARED" / "SHARED_CONTEXT")
        self.persist = persist
        self.max_trace_files = max_trace_files
        self.persistence_errors: List[str] = []
        self.traces: List[TraceSpan] = []
        self._lock = threading.RLock()
        self._trace_dir = self.log_dir / "traces"
        self._last_rotation_date: Optional[str] = None

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

    def rotate_traces(self, max_files: Optional[int] = None, max_age_days: int = 14) -> List[str]:
        """
        Xoay vòng và dọn dẹp các file trace cũ hơn max_age_days
        hoặc khi số lượng file vượt quá max_files.
        Trả về danh sách tên file đã dọn dẹp.
        """
        if not self._trace_dir.is_dir():
            return []

        limit = max_files if max_files is not None else self.max_trace_files
        removed: List[str] = []
        with self._lock:
            try:
                trace_files = sorted(self._trace_dir.glob("trace_*.jsonl"), key=lambda p: p.stat().st_mtime)
                now = time.time()
                remaining = []
                for p in trace_files:
                    try:
                        mtime = p.stat().st_mtime
                        if (now - mtime) > (max_age_days * 86400):
                            p.unlink(missing_ok=True)
                            removed.append(p.name)
                        else:
                            remaining.append(p)
                    except OSError:
                        remaining.append(p)

                if limit and len(remaining) > limit:
                    excess = len(remaining) - limit
                    for p in remaining[:excess]:
                        try:
                            p.unlink(missing_ok=True)
                            removed.append(p.name)
                        except OSError:
                            pass
            except OSError:
                pass
        return removed

    def _flush(self, span: TraceSpan):
        """Serialize appends across recorder instances in this process; expose I/O errors."""
        if not self.persist:
            return
        try:
            with self._io_lock:
                self._trace_dir.mkdir(parents=True, exist_ok=True)
                today = datetime.now().strftime("%Y%m%d")
                if self._last_rotation_date != today:
                    self._last_rotation_date = today
                    self.rotate_traces()
                payload = asdict(span)
                payload["logged_at"] = datetime.now().astimezone().isoformat()
                with open(self._trace_file(span.trace_id), "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
        except OSError as error:
            with self._lock:
                self.persistence_errors.append(str(error))

    def export_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_spans": len(self.traces),
                "persistence_errors": list(self.persistence_errors),
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
        self.recorder = BlackboxRecorder()
        self.breakers: Dict[str, CircuitBreaker] = {
            "revit_mcp": CircuitBreaker("revit_mcp", failure_threshold=3, recovery_timeout=30.0, recorder=self.recorder),
            "etabs_api": CircuitBreaker("etabs_api", failure_threshold=3, recovery_timeout=20.0, recorder=self.recorder),
            "cad_bridge": CircuitBreaker("cad_bridge", failure_threshold=3, recovery_timeout=15.0, recorder=self.recorder),
            "sqlite_db": CircuitBreaker("sqlite_db", failure_threshold=5, recovery_timeout=10.0, recorder=self.recorder),
        }
        self.guard = ExecutionGuard(mode="SAFE")
        self.loop_breaker = LoopBreaker(max_hops=10)
        self._sessions = {}
        self._default_trace_id = self.recorder.generate_trace_id()
        self._pending_approvals: Set[str] = set()
        self._lock = threading.RLock()

    def get_breaker(self, name: str) -> CircuitBreaker:
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, recorder=self.recorder)
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

    def start_session(self, session_id=None, token_budget=None, max_hops=100, max_cycle_repeats=2):
        session_id = session_id or uuid.uuid4().hex
        with self._lock:
            if session_id in self._sessions:
                raise ValueError('Session already exists')
            loop = LoopBreaker(max_hops, max_cycle_repeats, token_budget)
            self._sessions[session_id] = {'loop': loop, 'trace_id': self.recorder.generate_trace_id()}
        return session_id

    def end_session(self, session_id):
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _session(self, session_id):
        if session_id is None:
            return {'loop': self.loop_breaker, 'trace_id': self._default_trace_id}
        if session_id not in self._sessions:
            raise ValueError('Unknown session; call start_session first')
        return self._sessions[session_id]

    @staticmethod
    def _service(tool_name):
        for key, service in [('revit', 'revit_mcp'), ('etabs', 'etabs_api'),
                             ('cad', 'cad_bridge'), ('dwg', 'cad_bridge')]:
            if key in tool_name.lower():
                return service
        return None

    def _control_event(self, trace_id, action, status, metadata):
        span = self.recorder.start_span(trace_id, 'SystemController', action)
        self.recorder.end_span(span, status=status, metadata=metadata)

    def preflight_check(self, agent_name, tool_name, payload=None, session_id=None,
                        estimated_tokens=0, trace_id=None):
        """Admission + token reservation are atomic; rejected requests keep approval tickets."""
        with self._lock:
            session = self._session(session_id)
            trace_id = trace_id or session['trace_id']
            loop = session['loop']
            # Reject invalid token accounting before mutating any state.
            if isinstance(estimated_tokens, bool) or not isinstance(estimated_tokens, int) or estimated_tokens < 0:
                raise ValueError('estimated_tokens must be a non-negative integer')
            def reject(status, reason, **extra):
                self._control_event(trace_id, status, status,
                    {'tool': tool_name, 'agent': agent_name, 'session_id': session_id,
                     'reason': reason, **extra})
                return {'allowed': False, 'status': status, 'reason': reason,
                        'trace_id': trace_id, **extra}
            guard = self.guard.evaluate_tool_call(tool_name, payload)
            if guard['decision'] == GuardDecision.BLOCK.value:
                return reject('GUARD_BLOCKED', guard['reason'])
            if guard['decision'] == GuardDecision.PENDING_APPROVAL.value and tool_name not in self._pending_approvals:
                return reject('PENDING_APPROVAL', guard['reason'])
            service = self._service(tool_name)
            if service and not self.get_breaker(service).allow_execution():
                return reject('CIRCUIT_OPEN', f'Circuit {service} is open')
            # A loop check with zero token cost does not spend a reservation twice.
            outcome = loop.record_hop(agent_name)
            if outcome['is_loop']:
                return reject('LOOP_BLOCKED', outcome['reason'], trajectory=outcome['trajectory'])
            if outcome.get('budget_blocked'):
                return reject(outcome['budget']['decision'], outcome['reason'], budget=outcome['budget'])
            budget = loop.budget.reserve(estimated_tokens)
            if not budget['allowed']:
                return reject(budget['decision'], 'Token admission denied', budget=budget)
            if guard['decision'] == GuardDecision.PENDING_APPROVAL.value:
                self._pending_approvals.discard(tool_name)
            if budget['state'] == 'THROTTLED':
                self._control_event(trace_id, 'BUDGET_THROTTLED', 'THROTTLED', budget)
            return {'allowed': True, 'status': 'ALLOWED', 'reason': 'Preflight checks passed',
                    'trace_id': trace_id, 'budget': budget}

    def execute(self, agent_name, tool_name, func, *args, session_id=None,
                estimated_tokens=0, payload=None, **kwargs):
        """Integrated execution path. Reservations charge every admitted attempt, even failures."""
        admission = self.preflight_check(agent_name, tool_name, payload, session_id, estimated_tokens)
        if not admission['allowed']:
            return admission
        trace_id = admission['trace_id']
        span = self.recorder.start_span(trace_id, agent_name, tool_name)
        try:
            service = self._service(tool_name)
            result = self.get_breaker(service).call_traced(trace_id, func, *args, **kwargs) if service else func(*args, **kwargs)
            self.recorder.end_span(span, status='SUCCESS', metadata={'reserved_tokens': estimated_tokens})
            return {'allowed': True, 'status': 'SUCCESS', 'result': result, 'trace_id': trace_id}
        except Exception as error:
            self.recorder.end_span(span, status='FAILURE', error=repr(error))
            raise



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
