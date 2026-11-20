# -*- coding: utf-8 -*-
"""Compatibility adapter for DCE audit sidecars (v4 and v6).

The checker consumes the v4 evidence shape.  v6 sidecars remain the source of
truth; this module only normalizes their optional claims and never fabricates
semantic evidence.  Physical evidence is still cross-checked by the checker.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

V4_FIELDS = (
    "scale", "mode", "dxf_version", "entities_log", "blocks_defined",
    "dimstyles_defined", "layers_defined",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sidecar(dxf_file: Optional[Path], suffix: str = ".dce_audit.json") -> Dict[str, Any]:
    """Load a bound sidecar and reject malformed or stale evidence."""
    if dxf_file is None:
        return {}
    meta_file = dxf_file.with_suffix(suffix)
    if not meta_file.exists():
        raise ValueError(f"Missing bound audit sidecar: {meta_file}")
    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Metadata must be an object: {meta_file}")
    binding = payload.get("provenance", {})
    if not isinstance(binding, dict) or binding.get("dxf_sha256") != _sha256(dxf_file):
        raise ValueError(f"Missing or stale DXF SHA256 binding: {meta_file}")
    return payload


def normalize(payload: Dict[str, Any], dxf_file: Path) -> Dict[str, Any]:
    """Return the checker-compatible shape without inventing gate evidence.

    v4 payloads pass through unchanged. v6 claims are mapped where present;
    absent semantic claims become empty collections so gates report FAIL or
    UNVERIFIED rather than aborting the complete 20-gate run.
    """
    if not payload.get("v6_directive") and all(k in payload for k in V4_FIELDS):
        return payload

    registry = payload.get("element_registry")
    registry = registry if isinstance(registry, dict) else {}
    claims = payload.get("claims", {})
    claims = claims if isinstance(claims, dict) else {}

    normalized: Dict[str, Any] = dict(payload)
    normalized["evidence_schema_version"] = payload.get("evidence_schema_version", 6)
    normalized["dxf_version"] = payload.get("dxf_version", "AC1021")
    normalized["scale"] = claims.get("scale", payload.get("scale", 100.0))
    normalized["mode"] = claims.get("mode", payload.get("mode", "COLUMN_WALL_SETOUT"))
    normalized["entities_log"] = claims.get("entities_log", payload.get("entities_log", []))
    normalized["blocks_defined"] = claims.get("blocks_defined", payload.get("blocks_defined", {}))
    normalized["dimstyles_defined"] = claims.get("dimstyles_defined", payload.get("dimstyles_defined", {}))
    normalized["layers_defined"] = claims.get("layers_defined", payload.get("layers_defined", {}))
    normalized["element_registry"] = registry
    for opt_key in ("template_contract", "zone_evidence", "block_evidence"):
        if opt_key in payload:
            normalized[opt_key] = payload[opt_key]
        elif opt_key in claims:
            normalized[opt_key] = claims[opt_key]
    diagnostics: List[Any] = payload.get("v6_diagnostics", [])
    normalized["evidence_diagnostics"] = list(diagnostics) + [
        "V6 sidecar normalized through compatibility adapter; absent semantic claims were not inferred."
    ]
    return normalized


def load_evidence(dxf_file: Path, suffix: str = ".dce_audit.json") -> Dict[str, Any]:
    return normalize(load_sidecar(dxf_file, suffix), dxf_file)
