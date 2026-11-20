"""Assert the requested recheck gates and retain all compliance diagnostics."""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

for name in ('adversarial_probes.json', 'preview_comparison.json', 'product_measurements.json',
             'adversarial_probes.py', 'compare_previews.py', 'inspect_products.py',
             'KC-01_fresh_overview.png', 'KC-02_fresh_overview.png'):
    shutil.copy2(AUDIT / name, HERE / name)

probes = read(HERE / 'adversarial_probes.json')
preview = read(HERE / 'preview_comparison.json')
tests = read(HERE / 'full_tests/timings.json')
products = read(HERE / 'product_measurements.json')
f1 = probes['no_structural_source_micro_leader']
f2 = probes['leader_layer_creation_failure']
f3 = probes['dry_run_layer_mutation']
f4 = probes['existing_wrong_layer_color']
checks = {
    'F1_no_source_micro_leader_suppressed': f1['status'] == 'OK' and f1['leaders'] == [],
    'F2_layer_failure_fails_closed': f2['status'] == 'NEEDS_REVIEW' and f2['leaders'] == [] and bool(f2['errors']),
    'F3_dry_run_creates_no_layers': f3['status'] == 'DRY_RUN_OK' and f3['new_layers'] == [],
    'F4_existing_color_normalized': f4['status'] == 'OK' and f4['layer_color'] == 250 and
        len(f4['leaders']) == 1 and f4['leaders'][0]['layer'] == 'DCE_Leader',
    'both_previews_exact_rgb_match': {p['sheet'] for p in preview} == {'KC-01', 'KC-02'} and
        all(p['exact_pixel_match'] and p['different_pixels'] == 0 and p['supplied_size'] == p['fresh_size'] for p in preview),
    'full_regression_30_of_30': tests['tier'] == 'full' and tests['registered_suites'] == 30 and
        tests['selected_suites'] == 30 and tests['all_passed'] and len(tests['suites']) == 30 and
        all(s['passed'] for s in tests['suites']),
}
product_checks = {}
compliance = {}
for product in products:
    sheet = product['sheet']
    product_checks[sheet] = (
        product['remaining_collision_count'] == 0 and not product['leader_conflicts'] and
        product['leader_count'] == {'KC-01': 25, 'KC-02': 8}[sheet] and
        not product['micro_leaders'] and not product['wrong_layer'] and product['layer_color'] == 250 and
        all(x['entity_color'] == 250 for x in product['leaders']) and
        not product['altered_fixed_entities'] and product['dxf_audit_errors'] == 0 and
        product['repeat_status'] == 'DRY_RUN_OK' and product['repeat_displacements'] == 0
    )
    c = product['compliance']
    compliance[sheet] = {
        'api_status': c['status'], 'api_issues': c['issues'],
        'gates_passed': c['gates_passed'], 'gates_total': c['gates_total'],
        'failed_gate_ids': [g['gate_id'] for g in c['gate_results'] if not g['passed']],
        'all_20_gates_passed': c['gates_passed'] == c['gates_total'] == 20,
    }

before = read(HERE / 'manifest_before.json')['files']
after = {name: {'sha256': hashlib.sha256(Path(name).read_bytes()).hexdigest(),
                'bytes': Path(name).stat().st_size, 'mtime_ns': Path(name).stat().st_mtime_ns}
         for name in before}
changed = [name for name in before if before[name] != after[name]]
expected_change = str(AUDIT / 'inspect_products.py')
integrity = {
    'tracked_file_count': len(before), 'changed_files': changed,
    'only_change_is_audit_loader_fix': changed == [expected_change],
    'production_source_and_products_unchanged': all(name == expected_change for name in changed),
    'audit_loader_change': 'Register independent_compliance in sys.modules before exec_module for Python 3.12 dataclasses.',
    'no_git_push_performed': True,
}
(HERE / 'manifest_after.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
(HERE / 'integrity.json').write_text(json.dumps(integrity, indent=2), encoding='utf-8')
passed = all(checks.values()) and all(product_checks.values()) and integrity['production_source_and_products_unchanged']
verdict = {
    'timestamp': datetime.now().astimezone().isoformat(),
    'requested_recheck_status': 'PASS' if passed else 'FAIL',
    'scoped_signoff': 'APPROVED' if passed else 'WITHHELD',
    'scope': 'Original F1-F4 probes, KC-01/KC-02 RGB preview equality, full 30-suite regression.',
    'checks': checks, 'additional_product_geometry_checks': product_checks,
    'regression_wall_seconds': tests['wall_seconds'],
    'compliance_diagnostics': compliance,
    'full_20_gate_compliance_signoff': 'NOT_APPROVED',
    'followup': 'F5: physical PASS does not establish 20/20 gate PASS; audit API ignores failed gate results.',
    'publication_or_github_push_authorized': False,
    'confidence_level': 'HIGH',
}
(HERE / 'verdict.json').write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(verdict, indent=2, ensure_ascii=False))
assert passed, 'One or more requested recheck gates failed; do not issue scoped sign-off.'
