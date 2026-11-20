# -*- coding: utf-8 -*-
"""
test_cad_layer_standard.py — Verification for Unified DCE Pro (Form 2) + DCE STEEL Layer SSOT
=============================================================================================
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
SHARED_CTX = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY_DIR = AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"

for p in (str(SHARED_CTX), str(CAD_DIR), str(VERIFY_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
import cad_layer_standard as cls
import cad_plan_engine as cpe
import cad_multiview_a3 as cma
import dce_cad_compliance_checker as dcc


class TestCadLayerStandard(unittest.TestCase):
    def test_01_ssot_assets_exist_via_relative_paths(self):
        self.assertTrue(cls.STANDARD_JSON_PATH.is_file())
        self.assertTrue(cls.DEFAULT_TEMPLATE_DXF_PATH.is_file())
        self.assertTrue(cls.SEED_TEMPLATE_PATH.is_file())
        std = cls.load_dce_layer_standard()
        self.assertEqual(std["counts"]["form2_btct_46"], 46)
        self.assertEqual(std["counts"]["dce_steel_16"], 16)

    def test_02_exact_parity_with_form2_seed_layers(self):
        seed_doc = ezdxf.readfile(str(cls.SEED_TEMPLATE_PATH))
        specs = cls.get_layer_specs(profile="dce_native")
        for ly in seed_doc.layers:
            name = ly.dxf.name
            self.assertIn(name, specs, f"Missing Form 2 layer {name}")
            self.assertEqual(specs[name]["color"], int(ly.color), f"Color drift on {name}")
            self.assertEqual(specs[name]["linetype"], str(ly.dxf.linetype), f"Linetype drift on {name}")

    def test_03_all_dce_steel_layers_synced_across_engines_and_auditor(self):
        expected_steel = {
            "DCE_MainBeam", "DCE_SubBeam", "DCE_Flange", "DCE_Web", "DCE_Plate",
            "DCE_Bracing", "DCE_Purlin", "DCE_Rod", "DCE_Weld", "DCE_Tole",
            "DCE_Pipe", "DCE_Tube", "DCE_L", "DCE_U", "DCE_TopBars", "DCE_ThepSanGC",
        }
        self.assertTrue(expected_steel.issubset(set(cpe.DCE_PRO_LAYERS.keys())))
        matrix_names = {row[0] for row in cpe.DCE_LAYER_MATRIX}
        self.assertTrue((expected_steel - {"DCE_MainBeam"}).issubset(matrix_names))
        self.assertIn("DCE_MainBeam", matrix_names)
        for name in expected_steel:
            self.assertIn(name.lower(), dcc.DCE_STANDARD_LAYERS)

    def test_04_positive_valid_lineweights_and_dce_native_profile(self):
        specs_native = cls.get_layer_specs(profile="dce_native", include_compat=False)
        for lname, (col, ltype, lw) in cma.A3_LAYER_SPECS.items():
            self.assertIn(lname, specs_native)
            self.assertEqual(col, specs_native[lname]["color"])
            self.assertEqual(ltype, specs_native[lname]["linetype"])
            self.assertEqual(lw, specs_native[lname]["lineweight"])
            self.assertIn(lw, cls.VALID_DXF_LINEWEIGHTS)

    def test_05_compliance_checker_accepts_dce_steel_layers_and_template_audits_cleanly(self):
        tmpl_doc = ezdxf.readfile(str(cls.DEFAULT_TEMPLATE_DXF_PATH))
        self.assertEqual(tmpl_doc.dxfversion, "AC1021")
        aud = tmpl_doc.audit()
        self.assertEqual(len(aud.errors), 0)
        self.assertEqual(len(aud.fixes), 0)
        layer_names = {ly.dxf.name for ly in tmpl_doc.layers}
        for steel_name in ("DCE_Flange", "DCE_Web", "DCE_Plate", "DCE_Bracing", "DCE_Weld", "DCE_Purlin"):
            self.assertIn(steel_name, layer_names)

        with tempfile.TemporaryDirectory(prefix="dce_steel_layer_chk_") as tmp:
            out_dxf = Path(tmp) / "steel_layers_check.dxf"
            doc = ezdxf.readfile(str(cls.DEFAULT_TEMPLATE_DXF_PATH))
            msp = doc.modelspace()
            msp.add_line((0, 0), (6000, 0), dxfattribs={"layer": "DCE_Flange"})
            msp.add_line((0, 200), (6000, 200), dxfattribs={"layer": "DCE_Web"})
            msp.add_lwpolyline([(0, 0), (300, 0), (300, 300), (0, 300)], close=True, dxfattribs={"layer": "DCE_Plate"})
            msp.add_line((0, 0), (6000, 3000), dxfattribs={"layer": "DCE_Bracing"})
            msp.add_text("H300x150", dxfattribs={"layer": "DCE_Name", "height": 200, "insert": (1000, 500)})
            doc.saveas(str(out_dxf))

            res = dcc.audit_dxf_compliance(str(out_dxf), profile="physical")
            self.assertEqual(res["physical_status"], "PASS")
            self.assertEqual(res.get("non_dce_layers", []), [])


if __name__ == "__main__":
    unittest.main()
