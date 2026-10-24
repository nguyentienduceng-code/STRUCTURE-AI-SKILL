# .agents/tools/sync_bus.py
# Giao thức Cầu nối File (File-based IPC Bus) giữa Claude Code và Gemini Antigravity
#
# v1.1 (Claude review — vá CVE-2025-68146):
#   - Ghi file NGYUÊN TỬ: ghi ra file tạm cùng thư mục rồi os.replace().
#     Trước đây dùng write_text() trực tiếp — nếu tiến trình bị ngắt giữa chừng
#     hoặc 2 Agent ghi đồng thời, file bus có thể bị để lại JSON cắt cụt/hỏng.
#   - Khoá tệp (lock) chống race condition giữa Claude và Gemini khi chạy song song.
#   - Khoá đặt ở thư mục tạm CẢNH BÁO (local disk), KHÔNG đặt trên ổ Google Drive (G:)
#     vì Google Drive không hỗ trợ khoá file tương thích POSIX -> mọi lock sẽ hỏng.
#   - KHÔNG phụ thuộc thư viện ngoài: tự cài FileLock tối giản bằng msvcrt (Windows)
#     và fcntl (POSIX), fallback sang khoá theo tên file (O_EXCL) nếu không có.
#
# Usage:
#   python sync_bus.py <SENDER> <TARGET> <SUMMARY> <NEXT_COMMAND> <FILES_CSV> [STATUS]
#   python sync_bus.py --read

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

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
# KHOÁ TỆP TỐI GIẢN (không cần thư viện ngoài)
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
# BUS
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
LOCK_PATH = LOCK_DIR / LOCK_FILENAME


def _atomic_write_json(path: Path, payload: dict) -> None:
    """
    Ghi JSON nguyên tử.
    Ghi ra file tạm CÙNG THƯ MỤC (bắt buộc để os.replace() cùng filesystem),
    fsync rồi replace — không bao giờ để lại file nửa vời.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + f".tmp.{os.getpid()}")
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


def post_handoff(sender: str, target: str, summary: str, next_cmd: str, files: list[str], status: str = "PENDING_ACTION"):
    """Ghi trạng thái bàn giao vào DUAL_AGENT_BUS.json (nguyên tử + có khoá)."""
    payload = {
        "last_updated_by": sender,
        "timestamp": datetime.now().astimezone().isoformat(),
        "summary": summary,
        "artifacts_modified": [f.strip() for f in files if f.strip()],
        "next_action_for_partner": {
            "target_agent": target,
            "command": next_cmd
        },
        "Verification_Status": status
    }
    with FileLock(LOCK_PATH):
        _atomic_write_json(BUS_PATH, payload)
    print(f"[SYNC_BUS] ✅ Đã bàn giao trạng thái từ {sender} -> {target}")
    print(f"           Vị trí: {BUS_PATH}")
    print(f"           Lệnh tiếp theo: {next_cmd}")


def read_bus() -> dict:
    """Đọc trạng thái hiện tại từ bus."""
    if not BUS_PATH.exists():
        print(f"[SYNC_BUS] ⚠️ File bus chưa tồn tại tại {BUS_PATH}")
        return {}
    with FileLock(LOCK_PATH):
        data = json.loads(BUS_PATH.read_text(encoding="utf-8"))
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def show_usage():
    print("Sử dụng sync_bus.py:")
    print("  python .agents/tools/sync_bus.py <SENDER> <TARGET> <SUMMARY> <NEXT_COMMAND> <FILES_COMMA_SEPARATED> [STATUS]")
    print("\nVí dụ:")
    print('  python .agents/tools/sync_bus.py CLAUDE GEMINI "Đã viết xong 4 script" "Chạy test và tổng hợp" "file1.py,file2.py"')
    print("\nĐọc trạng thái hiện tại:")
    print("  python .agents/tools/sync_bus.py --read")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in ("--read", "-r", "read"):
        read_bus()
        sys.exit(0)

    if len(sys.argv) < 6:
        show_usage()
        sys.exit(1)

    sender = sys.argv[1]
    target = sys.argv[2]
    summary = sys.argv[3]
    next_cmd = sys.argv[4]
    files_str = sys.argv[5]
    status = sys.argv[6] if len(sys.argv) > 6 else "PENDING_PARTNER_ACTION"

    post_handoff(sender, target, summary, next_cmd, files_str.split(","), status)
