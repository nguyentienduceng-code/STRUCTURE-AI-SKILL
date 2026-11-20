import sys,json,shutil
from pathlib import Path
r=Path('G:/My Drive/Google AI Studio/.agents');sys.path.insert(0,str(r/'tools'))
from dce_virtual_drive_guard import configure_runtime,cleanup_preview
configure_runtime()
from dce_render_preview import render_dxf_to_png
folder=r/'memory/audits/sprint2_collision_completion_20261114'
data=json.loads((folder/'benchmark.json').read_text(encoding='utf-8'));photos=[]
for x in data:
 for state,path in [('before',x['source']),('after',x['runs'][0]['output_dxf'])]:
  res=render_dxf_to_png(path,dpi=100,view_box=(14500,33000,36500,47000))
  assert res['status']=='OK',res
  target=folder/(x['sheet']+'_'+state+'.png')
  shutil.copyfile(res['output_png'],target)
  cleanup_preview(res['preview_id'])
  photos.append(str(target))
(folder/'previews.json').write_text(json.dumps(photos,indent=2),encoding='utf-8')
print('Rendered four before/after crops')
