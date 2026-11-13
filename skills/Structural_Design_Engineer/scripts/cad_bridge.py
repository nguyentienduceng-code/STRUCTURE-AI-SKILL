# -*- coding: utf-8 -*-
"""
Thin re-export wrapper — Single Source of Truth nằm tại `.agents/tools/cad_bridge.py`.
Giữ tương thích ngược cho các script/test import từ Structural_Design_Engineer/scripts/.
"""
from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path

_SSOT_PATH = Path(__file__).resolve().parents[3] / "tools" / "cad_bridge.py"
_SPEC = importlib.util.spec_from_file_location("_ssot_cad_bridge", str(_SSOT_PATH))
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)

globals().update({k: v for k, v in vars(_MOD).items() if not k.startswith("__")})

if __name__ == "__main__":
    runpy.run_path(str(_SSOT_PATH), run_name="__main__")
