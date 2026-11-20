# -*- coding: utf-8 -*-
"""
test_p0_ops_workspace_and_lineage.py — P0-OPS Workspace, Schema-Gate, Lineage & NCR Tests
==========================================================================================

Verifies all 5 planned tests from P0-OPS:
1. `test_01_init_workspace_and_model_schema_validation`
2. `test_02_schema_gate_rejects_invalid_model_and_preserves_version`
3. `test_03_runbook_add_form_and_set_layer_ssot_guard`
4. `test_04_build_dossier_writes_dxf_audit_and_append_only_lineage`
5. `test_05_ncr_backloop_increments_version_and_regenerates_only_affected_sheets`
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
TOOLS_DIR = AGENTS_DIR / "tools"

for _p in (str(TOOLS_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf
import project_ops_manager as ops
from test_cad_multiview_a3 import _build_synthetic_multiview_model


def _build_two_sheet_model() -> dict:
    base = _build_synthetic_multiview_model()
    sh1 = copy.deepcopy(base["sheets"][0])
    sh1["sheet_no"] = "KC.02"
    sh1["title"] = "MẶT BẰNG CỘT & CỌC"
    sh1.pop("filename", None)
    sh1["viewports"][0]["piles"] = [
        {"x": 0.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE1", "id": "P1"},
        {"x": 4.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE3", "id": "P2"},
    ]

    sh2 = copy.deepcopy(base["sheets"][0])
    sh2["sheet_no"] = "KC.03"
    sh2["title"] = "MẶT BẰNG DẦM SÀN TẦNG TRỆT"
    sh2.pop("filename", None)
    # Give KC.03 distinct columns (C99) so NCR targeting C1 only affects KC.02!
    for vp in sh2["viewports"]:
        vp["columns"] = [
            {"id": "C99", "mark": "C99", "kind": "RC", "b_mm": 250, "h_mm": 250, "x0": -0.125, "y0": -0.125, "x1": 0.125, "y1": 0.125},
        ]
    base["sheets"] = [sh1, sh2]
    return base


class TestP0OpsWorkspaceAndLineage(unittest.TestCase):
    def test_01_init_workspace_and_model_schema_validation(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("TEST_PROJ_01", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            self.assertEqual(res["status"], "OK")
            self.assertEqual(res["model_version"], 1)
            for sub in ("model/revisions", "forms", "blocks", "outputs", "audit", "ncr", "nrc"):
                self.assertTrue((proj_dir / sub).is_dir(), f"Missing dir: {sub}")

            model_data = json.loads((proj_dir / "model" / "model.json").read_text(encoding="utf-8"))
            self.assertEqual(model_data["model_id"], "TEST_PROJ_01")
            self.assertEqual(model_data["model_version"], 1)
            self.assertIn("TCVN 5574:2018", model_data["standards_ref"]["standards"])
            self.assertTrue((proj_dir / "model" / "revisions" / "model_v001.json").is_file())
            self.assertTrue((proj_dir / "blocks" / "block_catalog_lock.json").is_file())
            self.assertTrue((proj_dir / "audit" / "lineage.jsonl").is_file())

    def test_02_schema_gate_rejects_invalid_model_and_preserves_version(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("TEST_PROJ_02", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            bad_model = json.loads((proj_dir / "model" / "model.json").read_text(encoding="utf-8"))
            bad_model["sheets"][0]["viewports"][0]["columns"][0]["b_mm"] = -150
            with self.assertRaises(ops.ModelSchemaError):
                ops.validate_model_dict(bad_model)

            # Schema-gate during NCR must also reject negative dimensions without bumping model_version
            with self.assertRaises(ops.ModelSchemaError):
                ops.runbook_apply_ncr(
                    proj_dir,
                    element_id="C1",
                    field="b_mm",
                    new_value=-200,
                    reason="Invalid negative column width",
                )
            model_after = json.loads((proj_dir / "model" / "model.json").read_text(encoding="utf-8"))
            self.assertEqual(model_after["model_version"], 1)
            self.assertEqual(list((proj_dir / "ncr").glob("NCR-*.json")), [])

    def test_03_runbook_add_form_and_set_layer_ssot_guard(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("TEST_PROJ_03", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])

            add_res = ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            self.assertEqual(add_res["status"], "OK")
            form_dxf = Path(add_res["dxf_path"])
            self.assertTrue(form_dxf.is_file())
            self.assertIn("VIEWPORT_TOP", add_res["zones"])

            layer_res = ops.runbook_set_layer(
                proj_dir,
                form_id="FORM_02_MULTIVIEW_A3_BTCT",
                layer_name="DCE_Cot",
                color=6,
                lineweight=35,
            )
            self.assertEqual(layer_res["after"]["color"], 6)
            self.assertEqual(layer_res["after"]["lineweight"], 35)
            doc = ezdxf.readfile(str(form_dxf))
            self.assertEqual(doc.layers.get("DCE_Cot").dxf.color, 6)

            # Reject illegal layer outside SSOT
            with self.assertRaises(ops.IllegalLayerOverrideError):
                ops.runbook_set_layer(
                    proj_dir,
                    form_id="FORM_02_MULTIVIEW_A3_BTCT",
                    layer_name="0_cot_tam",
                    color=1,
                )

    def test_04_build_dossier_writes_dxf_audit_and_append_only_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("TEST_PROJ_04", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            dossier = ops.build_project_dossier(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")

            self.assertEqual(dossier["status"], "DXF_INTEGRITY_PASS")
            self.assertEqual(dossier["sheets_generated"], ["KC.02", "KC.03"])
            self.assertTrue((proj_dir / "outputs" / "KC-02.dxf").is_file())
            self.assertTrue((proj_dir / "outputs" / "KC-03.dxf").is_file())
            self.assertTrue((proj_dir / "outputs" / "dossier_manifest.json").is_file())

            lines = [ln for ln in (proj_dir / "audit" / "lineage.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertEqual(len(lines), 2)
            rec0 = json.loads(lines[0])
            self.assertEqual(rec0["model_id"], "TEST_PROJ_04")
            self.assertEqual(rec0["model_version"], 1)
            self.assertEqual(rec0["form_tier"], "project")
            self.assertEqual(rec0["audit_status"], "DXF_INTEGRITY_PASS")
            self.assertFalse(":" in rec0["dxf_path"])  # POSIX relative path inside workspace

    def test_05_ncr_backloop_increments_version_and_regenerates_only_affected_sheets(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("TEST_PROJ_05", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            ops.build_project_dossier(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")

            kc03_sha_before = ops._sha256_file(proj_dir / "outputs" / "KC-03.dxf")

            ncr_res = ops.runbook_apply_ncr(
                proj_dir,
                element_id="C1",
                field="b_mm",
                new_value=350,
                reason="NCR-001: Tang be rong cot C1 len 350mm",
                source="FIELD_NCR",
                severity="MAJOR",
                auto_regenerate=True,
            )
            self.assertEqual(ncr_res["ncr_id"], "NCR-001")
            self.assertEqual(ncr_res["from_model_version"], 1)
            self.assertEqual(ncr_res["to_model_version"], 2)
            # Only KC.02 contains C1; KC.03 has C99 only
            self.assertEqual(ncr_res["affected_sheets"], ["KC.02"])
            self.assertEqual(ncr_res["regeneration"]["sheets_generated"], ["KC.02"])

            # Verify revision snapshot & NCR files (including mirror nrc/)
            self.assertTrue((proj_dir / "model" / "revisions" / "model_v002.json").is_file())
            self.assertTrue((proj_dir / "ncr" / "NCR-001.json").is_file())
            self.assertTrue((proj_dir / "nrc" / "NCR-001.json").is_file())

            # Verify KC-03.dxf untouched while lineage has 2 (initial) + 1 (KC.02 v2) = 3 lines
            kc03_sha_after = ops._sha256_file(proj_dir / "outputs" / "KC-03.dxf")
            self.assertEqual(kc03_sha_before, kc03_sha_after)

            lines = [ln for ln in (proj_dir / "audit" / "lineage.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertEqual(len(lines), 3)
            last = json.loads(lines[-1])
            self.assertEqual(last["model_version"], 2)
            self.assertEqual(last["sheet_no"], "KC.02")
            self.assertEqual(last["audit_status"], "DXF_INTEGRITY_PASS")


if __name__ == "__main__":
    unittest.main()
