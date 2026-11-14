# -*- coding: utf-8 -*-
"""
test_dce_cad_compliance.py — Test Suite Kiểm toán Hồi quy Chuẩn CAD DCE Pro & Zero White Text Lock
=================================================================================================
Sprint 6 · Test Suite #18 · DCE Pro Compliance & Anti-Collision Testing

Mục tiêu kiểm thử:
    1. Kiểm tra tính toàn vẹn của Master Seed Template (DCE_Master_Seed_Template.dxf).
    2. Kiểm tra DCEDXFGenerator kế thừa đúng template và xuất DXF 0 lỗi audit.
    3. Kiểm tra RCCalculatorToDXF và SteelCalculatorToDXF kế thừa template DCE.
    4. Kiểm tra Bộ lọc 8 SKILL_VERIFY (dce_cad_compliance_checker):
       - PASS đối với file chuẩn DCE Pro (15.TEST mat_bang_cot_vach_tang_dien_hinh.dxf).
       - FAIL và bắt sống các file chứa layer tùy tiện (0_TRUC, 0_COT...) hoặc thiếu Block DCE.
    5. Kiểm tra Auto-Linter sanitize_docx_table_colors() thực thi triệt để Điều 12b AGENTS.md.
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENTS_ROOT / "skills" / "Technical_Illustrator" / "cad_integration"))
sys.path.insert(0, str(AGENTS_ROOT / "skills" / "SKILL_VERIFY" / "scripts"))
sys.path.insert(0, str(AGENTS_ROOT / "skills" / "SKILL_PHULUC"))
sys.path.insert(0, str(AGENTS_ROOT / "tools"))

import ezdxf
from dce_dxf_generator import DCEDXFGenerator
from calc_to_dxf import RCCalculatorToDXF, SteelCalculatorToDXF
from cad_plan_engine import export_dce_plan
from cad_plan_engine import DcePlanEngine, build_structural_model, SCALE_MM
from dce_cad_compliance_checker import audit_dxf_compliance
from docx_generator import sanitize_docx_table_colors

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class TestDceMasterTemplate(unittest.TestCase):
    """Kiểm thử tính toàn vẹn của tệp Master Seed Template."""

    def test_01_template_exists_and_valid(self):
        template_path = AGENTS_ROOT / "skills" / "Technical_Illustrator" / "cad_integration" / "templates" / "DCE_Master_Seed_Template.dxf"
        self.assertTrue(template_path.is_file(), f"Master seed template không tồn tại tại: {template_path}")

        doc = ezdxf.readfile(str(template_path))
        self.assertGreaterEqual(len(doc.layers), 35, "Template phải có ít nhất 35 layer DCE chuẩn.")

        # Kiểm tra sự hiện diện của các layer cốt lõi
        layer_names = [l.dxf.name.lower() for l in doc.layers]
        for expected in ['dce_baobetong', 'dce_beam', 'dce_truc', 'dce_dim', 'dce_name', 'dce_hatch']:
            self.assertIn(expected, layer_names, f"Thiếu layer cốt lõi: {expected}")

        # Kiểm tra các blocks cốt lõi
        block_names = [b.name.lower() for b in doc.blocks if not b.name.startswith('*')]
        for expected_block in ['dce_khtentruc', 'tencaukien', 'tktitle', '_archtick']:
            self.assertIn(expected_block, block_names, f"Thiếu block cốt lõi: {expected_block}")

        # Kiểm tra DimStyle cốt lõi
        dimstyles = [d.dxf.name.lower() for d in doc.dimstyles]
        self.assertIn('dce_100mv', dimstyles, "Thiếu DimStyle dce_100mv trong template.")


class TestCadGeneratorsInheritance(unittest.TestCase):
    """Kiểm thử các class sinh CAD DXF kế thừa từ Seed Template."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_02_dce_dxf_generator_inheritance(self):
        gen = DCEDXFGenerator()
        gen.setup_document()
        gen.add_beam(b=300, h=600, h0=560)
        out_path = os.path.join(self.temp_dir.name, "test_beam.dxf")
        gen.save(out_path)

        self.assertTrue(os.path.isfile(out_path))
        doc = ezdxf.readfile(out_path)
        # Xác nhận các layer DCE tồn tại trong tệp xuất ra
        layer_names = [l.dxf.name.lower() for l in doc.layers]
        self.assertIn('dce_baobetong', layer_names)
        self.assertIn('dce_truc', layer_names)

        # Kiểm toán audit 0 lỗi
        auditor = doc.audit()
        self.assertEqual(len(auditor.errors), 0, "File sinh từ DCEDXFGenerator có lỗi audit.")

    def test_03_calc_to_dxf_inheritance(self):
        rc = RCCalculatorToDXF({'section': 'bxh = 300x600 mm', 'concrete': 'B30', 'As_chon_mm2': 1450})
        out_rc = os.path.join(self.temp_dir.name, "test_rc.dxf")
        rc.generate(out_rc)

        self.assertTrue(os.path.isfile(out_rc))
        doc_rc = ezdxf.readfile(out_rc)
        self.assertIn('DCE_BaoBeTong', [l.dxf.name for l in doc_rc.layers])
        self.assertEqual(len(doc_rc.audit().errors), 0)


class TestSkillVerifyCadAuditor(unittest.TestCase):
    """Kiểm thử Bộ lọc 8 (Filter 8: dce_cad_compliance_checker) của SKILL_VERIFY."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _resolve_or_generate(self, rel_name: str, sheet_type: str) -> str:
        deliverable = AGENTS_ROOT.parent / "01_Projects" / "15.TEST" / "04_Deliverables_ToTrinh" / rel_name
        if deliverable.is_file():
            return str(deliverable)
        tmp_dxf = os.path.join(self.temp_dir.name, rel_name)
        export_dce_plan(tmp_dxf, sheet_type=sheet_type)
        return tmp_dxf

    def test_04_audit_passes_on_deliverable_plan(self):
        # Kiểm toán KC-02: Mặt bằng định vị cột vách (deliverable hoặc tự sinh độc lập)
        plan_path = self._resolve_or_generate("mat_bang_cot_vach_tang_dien_hinh.dxf", "KC-02")
        result = audit_dxf_compliance(plan_path)
        self.assertEqual(result['status'], 'PASS', f"Bản vẽ KC-02 không đạt kiểm toán: {result.get('issues')}")
        self.assertEqual(len(result['illegal_layers']), 0)
        self.assertGreater(result['blocks']['axis_bubbles'], 0, "Bản vẽ phải có block bong bóng trục.")
        self.assertGreater(result['blocks']['member_tags'], 0, "Bản vẽ phải có block tên cấu kiện.")
        self.assertTrue(result['graphic_sanity']['has_concrete_solid_hatch'])
        self.assertTrue(result['graphic_sanity']['has_standard_frame'])

    def test_04b_audit_passes_on_beam_slab_plan(self):
        # Kiểm toán KC-03: Mặt bằng kết cấu dầm sàn tầng điển hình
        beam_path = self._resolve_or_generate("mat_bang_dam_san_tang_dien_hinh.dxf", "KC-03")
        result = audit_dxf_compliance(beam_path)
        self.assertEqual(result['status'], 'PASS', f"Bản vẽ KC-03 không đạt kiểm toán: {result.get('issues')}")
        self.assertEqual(len(result['illegal_layers']), 0)
        self.assertGreater(result['blocks']['axis_bubbles'], 0, "Bản vẽ dầm sàn phải có block bong bóng trục.")
        self.assertGreater(result['blocks']['member_tags'], 0, "Bản vẽ dầm sàn phải có block nhãn dầm.")

    def test_04c_audit_passes_on_master_layout_plan(self):
        # Kiểm toán KC-01: Tổng mặt bằng kết cấu & định vị công trình
        master_path = self._resolve_or_generate("mat_bang_tong_the_ket_cau.dxf", "KC-01")
        result = audit_dxf_compliance(master_path)
        self.assertEqual(result['status'], 'PASS', f"Bản vẽ KC-01 không đạt kiểm toán: {result.get('issues')}")
        self.assertEqual(len(result['illegal_layers']), 0)
        self.assertGreater(result['blocks']['axis_bubbles'], 0, "Bản vẽ tổng mặt bằng phải có block bong bóng trục.")

    def test_05_audit_fails_on_illegal_layers(self):
        # Tạo tệp vi phạm giả lập chứa layer 0_TRUC và 0_COT
        bad_path = os.path.join(self.temp_dir.name, "bad_drawing.dxf")
        doc = ezdxf.new('R2010')
        doc.layers.add('0_TRUC', color=1)
        doc.layers.add('0_COT', color=5)
        msp = doc.modelspace()
        msp.add_line((0, 0), (5000, 0), dxfattribs={'layer': '0_TRUC'})
        msp.add_circle((5000, 0), radius=200, dxfattribs={'layer': '0_TRUC'})
        msp.add_lwpolyline([(0, 0), (400, 0), (400, 400), (0, 400)], close=True, dxfattribs={'layer': '0_COT'})
        doc.saveas(bad_path)

        result = audit_dxf_compliance(bad_path)
        self.assertEqual(result['status'], 'FAIL', "Bộ lọc phải đánh rớt tệp có layer 0_TRUC và 0_COT.")
        self.assertGreaterEqual(len(result['illegal_layers']), 2)

    def test_05b_audit_fails_on_missing_hatch_frame_and_beam_void_clash(self):
        # Bản vẽ có layer DCE_* hợp lệ nhưng thiếu Solid Hatch, thiếu Khung/Trục block và có dầm xuyên lỗ mở
        bad_sanity_path = os.path.join(self.temp_dir.name, "bad_sanity.dxf")
        doc = ezdxf.new('R2010')
        for lname in ('DCE_Truc', 'DCE_Beam', 'DCE_VoidX'):
            if lname not in doc.layers:
                doc.layers.add(lname)
        msp = doc.modelspace()
        # 4 đường trục nhưng không có block Dce_KhTenTruc
        for i in range(4):
            msp.add_line((i * 5000, 0), (i * 5000, 10000), dxfattribs={'layer': 'DCE_Truc'})
        # Lỗ mở sàn X từ (1000,1000) đến (3000,3000)
        msp.add_line((1000, 1000), (3000, 3000), dxfattribs={'layer': 'DCE_VoidX'})
        msp.add_line((1000, 3000), (3000, 1000), dxfattribs={'layer': 'DCE_VoidX'})
        # Dầm cắt ngang xuyên qua tâm lỗ mở
        msp.add_line((0, 2000), (5000, 2000), dxfattribs={'layer': 'DCE_Beam'})
        doc.saveas(bad_sanity_path)

        result = audit_dxf_compliance(bad_sanity_path)
        self.assertEqual(result['status'], 'FAIL', "Bộ lọc phải FAIL khi thiếu block trục, thiếu Solid Hatch, thiếu khung hoặc dầm xuyên lỗ mở.")
        self.assertEqual(result['graphic_sanity']['beam_void_clashes'], 1)
        self.assertGreaterEqual(len(result['issues']), 3)


class TestZeroWhiteTextLock(unittest.TestCase):
    """Kiểm thử Điều 12b AGENTS.md (ZERO WHITE TEXT LOCK)."""

    def test_06_sanitize_docx_table_colors_overrides_white(self):
        if not HAS_DOCX:
            self.skipTest("python-docx chưa được cài đặt")

        doc = Document()
        table = doc.add_table(rows=2, cols=2)

        # Ô 1: Giả lập header có nền tối và chữ trắng
        cell = table.cell(0, 0)
        tcPr = cell._tc.get_or_add_tcPr()
        tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="1E3246"/>'))
        p = cell.paragraphs[0]
        run = p.add_run("TIÊU ĐỀ BẢNG")
        run.font.color.rgb = RGBColor(255, 255, 255) # Chữ trắng

        # Gọi hàm Auto-Linter
        sanitize_docx_table_colors(doc)

        # Xác nhận nền tối đã chuyển về nền sáng DCE4EC
        shd_elem = tcPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd")
        fill_val = shd_elem.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill")
        self.assertEqual(fill_val.upper(), "DCE4EC", "Nền tối phải được chuyển về DCE4EC")

        # Xác nhận chữ trắng đã được chuyển về chữ tối 1E3246
        self.assertNotEqual(run.font.color.rgb, RGBColor(255, 255, 255), "Chữ trắng phải bị ghi đè hoàn toàn.")
        self.assertEqual(run.font.color.rgb, RGBColor(0x1E, 0x32, 0x46))


class TestDceV5OffsetAndRevitConversion(unittest.TestCase):
    """
    Kiểm thử tích hợp DCE v5.0 starter kit (RFC_MCP_DCE_CAD_PERCEPTION_LOOP §6.3.1):
    1. _col_centers: model cũ (không offset) giữ 100% hành vi giữa trục (regression).
    2. _col_centers: cột mép (offset_x_mm = bx/2) dịch đúng, lệch vượt biên bị chặn.
    3. column_revit_center: khớp công thức compute_column_revit_center của kit (3 ca,
       kiểm chứng chiều nghịch đảo x_g = x_c - B/2 + a_left).
    """

    def _engine_at_origin(self):
        model = build_structural_model()
        eng = DcePlanEngine(model).setup()
        eng.ox, eng.oy = 0.0, 0.0  # origin trung tính: _wx(x) = x * SCALE_MM
        return eng

    def test_v5_01_regression_column_center_without_offset(self):
        eng = self._engine_at_origin()
        col = {'name': 'T1', 'x': 0.35, 'y': 27.50, 'bx': 0.70, 'by': 1.00}
        cx, cy = eng._col_centers(col)
        self.assertAlmostEqual(cx, 0.35 * SCALE_MM, places=3)
        self.assertAlmostEqual(cy, 27.50 * SCALE_MM, places=3)

    def test_v5_02_mep_column_offset_shifts_center(self):
        eng = self._engine_at_origin()
        # Cột mép: mặt trái nằm TRÊN trục (a_left = 0 theo kit) => tâm lệch +bx/2
        col = {'name': 'T2', 'x': 0.35, 'y': 27.50, 'bx': 0.70, 'by': 1.00,
               'offset_x_mm': 0.35 * SCALE_MM}
        cx, cy = eng._col_centers(col)
        self.assertAlmostEqual(cx, 0.70 * SCALE_MM, places=3)  # 350 + 350
        self.assertAlmostEqual(cy, 27.50 * SCALE_MM, places=3)

    def test_v5_03_offset_beyond_size_rejected(self):
        eng = self._engine_at_origin()
        bad = {'name': 'T3', 'x': 1.0, 'y': 1.0, 'bx': 0.70, 'by': 1.00,
               'offset_x_mm': 0.71 * SCALE_MM}
        with self.assertRaises(ValueError):
            eng._col_centers(bad)

    def test_v5_04_revit_center_matches_kit_formula(self):
        # Ca 1: cột giữa trục (offset 0)
        r0 = DcePlanEngine.column_revit_center({'x': 0.0, 'y': 0.0, 'bx': 0.4, 'by': 0.4})
        self.assertEqual(r0['x_center_mm'], 0.0)
        self.assertEqual(r0['x_center_ft'], 0.0)
        # Ca 2: cột mép (offset_x_mm = 200 = B/2) => khớp kit: tam +200mm
        r1 = DcePlanEngine.column_revit_center({'x': 0.0, 'y': 0.0, 'bx': 0.4, 'by': 0.4,
                                               'offset_x_mm': 200.0})
        self.assertEqual(r1['x_center_mm'], 200.0)
        self.assertAlmostEqual(r1['x_center_ft'], 200.0 / 304.8, places=6)
        # Ca 3: lệch tâm (kit: a_left=100 => x_c = 1500 + (200 - 100) = 1600mm)
        r2 = DcePlanEngine.column_revit_center({'x': 1.5, 'y': 3.0, 'bx': 0.4, 'by': 0.6,
                                               'offset_x_mm': 100.0, 'ssot_uuid': 'U-1'})
        self.assertEqual(r2['x_center_mm'], 1600.0)
        self.assertEqual(r2['y_center_mm'], 3000.0)
        self.assertEqual(r2['ssot_uuid'], 'U-1')
        self.assertAlmostEqual(r2['x_center_ft'], 1600.0 / 304.8, places=6)

    def test_v5_05_sheet_export_unaffected(self):
        # Sau khi thêm offset: model chuẩn (không offset) xuất KC-02 phải audit PASS
        tmp = os.path.join(self._tempdir(), "v5_kc02.dxf")
        export_dce_plan(tmp, sheet_type="KC-02")
        res = audit_dxf_compliance(tmp)
        self.assertEqual(res['status'], 'PASS', f"KC-02 regression FAIL: {res.get('issues')}")

    @classmethod
    def _tempdir(cls):
        import tempfile as _t
        d = _t.mkdtemp(prefix="dce_v5_")
        cls._t = d
        return d

    @classmethod
    def tearDownClass(cls):
        import shutil
        if getattr(cls, '_t', None):
            shutil.rmtree(cls._t, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

