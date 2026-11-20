"""Read-only measurements of delivered products plus generated regression artifacts."""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parents[3]
sys.path[:0] = [str(AGENTS/'tools'), str(AGENTS/'skills/SKILL_VERIFY/scripts'),
                str(AGENTS/'skills/Technical_Illustrator/cad_integration')]
from dce_virtual_drive_guard import configure_runtime, managed_dir
configure_runtime()
from cad_collision_solver import CadCollisionSolver
from cad_plan_engine import build_sample_40_story_tower_plan
from dce_cad_compliance_checker import audit_dxf_compliance
import ezdxf

PRODUCT = AGENTS.parent/'01_Projects/03_Sprint2_KetQua_NeChu_CAD'
scratch = managed_dir('temp')/'f5_completion'
scratch.mkdir(exist_ok=True)
records = []
for sheet, count in (('KC-01',25),('KC-02',8)):
    path = PRODUCT/(sheet+'_DA_NE_CHU_LeaderLine.dxf')
    solver = CadCollisionSolver.from_dxf(path)
    leaders = [e for e in solver.doc.modelspace() if e.has_xdata('DCE_COLLISION')]
    lengths = [e.dxf.start.distance(e.dxf.end)*solver.scene.mm_per_unit for e in leaders]
    physical = audit_dxf_compliance(str(path), profile='physical')
    full = audit_dxf_compliance(str(path))
    record = {'sheet':sheet, 'remaining_collision_count':len(solver.detect_collisions()),
        'leader_conflicts':solver.detect_leader_conflicts(), 'leaders':len(leaders),
        'min_length_mm':min(lengths), 'max_length_mm':max(lengths),
        'micro_leaders':sum(length < 100 for length in lengths),
        'wrong_leader_layer_or_color':sum(e.dxf.layer != 'DCE_Leader' or e.dxf.color != 250 for e in leaders),
        'physical_audit':physical, 'full_audit':full, 'benchmarks':[]}
    assert record['remaining_collision_count'] == 0 and not record['leader_conflicts']
    assert len(leaders) == count and not record['micro_leaders'] and not record['wrong_leader_layer_or_color']
    assert physical['status'] == 'PASS' and not physical['full_compliance_verified']
    assert full['status'] == 'NEEDS_REVIEW' and full['gates_unverified'] == 20
    for iteration in range(3):
        output = scratch/f'{sheet}_benchmark_{iteration}.dxf'
        started = time.perf_counter()
        instance = CadCollisionSolver.from_dxf(PRODUCT/(sheet+'_Goc_ChuaNeChu.dxf'))
        result = instance.solve_all(output_path=output)
        elapsed = time.perf_counter()-started
        record['benchmarks'].append({'wall_seconds_load_solve_save':elapsed,
            'status':result['status'], 'remaining_collision_count':result['remaining_collision_count'],
            'leaders_created':result['leaders_created']})
        assert result['status'] == 'OK' and elapsed < 2.0, record['benchmarks'][-1]
        assert result['leaders_created'] == count
        output.unlink()
    print(sheet, 'PASS', count, 'leaders, max seconds', max(x['wall_seconds_load_solve_save'] for x in record['benchmarks']))
    records.append(record)
(HERE/'product_verification.json').write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding='utf-8')

generated = HERE/'generated_native'
generated.mkdir(exist_ok=True)
native = []
for mode in ('COLUMN_WALL_SETOUT','BEAM_SLAB_FRAMING','SLAB_REBAR_PLAN','FOUNDATION_LAYOUT'):
    path = scratch/(mode+'.dxf')
    build_sample_40_story_tower_plan(str(path), mode)
    result = audit_dxf_compliance(str(path), profile='plan')
    assert result['status'] == 'PASS' and result['gates_passed'] == 16 and result['gates_not_applicable'] == 4, result
    assert not result['full_compliance_verified'] and result['audit_fixes_count'] == 0
    full = audit_dxf_compliance(str(path))
    assert full['status'] == 'NEEDS_REVIEW' and full['gates_unverified'] == 4
    doc = ezdxf.readfile(path)
    result['native_dimensions'] = len(doc.modelspace().query('DIMENSION'))
    result['native_attributes'] = sum(len(e.attribs) for e in doc.modelspace().query('INSERT'))
    result['full_status'] = full['status']
    for source in (path, path.with_suffix('.dce_audit.json')):
        shutil.copy2(source, generated/source.name)
    native.append(result)
    print(mode, result['status'], '16 PASS + 4 N/A', result['native_dimensions'], 'native dimensions')
(HERE/'native_generator_checks.json').write_text(json.dumps(native,indent=2,ensure_ascii=False),encoding='utf-8')

before = json.loads((HERE/'manifest_before.json').read_text(encoding='utf-8'))
product_names = [p for p in before if Path(p).parent == PRODUCT]
unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == before[p]['sha256'] and
                Path(p).stat().st_mtime_ns == before[p]['mtime_ns'] for p in product_names)
assert unchanged
(HERE/'product_integrity.json').write_text(json.dumps({'unchanged':unchanged,'product_files':len(product_names)},indent=2),encoding='utf-8')
print('All original product files unchanged:',len(product_names))
