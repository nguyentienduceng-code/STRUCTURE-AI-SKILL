# -*- coding: utf-8 -*-
"""
native_dwg_diff.py — Tầng 2B (solo) · Engine So Revision Snapshot Native DWG (D1/D1A)
=====================================================================================

So hai bản chụp chính tắc (native_dwg_snapshot) A (cơ sở) và B (ứng viên) theo
KHÓA ĐỊNH DANH NGHIỆP VỤ BỀN `element_id` (+ vai trò + tầng). Nguyên tắc cốt lõi
(đóng khung cho cả bài thi D1/D1A):

    * CHỈ ghép theo element_id đã được xác nhận. Không bao giờ tự ghép theo
      mark hay hình học — mark chỉ là NHÃN, và hai cấu kiện hợp lệ có thể cùng
      một mark (VD 2 dầm D1). Ghép nhầm => lỗi âm tính.
    * Mọi thay đổi phải truy về một mã quyết định rõ ràng (Decision Class), có
      đơn vị, ngưỡng và bằng chứng cả hai phía. Kết quả "PASS" chỉ khi không có
      thay đổi ngoài phạm vi được duyệt.

Decision Classes:
    ADDED / REMOVED                 : có trong B (A) mà không (B) A
    PROPERTY_CHANGED                 : cùng element_id, thuộc tính nghiệp vụ đổi
    GEOMETRY_CHANGED                 : cùng element_id, hình học sai > ngưỡng
    MARK_CHANGED                     : cùng element_id, nhãn đổi (D1 -> D1A) —
                                        ĐÓI NHÃN KHÔNG PHẢI định danh mới
    DUPLICATE_PRIMARY                : 1 element_id+tầng có >=2 handle PRIMARY
                                        (hệ quả COPY/WBLOCK) -> chờ người duyệt
    TAG_RELINKED                     : tag/chi tiết trỏ sai element
    UNMATCHED                        : PRIMARY thiếu element_id
    UNVERIFIED                       : Xref/thiếu transform không phân giải được
    CANDIDATE_MARK                   : nhiều cấu kiện cùng mark (đề xuất ghép,
                                        không tự chấp nhận)

Mọi ngưỡng (tolerance) có phiên bản, hiện trên báo cáo, không hardcode dùng chung
cho tọa độ/góc/kích thước/khối lượng (theo kiến trúc 2B).
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Ngưỡng chuẩn hóa mặc định (mm/độ) — có phiên bản, ghi trên report.
DEFAULT_TOLERANCES: Dict[str, Any] = {
    "version": "1.0",
    "length_mm": 0.5,       # sai số chấp nhận cho tọa độ/kích thước (mm)
    "angle_deg": 0.05,      # sai số chấp nhận cho góc (độ)
    "property_exact": True, # thuộc tính nghiệp vụ phải khớp đúng (không dung sai)
}

# Các key hình học là GÓC (so theo ngưỡng góc), còn lại là ĐỘ DÀI.
_ANGLE_KEYS = {"angle_deg"}

# Mã quyết định.
DC = {
    "ADDED": "ADDED",
    "REMOVED": "REMOVED",
    "PROPERTY_CHANGED": "PROPERTY_CHANGED",
    "GEOMETRY_CHANGED": "GEOMETRY_CHANGED",
    "MARK_CHANGED": "MARK_CHANGED",
    "DUPLICATE_PRIMARY": "DUPLICATE_PRIMARY",
    "TAG_RELINKED": "TAG_RELINKED",
    "UNMATCHED": "UNMATCHED",
    "UNVERIFIED": "UNVERIFIED",
    "CANDIDATE_MARK": "CANDIDATE_MARK",
}


def _key_of(rec: Dict[str, Any]) -> str:
    """Khóa ghép: element_id (nghiệp vụ). Không dùng mark/handle/hình học."""
    return rec.get("element_id") or ""


def _geometry_delta(a: Dict[str, Any], b: Dict[str, Any],
                    tol: Dict[str, Any]) -> Dict[str, Any]:
    """So hình học đã chuẩn hóa về mm/độ, trả về dict {key: {a, b, delta, exceeded}}."""
    union = set(a) | set(b)
    out: Dict[str, Any] = {}
    for k in sorted(union):
        va = a.get(k)
        vb = b.get(k)
        if va is None and vb is None:
            continue
        limit = tol["angle_deg"] if k in _ANGLE_KEYS else tol["length_mm"]
        delta = _scalar_delta(va, vb)
        exceeded = delta is not None and abs(delta) > limit
        out[k] = {"a": va, "b": vb, "delta": delta, "exceeded": exceeded,
                  "tolerance": limit, "unit": "deg" if k in _ANGLE_KEYS else "mm"}
    return out


def _scalar_delta(va: Any, vb: Any) -> Optional[float]:
    """Hiệu (b - a) trên scalar hoặc danh sách tọa độ (L2). None nếu không so được."""
    if va is None:
        return None if vb is None else float("nan")
    if vb is None:
        return float("nan")
    if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
        return float(vb) - float(va)
    if isinstance(va, (list, tuple)) and isinstance(vb, (list, tuple)) \
            and len(va) == len(vb):
        import math
        sq = 0.0
        for x, y in zip(va, vb):
            try:
                sq += (float(y) - float(x)) ** 2
            except (TypeError, ValueError):
                return None
        return math.sqrt(sq)
    return None


def _property_delta(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            out[k] = {"a": a.get(k), "b": b.get(k)}
    return out


def diff_snapshots(a: Dict[str, Any], b: Dict[str, Any],
                   tolerances: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """So snapshot B (ứng viên) với A (cơ sở). Hoàn toàn xác định, không sinh ngẫu nhiên."""
    tol = {**DEFAULT_TOLERANCES, **(tolerances or {})}

    def primaries(snap: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in snap.get("records", []):
            if r.get("role") == "PRIMARY_GEOM":
                groups.setdefault(_key_of(r), []).append(r)
        return groups

    pa, pb = primaries(a), primaries(b)
    common = sorted(set(pa) & set(pb))
    added_ids = sorted(set(pb) - set(pa))
    removed_ids = sorted(set(pa) - set(pb))

    # Cấu trúc báo cáo
    changes: Dict[str, Dict[str, Any]] = {}
    for eid in common:
        ra, rb = pa[eid][0], pb[eid][0]
        entry: Dict[str, Any] = {
            "element_id": eid,
            "floor_id": rb.get("floor_id") or ra.get("floor_id", ""),
            "classes": [],
        }
        gdel = _geometry_delta(ra.get("geometry") or {}, rb.get("geometry") or {}, tol)
        if any(v["exceeded"] for v in gdel.values()):
            entry["classes"].append(DC["GEOMETRY_CHANGED"])
            entry["geometry_delta"] = {k: v for k, v in gdel.items() if v["exceeded"]}
        pdel = _property_delta(ra.get("properties") or {}, rb.get("properties") or {})
        if pdel:
            entry["classes"].append(DC["PROPERTY_CHANGED"])
            entry["property_delta"] = pdel
        if ra.get("mark") != rb.get("mark"):
            entry["classes"].append(DC["MARK_CHANGED"])
            entry["mark"] = {"from": ra.get("mark"), "to": rb.get("mark"),
                             "note": "Đổi nhãn (mark) — KHÔNG phải định danh mới."}
        # Xref chưa phân giải -> UNVERIFIED
        for src in (ra.get("xref"), rb.get("xref")):
            if isinstance(src, dict) and not src.get("resolved", True):
                if DC["UNVERIFIED"] not in entry["classes"]:
                    entry["classes"].append(DC["UNVERIFIED"])
                break
        if entry["classes"]:
            changes[eid] = entry

    report: Dict[str, Any] = {
        "tolerances": tol,
        "document": {"a": a.get("document_id"), "b": b.get("document_id"),
                     "revision_a": a.get("revision"), "revision_b": b.get("revision")},
        "summary": {
            "matched": len(common),
            "added": len(added_ids),
            "removed": len(removed_ids),
            "changed": len(changes),
        },
        "added": _brief(pb, added_ids),
        "removed": _brief(pa, removed_ids),
        "changes": changes,
        "issues": {
            "DUPLICATE_PRIMARY": _dup_primaries(pa, pb),
            "UNMATCHED": _unmatched(a, b),
            "UNVERIFIED": sorted({eid for eid, e in changes.items()
                                  if DC["UNVERIFIED"] in e["classes"]}),
            "CANDIDATE_MARK": _candidate_marks(pa, pb),
        },
    }
    # Trạng thái tổng: CLEAN chỉ khi không có thay đổi nào (không gồm added/removed/changed
    # cũng như mọi issue trừ CANDIDATE/UNMATCHED được chấp nhận). Giữ nghiêm.
    has_change = bool(changes) or bool(added_ids) or bool(removed_ids)
    has_issue = (report["issues"]["DUPLICATE_PRIMARY"] or report["issues"]["UNMATCHED"]
                 or report["issues"]["UNVERIFIED"])
    report["overall"] = "CLEAN" if not (has_change or has_issue) else "DIFFERENCES"
    report["clean"] = not has_change and not has_issue
    return report


def _brief(groups: Dict[str, List[Dict[str, Any]]], ids: List[str]) -> List[Dict[str, Any]]:
    out = []
    for eid in ids:
        r = groups[eid][0]
        out.append({"element_id": eid, "mark": r.get("mark"), "floor_id": r.get("floor_id", ""),
                    "dxftype": r.get("dxftype")})
    return out


def _dup_primaries(pa: Dict[str, Any], pb: Dict[str, Any]) -> Dict[str, List[Any]]:
    """Các element_id (KHÁC RỖNG) có >=2 PRIMARY trong cùng một snapshot.

    Record CHƯA CÓ element_id (vô danh, chưa ghép — thuộc UNMATCHED) được nhóm
    vào key rỗng `""`; đó KHÔNG phải DUPLICATE_PRIMARY (duplicate chỉ có nghĩa
    khi CÙNG MỘT element_id đã xác nhận bị >=2 handle sở hữu, ví dụ hậu quả
    COPY/WBLOCK). Lọc bỏ nhóm key rỗng để khỏi dương tính giả trên mọi bản vẽ
    có khung/trắc/dim (luôn nhiều PRIMARY vô danh)."""
    dups: Dict[str, List[Any]] = {}
    for groups in (pa, pb):
        for eid, grp in groups.items():
            if not eid:
                continue
            if len(grp) >= 2:
                dups[eid] = [r.get("handle") for r in grp]
    return dups


def _unmatched(a: Dict[str, Any], b: Dict[str, Any]) -> List[Dict[str, Any]]:
    """PRIMARY không có element_id — không thể ghép, liệt kê rõ."""
    out: List[Dict[str, Any]] = []
    for snap, tag in ((a, "A"), (b, "B")):
        for r in snap.get("records", []):
            if r.get("role") == "PRIMARY_GEOM" and not r.get("element_id"):
                out.append({"side": tag, "handle": r.get("handle"),
                            "mark": r.get("mark"), "floor_id": r.get("floor_id", "")})
    return out


def _candidate_marks(pa: Dict[str, Any], pb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Nhiều cấu kiện cùng mark (VD 2 dầm D1) — ĐỀ XUẤT ghép, không tự chấp nhận."""
    mark_map: Dict[str, List[str]] = {}
    for groups in (pa, pb):
        for eid, grp in groups.items():
            for r in grp:
                m = r.get("mark")
                if m:
                    mark_map.setdefault(m, [])
                    if eid not in mark_map[m]:
                        mark_map[m].append(eid)
    return [{"mark": m, "element_ids": sorted(set(ids))}
            for m, ids in sorted(mark_map.items()) if len(set(ids)) >= 2]


# ── Bộ ca quyết định D1/D1A (trợ lý kiểm thử / trình diễn) ──────────────────

def d1d1a_decision(report: Dict[str, Any]) -> Dict[str, Any]:
    """Rút gọn report về các câu trả lời bài thi D1/D1A:

    Với 2 dầm cùng mark D1 (nhịp A–B: id1; nhịp B–C: id2, được duyệt đổi 250×500
    -> 250×600 và đổi nhãn D1A), kết quả PHẢI:
      * id2  : PROPERTY_CHANGED (tiết diện) + MARK_CHANGED (D1->D1A) — ĐÚNG như duyệt
      * id1  : nếu type dùng chung làm cả id1 thành 600 => id1 cũng PROPERTY_CHANGED
                (lỗi SAI, phải chỉ ra dầm A–B sai 100mm)
      * Không cấu kiện ngoài phạm vi bị cập nhật (không có ADDED/REMOVED ngoài dự kiến).
    """
    ch = report.get("changes", {})
    verdict: Dict[str, Any] = {"by_element": {}, "out_of_scope_changed": [],
                               "duplicate_primary": report["issues"]["DUPLICATE_PRIMARY"]}
    for eid, entry in ch.items():
        classes = entry.get("classes", [])
        pdelta = entry.get("property_delta", {})
        h = pdelta.get("h_mm", {})
        verdict["by_element"][eid] = {
            "classes": classes,
            "mark": entry.get("mark"),
            "h_mm": h,
            "in_scope_if_only_expected": _expected_change_ok(classes, pdelta),
        }
    # "outside scope" = cấu kiện đổi thuộc tính NHƯNG không đổi nhãn D1A
    # (lỗi type dùng chung: dầm A–B thành 600 mà vẫn mark D1). Cấu kiện đã
    # kèm MARK_CHANGED được coi là thay đổi trong phạm vi duyệt.
    for eid, entry in ch.items():
        classes = entry.get("classes", [])
        if DC["PROPERTY_CHANGED"] in classes and DC["MARK_CHANGED"] not in classes:
            verdict["out_of_scope_changed"].append(
                {"element_id": eid, "note": "đổi thuộc tính không kèm đổi nhãn D1A — kiểm tra scope/type dùng chung"})
    verdict["clean"] = bool(report.get("clean"))
    return verdict


def _expected_change_ok(classes: List[str], pdelta: Dict[str, Any]) -> bool:
    """Một thay đổi được coi là 'trong phạm vi duyệt' nếu kèm đổi nhãn (MARK_CHANGED)
    hoặc chỉ là thêm/xóa. Chốt cuối thuộc về người chủ trì, không phải engine."""
    return ("MARK_CHANGED" in classes) or (not pdelta and "PROPERTY_CHANGED" in classes)


__all__ = [
    "DEFAULT_TOLERANCES", "DC", "diff_snapshots", "d1d1a_decision",
    "DUPLICATE_PRIMARY",
]
# Tiện truy cập hằng cho test.
DUPLICATE_PRIMARY = DC["DUPLICATE_PRIMARY"]
