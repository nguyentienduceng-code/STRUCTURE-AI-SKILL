"""Independent read-back assertions for the benchmark DXFs; no source writes."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parents[2]
sys.path.insert(0, str(AGENTS / 'tools'))
from dce_virtual_drive_guard import configure_runtime, require_local
configure_runtime()
import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector
from cad_collision_solver import CadCollisionSolver

def signature(entity):
    # Translation may alter position and alignment points, not text/style/color/
    # dimensions/scales/rotation or any engineering metadata.
    return [tag for tag in TagCollector.dxftags(entity)
            if tag.code not in {10,20,30,11,21,31}]

records = []
for sheet in json.loads((HERE / 'benchmark.json').read_text(encoding='utf-8')):
    source = Path(sheet['source'])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sheet['source_sha256']
    original = CadCollisionSolver.from_dxf(source)
    movable = {e.handle for e in original.scene.movable_entities}
    for run in sheet['runs']:
        target = require_local(run['output_dxf'])
        fresh = CadCollisionSolver.from_dxf(target)
        assert not fresh.doc.audit().has_errors
        assert not fresh.detect_collisions()
        assert not fresh.detect_leader_conflicts()
        for entity in original.doc.modelspace():
            output = fresh.doc.entitydb[entity.dxf.handle]
            if entity.dxf.handle in movable:
                assert signature(entity) == signature(output)
                if entity.dxftype() == 'INSERT':
                    assert [signature(a) for a in entity.attribs] == [signature(a) for a in output.attribs]
            else:
                assert TagCollector.dxftags(entity) == TagCollector.dxftags(output)
        again = fresh.solve_all(dry_run=True)
        assert again['status'] == 'DRY_RUN_OK' and again['displacements_planned'] == 0
        assert not again['leader_paths']
        records.append({'sheet':sheet['sheet'], 'file':str(target),
                        'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                        'source_preserved':True, 'fixed_entities_preserved':True,
                        'annotation_content_and_style_preserved':True,
                        'label_collisions':0, 'leader_conflicts':0,
                        'repeat_displacements':0})
(HERE / 'verification.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(f'{len(records)} DXF read-back verifications PASS')
