#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixed P1 worker entrypoint; tool/role selection is host policy, never document text."""
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from agent_permissions import AgentPrincipal, AgentToolBroker, ROLE_ACTORS, STAGES
from project_run_store import RunStore, atomic_write, encoded, digest, file_hash, ToolBudgetExceeded


def reader_fingerprint(document):
    metadata = document.get('metadata', {})
    return digest({'file_type': document.get('file_type'), 'tables': document.get('tables'),
        'columns': document.get('engineering_entities', {}).get('columns'),
        'text_entities': metadata.get('text_entities'), 'drawing_units_code': metadata.get('drawing_units_code'),
        'coordinate_system': metadata.get('coordinate_system')})


def validate_snapshot(store, run_id, spec):
    sources, expectations = [], []
    for source in spec['sources']:
        path = (store.directory(run_id)/source['snapshot']).resolve()
        if not path.is_relative_to(store.directory(run_id)) or not path.is_file() or file_hash(path) != source['sha256']:
            raise ValueError('INPUT_SNAPSHOT_MISSING_OR_MODIFIED')
        item = {'source': str(path), 'story': source['story']} if source.get('story') else str(path)
        sources.append(item)
        if source.get('reader_expectation'):
            expectations.append({'source_index': len(sources)-1, 'fingerprint': source['reader_expectation']})
    manifest = dict(spec['parameters'], sources=sources)
    return {'manifest': manifest, 'reader_expectations': expectations, 'runtime_hash': digest(spec['runtime'])}


def execute_request(request):
    store, run_id = RunStore(request['store_root']), request['run_id']
    owner, generation = request['owner'], request['generation']
    definition = next((stage for stage in STAGES if stage[0] == request['stage']), None)
    if definition is None:
        raise ValueError('Unknown stage')
    stage, role, tool, _ = definition
    principal = AgentPrincipal(role, ROLE_ACTORS[role])
    spec = store.get(run_id)['spec']

    def load_input(payload):
        return store.blob(run_id, payload['input_hash'])

    def validate(payload):
        if payload:
            raise ValueError('Validation has no document-supplied controls')
        return validate_snapshot(store, run_id, spec)

    def bind(payload):
        from project_data_pipeline import prepare_project_pipeline
        validated = load_input(payload)
        prepared = prepare_project_pipeline(**validated['manifest'])
        for expected in validated['reader_expectations']:
            if reader_fingerprint(prepared['documents'][expected['source_index']]) != expected['fingerprint']:
                raise ValueError('STALE_OR_MODIFIED_READER_ASSERTION')
        return prepared

    def solve_case(payload):
        from calc_rc_section_pm_3d import calc_rc_section_pm_3d
        kwargs = payload['inputs']
        key = digest({'solver': 'rc_pm_3d', 'runtime': digest(spec['runtime']), 'inputs': kwargs})
        cached = store.cached_task(run_id, owner, generation, key)
        if cached is not None:
            return cached
        value = calc_rc_section_pm_3d(**kwargs)
        return store.commit_task(run_id, owner, generation, key, value)

    def calculate(payload):
        from project_data_pipeline import calculate_prepared_project
        prepared = load_input(payload)
        return calculate_prepared_project(prepared,
            calculation_executor=lambda **kwargs: broker.invoke('solver.rc_pm_3d', {'inputs': kwargs}))

    def verify(payload):
        from project_independent_verifier import verify_project_results
        return verify_project_results(load_input(payload))

    def draft(payload):
        calculation = store.blob(run_id, payload['calculation_hash'])
        verification = store.blob(run_id, payload['verification_hash'])
        if verification.get('verified') is not True:
            raise ValueError('Independent verification gate is not satisfied')
        return {'schema_version': 'project.review-draft.v1', 'run_id': run_id,
                'calculation_hash': payload['calculation_hash'], 'verification_hash': payload['verification_hash'],
                'runtime_hash': digest(spec['runtime']), 'approval_status': 'PENDING_HUMAN_REVIEW',
                'all_sections_passed': calculation['all_passed'], 'counts': calculation['counts'],
                'schedule': calculation['schedule'], 'summary_table': calculation['summary_table'],
                'verification_scope': verification['scope'], 'Scope_Limitation': calculation['Scope_Limitation'],
                'review_note': 'Engineer review must cover applicability, load combinations and member effects before publication.'}

    handlers = {'project.validate': validate, 'project.bind': bind, 'project.calculate': calculate,
                'solver.rc_pm_3d': solve_case, 'section.verify': verify, 'report.draft': draft}
    broker = AgentToolBroker(principal, handlers,
        on_admit=lambda actor, name: store.admit(run_id, owner, generation, actor, name))
    return broker.invoke(tool, request['payload'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--response', required=True)
    args = parser.parse_args(argv)
    try:
        request = json.loads(Path(args.request).read_text(encoding='utf-8'))
        result = {'ok': True, 'result': execute_request(request)}
        code = 0
    except Exception as error:
        result = {'ok': False, 'error_type': type(error).__name__, 'error': str(error)}
        code = 1
    atomic_write(Path(args.response), encoded(result))
    return code


if __name__ == '__main__':
    sys.exit(main())
