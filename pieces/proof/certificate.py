"""Canonical certificate payloads and checks against caller-supplied evidence."""

import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from hashlib import sha256
from hmac import compare_digest

from goldgraft_contracts.api import CertificateVerifyResult, VerifyCheck, VerifyCheckName
from goldgraft_contracts.proof import (
    Certificate,
    Grade,
    MoneyContract,
    ProofStrength,
    Scenario,
    Severity,
    Verdict,
)

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


type RunnerSigner = Callable[[bytes], tuple[str, str]]


def verdict_counts(verdicts: Sequence[Verdict]) -> dict[str, int]:
    counts = Counter(verdict.grade for verdict in verdicts)
    return {
        "scenarios": len(verdicts),
        "pass": counts[Grade.PASS],
        "pass_fixed": counts[Grade.PASS_FIXED],
        "problem": counts[Grade.PROBLEM],
        "unverified": counts[Grade.UNVERIFIED],
        "n_a": counts[Grade.NOT_APPLICABLE],
    }


def issue_certificate(
    metadata: Mapping[str, object],
    *,
    contract: MoneyContract,
    scenarios: Sequence[Scenario],
    verdicts: Sequence[Verdict],
    strength: ProofStrength,
    dependencies_allowlisted: bool,
    signer: RunnerSigner,
) -> Certificate:
    """Build a certificate after proof gates pass, then delegate signing to the runner."""
    scenario_rules = {scenario.id: set(scenario.rules) for scenario in scenarios}
    grades = {verdict.scenario_id: verdict.grade for verdict in verdicts}
    if (
        not scenarios
        or len(scenario_rules) != len(scenarios)
        or len(grades) != len(verdicts)
        or scenario_rules.keys() != grades.keys()
    ):
        raise ValueError("Certificate requires exactly one verdict per planned scenario")
    if not dependencies_allowlisted:
        raise ValueError("Certificate requires allowlisted dependencies")

    critical = {rule.id: rule for rule in contract.rules if rule.severity == Severity.CRITICAL}
    passing = {Grade.PASS, Grade.PASS_FIXED}
    if Grade.PROBLEM in grades.values() or any(
        grades[scenario] == Grade.UNVERIFIED and critical.keys() & rules
        for scenario, rules in scenario_rules.items()
    ):
        raise ValueError("Certificate requires resolved critical proof and no problem verdicts")
    if any(
        not rule.triangle.killed
        or not rule.triangle.mutants
        or not any(
            grades.get(scenario) in passing and rule.id in scenario_rules[scenario]
            for scenario in rule.triangle.scenarios
        )
        for rule in critical.values()
    ):
        raise ValueError(
            "Certificate requires scenario and mutation coverage of every critical rule"
        )

    retained = strength.total - strength.equivalent_dropped
    if (
        not retained
        or strength.killed * 100 < 95 * retained
        or strength.score != strength.killed / retained
    ):
        raise ValueError("Certificate requires consistent proof strength of at least 0.95")

    draft = Certificate.model_validate(
        {
            **metadata,
            "results": verdict_counts(verdicts),
            "proof_strength": {
                "mutants_total": strength.total,
                "equivalent_dropped": strength.equivalent_dropped,
                "killed": strength.killed,
                "score": strength.score,
            },
            "signature": "pending",
            "rekor_entry": "pending",
        }
    )
    if draft.shop_id != contract.shop_id:
        raise ValueError("Certificate and contract must refer to the same shop")
    if draft.survey.recall < 0.95:
        raise ValueError("Certificate requires survey recall of at least 0.95")
    if not draft.paypal_evidence or any(
        grades.get(evidence.scenario) not in passing for evidence in draft.paypal_evidence
    ):
        raise ValueError("Certificate requires PayPal evidence for passing scenarios")

    signature, rekor_entry = signer(certificate_payload(draft))
    return Certificate.model_validate(
        {
            **draft.model_dump(mode="json"),
            "signature": signature,
            "rekor_entry": rekor_entry,
        }
    )
