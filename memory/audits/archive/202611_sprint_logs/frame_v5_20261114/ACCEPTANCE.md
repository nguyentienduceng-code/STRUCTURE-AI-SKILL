# Frame scale and canvas fix ? 2026-11-14

Project: 06_FIX_FRAME_SCALE_AND_COLLISION_V5.

Implemented scale_spec-aware frame/title geometry, 25/10 mm margins, a reserved 220 mm sidebar and footprint centering in its usable canvas. Model geometry stays in real mm; only paper furniture is scaled. Schedule and notes move into the scaled sidebar. Plan-title text and attributes use true color #1E3246. Grid LINE segments intersecting the title-block exclusion zone are trimmed with a 10*S clearance.

Legacy calls without scale_spec retain their existing geometry; the title color correction applies to both paths. A1 S=125 and S=150 were checked on KC-02 and KC-03. Regression asserts frame width, center coordinates, grid/sidebar clearance and dark title attributes. At S=150 the frame is 126150 x 89100 mm.

Full regression: 31/31 suites PASS, 123.64 seconds. The added dynamic-frame test was also run separately after the final trim change and passed all four sheet/scale combinations. DXF reopen audits for the two rendered samples report zero errors and zero fixes.

Artifacts: frame_v5_kc02.dxf, frame_v5_kc03.dxf, kc02.png, kc03.png, tests/timings.json and per-suite logs. KC-02 overview was visually inspected; plan geometry is separated from the schedule and title block. These checks concern the reported frame/sidebar overlap, not a new blanket certification of every annotation on all possible projects.

No GitHub push or vendor-installation changes. CODEX implemented and tested this revision; Gemini may perform the next visual QA pass using these local artifacts.
