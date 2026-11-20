# -*- coding: utf-8 -*-
"""
rfi_ncr_docx_generator.py — P4.2 Rule-12b/12e-compliant RFI/NCR Word generator
=============================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.2, §3.2.3.

Turns NCR / RFI records (from `rfi_ncr_bridge`) + optional CAD defect crop PNGs
into a legal `.docx` that satisfies the two hard locks:

  * **Điều 12b — Zero White Text Lock:** no white text on a dark fill, and no
    all-white RGB / white hex literal anywhere in this source (the module reads
    every color from `design_tokens`, so it is `audit_zero_white_text.py` clean).
    Header = light mineral slate (`DCE4EC`) with dark steel text (`1E3246`).
  * **Điều 12e — Typography Floor & Math Lock:** body >= 13 pt, tables >= 10.5 pt,
    captions >= 10 pt (never a sub-10 pt size); no double-bullet; numbered lists
    use indented paragraphs (NOT `List Bullet`); raw `$...$` LaTeX is normalised
    to Unicode / real sub-superscript.

Legal framing (spec §3.2): Nghị định 175/2024/NĐ-CP, Thông tư 34/2026/TT-BXD,
FIDIC White Book. Rule 8 Approval Matrix + mandatory AI disclaimer are appended.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_AGENTS_DIR = Path(__file__).resolve().parents[1]  # .agents/ (this file is in .agents/tools/)
_SHARED_CTX = _AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
_TOOLS_DIR = _AGENTS_DIR / "tools"
for _p in (str(_SHARED_CTX), str(_TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from docx import Document  # noqa: E402
from docx.shared import Pt, Inches, RGBColor, Cm  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
import design_tokens as dt  # noqa: E402

# --- Colors (from SSOT design_tokens; none are white; 12b-safe) -------------
_HEADER_BG = dt.HEADER_BG_SLATE          # DCE4EC light mineral slate
_HEADER_TXT = dt.HEADER_TEXT_DARK        # 1E3246 dark steel
_BODY_TXT = dt.TEXT_BODY                 # 1C1E21
_ALT_BG = dt.HEADER_BG_LIMESTONE        # EAE6DF limestone (alt data rows)
_BORDER = dt.BORDER_GRID                # D0CEC7 thin grid
_CRIT_BG, _CRIT_TX = dt.STATUS_FAIL_BG, dt.STATUS_FAIL_TEXT     # F9EBE8 / 8C261E
_MAJ_BG, _MAJ_TX = dt.STATUS_WARN_BG, dt.STATUS_WARN_TEXT       # FBF3E4 / 8F5314
_MIN_BG, _MIN_TX = dt.STATUS_INFO_BG, dt.STATUS_INFO_TEXT       # EDF3F5 / 1F4E5B

# --- Sizes (Rule 12e floor; keep float tokens — no truncation; all >= 10 pt) ---
_TITLE_PT = float(dt.WORD_LEGAL_TITLE_PT)      # 16
_H2_PT = float(dt.WORD_LEGAL_H2_PT)            # 13.5 (SSOT value, not truncated)
_BODY_PT = float(dt.WORD_LEGAL_BODY_PT)        # 13
_TBL_HDR_PT = float(dt.WORD_LEGAL_TBL_HDR_PT)  # 11.5
_TBL_BODY_PT = float(dt.WORD_LEGAL_TBL_BODY_PT)  # 11
_CAPTION_PT = float(dt.WORD_MIN_CAPTION_FLOOR_PT)  # 10
_FONT = dt.FONT_WORD_LEGAL  # Times New Roman

_SEV_STYLE = {
    "CRITICAL": (_CRIT_BG, _CRIT_TX),
    "MAJOR": (_MAJ_BG, _MAJ_TX),
    "MINOR": (_MIN_BG, _MIN_TX),
}


# ---------------------------------------------------------------------------
# Rule 12e helpers
# ---------------------------------------------------------------------------
_MATH_MAP = {
    "\\gamma_f": "γf", "\\gamma_F": "γf", "\\alpha": "α", "\\beta": "β",
    "\\mu": "μ", "\\Delta": "Δ", "\\varphi": "φ", "\\lambda": "λ",
    "\\pi": "π", "\\ge": "≥", "\\le": "≤", "\\times": "×", "\\implies": "⇒",
    "\\approx": "≈", "\\infty": "∞", "\\sum": "Σ",
    "A_{s}": "As", "As,req": "As,req", "R_b": "Rb", "Rb": "Rb",
    "m^2": "m²", "m^3": "m³", "kN/m^2": "kN/m²",
}


def _math_to_unicode(text: str) -> str:
    """Strip raw `$` and map common LaTeX macros to Unicode (Rule 12e Math Lock)."""
    if not text:
        return ""
    s = str(text)
    # Replace known macros first, then remove any remaining $ delimiters.
    for macro, uni in _MATH_MAP.items():
        s = s.replace(macro, uni)
    s = s.replace("$", "")
    return s


_BULLET_PREFIX = "•-–—* \t"


def _strip_bullet_prefix(text: str) -> str:
    """Auto-strip leading bullet glyphs so Word's own bullet never doubles up (Rule 12e.2)."""
    return _math_to_unicode(str(text).lstrip(_BULLET_PREFIX))


# ---------------------------------------------------------------------------
# Low-level doc helpers
# ---------------------------------------------------------------------------

def _rgb(hexstr: str) -> RGBColor:
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


def _set_cell_bg(cell, hexstr: str) -> None:
    """Apply a solid cell fill (Rule 12b — light fills only, never white text on dark).

    The string "auto" means "no fill" — the `w:shd` element is omitted entirely
    (writing `w:fill="AUTO"` is out-of-spec OOXML and breaks strict consumers).
    """
    if str(hexstr).lower() in ("auto", "", "none"):
        return
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexstr.upper())


def _set_cell_borders(cell, color_hex: str = _BORDER) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    from docx.oxml import OxmlElement
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), color_hex.upper())
        borders.append(b)
    tc_pr.append(borders)


def _set_par_border(paragraph, color_hex: str = _BORDER) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    from docx.oxml import OxmlElement
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:color"), color_hex.upper())
    pbdr.append(bottom)
    p_pr.append(pbdr)


def _style_cell(cell, text: str, size_pt: int, color_hex: str = _BODY_TXT,
                bold: bool = False, align: int = WD_ALIGN_PARAGRAPH.LEFT) -> None:
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(_strip_bullet_prefix(text))
    run.font.name = _FONT
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color_hex)
    _set_cell_borders(cell)


def _heading(doc: Document, text: str, size_pt: float, color_hex: str = _HEADER_TXT) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    run = p.add_run(_math_to_unicode(text))
    run.font.name = _FONT
    run.font.size = Pt(size_pt)
    run.font.bold = True
    run.font.color.rgb = _rgb(color_hex)
    _set_par_border(p)
    p.paragraph_format.space_after = Pt(4)


def _body(doc: Document, text: str, size_pt: float = _BODY_PT) -> None:
    p = doc.add_paragraph()
    run = p.add_run(_math_to_unicode(text))
    run.font.name = _FONT
    run.font.size = Pt(size_pt)
    run.font.color.rgb = _rgb(_BODY_TXT)
    p.paragraph_format.space_after = Pt(4)


def _add_item(doc: Document, text: str, prefix: str = "1. ") -> None:
    """Numbered/lettered list item: indented paragraph with an explicit prefix
    (Rule 12e.3 — NEVER `List Bullet`, which would render a stray '•')."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.75)
    run = p.add_run(prefix + _strip_bullet_prefix(text))
    run.font.name = _FONT
    run.font.size = Pt(_BODY_PT)
    run.font.color.rgb = _rgb(_BODY_TXT)


def _add_bullet(doc: Document, text: str) -> None:
    """Bullet item with Word's native bullet glyph + auto-stripped text (Rule 12e.2)."""
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(_strip_bullet_prefix(text))
    run.font.name = _FONT
    run.font.size = Pt(_BODY_PT)
    run.font.color.rgb = _rgb(_BODY_TXT)


def _embed_image(doc: Document, png_path: Optional[str], caption: str, width_in: float = 5.5) -> None:
    if not png_path or not Path(png_path).is_file():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(png_path), width=Inches(width_in))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = cap.add_run(_math_to_unicode(caption))
    c.font.name = _FONT
    c.font.size = Pt(_CAPTION_PT)  # >= 10 pt floor
    c.font.italic = True
    c.font.color.rgb = _rgb(dt.INK_MUTED)


# ---------------------------------------------------------------------------
# Document builders
# ---------------------------------------------------------------------------
_DISCLAIMER = (
    "Tài liệu do trợ lý AI lập tự động. Kết quả mang tính tham khảo, phải được "
    "kỹ sư có chứng chỉ hành nghề kiểm tra và chịu trách nhiệm trước khi dùng "
    "cho hồ sơ thiết kế, thi công hoặc thẩm tra."
)


def _base_doc(doc_type_vi: str, meta: Dict[str, Any]) -> Document:
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin = Cm(2.2)
        sec.right_margin = Cm(2.2)

    # Title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = t.add_run(doc_type_vi)
    tr.font.name = _FONT
    tr.font.size = Pt(_TITLE_PT)
    tr.font.bold = True
    tr.font.color.rgb = _rgb(_HEADER_TXT)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run(
        _math_to_unicode(
            f"Hệ thống pháp lý: Nghị định 175/2024/NĐ-CP · Thông tư 34/2026/TT-BXD · "
            f"FIDIC White Book — {meta.get('project', meta.get('model_id', ''))}"
        )
    )
    sr.font.name = _FONT
    sr.font.size = Pt(_H2_PT)
    sr.font.color.rgb = _rgb(dt.INK_SECONDARY)

    _heading(doc, "I. THÔNG TIN HỒ SƠ", _H2_PT)
    rows = [
        ("Mã công trình", meta.get("project", meta.get("model_id", ""))),
        ("Phiên bản mô hình", f"{meta.get('from_version', '')} → {meta.get('to_version', '')}"),
        ("Nguồn kiểm toán", "Bộ lọc 8 (dce_cad_compliance_checker) — 20 Cổng G8.01..G8.20"),
        ("Trạng thái kiểm toán", str(meta.get("audit_status", ""))),
        ("Loại tài liệu", doc_type_vi),
    ]
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (k, v) in enumerate(rows):
        _style_cell(tbl.cell(i, 0), k, _TBL_HDR_PT, color_hex=_HEADER_TXT, bold=True)
        _set_cell_bg(tbl.cell(i, 0), _HEADER_BG)
        _style_cell(tbl.cell(i, 1), v, _TBL_BODY_PT)
        _set_cell_bg(tbl.cell(i, 1), _ALT_BG if i % 2 == 0 else "auto")
    return doc


def _add_finding_table(doc: Document, title: str, records: List[Dict[str, Any]],
                       cols: List[tuple], sev_key: str = "severity") -> None:
    """Render a findings table. Header = light slate; the `sev_key` cell is tinted
    by severity; other data rows alternate white / limestone (Rule 12b, no white text)."""
    _heading(doc, title, _H2_PT)
    if not records:
        _body(doc, "Không có mục nào trong nhóm này (tương ứng kiểm toán đạt chuẩn).")
        return
    sev_col_idx = next((j for j, (_, ck) in enumerate(cols) if ck == sev_key), -1)
    table = doc.add_table(rows=1, cols=len(cols))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr = table.rows[0].cells
    for j, (cname, _) in enumerate(cols):
        _style_cell(hdr[j], cname, _TBL_HDR_PT, color_hex=_HEADER_TXT, bold=True,
                    align=WD_ALIGN_PARAGRAPH.LEFT)
        _set_cell_bg(hdr[j], _HEADER_BG)
    for i, rec in enumerate(records):
        row = table.add_row().cells
        sev = str(rec.get(sev_key, "MINOR")).upper()
        sev_bg, sev_tx = _SEV_STYLE.get(sev, _SEV_STYLE["MINOR"])
        alt_bg = _ALT_BG if i % 2 == 0 else "auto"
        for j, (_, key) in enumerate(cols):
            is_sev = j == sev_col_idx
            color = sev_tx if is_sev else _BODY_TXT
            bg = sev_bg if is_sev else alt_bg
            _style_cell(row[j], str(rec.get(key, "")), _TBL_BODY_PT, color_hex=color,
                       align=WD_ALIGN_PARAGRAPH.LEFT)
            _set_cell_bg(row[j], bg)


def _add_approval(doc: Document, doc_ref: str) -> None:
    _heading(doc, "III. KÝ DUYỆT & CHẾ TÀI (Approval Matrix)", _H2_PT)
    ap = doc.add_table(rows=4, cols=3)
    ap.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr = ["Vai trò", "Họ tên & chữ ký", "Ngày"]
    for j, h in enumerate(hdr):
        _style_cell(ap.cell(0, j), h, _TBL_HDR_PT, color_hex=_HEADER_TXT, bold=True)
        _set_cell_bg(ap.cell(0, j), _HEADER_BG)
    for i, role in enumerate(["Đơn vị TVTK (tác giả)", "Đơn vị Chủ đầu tư", "Đơn vị Thẩm tra"], start=1):
        _style_cell(ap.cell(i, 0), role, _TBL_BODY_PT, bold=True)
        _style_cell(ap.cell(i, 1), "Trợ lý AI — cần kỹ sư có chứng chỉ kiểm tra & xác nhận trước khi ký", _TBL_BODY_PT)
        _style_cell(ap.cell(i, 2), "", _TBL_BODY_PT)
        _set_cell_bg(ap.cell(i, 1), _ALT_BG if i % 2 == 0 else "auto")

    d = doc.add_paragraph()
    dr = d.add_run(_DISCLAIMER)
    dr.font.name = _FONT
    dr.font.size = Pt(_CAPTION_PT)
    dr.font.italic = True
    dr.font.color.rgb = _rgb(dt.INK_MUTED)


def _build_report(doc: Document, records: List[Dict[str, Any]], meta: Dict[str, Any],
                  crops: Dict[str, str], doc_type: str) -> Document:
    cols = [
        ("STT", "n"),
        ("Mã Cổng", "element_id"),
        ("Hạng mục / Cấu kiện", "field"),
        ("Mức độ", "severity"),
        ("Trạng thái", "status"),
        ("Mô tả lỗi & Biện pháp khắc phục", "reason"),
        ("Nguồn", "source"),
    ]
    for k, rec in enumerate(records, start=1):
        rec["n"] = k
    _add_finding_table(doc, f"II. DANH MỤC {doc_type} & BIỆN PHÁP KHẮC PHỤC", records, cols)

    # Embedded defect-crop evidence (spec §3.2.2: 300 DPI, balanced ratio).
    img_refs = [(g, crops[g]) for g in list(crops) if crops[g]]
    if img_refs:
        _heading(doc, "IV. BẰNG CHỨNG TRỰC QUAN CAD (Crop BBox 300 DPI)", _H2_PT)
        for gate, png in img_refs:
            _embed_image(doc, png, f"Hình {gate}: vùng lỗi CAD {gate} (crop Bounding Box, 300 DPI).", width_in=5.5)

    _add_approval(doc, meta.get("model_id", ""))
    return doc


def build_ncr_docx(ncrs: List[Dict[str, Any]], out_path: str,
                   meta: Optional[Dict[str, Any]] = None,
                   crop_pngs: Optional[Dict[str, str]] = None) -> Path:
    """Build the NCR (Biên bản không phù hợp) legal Word document."""
    meta = dict(meta or {})
    crop_pngs = crop_pngs or {}
    doc = _base_doc("BIÊN BẢN NCR (NON-CONFORMANCE REPORT)", meta)
    _build_report(doc, ncrs, meta, crop_pngs, "NCR")
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(p))
    return p


def build_rfi_docx(rfis: List[Dict[str, Any]], out_path: str,
                   meta: Optional[Dict[str, Any]] = None,
                   crop_pngs: Optional[Dict[str, str]] = None) -> Path:
    """Build the RFI (Phiếu yêu cầu thông tin) legal Word document."""
    meta = dict(meta or {})
    crop_pngs = crop_pngs or {}
    doc = _base_doc("PHIẾU RFI (REQUEST FOR INFORMATION)", meta)
    cols = [
        ("STT", "n"), ("Mã Cổng", "gate_id"), ("Hạng mục", "gate_name"),
        ("Mức độ", "severity"), ("Câu hỏi / RFI", "question"),
        ("Hành động yêu cầu", "requested_action"), ("Căn cứ", "legal_basis"),
    ]
    for k, rec in enumerate(rfis, start=1):
        rec["n"] = k
    _add_finding_table(doc, "II. DANH MỤC RFI", rfis, cols)
    img_refs = [(g, crop_pngs[g]) for g in list(crop_pngs) if crop_pngs[g]]
    if img_refs:
        _heading(doc, "III. BẰNG CHỨNG TRỰC QUAN CAD", _H2_PT)
        for gate, png in img_refs:
            _embed_image(doc, png, f"Hình {gate}: vùng CAD liên quan RFI {gate} (300 DPI).", width_in=5.5)
    _add_approval(doc, meta.get("model_id", ""))
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(p))
    return p


def generate_report_docx(ncrs: List[Dict[str, Any]], rfis: List[Dict[str, Any]], out_path: str,
                         meta: Optional[Dict[str, Any]] = None,
                         crop_pngs: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Emit both NCR + RFI documents when present; returns their paths."""
    out = {"ncr": None, "rfi": None}
    if ncrs:
        out["ncr"] = str(build_ncr_docx(ncrs, out_path, meta, crop_pngs))
    if rfis:
        rfi_path = str(Path(out_path).with_name(Path(out_path).stem + "_RFI.docx"))
        out["rfi"] = str(build_rfi_docx(rfis, rfi_path, meta, crop_pngs))
    return out


if __name__ == "__main__":
    import json as _json
    print("usage: import rfi_ncr_docx_generator; build_ncr_docx(ncrs, path)")
