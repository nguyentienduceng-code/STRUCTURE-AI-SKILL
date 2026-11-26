"""2D Cognitive Intent Classifier for Global_Dispatcher.

Classifies every incoming user prompt across two orthogonal dimensions:
1. ``domain_skill``: Technical engineering or system domain (14 skills).
2. ``engagement_mode``: ``PRODUCT_COLLAB`` | ``SYSTEM_UPGRADE`` | ``SOLO_EXECUTION``.

Implements deterministic priority rules to resolve hybrid prompts (e.g. fixing a
project's build script to export a Word/PDF deliverable), enforces safe low-confidence
fallback to ``SOLO_EXECUTION``, and integrates ``ProjectTargetResolver`` to lock the
project's ``04_Deliverables_ToTrinh/`` target directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from project_target_resolver import (
    DEFAULT_DELIVERABLE_SUBDIR,
    DEFAULT_PROJECT_ROOTS,
    ProjectTargetResolver,
    ResolutionResult,
    normalize_vn,
)


MODE_PRODUCT = "PRODUCT_COLLAB"
MODE_SYSTEM = "SYSTEM_UPGRADE"
MODE_SOLO = "SOLO_EXECUTION"


from agent_selection import AGENT_CHOICES, SINGLE_AGENT, selected_agents, without_agent_directives


def task_intent_text(prompt: str) -> str:
    # A cited path supplies context, while an edit directed at a path is system work.
    return re.sub(
        r"(?i)\b(?:tham khảo|tham khao|chiếu theo tài liệu|chiếu theo|reference|theo hướng dẫn tại|theo|dựa theo|dua theo|căn cứ|can cu|tệp nguồn|tệp tham khảo)"
        r"\s*[:=]?\s*(?:`[^`]+`|\"[^\"]+\"|[^\s,;]+)", " ", without_agent_directives(prompt),
    )


def execution_plan(mode, choice):
    single = SINGLE_AGENT.get(choice)
    paired = choice == "DUAL" or (choice == "AUTO" and mode != MODE_SOLO)
    maker = single or ("GEMINI" if paired else "CURRENT_AGENT")
    reviewer = "CLAUDE" if paired else maker
    if mode == MODE_SYSTEM and paired:
        maker, reviewer = "CURRENT_AGENT", "PARTNER_AGENT"
    if mode == MODE_PRODUCT:
        steps = [
            ("bind", maker, [], "Nguồn đã xác nhận đúng dự án và danh mục tệp cần giao"),
            ("prepare", maker, ["bind"], "Dữ liệu, kết quả của skill và bản nháp theo từng hạng mục"),
            ("verify", reviewer, ["prepare"], "Đối chiếu nguồn, tiêu chuẩn và phiên bản bản nháp"),
            ("approve", "USER", ["verify"], "Xác nhận kết quả theo Điều 3 trước khi xuất"),
            ("export", reviewer, ["approve"], "Tệp chính thức đúng thư mục dự án"),
            ("check", reviewer, ["export"], "Mở lại tệp, kiểm tra định danh và ghi mã băm của bản cuối"),
        ]
    else:
        steps = [("execute", maker, [], "Kết quả theo skill và yêu cầu của ca")]
        if paired or mode == MODE_SYSTEM:
            steps.append(("verify", reviewer, ["execute"], "Kết quả kiểm tra và bằng chứng cùng phiên bản"))
    return [dict(step=k, owner=o, requires=r, output=v) for k, o, r, v in steps]


@dataclass
class ClassificationResult:
    domain_skill: str
    domain_confidence: float
    engagement_mode: str
    mode_confidence: float
    allow_script_patch: bool
    needs_project_confirmation: bool
    project_resolution: Optional[Dict[str, Any]]
    deliverable_dir_posix: Optional[str]
    deliverable_dir_win: Optional[str]
    use_dual_agent_bus: bool
    claude_role: str
    enforce_deliverable_gate: bool
    enforce_jargon_linter: bool
    routing_reason: str
    matched_signals: Dict[str, Any] = field(default_factory=dict)

    agent_selection: str = "AUTO"
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class IntentClassifier2D:
    """Two-dimensional cognitive dispatcher (Domain Skill x Engagement Mode)."""

    def __init__(
        self,
        db_path: Optional[str | Path] = None,
        workspace_root: Optional[str | Path] = None,
        resolver: Optional[ProjectTargetResolver] = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path else Path(__file__).with_name("keyword_database.json")
        self.db = self._load_db(self.db_path)
        cfg = self.db.get("config", {})
        self.low_confidence_threshold: float = float(cfg.get("low_confidence_threshold", 0.35))
        self.project_match_min_score: float = float(cfg.get("project_match_min_score", 0.45))
        self.project_ambiguity_margin: float = float(cfg.get("project_ambiguity_margin", 0.12))
        self.explicit_overrides: Dict[str, str] = dict(cfg.get("explicit_overrides", {}))
        self.system_core_paths: List[str] = list(self.db.get("system_core_paths", []))

        self.resolver = resolver or ProjectTargetResolver(
            workspace_root=workspace_root,
            project_roots=cfg.get("project_roots", DEFAULT_PROJECT_ROOTS),
            deliverable_subdir=cfg.get("deliverable_subdir", DEFAULT_DELIVERABLE_SUBDIR),
        )

    @staticmethod
    def _load_db(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _score_keyword_map(prompt_norm: str, kw_map: Dict[str, float]) -> Tuple[float, List[str]]:
        score = 0.0
        matched: List[str] = []
        for phrase, weight in kw_map.items():
            phrase_norm = normalize_vn(phrase)
            if not phrase_norm:
                continue
            if len(phrase_norm) <= 4:
                hit = bool(re.search(rf"(?<![a-z0-9]){re.escape(phrase_norm)}(?![a-z0-9])", prompt_norm))
            else:
                hit = phrase_norm in prompt_norm
            if hit:
                score += float(weight)
                matched.append(phrase)
        return min(1.0, round(score, 4)), matched

    def _detect_explicit_override(self, prompt: str) -> Optional[Tuple[str, str]]:
        stripped = prompt.strip()
        lowered = stripped.lower()
        words = lowered.split()
        if len(words) > 1 and all(word in self.explicit_overrides for word in words[:2]):
            raise ValueError("Chỉ chọn một cờ chế độ ở đầu yêu cầu.")
        for flag, mode in self.explicit_overrides.items():
            flag_l = flag.lower()
            if lowered.split(maxsplit=1)[:1] == [flag_l]:
                return flag, mode
        return None

    def _detect_system_core_paths(self, prompt: str) -> List[str]:
        lowered = prompt.lower()
        hits: List[str] = []
        for token in self.system_core_paths:
            if token.lower() in lowered:
                hits.append(token)
        if ".agents/" not in hits and ".agents\\" not in hits:
            if re.search(r'(?i)(?:^|[\s"\'`(\[,/@\\])\.agents(?=$|[\s"\'`\)\],/\\])', prompt):
                hits.append(".agents")
        return hits

    def _detect_script_patch_signals(self, prompt_norm: str) -> List[str]:
        edit = re.search(r"\b(?:sua|va|chinh sua|cap nhat|patch|fix) (?:ma |file )?(?:script|trinh tao)\b", prompt_norm)
        if edit and not re.search(r"\b(?:khong|cam|dung) (?:duoc |tu y )?$", prompt_norm[:edit.start()]):
            return [edit.group()]
        return []

    def _classify_domain(self, prompt_norm: str) -> Tuple[str, float, List[str]]:
        domain_cfg: Dict[str, Any] = self.db.get("domain_skills", {})
        matches: Dict[str, Tuple[float, List[str]]] = {}

        for skill_id, meta in domain_cfg.items():
            kw_map = meta.get("keywords", {})
            score, hits = self._score_keyword_map(prompt_norm, kw_map)
            if hits:
                matches[skill_id] = (score, hits)

        if not matches:
            return "GENERAL", 0.0, []

        # Tie-breakers per Rule 0.4 and tie_breakers in keyword_database.json
        top_score = max(s for s, _ in matches.values())

        # TB-04: Geotechnical keywords take precedence only when score is competitive or > low_confidence_threshold
        if "SKILL_GEOTECH" in matches:
            score, hits = matches["SKILL_GEOTECH"]
            if score >= top_score or score > self.low_confidence_threshold:
                return "SKILL_GEOTECH", score, hits

        # TB-06: Temporary works keywords take precedence (unless primary SDE calculation)
        if "SKILL_TEMPWORKS" in matches and "Structural_Design_Engineer" not in matches:
            score, hits = matches["SKILL_TEMPWORKS"]
            if score >= top_score or score > self.low_confidence_threshold:
                return "SKILL_TEMPWORKS", score, hits

        # TB-01 & TB-02: SDE vs DE
        has_sde = "Structural_Design_Engineer" in matches
        has_de = "Design_Evaluation" in matches
        if has_sde and has_de:
            sde_score, sde_hits = matches["Structural_Design_Engineer"]
            de_score, de_hits = matches["Design_Evaluation"]
            if sde_score >= de_score:
                return "Structural_Design_Engineer", sde_score, sde_hits
            else:
                return "Design_Evaluation", de_score, de_hits

        sorted_matches = sorted(
            matches.items(),
            key=lambda item: (item[1][0], len(item[1][1])),
            reverse=True,
        )
        best_skill = sorted_matches[0][0]
        best_score, best_hits = sorted_matches[0][1]
        return best_skill, best_score, best_hits

    def _build_result(
        self,
        domain_skill: str,
        domain_confidence: float,
        engagement_mode: str,
        mode_confidence: float,
        allow_script_patch: bool,
        proj_res: Optional[ResolutionResult],
        routing_reason: str,
        matched_signals: Dict[str, Any],
    ) -> ClassificationResult:
        needs_confirm = False
        deliv_posix: Optional[str] = None
        deliv_win: Optional[str] = None

        if engagement_mode == MODE_PRODUCT:
            if proj_res and proj_res.status == "RESOLVED" and proj_res.match:
                deliv_posix = proj_res.match.deliverable_dir_posix
                deliv_win = proj_res.match.deliverable_dir_win
            else:
                needs_confirm = True

        # Ensure SYSTEM_UPGRADE never ends up with domain_confidence == 0.0 or captured by weak /sys domain hits
        if engagement_mode == MODE_SYSTEM and (
            domain_skill == "GENERAL"
            or domain_confidence <= self.low_confidence_threshold
            or matched_signals.get("explicit_override") == "/sys"
        ):
            domain_skill = "SKILL_SYSTEM_ENGINEERING"
            domain_confidence = max(domain_confidence, mode_confidence)

        choice = matched_signals["agent_selection"]
        if choice == "DUAL" and matched_signals.get("explicit_override") == "/solo":
            raise ValueError("Cờ /solo yêu cầu một tác tử. Hãy chọn lại chế độ hoặc tác tử.")
        use_bus = choice == "DUAL" or (choice == "AUTO" and engagement_mode != MODE_SOLO)
        if engagement_mode == MODE_PRODUCT:
            claude_role = "LEAD_AUDITOR_TCVN"
        elif engagement_mode == MODE_SYSTEM:
            claude_role = "SOFTWARE_ARCHITECT"
        else:
            claude_role = "REVIEWER" if use_bus else "NONE"

        return ClassificationResult(
            domain_skill=domain_skill,
            domain_confidence=round(domain_confidence, 4),
            engagement_mode=engagement_mode,
            mode_confidence=round(mode_confidence, 4),
            allow_script_patch=allow_script_patch,
            needs_project_confirmation=needs_confirm,
            project_resolution=proj_res.to_dict() if proj_res else None,
            deliverable_dir_posix=deliv_posix,
            deliverable_dir_win=deliv_win,
            use_dual_agent_bus=use_bus,
            claude_role={"GEMINI_ONLY": "NONE", "CODEX_ONLY": "NONE", "CLAUDE_ONLY": "EXECUTOR"}.get(choice, claude_role),
            agent_selection=choice,
            execution_plan=execution_plan(engagement_mode, choice),
            enforce_deliverable_gate=(engagement_mode == MODE_PRODUCT),
            enforce_jargon_linter=(engagement_mode == MODE_PRODUCT),
            routing_reason=routing_reason,
            matched_signals=matched_signals,
        )

    def classify(self, prompt: str, agent_selection: Optional[str] = None) -> ClassificationResult:
        """Classify a prompt into (domain_skill, engagement_mode, project_target)."""
        task_text = task_intent_text(prompt)
        prompt_norm = normalize_vn(task_text)
        domain_skill, domain_score, domain_hits = self._classify_domain(prompt_norm)

        modes_cfg = self.db.get("engagement_modes", {})
        prod_score, prod_hits = self._score_keyword_map(
            prompt_norm, modes_cfg.get(MODE_PRODUCT, {}).get("keywords", {})
        )
        sys_score, sys_hits = self._score_keyword_map(
            prompt_norm, modes_cfg.get(MODE_SYSTEM, {}).get("keywords", {})
        )
        solo_score, solo_hits = self._score_keyword_map(
            prompt_norm, modes_cfg.get(MODE_SOLO, {}).get("keywords", {})
        )

        core_path_hits = self._detect_system_core_paths(task_text)
        script_patch_hits = self._detect_script_patch_signals(prompt_norm)
        proj_res = self.resolver.resolve(
            task_text,
            min_score=self.project_match_min_score,
            ambiguity_margin=self.project_ambiguity_margin,
        )
        has_project_match = proj_res.status in ("RESOLVED", "AMBIGUOUS")

        matched_signals: Dict[str, Any] = {
            "agent_selection": selected_agents(
                prompt, agent_selection, Path(proj_res.match.project_dir_posix) if proj_res.match else None
            ),
            "domain_hits": domain_hits,
            "product_hits": prod_hits,
            "system_hits": sys_hits,
            "solo_hits": solo_hits,
            "system_core_paths": core_path_hits,
            "script_patch_signals": script_patch_hits,
        }

        # Priority 1: Explicit override flag (/prod, /sys, /solo)
        override = self._detect_explicit_override(prompt)
        if override:
            flag, mode = override
            matched_signals["explicit_override"] = flag
            return self._build_result(
                domain_skill=domain_skill,
                domain_confidence=domain_score,
                engagement_mode=mode,
                mode_confidence=1.0,
                allow_script_patch=(mode == MODE_PRODUCT and bool(script_patch_hits)),
                proj_res=proj_res if mode == MODE_PRODUCT else None,
                routing_reason=f"Explicit override flag '{flag}' detected.",
                matched_signals=matched_signals,
            )

        # Priority 2: Direct reference to .agents/ core infrastructure -> SYSTEM_UPGRADE
        if core_path_hits:
            return self._build_result(
                domain_skill=domain_skill,
                domain_confidence=domain_score,
                engagement_mode=MODE_SYSTEM,
                mode_confidence=max(0.9, sys_score),
                allow_script_patch=False,
                proj_res=None,
                routing_reason=(
                    f"Core system path/module referenced ({', '.join(core_path_hits[:3])}); "
                    "routed to SYSTEM_UPGRADE."
                ),
                matched_signals=matched_signals,
            )

        # Priority 3: Project-scoped deliverable or hybrid project script patch -> PRODUCT_COLLAB
        project_action = any(term in prompt_norm for term in ("hoan thien bo", "gui khach", "chinh lai phan trinh bay"))
        if has_project_match and (prod_score >= 0.25 or script_patch_hits or project_action):
            effective_score = min(1.0, max(prod_score, 0.75) + (0.1 if script_patch_hits else 0.0))
            reason = (
                "Hybrid project deliverable + local build script fix detected; "
                "routed to PRODUCT_COLLAB with allow_script_patch=True."
                if script_patch_hits
                else "Matched workspace project directory with deliverable intent; routed to PRODUCT_COLLAB."
            )
            return self._build_result(
                domain_skill=domain_skill,
                domain_confidence=domain_score,
                engagement_mode=MODE_PRODUCT,
                mode_confidence=effective_score,
                allow_script_patch=bool(script_patch_hits),
                proj_res=proj_res,
                routing_reason=reason,
                matched_signals=matched_signals,
            )

        # Priority 4: Score-based routing across the 3 modes
        candidates: List[Tuple[str, float]] = [
            (MODE_SYSTEM, sys_score),
            (MODE_PRODUCT, prod_score),
            (MODE_SOLO, solo_score),
        ]
        candidates.sort(key=lambda item: -item[1])
        top_mode, top_score = candidates[0]

        if top_score >= self.low_confidence_threshold:
            if top_mode == MODE_SYSTEM:
                return self._build_result(
                    domain_skill=domain_skill,
                    domain_confidence=domain_score,
                    engagement_mode=MODE_SYSTEM,
                    mode_confidence=top_score,
                    allow_script_patch=False,
                    proj_res=None,
                    routing_reason="Matched SYSTEM_UPGRADE intent keywords.",
                    matched_signals=matched_signals,
                )
            if top_mode == MODE_PRODUCT:
                return self._build_result(
                    domain_skill=domain_skill,
                    domain_confidence=domain_score,
                    engagement_mode=MODE_PRODUCT,
                    mode_confidence=top_score,
                    allow_script_patch=bool(script_patch_hits),
                    proj_res=proj_res,
                    routing_reason="Matched PRODUCT_COLLAB deliverable keywords.",
                    matched_signals=matched_signals,
                )
            return self._build_result(
                domain_skill=domain_skill,
                domain_confidence=domain_score,
                engagement_mode=MODE_SOLO,
                mode_confidence=top_score,
                allow_script_patch=False,
                proj_res=None,
                routing_reason="Matched SOLO_EXECUTION direct query keywords; Bus IPC disabled.",
                matched_signals=matched_signals,
            )

        # Priority 5: Low-confidence safe fallback -> SOLO_EXECUTION (never silently trigger Bus IPC)
        return self._build_result(
            domain_skill=domain_skill,
            domain_confidence=domain_score,
            engagement_mode=MODE_SOLO,
            mode_confidence=top_score,
            allow_script_patch=False,
            proj_res=None,
            routing_reason=(
                f"Mode confidence ({top_score:.2f}) below threshold "
                f"({self.low_confidence_threshold:.2f}); defaulted safely to SOLO_EXECUTION."
            ),
            matched_signals=matched_signals,
        )


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="2D Cognitive Intent Classifier (Domain Skill x Engagement Mode)"
    )
    parser.add_argument("prompt", help="User prompt text to classify")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Workspace root containing 01_Projects / 01_Structural_Projects",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Path to keyword_database.json (defaults to sibling file)",
    )
    parser.add_argument("--agent-selection", choices=AGENT_CHOICES)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_cli()
    args = parser.parse_args(argv)
    classifier = IntentClassifier2D(db_path=args.db, workspace_root=args.workspace)
    try:
        result = classifier.classify(args.prompt, args.agent_selection)
    except ValueError as exc:
        parser.error(str(exc))
    print(result.to_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
