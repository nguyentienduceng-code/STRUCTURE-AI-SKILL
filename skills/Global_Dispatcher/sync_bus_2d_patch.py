"""SyncBus2DAdapter: Drop-in v3.4 bridge connecting IntentClassifier2D to sync_bus.py.

Import this adapter inside ``sync_bus.py`` and ``handover_task.py`` so that:
- ``SOLO_EXECUTION`` tasks bypass ``DUAL_AGENT_BUS.json`` completely (zero IPC latency).
- ``PRODUCT_COLLAB`` tasks lock ``04_Deliverables_ToTrinh/``, generate a Vietnamese
  Lead Auditor handover prompt, keep v3.3 atomic locks & SHA-256 hashes silently in
  ``bus_meta``, and enforce ``ProductDeliverableGate`` + ``JargonLinter`` on completion.
- ``SYSTEM_UPGRADE`` tasks retain full v3.3 DevOps/Architect workflow.
"""

from __future__ import annotations

import json
import hashlib
import uuid
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from scripts.intent_classifier import IntentClassifier as SkillClassifier
from project_target_resolver import normalize_vn
from agent_selection import SINGLE_AGENT
from intent_classifier import IntentClassifier2D, MODE_PRODUCT, MODE_SOLO, MODE_SYSTEM, task_intent_text
from product_deliverable_gate import (
    DEFAULT_ALLOWED_EXTENSIONS,
    ProductDeliverableGate,
    build_claude_handover_prompt,
)


def _task_guides(skill, task, catalog):
    """Select supplemental documents from the installed skill's own entry points."""
    data = catalog.get(skill, {})
    triggers = data.get("guide_triggers", {})
    if not triggers:
        return []
    phrases = []
    for clause in re.split(r"[,;.!?\n]", task):
        for part in re.split(r"\b(?:nhung|thay vao do|but|instead)\b", normalize_vn(clause)):
            positive = re.split(r"\b(?:khong(?! gian\b)|bo qua|do not|skip)\b", part, maxsplit=1)[0]
            phrases.append(f" {positive} ")
    folder = Path(__file__).resolve().parent.parent / skill
    guides = []
    for name in data.get("entry_points", []):
        if any(f" {normalize_vn(term)} " in phrase for term in triggers.get(name, []) for phrase in phrases):
            path = folder / name
            if path.suffix == ".md" and path.is_file():
                guides.append(str(path))
    return guides


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(target: Path, data: Dict[str, Any]) -> None:
    """Write JSON atomically via temp file + os.replace to prevent Drive lock corruption."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".bus_tmp_", suffix=".json", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp_path), str(target))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _approved_response(response):
    if not isinstance(response, str):
        return False
    from scripts.approval_state import is_affirmative_response
    accepted = response.strip().casefold() in {"approved", "xuất file", "xuất hồ sơ"}
    return accepted or is_affirmative_response(response)


def approve_drafts(ticket, response, drafts):
    """The host supplies the user's answer after displaying these draft results."""
    if not _approved_response(response):
        raise ValueError("Cần xác nhận rõ ràng của người dùng theo Điều 3.")
    if not drafts or ticket.get("status") not in {"QUEUED", "IN_PROGRESS", "NEED_REVIEW"}:
        raise ValueError("Cần phiếu đã sẵn sàng và bản nháp đã trình người dùng.")
    return {
        "request_id": ticket["request_id"], "approved_at": time.time(),
        "response": response,
        "draft_hashes": {str(Path(f).resolve(strict=True)): hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in drafts},
    }


def current_approval(ticket, approval, artifacts):
    if not approval or approval.get("request_id") != ticket.get("request_id"):
        return False
    if not _approved_response(approval.get("response")):
        return False
    when = approval.get("approved_at")
    if not isinstance(when, (int, float)) or not ticket["bus_meta"]["task_started_at_epoch"] <= when <= time.time():
        return False
    # Permit filesystem timestamp rounding only at the export boundary.
    if any(a.mtime_epoch < when - 0.02 for a in artifacts):
        return False
    hashes = approval.get("draft_hashes")
    if not hashes or not isinstance(hashes, dict):
        return False
    try:
        return all(hashlib.sha256(Path(f).read_bytes()).hexdigest() == digest for f, digest in hashes.items())
    except OSError:
        return False


class SyncBus2DAdapter:
    """Adapter integrating 2D Dispatcher & ProductDeliverableGate with DUAL_AGENT_BUS.json."""

    def __init__(
        self,
        workspace_root: Optional[str | Path] = None,
        bus_path: Optional[str | Path] = None,
        classifier: Optional[IntentClassifier2D] = None,
        deliverable_gate: Optional[ProductDeliverableGate] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root or os.getcwd())
        if bus_path:
            self.bus_path = Path(bus_path)
        elif (self.workspace_root / ".agents" / "memory").is_dir():
            self.bus_path = self.workspace_root / ".agents" / "memory" / "DUAL_AGENT_BUS.json"
        else:
            self.bus_path = self.workspace_root / "memory" / "DUAL_AGENT_BUS.json"
        self.classifier = classifier or IntentClassifier2D(workspace_root=self.workspace_root)
        self.deliverable_gate = deliverable_gate or ProductDeliverableGate()

    def prepare_handover_payload(
        self,
        prompt: str,
        task_id: str,
        task_title: str,
        source_scripts: Optional[Sequence[str]] = None,
        notes: str = "",
        lock_owner: Optional[str] = None,
        expected_extensions: Sequence[str] = DEFAULT_ALLOWED_EXTENSIONS,
        write_to_bus: bool = False,
        agent_selection: Optional[str] = None,
        expected_files: Sequence[str] = (),
        project_identity: Optional[str] = None,
        independent_review_required: bool = False,
        include_solo: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Classify prompt and construct v3.4 Dual-Plane bus payload.

        Returns ``None`` when ``engagement_mode == SOLO_EXECUTION`` (Bus IPC disabled).
        """
        clf = self.classifier.classify(prompt, agent_selection).to_dict()
        choice = clf["agent_selection"]
        single = SINGLE_AGENT.get(choice)
        lock_owner = single or lock_owner or "gemini_maker"
        write_to_bus = write_to_bus and clf["use_dual_agent_bus"]
        mode = clf["engagement_mode"]
        intent = normalize_vn(task_intent_text(prompt))
        if mode == MODE_PRODUCT and any(phrase in intent for phrase in ("tham tra doc lap", "kiem tra doc lap")):
            independent_review_required = True
        if independent_review_required and mode != MODE_PRODUCT:
            raise ValueError("Xác nhận mã băm độc lập qua phiếu này áp dụng cho hồ sơ dự án.")

        if mode == MODE_SOLO and choice == "AUTO" and not include_solo:
            return None

        resolution = clf.get("project_resolution") or {}
        match = resolution.get("match") or {}
        if any(Path(name).name != name or Path(name).suffix.lower() not in DEFAULT_ALLOWED_EXTENSIONS for name in expected_files):
            raise ValueError("Danh mục bàn giao cần tên tệp có định dạng được hỗ trợ.")
        if mode == MODE_PRODUCT:
            project_identity = (project_identity or "").strip() or match.get("project_name")
        now_epoch = time.time()
        now_iso = _utc_now_iso()
        classifier = SkillClassifier()
        task = task_intent_text(prompt)
        skills = classifier.classify(task)
        workflow = skills.get("workflow") or {}
        owners = {step["step"]: step["owner"] for step in clf["execution_plan"]}
        maker = owners.get("prepare", owners.get("execute"))
        for stage in workflow.get("stages", []):
            checks_design = stage["skill"] in {"SKILL_VERIFY", "Design_Evaluation"}
            stage["owner"] = owners.get("verify", maker) if checks_design else maker
        primary = skills["primary_skill"]
        if mode == MODE_SYSTEM and (not primary or clf["domain_skill"] in ("SKILL_SYSTEM_ENGINEERING", "SKILL_DUAL_AGENT_BRIDGE")):
            primary = ("SKILL_DUAL_AGENT_BRIDGE" if re.search(r"\b(?:sync bus|dual agent|ban giao ca)\b", intent)
                       else "Global_Dispatcher")
            workflow = {}
            skills["workflow"] = None
            skills["pipeline"] = None
        skill_names = workflow.get("skills") or ([primary] if primary else [])
        skill_files = [str(Path(__file__).resolve().parent.parent / name / "SKILL.md") for name in dict.fromkeys(skill_names)]
        stages = workflow.get("stages", [])
        for stage in stages:
            stage["guide_files"] = _task_guides(stage["skill"], stage.get("task") or task, classifier.skills)
        guides = [] if stages or not primary else _task_guides(primary, task, classifier.skills)
        dispatch = {
            key: clf[key] for key in (
                "domain_skill", "domain_confidence", "engagement_mode", "mode_confidence",
                "claude_role", "agent_selection", "use_dual_agent_bus", "execution_plan",
                "allow_script_patch", "deliverable_dir_posix", "deliverable_dir_win",
                "enforce_deliverable_gate", "enforce_jargon_linter",
            )
        }
        formats = {"word": ".docx", "docx": ".docx", "pdf": ".pdf", "excel": ".xlsx", "xlsx": ".xlsx", "dxf": ".dxf"}
        fmt = "(?:" + "|".join(formats) + ")"
        export = re.findall(
            rf"\b(?:xuat|lap|tao) (?:lai )?(?:bo )?(?:ho so |file |tep |ra )?({fmt}(?: (?:va |kem )?{fmt})*)\b", intent
        )
        required_formats = sorted({formats[w] for group in export for w in group.split() if w in formats})
        dispatch.update(
            required_extensions=required_formats,
            primary_skill=primary, skill_workflow=skills.get("workflow"), skill_files=skill_files, guide_files=guides,
            expected_files=list(expected_files), project_identity=project_identity,
            independent_review_required=independent_review_required,
            expected_extensions=list(expected_extensions) if mode == MODE_PRODUCT else [],
        )

        if mode == MODE_PRODUCT and clf.get("needs_project_confirmation"):
            proj_msg = (clf.get("project_resolution") or {}).get(
                "message_vi",
                "Vui lòng xác nhận đúng thư mục dự án trước khi tạo phiếu bàn giao.",
            )
            payload: Dict[str, Any] = {
                "bus_version": "3.4",
                "task_id": task_id,
                "task_title": task_title,
                "status": "NEEDS_PROJECT_CONFIRMATION",
                "dispatch_2d": dispatch,
                "bus_meta": {
                    "lock_owner": lock_owner,
                    "lock_acquired_at_iso": now_iso,
                    "task_started_at_epoch": now_epoch,
                    "lease_ttl_sec": 600,
                    "report_gate_p1": "PENDING",
                    "mcp_perception_p2": True,
                    "evidence_hashes": {},
                    "receipts": [
                        {
                            "agent": lock_owner,
                            "event": "NEEDS_PROJECT_CONFIRMATION",
                            "timestamp_iso": now_iso,
                            "gate_status": "PENDING",
                        }
                    ],
                },
                "human_handoff": {
                    "handover_prompt": "",
                    "source_scripts": list(source_scripts or []),
                    "user_report_vi": proj_msg,
                    "deliverable_gate_status": "PENDING",
                    "deliverable_gate_message_vi": proj_msg,
                    "verified_files": [],
                },
            }
            if write_to_bus:
                _atomic_write_json(self.bus_path, payload)
            return payload

        missing_skills = [path for path in skill_files if not Path(path).is_file()]
        if missing_skills or (mode == MODE_PRODUCT and not skill_names and not workflow.get("error")):
            message = ("Chưa tìm thấy hướng dẫn skill: " + ", ".join(missing_skills) if missing_skills
                       else "Cần xác định hạng mục kỹ thuật để chọn skill cho hồ sơ.")
            return {
                "task_id": task_id, "status": "NEEDS_TASK_CONFIRMATION", "dispatch_2d": dispatch,
                "human_handoff": {"user_report_vi": message},
            }
        if (skills.get("pipeline") or {}).get("requires_clarification"):
            return {
                "task_id": task_id, "status": "NEEDS_TASK_CONFIRMATION", "dispatch_2d": dispatch,
                "human_handoff": {"user_report_vi": skills["pipeline"]["error"]},
            }

        handover_prompt = build_claude_handover_prompt(
            classification=clf,
            task_title=task_title,
            source_scripts=source_scripts,
            notes=notes,
        )

        guide_steps = [(stage["skill"], stage["guide_files"]) for stage in stages] or [(primary, guides)]
        for name, files in guide_steps:
            if files:
                handover_prompt += f"\nKhi thực hiện bước {name}, đọc thêm: " + ", ".join(files)

        payload = {
            "bus_version": "3.4",
            "task_id": task_id,
            "task_title": task_title,
            "status": "QUEUED",
            "request_id": uuid.uuid4().hex,
            "workspace": str(self.workspace_root.resolve()),
            "dispatch_2d": dispatch,
            "bus_meta": {
                "lock_owner": lock_owner,
                "lock_acquired_at_iso": now_iso,
                "task_started_at_epoch": now_epoch,
                "lease_ttl_sec": 600,
                "report_gate_p1": "PENDING",
                "mcp_perception_p2": True,
                "evidence_hashes": {},
                "receipts": [
                    {
                        "agent": lock_owner,
                        "event": "HANDOVER_CREATED",
                        "timestamp_iso": now_iso,
                        "gate_status": "PENDING",
                    }
                ],
            },
            "human_handoff": {
                "handover_prompt": handover_prompt,
                "source_scripts": list(source_scripts or []),
                "user_report_vi": "",
                "deliverable_gate_status": "PENDING",
                "deliverable_gate_message_vi": "",
                "verified_files": [],
            },
        }

        if write_to_bus:
            _atomic_write_json(self.bus_path, payload)
        return payload

    def complete_handover_with_gate(
        self,
        bus_payload: Dict[str, Any],
        user_report_vi: str,
        agent_name: Optional[str] = None,
        write_to_bus: bool = False,
        reviewed_by: Optional[str] = None,
        reviewed_hashes: Optional[Dict[str, str]] = None,
        approval: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Validate completion against ProductDeliverableGate (if PRODUCT_COLLAB) and update Bus."""
        if bus_payload.get("status") in {"NEEDS_TASK_CONFIRMATION", "NEEDS_PROJECT_CONFIRMATION"}:
            return bus_payload
        dispatch = bus_payload.get("dispatch_2d", {})
        single = SINGLE_AGENT.get(dispatch.get("agent_selection"))
        agent_name = agent_name or single or "claude_auditor"
        if single and agent_name.upper() != single:
            raise ValueError(f"Ca này chỉ giao cho {single}.")
        write_to_bus = write_to_bus and dispatch.get("use_dual_agent_bus", True)
        mode = dispatch.get("engagement_mode", MODE_SYSTEM)
        if mode == MODE_PRODUCT and not dispatch.get("deliverable_dir_posix") and not dispatch.get("deliverable_dir_win"):
            bus_payload["status"] = "NEEDS_PROJECT_CONFIRMATION"
            return bus_payload
        bus_meta = bus_payload.setdefault("bus_meta", {})
        handoff = bus_payload.setdefault("human_handoff", {})
        now_iso = _utc_now_iso()

        if mode == MODE_PRODUCT:
            deliv_dir = dispatch.get("deliverable_dir_posix") or dispatch.get("deliverable_dir_win")
            started_at = float(bus_meta.get("task_started_at_epoch", 0.0))
            expected_exts = dispatch.get("expected_extensions") or DEFAULT_ALLOWED_EXTENSIONS

            gate_res = self.deliverable_gate.verify(
                deliverable_dir=deliv_dir or "",
                task_started_at=started_at,
                user_report_vi=user_report_vi,
                workspace_root=self.workspace_root,
                expected_extensions=expected_exts,
                expected_files=dispatch.get("expected_files", []),
                required_extensions=dispatch.get("required_extensions", []),
                project_identity=dispatch.get("project_identity"),
            )

            handoff["deliverable_gate_status"] = gate_res.status
            handoff["deliverable_gate_message_vi"] = gate_res.message_vi
            handoff["verified_files"] = [a.filename for a in gate_res.verified_artifacts]
            bus_meta["evidence_hashes"] = dict(gate_res.evidence_hashes)
            handoff["verification_level"] = "PENDING"
            handoff.pop("reviewed_by", None)

            if not gate_res.passed:
                bus_payload["status"] = "BLOCKED_GATE"
                bus_meta.setdefault("receipts", []).append(
                    {
                        "agent": agent_name,
                        "event": "HANDOVER_BLOCKED",
                        "timestamp_iso": now_iso,
                        "gate_status": gate_res.status,
                    }
                )
                if write_to_bus:
                    _atomic_write_json(self.bus_path, bus_payload)
                return bus_payload

            if bus_payload.get("request_id") and not current_approval(bus_payload, approval, gate_res.verified_artifacts):
                bus_payload["status"] = "AWAITING_USER_APPROVAL"
                handoff["deliverable_gate_message_vi"] = "Cần bản nháp đúng phiên bản và xác nhận trước khi xuất."
                if write_to_bus:
                    _atomic_write_json(self.bus_path, bus_payload)
                return bus_payload

            # The reviewer attests to the final file digests. Any re-export
            # requires another attestation, including edits by the lead reviewer.
            producer = agent_name.upper().split("_")[0]
            independent = bool(
                reviewed_by and reviewed_by.strip()
                and reviewed_by.strip().upper().split("_")[0] != producer
                and (not single or reviewed_by.strip().upper().split("_")[0] not in ("CLAUDE", "GEMINI"))
                and reviewed_hashes == gate_res.evidence_hashes
            )
            claims_independent = any(term in normalize_vn(user_report_vi) for term in (
                "da tham tra doc lap", "da kiem tra doc lap",
            ))
            if (dispatch.get("independent_review_required") or reviewed_by or reviewed_hashes or claims_independent) and not independent:
                bus_payload["status"] = "AWAITING_INDEPENDENT_REVIEW"
                handoff["deliverable_gate_message_vi"] = "Chờ xác nhận độc lập theo mã băm của tệp cuối."
                if write_to_bus:
                    _atomic_write_json(self.bus_path, bus_payload)
                return bus_payload
            handoff["verification_level"] = "INDEPENDENT" if independent else "SELF_CHECKED"
            handoff["reviewed_by"] = reviewed_by if independent else agent_name
            handoff["user_report_vi"] = user_report_vi
            bus_payload["status"] = "COMPLETED"
            bus_meta["report_gate_p1"] = "PASS"
            bus_meta.setdefault("receipts", []).append(
                {
                    "agent": agent_name,
                    "event": "HANDOVER_COMPLETED",
                    "timestamp_iso": now_iso,
                    "gate_status": "PASS",
                }
            )
            if write_to_bus:
                _atomic_write_json(self.bus_path, bus_payload)
            return bus_payload

        # SYSTEM_UPGRADE path: bypass ProductDeliverableGate, keep standard v3.3 completion
        handoff["user_report_vi"] = user_report_vi
        handoff["verification_level"] = "SELF_CHECKED"
        handoff["deliverable_gate_status"] = "BYPASSED_SYSTEM_MODE" if mode == MODE_SYSTEM else "NOT_APPLICABLE"
        handoff["deliverable_gate_message_vi"] = "Kiểm tra theo quy trình chuyên môn của ca."
        bus_payload["status"] = "COMPLETED"
        bus_meta["report_gate_p1"] = "CHECK_IN_SYSTEM_WORKFLOW" if mode == MODE_SYSTEM else "NOT_APPLICABLE"
        bus_meta.setdefault("receipts", []).append(
            {
                "agent": agent_name,
                "event": "HANDOVER_COMPLETED",
                "timestamp_iso": now_iso,
                "gate_status": handoff["deliverable_gate_status"],
            }
        )
        if write_to_bus:
            _atomic_write_json(self.bus_path, bus_payload)
        return bus_payload