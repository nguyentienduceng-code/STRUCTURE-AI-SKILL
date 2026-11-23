# -*- coding: utf-8 -*-
"""
test_mcp_dce_cad_server.py — Test Suite Kiểm Thử Toàn Diện MCP DCE-CAD Server
=============================================================================

Mục tiêu (Sprint 1 Verification):
    Kiểm thử tự động toàn bộ 8 công cụ MCP trong mcp_dce_cad_server.py:
    1. convert_to_dwg (degrade an toàn khi chưa có ODA)
    2. render_cad_plan (dry_run không ghi đĩa & render thật)
    3. render_preview (ảnh PNG phân giải cao cô lập trên ổ cứng vật lý)
    4. validate_cad (Bộ lọc 8 kiểm toán Điều 12d AGENTS.md)
    5. consume_preview (nạp base64 Vision & tự động xóa file PNG đĩa)
    6. release_preview (dọn dẹp tài nguyên thủ công)
    7. edit_entity (optimistic locking revision-based)
    8. resolve_cad_collisions (local output, source preservation)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import mcp_dce_cad_server as srv


class TestMcpDceCadServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp(prefix="mcp_cad_test_")

    def test_01_tool_registration_and_schemas(self):
        """Kiểm tra toàn bộ 8 tools được đăng ký với schema đầy đủ."""
        tools = srv.list_registered_tools() if hasattr(srv, 'list_registered_tools') else []
        if not tools and hasattr(srv.SERVER, 'list_tools'):
            import asyncio
            tools = asyncio.run(srv.SERVER.list_tools())
        
        tool_names = [t.name for t in tools]
        expected_tools = [
            "render_cad_plan", "render_preview", "consume_preview",
            "release_preview", "validate_cad", "edit_entity", "convert_to_dwg", "resolve_cad_collisions",
            "auto_layout_and_scale_plan", "export_cad_sheet_set",
            # Tầng 2B (solo): native DWG snapshot + D1/D1A diff (Core Console)
            "native_dwg_snapshot", "native_dwg_diff",
        ]
        for et in expected_tools:
            self.assertIn(et, tool_names, f"Thiếu công cụ: {et}")
        import json
        config = json.loads((TOOLS_DIR/'mcp_config.json').read_text(encoding='utf-8'))
        self.assertEqual({s.split('(',1)[0] for s in config['_note']['tools']}, set(tool_names))

    def test_02_convert_to_dwg_degrade(self):
        """convert_to_dwg phải degrade an toàn trả UNAVAILABLE khi chưa có ODA."""
        from unittest.mock import patch
        with patch.object(srv, 'ODA_EXE', str(Path(self.tmp_dir) / 'unavailable.exe')):
            res = srv.convert_to_dwg("non_existent.dxf")
        self.assertEqual(res.get("status"), "UNAVAILABLE")
        if res.get("status") == "UNAVAILABLE":
            self.assertIn("reason", res)
            self.assertIn("fallback", res)

    def test_03_render_cad_plan_dry_run(self):
        """render_cad_plan với dry_run=True không được ghi file xuống đĩa."""
        res = srv.render_cad_plan(sheet_type="KC-02", dry_run=True)
        self.assertEqual(res.get("status"), "DRY_RUN_OK")
        self.assertFalse(res.get("file_written", True))
        self.assertGreater(res.get("modelspace_entities", 0), 0)

    def test_04_full_perception_loop(self):
        """Kiểm thử trọn vẹn chuỗi: render_cad_plan -> render_preview -> validate_cad -> consume."""
        dxf_path = os.path.join(self.tmp_dir, "test_render.dxf")
        
        # 1. Sinh bản vẽ thật
        r_plan = srv.render_cad_plan(output_dxf_path=dxf_path, sheet_type="KC-02")
        self.assertEqual(r_plan.get("status"), "OK")
        self.assertEqual(r_plan['requested_output_dxf'], dxf_path)
        dxf_path = r_plan['output_dxf']
        self.assertTrue(os.path.isfile(dxf_path))
        self.assertGreater(os.path.getsize(dxf_path), 50000)

        # 2. Render ảnh preview PNG
        r_prev = srv.render_preview(dxf_path=dxf_path, dpi=150)
        self.assertEqual(r_prev.get("status"), "OK")
        png_path = r_prev.get("output_png")
        self.assertTrue(os.path.isfile(png_path))
        self.assertGreater(os.path.getsize(png_path), 1000)
        preview_id = r_prev.get("preview_id")
        self.assertIsNotNone(preview_id)

        # 3. Kiểm toán Điều 12d
        r_val = srv.validate_cad(dxf_path=dxf_path)
        self.assertEqual(r_val.get("status"), "NEEDS_REVIEW")
        self.assertFalse(r_val['full_compliance_verified'])
        self.assertEqual(srv.validate_cad(dxf_path, profile='physical')['status'], 'PASS')

        # 4. Consume ảnh phục vụ Vision & tự động xóa PNG trên đĩa
        img_contents = srv.consume_preview(preview_id)
        self.assertEqual(len(img_contents), 1)
        self.assertGreater(len(img_contents[0].data), 1000)
        # Xác nhận file PNG đã tự động bị xóa
        self.assertFalse(os.path.exists(png_path), "File PNG tạm phải bị xóa sau khi consume")

    def test_05_edit_entity_inspection(self):
        """edit_entity hỗ trợ inspect bản vẽ và dời vị trí text theo revision."""
        dxf_path = os.path.join(self.tmp_dir, "test_render.dxf")
        if not os.path.isfile(dxf_path):
            dxf_path = srv.render_cad_plan(output_dxf_path=dxf_path, sheet_type="KC-02")['output_dxf']
        
        sess_dir = os.path.join(self.tmp_dir, "edit_sess")
        # Inspect session
        res = srv.edit_entity(session_dir=sess_dir, source_dxf=dxf_path, dry_run=True)
        self.assertIn(res.get("status"), ["OK", "DRY_RUN_OK"])
        self.assertIn("revision", res)
        self.assertTrue("drawing" in res or "drawing" in res.get("current", {}))

    def test_06_resolve_cad_collisions_tool(self):
        """resolve_cad_collisions tự động phát hiện và né chữ qua MCP."""
        dxf_path = os.path.join(self.tmp_dir, "test_render.dxf")
        if not os.path.isfile(dxf_path):
            dxf_path = srv.render_cad_plan(output_dxf_path=dxf_path, sheet_type="KC-02")['output_dxf']

        # Test dry_run
        res_dry = srv.resolve_cad_collisions(dxf_path=dxf_path, dry_run=True)
        self.assertEqual(res_dry["status"], "NEEDS_REVIEW" if res_dry["remaining_collision_count"] else "DRY_RUN_OK")
        self.assertIn("displacements_planned", res_dry)

        # Test execute real
        out_dxf = os.path.join(self.tmp_dir, "resolved_plan.dxf")
        res_real = srv.resolve_cad_collisions(dxf_path=dxf_path, output_dxf=out_dxf, dry_run=False)
        self.assertEqual(res_real["status"], "NEEDS_REVIEW" if (res_real["remaining_collision_count"] or res_real["leader_conflicts"] or res_real["apply_errors"]) else "OK")
        self.assertLessEqual(res_real["remaining_collision_count"], res_real["initial_collision_count"])
        self.assertTrue(Path(res_real["output_dxf"]).is_file())

    def test_07_collision_tool_routes_output_and_preserves_source(self):
        import ezdxf, hashlib
        from dce_virtual_drive_guard import require_local
        src=Path(self.tmp_dir)/"collision_source.dxf"
        doc=ezdxf.new();doc.header["$INSUNITS"]=4
        doc.layers.new("DCE_Name")
        for x in (0,20):
            doc.modelspace().add_text("C\u1ed8T",dxfattribs={"layer":"DCE_Name","height":250,"insert":(x,0,0)})
        doc.saveas(src)
        before=hashlib.sha256(src.read_bytes()).hexdigest()
        result=srv.resolve_cad_collisions(str(src),output_dxf="G:/My Drive/forbidden_collision_output.dxf")
        self.assertTrue(result["file_written"])
        self.assertTrue(require_local(result["output_dxf"]).is_file())
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),before)
        Path(result["output_dxf"]).unlink()

    def test_08_render_routes_output_and_keeps_protocol_stdout_clean(self):
        import contextlib, io
        from dce_virtual_drive_guard import require_local
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            result = srv.render_cad_plan(output_dxf_path='G:/My Drive/forbidden_mcp.dxf')
        self.assertEqual(capture.getvalue(), '')
        self.assertTrue(require_local(result['output_dxf']).is_file())
        self.assertNotEqual(result['requested_output_dxf'], result['output_dxf'])
        Path(result['output_dxf']).unlink()

    def test_09_invalid_sheet_and_missing_model_do_not_use_demo(self):
        for args in ({'sheet_type': 'KC-INVALID'}, {'model_json_path':str(Path(self.tmp_dir)/'absent.json')},
                     {'pdf_path':str(Path(self.tmp_dir)/'absent.pdf')}):
            result = srv.render_cad_plan(**args)
            self.assertEqual(result['status'], 'E001')
            self.assertFalse(result['file_written'])

    def test_10_commit_requires_revision(self):
        result = srv.edit_entity(handle='123', dry_run=False)
        self.assertEqual(result['status'], 'E001')
        self.assertFalse(result['file_written'])

    def test_11_failed_module_import_does_not_poison_cache(self):
        module = Path(self.tmp_dir)/'bad_import.py'
        module.write_text("raise RuntimeError('injected')",encoding='utf-8')
        with self.assertRaises(RuntimeError):
            srv._load(module, 'dce_failed_import_probe')
        self.assertNotIn('dce_failed_import_probe',sys.modules)

    def test_12_real_stdio_registration_validation_and_generation(self):
        """Exercise JSON-RPC framing, schemas and tool responses in a fresh process."""
        import asyncio, json
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def exercise():
            params = StdioServerParameters(command=sys.executable,
                args=['-B', str(TOOLS_DIR/'mcp_dce_cad_server.py')],
                env={**os.environ,'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'})
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    schemas = {t.name:getattr(t, 'input_schema', None) or getattr(t, 'inputSchema') for t in listing.tools}
                    expected_cfg = json.loads((TOOLS_DIR / 'mcp_config.json').read_text(encoding='utf-8'))
                    self.assertEqual(len(schemas), len(expected_cfg['_note']['tools']))
                    self.assertEqual(schemas['validate_cad']['properties']['profile']['default'],'full')
                    result = await session.call_tool('render_cad_plan',{'sheet_type':'KC-02'})
                    self.assertFalse(getattr(result, 'is_error', getattr(result, 'isError', False)), str(result))
                    data = getattr(result, 'structured_content', None) or getattr(result, 'structuredContent', None) or json.loads(result.content[0].text)
                    self.assertEqual(data['status'],'OK')
                    actual = data['output_dxf']
                    try:
                        result = await session.call_tool('validate_cad',{'dxf_path':actual})
                        self.assertFalse(getattr(result, 'is_error', getattr(result, 'isError', False)),str(result))
                        data = getattr(result, 'structured_content', None) or getattr(result, 'structuredContent', None) or json.loads(result.content[0].text)
                        self.assertEqual(data['status'],'NEEDS_REVIEW')
                        self.assertEqual(data['gates_unverified'],20)
                        self.assertFalse(data['full_compliance_verified'])
                    finally:
                        Path(actual).unlink()
        asyncio.run(asyncio.wait_for(exercise(),timeout=45))

    def test_13_export_cad_sheet_set_and_auto_layout_cad_first_no_pdf(self):
        """MCP CAD tools phai uu tien xuat DXF, KHONG tu dong tao PDF khi khong ghi chu."""
        import shutil
        r_auto = srv.auto_layout_and_scale_plan(sheet_type="KC-03")
        try:
            self.assertEqual(r_auto["status"], "OK")
            self.assertTrue(r_auto["v6"])
            self.assertFalse(r_auto["pdf_generated"])
            self.assertEqual(r_auto["png"]["status"], "SKIPPED")
            self.assertTrue(Path(r_auto["output_dxf"]).is_file())
        finally:
            if r_auto.get("output_dxf") and Path(r_auto["output_dxf"]).exists():
                Path(r_auto["output_dxf"]).unlink()
                audit_p = Path(r_auto["output_dxf"]).with_suffix(".dce_audit.json")
                if audit_p.exists():
                    audit_p.unlink()

        r_set = srv.export_cad_sheet_set(sheet_types=["KC-02", "KC-03"])
        try:
            self.assertEqual(r_set["status"], "OK")
            self.assertTrue(r_set["file_written"])
            self.assertFalse(r_set["pdf_generated"])
            self.assertEqual(r_set["pdf_path"], "")
            self.assertEqual(r_set["preview_pngs"], [])
            self.assertGreater(r_set["registry_total_elements"], 0)
            out_dir = Path(r_set["output_dir"])
            self.assertEqual(list(out_dir.glob("*.pdf")), [])
            self.assertEqual(list(out_dir.glob("*.png")), [])
            self.assertEqual(len(r_set["sheets"]), 2)
            for s in r_set["sheets"]:
                self.assertTrue(Path(s["dxf_path"]).is_file())
                self.assertGreaterEqual(s["template_blocks"], 98)
        finally:
            if r_set.get("output_dir") and Path(r_set["output_dir"]).exists():
                shutil.rmtree(r_set["output_dir"], ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
