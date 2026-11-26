# -*- coding: utf-8 -*-
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY = ROOT / "skills" / "SKILL_VERIFY" / "scripts"
for p in (str(CAD), str(VERIFY)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ezdxf
from cad_element_registry import validate_dxf_entity_map_linkage
from cad_sheet_set import (
    _format_size,
    build_registry_from_fixture,
    export_sheet_set,
    manifest_from_fixture,
    validate_manifest,
)
from dce_cad_compliance_checker import audit_dxf_compliance

FIXTURE = CAD / "fixtures" / "g2_steel_and_sheet_fixture.json"


class TestC2SheetSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text(encoding="utf8"))

    def test_manifest_semantics_all_gates(self):
        m = manifest_from_fixture(self.data)
        r = build_registry_from_fixture(self.data)
        self.assertEqual(len(r.elements), 12)
        for eid in ("STEEL_PL_01", "STEEL_BP_01", "STEEL_BP_02", "COL_C1_F1", "BM_D1A_F2_S1"):
            self.assertIn(eid, r.elements)
        a = validate_manifest(r, m, self.data["rebar_strips"])
        self.assertTrue(a["is_valid"], a["violations"])
        self.assertTrue(all(a["checks"].values()))

    def test_dual_viewport_faces_are_disjoint(self):
        kc04 = next(s for s in self.data["sheet_set_preview_manifest"]["sheets"] if s["sheet_no"] == "KC-04")
        faces = {v["content_face"] for v in kc04["viewports"]}
        self.assertEqual(faces, {"TOP", "BOTTOM"})
        strips = {s["strip_id"]: s["face"] for s in self.data["rebar_strips"]}
        for v in kc04["viewports"]:
            self.assertTrue(all(strips[sid] == v["content_face"] for sid in v["strip_ids"]))

    def test_format_size_never_outputs_raw_dict(self):
        s_conc = _format_size({"width_mm": 300, "height_mm": 300, "concrete_grade": "B30"})
        s_bp = _format_size({"plate_width_mm": 400.0, "plate_height_mm": 400.0, "thickness_mm": 20.0})
        s_pl = _format_size({"width_mm": 240.0, "height_mm": 180.0, "plate_thickness": 14.0})
        self.assertEqual(s_conc, "300x300 mm")
        self.assertEqual(s_bp, "PL400x400x20")
        self.assertEqual(s_pl, "PL240x180x14")
        self.assertNotIn("{", _format_size('{"a": 1}'))

    def test_export_five_sheets_linkage_compliance_and_previews(self):
        reg = build_registry_from_fixture(self.data)
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            result = export_sheet_set(td_path, str(FIXTURE), strict=True, render_previews=True, export_pdf=True)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(len(result["sheets"]), 5)
            audit = json.loads((td_path / "C2_sheet_set_audit.json").read_text(encoding="utf8"))
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(next(s for s in audit["sheets"] if s["sheet_no"] == "KC-04")["faces"], ["BOTTOM", "TOP"])

            # Previews exist and are non-empty
            pdf_p = td_path / "c2_sheet_set_preview.pdf"
            self.assertTrue(pdf_p.is_file() and pdf_p.stat().st_size > 1000)
            for s in result["sheets"]:
                self.assertTrue((td_path / f"{s['sheet_no']}_preview.png").is_file())

            geom_sigs = set()
            for dxf_p in sorted(td_path.glob("*_C2_A3.dxf")):
                doc = ezdxf.readfile(str(dxf_p))
                self.assertEqual(doc.dxfversion, "AC1021")
                msp = doc.modelspace()
                ps = doc.layouts.get("Layout1")
                self.assertIsNotNone(ps)

                # Right-side A3 strip & sheet index present in Paperspace
                ps_texts = [e.dxf.text for e in ps if e.dxftype() == "TEXT"]
                self.assertTrue(any("MUC LUC BAN VE" in t for t in ps_texts))
                self.assertTrue(any("SO HIEU:" in t for t in ps_texts))

                # Zero raw dict literal in any INSERT attribute
                for ins in msp.query("INSERT"):
                    for att in ins.attribs:
                        self.assertFalse(att.dxf.text.startswith("{"), f"Raw dict in ATTRIB: {att.dxf.text}")

                # Sidecar entity_map & strict 3-way linkage
                meta = json.loads(dxf_p.with_suffix(".dce_audit.json").read_text(encoding="utf8"))
                self.assertEqual(meta["provenance"]["dxf_sha256"], hashlib.sha256(dxf_p.read_bytes()).hexdigest())
                for eid in ("COL_C1_F1", "BM_D1A_F2_S1", "STEEL_COL_C1", "STEEL_BP_01", "STEEL_BP_02", "STEEL_PL_01"):
                    self.assertIn(eid, meta["entity_map"])
                    self.assertTrue(meta["entity_map"][eid].get("tag_handle"))
                    self.assertTrue(meta["entity_map"][eid].get("schedule_handles"))

                link = validate_dxf_entity_map_linkage(dxf_p, registry=reg, fixture_data=self.data)
                self.assertTrue(link["strict_3way_physical_linkage_ok"], link["issues"])
                self.assertTrue(link["viewport_inspection"]["viewport_nonoverlap_ok"])
                if dxf_p.name.startswith("KC-04"):
                    self.assertTrue(link["viewport_inspection"]["disjoint_visible_rebar_ok"])

                comp_phys = audit_dxf_compliance(str(dxf_p), profile="physical")
                self.assertEqual(comp_phys["status"], "PASS", comp_phys["issues"])
                comp_plan = audit_dxf_compliance(str(dxf_p), profile="plan")
                self.assertEqual(comp_plan["status"], "PASS", comp_plan["issues"])

                sig = []
                for e in msp:
                    if e.dxftype() == "TEXT":
                        continue
                    attrs = {k: str(v) for k, v in e.dxf.all_existing_dxf_attribs().items() if k not in ("handle", "owner")}
                    if e.dxftype() == "LWPOLYLINE":
                        attrs["vertices"] = str(list(e.get_points()))
                    sig.append([e.dxftype(), attrs])
                geom_sigs.add(hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest())

            # All 5 sheets have distinct geometry signatures
            self.assertEqual(len(geom_sigs), 5)

    def test_missing_detail_input_handling_never_passes(self):
        broken = json.loads(json.dumps(self.data))
        broken["steel_plates"] = []
        broken["concrete_elements"] = [c for c in broken["concrete_elements"] if c["category"] != "BEAM"]
        with tempfile.TemporaryDirectory() as td:
            bad_fix = Path(td) / "missing_detail_fixture.json"
            bad_fix.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf8")
            with self.assertRaises(ValueError):
                export_sheet_set(Path(td) / "strict_out", bad_fix, strict=True, render_previews=False)
            res = export_sheet_set(Path(td) / "non_strict_out", bad_fix, strict=False, render_previews=False)
            self.assertEqual(res["status"], "MISSING_INPUT")
            self.assertNotEqual(res["status"], "PASS")
            self.assertIn("KC-06", res["missing_inputs"])


    def test_06_preview_pdf_is_true_a3_landscape_without_tick_axes(self) -> None:
        """Preview PDF generated by C2 must be A3 Landscape (420x297 mm)."""
        import sys
        import tempfile
        import pymupdf

        cad_dir = Path(__file__).resolve().parents[1] / "skills" / "Technical_Illustrator" / "cad_integration"
        if str(cad_dir) not in sys.path:
            sys.path.insert(0, str(cad_dir))
        import cad_sheet_set
        fixture_path = cad_dir / "fixtures" / "g2_steel_and_sheet_fixture.json"

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "c2_preview_a3"
            res = cad_sheet_set.export_sheet_set(
                out_dir, fixture_path, strict=True, render_previews=True, export_pdf=True
            )
            pdf_path = Path(res["previews"]["pdf_path"])
            self.assertTrue(pdf_path.is_file())
            with pymupdf.open(str(pdf_path)) as doc:
                self.assertEqual(len(doc), len(res["previews"]["png_paths"]))
                self.assertGreaterEqual(len(doc), 5)
                for page in doc:
                    w_mm = page.rect.width * 25.4 / 72.0
                    h_mm = page.rect.height * 25.4 / 72.0
                    self.assertAlmostEqual(w_mm, 420.0, delta=1.0)
                    self.assertAlmostEqual(h_mm, 297.0, delta=1.0)

    def test_07_export_project_a3_sheets_uses_real_engine_and_template(self) -> None:
        """Real-building A3 bridge must use DcePlanEngine + Master Template + Registry."""
        import sys
        import tempfile
        import pymupdf

        cad_dir = Path(__file__).resolve().parents[1] / "skills" / "Technical_Illustrator" / "cad_integration"
        if str(cad_dir) not in sys.path:
            sys.path.insert(0, str(cad_dir))
        import cad_sheet_set

        with tempfile.TemporaryDirectory() as tmp:
            # 1) Mac dinh CAD-first: KHONG tu dong xuat PDF hay PNG
            out_cad = Path(tmp) / "project_cad_only"
            res_cad = cad_sheet_set.export_project_a3_sheets(out_cad)
            self.assertEqual(res_cad["status"], "PASS")
            self.assertEqual(res_cad["pdf_path"], "")
            self.assertEqual(res_cad["preview_pngs"], [])
            self.assertEqual(list(out_cad.glob("*.pdf")), [])
            self.assertEqual(list(out_cad.glob("*.png")), [])
            for s in res_cad["sheets"]:
                self.assertTrue(Path(s["dxf_path"]).is_file())
                self.assertGreaterEqual(s["template_blocks"], 98)

            # 2) Chi xuat PNG + PDF A3 Landscape (420x297 mm) khi ghi ro yeu cau
            out_dir = Path(tmp) / "project_a3"
            res = cad_sheet_set.export_project_a3_sheets(
                out_dir, render_previews=True, export_pdf=True, dpi=150
            )
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["paper_size"], "A3_LANDSCAPE")
            self.assertIn("Standard_Method", res)
            self.assertTrue(res["Calculation_Logs"])
            self.assertGreater(res["registry_total_elements"], 0)
            self.assertEqual(len(res["sheets"]), 2)
            for s in res["sheets"]:
                self.assertTrue(Path(s["dxf_path"]).is_file())
                self.assertGreaterEqual(s["template_blocks"], 98)
                self.assertTrue(Path(s["preview_png"]).is_file())
                self.assertGreater(Path(s["preview_png"]).stat().st_size, 10000)

            pdf_path = Path(res["pdf_path"])
            self.assertTrue(pdf_path.is_file())
            with pymupdf.open(str(pdf_path)) as doc:
                self.assertEqual(len(doc), 2)
                for page in doc:
                    self.assertAlmostEqual(page.rect.width * 25.4 / 72.0, 420.0, delta=1.0)
                    self.assertAlmostEqual(page.rect.height * 25.4 / 72.0, 297.0, delta=1.0)

    def test_08_v2_01_schedule_rows_print_on_paper_not_clipped(self) -> None:
        """V2-01: the real BOM table (12 structural elements) must physically sit on the A3 paperspace sheet.

        - Each of the 12 fixture elements must carry ps_schedule_handles (paper-space TEXT
          handles) in the sidecar entity_map, each resolving to a real paperspace DCE_Schedule
          TEXT entity inside the A3 inner frame (no clip).
        - Rebar strips (no schedule_refs) must NOT get paper BOM rows.
        - The schedule band must not overlap any paperspace viewport (rows stay on-paper)."""
        import ezdxf
        BOM = ["COL_C1_F1", "COL_C1_F2", "BM_D1A_F2_S1", "BM_D1A_F2_S2",
               "STEEL_COL_C1", "STEEL_BP_01", "STEEL_BP_02", "STEEL_PL_01",
               "STEEL_BM_B1", "STEEL_BOX_BX1", "STEEL_CH_U1", "STEEL_PP_P1"]
        with tempfile.TemporaryDirectory() as td:
            res = export_sheet_set(Path(td), str(FIXTURE), strict=True, render_previews=False)
            self.assertEqual(res["status"], "PASS")
            for s in res["sheets"]:
                dxf_p = Path(td) / f"{s['sheet_no']}_C2_A3.dxf"
                doc = ezdxf.readfile(str(dxf_p))
                ps = doc.layouts.get("Layout1")
                audit = json.loads(dxf_p.with_suffix(".dce_audit.json").read_text(encoding="utf8"))
                emap = audit["entity_map"]

                # Every one of the 12 structural BOM elements must carry 3 paper TEXT rows
                for eid in BOM:
                    self.assertIn(eid, emap, f"{s['sheet_no']}/{eid} missing from entity_map")
                    handles = emap[eid].get("ps_schedule_handles", [])
                    self.assertEqual(len(handles), 3, f"{s['sheet_no']}/{eid}: expected 3 ps TEXT rows")
                    for h in handles:
                        found = next((e for e in ps if str(e.dxf.handle) == h), None)
                        self.assertIsNotNone(found, f"{s['sheet_no']}/{eid}: ps handle {h} not in paperspace")
                        self.assertEqual(found.dxf.layer, "DCE_Schedule")
                        self.assertTrue(10.0 <= found.dxf.insert.x <= 415.0, f"{eid} ps row off-sheet x={found.dxf.insert.x}")
                        self.assertTrue(5.0 <= found.dxf.insert.y <= 292.0, f"{eid} ps row off-sheet y={found.dxf.insert.y}")

                # Non-BOM entries (KC-04 rebar strips) must NOT print paper BOM rows
                for eid in [k for k in emap if k not in BOM]:
                    self.assertEqual(emap[eid].get("ps_schedule_handles", []), [],
                                     f"{s['sheet_no']}/{eid}: non-BOM entry must not print BOM rows")

                # Paper BOM band must not overlap any viewport (rows visible, not clipped)
                for vp in ps.query("VIEWPORT"):
                    if getattr(vp.dxf, "id", 1) == 1:
                        continue
                    vx0, vx1 = vp.dxf.center.x - vp.dxf.width / 2.0, vp.dxf.center.x + vp.dxf.width / 2.0
                    vy0, vy1 = vp.dxf.center.y - vp.dxf.height / 2.0, vp.dxf.center.y + vp.dxf.height / 2.0
                    for eid in BOM:
                        for h in emap[eid].get("ps_schedule_handles", []):
                            ent = next(e for e in ps if str(e.dxf.handle) == h)
                            self.assertFalse(vx0 <= ent.dxf.insert.x <= vx1 and vy0 <= ent.dxf.insert.y <= vy1,
                                             f"{s['sheet_no']}/{eid}: paper BOM row inside viewport")


    def test_09_v2_03_details_driven_by_input_not_hardcoded(self) -> None:
        """V2-03: changing the design input MUST change the detail geometry/labels.

        (a) KC-06 beam: mutate section/rebar/stirrup/grade in detail_design -> label + box update.
        (b) KC-04 rebar: mutate bar_spec in rebar_strips -> bar label updates.
        (c) Removing detail_design / rebar region -> MISSING_INPUT (never a PASS)."""
        import ezdxf
        import copy

        # (a) KC-06 beam driven by input
        base = copy.deepcopy(self.data)
        mutated = copy.deepcopy(self.data)
        mutated["detail_design"]["KC-06"]["beam"].update({
            "width_mm": 250, "height_mm": 500, "main_rebar": "4D24",
            "stirrup": "D10a200", "concrete_grade": "B30",
            "section_name": "250x500",
        })
        with tempfile.TemporaryDirectory() as td1:
            export_sheet_set(Path(td1), str(FIXTURE), strict=False, render_previews=False)
            txt_before = [e.dxf.text for e in ezdxf.readfile(str(Path(td1) / "KC-06_C2_A3.dxf")).modelspace() if e.dxftype() == "TEXT" and e.dxf.layer == "DCE_Name"]
        with tempfile.TemporaryDirectory() as td2:
            mut_fix = Path(td2) / "mut.json"
            mut_fix.write_text(json.dumps(mutated, ensure_ascii=False), encoding="utf8")
            export_sheet_set(Path(td2) / "out", mut_fix, strict=False, render_previews=False)
            txt_after = [e.dxf.text for e in ezdxf.readfile(str(Path(td2) / "out" / "KC-06_C2_A3.dxf")).modelspace() if e.dxftype() == "TEXT" and e.dxf.layer == "DCE_Name"]
        # the before label used the default 200x400/2D20+3D20; after must reflect the mutated input
        self.assertIn("250x500", " ".join(txt_after))
        self.assertIn("4D24+D10a200", " ".join(txt_after))
        self.assertNotIn("200x400", " ".join(txt_after))

        # (b) KC-04 rebar driven by input
        mut2 = copy.deepcopy(self.data)
        for r in mut2["rebar_strips"]:
            r["bar_spec"] = "d14a200"
        with tempfile.TemporaryDirectory() as td3:
            f3 = Path(td3) / "m2.json"; f3.write_text(json.dumps(mut2, ensure_ascii=False), encoding="utf8")
            export_sheet_set(Path(td3) / "out", f3, strict=False, render_previews=False)
            bars = [e.dxf.text for e in ezdxf.readfile(str(Path(td3) / "out" / "KC-04_C2_A3.dxf")).modelspace() if e.dxftype() == "TEXT" and str(e.dxf.layer).startswith("REBAR_")]
            self.assertTrue(any("d14a200" in b for b in bars), f"rebar label not driven by input: {bars}")

        # (c) missing design input -> MISSING_INPUT
        mut3 = copy.deepcopy(self.data)
        mut3["rebar_strips"] = [{k: v for k, v in r.items() if k != "region"} for r in mut3["rebar_strips"]]
        mut3.pop("detail_design", None)
        with tempfile.TemporaryDirectory() as td4:
            f4 = Path(td4) / "m3.json"; f4.write_text(json.dumps(mut3, ensure_ascii=False), encoding="utf8")
            res = export_sheet_set(Path(td4) / "out", f4, strict=False, render_previews=False)
            self.assertEqual(res["status"], "MISSING_INPUT")
            self.assertIn("KC-04", res["missing_inputs"])
            self.assertIn("KC-06", res["missing_inputs"])
            self.assertIn("KC-07", res["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
