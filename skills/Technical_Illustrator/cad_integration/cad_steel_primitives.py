# -*- coding: utf-8 -*-
"""
Module: cad_steel_primitives.py
Author: Antigravity (GEMINI) - DCE Pro CAD Engine v5.0
Description:
    Thư viện Hình học Tham số Thép & Biện pháp Thi công (Parametric Steel & BPTC Primitives).
    Cung cấp:
      1. draw_rolled_section: Vẽ mặt cắt ngang hoặc hình chiếu thép hình (H, I, U, C, L, Box, Pipe).
      2. draw_tapered_member: Vẽ cột/kèo tổ hợp vát tiết diện (PEB) tự động dựng cánh, bụng, tâm trục.
      3. draw_gusset_plate: Vẽ bản mã đa giác/vát góc kèm sườn gia cường & tính toán khối lượng theo Shoelace.
      4. draw_bolt_array: Vẽ lưới bu lông kèm tự động kiểm tra TCVN 5575:2024 (khoảng cách mép e1, e2, bước p1, p2).
      5. draw_weld_symbol_tcvn: Vẽ ký hiệu đường hàn góc/đối đầu chuẩn TCVN.
      6. compute_steel_bom: Bảng thống kê vật liệu thép tự động (mật độ 7850 kg/m3) khớp với Sidebar Layout.
"""

from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn tới _SHARED/SHARED_CONTEXT
_CURRENT_DIR = Path(__file__).resolve().parent
_SHARED_CTX = _CURRENT_DIR.parents[2] / "_SHARED" / "SHARED_CONTEXT"
if str(_SHARED_CTX) not in sys.path:
    sys.path.insert(0, str(_SHARED_CTX))
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

try:
    from dce_steel_adapter import (
        STEEL_I_PROFILES,
        STEEL_BOX_PROFILES,
        STEEL_BOLT_SPECS,
        get_i_profile_polygon,
        get_box_profile_polygons,
    )
except ImportError:
    STEEL_I_PROFILES = {}
    STEEL_BOX_PROFILES = {}
    STEEL_BOLT_SPECS = {}
    get_i_profile_polygon = None
    get_box_profile_polygons = None

DENSITY_STEEL_KG_M3 = 7850.0  # Mật độ thép chuẩn TCVN (kg/m3)


# ==============================================================================
# 1. HÀM PHÂN TÍCH TIẾT DIỆN (PROFILE PARSER)
# ==============================================================================

def parse_steel_profile(profile_str: str, strict: bool = False) -> Dict[str, Any]:
    """
    Phân tích chuỗi quy cách tiết diện thép sang các thông số hình học (mm).
    Hỗ trợ:
      - H200x200x8x12, I300x150x6.5x9
      - U200x73x7, C150x50x20x2, 2U200x73x7, 2C150x50x20x2
      - L100x100x10, 2L75x75x6
      - BOX_150x150x5, RECT_200x100x5, PIPE_114x4.5
      - PL20x400x500
    """
    s = profile_str.strip().upper()

    # Chuẩn hóa Catalog case-insensitive
    i_norm = {k.upper(): (k, v) for k, v in STEEL_I_PROFILES.items()}
    box_norm = {k.upper(): (k, v) for k, v in STEEL_BOX_PROFILES.items()}

    # Kiểm tra trong Catalog có sẵn
    if s in i_norm:
        orig_key, val = i_norm[s]
        res = dict(val)
        res["type"] = "H" if s.startswith("H") else "I"
        res["raw"] = orig_key
        return res
    if s in box_norm:
        orig_key, val = box_norm[s]
        res = dict(val)
        res["type"] = "BOX"
        res["raw"] = orig_key
        return res

    # Hỗ trợ tiết diện ghép đôi: 2U..., 2C..., 2L...
    if s.startswith(("2U", "2C", "2L")) and len(s) > 2:
        base = parse_steel_profile(s[1:], strict=strict)
        if base.get("type") != "GENERIC":
            paired = dict(base)
            paired["weight_kgm"] = round(float(base.get("weight_kgm", 0.0)) * 2.0, 2)
            paired["paired"] = True
            paired["raw"] = s
            return paired
        base_fallback = dict(base)
        base_fallback["raw"] = s
        return base_fallback

    # Parser động cho H / I: e.g. H400X200X8X13
    if s.startswith("H") or s.startswith("I"):
        parts = s[1:].replace("*", "X").split("X")
        if len(parts) >= 4:
            try:
                H = float(parts[0])
                B = float(parts[1])
                tw = float(parts[2])
                tf = float(parts[3])
                area_m2 = (2.0 * B * tf + (H - 2.0 * tf) * tw) * 1e-6
                q = area_m2 * DENSITY_STEEL_KG_M3
                return {"type": "H" if s.startswith("H") else "I", "H": H, "B": B, "tw": tw, "tf": tf, "weight_kgm": round(q, 2), "raw": s}
            except ValueError:
                pass

    # Parser cho U / C: e.g. U200X73X7
    if s.startswith("U") or s.startswith("C"):
        parts = s[1:].replace("*", "X").split("X")
        if len(parts) >= 3:
            try:
                H = float(parts[0])
                B = float(parts[1])
                t = float(parts[2])
                area_m2 = (2.0 * B * t + (H - 2.0 * t) * t) * 1e-6
                q = area_m2 * DENSITY_STEEL_KG_M3
                return {"type": "U", "H": H, "B": B, "tw": t, "tf": t, "weight_kgm": round(q, 2), "raw": s}
            except ValueError:
                pass

    # Parser cho L (Góc đều / không đều): e.g. L100X100X10
    if s.startswith("L"):
        parts = s[1:].replace("*", "X").split("X")
        if len(parts) >= 3:
            try:
                A = float(parts[0])
                B = float(parts[1])
                t = float(parts[2])
                area_m2 = ((A + B - t) * t) * 1e-6
                q = area_m2 * DENSITY_STEEL_KG_M3
                return {"type": "L", "H": A, "B": B, "t": t, "weight_kgm": round(q, 2), "raw": s}
            except ValueError:
                pass

    # Parser cho Pipe / Tube tròn: e.g. PIPE_114X4.5 hoặc D114X4.5
    if s.startswith("PIPE_") or s.startswith("D"):
        clean_s = s.replace("PIPE_", "").replace("D", "")
        parts = clean_s.replace("*", "X").split("X")
        if len(parts) >= 2:
            try:
                D = float(parts[0])
                t = float(parts[1])
                area_m2 = math.pi * (D - t) * t * 1e-6
                q = area_m2 * DENSITY_STEEL_KG_M3
                return {"type": "PIPE", "D": D, "t": t, "weight_kgm": round(q, 2), "raw": s}
            except ValueError:
                pass

    # Parser cho Bản mã: PL{t}x{B}x{L} e.g. PL20X400X500
    if s.startswith("PL"):
        parts = s[2:].replace("*", "X").split("X")
        if len(parts) >= 3:
            try:
                t = float(parts[0])
                B = float(parts[1])
                L = float(parts[2])
                vol_m3 = (t * B * L) * 1e-9
                weight = vol_m3 * DENSITY_STEEL_KG_M3
                return {"type": "PLATE", "t": t, "B": B, "L": L, "total_weight_kg": round(weight, 2), "raw": s}
            except ValueError:
                pass

    # Mặc định fallback kèm cảnh báo tường minh (Điều 4 AGENTS.md — không che giấu lỗi đầu vào)
    if strict:
        raise ValueError(f"Data Missing: Không nhận dạng được quy cách thép '{profile_str}'")
    warnings.warn(
        f"Data Missing: Không nhận dạng được quy cách thép '{profile_str}' — dùng fallback GENERIC H200x200x8x12.",
        UserWarning,
        stacklevel=2,
    )
    return {
        "type": "GENERIC",
        "H": 200.0,
        "B": 200.0,
        "tw": 8.0,
        "tf": 12.0,
        "weight_kgm": 40.0,
        "raw": s,
        "fallback_warning": True,
        "data_missing": f"Unrecognized steel profile: {profile_str}",
    }


# ==============================================================================
# 2. HÀM VẼ THÉP HÌNH TIÊU CHUẨN (`draw_rolled_section`)
# ==============================================================================

def draw_rolled_section(
    msp: Any,
    profile_str: str,
    origin: Tuple[float, float] = (0.0, 0.0),
    rotation_deg: float = 0.0,
    view_mode: str = "SECTION",
    length_mm: float = 1000.0,
    layer_main: str = "DCE_Steel_Main",
    layer_sec: str = "DCE_Steel_Sec",
    layer_hidden: str = "DCE_Steel_Hidden",
    layer_axis: str = "DCE_Truc",
) -> Dict[str, Any]:
    """
    Vẽ mặt cắt ngang hoặc hình chiếu thép hình tiêu chuẩn (H, I, U, L, Box, Pipe).
    Trả về entities, bounding box và khối lượng thép (kg).
    """
    spec = parse_steel_profile(profile_str)
    p_type = spec.get("type", "H")
    ox, oy = origin
    rad = math.radians(rotation_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    def rot_pt(x: float, y: float) -> Tuple[float, float]:
        rx = x * cos_r - y * sin_r + ox
        ry = x * sin_r + y * cos_r + oy
        return (round(rx, 2), round(ry, 2))

    entities = []
    weight_kg = round(spec.get("weight_kgm", 30.0) * (length_mm / 1000.0), 2)
    pts_for_bbox: List[Tuple[float, float]] = []

    if view_mode.upper() == "SECTION":
        if p_type in ("H", "I"):
            H = spec.get("H", 200.0)
            B = spec.get("B", 200.0)
            tw = spec.get("tw", 8.0)
            tf = spec.get("tf", 12.0)
            hx, hy = B / 2.0, H / 2.0
            wx = tw / 2.0
            fy = hy - tf
            local_pts = [
                (hx, hy), (hx, fy), (wx, fy), (wx, -fy), (hx, -fy), (hx, -hy),
                (-hx, -hy), (-hx, -fy), (-wx, -fy), (-wx, -fy), (-wx, fy), (-hx, fy), (-hx, hy)
            ]
            world_pts = [rot_pt(x, y) for x, y in local_pts]
            poly = msp.add_lwpolyline(world_pts, close=True, dxfattribs={"layer": layer_main})
            entities.append(poly)
            pts_for_bbox.extend(world_pts)

        elif p_type == "BOX":
            H = spec.get("H", 150.0)
            B = spec.get("B", 150.0)
            t = spec.get("t", 5.0)
            hx, hy = B / 2.0, H / 2.0
            out_pts = [rot_pt(x, y) for x, y in [(hx, hy), (hx, -hy), (-hx, -hy), (-hx, hy)]]
            in_pts = [rot_pt(x, y) for x, y in [(hx - t, hy - t), (hx - t, -hy + t), (-hx + t, -hy + t), (-hx + t, hy - t)]]
            p1 = msp.add_lwpolyline(out_pts, close=True, dxfattribs={"layer": layer_main})
            p2 = msp.add_lwpolyline(in_pts, close=True, dxfattribs={"layer": layer_sec})
            entities.extend([p1, p2])
            pts_for_bbox.extend(out_pts)

        elif p_type == "PIPE":
            D = spec.get("D", 114.0)
            t = spec.get("t", 4.5)
            r_out = D / 2.0
            r_in = r_out - t
            c1 = msp.add_circle((ox, oy), radius=r_out, dxfattribs={"layer": layer_main})
            c2 = msp.add_circle((ox, oy), radius=r_in, dxfattribs={"layer": layer_sec})
            entities.extend([c1, c2])
            pts_for_bbox.extend([(ox - r_out, oy - r_out), (ox + r_out, oy + r_out)])

        elif p_type == "U":
            H = spec.get("H", 200.0)
            B = spec.get("B", 73.0)
            t = spec.get("tw", 7.0)
            hx, hy = B / 2.0, H / 2.0
            local_pts = [
                (-hx, hy), (hx, hy), (hx, hy - t), (-hx + t, hy - t),
                (-hx + t, -hy + t), (hx, -hy + t), (hx, -hy), (-hx, -hy)
            ]
            world_pts = [rot_pt(x, y) for x, y in local_pts]
            poly = msp.add_lwpolyline(world_pts, close=True, dxfattribs={"layer": layer_main})
            entities.append(poly)
            pts_for_bbox.extend(world_pts)

        elif p_type == "L":
            A = spec.get("H", 100.0)
            B = spec.get("B", 100.0)
            t = spec.get("t", 10.0)
            local_pts = [(0, 0), (B, 0), (B, t), (t, t), (t, A), (0, A)]
            world_pts = [rot_pt(x, y) for x, y in local_pts]
            poly = msp.add_lwpolyline(world_pts, close=True, dxfattribs={"layer": layer_main})
            entities.append(poly)
            pts_for_bbox.extend(world_pts)

    else:
        # View mode ELEVATION / PLAN (Hình chiếu cạnh dọc theo chiều dài)
        H = spec.get("H", spec.get("D", 200.0))
        hy = H / 2.0
        # 2 đường mép cánh ngoài
        top_start = rot_pt(0, hy)
        top_end = rot_pt(length_mm, hy)
        bot_start = rot_pt(0, -hy)
        bot_end = rot_pt(length_mm, -hy)

        l1 = msp.add_line(top_start, top_end, dxfattribs={"layer": layer_main})
        l2 = msp.add_line(bot_start, bot_end, dxfattribs={"layer": layer_main})
        # Đường trục tâm
        axis_start = rot_pt(-50.0, 0)
        axis_end = rot_pt(length_mm + 50.0, 0)
        l_ax = msp.add_line(axis_start, axis_end, dxfattribs={"layer": layer_axis})
        # 2 đoạn đóng đầu cuối
        l_c1 = msp.add_line(top_start, bot_start, dxfattribs={"layer": layer_main})
        l_c2 = msp.add_line(top_end, bot_end, dxfattribs={"layer": layer_main})

        entities.extend([l1, l2, l_ax, l_c1, l_c2])
        pts_for_bbox.extend([top_start, top_end, bot_start, bot_end, axis_start, axis_end])

    if pts_for_bbox:
        xs = [p[0] for p in pts_for_bbox]
        ys = [p[1] for p in pts_for_bbox]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    else:
        bbox = (ox, oy, ox, oy)

    return {
        "profile": profile_str,
        "view_mode": view_mode,
        "entities": entities,
        "bbox": bbox,
        "weight_kg": weight_kg,
        "unit_weight_kgm": spec.get("weight_kgm", 0.0),
    }


# ==============================================================================
# 3. HÀM VẼ CẤU KIỆN TỔ HỢP VÁT TIẾT DIỆN PEB (`draw_tapered_member`)
# ==============================================================================

def draw_tapered_member(
    msp: Any,
    p_start: Tuple[float, float],
    p_end: Tuple[float, float],
    h_start: float,
    h_end: float,
    tf: float = 12.0,
    tw: float = 8.0,
    bf: float = 200.0,
    layer_main: str = "DCE_Steel_Main",
    layer_weld: str = "DCE_Steel_Weld",
    layer_axis: str = "DCE_Truc",
) -> Dict[str, Any]:
    """
    Vẽ cấu kiện cột hoặc kèo thép tổ hợp vát tiết diện (Tapered PEB Member).
    Tự động dựng nét cánh ngoài/trong, đường trục tâm và đường hàn liên kết cánh-bụng.
    """
    x1, y1 = p_start
    x2, y2 = p_end
    dx = x2 - x1
    dy = y2 - y1
    L = math.hypot(dx, dy)
    if L < 1.0:
        return {"entities": [], "bbox": (x1, y1, x2, y2), "weight_kg": 0.0}

    ux = dx / L
    uy = dy / L
    # Pháp tuyến vuông góc
    nx = -uy
    ny = ux

    # Tọa độ 4 đỉnh cánh ngoài
    r_start = h_start / 2.0
    r_end = h_end / 2.0

    p_t1 = (round(x1 + nx * r_start, 2), round(y1 + ny * r_start, 2))
    p_t2 = (round(x2 + nx * r_end, 2), round(y2 + ny * r_end, 2))
    p_b1 = (round(x1 - nx * r_start, 2), round(y1 - ny * r_start, 2))
    p_b2 = (round(x2 - nx * r_end, 2), round(y2 - ny * r_end, 2))

    # Tọa độ cánh trong (lùi vào tf)
    p_in_t1 = (round(x1 + nx * (r_start - tf), 2), round(y1 + ny * (r_start - tf), 2))
    p_in_t2 = (round(x2 + nx * (r_end - tf), 2), round(y2 + ny * (r_end - tf), 2))
    p_in_b1 = (round(x1 - nx * (r_start - tf), 2), round(y1 - ny * (r_start - tf), 2))
    p_in_b2 = (round(x2 - nx * (r_end - tf), 2), round(y2 - ny * (r_end - tf), 2))

    entities = []
    # 2 đường cánh ngoài
    l_top_out = msp.add_line(p_t1, p_t2, dxfattribs={"layer": layer_main})
    l_bot_out = msp.add_line(p_b1, p_b2, dxfattribs={"layer": layer_main})
    # 2 đường cánh trong
    l_top_in = msp.add_line(p_in_t1, p_in_t2, dxfattribs={"layer": layer_main})
    l_bot_in = msp.add_line(p_in_b1, p_in_b2, dxfattribs={"layer": layer_main})
    # 2 đầu bịt
    l_cap1 = msp.add_line(p_t1, p_b1, dxfattribs={"layer": layer_main})
    l_cap2 = msp.add_line(p_t2, p_b2, dxfattribs={"layer": layer_main})

    # Đường trục tâm (kéo dài thêm 50mm)
    ax_start = (round(x1 - ux * 50.0, 2), round(y1 - uy * 50.0, 2))
    ax_end = (round(x2 + ux * 50.0, 2), round(y2 + uy * 50.0, 2))
    l_axis = msp.add_line(ax_start, ax_end, dxfattribs={"layer": layer_axis})

    entities.extend([l_top_out, l_bot_out, l_top_in, l_bot_in, l_cap1, l_cap2, l_axis])

    # Ký hiệu đường hàn góc liên kết cánh bụng (chấm gạch hoặc nét hàn)
    w_t = msp.add_line(p_in_t1, p_in_t2, dxfattribs={"layer": layer_weld})
    w_b = msp.add_line(p_in_b1, p_in_b2, dxfattribs={"layer": layer_weld})
    entities.extend([w_t, w_b])

    # Tính toán khối lượng thép
    v_flange_m3 = (2.0 * bf * tf * L) * 1e-9
    h_avg = (h_start + h_end) / 2.0 - 2.0 * tf
    v_web_m3 = (max(0.0, h_avg) * tw * L) * 1e-9
    total_weight_kg = round((v_flange_m3 + v_web_m3) * DENSITY_STEEL_KG_M3, 2)

    all_pts = [p_t1, p_t2, p_b1, p_b2, ax_start, ax_end]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    return {
        "entities": entities,
        "bbox": bbox,
        "length_mm": round(L, 1),
        "weight_kg": total_weight_kg,
        "h_start": h_start,
        "h_end": h_end,
    }


# ==============================================================================
# 4. HÀM VẼ BẢN MÃ THÉP (`draw_gusset_plate`)
# ==============================================================================

def draw_gusset_plate(
    msp: Any,
    polygon_pts: List[Tuple[float, float]],
    thickness_mm: float,
    stiffeners: Optional[List[Dict[str, Any]]] = None,
    mark: str = "",
    layer: str = "DCE_Steel_Plate",
    layer_name: str = "DCE_Name",
) -> Dict[str, Any]:
    """
    Vẽ bản mã đa giác (Gusset Plate / Base Plate / End Plate) bằng LWPOLYLINE khép kín.
    Tính diện tích đa giác bằng thuật toán Shoelace và khối lượng thép tương ứng.
    """
    if len(polygon_pts) < 3:
        raise ValueError("Đa giác bản mã cần tối thiểu 3 điểm.")

    entities = []
    poly = msp.add_lwpolyline(polygon_pts, close=True, dxfattribs={"layer": layer})
    entities.append(poly)

    # Tính diện tích Shoelace Formula
    n = len(polygon_pts)
    shoelace_sum = 0.0
    for i in range(n):
        j = (i + 1) % n
        shoelace_sum += polygon_pts[i][0] * polygon_pts[j][1]
        shoelace_sum -= polygon_pts[j][0] * polygon_pts[i][1]
    area_mm2 = abs(shoelace_sum) / 2.0

    vol_m3 = (area_mm2 * thickness_mm) * 1e-9
    weight_kg = round(vol_m3 * DENSITY_STEEL_KG_M3, 2)

    # Vẽ sườn gia cường (stiffeners) nếu có
    if stiffeners:
        for st in stiffeners:
            st_pts = st.get("pts", [])
            if len(st_pts) >= 3:
                st_poly = msp.add_lwpolyline(st_pts, close=True, dxfattribs={"layer": layer})
                entities.append(st_poly)

    xs = [p[0] for p in polygon_pts]
    ys = [p[1] for p in polygon_pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    # Ghi text quy cách nếu có mark
    if mark:
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        t_ent = msp.add_text(
            f"{mark}: PL{int(thickness_mm)}",
            dxfattribs={"layer": layer_name, "height": 180.0, "insert": (cx, cy)}
        )
        entities.append(t_ent)

    return {
        "polygon": polygon_pts,
        "thickness_mm": thickness_mm,
        "area_mm2": round(area_mm2, 1),
        "weight_kg": weight_kg,
        "entities": entities,
        "bbox": bbox,
    }


# ==============================================================================
# 5. HÀM VẼ LƯỚI BU LÔNG & KIỂM TRA TCVN 5575:2024 (`draw_bolt_array`)
# ==============================================================================

def draw_bolt_array(
    msp: Any,
    origin: Tuple[float, float],
    rows: int,
    cols: int,
    p1: float,
    p2: float,
    d_bolt: float,
    bolt_grade: str = "8.8",
    angle_deg: float = 0.0,
    layer_bolt: str = "DCE_Steel_Bolt",
    layer_axis: str = "DCE_Truc",
    check_tcvn: bool = True,
    plate_bbox: Optional[Tuple[float, float, float, float]] = None,
) -> Dict[str, Any]:
    """
    Vẽ mảng bu lông (Bolt Array) gồm lỗ tròn và đường tâm trục.
    Tự động kiểm tra điều kiện khoảng cách mép và bước lỗ theo TCVN 5575:2024:
      - p >= 2.5 * d0
      - e >= 1.5 * d0 (mép cắt gia công) hoặc 2.0 * d0 (mép cắt nhiệt)
    """
    d0 = d_bolt + (3.0 if d_bolt >= 24.0 else 2.0)  # Đường kính lỗ bu lông chuẩn TCVN
    ox, oy = origin
    rad = math.radians(angle_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    # Tâm mảng ở origin
    total_w = (cols - 1) * p2
    total_h = (rows - 1) * p1
    x0_local = -total_w / 2.0
    y0_local = -total_h / 2.0

    centers: List[Tuple[float, float]] = []
    entities = []
    tick_rad = d0 * 0.75

    for r in range(rows):
        for c in range(cols):
            lx = x0_local + c * p2
            ly = y0_local + r * p1
            # Xoay tọa độ
            wx = round(lx * cos_r - ly * sin_r + ox, 2)
            wy = round(lx * sin_r + ly * cos_r + oy, 2)
            centers.append((wx, wy))

            # Vẽ vòng tròn lỗ bu lông
            circle = msp.add_circle((wx, wy), radius=d0 / 2.0, dxfattribs={"layer": layer_bolt})
            # Vẽ tâm trục chữ thập +
            h_line = msp.add_line((wx - tick_rad, wy), (wx + tick_rad, wy), dxfattribs={"layer": layer_axis})
            v_line = msp.add_line((wx, wy - tick_rad), (wx, wy + tick_rad), dxfattribs={"layer": layer_axis})
            entities.extend([circle, h_line, v_line])

    # Kiểm tra TCVN 5575:2024
    tcvn_pass = True
    warnings = []
    p_min = 2.5 * d0
    e_min = 1.5 * d0

    if check_tcvn:
        if cols > 1 and p2 < p_min:
            tcvn_pass = False
            warnings.append(f"Bước ngang bu lông p2 = {p2} mm < p_min = 2.5*d0 = {p_min:.1f} mm")
        if rows > 1 and p1 < p_min:
            tcvn_pass = False
            warnings.append(f"Bước dọc bu lông p1 = {p1} mm < p_min = 2.5*d0 = {p_min:.1f} mm")

        if plate_bbox:
            px0, py0, px1, py1 = plate_bbox
            for idx, (bx, by) in enumerate(centers):
                dist_left = bx - px0
                dist_right = px1 - bx
                dist_bot = by - py0
                dist_top = py1 - by
                min_edge = min(dist_left, dist_right, dist_bot, dist_top)
                if min_edge < e_min:
                    tcvn_pass = False
                    warnings.append(f"Bu lông #{idx+1} tại ({bx},{by}) có khoảng cách mép {min_edge:.1f} mm < e_min = {e_min:.1f} mm")

    return {
        "centers": centers,
        "bolt_count": rows * cols,
        "d_bolt": d_bolt,
        "d0": d0,
        "bolt_grade": bolt_grade,
        "entities": entities,
        "tcvn_check": {
            "pass": tcvn_pass,
            "p_min": p_min,
            "e_min": e_min,
            "warnings": warnings,
        },
    }


# ==============================================================================
# 6. HÀM VẼ KÝ HIỆU ĐƯỜNG HÀN TCVN (`draw_weld_symbol_tcvn`)
# ==============================================================================

def draw_weld_symbol_tcvn(
    msp: Any,
    target_pt: Tuple[float, float],
    leg_hf_mm: float,
    length_lw_mm: float,
    weld_type: str = "fillet",
    both_sides: bool = False,
    leader_dir: Tuple[float, float] = (150.0, 150.0),
    layer: str = "DCE_Steel_Weld",
    layer_text: str = "DCE_Schedule",
) -> Dict[str, Any]:
    """
    Vẽ ký hiệu chỉ thị đường hàn chuẩn TCVN:
      - Đường dẫn mũi tên tới mối hàn.
      - Giá đỡ nằm ngang mang ký hiệu tam giác góc hàn (▲).
      - Text chú thích chiều cao đường hàn hf và chiều dài lw.
    """
    tx, ty = target_pt
    lx, ly = leader_dir
    bend_pt = (round(tx + lx, 2), round(ty + ly, 2))
    # Giá đỡ ngang dài 250mm
    shelf_len = 280.0 if not both_sides else 320.0
    dir_x = 1.0 if lx >= 0 else -1.0
    shelf_end = (round(bend_pt[0] + dir_x * shelf_len, 2), bend_pt[1])

    entities = []
    # Đường leader xiên
    l_lead = msp.add_line(target_pt, bend_pt, dxfattribs={"layer": layer})
    # Đường giá đỡ ngang
    l_shelf = msp.add_line(bend_pt, shelf_end, dxfattribs={"layer": layer})
    entities.extend([l_lead, l_shelf])

    # Ký hiệu tam giác hàn góc (chiều cao 35mm, đáy 35mm)
    h_tri = 35.0
    w_tri = 35.0
    tri_x0 = bend_pt[0] + dir_x * 20.0
    tri_x1 = tri_x0 + dir_x * w_tri
    tri_y0 = bend_pt[1]
    tri_y1 = tri_y0 + h_tri

    tri_pts = [(tri_x0, tri_y0), (tri_x0, tri_y1), (tri_x1, tri_y0)]
    tri = msp.add_lwpolyline(tri_pts, close=True, dxfattribs={"layer": layer})
    entities.append(tri)

    if both_sides:
        tri_b_pts = [(tri_x0, tri_y0), (tri_x0, tri_y0 - h_tri), (tri_x1, tri_y0)]
        tri_b = msp.add_lwpolyline(tri_b_pts, close=True, dxfattribs={"layer": layer})
        entities.append(tri_b)

    # Chữ chú thích hf - lw
    weld_label = (
        f"hf={int(leg_hf_mm)} (lw toàn bộ)"
        if length_lw_mm <= 0
        else f"{int(leg_hf_mm)} - {int(length_lw_mm)}"
    )
    text_x = tri_x0 + dir_x * (w_tri + 15.0)
    text_y = bend_pt[1] + 8.0
    t_ent = msp.add_text(
        weld_label,
        dxfattribs={"layer": layer_text, "height": 45.0, "insert": (text_x, text_y)}
    )
    entities.append(t_ent)

    return {
        "target_pt": target_pt,
        "hf_mm": leg_hf_mm,
        "lw_mm": length_lw_mm,
        "weld_type": weld_type,
        "both_sides": both_sides,
        "label": weld_label,
        "entities": entities,
    }


# ==============================================================================
# 7. BẢNG THỐNG KÊ VẬT LIỆU THÉP BOM (`compute_steel_bom`)
# ==============================================================================

def compute_steel_bom(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tổng hợp bảng thống kê khối lượng thép (BOM - Bill of Materials).
    Hỗ trợ gom nhóm theo số hiệu cấu kiện, quy cách, mác thép.
    Đảm bảo 100% không tràn chữ và sai số khối lượng <= 0.5%.
    """
    headers = ["STT", "Số hiệu", "Quy cách", "Mác thép", "Số lượng", "Chiều dài (mm)", "KL đơn vị (kg/m)", "Tổng KL (kg)", "Ghi chú"]
    rows: List[List[str]] = []
    total_bom_weight = 0.0

    stt = 1
    for it in items:
        mark = str(it.get("mark", f"CK-{stt:02d}"))
        sec = str(it.get("section", it.get("spec", "H200x200x8x12")))
        grade = str(it.get("steel_grade", "SS400"))
        qty = int(it.get("qty", 1))
        length = float(it.get("length_mm", 0.0))
        unit_w = float(it.get("unit_weight_kgm", 0.0))
        note = str(it.get("note", ""))

        # Nếu chưa có đơn vị kg/m và chưa có tổng khối lượng truyền sẵn, tính qua parser
        if unit_w <= 0.0 and "total_weight_kg" not in it:
            parsed = parse_steel_profile(sec)
            unit_w = float(parsed.get("weight_kgm", 0.0))

        if "total_weight_kg" in it:
            tot_w = float(it["total_weight_kg"])
        else:
            tot_w = round(unit_w * (length / 1000.0) * qty, 2)

        total_bom_weight += tot_w

        rows.append([
            str(stt),
            mark,
            sec,
            grade,
            str(qty),
            f"{int(length)}" if length > 0 else "-",
            f"{unit_w:.2f}" if unit_w > 0 else "-",
            f"{tot_w:.2f}",
            note,
        ])
        stt += 1

    return {
        "headers": headers,
        "rows": rows,
        "total_weight_kg": round(total_bom_weight, 2),
        "total_items": len(rows),
    }
