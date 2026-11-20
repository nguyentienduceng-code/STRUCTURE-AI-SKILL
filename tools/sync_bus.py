# .agents/tools/sync_bus.py
# Giao thức Cầu nối File (File-based IPC Bus) giữa Claude Code và Gemini Antigravity
#
# ⚠ SSOT v3.2.0 — File này (thư mục .agents/tools/) là NGUỒN SỰ THẬT DUY NHẤT
#   (Single Source of Truth) cho toàn bộ logic của bus Dual-Agent.
#   Bản tại .agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py là THIN WRAPPER
#   chỉ đại diện CLI + import, KHÔNG chứa logic riêng. Mọi bảo trì logic
#   (bugfix, feature) phải thực thi tại file này, rồi đồng bộ lại cho
#   wrapper (wrapper tự động import file này, nên chỉ cần sửa 1 nơi).
#
# v3.2.0 (Architecture Upgrade — Research Proposal DUAL_AGENT_V32):
#   1. SSOT Khử trùng lặp: .agents/tools/sync_bus.py là duy nhất; bản trong
#      skills/scripts/sync_bus.py là thin wrapper.
#   2. Heartbeat / Lease Timeout: ca IN_PROGRESS kèm `lease_expire_at`
#      (mặc định 60 phút, env DUAL_AGENT_LEASE_MIN override). Khi lease hết hạn,
#      tác tử đối tác được auto-claim KHÔNG cần --force. Lệnh --heartbeat
#      để holder gia hạn.
#   3. Project-Scoped Path Resolver: cờ --project-dir <path> giúp chuẩn hóa
#      mọi artifacts về gốc workspace; `detect_modified_files` thu hẹp phạm vi
#      scan về đúng dự án (tránh gom nhầm artifact dự án khác).
#   4. Visual Gate & Bằng chứng Nghiệm thu (Điều 12d Enforcer): khi task thuộc
#      nhóm CAD/Bản vẽ/Báo cáo, bắt buộc có >=1 bằng chứng (preview .png/.jpg
#      / log nghiệm thu _verification.json) trong artifacts_modified trước khi
#      đặt PENDING / NEED_REVIEW / COMPLETED. --force để bỏ qua.
#
# v3.0 (Enterprise Dual-Agent Autonomous Collaboration & Anti-Collision Engine):
#   - Trạng thái bàn giao vòng đời hoàn chỉnh (handoff_status):
#     Hỗ trợ 4 trạng thái: PENDING, IN_PROGRESS, COMPLETED, NEED_REVIEW.
#     Thêm cờ current_holder & cơ chế Software Mutex chống 2 AI ghi đè/lệch nhịp.
#   - Chuẩn hóa đường dẫn tương đối (Relative POSIX Paths):
#     artifacts_modified chuyển 100% sang đường dẫn tương đối từ workspace root với '/',
#     tiết kiệm >75% token context và triệt tiêu lỗi escape ký tự \\ trong JSON trên Windows.
#   - Cấu trúc hóa lệnh giao việc kèm Tiêu chí Nghiệm thu (acceptance_criteria):
#     next_action_for_partner tách bạch: task_description, target_files, acceptance_criteria
#     và tự động render bảng checklist checkbox [-] trong DUAL_AGENT_HANDOFF_MEMO.md.
#   - Phòng ngừa và Xử lý Xung đột Google Drive (Drive Conflict Prevention & Resolver):
#     Ghi nguyên tử an toàn với tiền tố ẩn, tích hợp bộ quét và dọn dẹp file xung đột (1), (2)
#     thông minh (ưu tiên bản sửa đổi mới nhất, sao lưu an toàn, không xóa nhầm code).
#   - Tương thích ngược 100%: Toàn bộ API v1.0, v2.0 và CLI cũ hoạt động trơn tru.
#
# Usage:
#   # Đọc trạng thái bus:
#   python .agents/tools/sync_bus.py --read
#
#   # Tác tử nhận ca (khóa bus tránh đối tác ghi đè):
#   python .agents/tools/sync_bus.py --claim --agent CLAUDE
#
#   # Hoàn tất ca làm việc:
#   python .agents/tools/sync_bus.py --complete --agent CLAUDE --summary "Đã xong"
#
#   # Yêu cầu kiểm tra chéo / phê duyệt:
#   python .agents/tools/sync_bus.py --need-review --agent CLAUDE
#
#   # Bàn giao tự động v3.0 với tiêu chí nghiệm thu:
#   python .agents/tools/sync_bus.py --auto --sender GEMINI --target CLAUDE \
#       --project 00_MANAGEMENT_QLTK --purpose "Nâng cấp giao thức Bus v3.0" \
#       --task "Kiểm tra chéo và chuẩn hóa line ending" \
#       --criteria "100% test Suite PASS;Không còn file xung đột Drive" --confirm
#
#   # Quét và xử lý file xung đột Google Drive (1), (2):
#   python .agents/tools/sync_bus.py --scan-conflicts
#   python .agents/tools/sync_bus.py --clean-conflicts --confirm

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Đảm bảo UTF-8 theo Quy tắc AGENTS.md
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def _local_state_dir() -> str:
    """Thư mục trạng thái cục bộ (KHÔNG nằm trên ổ Google Drive)."""
    import tempfile
    return os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()


# Khoá nằm ở ổ đĩa LOCAL (không phải ổ Drive đồng bộ) — theo yêu cầu vá CVE.
LOCK_DIR = Path(_local_state_dir()) / "GoogleAIStudio" / "locks"
LOCK_FILENAME = "dual_agent_bus.lock"
LOCK_TIMEOUT_SEC = 15.0

# ==============================================================================
# v3.2.0 — HẰNG SỐ NÂNG CẤP (Lease/Heartbeat, Project Scope, Visual Gate)
# ==============================================================================

# Thời hạn thuê ca mặc định (phút) khi không có heartbeat. Agent đối tác được
# quyền auto-claim (không cần --force) khi lease hết hạn — chống ca treo vĩnh viễn.
LEASE_DURATION_MIN_DEFAULT = 60
LEASE_DURATION_ENV = "DUAL_AGENT_LEASE_MIN"  # override thời hạn thuê ca (phút)


def _parse_iso(value: str) -> Optional[datetime]:
    """Parse ISO-8601 an toàn (hỗ trợ 'Z'); trả None nếu sai định dạng."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _lease_duration_min() -> int:
    """Thời hạn thuê ca (phút): đọc từ env DUAL_AGENT_LEASE_MIN, mặc định 60."""
    try:
        raw = os.environ.get(LEASE_DURATION_ENV, "").strip()
        return max(1, int(raw)) if raw else LEASE_DURATION_MIN_DEFAULT
    except Exception:
        return LEASE_DURATION_MIN_DEFAULT


def _now_aware() -> datetime:
    return datetime.now().astimezone()


def _is_lease_expired(data: dict) -> bool:
    """
    Ca IN_PROGRESS có HẾT HẠN THUÊ (lease) hay không?
    - Có `lease_expire_at` (bản v3.2+): so sánh tuyệt đối với giờ hiện tại.
    - Chỉ có `last_heartbeat` / `claim_timestamp` / `timestamp` (bản v3.0):
      tính cửa sổ theo LEASE_DURATION (mặc định 60 phút).
    - Không có mốc thời gian nào (bus legacy): trả False (VẪN BẢO VỆ —
      yêu cầu --force để tiếp quản, tránh ghi đè một ca treo không rõ nguồn gốc).
    """
    if str(data.get("handoff_status", "")).upper() != "IN_PROGRESS":
        return False
    now = _now_aware()
    exp = _parse_iso(str(data.get("lease_expire_at", "")))
    if exp is not None:
        return exp <= now
    anchor = _parse_iso(str(data.get("last_heartbeat", "")))
    if anchor is None:
        anchor = _parse_iso(str(data.get("claim_timestamp", "")))
    if anchor is None:
        anchor = _parse_iso(str(data.get("timestamp", "")))
    if anchor is None:
        return False  # bus không có mốc thời gian -> vẫn giữ bảo vệ
    return (now - anchor).total_seconds() > LEASE_DURATION_MIN_DEFAULT * 60


# Bộ nhận diện task nhóm CAD/Bản vẽ/Báo cáo (Visual & Real-Model Gate — Điều 12d).
CAD_TASK_KEYWORDS = (
    "cad", "bản vẽ", "ban ve", "blueprint", "dwg", "dxf",
    "dce", "render", "preview", "kết cấu 2d", "sheet",
)
# Mẫu bằng chứng nghiệm thu bắt buộc khi bàn giao task CAD:
CAD_EVIDENCE_PATTERN = re.compile(
    r"(\.png|\.jpg|\.jpeg|\.webp|\.preview\.log|_verification\.json)", re.IGNORECASE
)

# ==============================================================================
# v3.3 — HẰNG SỐ NÂNG CẤP CẤP 2 (Evidence-Based Gate, Receipts, Product-First)
# ==============================================================================

# Các action_type (khai báo tường minh trong project_context) BẮT BÚỘC qua
# Visual Gate (cần bằng chứng nghiệm thu thật). Khi action_type trống/mặc định
# (DYNAMIC, RELAY, PARALLEL, AUDIT) -> fallback về dò keyword (hành vi v3.2).
GATED_ACTION_TYPES = {"CAD", "DRAWING", "CAD_DRAWING", "DOCX", "REPORT_VISUAL"}
# Các action_type loại bỏ rõ ràng khỏi Gate (meta/code-only):
EXEMPT_ACTION_TYPES = {"CODE", "META", "INFRA", "TEST", "DOCS"}
# Trạng thái bus sinh RECEIPT tự động (kết quả nghiệm thu / bàn giao chính thức):
RECEIPT_STATUSES = {"NEED_REVIEW", "COMPLETED"}

# ==============================================================================
# v3.3 — HẰNG SỐ NÂNG CẤP CẤP 3 (REPORT GATE: chuẩn RESULT.md theo ca)
# ==============================================================================

# Thư mục gốc lưu báo cáo pha (chuẩn hóa mẫu cad_v6: G1/C1/A1_RESULT.md).
# Cạnh: `.agents/memory/audits/<project_code_lower>/<agent_lower>/`
RESULTS_AUDIT_ROOT = ".agents/memory/audits"
# Hậu tố chuẩn cho file báo cáo pha theo ca (kèm số hiệu pha nếu có):
RESULT_FILENAME_TEMPLATE = "{phase}_{agent}_RESULT.md"
# 5 mục CỐ ĐỊNH của một RESULT.md (chuẩn hóa để Codex/đối tác đọc máy được):
RESULT_SECTIONS = (
    "SCOPE_DELIVERED",        # 1. Phạm vi & sản phẩm đã bàn giao (deliverable)
    "VERIFICATION_COMMAND",   # 2. Lệnh chạy lại được để tự chứng minh (acceptance_cmd)
    "RESULTS",               # 3. Kết quả ĐO ĐƯỢC (số liệu, PASS/FAIL, log)
    "CONSTRAINTS",           # 4. Ràng buộc / giới hạn của ca (không làm gì, vì sao)
    "HANDOFF_CONTRACT",      # 5. Hợp đồng giao diện cho ca kế tiếp (interface, fixture)
)




# ==============================================================================
# 1. KHOÁ TỆP TỐI GIẢN (không cần thư viện ngoài)
# ==============================================================================

class FileLock:
    """
    Khoá tệp tối giản, đa nền tảng.
    - Windows: dùng msvcrt.locking trên 1 byte đầu file.
    - POSIX:   dùng fcntl.flock.
    - Fallback: tạo file khoá với O_CREAT|O_EXCL (kém hơn nhưng vẫn chống race cơ bản).
    """

    def __init__(self, path: Path, timeout: float = LOCK_TIMEOUT_SEC):
        self.path = Path(path)
        self.timeout = timeout
        self._fh = None
        self._fallback_fd = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    self._fh = open(self.path, "a+b")
                    self._fh.seek(0)
                    try:
                        msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
                    except OSError:
                        self._fh.close()
                        self._fh = None
                        if time.time() >= deadline:
                            return False
                        time.sleep(0.1)
                        continue
                else:
                    import fcntl
                    self._fh = open(self.path, "a+b")
                    try:
                        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except OSError:
                        self._fh.close()
                        self._fh = None
                        if time.time() >= deadline:
                            return False
                        time.sleep(0.1)
                        continue
                return True
            except ImportError:
                # Fallback: khoá theo tên file (O_CREAT|O_EXCL).
                # msvcrt/flock tự nhả khi process chết, nhưng file khoá O_EXCL
                # thì KHÔNG — process chết giữa acquire/release sẽ để lại khóa
                # treo vĩnh viễn. Vì vậy: file khóa quá tuổi (mỗi lần ghi khi
                # acquire thành công làm mới mtime; holder hợp lệ luôn giữ mtime
                # mới trong deadline) được coi là rơi -> chiếm lại (unlink + retry).
                try:
                    self._fallback_fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    return True
                except FileExistsError:
                    try:
                        st = self.path.stat()
                        if time.time() - st.st_mtime > max(60.0, 4.0 * self.timeout):
                            os.unlink(str(self.path))  # khóa đã rơi
                            # vòng lặp retry O_EXCL ngay (không sleep)
                            continue
                    except OSError:
                        pass  # stat/unlink fail (đang bị chiếm hợp lệ) -> chờ
                    if time.time() >= deadline:
                        return False
                    time.sleep(0.1)

    def release(self) -> None:
        try:
            if self._fh is not None:
                if os.name == "nt":
                    import msvcrt
                    self._fh.seek(0)
                    try:
                        msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
                else:
                    import fcntl
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                self._fh.close()
                self._fh = None
            if self._fallback_fd is not None:
                os.close(self._fallback_fd)
                try:
                    os.unlink(str(self.path))
                except OSError:
                    pass
                self._fallback_fd = None
        except Exception:
            pass

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Không thể giành khoá file '{self.path}' trong {self.timeout}s.")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


# ==============================================================================
# 2. ĐỊNH TUYẾN THƯ MỤC & CHUẨN HÓA ĐƯỜNG DẪN TƯƠNG ĐỐI
# ==============================================================================

def find_workspace_root() -> Path:
    """Resolve the project root consistently from nested or external callers."""
    env_ws = os.environ.get("DUAL_AGENT_WORKSPACE")
    if env_ws:
        root = Path(env_ws).resolve()
        if not root.is_dir():
            raise ValueError("DUAL_AGENT_WORKSPACE is not a directory")
        return root.parent if root.name == '.agents' else root
    for start in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for candidate in (start, *start.parents):
            if (candidate / '.agents').is_dir():
                return candidate
    raise FileNotFoundError("Cannot locate workspace containing .agents")


WORKSPACE_ROOT = find_workspace_root()

def get_bus_paths(ws_root: Path) -> tuple[Path, Path]:
    agents_mem = ws_root / ".agents" / "memory"
    if (agents_mem / "DUAL_AGENT_BUS.json").exists() or agents_mem.is_dir():
        return agents_mem / "DUAL_AGENT_BUS.json", agents_mem / "DUAL_AGENT_HANDOFF_MEMO.md"
    return ws_root / "memory" / "DUAL_AGENT_BUS.json", ws_root / "memory" / "DUAL_AGENT_HANDOFF_MEMO.md"

BUS_PATH, MEMO_PATH = get_bus_paths(WORKSPACE_ROOT)
LOCK_PATH = LOCK_DIR / LOCK_FILENAME


def normalize_path(raw_path: str, workspace_root: Path = WORKSPACE_ROOT) -> str:
    """
    Chuẩn hóa đường dẫn tuyệt đối (duy trì tương thích ngược 100%):
    - Loại bỏ tiền tố ổ đĩa cũ (ví dụ H:\\My Drive\\AI AGENT -> G:\\My Drive\\Google AI Studio)
    - Quy đổi đường dẫn tương đối thành tuyệt đối.
    """
    p_str = str(raw_path).strip()
    if not p_str:
        return ""

    old_prefixes = [
        "H:\\My Drive\\AI AGENT",
        "h:\\my drive\\ai agent",
        "H:/My Drive/AI AGENT",
        "h:/my drive/ai agent"
    ]
    for old_pre in old_prefixes:
        if p_str.lower().startswith(old_pre.lower()):
            rel_part = p_str[len(old_pre):].lstrip("\\/")
            return str(workspace_root / rel_part)

    p = Path(p_str)
    if not p.is_absolute():
        return str(workspace_root / p)
    return str(p)


def to_relative_path(raw_path: str, workspace_root: Path = WORKSPACE_ROOT) -> str:
    """
    Chuẩn hóa đường dẫn thành tương đối từ workspace_root sử dụng ký tự gạch chéo xuôi (POSIX /).
    Loại bỏ tiền tố ổ đĩa cũ (H:\\...), giải quyết triệt để lỗi escape ký tự \\ trên Windows và tiết kiệm token context.
    """
    p_str = str(raw_path).strip()
    if not p_str:
        return ""

    old_prefixes = [
        "H:\\My Drive\\AI AGENT",
        "h:\\my drive\\ai agent",
        "H:/My Drive/AI AGENT",
        "h:/my drive/ai agent"
    ]
    for old_pre in old_prefixes:
        if p_str.lower().startswith(old_pre.lower()):
            rel_part = p_str[len(old_pre):].lstrip("\\/")
            return Path(rel_part).as_posix()

    p = Path(p_str)
    if not p.is_absolute():
        return p.as_posix()

    try:
        rel = os.path.relpath(str(p), str(workspace_root))
        if not rel.startswith(".."):
            return Path(rel).as_posix()
    except Exception:
        pass

    return p.as_posix()


def _atomic_write_json(path: Path, payload: dict) -> None:
    """
    Ghi JSON nguyên tử và an toàn với Google Drive sync:
    - Ghi file tạm ẩn (.dual_agent_bus.tmp.{pid}) cùng thư mục để os.replace() nguyên tử.
    - fsync đảm bảo dữ liệu ghi trọn vẹn xuống đĩa trước khi thay thế.
    - Tự động dọn dẹp các bản sao xung đột Google Drive của chính file này (nếu có).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Tên ẩn giúp Google Drive hạn chế bắt lock sync giữa chừng
    tmp_path = path.with_name(f".{path.stem}.tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    # Dọn dẹp bản sao xung đột tức thì trong cùng thư mục (ví dụ DUAL_AGENT_BUS (1).json)
    try:
        pat = re.compile(rf"^{re.escape(path.stem)}\s\(\d+\){re.escape(path.suffix)}$")
        for f in path.parent.iterdir():
            if pat.match(f.name):
                try:
                    f.unlink()
                except OSError:
                    pass
    except Exception:
        pass


def _atomic_write_text(path: Path, text: str) -> None:
    """
    Ghi text nguyên tử (temp ẩn + fsync + os.replace), an toàn với Google Drive sync.
    Dùng cho `.md` (handoff memo) — tránh file ghi dở giữa chừng khi Drive bắt lock
    sync (một file `.md` ghi nửa đường không thể đọc được bởi đối tác).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


# ==============================================================================
# 2.5. TRỢ LÝ VISUAL GATE & LEASE / HEARTBEAT (v3.2.0)
# ==============================================================================

def _is_cad_task(*texts: str) -> bool:
    """Task có thuộc nhóm CAD/Bản vẽ/Báo cáo (cần Visual Gate) không?"""
    blob = " ".join(t for t in texts if t).lower()
    return any(k in blob for k in CAD_TASK_KEYWORDS)


def _receipts_dir(ws_root: Path = WORKSPACE_ROOT) -> Path:
    """
    v3.3 — Thư mục RECEIPTS (phiếu nghiệm thu) chuẩn:
    `.agents/_SHARED/SHARED_CONTEXT/_active/RECEIPTS/` (đã tồn tại trong repo,
    hiện đang trống -> được kích hoạt ở đây). Fallback `.agents/_active_receips/`
    nếu cây _SHARED chưa có (workspace test).
    """
    primary = ws_root / ".agents" / "_SHARED" / "SHARED_CONTEXT" / "_active" / "RECEIPTS"
    if (ws_root / ".agents" / "_SHARED" / "SHARED_CONTEXT").is_dir() or primary.exists():
        return primary
    return ws_root / ".agents" / "_active_receips"


def _gate_action_type(payload: dict) -> str:
    """Đọc action_type khai báo (project_context) — chữ hoa để so khớp."""
    return str((payload.get("project_context") or {}).get("action_type", "")).strip().upper()


def _gate_applies(payload: dict) -> bool:
    """
    v3.3 — Gate có kích hoạt cho payload này không?
    - EXEMPT tường minh (CODE/META/TEST/DOCS/INFRAStructure) -> KHÔNG kích hoạt.
    - GATED tường minh (CAD/DRAWING/DOCX/REPORT_VISUAL) -> KÍCH HOẠT.
    - Mặc định/không khai báo (DYNAMIC, RELAY, PARALLEL, AUDIT, ...) ->
      fallback dò keyword (hành vi v3.2, giữ tương thích ngược 100%).
    """
    act = _gate_action_type(payload)
    if act in EXEMPT_ACTION_TYPES:
        return False
    if act in GATED_ACTION_TYPES:
        return True
    task = payload.get("next_action_for_partner", {})
    return _is_cad_task(
        task.get("task_description", ""),
        task.get("command", ""),
        payload.get("summary", ""),
        payload.get("project_context", {}).get("project_purpose", ""),
    )


def _evidence_candidates(payload: dict) -> List[str]:
    """
    Danh sách bằng chứng candidate = union(evidence_files khai báo,
    artifacts_modified). Chuẩn hóa về đường dẫn tuyệt đối để kiểm tra đĩa.
    """
    task = payload.get("next_action_for_partner", {})
    raw = list(task.get("evidence_files") or []) + list(payload.get("artifacts_modified") or [])
    seen: List[str] = []
    for r in raw:
        rp = to_relative_path(str(r), WORKSPACE_ROOT)
        if rp and rp not in seen:
            seen.append(rp)
    return seen


def visual_gate_check(
    payload: dict,
    workspace_root: Path = WORKSPACE_ROOT,
    check_on_disk: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Visual & Real-Model Gate v2 (Evidence-Based, Điều 12d — Bài học 2026-11-15,
    nâng cấp v3.3 theo DUAL_AGENT_ANTIGRAVITY_ORCHESTRATION_ANALYSIS.md).

    Logic 3 tầng:
      1. Kích hoạt: theo action_type (CAD/DOCX -> bắt buộc; CODE/META -> miễn)
         hoặc fallback keyword (hành vi v3.2) khi không khai báo.
      2. Bằng chứng: cần >=1 file (a) nằm trong evidence_files/artifacts_modified
         KHỚP CAD_EVIDENCE_PATTERN (.png/.jpg/_verification.json/.preview.log)
         HOẶC (b) `check_on_disk=True`: file bằng chứng THẬT SỰ TỒN TẠI TRÊN ĐĨA
         (tính SHA-256) — không chấp nhận danh khai suông.
      3. Kết quả: (đạt_cờ, danh_mục_thiếu). Lỗi file (không tồn tại khi
         check_on_disk) được ghi vào missing kèm lý do, không crash.
    """
    missing: List[str] = []
    if not _gate_applies(payload):
        return True, missing

    cands = _evidence_candidates(payload)
    # Tầng danh khai: khớp pattern hình ảnh/log
    pattern_hits = [c for c in cands if CAD_EVIDENCE_PATTERN.search(c)]
    if pattern_hits:
        # v3.3: nếu bật kiểm đĩa, file phải TỒN TẠI + được băm (bằng chứng thật)
        if check_on_disk:
            ok_files, bad_files = _verify_evidence_on_disk(cands, workspace_root)
            if not ok_files:
                missing.append("evidence_on_disk (mọi candidate bằng chứng không tồn tại trên đĩa)")
            else:
                missing.append("OK: " + ", ".join(Path(x[0]).name for x in ok_files[:8]))
            for bf, reason in bad_files:
                missing.append(f"MISSING_FILE: {Path(bf).name} ({reason})")
            return (not any(m.startswith("MISSING_FILE") or m.startswith("evidence_on_disk") for m in missing)), missing
        return True, missing

    # Không có pattern hit: thử kiếm bằng chứng trên đĩa (nâng cấp v3.3)
    if check_on_disk:
        ok_files, _ = _verify_evidence_on_disk(cands, workspace_root)
        if ok_files:
            return True, missing
        missing.append("evidence (>=1 preview .png/.jpg hoặc log _verification.json — danh khai + tồn tại trên đĩa)")
        return False, missing

    # v3.2 backward-compat: danh khai suông
    missing.append("visual_gate_evidence (>=1 .png preview / log nghiệm thu)")
    return False, missing


def _verify_evidence_on_disk(
    candidates_rel: List[str], workspace_root: Path = WORKSPACE_ROOT
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    v3.3 — Kiểm tra bằng chứng trên đĩa (SHA-256).
    Trả về (ok_files, bad_files): ok = [(rel_path, sha256)] đủ để ghi receipt;
    bad = [(rel_path, lý_do)] các file khai báo nhưng không tìm thấy/hỏng.
    Một candidate được chấp nhận khi (a) khớp CAD_EVIDENCE_PATTERN và tồn tại,
    hoặc (b) tồn tại trên đĩa (bằng chứng audit .json/.log/.dxg... được ghi nhận
    để receipt, chỉ được ĐẾM khi có kèm file preview/log — theo Điều 12d).
    """
    ok_files: List[Tuple[str, str]] = []
    bad_files: List[Tuple[str, str]] = []
    for rel in candidates_rel:
        # Chỉ file BẰNG CHỨNG (khớp CAD_EVIDENCE_PATTERN) mới được kiểm đếm;
        # artifact thường (code, DXF, JSON...) bị bỏ qua — không phải bằng
        # chứng visual, việc thiếu chúng không làm sai Visual Gate.
        if not CAD_EVIDENCE_PATTERN.search(rel):
            continue
        try:
            fp = Path(workspace_root) / rel
            if fp.exists() and fp.is_file():
                ok_files.append((rel, _file_hash(fp)))
            else:
                bad_files.append((rel, "không tồn tại trên đĩa"))
        except Exception as exc:
            bad_files.append((rel, f"không đọc được: {exc}"))
    return ok_files, bad_files


def _evidence_hashes(payload: dict, workspace_root: Path = WORKSPACE_ROOT) -> Dict[str, Optional[str]]:
    """
    v3.3 — Băm SHA-256 các bằng chứng candidate (evidence_files + artifacts_modified)
    để ghi vào RECEIPT. Trả về {rel_path: sha256|None}:
    - sha256: file bằng chứng (khớp CAD_EVIDENCE_PATTERN) TỒN TẠI trên đĩa.
    - None   : file không tồn tại / không đọc được / không phải bằng chứng visual.
    """
    cands = _evidence_candidates(payload)
    ok_files, _bad = _verify_evidence_on_disk(cands, workspace_root)
    hashes: Dict[str, Optional[str]] = {rel: None for rel in cands}
    for rel, digest in ok_files:
        hashes[rel] = digest
    return hashes


def write_receipt(
    payload: dict,
    gate_result,
    reason: str = "",
    force_used: bool = False,
    workspace_root: Path = WORKSPACE_ROOT,
) -> Optional[Path]:
    """
    v3.3 — Ghi RECEIPT (phiếu nghiệm thu) vào RECEIPTS/ (khóa cứng Điều 12d).

    Sinh khi nào:
      - ca NEED_REVIEW / COMPLETED (kết quả nghiệm thu chính thức), HOẶC
      - BẮT BUỘC khi --force (mọi bypass gate phải có dấu vết audit: hash bằng
        chứng SHA-256 + lý do + chữ ký agent) — chống bypass "vô danh" của v3.2.

    Tham số:
      - payload     : bus payload hiện tại.
      - gate_result : tuple (gate_ok, gate_missing) từ visual_gate_check, hoặc
                      dict {gate_passed, gate_missing} (phòng thủ).
      - reason      : lý do khi force_used (ghi vào receipt để audit).
      - force_used  : True nếu ca được ghi đè/bypass (kể cả bypass IN_PROGRESS).

    RECEIPT lưu: trạng thái gate, danh mục thiếu, hash bằng chứng, cờ force +
    lý do, hash bus, chữ ký. Tên file: RECEIPT_<sender>_<status>_<ts>.json
    Trả về Path receipt (None nếu không phải lúc sinh / không ghi được).
    """
    # Giải mã gate_result (tuple (ok, missing) hoặc dict {gate_passed, gate_missing})
    if isinstance(gate_result, dict):
        gate_ok = bool(gate_result.get("gate_passed", False))
        gate_missing = list(gate_result.get("gate_missing", []))
    elif isinstance(gate_result, (tuple, list)) and len(gate_result) >= 2:
        gate_ok = bool(gate_result[0])
        gate_missing = list(gate_result[1])
    else:
        gate_ok, gate_missing = True, []

    status = str(payload.get("handoff_status", "UNKNOWN")).upper()
    if status not in RECEIPT_STATUSES and not force_used:
        return None  # ca PENDING thường: chưa phải kết quả nghiệm thu -> chưa sinh receipt

    sender = str(payload.get("last_updated_by", "UNKNOWN")).upper().replace(" ", "_")
    ts = datetime.now().astimezone()
    ts_str = ts.strftime("%Y%m%d-%H%M%S")
    evidence = _evidence_hashes(payload, workspace_root)
    receipt = {
        "receipt_id": f"RCP_{ts_str}_{sender}_{status}",
        "issued_at": ts.isoformat(),
        "project_code": (payload.get("project_context") or {}).get("project_code", ""),
        "action_type": _gate_action_type(payload) or "UNSPECIFIED",
        "sender": sender,
        "target": (payload.get("next_action_for_partner") or {}).get("target_agent", ""),
        "handoff_status": status,
        "gate_passed": gate_ok,
        "gate_missing": gate_missing,
        "evidence_files": (payload.get("next_action_for_partner") or {}).get("evidence_files", []),
        "report_file": (payload.get("next_action_for_partner") or {}).get("report_file", ""),
        "evidence_hashes": evidence,
        "force_used": force_used,
        "force_reason": reason if force_used else "",
        "bus_sha256": _file_hash(BUS_PATH) if BUS_PATH.exists() else None,
        "signature": f"{sender}@{ts_str}",
    }
    try:
        rdir = _receipts_dir(workspace_root)
        rdir.mkdir(parents=True, exist_ok=True)
        rfile = rdir / f"RECEIPT_{sender}_{status}_{ts_str}.json"
        _atomic_write_json(rfile, receipt)
        print(f"[SYNC_BUS v3.3] 🧾 RECEIPT: {rfile.name} "
              f"(gate={'PASS' if gate_ok else 'MISSING'}, force={force_used}, "
              f"evidence={len(evidence)} candidate)")
        return rfile
    except Exception as exc:
        print(f"[SYNC_BUS v3.3] ⚠️ Không ghi được receipt: {exc}")
        return None


# ==============================================================================
# v3.3 — REPORT GATE (chuẩn RESULT.md theo ca — sản phẩm hóa mọi ca)
# Chuẩn hóa mẫu cad_v6 (G1/C1/A1_RESULT.md): 5 mục cố định để Codex/đối tác
# đọc máy được. Áp dụng BẮT BUỘC cho ca action_type gated (CAD/DOCX/...);
# ca legacy (DYNAMIC/CODE/META...) không bị ảnh hưởng (backward-compatible).
# ==============================================================================

def result_report_dir(project_code: str, agent: str = "CLAUDE",
                      workspace_root: Path = WORKSPACE_ROOT) -> Path:
    """Thư mục audit theo THỰC TẾ cad_v6 (cả 2 phía đã đặt đúng):
    `.agents/memory/audits/<project_lower>/<agent_lower>/`
    (vd cad_v6/claude/C1_RESULT.md, cad_v6/gemini/G1_RESULT.md).
    P1 CHỈ CHUẨN HÓA layout đang có — không phát minh layout mới khác biệt."""
    code = (project_code or "MASTER_SYSTEM").strip().lower() or "master_system"
    ag = (agent or "agent").strip().lower() or "agent"
    return Path(workspace_root) / RESULTS_AUDIT_ROOT / code / ag


def result_report_filename(agent: str, phase: str = "SHIFT") -> str:
    """Tên báo cáo chuẩn theo THỰC TẾ cad_v6: `<PHASE>_RESULT.md`
    (agent nằm trong THƯ MỤC, không phải trong tên file):
    cad_v6/claude/C1_RESULT.md, cad_v6/gemini/G1_RESULT.md."""
    ph = (phase or "SHIFT").strip().upper().replace(" ", "_") or "SHIFT"
    return f"{ph}_RESULT.md"


def emit_result_report(
    project_code: str,
    agent: str,
    summary: str = "",
    deliverable: str = "",
    acceptance_cmd: str = "",
    evidence_files: Optional[List[str]] = None,
    phase: str = "SHIFT",
    workspace_root: Path = WORKSPACE_ROOT,
) -> Path:
    """
    Sinh skeleton RESULT.md (5 mục cố định, tiền-điền metadata) vào thư mục
    audit chuẩn. Agent chỉ việc điền số liệu — cấu trúc 5 mục được bảo đảm,
    Codex/đối tác đọc máy được. Nếu file đã tồn tại: KHÔNG ghi đè (tránh
    huỷ kết quả ca trước), trả về path hiện có kèm cảnh báo.
    """
    rdir = result_report_dir(project_code, agent, workspace_root)
    rdir.mkdir(parents=True, exist_ok=True)
    rpath = rdir / result_report_filename(agent, phase)
    if rpath.exists():
        print(f"[SYNC_BUS v3.3] ⚠️ RESULT.md đã tồn tại: {to_relative_path(str(rpath), workspace_root)} — "
              "không ghi đè (điền bổ sung thủ công).")
        return rpath
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    ev_lines = "\n".join(f"  - `{e}`" for e in (evidence_files or [])) or "  - (chưa khai báo)"
    content = f"""# {result_report_filename(agent, phase)}

**Dự án:** `{project_code}`
**Ca:** `{phase}` | **Tác tử:** {str(agent).upper()} | **Ngày:** {ts}

## 1. SCOPE_DELIVERED
{deliverable or summary or "(điền: sản phẩm/scope đã bàn giao của ca này)"}

## 2. VERIFICATION_COMMAND
```
{acceptance_cmd or "(điền: lệnh chạy lại được để tự chứng minh ca xong)"}
```

## 3. RESULTS
(điền: kết quả ĐO ĐƯỢC — số liệu, PASS/FAIL, log kiểm chứng)

## 4. CONSTRAINTS
(điền: ràng buộc/giới hạn của ca — đã KHÔNG làm gì, vì sao)

## 5. HANDOFF_CONTRACT
(điền: hợp đồng giao diện cho ca kế tiếp — interface, fixture, điều kiện bàn giao)

---
*Bằng chứng (evidence files):*
{ev_lines}
*Report skeleton sinh tự động bởi `sync_bus.py` v3.3 (Report Gate).*
"""
    _atomic_write_text(rpath, content)
    print(f"[SYNC_BUS v3.3] 📄 RESULT.md skeleton: {to_relative_path(str(rpath), workspace_root)}")
    return rpath


def report_gate_check(
    payload: dict,
    workspace_root: Path = WORKSPACE_ROOT,
    check_on_disk: bool = True,
) -> Tuple[bool, List[str]]:
    """
    v3.3 — Report Gate: ca có action_type GATED (CAD/DRAWING/DOCX/REPORT_VISUAL)
    phải khai báo `report_file` (RESULT.md) trong next_action_for_partner;
    với check_on_disk=True, file đó phải THẬT SỰ TỒN TRÊN ĐĨA.
    Ca không gated (CODE/META/INFRA/TEST/DOCS hoặc fallback keyword) -> luôn đạt.
    Trả về (đạt_cờ, danh_mục_thiếu).
    """
    missing: List[str] = []
    act = _gate_action_type(payload)
    if act not in GATED_ACTION_TYPES:
        return True, missing
    nap = payload.get("next_action_for_partner") or {}
    report_rel = str(nap.get("report_file", "")).strip()
    if not report_rel:
        missing.append(
            "report_file (RESULT.md) — ca " + act + " phải khai báo báo cáo pha "
            "(dùng --emit-report để sinh skeleton, hoặc --report-file <path>)"
        )
        return False, missing
    if check_on_disk:
        rp = Path(workspace_root) / report_rel
        if not (rp.exists() and rp.is_file()):
            missing.append(f"report_file không tồn tại trên đĩa: {report_rel}")
            return False, missing
    return True, missing



def _refresh_lease(data: dict, agent: str) -> None:
    """Làm mới heartbeat + hết hạn thuê ca (IN_PROGRESS) trong payload."""
    now = _now_aware()
    data["last_heartbeat"] = now.isoformat()
    if str(data.get("handoff_status", "")).upper() == "IN_PROGRESS":
        data["lease_holder"] = agent
        data["lease_expire_at"] = (now + timedelta(minutes=_lease_duration_min())).isoformat()



# ==============================================================================
# 3. PHÁT HIỆN TỰ ĐỘNG TỆP TIN SỬA ĐỔI (AUTO-DETECTION OF ARTIFACTS)
# ==============================================================================

def detect_modified_files(
    workspace_root: Path = WORKSPACE_ROOT,
    project_code: Optional[str] = None,
    minutes: float = 120.0,
    max_files: int = 50,
    project_dir: Optional[Path] = None
) -> List[str]:
    """
    Tự động quét và phát hiện các tệp tin vừa sửa đổi gần đây:
    1. Kiểm tra git status --porcelain trong .agents (nếu là git repo).
    2. Quét mtime các tệp kỹ thuật trong thư mục dự án tương ứng và memory/.
    - v3.2 Project Scope: nếu truyền `project_dir` (thư mục dự án đang làm),
      bộ quét THU Hẹp phạm vi về đúng thư mục đó (kèm thư mục memory bus),
      tránh gom nhầm artifact của dự án khác. Trả về đường dẫn tương đối POSIX
      chuẩn hóa về `workspace_root`.
    """
    modified_set: set[str] = set()
    now = time.time()
    time_threshold = now - (minutes * 60)

    # 1. Quét git status trong .agents
    agents_dir = workspace_root / ".agents"
    if (agents_dir / ".git").is_dir():
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(agents_dir),
                timeout=5
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if line and len(line) > 3:
                        raw_rel = line[3:].strip().strip('"')
                        fp = agents_dir / raw_rel
                        if fp.exists() and not fp.name.startswith("."):
                            modified_set.add(to_relative_path(str(fp), workspace_root))
        except Exception:
            pass

    # 2. Quét thư mục dự án & memory theo mtime
    if project_dir is not None:
        # v3.2: Project-Scoped scan — chỉ quét đúng thư mục dự án + bus memory.
        scan_targets = [Path(project_dir), get_bus_paths(workspace_root)[0].parent]
    else:
        scan_targets = [get_bus_paths(workspace_root)[0].parent]
        if project_code and project_code not in ("MASTER_SYSTEM", "00_MANAGEMENT_QLTK"):
            proj_dir = workspace_root / "01_Projects" / project_code
            if proj_dir.is_dir():
                scan_targets.append(proj_dir)
            else:
                projs_root = workspace_root / "01_Projects"
                if projs_root.is_dir():
                    for p in projs_root.iterdir():
                        if p.is_dir() and project_code.lower() in p.name.lower():
                            scan_targets.append(p)
        else:
            scan_targets.append(workspace_root / "01_Projects")
            scan_targets.append(workspace_root / ".agents")

    ignore_dirs = {".git", "__pycache__", "archive", "_archive", "node_modules", "references", "locks"}
    allowed_exts = {".py", ".json", ".md", ".docx", ".xlsx", ".pdf", ".dwg", ".dxf"}

    for target in scan_targets:
        if not target.exists():
            continue
        pending = [str(target)]
        while pending:
            try:
                with os.scandir(pending.pop()) as entries:
                    for entry in entries:
                        if entry.name.startswith('.'):
                            continue
                        if entry.is_dir():
                            if entry.name not in ignore_dirs and not entry.is_symlink():
                                pending.append(entry.path)
                            continue
                        if '.tmp.' in entry.name or Path(entry.name).suffix.lower() not in allowed_exts:
                            continue
                        try:
                            if entry.stat().st_mtime >= time_threshold:
                                modified_set.add(to_relative_path(entry.path, workspace_root))
                        except OSError:
                            pass
            except OSError:
                continue

    filtered = [
        f for f in modified_set
        if not f.endswith("dual_agent_bus.lock") and not ".tmp." in f
    ]
    sorted_files = sorted(filtered)
    return sorted_files[:max_files]


# ==============================================================================
# 4. BỘ KIỂM TRA TÍNH HỢP LỆ DỮ LIỆU & QUY ƯỚC TRẠNG THÁI (SCHEMA v3.0)
# ==============================================================================

VALID_HANDOFF_STATUSES = {
    "PENDING",       # Agent A vừa giao việc, đang chờ Agent B nhận ca
    "IN_PROGRESS",   # Agent B đã tiếp nhận và đang chủ động thực thi (LOCK - Không can thiệp)
    "COMPLETED",     # Agent B đã thực hiện xong mọi tiêu chí nghiệm thu
    "NEED_REVIEW"    # Cần Agent A hoặc Kỹ sư trưởng đối chiếu / thẩm tra lại
}

VALID_STATUSES = {
    "PENDING_CONFIRMATION",
    "CONFIRMED_AND_HANDED_OFF",
    "PENDING_ACTION",
    "PENDING_PARTNER_ACTION",
    "IN_PROGRESS",
    "VERIFIED_AND_ACCEPTED_BY_BOTH_AGENTS",
    "CLAUDE_VERIFIED_PASS_WITH_FIXES",
    "REJECTED_WITH_FEEDBACK",
    "REVIEW_REQUIRED"
}

def validate_bus_payload(payload: dict) -> Tuple[bool, str]:
    """
    Kiểm tra tính toàn vẹn của bus payload theo chuẩn v3.0.
    Đảm bảo tương thích ngược 100% với các phiên bản v1.0 và v2.0.
    """
    if not isinstance(payload, dict):
        return False, "Payload phải là một từ điển (dictionary)."

    required_keys = [
        "last_updated_by",
        "timestamp",
        "summary",
        "artifacts_modified",
        "next_action_for_partner",
        "Verification_Status"
    ]
    for rk in required_keys:
        if rk not in payload:
            return False, f"Thiếu trường bắt buộc '{rk}' trong payload."

    if not isinstance(payload["artifacts_modified"], list):
        return False, "'artifacts_modified' bắt buộc phải là một danh sách (list)."

    if not isinstance(payload["next_action_for_partner"], dict):
        return False, "'next_action_for_partner' bắt buộc phải là một từ điển."

    if "target_agent" not in payload["next_action_for_partner"]:
        return False, "Thiếu trường 'target_agent' trong 'next_action_for_partner'."

    # Bắt buộc có command hoặc task_description
    if "command" not in payload["next_action_for_partner"] and "task_description" not in payload["next_action_for_partner"]:
        return False, "Thiếu trường 'command' hoặc 'task_description' trong 'next_action_for_partner'."

    # Kiểm tra handoff_status nếu có
    if "handoff_status" in payload and payload["handoff_status"] not in VALID_HANDOFF_STATUSES:
        return False, f"Trạng thái handoff_status không hợp lệ: {payload['handoff_status']}. Cho phép: {VALID_HANDOFF_STATUSES}"

    # Kiểm tra timestamp
    try:
        datetime.fromisoformat(payload["timestamp"])
    except Exception:
        return False, f"Timestamp không đúng định dạng ISO-8601: {payload.get('timestamp')}"

    return True, "Hợp lệ"


# ==============================================================================
# 5. TỰ ĐỘNG KẾT XUẤT BIÊN BẢN GIAO BAN (HANDOFF MEMO GENERATOR v3.0)
# ==============================================================================

def generate_handoff_memo(payload: dict, memo_path: Path = MEMO_PATH) -> None:
    """
    Tự động kết xuất file Markdown giao ban chi tiết: memory/DUAL_AGENT_HANDOFF_MEMO.md
    Tích hợp bảng tiêu chí nghiệm thu tương tác (Checklist) và trạng thái ca trực.
    """
    sender = payload.get("last_updated_by", "UNKNOWN")
    next_action = payload.get("next_action_for_partner", {})
    target = next_action.get("target_agent", "PARTNER")
    timestamp = payload.get("timestamp", datetime.now().astimezone().isoformat())
    handoff_status = payload.get("handoff_status", "PENDING")
    verification_status = payload.get("Verification_Status", "PENDING_ACTION")
    holder = payload.get("current_holder", "IDLE")
    summary = payload.get("summary", "")

    task_desc = next_action.get("task_description", next_action.get("command", ""))
    next_cmd = next_action.get("command", task_desc)
    criteria = next_action.get("acceptance_criteria", [])
    target_files = next_action.get("target_files", [])
    artifacts = payload.get("artifacts_modified", [])

    ctx = payload.get("project_context", {})
    project_code = ctx.get("project_code", "MASTER_SYSTEM")
    project_purpose = ctx.get("project_purpose", "Phối hợp liên tác tử theo mục tiêu dự án")
    role_distribution = ctx.get("role_distribution", "Linh hoạt tùy mục đích dự án (Dynamic Project-Driven)")

    memo_lines = [
        "# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.2)",
        "",
        f"> **Dự án:** `{project_code}` — *{project_purpose}*  ",
        f"> **Người gửi:** **{sender}** ➔ **Người nhận:** **{target}**  ",
        f"> **Thời điểm bàn giao:** `{timestamp}`  ",
        f"> **Trạng thái bàn giao (handoff_status):** `{handoff_status}` *(Verification: `{verification_status}`)*  ",
        f"> **Tác tử giữ ca (current_holder):** `{holder}`  ",
    ]
    # v3.2: hiển thị Lease/Heartbeat khi ca IN_PROGRESS đang chạy
    if str(handoff_status).upper() == "IN_PROGRESS" and payload.get("lease_expire_at"):
        lease_state = "HẾT HẠN (đang treo — có thể auto-claim)" if _is_lease_expired(payload) else "HOẠT ĐỘNG"
        memo_lines.extend([
            f"> **Lease ca trực (v3.2):** heartbeat `{payload.get('last_heartbeat', 'N/A')}`  ",
            f"> ➔ Hết hạn: `{payload.get('lease_expire_at')}` *(trạng thái: {lease_state})*  ",
        ])
    if str(handoff_status).upper() == "IN_PROGRESS" and not payload.get("lease_expire_at"):
        memo_lines.append("> **Lease ca trực (v3.2):** *(bus legacy — chưa có lease; dùng --force để tiếp quản)*  ")
    # v3.2: hiển thị kết quả Visual Gate (Điều 12d)
    gate_ok, gate_missing = visual_gate_check(payload)
    if not gate_ok:
        memo_lines.append(f"> **Visual Gate (Điều 12d):** 🛑 CHƯA ĐẠT — thiếu: {', '.join(gate_missing)}  ")
    memo_lines.extend([
        f"> **Chế độ phân việc:** {role_distribution}  ",
        f"> **Kênh bus nguyên tử:** `{to_relative_path(str(BUS_PATH), WORKSPACE_ROOT)}`  ",
        "",
        "---",
        "",
        "## 1. MỤC TIÊU DỰ ÁN & NGUYÊN TẮC PHÂN CÔNG",
        "",
        f"- **Mã dự án:** `{project_code}`",
        f"- **Mục tiêu chính:** {project_purpose}",
        f"- **Nguyên tắc phân vai:** Không cố định vai trò; phân việc linh hoạt tùy theo mục tiêu, tiến độ và độ phức tạp kỹ thuật của từng dự án cụ thể.",
        "",
        "---",
        "",
        "## 2. TÓM TẮT TIẾN ĐỘ & KẾT QUẢ ĐÃ THỰC HIỆN",
        "",
        f"{summary}",
        "",
        "---",
        "",
        "## 3. DANH MỤC TỆP ĐÃ SỬA ĐỔI / PHÁT SINH (ARTIFACTS MODIFIED - POSIX RELATIVE)",
        "",
    ])

    if artifacts:
        for idx, art in enumerate(artifacts, 1):
            memo_lines.append(f"{idx}. `{art}`")
    else:
        memo_lines.append("*(Không có tệp nào được sửa đổi hoặc chưa cập nhật danh sách)*")

    memo_lines.extend([
        "",
        "---",
        "",
        "## 4. CHỈ THỊ HÀNH ĐỘNG KẾ TIẾP & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)",
        "",
        f"- **Tác tử tiếp nhận:** `{target}`",
        f"- **Nhiệm vụ cụ thể (Task Description):**",
        f"  > {task_desc}",
    ])

    if target_files:
        memo_lines.append("")
        memo_lines.append("- **Tệp tin trọng tâm xử lý (Target Files):**")
        for tf in target_files:
            memo_lines.append(f"  - `{tf}`")

    if criteria:
        memo_lines.append("")
        memo_lines.append("- **Tiêu chí nghiệm thu (Checklist Verification):**")
        for crit in criteria:
            memo_lines.append(f"  - [ ] {crit}")

    memo_lines.extend([
        "",
        f"- **Lệnh điều phối tương thích (Command):**",
        f"  > `{next_cmd}`",
        "",
        "---",
        "",
        "*Tài liệu được sinh tự động bởi `sync_bus.py` v3.3 (SSOT) dưới cơ chế khóa nguyên tử FileLock, "
        "Lease/Heartbeat, Project-Scoped Resolver & Anti-Collision Mutex + Visual Gate (Điều 12d).*"
    ])

    memo_content = "\n".join(memo_lines)
    _atomic_write_text(memo_path, memo_content)


# ==============================================================================
# 6. GIAO DIỆN BÀN GIAO BUS (CORE & AUTOMATED APIS v3.0)
# ==============================================================================

def _dispatch_adapter(workspace):
    dispatcher_dir = str(Path(__file__).resolve().parents[1] / "skills" / "Global_Dispatcher")
    if dispatcher_dir not in sys.path:
        sys.path.insert(0, dispatcher_dir)
    from sync_bus_2d_patch import SyncBus2DAdapter
    return SyncBus2DAdapter(workspace_root=workspace)


def _route_handoff(task, project_code, project_dir=None, agent_selection=None, ticket=None):
    adapter = _dispatch_adapter(WORKSPACE_ROOT)
    if ticket is not None:
        if agent_selection is not None and agent_selection != ticket["dispatch_2d"]["agent_selection"]:
            raise ValueError("Lựa chọn tác tử khác phiếu giao việc.")
        if Path(ticket["workspace"]).resolve() != Path(WORKSPACE_ROOT).resolve():
            raise ValueError("Phiếu giao việc thuộc workspace khác.")
        if ticket["status"] != "QUEUED":
            raise ValueError("Phiếu chưa sẵn sàng để giao việc.")
        dispatch = ticket["dispatch_2d"]
        if dispatch["engagement_mode"] == "PRODUCT_COLLAB":
            bound = Path(dispatch["deliverable_dir_posix"]).resolve().parent
            if project_dir and Path(project_dir).resolve() != bound:
                raise ValueError("Thư mục bàn giao khác dự án đã xác nhận trên phiếu.")
            if project_code not in ("MASTER_SYSTEM", bound.name):
                raise ValueError("Mã dự án bàn giao khác dự án đã xác nhận trên phiếu.")
        return ticket
    project_name = Path(project_dir).name if project_dir else project_code
    prompt = f"{task} {project_name}"
    return adapter.prepare_handover_payload(
        prompt, project_code, task, agent_selection=agent_selection,
        include_solo=agent_selection is not None or task.lstrip().startswith("/solo"),
    )


def _verify_product_ticket(payload, agent, summary, review=None, approval=None):
    ticket = payload.get("work_ticket")
    if not ticket or ticket["dispatch_2d"]["engagement_mode"] != "PRODUCT_COLLAB":
        return
    review = review or {}
    checked = _dispatch_adapter(WORKSPACE_ROOT).complete_handover_with_gate(
        ticket, summary, agent_name=agent, reviewed_by=review.get("reviewer"),
        reviewed_hashes=review.get("evidence_hashes"), approval=approval,
    )
    if checked["status"] != "COMPLETED":
        raise ValueError(f"{checked['status']}: {checked['human_handoff']['deliverable_gate_message_vi']}")


def auto_handoff(
    sender: str,
    target: str,
    summary: str,
    next_cmd: str = "",
    project_code: str = "MASTER_SYSTEM",
    project_purpose: str = "Phối hợp liên tác tử theo mục tiêu dự án",
    role_distribution: str = "Linh hoạt tùy mục đích dự án",
    files: Optional[List[str]] = None,
    auto_detect_files: bool = True,
    confirmed: bool = True,
    status: Optional[str] = None,
    handoff_status: str = "PENDING",
    task_description: Optional[str] = None,
    target_files: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    action_type: str = "DYNAMIC",
    force: bool = False,
    project_dir: Optional[Path] = None,
    # ---- v3.3 Product-First (hợp đồng bàn giao sản phẩm) ----
    deliverable: Optional[str] = None,
    evidence_files: Optional[List[str]] = None,
    acceptance_cmd: Optional[str] = None,
    check_evidence_on_disk: bool = False,
    receipt_reason: str = "",
    # ---- v3.3 Report Gate (chuẩn RESULT.md theo ca) ----
    report_file: Optional[str] = None,
    phase: str = "SHIFT",
    emit_report: bool = False,
    agent_selection: Optional[str] = None,
    dispatch_ticket: Optional[dict] = None,
    approval_record: Optional[dict] = None,
    review_record: Optional[dict] = None,
) -> dict:
    """
    TỰ ĐỘNG BÀN GIAO THÔNG TIN KHI CÓ XÁC NHẬN (AUTOMATED HANDOFF ON CONFIRMATION v3.0/v3.3).
    - Chuẩn hóa 100% artifacts sang đường dẫn tương đối (POSIX /).
    - Bổ sung cấu trúc task_description, target_files và acceptance_criteria.
    - Cơ chế Software Mutex: kiểm tra cờ IN_PROGRESS để chống lệch nhịp khi đối tác đang làm.
    - v3.2: Project-Scoped Resolver (project_dir), Visual Gate (Điều 12d) và Lease/Heartbeat.
    - v3.3 Product-First: `deliverable` (sản phẩm mong đợi), `evidence_files`
      (bằng chứng phải tồn tại), `acceptance_cmd` (lệnh chạy lại để tự chứng minh).
      `check_evidence_on_disk` bật kiểm bằng chứng THẬT SỰ TỒN TẠI (SHA-256).
      Tự sinh RECEIPT khi ca NEED_REVIEW/COMPLETED hoặc khi --force (audit trail).
    """
    # NOTE: the IN_PROGRESS conflict check runs INSIDE `with FileLock(LOCK_PATH)`
    # below (near the write) — reading the bus unlocked and then writing under
    # the lock is a TOCTOU window two agents could both pass through.

    work = _route_handoff(task_description or next_cmd or summary, project_code, project_dir,
                          agent_selection, dispatch_ticket)
    if work and work["status"] in {"NEEDS_PROJECT_CONFIRMATION", "NEEDS_TASK_CONFIRMATION"}:
        raise ValueError(work["human_handoff"]["user_report_vi"])
    if work and not work["dispatch_2d"]["use_dual_agent_bus"]:
        return work
    if dispatch_ticket and work["dispatch_2d"]["engagement_mode"] == "PRODUCT_COLLAB":
        project_dir = Path(work["dispatch_2d"]["deliverable_dir_posix"]).resolve().parent
        project_code = project_dir.name
    if status is None:
        status = "CONFIRMED_AND_HANDED_OFF" if confirmed else "PENDING_CONFIRMATION"

    # Chuẩn hóa danh sách file tương đối
    raw_files = files or []
    if not raw_files and auto_detect_files:
        raw_files = detect_modified_files(
            WORKSPACE_ROOT, project_code=project_code, project_dir=project_dir
        )

    normalized_files = [to_relative_path(f, WORKSPACE_ROOT) for f in raw_files if f.strip()]
    bus_rel = to_relative_path(str(BUS_PATH), WORKSPACE_ROOT)
    if bus_rel not in normalized_files:
        normalized_files.append(bus_rel)

    effective_task = task_description or next_cmd or "Thực thi công việc theo kế hoạch dự án"
    effective_cmd = next_cmd or effective_task
    effective_target_files = [to_relative_path(f, WORKSPACE_ROOT) for f in (target_files or [])]

    # v3.3 Report Gate: ca GATED (CAD/DOCX/...) sinh skeleton RESULT.md nếu --emit-report,
    # hoặc dùng report_file khai báo. Chuẩn hoá về đường dẫn tương đối POSIX.
    eff_report_file = ""
    if emit_report:
        rpath = emit_result_report(
            project_code=project_code, agent=sender, summary=summary,
            deliverable=deliverable or "", acceptance_cmd=acceptance_cmd or "",
            evidence_files=evidence_files, phase=phase,
            workspace_root=WORKSPACE_ROOT,
        )
        eff_report_file = to_relative_path(str(rpath), WORKSPACE_ROOT)
    elif report_file:
        eff_report_file = to_relative_path(report_file, WORKSPACE_ROOT)

    payload = {
        **({"work_ticket": work} if work else {}),
        "project_context": {
            "project_code": project_code,
            "project_purpose": project_purpose,
            "role_distribution": role_distribution,
            "action_type": action_type
        },
        "last_updated_by": sender,
        "timestamp": datetime.now().astimezone().isoformat(),
        "handoff_status": handoff_status,
        "current_holder": "IDLE" if handoff_status != "IN_PROGRESS" else target,
        "summary": summary,
        "artifacts_modified": normalized_files,
        "next_action_for_partner": {
            "target_agent": target,
            "task_description": effective_task,
            "target_files": effective_target_files,
            "acceptance_criteria": acceptance_criteria or [],
            "command": effective_cmd,
            # ---- v3.3 Product-First (chỉ ghi khi khai báo — backward-compatible) ----
            **({"deliverable": deliverable} if deliverable else {}),
            **({"evidence_files": [to_relative_path(f, WORKSPACE_ROOT) for f in evidence_files if str(f).strip()]} if evidence_files else {}),
            **({"acceptance_cmd": acceptance_cmd} if acceptance_cmd else {}),
            **({"report_file": eff_report_file} if eff_report_file else {}),
        },
        "Verification_Status": status
    }

    if handoff_status == "COMPLETED":
        _verify_product_ticket(payload, sender, summary, review_record, approval_record)

    # v3.2: Lease/Heartbeat — ca IN_PROGRESS phải mang dấu thời gian hết hạn thuê.
    if handoff_status == "IN_PROGRESS":
        _refresh_lease(payload, target)

    # v3.2/v3.3: Visual Gate (Điều 12d) — chặn PENDING/NEED_REVIEW/COMPLETED khi
    # task CAD/Bản vẽ chưa có bằng chứng nghiệm thu. v3.3: có thể bắt bằng chứng
    # THẬT SỰ TỒN TẠI trên đĩa (check_evidence_on_disk) thay vì danh khai suông.
    gate_result = (True, [])
    if handoff_status in ("PENDING", "NEED_REVIEW", "COMPLETED"):
        gate_result = visual_gate_check(payload, workspace_root=WORKSPACE_ROOT,
                                        check_on_disk=check_evidence_on_disk)
        gate_ok, gate_missing = gate_result[0], gate_result[1]
        if not gate_ok and not force:
            raise ValueError(
                "[SYNC_BUS v3.3] 🛑 VISUAL GATE (Điều 12d, evidence-based): Task cần "
                "bằng chứng nghiệm thu trước khi bàn giao. Thiếu: "
                + ", ".join(gate_missing)
                + " — Đính kèm preview (.png/.jpg) hoặc log _verification.json (vào evidence_files/"
                  "artifacts) để file TỒN TẠI trên đĩa, hoặc dùng cờ --force để bỏ qua "
                  "(bypass sẽ được ghi RECEIPT để audit)."
            )
        # v3.3 Report Gate: ca GATED (CAD/DOCX...) phải kèm RESULT.md (báo cáo pha).
        rep_ok, rep_missing = report_gate_check(payload, workspace_root=WORKSPACE_ROOT,
                                                check_on_disk=check_evidence_on_disk)
        if not rep_ok and not force:
            raise ValueError(
                "[SYNC_BUS v3.3] 📄 REPORT GATE: Task GATED chưa có báo cáo pha "
                "(RESULT.md). Thiếu: " + ", ".join(rep_missing)
                + " — dùng --emit-report (sinh skeleton 5 mục) hoặc --report-file <path>."
            )

    # Kiểm tra schema
    is_valid, reason = validate_bus_payload(payload)
    if not is_valid:
        raise ValueError(f"[SYNC_BUS] Lỗi Schema Payload: {reason}")

    with FileLock(LOCK_PATH):
        # Re-validate the IN_PROGRESS conflict UNDER the lock: the earlier
        # unlocked read would let two agents both see PENDING and both write.
        # v3.2: ca IN_PROGRESS HẾT HẠN THUÊ (lease) coi như không còn người giữ
        # -> cho phép ghi đè hợp lệ (auto-claim) mà không cần --force.
        if not force:
            try:
                curr_data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
                if curr_data.get("handoff_status") == "IN_PROGRESS" and curr_data.get("current_holder") != sender:
                    if _is_lease_expired(curr_data):
                        holder = curr_data.get("current_holder", "PARTNER")
                        print(f"[SYNC_BUS v3.2] ⏳ Ca của {holder} đã HẾT HẠN THUÊ (lease) — không có "
                              "heartbeat trong thời hạn; cho phép tiếp quản mà không cần --force.")
                    else:
                        holder = curr_data.get("current_holder", "PARTNER")
                        print(f"[SYNC_BUS v3.0] ⚠️ CẢNH BÁO: Tác tử {holder} đang trong ca trực (IN_PROGRESS).")
                        print("              Để tránh xung đột race condition, hãy đợi tác tử hoàn tất hoặc dùng cờ --force.")
            except Exception:
                pass
        _atomic_write_json(BUS_PATH, payload)
        generate_handoff_memo(payload, MEMO_PATH)
        # v3.3: RECEIPT — ca NEED_REVIEW/COMPLETED (kết quả nghiệm thu) hoặc
        # mọi --force (bypass gate / ghi đè ca treo) đều để lại dấu vết audit.
        receipt_path = write_receipt(
            payload, gate_result, reason=receipt_reason, force_used=force
        )
    print(f"[SYNC_BUS v3.3] ✅ ĐÃ BÀN GIAO THÀNH CÔNG VỚI XÁC NHẬN:")
    print(f"  • Dự án:          {project_code} ({project_purpose})")
    print(f"  • Luồng bàn giao: {sender} ➔ {target}")
    print(f"  • Trạng thái:     handoff_status={handoff_status} | holder={payload['current_holder']}")
    print(f"  • Nhiệm vụ:       {effective_task}")
    print(f"  • Tiêu chí:       {len(acceptance_criteria or [])} mục kiểm tra")
    print(f"  • Số artifacts:   {len(normalized_files)} tệp tin (chuẩn POSIX relative)")
    if deliverable:
        print(f"  • Sản phẩm (deliverable): {deliverable}")
    if receipt_path is not None:
        print(f"  • RECEIPT:        {to_relative_path(str(receipt_path), WORKSPACE_ROOT)}")
    print(f"  • File cập nhật:  {BUS_PATH}")
    print(f"  • Memo cập nhật:  {MEMO_PATH}")

    return payload


def post_handoff(
    sender: str,
    target: str,
    summary: str,
    next_cmd: str,
    files: List[str],
    status: str = "PENDING_ACTION",
    project_code: str = "MASTER_SYSTEM",
    project_purpose: str = "Phối hợp liên tác tử theo mục tiêu dự án"
):
    """
    Hàm bàn giao tương thích ngược (Backward-compatible).
    """
    work = _route_handoff(next_cmd, project_code)
    if work and work["status"] in {"NEEDS_PROJECT_CONFIRMATION", "NEEDS_TASK_CONFIRMATION"}:
        raise ValueError(work["human_handoff"]["user_report_vi"])
    if work and not work["dispatch_2d"]["use_dual_agent_bus"]:
        return work
    normalized_files = [to_relative_path(f, WORKSPACE_ROOT) for f in files if f.strip()]
    bus_rel = to_relative_path(str(BUS_PATH), WORKSPACE_ROOT)
    if bus_rel not in normalized_files:
        normalized_files.append(bus_rel)

    payload = {
        **({"work_ticket": work} if work else {}),
        "project_context": {
            "project_code": project_code,
            "project_purpose": project_purpose,
            "role_distribution": "Linh hoạt tùy mục đích dự án"
        },
        "last_updated_by": sender,
        "timestamp": datetime.now().astimezone().isoformat(),
        "handoff_status": "PENDING",
        "current_holder": "IDLE",
        "summary": summary,
        "artifacts_modified": normalized_files,
        "next_action_for_partner": {
            "target_agent": target,
            "command": next_cmd,
            "task_description": next_cmd,
            "acceptance_criteria": []
        },
        "Verification_Status": status
    }

    is_valid, reason = validate_bus_payload(payload)
    if not is_valid:
        raise ValueError(f"[SYNC_BUS] Lỗi Schema Payload: {reason}")

    with FileLock(LOCK_PATH):
        _atomic_write_json(BUS_PATH, payload)
        generate_handoff_memo(payload, MEMO_PATH)

    print(f"[SYNC_BUS] ✅ Đã bàn giao trạng thái từ {sender} -> {target}")
    print(f"           Vị trí: {BUS_PATH}")
    print(f"           Lệnh tiếp theo: {next_cmd}")


# ==============================================================================
# 7. QUẢN LÝ VÒNG ĐỜI CA TRỰC (STATE TRANSITIONS: CLAIM / COMPLETE / REVIEW)
# ==============================================================================

def claim_task(agent: str, force: bool = False) -> dict:
    """
    Tác tử tiếp nhận (ví dụ CLAUDE) kích hoạt khi bắt đầu làm việc.
    Chuyển handoff_status -> IN_PROGRESS, current_holder -> agent.
    Bảo vệ tác tử không bị AI đối tác can thiệp hay ghi đè lúc đang chạy dở.

    v3.2 — Lease/Heartbeat: nếu ca IN_PROGRESS hiện tại đã HẾT HẠN THUÊ
    (lease_expire_at / last_heartbeat quá tuổi mà không có heartbeat mới),
    tác tử khác được TIẾP QUẢN TỰ ĐỘNG (auto-claim) mà không cần --force.
    Ca không có mốc thời gian nào (bus legacy) vẫn giữ nguyên bảo vệ:
    bắt buộc --force để tránh rủi ro ghi đè một ca treo không rõ nguồn gốc.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        holder = str(data.get("current_holder", "IDLE")).upper()
        agent = agent.upper()
        if data.get("handoff_status") == "IN_PROGRESS" and holder != agent:
            if force:
                print(f"[SYNC_BUS v3.2] ⚠️ FORCE: {agent} tiếp quản ca của {holder}.")
            elif _is_lease_expired(data):
                print(f"[SYNC_BUS v3.2] ⏳ Ca IN_PROGRESS của {holder} đã HẾT HẠN THUÊ (lease).")
                print(f"              Cho phép {agent} TIẾP QUẢN TỰ ĐỘNG mà không cần --force.")
            else:
                raise PermissionError(
                    f"Active shift belongs to {holder}; {agent} cannot change it (lease still active)"
                )
        data["handoff_status"] = "IN_PROGRESS"
        data["current_holder"] = agent
        data["Verification_Status"] = "IN_PROGRESS"
        data["claim_timestamp"] = datetime.now().astimezone().isoformat()
        _refresh_lease(data, agent)
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)

    print(f"[SYNC_BUS v3.2] 🔒 {agent} ĐÃ TIẾP NHẬN CA VÀ KHÓA THI HÀNH (IN_PROGRESS).")
    print(f"              Lease: {_lease_duration_min()} phút (heartbeat làm mới bằng --heartbeat).")
    print(f"              Đối tác đối chiếu hoặc Gemini sẽ KHÔNG can thiệp ghi đè lúc này!")
    return data


def complete_task(
    agent: str, summary: str = "", files: Optional[List[str]] = None, force: bool = False,
    reason: str = "", report_file: Optional[str] = None, review_record: Optional[dict] = None,
    approval_record: Optional[dict] = None
) -> dict:
    """
    Tác tử đã hoàn tất toàn bộ tiêu chí nghiệm thu.
    Chuyển handoff_status -> COMPLETED, current_holder -> IDLE.

    v3.2 — Visual Gate (Điều 12d): với task CAD/Bản vẽ, bắt buộc có bằng chứng
    nghiệm thu (preview .png / log) trong artifacts trước khi COMPLETED.
    v3.3 — RECEIPTS: ca COMPLETED (và mọi --force) sinh receipt; `reason` ghi
    lý do bypass vào audit trail.
    v3.3 — REPORT GATE: ca GATED (action_type CAD/DOCX/...) bắt buộc có
    `report_file` (RESULT.md) TỒN TRÊN ĐĨA; `report_file` có thể khai báo mới
    hoặc kế thừa từ bus hiện tại.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        holder = str(data.get("current_holder", "IDLE")).upper()
        agent = agent.upper()
        if data.get("handoff_status") == "IN_PROGRESS" and holder != agent:
            if force:
                print(f"[SYNC_BUS v3.2] ⚠️ FORCE: {agent} tiếp quyền đóng ca của {holder}.")
            elif _is_lease_expired(data):
                print(f"[SYNC_BUS v3.2] ⏳ Lease của {holder} đã hết hạn — {agent} tiếp quản quyền đóng ca.")
            else:
                raise PermissionError(
                    f"Active shift belongs to {holder}; {agent} cannot change it (lease still active)"
                )
        _verify_product_ticket(data, agent, summary or data.get("summary", ""), review_record, approval_record)
        data["handoff_status"] = "COMPLETED"
        data["current_holder"] = "IDLE"
        data["last_updated_by"] = agent
        data["timestamp"] = datetime.now().astimezone().isoformat()
        data["Verification_Status"] = "CONFIRMED_AND_HANDED_OFF"
        if summary:
            data["summary"] = summary
        if files:
            data["artifacts_modified"] = [to_relative_path(f, WORKSPACE_ROOT) for f in files]
        # v3.3: đính kèm báo cáo pha (RESULT.md) nếu khai báo
        if report_file:
            data.setdefault("next_action_for_partner", {})["report_file"] = to_relative_path(report_file, WORKSPACE_ROOT)
        # v3.2: xóa lease treo khi ca khép lại
        data.pop("lease_expire_at", None)
        data.pop("lease_holder", None)
        # v3.2/v3.3: Visual Gate (Điều 12d) + RECEIPT
        gate_result = (True, [])
        if not force:
            gate_result = visual_gate_check(data, workspace_root=WORKSPACE_ROOT)
            gate_ok, gate_missing = gate_result[0], gate_result[1]
            if not gate_ok:
                raise ValueError(
                    "[SYNC_BUS v3.3] 🛑 VISUAL GATE (Điều 12d, evidence-based): không thể COMPLETED "
                    "task cần bằng chứng khi chưa đủ. Thiếu: " + ", ".join(gate_missing)
                    + " — đính kèm preview/log (evidence_files/--files) để TỒN TẠI trên đĩa, "
                      "hoặc dùng --force (bypass sẽ ghi RECEIPT)."
                )
            # v3.3 Report Gate: ca GATED (CAD/DOCX...) phải kèm RESULT.md
            rep_ok, rep_missing = report_gate_check(data, workspace_root=WORKSPACE_ROOT)
            if not rep_ok:
                raise ValueError(
                    "[SYNC_BUS v3.3] 📄 REPORT GATE: ca GATED không thể COMPLETED khi chưa có "
                    "báo cáo pha (RESULT.md). Thiếu: " + ", ".join(rep_missing)
                    + " — đính kèm --report-file (hoặc --emit-report khi --auto), hoặc dùng --force."
                )
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)
        # v3.3: RECEIPT cho ca COMPLETED (kết quả nghiệm thu) hoặc --force
        write_receipt(data, gate_result, reason=reason, force_used=force)

    print(f"[SYNC_BUS v3.3] ✅ {agent} ĐÃ HOÀN TẤT NHIỆM VỤ (COMPLETED). Toàn bộ tiêu chí đạt yêu cầu!")
    return data


def request_review(
    agent: str, summary: str = "", next_agent: str = "GEMINI", force: bool = False,
    reason: str = "", report_file: Optional[str] = None
) -> dict:
    """
    Tác tử hoàn thành bước kỹ thuật và yêu cầu kiểm tra chéo / phê duyệt.
    Chuyển handoff_status -> NEED_REVIEW, bàn giao lượt review cho next_agent.

    v3.2 — Visual Gate (Điều 12d): với task CAD/Bản vẽ, bắt buộc có bằng chứng
    nghiệm thu (preview .png / log) trước khi đặt NEED_REVIEW.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        holder = str(data.get("current_holder", "IDLE")).upper()
        agent = agent.upper()
        if data.get("handoff_status") == "IN_PROGRESS" and holder != agent:
            if force:
                print(f"[SYNC_BUS v3.3] ⚠️ FORCE: {agent} tiếp quyền review ca của {holder}.")
            elif _is_lease_expired(data):
                print(f"[SYNC_BUS v3.2] ⏳ Lease của {holder} đã hết hạn — {agent} tiếp quản quyền review.")
            else:
                raise PermissionError(
                    f"Active shift belongs to {holder}; {agent} cannot change it (lease still active)"
                )
        data["handoff_status"] = "NEED_REVIEW"
        data["current_holder"] = "IDLE"
        data["last_updated_by"] = agent
        data["timestamp"] = datetime.now().astimezone().isoformat()
        data["Verification_Status"] = "REVIEW_REQUIRED"
        if summary:
            data["summary"] = summary
        if "next_action_for_partner" in data:
            data["next_action_for_partner"]["target_agent"] = next_agent
            # v3.3: đính kèm báo cáo pha (RESULT.md) nếu khai báo
            if report_file:
                data["next_action_for_partner"]["report_file"] = to_relative_path(report_file, WORKSPACE_ROOT)
        data.pop("lease_expire_at", None)
        data.pop("lease_holder", None)
        # v3.2/v3.3: Visual Gate (Điều 12d) + RECEIPT
        gate_result = (True, [])
        if not force:
            gate_result = visual_gate_check(data, workspace_root=WORKSPACE_ROOT)
            gate_ok, gate_missing = gate_result[0], gate_result[1]
            if not gate_ok:
                raise ValueError(
                    "[SYNC_BUS v3.3] 🛑 VISUAL GATE (Điều 12d, evidence-based): không thể đặt "
                    "NEED_REVIEW khi chưa đủ bằng chứng nghiệm thu. Thiếu: " + ", ".join(gate_missing)
                    + " — đính kèm preview/log (evidence_files) để TỒN TẠI trên đĩa, "
                      "hoặc dùng --force (bypass sẽ ghi RECEIPT)."
                )
            # v3.3 Report Gate: ca GATED (CAD/DOCX...) phải kèm RESULT.md
            rep_ok, rep_missing = report_gate_check(data, workspace_root=WORKSPACE_ROOT)
            if not rep_ok:
                raise ValueError(
                    "[SYNC_BUS v3.3] 📄 REPORT GATE: ca GATED không thể đặt NEED_REVIEW khi chưa có "
                    "báo cáo pha (RESULT.md). Thiếu: " + ", ".join(rep_missing)
                    + " — đính kèm --report-file (hoặc --emit-report khi --auto), hoặc dùng --force."
                )
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)
        # v3.3: RECEIPT cho ca NEED_REVIEW (lượt review chính thức) hoặc --force
        write_receipt(data, gate_result, reason=reason, force_used=force)

    print(f"[SYNC_BUS v3.3] 🔍 {agent} ĐÃ YÊU CẦU KIỂM TRA CHÉO (NEED_REVIEW) TỪ {next_agent}!")
    return data


def heartbeat(agent: str) -> dict:
    """
    v3.2 — Heartbeat: tác tử ĐANG GIỮ CA gọi định kỳ để gia hạn lease.
    Chỉ holder hợp lệ (hoặc --force) được phép heartbeat.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        agent = agent.upper()
        holder = str(data.get("current_holder", "IDLE")).upper()
        if str(data.get("handoff_status", "")).upper() != "IN_PROGRESS" or holder != agent:
            raise PermissionError(f"Heartbeat chỉ hợp lệ khi {agent} là holder đang giữ ca IN_PROGRESS.")
        _refresh_lease(data, agent)
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)

    print(f"[SYNC_BUS v3.2] 💓 {agent} GỬI HEARTBEAT — lease gia hạn đến {data.get('lease_expire_at')}.")
    return data


def read_bus(validate: bool = True) -> dict:
    """Đọc trạng thái hiện tại từ bus và tùy chọn kiểm tra tính hợp lệ."""
    if not BUS_PATH.exists():
        print(f"[SYNC_BUS] ⚠️ File bus chưa tồn tại tại {BUS_PATH}")
        return {}
    with FileLock(LOCK_PATH):
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))

    if validate:
        is_valid, reason = validate_bus_payload(data)
        if not is_valid:
            print(f"[SYNC_BUS] ⚠️ Cảnh báo Schema bus hiện tại chưa chuẩn: {reason}")

    print(json.dumps(data, ensure_ascii=False, indent=2))
    # v3.2: cảnh báo lease gần hết hạn để holder kịp heartbeat.
    if str(data.get("handoff_status", "")).upper() == "IN_PROGRESS" and data.get("lease_expire_at"):
        exp = _parse_iso(str(data.get("lease_expire_at")))
        if exp is not None:
            remain = (exp - _now_aware()).total_seconds() / 60.0
            if remain < 10:
                print(f"[SYNC_BUS v3.2] ⚠️ Lease của ca trực còn {remain:.0f} phút — "
                      f"chạy --heartbeat --agent <HOLDER> để gia hạn.")
    return data


# ==============================================================================
# 8. BỘ QUÉT & XỬ LÝ XUNG ĐỘT GOOGLE DRIVE (CONFLICT RESOLVER)
# ==============================================================================

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def scan_gdrive_conflicts(target_dir: Path = WORKSPACE_ROOT) -> List[Dict[str, Any]]:
    """
    Quét tìm các tệp tin xung đột đồng bộ Google Drive có định dạng: <tên_gốc> (1).<ext>, <tên_gốc> (2).<ext>...
    So sánh với tệp tin gốc về dung lượng, mtime và mã băm SHA-256.
    """
    conflicts = []
    dup_pattern = re.compile(r"^(.*?)\s\((\d+)\)(\.[a-zA-Z0-9_]+)$")

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "archive", "_archive", "00_Template_&_Standards"}]
        for f in files:
            m = dup_pattern.match(f)
            if not m:
                continue
            base_name = m.group(1) + m.group(3)
            dup_path = Path(root) / f
            base_path = Path(root) / base_name

            if not base_path.exists():
                conflicts.append({
                    "dup_path": str(dup_path),
                    "base_path": str(base_path),
                    "base_exists": False,
                    "is_identical": False,
                    "action_recommended": "RENAME_TO_BASE"
                })
                continue

            try:
                base_stat = base_path.stat()
                dup_stat = dup_path.stat()
                same_size = (base_stat.st_size == dup_stat.st_size)
                is_identical = same_size and (_file_hash(base_path) == _file_hash(dup_path))
                dup_is_newer = dup_stat.st_mtime > base_stat.st_mtime

                if is_identical:
                    action = "SAFE_DELETE_DUPLICATE"
                elif dup_is_newer:
                    action = "UPGRADE_BASE_WITH_DUPLICATE"  # Bản (1) mới hơn bản gốc
                else:
                    action = "KEEP_BASE_DELETE_DUPLICATE"   # Bản gốc mới hơn

                conflicts.append({
                    "dup_path": str(dup_path),
                    "base_path": str(base_path),
                    "base_exists": True,
                    "is_identical": is_identical,
                    "dup_is_newer": dup_is_newer,
                    "base_size": base_stat.st_size,
                    "dup_size": dup_stat.st_size,
                    "action_recommended": action
                })
            except Exception as e:
                conflicts.append({
                    "dup_path": str(dup_path),
                    "base_path": str(base_path),
                    "error": str(e)
                })

    return conflicts


def resolve_gdrive_conflicts(
    target_dir: Path = WORKSPACE_ROOT,
    dry_run: bool = True,
    backup_dir: Optional[Path] = None
) -> List[str]:
    """
    Xử lý tự động và an toàn các file xung đột Google Drive:
    - Nếu nội dung giống hệt: xóa file duplicate.
    - Nếu file duplicate mới hơn: sao lưu file cũ, ghi đè bản mới thành file gốc, rồi xóa duplicate.
    - Tuyệt đối không xóa nhầm mã nguồn mới của đồng nghiệp!
    """
    conflicts = scan_gdrive_conflicts(target_dir)
    results = []

    if backup_dir is None:
        backup_dir = WORKSPACE_ROOT / ".agents" / "_archive" / "gdrive_conflict_backups"

    for c in conflicts:
        dup = Path(c["dup_path"])
        base = Path(c["base_path"])
        action = c.get("action_recommended")

        if dry_run:
            results.append(f"[DRY-RUN] {dup.name} ➔ {action} (Gốc: {base.name})")
            continue

        try:
            if action == "SAFE_DELETE_DUPLICATE":
                dup.unlink()
                results.append(f"[DELETED_IDENTICAL] Đã xóa {dup.name}")
            elif action == "UPGRADE_BASE_WITH_DUPLICATE":
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_file = backup_dir / f"{base.stem}_pre_conflict_backup_{int(time.time())}{base.suffix}"
                shutil.copy2(base, backup_file)
                shutil.copy2(dup, base)
                dup.unlink()
                results.append(f"[UPGRADED_BASE] {base.name} được cập nhật từ {dup.name} mới hơn (đã backup: {backup_file.name})")
            elif action == "KEEP_BASE_DELETE_DUPLICATE":
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_file = backup_dir / f"{dup.stem}_dup_backup_{int(time.time())}{dup.suffix}"
                shutil.copy2(dup, backup_file)
                dup.unlink()
                results.append(f"[DELETED_OLDER_DUP] Bản gốc mới hơn, đã xóa {dup.name} (đã an toàn sao lưu: {backup_file.name})")
            elif action == "RENAME_TO_BASE":
                dup.rename(base)
                results.append(f"[RENAMED] Đã đổi {dup.name} thành {base.name}")
        except Exception as ex:
            results.append(f"[ERROR] Không thể xử lý {dup.name}: {ex}")

    return results


# ==============================================================================
# 9. GIAO DIỆN DÒNG LỆNH (CLI v3.0)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Giao thức Cầu nối File (Dual-Agent Bus v3.2) giữa Claude Code và Gemini Antigravity",
        add_help=False
    )
    # Lệnh truy vấn & Kiểm định
    parser.add_argument("--read", "-r", action="store_true", help="Đọc trạng thái hiện tại của bus")
    parser.add_argument("--validate", action="store_true", help="Kiểm tra tính hợp lệ của file bus hiện tại")
    parser.add_argument("--heartbeat", action="store_true",
                        help="v3.2: Gia hạn lease ca trực (chỉ hợp lệ khi agent là holder IN_PROGRESS)")

    # Lệnh quản lý vòng đời ca trực
    parser.add_argument("--claim", action="store_true", help="Nhận ca làm việc (chuyển handoff_status -> IN_PROGRESS)")
    parser.add_argument("--complete", action="store_true", help="Hoàn tất ca làm việc (chuyển handoff_status -> COMPLETED)")
    parser.add_argument("--need-review", action="store_true", help="Yêu cầu kiểm tra chéo (chuyển handoff_status -> NEED_REVIEW)")
    parser.add_argument("--agent", type=str, default="CLAUDE", help="Tên tác tử thực hiện thao tác vòng đời")

    # Bàn giao tự động
    parser.add_argument("--agent-selection", choices=("AUTO", "CLAUDE_ONLY", "GEMINI_ONLY", "DUAL"))
    parser.add_argument("--dispatch-ticket", type=Path, help="Phiếu do dispatch_task.py prepare tạo")
    parser.add_argument("--approval-record", type=Path, help="Xác nhận của người dùng trước khi xuất")
    parser.add_argument("--review-record", type=Path, help="Xác nhận kiểm tra phiên bản cuối")
    parser.add_argument("--auto", action="store_true", help="Kích hoạt chế độ bàn giao tự động")
    parser.add_argument("--confirm", action="store_true", help="Xác nhận trạng thái hoàn thành và chuyển giao")
    parser.add_argument("--sender", type=str, default="GEMINI", help="Tác tử gửi (GEMINI, CLAUDE, USER...)")
    parser.add_argument("--target", type=str, default="CLAUDE", help="Tác tử nhận (CLAUDE, GEMINI, SUBAGENT...)")
    parser.add_argument("--project", type=str, default="MASTER_SYSTEM", help="Mã dự án (ví dụ 01_MONTALP, 02_SS1...)")
    parser.add_argument("--project-dir", type=str, default=None,
                        help="v3.2: Đường dẫn thư mục dự án hiện tại — thu hẹp phạm vi quét artifacts")
    parser.add_argument("--purpose", type=str, default="Phối hợp liên tác tử theo mục tiêu dự án", help="Mục tiêu của dự án")
    parser.add_argument("--roles", type=str, default="Linh hoạt tùy mục đích dự án", help="Phân vai động")
    parser.add_argument("--summary", type=str, default="", help="Tóm tắt công việc đã làm")
    parser.add_argument("--files", type=str, default="", help="Danh sách tệp phân cách bằng dấu phẩy")
    parser.add_argument("--complete-files", type=str, default="",
                        help="v3.2: Tệp đính kèm khi --complete (phân cách bằng dấu phẩy), dùng cho Visual Gate")

    # Cấu trúc hóa lệnh & Tiêu chí nghiệm thu v3.0
    parser.add_argument("--task", type=str, default="", help="Mô tả nhiệm vụ cụ thể cho đối tác")
    parser.add_argument("--next-cmd", type=str, default="", help="Lệnh hành động tiếp theo cho đối tác")
    parser.add_argument("--target-files", type=str, default="", help="Các tệp trọng tâm phân cách bằng dấu phẩy")
    parser.add_argument("--criteria", type=str, default="", help="Tiêu chí nghiệm thu phân cách bằng dấu chấm phẩy (;)")
    parser.add_argument("--status", type=str, default=None, help="Trạng thái bàn giao tùy chỉnh")
    parser.add_argument("--force", action="store_true",
                        help="Bỏ qua cảnh báo IN_PROGRESS/Visual Gate và ghi đè bus (v3.3: bypass được ghi RECEIPT)")

    # v3.3 Product-First (hợp đồng bàn giao sản phẩm)
    parser.add_argument("--action-type", type=str, default="DYNAMIC",
                        help="v3.3: Loại việc (CAD|DOCX|CODE|META|...) — điều khiển Visual Gate; "
                             "CODE/META/TEST/DOCS được miễn gate, CAD/DOCX bắt buộc bằng chứng")
    parser.add_argument("--deliverable", type=str, default=None,
                        help="v3.3: Sản phẩm mong đợi của ca này (mô tả ngắn, cụ thể)")
    parser.add_argument("--evidence-files", type=str, default="",
                        help="v3.3: Tệp bằng chứng nghiệm thu (phân cách dấu phẩy) — phải khớp "
                             "preview .png/.jpg/.webp hoặc log _verification.json; "
                             "kết hợp --check-evidence-on-disk để bắt file TỒN TẠI trên đĩa")
    parser.add_argument("--acceptance-cmd", type=str, default=None,
                        help="v3.3: Lệnh chạy lại được để tự chứng minh ca xong (deterministic)")
    parser.add_argument("--check-evidence-on-disk", action="store_true",
                        help="v3.3: Visual Gate kiểm bằng chứng THẬT SỰ TỒN TẠI trên đĩa (SHA-256), "
                             "không chấp nhận danh khai suông")
    parser.add_argument("--receipt-reason", type=str, default="",
                        help="v3.3: Lý do (bắt buộc ghi rõ khi --force) — lưu vào RECEIPT để audit")

    # v3.3 Report Gate (chuẩn RESULT.md theo ca)
    parser.add_argument("--emit-report", action="store_true",
                        help="v3.3: Sinh skeleton RESULT.md 5 mục vào .agents/memory/audits/"
                             "<project>/<PHASE>_<AGENT>_RESULT.md trước bàn giao (không ghi đè)")
    parser.add_argument("--report-file", type=str, default=None,
                        help="v3.3: Chỉ định file báo cáo pha (RESULT.md) hiện có cho ca này")
    parser.add_argument("--phase", type=str, default="SHIFT",
                        help="v3.3: Số hiệu pha/ca (vd C1, G2, A1) — dùng cho tên RESULT.md")

    # Xử lý xung đột Google Drive
    parser.add_argument("--scan-conflicts", action="store_true", help="Quét tìm các tệp tin xung đột Google Drive (1), (2)")
    parser.add_argument("--clean-conflicts", action="store_true", help="Xử lý an toàn các tệp xung đột Google Drive")

    parser.add_argument("--help", "-h", action="store_true", help="Hiển thị hướng dẫn sử dụng")

    # Cú pháp vị trí cũ: <SENDER> <TARGET> <SUMMARY> <NEXT_COMMAND> <FILES_CSV> [STATUS]
    if len(sys.argv) >= 6 and not sys.argv[1].startswith("-"):
        sender = sys.argv[1]
        target = sys.argv[2]
        summary = sys.argv[3]
        next_cmd = sys.argv[4]
        files_str = sys.argv[5]
        status = sys.argv[6] if len(sys.argv) > 6 else "PENDING_PARTNER_ACTION"
        post_handoff(sender, target, summary, next_cmd, files_str.split(","), status)
        return

    args, unknown = parser.parse_known_args()

    if args.help:
        parser.print_help()
        return

    if args.read or (len(sys.argv) == 2 and sys.argv[1] in ("read", "--read", "-r")):
        read_bus()
        return

    if args.heartbeat:
        heartbeat(args.agent)
        return

    if args.validate:
        data = read_bus(validate=False)
        is_valid, reason = validate_bus_payload(data)
        if is_valid:
            print(f"[SYNC_BUS v3.2] ✅ File bus hợp lệ 100% theo tiêu chuẩn.")
            sys.exit(0)
        else:
            print(f"[SYNC_BUS v3.2] ❌ File bus không hợp lệ: {reason}")
            sys.exit(1)

    if args.claim:
        claim_task(args.agent, force=args.force)
        return

    if args.complete:
        complete_files = [f.strip() for f in args.complete_files.split(",") if f.strip()] if args.complete_files else None
        complete_task(args.agent, summary=args.summary, files=complete_files, force=args.force,
                      reason=args.receipt_reason, report_file=args.report_file,
                      approval_record=json.loads(args.approval_record.read_text(encoding="utf-8-sig")) if args.approval_record else None,
                      review_record=json.loads(args.review_record.read_text(encoding="utf-8-sig")) if args.review_record else None)
        return

    if args.need_review:
        request_review(args.agent, summary=args.summary, next_agent=args.target, force=args.force,
                       reason=args.receipt_reason, report_file=args.report_file)
        return

    if args.scan_conflicts:
        confs = scan_gdrive_conflicts(WORKSPACE_ROOT)
        print(f"[SYNC_BUS v3.2] Phát hiện {len(confs)} tệp xung đột Google Drive:")
        for c in confs:
            print(f"  • {Path(c['dup_path']).name} ➔ Khuyến nghị: {c.get('action_recommended', 'N/A')}")
        return

    if args.clean_conflicts:
        is_dry = not args.confirm
        res = resolve_gdrive_conflicts(WORKSPACE_ROOT, dry_run=is_dry)
        print(f"[SYNC_BUS v3.2] Kết quả xử lý xung đột (Dry-run: {is_dry}):")
        for r in res:
            print(f"  {r}")
        if is_dry:
            print("\n💡 Chạy thêm cờ --confirm để áp dụng thay đổi thực tế.")
        return

    if args.auto:
        file_list = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else None
        target_file_list = [f.strip() for f in args.target_files.split(",") if f.strip()] if args.target_files else None
        criteria_list = [c.strip() for c in args.criteria.split(";") if c.strip()] if args.criteria else None
        evidence_list = [f.strip() for f in args.evidence_files.split(",") if f.strip()] if args.evidence_files else None

        result = auto_handoff(
            agent_selection=args.agent_selection,
            dispatch_ticket=json.loads(args.dispatch_ticket.read_text(encoding="utf-8-sig")) if args.dispatch_ticket else None,
            sender=args.sender,
            target=args.target,
            summary=args.summary or "Tự động bàn giao sau khi hoàn tất công việc.",
            next_cmd=args.next_cmd or args.task or "Tiếp tục kiểm tra và thực thi theo kế hoạch.",
            project_code=args.project,
            project_purpose=args.purpose,
            role_distribution=args.roles,
            files=file_list,
            auto_detect_files=True,
            confirmed=args.confirm or True,
            status=args.status,
            handoff_status="PENDING",
            task_description=args.task,
            target_files=target_file_list,
            acceptance_criteria=criteria_list,
            action_type=args.action_type,
            force=args.force,
            project_dir=Path(args.project_dir).resolve() if args.project_dir else None,
            # v3.3 Product-First
            deliverable=args.deliverable,
            evidence_files=evidence_list,
            acceptance_cmd=args.acceptance_cmd,
            check_evidence_on_disk=args.check_evidence_on_disk,
            receipt_reason=args.receipt_reason,
            # v3.3 Report Gate
            report_file=args.report_file,
            phase=args.phase,
            emit_report=args.emit_report,
        )
        if "dispatch_2d" in result:
            print(json.dumps(result, ensure_ascii=False))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
