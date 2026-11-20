"""Read-only product audit; derived scratch stays on local disk."""
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parents[2]
PRODUCT = AGENTS.parent/'01_Projects/03_Sprint2_KetQua_NeChu_CAD'
sys.path.insert(0,str(AGENTS/'tools'))
from dce_virtual_drive_guard import configure_runtime, managed_dir
configure_runtime()
from cad_collision_solver import CadCollisionSolver
import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector
from PIL import Image

spec=importlib.util.spec_from_file_location('independent_compliance',AGENTS/'skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py')
checker=importlib.util.module_from_spec(spec)
# Python 3.12 dataclasses resolve postponed annotations through sys.modules.
sys.modules[spec.name]=checker
spec.loader.exec_module(checker)
SOURCE=[AGENTS/'tools/cad_collision_solver.py',AGENTS/'tools/cad_scene_index.py',AGENTS/'skills/Technical_Illustrator/cad_integration/cad_plan_engine.py',AGENTS/'tests/test_cad_collision_solver.py',AGENTS/'skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py']

def manifest():
    return {str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
            for p in [*PRODUCT.iterdir(),*SOURCE] if p.is_file()}

before=manifest()
(HERE/'manifest_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
results=[]
for name in ('KC-01','KC-02'):
    path=PRODUCT/(name+'_DA_NE_CHU_LeaderLine.dxf')
    baseline=PRODUCT/(name+'_Goc_ChuaNeChu.dxf')
    original=CadCollisionSolver.from_dxf(baseline)
    solver=CadCollisionSolver.from_dxf(path)
    doc=solver.doc
    leaders=[]
    for entity in doc.modelspace():
        tagged=entity.has_xdata('DCE_COLLISION')
        if entity.dxf.layer=='DCE_Leader' or tagged:
            if entity.dxftype()=='LINE':
                length=entity.dxf.start.distance(entity.dxf.end)*solver.scene.mm_per_unit
            elif entity.dxftype()=='LWPOLYLINE':
                pts=list(entity.get_points('xy'));length=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))*solver.scene.mm_per_unit
            else:
                length=None
            links=[t.value for t in entity.get_xdata('DCE_COLLISION') if t.code==1005] if tagged else []
            leaders.append({'handle':entity.dxf.handle,'type':entity.dxftype(),'layer':entity.dxf.layer,
                            'entity_color':entity.dxf.color,'length_mm':length,'owner':links[0] if links else None,
                            'source':links[1] if len(links)>1 else None})
    annotations={e.handle:e for e in original.scene.movable_entities}
    moved=[]
    for handle,entity in annotations.items():
        out=solver.scene.grid.entities.get(handle)
        if out is not None:
            distance=math.dist(entity.anchor_point,out.anchor_point)*solver.scene.mm_per_unit
            if distance>1e-6:
                sources=[l for l in leaders if l['owner']==handle]
                point=solver.doc.entitydb[handle].dxf.insert
                # Read physical clearance from the product's final geometry.
                nearby=[]
                for other in solver.scene.grid.entities.values():
                    if other.layer in solver.scene.HARD_OBSTACLE_LAYERS and other.layer not in {'DCE_Truc','DCE_Frame','DCE_Schedule'} and other.role!='boundary':
                        nearby.append((out.geometry.distance(other.geometry)*solver.scene.mm_per_unit,other.handle))
                clearance,source=min(nearby,default=(None,None))
                moved.append({'handle':handle,'distance_mm':distance,'leaders':len(sources),
                              'clearance_mm':clearance,'nearest_structural_handle':source,
                              'position':[point.x,point.y]})
    fixed={e.dxf.handle:TagCollector.dxftags(e) for e in original.doc.modelspace() if e.dxf.handle not in annotations}
    altered=[h for h,tags in fixed.items() if h not in doc.entitydb or TagCollector.dxftags(doc.entitydb[h])!=tags]
    lengths=[l['length_mm'] for l in leaders if l['length_mm'] is not None]
    compliance=checker.audit_dxf_compliance(str(path))
    repeat=solver.solve_all(dry_run=True)
    image=PRODUCT/(name+'_after.png')
    with Image.open(image) as img:
        png={'path':str(image),'size':img.size,'info':{k:str(v) for k,v in img.info.items()}}
    result={'sheet':name,'units':doc.header.get('$INSUNITS'),'entity_count':len(doc.modelspace()),
            'remaining_collision_count':len(solver.detect_collisions()),
            'leader_conflicts':solver.detect_leader_conflicts(),'leaders':leaders,
            'leader_count':len(leaders),'length_min_mm':min(lengths,default=None),'length_max_mm':max(lengths,default=None),
            'micro_leaders':[l for l in leaders if l['length_mm'] is not None and l['length_mm']<100],
            'layer_color':doc.layers.get('DCE_Leader').dxf.color if 'DCE_Leader' in doc.layers else None,
            'wrong_layer':[l for l in leaders if l['layer']!='DCE_Leader'],
            'moved_annotations':moved,'altered_fixed_entities':altered,
            'repeat_status':repeat['status'],'repeat_displacements':repeat['displacements_planned'],
            'compliance':compliance,'image':png,'dxf_audit_errors':len(doc.audit().errors)}
    results.append(result)
    print(json.dumps({k:result[k] for k in ('sheet','remaining_collision_count','leader_count','length_min_mm','length_max_mm','layer_color','repeat_status')},ensure_ascii=True))
(HERE/'product_measurements.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
assert before==manifest(),'Product or audited source changed during inspection'
print('Products and audited sources unchanged')
