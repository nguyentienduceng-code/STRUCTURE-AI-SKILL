import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib, hashlib, collections, subprocess
import ezdxf
ROOT=pathlib.Path(r'G:\My Drive\Google AI Studio\.agents')
SRC=ROOT/'memory/audits/cad_v6/claude/c2_remediated'
OUT=pathlib.Path(__file__).parent
rows=[]
for p in sorted(SRC.glob('*.dxf')):
 d=ezdxf.readfile(p);m=d.modelspace();ps=d.layouts.get('Layout1'); side=json.loads(p.with_suffix('.dce_audit.json').read_text(encoding='utf8')); em=side['entity_map']
 vps=[v for v in ps.query('VIEWPORT') if v.dxf.id>1];vr=[]
 for v in vps:
  c=v.dxf.center;w=v.dxf.width;h=v.dxf.height
  vr.append({'layer':v.dxf.layer,'bbox':[c.x-w/2,c.y-h/2,c.x+w/2,c.y+h/2],'scale':v.dxf.view_height/h,'frozen':list(v.frozen_layers)})
 overlap=[]
 for i,a in enumerate(vr):
  for b in vr[i+1:]:
   x=a['bbox'];y=b['bbox'];overlap.append(max(0,min(x[2],y[2])-max(x[0],y[0]))*max(0,min(x[3],y[3])-max(x[1],y[1])))
 handles=[];missing_tags=[];missing_schedules=[]
 for eid,e in em.items():
  handles.extend(e.get('geometry_handles',[]))
  if e.get('tag_handle'):handles.append(e['tag_handle'])
  elif not eid.startswith('RS_'):missing_tags.append(eid)
  if e.get('schedule_refs') and not (e.get('schedule_handle') or e.get('schedule_handles')):missing_schedules.append(eid)
 # geometry signature excludes sheet title, includes each shape and position via DXF attributes.
 sig=[]
 for e in m:
  if e.dxftype()=='TEXT':continue
  attrs={k:str(v) for k,v in e.dxf.all_existing_dxf_attribs().items() if k not in ('handle','owner')}
  if e.dxftype()=='LWPOLYLINE':attrs['vertices']=str(list(e.get_points()))
  sig.append([e.dxftype(),attrs])
 r={'file':p.name,'hash':hashlib.sha256(p.read_bytes()).hexdigest(),'model_counts':dict(collections.Counter(e.dxftype() for e in m)), 'paper_counts':dict(collections.Counter(e.dxftype() for e in ps)), 'viewports':vr,'overlap':overlap,'resolved_handles':sum(h in d.entitydb for h in handles),'recorded_handles':len(handles),'missing_tag_entries':missing_tags,'missing_schedule_entries':missing_schedules,'missing_plate':'STEEL_PL_01' not in em,'dimstyles':dict(collections.Counter(e.dxf.dimstyle for e in m.query('DIMENSION'))),'raw_dict_attributes':[(a.dxf.handle,a.dxf.text) for i in m.query('INSERT') for a in i.attribs if a.dxf.text.startswith('{')], 'provenance_present':bool(side.get('provenance',{}).get('dxf_sha256')),'geometry_signature':hashlib.sha256(json.dumps(sig,sort_keys=True).encode()).hexdigest()}
 r['top_hash_matches']=side.get('dxf_sha256')==r['hash'];r['compliance']={}
 for profile in ('physical','plan'):
  c=subprocess.run([sys.executable,str(ROOT/'skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py'),str(p),'--profile',profile],capture_output=True,encoding='utf8')
  r['compliance'][profile]=json.loads(c.stdout)
 rows.append(r)
(OUT/'evidence.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for r in rows:print(r['file'],r['model_counts'],'scale',[v['scale'] for v in r['viewports']],'overlap',r['overlap'],'handles',r['resolved_handles'],'physical',r['compliance']['physical']['status'],'plan',r['compliance']['plan']['status'])
print('Geometry signatures',len(set(r['geometry_signature'] for r in rows)))
