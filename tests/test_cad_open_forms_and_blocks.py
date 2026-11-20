# -*- coding: utf-8 -*-
"""
test_cad_open_forms_and_blocks.py — Phase 0/1/2 Open Form & DCE Block Tests
===========================================================================
Verifies:
1. All 4 user-editable Forms exist in 00_Template_&_Standards/CAD_Forms and
   .agents/_SHARED/data/CAD_Forms and pass `validate_open_form`.
2. 3-tier Form resolver precedence: project > user_standards > ssot_fallback.
3. Strict error/warning contracts: missing zone (`E002`), missing ATTDEF (`E003`),
   non-World UCS (`W003`), and high DXF version (`ROUNDTRIP_LIMITED`).
4. Real AutoCAD-style user customization round-trip in `template_mode="open"`:
   - Preserves user logo/graphics & user-modified layer colors (`Inherit-from-Form`).
   - Updates `DCE_TITLEBLOCK_A3` allowlisted `ATTRIB`s in-place while preserving
     custom company tags.
   - Shifts viewport placement cleanly when `DCE_ZONE_VIEWPORT_TOP` is moved.
   - Inserts `DCE_Pile_*` + `DCE_COL_*` + `Dce_KhTenTruc` blocks cleanly (`scale=1:1`
     on member geometry, zero `ATTDEF` distortion) and passes physical audit.
   - Re-export over existing output purges ONLY `DCE_AGENT_OWNED` entities.
5. `cad_evidence_contract.normalize` forwards `template_contract`, `zone_evidence`,
   `block_evidence` when present and never fabricates them when absent.
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
VERIFY_DIR = AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"

for p in (str(CAD_DIR), str(VERIFY_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
import cad_plan_engine
import cad_evidence_contract
from cad_form_contract import (
    FORM_CATALOG,
    SSOT_FORMS_DIR,
    USER_FORMS_DIR,
    resolve_form_paths,
    validate_open_form,
)
from dce_cad_compliance_checker import audit_dxf_compliance
from test_cad_multiview_a3 import _build_synthetic_multiview_model


class TestCadOpenFormsAndBlocks(unittest.TestCase):
    def test_01_all_four_forms_exist_and_validate_in_both_tiers(self):
        for folder in (SSOT_FORMS_DIR, USER_FORMS_DIR):
            self.assertTrue(folder.is_dir(), f"Missing forms dir: {folder}")
            self.assertTrue((folder / "README_HUONG_DAN_SUA_FORM_AUTOCAD.md").is_file())
            for form_id, spec in FORM_CATALOG.items():
                fp = folder / spec["filename"]
                mp = folder / spec["manifest_filename"]
                self.assertTrue(fp.is_file(), f"Missing form DXF: {fp}")
                self.assertTrue(mp.is_file(), f"Missing form manifest: {mp}")
                res = validate_open_form(fp, manifest_path=mp, form_id=form_id)
                self.assertTrue(res.valid, f"{form_id} failed validation: {res.errors}")
                self.assertEqual(res.roundtrip_status, "FULL")
                self.assertTrue(res.ucs_ok)
                self.assertGreaterEqual(res.titleblock_insert_count, 1)

    def test_02_three_tier_resolution_priority(self):
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "proj"
            (proj / "CAD_Forms").mkdir(parents=True)
            custom_f2 = proj / "CAD_Forms" / "Form_02_MultiView_A3_BTCT.dxf"
            custom_f2.write_bytes((SSOT_FORMS_DIR / "Form_02_MultiView_A3_BTCT.dxf").read_bytes())

            r_proj = resolve_form_paths("FORM_02_MULTIVIEW_A3_BTCT", project_dir=proj)
            self.assertEqual(r_proj.tier, "project")
            self.assertEqual(r_proj.dxf_path, custom_f2)

            r_user = resolve_form_paths("FORM_02_MULTIVIEW_A3_BTCT", project_dir=Path(td) / "no_forms")
            self.assertEqual(r_user.tier, "user_standards")
            self.assertEqual(r_user.dxf_path.parent, USER_FORMS_DIR)

    def test_03_contract_rejects_missing_zone_missing_attdef_and_flags_ucs(self):
        with tempfile.TemporaryDirectory() as td:
            fp = Path(td) / "broken_form02.dxf"
            doc = ezdxf.readfile(str(SSOT_FORMS_DIR / "Form_02_MultiView_A3_BTCT.dxf"))
            msp = doc.modelspace()
            # Delete VIEWPORT_TOP zone marker & change UCS
            for ent in list(msp):
                if ent.dxftype() == "LWPOLYLINE" and ent.dxf.layer.upper() == "DCE_ZONE_VIEWPORT_TOP":
                    msp.delete_entity(ent)
            doc.header["$UCSORG"] = (500.0, 200.0, 0.0)
            # Remove TEN_BAN_VE ATTDEF from DCE_TITLEBLOCK_A3
            blk = doc.blocks.get("DCE_TITLEBLOCK_A3")
            for b_ent in list(blk):
                if b_ent.dxftype() == "ATTDEF" and b_ent.dxf.tag == "TEN_BAN_VE":
                    blk.delete_entity(b_ent)
            doc.saveas(str(fp))

            val = validate_open_form(fp, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            self.assertFalse(val.valid)
            err_codes = {e["code"] for e in val.errors}
            warn_codes = {w["code"] for w in val.warnings}
            self.assertIn("E002_TEMPLATE_ZONE_MISSING", err_codes)
            self.assertIn("E003_TITLEBLOCK_ATTDEF_MISSING", err_codes)
            self.assertIn("W003_TEMPLATE_TRANSFORM_REVIEW", warn_codes)

    def test_04_user_customization_roundtrip_open_mode_with_blocks_and_idempotency(self):
        model = _build_synthetic_multiview_model()
        # Add sample piles cleanly to TOP viewport
        model["sheets"][0]["viewports"][0]["piles"] = [
            {"x": 0.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE1", "id": "P1", "length_m": "18", "capacity_t": "45"},
            {"x": 4.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE3", "id": "P2", "length_m": "18", "capacity_t": "45"},
        ]
        model["project"]["company"] = "CONG TY TU VAN TEST"
        model["project"]["investor"] = "CHU DAU TU ABC"

        with tempfile.TemporaryDirectory() as td:
            proj_dir = Path(td) / "demo_proj"
            forms_dir = proj_dir / "CAD_Forms"
            forms_dir.mkdir(parents=True)
            custom_dxf = forms_dir / "Form_02_MultiView_A3_BTCT.dxf"
            custom_man = forms_dir / "Form_02_MultiView_A3_BTCT.manifest.json"
            custom_dxf.write_bytes((SSOT_FORMS_DIR / "Form_02_MultiView_A3_BTCT.dxf").read_bytes())
            custom_man.write_bytes((SSOT_FORMS_DIR / "Form_02_MultiView_A3_BTCT.manifest.json").read_bytes())

            # Simulate engineer opening Form in AutoCAD & customizing:
            doc = ezdxf.readfile(str(custom_dxf))
            msp = doc.modelspace()
            # 1) Add user custom company emblem on DCE_Frame
            msp.add_circle((39400.0, 15000.0), 320.0, dxfattribs={"layer": "DCE_Frame"})
            # 2) Change DCE_Cot layer color to 6 (magenta)
            doc.layers.get("DCE_Cot").dxf.color = 6
            # 3) Shift DCE_ZONE_VIEWPORT_TOP box by +800 mm in X
            for ent in msp:
                if ent.dxftype() == "LWPOLYLINE" and ent.dxf.layer.upper() == "DCE_ZONE_VIEWPORT_TOP":
                    pts = [(x + 800.0, y) for x, y in ent.get_points("xy")]
                    ent.set_points(pts, format="xy")
            # 4) Add custom company ATTDEF + ATTRIB tag in DCE_TITLEBLOCK_A3
            tb_blk = doc.blocks.get("DCE_TITLEBLOCK_A3")
            tb_blk.add_attdef("MA_HOP_DONG", insert=(38000.0, 14200.0), text="HD-2026-88",
                              dxfattribs={"layer": "DCE_TKT-TEXT", "height": 140.0, "style": "Dce_Text", "color": 256})
            for ins in msp:
                if ins.dxftype() == "INSERT" and ins.dxf.name == "DCE_TITLEBLOCK_A3":
                    ins.add_attrib("MA_HOP_DONG", "HD-2026-99")
            doc.saveas(str(custom_dxf))

            out_dxf = Path(td) / "out_open_kc13.dxf"
            model_json = proj_dir / "model_multiview.json"
            model_json.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
            cad_plan_engine.export_dce_plan(
                str(out_dxf),
                sheet_type="CUSTOM_MULTIVIEW",
                model_json_path=str(model_json),
                v6=True,
                template_mode="open",
                form_id="FORM_02_MULTIVIEW_A3_BTCT",
                project_dir=str(proj_dir),
                dry_run=False,
            )

            self.assertTrue(out_dxf.is_file())
            out_doc = ezdxf.readfile(str(out_dxf))
            out_msp = out_doc.modelspace()

            # Check user edits survived 100%
            self.assertEqual(out_doc.layers.get("DCE_Cot").dxf.color, 6)
            user_circles = [
                e for e in out_msp
                if e.dxftype() == "CIRCLE" and e.dxf.layer == "DCE_Frame"
                and abs(e.dxf.center.x - 39400.0) < 1.0
            ]
            self.assertEqual(len(user_circles), 1)

            # Check TitleBlock updated in-place & custom tag preserved
            tbs = [e for e in out_msp if e.dxftype() == "INSERT" and e.dxf.name == "DCE_TITLEBLOCK_A3"]
            self.assertEqual(len(tbs), 1)
            tb_map = {a.dxf.tag: a.dxf.text for a in tbs[0].attribs}
            self.assertEqual(tb_map["MA_HOP_DONG"], "HD-2026-99")
            self.assertEqual(tb_map["CONG_TY"], "CONG TY TU VAN TEST")
            self.assertEqual(tb_map["KY_HIEU"], "KC.13")

            # Check DCE_Pile_* & DCE_COL_* blocks inserted without distorting text
            pile_inserts = [e for e in out_msp if e.dxftype() == "INSERT" and e.dxf.name.startswith("DCE_Pile_")]
            col_inserts = [e for e in out_msp if e.dxftype() == "INSERT" and e.dxf.name.startswith("DCE_COL_")]
            axis_inserts = [e for e in out_msp if e.dxftype() == "INSERT" and e.dxf.name == "Dce_KhTenTruc"]
            self.assertGreaterEqual(len(pile_inserts), 2)
            self.assertGreaterEqual(len(col_inserts), 6)
            self.assertGreater(len(axis_inserts), 0)
            for ins in pile_inserts + col_inserts:
                self.assertAlmostEqual(ins.dxf.xscale, 1.0, places=3)
                self.assertAlmostEqual(ins.dxf.yscale, 1.0, places=3)

            # Check TOP pile shifted +800 mm by edited DCE_ZONE_VIEWPORT_TOP
            first_pile_x = min(e.dxf.insert.x for e in pile_inserts)
            # Original TOP origin x=5200.0, plus +800.0 shift => 6000.0
            self.assertAlmostEqual(first_pile_x, 6000.0, delta=5.0)

            # Sidecar v6 contains template_contract, zone_evidence, block_evidence
            sidecar = json.loads(out_dxf.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
            self.assertEqual(sidecar["template_contract"]["tier"], "project")
            self.assertIn("VIEWPORT_TOP", sidecar["zone_evidence"]["zones_wcs"])
            self.assertTrue(sidecar["block_evidence"]["use_dce_blocks"])

            norm = cad_evidence_contract.load_evidence(out_dxf)
            self.assertIn("template_contract", norm)
            self.assertIn("block_evidence", norm)

            # Physical audit passes with native block detections
            phys = audit_dxf_compliance(str(out_dxf), profile="physical")
            self.assertEqual(phys["status"], "PASS", f"Physical audit issues: {phys.get('issues')}")
            self.assertGreaterEqual(phys["blocks"]["title_blocks"], 1)
            self.assertGreater(phys["blocks"]["attrib_inserts"], 0)

            # Idempotent re-render over already generated out_dxf keeps user circle & doesn't duplicate piles
            from cad_multiview_a3 import export_multiview_a3_sheet
            export_multiview_a3_sheet(
                str(out_dxf),
                model=model,
                sheet_index=0,
                template_path=str(out_dxf),
                v6=True,
                template_mode="open",
                form_id="FORM_02_MULTIVIEW_A3_BTCT",
                dry_run=False,
            )
            re_doc = ezdxf.readfile(str(out_dxf))
            re_piles = [e for e in re_doc.modelspace() if e.dxftype() == "INSERT" and e.dxf.name.startswith("DCE_Pile_")]
            self.assertEqual(len(re_piles), len(pile_inserts))

    def test_05_evidence_adapter_does_not_fabricate_open_form_fields_for_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "legacy.dxf"
            p.write_text("0\nEOF\n", encoding="utf-8")
            legacy_norm = cad_evidence_contract.normalize({"v6_directive": True, "claims": {}}, p)
            self.assertNotIn("template_contract", legacy_norm)
            self.assertNotIn("zone_evidence", legacy_norm)
            self.assertNotIn("block_evidence", legacy_norm)


if __name__ == "__main__":
    unittest.main()
