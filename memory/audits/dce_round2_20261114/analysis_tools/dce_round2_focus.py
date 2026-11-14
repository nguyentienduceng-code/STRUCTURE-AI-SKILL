import sys,json,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
legacy=json.loads((out/'DbimSteelAutocad-ToanHuynh-2_calls.json').read_text(encoding='utf-8'))
current=json.loads((out/'DbimSteelAutocad_calls.json').read_text(encoding='utf-8'))
names=[m['name'] for m in legacy['methods']]
for pat in ('Dim|SuaThep|DrawBase|DrawI|DrawU|DrawV|Weld|BuLong|Bolt|Gusset','ReadXData|Xdata|XData','DcePalette|DceEvent|DoubleClick'):
    print('METHOD_NAMES',pat,[n for n in names if re.search(pat,n)][:120])
for m in legacy['methods']:
    if re.search(r'DceCad::(ReadXData|DimRotate|AddDynamic|SetDynamicBlockProperty)$|SuaThep::Button1_Click$|DcePalette::|TemplateCode::SuaThepDcesteel$',m['name']):
        print('DETAIL',m['token'],m['name'],'STR',m.get('strings'), 'CALLS', [c for c in m.get('calls',[]) if not re.search('NewLateBinding|Conversions|Operators|GetObjectValue',c)])
print('SELECTEDCALLERS')
for m in legacy['methods']:
    c=m.get('calls',[])
    if any(re.search(r'AddXdata$|ReadXData$|::DimRotate$|::Erase$|::Show$|::AddCircle$|::AddPoly$|::AddTagBlock$',x) for x in c):
        if re.search(r'TemplateCode|DrawBasePlate|DrawBanBich|DrawSteel|Connection|SuaThep',m['name']):
            print(m['token'],m['name'],'STR',m.get('strings',[])[:25], 'CALLS',[x for x in c if re.search(r'AddXdata|ReadXData|DimRotate|Erase|Show$|AddCircle|AddPoly|AddTagBlock|Commit|Abort|Undo',x)])
# DXF authoritative snapshot, never save to source.
import ezdxf
d=ezdxf.readfile('C:/Dce Pro/Cad/Form 2.dxf')
dx={'version':d.dxfversion,'header':{k:d.header.get(k) for k in ('$DIMSCALE','$DIMLFAC','$DIMASSOC','$DIMSTYLE','$INSUNITS')},
    'styles':[s.dxfattribs() for s in d.dimstyles],
    'blocks':[{'name':b.name,'base':list(b.block.dxf.base_point),'types':dict(collections.Counter(e.dxftype() for e in b)),
               'attdefs':[e.dxfattribs() for e in b if e.dxftype()=='ATTDEF']} for b in d.blocks],
    'msp_types':dict(collections.Counter(e.dxftype() for e in d.modelspace()))}
(out/'form2_dxf_authoritative.json').write_text(json.dumps(dx,default=str,ensure_ascii=False,indent=2),encoding='utf-8')
print('DXFHEADER',dx['header']);print('DXFSTYLES',[{k:s.get(k) for k in ('name','dimscale','dimlfac','dimexo','dimexe','dimtxt')} for s in dx['styles'] if s['name'].lower().startswith('dce')])
summary=json.loads((out/'dwg_summary.json').read_text(encoding='utf-8'))
for name in ('Form 2.dwg','Form 2_Steel.dwg'):
    blocks=[b for b in summary[name]['blocks'] if not b['name'].startswith('*')]
    print('NAMED_BLOCKS',name,[(b['name'],b['types'],[(a.get('tag'),a.get('text')) for a in b['attdefs']]) for b in blocks if re.search('TK|THEP|STEEL|I[0-9]|U[0-9]|V[0-9]|M[0-9]|Bul|Bolt|Han|Ma|Cot|Coc|Dam|TH|Ten|Xag',b['name'],re.I)][:95])
