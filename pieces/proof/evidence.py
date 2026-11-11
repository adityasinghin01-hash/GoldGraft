"""Bind certificate claims to an audited ledger prefix and re-fetch PayPal evidence."""

import re
from collections.abc import Mapping, Sequence
from decimal import InvalidOperation

from goldgraft_contracts.api import CertificateVerifyResult
from goldgraft_contracts.interfaces import PayPalClient
from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.proof import (
    Certificate,
    Grade,
    MoneyContract,
    PayPalEvidence,
    ProofStrength,
    Scenario,
    ScenarioFamily,
    Verdict,
)
from goldgraft_foundation.ledger import Ledger

from .certificate import RunnerSigner, issue_certificate, verdict_counts
from .cmel import money
from .sigstore import verify_signed_certificate

PAYPAL_ID = re.compile(r"[A-Za-z0-9]{1,64}")
SETTLED = {"COMPLETED", "PARTIALLY_REFUNDED", "REFUNDED"}


def capture_evidence(events: Sequence[MoneyEvent]) -> list[PayPalEvidence]:
    """Use independently read NEW captures with traceable PayPal IDs."""
    rows = {}
    observed = {}
    for event in events:
        refs = event.pp
        if (
            event.variant == "NEW"
            and event.source == "PAYPAL_LEDGER"
            and event.kind == "CAPTURE"
            and event.status_norm == "COMPLETED"
            and event.money is not None
            and refs.order_id
            and refs.capture_id
            and refs.debug_id
            and PAYPAL_ID.fullmatch(refs.order_id)
            and PAYPAL_ID.fullmatch(refs.capture_id)
        ):
            subject = refs.order_id, event.money.minor, event.money.currency
            if observed.setdefault(refs.capture_id, subject) != subject:
                raise ValueError("Conflicting PayPal ledger observations for the same capture")
            key = event.scenario_id, refs.order_id, refs.capture_id
            rows[key] = PayPalEvidence(
                scenario=event.scenario_id,
                order_id=refs.order_id,
                capture_id=refs.capture_id,
                debug_id=refs.debug_id,
            )
    return [rows[key] for key in sorted(rows)]


def refetch_capture(client: PayPalClient, row: PayPalEvidence, event: MoneyEvent) -> bool:
    if not PAYPAL_ID.fullmatch(row.order_id) or not PAYPAL_ID.fullmatch(row.capture_id):
        return False
    try:
        order_status, order = client.rest("GET", f"/v2/checkout/orders/{row.order_id}")
        if order_status != 200 or not isinstance(order, Mapping) or order.get("id") != row.order_id:
            return False
        order_captures = [
            capture
            for unit in order["purchase_units"]
            for capture in unit.get("payments", {}).get("captures", [])
            if capture.get("id") == row.capture_id
        ]
        if len(order_captures) != 1:
            return False
        status, capture = client.rest("GET", f"/v2/payments/captures/{row.capture_id}")
        if status != 200 or capture.get("id") != row.capture_id or event.money is None:
            return False
        expected = event.money.model_dump(mode="json")
        for response in (order_captures[0], capture):
            amount = response["amount"]
            if response.get("status") not in SETTLED or not isinstance(amount["value"], str):
                return False
            if money(amount["value"], amount["currency_code"]) != expected:
                return False
        related = capture.get("supplementary_data", {}).get("related_ids", {})
        return related.get("order_id", row.order_id) == row.order_id
    except (AttributeError, KeyError, InvalidOperation, OSError, TypeError, ValueError):
        return False


def archived_evidence(ledger: Ledger, graft_id: str, root: str):
    check, payloads = ledger.verified_payloads(graft_id, root, ("CMEL/1", "Verdict/1"))
    events = [payload for payload in payloads if isinstance(payload, MoneyEvent)]
    verdicts = {
        payload.scenario_id: payload for payload in payloads if isinstance(payload, Verdict)
    }
    if not check.ok or any(event.graft_id != graft_id for event in events):
        raise ValueError("Certificate requires an intact evidence ledger")
    return events, verdicts


def _payment_witnesses(
    events: Sequence[MoneyEvent], verdicts: Mapping[str, Verdict]
) -> list[tuple[PayPalEvidence, MoneyEvent]]:
    # Check conflicting ledger observations before filtering by verdict.
    capture_evidence(events)
    passing = {
        scenario for scenario, verdict in verdicts.items()
        if verdict.grade in {Grade.PASS, Grade.PASS_FIXED}
    }
    eligible = [event for event in events if event.scenario_id in passing]
    rows = capture_evidence(eligible)
    by_key = {}
    for event in eligible:
        for row in capture_evidence((event,)):
            by_key[row.scenario, row.order_id, row.capture_id, row.debug_id] = event
    return [
        (row, by_key[row.scenario, row.order_id, row.capture_id, row.debug_id])
        for row in rows
    ]


def verify_certificate_evidence(
    certificate: Certificate,
    *,
    ledger: Ledger,
    graft_id: str,
    paypal: PayPalClient,
    workflow_identity: str,
    workflow_sha: str,
    cosign: str = "cosign",
) -> CertificateVerifyResult:
    witnesses: list[tuple[PayPalEvidence, MoneyEvent]] = []

    def check_ledger(cert: Certificate, _payload: bytes) -> bool:
        nonlocal witnesses
        try:
            events, verdicts = archived_evidence(ledger, graft_id, cert.ledger_root)
            if cert.results.model_dump(by_alias=True) != verdict_counts(list(verdicts.values())):
                return False
            expected = _payment_witnesses(events, verdicts)
        except ValueError:
            return False
        if not expected or cert.paypal_evidence != [row for row, _ in expected]:
            return False
        witnesses = expected
        return True

    def check_paypal(_cert: Certificate, _payload: bytes) -> bool:
        return bool(witnesses) and all(
            refetch_capture(paypal, row, event) for row, event in witnesses
        )

    return verify_signed_certificate(
        certificate,
        workflow_identity=workflow_identity,
        workflow_sha=workflow_sha,
        ledger_check=check_ledger,
        paypal_check=check_paypal,
        cosign=cosign,
    )


def issue_certificate_from_ledger(
    metadata: Mapping[str, object],
    *,
    ledger: Ledger,
    graft_id: str,
    contract: MoneyContract,
    scenarios: Sequence[Scenario],
    verdicts: Sequence[Verdict],
    smoke_verdicts: Sequence[Verdict],
    paypal: PayPalClient,
    strength: ProofStrength,
    dependencies_allowlisted: bool,
    signer: RunnerSigner,
) -> Certificate:
    families = {scenario.id: scenario.family for scenario in scenarios}
    smoke = {verdict.scenario_id: verdict.grade for verdict in smoke_verdicts}
    if (
        len(smoke_verdicts) != 4
        or len(smoke) != 4
        or not smoke.keys() <= families.keys()
        or sum(families[scenario] == ScenarioFamily.HAPPY for scenario in smoke) != 1
        or any(grade not in {Grade.PASS, Grade.PASS_FIXED} for grade in smoke.values())
    ):
        raise ValueError("Certificate requires passing smoke proof for HAPPY and three other cases")
    root = ledger.root_hash(graft_id)
    events, archived_verdicts = archived_evidence(ledger, graft_id, root)
    if archived_verdicts != {verdict.scenario_id: verdict for verdict in verdicts}:
        raise ValueError("Certificate verdicts must match the audited ledger")
    witnesses = _payment_witnesses(events, archived_verdicts)
    if not witnesses or not all(refetch_capture(paypal, row, event) for row, event in witnesses):
        raise ValueError(
            "Certificate requires successful PayPal re-fetch for all payment witnesses"
        )
    rows = [row for row, _ in witnesses]
    return issue_certificate(
        {**metadata, "ledger_root": root, "paypal_evidence": rows},
        contract=contract,
        scenarios=scenarios,
        verdicts=verdicts,
        strength=strength,
        dependencies_allowlisted=dependencies_allowlisted,
        signer=signer,
    )
