"""Local-only scratch for the Windows DCE CAD adapter.

Policy deliberately allows only fixed NTFS/ReFS C: and D: volumes. Drive type
alone is insufficient: Google Drive reports DRIVE_FIXED on this workstation.
This is an I/O routing guard, not an OS sandbox against hostile local processes.
"""
import ctypes
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import threading
import time
import uuid

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

_ROOT = None
PREVIEW_TTL_SECONDS = 24 * 60 * 60
RENDER_LOCK = threading.RLock()  # Matplotlib uses process-global pyplot state.


class UnsafeScratchPath(ValueError):
    pass


def require_local(path):
    """Validate before mkdir/write; reject aliases, junctions and sync folders."""
    path = Path(path)
    if os.name != 'nt' or not path.is_absolute() or path.drive.upper() not in {'C:', 'D:'}:
        raise UnsafeScratchPath(f'Scratch requires an absolute local C:/D: path: {path}')
    if '..' in path.parts or any(':' in part for part in path.parts[1:]):
        raise UnsafeScratchPath(f'Unsafe path components: {path}')
    for parent in (path, *path.parents):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise UnsafeScratchPath(f'Reparse point in scratch path: {parent}')
    resolved = path.resolve()
    resolved_str = str(resolved)
    if resolved_str.startswith('\\\\?\\'):
        resolved = Path(resolved_str[4:])
    if resolved.drive.upper() not in {'C:', 'D:'}:
        raise UnsafeScratchPath(f'Alias resolves outside local C:/D: volumes: {path}')
    path = resolved
    if any(any(word in part.casefold() for word in
               ('onedrive', 'google drive', 'googledrive', 'my drive', 'dropbox'))
           for part in path.parts):
        raise UnsafeScratchPath(f'Cloud sync folder: {path}')
    for key in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        if os.environ.get(key) and path.is_relative_to(Path(os.environ[key]).resolve()):
            raise UnsafeScratchPath(f'Cloud sync root: {path}')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel.GetDriveTypeW.restype = ctypes.c_uint
    kernel.GetVolumeInformationW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
        ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_wchar_p, ctypes.c_uint]
    kernel.GetVolumeInformationW.restype = ctypes.c_int
    fs = ctypes.create_unicode_buffer(64)
    if kernel.GetDriveTypeW(path.anchor) != 3 or not kernel.GetVolumeInformationW(
            path.anchor, None, 0, None, None, None, fs, len(fs)) or fs.value.upper() not in {'NTFS', 'REFS'}:
        raise UnsafeScratchPath(f'Unverified fixed NTFS/ReFS volume: {path}')
    return path


def local_root():
    global _ROOT
    if _ROOT is not None:
        return require_local(_ROOT)
    candidates = []
    if os.environ.get('DCE_CAD_SCRATCH_ROOT'):
        candidates.append(Path(os.environ['DCE_CAD_SCRATCH_ROOT']))
    # Do not call gettempdir() until validated: its probe may itself write to G:.
    for value in (tempfile.tempdir, os.environ.get('TEMP'), os.environ.get('TMP'),
                  os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
                  str(Path.home() / 'AppData' / 'Local' / 'Temp'), r'C:\Windows\Temp', r'D:\Temp'):
        if value:
            candidates.append(Path(value) / 'dce-cad')
    errors = []
    for candidate in candidates:
        try:
            root = require_local(candidate)
            root.mkdir(parents=True, exist_ok=True)
            require_local(root)
            with tempfile.TemporaryFile(dir=root):
                pass
            _ROOT = root
            return root
        except (OSError, UnsafeScratchPath) as error:
            errors.append(str(error))
    raise UnsafeScratchPath('No safe writable scratch directory; refusing I/O: ' + '; '.join(errors))


def managed_dir(name):
    if name not in {'previews', 'sessions', 'matplotlib', 'temp'}:
        raise ValueError('Unknown scratch category')
    path = require_local(local_root() / name)
    path.mkdir(parents=True, exist_ok=True)
    return require_local(path)


def configure_runtime():
    """Run before ezdxf/matplotlib imports; keep library caches off Drive too."""
    sys.dont_write_bytecode = True
    temp = managed_dir('temp')
    tempfile.tempdir = str(temp)
    os.environ.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
                      MPLCONFIGDIR=str(managed_dir('matplotlib')),
                      PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg')
    return local_root()


def session_path(requested=''):
    """Stable mapping for cloud/relative session names; local paths stay local."""
    if requested:
        try:
            return require_local(requested)
        except (OSError, UnsafeScratchPath):
            key = os.path.normcase(os.path.abspath(requested))
            name = hashlib.sha256(key.encode('utf-8')).hexdigest()
    else:
        name = uuid.uuid4().hex
    return require_local(managed_dir('sessions') / name)


def preview_path(preview_id):
    if not isinstance(preview_id, str) or not re.fullmatch(r'[0-9a-f]{32}', preview_id):
        raise ValueError('Invalid preview_id')
    return require_local(managed_dir('previews') / preview_id / 'preview.png')


def allocate_preview():
    sweep_previews()
    preview_id = uuid.uuid4().hex
    path = preview_path(preview_id)
    path.parent.mkdir(exist_ok=False)
    return preview_id, path


def finish_preview(preview_id):
    path = preview_path(preview_id)
    if not path.is_file() or path.stat().st_size == 0:
        raise OSError('Renderer produced no PNG')
    require_local(path.parent / '.ready').touch()


def cleanup_preview(preview_id):
    """Delete only our known files, never recursively delete a caller path."""
    path = preview_path(preview_id)
    try:
        for target in (path, path.parent / '.ready'):
            require_local(target)
            for attempt in range(3):
                try:
                    target.unlink(missing_ok=True)
                    break
                except PermissionError:
                    if attempt == 2:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        if path.parent.exists():
            path.parent.rmdir()
    except OSError as error:
        return {'status': 'CLEANUP_PENDING', 'preview_id': preview_id, 'error': str(error)}
    return {'status': 'CLEANED', 'preview_id': preview_id}


def sweep_previews():
    """Lazy TTL fallback for abandoned completed previews; never touch sessions."""
    results = []
    for folder in managed_dir('previews').iterdir():
        if not re.fullmatch(r'[0-9a-f]{32}', folder.name):
            continue
        try:
            ready = require_local(folder / '.ready')
            if ready.is_file() and time.time() - ready.stat().st_mtime > PREVIEW_TTL_SECONDS:
                results.append(cleanup_preview(folder.name))
        except (OSError, UnsafeScratchPath):
            continue
    return results


def consume_preview_bytes(preview_id):
    """Load fully into memory, then release disk backing before Vision delivery."""
    path = preview_path(preview_id)
    if not require_local(path.parent / '.ready').is_file():
        raise ValueError('Preview is not ready or was already consumed')
    data = path.read_bytes()  # read_bytes closes the handle before unlink (Windows).
    result = cleanup_preview(preview_id)
    if result['status'] != 'CLEANED':
        raise OSError(result['error'])
    return data
