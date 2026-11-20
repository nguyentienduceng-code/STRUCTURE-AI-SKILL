# -*- coding: utf-8 -*-
"""
revit_family_parameter_mapper.py — P4.3 Column/Beam/Wall Revit Parameter Sync
============================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.3, §3.3.2.

Maps a BIM Intermediate Schema node (from `bim_model_translator`) to a
flat, import-ready **Revit family parameter dict** suitable for a pyRevit
`FamilyDocument` workflow or a Dynamo `Dictionary` input.

Design goals:
  * Deterministic: same node -> same parameter dict.
  * No re-computation — only unit normalisation of already-translated values
    (mm -> m when needed; feet are kept for Revit internal coordinates).
  * Missing data is surfaced as `None` + a `_data_missing` list, never a guess.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CAD_DIR = Path(__file__).resolve().parent
for _p in (str(_CAD_DIR),):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Per-element parameter maps
# ---------------------------------------------------------------------------

def map_column_params(node: Dict[str, Any]) -> Dict[str, Any]:
    """Map a column BIM node to Structural Column family parameters."""
    sec = node.get("section", {})
    rebar = node.get("rebar", {})
    coords = node.get("coordinates", {})
    p: Dict[str, Any] = {
        "ParameterType": "StructuralColumn",
        "FamilyName": node.get("revit_family"),
        "ElementType": "IfcColumn" if node.get("ifc4_type") == "IfcColumn" else "IfcColumn",
        "Mark": node.get("mark"),
        "MaterialKind": node.get("material_kind", "concrete"),
        "ConcreteGrade": node.get("concrete_grade"),  # None => Data Missing
        # Section
        "Column_B": sec.get("b_mm"),
        "Column_H": sec.get("h_mm"),
        # Revit internal coordinates (feet) + engineering mm
        "X_Centre_ft": coords.get("x_ft"),
        "Y_Centre_ft": coords.get("y_ft"),
        "X_Centre_mm": coords.get("x_mm"),
        "Y_Centre_mm": coords.get("y_mm"),
        # Rebar
        "As_Provided_cm2": rebar.get("as_provided_cm2"),
        "As_Required_cm2": rebar.get("as_required_cm2"),
        "Mu_Pct": rebar.get("mu_pct"),
        "SSOT_UUID": coords.get("ssot_uuid", ""),
    }
    p["_data_missing"] = list(node.get("data_missing", []))
    return p


def map_beam_params(node: Dict[str, Any]) -> Dict[str, Any]:
    sec = node.get("section", {})
    coords = node.get("coordinates", {})
    p: Dict[str, Any] = {
        "ParameterType": "StructuralBeam",
        "FamilyName": node.get("revit_family"),
        "ElementType": "IfcBeam",
        "Mark": node.get("mark"),
        "Orientation": node.get("orientation", "X"),
        "Span_m": node.get("span_m"),
        "Beam_B": sec.get("b_mm"),
        "Beam_H": sec.get("h_mm"),
        # Start/end coordinates in metres
        "X0_m": coords.get("x0_m"),
        "Y0_m": coords.get("y0_m"),
        "X1_m": coords.get("x1_m"),
        "Y1_m": coords.get("y1_m"),
    }
    p["_data_missing"] = list(node.get("data_missing", []))
    return p


def map_wall_params(node: Dict[str, Any]) -> Dict[str, Any]:
    coords = node.get("coordinates", {})
    p: Dict[str, Any] = {
        "ParameterType": "StructuralWall",
        "FamilyName": node.get("revit_family"),
        "ElementType": "IfcWallStandardCase",
        "Mark": node.get("mark"),
        "Wall_Thickness_mm": node.get("thickness_mm"),
        "Wall_Length_m": node.get("length_m"),
        # _wall_to_bim emits x_mm/y_mm (metres converted via _to_mm).
        "X_mm": coords.get("x_mm"),
        "Y_mm": coords.get("y_mm"),
    }
    p["_data_missing"] = list(node.get("data_missing", []))
    return p


def map_slab_params(node: Dict[str, Any]) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "ParameterType": "Slab",
        "FamilyName": node.get("revit_family"),
        "ElementType": "IfcSlab",
        "Mark": node.get("mark"),
        "Slab_Thickness_mm": node.get("thickness_mm"),
        "Finished_Level_m": node.get("finished_level_m"),
    }
    p["_data_missing"] = list(node.get("data_missing", []))
    return p


_MAPS = {
    "column": map_column_params,
    "beam": map_beam_params,
    "wall": map_wall_params,
    "slab": map_slab_params,
}


def map_elements_to_revit(bim_payload: Dict[str, Any],
                         family: str = "StructuralColumnFamily") -> Dict[str, List[Dict[str, Any]]]:
    """Map every element of a BIM intermediate payload to a flat parameter list.

    `family` is a soft filter; it is recorded on each parameter dict but does
    not drop other element types (importers need all families).
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    for kind in ("columns", "beams", "walls", "slabs"):
        nodes = bim_payload.get("elements", {}).get(kind, [])
        mapped = []
        for node in nodes:
            fn = _MAPS.get(node.get("element_type", ""), map_column_params)
            rec = fn(node)
            rec["TargetFamily"] = family
            mapped.append(rec)
        out[kind] = mapped
    return out


__all__ = [
    "map_column_params", "map_beam_params", "map_wall_params", "map_slab_params",
    "map_elements_to_revit",
]

if __name__ == "__main__":
    import json
    p = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    res = map_elements_to_revit(p)
    print(json.dumps({k: len(v) for k, v in res.items()}, indent=2))
