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

    witness_calls = []

    def witness(name, ok):
        def check(*_):
            witness_calls.append(name)
            return ok

        return check

    def verify(sha, ledger_ok=True):
        return verify_signed_certificate(
            certificate,
            workflow_identity=workflow,
            workflow_sha=sha,
            ledger_check=witness("ledger", ledger_ok),
            paypal_check=witness("paypal", True),
        )

    assert verify(certificate.runner_identity.sha).ok
    assert not verify(certificate.runner_identity.sha, ledger_ok=False).ok
    assert not verify("another-workflow-sha").ok
    certificate.rekor_entry = "log:43"
    assert not verify(certificate.runner_identity.sha).ok
    assert len(verification_calls) == 2
    assert witness_calls == ["ledger", "paypal", "ledger", "paypal"]


def test_certificate_uses_signed_ledger_prefix_and_refetches_payment(
    issuance, monkeypatch, tmp_path
):
    from goldgraft_foundation.blobs import LocalBlobStore
    from goldgraft_foundation.ledger import Ledger

    from pieces.proof.evidence import issue_certificate_from_ledger, verify_certificate_evidence

    row = read("certificate/valid.json")["paypal_evidence"][0]
    event = next(
        item
        for item in read("cmel/HAPPY.NEW.json")
        if item["source"] == "PAYPAL_LEDGER" and item["pp"]["capture_id"] == row["capture_id"]
    )
    ledger = Ledger("sqlite://", blob_store=LocalBlobStore(tmp_path))
    producer = {"kind": "service", "name": "proof", "version": "1"}
    graft = event["graft_id"]
    ledger.append(graft, "ARTIFACT", producer, "CMEL/1", payload=event)
    for name in ("DECLINE", "NOTIFY_FORGED", "REFUND_TWICE"):
        issuance["scenarios"].append(validate("Scenario/1", read(f"scenarios/{name}.json")))
        issuance["verdicts"].append(validate("Verdict/1", read(f"expected/{name}.verdict.json")))

    class PayPal:
        value = "25.00"
        malformed_response = None
        calls = []

        def rest(self, method, path):
            assert method == "GET"
            self.calls.append(path)
            if path == self.malformed_response:
                return 200, []
            capture = {
                "id": row["capture_id"],
                "status": "COMPLETED",
                "amount": {"value": self.value, "currency_code": "USD"},
                "supplementary_data": {"related_ids": {"order_id": row["order_id"]}},
            }
            if path == f"/v2/checkout/orders/{row['order_id']}":
                return 200, {
                    "id": row["order_id"],
                    "purchase_units": [{"payments": {"captures": [capture]}}],
                }
            assert path == f"/v2/payments/captures/{row['capture_id']}"
            return 200, capture

    paypal = PayPal()

    def unexpected_sign(_):
        pytest.fail("An incomplete smoke round must not call the signer")

    with pytest.raises(ValueError, match="passing smoke proof"):
        issue_certificate_from_ledger(
            read("certificate/valid.json"),
            ledger=ledger,
            graft_id=graft,
            paypal=paypal,
            smoke_verdicts=issuance["verdicts"][:1],
            signer=unexpected_sign,
            **issuance,
        )

    with pytest.raises(ValueError, match="verdicts must match"):
        issue_certificate_from_ledger(
            read("certificate/valid.json"),
            ledger=ledger,
            graft_id=graft,
            paypal=paypal,
            smoke_verdicts=issuance["verdicts"],
            signer=unexpected_sign,
            **issuance,
        )

    for verdict in issuance["verdicts"]:
        entry = ledger.append(
            graft,
            "VERDICT",
            producer,
            "Verdict/1",
            payload=verdict.model_dump(mode="json"),
        )

    paypal.value = "25.01"
    with pytest.raises(ValueError, match="successful PayPal re-fetch"):
        issue_certificate_from_ledger(
            read("certificate/valid.json"),
            ledger=ledger,
            graft_id=graft,
            paypal=paypal,
            smoke_verdicts=issuance["verdicts"],
            signer=unexpected_sign,
            **issuance,
        )
    paypal.value = "25.00"
    certificate = issue_certificate_from_ledger(
        read("certificate/valid.json"),
        ledger=ledger,
        graft_id=graft,
        paypal=paypal,
        smoke_verdicts=issuance["verdicts"],
        signer=lambda _: ("test-signature", "test-rekor"),
        **issuance,
    )
    assert certificate.ledger_root == entry.entry_hash
    assert [item.model_dump() for item in certificate.paypal_evidence] == [row]

    ledger.append(graft, "ARTIFACT", producer, "Money/1", payload=event["money"])
    monkeypatch.setattr("pieces.proof.sigstore.verify_bundle", lambda *_, **__: True)

    paypal.calls.clear()

    def verify(graft_id=graft):
        return verify_certificate_evidence(
            certificate,
            ledger=ledger,
            graft_id=graft_id,
            paypal=paypal,
            workflow_identity="test",
            workflow_sha=certificate.runner_identity.sha,
        )

    assert verify().ok
    assert len(paypal.calls) == 2
    signed_rows = certificate.paypal_evidence
    certificate.paypal_evidence = []
    assert not verify().ok
    assert len(paypal.calls) == 2
    certificate.paypal_evidence = signed_rows
    certificate.results.pass_ -= 1
    assert not verify().ok
    assert len(paypal.calls) == 2
    certificate.results.pass_ += 1
    paypal.value = "25.01"
    assert not verify().ok
    assert len(paypal.calls) == 4
    assert not verify("another-graft").ok
    assert len(paypal.calls) == 4

    paypal.value = "25.00"
    for path in paypal.calls[:2]:
        paypal.calls.clear()
        paypal.malformed_response = path
        assert not verify().ok
        assert paypal.calls[-1] == path
    paypal.calls.clear()
    paypal.malformed_response = None

    table = ledger.entries
    with ledger.engine.begin() as connection:
        connection.execute(table.update().where(table.c.seq == 1).values(envelope_hash="0" * 64))
    assert not verify().ok
    assert not paypal.calls


@pytest.mark.parametrize(
    "gate", ["missing_verdict", "recall", "secrets", "missing_payment", "shop"]
)
def test_additional_issuance_gates_prevent_signing(issuance, gate):
    metadata = read("certificate/valid.json")
    if gate == "missing_verdict":
        issuance["verdicts"] = []
    elif gate == "recall":
        metadata["survey"]["recall"] = 0.94
    elif gate == "secrets":
        metadata["security"]["secrets_found"] = 1
    elif gate == "missing_payment":
        metadata["paypal_evidence"] = []
    else:
        metadata["shop_id"] = "another-shop"

    def sign(_):
        pytest.fail("Signing must follow all evidence checks")

    with pytest.raises(ValueError):
        issue_certificate(metadata, signer=sign, **issuance)


def test_conflicting_paypal_capture_observations_cannot_be_selected_by_debug_id():
    from pieces.proof.evidence import capture_evidence

    raw = next(
        event
        for event in read("cmel/HAPPY.NEW.json")
        if event["source"] == "PAYPAL_LEDGER" and event["kind"] == "CAPTURE"
    )
    first = validate("CMEL/1", raw)
    repeated = first.model_copy(deep=True)
    repeated.pp.debug_id = "another-observation"
    assert len(capture_evidence([first, repeated])) == 1
    repeated.money.minor += 1
    with pytest.raises(ValueError, match="Conflicting PayPal ledger observations"):
        capture_evidence([first, repeated])


def test_critical_planned_flow_cannot_be_certified_as_not_applicable(issuance):
    scenario = issuance["scenarios"][0].model_copy(deep=True)
    scenario.id = "skipped-critical-checkout"
    issuance["scenarios"].append(scenario)
    verdict = issuance["verdicts"][0].model_copy(deep=True)
    verdict.scenario_id = scenario.id
    verdict.grade = Grade.NOT_APPLICABLE
    issuance["verdicts"].append(verdict)
    with pytest.raises(ValueError, match="resolved critical proof"):
        issue_certificate(read("certificate/valid.json"),
                          signer=lambda _: pytest.fail("Must not sign skipped critical proof"),
                          **issuance)


@pytest.mark.parametrize("missing", ["debug_id", "capture_id", "order_id"])
def test_incomplete_payment_witness_cannot_be_omitted_from_signed_set(missing):
    from pieces.proof.evidence import _payment_witnesses

    raw = next(event for event in read("cmel/HAPPY.NEW.json")
               if event["source"] == "PAYPAL_LEDGER" and event["kind"] == "CAPTURE")
    complete = validate("CMEL/1", raw)
    incomplete = complete.model_copy(deep=True)
    incomplete.order_ref = "another-order"
    incomplete.pp.capture_id = "AnotherCapture"
    setattr(incomplete.pp, missing, None)
    verdict = validate("Verdict/1", read("expected/HAPPY.verdict.json"))
    with pytest.raises(ValueError, match="complete payment witnesses"):
        _payment_witnesses([complete, incomplete], {verdict.scenario_id: verdict})
