# -*- coding: utf-8 -*-
"""
skill_guard.py — Cầu nối kiểm soát hệ thống cho các Skill (v1.0)

Cung cấp một lớp trung gian để gắn `SystemController.preflight_check()` vào
cổng vào của bất kỳ Skill nào mà không phải sửa logic nghiệp vụ bên trong.

Pattern sử dụng (bọc quanh một hàm thực thi tool):

    from skill_guard import guarded

    @guarded(actor="Structural_Design_Engineer", tool="calc_rc_section")
    def run_calc(payload):
        ...

hoặc gọi trực tiếp trong main():

    from skill_guard import preflight
    ok, reason = preflight("Structural_Design_Engineer", "calc_rc_section", payload)
    if not ok:
        print(reason); sys.exit(2)

Nguyên tắc Fail-Closed: nếu controller lỗi, mặc định CHẶN (không cho chạy).
Để cho phép, truyền fail_open=True.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

# Đảm bảo UTF-8 theo AGENTS.md §2
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from system_controller import system_controller  # noqa: E402

__all__ = ["preflight", "guarded", "controller", "GuardBlocked"]


class GuardBlocked(RuntimeError):
    """Ngoại lệ ném ra khi preflight chặn thao tác."""

    def __init__(self, reason: str, status: str = "BLOCKED"):
        super().__init__(reason)
        self.reason = reason
        self.status = status


controller = system_controller


def preflight(
    actor: str,
    tool: str,
    payload: Optional[Dict[str, Any]] = None,
    fail_open: bool = False,
) -> Tuple[bool, str]:
    """
    Chạy kiểm tra an toàn trước khi thực thi tool.

    Returns:
        (allowed, reason)

    Ghi chú: `preflight_check` ghi nhận 1 hop vào LoopBreaker (bộ điều khiển global)
    của SystemController. Khi vòng lặp bị phát hiện (LOOP_BLOCKED), trajectory được
    reset để không lặp lại cùng cảnh — các lần gọi hợp lệ trong cùng process
    (vd workflow harness chạy nhiều stage) vẫn được tích luỹ để phát hiện ping-pong.
    """
    try:
        res = controller.preflight_check(actor, tool, payload or {})
        allowed = bool(res.get("allowed"))
        reason = res.get("reason", "")
        if not allowed:
            reason = f"[{res.get('status', 'BLOCKED')}] {reason}"
            if res.get("status") == "LOOP_BLOCKED":
                controller.loop_breaker.reset()
        return allowed, reason
    except Exception as e:
        # Fail-Closed theo mặc định: lỗi hệ thống kiểm soát => chặn thực thi.
        if fail_open:
            return True, f"[FAIL_OPEN] Bộ kiểm soát lỗi ({e}) — cho phép tiếp tục."
        return False, f"[CONTROLLER_ERROR] Bộ kiểm soát hệ thống gặp lỗi ({e}); chặn thực thi theo nguyên tắc Fail-Closed."


def guarded(
    actor: str,
    tool: Optional[str] = None,
    fail_open: bool = False,
):
    """
    Decorator bọc hàm thực thi tool với preflight check.

    Args:
        actor: Tên tác tử gọi (ví dụ "Structural_Design_Engineer").
        tool: Tên tool; mặc định lấy theo tên hàm được bọc.
        fail_open: Cho phép chạy tiếp nếu controller lỗi (mặc định False = Fail-Closed).
    """
    def decorator(func: Callable) -> Callable:
        tool_name = tool or func.__name__

        def wrapper(*args, **kwargs):
            allowed, reason = preflight(actor, tool_name, {}, fail_open=fail_open)
            if not allowed:
                raise GuardBlocked(reason)
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__wrapped__ = func
        return wrapper

    return decorator


if __name__ == '__main__':
    # Kiểm tra nhanh
    ok, why = preflight("Global_Dispatcher", "read_only_probe")
    print("ALLOW case:", ok, "|", why)

    ok, why = preflight("Global_Dispatcher", "revit_delete_elements")
    print("DELETE case:", ok, "|", why)

    ok, why = preflight("Global_Dispatcher", "run_shell", {"command": "rm -rf /"})
    print("DANGEROUS case:", ok, "|", why)
