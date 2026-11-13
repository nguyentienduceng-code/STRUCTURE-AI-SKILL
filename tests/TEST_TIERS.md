# Test tiers and timing reports

Run from the workspace root:

```powershell
python .agents/tests/run_all_tests.py --fast
python .agents/tests/run_all_tests.py --full --report-dir memory/audits/ci_run
python .agents/tests/run_all_tests.py --suite 13 --suite 23 --report-dir memory/audits/targeted_run
```

No flags still runs all registered suites. Full currently means **27 suites**,
including the original 24 plus project pipeline, durable orchestration and CAD
workbench. Fast runs 17 explicitly listed suites, including real-PDF citation
grounding; it is development feedback, not full certification. Fast and explicit
suite selection cannot be combined. Unknown suite IDs exit with an error.

Each report directory contains `timings.json` and stdout/stderr, exit code and
wall-clock duration for every selected suite. Failures propagate a nonzero exit
status. The default per-suite timeout is 300 seconds; `--timeout` overrides it.
Use a distinct report directory for each run to retain history. Timing includes
process startup. Targets are fast <15s and warm Suite 23 <2s; these are measured
budgets, not guaranteed performance on every filesystem/machine.

PDF text indexes live in `%LOCALAPPDATA%/GoogleAIStudio/pdf-text-index` by default.
`PDF_TEXT_INDEX_CACHE_DIR` selects another location, including a new empty
directory for a cold-cache benchmark. The source PDF is read and SHA-256 hashed
on every verification; changing content invalidates the index even when size
and modification time are preserved. Missing/unreadable PDFs fail closed.
The key includes the cache schema and PyMuPDF version. Only requested page text
is cached, never verification verdicts. The file must still pass the current
lock, edition, ambiguity, identity, locator and title checks.

Indexes use checksummed JSON and atomic local replacement. Corrupt or unavailable
cache files fall back to extraction. They are disposable derived data and may be
removed while no audit is running. Local in-process indexes are bounded to 16
PDFs; disk entries persist until removed. Keep the cache under the current user's
control, like other local application data.

See `memory/audits/PERFORMANCE_CODEX_20261113/REPORT.md` for baseline, final timings,
profiling evidence and limitations. Historical audit files are preserved in
`memory/audits/archive/audits_20261112.zip`; its adjacent manifest lists every
original relative path and SHA-256. Extract into `memory/audits` to restore them.
