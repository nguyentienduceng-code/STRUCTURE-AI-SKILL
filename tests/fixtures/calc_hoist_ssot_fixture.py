# -*- coding: utf-8 -*-
"""
Self-contained fixture verifying SSOT citation import without local duplication.
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from citation_grounding_auditor import normalize_citation

__all__ = ["normalize_citation"]
