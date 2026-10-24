"""
cad_bridge.py — AutoCAD & DCE Pro Direct Drawing Bridge
========================================================
Sprint 3 · Phase 2 & 3 · New DCE Pro Engine

Mục đích:
    Điều khiển AutoCAD qua COM Automation hoặc thư viện ezdxf để:
    1. Tự động vẽ mặt cắt và hình học cấu kiện BTCT (dầm, cột, vách).
    2. Kế thừa toàn bộ hệ thống 46 Layers chuẩn DCE_*, 18 DimStyles Dce_*MV
       và 168 Blocks từ template C:\\Dce Pro\\Cad\\Form 2.dxf.
    3. Tự động chèn bảng thống kê thép chuẩn DCE gồm tiêu đề TKTitle và các
       Block hình dáng tham số TK1..TK44 với đầy đủ thuộc tính ATTDEF:
       SH, DK, L/L1/L2, M1/M2, sumL, SL, SKC, TSL, Lall, KL.
    4. Chèn các Block ký hiệu kỹ thuật chuẩn DCE:
       - Dce_KhTenTruc (TRUC)
       - Dce_CaoTrinh (CT)
       - TenCauKien (TENCAUKIEN, SOCAUKIEN)
       - Dce_KhtSH (SH)

Giao thức:
    1. COM Automation: GetActiveObject("AutoCAD.Application")
    2. Template Mode ezdxf: nạp Form 2.dxf, bảo lưu toàn bộ Block/Layer/DimStyle tables
    3. Standalone Mode ezdxf: tạo file DXF mới với Layer tiêu chuẩn nếu không có template
    4. Demo Mode: fallback không cần AutoCAD / ezdxf

Sử dụng:
    # Vẽ mặt cắt dầm kèm bảng thống kê thép DCE từ Form 2.dxf:
    python cad_bridge.py --mode beam_section \\
        --b 300 --h 600 --cover 30 \\
        --top "3D22" --bot "3D25" --stirrup "D10@150" \\
        --schedule --output beam_dce.dxf

    # Xuất riêng bảng thống kê thép chuẩn TK1..TK44:
    python cad_bridge.py --mode rebar_schedule \\
        --schedule-items '[{"sh":1,"dk":25,"shape":"TK1","dims":{"L":5800},"sl":3}]' \\
        --output schedule.dxf
"""

import sys
import os
import json
import argparse
import math
import re
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 0. Phát hiện backend & Template mặc định
# ─────────────────────────────────────────────────────────────────────────────

_CAD_BACKEND = None   # "win32com" | "ezdxf" | None

try:
    import win32com.client as _wc
    _CAD_BACKEND = "win32com"
except ImportError:
    pass

if _CAD_BACKEND is None:
    try:
        import ezdxf
        _CAD_BACKEND = "ezdxf"
    except ImportError:
        pass

DCE_DEFAULT_TEMPLATE = Path(r"C:\Dce Pro\Cad\Form 2.dxf")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Bảng Layer chuẩn (tương thích cả tiêu chuẩn và DCE Pro)
# ─────────────────────────────────────────────────────────────────────────────

LAYERS = {
    "outline":   {"name": "DCE_BaoBeTong",  "fallback": "KC-BEAM-OUTLINE",    "color": 7, "ltype": "Continuous", "lw": 0.35},
    "rebar_top": {"name": "DCE_ThepChu",    "fallback": "KC-REBAR-TOP",        "color": 1, "ltype": "Continuous", "lw": 0.25},
    "rebar_bot": {"name": "DCE_ThepChu",    "fallback": "KC-REBAR-BOT",        "color": 3, "ltype": "Continuous", "lw": 0.25},
    "stirrup":   {"name": "DCE_ThepDai",    "fallback": "KC-REBAR-STIRRUP",    "color": 4, "ltype": "Continuous", "lw": 0.18},
    "dim":       {"name": "DCE_Dim",        "fallback": "KC-DIM",              "color": 2, "ltype": "Continuous", "lw": 0.13},
    "text":      {"name": "DCE_TKT-TEXT",   "fallback": "KC-TEXT-ANNOTATION",  "color": 7, "ltype": "Continuous", "lw": 0.13},
    "center":    {"name": "DCE_Truc",       "fallback": "KC-CENTERLINE",       "color": 4, "ltype": "CENTER",     "lw": 0.09},
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Rebar string parser & Trọng lượng đơn vị TCVN 5574:2018
# ─────────────────────────────────────────────────────────────────────────────

_REBAR_RE = re.compile(
    r"(\d+)D(\d+(?:\.\d+)?)"        # nD[dia]  ví dụ 2D25, 1D22
    r"|D(\d+(?:\.\d+)?)@(\d+)"      # D[dia]@[spacing]  cốt đai
    r"|(\d+)[Φφ](\d+(?:\.\d+)?)",   # nΦ[dia]
    re.IGNORECASE
)


def parse_rebar_string(s: str) -> list:
    """Bóc tách chuỗi thép: [{'n': 2, 'dia': 25.0, 'spacing': None}, ...]"""
    bars = []
    for m in _REBAR_RE.finditer(s):
        if m.group(1) and m.group(2):
            bars.append({"n": int(m.group(1)), "dia": float(m.group(2)), "spacing": None})
        elif m.group(3) and m.group(4):
            bars.append({"n": None, "dia": float(m.group(3)), "spacing": int(m.group(4))})
        elif m.group(5) and m.group(6):
            bars.append({"n": int(m.group(5)), "dia": float(m.group(6)), "spacing": None})
    return bars


def rebar_area_mm2(bars: list) -> float:
    """Tính tổng diện tích mặt cắt ngang thanh thép (mm²)."""
    total = 0.0
    for bar in bars:
        if bar.get("n"):
            total += bar["n"] * math.pi * (bar["dia"] / 2.0) ** 2
    return total


def unit_weight_kg_m(dia_mm: float) -> float:
    """Khối lượng đơn vị thép thanh tròn theo TCVN 5574:2018 (kg/m)."""
    return (math.pi * (dia_mm / 2000.0) ** 2) * 7850.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rect_pts(ox, oy, b, h):
    return [
        (ox,     oy),
        (ox + b, oy),
        (ox + b, oy + h),
        (ox,     oy + h),
        (ox,     oy),
    ]


def _circle_pts(cx, cy, r, n=24):
    pts = []
    for i in range(n + 1):
        theta = 2 * math.pi * i / n
        pts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    return pts


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 4. Engine chèn Bảng Thống Kê Thép chuẩn DCE (TKTitle + TK1..TK44)
# ─────────────────────────────────────────────────────────────────────────────

def insert_dce_rebar_schedule(doc_or_msp, rebar_items: list, insert_pt=(0.0, 0.0), skc: int = 1, anno_scale: float = 1.0) -> dict:
    """
    Tự động chèn bảng thống kê thép chuẩn Form 2.dxf của DCE Pro.
    - insert_pt: Tọa độ góc trên bên trái của bảng thống kê.
    - Tiêu đề TKTitle: Cao 35mm * anno_scale, rộng 192.5mm * anno_scale.
    - Mỗi hàng thép (TK1..TK44): Cao 8mm * anno_scale, rộng 192.5mm * anno_scale.
    - Tự động tính toán sumL, TSL, Lall, KL theo TCVN 5574:2018.
    """
    import ezdxf
    if hasattr(doc_or_msp, "modelspace"):
        doc = doc_or_msp
        msp = doc.modelspace()
    else:
        msp = doc_or_msp
        doc = msp.doc

    ox, oy = insert_pt
    scale = float(anno_scale)
    has_title_block = "TKTitle" in doc.blocks

    # 1. Chèn tiêu đề TKTitle nếu có trong template
    if has_title_block:
        msp.add_blockref("TKTitle", (ox, oy), dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
    else:
        # Fallback vẽ khung tiêu đề đơn giản nếu không có template
        msp.add_lwpolyline([(ox, oy), (ox + 192.5 * scale, oy), (ox + 192.5 * scale, oy - 35.0 * scale), (ox, oy - 35.0 * scale), (ox, oy)], close=True)
        msp.add_text("BẢNG THỐNG KÊ CỐT THÉP", dxfattribs={"height": 4.0 * scale, "insert": (ox + 30.0 * scale, oy - 15.0 * scale)})

    y_cur = oy - 35.0 * scale
    total_weight = 0.0
    total_length = 0.0
    rows_inserted = []

    for i, item in enumerate(rebar_items):
        sh = item.get("sh", i + 1)
        dk = float(item.get("dk", 20.0))
        shape = item.get("shape", "TK1").upper()
        dims = item.get("dims", {})
        sl = int(item.get("sl", 1))
        skc_row = int(item.get("skc", skc))
        tsl = sl * skc_row

        # Ánh xạ tên Block TK chuẩn Form 2.dxf
        shape_blk = shape
        if shape in ["STRAIGHT", "THANG"]:
            shape_blk = "TK1"
        elif shape in ["L_HOOK", "KE_1_DAU"]:
            shape_blk = "TK2"
        elif shape in ["U_HOOK"]:
            shape_blk = "TK3"
        elif shape in ["KE_2_DAU", "HOOK_2_ENDS"]:
            shape_blk = "TK4"
        elif shape in ["STIRRUP_135", "DAI_MOC"]:
            shape_blk = "TK8"
        elif shape in ["STIRRUP", "STIRRUP_CLOSED", "DAI_KIN"]:
            shape_blk = "TK9"
        elif shape in ["DAI_TRON", "CIRCULAR_STIRRUP"]:
            shape_blk = "TK23"

        # Tính toán chiều dài thanh sumL (mm) chính xác theo từng Block hình học
        if "sumL" in item:
            sum_l = float(item["sumL"])
        elif shape_blk in ("TK9", "STIRRUP", "STIRRUP_CLOSED", "DAI_KIN"):
            # Cốt đai kín chữ nhật: 2*(L1 + L2) + 2*M (móc đai M >= 8d)
            l1 = float(dims.get("L1", 0))
            l2 = float(dims.get("L2", 0))
            m_val = float(dims.get("M", dims.get("M1", 8 * dk)))
            sum_l = 2.0 * (l1 + l2) + 2.0 * m_val
        elif shape_blk in ("TK23", "DAI_TRON", "CIRCULAR_STIRRUP"):
            # Đai tròn đường kính D, 2 móc neo M
            d_val = float(dims.get("D", 0))
            m_val = float(dims.get("M", dims.get("M1", 8 * dk)))
            sum_l = math.pi * d_val + 2.0 * m_val
        else:
            # Các trường hợp thanh thẳng / bẻ ke (TK1, TK2, TK3, TK4, TK8...): cộng tổng các đoạn L, L1..L6, M, M1, M2
            if dims:
                seg_keys = ["L", "L1", "L2", "L3", "L4", "L5", "L6", "M", "M1", "M2"]
                found_keys = [k for k in seg_keys if k in dims]
                if found_keys:
                    sum_l = sum(float(dims[k]) for k in found_keys)
                else:
                    sum_l = sum(float(v) for v in dims.values())
            else:
                sum_l = float(item.get("L", 0.0))

        # Tổng chiều dài Lall (m) và Khối lượng KL (kg)
        lall = round(sum_l * tsl / 1000.0, 2)
        u_wt = unit_weight_kg_m(dk)
        kl = round(lall * u_wt, 2)

        total_length += lall
        total_weight += kl

        if shape_blk not in doc.blocks:
            shape_blk = "TK1" if "TK1" in doc.blocks else None

        row_pt = (ox, y_cur)

        # Chuẩn bị thuộc tính ATTDEF
        attribs = {
            "SH": str(sh),
            "DK": f"%%c{int(dk)}" if dk.is_integer() else f"%%c{dk}",
            "sumL": str(int(round(sum_l))),
            "SL": str(sl),
            "SKC": str(skc_row),
            "TSL": str(tsl),
            "Lall": f"{lall:.2f}",
            "KL": f"{kl:.2f}",
        }

        # Bổ sung các đoạn kích thước L, L1..L6, M, M1..M2
        if "L" in dims:
            attribs["L"] = str(int(dims["L"]))
        elif "L" in item:
            attribs["L"] = str(int(item["L"]))
        for k_dim, v_dim in dims.items():
            attribs[k_dim] = str(int(v_dim))

        if shape_blk and shape_blk in doc.blocks:
            bref = msp.add_blockref(shape_blk, row_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
            bref.add_auto_attribs(attribs)
        else:
            # Fallback nếu không có block TK
            msp.add_lwpolyline([(ox, y_cur), (ox + 192.5 * scale, y_cur), (ox + 192.5 * scale, y_cur - 8.0 * scale), (ox, y_cur - 8.0 * scale), (ox, y_cur)], close=True)
            txt_desc = f"{sh} | %%c{int(dk)} | L={int(sum_l)} | SL={sl} | TSL={tsl} | {lall:.2f}m | {kl:.2f}kg"
            msp.add_text(txt_desc, dxfattribs={"height": 2.2 * scale, "insert": (ox + 5.0 * scale, y_cur - 5.5 * scale)})

        rows_inserted.append({
            "sh": sh,
            "dk": dk,
            "block": shape_blk,
            "sumL_mm": sum_l,
            "tsl": tsl,
            "lall_m": lall,
            "kl_kg": kl,
            "y_pos": y_cur,
        })
        y_cur -= 8.0 * scale

    return {
        "status": "SUCCESS",
        "rows_count": len(rows_inserted),
        "total_length_m": round(total_length, 2),
        "total_weight_kg": round(total_weight, 2),
        "bottom_y": y_cur,
        "width": 192.5 * scale,
        "rows": rows_inserted,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Engine chèn các Block Ký Hiệu Kỹ Thuật chuẩn DCE
# ─────────────────────────────────────────────────────────────────────────────

def insert_dce_truc(doc_or_msp, insert_pt, name: str = "A", anno_scale: float = 1.0):
    """Chèn block ký hiệu tên trục DCE Dce_KhTenTruc (thẻ TRUC)."""
    msp = doc_or_msp.modelspace() if hasattr(doc_or_msp, "modelspace") else doc_or_msp
    doc = msp.doc
    scale = float(anno_scale)
    if "Dce_KhTenTruc" in doc.blocks:
        ref = msp.add_blockref("Dce_KhTenTruc", insert_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
        ref.add_auto_attribs({"TRUC": str(name)})
        return ref
    else:
        # Fallback circle + text
        msp.add_circle(insert_pt, 3.5 * scale, dxfattribs={"layer": "DCE_Truc" if "DCE_Truc" in doc.layers else "0"})
        msp.add_text(str(name), dxfattribs={"height": 3.0 * scale, "insert": (insert_pt[0] - 1.2 * scale, insert_pt[1] - 1.2 * scale)})
        return None


def insert_dce_caotrinh(doc_or_msp, insert_pt, elevation_str: str = "+0.000", anno_scale: float = 1.0):
    """Chèn block cao trình DCE Dce_CaoTrinh (thẻ CT)."""
    msp = doc_or_msp.modelspace() if hasattr(doc_or_msp, "modelspace") else doc_or_msp
    doc = msp.doc
    scale = float(anno_scale)
    if "Dce_CaoTrinh" in doc.blocks:
        ref = msp.add_blockref("Dce_CaoTrinh", insert_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
        ref.add_auto_attribs({"CT": str(elevation_str)})
        return ref
    else:
        msp.add_text(str(elevation_str), dxfattribs={"height": 2.5 * scale, "insert": insert_pt})
        return None


def insert_dce_tencaukien(doc_or_msp, insert_pt, name: str, count: int = 1, anno_scale: float = 1.0, scale_str: str = "TL: 1/20"):
    """
    Chèn block tên cấu kiện DCE:
    Ưu tiên dùng block ngang *U4 với thẻ TENDAM, TL cho dầm ngang, hoặc xoay TenCauKien -90 độ để chữ nằm ngang.
    """
    msp = doc_or_msp.modelspace() if hasattr(doc_or_msp, "modelspace") else doc_or_msp
    doc = msp.doc
    scale = float(anno_scale)
    if "*U4" in doc.blocks:
        ref = msp.add_blockref("*U4", insert_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
        ref.add_auto_attribs({"TENDAM": str(name), "TL": str(scale_str)})
        return ref
    elif "TenCauKien" in doc.blocks:
        ref = msp.add_blockref("TenCauKien", insert_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale, "rotation": -90.0})
        ref.add_auto_attribs({"TENCAUKIEN": str(name), "SOCAUKIEN": str(count)})
        return ref
    else:
        msp.add_text(f"{name} ({count})", dxfattribs={"height": 3.5 * scale, "insert": insert_pt})
        return None


def insert_dce_khtsh(doc_or_msp, insert_pt, sh_str: str, anno_scale: float = 1.0):
    """Chèn block số hiệu thanh thép DCE Dce_KhtSH (thẻ SH)."""
    msp = doc_or_msp.modelspace() if hasattr(doc_or_msp, "modelspace") else doc_or_msp
    doc = msp.doc
    scale = float(anno_scale)
    if "Dce_KhtSH" in doc.blocks:
        ref = msp.add_blockref("Dce_KhtSH", insert_pt, dxfattribs={"xscale": scale, "yscale": scale, "zscale": scale})
        ref.add_auto_attribs({"SH": str(sh_str)})
        return ref
    else:
        msp.add_text(str(sh_str), dxfattribs={"height": 2.0 * scale, "insert": insert_pt})
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 6. EzdxfDrawer — Hỗ trợ nạp Template Form 2.dxf & Chế độ độc lập
# ─────────────────────────────────────────────────────────────────────────────

class EzdxfDrawer:
    """Vẽ dầm và chi tiết BTCT vào DXF, kế thừa toàn bộ Block & Layer của DCE."""

    def __init__(self, output_path: str, template_path: str = None, clean_template: bool = True):
        import ezdxf
        self.output_path = output_path
        self.logs = []
        self.is_dce_template = False

        # Xác định template: ưu tiên template_path, nếu không có thì thử DCE_DEFAULT_TEMPLATE
        cand_template = None
        if template_path and Path(template_path).exists():
            cand_template = Path(template_path)
        elif DCE_DEFAULT_TEMPLATE.exists():
            cand_template = DCE_DEFAULT_TEMPLATE

        if cand_template:
            try:
                self.doc = ezdxf.readfile(str(cand_template))
                self.msp = self.doc.modelspace()
                self.is_dce_template = True
                self.logs.append(f"[OK] Kế thừa DCE Template từ: {cand_template} ({len(self.doc.layers)} layers, {len(self.doc.blocks)} blocks)")
                if clean_template:
                    for e in list(self.msp):
                        self.msp.delete_entity(e)
                    self.logs.append("[OK] Đã làm sạch ModelSpace của template để bắt đầu vẽ bản vẽ mới.")
            except Exception as e:
                self.logs.append(f"[WARN] Nạp template {cand_template} thất bại: {e} — chuyển sang ezdxf.new()")
                self.doc = ezdxf.new(dxfversion="R2010")
                self.msp = self.doc.modelspace()
        else:
            self.doc = ezdxf.new(dxfversion="R2010")
            self.msp = self.doc.modelspace()

        self._ensure_layers()

    def _ensure_layers(self):
        lts = self.doc.layers
        for key, info in LAYERS.items():
            target_name = info["name"] if self.is_dce_template else info["fallback"]
            if target_name not in lts:
                lts.new(name=target_name, dxfattribs={"color": info["color"]})

    def _get_layer_name(self, layer_key: str) -> str:
        info = LAYERS.get(layer_key, {})
        if self.is_dce_template and info.get("name") in self.doc.layers:
            return info["name"]
        return info.get("fallback", "0")

    def _dxf_attr(self, layer_key: str) -> dict:
        return {"layer": self._get_layer_name(layer_key)}

    def draw_beam_section(self, b: float, h: float, cover: float,
                          top_str: str, bot_str: str, stirrup_str: str,
                          ox: float = 0.0, oy: float = 0.0, scale: float = 1.0,
                          anno_scale: float = 10.0) -> dict:
        """Vẽ mặt cắt ngang dầm BTCT chuẩn kỹ thuật."""
        B = b * scale
        H = h * scale
        cv = cover * scale

        # 1. Viền tiết diện dầm
        pts = _rect_pts(ox, oy, B, H)
        self.msp.add_lwpolyline(pts, dxfattribs=self._dxf_attr("outline"), close=True)

        # 2. Cốt đai (stirrup)
        stir_bars = parse_rebar_string(stirrup_str)
        dia_s = stir_bars[0]["dia"] * scale if stir_bars else 8.0 * scale
        stp = [
            (ox + cv, oy + cv),
            (ox + B - cv, oy + cv),
            (ox + B - cv, oy + H - cv),
            (ox + cv, oy + H - cv),
        ]
        self.msp.add_lwpolyline(stp + [stp[0]], dxfattribs=self._dxf_attr("stirrup"), close=True)

        # 3. Thép trên & Thép dưới
        top_bars = parse_rebar_string(top_str)
        bot_bars = parse_rebar_string(bot_str)

        def _place_bars(bars, layer_key, y_center):
            if not bars:
                return []
            total_n = sum(b_["n"] for b_ in bars if b_.get("n"))
            if total_n < 1:
                return []
            dia_max = max(b_["dia"] for b_ in bars if b_.get("n")) * scale
            spacing = (B - 2 * cv - dia_max) / max(total_n - 1, 1) if total_n > 1 else 0
            placed = []
            xi = ox + cv + dia_max / 2.0 if total_n > 1 else ox + B / 2.0
            for b_ in bars:
                for _ in range(b_["n"]):
                    circle = _circle_pts(xi, y_center, b_["dia"] * scale / 2.0)
                    self.msp.add_lwpolyline(circle, dxfattribs=self._dxf_attr(layer_key), close=True)
                    placed.append({"x": xi, "y": y_center, "dia": b_["dia"]})
                    xi += spacing
            return placed

        top_placed = _place_bars(top_bars, "rebar_top", oy + H - cv - dia_s)
        bot_placed = _place_bars(bot_bars, "rebar_bot", oy + cv + dia_s)

        # 4. Kích thước (Dimensions)
        dim_off = 6.0 * anno_scale
        self._add_dim_linear(ox, oy - dim_off, ox + B, oy - dim_off, f"b={int(b)}", "dim", anno_scale=anno_scale)
        self._add_dim_linear(ox + B + dim_off, oy, ox + B + dim_off, oy + H, f"h={int(h)}", "dim", vertical=True, anno_scale=anno_scale)

        # 5. Ghi chú cốt thép
        txt_h = 3.0 * anno_scale
        As_top = rebar_area_mm2(top_bars)
        As_bot = rebar_area_mm2(bot_bars)
        ann = [
            f"TOP: {top_str} (As={As_top:.0f} mm²)",
            f"BOT: {bot_str} (As={As_bot:.0f} mm²)",
            f"STR: {stirrup_str}",
            f"COVER: {cover:.0f} mm",
        ]
        for i, line in enumerate(ann):
            self.msp.add_text(
                line,
                dxfattribs={
                    **self._dxf_attr("text"),
                    "height": txt_h,
                    "insert": (ox + B + 10.0 * anno_scale, oy + H - (i + 1) * (txt_h + 2.0 * anno_scale)),
                },
            )

        self.logs.append({
            "action": "draw_beam_section",
            "b_mm": b, "h_mm": h, "cover_mm": cover,
            "As_top_mm2": As_top, "As_bot_mm2": As_bot,
            "origin": (ox, oy),
            "anno_scale": anno_scale,
        })
        return {
            "As_top_mm2": As_top,
            "As_bot_mm2": As_bot,
            "top_bars": top_placed,
            "bot_bars": bot_placed,
            "top_parsed": top_bars,
            "bot_parsed": bot_bars,
            "stir_parsed": stir_bars,
        }

    def _add_dim_linear(self, x1, y1, x2, y2, label, layer_key, vertical=False, anno_scale: float = 1.0):
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        tick = 5.0 * anno_scale
        self.msp.add_line((x1, y1 - tick), (x1, y1 + tick), dxfattribs=self._dxf_attr(layer_key))
        self.msp.add_line((x2, y2 - tick), (x2, y2 + tick), dxfattribs=self._dxf_attr(layer_key))
        self.msp.add_line((x1, y1), (x2, y2), dxfattribs=self._dxf_attr(layer_key))
        angle = 90.0 if vertical else 0.0
        self.msp.add_text(
            label,
            dxfattribs={
                **self._dxf_attr(layer_key),
                "height": 2.5 * anno_scale,
                "rotation": angle,
                "insert": (mid_x + (2.0 * anno_scale if vertical else 0.0), mid_y + (2.0 * anno_scale if not vertical else 0.0)),
                "halign": 1, "valign": 0,
            },
        )

    def save(self) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        self.doc.saveas(self.output_path)
        return self.output_path


# ─────────────────────────────────────────────────────────────────────────────
# 7. win32com Backend (live AutoCAD)
# ─────────────────────────────────────────────────────────────────────────────

class AutoCADComDrawer:
    """Vẽ trực tiếp vào AutoCAD đang mở qua COM."""

    def __init__(self):
        import win32com.client as wc
        self._acad = wc.GetActiveObject("AutoCAD.Application")
        self._doc  = self._acad.ActiveDocument
        self._msp  = self._doc.ModelSpace
        self.logs  = []
        self._ensure_layers()

    def _ensure_layers(self):
        lts = self._doc.Layers
        for key, info in LAYERS.items():
            layer_name = info["name"]
            try:
                lts.Item(layer_name)
            except Exception:
                layer = lts.Add(layer_name)
                layer.color = info["color"]

    def _pt(self, x, y, z=0.0):
        import win32com.client as wc
        import pythoncom
        return wc.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, z])

    def _pts_array(self, pts):
        import win32com.client as wc
        import pythoncom
        flat = []
        for x, y in pts:
            flat.extend([x, y, 0.0])
        return wc.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)

    def draw_beam_section(self, b, h, cover, top_str, bot_str, stirrup_str,
                          ox=0.0, oy=0.0, scale=1.0, anno_scale=10.0) -> dict:
        B  = b * scale
        H  = h * scale
        cv = cover * scale

        pts = _rect_pts(ox, oy, B, H)
        pl  = self._msp.AddLightWeightPolyline(self._pts_array(pts))
        pl.Layer = LAYERS["outline"]["name"]
        pl.Closed = True

        stir_bars = parse_rebar_string(stirrup_str)
        dia_s = stir_bars[0]["dia"] * scale if stir_bars else 8.0 * scale
        stp = [(ox + cv, oy + cv), (ox + B - cv, oy + cv),
               (ox + B - cv, oy + H - cv), (ox + cv, oy + H - cv),
               (ox + cv, oy + cv)]
        sl = self._msp.AddLightWeightPolyline(self._pts_array(stp))
        sl.Layer = LAYERS["stirrup"]["name"]
        sl.Closed = True

        top_bars = parse_rebar_string(top_str)
        bot_bars = parse_rebar_string(bot_str)

        def _place_bars_acad(bars, layer_name, y_center):
            total_n = sum(b_["n"] for b_ in bars if b_.get("n"))
            if total_n < 1:
                return []
            dia_max = max(b_["dia"] for b_ in bars if b_.get("n")) * scale
            spacing = (B - 2 * cv - dia_max) / max(total_n - 1, 1) if total_n > 1 else 0
            placed = []
            xi = ox + cv + dia_max / 2.0 if total_n > 1 else ox + B / 2.0
            for b_ in bars:
                for _ in range(b_["n"]):
                    c = self._msp.AddCircle(self._pt(xi, y_center), b_["dia"] * scale / 2.0)
                    c.Layer = layer_name
                    placed.append({"x": xi, "y": y_center, "dia": b_["dia"]})
                    xi += spacing
            return placed

        top_placed = _place_bars_acad(top_bars, LAYERS["rebar_top"]["name"], oy + H - cv - dia_s)
        bot_placed = _place_bars_acad(bot_bars, LAYERS["rebar_bot"]["name"], oy + cv + dia_s)

        As_top = rebar_area_mm2(top_bars)
        As_bot = rebar_area_mm2(bot_bars)

        txt_h = 3.0 * anno_scale
        ann = [f"TOP: {top_str} (As={As_top:.0f}mm²)",
               f"BOT: {bot_str} (As={As_bot:.0f}mm²)",
               f"STIRRUP: {stirrup_str}",
               f"COVER: {cover:.0f}mm"]
        for i, line in enumerate(ann):
            t = self._msp.AddText(line, self._pt(ox + B + 10.0 * anno_scale, oy + H - (i + 1) * (txt_h + 2.0 * anno_scale)), txt_h)
            t.Layer = LAYERS["text"]["name"]

        self.logs.append({
            "action": "draw_beam_section_acad",
            "b_mm": b, "h_mm": h, "cover_mm": cover,
            "As_top_mm2": As_top, "As_bot_mm2": As_bot,
        })
        return {
            "As_top_mm2": As_top, "As_bot_mm2": As_bot,
            "top_bars": top_placed, "bot_bars": bot_placed,
            "top_parsed": top_bars, "bot_parsed": bot_bars,
            "stir_parsed": stir_bars,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 8. Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo_draw(b, h, cover, top_str, bot_str, stirrup_str) -> dict:
    top_bars  = parse_rebar_string(top_str)
    bot_bars  = parse_rebar_string(bot_str)
    stir_bars = parse_rebar_string(stirrup_str)
    As_top    = rebar_area_mm2(top_bars)
    As_bot    = rebar_area_mm2(bot_bars)
    return {
        "mode":       "DEMO",
        "section":    f"B{int(b)}x{int(h)}",
        "top_str":    top_str,
        "bot_str":    bot_str,
        "stirrup":    stirrup_str,
        "As_top_mm2": As_top,
        "As_bot_mm2": As_bot,
        "schedule":   [],
        "note":       "Demo mode — không có AutoCAD hoặc ezdxf",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. Public API
# ─────────────────────────────────────────────────────────────────────────────

def draw_beam_section(b: float, h: float, cover: float,
                      top_str: str, bot_str: str, stirrup_str: str,
                      origin=(0.0, 0.0), scale: float = 1.0,
                      anno_scale: float = 10.0,
                      output_path: str = None,
                      template_path: str = None,
                      with_schedule: bool = False,
                      force_demo: bool = False) -> dict:
    """
    Hàm vẽ chính — mặt cắt dầm BTCT + Tùy chọn Bảng thống kê thép DCE.
    - anno_scale: Tỷ lệ phóng đại chữ và block ký hiệu (mặc định 10.0 cho mặt cắt dầm).
    """
    raw_logs = []
    result = {}
    ox, oy = origin
    source = "UNKNOWN"

    if not force_demo:
        if _CAD_BACKEND == "win32com":
            try:
                drawer = AutoCADComDrawer()
                result = drawer.draw_beam_section(b, h, cover, top_str, bot_str, stirrup_str, ox, oy, scale, anno_scale)
                raw_logs += drawer.logs
                source = "AutoCAD_COM_LIVE"
            except Exception as e:
                raw_logs.append(f"[WARN] AutoCAD COM lỗi: {e} — fallback ezdxf")

        if source == "UNKNOWN":
            try:
                out = output_path or "beam_section.dxf"
                drawer = EzdxfDrawer(out, template_path=template_path)
                result = drawer.draw_beam_section(b, h, cover, top_str, bot_str, stirrup_str, ox, oy, scale, anno_scale)

                # Chèn thêm bảng thống kê thép nếu được yêu cầu
                if with_schedule:
                    rebar_items = []
                    # 1. Thép trên (TK1 - thẳng hoặc TK2 - bẻ ke)
                    sh_idx = 1
                    for tb in result.get("top_parsed", []):
                        rebar_items.append({
                            "sh": sh_idx,
                            "dk": tb["dia"],
                            "shape": "TK2",
                            "dims": {"L1": 350, "L2": 5200},
                            "sl": tb["n"],
                            "skc": 1,
                        })
                        sh_idx += 1
                    # 2. Thép dưới (TK2 - bẻ ke)
                    for bb in result.get("bot_parsed", []):
                        rebar_items.append({
                            "sh": sh_idx,
                            "dk": bb["dia"],
                            "shape": "TK2",
                            "dims": {"L1": 350, "L2": 5200},
                            "sl": bb["n"],
                            "skc": 1,
                        })
                        sh_idx += 1
                    # 3. Cốt đai (TK9 - đai kín)
                    for sb in result.get("stir_parsed", []):
                        rebar_items.append({
                            "sh": sh_idx,
                            "dk": sb["dia"],
                            "shape": "TK9",
                            "dims": {
                                "L1": int(b - 2 * cover),
                                "L2": int(h - 2 * cover),
                                "M": int(8 * sb["dia"]),
                            },
                            "sl": 35,
                            "skc": 1,
                        })
                        sh_idx += 1

                    sched_x = ox + b * scale + 15.0 * anno_scale
                    sched_y = oy + h * scale
                    sched_res = insert_dce_rebar_schedule(drawer.msp, rebar_items, insert_pt=(sched_x, sched_y), anno_scale=anno_scale)
                    result["schedule"] = sched_res
                    raw_logs.append(f"[OK] Đã chèn Bảng Thống Kê Thép DCE ({sched_res['rows_count']} hàng, {sched_res['total_weight_kg']} kg, anno_scale={anno_scale})")

                    # Chèn thêm block tên cấu kiện
                    insert_dce_tencaukien(drawer.msp, (ox + (b * scale) / 2.0 - 15.0 * anno_scale, oy - 15.0 * anno_scale), "DẦM D1 (200x400)", 1, anno_scale=anno_scale, scale_str="TL: 1/10")
                    # Chèn thêm cao trình
                    insert_dce_caotrinh(drawer.msp, (ox - 5.0 * anno_scale, oy + h * scale), "+3.600", anno_scale=anno_scale)

                saved = drawer.save()
                raw_logs += drawer.logs
                raw_logs.append(f"[OK] DXF saved: {saved}")
                source = f"ezdxf_DCE_ENGINE → {saved}"
                result["output_file"] = saved
            except Exception as e:
                raw_logs.append(f"[WARN] ezdxf lỗi: {e} — DEMO MODE")
                result = _demo_draw(b, h, cover, top_str, bot_str, stirrup_str)
                source = "DEMO_MODE"
    else:
        result = _demo_draw(b, h, cover, top_str, bot_str, stirrup_str)
        source = "DEMO_MODE"
        raw_logs.append("[INFO] --demo flag: DEMO MODE")

    exec_trace = [str(l) for l in raw_logs]
    calc_logs = [
        {
            "Step": 1,
            "Description": "Tính tổng diện tích tiết diện cốt thép dọc lớp trên As_top",
            "Formula": "As_top = sum(n_i * pi * d_i^2 / 4)",
            "Substitution": f"{top_str} (d_top={[b_['dia'] for b_ in result.get('top_parsed', [])]})",
            "Result": f"{result.get('As_top_mm2', 0):.1f} mm2",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.1.1", "title": "Diện tích cốt thép dọc chịu uốn"}
        },
        {
            "Step": 2,
            "Description": "Tính tổng diện tích tiết diện cốt thép dọc lớp dưới As_bot",
            "Formula": "As_bot = sum(n_i * pi * d_i^2 / 4)",
            "Substitution": f"{bot_str} (d_bot={[b_['dia'] for b_ in result.get('bot_parsed', [])]})",
            "Result": f"{result.get('As_bot_mm2', 0):.1f} mm2",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.1.1", "title": "Diện tích cốt thép dọc chịu uốn"}
        },
        {
            "Step": 3,
            "Description": "Tính chiều dài 1 thanh cốt đai kín chữ nhật TK9",
            "Formula": "sumL = 2 * (L1 + L2) + 2 * M",
            "Substitution": f"2 * ({int(b - 2*cover)} + {int(h - 2*cover)}) + 2 * {int(8 * (result.get('stir_parsed', [{}])[0].get('dia', 8.0)))}",
            "Result": f"{2 * (int(b - 2*cover) + int(h - 2*cover)) + 2 * int(8 * (result.get('stir_parsed', [{}])[0].get('dia', 8.0)))} mm",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.2", "title": "Cấu tạo cốt đai kín và móc neo"}
        }
    ]

    return {
        **result,
        "Execution_Trace":  exec_trace,
        "Calculation_Logs": calc_logs,
        "Standard_Method":  "TCVN 5574:2018 + DCE Pro Form 2.dxf Blocks (TK1..TK44)",
        "source":           source,
        "generated_at":     datetime.now().isoformat() + "Z",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 10. Engine Vẽ Mặt Cắt Dọc Dầm (Beam Longitudinal Elevation)
# ─────────────────────────────────────────────────────────────────────────────

def draw_beam_elevation(
    span_L: float = 4000.0,
    h: float = 400.0,
    b: float = 200.0,
    col_w: float = 300.0,
    cover: float = 25.0,
    top_str: str = "2D16",
    bot_str: str = "2D20",
    stirrup_str: str = "D8@100/200",
    beam_name: str = "D1 (200x400)",
    axis_start: str = "1",
    axis_end: str = "2",
    elevation_str: str = "+3.600",
    origin=(0.0, 0.0),
    scale: float = 1.0,
    anno_scale: float = 20.0,
    output_path: str = None,
    template_path: str = None,
    with_schedule: bool = False,
    force_demo: bool = False,
) -> dict:
    """
    Vẽ mặt cắt dọc dầm BTCT hoàn chỉnh:
    - 2 cột 2 đầu (bề rộng col_w).
    - Thân dầm nhịp L, chiều cao h.
    - Thép trên chạy suốt + bẻ ke neo vào 2 cột.
    - Thép dưới chạy suốt + bẻ ke neo vào 2 cột.
    - Phân bố cốt đai: L/4 ở 2 gối đai mau (100mm), L/2 giữa nhịp đai thưa (200mm).
    - Hệ thống dim: nhịp L, khoảng cách trục, các đoạn phân bố đai, chiều cao dầm.
    - Ký hiệu trục Dce_KhTenTruc, cao trình Dce_CaoTrinh, tên cấu kiện *U4 / TenCauKien.
    - anno_scale: Tỷ lệ chữ và block ký hiệu (mặc định 20.0 cho tỷ lệ 1:20).
    """
    ox, oy = origin
    out = output_path or "beam_elevation.dxf"
    drawer = EzdxfDrawer(out, template_path=template_path)
    msp = drawer.msp
    raw_logs = drawer.logs

    L = span_L * scale
    H = h * scale
    B = b * scale
    C_w = col_w * scale
    cv = cover * scale

    # 1. Viền thân dầm (0,0) -> (L, H)
    pts_beam = [(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)]
    msp.add_lwpolyline(pts_beam, dxfattribs=drawer._dxf_attr("outline"), close=True)

    # 2. Hai cột hai đầu
    # Cột trái: từ (-C_w, -150) -> (0, H + 150)
    pts_col_left = [
        (ox - C_w, oy - 150.0 * scale),
        (ox, oy - 150.0 * scale),
        (ox, oy + H + 150.0 * scale),
        (ox - C_w, oy + H + 150.0 * scale),
    ]
    msp.add_lwpolyline(pts_col_left, dxfattribs=drawer._dxf_attr("outline"), close=True)

    # Cột phải: từ (L, -150) -> (L + C_w, H + 150)
    pts_col_right = [
        (ox + L, oy - 150.0 * scale),
        (ox + L + C_w, oy - 150.0 * scale),
        (ox + L + C_w, oy + H + 150.0 * scale),
        (ox + L, oy + H + 150.0 * scale),
    ]
    msp.add_lwpolyline(pts_col_right, dxfattribs=drawer._dxf_attr("outline"), close=True)

    # 3. Trục tim cột (Centerlines)
    # Tim cột trái tại x = -C_w / 2
    x_axis_left = ox - C_w / 2.0
    ext_axis_top = H + 12.0 * anno_scale
    ext_axis_bot = 10.0 * anno_scale
    msp.add_line((x_axis_left, oy - ext_axis_bot), (x_axis_left, oy + ext_axis_top), dxfattribs=drawer._dxf_attr("center"))
    insert_dce_truc(msp, (x_axis_left, oy + ext_axis_top + 2.0 * anno_scale), axis_start, anno_scale=anno_scale)

    # Tim cột phải tại x = L + C_w / 2
    x_axis_right = ox + L + C_w / 2.0
    msp.add_line((x_axis_right, oy - ext_axis_bot), (x_axis_right, oy + ext_axis_top), dxfattribs=drawer._dxf_attr("center"))
    insert_dce_truc(msp, (x_axis_right, oy + ext_axis_top + 2.0 * anno_scale), axis_end, anno_scale=anno_scale)

    # 4. Cốt thép dọc
    # Thép trên: chạy suốt từ x = -C_w + cv đến L + C_w - cv, bẻ ke 30d xuống cột
    top_bars = parse_rebar_string(top_str)
    dia_top = top_bars[0]["dia"] if top_bars else 16.0
    hook_top = min(30.0 * dia_top * scale, H - 2 * cv)

    y_top = oy + H - cv
    pts_top_rebar = [
        (ox - C_w + cv, y_top - hook_top),
        (ox - C_w + cv, y_top),
        (ox + L + C_w - cv, y_top),
        (ox + L + C_w - cv, y_top - hook_top),
    ]
    msp.add_lwpolyline(pts_top_rebar, dxfattribs=drawer._dxf_attr("rebar_top"))

    # Thép dưới: chạy suốt từ x = -C_w + cv đến L + C_w - cv, bẻ ke 30d lên cột
    bot_bars = parse_rebar_string(bot_str)
    dia_bot = bot_bars[0]["dia"] if bot_bars else 20.0
    hook_bot = min(30.0 * dia_bot * scale, H - 2 * cv)

    y_bot = oy + cv
    pts_bot_rebar = [
        (ox - C_w + cv, y_bot + hook_bot),
        (ox - C_w + cv, y_bot),
        (ox + L + C_w - cv, y_bot),
        (ox + L + C_w - cv, y_bot + hook_bot),
    ]
    msp.add_lwpolyline(pts_bot_rebar, dxfattribs=drawer._dxf_attr("rebar_bot"))

    # 5. Phân bố cốt đai dọc dầm (L/4 ở 2 gối đai mau s=100, giữa nhịp s=200)
    stir_y1 = y_bot
    stir_y2 = y_top
    zone_gối = L / 4.0

    # Vùng gối trái (0 -> L/4)
    x_s = ox + 50.0 * scale
    while x_s <= ox + zone_gối:
        msp.add_line((x_s, stir_y1), (x_s, stir_y2), dxfattribs=drawer._dxf_attr("stirrup"))
        x_s += 100.0 * scale

    # Vùng giữa nhịp (L/4 -> 3L/4)
    x_s = ox + zone_gối + 100.0 * scale
    while x_s <= ox + 3 * zone_gối:
        msp.add_line((x_s, stir_y1), (x_s, stir_y2), dxfattribs=drawer._dxf_attr("stirrup"))
        x_s += 200.0 * scale

    # Vùng gối phải (3L/4 -> L)
    x_s = ox + 3 * zone_gối + 50.0 * scale
    while x_s <= ox + L - 50.0 * scale:
        msp.add_line((x_s, stir_y1), (x_s, stir_y2), dxfattribs=drawer._dxf_attr("stirrup"))
        x_s += 100.0 * scale

    # 6. Kích thước (Dimensions)
    # Dim 1: Các vùng cốt đai L/4, L/2, L/4
    dim_y1 = oy - 3.0 * anno_scale
    drawer._add_dim_linear(ox, dim_y1, ox + zone_gối, dim_y1, f"L/4={int(span_L/4)}", "dim", anno_scale=anno_scale)
    drawer._add_dim_linear(ox + zone_gối, dim_y1, ox + 3 * zone_gối, dim_y1, f"L/2={int(span_L/2)}", "dim", anno_scale=anno_scale)
    drawer._add_dim_linear(ox + 3 * zone_gối, dim_y1, ox + L, dim_y1, f"L/4={int(span_L/4)}", "dim", anno_scale=anno_scale)

    # Dim 2: Nhịp thông thủy L
    dim_y2 = oy - 6.0 * anno_scale
    drawer._add_dim_linear(ox, dim_y2, ox + L, dim_y2, f"L={int(span_L)}", "dim", anno_scale=anno_scale)

    # Dim 3: Tim trục đến tim trục
    dim_y3 = oy - 9.0 * anno_scale
    drawer._add_dim_linear(x_axis_left, dim_y3, x_axis_right, dim_y3, f"L_trục={int(span_L + col_w)}", "dim", anno_scale=anno_scale)

    # Ghi chú ký hiệu cốt đai
    txt_stir_h = 2.5 * anno_scale
    msp.add_text(r"%%c8a100", dxfattribs={**drawer._dxf_attr("text"), "height": txt_stir_h, "insert": (ox + zone_gối / 2.0 - 20, oy + H + 1.0 * anno_scale)})
    msp.add_text(r"%%c8a200", dxfattribs={**drawer._dxf_attr("text"), "height": txt_stir_h, "insert": (ox + L / 2.0 - 20, oy + H + 1.0 * anno_scale)})
    msp.add_text(r"%%c8a100", dxfattribs={**drawer._dxf_attr("text"), "height": txt_stir_h, "insert": (ox + 3.5 * zone_gối - 20, oy + H + 1.0 * anno_scale)})

    # Ký hiệu cao trình đỉnh dầm
    insert_dce_caotrinh(msp, (ox - C_w / 2.0, oy + H), elevation_str, anno_scale=anno_scale)
    # Ký hiệu tên cấu kiện
    insert_dce_tencaukien(msp, (ox + L / 2.0 - 10.0 * anno_scale, oy - 12.0 * anno_scale), beam_name, 1, anno_scale=anno_scale, scale_str="TL: 1/20")

    # 7. Chèn thêm bảng thống kê thép nếu được yêu cầu
    sched_res = None
    if with_schedule:
        # Thép dọc bẻ ke 2 đầu: hình dạng chuẩn TK4 (L1=hook, L2=thân dầm+cột, L3=hook)
        rebar_items = [
            {
                "sh": 1,
                "dk": dia_top,
                "shape": "TK4",
                "dims": {
                    "L1": int(hook_top),
                    "L2": int(span_L + 2 * col_w - 2 * cover),
                    "L3": int(hook_top)
                },
                "sl": top_bars[0]["n"] if top_bars else 2,
                "skc": 1
            },
            {
                "sh": 2,
                "dk": dia_bot,
                "shape": "TK4",
                "dims": {
                    "L1": int(hook_bot),
                    "L2": int(span_L + 2 * col_w - 2 * cover),
                    "L3": int(hook_bot)
                },
                "sl": bot_bars[0]["n"] if bot_bars else 2,
                "skc": 1
            },
            {
                "sh": 3,
                "dk": 8.0,
                "shape": "TK9",
                "dims": {
                    "L1": int(b - 2 * cover),
                    "L2": int(h - 2 * cover),
                    "M": 64
                },
                "sl": int(span_L / 150.0) + 1,
                "skc": 1
            },
        ]
        sched_x = ox + L + C_w + 5.0 * anno_scale
        sched_y = oy + H + 5.0 * anno_scale
        sched_res = insert_dce_rebar_schedule(msp, rebar_items, insert_pt=(sched_x, sched_y), anno_scale=anno_scale)
        raw_logs.append(f"[OK] Đã đính kèm Bảng Thống Kê Thép cho Mặt cắt dọc dầm ({sched_res['rows_count']} hàng, anno_scale={anno_scale})")

    saved = drawer.save()
    raw_logs.append(f"[OK] Bản vẽ Mặt cắt dọc dầm đã xuất ra: {saved}")

    exec_trace = [str(l) for l in raw_logs]
    calc_logs = [
        {
            "Step": 1,
            "Description": "Xác định chiều dài neo cốt thép dọc vào nút khung cột (hook)",
            "Formula": "L_hook = min(30 * d, H_dam - 2 * cover)",
            "Substitution": f"min(30 * {dia_top}, {h} - 2 * {cover})",
            "Result": f"{hook_top:.0f} mm",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.1", "title": "Chiều dài neo cốt thép dầm trong bê tông"}
        },
        {
            "Step": 2,
            "Description": "Tính tổng chiều dài thanh thép dọc bẻ ke 2 đầu TK4",
            "Formula": "sumL = L1 + L2 + L3",
            "Substitution": f"{int(hook_top)} + {int(span_L + 2 * col_w - 2 * cover)} + {int(hook_top)}",
            "Result": f"{2 * int(hook_top) + int(span_L + 2 * col_w - 2 * cover)} mm",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.1", "title": "Quy cách thanh bẻ ke neo 2 đầu"}
        },
        {
            "Step": 3,
            "Description": "Phân chia các vùng bố trí cốt đai chịu cắt dầm (gối L/4, nhịp L/2)",
            "Formula": "L_goi = L / 4, L_nhip = L / 2",
            "Substitution": f"{span_L} / 4 = {span_L/4:.0f} mm, {span_L} / 2 = {span_L/2:.0f} mm",
            "Result": f"L_goi = {span_L/4:.0f} mm (s=100), L_nhip = {span_L/2:.0f} mm (s=200)",
            "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.2", "title": "Bố trí cốt đai dầm chịu lực cắt"}
        }
    ]

    return {
        "status": "SUCCESS",
        "mode": "beam_elevation",
        "span_L_mm": span_L,
        "h_mm": h,
        "b_mm": b,
        "output_file": saved,
        "schedule": sched_res,
        "Execution_Trace": exec_trace,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "TCVN 5574:2018 + TCVN 196:2012 (Mặt cắt dọc cấu kiện BTCT)",
        "generated_at": datetime.now().isoformat() + "Z",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 11. Engine Vẽ Mặt Bằng Kết Cấu (Structural Framing Plan)
# ─────────────────────────────────────────────────────────────────────────────

def draw_framing_plan(
    grids_x: list = None,
    grids_y: list = None,
    col_w: float = 300.0,
    col_h: float = 300.0,
    beam_b: float = 200.0,
    beam_h: float = 400.0,
    beam_name: str = "D1 (200x400)",
    elevation_str: str = "+3.600",
    origin=(0.0, 0.0),
    scale: float = 1.0,
    anno_scale: float = 50.0,
    output_path: str = None,
    template_path: str = None,
    force_demo: bool = False,
) -> dict:
    """
    Vẽ mặt bằng kết cấu dầm sàn BTCT hoàn chỉnh:
    - Hệ lưới trục tọa độ X (1, 2, 3...) và Y (A, B, C...).
    - Bong bóng ký hiệu trục Dce_KhTenTruc ở 2 đầu lưới.
    - Cột BTCT tại các giao điểm trục.
    - Hệ dầm khung chính/phụ nối các cột.
    - Ghi chú tên dầm *U4 / TenCauKien và cao trình sàn Dce_CaoTrinh.
    - Chuỗi kích thước chi tiết và kích thước tổng thể.
    - anno_scale: Tỷ lệ phóng đại chữ và block ký hiệu (mặc định 50.0 cho tỷ lệ 1:50).
    """
    ox, oy = origin
    out = output_path or "framing_plan.dxf"
    drawer = EzdxfDrawer(out, template_path=template_path)
    msp = drawer.msp
    raw_logs = drawer.logs

    # Lưới trục mặc định nếu không truyền
    if grids_x is None:
        grids_x = [{"name": "1", "x": 0.0}, {"name": "2", "x": 4000.0}, {"name": "3", "x": 8000.0}]
    if grids_y is None:
        grids_y = [{"name": "A", "y": 0.0}, {"name": "B", "y": 4500.0}, {"name": "C", "y": 9000.0}]

    cw = col_w * scale
    ch = col_h * scale
    bb = beam_b * scale

    xs = [ox + g["x"] * scale for g in grids_x]
    ys = [oy + g["y"] * scale for g in grids_y]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    extension = 20.0 * anno_scale

    # 1. Vẽ các đường lưới trục (Grid lines) & Bong bóng trục
    # Trục đứng (phương Y, mang tên 1, 2, 3...)
    for gx, g_info in zip(xs, grids_x):
        y1 = min_y - extension
        y2 = max_y + extension
        msp.add_line((gx, y1), (gx, y2), dxfattribs=drawer._dxf_attr("center"))
        # Bong bóng 2 đầu
        insert_dce_truc(msp, (gx, y1 - 4.0 * anno_scale), g_info["name"], anno_scale=anno_scale)
        insert_dce_truc(msp, (gx, y2 + 4.0 * anno_scale), g_info["name"], anno_scale=anno_scale)

    # Trục ngang (phương X, mang tên A, B, C...)
    for gy, g_info in zip(ys, grids_y):
        x1 = min_x - extension
        x2 = max_x + extension
        msp.add_line((x1, gy), (x2, gy), dxfattribs=drawer._dxf_attr("center"))
        # Bong bóng 2 đầu
        insert_dce_truc(msp, (x1 - 4.0 * anno_scale, gy), g_info["name"], anno_scale=anno_scale)
        insert_dce_truc(msp, (x2 + 4.0 * anno_scale, gy), g_info["name"], anno_scale=anno_scale)

    # 2. Vẽ dầm nối giữa các trục
    txt_beam_h = 2.5 * anno_scale
    # Dầm ngang (chạy theo trục X nối giữa các cột)
    for gy in ys:
        for i in range(len(xs) - 1):
            x_start = xs[i] + cw / 2.0
            x_end = xs[i + 1] - cw / 2.0
            # Viền trên và viền dưới của dầm
            msp.add_line((x_start, gy + bb / 2.0), (x_end, gy + bb / 2.0), dxfattribs=drawer._dxf_attr("outline"))
            msp.add_line((x_start, gy - bb / 2.0), (x_end, gy - bb / 2.0), dxfattribs=drawer._dxf_attr("outline"))
            # Tên dầm
            msp.add_text(beam_name, dxfattribs={**drawer._dxf_attr("text"), "height": txt_beam_h, "insert": ((x_start + x_end) / 2.0 - 2.0 * anno_scale, gy + 0.5 * anno_scale)})

    # Dầm dọc (chạy theo trục Y nối giữa các cột)
    for gx in xs:
        for j in range(len(ys) - 1):
            y_start = ys[j] + ch / 2.0
            y_end = ys[j + 1] - ch / 2.0
            msp.add_line((gx - bb / 2.0, y_start), (gx - bb / 2.0, y_end), dxfattribs=drawer._dxf_attr("outline"))
            msp.add_line((gx + bb / 2.0, y_start), (gx + bb / 2.0, y_end), dxfattribs=drawer._dxf_attr("outline"))
            # Tên dầm xoay 90 độ
            msp.add_text(beam_name, dxfattribs={**drawer._dxf_attr("text"), "height": txt_beam_h, "rotation": 90.0, "insert": (gx - 0.5 * anno_scale, (y_start + y_end) / 2.0 - 2.0 * anno_scale)})

    # 3. Vẽ Cột tại các giao điểm trục (x_i, y_j)
    for gx in xs:
        for gy in ys:
            pts_col = [
                (gx - cw / 2.0, gy - ch / 2.0),
                (gx + cw / 2.0, gy - ch / 2.0),
                (gx + cw / 2.0, gy + ch / 2.0),
                (gx - cw / 2.0, gy + ch / 2.0),
            ]
            msp.add_lwpolyline(pts_col, dxfattribs=drawer._dxf_attr("outline"), close=True)

    # 4. Kích thước (Dimensions)
    # Dim X (ở phía dưới): từng bước cột + tổng
    dim_y_bot1 = min_y - extension + 6.0 * anno_scale
    for i in range(len(xs) - 1):
        drawer._add_dim_linear(xs[i], dim_y_bot1, xs[i + 1], dim_y_bot1, f"{int(grids_x[i+1]['x'] - grids_x[i]['x'])}", "dim", anno_scale=anno_scale)
    dim_y_bot2 = min_y - extension + 3.0 * anno_scale
    drawer._add_dim_linear(min_x, dim_y_bot2, max_x, dim_y_bot2, f"{int(grids_x[-1]['x'] - grids_x[0]['x'])}", "dim", anno_scale=anno_scale)

    # Dim Y (ở phía bên trái): từng bước cột + tổng
    dim_x_left1 = min_x - extension + 6.0 * anno_scale
    for j in range(len(ys) - 1):
        drawer._add_dim_linear(dim_x_left1, ys[j], dim_x_left1, ys[j + 1], f"{int(grids_y[j+1]['y'] - grids_y[j]['y'])}", "dim", vertical=True, anno_scale=anno_scale)
    dim_x_left2 = min_x - extension + 3.0 * anno_scale
    drawer._add_dim_linear(dim_x_left2, min_y, dim_x_left2, max_y, f"{int(grids_y[-1]['y'] - grids_y[0]['y'])}", "dim", vertical=True, anno_scale=anno_scale)

    # 5. Ký hiệu cao trình sàn & Tiêu đề mặt bằng
    insert_dce_caotrinh(msp, ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0), elevation_str, anno_scale=anno_scale)
    msp.add_text(f"CAO TRÌNH SÀN: {elevation_str}", dxfattribs={**drawer._dxf_attr("text"), "height": 3.0 * anno_scale, "insert": ((min_x + max_x) / 2.0 - 5.0 * anno_scale, (min_y + max_y) / 2.0 - 2.0 * anno_scale)})

    # Tiêu đề mặt bằng
    msp.add_text("MẶT BẰNG KẾT CẤU DẦM SÀN", dxfattribs={**drawer._dxf_attr("text"), "height": 5.0 * anno_scale, "insert": ((min_x + max_x) / 2.0 - 10.0 * anno_scale, min_y - extension - 8.0 * anno_scale)})

    saved = drawer.save()
    raw_logs.append(f"[OK] Bản vẽ Mặt bằng kết cấu đã xuất ra: {saved}")

    exec_trace = [str(l) for l in raw_logs]
    calc_logs = [
        {
            "Step": 1,
            "Description": "Xác định kích thước chiều dài nhịp khung theo phương X",
            "Formula": "Lx = max(Grid_X) - min(Grid_X)",
            "Substitution": f"{max(g['x'] for g in grids_x)} - {min(g['x'] for g in grids_x)}",
            "Result": f"{max(g['x'] for g in grids_x) - min(g['x'] for g in grids_x):.0f} mm",
            "Citation": {"standard": "TCVN 196:2012", "clause": "Điều 4", "title": "Bản vẽ mặt bằng kết cấu công trình"}
        },
        {
            "Step": 2,
            "Description": "Xác định kích thước chiều dài nhịp khung theo phương Y",
            "Formula": "Ly = max(Grid_Y) - min(Grid_Y)",
            "Substitution": f"{max(g['y'] for g in grids_y)} - {min(g['y'] for g in grids_y)}",
            "Result": f"{max(g['y'] for g in grids_y) - min(g['y'] for g in grids_y):.0f} mm",
            "Citation": {"standard": "TCVN 196:2012", "clause": "Điều 4", "title": "Bản vẽ mặt bằng kết cấu công trình"}
        }
    ]

    return {
        "status": "SUCCESS",
        "mode": "framing_plan",
        "grids_x_count": len(grids_x),
        "grids_y_count": len(grids_y),
        "columns_count": len(grids_x) * len(grids_y),
        "output_file": saved,
        "Execution_Trace": exec_trace,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "TCVN 5574:2018 + TCVN 196:2012 (Mặt bằng kết cấu công trình)",
        "generated_at": datetime.now().isoformat() + "Z",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(description="AutoCAD & DCE Pro Direct Drawing Bridge")
    parser.add_argument("--mode", default="beam_section", choices=["beam_section", "beam_elevation", "framing_plan", "rebar_schedule"], help="Chế độ vẽ")
    parser.add_argument("--b", type=float, default=200.0, help="Chiều rộng b (mm)")
    parser.add_argument("--h", type=float, default=400.0, help="Chiều cao h (mm)")
    parser.add_argument("--span", type=float, default=4000.0, help="Chiều dài nhịp dầm (mm)")
    parser.add_argument("--col-w", type=float, default=300.0, help="Bề rộng cột đỡ (mm)")
    parser.add_argument("--col-h", type=float, default=300.0, help="Chiều cao cột đỡ (mm)")
    parser.add_argument("--cover", type=float, default=25.0, help="Chiều dày bê tông bảo vệ (mm)")
    parser.add_argument("--top", default="2D16", help="Thép trên VD '2D16' hoặc '2D25+1D22'")
    parser.add_argument("--bot", default="2D20", help="Thép dưới VD '2D20'")
    parser.add_argument("--stirrup", default="D8@100/200", help="Cốt đai VD 'D8@100/200'")
    parser.add_argument("--name", default="D1 (200x400)", help="Tên cấu kiện")
    parser.add_argument("--elevation", default="+3.600", help="Cao trình cấu kiện")
    parser.add_argument("--origin", default="0,0", help="Tọa độ góc dưới-trái 'x,y'")
    parser.add_argument("--scale", type=float, default=1.0, help="Tỷ lệ vẽ hình học")
    parser.add_argument("--anno-scale", type=float, default=None, help="Tỷ lệ chữ và block ký hiệu (mặc định theo từng mode)")
    parser.add_argument("--template", default=None, help="Đường dẫn file DXF template (mặc định Form 2.dxf)")
    parser.add_argument("--schedule", action="store_true", help="Chèn Bảng Thống Kê Thép chuẩn DCE TK1..TK44")
    parser.add_argument("--schedule-items", type=str, default=None, help="Chuỗi JSON danh sách thanh thép cho mode rebar_schedule")
    parser.add_argument("--grids-x", type=str, default=None, help="JSON list grids X: '[{\"name\":\"1\",\"x\":0},{\"name\":\"2\",\"x\":4000}]'")
    parser.add_argument("--grids-y", type=str, default=None, help="JSON list grids Y: '[{\"name\":\"A\",\"y\":0},{\"name\":\"B\",\"y\":5000}]'")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn file DXF output")
    parser.add_argument("--demo", action="store_true", help="Chạy Demo mode")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()

    ox, oy = (float(v) for v in args.origin.split(","))

    if args.mode == "beam_section":
        anno_sc = args.anno_scale if args.anno_scale is not None else 10.0
        result = draw_beam_section(
            b=args.b, h=args.h, cover=args.cover,
            top_str=args.top, bot_str=args.bot, stirrup_str=args.stirrup,
            origin=(ox, oy), scale=args.scale, anno_scale=anno_sc,
            output_path=args.output,
            template_path=args.template,
            with_schedule=args.schedule,
            force_demo=args.demo,
        )
        print(json.dumps(result, ensure_ascii=False, indent=args.indent))

    elif args.mode == "beam_elevation":
        anno_sc = args.anno_scale if args.anno_scale is not None else 20.0
        result = draw_beam_elevation(
            span_L=args.span, h=args.h, b=args.b, col_w=args.col_w, cover=args.cover,
            top_str=args.top, bot_str=args.bot, stirrup_str=args.stirrup,
            beam_name=args.name, elevation_str=args.elevation,
            origin=(ox, oy), scale=args.scale, anno_scale=anno_sc,
            output_path=args.output, template_path=args.template,
            with_schedule=args.schedule, force_demo=args.demo,
        )
        print(json.dumps(result, ensure_ascii=False, indent=args.indent))

    elif args.mode == "framing_plan":
        gx = json.loads(args.grids_x) if args.grids_x else None
        gy = json.loads(args.grids_y) if args.grids_y else None
        anno_sc = args.anno_scale if args.anno_scale is not None else 50.0
        result = draw_framing_plan(
            grids_x=gx, grids_y=gy, col_w=args.col_w, col_h=args.col_h,
            beam_b=args.b, beam_h=args.h, beam_name=args.name, elevation_str=args.elevation,
            origin=(ox, oy), scale=args.scale, anno_scale=anno_sc,
            output_path=args.output, template_path=args.template, force_demo=args.demo,
        )
        print(json.dumps(result, ensure_ascii=False, indent=args.indent))

    elif args.mode == "rebar_schedule":
        items = []
        if args.schedule_items:
            items = json.loads(args.schedule_items)
        else:
            items = [
                {"sh": 1, "dk": 25, "shape": "TK1", "dims": {"L": 5800}, "sl": 3, "skc": 1},
                {"sh": 2, "dk": 22, "shape": "TK2", "dims": {"L1": 350, "L2": 4500}, "sl": 2, "skc": 1},
                {"sh": 3, "dk": 10, "shape": "TK9", "dims": {"L1": 240, "L2": 540, "M": 80}, "sl": 30, "skc": 1},
            ]
        anno_sc = args.anno_scale if args.anno_scale is not None else 1.0
        out_f = args.output or "rebar_schedule.dxf"
        drawer = EzdxfDrawer(out_f, template_path=args.template)
        sched_res = insert_dce_rebar_schedule(drawer.msp, items, insert_pt=(ox, oy), anno_scale=anno_sc)
        drawer.save()
        print(json.dumps(sched_res, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    _cli()
