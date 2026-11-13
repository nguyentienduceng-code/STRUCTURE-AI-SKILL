# Performance audit — CODEX — 2026-11-13

**Status: NEED_REVIEW. Functional checks pass; two timing budgets remain unmet.**

Original 24 suites: PASS 24/24; summed suite time 71.88s -> 30.04s.
Full registry: PASS 27/27, 79.23s. Fast: PASS 17/17, 11.41s (<15s).
Suite 23: baseline 17.43s; isolated cold 3.10s; warm 2.72s (target <2s not reached).

## Quantitative suite timings

Wall clock includes Python startup. Baseline values are rounded to 0.01s by the previous runner.
The 24-suite total is a sum, excluding runner/report overhead; the full total includes that overhead.

| Suite | Baseline seconds | Final seconds | Final result |
|---|---:|---:|---|
| 1. Integration Test (64 checks) | 0.30 | 0.34 | PASS |
| 2. Regression Calculator Test (13 calculators) | 0.34 | 0.23 | PASS |
| 3. Pre-Execution Approval Gate (32 tests) | 0.21 | 0.21 | PASS |
| 4. Intent Classifier Benchmark (17 tests) | 0.18 | 0.18 | PASS |
| 5. E2E Pipeline Workflow | 0.18 | 0.16 | PASS |
| 6. DE Calculators Unit Tests (10 tests) | 0.16 | 0.12 | PASS |
| 7. Sprint 1 Reporting & TCVN Tests (4 tests) | 2.28 | 1.05 | PASS |
| 8. Sprint 2 Cross-Doc Conflict Control Tests (3 tests) | 0.15 | 0.17 | PASS |
| 9. Sprint 3 Phase 2 CAD/BIM/ETABS Tools (61 tests) | 0.39 | 0.27 | PASS |
| 10. Sprint 3 Phase 3 DCE Pro Integration Tests (19 tests) | 3.12 | 2.85 | PASS |
| 11. Sprint 3.4 DCE Deep Integration Tests (16 tests) | 2.34 | 2.21 | PASS |
| 12. Sprint 4 Document Intelligence & Conflict Detection (70 tests) | 3.08 | 0.88 | PASS |
| 13. Sprint 5 Comprehensive Verification & Reporting (17 tests) | 15.68 | 0.92 | PASS |
| 14. Policy Engine & Multi-Trigger Rules (55 tests) | 1.78 | 1.69 | PASS |
| 15. Sync Report System Consistency (14 tests) | 0.75 | 0.55 | PASS |
| 16. Cognitive & System Control Engine (40 tests) | 7.75 | 5.37 | PASS |
| 17. XLSX View Sanity — Anti-[Repaired] (regression openpyxl sheetViews/MergedCell) | 0.65 | 0.57 | PASS |
| 18. DCE CAD Compliance & Zero White Text Lock (9 tests) | 4.84 | 4.65 | PASS |
| 19. Dual-Agent Bridge & Bus IPC (3 tests) | 0.18 | 0.18 | PASS |
| 20. Cognitive Brain v2.0 Benchmark (10 tests) | 0.32 | 0.27 | PASS |
| 21. R&D & Structural TCVN Regression Patches (20 checks) | 1.39 | 1.15 | PASS |
| 22. Cognitive Architecture v2 — Dynamic DAG, Cycles, Budget & JSONL (47 tests) | 0.69 | 0.61 | PASS |
| 23. PDF Citation Grounding & Input Provenance Guard (62 tests) | 17.43 | 2.69 | PASS |
| 24. Nonlinear RC Fiber Section P-Mx-My 3D (23 tests) | 7.69 | 2.73 | PASS |
| 25. Project Data Adapter & E2E Batch Pipeline (34 tests) | 12.30 | 9.99 | PASS |
| 26. Durable Project Orchestration & Agent Roles (39 tests) | 118.62* | 36.91 | PASS |
| 27. CAD Edit Workbench (9 tests) | 1.80 | 2.02 | PASS |

*The initial Suite 26 measurement is not a valid regression baseline: source edits overlapped its runtime fingerprint checks, producing six RUNTIME_CHANGED errors. The final full run had no source edits and all 39 orchestration tests passed. The original 24 completed before the implementation was changed.

## Bottlenecks and implementation

- Suite 13 profile: 18.96s in directory scanning, 20,136 stat calls (13.81s cumulative), 4,908 path resolutions (9.17s cumulative; overlaps stat time). Replaced repeated pathlib metadata queries with os.scandir/DirEntry and resolved the root once.
- Controlled metadata comparison: 4908 files; original Drive traversal 11.355s; new traversal 0.465s; local empty-file mirror 0.061s. Inventory names match. This measures metadata, not PDF content throughput; it does not establish that the entire repository still has the handoff's 6,335 files.
- Suite 23 profile before cache: 203 PDF text extractions, 11.40s cumulative; repeated cover-page extraction alone about 9.67s. After cache, source hashing, process launches and imports remain. Parent CPU before: 3.66s vs 19.75s wall; native extraction time must not be interpreted as pure CPU time.
- Cache stores requested page text in bounded process memory and local atomic JSON, keyed by full source SHA-256, schema and PyMuPDF version. Every call still reads/hashes the source. Cache corruption or write failure falls back to extraction. No citation verdict is cached.
- Edition, duplicate-file, PDF identity, page window, locators, title and forged-success checks remain enabled. Added two regression tests covering disk hits without extraction, corrupt cache, unwritable cache, same-size/same-mtime PDF edits and missing source.
- Document backends now load only when used. A DOCX audit no longer imports unrelated OCR, Excel and CAD dependencies. Added scanner inventory/nonrecursive regression coverage.
- Suite 16 profile: 2.85s artifact detection; changed its metadata traversal to DirEntry too. Its standards database setup, imports and intentional timeout tests remain.
- Suite 24 profile: 3.28s wall / 2.23s parent CPU, with 20,775 fiber response calls. Numerical solver, tolerances and cases were not changed. Its improvement from baseline also reflects eliminating eager dependency imports and run-to-run variability.
- Runtime fingerprint now includes the new cache module so durable orchestration detects changes to verification dependencies.
- No evidence was collected to quantify the handoff claim about model context/token overhead; it is not counted as a measured bottleneck.

## Test tiers and verification

Use `.agents/tests/run_all_tests.py --fast` for development and `--full` for all 27 CI suites. No flags retains full behavior. `--suite` remains repeatable. `--report-dir` records structured timings and complete subprocess logs. Invalid tier combinations fail explicitly; no tests are silently skipped by full mode.
Final full log: `final_full/suite_01.log` through `suite_27.log`; structured summary: `final_full/timings.json`. Fast summary: `final_fast/timings.json`. Independent cold/warm logs: `cache_cold.log`, `cache_warm.log`. Profiles and reproduction scripts are alongside this report.
Additional document-reader validation: 41 tests ran, 38 passed and 3 licensed native Office/AutoCAD integrations were explicitly skipped because native fixtures were not configured. The primary 27-suite registry passed.

## Archival and remaining acceptance gaps

181 legacy files (1,722,590 bytes) from six completed 20261112 audit directories were compressed into `../archive/audits_20261112.zip` (498,445 bytes). Every ZIP member was read back and SHA-256 checked before deleting its original. The adjacent manifest preserves all paths and hashes. Google Drive required retries for two remaining files; only `archive` and this active audit directory remain.
Unmet: warm Suite 23 <2s; summed original 24 <30s. The latest measured values are retained without rounding them into a pass. Full now includes three additional suites; Suite 26 alone takes more than 30s. The bus is NEED_REVIEW, not COMPLETED.
Remaining options require further engineering: isolate/parallelize independent tests after checking shared output paths, and profile remaining process/source-read costs on the deployment hardware. Do not omit real-PDF checks or weaken source invalidation just to meet a timing budget.
