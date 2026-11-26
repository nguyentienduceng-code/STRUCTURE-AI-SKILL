# Plan — Solo Tier 2B (Native DWG Snapshot Diff) + Tier 2C Tech Debt

## Decision (locked)
- **Guaranteed, host-testable core = deterministic Python**: canonical snapshot builder + D1/D1A diff engine + DXF fixture pipeline (reuses 2A `dce_xdata_bridge` identity helpers). Zero native dependency, fully unit-testable → this is what "pass" means.
- **Native bridge = thin adapter**: `autocad_snapshot_bridge.py` (accoreconsole detection, staging, timeout, read-only, mock injection, csc build) + `dce_snapshot_plugin.cs` source. Host-gated; reported honestly as UNAVAILABLE-on-host unless the real end-to-end runs green on a staged synthetic DWG (never project DWGs).

## Modules
1. `tools/native_dwg_snapshot.py` — units→mm, entity normalization, canonical snapshot + validator + stable fingerprint, `build_snapshot_from_dxf` (ezdxf) + `build_snapshot_from_inventory`.
2. `tools/native_dwg_diff.py` — join ONLY on `element_id`(+role+floor); `ADDED/REMOVED/PROPERTY_CHANGED/GEOMETRY_CHANGED/MARK_CHANGED/DUPLICATE_PRIMARY/TAG_RELINKED/UNMATCHED/UNVERIFIED/CANDIDATE_MARK`; never auto-match by mark/geometry; versioned tolerances; D1/D1A decision oracle.
3. `tools/autocad_snapshot_bridge.py` — native worker (detection/UNAVAILABLE, staged temp copy + SHA-256 immutability check, one Core-Console process/input with timeout, read-only, injected-fake tests, `csc` build hook for the plugin).
4. `tools/dce_snapshot_plugin.cs` — read-only `DCE_SNAPSHOT` command source (never `Document.Save()`), host-build artifact.
5. `tests/test_tier2_phase2b_snapshot_diff.py` — auto-registers into `run_all_tests.py --full`.
6. `docs/TECHNICAL_DEBT.md` — add **TD-08** (Tier 2C: Revit 2024 read-only + IFC/IfcOpenShell) with scope, trigger, acceptance, status; reconcile matrix without touching other debts.
7. Update `memory/audits/TIER2_PHASE2A_REVIEW_2B_2C_ARCHITECTURE.md` with the shipped 2B design.

## Verification
- Focused suite green; `run_all_tests.py --full` (52/52 after auto-register) green; `audit_zero_white_text.py` 0 warnings.
- Native end-to-end: ONE staged synthetic DWG in temp, hard timeout; assert source SHA unchanged. If host can't complete → report UNAVAILABLE-on-host, do NOT mask as pass.
