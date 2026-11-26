# -*- coding: utf-8 -*-
"""
cad_block_adapters.py — Native DCE Block & TitleBlock Attribute Adapters
=========================================================================

Implements Phase 1 & Phase 2 block architecture agreed between Gemini and Claude:
1. Agent-owned XData tagging (`DCE_AGENT_OWNED`) so Open Form Mode never deletes
   user shell geometry, company logos, or TitleBlock edits.
2. Parametric named TitleBlock blocks with real `ATTDEF`s:
     - `DCE_TITLEBLOCK_A3`: Matches canonical A3 vertical right Title Block
     - `DCE_TITLEBLOCK_A1`: Matches A1 right-sidebar lower Title Block
   Updates existing TitleBlock `INSERT` attributes cleanly in-place, preserving
   all user-edited fonts, positions, borders, logos, and custom company tags.
3. Native DCE member & symbol block adapters (never distorting ATTRIB text):
     - Grid bubble: `Dce_KhTenTruc` (`TRUC`) with native layer colors (no dark true_color override)
     - Piles: `DCE_Pile_SQ_<KIND>_<SIZE>` / `DCE_Pile_CIR_D<SIZE>` with `ATTDEF` (`PILE_ID`, `D`, `L`, `Q`)
     - Columns: Geometry-only named block `DCE_COL_<KIND>_<B>x<H>` (`xscale=yscale=1.0`)
                + optional separated `TenCauKien` annotation `INSERT`
     - Elevations / Slabs / Plan Headers: `Dce_CaoTrinh`, `DCE_Slab tag`, `DCE_Plan header 1`
"""

from __future__ import annotations

import math
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf
from ezdxf.enums import TextEntityAlignment

from cad_form_contract import AGENT_OWNED_APPID, DEFAULT_ALLOWLIST_TITLE_TAGS


# ---------------------------------------------------------------------------
# XDATA AGENT-OWNED LIFECYCLE HELPERS
# ---------------------------------------------------------------------------

def ensure_agent_owned_appid(doc: ezdxf.document.Drawing) -> None:
    """Register `DCE_AGENT_OWNED` AppID cleanly in the DXF document."""
    try:
        if AGENT_OWNED_APPID not in doc.appids:
            doc.appids.add(AGENT_OWNED_APPID)
    except Exception:
        pass


def mark_agent_owned(entity: Any, role: str = "GEOM") -> Any:
    """Tag an entity with `DCE_AGENT_OWNED` XData so Open Form mode can rebuild cleanly."""
    if entity is None:
        return entity
    try:
        if entity.has_xdata(AGENT_OWNED_APPID):
            return entity
        doc = getattr(entity, "doc", None)
        if doc is not None:
            ensure_agent_owned_appid(doc)
        entity.set_xdata(AGENT_OWNED_APPID, [(1000, str(role))])
    except Exception:
        pass
    return entity


def snapshot_msp_handles(msp) -> set:
    """Return current set of entity handles in ModelSpace."""
    out = set()
    for e in msp:
        try:
            out.add(e.dxf.handle)
        except Exception:
            pass
    return out


def mark_new_entities_owned(msp, before_handles: set, role: str = "GEOM") -> int:
    """Tag all entities added to ModelSpace after `before_handles` with XData."""
    doc = getattr(msp, "doc", None)
    if doc is not None:
        ensure_agent_owned_appid(doc)
    count = 0
    for ent in msp:
        try:
            h = ent.dxf.handle
            if h not in before_handles:
                if not ent.has_xdata(AGENT_OWNED_APPID):
                    ent.set_xdata(AGENT_OWNED_APPID, [(1000, str(role))])
                count += 1
        except Exception:
            pass
    return count


def purge_agent_owned_entities(doc: ezdxf.document.Drawing, msp=None) -> int:
    """Delete ONLY entities previously created by Agent (`DCE_AGENT_OWNED`), keeping user edits 100%."""
    if msp is None:
        msp = doc.modelspace()
    removed = 0
    for ent in list(msp):
        try:
            if ent.has_xdata(AGENT_OWNED_APPID):
                msp.delete_entity(ent)
                removed += 1
        except Exception:
            pass
    return removed


# ---------------------------------------------------------------------------
# COMMON DRAWING PRIMITIVES FOR BLOCK DEFINITIONS
# ---------------------------------------------------------------------------

def _add_attdef_to_block(
    blk,
    tag: str,
    default: str,
    x: float,
    y: float,
    height: float,
    layer: str = "DCE_TKT-TEXT",
    style: str = "Dce_Text",
    align: TextEntityAlignment = TextEntityAlignment.MIDDLE_CENTER,
    prompt: str = "",
    invisible: bool = False,
    width: float = 1.0,
):
    attribs: Dict[str, Any] = {
        "layer": layer,
        "height": float(height),
        "style": style,
        "color": 256,
        "width": float(width),
        "prompt": prompt or tag,
    }
    if align == TextEntityAlignment.MIDDLE_CENTER:
        attribs["halign"] = 1
        attribs["valign"] = 2
        attribs["align_point"] = (float(x), float(y))
    elif align == TextEntityAlignment.MIDDLE_LEFT:
        attribs["halign"] = 0
        attribs["valign"] = 2
        attribs["align_point"] = (float(x), float(y))
    att = blk.add_attdef(tag, insert=(float(x), float(y)), text=str(default), dxfattribs=attribs)
    if invisible:
        att.is_invisible = True
    try:
        att.set_placement((float(x), float(y)), align=align)
    except Exception:
        pass
    return att


def _add_static_text_to_block(
    blk,
    text: str,
    x: float,
    y: float,
    height: float,
    layer: str = "DCE_TKT-TEXT",
    style: str = "Dce_Text",
    align: TextEntityAlignment = TextEntityAlignment.MIDDLE_CENTER,
):
    t = blk.add_text(
        str(text),
        height=float(height),
        dxfattribs={"layer": layer, "style": style, "color": 256},
    )
    t.set_placement((float(x), float(y)), align=align)
    return t


def _ensure_dce_text_style(doc: ezdxf.document.Drawing, style_name: str = "Dce_Text") -> None:
    if style_name not in doc.styles:
        try:
            doc.styles.add(style_name, font="arial.ttf")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# TITLEBLOCK ATTDEF DEFINITIONS (A3 & A1) + IN-PLACE ATTRIB UPDATE
# ---------------------------------------------------------------------------

def ensure_titleblock_a3_definition(
    doc: ezdxf.document.Drawing,
    block_name: str = "DCE_TITLEBLOCK_A3",
) -> Any:
    """Create canonical `DCE_TITLEBLOCK_A3` named block with real ATTDEFs if missing."""
    if block_name in doc.blocks:
        return doc.blocks.get(block_name)

    _ensure_dce_text_style(doc, "Dce_Text")
    blk = doc.blocks.new(name=block_name, base_point=(0.0, 0.0))

    tb_x0, tb_x1 = 36858.0, 41821.0
    cx_tb = (tb_x0 + tb_x1) / 2.0

    # Outer & inner borders are left in ModelSpace frame shell OR included neatly here.
    # TitleBlock block owns the right vertical divider and all cells from tb_x0..tb_x1.
    blk.add_line((tb_x0, 212.0), (tb_x0, 29488.0), dxfattribs={"layer": "DCE_Frame", "color": 256})
    h_ys = [
        955.0, 1693.0, 3012.0, 3662.0, 4062.0, 5211.0, 6310.0, 6778.0,
        8007.0, 9237.0, 10467.0, 11697.0, 13445.0, 16595.0, 21245.0,
    ]
    for hy in h_ys:
        blk.add_line((tb_x0, hy), (tb_x1, hy), dxfattribs={"layer": "DCE_Schedule", "color": 256})

    blk.add_line((39082.0, 212.0), (39082.0, 1693.0), dxfattribs={"layer": "DCE_Schedule", "color": 256})
    blk.add_line((40331.0, 212.0), (40331.0, 1693.0), dxfattribs={"layer": "DCE_Schedule", "color": 256})
    blk.add_line((39766.0, 6778.0), (39766.0, 11697.0), dxfattribs={"layer": "DCE_Schedule", "color": 256})

    # Static labels (user can freely customize text/font/logo in AutoCAD Block Editor)
    _add_static_text_to_block(blk, "KEY PLAN", cx_tb, 21672.0, 230.0)
    _add_static_text_to_block(blk, "CHỦ ĐẦU TƯ:", cx_tb, 20700.0, 240.0)
    _add_static_text_to_block(blk, "ĐỊA CHỈ:", tb_x0 + 180.0, 13800.0, 155.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_static_text_to_block(blk, "Email:", tb_x0 + 180.0, 12700.0, 155.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_static_text_to_block(blk, "Tel:", tb_x0 + 180.0, 12200.0, 155.0, align=TextEntityAlignment.MIDDLE_LEFT)

    for y_row, lbl in [(11082.0, "GIÁM ĐỐC:"), (9852.0, "KIỂM TRA:"), (8622.0, "THIẾT KẾ:"), (7392.0, "THỂ HIỆN:")]:
        _add_static_text_to_block(blk, lbl, tb_x0 + 180.0, y_row, 185.0, align=TextEntityAlignment.MIDDLE_LEFT)

    _add_static_text_to_block(blk, "CÔNG TRÌNH:", cx_tb, 6540.0, 190.0)
    _add_static_text_to_block(blk, "TÊN BẢN VẼ:", cx_tb, 3860.0, 185.0)
    _add_static_text_to_block(blk, "BƯỚC THIẾT KẾ:", (tb_x0 + 39082.0) / 2.0, 1324.0, 150.0)
    _add_static_text_to_block(blk, "KÝ HIỆU BV:", (40331.0 + tb_x1) / 2.0, 1324.0, 150.0)
    _add_static_text_to_block(blk, "HOÀN THÀNH:", (tb_x0 + 39082.0) / 2.0, 583.0, 150.0)

    # Attribute definitions (ATTDEFs) populated dynamically by engine
    _add_attdef_to_block(blk, "CHU_DAU_TU", "ÔNG/BÀ ...", cx_tb, 19450.0, 200.0, prompt="Chủ đầu tư", width=0.88)
    _add_attdef_to_block(blk, "DIA_DIEM", "ĐỊA ĐIỂM XÂY DỰNG ...", cx_tb, 17950.0, 128.0, prompt="Địa điểm dòng 1", width=0.82)
    _add_attdef_to_block(blk, "DIA_DIEM_2", "", cx_tb, 17460.0, 128.0, prompt="Địa điểm dòng 2", width=0.82)
    _add_attdef_to_block(blk, "CONG_TY", "ĐƠN VỊ TƯ VẤN THIẾT KẾ", cx_tb, 15950.0, 185.0, prompt="Tên công ty tư vấn", width=0.88)
    _add_attdef_to_block(blk, "DIA_CHI_CTY", "", tb_x0 + 1150.0, 13800.0, 145.0, align=TextEntityAlignment.MIDDLE_LEFT, prompt="Địa chỉ công ty")
    _add_attdef_to_block(blk, "EMAIL_CTY", "", tb_x0 + 1000.0, 12700.0, 145.0, align=TextEntityAlignment.MIDDLE_LEFT, prompt="Email công ty")
    _add_attdef_to_block(blk, "TEL_CTY", "", tb_x0 + 850.0, 12200.0, 145.0, align=TextEntityAlignment.MIDDLE_LEFT, prompt="Số điện thoại")

    cx_sig = (39766.0 + tb_x1) / 2.0
    _add_attdef_to_block(blk, "GIAM_DOC", "", cx_sig, 11082.0, 165.0, prompt="Giám đốc")
    _add_attdef_to_block(blk, "KIEM_TRA", "", cx_sig, 9852.0, 165.0, prompt="Kiểm tra")
    _add_attdef_to_block(blk, "THIET_KE", "", cx_sig, 8622.0, 165.0, prompt="Thiết kế")
    _add_attdef_to_block(blk, "THE_HIEN", "", cx_sig, 7392.0, 165.0, prompt="Thể hiện")

    _add_attdef_to_block(blk, "TEN_CONG_TRINH", "NHÀ Ở RIÊNG LẺ", cx_tb, 5650.0, 220.0, prompt="Tên công trình")
    _add_attdef_to_block(blk, "HANG_MUC", "BẢN VẼ KẾT CẤU", cx_tb, 3335.0, 190.0, prompt="Hạng mục / Bộ môn")
    _add_attdef_to_block(blk, "TEN_BAN_VE", "MẶT BẰNG KẾT CẤU NGẦM", cx_tb, 2350.0, 210.0, prompt="Tên bản vẽ")

    _add_attdef_to_block(blk, "BUOC_TK", "TKTC", (39082.0 + 40331.0) / 2.0, 1324.0, 185.0, prompt="Bước thiết kế")
    _add_attdef_to_block(blk, "NAM", "2026", (39082.0 + 40331.0) / 2.0, 583.0, 190.0, prompt="Năm hoàn thành")
    _add_attdef_to_block(blk, "KY_HIEU", "KC.02", (40331.0 + tb_x1) / 2.0, 583.0, 220.0, prompt="Ký hiệu bản vẽ")
    _add_attdef_to_block(blk, "TY_LE", "1/100", cx_tb, 4550.0, 145.0, prompt="Tỷ lệ bản vẽ", invisible=True)
    return blk


def ensure_titleblock_a1_definition(
    doc: ezdxf.document.Drawing,
    block_name: str = "DCE_TITLEBLOCK_A1",
) -> Any:
    """Create canonical `DCE_TITLEBLOCK_A1` named block with real ATTDEFs for A1 forms."""
    if block_name in doc.blocks:
        return doc.blocks.get(block_name)

    _ensure_dce_text_style(doc, "Dce_Text")
    blk = doc.blocks.new(name=block_name, base_point=(0.0, 0.0))

    # Bottom-right A1 title block matching sidebar bounds (x=72500..83600, y=1000..15000)
    x0, y0, x1, y1 = 72500.0, 1000.0, 83600.0, 15000.0
    cx = (x0 + x1) / 2.0
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Schedule", "color": 256})

    for hy in [2800.0, 4800.0, 7200.0, 10200.0, 12600.0]:
        blk.add_line((x0, hy), (x1, hy), dxfattribs={"layer": "DCE_Schedule", "color": 256})
    blk.add_line((76200.0, 1000.0), (76200.0, 2800.0), dxfattribs={"layer": "DCE_Schedule", "color": 256})
    blk.add_line((79900.0, 1000.0), (79900.0, 2800.0), dxfattribs={"layer": "DCE_Schedule", "color": 256})

    _add_static_text_to_block(blk, "CHỦ ĐẦU TƯ:", x0 + 300.0, 14200.0, 260.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_attdef_to_block(blk, "CHU_DAU_TU", "CHỦ ĐẦU TƯ", cx, 13400.0, 310.0)

    _add_static_text_to_block(blk, "ĐƠN VỊ TƯ VẤN:", x0 + 300.0, 11850.0, 240.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_attdef_to_block(blk, "CONG_TY", "CÔNG TY TƯ VẤN THIẾT KẾ", cx, 11050.0, 300.0)

    _add_static_text_to_block(blk, "CÔNG TRÌNH:", x0 + 300.0, 9550.0, 250.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_attdef_to_block(blk, "TEN_CONG_TRINH", "DỰ ÁN KẾT CẤU", cx, 8550.0, 360.0)
    _add_attdef_to_block(blk, "DIA_DIEM", "", cx, 7700.0, 230.0)

    _add_static_text_to_block(blk, "TÊN BẢN VẼ:", x0 + 300.0, 6650.0, 240.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_attdef_to_block(blk, "TEN_BAN_VE", "MẶT BẰNG KẾT CẤU", cx, 5700.0, 330.0)

    _add_static_text_to_block(blk, "CHỦ TRÌ / TK / KIỂM:", x0 + 300.0, 4250.0, 220.0, align=TextEntityAlignment.MIDDLE_LEFT)
    _add_attdef_to_block(blk, "CHU_TRI", "KS. CHỦ TRÌ", 74800.0, 3450.0, 230.0)
    _add_attdef_to_block(blk, "THIET_KE", "KS. THIẾT KẾ", 78500.0, 3450.0, 230.0)
    _add_attdef_to_block(blk, "KIEM_TRA", "KS. KIỂM TRA", 81800.0, 3450.0, 230.0)

    _add_static_text_to_block(blk, "TỶ LỆ", 74350.0, 2300.0, 210.0)
    _add_attdef_to_block(blk, "TY_LE", "1/100", 74350.0, 1550.0, 270.0)

    _add_static_text_to_block(blk, "GIAI ĐOẠN / NĂM", 78050.0, 2300.0, 210.0)
    _add_attdef_to_block(blk, "BUOC_TK", "TKTC", 78050.0, 1550.0, 260.0)

    _add_static_text_to_block(blk, "KÝ HIỆU BV", 81750.0, 2300.0, 210.0)
    _add_attdef_to_block(blk, "KY_HIEU", "KC-01", 81750.0, 1550.0, 300.0)
    return blk


def insert_or_update_titleblock(
    doc: ezdxf.document.Drawing,
    msp,
    block_name: str,
    values: Dict[str, Any],
    allowlist_tags: Optional[Iterable[str]] = None,
    insert_point: Tuple[float, float] = (0.0, 0.0),
    mark_owned: bool = False,
) -> Dict[str, Any]:
    """Update existing TitleBlock INSERT attributes cleanly in-place, or insert if absent.

    Unknown custom company ATTRIB tags edited by the engineer in AutoCAD are preserved intact.
    """
    if block_name == "DCE_TITLEBLOCK_A1":
        ensure_titleblock_a1_definition(doc, block_name)
    elif block_name == "DCE_TITLEBLOCK_A3":
        ensure_titleblock_a3_definition(doc, block_name)

    allow = set(allowlist_tags or DEFAULT_ALLOWLIST_TITLE_TAGS) | {"CHU_TRI"}
    clean_vals = {
        str(k): str(v)
        for k, v in (values or {}).items()
        if str(k) in allow and v is not None
    }

    existing_inserts = [
        e for e in msp
        if e.dxftype() == "INSERT" and str(getattr(e.dxf, "name", "")) == block_name
    ]

    blk_def = doc.blocks.get(block_name)
    attdef_tags = [e.dxf.tag for e in blk_def if e.dxftype() == "ATTDEF"] if blk_def else []

    if existing_inserts:
        updated_tags: List[str] = []
        preserved_tags: List[str] = []
        for bref in existing_inserts:
            by_tag = {att.dxf.tag: att for att in bref.attribs}
            for tag, att in by_tag.items():
                if tag in clean_vals:
                    att.dxf.text = clean_vals[tag]
                    att.dxf.color = 256
                    if tag == "TEN_BAN_VE" and len(clean_vals[tag]) > 22:
                        att.dxf.width = max(0.62, min(0.85, 21.0 / float(len(clean_vals[tag]))))
                    updated_tags.append(tag)
                else:
                    preserved_tags.append(tag)
            # Add missing allowlisted attdefs if user had a partial insert
            missing_on_ref = {t: v for t, v in clean_vals.items() if t in attdef_tags and t not in by_tag}
            if missing_on_ref:
                bref.add_auto_attribs(missing_on_ref)
                for att in bref.attribs:
                    if att.dxf.tag in missing_on_ref:
                        att.dxf.color = 256
                updated_tags.extend(missing_on_ref.keys())
        return {
            "mode": "updated_in_place",
            "block_name": block_name,
            "insert_count": len(existing_inserts),
            "updated_tags": sorted(set(updated_tags)),
            "preserved_tags": sorted(set(preserved_tags)),
        }

    # Block defined in template, not yet inserted in ModelSpace
    if blk_def is None:
        raise ValueError(f"TitleBlock definition '{block_name}' not found in document.")

    bref = msp.add_blockref(
        block_name,
        insert_point,
        dxfattribs={"layer": "DCE_Frame", "color": 256},
    )
    to_write = {t: clean_vals[t] for t in attdef_tags if t in clean_vals}
    defaults = {
        e.dxf.tag: (clean_vals[e.dxf.tag] if e.dxf.tag in clean_vals else e.dxf.text)
        for e in blk_def
        if e.dxftype() == "ATTDEF"
    }
    bref.add_auto_attribs(defaults)
    for att in bref.attribs:
        att.dxf.color = 256
    if mark_owned:
        mark_agent_owned(bref, "TITLEBLOCK")
    return {
        "mode": "inserted_from_definition",
        "block_name": block_name,
        "insert_count": 1,
        "updated_tags": sorted(to_write.keys()),
        "preserved_tags": sorted(set(defaults.keys()) - set(to_write.keys())),
    }


# ---------------------------------------------------------------------------
# STRUCTURAL MEMBER & DCE ANNOTATION BLOCK ADAPTERS
# ---------------------------------------------------------------------------

def ensure_pile_block(
    doc: ezdxf.document.Drawing,
    kind: str = "TYPE1",
    size_mm: float = 250.0,
    shape: str = "SQUARE",
    draw_cross_lines: bool = True,
) -> str:
    """Ensure a named `DCE_Pile_*` block exists with clean geometry and semantic ATTDEFs."""
    _ensure_dce_text_style(doc, "Dce_Text")
    k = str(kind).upper()
    sh = str(shape).upper()
    sz_i = int(round(float(size_mm)))
    if sh == "CIRCLE":
        bname = f"DCE_Pile_CIR_{k}_D{sz_i}"
    else:
        cross_tag = "X" if (draw_cross_lines or k == "TYPE1") else "N"
        bname = f"DCE_Pile_SQ_{k}_{sz_i}_{cross_tag}"

    if bname in doc.blocks:
        return bname

    blk = doc.blocks.new(name=bname, base_point=(0.0, 0.0))
    half = float(size_mm) / 2.0

    if sh == "CIRCLE":
        blk.add_circle((0.0, 0.0), half, dxfattribs={"layer": "DCE_Coc", "color": 256})
        if k == "TYPE3":
            h = blk.add_hatch(color=256, dxfattribs={"layer": "DCE_Coc"})
            h.set_pattern_fill("SOLID")
            edge_path = h.paths.add_edge_path()
            edge_path.add_arc((0.0, 0.0), radius=half, start_angle=0, end_angle=360)
        ext = half * 1.35
        if draw_cross_lines:
            blk.add_line((-ext, 0.0), (ext, 0.0), dxfattribs={"layer": "DCE_Coc", "color": 256})
            blk.add_line((0.0, -ext), (0.0, ext), dxfattribs={"layer": "DCE_Coc", "color": 256})
    else:
        pts = [(-half, -half), (half, -half), (half, half), (-half, half)]
        blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Coc", "color": 256})
        if k == "TYPE3":
            h = blk.add_hatch(color=256, dxfattribs={"layer": "DCE_Coc"})
            h.set_pattern_fill("SOLID")
            h.paths.add_polyline_path(pts, is_closed=True)
        elif k == "TYPE2":
            h = blk.add_hatch(color=256, dxfattribs={"layer": "DCE_Hatch"})
            h.set_pattern_fill("ANSI31", scale=32.0, angle=45.0)
            h.paths.add_polyline_path(pts, is_closed=True)
        if draw_cross_lines or k == "TYPE1":
            ext = half * (1.45 if k == "TYPE1" else 1.25)
            blk.add_line((-ext, 0.0), (ext, 0.0), dxfattribs={"layer": "DCE_Coc", "color": 256})
            blk.add_line((0.0, -ext), (0.0, ext), dxfattribs={"layer": "DCE_Coc", "color": 256})

    # Invisible semantic ATTDEFs by default so dense pile clusters remain visually uncluttered
    # while carrying 100% structured BIM/BOQ metadata for checkers & takeoffs.
    _add_attdef_to_block(blk, "PILE_ID", "P1", 0.0, half + 110.0, 110.0, layer="DCE_Coc", invisible=True)
    _add_attdef_to_block(blk, "D", str(sz_i), 0.0, -half - 110.0, 100.0, layer="DCE_Coc", invisible=True)
    _add_attdef_to_block(blk, "L", "", 0.0, -half - 230.0, 100.0, layer="DCE_Coc", invisible=True)
    _add_attdef_to_block(blk, "Q", "", 0.0, -half - 350.0, 100.0, layer="DCE_Coc", invisible=True)
    return bname


def insert_pile_block(
    doc: ezdxf.document.Drawing,
    msp,
    cx: float,
    cy: float,
    kind: str = "TYPE1",
    size_mm: float = 250.0,
    shape: str = "SQUARE",
    draw_cross_lines: bool = True,
    pile_id: str = "P",
    length_m: str = "",
    capacity_t: str = "",
    show_label: bool = False,
    mark_owned: bool = True,
):
    """Insert a normalized 1:1 `DCE_Pile_*` block and bind semantic attributes."""
    bname = ensure_pile_block(doc, kind=kind, size_mm=size_mm, shape=shape, draw_cross_lines=draw_cross_lines)
    bref = msp.add_blockref(
        bname,
        (float(cx), float(cy)),
        dxfattribs={"layer": "DCE_Coc", "xscale": 1.0, "yscale": 1.0, "color": 256},
    )
    bref.add_auto_attribs({
        "PILE_ID": str(pile_id),
        "D": str(int(round(float(size_mm)))),
        "L": str(length_m),
        "Q": str(capacity_t),
    })
    for att in bref.attribs:
        att.dxf.color = 256
        att.is_invisible = not (show_label and att.dxf.tag == "PILE_ID")
    if mark_owned:
        mark_agent_owned(bref, "PILE")
    return bref


def ensure_column_geom_block(
    doc: ezdxf.document.Drawing,
    kind: str = "RC",
    b_mm: float = 200.0,
    h_mm: float = 200.0,
) -> str:
    """Create size-specific geometry-only column block (`xscale=yscale=1.0`, zero distortion)."""
    k = str(kind).upper()
    bi = int(round(float(b_mm)))
    hi = int(round(float(h_mm)))
    bname = f"DCE_COL_{k}_{bi}x{hi}"
    if bname in doc.blocks:
        return bname

    blk = doc.blocks.new(name=bname, base_point=(0.0, 0.0))
    hx = float(b_mm) / 2.0
    hy = float(h_mm) / 2.0
    pts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]

    if k == "RC_STOPPED":
        blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot", "color": 256})
        blk.add_line((-hx, -hy), (hx, hy), dxfattribs={"layer": "DCE_NetThay", "color": 256})
        blk.add_line((-hx, hy), (hx, -hy), dxfattribs={"layer": "DCE_NetThay", "color": 256})
    elif k == "STEEL_H":
        t_f = max(25.0, float(h_mm) * 0.14)
        t_w = max(20.0, float(b_mm) * 0.12)
        h_pts = [
            (-hx, -hy), (hx, -hy), (hx, -hy + t_f), (t_w / 2.0, -hy + t_f),
            (t_w / 2.0, hy - t_f), (hx, hy - t_f), (hx, hy), (-hx, hy),
            (-hx, hy - t_f), (-t_w / 2.0, hy - t_f), (-t_w / 2.0, -hy + t_f),
            (-hx, -hy + t_f),
        ]
        blk.add_lwpolyline(h_pts, close=True, dxfattribs={"layer": "DCE_Cot", "color": 256})
    else:
        blk.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_Cot", "color": 256})
        h = blk.add_hatch(color=8, dxfattribs={"layer": "DCE_Hatch"})
        h.set_pattern_fill("SOLID")
        h.paths.add_polyline_path(pts, is_closed=True)

    return bname


def insert_column_block(
    doc: ezdxf.document.Drawing,
    msp,
    cx: float,
    cy: float,
    b_mm: float,
    h_mm: float,
    kind: str = "RC",
    mark: str = "",
    size_label: str = "",
    show_tag: bool = False,
    tag_scale: float = 70.0,
    tag_offset: Tuple[float, float] = (0.0, 0.0),
    mark_owned: bool = True,
):
    """Insert distortion-free column geometry block + optional separate `TenCauKien` annotation."""
    bname = ensure_column_geom_block(doc, kind=kind, b_mm=b_mm, h_mm=h_mm)
    col_ref = msp.add_blockref(
        bname,
        (float(cx), float(cy)),
        dxfattribs={"layer": "DCE_Cot", "xscale": 1.0, "yscale": 1.0, "color": 256},
    )
    if mark_owned:
        mark_agent_owned(col_ref, "COLUMN")

    tag_ref = None
    if show_tag and mark and "TenCauKien" in doc.blocks:
        tx = float(cx) + float(tag_offset[0])
        ty = float(cy) + float(tag_offset[1])
        tag_ref = msp.add_blockref(
            "TenCauKien",
            (tx, ty),
            dxfattribs={"layer": "Dce_text", "xscale": tag_scale, "yscale": tag_scale, "color": 256},
        )
        tag_ref.add_auto_attribs({
            "TENCAUKIEN": str(mark),
            "SOCAUKIEN": str(size_label or f"({int(round(b_mm))}x{int(round(h_mm))})"),
        })
        for att in tag_ref.attribs:
            att.dxf.color = 256
        if mark_owned:
            mark_agent_owned(tag_ref, "COLUMN_TAG")
    return col_ref, tag_ref


def insert_axis_bubble_native(
    doc: ezdxf.document.Drawing,
    msp,
    x: float,
    y: float,
    label: str,
    rotation_deg: float = 0.0,
    scale: float = 100.0,
    mark_owned: bool = True,
):
    """Insert DCE `Dce_KhTenTruc` with native layer colors (no dark true_color override)."""
    if "Dce_KhTenTruc" not in doc.blocks:
        t = msp.add_text(
            str(label),
            height=2.2 * scale,
            dxfattribs={"layer": "DCE_Block", "style": "Dce_Text", "color": 256},
        )
        t.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)
        if mark_owned:
            mark_agent_owned(t, "AXIS_BUBBLE")
        return t

    bref = msp.add_blockref(
        "Dce_KhTenTruc",
        (float(x), float(y)),
        dxfattribs={
            "layer": "DCE_Block",
            "xscale": float(scale),
            "yscale": float(scale),
            "rotation": float(rotation_deg),
            "color": 256,
        },
    )
    bref.add_auto_attribs({"TRUC": str(label)})
    r = math.radians(rotation_deg)
    bx, by = 0.0, -3.5 * float(scale)
    c, s = math.cos(r), math.sin(r)
    cx = float(x) + c * bx - s * by
    cy = float(y) + s * bx + c * by
    for att in bref.attribs:
        att.dxf.rotation = 0.0
        att.dxf.insert = (cx, cy, 0.0)
        att.dxf.align_point = (cx, cy, 0.0)
        att.dxf.halign = 1
        att.dxf.valign = 2
        att.dxf.color = 256
    if mark_owned:
        mark_agent_owned(bref, "AXIS_BUBBLE")
    return bref


def insert_plan_header_native(
    doc: ezdxf.document.Drawing,
    msp,
    x: float,
    y: float,
    title_vn: str,
    title_en: str = "",
    scale_label: str = "TL: 1/100",
    scale: float = 80.0,
    mark_owned: bool = True,
):
    """Insert `DCE_Plan header 1` ATTRIB block when available, preserving native colors."""
    if "DCE_Plan header 1" not in doc.blocks:
        return None
    bref = msp.add_blockref(
        "DCE_Plan header 1",
        (float(x), float(y)),
        dxfattribs={"layer": "DCE_TKT-TEXT", "xscale": float(scale), "yscale": float(scale), "color": 256},
    )
    bref.add_auto_attribs({
        "DRAWING-VN": str(title_vn),
        "DRAWING-E": str(title_en),
        "SCALE_1:100": str(scale_label),
    })
    for att in bref.attribs:
        att.dxf.color = 256
    if mark_owned:
        mark_agent_owned(bref, "PLAN_HEADER")
    return bref


def purge_unused_blocks(
    doc: ezdxf.document.Drawing,
    keep_blocks: Optional[Iterable[str]] = None,
) -> int:
    """Purge unreferenced block definitions from an exported deliverable in-memory.

    Recursively traces INSERTs across ModelSpace, all PaperSpace layouts, and nested
    blocks, while preserving system blocks (`*`, `_`), dim arrowheads, and essential
    DCE structural contract blocks. Never modifies template files on disk.
    """
    used: set = set()
    queue: List[str] = []

    def _enqueue(name: Optional[str]) -> None:
        if not name:
            return
        if name not in used and name in doc.blocks:
            used.add(name)
            queue.append(name)

    for layout in doc.layouts:
        for ent in layout:
            if ent.dxftype() == "INSERT":
                _enqueue(getattr(ent.dxf, "name", None))

    # Preserve arrow/leader blocks referenced by DimStyles
    for ds in doc.dimstyles:
        for attr in ("dimblk", "dimblk1", "dimblk2", "dimldrblk"):
            val = getattr(ds.dxf, attr, "")
            if val:
                _enqueue(str(val))

    essential = {
        "Dce_KhTenTruc",
        "Dce_TenTruc",
        "DCE_TenCauKien",
    }
    for kb in list(essential) + list(keep_blocks or []):
        _enqueue(str(kb))

    while queue:
        bname = queue.pop()
        try:
            blk = doc.blocks.get(bname)
        except Exception:
            continue
        for ent in blk:
            if ent.dxftype() == "INSERT":
                _enqueue(getattr(ent.dxf, "name", None))

    removed = 0
    for blk in list(doc.blocks):
        bname = blk.name
        if bname.startswith("*") or bname.startswith("_") or bname in used:
            continue
        try:
            doc.blocks.delete_block(bname, safe=False)
            removed += 1
        except Exception:
            pass
    return removed
