# -*- coding: utf-8 -*-
"""
skill_guard.py — Cầu nối kiểm soát hệ thống cho các Skill (v2.0)

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

--------------------------------------------------------------------------
v2.0 (2026-10-25) — Sửa lỗi Fail-Open ngầm (BUG-014)
--------------------------------------------------------------------------
v1.0 tuyên bố nguyên tắc "Fail-Closed" nhưng cả 3 skill gọi vào đều hard-code
`fail_open=True` -> khi hệ thống kiểm soát lỗi, thao tác vẫn chạy tự do.

v2.0 phân biệt RÕ 2 tình huống khác nhau về mặt an toàn:

  1. CONTROLLER LỖI (đã cài, nhưng preflight_check ném exception)
     -> CHẶN. Đây là tín hiệu an toàn thật: hệ thống kiểm soát hỏng thì
        không ai xác nhận được thao tác còn an toàn hay không.
        Có thể mở lại bằng: whitelist tool trong guard_policy.json, hoặc
        đặt env var GUARD_FAIL_OPEN=1 (vận hành tạm).

  2. HẠ TẦNG GUARD CHƯA CÓ (import system_controller thất bại)
     -> CHO PHÉP + CẢNH BÁO. Không thể chặn cái chưa tồn tại; nếu chặn thì
        hệ thống sẽ không khởi động được. Đây là trạng thái "chưa có rào chắn",
        khác hẳn "rào chắn đã hỏng".

Cấu hình: `.agents/_SHARED/SHARED_CONTEXT/guard_policy.json`
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Đảm bảo UTF-8 theo AGENTS.md §2
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

POLICY_PATH = Path(__file__).resolve().parent / "guard_policy.json"

__all__ = [
    "preflight", "guarded", "controller", "GuardBlocked",
    "load_policy", "get_guard_mode", "is_fail_open_env",
]

# Ngữ cảnh dùng chung
_DEFAULT_POLICY: Dict[str, Any] = {
    "fail_closed": True,
    "controller_error_policy": "block",
    "harness_missing_policy": "allow_with_warn",
    "tools_fail_open": [],
    "modes": {},
    "readonly_skills": [],
    "env_override": {"fail_open": "GUARD_FAIL_OPEN", "mode": "GUARD_MODE"},
}
_policy_cache: Optional[Dict[str, Any]] = None
_controller: Any = None
_controller_available = True
_controller_import_attempted = False


def load_policy() -> Dict[str, Any]:
    """
    Đọc guard_policy.json (cache 1 lần). File hỏng -> dùng policy mặc định fail-closed.
    """
    global _policy_cache
    if _policy_cache is not None:
        return _policy_cache
    policy = dict(_DEFAULT_POLICY)
    try:
        if POLICY_PATH.exists():
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                policy.update(loaded)
                # Đảm bảo các khoá chuẩn có kiểu đúng
                if not isinstance(policy.get("tools_fail_open"), list):
                    policy["tools_fail_open"] = []
                if not isinstance(policy.get("modes"), dict):
                    policy["modes"] = {}
                if not isinstance(policy.get("readonly_skills"), list):
                    policy["readonly_skills"] = []
    except (OSError, ValueError):
        pass  # Policy mặc định (fail-closed) an toàn hơn
    _policy_cache = policy
    return policy


def is_fail_open_env() -> bool:
    """Env var ghi đè để vận hành tạm (vd GUARD_FAIL_OPEN=1)."""
    policy = load_policy()
    env_name = (policy.get("env_override") or {}).get("fail_open", "GUARD_FAIL_OPEN")
    return str(os.environ.get(env_name, "")).strip().lower() in ("1", "true", "yes", "on")


def get_guard_mode(skill: Optional[str] = None) -> str:
    """
    Chế độ guard cho skill: SAFE (mặc định) | READ_ONLY | UNRESTRICTED.
    - Env var GUARD_MODE ghi đè tất cả.
    - Skill trong `readonly_skills` -> READ_ONLY.
    - Skill có trong `modes` -> theo map.
    """
    policy = load_policy()
    env_name = (policy.get("env_override") or {}).get("mode", "GUARD_MODE")
    env_mode = str(os.environ.get(env_name, "")).strip().upper()
    if env_mode in ("SAFE", "READ_ONLY", "UNRESTRICTED"):
        return env_mode

    if skill:
        if skill in (policy.get("readonly_skills") or []):
            return "READ_ONLY"
        mapped = (policy.get("modes") or {}).get(skill)
        if mapped and str(mapped).upper() in ("SAFE", "READ_ONLY", "UNRESTRICTED"):
            return str(mapped).upper()
    return "SAFE"


def _import_controller() -> Tuple[Any, bool]:
    """
    Import SystemController. Trả (controller, available).
    available=False nghĩa là hạ tầng guard chưa có (không phải controller hỏng).

    Chỉ thử import MỘT lần (cờ _controller_import_attempted) để tránh việc
    re-import thành công sau khi đã bị đánh dấu là "không khả dụng" —
    đặc biệt quan trọng cho test simulation.
    """
    global _controller, _controller_available, _controller_import_attempted
    if _controller_import_attempted:
        return _controller, _controller_available
    _controller_import_attempted = True
    try:
        from system_controller import system_controller as sc
        _controller = sc
        _controller_available = True
    except Exception:
        _controller = None
        _controller_available = False
    return _controller, _controller_available


class GuardBlocked(RuntimeError):
    """Ngoại lệ ném ra khi preflight chặn thao tác."""

    def __init__(self, reason: str, status: str = "BLOCKED"):
        super().__init__(reason)
        self.reason = reason
        self.status = status


def _apply_mode(skill: Optional[str]) -> None:
    """Áp chế độ guard cho skill lên controller (nếu có)."""
    ctrl, available = _import_controller()
    if not available or ctrl is None:
        return
    try:
        mode = get_guard_mode(skill)
        if getattr(ctrl, "guard", None) is not None:
            ctrl.guard.mode = mode
    except Exception:
        pass


def preflight(
    actor: str,
    tool: str,
    payload: Optional[Dict[str, Any]] = None,
    fail_open: Optional[bool] = None,
    skill: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Chạy kiểm tra an toàn trước khi thực thi tool.

    Args:
        actor: Tên tác tử gọi (ví dụ "Structural_Design_Engineer").
        tool: Tên tool đang gọi.
        payload: Payload thực thi (vd {"command": "..."}).
        fail_open: Ghi đè hành vi fail-open cho lần gọi này.
                   None = theo policy (mặc định fail-closed).
        skill: Tên skill gọi — dùng để chọn chế độ guard theo policy.

    Returns:
        (allowed, reason)

    Ghi chú: `preflight_check` ghi nhận 1 hop vào LoopBreaker (bộ điều khiển global)
    của SystemController. Khi vòng lặp bị phát hiện (LOOP_BLOCKED), trajectory được
    reset để không lặp lại cùng cảnh — các lần gọi hợp lệ trong cùng process
    (vd workflow harness chạy nhiều stage) vẫn được tích luỹ để phát hiện ping-pong.
    """
    policy = load_policy()
    skill_name = skill or actor

    # --- Tình huống 1: hạ tầng guard chưa có ---
    ctrl, available = _import_controller()
    if not available or ctrl is None:
        if policy.get("harness_missing_policy") == "block":
            return False, (
                "[HARNESS_MISSING] Hệ thống kiểm soát chưa khả dụng (không import được "
                "system_controller); chặn thực thi theo chính sách Fail-Closed."
            )
        return True, (
            "[HARNESS_MISSING] Hệ thống kiểm soát chưa khả dụng — bỏ qua preflight "
            "(chưa có rào chắn, KHÁC với rào chắn đã hỏng)."
        )

    _apply_mode(skill_name)

    try:
        res = ctrl.preflight_check(actor, tool, payload or {})
        allowed = bool(res.get("allowed"))
        reason = res.get("reason", "")
        if not allowed:
            reason = f"[{res.get('status', 'BLOCKED')}] {reason}"
            if res.get("status") == "LOOP_BLOCKED":
                try:
                    ctrl.loop_breaker.reset()
                except Exception:
                    pass
        return allowed, reason
    except Exception as e:
        # --- Tình huống 2: controller đã cài nhưng preflight_check lỗi ---
        # Đây là tín hiệu an toàn thật -> mặc định CHẶN.
        allow = fail_open
        if allow is None:
            allow = bool(policy.get("fail_closed")) is False
            if tool in (policy.get("tools_fail_open") or []):
                allow = True
            if is_fail_open_env():
                allow = True
        if allow:
            return True, (
                f"[FAIL_OPEN] Bộ kiểm soát lỗi ({e}) — cho phép tiếp tục theo chính sách."
            )
        return False, (
            f"[CONTROLLER_ERROR] Bộ kiểm soát hệ thống gặp lỗi ({e}); "
            f"chặn thực thi theo nguyên tắc Fail-Closed. "
            f"(Bật tạm: set {env_name_hint()} = 1, hoặc thêm tool vào tools_fail_open)"
        )


def env_name_hint() -> str:
    policy = load_policy()
    return (policy.get("env_override") or {}).get("fail_open", "GUARD_FAIL_OPEN")


def guarded(
    actor: str,
    tool: Optional[str] = None,
    fail_open: Optional[bool] = None,
    skill: Optional[str] = None,
):
    """
    Decorator bọc hàm thực thi tool với preflight check.

    Args:
        actor: Tên tác tử gọi (ví dụ "Structural_Design_Engineer").
        tool: Tên tool; mặc định lấy theo tên hàm được bọc.
        fail_open: Ghi đè hành vi fail-open (None = theo policy, mặc định fail-closed).
        skill: Tên skill gọi (dùng để chọn chế độ guard).
    """
    def decorator(func: Callable) -> Callable:
        tool_name = tool or func.__name__

        def wrapper(*args, **kwargs):
            allowed, reason = preflight(
                actor, tool_name, {}, fail_open=fail_open, skill=skill or actor
            )
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
    print("Policy:", json.dumps(load_policy(), ensure_ascii=False, indent=2))
    print("Mode (Global_Dispatcher):", get_guard_mode("Global_Dispatcher"))

    ok, why = preflight("Global_Dispatcher", "read_only_probe")
    print("ALLOW case:", ok, "|", why)

    ok, why = preflight("Global_Dispatcher", "revit_delete_elements")
    print("DELETE case:", ok, "|", why)

    ok, why = preflight("Global_Dispatcher", "run_shell", {"command": "rm -rf /"})
    print("DANGEROUS case:", ok, "|", why)
