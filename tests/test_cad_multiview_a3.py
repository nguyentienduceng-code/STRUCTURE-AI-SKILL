# -*- coding: utf-8 -*-
"""
test_cad_multiview_a3.py — Integration Tests for Canonical A3 Multi-View CAD Builder
=====================================================================================

Verifies:
1. `cad_plan_engine.export_dce_plan(..., sheet_type="CUSTOM_MULTIVIEW", v6=True)`
   routes cleanly to `cad_multiview_a3.py`, auto-matches sheets by filename stem,
   writes valid AC1021 DXF + `.dce_audit.json` (`OK_V6`), passes `doc.audit()` with
   0 errors / 0 fixes, and emits zero `.pdf` files (`export_pdf=False` default).
2. `mcp_dce_cad_server.render_cad_plan` supports `"CUSTOM_MULTIVIEW"` / `"A3_MULTIVIEW"`
   for both `dry_run=True` (`DRY_RUN_OK`, no disk write) and live export.
3. Physical compliance (`validate_cad(..., profile="physical") == "PASS"`) and
   collision cleanliness (`resolve_cad_collisions(..., dry_run=True)` == 0 collisions).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
TOOLS_DIR = AGENTS_DIR / "tools"

for p in (str(CAD_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
import cad_plan_engine
import mcp_dce_cad_server as mcs


def _build_synthetic_multiview_model() -> dict:
    """Return a compact valid multi-sheet A3 structural JSON fixture."""
    grid_x = [["1", 0.0], ["2", 4.0], ["3", 8.0]]
    grid_y = [["A", 0.0], ["B", 4.5]]
    common_cols = [
        {"id": "C1", "mark": "C1", "kind": "RC", "b_mm": 200, "h_mm": 300, "x0": -0.10, "y0": -0.15, "x1": 0.10, "y1": 0.15},
        {"id": "C2", "mark": "C2", "kind": "RC_STOPPED", "b_mm": 200, "h_mm": 200, "x0": 3.90, "y0": -0.10, "x1": 4.10, "y1": 0.10},
        {"id": "C3", "mark": "C3", "kind": "STEEL_H", "b_mm": 200, "h_mm": 200, "x0": 7.90, "y0": 4.40, "x1": 8.10, "y1": 4.60},
    ]
    common_beams = [
        {
            "mark": "B1X.1",
            "size": "200x350",
            "orient": "X",
            "x0": 0.10,
            "y0": -0.10,
            "x1": 3.90,
            "y1": 0.10,
            "edge_bottom_dash": True,
            "label_side": "above",
        },
        {
            "mark": "B1X.2",
            "size": "200x350",
            "orient": "X",
            "x0": 4.10,
            "y0": -0.10,
            "x1": 7.90,
            "y1": 0.10,
            "edge_top_dash": False,
            "label_x_override": 6.0,
        },
        {
            "mark": "B1Y.1",
            "size": "200x350",
            "orient": "Y",
            "x0": -0.10,
            "y0": 0.15,
            "x1": 0.10,
            "y1": 4.35,
            "edge_right_dash": True,
            "label_side": "right",
        },
    ]

    def _make_vp(vp_id: str, slot: str, title: str, oy_mm: float) -> dict:
        return {
            "id": vp_id,
            "slot": slot,
            "title": title,
            "scale_label": "TL: 1/100",
            "origin_mm": [5200.0, oy_mm],
            "slab_outline": [[0.0, 0.0], [8.0, 0.0], [8.0, 4.5], [0.0, 4.5]],
            "columns": list(common_cols),
            "beams": list(common_beams),
            "voids": [{"x0": 1.2, "y0": 1.5, "x1": 2.4, "y1": 3.0}],
            "hatch_zones": [
                {"bbox": [4.2, 2.5, 5.4, 3.8], "style": "ANSI31", "spacing": 0.2, "angle": 45.0, "label": "-0.050"},
                {"bbox": [5.6, 2.5, 6.8, 3.8], "style": "VOID", "spacing": 0.2, "angle": 0.0, "label": "LIFT"},
            ],
            "extra_lines": [
                {"p1": [0.0, 2.25], "p2": [1.0, 2.25], "dash": True},
                {"p1": [7.0, 0.20], "p2": [7.8, 0.20], "dash": False},
            ],
            "local_dims": [
                {"p1": [1.2, 1.5], "p2": [2.4, 1.5], "base": [1.8, 1.15], "rot": 0.0, "text": "1200"},
            ],
            "notes_box": {
                "title": "GHI CHÚ:",
                "entries": [
                    {"swatch": "HATCH", "text": "SÀN HẠ CỐT 50mm"},
                    {"swatch": "NONE", "text": "BÊ TÔNG CẤP ĐỘ BỀN B25"},
                ],
            },
        }

    return {
        "project": {
            "project_name": "TEST MULTI-VIEW A3",
            "drawing_category": "BẢN VẼ KẾT CẤU",
            "design_stage": "TKTC",
            "year": "2026",
            "scale": 100.0,
            "frame_mm": [42000.0, 29700.0],
            "L_total": 8.0,
            "B_total": 4.5,
            "grid_x": grid_x,
            "grid_y": grid_y,
            "key_plan": {
                "strokes": [
                    [[0.0, 0.0], [100.0, 0.0]],
                    [[100.0, 0.0], [100.0, 60.0]],
                    [[100.0, 60.0], [0.0, 60.0]],
                    [[0.0, 60.0], [0.0, 0.0]],
                ],
                "texts": [
                    {"text": "A", "x": 15.0, "y": 30.0},
                    {"text": "B", "x": 85.0, "y": 30.0},
                ],
            },
        },
        "sheets": [
            {
                "sheet_no": "KC.13",
                "filename": "KC-13.dxf",
                "title": "MẶT BẰNG KẾT CẤU TẦNG 1 & TẦNG 2",
                "viewports": [
                    _make_vp("T1", "TOP", "MẶT BẰNG KẾT CẤU TẦNG 1", 20500.0),
                    _make_vp("T2", "BOT", "MẶT BẰNG KẾT CẤU TẦNG 2", 6500.0),
                ],
            },
            {
                "sheet_no": "KC.14",
                "filename": "KC-14.dxf",
                "title": "MẶT BẰNG KẾT CẤU TẦNG 3 & TẦNG 4",
                "viewports": [
                    _make_vp("T3", "TOP", "MẶT BẰNG KẾT CẤU TẦNG 3", 20500.0),
                    _make_vp("T4", "BOT", "MẶT BẰNG KẾT CẤU TẦNG 4", 6500.0),
                ],
            },
        ],
    }


class TestCadMultiviewA3(unittest.TestCase):
    def test_01_export_dce_plan_custom_multiview_v6_and_stem_matching(self):
        """export_dce_plan with CUSTOM_MULTIVIEW matches sheet by output stem and emits valid v6 DXF."""
        with tempfile.TemporaryDirectory(prefix="mv_a3_eng_") as tmp:
            tmp_dir = Path(tmp)
            model_path = tmp_dir / "synthetic_mv.json"
            model_path.write_text(
                json.dumps(_build_synthetic_multiview_model(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            out_dxf = tmp_dir / "KC-14.dxf"

            engine = cad_plan_engine.export_dce_plan(
                str(out_dxf),
                sheet_type="CUSTOM_MULTIVIEW",
                model_json_path=str(model_path),
                v6=True,
            )
            self.assertEqual(engine.sheet_type, "KC.14")
            self.assertTrue(out_dxf.is_file())
            self.assertEqual(list(tmp_dir.glob("*.pdf")), [])

            audit_sidecar = tmp_dir / "KC-14.dce_audit.json"
            self.assertTrue(audit_sidecar.is_file())
            audit_data = json.loads(audit_sidecar.read_text(encoding="utf-8"))
            self.assertEqual(audit_data.get("v6_status"), "OK_V6")
            prov = audit_data.get("provenance", {})
            self.assertRegex(str(prov.get("dxf_sha256", "")), r"^[0-9a-f]{64}$")
            self.assertGreater(audit_data.get("element_registry", {}).get("total_elements", 0), 0)

            doc = ezdxf.readfile(str(out_dxf))
            self.assertEqual(doc.dxfversion, "AC1021")
            aud = doc.audit()
            self.assertEqual(len(aud.errors), 0)
            self.assertEqual(len(aud.fixes), 0)

            texts = {
                str(e.dxf.text)
                for e in doc.modelspace()
                if e.dxftype() in {"TEXT", "MTEXT"}
            }
            self.assertIn("MẶT BẰNG KẾT CẤU TẦNG 3", texts)
            self.assertIn("MẶT BẰNG KẾT CẤU TẦNG 4", texts)
            self.assertNotIn("MẶT BẰNG KẾT CẤU TẦNG 1", texts)

    def test_02_mcp_render_cad_plan_multiview_dry_run_and_compliance(self):
        """MCP render_cad_plan handles CUSTOM_MULTIVIEW dry_run and A3_MULTIVIEW physical audit cleanly."""
        with tempfile.TemporaryDirectory(prefix="mv_a3_mcp_") as tmp:
            tmp_dir = Path(tmp)
            model_path = tmp_dir / "synthetic_mv.json"
            model_path.write_text(
                json.dumps(_build_synthetic_multiview_model(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            dry_dxf = tmp_dir / "KC-13.dxf"

            dry_res = mcs.render_cad_plan(
                sheet_type="CUSTOM_MULTIVIEW",
                model_json_path=str(model_path),
                output_dxf_path=str(dry_dxf),
                dry_run=True,
                v6=True,
            )
            self.assertEqual(dry_res.get("status"), "DRY_RUN_OK")
            self.assertFalse(dry_res.get("file_written", True))
            self.assertGreater(dry_res.get("modelspace_entities", 0), 0)
            self.assertFalse(dry_dxf.exists())

            live_dxf = tmp_dir / "KC-13.dxf"
            live_res = mcs.render_cad_plan(
                sheet_type="A3_MULTIVIEW",
                model_json_path=str(model_path),
                output_dxf_path=str(live_dxf),
                dry_run=False,
                v6=True,
            )
            self.assertEqual(live_res.get("status"), "OK")
            actual_dxf = Path(live_res["output_dxf"])
            self.assertTrue(actual_dxf.is_file())
            self.assertEqual(list(tmp_dir.glob("*.pdf")), [])

            val_res = mcs.validate_cad(dxf_path=str(actual_dxf), profile="physical")
            self.assertEqual(val_res.get("status"), "PASS")

            col_res = mcs.resolve_cad_collisions(dxf_path=str(actual_dxf), dry_run=True)
            self.assertEqual(col_res.get("status"), "DRY_RUN_OK")
            self.assertEqual(col_res.get("initial_collision_count"), 0)
            self.assertEqual(col_res.get("remaining_collision_count"), 0)


if __name__ == "__main__":
    unittest.main()
