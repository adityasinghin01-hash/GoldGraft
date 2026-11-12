"""Install a checksum-pinned official PHP ZIP on D:, without changing Windows PATH."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
INSTALL = Path("D:/DevTools/GoldGraft/php-8.3.36-1")
ZIP = INSTALL.parent / "php-8.3.36-1-nts-Win32-vs16-x64.zip"
URL = "https://downloads.php.net/~windows/releases/archives/" + ZIP.name
SHA256 = "1a097d52b7a68622cdc723073b61cc70caf79c941218ff65b2d8441dbc6b10d4"


def main():
    INSTALL.parent.mkdir(parents=True, exist_ok=True)
    if not ZIP.exists():
        with urlopen(URL, timeout=45) as response, ZIP.open("xb") as output:
            count = 0
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > 60_000_000:
                    raise ValueError("PHP archive exceeds expected size bound")
                output.write(chunk)
    with ZIP.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SHA256:
        raise ValueError("PHP archive checksum mismatch; archive preserved, nothing executed")
    if not INSTALL.exists():
        with zipfile.ZipFile(ZIP) as archive:
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or ":" in member.filename
                    or "\\" in member.filename
                ):
                    raise ValueError("Unsafe archive path")
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Archive link not allowed")
            if sum(m.file_size for m in archive.infolist()) > 250_000_000:
                raise ValueError("Expanded PHP archive exceeds expected bound")
            INSTALL.mkdir()
            archive.extractall(INSTALL)
    # Re-runs verify existing bytes too; never execute an unverified pre-existing php.exe.
    with zipfile.ZipFile(ZIP) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = INSTALL / member.filename
            if target.is_symlink() or not target.is_file():
                raise ValueError("Installed PHP file missing or linked; nothing executed")
            if (
                hashlib.sha256(target.read_bytes()).digest()
                != hashlib.sha256(archive.read(member)).digest()
            ):
                raise ValueError(
                    "Installed PHP bytes differ from official archive; nothing executed"
                )
    php = INSTALL / "php.exe"
    flags = [
        str(php),
        "-n",
        "-d",
        "extension_dir=" + str(INSTALL / "ext"),
        "-d",
        "extension=curl",
        "-d",
        "extension=openssl",
    ]
    result = subprocess.run(
        [
            *flags,
            "-r",
            'echo json_encode(["version"=>PHP_VERSION,"curl"=>extension_loaded("curl"),'
            '"openssl"=>extension_loaded("openssl")]);',
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    runtime = json.loads(result.stdout)
    if not runtime["version"].startswith("8.3.") or not runtime["curl"] or not runtime["openssl"]:
        raise ValueError("Required PHP runtime capabilities missing")
    record = {
        "php": str(php),
        "flags": flags[1:],
        "archive": str(ZIP),
        "url": URL,
        "sha256": SHA256,
        "archive_bytes": ZIP.stat().st_size,
        "runtime": runtime,
        "expanded_bytes": sum(p.stat().st_size for p in INSTALL.rglob("*") if p.is_file()),
    }
    target = ROOT / ".context/portable-php.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", **record}, indent=2))


if __name__ == "__main__":
    main()
