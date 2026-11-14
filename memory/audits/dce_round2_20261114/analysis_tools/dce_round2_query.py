import json,sys,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
if sys.argv[1]=='dwg':
    d=json.loads((out/'dwg_summary.json').read_text(encoding='utf-8'))
    for key in ('Form 2.dwg','Form 2_Steel.dwg','Form 1_Steel.dwg'):
        x=d[key]
        print('TEMPLATE',key)
        print('STYLES',[{k:s.get(k) for k in ('name','DIMSCALE','DIMLFAC','DIMEXO','DIMEXE','DIMTXT','DIMFXLON')} for s in x['styles'] if s['name'] in ('Dce_20MV','Dce_50MV','Dce_100MV','Dce_200MV')])
        for b in x['blocks']:
            if not b['name'].startswith('*'):
                print('BLOCK',b['name'],b['types'],'ATTRS',[(a.get('tag'),a.get('text')) for a in b['attdefs']])
    sys.exit()
name=sys.argv[1];pattern=sys.argv[2]
d=json.loads((out/(name+'_calls.json')).read_text(encoding='utf-8'))
ms=[m for m in d['methods'] if re.search(pattern,m['name'],re.I)]
for m in ms[:40]:
    print(m['token'],m['name'],'RVA',m['rva'],'EH',m.get('exception_handlers'),'CALLS',len(m.get('calls',[])))
    for c in m.get('calls',[]):
        if not re.search('^wuqY|NewLateBinding|Conversions|Operators|GetObjectValue|^token\(',c):print(' CALL',c)
    if len(sys.argv)>3:
        bodies=json.loads((out/(name+'_il.json')).read_text(encoding='utf-8'))
        for i in bodies.get(m['token'],{}).get('instructions',[]):print(i['offset'],i['op'],i['arg'])
