# -*- coding: utf-8 -*-
"""
test_p4_rfi_ncr_generator.py — P4.2 Round-Trip RFI/NCR Generator
================================================================

Covers TÁC VỤ P4.2 of `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md` (§3.2):
  - rfi_ncr_bridge: Filter-8 20-cổng -> legal findings + schema-valid NCR/RFI records
  - cad_defect_cropper: 300 DPI BBox crop (visual evidence) via dce_render_preview
  - rfi_ncr_docx_generator: Rule 12b (Zero White Text) & Rule 12e (font floor / Math Lock)
  - Acceptance: the generator source is `audit_zero_white_text.py`-clean, and the
    emitted .docx is reopened to prove no sub-10pt run and no white (255,255,255) text.
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
TOOLS_DIR = AGENTS_DIR / "tools"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"

for _p in (str(TOOLS_DIR), str(CAD_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import audit_zero_white_text as a12  # noqa: E402
import cad_plan_engine  # noqa: E402
import rfi_ncr_bridge as bridge  # noqa: E402
import rfi_ncr_docx_generator as gen  # noqa: E402
import project_ops_manager as ops  # noqa: E402
from cad_defect_cropper import crop_defect_region  # noqa: E402
from test_p0_ops_workspace_and_lineage import _build_two_sheet_model  # noqa: E402

from docx import Document  # noqa: E402


def _synthetic_audit() -> dict:
    """A minimal Filter-8-shaped audit result: 2 CRITICAL NCR gates, 2 MINOR RFI gates."""
    gates = [
        {"gate_id": "G8.09", "gate_name": "SHEAR_WALL_AND_CORE_DETAIL", "severity": "MAJOR",
         "passed": False, "applicable": True, "detail": "Thiếu DCE_CouplingBeam / vùng biên B.E."},
        {"gate_id": "G8.14", "gate_name": "COLUMN_SECTION_REBAR_RULES", "severity": "CRITICAL",
         "passed": False, "applicable": True, "detail": "Cột C1: As_prov < As_calc, mu ngoài dải."},
        {"gate_id": "G8.19", "gate_name": "SCHEDULE_TABLE_CELL_CONTAINMENT", "severity": "MAJOR",
         "passed": False, "applicable": True, "detail": "2 ô bảng thống kê tràn chữ."},
        {"gate_id": "G8.20", "gate_name": "BEAM_LABEL_ORIENTATION_AND_LW", "severity": "MAJOR",
         "passed": False, "applicable": True, "detail": "Nhãn dầm dọc chưa xoay 90°."},
    ]
    return {"status": "FAIL", "full_compliance_verified": False,
            "gates_failed": 4, "gates_unverified": 0, "gate_results": gates}


class TestP4Bridge(unittest.TestCase):
    def test_classify_routing_nvsrfi(self):
        res = bridge.generate_from_audit  # not used (no dxf); we feed the audit directly
        findings = bridge.classify_findings(_synthetic_audit())
        by_gate = {f["gate_id"]: f for f in findings}
        # NCR-routed (structural)
        self.assertEqual(by_gate["G8.14"]["doc_type"], "NCR")
        self.assertEqual(by_gate["G8.14"]["severity"], "CRITICAL")
        self.assertEqual(by_gate["G8.09"]["doc_type"], "RFI")
        # RFI-routed (cosmetic)
        self.assertEqual(by_gate["G8.19"]["doc_type"], "RFI")
        self.assertEqual(by_gate["G8.20"]["doc_type"], "RFI")
        self.assertEqual(len(findings), 4)

    def test_ncr_records_are_schema_valid(self):
        findings = bridge.classify_findings(_synthetic_audit())
        ncrs = bridge.build_ncr_records(findings, model_id="P4_RFI", from_version=1, to_version=2)
        # In this synthetic set only G8.14 is NCR-routed (G8.09/19/20 are RFI) => exactly 1 NCR.
        self.assertEqual(len(ncrs), 1)
        for rec in ncrs:
            ops.validate_ncr_dict(rec)  # raises on schema breach
            self.assertIn(rec["severity"], ("CRITICAL", "MAJOR"))
            self.assertEqual(rec["status"], "REJECTED")
            self.assertEqual(rec["source"], bridge.SOURCE_TAG)

    def test_rfi_records(self):
        findings = bridge.classify_findings(_synthetic_audit())
        rfis = bridge.build_rfi_records(findings, model_id="P4_RFI")
        self.assertEqual(len(rfis), 3)  # G8.09, G8.19, G8.20
        for rec in rfis:
            self.assertTrue(rec["rfi_id"].startswith("RFI-DES-"))
            self.assertIn(rec["severity"], ("MAJOR", "MINOR"))

    def test_pass_audit_has_no_findings(self):
        clean = {"gate_results": [
            {"gate_id": f"G8.{i:02d}", "passed": True, "applicable": True} for i in range(1, 21)
        ]}
        self.assertEqual(bridge.classify_findings(clean), [])


class TestP4Crop(unittest.TestCase):
    def test_crop_defect_region_300dpi(self):
        with tempfile.TemporaryDirectory() as td:
            out_dxf = Path(td) / "kc02.dxf"
            cad_plan_engine.export_dce_plan(str(out_dxf), sheet_type="KC-02", v6=True, full_evidence=True)
            self.assertTrue(out_dxf.is_file())
            out_png = Path(td) / "defect.png"
            r = crop_defect_region(str(out_dxf), str(out_png), view_box=(14000.0, 15000.0, 20000.0, 19000.0), dpi=300)
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["dpi"], 300)
            self.assertTrue(r["verified_file_exists"])
            self.assertTrue(out_png.is_file() and out_png.stat().st_size > 0)
            # PNG magic bytes
            with open(out_png, "rb") as f:
                self.assertEqual(f.read(4), b"\x89PNG")

    def test_crop_no_region_never_guesses(self):
        # Empty dxf -> no modelspace extents -> E004_REGION (no guessing), unless frame given.
        import ezdxf
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "empty.dxf"
            ezdxf.new("R2007").saveas(str(empty))
            r = crop_defect_region(str(empty), str(Path(td) / "x.png"))
            self.assertEqual(r["status"], "E004_REGION")
            self.assertFalse(r["ok"])


class TestP4Docx(unittest.TestCase):
    def _records(self):
        findings = bridge.classify_findings(_synthetic_audit())
        ncrs = bridge.build_ncr_records(findings, "P4_RFI", 1, 2)
        rfis = bridge.build_rfi_records(findings, "P4_RFI")
        return ncrs, rfis

    def test_ncr_docx_emits_and_reopens_clean(self):
        ncrs, rfis = self._records()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "NCR_P4.docx"
            p = gen.build_ncr_docx(ncrs, str(out),
                                   meta={"project": "P4_DEMO", "from_version": 1, "to_version": 2,
                                         "audit_status": "FAIL"})
            self.assertTrue(p.is_file())
            d = Document(str(p))
            # Rule 12e: every run's font is >= 10 pt; Rule 12b: no white (255,255,255) text.
            min_pt = None
            white_runs = 0
            total_runs = 0
            for para in d.paragraphs:
                for run in para.runs:
                    if run.font.size is not None:
                        total_runs += 1
                        pt = run.font.size.pt
                        min_pt = pt if min_pt is None else min(min_pt, pt)
                        if run.font.color and run.font.color.rgb is not None and str(run.font.color.rgb) == "FFFFFF":
                            white_runs += 1
            self.assertIsNotNone(min_pt)
            self.assertGreaterEqual(min_pt, 10.0, "Rule 12e typography floor violated")
            self.assertEqual(white_runs, 0, "Rule 12b zero-white-text violated")
            # No raw '$' LaTeX leaked into any paragraph (Rule 12e Math Lock).
            full_text = "\n".join(par.text for par in d.paragraphs)
            self.assertNotIn("$", full_text)

    def test_generator_source_is_audit_zero_white_text_clean(self):
        # Static scan over .agents; assert none of MY new source files add violations.
        rep = a12.scan_agents_directory(str(AGENTS_DIR))
        mine = {"rfi_ncr_bridge.py", "rfi_ncr_docx_generator.py", "cad_defect_cropper.py"}
        bad = [v for v in rep["violations"] if Path(v["file"]).name in mine]
        self.assertEqual(bad, [], f"Rule 12b/12e source violations in my P4.2 files: {bad}")

    def test_generate_both(self):
        ncrs, rfis = self._records()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "RFINCR.docx"
            res = gen.generate_report_docx(ncrs, rfis, str(out), meta={"project": "P4_BOTH", "audit_status": "FAIL"})
            self.assertTrue(Path(res["ncr"]).is_file())
            self.assertTrue(Path(res["rfi"]).is_file())


if __name__ == "__main__":
    unittest.main()
