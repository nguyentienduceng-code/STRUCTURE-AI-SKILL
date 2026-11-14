"""Exercise the real Windows guard, renderer and MCP tool lifecycle."""
import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import dce_virtual_drive_guard as guard
guard.configure_runtime()
import ezdxf
import dce_render_preview as preview
import mcp_dce_cad_server as server
logging.getLogger('ezdxf').setLevel(logging.WARNING)


class VirtualDriveGuardTests(unittest.TestCase):
    def setUp(self):
        self.saved_temp = tempfile.tempdir
        self.env_patch = patch.dict(os.environ)
        self.env_patch.start()
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root_patch = patch.object(guard, '_ROOT', self.base / 'scratch')
        self.root_patch.start()
        self.source = self.base / 'input.dxf'
        doc = ezdxf.new()
        self.handle = doc.modelspace().add_text('Vision', dxfattribs={'height': 2}).dxf.handle
        doc.modelspace().add_line((0, 0), (10, 10))
        doc.saveas(self.source)

    def tearDown(self):
        tempfile.tempdir = self.saved_temp
        self.env_patch.stop()
        self.root_patch.stop()
        self.tmp.cleanup()

    def render(self, **kwargs):
        result = preview.render_dxf_to_png(str(self.source), dpi=30, **kwargs)
        self.assertEqual(result['status'], 'OK', result)
        return result

    def test_reject_virtual_unc_relative_and_cloud_paths(self):
        for value in (r'G:\My Drive\preview.png', r'I:\My Drive\cache', r'J:\cache',
                      r'\\server\share\x', r'\\?\C:\Temp\x', r'C:relative', 'relative',
                      r'C:\Temp\..\x', r'C:\OneDrive\x', r'D:\Google Drive\x',
                      r'C:\Temp\image.png:stream'):
            with self.subTest(value=value), self.assertRaises(guard.UnsafeScratchPath):
                guard.require_local(value)

    def test_fixed_local_volume_accepted(self):
        self.assertEqual(guard.require_local(self.base), self.base.resolve())

    def test_unverified_volume_fails_closed(self):
        with patch.object(guard.ctypes, 'WinDLL') as win:
            win.return_value.GetDriveTypeW.return_value = 4
            with self.assertRaises(guard.UnsafeScratchPath):
                guard.require_local(self.base)

    def test_cloud_temp_environment_redirected_without_probe(self):
        original_temp = tempfile.tempdir
        try:
            with patch.object(guard, '_ROOT', None), patch.dict(os.environ, {
                'DCE_CAD_SCRATCH_ROOT': r'G:\must-not-create',
                'TEMP': r'G:\must-not-create', 'TMP': r'I:\must-not-create',
                'LOCALAPPDATA': str(self.base), 'MPLCONFIGDIR': r'G:\must-not-create'}):
                tempfile.tempdir = r'J:\must-not-create'
                with patch.object(tempfile, 'gettempdir', side_effect=AssertionError('unsafe probe')):
                    actual = guard.configure_runtime()
                self.assertTrue(actual.is_relative_to(self.base))
                self.assertEqual(guard.require_local(tempfile.tempdir), Path(tempfile.tempdir))
                guard.require_local(os.environ['MPLCONFIGDIR'])
        finally:
            tempfile.tempdir = original_temp

    def test_no_safe_fallback_refuses_io(self):
        with patch.object(guard, '_ROOT', None), patch.object(
            guard, 'require_local', side_effect=guard.UnsafeScratchPath('blocked')):
            with self.assertRaises(guard.UnsafeScratchPath):
                guard.local_root()

    def test_junction_rejected_and_target_preserved(self):
        target = self.base / 'target'
        target.mkdir()
        marker = target / 'keep.txt'
        marker.write_text('keep')
        junction = self.base / 'junction'
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(target)],
                       check=True, capture_output=True)
        try:
            with self.assertRaises(guard.UnsafeScratchPath):
                guard.require_local(junction / 'cache')
        finally:
            os.rmdir(junction)  # Remove junction only, never recurse into target.
        self.assertEqual(marker.read_text(), 'keep')

    def test_real_png_redirect_and_source_unchanged(self):
        before = self.source.read_bytes()
        result = self.render(out_png=r'G:\My Drive\must-not-create\preview.png')
        path = Path(result['output_png'])
        self.assertTrue(path.is_relative_to(self.base))
        self.assertTrue(path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(self.source.with_suffix('.png').exists())
        self.assertEqual(server.release_preview(result['preview_id'])['status'], 'CLEANED')
        self.assertFalse(path.exists())

    def test_explicit_existing_destination_never_overwritten(self):
        existing = self.base / 'existing.png'
        existing.write_bytes(b'original')
        result = self.render(out_png=str(existing))
        self.assertEqual(existing.read_bytes(), b'original')
        self.assertNotEqual(result['output_png'], str(existing))

    def test_mcp_image_response_automatically_releases_png(self):
        result = server.render_preview(str(self.source), dpi=30)
        content = server.consume_preview(result['preview_id'])
        self.assertEqual(content[0].model_dump(by_alias=True)['mimeType'], 'image/png')
        self.assertTrue(base64.b64decode(content[0].data).startswith(b'\x89PNG'))
        self.assertFalse(Path(result['output_png']).parent.exists())
        with self.assertRaises(ValueError):
            server.consume_preview(result['preview_id'])

    def test_python_vision_exception_still_cleans(self):
        result = None
        with self.assertRaisesRegex(RuntimeError, 'vision failed'):
            with preview.preview_for_vision(str(self.source), dpi=30) as result:
                self.assertTrue(Path(result['output_png']).exists())
                raise RuntimeError('vision failed')
        self.assertFalse(Path(result['output_png']).exists())

    def test_render_failure_removes_partial_png(self):
        import matplotlib.pyplot as plt
        original = plt.get_fignums()
        def fail(layout, target, **kwargs):
            plt.figure()
            Path(target).write_bytes(b'partial')
            raise RuntimeError('render failed')
        with patch.object(preview, 'qsave', side_effect=fail):
            result = preview.render_dxf_to_png(str(self.source))
        self.assertEqual(result['status'], 'E003')
        self.assertEqual(list(guard.managed_dir('previews').iterdir()), [])
        self.assertEqual(plt.get_fignums(), original)

    def test_crop_render_and_failure_close_figures(self):
        import matplotlib.pyplot as plt
        before = plt.get_fignums()
        result = self.render(view_box=(0, 0, 20, 20))
        self.assertTrue(Path(result['output_png']).exists())
        with patch.object(preview.Frontend, 'draw_layout', side_effect=RuntimeError('crop failed')):
            failed = preview.render_dxf_to_png(str(self.source), view_box=(0, 0, 20, 20))
        self.assertEqual(failed['status'], 'E003')
        self.assertEqual(plt.get_fignums(), before)

    def test_concurrent_allocation_is_unique(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: guard.allocate_preview(), range(16)))
        self.assertEqual(len({str(path) for _, path in results}), 16)
        for token, path in results:
            self.assertTrue(path.is_relative_to(self.base))
            self.assertEqual(guard.cleanup_preview(token)['status'], 'CLEANED')

    def test_cleanup_rejects_paths_and_preserves_unowned_files(self):
        for token in ('../input.dxf', str(self.source), 'x' * 32):
            with self.assertRaises(ValueError):
                guard.cleanup_preview(token)
        token, path = guard.allocate_preview()
        extra = path.parent / 'unowned.txt'
        extra.write_text('keep')
        self.assertEqual(guard.cleanup_preview(token)['status'], 'CLEANUP_PENDING')
        self.assertEqual(extra.read_text(), 'keep')
        self.assertTrue(self.source.exists())

    def test_local_lock_retry_and_pending_status(self):
        token, path = guard.allocate_preview()
        path.write_bytes(b'png')
        unlink = Path.unlink
        calls = []
        def locked_once(target, *args, **kwargs):
            if target == path and not calls:
                calls.append(1)
                raise PermissionError(32, 'simulated local lock')
            return unlink(target, *args, **kwargs)
        with patch.object(Path, 'unlink', locked_once):
            self.assertEqual(guard.cleanup_preview(token)['status'], 'CLEANED')
        token, path = guard.allocate_preview()
        with patch.object(Path, 'unlink', side_effect=PermissionError(32, 'locked')):
            self.assertEqual(guard.cleanup_preview(token)['status'], 'CLEANUP_PENDING')

    def test_ttl_sweeps_only_expired_completed_previews(self):
        old, old_path = guard.allocate_preview()
        active, active_path = guard.allocate_preview()
        new, new_path = guard.allocate_preview()
        for token, path in ((old, old_path), (new, new_path)):
            path.write_bytes(b'png')
            guard.finish_preview(token)
        expired = time.time() - guard.PREVIEW_TTL_SECONDS - 10
        os.utime(old_path.parent / '.ready', (expired, expired))
        session = guard.session_path(r'G:\session-keep')
        session.mkdir()
        (session / 'HEAD.json').write_text('{}')
        guard.sweep_previews()
        self.assertFalse(old_path.parent.exists())
        self.assertTrue(active_path.parent.exists())
        self.assertTrue(new_path.exists())
        self.assertTrue((session / 'HEAD.json').exists())

    def test_cloud_edit_session_reopen_revision_and_source_integrity(self):
        before = self.source.read_bytes()
        alias = r'G:\My Drive\must-not-create\session'
        result = server.edit_entity(alias, source_dxf=str(self.source))
        root = Path(result['session_dir'])
        self.assertTrue(root.is_relative_to(self.base))
        self.assertEqual(guard.session_path(alias), root)
        revision = result['revision']
        moved = server.edit_entity(alias, handle=self.handle, dx=1, dy=2,
                                   expected_revision=revision, dry_run=False)
        self.assertNotEqual(moved['revision'], revision)
        self.assertEqual(server.edit_entity(str(root))['revision'], moved['revision'])
        with self.assertRaisesRegex(Exception, 'Stale revision'):
            server.edit_entity(alias, handle=self.handle, dx=1,
                               expected_revision=revision, dry_run=False)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse((root / 'candidate.dxf').exists())
        self.assertTrue((root / 'HEAD.json').exists())

    def test_real_mcp_stdio_vision_lifecycle_with_cloud_temp(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def run():
            params = StdioServerParameters(command=sys.executable,
                args=['-B', str(Path(server.__file__).resolve())],
                env={**os.environ, 'TEMP': r'G:\must-not-create',
                     'TMP': r'G:\must-not-create', 'MPLCONFIGDIR': r'G:\must-not-create',
                     'DCE_CAD_SCRATCH_ROOT': str(self.base / 'server-scratch')})
            with open(self.base / 'server-stderr.log', 'w', encoding='utf-8') as err:
                async with stdio_client(params, errlog=err) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        listing = await session.list_tools()
                        names = {tool.name for tool in listing.tools}
                        self.assertTrue({'render_preview', 'consume_preview', 'release_preview'} <= names)
                        rendered = await session.call_tool('render_preview', {
                            'dxf_path': str(self.source), 'out_png': r'G:\must-not-create\preview.png',
                            'dpi': 30})
                        envelope = rendered.model_dump(by_alias=True)
                        self.assertFalse(envelope.get('isError'), envelope)
                        metadata = json.loads(next(c['text'] for c in envelope['content'] if c['type'] == 'text'))
                        path = Path(metadata['output_png'])
                        self.assertTrue(path.is_relative_to(self.base / 'server-scratch'))
                        self.assertTrue(path.exists())
                        consumed = await session.call_tool('consume_preview', {'preview_id': metadata['preview_id']})
                        envelope = consumed.model_dump(by_alias=True)
                        self.assertFalse(envelope.get('isError'), envelope)
                        pictures = [c for c in envelope['content'] if c['type'] == 'image']
                        self.assertEqual(len(pictures), 1, envelope)
                        self.assertTrue(base64.b64decode(pictures[0]['data']).startswith(b'\x89PNG'))
                        self.assertFalse(path.parent.exists())
        asyncio.run(run())


if __name__ == '__main__':
    unittest.main(verbosity=2)
