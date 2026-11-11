"""Chunked Upload Sessions and Integrity Checking (GU02).

Implements:
1. Chunked upload tracking with chunk receipts.
2. Per-upload byte and chunk limits.
3. Cancellation and assembly digest verification.
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
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
    """Manages secure chunked uploads with strict size and checksum validation."""

    def __init__(self, max_size_bytes: int = 50 * 1024 * 1024):
        if max_size_bytes <= 0:
            raise ValueError("Upload size limit must be positive")
        self.max_size_bytes = max_size_bytes
        self._lock = Lock()
        self._sessions: dict[str, UploadSession] = {}
        self._buffers: dict[str, dict[int, bytes]] = {}

    def create_session(
        self,
        case_id: str,
        filename: str,
        total_chunks: int,
        expected_sha256: str,
    ) -> UploadSession:
        if (
            type(total_chunks) is not int
            or not 1 <= total_chunks <= min(self.max_size_bytes, 10_000)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
        ):
            raise ValueError("Invalid upload chunk count or SHA-256 digest")
        raw = repr((case_id, filename, total_chunks, expected_sha256)).encode()
        session_id = f"upload-{hashlib.sha256(raw).hexdigest()[:24]}"
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = UploadSession(
                    session_id=session_id,
                    case_id=case_id,
                    filename=filename,
                    total_chunks=total_chunks,
                    expected_sha256=expected_sha256,
                )
                self._buffers[session_id] = {}
            return self._sessions[session_id]

    def add_chunk(
        self,
        session_id: str,
        chunk_index: int,
        data: bytes,
    ) -> UploadChunk:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.cancelled or session.completed:
                raise ValueError("Upload session is not active")
            if type(chunk_index) is not int or not 0 <= chunk_index < session.total_chunks:
                raise ValueError("Upload chunk index is out of range")
            if not data:
                raise ValueError("Upload chunks must be nonempty")
            buffers = self._buffers[session_id]
            if chunk_index in buffers:
                if buffers[chunk_index] != data:
                    raise ValueError("Upload retry does not match the stored chunk")
                return session.received_chunks[chunk_index]
            if sum(len(chunk) for chunk in buffers.values()) + len(data) > self.max_size_bytes:
                raise ValueError("Upload exceeds size limit")

            chunk = UploadChunk(chunk_index, hashlib.sha256(data).hexdigest(), len(data))
            session.received_chunks[chunk_index] = chunk
            buffers[chunk_index] = data
            return chunk

    def finalize_session(self, session_id: str) -> bytes:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.cancelled:
                raise ValueError("Upload session is not active")
            buffers = self._buffers[session_id]
            if len(buffers) != session.total_chunks:
                raise ValueError(
                    f"Missing chunks: received {len(buffers)} of {session.total_chunks}"
                )
            final_data = b"".join(buffers[idx] for idx in range(session.total_chunks))
            if hashlib.sha256(final_data).hexdigest() != session.expected_sha256:
                raise ValueError("Upload checksum mismatch")
            session.completed = True
            return final_data

    def cancel_session(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.cancelled = True
                self._buffers.pop(session_id, None)
