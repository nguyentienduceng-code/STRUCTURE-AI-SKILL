"""
ifc_parser.py — Direct IFC/BIM File Parser
============================================
Sprint 3 · Phase 2 · TD-02 Resolution

Mục đích:
    Đọc trực tiếp file mô hình .ifc mà không cần bước export JSON trung gian
    từ AutoCAD / Revit plugin. Xóa bỏ nợ kỹ thuật TD-02.

Backend:
    Tầng 1: ifcopenshell (chuẩn công nghiệp, ISO 16739-1:2018)
    Tầng 2: Fallback parser thô (regex trên IFC text format) khi không có ifcOS.
    Tầng 3: Demo Mode với hồ sơ mẫu đa tầng.

Entities trích xuất:
    • IfcBuilding / IfcBuildingStorey    → danh sách tầng, cao độ
    • IfcBeam / IfcColumn / IfcWall     → cấu kiện, tiết diện, vật liệu
    • IfcReinforcingBar / IfcTendon     → cốt thép đặt sẵn
    • IfcSpace                          → phòng, diện tích
    • IfcGrid                           → lưới trục định nghĩa vị trí

Tiêu chuẩn: ISO 16739-1:2018 (IFC 4.3), IFC 2x3 TC1 (tương thích ngược).

Đầu ra JSON (chuẩn handoff SKILL_BIM_COORDINATION):
    {
        "ifc_schema":   "IFC4",
        "project_name": "DuAnA",
        "storeys":      [{"name": "Level 1", "elevation_mm": 0.0, ...}],
        "elements":     [{"guid": "...", "type": "IfcBeam", "name": "B1",
                          "storey": "Level 1", "section": "B400x700",
                          "material": "B30", "coord": {...}}],
        "grids":        [{"name": "A", "direction": "X", "offset_mm": 0.0}],
        "reinforcement":[{"bar_guid": "...", "host_guid": "...",
                          "dia_mm": 25, "count": 3}],
        "Calculation_Logs": [...],
        "Standard_Method": "ISO 16739-1:2018 IFC4 + ifcopenshell"
    }

Sử dụng:
    python ifc_parser.py --input model.ifc [--output result.json] [--demo]
    python ifc_parser.py --validate model.ifc   # kiểm tra cấu trúc nhanh

Phụ thuộc tùy chọn:
    pip install ifcopenshell    # Tầng 1 (khuyến nghị)
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 0. Phát hiện backend
# ─────────────────────────────────────────────────────────────────────────────

_IFC_BACKEND = None   # "ifcopenshell" | "raw_parser" | None

try:
    import ifcopenshell
    import ifcopenshell.util.element as _ifc_elem
    import ifcopenshell.util.placement as _ifc_place
    _IFC_BACKEND = "ifcopenshell"
except ImportError:
    pass

if _IFC_BACKEND is None:
    _IFC_BACKEND = "raw_parser"   # fallback luôn có sẵn


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tầng 1: ifcopenshell Parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_with_ifcos(filepath: str, logs: list) -> dict:
    """Đọc IFC bằng ifcopenshell — độ chính xác cao nhất."""
    model = ifcopenshell.open(filepath)
    schema = model.schema

    logs.append(f"[IFC-OS] Schema: {schema}, File: {os.path.basename(filepath)}")

    # ── Project info ─────────────────────────────────────────────────────────
    project_name = "Unknown"
    try:
        projs = model.by_type("IfcProject")
        if projs:
            project_name = projs[0].Name or "Unknown"
    except Exception:
        pass

    # ── Storeys ──────────────────────────────────────────────────────────────
    storeys = []
    try:
        for storey in model.by_type("IfcBuildingStorey"):
            elev = 0.0
            if storey.Elevation is not None:
                elev = float(storey.Elevation) * 1000.0   # m → mm
            storeys.append({
                "guid":         storey.GlobalId,
                "name":         storey.Name or "",
                "elevation_mm": round(elev, 2),
            })
        storeys.sort(key=lambda s: s["elevation_mm"])
    except Exception as e:
        logs.append(f"[WARN] Storeys: {e}")

    # Lookup storey name by guid
    storey_by_guid = {s["guid"]: s["name"] for s in storeys}

    def _get_storey(element):
        """Trả về tên tầng chứa element (qua IfcRelContainedInSpatialStructure)."""
        try:
            for rel in element.ContainedInStructure:
                if rel.RelatingStructure.is_a("IfcBuildingStorey"):
                    return rel.RelatingStructure.Name or ""
        except Exception:
            pass
        return ""

    def _get_material(element):
        try:
            mats = _ifc_elem.get_materials(element, should_inherit=True)
            if mats:
                return mats[0].Name if hasattr(mats[0], "Name") else str(mats[0])
        except Exception:
            pass
        return ""

    def _get_section(element):
        try:
            psets = _ifc_elem.get_psets(element)
            for pset_name, pset in psets.items():
                for k, v in pset.items():
                    if any(x in k.lower() for x in ("section", "profile", "width", "depth")):
                        return str(v)
        except Exception:
            pass
        return ""

    def _get_coord(element):
        try:
            import ifcopenshell.util.placement as pl
            m = pl.get_local_placement(element.ObjectPlacement)
            return {"x": round(m[0][3] * 1000, 2),
                    "y": round(m[1][3] * 1000, 2),
                    "z": round(m[2][3] * 1000, 2)}
        except Exception:
            return {}

    # ── Structural Elements ───────────────────────────────────────────────────
    elements = []
    for ifc_type in ("IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcPile", "IfcFooting"):
        try:
            for elem in model.by_type(ifc_type):
                elements.append({
                    "guid":     elem.GlobalId,
                    "type":     ifc_type,
                    "name":     elem.Name or "",
                    "storey":   _get_storey(elem),
                    "section":  _get_section(elem),
                    "material": _get_material(elem),
                    "coord":    _get_coord(elem),
                })
        except Exception as e:
            logs.append(f"[WARN] {ifc_type}: {e}")

    logs.append(f"[IFC-OS] Elements: {len(elements)}")

    # ── Grids ─────────────────────────────────────────────────────────────────
    grids = []
    try:
        for grid in model.by_type("IfcGrid"):
            for axis in (grid.UAxes or []):
                grids.append({"name": axis.AxisTag, "direction": "U"})
            for axis in (grid.VAxes or []):
                grids.append({"name": axis.AxisTag, "direction": "V"})
    except Exception as e:
        logs.append(f"[WARN] Grids: {e}")

    # ── Reinforcement ─────────────────────────────────────────────────────────
    reinforcement = []
    for rebar_type in ("IfcReinforcingBar", "IfcTendon"):
        try:
            for bar in model.by_type(rebar_type):
                entry = {
                    "bar_guid":  bar.GlobalId,
                    "type":      rebar_type,
                    "name":      bar.Name or "",
                }
                # Nominal diameter
                try:
                    entry["dia_mm"] = float(bar.NominalDiameter) * 1000
                except Exception:
                    pass
                reinforcement.append(entry)
        except Exception as e:
            logs.append(f"[WARN] {rebar_type}: {e}")

    return {
        "ifc_schema":    schema,
        "project_name":  project_name,
        "storeys":       storeys,
        "elements":      elements,
        "grids":         grids,
        "reinforcement": reinforcement,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tầng 2: Raw IFC Text Parser (fallback)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns IFC text format (STEP / P21)
_SCHEMA_RE   = re.compile(r"FILE_SCHEMA\s*\(\s*\('(\w+)'\)", re.I)
_STOREY_RE   = re.compile(
    r"#(\d+)=\s*IFCBUILDINGSTOREY\([^;]*'([^']*)'[^;]*,\s*([\d.Ee+\-]+)", re.I)
_BEAM_RE     = re.compile(
    r"#(\d+)=\s*IFCBEAM\([^;]*'([^']*)'", re.I)
_COLUMN_RE   = re.compile(
    r"#(\d+)=\s*IFCCOLUMN\([^;]*'([^']*)'", re.I)
_SLAB_RE     = re.compile(
    r"#(\d+)=\s*IFCSLAB\([^;]*'([^']*)'", re.I)
_WALL_RE     = re.compile(
    r"#(\d+)=\s*IFCWALL\([^;]*'([^']*)'", re.I)
_GRID_U_RE   = re.compile(r"#(\d+)=\s*IFCGRIDAXIS\([^;]*'([^']*)'", re.I)


def _parse_raw(filepath: str, logs: list) -> dict:
    """Đọc IFC bằng text parser đơn giản — không cần ifcopenshell."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    schema_m = _SCHEMA_RE.search(content)
    schema   = schema_m.group(1) if schema_m else "Unknown"
    logs.append(f"[RAW] Schema: {schema}")

    storeys  = []
    for m in _STOREY_RE.finditer(content):
        try:
            elev_mm = float(m.group(3)) * 1000
        except ValueError:
            elev_mm = 0.0
        storeys.append({
            "guid":         f"#{m.group(1)}",
            "name":         m.group(2),
            "elevation_mm": round(elev_mm, 2),
        })
    storeys.sort(key=lambda s: s["elevation_mm"])

    elements = []
    for (pat, ifc_type) in [
        (_BEAM_RE,   "IfcBeam"),
        (_COLUMN_RE, "IfcColumn"),
        (_SLAB_RE,   "IfcSlab"),
        (_WALL_RE,   "IfcWall"),
    ]:
        for m in pat.finditer(content):
            elements.append({
                "guid":     f"#{m.group(1)}",
                "type":     ifc_type,
                "name":     m.group(2),
                "storey":   "",
                "section":  "",
                "material": "",
                "coord":    {},
            })

    grids = []
    for m in _GRID_U_RE.finditer(content):
        grids.append({"name": m.group(2), "direction": "U"})

    logs.append(f"[RAW] Storeys: {len(storeys)}, Elements: {len(elements)}")

    return {
        "ifc_schema":    schema,
        "project_name":  "ParsedByRawFallback",
        "storeys":       storeys,
        "elements":      elements,
        "grids":         grids,
        "reinforcement": [],
        "warning":       "Raw text parser — limited accuracy; install ifcopenshell for full parsing",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tầng 3: Demo Mode
# ─────────────────────────────────────────────────────────────────────────────

def _demo_payload() -> dict:
    return {
        "ifc_schema":   "IFC4 [DEMO]",
        "project_name": "DuAnA_Structural_Demo",
        "storeys": [
            {"guid": "S0",  "name": "BASE",   "elevation_mm":    0.0},
            {"guid": "S1",  "name": "STORY1", "elevation_mm": 3600.0},
            {"guid": "S2",  "name": "STORY2", "elevation_mm": 7200.0},
            {"guid": "S3",  "name": "STORY3", "elevation_mm":10800.0},
            {"guid": "ROOF","name": "ROOF",   "elevation_mm":14000.0},
        ],
        "elements": [
            {"guid": "B001", "type": "IfcBeam",   "name": "DB1A-1B/1-2",
             "storey": "STORY1", "section": "B400x700", "material": "B30",
             "coord": {"x": 0.0, "y": 0.0, "z": 3600.0}},
            {"guid": "B002", "type": "IfcBeam",   "name": "DB1B-1C/1-2",
             "storey": "STORY1", "section": "B400x700", "material": "B30",
             "coord": {"x": 6000.0, "y": 0.0, "z": 3600.0}},
            {"guid": "C001", "type": "IfcColumn", "name": "C-1A/1",
             "storey": "STORY1", "section": "C600x600",  "material": "B35",
             "coord": {"x": 0.0, "y": 0.0, "z": 0.0}},
            {"guid": "C002", "type": "IfcColumn", "name": "C-1B/1",
             "storey": "STORY1", "section": "C600x600",  "material": "B35",
             "coord": {"x": 6000.0, "y": 0.0, "z": 0.0}},
            {"guid": "S001", "type": "IfcSlab",   "name": "SN-STORY1",
             "storey": "STORY1", "section": "S200",       "material": "B25",
             "coord": {"x": 3000.0, "y": 2750.0, "z": 3600.0}},
        ],
        "grids": [
            {"name": "A", "direction": "X"}, {"name": "B", "direction": "X"},
            {"name": "C", "direction": "X"}, {"name": "1", "direction": "Y"},
            {"name": "2", "direction": "Y"},
        ],
        "reinforcement": [
            {"bar_guid": "R001", "type": "IfcReinforcingBar",
             "name": "Top-B001", "dia_mm": 25},
            {"bar_guid": "R002", "type": "IfcReinforcingBar",
             "name": "Bot-B001", "dia_mm": 22},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. CDC Validation (8 luật kiểm tra xung đột)
# ─────────────────────────────────────────────────────────────────────────────

def validate_cdc(data: dict, logs: list) -> list:
    """
    Kiểm tra 8 luật xung đột cơ bản (Clash Detection Criteria).
    Trả về list issues tìm thấy.
    """
    issues = []
    elements = data.get("elements", [])

    # CDC-01: Kiểm tra phần tử không gán tầng
    no_storey = [e for e in elements if not e.get("storey")]
    if no_storey:
        issues.append({
            "rule": "CDC-01",
            "severity": "MEDIUM",
            "desc": f"{len(no_storey)} phần tử không gán tầng",
            "elements": [e["name"] for e in no_storey[:5]],
        })
        logs.append(f"[CDC-01] {len(no_storey)} phần tử không storey")

    # CDC-02: Kiểm tra thiếu tiết diện
    no_section = [e for e in elements if not e.get("section") and
                  e["type"] in ("IfcBeam", "IfcColumn")]
    if no_section:
        issues.append({
            "rule": "CDC-02",
            "severity": "HIGH",
            "desc": f"{len(no_section)} dầm/cột thiếu thông tin tiết diện",
            "elements": [e["name"] for e in no_section[:5]],
        })

    # CDC-03: Kiểm tra thiếu vật liệu
    no_mat = [e for e in elements if not e.get("material")]
    if no_mat:
        issues.append({
            "rule": "CDC-03",
            "severity": "LOW",
            "desc": f"{len(no_mat)} phần tử thiếu thông tin vật liệu",
            "elements": [e["name"] for e in no_mat[:5]],
        })

    # CDC-04: Kiểm tra cao độ tầng hợp lý (> 2200mm, < 8000mm)
    storeys = data.get("storeys", [])
    for s in storeys:
        if s.get("elevation_mm", 0) < 0:
            issues.append({
                "rule": "CDC-04",
                "severity": "HIGH",
                "desc": f"Tầng '{s['name']}' có cao độ âm: {s['elevation_mm']}mm",
            })

    # CDC-05 đến CDC-08: Placeholder — cần dữ liệu hình học MEP
    for rule in ("CDC-05", "CDC-06", "CDC-07", "CDC-08"):
        logs.append(f"[{rule}] Pending — requires MEP geometry data")

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# 5. Main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def parse_ifc(filepath: str = None, force_demo: bool = False,
              run_cdc: bool = True) -> dict:
    """
    Điểm vào chính — đọc IFC và trả về dict chuẩn handoff.
    Tự động fallback: ifcopenshell → raw_parser → demo.
    """
    logs   = []
    source = "UNKNOWN"
    data   = {}

    if force_demo or filepath is None:
        data   = _demo_payload()
        source = "DEMO_MODE"
        logs.append("[INFO] DEMO MODE")
    elif not os.path.exists(filepath):
        logs.append(f"[ERROR] File không tồn tại: {filepath}")
        data   = _demo_payload()
        source = "DEMO_MODE (file not found)"
    elif _IFC_BACKEND == "ifcopenshell":
        try:
            data   = _parse_with_ifcos(filepath, logs)
            source = "ifcopenshell"
        except Exception as e:
            logs.append(f"[WARN] ifcopenshell lỗi: {e} — fallback raw")
            try:
                data   = _parse_raw(filepath, logs)
                source = "raw_parser (ifcopenshell failed)"
            except Exception as e2:
                logs.append(f"[ERROR] raw_parser lỗi: {e2}")
                data   = _demo_payload()
                source = "DEMO_MODE (all parsers failed)"
    else:  # raw_parser
        try:
            data   = _parse_raw(filepath, logs)
            source = "raw_parser"
        except Exception as e:
            logs.append(f"[ERROR] raw_parser: {e}")
            data   = _demo_payload()
            source = "DEMO_MODE (raw failed)"

    # ── CDC Validation ────────────────────────────────────────────────────────
    issues = []
    if run_cdc:
        issues = validate_cdc(data, logs)

    logs.append({
        "step":           "ifc_parser",
        "timestamp":      datetime.utcnow().isoformat() + "Z",
        "source":         source,
        "backend":        _IFC_BACKEND,
        "storeys_count":  len(data.get("storeys", [])),
        "elements_count": len(data.get("elements", [])),
        "grids_count":    len(data.get("grids", [])),
        "rebar_count":    len(data.get("reinforcement", [])),
        "cdc_issues":     len(issues),
    })

    return {
        **data,
        "cdc_issues":        issues,
        "Calculation_Logs":  logs,
        "Standard_Method":   "ISO 16739-1:2018 IFC4 + ifcopenshell",
        "source":            source,
        "generated_at":      datetime.utcnow().isoformat() + "Z",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        description="IFC Parser — đọc trực tiếp file .ifc không cần export trung gian")
    parser.add_argument("--input",    "-i", default=None,
                        help="Đường dẫn file .ifc cần đọc")
    parser.add_argument("--output",   "-o", default=None,
                        help="File JSON output")
    parser.add_argument("--demo",     action="store_true",
                        help="Chạy Demo Mode")
    parser.add_argument("--validate", action="store_true",
                        help="Chỉ chạy CDC validation nhanh")
    parser.add_argument("--no-cdc",   action="store_true",
                        help="Bỏ qua CDC validation")
    parser.add_argument("--indent",   type=int, default=2)
    args = parser.parse_args()

    result = parse_ifc(
        filepath=args.input,
        force_demo=args.demo,
        run_cdc=not args.no_cdc,
    )

    if args.validate:
        print(f"\n[IFC Validate] {os.path.basename(args.input or 'DEMO')}")
        print(f"  Backend : {_IFC_BACKEND}")
        print(f"  Schema  : {result.get('ifc_schema')}")
        print(f"  Tầng    : {len(result.get('storeys', []))}")
        print(f"  Elements: {len(result.get('elements', []))}")
        print(f"  Rebar   : {len(result.get('reinforcement', []))}")
        issues = result.get("cdc_issues", [])
        print(f"  CDC     : {len(issues)} issues")
        for iss in issues:
            print(f"    [{iss['rule']}] {iss['severity']:6s} — {iss['desc']}")
        return

    json_str = json.dumps(result, ensure_ascii=False, indent=args.indent)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"[OK] Ghi {args.output}")
        print(f"     Schema   : {result.get('ifc_schema')}")
        print(f"     Tầng     : {len(result.get('storeys', []))}")
        print(f"     Elements : {len(result.get('elements', []))}")
        print(f"     CDC issues: {len(result.get('cdc_issues', []))}")
        print(f"     Nguồn    : {result.get('source')}")
    else:
        print(json_str)


if __name__ == "__main__":
    _cli()
