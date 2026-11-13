#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dual_agent_bridge.py — Bộ kiểm thử tự động xác nhận cơ chế Mutex, FileLock và Atomic Write.
Chạy: python -m unittest test_dual_agent_bridge.py
"""

import unittest
import json
import os
import sys
import tempfile
from pathlib import Path

# Thêm đường dẫn scripts vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sync_bus import FileLock, _atomic_write_json, to_relative_path

class TestDualAgentBridge(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_file_lock_acquire_and_release(self):
        lock_file = self.test_path / "test.lock"
        lock = FileLock(lock_file, timeout=2.0)
        self.assertTrue(lock.acquire(), "Phải acquire được lock lần đầu")
        lock.release()

    def test_atomic_write_json(self):
        target_json = self.test_path / "test_bus.json"
        sample_data = {
            "project_code": "TEST_01",
            "status": "IN_PROGRESS",
            "holder": "GEMINI"
        }
        _atomic_write_json(target_json, sample_data)
        self.assertTrue(target_json.is_file(), "File JSON phải được tạo thành công")

        with open(target_json, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["project_code"], "TEST_01")
        self.assertEqual(loaded["holder"], "GEMINI")

    def test_to_relative_path(self):
        root = Path("C:/project/root")
        raw = "C:/project/root/src/module/app.py"
        rel = to_relative_path(raw, workspace_root=root)
        self.assertEqual(rel, "src/module/app.py", "Đường dẫn phải được chuẩn hóa POSIX relative")

if __name__ == "__main__":
    unittest.main()
