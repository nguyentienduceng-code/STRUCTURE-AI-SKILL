"""Read-only independent structural inventory; writes audit evidence only."""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
AGENTS = OUT.parents[2]
ROOT = AGENTS.parent
report = {'root': str(ROOT), 'skills': [], 'archives': [], 'syntax_errors': [],
          'windows_path_literals': [], 'missing_skill_links': [], 'sources': {}}
skip = {'__pycache__', '.git', '_archive', 'archive', 'references', 'standards'}
for skill in sorted((AGENTS/'skills').iterdir()):
    if not skill.is_dir():
        continue
    entry = skill/'SKILL.md'
    if not entry.exists():
        report['skills'].append({'name': skill.name, 'entry_exists': False})
        continue
    text = entry.read_text(encoding='utf-8-sig')
    version = re.search(r'^version:\s*(.+)$', text, re.M)
    report['skills'].append({'name': skill.name, 'entry_exists': True,
                             'version': version[1] if version else None,
                             'sha256': hashlib.sha256(entry.read_bytes()).hexdigest()})
    for target in re.findall(r'\]\(([^)]+)\)', text):
        target = target.split('#')[0].strip('<>')
        if not target or '://' in target or target.startswith('#'):
            continue
        if not (skill/target).exists():
            report['missing_skill_links'].append({'file': entry.relative_to(AGENTS).as_posix(), 'target': target})
for branch in ('tools', 'skills', '_SHARED'):
    for folder, dirs, files in os.walk(AGENTS/branch):
        dirs[:] = [name for name in dirs if name not in skip]
        for name in files:
            path = Path(folder)/name
            if path.suffix != '.py':
                continue
            relative = path.relative_to(AGENTS).as_posix()
            raw = path.read_bytes()
            report['sources'][relative] = hashlib.sha256(raw).hexdigest()
            try:
                tree = ast.parse(raw.decode('utf-8-sig'), filename=str(path))
            except (SyntaxError, UnicodeError) as error:
                report['syntax_errors'].append({'file': relative, 'error': str(error)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value = node.value
                    if re.match(r'^[A-Za-z]:[/\\]', value):
                        report['windows_path_literals'].append({'file': relative, 'line': node.lineno,
                            'value': value, 'exists': Path(value).exists()})
for path in sorted((AGENTS/'_references_archived').glob('*.zip')):
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as error:
        report['archives'].append({'name': path.name, 'files': 0, 'error': str(error),
                                  'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        continue
    with archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        unsafe = [m.filename for m in members if m.filename.startswith(('/', '\\')) or '..' in Path(m.filename).parts
                  or re.match(r'^[A-Za-z]:', m.filename)]
        report['archives'].append({'name': path.name, 'files': len(members),
            'uncompressed_bytes': sum(m.file_size for m in members), 'compressed_bytes': path.stat().st_size,
            'crc_error': archive.testzip(), 'unsafe_members': unsafe,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
report['ssot_hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (ROOT/'AGENTS.md', AGENTS/'AGENTS.md', AGENTS/'skills/AGENTS.md')}
report['bus_entrypoints'] = []
for module_dir in (AGENTS/'tools', AGENTS/'skills/SKILL_DUAL_AGENT_BRIDGE/scripts'):
    for override in (False, True):
        env = dict(os.environ, PYTHONUTF8='1')
        env.pop('DUAL_AGENT_WORKSPACE', None)
        if override:
            env['DUAL_AGENT_WORKSPACE'] = str(ROOT)
        code = ('import sys,json;sys.path.insert(0,'+repr(str(module_dir))+');import sync_bus as s;'
                'print(json.dumps({"workspace":str(s.WORKSPACE_ROOT),"bus":str(s.BUS_PATH),'
                '"relative_bus":s.to_relative_path(str(s.BUS_PATH))}))')
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                                capture_output=True, text=True, encoding='utf-8')
        report['bus_entrypoints'].append({'module_dir': str(module_dir.relative_to(AGENTS)),
            'explicit_workspace': override, 'exit_code': result.returncode, 'result': json.loads(result.stdout)})
bus = json.loads((AGENTS/'memory/DUAL_AGENT_BUS.json').read_text(encoding='utf-8'))
report['stale_bus_artifacts'] = [p for p in bus['artifacts_modified'] if not (ROOT/p).exists()]
report['archive_member_total'] = sum(a['files'] for a in report['archives'])
(OUT/'structure_evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in report.items()}, indent=2))
