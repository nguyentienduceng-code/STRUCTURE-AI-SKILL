import sys,json,re,hashlib,collections,zipfile
from pathlib import Path
from tempfile import gettempdir
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(gettempdir()) / 'dce_round2_analysis_tools'))
import dnfile
from dncil.cil.body.reader import read_method_body_from_bytes
from dncil.clr.token import Token,StringToken
out=Path(__file__).resolve().parents[1];out.mkdir(parents=True,exist_ok=True)
root=Path('C:/Dce Pro')
def manifest():
    result={}
    for p in root.rglob('*'):
        if p.is_file():
            st=p.stat()
            with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
            result[str(p.relative_to(root))]={'size':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':h}
    return result
if '--verify' in sys.argv:
    a=json.loads((out/'source_before.json').read_text(encoding='utf-8'));b=manifest()
    changes=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
    (out/'source_integrity.json').write_text(json.dumps({'files':len(b),'changes':changes,'unchanged':not changes},indent=2),encoding='utf-8')
    print('INTEGRITY',len(b),changes);sys.exit(bool(changes))
if not (out/'source_before.json').exists():(out/'source_before.json').write_text(json.dumps(manifest(),indent=2),encoding='utf-8')
targets=['DCE Pro.dll','AddinSteelCad/DbimSteelAutocad.dll','AddinSteel/DceSteel.dll','V.2020/DCE Excel.dll']
if len(sys.argv)>1:targets=[sys.argv[1]]
for rel in targets:
    p=root/rel; print('START',rel,flush=True)
    pe=dnfile.dnPE(str(p)); tables=pe.net.mdtables
    owner={}
    for t in tables.TypeDef:
        typename=str(t.TypeNamespace)+'.'+str(t.TypeName)
        for m in t.MethodList:owner[id(m.row)]=typename
    def resolve(tok):
        if isinstance(tok,StringToken):
            item=pe.net.user_strings.get(tok.rid)
            return str(item) if item is not None else '<missing string>'
        if not isinstance(tok,Token):return str(tok) if tok is not None else ''
        table=tables.tables.get(tok.table)
        if table is None or tok.rid<1 or tok.rid>len(table.rows):return str(tok)
        row=table.rows[tok.rid-1]
        if tok.table==6:return owner.get(id(row),'')+'::'+str(row.Name)
        if tok.table==10:
            par=row.Class.row
            prefix=str(getattr(par,'TypeNamespace',''))+'.'+str(getattr(par,'TypeName',getattr(par,'Name','')))
            return prefix+'::'+str(row.Name)
        if tok.table in (1,2):return str(row.TypeNamespace)+'.'+str(row.TypeName)
        if tok.table==43:return resolve(Token((row.Method.table.number<<24)|row.Method.row_index))
        return str(getattr(row,'Name',tok))
    methods=[]; bodies={}; errors=[]
    # Decode all method calls, not byte-pattern guesses for opcodes.
    for rid,m in enumerate(tables.MethodDef,1):
        name=owner.get(id(m),'')+'::'+str(m.Name)
        rec={'token':hex(0x06000000|rid),'name':name,'rva':m.Rva}
        if m.Rva:
            try:
                body=read_method_body_from_bytes(pe.get_data(m.Rva, min(2000000,len(pe.__data__)) ))
                instructions=[{'offset':i.offset,'op':str(i.opcode.name),'arg':resolve(i.operand)} for i in body.instructions]
                calls=[i['arg'] for i in instructions if i['op'] in ('call','callvirt','newobj')]
                strings=[i['arg'] for i in instructions if i['op']=='ldstr']
                rec.update(calls=calls,strings=strings,exception_handlers=len(body.exception_handlers))
                interesting=re.search(r'xdata|xrecord|dictionary|GanDL|Gandulieu|LayChieu|TKThep|DceRebar|Sua|DoubleClick|Dim|Bolt|BuLong|BanMa|Weld|Gusset|Rafter|Column|KNEE|TietDien|Undo',name,re.I)
                api=re.search(r'XData|Xrecord|Dictionary|DynamicBlock|DoubleClick|BeginDoubleClick|SetSystemVariable|ShowDialog|ShowModalDialog|SetDimstyleData', '\n'.join(calls),re.I)
                if interesting or api:bodies[rec['token']]={'name':name,'instructions':instructions}
            except Exception as e:errors.append({'name':name,'error':str(e)})
        methods.append(rec)
    result={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'methods':methods,'errors':errors}
    key=p.stem.replace(' ','_')
    (out/(key+'_calls.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/(key+'_il.json')).write_text(json.dumps(bodies,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',rel,len(methods),'bodies',len(bodies),'errors',len(errors),flush=True)
    for m in methods:
        if re.search(r'AddXdata|DocXdata|DceRebarXDataTKT|DoubleClick|SuaThep|SuaCK|GanXDataChoCauKien',m['name'],re.I):print(m['token'],m['name'],m.get('strings',[])[:12],flush=True)
    pe.close()
