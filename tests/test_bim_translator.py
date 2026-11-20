# -*- coding: utf-8 -*-
"""
test_bim_translator.py — P4.3 BIM / Revit Structural Translation
================================================================

Covers TÁC VỤ P4.3 of `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md` (§3.3):
  - bim_model_translator: model.json -> BIM Intermediate Schema v1.0
      (exact coordinate + section translation; reuses the audited
       DcePlanEngine.column_revit_center formula)
  - revit_family_parameter_mapper: intermediate node -> flat Revit params
  - Acceptance: "chuyển đổi chính xác 100% tọa độ và tiết diện cột/dầm/vách"
      * determinism (same model -> same schema)
      * no fabrication (missing fields -> `Data Missing`, not a guessed value)
      * column centre/section exact against the reference formula
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
for _p in (str(CAD_DIR), str(TOOLS_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bim_model_translator as bim  # noqa: E402
import revit_family_parameter_mapper as rvmap  # noqa: E402
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model  # noqa: E402
from cad_plan_engine import DcePlanEngine  # noqa: E402


def _model_with_concrete_and_rebar() -> dict:
    m = _build_two_sheet_model()
    m["project"]["concrete_grade"] = "B35"
    vp = m["sheets"][0]["viewports"][0]
    c = vp["columns"][0]  # C1, b_mm=200, h_mm=300, centred on grid node (0.0, 0.0)
    c["concrete_grade"] = "B35"
    c["as_prov_cm2"] = 45.0
    c["as_calc_cm2"] = 40.0
    c["rebar_pct"] = 1.4
    c["x"] = 0.0   # explicit centre coordinate -> exercises column_revit_center path
    c["y"] = 0.0
    # Give the model a wall + slab so those types exercise too.
    vp["walls"] = [{"mark": "V1", "thickness_m": 0.2, "length_m": 4.5, "x": 1.0, "y": 2.0}]
    vp["slabs"] = [{"id": "S1", "thickness_m": 0.15, "level_m": 3.5}]
    return m


class TestBimTranslatorExactness(unittest.TestCase):
    def test_column_coordinate_matches_reference_formula(self):
        m = _model_with_concrete_and_rebar()
        schema = bim.translate_model_to_bim(m)
        # Find C1 (first column of first viewport KC.02).
        c1 = next(n for n in schema["elements"]["columns"] if n["mark"] == "C1")
        ref = DcePlanEngine.column_revit_center({"x": 0.0, "y": 0.0, "offset_x_mm": 0, "offset_y_mm": 0})
        self.assertEqual(c1["coordinates"]["x_mm"], ref["x_center_mm"])
        self.assertEqual(c1["coordinates"]["y_mm"], ref["y_center_mm"])
        self.assertEqual(c1["coordinates"]["x_ft"], ref["x_center_ft"])
        self.assertEqual(c1["coordinates"]["y_ft"], ref["y_center_ft"])
        # Section exact (b/h mm).
        self.assertEqual(c1["section"]["b_mm"], 200.0)
        self.assertEqual(c1["section"]["h_mm"], 300.0)
        self.assertEqual(c1["concrete_grade"], "B35")
        self.assertEqual(c1["rebar"]["as_provided_cm2"], 45.0)

    def test_beam_span_and_section(self):
        m = _model_with_concrete_and_rebar()
        schema = bim.translate_model_to_bim(m)
        b1 = next(n for n in schema["elements"]["beams"] if n["mark"] == "B1X.1")
        # B1X.1: X orient, x0=0.10 -> x1=3.90 => span 3.80 m.
        self.assertAlmostEqual(b1["span_m"], 3.80, places=3)
        self.assertEqual(b1["section"]["b_mm"], 200)
        self.assertEqual(b1["section"]["h_mm"], 350)
        self.assertEqual(b1["ifc4_type"], "IfcBeam")

    def test_wall_and_slab_translated(self):
        m = _model_with_concrete_and_rebar()
        schema = bim.translate_model_to_bim(m)
        v1 = next(n for n in schema["elements"]["walls"] if n["mark"] == "V1")
        self.assertEqual(v1["thickness_mm"], 200.0)
        self.assertAlmostEqual(v1["length_m"], 4.5, places=3)
        s1 = next(n for n in schema["elements"]["slabs"] if n["mark"] == "S1")
        self.assertEqual(s1["thickness_mm"], 150.0)
        self.assertAlmostEqual(s1["finished_level_m"], 3.5, places=3)

    def test_deterministic_output(self):
        m = _model_with_concrete_and_rebar()
        a = json.dumps(bim.translate_model_to_bim(m), sort_keys=True)
        b = json.dumps(bim.translate_model_to_bim(m), sort_keys=True)
        self.assertEqual(a, b, "BIM schema must be deterministic for the same model")

    def test_missing_data_is_never_fabricated(self):
        # A column without b_mm / h_mm / concrete_grade must carry Data Missing.
        m = _build_two_sheet_model()
        c = m["sheets"][0]["viewports"][0]["columns"][0]
        c.pop("b_mm", None)
        c.pop("h_mm", None)
        schema = bim.translate_model_to_bim(m)
        c1 = next(n for n in schema["elements"]["columns"] if n["mark"] == c.get("mark"))
        self.assertIsNone(c1["section"]["b_mm"])
        self.assertTrue(any("b_mm/h_mm" in d for d in c1["data_missing"]))
        self.assertTrue(any("concrete_grade" in d for d in c1["data_missing"]))

    def test_completeness_map(self):
        m = _model_with_concrete_and_rebar()
        schema = bim.translate_model_to_bim(m)
        cc = schema["completeness"]["columns"]
        self.assertGreater(cc["total"], 0)
        # C1 (now fully populated with concrete_grade + rebar + section) is complete.
        self.assertGreaterEqual(cc["complete"], 1)
        self.assertLessEqual(cc["complete"], cc["total"])


class TestRevitParameterMapper(unittest.TestCase):
    def test_column_params_flat(self):
        m = _model_with_concrete_and_rebar()
        schema = bim.translate_model_to_bim(m)
        mapped = rvmap.map_elements_to_revit(schema)
        col = next(p for p in mapped["columns"] if p.get("Mark") == "C1")
        self.assertEqual(col["ParameterType"], "StructuralColumn")
        self.assertEqual(col["Column_B"], 200.0)
        self.assertEqual(col["Column_H"], 300.0)
        self.assertEqual(col["ConcreteGrade"], "B35")
        self.assertEqual(col["Mu_Pct"], 1.4)
        self.assertEqual(col["TargetFamily"], "StructuralColumnFamily")

    def test_mapper_roundtrip_with_evidence_schema(self):
        m = _model_with_concrete_and_rebar()
        payload = bim.translate_model_to_bim(m)  # in-memory, no file write
        self.assertEqual(payload["bim_intermediate_schema_version"], bim.BIM_INTERMEDIATE_SCHEMA_VERSION)
        mapped = rvmap.map_elements_to_revit(payload)
        self.assertEqual(set(mapped), {"columns", "beams", "walls", "slabs"})
        # Every mapped dict has a TargetFamily key.
        for kind, recs in mapped.items():
            for rec in recs:
                self.assertIn("TargetFamily", rec)

    def test_export_writes_file(self):
        m = _model_with_concrete_and_rebar()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "bim.json"
            res = bim.export_bim_intermediate(m, str(out), with_evidence=True)
            self.assertTrue(out.is_file())
            self.assertEqual(res["output_path"], str(out))
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("provenance", loaded)
            self.assertTrue(len(loaded["provenance"]["model_sha256"]) == 64)


if __name__ == "__main__":
    unittest.main()
