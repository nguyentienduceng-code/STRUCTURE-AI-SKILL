# -*- coding: utf-8 -*-
"""
test_tier2_phase2a_foundation.py — Regression Suite for Tier 2A (Data Backbone & MCP)
======================================================================================

Verifies all Phase 2A upgrades without altering Tier 1 core logic:
  1. MCP `dce-cad` validates all 5 profiles (`full`, `plan`, `physical`, `steel_peb`, `bptc`)
     and `render_cad_plan(..., full_evidence=True)` writes sidecar `semantic_log_format == "v4"`.
  2. `DcePlanEngine._col_centers` accepts negative eccentric offsets `[-size..+size]`
     and rejects out-of-bounds `|offset| > size`.
  3. `dce_xdata_bridge` attaches semantic `(element_id, role, floor_id)` XData, permits
     multiple annotation tags per `element_id`, and detects duplicate `PRIMARY_GEOM` handles
     created by block copying (`COPY` / `WBLOCK`).
  4. `bim_model_translator` avoids 1000x mm->m rescale bug on column `x0` fallback, computes
     Euclidean spans for diagonal beams, and deduplicates `bim_id` for twin-mark beams.
  5. `revit_family_parameter_mapper` routes each structural category to its own Revit
     `TargetFamily` (`StructuralColumnFamily`, `StructuralFramingFamily`, `StructuralWallFamily`,
     `SlabFamily`) and carries `Element_ID` + `SSOT_UUID`.
"""

from __future__ import annotations

import json
import sys
import typing
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
TOOLS_DIR = AGENTS_DIR / "tools"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"

for _p in (str(TOOLS_DIR), str(CAD_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf  # noqa: E402
import bim_model_translator as bim  # noqa: E402
import dce_xdata_bridge as xdb  # noqa: E402
import mcp_dce_cad_server as srv  # noqa: E402
import revit_family_parameter_mapper as rvmap  # noqa: E402
from cad_plan_engine import DcePlanEngine, SCALE_MM, build_structural_model  # noqa: E402
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model  # noqa: E402


class TestMcpProfileExpansion(unittest.TestCase):
    def test_validate_cad_supports_five_profiles(self):
        hints = typing.get_type_hints(srv.validate_cad)
        literal_vals = set(typing.get_args(hints["profile"]))
        self.assertEqual(literal_vals, {"full", "plan", "physical", "steel_peb", "bptc"})

        res_plan = srv.render_cad_plan(sheet_type="KC-02", full_evidence=True)
        self.assertEqual(res_plan.get("status"), "OK")
        self.assertTrue(res_plan.get("full_evidence"))
        dxf_path = Path(res_plan["output_dxf"])
        sidecar_path = dxf_path.with_suffix(".dce_audit.json")
        self.addCleanup(lambda: dxf_path.unlink(missing_ok=True))
        self.addCleanup(lambda: sidecar_path.unlink(missing_ok=True))

        self.assertTrue(sidecar_path.is_file())
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        self.assertEqual(sidecar.get("semantic_log_format"), "v4")

        for profile in ("physical", "plan", "steel_peb", "bptc"):
            with self.subTest(profile=profile):
                audit = srv.validate_cad(str(dxf_path), profile=profile)
                self.assertEqual(audit.get("profile"), profile)
                self.assertIn(audit.get("status"), ("PASS", "FAIL", "NEEDS_REVIEW"))


class TestNegativeColumnOffset(unittest.TestCase):
    def _engine_at_origin(self) -> DcePlanEngine:
        eng = DcePlanEngine(build_structural_model()).setup()
        eng.ox, eng.oy = 0.0, 0.0
        return eng

    def test_negative_eccentric_offsets_accepted_within_bounds(self):
        eng = self._engine_at_origin()
        col = {
            "name": "C_EDGE_R",
            "x": 1.0,
            "y": 2.0,
            "bx": 0.70,
            "by": 1.00,
            "offset_x_mm": -350.0,
            "offset_y_mm": -500.0,
        }
        cx, cy = eng._col_centers(col)
        self.assertAlmostEqual(cx, 650.0, places=3)
        self.assertAlmostEqual(cy, 1500.0, places=3)

        bad = dict(col, offset_x_mm=-0.71 * SCALE_MM)
        with self.assertRaises(ValueError):
            eng._col_centers(bad)


class TestXDataElementIdentity(unittest.TestCase):
    def test_duplicate_primary_geom_vs_multiple_tags(self):
        doc = ezdxf.new("R2007")
        msp = doc.modelspace()
        beam_line = msp.add_line((0, 0), (4000, 0))
        xdb.attach_element_identity(beam_line, "BM-001", role=xdb.ELEMENT_ROLE_PRIMARY, floor_id="L2")
        tag1 = msp.add_text("D1 250x500", dxfattribs={"insert": (1500, 150)})
        tag2 = msp.add_text("D1 SECTION", dxfattribs={"insert": (2500, -150)})
        xdb.attach_element_identity(tag1, "BM-001", role=xdb.ELEMENT_ROLE_TAG, floor_id="L2")
        xdb.attach_element_identity(tag2, "BM-001", role=xdb.ELEMENT_ROLE_DETAIL, floor_id="L2")

        ident = xdb.read_element_identity(beam_line)
        self.assertEqual(ident, {"element_id": "BM-001", "role": "PRIMARY_GEOM", "floor_id": "L2"})

        clean_audit = xdb.audit_duplicate_primary_owners(doc)
        self.assertEqual(clean_audit["status"], "PASS")
        self.assertEqual(clean_audit["unique_primary_ids"], 1)
        self.assertEqual(clean_audit["annotations_linked"], 2)

        copied = beam_line.copy()
        msp.add_entity(copied)
        dup_audit = xdb.audit_duplicate_primary_owners(doc)
        self.assertEqual(dup_audit["status"], "CONFLICT")
        self.assertEqual(len(dup_audit["duplicate_primary_ids"]), 1)
        self.assertEqual(dup_audit["duplicate_primary_ids"][0]["element_id"], "BM-001")
        self.assertEqual(len(dup_audit["duplicate_primary_ids"][0]["handles"]), 2)


class TestBimTranslatorAndMapperFixes(unittest.TestCase):
    def test_column_x0_fallback_stays_millimeters(self):
        m = _build_two_sheet_model()
        vp = m["sheets"][0]["viewports"][0]
        vp["columns"][0].pop("x", None)
        vp["columns"][0].pop("x1", None)
        vp["columns"][0].pop("y1", None)
        vp["columns"][0]["x0"] = 1500.0
        vp["columns"][0]["y0"] = 2500.0
        schema = bim.translate_model_to_bim(m)
        c1 = schema["elements"]["columns"][0]
        self.assertEqual(c1["coordinates"]["x_mm"], 1500.0)
        self.assertEqual(c1["coordinates"]["y_mm"], 2500.0)

    def test_diagonal_beam_and_unique_bim_ids_for_twin_marks(self):
        m = _build_two_sheet_model()
        vp = m["sheets"][0]["viewports"][0]
        vp["beams"] = [
            {"mark": "D1", "size": "250x500", "orient": "DIAGONAL", "x0": 0.0, "y0": 0.0, "x1": 3.0, "y1": 4.0},
            {"mark": "D1", "size": "250x500", "orient": "X", "x0": 4.0, "y0": 0.0, "x1": 10.0, "y1": 0.0},
            {"mark": "D1", "element_id": "BM-EXPLICIT", "floor_id": "L2", "size": "250x600",
             "orient": "X", "x0": 10.0, "y0": 0.0, "x1": 15.0, "y1": 0.0},
        ]
        schema = bim.translate_model_to_bim(m)
        all_beams = schema["elements"]["beams"]
        all_ids = [b["bim_id"] for b in all_beams]
        self.assertEqual(len(all_ids), len(set(all_ids)), f"Duplicate bim_id detected: {all_ids}")

        cctx = f"{m['sheets'][0]['sheet_no']}/{vp['id']}"
        vp0_beams = [b for b in all_beams if b["bim_id"].startswith(f"BEAM-{cctx}-")]
        self.assertEqual(len(vp0_beams), 3)
        self.assertAlmostEqual(vp0_beams[0]["span_m"], 5.0, places=4)
        self.assertNotEqual(vp0_beams[0]["bim_id"], vp0_beams[1]["bim_id"])
        self.assertIn("BM-EXPLICIT", vp0_beams[2]["bim_id"])
        self.assertEqual(vp0_beams[2]["floor_id"], "L2")

    def test_revit_mapper_assigns_distinct_target_families(self):
        m = _build_two_sheet_model()
        vp = m["sheets"][0]["viewports"][0]
        vp["beams"][0]["element_id"] = "BM-001"
        vp["beams"][0]["ssot_uuid"] = "UUID-BM-1"
        vp["walls"] = [{"mark": "V1", "element_id": "WL-001", "thickness_m": 0.2, "length_m": 4.0, "x": 0.0, "y": 0.0}]
        vp["slabs"] = [{"id": "S1", "element_id": "SL-001", "thickness_m": 0.15, "level_m": 3.5}]
        schema = bim.translate_model_to_bim(m)
        mapped = rvmap.map_elements_to_revit(schema)

        self.assertEqual(mapped["columns"][0]["TargetFamily"], "StructuralColumnFamily")
        self.assertEqual(mapped["beams"][0]["TargetFamily"], "StructuralFramingFamily")
        self.assertEqual(mapped["beams"][0]["Element_ID"], "BM-001")
        self.assertEqual(mapped["beams"][0]["SSOT_UUID"], "UUID-BM-1")
        self.assertEqual(mapped["walls"][0]["TargetFamily"], "StructuralWallFamily")
        self.assertEqual(mapped["walls"][0]["Element_ID"], "WL-001")
        self.assertEqual(mapped["slabs"][0]["TargetFamily"], "SlabFamily")
        self.assertEqual(mapped["slabs"][0]["Element_ID"], "SL-001")

        overridden = rvmap.map_elements_to_revit(schema, family="CustomOverride")
        self.assertEqual(overridden["beams"][0]["TargetFamily"], "CustomOverride")


if __name__ == "__main__":
    unittest.main()
