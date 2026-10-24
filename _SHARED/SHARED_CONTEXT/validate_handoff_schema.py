#!/usr/bin/env python3
"""
validate_handoff_schema.py — Validate JSON handoff against SKILL_BRIDGE schemas (v3.1.0)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from datetime import datetime
from pathlib import Path

SCHEMAS = {
    "structural_design_to_eval": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Structural_Design_Engineer"],
        "valid_targets": ["Design_Evaluation"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "structural_to_tempworks": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Structural_Design_Engineer"],
        "valid_targets": ["SKILL_TEMPWORKS"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "tempworks_to_cost": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["SKILL_TEMPWORKS"],
        "valid_targets": ["Cost_Estimator"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "eval_to_phuluc": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Design_Evaluation"],
        "valid_targets": ["SKILL_PHULUC"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "calc_to_verify": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Structural_Design_Engineer", "Design_Evaluation", "SKILL_GEOTECH", "SKILL_FORENSIC", "SKILL_TEMPWORKS"],
        "valid_targets": ["SKILL_VERIFY"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "any_to_verify": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Structural_Design_Engineer", "Design_Evaluation", "SKILL_GEOTECH", "SKILL_FORENSIC", "SKILL_TEMPWORKS"],
        "valid_targets": ["SKILL_VERIFY"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "geotech_to_structural": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["SKILL_GEOTECH"],
        "valid_targets": ["Structural_Design_Engineer"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "eval_to_cost": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Design_Evaluation", "Structural_Design_Engineer"],
        "valid_targets": ["Cost_Estimator"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "forensic_to_eval": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["SKILL_FORENSIC"],
        "valid_targets": ["Design_Evaluation"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "foundation_params": {
        "version": "1.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": ["soil_layers", "design_params", "assumptions"],
        "valid_sources": ["SKILL_GEOTECH"],
        "valid_targets": ["Structural_Design_Engineer"],
        "valid_confidence": ["HIGH", "MEDIUM", "LOW"]
    },
    "design_output_for_ve": {
        "version": "1.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": ["structural_system", "elements"],
        "valid_sources": ["Structural_Design_Engineer"],
        "valid_targets": ["Cost_Estimator"],
        "valid_confidence": None
    },
    "qa_check_request": {
        "version": "1.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": ["calculation_reference", "input_data", "results"],
        "valid_sources": ["Structural_Design_Engineer", "Design_Evaluation"],
        "valid_targets": ["SKILL_VERIFY"],
        "valid_confidence": None
    },
    "ve_analysis_request": {
        "version": "1.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": ["review_summary", "cost_context"],
        "valid_sources": ["Design_Evaluation"],
        "valid_targets": ["Cost_Estimator"],
        "valid_confidence": None
    },
    "foundation_review_request": {
        "version": "1.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": ["foundation_type", "soil_conditions", "design_params_provided"],
        "valid_sources": ["SKILL_GEOTECH"],
        "valid_targets": ["Design_Evaluation"],
        "valid_confidence": None
    }
}


def load_json(filepath: str) -> tuple:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except FileNotFoundError:
        return None, f"File not found: {filepath}"
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"


def validate_meta(data: dict, schema: dict) -> list:
    errors = []
    meta = data.get("handoff_meta") or data.get("_meta")
    if not meta or not isinstance(meta, dict):
        errors.append("Missing required section: handoff_meta or _meta")
        return errors

    for field in schema.get("required_meta", []):
        if field not in meta:
            if field == "project_id" and "project_context" in data:
                continue
            errors.append(f"Missing required field in meta: {field}")

    if "version" in meta and schema.get("version"):
        exp_ver = schema["version"]
        act_ver = str(meta["version"])
        if not (act_ver == exp_ver or act_ver.startswith(exp_ver.split('.')[0])):
            errors.append(f"Version mismatch: expected '{exp_ver}', got '{act_ver}'")

    if "source_skill" in meta and schema.get("valid_sources") and meta["source_skill"] not in schema["valid_sources"]:
        errors.append(f"Invalid source_skill: '{meta['source_skill']}'")
    if "target_skill" in meta and schema.get("valid_targets") and meta["target_skill"] not in schema["valid_targets"]:
        errors.append(f"Invalid target_skill: '{meta['target_skill']}'")
    if "confidence_level" in meta and schema.get("valid_confidence") and meta["confidence_level"] not in schema["valid_confidence"]:
        errors.append(f"Invalid confidence_level: '{meta['confidence_level']}'")
    return errors


def validate_data(data: dict, schema: dict) -> list:
    errors = []
    target = data.get("payload") if isinstance(data.get("payload"), dict) else data
    for field in schema.get("required_data", []):
        if field not in target:
            errors.append(f"Missing required field: {field}")
        elif target[field] is None:
            errors.append(f"Null value for required field: {field}")
        elif isinstance(target[field], list) and len(target[field]) == 0:
            errors.append(f"Empty array for required field: {field}")
    return errors


def validate_handoff(filepath: str) -> tuple:
    data, error = load_json(filepath)
    if error:
        return False, [error], []

    errors = []
    warnings = []
    meta = data.get("handoff_meta") or data.get("_meta", {})
    handoff_type = meta.get("handoff_type", "")

    if handoff_type not in SCHEMAS:
        errors.append(f"Unknown handoff_type: '{handoff_type}'. Cannot determine schema.")
        return False, errors, warnings

    schema = SCHEMAS.get(handoff_type, {})
    errors.extend(validate_meta(data, schema))
    errors.extend(validate_data(data, schema))

    if "timestamp" in meta:
        try:
            ts = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))
            now_dt = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
            age_hours = (now_dt - ts).total_seconds() / 3600
            if age_hours > 24:
                warnings.append(f"Handoff is {age_hours:.1f} hours old - data may be stale")
        except Exception:
            pass

    return len(errors) == 0, errors, warnings
