import sys,importlib.util,json,time,hashlib
from pathlib import Path
r=Path('G:/My Drive/Google AI Studio/.agents');sys.path.insert(0,str(r/'tools'))
from dce_virtual_drive_guard import configure_runtime,managed_dir,require_local
import os
os.environ["XDG_CACHE_HOME"]="G:/My Drive/forbidden_font_cache"
configure_runtime()
spec=importlib.util.spec_from_file_location('plan',r/'skills/Technical_Illustrator/cad_integration/cad_plan_engine.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from cad_collision_solver import CadCollisionSolver
folder=managed_dir('temp')/'sprint2_completion_20261114';folder.mkdir(exist_ok=True)

import os, statistics
import mcp_dce_cad_server as srv
from ezdxf.lldxf.tagwriter import TagCollector
import ezdxf

def fingerprint(ent):
 return repr(TagCollector.dxftags(ent))
results=[]
for label,method in [('KC-01','render_sheet_kc02'),('KC-02','render_sheet_kc03')]:
 e=m.DcePlanEngine(m.build_structural_model());e.setup();getattr(e,method)()
 src=folder/(label+'.dxf');e.save(str(src));source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
 original=ezdxf.readfile(src)
 before_index=CadCollisionSolver.from_dxf(src)
 movable={x.handle for x in before_index.scene.movable_entities}
 fixed={x.dxf.handle:fingerprint(x) for x in original.modelspace() if x.dxf.handle not in movable}
 runs=[]
 for run in range(3):
  start=time.perf_counter()
  res=srv.resolve_cad_collisions(str(src),output_dxf='G:/My Drive/forbidden_collision_output.dxf')
  elapsed=time.perf_counter()-start
  out=Path(res['output_dxf']);require_local(out)
  loaded=ezdxf.readfile(out)
  fixed_ok=all(fingerprint(loaded.entitydb[h])==value for h,value in fixed.items())
  fresh=CadCollisionSolver.from_dxf(out)
  fresh_count=len(fresh.detect_collisions())
  assert res['status']=='OK' and fresh_count==0 and not fresh.detect_leader_conflicts()
  repeat=fresh.solve_all(dry_run=True)
  assert repeat['status']=='DRY_RUN_OK' and repeat['displacements_planned']==0
  moved={p['handle'] for p in res['plans']}
  protected_hits=[c.__dict__ for c in fresh.detect_collisions() if c.entity_handle in moved and c.colliding_with_layer in {'DCE_Frame','DCE_Schedule'}]
  assert fixed_ok and fresh_count==res['remaining_collision_count'] and not protected_hits
  assert hashlib.sha256(src.read_bytes()).hexdigest()==source_hash
  assert not loaded.audit().has_errors
  runs.append(dict(wall_seconds=elapsed,**res))
 summary={'sheet':label,'engine_method':method,'description':'57m x 28m typical floor geometry, 40-storey tower scenario; not a solver-verified project',
  'entities':len(original.modelspace()),'movable_labels':len(movable),'units':original.header['$INSUNITS'],
  'source':str(src),'source_sha256':source_hash,'runs':runs,'max_wall_seconds':max(x['wall_seconds'] for x in runs),
  'fixed_entities_preserved':len(fixed),'moved_labels_in_frame_or_schedule':0,
  'remaining_details':[c.__dict__ for c in fresh.detect_collisions()]}
 assert summary['max_wall_seconds'] < 2.0
 results.append(summary)
 print(label,summary['entities'],'max_seconds',summary['max_wall_seconds'],'remaining',res['remaining_collision_count'],'leader_conflicts',len(res['leader_conflicts']))
 require_local(out)
audit=r/'memory/audits/sprint2_collision_completion_20261114';audit.mkdir(parents=True,exist_ok=True)
(audit/'benchmark.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
(audit/'runtime_paths.json').write_text(json.dumps({'scratch':str(require_local(folder)),'TEMP':os.environ['TEMP'],'TMP':os.environ['TMP'],'MPLCONFIGDIR':os.environ['MPLCONFIGDIR'],'XDG_CACHE_HOME':str(require_local(os.environ['XDG_CACHE_HOME'])),'python_bytecode_disabled':sys.dont_write_bytecode,'spatial_cache':'RAM only; no persistent spatial index','ezdxf':ezdxf.__version__},indent=2),encoding='utf-8')
