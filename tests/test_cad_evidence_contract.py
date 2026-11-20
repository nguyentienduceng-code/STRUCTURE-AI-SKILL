# -*- coding: utf-8 -*-
"""Contract tests for v4/v6 CAD audit evidence compatibility."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "skills" / "SKILL_VERIFY" / "scripts"
sys.path.insert(0, str(VERIFY))

from cad_evidence_contract import load_evidence, normalize  # noqa: E402


class TestCadEvidenceContract(unittest.TestCase):
    def test_v4_payload_passes_through(self):
        dxf = Path(tempfile.mktemp(suffix=".dxf"))
        dxf.write_bytes(b"v4")
        payload = {
            "scale": 100, "mode": "COLUMN_WALL_SETOUT", "dxf_version": "AC1021",
            "entities_log": [], "blocks_defined": {}, "dimstyles_defined": {},
            "layers_defined": {}, "provenance": {"dxf_sha256": hashlib.sha256(dxf.read_bytes()).hexdigest()},
        }
        self.assertIs(normalize(payload, dxf), payload)
        dxf.unlink()

    def test_v6_claims_are_normalized_without_inference(self):
        dxf = Path(tempfile.mktemp(suffix=".dxf"))
        dxf.write_bytes(b"v6")
        payload = {
            "v6_directive": True,
            "v6_status": "OK_V6",
            "claims": {"scale": 50, "mode": "BEAM_SLAB_FRAMING", "entities_log": []},
            "provenance": {"dxf_sha256": hashlib.sha256(dxf.read_bytes()).hexdigest()},
        }
        out = normalize(payload, dxf)
        self.assertEqual(out["scale"], 50)
        self.assertEqual(out["mode"], "BEAM_SLAB_FRAMING")
        self.assertEqual(out["entities_log"], [])
        self.assertEqual(out["blocks_defined"], {})
        self.assertIn("evidence_diagnostics", out)
        dxf.unlink()

    def test_stale_sidecar_is_rejected(self):
        dxf = Path(tempfile.mktemp(suffix=".dxf"))
        dxf.write_bytes(b"current")
        sidecar = dxf.with_suffix(".dce_audit.json")
        sidecar.write_text(json.dumps({"provenance": {"dxf_sha256": "stale"}}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_evidence(dxf)
        dxf.unlink()
        sidecar.unlink()

    def test_compliance_checker_loads_adapter_and_audits_v6_plan_honestly(self):
        import importlib.util
        cad_dir = ROOT / "skills" / "Technical_Illustrator" / "cad_integration"
        if str(cad_dir) not in sys.path:
            sys.path.insert(0, str(cad_dir))
        import cad_plan_engine as cpe

        checker_path = VERIFY / "dce_cad_compliance_checker.py"
        spec = importlib.util.spec_from_file_location("isolated_dce_checker", str(checker_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["isolated_dce_checker"] = mod
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.modules.pop("isolated_dce_checker", None)
        self.assertIsNotNone(mod.load_evidence)

        with tempfile.TemporaryDirectory(prefix="v6_contract_chk_") as tmp:
            out_dxf = Path(tmp) / "kc03_v6.dxf"
            cpe.export_dce_plan(str(out_dxf), sheet_type="KC-03", v6=True)
            res = mod.audit_dxf_compliance(str(out_dxf), profile="full")
            self.assertEqual(res["physical_status"], "PASS")
            self.assertEqual(res["gate_status"], "UNVERIFIED")
            self.assertEqual(res["status"], "NEEDS_REVIEW")

            # Tampering DXF must trigger SHA-256 mismatch via load_evidence
            out_dxf.write_bytes(b"999\nTAMPERED\n" + out_dxf.read_bytes())
            res_bad = mod.audit_dxf_compliance(str(out_dxf), profile="full")
            self.assertIn("SHA256", "\n".join(res_bad.get("metadata_issues", [])))


if __name__ == "__main__":
    unittest.main()
