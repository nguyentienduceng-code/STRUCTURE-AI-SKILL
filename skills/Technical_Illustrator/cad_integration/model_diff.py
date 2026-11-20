# -*- coding: utf-8 -*-
"""
model_diff.py — Schema-Gated CAD-to-Model Diff Extractor & Merger (P1 Hybrid Authoring)
========================================================================================

Implements Schema-Gate Authoring (D1 + P1 Spec from `CLAUDE_P0OPS_REVIEW_AND_P1_SPEC.md`):
  - `extract_form_diff(user_form_dxf, baseline_form_dxf, model=None, form_id=...)`
      Detects semantic edits made by engineers in AutoCAD across 4 domains:
        1) `layer_changes` (color, linetype, lineweight vs SSOT whitelist)
        2) `titleblock_changes` (`DCE_TITLEBLOCK_*` ATTRIB -> model `project.*` paths)
        3) `zone_changes` (`DCE_ZONE_*` WCS bbox shift/resize)
        4) `axes_changes` (`Dce_KhTenTruc` / `Dce_TenTruc` / `DCE_Truc` -> `project.grid_x/grid_y`)
  - `apply_form_diff_to_model(model, form_diff, validate_fn=None)`
      Applies mapped patches onto a candidate copy, bumps `model_version + 1`,
      and enforces canonical `model_schema.json` validation BEFORE any commit
      (raising `DiffValidationError` with code `E005_INVALID_DIFF` or
      `E006_SCHEMA_GATE_REJECTED` on failure; never mutating `model` in place).
"""

from __future__ import annotations

import copy
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf

CAD_DIR = Path(__file__).resolve().parent
AGENTS_DIR = CAD_DIR.parents[2]
SHARED_CTX_DIR = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
TOOLS_DIR = AGENTS_DIR / "tools"

for _p in (str(CAD_DIR), str(SHARED_CTX_DIR), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cad_form_contract import (
    DEFAULT_ALLOWLIST_TITLE_TAGS,
    FORM_CATALOG,
    validate_open_form,
)
from cad_layer_standard import get_standard_layer_whitelist


class DiffValidationError(ValueError):
    """Structured P1 error (`E005_INVALID_DIFF` / `E006_SCHEMA_GATE_REJECTED`)."""

    def __init__(self, code: str, message: str, diff_details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.diff_details = diff_details or {}


_TITLE_TAG_TO_MODEL_FIELD: Dict[str, Tuple[str, float]] = {
    "TEN_CONG_TRINH": ("project.project_name", 0.98),
    "CHU_DAU_TU": ("project.investor", 0.95),
    "CONG_TY": ("project.company", 0.95),
    "HANG_MUC": ("project.drawing_category", 0.92),
    "BUOC_TK": ("project.design_stage", 0.95),
    "NAM": ("project.year", 0.95),
    "TY_LE": ("project.scale", 0.95),
}


def _parse_scale_ratio(raw: str) -> float:
    s = str(raw or "").strip()
    m = re.match(r"^(?:TL\s*:?\s*)?1\s*[:/]\s*([0-9]+(?:\.[0-9]+)?)$", s, flags=re.IGNORECASE)
    if m:
        val = float(m.group(1))
    else:
        val = float(s)
    if not math.isfinite(val) or val <= 0.0:
        raise ValueError(f"Invalid positive scale ratio: {raw!r}")
    return val


def _extract_titleblock_attribs(doc: ezdxf.document.Drawing, tb_name: Optional[str]) -> Dict[str, str]:
    msp = doc.modelspace()
    out: Dict[str, str] = {}
    for ent in msp:
        if ent.dxftype() == "INSERT":
            bname = str(getattr(ent.dxf, "name", ""))
            if (tb_name and bname == tb_name) or bname.upper().startswith("DCE_TITLEBLOCK"):
                for att in getattr(ent, "attribs", []):
                    out[str(att.dxf.tag)] = str(att.dxf.text)
                break
    return out


def _extract_layers_snapshot(doc: ezdxf.document.Drawing) -> Dict[str, Dict[str, Any]]:
    snap: Dict[str, Dict[str, Any]] = {}
    for ly in doc.layers:
        snap[str(ly.dxf.name)] = {
            "color": int(getattr(ly.dxf, "color", 7)),
            "linetype": str(getattr(ly.dxf, "linetype", "Continuous")),
            "lineweight": int(getattr(ly.dxf, "lineweight", -3)),
        }
    return snap


def _extract_axis_bubbles_coords(
    doc: ezdxf.document.Drawing,
) -> Tuple[List[Tuple[str, float, float]], List[Tuple[str, float, float]]]:
    """Return unique (label, cx_mm, cy_mm) sorted for X-grid lines and Y-grid lines."""
    msp = doc.modelspace()
    axis_bubbles: List[Tuple[str, float, float, float]] = []
    for ent in msp:
        if ent.dxftype() != "INSERT":
            continue
        bname = str(getattr(ent.dxf, "name", "")).lower()
        if bname not in ("dce_khtentruc", "dce_tentruc", "dce_truc_bubble"):
            continue
        label = ""
        for att in getattr(ent, "attribs", []):
            if str(att.dxf.tag).upper() == "TRUC":
                label = str(att.dxf.text).strip()
                break
        if not label:
            continue
        ins = ent.dxf.insert
        rot = float(getattr(ent.dxf, "rotation", 0.0) or 0.0) % 360.0
        scale = float(getattr(ent.dxf, "xscale", 100.0) or 100.0)
        # Dce_KhTenTruc circle center is at local (0, -3.5 * scale) rotated by rot
        r = math.radians(rot)
        cx = float(ins.x) - math.sin(r) * (-3.5 * scale)
        cy = float(ins.y) + math.cos(r) * (-3.5 * scale)
        axis_bubbles.append((label, round(cx, 2), round(cy, 2), rot))

    # Group vertical grid bubbles (rot near 0 or 180 -> represent X axes) vs horizontal (rot near 90 or 270 -> Y axes)
    x_axes: Dict[str, List[float]] = {}
    y_axes: Dict[str, List[float]] = {}
    for label, cx, cy, rot in axis_bubbles:
        if abs(rot - 90.0) < 20.0 or abs(rot - 270.0) < 20.0:
            y_axes.setdefault(label, []).append(cy)
        else:
            x_axes.setdefault(label, []).append(cx)

    x_list = sorted([(lbl, sum(vals) / len(vals), 0.0) for lbl, vals in x_axes.items()], key=lambda item: item[1])
    y_list = sorted([(lbl, 0.0, sum(vals) / len(vals)) for lbl, vals in y_axes.items()], key=lambda item: item[2])
    return x_list, y_list


def _model_plan_origin_mm(model: Optional[Dict[str, Any]]) -> Optional[Tuple[float, float]]:
    """Plan origin (mm) of the model, resolved from the first sheet/viewport that carries one.

    All sheets of a project share the same plan origin, but `origin_mm` can be
    absent on some viewports (added later / upper floors). Hardcoding
    `sheets[0].viewports[0]` mis-resolves the origin when the diffed form is a
    later sheet whose first viewport has no `origin_mm` — so scan in order and
    take the first that declares one (AGENTS §4: no guess, just a robust lookup).
    """
    if not model:
        return None
    for sh in model.get("sheets", []):
        for vp in sh.get("viewports", []):
            o = vp.get("origin_mm")
            if o:
                try:
                    return (float(o[0]), float(o[1]))
                except (IndexError, TypeError, ValueError):
                    continue
    return None


def extract_form_diff(
    user_form_dxf: str | Path,
    baseline_form_dxf: str | Path,
    model: Optional[Dict[str, Any]] = None,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
) -> Dict[str, Any]:
    """Extract semantic diffs from a user-edited DXF vs baseline Form/SSOT and map to model paths."""
    up = Path(user_form_dxf)
    bp = Path(baseline_form_dxf)
    if not up.is_file():
        raise DiffValidationError("E005_INVALID_DIFF", f"User form DXF not found: {up}")
    if not bp.is_file():
        raise DiffValidationError("E005_INVALID_DIFF", f"Baseline form DXF not found: {bp}")

    u_val = validate_open_form(up, form_id=form_id, tier="user")
    if not u_val.valid:
        raise DiffValidationError(
            "E005_INVALID_DIFF",
            f"User form DXF violates Open Form contract: {u_val.errors}",
            {"validation_errors": u_val.errors},
        )
    b_val = validate_open_form(bp, form_id=form_id, tier="baseline")

    user_doc = ezdxf.readfile(str(up))
    base_doc = ezdxf.readfile(str(bp))

    # 1. Layer diffs
    whitelist = get_standard_layer_whitelist()
    u_layers = _extract_layers_snapshot(user_doc)
    b_layers = _extract_layers_snapshot(base_doc)
    layer_changes: List[Dict[str, Any]] = []
    for lname, uspec in sorted(u_layers.items()):
        if lname not in b_layers:
            layer_changes.append({
                "layer": lname,
                "kind": "added",
                "whitelist_ok": lname.lower() in whitelist,
                "after": uspec,
                "confidence": 1.0,
            })
        elif uspec != b_layers[lname]:
            diffs = {k: (b_layers[lname][k], uspec[k]) for k in ("color", "linetype", "lineweight") if uspec[k] != b_layers[lname][k]}
            if diffs:
                layer_changes.append({
                    "layer": lname,
                    "kind": "modified",
                    "whitelist_ok": lname.lower() in whitelist,
                    "before": b_layers[lname],
                    "after": uspec,
                    "changed_fields": diffs,
                    "confidence": 1.0,
                })

    # 2. Zone diffs
    zone_changes: List[Dict[str, Any]] = []
    for zkey, u_boxes in u_val.zones_wcs.items():
        b_boxes = b_val.zones_wcs.get(zkey, [])
        if not b_boxes:
            zone_changes.append({"zone": zkey, "kind": "added", "new_bbox": list(u_boxes[0]), "confidence": 1.0})
            continue
        ub = u_boxes[0]
        bb = b_boxes[0]
        if any(abs(ub[i] - bb[i]) > 1e-2 for i in range(4)):
            ucx, ucy = (ub[0] + ub[2]) / 2.0, (ub[1] + ub[3]) / 2.0
            bcx, bcy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
            zone_changes.append({
                "zone": zkey,
                "kind": "modified",
                "old_bbox": list(bb),
                "new_bbox": list(ub),
                "delta_center_mm": [round(ucx - bcx, 2), round(ucy - bcy, 2)],
                "delta_size_mm": [round((ub[2] - ub[0]) - (bb[2] - bb[0]), 2), round((ub[3] - ub[1]) - (bb[3] - bb[1]), 2)],
                "confidence": 1.0,
            })

    # 3. TitleBlock ATTRIB diffs -> Model field mappings
    tb_block = u_val.titleblock_block or FORM_CATALOG.get(form_id, {}).get("titleblock_block")
    u_tb = _extract_titleblock_attribs(user_doc, tb_block)
    b_tb = _extract_titleblock_attribs(base_doc, tb_block)
    titleblock_changes: List[Dict[str, Any]] = []
    model_patches: List[Dict[str, Any]] = []
    allow = set(DEFAULT_ALLOWLIST_TITLE_TAGS) | {"CHU_TRI"}

    for tag, u_text in sorted(u_tb.items()):
        b_text = b_tb.get(tag, "")
        if u_text == b_text:
            continue
        mapped_path, conf = _TITLE_TAG_TO_MODEL_FIELD.get(tag, ("", 0.0))
        entry: Dict[str, Any] = {
            "tag": tag,
            "before": b_text,
            "after": u_text,
            "allowlisted": tag in allow,
            "model_field": mapped_path or None,
            "confidence": conf if mapped_path else 0.5,
        }
        titleblock_changes.append(entry)
        if mapped_path and model is not None:
            parsed_val: Any = u_text
            if mapped_path == "project.scale":
                try:
                    parsed_val = _parse_scale_ratio(u_text)
                except ValueError as ex:
                    raise DiffValidationError(
                        "E005_INVALID_DIFF",
                        f"TitleBlock TY_LE value invalid: {ex}",
                        {"tag": tag, "value": u_text},
                    ) from ex
            model_patches.append({
                "path": mapped_path,
                "value": parsed_val,
                "source_tag": tag,
                "confidence": conf,
            })

    # 4. Axes diffs (when Dce_KhTenTruc grid bubbles exist in user DXF & model is provided)
    axes_changes: List[Dict[str, Any]] = []
    u_x_bubbles, u_y_bubbles = _extract_axis_bubbles_coords(user_doc)
    b_x_bubbles, b_y_bubbles = _extract_axis_bubbles_coords(base_doc)

    if model is not None and u_x_bubbles:
        proj_grid_x = list(model.get("project", {}).get("grid_x", []))
        base_map_x = {lbl: cx for lbl, cx, _ in b_x_bubbles}
        _origin_mm = _model_plan_origin_mm(model)
        origin_x_mm = _origin_mm[0] if _origin_mm else None

        u_map_x = {lbl: cx for lbl, cx, _ in u_x_bubbles}
        for idx, gx_pair in enumerate(proj_grid_x):
            lbl = str(gx_pair[0])
            old_m = float(gx_pair[1])
            if lbl not in u_map_x:
                continue
            if lbl in base_map_x:
                delta_m = round((u_map_x[lbl] - base_map_x[lbl]) / 1000.0, 4)
                new_m = round(old_m + delta_m, 4)
            elif origin_x_mm is not None:
                new_m = round((u_map_x[lbl] - origin_x_mm) / 1000.0, 4)
            else:
                continue
            if abs(new_m - old_m) > 1e-4:
                axes_changes.append({
                    "axis_dir": "X",
                    "axis_label": lbl,
                    "grid_index": idx,
                    "old_m": old_m,
                    "new_m": new_m,
                    "model_field": f"project.grid_x[{idx}][1]",
                    "confidence": 0.92,
                })
                model_patches.append({
                    "path": f"project.grid_x[{idx}][1]",
                    "value": new_m,
                    "axis_label": lbl,
                    "confidence": 0.92,
                })

    if model is not None and u_y_bubbles:
        proj_grid_y = list(model.get("project", {}).get("grid_y", []))
        base_map_y = {lbl: cy for lbl, _, cy in b_y_bubbles}
        _origin_mm = _model_plan_origin_mm(model)
        origin_y_mm = _origin_mm[1] if _origin_mm else None
        u_map_y = {lbl: cy for lbl, _, cy in u_y_bubbles}
        for idx, gy_pair in enumerate(proj_grid_y):
            lbl = str(gy_pair[0])
            old_m = float(gy_pair[1])
            if lbl not in u_map_y:
                continue
            if lbl in base_map_y:
                delta_m = round((u_map_y[lbl] - base_map_y[lbl]) / 1000.0, 4)
                new_m = round(old_m + delta_m, 4)
            elif origin_y_mm is not None:
                new_m = round((u_map_y[lbl] - origin_y_mm) / 1000.0, 4)
            else:
                continue
            if abs(new_m - old_m) > 1e-4:
                axes_changes.append({
                    "axis_dir": "Y",
                    "axis_label": lbl,
                    "grid_index": idx,
                    "old_m": old_m,
                    "new_m": new_m,
                    "model_field": f"project.grid_y[{idx}][1]",
                    "confidence": 0.92,
                })
                model_patches.append({
                    "path": f"project.grid_y[{idx}][1]",
                    "value": new_m,
                    "axis_label": lbl,
                    "confidence": 0.92,
                })

    total_changes = len(layer_changes) + len(zone_changes) + len(titleblock_changes) + len(axes_changes)
    return {
        "status": "OK",
        "form_id": form_id,
        "user_form_dxf": str(up),
        "baseline_form_dxf": str(bp),
        "user_form_sha256": u_val.inventory.get("dxf_sha256", ""),
        "change_count": total_changes,
        "layer_changes": layer_changes,
        "zone_changes": zone_changes,
        "titleblock_changes": titleblock_changes,
        "axes_changes": axes_changes,
        "model_patches": model_patches,
        "warnings": u_val.warnings,
    }


def _set_model_path(obj: Dict[str, Any], path_expr: str, value: Any) -> None:
    """Apply path expression like `project.grid_x[1][1]` or `project.project_name` safely."""
    tokens: List[Any] = []
    for part in path_expr.split("."):
        m = re.match(r"^([A-Za-z0-9_]+)((?:\[\d+\])*)$", part)
        if not m:
            raise DiffValidationError("E005_INVALID_DIFF", f"Unsupported model field path: {path_expr!r}")
        tokens.append(m.group(1))
        if m.group(2):
            for idx_str in re.findall(r"\[(\d+)\]", m.group(2)):
                tokens.append(int(idx_str))

    cur: Any = obj
    for tok in tokens[:-1]:
        try:
            cur = cur[tok]
        except (KeyError, IndexError, TypeError) as exc:
            raise DiffValidationError("E005_INVALID_DIFF", f"Path not found in model: {path_expr!r}") from exc
    last = tokens[-1]
    try:
        cur[last] = value
    except (KeyError, IndexError, TypeError) as exc:
        raise DiffValidationError("E005_INVALID_DIFF", f"Cannot set final token of path: {path_expr!r}") from exc


def apply_form_diff_to_model(
    model: Dict[str, Any],
    form_diff: Dict[str, Any],
    validate_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Apply FormDiff patches onto candidate model, bump `model_version`, and enforce Schema-Gate."""
    if validate_fn is None:
        from project_ops_manager import validate_model_dict
        validate_fn = validate_model_dict

    candidate = copy.deepcopy(model)
    patches = list(form_diff.get("model_patches", []))

    for patch in patches:
        path = str(patch.get("path", "")).strip()
        if not path:
            continue
        _set_model_path(candidate, path, patch.get("value"))

    # Semantic grid monotonicity guard (Schema-Gate beyond pure JSON types).
    # Runs ONLY on a grid this diff actually patches — a pre-existing
    # non-monotonic grid that the patch leaves untouched must not reject every
    # diff (false-positive E006). Un-patched grids pass through as-is.
    proj = candidate.get("project", {})
    for gkey, total_key in (("grid_x", "L_total"), ("grid_y", "B_total")):
        if not any(str(p.get("path", "")).startswith(f"project.{gkey}") for p in patches):
            continue
        grid = proj.get(gkey, [])
        if len(grid) >= 2:
            coords = [float(item[1]) for item in grid]
            if any(coords[i + 1] <= coords[i] for i in range(len(coords) - 1)):
                raise DiffValidationError(
                    "E006_SCHEMA_GATE_REJECTED",
                    f"Non-monotonic {gkey} coordinates detected after diff: {coords}",
                    {"grid": grid},
                )
            span = round(max(coords) - min(coords), 4)
            if span > 0:
                proj[total_key] = span

    candidate["model_version"] = int(model.get("model_version", 1)) + 1

    try:
        validate_fn(candidate)
    except DiffValidationError:
        # validate_fn already produced a coded E006 (e.g. the structural
        # schema-gate's violation list) — propagate it verbatim, keep its
        # diff_details, instead of re-wrapping and losing them.
        raise
    except Exception as exc:
        raise DiffValidationError(
            "E006_SCHEMA_GATE_REJECTED",
            f"Candidate model rejected by schema-gate: {exc}",
            {"patches": patches},
        ) from exc

    # Determine affected sheet numbers
    explicit_sheets = form_diff.get("affected_sheets")
    if isinstance(explicit_sheets, list) and explicit_sheets:
        affected = [str(s) for s in explicit_sheets]
    else:
        affected = [str(sh.get("sheet_no", "")) for sh in candidate.get("sheets", []) if sh.get("sheet_no")]
    return candidate, affected
