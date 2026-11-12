"""Typed Payment Broker (pieces.backend.payment_broker).

Evidence boundary
-----------------
Every response is either

* ``scripted``  - generated in process. It is a wire-shape cipher, never evidence
  of provider behaviour.
* ``real_sandbox`` - produced by an actual HTTP exchange with a pinned sandbox
  endpoint.

There is no fallback path. A refused, failed or uncertain sandbox request
raises, and can never become a synthetic success. ``BrokerResponse`` enforces
the invariant that a simulated response is never labelled real.

Money stays integer minor units plus an ISO 4217 code inside the broker; the
exact provider decimal string only exists at the wire boundary.

No function here opens a socket unless ``mode == "sandbox"`` and a real
transport is configured. Ordinary tests inject a transport or stay synthetic.
"""

import base64
import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from threading import RLock
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode

import httpx
from goldgraft_contracts.offline_payments import PaymentAccessDenied
from goldgraft_foundation.ledger import Ledger

from pieces.backend.custody_broker import CustodyBroker

BrokerMode = Literal["synthetic", "sandbox"]
Outcome = Literal["ok", "failed", "unknown"]
BrokerEvidenceClass = Literal["scripted", "real_sandbox"]

REST_SANDBOX = "https://api-m.sandbox.paypal.com"
NVP_SANDBOX = "https://api-3t.sandbox.paypal.com/nvp"
NVP_VERSION = "204.0"

# PayPal settles these currencies in the listed minor-unit exponent. An
# unlisted currency is refused rather than guessed.
CURRENCY_EXPONENTS = {
    "AUD": 2,
    "CAD": 2,
    "CHF": 2,
    "EUR": 2,
    "GBP": 2,
    "HKD": 2,
    "JPY": 0,
    "NZD": 2,
    "SGD": 2,
    "USD": 2,
}


class SecretDeniedError(PaymentAccessDenied):
    """Raised when a secret reference cannot be securely resolved or is empty."""


class RateLimitExceededError(Exception):
    """Raised when request limits exceed sandbox safety bounds (>50 req/min)."""


class BrokerRefused(Exception):
    """No real exchange could be attempted for the requested operation."""


class BrokerRequestFailed(Exception):
    """The provider answered and the exchange failed."""


class BrokerOutcomeUnknown(Exception):
    """The request may or may not have taken effect; it must be reconciled."""


def to_minor_units(amount: str, currency: str) -> int:
    """Exact decimal->minor-unit conversion; refuses unrepresentable input."""
    exponent = CURRENCY_EXPONENTS.get(currency.upper())
    if exponent is None:
        raise BrokerRefused(f"Unsupported currency for exact settlement: {currency!r}")
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError) as exc:
        raise BrokerRefused(f"Unparseable provider amount: {amount!r}") from exc
    if not value.is_finite():
        raise BrokerRefused("Non-finite money is forbidden")
    scaled = value.scaleb(exponent)
    if scaled != scaled.to_integral_value():
        raise BrokerRefused(f"Amount {amount!r} has more precision than {currency} allows")
    return int(scaled)


def to_provider_amount(minor: int, currency: str) -> str:
    """Format integer minor units as the exact provider decimal string."""
    exponent = CURRENCY_EXPONENTS.get(currency.upper())
    if exponent is None:
        raise BrokerRefused(f"Unsupported currency for exact settlement: {currency!r}")
    if not isinstance(minor, int) or isinstance(minor, bool):
        raise BrokerRefused("Money must be integer minor units, never float")
    value = Decimal(minor).scaleb(-exponent)
    return f"{value:.{exponent}f}"


@dataclass
class BrokerResponse:
    operation: str
    status_code: int
    data: dict[str, Any]
    exchange_ref: str
    duration_ms: float
    simulated: bool
    evidence_class: BrokerEvidenceClass
    outcome: Outcome = "ok"
    correlation_id: str | None = None

    def __post_init__(self):
        if self.simulated != (self.evidence_class == "scripted"):
            raise ValueError("synthetic exchange cannot be labelled as real sandbox evidence")
        if self.outcome == "ok" and self.simulated and "ACK" in self.data:
            if not str(self.data["ACK"]).startswith("Success"):
                raise ValueError("synthetic NVP response must not claim success")
        if self.evidence_class == "real_sandbox" and not self.correlation_id:
            raise ValueError("real sandbox response requires a provider correlation id")


def _success_ack(value: Any) -> bool:
    return str(value or "").split("/")[0] == "Success"


def _validate_wire_money(value):
    """Provider amounts are exact strings at this boundary, never floats/NaN."""
    if isinstance(value, float):
        raise BrokerRefused("Money must never use floating point")
    if isinstance(value, dict):
        if "currency_code" in value and "value" in value:
            to_minor_units(value["value"], value["currency_code"])
        if "AMT" in value:
            to_minor_units(value["AMT"], value.get("CURRENCYCODE", "USD"))
        for item in value.values():
            _validate_wire_money(item)
    elif isinstance(value, list):
        for item in value:
            _validate_wire_money(item)


# Locks cover validation, dispatch and cache commit. Unknown in-process requests
# cannot be blindly dispatched again; process-restart reconciliation is still a
# required live-profile prerequisite (this cache is deliberately not a ledger).
def _serialized_operation(method):
    from functools import wraps

    @wraps(method)
    def call(self, *args, **kwargs):
        with self._lock:
            try:
                return method(self, *args, **kwargs)
            except BrokerOutcomeUnknown:
                # The family/key was validated and registered before dispatch.
                key = kwargs.get("idempotency_key")
                secret_ref = kwargs.get("secret_ref")
                graft_id = kwargs.get("graft_id", "default")
                if key is not None:
                    family = "nvp" if method.__name__ == "execute_nvp" else "v2"
                    self._unknown_requests.add(repr((self.mode, family, graft_id, secret_ref, key)))
                raise

    return call


class PaymentBroker:
    """Typed NVP and Orders v2 broker with a strict evidence boundary."""

    def __init__(
        self,
        custody_broker: CustodyBroker | None = None,
        ledger: Ledger | None = None,
        rate_limit_per_min: int = 50,
        live: bool = False,
        *,
        mode: BrokerMode | None = None,
        transport: Any | None = None,
        authorize=None,
        database=None,
        **kwargs: Any,
    ):
        self.custody = custody_broker or CustodyBroker()
        self.ledger = ledger or Ledger()
        if type(rate_limit_per_min) is not int or not 1 <= rate_limit_per_min <= 50:
            raise ValueError("Sandbox rate limit must be between 1 and 50")
        self.rate_limit_per_min = rate_limit_per_min
        self.authorize = authorize
        self._lock = RLock()
        self._request_digests = {}
        self._unknown_requests = set()
        self._journal = None
        if database is not None:
            self._journal = sqlite3.connect(database, check_same_thread=False)
            self._journal.execute(
                "CREATE TABLE IF NOT EXISTS payment_requests "
                "(request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)"
            )
        if mode is None:
            mode = "sandbox" if live else "synthetic"
        if mode not in ("synthetic", "sandbox"):
            raise ValueError(f"Unknown broker mode: {mode!r}")
        self.mode: BrokerMode = mode
        self.transport = transport if transport is not None else httpx
        self._request_history: list[float] = []
        self._idempotent_cache: dict[str, BrokerResponse] = {}

    def _authorize(self, graft_id, operation, payload, secret_ref):
        if self.mode == "sandbox":
            if self._journal is None:
                raise BrokerRefused("Durable sandbox request journal required")
            if (
                self.authorize is None
                or self.authorize(graft_id, operation, payload, secret_ref) is not True
            ):
                raise BrokerRefused("Current accepted-work/payment/origin authority required")

    def _request_key(self, family, operation, payload, secret_ref, graft_id, key):
        if self.mode == "sandbox" and not key:
            raise BrokerRefused("Sandbox operations require a stable logical request identity")
        if key is None:
            return None
        import json

        cache_key = repr((self.mode, family, graft_id, secret_ref, key))
        fingerprint = hashlib.sha256(
            json.dumps(
                [operation, payload], sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        if self._request_digests.setdefault(cache_key, fingerprint) != fingerprint:
            raise BrokerRefused("Idempotency identity reused with different operation/payload")
        if cache_key in self._unknown_requests:
            raise BrokerOutcomeUnknown("Prior request outcome unknown; reconcile before retry")
        if self.mode == "sandbox" and cache_key not in self._idempotent_cache:
            request_id = hashlib.sha256(cache_key.encode()).hexdigest()
            with self._journal:
                prior = self._journal.execute(
                    "SELECT fingerprint FROM payment_requests WHERE request_id = ?", (request_id,)
                ).fetchone()
                if prior:
                    if prior[0] != fingerprint:
                        raise BrokerRefused("Durable payment idempotency conflict")
                    raise BrokerOutcomeUnknown("Recorded sandbox request requires reconciliation")
                self._journal.execute(
                    "INSERT INTO payment_requests VALUES (?, ?)", (request_id, fingerprint)
                )
        return cache_key

    def close(self):
        if self._journal is not None:
            self._journal.close()

    @property
    def live(self) -> bool:
        return self.mode == "sandbox"

    @property
    def evidence_class(self) -> str:
        """What any response this broker produces can honestly be labelled."""
        return "real_sandbox" if self.mode == "sandbox" else "scripted"

    def _check_rate_limit(self, now: float) -> None:
        window = now - 60.0
        self._request_history = [t for t in self._request_history if t > window]
        if len(self._request_history) >= self.rate_limit_per_min:
            raise RateLimitExceededError("Rate limit exceeded: >50 requests per minute in sandbox")
        self._request_history.append(now)

    def resolve_and_verify(self, secret_ref: str) -> dict[str, str]:
        """Resolves secrets from custody broker. Denies immediately if missing or empty."""
        if not secret_ref or not secret_ref.startswith("doppler://"):
            raise SecretDeniedError(f"Invalid secret reference scheme: {secret_ref!r}")
        creds = self.custody.resolve_credentials(secret_ref)
        if not creds:
            raise SecretDeniedError(
                f"Secret reference cannot be resolved or is empty: {secret_ref}"
            )
        return creds

    # ------------------------------------------------------------------
    # Synthetic path (never evidence)
    # ------------------------------------------------------------------

    def _synthetic_nvp(
        self, operation: str, params: dict[str, str], *, graft_id: str
    ) -> BrokerResponse:
        start_time = datetime.now(UTC)
        currency = params.get("CURRENCYCODE", "USD")
        amount = params.get("AMT", "10.00")
        resp_data: dict[str, str] = {
            "ACK": "Success",
            "TIMESTAMP": start_time.isoformat(),
            "CORRELATIONID": hashlib.sha256(f"nvp:{operation}:{start_time}".encode())
            .hexdigest()[:12]
            .upper(),
            "VERSION": NVP_VERSION,
        }
        if operation == "SetExpressCheckout":
            resp_data["TOKEN"] = (
                "EC-" + hashlib.sha256(f"tok:{start_time}".encode()).hexdigest()[:17].upper()
            )
        elif operation == "GetExpressCheckoutDetails":
            resp_data["TOKEN"] = params.get("TOKEN", "EC-UNKNOWN")
            resp_data["CHECKOUTSTATUS"] = "PaymentActionNotInitiated"
            resp_data["PAYERID"] = "PAYER-" + hashlib.sha256(b"payer").hexdigest()[:13].upper()
            resp_data["AMT"] = amount
            resp_data["CURRENCYCODE"] = currency
        elif operation == "DoExpressCheckoutPayment":
            resp_data["TOKEN"] = params.get("TOKEN", "EC-UNKNOWN")
            resp_data["PAYMENTINFO_0_TRANSACTIONID"] = (
                "TXN-" + hashlib.sha256(f"do:{start_time}".encode()).hexdigest()[:17].upper()
            )
            resp_data["PAYMENTINFO_0_PAYMENTSTATUS"] = "Completed"
            resp_data["PAYMENTINFO_0_AMT"] = amount
            resp_data["PAYMENTINFO_0_CURRENCYCODE"] = currency
        elif operation == "RefundTransaction":
            resp_data["REFUNDTRANSACTIONID"] = (
                "REF-" + hashlib.sha256(f"ref:{start_time}".encode()).hexdigest()[:17].upper()
            )
            resp_data["GROSSREFUNDAMT"] = amount
            resp_data["CURRENCYCODE"] = currency

        return BrokerResponse(
            operation=operation,
            status_code=200,
            data=resp_data,
            exchange_ref=f"blob://exchanges/{graft_id}/scripted-{operation.lower()}",
            duration_ms=0.0,
            simulated=True,
            evidence_class="scripted",
        )

    def _synthetic_orders_v2(
        self, action: str, payload: dict[str, Any], *, graft_id: str
    ) -> BrokerResponse:
        start_time = datetime.now(UTC)
        resp_data: dict[str, Any] = {}
        if action == "create":
            order_id = (
                "ORD-" + hashlib.sha256(f"v2ord:{start_time}".encode()).hexdigest()[:17].upper()
            )
            resp_data = {
                "id": order_id,
                "status": "CREATED",
                "intent": payload.get("intent", "CAPTURE"),
                "purchase_units": payload.get("purchase_units", []),
            }
        elif action == "capture":
            capture_id = (
                "CAP-" + hashlib.sha256(f"v2cap:{start_time}".encode()).hexdigest()[:17].upper()
            )
            resp_data = {
                "id": payload.get("order_id", "ORD-UNKNOWN"),
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": capture_id,
                                    "status": "COMPLETED",
                                    "amount": payload.get(
                                        "amount", {"currency_code": "USD", "value": "10.00"}
                                    ),
                                    "create_time": start_time.isoformat(),
                                }
                            ]
                        }
                    }
                ],
            }
        elif action == "refund":
            refund_ref = hashlib.sha256(f"v2ref:{start_time}".encode()).hexdigest()[:17].upper()
            resp_data = {
                "id": "REF-" + refund_ref,
                "status": "COMPLETED",
                "amount": payload.get("amount", {"currency_code": "USD", "value": "10.00"}),
            }
        elif action == "get_order":
            order_id = payload.get("order_id") or payload.get("id", "ORD-UNKNOWN")
            resp_data = {
                "id": order_id,
                "status": "COMPLETED",
                "intent": "CAPTURE",
                "purchase_units": payload.get("purchase_units", []),
            }
        elif action == "get_capture":
            capture_id = payload.get("capture_id") or payload.get("id", "CAP-UNKNOWN")
            resp_data = {
                "id": capture_id,
                "status": "COMPLETED",
                "amount": payload.get("amount", {"currency_code": "USD", "value": "10.00"}),
            }
        elif action == "get_refund":
            refund_id = payload.get("refund_id") or payload.get("id", "REF-UNKNOWN")
            resp_data = {
                "id": refund_id,
                "status": "COMPLETED",
                "amount": payload.get("amount", {"currency_code": "USD", "value": "10.00"}),
            }
        else:
            raise BrokerRefused(f"Unknown orders v2 action: {action}")
        resp_data["_evidence_class"] = "scripted"
        return BrokerResponse(
            operation=f"orders_v2_{action}",
            status_code=201 if action == "create" else 200,
            data=resp_data,
            exchange_ref=f"blob://exchanges/{graft_id}/scripted-v2-{action}",
            duration_ms=0.0,
            simulated=True,
            evidence_class="scripted",
        )

    # ------------------------------------------------------------------
    # Sandbox path (real exchanges only; raises instead of substituting)
    # ------------------------------------------------------------------

    def _sandbox_get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        operation: str,
    ) -> dict[str, Any]:
        self._check_rate_limit(datetime.now(UTC).timestamp())
        try:
            response = self.transport.get(url, headers=headers, timeout=15.0)
        except Exception as exc:  # transport uncertainty, never a synthetic success
            raise BrokerOutcomeUnknown(
                f"{operation}: transport failed after dispatch; provider state unknown"
            ) from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise BrokerOutcomeUnknown(
                f"{operation}: HTTP {response.status_code}; provider state unknown"
            )
        if response.status_code >= 400:
            raise BrokerRequestFailed(f"{operation}: HTTP {response.status_code}")
        try:
            return response.json()
        except (ValueError, TypeError):
            raise BrokerOutcomeUnknown(f"{operation}: malformed provider response") from None

    def _sandbox_post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json_body: Any | None = None,
        content: bytes | None = None,
        operation: str,
    ) -> dict[str, Any] | str:
        self._check_rate_limit(datetime.now(UTC).timestamp())
        try:
            if content is not None:
                response = self.transport.post(url, headers=headers, content=content, timeout=15.0)
            else:
                response = self.transport.post(url, headers=headers, json=json_body, timeout=15.0)
        except Exception as exc:  # transport uncertainty, never a synthetic success
            raise BrokerOutcomeUnknown(
                f"{operation}: transport failed after dispatch; provider state unknown"
            ) from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise BrokerOutcomeUnknown(
                f"{operation}: HTTP {response.status_code}; provider state unknown"
            )
        if response.status_code >= 400:
            raise BrokerRequestFailed(f"{operation}: HTTP {response.status_code}")
        try:
            return response.text if content is not None else response.json()
        except (ValueError, TypeError):
            raise BrokerOutcomeUnknown(f"{operation}: malformed provider response") from None

    def _sandbox_token(self, client_id: str, client_secret: str) -> str:
        if not client_id or not client_secret:
            raise BrokerRefused("sandbox REST requires client id and secret; no synthetic fallback")
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")
        self._check_rate_limit(datetime.now(UTC).timestamp())
        try:
            response = self.transport.post(
                f"{REST_SANDBOX}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
                timeout=15.0,
            )
        except Exception as exc:
            raise BrokerRequestFailed("sandbox token request failed") from exc
        if response.status_code != 200:
            raise BrokerRequestFailed(f"sandbox token request HTTP {response.status_code}")
        try:
            data = response.json()
            token = data.get("access_token") if isinstance(data, dict) else None
        except (ValueError, TypeError):
            raise BrokerRequestFailed("sandbox token response malformed") from None
        if not token:
            raise BrokerRequestFailed("sandbox token response omitted access_token")
        return str(token)

    @_serialized_operation
    def execute_nvp(
        self,
        operation: str,
        params: dict[str, str],
        *,
        secret_ref: str,
        idempotency_key: str | None = None,
        graft_id: str = "default",
    ) -> BrokerResponse:
        """Executes one typed NVP operation for the configured mode."""
        if operation not in {
            "SetExpressCheckout",
            "GetExpressCheckoutDetails",
            "DoExpressCheckoutPayment",
            "RefundTransaction",
        }:
            raise BrokerRefused("Unsupported NVP operation")
        if {k.upper() for k in params} & {"METHOD", "VERSION", "USER", "PWD", "SIGNATURE"}:
            raise BrokerRefused("NVP credential/method override forbidden")
        _validate_wire_money(params)
        creds = self.resolve_and_verify(secret_ref)
        self._authorize(graft_id, operation, params, secret_ref)
        cache_key = self._request_key(
            "nvp", operation, params, secret_ref, graft_id, idempotency_key
        )
        if cache_key and cache_key in self._idempotent_cache:
            return self._idempotent_cache[cache_key]

        if self.mode == "synthetic":
            response = self._synthetic_nvp(operation, params, graft_id=graft_id)
        else:
            user = creds.get("nvp_user")
            password = creds.get("nvp_password")
            signature = creds.get("nvp_signature")
            if not (user and password and signature):
                raise BrokerRefused(
                    "sandbox NVP requires nvp_user/nvp_password/nvp_signature; "
                    "no synthetic fallback is permitted"
                )
            form = {
                "METHOD": operation,
                "VERSION": NVP_VERSION,
                "USER": user,
                "PWD": password,
                "SIGNATURE": signature,
                **params,
            }
            raw = self._sandbox_post(
                NVP_SANDBOX,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                content=urlencode(form).encode("utf-8"),
                operation=f"NVP {operation}",
            )
            parsed = dict(parse_qsl(str(raw)))
            correlation = parsed.get("CORRELATIONID")
            if not correlation:
                raise BrokerOutcomeUnknown(
                    f"NVP {operation}: response had no correlation id; verify before retry"
                )
            response = BrokerResponse(
                operation=operation,
                status_code=200,
                data=parsed,
                exchange_ref=f"blob://exchanges/{graft_id}/nvp-{operation.lower()}-{correlation}",
                duration_ms=0.0,
                simulated=False,
                evidence_class="real_sandbox",
                outcome="ok" if _success_ack(parsed.get("ACK")) else "failed",
                correlation_id=correlation,
            )

        if cache_key:
            self._idempotent_cache[cache_key] = response
        return response

    @_serialized_operation
    def execute_orders_v2(
        self,
        action: str,
        payload: dict[str, Any],
        *,
        secret_ref: str,
        idempotency_key: str | None = None,
        graft_id: str = "default",
    ) -> BrokerResponse:
        """Executes one typed Orders v2 REST operation for the configured mode."""
        if action not in {
            "create",
            "capture",
            "refund",
            "get_order",
            "get_capture",
            "get_refund",
        }:
            raise BrokerRefused("Unsupported Orders v2 operation")
        if action != "create":
            import re

            identifier = (
                payload.get("order_id")
                if action in ("capture", "get_order")
                else (payload.get("capture_id") or payload.get("refund_id") or payload.get("id"))
            )
            if not isinstance(identifier, str) or not re.fullmatch(
                r"[A-Za-z0-9-]{1,128}", identifier
            ):
                raise BrokerRefused("Invalid payment resource identifier")
        _validate_wire_money(payload)
        creds = self.resolve_and_verify(secret_ref)
        self._authorize(graft_id, action, payload, secret_ref)
        # Re-fetches are read-only: never cached, never journalled as a payment
        # request and never sent with PayPal-Request-Id, so each call observes
        # the provider's current state.
        read_only = action.startswith("get_")
        if read_only:
            idempotency_key = None
            cache_key = None
        else:
            cache_key = self._request_key(
                "v2", action, payload, secret_ref, graft_id, idempotency_key
            )
        if cache_key and cache_key in self._idempotent_cache:
            return self._idempotent_cache[cache_key]

        if self.mode == "synthetic":
            response = self._synthetic_orders_v2(action, payload, graft_id=graft_id)
        else:
            client_id = creds.get("paypal_client_id") or creds.get("client_id", "")
            client_secret = creds.get("paypal_client_secret") or creds.get("client_secret", "")
            token = self._sandbox_token(client_id, client_secret)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            if idempotency_key:
                headers["PayPal-Request-Id"] = idempotency_key
            if action == "create":
                url = f"{REST_SANDBOX}/v2/checkout/orders"
                data = self._sandbox_post(
                    url, headers=headers, json_body=payload, operation="orders v2 create"
                )
            elif action == "capture":
                order_id = payload.get("order_id", "")
                url = f"{REST_SANDBOX}/v2/checkout/orders/{order_id}/capture"
                data = self._sandbox_post(
                    url, headers=headers, json_body={}, operation="orders v2 capture"
                )
            elif action == "refund":
                capture_id = payload.get("capture_id") or payload.get("id", "")
                url = f"{REST_SANDBOX}/v2/payments/captures/{capture_id}/refund"
                # The capture id is a path parameter, not part of PayPal's refund body.
                body = {k: v for k, v in payload.items() if k not in {"capture_id", "id"}}
                data = self._sandbox_post(
                    url, headers=headers, json_body=body, operation="orders v2 refund"
                )
            elif action == "get_order":
                order_id = payload.get("order_id") or payload.get("id", "")
                url = f"{REST_SANDBOX}/v2/checkout/orders/{order_id}"
                data = self._sandbox_get(url, headers=headers, operation="orders v2 get_order")
            elif action == "get_capture":
                capture_id = payload.get("capture_id") or payload.get("id", "")
                url = f"{REST_SANDBOX}/v2/payments/captures/{capture_id}"
                data = self._sandbox_get(url, headers=headers, operation="orders v2 get_capture")
            elif action == "get_refund":
                refund_id = payload.get("refund_id") or payload.get("id", "")
                url = f"{REST_SANDBOX}/v2/payments/refunds/{refund_id}"
                data = self._sandbox_get(url, headers=headers, operation="orders v2 get_refund")
            else:
                raise BrokerRefused(f"Unknown orders v2 action: {action}")

            if not isinstance(data, dict):
                raise BrokerOutcomeUnknown(f"orders v2 {action}: non-object response")
            correlation = str(data.get("id") or "")
            if not correlation:
                raise BrokerOutcomeUnknown(
                    f"orders v2 {action}: response had no provider id; verify before retry"
                )
            status = str(data.get("status", ""))
            response = BrokerResponse(
                operation=f"orders_v2_{action}",
                status_code=201 if action == "create" else 200,
                data=data,
                exchange_ref=f"blob://exchanges/{graft_id}/v2-{action}-{correlation}",
                duration_ms=0.0,
                simulated=False,
                evidence_class="real_sandbox",
                outcome="failed" if status in {"DECLINED", "FAILED"} else "ok",
                correlation_id=correlation,
            )

        if cache_key:
            self._idempotent_cache[cache_key] = response
        return response

    def refetch_capture(
        self,
        capture_id: str,
        *,
        secret_ref: str,
        graft_id: str = "default",
    ) -> BrokerResponse:
        """Re-fetches the capture record from PayPal (read-only, uncached)."""
        return self.execute_orders_v2(
            "get_capture",
            {"capture_id": capture_id},
            secret_ref=secret_ref,
            graft_id=graft_id,
        )

    def refetch_refund(
        self,
        refund_id: str,
        *,
        secret_ref: str,
        graft_id: str = "default",
    ) -> BrokerResponse:
        """Re-fetches the refund record from PayPal (read-only, uncached)."""
        return self.execute_orders_v2(
            "get_refund",
            {"refund_id": refund_id},
            secret_ref=secret_ref,
            graft_id=graft_id,
        )

    def refetch_order(
        self,
        order_id: str,
        *,
        secret_ref: str,
        graft_id: str = "default",
    ) -> BrokerResponse:
        """Re-fetches the order record from PayPal (read-only, uncached)."""
        return self.execute_orders_v2(
            "get_order",
            {"order_id": order_id},
            secret_ref=secret_ref,
            graft_id=graft_id,
        )
