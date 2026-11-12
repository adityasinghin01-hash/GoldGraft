"""Opt-in reference-shop recorder for the pinned PayPal sandbox (play money).

The loopback proxy owns credentials in memory; PHP receives placeholders. OAuth
bodies are recorded with credential/token fields redacted. Payment bodies, ids,
statuses and timings come from the wire. No redirects, retries or fake fallback.
"""

import base64
import json
import math
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

from integration.local_shop import KEEP_HEADERS, Recorder
from pieces.backend.payment_broker import REST_SANDBOX, to_minor_units

REAL_SCENARIOS = frozenset({"HAPPY", "REFUND", "REFUND_TWICE", "DOUBLE", "DECLINE"})
ID = r"[A-Za-z0-9-]{1,128}"
ORDER = re.compile(rf"/v2/checkout/orders/({ID})(/capture)?")
PAYMENT = re.compile(rf"/v2/payments/(captures|refunds)/({ID})(/refund)?")


class SandboxHeld(RuntimeError):
    """Safe local diagnostic, containing no provider payload or credentials."""


class SandboxReadUnavailable(SandboxHeld):
    """A read had no response; safe to retry only within bounded approval polling."""


def amount_minor(amount):
    if not isinstance(amount, dict) or not isinstance(amount.get("value"), str):
        raise ValueError("missing exact provider amount")
    currency = amount.get("currency_code")
    if not isinstance(currency, str):
        raise ValueError("missing currency")
    return to_minor_units(amount["value"], currency), currency


def require_id(body, what):
    value = body.get("id")
    if not isinstance(value, str) or not re.fullmatch(ID, value):
        raise SandboxHeld(f"PayPal response has no valid {what} id; stopping")
    return value


def recorded_resources(capture, *, strict=True):
    """All successful POST capture/refund resources, including idempotent repeats."""
    result = {}
    for ex in capture["exchanges"]:
        if ex["direction"] != "PAYPAL_TO_SHOP" or ex["method"] != "POST":
            continue
        if not 200 <= ex.get("status", 0) < 300:
            continue
        path = httpx.URL(ex["url"]).path
        body = ex.get("body_json") or {}
        if ORDER.fullmatch(path) and path.endswith("/capture"):
            rows = [
                cap
                for unit in body.get("purchase_units", [])
                for cap in unit.get("payments", {}).get("captures", [])
            ]
            if not rows and strict:
                raise SandboxHeld("PayPal response has no capture id; stopping")
            kind = "capture"
        elif PAYMENT.fullmatch(path) and path.endswith("/refund"):
            rows, kind = [body], "refund"
        else:
            continue
        for row in rows:
            try:
                rid = require_id(row, kind)
            except SandboxHeld:
                if strict:
                    raise
                continue  # No invented id; other known resources still need reconciliation.
            try:
                amount = amount_minor(row.get("amount"))
            except Exception:
                if strict:
                    raise
                amount = None  # Re-fetch the known id, but never qualify missing money evidence.
            key = (kind, rid)
            if key in result and result[key] != amount:
                raise ValueError("provider resource amount changed in recording")
            result[key] = amount
    return result


class SandboxProxy:
    """Forward only this run's Orders/Payments calls to api-m.sandbox.paypal.com."""

    real_sandbox = True

    def __init__(
        self,
        scenario,
        *,
        credentials,
        authorize_payment=False,
        transport=None,
        show_approval=None,
        approval_timeout_s=600,
        poll_s=5,
    ):
        if not authorize_payment:
            raise ValueError("--authorize-sandbox-payment is required")
        if scenario not in REAL_SCENARIOS:
            raise ValueError("scenario requires the stand-in")
        if not all(credentials.get(k) for k in ("PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET")):
            raise ValueError("sandbox credentials are required")
        if (
            not math.isfinite(approval_timeout_s)
            or not math.isfinite(poll_s)
            or approval_timeout_s < 0
            or poll_s < 0
        ):
            raise ValueError("approval timeout and polling interval must be finite and nonnegative")
        self.scenario = scenario
        self._credentials = dict(credentials)
        self._token = None
        self.recorder = Recorder(f"SHOP-{scenario}")
        self.orders, self.captures, self.refunds = {}, {}, {}
        self.approved = set()
        self.error = None
        self.show_approval = show_approval or (
            lambda url: print(f"Approve as the sandbox buyer: {url}", flush=True)
        )
        self.approval_timeout_s, self.poll_s = approval_timeout_s, poll_s
        self.client = httpx.Client(
            transport=transport, follow_redirects=False, trust_env=False, timeout=30
        )
        self.lock = threading.RLock()
        proxy = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _handle(self):
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if size < 0 or size > 1024 * 1024:
                        raise ValueError("unsupported request size")
                    status, headers, raw = proxy.exchange(
                        self.command, self.path, dict(self.headers), self.rfile.read(size)
                    )
                except Exception as exc:
                    # Exception text from HTTP libraries may contain wire data. Never log it.
                    with proxy.lock:
                        if proxy.error is None:
                            proxy.error = exc
                    status, headers, raw = 502, {}, b'{"error":"sandbox proxy held; see report"}'
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = _handle

        self.handler_class = Handler
        self.server = None

    def start(self):
        """Bind loopback only when the PHP runner actually needs the proxy."""
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler_class)
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.05), daemon=True
        )
        self.thread.start()

    def scrub(self, value):
        if isinstance(value, dict):
            return {
                k: "[REDACTED]"
                if k.lower()
                in {
                    "access_token",
                    "refresh_token",
                    "client_secret",
                    "client_id",
                    "id_token",
                }
                else self.scrub(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [self.scrub(v) for v in value]
        if isinstance(value, str):
            for secret in (*self._credentials.values(), self._token):
                if secret:
                    value = value.replace(secret, "[REDACTED]")
        return value

    def _record(self, direction, method, path, headers, raw, status=None):
        try:
            body = {"body_json": self.scrub(json.loads(raw))}
        except ValueError:
            body = {"body_text": self.scrub(raw.decode())}
        self.recorder.add(
            direction,
            method,
            REST_SANDBOX + path,
            self.scrub(headers),
            status=status,
            extra={k: v for k, v in headers.items() if k.lower() == "paypal-mock-response"},
            **body,
        )

    def exchange(self, method, path, headers, raw=b""):
        with self.lock:
            if self.error is not None and method != "GET":
                raise SandboxHeld("sandbox run held after earlier failure; writes refused")
            try:
                return self._exchange(method, path, headers, raw)
            except Exception as exc:
                if self.error is None and not isinstance(exc, SandboxReadUnavailable):
                    self.error = exc
                raise

    def _exchange(self, method, path, headers, raw):
        order, payment = ORDER.fullmatch(path), PAYMENT.fullmatch(path)
        oauth = path == "/v1/oauth2/token" and method == "POST"
        create = path == "/v2/checkout/orders" and method == "POST"
        capture = bool(order and order[2] and method == "POST")
        refund = bool(payment and payment[1] == "captures" and payment[3] and method == "POST")
        read = method == "GET" and ((order and not order[2]) or (payment and not payment[3]))
        if not (oauth or create or capture or refund or read):
            raise ValueError("unsupported sandbox path or method")
        if capture and order[1] not in self.approved:
            raise SandboxHeld("capture refused before buyer approval")
        if order and order[1] not in self.orders:
            raise ValueError("order path is outside this run")
        if payment:
            known = self.captures if payment[1] == "captures" else self.refunds
            if payment[2] not in known:
                raise ValueError("payment path is outside this run")
        outbound = {
            k: v
            for k, v in headers.items()
            if k.lower() in {"content-type", "paypal-request-id", "prefer", "x-goldgraft-ledger"}
        }
        outbound.setdefault("Content-Type", "application/json")
        if oauth:
            # Only the fixed client-credentials grant reaches PayPal; PHP never sees credentials.
            raw = b"grant_type=client_credentials"
            basic = base64.b64encode(
                (
                    self._credentials["PAYPAL_CLIENT_ID"]
                    + ":"
                    + self._credentials["PAYPAL_CLIENT_SECRET"]
                ).encode()
            ).decode()
            outbound = {
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        else:
            if not self._token:
                raise SandboxHeld("OAuth token missing")
            outbound["Authorization"] = f"Bearer {self._token}"
            # PayPal's default minimal responses may omit capture/refund amounts.
            # Record the added header and require PayPal's actual representation.
            outbound = {k: v for k, v in outbound.items() if k.lower() != "prefer"}
            outbound["Prefer"] = "return=representation"
        if create:
            units = json.loads(raw).get("purchase_units") or []
            if len(units) != 1 or amount_minor(units[0].get("amount")) != (2500, "USD"):
                raise ValueError("reference cart must be 2500 minor units USD")
        if refund:
            if amount_minor(json.loads(raw).get("amount")) != self.captures[payment[2]]:
                raise ValueError("refund amount differs from recorded capture")
        if capture and self.scenario == "DECLINE":
            # https://developer.paypal.com/negative-testing/request-headers/
            outbound["PayPal-Mock-Response"] = '{"mock_application_codes":"INSTRUMENT_DECLINED"}'
        self._record(
            "SHOP_TO_PAYPAL", method, path, {**outbound, "Authorization": "[REDACTED]"}, raw
        )
        try:
            response = self.client.request(
                method,
                REST_SANDBOX + path,
                headers=outbound,
                content=raw if method == "POST" else None,
            )
        except httpx.HTTPError:
            if method == "GET":
                raise SandboxReadUnavailable("sandbox status read unavailable") from None
            raise SandboxHeld("sandbox transport failed; outcome unknown; do not retry") from None
        response_headers = {k: v for k, v in response.headers.items() if k.lower() in KEEP_HEADERS}
        try:
            data = response.json()
        except ValueError:
            # An unparseable OAuth response cannot be inspected for token fields.
            recorded = b"[REDACTED]" if oauth else response.content
            self._record(
                "PAYPAL_TO_SHOP", method, path, response_headers, recorded, response.status_code
            )
            raise SandboxHeld("non-JSON PayPal response; stopping") from None
        if oauth and isinstance(data, dict) and data.get("access_token"):
            self._token = data["access_token"]
        self._record(
            "PAYPAL_TO_SHOP", method, path, response_headers, response.content, response.status_code
        )
        if not isinstance(data, dict):
            raise SandboxHeld("PayPal response is not an object")
        if 200 <= response.status_code < 300:
            allowed_http = {200} if oauth or read else {200, 201}
            if response.status_code not in allowed_http:
                raise SandboxHeld(f"unexpected PayPal HTTP {response.status_code}; stopping")
            if oauth and not self._token:
                raise SandboxHeld("PayPal response has no OAuth token")
            if read:
                expected_id = order[1] if order else payment[2]
                if require_id(data, "read resource") != expected_id:
                    raise SandboxHeld("read resource id mismatch; stopping")
                allowed_statuses = (
                    {"CREATED", "PAYER_ACTION_REQUIRED", "SAVED", "APPROVED", "COMPLETED"}
                    if order
                    else {"COMPLETED", "REFUNDED"}
                    if payment[1] == "captures" and self.refunds
                    else {"COMPLETED"}
                )
                if data.get("status") not in allowed_statuses:
                    raise SandboxHeld("unexpected provider read status; stopping")
            if create:
                oid = require_id(data, "order")
                self.orders[oid] = data
                if data.get("status") not in {"CREATED", "PAYER_ACTION_REQUIRED", "APPROVED"}:
                    raise SandboxHeld("unexpected create order status")
            if capture or refund:
                raw_capture = {"exchanges": self.recorder.exchanges}
                resources = recorded_resources(raw_capture)
                for (kind, rid), amount in resources.items():
                    (self.captures if kind == "capture" else self.refunds)[rid] = amount
                if capture and (data.get("id") != order[1] or data.get("status") != "COMPLETED"):
                    raise SandboxHeld("capture order id/status mismatch; stopping")
                if capture and any(amount != (2500, "USD") for amount in self.captures.values()):
                    raise SandboxHeld("capture amount/currency mismatch; stopping")
                rows = (
                    [
                        cap
                        for unit in data.get("purchase_units", [])
                        for cap in unit.get("payments", {}).get("captures", [])
                    ]
                    if capture
                    else [data]
                )
                if any(row.get("status") != "COMPLETED" for row in rows):
                    raise SandboxHeld("unexpected capture/refund status; stopping")
                if capture and self.scenario == "DECLINE":
                    raise SandboxHeld("negative test unexpectedly captured; stopping")
        elif not (
            capture
            and self.scenario == "DECLINE"
            and response.status_code == 422
            and any(d.get("issue") == "INSTRUMENT_DECLINED" for d in data.get("details", []))
        ):
            # Duplicate actions may be refused by PayPal; keep their real error responses.
            issues = {d.get("issue") for d in data.get("details", [])}
            duplicate = response.status_code == 422 and (
                (
                    capture
                    and self.captures
                    and self.scenario == "DOUBLE"
                    and issues == {"ORDER_ALREADY_CAPTURED"}
                )
                or (
                    refund
                    and self.refunds
                    and self.scenario == "REFUND_TWICE"
                    and issues in ({"CAPTURE_FULLY_REFUNDED"}, {"REFUND_AMOUNT_EXCEEDED"})
                )
            )
            if not duplicate:
                raise SandboxHeld(f"PayPal HTTP {response.status_code}; stopping")
        return response.status_code, response_headers, response.content

    def approve(self, token):
        if token not in self.orders:
            raise SandboxHeld("shop returned no recorded PayPal order id")
        link = next(
            (
                r.get("href")
                for r in self.orders[token].get("links", [])
                if r.get("rel") in {"approve", "payer-action"} and r.get("href")
            ),
            None,
        )
        if (
            not link
            or httpx.URL(link).scheme != "https"
            or httpx.URL(link).host
            not in {
                "www.sandbox.paypal.com",
                "sandbox.paypal.com",
            }
        ):
            raise SandboxHeld("PayPal response has no sandbox buyer approval link")
        self.show_approval(link)
        deadline = time.monotonic() + self.approval_timeout_s
        failed_reads = 0
        while True:
            try:
                _, _, raw = self.exchange(
                    "GET", f"/v2/checkout/orders/{token}", {"X-GoldGraft-Ledger": "order"}
                )
            except SandboxReadUnavailable:
                failed_reads += 1
                if failed_reads >= 3 or time.monotonic() >= deadline:
                    raise SandboxHeld(
                        "approval status unavailable after three reads; stopping"
                    ) from None
                time.sleep(min(self.poll_s, max(0, deadline - time.monotonic())))
                continue
            failed_reads = 0
            order = json.loads(raw)
            if require_id(order, "order") != token:
                raise SandboxHeld("approval order id mismatch")
            if order.get("status") == "APPROVED":
                self.approved.add(token)
                return
            if order.get("status") not in {"CREATED", "PAYER_ACTION_REQUIRED", "SAVED"}:
                raise SandboxHeld("unexpected approval order status; nothing captured")
            if time.monotonic() >= deadline:
                raise TimeoutError("order not approved before timeout; nothing captured")
            time.sleep(min(self.poll_s, max(0, deadline - time.monotonic())))

    def close(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
        self.client.close()


def refetch_resources(capture, broker, *, secret_ref, graft_id):
    """Uncached, read-only independent broker GETs; preserve failures per resource."""
    rows = []
    for kind, rid in recorded_resources(capture, strict=False):
        started = time.monotonic()
        row = {"kind": kind, "id": rid}
        try:
            response = getattr(broker, f"refetch_{kind}")(
                rid,
                secret_ref=secret_ref,
                graft_id=graft_id,
            )
            row.update(
                body=response.data,
                status_code=response.status_code,
                evidence_class=response.evidence_class,
                simulated=response.simulated,
                correlation_id=response.correlation_id,
            )
        except Exception as exc:
            # Never store provider/library exception text: it can embed request secrets.
            row["error"] = type(exc).__name__
        row["t_ms"] = int((time.monotonic() - started) * 1000)
        rows.append(row)
    return rows


def require_refetch_results(capture, rows):
    """Stop after failed/unknown reads; a real REFUNDED capture remains a gate hold."""
    resources = recorded_resources(capture)
    fetched = {(r["kind"], r["id"]): r for r in rows}
    if len(fetched) != len(rows) or fetched.keys() != resources.keys():
        raise SandboxHeld("independent re-fetch inventory mismatch; stopping")
    has_refund = any(kind == "refund" for kind, _ in resources)
    for (kind, rid), amount in resources.items():
        row = fetched[kind, rid]
        if (
            row.get("error")
            or row.get("simulated") is not False
            or row.get("evidence_class") != "real_sandbox"
            or row.get("status_code") != 200
        ):
            raise SandboxHeld("independent re-fetch failed; stopping")
        body = row.get("body") or {}
        if body.get("id") != rid:
            raise SandboxHeld("independent re-fetch id mismatch; stopping")
        statuses = {"COMPLETED", "REFUNDED"} if kind == "capture" and has_refund else {"COMPLETED"}
        if body.get("status") not in statuses:
            raise SandboxHeld("unexpected independent re-fetch status; stopping")
        if amount_minor(body.get("amount")) != amount:
            raise SandboxHeld("independent re-fetch amount/currency mismatch; stopping")
