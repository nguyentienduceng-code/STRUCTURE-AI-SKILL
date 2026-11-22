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
                            LOCK_PATH=self.test_path/'lock', WORKSPACE_ROOT=self.test_path), \
                patch.object(sync_bus, 'generate_handoff_memo'):
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


class TestV32Upgrades(unittest.TestCase):
    """Nâng cấp kiến trúc v3.2: Lease/Heartbeat, Visual Gate, Project-Scoped Resolver."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        self.bus = self.test_path/'bus.json'
        self.memo = self.test_path/'memo.md'
        self.lock = self.test_path/'lock'
        self.payload = {
            'project_context': {'project_code': 'T', 'project_purpose': 'p', 'action_type': 'DYNAMIC'},
            'last_updated_by': 'GEMINI',
            'timestamp': '2026-11-19T09:00:00+07:00',
            'handoff_status': 'PENDING',
            'current_holder': 'IDLE',
            'summary': 's',
            'artifacts_modified': ['.agents/memory/DUAL_AGENT_BUS.json'],
            'next_action_for_partner': {
                'target_agent': 'CLAUDE',
                'task_description': 'nhiem vu thong thuong',
                'target_files': [],
                'acceptance_criteria': [],
                'command': 'c'
            },
            'Verification_Status': 'CONFIRMED_AND_HANDED_OFF'
        }
        self.ctx = patch.multiple(
            sync_bus, BUS_PATH=self.bus, MEMO_PATH=self.memo, LOCK_PATH=self.lock,
            WORKSPACE_ROOT=self.test_path,
        )
        self.ctx.start()
        self._memo_patcher = patch.object(sync_bus, 'generate_handoff_memo')
        self._memo_patcher.start()
        self.bus.write_text(json.dumps(self.payload), encoding='utf-8')

    def tearDown(self):
        self.ctx.stop()
        self._memo_patcher.stop()
        self.test_dir.cleanup()

    # ---- Focus 2: Lease / Heartbeat ----
    def test_claim_sets_lease_and_heartbeat(self):
        with contextlib.redirect_stdout(io.StringIO()):
            data = sync_bus.claim_task('CLAUDE')
        self.assertIn('lease_expire_at', data)
        self.assertIn('last_heartbeat', data)
        self.assertEqual(data['current_holder'], 'CLAUDE')

    def test_heartbeat_refreshes_lease(self):
        with contextlib.redirect_stdout(io.StringIO()):
            first = sync_bus.claim_task('CLAUDE')
            import time
            time.sleep(0.01)
            second = sync_bus.heartbeat('CLAUDE')
        self.assertGreater(second['lease_expire_at'], first['lease_expire_at'])

    def test_expired_allows_auto_claim_without_force(self):
        with contextlib.redirect_stdout(io.StringIO()):
            data = sync_bus.claim_task('GEMINI')
        expired = dict(data)
        from datetime import datetime, timedelta
        expired['lease_expire_at'] = (datetime.now().astimezone() - timedelta(minutes=5)).isoformat()
        self.bus.write_text(json.dumps(expired), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            took_over = sync_bus.claim_task('CLAUDE')
        self.assertEqual(took_over['current_holder'], 'CLAUDE')

    def test_active_lease_still_blocks_other_agent(self):
        with contextlib.redirect_stdout(io.StringIO()):
            sync_bus.claim_task('GEMINI')
        with self.assertRaises(PermissionError):
            with contextlib.redirect_stdout(io.StringIO()):
                sync_bus.claim_task('CLAUDE')

    def test_lease_duration_env_override(self):
        with patch.dict(os.environ, {'DUAL_AGENT_LEASE_MIN': '5'}):
            self.assertEqual(sync_bus._lease_duration_min(), 5)
        self.assertEqual(sync_bus._lease_duration_min(), 60)

    # ---- Focus 4: Visual Gate (Điều 12d) ----
    def test_visual_gate_blocks_cad_task_without_evidence(self):
        cad = json.loads(json.dumps(self.payload))
        cad['next_action_for_partner']['task_description'] = 'Xuat ban ve CAD mat bang ket cau DCE'
        ok, missing = sync_bus.visual_gate_check(cad)
        self.assertFalse(ok)
        self.assertTrue(missing)

    def test_visual_gate_passes_with_png_preview(self):
        cad = json.loads(json.dumps(self.payload))
        cad['next_action_for_partner']['task_description'] = 'Xuat ban ve CAD mat bang ket cau DCE'
        cad['artifacts_modified'].append('01_Projects/16_BPTC_Q12/preview.png')
        ok, _ = sync_bus.visual_gate_check(cad)
        self.assertTrue(ok)

    def test_visual_gate_ignores_non_cad_tasks(self):
        plain = json.loads(json.dumps(self.payload))
        plain['next_action_for_partner']['task_description'] = 'Tinh lai dam D1 theo TCVN 5574:2018'
        ok, _ = sync_bus.visual_gate_check(plain)
        self.assertTrue(ok)

    def test_auto_handoff_blocks_cad_pending_without_evidence(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                sync_bus.auto_handoff(
                    sender='CLAUDE', target='GEMINI', summary='xuất DXF',
                    next_cmd='kiem tra ban ve',
                    task_description='Xuat ban ve CAD DXF',
                    files=['.agents/memory/DUAL_AGENT_BUS.json'],
                    auto_detect_files=False,
                )

    # ---- Focus 3: Project-Scoped Path Resolver ----
    def test_scoped_scan_finds_project_file_only(self):
        proj = self.test_path/'01_Projects'/'16_BPTC_Q12'/'out'
        proj.mkdir(parents=True)
        target = proj/'bmv.dxf'
        target.write_text('x')
        other = self.test_path/'unrelated'
        other.mkdir()
        (other/'noise.md').write_text('y')
        rels = sync_bus.detect_modified_files(self.test_path, project_dir=proj, minutes=5)
        self.assertTrue(any(r.endswith('bmv.dxf') for r in rels), rels)
        self.assertFalse(any('unrelated' in r for r in rels), rels)

    def test_to_relative_path_normalizes_to_workspace_root(self):
        ws = self.test_path/'ws'
        (ws/'a'/'b').mkdir(parents=True)
        f = ws/'a'/'b'/'mod.py'
        f.write_text('x')
        self.assertEqual(sync_bus.to_relative_path(str(f), workspace_root=ws), 'a/b/mod.py')


class TestV33ProductFirst(unittest.TestCase):
    """Nâng cấp v3.3: Evidence-Based Gate, RECEIPTS, Product-First schema (SSOT)."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        self.bus = self.test_path/'bus.json'
        self.memo = self.test_path/'memo.md'
        self.lock = self.test_path/'lock'
        self.payload = {
            'project_context': {'project_code': 'T', 'project_purpose': 'p', 'action_type': 'CODE'},
            'last_updated_by': 'CLAUDE',
            'timestamp': '2026-11-19T10:00:00+07:00',
            'handoff_status': 'PENDING',
            'current_holder': 'IDLE',
            'summary': 's',
            'artifacts_modified': ['.agents/tools/sync_bus.py'],
            'next_action_for_partner': {
                'target_agent': 'GEMINI',
                'task_description': 'nhiem vu',
                'command': 'c',
                'acceptance_criteria': []
            },
            'Verification_Status': 'CONFIRMED_AND_HANDED_OFF'
        }
        self.bus.write_text(json.dumps(self.payload), encoding='utf-8')
        self._patcher = patch.multiple(
            sync_bus, BUS_PATH=self.bus, MEMO_PATH=self.memo, LOCK_PATH=self.lock,
            WORKSPACE_ROOT=self.test_path
        )
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.test_dir.cleanup()

    def _receipts(self) -> Path:
        """Thư mục receipt (fallback: test_path/.agents/_active_receips)."""
        return self.test_path/'.agents/_active_receips'

    # ---- Gate v2: kích hoạt theo action_type ----
    def test_gate_exempt_for_code_action_type(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CODE'
        p['next_action_for_partner']['task_description'] = 'Xuat ban ve CAD DXF'  # keyword CAD
        ok, _ = sync_bus.visual_gate_check(p)
        self.assertTrue(ok)  # CODE -> miễn gate dù task có keyword CAD

    def test_gate_fires_for_cad_action_type_without_evidence(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['task_description'] = 'kiem tra thiet ke'  # KHÔNG keyword CAD
        ok, missing = sync_bus.visual_gate_check(p)
        self.assertFalse(ok)
        self.assertTrue(missing)

    def test_gate_passes_with_evidence_files_field(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['evidence_files'] = ['out/preview.png']
        ok, _ = sync_bus.visual_gate_check(p)
        self.assertTrue(ok)

    # ---- Gate v2: kiểm bằng chứng THẬT SỰ TỒN TẠI trên đĩa ----
    def test_check_on_disk_blocks_missing_evidence(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['evidence_files'] = ['out/preview.png']  # không tồn tại
        ok, missing = sync_bus.visual_gate_check(p, workspace_root=self.test_path, check_on_disk=True)
        self.assertFalse(ok)
        self.assertTrue(any('preview.png' in m for m in missing), missing)

    def test_check_on_disk_passes_with_real_file(self):
        ev = self.test_path/'out'; ev.mkdir(parents=True)
        (ev/'preview.png').write_bytes(b'PNG')
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['evidence_files'] = ['out/preview.png']
        ok, _ = sync_bus.visual_gate_check(p, workspace_root=self.test_path, check_on_disk=True)
        self.assertTrue(ok)

    # ---- RECEIPTS ----
    def test_receipt_written_for_need_review(self):
        p = json.loads(json.dumps(self.payload))
        p['handoff_status'] = 'NEED_REVIEW'
        rfile = sync_bus.write_receipt(p, (True, []), workspace_root=self.test_path)
        self.assertIsNotNone(rfile, "receipt phải được sinh cho ca NEED_REVIEW")
        data = json.loads(rfile.read_text(encoding='utf-8'))
        self.assertEqual(data['handoff_status'], 'NEED_REVIEW')
        self.assertEqual(data['sender'], 'CLAUDE')
        self.assertIn('evidence_hashes', data)
        self.assertIn('bus_sha256', data)

    def test_receipt_written_on_force_bypass_with_reason(self):
        p = json.loads(json.dumps(self.payload))
        rfile = sync_bus.write_receipt(p, (False, ['evidence']), reason='meta handoff, co y du lieu bang chung',
                                       force_used=True, workspace_root=self.test_path)
        self.assertIsNotNone(rfile)
        data = json.loads(rfile.read_text(encoding='utf-8'))
        self.assertTrue(data['force_used'])
        self.assertEqual(data['force_reason'], 'meta handoff, co y du lieu bang chung')

    def test_no_receipt_for_plain_pending(self):
        p = json.loads(json.dumps(self.payload))
        p['handoff_status'] = 'PENDING'
        self.assertIsNone(sync_bus.write_receipt(p, (True, []), workspace_root=self.test_path))

    # ---- Product-First schema trong auto_handoff ----
    def test_auto_handoff_includes_product_first_fields(self):
        with contextlib.redirect_stdout(io.StringIO()):
            payload = sync_bus.auto_handoff(
                sender='CLAUDE', target='GEMINI', summary='s',
                next_cmd='c', handoff_status='PENDING',
                deliverable='1 DXF + audit log',
                evidence_files=['out/preview.png'],
                acceptance_cmd='python -m unittest discover',
                files=['.agents/tools/sync_bus.py'], auto_detect_files=False,
            )
        nap = payload['next_action_for_partner']
        self.assertEqual(nap['deliverable'], '1 DXF + audit log')
        self.assertEqual(nap['evidence_files'], ['out/preview.png'])
        self.assertEqual(nap['acceptance_cmd'], 'python -m unittest discover')

    def test_auto_handoff_omits_product_first_fields_when_unset(self):
        with contextlib.redirect_stdout(io.StringIO()):
            payload = sync_bus.auto_handoff(
                sender='CLAUDE', target='GEMINI', summary='s', next_cmd='c',
                handoff_status='PENDING',
                files=['.agents/tools/sync_bus.py'], auto_detect_files=False,
            )
        nap = payload['next_action_for_partner']
        for key in ('deliverable', 'evidence_files', 'acceptance_cmd'):
            self.assertNotIn(key, nap)  # backward-compatible: không ghi trường rỗng

    # ---- P1 Report Gate: chuẩn RESULT.md theo ca ----
    def test_report_gate_exempt_for_code_action_type(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CODE'
        ok, missing = sync_bus.report_gate_check(p)
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_report_gate_fires_for_cad_without_report_file(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        ok, missing = sync_bus.report_gate_check(p)
        self.assertFalse(ok)
        self.assertTrue(any('report_file' in m for m in missing), missing)

    def test_report_gate_passes_when_report_file_present_on_disk(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        rpt = self.test_path/'.agents/memory/audits/t/claude/C1_RESULT.md'
        rpt.parent.mkdir(parents=True)
        rpt.write_text('# C1_RESULT.md\n## 1. SCOPE_DELIVERED\nx', encoding='utf-8')
        p['next_action_for_partner']['report_file'] = sync_bus.to_relative_path(str(rpt), self.test_path)
        ok, missing = sync_bus.report_gate_check(p, workspace_root=self.test_path, check_on_disk=True)
        self.assertTrue(ok, missing)

    def test_report_gate_fails_when_report_file_missing_on_disk(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['report_file'] = '.agents/memory/audits/t/ghost.md'
        ok, missing = sync_bus.report_gate_check(p, workspace_root=self.test_path, check_on_disk=True)
        self.assertFalse(ok)
        self.assertTrue(any('không tồn tại' in m or 'missing' in m.lower() for m in missing), missing)

    def test_emit_result_report_creates_skeleton_five_sections(self):
        rpath = sync_bus.emit_result_report(
            project_code='T', agent='CLAUDE', summary='scope moi',
            deliverable='1 DXF + log', acceptance_cmd='python -m unittest discover',
            phase='C1', workspace_root=self.test_path,
        )
        self.assertTrue(rpath.exists(), rpath)
        content = rpath.read_text(encoding='utf-8')
        for sec in ('SCOPE_DELIVERED', 'VERIFICATION_COMMAND', 'RESULTS',
                    'CONSTRAINTS', 'HANDOFF_CONTRACT'):
            self.assertIn(sec, content)
        self.assertIn('1 DXF + log', content)
        # layout chuẩn cad_v6: thư mục theo agent, tên file <PHASE>_RESULT.md
        self.assertEqual(rpath.name, 'C1_RESULT.md')
        self.assertIn('claude', str(rpath))

    def test_emit_result_report_does_not_overwrite_existing(self):
        first = sync_bus.emit_result_report(project_code='T', agent='CLAUDE', phase='C1',
                                            workspace_root=self.test_path)
        first.write_text('DU-LIEU-DA-DIEN', encoding='utf-8')
        second = sync_bus.emit_result_report(project_code='T', agent='CLAUDE', phase='C1',
                                             workspace_root=self.test_path)
        self.assertEqual(second, first)
        self.assertEqual(second.read_text(encoding='utf-8'), 'DU-LIEU-DA-DIEN')  # không ghi đè

    def test_auto_handoff_blocks_cad_without_report_file(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                sync_bus.auto_handoff(
                    sender='CLAUDE', target='GEMINI', summary='s', next_cmd='c',
                    handoff_status='PENDING', action_type='CAD',
                    deliverable='DXF', evidence_files=['out/p.png'],
                    check_evidence_on_disk=False,
                    files=['.agents/tools/sync_bus.py'], auto_detect_files=False,
                )

    def test_auto_handoff_passes_cad_with_emitted_report(self):
        with contextlib.redirect_stdout(io.StringIO()):
            payload = sync_bus.auto_handoff(
                sender='CLAUDE', target='GEMINI', summary='s', next_cmd='c',
                handoff_status='PENDING', action_type='CAD',
                deliverable='DXF', evidence_files=['out/p.png'],
                files=['.agents/tools/sync_bus.py'], auto_detect_files=False,
                emit_report=True, phase='C1',
            )
        self.assertIn('report_file', payload['next_action_for_partner'])

    def test_complete_task_blocked_by_report_gate_for_cad(self):
        # Visual Gate PASS nhờ khai báo evidence (chế độ danh khai, default);
        # Report Gate chặn ca CAD vì thiếu RESULT.md.
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['evidence_files'] = ['out/p.png']
        self.bus.write_text(json.dumps(p), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError) as cm:
                sync_bus.complete_task('CLAUDE')
        self.assertIn('REPORT GATE', str(cm.exception))

    def test_complete_task_cad_passes_with_report_file_on_disk(self):
        p = json.loads(json.dumps(self.payload))
        p['project_context']['action_type'] = 'CAD'
        p['next_action_for_partner']['evidence_files'] = ['out/p.png']
        rpt = self.test_path/'.agents/memory/audits/t/claude/C1_RESULT.md'
        rpt.parent.mkdir(parents=True)
        rpt.write_text('# C1_RESULT.md\n## 1. SCOPE_DELIVERED\nok', encoding='utf-8')
        p['next_action_for_partner']['report_file'] = sync_bus.to_relative_path(str(rpt), self.test_path)
        self.bus.write_text(json.dumps(p), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            data = sync_bus.complete_task('CLAUDE')
        self.assertEqual(data['handoff_status'], 'COMPLETED')

    # ---- Regression: generator thật (không patch) — bắt lỗi unpack ----
    def test_generate_handoff_memo_real_call_no_crash(self):
        """Regression: generate_handoff_memo phải chạy thật với visual_gate_check
        (nhiều lần từng vỡ do unpack sai số lượng trả về của gate)."""
        with contextlib.redirect_stdout(io.StringIO()):
            sync_bus.generate_handoff_memo(self.payload, self.memo)
        self.assertTrue(self.memo.exists())
        self.assertIn('HANDOFF', self.memo.read_text(encoding='utf-8'))


if __name__ == "__main__":
    unittest.main()
