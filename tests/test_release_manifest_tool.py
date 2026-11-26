# -*- coding: utf-8 -*-
"""Lớp P2 — khóa release/manifest_tool.py: hash, verify, drift detection, BUS read-only."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(__file__).resolve().parents[2]
MODULE_PATH = WORKSPACE / "release" / "manifest_tool.py"
spec = importlib.util.spec_from_file_location("manifest_tool", MODULE_PATH)
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)


class ReleaseManifestToolTests(unittest.TestCase):
    def test_make_and_verify_roundtrip(self):
        import tempfile, shutil
        # Chạy trên workspace thật nhưng dùng release-id riêng để tránh đè release production.
        rc = mt.main(["make", "--release-id", "test-roundtrip", "--tests-passed", "35/35"])
        self.assertEqual(rc, 0)
        rc = mt.main(["verify", "--release-id", "test-roundtrip"])
        self.assertEqual(rc, 0, "verify phải PASS với release vừa make (chưa có drift)")
        # Dọn release test (KHÔNG đụng release production khác).
        shutil.rmtree(WORKSPACE / "release" / "test-roundtrip", ignore_errors=True)

    def test_verify_detects_wrapper_crlf_drift(self):
        """Wrapper bị ghi LF phải làm verify FAIL (invariant P1/P2)."""
        wrapper = WORKSPACE / "bootstrap" / "hook_bootstrap.cmd"
        original = wrapper.read_bytes()
        try:
            lf_only = original.replace(b"\r\n", b"\n")
            wrapper.write_bytes(lf_only)
            rc = mt.main(["make", "--release-id", "test-crlf-marker", "--tests-passed", "0"])
            self.assertEqual(rc, 0)
            rc = mt.main(["verify", "--release-id", "test-crlf-marker"])
            self.assertEqual(rc, 1, "verify phải FAIL khi wrapper mất CRLF")
        finally:
            wrapper.write_bytes(original)
            # Dọn các release marker test, giữ nguyên release production.
            for marker in ("test-crlf-marker", "test-roundtrip"):
                shutil.rmtree(WORKSPACE / "release" / marker, ignore_errors=True)

    def test_bus_checksum_is_read_only(self):
        """bus-checksum không --write PHẢI không tạo file, và không sửa BUS."""
        import hashlib
        bus = WORKSPACE / ".agents" / "memory" / "DUAL_AGENT_BUS.json"
        bus_before = bus.read_bytes()
        bus_sha = hashlib.sha256(bus_before).hexdigest()
        chk = WORKSPACE / "release" / "bus_checksum.json"
        chk_state_before = chk.read_bytes() if chk.is_file() else None
        rc = mt.main(["bus-checksum"])  # không --write
        self.assertEqual(rc, 0)
        self.assertEqual(bus.read_bytes(), bus_before, "BUS bị sửa bởi lệnh read-only")
        if chk_state_before is None:
            self.assertFalse(chk.exists(), "bus-checksum không --write không được tạo file")

    def test_bus_checksum_write_creates_snapshot(self):
        """Regression: bare flag `--write` phải ghi snapshot, không in rồi bỏ qua."""
        import json
        chk = WORKSPACE / "release" / "bus_checksum.json"
        existed = chk.is_file()
        before = chk.read_text(encoding="utf-8") if existed else None
        try:
            rc = mt.main(["bus-checksum", "--write"])
            self.assertEqual(rc, 0, "bus-checksum --write phải trả 0")
            self.assertTrue(chk.is_file(), "release/bus_checksum.json chưa được tạo")
            record = json.loads(chk.read_text(encoding="utf-8"))
            self.assertIn("last_checksum", record)
            self.assertEqual(len(record["last_checksum"]), 64, "checksum SHA-256 phải đủ 64 hex")
        finally:
            if existed:
                chk.write_text(before, encoding="utf-8")
            elif chk.is_file():
                chk.unlink()

    def test_registry_has_no_secrets(self):
        reg = WORKSPACE / "release" / "machine_registry.json"
        if not reg.is_file():
            self.skipTest("registry chưa tạo (chạy register-machine trước)")
        text = reg.read_text(encoding="utf-8")
        for forbidden in ("password", "token", "secret", "key"):
            self.assertNotIn(forbidden, text.lower(), "registry chứa từ khóa secret")


if __name__ == "__main__":
    unittest.main(verbosity=2)
