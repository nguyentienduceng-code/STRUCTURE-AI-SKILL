#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_zero_white_text.py (v2.0) — Công cụ Kiểm toán Tự động Điều 12b & Điều 12c AGENTS.md
  1. Điều 12b (Zero White Text Lock): Cấm tuyệt đối chữ trắng (#FFFFFF / RGBColor(255,255,255)) trong bảng biểu.
  2. Điều 12c (Typography Floor Lock): Cấm tuyệt đối cỡ chữ Word/Excel siêu nhỏ (< 10.0pt: Pt(8), Pt(8.5), Pt(9), Pt(9.5), size=8.5, size=9.0, size=9.5).
"""

import os
import re
import sys
from typing import Dict, Any, List

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

FORBIDDEN_PATTERNS = [
    (r'RGBColor\s*\(\s*255\s*,\s*255\s*,\s*255\s*\)', "Điều 12b: RGBColor(255, 255, 255)"),
    (r'RGBColor\s*\(\s*0xFF\s*,\s*0xFF\s*,\s*0xFF\s*\)', "Điều 12b: RGBColor(0xFF, 0xFF, 0xFF)"),
    (r'header_text_color\s*[:=]\s*.FFFFFF.', "Điều 12b: header_text_color='FFFFFF'"),
    (r'text_color\s*=\s*.FFFFFF.', "Điều 12b: text_color='FFFFFF'"),
    (r'color\s*=\s*.FFFFFF.', "Điều 12b: color='FFFFFF'"),
    (r'color_hex\s*=\s*WHITE\b', "Điều 12b: color_hex=WHITE"),
    (r'fill\s*=\s*\(\s*255\s*,\s*255\s*,\s*255\s*\)', "Điều 12b: PIL draw.text fill=(255,255,255)"),
    (r"font\.size\s*=\s*Pt\(\s*(?:7|8|8\.5|9|9\.0|9\.5)\s*\)", "Điều 12c: Word Font < 10.0pt"),
    (r'size_pt\s*=\s*(?:7|8|8\.5|9|9\.0|9\.5)\b', "Điều 12c: Word size_pt < 10.0pt"),
    (r'Font\([^)]*\bsize\s*=\s*(?:7|8|8\.5|9|9\.0|9\.5)\b', "Điều 12c: Excel Font size < 10.0pt"),
]


def scan_agents_directory(root_dir: str) -> Dict[str, Any]:
    violations: List[Dict[str, Any]] = []
    files_scanned = 0
    skill_counts: Dict[str, int] = {}

    for dirpath, _, filenames in os.walk(root_dir):
        if "_deprecated" in dirpath or "_archive" in dirpath or "__pycache__" in dirpath:
            continue
        for fn in sorted(filenames):
            if not fn.endswith((".py", ".md")):
                continue
            fp = os.path.join(dirpath, fn)
            rel_p = os.path.relpath(fp, root_dir)
            if fn == "audit_zero_white_text.py":
                continue
            files_scanned += 1
            parts = rel_p.split(os.sep)
            group = parts[1] if (len(parts) > 1 and parts[0] == "skills") else parts[0]
            skill_counts[group] = skill_counts.get(group, 0) + 1

            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, 1):
                # Bỏ qua các dòng comment hoặc thuyết minh lịch sử đối chiếu lỗi cũ trong .md
                if any(k in line for k in ["Cấu hình cũ", "Đã loại bỏ", "cấm", "Cấm", "Before", "Trước"]):
                    continue
                for pat, desc in FORBIDDEN_PATTERNS:
                    if re.search(pat, line):
                        violations.append({
                            "file": rel_p,
                            "line": line_no,
                            "pattern": desc,
                            "snippet": line.strip()[:120],
                        })

    return {
        "root_dir": root_dir,
        "files_scanned": files_scanned,
        "skill_groups_scanned": skill_counts,
        "warnings_count": len(violations),
        "violations": violations,
        "status": "PASS (0 WARNINGS)" if len(violations) == 0 else "FAIL",
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rep = scan_agents_directory(target)
    print(f"[AUDIT ĐIỀU 12B & 12C v2.0] Scanned {rep['files_scanned']} files across {len(rep['skill_groups_scanned'])} modules -> Warnings: {rep['warnings_count']} | Status: {rep['status']}")
    if rep["violations"]:
        for v in rep["violations"]:
            print(f"  [!] {v['file']}:{v['line']} ({v['pattern']}): {v['snippet']}")
        sys.exit(1)
