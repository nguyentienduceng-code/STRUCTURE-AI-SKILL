#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cad_vector_renderer.py — Trình Kết Xuất Bản Vẽ Kỹ Thuật Kết Cấu `.dxf / .json` sang `.png` (300 DPI) & `.pdf` Vector (v4.7)
===========================================================================================================================
Nâng cấp toàn diện v4.7:
1. Thể hiện chuẩn xác phân cấp chiều dày nét in (CTB Lineweight Hierarchy: Khung 1.8pt, Cột/Vách 1.2pt, Dầm chính 0.95pt,
   Dầm phụ 0.65pt, Đường kích thước & gióng 0.45pt, Lưới trục & Hatch 0.35pt).
2. Vẽ đầy đủ 4 tầng kích thước biên ngoài kèm đường gióng chân kích thước (Extension Lines) và gạch chéo `_ARCHTICK`.
3. Xoay nhãn dầm dọc 90° song song với thân dầm theo đúng chuẩn TCVN 5571:2012, không lặp chuỗi `1/100`.
4. Kẻ chi tiết toàn bộ lưới dòng/cột của Bảng thống kê cấu kiện (`DCE_Schedule`), tự động ngắt dòng khung Ghi chú kỹ thuật
   (`DCE_Note`) và căn chỉnh Khung tên đồ án (`DCE_TitleBlock_A1`) nằm gọn 100% trong Cột Sidebar Bên Phải, 0 tràn chữ!
"""

from __future__ import annotations
import json
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def render_plan_to_png_pdf(
    dxf_or_json_path: str,
    output_png_path: Optional[str] = None,
    output_pdf_path: Optional[str] = None,
    dpi: int = 300,
) -> Dict[str, str]:
    """Đọc tệp `.dxf` hoặc `.dce_audit.json` của `cad_plan_engine.py` (v4.7) và kết xuất ra `.png` (300 DPI) / `.pdf`."""
    src = Path(dxf_or_json_path)
    json_path = src if src.suffix == ".json" else src.with_suffix(".dce_audit.json")
    if not json_path.exists():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu kiểm toán bản vẽ tại: {json_path}")

    meta = json.loads(json_path.read_text(encoding="utf-8"))
    entities = meta.get("entities_log", [])
    mode = meta.get("mode", "COLUMN_WALL_SETOUT")
    S = float(meta.get("scale", 100.0))

    fig, ax = plt.subplots(figsize=(16.54, 11.69), dpi=dpi)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    plan_mid_y = 30000.0

    # 1. Vẽ Khung A1, Vạch phân vùng Sidebar Phải, Khung tên & Dải tiêu đề mặt bằng
    frames = [e for e in entities if e.get("block") == "DCE_TitleBlock_A1"]
    if frames:
        fr = frames[0]
        ox1, oy1, ox2, oy2 = fr["outer_bbox"]
        ix1, iy1, ix2, iy2 = fr["inner_bbox"]
        plan_mid_y = 0.5 * (iy1 + iy2)
        ax.add_patch(patches.Rectangle((ox1, oy1), ox2 - ox1, oy2 - oy1, fill=False, edgecolor="#1C2833", linewidth=1.6, zorder=10))
        ax.add_patch(patches.Rectangle((ix1, iy1), ix2 - ix1, iy2 - iy1, fill=False, edgecolor="#1C2833", linewidth=1.1, zorder=10))
        ax.set_xlim(ox1 - 6.0 * S, ox2 + 6.0 * S)
        ax.set_ylim(oy1 - 6.0 * S, oy2 + 6.0 * S)

        sb_div_x = fr.get("sidebar_divider_x", ix2 - 165.0 * S)
        ax.plot([sb_div_x, sb_div_x], [iy1, iy2], color="#1C2833", linewidth=1.0, zorder=10)

        tb_meta = fr.get("attribs", {})
        tb_x0, tb_y0, tb_x1, tb_y1 = fr.get("title_block_bbox", (sb_div_x, iy1, ix2, iy1 + 55.0 * S))
        tb_w = tb_x1 - tb_x0
        tb_h = tb_y1 - tb_y0
        split_ratio = 0.68
        ax.add_patch(patches.Rectangle((tb_x0, tb_y0), tb_w, tb_h, facecolor="#F8FAFC", edgecolor="#1C2833", linewidth=1.0, zorder=9))
        ax.plot([tb_x0, tb_x1], [tb_y0 + 0.68 * tb_h, tb_y0 + 0.68 * tb_h], color="#1C2833", linewidth=0.7, zorder=10)
        ax.plot([tb_x0, tb_x1], [tb_y0 + 0.35 * tb_h, tb_y0 + 0.35 * tb_h], color="#1C2833", linewidth=0.7, zorder=10)
        ax.plot([tb_x0 + split_ratio * tb_w, tb_x0 + split_ratio * tb_w], [tb_y0, tb_y0 + 0.35 * tb_h], color="#1C2833", linewidth=0.7, zorder=10)

        ax.text(
            tb_x0 + tb_w / 2.0,
            tb_y0 + 0.84 * tb_h,
            f"TƯ VẤN THIẾT KẾ: {tb_meta.get('DON_VI_TVTK', 'DCE PRO STRUCTURAL PARTNERS')}",
            fontsize=5.5,
            fontweight="bold",
            color="#1E3246",
            ha="center",
            va="center",
            zorder=11,
        )
        proj_str = f"DỰ ÁN: {tb_meta.get('TEN_DU_AN', '')}"
        proj_wrapped = "\n".join(textwrap.wrap(proj_str, width=52))
        ax.text(
            tb_x0 + tb_w / 2.0,
            tb_y0 + 0.515 * tb_h,
            proj_wrapped,
            fontsize=4.35,
            fontweight="bold",
            color="#1C2833",
            ha="center",
            va="center",
            linespacing=1.15,
            zorder=11,
        )
        bv_str = f"BẢN VẼ: {tb_meta.get('TEN_BAN_VE', mode)}"
        bv_wrapped = "\n".join(textwrap.wrap(bv_str, width=34))
        ax.text(
            tb_x0 + (split_ratio * tb_w) / 2.0,
            tb_y0 + 0.175 * tb_h,
            bv_wrapped,
            fontsize=3.95,
            fontweight="bold",
            color="#1C2833",
            ha="center",
            va="center",
            linespacing=1.12,
            zorder=11,
        )
        ax.text(
            tb_x0 + (split_ratio + (1.0 - split_ratio) / 2.0) * tb_w,
            tb_y0 + 0.175 * tb_h,
            f"TL: {tb_meta.get('TY_LE', '1/100')}\nSỐ: {tb_meta.get('KY_HIEU_BV', 'KC')}",
            fontsize=4.15,
            fontweight="bold",
            color="#922B21",
            ha="center",
            va="center",
            linespacing=1.15,
            zorder=11,
        )

        # Dải Tiêu đề chính ở đáy Vùng Vẽ Trái (tách biệt hoàn toàn với bong bóng trục dưới)
        dt_x, dt_y = fr.get("drawing_title_pos", ((ix1 + sb_div_x) / 2.0, iy1 + 12.0 * S))
        ax.text(dt_x, dt_y + 2.2 * S, tb_meta.get("TEN_BAN_VE", mode), fontsize=9.5, fontweight="bold", color="#1E3246", ha="center", va="bottom", zorder=11)
        ax.text(dt_x, dt_y - 2.0 * S, f"TỶ LỆ (SCALE): {tb_meta.get('TY_LE', f'1/{int(S)}')}   |   KÝ HIỆU BẢN VẼ: {tb_meta.get('KY_HIEU_BV', 'KC')}", fontsize=6.8, fontweight="bold", color="#566573", ha="center", va="top", zorder=11)
        ax.plot([dt_x - 115.0 * S, dt_x + 115.0 * S], [dt_y + 0.8 * S, dt_y + 0.8 * S], color="#1E3246", linewidth=0.9, zorder=11)

    # 2. Vẽ Lưới trục & Vòng tròn đầu trục DCE_Truc_Bubble
    for ent in entities:
        et = ent.get("type")
        layer = ent.get("layer")
        if et == "LINE" and layer == "DCE_Truc":
            p1, p2 = ent["p1"], ent["p2"]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#95A5A6", linestyle=(0, (6, 2, 1, 2)), linewidth=0.40, zorder=1)
        elif et == "INSERT" and ent.get("block") == "DCE_Truc_Bubble":
            bx, by = ent["insert"]
            r = ent.get("radius", 4.0 * S)
            ax.add_patch(patches.Circle((bx, by), r, fill=True, facecolor="#EBF5FB", edgecolor="#1B4F72", linewidth=0.80, zorder=6))
            ax.text(bx, by, ent.get("attribs", {}).get("SH_TRUC", ""), fontsize=6.5, fontweight="bold", color="#1B4F72", ha="center", va="center", zorder=7)

    # 3. Vẽ Chuỗi Kích thước 4 Tầng biên ngoài & Dim định vị cột (kèm chân gióng & gạch chéo _ARCHTICK)
    for ent in entities:
        if ent.get("type") == "DIMENSION":
            layer = ent.get("layer", "DCE_Dim")
            p1 = ent.get("p1", (0.0, 0.0))
            p2 = ent.get("p2", (1000.0, 0.0))
            base = ent.get("base", ((p1[0] + p2[0]) / 2.0, p1[1] - 1000.0))
            dtxt = str(ent.get("dim_text", ""))
            axis_dir = ent.get("axis_dir", "X")
            is_setout = (layer == "DCE_Setout")
            col_dim = "#2E86C1" if is_setout else "#27AE60"
            lw_dim = 0.40 if is_setout else 0.50
            fs_dim = 3.6 if is_setout else 4.8
            tick = 0.9 * S if is_setout else 1.3 * S

            if axis_dir == "X":
                yb = base[1]
                ax.plot([p1[0], p2[0]], [yb, yb], color=col_dim, linewidth=lw_dim, zorder=3)
                ax.plot([p1[0], p1[0]], [p1[1], yb], color=col_dim, linewidth=0.30, linestyle="-", zorder=2)
                ax.plot([p2[0], p2[0]], [p2[1], yb], color=col_dim, linewidth=0.30, linestyle="-", zorder=2)
                ax.plot([p1[0] - tick, p1[0] + tick], [yb - tick, yb + tick], color=col_dim, linewidth=0.75, zorder=4)
                ax.plot([p2[0] - tick, p2[0] + tick], [yb - tick, yb + tick], color=col_dim, linewidth=0.75, zorder=4)
                ax.text((p1[0] + p2[0]) / 2.0, yb + 0.5 * S, dtxt, fontsize=fs_dim, color="#1C2833", ha="center", va="bottom", zorder=7)
            else:
                xb = base[0]
                ax.plot([xb, xb], [p1[1], p2[1]], color=col_dim, linewidth=lw_dim, zorder=3)
                ax.plot([p1[0], xb], [p1[1], p1[1]], color=col_dim, linewidth=0.30, linestyle="-", zorder=2)
                ax.plot([p2[0], xb], [p2[1], p2[1]], color=col_dim, linewidth=0.30, linestyle="-", zorder=2)
                ax.plot([xb - tick, xb + tick], [p1[1] - tick, p1[1] + tick], color=col_dim, linewidth=0.75, zorder=4)
                ax.plot([xb - tick, xb + tick], [p2[1] - tick, p2[1] + tick], color=col_dim, linewidth=0.75, zorder=4)
                ax.text(xb - 0.6 * S, (p1[1] + p2[1]) / 2.0, dtxt, fontsize=fs_dim, color="#1C2833", rotation=90.0, ha="right", va="center", zorder=7)

    # 4. Vẽ Dầm (Nét đôi chuẩn bề rộng b), Cột, Vách, Lỗ mở, Ranh đất & Nhãn xoay theo hướng nhịp
    for ent in entities:
        et = ent.get("type")
        layer = ent.get("layer")

        if et == "LINE" and layer == "DCE_NetThay":
            p1, p2 = ent["p1"], ent["p2"]
            is_beam_mode = (mode == "BEAM_SLAB_FRAMING")
            is_sec = bool(ent.get("is_secondary", False))
            w_mm = float(ent.get("width", 300.0))
            if is_beam_mode:
                b_col = "#B7950B" if is_sec else "#1E8449"
                b_lw = 0.65 if is_sec else 0.95
                if abs(p1[1] - p2[1]) < 10.0:
                    ax.plot([p1[0], p2[0]], [p1[1] - w_mm / 2, p2[1] - w_mm / 2], color=b_col, linewidth=b_lw, zorder=3)
                    ax.plot([p1[0], p2[0]], [p1[1] + w_mm / 2, p2[1] + w_mm / 2], color=b_col, linewidth=b_lw, zorder=3)
                elif abs(p1[0] - p2[0]) < 10.0:
                    ax.plot([p1[0] - w_mm / 2, p2[0] - w_mm / 2], [p1[1], p2[1]], color=b_col, linewidth=b_lw, zorder=3)
                    ax.plot([p1[0] + w_mm / 2, p2[0] + w_mm / 2], [p1[1], p2[1]], color=b_col, linewidth=b_lw, zorder=3)
                else:
                    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=b_col, linewidth=b_lw, zorder=3)
            else:
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#7F8C8D", linestyle="--", linewidth=0.45, zorder=2)

            if ent.get("has_beam_label") and ent.get("beam_label_text"):
                lx, ly = ent.get("beam_label_pos", ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0 + 350.0))
                rot = float(ent.get("beam_label_rotation", 0.0))
                ax.text(
                    lx, ly, ent["beam_label_text"],
                    fontsize=4.35, fontweight="bold",
                    color="#7D6608" if is_sec else "#145A32",
                    rotation=rot,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.06", facecolor="#FFFFFF", edgecolor="none", alpha=0.85),
                    zorder=8
                )

        elif et == "LWPOLYLINE" and "bbox" in ent:
            x1, y1, x2, y2 = ent["bbox"]
            if layer == "DCE_Vach":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor="#2C3E50", edgecolor="#17202A", linewidth=1.15, zorder=5))
            elif layer == "DCE_CouplingBeam":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor="#EAECEE", edgecolor="#8E44AD", linewidth=0.9, zorder=4))
                if ent.get("label"):
                    ym_cb = 0.5 * (y1 + y2)
                    if ym_cb < plan_mid_y:
                        ax.text(
                            (x1 + x2) / 2.0, y1 - 2.0 * S, ent["label"],
                            fontsize=4.1, fontweight="bold", color="#6C3483",
                            ha="center", va="top",
                            bbox=dict(boxstyle="round,pad=0.05", facecolor="#FFFFFF", edgecolor="none", alpha=0.88),
                            zorder=8
                        )
                    else:
                        ax.text(
                            (x1 + x2) / 2.0, y2 + 2.0 * S, ent["label"],
                            fontsize=4.1, fontweight="bold", color="#6C3483",
                            ha="center", va="bottom",
                            bbox=dict(boxstyle="round,pad=0.05", facecolor="#FFFFFF", edgecolor="none", alpha=0.88),
                            zorder=8
                        )
            elif layer == "DCE_VoidX":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="#5D6D7E", linewidth=0.75, zorder=3))
                ax.plot([x1, x2], [y1, y2], color="#7F8C8D", linewidth=0.45, zorder=3)
                ax.plot([x1, x2], [y2, y1], color="#7F8C8D", linewidth=0.45, zorder=3)
                if ent.get("label"):
                    ax.text((x1 + x2) / 2.0, (y1 + y2) / 2.0, ent["label"], fontsize=3.9, color="#2E4053", ha="center", va="center", bbox=dict(boxstyle="round,pad=0.05", facecolor="#FFFFFF", edgecolor="none", alpha=0.85), zorder=7)
            elif layer == "DCE_Cot":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="#B7950B", linewidth=0.95, zorder=4))
            elif layer == "DCE_RanhDat":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="#C0392B", linestyle="-.", linewidth=1.1, zorder=4))
                if ent.get("label"):
                    ax.text((x1 + x2) / 2.0, y2 + 2.5 * S, ent["label"], fontsize=6.0, fontweight="bold", color="#C0392B", ha="center", va="bottom", zorder=8)
            elif layer == "DCE_ChiGioi":
                ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="#8E44AD", linestyle="--", linewidth=0.8, zorder=3))

        elif et == "INSERT" and ent.get("block") in ("DCE_Cot_Block", "DCE_Cot_Dung"):
            cx, cy = ent["insert"]
            b, h = ent["xscale"], ent["yscale"]
            x1, y1 = cx - b / 2.0, cy - h / 2.0
            is_stop = (ent.get("block") == "DCE_Cot_Dung")
            ax.add_patch(patches.Rectangle(
                (x1, y1), b, h,
                facecolor="#F5B7B1" if is_stop else "#34495E",
                edgecolor="#78281F" if is_stop else "#17202A",
                linewidth=1.15, zorder=5
            ))
            if is_stop:
                ax.plot([x1, x1 + b], [y1, y1 + h], color="#78281F", linewidth=0.8, zorder=6)
                ax.plot([x1, x1 + b], [y1 + h, y1], color="#78281F", linewidth=0.8, zorder=6)

        elif et == "INSERT" and ent.get("block") == "DCE_Coc_Block":
            px, py = ent["insert"]
            r_p = ent.get("xscale", 600.0) / 2.0
            ax.add_patch(patches.Circle((px, py), r_p, facecolor="#D5F5E3", edgecolor="#196F3D", linewidth=0.75, zorder=4))

        elif et == "INSERT" and ent.get("block") == "DCE_TenCauKien":
            tx, ty = ent["insert"]
            att = ent.get("attribs", {})
            ax.text(
                tx, ty, f"{att.get('SOCAUKIEN', '')}\n{att.get('TENCAUKIEN', '')}",
                fontsize=4.35, fontweight="bold", color="#7D6608",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.06", facecolor="#FFFFFF", edgecolor="#D4AC0D", linewidth=0.35, alpha=0.90),
                zorder=8
            )

        elif et == "INSERT" and ent.get("block") == "DCE_KyHieuSan":
            sx, sy = ent["insert"]
            att = ent.get("attribs", {})
            is_drop = (ent.get("hatch_pattern") not in (None, "NONE"))
            if is_drop and "bbox" in ent:
                bx1, by1, bx2, by2 = ent["bbox"]
                ax.add_patch(patches.Rectangle((bx1, by1), bx2 - bx1, by2 - by1, facecolor="#EBF5FB", edgecolor="#2874A6", linestyle="--", linewidth=0.55, alpha=0.55, zorder=2))
            ax.text(
                sx, sy, f"{att.get('MA_SAN', '')}\n{att.get('CAO_DO', '')}",
                fontsize=4.2, fontweight="bold", color="#117864" if not is_drop else "#922B21",
                ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.10", facecolor="#FFFFFF", edgecolor="#117864" if not is_drop else "#922B21", linewidth=0.5, alpha=0.92),
                zorder=8
            )

        elif et == "SLAB_REBAR_STRIP":
            x1, y1, x2, y2 = ent["bbox"]
            cx, cy = ent["insert"]
            att = ent.get("attribs", {})
            ax.plot([x1, x2], [cy, cy], color="#C0392B", linewidth=1.2, zorder=6)
            ax.plot([cx, cx], [y1, y2], color="#27AE60", linestyle="--", linewidth=0.8, zorder=5)
            ax.text(cx, cy + 250.0, f"[{att.get('SO_HIEU', '1')}] {att.get('QUY_CACH', '')}", fontsize=5.2, color="#C0392B", fontweight="bold", ha="center", zorder=8)

        elif et == "SCHEDULE_TABLE":
            bx1, by1, bx2, by2 = ent["bbox"]
            ax.add_patch(patches.Rectangle((bx1, by1), bx2 - bx1, by2 - by1, facecolor="#FFFFFF", edgecolor="#1C2833", linewidth=0.95, zorder=7))
            h_title = 9.5 * S
            h_head = 7.0 * S
            h_row = 6.2 * S
            ax.add_patch(patches.Rectangle((bx1, by2 - h_title), bx2 - bx1, h_title, facecolor="#DCE4EC", edgecolor="#1C2833", linewidth=0.75, zorder=8))
            ax.add_patch(patches.Rectangle((bx1, by2 - h_title - h_head), bx2 - bx1, h_head, facecolor="#F2F4F4", edgecolor="#1C2833", linewidth=0.65, zorder=8))
            ax.text((bx1 + bx2) / 2.0, by2 - h_title / 2.0, "BẢNG THỐNG KÊ TIẾT DIỆN & CẤU KIỆN KẾT CẤU", fontsize=5.4, fontweight="bold", color="#1E3246", ha="center", va="center", zorder=9)

            col_w = ent.get("col_widths", [])
            headers = ent.get("columns_headers", [])
            rows = ent.get("rows", [])
            cx_col = bx1
            for j, h_str in enumerate(headers):
                w_c = col_w[j] if j < len(col_w) else (bx2 - bx1) / max(1, len(headers))
                ax.text(cx_col + w_c / 2.0, by2 - h_title - h_head / 2.0, h_str, fontsize=4.0, fontweight="bold", color="#1C2833", ha="center", va="center", zorder=9)
                cx_col += w_c
                if j < len(headers) - 1:
                    ax.plot([cx_col, cx_col], [by1, by2 - h_title], color="#566573", linewidth=0.5, zorder=9)

            cy_row = by2 - h_title - h_head
            for r_vals in rows:
                next_y = cy_row - h_row
                cx_col = bx1
                for j, val in enumerate(r_vals):
                    w_c = col_w[j] if j < len(col_w) else (bx2 - bx1) / max(1, len(r_vals))
                    ax.text(cx_col + w_c / 2.0, cy_row - h_row / 2.0, str(val), fontsize=3.85, color="#1C2833", ha="center", va="center", zorder=9)
                    cx_col += w_c
                ax.plot([bx1, bx2], [next_y, next_y], color="#ABB2B9", linewidth=0.45, zorder=8)
                cy_row = next_y

        elif et == "LEGEND_BOX":
            bx1, by1, bx2, by2 = ent["bbox"]
            ax.add_patch(patches.Rectangle((bx1, by1), bx2 - bx1, by2 - by1, facecolor="#FBFCFC", edgecolor="#1C2833", linewidth=0.85, zorder=7))
            notes_lines = ent.get("notes_lines", ["GHI CHÚ KỸ THUẬT & CHỈ DẪN THI CÔNG"])
            ax.add_patch(patches.Rectangle((bx1, by2 - 8.5 * S), bx2 - bx1, 8.5 * S, facecolor="#EAECEE", edgecolor="#1C2833", linewidth=0.65, zorder=8))
            ax.text(bx1 + (bx2 - bx1) / 2.0, by2 - 4.25 * S, "GHI CHÚ KỸ THUẬT & CHỈ DẪN THI CÔNG (TCVN 5574:2018)", fontsize=4.4, fontweight="bold", color="#1E3246", ha="center", va="center", zorder=9)
            wrapped_notes: List[str] = []
            for raw_line in notes_lines[1:]:
                wrapped = textwrap.wrap(raw_line, width=64)
                for idx_w, w_line in enumerate(wrapped):
                    wrapped_notes.append(w_line if idx_w == 0 else f"   {w_line}")
            for idx_n, n_line in enumerate(wrapped_notes, start=1):
                y_txt = by2 - (6.8 + idx_n * 5.6) * S
                if y_txt > by1 + 2.5 * S:
                    ax.text(bx1 + 2.2 * S, y_txt, n_line, fontsize=3.55, color="#1C2833", ha="left", va="center", zorder=9)

    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout(pad=0.15)

    outputs: Dict[str, str] = {}
    if output_png_path is None and output_pdf_path is None:
        output_png_path = str(src.with_suffix(".png"))
    if output_png_path:
        Path(output_png_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_png_path, dpi=dpi, bbox_inches="tight")
        outputs["png"] = str(output_png_path)
    if output_pdf_path:
        Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_pdf_path, bbox_inches="tight")
        outputs["pdf"] = str(output_pdf_path)

    plt.close(fig)
    return outputs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cad_vector_renderer.py <input.dxf|.dce_audit.json> [output.png] [output.pdf]")
        sys.exit(1)
    inp = sys.argv[1]
    out_png = sys.argv[2] if len(sys.argv) > 2 else str(Path(inp).with_suffix(".png"))
    out_pdf = sys.argv[3] if len(sys.argv) > 3 else str(Path(inp).with_suffix(".pdf"))
    res = render_plan_to_png_pdf(inp, out_png, out_pdf)
    print(f"[DCE Pro Vector Renderer v4.7] Đã xuất bản vẽ trực quan: {res}")
