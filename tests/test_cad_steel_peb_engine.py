# -*- coding: utf-8 -*-
"""
test_cad_steel_peb_engine.py — Unit Tests for Steel PEB Engine & 25 Gates (DCE Pro v5.0)
========================================================================================
"""

from __future__ import annotations

import hashlib
import json
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
import cad_steel_peb_engine as spe
import cad_steel_primitives as csp
import cad_bptc_engine as cbe
import dce_cad_compliance_checker as dcc


class TestCadSteelPebEngine(unittest.TestCase):
    def setUp(self):
        self.engine = spe.CadSteelPebEngine()

    def test_01_steel_layer_setup(self):
        """Kiểm tra các layer Profile STEEL_PEB được nạp đầy đủ."""
        self.engine._init_doc()
        doc = self.engine.doc
        assert doc is not None
        layer_names = {ly.dxf.name for ly in doc.layers}
        self.assertIn("DCE_Steel_Main", layer_names)
        self.assertIn("DCE_Steel_Plate", layer_names)
        self.assertIn("DCE_Steel_Bolt", layer_names)
        self.assertIn("DCE_Steel_Weld", layer_names)

    def test_02_generate_st01_and_audit_25_gates(self):
        """Kiểm tra sinh bản vẽ ST-01 và kiểm toán đạt 25/25 cổng G8.01-G8.25."""
        with tempfile.TemporaryDirectory(prefix="peb_test_") as tmpdir:
            out_dxf = Path(tmpdir) / "ST-01_MainFrame.dxf"
            res = self.engine.generate_st01_main_frame(
                span_m=24.0,
                eave_h_m=8.0,
                roof_slope_pct=10.0,
                output_dxf=str(out_dxf),
                project_name="NHÀ MÁY THÉP TIỀN CHẾ VIỆT NHẬT",
            )

            self.assertTrue(out_dxf.is_file())
            out_json = out_dxf.with_suffix(".steel_audit.json")
            self.assertTrue(out_json.is_file())

            # Kiểm tra dữ liệu audit
            with open(out_json, "r", encoding="utf-8") as f:
                dossier = json.load(f)

            self.assertEqual(dossier["schema_version"], "5.0")
            self.assertEqual(dossier["profile"], "STEEL_PEB")
            self.assertEqual(dossier["drawing_code"], "ST-01")
            self.assertEqual(dossier["sheet_layout"]["mode"], "COMPOSITE_DETAIL_GRID")
            self.assertEqual(len(dossier["sheet_layout"]["detail_cells"]), 2)
            self.assertGreater(dossier["bom_summary"]["total_weight_kg"], 500.0)

            real_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            self.assertEqual(dossier["sha256_sync_hash"], real_sha)
            self.assertEqual(dossier["provenance"]["dxf_sha256"], real_sha)

            # Kiểm toán compliance checker với profile steel_peb
            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="steel_peb")
            self.assertEqual(audit_res["status"], "PASS")
            self.assertEqual(audit_res["gates_registered"], 25)
            self.assertEqual(audit_res["gates_total"], 25)
            self.assertEqual(audit_res["gates_failed"], 0)
            self.assertTrue(audit_res["full_compliance_verified"])

            # Xác nhận có đủ các cổng mới G8.21 - G8.25
            gate_ids = {g["gate_id"] for g in audit_res["gate_results"]}
            for expected_gid in ("G8.21", "G8.22", "G8.23", "G8.24", "G8.25"):
                self.assertIn(expected_gid, gate_ids)

    def test_03_bp02_audit_25_gates(self):
        """Kiểm toán bản vẽ BP-02 (Cùm neo tháp) đạt trọn vẹn 25/25 cổng G8.01-G8.25."""
        with tempfile.TemporaryDirectory(prefix="bptc_25_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-02_Collar.dxf"
            bptc_eng = cbe.CadBptcEngine()
            bptc_eng.generate_bp02_tower_crane_tie(
                crane_model="QTP125",
                output_dxf=str(out_dxf),
                project_name="TÒA NHÀ SKYLINE",
            )

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "PASS")
            self.assertEqual(audit_res["gates_registered"], 25)
            self.assertEqual(audit_res["gates_total"], 25)
            self.assertEqual(audit_res["gates_failed"], 0)
            self.assertTrue(audit_res["full_compliance_verified"])

    def test_04_sidecar_sha256_tamper_rejected(self):
        """Sửa DXF sau khi xuất mà không cập nhật sidecar phải bị từ chối (K2)."""
        with tempfile.TemporaryDirectory(prefix="peb_tamper_") as tmpdir:
            out_dxf = Path(tmpdir) / "ST-01_Tamper.dxf"
            self.engine.generate_st01_main_frame(output_dxf=str(out_dxf))
            doc = ezdxf.readfile(str(out_dxf))
            doc.modelspace().add_text("TAMPERED", dxfattribs={"layer": "DCE_Name", "height": 50.0, "insert": (1000, 1000)})
            doc.saveas(str(out_dxf))

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="steel_peb")
            self.assertEqual(audit_res["status"], "NEEDS_REVIEW")
            self.assertFalse(audit_res["full_compliance_verified"])
            self.assertTrue(any("SHA256" in m for m in audit_res["metadata_issues"]))

    def test_05_evidence_based_g821_and_g822_failures(self):
        """Kiểm chứng G8.21 và G8.22 bắt thật vi phạm trên entity DXF (K1)."""
        def _resign(dxf_p: Path, json_p: Path) -> None:
            data = json.loads(json_p.read_text(encoding="utf-8"))
            dig = hashlib.sha256(dxf_p.read_bytes()).hexdigest()
            data["sha256_sync_hash"] = dig
            data["provenance"]["dxf_sha256"] = dig
            json_p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        with tempfile.TemporaryDirectory(prefix="peb_neg_") as tmpdir:
            # 1) Vi phạm bước bu lông G8.21 (p1=40 < 67.5)
            dxf_bolt = Path(tmpdir) / "ST-01_BadBolt.dxf"
            self.engine.generate_st01_main_frame(output_dxf=str(dxf_bolt))
            doc_b = ezdxf.readfile(str(dxf_bolt))
            csp.draw_bolt_array(
                doc_b.modelspace(),
                origin=(5000, 5000),
                rows=2,
                cols=2,
                p1=40.0,
                p2=40.0,
                d_bolt=24.0,
                layer_bolt="DCE_Steel_Bolt",
            )
            doc_b.saveas(str(dxf_bolt))
            _resign(dxf_bolt, dxf_bolt.with_suffix(".steel_audit.json"))

            res_b = dcc.audit_dxf_compliance(str(dxf_bolt), profile="steel_peb")
            self.assertEqual(res_b["status"], "FAIL")
            g21 = next(g for g in res_b["gate_results"] if g["gate_id"] == "G8.21")
            self.assertEqual(g21["status"], "FAIL")

            # 2) Thiếu ký hiệu hàn G8.22
            dxf_weld = Path(tmpdir) / "ST-01_NoWeld.dxf"
            self.engine.generate_st01_main_frame(output_dxf=str(dxf_weld))
            doc_w = ezdxf.readfile(str(dxf_weld))
            msp_w = doc_w.modelspace()
            for ent in [e for e in msp_w if e.dxf.layer.lower() == "dce_steel_weld"]:
                msp_w.delete_entity(ent)
            doc_w.saveas(str(dxf_weld))
            _resign(dxf_weld, dxf_weld.with_suffix(".steel_audit.json"))

            res_w = dcc.audit_dxf_compliance(str(dxf_weld), profile="steel_peb")
            self.assertEqual(res_w["status"], "FAIL")
            g22 = next(g for g in res_w["gate_results"] if g["gate_id"] == "G8.22")
            self.assertEqual(g22["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
