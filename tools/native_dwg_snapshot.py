# -*- coding: utf-8 -*-
"""
native_dwg_snapshot.py — Tầng 2B (solo) · Xương sống dữ liệu Snapshot Native DWG
==================================================================================

Mục đích (Tầng 2B của Chiến lược 3 Tầng v8.0):
    Chuẩn hóa thực thể CAD/DWG thành một **bản chụp (snapshot) chính tắc** bất biến
    đơn vị (mm), mang theo định danh nghiệp vụ 2A (`DCE_ELEMENT_ID`:
    element_id / role / floor_id). Đây là NGUỒN DỮ LIỆU DUY NHẤT mà engine so
    revision (native_dwg_diff.py) thao tác, nhờ đó MỘT thuật toán diff phục vụ:

      (a) bộ đọc ezdxf/DXF thuần (không cần AutoCAD),
      (b) cầu nối native accoreconsole DWG (cùng schema),
      (c) fixture dựng tay trong kiểm thử.

Nguyên tắc (AGENTS.md §4 — không tự nhẩm; mọi phép so là mã xác định):
    * Bản đồ định danh là `element_id` (nghiệp vụ bền); `handle` chỉ là tham chiếu
      vật lý theo revision, giữ cho truy nguồn, KHÔNG dùng làm khóa ghép.
    * Mọi đơn vị hình học quy về mm; góc giữ nguyên (độ).
    * Snapshot phải kiểm tra được toàn vẹn: schema + độ đầy đủ + loại bỏ trường
      biến động (handle, timestamp) trước khi tạo fingerprint SHA-256.

Không phụ thuộc AutoCAD để import hay chạy đường xác định (ezdxf là adapter).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ezdxf là adapter tùy chọn — không có nó vẫn dùng được đường inventory thuần.
try:
    import ezdxf  # type: ignore
    _HAVE_EZDXF = True
except ImportError:  # pragma: no cover - ezdxf luôn có trên máy trạm
    ezdxf = None  # type: ignore
    _HAVE_EZDXF = False

# ── Hằng số chuẩn hóa ──────────────────────────────────────────────────────────
SNAPSHOT_SCHEMA_VERSION = "1.0"
CANONICAL_UNITS = "mm"
MM_PER_M = 1000.0

# Vai trò 2A (đồng bộ với dce_xdata_bridge.ALLOWED_ELEMENT_ROLES).
ROLE_PRIMARY = "PRIMARY_GEOM"
ROLE_TAG = "ANNOTATION_TAG"
ROLE_DETAIL = "DETAIL_VIEW"
_KNOWN_ROLES = {ROLE_PRIMARY, ROLE_TAG, ROLE_DETAIL}

# Trường hình học (giá trị) phân loại: nào là ĐỘ DÀI (quy mm), nào là GÓC (giữ nguyên).
_LENGTH_KEYS = {
    "x_mm", "y_mm", "z_mm", "length_mm", "x0_mm", "y0_mm", "z0_mm",
    "x1_mm", "y1_mm", "z1_mm", "b_mm", "h_mm", "thickness_mm",
}
_ANGLE_KEYS = {"angle_deg"}

# Trường BIẾN ĐỘNG — phải gỡ trước khi tạo fingerprint để cùng revision cho cùng hash.
_VOLATILE_KEYS = {"handle", "generated_at", "snapshot_wall_ms"}

# Mã trạng thái đọc (đồng bộ với hợp đồng MCP): UNVERIFIED không được quy thành PASS.
SOURCE_UNITS_DEFAULT = "mm"


# ── 1. Chuẩn hóa đơn vị ───────────────────────────────────────────────────────

def _unit_scale(source_units: str) -> float:
    """Hệ số quy từ đơn vị nguồn về mm. Không biết đơn vị => giữ nguyên (giả định mm)."""
    u = (source_units or SOURCE_UNITS_DEFAULT).strip().lower()
    return {
        "mm": 1.0,
        "m": MM_PER_M,
        "cm": 10.0,
        "dm": 100.0,
        "km": 1000000.0,
        SOURCE_UNITS_DEFAULT: 1.0,
    }.get(u, 1.0)


def normalize_value(key: str, value: Any, source_units: str) -> Any:
    """Quy một trường về đơn vị chuẩn: độ dài về mm, góc giữ nguyên."""
    if value is None:
        return None
    scale = _unit_scale(source_units)
    if key in _LENGTH_KEYS:
        try:
            return round(float(value) * scale, 6)
        except (TypeError, ValueError):
            return value
    if key in _ANGLE_KEYS:
        try:
            return round(float(value), 6)
        except (TypeError, ValueError):
            return value
    return value


def normalize_geometry(geometry: Optional[Dict[str, Any]], source_units: str) -> Dict[str, Any]:
    """Chuẩn hóa từ dict hình học về mm/độ, bỏ None, sắp thứ tự để khớp fingerprint."""
    if not geometry:
        return {}
    out: Dict[str, Any] = {}
    for k in sorted(geometry.keys()):
        v = normalize_value(k, geometry[k], source_units)
        if v is not None:
            out[k] = v
    return out


# ── 2. Dựng snapshot chính tắc ────────────────────────────────────────────────

def build_snapshot_from_inventory(
    inventory: List[Dict[str, Any]],
    *,
    document_id: str,
    revision: str = "",
    source_units: str = SOURCE_UNITS_DEFAULT,
    provenance: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Dựng bản chụp chính tắc từ danh sách bản ghi (inventory).

    Mỗi bản ghi mong chờ (tùy chọn nếu thiếu):
        element_id  — định danh nghiệp vụ bền (None => chưa ghép, vào UNMATCHED)
        role        — PRIMARY_GEOM | ANNOTATION_TAG | DETAIL_VIEW
        floor_id    — phạm vi tầng
        handle      — tham chiếu vật lý (giữ cho truy nguồn, loại khỏi fingerprint)
        dxftype     — loại thực thể (LINE, INSERT, ...)
        layer       — tên layer
        mark        — nhãn hiển thị (VD "D1") — CHUYỂN NHÃN KHÔNG PHẢI khóa ghép
        geometry    — dict hình học (quy về mm)
        properties  — dict thuộc tính nghiệp vụ (section, b, h, mu, ...)
        xref        — None nếu gốc; dict {path, transform, resolved} nếu Xref
    """
    inv = list(inventory or [])
    records: List[Dict[str, Any]] = []
    for raw in inv:
        rec = _normalize_record(raw, source_units)
        records.append(rec)
    records.sort(key=lambda r: (
        r["element_id"] or "", r["role"], r["floor_id"], r["dxftype"], r["mark"] or ""
    ))
    xrefs = sorted({r["xref"] for r in records if r["xref"]})
    snapshot: Dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "document_id": document_id,
        "revision": revision,
        "units": CANONICAL_UNITS,
        "unit_scale_applied": _unit_scale(source_units),
        "source_units": source_units,
        "counts": {
            "total": len(records),
            "with_identity": sum(1 for r in records if r["element_id"]),
            "primary": sum(1 for r in records if r["role"] == ROLE_PRIMARY),
            "annotations": sum(1 for r in records if r["role"] in (ROLE_TAG, ROLE_DETAIL)),
            "unmatched": sum(1 for r in records if not r["element_id"]),
        },
        "records": records,
        "xrefs": xrefs,
        "provenance": provenance or {},
        "completion": {"complete": True, "errors": []},
    }
    snapshot["fingerprint"] = fingerprint_snapshot(snapshot)
    return snapshot


def _normalize_record(raw: Dict[str, Any], source_units: str) -> Dict[str, Any]:
    # Giữ nguyên role (chuẩn hóa in hoa) để validate_snapshot có thể bắt role lạ;
    # chỉ khi role RỖNG mới mặc định PRIMARY_GEOM. Không âm thầm ép role sai thành
    # PRIMARY (đó là lỗi nghiệp vụ, phải lộ ra ở cổng toàn vẹn).
    role = (str(raw.get("role")).strip().upper() if raw.get("role") else ROLE_PRIMARY)
    xref = raw.get("xref")
    if isinstance(xref, dict):
        xref = dict(xref)
    return {
        "element_id": (str(raw["element_id"]).strip() if raw.get("element_id") else None),
        "role": role,
        "floor_id": str(raw.get("floor_id") or "").strip(),
        "handle": str(raw.get("handle") or "").strip().upper(),
        "dxftype": str(raw.get("dxftype") or "").strip().upper(),
        "layer": str(raw.get("layer") or "").strip(),
        "mark": str(raw["mark"]).strip() if raw.get("mark") else None,
        "geometry": normalize_geometry(raw.get("geometry"), source_units),
        "properties": {k: v for k, v in (raw.get("properties") or {}).items() if v is not None},
        "xref": xref,
    }


def build_snapshot_from_dxf(
    dxf_path: str,
    *,
    document_id: str,
    revision: str = "",
    element_id_appid: str = "DCE_ELEMENT_ID",
    beam_appid: str = "DCE_BEAM",
    geometry_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Đọc file DXF bằng ezdxf và dựng snapshot chính tắc.

    Đọc `DCE_ELEMENT_ID` XData (2A: ID/ROLE/FLOOR) và `DCE_BEAM` (MARK/B/H —
    nghiệp vụ) trên từng thực thể modelspace; bắt lỗi nếu ezdxf chưa cài.
    """
    if not _HAVE_EZDXF:
        return build_snapshot_from_inventory([], document_id=document_id, revision=revision,
                                             provenance={"adapter": "ezdxf", "note": "ezdxf unavailable"})
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    inv: List[Dict[str, Any]] = []
    for ent in msp:
        inv.append(_ezdxf_entity_to_record(ent, element_id_appid, geometry_keys, beam_appid))
    return build_snapshot_from_inventory(
        inv, document_id=document_id, revision=revision,
        provenance={"adapter": "ezdxf", "file": str(dxf_path),
                    "autocad_version": doc.dxfversion},
    )


def _read_xdata_1000(ent: Any, appid: str) -> Dict[str, str]:
    """Đọc payload 'K=V;K=V' (code 1000) của một regapp XData; {} nếu không có."""
    out: Dict[str, str] = {}
    try:
        if hasattr(ent, "has_xdata") and ent.has_xdata(appid):
            for code, val in list(ent.get_xdata(appid)):
                if code == 1000:
                    for seg in str(val).split(";"):
                        if "=" in seg:
                            k, v = seg.split("=", 1)
                            out[k.strip().upper()] = v.strip()
    except Exception:
        pass
    return out


def _ezdxf_entity_to_record(
    ent: Any, element_id_appid: str, geometry_keys: Optional[List[str]],
    beam_appid: str = "DCE_BEAM",
) -> Dict[str, Any]:
    """Dịch một thực thể ezdxf thành bản ghi inventory (đọc XData 2A + DCE_BEAM)."""
    rec: Dict[str, Any] = {"dxftype": ent.dxftype() if hasattr(ent, "dxftype") else type(ent).__name__}
    try:
        if hasattr(ent, "dxf") and getattr(ent.dxf, "layer", None) is not None:
            rec["layer"] = ent.dxf.layer
        if hasattr(ent, "dxf") and getattr(ent.dxf, "handle", None):
            rec["handle"] = ent.dxf.handle
    except Exception:
        pass
    # XData định danh 2A (ID/ROLE/FLOOR) — khóa ghép bền.
    parts = _read_xdata_1000(ent, element_id_appid)
    if parts.get("ID"):
        rec["element_id"] = parts["ID"]
        rec["role"] = parts.get("ROLE") or ROLE_PRIMARY
        rec["floor_id"] = parts.get("FLOOR", "")
    # DCE_BEAM (MARK/B/H) — nghiệp vụ; CÙNG regapp mà native .NET cũng đọc.
    beam = _read_xdata_1000(ent, beam_appid)
    if beam.get("MARK"):
        rec["mark"] = beam["MARK"]
        props: Dict[str, Any] = {}
        if beam.get("B"):
            try:
                props["b_mm"] = round(float(beam["B"]), 3)
            except ValueError:
                pass
        if beam.get("H"):
            try:
                props["h_mm"] = round(float(beam["H"]), 3)
            except ValueError:
                pass
        if props:
            rec["properties"] = props
    # Hình học tối thiểu (đơn vị bản vẽ = mm trong bộ CAD DCE).
    # `geometry_keys` (nếu có) giới hạn tập attribute lấy hình học; mặc định tập DCE.
    attrs = tuple(geometry_keys) if geometry_keys else ("insert", "start", "end", "center")
    geo: Dict[str, Any] = {}
    for attr in attrs:
        try:
            if hasattr(ent, "dxf") and getattr(ent.dxf, attr, None) is not None:
                p = getattr(ent.dxf, attr)
                geo[attr + "_mm"] = [round(float(p.x), 3), round(float(p.y), 3), round(float(p.z), 3)]
        except Exception:
            pass
    if geo:
        rec["geometry"] = geo
    # Thuộc tính INSERT (mark/tag)
    if rec.get("dxftype") == "INSERT" and hasattr(ent, "get_block"):
        try:
            bname = ent.dxf.name
            rec.setdefault("properties", {})["block_name"] = bname
            for attr in ent.block_attributes:
                rec.setdefault("properties", {})["attr_" + (attr.dxf.tag or "?")] = attr.dxf.text
                if (attr.dxf.tag or "").upper() in ("MARK", "TAG"):
                    rec["mark"] = attr.dxf.text
        except Exception:
            pass
    return rec


# ── 3. Toàn vẹn snapshot ──────────────────────────────────────────────────────

def validate_snapshot(snapshot: Dict[str, Any]) -> List[str]:
    """Trả về danh sách lỗi toàn vẹn (trống = hợp lệ)."""
    issues: List[str] = []
    if not snapshot:
        return ["snapshot is empty/None"]
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        issues.append(f"schema_version mismatch: {snapshot.get('schema_version')}")
    recs = snapshot.get("records")
    if not isinstance(recs, list):
        issues.append("records missing or not a list")
        return issues
    for i, r in enumerate(recs):
        role = r.get("role")
        if role not in _KNOWN_ROLES:
            issues.append(f"record[{i}]: unknown role {role!r}")
        if role == ROLE_PRIMARY and not r.get("element_id"):
            issues.append(f"record[{i}]: PRIMARY_GEOM without element_id (unmatched)")
    if snapshot.get("fingerprint") and _stable_fingerprint(snapshot) != snapshot.get("fingerprint"):
        issues.append("fingerprint mismatch with stored value (volatile fields present?)")
    return issues


def fingerprint_snapshot(snapshot: Dict[str, Any]) -> str:
    """SHA-256 ổn định của nội dung nghiệp vụ (loại bỏ trường biến động)."""
    return _stable_fingerprint(snapshot)


def _stable_fingerprint(snapshot: Dict[str, Any]) -> str:
    body = dict(snapshot)
    body.pop("fingerprint", None)
    clean_records = []
    for r in body.get("records", []):
        rr = {k: v for k, v in r.items() if k not in _VOLATILE_KEYS}
        clean_records.append(rr)
    body["records"] = clean_records
    blob = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── 4. Tiện ích kiểm thử / fixture ───────────────────────────────────────────

def load_snapshot(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_snapshot(snapshot: Dict[str, Any], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "SNAPSHOT_SCHEMA_VERSION", "CANONICAL_UNITS", "ROLE_PRIMARY", "ROLE_TAG", "ROLE_DETAIL",
    "normalize_value", "normalize_geometry", "build_snapshot_from_inventory",
    "build_snapshot_from_dxf", "validate_snapshot", "fingerprint_snapshot",
    "load_snapshot", "dump_snapshot",
]
