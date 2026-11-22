# -*- coding: utf-8 -*-
"""
test_cad_bptc_engine.py — Unit Tests for Construction Method Engine BPTC (DCE Pro v5.0)
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
import cad_bptc_engine as cbe
import dce_cad_compliance_checker as dcc


class TestCadBptcEngine(unittest.TestCase):
    def setUp(self):
        self.engine = cbe.CadBptcEngine()

    def test_01_bptc_layer_setup(self):
        """Đảm bảo các layer BPTC được nạp chuẩn xác."""
        self.engine._init_doc()
        doc = self.engine.doc
        assert doc is not None
        layer_names = {ly.dxf.name for ly in doc.layers}
        self.assertIn("DCE_BPTC_Equip", layer_names)
        self.assertIn("DCE_BPTC_Tie", layer_names)
        self.assertIn("DCE_BPTC_Anchor", layer_names)
        self.assertIn("DCE_BPTC_SafeZone", layer_names)

    def test_02_generate_bp02_tower_crane_tie(self):
        """Kiểm tra sinh bản vẽ BP-02 (Cùm neo cẩu tháp QTP125) trên COMPOSITE_DETAIL_GRID."""
        with tempfile.TemporaryDirectory(prefix="bptc_test_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-02_QTP125.dxf"
            res = self.engine.generate_bp02_tower_crane_tie(
                crane_model="QTP125",
                tower_size_mm=1600.0,
                output_dxf=str(out_dxf),
                project_name="DỰ ÁN TÒA THÁP GOLDEN",
            )

            self.assertTrue(out_dxf.is_file())
            out_json = out_dxf.with_suffix(".bptc_audit.json")
            self.assertTrue(out_json.is_file())

            # Kiểm tra dữ liệu audit
            with open(out_json, "r", encoding="utf-8") as f:
                dossier = json.load(f)

            self.assertEqual(dossier["schema_version"], "5.0")
            self.assertEqual(dossier["profile"], "BPTC")
            self.assertEqual(dossier["drawing_code"], "BP-02")
            self.assertEqual(dossier["sheet_layout"]["mode"], "COMPOSITE_DETAIL_GRID")
            self.assertEqual(len(dossier["sheet_layout"]["detail_cells"]), 2)
            self.assertGreater(dossier["bom_summary"]["total_weight_kg"], 100.0)

            real_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            self.assertEqual(dossier["sha256_sync_hash"], real_sha)
            self.assertEqual(dossier["provenance"]["dxf_sha256"], real_sha)

            # Đọc lại DXF và audit tính toàn vẹn
            read_doc = ezdxf.readfile(str(out_dxf))
            self.assertEqual(read_doc.dxfversion, "AC1021")
            aud = read_doc.audit()
            self.assertEqual(len(aud.errors), 0)

            # Kiểm tra bằng compliance checker
            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="physical")
            self.assertEqual(audit_res["physical_status"], "PASS")

    def test_03_generate_bp01_site_plan(self):
        """Kiểm tra sinh bản vẽ BP-01 (Tổng mặt bằng thi công & bán kính an toàn cẩu)."""
        with tempfile.TemporaryDirectory(prefix="bptc_site_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-01_SitePlan.dxf"
            res = self.engine.generate_bp01_site_plan(
                site_w_m=80.0,
                site_h_m=50.0,
                crane_pos=(5.0, -2.0),
                crane_radius_m=60.0,
                output_dxf=str(out_dxf),
            )
            self.assertTrue(out_dxf.is_file())
            self.assertEqual(res["drawing_code"], "BP-01")
            out_json = out_dxf.with_suffix(".bptc_audit.json")
            self.assertTrue(out_json.is_file())
            real_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            self.assertEqual(res["sha256_sync_hash"], real_sha)
            self.assertEqual(res["provenance"]["dxf_sha256"], real_sha)

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "PASS", f"BP-01 audit issues: {audit_res.get('issues')}")
            self.assertTrue(audit_res.get("full_compliance_verified"))
            by_id = {g["gate_id"]: g for g in audit_res["gate_results"]}
            self.assertEqual(by_id["G8.21"]["status"], "NOT_APPLICABLE")
            self.assertEqual(by_id["G8.22"]["status"], "NOT_APPLICABLE")
            self.assertEqual(by_id["G8.24"]["status"], "NOT_APPLICABLE")
            self.assertEqual(by_id["G8.25"]["status"], "PASS")

    def test_04_bptc_g825_evidence_based_fail(self):
        """Xóa thực thể thiết bị DCE_BPTC_Equip trên DXF phải khiến G8.25 FAIL (K1)."""
        with tempfile.TemporaryDirectory(prefix="bptc_neg_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-02_NoEquip.dxf"
            self.engine.generate_bp02_tower_crane_tie(output_dxf=str(out_dxf))
            doc = ezdxf.readfile(str(out_dxf))
            msp = doc.modelspace()
            for ent in [e for e in msp if e.dxf.layer.lower() == "dce_bptc_equip"]:
                msp.delete_entity(ent)
            doc.saveas(str(out_dxf))
            out_json = out_dxf.with_suffix(".bptc_audit.json")
            dossier = json.loads(out_json.read_text(encoding="utf-8"))
            new_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            dossier["sha256_sync_hash"] = new_sha
            dossier["provenance"]["dxf_sha256"] = new_sha
            out_json.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "FAIL")
            g25 = next(g for g in audit_res["gate_results"] if g["gate_id"] == "G8.25")
            self.assertEqual(g25["status"], "FAIL")

    def test_05_bp01_missing_safezone_fails_g825(self):
        """Xóa vùng an toàn DCE_BPTC_SafeZone trên BP-01 phải khiến G8.25 FAIL."""
        with tempfile.TemporaryDirectory(prefix="bptc_bp01_neg_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-01_NoSafeZone.dxf"
            self.engine.generate_bp01_site_plan(
                site_w_m=80.0,
                site_h_m=50.0,
                crane_pos=(5.0, -2.0),
                crane_radius_m=60.0,
                output_dxf=str(out_dxf),
            )
            doc = ezdxf.readfile(str(out_dxf))
            msp = doc.modelspace()
            for ent in [e for e in msp if e.dxf.layer.lower() == "dce_bptc_safezone"]:
                msp.delete_entity(ent)
            doc.saveas(str(out_dxf))
            out_json = out_dxf.with_suffix(".bptc_audit.json")
            dossier = json.loads(out_json.read_text(encoding="utf-8"))
            new_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            dossier["sha256_sync_hash"] = new_sha
            dossier["provenance"]["dxf_sha256"] = new_sha
            out_json.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "FAIL")
            g25 = next(g for g in audit_res["gate_results"] if g["gate_id"] == "G8.25")
            self.assertEqual(g25["status"], "FAIL")

    def test_06_bp01_out_of_bounds_crane_fails_g825(self):
        """Tâm cẩu và SafeZone nằm ngoài ranh giới công trường BP-01 phải khiến G8.25 FAIL."""
        with tempfile.TemporaryDirectory(prefix="bptc_bp01_oob_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-01_OutOfBounds.dxf"
            self.engine.generate_bp01_site_plan(
                site_w_m=80.0,
                site_h_m=50.0,
                crane_pos=(60.0, 0.0),
                crane_radius_m=55.0,
                output_dxf=str(out_dxf),
            )
            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "FAIL")
            g25 = next(g for g in audit_res["gate_results"] if g["gate_id"] == "G8.25")
            self.assertEqual(g25["status"], "FAIL")

    def test_07_bp02_missing_cell_scale_label_fails_g824(self):
        """Xóa nhãn tỷ lệ 1/10 của ô chi tiết CT-01 trên BP-02 phải khiến G8.24 FAIL."""
        with tempfile.TemporaryDirectory(prefix="bptc_bp02_g24_") as tmpdir:
            out_dxf = Path(tmpdir) / "BP-02_NoCellScaleLabel.dxf"
            self.engine.generate_bp02_tower_crane_tie(output_dxf=str(out_dxf))
            doc = ezdxf.readfile(str(out_dxf))
            msp = doc.modelspace()
            for ent in [
                e for e in msp
                if e.dxftype() == "TEXT" and "1/10" in str(getattr(e.dxf, "text", ""))
            ]:
                msp.delete_entity(ent)
            doc.saveas(str(out_dxf))
            out_json = out_dxf.with_suffix(".bptc_audit.json")
            dossier = json.loads(out_json.read_text(encoding="utf-8"))
            new_sha = hashlib.sha256(out_dxf.read_bytes()).hexdigest()
            dossier["sha256_sync_hash"] = new_sha
            dossier["provenance"]["dxf_sha256"] = new_sha
            out_json.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")

            audit_res = dcc.audit_dxf_compliance(str(out_dxf), profile="bptc")
            self.assertEqual(audit_res["status"], "FAIL")
            g24 = next(g for g in audit_res["gate_results"] if g["gate_id"] == "G8.24")
            self.assertEqual(g24["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
