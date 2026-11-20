# -*- coding: utf-8 -*-
"""
cad_form_patcher.py — P4.1 Non-Destructive Selective-Sheet Patching Engine
=========================================================================

Specification: `CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md`, TÁC VỤ P4.1
(Interactive Form Modification Engine). The spec §3 diagram names this module
`non_destructive_patcher.py`; the §4 acceptance table names it `cad_form_patcher.py`.
This file implements that deliverable under the **acceptance-table name**
(`cad_form_patcher.py`) and is the *single, non-MCP, Drive-free* orchestrator for:

    open_form -> diff_form -> schema_gate -> apply_agent_changes
                 (read-only) (extract)   (E006)    (merge + selective regen)

Design constraints honoured (AGENTS.md + spec §3):
  * Non-destructive: user-drawn entities in the project-tier Form are PRESERVED on the
    regenerated sheets; UN-affected sheets are regenerated **not at all** so their
    output bytes stay identical (deterministic SHA-256).
  * Presentation Shell vs Engineering SSOT: only `model.json` mutates (v -> v+1); a
    revision snapshot is written to `model/revisions/model_v{N}.json`.
  * Error taxonomy (spec §3.3) — every code path returns one of:
        E001_FILE_NOT_FOUND
        E002_TEMPLATE_ZONE_MISSING
        E003_TITLEBLOCK_ATTDEF_MISSING
        E005_INVALID_DIFF
        E006_SCHEMA_GATE_REJECTED
  * No hand math: all limits are constants; the structural gate inspects explicit
    model fields and is *conditional* (additive) so it never breaks pre-P4 fixtures
    that omit the optional fields.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CAD_DIR = Path(__file__).resolve().parent
_AGENTS_DIR = _CAD_DIR.parents[2]
_SHARED_CTX = _AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
_TOOLS_DIR = _AGENTS_DIR / "tools"

for _p in (str(_CAD_DIR), str(_TOOLS_DIR), str(_SHARED_CTX)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ezdxf  # noqa: E402

import model_diff as mdf  # noqa: E402
import cad_form_contract as cfc  # noqa: E402
import project_ops_manager as pom  # noqa: E402


# ============================================================================
# Structural Schema Gate (spec §3.3) — additive limits on top of model_schema.json
# ============================================================================

MIN_SECTION_MM = 100.0          # TCVN 5574:2018 / spec: tiết diện không nhỏ hơn 100 mm
REBAR_RATIO_MIN = 0.1          # hàm lượng cốt thép dầm/cột mu_min (TCVN 5574:2018)
REBAR_RATIO_MAX = 3.0          # giới hạn trên phổ biến; mu > 3% => E006 (Điều 12c)
CONCRETE_GRADE_MAX_DEFAULT = 35   # B35 (Điều 12c — dân dụng, không đẩy mác)
CONCRETE_GRADE_MAX_WITH_NOTE = 40  # B40 chỉ khi Chủ đầu tư yêu cầu đặc thù (văn bản)

_CODE_E006 = "E006_SCHEMA_GATE_REJECTED"


def parse_concrete_grade(raw: Any) -> Optional[int]:
    """Parse a Vietnamese concrete grade label to its numeric class (B25 -> 25).

    Returns None when the value is absent or unparseable (never guesses — AGENTS §4).
    Accepts `B30`, `B35`, `M350`, `M400`; numeric is returned as the "B"-class.
    """
    if raw is None:
        return None
    s = str(raw).strip().upper()
    m = re.match(r"^([BM])\s*([0-9]+)", s)
    if not m:
        return None
    prefix, num = m.group(1), int(m.group(2))
    if prefix == "M":
        # M (MPa*100) -> B (MPa) conversion: M350 ~= B25, M400 ~= B30, M450 ~= B35, M500 ~= B40
        map_m = {200: 15, 250: 20, 300: 20, 350: 25, 400: 30, 450: 35, 500: 40, 550: 45, 600: 50}
        return map_m.get(num, None)
    return num


def _iter_viewport_elements(model: Dict[str, Any]):
    """Yield (context_label, element_dict) for every column/beam/pile across sheets."""
    for sh in model.get("sheets", []):
        sh_no = str(sh.get("sheet_no", "?"))
        for vp in sh.get("viewports", []):
            ctx = f"{sh_no}/{vp.get('id', '?')}"
            for col in vp.get("columns", []):
                yield f"{ctx} column {col.get('id', col.get('mark', '?'))}", col, "column"
            for bm in vp.get("beams", []):
                yield f"{ctx} beam {bm.get('mark', '?')}", bm, "beam"
            for pl in vp.get("piles", []):
                yield f"{ctx} pile {pl.get('id', '?')}", pl, "pile"


def _section_mm(el: Dict[str, Any], kind: str) -> List[float]:
    """Return the numeric section dims (mm) of an element; [] when not structurally sized."""
    if kind == "column":
        dims = []
        for k in ("b_mm", "h_mm"):
            v = el.get(k)
            if v is not None:
                dims.append(float(v))
        return dims
    if kind == "beam":
        size = str(el.get("size", "")).strip()
        m = re.match(r"^([0-9]+)\s*[xX]\s*([0-9]+)$", size)
        return [int(m.group(1)), int(m.group(2))] if m else []
    if kind == "pile":
        v = el.get("size_m")
        return [float(v) * 1000.0] if v is not None else []
    return []


def structural_schema_gate(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the list of structural-limit violations in `model` (empty = pass).

    Each violation: `{code, path, field, value, limit, message}`.
    - Concrete grade (project.concrete_grade): <= B35, or <= B40 only with an
      explicit CD note (project.concrete_grade_note). B50+ is always rejected (12c).
    - Section dims (b_mm/h_mm / beam size / pile size_m): every dim must be >= 100 mm
      and > 0 (negative/zero already caught by model_schema.json; the >=100 floor is new).
    - Rebar ratio (optional element.rebar_pct / element.mu_pct): must be in [0.1, 3.0].
    """
    violations: List[Dict[str, Any]] = []

    # 1) Concrete grade (conditional — additive).
    proj = model.get("project", {})
    grade_raw = proj.get("concrete_grade")
    if grade_raw is not None:
        grade = parse_concrete_grade(grade_raw)
        note = str(proj.get("concrete_grade_note", "") or "").strip()
        cap = CONCRETE_GRADE_MAX_WITH_NOTE if note else CONCRETE_GRADE_MAX_DEFAULT
        if grade is None:
            violations.append({
                "code": _CODE_E006,
                "path": "project.concrete_grade",
                "field": "concrete_grade",
                "value": grade_raw,
                "limit": f"parseable B/M grade <= B{cap}",
                "message": f"Concrete grade {grade_raw!r} không đọc được; ghi cấp bê tông hợp lệ (B20..B40).",
            })
        elif grade > cap:
            violations.append({
                "code": _CODE_E006,
                "path": "project.concrete_grade",
                "field": "concrete_grade",
                "value": grade_raw,
                "limit": f"B{cap}" + (" (yêu cầu Chủ đầu tư)" if note else " (Điều 12c, dân dụng)"),
                "message": (
                    f"Cấp bê tông {grade_raw!r} (class {grade}) vượt giới hạn B{cap}. "
                    "Ưu tiên tăng tiết diện / hàm lượng thép (Điều 12c AGENTS.md)."
                ),
            })

    # 2) Section-dim floor (>= MIN_SECTION_MM) + rebar-ratio band, per element.
    for ctx, el, kind in _iter_viewport_elements(model):
        # 2a) section floor
        for i, dim in enumerate(_section_mm(el, kind)):
            if not math.isfinite(dim) or dim < MIN_SECTION_MM:
                violations.append({
                    "code": _CODE_E006,
                    "path": ctx,
                    "field": f"{kind}_section[{i}]",
                    "value": dim,
                    "limit": f">= {MIN_SECTION_MM:.0f} mm",
                    "message": f"Tiết diện {ctx} = {dim:g} mm < {MIN_SECTION_MM:.0f} mm — từ chối merge.",
                })
        # 2b) rebar ratio band (conditional field)
        mu = el.get("rebar_pct", el.get("mu_pct"))
        if mu is not None:
            mv = float(mu)
            if mv < REBAR_RATIO_MIN or mv > REBAR_RATIO_MAX:
                violations.append({
                    "code": _CODE_E006,
                    "path": ctx,
                    "field": "rebar_pct",
                    "value": mu,
                    "limit": f"[{REBAR_RATIO_MIN}%, {REBAR_RATIO_MAX}%]",
                    "message": (
                        f"Hàm lượng cốt thép {ctx} = {mv:g}% ngoài dải "
                        f"[{REBAR_RATIO_MIN}%, {REBAR_RATIO_MAX}%] (TCVN 5574:2018) — từ chối merge."
                    ),
                })

    return violations


def combined_validate_fn(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-schema gate + structural gate. Raises mdf.DiffValidationError(E006) on breach."""
    pom.validate_model_dict(candidate)              # structural/JSON schema (raises ModelSchemaError)
    v = structural_schema_gate(candidate)
    if v:
        raise mdf.DiffValidationError(_CODE_E006, "Structural schema-gate rejected candidate.", v)
    return candidate


# ============================================================================
# The patcher
# ============================================================================

class NonDestructivePatcher:
    """Orchestrates open -> diff -> gate -> apply+selective-regen for one project Form.

    Every public method returns a plain dict whose `status`/`code` uses the spec §3.3
    taxonomy. No file is mutated until `apply_and_regen(commit=True)`.
    """

    def __init__(self, project_dir: str | Path, form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
                 baseline: str = "ssot"):
        self.project_dir = Path(project_dir)
        self.form_id = form_id
        self.baseline = baseline
        self._form_path: Optional[Path] = None
        self._baseline_path: Optional[Path] = None
        self._model: Optional[Dict[str, Any]] = None

    # -- helpers ------------------------------------------------------------
    def _resolve_form(self) -> cfc.FormResolution:
        return cfc.resolve_form_paths(form_id=self.form_id, project_dir=self.project_dir)

    def _baseline_form_path(self) -> Optional[Path]:
        spec = cfc.FORM_CATALOG.get(self.form_id)
        stem = Path(spec["filename"]).stem if spec else "Form"
        rev_dir = self.project_dir / "forms" / "revisions"
        if self.baseline == "prev_rev":
            # Sort by the numeric revision suffix (v002 < v010) — a plain
            # lexicographic sort would rank v9 after v10 with >=10 revisions.
            def _rev_no(p: Path) -> Optional[int]:
                m = re.match(rf"^{re.escape(stem)}_v(\d+)\.dxf$", p.name)
                return int(m.group(1)) if m else None
            revs = [p for p in rev_dir.glob(f"{stem}_v*.dxf")] if rev_dir.is_dir() else []
            revs.sort(key=lambda p: (_rev_no(p) is None, _rev_no(p) or 0, p.name))
            if len(revs) >= 2:
                return revs[-2]
            if len(revs) == 1:
                return revs[0]
            # No prior revision exists: diffing against the SSOT master would be
            # a silent baseline swap that changes the diff result, so surface it
            # as E001 instead (the caller can pass baseline="ssot" explicitly).
            raise mdf.DiffValidationError(
                "E001_FILE_NOT_FOUND",
                f"Baseline 'prev_rev' requested for '{self.form_id}' but no prior "
                f"form revision exists under {rev_dir}. Use baseline='ssot' instead.",
            )
        return cfc.SSOT_FORMS_DIR / spec["filename"] if spec else None

    def _load_model(self) -> Dict[str, Any]:
        model_path = self.project_dir / "model" / "model.json"
        if not model_path.is_file():
            raise mdf.DiffValidationError("E001_FILE_NOT_FOUND", f"Model SSOT not found: {model_path}")
        self._model = json.loads(model_path.read_text(encoding="utf-8"))
        return self._model

    # -- step 1: open_form (read-only inspection) --------------------------
    def open_form(self) -> Dict[str, Any]:
        res = self._resolve_form()
        if res.dxf_path is None:
            return {"status": "E001", "code": "E001_FILE_NOT_FOUND",
                    "error": f"Form '{self.form_id}' không tồn tại: {res.searched_paths}"}
        self._form_path = res.dxf_path
        val = cfc.validate_open_form(res.dxf_path, manifest_path=res.manifest_path,
                                     form_id=self.form_id, tier=res.tier)
        out = val.to_dict()
        # Surface the dominant taxonomy code for callers (E002/E003/W003...).
        codes = [e["code"] for e in val.errors]
        out["status"] = "OK" if val.valid else "INVALID"
        out["dominant_code"] = codes[0] if codes else None
        return out

    # -- step 2: diff_form (semantic diff extraction) ----------------------
    def diff_form(self) -> Dict[str, Any]:
        if self._form_path is None:
            self.open_form()
        if self._form_path is None:
            return {"status": "E001", "code": "E001_FILE_NOT_FOUND", "error": "Form không tồn tại."}
        # `base` and `model` are resolved OUTSIDE the try so their E001s
        # propagate to the caller (P4.1 contract: diff_form needs the Engineering
        # SSOT model + a valid baseline; missing either => raise, not swallow).
        base = self._baseline_form_path()
        model = self._load_model()
        try:
            res = mdf.extract_form_diff(self._form_path, base, model=model, form_id=self.form_id)
            res["baseline_mode"] = self.baseline
            return res
        except mdf.DiffValidationError as exc:
            return {"status": "ERROR", "code": exc.code, "error": exc.message, "details": exc.diff_details}

    # -- step 3: schema_gate (structural limits, candidate or model) -------
    def gate_model(self, model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target = model if model is not None else self._load_model()
        violations = structural_schema_gate(target)
        return {
            "status": "OK" if not violations else "REJECTED",
            "code": None if not violations else _CODE_E006,
            "violation_count": len(violations),
            "violations": violations,
        }

    # -- step 4: apply + selective regeneration ----------------------------
    def apply_and_regen(self, changes: Optional[Dict[str, Any]] = None,
                        commit: bool = True, compliance: str = "physical",
                        affected_sheets: Optional[List[str]] = None) -> Dict[str, Any]:
        model = self._load_model()

        if changes is None:
            changes = self.diff_form()
            if changes.get("status") not in ("OK", None):
                return {"status": "REJECTED", "code": changes.get("code", "E005_INVALID_DIFF"),
                        "error": changes.get("error", "Diff failed"), "committed": False,
                        "model_version": int(model.get("model_version", 1))}

        # Determine the set of sheets to regenerate before the merge (for the report).
        # Honour explicit arg > changes["affected_sheets"] (diff-derived) > all sheets.
        if not affected_sheets:
            affected_sheets = changes.get("affected_sheets")
        if not affected_sheets:
            affected_sheets = [str(s.get("sheet_no", "")) for s in model.get("sheets", [])
                               if s.get("sheet_no")]
        affected_sheets = [str(s) for s in affected_sheets if s]

        try:
            candidate, _ = mdf.apply_form_diff_to_model(model, changes,
                                                         validate_fn=combined_validate_fn)
        except mdf.DiffValidationError as exc:
            return {"status": "REJECTED", "code": exc.code, "error": exc.message,
                    "details": exc.diff_details, "committed": False,
                    "model_version": int(model.get("model_version", 1))}

        if not commit:
            return {"status": "DRY_RUN_OK", "committed": False,
                    "from_model_version": int(model["model_version"]),
                    "candidate_model_version": int(candidate["model_version"]),
                    "affected_sheets": [s for s in affected_sheets],
                    "patches_count": len(changes.get("model_patches", []))}

        # Persist SSOT + revision snapshot (v -> v+1).
        model_path = self.project_dir / "model" / "model.json"
        rev_path = self.project_dir / "model" / "revisions" / f"model_v{int(candidate['model_version']):03d}.json"
        pom._atomic_write_json(model_path, candidate)
        pom._atomic_write_json(rev_path, candidate)

        # Selective regeneration — ONLY affected sheets; unaffected sheets are untouched.
        dossier = pom.build_project_dossier(self.project_dir, form_id=self.form_id,
                                            sheet_numbers=affected_sheets, compliance=compliance)

        all_sheets = [s for s in [str(x.get("sheet_no", "")) for x in model.get("sheets", [])] if s]
        affected_set = set(affected_sheets)
        return {
            "status": "OK",
            "code": None,
            "committed": True,
            "region_scope_appid": "DCE_AGENT_OWNED",
            "from_model_version": int(model["model_version"]),
            "to_model_version": int(candidate["model_version"]),
            "revision_path": str(rev_path),
            "affected_sheets": list(dossier.get("sheets_generated", [])),
            "preserved_sheets": [s for s in all_sheets if s not in affected_set],
            "dossier_status": dossier.get("status"),
        }

    # -- one-shot convenience ----------------------------------------------
    def patch(self, commit: bool = True, affected_sheets: Optional[List[str]] = None,
              compliance: str = "physical") -> Dict[str, Any]:
        open_res = self.open_form()
        if open_res["status"] == "E001":
            return open_res
        if open_res["status"] == "INVALID":
            return {"status": "REJECTED", "code": open_res.get("dominant_code"),
                    "error": "Form INVALID — " + "; ".join(
                        e["code"] for e in open_res.get("errors", [])), "committed": False}
        diff = self.diff_form()
        if diff.get("status") == "ERROR":
            return {"status": "REJECTED", "code": diff.get("code"), "error": diff.get("error"),
                    "committed": False}
        return self.apply_and_regen(changes=diff, commit=commit,
                                    compliance=compliance, affected_sheets=affected_sheets)


def patch_project(project_dir: str | Path, form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
                  baseline: str = "ssot", commit: bool = True,
                  affected_sheets: Optional[List[str]] = None,
                  compliance: str = "physical") -> Dict[str, Any]:
    """Module-level one-shot entrypoint (no MCP, no Drive dependency)."""
    p = NonDestructivePatcher(project_dir, form_id=form_id, baseline=baseline)
    return p.patch(commit=commit, affected_sheets=affected_sheets, compliance=compliance)


if __name__ == "__main__":
    # Minimal CLI: python cad_form_patcher.py <project_dir> [form_id]
    args = sys.argv[1:]
    pdir = args[0] if args else "."
    fid = args[1] if len(args) > 1 else "FORM_02_MULTIVIEW_A3_BTCT"
    res = patch_project(pdir, form_id=fid, commit=False)
    print(json.dumps(res, ensure_ascii=False, indent=2))
