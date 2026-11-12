"""Run the legacy PHP shop for real (original and Grafter code) and record its payments.

The shop runs under PHP's built-in server on this machine. PayPal is a local stand-in that keeps a
ledger (orders, captures, refunds) and answers the classic NVP API, IPN verification and Orders v2
the way the scenario asks (completed, pending, declined, already captured, forged notification).
Every exchange is recorded as RawCapture/1 in the exact shape Singhal's proof mapper reads:
browser → shop, shop → PayPal, PayPal → shop (incl. ledger reads), PayPal notification → shop,
and shop database writes (orders.json diffs, statuses normalised to paid/pending/unpaid).

Honest limits: PayPal is a stand-in, not the PayPal sandbox; the buyer's approval at PayPal is
simulated; no secrets exist (credentials are fixed placeholders and are redacted in recordings).
The shop's own code is not edited: a PHP prepend file defines the PayPal endpoints first.
"""

import json
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from decimal import Decimal
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen

from goldgraft_contracts.registry import validate

ROOT = Path(__file__).resolve().parents[1]
SHOP_SRC = ROOT / "fixtures/shops/legacy-php-shop/src"
CANDIDATE_PATHS = frozenset(
    {
        "api/create-payment.php",
        "api/execute-payment.php",
        "api/refund.php",
        "ipn.php",
        "lib/paypal_orders.php",
    }
)
SCENARIOS = [
    "HAPPY",
    "PENDING",
    "DECLINE",
    "DOUBLE",
    "REFUND",
    "REFUND_TWICE",
    "NOTIFY_DUP",
    "NOTIFY_FORGED",
    "PARITY_EXTRA",
]
SHOP_STATUS = {"CREATED": "unpaid", "PENDING": "pending", "PAID": "paid", "REFUNDED": "paid"}
KEEP_HEADERS = {
    "content-type",
    "paypal-request-id",
    "prefer",
    "paypal-debug-id",
    "paypal-auth-algo",
    "paypal-cert-url",
    "paypal-transmission-id",
    "paypal-transmission-sig",
    "paypal-transmission-time",
}
REDACT = {"authorization"}
NVP_SECRETS = {"USER", "PWD", "SIGNATURE"}


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def minor(value):
    amount = Decimal(value)
    if not amount.is_finite():
        raise ValueError("non-finite amount")
    scaled = Fraction(amount) * 100
    if scaled.denominator != 1:
        raise ValueError("fractional minor units")
    return scaled.numerator


def decode_request(path, content_type, raw):
    """Both OAuth and NVP use forms; Orders/webhook calls use JSON."""
    form = content_type.split(";", 1)[
        0
    ].strip().lower() == "application/x-www-form-urlencoded" or path.endswith(
        ("/nvp", "/cgi-bin/webscr", "/oauth2/token")
    )
    return (dict(parse_qsl(raw)), {}) if form else ({}, json.loads(raw) if raw else {})


def validate_candidate(files):
    if not isinstance(files, dict) or any(
        path not in CANDIDATE_PATHS or not isinstance(text, str) for path, text in files.items()
    ):
        raise ValueError("unsupported candidate path or content")


def resolve_php(php):
    found = shutil.which(php)
    if found is None:
        raise ValueError("PHP executable unavailable")
    return Path(found).resolve()


def order_listing(capture):
    """One actual non-payment API observation; ignore provider ids/timestamps only."""
    observations = [
        exchange
        for exchange in capture.exchanges
        if (
            exchange.direction == "BROWSER_TO_SHOP"
            and exchange.method == "GET"
            and urlsplit(exchange.url).path == "/api/orders.php"
        )
    ]
    if len(observations) != 1 or observations[0].status != 200:
        raise ValueError("missing or failed order listing")
    body = observations[0].body_json
    if not isinstance(body, list) or not body:
        raise ValueError("incomplete order listing")
    rows = []
    for order in body:
        if not isinstance(order, dict) or order.get("status") not in SHOP_STATUS:
            raise ValueError("invalid order listing")
        rows.append((minor(order["amount"]), order["status"]))
    return sorted(rows)


class Recorder:
    """Collects one scenario run's exchanges in order, tagged with the order reference."""

    def __init__(self, ref):
        self.ref, self.exchanges, self.lock, self.t0 = ref, [], threading.Lock(), time.monotonic()

    def add(self, direction, method, url, headers=None, *, status=None, extra=None, **body):
        kept = {}
        for name, value in (headers or {}).items():
            low = name.lower()
            if low in REDACT:
                kept[name] = "[REDACTED]"
            elif low in KEEP_HEADERS or low.startswith("x-goldgraft-"):
                kept[name] = value
        kept["X-GoldGraft-Order-Ref"] = self.ref
        kept.update(extra or {})
        with self.lock:
            item = {
                "seq": len(self.exchanges),
                "t_ms": int((time.monotonic() - self.t0) * 1000),
                "direction": direction,
                "method": method,
                "url": url,
                "headers": kept,
                **body,
            }
            if status is not None:
                item["status"] = status
            self.exchanges.append(item)


def _nvp_text(fields):
    return urlencode({k: ("[REDACTED]" if k in NVP_SECRETS else v) for k, v in fields.items()})


class PayPalStandIn:
    """Local PayPal with a ledger; behaviour per scenario. Records every shop ↔ PayPal exchange."""

    def __init__(self, scenario):
        self.scenario, self.recorder = scenario, None
        self.orders, self.tokens, self.captures, self.refunds = {}, {}, {}, {}
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        stand_in = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _reply(self, status, body, *, text=False, extra=None):
                payload = body if text else json.dumps(body)
                kind = "application/x-www-form-urlencoded" if text else "application/json"
                debug = {"PayPal-Debug-Id": "standin" + uuid.uuid4().hex[:7]}
                url = stand_in.base + self.path
                headers = {"Content-Type": kind, **({} if text else debug)}
                if stand_in.recorder and not self.path.startswith("/v1/oauth2"):
                    rec = {"body_text": payload} if text else {"body_json": body}
                    if self.path.endswith("/nvp"):
                        rec = {"body_text": payload}
                    stand_in.recorder.add(
                        "PAYPAL_TO_SHOP",
                        self.command,
                        url,
                        {**headers, **dict(self._ledger)},
                        status=status,
                        extra=extra,
                        **rec,
                    )
                self.send_response(status)
                self.send_header("Content-Type", kind)
                for k, v in debug.items():
                    self.send_header(k, v)
                data = payload.encode()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _handle(self):
                size = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(size).decode() if size else ""
                path = urlsplit(self.path).path
                ledger = self.headers.get("X-GoldGraft-Ledger")
                self._ledger = {"X-GoldGraft-Ledger": ledger} if ledger else {}
                url = stand_in.base + self.path
                fields, body = decode_request(path, self.headers.get("Content-Type", ""), raw)
                form = bool(fields) or path.endswith(("/nvp", "/cgi-bin/webscr"))
                parent = stand_in.parent_of(path, fields if ledger == "refund" else None)
                extra = {"X-GoldGraft-Parent-Capture": parent} if parent else None
                if stand_in.recorder and not path.startswith("/v1/oauth2"):
                    req = (
                        {"body_text": _nvp_text(fields) if path.endswith("/nvp") else raw}
                        if form
                        else {"body_json": body}
                    )
                    stand_in.recorder.add(
                        "SHOP_TO_PAYPAL", self.command, url, dict(self.headers), extra=extra, **req
                    )
                status, answer, text = stand_in.answer(self.command, path, fields, body)
                self._reply(status, answer, text=text, extra=extra)

            do_GET = do_POST = _handle

        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    # ── ledger behaviour ─────────────────────────────────────────────────────────────────
    def parent_of(self, path, nvp_fields=None):
        if nvp_fields is not None:
            return self.refunds.get(nvp_fields.get("TRANSACTIONID", ""), {}).get("capture")
        if path.startswith("/v2/payments/captures/") and path.endswith("/refund"):
            return path.split("/")[4]
        if path.startswith("/v2/payments/refunds/"):
            return self.refunds.get(path.split("/")[4], {}).get("capture")
        return None

    def approve(self, token):
        if token in self.orders:
            self.orders[token]["status"] = "APPROVED"
        if token in self.tokens:
            self.tokens[token]["approved"] = True

    def answer(self, method, path, fields, body):
        s = self.scenario
        if path.endswith("/nvp"):
            return 200, urlencode(self.nvp(fields)), True
        if path.endswith("/cgi-bin/webscr"):
            txn = fields.get("txn_id")
            ok = s != "NOTIFY_FORGED" and txn in self.captures
            return 200, "VERIFIED" if ok else "INVALID", True
        if path == "/v1/oauth2/token":
            return (
                200,
                {"access_token": "standin", "token_type": "Bearer", "expires_in": 3600},
                False,
            )
        if path == "/v1/notifications/verify-webhook-signature":
            event = body.get("webhook_event") or {}
            known = (event.get("resource") or {}).get("id") in self.captures
            ok = s != "NOTIFY_FORGED" and known
            return 200, {"verification_status": "SUCCESS" if ok else "FAILURE"}, False
        if path == "/v2/checkout/orders" and method == "POST":
            unit = body["purchase_units"][0]
            oid = uuid.uuid4().hex[:17].upper()
            self.orders[oid] = {
                "id": oid,
                "intent": "CAPTURE",
                "status": "CREATED",
                "purchase_units": [
                    {"reference_id": unit.get("reference_id", "default"), "amount": unit["amount"]}
                ],
            }
            return 201, self.orders[oid], False
        if path.startswith("/v2/checkout/orders/"):
            parts = path.split("/")
            order = self.orders.get(parts[4])
            if order is None:
                return 404, {"name": "RESOURCE_NOT_FOUND"}, False
            if method == "GET":
                return 200, order, False
            if parts[-1] == "capture":
                return self.capture_v2(order)
        if path.startswith("/v2/payments/captures/"):
            parts = path.split("/")
            cap = self.captures.get(parts[4])
            if cap is None:
                return 404, {"name": "RESOURCE_NOT_FOUND"}, False
            if method == "GET":
                return 200, cap["v2"], False
            if parts[-1] == "refund":
                return self.refund_v2(cap)
        if path.startswith("/v2/payments/refunds/"):
            ref = self.refunds.get(path.split("/")[4])
            return (200, ref["v2"], False) if ref else (404, {"name": "RESOURCE_NOT_FOUND"}, False)
        return 404, {"name": "NOT_FOUND"}, False

    def _new_capture(self, amount, currency, order_id=None, token=None):
        cid = uuid.uuid4().hex[:17].upper()
        status = "PENDING" if self.scenario == "PENDING" else "COMPLETED"
        self.captures[cid] = {
            "status": status,
            "amount": amount,
            "currency": currency,
            "refunded": False,
            "token": token,
            "v2": {
                "id": cid,
                "status": status,
                "amount": {"currency_code": currency, "value": amount},
                "final_capture": True,
                "supplementary_data": {"related_ids": {"order_id": order_id or token}},
            },
        }
        return cid, status

    def capture_v2(self, order):
        if self.scenario == "DECLINE":
            return (
                422,
                {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "INSTRUMENT_DECLINED"}]},
                False,
            )
        if order["status"] == "COMPLETED":
            return (
                422,
                {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "ORDER_ALREADY_CAPTURED"}]},
                False,
            )
        if order["status"] != "APPROVED":
            return (
                422,
                {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "ORDER_NOT_APPROVED"}]},
                False,
            )
        amount = order["purchase_units"][0]["amount"]
        cid, status = self._new_capture(amount["value"], amount["currency_code"], order["id"])
        order["status"] = "COMPLETED"
        order["purchase_units"][0]["payments"] = {"captures": [self.captures[cid]["v2"]]}
        order["payer"] = {"payer_id": "FAKEPAYER0001", "email_address": "buyer@example.invalid"}
        return 201, order, False

    def refund_v2(self, cap):
        if cap["refunded"] or cap["status"] != "COMPLETED":
            return (
                422,
                {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "CAPTURE_FULLY_REFUNDED"}]},
                False,
            )
        cap["refunded"] = True
        rid = uuid.uuid4().hex[:17].upper()
        refund = {
            "id": rid,
            "status": "COMPLETED",
            "amount": {"currency_code": cap["currency"], "value": cap["amount"]},
        }
        self.refunds[rid] = {"capture": cap["v2"]["id"], "v2": refund}
        return 201, refund, False

    def nvp(self, f):
        op, ok = (
            f.get("METHOD"),
            {"ACK": "Success", "VERSION": "204.0", "CORRELATIONID": uuid.uuid4().hex[:13]},
        )

        def fail(code, msg):
            return {
                **ok,
                "ACK": "Failure",
                "L_ERRORCODE0": code,
                "L_LONGMESSAGE0": msg,
            }

        if op == "SetExpressCheckout":
            token = "EC-" + uuid.uuid4().hex[:17].upper()
            self.tokens[token] = {
                "amount": f.get("PAYMENTREQUEST_0_AMT"),
                "approved": False,
                "currency": f.get("PAYMENTREQUEST_0_CURRENCYCODE", "USD"),
                "txn": None,
            }
            return {**ok, "TOKEN": token}
        t = self.tokens.get(f.get("TOKEN", ""))
        if op == "GetExpressCheckoutDetails":
            if not t:
                return fail("10410", "Invalid token")
            return {
                **ok,
                "TOKEN": f["TOKEN"],
                "PAYERID": "FAKEPAYER0001",
                "EMAIL": "buyer@example.invalid",
                "PAYMENTREQUEST_0_AMT": t["amount"],
                "PAYMENTREQUEST_0_CURRENCYCODE": t["currency"],
            }
        if op == "DoExpressCheckoutPayment":
            if not t or not t["approved"]:
                return fail("10410", "Invalid token")
            if self.scenario == "DECLINE":
                return fail("10486", "This transaction couldn't be completed")
            if t["txn"]:
                return fail("10415", "Transaction already completed for this token")
            cid, status = self._new_capture(t["amount"], t["currency"], token=f["TOKEN"])
            t["txn"] = cid
            return {
                **ok,
                "TOKEN": f["TOKEN"],
                "PAYMENTINFO_0_TRANSACTIONID": cid,
                "PAYMENTINFO_0_AMT": t["amount"],
                "PAYMENTINFO_0_CURRENCYCODE": t["currency"],
                "PAYMENTINFO_0_PAYMENTSTATUS": status.capitalize(),
                **({"PAYMENTINFO_0_PENDINGREASON": "paymentreview"} if status == "PENDING" else {}),
            }
        if op == "RefundTransaction":
            cap = self.captures.get(f.get("TRANSACTIONID", ""))
            if not cap or cap["refunded"] or cap["status"] != "COMPLETED":
                return fail("10009", "Transaction refused")
            cap["refunded"] = True
            rid = uuid.uuid4().hex[:17].upper()
            self.refunds[rid] = {"capture": f["TRANSACTIONID"], "v2": None}
            return {
                **ok,
                "REFUNDTRANSACTIONID": rid,
                "GROSSREFUNDAMT": cap["amount"],
                "CURRENCYCODE": cap["currency"],
                "REFUNDSTATUS": "instant",
            }
        if op == "GetTransactionDetails":
            tid = f.get("TRANSACTIONID", "")
            if tid in self.captures:
                cap = self.captures[tid]
                return {
                    **ok,
                    "TRANSACTIONID": tid,
                    "AMT": cap["amount"],
                    "CURRENCYCODE": cap["currency"],
                    "PAYMENTSTATUS": cap["status"].capitalize(),
                }
            if tid in self.refunds:
                cap = self.captures[self.refunds[tid]["capture"]]
                return {
                    **ok,
                    "TRANSACTIONID": tid,
                    "AMT": "-" + cap["amount"],
                    "CURRENCYCODE": cap["currency"],
                    "PAYMENTSTATUS": "Refunded",
                }
            return fail("10004", "Transaction id is not valid")
        return fail("81002", "Unspecified method")


class Shop:
    """One shop tree served by `php -S`, with PayPal endpoints pointed at the stand-in."""

    def __init__(self, files, paypal, php="php"):
        validate_candidate(files)
        php = str(resolve_php(php))
        self.dir = Path(tempfile.mkdtemp(prefix="gg-shop-"))
        shutil.copytree(SHOP_SRC, self.dir, dirs_exist_ok=True)
        for rel, text in files.items():
            target = self.dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        (self.dir / "data").mkdir(exist_ok=True)
        prepend = self.dir / ".goldgraft_prepend.php"
        prepend.write_text(
            "<?php\n// Test harness only: the shop's PayPal endpoints go to the stand-in.\n"
            f"define('PAYPAL_NVP_ENDPOINT', '{paypal.base}/nvp');\n"
            f"define('PAYPAL_IPN_VERIFY_URL', '{paypal.base}/cgi-bin/webscr');\n"
            f"define('PAYPAL_REST_BASE', '{paypal.base}');\n"
        )
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
            "SHOP_BASE_URL": self.base,
            "PAYPAL_CLIENT_ID": "standin-client",
            "PAYPAL_CLIENT_SECRET": "standin-placeholder",
            "PAYPAL_WEBHOOK_ID": "WH-STANDIN",
        }
        self.proc = subprocess.Popen(
            [
                php,
                "-S",
                f"127.0.0.1:{self.port}",
                "-t",
                str(self.dir),
                "-d",
                f"auto_prepend_file={prepend}",
                "-d",
                "display_errors=0",
                "-d",
                "log_errors=0",
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("php built-in server did not start")

    def orders(self):
        path = self.dir / "data/orders.json"
        return json.loads(path.read_text() or "{}") if path.exists() else {}

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        finally:
            shutil.rmtree(self.dir, ignore_errors=True)


def _norm(order):
    if order is None:
        return {"status": "unpaid", "total_minor": 0, "currency": "USD", "refunded_minor": 0}
    total = minor(order.get("amount", "0"))
    return {
        "status": SHOP_STATUS.get(order.get("status"), "unpaid"),
        "total_minor": total,
        "currency": "USD",
        "refunded_minor": total if order.get("status") == "REFUNDED" else 0,
    }


def run_scenario(scenario, variant, files, *, graft_id, run_id, php="php"):
    """Drive one scenario through one shop tree; return a validated RawCapture/1 dict."""
    if scenario not in SCENARIOS or variant not in {"OLD", "OLD_TWIN", "NEW"}:
        raise ValueError("unsupported local scenario or variant")
    validate_candidate(files)
    php = str(resolve_php(php))
    ref = f"SHOP-{scenario}"
    paypal = PayPalStandIn(scenario)
    rec = Recorder(ref)
    paypal.recorder = rec
    try:
        shop = Shop(files, paypal, php=php)
    except BaseException:
        paypal.close()
        raise
    seen = {}

    def db_diff():
        for token, order in shop.orders().items():
            before, after = seen.get(token), _norm(order)
            if (before or _norm(None)) != after:
                rec.add(
                    "SHOP_DB_WRITE",
                    "UPDATE",
                    "db://legacy-php-shop/orders",
                    {},
                    db_change={
                        "table": "orders",
                        "key": {"order_ref": ref},
                        "before": before or _norm(None),
                        "after": after,
                    },
                )
            seen[token] = after

    def call(direction, path, body, *, form=False, headers=None):
        url = shop.base + path
        data = urlencode(body).encode() if form else json.dumps(body).encode()
        kind = "application/x-www-form-urlencoded" if form else "application/json"
        rec.add(
            direction,
            "POST",
            url,
            {"Content-Type": kind, **(headers or {})},
            **({"body_text": data.decode()} if form else {"body_json": body}),
        )
        req = Request(url, data=data, headers={"Content-Type": kind, **(headers or {})})
        try:
            with urlopen(req, timeout=20) as r:
                out = r.read().decode()
        except HTTPError as e:
            out = e.read().decode()
        db_diff()
        try:
            return json.loads(out)
        except ValueError:
            return {}

    def notify(token, *, forged=False):
        cap_id = next(
            (
                c
                for c, v in paypal.captures.items()
                if v["token"] == token
                or v["v2"]["supplementary_data"]["related_ids"]["order_id"] == token
            ),
            None,
        )
        if forged:
            cap_id = cap_id or uuid.uuid4().hex[:17].upper()
        if cap_id is None:
            return
        cap = paypal.captures.get(cap_id) or {
            "amount": "25.00",
            "currency": "USD",
            "status": "COMPLETED",
        }
        if variant == "NEW":
            event = {
                "id": "WH-" + uuid.uuid4().hex[:12].upper(),
                "event_type": f"PAYMENT.CAPTURE.{cap['status']}",
                "resource_type": "capture",
                "resource": {
                    "id": cap_id,
                    "status": cap["status"],
                    "amount": {"currency_code": cap["currency"], "value": cap["amount"]},
                    "supplementary_data": {"related_ids": {"order_id": token}},
                },
            }
            hdr = {
                "PAYPAL-AUTH-ALGO": "SHA256withRSA",
                "PAYPAL-CERT-URL": paypal.base + "/v1/notifications/certs/STANDIN",
                "PAYPAL-TRANSMISSION-ID": "T-" + uuid.uuid4().hex[:10],
                "PAYPAL-TRANSMISSION-SIG": "standin-signature",
                "PAYPAL-TRANSMISSION-TIME": "2026-11-12T00:00:00Z",
            }
            call("PAYPAL_NOTIFY_TO_SHOP", "/ipn.php", event, headers=hdr)
        else:
            call(
                "PAYPAL_NOTIFY_TO_SHOP",
                "/ipn.php",
                {
                    "txn_type": "express_checkout",
                    "payment_status": cap["status"].capitalize(),
                    "mc_gross": cap["amount"],
                    "mc_currency": cap["currency"],
                    "txn_id": cap_id,
                    "invoice": ref,
                    "receiver_email": "sb-business@business.example.com",
                },
                form=True,
            )

    try:
        created = call(
            "BROWSER_TO_SHOP", "/api/create-payment.php", {"tee": 1, "minor": 1, "currency": "EUR"}
        )
        token = created.get("token")
        if token and scenario != "NOTIFY_FORGED":
            paypal.approve(token)
            pay = {"token": token, "payerID": "FAKEPAYER0001", "orderId": token}
            call("BROWSER_TO_SHOP", "/api/execute-payment.php", pay)
            if scenario == "DOUBLE":
                call("BROWSER_TO_SHOP", "/api/execute-payment.php", pay)
            if scenario not in {"PENDING", "DECLINE"}:
                notify(token)
                if scenario == "NOTIFY_DUP":
                    notify(token)
            if scenario in {"REFUND", "REFUND_TWICE"}:
                call("BROWSER_TO_SHOP", "/api/refund.php", {"token": token})
                if scenario == "REFUND_TWICE":
                    call("BROWSER_TO_SHOP", "/api/refund.php", {"token": token})
        elif token:
            notify(token, forged=True)
        if scenario == "PARITY_EXTRA":
            # Observe an unchanged non-payment feature, instead of repeating HAPPY.
            url = shop.base + "/api/orders.php"
            with urlopen(url, timeout=10) as response:
                body = json.loads(response.read())
                rec.add(
                    "BROWSER_TO_SHOP",
                    "GET",
                    url,
                    dict(response.headers),
                    status=response.status,
                    body_json=body,
                )
        ledger_reads(paypal, rec, token, variant)
    finally:
        shop.close()
        paypal.close()
    capture = {
        "graft_id": graft_id,
        "run_id": run_id,
        "variant": variant,
        "scenario_id": scenario,
        "exchanges": rec.exchanges,
    }
    validate("RawCapture/1", capture)
    return capture


def ledger_reads(paypal, rec, token, variant):
    """After the run, read PayPal's own records (the proof's independent witness)."""

    def read(method, path, ledger, *, nvp=None):
        url = paypal.base + path
        headers = {"X-GoldGraft-Ledger": ledger}
        if nvp is not None:
            data = urlencode(
                {
                    "USER": "standin",
                    "PWD": "standin",
                    "SIGNATURE": "standin",
                    "VERSION": "204.0",
                    **nvp,
                }
            ).encode()
            req = Request(
                url,
                data=data,
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
        else:
            req = Request(
                url, method=method, headers={**headers, "Content-Type": "application/json"}
            )
        try:
            with urlopen(req, timeout=10) as r:
                r.read()
        except HTTPError:
            pass

    caps = [
        c
        for c, v in paypal.captures.items()
        if v["token"] == token or v["v2"]["supplementary_data"]["related_ids"]["order_id"] == token
    ]
    refunds = [r for r, v in paypal.refunds.items() if v["capture"] in caps]
    if variant == "NEW":
        if token in paypal.orders:
            read("GET", f"/v2/checkout/orders/{token}", "order")
        for c in caps:
            read("GET", f"/v2/payments/captures/{c}", "capture")
        for r in refunds:
            read("GET", f"/v2/payments/refunds/{r}", "refund")
    else:
        for c in caps:
            read(
                "POST",
                "/nvp",
                "capture",
                nvp={"METHOD": "GetTransactionDetails", "TRANSACTIONID": c},
            )
        for r in refunds:
            read(
                "POST",
                "/nvp",
                "refund",
                nvp={"METHOD": "GetTransactionDetails", "TRANSACTIONID": r},
            )
