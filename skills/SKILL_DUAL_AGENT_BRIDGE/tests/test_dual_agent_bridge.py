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
import subprocess
import contextlib
import io
from unittest.mock import patch
from pathlib import Path

# Thêm đường dẫn scripts vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sync_bus import FileLock, _atomic_write_json, to_relative_path
import sync_bus

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

    def test_other_agent_cannot_claim_complete_or_review_active_shift(self):
        target = self.test_path/'bus.json'
        payload = {'handoff_status': 'IN_PROGRESS', 'current_holder': 'CODEX'}
        target.write_text(json.dumps(payload), encoding='utf-8')
        with patch.multiple(sync_bus, BUS_PATH=target, MEMO_PATH=self.test_path/'memo.md',
                            LOCK_PATH=self.test_path/'lock'), patch.object(sync_bus, 'generate_handoff_memo'):
            before = target.read_bytes()
            for operation in (sync_bus.claim_task, sync_bus.complete_task, sync_bus.request_review):
                with self.assertRaises(PermissionError):
                    operation('GEMINI')
                self.assertEqual(target.read_bytes(), before)
            with contextlib.redirect_stdout(io.StringIO()):
                sync_bus.claim_task('codex')
                sync_bus.complete_task('CODEX')
            self.assertEqual(json.loads(target.read_text())['handoff_status'], 'COMPLETED')

    def test_concurrent_claim_has_only_one_winner(self):
        target = self.test_path/'bus.json'
        target.write_text(json.dumps({'handoff_status': 'PENDING', 'current_holder': 'IDLE'}))
        code = ('import sys;from pathlib import Path;sys.path.insert(0,'+repr(str(Path(sync_bus.__file__).parent))+');'
                'import sync_bus as s;s.BUS_PATH=Path(sys.argv[1]);s.LOCK_PATH=s.BUS_PATH.with_suffix(".lock");'
                's.generate_handoff_memo=lambda *args:None;s.claim_task(sys.argv[2])')
        processes = [subprocess.Popen([sys.executable, '-c', code, str(target), agent],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE) for agent in ('CODEX', 'GEMINI')]
        for process in processes:
            process.communicate(timeout=20)
        self.assertEqual(sorted(process.returncode for process in processes), [0, 1])

    def test_workspace_discovery_new_layout_and_external_cwd(self):
        workspace = self.test_path/'project'
        (workspace/'.agents/memory').mkdir(parents=True)
        with patch.dict(os.environ, {}, clear=False), patch.object(sync_bus.Path, 'cwd', return_value=workspace/'.agents/memory'):
            os.environ.pop('DUAL_AGENT_WORKSPACE', None)
            self.assertEqual(sync_bus.find_workspace_root(), workspace)
            self.assertEqual(sync_bus.get_bus_paths(workspace)[0], workspace/'.agents/memory/DUAL_AGENT_BUS.json')
        with patch.dict(os.environ, {}, clear=False), patch.object(sync_bus.Path, 'cwd', return_value=self.test_path):
            os.environ.pop('DUAL_AGENT_WORKSPACE', None)
            self.assertEqual(sync_bus.find_workspace_root(), Path(__file__).resolve().parents[4])

    def test_legacy_bus_path_supported(self):
        (self.test_path/'memory').mkdir()
        self.assertEqual(sync_bus.get_bus_paths(self.test_path)[0], self.test_path/'memory/DUAL_AGENT_BUS.json')

if __name__ == "__main__":
    unittest.main()
