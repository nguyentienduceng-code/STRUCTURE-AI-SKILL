# -*- coding: utf-8 -*-
"""
cad_defect_cropper.py — P4.2 CAD Defect BBox Visual Injection (Step 2: evidence crop)
===================================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.2, §3.2.2.

Crops the *exact* bounding box of a CAD defect and returns a high-resolution
(300 DPI) PNG suitable for embedding into the RFI/NCR Word document, using the
existing thin adapter `.agents/tools/dce_render_preview.py`
(`render_dxf_to_png(view_box=..., dpi=300)`). No AutoCAD / ODA required.

Region resolution order (never guesses):
  1. explicit `view_box` (mm) passed by the caller;
  2. element / zone bounding box supplied in `regions_mm`;
  3. the Form frame (`frame_mm`) — a full-sheet defect snapshot;
  4. modelspace extents of the DXF (last-resort, whole drawing).

The crop lands on a *stable* path (caller-provided `out_png`) and the temporary
preview is always released (Virtual Drive Guard), per AGENTS §10 (confirm the
file exists before reporting OK).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CAD_DIR = Path(__file__).resolve().parent
_AGENTS_DIR = _CAD_DIR.parents[2]
_TOOLS_DIR = _AGENTS_DIR / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import ezdxf  # noqa: E402

# dce_render_preview pulls in dce_virtual_drive_guard.configure_runtime() on import.
from dce_render_preview import (  # noqa: E402
    render_dxf_to_png,
    cleanup_preview,
)


def _mspace_extents(doc) -> Optional[Tuple[float, float, float, float]]:
    """Bounding box of modelspace geometry in world-mm (None when empty)."""
    minx = miny = None
    maxx = maxy = None
    msp = doc.modelspace()
    for ent in msp:
        try:
            import ezdxf.math
            bb = ezdxf.bbox.bbox([ent])
            if bb.has_data:
                a = bb.extmin
                b = bb.extmax
                minx = a.x if minx is None else min(minx, a.x)
                miny = a.y if miny is None else min(miny, a.y)
                maxx = b.x if maxx is None else max(maxx, b.x)
                maxy = b.y if maxy is None else max(maxy, b.y)
        except Exception:
            continue
    if minx is None:
        return None
    # Small guard against degenerate/zero-area boxes.
    if maxx - minx < 1.0 or maxy - miny < 1.0:
        return None
    return (minx, miny, maxx, maxy)


def _pad(box: Tuple[float, float, float, float], pct: float = 0.08) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    w = (x1 - x0) * pct
    h = (y1 - y0) * pct
    return (x0 - w, y0 - h, x1 + w, y1 + h)


def resolve_view_box(
    dxf_path: str,
    view_box: Optional[Tuple[float, float, float, float]] = None,
    regions_mm: Optional[List[Tuple[float, float, float, float]]] = None,
    frame_mm: Optional[Tuple[float, float, float, float]] = None,
) -> Optional[Tuple[float, float, float, float]]:
    """Pick the crop region by the resolution order documented above (no guessing)."""
    if view_box:
        return tuple(float(v) for v in view_box)
    if regions_mm:
        # Union of all provided element/zone bboxes (mm).
        allx = [r[0] for r in regions_mm] + [r[2] for r in regions_mm]
        ally = [r[1] for r in regions_mm] + [r[3] for r in regions_mm]
        if min(allx) < max(allx) and min(ally) < max(ally):
            return _pad((min(allx), min(ally), max(allx), max(ally)))
    doc = ezdxf.readfile(str(dxf_path))
    ext = _mspace_extents(doc)
    if ext is not None:
        if frame_mm:
            # Crop the modelspace region that lies inside the form frame; guard
            # against a non-intersecting frame (inverted box -> w/h <= 0).
            fx0, fy0, fx1, fy1 = (float(v) for v in frame_mm)
            ix0, iy0 = max(ext[0], fx0), max(ext[1], fy0)
            ix1, iy1 = min(ext[2], fx1), min(ext[3], fy1)
            if ix1 > ix0 and iy1 > iy0:
                return _pad((ix0, iy0, ix1, iy1))
        return ext
    if frame_mm:
        fx0, fy0, fx1, fy1 = (float(v) for v in frame_mm)
        if fx1 > fx0 and fy1 > fy0:
            return _pad((fx0, fy0, fx1, fy1))
    return None


def crop_defect_region(
    dxf_path: str,
    out_png: str,
    view_box: Optional[Tuple[float, float, float, float]] = None,
    regions_mm: Optional[List[Tuple[float, float, float, float]]] = None,
    frame_mm: Optional[Tuple[float, float, float, float]] = None,
    dpi: int = 300,
    layout_name: str = "Model",
) -> Dict[str, Any]:
    """Render the defect bbox to a stable PNG (default 300 DPI) and release the preview.

    Returns a JSON-serialisable dict:
        {status, ok, png_path, view_box, dpi, bytes, verified_file_exists, error}
    `status` reuses the render-preview codes (OK / E001 / E003) plus `E004_REGION`
    when no crop region can be derived (never guesses — AGENTS §4).
    """
    box = resolve_view_box(dxf_path, view_box=view_box, regions_mm=regions_mm, frame_mm=frame_mm)
    if box is None:
        return {"status": "E004_REGION", "ok": False, "png_path": None, "view_box": None,
                "dpi": dpi, "bytes": 0, "verified_file_exists": False,
                "error": "Không xác định được vùng crop (view_box/region/frame/modelspace đều rỗng)."}

    res = render_dxf_to_png(
        str(dxf_path), out_png=str(out_png), dpi=dpi,
        layout_name=layout_name, view_box=tuple(box),
    )
    preview_id = res.get("preview_id")
    ok = res.get("status") == "OK" and res.get("verified_file_exists", False)
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)

    final_path: Optional[str] = None
    n_bytes = 0
    try:
        if ok and res.get("output_png") and Path(res["output_png"]).is_file():
            shutil.copyfile(res["output_png"], str(out))
            final_path = str(out)
            n_bytes = out.stat().st_size
    finally:
        # ALWAYS release the Virtual Drive Guard preview, even if the copy/stat
        # above raised (disk full / permissions) — a leak here accumulates
        # in the previews scratch dir (dce_virtual_drive_guard only reaps
        # completed previews on TTL).
        if preview_id:
            cleanup_preview(preview_id)

    return {
        "status": "OK" if ok else res.get("status", "E003"),
        "ok": ok,
        "png_path": final_path,
        "view_box": list(box),
        "dpi": dpi,
        "bytes": n_bytes,
        "verified_file_exists": bool(ok and out.is_file() and n_bytes > 0),
        "modelspace_entities": res.get("modelspace_entities", 0),
        "layers": res.get("layers", 0),
        "render_seconds": res.get("render_seconds", 0.0),
        "error": None if ok else res.get("error"),
    }


if __name__ == "__main__":
    import json as _json
    args = sys.argv[1:]
    if len(args) < 2:
        print("usage: cad_defect_cropper.py <dxf> <out.png> [view_box=x0,y0,x1,y1]")
        sys.exit(2)
    vb = None
    for a in args[2:]:
        if a.startswith("view_box="):
            vb = tuple(float(v) for v in a[len("view_box="):].split(","))
    r = crop_defect_region(args[0], args[1], view_box=vb, dpi=300)
    print(_json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r["ok"] else 1)
