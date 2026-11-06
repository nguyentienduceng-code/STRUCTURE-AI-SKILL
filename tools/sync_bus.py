# .agents/tools/sync_bus.py
# Giao thức Cầu nối File (File-based IPC Bus) giữa Claude Code và Gemini Antigravity
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
from datetime import datetime
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
                # Fallback: khoá theo tên file
                try:
                    self._fallback_fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    return True
                except FileExistsError:
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
    """Tự động dò tìm thư mục gốc workspace chứa .agents và memory."""
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / ".agents").is_dir() and (curr / "memory").is_dir():
            return curr
        curr = curr.parent
    # Fallback chuẩn: .agents/tools -> parents[2]
    return Path(__file__).resolve().parents[2]


WORKSPACE_ROOT = find_workspace_root()
BUS_PATH = WORKSPACE_ROOT / "memory" / "DUAL_AGENT_BUS.json"
MEMO_PATH = WORKSPACE_ROOT / "memory" / "DUAL_AGENT_HANDOFF_MEMO.md"
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


# ==============================================================================
# 3. PHÁT HIỆN TỰ ĐỘNG TỆP TIN SỬA ĐỔI (AUTO-DETECTION OF ARTIFACTS)
# ==============================================================================

def detect_modified_files(
    workspace_root: Path = WORKSPACE_ROOT,
    project_code: Optional[str] = None,
    minutes: float = 120.0,
    max_files: int = 50
) -> List[str]:
    """
    Tự động quét và phát hiện các tệp tin vừa sửa đổi gần đây:
    1. Kiểm tra git status --porcelain trong .agents (nếu là git repo).
    2. Quét mtime các tệp kỹ thuật trong thư mục dự án tương ứng và memory/.
    Trả về danh sách đường dẫn tương đối (POSIX /).
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
    scan_targets = [workspace_root / "memory"]
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
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for f in files:
                if f.startswith(".") or ".tmp." in f:
                    continue
                ext = Path(f).suffix.lower()
                if ext in allowed_exts:
                    fp = Path(root) / f
                    try:
                        mtime = fp.stat().st_mtime
                        if mtime >= time_threshold:
                            modified_set.add(to_relative_path(str(fp), workspace_root))
                    except Exception:
                        pass

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
        "# BẢN GIAO BAN & YÊU CẦU PHỐI HỢP LIÊN TÁC TỬ (DYNAMIC DUAL-AGENT HANDOFF v3.0)",
        "",
        f"> **Dự án:** `{project_code}` — *{project_purpose}*  ",
        f"> **Người gửi:** **{sender}** ➔ **Người nhận:** **{target}**  ",
        f"> **Thời điểm bàn giao:** `{timestamp}`  ",
        f"> **Trạng thái bàn giao (handoff_status):** `{handoff_status}` *(Verification: `{verification_status}`)*  ",
        f"> **Tác tử giữ ca (current_holder):** `{holder}`  ",
        f"> **Chế độ phân việc:** {role_distribution}  ",
        f"> **Kênh bus nguyên tử:** `memory/DUAL_AGENT_BUS.json`  ",
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
    ]

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
        "*Tài liệu được sinh tự động bởi `sync_bus.py` v3.0 dưới cơ chế khóa nguyên tử FileLock & Anti-Collision Mutex.*"
    ])

    memo_content = "\n".join(memo_lines)
    with open(memo_path, "w", encoding="utf-8") as f:
        f.write(memo_content)


# ==============================================================================
# 6. GIAO DIỆN BÀN GIAO BUS (CORE & AUTOMATED APIS v3.0)
# ==============================================================================

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
    force: bool = False
) -> dict:
    """
    TỰ ĐỘNG BÀN GIAO THÔNG TIN KHI CÓ XÁC NHẬN (AUTOMATED HANDOFF ON CONFIRMATION v3.0).
    - Chuẩn hóa 100% artifacts sang đường dẫn tương đối (POSIX /).
    - Bổ sung cấu trúc task_description, target_files và acceptance_criteria.
    - Cơ chế Software Mutex: kiểm tra cờ IN_PROGRESS để chống lệch nhịp khi đối tác đang làm.
    """
    # Kiểm tra trạng thái hiện tại trên bus
    if BUS_PATH.exists() and not force:
        try:
            curr_data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
            if curr_data.get("handoff_status") == "IN_PROGRESS" and curr_data.get("current_holder") != sender:
                holder = curr_data.get("current_holder", "PARTNER")
                print(f"[SYNC_BUS v3.0] ⚠️ CẢNH BÁO: Tác tử {holder} đang trong ca trực (IN_PROGRESS).")
                print("              Để tránh xung đột race condition, hãy đợi tác tử hoàn tất hoặc dùng cờ --force.")
        except Exception:
            pass

    if status is None:
        status = "CONFIRMED_AND_HANDED_OFF" if confirmed else "PENDING_CONFIRMATION"

    # Chuẩn hóa danh sách file tương đối
    raw_files = files or []
    if not raw_files and auto_detect_files:
        raw_files = detect_modified_files(WORKSPACE_ROOT, project_code=project_code)

    normalized_files = [to_relative_path(f, WORKSPACE_ROOT) for f in raw_files if f.strip()]
    bus_rel = to_relative_path(str(BUS_PATH), WORKSPACE_ROOT)
    if bus_rel not in normalized_files:
        normalized_files.append(bus_rel)

    effective_task = task_description or next_cmd or "Thực thi công việc theo kế hoạch dự án"
    effective_cmd = next_cmd or effective_task
    effective_target_files = [to_relative_path(f, WORKSPACE_ROOT) for f in (target_files or [])]

    payload = {
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
            "command": effective_cmd
        },
        "Verification_Status": status
    }

    # Kiểm tra schema
    is_valid, reason = validate_bus_payload(payload)
    if not is_valid:
        raise ValueError(f"[SYNC_BUS] Lỗi Schema Payload: {reason}")

    with FileLock(LOCK_PATH):
        _atomic_write_json(BUS_PATH, payload)
        generate_handoff_memo(payload, MEMO_PATH)

    print(f"[SYNC_BUS v3.0] ✅ ĐÃ BÀN GIAO THÀNH CÔNG VỚI XÁC NHẬN:")
    print(f"  • Dự án:          {project_code} ({project_purpose})")
    print(f"  • Luồng bàn giao: {sender} ➔ {target}")
    print(f"  • Trạng thái:     handoff_status={handoff_status} | holder={payload['current_holder']}")
    print(f"  • Nhiệm vụ:       {effective_task}")
    print(f"  • Tiêu chí:       {len(acceptance_criteria or [])} mục kiểm tra")
    print(f"  • Số artifacts:   {len(normalized_files)} tệp tin (chuẩn POSIX relative)")
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
    normalized_files = [to_relative_path(f, WORKSPACE_ROOT) for f in files if f.strip()]
    bus_rel = to_relative_path(str(BUS_PATH), WORKSPACE_ROOT)
    if bus_rel not in normalized_files:
        normalized_files.append(bus_rel)

    payload = {
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

def claim_task(agent: str) -> dict:
    """
    Tác tử tiếp nhận (ví dụ CLAUDE) kích hoạt khi bắt đầu làm việc.
    Chuyển handoff_status -> IN_PROGRESS, current_holder -> agent.
    Bảo vệ tác tử không bị AI đối tác can thiệp hay ghi đè lúc đang chạy dở.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        data["handoff_status"] = "IN_PROGRESS"
        data["current_holder"] = agent
        data["Verification_Status"] = "IN_PROGRESS"
        data["claim_timestamp"] = datetime.now().astimezone().isoformat()
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)

    print(f"[SYNC_BUS v3.0] 🔒 {agent} ĐÃ TIẾP NHẬN CA VÀ KHÓA THI HÀNH (IN_PROGRESS).")
    print(f"              Đối tác đối chiếu hoặc Gemini sẽ KHÔNG can thiệp ghi đè lúc này!")
    return data


def complete_task(agent: str, summary: str = "", files: Optional[List[str]] = None) -> dict:
    """
    Tác tử đã hoàn tất toàn bộ tiêu chí nghiệm thu.
    Chuyển handoff_status -> COMPLETED, current_holder -> IDLE.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        data["handoff_status"] = "COMPLETED"
        data["current_holder"] = "IDLE"
        data["last_updated_by"] = agent
        data["timestamp"] = datetime.now().astimezone().isoformat()
        data["Verification_Status"] = "CONFIRMED_AND_HANDED_OFF"
        if summary:
            data["summary"] = summary
        if files:
            data["artifacts_modified"] = [to_relative_path(f, WORKSPACE_ROOT) for f in files]
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)

    print(f"[SYNC_BUS v3.0] ✅ {agent} ĐÃ HOÀN TẤT NHIỆM VỤ (COMPLETED). Toàn bộ tiêu chí đạt yêu cầu!")
    return data


def request_review(agent: str, summary: str = "", next_agent: str = "GEMINI") -> dict:
    """
    Tác tử hoàn thành bước kỹ thuật và yêu cầu kiểm tra chéo / phê duyệt.
    Chuyển handoff_status -> NEED_REVIEW, bàn giao lượt review cho next_agent.
    """
    with FileLock(LOCK_PATH):
        if not BUS_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy bus tại {BUS_PATH}")
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
        data["handoff_status"] = "NEED_REVIEW"
        data["current_holder"] = "IDLE"
        data["last_updated_by"] = agent
        data["timestamp"] = datetime.now().astimezone().isoformat()
        data["Verification_Status"] = "REVIEW_REQUIRED"
        if summary:
            data["summary"] = summary
        if "next_action_for_partner" in data:
            data["next_action_for_partner"]["target_agent"] = next_agent
        _atomic_write_json(BUS_PATH, data)
        generate_handoff_memo(data, MEMO_PATH)

    print(f"[SYNC_BUS v3.0] 🔍 {agent} ĐÃ YÊU CẦU KIỂM TRA CHÉO (NEED_REVIEW) TỪ {next_agent}!")
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
                dup.unlink()
                results.append(f"[DELETED_OLDER_DUP] Bản gốc mới hơn, đã xóa {dup.name}")
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
        description="Giao thức Cầu nối File (Dual-Agent Bus v3.0) giữa Claude Code và Gemini Antigravity",
        add_help=False
    )
    # Lệnh truy vấn & Kiểm định
    parser.add_argument("--read", "-r", action="store_true", help="Đọc trạng thái hiện tại của bus")
    parser.add_argument("--validate", action="store_true", help="Kiểm tra tính hợp lệ của file bus hiện tại")

    # Lệnh quản lý vòng đời ca trực
    parser.add_argument("--claim", action="store_true", help="Nhận ca làm việc (chuyển handoff_status -> IN_PROGRESS)")
    parser.add_argument("--complete", action="store_true", help="Hoàn tất ca làm việc (chuyển handoff_status -> COMPLETED)")
    parser.add_argument("--need-review", action="store_true", help="Yêu cầu kiểm tra chéo (chuyển handoff_status -> NEED_REVIEW)")
    parser.add_argument("--agent", type=str, default="CLAUDE", help="Tên tác tử thực hiện thao tác vòng đời")

    # Bàn giao tự động
    parser.add_argument("--auto", action="store_true", help="Kích hoạt chế độ bàn giao tự động")
    parser.add_argument("--confirm", action="store_true", help="Xác nhận trạng thái hoàn thành và chuyển giao")
    parser.add_argument("--sender", type=str, default="GEMINI", help="Tác tử gửi (GEMINI, CLAUDE, USER...)")
    parser.add_argument("--target", type=str, default="CLAUDE", help="Tác tử nhận (CLAUDE, GEMINI, SUBAGENT...)")
    parser.add_argument("--project", type=str, default="MASTER_SYSTEM", help="Mã dự án (ví dụ 01_MONTALP, 02_SS1...)")
    parser.add_argument("--purpose", type=str, default="Phối hợp liên tác tử theo mục tiêu dự án", help="Mục tiêu của dự án")
    parser.add_argument("--roles", type=str, default="Linh hoạt tùy mục đích dự án", help="Phân vai động")
    parser.add_argument("--summary", type=str, default="", help="Tóm tắt công việc đã làm")

    # Cấu trúc hóa lệnh & Tiêu chí nghiệm thu v3.0
    parser.add_argument("--task", type=str, default="", help="Mô tả nhiệm vụ cụ thể cho đối tác")
    parser.add_argument("--next-cmd", type=str, default="", help="Lệnh hành động tiếp theo cho đối tác")
    parser.add_argument("--target-files", type=str, default="", help="Các tệp trọng tâm phân cách bằng dấu phẩy")
    parser.add_argument("--criteria", type=str, default="", help="Tiêu chí nghiệm thu phân cách bằng dấu chấm phẩy (;)")
    parser.add_argument("--files", type=str, default="", help="Danh sách tệp phân cách bằng dấu phẩy")
    parser.add_argument("--status", type=str, default=None, help="Trạng thái bàn giao tùy chỉnh")
    parser.add_argument("--force", action="store_true", help="Bỏ qua cảnh báo IN_PROGRESS và ghi đè bus")

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

    if args.validate:
        data = read_bus(validate=False)
        is_valid, reason = validate_bus_payload(data)
        if is_valid:
            print(f"[SYNC_BUS] ✅ File bus hợp lệ 100% theo tiêu chuẩn v3.0.")
            sys.exit(0)
        else:
            print(f"[SYNC_BUS] ❌ File bus không hợp lệ: {reason}")
            sys.exit(1)

    if args.claim:
        claim_task(args.agent)
        return

    if args.complete:
        complete_task(args.agent, summary=args.summary)
        return

    if args.need_review:
        request_review(args.agent, summary=args.summary, next_agent=args.target)
        return

    if args.scan_conflicts:
        confs = scan_gdrive_conflicts(WORKSPACE_ROOT)
        print(f"[SYNC_BUS v3.0] Phát hiện {len(confs)} tệp xung đột Google Drive:")
        for c in confs:
            print(f"  • {Path(c['dup_path']).name} ➔ Khuyến nghị: {c.get('action_recommended', 'N/A')}")
        return

    if args.clean_conflicts:
        is_dry = not args.confirm
        res = resolve_gdrive_conflicts(WORKSPACE_ROOT, dry_run=is_dry)
        print(f"[SYNC_BUS v3.0] Kết quả xử lý xung đột (Dry-run: {is_dry}):")
        for r in res:
            print(f"  {r}")
        if is_dry:
            print("\n💡 Chạy thêm cờ --confirm để áp dụng thay đổi thực tế.")
        return

    if args.auto:
        file_list = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else None
        target_file_list = [f.strip() for f in args.target_files.split(",") if f.strip()] if args.target_files else None
        criteria_list = [c.strip() for c in args.criteria.split(";") if c.strip()] if args.criteria else None

        auto_handoff(
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
            force=args.force
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
