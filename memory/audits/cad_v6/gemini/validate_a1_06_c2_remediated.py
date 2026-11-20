# -*- coding: utf-8 -*-
"""
validate_a1_06_c2_remediated.py
===============================
GEMINI A1-06 Validator for `.agents/memory/audits/cad_v6/claude/c2_remediated/`:
- Reopens all 5 remediated C2 A3 DXFs via ezdxf.
- Verifies sidecar SHA-256 and resolves every handle in entity_map to real DXF entities.
- Verifies KC-04 TOP/BOTTOM viewport non-overlap, actual scale, and frozen layers.
- Evaluates strict 3-way source ref linkage (Geometry + Tag + Schedule) without allowing
  metadata-only PASS.
- Runs dce_cad_compliance_checker (physical & plan profiles) honestly.
"""

from __future__ import annotations
import sys

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import ezdxf

ROOT = Path(r"g:\My Drive\Google AI Studio\.agents")
CAD_DIR = ROOT / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY_DIR = ROOT / "skills" / "SKILL_VERIFY" / "scripts"
C2_DIR = ROOT / "memory" / "audits" / "cad_v6" / "claude" / "c2_remediated"
FIXTURE_PATH = CAD_DIR / "fixtures" / "g2_steel_and_sheet_fixture.json"
OUT_JSON = ROOT / "memory" / "audits" / "cad_v6" / "gemini" / "a1_06_linkage_validation.json"

for p in (str(CAD_DIR), str(VERIFY_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from cad_element_registry import validate_dxf_entity_map_linkage
from cad_sheet_set import build_registry_from_fixture
from dce_cad_compliance_checker import audit_dxf_compliance


def _normalize_scalars(obj: Any) -> Any:
    """Convert numpy/non-JSON scalar types recursively into plain Python types."""
    if isinstance(obj, dict):
        return {str(k): _normalize_scalars(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_scalars(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    return obj


def _inspect_layout_summary(dxf_path: Path) -> Dict[str, Any]:
    """Read raw entity type counts, frame bbox, title placement, and dimstyles from DXF."""
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    ps = doc.layouts.get("Layout1")
    msp_counts = dict(Counter(e.dxftype() for e in msp))
    ps_counts = dict(Counter(e.dxftype() for e in ps)) if ps is not None else {}

    msp_titles = [
        {"handle": e.dxf.handle, "text": e.dxf.text, "layer": e.dxf.layer}
        for e in msp
        if e.dxftype() == "TEXT" and e.dxf.layer == "SHEET_TITLE"
    ]
    ps_texts = [
        {"handle": e.dxf.handle, "layer": e.dxf.layer}
        for e in (ps or [])
        if e.dxftype() in ("TEXT", "MTEXT", "INSERT")
    ]
    dimstyles = sorted({getattr(d.dxf, "dimstyle", "") for d in msp if d.dxftype() == "DIMENSION"})

    return {
        "modelspace_entity_total": len(msp),
        "modelspace_counts": msp_counts,
        "paperspace_entity_total": len(ps) if ps is not None else 0,
        "paperspace_counts": ps_counts,
        "sheet_titles_in_modelspace": msp_titles,
        "paperspace_title_or_annotation_entities": ps_texts,
        "dimension_styles": dimstyles,
    }


def main(argv: List[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--c2-dir", default=str(ROOT / "memory" / "audits" / "cad_v6" / "claude" / "c2_remediated_v2"))
    parser.add_argument("--out-json", default=str(ROOT / "memory" / "audits" / "cad_v6" / "gemini" / "a1_06_linkage_validation_v2.json"))
    args = parser.parse_args(argv)

    target_dir = Path(args.c2_dir)
    out_json = Path(args.out_json)

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    manifest_path = target_dir / "sheet_set_manifest.json"
    c2_audit_path = target_dir / "C2_sheet_set_audit.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    c2_audit = json.loads(c2_audit_path.read_text(encoding="utf-8"))
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    c2_registry = build_registry_from_fixture(fixture)
    sheets_out: Dict[str, Any] = {}
    sheet_nos = [s["sheet_no"] for s in manifest["sheets"]]

    for sno in sheet_nos:
        dxf_path = target_dir / f"{sno}_C2_A3.dxf"
        layout_summary = _inspect_layout_summary(dxf_path)
        linkage_fixture = validate_dxf_entity_map_linkage(dxf_path, fixture_data=fixture)
        linkage_registry = validate_dxf_entity_map_linkage(dxf_path, registry=c2_registry, fixture_data=fixture)
        comp_phys = audit_dxf_compliance(str(dxf_path), profile="physical")
        comp_plan = audit_dxf_compliance(str(dxf_path), profile="plan")

        sheets_out[sno] = {
            "dxf_path": str(dxf_path),
            "layout_summary": layout_summary,
            "linkage_against_fixture": linkage_fixture,
            "linkage_against_c2_registry": linkage_registry,
            "compliance_physical": {
                "status": comp_phys["status"],
                "issues": comp_phys["issues"],
                "dimensions": comp_phys["dimensions"],
                "non_dce_layers": comp_phys["non_dce_layers"],
            },
            "compliance_plan": {
                "status": comp_plan["status"],
                "physical_status": comp_plan["physical_status"],
                "gate_status": comp_plan["gate_status"],
                "gates_passed": comp_plan["gates_passed"],
                "gates_unverified": comp_plan["gates_unverified"],
                "metadata_issues": comp_plan["metadata_issues"],
                "issues_count": len(comp_plan["issues"]),
            },
        }

    kc04_vp = sheets_out["KC-04"]["linkage_against_fixture"]["viewport_inspection"]
    checks = {
        "manifest_sha256_match": manifest_sha256 == c2_audit.get("artifact_sha256"),
        "all_5_sidecar_sha256_match": all(
            s["linkage_against_fixture"]["dxf_sha256_match"] for s in sheets_out.values()
        ),
        "all_5_recorded_handles_resolved": all(
            s["linkage_against_fixture"]["recorded_handles_resolved_ok"] for s in sheets_out.values()
        ),
        "all_5_viewports_nonoverlap": all(
            s["linkage_against_fixture"]["viewport_inspection"]["viewport_nonoverlap_ok"]
            for s in sheets_out.values()
        ),
        "kc04_dual_viewport_frozen_layers_disjoint": bool(kc04_vp["disjoint_visible_rebar_ok"]),
        "all_5_strict_3way_physical_linkage": all(
            s["linkage_against_fixture"]["strict_3way_physical_linkage_ok"] for s in sheets_out.values()
        ),
        "all_5_compliance_physical_pass": all(
            s["compliance_physical"]["status"] == "PASS" for s in sheets_out.values()
        ),
        "all_5_compliance_plan_pass": all(
            s["compliance_plan"]["status"] == "PASS" for s in sheets_out.values()
        ),
    }

    overall_status = (
        "PASS"
        if all(checks.values())
        else "PARTIAL_HANDLES_RESOLVED_STRICT_LINKAGE_NEEDS_REMEDIATION"
    )

    payload = _normalize_scalars({
        "Standard_Method": "DCE A1-06 Independent Linkage Validation Script v6",
        "c2_remediated_dir": str(target_dir),
        "source_fixture": str(FIXTURE_PATH),
        "manifest_sha256": manifest_sha256,
        "c2_audit_artifact_sha256": c2_audit.get("artifact_sha256"),
        "overall_status": overall_status,
        "checks": checks,
        "sheets": sheets_out,
        "Calculation_Logs": [{"step": k, "passed": v} for k, v in checks.items()],
    })

    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"overall_status = {overall_status}")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    print(f"Wrote: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
