# -*- coding: utf-8 -*-
"""
rfi_ncr_bridge.py — P4.2 Round-Trip RFI/NCR Report Engine (Step 1: findings)
===========================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.2, §3.2.

Bridges the **Bộ lọc 8** (`dce_cad_compliance_checker.audit_dxf_compliance`, 20 cổng
`G8.01..G8.20`) to **legal findings** per the Vietnamese construction-contract
regime (Nghị định 175/2024/NĐ-CP, Thông tư 34/2026/TT-BXD, FIDIC White Book) and
emits machine-checkable NCR / RFI records.

Severity -> document routing (spec §3.2.1):
  * Structural-safety / geometry-integrity gate FAIL  ->  **NCR** (Biên bản NCR, CRITICAL|MAJOR)
  * Cosmetic / drafting-quality gate FAIL             ->  **RFI** (Phiếu RFI, MINOR)

The NCR records produced here conform to `.agents/_SHARED/data/ncr_schema.json`
(11 required fields) and pass `project_ops_manager.validate_ncr_dict`.
No file is written in this module — it only *classifies* and *records*.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_AGENTS = Path(__file__).resolve().parents[1]  # .agents/ (this file is in .agents/tools/)
_TOOLS = _AGENTS / "tools"
_VERIFY = _AGENTS / "skills" / "SKILL_VERIFY" / "scripts"
for _p in (str(_TOOLS), str(_VERIFY)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dce_cad_compliance_checker import audit_dxf_compliance  # noqa: E402
import project_ops_manager as pom  # noqa: E402

SOURCE_TAG = "FILTER8_AUTOMATED_AUDIT"


# ---------------------------------------------------------------------------
# Gate taxonomy — which doc type + severity + legal basis each Filter-8 gate maps to
# ---------------------------------------------------------------------------
# "NCR"  => structural / geometry integrity defect  (Biên bản NCR)
# "RFI"  => cosmetic / drafting-quality defect        (Phiếu RFI)
_GATE_TAXONOMY: Dict[str, Dict[str, str]] = {
    # -- structural / integrity -> NCR --
    "G8.01": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d AGENTS.md; TT 34/2026/TT-BXD (chất lượng hồ sơ).",
              "fix": "DXF không đạt chuẩn AC1021 / thiếu bằng chứng. Xuất lại bản vẽ qua engine chuẩn."},
    "G8.04": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (khung 4 tầng biên).",
              "fix": "Bong bóng trục cắt xuyên nét. Tái bố trí trục theo 4-Tier Exterior Dimension."},
    "G8.05": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (khóa Solid Hatch cột).",
              "fix": "Cột thiếu block tham số / Solid Hatch. Nạp lại DCE_Cot_Block chuẩn."},
    "G8.06": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (kích thước định vị).",
              "fix": "Dim định vị lệch số đo thực. Sửa chuỗi Linear Dimension DCE_DIM_COT."},
    "G8.07": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (khóa ATTSYNC).",
              "fix": "ATTDEF lệch 700mm. Chuẩn hóa insert (0,±1) cho DCE_TenCauKien."},
    "G8.10": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (4-Tier Exterior Hierarchy).",
              "fix": "Thứ tự tầng kích thước đảo. Sắp xếp Mép->T1->T2->Bong bóng."},
    "G8.11": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (khung bản vẽ).",
              "fix": "Mặt bằng / Bảng thống kê tràn khung trong. Co viewport, dịch bảng."},
    "G8.13": {"doc": "NCR", "sev": "CRITICAL", "basis": "TCVN 5574:2018 (thép gối, đai tới hạn).",
              "fix": "Dầm thiếu thép gối/vùng đai 2*hb. Bổ thép theo SKILLKC."},
    "G8.14": {"doc": "NCR", "sev": "CRITICAL", "basis": "TCVN 5574:2018 (1%<=mu<=4%).",
              "fix": "Mặt cắt cột As_prov<As_calc / mu ngoài dải. Tăng thép dọc."},
    "G8.15": {"doc": "NCR", "sev": "CRITICAL", "basis": "TCVN 9386:2025 (vùng biên B.E.).",
              "fix": "Vách thiếu vùng biên B.E. l_be. Bổ đai kín + cốt thép biên."},
    "G8.17": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (đồng bộ tỷ lệ).",
              "fix": "Tỷ lệ S* lệch khung A1/A0. Kéo DimStyle Dce_{S}MV đúng khung."},
    "G8.18": {"doc": "NCR", "sev": "CRITICAL", "basis": "Điều 12d (vùng cấm Sidebar/TitleBlock).",
              "fix": "Trục/bong bóng xâm phạm khung tên & bảng. Dịch hệ trục ra ngoài vùng cấm."},
    # -- cosmetic / drafting-quality -> RFI --
    "G8.02": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (ma trận layer).", "fix": "Bổ layer chuẩn DCE còn thiếu."},
    "G8.03": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (DimStyle phân cấp).", "fix": "Khôi phục cặp DimStyle main/cot."},
    "G8.08": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (khóa phạm vi).", "fix": "Đảm bảo nhãn đúng mặt bằng, dầm cắt mép cột."},
    "G8.09": {"doc": "RFI", "sev": "MAJOR", "basis": "TCVN 9386:2025 (vách B.E., dầm nối lõi).", "fix": "Bổ DCE_Boundary_Zone / DCE_CouplingBeam khi có vách kháng chấn."},
    "G8.12": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (chống đè chữ).", "fix": "Đưa nhãn ra vùng thoáng, không đè lõi/MEP."},
    "G8.16": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (bảng thống kê thép).", "fix": "Đối soát BBS d²/162.2, tổng tấn khớp."},
    "G8.19": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12e (cỡ chữ bảng).", "fix": "Tăng Adaptive Column Widths cho bảng thống kê."},
    "G8.20": {"doc": "RFI", "sev": "MAJOR", "basis": "Điều 12d (hướng nhãn dầm).", "fix": "Xoay 90° nhãn dầm dọc, đủ mã 370 Lineweight."},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _ncr_seq_id(date8: str, seq: int) -> str:
    """NCR id per `ncr_schema.json` (SSOT): pattern `^NCR-[0-9]{3,}$` ->
    `NCR-{YYYYMMDD}{NNN}` (pure digits after the prefix)."""
    return f"NCR-{date8}{seq:03d}"


def classify_findings(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a Filter-8 `audit_dxf_compliance` result into legal findings.

    A "finding" = a failed / unverified gate that routes to an NCR or RFI document.
    PASS / NOT_APPLICABLE / UNVERIFIED gates are NOT findings (they carry no defect).
    Only concrete FAILs become findings; a fully-PASS audit yields [].
    """
    findings: List[Dict[str, Any]] = []
    for g in audit.get("gate_results", []):
        if not g.get("applicable", True):
            continue
        passed = g.get("passed")
        if passed is True:
            continue
        gid = g.get("gate_id", "")
        tax = _GATE_TAXONOMY.get(gid, {"doc": "RFI", "sev": "MAJOR",
                                       "basis": "TT 34/2026/TT-BXD (mặc định).", "fix": "Kiểm tra thủ công."})
        if passed is None:
            # UNVERIFIED => open question, not a confirmed defect -> always RFI (MINOR).
            doc_type, sev = "RFI", "MINOR"
            note = "Chưa kiểm chứng được bằng chứng (UNVERIFIED) — cần RFI."
        else:
            doc_type, sev = tax["doc"], tax["sev"]
            note = g.get("detail", "")
        findings.append({
            "gate_id": gid,
            "gate_name": g.get("gate_name", ""),
            "doc_type": doc_type,
            "severity": sev,
            "status": "FAIL" if passed is False else "UNVERIFIED",
            "detail": note,
            "rework": tax["fix"],
            "legal_basis": tax["basis"],
        })
    return findings


def build_ncr_records(findings: List[Dict[str, Any]],
                      model_id: str,
                      from_version: int,
                      to_version: int) -> List[Dict[str, Any]]:
    """Emit schema-valid NCR dicts for NCR-routed findings (validated by pom.validate_ncr_dict)."""
    date8 = _now_iso()[:10].replace("-", "")
    out: List[Dict[str, Any]] = []
    for i, f in enumerate([x for x in findings if x["doc_type"] == "NCR"], start=1):
        ncr = {
            "ncr_id": _ncr_seq_id(date8, i),
            "model_id": model_id,
            "from_model_version": int(from_version),
            "to_model_version": int(to_version),
            "element_id": f["gate_id"],
            "field": f["gate_name"],
            "old_value": "as_is",
            "new_value": "REWORK_REQUIRED",
            "reason": f"{f['detail']} | {f['rework']}",
            "source": SOURCE_TAG,
            "severity": "CRITICAL" if f["severity"] == "CRITICAL" else "MAJOR",
            "status": "REJECTED",
            "created_at": _now_iso(),
        }
        out.append(pom.validate_ncr_dict(ncr))
    return out


def build_rfi_records(findings: List[Dict[str, Any]], model_id: str) -> List[Dict[str, Any]]:
    """Emit RFI sheets (phiếu) for RFI-routed findings. Not NCR-schema; a lighter RFI record."""
    out: List[Dict[str, Any]] = []
    for i, f in enumerate([x for x in findings if x["doc_type"] == "RFI"], start=1):
        out.append({
            "rfi_id": f"RFI-DES-{_now_iso()[:10].replace('-', '')}-{i:03d}",
            "model_id": model_id,
            "gate_id": f["gate_id"],
            "gate_name": f["gate_name"],
            "severity": f["severity"],
            "question": f["detail"],
            "requested_action": f["rework"],
            "legal_basis": f["legal_basis"],
            "created_at": _now_iso(),
        })
    return out


def generate_from_audit(dxf_path: str,
                        model_id: str = "UNKNOWN",
                        from_version: int = 1,
                        to_version: Optional[int] = None,
                        profile: str = "full") -> Dict[str, Any]:
    """One-shot: run Filter-8 on a DXF, then classify into NCR + RFI records.

    `to_version` defaults to `from_version + 1` — the NCR schema requires
    `to_model_version >= 2` (an NCR is by definition a change into a newer model).
    """
    if to_version is None:
        to_version = int(from_version) + 1
    audit = audit_dxf_compliance(dxf_path, profile=profile)
    findings = classify_findings(audit)
    ncrs = build_ncr_records(findings, model_id, from_version, to_version)
    rfis = build_rfi_records(findings, model_id)
    return {
        "dxf_path": dxf_path,
        "audit_status": audit.get("status"),
        "full_compliance_verified": bool(audit.get("full_compliance_verified")),
        "gates_failed": audit.get("gates_failed", 0),
        "gates_unverified": audit.get("gates_unverified", 0),
        "findings": findings,
        "nrcs": ncrs,
        "rfis": rfis,
        "ncr_count": len(ncrs),
        "rfi_count": len(rfis),
    }


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else ""
    if not p:
        print("usage: rfi_ncr_bridge.py <dxf> [model_id]")
        sys.exit(2)
    res = generate_from_audit(p, model_id=sys.argv[2] if len(sys.argv) > 2 else "CLI")
    print(json.dumps({k: res[k] for k in ("audit_status", "ncr_count", "rfi_count", "gates_failed")},
                     ensure_ascii=False, indent=2))
