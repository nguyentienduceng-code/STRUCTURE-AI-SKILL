import sys,json,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
sys.path.insert(0,'C:/Users/ADMIN/AppData/Local/Temp/dce_round2_analysis_tools')
import dnfile
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
pe=dnfile.dnPE('C:/Dce Pro/AddinSteelCad/DbimSteelAutocad-ToanHuynh-2.dll')
for t in pe.net.mdtables.TypeDef:
    for idx in t.MethodList:
        m=idx.row
        if re.search(r'GandulieuKCThepBung|LayChieudayBung|DimRotate|DrawISection|DrawSectI|VeThepI|AddXdata',str(m.Name)):
            print('PARAMS',str(t.TypeName),str(m.Name),[(p.row.Sequence,str(p.row.Name)) for p in m.ParamList])
d=json.loads((out/'form2_dxf_authoritative.json').read_text(encoding='utf-8'))
print('DXF_HEADER',d['header']);print('DXF_MAIN_STYLES',[{k:s.get(k) for k in ('name','dimscale','dimlfac','dimexo','dimexe','dimtxt')} for s in d['styles'] if s['name'] in ('Dce_20MV','Dce_50MV','Dce_100MV','Dce_200MV')])
for b in d['blocks']:
    if b['name'] in ('TK1','TK9','TenCauKien','Dce_KhTenTruc','DCE_BlockBeam2','DceCot'):
        print('DXF_BLOCK',b['name'],b['base'],b['types'],[a.get('tag') for a in b['attdefs']])
dwgs=json.loads((out/'dwg_summary.json').read_text(encoding='utf-8'))
for key in ('Form 2.dwg','Form 2_Steel.dwg'):
    print('DWG_NAMED',key,[b['name'] for b in dwgs[key]['blocks'] if not b['name'].startswith('*')])
    for b in dwgs[key]['blocks']:
        if b['name'] in ('TH101','TH102','Dce-ThepTam','Dce_BeamI1','Dce_MBolt','Dce_giangxago','Dce_SectionI','M20','TK1'):
            print('STEEL_BLOCK',b['name'],b['types'],[a.get('tag') for a in b['attdefs']])
for rel in ('DBimApps.cuix','MenuDCE.cuix'):
    import zipfile
    with zipfile.ZipFile('C:/Dce Pro/'+rel) as z:
        print('DOUBLECLICK_CUIX',rel,z.read('DoubleClickRoot.cui').decode('utf-8')[:6000])
pe.close()
