"""Bounded private quarantine and non-executing archive inspection (GU02).

Inspection never extracts paths or runs hooks. Safe text and omissions are
separate from the raw quarantine; an omission is never completeness evidence.
"""

import hashlib
import io
import os
import re
import stat
import tarfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass
class AcquiredAsset:
    asset_id: str
    filename: str
    sha256: str
    byte_count: int
    quarantine_path: str


class SourceAcquisition:
    """Intake limits apply to compressed bytes, expanded bytes, entries and depth."""

    def __init__(
        self,
        quarantine_root: Path | None = None,
        *,
        max_bytes: int = 50 * 1024 * 1024,
        max_entries: int = 20000,
        max_file_bytes: int = 20 * 1024 * 1024,
        max_depth: int = 32,
    ):
        if any(
            type(x) is not int or x <= 0
            for x in (max_bytes, max_entries, max_file_bytes, max_depth)
        ):
            raise ValueError("Intake limits must be positive integers")
        self.root = quarantine_root or Path(".goldgraft/quarantine")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.max_file_bytes, self.max_depth = max_file_bytes, max_depth
        self._assets: dict[str, AcquiredAsset] = {}

    def acquire_bytes(self, filename: str, data: bytes) -> AcquiredAsset:
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            or "\x00" in filename
        ):
            raise ValueError("UNSAFE_FILE_PATH")
        if len(data) > self.max_bytes:
            raise ValueError("PAYLOAD_TOO_LARGE")
        digest = hashlib.sha256(data).hexdigest()
        asset_id = f"asset-{digest[:24]}"
        dest = self.root / f"{asset_id}_{filename}"
        # Never follow a pre-existing symlink, and never overwrite an earlier intake.
        try:
            fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != data:
                raise ValueError("QUARANTINE_COLLISION") from None
        else:
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
            except BaseException:
                dest.unlink(missing_ok=True)
                raise
        asset = AcquiredAsset(asset_id, filename, digest, len(data), str(dest))
        self._assets[asset_id] = asset
        return asset

    def inspect_archive(self, data: bytes, *, required_paths=()) -> tuple[dict, dict]:
        """Return safe text bytes plus omission reasons; malformed archives fail wholly.

        Caller must hold if required paths are omitted. Unrecognised binary,
        environment files, private keys, dumps and credential-bearing text stay
        in quarantine and never enter the returned safe-content projection.
        """
        if len(data) > self.max_bytes:
            raise ValueError("PAYLOAD_TOO_LARGE")
        seen: set[str] = set()
        paths: dict[str, bool] = {}
        safe, omissions = {}, {}
        total = 0

        def accept(name, size, directory, read):
            nonlocal total
            name = name.rstrip("/") if directory else name
            parts = PurePosixPath(name).parts
            if (
                not name
                or name.startswith("/")
                or "\\" in name
                or ":" in name
                or "\x00" in name
                or any(p in {"", ".", ".."} for p in name.split("/"))
                or len(parts) > self.max_depth
                or any(len(part.encode("utf-8")) > 255 for part in parts)
                or unicodedata.normalize("NFC", name) != name
            ):
                raise ValueError("UNSAFE_ARCHIVE_PATH")
            key = name.casefold()
            if key in seen or len(seen) >= self.max_entries:
                raise ValueError("ARCHIVE_COLLISION_OR_ENTRY_LIMIT")
            if any(
                paths.get("/".join(parts[:i]).casefold()) is False for i in range(1, len(parts))
            ):
                raise ValueError("ARCHIVE_FILE_DIRECTORY_COLLISION")
            if not directory and any(p.startswith(key + "/") for p in paths):
                raise ValueError("ARCHIVE_FILE_DIRECTORY_COLLISION")
            seen.add(key)
            paths[key] = directory
            if directory:
                return
            total += size
            if (
                size < 0
                or size > self.max_file_bytes
                or total > self.max_bytes
                or total > max(1, len(data)) * 100
            ):
                raise ValueError("ARCHIVE_EXPANSION_LIMIT")
            content = read(self.max_file_bytes + 1)
            if len(content) != size:
                raise ValueError("ARCHIVE_SIZE_MISMATCH")
            base = parts[-1].lower()
            reason = None
            if (
                base.startswith(".env")
                or base.endswith((".pem", ".key", ".sql", ".sqlite", ".db"))
                or any(p.casefold() in {".git", "node_modules", "vendor"} for p in parts)
            ):
                reason = "private_or_dependency_content"
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                reason = "unclassified_binary"
                text = ""
            if "\x00" in text:
                reason = "unclassified_binary"
            if re.search(
                r"(?i)(?:password|secret|token|api[_-]?key|signature)\s*[=:]\s*['\"]?[^\s'\";]+"
                r"|-----BEGIN .*PRIVATE KEY|sk-ant-|github_pat_|Bearer\s+",
                text,
            ):
                reason = "credential_content"
            if base == ".gitmodules" or text.startswith(
                "version https://git-lfs.github.com/spec/v1"
            ):
                reason = "unresolved_source_dependency"
            if reason:
                omissions[name] = reason
            else:
                safe[name] = content

        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.infolist():
                    mode = member.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    if member.flag_bits & 1 or kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                        raise ValueError("UNSUPPORTED_ARCHIVE_ENTRY")
                    with archive.open(member) as stream:
                        accept(member.filename, member.file_size, member.is_dir(), stream.read)
        else:
            try:
                with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
                    for member in archive:
                        if not (member.isfile() or member.isdir()):
                            raise ValueError("UNSUPPORTED_ARCHIVE_ENTRY")
                        stream = archive.extractfile(member) if member.isfile() else None
                        try:
                            accept(
                                member.name,
                                member.size,
                                member.isdir(),
                                stream.read if stream else lambda _: b"",
                            )
                        finally:
                            if stream:
                                stream.close()
            except tarfile.TarError:
                raise ValueError("UNSUPPORTED_OR_CORRUPT_ARCHIVE") from None
        if any(path not in safe for path in required_paths):
            raise ValueError("REQUIRED_SOURCE_OMITTED")
        return safe, omissions

    def get_asset(self, asset_id: str) -> AcquiredAsset | None:
        return self._assets.get(asset_id)
