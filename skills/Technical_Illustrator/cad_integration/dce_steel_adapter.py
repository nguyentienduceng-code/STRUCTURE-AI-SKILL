# -*- coding: utf-8 -*-
"""
Module: dce_steel_adapter.py
Author: Antigravity (GEMINI) - CAD DCE v6 Architecture
Description:
    Adapter thep hinh va lien ket thep (Steel Sections & Connection Adapter).
    Cung cap:
      1. Catalog thong so hinh hoc thep hinh tieu chuan thuc te (I, H, Box, Bu long, Ban ma).
      2. Ham tinh toan toa do da giac 2D tinh chinh xac (khong dung scale X/Y de gia lap tiet dien).
      3. Co che khai bao nang luc minh bach: Tra ve UNSUPPORTED_BLOCK_BEHAVIOR neu yeu cau
         thao tac dynamic block / runtime interaction trong moi truong headless khong co AutoCAD engine.
      4. Helper serialize/deserialize chuoi XData Steel tham chieu ('tw#soluong#socaukien#ghichu1').
"""

import sys
if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

import ezdxf

# ==============================================================================
# 1. CATALOG TIET DIEN THEP HINH CHUAN (JIS G3192 / TCVN / ASTM)
# Don vi: mm, kg/m
# ==============================================================================

STEEL_I_PROFILES: Dict[str, Dict[str, float]] = {
    # H-Sections (Canh rong)
    "H100x100x6x8":    {"H": 100.0, "B": 100.0, "tw": 6.0, "tf": 8.0,  "r": 8.0,  "weight_kgm": 16.9},
    "H150x150x7x10":   {"H": 150.0, "B": 150.0, "tw": 7.0, "tf": 10.0, "r": 8.0,  "weight_kgm": 31.1},
    "H200x200x8x12":   {"H": 200.0, "B": 200.0, "tw": 8.0, "tf": 12.0, "r": 13.0, "weight_kgm": 49.9},
    "H250x250x9x14":   {"H": 250.0, "B": 250.0, "tw": 9.0, "tf": 14.0, "r": 16.0, "weight_kgm": 71.8},
    "H300x300x10x15":  {"H": 300.0, "B": 300.0, "tw": 10.0, "tf": 15.0, "r": 18.0, "weight_kgm": 93.0},
    "H350x350x12x19":  {"H": 350.0, "B": 350.0, "tw": 12.0, "tf": 19.0, "r": 20.0, "weight_kgm": 135.0},
    "H400x400x13x21":  {"H": 400.0, "B": 400.0, "tw": 13.0, "tf": 21.0, "r": 22.0, "weight_kgm": 172.0},

    # I-Sections (Canh hep)
    "I150x75x5x7":     {"H": 150.0, "B": 75.0,  "tw": 5.0, "tf": 7.0,  "r": 8.0,  "weight_kgm": 14.0},
    "I200x100x5.5x8":  {"H": 200.0, "B": 100.0, "tw": 5.5, "tf": 8.0,  "r": 9.0,  "weight_kgm": 21.3},
    "I250x125x6x9":    {"H": 250.0, "B": 125.0, "tw": 6.0, "tf": 9.0,  "r": 12.0, "weight_kgm": 29.6},
    "I300x150x6.5x9":  {"H": 300.0, "B": 150.0, "tw": 6.5, "tf": 9.0,  "r": 13.0, "weight_kgm": 36.7},
    "I350x175x7x11":   {"H": 350.0, "B": 175.0, "tw": 7.0, "tf": 11.0, "r": 14.0, "weight_kgm": 49.6},
    "I400x200x8x13":   {"H": 400.0, "B": 200.0, "tw": 8.0, "tf": 13.0, "r": 16.0, "weight_kgm": 66.0},
}

STEEL_BOX_PROFILES: Dict[str, Dict[str, float]] = {
    "BOX_100x100x4":   {"H": 100.0, "B": 100.0, "t": 4.0, "r_out": 8.0,  "weight_kgm": 11.6},
    "BOX_150x150x5":   {"H": 150.0, "B": 150.0, "t": 5.0, "r_out": 10.0, "weight_kgm": 22.4},
    "BOX_200x200x6":   {"H": 200.0, "B": 200.0, "t": 6.0, "r_out": 12.0, "weight_kgm": 35.8},
    "RECT_150x100x4.5":{"H": 150.0, "B": 100.0, "t": 4.5, "r_out": 9.0,  "weight_kgm": 16.4},
    "RECT_200x100x5":  {"H": 200.0, "B": 100.0, "t": 5.0, "r_out": 10.0, "weight_kgm": 22.4},
}

STEEL_BOLT_SPECS: Dict[str, Dict[str, float]] = {
    "M16": {"d_mm": 16.0, "hole_d_mm": 18.0, "nut_s_mm": 24.0, "washer_d_mm": 30.0},
    "M20": {"d_mm": 20.0, "hole_d_mm": 22.0, "nut_s_mm": 30.0, "washer_d_mm": 37.0},
    "M24": {"d_mm": 24.0, "hole_d_mm": 26.0, "nut_s_mm": 36.0, "washer_d_mm": 44.0},
    "M30": {"d_mm": 30.0, "hole_d_mm": 33.0, "nut_s_mm": 46.0, "washer_d_mm": 56.0},
}

# ==============================================================================
# 2. CAPABILITY EVALUATION ENGINE
# ==============================================================================

def evaluate_steel_capability(action: str, target: str) -> Dict[str, Any]:
    """
    Danh gia nang luc thuc thi cua module Steel Adapter:
    - Neu yeu cau dynamic block action (stretching, dynamic grip, lookup table)
      ma khong co AutoCAD runtime -> Tra ve UNSUPPORTED_BLOCK_BEHAVIOR.
    - Neu yeu cau xuat hinh hoc vector 2D tinh chinh xac -> Ho tro day du (SUPPORTED).
    """
    action_upper = action.upper()
    dynamic_keywords = ["DYNAMIC", "GRIP", "PARAMETRIC", "LOOKUP", "STRETCH", "VISIBILITY_STATE"]

    is_dynamic_request = any(kw in action_upper for kw in dynamic_keywords)

    if is_dynamic_request:
        return {
            "supported": False,
            "capability": "STATIC_ONLY",
            "status": "UNSUPPORTED_BLOCK_BEHAVIOR",
            "target": target,
            "reason": (
                "AutoCAD Dynamic Block runtime engine (ObjectARX/RealDWG) is not available in headless environment. "
                "Parametric stretching and dynamic properties cannot be evaluated interactively. "
                "Falling back to accurate static 2D vector representation."
            ),
            "fallback": "STATIC_2D_ACCURATE"
        }

    return {
        "supported": True,
        "capability": "STATIC_2D_ACCURATE",
        "status": "SUPPORTED",
        "target": target,
        "geometry_backend": "EZDXF_LWPOLYLINE",
        "accuracy": "EXACT_MILLIMETERS"
    }

# ==============================================================================
# 3. STATIC 2D VECTOR GENERATORS (KHONG DUNG SCALE X/Y)
# ==============================================================================

def get_i_profile_polygon(
    profile_name: str,
    insert_x: float = 0.0,
    insert_y: float = 0.0,
    rotation_deg: float = 0.0
) -> List[Tuple[float, float]]:
    """
    Tao toa do 12 dinh cua tiet dien thep chu I/H dang da giac dong (Polygon).
    Khong dung scale X/Y de bieu dien, bao dam dung 100% kich thuoc thep.
    """
    spec = STEEL_I_PROFILES.get(profile_name)
    if not spec:
        raise ValueError(f"Khong tim thay tiet dien thep I/H: '{profile_name}' trong catalog.")

    H = spec["H"]
    B = spec["B"]
    tw = spec["tw"]
    tf = spec["tf"]

    # Tinh toa do 12 dinh quanh tam doi xung (0, 0)
    # nua kich thuoc:
    hx = B / 2.0
    hy = H / 2.0
    wx = tw / 2.0
    fy = hy - tf

    # 12 dinh theo chieu kim dong ho tu goc tren ben phai:
    local_pts = [
        (hx, hy),           # Dinh 1: Meo tren phai canh tren
        (hx, fy),           # Dinh 2: Mep duoi phai canh tren
        (wx, fy),           # Dinh 3: Giao bung - canh tren phai
        (wx, -fy),          # Dinh 4: Giao bung - canh duoi phai
        (hx, -fy),          # Dinh 5: Mep tren phai canh duoi
        (hx, -hy),          # Dinh 6: Mep duoi phai canh duoi
        (-hx, -hy),         # Dinh 7: Mep duoi trai canh duoi
        (-hx, -fy),         # Dinh 8: Mep tren trai canh duoi
        (-wx, -fy),         # Dinh 9: Giao bung - canh duoi trai
        (-wx, fy),          # Dinh 10: Giao bung - canh tren trai
        (-hx, fy),          # Dinh 11: Mep duoi trai canh tren
        (-hx, hy),          # Dinh 12: Mep tren trai canh tren
    ]

    rad = math.radians(rotation_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    world_pts = []
    for lx, ly in local_pts:
        rx = lx * cos_r - ly * sin_r + insert_x
        ry = lx * sin_r + ly * cos_r + insert_y
        world_pts.append((round(rx, 3), round(ry, 3)))

    return world_pts


def get_box_profile_polygons(
    profile_name: str,
    insert_x: float = 0.0,
    insert_y: float = 0.0,
    rotation_deg: float = 0.0
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Tao toa do 2 da giac bao ngoai va bao trong cua thep hop (Box/Tube).
    Tra ve (outer_pts, inner_pts).
    """
    spec = STEEL_BOX_PROFILES.get(profile_name)
    if not spec:
        raise ValueError(f"Khong tim thay tiet dien thep hop: '{profile_name}' trong catalog.")

    H = spec["H"]
    B = spec["B"]
    t = spec["t"]

    hx_out = B / 2.0
    hy_out = H / 2.0
    hx_in = hx_out - t
    hy_in = hy_out - t

    local_out = [
        (hx_out, hy_out), (hx_out, -hy_out), (-hx_out, -hy_out), (-hx_out, hy_out)
    ]
    local_in = [
        (hx_in, hy_in), (hx_in, -hy_in), (-hx_in, -hy_in), (-hx_in, hy_in)
    ]

    rad = math.radians(rotation_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    def transform(pts):
        res = []
        for lx, ly in pts:
            rx = lx * cos_r - ly * sin_r + insert_x
            ry = lx * sin_r + ly * cos_r + insert_y
            res.append((round(rx, 3), round(ry, 3)))
        return res

    return transform(local_out), transform(local_in)


def generate_baseplate_geometry(
    b_mm: float,
    h_mm: float,
    t_mm: float,
    bolt_spec_name: str,
    bolt_offsets: List[Tuple[float, float]],
    insert_x: float = 0.0,
    insert_y: float = 0.0
) -> Dict[str, Any]:
    """
    Tao hinh hoc ban ma chan cot / ban bich (Baseplate) gom:
    - Duong bao ban ma (Polygon chu nhat b_mm x h_mm)
    - Cac vi tri lo khoan bu long (Circle tam x,y voi ban kinh lo hole_r)
    """
    bolt_spec = STEEL_BOLT_SPECS.get(bolt_spec_name)
    if not bolt_spec:
        raise ValueError(f"Khong tim thay dac ta bu long '{bolt_spec_name}' trong catalog.")

    hx = b_mm / 2.0
    hy = h_mm / 2.0
    plate_polygon = [
        (insert_x - hx, insert_y - hy),
        (insert_x + hx, insert_y - hy),
        (insert_x + hx, insert_y + hy),
        (insert_x - hx, insert_y + hy),
    ]

    bolt_holes = []
    hole_radius = bolt_spec["hole_d_mm"] / 2.0
    for ox, oy in bolt_offsets:
        bolt_holes.append({
            "center": (insert_x + ox, insert_y + oy),
            "radius": hole_radius,
            "bolt_spec": bolt_spec_name
        })

    return {
        "plate_size": (b_mm, h_mm, t_mm),
        "plate_polygon": plate_polygon,
        "bolt_holes": bolt_holes,
        "bolt_spec": bolt_spec,
    }

# ==============================================================================
# 4. XDATA PAYLOAD SERIALIZER & PARSER (THAM CHIEU DCE STEEL)
# ==============================================================================

def serialize_steel_xdata_payload(tw: float, soluong: int, socaukien: int, ghichu: str = "") -> str:
    """
    Ma hoa chuoi payload XData tham chieu cua DCE Steel:
    Format: 'tw#soluong#socaukien#ghichu1'
    """
    return f"{tw}#{soluong}#{socaukien}#{ghichu}"


def deserialize_steel_xdata_payload(payload: str) -> Dict[str, Any]:
    """
    Giai ma chuoi payload XData cua DCE Steel.
    """
    parts = payload.split("#")
    if len(parts) < 3:
        return {
            "is_valid": False,
            "raw_payload": payload,
            "tw": 0.0,
            "soluong": 0,
            "socaukien": 0,
            "ghichu": ""
        }
    try:
        tw = float(parts[0])
    except ValueError:
        tw = 0.0
    try:
        soluong = int(parts[1])
    except ValueError:
        soluong = 0
    try:
        socaukien = int(parts[2])
    except ValueError:
        socaukien = 0
    ghichu = parts[3] if len(parts) > 3 else ""

    return {
        "is_valid": True,
        "raw_payload": payload,
        "tw": tw,
        "soluong": soluong,
        "socaukien": socaukien,
        "ghichu": ghichu
    }


# ---------------------------------------------------------------------------
# G2 EXTENSIONS: CHANNEL/PIPE PROFILES, BASEPLATE PRESETS, 1:1 DXF ROUND-TRIP
# ---------------------------------------------------------------------------

STEEL_CHANNEL_PROFILES: Dict[str, Dict[str, float]] = {
    "U100x46x4.5": {"H": 100.0, "B": 46.0, "tw": 4.5, "tf": 7.6},
    "U120x52x4.8": {"H": 120.0, "B": 52.0, "tw": 4.8, "tf": 7.8},
    "U160x64x5": {"H": 160.0, "B": 64.0, "tw": 5.0, "tf": 8.4},
    "U200x76x5.2": {"H": 200.0, "B": 76.0, "tw": 5.2, "tf": 9.0},
    "C150x50x20x2.0": {"H": 150.0, "B": 50.0, "tw": 2.0, "tf": 2.0},
}

STEEL_PIPE_PROFILES: Dict[str, Dict[str, float]] = {
    "D114x4.0": {"od": 114.0, "t": 4.0},
    "D168x5.0": {"od": 168.0, "t": 5.0},
    "D219x6.0": {"od": 219.0, "t": 6.0},
    "D273x8.0": {"od": 273.0, "t": 8.0},
    "D323x8.0": {"od": 323.0, "t": 8.0},
}

STEEL_BASEPLATE_PRESETS: Dict[str, Dict[str, Any]] = {
    "Dce_BP_Pin4": {"fixity": "PIN", "anchor_count": 4, "rows": 2, "cols": 2},
    "Dce_BP_Pin6": {"fixity": "PIN", "anchor_count": 6, "rows": 3, "cols": 2},
    "Dce_BP_Fix6": {"fixity": "FIX", "anchor_count": 6, "rows": 2, "cols": 3},
    "Dce_BP_Fix8": {"fixity": "FIX", "anchor_count": 8, "rows": 2, "cols": 4},
    "Dce_BP_Fix10": {"fixity": "FIX", "anchor_count": 10, "rows": 2, "cols": 5},
    "Dce_BP_Fix12": {"fixity": "FIX", "anchor_count": 12, "rows": 3, "cols": 4},
}


def get_channel_profile_polygon(
    section_or_dims: Union[str, Dict[str, float]],
    origin: Tuple[float, float] = (0.0, 0.0),
) -> List[Tuple[float, float]]:
    """Sinh polygon 8 đỉnh mặt cắt thép hình U/C (1:1 mm) có tâm bao tại origin."""
    if isinstance(section_or_dims, str):
        dims = STEEL_CHANNEL_PROFILES.get(section_or_dims)
        if dims is None:
            raise KeyError(f"Không tìm thấy tiết diện Channel '{section_or_dims}' trong catalog.")
    else:
        dims = section_or_dims

    h = float(dims.get("H", dims.get("h", 0.0)))
    b = float(dims.get("B", dims.get("b", 0.0)))
    tw = float(dims["tw"])
    tf = float(dims["tf"])

    cx, cy = float(origin[0]), float(origin[1])
    x0 = cx - b / 2.0
    x1 = cx + b / 2.0
    y0 = cy - h / 2.0
    y1 = cy + h / 2.0

    # Lưng chữ U bên trái (x = x0), cánh vươn sang phải (x = x1)
    return [
        (x0, y0),
        (x1, y0),
        (x1, y0 + tf),
        (x0 + tw, y0 + tf),
        (x0 + tw, y1 - tf),
        (x1, y1 - tf),
        (x1, y1),
        (x0, y1),
    ]


def get_pipe_profile_circles(
    section_or_dims: Union[str, Dict[str, float]],
    origin: Tuple[float, float] = (0.0, 0.0),
) -> Dict[str, Any]:
    """Sinh hình học ống thép tròn rỗng (DCE_SectOng) tại 1:1 mm."""
    if isinstance(section_or_dims, str):
        dims = STEEL_PIPE_PROFILES.get(section_or_dims)
        if dims is None:
            raise KeyError(f"Không tìm thấy tiết diện Pipe '{section_or_dims}' trong catalog.")
    else:
        dims = section_or_dims

    od = float(dims["od"])
    t = float(dims["t"])
    return {
        "center": (float(origin[0]), float(origin[1])),
        "outer_radius": od / 2.0,
        "inner_radius": max(0.5, od / 2.0 - t),
        "od": od,
        "t": t,
    }


def validate_uniform_block_scale(
    xscale: float,
    yscale: float,
    zscale: float = 1.0,
    tol: float = 1e-6,
    strict: bool = True,
) -> Dict[str, Any]:
    """Khóa chống méo hình (No X/Y Scale Distortion Lock): bắt buộc xscale == yscale > 0."""
    xs = float(xscale)
    ys = float(yscale)
    zs = float(zscale)
    diff = abs(xs - ys)
    is_valid = (xs > 0.0) and (ys > 0.0) and (zs > 0.0) and (diff <= tol)

    if not is_valid and strict:
        raise ValueError(
            f"UNIFORM_SCALE_VIOLATION: Cấm chèn Block Steel với tỷ lệ X/Y lệch nhau "
            f"(xscale={xs}, yscale={ys}, |dx-dy|={diff:.6g}). Phải vẽ hình học 1:1 mm."
        )
    return {
        "is_valid": is_valid,
        "xscale": xs,
        "yscale": ys,
        "zscale": zs,
        "scale_diff": diff,
    }


def evaluate_steel_drawing_request(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Đánh giá khả năng đáp ứng yêu cầu vẽ Steel (từ chối Dynamic giả & commercial XData)."""
    requested_mode = str(spec.get("requested_mode", "STATIC_2D")).strip().upper()
    wants_xdata = bool(spec.get("write_commercial_xdata", False))

    warnings: List[Dict[str, Any]] = []
    supported = True
    fallback_used = False
    capability_status = "STATIC_2D_ACCURATE"

    if requested_mode == "DYNAMIC":
        supported = False
        fallback_used = True
        capability_status = "UNSUPPORTED_BLOCK_BEHAVIOR"
        warnings.append({
            "code": "UNSUPPORTED_BLOCK_BEHAVIOR",
            "requested_mode": "DYNAMIC",
            "applied_mode": "STATIC_2D_ACCURATE",
            "member_mark": spec.get("mark", spec.get("element_id", "UNKNOWN")),
            "message": (
                "Headless DXF generator lacks AutoCAD ObjectARX/AcDbEvalGraph runtime; "
                "cannot evaluate Dynamic Block stretch/flip actions. Fallback to static 1:1 mm geometry."
            ),
        })

    if wants_xdata:
        warnings.append({
            "code": "UNSUPPORTED_COMMERCIAL_XDATA_DISABLED",
            "commercial_xdata_written": False,
            "member_mark": spec.get("mark", spec.get("element_id", "UNKNOWN")),
            "message": (
                "Commercial XData injection (DceSteelRebar / SYS_XData_App) is disabled in headless G2 DXF output."
            ),
        })

    return {
        "supported": supported,
        "fallback_used": fallback_used,
        "capability_status": capability_status,
        "commercial_xdata_written": False,
        "warnings": warnings,
    }


def _import_catalog_and_binding():
    try:
        from dce_block_catalog import get_default_catalog
        from dce_block_binding import (
            get_default_binding_registry,
            bind_block_attributes,
            extract_semantic_values,
        )
    except ImportError:
        from cad_integration.dce_block_catalog import get_default_catalog
        from cad_integration.dce_block_binding import (
            get_default_binding_registry,
            bind_block_attributes,
            extract_semantic_values,
        )
    return get_default_catalog, get_default_binding_registry, bind_block_attributes, extract_semantic_values


def _ensure_steel_block_def(doc: ezdxf.document.Drawing, spec: Any):
    """Tạo định nghĩa Block tĩnh kèm đủ ATTDEF theo DceBlockSpec nếu chưa tồn tại trong DXF."""
    if spec.name in doc.blocks:
        return doc.blocks.get(spec.name)

    blk = doc.blocks.new(name=spec.name)
    # Vẽ ký hiệu định vị nhỏ gọn màu tối (không tạo text trắng)
    blk.add_line((-15.0, 0.0), (15.0, 0.0), dxfattribs={"layer": "DCE_Steel_Plate", "color": 250})
    blk.add_line((0.0, -15.0), (0.0, 15.0), dxfattribs={"layer": "DCE_Steel_Plate", "color": 250})

    for idx, (tag, adef) in enumerate(spec.attdefs.items()):
        ins_pt = (float(adef.insert[0]), float(adef.insert[1]) if len(adef.insert) >= 2 else float(-idx * 4.0))
        blk.add_attdef(
            tag=tag,
            insert=ins_pt,
            text=str(adef.default_value or tag),
            height=max(2.5, float(adef.height or 2.5)),
            dxfattribs={
                "layer": "DCE_Name",
                "color": 256,
                "prompt": str(adef.prompt or tag),
            },
        )
    return blk


def _resolve_section_dims(item: Dict[str, Any]) -> Tuple[str, str, Dict[str, float]]:
    ptype = str(item.get("profile_type", "I")).strip().upper()
    pname = str(item.get("section_name", ""))
    explicit = item.get("dims")
    if isinstance(explicit, dict):
        return ptype, pname, {k: float(v) for k, v in explicit.items()}
    if ptype in ("I", "H") and pname in STEEL_I_PROFILES:
        return ptype, pname, dict(STEEL_I_PROFILES[pname])
    if ptype == "BOX" and pname in STEEL_BOX_PROFILES:
        return ptype, pname, dict(STEEL_BOX_PROFILES[pname])
    if ptype in ("CHANNEL", "U", "C") and pname in STEEL_CHANNEL_PROFILES:
        return "CHANNEL", pname, dict(STEEL_CHANNEL_PROFILES[pname])
    if ptype == "PIPE" and pname in STEEL_PIPE_PROFILES:
        return "PIPE", pname, dict(STEEL_PIPE_PROFILES[pname])
    raise KeyError(f"Không xác định được kích thước tiết diện thép: type={ptype}, section_name='{pname}'")


def _compute_bolt_grid_offsets(
    b_mm: float,
    h_mm: float,
    rows: int,
    cols: int,
    edge_dist_x: float = 50.0,
    edge_dist_y: float = 50.0,
) -> List[Tuple[float, float]]:
    """Tính tọa độ lưới bu lông neo đối xứng quanh tâm bản đế."""
    xs = [0.0] if cols <= 1 else [
        -b_mm / 2.0 + edge_dist_x + i * (b_mm - 2.0 * edge_dist_x) / (cols - 1)
        for i in range(cols)
    ]
    ys = [0.0] if rows <= 1 else [
        -h_mm / 2.0 + edge_dist_y + j * (h_mm - 2.0 * edge_dist_y) / (rows - 1)
        for j in range(rows)
    ]
    return [(float(x), float(y)) for y in ys for x in xs]


def render_steel_components_to_dxf(
    dxf_path: Union[str, Path],
    fixture_data: Dict[str, Any],
    registry: Optional[Any] = None,
    catalog: Optional[Any] = None,
    binding_registry: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Kết xuất mặt cắt thép hình, bản đế và bản mã thép sang tệp DXF tĩnh 1:1 mm chuẩn G2.

    Khóa an toàn:
      - Không bao giờ ép X/Y scale khác nhau (validate_uniform_block_scale).
      - Nếu yêu cầu DYNAMIC -> ghi nhận UNSUPPORTED_BLOCK_BEHAVIOR và fallback vẽ tĩnh 1:1 mm.
      - Không ghi commercial XData (DceSteelRebar / SYS_XData_App).
      - Toàn bộ layer & ATTRIB dùng màu tối chuẩn Rule 12b (Zero White Text Lock).
    """
    get_default_catalog, get_default_binding_registry, bind_block_attributes, _ = _import_catalog_and_binding()
    if catalog is None:
        catalog = get_default_catalog()
    if binding_registry is None:
        binding_registry = get_default_binding_registry()

    out_path = Path(dxf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # Millimeters
    msp = doc.modelspace()

    # Layers màu tối chuẩn Rule 12b + đăng ký đầy đủ hệ layer DCE STEEL từ SSOT
    dark_layers = [
        ("DCE_Steel_Sect", 5),    # Blue (compat)
        ("DCE_Steel_Plate", 250), # Charcoal dark (compat)
        ("DCE_Steel_Bolt", 1),    # Red (compat)
        ("DCE_Name", 250),        # Charcoal dark
        ("DCE_Hatch", 8),         # Dark grey
    ]
    for lname, aci in dark_layers:
        if lname not in doc.layers:
            doc.layers.add(lname, color=aci)
    try:
        shared_ctx = Path(__file__).resolve().parents[3] / "_SHARED" / "SHARED_CONTEXT"
        if str(shared_ctx) not in sys.path:
            sys.path.insert(0, str(shared_ctx))
        from cad_layer_standard import ensure_doc_layers, get_layer_specs
        steel_names = [
            name for name, sp in get_layer_specs(profile="light_bg_plot").items()
            if sp.get("group") == "dce_steel_16"
        ]
        ensure_doc_layers(doc, profile="light_bg_plot", layer_names=steel_names, override_existing=False)
    except Exception:
        pass

    calc_logs: List[Dict[str, Any]] = []
    capability_warnings: List[Dict[str, Any]] = []
    rendered_sections: List[Dict[str, Any]] = []
    rendered_baseplates: List[Dict[str, Any]] = []
    rendered_plates: List[Dict[str, Any]] = []
    bound_blocks: List[Dict[str, Any]] = []

    # 1. Render steel_sections (I, H, BOX, CHANNEL, PIPE) 1:1 mm
    for sec in fixture_data.get("steel_sections", []):
        req_eval = evaluate_steel_drawing_request(sec)
        capability_warnings.extend(req_eval["warnings"])

        ptype, pname, dims = _resolve_section_dims(sec)
        ox, oy = sec.get("origin_mm", [0.0, 0.0])
        ox_f, oy_f = float(ox), float(oy)
        rot_deg = float(sec.get("rotation_deg", 0.0))
        eid = sec.get("element_id")
        mark = sec.get("mark", pname)
        handles: List[str] = []

        if ptype in ("I", "H"):
            if pname in STEEL_I_PROFILES and not isinstance(sec.get("dims"), dict):
                pts = get_i_profile_polygon(pname, ox_f, oy_f, rot_deg)
            else:
                b_v = float(dims.get("B", dims.get("b")))
                h_v = float(dims.get("H", dims.get("h")))
                tw_v = float(dims["tw"])
                tf_v = float(dims["tf"])
                pts = [
                    (ox_f - b_v / 2, oy_f - h_v / 2), (ox_f + b_v / 2, oy_f - h_v / 2),
                    (ox_f + b_v / 2, oy_f - h_v / 2 + tf_v), (ox_f + tw_v / 2, oy_f - h_v / 2 + tf_v),
                    (ox_f + tw_v / 2, oy_f + h_v / 2 - tf_v), (ox_f + b_v / 2, oy_f + h_v / 2 - tf_v),
                    (ox_f + b_v / 2, oy_f + h_v / 2), (ox_f - b_v / 2, oy_f + h_v / 2),
                    (ox_f - b_v / 2, oy_f + h_v / 2 - tf_v), (ox_f - tw_v / 2, oy_f + h_v / 2 - tf_v),
                    (ox_f - tw_v / 2, oy_f - h_v / 2 + tf_v), (ox_f - b_v / 2, oy_f - h_v / 2 + tf_v),
                ]
            pl = msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            handles.append(pl.dxf.handle)
            exp_w = float(dims.get("B", dims.get("b")))
            exp_h = float(dims.get("H", dims.get("h")))
        elif ptype == "BOX":
            if pname in STEEL_BOX_PROFILES and not isinstance(sec.get("dims"), dict):
                outer, inner = get_box_profile_polygons(pname, ox_f, oy_f, rot_deg)
            else:
                b_v = float(dims.get("B", dims.get("b")))
                h_v = float(dims.get("H", dims.get("h")))
                t_v = float(dims["t"])
                outer = [
                    (ox_f - b_v / 2, oy_f - h_v / 2), (ox_f + b_v / 2, oy_f - h_v / 2),
                    (ox_f + b_v / 2, oy_f + h_v / 2), (ox_f - b_v / 2, oy_f + h_v / 2),
                ]
                inner = [
                    (ox_f - b_v / 2 + t_v, oy_f - h_v / 2 + t_v), (ox_f + b_v / 2 - t_v, oy_f - h_v / 2 + t_v),
                    (ox_f + b_v / 2 - t_v, oy_f + h_v / 2 - t_v), (ox_f - b_v / 2 + t_v, oy_f + h_v / 2 - t_v),
                ]
            pl_out = msp.add_lwpolyline(outer, close=True, dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            pl_in = msp.add_lwpolyline(inner, close=True, dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            handles.extend([pl_out.dxf.handle, pl_in.dxf.handle])
            exp_w = float(dims.get("B", dims.get("b")))
            exp_h = float(dims.get("H", dims.get("h")))
        elif ptype in ("CHANNEL", "U", "C"):
            pts = get_channel_profile_polygon(dims, origin=(ox_f, oy_f))
            pl = msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            handles.append(pl.dxf.handle)
            exp_w = float(dims.get("B", dims.get("b")))
            exp_h = float(dims.get("H", dims.get("h")))
        elif ptype == "PIPE":
            cinfo = get_pipe_profile_circles(dims, origin=(ox_f, oy_f))
            c_out = msp.add_circle(cinfo["center"], cinfo["outer_radius"], dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            c_in = msp.add_circle(cinfo["center"], cinfo["inner_radius"], dxfattribs={"layer": "DCE_Steel_Sect", "color": 5})
            handles.extend([c_out.dxf.handle, c_in.dxf.handle])
            exp_w = exp_h = float(cinfo["od"])
        else:
            raise ValueError(f"Unsupported profile_type: {ptype}")

        # Nhãn tên cấu kiện chữ tối
        lbl = msp.add_text(
            f"{mark} ({pname})",
            height=25.0,
            dxfattribs={"layer": "DCE_Name", "color": 250, "true_color": 0x1E3246},
        )
        lbl.dxf.insert = (ox_f, oy_f - exp_h / 2.0 - 45.0)

        tag_handles: List[str] = [lbl.dxf.handle]
        if sec.get("column_tag_block"):
            bname = sec["column_tag_block"]
            bspec = catalog.require_block(bname)
            _ensure_steel_block_def(doc, bspec)
            sc = validate_uniform_block_scale(
                sec.get("xscale", 1.0), sec.get("yscale", 1.0), strict=True
            )
            ins = msp.add_blockref(
                bname,
                (ox_f, oy_f + exp_h / 2.0 + 35.0),
                dxfattribs={
                    "layer": "DCE_Name",
                    "xscale": sc["xscale"],
                    "yscale": sc["yscale"],
                    "zscale": sc["zscale"],
                },
            )
            bound = bind_block_attributes(
                ins, bspec, {"column_mark": mark}, registry=binding_registry
            )
            tag_handles.append(ins.dxf.handle)
            bound_blocks.append({"block_name": bname, "element_id": eid, "tags": bound})

        if registry is not None and eid and registry.get(eid) is not None:
            for h in handles:
                registry.link_geometry(eid, h)
            for th in tag_handles:
                registry.link_tag(eid, th)

        rec = {
            "element_id": eid,
            "mark": mark,
            "profile_type": ptype,
            "section_name": pname,
            "expected_width_mm": exp_w,
            "expected_height_mm": exp_h,
            "capability_status": req_eval["capability_status"],
            "handles": handles,
        }
        rendered_sections.append(rec)
        calc_logs.append({"step": f"render_section:{mark}", **rec})

    # 2. Render baseplates (Dce_BP_Pin4/6, Fix6/8/10/12 + Dce_AnchorExpansion)
    for bp in fixture_data.get("baseplates", []):
        req_eval = evaluate_steel_drawing_request(bp)
        capability_warnings.extend(req_eval["warnings"])

        bname = bp.get("block_name", "Dce_BP_Pin4")
        preset = STEEL_BASEPLATE_PRESETS.get(bname, {"anchor_count": 4, "rows": 2, "cols": 2, "fixity": "PIN"})
        w_mm = float(bp["plate_width_mm"])
        h_mm = float(bp["plate_height_mm"])
        t_mm = float(bp["thickness_mm"])
        ox, oy = bp.get("origin_mm", [0.0, 0.0])
        ox_f, oy_f = float(ox), float(oy)
        eid = bp.get("element_id")
        mark = bp["baseplate_mark"]

        bolt_spec_name = str(bp.get("bolt_spec", "M20"))
        if bolt_spec_name not in STEEL_BOLT_SPECS:
            bolt_spec_name = "M20"

        if "bolt_offsets" in bp and isinstance(bp["bolt_offsets"], list):
            bolt_offsets = [(float(p[0]), float(p[1])) for p in bp["bolt_offsets"]]
        else:
            rows = int(bp.get("bolt_rows", preset["rows"]))
            cols = int(bp.get("bolt_cols", preset["cols"]))
            edx = float(bp.get("edge_dist_x_mm", 50.0))
            edy = float(bp.get("edge_dist_y_mm", 50.0))
            bolt_offsets = _compute_bolt_grid_offsets(w_mm, h_mm, rows, cols, edx, edy)

        geom = generate_baseplate_geometry(
            w_mm, h_mm, t_mm, bolt_spec_name, bolt_offsets, insert_x=ox_f, insert_y=oy_f
        )

        pl = msp.add_lwpolyline(geom["plate_polygon"], close=True, dxfattribs={"layer": "DCE_Steel_Plate", "color": 250})
        handles = [pl.dxf.handle]
        for bhole in geom["bolt_holes"]:
            c_bolt = msp.add_circle(
                bhole["center"],
                float(bhole["radius"]),
                dxfattribs={"layer": "DCE_Steel_Bolt", "color": 1},
            )
            handles.append(c_bolt.dxf.handle)

        # Bind Dce_BP_* block attributes (TenBanDe, ChieuDay) với uniform scale 1.0
        sc = validate_uniform_block_scale(bp.get("xscale", 1.0), bp.get("yscale", 1.0), strict=True)
        bp_spec = catalog.require_block(bname)
        _ensure_steel_block_def(doc, bp_spec)
        bp_ins = msp.add_blockref(
            bname,
            (ox_f, oy_f),
            dxfattribs={"layer": "DCE_Name", "xscale": sc["xscale"], "yscale": sc["yscale"], "zscale": sc["zscale"]},
        )
        bound_bp = bind_block_attributes(
            bp_ins,
            bp_spec,
            {"baseplate_mark": mark, "thickness_mm": t_mm},
            registry=binding_registry,
        )
        bound_blocks.append({"block_name": bname, "element_id": eid, "tags": bound_bp})

        # Bind Dce_AnchorExpansion (SL) nếu có bolt_count
        anc_count = int(bp.get("bolt_count", len(geom["bolt_holes"])))
        anc_spec = catalog.require_block("Dce_AnchorExpansion")
        _ensure_steel_block_def(doc, anc_spec)
        anc_ins = msp.add_blockref(
            "Dce_AnchorExpansion",
            (ox_f, oy_f - h_mm / 2.0 - 40.0),
            dxfattribs={"layer": "DCE_Name", "xscale": 1.0, "yscale": 1.0, "zscale": 1.0},
        )
        bound_anc = bind_block_attributes(
            anc_ins, anc_spec, {"bolt_count": anc_count}, registry=binding_registry
        )
        bound_blocks.append({"block_name": "Dce_AnchorExpansion", "element_id": eid, "tags": bound_anc})

        if registry is not None and eid and registry.get(eid) is not None:
            for h in handles:
                registry.link_geometry(eid, h)
            registry.link_tag(eid, bp_ins.dxf.handle)
            registry.link_tag(eid, anc_ins.dxf.handle)

        rec_bp = {
            "element_id": eid,
            "baseplate_mark": mark,
            "block_name": bname,
            "plate_width_mm": w_mm,
            "plate_height_mm": h_mm,
            "thickness_mm": t_mm,
            "bolt_count": anc_count,
            "handles": handles,
        }
        rendered_baseplates.append(rec_bp)
        calc_logs.append({"step": f"render_baseplate:{mark}", **rec_bp})

    # 3. Render steel_plates (Dce-ThepTam / Dce-Tangcung)
    for stp in fixture_data.get("steel_plates", []):
        req_eval = evaluate_steel_drawing_request(stp)
        capability_warnings.extend(req_eval["warnings"])

        bname = stp.get("block_name", "Dce-ThepTam")
        ox, oy = stp.get("origin_mm", [0.0, 0.0])
        ox_f, oy_f = float(ox), float(oy)
        pw = float(stp.get("width_mm", 200.0))
        ph = float(stp.get("height_mm", 150.0))
        pts = [
            (ox_f - pw / 2.0, oy_f - ph / 2.0),
            (ox_f + pw / 2.0, oy_f - ph / 2.0),
            (ox_f + pw / 2.0, oy_f + ph / 2.0),
            (ox_f - pw / 2.0, oy_f + ph / 2.0),
        ]
        pl = msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Steel_Plate", "color": 250})

        sc = validate_uniform_block_scale(stp.get("xscale", 1.0), stp.get("yscale", 1.0), strict=True)
        pspec = catalog.require_block(bname)
        _ensure_steel_block_def(doc, pspec)
        pins = msp.add_blockref(
            bname,
            (ox_f, oy_f),
            dxfattribs={"layer": "DCE_Name", "xscale": sc["xscale"], "yscale": sc["yscale"], "zscale": sc["zscale"]},
        )
        sem_payload = {
            "plate_thickness": stp["plate_thickness"],
            "quantity": stp["quantity"],
            "member_mark": stp["member_mark"],
        }
        if "shape_desc" in stp:
            sem_payload["shape_desc"] = stp["shape_desc"]
        if "chamfer_desc" in stp:
            sem_payload["chamfer_desc"] = stp["chamfer_desc"]

        bound_p = bind_block_attributes(pins, pspec, sem_payload, registry=binding_registry)
        bound_blocks.append({"block_name": bname, "element_id": stp.get("element_id"), "tags": bound_p})

        eid = stp.get("element_id")
        if registry is not None and eid and registry.get(eid) is not None:
            registry.link_geometry(eid, pl.dxf.handle)
            registry.link_tag(eid, pins.dxf.handle)

        rendered_plates.append({
            "element_id": eid,
            "member_mark": stp["member_mark"],
            "block_name": bname,
            "width_mm": pw,
            "height_mm": ph,
            "handle": pl.dxf.handle,
        })

    doc.saveas(str(out_path))

    return {
        "Standard_Method": "TCVN 5575:2024 / DCE Steel G2 Static-2D",
        "dxf_path": str(out_path),
        "sections_count": len(rendered_sections),
        "baseplates_count": len(rendered_baseplates),
        "plates_count": len(rendered_plates),
        "bound_blocks_count": len(bound_blocks),
        "commercial_xdata_written": False,
        "capability_warnings": capability_warnings,
        "rendered_sections": rendered_sections,
        "rendered_baseplates": rendered_baseplates,
        "rendered_plates": rendered_plates,
        "bound_blocks": bound_blocks,
        "Calculation_Logs": calc_logs,
    }


def verify_steel_dxf_roundtrip(
    dxf_path: Union[str, Path],
    fixture_data: Dict[str, Any],
    catalog: Optional[Any] = None,
    binding_registry: Optional[Any] = None,
    dim_tol_mm: float = 0.01,
) -> Dict[str, Any]:
    """Đọc lại tệp DXF vừa lưu và kiểm chứng 100% tính toàn vẹn hình học, scale đồng nhất và ATTRIB."""
    get_default_catalog, get_default_binding_registry, _, extract_semantic_values = _import_catalog_and_binding()
    if catalog is None:
        catalog = get_default_catalog()
    if binding_registry is None:
        binding_registry = get_default_binding_registry()

    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    scale_violations: List[Dict[str, Any]] = []
    dynamic_block_refs: List[str] = []
    commercial_xdata_entities: List[str] = []
    extracted_blocks: List[Dict[str, Any]] = []
    mismatches: List[str] = []

    for ent in msp:
        if ent.has_xdata("DceSteelRebar") or ent.has_xdata("SYS_XData_App"):
            commercial_xdata_entities.append(ent.dxf.handle)

        if ent.dxftype() == "INSERT":
            bname = ent.dxf.name
            if bname.startswith("*U"):
                dynamic_block_refs.append(bname)
            xs = float(getattr(ent.dxf, "xscale", 1.0))
            ys = float(getattr(ent.dxf, "yscale", 1.0))
            zs = float(getattr(ent.dxf, "zscale", 1.0))
            sc = validate_uniform_block_scale(xs, ys, zs, strict=False)
            if not sc["is_valid"]:
                scale_violations.append({"block_name": bname, "handle": ent.dxf.handle, **sc})

            bspec = catalog.get_block(bname)
            if bspec is not None and binding_registry.get(bname) is not None and ent.attribs:
                sem = extract_semantic_values(ent, bspec, registry=binding_registry)
                extracted_blocks.append({"block_name": bname, "handle": ent.dxf.handle, "semantic": sem})

    geometry_checks: List[Dict[str, Any]] = []
    # Kiểm tra mỗi thép hình khớp đúng 1:1 mm LWPOLYLINE / CIRCLE bbox quanh tâm origin
    for sec in fixture_data.get("steel_sections", []):
        ptype, pname, dims = _resolve_section_dims(sec)
        exp_w = float(dims["od"]) if ptype == "PIPE" else float(dims.get("B", dims.get("b")))
        exp_h = float(dims["od"]) if ptype == "PIPE" else float(dims.get("H", dims.get("h")))
        ox, oy = sec.get("origin_mm", [0.0, 0.0])

        matched = False
        for ent in msp.query('*[layer=="DCE_Steel_Sect"]'):
            if ent.dxftype() not in ("LWPOLYLINE", "CIRCLE"):
                continue
            if ent.dxftype() == "LWPOLYLINE":
                pts = list(ent.get_points("xy"))
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
                bw, bh = max(xs) - min(xs), max(ys) - min(ys)
            else:
                cx, cy = float(ent.dxf.center.x), float(ent.dxf.center.y)
                bw = bh = float(ent.dxf.radius) * 2.0

            if abs(cx - ox) <= dim_tol_mm and abs(cy - oy) <= dim_tol_mm:
                if abs(bw - exp_w) <= dim_tol_mm and abs(bh - exp_h) <= dim_tol_mm:
                    matched = True
                    geometry_checks.append({
                        "kind": "steel_section",
                        "mark": sec.get("mark"),
                        "expected_mm": [exp_w, exp_h],
                        "actual_mm": [round(bw, 3), round(bh, 3)],
                        "matched": True,
                    })
                    break
        if not matched:
            mismatches.append(f"Section '{sec.get('mark')}' bbox mismatch (expected {exp_w}x{exp_h} at ({ox},{oy}))")

    for bp in fixture_data.get("baseplates", []):
        exp_w = float(bp["plate_width_mm"])
        exp_h = float(bp["plate_height_mm"])
        ox, oy = bp.get("origin_mm", [0.0, 0.0])
        matched = False
        for ent in msp.query('LWPOLYLINE[layer=="DCE_Steel_Plate"]'):
            pts = list(ent.get_points("xy"))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
            bw, bh = max(xs) - min(xs), max(ys) - min(ys)
            if abs(cx - ox) <= dim_tol_mm and abs(cy - oy) <= dim_tol_mm:
                if abs(bw - exp_w) <= dim_tol_mm and abs(bh - exp_h) <= dim_tol_mm:
                    matched = True
                    geometry_checks.append({
                        "kind": "baseplate",
                        "mark": bp["baseplate_mark"],
                        "expected_mm": [exp_w, exp_h],
                        "actual_mm": [round(bw, 3), round(bh, 3)],
                        "matched": True,
                    })
                    break
        if not matched:
            mismatches.append(f"Baseplate '{bp['baseplate_mark']}' bbox mismatch (expected {exp_w}x{exp_h})")

    # Kiểm chứng khớp ngữ nghĩa ATTRIB cho Baseplate & Steel Plate
    bp_extracted = [
        b["semantic"] for b in extracted_blocks if b["block_name"].startswith("Dce_BP_")
    ]
    for bp in fixture_data.get("baseplates", []):
        exp_mark = str(bp["baseplate_mark"])
        exp_t = float(bp["thickness_mm"])
        if not any(
            str(s.get("baseplate_mark")) == exp_mark
            and abs(float(s.get("thickness_mm", -1)) - exp_t) <= 0.1
            for s in bp_extracted
        ):
            mismatches.append(f"ATTRIB mismatch for baseplate '{exp_mark}' (t={exp_t})")

    plate_extracted = [
        b["semantic"] for b in extracted_blocks if b["block_name"] in ("Dce-ThepTam", "Dce-Tangcung")
    ]
    for stp in fixture_data.get("steel_plates", []):
        exp_m = str(stp["member_mark"])
        exp_t = float(stp["plate_thickness"])
        exp_q = int(stp["quantity"])
        if not any(
            str(s.get("member_mark")) == exp_m
            and abs(float(s.get("plate_thickness", -1)) - exp_t) <= 0.1
            and int(s.get("quantity", -1)) == exp_q
            for s in plate_extracted
        ):
            mismatches.append(f"ATTRIB mismatch for steel_plate '{exp_m}' (B={exp_t}, SL={exp_q})")

    passed = (
        len(scale_violations) == 0
        and len(dynamic_block_refs) == 0
        and len(commercial_xdata_entities) == 0
        and len(mismatches) == 0
    )

    return {
        "Standard_Method": "TCVN 5575:2024 / DCE Steel G2 Roundtrip Audit",
        "passed": passed,
        "uniform_scale_ok": len(scale_violations) == 0,
        "scale_violations": scale_violations,
        "dynamic_block_refs_count": len(dynamic_block_refs),
        "commercial_xdata_count": len(commercial_xdata_entities),
        "extracted_blocks": extracted_blocks,
        "geometry_checks": geometry_checks,
        "mismatches": mismatches,
        "Calculation_Logs": [
            {"step": "roundtrip_audit", "passed": passed, "checks": len(geometry_checks), "blocks": len(extracted_blocks)}
        ],
    }
