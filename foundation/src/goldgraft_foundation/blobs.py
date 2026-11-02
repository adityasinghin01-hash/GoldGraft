"""Content-addressed local blobs; backend can supply the same interface for R2."""

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    def put(self, data: bytes) -> str: ...
    def get(self, ref: str) -> bytes: ...


class LocalBlobStore:
    def __init__(self, folder: str | Path = ".goldgraft/blobs"):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def path_for(self, ref: str) -> Path:
        if not re.fullmatch(r"blob://[a-f0-9]{64}", ref):
            raise ValueError("invalid local blob reference")
        return self.folder / ref.removeprefix("blob://")

    def put(self, data: bytes) -> str:
        ref = "blob://" + hashlib.sha256(data).hexdigest()
        path = self.path_for(ref)
        with tempfile.NamedTemporaryFile(dir=self.folder, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return ref

    def get(self, ref: str) -> bytes:
        return self.path_for(ref).read_bytes()
