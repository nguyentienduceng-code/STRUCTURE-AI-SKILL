"""ProjectTargetResolver: Dynamic project discovery and deliverable path resolution.

Scans configured project roots (e.g. ``01_Projects`` and ``01_Structural_Projects``)
under the workspace root, performs Vietnamese accent-folded token matching, and
returns canonical POSIX and Windows paths to ``04_Deliverables_ToTrinh``.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_PROJECT_ROOTS: Tuple[str, ...] = ("01_Projects", "01_Structural_Projects")
DEFAULT_DELIVERABLE_SUBDIR = "04_Deliverables_ToTrinh"

_STOP_TOKENS = frozenset(
    {
        "du",
        "an",
        "cong",
        "trinh",
        "nha",
        "toa",
        "khu",
        "project",
        "projects",
        "structural",
        "bptc",
        "kc",
        "kt",
    }
)


def normalize_vn(text: str) -> str:
    """Fold Vietnamese diacritics, lowercase, and normalize separators to spaces."""
    if not text:
        return ""
    replaced = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", replaced)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    lowered = stripped.lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(text: str) -> List[str]:
    norm = normalize_vn(text)
    return [tok for tok in norm.split(" ") if tok]


def _format_paths(path: Path) -> Tuple[str, str]:
    """Return (posix_path, win_path) preserving drive letters if present."""
    raw = str(path)
    posix_path = raw.replace("\\", "/")
    win_path = raw.replace("/", "\\")
    return posix_path, win_path


@dataclass
class ProjectMatch:
    project_name: str
    project_root: str
    project_dir_posix: str
    project_dir_win: str
    deliverable_dir_posix: str
    deliverable_dir_win: str
    deliverable_dir_exists: bool
    score: float
    matched_tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class ResolutionResult:
    status: str  # "RESOLVED" | "AMBIGUOUS" | "NOT_FOUND"
    match: Optional[ProjectMatch] = None
    candidates: List[ProjectMatch] = field(default_factory=list)
    message_vi: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "match": self.match.to_dict() if self.match else None,
            "candidates": [c.to_dict() for c in self.candidates],
            "message_vi": self.message_vi,
        }


class ProjectTargetResolver:
    """Resolve natural-language project mentions to deliverable directories."""

    def __init__(
        self,
        workspace_root: Optional[str | Path] = None,
        project_roots: Sequence[str] = DEFAULT_PROJECT_ROOTS,
        deliverable_subdir: str = DEFAULT_DELIVERABLE_SUBDIR,
    ) -> None:
        self.workspace_root = Path(workspace_root or os.getcwd())
        self.project_roots = tuple(project_roots) if project_roots else DEFAULT_PROJECT_ROOTS
        self.deliverable_subdir = deliverable_subdir or DEFAULT_DELIVERABLE_SUBDIR

    def discover_projects(self) -> List[Tuple[str, Path]]:
        """Return list of (root_rel_name, project_dir_path) discovered on disk."""
        discovered: List[Tuple[str, Path]] = []
        seen: set[str] = set()
        for root_name in self.project_roots:
            root_path = self.workspace_root / root_name
            if not root_path.exists() or not root_path.is_dir():
                continue
            for entry in sorted(root_path.iterdir(), key=lambda p: p.name.lower()):
                if not entry.is_dir():
                    continue
                if entry.name.startswith(".") or entry.name.startswith("_"):
                    continue
                key = str(entry).lower()
                if key not in seen:
                    seen.add(key)
                    discovered.append((root_name, entry))
        return discovered

    def _score_project(self, prompt: str, prompt_norm: str, prompt_tokens: set[str], folder_name: str) -> Tuple[float, List[str]]:
        """Compute match score in [0.0, 1.0] between prompt and a project folder name."""
        folder_norm = normalize_vn(folder_name)
        if not folder_norm:
            return 0.0, []

        # 1. Exact folder name or normalized phrase containment
        if folder_name.lower() in prompt.lower() or (
            len(folder_norm) >= 4 and folder_norm in prompt_norm
        ):
            return 1.0, _tokenize(folder_name)

        folder_tokens = _tokenize(folder_name)
        if not folder_tokens:
            return 0.0, []

        # Separate leading numeric prefix (e.g. "17" in "17_LIEN_CHIEU_DA_NANG")
        numeric_prefix = folder_tokens[0] if folder_tokens[0].isdigit() else None
        name_tokens = folder_tokens[1:] if numeric_prefix and len(folder_tokens) > 1 else folder_tokens
        significant_tokens = [t for t in name_tokens if t not in _STOP_TOKENS and len(t) >= 2]
        if not significant_tokens:
            significant_tokens = name_tokens

        # Phrase without numeric prefix (e.g. "lien chieu da nang")
        core_phrase = " ".join(name_tokens)
        if len(core_phrase) >= 4 and core_phrase in prompt_norm:
            return 0.95, list(name_tokens)

        matched_sig = [t for t in significant_tokens if t in prompt_tokens]
        if not matched_sig:
            return 0.0, []

        coverage = len(matched_sig) / len(significant_tokens)
        # Reward consecutive bigram matches and numeric prefix match
        bigram_bonus = 0.0
        if len(significant_tokens) >= 2:
            for i in range(len(significant_tokens) - 1):
                pair = f"{significant_tokens[i]} {significant_tokens[i + 1]}"
                if pair in prompt_norm:
                    bigram_bonus = 0.15
                    break

        prefix_bonus = 0.1 if (numeric_prefix and numeric_prefix in prompt_tokens) else 0.0

        # Guard against single short/generic token false positives
        if len(matched_sig) == 1 and len(significant_tokens) >= 3 and len(matched_sig[0]) <= 3:
            coverage *= 0.5

        score = min(0.92, round(coverage * 0.8 + bigram_bonus + prefix_bonus, 4))
        matched_all = ([numeric_prefix] if prefix_bonus > 0 and numeric_prefix else []) + matched_sig
        return score, matched_all

    def resolve(
        self,
        prompt: str,
        min_score: float = 0.38,
        ambiguity_margin: float = 0.12,
        discovered_override: Optional[Iterable[Tuple[str, Path]]] = None,
    ) -> ResolutionResult:
        """Resolve project target from prompt text."""
        projects = list(discovered_override) if discovered_override is not None else self.discover_projects()
        prompt_norm = normalize_vn(prompt)
        prompt_tokens = set(_tokenize(prompt))

        scored: List[ProjectMatch] = []
        for root_name, proj_path in projects:
            score, matched_tokens = self._score_project(prompt, prompt_norm, prompt_tokens, proj_path.name)
            if score >= min_score:
                deliv_path = proj_path / self.deliverable_subdir
                proj_posix, proj_win = _format_paths(proj_path)
                deliv_posix, deliv_win = _format_paths(deliv_path)
                scored.append(
                    ProjectMatch(
                        project_name=proj_path.name,
                        project_root=root_name,
                        project_dir_posix=proj_posix,
                        project_dir_win=proj_win,
                        deliverable_dir_posix=deliv_posix,
                        deliverable_dir_win=deliv_win,
                        deliverable_dir_exists=deliv_path.exists() and deliv_path.is_dir(),
                        score=score,
                        matched_tokens=matched_tokens,
                    )
                )

        if not scored:
            available_names = [p.name for _, p in projects[:8]]
            hint = f" Các dự án hiện có: {', '.join(available_names)}." if available_names else ""
            return ResolutionResult(
                status="NOT_FOUND",
                match=None,
                candidates=[],
                message_vi=(
                    "Chưa xác định được thư mục dự án tương ứng trong workspace."
                    f"{hint} Vui lòng xác nhận tên dự án để khóa đúng thư mục {self.deliverable_subdir}/."
                ),
            )

        scored.sort(key=lambda m: (-m.score, -len(m.matched_tokens), m.project_name.lower()))
        top = scored[0]
        # A user-supplied qualified path or folder code is a direct selection.
        # Otherwise surface every qualifying match across both roots (Rule 0.2).
        normalized_path = prompt.casefold().replace("\\\\", "/")
        paths = [m for m in scored if f"{m.project_root}/{m.project_name}".casefold() in normalized_path]
        exact = [m for m in scored if m.project_name.casefold() in prompt.casefold()]
        close_candidates = paths or exact or scored
        top = close_candidates[0]

        if len(close_candidates) > 1:
            names = ", ".join(f"{c.project_root}/{c.project_name}" for c in close_candidates[:5])
            return ResolutionResult(
                status="AMBIGUOUS",
                match=None,
                candidates=close_candidates[:5],
                message_vi=(
                    f"Phát hiện {len(close_candidates)} dự án khớp gần nhau ({names}). "
                    "Vui lòng chọn đúng dự án đích trước khi xuất hồ sơ."
                ),
            )

        return ResolutionResult(
            status="RESOLVED",
            match=top,
            candidates=scored[:3],
            message_vi=f"Đã khóa thư mục xuất hồ sơ: {top.deliverable_dir_win}",
        )