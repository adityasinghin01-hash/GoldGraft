"""Independently check a Sigstore bundle against the public Rekor log (network read only).

Confirms that the log entry named in the bundle records exactly the payload's
SHA-256 and that its signing certificate names the expected workflow identity.
This checks transparency inclusion and identity; it does not decide what the
signed bytes prove.
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REKOR = "https://rekor.sigstore.dev/api/v1/log/entries?logIndex={}"


def log_index(bundle: dict) -> int:
    entries = bundle.get("verificationMaterial", {}).get("tlogEntries")
    if entries:
        return int(entries[0]["logIndex"])
    return int(bundle["rekorBundle"]["Payload"]["logIndex"])


def check(payload: Path, bundle_path: Path, identity: str) -> dict:
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    index = log_index(json.loads(bundle_path.read_bytes()))
    with urllib.request.urlopen(REKOR.format(index), timeout=20) as reply:
        ((uuid, entry),) = json.load(reply).items()
    body = json.loads(base64.b64decode(entry["body"]))
    logged = body["spec"]["data"]["hash"]["value"]
    pem = base64.b64decode(body["spec"]["signature"]["publicKey"]["content"])
    text = subprocess.run(
        ["openssl", "x509", "-noout", "-text"], input=pem, capture_output=True, check=True
    ).stdout.decode()
    return {
        "log_index": index,
        "entry_uuid": uuid,
        "integrated_time": entry["integratedTime"],
        "payload_sha256": digest,
        "logged_sha256": logged,
        "hash_matches": logged == digest,
        "identity": identity,
        "identity_in_certificate": identity in text,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("payload", type=Path)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--identity", required=True)
    args = parser.parse_args()
    result = check(args.payload, args.bundle, args.identity)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["hash_matches"] and result["identity_in_certificate"] else 1)


if __name__ == "__main__":
    main()
