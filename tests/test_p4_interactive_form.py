# -*- coding: utf-8 -*-
"""
test_p4_interactive_form.py — P4.1 Interactive Form Modification Engine
======================================================================

Covers TÁC VỤ P4.1 of `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`:
  - NonDestructivePatcher (a.k.a. the spec's `non_destructive_patcher.py`)
  - open_form / diff_form / gate_model / apply_and_regen one-shot `patch()`
  - Structural schema gate (concrete grade, section floor, rebar band -> E006)
  - Full error taxonomy: E001, E002, E003, E005, E006
  - Selective regeneration + model v->v+1 + revision snapshot

Conventions mirror `test_p1_schema_gate_and_merge_lane.py` and
`test_p0_ops_workspace_and_lineage.py` (init_project_workspace + _build_two_sheet_model).
"""

from __future__ import annotations

import copy
import hashlib
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

import ezdxf
import cad_form_patcher as cfp
import model_diff as mdf
import project_ops_manager as ops
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model

FORM = "FORM_02_MULTIVIEW_A3_BTCT"


def _proj_with_form(base_dir: str, code: str = "P4_PROJ"):
    """Create a project workspace + the two-sheet model + an added project-tier Form."""
    res = ops.init_project_workspace(code, base_dir=base_dir, seed_model=_build_two_sheet_model())
    proj_dir = Path(res["project_dir"])
    add_r = ops.runbook_add_form(proj_dir, form_id=FORM)
    return proj_dir, Path(add_r["dxf_path"])


def _project_fields(proj_dir: Path) -> dict:
    return json.loads((proj_dir / "model" / "model.json").read_text(encoding="utf-8")).get("project", {})


def _inject_project_field(proj_dir: Path, **fields):
    mp = proj_dir / "model" / "model.json"
    model = json.loads(mp.read_text(encoding="utf-8"))
    model.setdefault("project", {}).update(fields)
    ops._atomic_write_json(mp, model)


# ============================================================================
# 1. Module-level unit tests: concrete-grade parser + structural gate
# ============================================================================

class TestP4StructuralGateUnit(unittest.TestCase):
    def test_concrete_grade_parsing(self):
        self.assertEqual(cfp.parse_concrete_grade("B35"), 35)
        self.assertEqual(cfp.parse_concrete_grade("B30"), 30)
        self.assertEqual(cfp.parse_concrete_grade("M400"), 30)
        self.assertEqual(cfp.parse_concrete_grade("M350"), 25)
        self.assertIsNone(cfp.parse_concrete_grade(None))
        self.assertIsNone(cfp.parse_concrete_grade("X100"))

    def test_clean_model_passes_gate(self):
        model = _build_two_sheet_model()
        ops.enrich_model_metadata(model, "CLEAN_P4")
        self.assertEqual(cfp.structural_schema_gate(model), [])

    def test_gate_rejects_b50_and_rebar_and_section(self):
        m = _build_two_sheet_model()
        ops.enrich_model_metadata(m, "BAD_P4")
        m["project"]["concrete_grade"] = "B50"
        m["sheets"][0]["viewports"][0]["columns"][0]["b_mm"] = 50
        m["sheets"][0]["viewports"][0]["columns"][0]["rebar_pct"] = 4.0
        v = cfp.structural_schema_gate(m)
        codes = set(x["field"] for x in v)
        self.assertIn("concrete_grade", codes)
        self.assertIn("column_section[0]", codes)
        self.assertIn("rebar_pct", codes)
        self.assertTrue(all(x["code"] == "E006_SCHEMA_GATE_REJECTED" for x in v))

    def test_b40_allowed_only_with_note(self):
        m = _build_two_sheet_model()
        ops.enrich_model_metadata(m, "B40")
        m["project"]["concrete_grade"] = "B40"
        self.assertNotEqual(cfp.structural_schema_gate(m), [])
        m["project"]["concrete_grade_note"] = "Chủ đầu tư yêu cầu B40"
        self.assertEqual(cfp.structural_schema_gate(m), [])


# ============================================================================
# 2. Full patcher flow — error taxonomy
# ============================================================================

class TestP4PatcherFlow(unittest.TestCase):
    def test_previous_revision_matches_across_mcp_and_patcher(self):
        import mcp_dce_cad_server as server

        with tempfile.TemporaryDirectory() as tmp:
            project, form = _proj_with_form(tmp)
            revisions = project / "forms" / "revisions"
            # Move the seeded history aside to model a project without snapshots.
            revisions.rename(project / "forms" / "seeded_revisions")
            revisions.mkdir()
            (revisions / f"{form.stem}_vbackup.dxf").touch()
            (revisions / f"{form.stem}_v99.dxf").mkdir()
            patcher = cfp.NonDestructivePatcher(project, FORM, baseline="prev_rev")

            missing = server.diff_form(str(project), FORM, "prev_rev")
            self.assertEqual(missing.get("code"), "E001_FILE_NOT_FOUND")
            with self.assertRaises(mdf.DiffValidationError) as caught:
                patcher.diff_form()
            self.assertEqual(caught.exception.code, "E001_FILE_NOT_FOUND")

            for version, expected in ((9, 9), (10, 9), (11, 10)):
                snapshot = revisions / f"{form.stem}_v{version}.dxf"
                drawing = ezdxf.readfile(form)
                drawing.layers.new(f"REVISION_{version}")
                drawing.saveas(snapshot)
                for diff in (server.diff_form(str(project), FORM, "prev_rev"), patcher.diff_form()):
                    expected_file = revisions / f"{form.stem}_v{expected}.dxf"
                    self.assertEqual(Path(diff["baseline_form_dxf"]), expected_file)
                    removed = [c["layer"] for c in diff["layer_changes"] if c["kind"] == "removed"]
                    self.assertEqual(removed, [f"REVISION_{expected}"])
                    self.assertEqual(diff["baseline_form_sha256"], hashlib.sha256(expected_file.read_bytes()).hexdigest())
                    self.assertEqual(diff["user_form_sha256"], hashlib.sha256(form.read_bytes()).hexdigest())

    def test_e001_missing_model_ssot(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P4_E001", base_dir=td, seed_model=_build_two_sheet_model())
            proj = Path(res["project_dir"])
            (proj / "model" / "model.json").unlink()  # remove the Engineering SSOT
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            with self.assertRaises(mdf.DiffValidationError) as ctx:
                p.diff_form()
            self.assertEqual(ctx.exception.code, "E001_FILE_NOT_FOUND")

    def test_e002_missing_required_zone(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_E002")
            doc = ezdxf.readfile(str(form_dxf))
            msp = doc.modelspace()
            for ent in list(msp):
                if ent.dxftype() == "LWPOLYLINE" and str(getattr(ent.dxf, "layer", "")).upper() == "DCE_ZONE_VIEWPORT_TOP":
                    msp.delete_entity(ent)
            doc.saveas(str(form_dxf))
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            r = p.open_form()
            self.assertEqual(r["status"], "INVALID")
            self.assertEqual(r["dominant_code"], "E002_TEMPLATE_ZONE_MISSING")

    def test_e003_titleblock_attdef_missing(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_E003")
            doc = ezdxf.readfile(str(form_dxf))
            block = doc.blocks.get("DCE_TITLEBLOCK_A3")
            self.assertIsNotNone(block, "title block should be defined in the form")
            target = "TEN_CONG_TRINH"
            for e in list(block):
                if e.dxftype() == "ATTDEF" and e.dxf.tag == target:
                    block.delete_entity(e)
            doc.saveas(str(form_dxf))
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            r = p.open_form()
            self.assertEqual(r["status"], "INVALID")
            self.assertEqual(r["dominant_code"], "E003_TITLEBLOCK_ATTDEF_MISSING")

    def test_e005_invalid_diff_bad_scale(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_E005")
            doc = ezdxf.readfile(str(form_dxf))
            for ent in doc.modelspace():
                if ent.dxftype() == "INSERT" and ent.dxf.name == "DCE_TITLEBLOCK_A3":
                    for att in ent.attribs:
                        if att.dxf.tag == "TY_LE":
                            att.dxf.text = "1/0"
            doc.saveas(str(form_dxf))
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            r = p.diff_form()
            self.assertEqual(r["status"], "ERROR")
            self.assertEqual(r["code"], "E005_INVALID_DIFF")

    def test_e006_gate_blocks_commit_on_bad_model(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_E006")
            _inject_project_field(proj, concrete_grade="B50")
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            gate = p.gate_model()
            self.assertEqual(gate["status"], "REJECTED")
            self.assertEqual(gate["code"], "E006_SCHEMA_GATE_REJECTED")
            r = p.apply_and_regen(changes={}, commit=False)
            self.assertEqual(r["status"], "REJECTED")
            self.assertEqual(r["code"], "E006_SCHEMA_GATE_REJECTED")
            self.assertFalse(r["committed"])
            self.assertEqual(json.loads((proj / "model" / "model.json").read_text(encoding="utf-8"))["model_version"], 1)

    def test_dry_run_does_not_bump_version(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_DRY")
            p = cfp.NonDestructivePatcher(proj, form_id=FORM)
            r = p.apply_and_regen(changes={}, commit=False)
            self.assertEqual(r["status"], "DRY_RUN_OK")
            self.assertEqual(r["from_model_version"], 1)
            self.assertEqual(r["candidate_model_version"], 2)
            self.assertEqual(json.loads((proj / "model" / "model.json").read_text(encoding="utf-8"))["model_version"], 1)
            self.assertFalse((proj / "model" / "revisions" / "model_v002.json").exists())


# ============================================================================
# 3. Success path: selective regeneration + SSOT v->v+1 + user-geometry safety
# ============================================================================

class TestP4SelectiveRegen(unittest.TestCase):
    def test_commit_bumps_version_and_selectively_regen(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_OK")

            # Establish a baseline: first commit regenerates both sheets (v -> 2).
            # A grid_x move changes geometry so the regenerated DXF bytes genuinely differ.
            first = cfp.NonDestructivePatcher(proj, form_id=FORM).apply_and_regen(
                changes={"model_patches": [{"path": "project.grid_x[1][1]", "value": 4.5}],
                         "affected_sheets": ["KC.02", "KC.03"]},
                commit=True)
            self.assertEqual(first["status"], "OK")
            self.assertEqual(first["to_model_version"], 2)
            sha_before = {f.name: ops._sha256_file(proj / "outputs" / f.name)
                          for f in (proj / "outputs").glob("*.dxf")}
            self.assertIn("KC-02.dxf", sha_before)
            self.assertIn("KC-03.dxf", sha_before)
            lineage_before = len([ln for ln in (proj / "audit" / "lineage.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()])

            # Second commit moves axis 2 further (4.5 -> 4.6) affecting ONLY KC.02 -> selective regen.
            second = cfp.NonDestructivePatcher(proj, form_id=FORM).apply_and_regen(
                changes={"model_patches": [{"path": "project.grid_x[1][1]", "value": 4.6}],
                         "affected_sheets": ["KC.02"]},
                commit=True)
            self.assertEqual(second["status"], "OK")
            self.assertEqual(second["to_model_version"], 3)
            self.assertEqual(second["affected_sheets"], ["KC.02"])
            self.assertIn("KC.03", second["preserved_sheets"])
            self.assertTrue((proj / "model" / "revisions" / "model_v003.json").is_file())
            self.assertAlmostEqual(
                json.loads((proj / "model" / "model.json").read_text(encoding="utf-8"))["project"]["grid_x"][1][1],
                4.6, delta=1e-6)

            # Non-affected sheet bytes must be UNCHANGED; affected sheet regenerated.
            self.assertEqual(ops._sha256_file(proj / "outputs" / "KC-03.dxf"), sha_before["KC-03.dxf"])
            self.assertNotEqual(ops._sha256_file(proj / "outputs" / "KC-02.dxf"), sha_before["KC-02.dxf"])

            # Lineage grew by exactly one (only the regenerated sheet was appended).
            lineage_after = len([ln for ln in (proj / "audit" / "lineage.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()])
            self.assertEqual(lineage_after, lineage_before + 1)

    def test_one_shot_patch_clean_form(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_ONE")
            r = cfp.patch_project(proj, form_id=FORM, commit=False)
            self.assertEqual(r["status"], "DRY_RUN_OK")
            self.assertEqual(r["candidate_model_version"], 2)

    def test_non_destructive_user_entity_preserved_on_regen(self):
        with tempfile.TemporaryDirectory() as td:
            proj, form_dxf = _proj_with_form(td, "P4_ND")
            cfp.patch_project(proj, form_id=FORM, commit=False)

            # Engineer adds a custom circle inside the project-tier Form (AutoCAD edit).
            doc = ezdxf.readfile(str(form_dxf))
            doc.modelspace().add_circle((39100.0, 14900.0), 250.0, dxfattribs={"layer": "DCE_Frame"})
            doc.saveas(str(form_dxf))

            changes = {"model_patches": [{"path": "project.design_stage", "value": "TKCS"}],
                      "affected_sheets": ["KC.02"]}
            r = cfp.NonDestructivePatcher(proj, form_id=FORM).apply_and_regen(changes=changes, commit=True)
            self.assertEqual(r["status"], "OK")
            reg = ezdxf.readfile(str(proj / "outputs" / "KC-02.dxf"))
            kept = [e for e in reg.modelspace()
                    if e.dxftype() == "CIRCLE" and abs(e.dxf.center.x - 39100.0) < 1.0]
            self.assertEqual(len(kept), 1, "user-drawn entity must survive selective regeneration")


if __name__ == "__main__":
    unittest.main()
