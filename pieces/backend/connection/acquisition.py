"""Source Acquisition and Quarantine Storage Boundary (GU02).

Implements:
1. Bounded quarantine for merchant source archives.
2. Cryptographic checksum calculation (SHA-256) of acquired assets.
3. Path traversal protection ensuring files cannot escape the quarantine directory.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AcquiredAsset:
    asset_id: str
    filename: str
    sha256: str
    byte_count: int
    quarantine_path: str


class SourceAcquisition:
    """Safely acquires and hashes incoming source assets in an isolated quarantine."""

    def __init__(self, quarantine_root: Path | None = None):
        self.root = quarantine_root or Path(".goldgraft/quarantine")
        self.root.mkdir(parents=True, exist_ok=True)
        self._assets: dict[str, AcquiredAsset] = {}

    def acquire_bytes(self, filename: str, data: bytes) -> AcquiredAsset:
        # Prevent path traversal
        clean_name = Path(filename).name
        digest = hashlib.sha256(data).hexdigest()
        asset_id = f"asset-{digest[:12]}"

        dest = self.root / f"{asset_id}_{clean_name}"
        dest.write_bytes(data)

        asset = AcquiredAsset(
            asset_id=asset_id,
            filename=clean_name,
            sha256=digest,
            byte_count=len(data),
            quarantine_path=str(dest),
        )
        self._assets[asset_id] = asset
        return asset

    def get_asset(self, asset_id: str) -> AcquiredAsset | None:
        return self._assets.get(asset_id)
