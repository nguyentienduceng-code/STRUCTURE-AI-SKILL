import json,collections,re,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
summaries={}
for p in out.glob('Form*.dwg.json'):
    d=json.loads(p.read_text(encoding='utf-8'));tabs=d['tables'];blocks=tabs['BLOCK_RECORD']['entries'];styles=tabs['DIMSTYLE']['entries']
    sel=[s for s in styles if re.search('Dce|DCE|Steel',s['name'])]
    # Recursively record dictionary keys and xdata, never equate anonymous blocks with dynamic.
    dynamic=[];xdata=[]
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if re.search('ENHANCEDBLOCK|BLOCKREPRESENTATION|ACAD_ASSOC|DYNAMIC',str(k),re.I):dynamic.append(str(k))
                if k=='xdata' and v:xdata.append(v)
                walk(v)
        elif isinstance(o,list):
            for x in o:walk(x)
    walk(d)
    bs=[]
    for b in blocks:
        ents=b.get('entities',[])
        bs.append({'name':b['name'],'types':dict(collections.Counter(e.get('type') for e in ents)),
            'attdefs':[e for e in ents if e.get('type')=='ATTDEF'],'handle':b.get('handle')})
    summary={'parse_warning':76,'header':{k:v for k,v in d['header'].items() if re.search('DIM|INSUNITS|LTSCALE',k,re.I)},'styles':sel,
             'blocks':bs,'dynamic_keys':list(set(dynamic)),'classes':[c for c in d.get('classes',[]) if re.search('BLOCK|ASSOC',str(c),re.I)],
             'xdata_samples':xdata[:12]}
    summaries[p.stem]=summary
    print('DWG',p.stem,'BLOCKS',len(blocks),'STYLES',[s['name'] for s in sel],'DYNAMIC',summary['dynamic_keys'],flush=True)
    if '2_Steel' in p.stem:
        print('STEEL_HEADER',json.dumps(summary['header']));print('STEEL_STYLES',json.dumps(sel[:8]));print('STEEL_BLOCKS',json.dumps(bs,ensure_ascii=False)[:18000])
(out/'dwg_summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ('DCE_Pro','DbimSteelAutocad','DceSteel','DCE_Excel'):
    p=out/(name+'_calls.json')
    if not p.exists():continue
    d=json.loads(p.read_text(encoding='utf-8'))
    patterns=r'AddXdata|DocXdata|DoubleClick|SuaCKThep|SetDim|DrawDim|DrawBolt|DrawISection|DrawSection|LKKNEE|GanDLApplication|GanXDataChoCauKien|UpdateBlock'
    selected=[m for m in d['methods'] if re.search(patterns,m['name'],re.I) and len(m.get('calls',[]))>0]
    print('IL_TARGETS',name,json.dumps(selected,ensure_ascii=False)[:24000])
    # Every method that touches relevant APIs, including obfuscated callers.
    groups={}
    for label,regex in {'xdata':'set_XData|GetXDataForApplication|ResultBuffer|TypedValue',
        'dict':'Xrecord|ExtensionDictionary|CreateExtensionDictionary',
        'dynamic':'DynamicBlockReferenceProperty|IsDynamicBlock|DynamicBlockTableRecord',
        'dim':'set_Dimscale|set_Dimlfac|set_Dimexo|set_Dimexe|set_Dimassoc|SetSystemVariable',
        'ui':'ShowDialog|ShowModalDialog|BeginDoubleClick|add_ObjectModified|add_CommandEnded',
        'draw':'AlignedDimension::.ctor|RotatedDimension::.ctor|Circle::.ctor|Polyline::.ctor'}.items():
        ms=[{'token':m['token'],'name':m['name'],'calls':[c for c in m.get('calls',[]) if re.search(regex,c,re.I)],'strings':m.get('strings',[])} for m in d['methods'] if any(re.search(regex,c,re.I) for c in m.get('calls',[]))]
        groups[label]=ms
        print('API',name,label,len(ms),json.dumps(ms[:10],ensure_ascii=False)[:8000])
    (out/(name+'_api_evidence.json')).write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf-8')
