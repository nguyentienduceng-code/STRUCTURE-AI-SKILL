#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cad_tag_placement.py — Planner Đặt Nhãn Cấu Kiện Theo Hình Học (Directive v6.0, C1)
=====================================================================================
Người sở hữu: CLAUDE (phạm vi renderer/tag placement — CAD_UPGRADE_V6_TASK_PLAN.md).

Giải quyết mục P1 của DCE_BLOCK_TAG_GUIDE.md §5:
  - Tag dầm đặt tại khoảng trống giữa nhịp, hướng chữ theo phương dầm,
    thử hai phía dầm bằng bbox chữ THẬT (ước lượng width theo aspect),
    KHÔNG dùng offset 600/500 mm cố định cho mọi tỷ lệ.
  - Tag sàn nằm TRONG đa giác ô và NGOÀI các lỗ mở.
  - Hết chỗ trong vùng => leader (đường chỉ dẫn) neo vào đúng cấu kiện.
  - Offset chỉnh tay của kỹ sư lưu theo (element_id, view_id), tái sinh
    kiểm va chạm lại và giữ chỉnh tay còn hợp lệ.

Tọa độ: world mm (modelspace). Obstacle = rectangle (xmin, ymin, xmax, ymax).
Module này THUẦN HÌNH HỌC + DỮ LIỆU — không phụ thuộc ezdxf, chạy được
độc lập trong unit test (bit-exact, không cần đọc DXF).
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Kiểu obstacle: hộp bao (xmin, ymin, xmax, ymax) mm
Rect = Tuple[float, float, float, float]


@dataclass
class TagPlacement:
    """Kết quả đặt một nhãn: vị trí, hướng, leader (nếu có) và chiến lược."""
    x: float
    y: float
    rotation_deg: float = 0.0
    leader_to: Optional[Tuple[float, float]] = None  # điểm neo lên cấu kiện (None = không leader)
    strategy: str = "direct"  # direct | leader
    element_id: str = ""
    view_id: str = "model"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["leader_to"] = list(self.leader_to) if self.leader_to else None
        return d


class TagPlacementPlanner:
    """Planner đặt nhãn dầm/sàn theo bbox chữ + va chạm obstacle."""

    def __init__(
        self,
        text_height_mm: float = 200.0,
        char_aspect: float = 0.72,      # ước lượng chiều rộng chữ / chiều cao (sans-serif CAD)
        gap_mm: float = 150.0,          # khoảng hở tối thiểu giữa chữ và mép cấu kiện
        leader_length_mm: float = 1800.0,
        overrides: Optional[Dict[Tuple[str, str], Tuple[float, float]]] = None,
    ):
        self.text_height_mm = float(text_height_mm)
        self.char_aspect = float(char_aspect)
        self.gap_mm = float(gap_mm)
        self.leader_length_mm = float(leader_length_mm)
        # chỉnh tay kỹ sư: {(element_id, view_id): (dx_mm, dy_mm)}
        self.overrides: Dict[Tuple[str, str], Tuple[float, float]] = dict(overrides or {})

    # ------------------------------------------------------------------
    # Ước lượng bbox chữ
    # ------------------------------------------------------------------
    def estimate_bbox(self, text: str, height_mm: Optional[float] = None) -> Tuple[float, float]:
        """(width, height) ước lượng của một dòng chữ — dùng thử va chạm."""
        h = float(height_mm or self.text_height_mm)
        w = max(len(text), 1) * self.char_aspect * h
        return w, h

    @staticmethod
    def _bbox_at(text: str, x: float, y: float, h: float, rot: float, aspect: float) -> Rect:
        """Hộp bao chữ đặt tại (x,y) làm TÂM, xoay rot (độ)."""
        w, hh = len(text) * aspect * h, h
        if abs(math.sin(math.radians(rot))) < 1e-9:
            # chữ ngang/dọc nguyên — bbox chính xác không cần xuyến chuyển
            if abs(math.cos(math.radians(rot))) >= 1:
                return (x - w / 2, y - hh / 2, x + w / 2, y + hh / 2)
            return (x - hh / 2, y - w / 2, x + hh / 2, y + w / 2)
        # chữ xiên: bbox của hình chữ nhật xoay
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        hw, hh2 = w / 2, hh / 2
        ext_x = abs(hw * c) + abs(hh2 * s)
        ext_y = abs(hw * s) + abs(hh2 * c)
        return (x - ext_x, y - ext_y, x + ext_x, y + ext_y)

    @staticmethod
    def _overlap(a: Rect, b: Rect, margin: float = 0.0) -> bool:
        return not (a[2] + margin <= b[0] or b[2] + margin <= a[0]
                    or a[3] + margin <= b[1] or b[3] + margin <= a[1])

    # ------------------------------------------------------------------
    # Chỉnh tay (kỹ sư)
    # ------------------------------------------------------------------
    def apply_override(self, element_id: str, view_id: str, base: TagPlacement,
                       dx: float, dy: float) -> TagPlacement:
        p = TagPlacement(x=base.x + dx, y=base.y + dy, rotation_deg=base.rotation_deg,
                         element_id=element_id, view_id=view_id, strategy="manual")
        if base.leader_to:
            p.leader_to = base.leader_to
        else:
            p.leader_to = (base.x, base.y)
        return p

    # ------------------------------------------------------------------
    # TAG DẦM
    # ------------------------------------------------------------------
    def plan_beam_tag(
        self,
        label: str,
        x0: float, y0: float, x1: float, y1: float,
        obstacles: List[Rect] = None,
        element_id: str = "",
        view_id: str = "model",
    ) -> TagPlacement:
        """Đặt nhãn dầm tại khoảng trống giữa 2 đầu (giữa nhịp), song song dầm.

        Thử các slot: giữa nhịp, lệch vuông góc lên/trước xuống/sau theo
        (gap + half_height). Nếu mọi slot va obstacle => leader ra ngoài.
        """
        obstacles = list(obstacles or [])
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        # hướng chữ đọc được: giữ trong (-90, 90]
        rot = ang
        if rot > 90:
            rot -= 180
        elif rot <= -90:
            rot += 180

        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        # vector vuông góc (nâng lên "phía trên" dầm khi nhìn theo chiều dầm)
        px, py = -s, c
        off = self.gap_mm + self.text_height_mm * 0.6

        slots = [
            (cx + px * off, cy + py * off),
            (cx - px * off, cy - py * off),
            (cx, cy - off - self.text_height_mm),
            (cx, cy + off + self.text_height_mm),
        ]
        for (sx, sy) in slots:
            bbox = self._bbox_at(label, sx, sy, self.text_height_mm, rot, self.char_aspect)
            if not any(self._overlap(bbox, ob, self.gap_mm * 0.5) for ob in obstacles):
                p = TagPlacement(x=sx, y=sy, rotation_deg=rot, strategy="direct",
                                 element_id=element_id, view_id=view_id)
                if (element_id, view_id) in self.overrides:
                    p = self.apply_override(element_id, view_id, p, *self.overrides[(element_id, view_id)])
                return p

        # Hết chỗ => leader: đưa nhãn ra ngoài, xa dần theo hướng vuông góc
        for mult in (1.0, 2.0, 3.0):
            L = self.leader_length_mm * mult
            lx, ly = cx + px * L, cy + py * L
            bbox = self._bbox_at(label, lx, ly, self.text_height_mm, rot, self.char_aspect)
            if not any(self._overlap(bbox, ob, 0.0) for ob in obstacles):
                p = TagPlacement(x=lx, y=ly, rotation_deg=rot, leader_to=(cx, cy),
                                 strategy="leader", element_id=element_id, view_id=view_id)
                if (element_id, view_id) in self.overrides:
                    p = self.apply_override(element_id, view_id, p, *self.overrides[(element_id, view_id)])
                return p
        # fallback cuối cùng (không thể va): vẫn trả direct tại tâm + ghi strategy
        return TagPlacement(x=cx, y=cy, rotation_deg=rot, strategy="fallback_center",
                            element_id=element_id, view_id=view_id)

    # ------------------------------------------------------------------
    # TAG SÀN (panel)
    # ------------------------------------------------------------------
    def plan_slab_tag(
        self,
        label: str,
        panel: Rect,
        openings: List[Rect] = None,
        obstacles: List[Rect] = None,
        element_id: str = "",
        view_id: str = "model",
    ) -> TagPlacement:
        """Đặt nhãn ô sàn: TRỌNG TÂM trong panel, ngoài mọi lỗ; thử 4 góc
        thu nhỏ nếu tâm va lỗ. Hết chỗ => leader neo vào trọng tâm panel."""
        openings = list(openings or [])
        obstacles = list(obstacles or [])
        px0, py0, px1, py1 = panel
        cx, cy = (px0 + px1) / 2.0, (py0 + py1) / 2.0
        bbox0 = self._bbox_at(label, cx, cy, self.text_height_mm, 0.0, self.char_aspect)

        def free(b: Rect) -> bool:
            for ob in openings + obstacles:
                if self._overlap(b, ob, 0.0):
                    return False
            # phải nằm trong panel (AC2 C1: tag trong đa giác ô)
            if b[0] < px0 or b[2] > px1 or b[1] < py0 or b[3] > py1:
                return False
            return True

        if free(bbox0):
            p = TagPlacement(x=cx, y=cy, strategy="direct",
                             element_id=element_id, view_id=view_id)
            if (element_id, view_id) in self.overrides:
                p = self.apply_override(element_id, view_id, p, *self.overrides[(element_id, view_id)])
            return p

        # thử 4 góc thu vào trong (tránh lỗ ở tâm)
        # Inset by half the actual text bbox as well as the requested gap.
        tw, th = self.estimate_bbox(label)
        mx, my = self.gap_mm + tw / 2.0, self.gap_mm + th / 2.0
        corners = [
            (px0 + mx, py0 + my), (px1 - mx, py0 + my),
            (px0 + mx, py1 - my), (px1 - mx, py1 - my),
        ]
        for (tx, ty) in corners:
            b = self._bbox_at(label, tx, ty, self.text_height_mm, 0.0, self.char_aspect)
            if free(b):
                p = TagPlacement(x=tx, y=ty, strategy="corner",
                                 element_id=element_id, view_id=view_id)
                if (element_id, view_id) in self.overrides:
                    p = self.apply_override(element_id, view_id, p, *self.overrides[(element_id, view_id)])
                return p

        # leader: nhãn đặt dưới panel, neo lên tâm
        ly = py1 + self.leader_length_mm * 0.6
        return TagPlacement(x=cx, y=ly, leader_to=(cx, cy), strategy="leader",
                            element_id=element_id, view_id=view_id)

    # ------------------------------------------------------------------
    # Lưu/đọc override chỉnh tay (JSON sidecar, stable per element_id/view_id)
    # ------------------------------------------------------------------
    @staticmethod
    def save_overrides(overrides: Dict[Tuple[str, str], Tuple[float, float]], path) -> None:
        payload = {"v": 1,
                   "overrides": {f"{k[0]}@{k[1]}": [dx, dy] for k, (dx, dy) in overrides.items()}}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_overrides(cls, path) -> Dict[Tuple[str, str], Tuple[float, float]]:
        import os
        if not path or not os.path.isfile(str(path)):
            return {}
        data = json.loads(open(str(path), encoding="utf-8").read())
        out: Dict[Tuple[str, str], Tuple[float, float]] = {}
        for key, v in data.get("overrides", {}).items():
            eid, _, view = key.partition("@")
            out[(eid, view or "model")] = (float(v[0]), float(v[1]))
        return out


# ----------------------------------------------------------------------
# Helper: obstacle từ model (beams/columns/openings) — world mm
# ----------------------------------------------------------------------
def beam_obstacle(x0: float, y0: float, x1: float, y1: float,
                  b_mm: float, margin_mm: float = 0.0) -> List[Rect]:
    """Hộp bao của một dầm (2 phía) từ model, cho planner va chạm."""
    c, s = 1.0, 0.0
    if abs(x0 - x1) >= abs(y0 - y1):
        half = b_mm / 2.0 + margin_mm
        return [(min(x0, x1), min(y0, y1) - half, max(x0, x1), max(y0, y1) + half)]
    half = b_mm / 2.0 + margin_mm
    return [(min(x0, x1) - half, min(y0, y1), max(x0, x1) + half, max(y0, y1))]


def building_obstacles(model: Dict[str, Any], scale_mm: float = 1000.0) -> List[Rect]:
    """Thao tác nhanh: danh sách obstacle từ model (cột + lỗ + dầm) world-mm."""
    obs: List[Rect] = []
    for col in model.get("columns", []):
        cx = col.get("x", 0) * scale_mm
        cy = col.get("y", 0) * scale_mm
        bw = col.get("bx", 0.3) * scale_mm
        bh = col.get("by", 0.3) * scale_mm
        obs.append((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))
    for v in model.get("voids", []):
        vx = v["x"] * scale_mm
        vy = v["y"] * scale_mm
        vw = v["w"] * scale_mm
        vh = v["h"] * scale_mm
        obs.append((vx - vw / 2, vy - vh / 2, vx + vw / 2, vy + vh / 2))
    return obs


if __name__ == "__main__":
    # Self-test nhanh
    p = TagPlacementPlanner()
    pl = p.plan_beam_tag("D1A (400x800)", x0=0.0, y0=0.0, x1=10000.0, y1=0.0,
                         obstacles=[(100.0, -500.0, 200.0, 500.0)])
    print(json.dumps(pl.to_dict(), ensure_ascii=False))
