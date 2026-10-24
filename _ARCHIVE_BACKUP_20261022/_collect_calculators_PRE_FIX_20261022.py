# tools/_collect_calculators.py
# Bộ thu thập: Với mỗi skill, liệt kê các Python calculator scripts trong scripts/ và calculators/.
# Loại trừ __init__.py, test_*.py, files trong _deprecated/.

from __future__ import annotations

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dataclasses import dataclass, field
from pathlib import Path


# Mapping skill → các thư mục chứa calculator. Một skill có thể có nhiều.
KNOWN_CALC_DIRS: dict[str, list[str]] = {
    "Design_Evaluation": ["calculators", "scripts"],
    "Structural_Design_Engineer": ["scripts"],
    "SKILL_GEOTECH": ["calculators", "scripts"],
    "SKILL_TEMPWORKS": ["calculators", "scripts"],
    "SKILL_FORENSIC": ["scripts"],
    "SKILL_RFI": ["scripts"],
    "SKILL_VERIFY": ["scripts"],
    "Cost_Estimator": ["calculators", "scripts"],
    "Global_Dispatcher": ["scripts"],
    "Technical_Illustrator": ["scripts"],
    "Project_Manager": ["calculators", "scripts"],
    "SKILL_BIM_COORDINATION": ["calculators", "scripts"],
    "SKILL_PHULUC": ["calculators", "scripts"],
}

EXCLUDE_PATTERNS = ("__init__.py",)
EXCLUDE_PREFIXES = ("test_",)
EXCLUDE_DIRS = ("_deprecated", "_archive", "__pycache__", "tests")


@dataclass
class CalculatorInventory:
    """Tồn kho calculator scripts theo skill."""

    by_skill: dict[str, list[str]] = field(default_factory=dict)
    total_count: int = 0
    skill_count_with_calculators: int = 0


def _is_excluded(p: Path) -> bool:
    """File có bị loại trừ không (test, __init__, trong _deprecated, ...)."""
    if p.name in EXCLUDE_PATTERNS:
        return True
    if any(p.name.startswith(pref) for pref in EXCLUDE_PREFIXES):
        return True
    # Nếu bất kỳ thành phần path nào thuộc EXCLUDE_DIRS
    return any(part in EXCLUDE_DIRS for part in p.parts)


def collect_calculators(skills_root: Path) -> CalculatorInventory:
    """Walk mỗi skill, glob *.py trong các thư mục KNOWN_CALC_DIRS, loại trừ test/deprecated."""
    inv = CalculatorInventory()
    if not skills_root.exists():
        return inv
    for skill_name, subdirs in KNOWN_CALC_DIRS.items():
        skill_dir = skills_root / skill_name
        if not skill_dir.exists():
            continue
        found: list[str] = []
        for sub in subdirs:
            target = skill_dir / sub
            if not target.exists() or not target.is_dir():
                continue
            for py in sorted(target.glob("*.py")):
                if _is_excluded(py):
                    continue
                # Tính path tương đối so với skills_root
                rel = py.relative_to(skills_root).as_posix()
                found.append(rel)
        if found:
            inv.by_skill[skill_name] = found
    inv.total_count = sum(len(v) for v in inv.by_skill.values())
    inv.skill_count_with_calculators = len(inv.by_skill)
    return inv
