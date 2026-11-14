import sys,json,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
out=Path('G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114')
legacy=json.loads((out/'DbimSteelAutocad-ToanHuynh-2_calls.json').read_text(encoding='utf-8'))
current=json.loads((out/'DbimSteelAutocad_calls.json').read_text(encoding='utf-8'))
for d,label in ((legacy,'LEGACY'),(current,'CURRENT')):
    for m in d['methods']:
        c=m.get('calls',[])
        if ('TemplateCode' in m['name'] and re.search(r'::.c?ctor$',m['name'])) or re.search('DceCad::(DimRotate|ReadXData|AddTH101|AddSteelI|DrawSect|ThepI)',m['name']):
            print(label,m['token'],m['name'],'STR',m.get('strings',[])[:25],'CALL', [x for x in c if re.search('AddXdata|ReadXData|AddTag|DimRotate|Dimension|Erase|set_TextString|BlockReference',x)][:25])
    print(label,'DRAW_METHODS',[m['name'] for m in d['methods'] if re.search(r'DceCad::(Draw|Add|Ve)',m['name']) and not re.search('Text|Object|Table',m['name'])][:90])
for m in current['methods']:
    if 'DcePalette::' in m['name']:
        print('PALETTE',m['token'],m['name'],[x for x in m.get('calls',[]) if re.search('DBObjects|DBObjectCollection|ObjectEvent|ObjectErased|CommandEvent|DcePalette|DceEtabs|ObjectModified|ObjectId|Append|Erase|FrameObj|GetDbObject|Commit|Abort',x)])
        # save a curated event-call map
selection={}
for name in ('DCE_Pro','DbimSteelAutocad','DbimSteelAutocad-ToanHuynh-2','DceSteel','DceSteel-DESKTOP-BT5QG2E','DCE_Excel'):
    p=out/(name+'_calls.json')
    if not p.exists():continue
    d=json.loads(p.read_text(encoding='utf-8'))
    ms=[m for m in d['methods'] if re.search(r'DcePalette::|DceCad::(DimRotate|AddXdata|ReadXData|SetDimStyleCurrent|SetDynamicBlockProperty|BlockName|AddTH101)$|SuaThep::Button1_Click$|TemplateCode::(GandulieuKCThepBung|LayChieudayBung|SuaThepDcesteel)$|DceEvent::(DoubleClick_DCE|App_BeginDoubleClick)$|CalVolumne::TKDuLieuExcelTong$',m['name'])]
    selection[name]={'source':d['source'],'sha256':d['sha256'],'methods':ms}
(out/'curated_method_evidence.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
dwgs=json.loads((out/'dwg_summary.json').read_text(encoding='utf-8'))
compact={}
for name,d in dwgs.items():
    compact[name]={'reader_warning':76,'header':d['header'],'styles':[{k:s.get(k) for k in ('name','DIMSCALE','DIMLFAC','DIMEXO','DIMEXE','DIMTXT','DIMGAP','DIMFXL','DIMFXLON')} for s in d['styles']],
     'dynamic_dictionary_keys':d['dynamic_keys'],'blocks':[{'name':b['name'],'types':b['types'],'attribute_tags':[a.get('tag') for a in b['attdefs']]} for b in d['blocks']]}
(out/'template_catalog.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2),encoding='utf-8')
