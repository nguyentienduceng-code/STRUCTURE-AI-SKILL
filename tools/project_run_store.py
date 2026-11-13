#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Durable P1 checkpoints, fenced leases, content-addressed artifacts and events.

SQLite transactions are the authoritative event/checkpoint journal. JSONL is an
export, avoiding inconsistent dual writes. Use a local disk (default LocalAppData),
not a shared/synchronized SQLite database. No secrets are stored in this journal.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp.'+uuid.uuid4().hex)
    try:
        with temporary.open('xb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class RunBusy(RuntimeError):
    pass


class StaleLease(RuntimeError):
    pass


class IntegrityError(RuntimeError):
    pass


class ToolBudgetExceeded(RuntimeError):
    pass


class RunStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root/'runs.sqlite3'
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, spec TEXT NOT NULL, state TEXT NOT NULL,
                  owner TEXT, generation INTEGER NOT NULL DEFAULT 0, expires REAL NOT NULL DEFAULT 0,
                  tool_calls INTEGER NOT NULL DEFAULT 0, call_limit INTEGER NOT NULL,
                  review TEXT, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS stages (
                  run_id TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL,
                  attempts INTEGER NOT NULL, output TEXT, error TEXT,
                  PRIMARY KEY(run_id,name));
                CREATE TABLE IF NOT EXISTS tasks (
                  run_id TEXT NOT NULL, task_key TEXT NOT NULL, output TEXT NOT NULL,
                  PRIMARY KEY(run_id,task_key));
                CREATE TABLE IF NOT EXISTS events (
                  run_id TEXT NOT NULL, seq INTEGER NOT NULL, body TEXT NOT NULL,
                  previous TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(run_id,seq));
            ''')

    @contextmanager
    def _db(self, write=False):
        db = sqlite3.connect(self.database, timeout=20, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        try:
            if write:
                db.execute('BEGIN IMMEDIATE')
            yield db
            if write:
                db.commit()
        except BaseException:
            if write:
                db.rollback()
            raise
        finally:
            db.close()

    def directory(self, run_id):
        if not re.fullmatch(r'run_[0-9a-f]{24}', run_id):
            raise ValueError('Invalid run ID')
        path = (self.root/run_id).resolve()
        if not path.is_relative_to(self.root):
            raise IntegrityError('Run directory escaped storage root')
        return path

    def put_blob(self, run_id, value):
        data = encoded(value)
        key = hashlib.sha256(data).hexdigest()
        path = self.directory(run_id)/'blobs'/f'{key}.json'
        if not path.resolve().is_relative_to(self.directory(run_id)):
            raise IntegrityError('Artifact directory escaped run scope')
        if path.exists():
            if file_hash(path) != key:
                raise IntegrityError('Immutable artifact was modified: '+key)
        else:
            atomic_write(path, data)
        return key

    def blob(self, run_id, key):
        if not isinstance(key, str) or not re.fullmatch(r'[0-9a-f]{64}', key):
            raise IntegrityError('Invalid artifact identity')
        path = (self.directory(run_id)/'blobs'/f'{key}.json').resolve()
        if not path.is_relative_to(self.directory(run_id)) or not path.is_file() or file_hash(path) != key:
            raise IntegrityError('Missing or modified artifact: '+key)
        return json.loads(path.read_text(encoding='utf-8'))

    @staticmethod
    def _event(db, run_id, kind, actor, details):
        last = db.execute('SELECT seq,hash FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1', (run_id,)).fetchone()
        previous = last['hash'] if last else '0'*64
        seq = last['seq']+1 if last else 1
        body = {'seq': seq, 'kind': kind, 'actor': actor, 'at': time.time(), 'details': details}
        key = digest({'previous': previous, 'event': body})
        db.execute('INSERT INTO events VALUES(?,?,?,?,?)', (run_id, seq, encoded(body).decode(), previous, key))

    def create(self, run_id, spec, call_limit):
        value = encoded(spec).decode()
        with self._db(True) as db:
            row = db.execute('SELECT spec FROM runs WHERE id=?', (run_id,)).fetchone()
            if row:
                if row['spec'] != value:
                    raise IntegrityError('Run-ID collision or modified manifest')
                return False
            db.execute('INSERT INTO runs(id,spec,state,call_limit,created) VALUES(?,?,?,?,?)',
                       (run_id, value, 'RECEIVED', call_limit, time.time()))
            self._event(db, run_id, 'RUN_CREATED', 'orchestrator', {'spec_hash': digest(spec)})
        return True

    def get(self, run_id):
        self.directory(run_id)
        with self._db() as db:
            row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
            if not row:
                raise KeyError('Unknown run')
            result = dict(row)
            result['spec'] = json.loads(result['spec'])
            if run_id != 'run_'+digest(result['spec'])[:24]:
                raise IntegrityError('Stored run manifest no longer matches its run ID')
            result['review'] = json.loads(result['review']) if result['review'] else None
            result['stages'] = {r['name']: dict(r) for r in db.execute('SELECT * FROM stages WHERE run_id=?', (run_id,))}
        return result

    @staticmethod
    def _fence(db, run_id, owner, generation):
        row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row or row['owner'] != owner or row['generation'] != generation or row['expires'] <= time.time():
            raise StaleLease('Lost/expired run ownership; stale workers cannot commit')
        return row

    def acquire(self, run_id, ttl=30.):
        if type(ttl) not in (int, float) or not math.isfinite(ttl) or not .01 <= ttl <= 3600:
            raise ValueError('Lease TTL must be finite in [.01,3600]')
        owner = uuid.uuid4().hex
        with self._db(True) as db:
            row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
            if not row:
                raise KeyError(run_id)
            if row['owner'] and row['expires'] > time.time():
                raise RunBusy('Run already owned by a live executor')
            generation = row['generation']+1
            db.execute('UPDATE runs SET owner=?,generation=?,expires=? WHERE id=?', (owner, generation, time.time()+ttl, run_id))
            self._event(db, run_id, 'LEASE_ACQUIRED', 'orchestrator', {'generation': generation})
        return owner, generation

    def renew(self, run_id, owner, generation, ttl=30.):
        if type(ttl) not in (int, float) or not math.isfinite(ttl) or not .01 <= ttl <= 3600:
            raise ValueError('Lease TTL must be finite in [.01,3600]')
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            db.execute('UPDATE runs SET expires=? WHERE id=?', (time.time()+ttl, run_id))

    def release(self, run_id, owner, generation):
        with self._db(True) as db:
            row = db.execute('SELECT owner,generation FROM runs WHERE id=?', (run_id,)).fetchone()
            if row and row['owner'] == owner and row['generation'] == generation:
                db.execute('UPDATE runs SET owner=NULL,expires=0 WHERE id=?', (run_id,))

    def state(self, run_id, owner, generation, state, details=None):
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            db.execute('UPDATE runs SET state=? WHERE id=?', (state, run_id))
            self._event(db, run_id, 'RUN_STATE', 'orchestrator', {'state': state, **(details or {})})

    def start_stage(self, run_id, owner, generation, name, max_attempts):
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            row = db.execute('SELECT * FROM stages WHERE run_id=? AND name=?', (run_id, name)).fetchone()
            if row and row['status'] == 'SUCCESS':
                return False
            attempts = row['attempts']+1 if row else 1
            if attempts > max_attempts:
                raise RuntimeError('STAGE_RETRY_LIMIT:'+name)
            db.execute('INSERT INTO stages VALUES(?,?,?,?,NULL,NULL) ON CONFLICT(run_id,name) DO UPDATE SET '
                       'status=excluded.status,attempts=excluded.attempts,output=NULL,error=NULL',
                       (run_id, name, 'RUNNING', attempts))
            self._event(db, run_id, 'STAGE_STARTED', name, {'attempt': attempts})
        return True

    def finish_stage(self, run_id, owner, generation, name, output=None, error=None):
        if output:
            self.blob(run_id, output)
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            db.execute('UPDATE stages SET status=?,output=?,error=? WHERE run_id=? AND name=?',
                       ('FAILED' if error else 'SUCCESS', output, error, run_id, name))
            self._event(db, run_id, 'STAGE_FAILED' if error else 'STAGE_COMPLETED', name, {'output': output, 'error': error})

    def admit(self, run_id, owner, generation, principal, tool):
        with self._db(True) as db:
            row = self._fence(db, run_id, owner, generation)
            if row['tool_calls'] >= row['call_limit']:
                raise ToolBudgetExceeded('Persistent tool-call budget exhausted')
            db.execute('UPDATE runs SET tool_calls=tool_calls+1 WHERE id=?', (run_id,))
            self._event(db, run_id, 'TOOL_ADMITTED', principal.actor, {'role': principal.role, 'tool': tool})

    def cached_task(self, run_id, owner, generation, key):
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            row = db.execute('SELECT output FROM tasks WHERE run_id=? AND task_key=?', (run_id, key)).fetchone()
            if row:
                self._event(db, run_id, 'CASE_CACHE_HIT', 'calculation-agent', {'task_key': key, 'output': row['output']})
        return self.blob(run_id, row['output']) if row else None

    def commit_task(self, run_id, owner, generation, key, value):
        output = self.put_blob(run_id, value)
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            previous = db.execute('SELECT output FROM tasks WHERE run_id=? AND task_key=?', (run_id, key)).fetchone()
            if previous and previous['output'] != output:
                raise IntegrityError('A deterministic case changed for the same inputs/runtime')
            db.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?)', (run_id, key, output))
            self._event(db, run_id, 'CASE_COMPLETED', 'calculation-agent', {'task_key': key, 'output': output})
        return value

    def review(self, run_id, owner, generation, receipt, approved):
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            db.execute('UPDATE runs SET review=?,state=? WHERE id=?',
                       (encoded(receipt).decode(), 'APPROVED' if approved else 'REJECTED', run_id))
            self._event(db, run_id, 'REVIEW_APPROVED' if approved else 'REVIEW_REJECTED', receipt['reviewer'],
                        {'draft': receipt['draft_hash'], 'decision': receipt['decision']})

    def extend_budget(self, run_id, owner, generation, additional, reviewer):
        with self._db(True) as db:
            self._fence(db, run_id, owner, generation)
            db.execute('UPDATE runs SET call_limit=call_limit+? WHERE id=?', (additional, run_id))
            self._event(db, run_id, 'BUDGET_EXTENDED', reviewer, {'additional_calls': additional})

    def events(self, run_id):
        with self._db() as db:
            rows = list(db.execute('SELECT * FROM events WHERE run_id=? ORDER BY seq', (run_id,)))
        previous = '0'*64
        result = []
        for seq, row in enumerate(rows, 1):
            body = json.loads(row['body'])
            if row['seq'] != seq or body.get('seq') != seq or row['previous'] != previous or digest({'previous': previous, 'event': body}) != row['hash']:
                raise IntegrityError('Event journal integrity check failed')
            result.append({**body, 'previous_hash': previous, 'event_hash': row['hash']})
            previous = row['hash']
        return result

    def export_events(self, run_id):
        data = b''.join(encoded(event)+b'\n' for event in self.events(run_id))
        path = self.directory(run_id)/'events.jsonl'
        atomic_write(path, data)
        return path
