"""FAKE PayPal sandbox at HTTP level, so the backend and shop owners can work offline.

It imitates the shapes in PayPal's public docs; it is NOT PayPal. Real behaviour must
still be confirmed in the sandbox (the 16 Step-6 tests in docs/design/09).
Docs used (URLs marked "verify" were not re-opened during this build):
- NVP Express Checkout: https://developer.paypal.com/api/nvp-soap/ (verify)
- IPN postback: https://developer.paypal.com/api/nvp-soap/ipn/IPNImplementation/ (verify)
- Orders v2: https://developer.paypal.com/docs/api/orders/v2/
- Payments v2 (refund): https://developer.paypal.com/docs/api/payments/v2/
- Webhook verify: https://developer.paypal.com/docs/api/webhooks/v1/ (verify)
- Mock responses (PayPal-Mock-Response header):
  https://developer.paypal.com/tools/sandbox/negative-testing/request-headers/ (verify)
- Rate limit (>50 req/min per IP -> blocked 5 min), EVIDENCE E113:
  https://www.paypal.com/us/cshelp/article/why-did-i-get-http-error-code-429-ts2115
Fake-only extras (not PayPal): POST /fake/approve/{order_id} (buyer approves),
NVP field X_FAKE_PAYMENTSTATUS=Pending, mock code FAKE_CAPTURE_PENDING, and the
helpers ipn_for() / webhook_for() that produce the notification a shop would receive.
"""

import hashlib
import itertools
import json
import time
from collections import defaultdict, deque
from urllib.parse import parse_qsl, urlencode

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

RATE_LIMIT = 50          # requests per minute per client IP (PayPal sandbox)
BLOCK_SECONDS = 300      # 5-minute block
NVP_VERSION = "204.0"


def _minor(value: str, currency: str) -> int:
    digits = 0 if currency in {"JPY", "HUF", "TWD"} else 2
    whole, _, frac = value.partition(".")
    return int(whole) * 10**digits + (int((frac + "00")[:digits]) if digits else 0)


def _value(minor: int, currency: str) -> str:
    if currency in {"JPY", "HUF", "TWD"}:
        return str(minor)
    return f"{minor // 100}.{minor % 100:02d}"


class FakePayPal:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.ids = itertools.count(1)
        self.hits: dict[str, deque] = defaultdict(deque)
        self.blocked_until: dict[str, float] = {}
        self.ec_tokens: dict[str, dict] = {}
        self.nvp_txns: dict[str, dict] = {}
        self.orders: dict[str, dict] = {}
        self.captures: dict[str, dict] = {}
        self.request_ids: dict[str, tuple[int, dict]] = {}
        self.webhook_sigs: dict[str, str] = {}
        self.app = self._build()

    # ------------------------------------------------------------ helpers
    def _id(self, prefix: str, size: int = 17) -> str:
        n = next(self.ids)
        return (prefix + hashlib.sha256(f"{prefix}{n}".encode()).hexdigest().upper())[:size]

    def _rate_limited(self, ip: str) -> bool:
        now = self.clock()
        if self.blocked_until.get(ip, 0) > now:
            return True
        window = self.hits[ip]
        while window and window[0] <= now - 60:
            window.popleft()
        window.append(now)
        if len(window) > RATE_LIMIT:
            self.blocked_until[ip] = now + BLOCK_SECONDS
            window.clear()
            return True
        return False

    @staticmethod
    def _rest_error(status: int, name: str, issue: str, description: str) -> JSONResponse:
        return JSONResponse(status_code=status, content={
            "name": name, "message": description, "debug_id": "fake" + issue[:8].lower(),
            "details": [{"issue": issue, "description": description}]})

    @staticmethod
    def _nvp(fields: dict) -> PlainTextResponse:
        base = {"TIMESTAMP": "2026-11-02T10:00:00Z", "CORRELATIONID": "fakecorr",
                "VERSION": NVP_VERSION, "BUILD": "000000"}
        return PlainTextResponse(urlencode({**fields, **base}))

    @staticmethod
    def _nvp_error(code: str, message: str) -> PlainTextResponse:
        return FakePayPal._nvp({"ACK": "Failure", "L_ERRORCODE0": code,
                                "L_SHORTMESSAGE0": "Transaction refused",
                                "L_LONGMESSAGE0": message, "L_SEVERITYCODE0": "Error"})

    # ------------------------------------------------------------ notifications
    def ipn_for(self, txn_id: str) -> dict:
        """The IPN form a shop would receive for an NVP transaction."""
        t = self.nvp_txns[txn_id]
        return {"txn_id": txn_id, "txn_type": "express_checkout",
                "payment_status": t["status"], "mc_gross": _value(t["minor"], t["currency"]),
                "mc_currency": t["currency"], "invoice": t.get("invoice", ""),
                "receiver_email": "merchant@example.test"}

    def webhook_for(self, capture_id: str) -> tuple[dict, dict]:
        """(headers, body) of PAYMENT.CAPTURE.COMPLETED the shop would receive."""
        cap = self.captures[capture_id]
        transmission = self._id("WH-")
        sig = hashlib.sha256(f"{transmission}{capture_id}".encode()).hexdigest()
        self.webhook_sigs[transmission] = sig
        body = {"id": self._id("WH-EV-"), "event_type": "PAYMENT.CAPTURE.COMPLETED",
                "resource_type": "capture", "resource": {
                    "id": capture_id, "status": cap["status"], "amount": cap["amount"],
                    "supplementary_data": {"related_ids": {"order_id": cap["order_id"]}}}}
        headers = {"PAYPAL-TRANSMISSION-ID": transmission,
                   "PAYPAL-TRANSMISSION-TIME": "2026-11-02T10:00:00Z",
                   "PAYPAL-TRANSMISSION-SIG": sig, "PAYPAL-AUTH-ALGO": "SHA256withRSA",
                   "PAYPAL-CERT-URL": "https://api.sandbox.paypal.com/v1/notifications/certs/FAKE"}
        return headers, body

    # ------------------------------------------------------------ app
    def _build(self) -> FastAPI:
        app = FastAPI(title="FAKE PayPal sandbox (GoldGraft stand-in — not PayPal)")

        @app.middleware("http")
        async def limit(request: Request, call_next):
            ip = request.client.host if request.client else "unknown"
            if self._rate_limited(ip):
                return self._rest_error(429, "RATE_LIMIT_REACHED", "RATE_LIMIT_REACHED",
                                        "Too many requests. Blocked due to rate limiting.")
            return await call_next(request)

        @app.post("/nvp")
        async def nvp(request: Request):
            form = dict(parse_qsl((await request.body()).decode(), keep_blank_values=True))
            return self._handle_nvp(form)

        @app.post("/cgi-bin/webscr")
        async def ipn_postback(request: Request):
            form = dict(parse_qsl((await request.body()).decode(), keep_blank_values=True))
            if form.pop("cmd", None) != "_notify-validate":
                return PlainTextResponse("INVALID")
            txn = form.get("txn_id")
            if txn in self.nvp_txns and form == self.ipn_for(txn):
                return PlainTextResponse("VERIFIED")
            return PlainTextResponse("INVALID")

        @app.post("/v1/oauth2/token")
        async def token(request: Request):
            if not request.headers.get("authorization", "").startswith("Basic "):
                return self._rest_error(401, "invalid_client", "INVALID_CLIENT",
                                        "Client Authentication failed")
            return {"scope": "https://uri.paypal.com/services/payments/payment",
                    "access_token": "FAKE-ACCESS-TOKEN", "token_type": "Bearer",
                    "app_id": "APP-FAKE", "expires_in": 32400, "nonce": "fake"}

        @app.post("/v2/checkout/orders")
        async def create_order(request: Request):
            body = await request.json()
            req_id = request.headers.get("PayPal-Request-Id")
            if req_id and req_id in self.request_ids:
                status, payload = self.request_ids[req_id]
                return JSONResponse(payload, status_code=status)
            unit = body["purchase_units"][0]
            oid = self._id("5O")
            order = {"id": oid, "intent": body.get("intent", "CAPTURE"), "status": "CREATED",
                     "purchase_units": [{"reference_id": unit.get("reference_id", "default"),
                                         "amount": unit["amount"]}],
                     "links": [{"href": f"https://www.sandbox.paypal.com/checkoutnow?token={oid}",
                                "rel": "approve", "method": "GET"}]}
            self.orders[oid] = order
            if req_id:
                self.request_ids[req_id] = (201, order)
            return JSONResponse(order, status_code=201)

        @app.get("/v2/checkout/orders/{oid}")
        async def get_order(oid: str):
            if oid not in self.orders:
                return self._rest_error(404, "RESOURCE_NOT_FOUND", "INVALID_RESOURCE_ID",
                                        "Specified resource ID does not exist.")
            return self.orders[oid]

        @app.post("/fake/approve/{oid}")
        async def approve(oid: str):
            self.orders[oid]["status"] = "APPROVED"
            return {"id": oid, "status": "APPROVED", "_fake": True}

        @app.post("/v2/checkout/orders/{oid}/capture")
        async def capture(oid: str, request: Request):
            order = self.orders.get(oid)
            if order is None:
                return self._rest_error(404, "RESOURCE_NOT_FOUND", "INVALID_RESOURCE_ID",
                                        "Specified resource ID does not exist.")
            mock = request.headers.get("PayPal-Mock-Response")
            code = json.loads(mock).get("mock_application_codes") if mock else None
            if code in {"INSTRUMENT_DECLINED", "PAYER_ACTION_REQUIRED"}:
                return self._rest_error(422, "UNPROCESSABLE_ENTITY", code, f"mocked {code}")
            if order["status"] == "COMPLETED":
                return self._rest_error(422, "UNPROCESSABLE_ENTITY", "ORDER_ALREADY_CAPTURED",
                                        "Order already captured.")
            if order["status"] != "APPROVED":
                return self._rest_error(422, "UNPROCESSABLE_ENTITY", "ORDER_NOT_APPROVED",
                                        "Payer has not yet approved the Order for payment.")
            cid = self._id("3C")
            status = "PENDING" if code == "FAKE_CAPTURE_PENDING" else "COMPLETED"
            amount = order["purchase_units"][0]["amount"]
            cap = {"id": cid, "status": status, "amount": amount, "final_capture": True,
                   "order_id": oid, "refunded_minor": 0}
            if status == "PENDING":
                cap["status_details"] = {"reason": "PENDING_REVIEW"}
            self.captures[cid] = cap
            order["status"] = "COMPLETED"
            public = {k: v for k, v in cap.items() if k not in {"order_id", "refunded_minor"}}
            order["purchase_units"][0]["payments"] = {"captures": [public]}
            return JSONResponse(order, status_code=201)

        @app.post("/v2/payments/captures/{cid}/refund")
        async def refund(cid: str, request: Request):
            cap = self.captures.get(cid)
            if cap is None:
                return self._rest_error(404, "RESOURCE_NOT_FOUND", "INVALID_RESOURCE_ID",
                                        "Specified resource ID does not exist.")
            raw = await request.body()
            body = json.loads(raw) if raw else {}
            cur = cap["amount"]["currency_code"]
            total = _minor(cap["amount"]["value"], cur)
            want = _minor(body["amount"]["value"], cur) if "amount" in body else (
                total - cap["refunded_minor"])
            if cap["refunded_minor"] >= total:
                return self._rest_error(422, "UNPROCESSABLE_ENTITY", "CAPTURE_FULLY_REFUNDED",
                                        "The capture has already been fully refunded.")
            if cap["refunded_minor"] + want > total:
                return self._rest_error(422, "UNPROCESSABLE_ENTITY", "REFUND_AMOUNT_EXCEEDED",
                                        "The refund amount must be less than or equal to "
                                        "the capture amount that has not yet been refunded.")
            cap["refunded_minor"] += want
            return JSONResponse({"id": self._id("1R"), "status": "COMPLETED",
                                 "amount": {"currency_code": cur, "value": _value(want, cur)}},
                                status_code=201)

        @app.post("/v1/notifications/verify-webhook-signature")
        async def verify(request: Request):
            body = await request.json()
            ok = self.webhook_sigs.get(body.get("transmission_id")) == body.get(
                "transmission_sig")
            return {"verification_status": "SUCCESS" if ok else "FAILURE"}

        return app

    # ------------------------------------------------------------ NVP
    def _handle_nvp(self, f: dict) -> PlainTextResponse:
        method = f.get("METHOD")
        if method == "SetExpressCheckout":
            token = "EC-" + self._id("", 17)
            cur = f.get("PAYMENTREQUEST_0_CURRENCYCODE", "USD")
            self.ec_tokens[token] = {"minor": _minor(f["PAYMENTREQUEST_0_AMT"], cur),
                                     "currency": cur, "paid": False,
                                     "invoice": f.get("PAYMENTREQUEST_0_INVNUM", "")}
            return self._nvp({"ACK": "Success", "TOKEN": token})
        if method == "GetExpressCheckoutDetails":
            t = self.ec_tokens.get(f.get("TOKEN"))
            if t is None:
                return self._nvp_error("10410", "Invalid token.")
            return self._nvp({"ACK": "Success", "TOKEN": f["TOKEN"], "PAYERID": "FAKEPAYER01",
                              "CHECKOUTSTATUS": "PaymentActionCompleted" if t["paid"]
                              else "PaymentActionNotInitiated",
                              "PAYMENTREQUEST_0_AMT": _value(t["minor"], t["currency"]),
                              "PAYMENTREQUEST_0_CURRENCYCODE": t["currency"]})
        if method == "DoExpressCheckoutPayment":
            t = self.ec_tokens.get(f.get("TOKEN"))
            if t is None:
                return self._nvp_error("10410", "Invalid token.")
            if t["paid"]:
                return self._nvp_error("10415", "A successful transaction has already been "
                                       "completed for this token.")
            t["paid"] = True
            txn = self._id("", 17)
            status = f.get("X_FAKE_PAYMENTSTATUS", "Completed")
            self.nvp_txns[txn] = {"minor": t["minor"], "currency": t["currency"],
                                  "status": status, "refunded_minor": 0,
                                  "invoice": t["invoice"]}
            return self._nvp({"ACK": "Success", "TOKEN": f["TOKEN"],
                              "PAYMENTINFO_0_TRANSACTIONID": txn,
                              "PAYMENTINFO_0_PAYMENTSTATUS": status,
                              "PAYMENTINFO_0_AMT": _value(t["minor"], t["currency"]),
                              "PAYMENTINFO_0_CURRENCYCODE": t["currency"],
                              "PAYMENTINFO_0_ACK": "Success"})
        if method == "RefundTransaction":
            t = self.nvp_txns.get(f.get("TRANSACTIONID"))
            if t is None:
                return self._nvp_error("10004", "Transaction id is invalid.")
            if t["refunded_minor"] >= t["minor"]:
                return self._nvp_error("10009", "This transaction has already been fully "
                                       "refunded")
            amount = t["minor"] - t["refunded_minor"] if f.get("REFUNDTYPE", "Full") == "Full" \
                else _minor(f["AMT"], t["currency"])
            t["refunded_minor"] += amount
            return self._nvp({"ACK": "Success", "REFUNDTRANSACTIONID": self._id("", 17),
                              "GROSSREFUNDAMT": _value(amount, t["currency"]),
                              "CURRENCYCODE": t["currency"]})
        if method == "GetTransactionDetails":
            t = self.nvp_txns.get(f.get("TRANSACTIONID"))
            if t is None:
                return self._nvp_error("10004", "Transaction id is invalid.")
            status = "Refunded" if t["refunded_minor"] >= t["minor"] else t["status"]
            return self._nvp({"ACK": "Success", "TRANSACTIONID": f["TRANSACTIONID"],
                              "PAYMENTSTATUS": status, "AMT": _value(t["minor"], t["currency"]),
                              "CURRENCYCODE": t["currency"]})
        return self._nvp_error("81002", "Unspecified Method")
