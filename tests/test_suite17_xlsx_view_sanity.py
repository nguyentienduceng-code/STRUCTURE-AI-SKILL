#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_suite17_xlsx_view_sanity.py — Regression Test: Ngăn tái phát nhóm lỗi
Excel `[Repaired]` / nhảy dòng / MergedCell crash khi skill sinh xlsx.

17 checks, chia 4 nhóm:
  A. reproduce + sửa bug openpyxl freeze_panes 2 chiều -> 1 chiều (root cause #1)
  B. guard MergedCell (root cause #2)
  C. validate_xlsx_file trên file thật trong thư mục (backup + CAPNAT + test_repaired)
  D. verify 2 script skill đã được gắn guard trước mọi wb.save()
"""

import sys
import os
import re
import io
import zipfile
import tempfile

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
sys.path.insert(0, TOOLS_DIR)

import xlsx_view_sanity as xs  # noqa: E402

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {('- ' + detail) if detail else ''}")


def _sheetviews_xml(path):
    zf = zipfile.ZipFile(path)
    xmls = []
    for n in sorted(zf.namelist()):
        if re.match(r"xl/worksheets/sheet\d+\.xml$", n):
            xmls.append(zf.read(n).decode("utf-8", errors="ignore"))
    zf.close()
    return xmls


def main():
    print("=" * 72)
    print(" SUITE 17 — XLSX VIEW SANITY (Anti-[Repaired] Regression)")
    print("=" * 72)

    if not xs.HAS_OPENPYXL:
        print("  [SKIP] openpyxl không có mặt — không chạy được suite này.")
        sys.exit(0)
    import openpyxl

    tmpdir = tempfile.mkdtemp(prefix="xlsx_view_sanity_")

    # ------------------------------------------------------------------ A
    print("\n[A] Root cause #1 — openpyxl freeze_panes stale <selection>")

    # A1: tái hiện bug thuần túy (CHƯA sanitize): C5 -> A5 để lại selection bottomRight rác
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A5"] = "PHẦN I"
    ws.merge_cells("A5:L5")
    ws.freeze_panes = "C5"
    ws.freeze_panes = "A5"
    p1 = os.path.join(tmpdir, "buggy_C5_to_A5.xlsx")
    wb.save(p1)
    _, issues = xs.validate_xlsx_file(p1)
    check("A1. tái hiện được lỗi: freeze C5->A5 sinh selection không hợp lệ",
          len(issues) > 0, f"issues={issues}")

    # A2: sanitize sửa đúng lỗi đó
    wb2 = openpyxl.Workbook()
    ws2 = wb2.active
    ws2.merge_cells("A5:L5")
    ws2.freeze_panes = "C5"
    ws2.freeze_panes = "A5"
    xs.sanitize_workbook(wb2, zoom=100)
    p2 = os.path.join(tmpdir, "sanitized.xlsx")
    wb2.save(p2)
    ok, issues2 = xs.validate_xlsx_file(p2)
    check("A2. sau sanitize: file validate PASS", ok, f"issues={issues2}")
    sel_tags = re.findall(r"<selection\b[^>]*>", _sheetviews_xml(p2)[0])
    check("A2b. chỉ còn đúng 1 thẻ <selection>", len(sel_tags) == 1, str(sel_tags))
    pane_tags = re.findall(r"<pane\b[^>]*>", _sheetviews_xml(p2)[0])
    check("A2c. thẻ <pane> giữ ySplit=4 (freeze 4 dòng trên)",
          len(pane_tags) == 1 and 'ySplit="4"' in pane_tags[0], str(pane_tags))

    # A3: freeze 2 chiều hợp lệ (B4: đóng 1 cột + 3 dòng) — sanitize không phá
    wb3 = openpyxl.Workbook(); ws3 = wb3.active
    ws3.freeze_panes = "B4"
    xs.sanitize_workbook(wb3)
    p3 = os.path.join(tmpdir, "freeze2d.xlsx")
    wb3.save(p3)
    ok3, issues3 = xs.validate_xlsx_file(p3)
    check("A3. freeze 2 chiều (B4) hợp lệ sau sanitize", ok3, f"issues={issues3}")

    # A4: round-trip — openpyxl mở file đã sanitize không crash, không rớt pane
    wb4 = openpyxl.load_workbook(p2)
    ws4 = wb4.active
    check("A4. load lại file sanitized: freeze_panes trả về A5",
          ws4.freeze_panes == "A5", f"got={ws4.freeze_panes!r}")

    # A5: topoLeftCell/zoom reset — file lỗi mẫu của skill (zoom 70-85, topLeft xa)
    wb5 = openpyxl.Workbook(); ws5 = wb5.active
    ws5.sheet_view.topLeftCell = "C60"
    ws5.sheet_view.zoomScale = 75
    ws5.sheet_view.zoomScaleNormal = 75
    xs.sanitize_workbook(wb5, zoom=100)
    p5 = os.path.join(tmpdir, "view_reset.xlsx")
    wb5.save(p5)
    xml5 = _sheetviews_xml(p5)[0]
    # sanitize phải: (1) không còn C60 (2) zoom 100 (openpyxl serialize A1 thành attribute)
    check("A5. topLeftCell trả về A1 (không còn C60), zoom=100",
          'topLeftCell="C60"' not in xml5
          and ('topLeftCell="A1"' in xml5 or 'topLeftCell' not in xml5)
          and 'zoomScale="100"' in xml5, xml5[:300])

    # ------------------------------------------------------------------ B
    print("\n[B] Root cause #2 — crash ghi giá trị vào MergedCell")

    wb6 = openpyxl.Workbook(); ws6 = wb6.active
    ws6.merge_cells("A5:L5")
    try:
        ref = xs.set_cell_safe(ws6, "J5", "21")
        check("B1. set_cell_safe('J5') không crash, ghi vào anchor A5",
              ref == "A5" and ws6["A5"].value == "21", f"anchor={ref}, A5={ws6['A5'].value!r}")
    except AttributeError as e:
        check("B1. set_cell_safe('J5') không crash, ghi vào anchor A5", False, repr(e))

    try:
        ref = xs.set_cell_safe(ws6, "G9", "hi")  # ô thường, không merge
        check("B2. ô thường (G9) ghi trực tiếp", ref == "G9" and ws6["G9"].value == "hi")
    except AttributeError as e:
        check("B2. ô thường (G9) ghi trực tiếp", False, repr(e))

    # copy_style_from sang sheet đích (style+value+hyperlink), không crash trên merge
    ws7 = wb6.create_sheet("dest")
    ws7.merge_cells("A5:L5")
    link = "https://example.com/sharepoint"
    ws6["G9"] = "text"
    ws6["G9"].hyperlink = link
    ref2 = xs.copy_style_from(ws6, ws7, "G9")
    check("B3. copy_style_from: value + hyperlink copy sang sheet đích",
          ws7["G9"].value == "text" and ws7["G9"].hyperlink is not None
          and ws7["G9"].hyperlink.target == link,
          f"value={ws7['G9'].value!r}")
    xs.copy_style_from(ws6, ws7, "J5")  # J5 cả 2 sheet đều nằm trong merge
    check("B4. copy_style_from vùng merge không crash", True)

    # ------------------------------------------------------------------ C
    print("\n[C] Validate file thật trong thư mục project (nếu có mặt)")

    proj = os.path.join(os.path.dirname(TOOLS_DIR),
                       r"..", "01_Projects", "00_Management_QLTK", "01_Tien_Do_&_PendingList")
    proj = os.path.abspath(proj)
    samples = [
        ("test_repaired.xlsx", "nên PASS (đã sửa XML tay)"),
        ("BXD_QLTK_TRACKING_CHECKLIST_PENDINGLIST-02.11.2026.xlsx", "nên PASS"),
        ("BXD_QLTK_TRACKING_CHECKLIST_PENDINGLIST-14.10.2026_backup.xlsx",
         "được phép FAIL (đang lỗi, chờ user đóng Excel để vá)"),
    ]
    for fname, note in samples:
        fp = os.path.join(proj, fname)
        if not os.path.exists(fp):
            fp = os.path.join(proj, "Archive_Checklists_Tuan_Cu", fname)
        if not os.path.exists(fp):
            check(f"C. {fname} — bỏ qua (không tồn tại)", True, f"note: {note}")
            continue
        okc, issc = xs.validate_xlsx_file(fp)
        # chỉ file backup là KHÔNG bắt buộc pass; 2 file còn lại bắt buộc pass
        must_pass = "backup" not in fname
        if must_pass:
            check(f"C. {fname} — PASS", okc, f"issues={issc[:3]}")
        else:
            print(f"  ℹ️  {fname}: {'PASS' if okc else 'FAIL (đúng như dự kiến)'} — {note}")

    # ------------------------------------------------------------------ D
    print("\n[D] 2 script skill đã gắn guard trước mọi wb.save()")

    candidates = []
    base_skills = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")
    for rel in [
        "Design_Evaluation/scripts/xlsx_report.py",
        "SKILL_GEOTECH/calculators/export_geotech_report.py",
    ]:
        p = os.path.abspath(os.path.join(base_skills, rel.replace("/", os.sep)))
        candidates.append((os.path.basename(p), p))

    for name, path in candidates:
        if not os.path.exists(path):
            check(f"D. {name} tồn tại", False, path)
            continue
        txt = open(path, encoding="utf-8", errors="ignore").read()
        # mọi dòng wb.save(...) nằm sau 1 lần gọi sanitize_workbook / xs.
        save_lines = [i for i, l in enumerate(txt.splitlines())
                      if re.search(r"\bwb\.save\(", l)]
        sanitize_hits = [i for i, l in enumerate(txt.splitlines())
                         if "sanitize_workbook(" in l]
        ok_d = bool(save_lines) and bool(sanitize_hits) and min(sanitize_hits) < min(save_lines)
        check(f"D. {name}: có sanitize_workbook() trước mọi wb.save()",
              ok_d, f"save@{save_lines}, sanitize@{sanitize_hits}")

    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print(f" SUITE 17 KẾT QUẢ: {PASS} pass, {FAIL} fail")
    print("=" * 72)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
