# .agents/tools/policy_engine.py
# Policy Engine (MD -> Code) — Quản lý và thực thi quy tắc kỹ thuật kết cấu tự động
# Phase A: Code hóa ngưỡng Value Engineering (η <= 0.70) và Repair (η > 1.00)
# Phase B: Code hóa 15 Inter-Skill Triggers (POST, CONDITIONAL, ERROR, CONFIDENCE)
# Phase C: Code hóa 18 Red Flag Triggers (SKILL_FORENSIC) + Phân loại ưu tiên RFI (SKILL_RFI)
# Nguồn quy tắc: AGENTS.md §6, §17; INTER_SKILL_TRIGGERS.md; RED_FLAG_TRIGGERS.md; SKILL_RFI.md

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Đảm bảo UTF-8 theo Quy tắc AGENTS.md §2
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =============================================================================
# SECTION 1: PHASE A — UTILIZATION RATIO & SAFETY (AGENTS.md §6)
# =============================================================================

class Action(str, Enum):
    """
    Hành động quyết định từ Policy Engine cho tỷ số sử dụng η.
    - PASS: Đạt yêu cầu chịu lực / sử dụng bình thường.
    - REPAIR: Không đạt (η > 1.00), yêu cầu điều chỉnh tiết diện / sửa chữa kết cấu.
    - TRIGGER_VE: An toàn dư lớn (η <= 0.70), kích hoạt Value Engineering (Cost_Estimator).
    """
    PASS = "PASS"
    REPAIR = "REPAIR"
    TRIGGER_VE = "TRIGGER_VE"


class StatusCode(str, Enum):
    """
    Mã trạng thái theo AGENTS.md §17.
    - PASS_OPTIMAL: 0.70 < η <= 0.90 (Thiết kế tối ưu, hợp lý).
    - PASS_WARNING: 0.90 < η <= 1.00 (W001: Sát ngưỡng giới hạn).
    - VE_RECOMMENDED: η <= 0.70 (W002 / I001: Khuyến nghị Value Engineering).
    - REPAIR_REQUIRED: η > 1.00 (KHÔNG ĐẠT: Yêu cầu điều chỉnh).
    """
    PASS_OPTIMAL = "PASS"
    PASS_WARNING = "W001"
    VE_RECOMMENDED = "W002"
    REPAIR_REQUIRED = "REPAIR"


@dataclass(frozen=True)
class PolicyDecision:
    """
    Kết quả đánh giá từ Policy Engine cho chỉ số sử dụng η (Utilization Ratio).

    Các field `standard_basis` và `standard_conflicts` chỉ được điền khi gọi
    `decide_eta_with_standards(...)` — các trường hợp còn lại giữ giá trị mặc định None.
    """
    action: Action
    status_code: StatusCode
    color: str
    max_eta: float
    min_eta: float
    message: str
    reasons: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    rule_sources: list[str] = field(default_factory=list)
    standard_basis: Optional[Dict[str, Any]] = None
    standard_conflicts: Optional[List[str]] = None

    @property
    def is_safe(self) -> bool:
        """Kiểm tra kết cấu có đạt an toàn chịu lực hay không (η <= 1.00)."""
        return self.action in (Action.PASS, Action.TRIGGER_VE)


def _extract_eta_values(
    eta_input: Union[float, int, Dict[str, Any], List[Union[float, int]]]
) -> List[Tuple[str, float]]:
    """
    Trích xuất danh sách (tên_phần_tử/thông_số, giá_trị_eta) từ nhiều định dạng đầu vào khác nhau.
    """
    extracted: List[Tuple[str, float]] = []

    def _traverse(prefix: str, val: Any):
        if isinstance(val, (int, float)):
            num = float(val)
            if num < 0:
                raise ValueError(f"Chỉ số sử dụng η không thể âm: {prefix} = {num}")
            extracted.append((prefix or "eta", num))
        elif isinstance(val, dict):
            if not val and not extracted:
                raise ValueError(f"Dữ liệu η rỗng tại '{prefix or 'root'}'")
            for k, v in val.items():
                p = f"{prefix}.{k}" if prefix else str(k)
                _traverse(p, v)
        elif isinstance(val, (list, tuple)):
            if not val and not extracted:
                raise ValueError(f"Danh sách η rỗng tại '{prefix or 'root'}'")
            for idx, item in enumerate(val):
                p = f"{prefix}[{idx}]" if prefix else f"item_{idx}"
                _traverse(p, item)
        else:
            raise TypeError(f"Giá trị không hợp lệ cho η tại '{prefix}': {type(val).__name__} ({val})")

    _traverse("", eta_input)
    if not extracted:
        raise ValueError("Không tìm thấy giá trị số η nào trong dữ liệu đầu vào.")
    return extracted


def decide_eta(
    eta_input: Union[float, int, Dict[str, Any], List[Union[float, int]]]
) -> PolicyDecision:
    """
    Quyết định hành động kỹ thuật dựa trên chỉ số sử dụng η (Utilization Ratio).
    """
    items = _extract_eta_values(eta_input)
    values = [val for _, val in items]
    max_eta = max(values)
    min_eta = min(values)

    reasons: list[str] = []
    triggers: list[str] = []
    rule_sources: list[str] = ["AGENTS.md §6 (Bảng chỉ số sử dụng η)"]

    # 1. Kiểm tra điều kiện REPAIR (Ưu tiên số 1 — An toàn kết cấu, η > 1.00)
    failing_items = [(name, val) for name, val in items if val > 1.00]
    if failing_items:
        detail_str = ", ".join([f"{name}={val:.3f}" for name, val in failing_items[:3]])
        if len(failing_items) > 3:
            detail_str += f" (+{len(failing_items) - 3} phần tử khác)"

        reasons.append(f"Có {len(failing_items)} vị trí vượt ngưỡng chịu lực (η > 1.00): {detail_str}")
        rule_sources.append("AGENTS.md §6 (η > 1.00 -> KHÔNG ĐẠT)")

        return PolicyDecision(
            action=Action.REPAIR,
            status_code=StatusCode.REPAIR_REQUIRED,
            color="🔴",
            max_eta=max_eta,
            min_eta=min_eta,
            message=f"KHÔNG ĐẠT — η_max = {max_eta:.3f} > 1.00. Yêu cầu tăng tiết diện hoặc giải pháp gia cường.",
            reasons=reasons,
            triggers=[],
            rule_sources=rule_sources,
        )

    # 2. Kiểm tra cảnh báo sát ngưỡng (Ưu tiên số 2 — 0.90 < max_eta <= 1.00)
    # LƯU Ý: Phải xét TRƯỚC TRIGGER_VE để cấu kiện đa nội lực (vd η_M=0.96, η_V=0.50)
    #        trả về PASS_WARNING thay vì bị TRIGGER_VE nuốt (Argon audit 3A, 2026-10-18).
    if max_eta > 0.90:
        high_items = [(name, val) for name, val in items if val > 0.90]
        detail_str = ", ".join([f"{name}={val:.3f}" for name, val in high_items[:3]])
        if len(high_items) > 3:
            detail_str += f" (+{len(high_items) - 3} phần tử khác)"

        reasons.append(
            f"Có {len(high_items)} vị trí sát ngưỡng giới hạn (0.90 < η <= 1.00): {detail_str}"
        )
        rule_sources.append("AGENTS.md §17 (W001: Approaching threshold > 90%)")

        return PolicyDecision(
            action=Action.PASS,
            status_code=StatusCode.PASS_WARNING,
            color="🟠",
            max_eta=max_eta,
            min_eta=min_eta,
            message=f"ĐẠT — η_max = {max_eta:.3f} (0.90 < η <= 1.00). Đạt nhưng sát ngưỡng, cảnh báo lưu ý.",
            reasons=reasons,
            triggers=[],
            rule_sources=rule_sources,
        )

    # 3. Kiểm tra điều kiện TRIGGER_VE (Ưu tiên số 3 — Khi không có phần tử nào > 0.90
    #    và tồn tại phần tử <= 0.70 thì kích hoạt Value Engineering).
    ve_items = [(name, val) for name, val in items if val <= 0.70]
    if ve_items:
        detail_str = ", ".join([f"{name}={val:.3f}" for name, val in ve_items[:3]])
        if len(ve_items) > 3:
            detail_str += f" (+{len(ve_items) - 3} phần tử khác)"

        reasons.append(
            f"Phát hiện {len(ve_items)} vị trí có η <= 0.70 (dự trữ chịu lực > 30%): {detail_str}"
        )
        triggers.append("POST-DESIGN-02: Cost_Estimator (Value Engineering)")
        rule_sources.append("INTER_SKILL_TRIGGERS.md §POST-DESIGN-02")
        rule_sources.append("AGENTS.md §17 (W002: VE possible)")

        return PolicyDecision(
            action=Action.TRIGGER_VE,
            status_code=StatusCode.VE_RECOMMENDED,
            color="🟢",
            max_eta=max_eta,
            min_eta=min_eta,
            message=f"ĐẠT & AN TOÀN CAO — η_min = {min_eta:.3f} <= 0.70 (dự trữ > 30%). Kích hoạt Cost_Estimator để xem xét Value Engineering.",
            reasons=reasons,
            triggers=triggers,
            rule_sources=rule_sources,
        )

    # 4. Trạng thái tối ưu chuẩn (0.70 < all_eta <= 0.90)
    reasons.append(f"Tất cả giá trị η đều nằm trong khoảng tối ưu (0.70 < η <= 0.90): η_max = {max_eta:.3f}")
    return PolicyDecision(
        action=Action.PASS,
        status_code=StatusCode.PASS_OPTIMAL,
        color="🟡",
        max_eta=max_eta,
        min_eta=min_eta,
        message=f"ĐẠT — η_max = {max_eta:.3f} (0.70 < η <= 0.90). Thiết kế hợp lý và tối ưu.",
        reasons=reasons,
        triggers=[],
        rule_sources=rule_sources,
    )


# =============================================================================
# SECTION 1B: ĐỒ THỊ TRI THỨC TIÊU CHUẨN — TRÍCH DẪN NGUỒN & PHÁT HIỆN MÂU THUẪN
# =============================================================================
#
# Mối liên kết Policy Engine <-> StandardsGraph:
#   - AGENTS.md §6 là nguồn luật TUYỆT ĐỐI cho ngưỡng η (0.70 / 0.90 / 1.00).
#     Policy Engine KHÔNG tự dịch chuyển ngưỡng theo đồ thị — tránh vi phạm quy tắc.
#   - StandardsGraph cung cấp CĂN CỨ cho ngưỡng: điều khoản nào, tiêu chuẩn nào,
#     công thức nào, ngưỡng riêng của phép kiểm tra là bao nhiêu.
#   - Nếu ngưỡng riêng trong tiêu chuẩn LỆCH khỏi ngưỡng 1.00 của AGENTS.md §6,
#     đó là tín hiệu MÂU THUẪN cần báo cáo (không tự ý quyết định).
#
# Xem .agents/_SHARED/standards/standards_graph.py

import re as _re
from pathlib import Path as _Path
from dataclasses import replace as _dataclass_replace

# Ngưỡng η tuyệt đối theo AGENTS.md §6 — giá trị chuẩn để đối chiếu.
AGENTS_ETA_ULS_LIMIT = 1.00

# Ánh xạ loại cấu kiện (tiếng Anh/Việt) -> node id trong StandardsGraph
ELEMENT_TYPE_TO_NODE = {
    "beam": "ELEMENT_BEAM",
    "dầm": "ELEMENT_BEAM",
    "dam": "ELEMENT_BEAM",
    "rc_beam": "ELEMENT_BEAM",
    "column": "ELEMENT_COLUMN",
    "cột": "ELEMENT_COLUMN",
    "cot": "ELEMENT_COLUMN",
    "rc_column": "ELEMENT_COLUMN",
    "steel_beam": "ELEMENT_STEEL_BEAM",
    "dầm thép": "ELEMENT_STEEL_BEAM",
    "dam_thep": "ELEMENT_STEEL_BEAM",
}

_standards_graph_cache: Dict[str, Any] = {}


def _get_standards_graph(graph: Any = None):
    """
    Lấy instance StandardsGraph (lazy import + cache).

    - Nếu truyền `graph` -> dùng luôn (tiện cho test).
    - Nếu không -> import từ .agents/_SHARED/standards/standards_graph.py.

    Trả về None nếu không import được — Policy Engine KHÔNG BAO GIỜ crash
    vì thiếu đồ thị tri thức (fail-safe: quyết định vẫn đúng theo AGENTS.md).
    """
    if graph is not None:
        return graph
    if "instance" in _standards_graph_cache:
        return _standards_graph_cache["instance"]

    try:
        import sys as _sys
        _standards_dir = _Path(__file__).resolve().parent.parent / "_SHARED" / "standards"
        if str(_standards_dir) not in _sys.path:
            _sys.path.insert(0, str(_standards_dir))
        from standards_graph import StandardsGraph as _SG
        instance = _SG()
        _standards_graph_cache["instance"] = instance
        return instance
    except Exception:
        _standards_graph_cache["instance"] = None
        return None


def _parse_threshold_value(threshold: Any) -> Optional[float]:
    """
    Trích ngưỡng số từ chuỗi threshold của StandardsGraph.
    - "<= 1.00"   -> 1.0
    - "<= 0.95"   -> 0.95
    - "<= L/200"  -> None (tỷ số phân số, không phải ngưỡng η)
    - "<= 1/200"  -> None (tỷ số, không phải η)
    - "x/y" bất kỳ -> None (phân số, không chuyển được về η)
    """
    if isinstance(threshold, (int, float)):
        return float(threshold)
    if not isinstance(threshold, str):
        return None
    s = threshold.strip()
    # Phân số (L/200, 1/200, ...) -> không phải ngưỡng η đơn giản -> None
    if _re.search(r"\d+\s*/\s*\d+", s):
        return None
    m = _re.search(r"(\d+(?:[.,]\d+)?)\s*$", s)
    if not m:
        return None
    raw = m.group(1).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def resolve_element_node(
    element_id: Optional[str] = None,
    element_type: Optional[str] = None,
) -> Optional[str]:
    """
    Chuẩn hoá định danh cấu kiện thành node id của StandardsGraph.
    - element_id dạng "ELEMENT_BEAM" -> giữ nguyên.
    - element_type "beam"/"dầm"/"cot" -> tra bảng ELEMENT_TYPE_TO_NODE.
    """
    if element_id:
        eid = str(element_id).strip()
        if eid.upper().startswith("ELEMENT_"):
            return eid.upper()
        mapped = ELEMENT_TYPE_TO_NODE.get(eid.lower())
        if mapped:
            return mapped
    if element_type:
        return ELEMENT_TYPE_TO_NODE.get(str(element_type).strip().lower())
    return None


def resolve_standard_basis(
    element_id: Optional[str] = None,
    element_type: Optional[str] = None,
    graph: Any = None,
) -> Optional[Dict[str, Any]]:
    """
    Tra cứu căn cứ tiêu chuẩn cho một cấu kiện trong StandardsGraph.

    Trả về dict:
        {
            "element_node": "ELEMENT_BEAM",
            "element_name": "Dầm bê tông cốt thép",
            "standards": ["TCVN 5574:2018", ...],
            "clauses": [{"id", "standard", "clause_no", "title"}],
            "checks": [{"id", "limit_type", "formula", "threshold", "threshold_value"}],
        }
    hoặc None nếu không tra được.
    """
    sg = _get_standards_graph(graph)
    if sg is None:
        return None

    node_id = resolve_element_node(element_id, element_type)
    if not node_id:
        return None

    try:
        reqs = sg.query_element_requirements(node_id)
    except Exception:
        return None

    if not reqs or reqs.get("error"):
        return None

    checks = []
    for c in reqs.get("verification_checks", []) or []:
        item = dict(c)
        item["threshold_value"] = _parse_threshold_value(item.get("threshold"))
        checks.append(item)

    return {
        "element_node": node_id,
        "element_name": (reqs.get("element") or {}).get("name"),
        "standards": reqs.get("connected_standards", []) or [],
        "clauses": reqs.get("applicable_clauses", []) or [],
        "checks": checks,
    }


def _find_conflicts(basis: Dict[str, Any]) -> List[str]:
    """
    Phát hiện mâu thuẫn giữa ngưỡng riêng trong tiêu chuẫn và ngưỡng η của AGENTS.md §6.
    - Chỉ xét các check ULS (trạng thái giới hạn) có ngưỡng số.
    - Ngưỡng lệch khỏi 1.00 -> báo cáo mâu thuẫn (KHÔNG tự quyết định thay).
    """
    conflicts: List[str] = []
    for chk in basis.get("checks", []) or []:
        if chk.get("limit_type") != "ULS":
            continue
        tv = chk.get("threshold_value")
        if tv is None:
            continue
        if abs(tv - AGENTS_ETA_ULS_LIMIT) > 1e-9:
            clause_txt = ""
            for cl in basis.get("clauses", []) or []:
                if chk["id"] in str(cl.get("id", "")) or cl.get("id") in str(chk.get("id", "")):
                    clause_txt = f" [{cl.get('standard', '?')} {cl.get('clause_no', '')}]"
                    break
            conflicts.append(
                f"Phép kiểm tra '{chk['id']}'{clause_txt} đặt ngưỡng η = {tv:.3f} "
                f"khác ngưỡng AGENTS.md §6 (η <= {AGENTS_ETA_ULS_LIMIT:.2f}). Cần lưu ý."
            )
    return conflicts


def _format_citation(basis: Dict[str, Any]) -> List[str]:
    """Tạo chuỗi trích dẫn tiêu chuẩn để bổ sung vào rule_sources."""
    out: List[str] = []
    clauses = basis.get("clauses") or []
    seen = set()
    for cl in clauses:
        std = cl.get("standard", "?")
        cno = cl.get("clause_no", "")
        key = f"{std}|{cno}"
        if key in seen:
            continue
        seen.add(key)
        out.append(f"Đồ thị tri thức: {std} {cno} — {cl.get('title', '')}".strip())
    return out


def decide_eta_with_standards(
    eta_input: Union[float, int, Dict[str, Any], List[Union[float, int]]],
    element_id: Optional[str] = None,
    element_type: Optional[str] = None,
    graph: Any = None,
) -> PolicyDecision:
    """
    Quyết định hành động theo η, kèm CĂN CỨ TIÊU CHUẨN từ StandardsGraph.

    Hành vi:
    1. Gọi `decide_eta()` để lấy quyết định theo AGENTS.md §6 (ngưỡng KHÔNG đổi).
    2. Tra StandardsGraph để bổ sung:
       - rule_sources: điều khoản tiêu chuẩn điều khiển phép kiểm tra.
       - reasons: câu giải thích "vì sao ngưỡng này áp dụng".
       - standard_basis: toàn bộ căn cứ (tiêu chuẩn / điều khoản / phép kiểm tra).
       - standard_conflicts: cảnh báo nếu ngưỡng tiêu chuẩn lệch ngưỡng AGENTS.md.

    Nếu đồ thị không khả dụng -> trả về đúng như `decide_eta()` (fail-safe).
    """
    decision = decide_eta(eta_input)

    basis = resolve_standard_basis(element_id, element_type, graph)
    if not basis:
        return decision

    citations = _format_citation(basis)
    conflicts = _find_conflicts(basis)

    reasons = list(decision.reasons)
    rule_sources = list(decision.rule_sources)

    if citations:
        reasons.append(
            "Căn cứ tiêu chuẩn (đồ thị tri thức): "
            + "; ".join(f"{c.get('standard', '?')} {c.get('clause_no', '')}".strip()
                        for c in (basis.get("clauses") or [])[:3])
        )
    if conflicts:
        reasons.extend(conflicts)

    return _dataclass_replace(
        decision,
        reasons=reasons,
        rule_sources=rule_sources + citations,
        standard_basis=basis,
        standard_conflicts=conflicts,
    )


# =============================================================================
# SECTION 2: PHASE B — 15 INTER-SKILL TRIGGERS (INTER_SKILL_TRIGGERS.md)
# =============================================================================

class TriggerPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TriggerType(str, Enum):
    POST_COMPLETION = "POST_COMPLETION"
    CONDITIONAL = "CONDITIONAL"
    ERROR = "ERROR"
    MANUAL = "MANUAL"


@dataclass(frozen=True)
class TriggerDefinition:
    """Định nghĩa metadata của 1 Trigger trong hệ thống."""
    trigger_id: str
    name: str
    trigger_type: TriggerType
    source_skill: str
    target_skill: str
    priority: TriggerPriority
    condition_desc: str
    action: str
    handoff_type: Optional[str] = None
    pipeline: Optional[str] = None


@dataclass(frozen=True)
class TriggerEvaluationResult:
    """Kết quả đánh giá 1 trigger."""
    trigger_id: str
    fired: bool
    target_skill: str
    priority: TriggerPriority
    action: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    handoff_type: Optional[str] = None


INTER_SKILL_TRIGGERS_REGISTRY: Dict[str, TriggerDefinition] = {
    "POST-SDE-001": TriggerDefinition(
        trigger_id="POST-SDE-001",
        name="Structural Design → Design Evaluation",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="Structural_Design_Engineer",
        target_skill="Design_Evaluation",
        priority=TriggerPriority.HIGH,
        condition_desc="pipeline in ('design-review', 'to_trinh')",  # v7.1: conditional, not always
        action="TRIGGER_SKILL",
        handoff_type="structural_design_to_eval",
        pipeline="Design_Pipeline",
    ),
    "POST-DEV-001": TriggerDefinition(
        trigger_id="POST-DEV-001",
        name="Design Evaluation → SKILL_PHULUC",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="Design_Evaluation",
        target_skill="SKILL_PHULUC",
        priority=TriggerPriority.NORMAL,
        condition_desc="evaluation_type == 'REVIEW' and status == 'PASS'",
        action="TRIGGER_SKILL",
        handoff_type="eval_to_phuluc",
        pipeline="Design_Pipeline",
    ),
    "POST-SDE-002": TriggerDefinition(
        trigger_id="POST-SDE-002",
        name="Structural Design → SKILL_VERIFY",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="Structural_Design_Engineer",
        target_skill="SKILL_VERIFY",
        priority=TriggerPriority.MEDIUM,
        condition_desc="confidence_level < 0.85 or manual_request == True",
        action="TRIGGER_SKILL",
        handoff_type="any_to_verify",
        pipeline="Design_Pipeline",
    ),
    "POST-GEOTECH-01": TriggerDefinition(
        trigger_id="POST-GEOTECH-01",
        name="Geotech → Structural Design (Foundation Params)",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="SKILL_GEOTECH",
        target_skill="Structural_Design_Engineer",
        priority=TriggerPriority.HIGH,
        condition_desc="foundation_params_ready == True",
        action="TRIGGER_SKILL",
        handoff_type="geotech_to_structural",
        pipeline="Geotech_Pipeline",
    ),
    "POST-GEOTECH-02": TriggerDefinition(
        trigger_id="POST-GEOTECH-02",
        name="Geotech → Design Evaluation (Base Heave Review)",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="SKILL_GEOTECH",
        target_skill="Design_Evaluation",
        priority=TriggerPriority.HIGH,
        condition_desc="base_heave_FS < 1.5",
        action="ALERT_AND_TRIGGER",
        handoff_type="geotech_to_eval",
        pipeline="Geotech_Pipeline",
    ),
    "POST-GEOTECH-03": TriggerDefinition(
        trigger_id="POST-GEOTECH-03",
        name="Geotech → SKILL_FORENSIC (Adverse Conditions)",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="SKILL_GEOTECH",
        target_skill="SKILL_FORENSIC",
        priority=TriggerPriority.CRITICAL,
        condition_desc="adverse_conditions_detected == True",
        action="ALERT_AND_TRIGGER",
        handoff_type="geotech_to_forensic",
        pipeline="Geotech_Pipeline",
    ),
    "POST-EVAL-01": TriggerDefinition(
        trigger_id="POST-EVAL-01",
        name="Design Evaluation → Cost Estimator (VE Opportunity)",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="Design_Evaluation",
        target_skill="Cost_Estimator",
        priority=TriggerPriority.MEDIUM,
        condition_desc="any element has eta <= 0.70 and max_eta <= 1.00",
        action="TRIGGER_SKILL",
        handoff_type="eval_to_cost",
        pipeline="Review_Pipeline",
    ),
    "POST-EVAL-02": TriggerDefinition(
        trigger_id="POST-EVAL-02",
        name="Design Evaluation → SKILL_VERIFY (Standard Conflict)",
        trigger_type=TriggerType.POST_COMPLETION,
        source_skill="Design_Evaluation",
        target_skill="SKILL_VERIFY",
        priority=TriggerPriority.HIGH,
        condition_desc="standard_version_mismatch == True",
        action="TRIGGER_SKILL",
        handoff_type="any_to_verify",
        pipeline="Review_Pipeline",
    ),
    "COND-VE-001": TriggerDefinition(
        trigger_id="COND-VE-001",
        name="Value Engineering Trigger",
        trigger_type=TriggerType.CONDITIONAL,
        source_skill="ANY",
        target_skill="Cost_Estimator",
        priority=TriggerPriority.MEDIUM,
        condition_desc="any element has eta <= 0.70",
        action="TRIGGER_SKILL",
        pipeline="Global",
    ),
    "COND-WARNING-001": TriggerDefinition(
        trigger_id="COND-WARNING-001",
        name="Warning Boundary Alert",
        trigger_type=TriggerType.CONDITIONAL,
        source_skill="ANY",
        target_skill="USER",
        priority=TriggerPriority.HIGH,
        condition_desc="any element has 0.90 < eta <= 1.00",
        action="ALERT_USER",
        pipeline="Global",
    ),
    "COND-FAIL-001": TriggerDefinition(
        trigger_id="COND-FAIL-001",
        name="Design Failure Alert",
        trigger_type=TriggerType.CONDITIONAL,
        source_skill="ANY",
        target_skill="USER",
        priority=TriggerPriority.CRITICAL,
        condition_desc="any element has eta > 1.00",
        action="BLOCK_EXPORT",
        pipeline="Global",
    ),
    "COND-CONF-001": TriggerDefinition(
        trigger_id="COND-CONF-001",
        name="Low Confidence → SKILL_VERIFY (Full)",
        trigger_type=TriggerType.CONDITIONAL,
        source_skill="ANY",
        target_skill="SKILL_VERIFY",
        priority=TriggerPriority.HIGH,
        condition_desc="confidence_level == 'LOW' or confidence_score < 0.60",
        action="PAUSE_AND_VERIFY",
        pipeline="Global",
    ),
    "COND-CONF-002": TriggerDefinition(
        trigger_id="COND-CONF-002",
        name="Medium Confidence → SKILL_VERIFY (Spot Check)",
        trigger_type=TriggerType.CONDITIONAL,
        source_skill="ANY",
        target_skill="SKILL_VERIFY",
        priority=TriggerPriority.MEDIUM,
        condition_desc="confidence_level == 'MEDIUM' or 0.60 <= confidence_score < 0.85",
        action="CONTINUE_WITH_WARNING",
        pipeline="Global",
    ),
    "ERR-STANDARD-001": TriggerDefinition(
        trigger_id="ERR-STANDARD-001",
        name="Standard Version Conflict → SKILL_VERIFY",
        trigger_type=TriggerType.ERROR,
        source_skill="ANY",
        target_skill="SKILL_VERIFY",
        priority=TriggerPriority.HIGH,
        condition_desc="error.code == 'E004'",
        action="BLOCK_UNTIL_RESOLVED",
        pipeline="Global",
    ),
    "ERR-DATA-001": TriggerDefinition(
        trigger_id="ERR-DATA-001",
        name="Missing Data → SKILL_RFI",
        trigger_type=TriggerType.ERROR,
        source_skill="ANY",
        target_skill="SKILL_RFI",
        priority=TriggerPriority.HIGH,
        condition_desc="error.code == 'E002'",
        action="AWAIT_DATA",
        pipeline="Global",
    ),
}


def evaluate_trigger(trigger_id: str, context: Dict[str, Any]) -> TriggerEvaluationResult:
    """Đánh giá điều kiện thực thi của 1 trigger cụ thể trong 15 triggers."""
    if trigger_id not in INTER_SKILL_TRIGGERS_REGISTRY:
        raise KeyError(f"Trigger ID '{trigger_id}' không tồn tại trong INTER_SKILL_TRIGGERS_REGISTRY.")

    trig = INTER_SKILL_TRIGGERS_REGISTRY[trigger_id]
    fired = False
    details: Dict[str, Any] = {}
    message = ""

    if trigger_id == "POST-SDE-001":
        # v7.1 (Argon audit 3A): Chỉ fire khi pipeline = design-review hoặc to_trinh.
        # Tránh auto-trigger DE sau MỌI thiết kế (sai với AGENTS.md §18.2).
        pipeline = str(context.get("pipeline", "")).lower().strip()
        if pipeline in ("design-review", "to_trinh"):
            fired = True
            message = f"Pipeline='{pipeline}': Hoàn thành thiết kế kết cấu -> Tự động chuyển Design_Evaluation để review/thẩm tra."
            details["pipeline"] = pipeline
        else:
            fired = False
            message = f"Pipeline='{pipeline or '(none)'}': Không auto-trigger Design_Evaluation (chỉ fire trong design-review hoặc to_trinh pipeline)."
            details["pipeline"] = pipeline

    elif trigger_id == "POST-DEV-001":
        eval_type = str(context.get("evaluation_type", "")).upper()
        status = str(context.get("status", "")).upper()
        if eval_type == "REVIEW" and status == "PASS":
            fired = True
            message = "Review đạt yêu cầu (PASS) -> Kích hoạt SKILL_PHULUC để xuất phụ lục tính toán."
        else:
            message = f"Không thỏa điều kiện (cần REVIEW & PASS, hiện tại: {eval_type} & {status})."

    elif trigger_id == "POST-SDE-002":
        conf_score = context.get("confidence_score")
        conf_level = str(context.get("confidence_level", "")).upper()
        manual_req = bool(context.get("manual_request", False))
        if manual_req or (conf_score is not None and float(conf_score) < 0.85) or conf_level in ("LOW", "MEDIUM"):
            fired = True
            message = f"Độ tin cậy chưa đạt HIGH (score={conf_score}, level={conf_level}, manual={manual_req}) -> Chuyển SKILL_VERIFY QA check."
        else:
            message = f"Độ tin cậy đạt HIGH ({conf_score}) -> Không cần verify tự động."

    elif trigger_id == "POST-GEOTECH-01":
        ready = bool(context.get("foundation_params_ready", False))
        if ready:
            fired = True
            message = "Thông số địa kỹ thuật/móng đã sẵn sàng -> Handoff sang Structural_Design_Engineer."
            details["foundation_params"] = context.get("foundation_params", {})
        else:
            message = "Thông số địa kỹ thuật chưa sẵn sàng."

    elif trigger_id == "POST-GEOTECH-02":
        fs = context.get("base_heave_FS")
        if fs is not None and float(fs) < 1.5:
            fired = True
            message = f"Hệ số an toàn trồi đáy hố đào FS = {float(fs):.2f} < 1.5 (nguy hiểm) -> Cảnh báo khẩn cấp tới Design_Evaluation."
            details["base_heave_FS"] = float(fs)
        else:
            message = f"Hệ số an toàn trồi đáy FS = {fs} >= 1.5 (an toàn)."

    elif trigger_id == "POST-GEOTECH-03":
        adv = bool(context.get("adverse_conditions_detected", False))
        if adv:
            fired = True
            message = "Phát hiện điều kiện địa chất bất lợi nghiêm trọng -> Kích hoạt điều tra sự cố SKILL_FORENSIC."
            details["adverse_conditions"] = context.get("adverse_conditions", [])
        else:
            message = "Không phát hiện điều kiện địa chất bất thường."

    elif trigger_id == "POST-EVAL-01":
        design_res = context.get("design_results")
        if design_res:
            try:
                # Dùng bản có căn cứ tiêu chuẩn (đồ thị tri thức) — quyết định η
                # KHÔNG đổi so với decide_eta, chỉ bổ sung trích dẫn + phát hiện mâu thuẫn.
                dec = decide_eta_with_standards(
                    design_res,
                    element_id=context.get("element_id"),
                    element_type=context.get("element_type"),
                )
                if dec.action == Action.TRIGGER_VE:
                    fired = True
                    message = f"Phát hiện phần tử có η <= 0.70 (min_eta={dec.min_eta:.2f}) -> Kích hoạt Cost_Estimator để Value Engineering."
                    details["min_eta"] = dec.min_eta
                    details["max_eta"] = dec.max_eta
                if dec.standard_basis:
                    details["standard_basis"] = dec.standard_basis
                    details["standard_citations"] = [
                        rs for rs in dec.rule_sources if rs.startswith("Đồ thị tri thức:")
                    ]
                if dec.standard_conflicts:
                    fired = True
                    details["standard_conflicts"] = dec.standard_conflicts
                    message += " | CẢNH BÁO MÂU THUẪN TIÊU CHUẨN: " + "; ".join(dec.standard_conflicts)
            except Exception as e:
                message = f"Lỗi tính toán η: {e}"
        else:
            message = "Không có dữ liệu design_results để đánh giá VE."

    elif trigger_id == "POST-EVAL-02":
        mismatch = bool(context.get("standard_version_mismatch", False))
        if mismatch:
            fired = True
            message = "Phát hiện mâu thuẫn phiên bản tiêu chuẩn thiết kế -> Chuyển SKILL_VERIFY để xử lý xung đột."
            details["conflict_info"] = context.get("conflict_info", {})
        else:
            message = "Tiêu chuẩn đồng nhất, không có xung đột phiên bản."

    elif trigger_id == "COND-VE-001":
        design_res = context.get("design_results")
        if design_res:
            try:
                items = _extract_eta_values(design_res)
                ve_items = [val for _, val in items if val <= 0.70]
                fail_items = [val for _, val in items if val > 1.00]
                if ve_items and not fail_items:
                    fired = True
                    message = f"Phát hiện {len(ve_items)} phần tử có η ≤ 70% - Có cơ hội Value Engineering."
                    details["count"] = len(ve_items)
            except Exception as e:
                message = f"Lỗi trích xuất η: {e}"

    elif trigger_id == "COND-WARNING-001":
        design_res = context.get("design_results")
        if design_res:
            try:
                items = _extract_eta_values(design_res)
                warn_items = [val for _, val in items if 0.90 < val <= 1.00]
                if warn_items:
                    fired = True
                    message = f"⚠️ {len(warn_items)} phần tử có η > 90% (sát ngưỡng cho phép) - Cần lưu ý."
                    details["count"] = len(warn_items)
            except Exception as e:
                message = f"Lỗi trích xuất η: {e}"

    elif trigger_id == "COND-FAIL-001":
        design_res = context.get("design_results")
        if design_res:
            try:
                items = _extract_eta_values(design_res)
                fail_items = [val for _, val in items if val > 1.00]
                if fail_items:
                    fired = True
                    message = f"🔴 {len(fail_items)} phần tử vượt khả năng chịu lực (η > 1.00) - YÊU CẦU ĐIỀU CHỈNH THIẾT KẾ."
                    details["count"] = len(fail_items)
                    details["max_eta"] = max(fail_items)
            except Exception as e:
                message = f"Lỗi trích xuất η: {e}"

    elif trigger_id == "COND-CONF-001":
        score = context.get("confidence_score")
        level = str(context.get("confidence_level", "")).upper()
        if (score is not None and float(score) < 0.60) or level == "LOW":
            fired = True
            message = f"Độ tin cậy LOW (score={score}) -> BLOCK/PAUSE quy trình và yêu cầu SKILL_VERIFY kiểm tra toàn diện."
            details["confidence_score"] = score
            details["scope"] = "FULL"

    elif trigger_id == "COND-CONF-002":
        score = context.get("confidence_score")
        level = str(context.get("confidence_level", "")).upper()
        if (score is not None and 0.60 <= float(score) < 0.85) or level == "MEDIUM":
            fired = True
            message = f"Độ tin cậy MEDIUM (score={score}) -> Tiếp tục quy trình nhưng cảnh báo và gửi SKILL_VERIFY kiểm tra chọn điểm."
            details["confidence_score"] = score
            details["scope"] = "SPOT_CHECK"

    elif trigger_id == "ERR-STANDARD-001":
        err = context.get("error")
        err_code = None
        if isinstance(err, dict):
            err_code = err.get("code")
        elif isinstance(err, str):
            err_code = err
        if not err_code:
            err_code = context.get("error_code")
        if err_code == "E004":
            fired = True
            message = "Mã lỗi E004 (Standard Conflict) -> BLOCK quy trình cho đến khi SKILL_VERIFY giải quyết xong mâu thuẫn."
            details["error_code"] = "E004"

    elif trigger_id == "ERR-DATA-001":
        err = context.get("error")
        err_code = None
        if isinstance(err, dict):
            err_code = err.get("code")
        elif isinstance(err, str):
            err_code = err
        if not err_code:
            err_code = context.get("error_code")
        if err_code == "E002":
            fired = True
            message = "Mã lỗi E002 (Missing Required Data) -> Tự động sinh RFI qua SKILL_RFI yêu cầu bổ sung dữ liệu."
            details["error_code"] = "E002"

    return TriggerEvaluationResult(
        trigger_id=trigger_id,
        fired=fired,
        target_skill=trig.target_skill,
        priority=trig.priority,
        action=trig.action,
        message=message,
        details=details,
        handoff_type=trig.handoff_type,
    )


def evaluate_all_triggers(
    context: Dict[str, Any], source_skill: Optional[str] = None, include_global: bool = True
) -> List[TriggerEvaluationResult]:
    """Đánh giá tất cả triggers khả dĩ trong context."""
    results: List[TriggerEvaluationResult] = []
    for tid, trig in INTER_SKILL_TRIGGERS_REGISTRY.items():
        if source_skill:
            if trig.source_skill != source_skill:
                if not (include_global and trig.source_skill == "ANY"):
                    continue
        res = evaluate_trigger(tid, context)
        results.append(res)
    return results


def get_active_fired_triggers(
    context: Dict[str, Any], source_skill: Optional[str] = None, include_global: bool = True
) -> List[TriggerEvaluationResult]:
    """Chỉ trả về danh sách các triggers THỰC SỰ ĐƯỢC KÍCH HOẠT (fired=True)."""
    all_res = evaluate_all_triggers(context, source_skill=source_skill, include_global=include_global)
    return [r for r in all_res if r.fired]


# =============================================================================
# SECTION 3: PHASE C — 18 RED FLAG TRIGGERS (SKILL_FORENSIC)
# =============================================================================

class RedFlagSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # 🔴 RCF: Rời khỏi công trình ngay lập tức
    HIGH = "HIGH"          # 🟠 RHF: Sơ tán, chống đỡ tạm, xử lý trong 2h
    MEDIUM = "MEDIUM"      # 🟡 RMF: Tăng cường giám sát, xử lý trong 48h
    LOW = "LOW"            # 🟢 RLF: Ghi nhận, theo dõi trong 1 tuần


class RedFlagAction(str, Enum):
    LEAVE_SITE = "LEAVE_SITE"
    EVACUATE = "EVACUATE"
    INVESTIGATE = "INVESTIGATE"
    MONITOR = "MONITOR"


@dataclass(frozen=True)
class RedFlagDefinition:
    """Định nghĩa metadata của 1 Red Flag Trigger."""
    flag_id: str
    name: str
    severity: RedFlagSeverity
    action: RedFlagAction
    deadline: str
    keywords: List[str]
    description: str
    rationale: str


@dataclass(frozen=True)
class RedFlagEvaluationResult:
    """Kết quả kiểm tra 1 Red Flag."""
    flag_id: str
    triggered: bool
    severity: RedFlagSeverity
    action: RedFlagAction
    deadline: str
    name: str
    message: str
    matched_clues: List[str] = field(default_factory=list)


RED_FLAG_REGISTRY: Dict[str, RedFlagDefinition] = {
    # --- 1. CRITICAL FLAGS (RCF: 5 Triggers) ---
    "RCF-01": RedFlagDefinition(
        flag_id="RCF-01",
        name="Sập / Gãy Cấu kiện",
        severity=RedFlagSeverity.CRITICAL,
        action=RedFlagAction.LEAVE_SITE,
        deadline="Ngay lập tức",
        keywords=["sập", "gãy", "đứt", "sụp", "collapse", "gãy cột", "đứt dầm", "phá hoại giòn"],
        description="Cấu kiện bị phá hoại toàn phần (thanh cột gãy, dầm đứt).",
        rationale="Nguy hiểm đến tính mạng, cần sơ tán toàn bộ khu vực ngay lập tức.",
    ),
    "RCF-02": RedFlagDefinition(
        flag_id="RCF-02",
        name="Võng Quá Mức Thấy Được (≥ L/50)",
        severity=RedFlagSeverity.CRITICAL,
        action=RedFlagAction.LEAVE_SITE,
        deadline="Ngay lập tức",
        keywords=["võng quá mức", "l/50", "võng thấy rõ", "võng nhìn thấy", "sagging excessive"],
        description="Độ võng dầm/sàn nhìn thấy bằng mắt thường (≥ L/50).",
        rationale="Dấu hiệu phá hoại cấu trúc nghiêm trọng sắp xảy ra.",
    ),
    "RCF-03": RedFlagDefinition(
        flag_id="RCF-03",
        name="Tiếng Động Lạ / Nổ Kết Cấu",
        severity=RedFlagSeverity.CRITICAL,
        action=RedFlagAction.LEAVE_SITE,
        deadline="Ngay lập tức",
        keywords=["tiếng nổ", "tiếng rắc", "tiếng cót két", "tiếng động lạ", "tiếng nứt lớn", "loud bang", "cracking sound"],
        description="Tiếng nổ, kẹt, rắc rắc phát ra từ cấu kiện kết cấu chịu lực.",
        rationale="Tín hiệu giải phóng ứng suất hoặc đứt cốt thép / bu lông đột ngột.",
    ),
    "RCF-04": RedFlagDefinition(
        flag_id="RCF-04",
        name="Vết nứt Xuyên Thấu (≥ 3mm)",
        severity=RedFlagSeverity.CRITICAL,
        action=RedFlagAction.LEAVE_SITE,
        deadline="Ngay lập tức",
        keywords=["nứt xuyên thấu", "nứt qua tiết diện", "nứt xuyên", "through crack", "nứt >= 3mm", "nứt rộng > 3mm"],
        description="Vết nứt xuyên qua tiết diện cột, dầm, vách với bề rộng ≥ 3mm.",
        rationale="Mất hoàn toàn khả năng chịu lực cục bộ của cấu kiện.",
    ),
    "RCF-05": RedFlagDefinition(
        flag_id="RCF-05",
        name="Vết nứt Động (Mở Rộng Theo Thời Gian)",
        severity=RedFlagSeverity.CRITICAL,
        action=RedFlagAction.LEAVE_SITE,
        deadline="Ngay lập tức",
        keywords=["nứt động", "nứt mở rộng", "nứt lan nhanh", "vết nứt đang tiến triển", "active crack", "propagating crack"],
        description="Vết nứt mở rộng hoặc lan dài theo thời gian quan sát trong ca kiểm tra.",
        rationale="Cấu kiện đang trong trạng thái mất ổn định động, sắp sụp đổ.",
    ),

    # --- 2. HIGH FLAGS (RHF: 6 Triggers) ---
    "RHF-01": RedFlagDefinition(
        flag_id="RHF-01",
        name="Vết nứt Chéo Lớn trên Cột (≥ 1.5mm)",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["nứt chéo cột", "nứt xiên cột", "nứt 45 độ", "shear crack column", "nứt cắt cột"],
        description="Vết nứt xiên 45° trên cột chịu nén uốn với bề rộng ≥ 1.5mm.",
        rationale="Dấu hiệu đặc trưng của phá hoại cắt nguy hiểm trên cột.",
    ),
    "RHF-02": RedFlagDefinition(
        flag_id="RHF-02",
        name="Vết nứt Kết Hợp Trên Sàn / Punching",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["punching shear", "đâm thủng", "nứt mắt cá", "nứt bảng sàn", "nứt nón đầu cột"],
        description="Vết nứt hình mắt cá lưới trên sàn kèm võng, hoặc nứt nón quanh đầu cột.",
        rationale="Nguy cơ phá hoại đâm thủng đột ngột của sàn nấm / sàn phẳng.",
    ),
    "RHF-03": RedFlagDefinition(
        flag_id="RHF-03",
        name="Lún Không Đều Gây Nghiêng (≥ 1/200)",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["lún lệch", "lún không đều", "nghiêng công trình", "lún nghiêng", "chênh lún 1/200", "differential settlement"],
        description="Độ chênh lún giữa 2 mốc kề cận ≥ 1/200 gây nghiêng kết cấu rõ rệt.",
        rationale="Gây mômen uốn phụ thứ cấp cực lớn, nguy cơ lật công trình.",
    ),
    "RHF-04": RedFlagDefinition(
        flag_id="RHF-04",
        name="Liên Kết Bu Lông / Đường Hàn Hư Hỏng",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["bu lông lỏng", "nứt đường hàn", "đứt bu lông", "bản mã biến dạng", "bolt loose", "weld crack"],
        description="Bu lông bị đứt/lỏng, bản mã bị oằn, mối hàn nứt nghiêm trọng.",
        rationale="Khớp nối kết cấu mất độ cứng và khả năng truyền lực thiết kế.",
    ),
    "RHF-05": RedFlagDefinition(
        flag_id="RHF-05",
        name="Bê Tông Phong Hóa / Rỗng Xốp",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["bê tông xốp", "bê tông phong hóa", "rỗng bê tông", "bê tông bở", "honeycomb severe", "bê tông bấm tay thủng"],
        description="Bê tông bị rỗng tổ ong lớn, mục nát, phong hóa có thể bẻ bằng tay.",
        rationale="Cường độ bê tông thực tế thấp hơn thiết kế nghiêm trọng.",
    ),
    "RHF-06": RedFlagDefinition(
        flag_id="RHF-06",
        name="Cốt Thép Gỉ Ăn Thủng / Giảm Tiết Diện",
        severity=RedFlagSeverity.HIGH,
        action=RedFlagAction.EVACUATE,
        deadline="Trong 2 giờ",
        keywords=["thép gỉ", "gỉ thép", "gỉ bong tróc", "giảm tiết diện", "thép gỉ thủng", "rebar corrosion", "gỉ ăn mòn"],
        description="Cốt thép bị gỉ oxy hóa bong tróc làm suy giảm tiết diện thấy rõ.",
        rationale="Suy giảm lực kéo/nén của cốt thép, nứt vỡ lớp bê tông bảo vệ.",
    ),

    # --- 3. MEDIUM FLAGS (RMF: 4 Triggers) ---
    "RMF-01": RedFlagDefinition(
        flag_id="RMF-01",
        name="Vết Nứt Uốn Dầm Thông Thường (< 1mm)",
        severity=RedFlagSeverity.MEDIUM,
        action=RedFlagAction.INVESTIGATE,
        deadline="Trong 48 giờ",
        keywords=["nứt uốn", "nứt giữa dầm", "nứt thẳng đứng dầm", "flexural crack", "nứt uốn dầm < 1mm"],
        description="Vết nứt thẳng đứng vuông góc trục dầm tại giữa nhịp với bề rộng < 1mm.",
        rationale="Phổ biến trong BTCT nhưng cần đo đạc và kiểm tra giới hạn nứt SLS.",
    ),
    "RMF-02": RedFlagDefinition(
        flag_id="RMF-02",
        name="Vết Nứt Co Ngót Bề Mặt Sàn (< 0.3mm)",
        severity=RedFlagSeverity.MEDIUM,
        action=RedFlagAction.INVESTIGATE,
        deadline="Trong 48 giờ",
        keywords=["nứt co ngót", "nứt bề mặt", "nứt chân chim sàn", "shrinkage crack", "nứt mịn sàn"],
        description="Vết nứt mạng lưới mịn nông (< 0.3mm) trên mặt sàn do co ngót thể tích.",
        rationale="Không gây sập tức thời nhưng ảnh hưởng đến độ bền lâu và ăn mòn.",
    ),
    "RMF-03": RedFlagDefinition(
        flag_id="RMF-03",
        name="Lún Nhỏ Đều Đặn (≤ 5mm/tháng)",
        severity=RedFlagSeverity.MEDIUM,
        action=RedFlagAction.INVESTIGATE,
        deadline="Trong 48 giờ",
        keywords=["lún đều", "lún cố kết", "tốc độ lún < 5mm", "lún chậm", "steady settlement"],
        description="Công trình lún đều đặn với tốc độ ≤ 5mm/tháng, không tăng tốc.",
        rationale="Thường là quá trình cố kết đất nền bình thường, cần lập mốc quan trắc.",
    ),
    "RMF-04": RedFlagDefinition(
        flag_id="RMF-04",
        name="Neo Cốt Thép Bị Trượt (> 10mm)",
        severity=RedFlagSeverity.MEDIUM,
        action=RedFlagAction.INVESTIGATE,
        deadline="Trong 48 giờ",
        keywords=["trượt neo", "neo tuột", "slip anchorage", "trượt thép > 10mm", "neo không bám"],
        description="Thanh cốt thép hoặc đầu cáp dự ứng lực bị trượt khỏi vị trí > 10mm.",
        rationale="Giảm lực dính bám neo, gây tập trung ứng suất vùng đầu mối.",
    ),

    # --- 4. LOW FLAGS (RLF: 3 Triggers) ---
    "RLF-01": RedFlagDefinition(
        flag_id="RLF-01",
        name="Vết Nứt Nhiệt Mạng Nhện Cực Nhỏ",
        severity=RedFlagSeverity.LOW,
        action=RedFlagAction.MONITOR,
        deadline="Trong 1 tuần",
        keywords=["nứt nhiệt", "nứt chân chim ngoài", "thermal crack hair", "nứt nông nhiệt"],
        description="Vết nứt chân chim rất nông bề mặt do ứng suất nhiệt.",
        rationale="Ảnh hưởng thẩm mỹ, nguy cơ rủi ro kết cấu rất thấp.",
    ),
    "RLF-02": RedFlagDefinition(
        flag_id="RLF-02",
        name="Ống Kỹ Thuật Xuyên Sàn / Dầm Nhỏ",
        severity=RedFlagSeverity.LOW,
        action=RedFlagAction.MONITOR,
        deadline="Trong 1 tuần",
        keywords=["lỗ xuyên nhỏ", "ống kỹ thuật xuyên", "penetration small", "xuyên sàn dầm nhỏ"],
        description="Ống kỹ thuật ME xuyên qua dầm/sàn kích thước nhỏ (≤ 1/4 bề rộng).",
        rationale="Cần kiểm tra gia cường bổ sung, thường không gây suy giảm lớn.",
    ),
    "RLF-03": RedFlagDefinition(
        flag_id="RLF-03",
        name="Thay Đổi Tải Trọng / Công Năng Nhỏ",
        severity=RedFlagSeverity.LOW,
        action=RedFlagAction.MONITOR,
        deadline="Trong 1 tuần",
        keywords=["thay đổi công năng", "tăng tải nhẹ", "kê thêm đồ", "minor load change"],
        description="Chủ đầu tư thay đổi tải trọng sử dụng cục bộ mà chưa có bản vẽ cập nhật.",
        rationale="Cần cập nhật vào mô hình tính toán kiểm tra định kỳ.",
    ),
}


def evaluate_red_flag(
    flag_id: str, observation_data: Union[str, Dict[str, Any]]
) -> RedFlagEvaluationResult:
    """
    Kiểm tra một Red Flag cụ thể đối chiếu với dữ liệu hiện trường (text hoặc dict).
    """
    if flag_id not in RED_FLAG_REGISTRY:
        raise KeyError(f"Red Flag ID '{flag_id}' không tồn tại trong RED_FLAG_REGISTRY.")

    flag = RED_FLAG_REGISTRY[flag_id]
    triggered = False
    matched_clues: List[str] = []

    # 1. Nếu observation là string
    if isinstance(observation_data, str):
        text_lower = observation_data.lower()
        for kw in flag.keywords:
            if kw.lower() in text_lower:
                triggered = True
                matched_clues.append(f"Khớp từ khóa: '{kw}'")

    # 2. Nếu observation là dict (dữ liệu đo đạc định lượng)
    elif isinstance(observation_data, dict):
        # Trực tiếp kiểm tra trigger_id nếu có khai báo rõ
        if observation_data.get("flag_id") == flag_id or observation_data.get(flag_id):
            triggered = True
            matched_clues.append(f"Khai báo trực tiếp cờ {flag_id}")

        # Kiểm tra theo tham số kỹ thuật định lượng
        if flag_id == "RCF-02":  # Võng >= L/50
            deflection_ratio = observation_data.get("deflection_ratio")
            if deflection_ratio is not None and float(deflection_ratio) >= (1.0 / 50.0):
                triggered = True
                matched_clues.append(f"Độ võng đo đạc 1/{1.0/float(deflection_ratio):.1f} >= 1/50")

        elif flag_id == "RCF-04":  # Nứt xuyên thấu >= 3mm
            crack_w = observation_data.get("crack_width_mm")
            crack_type = str(observation_data.get("crack_type", "")).lower()
            if (crack_w is not None and float(crack_w) >= 3.0) or "xuyên" in crack_type or "through" in crack_type:
                triggered = True
                matched_clues.append(f"Bề rộng vết nứt {crack_w}mm >= 3.0mm hoặc loại nứt xuyên thấu")

        elif flag_id == "RHF-01":  # Nứt chéo cột >= 1.5mm
            crack_w = observation_data.get("crack_width_mm")
            member = str(observation_data.get("member_type", "")).lower()
            pattern = str(observation_data.get("crack_pattern", "")).lower()
            if (crack_w is not None and float(crack_w) >= 1.5) and ("cột" in member or "column" in member) and ("chéo" in pattern or "xiên" in pattern or "diagonal" in pattern):
                triggered = True
                matched_clues.append(f"Vết nứt xiên cột bề rộng {crack_w}mm >= 1.5mm")

        elif flag_id == "RHF-03":  # Lún chênh >= 1/200
            diff_settlement = observation_data.get("differential_settlement_ratio")
            if diff_settlement is not None and float(diff_settlement) >= (1.0 / 200.0):
                triggered = True
                matched_clues.append(f"Chênh lệch lún 1/{1.0/float(diff_settlement):.1f} >= 1/200")

        # Quét văn bản mô tả nếu có trường 'description' / 'notes' / 'finding'
        for text_field in ("description", "notes", "finding", "symptom"):
            val = observation_data.get(text_field)
            if isinstance(val, str):
                for kw in flag.keywords:
                    if kw.lower() in val.lower():
                        triggered = True
                        matched_clues.append(f"Khớp từ khóa trường '{text_field}': '{kw}'")

    if triggered:
        message = (
            f"[{flag.severity.value}] KÍCH HOẠT {flag.flag_id}: {flag.name}. "
            f"Hành động: {flag.action.value} ({flag.deadline}). Lý do: {flag.rationale}"
        )
    else:
        message = f"Không phát hiện dấu hiệu {flag.flag_id} ({flag.name})."

    return RedFlagEvaluationResult(
        flag_id=flag_id,
        triggered=triggered,
        severity=flag.severity,
        action=flag.action,
        deadline=flag.deadline,
        name=flag.name,
        message=message,
        matched_clues=matched_clues,
    )


def scan_red_flags(
    observations: Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]
) -> List[RedFlagEvaluationResult]:
    """
    Quét toàn bộ 18 Red Flags trên dữ liệu hiện trường và trả về danh sách các cờ ĐÃ BỊ KÍCH HOẠT.
    """
    triggered_flags: List[RedFlagEvaluationResult] = []
    
    # Chuẩn hóa về list
    obs_list: List[Union[str, Dict[str, Any]]] = []
    if isinstance(observations, list):
        obs_list = observations
    else:
        obs_list = [observations]

    for fid in RED_FLAG_REGISTRY.keys():
        flag_triggered = False
        all_clues: List[str] = []
        last_res = None
        for item in obs_list:
            res = evaluate_red_flag(fid, item)
            if res.triggered:
                flag_triggered = True
                all_clues.extend(res.matched_clues)
                last_res = res
        if flag_triggered and last_res:
            triggered_flags.append(
                RedFlagEvaluationResult(
                    flag_id=last_res.flag_id,
                    triggered=True,
                    severity=last_res.severity,
                    action=last_res.action,
                    deadline=last_res.deadline,
                    name=last_res.name,
                    message=last_res.message,
                    matched_clues=list(set(all_clues)),
                )
            )

    # Sắp xếp theo thứ tự ưu tiên: CRITICAL -> HIGH -> MEDIUM -> LOW
    priority_order = {
        RedFlagSeverity.CRITICAL: 0,
        RedFlagSeverity.HIGH: 1,
        RedFlagSeverity.MEDIUM: 2,
        RedFlagSeverity.LOW: 3,
    }
    triggered_flags.sort(key=lambda x: priority_order[x.severity])
    return triggered_flags


# =============================================================================
# SECTION 4: PHASE C — RFI PRIORITY CLASSIFIER (SKILL_RFI)
# =============================================================================

class RFIPriority(str, Enum):
    """
    5 cấp độ ưu tiên của giao dịch kỹ thuật / RFI theo SKILL_RFI.
    """
    CRITICAL = "CRITICAL"  # 🔴 24h, An toàn/Kết cấu, dừng thi công
    URGENT = "URGENT"      # 🟠 3 ngày, Ảnh hưởng tiến độ/critical path
    HIGH = "HIGH"          # 🟡 7 ngày, Kỹ thuật quan trọng (thiếu dữ liệu, mâu thuẫn)
    NORMAL = "NORMAL"      # 🟢 14 ngày, Kỹ thuật thông thường
    ROUTINE = "ROUTINE"    # 🔵 21 ngày, Hành chính, format, bổ sung hồ sơ


@dataclass(frozen=True)
class RFIDecision:
    """Kết quả phân loại mức độ ưu tiên RFI."""
    priority: RFIPriority
    deadline_str: str
    deadline_days: float
    action: str
    color: str
    reasons: List[str] = field(default_factory=list)


def classify_rfi_priority(rfi_input: Union[str, Dict[str, Any]]) -> RFIDecision:
    """
    Phân loại mức độ ưu tiên và thời hạn phản hồi cho RFI / Giao dịch kỹ thuật.
    
    Quy tắc phân loại:
      1. CRITICAL (🔴, 24h): Từ khóa liên quan an toàn, sập, gãy, sai tiết diện chịu lực, vượt tải.
      2. URGENT (🟠, 3 ngày): Liên quan tiến độ, đường găng, phát sinh lớn, chậm công trình.
      3. HIGH (🟡, 7 ngày): Thiếu dữ liệu tính toán kỹ thuật, mâu thuẫn tiêu chuẩn (E002, E004).
      4. ROUTINE (🔵, 21 ngày): Yêu cầu hành chính, định dạng, bản vẽ hoàn công, cập nhật hồ sơ.
      5. NORMAL (🟢, 14 ngày): Làm rõ kỹ thuật thông thường hoặc trình duyệt mẫu vật liệu tiêu chuẩn.
    """
    text_content = ""
    direct_priority = None

    if isinstance(rfi_input, str):
        text_content = rfi_input.lower()
    elif isinstance(rfi_input, dict):
        direct_priority = rfi_input.get("priority") or rfi_input.get("urgency")
        parts: List[str] = []
        for fld in ("title", "subject", "question", "content", "description", "reason", "impact"):
            v = rfi_input.get(fld)
            if isinstance(v, str):
                parts.append(v)
        text_content = " ".join(parts).lower()

    reasons: List[str] = []

    # 1. Nếu có khai báo trực tiếp
    if direct_priority:
        dp = str(direct_priority).upper()
        if dp in RFIPriority.__members__:
            p = RFIPriority(dp)
            if p == RFIPriority.CRITICAL:
                return RFIDecision(priority=p, deadline_str="24h", deadline_days=1.0, action="Dừng thi công công tác liên quan", color="🔴", reasons=[f"Khai báo trực tiếp mức {dp}"])
            elif p == RFIPriority.URGENT:
                return RFIDecision(priority=p, deadline_str="3 ngày", deadline_days=3.0, action="Leo thang khẩn cấp", color="🟠", reasons=[f"Khai báo trực tiếp mức {dp}"])
            elif p == RFIPriority.HIGH:
                return RFIDecision(priority=p, deadline_str="7 ngày", deadline_days=7.0, action="Theo dõi & đôn đốc chặt chẽ", color="🟡", reasons=[f"Khai báo trực tiếp mức {dp}"])
            elif p == RFIPriority.ROUTINE:
                return RFIDecision(priority=p, deadline_str="21 ngày", deadline_days=21.0, action="Batch review định kỳ", color="🔵", reasons=[f"Khai báo trực tiếp mức {dp}"])
            else:
                return RFIDecision(priority=p, deadline_str="14 ngày", deadline_days=14.0, action="Quy trình xem xét tiêu chuẩn", color="🟢", reasons=[f"Khai báo trực tiếp mức {dp}"])

    # 2. Quy tắc CRITICAL (🔴 24h)
    critical_kws = ["sập", "nguy hiểm tính mạng", "sai tiết diện", "vượt tải", "collapse", "gãy cấu kiện", "nứt nghiêm trọng", "dừng thi công"]
    matched_crit = [kw for kw in critical_kws if kw in text_content]
    if matched_crit:
        reasons.append(f"Phát hiện yếu tố nguy hiểm an toàn kết cấu: {', '.join(matched_crit)}")
        return RFIDecision(
            priority=RFIPriority.CRITICAL,
            deadline_str="24h",
            deadline_days=1.0,
            action="Dừng thi công công tác liên quan & yêu cầu đơn vị thiết kế phản hồi khẩn cấp",
            color="🔴",
            reasons=reasons,
        )

    # 3. Quy tắc URGENT (🟠 3 ngày)
    urgent_kws = ["chậm tiến độ", "ảnh hưởng tiến độ", "đường găng", "critical path", "phát sinh chi phí lớn", "thay đổi biện pháp thi công khẩn"]
    matched_urg = [kw for kw in urgent_kws if kw in text_content]
    if matched_urg:
        reasons.append(f"Phát hiện nguy cơ chậm tiến độ / phát sinh công trường: {', '.join(matched_urg)}")
        return RFIDecision(
            priority=RFIPriority.URGENT,
            deadline_str="3 ngày",
            deadline_days=3.0,
            action="Leo thang Ban QLDA & Tổ chức họp kỹ thuật trong 48h",
            color="🟠",
            reasons=reasons,
        )

    # 4. Quy tắc HIGH (🟡 7 ngày)
    high_kws = ["thiếu thông tin", "không rõ quy cách", "mâu thuẫn tiêu chuẩn", "e002", "e004", "data missing", "chưa đủ kích thước thép", "thiếu tải trọng"]
    matched_high = [kw for kw in high_kws if kw in text_content]
    if matched_high:
        reasons.append(f"Phát hiện thiếu hụt thông tin kỹ thuật bắt buộc: {', '.join(matched_high)}")
        return RFIDecision(
            priority=RFIPriority.HIGH,
            deadline_str="7 ngày",
            deadline_days=7.0,
            action="Gửi văn bản làm rõ đến Tư vấn Thiết kế / TVGS",
            color="🟡",
            reasons=reasons,
        )

    # 5. Quy tắc ROUTINE (🔵 21 ngày)
    routine_kws = ["bổ sung hồ sơ lưu", "định dạng bản vẽ", "cập nhật chữ ký", "format bìa", "hồ sơ pháp lý lưu trữ"]
    matched_rout = [kw for kw in routine_kws if kw in text_content]
    if matched_rout:
        reasons.append(f"Yêu cầu thủ tục hành chính / định dạng hồ sơ: {', '.join(matched_rout)}")
        return RFIDecision(
            priority=RFIPriority.ROUTINE,
            deadline_str="21 ngày",
            deadline_days=21.0,
            action="Gom nhóm xử lý theo đợt nghiệm thu giai đoạn (Batch review)",
            color="🔵",
            reasons=reasons,
        )

    # 6. Mặc định: NORMAL (🟢 14 ngày)
    reasons.append("Yêu cầu làm rõ kỹ thuật / đệ trình tiêu chuẩn thông thường")
    return RFIDecision(
        priority=RFIPriority.NORMAL,
        deadline_str="14 ngày",
        deadline_days=14.0,
        action="Xử lý theo quy trình phê duyệt thông thường",
        color="🟢",
        reasons=reasons,
    )


# =============================================================================
# SECTION 5: METADATA & STATUS REPORTING (PHASES A, B, C)
# =============================================================================

POLICY_METADATA = {
    "engine_name": "Structural_Policy_Engine",
    "version": "3.0.0",
    "phase": "Phase C (Full Suite)",
    "last_updated": "2026-10-17",
    "rules_count": 36,  # 2 Phase A + 15 Phase B + 18 Phase C Red Flags + 1 RFI priority
    "active_rules": [
        {
            "id": "RULE_ETA_REPAIR",
            "name": "Ngưỡng Cảnh báo Sửa chữa / Không đạt (Repair Threshold)",
            "condition": "η > 1.00",
            "action": "REPAIR",
            "source": "AGENTS.md §6; TCVN 5574:2018; TCVN 5575:2024",
            "description": "Bất kỳ phần tử hoặc hiệu ứng lực nào có η > 1.00 đều vi phạm trạng thái giới hạn, bắt buộc điều chỉnh.",
        },
        {
            "id": "RULE_ETA_VE",
            "name": "Ngưỡng Kích hoạt Value Engineering (VE Threshold)",
            "condition": "η <= 0.70",
            "action": "TRIGGER_VE",
            "source": "AGENTS.md §6; INTER_SKILL_TRIGGERS.md §POST-DESIGN-02; Cost_Estimator/SKILL.md",
            "description": "Khi kết cấu có dự trữ chịu lực > 30% (η <= 0.70) và không có phần tử nào vượt tải, tự động kích hoạt Cost_Estimator.",
        },
        *[
            {
                "id": t.trigger_id,
                "name": t.name,
                "condition": t.condition_desc,
                "action": t.action,
                "source": f"INTER_SKILL_TRIGGERS.md §{t.trigger_id}",
                "description": f"{t.source_skill} -> {t.target_skill} ({t.priority.value})",
            }
            for t in INTER_SKILL_TRIGGERS_REGISTRY.values()
        ],
        *[
            {
                "id": f.flag_id,
                "name": f.name,
                "condition": f.description,
                "action": f"{f.action.value} ({f.deadline})",
                "source": f"RED_FLAG_TRIGGERS.md §{f.flag_id}",
                "description": f.rationale,
            }
            for f in RED_FLAG_REGISTRY.values()
        ],
        {
            "id": "RULE_RFI_PRIORITY",
            "name": "Phân loại mức độ ưu tiên RFI (5 Cấp: CRITICAL/URGENT/HIGH/NORMAL/ROUTINE)",
            "condition": "Quét từ khóa & tác động tiến độ/kết cấu",
            "action": "Gán deadline (24h/3d/7d/14d/21d) & hành động",
            "source": "SKILL_RFI/SKILL.md §BƯỚC 1",
            "description": "Tự động phân loại thời hạn và biện pháp xử lý giao dịch kỹ thuật.",
        },
    ],
}


def get_policy_engine_status() -> dict:
    """Trả về trạng thái hiện tại của Policy Engine phục vụ báo cáo và sync_report."""
    return {
        "engine_name": POLICY_METADATA["engine_name"],
        "version": POLICY_METADATA["version"],
        "phase": POLICY_METADATA["phase"],
        "active_rules_count": len(POLICY_METADATA["active_rules"]),
        "triggers_count": len(INTER_SKILL_TRIGGERS_REGISTRY),
        "red_flags_count": len(RED_FLAG_REGISTRY),
        "rfi_priority_active": True,
        "active_rules": POLICY_METADATA["active_rules"],
    }
