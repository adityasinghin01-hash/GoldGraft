"""Canonical certificate payloads and checks against caller-supplied evidence."""

import json
from collections.abc import Callable, Mapping
from hashlib import sha256
from hmac import compare_digest

from goldgraft_contracts.api import CertificateVerifyResult, VerifyCheck, VerifyCheckName
from goldgraft_contracts.proof import Certificate

type CertificateCheck = Callable[[Certificate, bytes], bool]


def certificate_payload(certificate: Certificate | Mapping[str, object]) -> bytes:
    fields = (
        certificate.model_dump(mode="json") if isinstance(certificate, Certificate) else certificate
    )
    payload = {
        name: value
        for name, value in fields.items()
        if name not in {"signature", "rekor_entry", "ots_proof"}
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def matches_payload_hash(certificate: Mapping[str, object], trusted_sha256: str) -> bool:
    """Check the original JSON representation against an independently trusted hash."""
    return compare_digest(sha256(certificate_payload(certificate)).hexdigest(), trusted_sha256)


def verify_certificate(
    certificate: Certificate,
    verifiers: Mapping[VerifyCheckName, CertificateCheck],
) -> CertificateVerifyResult:
    payload = certificate_payload(certificate)
    checks = []
    for name in VerifyCheckName:
        verifier = verifiers.get(name)
        if verifier is None:
            ok, detail = False, "Trusted verification evidence unavailable"
        else:
            ok = verifier(certificate, payload) is True
            detail = "Verified" if ok else "Evidence verification failed"
        checks.append(VerifyCheck(name=name, ok=ok, detail=detail))
    return CertificateVerifyResult(
        cert_id=certificate.cert_id,
        ok=all(check.ok for check in checks),
        checks=checks,
    )
