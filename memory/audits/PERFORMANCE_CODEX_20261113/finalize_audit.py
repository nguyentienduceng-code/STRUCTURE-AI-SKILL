"""Build the measured audit report and atomically update the handoff bus."""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT/'.agents/tools'))
import sync_bus

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))

full = read('final_full/timings.json')
fast = read('final_fast/timings.json')
cache = read('cache_timings.json')
io = read('measure_io.json')
raw = (OUT/'baseline.log').read_bytes()
baseline_log = raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
baseline = {int(n): {'passed': status == 'PASS', 'seconds': float(seconds)}
            for status, n, seconds in re.findall(r'(PASS|FAIL) \| (\d+)\..*?\(([\d.]+)s\)', baseline_log)}
assert len(baseline) == 27 and full['all_passed'] and fast['all_passed']
original = full['suites'][:24]
original_seconds = sum(row['wall_seconds'] for row in original)
summary = {
    'timestamp': datetime.now().astimezone().isoformat(),
    'original_24_passed': all(row['passed'] for row in original),
    'original_24_baseline_seconds': sum(baseline[n]['seconds'] for n in range(1, 25)),
    'original_24_final_sum_seconds': original_seconds,
    'full_registered_suites': 27, 'full_passed': full['all_passed'], 'full_seconds': full['wall_seconds'],
    'fast_suites': fast['selected_suites'], 'fast_seconds': fast['wall_seconds'],
    'suite23_cold_seconds': cache[0]['wall_seconds'], 'suite23_warm_seconds': cache[1]['wall_seconds'],
    'acceptance': {'profiling': True, 'citation_cache': True, 'suite23_under_2s': cache[1]['wall_seconds'] < 2,
                   'fast_under_15s': fast['wall_seconds'] < 15, 'original_24_under_30s': original_seconds < 30,
                   'original_24_all_passed': True, 'full_27_all_passed': True, 'archive_verified': True}}
changed = ['.agents/tools/pdf_text_index.py', '.agents/tools/citation_grounding_auditor.py',
           '.agents/tools/doc_reader.py', '.agents/tools/sync_bus.py', '.agents/tools/project_orchestrator.py',
           '.agents/tests/run_all_tests.py', '.agents/tests/test_citation_grounding_guard.py',
           '.agents/tests/test_suite13_verification.py', '.agents/tests/TEST_TIERS.md']
summary['source_sha256'] = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in changed}
(OUT/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
lines = ['# Performance audit — CODEX — 2026-11-13', '',
         '**Status: NEED_REVIEW. Functional checks pass; two timing budgets remain unmet.**', '',
         f"Original 24 suites: PASS 24/24; summed suite time {summary['original_24_baseline_seconds']:.2f}s -> {original_seconds:.2f}s.",
         f"Full registry: PASS 27/27, {full['wall_seconds']:.2f}s. Fast: PASS {fast['selected_suites']}/17, {fast['wall_seconds']:.2f}s (<15s).",
         f"Suite 23: baseline {baseline[23]['seconds']:.2f}s; isolated cold {cache[0]['wall_seconds']:.2f}s; warm {cache[1]['wall_seconds']:.2f}s (target <2s not reached).", '',
         '## Quantitative suite timings', '',
         'Wall clock includes Python startup. Baseline values are rounded to 0.01s by the previous runner.',
         'The 24-suite total is a sum, excluding runner/report overhead; the full total includes that overhead.', '',
         '| Suite | Baseline seconds | Final seconds | Final result |', '|---|---:|---:|---|']
for row in full['suites']:
    n = row['number']
    marker = '*' if n == 26 else ''
    lines.append(f"| {row['name']} | {baseline[n]['seconds']:.2f}{marker} | {row['wall_seconds']:.2f} | PASS |")
lines += ['', '*The initial Suite 26 measurement is not a valid regression baseline: source edits overlapped its runtime fingerprint checks, producing six RUNTIME_CHANGED errors. The final full run had no source edits and all 39 orchestration tests passed. The original 24 completed before the implementation was changed.', '',
          '## Bottlenecks and implementation', '',
          '- Suite 13 profile: 18.96s in directory scanning, 20,136 stat calls (13.81s cumulative), 4,908 path resolutions (9.17s cumulative; overlaps stat time). Replaced repeated pathlib metadata queries with os.scandir/DirEntry and resolved the root once.',
          f"- Controlled metadata comparison: {io['files']} files; original Drive traversal {io['old_drive_seconds']:.3f}s; new traversal {io['scandir_drive_seconds']:.3f}s; local empty-file mirror {io['scandir_local_empty_mirror_seconds']:.3f}s. Inventory names match. This measures metadata, not PDF content throughput; it does not establish that the entire repository still has the handoff's 6,335 files.",
          '- Suite 23 profile before cache: 203 PDF text extractions, 11.40s cumulative; repeated cover-page extraction alone about 9.67s. After cache, source hashing, process launches and imports remain. Parent CPU before: 3.66s vs 19.75s wall; native extraction time must not be interpreted as pure CPU time.',
          '- Cache stores requested page text in bounded process memory and local atomic JSON, keyed by full source SHA-256, schema and PyMuPDF version. Every call still reads/hashes the source. Cache corruption or write failure falls back to extraction. No citation verdict is cached.',
          '- Edition, duplicate-file, PDF identity, page window, locators, title and forged-success checks remain enabled. Added two regression tests covering disk hits without extraction, corrupt cache, unwritable cache, same-size/same-mtime PDF edits and missing source.',
          '- Document backends now load only when used. A DOCX audit no longer imports unrelated OCR, Excel and CAD dependencies. Added scanner inventory/nonrecursive regression coverage.',
          '- Suite 16 profile: 2.85s artifact detection; changed its metadata traversal to DirEntry too. Its standards database setup, imports and intentional timeout tests remain.',
          '- Suite 24 profile: 3.28s wall / 2.23s parent CPU, with 20,775 fiber response calls. Numerical solver, tolerances and cases were not changed. Its improvement from baseline also reflects eliminating eager dependency imports and run-to-run variability.',
          '- Runtime fingerprint now includes the new cache module so durable orchestration detects changes to verification dependencies.',
          '- No evidence was collected to quantify the handoff claim about model context/token overhead; it is not counted as a measured bottleneck.', '',
          '## Test tiers and verification', '',
          'Use `.agents/tests/run_all_tests.py --fast` for development and `--full` for all 27 CI suites. No flags retains full behavior. `--suite` remains repeatable. `--report-dir` records structured timings and complete subprocess logs. Invalid tier combinations fail explicitly; no tests are silently skipped by full mode.',
          'Final full log: `final_full/suite_01.log` through `suite_27.log`; structured summary: `final_full/timings.json`. Fast summary: `final_fast/timings.json`. Independent cold/warm logs: `cache_cold.log`, `cache_warm.log`. Profiles and reproduction scripts are alongside this report.',
          'Additional document-reader validation: 41 tests ran, 38 passed and 3 licensed native Office/AutoCAD integrations were explicitly skipped because native fixtures were not configured. The primary 27-suite registry passed.', '',
          '## Archival and remaining acceptance gaps', '',
          '181 legacy files (1,722,590 bytes) from six completed 20261112 audit directories were compressed into `../archive/audits_20261112.zip` (498,445 bytes). Every ZIP member was read back and SHA-256 checked before deleting its original. The adjacent manifest preserves all paths and hashes. Google Drive required retries for two remaining files; only `archive` and this active audit directory remain.',
          'Unmet: warm Suite 23 <2s; summed original 24 <30s. The latest measured values are retained without rounding them into a pass. Full now includes three additional suites; Suite 26 alone takes more than 30s. The bus is NEED_REVIEW, not COMPLETED.',
          'Remaining options require further engineering: isolate/parallelize independent tests after checking shared output paths, and profile remaining process/source-read costs on the deployment hardware. Do not omit real-PDF checks or weaken source invalidation just to meet a timing budget.', '']
(OUT/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
with sync_bus.FileLock(sync_bus.LOCK_PATH):
    data = json.loads(sync_bus.BUS_PATH.read_text(encoding='utf-8'))
    assert data['current_holder'] == 'CODEX', 'Bus ownership changed'
    data.update(last_updated_by='CODEX', timestamp=summary['timestamp'], handoff_status='NEED_REVIEW',
                current_holder='IDLE', Verification_Status='FUNCTIONAL_PASS_PERFORMANCE_TARGETS_UNMET',
                summary=f"PASS 27/27 suites (original 24/24). Fast {fast['wall_seconds']:.2f}s; original 24 summed {original_seconds:.2f}s; full {full['wall_seconds']:.2f}s. PDF text index caching implemented; Suite 23 cold/warm {cache[0]['wall_seconds']:.2f}/{cache[1]['wall_seconds']:.2f}s, still above 2s. Archived and SHA-256 verified 181 files. See memory/audits/PERFORMANCE_CODEX_20261113/REPORT.md.",
                artifacts_modified=changed+['memory/audits/PERFORMANCE_CODEX_20261113/REPORT.md',
                                           'memory/audits/PERFORMANCE_CODEX_20261113/summary.json',
                                           'memory/audits/archive/audits_20261112.zip',
                                           'memory/audits/archive/audits_20261112.manifest.json',
                                           'memory/DUAL_AGENT_BUS.json', 'memory/DUAL_AGENT_HANDOFF_MEMO.md'],
                performance_verification=summary)
    data['next_action_for_partner'].update(target_agent='GEMINI',
        task_description='Review measured performance gaps: Suite 23 warm <2s and original 24 suites <30s are not achieved. Preserve real PDF checks and full content invalidation; inspect REPORT.md and per-suite profiles before further optimization.',
        command='python .agents/tests/run_all_tests.py --full --report-dir memory/audits/performance_review')
    valid, reason = sync_bus.validate_bus_payload(data)
    assert valid, reason
    sync_bus._atomic_write_json(sync_bus.BUS_PATH, data)
    sync_bus.generate_handoff_memo(data, sync_bus.MEMO_PATH)
print(json.dumps(summary, indent=2))
