"""
report_pipeline.py — End-to-End Engineering Report Pipeline
============================================================
Sprint 4 · Gap 3

Mục đích:
    Pipeline đầu cuối: từ file hồ sơ đầu vào → tính toán → thẩm tra → xuất báo cáo.
    Thay thế quy trình thủ công nhiều bước bằng 1 lệnh duy nhất.

Luồng thực thi:
    INPUT FILE
        ↓
    [Stage 1] doc_reader    → structured JSON
        ↓
    [Stage 2] calc engine   → calculation result JSON   (tùy chọn)
        ↓
    [Stage 3] conflict check → conflict report JSON     (tùy chọn)
        ↓
    [Stage 4] rebar check   → As_req vs As_prov        (tùy chọn)
        ↓
    [Stage 5] report writer → .md + .docx              (bắt buộc)
        ↓
    Review Gate → Confidence check → OUTPUT

Chế độ:
    --mode read_only     : Chỉ đọc và extract dữ liệu (không tính toán)
    --mode review        : Đọc + check xung đột (không tính toán mới)
    --mode full_calc     : Đọc + tính toán đơn giản + check + xuất
    --mode compare       : So sánh 2 phiên bản hồ sơ

Sử dụng:
    python report_pipeline.py --input thuyetminh.pdf --mode review --output-dir ./out
    python report_pipeline.py --input-a rev_a.pdf --input-b rev_b.pdf --mode compare
    python report_pipeline.py --input model.ifc --mode read_only
    python report_pipeline.py --demo
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm tools vào path
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

# Structural scripts
STRUCTURAL_DIR = Path(__file__).parent.parent / "skills" / "Structural_Design_Engineer" / "scripts"
sys.path.insert(0, str(STRUCTURAL_DIR))

# ─────────────────────────────────────────────────────────────────────────────
# 1. Stage Imports (lazy — chỉ import khi cần)
# ─────────────────────────────────────────────────────────────────────────────

def _import_doc_reader():
    import doc_reader as m; return m

def _import_conflict_analyzer():
    import conflict_analyzer as m; return m

def _import_version_differ():
    import version_differ as m; return m

def _import_rebar_checker():
    import rebar_provided_checker as m; return m

def _import_calc_rc():
    try:
        import calc_rc_section as m; return m
    except ImportError:
        return None

def _import_docx_builder():
    try:
        import docx_report_builder as m; return m
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Stage Runners
# ─────────────────────────────────────────────────────────────────────────────

def stage_read(input_path: str, logs: list) -> dict:
    """Stage 1: Đọc file đầu vào."""
    t0 = time.time()
    dr = _import_doc_reader()
    result = dr.read_document(input_path)
    elapsed = time.time() - t0
    logs.append({
        "stage": 1,
        "name": "doc_reader",
        "input": Path(input_path).name,
        "confidence": result.get("confidence_level"),
        "loads_found": len(result.get("engineering_data", {}).get("loads", [])),
        "sections_found": len(result.get("engineering_data", {}).get("sections", [])),
        "elapsed_s": round(elapsed, 3),
    })
    print(f"  [Stage 1] ✅ Đọc xong: {Path(input_path).name} "
          f"(confidence={result.get('confidence_level')}, {elapsed:.2f}s)")
    return result


def stage_conflict_check(docs: List[dict], logs: list, threshold: float = 5.0) -> dict:
    """Stage 3: Phát hiện xung đột chéo."""
    t0 = time.time()
    ca = _import_conflict_analyzer()
    result = ca.analyze_conflicts(docs, threshold_pct=threshold)
    elapsed = time.time() - t0
    s = result.get("conflict_summary", {})
    logs.append({
        "stage": 3,
        "name": "conflict_analyzer",
        "conflicts_total": s.get("total", 0),
        "critical": s.get("CRITICAL", 0),
        "elapsed_s": round(elapsed, 3),
    })
    print(f"  [Stage 3] ✅ Xung đột: {s.get('total',0)} "
          f"(CRITICAL={s.get('CRITICAL',0)}, HIGH={s.get('HIGH',0)}, {elapsed:.2f}s)")
    return result


def stage_rebar_check(doc: dict, rebar_pairs: list, logs: list) -> List[dict]:
    """Stage 4: Kiểm tra As_required vs As_provided."""
    t0 = time.time()
    rc = _import_rebar_checker()
    results = []
    for element, as_req, notation in rebar_pairs:
        as_prov, bars = rc.parse_rebar_notation(notation)
        res = rc.check_as(element, as_req, as_prov, rebar_detail=notation)
        results.append(res)
    elapsed = time.time() - t0
    critical = sum(1 for r in results if r.get("severity") == "CRITICAL")
    logs.append({
        "stage": 4,
        "name": "rebar_checker",
        "checks": len(results),
        "critical": critical,
        "elapsed_s": round(elapsed, 3),
    })
    print(f"  [Stage 4] ✅ Cốt thép: {len(results)} kiểm tra, {critical} CRITICAL ({elapsed:.2f}s)")
    return results


def stage_calc_simple(doc: dict, logs: list) -> Optional[dict]:
    """Stage 2: Tính toán đơn giản từ dữ liệu extract (nếu đủ điều kiện)."""
    t0 = time.time()
    calc_mod = _import_calc_rc()
    if not calc_mod:
        logs.append({"stage": 2, "note": "calc_rc_section không available — bỏ qua"})
        return None

    eng = doc.get("engineering_data", {})
    secs = eng.get("sections", [])
    loads = eng.get("loads", [])
    mats = eng.get("materials", [])

    if not secs or not loads:
        logs.append({"stage": 2, "note": "Không đủ dữ liệu tiết diện+tải để tính toán"})
        return None

    # Chỉ tính cấu kiện đầu tiên để demo pipeline
    sec = secs[0]
    b = sec.get("b_mm", 300)
    h = sec.get("h_mm", 500)

    # Ước tính M_ed và V_ed từ tải trọng (đơn giản hóa: uniform load, nhịp 5m)
    tl_load = next((l["value"] for l in loads if "tĩnh" in l.get("label","").lower()), 0)
    hl_load = next((l["value"] for l in loads if "hoạt" in l.get("label","").lower()), 0)
    total_load = tl_load + hl_load
    L = 5000  # mm mặc định nếu không có nhịp

    # w = total_load * (b/1000) kN/m → M = wL²/8, V = wL/2
    w_beam = total_load * (b / 1000) if total_load > 0 else 15.0
    M_ed = w_beam * (L / 1000) ** 2 / 8
    V_ed = w_beam * (L / 1000) / 2

    # Grade vật liệu
    conc = next((m["grade"] for m in mats if m.get("type") == "concrete"), "B25")
    steel = next((m["grade"] for m in mats if m.get("type") == "steel_rebar"), "CB400-V")
    if not steel.endswith(("-T", "-V")):
        steel = steel.replace("CB", "CB").replace("T", "-T").replace("V", "-V")
        if "-" not in steel:
            steel = steel + "-V"

    try:
        calc_result = calc_mod.calc_rc_beam(
            b=b, h=h, concrete=conc, rebar=steel,
            M_ed=M_ed, V_ed=V_ed,
        )
        elapsed = time.time() - t0
        logs.append({
            "stage": 2,
            "name": "calc_rc_section",
            "element": sec.get("element", "Cấu kiện đầu tiên"),
            "M_ed": round(M_ed, 1),
            "V_ed": round(V_ed, 1),
            "elapsed_s": round(elapsed, 3),
        })
        print(f"  [Stage 2] ✅ Tính toán {sec.get('element','CK1')}: "
              f"M={M_ed:.1f}kNm, V={V_ed:.1f}kN ({elapsed:.2f}s)")
        return calc_result
    except Exception as e:
        logs.append({"stage": 2, "error": str(e)})
        print(f"  [Stage 2] ⚠️ Tính toán lỗi: {e}")
        return None


def stage_compare(path_a: str, path_b: str, logs: list) -> dict:
    """Stage: So sánh 2 phiên bản."""
    dr = _import_doc_reader()
    vd = _import_version_differ()

    t0 = time.time()
    doc_a = dr.read_document(path_a)
    doc_b = dr.read_document(path_b)
    result = vd.diff_versions(doc_a, doc_b)
    elapsed = time.time() - t0

    logs.append({
        "stage": "compare",
        "rev_a": Path(path_a).name,
        "rev_b": Path(path_b).name,
        "major_changes": result["change_summary"]["MAJOR"],
        "elapsed_s": round(elapsed, 3),
    })
    print(f"  [Compare] ✅ So sánh xong ({elapsed:.2f}s): "
          f"MAJOR={result['change_summary']['MAJOR']}, "
          f"ADDED={result['change_summary']['ADDED']}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 3. Report Writers
# ─────────────────────────────────────────────────────────────────────────────

def write_markdown_report(
    pipeline_result: dict,
    output_path: str,
) -> None:
    """Xuất báo cáo Markdown đầy đủ từ kết quả pipeline."""

    def _eta_icon(eta):
        if eta is None: return "⬜"
        if eta > 1.0: return "🔴"
        if eta > 0.9: return "🟠"
        if eta > 0.7: return "🟡"
        return "🟢"

    doc = pipeline_result.get("read_result", {})
    conflict = pipeline_result.get("conflict_result")
    rebar = pipeline_result.get("rebar_results", [])
    calc = pipeline_result.get("calc_result")
    compare = pipeline_result.get("compare_result")
    meta = pipeline_result.get("meta", {})

    lines = [
        "# BÁO CÁO THẨM TRA KỸ THUẬT KẾT CẤU",
        f"**Tạo bởi:** report_pipeline v1.0 — Sprint 4",
        f"**Thời điểm:** {meta.get('started_at', datetime.now().isoformat())}",
        f"**Hồ sơ:** {doc.get('source_file', 'N/A')} ({doc.get('source_type', '?')})",
        f"**Confidence đọc dữ liệu:** {doc.get('confidence_level', '?')}",
        "",
        "---",
        "",
        "## 1. Dữ liệu Trích xuất",
        "",
    ]

    # Loads
    eng = doc.get("engineering_data", {})
    loads = eng.get("loads", [])
    if loads:
        lines += ["### Tải trọng", "| Loại tải | Giá trị | Đơn vị |", "|----------|---------|--------|"]
        for l in loads:
            lines.append(f"| {l.get('label','?')} | {l.get('value','?')} | {l.get('unit','?')} |")
        lines.append("")

    # Sections
    secs = eng.get("sections", [])
    if secs:
        lines += ["### Tiết diện cấu kiện", "| Cấu kiện | B (mm) | H (mm) |", "|---------|--------|--------|"]
        for s in secs:
            lines.append(f"| {s.get('element','?')} | {s.get('b_mm','?')} | {s.get('h_mm','?')} |")
        lines.append("")

    # Materials
    mats = eng.get("materials", [])
    if mats:
        lines += ["### Vật liệu", "| Loại | Grade | Cường độ |", "|------|-------|---------|"]
        for m in mats:
            strength = f"fck={m['fck_MPa']}MPa" if m.get("fck_MPa") else f"fy={m.get('fy_MPa','?')}MPa"
            lines.append(f"| {m.get('type','?')} | {m.get('grade','?')} | {strength} |")
        lines.append("")

    # Conflict results
    if conflict:
        lines += [
            "## 2. Kết quả Thẩm tra Xung đột",
            "",
            f"**{conflict.get('overall_assessment', '')}**",
            "",
        ]
        cs = conflict.get("conflict_summary", {})
        lines += [
            "| Mức | Số lượng |",
            "|-----|----------|",
            f"| 🔴 CRITICAL | {cs.get('CRITICAL', 0)} |",
            f"| 🟠 HIGH     | {cs.get('HIGH', 0)} |",
            f"| 🟡 MEDIUM   | {cs.get('MEDIUM', 0)} |",
            f"| ✅ PASS     | {len(conflict.get('passes', []))} |",
            "",
        ]
        for cf in conflict.get("conflicts", []):
            sev_icon = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(cf.get("severity",""), "⬜")
            lines += [
                f"### {sev_icon} [{cf['id']}] {cf.get('type','')}",
                f"- **Tham số:** {cf.get('param','')}",
                f"- **Nguồn A:** {cf.get('value_A',{}).get('source','?')} = {cf.get('value_A',{}).get('value','?')} {cf.get('value_A',{}).get('unit','')}",
                f"- **Nguồn B:** {cf.get('value_B',{}).get('source','?')} = {cf.get('value_B',{}).get('value','?')} {cf.get('value_B',{}).get('unit','')}",
                f"- **Chênh lệch:** {cf.get('delta_pct','N/A')}%",
                f"- **Đề xuất:** {cf.get('recommendation','')}",
                "",
            ]

    # Rebar check results
    if rebar:
        lines += ["## 3. Kiểm tra Cốt thép (As_req vs As_prov)", ""]
        ok = sum(1 for r in rebar if r["status"] == "OK")
        fail = len(rebar) - ok
        lines.append(f"**Tổng: {len(rebar)} | ✅ Đạt: {ok} | ❌ Không đạt: {fail}**\n")
        lines += ["| Cấu kiện | Ký hiệu | As_req (mm²) | As_prov (mm²) | Tỷ lệ | Kết quả |",
                  "|----------|---------|-------------|--------------|-------|---------|"]
        for r in rebar:
            icon = "✅" if r["status"] == "OK" else "❌"
            lines.append(
                f"| {r['element']} | {r.get('rebar_notation','?')} "
                f"| {r.get('As_required_mm2','?')} "
                f"| {r.get('As_provided_mm2','?')} "
                f"| {r.get('As_ratio','?')} | {icon} {r['status']} |"
            )
        lines.append("")
        for r in rebar:
            if r["status"] != "OK":
                lines.append(f"> ⚠️ **{r['element']}**: {r['recommendation']}")
        lines.append("")

    # Calc result
    if calc:
        eta_M = calc.get("eta_M")
        eta_V = calc.get("eta_V")
        lines += [
            "## 4. Kết quả Tính toán",
            "",
            f"| Kiểm tra | η | Kết quả |",
            f"|----------|---|---------|",
            f"| Uốn | {eta_M:.3f} | {_eta_icon(eta_M)} {'ĐẠT' if eta_M and eta_M <= 1.0 else 'KHÔNG ĐẠT'} |",
            f"| Cắt | {eta_V:.3f} | {_eta_icon(eta_V)} {'ĐẠT' if eta_V and eta_V <= 1.0 else 'KHÔNG ĐẠT'} |",
            "",
        ]

    # Compare result
    if compare:
        vd = _import_version_differ()
        lines += ["## 5. So sánh Phiên bản", ""]
        lines.append(compare.get("overall_assessment", ""))
        lines.append("")
        diff_report = vd.generate_diff_report(compare)
        # Chỉ lấy phần chi tiết changes
        lines.append(diff_report)

    # Footer
    lines += [
        "---",
        "",
        "> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, "
        "phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm "
        "trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [Report] ✅ Xuất Markdown: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Master Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    input_path: Optional[str] = None,
    input_path_b: Optional[str] = None,
    mode: str = "review",
    output_dir: str = ".",
    conflict_threshold: float = 5.0,
    rebar_pairs: Optional[list] = None,
    demo: bool = False,
    export_docx: bool = True,
    project_dir: Optional[str] = None,
) -> dict:
    """
    Pipeline chính. Trả về dict kết quả đầy đủ.

    Modes:
        read_only  — Chỉ đọc + extract dữ liệu
        review     — Đọc + check xung đột
        full_calc  — Đọc + tính toán + check xung đột + cốt thép
        compare    — So sánh 2 phiên bản
    """
    started_at = datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"  REPORT PIPELINE — Mode: {mode.upper()}")
    print(f"  {started_at}")
    print(f"{'='*60}")

    logs = []
    pipeline_result = {
        "meta": {"mode": mode, "started_at": started_at},
        "read_result": {},
        "conflict_result": None,
        "calc_result": None,
        "rebar_results": [],
        "compare_result": None,
        "pipeline_logs": logs,
    }

    # Demo data
    if demo:
        dr = _import_doc_reader()
        input_doc = dr._demo_result()
        pipeline_result["read_result"] = input_doc
        mode = "review"
        # Add second demo doc for conflict check
        second_doc = {
            "source_file": "DEMO_ETABS",
            "source_type": "ETABS",
            "raw_text_preview": "",
            "engineering_data": {
                "loads": [
                    {"label": "Tĩnh tải sàn", "value": 4.5, "unit": "kN/m²"},
                    {"label": "Hoạt tải sàn", "value": 5.0, "unit": "kN/m²"},
                ],
                "sections": [
                    {"element": "Dầm D1", "b_mm": 250, "h_mm": 600},
                ],
                "materials": [
                    {"type": "concrete", "grade": "B25", "fck_MPa": 20},
                ],
                "soil_params": [],
                "rebar_schedule": [],
            },
        }
        pipeline_result["conflict_result"] = _import_conflict_analyzer().analyze_conflicts(
            [input_doc, second_doc], threshold_pct=conflict_threshold
        )
        # Demo rebar check
        rc = _import_rebar_checker()
        demo_pairs = [
            ("Dầm D1 — Gối", "4Ø25", 1800.0),
            ("Dầm D1 — Nhịp", "3Ø20", 900.0),
        ]
        rebar_results = []
        for elem, notation, as_req in demo_pairs:
            as_prov, _ = rc.parse_rebar_notation(notation)
            rebar_results.append(rc.check_as(elem, as_req, as_prov, rebar_detail=notation))
        pipeline_result["rebar_results"] = rebar_results
        logs.append({"mode": "demo", "note": "Chạy với dữ liệu mẫu"})
        print("  [Demo mode] Sử dụng dữ liệu mẫu")
    elif project_dir:
        dr = _import_doc_reader()
        ca = _import_conflict_analyzer()
        scan_res = dr.scan_project_directory(project_dir)
        pipeline_result["project_inventory"] = scan_res
        print(f"  [Project Scan] Phát hiện {scan_res['summary']['total_files']} files trong {project_dir}")

        found_docs = []
        for cat in ("thuyet_minh", "ban_ve", "bang_tinh"):
            for f_item in scan_res.get("inventory", {}).get(cat, []):
                doc_path = f_item["path"]
                try:
                    d_read = dr.read_document(doc_path)
                    if d_read.get("status") != "ERROR":
                        found_docs.append(d_read)
                except Exception:
                    pass

        if found_docs:
            pipeline_result["read_result"] = found_docs[0]
            pipeline_result["all_read_docs"] = found_docs
            pipeline_result["conflict_result"] = ca.analyze_conflicts(found_docs, threshold_pct=conflict_threshold)
        else:
            pipeline_result["read_result"] = {"source_file": project_dir, "confidence_level": "LOW", "engineering_data": {}}
    else:
        # Stage 1: Read
        if not input_path or not os.path.exists(input_path):
            print(f"  ❌ File không tồn tại: {input_path}")
            return pipeline_result

        if mode == "compare":
            if not input_path_b or not os.path.exists(input_path_b):
                print(f"  ❌ File B không tồn tại: {input_path_b}")
                return pipeline_result
            compare_result = stage_compare(input_path, input_path_b, logs)
            pipeline_result["compare_result"] = compare_result
            # Cũng đọc file A để extract dữ liệu hiển thị
            pipeline_result["read_result"] = stage_read(input_path, logs)
        else:
            pipeline_result["read_result"] = stage_read(input_path, logs)

    input_doc = pipeline_result["read_result"]

    # Stage 2: Calc (chỉ full_calc)
    if mode == "full_calc" and not demo:
        calc_res = stage_calc_simple(input_doc, logs)
        pipeline_result["calc_result"] = calc_res

    # Stage 3: Conflict check
    if mode in ("review", "full_calc") and not pipeline_result["conflict_result"] and not demo:
        # Cần ít nhất 2 docs — đây check single doc chỉ C05
        ca = _import_conflict_analyzer()
        conflict_res = ca.analyze_conflicts([input_doc], threshold_pct=conflict_threshold, checks=["C05"])
        pipeline_result["conflict_result"] = conflict_res

    # Stage 4: Rebar check
    if rebar_pairs and not demo:
        rebar_res = stage_rebar_check(input_doc, rebar_pairs, logs)
        pipeline_result["rebar_results"] = rebar_res

    # Stage 5: Write report
    suffix = datetime.now().strftime("%Y%m%d_%H%M")
    out_base = Path(output_dir) / f"REPORT_{suffix}"
    md_path = str(out_base) + ".md"
    json_path = str(out_base) + "_data.json"

    os.makedirs(output_dir, exist_ok=True)
    write_markdown_report(pipeline_result, md_path)

    # Save JSON data
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_result, f, ensure_ascii=False, indent=2)
    print(f"  [Report] ✅ Dữ liệu JSON: {json_path}")

    # Export Word .docx
    if export_docx:
        drb = _import_docx_builder()
        if drb:
            docx_path = str(out_base) + ".docx"
            try:
                drb.build_docx_report(pipeline_result, docx_path)
                pipeline_result["output_docx"] = docx_path
            except Exception as e:
                print(f"  [Report] ⚠️ Xuất Word lỗi: {e}")

    pipeline_result["output_md"] = md_path
    pipeline_result["output_json"] = json_path

    print(f"\n{'='*60}")
    print(f"  ✅ PIPELINE HOÀN THÀNH")
    print(f"  📄 Báo cáo MD:   {md_path}")
    if pipeline_result.get("output_docx"):
        print(f"  📘 Báo cáo DOCX: {pipeline_result['output_docx']}")

    # Confidence gate
    conf = input_doc.get("confidence_level", "LOW")
    if conf == "LOW":
        print(f"  ⚠️  Confidence đầu vào LOW — kết quả cần kiểm tra kỹ trước khi sử dụng")
    elif conf == "MEDIUM":
        print(f"  🟡 Confidence MEDIUM — một số thông tin có thể thiếu")
    else:
        print(f"  🟢 Confidence HIGH — dữ liệu đầu vào đầy đủ")

    print(f"{'='*60}\n")

    return pipeline_result


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="report_pipeline — End-to-End Engineering Report (Sprint 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input",      help="File đầu vào (PDF/DOCX/XLSX/DXF/IFC)")
    parser.add_argument("--input-b",    help="File đầu vào thứ 2 (cho mode compare)")
    parser.add_argument("--project-dir", help="Quét và thẩm tra toàn bộ thư mục dự án")
    parser.add_argument("--mode",       choices=["read_only","review","full_calc","compare"],
                        default="review", help="Chế độ pipeline (mặc định: review)")
    parser.add_argument("--output-dir", default=".", help="Thư mục xuất báo cáo")
    parser.add_argument("--threshold",  type=float, default=5.0,
                        help="Ngưỡng %% tải trọng cho conflict (mặc định 5.0)")
    parser.add_argument("--rebar",      nargs="+",
                        help="Cặp kiểm tra thép: 'DamD1:1520:4Ø25' (element:as_req:notation)")
    parser.add_argument("--no-docx",    action="store_true", help="Không xuất file Word .docx")
    parser.add_argument("--demo",       action="store_true", help="Chạy demo")
    args = parser.parse_args()

    rebar_pairs = []
    if args.rebar:
        for item in args.rebar:
            parts = item.split(":")
            if len(parts) == 3:
                rebar_pairs.append((parts[0], parts[2], float(parts[1])))

    result = run_pipeline(
        input_path=args.input,
        input_path_b=args.input_b,
        mode=args.mode,
        output_dir=args.output_dir,
        conflict_threshold=args.threshold,
        rebar_pairs=rebar_pairs if rebar_pairs else None,
        demo=args.demo,
        export_docx=not args.no_docx,
        project_dir=args.project_dir,
    )

    if result.get("output_md"):
        print(f"Báo cáo: {result['output_md']}")


if __name__ == "__main__":
    main()
