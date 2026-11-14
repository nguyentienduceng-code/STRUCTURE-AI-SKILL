# g:\My Drive\Google AI Studio\.agents\tools\cad_scene_index.py
"""Spatial Indexing and Bounding Box Extraction for CAD DXF Drawings.

Part of Sprint 2 (Vision Perception Loop & Anti-Collision Engine).
Supports:
- Robust Bounding Box (AABB) & Polygon computation for TEXT, MTEXT, INSERT, DIMENSION.
- Spatial Grid Indexing for O(1)/O(K) collision queries.
- Classification of obstacles: HARD_OBSTACLE (columns, frames, gridlines) vs SOFT_TEXT (labels, dimensions).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import ezdxf


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

    def intersects(self, other: BoundingBox, margin: float = 0.0) -> bool:
        return not (
            self.max_x + margin < other.min_x - margin or
            self.min_x - margin > other.max_x + margin or
            self.max_y + margin < other.min_y - margin or
            self.min_y - margin > other.max_y + margin
        )

    def overlap_area(self, other: BoundingBox) -> float:
        dx = max(0.0, min(self.max_x, other.max_x) - max(self.min_x, other.min_x))
        dy = max(0.0, min(self.max_y, other.max_y) - max(self.min_y, other.min_y))
        return dx * dy

    def expanded(self, pad: float) -> BoundingBox:
        return BoundingBox(
            min_x=self.min_x - pad,
            min_y=self.min_y - pad,
            max_x=self.max_x + pad,
            max_y=self.max_y + pad
        )


@dataclass
class SceneEntity:
    handle: str
    dxftype: str
    layer: str
    text_content: str = ""
    bbox: BoundingBox = field(default_factory=lambda: BoundingBox(0, 0, 0, 0))
    is_movable: bool = False
    is_hard_obstacle: bool = False
    anchor_point: Tuple[float, float] = (0.0, 0.0)
    current_offset: Tuple[float, float] = (0.0, 0.0)
    role: str = "generic"


class CadSpatialGrid:
    """Fast Spatial Hash Grid for 2D entity collision queries."""

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
        self.entities[entity.handle] = entity
        bbox = entity.bbox
        min_cx, min_cy = self._cell_coords(bbox.min_x, bbox.min_y)
        max_cx, max_cy = self._cell_coords(bbox.max_x, bbox.max_y)

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                self.cells.setdefault((cx, cy), []).append(entity)

    def query_bbox(self, bbox: BoundingBox, exclude_handle: Optional[str] = None) -> List[SceneEntity]:
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
                        if exclude_handle and ent.handle == exclude_handle:
                            continue
                        if ent.bbox.intersects(bbox):
                            matched.append(ent)
        return matched


class CadSceneIndex:
    """Extracts, indexes, and analyzes entities from a DXF document."""

    # Layers considered as hard obstacles (cannot place text inside them)
    HARD_OBSTACLE_LAYERS = {
        "DCE_Truc", "DCE_BaoBeTong", "DCE_MainBeam", "DCE_Beam",
        "DCE_Frame", "DCE_Schedule", "DCE_Core", "DCE_Vach", "DCE_Cot"
    }

    # Layers for labels that can be relocated if colliding
    MOVABLE_TEXT_LAYERS = {
        "DCE_Name", "Dce_text", "DCE_Text", "DCE_Symbol"
    }

    def __init__(self, doc: Optional[ezdxf.document.Drawing] = None, cell_size: float = 1000.0):
        self.doc = doc
        self.grid = CadSpatialGrid(cell_size=cell_size)
        self.movable_entities: List[SceneEntity] = []
        self.hard_obstacles: List[SceneEntity] = []
        if doc is not None:
            self.index_document(doc)

    @classmethod
    def from_dxf_file(cls, dxf_path: Path | str, cell_size: float = 1000.0) -> CadSceneIndex:
        dxf_path = Path(dxf_path)
        doc = ezdxf.readfile(dxf_path)
        return cls(doc=doc, cell_size=cell_size)

    def index_document(self, doc: ezdxf.document.Drawing):
        self.doc = doc
        self.grid.clear()
        self.movable_entities.clear()
        self.hard_obstacles.clear()

        msp = doc.modelspace()
        for entity in msp:
            scene_ent = self._extract_entity_info(entity)
            if scene_ent is not None:
                self.grid.insert(scene_ent)
                if scene_ent.is_movable:
                    self.movable_entities.append(scene_ent)
                elif scene_ent.is_hard_obstacle:
                    self.hard_obstacles.append(scene_ent)

    def _extract_entity_info(self, entity) -> Optional[SceneEntity]:
        dxftype = entity.dxftype()
        layer = entity.dxf.get("layer", "0")
        handle = entity.dxf.handle

        # 1. TEXT Entity
        if dxftype == "TEXT":
            text = entity.dxf.get("text", "")
            height = float(entity.dxf.get("height", 250.0))
            insert = entity.dxf.get("insert", (0.0, 0.0, 0.0))
            rotation = float(entity.dxf.get("rotation", 0.0))
            
            # Approximate width based on character count and font aspect ratio (~0.7)
            char_w = height * 0.7
            text_len = len(text)
            est_width = max(char_w, text_len * char_w)

            x0, y0 = insert[0], insert[1]
            rad = math.radians(rotation)
            dx = est_width * math.cos(rad)
            dy = est_width * math.sin(rad)
            h_dy = height * math.cos(rad)
            h_dx = -height * math.sin(rad)

            xs = [x0, x0 + dx, x0 + h_dx, x0 + dx + h_dx]
            ys = [y0, y0 + dy, y0 + h_dy, y0 + dy + h_dy]
            bbox = BoundingBox(min(xs), min(ys), max(xs), max(ys)).expanded(50.0)

            is_movable = (layer in self.MOVABLE_TEXT_LAYERS)
            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                text_content=text,
                bbox=bbox,
                is_movable=is_movable,
                is_hard_obstacle=not is_movable,
                anchor_point=(x0, y0),
                role="text_label" if is_movable else "text_static"
            )

        # 2. MTEXT Entity
        elif dxftype == "MTEXT":
            text = entity.text
            char_height = float(entity.dxf.get("char_height", 250.0))
            insert = entity.dxf.get("insert", (0.0, 0.0, 0.0))
            defined_width = float(entity.dxf.get("width", 0.0))

            lines = text.split("\n")
            num_lines = max(1, len(lines))
            max_line_len = max(len(l) for l in lines) if lines else 1
            est_width = defined_width if defined_width > 0.0 else max_line_len * char_height * 0.7
            est_height = num_lines * char_height * 1.4

            x0, y0 = insert[0], insert[1]
            bbox = BoundingBox(x0, y0 - est_height, x0 + est_width, y0).expanded(50.0)
            is_movable = (layer in self.MOVABLE_TEXT_LAYERS)

            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                text_content=text,
                bbox=bbox,
                is_movable=is_movable,
                is_hard_obstacle=not is_movable,
                anchor_point=(x0, y0),
                role="mtext_label" if is_movable else "mtext_static"
            )

        # 3. INSERT (Block Reference, e.g., TenCauKien, BongBongTruc)
        elif dxftype == "INSERT":
            name = entity.dxf.get("name", "")
            insert = entity.dxf.get("insert", (0.0, 0.0, 0.0))
            x0, y0 = insert[0], insert[1]

            # Bounding box estimation based on block type
            if "TenCauKien" in name or "Name" in name:
                bbox = BoundingBox(x0 - 500.0, y0 - 300.0, x0 + 500.0, y0 + 300.0)
                is_movable = True
                role = "block_column_label"
            elif "Truc" in name or "KhTenTruc" in name:
                bbox = BoundingBox(x0 - 450.0, y0 - 450.0, x0 + 450.0, y0 + 450.0)
                is_movable = False
                role = "grid_bubble"
            else:
                bbox = BoundingBox(x0 - 200.0, y0 - 200.0, x0 + 200.0, y0 + 200.0)
                is_movable = False
                role = "generic_block"

            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                text_content=name,
                bbox=bbox,
                is_movable=is_movable,
                is_hard_obstacle=not is_movable,
                anchor_point=(x0, y0),
                role=role
            )

        # 4. LWPOLYLINE (Columns, Beams boundaries)
        elif dxftype == "LWPOLYLINE":
            points = entity.get_points()
            if not points:
                return None
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            bbox = BoundingBox(min(xs), min(ys), max(xs), max(ys))
            is_obstacle = (layer in self.HARD_OBSTACLE_LAYERS)

            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                bbox=bbox,
                is_movable=False,
                is_hard_obstacle=is_obstacle,
                anchor_point=bbox.center,
                role="structural_boundary" if is_obstacle else "geometry"
            )

        # 5. LINE (Gridlines, Beams)
        elif dxftype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            bbox = BoundingBox(
                min(start[0], end[0]), min(start[1], end[1]),
                max(start[0], end[0]), max(start[1], end[1])
            ).expanded(20.0)
            is_obstacle = (layer in self.HARD_OBSTACLE_LAYERS)

            return SceneEntity(
                handle=handle,
                dxftype=dxftype,
                layer=layer,
                bbox=bbox,
                is_movable=False,
                is_hard_obstacle=is_obstacle,
                anchor_point=bbox.center,
                role="linear_obstacle" if is_obstacle else "geometry"
            )

        return None

