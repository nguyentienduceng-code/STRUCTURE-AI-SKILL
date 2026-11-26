# -*- coding: utf-8 -*-
"""Bootstrap matrix — khóa hành vi fail-closed của wrapper hook_bootstrap.cmd.

Vận hành qua Google Drive trên nhiều máy: wrapper phải tự chọn Python hợp lệ
và fail-closed (exit 125) khi chỉ có stub WindowsApps. Bộ test này khóa 4 case
để tránh tái phát hiện tượng "The system cannot find the path specified".

Chỉ chạy trên Windows (wrapper là .cmd). Mọi thao tác đều khôi phục PATH và
cache Python về trạng thái ban đầu; không đụng BUS hay cấu hình production.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(__file__).resolve().parents[2]
WRAPPER = WORKSPACE / "bootstrap" / "hook_bootstrap.cmd"
CACHE = Path(os.environ.get("LOCALAPPDATA", "")) / "GoogleAIStudio" / "python_exe.cache"
SAFE_CMD = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "cmd.exe")

# Payload hợp lệ (doi duong POSIX, khong escape) — hook se tra "allow".
PAYLOAD = (
    '{"hook_event_name":"PreToolUse","tool_name":"Bash",'
    '"tool_input":{"command":"git status"},"cwd":"g:/My Drive/Google AI Studio"}'
)


def _run_wrapper(path_value, pyexe_env, payload=PAYLOAD):
    """Run wrapper with a controlled PATH/PYTHON_EXECUTABLE, return exit code."""
    env = dict(os.environ)
    env["PATH"] = path_value
    if pyexe_env is None:
        env.pop("PYTHON_EXECUTABLE", None)
    else:
        env["PYTHON_EXECUTABLE"] = pyexe_env
    # Wrapper reads cache first; clear it so discovery is deterministic, then restore it.
    cache_backup = CACHE.read_bytes() if CACHE.is_file() else None
    if CACHE.exists():
        CACHE.unlink()
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            fh.write(payload)
            tmp = fh.name
        out = subprocess.run(
            f'"{WRAPPER}" claude_safety_hook.py < "{tmp}"',
            shell=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return out.returncode
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        if cache_backup is not None:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_bytes(cache_backup)
        elif CACHE.exists():
            try:
                CACHE.unlink()
            except OSError:
                pass


def _real_python():
    for name in ("python", "python3"):
        p = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        # Prefer the actual interpreter this test process runs under.
        break
    return sys.executable


class BootstrapMatrixTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32" and WRAPPER.exists(),
                         "Windows-only wrapper")
    def test_windowsapps_stub_only_fails_closed(self):
        stub = Path(tempfile.gettempdir()) / "WindowsApps"
        stub.mkdir(exist_ok=True)
        for exe in ("py.exe", "python.exe"):
            (stub / exe).write_text("@echo off\n", encoding="ascii")
        try:
            rc = _run_wrapper(str(stub), None)
            self.assertEqual(rc, 125, f"stub-only must fail-closed 125, got {rc}")
        finally:
            for exe in ("py.exe", "python.exe"):
                p = stub / exe
                if p.exists():
                    p.unlink()

    @unittest.skipUnless(sys.platform == "win32" and WRAPPER.exists(),
                         "Windows-only wrapper")
    def test_real_python_allows(self):
        rc = _run_wrapper(os.environ["PATH"], None)
        self.assertEqual(rc, 0, f"real python should allow, got {rc}")

    @unittest.skipUnless(sys.platform == "win32" and WRAPPER.exists(),
                         "Windows-only wrapper")
    def test_python_executable_override(self):
        rc = _run_wrapper(os.environ["PATH"], _real_python())
        self.assertEqual(rc, 0, f"PYTHON_EXECUTABLE override should allow, got {rc}")

    @unittest.skipUnless(sys.platform == "win32" and WRAPPER.exists(),
                         "Windows-only wrapper")
    def test_no_python_anywhere_fails_closed(self):
        empty = Path(tempfile.gettempdir()) / "no_python_here"
        empty.mkdir(exist_ok=True)
        rc = _run_wrapper(str(empty), None)
        self.assertEqual(rc, 125, f"no-python must fail-closed 125, got {rc}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
