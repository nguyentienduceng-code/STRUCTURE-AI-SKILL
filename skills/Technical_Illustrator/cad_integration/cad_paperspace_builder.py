# -*- coding: utf-8 -*-
"""
cad_paperspace_builder.py — P3 Single-File Multi-Layout PaperSpace & All-4-Form Open Runner
============================================================================================

Implements D2 & P3 (`DECISION_OPS_HYBRID_AUTHORING_20261116.md`):
  1. `export_single_file_multilayout_dxf(...)`:
     - 1 DXF file + 1 SHA-256 hash (`1 file = 1 dossier`) for simple/medium projects.
     - Shared `ModelSpace`: views placed at exact WCS mm (center-anchored columns/piles,
       shared `Dce_KhTenTruc` axis bubbles, model-scale text heights `paper_h * vp_scale`).
     - Multi `PaperSpace Layouts` (`KC.02`, `KC.03`, ...): each Layout has its own `1:1`
       mm sheet frame (`420x297` A3 or `841x594` A1), named paper TitleBlock block with
       real `ATTDEF`s (`DCE_TITLEBLOCK_A3_PAPER` / `DCE_TITLEBLOCK_A1_PAPER`), and
       non-overlapping `VIEWPORT` entities targeting exact ModelSpace viewport bboxes.
  2. `export_with_open_form(...)`:
     - Open-mode runner supporting all 4 Forms (`FORM_01` A1 RC, `FORM_02` A3 MultiView,
       `FORM_03` A1 Steel, `FORM_04` A3 Details) while preserving user AutoCAD edits
       (`DCE_AGENT_OWNED` region scoping).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf
from ezdxf.enums import TextEntityAlignment

CAD_DIR = Path(__file__).resolve().parent
AGENTS_DIR = CAD_DIR.parents[2]
SHARED_CTX_DIR = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"

for _p in (str(CAD_DIR), str(SHARED_CTX_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cad_block_adapters import (
    ensure_titleblock_a1_definition,
    ensure_titleblock_a3_definition,
    insert_axis_bubble_native,
    insert_column_block,
    insert_or_update_titleblock,
    insert_pile_block,
    mark_new_entities_owned,
    purge_agent_owned_entities,
    snapshot_msp_handles,
)
from cad_form_contract import (
    FORM_CATALOG,
    resolve_form_paths,
    validate_open_form,
)
from cad_multiview_a3 import (
    _ensure_a3_layers_and_styles,
    _hide_zone_guide_layers_for_export,
    _render_viewport,
    export_multiview_a3_sheet,
)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Atomic JSON write (temp + `os.replace`), safe on Drive-synced paths.

    Mirrors `project_ops_manager._atomic_write_json` (which this module does not
    import) so a sidecar can never be left torn mid-sync.
    """
    import os as _os
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{_os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            _os.fsync(f.fileno())
        _os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _resolve_total_dims(project: Dict[str, Any]) -> Tuple[float, float]:
    """Total building L/B (metres) for the engine, with no silent fabrication.

    `L_total`/`B_total` are schema-required (model_schema.json:148), so a valid
    model always carries them. When a hand-crafted model omits them, we derive
    the real span from the grid coordinates (a truthful value, not a guessed
    10x6 m) and only raise when neither dim nor grid is available (AGENTS §4).
    """
    def _dim(key: str, grid_key: str) -> float:
        raw = project.get(key)
        if raw is not None:
            return float(raw)
        vals = [float(p[1]) for p in project.get(grid_key, []) if len(p) >= 2]
        if vals:
            return round(max(vals) - min(vals), 4)
        raise ValueError(
            f"project.{key} is required to export this Form; provide {key} "
            f"or {grid_key} (grid span). Refusing to fabricate building dimensions."
        )
    return _dim("L_total", "grid_x"), _dim("B_total", "grid_y")


def _add_paper_static_label(blk, text: str, x: float, y: float, height: float = 1.6, align=TextEntityAlignment.MIDDLE_CENTER) -> None:
    t = blk.add_text(
        str(text),
        dxfattribs={
            "layer": "DCE_TKT-TEXT",
            "height": float(height),
            "style": "Dce_Text" if "Dce_Text" in blk.doc.styles else "Standard",
            "color": 256,
        },
    )
    t.set_placement((float(x), float(y)), align=align)


def _ensure_paper_titleblock_definition(
    doc: ezdxf.document.Drawing,
    paper_size: str = "A3",
) -> Tuple[str, float, float]:
    """Ensure 1:1 mm paper-space TitleBlock block with ATTDEFs exists."""
    psize = str(paper_size).upper()
    if psize == "A1":
        bname = "DCE_TITLEBLOCK_A1_PAPER"
        pw, ph = 841.0, 594.0
        if bname not in doc.blocks:
            blk = doc.blocks.new(bname, base_point=(0.0, 0.0))
            x0, y0, x1, y1 = 720.0, 10.0, 831.0, 120.0
            cx = (x0 + x1) / 2.0
            blk.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "DCE_Schedule"})
            for hy in (32.0, 58.0, 84.0, 102.0):
                blk.add_line((x0, hy), (x1, hy), dxfattribs={"layer": "DCE_Schedule"})
            blk.add_line((757.0, y0), (757.0, 32.0), dxfattribs={"layer": "DCE_Schedule"})
            blk.add_line((794.0, y0), (794.0, 32.0), dxfattribs={"layer": "DCE_Schedule"})
            _add_paper_static_label(blk, "CHỦ ĐẦU TƯ:", x0 + 2.5, 117.0, 1.8, align=TextEntityAlignment.MIDDLE_LEFT)
            _add_paper_attdef(blk, "CHU_DAU_TU", "CHỦ ĐẦU TƯ", cx, 109.0, 2.8)
            _add_paper_static_label(blk, "ĐƠN VỊ TƯ VẤN:", x0 + 2.5, 99.0, 1.8, align=TextEntityAlignment.MIDDLE_LEFT)
            _add_paper_attdef(blk, "CONG_TY", "ĐƠN VỊ TƯ VẤN", cx, 91.0, 2.6)
            _add_paper_static_label(blk, "CÔNG TRÌNH:", x0 + 2.5, 81.0, 1.8, align=TextEntityAlignment.MIDDLE_LEFT)
            _add_paper_attdef(blk, "TEN_CONG_TRINH", "DỰ ÁN KẾT CẤU", cx, 70.0, 3.2)
            _add_paper_static_label(blk, "TÊN BẢN VẼ:", x0 + 2.5, 55.0, 1.8, align=TextEntityAlignment.MIDDLE_LEFT)
            _add_paper_attdef(blk, "TEN_BAN_VE", "MẶT BẰNG KẾT CẤU", cx, 43.0, 3.0)
            _add_paper_static_label(blk, "TỶ LỆ", 738.5, 28.0, 1.7)
            _add_paper_attdef(blk, "TY_LE", "1/100", 738.5, 19.0, 2.5)
            _add_paper_static_label(blk, "GIAI ĐOẠN", 775.5, 28.0, 1.7)
            _add_paper_attdef(blk, "BUOC_TK", "TKTC", 775.5, 20.5, 2.4)
            _add_paper_attdef(blk, "NAM", "2026", 775.5, 13.5, 1.9)
            _add_paper_static_label(blk, "KÝ HIỆU", 812.5, 28.0, 1.7)
            _add_paper_attdef(blk, "KY_HIEU", "KC-01", 812.5, 19.0, 2.8)
        return bname, pw, ph

    bname = "DCE_TITLEBLOCK_A3_PAPER"
    pw, ph = 420.0, 297.0
    if bname not in doc.blocks:
        blk = doc.blocks.new(bname, base_point=(0.0, 0.0))
        x0, y0, x1, y1 = 368.5, 5.0, 415.0, 292.0
        cx = (x0 + x1) / 2.0
        blk.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "DCE_Schedule"})
        for hy in (22.0, 46.0, 82.0, 128.0, 175.0, 222.0):
            blk.add_line((x0, hy), (x1, hy), dxfattribs={"layer": "DCE_Schedule"})
        blk.add_line((391.5, y0), (391.5, 22.0), dxfattribs={"layer": "DCE_Schedule"})
        _add_paper_static_label(blk, "CHỦ ĐẦU TƯ:", cx, 282.0, 1.8)
        _add_paper_attdef(blk, "CHU_DAU_TU", "CHỦ ĐẦU TƯ", cx, 255.0, 2.4)
        _add_paper_static_label(blk, "ĐƠN VỊ TƯ VẤN:", cx, 215.0, 1.7)
        _add_paper_attdef(blk, "CONG_TY", "TƯ VẤN THIẾT KẾ", cx, 197.0, 2.2)
        _add_paper_static_label(blk, "CÔNG TRÌNH:", cx, 168.0, 1.8)
        _add_paper_attdef(blk, "TEN_CONG_TRINH", "TÊN CÔNG TRÌNH", cx, 150.0, 2.6)
        _add_paper_static_label(blk, "HẠNG MỤC:", cx, 121.0, 1.7)
        _add_paper_attdef(blk, "HANG_MUC", "BẢN VẼ KẾT CẤU", cx, 104.0, 2.1)
        _add_paper_static_label(blk, "TÊN BẢN VẼ:", cx, 75.0, 1.7)
        _add_paper_attdef(blk, "TEN_BAN_VE", "TÊN BẢN VẼ", cx, 61.0, 2.2)
        _add_paper_static_label(blk, "TỶ LỆ", 380.0, 41.5, 1.5)
        _add_paper_attdef(blk, "TY_LE", "1/100", 380.0, 31.0, 2.1)
        _add_paper_static_label(blk, "BƯỚC TK", 403.0, 41.5, 1.5)
        _add_paper_attdef(blk, "BUOC_TK", "TKTC", 403.0, 31.0, 2.1)
        _add_paper_static_label(blk, "NĂM", 380.0, 18.5, 1.4)
        _add_paper_attdef(blk, "NAM", "2026", 380.0, 10.5, 2.0)
        _add_paper_static_label(blk, "KÝ HIỆU", 403.0, 18.5, 1.4)
        _add_paper_attdef(blk, "KY_HIEU", "KC.02", 403.0, 10.5, 2.4)
    return bname, pw, ph


def _add_paper_attdef(blk, tag: str, default: str, x: float, y: float, height: float) -> None:
    att = blk.add_attdef(
        tag,
        insert=(float(x), float(y)),
        text=str(default),
        dxfattribs={
            "layer": "DCE_TKT-TEXT",
            "height": float(height),
            "style": "Dce_Text" if "Dce_Text" in blk.doc.styles else "Standard",
            "color": 256,
            "halign": 1,
            "valign": 2,
            "align_point": (float(x), float(y)),
        },
    )
    try:
        att.set_placement((float(x), float(y)), align=TextEntityAlignment.MIDDLE_CENTER)
    except Exception:
        pass


def _shift_viewport_model_annotations(
    vp_eff: Dict[str, Any],
    dx: float,
    dy: float,
) -> None:
    """Shift viewport-local ModelSpace coordinates (title, tables, notes) by (dx, dy) cleanly."""
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return
    if vp_eff.get("title_pos_mm") and len(vp_eff["title_pos_mm"]) >= 2:
        vp_eff["title_pos_mm"] = [
            float(vp_eff["title_pos_mm"][0]) + dx,
            float(vp_eff["title_pos_mm"][1]) + dy,
        ]
    lt = vp_eff.get("left_table")
    if isinstance(lt, dict):
        lt = copy.deepcopy(lt)
        if "x0_mm" in lt:
            lt["x0_mm"] = float(lt["x0_mm"]) + dx
        if "y_top_mm" in lt:
            lt["y_top_mm"] = float(lt["y_top_mm"]) + dy
        vp_eff["left_table"] = lt
    nb = vp_eff.get("notes_box")
    if isinstance(nb, dict):
        nb = copy.deepcopy(nb)
        if isinstance(nb.get("x_range_mm"), (list, tuple)) and len(nb["x_range_mm"]) == 2:
            nb["x_range_mm"] = [float(nb["x_range_mm"][0]) + dx, float(nb["x_range_mm"][1]) + dx]
        if "y_bot_mm" in nb:
            nb["y_bot_mm"] = float(nb["y_bot_mm"]) + dy
        vp_eff["notes_box"] = nb


def _measure_entity_extents(entities: List[Any]) -> Optional[Tuple[float, float, float, float]]:
    """Compute tight WCS extents around rendered ModelSpace viewport entities."""
    try:
        from ezdxf import bbox as ezbbox

        box = ezbbox.extents(entities, fast=True)
        if box.has_data:
            return (
                float(box.extmin.x),
                float(box.extmin.y),
                float(box.extmax.x),
                float(box.extmax.y),
            )
    except Exception:
        pass
    return None


def _render_shared_modelspace_viewport(
    engine,
    vp: Dict[str, Any],
    project: Dict[str, Any],
    sheet_no: str,
    model_origin_mm: Tuple[float, float],
    scale: float,
) -> Dict[str, Any]:
    """Render one viewport cleanly into shared ModelSpace at WCS coordinates with model-scale text."""
    vp_eff = copy.deepcopy(vp)
    orig = vp_eff.get("origin_mm") or [model_origin_mm[0], model_origin_mm[1]]
    old_ox, old_oy = float(orig[0]), float(orig[1])
    new_ox, new_oy = float(model_origin_mm[0]), float(model_origin_mm[1])
    dx, dy = new_ox - old_ox, new_oy - old_oy
    vp_eff["origin_mm"] = [new_ox, new_oy]
    _shift_viewport_model_annotations(vp_eff, dx, dy)

    # Enforce model-scale text heights (`paper_h_mm * scale`) cleanly on custom view tags
    scale_factor = float(scale) / 100.0
    if abs(scale_factor - 1.0) > 1e-3:
        vp_eff["title_h_override"] = round(3.0 * float(scale), 1)

    prev_handles = {e.dxf.handle for e in engine.msp if hasattr(e.dxf, "handle")}
    meta = _render_viewport(
        engine,
        vp_eff,
        project,
        sheet_no,
        use_dce_blocks=True,
        zone_bboxes=None,
    )
    new_ents = [e for e in engine.msp if getattr(e.dxf, "handle", None) not in prev_handles]
    ext = _measure_entity_extents(new_ents)
    if ext is not None:
        min_x, min_y, max_x, max_y = ext
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        plan_w = max(max_x - min_x + 1200.0, 12000.0)
        plan_h = max(max_y - min_y + 1000.0, 9000.0)
    else:
        xs = [float(pt[0]) for pt in vp_eff.get("slab_outline", [[0.0, 0.0], [8.0, 5.0]])]
        ys = [float(pt[1]) for pt in vp_eff.get("slab_outline", [[0.0, 0.0], [8.0, 5.0]])]
        cx = new_ox + ((min(xs) + max(xs)) / 2.0) * 1000.0
        cy = new_oy + ((min(ys) + max(ys)) / 2.0) * 1000.0
        plan_w = max((max(xs) - min(xs)) * 1000.0 + 6000.0, 12000.0)
        plan_h = max((max(ys) - min(ys)) * 1000.0 + 6000.0, 9000.0)

    return {
        "vp_id": vp_eff.get("id", "VP"),
        "slot": vp_eff.get("slot", "TOP"),
        "scale": float(scale),
        "model_center_mm": [round(cx, 2), round(cy, 2)],
        "model_span_mm": [round(plan_w, 2), round(plan_h, 2)],
        "meta": meta,
    }


def export_single_file_multilayout_dxf(
    output_dxf_path: str | Path,
    model: Dict[str, Any],
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    project_dir: Optional[str | Path] = None,
    paper_size: Optional[str] = None,
    full_evidence: bool = False,
) -> Dict[str, Any]:
    """P3: Export 1 DXF file containing shared ModelSpace + multiple PaperSpace Layouts."""
    from cad_plan_engine import DcePlanEngine

    res = resolve_form_paths(form_id=form_id, project_dir=project_dir)
    if res.dxf_path is None:
        raise FileNotFoundError(f"Open Form '{form_id}' not found: {res.searched_paths}")
    val = validate_open_form(res.dxf_path, manifest_path=res.manifest_path, form_id=form_id, tier=res.tier)
    if not val.valid:
        raise ValueError(f"Open Form contract failed: {val.errors}")

    project = dict(model.get("project", {}))
    sheets = list(model.get("sheets", []))
    if not sheets and "viewports" in model:
        sheets = [model]
    if not sheets:
        raise ValueError("Model must contain 'sheets' or 'viewports'.")

    eff_paper = str(paper_size or FORM_CATALOG[form_id]["sheet_size"] or "A3").upper()
    L_m, B_m = _resolve_total_dims(project)
    engine = DcePlanEngine(
        {
            **project,
            "L_total": L_m,
            "B_total": B_m,
        },
        template_path=res.dxf_path,
        v6=True,
        preserve_modelspace=True,
        template_mode="open",
        template_contract=val.to_dict(),
        full_evidence=full_evidence,
    )
    engine.setup()
    _ensure_a3_layers_and_styles(engine.doc)

    # Clear legacy template ModelSpace zone hints cleanly for PaperSpace master file
    for ent in list(engine.msp):
        engine.msp.delete_entity(ent)

    tb_paper_name, pw, ph = _ensure_paper_titleblock_definition(engine.doc, paper_size=eff_paper)
    scale = float(project.get("scale", 100.0))

    # Arrange each sheet's viewports cleanly in ModelSpace rows (`row_y = s_idx * 42000`, `col_x = v_idx * 35000`)
    before_h = snapshot_msp_handles(engine.msp)
    layout_records: List[Dict[str, Any]] = []

    for s_idx, sh in enumerate(sheets):
        sh_no = str(sh.get("sheet_no", f"KC-{s_idx + 1:02d}"))
        layout_name = sh_no.replace("/", "_")
        if s_idx == 0 and "Layout1" in engine.doc.layouts:
            engine.doc.layouts.rename("Layout1", layout_name)
            ps = engine.doc.layouts.get(layout_name)
        elif layout_name in engine.doc.layouts:
            ps = engine.doc.layouts.get(layout_name)
        else:
            ps = engine.doc.layouts.new(layout_name)

        for ent in list(ps):
            ps.delete_entity(ent)

        # Paper frame & Paper TitleBlock INSERT (1:1 mm)
        ps.add_lwpolyline([(0.0, 0.0), (pw, 0.0), (pw, ph), (0.0, ph)], close=True, dxfattribs={"layer": "DCE_Frame"})
        if eff_paper == "A1":
            ps.add_lwpolyline([(20.0, 10.0), (pw - 10.0, 10.0), (pw - 10.0, ph - 10.0), (20.0, ph - 10.0)], close=True, dxfattribs={"layer": "DCE_Frame"})
        else:
            ps.add_lwpolyline([(10.0, 5.0), (368.5, 5.0), (368.5, 292.0), (10.0, 292.0)], close=True, dxfattribs={"layer": "DCE_Frame"})

        tb_vals = {
            "CHU_DAU_TU": project.get("investor", ""),
            "CONG_TY": project.get("company", "TƯ VẤN THIẾT KẾ"),
            "TEN_CONG_TRINH": project.get("project_name", "DỰ ÁN"),
            "HANG_MUC": project.get("drawing_category", "BẢN VẼ KẾT CẤU"),
            "TEN_BAN_VE": sh.get("title", sh_no),
            "TY_LE": f"1/{int(round(scale))}",
            "BUOC_TK": project.get("design_stage", "TKTC"),
            "NAM": str(project.get("year", "2026")),
            "KY_HIEU": sh_no,
        }
        insert_or_update_titleblock(engine.doc, ps, tb_paper_name, tb_vals, mark_owned=False)

        vps = list(sh.get("viewports", []))
        vp_records: List[Dict[str, Any]] = []
        n_vp = max(len(vps), 1)
        for v_idx, vp in enumerate(vps):
            vp_scale = float(vp.get("scale", scale))
            mx0 = 8000.0 + v_idx * 48000.0
            my0 = 5000.0 + s_idx * 38000.0
            vp_info = _render_shared_modelspace_viewport(
                engine,
                vp,
                project,
                sh_no,
                model_origin_mm=(mx0, my0),
                scale=vp_scale,
            )

            # Non-overlapping PaperSpace viewport window(s)
            if eff_paper == "A1":
                draw_x0, draw_x1 = 25.0, 712.0
                draw_y0, draw_y1 = 15.0, 578.0
            else:
                draw_x0, draw_x1 = 15.0, 363.0
                draw_y0, draw_y1 = 12.0, 286.0

            slot_h = (draw_y1 - draw_y0) / float(n_vp)
            # Slot 0 on top, slot 1 below
            wy1 = draw_y1 - v_idx * slot_h - 3.0
            wy0 = wy1 - slot_h + 6.0
            w_center = ((draw_x0 + draw_x1) / 2.0, (wy0 + wy1) / 2.0)
            w_size = (draw_x1 - draw_x0, wy1 - wy0)
            aspect = float(w_size[1]) / max(float(w_size[0]), 1.0)
            v_height = max(
                float(vp_info["model_span_mm"][1]),
                float(vp_info["model_span_mm"][0]) * aspect,
                float(w_size[1]) * vp_scale,
            )

            ps_vp = ps.add_viewport(
                center=w_center,
                size=w_size,
                view_center_point=tuple(vp_info["model_center_mm"]),
                view_height=v_height,
            )
            ps_vp.dxf.layer = f"VP_{str(vp.get('slot', v_idx + 1)).upper()}"
            vp_records.append({
                "vp_id": vp_info["vp_id"],
                "paper_center_mm": list(w_center),
                "paper_size_mm": list(w_size),
                "view_center_mm": vp_info["model_center_mm"],
                "view_height_mm": v_height,
                "scale": vp_scale,
            })

        layout_records.append({
            "layout_name": layout_name,
            "sheet_no": sh_no,
            "paper_size": eff_paper,
            "titleblock_block": tb_paper_name,
            "viewports": vp_records,
        })

    mark_new_entities_owned(engine.msp, before_h, role="P3_SHARED_MODEL")
    _hide_zone_guide_layers_for_export(engine.doc)

    engine.block_evidence = {
        "layout_mode": "paperspace_single_file",
        "shared_axis_block": "Dce_KhTenTruc",
        "layouts": layout_records,
    }

    out_p = Path(output_dxf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    engine.save_v6(str(out_p))
    sha = hashlib.sha256(out_p.read_bytes()).hexdigest()

    # Append layout summary cleanly to sidecar (atomic: temp + os.replace, so a
    # OneDrive-synced path can't leave a torn .dce_audit.json).
    sc_path = out_p.with_suffix(".dce_audit.json")
    sc = json.loads(sc_path.read_text(encoding="utf-8"))
    sc["paperspace_layouts"] = layout_records
    sc["single_file_sha256"] = sha
    _atomic_write_json(sc_path, sc)

    return {
        "status": "OK",
        "output_dxf": str(out_p),
        "single_file_sha256": sha,
        "layout_count": len(layout_records),
        "layouts": layout_records,
        "shared_axis_blocks": sum(
            1 for e in engine.msp if e.dxftype() == "INSERT" and e.dxf.name == "Dce_KhTenTruc"
        ),
    }


def export_with_open_form(
    output_dxf_path: str | Path,
    model: Dict[str, Any],
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    project_dir: Optional[str | Path] = None,
    layout_mode: str = "model",
    full_evidence: bool = False,
) -> Dict[str, Any]:
    """Unified open-mode dispatcher across all 4 editable Forms (`FORM_01`..`FORM_04`)."""
    if form_id not in FORM_CATALOG:
        raise ValueError(f"Unknown form_id '{form_id}'. Known: {list(FORM_CATALOG.keys())}")

    lmode = str(layout_mode or "model").lower()
    if lmode == "paperspace":
        return export_single_file_multilayout_dxf(
            output_dxf_path,
            model=model,
            form_id=form_id,
            project_dir=project_dir,
            full_evidence=full_evidence,
        )

    if form_id == "FORM_02_MULTIVIEW_A3_BTCT":
        eng = export_multiview_a3_sheet(
            str(output_dxf_path),
            model=model,
            template_mode="open",
            form_id=form_id,
            project_dir=str(project_dir) if project_dir else None,
            v6=True,
            full_evidence=full_evidence,
        )
        return {
            "status": "OK",
            "form_id": form_id,
            "layout_mode": "model",
            "output_dxf": str(output_dxf_path),
            "dxf_sha256": hashlib.sha256(Path(output_dxf_path).read_bytes()).hexdigest(),
            "block_evidence": getattr(eng, "block_evidence", {}),
        }

    if form_id == "FORM_04_CHITIET_COC_DAM_COT" and (model.get("detail_sheet") or model.get("sheet_no")):
        from cad_rc_detail_engine import build_custom_detail_sheet
        res_det = build_custom_detail_sheet(model, output_dxf_path, project_dir=project_dir)
        return {
            "status": "OK",
            "form_id": form_id,
            "layout_mode": "model+paperspace",
            "output_dxf": str(output_dxf_path),
            "dxf_sha256": hashlib.sha256(Path(output_dxf_path).read_bytes()).hexdigest(),
            "detail_result": res_det,
        }

    # Open-Form runner for FORM_01 (A1 RC), FORM_03 (A1 Steel), FORM_04 (A3 Details)
    from cad_plan_engine import DcePlanEngine

    res = resolve_form_paths(form_id=form_id, project_dir=project_dir)
    if res.dxf_path is None:
        raise FileNotFoundError(f"Form '{form_id}' not found: {res.searched_paths}")
    val = validate_open_form(res.dxf_path, manifest_path=res.manifest_path, form_id=form_id, tier=res.tier)
    if not val.valid:
        raise ValueError(f"Form '{form_id}' contract invalid: {val.errors}")

    project = dict(model.get("project", {}))
    sheets = list(model.get("sheets", []))
    sh = sheets[0] if sheets else {"sheet_no": "KC.01", "title": FORM_CATALOG[form_id]["title_vi"], "viewports": []}
    vps = list(sh.get("viewports", []))

    engine = DcePlanEngine(
        {
            **project,
            "L_total": _resolve_total_dims(project)[0],
            "B_total": _resolve_total_dims(project)[1],
        },
        template_path=res.dxf_path,
        v6=True,
        preserve_modelspace=True,
        template_mode="open",
        template_contract=val.to_dict(),
        zone_evidence={"zones_wcs": val.zones_wcs},
        full_evidence=full_evidence,
    )
    engine.setup()
    _ensure_a3_layers_and_styles(engine.doc)

    purge_agent_owned_entities(engine.doc, engine.msp)
    before_h = snapshot_msp_handles(engine.msp)

    tb_name = str(val.titleblock_block or FORM_CATALOG[form_id]["titleblock_block"])
    tb_vals = {
        "CHU_DAU_TU": project.get("investor", ""),
        "CONG_TY": project.get("company", "TƯ VẤN THIẾT KẾ"),
        "TEN_CONG_TRINH": project.get("project_name", "DỰ ÁN"),
        "TEN_BAN_VE": sh.get("title", FORM_CATALOG[form_id]["title_vi"]),
        "TY_LE": f"1/{int(round(float(project.get('scale', 100.0))))}",
        "BUOC_TK": project.get("design_stage", "TKTC"),
        "NAM": str(project.get("year", "2026")),
        "KY_HIEU": sh.get("sheet_no", "KC-01"),
    }
    tb_res = insert_or_update_titleblock(engine.doc, engine.msp, tb_name, tb_vals, mark_owned=False)

    # Render elements centered neatly into the Form's active Viewport zone(s)
    vp_zone_key = "VIEWPORT_MAIN" if "VIEWPORT_MAIN" in val.zones_wcs else next(iter(val.zones_wcs.keys()))
    zx0, zy0, zx1, zy1 = val.zones_wcs[vp_zone_key][0]
    zcx, zcy = (zx0 + zx1) / 2.0, (zy0 + zy1) / 2.0
    L_m, B_m = _resolve_total_dims(project)
    l_mm = L_m * 1000.0
    b_mm = B_m * 1000.0
    ox = zcx - l_mm / 2.0
    oy = zcy - b_mm / 2.0

    # Grid lines & shared Dce_KhTenTruc axis bubbles centered inside zone
    for ax_name, xm in project.get("grid_x", []):
        gx_w = ox + float(xm) * 1000.0
        engine.msp.add_line((gx_w, oy - 1200.0), (gx_w, oy + b_mm + 1200.0), dxfattribs={"layer": "DCE_Truc"})
        insert_axis_bubble_native(engine.doc, engine.msp, gx_w, oy - 1550.0, str(ax_name), 0.0, scale=100.0)
    for ay_name, ym in project.get("grid_y", []):
        gy_w = oy + float(ym) * 1000.0
        engine.msp.add_line((ox - 1200.0, gy_w), (ox + l_mm + 1200.0, gy_w), dxfattribs={"layer": "DCE_Truc"})
        insert_axis_bubble_native(engine.doc, engine.msp, ox - 1550.0, gy_w, str(ay_name), 90.0, scale=100.0)

    # Members placed via native blocks according to Form discipline (RC / Steel / Details)
    src_vp = vps[0] if vps else {}
    for col in src_vp.get("columns", []):
        cx = ox + ((float(col["x0"]) + float(col["x1"])) / 2.0) * 1000.0
        cy = oy + ((float(col["y0"]) + float(col["y1"])) / 2.0) * 1000.0
        ckind = "STEEL_H" if form_id == "FORM_03_KETCAU_THEP_STEEL" else str(col.get("kind", "RC"))
        insert_column_block(
            engine.doc, engine.msp, cx, cy,
            b_mm=float(col.get("b_mm", 200)), h_mm=float(col.get("h_mm", 200)),
            kind=ckind, mark=str(col.get("mark", "")), show_tag=True,
        )
    for pidx, pl in enumerate(src_vp.get("piles", [])):
        px = ox + float(pl["x"]) * 1000.0
        py = oy + float(pl["y"]) * 1000.0
        insert_pile_block(
            engine.doc, engine.msp, px, py,
            kind=str(pl.get("kind", "TYPE1")),
            size_mm=float(pl.get("size_m", 0.25)) * 1000.0,
            pile_id=str(pl.get("id") or f"P{pidx + 1}"),
            show_label=(form_id == "FORM_04_CHITIET_COC_DAM_COT"),
        )

    # Beam segments (Steel beams on DCE_Beam / RC beams on DCE_Beam)
    beam_layer = "DCE_MainBeam" if form_id == "FORM_03_KETCAU_THEP_STEEL" else "DCE_Beam"
    for bm in src_vp.get("beams", []):
        bx0 = ox + float(bm.get("x0", 0.0)) * 1000.0
        by0 = oy + float(bm.get("y0", 0.0)) * 1000.0
        bx1 = ox + float(bm.get("x1", 0.0)) * 1000.0
        by1 = oy + float(bm.get("y1", 0.0)) * 1000.0
        engine.msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], close=True, dxfattribs={"layer": beam_layer})

    owned = mark_new_entities_owned(engine.msp, before_h, role=f"OPEN_{form_id}")
    _hide_zone_guide_layers_for_export(engine.doc)
    engine.block_evidence = {"form_id": form_id, "titleblock": tb_res, "agent_owned_entities": owned}

    out_p = Path(output_dxf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    engine.save_v6(str(out_p))
    return {
        "status": "OK",
        "form_id": form_id,
        "layout_mode": "model",
        "output_dxf": str(out_p),
        "dxf_sha256": hashlib.sha256(out_p.read_bytes()).hexdigest(),
        "titleblock": tb_res,
        "agent_owned_entities": owned,
    }
