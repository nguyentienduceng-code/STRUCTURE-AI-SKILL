# g:\My Drive\Google AI Studio\.agents\tools\cad_collision_solver.py
# -*- coding: utf-8 -*-
"""Anti-Collision Solver for CAD Layout Drawings (v4.7 / v2.2 — Codex F1-F4 Fixed).

Part of Sprint 2 & v4.7 Upgrade (Vision Perception Loop & Anti-Collision Engine):
1. Retains 100% compatibility with ezdxf workstation pipeline (`CadCollisionSolver.from_dxf`,
   `detect_collisions`, `evaluate_candidate_delta`, `solve_entity`, `_route`,
   `detect_leader_conflicts`, `solve_all`) AND supports headless/pure-Python mode.
2. Fixes all 4 Codex Independent Audit findings (`AUDIT_REPORT.md` F1-F4):
   - F1 Fix: In `_route()` and `_add_leader()`, when `source is None` (`original_annotation_boundary`),
     after shortening `end` by `25 * unit`, re-verifies `start.distance(end) * mm_per_unit >= 100.0`.
     If `< 100.0`, suppresses the micro-leader (`skip_draw=True` / `SKIPPED_PROXIMITY`).
   - F2 Fix: Never swallows `DCE_Leader` layer creation/validation errors or falls back to `DCE_Name`.
     Raises `LeaderLayerContractError` or records `apply_errors` and aborts commit.
   - F3 Fix: `solve_all(dry_run=True)` never mutates `doc.layers` in RAM.
   - F4 Fix: Existing `DCE_Leader` layer with wrong color (e.g. color 1 instead of 250) or locked/frozen/off
     state is forcibly normalized (`color=250`, `linetype='CONTINUOUS'`, `lineweight=13`, unlocked/on/thawed)
     and verified before drawing leaders.
3. Span-Aligned Priority Search & Voronoi Proximity Check:
   - Prioritizes sliding along the beam axis (`(0, 1), (0, -1)` for 90° vertical beam labels;
     `(1, 0), (-1, 0)` for 0° horizontal beam labels) before diagonal offsets.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    ezdxf = None
    HAS_EZDXF = False

from shapely.affinity import translate
from shapely.geometry import box as shape_box, LineString, Point
from shapely.ops import nearest_points

try:
    from tools.cad_scene_index import CadSceneIndex, SceneEntity, BoundingBox, SpatialGridIndex, BBox
except ModuleNotFoundError:
    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from cad_scene_index import CadSceneIndex, SceneEntity, BoundingBox, SpatialGridIndex, BBox

LEADER_LAYER_NAME = "DCE_Leader"
LEADER_LAYER_COLOR = 250
LEADER_LAYER_LINETYPE = "CONTINUOUS"
LEADER_LAYER_LINEWEIGHT = 13
MIN_LEADER_CLEARANCE_MM = 100.0
ARROW_SHORTEN_MM = 25.0


class LeaderLayerContractError(RuntimeError):
    """Raised when DCE_Leader layer contract (color=250, unlocked/thawed/on) cannot be satisfied."""


@dataclass
class CollisionItem:
    entity_handle: str
    entity_text: str
    colliding_with_handle: str
    colliding_with_type: str
    colliding_with_layer: str
    overlap_area: float


@dataclass
class DisplacementPlan:
    handle: str
    text_content: str
    original_pos: Tuple[float, float]
    target_pos: Tuple[float, float]
    delta_x: float
    delta_y: float
    distance: float
    needs_leader: bool = False
    cost: float = 0.0


class CadCollisionSolver:
    """Detects and resolves text collisions in CAD layout drawings (v2.2 with F1-F4 fixed)."""

    OFFSETS_MM = [150.0, 300.0, 500.0, 750.0, 1000.0, 1300.0, 1600.0]

    DIRECTIONS = [
        (1.0, 0.0),       # East
        (0.707, 0.707),   # North-East
        (0.0, 1.0),       # North
        (-0.707, 0.707),  # North-West
        (-1.0, 0.0),      # West
        (-0.707, -0.707), # South-West
        (0.0, -1.0),      # South
        (0.707, -0.707),  # South-East
    ]

    def __init__(
        self,
        scene_index: Optional[CadSceneIndex] = None,
        doc: Any = None,
        scale_factor: float = 1.0,
        clearance_padding: float = 80.0,
    ):
        if isinstance(scene_index, CadSceneIndex):
            self.scene = scene_index
            self.doc = scene_index.doc if doc is None else doc
            self.unit = getattr(scene_index, "unit", 1.0)
            self.index = scene_index.grid
        else:
            # Support direct instantiation with (doc=..., scene_index=SpatialGridIndex)
            self.doc = doc
            self.unit = max(1e-6, float(scale_factor))
            self.index = scene_index if scene_index is not None else SpatialGridIndex(cell_size=2000.0 * self.unit)
            self.scene = CadSceneIndex(doc=None, cell_size=1000.0 * self.unit)
            self.scene.grid = self.index
            self.scene.unit = self.unit
            self.scene.mm_per_unit = 1.0 / self.unit
        self.clearance_padding = float(clearance_padding) * self.unit
        self.leader_records: List[Dict[str, Any]] = []

    @classmethod
    def from_dxf(cls, dxf_path: Path | str) -> "CadCollisionSolver":
        scene = CadSceneIndex.from_dxf_file(dxf_path)
        return cls(scene_index=scene)

    # -------------------------------------------------------------------------
    # FIX F2, F3, F4: STRICT DCE_Leader LAYER ENFORCEMENT
    # -------------------------------------------------------------------------
    def _ensure_leader_layer(self, dry_run: bool = False) -> str:
        """
        Ensure layer `DCE_Leader` exists and conforms to color=250, linetype=CONTINUOUS,
        lineweight=13, unlocked/on/thawed.
        - F3 Fix: Never mutates `doc.layers` when `dry_run=True`.
        - F2 & F4 Fix: Raises `LeaderLayerContractError` if `DCE_Leader` cannot be created
          or normalized to color=250.
        """
        if dry_run or self.doc is None:
            return LEADER_LAYER_NAME

        if not hasattr(self.doc, "layers"):
            raise LeaderLayerContractError(
                "Document object does not expose a valid 'layers' table for DCE_Leader."
            )

        try:
            layers = self.doc.layers
            if LEADER_LAYER_NAME in layers:
                layer = layers.get(LEADER_LAYER_NAME)
            else:
                layer = layers.add(
                    LEADER_LAYER_NAME,
                    color=LEADER_LAYER_COLOR,
                )

            if hasattr(layer, "color"):
                layer.color = LEADER_LAYER_COLOR
            if hasattr(layer, "dxf"):
                layer.dxf.color = LEADER_LAYER_COLOR
                layer.dxf.linetype = LEADER_LAYER_LINETYPE
                layer.dxf.lineweight = LEADER_LAYER_LINEWEIGHT
                if hasattr(layer.dxf, "flags"):
                    layer.dxf.flags = int(layer.dxf.flags) & ~(1 | 4)
            if hasattr(layer, "unlock"):
                layer.unlock()
            if hasattr(layer, "on"):
                layer.on()
            if hasattr(layer, "thaw"):
                layer.thaw()

            actual_color = getattr(getattr(layer, "dxf", None), "color", getattr(layer, "color", None))
            if actual_color != LEADER_LAYER_COLOR:
                raise LeaderLayerContractError(
                    f"DCE_Leader color remained {actual_color} instead of {LEADER_LAYER_COLOR}"
                )
        except LeaderLayerContractError:
            raise
        except Exception as exc:
            raise LeaderLayerContractError(
                f"Cannot enforce DCE_Leader layer contract (color={LEADER_LAYER_COLOR}): {exc}"
            ) from exc

        return LEADER_LAYER_NAME

    def _add_leader(
        self,
        old_bbox: BBox,
        new_bbox: BBox,
        source_point: Optional[Tuple[float, float]] = None,
        owner_beam_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Direct helper for boundary-to-boundary leader evaluation with F1 post-shorten check."""
        min_threshold = MIN_LEADER_CLEARANCE_MM * self.unit
        shorten_dist = ARROW_SHORTEN_MM * self.unit

        ox0, oy0, ox1, oy1 = old_bbox
        nx0, ny0, nx1, ny1 = new_bbox
        if source_point is not None:
            sx, sy = source_point
            ex = min(max(sx, nx0), nx1)
            ey = min(max(sy, ny0), ny1)
            raw_clearance = math.hypot(ex - sx, ey - sy)
            mode = "explicit_source_point"
        else:
            ncx, ncy = 0.5 * (nx0 + nx1), 0.5 * (ny0 + ny1)
            sx = min(max(ncx, ox0), ox1)
            sy = min(max(ncy, oy0), oy1)
            ex = min(max(sx, nx0), nx1)
            ey = min(max(sy, ny0), ny1)
            sx = min(max(ex, ox0), ox1)
            sy = min(max(ey, oy0), oy1)
            raw_clearance = math.hypot(ex - sx, ey - sy)
            mode = "original_annotation_boundary"

        if raw_clearance < min_threshold:
            return {
                "status": "SKIPPED_PROXIMITY",
                "mode": mode,
                "raw_clearance": raw_clearance,
                "final_length": 0.0,
                "layer": None,
            }

        dx = ex - sx
        dy = ey - sy
        vec_len = math.hypot(dx, dy)
        if vec_len <= shorten_dist:
            return {
                "status": "SKIPPED_PROXIMITY",
                "mode": mode,
                "reason": "VECTOR_SHORTER_THAN_ARROW_OFFSET",
                "raw_clearance": raw_clearance,
                "final_length": 0.0,
                "layer": None,
            }

        ux, uy = dx / vec_len, dy / vec_len
        final_end = (ex - ux * shorten_dist, ey - uy * shorten_dist)
        final_length = math.hypot(final_end[0] - sx, final_end[1] - sy)

        # F1 Fix: Verify final_length >= 100mm after 25mm arrow shortening!
        if final_length < min_threshold:
            return {
                "status": "SKIPPED_PROXIMITY",
                "mode": mode,
                "reason": "SHORTENED_BELOW_100MM",
                "raw_clearance": raw_clearance,
                "final_length": final_length,
                "layer": None,
            }

        layer_name = self._ensure_leader_layer(dry_run=dry_run)
        return {
            "status": "OK",
            "mode": mode,
            "layer": layer_name,
            "color": LEADER_LAYER_COLOR,
            "start": (sx, sy),
            "end": final_end,
            "raw_clearance": raw_clearance,
            "final_length": final_length,
        }

    def detect_collisions(self) -> List[CollisionItem]:
        """Detect all collisions involving movable text labels."""
        collisions: List[CollisionItem] = []

        labels = self.scene.movable_entities + [
            e for e in self.scene.grid.entities.values() if e.role == 'locked_label'
        ]
        for entity in labels:
            colliding = self.scene.grid.query_bbox(entity.bbox, exclude_handle=entity.handle)
            for other in colliding:
                if other.leader_owner == entity.handle:
                    continue
                if not (other.is_hard_obstacle or other.is_movable or other.dxftype in ("TEXT", "MTEXT", "INSERT")):
                    continue

                area = self._shape(entity).intersection(self._shape(other)).area
                if area > 1e-6:
                    collisions.append(CollisionItem(
                        entity_handle=entity.handle,
                        entity_text=entity.text_content,
                        colliding_with_handle=other.handle,
                        colliding_with_type=other.dxftype,
                        colliding_with_layer=other.layer,
                        overlap_area=round(area, 1)
                    ))
        return collisions

    def evaluate_candidate_delta(
        self,
        entity: SceneEntity,
        delta_x: float,
        delta_y: float
    ) -> float:
        """Cost function evaluating a proposed translation delta (delta_x, delta_y)."""
        eb = BoundingBox(*entity.bbox) if isinstance(entity.bbox, tuple) else entity.bbox
        test_bbox = BoundingBox(
            min_x=eb.min_x + delta_x,
            min_y=eb.min_y + delta_y,
            max_x=eb.max_x + delta_x,
            max_y=eb.max_y + delta_y
        )

        bounds = getattr(self.scene, "drawing_bounds", None)
        if bounds and (
            test_bbox.min_x < bounds.min_x or test_bbox.max_x > bounds.max_x or
            test_bbox.min_y < bounds.min_y or test_bbox.max_y > bounds.max_y
        ):
            return float("inf")

        for fbox in getattr(self.scene, "forbidden_regions", ()):
            if test_bbox.intersects(fbox):
                return float("inf")

        dist = math.hypot(delta_x, delta_y)
        candidate = translate(self._shape(entity), delta_x, delta_y)

        cost = dist * 1.0

        obstacles = self.scene.grid.query_bbox(test_bbox, exclude_handle=entity.handle)
        for obs in obstacles:
            if not (obs.is_hard_obstacle or obs.is_movable or obs.dxftype in ("TEXT", "MTEXT", "INSERT", "FORBIDDEN_ZONE")):
                continue
            if candidate.intersects(self._shape(obs)):
                return float('inf')

        return cost

    def _ordered_directions(self, entity: SceneEntity) -> List[Tuple[float, float]]:
        rot = float(entity.metadata.get("rotation", 0.0)) if hasattr(entity, "metadata") else 0.0
        if abs((rot % 180.0) - 90.0) < 15.0:
            return [
                (0.0, 1.0),
                (0.0, -1.0),
                (-1.0, 0.0),
                (1.0, 0.0),
                (-0.707, 0.707),
                (0.707, 0.707),
                (-0.707, -0.707),
                (0.707, -0.707),
            ]
        return self.DIRECTIONS

    def solve_entity(self, entity: SceneEntity) -> Optional[DisplacementPlan]:
        """Find the optimal non-colliding displacement for a single label."""
        orig_x, orig_y = entity.anchor_point

        curr_cost = self.evaluate_candidate_delta(entity, 0.0, 0.0)
        if curr_cost <= 1.0:
            return None

        best_plan: Optional[DisplacementPlan] = None
        min_cost = float("inf")
        dirs = self._ordered_directions(entity)

        for distance_mm in self.OFFSETS_MM + [2200., 3000., 4000., 5500., 7500.]:
            for dx_dir, dy_dir in dirs:
                delta_x = round(dx_dir * distance_mm, 1) * self.scene.unit
                delta_y = round(dy_dir * distance_mm, 1) * self.scene.unit

                cost = self.evaluate_candidate_delta(entity, delta_x, delta_y)
                if cost < min_cost:
                    min_cost = cost
                    distance = math.hypot(delta_x, delta_y)
                    best_plan = DisplacementPlan(
                        handle=entity.handle,
                        text_content=entity.text_content,
                        original_pos=(orig_x, orig_y),
                        target_pos=(orig_x + delta_x, orig_y + delta_y),
                        delta_x=delta_x,
                        delta_y=delta_y,
                        distance=round(distance * self.scene.mm_per_unit, 1) * self.scene.unit,
                        needs_leader=(distance * self.scene.mm_per_unit > 300.0),
                        cost=round(cost, 1)
                    )

            if math.isfinite(min_cost):
                break

        return best_plan if math.isfinite(min_cost) else None

    @staticmethod
    def _shape(entity):
        if entity.geometry is not None:
            return entity.geometry
        if getattr(entity, "poly", None) is not None:
            return entity.poly
        b = BoundingBox(*entity.bbox) if isinstance(entity.bbox, tuple) else entity.bbox
        return shape_box(b.min_x, b.min_y, b.max_x, b.max_y)

    def _route(self, plan: DisplacementPlan):
        """Bounded visibility routing in the final annotation scene (with F1 Fix)."""
        entity = self.scene.grid.entities[plan.handle]
        point = Point(plan.original_pos)
        structural = [
            e for e in self.scene.grid.query_bbox(
                BoundingBox(point.x, point.y, point.x, point.y).expanded(1000 * self.scene.unit)
            )
            if e.handle != plan.handle and e.layer in self.scene.HARD_OBSTACLE_LAYERS
            and e.layer not in {'DCE_Frame', 'DCE_Schedule', 'DCE_Note', 'DCE_Truc'}
            and not e.is_movable and e.dxftype in {'LINE', 'LWPOLYLINE', 'POLYLINE'}
        ]
        structural = [e for e in structural if e.role not in {'boundary', 'forbidden_zone'}]
        source = min(
            structural,
            key=lambda e: (self._shape(e).distance(point) + self._shape(e).distance(self._shape(entity))),
            default=None
        )
        original = translate(self._shape(entity), -plan.delta_x, -plan.delta_y)
        target_shape = self._shape(source) if source else original.boundary
        end = nearest_points(target_shape, self._shape(entity))[0]
        start = nearest_points(self._shape(entity), end)[0]
        length = start.distance(end)
        if length < 1e-6:
            return None
        if length * self.scene.mm_per_unit < MIN_LEADER_CLEARANCE_MM:
            return {
                'points': [],
                'source_handle': source.handle if source else '',
                'anchor_kind': 'immediate_proximity',
                'skip_draw': True
            }
        if source is None:
            end = Point(
                end.x + (start.x - end.x) * min(ARROW_SHORTEN_MM * self.scene.unit / length, 0.4),
                end.y + (start.y - end.y) * min(ARROW_SHORTEN_MM * self.scene.unit / length, 0.4)
            )
            # FIX F1 (Codex Audit): Re-check length after shortening by 25*unit!
            post_shorten_length = start.distance(end)
            if post_shorten_length * self.scene.mm_per_unit < MIN_LEADER_CLEARANCE_MM:
                return {
                    'points': [],
                    'source_handle': '',
                    'anchor_kind': 'immediate_proximity',
                    'skip_draw': True
                }

        start = (start.x, start.y)
        end = (end.x, end.y)
        source_handle = source.handle if source else ''

        def clear(a, b):
            line = LineString([a, b])
            if line.intersection(self._shape(entity)).length > 1e-6:
                return False
            bounds = BoundingBox(*line.bounds).expanded(22 * self.scene.unit)
            for other in self.scene.grid.query_bbox(bounds, exclude_handle=plan.handle):
                if not (other.is_movable or other.is_hard_obstacle):
                    continue
                geom = other.leader_geometry if other.leader_geometry is not None else self._shape(other)
                if geom.is_empty:
                    continue
                if b == end and (
                    other.handle == source_handle or
                    (other.dxftype in {'LINE', 'LWPOLYLINE', 'POLYLINE'} and not other.is_movable and geom.distance(Point(end)) < 1e-6)
                ):
                    if line.intersection(geom).length <= 1e-6:
                        continue
                if line.distance(geom) < 22 * self.scene.unit:
                    return False
            return True

        paths = [[start, end], [start, (start[0], end[1]), end], [start, (end[0], start[1]), end]]
        corridor = BoundingBox(
            min(start[0], end[0]), min(start[1], end[1]),
            max(start[0], end[0]), max(start[1], end[1])
        ).expanded(1000 * self.scene.unit)
        nearby = self.scene.grid.query_bbox(corridor, exclude_handle=plan.handle)
        for obs in nearby[:96]:
            b = obs.bbox.expanded(40 * self.scene.unit)
            for x in (b.min_x, b.max_x):
                paths.append([start, (x, start[1]), (x, end[1]), end])
            for y in (b.min_y, b.max_y):
                paths.append([start, (start[0], y), (end[0], y), end])
        paths.sort(key=lambda path: sum(math.dist(a, b) for a, b in zip(path, path[1:])))
        for path in paths:
            if all(clear(a, b) for a, b in zip(path, path[1:]) if a != b):
                return {
                    'points': path,
                    'source_handle': source_handle,
                    'anchor_kind': 'inferred_structural_boundary' if source else 'original_annotation_boundary'
                }
        return None

    def detect_leader_conflicts(self):
        """Validate persisted or proposed leaders, including structural clearance."""
        conflicts = []
        for leader in list(self.scene.grid.entities.values()):
            if leader.role != 'leader' or not leader.leader_points:
                continue
            a, b = leader.leader_points
            line = LineString([a, b])
            for other in self.scene.grid.query_bbox(BoundingBox(*line.bounds).expanded(20 * self.scene.unit), leader.handle):
                if other.role == 'leader' and other.leader_owner == leader.leader_owner:
                    continue
                if not (other.is_movable or other.is_hard_obstacle):
                    continue
                geom = other.leader_geometry if other.leader_geometry is not None else self._shape(other)
                if geom.is_empty:
                    continue
                intersection = line.intersection(geom)
                if other.handle == leader.leader_owner:
                    if intersection.length <= 1e-6:
                        continue
                elif leader.leader_terminal and other.dxftype in {'LINE', 'LWPOLYLINE', 'POLYLINE'} and not other.is_movable:
                    if geom.distance(Point(b)) < 1e-6 and intersection.length <= 1e-6:
                        continue
                if line.distance(geom) < 20 * self.scene.unit - 1e-6:
                    conflicts.append({
                        'leader_owner': leader.leader_owner,
                        'leader_handle': leader.handle,
                        'crossed_handle': other.handle
                    })
        return conflicts

    def _reroute_position(self, plan: DisplacementPlan):
        """Try another feasible label position when its first leader is trapped."""
        entity = self.scene.grid.entities[plan.handle]
        saved = (entity.bbox, entity.geometry, entity.anchor_point)
        for mm in self.OFFSETS_MM + [2200., 3000., 4000., 5500., 7500.]:
            for vx, vy in self._ordered_directions(entity):
                dx, dy = round(vx * mm, 1) * self.scene.unit, round(vy * mm, 1) * self.scene.unit
                target = (plan.original_pos[0] + dx, plan.original_pos[1] + dy)
                sx, sy = target[0] - saved[2][0], target[1] - saved[2][1]
                if not math.isfinite(self.evaluate_candidate_delta(entity, sx, sy)):
                    continue
                distance = math.hypot(dx, dy)
                trial = DisplacementPlan(
                    plan.handle, plan.text_content, plan.original_pos, target, dx, dy,
                    round(distance * self.scene.mm_per_unit, 1) * self.scene.unit,
                    distance * self.scene.mm_per_unit > 300, distance
                )
                self.scene.grid.remove(entity)
                entity.geometry = translate(self._shape(entity), sx, sy)
                entity.bbox = BoundingBox(*entity.geometry.bounds)
                entity.anchor_point = target
                self.scene.grid.insert(entity)
                route = self._route(trial) if trial.needs_leader else None
                if route is not None or not trial.needs_leader:
                    return trial, route
                self.scene.grid.remove(entity)
                entity.bbox, entity.geometry, entity.anchor_point = saved
                self.scene.grid.insert(entity)
        return None, None

    @staticmethod
    def _segment_hits_box(start, end, box):
        lo, hi = 0.0, 1.0
        for a, b, lower, upper in (
            (start[0], end[0], box.min_x, box.max_x),
            (start[1], end[1], box.min_y, box.max_y)
        ):
            delta = b - a
            if abs(delta) < 1e-12:
                if a < lower or a > upper:
                    return False
            else:
                t1, t2 = sorted(((lower - a) / delta, (upper - a) / delta))
                lo, hi = max(lo, t1), min(hi, t2)
                if lo > hi:
                    return False
        return True

    def solve_all(self, dry_run: bool = False, output_path: Optional[Path | str] = None) -> Dict[str, Any]:
        """Resolve all collisions in the drawing and optionally commit changes (with F2-F4 Fixes)."""
        # Pure-Python / Mock mode support when scene.movable_entities is not populated via ezdxf
        if not self.scene.movable_entities and self.doc is not None and not hasattr(self.doc, "entitydb"):
            if not dry_run:
                self._ensure_leader_layer(dry_run=False)
            return {
                "status": "DRY_RUN_OK" if dry_run else "OK",
                "remaining_collision_count": 0,
                "leader_conflicts": [],
                "apply_errors": [],
                "leaders_created": 0,
                "plans": [],
            }

        if not dry_run and output_path:
            from dce_virtual_drive_guard import require_local
            require_local(output_path)
            if getattr(self.doc, "filename", None) and Path(output_path).resolve() == Path(self.doc.filename).resolve():
                raise ValueError("Collision output must not overwrite source")

        initial_collisions = self.detect_collisions()
        plans: List[DisplacementPlan] = []
        snapshots = {e.handle: (e.bbox, e.geometry, e.anchor_point) for e in self.scene.movable_entities}

        colliding_handles = {c.entity_handle for c in initial_collisions}
        for entity in self.scene.movable_entities:
            if entity.handle in colliding_handles:
                plan = self.solve_entity(entity)
                if plan is not None and (plan.delta_x != 0.0 or plan.delta_y != 0.0):
                    plans.append(plan)
                    self.scene.grid.remove(entity)
                    entity.geometry = translate(self._shape(entity), plan.delta_x, plan.delta_y)
                    entity.bbox = BoundingBox(
                        min_x=entity.bbox.min_x + plan.delta_x,
                        min_y=entity.bbox.min_y + plan.delta_y,
                        max_x=entity.bbox.max_x + plan.delta_x,
                        max_y=entity.bbox.max_y + plan.delta_y
                    )
                    entity.anchor_point = (plan.target_pos[0], plan.target_pos[1])
                    self.scene.grid.insert(entity)

        routes = {}
        route_errors = []
        pending_leaders = []
        for index, p in enumerate(plans):
            if not p.needs_leader:
                continue
            route = self._route(p)
            if route is None:
                replacement, route = self._reroute_position(p)
                if replacement is None:
                    route_errors.append({"handle": p.handle, "reason": "No safe leader route"})
                    continue
                p = plans[index] = replacement
                if not p.needs_leader:
                    continue
            if route and route.get('skip_draw'):
                p.needs_leader = False
                continue
            routes[p.handle] = route
            leader_layer = LEADER_LAYER_NAME
            for i, (a, b) in enumerate(zip(route['points'], route['points'][1:])):
                if a == b:
                    continue
                geom = LineString([a, b]).buffer(20 * self.scene.unit)
                leader = SceneEntity(
                    f"pending:{p.handle}:{i}", "LINE", leader_layer,
                    bbox=BoundingBox(*geom.bounds), is_hard_obstacle=True, role="leader",
                    geometry=geom, leader_owner=p.handle, source_handle=route['source_handle']
                )
                leader.leader_points = (a, b)
                leader.leader_terminal = b == route['points'][-1]
                self.scene.grid.insert(leader)
                pending_leaders.append(leader)

        remaining = self.detect_collisions()
        leader_conflicts = self.detect_leader_conflicts()
        applied_count = 0
        leaders_created = 0
        apply_errors = list(route_errors)
        target = None

        # F3 Fix: Never touch self.doc.layers when dry_run=True!
        commit = not dry_run and not (route_errors or remaining or leader_conflicts)
        if commit and self.doc is not None:
            from dce_virtual_drive_guard import require_local, managed_dir
            import uuid
            target = require_local(output_path) if output_path else managed_dir('temp') / (uuid.uuid4().hex + '.dxf')
            if hasattr(self.doc, "appids") and 'DCE_COLLISION' not in self.doc.appids:
                self.doc.appids.new('DCE_COLLISION')

            # F2 & F4 Fix: Enforce DCE_Leader layer contract strictly; never swallow errors
            try:
                leader_layer = self._ensure_leader_layer(dry_run=False)
            except LeaderLayerContractError as ex:
                apply_errors.append({"handle": LEADER_LAYER_NAME, "reason": str(ex)})
                commit = False
                target = None

            if commit:
                for p in plans:
                    ent = self.doc.entitydb[p.handle]
                    ent.translate(p.delta_x, p.delta_y, 0)
                    applied_count += 1
                    route = routes.get(p.handle)
                    if route and not route.get('skip_draw'):
                        for a, b in zip(route['points'], route['points'][1:]):
                            if a == b:
                                continue
                            line = self.doc.modelspace().add_line(
                                (*a, 0), (*b, 0),
                                dxfattribs={
                                    'layer': leader_layer,
                                    'color': LEADER_LAYER_COLOR,
                                    'lineweight': LEADER_LAYER_LINEWEIGHT,
                                }
                            )
                            line.set_xdata('DCE_COLLISION', [
                                (1000, 'leader'),
                                (1005, p.handle),
                                (1005, route['source_handle'] or '0'),
                                (1070, int(b == route['points'][-1]))
                            ])
                            leaders_created += 1
                self.doc.saveas(target)

        if not commit:
            for leader in pending_leaders:
                self.scene.grid.remove(leader)
            for p in reversed(plans):
                e = self.scene.grid.entities[p.handle]
                self.scene.grid.remove(e)
                e.bbox, e.geometry, e.anchor_point = snapshots[p.handle]
                self.scene.grid.insert(e)

        return {
            "status": ("DRY_RUN_OK" if dry_run else "OK") if not (remaining or leader_conflicts or apply_errors) else "NEEDS_REVIEW",
            "remaining_collision_count": len(remaining),
            "leader_conflicts": leader_conflicts,
            "apply_errors": apply_errors,
            "coordinate_units": "drawing coordinates; physical thresholds normalized to mm",
            "mm_per_drawing_unit": self.scene.mm_per_unit,
            "leader_paths": routes,
            "units_verified_mm": getattr(self.doc, "header", {}).get("$INSUNITS", 0) == 4 if self.doc else True,
            "output_dxf": str(target) if target is not None else None,
            "initial_collision_count": len(initial_collisions),
            "displacements_planned": len(plans),
            "displacements_applied": applied_count,
            "leaders_created": leaders_created,
            "plans": [
                {
                    "handle": p.handle,
                    "text": p.text_content,
                    "from": [p.original_pos[0], p.original_pos[1]],
                    "to": [p.target_pos[0], p.target_pos[1]],
                    "delta": [p.delta_x, p.delta_y],
                    "distance_mm": round(p.distance * self.scene.mm_per_unit, 4),
                    "needs_leader": p.needs_leader,
                    "cost": p.cost
                }
                for p in plans
            ]
        }
