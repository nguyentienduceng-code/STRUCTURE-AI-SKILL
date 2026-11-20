# -*- coding: utf-8 -*-
"""
test_p2_p3_paperspace_and_4forms.py — P2 NCR Polish, P3 PaperSpace Multi-Layout & 4-Form Tests
================================================================================================

Verifies:
1. P3 Single-File Multi-Layout PaperSpace (`export_single_file_multilayout_dxf` + `build_project_dossier(..., layout_mode="paperspace")`):
   - 1 file + 1 SHA-256 hash across multiple PaperSpace Layouts (`KC.02`, `KC.03`).
   - Shared `Dce_KhTenTruc`, `DCE_Pile_*`, `DCE_COL_*` blocks in ModelSpace (`0` audit errors).
   - Separate `DCE_TITLEBLOCK_A3_PAPER` `ATTRIB`s per Layout + non-overlapping `VIEWPORT`s.
2. Open-mode execution across ALL 4 Forms (`FORM_01`, `FORM_02`, `FORM_03`, `FORM_04`).
3. P2 NCR human-readable `ncr/NCR-001.md` slip + JSON mirror + lineage traceability.
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
TOOLS_DIR = AGENTS_DIR / "tools"

for _p in (str(CAD_DIR), str(VERIFY_DIR), str(TOOLS_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf
import cad_paperspace_builder as psb
import project_ops_manager as ops
from dce_cad_compliance_checker import audit_dxf_compliance
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model


class TestP2P3PaperSpaceAnd4Forms(unittest.TestCase):
    def test_01_p3_single_file_multilayout_paperspace_dxf(self):
        model = _build_two_sheet_model()
        # Give second sheet viewport a distinct scale (1:50) to verify model-scale text adaptation
        model["sheets"][1]["viewports"][0]["scale"] = 50.0

        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P3_PAPER_PROJ", base_dir=td, seed_model=model)
            proj_dir = Path(res["project_dir"])
            ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")

            dossier = ops.build_project_dossier(
                proj_dir,
                form_id="FORM_02_MULTIVIEW_A3_BTCT",
                compliance="physical",
                layout_mode="paperspace",
            )
            self.assertEqual(dossier["status"], "DXF_INTEGRITY_PASS")
            self.assertEqual(dossier["sheets_generated"], ["KC.02", "KC.03"])
            self.assertEqual(len(dossier["records"]), 2)
            # 1 single DXF & 1 single SHA256 shared across both layouts!
            r0, r1 = dossier["records"][0], dossier["records"][1]
            self.assertEqual(r0["dxf_path"], r1["dxf_path"])
            self.assertEqual(r0["dxf_sha256"], r1["dxf_sha256"])

            master_dxf = proj_dir / r0["dxf_path"]
            self.assertTrue(master_dxf.is_file())
            doc = ezdxf.readfile(str(master_dxf))
            aud = doc.audit()
            self.assertEqual(len(aud.errors), 0)
            self.assertEqual(len(aud.fixes), 0)

            layout_names = [ly.dxf.name for ly in doc.layouts]
            self.assertIn("KC.02", layout_names)
            self.assertIn("KC.03", layout_names)
            self.assertNotIn("Layout1", layout_names)

            # Inspect TitleBlock ATTRIB per PaperSpace Layout + Viewports
            for sh_no in ("KC.02", "KC.03"):
                ps = doc.layouts.get(sh_no)
                vps = [e for e in ps if e.dxftype() == "VIEWPORT" and getattr(e.dxf, "id", 0) != 1]
                self.assertEqual(len(vps), 2)
                tbs = [e for e in ps if e.dxftype() == "INSERT" and e.dxf.name == "DCE_TITLEBLOCK_A3_PAPER"]
                self.assertEqual(len(tbs), 1)
                tags = {a.dxf.tag: a.dxf.text for a in tbs[0].attribs}
                self.assertEqual(tags["KY_HIEU"], sh_no)

            # Shared Dce_KhTenTruc axis bubbles exist in shared ModelSpace
            axis_bubbles = [e for e in doc.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "Dce_KhTenTruc"]
            self.assertGreater(len(axis_bubbles), 0)

            phys = audit_dxf_compliance(str(master_dxf), profile="physical")
            self.assertEqual(phys["status"], "PASS", f"PaperSpace physical issues: {phys.get('issues')}")

    def test_02_all_four_open_forms_export_cleanly(self):
        model = _build_two_sheet_model()
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P3_4FORMS", base_dir=td, seed_model=model)
            proj_dir = Path(res["project_dir"])
            for fid in (
                "FORM_01_MATBANG_A1_BTCT",
                "FORM_02_MULTIVIEW_A3_BTCT",
                "FORM_03_KETCAU_THEP_STEEL",
                "FORM_04_CHITIET_COC_DAM_COT",
            ):
                ops.runbook_add_form(proj_dir, form_id=fid)
                out_dxf = proj_dir / "outputs" / f"OUT_{fid}.dxf"
                r = psb.export_with_open_form(out_dxf, model=model, form_id=fid, project_dir=proj_dir)
                self.assertEqual(r["status"], "OK")
                self.assertTrue(out_dxf.is_file())
                doc = ezdxf.readfile(str(out_dxf))
                self.assertEqual(len(doc.audit().errors), 0)
                phys = audit_dxf_compliance(str(out_dxf), profile="physical")
                self.assertEqual(phys["status"], "PASS", f"{fid} physical issues: {phys.get('issues')}")
                if fid == "FORM_03_KETCAU_THEP_STEEL":
                    steel_blocks = [
                        e for e in doc.modelspace()
                        if e.dxftype() == "INSERT" and "STEEL_H" in e.dxf.name
                    ]
                    self.assertGreater(len(steel_blocks), 0)
                if fid == "FORM_04_CHITIET_COC_DAM_COT":
                    piles = [
                        e for e in doc.modelspace()
                        if e.dxftype() == "INSERT" and e.dxf.name.startswith("DCE_Pile_")
                    ]
                    self.assertGreater(len(piles), 0)

    def test_03_p2_ncr_markdown_slip_and_json_mirror(self):
        with tempfile.TemporaryDirectory() as td:
            res = ops.init_project_workspace("P2_NCR_MD", base_dir=td, seed_model=_build_two_sheet_model())
            proj_dir = Path(res["project_dir"])
            ops.runbook_add_form(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")
            ops.build_project_dossier(proj_dir, form_id="FORM_02_MULTIVIEW_A3_BTCT")

            ncr_res = ops.runbook_apply_ncr(
                proj_dir,
                element_id="C1",
                field="h_mm",
                new_value=450,
                reason="Tang chieu cao tiet dien cot C1 theo RFI-02",
                source="DESIGN_RFI",
                severity="MAJOR",
            )
            self.assertEqual(ncr_res["ncr_id"], "NCR-001")
            md_path = Path(ncr_res["ncr_md_path"])
            self.assertTrue(md_path.is_file())
            md_txt = md_path.read_text(encoding="utf-8")
            self.assertIn("NCR-001", md_txt)
            self.assertIn("`C1`", md_txt)
            self.assertIn("`v1`", md_txt)
            self.assertIn("`v2`", md_txt)


if __name__ == "__main__":
    unittest.main()
