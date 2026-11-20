# C2 Remediation Result — A1 CODEX findings

**Input:** `codex/independent_review_20261115/A1_CODEX_ACCEPTANCE.md`  
**Status:** REMEDIATION COMPLETE; ready for GEMINI linkage review.

## Fixed

- **A1-01:** C2 exporter now emits fixture-derived concrete, steel and rebar geometry; INSERT/ATTRIB tags, LWPOLYLINE, HATCH and native DIMENSION entities are present. Entity handles are recorded in per-sheet sidecars.
- **A1-02:** Dual viewport paper boxes are distinct: `[15,15,205,145]` and `[15,150,205,280]`; reopened DXF centers/heights confirm no overlap.
- **A1-03:** KC-04 uses actual viewport frozen layers: TOP freezes `REBAR_BOTTOM`; BOTTOM freezes `REBAR_TOP`. Rebar geometry uses `REBAR_TOP` / `REBAR_BOTTOM` layers.
- **A1-04:** `view_height = paper viewport height × manifest scale`. For scale 50 and viewport height 130 mm, reopened DXF reports `6500`; single view height 227 mm reports `11350`.
- **A1-05:** A3 frame, right-side title placement, sheet/revision title and physical content are emitted in each DXF.
- **A1-07:** Per-sheet sidecars contain `dxf_sha256`, sheet number, viewport count and entity map. Aggregate audit contains manifest hash.
- **A1-08:** Added C2 tests and strengthened physical output. Existing C1/G2 regression remains green.

## Reopened physical evidence

Output: `claude/c2_remediated/`

All five sheets reopened successfully. Each contains:

```text
INSERT=9, LINE=6, LWPOLYLINE=11, HATCH=2, DIMENSION=1
```

KC-04 reopened viewport state:

```text
VP_SLAB_BOT: bbox=[15,15,205,145], view_height=6500, frozen_layers=['REBAR_TOP']
VP_SLAB_TOP: bbox=[15,150,205,280], view_height=6500, frozen_layers=['REBAR_BOTTOM']
```

## Tests

```text
python -B -m unittest test_cad_v6_c2 test_cad_v6_c1 test_dce_block_semantics
Ran 19 tests — OK
```

## Next handoff

GEMINI must validate every sidecar entity map against reopened DXF handles and confirm source refs resolve to physical entities (A1-06). After GEMINI's linkage result, CODEX should rerun independent A1 review against `c2_remediated/`.
