# -*- coding: utf-8 -*-
"""
cad_rc_detail_engine.py — Native Open-Form 04 RC Detail & Rebar Schedule Engine (CAD v6.0)
=========================================================================================
Dựng mới 100% bản vẽ chi tiết Kết cấu BTCT (Móng, Giằng móng, Cột vách) trực tiếp trên
nền `Form_04_ChiTiet_Coc_Dam_Cot.dxf` (không tái lập vector từ PDF).

Tuân thủ:
- Native Entities only: LINE/LWPOLYLINE phân lớp DCE_*, DIMENSION (`Dce_25MV`/`Dce_50MV`),
  HATCH `ANSI31` trên `DCE_Hatch`, INSERT các block chuẩn có sẵn trong `Form_04`:
  `DCE_TITLEBLOCK_A3`, `TKTitle`, `TK1..TK14`, `Dce_CaoTrinh`, `DCE_MatCatA`,
  `Dce_KhtThepDai`, `Dce_DanhDauThep`, `Dce_McThepChu`.
- Ký hiệu AutoCAD chuẩn: 100% dùng `%%c` thay cho đường kính phi (`%%c16`) và `%%p` thay cho `±`.
- Deterministic Math: `RebarScheduleBuilder` tính toán và ghi `Calculation_Logs` +
  `Standard_Method` + `total_steel_kg` vào `.dce_audit.json` (khớp tuyệt đối tổng `KL` trên `TK*`).
- PaperSpace Layout: thiết lập layout A3 (`420x297 mm`) kèm `VIEWPORT` zoom chuẩn.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf
from ezdxf.math import Matrix44

_CAD_DIR = str(Path(__file__).resolve().parent)
if _CAD_DIR not in sys.path:
    sys.path.insert(0, _CAD_DIR)

from cad_block_adapters import (  # noqa: E402
    insert_or_update_titleblock,
    mark_new_entities_owned,
    purge_unused_blocks,
    snapshot_msp_handles,
)
from cad_form_contract import resolve_form_paths, validate_open_form  # noqa: E402
from cad_multiview_a3 import (  # noqa: E402
    _ensure_a3_layers_and_styles,
    _hide_zone_guide_layers_for_export,
)
from cad_plan_engine import DcePlanEngine  # noqa: E402

STANDARD_METHOD_DETAIL = "TCVN 5574:2018 + TCVN 1651-2:2018 (CAD v6.0 Open Form_04)"
STEEL_DENSITY_KG_M3 = 7850.0


def rebar_unit_weight_kg_per_m(dia_mm: float) -> float:
    """Trọng lượng riêng cốt thép tròn [kg/m] theo đường kính danh nghĩa mm."""
    d = float(dia_mm)
    return math.pi * ((d / 2000.0) ** 2) * STEEL_DENSITY_KG_M3


def _fmt_tk_dim(val: Any) -> str:
    if isinstance(val, (int, float)):
        v = float(val)
        return str(int(round(v))) if abs(v - round(v)) < 1e-6 else f"{v:.1f}"
    return str(val)


def compute_bbs_rows(raw_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Tính toán định lượng bảng thống kê cốt thép (BBS) và sinh `Calculation_Logs`."""
    computed: List[Dict[str, Any]] = []
    calc_logs: List[Dict[str, Any]] = []
    total_kg = 0.0
    total_len_m = 0.0

    for idx, row in enumerate(raw_rows, start=1):
        tk_block = str(row.get("tk_block", "TK1")).strip()
        dims = dict(row.get("dims_mm", {}))
        dia = int(row.get("dia_mm", 12))
        sl = int(row.get("sl", 1))
        skc = int(row.get("skc", 1))
        member = str(row.get("member", ""))
        sh = str(row.get("sh", str(idx)))

        if tk_block == "TK1":
            sum_l_mm = float(dims.get("L", 0.0))
            len_expr = f"L={_fmt_tk_dim(sum_l_mm)}"
        elif tk_block in ("TK2", "TK3", "TK5"):
            l1 = float(dims.get("L1", 0.0))
            l2 = float(dims.get("L2", 0.0))
            sum_l_mm = l1 + l2
            len_expr = f"L1+L2={_fmt_tk_dim(l1)}+{_fmt_tk_dim(l2)}"
        elif tk_block in ("TK4", "TK7"):
            l1 = float(dims.get("L1", 0.0))
            l2 = float(dims.get("L2", 0.0))
            l3 = float(dims.get("L3", 0.0))
            sum_l_mm = l1 + l2 + l3
            len_expr = f"L1+L2+L3={_fmt_tk_dim(l1)}+{_fmt_tk_dim(l2)}+{_fmt_tk_dim(l3)}"
        elif tk_block == "TK8":
            l0 = float(dims.get("L", 0.0))
            m1 = float(dims.get("M1", 0.0))
            m2 = float(dims.get("M2", 0.0))
            sum_l_mm = l0 + m1 + m2
            len_expr = f"L+M1+M2={_fmt_tk_dim(l0)}+{_fmt_tk_dim(m1)}+{_fmt_tk_dim(m2)}"
        elif tk_block == "TK9":
            l1 = float(dims.get("L1", 0.0))
            l2 = float(dims.get("L2", 0.0))
            m = float(dims.get("M", 120.0))
            sum_l_mm = 2.0 * (l1 + l2) + m
            len_expr = f"2*(L1+L2)+M=2*({_fmt_tk_dim(l1)}+{_fmt_tk_dim(l2)})+{_fmt_tk_dim(m)}"
        else:
            sum_l_mm = float(sum(float(v) for v in dims.values()))
            len_expr = "+".join(f"{k}={_fmt_tk_dim(v)}" for k, v in dims.items())

        tsl = sl * skc
        l_all_m = round((sum_l_mm * tsl) / 1000.0, 2)
        uw = rebar_unit_weight_kg_per_m(dia)
        kl_kg = round(l_all_m * uw, 2)
        total_kg = round(total_kg + kl_kg, 2)
        total_len_m = round(total_len_m + l_all_m, 2)

        attr_map: Dict[str, str] = {
            "SH": sh,
            "DK": f"%%c{dia}",
            "sumL": _fmt_tk_dim(sum_l_mm),
            "SKC": str(skc),
            "SL": str(sl),
            "TSL": str(tsl),
            "Lall": f"{l_all_m:.2f}",
            "KL": f"{kl_kg:.2f}",
        }
        for dk, dv in dims.items():
            attr_map[str(dk)] = _fmt_tk_dim(dv)

        item = {
            "member": member,
            "member_title": str(row.get("member_title", member)),
            "sh": sh,
            "tk_block": tk_block,
            "dims_mm": dims,
            "dia_mm": dia,
            "sum_l_mm": round(sum_l_mm, 1),
            "sl": sl,
            "skc": skc,
            "tsl": tsl,
            "l_all_m": l_all_m,
            "unit_weight_kg_m": round(uw, 4),
            "kl_kg": kl_kg,
            "attribs": attr_map,
        }
        computed.append(item)
        calc_logs.append({
            "step": f"BBS-{idx:02d}",
            "member": member,
            "sh": sh,
            "dia_mm": dia,
            "cut_length_mm": round(sum_l_mm, 1),
            "tsl": tsl,
            "total_length_m": l_all_m,
            "unit_weight_kg_m": round(uw, 4),
            "mass_kg": kl_kg,
            "formula": f"({len_expr})*{tsl}/1000 * {uw:.4f}",
            "result": f"{kl_kg:.2f} kg",
        })

    return {
        "rows": computed,
        "Calculation_Logs": calc_logs,
        "Standard_Method": STANDARD_METHOD_DETAIL,
        "total_length_m": total_len_m,
        "total_steel_kg": total_kg,
    }


def _rect_poly(
    msp,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    layer: str,
    const_width: float = 0.0,
    color: int = 256,
):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return msp.add_lwpolyline(
        pts,
        close=True,
        dxfattribs={"layer": layer, "const_width": const_width, "color": color},
    )


def _add_text(
    msp,
    text: str,
    x: float,
    y: float,
    height: float,
    layer: str = "Dce_text",
    width: float = 0.85,
    halign: str = "CENTER",
    rotation: float = 0.0,
    color: int = 256,
    style: str = "Dce_Text",
):
    from ezdxf.enums import TextEntityAlignment

    align_map = {
        "LEFT": TextEntityAlignment.LEFT,
        "CENTER": TextEntityAlignment.CENTER,
        "RIGHT": TextEntityAlignment.RIGHT,
        "MIDDLE_CENTER": TextEntityAlignment.MIDDLE_CENTER,
        "MIDDLE_LEFT": TextEntityAlignment.MIDDLE_LEFT,
        "MIDDLE_RIGHT": TextEntityAlignment.MIDDLE_RIGHT,
    }
    al = align_map.get(halign.upper(), TextEntityAlignment.MIDDLE_CENTER)
    ent = msp.add_text(
        str(text),
        dxfattribs={
            "height": float(height),
            "layer": layer,
            "style": style,
            "width": float(width),
            "rotation": float(rotation),
            "color": int(color),
        },
    )
    ent.set_placement((float(x), float(y)), align=al)
    return ent


def _add_hatch_poly(
    msp,
    points: Sequence[Tuple[float, float]],
    pattern: str = "ANSI31",
    scale: float = 1.0,
    angle: float = 0.0,
    layer: str = "DCE_Hatch",
    color: int = 8,
):
    h = msp.add_hatch(dxfattribs={"layer": layer, "color": int(color)})
    if pattern.upper() == "SOLID":
        h.set_solid_fill(color=int(color))
    else:
        h.set_pattern_fill(pattern, color=int(color), angle=float(angle), scale=float(scale))
    h.paths.add_polyline_path(list(points), is_closed=True)
    return h


def _add_dim(
    msp,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    distance: float,
    dimstyle: str = "Dce_25MV",
    text_override: Optional[str] = None,
    dimlfac: Optional[float] = None,
    layer: str = "DCE_Dim",
):
    ov: Dict[str, Any] = {"dimtad": 1, "dimclrd": 256, "dimclre": 256, "dimclrt": 256}
    if dimlfac is not None:
        ov["dimlfac"] = float(dimlfac)
    kw: Dict[str, Any] = {
        "p1": p1,
        "p2": p2,
        "distance": float(distance),
        "dimstyle": dimstyle,
        "override": ov,
        "dxfattribs": {"layer": layer},
    }
    if text_override is not None:
        kw["text"] = str(text_override)
    dim = msp.add_aligned_dim(**kw)
    dim.render()
    return dim


def _insert_block(
    doc,
    msp,
    block_name: str,
    insert_pt: Tuple[float, float],
    scale: float,
    layer: str,
    attribs: Optional[Dict[str, str]] = None,
    rotation: float = 0.0,
):
    blk_ref = msp.add_blockref(
        block_name,
        insert_pt,
        dxfattribs={
            "xscale": float(scale),
            "yscale": float(scale),
            "zscale": float(scale),
            "rotation": float(rotation),
            "layer": layer,
        },
    )
    if block_name in doc.blocks:
        blk_def = doc.blocks[block_name]
        if any(e.dxftype() == "ATTDEF" for e in blk_def):
            blk_ref.add_auto_attribs(attribs or {})
    return blk_ref


def _insert_elev(
    doc,
    msp,
    ct_text: str,
    x: float,
    y: float,
    sheet_scale: float,
    layer: str = "DCE_Dim",
):
    return _insert_block(
        doc,
        msp,
        "Dce_CaoTrinh",
        (x, y),
        scale=float(sheet_scale),
        layer=layer,
        attribs={"CT": str(ct_text)},
    )


def _insert_section_tag(
    doc,
    msp,
    sec_num: str,
    x: float,
    y: float,
    sheet_scale: float,
    rotation: float = 0.0,
):
    return _insert_block(
        doc,
        msp,
        "DCE_MatCatA",
        (x, y),
        scale=float(sheet_scale),
        layer="DCE_Name",
        attribs={"1": str(sec_num)},
        rotation=rotation,
    )


def _insert_rebar_dot(
    doc,
    msp,
    x: float,
    y: float,
    dot_scale: float,
    layer: str = "DCE_ThepChu",
):
    return _insert_block(
        doc,
        msp,
        "Dce_McThepChu",
        (x, y),
        scale=float(dot_scale),
        layer=layer,
    )


def _insert_rebar_callout(
    doc,
    msp,
    sh: str,
    dkvakc: str,
    vitri: str,
    tag_x: float,
    tag_y: float,
    ticks: Sequence[Tuple[float, float]],
    sheet_scale: float,
    bend_x: Optional[float] = None,
    layer_leader: str = "DCE_Leader",
):
    """Vẽ leader nối `Dce_KhtThepDai` tới các thanh thép (gắn tick `Dce_DanhDauThep`)."""
    tick_scale = sheet_scale * 0.85
    if ticks:
        for tx, ty in ticks:
            _insert_block(doc, msp, "Dce_DanhDauThep", (tx, ty), scale=tick_scale, layer=layer_leader)
        t0x, t0y = ticks[0]
        # Đường gạch chân nằm sát dưới text & đáy vòng tròn block (`-6.2 * s`), tránh cắt ngang chữ (`-4.5 * s`)
        line_y = tag_y - 6.2 * sheet_scale
        if bend_x is None:
            bend_x = tag_x - 8.5 * sheet_scale if tag_x >= t0x else tag_x + 17.5 * sheet_scale
        end_x = tag_x + (16.5 * sheet_scale if vitri else 9.0 * sheet_scale)
        msp.add_polyline2d(
            [(t0x, t0y), (bend_x, line_y), (end_x, line_y)],
            dxfattribs={"layer": layer_leader},
        )
        for tx, ty in ticks[1:]:
            msp.add_line((tx, ty), (t0x, t0y), dxfattribs={"layer": layer_leader})

    return _insert_block(
        doc,
        msp,
        "Dce_KhtThepDai",
        (tag_x, tag_y),
        scale=float(sheet_scale),
        layer="DCE_Name",
        attribs={"SH": str(sh), "DKVAKC": str(dkvakc), "VITRI": str(vitri)},
    )


def _render_bbs_table(
    doc,
    msp,
    bbs_data: Dict[str, Any],
    zone_bbox: Tuple[float, float, float, float],
    sheet_scale: float,
    sheet_no: str,
) -> None:
    """Chèn `TKTitle` + các dòng `TK*` + khung tên cấu kiện gộp + tổng khối lượng thép."""
    zx0, zy0, zx1, zy1 = zone_bbox
    scale_ratio = float(sheet_scale) / 100.0
    zone_w = zx1 - zx0
    tk_scale = min(61.5 * scale_ratio, (zone_w - 80.0 * scale_ratio) / 192.5)
    tbl_w = 192.5 * tk_scale
    x0 = zx0 + (zone_w - tbl_w) / 2.0
    cur_y = zy1 - 120.0 * scale_ratio

    # 1. Insert header `TKTitle`
    _insert_block(doc, msp, "TKTitle", (x0, cur_y), scale=tk_scale, layer="DCE_Schedule")
    cur_y -= 35.0 * tk_scale

    rows = list(bbs_data.get("rows", []))
    row_h = 8.0 * tk_scale

    # Nhóm liên tiếp theo `member` để vẽ khung gộp cột 0..15 (`TÊN CẤU KIỆN`)
    groups: List[Tuple[str, str, int, int]] = []
    start_idx = 0
    while start_idx < len(rows):
        mem = rows[start_idx]["member"]
        title = rows[start_idx].get("member_title") or mem
        end_idx = start_idx + 1
        while end_idx < len(rows) and rows[end_idx]["member"] == mem:
            end_idx += 1
        groups.append((mem, title, start_idx, end_idx))
        start_idx = end_idx

    group_starts = {g[2]: g for g in groups}
    group_ends = {g[3] - 1: g for g in groups}

    for i, r in enumerate(rows):
        _insert_block(
            doc,
            msp,
            r["tk_block"],
            (x0, cur_y),
            scale=tk_scale,
            layer="DCE_Schedule",
            attribs=r["attribs"],
        )
        if i in group_ends:
            _, title, g_start, g_end = group_ends[i]
            n_rows = g_end - g_start
            y_top_grp = cur_y + (n_rows - 1) * row_h
            y_bot_grp = cur_y - row_h
            # Đường ngang đóng nhóm cột TÊN CẤU KIỆN (x = 0 .. 15 * tk_scale)
            msp.add_line((x0, y_bot_grp), (x0 + 15.0 * tk_scale, y_bot_grp), dxfattribs={"layer": "DCE_BaoBeTong"})
            lines = [ln.strip() for ln in str(title).split("\n") if ln.strip()]
            cx_mem = x0 + 7.5 * tk_scale
            cy_mem = (y_top_grp + y_bot_grp) / 2.0
            th = min(2.3 * tk_scale, max(1.6 * tk_scale, (row_h * 0.34)))
            line_step = th * 1.45
            y_first = cy_mem + ((len(lines) - 1) * line_step) / 2.0
            for li, ltxt in enumerate(lines):
                _add_text(
                    msp,
                    ltxt,
                    cx_mem,
                    y_first - li * line_step,
                    th,
                    layer="Dce_text",
                    halign="MIDDLE_CENTER",
                )
        cur_y -= row_h

    # Dòng tổng kết toàn tờ
    tot_h = 9.0 * tk_scale
    _rect_poly(msp, x0, cur_y - tot_h, x0 + tbl_w, cur_y, layer="DCE_BaoBeTong")
    _add_text(
        msp,
        f"TỔNG CỘNG KHỐI LƯỢNG THÉP TỜ {sheet_no}:",
        x0 + 6.0 * tk_scale,
        cur_y - tot_h / 2.0,
        2.5 * tk_scale,
        layer="Dce_text",
        halign="MIDDLE_LEFT",
    )
    _add_text(
        msp,
        f"{bbs_data['total_length_m']:.2f} m",
        x0 + 165.0 * tk_scale,
        cur_y - tot_h / 2.0,
        2.5 * tk_scale,
        layer="Dce_text",
        halign="MIDDLE_RIGHT",
    )
    _add_text(
        msp,
        f"{bbs_data['total_steel_kg']:.2f} kg",
        x0 + 190.5 * tk_scale,
        cur_y - tot_h / 2.0,
        2.6 * tk_scale,
        layer="Dce_text",
        halign="MIDDLE_RIGHT",
    )


def _render_note_box(
    msp,
    zone_bbox: Tuple[float, float, float, float],
    sheet_scale: float,
    title: str,
    notes: Sequence[str],
) -> None:
    zx0, zy0, zx1, zy1 = zone_bbox
    sr = float(sheet_scale) / 100.0
    pad_x = 180.0 * sr
    pad_y = 220.0 * sr
    x_txt = zx0 + pad_x + 120.0 * sr
    y_cur = zy1 - pad_y - 250.0 * sr
    _rect_poly(msp, zx0 + pad_x, zy0 + pad_y, zx1 - pad_x, zy1 - pad_y, layer="DCE_Schedule")
    _add_text(
        msp,
        title,
        (zx0 + zx1) / 2.0,
        y_cur,
        260.0 * sr,
        layer="DCE_Name",
        halign="MIDDLE_CENTER",
    )
    y_cur -= 260.0 * sr
    msp.add_line((zx0 + pad_x, y_cur), (zx1 - pad_x, y_cur), dxfattribs={"layer": "DCE_Schedule"})
    y_cur -= 320.0 * sr
    wrap_w = 50
    for note in notes:
        wrapped = textwrap.wrap(note, width=wrap_w) or [note]
        for ln in wrapped:
            if y_cur < zy0 + pad_y + 220.0 * sr:
                break
            _add_text(
                msp,
                ln,
                x_txt,
                y_cur,
                165.0 * sr,
                layer="Dce_text",
                halign="MIDDLE_LEFT",
                width=0.82,
            )
            y_cur -= 290.0 * sr
        y_cur -= 90.0 * sr


def _load_scaled_form04(
    project: Dict[str, Any],
    sheet_no: str,
    sheet_title: str,
    sheet_scale: float,
    project_dir: Optional[str | Path] = None,
) -> Tuple[DcePlanEngine, Dict[str, Tuple[float, float, float, float]], float, float]:
    """Nạp `Form_04_ChiTiet_Coc_Dam_Cot.dxf`, scale khung A3 theo `sheet_scale/100`, cập nhật `DCE_TITLEBLOCK_A3`."""
    res = resolve_form_paths(form_id="FORM_04_CHITIET_COC_DAM_COT", project_dir=project_dir)
    if res.dxf_path is None:
        raise FileNotFoundError(f"Open Form_04 not found: {res.searched_paths}")
    val = validate_open_form(res.dxf_path, manifest_path=res.manifest_path, form_id="FORM_04_CHITIET_COC_DAM_COT", tier=res.tier)
    if not val.valid:
        raise ValueError(f"Open Form_04 contract invalid: {val.errors}")

    sr = float(sheet_scale) / 100.0
    frame_w = 42000.0 * sr
    frame_h = 29700.0 * sr

    engine = DcePlanEngine(
        {
            **project,
            "scale": float(sheet_scale),
            "sheet_scale_label": f"1/{int(sheet_scale)}",
            "L_total": 4.2,
            "B_total": 2.97,
        },
        template_path=res.dxf_path,
        v6=True,
        preserve_modelspace=True,
        template_mode="open",
        template_contract={
            "template_mode": "open",
            "form_id": val.form_id,
            "tier": val.tier,
            "dxf_path": val.dxf_path,
            "dxf_version": val.dxf_version,
            "ucs_ok": val.ucs_ok,
            "titleblock_block": val.titleblock_block,
        },
        zone_evidence={"zones_wcs": {k: [[round(v * sr, 2) for v in bb] for bb in bbs] for k, bbs in val.zones_wcs.items()}},
        full_evidence=False,
    )
    engine.setup()
    _ensure_a3_layers_and_styles(engine.doc)

    # Scale 12 thực thể nền của Form_04 quanh gốc (0, 0) theo tỷ lệ thực của tờ bản vẽ
    if abs(sr - 1.0) > 1e-6:
        mat = Matrix44.scale(sr, sr, sr)
        for ent in list(engine.msp):
            try:
                ent.transform(mat)
            except Exception:
                pass

    # Với tờ dàn trải toàn khung dọc (KC.03 3 đài, KC.08/KC.09 cột đứng), ẩn/bỏ đường LINE chia đôi ngang ở y=frame_h/2
    if sheet_no in ("KC.03", "KC.08", "KC.09"):
        mid_y = frame_h / 2.0
        for ent in list(engine.msp):
            if ent.dxftype() == "LINE" and str(ent.dxf.get("layer", "")) == "DCE_Frame":
                if abs(ent.dxf.start.y - mid_y) < 120.0 * sr and abs(ent.dxf.end.y - mid_y) < 120.0 * sr:
                    engine.msp.delete_entity(ent)

    # Đảm bảo chữ trong DCE_TITLEBLOCK_A3 scale đúng và điền thông tin thực dự án
    addr_lines = [str(x) for x in project.get("site_address_lines", []) if str(x).strip()]
    dia_diem_1 = addr_lines[0] if len(addr_lines) >= 1 else ""
    dia_diem_2 = addr_lines[1] if len(addr_lines) >= 2 else ""
    tb_values = {
        "CHU_DAU_TU": project.get("investor", ""),
        "DIA_DIEM": dia_diem_1,
        "DIA_DIEM_2": dia_diem_2,
        "CONG_TY": project.get("company", ""),
        "GIAM_DOC": project.get("director", ""),
        "KIEM_TRA": project.get("reviewer", ""),
        "THIET_KE": project.get("designer", ""),
        "THE_HIEN": project.get("drafter", ""),
        "TEN_CONG_TRINH": project.get("project_name", "NHÀ Ở RIÊNG LẺ"),
        "HANG_MUC": project.get("drawing_category", "BẢN VẼ KẾT CẤU"),
        "TEN_BAN_VE": sheet_title,
        "BUOC_TK": project.get("design_stage", "TKTC"),
        "NAM": str(project.get("year", "2026")),
        "KY_HIEU": str(sheet_no),
        "TY_LE": f"1/{int(sheet_scale)}",
    }
    insert_or_update_titleblock(
        engine.doc,
        engine.msp,
        block_name="DCE_TITLEBLOCK_A3",
        values=tb_values,
        mark_owned=False,
    )

    scaled_zones: Dict[str, Tuple[float, float, float, float]] = {}
    for zname, bbs in val.zones_wcs.items():
        if bbs:
            b = bbs[0]
            scaled_zones[zname] = (b[0] * sr, b[1] * sr, b[2] * sr, b[3] * sr)

    return engine, scaled_zones, frame_w, frame_h


def _setup_a3_paperspace_layout(doc, sheet_no: str, frame_w: float, frame_h: float) -> str:
    """Thiết lập PaperSpace Layout A3 (420x297 mm) với VIEWPORT nhìn toàn bộ ModelSpace khung Form_04."""
    lname = str(sheet_no).replace("/", "_")
    if "Layout1" in doc.layouts:
        doc.layouts.rename("Layout1", lname)
        ps = doc.layouts.get(lname)
    elif lname in doc.layouts:
        ps = doc.layouts.get(lname)
    else:
        ps = doc.layouts.new(lname)

    if "Layout2" in doc.layouts and "Layout2" != lname:
        try:
            doc.layouts.delete("Layout2")
        except Exception:
            pass

    for ent in list(ps):
        ps.delete_entity(ent)

    ps.page_setup(size=(420.0, 297.0), margins=(0.0, 0.0, 0.0, 0.0), units="mm")
    _rect_poly(ps, 0.0, 0.0, 420.0, 297.0, layer="DCE_Frame")
    ps.add_viewport(
        center=(210.0, 148.5),
        size=(410.0, 287.0),
        view_center_point=(frame_w / 2.0, frame_h / 2.0),
        view_height=frame_h * 1.02,
        status=2,
        dxfattribs={"layer": "Defpoints"},
    )
    return lname


# ==============================================================================
# CỤM BẢN VẼ 1: MÓNG & GIẰNG MÓNG (KC.03, KC.04 — TL 1/25)
# ==============================================================================

def _draw_pile_cap_detail(
    doc,
    msp,
    cap: Dict[str, Any],
    origin_x: float,
    base_y: float,
    sheet_scale: float = 25.0,
) -> None:
    """Vẽ Mặt bằng đài cọc (bên trái) + Mặt cắt chi tiết đài cọc (bên phải) với cọc, bê tông lót, thép T1/T2/B1/B2, đai C."""
    name = cap["name"]
    sl_count = int(cap["sl"])
    w = float(cap["w"])
    h = float(cap["h"])
    thick = float(cap["thick"])
    lean = float(cap.get("lean", 100.0))
    cover = float(cap.get("cover", 50.0))
    piles: List[Tuple[float, float]] = [(float(px), float(py)) for px, py in cap["piles"]]
    pile_sz = float(cap.get("pile_size", 250.0))
    top_elev = str(cap["top_elev"])
    bot_elev = str(cap["bot_elev"])
    sec_name = str(cap["sec_name"])
    sec_num = str(cap["sec_num"])
    chamfer = float(cap.get("chamfer", 0.0))
    col_sz: Tuple[float, float] = (float(cap["col_sz"][0]), float(cap["col_sz"][1]))
    hook_len = float(cap.get("hook", 360.0))
    bars = cap["bars"]

    # 1. MẶT BẰNG ĐÀI CỌC (góc dưới trái tại origin_x, base_y)
    px0, py0 = origin_x, base_y
    px1, py1 = px0 + w, py0 + h
    if chamfer > 0:
        pts = [
            (px0 + chamfer, py0), (px1 - chamfer, py0),
            (px1, py0 + chamfer), (px1, py1 - chamfer),
            (px1 - chamfer, py1), (px0 + chamfer, py1),
            (px0, py1 - chamfer), (px0, py0 + chamfer),
        ]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "DCE_BaoBeTong"})
    else:
        _rect_poly(msp, px0, py0, px1, py1, layer="DCE_BaoBeTong")

    # Bê tông lót 100mm bao ngoài
    _rect_poly(msp, px0 - lean, py0 - lean, px1 + lean, py1 + lean, layer="DCE_NetDut")

    # Cọc BTCT 250x250 trên mặt bằng
    half_p = pile_sz / 2.0
    for cx_rel, cy_rel in piles:
        cx, cy = px0 + cx_rel, py0 + cy_rel
        _rect_poly(msp, cx - half_p, cy - half_p, cx + half_p, cy + half_p, layer="DCE_Coc")
        msp.add_line((cx - half_p - 60, cy), (cx + half_p + 60, cy), dxfattribs={"layer": "DCE_NetDut"})
        msp.add_line((cx, cy - half_p - 60), (cx, cy + half_p + 60), dxfattribs={"layer": "DCE_NetDut"})

    # Cổ cột trên mặt bằng (Solid Hatch xám chuẩn DCE_Hatch color=8)
    cw, ch = col_sz
    ccx, ccy = (px0 + px1) / 2.0, (py0 + py1) / 2.0
    _rect_poly(msp, ccx - cw / 2.0, ccy - ch / 2.0, ccx + cw / 2.0, ccy + ch / 2.0, layer="DCE_Cot")
    _add_hatch_poly(
        msp,
        [(ccx - cw / 2.0, ccy - ch / 2.0), (ccx + cw / 2.0, ccy - ch / 2.0),
         (ccx + cw / 2.0, ccy + ch / 2.0), (ccx - cw / 2.0, ccy + ch / 2.0)],
        pattern="SOLID",
        color=8,
        layer="DCE_Hatch",
    )

    # Ký hiệu mặt cắt ngang đi qua tim đài
    msp.add_line((px0 - 240.0, ccy), (px1 + 240.0, ccy), dxfattribs={"layer": "DCE_NetDut"})
    _insert_section_tag(doc, msp, sec_num, px0 - 200.0, ccy, sheet_scale, rotation=90.0)
    _insert_section_tag(doc, msp, sec_num, px1 + 200.0, ccy, sheet_scale, rotation=90.0)

    # Kích thước mặt bằng đài (`Dce_25MV`)
    _add_dim(msp, (px0, py0 - lean), (px1, py0 - lean), -240.0, dimstyle="Dce_25MV")
    if len(piles) >= 2:
        p_xs = sorted({px0 + p[0] for p in piles})
        _add_dim(msp, (px0, py0 - lean), (p_xs[0], py0 - lean), -120.0, dimstyle="Dce_25MV")
        _add_dim(msp, (p_xs[0], py0 - lean), (p_xs[-1], py0 - lean), -120.0, dimstyle="Dce_25MV")
        _add_dim(msp, (p_xs[-1], py0 - lean), (px1, py0 - lean), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, py0), (px0 - lean, py1), -240.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, py0), (px0 - lean, ccy), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, ccy), (px0 - lean, py1), -120.0, dimstyle="Dce_25MV")

    # Tên Mặt bằng đài
    _add_text(
        msp,
        f"MẶT BẰNG ĐÀI {name} (SL={sl_count})",
        (px0 + px1) / 2.0,
        py0 - lean - 420.0,
        75.0,
        layer="DCE_Name",
        halign="MIDDLE_CENTER",
    )

    # 2. MẶT CẮT CHI TIẾT ĐÀI CỌC (bên phải Mặt bằng)
    sx0 = px1 + 780.0
    sy_bot = py0 + 180.0
    sy_top = sy_bot + thick
    sx1 = sx0 + w

    # Bao bê tông đài & cổ cột nhô 380mm
    _rect_poly(msp, sx0, sy_bot, sx1, sy_top, layer="DCE_BaoBeTong")
    _rect_poly(msp, sx0 + (w - cw) / 2.0, sy_top, sx0 + (w + cw) / 2.0, sy_top + 380.0, layer="DCE_Cot")
    # Bê tông lót 100mm dưới đáy đài
    _rect_poly(msp, sx0 - lean, sy_bot - lean, sx1 + lean, sy_bot, layer="DCE_NetThay")
    _add_hatch_poly(
        msp,
        [(sx0 - lean, sy_bot - lean), (sx1 + lean, sy_bot - lean), (sx1 + lean, sy_bot), (sx0 - lean, sy_bot)],
        pattern="AR-CONC" if "AR-CONC" in doc.linetypes else "ANSI31",
        scale=1.6,
        angle=45.0,
        layer="DCE_Hatch",
    )

    # Cọc nhô vào đài 100mm & thân cọc xuống 380mm
    unique_px = sorted({p[0] for p in piles})
    for ux in unique_px:
        cx_s = sx0 + ux
        _rect_poly(msp, cx_s - half_p, sy_bot - lean - 380.0, cx_s + half_p, sy_bot - lean, layer="DCE_Coc")
        _rect_poly(msp, cx_s - half_p, sy_bot - lean, cx_s + half_p, sy_bot + 100.0, layer="DCE_Coc")
        # Thép râu đầu cọc
        msp.add_line((cx_s - 65, sy_bot + 100.0), (cx_s - 65, sy_bot + 360.0), dxfattribs={"layer": "DCE_ThepChu"})
        msp.add_line((cx_s + 65, sy_bot + 100.0), (cx_s + 65, sy_bot + 360.0), dxfattribs={"layer": "DCE_ThepChu"})

    # Cốt thép đài: lưới dưới B1 (dọc) + chấm B2 (ngang), lưới trên T1 (dọc) + chấm T2 (ngang), đai giữ C
    y_bot_bar = sy_bot + cover + 20.0
    y_top_bar = sy_top - cover - 20.0
    x_bar0 = sx0 + cover
    x_bar1 = sx1 - cover
    hook_dy = min(hook_len, thick - 2 * cover - 40.0)
    # Thanh B1 (chữ U ngửa)
    msp.add_lwpolyline(
        [(x_bar0, y_bot_bar + hook_dy), (x_bar0, y_bot_bar), (x_bar1, y_bot_bar), (x_bar1, y_bot_bar + hook_dy)],
        dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0},
    )
    # Thanh T1 (chữ U úp)
    msp.add_lwpolyline(
        [(x_bar0 + 18, y_top_bar - hook_dy * 0.7), (x_bar0 + 18, y_top_bar), (x_bar1 - 18, y_top_bar), (x_bar1 - 18, y_top_bar - hook_dy * 0.7)],
        dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0},
    )
    # Thép cổ cột neo vào đài
    col_bx0 = sx0 + (w - cw) / 2.0 + 35.0
    col_bx1 = sx0 + (w + cw) / 2.0 - 35.0
    msp.add_lwpolyline([(col_bx0 - 140, y_bot_bar + 20), (col_bx0, y_bot_bar + 20), (col_bx0, sy_top + 380.0)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0})
    msp.add_lwpolyline([(col_bx1 + 140, y_bot_bar + 20), (col_bx1, y_bot_bar + 20), (col_bx1, sy_top + 380.0)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0})

    # Các chấm thép ngang B2 (dưới) & T2 (trên) + đai C ở mặt bên
    n_dots = max(5, int((w - 2 * cover) / 160))
    for di in range(n_dots):
        dx = x_bar0 + 75.0 + di * ((w - 2 * cover - 150.0) / max(1, n_dots - 1))
        _insert_rebar_dot(doc, msp, dx, y_bot_bar + 24.0, dot_scale=18.0)
        _insert_rebar_dot(doc, msp, dx, y_top_bar - 24.0, dot_scale=18.0)

    y_mid_tie = (y_bot_bar + y_top_bar) / 2.0
    msp.add_line((x_bar0 - 15, y_mid_tie), (x_bar1 + 15, y_mid_tie), dxfattribs={"layer": "DCE_ThepDai"})

    # Cao trình + Kích thước mặt cắt đài
    _insert_elev(doc, msp, top_elev, sx0 - 30.0, sy_top, sheet_scale)
    _insert_elev(doc, msp, bot_elev, sx0 - 30.0, sy_bot, sheet_scale)
    _add_dim(msp, (sx0 - lean, sy_bot - lean), (sx0 - lean, sy_bot), -160.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0, sy_bot), (sx0, sy_top), -160.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0, sy_top + 380.0), (sx1, sy_top + 380.0), 160.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0 + (w - cw) / 2.0, sy_top + 380.0), (sx0 + (w + cw) / 2.0, sy_top + 380.0), 80.0, dimstyle="Dce_25MV")
    if unique_px:
        _add_dim(msp, (sx0 + unique_px[0] - half_p, sy_bot - lean - 380.0), (sx0 + unique_px[0] + half_p, sy_bot - lean - 380.0), -90.0, dimstyle="Dce_25MV")

    # Gọi thép T1, T2, B1, B2, Đai (`Dce_KhtThepDai`) bên phải mặt cắt (cách đều 175 mm theo Y, không đụng trên đài mỏng 500mm)
    call_x = sx1 + 360.0
    y_c0 = sy_top + 180.0
    _insert_rebar_callout(doc, msp, bars["T1"]["sh"], f"%%c{bars['T1']['dk']}", "L.TRÊN", call_x, y_c0, [(x_bar1 - 120.0, y_top_bar)], sheet_scale, bend_x=sx1 + 170.0)
    _insert_rebar_callout(doc, msp, bars["T2"]["sh"], f"%%c{bars['T2']['dk']}", "L.TRÊN", call_x, y_c0 - 175.0, [(x_bar1 - 75.0, y_top_bar - 24.0)], sheet_scale, bend_x=sx1 + 170.0)
    _insert_rebar_callout(doc, msp, bars["C"]["sh"], f"%%c{bars['C']['dk']}", "ĐAI C", call_x, y_c0 - 350.0, [(x_bar1, y_mid_tie)], sheet_scale, bend_x=sx1 + 170.0)
    _insert_rebar_callout(doc, msp, bars["B2"]["sh"], f"%%c{bars['B2']['dk']}", "L.DƯỚI", call_x, y_c0 - 525.0, [(x_bar1 - 75.0, y_bot_bar + 24.0)], sheet_scale, bend_x=sx1 + 170.0)
    _insert_rebar_callout(doc, msp, bars["B1"]["sh"], f"%%c{bars['B1']['dk']}", "L.DƯỚI", call_x, y_c0 - 700.0, [(x_bar1 - 120.0, y_bot_bar)], sheet_scale, bend_x=sx1 + 170.0)

    _add_text(
        msp,
        f"MẶT CẮT {sec_name}",
        (sx0 + sx1) / 2.0,
        sy_bot - lean - 640.0,
        75.0,
        layer="DCE_Name",
        halign="MIDDLE_CENTER",
    )


def _draw_beam_section(
    doc,
    msp,
    beam: Dict[str, Any],
    cx: float,
    cy: float,
    sheet_scale: float = 25.0,
) -> None:
    """Vẽ mặt cắt ngang giằng móng (300x500 / 200x400) TL 1/25 kèm thép chủ & thép đai."""
    b = float(beam["b"])
    h = float(beam["h"])
    cover = 30.0
    x0, y0 = cx - b / 2.0, cy - h / 2.0
    x1, y1 = cx + b / 2.0, cy + h / 2.0

    _rect_poly(msp, x0, y0, x1, y1, layer="DCE_BaoBeTong")
    _add_hatch_poly(msp, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pattern="ANSI31", scale=12.0, angle=45.0, layer="DCE_Hatch")
    # Đai kín bên trong
    _rect_poly(msp, x0 + cover, y0 + cover, x1 - cover, y1 - cover, layer="DCE_ThepDai", const_width=8.0)

    # Thép chủ trên / dưới / hông
    n_top = int(beam["n_top"])
    n_bot = int(beam["n_bot"])
    top_xs = [x0 + cover + 18.0 + i * ((b - 2 * cover - 36.0) / max(1, n_top - 1)) for i in range(n_top)]
    bot_xs = [x0 + cover + 18.0 + i * ((b - 2 * cover - 36.0) / max(1, n_bot - 1)) for i in range(n_bot)]
    for tx in top_xs:
        _insert_rebar_dot(doc, msp, tx, y1 - cover - 18.0, dot_scale=16.0)
    for bx in bot_xs:
        _insert_rebar_dot(doc, msp, bx, y0 + cover + 18.0, dot_scale=16.0)
    if beam.get("has_side"):
        _insert_rebar_dot(doc, msp, x0 + cover + 18.0, cy, dot_scale=13.0)
        _insert_rebar_dot(doc, msp, x1 - cover - 18.0, cy, dot_scale=13.0)

    _add_dim(msp, (x0, y1), (x1, y1), 150.0, dimstyle="Dce_25MV")
    _add_dim(msp, (x0 + cover, y1 - cover), (x1 - cover, y1 - cover), 75.0, dimstyle="Dce_25MV")
    _add_dim(msp, (x0, y0), (x0, y1), -150.0, dimstyle="Dce_25MV")
    _add_dim(msp, (x0, y0 + cover), (x0, y1 - cover), -75.0, dimstyle="Dce_25MV")
    _insert_elev(doc, msp, "-1.450", x0, y1, sheet_scale)

    tag_x = x1 + 260.0
    _insert_rebar_callout(doc, msp, beam["top_sh"], beam["top_label"], "TRÊN", tag_x, y1 + 30.0, [(top_xs[-1], y1 - cover - 18.0)], sheet_scale, bend_x=x1 + 90.0)
    _insert_rebar_callout(doc, msp, beam["st_sh"], beam["st_label"], "ĐAI", tag_x, cy + 50.0, [(x1 - cover, cy + 40.0)], sheet_scale, bend_x=x1 + 90.0)
    _insert_rebar_callout(doc, msp, beam["bot_sh"], beam["bot_label"], "DƯỚI", tag_x, y0 + 50.0, [(bot_xs[-1], y0 + cover + 18.0)], sheet_scale, bend_x=x1 + 90.0)

    _add_text(
        msp,
        f"{beam['name']} ({int(b)}x{int(h)})",
        cx,
        y0 - 200.0,
        70.0,
        layer="DCE_Name",
        halign="MIDDLE_CENTER",
    )


def _draw_elevator_pit_detail(
    doc,
    msp,
    origin_x: float,
    base_y: float,
    sheet_scale: float = 25.0,
) -> None:
    """Vẽ ĐM.TM hố thang máy 1550x1500 (đáy -2.950 lên mặt giằng -1.450, 3 cọc 250x250)."""
    w, h = 1550.0, 1500.0
    wall_t = 200.0
    cap_t = 700.0
    pit_h = 1500.0
    lean = 100.0
    half_p = 125.0
    piles = [(400.0, 375.0), (1150.0, 375.0), (775.0, 1125.0)]

    # 1. Mặt bằng DM.TM (trái)
    px0, py0 = origin_x, base_y + 150.0
    px1, py1 = px0 + w, py0 + h
    _rect_poly(msp, px0, py0, px1, py1, layer="DCE_BaoBeTong")
    _rect_poly(msp, px0 + wall_t, py0 + wall_t, px1 - wall_t, py1 - wall_t, layer="DCE_NetThay")
    _rect_poly(msp, px0 - lean, py0 - lean, px1 + lean, py1 + lean, layer="DCE_NetDut")
    for ux, uy in piles:
        cx, cy = px0 + ux, py0 + uy
        _rect_poly(msp, cx - half_p, cy - half_p, cx + half_p, cy + half_p, layer="DCE_Coc")
        msp.add_line((cx - 165, cy), (cx + 165, cy), dxfattribs={"layer": "DCE_NetDut"})
        msp.add_line((cx, cy - 165), (cx, cy + 165), dxfattribs={"layer": "DCE_NetDut"})

    ccy = (py0 + py1) / 2.0
    msp.add_line((px0 - 220, ccy), (px1 + 220, ccy), dxfattribs={"layer": "DCE_NetDut"})
    _insert_section_tag(doc, msp, "4", px0 - 180.0, ccy, sheet_scale, rotation=90.0)
    _insert_section_tag(doc, msp, "4", px1 + 180.0, ccy, sheet_scale, rotation=90.0)

    _add_dim(msp, (px0, py0 - lean), (px1, py0 - lean), -240.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0, py0 - lean), (px0 + 400.0, py0 - lean), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 + 400.0, py0 - lean), (px0 + 1150.0, py0 - lean), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 + 1150.0, py0 - lean), (px1, py0 - lean), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, py0), (px0 - lean, py1), -240.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, py0), (px0 - lean, py0 + 375.0), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 - lean, py0 + 375.0), (px0 - lean, py0 + 1125.0), -120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0 + wall_t, py1), (px1 - wall_t, py1), 120.0, dimstyle="Dce_25MV")
    _add_dim(msp, (px0, py1), (px0 + wall_t, py1), 120.0, dimstyle="Dce_25MV")
    _add_text(msp, "MẶT BẰNG ĐÀI HỐ THANG ĐM.TM (SL=1)", (px0 + px1) / 2.0, py0 - lean - 420.0, 72.0, layer="DCE_Name", halign="MIDDLE_CENTER")

    # 2. Mặt cắt MC 4-4 (phải)
    sx0 = px1 + 720.0
    sx1 = sx0 + w
    sy_cap_bot = base_y + 150.0
    sy_cap_top = sy_cap_bot + cap_t
    sy_pit_top = sy_cap_bot + pit_h  # -2.950 + 1.500 = -1.450

    pit_pts = [
        (sx0, sy_cap_bot), (sx1, sy_cap_bot),
        (sx1, sy_pit_top), (sx1 - wall_t, sy_pit_top),
        (sx1 - wall_t, sy_cap_top), (sx0 + wall_t, sy_cap_top),
        (sx0 + wall_t, sy_pit_top), (sx0, sy_pit_top),
    ]
    msp.add_lwpolyline(pit_pts, close=True, dxfattribs={"layer": "DCE_BaoBeTong"})
    _add_hatch_poly(
        msp,
        [(sx0, sy_cap_top), (sx0 + wall_t, sy_cap_top), (sx0 + wall_t, sy_pit_top), (sx0, sy_pit_top)],
        pattern="SOLID",
        color=8,
        layer="DCE_Hatch",
    )
    _rect_poly(msp, sx0 - lean, sy_cap_bot - lean, sx1 + lean, sy_cap_bot, layer="DCE_NetThay")
    _add_hatch_poly(msp, [(sx0 - lean, sy_cap_bot - lean), (sx1 + lean, sy_cap_bot - lean), (sx1 + lean, sy_cap_bot), (sx0 - lean, sy_cap_bot)], pattern="ANSI31", scale=1.6, angle=45.0, layer="DCE_Hatch")

    for ux in (400.0, 1150.0):
        cx_s = sx0 + ux
        _rect_poly(msp, cx_s - half_p, sy_cap_bot - lean - 320.0, cx_s + half_p, sy_cap_bot + 100.0, layer="DCE_Coc")

    # Thép đáy U ngửa + thép vách U đứng
    msp.add_lwpolyline([(sx0 + 50, sy_cap_bot + 480), (sx0 + 50, sy_cap_bot + 55), (sx1 - 50, sy_cap_bot + 55), (sx1 - 50, sy_cap_bot + 480)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0})
    msp.add_lwpolyline([(sx0 + 50, sy_cap_top - 55), (sx1 - 50, sy_cap_top - 55)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 12.0})
    for wx in (sx0 + 45.0, sx0 + wall_t - 45.0, sx1 - wall_t + 45.0, sx1 - 45.0):
        msp.add_lwpolyline([(wx, sy_cap_bot + 70.0), (wx, sy_pit_top - 45.0)], dxfattribs={"layer": "DCE_ThepChu"})
    for di in range(6):
        dx = sx0 + 130.0 + di * ((w - 260.0) / 5.0)
        _insert_rebar_dot(doc, msp, dx, sy_cap_bot + 80.0, dot_scale=17.0)
        _insert_rebar_dot(doc, msp, dx, sy_cap_top - 80.0, dot_scale=17.0)

    _insert_elev(doc, msp, "-1.450", sx0 - 20.0, sy_pit_top, sheet_scale)
    _insert_elev(doc, msp, "-2.950", sx0 - 20.0, sy_cap_bot, sheet_scale)
    _add_dim(msp, (sx0, sy_cap_bot), (sx0, sy_cap_top), -140.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0, sy_cap_top), (sx0, sy_pit_top), -140.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0, sy_cap_bot), (sx0, sy_pit_top), -260.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0 - lean, sy_cap_bot - lean), (sx0 - lean, sy_cap_bot), -140.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0 + wall_t, sy_pit_top), (sx1 - wall_t, sy_pit_top), 130.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0, sy_pit_top), (sx1, sy_pit_top), 240.0, dimstyle="Dce_25MV")
    _add_dim(msp, (sx0 + 400.0, sy_cap_bot - lean), (sx0 + 1150.0, sy_cap_bot - lean), -160.0, dimstyle="Dce_25MV")

    call_x = sx1 + 330.0
    _insert_rebar_callout(doc, msp, "5", "%%c12a150", "VÁCH", call_x, sy_pit_top - 180.0, [(sx1 - 45.0, sy_pit_top - 220.0)], sheet_scale, bend_x=sx1 + 140.0)
    _insert_rebar_callout(doc, msp, "2", "%%c12a150", "L.TRÊN", call_x, sy_cap_top + 40.0, [(sx1 - 140.0, sy_cap_top - 55.0)], sheet_scale, bend_x=sx1 + 140.0)
    _insert_rebar_callout(doc, msp, "1", "%%c16a150", "L.DƯỚI", call_x, sy_cap_bot + 160.0, [(sx1 - 140.0, sy_cap_bot + 55.0)], sheet_scale, bend_x=sx1 + 140.0)
    _add_text(msp, "MẶT CẮT 4-4 (ĐÀI HỐ THANG)", (sx0 + sx1) / 2.0, sy_cap_bot - lean - 380.0, 72.0, layer="DCE_Name", halign="MIDDLE_CENTER")


# ==============================================================================
# CỤM BẢN VẼ 2: CHI TIẾT CỘT VÁCH (KC.08, KC.09 — TL 1/50 + MC 1/25)
# ==============================================================================

_COLUMN_LEVELS = [
    ("-1.400", 0.0, "TẦNG HẦM", 2550.0),
    ("+1.150", 2550.0, "TẦNG 1", 3050.0),
    ("+4.200", 5600.0, "LỬNG", 2800.0),
    ("+7.000", 8400.0, "TẦNG 2", 3400.0),
    ("+10.400", 11800.0, "TẦNG 3", 3400.0),
    ("+13.800", 15200.0, "TẦNG 4", 3400.0),
    ("+17.200", 18600.0, "SÂN THƯỢNG", 3000.0),
    ("+20.200", 21600.0, "TUM MÁI", 0.0),
]


def _draw_column_cross_section_25(
    doc,
    msp,
    sec: Dict[str, Any],
    cx: float,
    cy: float,
    sheet_scale: float = 50.0,
) -> None:
    """Vẽ Mặt cắt cột TL 1/25 trên bản vẽ TL 1/50 (zoom 2.0x, `DIMLFAC=0.5` đọc đúng kích thước thật mm)."""
    zoom = 2.0
    b_real = float(sec["b"])
    h_real = float(sec["h"])
    b = b_real * zoom
    h = h_real * zoom
    cov = 25.0 * zoom
    x0, y0 = cx - b / 2.0, cy - h / 2.0
    x1, y1 = cx + b / 2.0, cy + h / 2.0

    _rect_poly(msp, x0, y0, x1, y1, layer="DCE_Cot")
    _add_hatch_poly(msp, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pattern="ANSI31", scale=18.0, angle=45.0, layer="DCE_Hatch")
    # Đai bao ngoài
    _rect_poly(msp, x0 + cov, y0 + cov, x1 - cov, y1 - cov, layer="DCE_ThepDai", const_width=14.0)

    # Bố trí thép chủ theo mặt dọc y (n_bars = 6, 8, 10)
    n_tot = int(sec["n_bars"])
    n_per_face = max(2, n_tot // 2)
    xs_face = (x0 + cov + 24.0, x1 - cov - 24.0)
    ys_face = [y0 + cov + 24.0 + i * ((h - 2 * cov - 48.0) / max(1, n_per_face - 1)) for i in range(n_per_face)]
    for yy in ys_face:
        _insert_rebar_dot(doc, msp, xs_face[0], yy, dot_scale=28.0)
        _insert_rebar_dot(doc, msp, xs_face[1], yy, dot_scale=28.0)
        if n_per_face >= 3 and yy not in (ys_face[0], ys_face[-1]):
            msp.add_lwpolyline([(xs_face[0], yy), (xs_face[1], yy)], dxfattribs={"layer": "DCE_ThepDai"})

    # Kích thước đọc đúng giá trị thật (`dimlfac=0.5`)
    _add_dim(msp, (x0, y1), (x1, y1), 170.0, dimstyle="Dce_50MV", dimlfac=0.5)
    _add_dim(msp, (x0, y0), (x0, y1), -170.0, dimstyle="Dce_50MV", dimlfac=0.5)

    _add_text(msp, sec["label"], cx, y0 - 200.0, 90.0, layer="DCE_Name", width=0.78, halign="MIDDLE_CENTER")
    _add_text(msp, sec["rebar_label"], cx, y0 - 380.0, 82.0, layer="Dce_text", width=0.78, halign="MIDDLE_CENTER")


def _draw_column_panel(
    doc,
    msp,
    col_spec: Dict[str, Any],
    panel_x0: float,
    sheet_scale: float = 50.0,
) -> None:
    """Vẽ 1 cột hoàn chỉnh (-1.400 -> +20.200) chia 2 băng đứng gọn + 3 Mặt cắt TL 1/25."""
    name = col_spec["name"]
    sl_count = int(col_spec["sl"])
    tiers = col_spec["tiers"]  # list of (z_start, z_end, b, h, n_bars, dia, st_spec)

    def _tier_for_z(z: float) -> Tuple[float, float, int, int, str]:
        for zs, ze, b, h, nb, d, st in tiers:
            if zs - 1e-6 <= z < ze - 1e-6:
                return float(b), float(h), int(nb), int(d), str(st)
        zs, ze, b, h, nb, d, st = tiers[-1]
        return float(b), float(h), int(nb), int(d), str(st)

    # Hai băng cao độ nằm song song theo phương X (dịch gọn để callout bên phải cách bảng BBS >= 300mm):
    # Băng 1: HẦM (-1.400) -> TẦNG 3 (+10.400) [0 .. 11800] đặt tại y_origin = 1400 (đỉnh 13200)
    # Băng 2: TẦNG 3 (+10.400) -> TUM MÁI (+20.200) [11800 .. 21600] đặt tại y_origin = 3950 (đỉnh 13750)
    strips = [
        {"x_cx": panel_x0 + 1180.0, "z0": 0.0, "z1": 11800.0, "y_base": 1400.0, "idx0": 0, "idx1": 4},
        {"x_cx": panel_x0 + 3580.0, "z0": 11800.0, "z1": 21600.0, "y_base": 3950.0, "idx0": 4, "idx1": 7},
    ]

    for s_idx, st in enumerate(strips):
        xc = st["x_cx"]
        y_base = st["y_base"]
        z0 = st["z0"]

        # Cột mặt cắt ngang dầm sàn & thân cột từng tầng trong băng
        for lv_i in range(st["idx0"], st["idx1"]):
            ct_txt, lv_z, lv_name, fl_h = _COLUMN_LEVELS[lv_i]
            next_ct, next_z, _, _ = _COLUMN_LEVELS[lv_i + 1]
            b_mm, h_mm, nb, dia, st_spec = _tier_for_z(lv_z)
            # Vẽ chiều cao cột theo bề rộng h_mm (lớn hơn, thấy rõ 2 mặt thép chủ)
            yy0 = y_base + (lv_z - z0)
            yy1 = y_base + (next_z - z0)
            _rect_poly(msp, xc - h_mm / 2.0, yy0, xc + h_mm / 2.0, yy1, layer="DCE_Cot")
            # Bản sàn dày 150mm tại đáy và đỉnh tầng (Solid Hatch xám chuẩn DCE_Hatch color=8)
            slab_pts = [
                (xc - h_mm / 2.0 - 240.0, yy0 - 150.0),
                (xc + h_mm / 2.0 + 240.0, yy0 - 150.0),
                (xc + h_mm / 2.0 + 240.0, yy0),
                (xc - h_mm / 2.0 - 240.0, yy0),
            ]
            msp.add_lwpolyline(slab_pts, close=True, dxfattribs={"layer": "DCE_BaoBeTong"})
            _add_hatch_poly(msp, slab_pts, pattern="SOLID", color=8, layer="DCE_Hatch")
            if lv_i == st["idx1"] - 1:
                top_slab_pts = [
                    (xc - h_mm / 2.0 - 240.0, yy1 - 150.0),
                    (xc + h_mm / 2.0 + 240.0, yy1 - 150.0),
                    (xc + h_mm / 2.0 + 240.0, yy1),
                    (xc - h_mm / 2.0 - 240.0, yy1),
                ]
                msp.add_lwpolyline(top_slab_pts, close=True, dxfattribs={"layer": "DCE_BaoBeTong"})
                _add_hatch_poly(msp, top_slab_pts, pattern="SOLID", color=8, layer="DCE_Hatch")

            # Thép chủ 2 biên cột (LWPOLYLINE)
            cov_line = 38.0
            msp.add_lwpolyline([(xc - h_mm / 2.0 + cov_line, yy0), (xc - h_mm / 2.0 + cov_line, yy1)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 16.0})
            msp.add_lwpolyline([(xc + h_mm / 2.0 - cov_line, yy0), (xc + h_mm / 2.0 - cov_line, yy1)], dxfattribs={"layer": "DCE_ThepChu", "const_width": 16.0})

            # Vạch đai đại diện (3 vạch vùng nút dày a100 + 2 vạch vùng giữa a200) bằng LWPOLYLINE + Dim vùng nối/tăng cường
            x_tie0 = xc - h_mm / 2.0 + cov_line
            x_tie1 = xc + h_mm / 2.0 - cov_line
            for dz in (120.0, 260.0, 400.0, 600.0, fl_h / 2.0 - 150.0, fl_h / 2.0 + 150.0, fl_h - 600.0, fl_h - 400.0, fl_h - 260.0):
                msp.add_lwpolyline([(x_tie0, yy0 + dz), (x_tie1, yy0 + dz)], dxfattribs={"layer": "DCE_ThepDai"})

            # Cao trình & Dim chiều cao tầng + vùng tăng cường đầu/chân cột bên trái băng
            _insert_elev(doc, msp, ct_txt, xc - h_mm / 2.0 - 200.0, yy0, sheet_scale)
            _add_dim(msp, (xc - h_mm / 2.0 - 260.0, yy0), (xc - h_mm / 2.0 - 260.0, yy1), -420.0, dimstyle="Dce_50MV")
            _add_dim(msp, (xc + h_mm / 2.0 + 90.0, yy0), (xc + h_mm / 2.0 + 90.0, yy0 + 600.0), 180.0, dimstyle="Dce_50MV")
            # Gọi thép tầng 1 (băng 1, tránh vùng mặt cắt phía dưới) & tầng 3 (băng 2)
            if lv_i in (1, 4, 5):
                _insert_rebar_callout(
                    doc,
                    msp,
                    f"{lv_i + 1}",
                    f"{nb}%%c{dia}",
                    lv_name,
                    xc + h_mm / 2.0 + 420.0,
                    (yy0 + yy1) / 2.0 + 180.0,
                    [(x_tie1, (yy0 + yy1) / 2.0)],
                    sheet_scale,
                    bend_x=xc + h_mm / 2.0 + 210.0,
                )
            if lv_i == st["idx1"] - 1:
                _insert_elev(doc, msp, next_ct, xc - h_mm / 2.0 - 200.0, yy1, sheet_scale)
                _insert_rebar_callout(
                    doc,
                    msp,
                    "Đ",
                    st_spec,
                    "",
                    xc + h_mm / 2.0 + 420.0,
                    yy1 - 360.0,
                    [(x_tie1, yy1 - 260.0)],
                    sheet_scale,
                    bend_x=xc + h_mm / 2.0 + 210.0,
                )

    # Tiêu đề cột nằm gọn phía trên cả 2 băng (y = 14300 <= 14600)
    _add_text(
        msp,
        f"CHI TIẾT CỘT {name} (SL={sl_count})",
        panel_x0 + 2600.0,
        14280.0,
        240.0,
        layer="DCE_Name",
        halign="MIDDLE_CENTER",
    )

    # 3 Mặt cắt TL 1/25 cách đều 1320mm bên dưới Băng 2 (tách hoàn toàn khỏi sàn +10.400 và Băng 1)
    sec_xs = [panel_x0 + 2350.0, panel_x0 + 3670.0, panel_x0 + 4990.0]
    for sec, scx in zip(col_spec["sections"], sec_xs):
        _draw_column_cross_section_25(doc, msp, sec, scx, 1950.0, sheet_scale=sheet_scale)


# ==============================================================================
# DỮ LIỆU KỸ THUẬT CHUẨN DỰ ÁN NHÀ PHỐ Q2 CÁT LÁI (KC.03, KC.04, KC.08, KC.09)
# ==============================================================================

DEFAULT_CATLAI_PROJECT: Dict[str, Any] = {
    "project_name": "NHÀ Ở RIÊNG LẺ",
    "investor": "",
    "site_address_lines": ["THỬA 1039 TỜ BẢN ĐỒ 20", "PHƯỜNG CÁT LÁI, TP.HCM"],
    "company": "",
    "director": "",
    "reviewer": "",
    "designer": "",
    "drafter": "",
    "drawing_category": "BẢN VẼ KẾT CẤU",
    "design_stage": "TKTC",
    "year": "2026",
}


def _spec_kc03() -> Dict[str, Any]:
    caps = [
        {
            "name": "DM.01", "sl": 2, "w": 650, "h": 850, "thick": 500, "lean": 100, "cover": 50,
            "piles": [(325, 425)], "pile_size": 250, "top_elev": "-0.050", "bot_elev": "-0.550",
            "sec_name": "1-1", "sec_num": "1", "chamfer": 0, "col_sz": (200, 400), "hook": 320,
            "bars": {
                "T1": {"sh": "1", "dk": "14a150"}, "T2": {"sh": "2", "dk": "12a200"},
                "B1": {"sh": "3", "dk": "12a200"}, "B2": {"sh": "4", "dk": "12a200"},
                "C": {"sh": "5", "dk": "10a250"},
            },
        },
        {
            "name": "DM.02", "sl": 8, "w": 1400, "h": 1500, "thick": 700, "lean": 100, "cover": 50,
            "piles": [(325, 750), (1075, 750)], "pile_size": 250, "top_elev": "-1.450", "bot_elev": "-2.150",
            "sec_name": "2-2", "sec_num": "2", "chamfer": 250, "col_sz": (200, 500), "hook": 360,
            "bars": {
                "T1": {"sh": "6", "dk": "16a150"}, "T2": {"sh": "7", "dk": "12a150"},
                "B1": {"sh": "8", "dk": "16a150"}, "B2": {"sh": "9", "dk": "12a150"},
                "C": {"sh": "10", "dk": "10a250"},
            },
        },
        {
            "name": "DM.03", "sl": 2, "w": 1400, "h": 1500, "thick": 700, "lean": 100, "cover": 50,
            "piles": [(325, 750), (1075, 750)], "pile_size": 250, "top_elev": "-1.450", "bot_elev": "-2.150",
            "sec_name": "3-3", "sec_num": "3", "chamfer": 0, "col_sz": (200, 500), "hook": 480,
            "bars": {
                "T1": {"sh": "11", "dk": "16a150"}, "T2": {"sh": "12", "dk": "16a150"},
                "B1": {"sh": "13", "dk": "16a150"}, "B2": {"sh": "14", "dk": "12a150"},
                "C": {"sh": "15", "dk": "10a250"},
            },
        },
    ]
    bbs_rows = [
        # DM.01 (SL=2)
        {"member": "DM01", "member_title": "ĐÀI\nDM.01\n(SL=2)", "sh": "1", "tk_block": "TK4", "dims_mm": {"L1": 240, "L2": 550, "L3": 240}, "dia_mm": 14, "sl": 6, "skc": 2},
        {"member": "DM01", "member_title": "ĐÀI\nDM.01\n(SL=2)", "sh": "2", "tk_block": "TK4", "dims_mm": {"L1": 220, "L2": 750, "L3": 220}, "dia_mm": 12, "sl": 4, "skc": 2},
        {"member": "DM01", "member_title": "ĐÀI\nDM.01\n(SL=2)", "sh": "3", "tk_block": "TK7", "dims_mm": {"L1": 320, "L2": 550, "L3": 320}, "dia_mm": 12, "sl": 5, "skc": 2},
        {"member": "DM01", "member_title": "ĐÀI\nDM.01\n(SL=2)", "sh": "4", "tk_block": "TK7", "dims_mm": {"L1": 320, "L2": 750, "L3": 320}, "dia_mm": 12, "sl": 4, "skc": 2},
        {"member": "DM01", "member_title": "ĐÀI\nDM.01\n(SL=2)", "sh": "5", "tk_block": "TK9", "dims_mm": {"L1": 550, "L2": 750, "M": 120}, "dia_mm": 10, "sl": 2, "skc": 2},
        # DM.02 (SL=8)
        {"member": "DM02", "member_title": "ĐÀI\nDM.02\n(SL=8)", "sh": "6", "tk_block": "TK4", "dims_mm": {"L1": 360, "L2": 1300, "L3": 360}, "dia_mm": 16, "sl": 10, "skc": 8},
        {"member": "DM02", "member_title": "ĐÀI\nDM.02\n(SL=8)", "sh": "7", "tk_block": "TK4", "dims_mm": {"L1": 360, "L2": 1400, "L3": 360}, "dia_mm": 12, "sl": 9, "skc": 8},
        {"member": "DM02", "member_title": "ĐÀI\nDM.02\n(SL=8)", "sh": "8", "tk_block": "TK7", "dims_mm": {"L1": 360, "L2": 1300, "L3": 360}, "dia_mm": 16, "sl": 10, "skc": 8},
        {"member": "DM02", "member_title": "ĐÀI\nDM.02\n(SL=8)", "sh": "9", "tk_block": "TK7", "dims_mm": {"L1": 360, "L2": 1400, "L3": 360}, "dia_mm": 12, "sl": 9, "skc": 8},
        {"member": "DM02", "member_title": "ĐÀI\nDM.02\n(SL=8)", "sh": "10", "tk_block": "TK9", "dims_mm": {"L1": 1300, "L2": 1400, "M": 120}, "dia_mm": 10, "sl": 2, "skc": 8},
        # DM.03 (SL=2)
        {"member": "DM03", "member_title": "ĐÀI\nDM.03\n(SL=2)", "sh": "11", "tk_block": "TK4", "dims_mm": {"L1": 480, "L2": 1300, "L3": 480}, "dia_mm": 16, "sl": 10, "skc": 2},
        {"member": "DM03", "member_title": "ĐÀI\nDM.03\n(SL=2)", "sh": "12", "tk_block": "TK4", "dims_mm": {"L1": 480, "L2": 1400, "L3": 480}, "dia_mm": 16, "sl": 10, "skc": 2},
        {"member": "DM03", "member_title": "ĐÀI\nDM.03\n(SL=2)", "sh": "13", "tk_block": "TK7", "dims_mm": {"L1": 480, "L2": 1300, "L3": 480}, "dia_mm": 16, "sl": 10, "skc": 2},
        {"member": "DM03", "member_title": "ĐÀI\nDM.03\n(SL=2)", "sh": "14", "tk_block": "TK7", "dims_mm": {"L1": 480, "L2": 1400, "L3": 480}, "dia_mm": 12, "sl": 9, "skc": 2},
        {"member": "DM03", "member_title": "ĐÀI\nDM.03\n(SL=2)", "sh": "15", "tk_block": "TK9", "dims_mm": {"L1": 1300, "L2": 1400, "M": 120}, "dia_mm": 10, "sl": 2, "skc": 2},
    ]
    return {
        "sheet_no": "KC.03",
        "filename": "KC-03_ChiTietMong_1.dxf",
        "title": "CHI TIẾT MÓNG 1",
        "scale": 25.0,
        "caps": caps,
        "bbs_rows": bbs_rows,
        "notes_title": "GHI CHÚ CHI TIẾT ĐÀI CỌC (KC.03)",
        "notes": [
            "1. Vật liệu: Bê tông đài cọc cấp bền B25 (M300), bê tông lót đá 1x2 B7.5 (M100) dày 100 mm.",
            "2. Cốt thép: D <= 10 dùng thép trơn CB240-T; D >= 12 dùng thép gân CB400-V theo TCVN 1651-2:2018.",
            "3. Lớp bê tông bảo vệ a_bv = 50 mm đối với mặt tiếp đất đáy đài; a_bv = 35 mm đối với mặt thành đài.",
            "4. Cọc BTCT 250x250 ngàm vào đài 100 mm; đập đầu cọc giữ cốt thép neo thẳng >= 360 mm.",
            "5. Toàn bộ chiều dài thanh trên bảng thống kê tính theo hình học thực + móc uốn chuẩn Form_04.",
        ],
    }


def _spec_kc04() -> Dict[str, Any]:
    beams = [
        {"name": "GMX.1", "b": 300, "h": 500, "n_top": 3, "n_bot": 3, "has_side": True, "top_sh": "7", "top_label": "3%%c16", "bot_sh": "8", "bot_label": "3%%c16", "st_sh": "9", "st_label": "%%c10a100/200"},
        {"name": "GMX.2", "b": 200, "h": 400, "n_top": 3, "n_bot": 2, "has_side": False, "top_sh": "10", "top_label": "3%%c16", "bot_sh": "11", "bot_label": "2%%c16", "st_sh": "12", "st_label": "%%c10a100/200"},
        {"name": "GMY.1", "b": 300, "h": 500, "n_top": 3, "n_bot": 3, "has_side": True, "top_sh": "13", "top_label": "3%%c16", "bot_sh": "14", "bot_label": "3%%c16", "st_sh": "9", "st_label": "%%c10a100/200"},
        {"name": "GMY.2", "b": 300, "h": 500, "n_top": 3, "n_bot": 4, "has_side": False, "top_sh": "13", "top_label": "3%%c16", "bot_sh": "14", "bot_label": "4%%c16", "st_sh": "9", "st_label": "%%c10a100/200"},
    ]
    bbs_rows = [
        # ĐM.TM (SL=1)
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "1", "tk_block": "TK7", "dims_mm": {"L1": 480, "L2": 1450, "L3": 480}, "dia_mm": 16, "sl": 11, "skc": 1},
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "2", "tk_block": "TK7", "dims_mm": {"L1": 480, "L2": 1400, "L3": 480}, "dia_mm": 16, "sl": 11, "skc": 1},
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "3", "tk_block": "TK4", "dims_mm": {"L1": 350, "L2": 1450, "L3": 350}, "dia_mm": 12, "sl": 10, "skc": 1},
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "4", "tk_block": "TK4", "dims_mm": {"L1": 350, "L2": 1400, "L3": 350}, "dia_mm": 12, "sl": 10, "skc": 1},
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "5", "tk_block": "TK5", "dims_mm": {"L1": 320, "L2": 1420}, "dia_mm": 12, "sl": 36, "skc": 1},
        {"member": "DMTM", "member_title": "ĐÀI\nHỐ\nTHANG\nĐM.TM\n(SL=1)", "sh": "6", "tk_block": "TK9", "dims_mm": {"L1": 1450, "L2": 1400, "M": 120}, "dia_mm": 10, "sl": 5, "skc": 1},
        # GMX.1 (300x500, L=12.6m)
        {"member": "GMX1", "member_title": "GIẰNG\nGMX.1\n(SL=3)", "sh": "7", "tk_block": "TK5", "dims_mm": {"L1": 420, "L2": 4200}, "dia_mm": 16, "sl": 3, "skc": 3},
        {"member": "GMX1", "member_title": "GIẰNG\nGMX.1\n(SL=3)", "sh": "8", "tk_block": "TK2", "dims_mm": {"L1": 420, "L2": 4200}, "dia_mm": 16, "sl": 3, "skc": 3},
        {"member": "GMX1", "member_title": "GIẰNG\nGMX.1\n(SL=3)", "sh": "9", "tk_block": "TK9", "dims_mm": {"L1": 240, "L2": 440, "M": 120}, "dia_mm": 10, "sl": 28, "skc": 3},
        # GMX.2 (200x400)
        {"member": "GMX2", "member_title": "GIẰNG\nGMX.2\n(SL=2)", "sh": "10", "tk_block": "TK5", "dims_mm": {"L1": 320, "L2": 4000}, "dia_mm": 16, "sl": 3, "skc": 2},
        {"member": "GMX2", "member_title": "GIẰNG\nGMX.2\n(SL=2)", "sh": "11", "tk_block": "TK2", "dims_mm": {"L1": 320, "L2": 4000}, "dia_mm": 16, "sl": 2, "skc": 2},
        {"member": "GMX2", "member_title": "GIẰNG\nGMX.2\n(SL=2)", "sh": "12", "tk_block": "TK9", "dims_mm": {"L1": 140, "L2": 340, "M": 120}, "dia_mm": 10, "sl": 26, "skc": 2},
        # GMY.1/2 (300x500)
        {"member": "GMY", "member_title": "GIẰNG\nGMY.1/2\n(SL=4)", "sh": "13", "tk_block": "TK1", "dims_mm": {"L": 4400}, "dia_mm": 16, "sl": 3, "skc": 4},
        {"member": "GMY", "member_title": "GIẰNG\nGMY.1/2\n(SL=4)", "sh": "14", "tk_block": "TK1", "dims_mm": {"L": 4400}, "dia_mm": 16, "sl": 4, "skc": 4},
    ]
    return {
        "sheet_no": "KC.04",
        "filename": "KC-04_ChiTietMong_2.dxf",
        "title": "CHI TIẾT MÓNG 2",
        "scale": 25.0,
        "beams": beams,
        "bbs_rows": bbs_rows,
        "notes_title": "GHI CHÚ ĐÀI HỐ THANG & GIẰNG MÓNG (KC.04)",
        "notes": [
            "1. ĐM.TM (1550x1500x700) đáy -2.950, vách pit dày 200 cao lên -1.450, 3 cọc 250x250.",
            "2. Đổ bê tông hố thang kết hợp băng cản nước PVC chống thấm mạch ngừng vách đáy.",
            "3. Giằng móng GMX/GMY bố trí thép đai %%c10a100 vùng gối (L/4 mỗi đầu), %%c10a200 giữa nhịp.",
            "4. Thép chủ giằng móng neo vào đài cọc tối thiểu 40d (640 mm với thanh %%c16).",
        ],
    }


def _spec_kc08() -> Dict[str, Any]:
    c1 = {
        "name": "C1", "sl": 2,
        "tiers": [
            (0.0, 8400.0, 200, 400, 8, 20, "%%c8a100/200"),
            (8400.0, 15200.0, 200, 400, 8, 16, "%%c8a100/200"),
            (15200.0, 21600.0, 200, 300, 6, 16, "%%c8a100/200"),
        ],
        "sections": [
            {"b": 200, "h": 400, "n_bars": 8, "label": "MC C1 (HẦM - T2)", "rebar_label": "8%%c20 | %%c8a100/200"},
            {"b": 200, "h": 400, "n_bars": 8, "label": "MC C1 (T2 - T4)", "rebar_label": "8%%c16 | %%c8a100/200"},
            {"b": 200, "h": 300, "n_bars": 6, "label": "MC C1 (T4 - TUM)", "rebar_label": "6%%c16 | %%c8a100/200"},
        ],
    }
    c2 = {
        "name": "C2", "sl": 4,
        "tiers": [
            (0.0, 8400.0, 200, 500, 10, 20, "%%c8a100/200"),
            (8400.0, 15200.0, 200, 400, 8, 20, "%%c8a100/200"),
            (15200.0, 21600.0, 200, 300, 6, 16, "%%c8a100/200"),
        ],
        "sections": [
            {"b": 200, "h": 500, "n_bars": 10, "label": "MC C2 (HẦM - T2)", "rebar_label": "10%%c20 | %%c8a100/200"},
            {"b": 200, "h": 400, "n_bars": 8, "label": "MC C2 (T2 - T4)", "rebar_label": "8%%c20 | %%c8a100/200"},
            {"b": 200, "h": 300, "n_bars": 6, "label": "MC C2 (T4 - TUM)", "rebar_label": "6%%c16 | %%c8a100/200"},
        ],
    }
    bbs_rows = [
        # C1 (SL=2)
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "1", "tk_block": "TK1", "dims_mm": {"L": 9200}, "dia_mm": 20, "sl": 8, "skc": 2},
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "2", "tk_block": "TK1", "dims_mm": {"L": 7400}, "dia_mm": 16, "sl": 8, "skc": 2},
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "3", "tk_block": "TK5", "dims_mm": {"L1": 450, "L2": 6400}, "dia_mm": 16, "sl": 6, "skc": 2},
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "4", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 350, "M": 120}, "dia_mm": 8, "sl": 96, "skc": 2},
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "5", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 250, "M": 120}, "dia_mm": 8, "sl": 42, "skc": 2},
        {"member": "C1", "member_title": "CỘT C1\n(SL=2)", "sh": "6", "tk_block": "TK8", "dims_mm": {"L": 150, "M1": 80, "M2": 80}, "dia_mm": 8, "sl": 96, "skc": 2},
        # C2 (SL=4)
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "7", "tk_block": "TK1", "dims_mm": {"L": 9200}, "dia_mm": 20, "sl": 10, "skc": 4},
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "8", "tk_block": "TK1", "dims_mm": {"L": 7400}, "dia_mm": 20, "sl": 8, "skc": 4},
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "9", "tk_block": "TK5", "dims_mm": {"L1": 450, "L2": 6400}, "dia_mm": 16, "sl": 6, "skc": 4},
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "10", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 450, "M": 120}, "dia_mm": 8, "sl": 56, "skc": 4},
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "11", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 350, "M": 120}, "dia_mm": 8, "sl": 44, "skc": 4},
        {"member": "C2", "member_title": "CỘT C2\n(SL=4)", "sh": "12", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 250, "M": 120}, "dia_mm": 8, "sl": 42, "skc": 4},
    ]
    return {
        "sheet_no": "KC.08",
        "filename": "KC-08_ChiTietCotVach_1.dxf",
        "title": "CHI TIẾT CỘT VÁCH 1",
        "scale": 50.0,
        "columns": [c1, c2],
        "bbs_rows": bbs_rows,
        "notes_title": "GHI CHÚ CHI TIẾT CỘT C1 & C2 (KC.08)",
        "notes": [
            "1. Cao trình từ Hầm (-1.400) tới Tum Mái (+20.200) chia 2 băng để đọc rõ tại TL 1/50.",
            "2. Mặt cắt ngang cột vẽ tại TL 1/25 (`DIMLFAC=0.50`) bảo toàn kích thước đo thật (200x500/400/300).",
            "3. Nối chồng cốt thép cột tại vùng 1/3 giữa tầng, l_lap = 40d (>= 800 mm với %%c20), sole 50%.",
            "4. Vùng tăng cường đai cột (đầu và chân cột dài >= max(h_c, H/6, 550 mm)): bố trí %%c8a100.",
        ],
    }


def _spec_kc09() -> Dict[str, Any]:
    c3 = {
        "name": "C3", "sl": 2,
        "tiers": [
            (0.0, 8400.0, 200, 500, 10, 20, "%%c8a100/200"),
            (8400.0, 15200.0, 200, 400, 8, 20, "%%c8a100/200"),
            (15200.0, 21600.0, 200, 300, 6, 16, "%%c8a100/200"),
        ],
        "sections": [
            {"b": 200, "h": 500, "n_bars": 10, "label": "MC C3 (HẦM - T2)", "rebar_label": "10%%c20 | %%c8a100/200"},
            {"b": 200, "h": 400, "n_bars": 8, "label": "MC C3 (T2 - T4)", "rebar_label": "8%%c20 | %%c8a100/200"},
            {"b": 200, "h": 300, "n_bars": 6, "label": "MC C3 (T4 - TUM)", "rebar_label": "6%%c16 | %%c8a100/200"},
        ],
    }
    c3b = {
        "name": "C3B", "sl": 2,
        "tiers": [
            (0.0, 8400.0, 200, 400, 10, 20, "%%c8a100/200"),
            (8400.0, 15200.0, 200, 400, 8, 16, "%%c8a100/200"),
            (15200.0, 21600.0, 200, 300, 6, 16, "%%c8a100/200"),
        ],
        "sections": [
            {"b": 200, "h": 400, "n_bars": 10, "label": "MC C3B (HẦM - T2)", "rebar_label": "10%%c20 | %%c8a100/200"},
            {"b": 200, "h": 400, "n_bars": 8, "label": "MC C3B (T2 - T4)", "rebar_label": "8%%c16 | %%c8a100/200"},
            {"b": 200, "h": 300, "n_bars": 6, "label": "MC C3B (T4 - TUM)", "rebar_label": "6%%c16 | %%c8a100/200"},
        ],
    }
    bbs_rows = [
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "1", "tk_block": "TK1", "dims_mm": {"L": 9200}, "dia_mm": 20, "sl": 10, "skc": 2},
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "2", "tk_block": "TK1", "dims_mm": {"L": 7400}, "dia_mm": 20, "sl": 8, "skc": 2},
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "3", "tk_block": "TK5", "dims_mm": {"L1": 450, "L2": 6400}, "dia_mm": 16, "sl": 6, "skc": 2},
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "4", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 450, "M": 120}, "dia_mm": 8, "sl": 56, "skc": 2},
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "5", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 350, "M": 120}, "dia_mm": 8, "sl": 44, "skc": 2},
        {"member": "C3", "member_title": "CỘT C3\n(SL=2)", "sh": "6", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 250, "M": 120}, "dia_mm": 8, "sl": 42, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "7", "tk_block": "TK1", "dims_mm": {"L": 9200}, "dia_mm": 20, "sl": 10, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "8", "tk_block": "TK1", "dims_mm": {"L": 7400}, "dia_mm": 16, "sl": 8, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "9", "tk_block": "TK5", "dims_mm": {"L1": 450, "L2": 6400}, "dia_mm": 16, "sl": 6, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "10", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 350, "M": 120}, "dia_mm": 8, "sl": 96, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "11", "tk_block": "TK9", "dims_mm": {"L1": 150, "L2": 250, "M": 120}, "dia_mm": 8, "sl": 42, "skc": 2},
        {"member": "C3B", "member_title": "CỘT\nC3B\n(SL=2)", "sh": "12", "tk_block": "TK8", "dims_mm": {"L": 150, "M1": 80, "M2": 80}, "dia_mm": 8, "sl": 96, "skc": 2},
    ]
    return {
        "sheet_no": "KC.09",
        "filename": "KC-09_ChiTietCotVach_2.dxf",
        "title": "CHI TIẾT CỘT VÁCH 2",
        "scale": 50.0,
        "columns": [c3, c3b],
        "bbs_rows": bbs_rows,
        "notes_title": "GHI CHÚ CHI TIẾT CỘT C3 & C3B (KC.09)",
        "notes": [
            "1. Cao trình từ Hầm (-1.400) tới Tum Mái (+20.200) chia 2 băng để đọc rõ tại TL 1/50.",
            "2. Mặt cắt ngang cột vẽ tại TL 1/25 (`DIMLFAC=0.50`) bảo toàn kích thước đo thật.",
            "3. Chỗ giật tiết diện (500->400 ở T2 và 400->300 ở T4): uốn chuyển vị thanh chủ 1:6 trong nút dầm.",
            "4. Toàn bộ đai C trong C3B uốn móc 135 độ dài >= 10d = 80 mm neo vào lõi bê tông.",
        ],
    }


CATLAI_DETAIL_SPECS = {
    "KC.03": _spec_kc03,
    "KC.04": _spec_kc04,
    "KC.08": _spec_kc08,
    "KC.09": _spec_kc09,
}


def build_detail_sheet(
    sheet_spec: Dict[str, Any],
    output_dxf_path: str | Path,
    project: Optional[Dict[str, Any]] = None,
    project_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Dựng 1 tờ bản vẽ chi tiết BTCT chuẩn Form_04, tính BBS, xuất DXF v6 & sidecar SHA-256."""
    proj = dict(DEFAULT_CATLAI_PROJECT)
    if project:
        proj.update(project)

    sheet_no = str(sheet_spec["sheet_no"])
    sheet_title = str(sheet_spec["title"])
    sheet_scale = float(sheet_spec["scale"])
    out_p = Path(output_dxf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    engine, zones, frame_w, frame_h = _load_scaled_form04(
        proj,
        sheet_no=sheet_no,
        sheet_title=sheet_title,
        sheet_scale=sheet_scale,
        project_dir=project_dir,
    )
    doc = engine.doc
    msp = engine.msp
    before_handles = snapshot_msp_handles(msp)

    bbs_data = compute_bbs_rows(sheet_spec["bbs_rows"])

    # Vẽ phần chi tiết kỹ thuật bên trái
    if sheet_no == "KC.03":
        caps = sheet_spec["caps"]
        # DM.01 (trên trái), DM.02 (trên phải vùng rộng / giữa), DM.03 (dưới)
        _draw_pile_cap_detail(doc, msp, caps[0], origin_x=780.0, base_y=5250.0, sheet_scale=sheet_scale)
        _draw_pile_cap_detail(doc, msp, caps[1], origin_x=780.0, base_y=2950.0, sheet_scale=sheet_scale)
        _draw_pile_cap_detail(doc, msp, caps[2], origin_x=780.0, base_y=650.0, sheet_scale=sheet_scale)
    elif sheet_no == "KC.04":
        # VP_DETAIL_1: ĐM.TM Hố thang (trái + MC 4-4 phải)
        _draw_elevator_pit_detail(doc, msp, origin_x=780.0, base_y=4550.0, sheet_scale=sheet_scale)
        # VP_DETAIL_2: 4 mặt cắt giằng móng (2x2 lưới sạch)
        beams = sheet_spec["beams"]
        grid_pts = [(1350.0, 2650.0), (4150.0, 2650.0), (1350.0, 1250.0), (4150.0, 1250.0)]
        for bm, (bx, by) in zip(beams, grid_pts):
            _draw_beam_section(doc, msp, bm, cx=bx, cy=by, sheet_scale=sheet_scale)
    elif sheet_no in ("KC.08", "KC.09"):
        cols = sheet_spec["columns"]
        _draw_column_panel(doc, msp, cols[0], panel_x0=650.0, sheet_scale=sheet_scale)
        _draw_column_panel(doc, msp, cols[1], panel_x0=6250.0, sheet_scale=sheet_scale)
    else:
        raise ValueError(f"Unsupported detail sheet_no for Form_04 engine: {sheet_no}")

    # Render Bảng TK Cốt thép & Ghi chú kỹ thuật bên phải
    _render_bbs_table(doc, msp, bbs_data, zones["TABLE_REBAR"], sheet_scale=sheet_scale, sheet_no=sheet_no)
    _render_note_box(msp, zones["NOTE"], sheet_scale=sheet_scale, title=sheet_spec["notes_title"], notes=sheet_spec["notes"])

    owned_cnt = mark_new_entities_owned(msp, before_handles, role="DETAIL_NATIVE_FORM04")
    _hide_zone_guide_layers_for_export(doc)

    # PaperSpace layout A3 + Purge Unused Blocks
    ps_name = _setup_a3_paperspace_layout(doc, sheet_no=sheet_no, frame_w=frame_w, frame_h=frame_h)
    purge_stats = purge_unused_blocks(doc)

    try:
        doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        doc.header["$EXTMAX"] = (frame_w, frame_h, 0.0)
        doc.header["$LIMMIN"] = (0.0, 0.0)
        doc.header["$LIMMAX"] = (frame_w, frame_h)
    except Exception:
        pass

    engine.block_evidence = {
        "form_id": "FORM_04_CHITIET_COC_DAM_COT",
        "sheet_no": sheet_no,
        "paperspace_layout": ps_name,
        "agent_owned_entities": owned_cnt,
        "purge_stats": purge_stats,
        "bbs_rows": len(bbs_data["rows"]),
        "total_steel_kg": bbs_data["total_steel_kg"],
    }

    engine.save_v6(str(out_p))

    # Bổ sung metadata Deterministic Math & Detail Evidence vào sidecar while preserving exact SHA-256
    sidecar_path = out_p.with_suffix(".dce_audit.json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    by_type: Dict[str, int] = {}
    for ent in msp:
        t = ent.dxftype()
        by_type[t] = by_type.get(t, 0) + 1
    named_blocks = [b.name for b in doc.blocks if not b.name.startswith("*")]
    sidecar.update({
        "sheet_no": sheet_no,
        "title": sheet_title,
        "scale": sheet_scale,
        "mode": "DETAIL_NATIVE_FORM04",
        "Standard_Method": bbs_data["Standard_Method"],
        "Calculation_Logs": bbs_data["Calculation_Logs"],
        "total_length_m": bbs_data["total_length_m"],
        "total_steel_kg": bbs_data["total_steel_kg"],
        "bbs_rows_count": len(bbs_data["rows"]),
        "paperspace_layouts": [l.name for l in doc.layouts if l.name != "Model"],
        "named_blocks_count": len(named_blocks),
        "entities_by_type": by_type,
        "provenance": {
            "dxf_sha256": hashlib.sha256(out_p.read_bytes()).hexdigest(),
            "generator": "cad_rc_detail_engine (CAD v6.0 Open Form_04)",
            "status": sidecar.get("v6_status", "OK_V6"),
        },
    })
    sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "sheet_no": sheet_no,
        "title": sheet_title,
        "dxf_path": str(out_p),
        "scale": sheet_scale,
        "mode": "DETAIL_NATIVE_FORM04",
        "total_steel_kg": bbs_data["total_steel_kg"],
        "total_length_m": bbs_data["total_length_m"],
        "bbs_rows": len(bbs_data["rows"]),
        "named_blocks": len(named_blocks),
        "entities_by_type": by_type,
    }


def build_all_catlai_detail_sheets(
    out_dir: str | Path,
    project: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Sinh trọn bộ 4 tờ chi tiết BTCT Cát Lái (KC.03, KC.04, KC.08, KC.09) từ Form_04 Native."""
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for sh_key in ("KC.03", "KC.04", "KC.08", "KC.09"):
        spec = CATLAI_DETAIL_SPECS[sh_key]()
        out_dxf = out_root / spec["filename"]
        res = build_detail_sheet(spec, out_dxf, project=project, project_dir=out_root.parent)
        results.append(res)
    return results


def build_custom_detail_sheet(
    model: Dict[str, Any],
    output_dxf_path: str | Path,
    project_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Hook đa năng cho `cad_paperspace_builder.export_with_open_form(form_id='FORM_04_...')`."""
    sh_no = str(model.get("sheet_no") or model.get("detail_sheet", {}).get("sheet_no") or "KC.03").upper().replace("-", ".")
    if sh_no in CATLAI_DETAIL_SPECS:
        spec = CATLAI_DETAIL_SPECS[sh_no]()
    elif "detail_sheet" in model and isinstance(model["detail_sheet"], dict):
        spec = dict(model["detail_sheet"])
    else:
        raise ValueError(f"Unsupported custom Form_04 model without CATLAI spec or detail_sheet payload: {sh_no}")
    return build_detail_sheet(spec, output_dxf_path, project=model.get("project"), project_dir=project_dir)
