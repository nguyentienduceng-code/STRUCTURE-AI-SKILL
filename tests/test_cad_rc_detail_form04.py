# -*- coding: utf-8 -*-
"""
test_cad_rc_detail_form04.py — Unit tests cho Sprint 2 (CAD v6.0 Form_04 Native RC Detail & Gates G8.26-G8.28).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf

_AGENTS_DIR = Path(__file__).resolve().parents[1]
_CAD_INT = _AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
_VERIFY_DIR = _AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"
for _p in (str(_CAD_INT), str(_VERIFY_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cad_paperspace_builder import export_with_open_form  # noqa: E402
from cad_rc_detail_engine import (  # noqa: E402
    CATLAI_DETAIL_SPECS,
    build_detail_sheet,
    compute_bbs_rows,
    rebar_unit_weight_kg_per_m,
)
from dce_cad_compliance_checker import audit_dxf_compliance  # noqa: E402


class TestCadRcDetailForm04(unittest.TestCase):
    def test_rebar_schedule_deterministic_math(self) -> None:
        self.assertAlmostEqual(rebar_unit_weight_kg_per_m(16), 1.578, places=2)
        self.assertAlmostEqual(rebar_unit_weight_kg_per_m(20), 2.466, places=2)

        spec = CATLAI_DETAIL_SPECS["KC.03"]()
        bbs = compute_bbs_rows(spec["bbs_rows"])
        self.assertIn("Calculation_Logs", bbs)
        self.assertIn("Standard_Method", bbs)
        self.assertEqual(len(bbs["Calculation_Logs"]), len(spec["bbs_rows"]))
        row_sum = round(sum(r["kl_kg"] for r in bbs["rows"]), 2)
        self.assertAlmostEqual(row_sum, bbs["total_steel_kg"], places=2)
        self.assertGreater(bbs["total_steel_kg"], 500.0)

    def test_kc03_native_form04_gates(self) -> None:
        spec = CATLAI_DETAIL_SPECS["KC.03"]()
        with tempfile.TemporaryDirectory() as tmp:
            out_dxf = Path(tmp) / spec["filename"]
            res = build_detail_sheet(spec, out_dxf)
            self.assertTrue(out_dxf.exists())
            sidecar = out_dxf.with_suffix(".dce_audit.json")
            self.assertTrue(sidecar.exists())
            sc_data = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(sc_data.get("mode"), "DETAIL_NATIVE_FORM04")
            self.assertEqual(res["total_steel_kg"], sc_data["total_steel_kg"])

            phys = audit_dxf_compliance(str(out_dxf), profile="physical")
            self.assertEqual(phys["status"], "PASS", phys.get("issues"))

            det = audit_dxf_compliance(str(out_dxf), profile="detail_v6")
            self.assertEqual(det["status"], "PASS", det.get("issues"))
            self.assertEqual(det["gates_passed"], 3)
            self.assertEqual(det["gates_failed"], 0)
            self.assertTrue(det["full_compliance_verified"])

    def test_kc08_column_multiscale_and_blocks(self) -> None:
        spec = CATLAI_DETAIL_SPECS["KC.08"]()
        with tempfile.TemporaryDirectory() as tmp:
            out_dxf = Path(tmp) / spec["filename"]
            res = build_detail_sheet(spec, out_dxf)
            det = audit_dxf_compliance(str(out_dxf), profile="detail_v6")
            self.assertEqual(det["status"], "PASS", det.get("issues"))

            doc = ezdxf.readfile(str(out_dxf))
            self.assertIn("KC.08", doc.layouts)
            ps = doc.layouts.get("KC.08")
            self.assertGreaterEqual(sum(1 for e in ps if e.dxftype() == "VIEWPORT"), 1)
            named_blocks = [b.name for b in doc.blocks if not b.name.startswith("*")]
            self.assertLessEqual(len(named_blocks), 35)

            for ent in doc.modelspace():
                if ent.dxftype() == "TEXT":
                    self.assertNotIn("Ø", str(ent.dxf.text))
                    self.assertNotIn("●", str(ent.dxf.text))
                elif ent.dxftype() == "INSERT":
                    for att in ent.attribs:
                        self.assertNotIn("Ø", str(att.dxf.text))
                        self.assertNotIn("●", str(att.dxf.text))
            self.assertGreater(res["bbs_rows"], 0)

    def test_export_with_open_form_form04_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dxf = Path(tmp) / "KC-04_delegated.dxf"
            res = export_with_open_form(
                output_dxf_path=str(out_dxf),
                model={"sheet_no": "KC.04"},
                form_id="FORM_04_CHITIET_COC_DAM_COT",
            )
            self.assertEqual(res["status"], "OK")
            self.assertEqual(res["layout_mode"], "model+paperspace")
            self.assertTrue(out_dxf.exists())
            det = audit_dxf_compliance(str(out_dxf), profile="detail_v6")
            self.assertEqual(det["status"], "PASS", det.get("issues"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
