"""Map recorded checkout exchanges into canonical money events."""

from decimal import Decimal
from fractions import Fraction
from urllib.parse import parse_qsl, urlsplit

from goldgraft_contracts.currencies import CURRENCY_MINOR_DIGITS
from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.runner import RawCapture

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
    digits = CURRENCY_MINOR_DIGITS[currency]
    decimal = Decimal(value)
    if not decimal.is_finite():
        raise ValueError("non-finite PayPal amount")
    scaled = Fraction(decimal) * 10**digits
    if scaled.denominator != 1:
        raise ValueError("fractional minor units")
    return {"minor": int(scaled), "currency": currency}


def to_cmel(capture: RawCapture) -> list[MoneyEvent]:
    raw = capture.model_dump(mode="json")
    filename = f"{capture.scenario_id}.{capture.variant}.json"
    events = []
    requests, tokens, orders, notifications = {}, {}, {}, {}
    for index, x in enumerate(raw["exchanges"]):
        h = {key.lower(): value for key, value in x["headers"].items()}
        direction, path = x["direction"], urlsplit(x["url"]).path
        body = x.get("body_json") or {}
        ref = h.get("x-goldgraft-order-ref")
        if not ref and direction == "SHOP_TO_PAYPAL" and path.endswith("/cgi-bin/webscr"):
            fields = nvp(x)
            ref = fields.get("invoice") or fields.get("custom")
        if not ref:
            continue
        token, order_id = tokens.get(ref), orders.get(ref)
        notification_pp = notifications.get(ref, {})
        pp, amount, status, kind, source = {}, None, None, None, None
        if direction == "SHOP_TO_PAYPAL":
            fields = nvp(x)
            if (
                path.endswith("/cgi-bin/webscr")
                and ("amount" in fields or "amount_n" in fields)
                and fields.get("cmd") != "_notify-validate"
            ):
                kind, source = "INTENT", "PAYPAL_CALL"
                amount = money(
                    fields.get("amount", fields.get("amount_n")), fields["currency_code"]
                )
            else:
                requests[ref] = x
                continue
        elif direction == "SHOP_DB_WRITE":
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
            # Content decides, not the path: a migrated shop may keep its webhook at /ipn.php.
            if path == "/ipn.php" and "resource" not in body:
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
            notifications[ref] = pp.copy()
        elif direction == "PAYPAL_TO_SHOP":
            request = requests.pop(ref, None)
            if request is None:
                raise ValueError(f"Unpaired PayPal response at exchange {index}")
            ledger = h.get("x-goldgraft-ledger")
            if (x.get("status") or 200) >= 400:
                continue
            source = "PAYPAL_LEDGER" if ledger else "PAYPAL_CALL"
            fields = nvp(x)
            operation = nvp(request).get("METHOD")
            if operation and fields.get("ACK") not in {"Success", "SuccessWithWarning"}:
                continue
            if operation == "SetExpressCheckout":
                tokens[ref] = token = fields["TOKEN"]
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
                            "PARENTTRANSACTIONID", h.get("x-goldgraft-parent-capture")
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
            elif operation == "DoDirectPayment":
                kind, pp = "CAPTURE", {"txn_id": fields["TRANSACTIONID"]}
                currency = fields.get("CURRENCYCODE") or nvp(request)["CURRENCYCODE"]
                amount = money(fields["AMT"], currency)
                status = fields.get("PAYMENTSTATUS", "Completed").upper()
            elif operation == "CreateRecurringPaymentsProfile":
                kind, pp = "RECUR_SETUP", {"profile_id": fields["PROFILEID"]}
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
                orders[ref] = order_id = body["id"]
                kind, pp = "INTENT", {"order_id": order_id}
                unit = body["purchase_units"][0]
                amount = money(unit["amount"]["value"], unit["amount"]["currency_code"])
            elif "/v2/payments/refunds/" in path or path.endswith("/refund"):
                kind = "REFUND"
                pp = {
                    "order_id": order_id,
                    "capture_id": h.get("x-goldgraft-parent-capture"),
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
            if kind and source in {"PAYPAL_CALL", "PAYPAL_LEDGER"}:
                debug = fields.get("CORRELATIONID") or h.get("paypal-debug-id")
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
            events.append(MoneyEvent.model_validate(event))
    return events
