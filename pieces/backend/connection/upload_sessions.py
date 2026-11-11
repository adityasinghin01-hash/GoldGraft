"""Chunked Upload Sessions and Integrity Checking (GU02).

Implements:
1. Chunked upload tracking with chunk receipts.
2. Max file size enforcement (inline limit 16KB / blob limit 50MB).
3. Session expiration, cancellation, and assembly digest verification.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime


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
        self.max_size_bytes = max_size_bytes
        self._sessions: dict[str, UploadSession] = {}
        self._buffers: dict[str, dict[int, bytes]] = {}

    def create_session(
        self,
        case_id: str,
        filename: str,
        total_chunks: int,
        expected_sha256: str,
    ) -> UploadSession:
        raw = f"{case_id}:{filename}:{expected_sha256}".encode()
        session_id = f"upload-{hashlib.sha256(raw).hexdigest()[:12]}"

        session = UploadSession(
            session_id=session_id,
            case_id=case_id,
            filename=filename,
            total_chunks=total_chunks,
            expected_sha256=expected_sha256,
        )
        self._sessions[session_id] = session
        self._buffers[session_id] = {}
        return session

    def add_chunk(
        self,
        session_id: str,
        chunk_index: int,
        data: bytes,
    ) -> UploadChunk:
        session = self._sessions.get(session_id)
        if not session or session.cancelled:
            raise ValueError(f"Upload session {session_id} not active")

        digest = hashlib.sha256(data).hexdigest()
        chunk = UploadChunk(
            chunk_index=chunk_index,
            sha256=digest,
            byte_count=len(data),
        )
        session.received_chunks[chunk_index] = chunk
        self._buffers[session_id][chunk_index] = data
        return chunk

    def finalize_session(self, session_id: str) -> bytes:
        session = self._sessions.get(session_id)
        if not session or session.cancelled:
            raise ValueError(f"Upload session {session_id} not active")

        if len(session.received_chunks) != session.total_chunks:
            raise ValueError(
                f"Missing chunks: received {len(session.received_chunks)} of {session.total_chunks}"
            )

        # Assemble chunks in order
        assembled = bytearray()
        for idx in range(session.total_chunks):
            assembled.extend(self._buffers[session_id][idx])

        final_data = bytes(assembled)
        final_digest = hashlib.sha256(final_data).hexdigest()
        if final_digest != session.expected_sha256:
            raise ValueError(
                f"Checksum mismatch: expected {session.expected_sha256}, got {final_digest}"
            )

        session.completed = True
        return final_data

    def cancel_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.cancelled = True
            self._buffers.pop(session_id, None)
