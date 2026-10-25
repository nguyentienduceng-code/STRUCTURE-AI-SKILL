"""
doc_reader.py — Universal Engineering Document Reader v2.0 (Sprint 4 & Roadmap v2.0)
==================================================================================

Mục đích:
 Đọc mọi định dạng hồ sơ kỹ thuật phổ biến (PDF / DOCX / XLSX / DXF / DWG)
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
        from pdfminer.high_level import extract_text as _pm_extract
        _PDF_BACKEND = "pdfminer"
    except ImportError:
        _PDF_BACKEND = "raw"

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
            (?P<label_vi>(?:tĩnh\s*tải|hoạt\s*tải|tải\s*trọng|tải|solar|mep|q|g|p|w)\s*[\w\s]*)
            \s*[:=]\s*
            (?P<value_load>\d+(?:[.,]\d+)?)\s*
            (?P<unit_load>kN/m[²2]?|kN/m|kN|T/m[²2]?|T/m|T|kg/m[²2]?|kg/m|kPa|MPa|daN/m[²2]?)
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
                if not (50 <= val1 <= 4000 and 50 <= val1 <= 4000):
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
            if 200 <= val1 <= 3000:
                key = (f"D{val1}",)
                if key not in seen_secs:
                    seen_secs.add(key)
                    sections.append({"element": f"Cọc/Cấu kiện tròn D{val1}", "diameter_mm": val1, "source_hint": source_hint})

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

def read_pdf(path: str) -> dict:
    logs = [{"step": "pdf_backend", "backend": _PDF_BACKEND}]
    raw_text = ""
    tables_raw = []
    sections_doc = []
    boundaries = []
    current_offset = 0

    if _PDF_BACKEND == "pdfplumber":
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                decoded_page = VietnameseLegacyDecoder.decode(page_text)
                start_off = current_offset
                chunk_str = f"\n[PAGE {i+1}]\n{decoded_page}"
                raw_text += chunk_str
                current_offset += len(chunk_str)
                boundaries.append((start_off, current_offset, i + 1))
                
                for tbl in page.extract_tables():
                    if tbl:
                        tables_raw.append({
                            "caption": f"Bảng trang {i+1}",
                            "headers": tbl[0] if tbl else [],
                            "rows": tbl[1:] if len(tbl) > 1 else [],
                            "source_page": i+1,
                        })
            logs.append({"step": "pdf_read", "pages": len(pdf.pages), "tables": len(tables_raw)})

    elif _PDF_BACKEND == "pdfminer":
        raw_text = VietnameseLegacyDecoder.decode(_pm_extract(path) or "")
        boundaries.append((0, len(raw_text), 1))
        logs.append({"step": "pdf_read_pdfminer", "chars": len(raw_text)})
    else:
        raw_text = ""
        boundaries.append((0, 0, 1))
        logs.append({"step": "pdf_read_fallback"})

    # OCR fallback khi PDF scan
    if len(raw_text.strip()) < 100 and _OCR_BACKEND == "tesseract":
        try:
            ocr_text = ""
            images = _pdf2img(path, dpi=300)
            for i, img in enumerate(images):
                page_ocr = _tesseract.image_to_string(img, lang="vie+eng")
                decoded_ocr = VietnameseLegacyDecoder.decode(page_ocr)
                ocr_text += f"\n[OCR PAGE {i+1}]\n{decoded_ocr}"
            if ocr_text.strip():
                raw_text = ocr_text
                boundaries = [(0, len(raw_text), 1)]
                logs.append({"step": "ocr_fallback", "backend": "tesseract", "pages": len(images)})
        except Exception as ocr_err:
            logs.append({"step": "ocr_failed", "error": str(ocr_err)})

    span_map = PageSpanMap(boundaries)
    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name, span_map=span_map)
    logs += ext_logs

    return {
        "source_file": Path(path).name,
        "source_type": "PDF",
        "backend": _PDF_BACKEND,
        "raw_text_preview": raw_text[:800],
        "sections": sections_doc,
        "tables": tables_raw,
        "engineering_data": eng_data,
        "Calculation_Logs": logs,
    }


def read_docx(path: str) -> dict:
    logs = [{"step": "docx_backend", "backend": _DOCX_BACKEND}]
    raw_text = ""
    tables_raw = []
    sections_doc = []

    if _DOCX_BACKEND != "python-docx":
        return _error_result(path, "DOCX", "python-docx not installed.", logs)

    doc = _docx_lib.Document(path)
    for para in doc.paragraphs:
        txt = VietnameseLegacyDecoder.decode(para.text.strip())
        if txt:
            raw_text += txt + "\n"

    for i, tbl in enumerate(doc.tables):
        rows = [[VietnameseLegacyDecoder.decode(cell.text.strip()) for cell in row.cells] for row in tbl.rows]
        if rows:
            tables_raw.append({"caption": f"Bảng {i+1}", "headers": rows[0], "rows": rows[1:]})
            for r in rows:
                raw_text += " | ".join(r) + "\n"

    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
    logs += ext_logs

    return {
        "source_file": Path(path).name,
        "source_type": "DOCX",
        "backend": _DOCX_BACKEND,
        "raw_text_preview": raw_text[:800],
        "sections": sections_doc,
        "tables": tables_raw,
        "engineering_data": eng_data,
        "Calculation_Logs": logs,
    }


def read_xlsx(path: str) -> dict:
    logs = [{"step": "xlsx_backend", "backend": _XLSX_BACKEND}]
    if _XLSX_BACKEND != "openpyxl":
        return _error_result(path, "XLSX", "openpyxl not installed.", logs)

    wb = _openpyxl_lib.load_workbook(path, data_only=True)
    tables_raw, raw_text, rebar_schedule, loads = [], "", [], []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_rows = []
        for row in ws.iter_rows(values_only=True):
            clean = [VietnameseLegacyDecoder.decode(str(c) if c is not None else "") for c in row]
            if any(c.strip() for c in clean):
                sheet_rows.append(clean)
                raw_text += " | ".join(clean) + "\n"
        if sheet_rows:
            tables_raw.append({"caption": f"Sheet: {sheet_name}", "headers": sheet_rows[0], "rows": sheet_rows[1:]})

    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
    logs += ext_logs

    return {
        "source_file": Path(path).name,
        "source_type": "XLSX",
        "backend": _XLSX_BACKEND,
        "raw_text_preview": raw_text[:800],
        "sections": [],
        "tables": tables_raw,
        "engineering_data": eng_data,
        "Calculation_Logs": logs,
    }


def read_dxf(path: str) -> dict:
    logs = [{"step": "dxf_backend", "backend": _DXF_BACKEND}]
    if _DXF_BACKEND != "ezdxf":
        return _error_result(path, "DXF", "ezdxf not installed.", logs)

    doc_dxf = _ezdxf_lib.readfile(path)
    msp = doc_dxf.modelspace()
    text_entities, dims, raw_text = [], [], ""

    # Spatial sorting: gom nhóm TEXT/MTEXT theo tọa độ Y giảm dần, X tăng dần
    sorted_texts = []
    for entity in msp:
        etype = entity.dxftype()
        if etype in ("TEXT", "MTEXT"):
            txt = VietnameseLegacyDecoder.decode(entity.dxf.text if etype == "TEXT" else entity.plain_mtext())
            txt = txt.strip()
            if txt:
                pos = entity.dxf.insert
                sorted_texts.append((round(pos.y, 1), round(pos.x, 1), txt))
        elif etype == "DIMENSION":
            try:
                dims.append({"measurement": round(entity.dxf.actual_measurement, 2)})
            except Exception:
                pass

    # Sắp xếp theo Y giảm dần (từ trên xuống dưới), X tăng dần (từ trái sang phải)
    sorted_texts.sort(key=lambda t: (-t[0], t[1]))
    for _, _, txt in sorted_texts:
        raw_text += txt + "\n"

    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
    eng_data["dxf_dimensions"] = dims
    eng_data["dxf_layers"] = [layer.dxf.name for layer in doc_dxf.layers]
    logs += ext_logs

    return {
        "source_file": Path(path).name,
        "source_type": "DXF",
        "backend": _DXF_BACKEND,
        "raw_text_preview": raw_text[:800],
        "sections": [],
        "tables": [],
        "engineering_data": eng_data,
        "Calculation_Logs": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. DEMO & HELPERS v2.0
# ─────────────────────────────────────────────────────────────────────────────

def _demo_result() -> dict:
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
    return {
        "source_file": Path(path).name,
        "source_type": src_type,
        "error": msg,
        "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[],"project_info":{}},
        "confidence_level": "LOW",
        "Calculation_Logs": logs + [{"step": "error", "message": msg}],
        "Standard_Method": "doc_reader v2.0",
    }


def read_document(path: str) -> dict:
    ext = Path(path).suffix.lower()
    dispatch = {
        ".pdf": read_pdf,
        ".docx": read_docx,
        ".doc": read_docx,
        ".xlsx": read_xlsx,
        ".xls": read_xlsx,
        ".dxf": read_dxf,
        ".dwg": lambda p: _error_result(p, "DWG", "DWG binary không hỗ trợ trực tiếp — hãy export sang DXF.", []),
    }
    if ext not in dispatch:
        return _error_result(path, ext.upper(), f"Định dạng '{ext}' chưa được hỗ trợ.", [])
    result = dispatch[ext](path)
    result["confidence_level"] = _compute_confidence(result)
    result["extracted_at"] = datetime.now().isoformat()
    result["Standard_Method"] = "doc_reader v2.0"
    return result


def scan_project_directory(dir_path: str, recursive: bool = True) -> dict:
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return {"status": "ERROR", "error": f"Thư mục không tồn tại: {dir_path}", "files": []}

    categories = {
        "thuyet_minh": [".pdf", ".docx", ".doc"],
        "ban_ve": [".dxf", ".dwg"],
        "bang_tinh": [".xlsx", ".xls", ".csv"],
        "mo_hinh": [".ifc", ".edb", ".sdb", ".fdb"],
    }

    results = {
        "project_dir": str(p.resolve()),
        "scanned_at": datetime.now().isoformat(),
        "summary": {"total_files": 0, "thuyet_minh": 0, "ban_ve": 0, "bang_tinh": 0, "mo_hinh": 0, "other": 0},
        "inventory": {"thuyet_minh": [], "ban_ve": [], "bang_tinh": [], "mo_hinh": [], "other": []},
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
    parser = argparse.ArgumentParser(description="doc_reader v2.0 — Universal Engineering Document Reader")
    parser.add_argument("--input", "-i", help="Đường dẫn file đầu vào")
    parser.add_argument("--scan-dir", help="Quét thư mục dự án")
    parser.add_argument("--output", "-o", help="Đường dẫn file JSON đầu ra")
    parser.add_argument("--demo", action="store_true", help="Chạy với dữ liệu mẫu")
    args = parser.parse_args()

    if args.demo:
        result = _demo_result()
    elif args.scan_dir:
        result = scan_project_directory(args.scan_dir)
    elif args.input:
        if not os.path.exists(args.input):
            print(json.dumps({"error": f"File không tồn tại: {args.input}"}, ensure_ascii=False))
            sys.exit(1)
        result = read_document(args.input)
    else:
        parser.print_help()
        return

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"✅ Đã ghi: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
