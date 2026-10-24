"""
conflict_analyzer.py — Cross-Document Conflict Checker
=======================================================
Sprint 4 · Task 4.2

Mục đích:
    Nhận 2+ tài liệu đã được đọc bởi doc_reader.py / etabs_com_reader.py / ifc_parser.py
    và phát hiện 5 loại xung đột kỹ thuật tự động:

    C01 — LOAD_MISMATCH     : Tải trọng ETABS ≠ Thuyết minh PDF (ngưỡng > 5%)
    C02 — SECTION_MISMATCH  : Tiết diện thiết kế ≠ tiết diện trong mô hình
    C03 — MATERIAL_MISMATCH : Grade vật liệu khác nhau giữa các tài liệu
    C04 — GEOTECH_MISMATCH  : SPT/sức chịu tải móng không tương thích
    C05 — TCVN_VIOLATION    : Eta vượt ngưỡng / không đạt TCVN check

Đầu vào:
    Danh sách dict (output của doc_reader / etabs / ifc), hoặc đường dẫn JSON.

Đầu ra JSON:
    {
        "checked_at": "...",
        "sources_checked": ["file_A.pdf", "ETABS_model"],
        "conflict_summary": {"total": 5, "CRITICAL": 2, "HIGH": 1, "MEDIUM": 2, "LOW": 0},
        "conflicts": [{...}],
        "passes": [{...}],
        "Calculation_Logs": [...],
        "Standard_Method": "conflict_analyzer v1.0 Sprint-4"
    }

Sử dụng:
    python conflict_analyzer.py --a doc_A.json --b doc_B.json [--output conflicts.json]
    python conflict_analyzer.py --a pdf_result.json --b etabs_result.json --threshold 5.0
    python conflict_analyzer.py --demo
"""

import sys
import os
import json
import math
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Data Models
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "OK": 4}

# TCVN capped utilization ratios (from STANDARDS_LOCK / policy_engine)
TCVN_LIMITS = {
    "eta_flexure":   1.0,  # Uốn TCVN 5574:2018 §8
    "eta_shear":     1.0,  # Cắt
    "eta_crack":     1.0,  # Nứt SLS
    "eta_deflect":   1.0,  # Võng SLS l/250
    "eta_buckling":  1.0,  # Ổn định cột TCVN 5575:2024
}

# Bảng fck theo grade bê tông (MPa)
FCK_TABLE = {
    "B15":12, "B20":16, "B25":20, "B30":25, "B35":30,
    "B40":35, "B45":38, "B50":42, "B60":52,
}

# Bảng fy theo grade thép (MPa)
FY_TABLE = {
    "AI":235, "AII":295, "AIII":390, "AIV":490,
    "CB240T":240, "CB300T":300, "CB300V":300,
    "CB400V":400, "CB500V":500,
}

# Bảng Rbt theo grade bê tông (MPa) - TCVN 5574:2018 Bảng 6
RBT_TABLE = {
    "B15": 0.75, "B20": 0.90, "B25": 1.05, "B30": 1.15, "B35": 1.30,
    "B40": 1.40, "B45": 1.45, "B50": 1.55, "B60": 1.70,
    "C20/25": 1.05, "C25/30": 1.15, "C30/37": 1.30, "C35/45": 1.40,
}

# Bảng Rs theo grade thép (MPa) - TCVN 5574:2018 Bảng 13
RS_TABLE = {
    "CB240T": 210, "CB300T": 260, "CB300V": 260,
    "CB400V": 350, "CB500V": 435, "AI": 210, "AII": 260, "AIII": 350,
    "B500B": 435, "B500C": 435, "GRADE 60": 400, "GR 60": 400,
}


def _make_conflict(
    conflict_id: str,
    conflict_type: str,
    severity: str,
    param: str,
    val_a: dict,
    val_b: dict,
    delta_pct: Optional[float],
    description: str,
    recommendation: str,
) -> dict:
    return {
        "id": conflict_id,
        "type": conflict_type,
        "severity": severity,
        "param": param,
        "value_A": val_a,
        "value_B": val_b,
        "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
        "description": description,
        "recommendation": recommendation,
    }


def _make_pass(pass_id: str, param: str, description: str) -> dict:
    return {"id": pass_id, "param": param, "description": description, "result": "PASS"}


# ─────────────────────────────────────────────────────────────────────────────
# 2. C01 — Load Mismatch
# ─────────────────────────────────────────────────────────────────────────────

def check_load_mismatch(
    doc_a: dict, doc_b: dict, threshold_pct: float = 5.0, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    So sánh tải trọng giữa 2 nguồn tài liệu.
    Khớp theo label (fuzzy match đơn giản).
    """
    conflicts, passes = [], []
    ctr = 0

    loads_a = doc_a.get("engineering_data", {}).get("loads", [])
    loads_b = doc_b.get("engineering_data", {}).get("loads", [])
    src_a = doc_a.get("source_file", "Source A")
    src_b = doc_b.get("source_file", "Source B")

    if not loads_a or not loads_b:
        if logs is not None:
            logs.append({"step": "C01", "note": "Không đủ dữ liệu tải trọng để so sánh", "skipped": True})
        return conflicts, passes

    # Normalize label để so sánh
    def norm(label: str) -> str:
        return re.sub(r"\s+", " ", label.lower().strip()) if label else ""

    import re
    matched = set()
    for la in loads_a:
        label_a = norm(la.get("label", ""))
        unit_a = la.get("unit", "")
        val_a = la.get("value")
        if val_a is None:
            continue

        # Tìm label tương ứng trong b
        best_b = None
        best_score = 0
        for lb in loads_b:
            label_b = norm(lb.get("label", ""))
            # simple token overlap score
            tokens_a = set(label_a.split())
            tokens_b = set(label_b.split())
            if not tokens_a or not tokens_b:
                continue
            score = len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))
            if score > best_score and lb.get("value") is not None:
                best_score = score
                best_b = lb

        if best_b is None or best_score < 0.3:
            # Không tìm được cặp — coi là tải thiếu ở phía B
            ctr += 1
            conflicts.append(_make_conflict(
                f"C01-{ctr:03d}", "LOAD_MISMATCH", "MEDIUM",
                la.get("label", f"Tải {ctr}"),
                {"source": src_a, "value": val_a, "unit": unit_a},
                {"source": src_b, "value": "N/A", "unit": ""},
                None,
                f"Tải '{la.get('label')}' tìm thấy trong {src_a} nhưng không có trong {src_b}.",
                f"Kiểm tra lại bảng tải trọng trong {src_b} — có thể đặt tên khác hoặc bị thiếu.",
            ))
            continue

        val_b = best_b.get("value")
        if val_b == 0:
            continue

        delta = abs(val_a - val_b) / abs(val_b) * 100.0
        ctr += 1

        if delta > threshold_pct:
            severity = "CRITICAL" if delta > 20 else "HIGH" if delta > 10 else "MEDIUM"
            conflicts.append(_make_conflict(
                f"C01-{ctr:03d}", "LOAD_MISMATCH", severity,
                la.get("label", f"Tải {ctr}"),
                {"source": src_a, "value": val_a, "unit": unit_a},
                {"source": src_b, "value": val_b, "unit": best_b.get("unit", "")},
                delta,
                f"Tải '{la.get('label')}': {src_a}={val_a}{unit_a} vs {src_b}={val_b}{best_b.get('unit','')} — chênh {delta:.1f}%.",
                f"Chênh lệch {delta:.1f}% vượt ngưỡng {threshold_pct}%. Xác nhận lại tải với thiết kế.",
            ))
        else:
            passes.append(_make_pass(
                f"C01-P{ctr:03d}",
                la.get("label", ""),
                f"Tải khớp: {val_a} ≈ {val_b} {unit_a} (chênh {delta:.1f}% ≤ {threshold_pct}%)",
            ))
        matched.add(id(best_b))

    if logs is not None:
        logs.append({"step": "C01", "conflicts": len(conflicts), "passes": len(passes)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 3. C02 — Section Mismatch
# ─────────────────────────────────────────────────────────────────────────────

def check_section_mismatch(
    doc_a: dict, doc_b: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """So sánh tiết diện cấu kiện giữa 2 tài liệu."""
    conflicts, passes = [], []
    sec_a = doc_a.get("engineering_data", {}).get("sections", [])
    sec_b = doc_b.get("engineering_data", {}).get("sections", [])
    src_a = doc_a.get("source_file", "Source A")
    src_b = doc_b.get("source_file", "Source B")

    if not sec_a or not sec_b:
        if logs:
            logs.append({"step": "C02", "note": "Không đủ dữ liệu tiết diện", "skipped": True})
        return conflicts, passes

    # Build lookup từ sec_b theo element name
    b_lookup = {}
    for s in sec_b:
        elem = (s.get("element") or "").upper().strip()
        if elem:
            b_lookup[elem] = s

    ctr = 0
    for sa in sec_a:
        ctr += 1
        elem_key = (sa.get("element") or "").upper().strip()
        sb = b_lookup.get(elem_key)

        if not sb:
            # Thử tìm kiếm gần đúng
            for k, v in b_lookup.items():
                if elem_key in k or k in elem_key:
                    sb = v
                    break

        if sb is None:
            conflicts.append(_make_conflict(
                f"C02-{ctr:03d}", "SECTION_MISMATCH", "MEDIUM",
                elem_key or f"CK-{ctr}",
                {"source": src_a, "b_mm": sa.get("b_mm"), "h_mm": sa.get("h_mm")},
                {"source": src_b, "value": "Không tìm thấy"},
                None,
                f"Cấu kiện '{elem_key}' có trong {src_a} nhưng không tìm thấy trong {src_b}.",
                "Kiểm tra lại tên cấu kiện hoặc bổ sung vào tài liệu thứ 2.",
            ))
            continue

        b_bh = (sb.get("b_mm"), sb.get("h_mm"))
        a_bh = (sa.get("b_mm"), sa.get("h_mm"))

        if None in a_bh or None in b_bh:
            continue

        if a_bh != b_bh:
            # Tính delta diện tích
            area_a = a_bh[0] * a_bh[1]
            area_b = b_bh[0] * b_bh[1]
            delta_area = abs(area_a - area_b) / area_b * 100 if area_b else 0
            severity = "CRITICAL" if delta_area > 30 else "HIGH" if delta_area > 10 else "MEDIUM"
            conflicts.append(_make_conflict(
                f"C02-{ctr:03d}", "SECTION_MISMATCH", severity,
                elem_key,
                {"source": src_a, "b_mm": a_bh[0], "h_mm": a_bh[1]},
                {"source": src_b, "b_mm": b_bh[0], "h_mm": b_bh[1]},
                delta_area,
                f"{elem_key}: {src_a}={a_bh[0]}×{a_bh[1]}mm vs {src_b}={b_bh[0]}×{b_bh[1]}mm (ΔA={delta_area:.1f}%).",
                f"Xác nhận tiết diện chính xác với kỹ sư thiết kế — chênh lệch diện tích {delta_area:.1f}%.",
            ))
        else:
            passes.append(_make_pass(
                f"C02-P{ctr:03d}", elem_key,
                f"Tiết diện khớp: {a_bh[0]}×{a_bh[1]}mm",
            ))

    if logs:
        logs.append({"step": "C02", "conflicts": len(conflicts), "passes": len(passes)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 4. C03 — Material Mismatch
# ─────────────────────────────────────────────────────────────────────────────

def check_material_mismatch(
    doc_a: dict, doc_b: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """So sánh grade vật liệu giữa 2 tài liệu."""
    conflicts, passes = [], []
    mat_a = doc_a.get("engineering_data", {}).get("materials", [])
    mat_b = doc_b.get("engineering_data", {}).get("materials", [])
    src_a = doc_a.get("source_file", "Source A")
    src_b = doc_b.get("source_file", "Source B")

    if not mat_a or not mat_b:
        if logs:
            logs.append({"step": "C03", "note": "Không đủ dữ liệu vật liệu", "skipped": True})
        return conflicts, passes

    # Group by type
    def group_by_type(mats):
        out = {}
        for m in mats:
            t = m.get("type", "unknown")
            if t not in out:
                out[t] = []
            out[t].append(m.get("grade", "").upper())
        return out

    ga = group_by_type(mat_a)
    gb = group_by_type(mat_b)

    ctr = 0
    for mat_type in set(list(ga.keys()) + list(gb.keys())):
        grades_a = set(ga.get(mat_type, []))
        grades_b = set(gb.get(mat_type, []))
        ctr += 1

        if not grades_a:
            conflicts.append(_make_conflict(
                f"C03-{ctr:03d}", "MATERIAL_MISMATCH", "MEDIUM",
                mat_type,
                {"source": src_a, "grades": "Không có"},
                {"source": src_b, "grades": list(grades_b)},
                None,
                f"Vật liệu '{mat_type}' có trong {src_b} nhưng không trong {src_a}.",
                "Bổ sung khai báo vật liệu vào thuyết minh.",
            ))
        elif not grades_b:
            conflicts.append(_make_conflict(
                f"C03-{ctr:03d}", "MATERIAL_MISMATCH", "MEDIUM",
                mat_type,
                {"source": src_a, "grades": list(grades_a)},
                {"source": src_b, "grades": "Không có"},
                None,
                f"Vật liệu '{mat_type}' có trong {src_a} nhưng không trong {src_b}.",
                "Bổ sung khai báo vật liệu vào mô hình.",
            ))
        elif grades_a != grades_b:
            # So sánh cường độ
            fck_delta = None
            try:
                if mat_type == "concrete":
                    fck_a = max(FCK_TABLE.get(g, 0) for g in grades_a)
                    fck_b = max(FCK_TABLE.get(g, 0) for g in grades_b)
                    fck_delta = abs(fck_a - fck_b) / fck_b * 100 if fck_b else None
                elif mat_type == "steel_rebar":
                    fy_a = max(FY_TABLE.get(g, 0) for g in grades_a)
                    fy_b = max(FY_TABLE.get(g, 0) for g in grades_b)
                    fck_delta = abs(fy_a - fy_b) / fy_b * 100 if fy_b else None
            except Exception:
                pass

            severity = "CRITICAL" if (fck_delta and fck_delta > 20) else "HIGH"
            conflicts.append(_make_conflict(
                f"C03-{ctr:03d}", "MATERIAL_MISMATCH", severity,
                mat_type,
                {"source": src_a, "grades": list(grades_a)},
                {"source": src_b, "grades": list(grades_b)},
                fck_delta,
                f"Grade {mat_type}: {src_a}={grades_a} vs {src_b}={grades_b}.",
                "Thống nhất grade vật liệu giữa thuyết minh và mô hình phân tích.",
            ))
        else:
            passes.append(_make_pass(
                f"C03-P{ctr:03d}", mat_type,
                f"Grade khớp: {grades_a}",
            ))

    if logs:
        logs.append({"step": "C03", "conflicts": len(conflicts), "passes": len(passes)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 5. C04 — Geotech vs Foundation Mismatch
# ─────────────────────────────────────────────────────────────────────────────

def check_geotech_mismatch(
    doc_geotech: dict, doc_design: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    So sánh thông số địa chất (SPT) với giả định thiết kế móng.
    Logic đơn giản: nếu SPT trung bình < 10 mà thiết kế dùng móng nông → cảnh báo.
    """
    conflicts, passes = [], []
    soils = doc_geotech.get("engineering_data", {}).get("soil_params", [])
    src_geo = doc_geotech.get("source_file", "Báo cáo ĐCCT")
    src_des = doc_design.get("source_file", "Thiết kế")

    if not soils:
        if logs:
            logs.append({"step": "C04", "note": "Không có dữ liệu SPT", "skipped": True})
        return conflicts, passes

    spt_values = [s.get("SPT_N") for s in soils if s.get("SPT_N") is not None]
    if not spt_values:
        return conflicts, passes

    spt_avg = sum(spt_values) / len(spt_values)
    spt_min = min(spt_values)

    ctr = 0
    # Ngưỡng cứng theo quy ước thực hành TCVN 10304:2014 móng cọc
    if spt_avg < 5:
        ctr += 1
        conflicts.append(_make_conflict(
            f"C04-{ctr:03d}", "GEOTECH_MISMATCH", "CRITICAL",
            "SPT trung bình",
            {"source": src_geo, "SPT_avg": round(spt_avg, 1), "SPT_min": spt_min},
            {"source": src_des, "note": "Cần kiểm tra loại móng"},
            None,
            f"SPT trung bình = {spt_avg:.1f} búa — đất rất yếu, không đủ sức chịu tải cho móng nông.",
            "Xem xét phương án móng cọc. Kiểm tra lại sức chịu tải đất nền theo TCVN 10304:2014.",
        ))
    elif spt_avg < 10:
        ctr += 1
        conflicts.append(_make_conflict(
            f"C04-{ctr:03d}", "GEOTECH_MISMATCH", "HIGH",
            "SPT trung bình",
            {"source": src_geo, "SPT_avg": round(spt_avg, 1)},
            {"source": src_des, "note": "Xác nhận loại móng"},
            None,
            f"SPT trung bình = {spt_avg:.1f} búa — đất yếu đến trung bình.",
            "Xác nhận thiết kế móng tương thích. Tính lún kiểm tra theo TCVN 9362:2012.",
        ))
    else:
        passes.append(_make_pass(
            "C04-P001", "SPT trung bình",
            f"SPT_avg = {spt_avg:.1f} búa — đất tốt, phù hợp thiết kế móng.",
        ))

    if logs:
        logs.append({"step": "C04", "SPT_avg": round(spt_avg, 1), "conflicts": len(conflicts)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 6. C05 — TCVN Violation Check
# ─────────────────────────────────────────────────────────────────────────────

def check_tcvn_violations(
    doc: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    Kiểm tra các chỉ số sử dụng η trong tài liệu so với ngưỡng TCVN.
    Tìm pattern 'eta = 0.95' hoặc 'η = 1.05' trong text.
    """
    import re as _re
    conflicts, passes = [], []
    src = doc.get("source_file", "Tài liệu")
    raw = doc.get("raw_text_preview", "") + " ".join(
        str(v) for v in doc.get("engineering_data", {}).values() if isinstance(v, str)
    )

    # Pattern: η=0.95 | eta=1.05 | η = 0.87
    eta_pat = _re.compile(
        r"""(?:[ηη]|eta)\s*=\s*(?P<eta>[\d]+(?:[.,][\d]+)?)""",
        _re.IGNORECASE | _re.UNICODE,
    )

    ctr = 0
    for m in eta_pat.finditer(raw):
        ctr += 1
        try:
            eta = float(m.group("eta").replace(",", "."))
        except ValueError:
            continue

        # Lấy context
        snippet = raw[max(0, m.start()-40):m.end()+40].strip()

        if eta > 1.0:
            conflicts.append(_make_conflict(
                f"C05-{ctr:03d}", "TCVN_VIOLATION", "CRITICAL",
                f"Chỉ số sử dụng η = {eta}",
                {"source": src, "eta": eta, "context": snippet[:80]},
                {"limit": 1.0, "standard": "TCVN 5574:2018 / 5575:2024"},
                (eta - 1.0) * 100,
                f"η = {eta} > 1.0 — KHÔNG ĐẠT. Context: '{snippet[:60]}'",
                "Tăng tiết diện hoặc bổ sung cốt thép. Tính lại theo TCVN.",
            ))
        elif eta > 0.9:
            conflicts.append(_make_conflict(
                f"C05-{ctr:03d}", "TCVN_VIOLATION", "MEDIUM",
                f"η = {eta} — sát ngưỡng",
                {"source": src, "eta": eta, "context": snippet[:80]},
                {"limit": 1.0, "standard": "TCVN 5574:2018"},
                None,
                f"η = {eta} — đạt nhưng sát giới hạn (> 0.90).",
                "Cảnh báo W001: xem xét tăng nhẹ tiết diện để tăng dự trữ an toàn.",
            ))
        else:
            passes.append(_make_pass(
                f"C05-P{ctr:03d}",
                f"η = {eta}",
                f"Đạt TCVN — η = {eta} ≤ 0.90 (an toàn hợp lý)",
            ))

    if logs:
        logs.append({"step": "C05", "eta_found": ctr, "violations": len(conflicts)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 6b. C07 — Anchorage & Lap Length Check (TCVN 5574:2018 §10.3)
# ─────────────────────────────────────────────────────────────────────────────

def check_anchorage_lap(
    doc: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    C07: Kiểm tra chiều dài neo cốt thép (L_an / L_neo) và nối chồng (L_lap / L_noi)
    so với yêu cầu tối thiểu theo TCVN 5574:2018 Điều 10.3.
    """
    import re as _re
    conflicts, passes = [], []
    src = doc.get("source_file", "Tài liệu")
    raw = doc.get("raw_text_preview", "")
    eng = doc.get("engineering_data", {})
    mats = eng.get("materials", [])

    conc_grade = next((m["grade"] for m in mats if m.get("type") == "concrete"), "B25")
    steel_grade = next((m["grade"] for m in mats if m.get("type") == "steel_rebar"), "CB400V")
    Rbt = RBT_TABLE.get(conc_grade, 1.05)
    Rs = RS_TABLE.get(steel_grade, 350)
    R_bond = 2.5 * 1.0 * Rbt  # Cốt thép có gờ, eta1=2.5, eta2=1.0

    neo_pat = _re.compile(
        r"""(?:L(?:_?(?:an|neo))\s*[:=]\s*(?P<l_an>\d+)\s*(?:mm)?|neo\s*(?P<mult_an>\d+)\s*d)""",
        _re.IGNORECASE | _re.UNICODE,
    )
    noi_pat = _re.compile(
        r"""(?:L(?:_?(?:lap|n[oố]i))\s*[:=]\s*(?P<l_lap>\d+)\s*(?:mm)?|n[oố]i\s*(?:chồng)?\s*(?P<mult_lap>\d+)\s*d)""",
        _re.IGNORECASE | _re.UNICODE,
    )

    rebars = eng.get("rebar_schedule", [])
    dia_sample = max([r.get("dia_mm", 20.0) for r in rebars] or [20.0])

    ctr = 0
    for m in neo_pat.finditer(raw):
        ctr += 1
        d = dia_sample
        L0_an = (Rs * d) / (4.0 * R_bond)
        Lan_req = max(0.3 * L0_an, 15.0 * d, 200.0)
        Lbd_req = 1.0 * L0_an

        Lan_prov = float(m.group("l_an")) if m.group("l_an") else float(m.group("mult_an")) * d

        if Lan_prov < Lan_req or Lan_prov < 0.8 * Lbd_req:
            conflicts.append(_make_conflict(
                f"C07-{ctr:03d}", "ANCHORAGE_VIOLATION", "CRITICAL",
                f"Chiều dài neo cốt thép d={d}mm ({conc_grade}, {steel_grade})",
                {"source": src, "Lan_prov": Lan_prov, "unit": "mm"},
                {"Lan_req": round(Lbd_req, 1), "Lan_min": round(Lan_req, 1), "standard": "TCVN 5574:2018 §10.3.1"},
                round((Lan_req - Lan_prov) / Lan_req * 100, 1) if Lan_prov < Lan_req else 0.0,
                f"Chiều dài neo L_neo = {Lan_prov}mm < L_bd = {round(Lbd_req, 1)}mm — không đủ chiều dài neo.",
                "Tăng chiều dài đoạn neo hoặc sử dụng móc neo/bản neo cơ khí theo TCVN 5574:2018.",
            ))
        else:
            passes.append(_make_pass(
                f"C07-P{ctr:03d}",
                f"Chiều dài neo L_neo = {Lan_prov}mm",
                f"Đạt TCVN 5574:2018 — L_neo = {Lan_prov}mm ≥ L_min = {round(Lan_req, 1)}mm.",
            ))

    for m in noi_pat.finditer(raw):
        ctr += 1
        d = dia_sample
        L0_an = (Rs * d) / (4.0 * R_bond)
        Llap_req = max(0.4 * 1.2 * L0_an, 20.0 * d, 250.0)
        Llap_calc = 1.2 * L0_an

        Llap_prov = float(m.group("l_lap")) if m.group("l_lap") else float(m.group("mult_lap")) * d

        if Llap_prov < Llap_req or Llap_prov < 0.8 * Llap_calc:
            conflicts.append(_make_conflict(
                f"C07-{ctr:03d}", "LAP_SPLICE_VIOLATION", "CRITICAL",
                f"Chiều dài nối chồng cốt thép d={d}mm ({conc_grade}, {steel_grade})",
                {"source": src, "Llap_prov": Llap_prov, "unit": "mm"},
                {"Llap_calc": round(Llap_calc, 1), "Llap_min": round(Llap_req, 1), "standard": "TCVN 5574:2018 §10.3.2"},
                round((Llap_calc - Llap_prov) / Llap_calc * 100, 1),
                f"Chiều dài nối chồng L_nối = {Llap_prov}mm < {round(Llap_calc, 1)}mm yêu cầu theo TCVN 5574:2018.",
                "Tăng chiều dài đoạn nối buộc hoặc chuyển sang biện pháp nối hàn/ống nối coupler.",
            ))
        else:
            passes.append(_make_pass(
                f"C07-P{ctr:03d}",
                f"Chiều dài nối chồng L_nối = {Llap_prov}mm",
                f"Đạt TCVN 5574:2018 — L_nối = {Llap_prov}mm ≥ L_lap_min.",
            ))

    if logs:
        logs.append({"step": "C07", "checks": ctr, "conflicts": len(conflicts)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 6c. C08 — Rebar Spacing & Ratio Check (TCVN 5574:2018 §10.2 & §10.3)
# ─────────────────────────────────────────────────────────────────────────────

def check_rebar_spacing_and_ratio(
    doc: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    C08: Kiểm tra khoảng cách thông thủy a_clear và hàm lượng cốt thép mu:
      - a_clear >= max(d_bar, 25mm với cốt thép dưới, 30mm với cốt thép trên).
      - mu_beam <= 2.5%, mu_column <= 4.0%, mu >= 0.1%.
    """
    conflicts, passes = [], []
    src = doc.get("source_file", "Tài liệu")
    eng = doc.get("engineering_data", {})
    sections = eng.get("sections", [])
    rebars = eng.get("rebar_schedule", [])

    ctr = 0
    c_nom = 25.0

    for sec in sections:
        b = sec.get("b_mm", 0)
        h = sec.get("h_mm", 0)
        elem = sec.get("element", "CK")
        if b <= 0 or h <= 0:
            continue

        rel_rebars = [r for r in rebars if r.get("count") and r.get("dia_mm")]
        if not rel_rebars:
            continue

        rb = rel_rebars[0]
        n = rb.get("count", 2)
        d = rb.get("dia_mm", 20.0)

        # 1. Khoảng cách thông thủy
        if n > 1:
            ctr += 1
            a_clear = (b - 2.0 * c_nom - n * d) / (n - 1.0)
            a_min = max(d, 25.0)

            if a_clear < a_min:
                conflicts.append(_make_conflict(
                    f"C08-{ctr:03d}", "REBAR_SPACING_CONGESTION", "HIGH",
                    f"Khoảng cách thông thủy cốt thép {elem} (b={b}mm, {n}Ø{int(d)})",
                    {"source": src, "a_clear_mm": round(a_clear, 1), "b_mm": b, "n": n, "dia_mm": d},
                    {"a_min_mm": a_min, "standard": "TCVN 5574:2018 §10.2.1"},
                    round((a_min - a_clear) / a_min * 100, 1),
                    f"Khoảng cách thông thủy a_clear = {round(a_clear, 1)}mm < {a_min}mm — cốt thép quá dày.",
                    "Bố trí thành 2 lớp thép hoặc tăng đường kính thép để giảm số lượng thanh.",
                ))
            else:
                passes.append(_make_pass(
                    f"C08-P{ctr:03d}",
                    f"Khoảng cách cốt thép {elem}",
                    f"Đạt — a_clear = {round(a_clear, 1)}mm ≥ {a_min}mm.",
                ))

        # 2. Hàm lượng cốt thép mu
        h0 = h - 40.0
        As = n * math.pi * (d ** 2) / 4.0
        mu = (As / (b * h0)) * 100.0
        is_column = "cột" in elem.lower() or "col" in elem.lower()
        mu_max = 4.0 if is_column else 2.5
        mu_min = 0.1

        ctr += 1
        if mu > mu_max:
            conflicts.append(_make_conflict(
                f"C08-{ctr:03d}", "MAX_REBAR_RATIO_EXCEEDED", "CRITICAL",
                f"Hàm lượng cốt thép {elem} ({n}Ø{int(d)})",
                {"source": src, "mu_pct": round(mu, 2), "As_mm2": round(As, 1)},
                {"mu_max_pct": mu_max, "standard": "TCVN 5574:2018 §10.3"},
                round((mu - mu_max) / mu_max * 100, 1),
                f"Hàm lượng cốt thép mu = {round(mu, 2)}% > {mu_max}% — vượt ngưỡng cho phép, nguy cơ phá hoại giòn.",
                "Tăng kích thước tiết diện b x h để hạ hàm lượng cốt thép về khoảng 1.0 - 1.8% tối ưu.",
            ))
        elif mu < mu_min:
            conflicts.append(_make_conflict(
                f"C08-{ctr:03d}", "MIN_REBAR_RATIO_VIOLATION", "HIGH",
                f"Hàm lượng cốt thép {elem}",
                {"source": src, "mu_pct": round(mu, 2)},
                {"mu_min_pct": mu_min, "standard": "TCVN 5574:2018 §10.3"},
                None,
                f"Hàm lượng cốt thép mu = {round(mu, 2)}% < {mu_min}% — dưới hàm lượng tối thiểu.",
                "Tăng cốt thép để đảm bảo điều kiện hàm lượng tối thiểu chống nứt đột ngột.",
            ))
        else:
            passes.append(_make_pass(
                f"C08-P{ctr:03d}",
                f"Hàm lượng cốt thép {elem}",
                f"Đạt — mu = {round(mu, 2)}% (nằm trong khoảng an toàn {mu_min}% - {mu_max}%).",
            ))

    if logs:
        logs.append({"step": "C08", "checks": ctr, "conflicts": len(conflicts)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 6d. C09 — Pile Capacity vs Reaction Check (TCVN 10304:2014)
# ─────────────────────────────────────────────────────────────────────────────

def check_pile_capacity_match(
    doc_a: dict, doc_b: dict, logs: list = None
) -> Tuple[List[dict], List[dict]]:
    """
    C09: So sánh phản lực đầu cọc P_max (từ mô hình kết cấu) với sức chịu tải
    cho phép của cọc R_cd (từ báo cáo ĐCCT / thiết kế móng).
    """
    import re as _re
    conflicts, passes = [], []
    src_a = doc_a.get("source_file", "Nguồn A")
    src_b = doc_b.get("source_file", "Nguồn B")
    raw_a = doc_a.get("raw_text_preview", "")
    raw_b = doc_b.get("raw_text_preview", "")

    p_pat = _re.compile(r"""(?:P(?:_?(?:max|coc|pile))?\s*[:=]\s*(?P<val>\d+(?:[.,]\d+)?)\s*(?P<unit>kN|T))""", _re.IGNORECASE)
    rcd_pat = _re.compile(r"""(?:(?:R(?:_?(?:cd|cu))?|Q(?:_?a)?|sức\s*chịu\s*tải(?:\s*cọc)?)\s*[:=]\s*(?P<val>\d+(?:[.,]\d+)?)\s*(?P<unit>kN|T))""", _re.IGNORECASE)

    p_val, p_unit = None, "kN"
    rcd_val, rcd_unit = None, "kN"

    for raw in (raw_a, raw_b):
        m1 = p_pat.search(raw)
        if m1 and p_val is None:
            p_val = float(m1.group("val").replace(",", "."))
            p_unit = m1.group("unit")
            if p_unit.upper() == "T":
                p_val *= 9.81
        m2 = rcd_pat.search(raw)
        if m2 and rcd_val is None:
            rcd_val = float(m2.group("val").replace(",", "."))
            rcd_unit = m2.group("unit")
            if rcd_unit.upper() == "T":
                rcd_val *= 9.81

    if p_val and rcd_val:
        eta_pile = p_val / rcd_val
        if eta_pile > 1.0:
            conflicts.append(_make_conflict(
                "C09-001", "PILE_CAPACITY_OVERLOAD", "CRITICAL",
                "Phản lực đầu cọc vs Sức chịu tải tính toán",
                {"source": src_a, "P_max": round(p_val, 1), "unit": "kN"},
                {"source": src_b, "R_cd": round(rcd_val, 1), "unit": "kN", "standard": "TCVN 10304:2014"},
                round((eta_pile - 1.0) * 100, 1),
                f"Phản lực cọc P_max = {round(p_val, 1)}kN > R_cd = {round(rcd_val, 1)}kN (eta = {round(eta_pile, 2)} > 1.0) — Quá tải cọc.",
                "Tăng số lượng cọc, tăng chiều dài cọc hoặc điều chỉnh lại kích thước đài móng.",
            ))
        else:
            passes.append(_make_pass(
                "C09-P001",
                "Sức chịu tải cọc",
                f"Đạt — P_max = {round(p_val, 1)}kN ≤ R_cd = {round(rcd_val, 1)}kN (eta = {round(eta_pile, 2)} ≤ 1.0).",
            ))

    if logs:
        logs.append({"step": "C09", "P_val": p_val, "Rcd_val": rcd_val, "conflicts": len(conflicts)})
    return conflicts, passes


# ─────────────────────────────────────────────────────────────────────────────
# 7. Master Analyzer
# ─────────────────────────────────────────────────────────────────────────────

def analyze_conflicts(
    docs: List[dict],
    threshold_pct: float = 5.0,
    checks: List[str] = None,
) -> dict:
    """
    Chạy toàn bộ các check C01–C09 trên danh sách tài liệu.

    Args:
        docs: List các dict từ doc_reader / etabs_com_reader / ifc_parser.
        threshold_pct: Ngưỡng % cho LOAD_MISMATCH (mặc định 5%).
        checks: Subset check cần chạy, mặc định tất cả ["C01","C02","C03","C04","C05","C07","C08","C09"].

    Returns:
        dict conflict report hoàn chỉnh.
    """
    if checks is None:
        checks = ["C01", "C02", "C03", "C04", "C05", "C07", "C08", "C09"]

    all_conflicts: List[dict] = []
    all_passes: List[dict] = []
    logs: List[dict] = [{"step": "init", "docs_count": len(docs), "checks": checks}]

    sources_checked = [d.get("source_file", f"doc_{i}") for i, d in enumerate(docs)]

    # Chạy checks pairwise cho tài liệu
    for i in range(len(docs)):
        for j in range(i+1, len(docs)):
            a, b = docs[i], docs[j]

            if "C01" in checks:
                c, p = check_load_mismatch(a, b, threshold_pct, logs)
                all_conflicts += c; all_passes += p

            if "C02" in checks:
                c, p = check_section_mismatch(a, b, logs)
                all_conflicts += c; all_passes += p

            if "C03" in checks:
                c, p = check_material_mismatch(a, b, logs)
                all_conflicts += c; all_passes += p

            if "C04" in checks:
                geo = a if a.get("engineering_data", {}).get("soil_params") else b
                des = b if geo is a else a
                c, p = check_geotech_mismatch(geo, des, logs)
                all_conflicts += c; all_passes += p

            if "C09" in checks:
                c, p = check_pile_capacity_match(a, b, logs)
                all_conflicts += c; all_passes += p

    # Checks chạy trên từng doc riêng lẻ
    for d in docs:
        if "C05" in checks:
            c, p = check_tcvn_violations(d, logs)
            all_conflicts += c; all_passes += p

        if "C07" in checks:
            c, p = check_anchorage_lap(d, logs)
            all_conflicts += c; all_passes += p

        if "C08" in checks:
            c, p = check_rebar_spacing_and_ratio(d, logs)
            all_conflicts += c; all_passes += p

    # Tổng kết severity
    summary = {"total": len(all_conflicts), "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for cf in all_conflicts:
        sv = cf.get("severity", "LOW")
        if sv in summary:
            summary[sv] += 1

    # Sort by severity
    all_conflicts.sort(key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 9))

    # Overall assessment
    if summary["CRITICAL"] > 0:
        overall = "❌ KHÔNG ĐẠT — Có xung đột NGHIÊM TRỌNG cần xử lý ngay"
    elif summary["HIGH"] > 0:
        overall = "⚠️ CẦN XEM XÉT — Có xung đột mức HIGH"
    elif summary["MEDIUM"] > 0:
        overall = "🟡 CẦN KIỂM TRA — Có cảnh báo mức MEDIUM"
    else:
        overall = "✅ ĐẠT — Không phát hiện xung đột đáng kể"

    return {
        "checked_at": datetime.now().isoformat(),
        "sources_checked": sources_checked,
        "threshold_pct": threshold_pct,
        "overall_assessment": overall,
        "conflict_summary": summary,
        "conflicts": all_conflicts,
        "passes": all_passes,
        "Calculation_Logs": logs,
        "Standard_Method": "conflict_analyzer v1.0 Sprint-4",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo_docs():
    """2 tài liệu mẫu để test conflict detection."""
    doc_pdf = {
        "source_file": "DEMO_ThuyetMinh.pdf",
        "source_type": "PDF",
        "raw_text_preview": "η = 1.05 dầm D1 → không đạt\nTĩnh tải sàn: 3.5 kN/m²\nDầm D1: 300x600\nBê tông B30",
        "engineering_data": {
            "loads": [
                {"label": "Tĩnh tải sàn", "value": 3.5, "unit": "kN/m²"},
                {"label": "Hoạt tải sàn", "value": 5.0, "unit": "kN/m²"},
            ],
            "sections": [
                {"element": "Dầm D1", "b_mm": 300, "h_mm": 600},
                {"element": "Cột C1", "b_mm": 400, "h_mm": 400},
            ],
            "materials": [
                {"type": "concrete", "grade": "B30", "fck_MPa": 25},
                {"type": "steel_rebar", "grade": "CB400V", "fy_MPa": 400},
            ],
            "soil_params": [],
            "rebar_schedule": [],
        },
    }
    doc_etabs = {
        "source_file": "DEMO_ETABS_Model",
        "source_type": "ETABS",
        "raw_text_preview": "",
        "engineering_data": {
            "loads": [
                {"label": "Tĩnh tải sàn", "value": 4.5, "unit": "kN/m²"},  # C01: chênh 28.6%!
                {"label": "Hoạt tải sàn", "value": 5.0, "unit": "kN/m²"},
            ],
            "sections": [
                {"element": "Dầm D1", "b_mm": 250, "h_mm": 600},  # C02: b khác!
                {"element": "Cột C1", "b_mm": 400, "h_mm": 400},
            ],
            "materials": [
                {"type": "concrete", "grade": "B25", "fck_MPa": 20},  # C03: grade khác!
                {"type": "steel_rebar", "grade": "CB400V", "fy_MPa": 400},
            ],
            "soil_params": [],
            "rebar_schedule": [],
        },
    }
    return [doc_pdf, doc_etabs]


# ─────────────────────────────────────────────────────────────────────────────
# 9. CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="conflict_analyzer — Cross-Document Conflict Checker (Sprint 4)",
    )
    parser.add_argument("--a",        help="Tài liệu A (JSON từ doc_reader)")
    parser.add_argument("--b",        help="Tài liệu B (JSON từ doc_reader)")
    parser.add_argument("--docs",     nargs="+", help="Nhiều tài liệu (JSON paths)")
    parser.add_argument("--output",   help="Đường dẫn file JSON kết quả")
    parser.add_argument("--threshold",type=float, default=5.0, help="Ngưỡng %% load mismatch (mặc định 5.0)")
    parser.add_argument("--checks",   nargs="+", default=["C01","C02","C03","C04","C05"],
                        help="Subset check cần chạy: C01 C02 C03 C04 C05")
    parser.add_argument("--demo",     action="store_true", help="Chạy với dữ liệu mẫu")
    args = parser.parse_args()

    if args.demo:
        docs = _demo_docs()
    else:
        docs = []
        paths = []
        if args.a: paths.append(args.a)
        if args.b: paths.append(args.b)
        if args.docs: paths += args.docs
        if not paths:
            parser.print_help()
            return
        for p in paths:
            with open(p, encoding="utf-8") as f:
                docs.append(json.load(f))

    result = analyze_conflicts(docs, threshold_pct=args.threshold, checks=args.checks)
    out_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"✅ Kết quả: {args.output}")
    
    # In tóm tắt ra console
    s = result["conflict_summary"]
    print(f"\n{result['overall_assessment']}")
    print(f"  CRITICAL: {s['CRITICAL']} | HIGH: {s['HIGH']} | MEDIUM: {s['MEDIUM']} | PASS: {len(result['passes'])}")
    if not args.output:
        print(out_json)


if __name__ == "__main__":
    main()
