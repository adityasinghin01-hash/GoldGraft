"""Qualified callback ingress (pieces.backend.callback_gateway).

Protocol boundary (IR04)
------------------------
1. The original bytes are accepted and made durable as an *unverified* receipt.
2. The caller may then acknowledge the provider.
3. Verification is a separate, retryable step against the pinned provider
   endpoint. Its result is one of ``verified``, ``invalid``, ``unknown`` or
   ``unverified``.
4. No business effect is applied unless verification is ``verified`` *and* the
   business binding matches.

Verification failure never becomes success. There is no mock header, no string
inspection of a signature field and no certificate-URL prefix heuristic: those
were false positives and are gone. A missing verifier yields ``unverified``,
which is not a pass.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from urllib.parse import parse_qsl

import httpx
from goldgraft_contracts.common import Producer, ProducerKind
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

from .payment_broker import to_minor_units

Verification = Literal["verified", "invalid", "unknown", "unverified"]

IPN_SANDBOX = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
IPN_LIVE = "https://ipnpb.paypal.com/cgi-bin/webscr"
WEBHOOK_VERIFY_SANDBOX = "https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature"


class IpnVerifier(Protocol):
    def verify(self, raw_body: str, headers: dict[str, str]) -> Verification: ...


class WebhookVerifier(Protocol):
    def verify(self, payload: dict[str, Any], headers: dict[str, str]) -> Verification: ...


@dataclass
class IngressReceipt:
    delivery_id: str
    """Identity of the delivered message, used for deduplication."""

    verification: Verification
    status: str
    event_type: str
    ledger_seq: int
    summary: str
    applied: bool = False
    binding_checked: bool = False
    binding_ok: bool | None = None
    holds: list[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        """A pass is only ever an explicit ``verified`` verification."""
        return self.verification == "verified"


def _check_status(verification: Verification) -> str:
    return {
        "verified": "pass",
        "invalid": "failed",
        "unknown": "unknown",
        "unverified": "missing",
    }[verification]


class IpnPostbackVerifier:
    """Real IPN postback validation against the pinned PayPal endpoint."""

    def __init__(self, *, sandbox: bool = True, transport: Any | None = None):
        self.endpoint = IPN_SANDBOX if sandbox else IPN_LIVE
        self.transport = transport if transport is not None else httpx

    def verify(self, raw_body: str, headers: dict[str, str]) -> Verification:
        body = f"cmd=_notify-validate&{raw_body}".encode()
        try:
            response = self.transport.post(
                self.endpoint,
                content=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
        except Exception:
            return "unknown"
        if response.status_code != 200:
            return "unknown"
        text = (response.text or "").strip()
        if text == "VERIFIED":
            return "verified"
        if text == "INVALID":
            return "invalid"
        return "unknown"


class WebhookSignatureVerifier:
    """Real Orders v2 webhook signature validation against PayPal's API."""

    def __init__(self, *, token: str, webhook_id: str, transport: Any | None = None):
        if not token or not webhook_id:
            raise ValueError("webhook verification requires an access token and webhook id")
        self.token = token
        self.webhook_id = webhook_id
        self.transport = transport if transport is not None else httpx

    def verify(self, payload: dict[str, Any], headers: dict[str, str]) -> Verification:
        request = {
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "cert_url": headers.get("paypal-cert-url"),
            "auth_algo": headers.get("paypal-auth-algo"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "webhook_id": self.webhook_id,
            "webhook_event": payload,
        }
        if not all(request[key] for key in ("transmission_id", "transmission_sig", "auth_algo")):
            return "invalid"
        try:
            response = self.transport.post(
                WEBHOOK_VERIFY_SANDBOX,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=request,
                timeout=10.0,
            )
        except Exception:
            return "unknown"
        if response.status_code != 200:
            return "unknown"
        status = response.json().get("verification_status")
        if status == "SUCCESS":
            return "verified"
        if status == "FAILURE":
            return "invalid"
        return "unknown"


class CallbackGateway:
    """Durable ingress, separate verification, and binding-gated effects."""

    def __init__(
        self,
        ledger: Ledger | None = None,
        *,
        ipn_verifier: IpnVerifier | None = None,
        webhook_verifier: WebhookVerifier | None = None,
    ):
        self.ledger = ledger or Ledger()
        self.ipn_verifier = ipn_verifier
        self.webhook_verifier = webhook_verifier
        self._receipts: dict[str, IngressReceipt] = {}

    # ------------------------------------------------------------------
    # IPN
    # ------------------------------------------------------------------

    def handle_ipn(
        self,
        raw_body: str,
        headers: dict[str, str],
        *,
        graft_id: str,
        sandbox: bool = True,
        expected: dict[str, Any] | None = None,
    ) -> IngressReceipt:
        """Accept, receipt, verify and only then apply one IPN message."""
        normalized = {str(k).lower(): str(v) for k, v in headers.items()}
        delivery_id = normalized.get("paypal-delivery-id") or hashlib.sha256(
            raw_body.encode("utf-8")
        ).hexdigest()[:16]

        prior = self._receipts.get(delivery_id)
        if prior is not None:
            return IngressReceipt(
                delivery_id=delivery_id,
                verification=prior.verification,
                status="DUPLICATE",
                event_type=prior.event_type,
                ledger_seq=prior.ledger_seq,
                summary=f"Duplicate delivery {delivery_id}; no second effect",
                applied=False,
                binding_checked=prior.binding_checked,
                binding_ok=prior.binding_ok,
            )

        parsed = {str(k).lower(): v for k, v in parse_qsl(raw_body)}
        event_type = "IPN"
        # Step 1: durable unverified receipt before any network verification.
        seq = self._record(graft_id, delivery_id, "unverified", "missing", "IPN received")

        # Step 2: verification is separate and never synthesized.
        if self.ipn_verifier is None:
            verification: Verification = "unverified"
            holds = ["no IPN postback verifier configured"]
        else:
            try:
                verification = self.ipn_verifier.verify(raw_body, normalized)
            except Exception:
                verification = "unknown"
            holds = [] if verification == "verified" else [f"IPN verification {verification}"]

        # Step 3: business binding, only meaningful after a verified message.
        binding_checked = expected is not None
        binding_ok: bool | None = None
        if binding_checked:
            binding_ok, binding_holds = self._bind_ipn(parsed, expected or {})
            holds.extend(binding_holds)

        applied = verification == "verified" and binding_ok is not False
        if verification == "verified" and binding_ok is False:
            holds.append("verified message does not match the recorded business intent")

        receipt = IngressReceipt(
            delivery_id=delivery_id,
            verification=verification,
            status="APPLIED" if applied else verification.upper(),
            event_type=event_type,
            ledger_seq=seq,
            summary=f"IPN {parsed.get('payment_status', 'UNKNOWN')} {delivery_id}",
            applied=applied,
            binding_checked=binding_checked,
            binding_ok=binding_ok,
            holds=holds,
        )
        self._receipts[delivery_id] = receipt
        self._record(
            graft_id,
            delivery_id,
            verification,
            _check_status(verification),
            f"IPN verification {verification} applied={applied}",
        )
        return receipt

    def _bind_ipn(
        self, parsed: dict[str, str], expected: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        holds: list[str] = []
        for key in ("txn_id", "receiver_email", "payment_status"):
            if key in expected and parsed.get(key) != str(expected[key]):
                holds.append(f"IPN {key} does not match the recorded intent")
        if "amount_minor" in expected:
            currency = parsed.get("mc_currency", "")
            if currency != str(expected.get("currency")):
                holds.append("IPN currency does not match the recorded intent")
            else:
                try:
                    observed = to_minor_units(parsed.get("mc_gross", ""), currency)
                except Exception:
                    holds.append("IPN gross amount is not exactly representable")
                else:
                    if observed != int(expected["amount_minor"]):
                        holds.append("IPN gross amount does not match the recorded intent")
        return (not holds), holds

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    def handle_webhook(
        self,
        event_payload: dict[str, Any],
        headers: dict[str, str],
        *,
        graft_id: str,
        webhook_id: str | None = None,
        auth_token: str | None = None,
        expected: dict[str, Any] | None = None,
    ) -> IngressReceipt:
        """Accept, receipt, verify and only then apply one webhook event."""
        normalized = {str(k).lower(): str(v) for k, v in headers.items()}
        event_id = event_payload.get("id")
        delivery_id = (
            normalized.get("paypal-transmission-id")
            or str(event_id)
            or hashlib.sha256(str(sorted(event_payload.items())).encode()).hexdigest()[:16]
        )

        prior = self._receipts.get(delivery_id)
        if prior is not None:
            return IngressReceipt(
                delivery_id=delivery_id,
                verification=prior.verification,
                status="DUPLICATE",
                event_type=prior.event_type,
                ledger_seq=prior.ledger_seq,
                summary=f"Duplicate transmission {delivery_id}; no second effect",
                applied=False,
                binding_checked=prior.binding_checked,
                binding_ok=prior.binding_ok,
            )

        event_type = str(event_payload.get("event_type", "UNKNOWN"))
        seq = self._record(graft_id, delivery_id, "unverified", "missing", "webhook received")

        verifier = self.webhook_verifier
        if verifier is None and auth_token and webhook_id:
            verifier = WebhookSignatureVerifier(token=auth_token, webhook_id=webhook_id)
        if verifier is None:
            verification: Verification = "unverified"
            holds = ["no webhook signature verifier configured"]
        else:
            try:
                verification = verifier.verify(event_payload, normalized)
            except Exception:
                verification = "unknown"
            holds = [] if verification == "verified" else [f"webhook verification {verification}"]

        binding_checked = expected is not None
        binding_ok: bool | None = None
        if binding_checked:
            binding_ok, binding_holds = self._bind_webhook(event_payload, expected or {})
            holds.extend(binding_holds)

        applied = verification == "verified" and binding_ok is not False
        receipt = IngressReceipt(
            delivery_id=delivery_id,
            verification=verification,
            status="APPLIED" if applied else verification.upper(),
            event_type=event_type,
            ledger_seq=seq,
            summary=f"webhook {event_type} {delivery_id}",
            applied=applied,
            binding_checked=binding_checked,
            binding_ok=binding_ok,
            holds=holds,
        )
        self._receipts[delivery_id] = receipt
        self._record(
            graft_id,
            delivery_id,
            verification,
            _check_status(verification),
            f"webhook verification {verification} applied={applied}",
        )
        return receipt

    def _bind_webhook(
        self, payload: dict[str, Any], expected: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        holds: list[str] = []
        resource = payload.get("resource") or {}
        if "order_id" in expected:
            wanted = str(expected["order_id"])
            candidates = {str(resource.get("id") or "")}
            related = (resource.get("supplementary_data") or {}).get("related_ids") or {}
            if related.get("order_id"):
                candidates.add(str(related["order_id"]))
            for unit in resource.get("purchase_units") or []:
                payments = unit.get("payments") or {}
                for capture in payments.get("captures") or []:
                    for key in ("custom_id", "invoice_id"):
                        if capture.get(key):
                            candidates.add(str(capture[key]))
            candidates.discard("")
            if wanted not in candidates:
                holds.append("webhook resource is not the recorded order")
        if "currency" in expected:
            currency = ((resource.get("amount") or {}).get("currency_code")) or ""
            if currency != str(expected["currency"]):
                holds.append("webhook currency does not match the recorded intent")
        if "amount_minor" in expected:
            amount = (resource.get("amount") or {}).get("value")
            currency = (resource.get("amount") or {}).get("currency_code") or ""
            if amount is not None:
                try:
                    observed_minor = to_minor_units(str(amount), str(currency))
                except Exception:
                    holds.append("webhook amount is not exactly representable")
                else:
                    if observed_minor != int(expected["amount_minor"]):
                        holds.append("webhook amount does not match the recorded intent")
        return (not holds), holds

    # ------------------------------------------------------------------

    def _record(
        self, graft_id: str, delivery_id: str, verification: Verification, status: str, note: str
    ) -> int:
        producer = Producer(kind=ProducerKind.SERVICE, name="CallbackGateway", version="2.0.0")
        payload = {
            "check_id": f"cb-{hashlib.sha256(delivery_id.encode()).hexdigest()[:16]}",
            "status": status,
            "evidence_refs": [f"blob://callbacks/{delivery_id}"],
            "checked_at": datetime.now(UTC).isoformat(),
            "expires_at": None,
            "recovery_code": None,
        }
        entry = self.ledger.append(
            graft_id=graft_id,
            type=EntryType.ARTIFACT.value,
            producer=producer.model_dump(),
            schema="CheckResult/1",
            payload=payload,
            idempotency_key=f"cb-{delivery_id}-{status}-{note[:32]}",
        )
        return entry.seq
