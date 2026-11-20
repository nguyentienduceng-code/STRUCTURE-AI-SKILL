# -*- coding: utf-8 -*-
"""
test_p1_schema_gate_and_merge_lane.py — P0-Hardening & P1 Schema-Gate Authoring Tests
======================================================================================

Covers all items in `CLAUDE_P0OPS_REVIEW_AND_P1_SPEC.md`:
  - F1: `DXF_INTEGRITY_PASS` label + `--compliance {physical,plan,full}`
  - F2/F3: `model_schema.json` flexible `standards` + working `anyOf` for `project.L_total/B_total`
  - F4/F5/F6/F7: SSOT `BLOCK_CATALOG_VERSION`, `forms/revisions/form_v00N`, unified element iter, strict `jsonschema`
  - P1 `model_diff.py`: extract `layer`, `titleblock`, `zone`, `axes` diffs & Schema-Gate reject (`E005`/`E006`)
  - P1 3 merge-lane MCP tools: `open_form`, `diff_form`, `apply_agent_changes` (region-scoped `DCE_AGENT_OWNED`)
  - Khối 3: `full_evidence=False` vs `full_evidence=True` honest Filter 8 telemetry
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TESTS_DIR.parent
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY_DIR = AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"
TOOLS_DIR = AGENTS_DIR / "tools"

for _p in (str(CAD_DIR), str(VERIFY_DIR), str(TOOLS_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf
import cad_plan_engine
import dce_block_catalog
import mcp_dce_cad_server as mcs
import model_diff
import project_ops_manager as ops
from dce_cad_compliance_checker import audit_dxf_compliance
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model


class TestP1SchemaGateAndMergeLane(unittest.TestCase):
    def test_01_f1_compliance_labels_and_full_needs_review(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P1_F1_PROJ", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")

            d_phys = ops.build_project_dossier(proj_dir, compliance="physical", sheet_numbers=["KC.02"])
            self.assertEqual(d_phys["status"], "DXF_INTEGRITY_PASS")
            self.assertEqual(d_phys["records"][0]["audit_status"], "DXF_INTEGRITY_PASS")

            d_full = ops.build_project_dossier(proj_dir, compliance="full", sheet_numbers=["KC.02"])
            self.assertEqual(d_full["status"], "NEEDS_REVIEW")
            self.assertEqual(d_full["records"][0]["audit_status"], "NEEDS_REVIEW")

    def test_02_f2_f3_f4_f5_f7_schema_revisions_and_ssot(self):
        # F4: catalog version from SSOT
        self.assertEqual(ops._block_catalog_version(), dce_block_catalog.get_block_catalog_version())

        # F2: simple single TCVN standard accepted
        simple_model = ops.enrich_model_metadata(_build_two_sheet_model(), "P1_F2")
        simple_model["standards_ref"]["standards"] = {"TCVN 5574:2018": "BTCT"}
        ops.validate_model_dict(simple_model)

        # F3: fixed anyOf rejects model missing both sheets and project.L_total/B_total
        bad_dims = copy.deepcopy(simple_model)
        bad_dims.pop("sheets", None)
        bad_dims["project"].pop("L_total", None)
        bad_dims["project"].pop("B_total", None)
        with self.assertRaises(ops.ModelSchemaError):
            ops.validate_model_dict(bad_dims)

        # F7: missing jsonschema raises ImportError/ModelSchemaError (no silent pass)
        with patch.object(ops, "jsonschema", None):
            with self.assertRaises((ops.ModelSchemaError, ImportError)):
                ops.validate_model_dict(simple_model)
            with self.assertRaises((ValueError, ImportError)):
                ops.validate_ncr_dict({"ncr_id": "NCR-001"})

        # F5: form revisions increment on add-form and set-layer
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P1_F5_PROJ", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            r1 = ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            self.assertEqual(r1["form_version"], 1)
            r2 = ops.runbook_set_layer(proj_dir, "FORM_02_MULTIVIEW_A3_BTCT", "DCE_Cot", color=3)
            self.assertEqual(r2["form_version"], 2)
            self.assertTrue((proj_dir / "forms" / "revisions" / "Form_02_MultiView_A3_BTCT_v001.dxf").is_file())
            self.assertTrue((proj_dir / "forms" / "revisions" / "Form_02_MultiView_A3_BTCT_v002.dxf").is_file())

    def test_03_extract_form_diff_across_layers_title_zone_and_axes(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P1_DIFF_PROJ", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            add_r = ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            user_dxf = Path(add_r["dxf_path"])

            # Simulate engineer editing DXF in AutoCAD: layer color, titleblock, zone shift, and shifted axis 2
            doc = ezdxf.readfile(str(user_dxf))
            doc.layers.get("DCE_Cot").dxf.color = 6
            msp = doc.modelspace()
            for ent in msp:
                if ent.dxftype() == "INSERT" and ent.dxf.name == "DCE_TITLEBLOCK_A3":
                    for att in ent.attribs:
                        if att.dxf.tag == "TEN_CONG_TRINH":
                            att.dxf.text = "BIET THU Q2 MOI"
                elif ent.dxftype() == "LWPOLYLINE" and ent.dxf.layer.upper() == "DCE_ZONE_VIEWPORT_TOP":
                    ent.set_points([(x + 500.0, y) for x, y in ent.get_points("xy")], format="xy")
            # Insert reference Dce_KhTenTruc bubbles matching origin_x=5200mm, with Axis "2" moved from 4.0m to 4.6m (x=9800)
            for lbl, gx_mm in (("1", 5200.0), ("2", 9800.0), ("3", 13200.0)):
                bref = msp.add_blockref("Dce_KhTenTruc", (gx_mm, 16000.0), dxfattribs={"layer": "DCE_Block", "xscale": 100.0, "yscale": 100.0})
                bref.add_auto_attribs({"TRUC": lbl})
            doc.saveas(str(user_dxf))

            diff = mcs.diff_form(str(proj_dir), form_id="FORM_02_MULTIVIEW_A3_BTCT", baseline="ssot")
            self.assertEqual(diff["status"], "OK")
            self.assertEqual(len(diff["layer_changes"]), 1)
            self.assertEqual(diff["layer_changes"][0]["layer"], "DCE_Cot")
            self.assertEqual(len(diff["zone_changes"]), 1)
            self.assertAlmostEqual(diff["zone_changes"][0]["delta_center_mm"][0], 500.0, delta=1.0)
            self.assertEqual(diff["titleblock_changes"][0]["after"], "BIET THU Q2 MOI")
            self.assertEqual(len(diff["axes_changes"]), 1)
            self.assertEqual(diff["axes_changes"][0]["axis_label"], "2")
            self.assertAlmostEqual(diff["axes_changes"][0]["new_m"], 4.6, delta=0.01)

    def test_04_schema_gate_rejects_bad_scale_non_monotonic_axis_and_missing_zone(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P1_GATE_PROJ", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            add_r = ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            user_dxf = Path(add_r["dxf_path"])

            # Bad TY_LE = "1/0" -> E005_INVALID_DIFF
            doc = ezdxf.readfile(str(user_dxf))
            for ent in doc.modelspace():
                if ent.dxftype() == "INSERT" and ent.dxf.name == "DCE_TITLEBLOCK_A3":
                    for att in ent.attribs:
                        if att.dxf.tag == "TY_LE":
                            att.dxf.text = "1/0"
            doc.saveas(str(user_dxf))
            d_bad_scale = mcs.diff_form(str(proj_dir), form_id="FORM_02_MULTIVIEW_A3_BTCT")
            self.assertEqual(d_bad_scale["status"], "ERROR")
            self.assertEqual(d_bad_scale["code"], "E005_INVALID_DIFF")

            # Missing zone -> open_form INVALID & diff_form ERROR
            for ent in list(doc.modelspace()):
                if ent.dxftype() == "LWPOLYLINE" and ent.dxf.layer.upper() == "DCE_ZONE_VIEWPORT_TOP":
                    doc.modelspace().delete_entity(ent)
            doc.saveas(str(user_dxf))
            open_bad = mcs.open_form(str(proj_dir), form_id="FORM_02_MULTIVIEW_A3_BTCT")
            self.assertEqual(open_bad["status"], "INVALID")

            # Non-monotonic axis patch -> apply_agent_changes REJECTED (E006) without bumping version
            bad_patch = {"model_patches": [{"path": "project.grid_x[1][1]", "value": 9.5}]}
            rej = mcs.apply_agent_changes(str(proj_dir), changes=bad_patch, commit=True)
            self.assertEqual(rej["status"], "REJECTED")
            self.assertEqual(rej["code"], "E006_SCHEMA_GATE_REJECTED")
            self.assertFalse(rej["committed"])
            m_now = json.loads((proj_dir / "model" / "model.json").read_text(encoding="utf-8"))
            self.assertEqual(m_now["model_version"], 1)

    def test_05_mcp_merge_lane_preserves_user_geom_and_regenerates_affected_sheet(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P1_MERGE_PROJ", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            add_r = ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            ops.build_project_dossier(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            kc03_sha_before = ops._sha256_file(proj_dir / "outputs" / "KC-03.dxf")

            # User adds custom circle inside Form DXF
            user_dxf = Path(add_r["dxf_path"])
            doc = ezdxf.readfile(str(user_dxf))
            doc.modelspace().add_circle((39100.0, 14900.0), 250.0, dxfattribs={"layer": "DCE_Frame"})
            for ent in doc.modelspace():
                if ent.dxftype() == "INSERT" and ent.dxf.name == "DCE_TITLEBLOCK_A3":
                    for att in ent.attribs:
                        if att.dxf.tag == "TEN_CONG_TRINH":
                            att.dxf.text = "CONG TRINH MERGE LANE"
            doc.saveas(str(user_dxf))

            # Dry-run apply_agent_changes first
            dry = mcs.apply_agent_changes(str(proj_dir), commit=False)
            self.assertEqual(dry["status"], "DRY_RUN_OK")
            self.assertEqual(dry["candidate_model_version"], 2)

            # Commit scoped ONLY to KC.02
            diff = mcs.diff_form(str(proj_dir), form_id="FORM_02_MULTIVIEW_A3_BTCT")
            diff["affected_sheets"] = ["KC.02"]
            applied = mcs.apply_agent_changes(str(proj_dir), changes=diff, commit=True)
            self.assertEqual(applied["status"], "OK")
            self.assertEqual(applied["to_model_version"], 2)
            self.assertEqual(applied["region_scope_appid"], "DCE_AGENT_OWNED")
            self.assertEqual(applied["dossier_status"], "DXF_INTEGRITY_PASS")

            # User geometry preserved on KC-02.dxf & KC-03.dxf untouched
            out_doc = ezdxf.readfile(str(proj_dir / "outputs" / "KC-02.dxf"))
            user_circles = [
                e for e in out_doc.modelspace()
                if e.dxftype() == "CIRCLE" and abs(e.dxf.center.x - 39100.0) < 1.0
            ]
            self.assertEqual(len(user_circles), 1)
            self.assertEqual(ops._sha256_file(proj_dir / "outputs" / "KC-03.dxf"), kc03_sha_before)

    def test_06_full_evidence_gated_off_vs_on(self):
        with tempfile.TemporaryDirectory() as td:
            off_dxf = Path(td) / "kc02_off.dxf"
            cad_plan_engine.export_dce_plan(str(off_dxf), sheet_type="KC-02", v6=True, full_evidence=False)
            off_sc = json.loads(off_dxf.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
            self.assertNotIn("semantic_log_format", off_sc)
            off_aud = audit_dxf_compliance(str(off_dxf), profile="plan")
            self.assertEqual(off_aud["status"], "NEEDS_REVIEW")

            on_dxf = Path(td) / "kc02_on.dxf"
            cad_plan_engine.export_dce_plan(str(on_dxf), sheet_type="KC-02", v6=True, full_evidence=True)
            on_sc = json.loads(on_dxf.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
            self.assertEqual(on_sc["semantic_log_format"], "v4")
            self.assertIn("DCE_Cot_Block", on_sc["blocks_defined"])
            self.assertIn("DCE_TenCauKien", on_sc["blocks_defined"])
            on_aud = audit_dxf_compliance(str(on_dxf), profile="plan")
            # Gate evaluation runs genuinely (not NEEDS_REVIEW for missing semantic format)
            self.assertNotIn("không xuất V4 semantic gate logs", " ".join(on_aud.get("metadata_issues", [])))


if __name__ == "__main__":
    unittest.main()
