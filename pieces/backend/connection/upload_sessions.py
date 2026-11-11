"""Bounded, checksum-verified chunked uploads with optional restart recovery."""

import hashlib
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock


@dataclass
class UploadChunk:
    chunk_index: int
    sha256: str
    byte_count: int


@dataclass
class UploadSession:
    session_id: str
    case_id: str
    filename: str
    total_chunks: int
    expected_sha256: str
    received_chunks: dict[int, UploadChunk] = field(default_factory=dict)
    completed: bool = False
    cancelled: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class UploadSessionManager:
    """Stores chunks transactionally. Pass a private database path to resume after restart."""

    def __init__(self, max_size_bytes: int = 50 * 1024 * 1024, *, database: Path | None = None):
        if max_size_bytes <= 0:
            raise ValueError("Upload size limit must be positive")
        self.max_size_bytes = max_size_bytes
        self._lock = Lock()
        self._views: dict[str, UploadSession] = {}
        self._db = sqlite3.connect(database if database is not None else ":memory:",
                                   check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS uploads (
                session_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, filename TEXT NOT NULL,
                total_chunks INTEGER NOT NULL, expected_sha256 TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0, cancelled INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS upload_chunks (
                session_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,
                sha256 TEXT NOT NULL, data BLOB NOT NULL,
                PRIMARY KEY (session_id, chunk_index)
            );
        """)

    @contextmanager
    def _write(self):
        with self._lock, self._db:
            self._db.execute("BEGIN IMMEDIATE")
            yield

    def _active(self, session_id: str) -> sqlite3.Row:
        session = self._db.execute(
            "SELECT * FROM uploads WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not session or session["cancelled"]:
            raise ValueError("Upload session is not active")
        return session

    def create_session(
        self, case_id: str, filename: str, total_chunks: int, expected_sha256: str
    ) -> UploadSession:
        if (
            type(total_chunks) is not int
            or not 1 <= total_chunks <= min(self.max_size_bytes, 10_000)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
        ):
            raise ValueError("Invalid upload chunk count or SHA-256 digest")
        raw = repr((case_id, filename, total_chunks, expected_sha256)).encode()
        session_id = f"upload-{hashlib.sha256(raw).hexdigest()[:24]}"
        with self._write():
            self._db.execute(
                "INSERT OR IGNORE INTO uploads "
                "(session_id, case_id, filename, total_chunks, expected_sha256, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, case_id, filename, total_chunks, expected_sha256,
                 datetime.now(UTC).isoformat()),
            )
            session = dict(self._active(session_id))
            chunks = self._db.execute(
                "SELECT chunk_index, sha256, length(data) FROM upload_chunks WHERE session_id = ?",
                (session_id,),
            )
            session["received_chunks"] = {row[0]: UploadChunk(*row) for row in chunks}
            session["completed"] = bool(session["completed"])
            session["cancelled"] = bool(session["cancelled"])
            self._db.commit()
            view = self._views.setdefault(session_id, UploadSession(**session))
            view.received_chunks = session["received_chunks"]
            view.completed = session["completed"]
            return view

    def add_chunk(self, session_id: str, chunk_index: int, data: bytes) -> UploadChunk:
        with self._write():
            session = self._active(session_id)
            if session["completed"]:
                raise ValueError("Upload session is not active")
            if type(chunk_index) is not int or not 0 <= chunk_index < session["total_chunks"]:
                raise ValueError("Upload chunk index is out of range")
            if not data:
                raise ValueError("Upload chunks must be nonempty")
            old = self._db.execute(
                "SELECT sha256, data FROM upload_chunks WHERE session_id = ? AND chunk_index = ?",
                (session_id, chunk_index),
            ).fetchone()
            if old is not None:
                if old["data"] != data:
                    raise ValueError("Upload retry does not match the stored chunk")
                return UploadChunk(chunk_index, old["sha256"], len(data))
            stored_bytes = self._db.execute(
                "SELECT coalesce(sum(length(data)), 0) FROM upload_chunks WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            if stored_bytes + len(data) > self.max_size_bytes:
                raise ValueError("Upload exceeds size limit")
            digest = hashlib.sha256(data).hexdigest()
            self._db.execute(
                "INSERT INTO upload_chunks VALUES (?, ?, ?, ?)",
                (session_id, chunk_index, digest, data),
            )
            self._db.commit()
            chunk = UploadChunk(chunk_index, digest, len(data))
            if session_id in self._views:
                self._views[session_id].received_chunks[chunk_index] = chunk
            return chunk

    def finalize_session(self, session_id: str) -> bytes:
        with self._write():
            session = self._active(session_id)
            count, size = self._db.execute(
                "SELECT count(*), coalesce(sum(length(data)), 0) "
                "FROM upload_chunks WHERE session_id = ?", (session_id,)
            ).fetchone()
            if count != session["total_chunks"]:
                raise ValueError(f"Missing chunks: received {count} of {session['total_chunks']}")
            if size > self.max_size_bytes:
                raise ValueError("Upload exceeds size limit")
            chunks = self._db.execute(
                "SELECT data FROM upload_chunks WHERE session_id = ? ORDER BY chunk_index",
                (session_id,),
            )
            final_data = b"".join(row[0] for row in chunks)
            if hashlib.sha256(final_data).hexdigest() != session["expected_sha256"]:
                raise ValueError("Upload checksum mismatch")
            self._db.execute("UPDATE uploads SET completed = 1 WHERE session_id = ?", (session_id,))
            self._db.commit()
            if session_id in self._views:
                self._views[session_id].completed = True
            return final_data

    def cancel_session(self, session_id: str) -> None:
        with self._write():
            self._db.execute("UPDATE uploads SET cancelled = 1 WHERE session_id = ?", (session_id,))
            self._db.execute("DELETE FROM upload_chunks WHERE session_id = ?", (session_id,))
            self._db.commit()
            if session_id in self._views:
                self._views[session_id].cancelled = True

    def close(self) -> None:
        with self._lock:
            self._db.close()
