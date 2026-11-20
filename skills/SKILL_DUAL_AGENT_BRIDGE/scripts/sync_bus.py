#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_bus.py — THIN WRAPPER (v3.2.0) — Single Source of Truth (SSOT) Design

⚠ Nền tảng kiến trúc v3.2 (PROPOSAL_DUAL_AGENT_V32_RESEARCH, Trọng tâm 1):
   File này KHÔNG còn chứa bất kỳ logic nghiệp vụ nào. Toàn bộ mã nguồn của
   bus Dual-Agent sống duy nhất tại SSOT:

       .agents/tools/sync_bus.py

   Wrapper này chỉ đảm nhận 2 vai trò:
   1. CLI (khi chạy `python scripts/sync_bus.py ...`): nạp SSOT rồi gọi
      `main()` của SSOT.
   2. Import (khi `import sync_bus` với scripts/ nằm trong sys.path): nạp SSOT
      và alias nó vào `sys.modules["sync_bus"]` để `import sync_bus` trả về
      đúng module SSOT (một namespace duy nhất) — nhờ đó cơ chế monkey-patch
      của test suite (patch BUS_PATH/LOCK_PATH/...) vẫn hoạt động 100%.

   Lệnh `claim_task.py` / `handover_task.py` gọi wrapper này theo CLI nên
   không bị ảnh hưởng. Mọi bảo trì logic (bugfix, feature) thực thi tại
   `.agents/tools/sync_bus.py`; wrapper tự động kế thừa (chỉ sửa 1 nơi).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _locate_ssot() -> Path:
    """
    Định vị file SSOT (.agents/tools/sync_bus.py) một cách xác thực:
    1. Theo cấu trúc thư mục chuẩn (scripts -> SKILL_DUAL_AGENT_BRIDGE -> skills
       -> .agents -> <root>).
    2. Override bằng env SYNC_BUS_SSOT (nếu đặt).
    3. Duyệt ngược thư mục cha để tìm `.agents/tools/sync_bus.py`.
    """
    here = Path(__file__).resolve().parent
    # here = <root>/.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts
    # parents: [0]=SKILL_DUAL_AGENT_BRIDGE [1]=skills [2]=.agents [3]=<root>
    root = here.parents[3]
    candidate = root / ".agents" / "tools" / "sync_bus.py"
    if candidate.exists():
        return candidate

    env_override = os.environ.get("SYNC_BUS_SSOT", "").strip()
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p

    for base in (here, *here.parents):
        cand = base / ".agents" / "tools" / "sync_bus.py"
        if cand.exists():
            return cand
    raise FileNotFoundError(
        "Không tìm thấy SSOT .agents/tools/sync_bus.py. "
        "Đặt env SYNC_BUS_SSOT=<path> để chỉ định vị trí file SSOT."
    )


def _load_ssot():
    """Nạp module SSOT và alias vào sys.modules['sync_bus'] (single namespace)."""
    ssot_path = str(_locate_ssot())
    spec = importlib.util.spec_from_file_location("sync_bus", ssot_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Không thể tạo spec import cho SSOT tại {ssot_path}")
    module = importlib.util.module_from_spec(spec)
    # Alias SSOT làm module 'sync_bus' chính thức. Khi caller `import sync_bus`
    # với scripts/ nằm trong sys.path, import machinery sẽ trả về đúng module
    # SSOT này (namespace duy nhất), giữ nguyên khả năng monkey-patch.
    sys.modules["sync_bus"] = module
    spec.loader.exec_module(module)
    return module


_SSOT_MODULE = _load_ssot()

# Re-export API công khai để `from sync_bus import X` hoạt động minh bạch.
FileLock = _SSOT_MODULE.FileLock
_atomic_write_json = _SSOT_MODULE._atomic_write_json
_atomic_write_text = _SSOT_MODULE._atomic_write_text
to_relative_path = _SSOT_MODULE.to_relative_path
normalize_path = _SSOT_MODULE.normalize_path
find_workspace_root = _SSOT_MODULE.find_workspace_root
get_bus_paths = _SSOT_MODULE.get_bus_paths
detect_modified_files = _SSOT_MODULE.detect_modified_files
validate_bus_payload = _SSOT_MODULE.validate_bus_payload
generate_handoff_memo = _SSOT_MODULE.generate_handoff_memo
auto_handoff = _SSOT_MODULE.auto_handoff
post_handoff = _SSOT_MODULE.post_handoff
claim_task = _SSOT_MODULE.claim_task
complete_task = _SSOT_MODULE.complete_task
request_review = _SSOT_MODULE.request_review
heartbeat = _SSOT_MODULE.heartbeat
read_bus = _SSOT_MODULE.read_bus
scan_gdrive_conflicts = _SSOT_MODULE.scan_gdrive_conflicts
resolve_gdrive_conflicts = _SSOT_MODULE.resolve_gdrive_conflicts
visual_gate_check = _SSOT_MODULE.visual_gate_check
write_receipt = _SSOT_MODULE.write_receipt
_evidence_hashes = _SSOT_MODULE._evidence_hashes
_receipts_dir = _SSOT_MODULE._receipts_dir

# v3.3 — Product-First constants (gated/exempt action types, receipt statuses)
GATED_ACTION_TYPES = _SSOT_MODULE.GATED_ACTION_TYPES
EXEMPT_ACTION_TYPES = _SSOT_MODULE.EXEMPT_ACTION_TYPES
RECEIPT_STATUSES = _SSOT_MODULE.RECEIPT_STATUSES

# v3.3 — Report Gate (chuẩn RESULT.md theo ca)
result_report_dir = _SSOT_MODULE.result_report_dir
result_report_filename = _SSOT_MODULE.result_report_filename
emit_result_report = _SSOT_MODULE.emit_result_report
report_gate_check = _SSOT_MODULE.report_gate_check
RESULT_SECTIONS = _SSOT_MODULE.RESULT_SECTIONS

# Giữ nguyên các hằng số module-level có thể được import trực tiếp.
WORKSPACE_ROOT = _SSOT_MODULE.WORKSPACE_ROOT
BUS_PATH = _SSOT_MODULE.BUS_PATH
MEMO_PATH = _SSOT_MODULE.MEMO_PATH
LOCK_PATH = _SSOT_MODULE.LOCK_PATH


def main() -> None:
    """Điểm vào CLI: đại diện 100% tới main() của SSOT."""
    _SSOT_MODULE.main()


if __name__ == "__main__":
    main()
