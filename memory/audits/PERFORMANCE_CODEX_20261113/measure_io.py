"""Compare metadata traversal; local fixture mirrors names, not PDF contents."""
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'.agents/tools'))
from doc_reader import scan_project_directory

source = ROOT/'.agents'
start = time.perf_counter()
old = [(p.relative_to(source).as_posix(), p.stat().st_size, str(p.resolve()))
       for p in source.glob('**/*') if p.is_file() and not p.name.startswith(('~$', '.'))]
old_seconds = time.perf_counter()-start
start = time.perf_counter()
new = scan_project_directory(source)
new_seconds = time.perf_counter()-start
names = {p for p, size, resolved in old}
assert names == {Path(item['path']).relative_to(source).as_posix()
                 for items in new['inventory'].values() for item in items}
with tempfile.TemporaryDirectory(prefix='metadata_benchmark_') as folder:
    local = Path(folder)
    for relative in names:
        target = local/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    start = time.perf_counter()
    result = scan_project_directory(local)
    local_seconds = time.perf_counter()-start
    assert result['summary']['total_files'] == len(names)
report = {'files': len(names), 'old_drive_seconds': old_seconds,
          'scandir_drive_seconds': new_seconds, 'scandir_local_empty_mirror_seconds': local_seconds,
          'inventory_names_equal': True,
          'scope': 'Metadata traversal only; local mirror has empty files, no PDF content I/O comparison'}
Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
