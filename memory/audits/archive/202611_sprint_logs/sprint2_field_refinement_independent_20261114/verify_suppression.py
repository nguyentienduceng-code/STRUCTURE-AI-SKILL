"""Replay baseline in RAM and independently identify proximity suppression."""
import json
import math
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
AGENTS=HERE.parents[2]
sys.path.insert(0,str(AGENTS/'tools'))
from dce_virtual_drive_guard import configure_runtime
configure_runtime()
from cad_collision_solver import CadCollisionSolver
from ezdxf import disassemble
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
PRODUCT=AGENTS.parent/'01_Projects/03_Sprint2_KetQua_NeChu_CAD'
records=[]
def unpadded(entity):
    shapes=[]
    for leaf in disassemble.recursive_decompose([entity]):
        pts=[(v.x,v.y) for v in disassemble.make_primitive(leaf,max_flattening_distance=5).vertices()]
        if len(pts)<2:
            continue
        if leaf.dxftype() in {'TEXT','MTEXT','ATTRIB','ATTDEF'} or (len(pts)>2 and pts[0]==pts[-1]):
            shapes.append(Polygon(pts).buffer(0))
        else:
            shapes.append(LineString(pts))
    return unary_union(shapes)
for sheet in ('KC-01','KC-02'):
    solver=CadCollisionSolver.from_dxf(PRODUCT/(sheet+'_Goc_ChuaNeChu.dxf'))
    product=CadCollisionSolver.from_dxf(PRODUCT/(sheet+'_DA_NE_CHU_LeaderLine.dxf'))
    original_route=solver._route
    skipped={}
    def observe(plan):
        route=original_route(plan)
        if route and route.get('skip_draw'):
            annotation=solver.scene.grid.entities[plan.handle]
            source=solver.scene.grid.entities[route['source_handle']]
            skipped[plan.handle]={'handle':plan.handle,'source':source.handle,
                'gap_mm':annotation.geometry.distance(source.geometry)*solver.scene.mm_per_unit,
                'planned_position':list(plan.target_pos)}
        return route
    solver._route=observe
    result=solver.solve_all(dry_run=True)
    assert result['status']=='DRY_RUN_OK'
    mismatches=[p['handle'] for p in result['plans'] if math.dist(p['to'],product.scene.grid.entities[p['handle']].anchor_point)>1e-6]
    assert not mismatches,mismatches
    for handle,row in skipped.items():
        assert math.dist(row['planned_position'],product.scene.grid.entities[handle].anchor_point)<1e-6
        assert not any(e.leader_owner==handle for e in product.scene.grid.entities.values())
        row['unpadded_layout_to_source_mm']=unpadded(product.doc.entitydb[handle]).distance(
            unpadded(product.doc.entitydb[row['source']]))*product.scene.mm_per_unit
    gaps=[row['gap_mm'] for row in skipped.values()]
    record={'sheet':sheet,'skip_count':len(skipped),'min_gap_mm':min(gaps),'max_gap_mm':max(gaps),
            'replay_matches_product':True,'skipped_annotations':list(skipped.values())}
    raw=[row['unpadded_layout_to_source_mm'] for row in skipped.values()]
    record.update(unpadded_min_mm=min(raw),unpadded_max_mm=max(raw),unpadded_count_below_100=sum(v<100 for v in raw))
    records.append(record)
    print(sheet,len(skipped),min(gaps),max(gaps),'positions match product')
    print('Unpadded layout-to-source:',min(raw),max(raw),'below 100:',sum(v<100 for v in raw))
(HERE/'suppression_replay.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
