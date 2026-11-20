# -*- coding: utf-8 -*-
"""
cad_form_contract.py — Open Form Contract, 3-Tier Form Resolver & Read-Only Validator
=====================================================================================

Implements Phase 0 of the 4-Form Customizable CAD Architecture:
1. Canonical 4-Form catalog (Form 01..Form 04) + manifest schema (v1.0).
2. 3-tier Form resolution order:
     (1) <project_dir>/CAD_Forms/
     (2) <workspace>/00_Template_&_Standards/CAD_Forms/   (user-editable on Drive)
     (3) <workspace>/.agents/_SHARED/data/CAD_Forms/      (immutable SSOT fallback)
3. Strict read-only contract validator (`validate_open_form`):
   - Checks DXF version (`AC1021` safe base; > AC1021 => `ROUNDTRIP_LIMITED`).
   - Checks `source_space` (`MODEL` supported in v1; explicit mapping required for `PAPER`).
   - Checks UCS / non-orthogonal transform (`W003 TEMPLATE_TRANSFORM_REVIEW`).
   - Reads explicit WCS bounding boxes from `DCE_ZONE_*` marker polylines
     (missing required zone => `E002 TEMPLATE_ZONE_MISSING`, never guesses coordinates).
   - Verifies named `DCE_TITLEBLOCK_*` block exists with required `ATTDEF` tags
     (`E003 TITLEBLOCK_ATTDEF_MISSING`, never silently falls back to static TEXT).
   - Inventories layers, dimstyles, textstyles, blocks, and dynamic `*U*` presence.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf

CAD_INTEGRATION_DIR = Path(__file__).resolve().parent
AGENTS_DIR = CAD_INTEGRATION_DIR.parents[2]
WORKSPACE_ROOT = AGENTS_DIR.parent

AGENT_OWNED_APPID = "DCE_AGENT_OWNED"
FORM_CONTRACT_VERSION = "1.0"

USER_FORMS_DIR = WORKSPACE_ROOT / "00_Template_&_Standards" / "CAD_Forms"
SSOT_FORMS_DIR = AGENTS_DIR / "_SHARED" / "data" / "CAD_Forms"

DEFAULT_REQUIRED_TITLE_TAGS = [
    "TEN_CONG_TRINH",
    "TEN_BAN_VE",
    "KY_HIEU",
    "TY_LE",
]

DEFAULT_ALLOWLIST_TITLE_TAGS = [
    "CHU_DAU_TU",
    "DIA_DIEM",
    "DIA_DIEM_2",
    "CONG_TY",
    "DIA_CHI_CTY",
    "EMAIL_CTY",
    "TEL_CTY",
    "GIAM_DOC",
    "KIEM_TRA",
    "THIET_KE",
    "THE_HIEN",
    "TEN_CONG_TRINH",
    "HANG_MUC",
    "TEN_BAN_VE",
    "BUOC_TK",
    "NAM",
    "NGAY_VE",
    "KY_HIEU",
    "TY_LE",
]

FORM_CATALOG: Dict[str, Dict[str, Any]] = {
    "FORM_01_MATBANG_A1_BTCT": {
        "form_id": "FORM_01_MATBANG_A1_BTCT",
        "filename": "Form_01_MatBang_A1_BTCT.dxf",
        "manifest_filename": "Form_01_MatBang_A1_BTCT.manifest.json",
        "title_vi": "Form 01 — Mặt bằng Kết cấu BTCT (Khổ A1/A0)",
        "sheet_size": "A1",
        "frame_mm": [84100.0, 59400.0],
        "source_space": "MODEL",
        "titleblock_block": "DCE_TITLEBLOCK_A1",
        "required_zones": {
            "VIEWPORT_MAIN": "DCE_ZONE_VIEWPORT_MAIN",
            "TABLE_SCHEDULE": "DCE_ZONE_TABLE",
            "NOTE": "DCE_ZONE_NOTE",
            "TITLEBLOCK": "DCE_TITLEBLOCK_A1",
        },
        "zone_aliases": {
            "VIEWPORT_MAIN": ["DCE_ZONE_VIEWPORT"],
        },
        "required_title_tags": list(DEFAULT_REQUIRED_TITLE_TAGS),
        "preserve_user_styles": True,
        "min_supported_dxf_version": "AC1021",
        "profile": "rc_plan",
    },
    "FORM_02_MULTIVIEW_A3_BTCT": {
        "form_id": "FORM_02_MULTIVIEW_A3_BTCT",
        "filename": "Form_02_MultiView_A3_BTCT.dxf",
        "manifest_filename": "Form_02_MultiView_A3_BTCT.manifest.json",
        "title_vi": "Form 02 — Bản vẽ Triển khai Nhiều Khung nhìn (Khổ A3 Ngang)",
        "sheet_size": "A3",
        "frame_mm": [42000.0, 29700.0],
        "source_space": "MODEL",
        "titleblock_block": "DCE_TITLEBLOCK_A3",
        "required_zones": {
            "VIEWPORT_TOP": "DCE_ZONE_VIEWPORT_TOP",
            "VIEWPORT_BOTTOM": "DCE_ZONE_VIEWPORT_BOTTOM",
            "TABLE": "DCE_ZONE_TABLE",
            "NOTE": "DCE_ZONE_NOTE",
            "KEYPLAN": "DCE_ZONE_KEYPLAN",
            "TITLEBLOCK": "DCE_TITLEBLOCK_A3",
        },
        "zone_aliases": {
            "VIEWPORT_TOP": ["DCE_ZONE_VP_TOP"],
            "VIEWPORT_BOTTOM": ["DCE_ZONE_VP_BOT"],
        },
        "required_title_tags": list(DEFAULT_REQUIRED_TITLE_TAGS),
        "preserve_user_styles": True,
        "min_supported_dxf_version": "AC1021",
        "profile": "multiview_a3",
    },
    "FORM_03_KETCAU_THEP_STEEL": {
        "form_id": "FORM_03_KETCAU_THEP_STEEL",
        "filename": "Form_03_KetCau_Thep_Steel.dxf",
        "manifest_filename": "Form_03_KetCau_Thep_Steel.manifest.json",
        "title_vi": "Form 03 — Kết cấu Thép & Liên kết (DCE STEEL, Khổ A1)",
        "sheet_size": "A1",
        "frame_mm": [84100.0, 59400.0],
        "source_space": "MODEL",
        "titleblock_block": "DCE_TITLEBLOCK_A1",
        "required_zones": {
            "VIEWPORT_MAIN": "DCE_ZONE_VIEWPORT_MAIN",
            "TABLE_STEEL": "DCE_ZONE_TABLE",
            "NOTE": "DCE_ZONE_NOTE",
            "TITLEBLOCK": "DCE_TITLEBLOCK_A1",
        },
        "zone_aliases": {
            "VIEWPORT_MAIN": ["DCE_ZONE_VIEWPORT"],
        },
        "required_title_tags": list(DEFAULT_REQUIRED_TITLE_TAGS),
        "preserve_user_styles": True,
        "min_supported_dxf_version": "AC1021",
        "profile": "steel",
    },
    "FORM_04_CHITIET_COC_DAM_COT": {
        "form_id": "FORM_04_CHITIET_COC_DAM_COT",
        "filename": "Form_04_ChiTiet_Coc_Dam_Cot.dxf",
        "manifest_filename": "Form_04_ChiTiet_Coc_Dam_Cot.manifest.json",
        "title_vi": "Form 04 — Chi tiết Cọc, Đài Móng, Dầm, Cột & Thống kê Thép (Khổ A3)",
        "sheet_size": "A3",
        "frame_mm": [42000.0, 29700.0],
        "source_space": "MODEL",
        "titleblock_block": "DCE_TITLEBLOCK_A3",
        "required_zones": {
            "VIEWPORT_DETAIL_1": "DCE_ZONE_DETAIL_1",
            "VIEWPORT_DETAIL_2": "DCE_ZONE_DETAIL_2",
            "TABLE_REBAR": "DCE_ZONE_TABLE",
            "NOTE": "DCE_ZONE_NOTE",
            "TITLEBLOCK": "DCE_TITLEBLOCK_A3",
        },
        "zone_aliases": {
            "VIEWPORT_DETAIL_1": ["DCE_ZONE_VIEWPORT_TOP"],
            "VIEWPORT_DETAIL_2": ["DCE_ZONE_VIEWPORT_BOTTOM"],
        },
        "required_title_tags": list(DEFAULT_REQUIRED_TITLE_TAGS),
        "preserve_user_styles": True,
        "min_supported_dxf_version": "AC1021",
        "profile": "detail_rebar",
    },
}


@dataclass
class FormResolution:
    form_id: str
    dxf_path: Optional[Path]
    manifest_path: Optional[Path]
    tier: str  # "explicit" | "project" | "user_standards" | "ssot_fallback" | "missing"
    searched_paths: List[str] = field(default_factory=list)


@dataclass
class FormValidationResult:
    valid: bool
    form_id: str
    dxf_path: str
    manifest_path: Optional[str]
    tier: str
    dxf_version: str
    source_space: str
    roundtrip_status: str  # "FULL" | "ROUNDTRIP_LIMITED"
    ucs_ok: bool
    zones_wcs: Dict[str, List[Tuple[float, float, float, float]]] = field(default_factory=dict)
    titleblock_block: Optional[str] = None
    titleblock_insert_count: int = 0
    titleblock_tags: List[str] = field(default_factory=list)
    extra_title_tags: List[str] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)
    inventory: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_default_manifest(form_id: str) -> Dict[str, Any]:
    if form_id not in FORM_CATALOG:
        raise KeyError(f"Unknown form_id: {form_id}")
    spec = FORM_CATALOG[form_id]
    return {
        "template_contract_version": FORM_CONTRACT_VERSION,
        "form_id": spec["form_id"],
        "title_vi": spec["title_vi"],
        "sheet_size": spec["sheet_size"],
        "frame_mm": list(spec["frame_mm"]),
        "source_space": spec["source_space"],
        "titleblock_block": spec["titleblock_block"],
        "required_zones": dict(spec["required_zones"]),
        "zone_aliases": dict(spec.get("zone_aliases", {})),
        "required_title_tags": list(spec["required_title_tags"]),
        "allowlist_title_tags": list(DEFAULT_ALLOWLIST_TITLE_TAGS),
        "preserve_user_styles": bool(spec["preserve_user_styles"]),
        "min_supported_dxf_version": spec["min_supported_dxf_version"],
        "profile": spec["profile"],
        "agent_owned_appid": AGENT_OWNED_APPID,
    }


def resolve_form_paths(
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    project_dir: Optional[str | Path] = None,
    explicit_form_path: Optional[str | Path] = None,
    user_forms_dir: Optional[str | Path] = None,
    ssot_forms_dir: Optional[str | Path] = None,
) -> FormResolution:
    """Resolve Form DXF + manifest across the 3-tier hierarchy."""
    spec = FORM_CATALOG.get(form_id)
    if spec is None:
        raise ValueError(f"Unknown form_id '{form_id}'. Known forms: {list(FORM_CATALOG.keys())}")

    fname = spec["filename"]
    mname = spec["manifest_filename"]
    searched: List[str] = []

    if explicit_form_path:
        p = Path(explicit_form_path)
        searched.append(str(p))
        if p.exists():
            mp = p.with_suffix(".manifest.json")
            if not mp.exists():
                alt = p.parent / mname
                mp = alt if alt.exists() else None
            return FormResolution(form_id=form_id, dxf_path=p, manifest_path=mp, tier="explicit", searched_paths=searched)

    candidates: List[Tuple[str, Path]] = []
    if project_dir:
        candidates.append(("project", Path(project_dir) / "CAD_Forms"))
        candidates.append(("project", Path(project_dir) / "forms"))
    candidates.append(("user_standards", Path(user_forms_dir) if user_forms_dir else USER_FORMS_DIR))
    candidates.append(("ssot_fallback", Path(ssot_forms_dir) if ssot_forms_dir else SSOT_FORMS_DIR))

    for tier_name, folder in candidates:
        p = folder / fname
        searched.append(str(p))
        if p.exists():
            mp = p.with_suffix(".manifest.json")
            if not mp.exists():
                mp2 = folder / mname
                mp = mp2 if mp2.exists() else None
            return FormResolution(form_id=form_id, dxf_path=p, manifest_path=mp, tier=tier_name, searched_paths=searched)

    return FormResolution(form_id=form_id, dxf_path=None, manifest_path=None, tier="missing", searched_paths=searched)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lwpoly_bbox(ent) -> Optional[Tuple[float, float, float, float]]:
    try:
        pts = list(ent.get_points("xy"))
        if len(pts) < 2:
            return None
        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]
        return (round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3))
    except Exception:
        return None


def _check_ucs_world_orthogonal(doc: ezdxf.document.Drawing) -> Tuple[bool, Dict[str, Any]]:
    """Verify $UCSORG is (0,0,0) and X/Y axes are standard World or orthogonal unit vectors."""
    try:
        org = tuple(float(v) for v in doc.header.get("$UCSORG", (0.0, 0.0, 0.0)))
        xdir = tuple(float(v) for v in doc.header.get("$UCSXDIR", (1.0, 0.0, 0.0)))
        ydir = tuple(float(v) for v in doc.header.get("$UCSYDIR", (0.0, 1.0, 0.0)))
    except Exception:
        return True, {"origin": (0.0, 0.0, 0.0), "xdir": (1.0, 0.0, 0.0), "ydir": (0.0, 1.0, 0.0)}

    dot = xdir[0] * ydir[0] + xdir[1] * ydir[1] + xdir[2] * ydir[2]
    nx = math.sqrt(sum(v * v for v in xdir))
    ny = math.sqrt(sum(v * v for v in ydir))
    is_world = (
        max(abs(org[0]), abs(org[1]), abs(org[2])) < 1e-3
        and abs(xdir[0] - 1.0) < 1e-3 and abs(xdir[1]) < 1e-3
        and abs(ydir[1] - 1.0) < 1e-3 and abs(ydir[0]) < 1e-3
    )
    is_ortho = abs(dot) < 1e-3 and abs(nx - 1.0) < 1e-3 and abs(ny - 1.0) < 1e-3
    return bool(is_world and is_ortho), {
        "origin": org,
        "xdir": xdir,
        "ydir": ydir,
        "is_world": is_world,
        "is_orthogonal": is_ortho,
    }


def _dxf_version_num(ver: str) -> int:
    try:
        return int(str(ver).upper().replace("AC", "").strip())
    except Exception:
        return 0


def validate_open_form(
    dxf_path: str | Path,
    manifest_path: Optional[str | Path] = None,
    form_id: Optional[str] = None,
    tier: str = "explicit",
) -> FormValidationResult:
    """Strictly validate an Open Form DXF + manifest in read-only mode."""
    p = Path(dxf_path)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    manifest: Dict[str, Any] = {}
    mp_resolved: Optional[Path] = Path(manifest_path) if manifest_path else None
    if mp_resolved is None:
        cand = p.with_suffix(".manifest.json")
        if cand.exists():
            mp_resolved = cand

    if mp_resolved and mp_resolved.exists():
        try:
            manifest = json.loads(mp_resolved.read_text(encoding="utf-8"))
        except Exception as ex:
            errors.append({"code": "E000_MANIFEST_INVALID", "message": f"Invalid manifest JSON: {ex}"})

    eff_form_id = form_id or manifest.get("form_id") or "FORM_02_MULTIVIEW_A3_BTCT"
    if not manifest and eff_form_id in FORM_CATALOG:
        manifest = build_default_manifest(eff_form_id)

    if not p.exists():
        errors.append({"code": "E001_FORM_NOT_FOUND", "message": f"Form DXF not found: {p}"})
        return FormValidationResult(
            valid=False,
            form_id=eff_form_id,
            dxf_path=str(p),
            manifest_path=str(mp_resolved) if mp_resolved else None,
            tier=tier,
            dxf_version="UNKNOWN",
            source_space=str(manifest.get("source_space", "MODEL")),
            roundtrip_status="ROUNDTRIP_LIMITED",
            ucs_ok=False,
            errors=errors,
            warnings=warnings,
        )

    doc = ezdxf.readfile(str(p))
    dxf_ver = str(getattr(doc, "dxfversion", "AC1021"))
    ver_num = _dxf_version_num(dxf_ver)
    roundtrip_status = "FULL"
    if ver_num > 1021 or ver_num == 0:
        roundtrip_status = "ROUNDTRIP_LIMITED"
        warnings.append({
            "code": "W001_DXF_VERSION_HIGH",
            "message": f"DXF version {dxf_ver} > AC1021; exporting copy with ROUNDTRIP_LIMITED caution.",
        })

    src_space = str(manifest.get("source_space", "MODEL")).upper()
    if src_space not in ("MODEL", "PAPER"):
        errors.append({"code": "E001_UNSUPPORTED_SPACE", "message": f"Unsupported source_space: {src_space}"})
    elif src_space == "PAPER":
        layout_name = manifest.get("paper_layout_name")
        vp_handle = manifest.get("paper_viewport_handle")
        if not (layout_name and vp_handle):
            errors.append({
                "code": "E001_PAPER_MAPPING_REQUIRED",
                "message": "PAPER source_space requires explicit paper_layout_name and paper_viewport_handle.",
            })

    ucs_ok, ucs_info = _check_ucs_world_orthogonal(doc)
    if not ucs_ok:
        warnings.append({
            "code": "W003_TEMPLATE_TRANSFORM_REVIEW",
            "message": f"Non-World or non-orthogonal UCS detected: {ucs_info}",
        })

    msp = doc.modelspace()
    zones_by_layer: Dict[str, List[Tuple[float, float, float, float]]] = {}
    title_inserts: Dict[str, int] = {}
    dynamic_inserts: List[str] = []
    agent_owned_count = 0

    for ent in msp:
        et = ent.dxftype()
        try:
            if ent.has_xdata(AGENT_OWNED_APPID):
                agent_owned_count += 1
        except Exception:
            pass
        layer = str(getattr(ent.dxf, "layer", "0"))
        if et == "LWPOLYLINE" and layer.upper().startswith("DCE_ZONE_"):
            bb = _lwpoly_bbox(ent)
            if bb is not None:
                zones_by_layer.setdefault(layer.upper(), []).append(bb)
        elif et == "INSERT":
            bname = str(getattr(ent.dxf, "name", ""))
            if bname.startswith("*U"):
                dynamic_inserts.append(bname)
            if bname.upper().startswith("DCE_TITLEBLOCK") or bname == manifest.get("titleblock_block"):
                title_inserts[bname] = title_inserts.get(bname, 0) + 1

    # Resolve required zones cleanly using manifest + aliases
    required_zones: Dict[str, str] = dict(manifest.get("required_zones", {}))
    zone_aliases: Dict[str, List[str]] = dict(manifest.get("zone_aliases", {}))
    expected_tb = str(manifest.get("titleblock_block", "DCE_TITLEBLOCK_A3"))
    zones_wcs: Dict[str, List[Tuple[float, float, float, float]]] = {}

    for z_key, z_layer in required_zones.items():
        if z_key == "TITLEBLOCK" or z_layer == expected_tb:
            continue
        matched_boxes = list(zones_by_layer.get(z_layer.upper(), []))
        if not matched_boxes:
            for alias in zone_aliases.get(z_key, []):
                matched_boxes = list(zones_by_layer.get(alias.upper(), []))
                if matched_boxes:
                    break
        if matched_boxes:
            zones_wcs[z_key] = matched_boxes
        else:
            errors.append({
                "code": "E002_TEMPLATE_ZONE_MISSING",
                "message": f"Missing required zone '{z_key}' (layer '{z_layer}') in {p.name}.",
            })

    # Validate TitleBlock definition + ATTDEFs + ModelSpace INSERT
    tb_block = doc.blocks.get(expected_tb)
    tb_attdefs: List[str] = []
    extra_tags: List[str] = []
    req_tags = list(manifest.get("required_title_tags", DEFAULT_REQUIRED_TITLE_TAGS))
    allowlist = set(manifest.get("allowlist_title_tags", DEFAULT_ALLOWLIST_TITLE_TAGS))
    if tb_block is None:
        errors.append({
            "code": "E003_TITLEBLOCK_BLOCK_MISSING",
            "message": f"Missing named block '{expected_tb}' in {p.name}.",
        })
    else:
        tb_attdefs = [e.dxf.tag for e in tb_block if e.dxftype() == "ATTDEF"]
        missing_tags = [t for t in req_tags if t not in tb_attdefs]
        if missing_tags:
            errors.append({
                "code": "E003_TITLEBLOCK_ATTDEF_MISSING",
                "message": f"Block '{expected_tb}' missing required ATTDEF tags: {missing_tags}.",
            })
        extra_tags = [t for t in tb_attdefs if t not in allowlist]

    tb_insert_cnt = title_inserts.get(expected_tb, 0)
    if "TITLEBLOCK" in required_zones and tb_insert_cnt == 0:
        warnings.append({
            "code": "W002_TITLEBLOCK_NOT_PLACED_IN_MSP",
            "message": f"Block '{expected_tb}' is defined but not inserted in ModelSpace; engine may insert it.",
        })

    # Read-only inventory for evidence sidecar / diagnostics
    dimstyles = [ds.dxf.name for ds in doc.dimstyles]
    layers = [ly.dxf.name for ly in doc.layers]
    textstyles = [ts.dxf.name for ts in doc.styles]
    named_blocks = [b.name for b in doc.blocks if not b.name.startswith("*")]
    dyn_anon_blocks = [b.name for b in doc.blocks if b.name.startswith("*U") and len(b) > 0]

    inventory = {
        "dxf_sha256": _sha256(p),
        "layer_count": len(layers),
        "dimstyle_count": len(dimstyles),
        "textstyle_count": len(textstyles),
        "named_block_count": len(named_blocks),
        "dynamic_anonymous_block_count": len(dyn_anon_blocks),
        "dynamic_inserts_in_msp": len(dynamic_inserts),
        "agent_owned_entity_count": agent_owned_count,
        "has_Dce_KhTenTruc": "Dce_KhTenTruc" in doc.blocks,
        "has_DCE_Pile": any(b.startswith("DCE_Pile") for b in named_blocks),
        "ucs": ucs_info,
    }

    return FormValidationResult(
        valid=(len(errors) == 0),
        form_id=eff_form_id,
        dxf_path=str(p),
        manifest_path=str(mp_resolved) if mp_resolved else None,
        tier=tier,
        dxf_version=dxf_ver,
        source_space=src_space,
        roundtrip_status=roundtrip_status,
        ucs_ok=ucs_ok,
        zones_wcs=zones_wcs,
        titleblock_block=expected_tb if tb_block is not None else None,
        titleblock_insert_count=tb_insert_cnt,
        titleblock_tags=tb_attdefs,
        extra_title_tags=extra_tags,
        errors=errors,
        warnings=warnings,
        inventory=inventory,
    )


def refresh_manifest_from_form(
    dxf_path: str | Path,
    manifest_path: Optional[str | Path] = None,
    form_id: Optional[str] = None,
) -> Path:
    """Refresh `.manifest.json` WCS zone snapshots after the engineer edits a Form DXF in AutoCAD."""
    p = Path(dxf_path)
    mp = Path(manifest_path) if manifest_path else p.with_suffix(".manifest.json")
    base = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else build_default_manifest(
        form_id or "FORM_02_MULTIVIEW_A3_BTCT"
    )
    val = validate_open_form(p, manifest_path=mp if mp.exists() else None, form_id=base["form_id"])
    base["dxf_sha256"] = val.inventory.get("dxf_sha256", "")
    base["dxf_version"] = val.dxf_version
    base["roundtrip_status"] = val.roundtrip_status
    base["zones_wcs_snapshot"] = val.zones_wcs
    base["detected_title_tags"] = val.titleblock_tags
    mp.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    return mp
