#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_VERIFY Loại 6: Cross-Document Conflict & Document Control Checker
Đối chiếu chéo 5 nguồn hồ sơ (Bản vẽ KC, Bản vẽ KT, Bản vẽ MEP, Mô hình FEM, Địa chất & BOQ)
từ project_truth_graph.json theo 8 quy tắc CDC-01 đến CDC-08.
"""

import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
import json
import argparse
from datetime import datetime
from pathlib import Path

STAGE_ORDER = {
    "S1": 1, "CONCEPT": 1,
    "S2": 2, "FEED": 2,
    "S3": 3, "TKCS": 3, "BASIC_DESIGN": 3,
    "S4": 4, "TKKT": 4, "TECH_DESIGN": 4,
    "S5": 5, "BVTC": 5, "SHOP_DRAWING": 5,
}

LEGACY_CONCRETE_MAP = {
    "M150": "B12.5", "M200": "B15", "M250": "B20", "M300": "B22.5",
    "M350": "B25", "M400": "B30", "M450": "B35", "M500": "B40", "M600": "B45",
}

def normalize_concrete(grade: str) -> str:
    g = str(grade or "").strip().upper()
    return LEGACY_CONCRETE_MAP.get(g, g)

def run_conflict_checks(graph: dict) -> dict:
    """
    Thực thi 8 quy tắc kiểm soát xung đột hồ sơ chéo (CDC-01 -> CDC-08).
    """
    issues = []

    def add_issue(rule_id: str, severity: str, disciplines: str, title: str,
                  detail: str, action: str, deadline_days: int = 7):
        issues.append({
            "Rule_ID": rule_id,
            "Severity": severity,
            "Disciplines": disciplines,
            "Title": title,
            "Detail": detail,
            "Action": action,
            "Deadline_Days": deadline_days,
        })

    docs = graph.get("documents_registry", {})

    # --- CDC-01: Đồng bộ giai đoạn hồ sơ KC vs KT ---
    arch_stage = str(docs.get("ARCH", {}).get("stage", "")).upper()
    struc_stage = str(docs.get("STRUC", {}).get("stage", "")).upper()
    if arch_stage in STAGE_ORDER and struc_stage in STAGE_ORDER:
        if STAGE_ORDER[struc_stage] > STAGE_ORDER[arch_stage]:
            add_issue(
                "CDC-01", "CRITICAL", "KC + KT",
                f"Giai đoạn hồ sơ không đồng bộ (KC: {struc_stage} > KT: {arch_stage})",
                f"Hồ sơ Kết cấu đã ở giai đoạn {struc_stage} trong khi Kiến trúc mới ở giai đoạn {arch_stage}.",
                "Phê duyệt hồ sơ Kiến trúc trước và rà soát đồng bộ lại Kết cấu theo Nghị định 15/2021/NĐ-CP.",
                5
            )

    # --- CDC-02: Kiểm tra thiếu bộ môn bắt buộc ---
    required_disciplines = graph.get("required_disciplines", ["ARCH", "STRUC", "MEP_ELEC", "MEP_PLUMB"])
    for req_disc in required_disciplines:
        info = docs.get(req_disc, {})
        if not info or info.get("present") is False:
            add_issue(
                "CDC-02", "MAJOR", req_disc,
                f"Thiếu hồ sơ bộ môn bắt buộc: {req_disc}",
                f"Không tìm thấy dữ liệu hoặc bản vẽ của bộ môn {req_disc} trong bộ hồ sơ đầu vào.",
                f"Bổ sung đầy đủ hồ sơ bộ môn {req_disc} trước khi trình thẩm định.",
                10
            )

    # --- CDC-03: Xung đột mác vật liệu giữa các tài liệu ---
    mats = graph.get("materials", {})
    concrete_by_source = {}
    for src, mdata in mats.items():
        if isinstance(mdata, dict) and mdata.get("concrete_grade"):
            raw_g = mdata["concrete_grade"]
            norm_g = normalize_concrete(raw_g)
            concrete_by_source[src] = (raw_g, norm_g)
            if raw_g.upper().startswith("M") and norm_g.startswith("B"):
                add_issue(
                    "CDC-03", "WARNING", "KC",
                    f"Sử dụng ký hiệu mác bê tông cũ '{raw_g}' tại nguồn '{src}'",
                    f"Nguồn '{src}' ghi '{raw_g}'. Theo TCVN 5574:2018 phải ghi cấp độ bền '{norm_g}'.",
                    f"Đổi ký hiệu trên bản vẽ/thuyết minh/BOQ sang cấp độ bền '{norm_g}'.",
                    7
                )

    unique_norm_grades = set(v[1] for v in concrete_by_source.values())
    if len(unique_norm_grades) > 1:
        detail_pairs = ", ".join([f"{s}: {r} ({n})" for s, (r, n) in concrete_by_source.items()])
        add_issue(
            "CDC-03", "CRITICAL", "KC + BOQ + FEM",
            "Xung đột cấp độ bền bê tông giữa các tài liệu",
            f"Phát hiện nhiều cấp độ bền khác nhau cho cùng hạng mục: {detail_pairs}.",
            "Thống nhất cấp độ bền bê tông giữa Bản vẽ, Thuyết minh, Mô hình ETABS và Dự toán BOQ.",
            5
        )

    # --- CDC-04: Xung đột cao độ tầng KC vs KT vs FEM ---
    levels = graph.get("grids_and_levels", {}).get("story_levels", [])
    for lv in levels:
        story = lv.get("story", "?")
        z_kc = lv.get("z_struc_mm")
        z_kt = lv.get("z_arch_mm")
        z_fem = lv.get("z_fem_mm")
        finish_t = lv.get("finish_thickness_mm", 0)

        if z_kc is not None and z_kt is not None:
            delta = (z_kt - finish_t) - z_kc
            if abs(delta) > 5:
                add_issue(
                    "CDC-04", "CRITICAL", "KC + KT",
                    f"Cao độ sàn {story} lệch {delta:+.0f}mm giữa KC và KT",
                    f"Tầng {story}: KC = {z_kc}mm, KT = {z_kt}mm (lớp hoàn thiện = {finish_t}mm) -> Lệch {delta:+.0f}mm.",
                    "Thống nhất lại cao độ sàn kết cấu và hoàn thiện giữa KC và KT để tránh sai bậc thang và ngưỡng cửa.",
                    5
                )

        if z_kc is not None and z_fem is not None:
            delta_fem = z_fem - z_kc
            if abs(delta_fem) > 10:
                add_issue(
                    "CDC-04", "CRITICAL", "KC + FEM",
                    f"Cao độ sàn {story} trong mô hình FEM lệch {delta_fem:+.0f}mm so với bản vẽ KC",
                    f"Tầng {story}: KC = {z_kc}mm, FEM = {z_fem}mm -> Lệch {delta_fem:+.0f}mm.",
                    "Cập nhật lại cao độ Story trong mô hình ETABS/SAP2000 đúng với bản vẽ kết cấu.",
                    5
                )

    # --- CDC-05: Xung đột lưới trục KC vs KT vs MEP ---
    grids = graph.get("grids_and_levels", {})
    w_kc = grids.get("total_width_x_mm", {}).get("STRUC")
    for other_disc in ("ARCH", "MEP"):
        w_other = grids.get("total_width_x_mm", {}).get(other_disc)
        if w_kc is not None and w_other is not None and abs(w_other - w_kc) > 10:
            diff = w_other - w_kc
            add_issue(
                "CDC-05", "MAJOR", f"KC + {other_disc}",
                f"Tổng chiều rộng lưới trục X của {other_disc} lệch {diff:+.0f}mm so với KC",
                f"Tổng bề rộng mặt bằng KC = {w_kc}mm nhưng {other_disc} = {w_other}mm (sai lệch {diff:+.0f}mm).",
                f"Cập nhật toàn bộ mặt bằng bộ môn {other_disc} theo đúng lưới trục Kết cấu.",
                7
            )

    l_kc = grids.get("total_length_y_mm", {}).get("STRUC")
    for other_disc in ("ARCH", "MEP"):
        l_other = grids.get("total_length_y_mm", {}).get(other_disc)
        if l_kc is not None and l_other is not None and abs(l_other - l_kc) > 10:
            diff_y = l_other - l_kc
            add_issue(
                "CDC-05", "MAJOR", f"KC + {other_disc}",
                f"Tổng chiều dài lưới trục Y của {other_disc} lệch {diff_y:+.0f}mm so với KC",
                f"Tổng chiều dài mặt bằng KC = {l_kc}mm nhưng {other_disc} = {l_other}mm (sai lệch {diff_y:+.0f}mm).",
                f"Cập nhật toàn bộ mặt bằng bộ môn {other_disc} theo đúng lưới trục Kết cấu.",
                7
            )

    # --- CDC-06: Kiểm tra đường truyền tải cột & Cột mồ côi ---
    columns = graph.get("elements", {}).get("columns", [])
    for col in columns:
        cid = col.get("id", "?")
        stories_present = col.get("stories_present", [])
        has_foundation = col.get("has_foundation", True)
        in_arch = col.get("in_arch_plan", True)

        if not has_foundation or (stories_present and "T1" not in stories_present and "F1" not in stories_present and "Tang_1" not in stories_present):
            add_issue(
                "CDC-06", "MAJOR", "KC + KT",
                f"Cột {cid} xuất hiện tại {stories_present} nhưng thiếu cột tầng dưới / móng đỡ",
                f"Cột {cid} (tiết diện {col.get('section', '?')}) chỉ xuất hiện ở {stories_present}, has_foundation={has_foundation}, in_arch={in_arch}.",
                f"Kiểm tra đường truyền tải của cột {cid}, bổ sung chi tiết dầm chuyển/móng và đồng bộ với mặt bằng Kiến trúc.",
                7
            )

        if not in_arch:
            add_issue(
                "CDC-06", "MAJOR", "KC + KT",
                f"Cột {cid} có trong KC nhưng không xuất hiện trên mặt bằng Kiến trúc",
                f"Cột {cid} (tiết diện {col.get('section', '?')}) chưa được thể hiện trên bản vẽ kiến trúc, nguy cơ chiếm dụng không gian sử dụng.",
                f"Phối hợp với Kiến trúc sư để thể hiện vị trí cột {cid} hoặc điều chỉnh tim cột.",
                7
            )

    # --- CDC-07: Kiểm tra tĩnh không đáy dầm vs MEP âm trần ---
    beams = graph.get("elements", {}).get("beams", [])
    for bm in beams:
        bid = bm.get("id", "?")
        z_floor = bm.get("story_elevation_mm")
        h_beam = bm.get("h_mm")
        z_ceil = bm.get("ceiling_aff_mm")
        mep_req = bm.get("mep_clearance_req_mm", 450)

        if all(v is not None for v in (z_floor, h_beam, z_ceil)):
            beam_bot = z_floor - h_beam
            mep_space = beam_bot - z_ceil
            if mep_space < mep_req:
                sev = "CRITICAL" if mep_space < 250 else "MAJOR"
                add_issue(
                    "CDC-07", sev, "KC + MEP + KT",
                    f"Không gian MEP dưới đáy dầm {bid} không đủ ({mep_space:.0f}mm < {mep_req:.0f}mm)",
                    f"Đáy dầm {bid} (h={h_beam}mm) ở cốt +{beam_bot}mm AFF, trần giả ở +{z_ceil}mm -> Khoảng MEP còn {mep_space:.0f}mm (yêu cầu >= {mep_req:.0f}mm).",
                    "Giảm chiều cao dầm (tăng bề rộng b), hạ cốt trần hoàn thiện hoặc bố trí lỗ xuyên dầm có gia cường.",
                    7
                )

    # --- CDC-08: Kiểm tra mũi cọc trong lớp đất địa chất ---
    geo = graph.get("geotech", {})
    pile_tip_spt = geo.get("pile_tip_layer_spt")
    if pile_tip_spt is not None and pile_tip_spt < 15:
        add_issue(
            "CDC-08", "CRITICAL", "KC + GEOTECH",
            f"Mũi cọc đặt trong lớp đất yếu (N_SPT = {pile_tip_spt} < 15)",
            f"Cao độ mũi cọc thiết kế ({geo.get('pile_tip_elev_m')}m) nằm trong lớp đất có N_SPT = {pile_tip_spt}, nguy cơ lún vượt giới hạn theo TCVN 10304:2025.",
            "Tăng chiều dài cọc để ngàm mũi cọc vào lớp đất tốt hoặc tính toán kiểm tra lún nhóm cọc chi tiết.",
            5
        )

    critical_cnt = sum(1 for i in issues if i["Severity"] == "CRITICAL")
    major_cnt = sum(1 for i in issues if i["Severity"] == "MAJOR")
    warning_cnt = sum(1 for i in issues if i["Severity"] == "WARNING")
    status = "CRITICAL" if critical_cnt > 0 else ("MAJOR" if major_cnt > 0 else ("WARNING" if warning_cnt > 0 else "PASS"))

    return {
        "Verification_Type": "Cross-Document-Conflict-Control",
        "Timestamp": datetime.now().isoformat(),
        "Project_Name": graph.get("project_name", "N/A"),
        "Overall_Status": status,
        "Summary": {
            "Total_Issues": len(issues),
            "Critical_Count": critical_cnt,
            "Major_Count": major_cnt,
            "Warning_Count": warning_cnt,
        },
        "Issues": issues,
    }


def format_markdown_report(result: dict) -> str:
    """Format kết quả kiểm tra xung đột thành báo cáo Markdown trực quan."""
    md = []
    pname = result.get("Project_Name", "Dự Án")
    summary = result.get("Summary", {})
    status = result.get("Overall_Status", "UNKNOWN")

    status_badge = "🔴 FAILED (CÓ LỖI NGHIÊM TRỌNG)" if status == "CRITICAL" else (
        "🟠 MAJOR WARNING" if status == "MAJOR" else ("🟡 CẢNH BÁO" if status == "WARNING" else "🟢 ĐẠT")
    )

    md.append(f"# BÁO CÁO KIỂM SOÁT XUNG ĐỘT HỒ SƠ CHÉO (CROSS-DOCUMENT CONTROL)")
    md.append(f"- **Dự án:** {pname}")
    md.append(f"- **Thời điểm kiểm tra:** {result.get('Timestamp', '')}")
    md.append(f"- **Đánh giá tổng thể:** {status_badge}")
    md.append("")
    md.append("## 1. TỔNG HỢP VẤN ĐỀ THEO MỨC ĐỘ")
    md.append(f"| Mức độ | Số lượng |")
    md.append(f"| :--- | :---: |")
    md.append(f"| 🔴 CRITICAL (Bắt buộc xử lý ngay) | **{summary.get('Critical_Count', 0)}** |")
    md.append(f"| 🟠 MAJOR (Cần làm rõ trước khi thi công) | **{summary.get('Major_Count', 0)}** |")
    md.append(f"| 🟡 WARNING (Cảnh báo ký hiệu/chuẩn hóa) | **{summary.get('Warning_Count', 0)}** |")
    md.append(f"| **Tổng số vấn đề phát hiện** | **{summary.get('Total_Issues', 0)}** |")
    md.append("")
    md.append("## 2. DANH SÁCH CHI TIẾT CÁC XUNG ĐỘT")
    md.append("| STT | Mã luật | Mức độ | Bộ môn | Tiêu đề xung đột | Biện pháp xử lý | Hạn (ngày) |")
    md.append("| :---: | :---: | :---: | :---: | :--- | :--- | :---: |")

    for idx, iss in enumerate(result.get("Issues", []), 1):
        sev_icon = "🔴 CRITICAL" if iss["Severity"] == "CRITICAL" else ("🟠 MAJOR" if iss["Severity"] == "MAJOR" else "🟡 WARNING")
        md.append(f"| {idx} | `{iss['Rule_ID']}` | {sev_icon} | {iss['Disciplines']} | {iss['Title']} | {iss['Action']} | {iss['Deadline_Days']} |")

    md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Cross-Document Conflict Checker (CDC-01 to CDC-08)")
    parser.add_argument("--graph", required=True, help="File project_truth_graph.json")
    parser.add_argument("--output", help="File JSON kết quả")
    parser.add_argument("--report", help="File Markdown báo cáo kết quả (.md)")

    args = parser.parse_args()

    with open(args.graph, "r", encoding="utf-8") as f:
        graph = json.load(f)

    result = run_conflict_checks(graph)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(format_markdown_report(result))

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
