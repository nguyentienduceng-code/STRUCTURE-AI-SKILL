# g:\My Drive\Google AI Studio\.agents\tools\cad_scene_index.py
# -*- coding: utf-8 -*-
"""Spatial broad phase and world-space geometry for supported 2D DXF entities (v4.7 / v2.2).

Upgrades in v4.7 (DCE Pro):
1. Retains 100% compatibility with ezdxf workstation pipeline (`BoundingBox`, `SceneEntity`,
   `CadSpatialGrid`, `CadSceneIndex.from_dxf_file`, `index_document`, `_extract_entity_info`, `_geometry`).
2. Integrates explicit `FORBIDDEN_ZONES` (Sidebar Schedule Table, Notes Box, Title Block,
   and Bottom Drawing Title Band) as hard obstacles so movable labels can never be displaced
   into layout tables or title blocks.
3. Provides `SpatialGridIndex` alias for pure-Python headless/sandbox environments where
   `ezdxf` is not installed.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import ezdxf
    from ezdxf import bbox as dxf_bbox
    from ezdxf import disassemble, units
    HAS_EZDXF = True
except ImportError:
    ezdxf = None
    dxf_bbox = None
    disassemble = None
    units = None
    HAS_EZDXF = False

from shapely.geometry import Polygon, LineString, GeometryCollection, box as shape_box
from shapely.ops import unary_union

BBox = Tuple[float, float, float, float]


@dataclass
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.min_x + self.max_x) / 2.0, (self.min_y + self.max_y) / 2.0)

    def intersects(self, other: "BoundingBox", margin: float = 0.0) -> bool:
        return not (
            self.max_x + margin < other.min_x - margin or
            self.min_x - margin > other.max_x + margin or
            self.max_y + margin < other.min_y - margin or
            self.min_y - margin > other.max_y + margin
        )

    def overlap_area(self, other: "BoundingBox") -> float:
        dx = max(0.0, min(self.max_x, other.max_x) - max(self.min_x, other.min_x))
        dy = max(0.0, min(self.max_y, other.max_y) - max(self.min_y, other.min_y))
        return dx * dy

    def expanded(self, pad: float) -> "BoundingBox":
        return BoundingBox(
            min_x=self.min_x - pad,
            min_y=self.min_y - pad,
            max_x=self.max_x + pad,
            max_y=self.max_y + pad
        )

    def as_tuple(self) -> BBox:
        return (self.min_x, self.min_y, self.max_x, self.max_y)


@dataclass
class SceneEntity:
    handle: str
    dxftype: str
    layer: str
    text_content: str = ""
    bbox: Any = field(default_factory=lambda: BoundingBox(0, 0, 0, 0))
    is_movable: bool = False
    is_hard_obstacle: bool = False
    anchor_point: Tuple[float, float] = (0.0, 0.0)
    current_offset: Tuple[float, float] = (0.0, 0.0)
    role: str = "generic"
    geometry: Any = None
    leader_owner: str = ""
    source_handle: str = ""
    leader_geometry: Any = None
    leader_points: Any = None
    leader_terminal: bool = False
    poly: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CadSpatialGrid:
    """Spatial hash grid for local 2D collision candidate queries."""

    def __init__(self, cell_size: float = 1000.0):
        self.cell_size = max(100.0, float(cell_size))
        self.cells: Dict[Tuple[int, int], List[SceneEntity]] = {}
        self.entities: Dict[str, SceneEntity] = {}

    def _cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        return (int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size)))

    def clear(self):
        self.cells.clear()
        self.entities.clear()

    def insert(self, entity: SceneEntity):
        if isinstance(entity.bbox, tuple):
            entity.bbox = BoundingBox(*entity.bbox)
        self.entities[entity.handle] = entity
        bbox = entity.bbox
        min_cx, min_cy = self._cell_coords(bbox.min_x, bbox.min_y)
        max_cx, max_cy = self._cell_coords(bbox.max_x, bbox.max_y)

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                self.cells.setdefault((cx, cy), []).append(entity)

    def remove(self, entity: SceneEntity | str):
        if isinstance(entity, str):
            ent_obj = self.entities.get(entity)
            if ent_obj is None:
                return
            entity = ent_obj
        if isinstance(entity.bbox, tuple):
            entity.bbox = BoundingBox(*entity.bbox)
        for key in self._keys(entity.bbox):
            bucket = self.cells.get(key, [])
            self.cells[key] = [e for e in bucket if e.handle != entity.handle]
        self.entities.pop(entity.handle, None)

    def _keys(self, box: BoundingBox):
        a, b = self._cell_coords(box.min_x, box.min_y), self._cell_coords(box.max_x, box.max_y)
        return ((x, y) for x in range(a[0], b[0] + 1) for y in range(a[1], b[1] + 1))

    def query_bbox(
        self,
        bbox: BoundingBox | BBox,
        exclude_handle: Optional[str] = None,
        exclude_handles: Optional[Set[str]] = None,
        only_static: bool = False,
    ) -> List[SceneEntity]:
        if isinstance(bbox, tuple):
            bbox = BoundingBox(*bbox)
        excl = set(exclude_handles or set())
        if exclude_handle:
            excl.add(exclude_handle)

        min_cx, min_cy = self._cell_coords(bbox.min_x, bbox.min_y)
        max_cx, max_cy = self._cell_coords(bbox.max_x, bbox.max_y)

        candidates: Set[str] = set()
        matched: List[SceneEntity] = []

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell_entities = self.cells.get((cx, cy), [])
                for ent in cell_entities:
                    if ent.handle not in candidates:
                        candidates.add(ent.handle)
                        if ent.handle in excl:
                            continue
                        if only_static and ent.is_movable:
                            continue
                        ent_box = BoundingBox(*ent.bbox) if isinstance(ent.bbox, tuple) else ent.bbox
                        if ent_box.intersects(bbox):
                            matched.append(ent)
        return matched


class SpatialGridIndex(CadSpatialGrid):
    """Pure-Python / headless compatible alias with forbidden zone registration."""

    def __init__(self, cell_size: float = 2000.0):
        super().__init__(cell_size=cell_size)
        self.forbidden_zones: List[Tuple[str, BBox]] = []

    def register_forbidden_zone(self, zone_id: str, bbox: BBox, layer: str = "DCE_Frame") -> None:
        self.forbidden_zones.append((zone_id, bbox))
        box_obj = BoundingBox(*bbox)
        self.insert(
            SceneEntity(
                handle=f"FZ_{zone_id}",
                dxftype="FORBIDDEN_ZONE",
                layer=layer,
                bbox=box_obj,
                is_movable=False,
                is_hard_obstacle=True,
                role="forbidden_zone",
                geometry=shape_box(*bbox),
                metadata={"zone_id": zone_id},
            )
        )


class CadSceneIndex:
    """Extracts, indexes, and analyzes entities from a DXF document."""

    # Layers considered as hard obstacles (cannot place text inside them)
    HARD_OBSTACLE_LAYERS = {
        "DCE_Truc", "DCE_BaoBeTong", "DCE_MainBeam", "DCE_Beam",
        "DCE_Frame", "DCE_Schedule", "DCE_Note", "DCE_Core", "DCE_Vach", "DCE_Cot"
    }

    # Layers for labels that can be relocated if colliding
    MOVABLE_TEXT_LAYERS = {
        "DCE_Name", "Dce_text", "DCE_Text", "DCE_Symbol"
    }

    def __init__(self, doc: Any = None, cell_size: float = 1000.0):
        self.doc = doc
        self.grid = CadSpatialGrid(cell_size=cell_size)
        self.movable_entities: List[SceneEntity] = []
        self.hard_obstacles: List[SceneEntity] = []
        self.forbidden_regions: List[BoundingBox] = []
        self.drawing_bounds: Optional[BoundingBox] = None
        self.mm_per_unit = 1.0
        self.unit = 1.0
        if doc is not None and HAS_EZDXF:
            self.index_document(doc)

    @classmethod
    def from_dxf_file(cls, dxf_path: Path | str, cell_size: float = 1000.0) -> "CadSceneIndex":
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf is required for CadSceneIndex.from_dxf_file")
        dxf_path = Path(dxf_path)
        doc = ezdxf.readfile(dxf_path)
        return cls(doc=doc, cell_size=cell_size)

    def register_forbidden_box(self, zone_id: str, box: BoundingBox, layer: str = "DCE_Frame"):
        """Register an impenetrable forbidden layout zone (Sidebar / TitleBlock / Notes / TitleBand)."""
        self.forbidden_regions.append(box)
        geom = shape_box(box.min_x, box.min_y, box.max_x, box.max_y)
        ent = SceneEntity(
            handle=f"FORBIDDEN:{zone_id}",
            dxftype="LWPOLYLINE",
            layer=layer,
            text_content=zone_id,
            bbox=box,
            is_movable=False,
            is_hard_obstacle=True,
            anchor_point=box.center,
            role="forbidden_zone",
            geometry=geom,
        )
        self.grid.insert(ent)
        self.hard_obstacles.append(ent)

    def index_document(self, doc: Any):
        self.doc = doc
        self.drawing_bounds = None
        code = doc.header.get('$INSUNITS', 0)
        if not code:
            raise ValueError('INSUNITS must specify drawing units before collision resolution')
        self.mm_per_unit = units.conversion_factor(code, 4)
        self.unit = 1.0 / self.mm_per_unit
        self.grid.clear()
        self.movable_entities.clear()
        self.hard_obstacles.clear()
        self.forbidden_regions.clear()

        msp = doc.modelspace()
        # Title block, Schedule table, and Notes box contents are fixed even when the
        # template puts them on the same annotation layer as structural labels.
        title_regions: List[BoundingBox] = []
        for frame in msp.query('LWPOLYLINE[layer=="DCE_Frame"]'):
            ext = dxf_bbox.extents([frame], fast=True)
            if ext.has_data and ext.extmax.x - ext.extmin.x < 50000 * self.unit:
                tbox = BoundingBox(ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
                title_regions.append(tbox)
                self.forbidden_regions.append(tbox)

        for sched_or_note in msp.query('LWPOLYLINE[layer=="DCE_Schedule" | layer=="DCE_Note"]'):
            ext = dxf_bbox.extents([sched_or_note], fast=True)
            if ext.has_data:
                sbox = BoundingBox(ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
                title_regions.append(sbox)
                self.forbidden_regions.append(sbox)

        for entity in msp:
            scene_ent = self._extract_entity_info(entity)
            if scene_ent is not None:
                if entity.has_xdata('DCE_SCENE') and any(
                    t.code == 1000 and t.value == 'boundary_only' for t in entity.get_xdata('DCE_SCENE')
                ):
                    scene_ent.role = 'boundary'
                locked = doc.layers.get(entity.dxf.layer).is_locked() or entity.has_xdata("DCE_USER_OVERRIDE")
                title = any(
                    b.min_x <= scene_ent.anchor_point[0] <= b.max_x and b.min_y <= scene_ent.anchor_point[1] <= b.max_y
                    for b in title_regions
                )
                if locked or title:
                    if scene_ent.is_movable:
                        scene_ent.role = 'title_content' if title else 'locked_label'
                    scene_ent.is_movable = False
                    scene_ent.is_hard_obstacle = True
            if scene_ent is not None:
                if entity.dxftype() == "LWPOLYLINE" and scene_ent.layer == "DCE_Frame" and scene_ent.bbox.width > 50000 * self.unit:
                    box = scene_ent.bbox
                    if self.drawing_bounds is None or box.width < self.drawing_bounds.width:
                        self.drawing_bounds = box
                    pts = list(entity.get_points("xy"))
                    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
                        edge = SceneEntity(
                            f"{scene_ent.handle}:edge:{i}",
                            "LINE",
                            scene_ent.layer,
                            bbox=BoundingBox(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])).expanded(20 * self.unit),
                            is_hard_obstacle=True,
                            geometry=LineString([a, b]).buffer(20 * self.unit),
                        )
                        self.grid.insert(edge)
                        self.hard_obstacles.append(edge)
                    continue
                if scene_ent.geometry is None:
                    scene_ent.geometry = self._geometry(entity)
                if scene_ent.geometry.is_empty:
                    continue
                scene_ent.bbox = BoundingBox(*scene_ent.geometry.bounds)
                if scene_ent.role == 'boundary' or (entity.dxftype() == 'LINE' and scene_ent.layer == 'DCE_Truc'):
                    scene_ent.leader_geometry = GeometryCollection()
                elif entity.dxftype() == 'DIMENSION':
                    scene_ent.leader_geometry = self._geometry(entity, text_only=True)
                self.grid.insert(scene_ent)
                if scene_ent.is_movable:
                    self.movable_entities.append(scene_ent)
                elif scene_ent.is_hard_obstacle:
                    self.hard_obstacles.append(scene_ent)

    def _extract_entity_info(self, entity) -> Optional[SceneEntity]:
        dxftype = entity.dxftype()
        layer = entity.dxf.get("layer", "0")
        handle = entity.dxf.handle

        if dxftype in {"TEXT", "MTEXT", "INSERT", "DIMENSION", "POLYLINE", "LWPOLYLINE"}:
            geometry = self._geometry(entity)
            if geometry.is_empty:
                return None
            box = BoundingBox(*geometry.bounds)
            name = entity.dxf.get("name", "") if dxftype == "INSERT" else ""
            movable = (dxftype in {"TEXT", "MTEXT"} and layer in self.MOVABLE_TEXT_LAYERS)
            movable |= dxftype == "INSERT" and name in {"TenCauKien", "Dce_KhTenDam"} and layer in self.MOVABLE_TEXT_LAYERS
            anchor = entity.dxf.get("insert", (0, 0, 0)) if dxftype in {"TEXT", "MTEXT", "INSERT"} else (*box.center, 0)
            text = entity.plain_text() if dxftype in {"TEXT", "MTEXT"} else name
            rot = float(entity.dxf.get("rotation", 0.0)) if dxftype in {"TEXT", "MTEXT", "INSERT"} else 0.0
            ent = SceneEntity(
                handle,
                dxftype,
                layer,
                text,
                box,
                movable,
                not movable and (dxftype not in {"POLYLINE", "LWPOLYLINE"} or layer in self.HARD_OBSTACLE_LAYERS),
                (anchor[0], anchor[1]),
                role="label" if movable else "obstacle",
                geometry=geometry,
            )
            ent.metadata["rotation"] = rot
            return ent

        elif dxftype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            bbox = BoundingBox(
                min(start[0], end[0]), min(start[1], end[1]),
                max(start[0], end[0]), max(start[1], end[1])
            ).expanded(20.0)
            links = [t.value for t in entity.get_xdata('DCE_COLLISION') if t.code == 1005] if entity.has_xdata('DCE_COLLISION') else []
            is_obstacle = (layer in self.HARD_OBSTACLE_LAYERS) or bool(links)

            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                bbox=bbox,
                is_movable=False,
                is_hard_obstacle=is_obstacle,
                anchor_point=bbox.center,
                role="leader" if links else "linear_obstacle" if is_obstacle else "geometry",
                leader_owner=links[0] if links else "",
                source_handle=links[1] if len(links) > 1 else "",
                leader_points=((start.x, start.y), (end.x, end.y)) if links else None,
                leader_terminal=next((bool(t.value) for t in entity.get_xdata('DCE_COLLISION') if t.code == 1070), True) if links else False
            )

        return None

    def _geometry(self, entity, text_only=False):
        """World-space primitives, preserving empty space inside dimensions/blocks."""
        shapes = []
        boundary_only = entity.has_xdata('DCE_SCENE') and any(
            tag.code == 1000 and tag.value == 'boundary_only' for tag in entity.get_xdata('DCE_SCENE')
        )
        for item in disassemble.recursive_decompose([entity]):
            if text_only and item.dxftype() not in {'TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF', 'SOLID'}:
                continue
            primitive = disassemble.make_primitive(item, max_flattening_distance=5 * self.unit)
            pts = [(v.x, v.y) for v in primitive.vertices()]
            if len(pts) < 2:
                continue
            kind = item.dxftype()
            text = kind in {'TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF'}
            closed = len(pts) > 2 and pts[0] == pts[-1]
            filled = text or (
                closed and not boundary_only
                and entity.dxf.layer in self.HARD_OBSTACLE_LAYERS
                and entity.dxf.layer != 'DCE_Truc'
            )
            geom = Polygon(pts).buffer(0) if filled else LineString(pts)
            shapes.append(geom.buffer((50 if text else 20) * self.unit, join_style=2))
        return shapes[0] if len(shapes) == 1 else unary_union(shapes) if shapes else GeometryCollection()
