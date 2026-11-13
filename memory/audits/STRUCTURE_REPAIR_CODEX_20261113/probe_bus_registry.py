"""Audit ownership on an isolated bus; never mutate the live handoff."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
AGENTS = OUT.parents[2]
sys.path.insert(0, str(AGENTS/'tools'))
import sync_bus as bus

report = {}
original = json.loads((AGENTS/'memory/DUAL_AGENT_BUS.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='bus_independent_audit_') as temporary:
    root = Path(temporary)
    bus.BUS_PATH, bus.MEMO_PATH, bus.LOCK_PATH = root/'bus.json', root/'memo.md', root/'local.lock'
    original.update(handoff_status='IN_PROGRESS', current_holder='CODEX')
    bus.BUS_PATH.write_text(json.dumps(original), encoding='utf-8')
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        try:
            bus.claim_task('GEMINI')
            denied = False
        except Exception as error:
            denied = True
    after = json.loads(bus.BUS_PATH.read_text(encoding='utf-8'))
    report['ownership_probe'] = {'initial_holder': 'CODEX', 'attempted_claim': 'GEMINI',
        'claim_rejected': denied, 'final_holder': after['current_holder'],
        'ownership_preserved': after['current_holder'] == 'CODEX', 'isolated_test': True,
        'stdout': stream.getvalue()}

path = AGENTS/'skills/Design_Evaluation/scripts/validate_registry.py'
spec = importlib.util.spec_from_file_location('independent_registry', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stream = io.StringIO()
with contextlib.redirect_stdout(stream):
    registry = module.load_registry()
    issues, warnings = module.validate_scripts(registry)
    issues += module.validate_structure(registry)
    issues += module.validate_cad_integration(registry)
report['registry'] = {'version': registry['registry_version'], 'issues': issues, 'warnings': warnings}
(OUT/'registry.log').write_text(stream.getvalue(), encoding='utf-8')
(OUT/'bus_registry_evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
