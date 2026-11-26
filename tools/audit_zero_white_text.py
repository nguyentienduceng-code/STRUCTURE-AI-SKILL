#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_zero_white_text.py (v2.1) — Công cụ Kiểm toán Tự động Điều 12b & Điều 12e AGENTS.md
  1. Điều 12b (Zero White Text Lock): Cấm tuyệt đối chữ trắng (#FFFFFF / RGBColor(255,255,255)) trong bảng biểu.
  2. Điều 12e (Typography Floor Lock): Cấm tuyệt đối cỡ chữ Word/Excel siêu nhỏ (< 10.0pt: Pt(8), Pt(8.5), Pt(9), Pt(9.5), size=8.5, size=9.0, size=9.5).
"""

import os
import re
import sys
from typing import Dict, Any, List

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SKIP_DIRS = {
    ".git", "_deprecated", "_archive", "_ARCHIVE_BACKUP_20261022",
    "__pycache__", ".pytest_cache", "references", ".npm", "node_modules",
}

FORBIDDEN_PATTERNS = [
    (r'RGBColor\s*\(\s*255\s*,\s*255\s*,\s*255\s*\)', "Điều 12b: RGBColor(255, 255, 255)"),
    (r'RGBColor\s*\(\s*0xFF\s*,\s*0xFF\s*,\s*0xFF\s*\)', "Điều 12b: RGBColor(0xFF, 0xFF, 0xFF)"),
    (r'header_text_color\s*[:=]\s*.FFFFFF.', "Điều 12b: header_text_color='FFFFFF'"),
    (r'text_color\s*=\s*.FFFFFF.', "Điều 12b: text_color='FFFFFF'"),
    (r'color\s*=\s*.FFFFFF.', "Điều 12b: color='FFFFFF'"),
    (r'color_hex\s*=\s*WHITE\b', "Điều 12b: color_hex=WHITE"),
    (r'fill\s*=\s*\(\s*255\s*,\s*255\s*,\s*255\s*\)', "Điều 12b: PIL draw.text fill=(255,255,255)"),
    (r"font\.size\s*=\s*Pt\(\s*(?:7|8|8\.5|9|9\.0|9\.5)\s*\)", "Điều 12e: Word Font < 10.0pt"),
    (r'size_pt\s*=\s*(?:7|8|8\.5|9|9\.0|9\.5)\b', "Điều 12e: Word size_pt < 10.0pt"),
    (r'Font\([^)]*\bsize\s*=\s*(?:7|8|8\.5|9|9\.0|9\.5)\b', "Điều 12e: Excel Font size < 10.0pt"),
]


def _source_findings(fp, rel_p):
    violations = []
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for line_no, line in enumerate(lines, 1):
        # Bỏ qua các dòng comment hoặc thuyết minh quy tắc cấm lỗi cũ trong .md/.py
        line_low = line.lower()
        if any(k in line_low for k in ["cấu hình cũ", "đã loại bỏ", "cấm", "before", "trước"]):
            continue
        for pat, desc in FORBIDDEN_PATTERNS:
            if re.search(pat, line):
                violations.append({
                    "file": rel_p,
                    "line": line_no,
                    "pattern": desc,
                    "snippet": line.strip()[:120],
                })

    return violations


def scan_agents_directory(root_dir: str) -> Dict[str, Any]:
    violations: List[Dict[str, Any]] = []
    files_scanned = 0
    skill_counts: Dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.lower().startswith("_archive")
        ]
        for fn in sorted(filenames):
            if not fn.endswith((".py", ".md")):
                continue
            if fn == "audit_zero_white_text.py" or "_OLD" in fn or fn.startswith("test_"):
                continue
            fp = os.path.join(dirpath, fn)
            rel_p = os.path.relpath(fp, root_dir)
            files_scanned += 1
            parts = rel_p.split(os.sep)
            group = parts[1] if (len(parts) > 1 and parts[0] == "skills") else parts[0]
            skill_counts[group] = skill_counts.get(group, 0) + 1

            violations.extend(_source_findings(fp, rel_p))

    return {
        "root_dir": root_dir,
        "files_scanned": files_scanned,
        "skill_groups_scanned": skill_counts,
        "warnings_count": len(violations),
        "violations": violations,
        "status": "PASS (0 WARNINGS)" if len(violations) == 0 else "FAIL",
    }


def audit_file(path):
    """Inspect a single edited source or report without scanning neighbouring files."""
    from pathlib import Path
    from zipfile import ZipFile
    from xml.etree import ElementTree as ET

    path = Path(path)
    ext = path.suffix.lower()
    if ext in {".py", ".md"}:
        return [f"{v['line']}: {v['pattern']}" for v in _source_findings(path, path.name)]
    if ext == ".pdf":
        import fitz
        with fitz.open(path) as pdf:
            return [f"Trang {page.number + 1}: chữ trắng" for page in pdf
                    if any(span.get("color") == 0xffffff and span["text"].strip()
                           for block in page.get_text("dict")["blocks"] for line in block.get("lines", [])
                           for span in line["spans"])]
    findings = []
    with ZipFile(path) as package:
        if ext == ".docx":
            w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            def attr(node, name):
                return node.get(w + name, "") if node is not None else ""
            styles = {}
            if "word/styles.xml" in package.namelist():
                styles = {attr(node, "styleId"): node for node in
                          ET.fromstring(package.read("word/styles.xml")).findall(w + "style")}
            def style_colors(key):
                seen = set()
                while key in styles and key not in seen:
                    seen.add(key)
                    node = styles[key]
                    yield node.find(w + "rPr/" + w + "color")
                    key = attr(node.find(w + "basedOn"), "val")
            for name in package.namelist():
                if not re.fullmatch(r"word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml", name):
                    continue
                doc = ET.fromstring(package.read(name))
                for para in doc.iter(w + "p"):
                    pstyle = attr(para.find(w + "pPr/" + w + "pStyle"), "val") or "Normal"
                    for run in para.iter(w + "r"):
                        if not any(t.text and t.text.strip() for t in run.iter(w + "t")):
                            continue
                        rstyle = attr(run.find(w + "rPr/" + w + "rStyle"), "val")
                        colors = [run.find(w + "rPr/" + w + "color"), *style_colors(rstyle), *style_colors(pstyle)]
                        color = next((c for c in colors if c is not None), None)
                        if attr(color, "val").upper() == "FFFFFF":
                            findings.append(f"{name}: chữ trắng")
        elif ext == ".xlsx":
            ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
            if "xl/styles.xml" in package.namelist():
                styles = ET.fromstring(package.read("xl/styles.xml"))
                fonts = styles.findall(ns + "fonts/" + ns + "font")
                formats = styles.findall(ns + "cellXfs/" + ns + "xf")
                for name in package.namelist():
                    if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
                        for cell in ET.fromstring(package.read(name)).iter(ns + "c"):
                            if not len(cell) or not formats:
                                continue
                            font = fonts[int(formats[int(cell.get("s", 0))].get("fontId", 0))]
                            color = font.find(ns + "color")
                            if color is not None and color.get("rgb", "").upper()[-6:] == "FFFFFF":
                                findings.append(f"{name} {cell.get('r')}: chữ trắng")
    return findings


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if os.path.isfile(target):
        errors = audit_file(target)
        print("\n".join(errors) if errors else "PASS")
        sys.exit(int(bool(errors)))
    rep = scan_agents_directory(target)
    print(f"[AUDIT ĐIỀU 12B & 12E v2.1] Scanned {rep['files_scanned']} files across {len(rep['skill_groups_scanned'])} modules -> Warnings: {rep['warnings_count']} | Status: {rep['status']}")
    if rep["violations"]:
        for v in rep["violations"]:
            print(f"  [!] {v['file']}:{v['line']} ({v['pattern']}): {v['snippet']}")
        sys.exit(1)
