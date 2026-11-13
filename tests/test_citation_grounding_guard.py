#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suite 23: actual normative PDF grounding and adversarial input audit trails.

The real-PDF tests are mandatory: a missing TCVN 5574:2018 fixture is a failure,
not a skipped/green test. Other PDFs are synthetic adversarial test fixtures.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import citation_grounding_auditor as cg
import input_provenance_guard as pg


def real_citation(**changes):
    c = {'Ma_Tieu_Chuan': 'TCVN 5574', 'Nam_Ban_Hanh': 2018,
         'Dieu_Bang_Muc': 'Điều 7.3.5', 'Ten_Bang_Hinh': 'Công thức (26)',
         'Trang_So': 52, 'Trich_Yeu': 'Hệ số kể đến ảnh hưởng của uốn dọc'}
    c.update(changes)
    return c


def provenance(name='gamma_II', value=18.5, **changes):
    record = {'Parameter': name, 'Value': value, 'Unit': 'kN/m3',
              'Source_Type': 'DOCUMENT_EXTRACTED',
              'Source_Ref': 'BaoCao_DCCT_HK1.pdf, Trang 12, Bảng 3', 'Verified': True}
    record.update(changes)
    return record


class RealPDFGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auditor = cg.CitationGroundingAuditor()

    def test_real_5574_clause_and_equation_26(self):
        result = self.auditor.verify_citation(real_citation())
        self.assertTrue(result['Citation_Content_Verified'], result)
        self.assertEqual(result['Verified_PDF_Page'], 52)
        self.assertIn('7.3.5', result['Verified_Evidence_Snippet'])
        self.assertIn('(26)', result['Verified_Evidence_Snippet'])
        self.assertEqual(len(result['PDF_SHA256']), 64)
        self.assertTrue(Path(result['PDF_Path']).is_file())

    def test_cover_offset_plus_two_pages(self):
        r = self.auditor.verify_citation(real_citation(Trang_So=50))
        self.assertTrue(r['Citation_Content_Verified'], r)
        self.assertEqual(r['Page_Offset'], 2)

    def test_adversarial_nonexistent_clause_and_table(self):
        for changes in [{'Dieu_Bang_Muc': 'Điều 99.99', 'Ten_Bang_Hinh': ''},
                        {'Dieu_Bang_Muc': 'Bảng 100', 'Ten_Bang_Hinh': ''},
                        {'Ten_Bang_Hinh': 'Bảng 100'}]:
            with self.subTest(changes=changes):
                r = self.auditor.verify_citation(real_citation(**changes))
                self.assertFalse(r['Citation_Content_Verified'])
                self.assertEqual(r['Error_Code'], 'HALLUCINATION_DETECTED')
                self.assertEqual(r['Warning'], 'CITATION_GROUNDING_MISMATCH')
                self.assertEqual(r['Verified_Evidence_Snippet'], '')

    def test_real_clause_with_fabricated_title_is_blocked(self):
        r = self.auditor.verify_citation(real_citation(Ten_Bang_Hinh='Bảng cường độ vật liệu vũ trụ'))
        self.assertFalse(r['Citation_Content_Verified'])

    def test_wrong_page_outside_window_not_global_search(self):
        r = self.auditor.verify_citation(real_citation(Trang_So=100))
        self.assertFalse(r['Citation_Content_Verified'])
        self.assertNotIn(52, r['Searched_PDF_Pages'])

    def test_replaced_edition_rejected_even_with_existing_pdf(self):
        r = self.auditor.verify_citation(real_citation(Nam_Ban_Hanh=2012))
        self.assertEqual(r['Reason'], 'EDITION_NOT_CURRENT_IN_LOCK')

    def test_conflicting_combined_and_separate_year(self):
        r = self.auditor.verify_citation(real_citation(Ma_Tieu_Chuan='TCVN 5574:2012'))
        self.assertEqual(r['Reason'], 'CONFLICTING_EDITION')

    def test_multiple_standards_in_one_object_must_not_use_only_first(self):
        result = self.auditor.verify_citation(real_citation(Ma_Tieu_Chuan='TCVN 5574:2018 / TCVN 99999:2020'))
        self.assertFalse(result['Citation_Content_Verified'])
        self.assertEqual(result['Reason'], 'MULTIPLE_STANDARDS_IN_ONE_CITATION')

    def test_unknown_or_unavailable_standard_fails_closed(self):
        unknown = self.auditor.verify_citation(real_citation(Ma_Tieu_Chuan='TCVN 99999'))
        self.assertEqual(unknown['Reason'], 'STANDARD_NOT_IN_LOCK')
        missing = self.auditor.verify_citation(real_citation(Ma_Tieu_Chuan='QCVN 01', Nam_Ban_Hanh=2021))
        self.assertFalse(missing['Citation_Content_Verified'])
        self.assertEqual(missing['Reason'], 'PDF_NOT_FOUND')

    def test_base_qcvn_without_required_amendment_not_green(self):
        r = self.auditor.verify_citation(real_citation(Ma_Tieu_Chuan='QCVN 06', Nam_Ban_Hanh=2022))
        self.assertEqual(r['Reason'], 'COMPOSITE_EDITION_REQUIRES_AMENDMENT_VERIFICATION')

    def test_legacy_calculator_aliases(self):
        citation = {'Ma_TC': 'TCVN 5574:2018', 'Dieu_Muc': 'Điều 7.3.5',
                    'Bang_Hinh': 'Công thức (26)', 'Trang': '52'}
        self.assertTrue(self.auditor.verify_citation(citation)['Citation_Content_Verified'])

    def test_nested_citations_lists_and_summary_percentage(self):
        data = {'Calculation_Logs': [{'nested': [{'Citation': real_citation()}]},
                                    {'Citations': [real_citation(Dieu_Bang_Muc='Điều 99.99')]}]}
        before = copy.deepcopy(data)
        r = self.auditor.audit(data)
        self.assertEqual((r['total_citations'], r['verified_citations'], r['pdf_verified_percent']), (2, 1, 50))
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(len(r['suspicious_citations']), 1)
        self.assertEqual(data, before)

    def test_untrusted_verified_flag_is_recomputed(self):
        r = self.auditor.verify_citation(real_citation(Dieu_Bang_Muc='Điều 99.99',
            Citation_Content_Verified=True, Verified_Evidence_Snippet='forged'))
        self.assertFalse(r['Citation_Content_Verified'])
        self.assertEqual(r['Verified_Evidence_Snippet'], '')

    def test_invalid_pages(self):
        for page in [None, '', 0, -1, True, 52.5, 99999, '52-55']:
            with self.subTest(page=page):
                self.assertFalse(self.auditor.verify_citation(real_citation(Trang_So=page))['Citation_Content_Verified'])

    def test_no_citations_and_empty_citation_are_not_pass(self):
        for data in [{}, {'Citation': {}}, {'Citation': None}, {'Citation': []}]:
            self.assertEqual(self.auditor.audit(data)['status'], 'BLOCKED')

    def test_bad_citation_cannot_hide_next_to_valid_one(self):
        for malformed in [{}, 23, None, 'not a citation']:
            with self.subTest(malformed=malformed):
                data = {'good': {'Citation': real_citation()}, 'bad': {'Citation': malformed}}
                result = self.auditor.audit(data)
                self.assertEqual(result['total_citations'], 2)
                self.assertEqual(result['status'], 'BLOCKED')
        result = self.auditor.audit({'Citations': [real_citation(), {}]})
        self.assertEqual(result['total_citations'], 2)
        self.assertEqual(result['status'], 'BLOCKED')

    def test_shorthand_unknown_clause_not_silently_dropped(self):
        for data in [real_citation(Dieu_Bang_Muc='Điều 7.3.5 và 99.99'),
                     'TCVN 5574:2018 — Điều 7.3.5 và 99.99 — Trang 52']:
            with self.subTest(data=data):
                self.assertEqual(self.auditor.audit(data)['status'], 'BLOCKED')

    def test_markdown_and_docx_including_header_and_table(self):
        from docx import Document
        text = 'TCVN 5574:2018 — Điều 7.3.5 / Công thức (26) — Trang 52'
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            markdown = directory/'report.md'
            markdown.write_text(text, encoding='utf-8')
            self.assertEqual(self.auditor.audit_file(markdown)['status'], 'PASS')
            doc = Document()
            doc.add_paragraph(text)
            doc.sections[0].header.paragraphs[0].text = 'TCVN 5574:2018 — Điều 99.99 — Trang 52'
            doc.add_table(rows=1, cols=1).cell(0, 0).text = text
            path = directory/'report.docx'
            doc.save(path)
            r = self.auditor.audit_file(path)
            self.assertEqual(r['total_citations'], 3)
            self.assertEqual(r['verified_citations'], 2)
            self.assertEqual(r['status'], 'BLOCKED')

    def test_text_missing_page_or_year_is_detected_and_blocked(self):
        for text in ['TCVN 5574:2018 Điều 7.3.5', 'TCVN 5574 Điều 7.3.5 Trang 52']:
            r = self.auditor.audit(text)
            self.assertEqual(r['total_citations'], 1)
            self.assertEqual(r['status'], 'BLOCKED')


class AdversarialPDFTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        (self.directory/'TCVN').mkdir()
        self.lock = self.directory/'lock.md'
        self.lock.write_text('## 1. Bảng Chốt\n| Field | Current | Old | File |\n'
                             '| Concrete | **TCVN 5574:2018** | TCVN 5574:2012 | test.pdf |\n'
                             '## 2. Known Gap\n| misleading | TCVN 5574:2012 | | |', encoding='utf-8')
        self.path = self.directory/'TCVN'/'TCVN 5574-2018.pdf'

    def tearDown(self):
        self.temp.cleanup()

    def write_pdf(self, text):
        import pymupdf
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((30, 40), text, fontsize=11)
            pdf.save(self.path)

    def auditor(self):
        return cg.CitationGroundingAuditor(self.directory, self.lock)

    def test_heading_numeric_prefix_and_cross_reference_do_not_match(self):
        for text in ['TCVN 5574:2018\n7.3.50 Wrong clause\n(26)',
                     'TCVN 5574:2018\nSee 7.3.5 for details\n(26)',
                     'TCVN 5574:2018\n7.3.5 Real clause\n(260)']:
            with self.subTest(text=text):
                self.write_pdf(text)
                self.assertFalse(self.auditor().verify_citation(real_citation(Trang_So=1))['Citation_Content_Verified'])

    def test_renamed_wrong_standard_pdf_rejected(self):
        self.write_pdf('TCVN 5575:2024\n7.3.5 Fake heading\n(26)')
        r = self.auditor().verify_citation(real_citation(Trang_So=1))
        self.assertEqual(r['Reason'], 'PDF_IDENTITY_NOT_VERIFIED')

    def test_duplicate_pdf_is_ambiguous(self):
        self.write_pdf('TCVN 5574:2018\n7.3.5 Real clause\n(26)')
        (self.path.parent/'copy TCVN 5574-2018.pdf').write_bytes(self.path.read_bytes())
        self.assertEqual(self.auditor().verify_citation(real_citation(Trang_So=1))['Reason'], 'AMBIGUOUS_PDF_PART_OR_DUPLICATE')

    def test_old_edition_in_known_gap_does_not_authorize(self):
        self.assertEqual(self.auditor().editions['TCVN 5574'], {'2018'})

    def test_contents_entry_is_not_clause_body(self):
        self.write_pdf('TCVN 5574:2018\n7.3.5 .............. 52\n(26)')
        r = self.auditor().verify_citation(real_citation(Trang_So=1))
        self.assertFalse(r['Citation_Content_Verified'])

    def test_missing_lock_is_configuration_error(self):
        with self.assertRaises(FileNotFoundError):
            cg.CitationGroundingAuditor(self.directory, self.directory/'absent.md')


class PDFTextIndexCacheTests(unittest.TestCase):
    def test_memory_disk_and_disabled_cache_return_identical_text(self):
        from unittest.mock import patch
        import pdf_text_index as index
        import pymupdf
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'PDF_TEXT_INDEX_CACHE_DIR': folder}):
            path = Path(folder)/'fixture.pdf'
            with pymupdf.open() as doc:
                doc.new_page().insert_text((30, 40), 'Original evidence')
                doc.save(path)
            with index.PDFTextIndex(path) as pdf:
                original = pdf.text(0)
                cache = pdf.path
            index._MEMORY.clear()
            with patch.object(pymupdf, 'open', side_effect=AssertionError('warm cache re-extracted PDF')):
                with index.PDFTextIndex(path) as pdf:
                    self.assertEqual(pdf.text(0), original)
            index._MEMORY.clear()
            cache.write_text('{broken', encoding='utf-8')
            with index.PDFTextIndex(path) as pdf:
                self.assertEqual(pdf.text(0), original)
            index._MEMORY.clear()
            with patch.dict('os.environ', {'PDF_TEXT_INDEX_CACHE_DIR': str(path)}):
                with index.PDFTextIndex(path) as pdf:
                    self.assertEqual(pdf.text(0), original)

    def test_source_hash_invalidates_same_size_same_mtime_and_missing_source(self):
        import os
        import pdf_text_index as index
        import pymupdf
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'PDF_TEXT_INDEX_CACHE_DIR': folder}):
            path = Path(folder)/'fixture.pdf'
            with pymupdf.open() as doc:
                doc.new_page().insert_text((30, 40), 'Alpha evidence')
                doc.save(path)
            with index.PDFTextIndex(path) as pdf:
                before = pdf.sha256
                self.assertIn('Alpha', pdf.text(0))
            stat = path.stat()
            raw = path.read_bytes()
            changed = raw.replace(b'416c706861', b'4f6d656761')  # Alpha -> Omega, equal length.
            self.assertNotEqual(raw, changed)
            path.write_bytes(changed)
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            with index.PDFTextIndex(path) as pdf:
                self.assertNotEqual(pdf.sha256, before)
                self.assertIn('Omega', pdf.text(0))
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                index.PDFTextIndex(path)


class InputProvenanceTests(unittest.TestCase):
    def test_complete_audit_trail(self):
        r = pg.audit_inputs({'Inputs': {'gamma_II': 18.5}, 'Provenance': [provenance()]})
        self.assertTrue(r['allowed'])
        self.assertEqual(r['coverage_percent'], 100)

    def test_missing_sources_block_every_input_category(self):
        values = {'load': 250, 'concrete': 'B30', 'steel': 'CB400-V',
                  'SPT': 8, 'c': 12, 'phi': 20, 'b': 300, 'custom_factor': 1.1}
        r = pg.audit_inputs(values)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual({v['Parameter'] for v in r['violations']}, set(values))
        self.assertEqual(r['anchored_parameters'], 0)

    def test_inline_provenance(self):
        r = pg.audit_inputs({'gamma_II': {'Value': 18.5, 'Unit': 'kN/m3', 'Provenance': provenance()}})
        self.assertTrue(r['allowed'])

    def test_nested_layers_bind_exact_paths(self):
        data = {'soil': {'layers': [{'phi': 20}, {'phi': 30}]}}
        records = [provenance('soil.layers[0].phi', 20, Unit='deg'), provenance('soil.layers[1].phi', 30, Unit='deg')]
        self.assertTrue(pg.audit_inputs(data, records)['allowed'])
        self.assertFalse(pg.audit_inputs(data, [provenance('phi', 20)])['allowed'])

    def test_missing_fields_invalid_category_and_unverified_flags(self):
        for field in pg.FIELDS:
            record = provenance()
            del record[field]
            with self.subTest(field=field):
                self.assertFalse(pg.audit_inputs({'gamma_II': 18.5}, [record])['allowed'])
        for changes in [{'Verified': False}, {'Verified': 'true'}, {'Verified': 1},
                        {'Source_Type': 'AI_GUESSED'}, {'Source_Ref': 'unknown'}, {'Unit': ''}]:
            with self.subTest(changes=changes):
                self.assertFalse(pg.audit_inputs({'gamma_II': 18.5}, [provenance(**changes)])['allowed'])

    def test_value_unit_and_parameter_mismatches(self):
        for record in [provenance(value=19), provenance(value='18.5'), provenance(value=True),
                       provenance(name='gamma'), provenance(Unit='kg/m3')]:
            data = {'gamma_II': {'Value': 18.5, 'Unit': 'kN/m3'}}
            with self.subTest(record=record):
                self.assertFalse(pg.audit_inputs(data, [record])['allowed'])

    def test_zero_is_anchored_not_missing(self):
        self.assertTrue(pg.audit_inputs({'c': 0}, [provenance('c', 0, Unit='kPa')])['allowed'])

    def test_nonfinite_or_missing_values_blocked(self):
        for value in [float('nan'), float('inf'), None, 'unknown']:
            with self.subTest(value=value):
                self.assertFalse(pg.audit_inputs({'c': value}, [provenance('c', value)])['allowed'])

    def test_duplicates_orphans_and_empty_inputs_blocked(self):
        for values, records in [({'gamma_II': 18.5}, [provenance(), provenance()]),
                                ({'gamma_II': 18.5}, [provenance(), provenance('unused')]), ({}, [])]:
            with self.subTest(values=values, records=records):
                self.assertFalse(pg.audit_inputs(values, records)['allowed'])

    def test_hidden_parameters_in_envelope_or_value_wrapper_blocked(self):
        data = {'Inputs': {'gamma_II': 18.5}, 'Provenance': [provenance()], 'hidden_load': 500}
        self.assertFalse(pg.audit_inputs(data)['allowed'])
        wrapped = {'gamma_II': {'Value': 18.5, 'Provenance': provenance(), 'hidden_load': 500}}
        r = pg.audit_inputs(wrapped)
        self.assertFalse(r['allowed'])
        self.assertIn('gamma_II.hidden_load', [v['Parameter'] for v in r['violations']])

    def test_empty_nested_inputs_and_path_collisions_cannot_bypass_guard(self):
        for value in [{}, []]:
            self.assertFalse(pg.audit_inputs({'soil': value})['allowed'])
        with self.assertRaises(ValueError):
            pg.audit_inputs({'soil.c': 12, 'soil': {'c': 15}})

    def test_malformed_source_category_is_structured_failure(self):
        r = pg.audit_inputs({'gamma_II': 18.5}, [provenance(Source_Type=['DOCUMENT_EXTRACTED'])])
        self.assertFalse(r['allowed'])

    def test_required_parameters_cannot_hide_other_unanchored_inputs(self):
        r = pg.audit_inputs({'gamma_II': 18.5, 'hidden_load': 500}, [provenance()], required_parameters=['gamma_II', 'b'])
        self.assertEqual({v['Code'] for v in r['violations']}, {'MISSING_INPUT', 'UNANCHORED_VALUE'})

    def test_engineer_assumption_remains_explicit(self):
        r = pg.audit_inputs({'gamma_II': 18.5}, [provenance(Source_Type='ENGINEER_ASSUMED', Source_Ref='Engineer decision ENG-001')])
        self.assertTrue(r['allowed'])
        self.assertEqual(r['engineer_assumed_parameters'], ['gamma_II'])

    def test_standard_defaults_grounded_by_companion_tool(self):
        auditor = cg.CitationGroundingAuditor()
        record = provenance(Source_Type='STANDARDS_DEFAULT', Citation=real_citation())
        self.assertTrue(pg.audit_inputs({'gamma_II': 18.5}, [record], citation_auditor=auditor)['allowed'])
        record['Citation']['Dieu_Bang_Muc'] = 'Điều 99.99'
        self.assertFalse(pg.audit_inputs({'gamma_II': 18.5}, [record], citation_auditor=auditor)['allowed'])

    def test_guard_blocks_call_and_includes_calculator_defaults(self):
        called = []
        def calculator(load, factor=1.1):
            called.append(True)
            return load*factor
        with self.assertRaises(pg.UnanchoredInputError):
            pg.guarded_calculate(calculator, {'load': 10}, [provenance('load', 10, Unit='kN')])
        self.assertEqual(called, [])
        result = pg.guarded_calculate(calculator, {'load': 10},
            [provenance('load', 10, Unit='kN'), provenance('factor', 1.1, Unit='1')])
        self.assertEqual(result, 11)
        self.assertEqual(called, [True])

    def test_require_provenance_raises_with_audit_details(self):
        with self.assertRaises(pg.UnanchoredInputError) as raised:
            pg.require_provenance({'load': 10})
        self.assertEqual(raised.exception.audit['violations'][0]['Code'], 'UNANCHORED_VALUE')


class CitationStandardizationTests(unittest.TestCase):
    fields = {'Ma_Tieu_Chuan', 'Nam_Ban_Hanh', 'Dieu_Bang_Muc', 'Ten_Bang_Hinh', 'Trang_So', 'Trich_Yeu'}

    def test_legacy_string_and_dict_use_one_normalizer(self):
        c = cg.normalize_citation('TCVN 5574:2018 Điều 8.1.2')
        self.assertTrue(self.fields <= c.keys())
        self.assertEqual((c['Ma_Tieu_Chuan'], c['Nam_Ban_Hanh'], c['Dieu_Bang_Muc']),
                         ('TCVN 5574', '2018', 'Điều 8.1.2'))
        self.assertEqual(c['Trang_So'], '')
        self.assertEqual(c['Citation_Status'], 'UNVERIFIED')
        self.assertFalse(c['Citation_Content_Verified'])
        original = real_citation(Citation_Content_Verified=True)
        before = copy.deepcopy(original)
        c = cg.normalize_citation(original)
        self.assertEqual(original, before)
        self.assertEqual(c['Citation_Status'], 'SCHEMA_COMPLETE')
        self.assertFalse(c['Citation_Content_Verified'])

    def test_explicit_old_year_not_silently_upgraded(self):
        c = cg.normalize_citation('TCVN 5574:2012 Điều 8.1.2')
        self.assertEqual(c['Nam_Ban_Hanh'], '2012')
        self.assertTrue(c['Citation_Version_Conflict'])

    def test_inferred_year_never_becomes_pdf_evidence(self):
        c = cg.normalize_citation(dict(real_citation(), Nam_Ban_Hanh=''))
        self.assertEqual(c['Nam_Ban_Hanh'], '2018')
        self.assertEqual(c['Citation_Status'], 'UNVERIFIED')
        c = cg.normalize_citation(c)
        self.assertEqual(c['Citation_Status'], 'UNVERIFIED')
        self.assertFalse(cg.CitationGroundingAuditor().verify_citation(c)['Citation_Content_Verified'])

    def test_international_editions_and_unknown_locators(self):
        for text, code, year in [('ACI 347-04', 'ACI 347', '2004'), ('Bowles (1997)', 'Bowles', '1997'),
                                 ('EN 1993-1-1', 'EN 1993-1-1', '')]:
            with self.subTest(text=text):
                c = cg.normalize_citation(text)
                self.assertEqual((c['Ma_Tieu_Chuan'], c['Nam_Ban_Hanh']), (code, year))
                self.assertEqual(c['Trang_So'], '')
                self.assertFalse(c['Citation_Content_Verified'])

    def test_project_imports_ssot_without_local_duplicate(self):
        import ast
        p = ROOT.parent/'01_Projects/16.BPTC Q12/02_Calculation_Models/calc_hoist_sunrise_q12.py'
        tree = ast.parse(p.read_text(encoding='utf-8'))
        self.assertFalse(any(isinstance(n, ast.FunctionDef) and n.name == 'normalize_citation' for n in tree.body))
        self.assertTrue(any(isinstance(n, ast.ImportFrom) and n.module == 'citation_grounding_auditor'
                            and any(alias.name == 'normalize_citation' for alias in n.names) for n in tree.body))

    def module(self, relative):
        path = ROOT/'skills'/relative
        name = '_citation_test_'+path.stem
        if name not in sys.modules:
            sys.path.insert(0, str(path.parent))
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        return sys.modules[name]

    def check_logs(self, result):
        logs = result['Calculation_Logs']
        self.assertTrue(logs)
        for log in logs:
            self.assertTrue(self.fields <= log['Citation'].keys(), log)
            self.assertFalse(log['Citation']['Citation_Content_Verified'])
            for citation in log.get('Supporting_Citations', []):
                self.assertTrue(self.fields <= citation.keys())
                self.assertEqual(citation['Citation_Status'], 'UNVERIFIED')

    def test_spt_clay_and_sand_keep_their_real_sources(self):
        module = self.module('SKILL_GEOTECH/calculators/calc_spt_correlations.py')
        for soil in ['sand_medium', 'clay_soft']:
            result = module.correlate_spt(10, soil_class=soil)
            self.check_logs(result)
            self.assertTrue(all(log['Supporting_Citations'][0]['Nam_Ban_Hanh'] == '2022'
                                for log in result['Calculation_Logs']))
            self.assertIn(result['Calculation_Logs'][0]['Citation']['Ma_Tieu_Chuan'], ['Bowles', 'Stroud'])

    def test_base_heave_logs_keep_method_and_normative_context(self):
        module = self.module('SKILL_GEOTECH/calculators/calc_base_heave.py')
        result = module.calc_base_heave({'B_m': 20, 'L_m': 30, 'H_exc_m': 5, 'Su_kpa': 30},
            [{'id': 'L1', 'top_depth': 0, 'bottom_depth': -20, 'gamma_unsat': 18, 'gamma_sat': 19}])
        self.check_logs(result)
        self.assertEqual({c['Ma_Tieu_Chuan'] for c in result['Calculation_Logs'][0]['Supporting_Citations']},
                         {'TCVN 9362', 'TCVN 10304'})
        self.assertIn('Terzaghi', result['Standard_Method'])

    def test_formwork_design_and_optimizer_logs(self):
        module = self.module('SKILL_TEMPWORKS/calculators/calc_formwork_slab.py')
        self.check_logs(module.calc_slab_formwork())
        self.check_logs(module.SlabFormworkCalculator(200, 5, 'B25', timber_spacing=[600]).optimize())

    def test_shoring_acrow_and_ringlock_logs(self):
        module = self.module('SKILL_TEMPWORKS/calculators/calc_shoring_system.py')
        for kind in ['acrow', 'ringlock', 'tower']:
            result = module.ShoringSystemDesigner(3, 5, kind).design().to_dict()
            self.check_logs(result)
            self.assertTrue(any(c['Ma_Tieu_Chuan'] == 'TCVN 5575' for c in result['Calculation_Logs'][0]['Supporting_Citations']))


class PolicyProvenanceTests(unittest.TestCase):
    def test_valid_trail_approves_and_missing_trail_does_not(self):
        from policy_engine import decide_eta
        audit = pg.audit_inputs({'gamma_II': 18.5}, [provenance()])
        self.assertTrue(decide_eta(.8, audit).is_approved)
        legacy = decide_eta(.8)
        self.assertTrue(legacy.is_safe)
        self.assertFalse(legacy.is_approved)
        self.assertIn('INPUT_PROVENANCE_NOT_PROVIDED', legacy.input_risk_warnings)

    def test_unanchored_values_cannot_be_approved_by_eta(self):
        from policy_engine import decide_eta
        audit = pg.audit_inputs({'load': 10})
        result = decide_eta({'eta': .6, 'Input_Provenance_Audit': audit})
        self.assertFalse(result.is_approved)
        self.assertEqual(result.input_provenance_status, 'RISK')
        self.assertIn('RỦI RO ĐẦU VÀO', result.message)

    def test_global_assumption_flag_and_bare_pass_cannot_bypass(self):
        from policy_engine import decide_eta
        for audit in [{'status': 'PASS'}, {'status': 'PASS', 'UNANCHORED_VALUES': ['load'], 'ENGINEER_ASSUMED': True}]:
            self.assertFalse(decide_eta(.8, audit).is_approved)

    def test_explicit_engineer_assumption_preserves_transparency(self):
        from policy_engine import decide_eta
        audit = pg.audit_inputs({'gamma_II': 18.5}, [provenance(Source_Type='ENGINEER_ASSUMED', Source_Ref='ENG-001')])
        result = decide_eta(.8, audit)
        self.assertTrue(result.is_approved)
        self.assertEqual(result.input_provenance_status, 'ENGINEER_ASSUMED')
        self.assertTrue(result.input_risk_warnings)

    def test_actual_input_value_is_rebound_and_repair_never_waived(self):
        from policy_engine import decide_eta, Action, decide_eta_with_standards
        audit = pg.audit_inputs({'gamma_II': 18.5}, [provenance()])
        result = decide_eta(.8, audit, inputs={'gamma_II': 20})
        self.assertFalse(result.is_approved)
        self.assertEqual(result.input_provenance_status, 'RISK')
        result = decide_eta_with_standards(1.2, input_provenance_audit=audit)
        self.assertEqual(result.action, Action.REPAIR)
        self.assertFalse(result.is_approved)


class CLITests(unittest.TestCase):
    def test_json_cli_exit_codes_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input.json'
            cases = [('citation_grounding_auditor.py', {'Citation': real_citation()}, 0),
                     ('citation_grounding_auditor.py', {'Citation': real_citation(Dieu_Bang_Muc='Điều 99.99')}, 1),
                     ('input_provenance_guard.py', {'Inputs': {'gamma_II': 18.5}, 'Provenance': [provenance()]}, 0),
                     ('input_provenance_guard.py', {'Inputs': {'gamma_II': 18.5}}, 1)]
            for script, data, code in cases:
                with self.subTest(script=script, code=code):
                    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                    before = path.read_bytes()
                    process = subprocess.run([sys.executable, str(ROOT/'tools'/script), '--input', str(path)],
                                             capture_output=True, text=True, encoding='utf-8', timeout=60)
                    self.assertEqual(process.returncode, code, process.stderr)
                    result = json.loads(process.stdout)
                    self.assertIn(result['status'], ('PASS', 'BLOCKED'))
                    self.assertEqual(path.read_bytes(), before)

    def test_corrupt_input_cli_exits_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            path.write_text('{bad', encoding='utf-8')
            process = subprocess.run([sys.executable, str(ROOT/'tools/input_provenance_guard.py'), '-i', str(path)],
                                     capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertEqual(process.returncode, 2)
            self.assertFalse(json.loads(process.stdout)['allowed'])

    def test_nonfinite_json_cli_is_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            path.write_text('{"load": NaN}', encoding='utf-8')
            process = subprocess.run([sys.executable, str(ROOT/'tools/input_provenance_guard.py'), '-i', str(path)],
                                     capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertEqual(process.returncode, 2)
            self.assertFalse(json.loads(process.stdout)['allowed'])

    def test_registered_as_suite_23(self):
        spec = importlib.util.spec_from_file_location('suite_registry', ROOT/'tests/run_all_tests.py')
        # Read/compile the registry without its legacy stdout replacement.
        namespace = {'__file__': spec.origin, '__name__': 'suite_registry'}
        source = Path(spec.origin).read_text(encoding='utf-8').replace("if sys.platform == 'win32':", 'if False:')
        exec(compile(source, spec.origin, 'exec'), namespace)
        suites = [suite for suite in namespace['SUITES'] if suite[0].startswith('23.')]
        self.assertEqual(len(suites), 1)
        self.assertEqual(Path(suites[0][1][1]).resolve(), Path(__file__).resolve())


if __name__ == '__main__':
    unittest.main(verbosity=2)
