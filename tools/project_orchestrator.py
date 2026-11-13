#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 durable project workflow and operator-gated publication.

Receive -> validate -> bind -> calculate -> independent verify -> draft ->
AWAITING_REVIEW -> APPROVED/REJECTED -> PUBLISHED.

CLI examples (all paths may be absolute):
  --create MANIFEST.json [--run]        freeze inputs and run to a reviewable draft
  --resume RUN_ID                       resume committed stages/cases
  --status RUN_ID                       inspect state without executing tools
  --approve RUN_ID --draft-hash SHA --reviewer NAME
  --reject RUN_ID --draft-hash SHA --reviewer NAME --reason TEXT
  --publish RUN_ID                      publish exactly the approved draft
Operator actions require ENGINEERING_OPERATOR_TOKEN in the trusted host env.
Worker subprocesses never receive that credential. No LLM/network tools are
registered. Role checks protect this broker boundary, not arbitrary hostile
Python with the operating-system user's filesystem privileges.
"""
import argparse
import csv
import hashlib
import hmac
import importlib.metadata
import io
import json
import math
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from agent_permissions import ROLE_ACTORS, STAGES
from project_run_store import (RunStore, RunBusy, StaleLease, IntegrityError, ToolBudgetExceeded,
                               encoded, digest, file_hash, atomic_write)

TOOLS = Path(__file__).resolve().parent
AGENTS = TOOLS.parent
sys.path.insert(0, str(AGENTS/'skills/Global_Dispatcher/scripts'))
from pipeline_builder import PipelineBuilder

MANIFEST_KEYS = frozenset({'sources', 'conventions', 'solver_options', 'stories',
                          'coordinate_tolerance_mm', 'label_tolerance_mm', 'coordinate_mode'})


class WorkerFailure(RuntimeError):
    def __init__(self, message, error_type='WorkerFailure'):
        self.error_type = error_type
        super().__init__(message)


def runtime_fingerprint():
    paths = [TOOLS/name for name in ('project_orchestrator.py', 'project_orchestrator_worker.py',
        'project_run_store.py', 'agent_permissions.py', 'project_independent_verifier.py',
        'project_data_pipeline.py', 'doc_reader.py', 'citation_grounding_auditor.py', 'pdf_text_index.py',
        'input_provenance_guard.py', 'policy_engine.py', 'system_controller.py')]
    paths += [AGENTS/'skills/Structural_Design_Engineer/scripts/calc_rc_section_pm_3d.py',
              AGENTS/'skills/Global_Dispatcher/scripts/pipeline_builder.py', AGENTS/'skills/STANDARDS_LOCK.md']
    paths += sorted((AGENTS/'skills/Global_Dispatcher').glob('config/*.json'))
    paths += sorted((AGENTS/'skills/Design_Evaluation/standards/TCVN').glob('*5574*2018*.pdf'))
    return {'python': sys.version, 'platform': platform.platform(),
            'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'openpyxl', 'ezdxf', 'PyMuPDF')},
            'files': {str(path.relative_to(AGENTS)): file_hash(path) for path in paths}}


def _read_json(path):
    def invalid(value):
        raise ValueError('Non-finite JSON: '+value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=invalid)


def _valid_int(name, value, lower=1, upper=1000000):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f'{name} must be an integer in [{lower},{upper}]')
    return value


class ProjectOrchestrator:
    def __init__(self, storage_root=None, *, operator_token=None):
        default = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.cache')))/'EngineeringAgent/project_runs'
        self.store = RunStore(storage_root or default)
        self._operator_token = operator_token if operator_token is not None else os.environ.get('ENGINEERING_OPERATOR_TOKEN')
        # Reuse the existing DAG builder/scheduler rather than inventing another DAG contract.
        plan = PipelineBuilder().build_dag([
            {'skill': definition[3], 'depends_on': [i] if i else []} for i, definition in enumerate(STAGES)])
        # The legacy plan includes wall-clock IDs/timestamps. They are not DAG
        # semantics and must not invalidate restart/idempotency fingerprints.
        self.plan = {key: plan[key] for key in ('schema_version', 'graph_type', 'stages', 'edges',
                                              'topological_order', 'execution_batches')}

    def create_run(self, manifest, *, stage_timeout_s=120., max_tool_calls=10000, max_stage_attempts=3):
        base = Path.cwd()
        if isinstance(manifest, (str, Path)):
            path = Path(manifest).resolve()
            base, manifest = path.parent, _read_json(path)
        if not isinstance(manifest, dict) or set(manifest)-MANIFEST_KEYS:
            raise ValueError('Manifest may contain data/settings only; roles, tools, commands and approvals are host policy')
        if type(stage_timeout_s) not in (int, float) or not math.isfinite(stage_timeout_s) or not .05 <= stage_timeout_s <= 3600:
            raise ValueError('stage_timeout_s must be finite in [.05,3600]')
        _valid_int('max_tool_calls', max_tool_calls)
        _valid_int('max_stage_attempts', max_stage_attempts, 1, 10)
        sources = manifest.get('sources')
        if isinstance(sources, (str, Path, dict)):
            sources = [sources]
        if not isinstance(sources, list) or not sources:
            raise ValueError('At least one source is required')
        descriptors = []
        from project_orchestrator_worker import reader_fingerprint
        for index, source in enumerate(sources):
            story, expected = None, None
            if isinstance(source, dict) and 'source' in source and 'metadata' not in source:
                if set(source)-{'source', 'story'} or not isinstance(source.get('story'), str) or not source['story'].strip():
                    raise ValueError('Invalid source story context')
                story, source = source['story'], source['source']
            if isinstance(source, (str, Path)):
                path = (base/Path(source)).resolve()
                if path.suffix.lower() == '.json':
                    source = _read_json(path)
                else:
                    source = None
            if isinstance(source, dict):
                if source.get('status') not in ('OK', 'PARTIAL') or not source.get('metadata', {}).get('source_path'):
                    raise ValueError('Reader result requires an accessible original for durable verification')
                path = (base/Path(source['metadata']['source_path'])).resolve()
                expected = reader_fingerprint(source)
                declared_story = source['metadata'].get('story')
                if story and declared_story and story != declared_story:
                    raise ValueError('Conflicting source story context')
                story = story or declared_story
            if not path.is_file():
                raise FileNotFoundError('Original source unavailable: '+str(path))
            if path.suffix.lower() not in ('.dwg', '.dxf', '.xlsx', '.xls', '.csv', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.tif', '.tiff'):
                raise ValueError('Unsupported original source format')
            descriptors.append({'original_path': str(path), 'name': path.name, 'sha256': file_hash(path),
                'snapshot': f'inputs/{index}/{path.name}', 'story': story, 'reader_expectation': expected})
        spec = {'schema_version': 'project.run.v1', 'sources': descriptors,
                'parameters': {key: value for key, value in manifest.items() if key != 'sources'},
                'runtime': runtime_fingerprint(), 'dag': self.plan,
                'settings': {'stage_timeout_s': float(stage_timeout_s), 'max_tool_calls': max_tool_calls,
                             'max_stage_attempts': max_stage_attempts}}
        run_id = 'run_'+digest(spec)[:24]
        # Freeze exact input versions before registering the run. Partial copies are never usable.
        for source in descriptors:
            target = (self.store.directory(run_id)/source['snapshot']).resolve()
            if not target.is_relative_to(self.store.directory(run_id)):
                raise IntegrityError('Snapshot path escaped run directory')
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if file_hash(target) != source['sha256']:
                    raise IntegrityError('Immutable input snapshot was modified')
                continue
            temporary = target.with_name(target.name+'.tmp.'+uuid.uuid4().hex)
            try:
                shutil.copyfile(source['original_path'], temporary)
                if file_hash(temporary) != source['sha256']:
                    raise IntegrityError('Source changed while snapshotting')
                with temporary.open('r+b') as handle:
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        self.store.create(run_id, spec, max_tool_calls)
        return run_id

    def _check_versions(self, run):
        if runtime_fingerprint() != run['spec']['runtime'] or self.plan != run['spec']['dag']:
            raise IntegrityError('RUNTIME_CHANGED: create a new run for changed code, standards, material profiles or environment')
        from project_orchestrator_worker import validate_snapshot
        validate_snapshot(self.store, run['id'], run['spec'])
        self.store.events(run['id'])
        for stage in run['stages'].values():
            if stage['status'] == 'SUCCESS':
                self.store.blob(run['id'], stage['output'])

    @staticmethod
    def _kill_worker(process):
        if process.poll() is not None:
            return
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        process.wait(timeout=15)

    def _worker(self, run_id, owner, generation, stage, payload, timeout):
        folder = self.store.directory(run_id)/'attempts'/f'{stage}-{uuid.uuid4().hex}'
        folder.mkdir(parents=True)
        request, response = folder/'request.json', folder/'response.json'
        atomic_write(request, encoded({'store_root': str(self.store.root), 'run_id': run_id, 'owner': owner,
                                      'generation': generation, 'stage': stage, 'payload': payload}))
        env = dict(os.environ)
        env.pop('ENGINEERING_OPERATOR_TOKEN', None)
        env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(folder/'pycache'),
                   OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
        with (folder/'stdout.log').open('wb') as stdout, (folder/'stderr.log').open('wb') as stderr:
            process = subprocess.Popen([sys.executable, str(TOOLS/'project_orchestrator_worker.py'),
                '--request', str(request), '--response', str(response)], stdout=stdout, stderr=stderr, env=env, **flags)
            deadline, heartbeat = time.monotonic()+timeout, time.monotonic()
            try:
                while process.poll() is None:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Worker hard timeout: '+stage)
                    if time.monotonic() >= heartbeat:
                        self.store.renew(run_id, owner, generation)
                        heartbeat = time.monotonic()+1.
                    time.sleep(.05)
            except BaseException:
                self._kill_worker(process)
                raise
        if not response.is_file():
            raise WorkerFailure(f'Worker exited {process.returncode} without a response; see {folder}')
        value = _read_json(response)
        if process.returncode or not value.get('ok'):
            raise WorkerFailure(value.get('error', 'Worker failed'), value.get('error_type', 'WorkerFailure'))
        return value['result']

    def run(self, run_id, *, stop_after=None):
        if stop_after is not None and stop_after not in {stage[0] for stage in STAGES}:
            raise ValueError('Unknown checkpoint stage')
        run = self.store.get(run_id)
        self._check_versions(run)
        if run['state'] in ('AWAITING_REVIEW', 'APPROVED', 'REJECTED', 'VERIFICATION_BLOCKED', 'DATA_BLOCKED', 'PUBLISHED'):
            return self.status(run_id)
        owner, generation = self.store.acquire(run_id)
        try:
            while True:
                run = self.store.get(run_id)
                states = {index+1: 'SUCCESS' for index, definition in enumerate(STAGES)
                          if run['stages'].get(definition[0], {}).get('status') == 'SUCCESS'}
                ready = PipelineBuilder.ready_stages(self.plan, states)['ready']
                if not ready:
                    self.store.state(run_id, owner, generation, 'AWAITING_REVIEW')
                    break
                index = ready[0]-1
                stage, role, _, _ = STAGES[index]
                self._check_versions(run)
                self.store.start_stage(run_id, owner, generation, stage, run['spec']['settings']['max_stage_attempts'])
                self.store.state(run_id, owner, generation, stage.upper())
                payload = {}
                if index:
                    payload = {'input_hash': run['stages'][STAGES[index-1][0]]['output']}
                if stage == 'draft':
                    payload = {'calculation_hash': run['stages']['calculate']['output'],
                               'verification_hash': run['stages']['verify']['output']}
                try:
                    output = self._worker(run_id, owner, generation, stage, payload,
                                          run['spec']['settings']['stage_timeout_s'])
                    key = self.store.put_blob(run_id, output)
                    self.store.finish_stage(run_id, owner, generation, stage, output=key)
                    if stage == 'verify' and output.get('verified') is not True:
                        self.store.state(run_id, owner, generation, 'VERIFICATION_BLOCKED', {'errors': output.get('errors')})
                        break
                    if stop_after == stage:
                        self.store.state(run_id, owner, generation, 'CHECKPOINTED')
                        break
                except (WorkerFailure, TimeoutError, ValueError) as error:
                    self.store.finish_stage(run_id, owner, generation, stage, error=str(error))
                    error_type = getattr(error, 'error_type', type(error).__name__)
                    state = ('BUDGET_EXHAUSTED' if error_type == 'ToolBudgetExceeded' else
                             'TIMED_OUT' if isinstance(error, TimeoutError) else
                             'DATA_BLOCKED' if error_type in ('ValueError', 'PipelineDataError', 'CapabilityDenied', 'IntegrityError') else 'FAILED')
                    self.store.state(run_id, owner, generation, state, {'error': str(error)})
                    break
        finally:
            self.store.release(run_id, owner, generation)
            self.store.export_events(run_id)
        return self.status(run_id)

    def status(self, run_id):
        run = self.store.get(run_id)
        draft = run['stages'].get('draft', {}).get('output')
        if run['state'] == 'PUBLISHED':
            files = self._render_publication(run)
            destination = self.store.directory(run_id)/'published'
            if not destination.is_dir() or {p.name for p in destination.iterdir()} != set(files) or any(
                    not (destination/name).is_file() or (destination/name).read_bytes() != value for name, value in files.items()):
                raise IntegrityError('Published files no longer match the reviewed draft')
        return {'run_id': run_id, 'state': run['state'], 'tool_calls': run['tool_calls'], 'call_limit': run['call_limit'],
                'stages': {name: {key: value for key, value in stage.items() if key not in ('run_id', 'name')}
                           for name, stage in run['stages'].items()},
                'draft_hash': draft,
                'draft_path': str(self.store.directory(run_id)/'blobs'/f'{draft}.json') if draft else None,
                'published_path': str(self.store.directory(run_id)/'published') if run['state'] == 'PUBLISHED' else None,
                'requires_operator_review': run['state'] == 'AWAITING_REVIEW'}

    def _authenticate(self, supplied):
        if not isinstance(self._operator_token, str) or len(self._operator_token) < 24 or not isinstance(supplied, str) or not hmac.compare_digest(self._operator_token, supplied):
            raise PermissionError('Authenticated operator credential required; agents cannot approve or publish')

    def _sign(self, receipt):
        return hmac.new(self._operator_token.encode(), encoded(receipt), hashlib.sha256).hexdigest()

    def review(self, run_id, *, expected_draft_hash, reviewer, operator_token, decision='APPROVE', reason=''):
        self._authenticate(operator_token)
        if decision not in ('APPROVE', 'REJECT') or not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError('Explicit reviewer and APPROVE/REJECT decision required')
        if reviewer in ROLE_ACTORS.values():
            raise PermissionError('A built-in agent cannot attest engineer review')
        if decision == 'REJECT' and not reason.strip():
            raise ValueError('Rejection requires a reason')
        run = self.store.get(run_id)
        self._check_versions(run)
        if run['state'] != 'AWAITING_REVIEW':
            raise ValueError('Run is not awaiting a concrete draft review')
        if expected_draft_hash != run['stages']['draft']['output']:
            raise IntegrityError('Approval refers to a different draft')
        verification = self.store.blob(run_id, run['stages']['verify']['output'])
        if verification.get('verified') is not True:
            raise IntegrityError('Independent verification is not satisfied')
        owner, generation = self.store.acquire(run_id)
        try:
            current = self.store.get(run_id)
            if current['state'] != 'AWAITING_REVIEW' or current['stages']['draft']['output'] != expected_draft_hash:
                raise IntegrityError('Run/draft changed before the review lease was acquired')
            receipt = {'run_id': run_id, 'draft_hash': expected_draft_hash,
                'calculation_hash': run['stages']['calculate']['output'], 'verification_hash': run['stages']['verify']['output'],
                'runtime_hash': digest(run['spec']['runtime']), 'decision': decision, 'reviewer': reviewer.strip(),
                'reason': reason, 'at': time.time(), 'kind': 'AUTHENTICATED_OPERATOR_ATTESTATION'}
            receipt['signature'] = self._sign(receipt)
            self.store.review(run_id, owner, generation, receipt, decision == 'APPROVE')
        finally:
            self.store.release(run_id, owner, generation)
            self.store.export_events(run_id)
        return self.status(run_id)

    def extend_budget(self, run_id, additional_calls, *, reviewer, operator_token):
        self._authenticate(operator_token)
        _valid_int('additional_calls', additional_calls)
        if not reviewer or reviewer in ROLE_ACTORS.values():
            raise PermissionError('Operator identity required')
        run = self.store.get(run_id)
        if run['state'] != 'BUDGET_EXHAUSTED':
            raise ValueError('Budget extension is only applicable to an exhausted run')
        owner, generation = self.store.acquire(run_id)
        try:
            if self.store.get(run_id)['state'] != 'BUDGET_EXHAUSTED':
                raise ValueError('Run state changed before budget authorization')
            self.store.extend_budget(run_id, owner, generation, additional_calls, reviewer)
        finally:
            self.store.release(run_id, owner, generation)
        return self.status(run_id)

    def _publication_payload(self, run):
        receipt = dict(run['review'] or {})
        signature = receipt.pop('signature', '')
        if not isinstance(signature, str) or not hmac.compare_digest(signature, self._sign(receipt)):
            raise IntegrityError('Missing or modified operator review receipt')
        if receipt.get('decision') != 'APPROVE' or receipt.get('run_id') != run['id'] or receipt.get('draft_hash') != run['stages']['draft']['output'] or receipt.get('runtime_hash') != digest(run['spec']['runtime']):
            raise IntegrityError('Review receipt does not authorize this exact run/draft/runtime')
        if receipt.get('calculation_hash') != run['stages']['calculate']['output'] or receipt.get('verification_hash') != run['stages']['verify']['output']:
            raise IntegrityError('Calculation or verification changed after review')
        return self._render_publication(run)

    def _render_publication(self, run):
        receipt = run.get('review')
        if not receipt or receipt.get('decision') != 'APPROVE' or receipt.get('draft_hash') != run['stages']['draft']['output']:
            raise IntegrityError('Publication has no matching review receipt')
        signature = receipt['signature']
        draft = self.store.blob(run['id'], receipt['draft_hash'])
        report = dict(draft, approval_status='APPROVED_FOR_PUBLICATION', engineer_review=run['review'])
        csv_stream = io.StringIO(newline='')
        writer = csv.writer(csv_stream)
        writer.writerow(draft['summary_table']['headers'])
        for row in draft['summary_table']['rows']:
            # Document text cannot inject a spreadsheet formula in exported cells.
            writer.writerow(["'"+value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value for value in row])
        files = {'report.json': encoded(report), 'schedule.csv': csv_stream.getvalue().encode('utf-8-sig')}
        manifest = {'run_id': run['id'], 'draft_hash': receipt['draft_hash'], 'review_signature': signature,
                    'files': {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}}
        files['publication_receipt.json'] = encoded(manifest)
        return files

    def publish(self, run_id, *, operator_token):
        self._authenticate(operator_token)
        run = self.store.get(run_id)
        self._check_versions(run)
        if run['state'] not in ('APPROVED', 'PUBLISHING', 'PUBLISHED'):
            raise PermissionError('Publication requires approval of the exact concrete draft')
        files = self._publication_payload(run)
        owner, generation = self.store.acquire(run_id)
        try:
            destination = self.store.directory(run_id)/'published'
            if destination.exists():
                if {p.name for p in destination.iterdir()} != set(files) or any(not (destination/name).is_file() or (destination/name).read_bytes() != value for name, value in files.items()):
                    raise IntegrityError('Existing publication differs from the approved artifacts')
            else:
                self.store.state(run_id, owner, generation, 'PUBLISHING')
                staging = self.store.directory(run_id)/('publication.tmp.'+uuid.uuid4().hex)
                staging.mkdir()
                for name, value in files.items():
                    atomic_write(staging/name, value)
                os.replace(staging, destination)
            if run['state'] != 'PUBLISHED':
                self.store.state(run_id, owner, generation, 'PUBLISHED', {'files': list(files)})
        finally:
            self.store.release(run_id, owner, generation)
            self.store.export_events(run_id)
        return self.status(run_id)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ('create', 'resume', 'status', 'approve', 'reject', 'publish'):
        action.add_argument('--'+name)
    parser.add_argument('--store-root')
    parser.add_argument('--run', action='store_true', help='Run a newly created job to a reviewable draft')
    parser.add_argument('--draft-hash')
    parser.add_argument('--reviewer')
    parser.add_argument('--reason', default='')
    args = parser.parse_args(argv)
    runner = ProjectOrchestrator(args.store_root)
    try:
        if args.create:
            run_id = runner.create_run(args.create)
            result = runner.run(run_id) if args.run else runner.status(run_id)
        elif args.resume:
            result = runner.run(args.resume)
        elif args.status:
            result = runner.status(args.status)
        elif args.approve or args.reject:
            result = runner.review(args.approve or args.reject, expected_draft_hash=args.draft_hash,
                reviewer=args.reviewer, reason=args.reason, decision='APPROVE' if args.approve else 'REJECT',
                operator_token=os.environ.get('ENGINEERING_OPERATOR_TOKEN'))
        else:
            result = runner.publish(args.publish, operator_token=os.environ.get('ENGINEERING_OPERATOR_TOKEN'))
        code = 0 if result['state'] in ('RECEIVED', 'CHECKPOINTED', 'AWAITING_REVIEW', 'APPROVED', 'REJECTED', 'PUBLISHED') else 1
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        result, code = {'state': 'ERROR', 'error_type': type(error).__name__, 'error': str(error)}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
