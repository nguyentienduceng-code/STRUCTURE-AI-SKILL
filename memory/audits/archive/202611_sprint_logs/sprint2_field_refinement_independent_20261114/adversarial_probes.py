"""Isolated failure/edge probes; never edits audited source or deliverables."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
AGENTS=HERE.parents[2]
sys.path.insert(0,str(AGENTS/'tools'))
from dce_virtual_drive_guard import configure_runtime,managed_dir
configure_runtime()
import ezdxf
from cad_collision_solver import CadCollisionSolver
from cad_scene_index import CadSceneIndex

def fixture():
    doc=ezdxf.new();doc.header['$INSUNITS']=4
    for name in ('DCE_Name','DCE_Cot','DCE_Truc'):
        doc.layers.new(name)
    doc.modelspace().add_lwpolyline([(-200,-200),(600,-200),(600,600),(-200,600)],close=True,dxfattribs={'layer':'DCE_Cot'})
    doc.modelspace().add_text('BIG_LABEL',dxfattribs={'layer':'DCE_Name','height':250,'insert':(100,100)})
    return doc

def leaders(doc):
    return [{'layer':e.dxf.layer,'length_mm':e.dxf.start.distance(e.dxf.end)}
            for e in doc.modelspace().query('LINE') if e.has_xdata('DCE_COLLISION')]

root=managed_dir('temp')/'field_refinement_audit'
root.mkdir(exist_ok=True)
results={}
doc=fixture();before=list(doc.layers.entries)
result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(dry_run=True)
results['dry_run_layer_mutation']={'status':result['status'],'new_layers':sorted(set(doc.layers.entries)-set(before))}

doc=fixture();original_add=doc.layers.add
def deny_layer(name,*args,**kwargs):
    if name=='DCE_Leader':
        raise OSError('injected DCE_Leader creation failure')
    return original_add(name,*args,**kwargs)
with patch.object(doc.layers,'add',side_effect=deny_layer):
    result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=root/'fallback.dxf')
results['leader_layer_creation_failure']={'status':result['status'],'leaders':leaders(doc),'errors':result['apply_errors']}

doc=fixture();doc.layers.new('DCE_Leader',dxfattribs={'color':1})
result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=root/'wrong_color.dxf')
results['existing_wrong_layer_color']={'status':result['status'],'layer_color':doc.layers.get('DCE_Leader').dxf.color,'leaders':leaders(doc)}

doc=ezdxf.new();doc.header['$INSUNITS']=4;doc.layers.new('DCE_Name')
for x,y,text in ((500,500,'LABEL_A'),(520,510,'LABEL_B')):
    doc.modelspace().add_text(text,dxfattribs={'layer':'DCE_Name','height':250,'insert':(x,y)})
result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=root/'no_structural_source.dxf')
results['no_structural_source_micro_leader']={'status':result['status'],'leaders':leaders(doc),'paths':result['leader_paths']}
(HERE/'adversarial_probes.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
