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
