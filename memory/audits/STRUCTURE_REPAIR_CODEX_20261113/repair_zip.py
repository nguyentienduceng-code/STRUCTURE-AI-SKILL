"""Rebuild a missing ZIP directory only when every local entry validates."""
import hashlib
import json
import os
import struct
import zipfile
import zlib
from pathlib import Path, PurePosixPath

OUT = Path(__file__).resolve().parent
source = OUT.parents[2]/'_references_archived/rvt-mcp.zip'
data = source.read_bytes()
backup = OUT/'rvt-mcp.original.damaged'
with backup.open('xb') as stream:
    stream.write(data)
entries, manifest, position = [], [], 0
while position < len(data):
    assert data[position:position+4] == b'PK\x03\x04', 'Unexpected bytes; cannot certify complete recovery'
    header = struct.unpack_from('<IHHHHHIIIHH', data, position)
    _, version, flags, method, time, date, crc, compressed, size, namesize, extrasize = header
    assert not flags & (1 | 8), 'Encrypted/descriptor entries require separate recovery'
    name = data[position+30:position+30+namesize].decode('utf-8' if flags & 2048 else 'cp437')
    assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and ':' not in name
    start = position+30+namesize+extrasize
    assert start+compressed <= len(data)
    raw = data[start:start+compressed]
    assert method in (0, 8)
    content = zlib.decompress(raw, -15) if method == 8 else raw
    assert len(content) == size and zlib.crc32(content) == crc, name
    entries.append((name, content))
    manifest.append({'path': name, 'bytes': size, 'crc32': crc, 'sha256': hashlib.sha256(content).hexdigest()})
    position = start+compressed
assert len({name for name, _ in entries}) == len(entries)
temporary = source.with_suffix('.repair.tmp')
with zipfile.ZipFile(temporary, 'x', zipfile.ZIP_DEFLATED) as archive:
    for name, content in entries:
        archive.writestr(name, content)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    for item in manifest:
        assert hashlib.sha256(archive.read(item['path'])).hexdigest() == item['sha256']
record = {'recovered_entries': len(entries), 'all_original_bytes_consumed': position == len(data),
          'original_sha256': hashlib.sha256(data).hexdigest(),
          'repaired_sha256': hashlib.sha256(temporary.read_bytes()).hexdigest(),
          'scope': 'All local entries present in damaged archive recovered and verified. Pre-archive repository completeness is unknown.',
          'original_backup': str(backup), 'files': manifest}
source.with_suffix('.manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
os.replace(temporary, source)
print(json.dumps({k:v for k,v in record.items() if k != 'files'}))
