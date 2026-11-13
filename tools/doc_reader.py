"""
doc_reader.py — Universal Engineering Document Reader v3.0
==================================================================================

Mục đích:
 Đọc Word (DOCX/DOC), PDF, Excel (XLSX/XLS/CSV), ảnh OCR và CAD (DXF/DWG)
 và chuẩn hóa thành một JSON thống nhất chứa dữ liệu kỹ thuật có cấu trúc.
 Tầng Input Intelligence — tích hợp 4 tầng thông minh:
   1. Pre-processing & Encoding Normalization (VNI/TCVN3 -> Unicode, Page Garbled Detector).
   2. Spatial & Table Context (DXF Spatial Clustering, Page-Indexed Span Map).
   3. Multi-Code Engineering NER v2.0 (Thép tổ hợp 4 số, Xà gồ Z, Cọc tròn, Sàn, Mác thép ASTM/JIS/Q345B).
   4. Truth Graph Auto-Ingestion (Đấu nối thẳng vào ingest_project_docs.py).
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from bisect import bisect_right
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Backend Detection
_PDF_BACKEND = None
_DOCX_BACKEND = None
_XLSX_BACKEND = None
_DXF_BACKEND = None
_OCR_BACKEND = None

try:
    import pdfplumber
    _PDF_BACKEND = "pdfplumber"
except ImportError:
    pass

if _PDF_BACKEND is None:
    try:
        import pymupdf
        _PDF_BACKEND = "pymupdf"
    except ImportError:
        pass

try:
    import pytesseract as _tesseract
    from pdf2image import convert_from_path as _pdf2img
    _OCR_BACKEND = "tesseract"
except ImportError:
    pass

try:
    import docx as _docx_lib
    _DOCX_BACKEND = "python-docx"
except ImportError:
    pass

try:
    import openpyxl as _openpyxl_lib
    _XLSX_BACKEND = "openpyxl"
except ImportError:
    pass

try:
    import ezdxf as _ezdxf_lib
    _DXF_BACKEND = "ezdxf"
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. TẦNG 1: VIETNAMESE LEGACY DECODER (VNI / TCVN3 -> UNICODE UTF-8)
# ─────────────────────────────────────────────────────────────────────────────

class VietnameseLegacyDecoder:
    """Giải mã các bảng mã cũ VNI-Windows và TCVN3 (ABC) trong bản vẽ CAD / PDF cũ sang Unicode chuẩn."""
    
    # Bảng ánh xạ VNI cơ bản phổ biến trong bản vẽ CAD/Thuyết minh
    VNI_MAP = {
        "Daàm": "Dầm", "daàm": "dầm", "Beâ": "Bê", "beâ": "bê", "toâng": "tông", "Toâng": "Tông",
        "Keâ": "Kể", "keâ": "kể", "ThÐ": "Thép", "thÐ": "thép", "MÆt": "Mặt", "mÆt": "mặt",
        "KÕt": "Kết", "kÕt": "kết", "cÊu": "cấu", "CÊu": "Cấu", "b»n": "bền", "B»n": "Bền",
        "hÖ": "hệ", "HÖ": "Hệ", "t¶i": "tải", "T¶i": "Tải", "träng": "trọng", "Träng": "Trọng",
    }

    @classmethod
    def decode(cls, text: str) -> str:
        if not text:
            return ""
        res = text
        # VNI heuristic replacement
        for k, v in cls.VNI_MAP.items():
            res = res.replace(k, v)
        # Sửa các cụm dấu thô phổ biến trong CAD font lỗi
        res = res.replace("CHUNG PHAÀN KEÁT CAÁU", "CHUNG PHẦN KẾT CẤU")
        res = res.replace("GHI CHUÙ", "GHI CHÚ")
        return res


# ─────────────────────────────────────────────────────────────────────────────
# 2. TẦNG 3: MULTI-CODE ENGINEERING PATTERN REGISTRY v2.0
# ─────────────────────────────────────────────────────────────────────────────

ENGINEERING_PATTERNS = {
    # Tải trọng: "tĩnh tải sàn: 3.5 kN/m2" | "q = 12.5 kN/m²" | "Solar = 0.25 kN/m2"
    "load": re.compile(
        r"""(?:
            (?P<label_vi>(?:tĩnh\s*tải|hoạt\s*tải|tải\s*trọng|tải|solar|mep|q|g|p|w|n|v|fx|fy|fz|mx|my|mz)\s*[\w\s]*)
            \s*[:=]\s*
            (?P<value_load>[+-]?\d+(?:[.,]\d+)?)\s*
            (?P<unit_load>kN/m[²2]?|kN/m|kN[.]?m|kN|T/m[²2]?|T/m|T|kg/m[²2]?|kg/m|kPa|MPa|daN/m[²2]?)
        )""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
    # Tiết diện v2.0: "300x600" | "b=300mm, h=600mm" | "H400x200x8x12" | "Z200x68x62x1.8" | "50x50x2" | "D600" | "h=120mm"
    "section": re.compile(
        r"""(?:
            (?:[bB]\s*=\s*)?(?P<b_or_full>\d{2,4})
            (?:
                \s*[xX×]\s*(?P<h_or_sub>\d{2,4})
                (?:\s*[xX×]\s*(?P<t1>\d{1,2}(?:\.\d+)?))?
                (?:\s*[xX×]\s*(?P<t2>\d{1,2}(?:\.\d+)?))?
            )?
            \s*(?:mm)?
        )""",
        re.VERBOSE,
    ),
    # Cốt thép / Cọc tròn: "4Ø25" | "6φ20" | "D1000" | "Ø800" | "As = 1520 mm²"
    "rebar_or_pile": re.compile(
        r"""(?:
            (?P<count_rb>\d+)\s*[ØøφΦd]\s*(?P<dia>\d+(?:[.,]\d+)?)
            |[ØøφΦdD](?P<pile_dia>\d{3,4})
            |As\s*=\s*(?P<as_val>\d+(?:[.,]\d+)?)\s*mm[²2]?
        )""",
        re.VERBOSE | re.IGNORECASE,
    ),
    # SPT: "N = 12 búa" | "NSPT = 20"
    "spt": re.compile(
        r"""(?:N(?:SPT)?\s*=?\s*(?P<spt_n>\d+(?:[.,]\d+)?)\s*(?:búa|blows)?)""",
        re.IGNORECASE | re.UNICODE,
    ),
    # Vật liệu v2.0: TCVN (B15-B60), Eurocode (C25/30), Thép hình/tấm (S355, Q345B, A572 Gr50, SS400, A490)
    "material": re.compile(
        r"""(?:
            (?:bê\s*tông\s*)?(?P<concrete>B(?:1[5-9]|[2-5]\d|60)|C\d{2}/\d{2})
            |(?:thép\s*(?:hình|kết\s*cấu)?\s*)?(?P<steel_struct>S(?:235|275|355|450)[A-Z0-9]*|Q345[A-Z]?|SS400|A572\s*Gr\s*50|A490)
            |(?:thép(\s*chịu\s*(?:kéo|nén|uốn|lực)?)?\s*)?(?P<steel>CB\d{3}[-–]?[VT]?|AI{1,3}|SD\d{3}|B500[ABC]|(?:Grade|Gr)\s*60)
        )""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
    # Tải trọng gió TCVN 2737:2023: "W0 = 95 daN/m2", "vùng gió II-A"
    "wind_load": re.compile(
        r"""(?:
            (?:W[0o]\s*=\s*(?P<w0_val>\d+(?:[.,]\d+)?)\s*(?P<w0_unit>daN/m[²2]?|kN/m[²2]?|kPa))
            |(?:vùng\s*(?:áp\s*lực\s*)?gió\s*(?P<wind_zone>[I|V|X]+[-–]?[A-B]?))
        )""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
    # Phần tử: "Dầm D1", "Cột C2A", "Vách V3"
    "element_label": re.compile(
        r"""(?P<elem_type>Dầm|Dam|Cột|Col|Vách|Vach|Sàn|San|Móng|Mong)\s*
            (?P<elem_id>[A-Z0-9]{1,6})""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. TẦNG 2: PAGE-INDEXED SPAN MAP & SPATIAL CLUSTERING
# ─────────────────────────────────────────────────────────────────────────────

class PageSpanMap:
    """Ánh xạ vị trí ký tự (char offset) với số trang PDF, thay thế hoàn toàn lỗi tìm ngược [::-1]."""
    def __init__(self, page_boundaries: List[Tuple[int, int, int]]):
        # List of (start_offset, end_offset, page_no)
        self.boundaries = page_boundaries

    def get_page(self, offset: int) -> Optional[int]:
        if not self.boundaries:
            return None
        # Binary search bằng bisect
        idx = bisect_right(self.boundaries, (offset, float('inf'), 0))
        if idx > 0:
            start, end, page_no = self.boundaries[idx - 1]
            if start <= offset <= end:
                return page_no
        return self.boundaries[0][2] if offset < self.boundaries[0][0] else self.boundaries[-1][2]


def _extract_engineering_data(text: str, source_hint: str = "", span_map: Optional[PageSpanMap] = None) -> Tuple[dict, list]:
    decoded_text = VietnameseLegacyDecoder.decode(text)
    loads, sections, rebars, soils, materials = [], [], [], [], []
    logs = []

    # — Loads —
    for m in ENGINEERING_PATTERNS["load"].finditer(decoded_text):
        label = (m.group("label_vi") or "").strip().rstrip(":= ").strip()
        raw_val = m.group("value_load").replace(",", ".")
        unit = m.group("unit_load")
        try:
            value = float(raw_val)
            page = span_map.get_page(m.start()) if span_map else None
            loads.append({
                "label": label or f"Tải {len(loads)+1}",
                "value": value,
                "unit": unit,
                "source_page": page,
                "source_hint": source_hint,
            })
        except ValueError:
            pass

    # — Sections v2.0 (Hỗ trợ thép hình 4 số, xà gồ Z, cọc D, sàn) —
    seen_secs = set()
    for m in ENGINEERING_PATTERNS["section"].finditer(decoded_text):
        b_str = m.group("b_or_full")
        h_str = m.group("h_or_sub")
        t1 = m.group("t1")
        t2 = m.group("t2")
        
        if not b_str:
            continue
        val1 = int(b_str)
        
        if h_str:
            val2 = int(h_str)
            if t1:
                # Thép hình tổ hợp H/I hoặc Xà gồ Z (vd H400x200x8x12)
                sec_str = f"H{val1}x{val2}x{t1}x{t2}" if t2 else f"H{val1}x{val2}x{t1}"
                key = (sec_str,)
                if key not in seen_secs:
                    seen_secs.add(key)
                    sections.append({"element": f"Thép hình {sec_str}", "profile": sec_str, "source_hint": source_hint})
            else:
                # Tiết diện BxH thông thường
                if not (50 <= val1 <= 4000 and 50 <= val2 <= 4000):
                    continue
                key = (val1, val2)
                if key in seen_secs:
                    continue
                seen_secs.add(key)
                snippet = decoded_text[max(0, m.start()-60):m.start()]
                em = ENGINEERING_PATTERNS["element_label"].search(snippet)
                element = f"{em.group('elem_type')} {em.group('elem_id')}" if em else f"CK-{len(sections)+1}"
                sections.append({"element": element, "b_mm": val1, "h_mm": val2, "source_hint": source_hint})
        else:
            # Cọc tròn hoặc chiều dày sàn đơn (vd D600, dày 150)
            prefix = decoded_text[max(0, m.start()-20):m.start()]
            if re.search(r'(?:[dDØøφΦ]|đường\s*kính)\s*$', prefix) and 200 <= val1 <= 3000:
                key = (f"D{val1}",)
                if key not in seen_secs:
                    seen_secs.add(key)
                    sections.append({"element": f"Cọc/Cấu kiện tròn D{val1}", "diameter_mm": val1, "source_hint": source_hint})
            elif re.search(r'(?:\bh\s*=|dày|day)\s*$', prefix) and 50 <= val1 <= 1000:
                key = ('thickness', val1)
                if key not in seen_secs:
                    seen_secs.add(key)
                    sections.append({'element': 'Chiều dày cấu kiện', 'thickness_mm': val1, 'source_hint': source_hint})

    # — Rebar & Piles —
    for m in ENGINEERING_PATTERNS["rebar_or_pile"].finditer(decoded_text):
        if m.group("count_rb") and m.group("dia"):
            rebars.append({
                "mark": str(len(rebars)+1),
                "count": int(m.group("count_rb")),
                "dia_mm": float(m.group("dia").replace(",", ".")),
                "source_hint": source_hint,
            })
        elif m.group("pile_dia"):
            dia = float(m.group("pile_dia"))
            sections.append({
                "element": f"Cọc khoan nhồi D{int(dia)}",
                "diameter_mm": dia,
                "source_hint": source_hint,
            })
        elif m.group("as_val"):
            rebars.append({
                "mark": str(len(rebars)+1),
                "As_mm2": float(m.group("as_val").replace(",", ".")),
                "source_hint": source_hint,
            })

    # — Materials v2.0 (TCVN + Eurocode + ASTM/JIS/Q345B) —
    seen_mats = set()
    for m in ENGINEERING_PATTERNS["material"].finditer(decoded_text):
        if m.group("concrete") and m.group("concrete") not in seen_mats:
            grade = m.group("concrete").upper()
            seen_mats.add(grade)
            fck_map = {
                "B15": 12, "B20": 16, "B25": 20, "B30": 25, "B35": 30, "B40": 35, "B45": 38, "B50": 42,
                "C16/20": 16, "C20/25": 20, "C25/30": 25, "C30/37": 30, "C35/45": 35, "C40/50": 40, "C50/60": 50,
            }
            materials.append({
                "type": "concrete",
                "grade": grade,
                "fck_MPa": fck_map.get(grade, 25 if grade.startswith("C") else 20),
            })
        if m.group("steel_struct") and m.group("steel_struct") not in seen_mats:
            grade = m.group("steel_struct").upper()
            seen_mats.add(grade)
            fy_map_struct = {"S235": 235, "S275": 275, "S355": 355, "S450": 450, "Q345": 345, "SS400": 235, "A572": 345, "A490": 895}
            materials.append({
                "type": "structural_steel",
                "grade": grade,
                "fy_MPa": next((v for k, v in fy_map_struct.items() if grade.startswith(k)), 345),
            })
        if m.group("steel") and m.group("steel") not in seen_mats:
            grade = m.group("steel").upper()
            seen_mats.add(grade)
            fy_map = {
                "CB240T": 240, "CB300T": 300, "CB300V": 300, "CB400V": 400, "CB500V": 500,
                "AI": 235, "AII": 295, "AIII": 390, "B500": 500, "B500B": 500, "B500C": 500,
                "GRADE 60": 414, "GR 60": 414,
            }
            found_fy = next((v for k, v in fy_map.items() if grade.replace(" ", "").startswith(k.replace(" ", "")[:4])), 400)
            materials.append({
                "type": "steel_rebar",
                "grade": grade,
                "fy_MPa": found_fy,
            })

    # — Wind Load —
    for m in ENGINEERING_PATTERNS["wind_load"].finditer(decoded_text):
        if m.group("w0_val"):
            w0 = float(m.group("w0_val").replace(",", "."))
            unit = m.group("w0_unit")
            loads.append({
                "label": "Áp lực gió cơ bản W0",
                "value": w0,
                "unit": unit,
                "source_hint": source_hint,
            })

    # — SPT —
    for m in ENGINEERING_PATTERNS["spt"].finditer(decoded_text):
        if re.match(r"\s*(?:kN|kPa|MPa|N)\b", decoded_text[m.end():], re.I):
            continue  # Axial force N is not an SPT blow count.
        soils.append({
            "SPT_N": float(m.group("spt_n").replace(",", ".")),
            "source_hint": source_hint,
        })

    logs.append({
        "step": "pattern_extraction_v2",
        "loads_found": len(loads),
        "sections_found": len(sections),
        "rebars_found": len(rebars),
        "materials_found": len(materials),
        "spt_found": len(soils),
    })

    return {
        "loads": loads,
        "sections": sections,
        "materials": materials,
        "soil_params": soils,
        "rebar_schedule": rebars,
        "project_info": {},
    }, logs


# ─────────────────────────────────────────────────────────────────────────────
# 4. FORMAT-SPECIFIC READERS v2.0
# ─────────────────────────────────────────────────────────────────────────────

# Universal v3 common schema and Word reader.
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W_NS, 'm': M_NS}


def _ascii_label(value):
    import unicodedata
    text = str(value or '').lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def _result(path, file_type, text='', tables=None, metadata=None, warnings=None,
            logs=None, headings=None, equations=None, entities=None, span_map=None, error=None):
    warnings, logs = list(warnings or []), list(logs or [])
    data, extracted = _extract_engineering_data(text, Path(path).name, span_map)
    if error:
        logs.append({'step': 'error', 'message': str(error)})
    canonical = {'loads': data['loads'], 'sections': data['sections'],
                 'rebars': data['rebar_schedule'], 'materials': [{k: v for k, v in item.items() if k not in ('fck_MPa', 'fy_MPa')} for item in data['materials']],
                 'soils': data['soil_params'], 'grids': [], 'columns': []}
    for key, values in _table_entities(tables or [], path).items():
        canonical[key].extend(values)
    for key, values in (entities or {}).items():
        if key in canonical:
            canonical[key].extend(values)
    data.update(loads=canonical['loads'], sections=canonical['sections'],
                rebar_schedule=canonical['rebars'], soil_params=canonical['soils'],
                grids=canonical['grids'], columns=canonical['columns'])
    status = 'ERROR' if error else 'PARTIAL' if warnings else 'OK' if text.strip() or tables or any(canonical.values()) else 'EMPTY'
    meta = {'schema_version': '3.0', 'source_path': str(Path(path).resolve()),
            'extracted_at': datetime.now().astimezone().isoformat(), 'warnings': warnings,
            'entity_method': 'pattern/table extraction; not design verification', **(metadata or {})}
    output = {'status': status, 'file_type': file_type, 'metadata': meta,
              'raw_text': text, 'tables': tables or [], 'engineering_entities': canonical,
              # Keep v2 consumers (conflict analyzer, truth-graph ingestion) working.
              'source_file': Path(path).name, 'source_type': file_type,
              'backend': meta.get('backend'), 'raw_text_preview': text[:800],
              'sections': headings or [], 'headings': headings or [], 'equations': equations or [],
              'engineering_data': data, 'Calculation_Logs': logs + extracted,
              'Standard_Method': 'doc_reader v3.0', 'extracted_at': meta['extracted_at']}
    if error:
        output['error'] = str(error)
    output['confidence_level'] = 'LOW' if error or warnings else _compute_confidence(output)
    return output


def _safe_reader(function):
    from functools import wraps
    @wraps(function)
    def wrapper(path, *args, **kwargs):
        kind = Path(path).suffix.lstrip('.').upper()
        try:
            if not Path(path).is_file():
                raise FileNotFoundError(f'Input file does not exist: {path}')
            return function(str(Path(path).resolve()), *args, **kwargs)
        except Exception as error:
            return _result(str(path), kind, error=f'{type(error).__name__}: {error}')
    return wrapper


def _office_converter_available(kind):
    import shutil
    if os.environ.get('SOFFICE_BINARY') or shutil.which('soffice'):
        return True
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 'Word.Application' if kind in ('doc', 'docx') else 'Excel.Application'):
                return True
        except OSError:
            pass
    return False


def _convert_office(source, target_dir, kind, timeout=90):
    """Use an isolated headless process; macros/links disabled for Windows Office."""
    import shutil, subprocess
    target_dir = Path(target_dir)
    target = target_dir / (Path(source).stem + '.' + kind)
    binary = os.environ.get('SOFFICE_BINARY') or shutil.which('soffice')
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    if binary:
        profile = (target_dir/'lo_profile').as_uri()
        command = [binary, f'-env:UserInstallation={profile}', '--headless', '--convert-to',
                   kind, '--outdir', str(target_dir), str(source)]
    elif os.name == 'nt' and _office_converter_available(kind):
        script = '''import sys
import win32com.client
source,target,kind=sys.argv[1:]
app=book=None
try:
 if kind in ('docx','doc'):
  app=win32com.client.DispatchEx('Word.Application')
  app.Visible=False
  app.DisplayAlerts=0
  app.AutomationSecurity=3
  app.Options.UpdateLinksAtOpen=False
  book=app.Documents.Open(source,ReadOnly=True,AddToRecentFiles=False,ConfirmConversions=False)
  book.SaveAs2(target,FileFormat=16 if kind=='docx' else 0)
 else:
  app=win32com.client.DispatchEx('Excel.Application')
  app.Visible=False
  app.DisplayAlerts=False
  app.AskToUpdateLinks=False
  app.AutomationSecurity=3
  book=app.Workbooks.Open(source,UpdateLinks=0,ReadOnly=True,IgnoreReadOnlyRecommended=True,AddToMru=False)
  book.SaveAs(target,FileFormat=51 if kind=='xlsx' else 56)
finally:
 if book is not None: book.Close(False)
 if app is not None: app.Quit()
'''
        command = [sys.executable, '-c', script, str(source), str(target), kind]
    else:
        raise RuntimeError('Legacy Office conversion requires LibreOffice (SOFFICE_BINARY) or installed Windows Word/Excel')
    completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=timeout, **flags)
    if completed.returncode or not target.is_file():
        raise RuntimeError(f'Office conversion failed: {completed.stderr[-600:]}')
    return target


def _omml_text(element):
    """Readable structural math plus original OMML XML; no symbolic evaluation."""
    def child(name):
        found = element.find('m:'+name, NS)
        return _omml_text(found) if found is not None else ''
    tag = element.tag.rsplit('}', 1)[-1]
    if tag in ('t',):
        return element.text or ''
    if tag == 'f':
        return '(' + child('num') + ')/(' + child('den') + ')'
    if tag == 'sSub':
        return child('e') + '_(' + child('sub') + ')'
    if tag == 'sSup':
        return child('e') + '^(' + child('sup') + ')'
    if tag == 'sSubSup':
        return child('e') + '_(' + child('sub') + ')^(' + child('sup') + ')'
    if tag == 'rad':
        return ('root[' + child('deg') + ']' if child('deg') else 'sqrt') + '(' + child('e') + ')'
    if tag == 'd':
        props = element.find('m:dPr', NS)
        def delimiter(name, default):
            node = props.find('m:'+name, NS) if props is not None else None
            return node.get('{'+M_NS+'}val', default) if node is not None else default
        return (delimiter('begChr', '(') + delimiter('sepChr', '|').join(
            _omml_text(e) for e in element.findall('m:e', NS)) + delimiter('endChr', ')'))
    if tag == 'nary':
        operator = element.find('m:naryPr/m:chr', NS)
        symbol = operator.get('{'+M_NS+'}val', '∫') if operator is not None else '∫'
        return symbol + ('_('+child('sub')+')' if child('sub') else '') + (
            '^('+child('sup')+')' if child('sup') else '') + '('+child('e')+')'
    if tag == 'm':
        return '[' + '; '.join(', '.join(_omml_text(e) for e in row.findall('m:e', NS))
                               for row in element.findall('m:mr', NS)) + ']'
    if tag == 'eqArr':
        return '; '.join(_omml_text(e) for e in element.findall('m:e', NS))
    if tag.endswith('Pr'):
        return ''
    return ''.join(_omml_text(item) for item in element)


def _word_text(element):
    pieces = []
    def visit(item):
        if item.tag in ('{'+M_NS+'}oMath', '{'+M_NS+'}oMathPara'):
            pieces.append(_omml_text(item))
        elif item.tag == '{'+W_NS+'}t':
            pieces.append(item.text or '')
        elif item.tag in ('{'+W_NS+'}tab', '{'+W_NS+'}br'):
            pieces.append(' ')
        else:
            for nested in item:
                visit(nested)
            if item.tag == '{'+W_NS+'}p':
                pieces.append('\n')
    visit(element)
    return VietnameseLegacyDecoder.decode(''.join(pieces).strip())


def _word_table(element, number, equations, warnings):
    grid = element.find('w:tblGrid', NS)
    width = len(grid) if grid is not None else 0
    rows, cells, previous = [], [], {}
    for row_index, row in enumerate(element.findall('w:tr', NS)):
        before = row.find('w:trPr/w:gridBefore', NS)
        col = int(before.get('{'+W_NS+'}val', '0')) if before is not None else 0
        expanded, current = {}, {}
        for tc in row.findall('w:tc', NS):
            span = tc.find('w:tcPr/w:gridSpan', NS)
            span = int(span.get('{'+W_NS+'}val', '1')) if span is not None else 1
            merge = tc.find('w:tcPr/w:vMerge', NS)
            continuing = merge is not None and merge.get('{'+W_NS+'}val', 'continue') != 'restart'
            if continuing and col in previous:
                anchor = previous[col]
                anchor['row_span'] += 1
            else:
                if continuing:
                    warnings.append(f'Table {number}: orphan vertical merge at row {row_index}, column {col}')
                anchor = {'row': row_index, 'column': col, 'row_span': 1,
                          'col_span': span, 'text': _word_text(tc)}
                cells.append(anchor)
            for c in range(col, col+span):
                expanded[c] = anchor['text']
                if merge is not None:
                    current[c] = anchor
            for math in tc.findall('.//m:oMath', NS):
                import xml.etree.ElementTree as ET
                equations.append({'text': _omml_text(math), 'omml': ET.tostring(math, encoding='unicode'),
                                  'table': number, 'row': row_index, 'column': col})
            col += span
        width = max(width, col)
        rows.append(expanded)
        previous = current
    dense = [[row.get(i) for i in range(width)] for row in rows]
    return {**_make_table(dense, f'Bảng {number}', structure='word_grid'),
            'grid': dense, 'cells': cells, 'merged_cells': [
                cell for cell in cells if cell['col_span'] > 1 or cell['row_span'] > 1]}


@_safe_reader
def read_docx(path):
    import tempfile
    if Path(path).suffix.lower() == '.doc':
        with tempfile.TemporaryDirectory(prefix='reader_doc_') as directory:
            converted = _convert_office(path, directory, 'docx')
            result = read_docx(str(converted))
            result.update(file_type='DOC', source_type='DOC', source_file=Path(path).name)
            result['metadata'].update(source_path=path, converted_from='DOC', conversion='headless_office')
            if result['metadata'].get('embedded_images'):
                result['metadata']['warnings'].append('LEGACY_DOC_GRAPHICS_NOT_OCR: legacy equations may be stored as images/OLE, not OMML')
                if result['status'] != 'ERROR':
                    result['status'], result['confidence_level'] = 'PARTIAL', 'LOW'
            for records in result['engineering_entities'].values():
                for record in records:
                    if isinstance(record, dict) and 'source_hint' in record:
                        record['source_hint'] = Path(path).name
            return result
    if _DOCX_BACKEND is None:
        raise RuntimeError('python-docx is required')
    from docx.text.paragraph import Paragraph
    import xml.etree.ElementTree as ET
    doc = _docx_lib.Document(path)
    import zipfile
    with zipfile.ZipFile(path) as archive:
        embedded = [name for name in archive.namelist() if name.startswith('word/embeddings/')]
        images = [name for name in archive.namelist() if name.startswith('word/media/')]
    text, tables, headings, equations, warnings, stack = [], [], [], [], [], []
    for block in doc.element.body:
        if block.tag == '{'+W_NS+'}p':
            paragraph = Paragraph(block, doc)
            content = _word_text(block)
            level, style, visited = None, paragraph.style, set()
            while style is not None and style.style_id not in visited:
                visited.add(style.style_id)
                outline = style.element.find('w:pPr/w:outlineLvl', NS)
                name = re.search(r'heading\s*([123])', style.name, re.I)
                if outline is not None:
                    level = int(outline.get('{'+W_NS+'}val', '9'))+1
                    break
                if name:
                    level = int(name[1])
                    break
                style = style.base_style
            direct = block.find('w:pPr/w:outlineLvl', NS)
            if direct is not None:
                level = int(direct.get('{'+W_NS+'}val', '9'))+1
            if level in (1, 2, 3):
                while stack and stack[-1]['level'] >= level:
                    stack.pop()
                heading = {'id': 'h'+str(len(headings)+1), 'level': level, 'title': content,
                           'parent_id': stack[-1]['id'] if stack else None, 'content': ''}
                headings.append(heading)
                stack.append(heading)
            elif stack and content:
                stack[-1]['content'] += content + '\n'
            if content:
                text.append(content)
            for math in block.findall('.//m:oMath', NS):
                equations.append({'text': _omml_text(math), 'omml': ET.tostring(math, encoding='unicode'),
                                  'paragraph': len(text)})
        elif block.tag == '{'+W_NS+'}tbl':
            table = _word_table(block, len(tables)+1, equations, warnings)
            tables.append(table)
            text.extend(' | '.join(str(v) if v is not None else '' for v in row) for row in table['grid'])
    if embedded:
        warnings.append(f'EMBEDDED_OLE_NOT_PARSED:{len(embedded)}; native OMML is extracted separately')
    return _result(path, 'DOCX', '\n'.join(text), tables,
                   metadata={'backend': 'python-docx+xml', 'heading_count': len(headings),
                             'equation_count': len(equations), 'embedded_objects': embedded, 'embedded_images': images},
                   warnings=warnings, headings=headings, equations=equations)


def _tesseract_binary():
    import shutil
    candidates = [os.environ.get('TESSERACT_CMD'), shutil.which('tesseract'),
                  str(Path.home()/'scoop/apps/tesseract/current/tesseract.exe'),
                  r'C:\Program Files\Tesseract-OCR\tesseract.exe']
    return next((p for p in candidates if p and Path(p).is_file()), None)


def _preprocess_image(image):
    from PIL import Image, ImageOps
    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGBA', image.size, 'white')
        background.alpha_composite(image.convert('RGBA'))
        image = background.convert('RGB')
    gray = ImageOps.autocontrast(image.convert('L'))
    details = {'original_size': list(image.size), 'deskew_degrees': 0.0,
               'contrast': 'autocontrast', 'binarization': 'PIL_threshold'}
    try:
        import cv2, numpy as np
        array = np.array(gray)
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(array)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        lines = cv2.HoughLinesP(255-binary, 1, np.pi/1800, threshold=60,
                                minLineLength=max(40, image.width//8), maxLineGap=15)
        angles = []
        if lines is not None:
            for item in lines.reshape(-1, 4):
                x1, y1, x2, y2 = item
                angle = float(np.degrees(np.arctan2(y2-y1, x2-x1)))
                if abs(angle) <= 15:
                    angles.append(angle)
        if angles:
            angle = float(np.median(angles))
        else:
            ys, xs = np.where(binary < 128)
            angle = float(cv2.minAreaRect(np.column_stack([xs, ys]).astype('float32'))[-1]) if len(xs) > 20 else 0.0
            if angle > 45:
                angle -= 90
            if abs(angle) > 15:
                angle = 0.0
        if abs(angle) > .15:
            gray = Image.fromarray(enhanced).rotate(angle, resample=Image.Resampling.BICUBIC,
                                                    expand=True, fillcolor=255)
            enhanced = np.array(gray)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        details.update(deskew_degrees=round(angle, 3), contrast='CLAHE', binarization='OTSU')
        return Image.fromarray(binary), details
    except ImportError:
        details['deskew_available'] = False
        return gray.point(lambda value: 255 if value > 160 else 0), details


def _grid_lines(image):
    import cv2, numpy as np
    array = np.array(image.convert('L'))
    ink = 255-array
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                                  np.ones((1, max(40, image.width//25)), 'uint8'))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                                np.ones((max(40, image.height//25), 1), 'uint8'))
    def centers(values):
        groups = []
        for index in values:
            if groups and index <= groups[-1][-1]+2:
                groups[-1].append(int(index))
            else:
                groups.append([int(index)])
        return [float(np.mean(group)) for group in groups]
    x_indices = np.where(np.count_nonzero(vertical, axis=0) > image.height*.2)[0]
    y_indices = np.where(np.count_nonzero(horizontal, axis=1) > image.width*.2)[0]
    xs, ys = centers(x_indices), centers(y_indices)
    # Remove only confirmed table rules, not vertical strokes in large-font glyphs.
    mask = np.zeros_like(array)
    if len(xs) >= 2 and len(ys) >= 2:
        mask[:, x_indices] = vertical[:, x_indices]
        mask[y_indices, :] = np.maximum(mask[y_indices, :], horizontal[y_indices, :])
    return xs, ys, mask


def _run_ocr(image, lang='vie+eng'):
    import pytesseract
    binary = _tesseract_binary()
    if not binary:
        raise RuntimeError('Tesseract executable missing; configure TESSERACT_CMD')
    pytesseract.pytesseract.tesseract_cmd = binary
    available = set(pytesseract.get_languages(config=''))
    requested = lang.split('+')
    selected = [item for item in requested if item in available]
    if not selected:
        raise RuntimeError(f'OCR language data missing: {lang}')
    warnings = [] if selected == requested else [f'OCR_LANGUAGE_FALLBACK: {lang} -> {"+".join(selected)}']
    try:
        import numpy as np
        from PIL import Image
        _, _, mask = _grid_lines(image)
        ocr_image = Image.fromarray(np.maximum(np.array(image.convert('L')), mask))
    except ImportError:
        ocr_image = image
    data = pytesseract.image_to_data(ocr_image, lang='+'.join(selected), config='--psm 6',
                                     output_type=pytesseract.Output.DICT, timeout=40)
    words = []
    for i, text in enumerate(data['text']):
        if not text or not text.strip():
            continue
        confidence = float(data['conf'][i])
        if confidence < 0:
            continue
        words.append({'text': text.strip(), 'confidence': confidence,
                      'left': int(data['left'][i]), 'top': int(data['top'][i]),
                      'width': int(data['width'][i]), 'height': int(data['height'][i]),
                      'line': [int(data[k][i]) for k in ('block_num', 'par_num', 'line_num')]})
    lines = {}
    for word in words:
        lines.setdefault(tuple(word['line']), []).append(word)
    text = '\n'.join(' '.join(x['text'] for x in sorted(line, key=lambda x: x['left']))
                     for line in lines.values())
    return {'text': text, 'words': words, 'languages': selected, 'warnings': warnings}


def _ocr_tables(image, words, source_page):
    try:
        xs, ys, _ = _grid_lines(image)
    except ImportError:
        xs, ys = [], []
    if len(xs) >= 2 and len(ys) >= 2:
        rows = []
        for y1, y2 in zip(ys, ys[1:]):
            row = []
            for x1, x2 in zip(xs, xs[1:]):
                contained = [w for w in words if x1 < w['left']+w['width']/2 < x2
                             and y1 < w['top']+w['height']/2 < y2]
                row.append(' '.join(w['text'] for w in sorted(contained, key=lambda w: (w['top'], w['left']))))
            rows.append(row)
        if any(any(row) for row in rows):
            return [_make_table(rows, f'OCR table page {source_page}', source_page=source_page,
                                structure='raster_grid', grid_x=xs, grid_y=ys)]
    # Alignment fallback is explicitly inferred; never presented as measured CAD/table geometry.
    groups = []
    for word in sorted(words, key=lambda w: (w['top']+w['height']/2, w['left'])):
        center = word['top']+word['height']/2
        matching = next((g for g in groups if abs(g[0]-center) <= max(6, word['height']*.6)), None)
        if matching is None:
            groups.append([center, [word]])
        else:
            matching[1].append(word)
    rows = []
    for _, row in groups:
        chunks, right = [], None
        for word in sorted(row, key=lambda w: w['left']):
            if right is None or word['left']-right > max(25, word['height']*2.5):
                chunks.append(word['text'])
            else:
                chunks[-1] += ' '+word['text']
            right = word['left']+word['width']
        if len(chunks) >= 2:
            rows.append(chunks)
    if len(rows) >= 2 and len({len(row) for row in rows}) == 1:
        return [_make_table(rows, f'OCR aligned table page {source_page}', source_page=source_page,
                            structure='inferred_alignment', structural_confidence='LOW')]
    return []


def _ocr_frame(image, source_page=1, lang='vie+eng'):
    processed, preprocessing = _preprocess_image(image)
    recognized = _run_ocr(processed, lang)
    recognized['tables'] = _ocr_tables(processed, recognized['words'], source_page)
    recognized['preprocessing'] = preprocessing
    recognized['mean_word_confidence'] = (sum(w['confidence'] for w in recognized['words'])/
                                         len(recognized['words'])) if recognized['words'] else None
    return recognized


@_safe_reader
def read_image_ocr(path, lang='vie+eng'):
    from PIL import Image, ImageSequence
    chunks, tables, frames, warnings = [], [], [], []
    with Image.open(path) as image:
        for number, frame in enumerate(ImageSequence.Iterator(image), 1):
            try:
                recognized = _ocr_frame(frame.copy(), number, lang)
            except Exception as error:
                frames.append({'page': number, 'ocr_error': str(error)})
                warnings.append(f'OCR_UNAVAILABLE_PAGE:{number}:{error}')
                continue
            chunks.append(f'[PAGE {number}]\n'+recognized['text'])
            tables.extend(recognized.pop('tables'))
            warnings.extend(recognized.pop('warnings'))
            if not recognized['text'].strip():
                warnings.append(f'OCR_EMPTY_PAGE:{number}')
            frames.append({'page': number, **recognized})
    failed = [frame for frame in frames if 'ocr_error' in frame]
    return _result(path, Path(path).suffix.lstrip('.').upper(), '\n'.join(chunks), tables,
                   metadata={'backend': 'tesseract', 'pages': frames, 'page_count': len(frames)},
                   warnings=warnings, error=failed[0]['ocr_error'] if len(failed) == len(frames) and failed else None)


def _render_pdf_page(path, index, dpi=300):
    from PIL import Image
    try:
        import pymupdf as fitz
        with fitz.open(path) as pdf:
            pixmap = pdf[index].get_pixmap(dpi=dpi, alpha=False)
            return Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
    except ImportError:
        from pdf2image import convert_from_path
        return convert_from_path(path, dpi=dpi, first_page=index+1, last_page=index+1)[0]


@_safe_reader
def read_pdf(path, min_vector_chars=40, lang='vie+eng'):
    chunks, tables, pages, warnings, boundaries = [], [], [], [], []
    offset = 0
    if _PDF_BACKEND == 'pdfplumber':
        document = pdfplumber.open(path)
        count = len(document.pages)
    else:
        import pymupdf as fitz
        document = fitz.open(path)
        count = len(document)
    backend = 'pdfplumber' if _PDF_BACKEND == 'pdfplumber' else 'pymupdf'
    try:
        for index in range(count):
            page = document.pages[index] if _PDF_BACKEND == 'pdfplumber' else document[index]
            vector = (page.extract_text() if _PDF_BACKEND == 'pdfplumber' else page.get_text()) or ''
            coverage = 0.0
            if _PDF_BACKEND == 'pdfplumber':
                coverage = min(1.0, sum(max(0, image['x1']-image['x0'])*max(0, image['bottom']-image['top'])
                    for image in page.images)/max(1, page.width*page.height))
            else:
                coverage = min(1.0, sum(max(0, image['bbox'][2]-image['bbox'][0]) *
                    max(0, image['bbox'][3]-image['bbox'][1]) for image in page.get_image_info()) /
                    max(1, page.rect.width*page.rect.height))
            sparse = len(re.sub(r'\s', '', vector)) < min_vector_chars or (coverage > .5 and len(vector.strip()) < 200)
            garbled = vector.count('\ufffd')/max(1, len(vector)) > .05
            page_info = {'page': index+1, 'vector_chars': len(vector),
                         'scanned_candidate': sparse or garbled, 'ocr_used': False, 'image_coverage': coverage}
            selected = vector
            if sparse or garbled:
                try:
                    image = _render_pdf_page(path, index)
                    ocr = _ocr_frame(image, index+1, lang)
                    page_info.update(preprocessing=ocr['preprocessing'], languages=ocr['languages'],
                                     mean_word_confidence=ocr['mean_word_confidence'])
                    warnings.extend(ocr['warnings'])
                    if ocr['text'].strip():
                        page_info.update(vector_text=vector, ocr_text=ocr['text'])
                        selected = ocr['text'] if len(ocr['text']) >= len(vector) or garbled or coverage > .5 else vector
                        page_info['ocr_used'] = selected == ocr['text']
                        tables.extend(ocr['tables'])
                    elif not vector.strip():
                        warnings.append(f'OCR_EMPTY_PAGE:{index+1}')
                except Exception as error:
                    page_info['ocr_error'] = str(error)
                    warnings.append(f'OCR_UNAVAILABLE_PAGE:{index+1}:{error}')
            try:
                raw_tables = page.extract_tables() if _PDF_BACKEND == 'pdfplumber' else [t.extract() for t in page.find_tables().tables]
                # ETABS/soil exports often have aligned columns without visible rules.
                if not raw_tables:
                    raw_tables = (page.extract_tables({'vertical_strategy': 'text', 'horizontal_strategy': 'text'})
                                  if _PDF_BACKEND == 'pdfplumber' else
                                  [t.extract() for t in page.find_tables(strategy='text').tables])
                    raw_tables = [raw for raw in raw_tables if raw and
                                  _make_table(raw, '')['table_type'] != 'generic']
                for raw in raw_tables:
                    if raw:
                        tables.append(_make_table(raw, f'Bảng trang {index+1}', source_page=index+1,
                                                  structure='vector_table'))
            except Exception as error:
                warnings.append(f'TABLE_EXTRACTION_PAGE:{index+1}:{error}')
            chunk = f'[PAGE {index+1}]\n{VietnameseLegacyDecoder.decode(selected)}\n'
            chunks.append(chunk)
            boundaries.append((offset, offset+len(chunk)-1, index+1))
            offset += len(chunk)
            pages.append(page_info)
    finally:
        document.close()
    return _result(path, 'PDF', ''.join(chunks), tables,
                   metadata={'backend': backend, 'pages': pages, 'page_count': count},
                   warnings=warnings, span_map=PageSpanMap(boundaries))


def _header_key(value):
    text = _ascii_label(value)
    if re.fullmatch(r'n\s*[_\s]*(?:\(spt\)|spt)', text):
        return 'nspt'
    key = re.sub(r'[\s_]+', '', re.sub(r'\([^)]*\)|\[[^]]*\]', '', text))
    return {'jointlabel': 'joint', 'case/combo': 'outputcase', 'sptn': 'spt'}.get(key, key)


def _table_header_score(row):
    vocabulary = {'joint', 'outputcase', 'case', 'casetype', 'f1', 'f2', 'f3', 'fx', 'fy', 'fz',
                  'm1', 'm2', 'm3', 'mx', 'my', 'mz', 'stt', 'description', 'quantity', 'unit',
                  'amount', 'unitprice', 'khoi luong', 'don gia', 'thanh tien', 'don vi',
                  'layer', 'depth', 'spt', 'nspt', 'phi', 'cohesion', 'lop', 'chieu sau', 'ten cong tac'}
    normalized = [_header_key(v) for v in row]
    vocabulary = {_header_key(v) for v in vocabulary}
    recognized = sum(label in vocabulary for label in normalized)
    strings = sum(isinstance(v, str) and bool(v.strip()) for v in row)
    numeric = sum(isinstance(v, (int, float)) and not isinstance(v, bool) for v in row)
    filled = sum(v is not None and str(v).strip() != '' for v in row)
    return recognized*20 + min(filled, 12)*2 + strings - numeric*5 if filled >= 2 else -1


def _make_table(rows, caption, **metadata):
    rows = [list(row) for row in rows]
    if not rows:
        return {'caption': caption, 'headers': [], 'rows': [], **metadata}
    candidates = [(_table_header_score(row), i) for i, row in enumerate(rows[:80])]
    best, header = max(candidates, key=lambda item: (item[0], -item[1]))
    if best < 20:
        header = next((i for score, i in candidates if score >= 0), 0)
    # Pure numeric data must not lose the first row through header guessing.
    def header_text(value):
        if not isinstance(value, str) or not value.strip():
            return False
        try:
            float(value.replace(',', '.'))
            return False
        except ValueError:
            return True
    inferred = not any(header_text(value) for value in rows[header])
    if inferred:
        headers, body, header = [f'Column{i+1}' for i in range(len(rows[0]))], rows, -1
    else:
        headers = ['' if value is None else str(value).strip() for value in rows[header]]
        body = rows[header+1:]
    width = max([len(headers)]+[len(row) for row in body])
    headers.extend('Column'+str(i+1) for i in range(len(headers), width))
    body = [row+[None]*(width-len(row)) for row in body]
    names = {_header_key(h) for h in headers}
    kind = ('joint_reactions' if 'joint' in names and names & {'f1', 'fx', 'f3', 'fz'} else
            'boq' if names & {'quantity', 'khoiluong'} and names & {'unitprice', 'dongia', 'amount', 'thanhtien'} else
            'geotechnical' if names & {'spt', 'nspt'} or (names & {'layer', 'lop'} and names & {'depth', 'chieusau'}) else 'generic')
    units, unit_row = [None]*width, False
    if body:
        present = [str(value).strip() for value in body[0] if value is not None and str(value).strip()]
        recognized = [value for value in present if re.fullmatch(r'(?i)(?:kN|N|kNm|kN[.]m|Nmm|Nm|kNmm|m|mm|cm|kPa|MPa|m2|m3|deg|degrees|ton|tf)', value)]
        if recognized and len(recognized) == len(present):
            units, unit_row = body.pop(0), True
    return {'caption': caption, 'headers': headers, 'rows': body, 'table_type': kind,
            'header_index': header, 'header_inferred': inferred, 'preamble': rows[:max(0, header)],
            'units': units, 'unit_row': unit_row, **metadata}


def _json_cell(value):
    import math
    from datetime import date, time
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _sheet_tables(rows, formulas, sheet_name, merged_ranges=None):
    blocks, current = [], []
    for number, row in enumerate(rows, 1):
        if any(value is not None and str(value).strip() != '' for value in row) or any(
                isinstance(v, str) and v.startswith('=') for v in formulas[number-1]):
            current.append((number, row))
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    tables = []
    for block in blocks:
        if len(block) < 2:
            continue
        table = _make_table([row for _, row in block], f'Sheet: {sheet_name}', sheet=sheet_name)
        header = table['header_index']
        start = (0 if header < 0 else header+1) + int(table.get('unit_row', False))
        table['header_row'] = None if header < 0 else block[header][0]
        table['row_numbers'] = [number for number, _ in block[start:]]
        table['formula_rows'] = [[value if isinstance(value, str) and value.startswith('=') else None
                                  for value in formulas[number-1]] for number in table['row_numbers']]
        table['merged_ranges'] = merged_ranges or []
        tables.append(table)
    return tables


@_safe_reader
def read_xlsx(path):
    import csv, tempfile
    suffix = Path(path).suffix.lower()
    legacy_warning = None
    if suffix == '.xls' and _office_converter_available('xlsx'):
        try:
            with tempfile.TemporaryDirectory(prefix='reader_xls_') as directory:
                converted = _convert_office(path, directory, 'xlsx')
                result = read_xlsx(str(converted))
                if result['status'] == 'ERROR':
                    raise RuntimeError(result['error'])
                result.update(file_type='XLS', source_type='XLS', source_file=Path(path).name)
                result['metadata'].update(source_path=path, converted_from='XLS', conversion='headless_office')
                for records in result['engineering_entities'].values():
                    for record in records:
                        if isinstance(record, dict) and 'source_hint' in record:
                            record['source_hint'] = Path(path).name
                return result
        except Exception as error:
            legacy_warning = f'XLS_OFFICE_CONVERSION_FAILED: {error}'
    tables, texts, warnings, missing, formula_cells = [], [], [legacy_warning] if legacy_warning else [], [], []
    if suffix == '.csv':
        data = Path(path).read_bytes()
        for encoding in ('utf-8-sig', 'utf-16', 'cp1258'):
            if encoding == 'utf-16' and not data.startswith((b'\xff\xfe', b'\xfe\xff')):
                continue
            try:
                content = data.decode(encoding)
                break
            except UnicodeError:
                continue
        else:
            raise ValueError('CSV encoding not recognized')
        try:
            dialect = csv.Sniffer().sniff(content[:8192], delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel
        import io
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        rows = list(csv.reader(io.StringIO(content, newline=""), dialect=dialect))
        empty_formulas = [[None]*len(row) for row in rows]
        tables = _sheet_tables(rows, empty_formulas, Path(path).stem)
        texts = [' | '.join(row) for row in rows]
        backend, sheet_count = 'csv', 1
    elif suffix == '.xls':
        import xlrd
        workbook = xlrd.open_workbook(path, on_demand=True)
        try:
            for sheet in workbook.sheets():
                rows = [[_json_cell(value) for value in sheet.row_values(row)] for row in range(sheet.nrows)]
                tables.extend(_sheet_tables(rows, [[None]*len(row) for row in rows], sheet.name))
                texts.extend(' | '.join(str(v) if v is not None else '' for v in row) for row in rows)
            sheet_count = workbook.nsheets
        finally:
            workbook.release_resources()
        warnings.append('XLS_FORMULAS_UNAVAILABLE: xlrd exposes cached values only; install Office/LibreOffice for formula conversion')
        backend = 'xlrd'
    else:
        if _XLSX_BACKEND is None:
            raise RuntimeError('openpyxl is required')
        from concurrent.futures import ThreadPoolExecutor
        # Separate workbook instances: no shared openpyxl state between worker threads.
        def load(data_only):
            return _openpyxl_lib.load_workbook(path, data_only=data_only, read_only=True, keep_links=False)
        with ThreadPoolExecutor(max_workers=2) as executor:
            fvalues, fformulas = executor.submit(load, True), executor.submit(load, False)
            values, formulas = None, None
            try:
                values, formulas = fvalues.result(), fformulas.result()
                sheet_count = len(values.sheetnames)
                for name in values.sheetnames:
                    vrows = [[_json_cell(cell) for cell in row] for row in values[name].iter_rows(values_only=True)]
                    frows = [[_json_cell(cell) for cell in row] for row in formulas[name].iter_rows(values_only=True)]
                    tables.extend(_sheet_tables(vrows, frows, name))
                    texts.extend(' | '.join(str(value) if value is not None else '' for value in row) for row in vrows)
                    for row_index, row in enumerate(frows):
                        for col, value in enumerate(row):
                            if isinstance(value, str) and value.startswith('='):
                                coordinate = _openpyxl_lib.utils.get_column_letter(col+1)+str(row_index+1)
                                cache = vrows[row_index][col]
                                formula_cells.append({'sheet': name, 'coordinate': coordinate, 'formula': value, 'cached_value': cache})
                                if cache is None:
                                    missing.append(f'{name}!{coordinate}')
                            if isinstance(value, str) and value in {'#REF!', '#VALUE!', '#DIV/0!', '#N/A', '#NAME?', '#NUM!'}:
                                warnings.append(f'EXCEL_ERROR:{name}:{row_index+1}:{col+1}:{value}')
                            elif isinstance(vrows[row_index][col], str) and vrows[row_index][col] in {
                                    '#REF!', '#VALUE!', '#DIV/0!', '#N/A', '#NAME?', '#NUM!', '#NULL!'}:
                                warnings.append(f'EXCEL_ERROR:{name}:{row_index+1}:{col+1}:{vrows[row_index][col]}')
            finally:
                # Close both streams even if a worker/load failed.
                for future in (fvalues, fformulas):
                    if not future.cancelled() and future.exception() is None:
                        future.result().close()
        if missing:
            warnings.append(f'MISSING_FORMULA_CACHE:{len(missing)} cells; formulas are preserved, not evaluated')
        backend = 'openpyxl-dual-stream'
    entities = {}
    return _result(path, suffix.lstrip('.').upper(), '\n'.join(texts), tables,
                   metadata={'backend': backend, 'sheet_count': sheet_count, 'formula_cells': formula_cells,
                             'missing_formula_cache': missing}, warnings=warnings, entities=entities)


def _table_entities(tables, path):
    loads, soils = [], []
    for table in tables:
        names = [_header_key(value) for value in table['headers']]
        kind = table.get('table_type')
        for index, row in enumerate(table['rows']):
            record = dict(zip(names, row))
            source = {'source_hint': Path(path).name, 'source_page': table.get('source_page'),
                      'sheet': table.get('sheet'), 'row': table.get('row_numbers', [])[index] if index < len(table.get('row_numbers', [])) else index+1}
            def number(value):
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return value
                try:
                    return float(str(value).strip().replace(',', '.'))
                except (ValueError, TypeError):
                    return None
            if kind == 'joint_reactions':
                for col, name in enumerate(names):
                    if name in {'f1', 'f2', 'f3', 'fx', 'fy', 'fz', 'm1', 'm2', 'm3', 'mx', 'my', 'mz'}:
                        value = number(record.get(name))
                        if value is not None:
                            match = re.search(r'\(([^)]+)\)|\[([^]]+)\]', table['headers'][col])
                            unit = next((x for x in match.groups() if x), None) if match else table.get('units', [None]*len(names))[col]
                            loads.append({'label': name.upper(), 'value': value, 'unit': unit,
                                          'joint': record.get('joint'), 'case': record.get('outputcase', record.get('case')), **source})
            elif kind == 'geotechnical':
                item = {key: number(record[name]) for name, key in [('spt', 'SPT_N'), ('nspt', 'SPT_N'),
                        ('phi', 'phi'), ('cohesion', 'c'), ('c', 'c'), ('depth', 'depth'), ('chieusau', 'depth')] if name in record and number(record[name]) is not None}
                if item:
                    item['layer'] = record.get('layer', record.get('lop'))
                    item['units'] = {}
                    for col, name in enumerate(names):
                        if name in {'phi', 'cohesion', 'c', 'depth', 'chieusau'}:
                            match = re.search(r'\(([^)]+)\)|\[([^]]+)\]', table['headers'][col])
                            unit = next((v for v in match.groups() if v), None) if match else table.get('units', [None]*len(names))[col]
                            key = 'c' if name == 'cohesion' else 'depth' if name == 'chieusau' else name
                            item['units'][key] = unit
                    soils.append({**item, **source})
    return {'loads': loads, 'soils': soils}


_CAD_DEEP_MODULE = None
import threading
_CAD_LOAD_LOCK = threading.RLock()


def _load_cad_parser():
    global _CAD_DEEP_MODULE
    with _CAD_LOAD_LOCK:
        if _CAD_DEEP_MODULE is None:
            import importlib.util
            location = Path(__file__).resolve().parent.parent/'skills/Design_Evaluation/scripts/cad_deep_reader.py'
            spec = importlib.util.spec_from_file_location('_universal_cad_deep', location)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            _CAD_DEEP_MODULE = module
        return _CAD_DEEP_MODULE


def _cad_wcs_entities(document, parser, warnings):
    grids, columns, texts, geometries = [], [], [], []
    def walk(entities, inherited='0', context='', depth=0):
        if depth > 32:
            warnings.append('CAD_BLOCK_DEPTH_LIMIT: possible recursive block definition')
            return
        for entity in entities:
            layer = entity.dxf.get('layer', '0')
            layer = inherited if layer == '0' else layer
            if entity.dxftype() == 'INSERT':
                if entity.block() is None:
                    warnings.append(f'CAD_BLOCK_MISSING:{entity.dxf.name}')
                    continue
                if entity.block().block.is_xref:
                    warnings.append(f'CAD_XREF_UNRESOLVED:{entity.dxf.name}')
                    continue
                if entity.mcount > 1:
                    yield from walk(entity.multi_insert(), layer, entity.dxf.name, depth+1)
                else:
                    yield from walk(entity.attribs, layer, entity.dxf.name, depth+1)
                    virtual = entity.virtual_entities(skipped_entity_callback=lambda e, reason: warnings.append(f'CAD_SKIPPED:{reason}'))
                    yield from walk(virtual, layer, entity.dxf.name, depth+1)
            else:
                yield entity, layer, context
    for entity, layer, context in walk(document.modelspace()):
        kind = entity.dxftype()
        group = parser.SemanticLayerClassifier.classify(layer, kind)
        if group == 'GENERAL_STRUCTURAL' and re.search(r'cot|column|vach|wall', _ascii_label(context)):
            group = 'COLUMN_WALL'
        item = {'entity_type': kind, 'layer': layer, 'semantic_group': group, 'coordinate_system': 'WCS',
                'block_context': context}
        if kind in ('TEXT', 'MTEXT', 'ATTRIB'):
            raw = entity.dxf.text if kind != 'MTEXT' else entity.plain_text()
            decoded, encoding = parser.VietnameseCADTextDecoder.decode(raw, entity.dxf.get('style', 'Standard'))
            position = entity.dxf.insert
            if kind in ('TEXT', 'ATTRIB'):
                position = entity.ocs().to_wcs(position)
            item.update(text=decoded, raw_text=raw, encoding=encoding, position_wcs=list(position))
            texts.append(item)
        elif kind == 'LINE':
            item['points_wcs'] = [list(entity.dxf.start), list(entity.dxf.end)]
        elif kind == 'LWPOLYLINE':
            item.update(points_wcs=[list(point) for point in entity.vertices_in_wcs()], closed=entity.closed,
                        has_arc=bool(entity.has_arc))
        elif kind == 'POLYLINE':
            item.update(points_wcs=[list(point) for point in entity.points_in_wcs()], closed=entity.is_closed,
                        has_arc=any(abs(vertex.dxf.get('bulge', 0)) > 1e-12 for vertex in entity.vertices))
        elif kind == 'CIRCLE':
            item.update(position_wcs=list(entity.ocs().to_wcs(entity.dxf.center)), radius=entity.dxf.radius)
        elif kind == 'ELLIPSE':
            item.update(position_wcs=list(entity.dxf.center), major_axis_wcs=list(entity.dxf.major_axis),
                        ratio=entity.dxf.ratio, start_param=entity.dxf.start_param, end_param=entity.dxf.end_param)
        else:
            if group in ('GRID_AXIS', 'COLUMN_WALL'):
                warnings.append(f'CAD_GEOMETRY_UNSUPPORTED:{kind}:{layer}')
            continue
        if 'points_wcs' in item:
            points = item['points_wcs']
            if points:
                item['bbox_wcs'] = [[min(p[i] for p in points) for i in range(3)],
                                    [max(p[i] for p in points) for i in range(3)]]
            geometries.append(item)
        if group == 'GRID_AXIS':
            grids.append(item)
        elif group == 'COLUMN_WALL':
            columns.append(item)
    return {'grids': grids, 'columns': columns}, texts, geometries


@_safe_reader
def read_dxf(path):
    import tempfile, shutil
    parser = _load_cad_parser()
    original, warnings = path, []
    with tempfile.TemporaryDirectory(prefix='reader_cad_') as directory:
        if Path(path).suffix.lower() == '.dwg':
            # Isolate native AUDIT/BIND/QUIT side effects from the user's drawing.
            staged = Path(directory)/'source.dwg'
            shutil.copy2(path, staged)
            target = Path(directory)/'converted.dxf'
            path = parser.DWGHeadlessBridge.convert_dwg_to_dxf(str(staged), output_dxf=str(target))
        deep = parser.DXFDeepExtractor.parse_dxf_file(path)
        if _DXF_BACKEND is None:
            entities, texts, geometry = {}, [dict(text=t['decoded_utf8'], **t) for t in deep['texts']], []
            warnings.append('CAD_WCS_UNAVAILABLE: install ezdxf for block geometry')
            units = None
        else:
            document = _ezdxf_lib.readfile(path)
            entities, texts, geometry = _cad_wcs_entities(document, parser, warnings)
            units = document.header.get('$INSUNITS')
        texts.sort(key=lambda item: (-item.get('position_wcs', [0, 0])[1], item.get('position_wcs', [0, 0])[0]))
        raw = '\n'.join(item['text'] for item in texts)
        return _result(original, Path(original).suffix.lstrip('.').upper(), raw,
                       metadata={'backend': 'cad_deep_reader+ezdxf', 'coordinate_system': 'WCS',
                                 'drawing_units_code': units, 'text_entities': texts,
                                 'geometry': geometry, 'cad_audit': deep['summary'],
                                 'conversion': 'DWGHeadlessBridge' if original.lower().endswith('.dwg') else None},
                       warnings=warnings, entities=entities, logs=deep.get('Calculation_Logs'))



# ─────────────────────────────────────────────────────────────────────────────
# 5. DEMO & HELPERS v2.0
# ─────────────────────────────────────────────────────────────────────────────

def _legacy_demo_result() -> dict:
    return {
        "source_file": "DEMO_thuyetminh_Dam_Tang3.pdf",
        "source_type": "PDF",
        "backend": "DEMO",
        "raw_text_preview": "DEMO V2.0 Universal Engineering Document Reader",
        "sections": [{"title": "Demo Section", "content": "Bê tông B30, Thép H400x200x8x12"}],
        "tables": [],
        "engineering_data": {
            "project_info": {"name": "Bourbon Steel & Concrete Plant", "location": "Long An"},
            "loads": [{"label": "Tải Solar", "value": 0.25, "unit": "kN/m²", "source_page": 1}],
            "sections": [{"element": "Thép hình H400x200x8x12", "profile": "H400x200x8x12"}],
            "materials": [{"type": "concrete", "grade": "B30"}, {"type": "structural_steel", "grade": "S355"}],
            "soil_params": [],
            "rebar_schedule": [],
        },
        "confidence_level": "HIGH",
        "Calculation_Logs": [{"step": "demo_v2", "note": "Demo v2.0 active"}],
        "Standard_Method": "doc_reader v2.0",
    }


def _demo_result() -> dict:
    legacy = _legacy_demo_result()
    result = _result(legacy['source_file'], 'PDF', legacy['raw_text_preview'].replace('V2.0', 'V3.0'),
                     metadata={'backend': 'DEMO'}, headings=legacy['sections'])
    result['engineering_data'] = legacy['engineering_data']
    data = legacy['engineering_data']
    result['engineering_entities'] = {'loads': data['loads'], 'sections': data['sections'],
        'rebars': data['rebar_schedule'], 'materials': data['materials'],
        'soils': data['soil_params'], 'grids': [], 'columns': []}
    result['confidence_level'] = _compute_confidence(result)
    return result


def _detect_rebar_columns(header_row: list) -> dict:
    """Heuristic: ánh xạ cột → tên field từ header của bảng thống kê thép."""
    col_map = {}
    kw_map = {
        "mark": ["ký hiệu", "mark", "kh", "stt"],
        "dia": ["đường kính", "diameter", "dia", "d(mm)", "ø"],
        "count": ["số lượng", "count", "sl", "quantity", "n"],
        "length": ["chiều dài", "length", "l(mm)", "l(m)", "dài"],
    }
    for col_idx, cell in enumerate(header_row):
        cell_lower = str(cell).lower()
        for field, keywords in kw_map.items():
            if field not in col_map and any(k in cell_lower for k in keywords):
                col_map[field] = col_idx
    return col_map


def _compute_confidence(result: dict) -> str:
    eng = result.get("engineering_data", {})
    score = 0
    if eng.get("loads"): score += 25
    if eng.get("sections"): score += 25
    if eng.get("materials"): score += 20
    if result.get("tables"): score += 15
    if eng.get("rebar_schedule") or eng.get("soil_params"): score += 15
    return "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")


def _error_result(path: str, src_type: str, msg: str, logs: list) -> dict:
    return _result(path, src_type, error=msg, logs=logs)


def read_document(path: str, ocr_lang='vie+eng') -> dict:
    suffix = Path(path).suffix.lower()
    dispatch = {'.pdf': read_pdf, '.docx': read_docx, '.doc': read_docx,
                '.xlsx': read_xlsx, '.xls': read_xlsx, '.csv': read_xlsx,
                '.dxf': read_dxf, '.dwg': read_dxf,
                **{ext: read_image_ocr for ext in ('.png', '.jpg', '.jpeg', '.tif', '.tiff')}}
    reader = dispatch.get(suffix)
    if reader is None:
        return _error_result(path, suffix.lstrip('.').upper(), f'Unsupported format: {suffix}', [])
    if suffix in ('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'):
        return reader(path, lang=ocr_lang)
    return reader(path)


def scan_project_directory(dir_path: str, recursive: bool = True) -> dict:
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return {"status": "ERROR", "error": f"Thư mục không tồn tại: {dir_path}", "files": []}

    categories = {
        "thuyet_minh": [".pdf", ".docx", ".doc"],
        "ban_ve": [".dxf", ".dwg"],
        "bang_tinh": [".xlsx", ".xls", ".csv"],
        "mo_hinh": [".ifc", ".edb", ".sdb", ".fdb"],
        "hinh_anh": [".png", ".jpg", ".jpeg", ".tif", ".tiff"],
    }

    results = {
        "project_dir": str(p.resolve()),
        "scanned_at": datetime.now().isoformat(),
        "summary": {"total_files": 0, "thuyet_minh": 0, "ban_ve": 0, "bang_tinh": 0, "mo_hinh": 0, "hinh_anh": 0, "other": 0},
        "inventory": {"thuyet_minh": [], "ban_ve": [], "bang_tinh": [], "mo_hinh": [], "hinh_anh": [], "other": []},
    }

    pattern = "**/*" if recursive else "*"
    all_paths = [f for f in p.glob(pattern) if f.is_file() and not f.name.startswith("~$") and not f.name.startswith(".")]

    for fpath in all_paths:
        ext = fpath.suffix.lower()
        cat = "other"
        for k, exts in categories.items():
            if ext in exts:
                cat = k
                break
        item_info = {"name": fpath.name, "path": str(fpath.resolve()), "extension": ext, "size_kb": round(fpath.stat().st_size / 1024, 1), "category": cat}
        results["inventory"][cat].append(item_info)
        results["summary"][cat] += 1
        results["summary"]["total_files"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="doc_reader v3.0 — Universal Engineering Document Reader")
    parser.add_argument("--input", "-i", help="Đường dẫn file đầu vào")
    parser.add_argument("--scan-dir", help="Quét thư mục dự án")
    parser.add_argument("--output", "-o", help="Đường dẫn file JSON đầu ra")
    parser.add_argument("--ocr-lang", default="vie+eng", help="Tesseract languages, e.g. vie+eng")
    parser.add_argument("--demo", action="store_true", help="Chạy với dữ liệu mẫu")
    args = parser.parse_args()

    if args.demo:
        result = _demo_result()
    elif args.scan_dir:
        result = scan_project_directory(args.scan_dir)
    elif args.input:
        result = read_document(args.input, ocr_lang=args.ocr_lang)
    else:
        parser.print_help()
        return

    output_json = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"✅ Đã ghi: {args.output}")
    else:
        print(output_json)
    return 1 if result.get('status') == 'ERROR' else 2 if result.get('status') == 'PARTIAL' else 0


if __name__ == "__main__":
    sys.exit(main())
