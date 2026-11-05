"""Certificate policy and trust boundary tests with an offline signing stand-in."""

import json

import pytest
from goldgraft_contracts.api import VerifyCheckName
from goldgraft_contracts.proof import Grade, ProofStrength
from goldgraft_contracts.registry import validate

from pieces.proof.certificate import certificate_payload, issue_certificate, verify_certificate

from .conftest import ROOT

FIXTURE = ROOT / "fixtures/proof/legacy-php-shop"


def read(path):
    return json.loads((FIXTURE / path).read_text())


@pytest.fixture
def issuance():
    contract = validate("Contract/1", read("contract.json"))
    contract.rules = [rule for rule in contract.rules if rule.id == "R01"]
    scenario = validate("Scenario/1", read("scenarios/HAPPY.json"))
    verdict = validate("Verdict/1", read("expected/HAPPY.verdict.json"))
    return {
        "contract": contract,
        "scenarios": [scenario],
        "verdicts": [verdict],
        "strength": ProofStrength(total=12, equivalent_dropped=0, killed=12, score=1.0),
        "dependencies_allowlisted": True,
    }


def test_issuance_binds_the_payload_and_requires_all_trust_checks(issuance):
    signed = []

    def sign(payload):
        signed.append(payload)
        return "test-signature", "test-rekor-entry"

    certificate = issue_certificate(read("certificate/valid.json"), signer=sign, **issuance)
    assert signed == [certificate_payload(certificate)]
    assert certificate.results.scenarios == 1
    assert certificate.proof_strength.score == 1.0

    def check(cert, payload):
        return payload == signed[0] and cert.signature == "test-signature"

    verifiers = dict.fromkeys(VerifyCheckName, check)
    assert verify_certificate(certificate, verifiers).ok
    assert not verify_certificate(certificate, {VerifyCheckName.SIGNATURE: check}).ok

    certificate.cost.tokens += 1
    assert not verify_certificate(certificate, verifiers).ok


@pytest.mark.parametrize("failure", ["verdict", "strength", "deps", "coverage"])
def test_failed_certificate_gate_never_calls_the_signer(issuance, failure):
    if failure == "verdict":
        issuance["verdicts"][0].grade = Grade.UNVERIFIED
    elif failure == "strength":
        issuance["strength"].killed = 0
    elif failure == "deps":
        issuance["dependencies_allowlisted"] = False
    else:
        issuance["contract"].rules[0].triangle.killed = False

    def sign(_):
        pytest.fail("Signing must follow all evidence checks")

    with pytest.raises(ValueError, match="Certificate requires"):
        issue_certificate(read("certificate/valid.json"), signer=sign, **issuance)


def test_cosign_adapter_requires_runner_and_pins_workflow(monkeypatch):
    from pathlib import Path
    from subprocess import CompletedProcess

    from pieces.proof.sigstore import sign_payload, verify_signed_certificate

    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(RuntimeError, match="GitHub Actions"):
        sign_payload(b"payload")

    for name, value in (
        ("GITHUB_ACTIONS", "true"),
        ("ACTIONS_ID_TOKEN_REQUEST_URL", "fixture-url"),
        ("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "fixture-token"),
    ):
        monkeypatch.setenv(name, value)
    certificate = validate("Certificate/1", read("certificate/valid.json"))
    expected = certificate_payload(certificate)
    workflow = "https://github.com/example/repo/.github/workflows/proof.yml@refs/heads/main"
    bundle = json.dumps(
        {"verificationMaterial": {"tlogEntries": [{"logIndex": "42", "logId": {"keyId": "log"}}]}}
    )
    verification_calls = []

    def run(args, **kwargs):
        assert Path(args[-1]).read_bytes() == expected
        bundle_file = Path(args[args.index("--bundle") + 1])
        if args[1] == "sign-blob":
            bundle_file.write_text(bundle)
        else:
            verification_calls.append(args)
            assert bundle_file.read_text() == bundle
            assert args[args.index("--certificate-identity") + 1] == workflow
            assert args[args.index("--certificate-github-workflow-sha") + 1] == (
                certificate.runner_identity.sha
            )
        return CompletedProcess(args, 0)

    monkeypatch.setattr("pieces.proof.sigstore.subprocess.run", run)
    certificate.signature, certificate.rekor_entry = sign_payload(expected)
    assert certificate.rekor_entry == "log:42"

    def verify(sha, ledger_ok=True):
        return verify_signed_certificate(
            certificate,
            workflow_identity=workflow,
            workflow_sha=sha,
            ledger_check=lambda *_: ledger_ok,
            paypal_check=lambda *_: True,
        )

    assert verify(certificate.runner_identity.sha).ok
    assert not verify(certificate.runner_identity.sha, ledger_ok=False).ok
    assert not verify("another-workflow-sha").ok
    certificate.rekor_entry = "log:43"
    assert not verify(certificate.runner_identity.sha).ok
    assert len(verification_calls) == 2
