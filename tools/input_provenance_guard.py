#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed audit trail guard for calculator input parameters.

Supported forms:
  {"Inputs": {"gamma_II": 18.5}, "Provenance": [{...record...}]}
  {"gamma_II": {"Value": 18.5, "Provenance": {...record...}}}
Nested parameters use exact paths (soil.layers[0].phi), never ambiguous leaf names.
Use require_provenance before calculation, or guarded_calculate to enforce it and
include function defaults in the audit. A CLI BLOCKED result exits with code 1.
Verified is an upstream attestation; this guard validates its schema and value
binding, not the truth of a document. Optional citation_auditor verifies standard
defaults against PDFs. It never promotes ENGINEER_ASSUMED to document evidence.
"""
import argparse
import inspect
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SOURCE_TYPES = {'DOCUMENT_EXTRACTED', 'STANDARDS_DEFAULT', 'ENGINEER_ASSUMED'}
FIELDS = {'Parameter', 'Value', 'Unit', 'Source_Type', 'Source_Ref', 'Verified'}
PLACEHOLDERS = {'', '?', '-', 'unknown', 'none', 'null', 'n/a', 'tbd', 'unverified', 'không rõ', 'khong ro'}
INPUT_KEYS = ('Inputs', 'inputs', 'Input_Data', 'input_data', 'Parameters', 'parameters')


class UnanchoredInputError(ValueError):
    def __init__(self, audit):
        self.audit = audit
        super().__init__('UNANCHORED_VALUES_BLOCKED: '+', '.join(e['Parameter'] for e in audit['violations']))


def _same_value(left, right):
    # bool is a subclass of int in Python but never a matching physical value.
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return not any(isinstance(v, float) and not math.isfinite(v) for v in (left, right)) and left == right
    return type(left) is type(right) and left == right


def _nonempty(value):
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def _extract_parameters(inputs):
    parameters, embedded = {}, []

    def walk(node, path):
        if isinstance(node, dict) and 'Value' in node:
            if not path:
                path = node.get('Parameter', '')
            parameters[path] = {'Value': node['Value'], 'Unit': node.get('Unit')}
            if 'Provenance' in node:
                embedded.append((path, node['Provenance']))
            for key, value in node.items():
                if key not in ('Value', 'Unit', 'Parameter', 'Provenance'):
                    walk(value, f'{path}.{key}' if path else key)
        elif isinstance(node, dict):
            if not node and path:
                parameters[path] = {'Value': node, 'Unit': None}
            for key, value in node.items():
                if not isinstance(key, str) or not key or any(c in key for c in '.[]'):
                    raise ValueError('Input keys must be nonempty names without path delimiters: '+str(key))
                if key != 'Provenance':
                    walk(value, f'{path}.{key}' if path else key)
                elif path:
                    raise ValueError('Nested Provenance must be attached to a Value wrapper: '+path)
        elif isinstance(node, list):
            if not node:
                parameters[path] = {'Value': node, 'Unit': None}
            for index, value in enumerate(node):
                walk(value, f'{path}[{index}]')
        else:
            parameters[path] = {'Value': node, 'Unit': None}

    walk(inputs, '')
    return parameters, embedded


def audit_inputs(data, provenance=None, *, required_parameters=None, citation_auditor=None):
    """Audit ALL leaves in an input mapping, not a whitelist of familiar load names.

    required_parameters adds missing-input checks; it never excludes other leaves.
    Flat mapping and explicit Inputs envelope are accepted. Calculator output logs
    are not guessed to be inputs: pass its actual input mapping explicitly.
    """
    if not isinstance(data, dict):
        raise ValueError('Calculator input must be a mapping or Inputs envelope')
    containers = [key for key in INPUT_KEYS if key in data]
    if len(containers) > 1:
        raise ValueError('Ambiguous input envelope: multiple input containers')
    inputs = data[containers[0]] if containers else {k: v for k, v in data.items() if k != 'Provenance'}
    if not isinstance(inputs, dict):
        raise ValueError('Input container must be a mapping')
    parameters, inline = _extract_parameters(inputs)
    records, violations = {}, []

    def violation(parameter, code, detail):
        violations.append({'Parameter': parameter, 'Code': code, 'Detail': detail})

    if containers:
        for key in data:
            if key not in (containers[0], 'Provenance'):
                violation(key, 'UNEXPECTED_INPUT_ENVELOPE_FIELD', 'Place every calculator parameter inside the input container')

    def register(record, expected=None):
        if not isinstance(record, dict):
            violation(expected or '$', 'INVALID_PROVENANCE', 'Provenance record must be an object')
            return
        name = record.get('Parameter')
        if not isinstance(name, str) or not name.strip():
            violation(expected or '$', 'MISSING_PARAMETER_NAME', 'Parameter must identify an exact input path')
            return
        if expected is not None and name != expected:
            violation(expected, 'PROVENANCE_PARAMETER_MISMATCH', f'Record identifies {name}')
        records.setdefault(name, []).append(record)

    global_records = provenance if provenance is not None else data.get('Provenance', [])
    if isinstance(global_records, dict):
        if 'Parameter' in global_records:
            register(global_records)
        else:
            # Keyed registry still requires an explicit Parameter; no inferred attestations.
            for name, record in global_records.items():
                register(record, name)
    elif isinstance(global_records, list):
        for record in global_records:
            register(record)
    else:
        violation('$', 'INVALID_PROVENANCE', 'Provenance registry must be an object or list')
    for path, record in inline:
        register(record, path)

    for name in required_parameters or []:
        if name not in parameters:
            violation(name, 'MISSING_INPUT', 'Required input parameter absent')
    if not parameters:
        violation('$', 'NO_INPUT_PARAMETERS', 'Empty input cannot pass the provenance gate')
    valid, assumptions = [], []
    for name, parameter in parameters.items():
        candidates = records.get(name, [])
        if not candidates:
            violation(name, 'UNANCHORED_VALUE', 'Missing Provenance record')
            continue
        if len(candidates) != 1:
            violation(name, 'DUPLICATE_PROVENANCE', 'Exactly one authoritative record is required')
            continue
        record = candidates[0]
        start = len(violations)
        missing = sorted(FIELDS-record.keys())
        if missing:
            violation(name, 'MISSING_PROVENANCE_FIELDS', ', '.join(missing))
        value = parameter['Value']
        if value is None or (isinstance(value, str) and not _nonempty(value)) or not isinstance(value, (str, int, float, bool)):
            violation(name, 'INVALID_INPUT_VALUE', 'Value must be a present scalar; annotate array elements separately')
        if not _same_value(value, record.get('Value')):
            violation(name, 'PROVENANCE_VALUE_MISMATCH', 'Attested value must equal the actual input, without coercion')
        if not _nonempty(record.get('Unit')):
            violation(name, 'MISSING_UNIT', 'Use an explicit unit, or 1 for dimensionless parameters')
        if parameter['Unit'] is not None and parameter['Unit'] != record.get('Unit'):
            violation(name, 'PROVENANCE_UNIT_MISMATCH', 'Input and attested units differ')
        if not isinstance(record.get('Source_Type'), str) or record.get('Source_Type') not in SOURCE_TYPES:
            violation(name, 'INVALID_SOURCE_TYPE', 'Source_Type must be one of the three allowed categories')
        if not _nonempty(record.get('Source_Ref')):
            violation(name, 'MISSING_SOURCE_REF', 'Provide document/page/table, standard citation, or engineer decision reference')
        if record.get('Verified') is not True:
            violation(name, 'UNVERIFIED_SOURCE', 'Verified must be the literal boolean true')
        if record.get('Source_Type') == 'ENGINEER_ASSUMED':
            assumptions.append(name)
        if record.get('Source_Type') == 'STANDARDS_DEFAULT' and citation_auditor is not None:
            citation = record.get('Citation', record.get('Source_Ref', ''))
            audited = citation_auditor.audit({'Citation': citation})
            if audited['status'] != 'PASS':
                violation(name, 'STANDARDS_DEFAULT_NOT_GROUNDED', 'Standard default citation failed the PDF grounding gate')
        if start == len(violations) and not any(v['Parameter'] == name for v in violations):
            valid.append(name)
    for name in records:
        if name not in parameters:
            violation(name, 'ORPHAN_PROVENANCE', 'Record has no matching input parameter')
    return {'status': 'BLOCKED' if violations else 'PASS', 'allowed': not violations,
            'total_parameters': len(parameters), 'anchored_parameters': len(valid),
            'coverage_percent': round(100*len(valid)/len(parameters), 2) if parameters else 0.0,
            'violations': violations, 'engineer_assumed_parameters': assumptions,
            'provenance': [record for group in records.values() for record in group],
            'verification_scope': 'Schema, exact input binding and upstream attestations' +
                ('; standard defaults grounded in local PDFs' if citation_auditor else '; document content not independently verified')}


def require_provenance(data, provenance=None, **kwargs):
    result = audit_inputs(data, provenance, **kwargs)
    if not result['allowed']:
        raise UnanchoredInputError(result)
    return result


def guarded_calculate(calculator, inputs, provenance=None, *, citation_auditor=None):
    """No calculator call occurs until all supplied AND defaulted parameters pass.

    inputs is the calculator's keyword argument mapping (plain scalar/nested values).
    Defaulted coefficients require explicit provenance too; *args/**kwargs are
    rejected because their input contract cannot be bound unambiguously here.
    """
    signature = inspect.signature(calculator)
    if any(p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD) for p in signature.parameters.values()):
        raise ValueError('Guarded calculators require an explicit parameter signature')
    bound = signature.bind(**inputs)
    bound.apply_defaults()
    require_provenance(dict(bound.arguments), provenance, citation_auditor=citation_auditor)
    return calculator(*bound.args, **bound.kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o')
    parser.add_argument('--verify-standard-citations', action='store_true')
    args = parser.parse_args(argv)
    try:
        def reject_constant(value):
            raise ValueError('Non-finite JSON input: '+value)
        data = json.loads(Path(args.input).resolve().read_text(encoding='utf-8-sig'), parse_constant=reject_constant)
        auditor = None
        if args.verify_standard_citations:
            from citation_grounding_auditor import CitationGroundingAuditor
            auditor = CitationGroundingAuditor()
        result = audit_inputs(data, citation_auditor=auditor)
        code = 0 if result['allowed'] else 1
    except Exception as error:
        result, code = {'status': 'ERROR', 'allowed': False, 'error': f'{type(error).__name__}: {error}'}, 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        target = Path(args.output).resolve()
        if target == Path(args.input).resolve():
            parser.error('Output must not overwrite the input')
        target.write_text(encoded, encoding='utf-8')
    print(encoded)
    return code


if __name__ == '__main__':
    sys.exit(main())
