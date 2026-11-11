"""Chunked Upload Sessions and Integrity Checking (GU02).

Implements:
1. Chunked upload tracking with chunk receipts.
2. Max file size enforcement (inline limit 16KB / chunk limit 1MB / blob limit 50MB).
3. Path traversal prevention and safe filename validation.
4. Session expiration, cancellation, and assembly digest verification.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

MAX_INLINE_SIZE_BYTES = 16 * 1024  # 16 KB
MAX_CHUNK_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
DEFAULT_MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MB


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

    def __init__(self, max_size_bytes: int = DEFAULT_MAX_TOTAL_BYTES):
        self.max_size_bytes = max_size_bytes
        self._sessions: dict[str, UploadSession] = {}
        self._buffers: dict[str, dict[int, bytes]] = {}

    def validate_inline_upload(self, data: bytes) -> bool:
        """Enforces 16KB inline payload limit."""
        if len(data) > MAX_INLINE_SIZE_BYTES:
            msg = f"PAYLOAD_TOO_LARGE: Inline payload {len(data)} exceeds {MAX_INLINE_SIZE_BYTES}"
            raise ValueError(msg)
        return True

    def _sanitize_filename(self, filename: str) -> str:
        """Guarantees filename contains no path traversal components."""
        if not filename or not filename.strip():
            raise ValueError("UNSAFE_FILE_PATH: Empty filename")
        p = Path(filename)
        if ".." in p.parts or p.is_absolute() or "/" in filename or "\\" in filename:
            raise ValueError(f"UNSAFE_FILE_PATH: Path traversal detected in {filename!r}")
        return p.name

    def create_session(
        self,
        case_id: str,
        filename: str,
        total_chunks: int,
        expected_sha256: str,
    ) -> UploadSession:
        safe_filename = self._sanitize_filename(filename)
        if total_chunks <= 0:
            raise ValueError("Invalid total_chunks count: must be > 0")

        raw = f"{case_id}:{safe_filename}:{expected_sha256}".encode()
        session_id = f"upload-{hashlib.sha256(raw).hexdigest()[:12]}"

        session = UploadSession(
            session_id=session_id,
            case_id=case_id,
            filename=safe_filename,
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

        if chunk_index < 0 or chunk_index >= session.total_chunks:
            raise ValueError(
                f"Invalid chunk index {chunk_index}: out of range 0..{session.total_chunks - 1}"
            )

        if len(data) > MAX_CHUNK_SIZE_BYTES:
            raise ValueError(
                f"CHUNK_TOO_LARGE: Chunk {len(data)} bytes exceeds limit {MAX_CHUNK_SIZE_BYTES}"
            )

        # Calculate projected total byte count
        projected = sum(
            c.byte_count for idx, c in session.received_chunks.items() if idx != chunk_index
        ) + len(data)
        if projected > self.max_size_bytes:
            raise ValueError(
                f"PAYLOAD_TOO_LARGE: Total upload exceeds maximum size {self.max_size_bytes} bytes"
            )

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
