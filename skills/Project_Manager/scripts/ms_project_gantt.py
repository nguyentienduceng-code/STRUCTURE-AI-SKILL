# -*- coding: utf-8 -*-
"""
Thin re-export wrapper — Single Source of Truth nằm tại `.agents/skills/Technical_Illustrator/scripts/ms_project_gantt.py`.
Giữ tương thích ngược cho `Project_Manager/scripts/msproject_bridge.py`.
"""
from __future__ import annotations

import importlib.util
import runpy
from pathlib import Path

_SSOT_PATH = Path(__file__).resolve().parents[2] / "Technical_Illustrator" / "scripts" / "ms_project_gantt.py"
_SPEC = importlib.util.spec_from_file_location("_ssot_ms_project_gantt", str(_SSOT_PATH))
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)

globals().update({k: v for k, v in vars(_MOD).items() if not k.startswith("__")})

if __name__ == "__main__":
    runpy.run_path(str(_SSOT_PATH), run_name="__main__")
