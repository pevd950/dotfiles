"""Repository-local atomic output, without following project-controlled links."""
import os
from pathlib import Path
import secrets
import stat


class SafeOutput:
    """Pin every parent directory; never open an existing destination for writing.

    The selected repository root is trusted. Descendant symlinks and linked or
    nonregular destinations are not. Atomic replacement also closes a leaf swap
    between validation and publication, without truncating any linked target.
    """

    def __init__(self, repo, relative):
        parts = Path(relative).parts
        if not parts or Path(relative).is_absolute() or '..' in parts:
            raise ValueError('output must be a relative path inside the repository')
        if any('\n' in part or '\r' in part for part in parts):
            raise ValueError('output path must not contain line breaks')
        self.name = parts[-1]
        if (not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY')
                or os.open not in os.supports_dir_fd):
            raise ValueError('SafeOutput requires POSIX no-follow directory descriptors')
        self.fd = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)
                os.close(self.fd)
                self.fd = child
            self.check()
        except BaseException:
            self.close()
            raise

    @staticmethod
    def check_stat(info):
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('output must be an unlinked regular file or absent')

    def check(self):
        try:
            info = os.stat(self.name, dir_fd=self.fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        self.check_stat(info)

    def read(self):
        try:
            fd = os.open(self.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        except FileNotFoundError:
            return ''
        with os.fdopen(fd, encoding='utf-8') as stream:
            self.check_stat(os.fstat(stream.fileno()))
            return stream.read()

    def write(self, content):
        self.check()
        temporary = '.env-output-' + secrets.token_hex(16)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=self.fd)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(content)
            self.check()
            os.replace(temporary, self.name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=self.fd)
            except FileNotFoundError:
                pass

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
