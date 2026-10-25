"""
doc_reader.py — Universal Engineering Document Reader
======================================================
Sprint 4 · Task 4.1

Mục đích:
    Đọc mọi định dạng hồ sơ kỹ thuật phổ biến (PDF / DOCX / XLSX / DXF)
    và chuẩn hóa thành một JSON thống nhất chứa dữ liệu kỹ thuật có cấu trúc.
    Đây là tầng Input Intelligence — bước đầu tiên của pipeline thẩm tra.

Định dạng hỗ trợ:
    • PDF   — pdfplumber (Tier 1) | pdfminer fallback | regex raw text (Tier 3)
    • DOCX  — python-docx: paragraphs + tables
    • XLSX  — openpyxl: named ranges + BOQ patterns + rebar schedule
    • DXF   — ezdxf: TEXT / MTEXT / DIMENSION entities

Đầu ra JSON (chuẩn handoff conflict_analyzer):
    {
        "source_file":       "thuyetminh_cot_tang3.pdf",
        "source_type":       "PDF",
        "extracted_at":      "2026-10-18T21:00:00",
        "raw_text_preview":  "...",
        "sections":          [{"title": "...", "content": "..."}],
        "tables":            [{"caption": "...", "headers": [], "rows": [[]]}],
        "engineering_data": {
            "project_info":   {...},
            "loads":          [{"label": "Tĩnh tải sàn T3", "value": 12.5, "unit": "kN/m²", "source_page": 5}],
            "sections":       [{"element": "D1", "b_mm": 300, "h_mm": 600, "source": "tr.12"}],
            "materials":      [{"type": "concrete", "grade": "B30", "fck_MPa": 25}],
            "soil_params":    [{"layer": 1, "SPT_N": 12, "description": "Sét dẻo mềm"}],
            "rebar_schedule": [{"mark": "1", "dia_mm": 20, "count": 4, "length_mm": 5800}]
        },
        "confidence_level":  "HIGH",
        "Calculation_Logs":  [...],
        "Standard_Method":   "doc_reader v1.0 Sprint-4"
    }

Sử dụng:
    python doc_reader.py --input thuyetminh.pdf [--output result.json] [--demo]
    python doc_reader.py --input model.xlsx
    python doc_reader.py --input bando.dxf

Phụ thuộc tùy chọn (cài qua pip):
    pip install pdfplumber python-docx openpyxl ezdxf
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 0. Backend Detection
# ─────────────────────────────────────────────────────────────────────────────

_PDF_BACKEND   = None  # "pdfplumber" | "pdfminer" | "ocr" | "raw"
_DOCX_BACKEND  = None  # "python-docx" | None
_XLSX_BACKEND  = None  # "openpyxl" | None
_DXF_BACKEND   = None  # "ezdxf" | None
_OCR_BACKEND   = None  # "tesseract" | None

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

# OCR backend — dùng cho PDF scan (ảnh)
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
# 1. Engineering Pattern Registry
# ─────────────────────────────────────────────────────────────────────────────

# Regex patterns để nhận dạng số liệu kỹ thuật từ text thô
ENGINEERING_PATTERNS = {
    # Tải trọng: "tĩnh tải sàn: 3.5 kN/m2" | "q = 12.5 kN/m²"
    "load": re.compile(
        r"""(?:
            (?P<label_vi>(?:tĩnh\s*tải|hoạt\s*tải|tải\s*trọng|tải|q|g|p|w)\s*[\w\s]*?)
            \s*[:=]\s*
            (?P<value_load>[\d]+(?:[.,][\d]+)?)\s*
            (?P<unit_load>kN/m[²2]?|kN/m|kN|T/m[²2]?|T/m|T|kg/m[²2]?|kg/m|kPa|MPa)
        )""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
    # Tiết diện: "300x600" | "b=300mm, h=600mm" | "300×600"
    "section": re.compile(
        r"""(?:
            (?:b\s*=\s*)?(?P<b>[\d]{2,4})\s*[xX×]\s*(?P<h>[\d]{2,4})\s*(?:mm)?
        )""",
        re.VERBOSE,
    ),
    # Cốt thép: "4Ø20" | "6φ25" | "As = 1520 mm²"
    "rebar": re.compile(
        r"""(?:
            (?P<count_rb>\d+)\s*[ØøφΦ]\s*(?P<dia>[\d]+(?:[.,][\d]+)?)
            |As\s*=\s*(?P<as_val>[\d]+(?:[.,][\d]+)?)\s*mm[²2]?
        )""",
        re.VERBOSE | re.IGNORECASE,
    ),
    # SPT: "N = 12 búa" | "NSPT = 20"
    "spt": re.compile(
        r"""(?:N(?:SPT)?\s*=?\s*(?P<spt_n>[\d]+(?:[.,][\d]+)?)\s*(?:búa|blows)?)""",
        re.IGNORECASE | re.UNICODE,
    ),
    # Vật liệu: "bê tông B30", "C25/30", "thép CB300-T", "S355", "B500B", "Gr 60"
    "material": re.compile(
        r"""(?:
            (?:bê\s*tông\s*)?(?P<concrete>B(?:1[5-9]|[2-5]\d|60)|C\d{2}/\d{2})
            |(?:thép\s*(?:hình|kết\s*cấu)?\s*)?(?P<steel_struct>S(?:235|275|355|450)[A-Z0-9]*)
            |(?:thép(?:\s*chịu\s*(?:kéo|nén|uốn|lực)?)?\s*)?(?P<steel>CB\d{3}[-–]?[VT]?|AI{1,3}|SD\d{3}|B500[ABC]|(?:Grade|Gr)\s*60)
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
    # Trang: "Trang 5" | "tr.12" | "p.7"
    "page_ref": re.compile(
        r"""(?:(?:trang|tr|page|p)\s*\.?\s*(?P<page>\d+))""",
        re.IGNORECASE | re.UNICODE,
    ),
    # Phần tử: "Dầm D1", "Cột C2A", "Vách V3"
    "element_label": re.compile(
        r"""(?P<elem_type>Dầm|Dam|Cột|Col|Vách|Vach|Sàn|San|Móng|Mong)\s*
            (?P<elem_id>[A-Z0-9]{1,6})""",
        re.VERBOSE | re.IGNORECASE | re.UNICODE,
    ),
}

# Bảng quy đổi đơn vị về kN/m²
UNIT_CONVERT_TO_KN_M2 = {
    "kN/m²": 1.0, "kN/m2": 1.0, "kPa": 1.0,
    "T/m²": 9.81, "T/m2": 9.81,
    "kg/m²": 0.00981, "kg/m2": 0.00981,
    "kN/m": None,  # dạng phân bố dài — giữ nguyên
    "kN": None,    # tải tập trung — giữ nguyên
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. Core Extraction Functions
# ─────────────────────────────────────────────────────────────────────────────

def _extract_engineering_data(text: str, source_hint: str = "") -> dict:
    """
    Chạy toàn bộ pattern registry trên đoạn text,
    trả về dict engineering_data có cấu trúc.
    """
    loads, sections, rebars, soils, materials = [], [], [], [], []
    logs = []

    # — Loads —
    for m in ENGINEERING_PATTERNS["load"].finditer(text):
        label = (m.group("label_vi") or "").strip().rstrip(":=").strip()
        raw_val = m.group("value_load").replace(",", ".")
        unit = m.group("unit_load")
        try:
            value = float(raw_val)
            # tìm page gần nhất trước match
            page_m = ENGINEERING_PATTERNS["page_ref"].search(text[:m.start()][::-1])
            page = int(page_m.group("page")) if page_m else None
            loads.append({
                "label": label or f"Tải {len(loads)+1}",
                "value": value,
                "unit": unit,
                "source_page": page,
                "source_hint": source_hint,
            })
        except ValueError:
            pass

    # — Sections —
    seen_secs = set()
    for m in ENGINEERING_PATTERNS["section"].finditer(text):
        b, h = int(m.group("b")), int(m.group("h"))
        # lọc số không hợp lý (quá nhỏ hoặc quá lớn cho mm)
        if not (100 <= b <= 3000 and 100 <= h <= 5000):
            continue
        key = (b, h)
        if key in seen_secs:
            continue
        seen_secs.add(key)
        # tìm nhãn phần tử gần nhất
        snippet = text[max(0, m.start()-60):m.start()]
        em = ENGINEERING_PATTERNS["element_label"].search(snippet)
        element = f"{em.group('elem_type')} {em.group('elem_id')}" if em else f"CK-{len(sections)+1}"
        sections.append({
            "element": element,
            "b_mm": b,
            "h_mm": h,
            "source_hint": source_hint,
        })

    # — Rebar —
    for m in ENGINEERING_PATTERNS["rebar"].finditer(text):
        if m.group("count_rb") and m.group("dia"):
            rebars.append({
                "mark": str(len(rebars)+1),
                "count": int(m.group("count_rb")),
                "dia_mm": float(m.group("dia")),
                "source_hint": source_hint,
            })
        elif m.group("as_val"):
            rebars.append({
                "mark": str(len(rebars)+1),
                "As_mm2": float(m.group("as_val").replace(",", ".")),
                "source_hint": source_hint,
            })

    # — Materials —
    seen_mats = set()
    for m in ENGINEERING_PATTERNS["material"].finditer(text):
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
            fy_map_struct = {"S235": 235, "S275": 275, "S355": 355, "S450": 450}
            materials.append({
                "type": "structural_steel",
                "grade": grade,
                "fy_MPa": next((v for k, v in fy_map_struct.items() if grade.startswith(k)), 355),
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
    for m in ENGINEERING_PATTERNS["wind_load"].finditer(text):
        if m.group("w0_val"):
            w0 = float(m.group("w0_val").replace(",", "."))
            unit = m.group("w0_unit")
            loads.append({
                "label": "Áp lực gió cơ bản W0",
                "value": w0,
                "unit": unit,
                "source_hint": source_hint,
            })
        elif m.group("wind_zone"):
            loads.append({
                "label": f"Vùng gió {m.group('wind_zone')}",
                "value": m.group("wind_zone"),
                "unit": "vùng",
                "source_hint": source_hint,
            })

    # — SPT —
    for m in ENGINEERING_PATTERNS["spt"].finditer(text):
        soils.append({
            "SPT_N": float(m.group("spt_n").replace(",", ".")),
            "source_hint": source_hint,
        })

    logs.append({
        "step": "pattern_extraction",
        "loads_found": len(loads),
        "sections_found": len(sections),
        "rebars_found": len(rebars),
        "materials_found": len(materials),
        "spt_found": len(soils),
    })

    return {
        "loads":          loads,
        "sections":       sections,
        "materials":      materials,
        "soil_params":    soils,
        "rebar_schedule": rebars,
        "project_info":   {},
    }, logs


# ─────────────────────────────────────────────────────────────────────────────
# 3. Format-Specific Readers
# ─────────────────────────────────────────────────────────────────────────────

def read_pdf(path: str) -> dict:
    """Đọc PDF — trả về structured output."""
    logs = [{"step": "pdf_backend", "backend": _PDF_BACKEND}]
    raw_text = ""
    tables_raw = []
    sections_doc = []

    if _PDF_BACKEND == "pdfplumber":
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                raw_text += f"\n[PAGE {i+1}]\n{page_text}"
                # Extract tables
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
        raw_text = _pm_extract(path) or ""
        logs.append({"step": "pdf_read_pdfminer", "chars": len(raw_text)})

    else:
        raw_text = ""
        logs.append({"step": "pdf_read_fallback"})

    # Tier 1.5 — OCR fallback khi text quá ngắn (PDF scan / ảnh)
    # Kích hoạt khi text extract < 100 ký tự và OCR backend sẵn sàng
    if len(raw_text.strip()) < 100 and _OCR_BACKEND == "tesseract":
        try:
            ocr_text = ""
            images = _pdf2img(path, dpi=300)
            for i, img in enumerate(images):
                page_ocr = _tesseract.image_to_string(img, lang="vie+eng")
                ocr_text += f"\n[OCR PAGE {i+1}]\n{page_ocr}"
            if ocr_text.strip():
                raw_text = ocr_text
                logs.append({
                    "step": "ocr_fallback",
                    "backend": "tesseract",
                    "pages": len(images),
                    "chars": len(ocr_text),
                    "note": "PDF scan — đã dùng OCR để extract text",
                })
        except Exception as ocr_err:
            logs.append({"step": "ocr_failed", "error": str(ocr_err)})

    # Tier 3 raw fallback nếu vẫn còn trống
    if not raw_text.strip():
        with open(path, "rb") as f:
            content = f.read()
        raw_text = content.decode("latin-1", errors="replace")
        logs.append({"step": "pdf_read_raw", "bytes": len(content)})

    # Phân đoạn sections từ heading pattern
    heading_pat = re.compile(r"(?m)^(?:CHƯƠNG|MỤC|PHẦN|\d+\.)\s+.{3,80}$", re.UNICODE)
    positions = [(m.start(), m.group()) for m in heading_pat.finditer(raw_text)]
    for idx, (pos, title) in enumerate(positions):
        end = positions[idx+1][0] if idx+1 < len(positions) else pos+2000
        sections_doc.append({"title": title.strip(), "content": raw_text[pos:end][:500]})

    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
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
    """Đọc DOCX — extract paragraphs + tables."""
    logs = [{"step": "docx_backend", "backend": _DOCX_BACKEND}]
    raw_text = ""
    tables_raw = []
    sections_doc = []

    if _DOCX_BACKEND != "python-docx":
        return _error_result(path, "DOCX", "python-docx not installed. Run: pip install python-docx", logs)

    doc = _docx_lib.Document(path)
    current_section = None

    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        raw_text += txt + "\n"
        # Heading detection
        if para.style.name.startswith("Heading"):
            if current_section:
                sections_doc.append(current_section)
            current_section = {"title": txt, "content": ""}
        elif current_section:
            current_section["content"] += txt + " "

    if current_section:
        sections_doc.append(current_section)

    # Tables
    for i, tbl in enumerate(doc.tables):
        rows = []
        for row in tbl.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        if rows:
            tables_raw.append({
                "caption": f"Bảng {i+1}",
                "headers": rows[0],
                "rows": rows[1:],
            })
            # Flatten table text vào raw_text để extract
            for r in rows:
                raw_text += " | ".join(r) + "\n"

    logs.append({"step": "docx_read", "paragraphs": len(doc.paragraphs), "tables": len(tables_raw)})
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
    """Đọc Excel BOQ / bảng thống kê thép."""
    logs = [{"step": "xlsx_backend", "backend": _XLSX_BACKEND}]

    if _XLSX_BACKEND != "openpyxl":
        return _error_result(path, "XLSX", "openpyxl not installed. Run: pip install openpyxl", logs)

    wb = _openpyxl_lib.load_workbook(path, data_only=True)
    tables_raw = []
    raw_text = ""
    rebar_schedule = []
    loads = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_rows = []
        for row in ws.iter_rows(values_only=True):
            clean = [str(c) if c is not None else "" for c in row]
            if any(c.strip() for c in clean):
                sheet_rows.append(clean)
                raw_text += " | ".join(clean) + "\n"

        if sheet_rows:
            tables_raw.append({
                "caption": f"Sheet: {sheet_name}",
                "headers": sheet_rows[0] if sheet_rows else [],
                "rows": sheet_rows[1:],
            })

        # Heuristic: nhận dạng bảng thống kê thép
        # Header có chứa "ký hiệu", "đường kính", "số lượng", "chiều dài"
        header_text = " ".join(sheet_rows[0]).lower() if sheet_rows else ""
        is_rebar = any(k in header_text for k in ["ký hiệu", "đường kính", "dia", "chiều dài", "length", "số lượng"])
        if is_rebar:
            col_map = _detect_rebar_columns(sheet_rows[0])
            for r in sheet_rows[1:]:
                entry = {}
                if col_map.get("mark") is not None and col_map["mark"] < len(r):
                    entry["mark"] = r[col_map["mark"]]
                if col_map.get("dia") is not None and col_map["dia"] < len(r):
                    try:
                        entry["dia_mm"] = float(str(r[col_map["dia"]]).replace(",", "."))
                    except (ValueError, TypeError):
                        pass
                if col_map.get("count") is not None and col_map["count"] < len(r):
                    try:
                        entry["count"] = int(float(str(r[col_map["count"]]).replace(",", ".")))
                    except (ValueError, TypeError):
                        pass
                if col_map.get("length") is not None and col_map["length"] < len(r):
                    try:
                        entry["length_mm"] = float(str(r[col_map["length"]]).replace(",", "."))
                    except (ValueError, TypeError):
                        pass
                if entry:
                    rebar_schedule.append(entry)

        # Heuristic: nhận dạng bảng tải trọng
        is_load = any(k in header_text for k in ["tải", "load", "kn", "kg/m"])
        if is_load:
            for r in sheet_rows[1:]:
                row_text = " ".join(r)
                for m in ENGINEERING_PATTERNS["load"].finditer(row_text):
                    try:
                        loads.append({
                            "label": (m.group("label_vi") or "").strip(),
                            "value": float(m.group("value_load").replace(",", ".")),
                            "unit": m.group("unit_load"),
                            "source_hint": f"{Path(path).name}:{sheet_name}",
                        })
                    except (ValueError, AttributeError):
                        pass

    logs.append({"step": "xlsx_read", "sheets": len(wb.sheetnames)})
    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
    # Override với dữ liệu heuristic chính xác hơn
    if rebar_schedule:
        eng_data["rebar_schedule"] = rebar_schedule
    if loads:
        eng_data["loads"] = loads
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
    """Đọc DXF — extract text, dimension, block attributes."""
    logs = [{"step": "dxf_backend", "backend": _DXF_BACKEND}]

    if _DXF_BACKEND != "ezdxf":
        return _error_result(path, "DXF", "ezdxf not installed. Run: pip install ezdxf", logs)

    doc_dxf = _ezdxf_lib.readfile(path)
    msp = doc_dxf.modelspace()

    text_entities = []
    dims = []
    raw_text = ""

    for entity in msp:
        etype = entity.dxftype()
        if etype in ("TEXT", "MTEXT"):
            txt = entity.dxf.text if etype == "TEXT" else entity.plain_mtext()
            txt = txt.strip()
            if txt:
                text_entities.append({"type": etype, "text": txt})
                raw_text += txt + "\n"
        elif etype == "DIMENSION":
            try:
                dims.append({
                    "measurement": round(entity.dxf.actual_measurement, 2),
                    "text_override": getattr(entity.dxf, "text", ""),
                })
            except Exception:
                pass
        elif etype == "INSERT":
            # Block attributes
            try:
                for attrib in entity.attribs:
                    tag = attrib.dxf.tag
                    val = attrib.dxf.text
                    raw_text += f"{tag}={val}\n"
            except Exception:
                pass

    logs.append({
        "step": "dxf_read",
        "text_entities": len(text_entities),
        "dimensions": len(dims),
        "layers": len(doc_dxf.layers),
    })

    eng_data, ext_logs = _extract_engineering_data(raw_text, source_hint=Path(path).name)
    # Thêm dimensions vào sections
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
# 4. Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo_result() -> dict:
    """Trả về kết quả mẫu đầy đủ cho kiểm thử khi không có file thực."""
    return {
        "source_file": "DEMO_thuyetminh_Dam_Tang3.pdf",
        "source_type": "PDF",
        "backend": "DEMO",
        "raw_text_preview": (
            "[PAGE 1]\nDỰ ÁN: Nhà ở kết hợp văn phòng — TP.HCM\n"
            "THUYẾT MINH TÍNH TOÁN — PHẦN KẾT CẤU\n"
            "[PAGE 2]\nVật liệu sử dụng:\n  Bê tông B30, thép CB400V\n"
            "[PAGE 3]\nTải trọng:\n  Tĩnh tải sàn: 3.5 kN/m²\n  Hoạt tải sàn: 5.0 kN/m²\n"
            "[PAGE 5]\nDầm D1: tiết diện 300x600mm, cốt thép 4Ø25 chịu mô men dương\n"
            "Dầm D2: tiết diện 250x500mm\n"
        ),
        "sections": [
            {"title": "1. Vật liệu", "content": "Bê tông B30, thép CB400V"},
            {"title": "2. Tải trọng", "content": "Tĩnh tải sàn 3.5 kN/m², Hoạt tải 5.0 kN/m²"},
            {"title": "3. Kích thước cấu kiện", "content": "Dầm D1 300x600, Dầm D2 250x500"},
        ],
        "tables": [
            {
                "caption": "Bảng tải trọng sàn",
                "headers": ["Loại tải", "Giá trị (kN/m²)", "Hệ số vượt tải"],
                "rows": [
                    ["Tĩnh tải sàn BTCT", "3.5", "1.1"],
                    ["Hoạt tải sử dụng VP", "5.0", "1.2"],
                ],
                "source_page": 3,
            }
        ],
        "engineering_data": {
            "project_info": {"name": "Nhà ở kết hợp VP", "location": "TP.HCM"},
            "loads": [
                {"label": "Tĩnh tải sàn", "value": 3.5, "unit": "kN/m²", "source_page": 3, "source_hint": "DEMO"},
                {"label": "Hoạt tải sàn", "value": 5.0, "unit": "kN/m²", "source_page": 3, "source_hint": "DEMO"},
            ],
            "sections": [
                {"element": "Dầm D1", "b_mm": 300, "h_mm": 600, "source_hint": "DEMO"},
                {"element": "Dầm D2", "b_mm": 250, "h_mm": 500, "source_hint": "DEMO"},
            ],
            "materials": [
                {"type": "concrete", "grade": "B30", "fck_MPa": 25},
                {"type": "steel_rebar", "grade": "CB400V", "fy_MPa": 400},
            ],
            "soil_params": [],
            "rebar_schedule": [
                {"mark": "1", "count": 4, "dia_mm": 25, "source_hint": "DEMO"},
            ],
        },
        "confidence_level": "HIGH",
        "Calculation_Logs": [{"step": "demo_mode", "note": "Dữ liệu mẫu — không phải file thực"}],
        "Standard_Method": "doc_reader v1.0 Sprint-4 DEMO",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _detect_rebar_columns(header_row: list) -> dict:
    """Heuristic: ánh xạ cột → tên field từ header của bảng thống kê thép."""
    col_map = {}
    kw_map = {
        "mark":   ["ký hiệu", "mark", "kh", "stt"],
        "dia":    ["đường kính", "diameter", "dia", "d(mm)", "ø"],
        "count":  ["số lượng", "count", "sl", "quantity", "n"],
        "length": ["chiều dài", "length", "l(mm)", "l(m)", "dài"],
    }
    for col_idx, cell in enumerate(header_row):
        cell_lower = str(cell).lower()
        for field, keywords in kw_map.items():
            if field not in col_map and any(k in cell_lower for k in keywords):
                col_map[field] = col_idx
    return col_map


def _compute_confidence(result: dict) -> str:
    """Tính confidence level dựa trên completeness của engineering_data."""
    eng = result.get("engineering_data", {})
    score = 0
    if eng.get("loads"):       score += 25
    if eng.get("sections"):    score += 25
    if eng.get("materials"):   score += 20
    if result.get("tables"):   score += 15
    if eng.get("rebar_schedule") or eng.get("soil_params"): score += 15
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    return "LOW"


def _error_result(path: str, src_type: str, msg: str, logs: list) -> dict:
    return {
        "source_file": Path(path).name,
        "source_type": src_type,
        "error": msg,
        "engineering_data": {"loads":[],"sections":[],"materials":[],"soil_params":[],"rebar_schedule":[],"project_info":{}},
        "confidence_level": "LOW",
        "Calculation_Logs": logs + [{"step": "error", "message": msg}],
        "Standard_Method": "doc_reader v1.0 Sprint-4",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Main Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def read_document(path: str) -> dict:
    """
    Entry point chính — tự phát hiện định dạng và dispatch đến reader phù hợp.
    """
    ext = Path(path).suffix.lower()
    dispatch = {
        ".pdf":  read_pdf,
        ".docx": read_docx,
        ".doc":  read_docx,
        ".xlsx": read_xlsx,
        ".xls":  read_xlsx,
        ".dxf":  read_dxf,
        ".dwg":  lambda p: _error_result(p, "DWG",
                    "DWG binary format không hỗ trợ trực tiếp — export sang DXF từ AutoCAD.", []),
    }

    if ext not in dispatch:
        return _error_result(path, ext.upper(),
                             f"Định dạng '{ext}' chưa được hỗ trợ.", [])

    result = dispatch[ext](path)
    result["confidence_level"] = _compute_confidence(result)
    result["extracted_at"] = datetime.now().isoformat()
    result["Standard_Method"] = "doc_reader v1.0 Sprint-4"
    return result


def scan_project_directory(dir_path: str, recursive: bool = True) -> dict:
    """
    Quét toàn bộ thư mục dự án, tự động phát hiện và phân loại tất cả tài liệu kỹ thuật:
      - thuyet_minh: .pdf, .docx, .doc (Thuyết minh, Báo cáo kỹ thuật)
      - ban_ve: .dxf, .dwg (Bản vẽ CAD kỹ thuật)
      - bang_tinh: .xlsx, .xls, .csv (Bảng thống kê thép, BOQ, bảng tính Excel)
      - mo_hinh: .ifc, .edb, .sdb, .fdb (Mô hình BIM IFC, ETABS, SAP2000)

    Trả về cấu trúc tổng hợp hồ sơ dự án, sẵn sàng đưa vào conflict_analyzer.
    """
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return {
            "status": "ERROR",
            "error": f"Thư mục không tồn tại: {dir_path}",
            "files": [],
        }

    categories = {
        "thuyet_minh": [".pdf", ".docx", ".doc"],
        "ban_ve":      [".dxf", ".dwg"],
        "bang_tinh":   [".xlsx", ".xls", ".csv"],
        "mo_hinh":     [".ifc", ".edb", ".sdb", ".fdb"],
    }

    results = {
        "project_dir": str(p.resolve()),
        "scanned_at": datetime.now().isoformat(),
        "summary": {"total_files": 0, "thuyet_minh": 0, "ban_ve": 0, "bang_tinh": 0, "mo_hinh": 0, "other": 0},
        "inventory": {
            "thuyet_minh": [],
            "ban_ve": [],
            "bang_tinh": [],
            "mo_hinh": [],
            "other": [],
        },
        "processed_documents": [],
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

        item_info = {
            "name": fpath.name,
            "path": str(fpath.resolve()),
            "extension": ext,
            "size_kb": round(fpath.stat().st_size / 1024, 1),
            "category": cat,
        }
        results["inventory"][cat].append(item_info)
        results["summary"][cat] += 1
        results["summary"]["total_files"] += 1

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="doc_reader — Universal Engineering Document Reader (Sprint 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input",  "-i", help="Đường dẫn file đầu vào (PDF/DOCX/XLSX/DXF)")
    parser.add_argument("--scan-dir",     help="Quét toàn bộ thư mục dự án")
    parser.add_argument("--output", "-o", help="Đường dẫn file JSON đầu ra")
    parser.add_argument("--demo",   action="store_true", help="Chạy với dữ liệu mẫu (không cần file thực)")
    parser.add_argument("--backends", action="store_true", help="In danh sách backend khả dụng và thoát")
    args = parser.parse_args()

    if args.backends:
        print(json.dumps({
            "PDF":  _PDF_BACKEND,
            "DOCX": _DOCX_BACKEND,
            "XLSX": _XLSX_BACKEND,
            "DXF":  _DXF_BACKEND,
        }, ensure_ascii=False, indent=2))
        return

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
        # Summary
        eng = result.get("engineering_data", {})
        print(f"   Tải trọng: {len(eng.get('loads',[]))} | Tiết diện: {len(eng.get('sections',[]))} | Vật liệu: {len(eng.get('materials',[]))}")
        print(f"   Confidence: {result.get('confidence_level','?')}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
