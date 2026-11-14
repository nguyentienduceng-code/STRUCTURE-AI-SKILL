import sys,json,re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
d=json.loads((out/'DbimSteelAutocad-ToanHuynh-2_calls.json').read_text(encoding='utf-8'))
for m in d['methods']:
    if re.search(r'DceCad::(Draw_MCN_I|Draw_MCN_U|Draw_MCN_Pipe|DrawSectV|DrawBolt|AddTagBlock|ReadBlock|AddTH101)$|Connection::Dim1$|CalVolumne::TKDuLieuExcelTong$',m['name']):
        print(m['token'],m['name'],'STR',m.get('strings',[])[:12],
              'CALL',[c for c in m.get('calls',[]) if re.search('DceCad|Attribute|Dimension|Matrix|BlockReference|DynamicBlock',c)][:25])
print('ERASE_REBUILD')
for m in d['methods']:
    calls=m.get('calls',[])
    if any('::Erase' in c for c in calls) and any(re.search('DceCad::(Draw|Add)',c) for c in calls):
        print(m['token'],m['name'],[c for c in calls if re.search('Erase|DceCad::(Draw|Add)|Commit',c)][:10])
