#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suite 25: real DXF/XLSX -> Universal Reader -> provenance -> batch PMM.

No solver stub: tests evaluate concurrent N-Mx-My rows with the actual fiber
solver. Fixture data are explicitly synthetic, not project design approvals.
"""
import copy
import csv
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import project_data_pipeline as pipeline
from doc_reader import read_document
from input_provenance_guard import audit_inputs

CONVENTIONS = dict(reaction_axes='GLOBAL', axial_sign=1, mx_sign=1, my_sign=1)


def bars(h=400):
    return [dict(x=x, y=y, dia=25) for x, y in [(-150, -h/2+50), (0, -h/2+50), (150, -h/2+50),
        (-150, 0), (150, 0), (-150, h/2-50), (0, h/2-50), (150, h/2-50)]]


class ProjectPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='project_pipeline_tests_')
        cls.folder = Path(cls.temp.name)
        cls.book_path = cls.folder/'project_inputs.xlsx'
        cls.cad_path = cls.folder/'column_plan.dxf'
        import openpyxl
        book = openpyxl.Workbook()
        columns = book.active
        columns.title = 'Column Schedule'
        columns.append(['Column', 'Story', 'Joint', 'b(mm)', 'h(mm)', 'Concrete', 'Rebar', 'Bars(mm)', 'Angle(deg)'])
        columns.append(['C1', 'L1', None, 400, 400, 'B30', 'CB400-V', json.dumps(bars()), 0])
        columns.append(['C2', 'L1', None, 400, 600, 'B30', 'CB400-V', json.dumps(bars(600)), 90])
        model = book.create_sheet('Model Parameters')
        model.append(['Parameter', 'Value', 'Unit'])
        for name, value, unit in [('Concrete', 'B30', '1'), ('Rebar', 'CB400-V', '1'),
            ('Rb', 17, 'MPa'), ('Eb', 32500, 'MPa'), ('Rs', 350, 'MPa'), ('Rsc', 350, 'MPa'),
            ('Es', 200000, 'MPa'), ('eps_b0', .002, '1'), ('eps_b2', .0035, '1'),
            ('eps_s_max', .025, '1'), ('concrete_diagram', 'trilinear', '1')]:
            model.append([name, value, unit])
        coordinates = book.create_sheet('Joint Coordinates')
        coordinates.append(['Joint', 'Story', 'X(m)', 'Y(m)', 'Z(m)'])
        coordinates.append([101, 'L1', 0, 0, 0])
        coordinates.append([102, 'L1', 2, 0, 0])
        reactions = book.create_sheet('Joint Reactions')
        reactions.merge_cells('A1:I1')
        reactions['A1'] = 'SYNTHETIC ETABS CONCURRENT TEST REACTIONS'
        reactions.append([None]*9)
        reactions.append(['Joint', 'Story', 'OutputCase', 'StepType', 'StepNum', 'F3', 'M1', 'M2', 'CaseType'])
        reactions.append([None, None, None, None, None, 'kN', 'kNm', 'kNm', None])
        reactions.append([101, 'L1', 'ULS_HIGH_N', None, None, 2000, 40, 20, 'Linear Static'])
        reactions.append([101, 'L1', 'ULS_GOVERNING_M', None, None, 1000, 150, 100, 'Linear Static'])
        reactions.append([101, 'L1', 'ULS_BALANCED', None, None, 1500, 120, 80, 'Linear Static'])
        reactions.append([102, 'L1', 'ULS_ROTATED', None, None, 1200, 50, 80, 'Linear Static'])
        book.save(cls.book_path)
        book.close()
        import ezdxf
        drawing = ezdxf.new('R2010')
        drawing.header['$INSUNITS'] = 4
        drawing.layers.new('S-COLUMN')
        for name, center, width, height in [('C1', 0, 400, 400), ('C2', 2000, 600, 400)]:
            drawing.modelspace().add_lwpolyline([(center-width/2, -height/2), (center+width/2, -height/2),
                (center+width/2, height/2), (center-width/2, height/2)], close=True, dxfattribs={'layer': 'S-COLUMN'})
            drawing.modelspace().add_text(name, dxfattribs={'insert': (center, 0), 'height': 30, 'layer': 'S-COLUMN'})
        drawing.saveas(cls.cad_path)
        cls.cad = read_document(cls.cad_path)
        cls.excel = read_document(cls.book_path)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_pipeline(self, workbook=None, **kwargs):
        sources = kwargs.pop('sources', [self.cad, workbook or self.excel])
        return pipeline.run_project_pipeline(sources, conventions=kwargs.pop('conventions', CONVENTIONS), **kwargs)

    def edited_book(self, name, edit):
        import openpyxl
        book = openpyxl.load_workbook(self.book_path)
        edit(book)
        path = self.folder/(name+'.xlsx')
        book.save(path)
        book.close()
        return read_document(path)

    def test_01_real_files_e2e_complete_schedule_and_guard_pass(self):
        result = self.run_pipeline(sources=[self.cad_path, self.book_path])
        self.assertEqual(result['status'], 'COMPLETED', result)
        self.assertTrue(result['all_passed'])
        self.assertEqual(result['counts']['PASS'], 2)
        self.assertEqual(result['summary_table']['headers'], pipeline.SUMMARY_HEADERS)
        self.assertEqual(len(result['summary_table']['rows']), 2)
        for member in result['members']:
            self.assertEqual(member['summary']['Trạng thái'], 'ĐẠT')
            self.assertEqual(member['Binding']['method'], 'UNIQUE_3D_WCS_COORDINATES')
            for case in member['case_results']:
                self.assertTrue(case['calculation']['converged'])
                self.assertTrue(case['calculation']['Input_Provenance_Audit']['allowed'])
                self.assertTrue(audit_inputs(case['calculation']['Inputs'], case['Provenance'])['allowed'])
                self.assertTrue(all(p['Source_Type'] == 'DOCUMENT_EXTRACTED' and p['Verified'] is True for p in case['Provenance']))
        json.dumps(result, ensure_ascii=False, allow_nan=False)

    def test_02_governing_case_is_max_eta_not_max_N_or_mixed_envelope(self):
        result = self.run_pipeline()
        member = result['members'][0]
        governing = member['governing']
        self.assertEqual(governing['case'], 'ULS_GOVERNING_M')
        self.assertEqual((governing['inputs']['N_ed'], governing['inputs']['Mx_ed'], governing['inputs']['My_ed']),
                         (1000, 150, 100))
        self.assertEqual(governing['calculation']['eta'], max(c['calculation']['eta'] for c in member['case_results']))
        self.assertEqual(len(member['case_results']), 3)

    def test_provenance_preserves_actual_file_sheet_row_and_material_sources(self):
        governing = self.run_pipeline()['members'][0]['governing']
        records = {p['Parameter']: p for p in governing['Provenance']}
        self.assertIn('project_inputs.xlsx, Sheet: Joint Reactions, Row: 6', records['N_ed']['Source_Ref'])
        self.assertIn('column_plan.dxf', records['b']['Source_Ref'])
        self.assertIn('Layer:', records['b']['Source_Ref'])
        self.assertIn('Sheet: Column Schedule, Row: 2', records['bars[0].x']['Source_Ref'])
        self.assertIn('Sheet: Model Parameters', records['Rb']['Source_Ref'])
        self.assertEqual(len(records['Rb']['Source_SHA256']), 64)
        self.assertAlmostEqual(records['bars[0].area']['Value'], math.pi*25**2/4)

    def test_global_to_local_moment_rotation_and_cad_dimensions(self):
        governing = self.run_pipeline()['members'][1]['governing']
        self.assertAlmostEqual(governing['inputs']['b'], 400)
        self.assertAlmostEqual(governing['inputs']['h'], 600)
        self.assertAlmostEqual(governing['inputs']['Mx_ed'], 80)
        self.assertAlmostEqual(governing['inputs']['My_ed'], -50)

    def test_reader_results_and_json_cache_are_supported_without_mutation(self):
        before = copy.deepcopy(self.excel)
        path = self.folder/'reader_cache.json'
        path.write_text(json.dumps(self.excel, ensure_ascii=False), encoding='utf-8')
        result = self.run_pipeline(sources=[self.cad, path])
        self.assertTrue(result['all_passed'])
        self.assertEqual(self.excel, before)

    def test_stale_or_modified_reader_cache_cannot_receive_verified_file_provenance(self):
        modified = copy.deepcopy(self.excel)
        table = next(t for t in modified['tables'] if t.get('sheet') == 'Joint Reactions')
        table['rows'][0][5] = 1
        with self.assertRaisesRegex(pipeline.PipelineDataError, 'STALE_OR_MODIFIED_READER_RESULT'):
            self.run_pipeline(modified)

    def test_workbook_only_explicit_document_id_binding(self):
        def change(book):
            book['Column Schedule']['C2'] = 101
            book['Column Schedule']['C3'] = 102
        excel = self.edited_book('explicit_ids', change)
        result = self.run_pipeline(sources=[excel])
        self.assertTrue(result['all_passed'])
        self.assertTrue(all(m['Binding']['method'] == 'EXPLICIT_DOCUMENT_ID' for m in result['members']))

    def test_units_are_converted_and_mixed_force_moment_units_supported(self):
        def change(book):
            sheet = book['Joint Reactions']
            sheet['F4'], sheet['G4'], sheet['H4'] = 'N', 'Nmm', 'Nmm'
            for row in range(5, 9):
                sheet.cell(row, 6).value *= 1000
                sheet.cell(row, 7).value *= 1e6
                sheet.cell(row, 8).value *= 1e6
        result = self.run_pipeline(self.edited_book('new_units', change))
        self.assertTrue(result['all_passed'])
        inputs = result['members'][0]['governing']['inputs']
        self.assertEqual((inputs['N_ed'], inputs['Mx_ed'], inputs['My_ed']), (1000, 150, 100))

    def test_missing_sign_convention_is_not_guessed(self):
        for convention in [None, {}, dict(CONVENTIONS, axial_sign=True), dict(CONVENTIONS, reaction_axes='LOCAL')]:
            with self.subTest(convention=convention), self.assertRaises(pipeline.PipelineDataError):
                self.run_pipeline(conventions=convention)

    def test_negative_axial_sign_mapping_is_explicit_and_traceable(self):
        def change(book):
            for row in range(5, 9):
                book['Joint Reactions'].cell(row, 6).value *= -1
        result = self.run_pipeline(self.edited_book('downward_sign', change), conventions=dict(CONVENTIONS, axial_sign=-1))
        self.assertTrue(result['all_passed'])
        record = next(r for r in result['members'][0]['governing']['Provenance'] if r['Parameter'] == 'N_ed')
        self.assertEqual(record['Value'], 1000)
        self.assertEqual(record['Source_Value'], -1000)
        self.assertIn('axial_sign', record['Transform'])

    def test_missing_actual_bar_layout_blocks_only_affected_member(self):
        excel = self.edited_book('missing_bars', lambda b: setattr(b['Column Schedule']['H2'], 'value', '8D25'))
        result = self.run_pipeline(excel)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['members'][0]['summary']['Trạng thái'], 'CHƯA ĐỦ DỮ LIỆU')
        self.assertEqual(result['members'][1]['state'], 'PASS')
        self.assertIsNone(result['schedule'][0]['η'])

    def test_missing_model_parameter_is_not_filled_from_solver_default(self):
        def change(book):
            model = book['Model Parameters']
            for row in range(2, model.max_row+1):
                if model.cell(row, 1).value == 'Es':
                    model.delete_rows(row)
                    break
        result = self.run_pipeline(self.edited_book('missing_Es', change))
        self.assertFalse(result['all_passed'])
        self.assertEqual(result['counts']['BLOCKED'], 2)
        self.assertTrue(all('MISSING_DOCUMENTED_MODEL_PARAMETER:Es' in ' '.join(m['errors']) for m in result['members']))

    def test_material_grade_context_prevents_reusing_B30_strength_for_B25(self):
        excel = self.edited_book('wrong_grade', lambda b: setattr(b['Column Schedule']['F3'], 'value', 'B25'))
        result = self.run_pipeline(excel)
        self.assertEqual(result['members'][0]['state'], 'PASS')
        self.assertEqual(result['members'][1]['state'], 'BLOCKED')
        self.assertIn('GRADE_CONTEXT', ' '.join(result['members'][1]['errors']))

    def test_missing_load_in_one_case_cannot_turn_other_cases_into_pass(self):
        excel = self.edited_book('missing_F3', lambda b: setattr(b['Joint Reactions']['F6'], 'value', None))
        result = self.run_pipeline(excel)
        self.assertFalse(result['members'][0]['approved'])
        self.assertEqual(result['members'][0]['state'], 'INCONCLUSIVE')
        self.assertFalse(result['members'][0]['governing_is_final'])
        self.assertEqual(result['members'][1]['state'], 'PASS')

    def test_max_min_envelope_rows_are_not_concurrent_cases(self):
        excel = self.edited_book('envelope', lambda b: setattr(b['Joint Reactions']['D6'], 'value', 'Max'))
        result = self.run_pipeline(excel)
        self.assertEqual(result['members'][0]['state'], 'INCONCLUSIVE')
        self.assertIn('NONCONCURRENT_ENVELOPE', ' '.join(result['members'][0]['errors']))

    def test_missing_units_block_load_conversion(self):
        excel = self.edited_book('wrong_unit', lambda b: setattr(b['Joint Reactions']['F4'], 'value', 'm'))
        result = self.run_pipeline(excel)
        self.assertFalse(result['all_passed'])
        self.assertTrue(all('MISSING_OR_UNSUPPORTED_UNIT' in ' '.join(m['errors']) for m in result['members']))

    def test_duplicate_case_different_values_are_not_silently_selected(self):
        def change(book):
            sheet = book['Joint Reactions']
            values = [c.value for c in sheet[6]]
            values[5] = 3000
            sheet.append(values)
        result = self.run_pipeline(self.edited_book('duplicate_case', change))
        self.assertEqual(result['members'][0]['state'], 'BLOCKED')
        self.assertIn('DUPLICATE_CONCURRENT', ' '.join(result['members'][0]['errors']))

    def test_ambiguous_nearby_joint_coordinates_are_blocked(self):
        excel = self.edited_book('ambiguous_joint', lambda b: b['Joint Coordinates'].append([999, 'L1', .0005, 0, 0]))
        result = self.run_pipeline(excel)
        self.assertEqual(result['members'][0]['state'], 'BLOCKED')
        self.assertIn('AMBIGUOUS', ' '.join(result['members'][0]['errors']))

    def test_same_joint_cannot_be_assigned_to_two_columns(self):
        def change(book):
            book['Column Schedule']['C2'] = 101
            book['Column Schedule']['C3'] = 101
        excel = self.edited_book('joint_reused', change)
        result = self.run_pipeline(sources=[excel])
        self.assertFalse(result['all_passed'])
        self.assertTrue(all('JOINT_ASSIGNED_TO_MULTIPLE' in ' '.join(m['errors']) for m in result['members']))

    def test_joint_identifier_punctuation_is_preserved_in_binding(self):
        def change(book):
            book['Column Schedule']['C2'] = '10-1'
            book['Column Schedule']['C3'] = 102
        excel = self.edited_book('joint_punctuation', change)
        result = self.run_pipeline(sources=[excel])
        self.assertEqual(result['members'][0]['state'], 'BLOCKED')
        self.assertIn('NO_LOAD_CASES_FOR_BOUND_JOINT', result['members'][0]['errors'])
        self.assertEqual(result['members'][1]['state'], 'PASS')

    def test_column_identifier_punctuation_is_not_stripped_from_cad_labels(self):
        import ezdxf
        drawing = ezdxf.readfile(self.cad_path)
        for text in drawing.modelspace().query('TEXT'):
            if text.dxf.text == 'C1':
                text.dxf.text = 'C-1'
        path = self.folder/'punctuation_plan.dxf'
        drawing.saveas(path)
        result = self.run_pipeline(sources=[path, self.excel])
        self.assertEqual(result['members'][0]['state'], 'BLOCKED')
        self.assertFalse(result['all_passed'])

    def test_cad_and_schedule_dimension_conflict_blocks_binding(self):
        excel = self.edited_book('bad_dimension', lambda b: setattr(b['Column Schedule']['D2'], 'value', 500))
        result = self.run_pipeline(excel)
        self.assertEqual(result['members'][0]['state'], 'BLOCKED')
        self.assertIn('DIMENSION_CONFLICT', ' '.join(result['members'][0]['errors']))

    def test_joint_centroid_offset_generates_traceable_first_moments(self):
        excel = self.edited_book('tiny_offset', lambda b: setattr(b['Joint Coordinates']['C2'], 'value', .0005))
        result = self.run_pipeline(excel)
        inputs = result['members'][0]['governing']['inputs']
        self.assertAlmostEqual(inputs['My_ed'], 100.5)
        record = next(r for r in result['members'][0]['governing']['Provenance'] if r['Parameter'] == 'My_ed')
        self.assertIn('Joint coordinates', record['Source_Ref'])

    def test_known_structural_failure_is_not_marked_pass(self):
        def change(book):
            book['Joint Reactions']['G6'], book['Joint Reactions']['H6'] = 1500, 1000
        result = self.run_pipeline(self.edited_book('structural_failure', change))
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertFalse(result['all_passed'])
        self.assertEqual(result['schedule'][0]['Trạng thái'], 'KHÔNG ĐẠT')
        self.assertGreater(result['schedule'][0]['η'], 1)

    def test_axial_failure_retains_unknown_moment_utilization_without_nan(self):
        excel = self.edited_book('axial_failure', lambda b: setattr(b['Joint Reactions']['F6'], 'value', 10000))
        result = self.run_pipeline(excel)
        self.assertEqual(result['schedule'][0]['Trạng thái'], 'KHÔNG ĐẠT')
        self.assertIsNone(result['schedule'][0]['η'])
        self.assertEqual(result['members'][0]['governing']['inputs']['N_ed'], 10000)
        json.dumps(result, allow_nan=False)

    def test_solver_controls_cannot_overwrite_physical_input_or_provenance(self):
        for options in [dict(N_ed=1), dict(provenance=[]), dict(require_provenance=False)]:
            with self.subTest(options=options), self.assertRaises(pipeline.PipelineDataError):
                self.run_pipeline(solver_options=options)

    def multifloor_book(self):
        def change(book):
            columns = book['Column Schedule']
            coordinates = book['Joint Coordinates']
            reactions = book['Joint Reactions']
            for i, joint in [(2, 201), (3, 202)]:
                values = [cell.value for cell in columns[i]]
                values[1], values[2] = 'L2', None
                columns.append(values)
                coordinates.append([joint, 'L2', 0 if joint == 201 else 2, 0, 3])
                reactions.append([joint, 'L2', 'ULS_L2', None, None, 1000, 60, 40, 'Linear Static'])
        return self.edited_book('multifloor', change)

    def test_multi_storey_same_column_names_are_scoped_and_flat_plan_elevation_is_explicit(self):
        excel = self.multifloor_book()
        sources = [{'source': self.cad, 'story': 'L1'}, {'source': self.cad, 'story': 'L2'}, excel]
        result = self.run_pipeline(sources=sources, coordinate_mode='XY_STORY')
        self.assertTrue(result['all_passed'], [(m['column'], m['story'], m['errors']) for m in result['members']])
        self.assertEqual(result['counts']['PASS'], 4)
        self.assertEqual({(m['story'], m['column']) for m in result['members']},
                         {('L1', 'C1'), ('L1', 'C2'), ('L2', 'C1'), ('L2', 'C2')})
        self.assertEqual(result['members'][2]['Binding']['joint'], '201')

    def test_storey_filter_excludes_other_storeys_without_creating_orphans(self):
        result = self.run_pipeline(sources=[{'source': self.cad, 'story': 'L1'},
            {'source': self.cad, 'story': 'L2'}, self.multifloor_book()], stories=['L1'], coordinate_mode='XY_STORY')
        self.assertTrue(result['all_passed'])
        self.assertEqual(len(result['members']), 2)
        self.assertEqual(len(result['excluded_by_story_filter']), 2)
        self.assertEqual(result['unbound_reaction_rows'], [])

    def test_unscoped_plan_cannot_be_reused_for_multiple_storeys_silently(self):
        result = self.run_pipeline(self.multifloor_book(), coordinate_mode='XY_STORY')
        self.assertFalse(result['all_passed'])
        self.assertTrue(all('UNSCOPED_CAD_REUSED' in ' '.join(m['errors']) for m in result['members']))

    def test_xyz_mode_does_not_ignore_mismatched_plan_elevations(self):
        result = self.run_pipeline(sources=[{'source': self.cad, 'story': 'L1'},
            {'source': self.cad, 'story': 'L2'}, self.multifloor_book()])
        self.assertFalse(result['all_passed'])
        self.assertTrue(all(m['state'] == 'BLOCKED' for m in result['members'] if m['story'] == 'L2'))

    def test_arc_segments_are_not_misrepresented_as_rectangular_columns(self):
        import ezdxf
        drawing = ezdxf.readfile(self.cad_path)
        entity = drawing.modelspace().query('LWPOLYLINE')[0]
        points = entity.get_points('xyb')
        points[0] = (points[0][0], points[0][1], .2)
        entity.set_points(points, format='xyb')
        path = self.folder/'curved_column.dxf'
        drawing.saveas(path)
        result = self.run_pipeline(sources=[path, self.excel])
        self.assertFalse(result['all_passed'])
        self.assertTrue(any('CAD_ARC' in item['error'] for item in result['binding_issues']))

    def test_cad_column_without_section_schedule_still_appears_as_blocked(self):
        import ezdxf
        drawing = ezdxf.readfile(self.cad_path)
        drawing.modelspace().add_lwpolyline([(3800,-200),(4200,-200),(4200,200),(3800,200)],
                                          close=True,dxfattribs={'layer':'S-COLUMN'})
        drawing.modelspace().add_text('C3',dxfattribs={'insert':(4000,0),'height':30,'layer':'S-COLUMN'})
        path = self.folder/'extra_column.dxf'
        drawing.saveas(path)
        result = self.run_pipeline(sources=[path,self.excel])
        self.assertFalse(result['all_passed'])
        self.assertEqual(result['counts']['total'],3)
        self.assertEqual(result['schedule'][2]['Tên cột'],'C3')
        self.assertEqual(result['schedule'][2]['Trạng thái'],'CHƯA ĐỦ DỮ LIỆU')

    def test_cli_exports_summary_csv_and_keeps_sources_unchanged(self):
        manifest = self.folder/'manifest.json'
        manifest.write_text(json.dumps(dict(sources=[str(self.cad_path), str(self.book_path)], conventions=CONVENTIONS)), encoding='utf-8')
        target, csv_target = self.folder/'batch_result.json', self.folder/'schedule.csv'
        before = (self.cad_path.read_bytes(), self.book_path.read_bytes())
        process = subprocess.run([sys.executable, str(ROOT/'tools/project_data_pipeline.py'), '-i', str(manifest),
                                  '-o', str(target), '--summary-csv', str(csv_target)],
                                 capture_output=True, text=True, encoding='utf-8', timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(json.loads(process.stdout)['all_passed'])
        self.assertTrue(json.loads(target.read_text(encoding='utf-8'))['all_passed'])
        with csv_target.open(encoding='utf-8-sig', newline='') as file:
            records = list(csv.reader(file))
        self.assertEqual(records[0], pipeline.SUMMARY_HEADERS)
        self.assertEqual(len(records), 3)
        self.assertEqual(before, (self.cad_path.read_bytes(), self.book_path.read_bytes()))

    def test_registered_as_suite_25(self):
        path = ROOT/'tests/run_all_tests.py'
        source = path.read_text(encoding='utf-8').replace("if sys.platform == 'win32':", 'if False:')
        namespace = {'__file__': str(path), '__name__': 'suite_registry'}
        exec(compile(source, str(path), 'exec'), namespace)
        suites = [s for s in namespace['SUITES'] if s[0].startswith('25.')]
        self.assertEqual(len(suites), 1)
        self.assertEqual(Path(suites[0][1][1]).resolve(), Path(__file__).resolve())


if __name__ == '__main__':
    unittest.main(verbosity=2)
