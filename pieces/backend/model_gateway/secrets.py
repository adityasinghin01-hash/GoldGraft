"""Owner-only bounded local custody; values never leave provider/signing boundaries."""

import os
import stat
from pathlib import Path


def private_bytes(path, *, maximum=16384):
    path = Path(path)
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("UNSAFE_SECRET_FILE")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            meta = os.fstat(fd)
            if (
                not stat.S_ISREG(meta.st_mode)
                or meta.st_uid != os.getuid()
                or stat.S_IMODE(meta.st_mode) != 0o600
                or meta.st_size > maximum
            ):
                raise ValueError("UNSAFE_SECRET_FILE")
            data = os.read(fd, maximum + 1)
            if len(data) > maximum:
                raise ValueError("UNSAFE_SECRET_FILE")
            return data
        finally:
            os.close(fd)
    except OSError:
        raise ValueError("SECRET_CONFIGURATION_UNAVAILABLE") from None


def api_key(path):
    try:
        entries = [
            line.partition("=")[2].strip().strip("\"'")
            for line in private_bytes(path).decode().splitlines()
            if line.startswith("ANTHROPIC_API_KEY=")
        ]
    except UnicodeError:
        raise ValueError("SECRET_CONFIGURATION_INVALID") from None
    if len(entries) != 1 or not entries[0].startswith("sk-ant-"):
        raise ValueError("SECRET_CONFIGURATION_INVALID")
    return entries[0]


def signing_key(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "wb") as stream:
            stream.write(os.urandom(32))
            stream.flush()
            os.fsync(stream.fileno())
    data = private_bytes(path, maximum=32)
    if len(data) != 32:
        raise ValueError("INVALID signing key")
    return data
