"""Small offline reference for the mapping rows used by C4 (01 §3 and 02 R3).

Recorder annotations X-GoldGraft-* are capture metadata, not wire headers sent to
PayPal. Errors stay in raw evidence; the table defines no general ERROR mapping.
"""

from decimal import Decimal
from urllib.parse import parse_qsl, urlsplit

NOISE = [
    "run_id",
    "variant",
    "raw_ref",
    "t_ms",
    "pp.legacy_token",
    "pp.txn_id",
    "pp.order_id",
    "pp.capture_id",
    "pp.refund_id",
    "pp.debug_id",
]


def nvp(exchange):
    return dict(parse_qsl(exchange.get("body_text", "")))


def money(value, currency):
    digits = 0 if currency in {"HUF", "JPY", "TWD"} else 2
    scaled = Decimal(value) * 10**digits
    if scaled != scaled.to_integral_value():
        raise ValueError("fractional minor units")
    return {"minor": int(scaled), "currency": currency}


def map_capture(raw, filename):
    events, request, token, order_id, notification_pp = [], None, None, None, {}
    for index, x in enumerate(raw["exchanges"]):
        h = x["headers"]
        direction, path = x["direction"], urlsplit(x["url"]).path
        body = x.get("body_json", {})
        ref = h["X-GoldGraft-Order-Ref"]
        pp, amount, status, kind, source = {}, None, None, None, None
        if direction == "SHOP_TO_PAYPAL":
            request = x
            continue
        if direction == "SHOP_DB_WRITE":
            after = x["db_change"]["after"]
            if after["status"] not in {"paid", "pending", "unpaid"}:
                raise ValueError("unmapped DB status")
            kind = {"paid": "SHOP_PAID", "pending": "SHOP_PENDING", "unpaid": "SHOP_UNPAID"}[
                after["status"]
            ]
            source = "SHOP_DB"
            amount = {"minor": after["total_minor"], "currency": after["currency"]}
        elif direction == "BROWSER_TO_SHOP" and path in {
            "/api/approve",
            "/api/execute-payment.php",
        }:
            kind, source = "APPROVE", "SHOP_HTTP"
            pp = (
                {"order_id": body["orderId"]}
                if raw["variant"] == "NEW"
                else {"legacy_token": body["token"]}
            )
        elif direction == "PAYPAL_NOTIFY_TO_SHOP":
            kind, source = "NOTIFY", "NOTIFICATION"
            if path == "/ipn.php":
                fields = nvp(x)
                pp = {"legacy_token": token, "txn_id": fields["txn_id"]}
                amount = money(fields["mc_gross"], fields["mc_currency"])
                status = fields["payment_status"].upper()
            else:
                resource = body["resource"]
                pp = {
                    "order_id": resource["supplementary_data"]["related_ids"]["order_id"],
                    "capture_id": resource["id"],
                }
                amount = money(resource["amount"]["value"], resource["amount"]["currency_code"])
                status = resource["status"]
            notification_pp = pp.copy()
        elif direction == "PAYPAL_TO_SHOP" and x.get("status", 200) < 400:
            assert request is not None
            ledger = h.get("X-GoldGraft-Ledger")
            source = "PAYPAL_LEDGER" if ledger else "PAYPAL_CALL"
            fields = nvp(x)
            operation = nvp(request).get("METHOD")
            if operation and fields.get("ACK") not in {"Success", "SuccessWithWarning"}:
                continue
            if operation == "SetExpressCheckout":
                token = fields["TOKEN"]
                req = nvp(request)
                kind, pp = "INTENT", {"legacy_token": token}
                amount = money(req["PAYMENTREQUEST_0_AMT"], req["PAYMENTREQUEST_0_CURRENCYCODE"])
            elif operation in {"DoExpressCheckoutPayment", "GetTransactionDetails"}:
                if ledger == "refund":
                    kind = "REFUND"
                    # A refund is a separate NVP transaction, negative AMT in the ledger.
                    pp = {
                        "legacy_token": token,
                        "txn_id": nvp(request).get(
                            "PARENTTRANSACTIONID", h["X-GoldGraft-Parent-Capture"]
                        ),
                        "refund_id": fields["TRANSACTIONID"],
                    }
                    amount = money(str(abs(Decimal(fields["AMT"]))), fields["CURRENCYCODE"])
                    status = "REFUNDED"
                else:
                    prefix = "PAYMENTINFO_0_" if operation == "DoExpressCheckoutPayment" else ""
                    kind = "CAPTURE"
                    pp = {"legacy_token": token, "txn_id": fields[prefix + "TRANSACTIONID"]}
                    amount = money(fields[prefix + "AMT"], fields[prefix + "CURRENCYCODE"])
                    status = fields[prefix + "PAYMENTSTATUS"].upper()
            elif operation == "RefundTransaction" and "REFUNDTRANSACTIONID" in fields:
                kind = "REFUND"
                pp = {
                    "legacy_token": token,
                    "txn_id": nvp(request)["TRANSACTIONID"],
                    "refund_id": fields["REFUNDTRANSACTIONID"],
                }
                amount = money(fields["GROSSREFUNDAMT"], fields["CURRENCYCODE"])
                status = "REFUNDED" if fields["REFUNDSTATUS"] == "instant" else "PENDING"
            elif path.endswith("/cgi-bin/webscr") and x.get("body_text") in {"VERIFIED", "INVALID"}:
                source = "NOTIFICATION"
                kind = "NOTIFY_VERIFIED" if x["body_text"] == "VERIFIED" else "NOTIFY_REJECTED"
                pp = notification_pp.copy()
            elif path.endswith("/verify-webhook-signature"):
                source, pp = "NOTIFICATION", notification_pp.copy()
                kind = (
                    "NOTIFY_VERIFIED"
                    if body["verification_status"] == "SUCCESS"
                    else "NOTIFY_REJECTED"
                )
            elif path == "/v2/checkout/orders" and request["method"] == "POST":
                order_id = body["id"]
                kind, pp = "INTENT", {"order_id": order_id}
                unit = body["purchase_units"][0]
                amount = money(unit["amount"]["value"], unit["amount"]["currency_code"])
            elif "/v2/payments/refunds/" in path or path.endswith("/refund"):
                kind = "REFUND"
                pp = {
                    "order_id": order_id,
                    "capture_id": h["X-GoldGraft-Parent-Capture"],
                    "refund_id": body["id"],
                }
                amount = money(body["amount"]["value"], body["amount"]["currency_code"])
                status = "REFUNDED" if body["status"] == "COMPLETED" else body["status"]
            elif "/v2/payments/captures/" in path:
                kind = "CAPTURE"
                pp = {
                    "order_id": body["supplementary_data"]["related_ids"]["order_id"],
                    "capture_id": body["id"],
                }
                amount = money(body["amount"]["value"], body["amount"]["currency_code"])
                status = body["status"]
            elif path.endswith("/capture") or (ledger and "purchase_units" in body):
                units = body.get("purchase_units", [])
                captures = units[0].get("payments", {}).get("captures", []) if units else []
                if captures:
                    capture = captures[0]
                    kind = "CAPTURE"
                    pp = {"order_id": body["id"], "capture_id": capture["id"]}
                    amount = money(capture["amount"]["value"], capture["amount"]["currency_code"])
                    status = capture["status"]
            if kind and source == "PAYPAL_CALL":
                debug = fields.get("CORRELATIONID") or h.get("PayPal-Debug-Id")
                if debug:
                    pp["debug_id"] = debug
            elif kind and source == "PAYPAL_LEDGER":
                debug = fields.get("CORRELATIONID") or h.get("PayPal-Debug-Id")
                if debug:
                    pp["debug_id"] = debug
        if kind:
            event = {key: raw[key] for key in ("graft_id", "run_id", "variant", "scenario_id")}
            event.update(
                seq=len(events),
                t_ms=x["t_ms"],
                source=source,
                kind=kind,
                order_ref=ref,
                pp=pp,
                raw_ref=f"raw/{filename}#/exchanges/{index}",
                noise=NOISE,
            )
            if amount is not None:
                event["money"] = amount
            if status is not None:
                event["status_norm"] = status
            events.append(event)
    return events
