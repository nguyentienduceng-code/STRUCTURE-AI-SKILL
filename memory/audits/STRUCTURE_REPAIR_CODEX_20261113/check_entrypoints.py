import json
import subprocess
import sys
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
AGENTS = OUT.parents[2]
cases = [('skills/Technical_Illustrator/cad_integration/cad_plan_engine.py', []),
         ('skills/Project_Manager/scripts/msproject_bridge.py', ['--demo', 'yen_quang'])]
results = []
with tempfile.TemporaryDirectory() as folder:
    for relative, args in cases:
        result = subprocess.run([sys.executable, str(AGENTS/relative), *args], cwd=folder,
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        results.append({'entrypoint': relative, 'exit_code': result.returncode, 'stderr': result.stderr,
                        'no_output_created': not list(Path(folder).iterdir())})
        assert result.returncode == 2 and not list(Path(folder).iterdir()), result.stderr
sys.path.insert(0, str(AGENTS/'skills/Design_Evaluation/modules'))
from script_discovery import ScriptDiscovery
discovery = ScriptDiscovery()
found = discovery.find_script('dce')
assert found
for relative, score, description in found:
    assert (Path(discovery.registry_path).parent/relative).is_file(), relative
(OUT/'entrypoints.json').write_text(json.dumps({'cli': results, 'discovery': found}, ensure_ascii=False, indent=2), encoding='utf-8')
print('CLI defaults fail safely with exit 2; discovered script paths exist.')
