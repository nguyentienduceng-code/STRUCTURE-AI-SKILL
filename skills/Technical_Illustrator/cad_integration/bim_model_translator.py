# -*- coding: utf-8 -*-
"""
bim_model_translator.py — P4.3 DCE Structural Model -> OpenBIM Intermediate Schema
================================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.3, §3.3.

Translates the DCE `model.json` (Engineering SSOT) into a **versioned,
schema-locked intermediate JSON** (BIM Intermediate Schema v1.0) that can be
imported directly into a pyRevit / Dynamo pipeline (or an IFC4 exporter)
without re-reading the DCE DXF.

Design goals (acceptance criterion: "chuyển đổi chính xác 100% tọa độ và
tiết diện cột/dầm/vách sang schema BIM trung gian"):
  * No re-implemented math — column centre/Revit-feet conversion reuses the
    audited `DcePlanEngine.column_revit_center` formula (RFC §6.2B).
  * Deterministic: same model -> byte-identical intermediate schema
    (sorted keys, stable ordering, `model_sha256` provenance).
  * No guessing: elements the model does not carry (walls, slabs,
    concrete_grade, rebar) emit `Data Missing: <field>` (AGENTS §4) and the
    `completeness` map, never a fabricated value.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CAD_DIR = Path(__file__).resolve().parent
_AGENTS_DIR = _CAD_DIR.parents[2]
_TOOLS_DIR = _AGENTS_DIR / "tools"
for _p in (str(_CAD_DIR), str(_TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Reuse the audited Revit column-centre formula (single source of truth).
from cad_plan_engine import DcePlanEngine  # noqa: E402

BIM_INTERMEDIATE_SCHEMA_VERSION = "1.0"
MM_PER_M = 1000.0
# Revit internal unit = foot; 1 mm = 0.0032808399 ft (6 decimals).
MM_TO_FT = DcePlanEngine.MM_TO_FT


# ---------------------------------------------------------------------------
# IFC4 / Revit family target mapping (spec §3.3.1)
# ---------------------------------------------------------------------------
_ELEMENT_TARGETS = {
    "column": {"ifc4": "IfcColumn", "revit_family": "StructuralColumnFamily"},
    "wall":   {"ifc4": "IfcWallStandardCase", "revit_family": "StructuralWallFamily"},
    "beam":   {"ifc4": "IfcBeam", "revit_family": "StructuralFramingFamily"},
    "slab":   {"ifc4": "IfcSlab", "revit_family": "SlabFamily"},
}


def _to_mm(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return round(float(v) * MM_PER_M, 2)


def _num(v: Optional[float]) -> Optional[float]:
    """Pass an already-numeric value through (mm-scale fields are NOT rescaled)."""
    return None if v is None else round(float(v), 2)


def _thickness_mm(w: Dict[str, Any]) -> Optional[float]:
    """Normalise a wall/slab thickness to mm.

    DCE models use `b_mm`/`t_mm` (mm) or `thickness_m` (metres) depending on
    authoring path — both are present in the model schema, so prefer the mm
    fields and only convert metres when no mm field is given (no guessing).
    """
    for k in ("b_mm", "t_mm"):
        if w.get(k) is not None:
            return _num(w.get(k))
    if w.get("thickness_m") is not None:
        return _to_mm(w.get("thickness_m"))
    return None


def _col_to_bim(col: Dict[str, Any], ctx: str) -> Dict[str, Any]:
    """Translate a column element to the BIM intermediate node.

    Coordinates: model centre `x/y` in metres; offsets `offset_x_mm/offset_y_mm`
    and edge fallbacks `x0/x1/y0/y1` are mm. Section `b_mm`/`h_mm` are ALREADY mm.
    """
    kind = str(col.get("kind", "RC")).upper()
    is_steel = "STEEL" in kind or "H" in kind
    elem_id = col.get("element_id")
    rec: Dict[str, Any] = {
        "bim_id": f"COL-{ctx}-{elem_id or col.get('id', col.get('mark', '?'))}",
        "element_id": elem_id,
        "floor_id": col.get("floor_id") or ctx,
        "element_type": "column",
        "ifc4_type": _ELEMENT_TARGETS["column"]["ifc4"],
        "revit_family": _ELEMENT_TARGETS["column"]["revit_family"],
        "mark": col.get("mark", col.get("id")),
        "material_kind": "steel" if is_steel else "concrete",
        "section": {"b_mm": _num(col.get("b_mm")), "h_mm": _num(col.get("h_mm"))},
        "coordinates": {},
        "rebar": {"as_provided_cm2": col.get("as_prov_cm2"),
                   "as_required_cm2": col.get("as_calc_cm2"),
                   "mu_pct": col.get("rebar_pct", col.get("mu_pct"))},
        "concrete_grade": col.get("concrete_grade"),
        "data_missing": [],
    }
    # Revit centre (mm + ft) via the audited formula.
    if "x" in col:
        rc = DcePlanEngine.column_revit_center(col)
        rec["coordinates"] = {
            "x_mm": rc["x_center_mm"], "y_mm": rc["y_center_mm"],
            "x_ft": rc["x_center_ft"], "y_ft": rc["y_center_ft"],
            "ssot_uuid": rc.get("ssot_uuid", ""),
        }
    else:
        # x0/x1/y0/y1 are column edges in mm; centre = (x0+x1)/2 when both exist.
        # Fallback to x0 alone is a known approximation — flagged Data Missing.
        if col.get("x0") is not None and col.get("x1") is not None:
            x_mm = _num((float(col["x0"]) + float(col["x1"])) / 2.0)
            y_mm = _num((float(col.get("y0", 0)) + float(col.get("y1", 0))) / 2.0)
        else:
            x_mm = _num(col.get("x0"))
            y_mm = _num(col.get("y0"))
        rec["coordinates"] = {"x_mm": x_mm, "y_mm": y_mm, "ssot_uuid": col.get("ssot_uuid", "")}
        rec["data_missing"].append("column centre coordinate (x) -> Data Missing (edge x0 fallback)")
    if col.get("b_mm") is None or col.get("h_mm") is None:
        rec["data_missing"].append("column section b_mm/h_mm -> Data Missing")
    if not is_steel and col.get("concrete_grade") is None:
        rec["data_missing"].append("column concrete_grade -> Data Missing")
    return rec


def _beam_to_bim(beam: Dict[str, Any], ctx: str) -> Dict[str, Any]:
    """Translate a beam element to the BIM intermediate node.

    Section: `size` is free-text in the model schema; only a strict `B x H`
    (or `BxH`) numeric form is parsed — anything else yields `None` +
    `Data Missing`, never a fabricated section (AGENTS §4).
    Span: uses Euclidean length when full 2D endpoints `(x0, y0, x1, y1)` are
    present (handles diagonal beams accurately), or axis difference when only
    the axis endpoints exist.
    """
    size = str(beam.get("size", "")).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)$", size)
    bw = float(m.group(1)) if m else None
    bh = float(m.group(2)) if m else None

    orient = str(beam.get("orient", "X"))
    orient_up = orient.upper()
    span: Optional[float] = None
    endpoints_missing = False
    if orient_up == "X" and beam.get("x0") is not None and beam.get("x1") is not None:
        span = _round4(abs(float(beam["x1"]) - float(beam["x0"])))
    elif orient_up == "Y" and beam.get("y0") is not None and beam.get("y1") is not None:
        span = _round4(abs(float(beam["y1"]) - float(beam["y0"])))
    elif all(beam.get(k) is not None for k in ("x0", "y0", "x1", "y1")):
        dx = float(beam["x1"]) - float(beam["x0"])
        dy = float(beam["y1"]) - float(beam["y0"])
        dz = (float(beam["z1"]) - float(beam["z0"])) if (beam.get("z0") is not None and beam.get("z1") is not None) else 0.0
        span = _round4(math.sqrt(dx * dx + dy * dy + dz * dz))
    else:
        endpoints_missing = True

    elem_id = beam.get("element_id")
    rec: Dict[str, Any] = {
        "bim_id": f"BEAM-{ctx}-{elem_id or beam.get('mark', '?')}",
        "element_id": elem_id,
        "floor_id": beam.get("floor_id") or ctx,
        "ssot_uuid": beam.get("ssot_uuid", ""),
        "element_type": "beam",
        "ifc4_type": _ELEMENT_TARGETS["beam"]["ifc4"],
        "revit_family": _ELEMENT_TARGETS["beam"]["revit_family"],
        "mark": beam.get("mark"),
        "orientation": orient,
        "span_m": span,
        "section": {"b_mm": bw, "h_mm": bh},
        "coordinates": {"x0_m": beam.get("x0"), "y0_m": beam.get("y0"),
                         "x1_m": beam.get("x1"), "y1_m": beam.get("y1")},
        "data_missing": [],
    }
    if bw is None or bh is None:
        rec["data_missing"].append(f"beam {beam.get('mark')} section '{size}' -> Data Missing")
    if endpoints_missing:
        rec["data_missing"].append(f"beam {beam.get('mark')} span endpoint ({orient} axis) -> Data Missing")
    return rec


def _wall_to_bim(wall: Dict[str, Any], ctx: str) -> Dict[str, Any]:
    t_mm = _thickness_mm(wall)
    elem_id = wall.get("element_id")
    rec: Dict[str, Any] = {
        "bim_id": f"WALL-{ctx}-{elem_id or wall.get('mark', wall.get('id', '?'))}",
        "element_id": elem_id,
        "floor_id": wall.get("floor_id") or ctx,
        "ssot_uuid": wall.get("ssot_uuid", ""),
        "element_type": "wall",
        "ifc4_type": _ELEMENT_TARGETS["wall"]["ifc4"],
        "revit_family": _ELEMENT_TARGETS["wall"]["revit_family"],
        "mark": wall.get("mark", wall.get("id")),
        "thickness_mm": t_mm,
        "length_m": _round4(wall.get("length_m")),
        "coordinates": {"x_mm": _to_mm(wall.get("x")), "y_mm": _to_mm(wall.get("y"))},
        "data_missing": [],
    }
    if t_mm is None:
        rec["data_missing"].append("wall thickness -> Data Missing")
    if wall.get("length_m") is None:
        rec["data_missing"].append("wall length_m -> Data Missing")
    return rec


def _slab_to_bim(slab: Dict[str, Any], ctx: str) -> Dict[str, Any]:
    t_mm = _thickness_mm(slab)
    elem_id = slab.get("element_id")
    rec: Dict[str, Any] = {
        "bim_id": f"SLAB-{ctx}-{elem_id or slab.get('id', slab.get('mark', '?'))}",
        "element_id": elem_id,
        "floor_id": slab.get("floor_id") or ctx,
        "ssot_uuid": slab.get("ssot_uuid", ""),
        "element_type": "slab",
        "ifc4_type": _ELEMENT_TARGETS["slab"]["ifc4"],
        "revit_family": _ELEMENT_TARGETS["slab"]["revit_family"],
        "mark": slab.get("id", slab.get("mark")),
        "thickness_mm": t_mm,
        "finished_level_m": slab.get("level_m", slab.get("finished_level_m")),
        "data_missing": [],
    }
    if t_mm is None:
        rec["data_missing"].append("slab thickness -> Data Missing")
    return rec


def _round4(v: Any) -> Optional[float]:
    return round(float(v), 4) if v is not None else None


def _dedupe_bim_id(node: Dict[str, Any], seen_counts: Dict[str, int]) -> Dict[str, Any]:
    base_id = node["bim_id"]
    count = seen_counts.get(base_id, 0) + 1
    seen_counts[base_id] = count
    if count > 1:
        node["bim_id"] = f"{base_id}#{count}"
    return node


# ---------------------------------------------------------------------------
# Main translator
# ---------------------------------------------------------------------------

def translate_model_to_bim(model: Dict[str, Any],
                           include: Optional[Tuple[str, ...]] = ("columns", "beams", "walls", "slabs"),
                           with_evidence: bool = False) -> Dict[str, Any]:
    """Translate a DCE model dict into the BIM Intermediate Schema v1.0 payload.

    `with_evidence` also embeds a `provenance` block (deterministic
    `model_sha256` + schema version + element counts + completeness map).
    """
    elements: Dict[str, Any] = {"columns": [], "beams": [], "walls": [], "slabs": []}
    completeness = {"columns": {"total": 0, "complete": 0},
                    "beams": {"total": 0, "complete": 0},
                    "walls": {"total": 0, "complete": 0},
                    "slabs": {"total": 0, "complete": 0}}
    seen_counts: Dict[str, int] = {}

    proj = model.get("project", {})
    for sh in model.get("sheets", []):
        ctx = str(sh.get("sheet_no", "?"))
        for vp in sh.get("viewports", []):
            vp_id = str(vp.get("id", "?"))
            cctx = f"{ctx}/{vp_id}"
            for col in vp.get("columns", []):
                node = _dedupe_bim_id(_col_to_bim(col, cctx), seen_counts)
                elements["columns"].append(node)
                completeness["columns"]["total"] += 1
                if not node["data_missing"]:
                    completeness["columns"]["complete"] += 1
            for bm in vp.get("beams", []):
                node = _dedupe_bim_id(_beam_to_bim(bm, cctx), seen_counts)
                elements["beams"].append(node)
                completeness["beams"]["total"] += 1
                if not node["data_missing"]:
                    completeness["beams"]["complete"] += 1
            for wl in vp.get("walls", []):
                node = _dedupe_bim_id(_wall_to_bim(wl, cctx), seen_counts)
                elements["walls"].append(node)
                completeness["walls"]["total"] += 1
                if not node["data_missing"]:
                    completeness["walls"]["complete"] += 1
            for sl in vp.get("slabs", []):
                node = _dedupe_bim_id(_slab_to_bim(sl, cctx), seen_counts)
                elements["slabs"].append(node)
                completeness["slabs"]["total"] += 1
                if not node["data_missing"]:
                    completeness["slabs"]["complete"] += 1

    selected = {k: elements[k] for k in include if k in elements} if include else elements

    payload: Dict[str, Any] = {
        "bim_intermediate_schema_version": BIM_INTERMEDIATE_SCHEMA_VERSION,
        "model_id": model.get("model_id", "UNKNOWN"),
        "model_version": model.get("model_version"),
        "project_name": proj.get("project_name", ""),
        "concrete_grade": proj.get("concrete_grade"),
        "elements": selected,
        "completeness": completeness,
    }
    if with_evidence:
        payload["provenance"] = {
            "model_sha256": _model_sha256(model),
            "generated_from": "bim_model_translator",
            "total_elements": {k: len(v) for k, v in selected.items()},
        }
    return payload


def _model_sha256(model: Dict[str, Any]) -> str:
    blob = json.dumps(model, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def export_bim_intermediate(model: Dict[str, Any], out_path: str | Path,
                           include: Optional[Tuple[str, ...]] = None,
                           with_evidence: bool = True) -> Dict[str, Any]:
    """Translate + write the intermediate schema JSON to `out_path`."""
    payload = translate_model_to_bim(model, include=include, with_evidence=with_evidence)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["output_path"] = str(p)
    return payload


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("usage: bim_model_translator.py <model.json> <out.json>")
        sys.exit(2)
    m = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    res = export_bim_intermediate(m, args[1], with_evidence=True)
    print(json.dumps({"elements": {k: len(v) for k, v in res["elements"].items()},
                      "completeness": res["completeness"]}, ensure_ascii=False, indent=2))
