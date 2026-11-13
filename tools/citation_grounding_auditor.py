#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ground citations in local normative PDFs, never in model memory.

API: CitationGroundingAuditor().audit(data), .audit_file(path), .verify_citation(citation).
CLI: python citation_grounding_auditor.py --input ABS_PATH [--output ABS_PATH]
Exit 0 = all citations grounded; 1 = blocked; 2 = input/configuration error.
Trang_So is a one-based physical PDF page; the search window is at most +/-2.
Edition eligibility is repository policy from STANDARDS_LOCK, not a live legal opinion.
Text matching establishes location/content presence, not engineering applicability.
"""
import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SKILLS = Path(__file__).resolve().parents[1] / 'skills'
DEFAULT_STANDARDS = SKILLS / 'Design_Evaluation' / 'standards'
DEFAULT_LOCK = SKILLS / 'STANDARDS_LOCK.md'
STANDARD_RE = re.compile(r'\b(TCVN|QCVN)\s*(\d+(?:-\d{1,2}(?!\d))?)\s*(?:[:\-]\s*((?:19|20)\d{2}))?(?:\s*/\s*((?!TCVN\b|QCVN\b)[A-ZĐ]+))?', re.I)
REFERENCE_RE = re.compile(
    r'(?P<kind>điều|mục|bảng|hình|phụ\s+lục|công\s+thức|formula|table|clause|figure|annex|§|CT\.)'
    r'\s*\(?\s*(?P<number>[A-Z](?:\.\d+)*|\d+(?:\.\d+)*)\s*\)?(?![\w.])', re.I)


def normalized(text):
    text = unicodedata.normalize('NFKC', str(text)).lower().replace('đ', 'd')
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip()


def standard_identity(text):
    match = STANDARD_RE.search(str(text))
    if not match:
        return None
    return f'{match[1].upper()} {match[2]}', match[3]


def _locked_citation_years(lock_path=DEFAULT_LOCK):
    """Only the CURRENT column of the normative table may supply missing editions."""
    lock = Path(lock_path).read_text(encoding='utf-8-sig')
    normative = lock.split('## 1.', 1)[1].split('## 2.', 1)[0]
    years = {}
    for row in normative.splitlines():
        cells = row.split('|')
        if len(cells) > 3:
            for match in STANDARD_RE.finditer(cells[2]):
                if match[3]:
                    years[f'{match[1].upper()} {match[2]}'] = match[3]
    return years


def normalize_citation(citation, *, lock_path=DEFAULT_LOCK, infer_year=True):
    """SSOT six-field schema for legacy strings/dicts; never certifies PDF content.

    Unknown page/clause/year remains empty and UNVERIFIED. Inferred lock editions
    are explicitly marked, and never substitute for PDF edition evidence.
    International references retain their actual method, not a TCVN relabeling.
    """
    if isinstance(citation, dict):
        original = copy.deepcopy(citation)
    else:
        text = str(citation or '').strip()
        original = {'Citation_Original': text, 'Trich_Yeu': text}
        match = STANDARD_RE.search(text)
        if match:
            original.update(Ma_Tieu_Chuan=match[0], Nam_Ban_Hanh=match[3] or '')
            tail = text[match.end():].strip()
            page = re.search(r'(?:trang|page|tr\.)\s*[:.]?\s*(\d+(?:-\d+)?)', tail, re.I)
            original['Trang_So'] = page[1] if page else ''
            original['Dieu_Bang_Muc'] = tail[:page.start() if page else len(tail)].strip(' —–-|;')
        else:
            # Explicit publication notations used by the core calculators.
            aci = re.match(r'(ACI\s+\d+(?:\.\d+R?)?)-(\d{2}|\d{4})\b\s*(.*)', text, re.I)
            publication = re.match(r'(.+?)\s*\(?((?:19|20)\d{2})\)?(?:\s*[-—:]\s*|\s+)?(.*)$', text)
            if aci:
                year = aci[2] if len(aci[2]) == 4 else ('19' if int(aci[2]) >= 70 else '20')+aci[2]
                original.update(Ma_Tieu_Chuan=aci[1].upper(), Nam_Ban_Hanh=year, Dieu_Bang_Muc=aci[3])
            elif publication and not text.upper().startswith('EN '):
                original.update(Ma_Tieu_Chuan=publication[1].strip(), Nam_Ban_Hanh=publication[2], Dieu_Bang_Muc=publication[3])
            else:
                original['Ma_Tieu_Chuan'] = text
    aliases = {
        'Ma_Tieu_Chuan': ('Ma_Tieu_Chuan', 'Ma_TC', 'standard', 'code'),
        'Nam_Ban_Hanh': ('Nam_Ban_Hanh', 'year'),
        'Dieu_Bang_Muc': ('Dieu_Bang_Muc', 'Dieu_Muc', 'clause'),
        'Ten_Bang_Hinh': ('Ten_Bang_Hinh', 'Bang_Hinh', 'table_title'),
        'Trang_So': ('Trang_So', 'Trang', 'page'),
        'Trich_Yeu': ('Trich_Yeu', 'summary'),
    }
    result = dict(original)
    for key, choices in aliases.items():
        result[key] = next((original[k] for k in choices if k in original and original[k] is not None), '')
    identity = standard_identity(result['Ma_Tieu_Chuan'])
    if len(list(STANDARD_RE.finditer(str(result['Ma_Tieu_Chuan'])))) > 1:
        result['_multiple_standards'] = True
    if identity:
        result['Ma_Tieu_Chuan'] = identity[0]
        if not result['Nam_Ban_Hanh']:
            result['Nam_Ban_Hanh'] = identity[1] or ''
        elif identity[1] and str(result['Nam_Ban_Hanh']) != identity[1]:
            result['_edition_conflict'] = True
    year = str(result['Nam_Ban_Hanh']).strip()
    code = str(result['Ma_Tieu_Chuan']).strip()
    locked = _locked_citation_years(lock_path).get(code, '')
    source = original.get('Citation_Version_Source', 'citation_source' if year else 'UNVERIFIED')
    if not year and locked and infer_year:
        year, source = locked, '.agents/skills/STANDARDS_LOCK.md#1'
    result['Nam_Ban_Hanh'] = year
    missing = [key for key in ('Ma_Tieu_Chuan', 'Nam_Ban_Hanh', 'Dieu_Bang_Muc', 'Trang_So', 'Trich_Yeu') if not result[key]]
    conflict = bool(result.get('_edition_conflict') or (locked and year and year != locked))
    inferred = source == '.agents/skills/STANDARDS_LOCK.md#1'
    result.update(Ma_TC=f'{code}:{year}' if code and year else code,
                  Dieu_Muc=result['Dieu_Bang_Muc'], Bang_Hinh=result['Ten_Bang_Hinh'], Trang=result['Trang_So'],
                  Citation_Status='UNVERIFIED' if missing or conflict or inferred else 'SCHEMA_COMPLETE',
                  Citation_Version_Source=source, Citation_Content_Verified=False,
                  Citation_Missing_Fields=missing, Citation_Version_Conflict=conflict,
                  Table_Reference_Status='PROVIDED' if result['Ten_Bang_Hinh'] else 'NOT_PROVIDED')
    for key in ('Verified_Evidence_Snippet', 'Verification_Evidence', 'Verified_PDF_Page', 'Page_Offset', 'PDF_Path', 'PDF_SHA256'):
        result.pop(key, None)
    return result


def canonical_citation(citation):
    """Compatibility alias; PDF verification requires an explicitly supplied year."""
    return normalize_citation(citation, infer_year=False)


def normalize_output_citations(value):
    """Normalize every nested Citation, preserving output values and legacy keys."""
    if isinstance(value, list):
        return [normalize_output_citations(item) for item in value]
    if isinstance(value, dict):
        return {key: ([normalize_citation(c) for c in item] if isinstance(item, list) else normalize_citation(item))
                if key.lower() in ('citation', 'citations', 'supporting_citations')
                else normalize_output_citations(item) for key, item in value.items()}
    return value


def text_citations(text):
    """Keep each occurrence, including incomplete citations (which must fail closed)."""
    matches = list(STANDARD_RE.finditer(text))
    found = []
    for i, match in enumerate(matches):
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        # Do not bind a citation to a different paragraph's page or clause.
        tail = text[match.end():end].split('\n\n', 1)[0]
        first_ref = REFERENCE_RE.search(tail)
        page = re.search(r'(?:trang|page|tr\.)\s*[:.]?\s*(\d+)(?!\d)', tail, re.I)
        locator = tail[first_ref.start():page.start() if page else len(tail)].strip(' —–-|;') if first_ref else ''
        found.append({'Ma_Tieu_Chuan': f'{match[1].upper()} {match[2]}',
                      'Nam_Ban_Hanh': match[3] or '', 'Dieu_Bang_Muc': locator,
                      'Ten_Bang_Hinh': '', 'Trang_So': page[1] if page else '',
                      'Trich_Yeu': '', '_text': text[match.start():match.end()]+tail})
    return found


def collect_citations(data, path='$'):
    """Return (JSON path, citation); handle arbitrary nested logs and Citation lists."""
    found = []
    if isinstance(data, dict):
        if any(key in data for key in ('Ma_Tieu_Chuan', 'Ma_TC')):
            found.append((path, data))
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    if key.lower() in ('citation', 'citations'):
                        found.extend(collect_citations({key: value}, path))
                    else:
                        found.extend(collect_citations(value, f'{path}.{key}'))
        else:
            for key, value in data.items():
                if key.lower() in ('citation', 'citations') and isinstance(value, dict):
                    if any(k in value for k in ('Ma_Tieu_Chuan', 'Ma_TC')):
                        found.extend(collect_citations(value, f'{path}.{key}'))
                    else:
                        # Invalid Citation objects must not disappear from the audit.
                        found.append((f'{path}.{key}', value))
                elif key.lower() in ('citation', 'citations') and isinstance(value, list):
                    if not value:
                        found.append((f'{path}.{key}', {}))
                    for i, citation in enumerate(value):
                        item_path = f'{path}.{key}[{i}]'
                        if isinstance(citation, dict):
                            found.append((item_path, citation))
                        elif isinstance(citation, str):
                            extracted = text_citations(citation)
                            found.extend((item_path, item) for item in extracted or [{}])
                        else:
                            found.append((item_path, {}))
                elif key.lower() in ('citation', 'citations') and value is None:
                    found.append((f'{path}.{key}', {}))
                elif key.lower() in ('citation', 'citations'):
                    extracted = text_citations(value) if isinstance(value, str) else []
                    found.extend((f'{path}.{key}', citation) for citation in extracted or [{}])
                else:
                    found.extend(collect_citations(value, f'{path}.{key}'))
    elif isinstance(data, list):
        for i, value in enumerate(data):
            found.extend(collect_citations(value, f'{path}[{i}]'))
    elif isinstance(data, str):
        found.extend((path, citation) for citation in text_citations(data))
    return found


def load_report(path):
    path = Path(path).resolve()
    if path.suffix.lower() == '.json':
        return json.loads(path.read_text(encoding='utf-8-sig'))
    if path.suffix.lower() in ('.md', '.txt', '.markdown'):
        return path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() in ('.doc', '.docx'):
        from doc_reader import read_docx
        result = read_docx(path)
        if result['status'] == 'ERROR':
            raise ValueError(result['error'])
        if result['metadata'].get('embedded_objects') or (path.suffix.lower() == '.doc' and result['metadata'].get('embedded_images')):
            raise ValueError('Word contains unsupported embedded content; cannot audit every citation')
        # Include headers, footers and text boxes, not just python-docx Paragraph.text.
        if path.suffix.lower() == '.docx':
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(path) as archive:
                parts = [name for name in archive.namelist() if re.fullmatch(
                    r'word/(?:document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml', name)]
                texts = []
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                for name in parts:
                    root = ET.fromstring(archive.read(name))
                    texts.extend(''.join(p.itertext()) for p in root.findall('.//w:p', ns))
            return '\n\n'.join(texts)
        return result['raw_text']
    raise ValueError(f'Unsupported report format: {path.suffix}')


class CitationGroundingAuditor:
    def __init__(self, standards_dir=DEFAULT_STANDARDS, lock_path=DEFAULT_LOCK, page_window=2):
        if type(page_window) is not int or not 0 <= page_window <= 2:
            raise ValueError('page_window must be an integer from 0 to 2')
        self.standards_dir = Path(standards_dir).resolve()
        self.lock_path = Path(lock_path).resolve()
        self.page_window = page_window
        lock = self.lock_path.read_text(encoding='utf-8-sig')
        self.lock_sha256 = hashlib.sha256(self.lock_path.read_bytes()).hexdigest()
        self.editions, self.amendments = {}, {}
        # Only the normative table's CURRENT column authorizes editions. Never read old
        # editions, Known Gap rows or examples as current permissions.
        in_table = False
        for line in lock.splitlines():
            if line.startswith('## 1.'):
                in_table = True
            elif in_table and line.startswith('## '):
                break
            if not in_table or not line.lstrip().startswith('|'):
                continue
            cells = line.split('|')
            if len(cells) < 5:
                continue
            for match in STANDARD_RE.finditer(cells[2]):
                if match[3]:
                    key = f'{match[1].upper()} {match[2]}'
                    self.editions.setdefault(key, set()).add(match[3])
                    if re.search(r'Sửa\s+đổi', cells[2], re.I):
                        self.amendments[key] = cells[2].strip()
        if not self.editions:
            raise ValueError('No current TCVN/QCVN editions found in normative lock table')

    def _pdf_candidates(self, code, year):
        family = code.split()[0]
        found = []
        for path in sorted((self.standards_dir / family).glob('*.pdf')):
            if re.search(r'\d+\s*TK\b', path.name, re.I):
                continue
            identity = standard_identity(path.name)
            if identity == (code, year):
                found.append(path)
        return found

    @staticmethod
    def _reference_pattern(reference):
        kind, number = reference['kind'], reference['number']
        kind = normalized(kind)
        token = re.escape(number).replace(r'\.', r'\s*\.\s*')
        end = r'(?![\w.]|\s*\.\s*\d)'
        if kind in ('cong thuc', 'formula', 'ct.'):
            return re.compile(r'(?<!\w)\(\s*'+token+r'\s*\)'+end, re.I | re.M)
        if kind in ('dieu', 'muc', 'clause', '§'):
            return re.compile(r'^\s*(?:(?:điều|mục|clause|§)\s*)?'+token+end+r'(?:[ \t]|$)', re.I | re.M)
        labels = {'bang': r'(?:bảng|table)', 'table': r'(?:bảng|table)',
                  'hinh': r'(?:hình|figure)', 'figure': r'(?:hình|figure)',
                  'phu luc': r'(?:phụ\s+lục|annex)', 'annex': r'(?:phụ\s+lục|annex)'}
        return re.compile(r'^\s*'+labels[kind]+r'\s+'+token+end, re.I | re.M)

    def verify_citation(self, citation):
        c = normalize_citation(citation, lock_path=self.lock_path, infer_year=False)
        result = {**copy.deepcopy(citation), **c, 'Citation_Content_Verified': False,
                  'Verified_Evidence_Snippet': '', 'Verification_Evidence': [],
                  'Edition_Policy': 'STANDARDS_LOCK', 'Lock_SHA256': self.lock_sha256}
        for key in ('Verified_PDF_Page', 'Page_Offset', 'Searched_PDF_Pages', 'PDF_Path', 'PDF_SHA256'):
            result.pop(key, None)

        def fail(reason, hallucination=False):
            result.update(Citation_Status='UNVERIFIED', Reason=reason,
                          Warning='CITATION_GROUNDING_MISMATCH',
                          Error_Code='HALLUCINATION_DETECTED' if hallucination else 'CITATION_GROUNDING_MISMATCH')
            return result

        code, year = str(c['Ma_Tieu_Chuan']), str(c['Nam_Ban_Hanh'])
        if c.get('Citation_Version_Source') == '.agents/skills/STANDARDS_LOCK.md#1':
            return fail('INFERRED_EDITION_NOT_SOURCE_EVIDENCE')
        if c.get('_multiple_standards'):
            return fail('MULTIPLE_STANDARDS_IN_ONE_CITATION')
        if c.get('_edition_conflict'):
            return fail('CONFLICTING_EDITION')
        if code not in self.editions:
            return fail('STANDARD_NOT_IN_LOCK')
        if year not in self.editions[code]:
            return fail('EDITION_NOT_CURRENT_IN_LOCK')
        if code in self.amendments:
            # Amendment identity cannot be inferred from a base-edition citation.
            return fail('COMPOSITE_EDITION_REQUIRES_AMENDMENT_VERIFICATION')
        page = c['Trang_So']
        if isinstance(page, bool) or not re.fullmatch(r'[1-9]\d*', str(page)):
            return fail('MISSING_OR_INVALID_PAGE')
        page = int(page)
        clause = str(c['Dieu_Bang_Muc']).strip()
        title = str(c['Ten_Bang_Hinh']).strip()
        refs = list(REFERENCE_RE.finditer(clause))
        if not refs and re.fullmatch(r'\d+(?:\.\d+)+', clause):
            refs = list(REFERENCE_RE.finditer('Điều '+clause))
        if not refs:
            return fail('MISSING_OR_UNSUPPORTED_LOCATOR')
        remainder = REFERENCE_RE.sub('', clause)
        if re.search(r'\d', remainder) and not re.fullmatch(r'\d+(?:\.\d+)+', clause):
            return fail('UNPARSED_LOCATOR_NUMBERS')
        title_refs = list(REFERENCE_RE.finditer(title))
        patterns = [self._reference_pattern(ref) for ref in refs + title_refs]
        # A descriptive title is additional required evidence, not an alternative to clause matching.
        title_remainder = REFERENCE_RE.sub('', title).strip(' :-–—/()')
        candidates = self._pdf_candidates(code, year)
        if not candidates:
            return fail('PDF_NOT_FOUND')
        if len(candidates) != 1:
            return fail('AMBIGUOUS_PDF_PART_OR_DUPLICATE')
        path = candidates[0]
        try:
            import pymupdf
            with pymupdf.open(path) as pdf:
                if pdf.needs_pass:
                    return fail('PDF_PASSWORD_REQUIRED')
                if page > len(pdf):
                    return fail('PAGE_OUT_OF_RANGE')
                # Validate file contents as well as filename; reject renamed PDFs.
                identity_text = '\n'.join(pdf[i].get_text() for i in range(min(6, len(pdf))))
                identities = [standard_identity(m[0]) for m in STANDARD_RE.finditer(identity_text)]
                if (code, year) not in identities:
                    return fail('PDF_IDENTITY_NOT_VERIFIED')
                result['PDF_Path'] = str(path)
                result['PDF_SHA256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                indices = sorted(range(max(0, page-1-self.page_window), min(len(pdf), page+self.page_window)),
                                 key=lambda i: (abs(i-(page-1)), i))
                result['Searched_PDF_Pages'] = [i+1 for i in indices]
                has_text = False
                for index in indices:
                    text = unicodedata.normalize('NFKC', pdf[index].get_text())
                    has_text = has_text or bool(text.strip())
                    matches = [pattern.search(text) for pattern in patterns]
                    if not all(matches):
                        continue
                    if any(re.search(r'\.{3,}|…{2,}', text[m.start():text.find('\n', m.end())
                               if text.find('\n', m.end()) >= 0 else len(text)]) for m in matches):
                        continue  # A contents-list entry is not the clause's body.
                    if title_remainder and normalized(title_remainder) not in normalized(text):
                        continue
                    snippets = [text[max(0, match.start()-100):min(len(text), match.end()+400)].strip()
                                for match in matches]
                    result.update(Citation_Content_Verified=True, Citation_Status='VERIFIED',
                                  Verified_PDF_Page=index+1, Page_Offset=index+1-page,
                                  Verified_Evidence_Snippet='\n…\n'.join(snippets),
                                  Verification_Evidence=[{'PDF_Page': index+1, 'Matched_Text': match[0],
                                                          'Snippet': snippet} for match, snippet in zip(matches, snippets)],
                                  Reason='ALL_LOCATORS_FOUND_ON_SAME_PDF_PAGE')
                    # Ignore any caller-supplied success/error flags.
                    result.pop('Warning', None)
                    result.pop('Error_Code', None)
                    return result
                return fail('LOCATOR_OR_TITLE_NOT_FOUND' if has_text else 'PDF_TEXT_UNAVAILABLE', has_text)
        except Exception as error:
            return fail(f'PDF_READ_ERROR:{type(error).__name__}:{error}')

    def audit(self, data):
        citations = [{**self.verify_citation(c), 'Source_Path': path} for path, c in collect_citations(data)]
        verified = sum(c['Citation_Content_Verified'] is True for c in citations)
        suspicious = [c for c in citations if not c['Citation_Content_Verified']]
        return {'status': 'PASS' if citations and not suspicious else 'BLOCKED',
                'total_citations': len(citations), 'verified_citations': verified,
                'pdf_verified_percent': round(100*verified/len(citations), 2) if citations else 0.0,
                'citations': citations, 'suspicious_citations': suspicious,
                'warnings': [] if citations and not suspicious else ['CITATION_GROUNDING_MISMATCH' if citations else 'NO_CITATIONS_FOUND'],
                'verification_scope': 'Local PDF text presence and repository edition policy; not applicability or live legal status'}

    def audit_file(self, path):
        result = self.audit(load_report(path))
        result['source_file'] = str(Path(path).resolve())
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o')
    parser.add_argument('--standards-dir', default=str(DEFAULT_STANDARDS))
    parser.add_argument('--lock', default=str(DEFAULT_LOCK))
    args = parser.parse_args(argv)
    try:
        auditor = CitationGroundingAuditor(args.standards_dir, args.lock)
        result = auditor.audit_file(args.input)
        code = 0 if result['status'] == 'PASS' else 1
    except Exception as error:
        result, code = {'status': 'ERROR', 'error': f'{type(error).__name__}: {error}'}, 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        target = Path(args.output).resolve()
        if target == Path(args.input).resolve():
            parser.error('Output must not overwrite the source report')
        target.write_text(encoded, encoding='utf-8')
    print(encoded)
    return code


if __name__ == '__main__':
    sys.exit(main())
