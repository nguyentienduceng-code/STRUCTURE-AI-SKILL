import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, hashlib, pathlib, collections, importlib.util, subprocess
import ezdxf
ROOT=pathlib.Path(r'G:\My Drive\Google AI Studio\.agents')
OUT=pathlib.Path(__file__).parent
SRC=ROOT/'memory/audits/cad_v6/claude/c2_sheet_set'
manifest=json.loads((SRC/'sheet_set_manifest.json').read_text(encoding='utf8'))
rows=[]
for p in sorted(SRC.glob('*.dxf')):
 d=ezdxf.readfile(p); m=d.modelspace(); ps=d.layouts.get('Layout1')
 sheet=next(s for s in manifest['sheets'] if s['sheet_no']==p.name[:5])
 vps=[v for v in ps.query('VIEWPORT') if v.dxf.id>1]; vr=[]
 for i,v in enumerate(vps):
  c=v.dxf.center; w=v.dxf.width; h=v.dxf.height
  vr.append(dict(handle=v.dxf.handle,layer=v.dxf.layer,bbox=[c.x-w/2,c.y-h/2,c.x+w/2,c.y+h/2],actual_scale_denominator=v.dxf.view_height/h,declared_scale=sheet['viewports'][i]['scale'],frozen_layers=list(v.frozen_layers)))
 overlaps=[]
 for i,a in enumerate(vr):
  for b in vr[i+1:]:
   aa=a['bbox'];bb=b['bbox'];area=max(0,min(aa[2],bb[2])-max(aa[0],bb[0]))*max(0,min(aa[3],bb[3])-max(aa[1],bb[1]))
   if area:overlaps.append(area)
 row=dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),model_counts=dict(collections.Counter(e.dxftype() for e in m)),paper_counts=dict(collections.Counter(e.dxftype() for e in ps)),viewports=vr,viewport_overlap_mm2=overlaps,missing_sidecar=not p.with_suffix('.dce_audit.json').exists())
 row['compliance']={}
 for profile in ('physical','plan'):
  r=subprocess.run([sys.executable,str(ROOT/'skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py'),str(p),'--profile',profile],capture_output=True,encoding='utf8')
  try:
   comp=json.loads(r.stdout);row['compliance'][profile]=comp
  except Exception:row['compliance'][profile]={'error':r.stderr,'stdout':r.stdout}
 rows.append(row)
 if p.name.startswith('KC-04'):
  try:
   from ezdxf.addons.drawing import matplotlib
   matplotlib.qsave(ps,str(OUT/'KC-04_actual_paperspace.png'),dpi=120)
   row['preview']='KC-04_actual_paperspace.png'
  except Exception as e:row['preview_error']=str(e)
print(json.dumps([{k:v for k,v in r.items() if k!='compliance'} for r in rows],indent=2))
(OUT/'physical_evidence.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
# Re-run existing mutation/round-trip helpers, retaining their results separately from acceptance.
old=ROOT/'memory/audits/cad_v6/codex/a1_independent_audit.py'
spec=importlib.util.spec_from_file_location('previous_audit',old);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.AUDIT_OUT_DIR=OUT
checks={'c1':mod.audit_c1_mutation_and_manual_override(),'g2':mod.audit_g2_steel_and_semantics()}
(OUT/'mutation_roundtrip.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2,default=str),encoding='utf8')
print('C1',checks['c1']['passed'],'G2',checks['g2']['passed'])
gates={
 'structural_content':all(r['model_counts'].get('INSERT',0)>0 for r in rows),
 'viewport_nonoverlap':all(not r['viewport_overlap_mm2'] for r in rows),
 'viewport_scale':all(abs(v['actual_scale_denominator']-v['declared_scale'])<1e-6 for r in rows for v in r['viewports']),
 'face_filters':all(v['frozen_layers'] for r in rows for v in r['viewports'] if v['layer'] in ('VP_TOP','VP_BOTTOM')),
 'sidecars':all(not r['missing_sidecar'] for r in rows),
 'c1_fixture_mutations':checks['c1']['passed'],
 'g2_fixture_roundtrip':checks['g2']['passed'],
}
(OUT/'acceptance_verdict.json').write_text(json.dumps({'status':'PASS' if all(gates.values()) else 'FAIL','gates':gates},indent=2),encoding='utf8')
raise SystemExit(0 if all(gates.values()) else 1)
