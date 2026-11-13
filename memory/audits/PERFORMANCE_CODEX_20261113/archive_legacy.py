"""Archive only the six completed 20261112 audit runs, verify every member."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['CODEX_20261112', 'CODEX_ROUND2_20261112', 'CODEX_ROUND3_20261112',
         'CODEX_REPAIR_20261112', 'COGNITIVE_V2_20261112', 'DOC_READER_V3_20261112']
destination = ROOT/'archive'
destination.mkdir(exist_ok=True)
archive = destination/'audits_20261112.zip'
manifest = []
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as out:
    for name in NAMES:
        directory = (ROOT/name).resolve()
        assert directory.parent == ROOT and directory.is_dir()
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                data = path.read_bytes()
                relative = path.relative_to(ROOT).as_posix()
                out.writestr(relative, data)
                manifest.append({'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
with zipfile.ZipFile(archive) as saved:
    assert saved.testzip() is None
    assert len(saved.namelist()) == len(manifest)
    for item in manifest:
        assert hashlib.sha256(saved.read(item['path'])).hexdigest() == item['sha256']
report = {'archive': archive.name, 'verified': True, 'file_count': len(manifest),
          'source_bytes': sum(item['bytes'] for item in manifest), 'archive_bytes': archive.stat().st_size,
          'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'directories': NAMES, 'files': manifest}
(destination/'audits_20261112.manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'files'}))
