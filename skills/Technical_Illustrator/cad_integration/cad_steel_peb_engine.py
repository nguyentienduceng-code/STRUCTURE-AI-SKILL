# -*- coding: utf-8 -*-
"""
Module: cad_steel_peb_engine.py
Author: Antigravity (GEMINI) - DCE Pro CAD Engine v5.0
Description:
    Động cơ Vẽ Kết cấu Thép Tiền chế PEB (Pre-Engineered Building Engine)
    chuẩn TCVN 5575:2024 & TCVN 2737:2023.
    Cung cấp:
      1. ST-01: Mặt đứng khung chính PEB (Tổ hợp vát tiết diện, nhịp L=24-30m, nách cột & đỉnh kèo).
      2. ST-02: Mặt bằng xà gồ mái, thanh chống dọc và hệ giằng mái.
      3. ST-03: Chi tiết nút chân cột & bu lông neo (tỷ lệ 1/10-1/15) trên COMPOSITE_DETAIL_GRID.
      4. ST-04: Chi tiết nút nách cột-kèo và nút đỉnh kèo liên kết bu lông cường độ cao.
      5. Tự động xuất file DXF AC1021 và hồ sơ kiểm toán .steel_audit.json đồng bộ SSOT.
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


class CadSteelPebEngine:
    """
    Engine chuyên biệt vẽ Kết cấu Thép PEB DCE Pro v5.0.
    """

    def __init__(self, template_dxf_path: Optional[str] = None):
        self.template_dxf_path = template_dxf_path or str(cls.DEFAULT_TEMPLATE_DXF_PATH)
        self.doc: Optional[ezdxf.document.Drawing] = None
        self.msp: Any = None
        self.layer_profile = "STEEL_PEB"

    def _init_doc(self) -> None:
        """Khởi tạo tài liệu DXF từ template hạt nhân hoặc bản mới AC1021."""
        if Path(self.template_dxf_path).is_file():
            self.doc = ezdxf.readfile(self.template_dxf_path)
        else:
            self.doc = ezdxf.new("AC1021")
        self.msp = self.doc.modelspace()
        self._ensure_steel_layers()

    def _ensure_steel_layers(self) -> None:
        """Đảm bảo đầy đủ 16 layer của Profile STEEL_PEB trong tài liệu DXF."""
        if not self.doc:
            return
        steel_layers = cls.select_layer_profile("STEEL_PEB")
        existing_layers = {ly.dxf.name for ly in self.doc.layers}
        for name, color, ltype, lw, screening in steel_layers:
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
    # ST-01: MẶT ĐỨNG KHUNG CHÍNH PEB (MAIN FRAME ELEVATION)
    # ==========================================================================

    def generate_st01_main_frame(
        self,
        span_m: float = 24.0,
        eave_h_m: float = 8.0,
        roof_slope_pct: float = 10.0,
        col_start_h: float = 400.0,
        col_end_h: float = 800.0,
        rafter_start_h: float = 800.0,
        rafter_mid_h: float = 550.0,
        output_dxf: Optional[str] = None,
        project_name: str = "DỰ ÁN NHÀ XƯỞNG CÔNG NGHIỆP PEB",
    ) -> Dict[str, Any]:
        """
        Sinh bản vẽ ST-01: Mặt đứng khung chính PEB tổ hợp vát tiết diện.
        Nhịp span_m (m), chiều cao vai cột eave_h_m (m), độ dốc mái roof_slope_pct (%).
        Bố cục COMPOSITE_DETAIL_GRID:
          - Vùng chính (Primary Zone, 60%): Toàn cảnh khung chính nhịp 24m (tỷ lệ 1/100).
          - Ô chi tiết CT-01 (tỷ lệ 1/15): Chi tiết nách cột-kèo (Haunch Connection).
          - Ô chi tiết CT-02 (tỷ lệ 1/15): Chi tiết đỉnh kèo (Apex Connection).
        """
        self._init_doc()
        assert self.msp is not None
        assert self.doc is not None

        L_mm = span_m * 1000.0
        H_eave_mm = eave_h_m * 1000.0
        delta_apex = (L_mm / 2.0) * (roof_slope_pct / 100.0)
        H_apex_mm = H_eave_mm + delta_apex

        detail_specs = [
            {"cell_id": "CT-01", "scale": 15.0, "title": "CHI TIẾT NÚT NÁCH KÈO (CT-01)"},
            {"cell_id": "CT-02", "scale": 15.0, "title": "CHI TIẾT NÚT ĐỈNH KÈO (CT-02)"},
        ]
        layout_spec = DceSheetLayoutPlanner.resolve_composite_grid(
            model_w_mm=L_mm + 4000.0,
            model_h_mm=H_apex_mm + 2500.0,
            detail_specs=detail_specs,
            preferred_scale=100.0,
            sheet_size="A1",
        )
        S = layout_spec.scale

        # Tọa độ gốc khung chính tại Primary Zone
        gx0 = layout_spec.plan_x0 + 2000.0
        gy0 = layout_spec.plan_y0 + 1000.0

        # Cột trái (Trục A: (gx0, gy0) -> (gx0, gy0 + H_eave_mm))
        p_c1_bot = (gx0, gy0)
        p_c1_top = (gx0, gy0 + H_eave_mm)
        c1 = csp.draw_tapered_member(
            self.msp, p_c1_bot, p_c1_top, h_start=col_start_h, h_end=col_end_h, tf=14.0, tw=8.0, bf=250.0
        )

        # Cột phải (Trục B: (gx0 + L_mm, gy0) -> (gx0 + L_mm, gy0 + H_eave_mm))
        p_c2_bot = (gx0 + L_mm, gy0)
        p_c2_top = (gx0 + L_mm, gy0 + H_eave_mm)
        c2 = csp.draw_tapered_member(
            self.msp, p_c2_bot, p_c2_top, h_start=col_start_h, h_end=col_end_h, tf=14.0, tw=8.0, bf=250.0
        )

        # Kèo trái (Nách trái -> Đỉnh kèo)
        p_apex = (gx0 + L_mm / 2.0, gy0 + H_apex_mm)
        r1 = csp.draw_tapered_member(
            self.msp, p_c1_top, p_apex, h_start=rafter_start_h, h_end=rafter_mid_h, tf=12.0, tw=6.0, bf=200.0
        )

        # Kèo phải (Đỉnh kèo -> Nách phải)
        r2 = csp.draw_tapered_member(
            self.msp, p_apex, p_c2_top, h_start=rafter_mid_h, h_end=rafter_start_h, tf=12.0, tw=6.0, bf=200.0
        )

        # Trục định vị A và B
        self.msp.add_line((gx0, gy0 - 1500.0), (gx0, gy0 + H_eave_mm + 1500.0), dxfattribs={"layer": "DCE_Truc"})
        self.msp.add_line((gx0 + L_mm, gy0 - 1500.0), (gx0 + L_mm, gy0 + H_eave_mm + 1500.0), dxfattribs={"layer": "DCE_Truc"})

        # Nhãn cao độ và trục
        self.msp.add_text("TRỤC (A)", dxfattribs={"layer": "DCE_Name", "height": 3.0 * S, "insert": (gx0, gy0 - 1800.0)})
        self.msp.add_text("TRỤC (B)", dxfattribs={"layer": "DCE_Name", "height": 3.0 * S, "insert": (gx0 + L_mm, gy0 - 1800.0)})
        self.msp.add_text(
            f"CAO ĐỘ ĐỈNH KÈO +{H_apex_mm/1000.0:.3f}M",
            dxfattribs={"layer": "DCE_Name", "height": 2.5 * S, "insert": (p_apex[0] - 1500.0, p_apex[1] + 1000.0)}
        )

        # Ký hiệu vị trí nút liên kết N1..N4
        nodes = [
            ("N1", (gx0, gy0 + 400.0)),
            ("N2", (gx0 + 600.0, gy0 + H_eave_mm - 400.0)),
            ("N3", (p_apex[0], p_apex[1] - 400.0)),
            ("N4", (gx0 + L_mm - 600.0, gy0 + H_eave_mm - 400.0)),
        ]
        for nid, (nx, ny) in nodes:
            self.msp.add_circle((nx, ny), radius=200.0, dxfattribs={"layer": "DCE_Name"})
            self.msp.add_text(nid, dxfattribs={"layer": "DCE_Name", "height": 2.0 * S, "insert": (nx - 100.0, ny - 80.0)})

        # 4. VẼ CÁC Ô CHI TIẾT TRÊN COMPOSITE_DETAIL_GRID
        for cell in layout_spec.detail_cells:
            x0, y0, x1, y1 = cell.bbox
            self.msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "DCE_Frame"})
            tx, ty = cell.title_pos
            self.msp.add_text(f"{cell.title} - TỶ LỆ {cell.scale_label}", dxfattribs={"layer": "DCE_Name", "height": 3.0 * S, "insert": (tx - 50.0 * S, ty)})

            cx, cy = cell.inner_origin
            if cell.cell_id == "CT-01":
                # Nút nách kèo: Mặt bích xiên + Mảng bu lông 8.8 + Sườn gia cường
                csp.draw_gusset_plate(
                    self.msp,
                    polygon_pts=[(cx - 300, cy - 350), (cx + 300, cy - 350), (cx + 300, cy + 350), (cx - 300, cy + 350)],
                    thickness_mm=22.0,
                    mark="MB-01",
                    layer="DCE_Steel_Plate",
                )
                csp.draw_bolt_array(
                    self.msp,
                    origin=(cx, cy),
                    rows=4,
                    cols=2,
                    p1=110.0,
                    p2=120.0,
                    d_bolt=24.0,
                    bolt_grade="8.8",
                    layer_bolt="DCE_Steel_Bolt",
                )
                csp.draw_weld_symbol_tcvn(
                    self.msp,
                    target_pt=(cx + 150, cy + 220),
                    leg_hf_mm=8.0,
                    length_lw_mm=280.0,
                    both_sides=True,
                )
            elif cell.cell_id == "CT-02":
                # Nút đỉnh kèo: Mặt bích đỉnh + 6 bu lông M22
                csp.draw_gusset_plate(
                    self.msp,
                    polygon_pts=[(cx - 200, cy - 300), (cx + 200, cy - 300), (cx + 200, cy + 300), (cx - 200, cy + 300)],
                    thickness_mm=20.0,
                    mark="MB-02",
                    layer="DCE_Steel_Plate",
                )
                csp.draw_bolt_array(
                    self.msp,
                    origin=(cx, cy),
                    rows=3,
                    cols=2,
                    p1=100.0,
                    p2=100.0,
                    d_bolt=22.0,
                    bolt_grade="8.8",
                    layer_bolt="DCE_Steel_Bolt",
                )

        # 5. BẢNG THỐNG KÊ VẬT LIỆU THÉP BOM VÀO SIDEBAR
        bom_items = [
            {"mark": "C-01", "spec": f"Cột vát H({int(col_start_h)}-{int(col_end_h)})x250x8x14", "steel_grade": "Q345B", "qty": 2, "total_weight_kg": c1["weight_kg"] * 2, "note": "Cột chính"},
            {"mark": "K-01", "spec": f"Kèo vát H({int(rafter_start_h)}-{int(rafter_mid_h)})x200x6x12", "steel_grade": "Q345B", "qty": 2, "total_weight_kg": r1["weight_kg"] * 2, "note": "Kèo chính"},
            {"mark": "MB-01", "spec": "PL22x600x700", "steel_grade": "SS400", "qty": 4, "total_weight_kg": 22 * 600 * 700 * 1e-9 * 7850 * 4, "note": "Mặt bích nách"},
            {"mark": "MB-02", "spec": "PL20x400x600", "steel_grade": "SS400", "qty": 2, "total_weight_kg": 20 * 400 * 600 * 1e-9 * 7850 * 2, "note": "Mặt bích đỉnh"},
        ]
        bom_data = csp.compute_steel_bom(bom_items)

        # Khung bản vẽ A1 & Sidebar
        in_x0, in_y0, in_x1, in_y1 = layout_spec.inner_bbox
        self.msp.add_lwpolyline([(in_x0, in_y0), (in_x1, in_y0), (in_x1, in_y1), (in_x0, in_y1)], close=True, dxfattribs={"layer": "DCE_Frame"})
        sb_x = layout_spec.sidebar_divider_x
        self.msp.add_line((sb_x, in_y0), (sb_x, in_y1), dxfattribs={"layer": "DCE_Frame"})

        # In BOM
        sb_top = in_y1 - 20.0 * S
        self.msp.add_text("BẢNG THỐNG KÊ VẬT LIỆU KHUNG PEB (BOM)", dxfattribs={"layer": "DCE_Name", "height": 2.5 * S, "insert": (sb_x + 5.0 * S, sb_top)})
        row_y = sb_top - 12.0 * S
        col_offsets = [0.0, 8.0 * S, 25.0 * S, 60.0 * S, 80.0 * S, 95.0 * S, 115.0 * S, 135.0 * S]
        for idx, h_txt in enumerate(["STT", "Hiệu", "Quy cách", "Mác", "SL", "Dài", "Tổng KL", "Ghi chú"]):
            if idx < len(col_offsets):
                self.msp.add_text(h_txt, dxfattribs={"layer": "DCE_Schedule", "height": 1.6 * S, "insert": (sb_x + 5.0 * S + col_offsets[idx], row_y)})

        for r in bom_data["rows"]:
            row_y -= 8.0 * S
            disp_vals = [r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[8]]
            for idx, val in enumerate(disp_vals):
                if idx < len(col_offsets):
                    self.msp.add_text(val, dxfattribs={"layer": "DCE_Schedule", "height": 1.5 * S, "insert": (sb_x + 5.0 * S + col_offsets[idx], row_y)})

        row_y -= 12.0 * S
        self.msp.add_text(f"TỔNG KHỐI LƯỢNG THÉP: {bom_data['total_weight_kg']:.1f} KG", dxfattribs={"layer": "DCE_Name", "height": 2.2 * S, "insert": (sb_x + 5.0 * S, row_y)})

        # Khung tên chính
        tb_x0, tb_y0, tb_x1, tb_y1 = layout_spec.title_block_bbox
        self.msp.add_lwpolyline([(tb_x0, tb_y0), (tb_x1, tb_y0), (tb_x1, tb_y1), (tb_x0, tb_y1)], close=True, dxfattribs={"layer": "DCE_Frame"})
        self.msp.add_text(project_name, dxfattribs={"layer": "DCE_Name", "height": 3.2 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 35.0 * S)})
        self.msp.add_text(f"MẶT ĐỨNG KHUNG CHÍNH PEB (NHỊP L={int(span_m)}M)", dxfattribs={"layer": "DCE_Name", "height": 2.8 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 20.0 * S)})
        self.msp.add_text(f"BẢN VẼ SỐ: ST-01 | TỶ LỆ CHÍNH: 1/{int(S)}", dxfattribs={"layer": "DCE_Schedule", "height": 2.0 * S, "insert": (tb_x0 + 10.0 * S, tb_y0 + 8.0 * S)})

        # Lưu hồ sơ audit SSOT
        audit_dossier = {
            "schema_version": "5.0",
            "profile": "STEEL_PEB",
            "drawing_code": "ST-01",
            "title": f"Mặt đứng khung chính PEB nhịp {span_m}m",
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
                "generator": "CadSteelPebEngine v5.0",
                "drawing_code": "ST-01",
            }
            audit_json_p = out_p.with_suffix(".steel_audit.json")
            with open(audit_json_p, "w", encoding="utf-8") as f:
                json.dump(audit_dossier, f, indent=2, ensure_ascii=False)
            audit_dossier["output_dxf"] = str(out_p)
            audit_dossier["output_audit_json"] = str(audit_json_p)

        return audit_dossier
