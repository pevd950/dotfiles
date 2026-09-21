"""Private cache primitives shared by the transcript puller and local reader."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


def private_dir(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Cache paths must not contain symlinks")
    for parent in reversed((path, *path.parents)):
        if not parent.exists():
            parent.mkdir(mode=0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("Cache directory must be owned and mode 0700")
    return path


def private_file(path):
    path = Path(path)
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077 or info.st_nlink != 1):
        raise ValueError("Expected an owned private regular file")
    return path


def cache_path(root, relative):
    if not isinstance(relative, str) or not relative or "\0" in relative:
        raise ValueError("Invalid cache-relative path")
    parts = relative.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise ValueError("Invalid cache-relative path")
    path = root.joinpath(*parts)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink in cache path")
    return path


def read_json(path):
    return json.loads(private_file(path).read_text())


def write_json(path, value):
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def signature(path):
    info = private_file(path).stat()
    return (info.st_size, info.st_mtime_ns)


def file_hash(path):
    digest = hashlib.sha256()
    with private_file(path).open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def locked_cache(path):
    root = private_dir(path)
    lock = root / ".lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        private_file(lock)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield root
    finally:
        os.close(fd)
