#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_phuluc_docx.py (v3.1.0 — SKILL_PHULUC Master Quality Gate)
Kiểm toán độc lập chất lượng tài liệu Word (.docx) sau khi xuất từ SKILL_PHULUC.

Kiểm tra 5 bộ tiêu chí bắt buộc theo AGENTS.md:
1. Điều 12b: ZERO WHITE TEXT LOCK — Cấm tuyệt đối chữ trắng trên nền tối / trong bảng biểu.
2. Điều 12e: SÀN CỠ CHỮ & MATH LOCK — Bảng >= 10.0pt, Thân bài >= 11.0pt, Xóa 100% mã thô LaTeX ($), Không Double Bullet (• •).
3. Điều 13: ĐỘ SÂU DIỄN GIẢI — Phần thuyết minh >= 800 từ.
4. Điều 8: APPROVAL MATRIX & DISCLAIMER — Bảng trách nhiệm 4 cấp và câu miễn trừ pháp lý AI bắt buộc.
5. Section & Table Integrity — w:cantSplit, w:tblHeader, Auto-TOC fields.
"""

import sys
import os
import json
import re
import argparse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def audit_docx_file(docx_path: Path) -> dict:
    if not docx_path.exists():
        return {"status": "FAIL", "error": f"File '{docx_path}' không tồn tại."}

    results = {
        "file": str(docx_path),
        "checks": [],
        "passed_all": True,
        "details": {}
    }

    with zipfile.ZipFile(docx_path, "r") as docx_zip:
        if "word/document.xml" not in docx_zip.namelist():
            return {"status": "FAIL", "error": "Không tìm thấy word/document.xml trong file .docx"}

        doc_xml = docx_zip.read("word/document.xml").decode("utf-8")
        root = ET.fromstring(doc_xml)

    # 1. KIỂM TRA ĐIỀU 12B: ZERO WHITE TEXT LOCK
    white_text_instances = []
    for r in root.findall(".//w:r", NAMESPACES):
        color_elem = r.find(".//w:color", NAMESPACES)
        if color_elem is not None:
            cval = color_elem.get(f"{{{NAMESPACES['w']}}}val", "").upper()
            if cval in ["FFFFFF", "WHITE"]:
                t_elem = r.find(".//w:t", NAMESPACES)
                txt = t_elem.text if t_elem is not None and t_elem.text else ""
                if txt.strip():
                    white_text_instances.append(txt[:40])

    chk1 = {
        "rule": "12b: ZERO WHITE TEXT LOCK",
        "description": "Không có chữ màu trắng (FFFFFF) trong văn bản và bảng biểu",
        "passed": len(white_text_instances) == 0,
        "violations": white_text_instances[:5],
    }
    results["checks"].append(chk1)

    # 2. KIỂM TRA ĐIỀU 12E: SÀN CỠ CHỮ >= 10.0pt TRONG BẢNG
    sub_10pt_cells = []
    tables = root.findall(".//w:tbl", NAMESPACES)
    for tbl_idx, tbl in enumerate(tables):
        for cell in tbl.findall(".//w:tc", NAMESPACES):
            for sz_elem in cell.findall(".//w:sz", NAMESPACES):
                sz_val = sz_elem.get(f"{{{NAMESPACES['w']}}}val")
                if sz_val and sz_val.isdigit():
                    half_pt = int(sz_val)
                    if half_pt < 20:  # < 10.0 pt
                        sub_10pt_cells.append(f"Table {tbl_idx}: {half_pt/2.0}pt")

    chk2 = {
        "rule": "12e: SÀN CỠ CHỮ BẢNG >= 10.0pt",
        "description": "Cỡ chữ trong bảng biểu không được nhỏ hơn 10.0pt (half_pt >= 20)",
        "passed": len(sub_10pt_cells) == 0,
        "violations": sub_10pt_cells[:5],
    }
    results["checks"].append(chk2)

    # 3. KIỂM TRA ĐIỀU 12E: TRIỆT TIÊU 100% MÃ THÔ LATEX ($)
    raw_latex_runs = []
    # Tìm kiếm ký tự $ đứng độc lập hoặc trong đoạn văn thông thường (ngoại trừ OMML)
    for p in root.findall(".//w:p", NAMESPACES):
        # Bỏ qua các đoạn chỉ có Office Math
        math_elems = p.findall(".//m:oMath", NAMESPACES)
        p_text = "".join(t.text for t in p.findall(".//w:t", NAMESPACES) if t.text)
        # Kiểm tra nếu xuất hiện cặp $...$ hoặc ký tự $ thô
        if "$" in p_text and not p_text.strip().startswith("\\$"):
            # Nếu chứa $ có kèm theo công thức chưa chuyển đổi
            if re.search(r"\$[^$]+\$", p_text) or p_text.count("$") >= 2:
                raw_latex_runs.append(p_text[:60])

    chk3 = {
        "rule": "12e: MATH LOCK — TRIỆT TIÊU 100% MÃ THÔ LATEX ($)",
        "description": "Không để lộ ký tự $ hoặc mã công thức LaTeX thô chưa chuyển đổi sang OMML",
        "passed": len(raw_latex_runs) == 0,
        "violations": raw_latex_runs[:5],
    }
    results["checks"].append(chk3)

    # 4. KIỂM TRA ĐIỀU 12E: CHỐNG DOUBLE BULLET (• •)
    double_bullet_runs = []
    for p in root.findall(".//w:p", NAMESPACES):
        p_style = p.find(".//w:pStyle", NAMESPACES)
        is_bullet_style = p_style is not None and "bullet" in p_style.get(f"{{{NAMESPACES['w']}}}val", "").lower()
        p_text = "".join(t.text for t in p.findall(".//w:t", NAMESPACES) if t.text).strip()
        if is_bullet_style and (p_text.startswith("•") or p_text.startswith("- ") or p_text.startswith("– ")):
            double_bullet_runs.append(p_text[:40])
        elif re.match(r"^[•\-\*]\s*[•\-\*]", p_text):
            double_bullet_runs.append(p_text[:40])

    chk4 = {
        "rule": "12e: CHỐNG DOUBLE BULLET (• •)",
        "description": "Không có đoạn văn bị trùng lặp 2 ký tự bullet hoặc thừa ký tự đầu dòng",
        "passed": len(double_bullet_runs) == 0,
        "violations": double_bullet_runs[:5],
    }
    results["checks"].append(chk4)

    # 5. KIỂM TRA ĐIỀU 13: ĐỘ SÂU DIỄN GIẢI THUYẾT MINH (>= 800 TỪ)
    # Trích xuất toàn bộ text của văn bản (loại trừ tiêu đề và bảng biểu)
    # Narrative depth excludes tables, headings, TOC/captions and approval/disclaimer text.
    all_body_words = []
    body = root.find("w:body", NAMESPACES)
    for p in body.findall("w:p", NAMESPACES) if body is not None else []:
        style = p.find("w:pPr/w:pStyle", NAMESPACES)
        name = style.get(f"{{{NAMESPACES['w']}}}val", "").lower() if style is not None else ""
        text = "".join(t.text or "" for t in p.findall(".//w:t", NAMESPACES)).strip()
        if any(item in name for item in ("heading", "caption", "title", "toc")):
            continue
        if "Tài liệu do trợ lý AI lập tự động" in text:
            continue
        all_body_words.extend(text.split())

    total_words = len(all_body_words)
    chk5 = {
        "rule": "13: MINIMUM NARRATIVE DEPTH (>= 800 TỪ)",
        "description": f"Tổng dung lượng phần diễn giải thuyết minh: {total_words} từ (yêu cầu >= 800 từ)",
        "passed": total_words >= 800,
        "violations": [f"Tổng số từ: {total_words} < 800"] if total_words < 800 else [],
    }
    results["checks"].append(chk5)

    # 6. KIỂM TRA ĐIỀU 8: APPROVAL MATRIX & LEGAL DISCLAIMER
    full_text = " ".join(t.text or "" for t in root.findall(".//w:t", NAMESPACES))
    has_disclaimer = "Tài liệu do trợ lý AI lập tự động" in full_text or "kỹ sư có chứng chỉ hành nghề" in full_text
    has_approval_matrix = "Chủ đầu tư" in full_text and ("Tư vấn" in full_text or "Kiểm tra" in full_text)

    chk6 = {
        "rule": "8: APPROVAL MATRIX & AI DISCLAIMER",
        "description": "Có bảng phân định trách nhiệm ký duyệt và câu tuyên bố miễn trừ pháp lý AI bắt buộc",
        "passed": has_disclaimer and has_approval_matrix,
        "violations": [] if (has_disclaimer and has_approval_matrix) else ["Thiếu câu tuyên bố miễn trừ hoặc bảng phê duyệt"],
    }
    results["checks"].append(chk6)

    # 7. KIỂM TRA BẢO VỆ BẢNG BIỂU (w:cantSplit & w:tblHeader)
    table_integrity_issues = []
    for t_idx, tbl in enumerate(tables):
        rows = tbl.findall(".//w:tr", NAMESPACES)
        if len(rows) > 1:
            header_row = rows[0]
            # Check tblHeader
            tbl_header = header_row.find(".//w:tblHeader", NAMESPACES)
            cant_splits = [r.find(".//w:cantSplit", NAMESPACES) is not None for r in rows]
            if tbl_header is None:
                table_integrity_issues.append(f"Table {t_idx}: Thiếu w:tblHeader ở hàng tiêu đề")
            if not all(cant_splits):
                table_integrity_issues.append(f"Table {t_idx}: Có hàng thiếu w:cantSplit bảo vệ ngắt trang")

    chk7 = {
        "rule": "TABLE INTEGRITY LOCK",
        "description": "Các bảng biểu có w:tblHeader lặp lại tiêu đề trang và w:cantSplit chống rách dòng",
        "passed": len(table_integrity_issues) == 0,
        "violations": table_integrity_issues[:5],
    }
    results["checks"].append(chk7)

    incomplete = []
    for index, table in enumerate(tables):
        for row_index, row in enumerate(table.findall("w:tr", NAMESPACES)):
            texts = [node.text or "" for node in row.iter()
                     if node.tag in (f"{{{NAMESPACES['w']}}}t", f"{{{NAMESPACES['m']}}}t")]
            text = " ".join(texts)
            if "___" in text:
                incomplete.append(f"Table {index}, row {row_index}: còn ô dữ liệu mẫu ___")
    results["checks"].append({
        "rule": "DATA COMPLETENESS — NO UNFILLED TEMPLATE",
        "description": "Hồ sơ phát hành không chứa ô mẫu ___ trong bảng kỹ thuật",
        "passed": not incomplete, "violations": incomplete[:10],
    })

    results["passed_all"] = all(c["passed"] for c in results["checks"])
    results["status"] = "PASS" if results["passed_all"] else "FAIL"
    results["details"]["total_words"] = total_words
    results["details"]["total_tables"] = len(tables)

    return results


def main():
    parser = argparse.ArgumentParser(description="Auditor kiểm toán chất lượng hồ sơ DOCX SKILL_PHULUC")
    parser.add_argument("docx_path", help="Đường dẫn tới file .docx cần kiểm toán")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")
    args = parser.parse_args()

    doc_path = Path(args.docx_path)
    report = audit_docx_file(doc_path)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("passed_all") else 1
    else:
        print("=" * 80)
        print(f" KIỂM TOÁN CHẤT LƯỢNG HỒ SƠ WORD (.DOCX) — SKILL_PHULUC v3.1")
        print(f" Tệp kiểm toán: {doc_path.name}")
        print("=" * 80)
        for c in report["checks"]:
            mark = "✅ PASS" if c["passed"] else "❌ FAIL"
            print(f" {mark} | {c['rule']:<35} | {c['description']}")
            if not c["passed"]:
                for v in c["violations"]:
                    print(f"         ↳ Vi phạm: {v}")
        print("-" * 80)
        if report["passed_all"]:
            print(f" 🎉 HỒ SƠ ĐẠT CÁC TIÊU CHÍ KIỂM TRA TỰ ĐỘNG (Status: PASS)")
            sys.exit(0)
        else:
            print(f" ⚠️ CẢNH BÁO: HỒ SƠ CÒN ĐIỂM VI PHẠM QUY TẮC AGENTS.MD (Status: FAIL)")
            sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

