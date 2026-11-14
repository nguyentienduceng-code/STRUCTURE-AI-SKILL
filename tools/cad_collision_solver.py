# g:\My Drive\Google AI Studio\.agents\tools\cad_collision_solver.py
"""Anti-Collision Solver for CAD Layout Drawings.

Part of Sprint 2 (Vision Perception Loop & Anti-Collision Engine).
Algorithms:
- Spatial Conflict Detection between Text Labels, Structural Elements, Grid Lines.
- Exact Bounding Box translation tracking (delta_x, delta_y).
- Dynamic Grid Updating for sequential multi-label mutual avoidance.
- Multi-objective Cost Function (Hard penalty for obstacles, soft penalty for distance).
- Automatic Leader Line generation for displaced annotations (> 300mm).
- Support for dry_run mode and lossless DXF modification.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import ezdxf

try:
    from tools.cad_scene_index import CadSceneIndex, SceneEntity, BoundingBox
except ModuleNotFoundError:
    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from cad_scene_index import CadSceneIndex, SceneEntity, BoundingBox


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
    """Detects and resolves text collisions in CAD layout drawings."""

    # Offsets in millimeters to test in each direction
    OFFSETS_MM = [150.0, 300.0, 500.0, 750.0, 1000.0, 1300.0, 1600.0]

    # 8 search directions: E, NE, N, NW, W, SW, S, SE
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

    def __init__(self, scene_index: CadSceneIndex):
        self.scene = scene_index
        self.doc = scene_index.doc

    @classmethod
    def from_dxf(cls, dxf_path: Path | str) -> CadCollisionSolver:
        scene = CadSceneIndex.from_dxf_file(dxf_path)
        return cls(scene)

    def detect_collisions(self) -> List[CollisionItem]:
        """Detect all collisions involving movable text labels."""
        collisions: List[CollisionItem] = []

        for entity in self.scene.movable_entities:
            colliding = self.scene.grid.query_bbox(entity.bbox, exclude_handle=entity.handle)
            for other in colliding:
                # Only check collision against hard obstacles or other text/block labels
                if not (other.is_hard_obstacle or other.is_movable or other.dxftype in ("TEXT", "MTEXT", "INSERT")):
                    continue

                area = entity.bbox.overlap_area(other.bbox)
                if area > 100.0:  # Ignore microscopic rounding overlaps
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
        test_bbox = BoundingBox(
            min_x=entity.bbox.min_x + delta_x,
            min_y=entity.bbox.min_y + delta_y,
            max_x=entity.bbox.max_x + delta_x,
            max_y=entity.bbox.max_y + delta_y
        )

        dist = math.hypot(delta_x, delta_y)

        # Base cost proportional to displacement distance
        cost = dist * 1.0

        # Query obstacles at proposed candidate box
        obstacles = self.scene.grid.query_bbox(test_bbox, exclude_handle=entity.handle)
        for obs in obstacles:
            # Ignore leaders or non-obstacle annotations
            if not (obs.is_hard_obstacle or obs.is_movable or obs.dxftype in ("TEXT", "MTEXT", "INSERT")):
                continue

            overlap = test_bbox.overlap_area(obs.bbox)
            if overlap > 50.0:
                if obs.is_hard_obstacle:
                    cost += 50000.0 + (overlap * 10.0)
                else:
                    cost += 10000.0 + (overlap * 5.0)

        return cost

    def solve_entity(self, entity: SceneEntity) -> Optional[DisplacementPlan]:
        """Find the optimal non-colliding displacement for a single label."""
        orig_x, orig_y = entity.anchor_point

        # Evaluate current position first
        curr_cost = self.evaluate_candidate_delta(entity, 0.0, 0.0)
        if curr_cost <= 1.0:
            return None  # No collision, no move needed

        best_plan: Optional[DisplacementPlan] = None
        min_cost = float("inf")

        # Systematic radial search across 8 directions and expanding radii
        for dist in self.OFFSETS_MM:
            for dx_dir, dy_dir in self.DIRECTIONS:
                delta_x = round(dx_dir * dist, 1)
                delta_y = round(dy_dir * dist, 1)

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
                        distance=round(distance, 1),
                        needs_leader=(distance > 300.0),
                        cost=round(cost, 1)
                    )

            # If an obstacle-free position found (no hard or soft overlaps), stop expanding
            if min_cost < 2000.0:
                break

        return best_plan

    def solve_all(self, dry_run: bool = False, output_path: Optional[Path | str] = None) -> Dict[str, Any]:
        """Resolve all collisions in the drawing and optionally commit changes."""
        initial_collisions = self.detect_collisions()
        plans: List[DisplacementPlan] = []

        # Process colliding entities sequentially with active grid update
        colliding_handles = {c.entity_handle for c in initial_collisions}
        for entity in self.scene.movable_entities:
            if entity.handle in colliding_handles:
                plan = self.solve_entity(entity)
                if plan is not None and (plan.delta_x != 0.0 or plan.delta_y != 0.0):
                    plans.append(plan)
                    # Update entity bbox in memory & spatial index so next entities avoid this new location!
                    entity.bbox = BoundingBox(
                        min_x=entity.bbox.min_x + plan.delta_x,
                        min_y=entity.bbox.min_y + plan.delta_y,
                        max_x=entity.bbox.max_x + plan.delta_x,
                        max_y=entity.bbox.max_y + plan.delta_y
                    )
                    entity.anchor_point = (plan.target_pos[0], plan.target_pos[1])

        applied_count = 0
        leaders_created = 0

        if not dry_run and plans and self.doc is not None:
            msp = self.doc.modelspace()

            for p in plans:
                try:
                    ent = self.doc.entitydb.get(p.handle)
                    if ent is None:
                        continue

                    # Apply translation to entity
                    dxftype = ent.dxftype()
                    if dxftype in ("TEXT", "INSERT", "MTEXT"):
                        curr_insert = ent.dxf.get("insert", (0.0, 0.0, 0.0))
                        ent.dxf.insert = (curr_insert[0] + p.delta_x, curr_insert[1] + p.delta_y, curr_insert[2])
                        applied_count += 1

                    # Add Leader Line if displaced significantly (> 300mm)
                    if p.needs_leader:
                        msp.add_line(
                            start=(p.target_pos[0], p.target_pos[1], 0.0),
                            end=(p.original_pos[0], p.original_pos[1], 0.0),
                            dxfattribs={"layer": "DCE_Name", "color": 250}
                        )
                        leaders_created += 1

                except Exception as e:
                    print(f"Error applying displacement to {p.handle}: {e}", file=sys.stderr)

            # Save modified document
            target = Path(output_path) if output_path else Path(self.doc.filename)
            self.doc.saveas(target)

        return {
            "status": "OK" if not dry_run else "DRY_RUN_OK",
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
                    "distance_mm": p.distance,
                    "needs_leader": p.needs_leader,
                    "cost": p.cost
                }
                for p in plans
            ]
        }
