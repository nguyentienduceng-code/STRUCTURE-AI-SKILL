#!/usr/bin/env python3
"""
validate_handoff_schema.py — Validate JSON handoff against SKILL_BRIDGE schemas

Usage:
    python validate_handoff_schema.py <handoff_file.json>

Exit codes:
    0 = Valid
    1 = Schema invalid
    2 = File not found
"""

import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from datetime import datetime
from pathlib import Path

# Schema definitions from SKILL_BRIDGE.md (v3.0.0 + v1.0 legacy)
SCHEMAS = {
    # ── v3.0.0 Schemas (SKILL_BRIDGE.md v3.0.0) ──────────────────────────────
    "structural_design_to_eval": {
        "version": "3.0.0",
        "required_meta": ["handoff_type", "source_skill", "target_skill", "timestamp"],
        "required_data": [],
        "valid_sources": ["Structural_Design_Engineer"],
        "valid_targets": ["Design_Evaluation"],
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
    # ── Legacy v1.0 Schemas (Backward Compatibility) ─────────────────────────
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
        "valid_confidence": None  # Optional for this schema
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
    """Load JSON file, return (data, error_msg)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except FileNotFoundError:
        return None, f"File not found: {filepath}"
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"


def validate_meta(data: dict, schema: dict) -> list:
    """Validate handoff_meta or _meta section"""
    errors = []

    meta = data.get("handoff_meta") or data.get("_meta")
    if not meta or not isinstance(meta, dict):
        errors.append("Missing required section: handoff_meta or _meta")
        return errors

    # Check required meta fields
    for field in schema.get("required_meta", []):
        if field not in meta:
            if field == "project_id" and "project_context" in data:
                continue
            errors.append(f"Missing required field in meta: {field}")

    # Check version compatibility if present
    if "version" in meta and schema.get("version"):
        exp_ver = schema["version"]
        act_ver = str(meta["version"])
        # Allow major version match (1.x for 1.0, 3.x for 3.0.0)
        if not (act_ver == exp_ver or act_ver.startswith(exp_ver.split('.')[0])):
            errors.append(f"Version mismatch: expected '{exp_ver}', got '{act_ver}'")

    # Check source skill
    if "source_skill" in meta:
        if schema.get("valid_sources") and meta["source_skill"] not in schema["valid_sources"]:
            errors.append(f"Invalid source_skill: '{meta['source_skill']}'. Valid: {schema['valid_sources']}")

    # Check target skill
    if "target_skill" in meta:
        if schema.get("valid_targets") and meta["target_skill"] not in schema["valid_targets"]:
            errors.append(f"Invalid target_skill: '{meta['target_skill']}'. Valid: {schema['valid_targets']}")

    # Check confidence level
    if "confidence_level" in meta:
        if schema.get("valid_confidence") and meta["confidence_level"] not in schema["valid_confidence"]:
            errors.append(f"Invalid confidence_level: '{meta['confidence_level']}'. Valid: {schema['valid_confidence']}")

    return errors


def validate_data(data: dict, schema: dict) -> list:
    """Validate data or payload section"""
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
    """
    Validate handoff JSON against schema.
    Returns: (is_valid, errors_list, warnings_list)
    """
    data, error = load_json(filepath)
    if error:
        return False, [error], []

    errors = []
    warnings = []

    # Determine schema type
    meta = data.get("handoff_meta") or data.get("_meta", {})
    handoff_type = meta.get("handoff_type", "")

    if handoff_type not in SCHEMAS:
        # Try to infer from source/target
        source = meta.get("source_skill", "")
        target = meta.get("target_skill", "")

        if source == "Structural_Design_Engineer" and target == "Design_Evaluation":
            handoff_type = "structural_design_to_eval"
        elif source == "Design_Evaluation" and target == "SKILL_PHULUC":
            handoff_type = "eval_to_phuluc"
        elif target == "SKILL_VERIFY":
            handoff_type = "calc_to_verify" if "handoff_meta" in data else "qa_check_request"
        elif source == "SKILL_GEOTECH" and target == "Structural_Design_Engineer":
            handoff_type = "geotech_to_structural" if "handoff_meta" in data else "foundation_params"
        elif source in ["Design_Evaluation", "Structural_Design_Engineer"] and target == "Cost_Estimator":
            handoff_type = "eval_to_cost" if "handoff_meta" in data else "design_output_for_ve"
        elif source == "SKILL_FORENSIC" and target == "Design_Evaluation":
            handoff_type = "forensic_to_eval"
        elif source == "SKILL_GEOTECH" and target == "Design_Evaluation":
            handoff_type = "foundation_review_request"
        else:
            errors.append(f"Unknown handoff_type: '{handoff_type}'. Cannot determine schema.")
            return False, errors, warnings

    schema = SCHEMAS.get(handoff_type, {})

    # Validate meta section
    errors.extend(validate_meta(data, schema))

    # Validate data section
    errors.extend(validate_data(data, schema))

    # Additional validations based on schema type
    if handoff_type == "foundation_params":
        # Check soil_layers structure
        if "soil_layers" in data and isinstance(data["soil_layers"], list):
            for i, layer in enumerate(data["soil_layers"]):
                if not isinstance(layer, dict):
                    errors.append(f"soil_layers[{i}] must be an object")
                else:
                    # Check required layer fields
                    for field in ["depth_top_m", "depth_bottom_m", "soil_type"]:
                        if field not in layer:
                            errors.append(f"soil_layers[{i}]: missing required field '{field}'")

        # Check design_params
        if "design_params" in data:
            dp = data["design_params"]
            if "q_allowable_kpa" not in dp:
                warnings.append("design_params.q_allowable_kpa not found - may be needed for foundation design")

    elif handoff_type == "design_output_for_ve":
        # Check elements array
        if "elements" in data and isinstance(data["elements"], list):
            for i, elem in enumerate(data["elements"]):
                if "eta" in elem:
                    eta = elem["eta"]
                    if eta > 1.0:
                        warnings.append(f"elements[{i}].eta = {eta:.2f} > 1.0 - NOT PASSING")
                    elif eta < 0.7:
                        warnings.append(f"elements[{i}].eta = {eta:.2f} < 0.7 - VE opportunity")

    elif handoff_type == "qa_check_request":
        # Check calculation_log_ids exists
        meta = data.get("_meta", {})
        if "calculation_log_ids" not in meta:
            if "calculation_log_id" not in meta:
                errors.append("Missing calculation_log_id(s) - cannot verify calculations")

        # Check verification scope
        if "check_scope" in data.get("results", {}):
            scope = data["results"]["check_scope"]
            if not any(scope.values()):
                warnings.append("check_scope has all false values - no verification will be performed")

    # Check for timestamp freshness (warning only)
    if "timestamp" in meta:
        try:
            ts = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))
            age_hours = (datetime.now() - ts).total_seconds() / 3600
            if age_hours > 24:
                warnings.append(f"Handoff is {age_hours:.1f} hours old - data may be stale")
        except:
            pass

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_handoff_schema.py <handoff_file.json>")
        print("\nSupported handoff types:")
        for htype in SCHEMAS.keys():
            print(f"  - {htype}")
        sys.exit(1)

    filepath = sys.argv[1]

    # Also accept directory - find latest handoff
    if os.path.isdir(filepath):
        dir_path = Path(filepath)
        json_files = list(dir_path.glob("*.json"))
        if not json_files:
            print(f"No JSON files found in {filepath}")
            sys.exit(2)
        # Get most recent
        filepath = max(json_files, key=lambda f: f.stat().st_mtime)
        print(f"Using most recent: {filepath.name}")

    is_valid, errors, warnings = validate_handoff(filepath)

    print(f"\n{'='*60}")
    print(f"Validation Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print(f"{'='*60}")

    if warnings:
        print(f"\n⚠ Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"\n✗ Errors ({len(errors)}):")
        for e in errors:
            print(f"  • {e}")

    print(f"\nFile: {filepath}")
    print(f"Validated: {datetime.now().isoformat()}")

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
