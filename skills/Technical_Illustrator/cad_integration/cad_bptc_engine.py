# -*- coding: utf-8 -*-
"""
Module: cad_bptc_engine.py
Author: Antigravity (GEMINI) - DCE Pro CAD Engine v5.0
Description:
    Động cơ Vẽ Bản vẽ Biện pháp Thi công (BPTC Engine) chuẩn QCVN 18:2021/BXD & TCVN 5575:2024.
    Cung cấp:
      1. BP-01: Tổng mặt bằng thi công & an toàn (Site Logistics & Safe Zones).
      2. BP-02: Chi tiết hệ cùm neo cần trục tháp (Tower Crane Tie Collar - Bài toán QTP125)
         trên bố cục đa tỷ lệ COMPOSITE_DETAIL_GRID.
      3. BP-03: Hệ văng chống shoring hố đào (Deep Excavation Bracing & Waling Beams).
      4. Tự động xuất file DXF chuẩn AC1021 và hồ sơ kiểm toán .bptc_audit.json đồng bộ SSOT.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn tới _SHARED/SHARED_CONTEXT và cad_integration
_CURRENT_DIR = Path(__file__).resolve().parent
_SHARED_CTX = _CURRENT_DIR.parents[2] / "_SHARED" / "SHARED_CONTEXT"
_VERIFY_DIR = _CURRENT_DIR.parents[2] / "skills" / "SKILL_VERIFY" / "scripts"

for p in (str(_SHARED_CTX), str(_CURRENT_DIR), str(_VERIFY_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
import cad_layer_standard as cls
from cad_plan_engine import DceSheetLayoutPlanner, SheetLayoutSpec, CompositeCellSpec
import cad_steel_primitives as csp


class CadBptcEngine:
    """
    Engine chuyên biệt vẽ Bản vẽ Biện pháp Thi công (BPTC) DCE Pro v5.0.
    """

    def __init__(self, template_dxf_path: Optional[str] = None):
        self.template_dxf_path = template_dxf_path or str(cls.DEFAULT_TEMPLATE_DXF_PATH)
        self.doc: Optional[ezdxf.document.Drawing] = None
        self.msp: Any = None
        self.layer_profile = "BPTC"

    def _init_doc(self) -> None:
        """Khởi tạo tài liệu DXF từ template hạt nhân hoặc bản mới AC1021."""
        if Path(self.template_dxf_path).is_file():
            self.doc = ezdxf.readfile(self.template_dxf_path)
        else:
            self.doc = ezdxf.new("AC1021")
        self.msp = self.doc.modelspace()
        self._ensure_bptc_layers()

    def _ensure_bptc_layers(self) -> None:
        """Đảm bảo đầy đủ 12 layer của Profile BPTC trong tài liệu DXF."""
        if not self.doc:
            return
        bptc_layers = cls.select_layer_profile("BPTC")
        existing_layers = {ly.dxf.name for ly in self.doc.layers}
        for name, color, ltype, lw, screening in bptc_layers:
            if name not in existing_layers:
                self.doc.layers.new(
                    name=name,
                    dxfattribs={
                        "color": color,
                        "linetype": ltype if ltype in self.doc.linetypes else "Continuous",
                        "lineweight": lw,
                    },
                )

    # ==========================================================================
    # BP-02: CHI TIẾT HỆ CÙM NEO CẦN TRỤC THÁP (TOWER CRANE TIE COLLAR)
    # ==========================================================================

    def generate_bp02_tower_crane_tie(
        self,
        crane_model: str = "QTP125",
        tower_size_mm: float = 1600.0,
        tie_struts: Optional[List[Dict[str, Any]]] = None,
        anchor_plates: Optional[List[Dict[str, Any]]] = None,
        output_dxf: Optional[str] = None,
        project_name: str = "DỰ ÁN CAO TẦNG",
    ) -> Dict[str, Any]:
        """
        Sinh bản vẽ BP-02: Chi tiết hệ cùm neo cần trục tháp (ví dụ QTP125).
        Bố cục COMPOSITE_DETAIL_GRID:
          - Vùng chính (Primary Zone, 60%): Mặt bằng tổng thể cùm giằng neo tháp về vách/dầm công trình (tỷ lệ 1/50).
          - Ô chi tiết CT-01 (tỷ lệ 1/10): Chi tiết nút bản mã liên kết vào dầm/vách BTCT.
          - Ô chi tiết CT-02 (tỷ lệ 1/15): Chi tiết cùm ôm thân tháp cần trục.
        """
        self._init_doc()
        assert self.msp is not None
        assert self.doc is not None

        # Dữ liệu mặc định thanh giằng (3 thanh giằng thép hộp hoặc dầm I/U)
        if not tie_struts:
            tie_struts = [
                {"mark": "TG-01", "section": "2U200x73x7", "steel_grade": "SS400", "p1": (-800, 800), "p2": (-3500, 4200), "qty": 1},
                {"mark": "TG-02", "section": "2U200x73x7", "steel_grade": "SS400", "p1": (800, 800), "p2": (2800, 4500), "qty": 1},
                {"mark": "TG-03", "section": "2U200x73x7", "steel_grade": "SS400", "p1": (800, -800), "p2": (3800, -2500), "qty": 1},
            ]

        if not anchor_plates:
            anchor_plates = [
                {"mark": "BM-01", "t_mm": 20.0, "b_mm": 450.0, "h_mm": 500.0, "pos": (-3500, 4200), "bolts": "8 M24", "qty": 2},
                {"mark": "BM-02", "t_mm": 20.0, "b_mm": 450.0, "h_mm": 500.0, "pos": (2800, 4500), "bolts": "8 M24", "qty": 2},
                {"mark": "BM-03", "t_mm": 20.0, "b_mm": 450.0, "h_mm": 500.0, "pos": (3800, -2500), "bolts": "8 M24", "qty": 2},
            ]

        # 1. Tính toán Kích thước tổng thể mặt bằng giằng neo
        all_x = [p["p1"][0] for p in tie_struts] + [p["p2"][0] for p in tie_struts]
        all_y = [p["p1"][1] for p in tie_struts] + [p["p2"][1] for p in tie_struts]
        w_model = max(all_x) - min(all_x) + 2000.0
        h_model = max(all_y) - min(all_y) + 2000.0

        # 2. Khởi tạo Bố cục Đa tỷ lệ COMPOSITE_DETAIL_GRID
        detail_specs = [
            {"cell_id": "CT-01", "scale": 10.0, "title": "CHI TIẾT BẢN MÃ NEO VÁCH/DẦM (CT-01)"},
            {"cell_id": "CT-02", "scale": 15.0, "title": "CHI TIẾT CÙM ÔM THÂN THÁP (CT-02)"},
        ]
        layout_spec = DceSheetLayoutPlanner.resolve_composite_grid(
            model_w_mm=w_model,
            model_h_mm=h_model,
            detail_specs=detail_specs,
            preferred_scale=50.0,
            sheet_size="A1",
        )
        S = layout_spec.scale

        # 3. Vẽ VÙNG CHÍNH (PRIMARY ZONE) — Mặt bằng Cùm Neo Tháp (Tỷ lệ S=1/50)
        # Tọa độ tâm tháp tại plan_x0 + w_model/2, plan_y0 + h_model/2
        crane_cx = layout_spec.plan_x0 + (w_model / 2.0)
        crane_cy = layout_spec.plan_y0 + (h_model / 2.0)

        # 3.1 Vẽ Thân Tháp (Khung vuông tower_size x tower_size)
        half_tw = tower_size_mm / 2.0
        tower_pts = [
            (crane_cx - half_tw, crane_cy - half_tw),
            (crane_cx + half_tw, crane_cy - half_tw),
            (crane_cx + half_tw, crane_cy + half_tw),
            (crane_cx - half_tw, crane_cy + half_tw),
        ]
        self.msp.add_lwpolyline(tower_pts, close=True, dxfattribs={"layer": "DCE_BPTC_Equip"})
        # 4 trụ tháp (cột góc L hoặc ống)
        leg_r = 80.0
        for tx, ty in tower_pts:
            self.msp.add_circle((tx, ty), radius=leg_r, dxfattribs={"layer": "DCE_BPTC_Equip"})
        # Chữ thập tâm thân tháp
        self.msp.add_line((crane_cx - half_tw * 1.3, crane_cy), (crane_cx + half_tw * 1.3, crane_cy), dxfattribs={"layer": "DCE_BPTC_Equip"})
        self.msp.add_line((crane_cx, crane_cy - half_tw * 1.3), (crane_cx, crane_cy + half_tw * 1.3), dxfattribs={"layer": "DCE_BPTC_Equip"})
        # Nhãn thân tháp
        self.msp.add_text(
            f"THÂN THÁP {crane_model} ({int(tower_size_mm)}x{int(tower_size_mm)})",
            dxfattribs={"layer": "DCE_Name", "height": 3.0 * S, "insert": (crane_cx, crane_cy + half_tw + 6.0 * S)}
        )

        # 3.2 Vẽ Khung cùm ôm thân tháp (Collar Frame)
        collar_offset = 60.0
        collar_pts = [
            (crane_cx - half_tw - collar_offset, crane_cy - half_tw - collar_offset),
            (crane_cx + half_tw + collar_offset, crane_cy - half_tw - collar_offset),
            (crane_cx + half_tw + collar_offset, crane_cy + half_tw + collar_offset),
            (crane_cx - half_tw - collar_offset, crane_cy + half_tw + collar_offset),
        ]
        self.msp.add_lwpolyline(collar_pts, close=True, dxfattribs={"layer": "DCE_BPTC_Tie"})

        # 3.3 Vẽ các Thanh Giằng (Tie Struts)
        bom_items: List[Dict[str, Any]] = []
        for st in tie_struts:
            p1_world = (crane_cx + st["p1"][0], crane_cy + st["p1"][1])
            p2_world = (crane_cx + st["p2"][0], crane_cy + st["p2"][1])
            # Vẽ đường trục thanh giằng
            self.msp.add_line(p1_world, p2_world, dxfattribs={"layer": "DCE_BPTC_Tie"})
            # Tính chiều dài và khối lượng
            L_strut = math.hypot(p2_world[0] - p1_world[0], p2_world[1] - p1_world[1])
            bom_items.append({
                "mark": st["mark"],
                "section": st["section"],
                "steel_grade": st["steel_grade"],
                "qty": st.get("qty", 1),
                "length_mm": round(L_strut, 0),
                "note": "Thanh giằng cùm neo",
            })
            # Ghi nhãn thanh giằng
            mid_x = (p1_world[0] + p2_world[0]) / 2.0
            mid_y = (p1_world[1] + p2_world[1]) / 2.0
            self.msp.add_text(
                f"{st['mark']}: {st['section']}",
                dxfattribs={"layer": "DCE_Name", "height": 2.2 * S, "insert": (mid_x, mid_y + 3.0 * S)}
            )

        # 3.4 Vẽ các Nút Bản mã neo vào vách/dầm BTCT (Anchor Plates)
        for ap in anchor_plates:
            pos_w = (crane_cx + ap["pos"][0], crane_cy + ap["pos"][1])
            half_b = ap["b_mm"] / 2.0
            half_h = ap["h_mm"] / 2.0
            pts_ap = [
                (pos_w[0] - half_b, pos_w[1] - half_h),
                (pos_w[0] + half_b, pos_w[1] - half_h),
                (pos_w[0] + half_b, pos_w[1] + half_h),
                (pos_w[0] - half_b, pos_w[1] + half_h),
            ]
            self.msp.add_lwpolyline(pts_ap, close=True, dxfattribs={"layer": "DCE_BPTC_Anchor"})
            self.msp.add_text(
                f"{ap['mark']} ({ap['bolts']})",
                dxfattribs={"layer": "DCE_Name", "height": 2.0 * S, "insert": (pos_w[0], pos_w[1] + half_h + 3.0 * S)}
            )
            bom_items.append({
                "mark": ap["mark"],
                "spec": f"PL{int(ap['t_mm'])}x{int(ap['b_mm'])}x{int(ap['h_mm'])}",
                "steel_grade": "SS400",
                "qty": ap.get("qty", 1),
                "total_weight_kg": round((ap['t_mm'] * ap['b_mm'] * ap['h_mm'] * 1e-9 * 7850.0) * ap.get("qty", 1), 2),
                "note": "Bản mã neo vách/dầm",
            })

        # 4. VẼ CÁC Ô CHI TIẾT TRÊN COMPOSITE_DETAIL_GRID (DETAIL CELLS)
        for cell in layout_spec.detail_cells:
            # 4.1 Vẽ khung viền ô chi tiết
            x0, y0, x1, y1 = cell.bbox
            cell_box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            self.msp.add_lwpolyline(cell_box, close=True, dxfattribs={"layer": "DCE_Frame"})

            # 4.2 Tiêu đề ô chi tiết
            tx, ty = cell.title_pos
            self.msp.add_text(
                f"{cell.title} - TỶ LỆ {cell.scale_label}",
                dxfattribs={"layer": "DCE_Name", "height": 3.0 * S, "insert": (tx - 50.0 * S, ty)}
            )

            # 4.3 Nội dung chi tiết từng ô
            cx, cy = cell.inner_origin
            if cell.cell_id == "CT-01":
                # Nút chi tiết bản mã neo: Bản mã + Bu lông + Ký hiệu hàn TCVN
                # Bản mã 450x500x20
                csp.draw_gusset_plate(
                    self.msp,
                    polygon_pts=[(cx - 225, cy - 250), (cx + 225, cy - 250), (cx + 225, cy + 250), (cx - 225, cy + 250)],
                    thickness_mm=20.0,
                    mark="BM-01",
                    layer="DCE_Steel_Plate",
                )
                # Mảng bu lông 2 hàng 4 cột M24
                csp.draw_bolt_array(
                    self.msp,
                    origin=(cx, cy),
                    rows=2,
                    cols=4,
                    p1=120.0,
                    p2=100.0,
                    d_bolt=24.0,
                    bolt_grade="8.8",
                    layer_bolt="DCE_BPTC_Anchor",
                )
                # Ký hiệu đường hàn góc liên kết tai neo vào bản mã hf=10, lw=300
                csp.draw_weld_symbol_tcvn(
                    self.msp,
                    target_pt=(cx + 100, cy + 180),
                    leg_hf_mm=10.0,
                    length_lw_mm=300.0,
                    both_sides=True,
                    leader_dir=(120.0, 100.0),
                )
            elif cell.cell_id == "CT-02":
                # Chi tiết góc cùm ôm thân tháp (Góc thân tháp L + Bản mã nối + Bu lông siết)
                csp.draw_rolled_section(
                    self.msp,
                    profile_str="L150x150x15",
                    origin=(cx, cy),
                    view_mode="SECTION",
                    layer_main="DCE_Steel_Main",
                )
                csp.draw_bolt_array(
                    self.msp,
                    origin=(cx + 80, cy - 80),
                    rows=2,
                    cols=2,
                    p1=80.0,
                    p2=80.0,
                    d_bolt=20.0,
                    layer_bolt="DCE_BPTC_Anchor",
                )

        # 5. KHUNG BẢN VẼ A1 & SIDEBAR BẢNG THỐNG KÊ (BOM)
        # Khung viền ngoài
        in_x0, in_y0, in_x1, in_y1 = layout_spec.inner_bbox
        self.msp.add_lwpolyline(
            [(in_x0, in_y0), (in_x1, in_y0), (in_x1, in_y1), (in_x0, in_y1)],
            close=True,
            dxfattribs={"layer": "DCE_Frame"}
        )
        # Đường chia Sidebar
        sb_x = layout_spec.sidebar_divider_x
        self.msp.add_line((sb_x, in_y0), (sb_x, in_y1), dxfattribs={"layer": "DCE_Frame"})

        # Tổng hợp Bảng Thống kê BOM vào Sidebar
        bom_data = csp.compute_steel_bom(bom_items)
        sb_top = in_y1 - 20.0 * S
        self.msp.add_text(
            "BẢNG THỐNG KÊ VẬT LIỆU THÉP & BULÔNG (BOM)",
            dxfattribs={"layer": "DCE_Name", "height": 2.5 * S, "insert": (sb_x + 5.0 * S, sb_top)}
        )

        row_y = sb_top - 12.0 * S
        col_offsets = [0.0, 8.0 * S, 25.0 * S, 60.0 * S, 80.0 * S, 95.0 * S, 115.0 * S, 135.0 * S]
        # In header
        for idx, h_txt in enumerate(["STT", "Hiệu", "Quy cách", "Mác", "SL", "Dài", "Tổng KL", "Ghi chú"]):
            if idx < len(col_offsets):
                self.msp.add_text(
                    h_txt,
                    dxfattribs={"layer": "DCE_Schedule", "height": 1.6 * S, "insert": (sb_x + 5.0 * S + col_offsets[idx], row_y)}
                )

        # In từng dòng
        for r in bom_data["rows"]:
            row_y -= 8.0 * S
            # stt, mark, sec, grade, qty, length, unit_w, tot_w, note
            disp_vals = [r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[8]]
            for idx, val in enumerate(disp_vals):
                if idx < len(col_offsets):
                    self.msp.add_text(
                        val,
                        dxfattribs={"layer": "DCE_Schedule", "height": 1.5 * S, "insert": (sb_x + 5.0 * S + col_offsets[idx], row_y)}
                    )

        # In tổng khối lượng
        row_y -= 12.0 * S
        self.msp.add_text(
            f"TỔNG KHỐI LƯỢNG THÉP: {bom_data['total_weight_kg']:.1f} KG",
            dxfattribs={"layer": "DCE_Name", "height": 2.2 * S, "insert": (sb_x + 5.0 * S, row_y)}
        )

        # Khung tên chính (Title Block)
        tb_x0, tb_y0, tb_x1, tb_y1 = layout_spec.title_block_bbox
        self.msp.add_lwpolyline(
            [(tb_x0, tb_y0), (tb_x1, tb_y0), (tb_x1, tb_y1), (tb_x0, tb_y1)],
            close=True,
            dxfattribs={"layer": "DCE_Frame"}
        )
        self.msp.add_text(
            project_name,
            dxfattribs={"layer": "DCE_Name", "height": 3.2 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 35.0 * S)}
        )
        self.msp.add_text(
            f"BPTC: CHI TIẾT HỆ CÙM NEO CẦN TRỤC THÁP {crane_model}",
            dxfattribs={"layer": "DCE_Name", "height": 2.8 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 20.0 * S)}
        )
        self.msp.add_text(
            f"BẢN VẼ SỐ: BP-02 | TỶ LỆ CHÍNH: 1/{int(S)}",
            dxfattribs={"layer": "DCE_Schedule", "height": 2.0 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 8.0 * S)}
        )

        # 6. LƯU TỆP DXF & TẠO HỒ SƠ KIỂM TOÁN SSOT
        audit_dossier = {
            "schema_version": "5.0",
            "profile": "BPTC",
            "drawing_code": "BP-02",
            "title": f"Chi tiết hệ cùm neo cần trục tháp {crane_model}",
            "sha256_sync_hash": "IN_MEMORY_UNSAVED",
            "sheet_layout": {
                "mode": layout_spec.layout_mode,
                "sheet_size": layout_spec.sheet_size,
                "primary_scale": layout_spec.scale,
                "detail_cells": [
                    {"cell_id": c.cell_id, "scale": c.scale_S, "dimlfac": c.dimlfac, "title": c.title}
                    for c in layout_spec.detail_cells
                ],
            },
            "members": bom_items,
            "bom_summary": bom_data,
        }

        if output_dxf:
            out_p = Path(output_dxf).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            self.doc.saveas(str(out_p))
            dxf_sha256 = hashlib.sha256(out_p.read_bytes()).hexdigest()
            audit_dossier["sha256_sync_hash"] = dxf_sha256
            audit_dossier["provenance"] = {
                "dxf_sha256": dxf_sha256,
                "generator": "CadBptcEngine v5.0",
                "drawing_code": "BP-02",
            }
            # Lưu file json audit song hành
            audit_json_p = out_p.with_suffix(".bptc_audit.json")
            with open(audit_json_p, "w", encoding="utf-8") as f:
                json.dump(audit_dossier, f, indent=2, ensure_ascii=False)
            audit_dossier["output_dxf"] = str(out_p)
            audit_dossier["output_audit_json"] = str(audit_json_p)

        return audit_dossier

    # ==========================================================================
    # BP-01: TỔNG MẶT BẰNG THI CÔNG & AN TOÀN (SITE LOGISTICS)
    # ==========================================================================

    def generate_bp01_site_plan(
        self,
        site_w_m: float = 60.0,
        site_h_m: float = 40.0,
        crane_pos: Tuple[float, float] = (0.0, 0.0),
        crane_radius_m: float = 55.0,
        output_dxf: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sinh bản vẽ BP-01: Tổng mặt bằng thi công & an toàn (Site Logistics).
        """
        self._init_doc()
        assert self.msp is not None
        assert self.doc is not None

        w_mm = site_w_m * 1000.0
        h_mm = site_h_m * 1000.0
        layout_spec = DceSheetLayoutPlanner.resolve_layout(
            model_w_mm=w_mm,
            model_h_mm=h_mm,
            sheet_size="A1",
        )
        S = layout_spec.scale

        # Ranh giới công trường (DCE_Truc hoặc DCE_BaoBeTong)
        px0 = layout_spec.plan_x0
        py0 = layout_spec.plan_y0
        site_box = [(px0, py0), (px0 + w_mm, py0), (px0 + w_mm, py0 + h_mm), (px0, py0 + h_mm)]
        self.msp.add_lwpolyline(site_box, close=True, dxfattribs={"layer": "DCE_Truc"})

        # Vị trí cần trục tháp & bán kính quay an toàn
        cx = px0 + (w_mm / 2.0) + crane_pos[0] * 1000.0
        cy = py0 + (h_mm / 2.0) + crane_pos[1] * 1000.0

        # Thân cẩu
        t_size = 1600.0
        self.msp.add_lwpolyline(
            [(cx - t_size/2, cy - t_size/2), (cx + t_size/2, cy - t_size/2),
             (cx + t_size/2, cy + t_size/2), (cx - t_size/2, cy + t_size/2)],
            close=True,
            dxfattribs={"layer": "DCE_BPTC_Equip"}
        )
        # Bán kính hoạt động an toàn
        r_safe_mm = crane_radius_m * 1000.0
        self.msp.add_circle((cx, cy), radius=r_safe_mm, dxfattribs={"layer": "DCE_BPTC_SafeZone"})
        self.msp.add_text(
            f"BÁN KÍNH HOẠT ĐỘNG CẨU R = {int(crane_radius_m)}M",
            dxfattribs={"layer": "DCE_Name", "height": 2.5 * S, "insert": (cx, cy + r_safe_mm + 5.0 * S)}
        )

        # Khung viền A1
        in_x0, in_y0, in_x1, in_y1 = layout_spec.inner_bbox
        self.msp.add_lwpolyline([(in_x0, in_y0), (in_x1, in_y0), (in_x1, in_y1), (in_x0, in_y1)], close=True, dxfattribs={"layer": "DCE_Frame"})

        audit = {
            "schema_version": "5.0",
            "profile": "BPTC",
            "drawing_code": "BP-01",
            "title": "Tổng mặt bằng thi công & An toàn cần trục",
            "crane_radius_m": crane_radius_m,
            "sha256_sync_hash": "IN_MEMORY_UNSAVED",
        }
        if output_dxf:
            out_p = Path(output_dxf).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            self.doc.saveas(str(out_p))
            dxf_sha256 = hashlib.sha256(out_p.read_bytes()).hexdigest()
            audit["sha256_sync_hash"] = dxf_sha256
            audit["provenance"] = {
                "dxf_sha256": dxf_sha256,
                "generator": "CadBptcEngine v5.0",
                "drawing_code": "BP-01",
            }
            audit_json_p = out_p.with_suffix(".bptc_audit.json")
            with open(audit_json_p, "w", encoding="utf-8") as f:
                json.dump(audit, f, indent=2, ensure_ascii=False)
            audit["output_dxf"] = str(out_p)
            audit["output_audit_json"] = str(audit_json_p)

        return audit
