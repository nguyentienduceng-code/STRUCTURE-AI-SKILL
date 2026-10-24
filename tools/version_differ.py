"""
version_differ.py — Engineering Document Version Comparator
============================================================
Sprint 4 · Task 4.3

Mục đích:
    So sánh 2 phiên bản hồ sơ kỹ thuật (Rev A vs Rev B) và tự động
    phát hiện, phân loại các thay đổi kỹ thuật có ý nghĩa.

Phân loại thay đổi:
    MAJOR — Thay đổi có ảnh hưởng kết cấu (tiết diện, tải trọng, vật liệu grade)
    MINOR — Thay đổi không ảnh hưởng kết cấu (ghi chú, nhãn, bố trí)
    ADDED — Thêm mới cấu kiện / tải / mục
    REMOVED — Xóa bỏ cấu kiện / tải / mục

Đầu vào:
    2 file JSON từ doc_reader.py (hoặc dict trực tiếp)

Đầu ra JSON:
    {
        "compared_at": "...",
        "rev_a": {"source_file": "...", "revision": "A"},
        "rev_b": {"source_file": "...", "revision": "B"},
        "change_summary": {"MAJOR": 2, "MINOR": 1, "ADDED": 3, "REMOVED": 0},
        "changes": [{
            "id": "VD-001",
            "category": "MAJOR",
            "field": "sections.Dầm D1.b_mm",
            "old_value": 300,
            "new_value": 250,
            "description": "...",
            "impact": "..."
        }],
        "unchanged": [...],
        "Calculation_Logs": [...]
    }

Sử dụng:
    python version_differ.py --rev-a rev_a.json --rev-b rev_b.json [--output diff.json]
    python version_differ.py --demo
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Change Data Models
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_ORDER = {"MAJOR": 0, "MINOR": 1, "ADDED": 2, "REMOVED": 3}

STRUCTURAL_FIELDS = {
    "sections":    ["b_mm", "h_mm"],
    "loads":       ["value", "unit"],
    "materials":   ["grade", "fck_MPa", "fy_MPa"],
    "soil_params": ["SPT_N"],
    "rebar_schedule": ["dia_mm", "count", "length_mm", "As_mm2"],
}


def _make_change(
    change_id: str,
    category: str,
    field: str,
    old_val: Any,
    new_val: Any,
    description: str,
    impact: str,
    delta_pct: Optional[float] = None,
) -> dict:
    return {
        "id": change_id,
        "category": category,
        "field": field,
        "old_value": old_val,
        "new_value": new_val,
        "delta_pct": round(delta_pct, 1) if delta_pct is not None else None,
        "description": description,
        "impact": impact,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Deep Diff Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _numeric_delta(old: Any, new: Any) -> Optional[float]:
    """Tính % thay đổi số, trả None nếu không phải số."""
    try:
        o, n = float(str(old).replace(",", ".")), float(str(new).replace(",", "."))
        return abs(n - o) / abs(o) * 100.0 if o != 0 else None
    except (ValueError, TypeError):
        return None


def _classify_change(field_path: str, old_val: Any, new_val: Any) -> str:
    """
    Quyết định MAJOR / MINOR dựa trên tên field.
    Structural fields = MAJOR, còn lại = MINOR.
    """
    structural_kws = [
        "b_mm", "h_mm", "value", "grade", "fck", "fy",
        "dia_mm", "count", "length_mm", "As_mm2", "SPT_N",
    ]
    for kw in structural_kws:
        if kw in field_path:
            delta = _numeric_delta(old_val, new_val)
            # Thay đổi < 1% có thể là làm tròn số, không coi là MAJOR
            if delta is not None and delta < 1.0:
                return "MINOR"
            return "MAJOR"
    return "MINOR"


def _impact_message(field_path: str, old_val: Any, new_val: Any, delta: Optional[float]) -> str:
    """Sinh mô tả impact tự động từ field name."""
    impact_map = {
        "b_mm":       "Thay đổi bề rộng tiết diện — ảnh hưởng khả năng chịu cắt và uốn.",
        "h_mm":       "Thay đổi chiều cao tiết diện — ảnh hưởng trực tiếp mô men kháng uốn.",
        "value":      f"Thay đổi tải trọng {delta:.1f}% — cần chạy lại phân tích." if delta else "Thay đổi tải trọng.",
        "grade":      "Thay đổi grade vật liệu — cần kiểm tra lại toàn bộ η.",
        "fck_MPa":    "Thay đổi cường độ bê tông — ảnh hưởng tính toán bê tông cốt thép.",
        "fy_MPa":     "Thay đổi cường độ thép — ảnh hưởng diện tích cốt thép yêu cầu.",
        "dia_mm":     "Thay đổi đường kính thép — ảnh hưởng As thực tế.",
        "count":      "Thay đổi số lượng thanh thép — kiểm tra lại As và khoảng cách.",
        "length_mm":  "Thay đổi chiều dài thép — kiểm tra lại neo và nối thép.",
        "SPT_N":      "Thay đổi chỉ số SPT — ảnh hưởng đánh giá sức chịu tải nền.",
    }
    for kw, msg in impact_map.items():
        if kw in field_path:
            return msg
    return "Thay đổi thông tin — xem xét ảnh hưởng."


# ─────────────────────────────────────────────────────────────────────────────
# 3. List Diff (cấu kiện, tải trọng...)
# ─────────────────────────────────────────────────────────────────────────────

def _diff_list_by_key(
    list_a: List[dict],
    list_b: List[dict],
    id_fields: List[str],
    compare_fields: List[str],
    section_name: str,
    changes: List[dict],
    unchanged: List[dict],
    ctr_ref: List[int],
) -> None:
    """
    So sánh 2 list[dict] theo id_fields.
    Kết quả ghi vào changes / unchanged in-place.
    """

    def make_key(item: dict) -> str:
        return "|".join(str(item.get(f, "")).upper().strip() for f in id_fields)

    lookup_b = {make_key(item): item for item in list_b}
    lookup_a = {make_key(item): item for item in list_a}

    # Items in A
    for item_a in list_a:
        key = make_key(item_a)
        item_b = lookup_b.get(key)
        ctr_ref[0] += 1
        id_str = f"VD-{ctr_ref[0]:03d}"

        if item_b is None:
            # Bị xóa trong Rev B
            changes.append(_make_change(
                id_str, "REMOVED",
                f"{section_name}.{key}",
                item_a, None,
                f"'{key}' có trong Rev A nhưng bị xóa trong Rev B.",
                f"Xác nhận việc xóa '{key}' là cố ý.",
            ))
            continue

        # So sánh từng field
        found_change = False
        for field in compare_fields:
            val_a = item_a.get(field)
            val_b = item_b.get(field)
            if val_a is None and val_b is None:
                continue
            if val_a != val_b:
                found_change = True
                ctr_ref[0] += 1
                fid = f"VD-{ctr_ref[0]:03d}"
                field_path = f"{section_name}.{key}.{field}"
                delta = _numeric_delta(val_a, val_b)
                cat = _classify_change(field_path, val_a, val_b)
                changes.append(_make_change(
                    fid, cat, field_path,
                    val_a, val_b,
                    f"Rev A: {val_a} → Rev B: {val_b}" + (f" (Δ {delta:.1f}%)" if delta else ""),
                    _impact_message(field_path, val_a, val_b, delta),
                    delta,
                ))

        if not found_change:
            unchanged.append({
                "field": f"{section_name}.{key}",
                "note": "Không thay đổi",
            })

    # Items added in B (không có trong A)
    for item_b in list_b:
        key = make_key(item_b)
        if key not in lookup_a:
            ctr_ref[0] += 1
            changes.append(_make_change(
                f"VD-{ctr_ref[0]:03d}", "ADDED",
                f"{section_name}.{key}",
                None, item_b,
                f"'{key}' được thêm mới trong Rev B.",
                f"Kiểm tra xem '{key}' đã được tính toán đầy đủ chưa.",
            ))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Master Differ
# ─────────────────────────────────────────────────────────────────────────────

def diff_versions(doc_a: dict, doc_b: dict) -> dict:
    """
    So sánh 2 phiên bản hồ sơ và trả về báo cáo thay đổi.
    """
    changes: List[dict] = []
    unchanged: List[dict] = []
    logs: List[dict] = []
    ctr_ref = [0]  # mutable counter

    eng_a = doc_a.get("engineering_data", {})
    eng_b = doc_b.get("engineering_data", {})

    # 1. Sections (tiết diện cấu kiện)
    _diff_list_by_key(
        eng_a.get("sections", []),
        eng_b.get("sections", []),
        id_fields=["element"],
        compare_fields=["b_mm", "h_mm"],
        section_name="sections",
        changes=changes, unchanged=unchanged, ctr_ref=ctr_ref,
    )
    logs.append({"step": "diff_sections", "items_a": len(eng_a.get("sections", []))})

    # 2. Loads (tải trọng)
    _diff_list_by_key(
        eng_a.get("loads", []),
        eng_b.get("loads", []),
        id_fields=["label"],
        compare_fields=["value", "unit"],
        section_name="loads",
        changes=changes, unchanged=unchanged, ctr_ref=ctr_ref,
    )
    logs.append({"step": "diff_loads", "items_a": len(eng_a.get("loads", []))})

    # 3. Materials (vật liệu)
    _diff_list_by_key(
        eng_a.get("materials", []),
        eng_b.get("materials", []),
        id_fields=["type"],
        compare_fields=["grade", "fck_MPa", "fy_MPa"],
        section_name="materials",
        changes=changes, unchanged=unchanged, ctr_ref=ctr_ref,
    )
    logs.append({"step": "diff_materials"})

    # 4. Rebar schedule (bảng thống kê thép)
    _diff_list_by_key(
        eng_a.get("rebar_schedule", []),
        eng_b.get("rebar_schedule", []),
        id_fields=["mark"],
        compare_fields=["dia_mm", "count", "length_mm", "As_mm2"],
        section_name="rebar_schedule",
        changes=changes, unchanged=unchanged, ctr_ref=ctr_ref,
    )
    logs.append({"step": "diff_rebar"})

    # 5. Soil params
    _diff_list_by_key(
        eng_a.get("soil_params", []),
        eng_b.get("soil_params", []),
        id_fields=["layer"],
        compare_fields=["SPT_N"],
        section_name="soil_params",
        changes=changes, unchanged=unchanged, ctr_ref=ctr_ref,
    )
    logs.append({"step": "diff_soil"})

    # Sort by category
    changes.sort(key=lambda x: CATEGORY_ORDER.get(x.get("category", "MINOR"), 9))

    # Summary
    summary = {"MAJOR": 0, "MINOR": 0, "ADDED": 0, "REMOVED": 0}
    for ch in changes:
        cat = ch.get("category", "MINOR")
        if cat in summary:
            summary[cat] += 1

    # Overall
    if summary["MAJOR"] > 0:
        overall = f"⚠️ CÓ {summary['MAJOR']} THAY ĐỔI KẾT CẤU (MAJOR) — Cần review và phê duyệt lại"
    elif summary["ADDED"] + summary["REMOVED"] > 0:
        overall = f"ℹ️ CÓ {summary['ADDED']+summary['REMOVED']} CẤU KIỆN THÊM/XÓA — Kiểm tra tính đầy đủ"
    elif summary["MINOR"] > 0:
        overall = f"🟡 Chỉ có {summary['MINOR']} thay đổi nhỏ (MINOR)"
    else:
        overall = "✅ KHÔNG THAY ĐỔI — Rev A và Rev B giống nhau hoàn toàn"

    return {
        "compared_at": datetime.now().isoformat(),
        "rev_a": {
            "source_file": doc_a.get("source_file", "Rev A"),
            "source_type": doc_a.get("source_type", "?"),
            "extracted_at": doc_a.get("extracted_at"),
        },
        "rev_b": {
            "source_file": doc_b.get("source_file", "Rev B"),
            "source_type": doc_b.get("source_type", "?"),
            "extracted_at": doc_b.get("extracted_at"),
        },
        "overall_assessment": overall,
        "change_summary": summary,
        "total_changes": len(changes),
        "total_unchanged": len(unchanged),
        "changes": changes,
        "unchanged": unchanged,
        "Calculation_Logs": logs,
        "Standard_Method": "version_differ v1.0 Sprint-4",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo_docs():
    """Tạo 2 phiên bản mẫu Rev A vs Rev B có sự khác biệt."""
    rev_a = {
        "source_file": "TM_KetCau_RevA.pdf",
        "source_type": "PDF",
        "extracted_at": "2026-09-01T10:00:00",
        "engineering_data": {
            "loads": [
                {"label": "Tĩnh tải sàn", "value": 3.5, "unit": "kN/m²"},
                {"label": "Hoạt tải VP",   "value": 5.0, "unit": "kN/m²"},
            ],
            "sections": [
                {"element": "Dầm D1", "b_mm": 300, "h_mm": 600},
                {"element": "Cột C1", "b_mm": 400, "h_mm": 400},
                {"element": "Dầm D2", "b_mm": 250, "h_mm": 500},
            ],
            "materials": [
                {"type": "concrete", "grade": "B25", "fck_MPa": 20},
                {"type": "steel_rebar", "grade": "CB400V", "fy_MPa": 400},
            ],
            "rebar_schedule": [
                {"mark": "1", "dia_mm": 20, "count": 4, "length_mm": 5800},
                {"mark": "2", "dia_mm": 16, "count": 6, "length_mm": 3200},
            ],
            "soil_params": [],
        },
    }
    rev_b = {
        "source_file": "TM_KetCau_RevB.pdf",
        "source_type": "PDF",
        "extracted_at": "2026-10-18T21:00:00",
        "engineering_data": {
            "loads": [
                {"label": "Tĩnh tải sàn", "value": 4.0, "unit": "kN/m²"},  # MAJOR: +14.3%
                {"label": "Hoạt tải VP",   "value": 5.0, "unit": "kN/m²"},  # OK
            ],
            "sections": [
                {"element": "Dầm D1", "b_mm": 300, "h_mm": 700},  # MAJOR: h tăng 16.7%
                {"element": "Cột C1", "b_mm": 400, "h_mm": 400},  # OK
                # Dầm D2 bị xóa (REMOVED)
                {"element": "Dầm D3", "b_mm": 200, "h_mm": 450},  # ADDED
            ],
            "materials": [
                {"type": "concrete", "grade": "B30", "fck_MPa": 25},  # MAJOR: grade tăng
                {"type": "steel_rebar", "grade": "CB400V", "fy_MPa": 400},  # OK
            ],
            "rebar_schedule": [
                {"mark": "1", "dia_mm": 22, "count": 4, "length_mm": 5800},  # MAJOR: dia tăng
                {"mark": "2", "dia_mm": 16, "count": 6, "length_mm": 3200},  # OK
            ],
            "soil_params": [],
        },
    }
    return rev_a, rev_b


# ─────────────────────────────────────────────────────────────────────────────
# 6. Report Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_diff_report(diff_result: dict) -> str:
    """Tạo báo cáo Markdown từ kết quả diff."""
    lines = [
        f"# Báo cáo So sánh Phiên bản Hồ sơ",
        f"",
        f"**Thời điểm so sánh:** {diff_result.get('compared_at', '')}",
        f"**Rev A:** {diff_result['rev_a']['source_file']}",
        f"**Rev B:** {diff_result['rev_b']['source_file']}",
        f"",
        f"## Đánh giá tổng thể",
        f"{diff_result.get('overall_assessment', '')}",
        f"",
        f"## Tóm tắt Thay đổi",
        f"| Loại | Số lượng |",
        f"|------|----------|",
    ]
    for cat, cnt in diff_result.get("change_summary", {}).items():
        lines.append(f"| {cat} | {cnt} |")
    lines += [
        f"| **Không đổi** | {diff_result.get('total_unchanged', 0)} |",
        f"",
        f"## Chi tiết Thay đổi",
    ]

    for ch in diff_result.get("changes", []):
        cat_icon = {"MAJOR": "🔴", "MINOR": "🟡", "ADDED": "🟢", "REMOVED": "⚫"}.get(ch["category"], "⬜")
        delta_str = f" (Δ {ch['delta_pct']:.1f}%)" if ch.get("delta_pct") else ""
        lines += [
            f"",
            f"### {cat_icon} [{ch['id']}] {ch['category']} — `{ch['field']}`",
            f"- **Trước (Rev A):** `{ch['old_value']}`",
            f"- **Sau (Rev B):** `{ch['new_value']}`{delta_str}",
            f"- **Mô tả:** {ch['description']}",
            f"- **Tác động:** {ch['impact']}",
        ]

    lines += [
        f"",
        f"---",
        f"*Báo cáo do `version_differ v1.0 Sprint-4` tạo tự động — cần kỹ sư kiểm tra xác nhận trước khi sử dụng.*",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="version_differ — Engineering Document Version Comparator (Sprint 4)",
    )
    parser.add_argument("--rev-a",  help="File JSON Rev A (từ doc_reader)")
    parser.add_argument("--rev-b",  help="File JSON Rev B (từ doc_reader)")
    parser.add_argument("--output", help="File JSON kết quả diff")
    parser.add_argument("--report", help="File Markdown báo cáo")
    parser.add_argument("--demo",   action="store_true", help="Chạy demo")
    args = parser.parse_args()

    if args.demo:
        doc_a, doc_b = _demo_docs()
    elif args.rev_a and args.rev_b:
        with open(args.rev_a, encoding="utf-8") as f:
            doc_a = json.load(f)
        with open(args.rev_b, encoding="utf-8") as f:
            doc_b = json.load(f)
    else:
        parser.print_help()
        return

    result = diff_versions(doc_a, doc_b)
    out_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"✅ Diff JSON: {args.output}")

    if args.report:
        report_md = generate_diff_report(result)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"✅ Báo cáo MD: {args.report}")

    # Console summary
    s = result["change_summary"]
    print(f"\n{result['overall_assessment']}")
    print(f"  MAJOR: {s['MAJOR']} | MINOR: {s['MINOR']} | ADDED: {s['ADDED']} | REMOVED: {s['REMOVED']}")
    print(f"  Unchanged: {result['total_unchanged']}")

    if not args.output and not args.report:
        print(out_json)


if __name__ == "__main__":
    main()
