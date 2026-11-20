#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_ops_manager.py — P0-OPS Workspace, Schema-Gated Versioning, Lineage & 4-Command Runbook
================================================================================================

Implements P0-OPS from `DECISION_OPS_HYBRID_AUTHORING_20261116.md`:
  - Standardized workspace under `01_Projects/<DuAn>/`
    (`model/`, `forms/`, `blocks/`, `outputs/`, `audit/`, `ncr/`, `nrc/`)
  - Canonical `model_schema.json` validation (via `jsonschema`) + `model_version` snapshots
  - Append-only thin lineage at `audit/lineage.jsonl`
  - 4-command CLI runbook (`init-project`, `add-form`, `set-layer`, `apply-ncr`) + `build-dossier`
  - Diff-based NCR regeneration: modifies only affected element(s), bumps `model_version`,
    validates via schema-gate before commit, and regenerates only affected sheets.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TOOLS_DIR.parent
WORKSPACE_ROOT = AGENTS_DIR.parent
PROJECTS_ROOT = WORKSPACE_ROOT / "01_Projects"
SHARED_DATA_DIR = AGENTS_DIR / "_SHARED" / "data"
SHARED_CTX_DIR = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
CAD_DIR = AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration"
VERIFY_DIR = AGENTS_DIR / "skills" / "SKILL_VERIFY" / "scripts"

for _p in (str(SHARED_CTX_DIR), str(CAD_DIR), str(VERIFY_DIR), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf
try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from dce_block_catalog import get_block_catalog_version, get_default_catalog

from cad_form_contract import (
    FORM_CATALOG,
    SSOT_FORMS_DIR,
    USER_FORMS_DIR,
    refresh_manifest_from_form,
    validate_open_form,
)
from cad_layer_standard import get_layer_specs, get_standard_layer_whitelist
from cad_multiview_a3 import export_multiview_a3_sheet
from dce_cad_compliance_checker import audit_dxf_compliance

MODEL_SCHEMA_PATH = SHARED_DATA_DIR / "model_schema.json"
NCR_SCHEMA_PATH = SHARED_DATA_DIR / "ncr_schema.json"
STANDARDS_LOCK_PATH = AGENTS_DIR / "skills" / "STANDARDS_LOCK.md"


def _read_standards_lock_version() -> str:
    """Read active STANDARDS_LOCK.md version (e.g. 'v3.3.0') dynamically."""
    if STANDARDS_LOCK_PATH.is_file():
        head = "\n".join(STANDARDS_LOCK_PATH.read_text(encoding="utf-8").splitlines()[:20])
        m = re.search(r"v\d+\.\d+\.\d+", head)
        if m:
            return m.group(0)
    return "v3.3.0"


def _block_catalog_version() -> str:
    """Read the active catalog schema version from the SSOT catalog."""
    try:
        return get_block_catalog_version()
    except Exception:
        try:
            version = str(get_default_catalog().to_dict().get("schema_version", "")).strip()
            if version:
                return f"dce_block_catalog_v{version}"
        except Exception:
            pass
    return "dce_block_catalog_v6.0"


# Kept as a compatibility value; new locks resolve through the SSOT accessor.
BLOCK_CATALOG_VERSION = _block_catalog_version()

STANDARDS_REF_DEFAULT: Dict[str, Any] = {
    "version_lock": "STANDARDS_LOCK.md v3.3.0",
    "standards": {
        "TCVN 5574:2018": "Bê tông cốt thép",
        "TCVN 2737:2023": "Tải trọng & tác động",
        "TCVN 10304:2025": "Móng cọc",
        "TCVN 5575:2024": "Kết cấu thép",
        "TCVN 9386:2025": "Động đất",
    },
}


class ModelSchemaError(ValueError):
    """Raised when structural model JSON fails canonical `model_schema.json` validation."""


class IllegalLayerOverrideError(ValueError):
    """Raised when attempting to configure an illegal/non-standard layer outside SSOT."""


class NcrElementNotFoundError(LookupError):
    """Raised when target `element_id` cannot be found in active `model.json`."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{uuid.uuid4().hex[:8]}")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_model_dict(model: Dict[str, Any]) -> Dict[str, Any]:
    """Validate structural model dictionary strictly against `model_schema.json`."""
    if not isinstance(model, dict):
        raise ModelSchemaError("Model payload must be a JSON object.")

    schema = _load_schema(MODEL_SCHEMA_PATH)
    if jsonschema is not None:
        try:
            jsonschema.validate(instance=model, schema=schema)
        except jsonschema.ValidationError as exc:
            loc = ".".join(str(x) for x in exc.absolute_path) or "<root>"
            raise ModelSchemaError(f"Schema violation at '{loc}': {exc.message}") from exc
    else:  # pragma: no cover
        raise ModelSchemaError(
            "jsonschema is required for the model schema-gate; install jsonschema before continuing."
        )

    if int(model["model_version"]) < 1:
        raise ModelSchemaError(f"model_version must be >= 1, got {model['model_version']!r}")

    vlock = str(model.get("standards_ref", {}).get("version_lock", ""))
    if "STANDARDS_LOCK" not in vlock.upper():
        raise ModelSchemaError(f"standards_ref.version_lock must reference STANDARDS_LOCK.md, got {vlock!r}")
    return model


def validate_ncr_dict(ncr: Dict[str, Any]) -> Dict[str, Any]:
    """Validate NCR record strictly against `ncr_schema.json`."""
    if jsonschema is None:  # pragma: no cover
        raise ImportError("jsonschema package is required for NCR schema validation.")
    schema = _load_schema(NCR_SCHEMA_PATH)
    try:
        jsonschema.validate(instance=ncr, schema=schema)
    except jsonschema.ValidationError as exc:
        loc = ".".join(str(x) for x in exc.absolute_path) or "<root>"
        raise ValueError(f"NCR schema violation at '{loc}': {exc.message}") from exc
    return ncr


def _build_default_seed_model(project_code: str) -> Dict[str, Any]:
    """Return a clean minimal multi-view project model ready for authoring."""
    return {
        "model_id": project_code,
        "model_version": 1,
        "schema_version": "1.0",
        "standards_ref": copy.deepcopy(STANDARDS_REF_DEFAULT),
        "project": {
            "project_name": project_code,
            "drawing_category": "BẢN VẼ KẾT CẤU",
            "design_stage": "TKTC",
            "year": "2026",
            "scale": 100.0,
            "frame_mm": [42000.0, 29700.0],
            "L_total": 8.0,
            "B_total": 4.5,
            "grid_x": [["1", 0.0], ["2", 4.0], ["3", 8.0]],
            "grid_y": [["A", 0.0], ["B", 4.5]],
        },
        "sheets": [
            {
                "sheet_no": "KC.02",
                "title": "MẶT BẰNG ĐỊNH VỊ CỌC & KẾT CẤU TẦNG 1",
                "viewports": [
                    {
                        "id": "COC",
                        "slot": "TOP",
                        "title": "MẶT BẰNG ĐỊNH VỊ CỌC",
                        "scale_label": "TL: 1/100",
                        "origin_mm": [5200.0, 19600.0],
                        "slab_outline": [[0.0, 0.0], [8.0, 0.0], [8.0, 4.5], [0.0, 4.5]],
                        "piles": [
                            {"x": 0.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE1", "id": "P1"},
                            {"x": 4.0, "y": 0.0, "size_m": 0.25, "kind": "TYPE1", "id": "P2"},
                        ],
                        "columns": [
                            {"id": "C1", "mark": "C1", "kind": "RC", "b_mm": 200, "h_mm": 300, "x0": -0.10, "y0": -0.15, "x1": 0.10, "y1": 0.15},
                            {"id": "C2", "mark": "C2", "kind": "RC", "b_mm": 200, "h_mm": 200, "x0": 3.90, "y0": -0.10, "x1": 4.10, "y1": 0.10},
                        ],
                        "beams": [],
                        "voids": [],
                    },
                    {
                        "id": "T1",
                        "slot": "BOT",
                        "title": "MẶT BẰNG KẾT CẤU TẦNG 1",
                        "scale_label": "TL: 1/100",
                        "origin_mm": [5200.0, 5200.0],
                        "slab_outline": [[0.0, 0.0], [8.0, 0.0], [8.0, 4.5], [0.0, 4.5]],
                        "columns": [
                            {"id": "C1", "mark": "C1", "kind": "RC", "b_mm": 200, "h_mm": 300, "x0": -0.10, "y0": -0.15, "x1": 0.10, "y1": 0.15},
                            {"id": "C2", "mark": "C2", "kind": "RC", "b_mm": 200, "h_mm": 200, "x0": 3.90, "y0": -0.10, "x1": 4.10, "y1": 0.10},
                        ],
                        "beams": [
                            {"mark": "D1", "size": "200x400", "orient": "X", "x0": 0.10, "y0": -0.10, "x1": 3.90, "y1": 0.10, "show_label": True},
                        ],
                        "voids": [],
                    },
                ],
            }
        ],
    }


def enrich_model_metadata(model: Dict[str, Any], project_code: str) -> Dict[str, Any]:
    """Attach canonical P0-OPS versioning & standards metadata if absent, then schema-validate."""
    m = copy.deepcopy(model)
    m.setdefault("model_id", project_code)
    m.setdefault("model_version", 1)
    m.setdefault("schema_version", "1.0")
    m.setdefault("standards_ref", copy.deepcopy(STANDARDS_REF_DEFAULT))
    return validate_model_dict(m)


def _snapshot_block_catalog_lock(project_dir: Path) -> Path:
    lock_path = project_dir / "blocks" / "block_catalog_lock.json"
    forms_hashes: Dict[str, str] = {}
    form_versions: Dict[str, int] = {}
    for forms_folder in (project_dir / "forms", project_dir / "CAD_Forms"):
        if forms_folder.is_dir():
            for dxf in sorted(forms_folder.glob("*.dxf")):
                forms_hashes[dxf.name] = _sha256_file(dxf)
                man = dxf.with_suffix(".manifest.json")
                if man.is_file():
                    try:
                        form_versions[dxf.name] = int(json.loads(man.read_text(encoding="utf-8")).get("form_version", 1))
                    except Exception:
                        pass
    payload = {
        "block_catalog_version": _block_catalog_version(),
        "standards_lock": f"STANDARDS_LOCK.md {_read_standards_lock_version()}",
        "project_form_hashes": forms_hashes,
        "form_versions": form_versions,
        "updated_at": _now_iso(),
    }
    _atomic_write_json(lock_path, payload)
    return lock_path


def _save_form_revision(project_dir: Path, form_dxf: Path, form_man: Path) -> int:
    """Save numbered revision snapshot `<stem>_v00N.dxf` in `forms/revisions/` and update `form_version`."""
    rev_dir = project_dir / "forms" / "revisions"
    rev_dir.mkdir(parents=True, exist_ok=True)
    stem = form_dxf.stem
    existing = []
    for p in rev_dir.glob(f"{stem}_v*.dxf"):
        m = re.match(rf"^{re.escape(stem)}_v(\d+)$", p.stem)
        if m:
            existing.append(int(m.group(1)))
    ver = (max(existing) + 1) if existing else 1
    if form_man.is_file():
        try:
            mdata = json.loads(form_man.read_text(encoding="utf-8"))
        except Exception:
            mdata = {}
    else:
        mdata = {}
    mdata["form_version"] = ver
    mdata["updated_at"] = _now_iso()
    _atomic_write_json(form_man, mdata)
    shutil.copy2(form_dxf, rev_dir / f"{stem}_v{ver:03d}.dxf")
    shutil.copy2(form_man, rev_dir / f"{stem}_v{ver:03d}.manifest.json")
    return ver


def init_project_workspace(
    project_code: str,
    base_dir: Optional[str | Path] = None,
    seed_model: Optional[Dict[str, Any]] = None,
    seed_model_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Initialize `01_Projects/<DuAn>/` workspace with v1 schema-gated model & empty lineage."""
    clean_code = re.sub(r"[^A-Za-z0-9._-]+", "_", project_code.strip())
    if not clean_code:
        raise ValueError("project_code cannot be empty")

    root = Path(base_dir) if base_dir else PROJECTS_ROOT
    project_dir = root / clean_code
    for sub in ("model/revisions", "forms/revisions", "blocks", "outputs", "audit", "ncr", "nrc"):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    if seed_model is not None:
        raw_model = copy.deepcopy(seed_model)
    elif seed_model_path is not None:
        raw_model = json.loads(Path(seed_model_path).read_text(encoding="utf-8"))
    else:
        raw_model = _build_default_seed_model(clean_code)

    validated = enrich_model_metadata(raw_model, clean_code)
    model_path = project_dir / "model" / "model.json"
    rev_path = project_dir / "model" / "revisions" / f"model_v{int(validated['model_version']):03d}.json"
    _atomic_write_json(model_path, validated)
    _atomic_write_json(rev_path, validated)

    lock_path = _snapshot_block_catalog_lock(project_dir)
    lineage_path = project_dir / "audit" / "lineage.jsonl"
    if not lineage_path.exists():
        _atomic_write_text(lineage_path, "")

    return {
        "status": "OK",
        "project_dir": str(project_dir),
        "model_id": validated["model_id"],
        "model_version": validated["model_version"],
        "model_path": str(model_path),
        "revision_path": str(rev_path),
        "block_catalog_lock": str(lock_path),
        "lineage_path": str(lineage_path),
    }


def _find_source_form_pair(form_id: str, source_dir: Optional[Path] = None) -> Tuple[Path, Optional[Path], str]:
    if form_id not in FORM_CATALOG:
        raise ValueError(f"Unknown form_id '{form_id}'. Known: {list(FORM_CATALOG.keys())}")
    spec = FORM_CATALOG[form_id]
    fname, mname = spec["filename"], spec["manifest_filename"]
    candidates = []
    if source_dir is not None:
        candidates.append(("custom", Path(source_dir)))
    candidates.extend([("user_standards", USER_FORMS_DIR), ("ssot_fallback", SSOT_FORMS_DIR)])
    for tier, folder in candidates:
        dxf_p = folder / fname
        if dxf_p.is_file():
            man_p = folder / mname
            return dxf_p, (man_p if man_p.is_file() else None), tier
    raise FileNotFoundError(f"Source Form '{form_id}' not found in user or SSOT directories.")


def runbook_add_form(
    project_dir: str | Path,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    overwrite: bool = False,
    source_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Runbook cmd 2: Copy & validate an editable Form DXF + manifest into `<project_dir>/forms/`."""
    proj = Path(project_dir)
    forms_dir = proj / "forms"
    forms_dir.mkdir(parents=True, exist_ok=True)
    spec = FORM_CATALOG[form_id]
    dst_dxf = forms_dir / spec["filename"]
    dst_man = forms_dir / spec["manifest_filename"]

    if dst_dxf.exists() and not overwrite:
        raise FileExistsError(f"Form already exists at {dst_dxf}; pass overwrite=True to replace.")

    src_dxf, src_man, src_tier = _find_source_form_pair(form_id, Path(source_dir) if source_dir else None)
    shutil.copy2(src_dxf, dst_dxf)
    if src_man and src_man.exists():
        shutil.copy2(src_man, dst_man)
    refresh_manifest_from_form(dst_dxf, manifest_path=dst_man, form_id=form_id)
    val = validate_open_form(dst_dxf, manifest_path=dst_man, form_id=form_id, tier="project")
    if not val.valid:
        raise ValueError(f"Copied Form failed validation: {val.errors}")
    form_ver = _save_form_revision(proj, dst_dxf, dst_man)
    _snapshot_block_catalog_lock(proj)

    return {
        "status": "OK",
        "form_id": form_id,
        "form_version": form_ver,
        "source_tier": src_tier,
        "dxf_path": str(dst_dxf),
        "manifest_path": str(dst_man),
        "dxf_sha256": val.inventory.get("dxf_sha256", ""),
        "zones": sorted(val.zones_wcs.keys()),
    }


def runbook_set_layer(
    project_dir: str | Path,
    form_id: str,
    layer_name: str,
    color: Optional[int] = None,
    linetype: Optional[str] = None,
    lineweight: Optional[int] = None,
) -> Dict[str, Any]:
    """Runbook cmd 3: Update layer styling on `<project_dir>/forms/<Form>.dxf` guarded by SSOT whitelist."""
    proj = Path(project_dir)
    whitelist = get_standard_layer_whitelist()
    lname_clean = str(layer_name).strip()
    if lname_clean.lower() not in whitelist:
        raise IllegalLayerOverrideError(
            f"Layer '{lname_clean}' is not in SSOT whitelist (STANDARDS_LOCK / dce_layers_standard.json)."
        )

    if form_id not in FORM_CATALOG:
        raise ValueError(f"Unknown form_id: {form_id}")
    form_dxf = proj / "forms" / FORM_CATALOG[form_id]["filename"]
    form_man = proj / "forms" / FORM_CATALOG[form_id]["manifest_filename"]
    if not form_dxf.is_file():
        raise FileNotFoundError(f"Project form not found at {form_dxf}. Run `add-form` first.")

    doc = ezdxf.readfile(str(form_dxf))
    if lname_clean in doc.layers:
        ly = doc.layers.get(lname_clean)
    else:
        ssot = get_layer_specs(profile="dce_native", include_compat=False)
        base_spec = ssot.get(lname_clean, {"color": 7, "linetype": "Continuous", "lineweight": 18})
        lt0 = str(base_spec.get("linetype", "Continuous"))
        if lt0 not in doc.linetypes:
            lt0 = "Continuous"
        ly = doc.layers.add(lname_clean, color=int(base_spec.get("color", 7)), linetype=lt0, lineweight=int(base_spec.get("lineweight", 18)))

    before = {
        "color": int(getattr(ly.dxf, "color", 7)),
        "linetype": str(getattr(ly.dxf, "linetype", "Continuous")),
        "lineweight": int(getattr(ly.dxf, "lineweight", 18)),
    }
    if color is not None:
        ly.dxf.color = int(color)
    if linetype is not None:
        if linetype not in doc.linetypes:
            raise ValueError(f"Linetype '{linetype}' not defined in Form DXF.")
        ly.dxf.linetype = str(linetype)
    if lineweight is not None:
        if int(lineweight) <= 0:
            raise ValueError(f"Lineweight must be > 0, got {lineweight}")
        ly.dxf.lineweight = int(lineweight)

    after = {
        "color": int(ly.dxf.color),
        "linetype": str(ly.dxf.linetype),
        "lineweight": int(ly.dxf.lineweight),
    }
    doc.saveas(str(form_dxf), encoding="utf-8")
    refresh_manifest_from_form(form_dxf, manifest_path=form_man, form_id=form_id)
    form_ver = _save_form_revision(proj, form_dxf, form_man)
    _snapshot_block_catalog_lock(proj)

    return {
        "status": "OK",
        "form_id": form_id,
        "form_version": form_ver,
        "layer": lname_clean,
        "before": before,
        "after": after,
        "form_sha256": _sha256_file(form_dxf),
    }


def _iter_sheet_elements(sheet_spec: Dict[str, Any]):
    """Unified iterator yielding (aliases, vp_id, elem_kind, elem_dict) across viewports."""
    for vp in sheet_spec.get("viewports", []):
        vp_id = str(vp.get("id", "")).strip()
        for col in vp.get("columns", []):
            cid = str(col.get("id", "")).strip()
            cmark = str(col.get("mark", "")).strip()
            aliases = [a for a in (cid, f"{vp_id}_{cid}" if (vp_id and cid) else "", cmark) if a]
            yield tuple(dict.fromkeys(aliases)), vp_id, "column", col
        for bm in vp.get("beams", []):
            bmark = str(bm.get("mark", "")).strip()
            aliases = [a for a in (bmark, f"{vp_id}_{bmark}" if (vp_id and bmark) else "") if a]
            yield tuple(dict.fromkeys(aliases)), vp_id, "beam", bm
        for pidx, pl in enumerate(vp.get("piles", [])):
            pid = str(pl.get("id") or f"{vp_id}_P{pidx + 1}").strip()
            aliases = [a for a in (pid,) if a]
            yield tuple(aliases), vp_id, "pile", pl


def _collect_sheet_element_ids(sheet_spec: Dict[str, Any]) -> List[str]:
    ids = set()
    for aliases, _vp_id, _kind, _obj in _iter_sheet_elements(sheet_spec):
        ids.update(aliases)
    return sorted(ids)


def _sheet_filename(sheet_spec: Dict[str, Any]) -> str:
    if sheet_spec.get("filename"):
        return Path(str(sheet_spec["filename"])).name
    sno = str(sheet_spec.get("sheet_no", "KC-02")).strip().replace(".", "-")
    return f"{sno}.dxf"


def _classify_compliance_status(audit_res: Dict[str, Any], compliance: str) -> str:
    """Honest compliance status classifier (F1): never equate `physical` with Filter 8 PASS."""
    raw = str(audit_res.get("status", "UNKNOWN")).upper()
    if compliance == "physical":
        return "DXF_INTEGRITY_PASS" if raw == "PASS" else "DXF_INTEGRITY_FAIL"
    if raw == "PASS":
        if compliance == "full" and not audit_res.get("full_compliance_verified"):
            return "NEEDS_REVIEW"
        return f"FILTER8_{compliance.upper()}_PASS"
    if raw == "NEEDS_REVIEW":
        return "NEEDS_REVIEW"
    return f"FILTER8_{compliance.upper()}_FAIL"


def build_project_dossier(
    project_dir: str | Path,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    sheet_numbers: Optional[List[str]] = None,
    compliance: str = "physical",
    full_evidence: bool = False,
    layout_mode: str = "model",
) -> Dict[str, Any]:
    """Generate schema-validated CAD outputs (`model` or `paperspace`), run audit, and append thin lineage."""
    eff_comp = str(compliance or "physical").lower()
    if eff_comp not in ("physical", "plan", "full"):
        raise ValueError(f"Unsupported compliance profile: {compliance!r}; expected physical|plan|full")
    eff_layout_mode = str(layout_mode or "model").lower()
    if eff_layout_mode not in ("model", "paperspace"):
        raise ValueError(f"Unsupported layout_mode: {layout_mode!r}; expected model|paperspace")

    proj = Path(project_dir)
    model_path = proj / "model" / "model.json"
    if not model_path.is_file():
        raise FileNotFoundError(f"Model SSOT not found: {model_path}")

    model = validate_model_dict(json.loads(model_path.read_text(encoding="utf-8")))
    model_sha = _sha256_file(model_path)

    lock_path = proj / "blocks" / "block_catalog_lock.json"
    if lock_path.is_file():
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        block_ver = lock_data.get("block_catalog_version", _block_catalog_version())
        form_versions_map = lock_data.get("form_versions", {})
    else:
        block_ver = _block_catalog_version()
        form_versions_map = {}

    sheets = list(model.get("sheets", []))
    target_norm = {s.strip().upper().replace("-", ".") for s in sheet_numbers} if sheet_numbers else None

    outputs_dir = proj / "outputs"
    audit_dir = proj / "audit"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    lineage_path = audit_dir / "lineage.jsonl"

    generated: List[Dict[str, Any]] = []
    lineage_lines: List[str] = []
    used_names: set = set()
    form_fname = FORM_CATALOG[form_id]["filename"] if form_id in FORM_CATALOG else ""
    form_ver = int(form_versions_map.get(form_fname, 1)) if form_fname else 1

    if eff_layout_mode == "paperspace":
        from cad_paperspace_builder import export_single_file_multilayout_dxf
        from cad_form_contract import resolve_form_paths

        master_dxf = outputs_dir / f"{model['model_id']}_MASTER_SET.dxf"
        ps_res = export_single_file_multilayout_dxf(
            master_dxf,
            model=model,
            form_id=form_id,
            project_dir=proj,
            full_evidence=full_evidence,
        )
        audit_res = audit_dxf_compliance(str(master_dxf), profile=eff_comp)
        comp_status = _classify_compliance_status(audit_res, eff_comp)
        dxf_sha = ps_res["single_file_sha256"]
        rel_dxf = master_dxf.relative_to(proj).as_posix()
        f_res = resolve_form_paths(form_id=form_id, project_dir=proj)
        form_sha = _sha256_file(f_res.dxf_path) if (f_res.dxf_path and f_res.dxf_path.is_file()) else ""
        for lay in ps_res.get("layouts", []):
            sh_no = str(lay["sheet_no"])
            sh_match = next((s for s in sheets if str(s.get("sheet_no")) == sh_no), {})
            record = {
                "timestamp": _now_iso(),
                "model_id": model["model_id"],
                "model_version": int(model["model_version"]),
                "model_sha256": model_sha,
                "sheet_no": sh_no,
                "layout_name": lay["layout_name"],
                "layout_mode": "paperspace",
                "form_id": form_id,
                "form_version": form_ver,
                "form_tier": f_res.tier,
                "form_sha256": form_sha,
                "block_catalog_version": block_ver,
                "standards_ref": model["standards_ref"].get("version_lock", "STANDARDS_LOCK.md v3.3.0"),
                "dxf_path": rel_dxf,
                "dxf_sha256": dxf_sha,
                "compliance_profile": eff_comp,
                "audit_status": comp_status,
                "element_ids": _collect_sheet_element_ids(sh_match) if sh_match else [],
            }
            lineage_lines.append(json.dumps(record, ensure_ascii=False))
            generated.append(record)
    else:
        for sh in sheets:
            sh_no = str(sh.get("sheet_no", ""))
            if target_norm is not None and sh_no.upper().replace("-", ".") not in target_norm:
                continue

            out_name = _sheet_filename(sh)
            if out_name in used_names:
                out_name = f"{sh_no.strip().replace('.', '-')}.dxf"
            used_names.add(out_name)
            out_dxf = outputs_dir / out_name
            if form_id == "FORM_02_MULTIVIEW_A3_BTCT":
                eng = export_multiview_a3_sheet(
                    str(out_dxf),
                    model=model,
                    sheet_no=sh_no,
                    v6=True,
                    template_mode="open",
                    form_id=form_id,
                    project_dir=str(proj),
                    dry_run=False,
                    full_evidence=full_evidence,
                )
                tc = getattr(eng, "template_contract", None) or {}
                f_tier = tc.get("tier", "unknown")
                form_sha = str(tc.get("inventory", {}).get("dxf_sha256", ""))
            else:
                from cad_paperspace_builder import export_with_open_form
                from cad_form_contract import resolve_form_paths

                sub_model = {**model, "sheets": [sh]}
                export_with_open_form(
                    out_dxf,
                    model=sub_model,
                    form_id=form_id,
                    project_dir=proj,
                    layout_mode="model",
                    full_evidence=full_evidence,
                )
                f_res = resolve_form_paths(form_id=form_id, project_dir=proj)
                f_tier = f_res.tier
                form_sha = _sha256_file(f_res.dxf_path) if (f_res.dxf_path and f_res.dxf_path.is_file()) else ""

            audit_res = audit_dxf_compliance(str(out_dxf), profile=eff_comp)
            comp_status = _classify_compliance_status(audit_res, eff_comp)
            dxf_sha = _sha256_file(out_dxf)
            rel_dxf = out_dxf.relative_to(proj).as_posix()
            elem_ids = _collect_sheet_element_ids(sh)

            record = {
                "timestamp": _now_iso(),
                "model_id": model["model_id"],
                "model_version": int(model["model_version"]),
                "model_sha256": model_sha,
                "sheet_no": sh_no,
                "layout_mode": "model",
                "form_id": form_id,
                "form_version": form_ver,
                "form_tier": f_tier,
                "form_sha256": form_sha,
                "block_catalog_version": block_ver,
                "standards_ref": model["standards_ref"].get("version_lock", "STANDARDS_LOCK.md v3.3.0"),
                "dxf_path": rel_dxf,
                "dxf_sha256": dxf_sha,
                "compliance_profile": eff_comp,
                "audit_status": comp_status,
                "element_ids": elem_ids,
            }
            lineage_lines.append(json.dumps(record, ensure_ascii=False))
            generated.append(record)

    if not generated:
        raise ValueError(f"No matching sheets exported for sheet_numbers={sheet_numbers!r}")

    with lineage_path.open("a", encoding="utf-8") as lf:
        for line in lineage_lines:
            lf.write(line + "\n")
        lf.flush()
        os.fsync(lf.fileno())

    ok_labels = {"DXF_INTEGRITY_PASS", "FILTER8_PLAN_PASS", "FILTER8_FULL_PASS"}
    statuses = [r["audit_status"] for r in generated]
    if all(s in ok_labels for s in statuses):
        overall = statuses[0] if len(set(statuses)) == 1 else f"FILTER8_{eff_comp.upper()}_PASS"
    elif any("FAIL" in s for s in statuses):
        overall = "DXF_INTEGRITY_FAIL" if eff_comp == "physical" else f"FILTER8_{eff_comp.upper()}_FAIL"
    else:
        overall = "NEEDS_REVIEW"

    dossier_manifest = {
        "model_id": model["model_id"],
        "model_version": int(model["model_version"]),
        "standards_ref": model["standards_ref"],
        "block_catalog_version": block_ver,
        "compliance_profile": eff_comp,
        "generated_at": _now_iso(),
        "overall_status": overall,
        "sheets": generated,
    }
    _atomic_write_json(outputs_dir / "dossier_manifest.json", dossier_manifest)
    _atomic_write_json(audit_dir / "compliance_report.json", dossier_manifest)

    return {
        "status": overall,
        "compliance_profile": eff_comp,
        "model_id": model["model_id"],
        "model_version": int(model["model_version"]),
        "sheets_generated": [r["sheet_no"] for r in generated],
        "records": generated,
        "lineage_path": str(lineage_path),
        "dossier_manifest_path": str(outputs_dir / "dossier_manifest.json"),
    }


def _next_ncr_id(ncr_dir: Path) -> str:
    nums = []
    if ncr_dir.is_dir():
        for p in ncr_dir.glob("NCR-*.json"):
            m = re.match(r"NCR-(\d+)", p.stem)
            if m:
                nums.append(int(m.group(1)))
    nxt = (max(nums) + 1) if nums else 1
    return f"NCR-{nxt:03d}"


def _coerce_field_value(field: str, raw_val: Any) -> Any:
    if field in ("b_mm", "h_mm", "size_m", "x", "y"):
        if isinstance(raw_val, (int, float)):
            return raw_val
        try:
            fval = float(raw_val)
            return int(fval) if fval.is_integer() and field in ("b_mm", "h_mm") else fval
        except (ValueError, TypeError):
            return raw_val
    return raw_val


def runbook_apply_ncr(
    project_dir: str | Path,
    element_id: str,
    field: str,
    new_value: Any,
    reason: str = "",
    source: str = "FIELD_NCR",
    severity: str = "MAJOR",
    auto_regenerate: bool = True,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    compliance: str = "physical",
) -> Dict[str, Any]:
    """Runbook cmd 4: Schema-gated NCR back-loop -> version +1 -> regenerate only affected sheets."""
    proj = Path(project_dir)
    model_path = proj / "model" / "model.json"
    if not model_path.is_file():
        raise FileNotFoundError(f"Model SSOT not found: {model_path}")

    current = validate_model_dict(json.loads(model_path.read_text(encoding="utf-8")))
    candidate = copy.deepcopy(current)
    coerced = _coerce_field_value(field, new_value)
    old_values: List[Any] = []
    affected_sheets: List[str] = []

    for sh in candidate.get("sheets", []):
        sh_no = str(sh.get("sheet_no", ""))
        matched_in_sheet = False
        for aliases, _vp_id, elem_kind, elem_obj in _iter_sheet_elements(sh):
            if element_id in aliases:
                old_values.append(elem_obj.get(field))
                elem_obj[field] = coerced
                if elem_kind == "column" and field in ("b_mm", "h_mm") and all(k in elem_obj for k in ("x0", "x1", "y0", "y1")):
                    try:
                        b_new = float(elem_obj["b_mm"])
                        h_new = float(elem_obj["h_mm"])
                        if b_new > 0 and h_new > 0:
                            cx = (float(elem_obj["x0"]) + float(elem_obj["x1"])) / 2.0
                            cy = (float(elem_obj["y0"]) + float(elem_obj["y1"])) / 2.0
                            elem_obj["x0"] = round(cx - b_new / 2000.0, 4)
                            elem_obj["x1"] = round(cx + b_new / 2000.0, 4)
                            elem_obj["y0"] = round(cy - h_new / 2000.0, 4)
                            elem_obj["y1"] = round(cy + h_new / 2000.0, 4)
                    except (ValueError, TypeError):
                        pass
                matched_in_sheet = True
        if matched_in_sheet and sh_no and sh_no not in affected_sheets:
            affected_sheets.append(sh_no)

    if not affected_sheets:
        raise NcrElementNotFoundError(f"Element '{element_id}' not found in {model_path}")

    from_ver = int(current["model_version"])
    to_ver = from_ver + 1
    candidate["model_version"] = to_ver

    # Schema-gate BEFORE committing any revision to disk
    validate_model_dict(candidate)

    ncr_dir = proj / "ncr"
    nrc_dir = proj / "nrc"
    ncr_id = _next_ncr_id(ncr_dir)

    _atomic_write_json(model_path, candidate)
    rev_path = proj / "model" / "revisions" / f"model_v{to_ver:03d}.json"
    _atomic_write_json(rev_path, candidate)

    # NCR record is written BEFORE regeneration (status APPLIED_PENDING_REGEN):
    # if `build_project_dossier` crashes or is interrupted, the model change is
    # still traceable (no silent drift). On success the record is re-written
    # with APPLIED_AND_REGENERATED.
    ncr_record = {
        "ncr_id": ncr_id,
        "model_id": candidate["model_id"],
        "from_model_version": from_ver,
        "to_model_version": to_ver,
        "element_id": element_id,
        "field": field,
        "old_value": old_values[0] if len(old_values) == 1 else old_values,
        "new_value": coerced,
        "reason": reason,
        "source": source,
        "severity": severity,
        "status": "APPLIED_PENDING_REGEN",
        "affected_sheets": affected_sheets,
        "created_at": _now_iso(),
    }
    validate_ncr_dict(ncr_record)
    _atomic_write_json(ncr_dir / f"{ncr_id}.json", ncr_record)
    _atomic_write_json(nrc_dir / f"{ncr_id}.json", ncr_record)

    regen_res: Optional[Dict[str, Any]] = None
    if auto_regenerate:
        regen_res = build_project_dossier(
            proj, form_id=form_id, sheet_numbers=affected_sheets, compliance=compliance
        )
        ncr_record["status"] = "APPLIED_AND_REGENERATED"
        ncr_record["regenerated_at"] = _now_iso()
        validate_ncr_dict(ncr_record)
        _atomic_write_json(ncr_dir / f"{ncr_id}.json", ncr_record)
        _atomic_write_json(nrc_dir / f"{ncr_id}.json", ncr_record)

    ncr_md = "\n".join([
        f"# PHIẾU NCR KHÔNG PHÙ HỢP KỸ THUẬT: {ncr_id}",
        f"",
        f"- **Dự án (`model_id`):** `{ncr_record['model_id']}`",
        f"- **Mức độ (`severity`):** `{severity}` | **Nguồn (`source`):** `{source}`",
        f"- **Cấu kiện (`element_id`):** `{element_id}`",
        f"- **Trường thay đổi:** `{field}`: `{ncr_record['old_value']}` $\\to$ `{coerced}`",
        f"- **Phiên bản Model:** `v{from_ver}` $\\to$ `v{to_ver}`",
        f"- **Tờ ảnh hưởng tái sinh:** `{', '.join(affected_sheets)}`",
        f"- **Lý do:** {reason or 'Cập nhật theo hiện trường / thẩm tra'}",
        f"- **Trạng thái:** `{ncr_record['status']}` (`{ncr_record['created_at']}`)",
        "",
    ])
    _atomic_write_text(ncr_dir / f"{ncr_id}.md", ncr_md)

    return {
        "status": "OK",
        "ncr_id": ncr_id,
        "from_model_version": from_ver,
        "to_model_version": to_ver,
        "affected_sheets": affected_sheets,
        "ncr_path": str(ncr_dir / f"{ncr_id}.json"),
        "ncr_md_path": str(ncr_dir / f"{ncr_id}.md"),
        "revision_path": str(rev_path),
        "regeneration": regen_res,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DCE P0-OPS Project Workspace & 4-Command Runbook CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-project", help="1. Initialize standardized 01_Projects/<DuAn> workspace")
    p_init.add_argument("--project", required=True, help="Project folder code under 01_Projects/")
    p_init.add_argument("--base-dir", default=None, help="Optional custom projects root")
    p_init.add_argument("--seed-model", default=None, help="Optional seed model JSON file")

    p_add = sub.add_parser("add-form", help="2. Copy and validate editable Form DXF into project forms/")
    p_add.add_argument("--project-dir", required=True)
    p_add.add_argument("--form-id", default="FORM_02_MULTIVIEW_A3_BTCT")
    p_add.add_argument("--overwrite", action="store_true")

    p_layer = sub.add_parser("set-layer", help="3. Update SSOT-validated layer styling in project form")
    p_layer.add_argument("--project-dir", required=True)
    p_layer.add_argument("--form-id", default="FORM_02_MULTIVIEW_A3_BTCT")
    p_layer.add_argument("--layer", required=True)
    p_layer.add_argument("--color", type=int, default=None)
    p_layer.add_argument("--linetype", default=None)
    p_layer.add_argument("--lineweight", type=int, default=None)

    p_ncr = sub.add_parser("apply-ncr", help="4. Apply NCR field change -> v+1 -> regenerate affected sheets")
    p_ncr.add_argument("--project-dir", required=True)
    p_ncr.add_argument("--element-id", required=True)
    p_ncr.add_argument("--field", required=True)
    p_ncr.add_argument("--new-value", required=True)
    p_ncr.add_argument("--reason", default="")
    p_ncr.add_argument("--source", default="FIELD_NCR")
    p_ncr.add_argument("--severity", default="MAJOR", choices=["CRITICAL", "MAJOR", "MINOR"])
    p_ncr.add_argument("--form-id", default="FORM_02_MULTIVIEW_A3_BTCT")
    p_ncr.add_argument("--compliance", default="physical", choices=["physical", "plan", "full"])
    p_ncr.add_argument("--no-regen", action="store_true")

    p_build = sub.add_parser("build-dossier", help="Build dossier DXFs + compliance audit + lineage.jsonl")
    p_build.add_argument("--project-dir", required=True)
    p_build.add_argument("--form-id", default="FORM_02_MULTIVIEW_A3_BTCT")
    p_build.add_argument("--sheets", default=None, help="Comma-separated sheet numbers (e.g. KC.02,KC.03)")
    p_build.add_argument("--compliance", default="physical", choices=["physical", "plan", "full"])
    p_build.add_argument("--layout-mode", default="model", choices=["model", "paperspace"])
    p_build.add_argument("--full-evidence", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "init-project":
        out = init_project_workspace(args.project, base_dir=args.base_dir, seed_model_path=args.seed_model)
    elif args.cmd == "add-form":
        out = runbook_add_form(args.project_dir, form_id=args.form_id, overwrite=args.overwrite)
    elif args.cmd == "set-layer":
        out = runbook_set_layer(
            args.project_dir, args.form_id, args.layer,
            color=args.color, linetype=args.linetype, lineweight=args.lineweight,
        )
    elif args.cmd == "apply-ncr":
        out = runbook_apply_ncr(
            args.project_dir, args.element_id, args.field, args.new_value,
            reason=args.reason, source=args.source, severity=args.severity,
            auto_regenerate=not args.no_regen, form_id=args.form_id,
            compliance=args.compliance,
        )
    else:
        sheets = [s.strip() for s in args.sheets.split(",") if s.strip()] if args.sheets else None
        out = build_project_dossier(
            args.project_dir, form_id=args.form_id, sheet_numbers=sheets,
            compliance=args.compliance, full_evidence=args.full_evidence,
            layout_mode=args.layout_mode,
        )

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
