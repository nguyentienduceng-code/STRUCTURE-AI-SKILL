# -*- coding: utf-8 -*-
"""
cad_multiview_a3.py — Canonical A3 Landscape Multi-View Structural Sheet Builder
===============================================================================

Renders dual-viewport A3 Landscape (42000 x 29700 mm at 1:100) structural CAD
drawings cleanly on top of DCE Pro's canonical `DcePlanEngine` and
`DCE_Master_Seed_Template.dxf` infrastructure (layers, linetypes, Dce_Text,
Dce_100MV dimstyles, Dce_KhTenTruc axis bubbles, v6 SHA256 audit sidecar).

Rules followed:
- AGENTS.md §1, §2: UTF-8 stdout + absolute paths.
- Rule 12b: Zero white text on dark background (CAD plot-ready light bg / dark ink).
- Rule 12d: Segmented beams, active SOLID concrete hatch (color=8), stopped column X,
            native DIMENSION (Dce_100MV), A3 frame + vertical right Title Block + Key Plan,
            voids on DCE_VoidX with zero beams crossing.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf
from ezdxf.enums import TextEntityAlignment


_FALLBACK_A3_LAYER_SPECS: Dict[str, Tuple[int, str, int]] = {
    # Authentic DCE Pro (Form 2.dxf) + Plan native colors (never alter Form 2 colors!)
    "DCE_Frame": (7, "Continuous", 50),
    "DCE_Schedule": (7, "Continuous", 20),
    "DCE_TKT-TEXT": (2, "Continuous", 15),
    "DCE_Note": (117, "Continuous", 18),
    "Dce_text": (7, "Continuous", 13),
    "DCE_Truc": (8, "DASHDOT2_DBIM", 13),
    "DCE_Dim": (254, "Continuous", 9),
    "DCE_Setout": (3, "Continuous", 13),
    "DCE_Cot": (2, "Continuous", 35),
    "DCE_Hatch": (8, "Continuous", 13),
    "DCE_Beam": (2, "BEAM HIDEN_DBIM", 25),
    "DCE_MainBeam": (3, "Continuous", 30),
    "DCE_NetThay": (7, "Continuous", 18),
    "DCE_NetDut": (8, "HIDDEN_DBIM", 5),
    "DCE_BaoBeTong": (4, "Continuous", 18),
    "DCE_Coc": (2, "Continuous", 13),
    "DCE_VoidX": (8, "Continuous", 13),
    "DCE_Name": (142, "Continuous", 20),
    "DCE_Symbol": (8, "Continuous", 9),
    "DCE_Leader": (250, "Continuous", 13),
}


def _load_a3_layer_specs() -> Dict[str, Tuple[int, str, int]]:
    try:
        shared_ctx = Path(__file__).resolve().parents[3] / "_SHARED" / "SHARED_CONTEXT"
        if str(shared_ctx) not in sys.path:
            sys.path.insert(0, str(shared_ctx))
        from cad_layer_standard import get_layer_specs
        ssot = get_layer_specs(profile="dce_native", include_compat=False)
        specs = dict(_FALLBACK_A3_LAYER_SPECS)
        for lname in list(_FALLBACK_A3_LAYER_SPECS.keys()):
            if lname in ssot:
                sp = ssot[lname]
                specs[lname] = (int(sp["color"]), str(sp["linetype"]), int(sp["lineweight"]))
        return specs
    except Exception:
        return dict(_FALLBACK_A3_LAYER_SPECS)


# Đồng bộ từ SSOT DCE Form 2 + DCE STEEL (profile dce_native — giữ nguyên màu gốc DCE Pro)
A3_LAYER_SPECS: Dict[str, Tuple[int, str, int]] = _load_a3_layer_specs()


def _ensure_a3_layers_and_styles(doc: ezdxf.document.Drawing) -> None:
    """Ensure active DCE layers exist with authentic Form 2 colors and positive lineweights."""
    try:
        doc.header["$LTSCALE"] = 100.0
    except Exception:
        pass

    for lname, (color, ltype, lw) in A3_LAYER_SPECS.items():
        if ltype not in doc.linetypes:
            ltype = "Continuous"
        if lname in doc.layers:
            # Keep authentic Form 2 / Seed template colors & linetypes untouched;
            # only ensure lineweight > 0 (G8.20) when template defaulted to <= 0.
            ly = doc.layers.get(lname)
            if int(getattr(ly.dxf, "lineweight", -3)) <= 0:
                ly.dxf.lineweight = lw
        else:
            doc.layers.add(
                lname,
                color=color,
                linetype=ltype,
                lineweight=lw,
            )

    # Fix any leftover template layers with negative/default lineweight (-3)
    # except layer '0' / 'Defpoints' if needed; G8.20 expects positive lineweights
    for ly in doc.layers:
        try:
            if ly.dxf.name.lower() == "defpoints":
                continue
            if int(getattr(ly.dxf, "lineweight", -3)) <= 0:
                ly.dxf.lineweight = 18
        except Exception:
            pass

    if "Dce_Text" not in doc.styles:
        doc.styles.add("Dce_Text", font="arial.ttf")


def _rect_poly(msp, x0: float, y0: float, x1: float, y1: float, layer: str, close: bool = True, const_width: float = 0.0):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    attr = {"layer": layer}
    if const_width > 0:
        attr["const_width"] = const_width
    return msp.add_lwpolyline(pts, close=close, dxfattribs=attr)


def _add_text(
    msp,
    text: str,
    x: float,
    y: float,
    height: float,
    layer: str = "DCE_TKT-TEXT",
    align: TextEntityAlignment = TextEntityAlignment.MIDDLE_CENTER,
    rotation: float = 0.0,
    style: str = "Dce_Text",
    color: Optional[int] = None,
):
    attribs: Dict[str, Any] = {
        "height": height,
        "layer": layer,
        "style": style,
        "rotation": rotation,
    }
    if color is not None:
        attribs["color"] = color
    ent = msp.add_text(str(text), dxfattribs=attribs)
    ent.set_placement((x, y), align=align)
    return ent


def _add_native_dim(
    msp,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    base: Tuple[float, float],
    angle: float = 0.0,
    dimstyle: str = "Dce_100MV",
    dimtxt_mm: float = 2.0,
    text_override: Optional[str] = None,
    layer: str = "DCE_Dim",
    dimtad: int = 1,
    text_shift_x: float = 0.0,
    text_shift_y: float = 0.0,
):
    override: Dict[str, Any] = {
        "dimtxt": dimtxt_mm,
        "dimclrd": 8,
        "dimclre": 8,
        "dimclrt": 3,
        "dimasz": 1.35,
        "dimexo": 1.5,
        "dimexe": 1.0,
        "dimtad": dimtad,
    }
    kw: Dict[str, Any] = {
        "base": base,
        "p1": p1,
        "p2": p2,
        "angle": angle,
        "dimstyle": dimstyle,
        "override": override,
        "dxfattribs": {"layer": layer},
    }
    if text_override:
        kw["text"] = str(text_override)
    dim = msp.add_linear_dim(**kw)
    if (abs(text_shift_x) > 1e-3 or abs(text_shift_y) > 1e-3) and hasattr(dim, "shift_text"):
        dim.shift_text(text_shift_x, text_shift_y)
    dim.render()
    return dim


def _draw_pile_symbol(msp, cx: float, cy: float, size_mm: float = 250.0, kind: str = "TYPE1", draw_cross_lines: bool = True) -> None:
    """Draw a square RC pile symbol (TYPE1: + cross, TYPE2: diagonal hatch, TYPE3: solid fill)."""
    half = size_mm / 2.0
    x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
    _rect_poly(msp, x0, y0, x1, y1, layer="DCE_Coc")
    k = str(kind).upper()
    if k == "TYPE3":
        h = msp.add_hatch(color=256, dxfattribs={"layer": "DCE_Coc"})
        h.set_pattern_fill("SOLID")
        h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    elif k == "TYPE2":
        h = msp.add_hatch(color=256, dxfattribs={"layer": "DCE_Hatch"})
        h.set_pattern_fill("ANSI31", scale=32.0, angle=45.0)
        h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    if draw_cross_lines or k == "TYPE1":
        ext = half * 1.45 if k == "TYPE1" else half * 1.25
        msp.add_line((cx - ext, cy), (cx + ext, cy), dxfattribs={"layer": "DCE_Coc"})
        msp.add_line((cx, cy - ext), (cx, cy + ext), dxfattribs={"layer": "DCE_Coc"})


def _render_left_table(engine, tbl: Dict[str, Any]) -> None:
    """Render a clean tabular schedule block (e.g., BẢNG CỌC / BẢNG ĐÀI MÓNG) on DCE_Schedule."""
    msp = engine.msp
    x0 = float(tbl["x0_mm"])
    y_top = float(tbl["y_top_mm"])
    col_widths = [float(w) for w in tbl["col_widths_mm"]]
    headers = list(tbl["headers"])
    rows = list(tbl["rows"])
    hdr_h = float(tbl.get("header_height_mm", 560.0))
    row_h = float(tbl.get("row_height_mm", 540.0))
    sub_headers = tbl.get("sub_headers")  # Optional grouped sub-header list
    title_note = tbl.get("top_note", "")

    total_w = sum(col_widths)
    x1 = x0 + total_w
    y_bot = y_top - hdr_h - len(rows) * row_h

    if title_note:
        _add_text(
            msp,
            str(title_note),
            x0 + 40.0,
            y_top + 260.0,
            175.0,
            layer="Dce_text",
            align=TextEntityAlignment.MIDDLE_LEFT,
        )

    _rect_poly(msp, x0, y_bot, x1, y_top, layer="DCE_Schedule")
    msp.add_line((x0, y_top - hdr_h), (x1, y_top - hdr_h), dxfattribs={"layer": "DCE_Schedule"})

    # Column boundaries
    xs = [x0]
    for w in col_widths:
        xs.append(xs[-1] + w)
    for col_i, cx_b in enumerate(xs[1:-1], start=1):
        # Optional merged group header spanning sub-columns
        skip_top = False
        if sub_headers:
            grp_s = int(sub_headers["group"]["start_col"])
            grp_e = int(sub_headers["group"]["end_col"])
            skip_top = grp_s < col_i <= grp_e
        y_line_top = (y_top - hdr_h * 0.5) if skip_top else y_top
        msp.add_line((cx_b, y_bot), (cx_b, y_line_top), dxfattribs={"layer": "DCE_Schedule"})

    if sub_headers:
        grp = sub_headers["group"]
        gx0 = xs[int(grp["start_col"])]
        gx1 = xs[int(grp["end_col"]) + 1]
        y_mid_h = y_top - hdr_h * 0.5
        msp.add_line((gx0, y_mid_h), (gx1, y_mid_h), dxfattribs={"layer": "DCE_Schedule"})
        engine._add_fitted_table_text(
            str(grp["title"]), (gx0 + gx1) / 2.0, (y_top + y_mid_h) / 2.0, gx1 - gx0 - 60.0, height=130.0, layer="DCE_Schedule"
        )
        for ci, htxt in enumerate(headers):
            cx_m = (xs[ci] + xs[ci + 1]) / 2.0
            if int(grp["start_col"]) <= ci <= int(grp["end_col"]):
                engine._add_fitted_table_text(str(htxt), cx_m, (y_mid_h + y_top - hdr_h) / 2.0, col_widths[ci] - 40.0, height=115.0, layer="DCE_Schedule")
            else:
                engine._add_fitted_table_text(str(htxt), cx_m, y_top - hdr_h / 2.0, max(120.0, col_widths[ci] - 120.0), height=130.0, layer="DCE_Schedule")
    else:
        for ci, htxt in enumerate(headers):
            cx_m = (xs[ci] + xs[ci + 1]) / 2.0
            engine._add_fitted_table_text(str(htxt), cx_m, y_top - hdr_h / 2.0, max(120.0, col_widths[ci] - 120.0), height=145.0, layer="DCE_Schedule")

    for ri, row in enumerate(rows):
        ry_top = y_top - hdr_h - ri * row_h
        ry_mid = ry_top - row_h / 2.0
        if ri > 0:
            msp.add_line((x0, ry_top), (x1, ry_top), dxfattribs={"layer": "DCE_Schedule"})
        for ci, val in enumerate(row):
            cx_m = (xs[ci] + xs[ci + 1]) / 2.0
            if isinstance(val, dict) and "pile_icon" in val:
                _draw_pile_symbol(msp, cx_m, ry_mid, size_mm=240.0, kind=str(val["pile_icon"]), draw_cross_lines=True)
            else:
                engine._add_fitted_table_text(str(val), cx_m, ry_mid, max(120.0, col_widths[ci] - 160.0), height=140.0, layer="DCE_Schedule")


def _add_hatch_zone(msp, bbox: List[float], style: str, spacing_m: float, angle: float, ox: float, oy: float, label: str = "") -> None:
    """Draw clean crisp diagonal/cross/dot hatch pattern matching floor elevation zones."""
    x0_w = ox + bbox[0] * 1000.0
    y0_w = oy + bbox[1] * 1000.0
    x1_w = ox + bbox[2] * 1000.0
    y1_w = oy + bbox[3] * 1000.0

    # Perimeter boundary on DCE_BaoBeTong so zone boundary reads clearly
    _rect_poly(msp, x0_w, y0_w, x1_w, y1_w, layer="DCE_BaoBeTong")

    if label == "LIFT":
        # Lift shaft: cross X + centered HỐ THANG label sized cleanly inside clear opening
        msp.add_line((x0_w, y0_w), (x1_w, y1_w), dxfattribs={"layer": "DCE_VoidX"})
        msp.add_line((x0_w, y1_w), (x1_w, y0_w), dxfattribs={"layer": "DCE_VoidX"})
        _add_text(
            msp,
            "HỐ THANG",
            (x0_w + x1_w) / 2.0,
            (y0_w + y1_w) / 2.0,
            130.0,
            layer="Dce_text",
        )
        return

    # Native ezdxf HATCH with light pattern on DCE_Hatch
    hatch = msp.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
    if label == "+1.050":
        # Raised porch landing +1.050 matches dotted/cross fill in reference legend
        hatch.set_pattern_fill("ANSI37", scale=95.0, angle=45.0)
    elif str(style).upper() == "DASH":
        hatch.set_pattern_fill("DASH", scale=75.0, angle=float(angle))
    else:
        hatch.set_pattern_fill("ANSI31", scale=110.0, angle=angle)
    hatch.paths.add_polyline_path(
        [(x0_w, y0_w), (x1_w, y0_w), (x1_w, y1_w), (x0_w, y1_w)],
        is_closed=True,
    )


def _draw_steel_h_inside(msp, x0: float, y0: float, x1: float, y1: float) -> None:
    """Draw recognizable H-section steel profile inside column box (200x200)."""
    cx = (x0 + x1) / 2.0
    t_f = max(25.0, (y1 - y0) * 0.14)
    t_w = max(20.0, (x1 - x0) * 0.12)
    pts = [
        (x0, y0), (x1, y0), (x1, y0 + t_f), (cx + t_w / 2.0, y0 + t_f),
        (cx + t_w / 2.0, y1 - t_f), (x1, y1 - t_f), (x1, y1), (x0, y1),
        (x0, y1 - t_f), (cx - t_w / 2.0, y1 - t_f), (cx - t_w / 2.0, y0 + t_f),
        (x0, y0 + t_f),
    ]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot"})


def _boxes_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float], pad: float = 35.0) -> bool:
    return not (
        a[2] + pad < b[0]
        or b[2] + pad < a[0]
        or a[3] + pad < b[1]
        or b[3] + pad < a[1]
    )


def _make_tag_box(cx: float, cy: float, w: float, h: float, rot: float) -> Tuple[float, float, float, float]:
    if abs(rot - 90.0) < 10.0:
        w, h = h, w
    return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


def _active_axes_for_floor(vp: Dict[str, Any], project: Dict[str, Any]) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """Return active X and Y grid lines present on this floor."""
    all_x = [(str(name), float(val)) for name, val in project["grid_x"]]
    all_y = [(str(name), float(val)) for name, val in project["grid_y"]]

    # Determine min/max X from slab outline & columns so T1 shows 0..6 and upper floors show 1..5
    xs = [pt[0] for pt in vp.get("slab_outline", [])]
    # `x0`/`x1` are optional on a column (schema requires only id/mark/b_mm/h_mm);
    # a schema-valid column without them must not crash the axis filter.
    for c in vp.get("columns", []):
        if c.get("x0") is not None:
            xs.append(c["x0"])
        if c.get("x1") is not None:
            xs.append(c["x1"])
    min_x = min(xs) if xs else 0.0
    max_x = max(xs) if xs else 18.0

    # Keep axes whose coordinate falls within [min_x - 0.1, max_x + 0.1] OR matches a column center
    active_x = []
    for name, val in all_x:
        if val >= min_x - 0.15 and val <= max_x + 0.15:
            active_x.append((name, val))
        elif vp.get("id") == "T1":
            active_x.append((name, val))
    return active_x, all_y


_DEFAULT_FORM02_ZONES: Dict[str, Tuple[float, float, float, float]] = {
    "VIEWPORT_TOP": (700.0, 15250.0, 28300.0, 29200.0),
    "VIEWPORT_BOTTOM": (700.0, 650.0, 28300.0, 14500.0),
    "TABLE": (700.0, 15250.0, 11200.0, 18600.0),
    "NOTE": (28500.0, 650.0, 36400.0, 14500.0),
    "KEYPLAN": (36950.0, 22200.0, 41750.0, 29350.0),
}


def _zone_shift_delta(
    zone_key: str,
    zone_bboxes: Optional[Dict[str, List[Tuple[float, float, float, float]]]],
) -> Tuple[float, float]:
    if not zone_bboxes or zone_key not in zone_bboxes or not zone_bboxes[zone_key]:
        return (0.0, 0.0)
    zx0, zy0, zx1, zy1 = zone_bboxes[zone_key][0]
    dx0, dy0, dx1, dy1 = _DEFAULT_FORM02_ZONES[zone_key]
    cx_actual, cy_actual = (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0
    cx_def, cy_def = (dx0 + dx1) / 2.0, (dy0 + dy1) / 2.0
    dx = cx_actual - cx_def
    dy = cy_actual - cy_def
    if abs(dx) < 50.0 and abs(dy) < 50.0:
        return (0.0, 0.0)
    return (dx, dy)


def _render_viewport(
    engine,
    vp: Dict[str, Any],
    project: Dict[str, Any],
    sheet_no: str,
    use_dce_blocks: bool = False,
    zone_bboxes: Optional[Dict[str, List[Tuple[float, float, float, float]]]] = None,
) -> Dict[str, Any]:
    """Render one structural floor plan viewport (TOP or BOT) with zero collisions."""
    msp = engine.msp
    slot_key = "VIEWPORT_TOP" if str(vp.get("slot", "")).upper() == "TOP" else (
        "VIEWPORT_BOTTOM" if str(vp.get("slot", "")).upper() == "BOT" else ""
    )
    dx_zone, dy_zone = _zone_shift_delta(slot_key, zone_bboxes) if slot_key else (0.0, 0.0)
    ox = float(vp["origin_mm"][0]) + dx_zone
    oy = float(vp["origin_mm"][1]) + dy_zone
    vp_id = str(vp.get("id", "VP"))

    active_x, active_y = _active_axes_for_floor(vp, project)
    min_ax_m = min(x for _, x in active_x)
    max_ax_m = max(x for _, x in active_x)
    min_slab_m = min([pt[0] for pt in vp["slab_outline"]] + [min_ax_m])
    max_slab_m = max([pt[0] for pt in vp["slab_outline"]] + [max_ax_m])

    x_left_plan = ox + min_slab_m * 1000.0
    x_right_plan = ox + max_slab_m * 1000.0
    y_bot_plan = oy
    y_top_plan = oy + float(project["B_total"]) * 1000.0

    # Coordinates for exterior 4-tier hierarchy (configurable per viewport, defaults preserved)
    ext_off = vp.get("exterior_offsets_mm", {})
    bubble_left_cx = x_left_plan - float(ext_off.get("bubble_left", 1950.0))
    dim_left_x = x_left_plan - float(ext_off.get("dim_left", 950.0))
    bubble_right_cx = x_right_plan + float(ext_off.get("bubble_right", 1950.0))
    dim_right_x = x_right_plan + float(ext_off.get("dim_right", 950.0))

    dim_top_t1_y = y_top_plan + float(ext_off.get("dim_top_t1", 760.0))
    dim_top_t2_y = y_top_plan + float(ext_off.get("dim_top_t2", 1260.0))
    bubble_top_cy = y_top_plan + float(ext_off.get("bubble_top", 1950.0))

    dim_bot_t1_y = y_bot_plan - float(ext_off.get("dim_bot_t1", 1850.0))
    dim_bot_t2_y = y_bot_plan - float(ext_off.get("dim_bot_t2", 2350.0))
    bubble_bot_cy = y_bot_plan - float(ext_off.get("bubble_bot", 3000.0))

    obstacles: List[Tuple[float, float, float, float]] = []

    # 1. Grid lines (stop cleanly at outer bubble rims ±250 mm so text is never crossed)
    gx_line_y0 = bubble_bot_cy + 250.0
    gx_line_y1 = bubble_top_cy - 250.0
    for ax_name, gx_m in active_x:
        gx_w = ox + gx_m * 1000.0
        msp.add_line(
            (gx_w, gx_line_y0),
            (gx_w, gx_line_y1),
            dxfattribs={"layer": "DCE_Truc", "linetype": "DASHDOT2_DBIM", "ltscale": 1.0},
        )
        engine._insert_axis_bubble(gx_w, bubble_top_cy - 350.0, ax_name, 180.0)
        engine._insert_axis_bubble(gx_w, bubble_bot_cy + 350.0, ax_name, 0.0)
        obstacles.append((gx_w - 280.0, bubble_top_cy - 280.0, gx_w + 280.0, bubble_top_cy + 280.0))
        obstacles.append((gx_w - 280.0, bubble_bot_cy - 280.0, gx_w + 280.0, bubble_bot_cy + 280.0))

    gy_line_x0 = bubble_left_cx + 250.0
    gy_line_x1 = bubble_right_cx - 250.0
    for ay_name, gy_m in active_y:
        gy_w = oy + gy_m * 1000.0
        msp.add_line(
            (gy_line_x0, gy_w),
            (gy_line_x1, gy_w),
            dxfattribs={"layer": "DCE_Truc", "linetype": "DASHDOT2_DBIM", "ltscale": 1.0},
        )
        engine._insert_axis_bubble(bubble_left_cx - 350.0, gy_w, ay_name, 90.0)
        engine._insert_axis_bubble(bubble_right_cx + 350.0, gy_w, ay_name, -90.0)
        obstacles.append((bubble_left_cx - 280.0, gy_w - 280.0, bubble_left_cx + 280.0, gy_w + 280.0))
        obstacles.append((bubble_right_cx - 280.0, gy_w - 280.0, bubble_right_cx + 280.0, gy_w + 280.0))

    # 2. Outer slab perimeter (cantilever overhang / floor footprint)
    slab_pts = [(ox + p[0] * 1000.0, oy + p[1] * 1000.0) for p in vp["slab_outline"]]
    msp.add_lwpolyline(slab_pts, close=True, dxfattribs={"layer": "DCE_BaoBeTong"})

    # 3. Hatch zones (lowered slabs + lift shaft + raised porch)
    for hz in vp.get("hatch_zones", []):
        _add_hatch_zone(
            msp,
            hz["bbox"],
            hz.get("style", "ANSI31"),
            float(hz.get("spacing", 0.2)),
            float(hz.get("angle", 45.0)),
            ox,
            oy,
            label=str(hz.get("label", "")),
        )
        if str(hz.get("label", "")) == "LIFT":
            hb = hz["bbox"]
            obstacles.append((ox + hb[0] * 1000.0, oy + hb[1] * 1000.0, ox + hb[2] * 1000.0, oy + hb[3] * 1000.0))

    # 4. Floor voids (DCE_VoidX — never crossed by beams)
    for vd in vp.get("voids", []):
        vx0 = ox + vd["x0"] * 1000.0
        vy0 = oy + vd["y0"] * 1000.0
        vx1 = ox + vd["x1"] * 1000.0
        vy1 = oy + vd["y1"] * 1000.0
        _rect_poly(msp, vx0, vy0, vx1, vy1, layer="DCE_VoidX")
        msp.add_line((vx0, vy0), (vx1, vy1), dxfattribs={"layer": "DCE_VoidX"})
        msp.add_line((vx0, vy1), (vx1, vy0), dxfattribs={"layer": "DCE_VoidX"})
        obstacles.append((vx0, vy0, vx1, vy1))

    # 5. Extra structural lines (stairs, trimmers, ramp >>> chevrons, stepped edges, roof diagonals)
    for ln in vp.get("extra_lines", []):
        p1 = (ox + ln["p1"][0] * 1000.0, oy + ln["p1"][1] * 1000.0)
        p2 = (ox + ln["p2"][0] * 1000.0, oy + ln["p2"][1] * 1000.0)
        is_dash = bool(ln.get("dash", False))
        attribs: Dict[str, Any] = {
            "layer": "DCE_NetDut" if is_dash else "DCE_BaoBeTong",
            "linetype": "HIDDEN_DBIM" if is_dash else "Continuous",
        }
        if is_dash:
            attribs["ltscale"] = 0.85
        msp.add_line(p1, p2, dxfattribs=attribs)

    # Obstacles are data-driven; legacy fixtures retain the historical stair
    # boxes unless the viewport explicitly supplies its own list.
    stair_boxes = vp.get("obstacle_bboxes_mm")
    if stair_boxes is None and vp_id != "MT":
        stair_boxes = [
            [13550.0, 2700.0, 14500.0, 4850.0],
            [14450.0, 3950.0, 16850.0, 4850.0],
            [15950.0, 3200.0, 16850.0, 4050.0],
        ]
    for box in stair_boxes or []:
        if len(box) != 4:
            raise ValueError(f"obstacle_bboxes_mm must contain [x0,y0,x1,y1], got {box!r}")
        obstacles.append(tuple(ox + float(box[i]) if i % 2 == 0 else oy + float(box[i]) for i in range(4)))

    # 5b. Pile caps (Đài móng) & Lean concrete pads (Bê tông lót)
    for cidx, cap in enumerate(vp.get("pile_caps", [])):
        px0 = ox + float(cap["x0"]) * 1000.0
        py0 = oy + float(cap["y0"]) * 1000.0
        px1 = ox + float(cap["x1"]) * 1000.0
        py1 = oy + float(cap["y1"]) * 1000.0
        if cap.get("dashed"):
            msp.add_lwpolyline(
                [(px0, py0), (px1, py0), (px1, py1), (px0, py1)],
                close=True,
                dxfattribs={"layer": "DCE_NetDut", "linetype": "HIDDEN_DBIM", "ltscale": 0.85},
            )
            continue
        _rect_poly(msp, px0, py0, px1, py1, layer="DCE_BaoBeTong")
        obstacles.append((px0 - 50.0, py0 - 50.0, px1 + 50.0, py1 + 50.0))
        pad_m = float(cap.get("pad_m", 0.10))
        if pad_m > 0:
            x_min_b = ox + float(cap.get("clip_x0", 0.0)) * 1000.0
            y_min_b = oy + float(cap.get("clip_y0", 0.0)) * 1000.0
            x_max_b = ox + float(cap.get("clip_x1", 18.0)) * 1000.0
            y_max_b = oy + float(cap.get("clip_y1", float(project["B_total"]))) * 1000.0
            lx0 = max(x_min_b, px0 - pad_m * 1000.0)
            ly0 = max(y_min_b, py0 - pad_m * 1000.0)
            lx1 = min(x_max_b, px1 + pad_m * 1000.0)
            ly1 = min(y_max_b, py1 + pad_m * 1000.0)
            msp.add_lwpolyline(
                [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)],
                close=True,
                dxfattribs={"layer": "DCE_NetDut", "linetype": "HIDDEN_DBIM", "ltscale": 0.85},
            )
        mark_c = str(cap.get("mark", "")).strip()
        if mark_c:
            lpos = cap.get("label_pos")
            lx_m = ox + float(lpos[0]) * 1000.0 if lpos else (px0 + px1) / 2.0
            ly_m = oy + float(lpos[1]) * 1000.0 if lpos else (py0 + py1) / 2.0
            _add_text(msp, mark_c, lx_m, ly_m, float(cap.get("label_h", 145.0)), layer="DCE_Name")
            obstacles.append((lx_m - 320.0, ly_m - 120.0, lx_m + 320.0, ly_m + 120.0))
        if engine.element_registry is not None and mark_c:
            engine._v6_register_element(
                "pile_cap",
                f"{vp_id}_{mark_c}_{cidx}",
                mark_c,
                {
                    "b_mm": round(px1 - px0),
                    "h_mm": round(py1 - py0),
                    "floor": vp_id,
                    "sheet": sheet_no,
                },
            )

    # 5c. Piles (Cọc ép vuông 250x250 — named block `DCE_Pile_*` when use_dce_blocks=True)
    pile_block_cnt = 0
    col_block_cnt = 0
    if use_dce_blocks:
        from cad_block_adapters import insert_column_block, insert_pile_block
    for pidx, pl in enumerate(vp.get("piles", [])):
        cx_p = ox + float(pl["x"]) * 1000.0
        cy_p = oy + float(pl["y"]) * 1000.0
        sz_mm = float(pl.get("size_m", 0.25)) * 1000.0
        pkind = str(pl.get("kind", "TYPE1"))
        if use_dce_blocks:
            insert_pile_block(
                engine.doc,
                msp,
                cx_p,
                cy_p,
                kind=pkind,
                size_mm=sz_mm,
                shape=str(pl.get("shape", "SQUARE")),
                draw_cross_lines=bool(pl.get("cross", True)),
                pile_id=str(pl.get("id") or f"{vp_id}_P{pidx + 1}"),
                length_m=str(pl.get("length_m", "")),
                capacity_t=str(pl.get("capacity_t", "")),
                show_label=bool(pl.get("show_label", False)),
                mark_owned=True,
            )
            pile_block_cnt += 1
        else:
            _draw_pile_symbol(msp, cx_p, cy_p, size_mm=sz_mm, kind=pkind, draw_cross_lines=bool(pl.get("cross", True)))
        obstacles.append((cx_p - sz_mm * 0.6, cy_p - sz_mm * 0.6, cx_p + sz_mm * 0.6, cy_p + sz_mm * 0.6))
        if engine.element_registry is not None and pl.get("register", False):
            engine._v6_register_element(
                "pile",
                f"{vp_id}_PILE_{pidx}",
                f"CỌC-{pkind}",
                {"size_mm": round(sz_mm), "kind": pkind, "floor": vp_id, "sheet": sheet_no},
            )

    # 6. Columns (named block `DCE_COL_*` when use_dce_blocks=True, or inline geometry)
    for col in vp.get("columns", []):
        cx0 = ox + col["x0"] * 1000.0
        cy0 = oy + col["y0"] * 1000.0
        cx1 = ox + col["x1"] * 1000.0
        cy1 = oy + col["y1"] * 1000.0
        kind = str(col.get("kind", "RC"))
        if use_dce_blocks:
            insert_column_block(
                engine.doc,
                msp,
                cx=(cx0 + cx1) / 2.0,
                cy=(cy0 + cy1) / 2.0,
                b_mm=(cx1 - cx0),
                h_mm=(cy1 - cy0),
                kind=kind,
                mark=str(col.get("mark", "")),
                show_tag=bool(col.get("show_tag", False)),
                mark_owned=True,
            )
            col_block_cnt += 1
        elif kind == "RC_STOPPED":
            _rect_poly(msp, cx0, cy0, cx1, cy1, layer="DCE_Cot")
            msp.add_line((cx0, cy0), (cx1, cy1), dxfattribs={"layer": "DCE_NetThay"})
            msp.add_line((cx0, cy1), (cx1, cy0), dxfattribs={"layer": "DCE_NetThay"})
        elif kind == "STEEL_H":
            _draw_steel_h_inside(msp, cx0, cy0, cx1, cy1)
        else:
            _rect_poly(msp, cx0, cy0, cx1, cy1, layer="DCE_Cot")
            engine._solid_hatch([(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], layer="DCE_Hatch")
        obstacles.append((cx0, cy0, cx1, cy1))

        # Register active columns into v6 CadElementRegistry
        if engine.element_registry is not None:
            eid = f"{vp_id}_{col['id']}"
            engine._v6_register_element(
                "column",
                eid,
                str(col["mark"]),
                {
                    "b_mm": col.get("b_mm", 200),
                    "h_mm": col.get("h_mm", 200),
                    "floor": vp_id,
                    "sheet": sheet_no,
                    "kind": kind,
                },
            )

    # 7. Segmented beams (independent SOLID vs HIDDEN_DBIM edge drawing + collision-aware labels)
    placed_tag_boxes: List[Tuple[float, float, float, float]] = []
    seen_beam_ids: set = set()
    for bidx, bm in enumerate(vp.get("beams", [])):
        bx0 = ox + bm["x0"] * 1000.0
        by0 = oy + bm["y0"] * 1000.0
        bx1 = ox + bm["x1"] * 1000.0
        by1 = oy + bm["y1"] * 1000.0
        orient = bm.get("orient", "X").upper()

        if orient == "X":
            l_bot = "DCE_NetThay" if bm.get("edge_bottom_dash") else "DCE_Beam"
            lt_bot = "BEAM HIDEN_DBIM" if bm.get("edge_bottom_dash") else "Continuous"
            l_top = "DCE_NetThay" if bm.get("edge_top_dash") else "DCE_Beam"
            lt_top = "BEAM HIDEN_DBIM" if bm.get("edge_top_dash") else "Continuous"
            msp.add_line((bx0, by0), (bx1, by0), dxfattribs={"layer": l_bot, "linetype": lt_bot, "ltscale": 0.9})
            msp.add_line((bx0, by1), (bx1, by1), dxfattribs={"layer": l_top, "linetype": lt_top, "ltscale": 0.9})
        else:
            l_l = "DCE_NetThay" if bm.get("edge_left_dash") else "DCE_Beam"
            lt_l = "BEAM HIDEN_DBIM" if bm.get("edge_left_dash") else "Continuous"
            l_r = "DCE_NetThay" if bm.get("edge_right_dash") else "DCE_Beam"
            lt_r = "BEAM HIDEN_DBIM" if bm.get("edge_right_dash") else "Continuous"
            msp.add_line((bx0, by0), (bx0, by1), dxfattribs={"layer": l_l, "linetype": lt_l, "ltscale": 0.9})
            msp.add_line((bx1, by0), (bx1, by1), dxfattribs={"layer": l_r, "linetype": lt_r, "ltscale": 0.9})

        if engine.element_registry is not None:
            beid = f"{vp_id}_{bm['mark']}_{bidx}"
            if beid not in seen_beam_ids:
                seen_beam_ids.add(beid)
                parts = str(bm.get("size", "200x300")).lower().split("x")
                engine._v6_register_element(
                    "beam",
                    beid,
                    str(bm["mark"]),
                    {
                        "b_mm": int(parts[0]) if len(parts) == 2 and parts[0].isdigit() else 200,
                        "h_mm": int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 300,
                        "floor": vp_id,
                        "sheet": sheet_no,
                    },
                )

    # Place beam labels AFTER all columns/voids/stairs are in obstacles
    # Track local_dims lines/text as obstacles too
    for ld in vp.get("local_dims", []):
        bp = (ox + ld["base"][0] * 1000.0, oy + ld["base"][1] * 1000.0)
        obstacles.append((bp[0] - 250.0, bp[1] - 180.0, bp[0] + 250.0, bp[1] + 180.0))

    tag_h = 145.0
    for bm in vp.get("beams", []):
        if not bm.get("show_label", False):
            continue
        bx0 = ox + bm["x0"] * 1000.0
        by0 = oy + bm["y0"] * 1000.0
        bx1 = ox + bm["x1"] * 1000.0
        by1 = oy + bm["y1"] * 1000.0
        orient = bm.get("orient", "X").upper()
        side = str(bm.get("label_side", "above" if orient == "X" else "left"))
        span_w = bx1 - bx0 if orient == "X" else by1 - by0
        compact_stack = bool(bm.get("stack_label")) or (span_w < 1900.0 and orient == "X") or (bm["x0"] >= 13.5 and orient == "X") or (span_w < 1300.0 and orient == "Y")

        mark_s = str(bm["mark"])
        size_s = str(bm["size"])
        if compact_stack:
            # Stacked 2-line label for tight bays (e.g. Bay 4-5 stair/lift corridor or short cantilevers)
            th = 112.0
            est_w = max(460.0, max(len(mark_s), len(size_s)) * th * 0.65)
            est_h = th * 2.35
        else:
            th = tag_h
            label_txt = f"{mark_s} ({size_s})"
            est_w = max(550.0, len(label_txt) * th * 0.62)
            est_h = th * 1.15

        if orient == "X":
            cx = (
                ox + float(bm["label_x_override"]) * 1000.0
                if bm.get("label_x_override") is not None
                else (bx0 + bx1) / 2.0
            )
            rot = 0.0
            # Special stair corridor smart slots (open gap y=1.70..2.30 or 2.55..3.00)
            if bm["x0"] >= 13.5 and 1.40 <= bm["y0"] <= 1.60:
                cands = [(ox + 14950.0, oy + 2000.0), (ox + 15950.0, oy + 2000.0), (cx, by1 + 210.0)]
            elif bm["x0"] >= 13.5 and 2.20 <= bm["y0"] <= 2.40:
                cands = [(ox + 16050.0, oy + 2000.0), (ox + 15000.0, oy + 2000.0), (cx, by0 - 210.0)]
            elif bm["x0"] >= 15.8 and 2.95 <= bm["y0"] <= 3.15:
                cands = [(ox + 16540.0, oy + 2760.0), (ox + 16540.0, oy + 3450.0), (cx - 500.0, oy + 2760.0)]
            elif bm.get("label_y_override") is not None:
                cy = oy + float(bm["label_y_override"]) * 1000.0
                cands = [(cx, cy), (cx, cy - 260.0), (cx, cy + 260.0)]
            else:
                off = 250.0
                off_far = 490.0
                cands = (
                    [
                        (cx, by1 + off),
                        (cx, by0 - off),
                        (cx, by1 + off_far),
                        (cx + 480.0, by1 + off),
                        (cx - 480.0, by1 + off),
                        (cx + 820.0, by1 + off),
                        (cx - 820.0, by1 + off),
                    ]
                    if side == "above"
                    else [
                        (cx, by0 - off),
                        (cx, by1 + off),
                        (cx, by0 - off_far),
                        (cx + 480.0, by0 - off),
                        (cx - 480.0, by0 - off),
                        (cx + 820.0, by0 - off),
                        (cx - 820.0, by0 - off),
                    ]
                )
        else:
            cy = oy + float(bm["label_y_override"]) * 1000.0 if bm.get("label_y_override") is not None else (by0 + by1) / 2.0
            rot = 90.0
            off = 240.0
            off_far = 470.0
            cands = (
                [
                    (bx0 - off, cy),
                    (bx1 + off, cy),
                    (bx0 - off_far, cy),
                    (bx0 - off, cy + 480.0),
                    (bx0 - off, cy - 480.0),
                    (bx1 + off, cy + 480.0),
                    (bx1 + off, cy - 480.0),
                ]
                if side == "left"
                else [
                    (bx1 + off, cy),
                    (bx0 - off, cy),
                    (bx1 + off_far, cy),
                    (bx1 + off, cy + 480.0),
                    (bx1 + off, cy - 480.0),
                    (bx0 - off, cy + 480.0),
                    (bx0 - off, cy - 480.0),
                ]
            )

        chosen = cands[0]
        for px, py in cands:
            tb = _make_tag_box(px, py, est_w, est_h, rot)
            if not any(_boxes_overlap(tb, ob, pad=20.0) for ob in obstacles + placed_tag_boxes):
                chosen = (px, py)
                break
        placed_tag_boxes.append(_make_tag_box(chosen[0], chosen[1], est_w, est_h, rot))
        if compact_stack:
            if abs(rot - 90.0) < 10.0:
                _add_text(msp, mark_s, chosen[0] - th * 0.62, chosen[1], th, layer="DCE_Name", rotation=rot)
                _add_text(msp, size_s, chosen[0] + th * 0.62, chosen[1], th, layer="DCE_Name", rotation=rot)
            else:
                _add_text(msp, mark_s, chosen[0], chosen[1] + th * 0.62, th, layer="DCE_Name", rotation=rot)
                _add_text(msp, size_s, chosen[0], chosen[1] - th * 0.62, th, layer="DCE_Name", rotation=rot)
        else:
            _add_text(msp, f"{mark_s} ({size_s})", chosen[0], chosen[1], th, layer="DCE_Name", rotation=rot)

    # 8. Extra callout texts (e.g., DẦM RAM DỐC 200x300)
    for et in vp.get("extra_texts", []):
        tx = ox + float(et["x"]) * 1000.0
        ty = oy + float(et["y"]) * 1000.0
        _add_text(msp, et["text"], tx, ty, float(et.get("h", 155.0)), layer="DCE_Name")

    # 9. Exterior Grid Dimensions (Dce_100MV native DIMENSION entities)
    ax_coords_w = [ox + gx_m * 1000.0 for _, gx_m in active_x]
    for i in range(len(ax_coords_w) - 1):
        x_a, x_b = ax_coords_w[i], ax_coords_w[i + 1]
        _add_native_dim(msp, (x_a, y_top_plan), (x_b, y_top_plan), (x_a, dim_top_t1_y), angle=0.0)
        _add_native_dim(msp, (x_a, y_bot_plan), (x_b, y_bot_plan), (x_a, dim_bot_t1_y), angle=0.0)
    # Overall X dim: shift text horizontally if midpoint lands near an active vertical grid line (e.g. Axis 3)
    x_ov_0, x_ov_1 = ax_coords_w[0], ax_coords_w[-1]
    mid_ov = (x_ov_0 + x_ov_1) / 2.0
    shift_ov = -620.0 if any(abs(gx_w - mid_ov) < 550.0 for gx_w in ax_coords_w) else 0.0
    _add_native_dim(msp, (x_ov_0, y_top_plan), (x_ov_1, y_top_plan), (x_ov_0, dim_top_t2_y), angle=0.0, text_shift_x=shift_ov)
    _add_native_dim(msp, (x_ov_0, y_bot_plan), (x_ov_1, y_bot_plan), (x_ov_0, dim_bot_t2_y), angle=0.0, text_shift_x=shift_ov)
    # Left & Right Y dims (5000)
    _add_native_dim(msp, (x_left_plan, y_bot_plan), (x_left_plan, y_top_plan), (dim_left_x, y_bot_plan), angle=90.0)
    _add_native_dim(msp, (x_right_plan, y_bot_plan), (x_right_plan, y_top_plan), (dim_right_x, y_bot_plan), angle=90.0)

    # 10. Local structural dimensions (centered dimtad=0 & compact dimtxt_mm=1.35 for tight interior bays)
    for ld in vp.get("local_dims", []):
        p1_w = (ox + ld["p1"][0] * 1000.0, oy + ld["p1"][1] * 1000.0)
        p2_w = (ox + ld["p2"][0] * 1000.0, oy + ld["p2"][1] * 1000.0)
        base_w = (ox + ld["base"][0] * 1000.0, oy + ld["base"][1] * 1000.0)
        rot_ld = float(ld.get("rot", 0.0))
        default_tad = 0 if (rot_ld == 90.0 and ld["p1"][0] > 10.0) else 1
        _add_native_dim(
            msp,
            p1_w,
            p2_w,
            base_w,
            angle=rot_ld,
            dimtxt_mm=float(ld.get("dimtxt_mm", 1.35)),
            text_override=str(ld.get("text", "")),
            dimtad=int(ld.get("dimtad", default_tad)),
            text_shift_x=float(ld.get("text_shift_x", 0.0)),
            text_shift_y=float(ld.get("text_shift_y", 0.0)),
        )

    # 10b. Automatic 2-axis column edge setout dimensions (`DCE_Setout`, Rule 12d / G8.06)
    if vp.get("auto_column_setout_dims") and vp.get("columns"):
        gx_coords_w = [ox + float(gm) * 1000.0 for _, gm in active_x]
        gy_coords_w = [oy + float(gm) * 1000.0 for _, gm in active_y]
        seen_x_setout: set = set()
        seen_y_setout: set = set()
        for col in vp.get("columns", []):
            ckind = str(col.get("kind", "RC")).upper()
            if "STOP" in ckind or "STEEL" in ckind:
                continue
            cx0 = ox + float(col["x0"]) * 1000.0
            cy0 = oy + float(col["y0"]) * 1000.0
            cx1 = ox + float(col["x1"]) * 1000.0
            cy1 = oy + float(col["y1"]) * 1000.0
            cx_mid = (cx0 + cx1) / 2.0
            cy_mid = (cy0 + cy1) / 2.0
            if gx_coords_w:
                gx_near = min(gx_coords_w, key=lambda gx: abs(gx - cx_mid))
                is_bot_side = abs(cy_mid - y_bot_plan) <= abs(cy_mid - y_top_plan)
                base_y_set = (y_bot_plan - 430.0) if is_bot_side else (y_top_plan + 330.0)
                for face_x in (cx0, cx1):
                    dx_off = abs(face_x - gx_near)
                    if 100.0 <= dx_off <= 600.0:
                        k_x = (round(gx_near), is_bot_side, round(face_x))
                        if k_x not in seen_x_setout:
                            seen_x_setout.add(k_x)
                            _add_native_dim(
                                msp,
                                (min(gx_near, face_x), cy_mid),
                                (max(gx_near, face_x), cy_mid),
                                (min(gx_near, face_x), base_y_set),
                                angle=0.0,
                                layer="DCE_Setout",
                                dimtxt_mm=1.10,
                                dimtad=1,
                            )
            if gy_coords_w:
                gy_near = min(gy_coords_w, key=lambda gy: abs(gy - cy_mid))
                base_x_set = cx0 - 420.0
                for face_y in (cy0, cy1):
                    dy_off = abs(face_y - gy_near)
                    if 100.0 <= dy_off <= 600.0:
                        k_y = (round(gy_near), round(dy_off))
                        if k_y not in seen_y_setout:
                            seen_y_setout.add(k_y)
                            _add_native_dim(
                                msp,
                                (cx_mid, min(gy_near, face_y)),
                                (cx_mid, max(gy_near, face_y)),
                                (base_x_set, min(gy_near, face_y)),
                                angle=90.0,
                                layer="DCE_Setout",
                                dimtxt_mm=1.10,
                                dimtad=1,
                            )

    # 11. Viewport Title + Underline + Scale
    tpos = vp.get("title_pos_mm")
    cx_title = float(tpos[0]) if tpos else (x_left_plan + x_right_plan) / 2.0
    title_y = float(tpos[1]) if tpos else (y_bot_plan - 3950.0)
    title_txt = str(vp["title"])
    _add_text(msp, title_txt, cx_title, title_y, 330.0, layer="DCE_TKT-TEXT")
    half_ul = max(2500.0, len(title_txt) * 140.0)
    msp.add_line((cx_title - half_ul, title_y - 250.0), (cx_title + half_ul, title_y - 250.0), dxfattribs={"layer": "DCE_TKT-TEXT"})
    _add_text(msp, str(vp.get("scale_label", "TL: 1/100")), cx_title, title_y - 530.0, 220.0, layer="DCE_TKT-TEXT")

    # 11b. Optional bottom-left viewport schedule (e.g. BẢNG THỐNG KÊ CỌC / ĐÀI MÓNG / CỘT)
    if vp.get("left_table"):
        lt_spec = dict(vp["left_table"])
        hdrs_lt = [str(h).strip().upper() for h in lt_spec.get("headers", [])]
        if vp.get("columns") and hdrs_lt and hdrs_lt[0] == "CỘT" and not lt_spec.get("keep_stopped_rows"):
            active_marks = {
                str(c.get("mark", "")).strip()
                for c in vp["columns"]
                if "STOP" not in str(c.get("kind", "")).upper()
            }
            if active_marks:
                lt_spec["rows"] = [r for r in lt_spec.get("rows", []) if str(r[0]).strip() in active_marks]
        _render_left_table(engine, lt_spec)

    # 12. Right-hand GHI CHÚ box (optional; supports default top-right or bottom_right)
    note_x0 = max(bubble_right_cx + 750.0, 28500.0)
    note_x1 = 36300.0
    note_box = vp.get("notes_box") or {}
    entries = note_box.get("entries", [])
    box_top_y = y_top_plan - 500.0
    box_bot_y = box_top_y
    if entries:
        if isinstance(note_box.get("x_range_mm"), (list, tuple)) and len(note_box["x_range_mm"]) == 2:
            note_x0 = float(note_box["x_range_mm"][0])
            note_x1 = float(note_box["x_range_mm"][1])
        row_h = 560.0
        total_box_h = 680.0 + len(entries) * row_h + 220.0
        if str(note_box.get("position", "")).lower() == "bottom_right":
            box_bot_y = float(note_box.get("y_bot_mm", 650.0))
            box_top_y = box_bot_y + total_box_h
        else:
            box_bot_y = box_top_y - total_box_h
        _rect_poly(msp, note_x0, box_bot_y, note_x1, box_top_y, layer="DCE_Schedule")
        _add_text(
            msp,
            note_box.get("title", "GHI CHÚ:"),
            note_x0 + 250.0,
            box_top_y - 340.0,
            240.0,
            layer="Dce_text",
            align=TextEntityAlignment.MIDDLE_LEFT,
        )
        msp.add_line((note_x0, box_top_y - 620.0), (note_x1, box_top_y - 620.0), dxfattribs={"layer": "DCE_Schedule"})

        for r_i, ent in enumerate(entries):
            ry = box_top_y - 980.0 - r_i * row_h
            sw = str(ent.get("swatch", "NONE"))
            sw_x0, sw_x1 = note_x0 + 240.0, note_x0 + 840.0
            sw_y0, sw_y1 = ry - 150.0, ry + 150.0
            _rect_poly(msp, sw_x0, sw_y0, sw_x1, sw_y1, layer="DCE_BaoBeTong")
            if sw == "HATCH":
                h = msp.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
                h.set_pattern_fill("ANSI31", scale=45.0, angle=45.0)
                h.paths.add_polyline_path([(sw_x0, sw_y0), (sw_x1, sw_y0), (sw_x1, sw_y1), (sw_x0, sw_y1)], is_closed=True)
            elif sw == "SOLID_DOT":
                h = msp.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
                h.set_pattern_fill("ANSI37", scale=45.0, angle=45.0)
                h.paths.add_polyline_path([(sw_x0, sw_y0), (sw_x1, sw_y0), (sw_x1, sw_y1), (sw_x0, sw_y1)], is_closed=True)
            elif sw == "DASH":
                h = msp.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
                h.set_pattern_fill("DASH", scale=55.0, angle=0.0)
                h.paths.add_polyline_path([(sw_x0, sw_y0), (sw_x1, sw_y0), (sw_x1, sw_y1), (sw_x0, sw_y1)], is_closed=True)

            engine._add_fitted_table_text(
                str(ent["text"]),
                note_x0 + 1000.0,
                ry,
                max_width=(note_x1 - note_x0 - 1150.0),
                height=175.0,
                layer="Dce_text",
                align=TextEntityAlignment.MIDDLE_LEFT,
            )

    return {
        "vp_id": vp_id,
        "note_x0": note_x0,
        "note_x1": note_x1,
        "box_bot_y": box_bot_y,
        "cols": vp.get("columns", []),
        "beams": vp.get("beams", []),
        "pile_blocks": pile_block_cnt,
        "column_blocks": col_block_cnt,
        "axis_blocks": len(active_x) * 2 + len(active_y) * 2,
    }


def _render_compact_schedule_box(engine, sheet_spec: Dict[str, Any], project: Dict[str, Any], x0: float, x1: float, y_top: float) -> None:
    """Render concise CỘT - DẦM summary table on DCE_Schedule cleanly under BOT GHI CHÚ."""
    msp = engine.msp
    # Collect unique active column & beam marks on this sheet cleanly without nested parens
    col_rows: Dict[str, str] = {}
    beam_rows: Dict[str, str] = {}
    for vp in sheet_spec.get("viewports", []):
        for c in vp.get("columns", []):
            suffix = " (Dừng)" if c.get("kind") == "RC_STOPPED" else (" (Thép H)" if c.get("kind") == "STEEL_H" else "")
            col_rows[str(c["mark"])] = f"{c.get('b_mm', 200)}x{c.get('h_mm', 200)}{suffix}"
        for b in vp.get("beams", []):
            beam_rows[str(b["mark"])] = str(b.get("size", "200x300"))

    summary_rows: List[Tuple[str, str, str]] = [
        # concrete_grade absent -> visible "—" (never fabricate a grade — AGENTS §4).
        # The `standard` default is this DCE Pro system's own convention (TCVN-based),
        # not project data, so it stays.
        ("BÊ TÔNG", str(project.get("concrete_grade") or "—"), project.get("standard", "TCVN 5574:2018")),
    ]
    for mk, desc in list(col_rows.items())[:5]:
        summary_rows.append(("CỘT", mk, desc))
    for mk, desc in list(beam_rows.items())[:6]:
        summary_rows.append(("DẦM", mk, desc))

    row_h = 340.0
    hdr_h = 400.0
    total_h = hdr_h + len(summary_rows) * row_h
    y_bot = max(650.0, y_top - total_h)
    if y_top - y_bot < 1600.0:
        return  # Not enough clean height below BOT GHI CHÚ

    _rect_poly(msp, x0, y_bot, x1, y_top, layer="DCE_Schedule")
    msp.add_line((x0, y_top - hdr_h), (x1, y_top - hdr_h), dxfattribs={"layer": "DCE_Schedule"})
    engine._add_fitted_table_text(
        f"THỐNG KÊ TIẾT DIỆN ({sheet_spec['sheet_no']})",
        (x0 + x1) / 2.0,
        y_top - hdr_h / 2.0,
        max_width=(x1 - x0 - 200.0),
        height=175.0,
        layer="DCE_Schedule",
    )

    c1_x = x0 + (x1 - x0) * 0.24
    c2_x = x0 + (x1 - x0) * 0.50
    msp.add_line((c1_x, y_bot), (c1_x, y_top - hdr_h), dxfattribs={"layer": "DCE_Schedule"})
    msp.add_line((c2_x, y_bot), (c2_x, y_top - hdr_h), dxfattribs={"layer": "DCE_Schedule"})

    for i, (t1, t2, t3) in enumerate(summary_rows):
        ry_top = y_top - hdr_h - i * row_h
        ry_mid = ry_top - row_h / 2.0
        if ry_top - row_h < y_bot - 5.0:
            break
        if i > 0:
            msp.add_line((x0, ry_top), (x1, ry_top), dxfattribs={"layer": "DCE_Schedule"})
        engine._add_fitted_table_text(t1, (x0 + c1_x) / 2.0, ry_mid, c1_x - x0 - 80.0, height=135.0, layer="DCE_Schedule")
        engine._add_fitted_table_text(t2, (c1_x + c2_x) / 2.0, ry_mid, c2_x - c1_x - 80.0, height=135.0, layer="DCE_Schedule")
        engine._add_fitted_table_text(t3, (c2_x + x1) / 2.0, ry_mid, x1 - c2_x - 80.0, height=135.0, layer="DCE_Schedule")


def _render_a3_frame_title_and_keyplan(engine, sheet_spec: Dict[str, Any], project: Dict[str, Any]) -> None:
    """Draw canonical A3 Landscape frame, right-side Cat Lai Title Block, and Key Plan."""
    msp = engine.msp
    # 1. Sheet frame (0..42000 x 0..29700) & Inner border (500, 212 .. 41821, 29488)
    _rect_poly(msp, 0.0, 0.0, 42000.0, 29700.0, layer="DCE_Frame")
    _rect_poly(msp, 500.0, 212.0, 41821.0, 29488.0, layer="DCE_Frame")

    # Right Title Block vertical divider & horizontal viewport split
    tb_x0, tb_x1 = 36858.0, 41821.0
    msp.add_line((tb_x0, 212.0), (tb_x0, 29488.0), dxfattribs={"layer": "DCE_Frame"})
    msp.add_line((500.0, 14850.0), (tb_x0, 14850.0), dxfattribs={"layer": "DCE_Frame"})

    # 2. Exact Title Block Horizontal Dividers (model mm matching PDF layout)
    h_ys = [
        955.0, 1693.0, 3012.0, 3662.0, 4062.0, 5211.0, 6310.0, 6778.0,
        8007.0, 9237.0, 10467.0, 11697.0, 13445.0, 16595.0, 21245.0,
    ]
    for hy in h_ys:
        msp.add_line((tb_x0, hy), (tb_x1, hy), dxfattribs={"layer": "DCE_Schedule"})

    # Vertical splits inside Title Block
    msp.add_line((39082.0, 212.0), (39082.0, 1693.0), dxfattribs={"layer": "DCE_Schedule"})
    msp.add_line((40331.0, 212.0), (40331.0, 1693.0), dxfattribs={"layer": "DCE_Schedule"})
    msp.add_line((39766.0, 6778.0), (39766.0, 11697.0), dxfattribs={"layer": "DCE_Schedule"})

    cx_tb = (tb_x0 + tb_x1) / 2.0
    w_tb = tb_x1 - tb_x0 - 240.0

    # Key Plan header strip (21245..22100) + Key Plan map cleanly scaled inside box [36950..41750, 22200..29350]
    _add_text(msp, "KEY PLAN", cx_tb, 21672.0, 240.0, layer="DCE_TKT-TEXT")
    kp_cx, kp_cy, kp_scale = 39480.0, 25800.0, 0.75
    def _kp_pt(x_val: float, y_val: float) -> Tuple[float, float]:
        return (kp_cx + (x_val - kp_cx) * kp_scale, kp_cy + (y_val - kp_cy) * kp_scale)

    for kl in project.get("key_plan_lines", []):
        p1 = _kp_pt(float(kl["p1"][0]), float(kl["p1"][1]))
        p2 = _kp_pt(float(kl["p2"][0]), float(kl["p2"][1]))
        is_dash = bool(kl.get("dash", False))
        att = {"layer": "Dce_text" if not is_dash else "DCE_NetDut", "linetype": "HIDDEN_DBIM" if is_dash else "Continuous"}
        if is_dash:
            att["ltscale"] = 0.65
        msp.add_line(p1, p2, dxfattribs=att)
    for kt in project.get("key_plan_texts", []):
        kx, ky = _kp_pt(float(kt["x"]), float(kt["y"]))
        kh = min(105.0, float(kt.get("h", 125.0)) * 0.72)
        if "ĐƯỜNG SỐ 71" in str(kt["text"]):
            kx = max(kx + 220.0, tb_x0 + 1150.0)
            kh = 86.0
        _add_text(
            msp,
            str(kt["text"]),
            kx,
            ky,
            kh,
            layer="Dce_text",
            rotation=float(kt.get("rot", 0.0)),
        )

    # Investor block (16595..21245)
    _add_text(msp, "CHỦ ĐẦU TƯ:", cx_tb, 20700.0, 250.0, layer="DCE_TKT-TEXT")
    # No fabricated parcel address (AGENTS §4): when `site_address_lines` is
    # absent, the block shows the project name / owner only, never a guessed site.
    addr_lines = [str(x) for x in project.get("site_address_lines", []) if str(x).strip()][:2]
    if addr_lines:
        engine._add_fitted_table_text(addr_lines[0], cx_tb, 17850.0, w_tb, 165.0, layer="DCE_TKT-TEXT")
    if len(addr_lines) > 1:
        engine._add_fitted_table_text(addr_lines[1], cx_tb, 17420.0, w_tb, 165.0, layer="DCE_TKT-TEXT")

    # Company block (13445..16595)
    engine._add_fitted_table_text(project.get("company", "CÔNG TY ................."), cx_tb, 15950.0, w_tb, 210.0, layer="DCE_TKT-TEXT")
    _add_text(msp, "ĐỊA CHỈ:", tb_x0 + 180.0, 13800.0, 160.0, layer="DCE_TKT-TEXT", align=TextEntityAlignment.MIDDLE_LEFT)
    _add_text(msp, "Email:", tb_x0 + 180.0, 12700.0, 160.0, layer="DCE_TKT-TEXT", align=TextEntityAlignment.MIDDLE_LEFT)
    _add_text(msp, "Tel:", tb_x0 + 180.0, 12200.0, 160.0, layer="DCE_TKT-TEXT", align=TextEntityAlignment.MIDDLE_LEFT)

    # Approval signoff rows (6778..11697)
    for y_row, lbl in [(11082.0, "GIÁM ĐỐC:"), (9852.0, "KIỂM TRA:"), (8622.0, "THIẾT KẾ:"), (7392.0, "THỂ HIỆN:")]:
        _add_text(msp, lbl, tb_x0 + 180.0, y_row, 195.0, layer="DCE_TKT-TEXT", align=TextEntityAlignment.MIDDLE_LEFT)

    # Project name & site address (4062..6778)
    _add_text(msp, "CÔNG TRÌNH:", cx_tb, 6540.0, 195.0, layer="DCE_TKT-TEXT")
    engine._add_fitted_table_text(project.get("project_name", "NHÀ Ở RIÊNG LẺ"), cx_tb, 5750.0, w_tb, 240.0, layer="DCE_TKT-TEXT")
    if addr_lines:
        engine._add_fitted_table_text(addr_lines[0], cx_tb, 4800.0, w_tb, 160.0, layer="DCE_TKT-TEXT")
    if len(addr_lines) > 1:
        engine._add_fitted_table_text(addr_lines[1], cx_tb, 4380.0, w_tb, 160.0, layer="DCE_TKT-TEXT")

    # Drawing name (1693..4062)
    _add_text(msp, "TÊN BẢN VẼ:", cx_tb, 3860.0, 185.0, layer="DCE_TKT-TEXT")
    engine._add_fitted_table_text(project.get("drawing_category", "BẢN VẼ KẾT CẤU"), cx_tb, 3335.0, w_tb, 200.0, layer="DCE_TKT-TEXT")
    engine._add_fitted_table_text(sheet_spec["title"], cx_tb, 2350.0, w_tb, 230.0, layer="DCE_TKT-TEXT")

    # Bottom 2x3 cell metadata
    _add_text(msp, "BƯỚC THIẾT KẾ:", (tb_x0 + 39082.0) / 2.0, 1324.0, 165.0, layer="DCE_TKT-TEXT")
    _add_text(msp, project.get("design_stage", "TKTC"), (39082.0 + 40331.0) / 2.0, 1324.0, 195.0, layer="DCE_TKT-TEXT")
    _add_text(msp, "KÝ HIỆU BV:", (40331.0 + tb_x1) / 2.0, 1324.0, 165.0, layer="DCE_TKT-TEXT")

    _add_text(msp, "HOÀN THÀNH:", (tb_x0 + 39082.0) / 2.0, 583.0, 165.0, layer="DCE_TKT-TEXT")
    _add_text(msp, str(project.get("year", "2026")), (39082.0 + 40331.0) / 2.0, 583.0, 200.0, layer="DCE_TKT-TEXT")
    _add_text(msp, sheet_spec["sheet_no"], (40331.0 + tb_x1) / 2.0, 583.0, 235.0, layer="DCE_TKT-TEXT")


def _render_open_keyplan_only(
    engine,
    project: Dict[str, Any],
    zones_wcs: Optional[Dict[str, List[Tuple[float, float, float, float]]]] = None,
) -> None:
    """Render dynamic Key Plan vectors cleanly inside the `KEYPLAN` zone without redrawing TitleBlock."""
    msp = engine.msp
    kx0, ky0, kx1, ky1 = (
        zones_wcs["KEYPLAN"][0]
        if (zones_wcs and zones_wcs.get("KEYPLAN"))
        else _DEFAULT_FORM02_ZONES["KEYPLAN"]
    )
    kp_cx = (kx0 + kx1) / 2.0 + 130.0
    kp_cy = (ky0 + ky1) / 2.0 + 25.0
    def_cx, def_cy = 39480.0, 25800.0
    kp_scale = 0.75

    def _kp_pt(x_val: float, y_val: float) -> Tuple[float, float]:
        return (kp_cx + (x_val - def_cx) * kp_scale, kp_cy + (y_val - def_cy) * kp_scale)

    for kl in project.get("key_plan_lines", []):
        p1 = _kp_pt(float(kl["p1"][0]), float(kl["p1"][1]))
        p2 = _kp_pt(float(kl["p2"][0]), float(kl["p2"][1]))
        is_dash = bool(kl.get("dash", False))
        att = {"layer": "Dce_text" if not is_dash else "DCE_NetDut", "linetype": "HIDDEN_DBIM" if is_dash else "Continuous"}
        if is_dash:
            att["ltscale"] = 0.65
        msp.add_line(p1, p2, dxfattribs=att)

    for kt in project.get("key_plan_texts", []):
        kx, ky = _kp_pt(float(kt["x"]), float(kt["y"]))
        kh = min(105.0, float(kt.get("h", 125.0)) * 0.72)
        if "ĐƯỜNG SỐ 71" in str(kt["text"]):
            kx = max(kx + 220.0, kx0 + 1060.0)
            kh = 86.0
        _add_text(
            msp,
            str(kt["text"]),
            kx,
            ky,
            kh,
            layer="Dce_text",
            rotation=float(kt.get("rot", 0.0)),
        )


def _hide_zone_guide_layers_for_export(doc: ezdxf.document.Drawing) -> None:
    """Turn off template guide boxes (`DCE_ZONE_*`) in exported deliverable while preserving entities."""
    for ly in doc.layers:
        lname = ly.dxf.name.upper()
        if lname.startswith("DCE_ZONE_"):
            try:
                ly.dxf.plot = 0
                ly.off()
            except Exception:
                pass


def render_multiview_a3_sheet(
    engine,
    sheet_spec: Dict[str, Any],
    project: Dict[str, Any],
    template_mode: Optional[str] = None,
    form_validation: Optional[Dict[str, Any]] = None,
    use_dce_blocks: Optional[bool] = None,
) -> Any:
    """Populate `engine.doc` / `engine.msp` with a single dual-viewport A3 sheet."""
    _ensure_a3_layers_and_styles(engine.doc)

    eff_mode = str(template_mode or getattr(engine, "template_mode", "legacy") or "legacy").lower()
    eff_blocks = bool(use_dce_blocks) if use_dce_blocks is not None else (eff_mode == "open")

    engine.FRAME_X0, engine.FRAME_Y0 = 0.0, 0.0
    engine.FRAME_W = float(project.get("frame_mm", [42000.0, 29700.0])[0])
    engine.FRAME_H = float(project.get("frame_mm", [42000.0, 29700.0])[1])
    engine.print_scale = float(project.get("scale", 100.0))
    engine.sheet_type = str(sheet_spec.get("sheet_no", "KC.13"))

    zones_wcs = (form_validation or {}).get("zones_wcs", {})

    if eff_mode == "open":
        from cad_block_adapters import (
            insert_or_update_titleblock,
            mark_new_entities_owned,
            purge_agent_owned_entities,
            snapshot_msp_handles,
        )

        # Keep 100% of user's frame, logos, edited styles, and TitleBlock; purge ONLY prior Agent entities
        purge_agent_owned_entities(engine.doc, engine.msp)
        before_handles = snapshot_msp_handles(engine.msp)

        import textwrap as _tw
        addr_lines = [str(x) for x in project.get("site_address_lines", []) if str(x).strip()]
        if len(addr_lines) >= 2:
            dia_diem_1, dia_diem_2 = addr_lines[0], addr_lines[1]
        elif len(addr_lines) == 1:
            wrapped_addr = _tw.wrap(addr_lines[0], width=34) or [addr_lines[0]]
            dia_diem_1 = wrapped_addr[0]
            dia_diem_2 = " ".join(wrapped_addr[1:]) if len(wrapped_addr) > 1 else ""
        else:
            dia_diem_1, dia_diem_2 = "", ""
        tb_name = str((form_validation or {}).get("titleblock_block") or "DCE_TITLEBLOCK_A3")
        tb_values = {
            "CHU_DAU_TU": project.get("investor", ""),
            "DIA_DIEM": dia_diem_1,
            "DIA_DIEM_2": dia_diem_2,
            "CONG_TY": project.get("company", "CÔNG TY ................."),
            "GIAM_DOC": project.get("director", ""),
            "KIEM_TRA": project.get("reviewer", ""),
            "THIET_KE": project.get("designer", ""),
            "THE_HIEN": project.get("drafter", ""),
            "TEN_CONG_TRINH": project.get("project_name", "NHÀ Ở RIÊNG LẺ"),
            "HANG_MUC": project.get("drawing_category", "BẢN VẼ KẾT CẤU"),
            "TEN_BAN_VE": sheet_spec.get("title", ""),
            "BUOC_TK": project.get("design_stage", "TKTC"),
            "NAM": str(project.get("year", "2026")),
            "KY_HIEU": str(sheet_spec.get("sheet_no", "KC.02")),
            "TY_LE": f"1/{int(project.get('scale', 100))}",
        }
        tb_res = insert_or_update_titleblock(
            engine.doc,
            engine.msp,
            block_name=tb_name,
            values=tb_values,
            mark_owned=False,
        )
        _render_open_keyplan_only(engine, project, zones_wcs=zones_wcs)
    else:
        # Clear template modelspace cleanly (legacy default)
        for ent in list(engine.msp):
            engine.msp.delete_entity(ent)
        _render_a3_frame_title_and_keyplan(engine, sheet_spec, project)
        tb_res = {"mode": "legacy_static_titleblock", "block_name": None}

    bot_meta = None
    vp_stats: List[Dict[str, Any]] = []
    for vp in sheet_spec.get("viewports", []):
        meta = _render_viewport(
            engine,
            vp,
            project,
            sheet_spec["sheet_no"],
            use_dce_blocks=eff_blocks,
            zone_bboxes=zones_wcs if eff_mode == "open" else None,
        )
        vp_stats.append({
            "vp_id": meta["vp_id"],
            "pile_blocks": meta["pile_blocks"],
            "column_blocks": meta["column_blocks"],
            "axis_blocks": meta["axis_blocks"],
        })
        if str(vp.get("slot", "")).upper() == "BOT":
            bot_meta = meta

    if bot_meta is not None and not sheet_spec.get("hide_default_col_beam_schedule"):
        _render_compact_schedule_box(
            engine,
            sheet_spec,
            project,
            bot_meta["note_x0"],
            bot_meta["note_x1"],
            bot_meta["box_bot_y"] - 350.0,
        )

    if eff_mode == "open":
        owned_cnt = mark_new_entities_owned(engine.msp, before_handles, role="A3_MULTIVIEW")
        _hide_zone_guide_layers_for_export(engine.doc)
        engine.block_evidence = {
            "use_dce_blocks": eff_blocks,
            "titleblock": tb_res,
            "viewports": vp_stats,
            "agent_owned_entities": owned_cnt,
            "preserve_user_styles": True,
        }

    # Update header limits cleanly so CAD zoom extents matches A3 bounds
    try:
        engine.doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        engine.doc.header["$EXTMAX"] = (engine.FRAME_W, engine.FRAME_H, 0.0)
        engine.doc.header["$LIMMIN"] = (0.0, 0.0)
        engine.doc.header["$LIMMAX"] = (engine.FRAME_W, engine.FRAME_H)
    except Exception:
        pass
    return engine


def export_multiview_a3_sheet(
    output_dxf_path: str,
    model: Dict[str, Any],
    sheet_index: int = 0,
    sheet_no: Optional[str] = None,
    template_path: Optional[str] = None,
    v6: bool = True,
    element_registry: Optional[Any] = None,
    tag_overrides: Optional[Dict[Any, Any]] = None,
    dry_run: bool = False,
    template_mode: Optional[str] = None,
    form_id: Optional[str] = None,
    project_dir: Optional[str] = None,
    use_dce_blocks: Optional[bool] = None,
    full_evidence: bool = False,
    purge_unused: bool = True,
) -> Any:
    """Export one A3 multi-view sheet using `DcePlanEngine` + `.dce_audit.json` sidecar."""
    _cad_dir = str(Path(__file__).resolve().parent)
    if _cad_dir not in sys.path:
        sys.path.insert(0, _cad_dir)
    from cad_plan_engine import DcePlanEngine

    project = dict(model.get("project", {}))
    sheets = list(model.get("sheets", []))
    if not sheets and "viewports" in model:
        sheets = [model]
    if not sheets:
        raise ValueError("Multi-view model must contain 'sheets' or 'viewports'.")

    target_key = (sheet_no or model.get("active_sheet_no") or "").strip().upper()
    if not target_key and output_dxf_path:
        stem = Path(output_dxf_path).stem.upper()
        for sh in sheets:
            sh_no = str(sh.get("sheet_no", "")).upper()
            sh_fn = Path(str(sh.get("filename", ""))).stem.upper()
            if stem == sh_fn or (sh_no and sh_no in stem):
                target_key = sh_no or stem
                break

    if target_key:
        norm = target_key.replace("-", ".")
        matched = [
            sh for sh in sheets
            if str(sh.get("sheet_no", "")).upper().replace("-", ".") == norm
            or Path(str(sh.get("filename", ""))).stem.upper().replace("-", ".") == norm
        ]
        if not matched:
            raise ValueError(f"Sheet '{target_key}' not found in multi-view model.")
        sheet_spec = matched[0]
    else:
        sheet_spec = sheets[int(sheet_index)]

    eff_mode = str(template_mode or project.get("template_mode") or "legacy").lower()
    eff_template_path = template_path
    form_val_dict: Optional[Dict[str, Any]] = None
    template_contract_ev: Optional[Dict[str, Any]] = None
    zone_ev: Optional[Dict[str, Any]] = None

    if eff_mode == "open":
        from cad_form_contract import resolve_form_paths, validate_open_form

        eff_form_id = form_id or project.get("form_id") or "FORM_02_MULTIVIEW_A3_BTCT"
        eff_proj_dir = project_dir or project.get("project_dir")
        res = resolve_form_paths(
            form_id=eff_form_id,
            project_dir=eff_proj_dir,
            explicit_form_path=template_path,
        )
        if res.dxf_path is None:
            raise FileNotFoundError(
                f"Open Form '{eff_form_id}' not found across 3-tier hierarchy: {res.searched_paths}"
            )
        val = validate_open_form(
            res.dxf_path,
            manifest_path=res.manifest_path,
            form_id=eff_form_id,
            tier=res.tier,
        )
        if not val.valid:
            raise ValueError(f"Open Form Contract validation failed ({eff_form_id}): {val.errors}")
        form_val_dict = val.to_dict()
        eff_template_path = str(res.dxf_path)
        template_contract_ev = {
            "template_mode": "open",
            "form_id": val.form_id,
            "tier": val.tier,
            "dxf_path": val.dxf_path,
            "manifest_path": val.manifest_path,
            "dxf_version": val.dxf_version,
            "source_space": val.source_space,
            "roundtrip_status": val.roundtrip_status,
            "ucs_ok": val.ucs_ok,
            "titleblock_block": val.titleblock_block,
            "titleblock_tags": val.titleblock_tags,
            "extra_title_tags": val.extra_title_tags,
            "warnings": val.warnings,
            "inventory": val.inventory,
        }
        zone_ev = {"zones_wcs": val.zones_wcs}

    engine_model = dict(project)
    engine_model.update({
        "sheet": sheet_spec,
        "sheet_scale_label": f"1/{int(project.get('scale', 100))}",
        "multi_view_a3": True,
    })

    if v6 and element_registry is None:
        try:
            from cad_element_registry import CadElementRegistry
            element_registry = CadElementRegistry(
                project_name=str(project.get("project_name", "MULTIVIEW_A3"))
            )
        except Exception:
            element_registry = None

    engine = DcePlanEngine(
        engine_model,
        template_path=eff_template_path,
        v6=v6,
        element_registry=element_registry,
        tag_overrides=tag_overrides,
        preserve_modelspace=(eff_mode == "open"),
        template_mode=eff_mode,
        template_contract=template_contract_ev,
        zone_evidence=zone_ev,
        full_evidence=full_evidence,
    )
    engine.setup()
    render_multiview_a3_sheet(
        engine,
        sheet_spec,
        project,
        template_mode=eff_mode,
        form_validation=form_val_dict,
        use_dce_blocks=use_dce_blocks,
    )

    if purge_unused:
        from cad_block_adapters import purge_unused_blocks
        purge_unused_blocks(engine.doc)

    if not dry_run:
        out_p = Path(output_dxf_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if v6:
            engine.save_v6(str(out_p))
        else:
            engine.save(str(out_p))
    return engine

