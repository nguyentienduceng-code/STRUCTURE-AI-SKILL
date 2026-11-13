"""Revision-based DXF editing. Draft artifacts only; no source drawing writes.

Supported: modelspace TEXT/MTEXT translations and planar linear/aligned DIMENSION
line relocation. INSERT/ATTRIB, paper space and DWG are explicitly unsupported.
Each committed revision contains a reopened, verified DXF and SVG preview.
The HEAD file is the sole commit point; failed attempts leave HEAD unchanged.
"""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import uuid

import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def fingerprint(entity):
    # MTEXT translation materializes default axes which DXF reload can omit.
    if entity.dxftype() == 'MTEXT':
        entity = entity.copy()
        for key, default in [('extrusion', (0., 0., 1.)), ('text_direction', (1., 0., 0.))]:
            if entity.dxf.hasattr(key) and tuple(entity.dxf.get(key)) == default:
                entity.dxf.discard(key)
    tags = TagCollector.dxftags(entity)
    return repr([(t.code, t.value) for t in tags])


def render(doc, target):
    from ezdxf.addons.drawing import Frontend, RenderContext, layout
    from ezdxf.addons.drawing.svg import SVGBackend
    backend = SVGBackend()
    Frontend(RenderContext(doc), backend).draw_layout(doc.modelspace(), finalize=True)
    target.write_text(backend.get_string(layout.Page(297, 210, layout.Units.mm)), encoding='utf-8')


class ConflictError(RuntimeError):
    pass


class CadEditSession:
    def __init__(self, root):
        self.root = Path(root).resolve()

    @classmethod
    def create(cls, source, root):
        source = Path(source).resolve()
        if source.suffix.lower() != '.dxf':
            raise ValueError('DXF required; convert DWG on a separate copy first')
        doc = ezdxf.readfile(source)
        if doc.audit().errors:
            raise ValueError('Input DXF has audit errors')
        session = cls(root)
        session.root.mkdir(parents=True, exist_ok=False)
        with session._lock():
            session._commit(source, None, {'operation': 'IMPORT', 'source': str(source),
                                         'source_sha256': sha(source)})
        return session

    @contextlib.contextmanager
    def _lock(self):
        lock = self.root / '.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ConflictError('Session busy; inspect interrupted process before removing .lock')
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink()

    def _head(self, expected=None):
        head = json.loads((self.root / 'HEAD.json').read_text(encoding='utf-8'))
        if expected is not None and expected != head['revision']:
            raise ConflictError('Stale revision; inspect latest drawing before editing')
        return head

    def _revision(self, revision):
        if len(revision) != 32 or any(c not in '0123456789abcdef' for c in revision):
            raise ValueError('Invalid revision')
        folder = self.root / revision
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        if sha(folder / 'drawing.dxf') != manifest['drawing_sha256']:
            raise ConflictError('Drawing changed externally; import it into a new session')
        return folder, manifest

    def inspect(self):
        head = self._head()
        folder, manifest = self._revision(head['revision'])
        doc = ezdxf.readfile(folder / 'drawing.dxf')
        entities = []
        for e in doc.modelspace():
            kind = e.dxftype()
            item = {'handle': e.dxf.handle, 'type': kind, 'layer': e.dxf.layer,
                    'editable': kind in ('TEXT', 'MTEXT', 'DIMENSION')}
            if kind in ('TEXT', 'MTEXT'):
                item.update(text=e.dxf.text if kind == 'TEXT' else e.text,
                            position=list(e.dxf.insert))
            elif kind == 'DIMENSION':
                item.update(position=list(e.dxf.defpoint), measurement=e.get_measurement(),
                            editable=(e.dxf.dimtype & 15) in (0, 1))
            entities.append(item)
        return {'revision': head['revision'], 'status': 'DRAFT', 'entities': entities,
                'drawing': str(folder / 'drawing.dxf'), 'preview': str(folder / 'preview.svg'),
                'change': manifest['change']}

    def _commit(self, drawing, parent, change):
        revision = uuid.uuid4().hex
        folder = self.root / revision
        folder.mkdir()
        shutil.copyfile(drawing, folder / 'drawing.dxf')
        reopened = ezdxf.readfile(folder / 'drawing.dxf')
        if reopened.audit().errors:
            raise ValueError('Output DXF audit failed')
        render(reopened, folder / 'preview.svg')
        write_json(folder / 'manifest.json', {'parent': parent, 'change': change,
                   'drawing_sha256': sha(folder / 'drawing.dxf')})
        temporary = self.root / 'HEAD.tmp'
        write_json(temporary, {'revision': revision})
        os.replace(temporary, self.root / 'HEAD.json')
        return revision

    def move(self, handle, dx, dy, *, expected_revision):
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                   for v in (dx, dy)):
            raise ValueError('Finite numeric offsets required')
        with self._lock():
            head = self._head(expected_revision)
            folder, _ = self._revision(head['revision'])
            doc = ezdxf.readfile(folder / 'drawing.dxf')
            members = {e.dxf.handle: e for e in doc.modelspace()}
            e = members.get(handle.upper())
            if e is None:
                raise ValueError('Handle is not a modelspace entity')
            kind = e.dxftype()
            before = {h: fingerprint(v) for h, v in members.items() if h != e.dxf.handle}
            if kind in ('TEXT', 'MTEXT'):
                e.translate(dx, dy, 0)
            elif kind == 'DIMENSION':
                if (e.dxf.dimtype & 15) not in (0, 1) or tuple(e.dxf.extrusion) != (0., 0., 1.):
                    raise ValueError('Only planar linear/aligned dimensions supported')
                measurement = e.get_measurement()
                points = (tuple(e.dxf.defpoint2), tuple(e.dxf.defpoint3))
                e.dxf.defpoint = e.dxf.defpoint + (dx, dy, 0)
                e.render()
            else:
                raise ValueError('Only TEXT, MTEXT and linear/aligned DIMENSION can move')
            expected = fingerprint(e)
            temporary = self.root / 'candidate.dxf'
            doc.saveas(temporary)
            check = ezdxf.readfile(temporary)
            after = {v.dxf.handle: fingerprint(v) for v in check.modelspace() if v.dxf.handle != e.dxf.handle}
            if before != after or fingerprint(check.entitydb[e.dxf.handle]) != expected:
                raise ValueError('Round-trip or out-of-scope entity verification failed')
            if kind == 'DIMENSION':
                actual = check.entitydb[e.dxf.handle]
                if actual.get_measurement() != measurement or (tuple(actual.dxf.defpoint2), tuple(actual.dxf.defpoint3)) != points:
                    raise ValueError('Dimension measurement/extension origins changed')
            self._revision(head['revision'])  # reject manual changes made during rendering/edit
            revision = self._commit(temporary, head['revision'], {'operation': 'MOVE',
                                    'handle': e.dxf.handle, 'dx': dx, 'dy': dy,
                                    'verification': 'ROUND_TRIP_AND_UNSELECTED_MODELSPACE_UNCHANGED'})
            temporary.unlink()
            return revision

    def undo(self, *, expected_revision):
        with self._lock():
            head = self._head(expected_revision)
            _, manifest = self._revision(head['revision'])
            if manifest['change']['operation'] == 'UNDO':
                _, manifest = self._revision(manifest['change']['restored_revision'])
            parent = manifest['parent']
            if parent is None:
                raise ValueError('Nothing to undo')
            folder, _ = self._revision(parent)
            return self._commit(folder / 'drawing.dxf', head['revision'],
                                {'operation': 'UNDO', 'restored_revision': parent})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['create', 'inspect', 'move', 'undo'])
    p.add_argument('--session', required=True)
    p.add_argument('--source')
    p.add_argument('--revision')
    p.add_argument('--handle')
    p.add_argument('--dx', type=float, default=0)
    p.add_argument('--dy', type=float, default=0)
    a = p.parse_args()
    s = CadEditSession(a.session)
    if a.action == 'create':
        s = CadEditSession.create(a.source, a.session)
    elif a.action in ('move', 'undo'):
        if not a.revision:
            p.error('--revision is required for edits')
        if a.action == 'move':
            if not a.handle:
                p.error('--handle required')
            s.move(a.handle, a.dx, a.dy, expected_revision=a.revision)
        else:
            s.undo(expected_revision=a.revision)
    print(json.dumps(s.inspect(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
