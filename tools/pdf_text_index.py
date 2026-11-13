"""Content-addressed, lazy PDF text cache; never caches citation verdicts.

Every open hashes the source bytes (even if size/mtime are unchanged). Cache
files are disposable local artifacts, keyed by PDF content and extractor version.
Concurrent writers atomically replace complete files; lost page additions only
cause extra extraction. Cache I/O failures fall back to the source PDF.
"""
import hashlib
import json
import os
import tempfile
from collections import OrderedDict
from pathlib import Path
from importlib.metadata import version
from functools import lru_cache

_MEMORY = OrderedDict()
SCHEMA = 1


@lru_cache(maxsize=1)
def _extractor_version():
    return version('PyMuPDF')


class PDFTextIndex:
    def __init__(self, path):
        self._source = Path(path).read_bytes()
        self.sha256 = hashlib.sha256(self._source).hexdigest()
        self.key = f'{SCHEMA}-{_extractor_version()}-{self.sha256}'
        base = os.environ.get('PDF_TEXT_INDEX_CACHE_DIR')
        self.cache_dir = Path(base) if base else Path(os.environ.get('LOCALAPPDATA', tempfile.gettempdir())) / 'GoogleAIStudio' / 'pdf-text-index'
        self.path = self.cache_dir / (self.key + '.json')
        self._pdf = None
        self._dirty = False
        self.data = _MEMORY.get(self.key)
        if self.data is None:
            try:
                envelope = json.loads(self.path.read_text(encoding='utf-8'))
                payload = envelope['payload']
                if hashlib.sha256(payload.encode('utf-8')).hexdigest() != envelope['checksum']:
                    raise ValueError('Cache checksum mismatch')
                data = json.loads(payload)
                if (data['key'] != self.key or type(data['count']) is not int or data['count'] < 0
                        or type(data['needs_pass']) is not bool or not isinstance(data['pages'], dict)
                        or any(not k.isdigit() or not 0 <= int(k) < data['count'] or not isinstance(v, str)
                               for k, v in data['pages'].items())):
                    raise ValueError('Invalid text index')
                self.data = data
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                pdf = self._document()
                self.data = {'key': self.key, 'count': len(pdf), 'needs_pass': bool(pdf.needs_pass), 'pages': {}}
                self._dirty = True
        _MEMORY[self.key] = self.data
        _MEMORY.move_to_end(self.key)
        while len(_MEMORY) > 16:
            _MEMORY.popitem(last=False)

    def _document(self):
        if self._pdf is None:
            import pymupdf
            self._pdf = pymupdf.open(stream=self._source, filetype='pdf')
        return self._pdf

    @property
    def needs_pass(self):
        return self.data['needs_pass']

    def __len__(self):
        return self.data['count']

    def text(self, index):
        if not 0 <= index < len(self):
            raise IndexError(index)
        key = str(index)
        if key not in self.data['pages']:
            self.data['pages'][key] = self._document()[index].get_text()
            self._dirty = True
        return self.data['pages'][key]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self._pdf is not None:
            self._pdf.close()
        if not self._dirty:
            return
        temporary = None
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(self.data, ensure_ascii=False, sort_keys=True)
            envelope = {'payload': payload, 'checksum': hashlib.sha256(payload.encode('utf-8')).hexdigest()}
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.cache_dir, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(envelope, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError:
            pass  # A read-only/full cache must not change verification results.
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
