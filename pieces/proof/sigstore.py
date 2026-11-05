"""Cosign bridge for the runner's keyless GitHub Actions signing job."""

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from goldgraft_contracts.api import CertificateVerifyResult, VerifyCheckName
from goldgraft_contracts.proof import Certificate

from .certificate import CertificateCheck, certificate_payload, verify_certificate

ISSUER = "https://token.actions.githubusercontent.com"


def rekor_reference(bundle: str) -> str:
    entries = json.loads(bundle)["verificationMaterial"]["tlogEntries"]
    if len(entries) != 1:
        raise ValueError("Expected one Rekor entry in the signing bundle")
    entry = entries[0]
    index = int(entry["logIndex"])
    log_id = entry["logId"]["keyId"]
    if index < 0 or not isinstance(log_id, str) or not log_id:
        raise ValueError("Invalid Rekor entry reference")
    return f"{log_id}:{index}"


def sign_payload(payload: bytes, *, cosign: str = "cosign") -> tuple[str, str]:
    if os.environ.get("GITHUB_ACTIONS") != "true" or not all(
        os.environ.get(name)
        for name in ("ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    ):
        raise RuntimeError("Signing requires a GitHub Actions runner with id-token: write")

    with TemporaryDirectory() as directory:
        blob = Path(directory) / "certificate.json"
        bundle_path = Path(directory) / "certificate.sigstore.json"
        blob.write_bytes(payload)
        subprocess.run(
            [cosign, "sign-blob", "--yes", "--bundle", str(bundle_path), str(blob)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        bundle = bundle_path.read_text()
        return bundle, rekor_reference(bundle)


def verify_bundle(
    certificate: Certificate,
    payload: bytes,
    *,
    workflow_identity: str,
    workflow_sha: str,
    cosign: str = "cosign",
) -> bool:
    """Check blob signature and Rekor inclusion using independently trusted workflow pins."""
    if not workflow_identity or not workflow_sha or certificate.runner_identity.sha != workflow_sha:
        return False
    try:
        if rekor_reference(certificate.signature) != certificate.rekor_entry:
            return False
        with TemporaryDirectory() as directory:
            blob = Path(directory) / "certificate.json"
            bundle = Path(directory) / "certificate.sigstore.json"
            blob.write_bytes(payload)
            bundle.write_text(certificate.signature)
            result = subprocess.run(
                [
                    cosign,
                    "verify-blob",
                    "--bundle",
                    str(bundle),
                    "--certificate-identity",
                    workflow_identity,
                    "--certificate-oidc-issuer",
                    ISSUER,
                    "--certificate-github-workflow-sha",
                    workflow_sha,
                    str(blob),
                ],
                check=False,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        return False


def verify_signed_certificate(
    certificate: Certificate,
    *,
    workflow_identity: str,
    workflow_sha: str,
    ledger_check: CertificateCheck,
    paypal_check: CertificateCheck,
    cosign: str = "cosign",
) -> CertificateVerifyResult:
    verified = verify_bundle(
        certificate,
        certificate_payload(certificate),
        workflow_identity=workflow_identity,
        workflow_sha=workflow_sha,
        cosign=cosign,
    )

    def checked_bundle(_certificate: Certificate, _payload: bytes) -> bool:
        return verified

    checks = {
        VerifyCheckName.SIGNATURE: checked_bundle,
        VerifyCheckName.REKOR: checked_bundle,
    }
    if verified:
        checks[VerifyCheckName.LEDGER_CHAIN] = ledger_check
        checks[VerifyCheckName.PAYPAL_REFETCH] = paypal_check
    return verify_certificate(certificate, checks)
