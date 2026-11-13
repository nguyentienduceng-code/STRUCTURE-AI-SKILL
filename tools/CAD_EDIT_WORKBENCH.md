# CAD editing workbench — initial DXF backend

Draft-only editing of existing drawings. Requires ezdxf with its SVG drawing
backend. The original input is never saved over. Every revision retains its DXF,
SVG preview and change manifest; HEAD.json changes only after verification/render.

Use absolute paths. Example PowerShell commands from the repository root:

```powershell
python .agents/tools/cad_edit_workbench.py create --source 'C:/CAD/plan.dxf' --session 'C:/CAD/sessions/review01'
python .agents/tools/cad_edit_workbench.py inspect --session 'C:/CAD/sessions/review01'
python .agents/tools/cad_edit_workbench.py move --session 'C:/CAD/sessions/review01' --revision '<revision from inspect>' --handle '<entity handle>' --dx 0 --dy 100
python .agents/tools/cad_edit_workbench.py undo --session 'C:/CAD/sessions/review01' --revision '<latest revision>'
```

Offsets are drawing units, not implicitly millimetres. Inspect gives exact handles,
types, layers, text and positions, together with the drawing and SVG preview paths.
Review the preview and identify the intended handle before editing. Prior revisions
retain the before image; each new revision contains the after image. Selection is
explicit by modelspace handle, not fuzzy text matching. Existing source changes do
not alter an imported snapshot. External changes to a revision are rejected: import
the changed DXF into a new session rather than silently overwriting it.

Supported edits: translate modelspace TEXT/MTEXT; relocate the dimension line of
planar linear/aligned DIMENSION while preserving extension origins and measurement.
Other entities are not editable. Reopened selected entity tags must match intended
tags, and every unselected modelspace entity must retain its exported tags.
Dimension render blocks can be regenerated; document metadata can change on save.

Undo creates a new revision restoring exact previous DXF bytes. Repeated undo walks
back through the restored history. Stale revision tokens, concurrent writers and
manual edits are blocked. A crash may leave an uncommitted revision/candidate file;
HEAD still identifies the committed state. After confirming no editing process is
running, an operator may remove a leftover .lock to recover. This is local cooperative
locking, not an OS security sandbox or protection against malicious session metadata edits.

Limitations: no DWG/AutoCAD COM editing, nested block/ATTRIB editing, graphical picking,
cropped comparison, automatic collision detection or engineering approval. SVG is a
whole-modelspace preview, not a validated paper-space plot; fonts and unsupported
entities may render differently in AutoCAD. The tests use synthetic DXF fixtures;
a real project pilot and AutoCAD visual review remain necessary before production use.
