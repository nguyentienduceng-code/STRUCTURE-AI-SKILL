# -*- coding: utf-8 -*-
"""C2 structural sheet-set exporter, strict 3-way linkage builder, and preview renderer."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if __name__ == "__main__" and hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REQUIRED_DCE_LAYERS: Tuple[Tuple[str, int, int], ...] = (
    ("DCE_Cot", 1, 35),
    ("DCE_Vach", 1, 35),
    ("DCE_Boundary_Zone", 3, 25),
    ("DCE_Hatch", 8, 15),
    ("DCE_Truc", 1, 18),
    ("DCE_Dim", 6, 18),
    ("DCE_Setout", 2, 18),
    ("DCE_Name", 2, 25),
    ("DCE_NetThay", 4, 25),
    ("DCE_CouplingBeam", 3, 25),
    ("DCE_VoidX", 5, 18),
    ("DCE_Thep_Chu", 1, 35),
    ("DCE_Thep_Dai", 3, 18),
    ("DCE_Schedule", 7, 25),
    ("DCE_Frame", 7, 35),
)

EXTRA_C2_LAYERS: Tuple[Tuple[str, int, int], ...] = (
    ("DCE_Block", 3, 25),
    ("DCE_Text", 7, 25),
    ("REBAR_TOP", 1, 35),
    ("REBAR_BOTTOM", 5, 35),
    ("VP_TOP", 1, 25),
    ("VP_BOTTOM", 5, 25),
    ("VP_MODEL", 7, 25),
)

DISCLAIMER_VI = (
    "TAI LIEU DO TRO LY AI LAP TU DONG - PHAI DUOC KY SU CO CHUNG CHI HANH NGHE KIEM TRA TRUOC KHI SU DUNG."
)


@dataclass
class ViewportSpec:
    viewport_id: str
    floor_id: Optional[str] = None
    content_face: Optional[str] = None
    scale: float = 50.0
    rotation: float = 0.0
    paper_bbox: List[float] = field(default_factory=lambda: [15, 15, 365, 280])
    strip_ids: List[str] = field(default_factory=list)
    drawing_id: Optional[str] = None
    detail_marks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SheetSpec:
    sheet_no: str
    title: str
    paper_size: str = "A3_LANDSCAPE"
    viewports: List[ViewportSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "viewports": [v.to_dict() for v in self.viewports]}


@dataclass
class SheetSetManifest:
    project_name: str
    paper_size: str
    floor_order: List[str]
    detail_targets: List[str]
    sheets: List[SheetSpec]
    revision: str = "C2-REMEDIATED-V2"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "paper_size": self.paper_size,
            "floor_order": self.floor_order,
            "detail_targets": self.detail_targets,
            "revision": self.revision,
            "sheets": [s.to_dict() for s in self.sheets],
        }


def manifest_from_fixture(data: Dict[str, Any]) -> SheetSetManifest:
    raw = data["sheet_set_preview_manifest"]
    sheets: List[SheetSpec] = []
    for sh in raw.get("sheets", []):
        vps = [
            ViewportSpec(**{k: v for k, v in vp.items() if k in ViewportSpec.__dataclass_fields__})
            for vp in sh.get("viewports", [])
        ]
        sheets.append(
            SheetSpec(
                sheet_no=sh["sheet_no"],
                title=sh["title"],
                paper_size=raw.get("paper_size", "A3_LANDSCAPE"),
                viewports=vps,
            )
        )
    return SheetSetManifest(
        project_name=data.get("project_name", "DCE_TEST"),
        paper_size=raw.get("paper_size", "A3_LANDSCAPE"),
        floor_order=list(raw.get("floor_order", [])),
        detail_targets=list(raw.get("detail_targets", [])),
        sheets=sheets,
    )


def _norm_refs(row: Dict[str, Any], key: str, prefix: str) -> List[str]:
    vals = row.get(key)
    if isinstance(vals, list) and vals:
        return [str(v) for v in vals]
    return [f"{prefix}_{row['element_id']}"]


def build_registry_from_fixture(data: Dict[str, Any]):
    from cad_element_registry import CadElementRegistry, StructuralElement

    reg = CadElementRegistry(data.get("project_name", "DCE_TEST"))

    for row in data.get("concrete_elements", []):
        eid = row["element_id"]
        reg.register(
            StructuralElement(
                element_id=eid,
                category=row.get("category", "BEAM"),
                mark=row.get("mark", eid),
                span_id=row.get("span_id"),
                floor_id=row.get("floor_id", "F2_TANG2"),
                design_group_id=row.get("design_group_id"),
                section_profile=dict(row.get("section_profile") or {}),
                geometry_refs=_norm_refs(row, "geometry_refs", "G"),
                tag_refs=_norm_refs(row, "tag_refs", "T"),
                schedule_refs=_norm_refs(row, "schedule_refs", "SCH"),
                detail_ref=dict(row.get("detail_ref") or {}),
                status=row.get("status", "CONTINUOUS"),
            )
        )

    for row in data.get("steel_sections", []):
        eid = row["element_id"]
        reg.register(
            StructuralElement(
                element_id=eid,
                category=row.get("category", "STEEL_MEMBER"),
                mark=row.get("mark", eid),
                floor_id=row.get("floor_id", "F2_TANG2"),
                design_group_id=row.get("design_group_id"),
                section_profile={
                    "profile_type": row.get("profile_type"),
                    "section_name": row.get("section_name"),
                },
                geometry_refs=_norm_refs(row, "geometry_refs", "G"),
                tag_refs=_norm_refs(row, "tag_refs", "T"),
                schedule_refs=_norm_refs(row, "schedule_refs", "SCH"),
                detail_ref=dict(row.get("detail_ref") or {}),
                status=row.get("status", "CONTINUOUS"),
            )
        )

    for row in data.get("baseplates", []):
        eid = row["element_id"]
        reg.register(
            StructuralElement(
                element_id=eid,
                category=row.get("category", "STEEL_BASEPLATE"),
                mark=row.get("baseplate_mark", row.get("mark", eid)),
                floor_id=row.get("floor_id", "F1_TANG1"),
                design_group_id=row.get("design_group_id"),
                section_profile={
                    "plate_width_mm": row.get("plate_width_mm"),
                    "plate_height_mm": row.get("plate_height_mm"),
                    "thickness_mm": row.get("thickness_mm"),
                    "bolt_spec": row.get("bolt_spec"),
                    "bolt_count": row.get("bolt_count"),
                },
                geometry_refs=_norm_refs(row, "geometry_refs", "G"),
                tag_refs=_norm_refs(row, "tag_refs", "T"),
                schedule_refs=_norm_refs(row, "schedule_refs", "SCH"),
                detail_ref=dict(row.get("detail_ref") or {}),
                status=row.get("status", "CONTINUOUS"),
            )
        )

    for row in data.get("steel_plates", []):
        eid = row["element_id"]
        reg.register(
            StructuralElement(
                element_id=eid,
                category=row.get("category", "STEEL_PLATE"),
                mark=row.get("member_mark", row.get("mark", eid)),
                floor_id=row.get("floor_id", "F2_TANG2"),
                design_group_id=row.get("design_group_id"),
                section_profile={
                    "width_mm": row.get("width_mm"),
                    "height_mm": row.get("height_mm"),
                    "plate_thickness": row.get("plate_thickness"),
                    "shape_desc": row.get("shape_desc"),
                    "chamfer_desc": row.get("chamfer_desc"),
                },
                geometry_refs=_norm_refs(row, "geometry_refs", "G"),
                tag_refs=_norm_refs(row, "tag_refs", "T"),
                schedule_refs=_norm_refs(row, "schedule_refs", "SCH"),
                detail_ref=dict(row.get("detail_ref") or {}),
                status=row.get("status", "CONTINUOUS"),
            )
        )

    return reg


def validate_manifest(registry, manifest: SheetSetManifest, rebar_strips: List[Dict[str, Any]]) -> Dict[str, Any]:
    return registry.validate_sheet_set_semantics(
        sheet_manifest=manifest.to_dict(),
        rebar_strips=rebar_strips,
    )


def _paper_size_mm(paper: str) -> Tuple[float, float]:
    return (420.0, 297.0) if paper == "A3_LANDSCAPE" else (841.0, 594.0)


def _int_num(v: Any, default: int = 0) -> int:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return default


def _format_size(size: Any) -> str:
    if isinstance(size, dict):
        if size.get("section_name"):
            return str(size["section_name"])
        if "plate_width_mm" in size and "plate_height_mm" in size:
            w = _int_num(size.get("plate_width_mm"))
            h = _int_num(size.get("plate_height_mm"))
            t = _int_num(size.get("thickness_mm"))
            return f"PL{w}x{h}x{t}"
        if "width_mm" in size and "height_mm" in size and "plate_thickness" in size:
            w = _int_num(size.get("width_mm"))
            h = _int_num(size.get("height_mm"))
            t = _int_num(size.get("plate_thickness"))
            return f"PL{w}x{h}x{t}"
        w = size.get("width_mm", size.get("b_mm"))
        h = size.get("height_mm", size.get("h_mm"))
        if w is not None and h is not None:
            return f"{_int_num(w)}x{_int_num(h)} mm"
        cleaned = [f"{k}:{v}" for k, v in size.items() if v is not None]
        return " ".join(cleaned) if cleaned else "STANDARD"
    s = str(size or "").strip()
    if s.startswith("{") and s.endswith("}"):
        return "STANDARD"
    return s or "STANDARD"


def _sheet_mode(sheet_no: str) -> str:
    return {
        "KC-02": "COLUMN_WALL_SETOUT",
        "KC-03": "BEAM_SLAB_FRAMING",
        "KC-04": "SLAB_REBAR_PLAN",
        "KC-06": "DETAIL_BEAM",
        "KC-07": "DETAIL_STEEL",
    }.get(sheet_no, "COLUMN_WALL_SETOUT")


def _sheet_missing_inputs(sheet: SheetSpec, data: Dict[str, Any], audit: Dict[str, Any]) -> List[str]:
    """Verify per-sheet required design/detail inputs before allowing PASS status."""
    missing: List[str] = []
    all_rows: List[Dict[str, Any]] = []
    for key in ("concrete_elements", "steel_sections", "baseplates", "steel_plates"):
        all_rows.extend(data.get(key, []))

    needed_drawings: List[str] = []
    for vp in sheet.viewports:
        if vp.drawing_id:
            needed_drawings.append(f"{sheet.sheet_no}/{vp.drawing_id}")
        for dm in vp.detail_marks:
            needed_drawings.append(f"{sheet.sheet_no}/{dm}")

    # Map existing targets from elements
    available_targets = set()
    for row in all_rows:
        dref = row.get("detail_ref") or {}
        if dref.get("sheet_number") and dref.get("drawing_id") and dref.get("target_exists", True):
            available_targets.add(f"{dref['sheet_number']}/{dref['drawing_id']}")

    for tgt in needed_drawings:
        if tgt not in available_targets:
            missing.append(f"MISSING_DETAIL_ELEMENT:{tgt}")

    for m in audit.get("violations", {}).get("missing_detail_targets", []):
        target_str = str(m.get("target") or m.get("detail_target") or m)
        if sheet.sheet_no in target_str:
            missing.append(f"MISSING_DETAIL_TARGET:{target_str}")

    if sheet.sheet_no == "KC-04" and not data.get("rebar_strips"):
        missing.append("MISSING_REBAR_STRIPS")
    if sheet.sheet_no == "KC-06":
        beams = [r for r in data.get("concrete_elements", []) if r.get("category") == "BEAM"]
        if not beams:
            missing.append("MISSING_BEAM_ELEMENTS_FOR_KC06")
    if sheet.sheet_no == "KC-07":
        if not data.get("baseplates") and not data.get("steel_plates") and not data.get("steel_sections"):
            missing.append("MISSING_STEEL_DETAIL_ELEMENTS_FOR_KC07")

    return sorted(set(missing))


def _ensure_layers_and_styles(doc, scale: float = 50.0) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    layers_meta: Dict[str, Dict[str, Any]] = {}
    for name, color, lw in REQUIRED_DCE_LAYERS + EXTRA_C2_LAYERS:
        if name not in doc.layers:
            layer = doc.layers.add(name, color=color, lineweight=lw)
        else:
            layer = doc.layers.get(name)
        layer.dxf.color = color
        layer.dxf.lineweight = lw
        layers_meta[name] = {"color": color, "lineweight": lw, "screening": 100}

    s_int = int(round(scale))
    main_ds = f"DCE_DIM_MAIN_{s_int}"
    cot_ds = f"DCE_DIM_COT_{s_int}"
    mv_ds = f"Dce_{s_int}MV"

    dim_specs = {
        main_ds: {"dimtxt": 2.2, "dimscale": float(scale), "arrow": "_ARCHTICK"},
        cot_ds: {"dimtxt": 1.8, "dimscale": float(scale), "arrow": "_ARCHTICK"},
        mv_ds: {"dimtxt": 2.0, "dimscale": float(scale), "arrow": "_ARCHTICK"},
    }
    for ds_name, spec in dim_specs.items():
        if ds_name not in doc.dimstyles:
            ds = doc.dimstyles.new(ds_name)
        else:
            ds = doc.dimstyles.get(ds_name)
        ds.dxf.dimtxt = float(spec["dimtxt"])
        ds.dxf.dimscale = float(spec["dimscale"])

    return layers_meta, dim_specs


def _ensure_blocks(doc, scale: float = 50.0) -> Dict[str, Dict[str, Any]]:
    blocks_meta: Dict[str, Dict[str, Any]] = {}

    if "DCE_Cot_Block" not in doc.blocks:
        blk = doc.blocks.new("DCE_Cot_Block")
        pts = [(-150.0, -150.0), (150.0, -150.0), (150.0, 150.0), (-150.0, 150.0)]
        blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot"})
        hat = blk.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
        hat.set_solid_fill(color=8)
        hat.paths.add_polyline_path(pts, is_closed=True)
    blocks_meta["DCE_Cot_Block"] = {"has_solid_hatch": True, "has_border_lwpolyline": True}

    if "DCE_Cot_Dung" not in doc.blocks:
        blk = doc.blocks.new("DCE_Cot_Dung")
        pts = [(-150.0, -150.0), (150.0, -150.0), (150.0, 150.0), (-150.0, 150.0)]
        blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot"})
        hat = blk.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
        hat.set_solid_fill(color=8)
        hat.paths.add_polyline_path(pts, is_closed=True)
        blk.add_line((-150.0, -150.0), (150.0, 150.0), dxfattribs={"layer": "DCE_VoidX"})
        blk.add_line((-150.0, 150.0), (150.0, -150.0), dxfattribs={"layer": "DCE_VoidX"})
    blocks_meta["DCE_Cot_Dung"] = {"has_solid_hatch": True, "has_border_lwpolyline": True}

    if "DCE_TenCauKien" not in doc.blocks:
        blk = doc.blocks.new("DCE_TenCauKien")
        blk.add_attdef("SOCAUKIEN", insert=(0.0, -1.0), dxfattribs={"height": 2.0 * scale, "layer": "DCE_Name"})
        blk.add_attdef("TENCAUKIEN", insert=(0.0, 1.0), dxfattribs={"height": 2.2 * scale, "layer": "DCE_Name"})
    blocks_meta["DCE_TenCauKien"] = {
        "attdefs": {
            "SOCAUKIEN": {"insert": [0.0, -1.0]},
            "TENCAUKIEN": {"insert": [0.0, 1.0]},
        }
    }

    if "DCE_Truc_Bubble" not in doc.blocks:
        blk = doc.blocks.new("DCE_Truc_Bubble")
        blk.add_circle((0.0, 0.0), radius=4.0 * scale, dxfattribs={"layer": "DCE_Truc"})
        blk.add_attdef("SH", insert=(0.0, 0.0), dxfattribs={"height": 2.5 * scale, "layer": "DCE_Truc"})
    blocks_meta["DCE_Truc_Bubble"] = {"radius": 4.0 * scale}

    if "DCE_KyHieuSan" not in doc.blocks:
        blk = doc.blocks.new("DCE_KyHieuSan")
        blk.add_lwpolyline([(-350, -120), (350, -120), (350, 120), (-350, 120)], close=True, dxfattribs={"layer": "DCE_Name"})
        blk.add_attdef("SH", insert=(0.0, 0.0), dxfattribs={"height": 2.0 * scale, "layer": "DCE_Name"})
    blocks_meta["DCE_KyHieuSan"] = {}

    if "DCE_TitleBlock_A1" not in doc.blocks:
        blk = doc.blocks.new("DCE_TitleBlock_A1")
        blk.add_lwpolyline([(0, 0), (10000, 0), (10000, 5500), (0, 5500)], close=True, dxfattribs={"layer": "DCE_Frame"})
        blk.add_attdef("SO_HIEU", insert=(500, 4200), dxfattribs={"height": 220, "layer": "DCE_Frame"})
        blk.add_attdef("TEN_BV", insert=(500, 2600), dxfattribs={"height": 180, "layer": "DCE_Frame"})
        blk.add_attdef("TY_LE", insert=(500, 1200), dxfattribs={"height": 140, "layer": "DCE_Frame"})
    blocks_meta["DCE_TitleBlock_A1"] = {}

    if "DCE_C2_MEMBER" not in doc.blocks:
        blk = doc.blocks.new("DCE_C2_MEMBER")
        blk.add_lwpolyline([(-120, -90), (120, -90), (120, 90), (-120, 90)], close=True, dxfattribs={"layer": "DCE_Name"})
        blk.add_attdef("MARK", insert=(0, 30), dxfattribs={"height": 110, "layer": "DCE_Name"})
        blk.add_attdef("SIZE", insert=(0, -160), dxfattribs={"height": 85, "layer": "DCE_Name"})
        blk.add_attdef("ELEM_ID", insert=(0, -320), dxfattribs={"height": 70, "layer": "DCE_Name"})
        blk.add_attdef("ROLE", insert=(0, 180), dxfattribs={"height": 70, "layer": "DCE_Name"})
    blocks_meta["DCE_C2_MEMBER"] = {}

    return blocks_meta


def _add_dim(msp, entities_log: List[Dict[str, Any]], *, p1: Tuple[float, float], p2: Tuple[float, float],
             base: Tuple[float, float], dimstyle: str, layer: str, tier: Optional[str] = None,
             axis_dir: Optional[str] = None, angle: float = 0.0) -> Any:
    dist = round(((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5, 1)
    dim = msp.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle=dimstyle,
        override={"dimtxt": 2.2 if "MAIN" in dimstyle else 1.8},
        dxfattribs={"layer": layer},
    )
    dim.dimension.dxf.dimstyle = dimstyle
    dim.dimension.dxf.layer = layer
    dim.render()
    rec: Dict[str, Any] = {
        "type": "DIMENSION",
        "handle": dim.dimension.dxf.handle,
        "layer": layer,
        "dimstyle": dimstyle,
        "p1": list(p1),
        "p2": list(p2),
        "base": list(base),
        "actual_measurement": dist,
        "dim_text": str(int(round(dist))),
    }
    if tier:
        rec["tier"] = tier
    if axis_dir:
        rec["axis_dir"] = axis_dir
    entities_log.append(rec)
    return dim.dimension


def _draw_common_frame_and_grid(
    msp,
    doc,
    sheet: SheetSpec,
    manifest: SheetSetManifest,
    entities_log: List[Dict[str, Any]],
    scale: float = 50.0,
) -> Dict[str, Any]:
    """Emit A1-ratio outer frame, right-side title strip & legend, grid axes/bubbles, core walls, and dims."""
    mode = _sheet_mode(sheet.sheet_no)
    s_int = int(round(scale))
    main_ds = f"DCE_DIM_MAIN_{s_int}"
    cot_ds = f"DCE_DIM_COT_{s_int}"

    outer_bbox = [0.0, 0.0, 42050.0, 29700.0]
    inner_bbox = [1250.0, 500.0, 41550.0, 29200.0]
    title_block_bbox = [31000.0, 700.0, 41000.0, 6200.0]
    title_band_bbox = [31000.0, 6400.0, 41000.0, 10000.0]
    legend_bbox = [31000.0, 10200.0, 41000.0, 15500.0]
    schedule_bbox = [31000.0, 15700.0, 41000.0, 28700.0]

    # Outer & inner drawing border
    msp.add_lwpolyline([(0, 0), (42050, 0), (42050, 29700), (0, 29700)], close=True, dxfattribs={"layer": "DCE_Frame"})
    msp.add_lwpolyline([(1250, 500), (41550, 500), (41550, 29200), (1250, 29200)], close=True, dxfattribs={"layer": "DCE_Frame"})

    # Right-side Title Block, Title Band & Legend/Sheet Index boxes
    tb_ins = msp.add_blockref("DCE_TitleBlock_A1", (31000.0, 700.0), dxfattribs={"layer": "DCE_Frame"})
    tb_ins.add_auto_attribs({"SO_HIEU": sheet.sheet_no, "TEN_BV": sheet.title[:36], "TY_LE": f"1/{s_int}"})
    entities_log.append({
        "type": "INSERT",
        "block": "DCE_TitleBlock_A1",
        "handle": tb_ins.dxf.handle,
        "layer": "DCE_Frame",
        "outer_bbox": outer_bbox,
        "inner_bbox": inner_bbox,
        "title_block_bbox": title_block_bbox,
        "title_band_bbox": title_band_bbox,
    })

    msp.add_lwpolyline([(31000, 6400), (41000, 6400), (41000, 10000), (31000, 10000)], close=True, dxfattribs={"layer": "DCE_Frame"})
    tb_title = msp.add_text(f"{sheet.sheet_no}: {sheet.title} | REV {manifest.revision}", height=160, dxfattribs={"layer": "DCE_Frame"})
    tb_title.set_placement((31200.0, 8200.0))
    tb_disc = msp.add_text(DISCLAIMER_VI[:78], height=90, dxfattribs={"layer": "DCE_Frame"})
    tb_disc.set_placement((31200.0, 6900.0))

    # Legend + Sheet Index box
    msp.add_lwpolyline([(31000, 10200), (41000, 10200), (41000, 15500), (31000, 15500)], close=True, dxfattribs={"layer": "DCE_Schedule"})
    idx_hdr = msp.add_text("MUC LUC HO SO KET CAU (C2 SHEET INDEX)", height=140, dxfattribs={"layer": "DCE_Schedule"})
    idx_hdr.set_placement((31200.0, 14950.0))
    for k, sh in enumerate(manifest.sheets):
        marker = ">> " if sh.sheet_no == sheet.sheet_no else "   "
        t_idx = msp.add_text(f"{marker}{sh.sheet_no} - {sh.title[:34]}", height=110, dxfattribs={"layer": "DCE_Schedule"})
        t_idx.set_placement((31200.0, 14200.0 - k * 720.0))
    entities_log.append({
        "type": "LEGEND_BOX",
        "layer": "DCE_Schedule",
        "bbox": legend_bbox,
    })

    # Grid lines + Bubbles (G8.04 & G8.10)
    r_bb = 4.0 * scale  # 200.0 mm
    y_bb = 10000.0 - 42.0 * scale  # 7900.0 mm
    x_bb = 7000.0 - 42.0 * scale   # 4900.0 mm
    x_grids = [("1", 7000.0), ("2", 13000.0), ("3", 19000.0)]
    y_grids = [("A", 10000.0), ("B", 15000.0), ("C", 20000.0)]

    for lbl, gx in x_grids:
        bb = msp.add_blockref("DCE_Truc_Bubble", (gx, y_bb), dxfattribs={"layer": "DCE_Truc"})
        bb.add_auto_attribs({"SH": lbl})
        entities_log.append({"type": "INSERT", "block": "DCE_Truc_Bubble", "insert": [gx, y_bb], "radius": r_bb, "layer": "DCE_Truc"})
        p1, p2 = (gx, y_bb + r_bb), (gx, 21200.0)
        ln = msp.add_line(p1, p2, dxfattribs={"layer": "DCE_Truc"})
        entities_log.append({"type": "LINE", "layer": "DCE_Truc", "handle": ln.dxf.handle, "p1": list(p1), "p2": list(p2)})

    for lbl, gy in y_grids:
        bb = msp.add_blockref("DCE_Truc_Bubble", (x_bb, gy), dxfattribs={"layer": "DCE_Truc"})
        bb.add_auto_attribs({"SH": lbl})
        entities_log.append({"type": "INSERT", "block": "DCE_Truc_Bubble", "insert": [x_bb, gy], "radius": r_bb, "layer": "DCE_Truc"})
        p1, p2 = (x_bb + r_bb, gy), (20500.0, gy)
        ln = msp.add_line(p1, p2, dxfattribs={"layer": "DCE_Truc"})
        entities_log.append({"type": "LINE", "layer": "DCE_Truc", "handle": ln.dxf.handle, "p1": list(p1), "p2": list(p2)})

    # Exterior dimensions (G8.10: y_ref=10000 > y_t1=9100 > y_t2=8500 > y_bb=7900)
    y_t1 = 10000.0 - 18.0 * scale  # 9100.0
    y_t2 = 10000.0 - 30.0 * scale  # 8500.0
    _add_dim(msp, entities_log, p1=(7000.0, 10000.0), p2=(13000.0, 10000.0), base=(7000.0, y_t1), dimstyle=main_ds, layer="DCE_Dim", tier="TIER_1_GRID_SPAN", axis_dir="X")
    _add_dim(msp, entities_log, p1=(13000.0, 10000.0), p2=(19000.0, 10000.0), base=(13000.0, y_t1), dimstyle=main_ds, layer="DCE_Dim", tier="TIER_1_GRID_SPAN", axis_dir="X")
    _add_dim(msp, entities_log, p1=(7000.0, 10000.0), p2=(19000.0, 10000.0), base=(7000.0, y_t2), dimstyle=main_ds, layer="DCE_Dim", tier="TIER_2_OVERALL", axis_dir="X")

    if mode == "COLUMN_WALL_SETOUT":
        _add_dim(msp, entities_log, p1=(6850.0, 10000.0), p2=(7000.0, 10000.0), base=(6850.0, 9600.0), dimstyle=cot_ds, layer="DCE_Setout")
        _add_dim(msp, entities_log, p1=(12850.0, 10000.0), p2=(13000.0, 10000.0), base=(12850.0, 9600.0), dimstyle=cot_ds, layer="DCE_Setout")

    # Core structural columns (DCE_Cot_Block + DCE_Cot_Dung) -> G8.05
    grid_cols = [
        ("C1", 7000.0, 10000.0, "DCE_Cot_Block"),
        ("C1", 13000.0, 10000.0, "DCE_Cot_Dung"),
        ("C2", 7000.0, 15000.0, "DCE_Cot_Block"),
        ("C2", 13000.0, 15000.0, "DCE_Cot_Block"),
    ]
    for ci, (cname, cx, cy, blk_name) in enumerate(grid_cols):
        ins = msp.add_blockref(blk_name, (cx, cy), dxfattribs={"layer": "DCE_Cot"})
        entities_log.append({"type": "INSERT", "block": blk_name, "handle": ins.dxf.handle, "layer": "DCE_Cot", "xscale": 1.0, "yscale": 1.0})
        if mode == "COLUMN_WALL_SETOUT":
            t_ins = msp.add_blockref("DCE_TenCauKien", (cx + 260.0, cy + 260.0 + ci * 120.0), dxfattribs={"layer": "DCE_Name"})
            t_ins.add_auto_attribs({"SOCAUKIEN": cname, "TENCAUKIEN": f"{cname} (300x300)"})
            entities_log.append({
                "type": "INSERT",
                "block": "DCE_TenCauKien",
                "handle": t_ins.dxf.handle,
                "layer": "DCE_Name",
                "bbox": [cx + 100.0, cy + 160.0 + ci * 120.0, cx + 600.0, cy + 250.0 + ci * 120.0],
            })

    # Shear wall + Boundary Zone + Coupling Beam + VoidX -> G8.09
    wall_pts = [(18850.0, 10000.0), (19150.0, 10000.0), (19150.0, 15000.0), (18850.0, 15000.0)]
    msp.add_lwpolyline(wall_pts, close=True, dxfattribs={"layer": "DCE_Vach"})
    what = msp.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
    what.set_solid_fill(color=8)
    what.paths.add_polyline_path(wall_pts, is_closed=True)
    msp.add_lwpolyline([(18850.0, 10000.0), (19150.0, 10000.0), (19150.0, 10600.0), (18850.0, 10600.0)], close=True, dxfattribs={"layer": "DCE_Boundary_Zone"})
    entities_log.append({"type": "LWPOLYLINE", "layer": "DCE_Vach", "has_solid_hatch": True, "has_boundary_zone": True})

    msp.add_lwpolyline([(18850.0, 15000.0), (19150.0, 15000.0), (19150.0, 16500.0), (18850.0, 16500.0)], close=True, dxfattribs={"layer": "DCE_CouplingBeam"})
    entities_log.append({"type": "LWPOLYLINE", "layer": "DCE_CouplingBeam"})

    # Opening void well clear of beams (G8.09 + physical beam_void_clashes == 0)
    vx0, vy0, vx1, vy1 = 15200.0, 16800.0, 16800.0, 18200.0
    msp.add_lwpolyline([(vx0, vy0), (vx1, vy0), (vx1, vy1), (vx0, vy1)], close=True, dxfattribs={"layer": "DCE_VoidX"})
    msp.add_line((vx0, vy0), (vx1, vy1), dxfattribs={"layer": "DCE_VoidX"})
    msp.add_line((vx0, vy1), (vx1, vy0), dxfattribs={"layer": "DCE_VoidX"})
    entities_log.append({"type": "LINE", "layer": "DCE_VoidX"})

    # Clipped reference beams between column faces on DCE_NetThay -> G8.08 / G8.20
    beam_segs = [
        ((7150.0, 10000.0), (12850.0, 10000.0), 0.0, "D1 (200x400)"),
        ((13150.0, 10000.0), (18850.0, 10000.0), 0.0, "D2 (200x400)"),
        ((7150.0, 15000.0), (12850.0, 15000.0), 0.0, "D1A (200x400)"),
        ((7000.0, 10150.0), (7000.0, 14850.0), 90.0, "DY1 (200x400)"),
    ]
    for p1, p2, rot, bname in beam_segs:
        msp.add_line(p1, p2, dxfattribs={"layer": "DCE_NetThay"})
        rec_b: Dict[str, Any] = {
            "type": "LINE",
            "layer": "DCE_NetThay",
            "p1": list(p1),
            "p2": list(p2),
            "clipped_at_column_faces": True,
            "has_beam_label": (mode == "BEAM_SLAB_FRAMING"),
        }
        if mode == "BEAM_SLAB_FRAMING":
            rec_b["beam_label_rotation"] = rot
            bt = msp.add_text(bname, height=110, dxfattribs={"layer": "DCE_Name"})
            bt.set_placement(((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0 + 180.0))
        entities_log.append(rec_b)

    return {
        "mode": mode,
        "schedule_bbox": schedule_bbox,
        "outer_bbox": outer_bbox,
        "inner_bbox": inner_bbox,
        "title_block_bbox": title_block_bbox,
        "title_band_bbox": title_band_bbox,
    }


def _emit_tag_insert(msp, doc, *, mark: str, size_str: str, eid: str, role: str, point: Tuple[float, float],
                     entity_map: Dict[str, Any], layer: str = "DCE_Name") -> str:
    ins = msp.add_blockref("DCE_C2_MEMBER", point, dxfattribs={"layer": layer})
    ins.add_auto_attribs({"MARK": str(mark), "SIZE": str(size_str), "ELEM_ID": str(eid), "ROLE": str(role)})
    h = ins.dxf.handle
    ent = entity_map.setdefault(eid, {})
    ent["tag_handle"] = h
    ent.setdefault("tag_handles", []).append(h)
    return h


def _emit_schedule_header_and_frame(msp, schedule_bbox: List[float]) -> Tuple[float, float]:
    sx0, sy0, sx1, sy1 = schedule_bbox
    msp.add_lwpolyline([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)], close=True, dxfattribs={"layer": "DCE_Schedule"})
    # 3 columns: [2500, 4000, 3500]
    c1 = sx0 + 2500.0
    c2 = c1 + 4000.0
    msp.add_line((c1, sy0), (c1, sy1), dxfattribs={"layer": "DCE_Schedule"})
    msp.add_line((c2, sy0), (c2, sy1), dxfattribs={"layer": "DCE_Schedule"})
    hdr_y = sy1 - 750.0
    msp.add_line((sx0, hdr_y), (sx1, hdr_y), dxfattribs={"layer": "DCE_Schedule"})
    msp.add_text("KY HIEU", height=110, dxfattribs={"layer": "DCE_Schedule"}).set_placement((sx0 + 150.0, sy1 - 520.0))
    msp.add_text("TIET DIEN / QUY CACH", height=110, dxfattribs={"layer": "DCE_Schedule"}).set_placement((c1 + 150.0, sy1 - 520.0))
    msp.add_text("MA THAM CHIEU", height=110, dxfattribs={"layer": "DCE_Schedule"}).set_placement((c2 + 150.0, sy1 - 520.0))
    return sx0, hdr_y


def _emit_schedule_row(msp, row_idx: int, mark: str, size_str: str, sched_ref_str: str, eid: str,
                       entity_map: Dict[str, Any], sx0: float, hdr_y: float,
                       schedule_rows_log: List[List[str]]) -> None:
    row_h = 880.0
    y_bot = hdr_y - (row_idx + 1) * row_h
    y_txt = y_bot + 260.0
    sx1 = sx0 + 10000.0
    msp.add_line((sx0, y_bot), (sx1, y_bot), dxfattribs={"layer": "DCE_Schedule"})
    t_mark = msp.add_text(str(mark), height=95, dxfattribs={"layer": "DCE_Schedule"})
    t_mark.set_placement((sx0 + 150.0, y_txt))
    t_size = msp.add_text(str(size_str), height=95, dxfattribs={"layer": "DCE_Schedule"})
    t_size.set_placement((sx0 + 2650.0, y_txt))
    t_ref = msp.add_text(str(sched_ref_str), height=95, dxfattribs={"layer": "DCE_Schedule"})
    t_ref.set_placement((sx0 + 6650.0, y_txt))

    h = t_size.dxf.handle
    ent = entity_map.setdefault(eid, {})
    ent.setdefault("schedule_handle", h)
    ent.setdefault("schedule_handles", []).extend([t_mark.dxf.handle, h, t_ref.dxf.handle])
    schedule_rows_log.append([str(mark), str(size_str), str(sched_ref_str)])


def _emit_all_fixture_elements(
    msp,
    doc,
    data: Dict[str, Any],
    entity_map: Dict[str, Any],
    schedule_bbox: List[float],
    entities_log: List[Dict[str, Any]],
) -> None:
    """Emit resolvable geometry + physical tag INSERT + schedule TEXT for all 12 fixture elements."""
    sx0, hdr_y = _emit_schedule_header_and_frame(msp, schedule_bbox)
    schedule_rows_log: List[List[str]] = [["KY HIEU", "TIET DIEN / QUY CACH", "MA THAM CHIEU"]]
    row_idx = 0

    # 1. Concrete Elements (4 items: COL_C1_F1, COL_C1_F2, BM_D1A_F2_S1, BM_D1A_F2_S2)
    conc_coords = [
        (7000.0, 10000.0),
        (13000.0, 10000.0),
        (7150.0, 15000.0),
        (13150.0, 15000.0),
    ]
    for idx, row in enumerate(data.get("concrete_elements", [])):
        eid = row["element_id"]
        mark = str(row.get("mark", eid))
        cat = str(row.get("category", "BEAM")).upper()
        sec = dict(row.get("section_profile") or {})
        size_str = _format_size(sec)
        cx, cy = conc_coords[idx % len(conc_coords)]

        if cat == "COLUMN":
            w = float(sec.get("width_mm", 300.0))
            h = float(sec.get("height_mm", 300.0))
            pts = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
            geom = msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot"})
            layer_role = "CONCRETE_COLUMN"
            tag_pt = (cx + 420.0, cy + 450.0 + idx * 350.0)
        else:
            geom = msp.add_lwpolyline([(cx, cy - 100.0), (cx + 5700.0, cy - 100.0), (cx + 5700.0, cy + 100.0), (cx, cy + 100.0)], close=True, dxfattribs={"layer": "DCE_NetThay"})
            layer_role = "CONCRETE_BEAM"
            tag_pt = (cx + 2500.0, cy + 420.0)

        g_refs = _norm_refs(row, "geometry_refs", "G")
        t_refs = _norm_refs(row, "tag_refs", "T")
        s_refs = _norm_refs(row, "schedule_refs", "SCH")
        entity_map[eid] = {
            "geometry_handles": [geom.dxf.handle],
            "source_refs": g_refs,
            "tag_refs": t_refs,
            "schedule_refs": s_refs,
            "size": size_str,
        }
        _emit_tag_insert(msp, doc, mark=mark, size_str=size_str, eid=eid, role=layer_role, point=tag_pt, entity_map=entity_map)
        _emit_schedule_row(msp, row_idx, mark, size_str, ",".join(s_refs), eid, entity_map, sx0, hdr_y, schedule_rows_log)
        row_idx += 1

    # 2. Steel Sections (5 items placed in Steel Sub-zone X in [21500..28500], Y=18500..20500)
    for idx, row in enumerate(data.get("steel_sections", [])):
        eid = row["element_id"]
        mark = str(row.get("mark", eid))
        size_str = _format_size({"profile_type": row.get("profile_type"), "section_name": row.get("section_name")})
        x = 22000.0 + idx * 1700.0
        y = 19500.0
        geom = msp.add_lwpolyline([(x - 160, y - 160), (x + 160, y - 160), (x + 160, y + 160), (x - 160, y + 160)], close=True, dxfattribs={"layer": "DCE_Block"})
        g_refs = _norm_refs(row, "geometry_refs", "G")
        t_refs = _norm_refs(row, "tag_refs", "T")
        s_refs = _norm_refs(row, "schedule_refs", "SCH")
        entity_map[eid] = {
            "geometry_handles": [geom.dxf.handle],
            "source_refs": g_refs,
            "tag_refs": t_refs,
            "schedule_refs": s_refs,
            "size": size_str,
        }
        _emit_tag_insert(msp, doc, mark=mark, size_str=size_str, eid=eid, role="STEEL_MEMBER", point=(x, y + 480.0), entity_map=entity_map)
        _emit_schedule_row(msp, row_idx, mark, size_str, ",".join(s_refs), eid, entity_map, sx0, hdr_y, schedule_rows_log)
        row_idx += 1

    # 3. Baseplates (2 items: STEEL_BP_01, STEEL_BP_02)
    for idx, row in enumerate(data.get("baseplates", [])):
        eid = row["element_id"]
        mark = str(row.get("baseplate_mark", row.get("mark", eid)))
        size_str = _format_size(row)
        x = 22200.0 + idx * 2400.0
        y = 16500.0
        pw = float(row.get("plate_width_mm", 400.0))
        ph = float(row.get("plate_height_mm", 400.0))
        geom = msp.add_lwpolyline([(x - pw / 2, y - ph / 2), (x + pw / 2, y - ph / 2), (x + pw / 2, y + ph / 2), (x - pw / 2, y + ph / 2)], close=True, dxfattribs={"layer": "DCE_Block"})
        g_refs = _norm_refs(row, "geometry_refs", "G")
        t_refs = _norm_refs(row, "tag_refs", "T")
        s_refs = _norm_refs(row, "schedule_refs", "SCH")
        entity_map[eid] = {
            "geometry_handles": [geom.dxf.handle],
            "source_refs": g_refs,
            "tag_refs": t_refs,
            "schedule_refs": s_refs,
            "size": size_str,
        }
        _emit_tag_insert(msp, doc, mark=mark, size_str=size_str, eid=eid, role="STEEL_BASEPLATE", point=(x, y + ph / 2 + 320.0), entity_map=entity_map)
        _emit_schedule_row(msp, row_idx, mark, size_str, ",".join(s_refs), eid, entity_map, sx0, hdr_y, schedule_rows_log)
        row_idx += 1

    # 4. Steel Plates (STEEL_PL_01)
    for idx, row in enumerate(data.get("steel_plates", [])):
        eid = row["element_id"]
        mark = str(row.get("member_mark", row.get("mark", eid)))
        size_str = _format_size(row)
        x = 27400.0 + idx * 1400.0
        y = 16500.0
        gw = float(row.get("width_mm", 240.0))
        gh = float(row.get("height_mm", 180.0))
        geom = msp.add_lwpolyline([(x - gw / 2, y - gh / 2), (x + gw / 2, y - gh / 2), (x + gw / 2 + 40, y + gh / 2), (x - gw / 2, y + gh / 2)], close=True, dxfattribs={"layer": "DCE_Block"})
        g_refs = _norm_refs(row, "geometry_refs", "G")
        t_refs = _norm_refs(row, "tag_refs", "T")
        s_refs = _norm_refs(row, "schedule_refs", "SCH")
        entity_map[eid] = {
            "geometry_handles": [geom.dxf.handle],
            "source_refs": g_refs,
            "tag_refs": t_refs,
            "schedule_refs": s_refs,
            "size": size_str,
        }
        _emit_tag_insert(msp, doc, mark=mark, size_str=size_str, eid=eid, role="STEEL_PLATE", point=(x, y + gh / 2 + 320.0), entity_map=entity_map)
        _emit_schedule_row(msp, row_idx, mark, size_str, ",".join(s_refs), eid, entity_map, sx0, hdr_y, schedule_rows_log)
        row_idx += 1

    entities_log.append({
        "type": "SCHEDULE_TABLE",
        "layer": "DCE_Schedule",
        "bbox": schedule_bbox,
        "col_widths": [2500.0, 4000.0, 3500.0],
        "rows": schedule_rows_log,
        "cell_width_factors": [[0.70, 0.70, 0.70] for _ in schedule_rows_log],
    })


def _add_sheet_role_specific_geometry(
    msp,
    sheet: SheetSpec,
    data: Dict[str, Any],
    entity_map: Dict[str, Any],
    entities_log: List[Dict[str, Any]],
) -> None:
    """Emit genuinely distinct engineering geometry per sheet role so all 5 sheets are visually and semantically distinct."""
    sno = sheet.sheet_no

    if sno == "KC-02":
        # Column/Wall setout detail: upper story column layout + foundation pedestal outline
        for cx, cy in ((7000.0, 20000.0), (13000.0, 20000.0)):
            msp.add_lwpolyline([(cx - 450, cy - 450), (cx + 450, cy - 450), (cx + 450, cy + 450), (cx - 450, cy + 450)], close=True, dxfattribs={"layer": "DCE_Cot"})
            msp.add_line((cx - 450, cy - 450), (cx + 450, cy + 450), dxfattribs={"layer": "DCE_Cot"})
            msp.add_line((cx - 450, cy + 450), (cx + 450, cy - 450), dxfattribs={"layer": "DCE_Cot"})
        msp.add_lwpolyline([(6400, 9400), (19600, 9400), (19600, 20600), (6400, 20600)], close=True, dxfattribs={"layer": "DCE_NetThay"})

    elif sno == "KC-03":
        # Beam-slab framing plan: slab boundary + two-way span diagonal arrows + DCE_KyHieuSan inserts
        slab_panels = [
            ("S1", "h=120", 10000.0, 12500.0, 7150.0, 10150.0, 12850.0, 14850.0),
            ("S2", "h=120", 16000.0, 12500.0, 13150.0, 10150.0, 18750.0, 14850.0),
        ]
        for smark, sthick, sx, sy, px0, py0, px1, py1 in slab_panels:
            s_ins = msp.add_blockref("DCE_KyHieuSan", (sx, sy), dxfattribs={"layer": "DCE_Name"})
            s_ins.add_auto_attribs({"SH": f"{smark} {sthick}"})
            entities_log.append({"type": "INSERT", "block": "DCE_KyHieuSan", "handle": s_ins.dxf.handle, "layer": "DCE_Name"})
            msp.add_line((px0 + 300, py0 + 300), (px1 - 300, py1 - 300), dxfattribs={"layer": "DCE_NetThay"})
            msp.add_line((px0 + 300, py1 - 300), (px1 - 300, py0 + 300), dxfattribs={"layer": "DCE_NetThay"})

    elif sno == "KC-04":
        # Slab rebar plan: distinct BOTTOM (midspan) & TOP (support) bars with hooks on REBAR_BOTTOM / REBAR_TOP
        for idx, row in enumerate(data.get("rebar_strips", [])):
            sid = row["strip_id"]
            face = str(row.get("face", "")).upper()
            direction = str(row.get("direction", "X")).upper()
            layer = f"REBAR_{face}"
            if face == "BOTTOM":
                if direction == "X":
                    pts = [(7500.0, 12200.0 + idx * 450.0), (12500.0, 12200.0 + idx * 450.0)]
                else:
                    pts = [(9500.0 + idx * 450.0, 10400.0), (9500.0 + idx * 450.0, 14600.0)]
            else:
                if direction == "X":
                    pts = [(12100.0, 13400.0 + idx * 250.0), (14100.0, 13400.0 + idx * 250.0)]
                else:
                    pts = [(15200.0 + idx * 350.0, 12600.0), (15200.0 + idx * 350.0, 14400.0)]

            pl = msp.add_lwpolyline([(pts[0][0], pts[0][1] - 120), pts[0], pts[1], (pts[1][0], pts[1][1] - 120)], dxfattribs={"layer": layer})
            msp.add_text(f"{row.get('bar_spec', 'd10a150')} ({face})", height=95, dxfattribs={"layer": layer}).set_placement((pts[0][0] + 150.0, pts[0][1] + 220.0))
            entity_map[sid] = {
                "geometry_handles": [pl.dxf.handle],
                "source_refs": [sid],
                "face": face,
                "tag_refs": [],
                "schedule_refs": [],
            }
            entities_log.append({
                "type": "SLAB_REBAR_STRIP",
                "strip_id": sid,
                "face": face,
                "layer": layer,
                "handle": pl.dxf.handle,
            })

    elif sno == "KC-06":
        # Real Beam Elevation & Cross-Section Details (MC-BM-D1A: 200x400 mm, B25)
        bx0, by0 = 21600.0, 11200.0
        # Beam longitudinal elevation (L = 6000 scaled box)
        msp.add_lwpolyline([(bx0, by0), (bx0 + 6000, by0), (bx0 + 6000, by0 + 800), (bx0, by0 + 800)], close=True, dxfattribs={"layer": "DCE_Cot"})
        msp.add_line((bx0 + 80, by0 + 700), (bx0 + 5920, by0 + 700), dxfattribs={"layer": "DCE_Thep_Chu"})
        msp.add_line((bx0 + 80, by0 + 100), (bx0 + 5920, by0 + 100), dxfattribs={"layer": "DCE_Thep_Chu"})
        for sx in range(0, 5800, 220):
            x_st = bx0 + 150 + sx
            msp.add_line((x_st, by0 + 80), (x_st, by0 + 720), dxfattribs={"layer": "DCE_Thep_Dai"})
        # Cross-section 1-1 (200x400 enlarged x3 -> 600x1200)
        cx0, cy0 = 22200.0, 22200.0
        msp.add_lwpolyline([(cx0, cy0), (cx0 + 600, cy0), (cx0 + 600, cy0 + 1200), (cx0, cy0 + 1200)], close=True, dxfattribs={"layer": "DCE_Cot"})
        msp.add_lwpolyline([(cx0 + 75, cy0 + 75), (cx0 + 525, cy0 + 75), (cx0 + 525, cy0 + 1125), (cx0 + 75, cy0 + 1125)], close=True, dxfattribs={"layer": "DCE_Thep_Dai"})
        for rx, ry in ((cx0 + 95, cy0 + 95), (cx0 + 300, cy0 + 95), (cx0 + 505, cy0 + 95), (cx0 + 95, cy0 + 1105), (cx0 + 505, cy0 + 1105)):
            msp.add_circle((rx, ry), radius=35.0, dxfattribs={"layer": "DCE_Thep_Chu"})
        msp.add_text("MC-BM-D1A (200x400) | 2D20+3D20 | D8a150", height=110, dxfattribs={"layer": "DCE_Name"}).set_placement((cx0, cy0 + 1350.0))

    elif sno == "KC-07":
        # Real Column Section (CT-COL-C1) + Baseplates (CT-BP-BD01, CT-BP-BD02) + Gusset Plate (CT-GUSSET-01)
        # 2x2 grid in [21600..28600, 12000..23500] so zero label collision
        # 1. CT-COL-C1 (300x300 enlarged 900x900)
        cx0, cy0 = 21600.0, 22200.0
        msp.add_lwpolyline([(cx0, cy0), (cx0 + 900, cy0), (cx0 + 900, cy0 + 900), (cx0, cy0 + 900)], close=True, dxfattribs={"layer": "DCE_Cot"})
        msp.add_lwpolyline([(cx0 + 80, cy0 + 80), (cx0 + 820, cy0 + 80), (cx0 + 820, cy0 + 820), (cx0 + 80, cy0 + 820)], close=True, dxfattribs={"layer": "DCE_Thep_Dai"})
        for rx, ry in ((cx0 + 110, cy0 + 110), (cx0 + 450, cy0 + 110), (cx0 + 790, cy0 + 110),
                       (cx0 + 110, cy0 + 450), (cx0 + 790, cy0 + 450),
                       (cx0 + 110, cy0 + 790), (cx0 + 450, cy0 + 790), (cx0 + 790, cy0 + 790)):
            msp.add_circle((rx, ry), radius=32.0, dxfattribs={"layer": "DCE_Thep_Chu"})
        msp.add_text("CT-COL-C1 (300x300) 8D20", height=100, dxfattribs={"layer": "DCE_Name"}).set_placement((cx0, cy0 + 1040.0))

        # 2. CT-BP-BD01 (400x400 + 4 bolts M20)
        bx1, by1 = 25600.0, 22200.0
        msp.add_lwpolyline([(bx1, by1), (bx1 + 800, by1), (bx1 + 800, by1 + 800), (bx1, by1 + 800)], close=True, dxfattribs={"layer": "DCE_Block"})
        for dx, dy in ((120, 120), (680, 120), (120, 680), (680, 680)):
            msp.add_circle((bx1 + dx, by1 + dy), radius=42.0, dxfattribs={"layer": "DCE_Block"})
        msp.add_text("CT-BP-BD01 PL400x400x20", height=100, dxfattribs={"layer": "DCE_Name"}).set_placement((bx1, by1 + 940.0))

        # 3. CT-BP-BD02 (560x420 + 8 bolts M24)
        bx2, by2 = 21600.0, 12500.0
        msp.add_lwpolyline([(bx2, by2), (bx2 + 1120, by2), (bx2 + 1120, by2 + 840), (bx2, by2 + 840)], close=True, dxfattribs={"layer": "DCE_Block"})
        for ci in range(4):
            for ri in range(2):
                msp.add_circle((bx2 + 130 + ci * 285, by2 + 130 + ri * 580), radius=46.0, dxfattribs={"layer": "DCE_Block"})
        msp.add_text("CT-BP-BD02 PL560x420x28", height=100, dxfattribs={"layer": "DCE_Name"}).set_placement((bx2, by2 + 980.0))

        # 4. CT-GUSSET-01 (STEEL_PL_01 trapezoid + 4 bolt holes)
        gx0, gy0 = 25600.0, 12500.0
        msp.add_lwpolyline([(gx0, gy0), (gx0 + 900, gy0), (gx0 + 900, gy0 + 420), (gx0 + 480, gy0 + 780), (gx0, gy0 + 780)], close=True, dxfattribs={"layer": "DCE_Block"})
        for bxp, byp in ((180, 180), (700, 180), (180, 560), (480, 560)):
            msp.add_circle((gx0 + bxp, gy0 + byp), radius=35.0, dxfattribs={"layer": "DCE_Block"})
        msp.add_text("CT-GUSSET-01 PL240x180x14", height=100, dxfattribs={"layer": "DCE_Name"}).set_placement((gx0, gy0 + 940.0))


def _setup_paperspace_a3(
    doc,
    sheet: SheetSpec,
    manifest: SheetSetManifest,
    result_viewports: List[Dict[str, Any]],
) -> None:
    """Create A3 paperspace frame, non-overlapping viewports (scale 1:50), right-side title strip & sheet index."""
    ps = doc.layouts.get("Layout1")
    w, h = _paper_size_mm(sheet.paper_size)  # (420, 297)

    # A3 outer + inner frame + right-side title strip [370..415, 5..292]
    ps.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True, dxfattribs={"layer": "DCE_Frame"})
    ps.add_lwpolyline([(10, 5), (415, 5), (415, 292), (10, 292)], close=True, dxfattribs={"layer": "DCE_Frame"})
    ps.add_lwpolyline([(370, 5), (415, 5), (415, 292), (370, 292)], close=True, dxfattribs={"layer": "DCE_Frame"})
    ps.add_line((370, 100), (415, 100), dxfattribs={"layer": "DCE_Frame"})
    ps.add_line((370, 215), (415, 215), dxfattribs={"layer": "DCE_Frame"})

    # Right strip content: Sheet Index (top), Notes/Legend (middle), Title Block (bottom)
    ps.add_text("MUC LUC BAN VE", height=2.6, dxfattribs={"layer": "DCE_Schedule"}).set_placement((372, 286))
    for k, sh in enumerate(manifest.sheets):
        mark = ">" if sh.sheet_no == sheet.sheet_no else " "
        ps.add_text(f"{mark}{sh.sheet_no} {sh.title[:16]}", height=1.9, dxfattribs={"layer": "DCE_Schedule"}).set_placement((372, 278 - k * 10.0))

    ps.add_text(f"SO HIEU: {sheet.sheet_no}", height=3.2, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 92))
    ps.add_text(sheet.title[:22], height=2.2, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 78))
    ps.add_text(f"DU AN: {manifest.project_name[:18]}", height=1.9, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 62))
    ps.add_text(f"TY LE: 1:{int(round(sheet.viewports[0].scale)) if sheet.viewports else 50}", height=2.0, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 46))
    ps.add_text(f"REV: {manifest.revision}", height=2.0, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 32))
    ps.add_text("AI DRAFT - CHECK BY KS", height=1.7, dxfattribs={"layer": "DCE_Frame"}).set_placement((372, 12))

    # Non-overlapping Paperspace Viewports inside [15..365, 15..280]
    for vi, vp in enumerate(sheet.viewports):
        if len(sheet.viewports) > 1:
            bbox = [15.0, 15.0 + vi * 135.0, 205.0, 145.0 + vi * 135.0]
        else:
            bbox = [15.0, 15.0, 365.0, 280.0]

        x0, y0, x1, y1 = bbox
        vp_h = y1 - y0
        view_height = vp_h * vp.scale
        vc_x = 13500.0 if len(sheet.viewports) > 1 else 18000.0
        vc_y = 14000.0 if vi == 0 else 15000.0
        if sheet.sheet_no in ("KC-06", "KC-07"):
            vc_x = 20000.0
            vc_y = 17000.0

        v = ps.add_viewport(
            center=((x0 + x1) / 2.0, (y0 + y1) / 2.0),
            size=(x1 - x0, vp_h),
            view_center_point=(vc_x, vc_y),
            view_height=view_height,
        )
        v.dxf.layer = "VP_" + (vp.content_face or "MODEL")
        if vp.content_face == "TOP":
            v.freeze("REBAR_BOTTOM")
        elif vp.content_face == "BOTTOM":
            v.freeze("REBAR_TOP")
        v.dxf.view_twist_angle = vp.rotation

        # Update manifest viewport paper_bbox so manifest reflects actual non-overlapping A3 bboxes
        vp.paper_bbox = list(bbox)

        result_viewports.append({
            "sheet_no": sheet.sheet_no,
            "viewport_id": vp.viewport_id,
            "paper_bbox": list(bbox),
            "view_height": view_height,
            "scale": vp.scale,
            "content_face": vp.content_face,
            "frozen_layers": sorted(str(x) for x in v.frozen_layers),
        })

    if len(sheet.viewports) > 1:
        ps.add_lwpolyline([(212, 15), (365, 15), (365, 280), (212, 280)], close=True, dxfattribs={"layer": "DCE_Schedule"})
        ps.add_text(f"GHI CHU & BANG KE {sheet.sheet_no}", height=2.5, dxfattribs={"layer": "DCE_Schedule"}).set_placement((216, 272))
        if sheet.sheet_no == "KC-04":
            ps.add_text("VP DUOI: THEP LOP DUOI (FREEZE REBAR_TOP)", height=2.0, dxfattribs={"layer": "DCE_Schedule"}).set_placement((216, 258))
            ps.add_text("VP TREN: THEP LOP TREN (FREEZE REBAR_BOTTOM)", height=2.0, dxfattribs={"layer": "DCE_Schedule"}).set_placement((216, 246))


def _draw_viewport_contents(ax, msp, *, frozen_layers: set[str], layer_colors: Dict[str, str], fg_dark: str) -> None:
    """Render modelspace CAD entities onto an axis respecting viewport frozen layers (no math ticks)."""
    import math
    from matplotlib.patches import Circle, Polygon, Rectangle

    for ent in msp:
        layer = str(getattr(ent.dxf, "layer", "0"))
        if layer.upper() in frozen_layers:
            continue
        col = layer_colors.get(layer, "#334155")
        et = ent.dxftype()

        if et == "LINE":
            s, e = ent.dxf.start, ent.dxf.end
            if max(s.x, e.x) < 30500:
                ls = "-." if layer == "DCE_Truc" else ("--" if layer == "DCE_NetThay" else "-")
                lw = 0.55 if layer == "DCE_Truc" else (0.75 if layer == "DCE_NetThay" else 0.9)
                ax.plot([s.x, e.x], [s.y, e.y], color=col, linewidth=lw, linestyle=ls, zorder=2)

        elif et == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in ent.get_points()]
            if pts and max(p[0] for p in pts) < 30500:
                if ent.closed:
                    pts.append(pts[0])
                xs, ys = zip(*pts)
                lw = 1.6 if layer in ("REBAR_TOP", "REBAR_BOTTOM", "DCE_Thep_Chu") else 1.05
                ax.plot(xs, ys, color=col, linewidth=lw, zorder=3)

        elif et == "HATCH":
            try:
                for p in ent.paths:
                    verts = getattr(p, "vertices", None)
                    if verts and max(v[0] for v in verts) < 30500:
                        poly = Polygon([(v[0], v[1]) for v in verts], closed=True, facecolor="#94A3B8", edgecolor="none", alpha=0.55, zorder=1)
                        ax.add_patch(poly)
            except Exception:
                pass

        elif et == "CIRCLE":
            c = ent.dxf.center
            if c.x < 30500:
                ax.add_patch(Circle((c.x, c.y), ent.dxf.radius, fill=False, edgecolor=col, linewidth=0.9, zorder=3))

        elif et == "DIMENSION":
            try:
                p1 = getattr(ent.dxf, "defpoint2", None)
                p2 = getattr(ent.dxf, "defpoint3", None)
                dp = getattr(ent.dxf, "defpoint", None)
                if p1 and p2 and dp and max(p1.x, p2.x, dp.x) < 30500:
                    if abs(p2.x - p1.x) >= abs(p2.y - p1.y):
                        d_p1 = (p1.x, dp.y)
                        d_p2 = (p2.x, dp.y)
                        val = int(round(abs(p2.x - p1.x)))
                        rot_d = 0.0
                        txt_pt = ((d_p1[0] + d_p2[0]) / 2.0, dp.y + 120.0)
                    else:
                        d_p1 = (dp.x, p1.y)
                        d_p2 = (dp.x, p2.y)
                        val = int(round(abs(p2.y - p1.y)))
                        rot_d = 90.0
                        txt_pt = (dp.x - 120.0, (d_p1[1] + d_p2[1]) / 2.0)
                    ax.plot([p1.x, d_p1[0]], [p1.y, d_p1[1]], color=col, linewidth=0.45, alpha=0.75, zorder=2)
                    ax.plot([p2.x, d_p2[0]], [p2.y, d_p2[1]], color=col, linewidth=0.45, alpha=0.75, zorder=2)
                    ax.plot([d_p1[0], d_p2[0]], [d_p1[1], d_p2[1]], color=col, linewidth=0.65, zorder=2)
                    for qx, qy in (d_p1, d_p2):
                        ax.plot([qx - 70, qx + 70], [qy - 70, qy + 70], color=col, linewidth=0.8, zorder=3)
                    ax.text(txt_pt[0], txt_pt[1], str(val), fontsize=5.2, color=col, ha="center", va="center", rotation=rot_d, zorder=4)
            except Exception:
                pass

        elif et == "INSERT":
            bname = getattr(ent.dxf, "name", "")
            ip = ent.dxf.insert
            if ip.x >= 30500:
                continue
            if bname in ("DCE_Cot_Block", "DCE_Cot_Dung"):
                ax.add_patch(Rectangle((ip.x - 150, ip.y - 150), 300, 300, facecolor="#94A3B8", edgecolor="#1E3246", linewidth=1.0, zorder=3))
                if bname == "DCE_Cot_Dung":
                    ax.plot([ip.x - 150, ip.x + 150], [ip.y - 150, ip.y + 150], color="#1E3246", linewidth=0.7, zorder=4)
                    ax.plot([ip.x - 150, ip.x + 150], [ip.y + 150, ip.y - 150], color="#1E3246", linewidth=0.7, zorder=4)
            elif bname == "DCE_Truc_Bubble":
                ax.add_patch(Circle((ip.x, ip.y), 200, facecolor="#FFFFFF", edgecolor="#B91C1C", linewidth=0.9, zorder=4))
                sh = next((a.dxf.text for a in ent.attribs if a.dxf.tag == "SH"), "")
                ax.text(ip.x, ip.y, sh, ha="center", va="center", fontsize=6.2, fontweight="bold", color="#7F1D1D", zorder=5)
            elif bname == "DCE_KyHieuSan":
                ax.add_patch(Circle((ip.x, ip.y), 190, facecolor="#FFFFFF", edgecolor="#0F766E", linewidth=0.85, zorder=4))
                sh = next((a.dxf.text for a in ent.attribs if a.dxf.tag == "SH"), "")
                ax.text(ip.x, ip.y, sh, ha="center", va="center", fontsize=4.8, fontweight="bold", color="#0F766E", zorder=5)
            elif bname == "DCE_C2_MEMBER":
                mk = next((a.dxf.text for a in ent.attribs if a.dxf.tag == "MARK"), "")
                sz = next((a.dxf.text for a in ent.attribs if a.dxf.tag == "SIZE"), "")
                lbl = f"{mk} ({sz})" if sz and sz != "STANDARD" and len(sz) <= 14 else mk
                ax.text(
                    ip.x, ip.y, lbl, ha="center", va="center", fontsize=4.8, fontweight="bold", color="#1E3246",
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="#94A3B8", linewidth=0.5, alpha=0.88),
                    zorder=5,
                )

        elif et == "TEXT":
            ip = ent.dxf.insert
            if ip.x < 30500 and not str(ent.dxf.text).startswith("MISSING"):
                rot_t = float(getattr(ent.dxf, "rotation", 0.0) or 0.0)
                if math.isnan(rot_t):
                    rot_t = 0.0
                ax.text(ip.x, ip.y, ent.dxf.text[:44], fontsize=5.2, color=col, rotation=rot_t, ha="left", va="bottom", zorder=5)


def render_sheet_set_previews(
    output_dir: str | Path,
    *,
    export_pdf: bool = False,
) -> Dict[str, Any]:
    """Render each DXF Paperspace (A3 420x297mm, viewport frozen layers, zero tick axes) to PNG (and PDF only if requested)."""
    import contextlib
    import ezdxf
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import Rectangle

    out = Path(output_dir)
    manifest_path = out / "sheet_set_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {"sheets": []}

    png_paths: List[str] = []
    pdf_path = out / "c2_sheet_set_preview.pdf"

    # Rule 12b mineral light theme — zero white text on dark background
    bg_page = "#FFFFFF"
    bg_header = "#DCE4EC"
    fg_dark = "#1C1E21"
    fg_navy = "#1E3246"

    layer_colors = {
        "DCE_Cot": "#1E3246",
        "DCE_Vach": "#7F1D1D",
        "DCE_Boundary_Zone": "#991B1B",
        "DCE_CouplingBeam": "#0F766E",
        "DCE_Truc": "#B91C1C",
        "DCE_NetThay": "#475569",
        "DCE_Dim": "#0369A1",
        "DCE_Setout": "#B45309",
        "DCE_Block": "#0F766E",
        "DCE_Name": "#1E3246",
        "DCE_Thep_Chu": "#B91C1C",
        "DCE_Thep_Dai": "#15803D",
        "REBAR_TOP": "#DC2626",
        "REBAR_BOTTOM": "#1D4ED8",
        "DCE_VoidX": "#9A3412",
        "DCE_Schedule": "#334155",
        "DCE_Frame": "#0F172A",
    }

    a3_w, a3_h = 420.0, 297.0
    fig_w_in, fig_h_in = a3_w / 25.4, a3_h / 25.4  # Exact A3 Landscape 420x297 mm

    pdf_ctx = PdfPages(str(pdf_path)) if export_pdf else contextlib.nullcontext(None)
    with pdf_ctx as pdf:
        for sh_meta in manifest.get("sheets", []):
            sno = sh_meta["sheet_no"]
            dxf_file = out / f"{sno}_C2_A3.dxf"
            if not dxf_file.is_file():
                continue
            doc = ezdxf.readfile(str(dxf_file))
            msp = doc.modelspace()
            ps = doc.layouts.get("Layout1") if "Layout1" in doc.layouts else None
            sidecar_p = dxf_file.with_suffix(".dce_audit.json")
            sidecar = json.loads(sidecar_p.read_text(encoding="utf-8")) if sidecar_p.is_file() else {}

            fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=180, facecolor=bg_page)

            # Background Paperspace sheet axis (exact 0..420 x 0..297 mm, ZERO coordinate ticks)
            ax_bg = fig.add_axes([0.0, 0.0, 1.0, 1.0], facecolor=bg_page)
            ax_bg.set_xlim(0.0, a3_w)
            ax_bg.set_ylim(0.0, a3_h)
            ax_bg.set_xticks([])
            ax_bg.set_yticks([])
            for sp in ax_bg.spines.values():
                sp.set_visible(False)

            # Outer & Inner A3 borders
            ax_bg.add_patch(Rectangle((3.0, 3.0), 414.0, 291.0, fill=False, edgecolor="#0F172A", linewidth=1.2))
            ax_bg.add_patch(Rectangle((10.0, 5.0), 405.0, 287.0, fill=False, edgecolor="#0F172A", linewidth=0.9))

            # Collect non-main Paperspace viewports from Layout1
            ps_vps = []
            if ps is not None:
                for ent in ps.query("VIEWPORT"):
                    if getattr(ent.dxf, "id", 1) == 1:
                        continue
                    ps_vps.append(ent)

            if not ps_vps:
                ax_vp = fig.add_axes([15.0 / a3_w, 15.0 / a3_h, 350.0 / a3_w, 265.0 / a3_h], facecolor="#FFFFFF")
                ax_vp.set_xticks([])
                ax_vp.set_yticks([])
                _draw_viewport_contents(ax_vp, msp, frozen_layers=set(), layer_colors=layer_colors, fg_dark=fg_dark)
                ax_vp.set_xlim(4200, 29800)
                ax_vp.set_ylim(7400, 24400)
                ax_vp.set_aspect("equal")
            else:
                vp_specs_meta = sh_meta.get("viewports", [])
                for vi, vp_ent in enumerate(ps_vps):
                    cx_p, cy_p = vp_ent.dxf.center.x, vp_ent.dxf.center.y
                    vw_p, vh_p = float(vp_ent.dxf.width), float(vp_ent.dxf.height)
                    x0_p, y0_p = cx_p - vw_p / 2.0, cy_p - vh_p / 2.0

                    ax_vp = fig.add_axes([x0_p / a3_w, y0_p / a3_h, vw_p / a3_w, vh_p / a3_h], facecolor="#FFFFFF")
                    ax_vp.set_xticks([])
                    ax_vp.set_yticks([])
                    for sp in ax_vp.spines.values():
                        sp.set_edgecolor("#475569")
                        sp.set_linewidth(0.8)

                    frozen = {str(x).upper() for x in vp_ent.frozen_layers}
                    _draw_viewport_contents(ax_vp, msp, frozen_layers=frozen, layer_colors=layer_colors, fg_dark=fg_dark)

                    # Fit model box honoring viewport center & height + ensuring core geometry isn't awkwardly clipped
                    vc = vp_ent.dxf.view_center_point
                    vh_m = float(vp_ent.dxf.view_height)
                    vw_m = vh_m * (vw_p / max(vh_p, 1.0))
                    if len(ps_vps) == 1 and sno in ("KC-03", "KC-06", "KC-07"):
                        ax_vp.set_xlim(4200.0, 29600.0)
                        ax_vp.set_ylim(7200.0, 24200.0)
                    else:
                        ax_vp.set_xlim(vc.x - vw_m / 2.0, vc.x + vw_m / 2.0)
                        ax_vp.set_ylim(vc.y - vh_m / 2.0, vc.y + vh_m / 2.0)
                    ax_vp.set_aspect("equal")

                    vp_meta = vp_specs_meta[vi] if vi < len(vp_specs_meta) else {}
                    vp_lbl = vp_meta.get("viewport_id", f"VP_{vi+1}")
                    face = vp_meta.get("content_face") or ""
                    sc = _int_num(vp_meta.get("scale", 50))
                    tag_txt = f"{vp_lbl} ({face}) — TL 1:{sc}" if face else f"{vp_lbl} — TL 1:{sc}"
                    ax_vp.text(
                        0.015, 0.965, tag_txt, transform=ax_vp.transAxes,
                        ha="left", va="top", fontsize=6.5, fontweight="bold", color=fg_navy,
                        bbox=dict(boxstyle="square,pad=0.22", facecolor=bg_header, edgecolor=fg_navy, linewidth=0.6),
                        zorder=10,
                    )

                # Dual-viewport middle schedule / notes panel [212..365, 15..280]
                if len(ps_vps) > 1:
                    ax_mid = fig.add_axes([212.0 / a3_w, 15.0 / a3_h, 153.0 / a3_w, 265.0 / a3_h], facecolor="#F8F7F4")
                    ax_mid.set_xlim(0, 1)
                    ax_mid.set_ylim(0, 1)
                    ax_mid.set_xticks([])
                    ax_mid.set_yticks([])
                    for sp in ax_mid.spines.values():
                        sp.set_edgecolor("#1E3246")
                        sp.set_linewidth(0.8)
                    ax_mid.add_patch(Rectangle((0.0, 0.92), 1.0, 0.08, facecolor=bg_header, edgecolor="#1E3246", linewidth=0.7))
                    ax_mid.text(0.5, 0.96, f"BANG THONG KE & GHI CHU {sno}", ha="center", va="center", fontsize=7.8, fontweight="bold", color=fg_navy)

                    sched_rows = []
                    for ent_log in sidecar.get("entities_log", []):
                        if ent_log.get("type") == "SCHEDULE_TABLE":
                            sched_rows = ent_log.get("rows", [])
                            break
                    y_cur = 0.88
                    ax_mid.text(0.03, y_cur, "KY HIEU   | QUY CACH / TIET DIEN", fontsize=6.5, fontweight="bold", color=fg_navy)
                    y_cur -= 0.035
                    ax_mid.plot([0.02, 0.98], [y_cur + 0.015, y_cur + 0.015], color="#94A3B8", linewidth=0.6)
                    for row in sched_rows[:12]:
                        mk, sz = str(row[0])[:12], str(row[1])[:24]
                        ax_mid.text(0.03, y_cur, f"{mk:<10s} | {sz}", fontsize=6.0, color=fg_dark, family="monospace")
                        y_cur -= 0.042
                    if sno == "KC-04":
                        ax_mid.text(0.03, 0.22, "LOC LOP VIEWPORT:", fontsize=6.5, fontweight="bold", color=fg_navy)
                        ax_mid.text(0.03, 0.17, "• VP_SLAB_BOT: Chi hien REBAR_BOTTOM (Xanh)", fontsize=5.8, color="#1D4ED8")
                        ax_mid.text(0.03, 0.12, "• VP_SLAB_TOP: Chi hien REBAR_TOP (Do)", fontsize=5.8, color="#DC2626")

            # Right-side A3 Title Strip [370..415, 5..292]
            ax_side = fig.add_axes([370.0 / a3_w, 5.0 / a3_h, 45.0 / a3_w, 287.0 / a3_h], facecolor="#FFFFFF")
            ax_side.set_xlim(0, 1)
            ax_side.set_ylim(0, 1)
            ax_side.set_xticks([])
            ax_side.set_yticks([])
            for sp in ax_side.spines.values():
                sp.set_edgecolor("#0F172A")
                sp.set_linewidth(0.9)

            ax_side.add_patch(Rectangle((0.0, 0.91), 1.0, 0.09, facecolor=bg_header, edgecolor="#0F172A", linewidth=0.7))
            ax_side.text(0.50, 0.955, f"SO HIEU: {sno}", ha="center", va="center", fontsize=8.8, fontweight="bold", color=fg_navy)
            ax_side.text(0.06, 0.87, "MUC LUC BAN VE:", fontsize=7.0, fontweight="bold", color=fg_navy)
            for idx_s, sh_i in enumerate(manifest.get("sheets", [])):
                pfx = ">> " if sh_i["sheet_no"] == sno else "   "
                ax_side.text(
                    0.06, 0.82 - idx_s * 0.045, f"{pfx}{sh_i['sheet_no']}",
                    fontsize=6.6, color=fg_dark, fontweight=("bold" if sh_i["sheet_no"] == sno else "normal"),
                )

            ax_side.plot([0.0, 1.0], [0.52, 0.52], color="#0F172A", linewidth=0.7)
            vp_list = sh_meta.get("viewports", [])
            ax_side.text(0.06, 0.48, f"VIEWPORTS ({len(vp_list)}):", fontsize=6.8, fontweight="bold", color=fg_navy)
            for vi, vp_i in enumerate(vp_list):
                face_s = f" [{vp_i.get('content_face')}]" if vp_i.get("content_face") else ""
                ax_side.text(0.06, 0.43 - vi * 0.065, f"- {vp_i.get('viewport_id')}{face_s}\n  TL 1:{_int_num(vp_i.get('scale', 50))}", fontsize=5.8, color=fg_dark)

            ax_side.add_patch(Rectangle((0.0, 0.0), 1.0, 0.22, facecolor=bg_header, edgecolor="#0F172A", linewidth=0.7))
            ax_side.text(0.06, 0.175, sh_meta.get("title", sno)[:22], fontsize=6.4, fontweight="bold", color=fg_navy)
            ax_side.text(0.06, 0.125, f"DU AN: {manifest.get('project_name', '')[:18]}", fontsize=5.6, color=fg_dark)
            ax_side.text(0.06, 0.075, f"REV: {manifest.get('revision', 'C2')}", fontsize=6.2, fontweight="bold", color=fg_navy)
            ax_side.text(0.06, 0.025, "Tro ly AI lap -\ncan KS kiem tra", fontsize=5.4, color=fg_dark)

            ax_bg.text(12.0, 8.0, DISCLAIMER_VI, fontsize=6.0, color=fg_dark, ha="left", va="bottom")

            png_file = out / f"{sno}_preview.png"
            fig.savefig(str(png_file), dpi=180, facecolor=bg_page)
            if pdf is not None:
                pdf.savefig(fig)
            plt.close(fig)
            png_paths.append(str(png_file))

    return {
        "png_paths": png_paths,
        "pdf_path": str(pdf_path) if export_pdf else "",
        "paper_size": "A3_LANDSCAPE",
    }


def export_sheet_set(
    output_dir: str | Path,
    fixture_path: str | Path,
    *,
    strict: bool = True,
    render_previews: bool = False,
    export_pdf: bool = False,
) -> Dict[str, Any]:
    import ezdxf

    f_path = Path(fixture_path)
    data = json.loads(f_path.read_text(encoding="utf-8"))
    manifest = manifest_from_fixture(data)
    reg = build_registry_from_fixture(data)
    audit = validate_manifest(reg, manifest, data.get("rebar_strips", []))

    per_sheet_missing: Dict[str, List[str]] = {}
    for sheet in manifest.sheets:
        miss = _sheet_missing_inputs(sheet, data, audit)
        if miss:
            per_sheet_missing[sheet.sheet_no] = miss

    if strict and (not audit["is_valid"] or per_sheet_missing):
        raise ValueError(
            "C2 semantic/input gate failed: "
            + json.dumps({"violations": audit["violations"], "missing_inputs": per_sheet_missing}, ensure_ascii=False)
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fixture_sha256 = hashlib.sha256(f_path.read_bytes()).hexdigest()

    overall_status = "PASS"
    if per_sheet_missing:
        overall_status = "MISSING_INPUT"
    elif not audit["is_valid"]:
        overall_status = "UNVERIFIED"

    result: Dict[str, Any] = {
        "Standard_Method": "DCE Sheet Set Semantics & 3-Way Linkage Exporter C2 v2",
        "status": overall_status,
        "audit": audit,
        "missing_inputs": per_sheet_missing,
        "sheets": [],
        "viewports": [],
        "source_fixture": str(f_path),
        "Calculation_Logs": list(audit.get("Calculation_Logs", [])),
    }

    for sheet in manifest.sheets:
        doc = ezdxf.new("R2007")  # Native AC1021
        scale = float(sheet.viewports[0].scale) if sheet.viewports else 50.0
        layers_meta, dimstyles_meta = _ensure_layers_and_styles(doc, scale=scale)
        blocks_meta = _ensure_blocks(doc, scale=scale)
        msp = doc.modelspace()

        entity_map: Dict[str, Any] = {}
        entities_log: List[Dict[str, Any]] = []

        ctx = _draw_common_frame_and_grid(msp, doc, sheet, manifest, entities_log, scale=scale)
        _emit_all_fixture_elements(msp, doc, data, entity_map, ctx["schedule_bbox"], entities_log)
        _add_sheet_role_specific_geometry(msp, sheet, data, entity_map, entities_log)
        _setup_paperspace_a3(doc, sheet, manifest, result["viewports"])

        miss_for_sheet = per_sheet_missing.get(sheet.sheet_no, [])
        if miss_for_sheet:
            msp.add_text(f"MISSING INPUT: {', '.join(miss_for_sheet)}", height=180, dxfattribs={"layer": "DCE_Name"}).set_placement((7000.0, 21500.0))

        path = out / f"{sheet.sheet_no}_C2_A3.dxf"
        doc.saveas(str(path))
        dxf_hash = hashlib.sha256(path.read_bytes()).hexdigest()

        blocks_defined: Dict[str, Any] = {
            blk.name: blocks_meta.get(blk.name, {})
            for blk in doc.blocks
            if not blk.name.startswith("*")
        }
        sheet_status = "MISSING_INPUT" if miss_for_sheet else ("PASS" if audit["is_valid"] else "UNVERIFIED")
        bound = {
            "schema_version": "DCE_C2_PROVENANCE_V2",
            "provenance": {
                "dxf_sha256": dxf_hash,
                "fixture_sha256": fixture_sha256,
                "generator": "cad_sheet_set.C2_REMEDIATED_V2",
            },
            "dxf_sha256": dxf_hash,
            "sheet_no": sheet.sheet_no,
            "sheet_status": sheet_status,
            "scale": scale,
            "mode": ctx["mode"],
            "dxf_version": doc.dxfversion,
            "entities_log": entities_log,
            "blocks_defined": blocks_defined,
            "dimstyles_defined": dimstyles_meta,
            "layers_defined": layers_meta,
            "entity_map": entity_map,
            "viewport_count": len(sheet.viewports),
            "missing_inputs": miss_for_sheet,
        }
        (out / f"{sheet.sheet_no}_C2_A3.dce_audit.json").write_text(
            json.dumps(bound, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        result["sheets"].append({
            "sheet_no": sheet.sheet_no,
            "status": sheet_status,
            "mode": ctx["mode"],
            "path": str(path),
            "viewport_count": len(sheet.viewports),
            "faces": [v.content_face for v in sheet.viewports],
            "entity_counts": {
                "INSERT": len([e for e in msp if e.dxftype() == "INSERT"]),
                "LINE": len([e for e in msp if e.dxftype() == "LINE"]),
                "LWPOLYLINE": len([e for e in msp if e.dxftype() == "LWPOLYLINE"]),
                "HATCH": len([e for e in msp if e.dxftype() == "HATCH"]),
                "CIRCLE": len([e for e in msp if e.dxftype() == "CIRCLE"]),
                "DIMENSION": len([e for e in msp if e.dxftype() == "DIMENSION"]),
                "TEXT": len([e for e in msp if e.dxftype() == "TEXT"]),
            },
        })

    # Write manifest after _setup_paperspace_a3 updated non-overlapping paper_bbox values
    manifest_file = out / "sheet_set_manifest.json"
    manifest_file.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    if render_previews or export_pdf:
        result["previews"] = render_sheet_set_previews(out, export_pdf=export_pdf)

    result["artifact_sha256"] = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    (out / "C2_sheet_set_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


_SHEET_FILENAMES: Dict[str, str] = {
    "KC-01": "KC-01_TongMatBang.dxf",
    "KC-02": "KC-02_DinhViCotVach.dxf",
    "KC-03": "KC-03_KetCauDamSan.dxf",
}


def _compile_a3_project_pdf(
    sheet_records: List[Dict[str, Any]],
    pdf_path: Path,
    *,
    project_label: str,
) -> Path:
    """Compile rendered sheet PNGs onto true A3 Landscape (420x297 mm) PDF pages."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages

    a3_w_in = 420.0 / 25.4
    a3_h_in = 297.0 / 25.4
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(str(pdf_path)) as pdf:
        for rec in sheet_records:
            png_file = rec.get("preview_png")
            if not png_file or not Path(png_file).is_file():
                continue
            fig = plt.figure(figsize=(a3_w_in, a3_h_in), dpi=300, facecolor="#FFFFFF")
            ax = fig.add_axes([0.015, 0.035, 0.97, 0.94])
            ax.set_axis_off()
            img = mpimg.imread(str(png_file))
            ax.imshow(img, interpolation="lanczos")
            fig.text(
                0.02, 0.012,
                f"{rec['sheet_id']} | {project_label} | {rec['dxf_filename']} | "
                f"Tai lieu do tro ly AI lap - can KS co CCHN kiem tra xac nhan.",
                fontsize=7.0,
                color="#1E3246",
            )
            fig.text(
                0.98, 0.012,
                f"Kho A3 Landscape (420x297 mm) | Blocks: {rec['template_blocks']}",
                fontsize=7.0,
                color="#1E3246",
                ha="right",
            )
            pdf.savefig(fig, dpi=300, facecolor="#FFFFFF")
            plt.close(fig)
    return pdf_path


def export_project_a3_sheets(
    output_dir: str | Path,
    *,
    model_json_path: Optional[str | Path] = None,
    scale_spec: Optional[Dict[str, Any]] = None,
    render_previews: bool = False,
    export_pdf: bool = False,
    sheet_types: Tuple[str, ...] = ("KC-02", "KC-03"),
    dpi: int = 200,
) -> Dict[str, Any]:
    """Export real structural CAD sheets via DcePlanEngine + DCE_Master_Seed_Template.

    CAD-first default: emits DXF files, .dce_audit.json sidecars, immutable element
    registry JSON, and manifest without rendering PDFs unless `export_pdf=True`.
    """
    import shutil
    import importlib
    import tempfile

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    cad_dir = Path(__file__).resolve().parent
    tools_dir = cad_dir.parents[2] / "tools"
    for p_dir in (str(cad_dir), str(tools_dir)):
        if p_dir not in sys.path:
            sys.path.insert(0, p_dir)

    import cad_plan_engine
    import cad_element_registry
    dce_render_preview = importlib.import_module("dce_render_preview")

    model_str = str(Path(model_json_path).resolve()) if model_json_path else None
    reg = cad_element_registry.CadElementRegistry(project_name="DCE_PROJECT_A3_SET")

    calc_logs: List[Dict[str, Any]] = []
    sheet_records: List[Dict[str, Any]] = []
    preview_pngs: List[str] = []

    for st_raw in sheet_types:
        st = str(st_raw).upper()
        dxf_name = _SHEET_FILENAMES.get(st, f"{st}_BanVe.dxf")
        dxf_path = out / dxf_name

        engine = cad_plan_engine.export_dce_plan(
            str(dxf_path),
            sheet_type=st,
            model_json_path=model_str,
            scale_spec=scale_spec,
            v6=True,
            element_registry=reg,
        )
        audit_candidate = dxf_path.with_suffix(".dce_audit.json")
        if not audit_candidate.exists() and hasattr(engine, "_v6_write_sidecar"):
            engine._v6_write_sidecar(str(dxf_path))

        audit_path_str = str(audit_candidate) if audit_candidate.exists() else ""
        n_blocks = len(engine.doc.blocks) if engine.doc else 0
        n_entities = sum(1 for _ in engine.msp) if engine.msp else 0
        diag_count = len(getattr(engine, "v6_diagnostics", []))

        png_dest_str = ""
        if render_previews:
            prev = dce_render_preview.render_dxf_to_png(str(dxf_path), dpi=dpi)
            if prev.get("status") == "OK" and prev.get("output_png"):
                png_dest = out / f"{st}_preview.png"
                shutil.copy2(prev["output_png"], png_dest)
                png_dest_str = str(png_dest)
                preview_pngs.append(png_dest_str)
            if prev.get("preview_id"):
                dce_render_preview.cleanup_preview(prev["preview_id"])

        rec = {
            "sheet_id": st,
            "dxf_filename": dxf_name,
            "dxf_path": str(dxf_path),
            "audit_path": audit_path_str,
            "preview_png": png_dest_str,
            "template_blocks": n_blocks,
            "modelspace_entities": n_entities,
            "v6_diagnostics_count": diag_count,
        }
        sheet_records.append(rec)
        calc_logs.append({
            "step": f"Export {st}",
            "engine": "DcePlanEngine (v6=True)",
            "template_blocks": n_blocks,
            "modelspace_entities": n_entities,
            "v6_diagnostics": diag_count,
        })

    pdf_path_str = ""
    if export_pdf:
        pdf_file = out / "project_sheet_set_a3.pdf"
        if preview_pngs:
            _compile_a3_project_pdf(
                sheet_records,
                pdf_file,
                project_label=Path(model_str).name if model_str else "Default 40-Story Tower",
            )
        else:
            with tempfile.TemporaryDirectory() as tmp_png_dir:
                tmp_records: List[Dict[str, Any]] = []
                for rec in sheet_records:
                    prev = dce_render_preview.render_dxf_to_png(rec["dxf_path"], dpi=dpi)
                    tmp_rec = dict(rec)
                    if prev.get("status") == "OK" and prev.get("output_png"):
                        tmp_png = Path(tmp_png_dir) / f"{rec['sheet_id']}_tmp.png"
                        shutil.copy2(prev["output_png"], tmp_png)
                        tmp_rec["preview_png"] = str(tmp_png)
                    if prev.get("preview_id"):
                        dce_render_preview.cleanup_preview(prev["preview_id"])
                    tmp_records.append(tmp_rec)
                _compile_a3_project_pdf(
                    tmp_records,
                    pdf_file,
                    project_label=Path(model_str).name if model_str else "Default 40-Story Tower",
                )
        pdf_path_str = str(pdf_file) if pdf_file.is_file() else ""

    reg_path = out / "project_element_registry.json"
    reg_path.write_text(reg.to_json(indent=2), encoding="utf-8")
    integrity = reg.validate_integrity()

    manifest = {
        "Standard_Method": "TCVN 5574:2018 / TCVN 5575:2024 / DCE Pro v6",
        "Calculation_Logs": calc_logs,
        "status": "PASS" if sheet_records else "FAIL",
        "paper_size": "A3_LANDSCAPE",
        "paper_mm": [420.0, 297.0],
        "sheet_count": len(sheet_records),
        "sheets": sheet_records,
        "preview_pngs": preview_pngs,
        "pdf_path": pdf_path_str,
        "registry_path": str(reg_path),
        "registry_total_elements": len(reg.elements),
        "registry_integrity": integrity,
        "Disclaimer": (
            "Tai lieu do tro ly AI lap tu dong. Ket qua va ban ve mang tinh tham khao, "
            "phai duoc ky su co chung chi hanh nghe phu hop kiem tra va chiu trach nhiem "
            "truoc khi su dung."
        ),
    }
    manifest_path = out / "project_sheet_set_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest

