"""Install official checksum-pinned Node 22 on D:; never change global PATH."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSION = "22.23.4"
NAME = f"node-v{VERSION}-win-x64"
STORE = Path("D:/DevTools/GoldGraft")
ARCHIVE = STORE / (NAME + ".zip")
INSTALL = STORE / NAME
URL = f"https://nodejs.org/dist/v{VERSION}/{NAME}.zip"
# Official SHASUMS256.txt retrieved 8 November 2026 over HTTPS.
SHA256 = "cbc74b5e0982c9dbb41525fd8fb5dcd32fbee237863f7829072f4639a1ce5f20"


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        with urlopen(URL, timeout=45) as response, ARCHIVE.open("xb") as output:
            count = 0
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > 60_000_000:
                    raise ValueError("Node archive exceeds size limit")
                output.write(chunk)
    with ARCHIVE.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != SHA256:
            raise ValueError("Node archive checksum mismatch; nothing executed")
    with zipfile.ZipFile(ARCHIVE) as archive:
        entries = archive.infolist()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or ":" in entry.filename
                or "\\" in entry.filename
                or not path.parts
                or path.parts[0] != NAME
                or (entry.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("Unsafe Node archive path")
        if sum(e.file_size for e in entries) > 250_000_000:
            raise ValueError("Expanded Node archive exceeds size limit")
        if not INSTALL.exists():
            for entry in entries:
                target = STORE / entry.filename
                if target.is_symlink() or any(p.is_symlink() for p in target.parents):
                    raise ValueError("Linked Node install path")
            archive.extractall(STORE)
        for entry in entries:
            if entry.is_dir():
                continue
            target = STORE / entry.filename
            if (
                target.is_symlink()
                or any(p.is_symlink() for p in target.parents)
                or not target.is_file()
                or hashlib.sha256(target.read_bytes()).digest()
                != hashlib.sha256(archive.read(entry)).digest()
            ):
                raise ValueError("Node install bytes changed; nothing executed")
    node = INSTALL / "node.exe"
    version = subprocess.check_output([str(node), "--version"], text=True, timeout=15).strip()
    if version != "v" + VERSION:
        raise ValueError("Unexpected Node version")
    record = {
        "node": str(node),
        "version": version,
        "archive_sha256": SHA256,
        "url": URL,
        "archive_bytes": ARCHIVE.stat().st_size,
        "node_sha256": hashlib.sha256(node.read_bytes()).hexdigest(),
        "global_path_changed": False,
    }
    (ROOT / ".context").mkdir(exist_ok=True)
    (ROOT / ".context/portable-node.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": "PASS", **record}, indent=2))


if __name__ == "__main__":
    main()
