"""
rebar_provided_checker.py — As_required vs As_provided Pipeline
===============================================================
Sprint 4 · Gap 2

Mục đích:
    Thực hiện check kết cấu quan trọng nhất trong thẩm tra:
    So sánh diện tích cốt thép YÊU CẦU từ phân tích (ETABS/tính tay)
    với cốt thép THỰC TẾ bố trí trong hồ sơ bản vẽ.

    Nếu As_provided < As_required → CẤU KIỆN THIẾU THÉP → CRITICAL

Nguồn dữ liệu:
    As_required: Từ ETABS (etabs_com_reader.py) hoặc kết quả calc_rc_section
    As_provided: Từ rebar_tokenizer.py hoặc doc_reader.py (bảng thống kê thép)

Tính As_provided từ ký hiệu thép:
    "4Ø25"  → As = 4 × π/4 × 25² = 4 × 490.9 = 1963 mm²
    "6φ20"  → As = 6 × π/4 × 20² = 6 × 314.2 = 1885 mm²
    "2Ø32"  → As = 2 × π/4 × 32² = 2 × 804.2 = 1608 mm²

Đầu ra JSON (conflict C06):
    {
        "check_type": "AS_COMPARISON",
        "element": "Dầm D1",
        "As_required_mm2": 1520.0,
        "As_provided_mm2": 1257.0,
        "As_ratio": 0.827,
        "status": "INSUFFICIENT",
        "severity": "CRITICAL",
        "shortfall_mm2": 263.0,
        "shortfall_pct": 17.3,
        "recommendation": "..."
    }

Sử dụng:
    python rebar_provided_checker.py --etabs etabs_result.json --doc doc_result.json
    python rebar_provided_checker.py --as-req 1520 --rebar "4Ø25" --element "Dầm D1"
    python rebar_provided_checker.py --demo
"""

import sys
import os
import json
import math
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 1. As_provided Calculator
# ─────────────────────────────────────────────────────────────────────────────

# Diện tích tiết diện theo đường kính (mm²)
BAR_AREA = {d: math.pi / 4 * d ** 2 for d in [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40]}

# Regex nhận dạng ký hiệu thép: "4Ø25" | "6φ20" | "2Ø32+2Ø20" | "3d25"
REBAR_TOKEN_PAT = re.compile(
    r"""(?P<count>\d+)\s*[ØøΦφd]\s*(?P<dia>[\d]+(?:[.,][\d]+)?)""",
    re.IGNORECASE | re.UNICODE,
)


def parse_rebar_notation(notation: str) -> Tuple[float, List[dict]]:
    """
    Phân tích ký hiệu thép → tổng As (mm²).

    Examples:
        "4Ø25"        → 1963.5 mm²
        "6φ20"        → 1884.9 mm²
        "2Ø32+2Ø20"  → 2232.5 mm²
        "3d25"        → 1472.6 mm²
    """
    bars = []
    total_as = 0.0

    for m in REBAR_TOKEN_PAT.finditer(notation):
        count = int(m.group("count"))
        dia = float(m.group("dia").replace(",", "."))
        # Lấy area từ bảng hoặc tính trực tiếp
        area_per_bar = BAR_AREA.get(int(dia), math.pi / 4 * dia ** 2)
        as_group = count * area_per_bar
        total_as += as_group
        bars.append({
            "count": count,
            "dia_mm": dia,
            "area_per_bar_mm2": round(area_per_bar, 1),
            "As_group_mm2": round(as_group, 1),
        })

    return round(total_as, 1), bars


def calc_as_provided(rebar_items: List[dict]) -> float:
    """
    Tính As_provided từ danh sách dict (từ doc_reader engineering_data.rebar_schedule).
    Mỗi item có thể có: dia_mm, count, As_mm2
    """
    total = 0.0
    for item in rebar_items:
        if "As_mm2" in item:
            total += float(item["As_mm2"])
        elif "dia_mm" in item and "count" in item:
            dia = float(item["dia_mm"])
            count = int(item.get("count", 1))
            area = BAR_AREA.get(int(dia), math.pi / 4 * dia ** 2)
            total += count * area
    return round(total, 1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Single-Element Check
# ─────────────────────────────────────────────────────────────────────────────

def check_as(
    element: str,
    as_required: float,
    as_provided: float,
    rebar_detail: Optional[str] = None,
    check_type: str = "FLEXURE",
    tolerance_pct: float = 0.0,
) -> dict:
    """
    So sánh As_required vs As_provided cho 1 cấu kiện.

    Args:
        element:      Tên cấu kiện ("Dầm D1")
        as_required:  Diện tích cốt thép yêu cầu (mm²)
        as_provided:  Diện tích cốt thép thực tế bố trí (mm²)
        rebar_detail: Ký hiệu thép bố trí ("4Ø25") — hiển thị trong báo cáo
        check_type:   Loại kiểm tra ("FLEXURE" | "SHEAR" | "MIN_REBAR")
        tolerance_pct: Cho phép thiếu hụt ≤ N% (mặc định 0 = nghiêm ngặt)
    """
    if as_required <= 0:
        return {
            "check_type": check_type,
            "element": element,
            "status": "SKIP",
            "note": "As_required ≤ 0 — không có yêu cầu cốt thép.",
        }

    ratio = as_provided / as_required if as_required > 0 else float("inf")
    shortfall = max(0.0, as_required - as_provided)
    shortfall_pct = shortfall / as_required * 100 if as_required > 0 else 0

    # Phân loại kết quả
    if ratio >= 1.0:
        status = "OK"
        severity = "OK"
    elif ratio >= (1.0 - tolerance_pct / 100):
        status = "MARGINAL"
        severity = "MEDIUM"
    elif ratio >= 0.85:
        status = "INSUFFICIENT"
        severity = "HIGH"
    else:
        status = "INSUFFICIENT"
        severity = "CRITICAL"

    # Recommendation
    if status == "OK":
        recommendation = (
            f"As_provided = {as_provided:.0f} mm² ≥ As_required = {as_required:.0f} mm² — Đạt."
            + (f" Tỷ lệ bố trí {ratio:.2f} — có thể xem xét tối ưu hóa." if ratio > 1.5 else "")
        )
    else:
        # Tính số thanh cần thêm để đủ (thanh phổ biến nhất)
        typical_dias = [20, 22, 25, 28, 32]
        add_suggestion = []
        for d in typical_dias:
            area_per = math.pi / 4 * d ** 2
            n_add = math.ceil(shortfall / area_per)
            if n_add <= 3:
                add_suggestion.append(f"thêm {n_add}Ø{d}")
                break
        add_str = " hoặc ".join(add_suggestion) if add_suggestion else "tăng đường kính / số lượng"
        recommendation = (
            f"THIẾU {shortfall:.0f} mm² ({shortfall_pct:.1f}%). "
            f"Đề xuất: {add_str}. "
            f"Kiểm tra lại bố trí thép theo TCVN 5574:2018 §8.3."
        )

    result = {
        "check_id": f"C06-AS-{element}",
        "check_type": check_type,
        "element": element,
        "As_required_mm2": round(as_required, 1),
        "As_provided_mm2": round(as_provided, 1),
        "As_ratio": round(ratio, 3),
        "status": status,
        "severity": severity,
        "shortfall_mm2": round(shortfall, 1),
        "shortfall_pct": round(shortfall_pct, 1),
        "recommendation": recommendation,
        "Standard": "TCVN 5574:2018 §8.3",
    }

    if rebar_detail:
        result["rebar_notation"] = rebar_detail

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 3. Batch Check — ETABS output vs hồ sơ bản vẽ
# ─────────────────────────────────────────────────────────────────────────────

def batch_check_from_etabs(
    etabs_doc: dict,
    drawing_doc: dict,
    tolerance_pct: float = 0.0,
) -> dict:
    """
    So sánh toàn bộ As_required từ ETABS với As_provided trong hồ sơ.

    etabs_doc:   Output của etabs_com_reader.py (có trường design_results)
    drawing_doc: Output của doc_reader.py (có engineering_data.rebar_schedule)
    """
    logs = []
    results = []
    summary = {"total": 0, "OK": 0, "INSUFFICIENT": 0, "MARGINAL": 0, "CRITICAL": 0, "SKIP": 0}

    # Extract As_required từ ETABS design_results
    etabs_design = etabs_doc.get("design_results", {})
    etabs_beams = etabs_design.get("beams", [])
    etabs_columns = etabs_design.get("columns", [])

    # Extract rebar từ drawing
    drawing_rebars = drawing_doc.get("engineering_data", {}).get("rebar_schedule", [])
    drawing_sections = drawing_doc.get("engineering_data", {}).get("sections", [])

    # Build lookup As_provided theo element name
    # Nếu không có tên cụ thể, dùng tổng As_provided từ bảng thống kê
    as_provided_map: Dict[str, float] = {}
    for sec in drawing_sections:
        elem = (sec.get("element") or "").upper().strip()
        if elem and drawing_rebars:
            # Lấy rebar đầu tiên phù hợp (đơn giản hóa)
            as_prov = calc_as_provided(drawing_rebars[:3])  # lấy 3 thanh đầu mặc định
            as_provided_map[elem] = as_prov

    # Check từng dầm ETABS
    for beam in etabs_beams:
        elem = beam.get("label", beam.get("name", "B?"))
        as_req_bot = beam.get("As_bottom_mm2", beam.get("as_req_bottom", 0))
        as_req_top = beam.get("As_top_mm2", beam.get("as_req_top", 0))
        as_prov = as_provided_map.get(elem.upper(), drawing_doc.get("_total_as_override"))

        if as_prov is None:
            # Không tìm được As_provided → cảnh báo thiếu dữ liệu
            logs.append({"step": "C06_warn", "element": elem, "note": "Không tìm thấy As_provided trong hồ sơ"})
            continue

        # Check uốn dương (Bottom)
        if as_req_bot and as_req_bot > 0:
            res = check_as(elem, as_req_bot, as_prov, check_type="FLEXURE_BOTTOM")
            results.append(res)
            summary["total"] += 1
            sv = res.get("severity", "SKIP")
            if sv in summary: summary[sv] += 1
            if sv == "CRITICAL": summary["CRITICAL"] += 1

    # Check từng cột ETABS
    for col in etabs_columns:
        elem = col.get("label", col.get("name", "C?"))
        as_req = col.get("As_mm2", col.get("as_req", 0))
        as_prov = as_provided_map.get(elem.upper())

        if as_prov is None:
            continue

        res = check_as(elem, as_req, as_prov, check_type="COLUMN_REBAR")
        results.append(res)
        summary["total"] += 1

    logs.append({"step": "batch_complete", "checks": len(results)})

    # Overall
    if summary["CRITICAL"] > 0 or summary["INSUFFICIENT"] > 0:
        overall = f"❌ CÓ {summary['CRITICAL'] + summary['INSUFFICIENT']} CẤU KIỆN THIẾU THÉP — KHÔNG ĐẠT"
    elif summary["MARGINAL"] > 0:
        overall = f"⚠️ CÓ {summary['MARGINAL']} CẤU KIỆN THÉP SÁT NGƯỠNG"
    else:
        overall = f"✅ TẤT CẢ {summary['total']} CẤU KIỆN ĐỦ THÉP"

    return {
        "checked_at": datetime.now().isoformat(),
        "source_etabs": etabs_doc.get("source_file", "ETABS"),
        "source_drawing": drawing_doc.get("source_file", "Hồ sơ"),
        "overall_assessment": overall,
        "summary": summary,
        "results": results,
        "Calculation_Logs": logs,
        "Standard_Method": "rebar_provided_checker v1.0 Sprint-4",
        "Standard": "TCVN 5574:2018 §8.3",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo():
    """Demo: kiểm tra 3 cấu kiện với dữ liệu mẫu."""
    print("\n" + "=" * 60)
    print("  DEMO — As_required vs As_provided Checker")
    print("=" * 60)

    test_cases = [
        # (element, notation, As_required, check_type)
        ("Dầm D1 — Gối A",   "4Ø25",      1520.0, "FLEXURE_TOP"),
        ("Dầm D1 — Nhịp",    "3Ø20",      1200.0, "FLEXURE_BOTTOM"),
        ("Dầm D2 — Gối",     "2Ø25+2Ø20", 1650.0, "FLEXURE_TOP"),
        ("Cột C1",            "8Ø22",      3200.0, "COLUMN_REBAR"),
        ("Dầm D3 — Nhịp",    "4Ø16",       700.0, "FLEXURE_BOTTOM"),
    ]

    all_results = []
    for element, notation, as_req, ctype in test_cases:
        as_prov, bars = parse_rebar_notation(notation)
        result = check_as(element, as_req, as_prov, rebar_detail=notation, check_type=ctype)
        all_results.append(result)

        icon = {"OK": "✅", "MARGINAL": "🟡", "INSUFFICIENT": "🟠", "SKIP": "⬜"}.get(result["status"], "❌")
        sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "OK": "🟢"}.get(result["severity"], "⬜")
        print(f"\n{icon} {element}")
        print(f"   Bố trí: {notation} → As_prov = {as_prov:.0f} mm²")
        print(f"   As_req  = {as_req:.0f} mm² | Tỷ lệ = {result['As_ratio']:.3f} {sev_icon}")
        if result["shortfall_mm2"] > 0:
            print(f"   ⚠️  Thiếu {result['shortfall_mm2']:.0f} mm² ({result['shortfall_pct']:.1f}%)")
        print(f"   → {result['recommendation']}")

    print("\n" + "=" * 60)
    ok = sum(1 for r in all_results if r["status"] == "OK")
    fail = len(all_results) - ok
    print(f"  Tổng: {len(all_results)} | ✅ Đạt: {ok} | ❌ Không đạt: {fail}")
    print("=" * 60)

    return all_results


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="rebar_provided_checker — As_required vs As_provided (Sprint 4)",
    )
    parser.add_argument("--element",  help="Tên cấu kiện")
    parser.add_argument("--as-req",   type=float, help="As_required (mm²)")
    parser.add_argument("--rebar",    help="Ký hiệu thép bố trí ('4Ø25')")
    parser.add_argument("--etabs",    help="File JSON từ etabs_com_reader")
    parser.add_argument("--doc",      help="File JSON từ doc_reader")
    parser.add_argument("--output",   help="File JSON kết quả")
    parser.add_argument("--demo",     action="store_true")
    args = parser.parse_args()

    if args.demo:
        results = _demo()
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        return

    if args.as_req and args.rebar:
        as_prov, bars = parse_rebar_notation(args.rebar)
        result = check_as(
            args.element or "Cấu kiện",
            args.as_req,
            as_prov,
            rebar_detail=args.rebar,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return

    if args.etabs and args.doc:
        with open(args.etabs, encoding="utf-8") as f:
            etabs_doc = json.load(f)
        with open(args.doc, encoding="utf-8") as f:
            drawing_doc = json.load(f)
        result = batch_check_from_etabs(etabs_doc, drawing_doc)
        out_json = json.dumps(result, ensure_ascii=False, indent=2)
        print(result["overall_assessment"])
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out_json)
        else:
            print(out_json)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
