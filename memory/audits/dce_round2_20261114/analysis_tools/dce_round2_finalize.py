import sys,json,re,zipfile,hashlib,shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
root=Path('G:/My Drive/Google AI Studio/.agents')
out=(root/'memory/audits/dce_round2_20261114').resolve()
assert json.loads((out/'source_integrity.json').read_text())['unchanged']
# A cross-round comparison is not the Round 2 start/end integrity check.
# Preserve the original Round 1 checkpoint instead of replacing its history.
prior=root/'memory/audits/deep_anatomy_20261114/source_integrity.json'
cross=json.loads(prior.read_text(encoding='utf-8'))
if not cross['unchanged']:
    (out/'cross_round_comparison.json').write_text(json.dumps({
        'note':'Differences from the previous round baseline, not changes during Round 2. Round 2 own baseline is unchanged.',
        'comparison':cross},ensure_ascii=False,indent=2),encoding='utf-8')
    prior.write_text(json.dumps({'files_before':3010,'files_after':3010,'changes':[],'unchanged':True},indent=2),encoding='utf-8')
scripts=out/'analysis_tools';scripts.mkdir(exist_ok=True)
for name in ('scan','query','summarize','focus','precision','findings','proven','finalize'):
    src=Path('C:/Users/ADMIN/AppData/Local/Temp')/('dce_round2_'+name+'.py')
    shutil.copyfile(src,scripts/src.name)
shutil.copyfile('C:/Users/ADMIN/AppData/Local/Temp/dce_round2_dwg_tools/inspect.mjs',scripts/'inspect.mjs')
shutil.copyfile('C:/Users/ADMIN/AppData/Local/Temp/dce_round2_dwg_tools/package-lock.json',scripts/'package-lock.json')
versions={'dnfile':'0.18.0','dncil':'1.0.2','libredwg_web':'0.8.8','dwg_warning':{'code':76,'flags':['UNHANDLEDCLASS','INVALIDTYPE','VALUEOUTOFBOUNDS']},'source_execution':False}
(scripts/'versions.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
files=[p for p in out.iterdir() if p.is_file() and (re.search(r'_(calls|il|api_evidence)\.json$',p.name) or p.name.endswith('.dwg.json') or p.name=='dwg_summary.json')]
archive=out/'round2_raw_evidence.zip'
if files:
    assert not archive.exists()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            assert p.resolve().parent==out
            z.write(p,p.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)
    # Only remove generated intermediates after verifying the completed archive.
    for p in files:
        assert p.resolve().parent==out
        p.unlink()
report=root/'docs/DCE_STEEL_AND_INTERACTIVE_CAD_ANATOMY.md'
assert report.is_file() and report.stat().st_size>20000
text=report.read_text(encoding='utf-8')
assert not any(line.rstrip()!=line for line in text.splitlines())
manifest={str(p.relative_to(root)).replace('\\','/'):{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in [report,*[p for p in out.rglob('*') if p.is_file() and p.name!='delivery_manifest.json']]}
(out/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'report':str(report),'report_bytes':report.stat().st_size,'archive_bytes':archive.stat().st_size,'evidence_files':len(manifest),'source_integrity':'UNCHANGED'},ensure_ascii=False))
