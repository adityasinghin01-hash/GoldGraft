"""Rebuild the C4 synthetic corpus locally, with no network or new dependencies."""

import copy
import difflib
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

from cmel_reference import NOISE, map_capture
from goldgraft_contracts.base_rules import BASE_RULES
from goldgraft_contracts.registry import validate
from heal_reference import decision, probabilities

ROOT = Path(__file__).resolve().parents[1]
PROOF = "proof/legacy-php-shop/"
COMMIT = "aedc11dde1a8793285665ca2188aff62ab5aab65"
REPO = "https://github.com/jeretc/cutover"
UPSTREAM = f"{REPO}/tree/{COMMIT}/samples/legacy-php-shop"
SYNTHETIC = (
    "SYNTHETIC — hand-made from PayPal docs; not a recording and not a claim about the real shop"
)
DOC = "https://developer.paypal.com/"
NVP = DOC + "api/nvp-soap/"
ORDERS = DOC + "api/orders/v2/"
PAYMENTS = DOC + "api/payments/v2/"
WEBHOOKS = DOC + "api/webhooks/v1/"
SDK = DOC + "sdk/js/reference/"
SOURCES = [
    NVP + "set-express-checkout-nvp/",
    NVP + "get-express-checkout-details-nvp/",
    NVP + "do-express-checkout-payment-nvp/",
    NVP + "refund-transaction-nvp/",
    NVP + "get-transaction-details-nvp/",
    NVP + "ipn/IPNandPDTVariables/",
    NVP + "ipn/ht-ipn/",
    NVP + "errors/",
    PAYMENTS + "schema.json",
    ORDERS,
    PAYMENTS,
    WEBHOOKS,
    SDK,
]
SCENARIOS = [
    "HAPPY",
    "PENDING",
    "REFUND",
    "REFUND_TWICE",
    "DOUBLE",
    "DECLINE",
    "NOTIFY_FORGED",
    "NOTIFY_DUP",
    "PARITY_EXTRA",
]
GRADES = dict(
    zip(
        SCENARIOS,
        ["PASS", "PROBLEM", "PASS", "PASS_FIXED", "PASS", "PASS", "PASS", "UNVERIFIED", "PROBLEM"],
        strict=True,
    )
)
FORMATS = {}
PURPOSES = {}
# Hand-written files (not produced by write()); keep their index wording on regeneration.
PURPOSES.update({
    'switch-libs/php/API.md': 'API notes for the GoldGraft Orders v2 PHP library (given to the Grafter when it writes code)',
    'switch-libs/php/paypal_orders.php': 'Hand-written GoldGraft Orders v2 PHP library the AI-written checkout calls (not AI-written)',
})


def write(path, data, schema=None, purpose="Synthetic reference answer key"):
    file = ROOT / path
    file.parent.mkdir(parents=True, exist_ok=True)
    if schema:
        many = schema.endswith("[]")
        for record in data if many else [data]:
            validate(schema.removesuffix("[]"), record)
    elif isinstance(data, dict):
        data = {"_label": SYNTHETIC, "_source": SOURCES, **data}
    file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    FORMATS[path], PURPOSES[path] = schema or "reference", purpose


def loc(file, line):
    return {"file": "src/" + file, "line": line}


def build_shop():
    # Executable integration sites, endpoint definitions/uses and SDK hooks.
    # Comment-only mentions, presentation text, credential names and CSS are not operations.
    sites = [
        ("EC_NVP", "NVP endpoint definition", "config.php", 7, ORDERS, "POST /v2/checkout/orders"),
        ("EC_NVP", "NVP client wrapper", "lib/paypal_nvp.php", 5, ORDERS, "REST HTTP client"),
        ("EC_NVP", "NVP endpoint transport", "lib/paypal_nvp.php", 14, ORDERS, "REST HTTP client"),
        (
            "EC_NVP",
            "SetExpressCheckout",
            "api/create-payment.php",
            20,
            ORDERS,
            "POST /v2/checkout/orders",
        ),
        ("EC_NVP", "RETURNURL", "api/create-payment.php", 25, SDK, "v6 onApprove"),
        ("EC_NVP", "CANCELURL", "api/create-payment.php", 26, SDK, "v6 onCancel"),
        (
            "EC_NVP",
            "GetExpressCheckoutDetails",
            "api/execute-payment.php",
            12,
            ORDERS,
            "GET /v2/checkout/orders/{id}",
        ),
        (
            "EC_NVP",
            "DoExpressCheckoutPayment",
            "api/execute-payment.php",
            15,
            ORDERS,
            "POST /v2/checkout/orders/{id}/capture",
        ),
        (
            "EC_NVP",
            "RefundTransaction",
            "api/refund.php",
            11,
            PAYMENTS,
            "POST /v2/payments/captures/{id}/refund",
        ),
        (
            "IPN",
            "IPN verification endpoint definition",
            "config.php",
            9,
            WEBHOOKS,
            "POST /v1/notifications/verify-webhook-signature",
        ),
        ("IPN", "IPN input handler", "ipn.php", 6, WEBHOOKS, "webhook input handler"),
        (
            "IPN",
            "IPN verification transport",
            "ipn.php",
            7,
            WEBHOOKS,
            "POST /v1/notifications/verify-webhook-signature",
        ),
        (
            "IPN",
            "_notify-validate",
            "ipn.php",
            9,
            WEBHOOKS,
            "POST /v1/notifications/verify-webhook-signature",
        ),
        (
            "IPN",
            "VERIFIED / Completed gate",
            "ipn.php",
            15,
            WEBHOOKS,
            "SUCCESS / PAYMENT.CAPTURE.COMPLETED gate",
        ),
        (
            "IPN",
            "IPN accepted-payment log",
            "ipn.php",
            16,
            WEBHOOKS,
            "deduplicated webhook persistence",
        ),
        ("CHECKOUT_JS_V4", "checkout.js script", "index.php", 31, SDK, "v6 core script"),
        ("CHECKOUT_JS_V4", "PayPal button mount", "index.php", 24, SDK, "v6 paypal-button"),
        (
            "CHECKOUT_JS_V4",
            "paypal.Button.render",
            "index.php",
            38,
            SDK,
            "v6 createPayPalOneTimePaymentSession",
        ),
        (
            "CHECKOUT_JS_V4",
            "payment / create callback",
            "index.php",
            43,
            SDK,
            "server create order / session start",
        ),
        ("CHECKOUT_JS_V4", "onAuthorize", "index.php", 45, SDK, "v6 onApprove"),
        (
            "CHECKOUT_JS_V4",
            "approved confirmation POST",
            "index.php",
            46,
            SDK,
            "server capture from v6 onApprove",
        ),
        ("CHECKOUT_JS_V4", "onCancel", "index.php", 51, SDK, "v6 onCancel"),
        ("EC_NVP", "return page", "success.php", 1, SDK, "v6 onApprove result UI"),
        ("EC_NVP", "cancel page", "cancel.php", 1, SDK, "v6 onCancel result UI"),
    ]
    touchpoints = [
        {
            "id": f"TP{i:02}",
            "family": family,
            "operation": operation,
            "location": loc(file, line),
            "lenses": ["code"],
            "confidence": 1,
            "live": False,
            "target": {"paypal_mapping_id": source, "rest_op": target},
            "paypal_only": False,
        }
        for i, (family, operation, file, line, source, target) in enumerate(sites, 1)
    ]
    flow = {
        "create": [
            loc("api/create-payment.php", 10),
            loc("api/create-payment.php", 20),
            loc("api/create-payment.php", 32),
        ],
        "approve": [loc("index.php", 45), loc("index.php", 46), loc("api/execute-payment.php", 8)],
        "capture": [loc("api/execute-payment.php", 12), loc("api/execute-payment.php", 15)],
        "mark_paid": [
            loc("api/execute-payment.php", 23),
            loc("api/execute-payment.php", 27),
            loc("lib/orders_store.php", 11),
        ],
        "refund": [
            loc("api/refund.php", 9),
            loc("api/refund.php", 11),
            loc("api/refund.php", 13),
            loc("api/refund.php", 14),
        ],
        "notify": [loc("ipn.php", 6), loc("ipn.php", 9), loc("ipn.php", 15), loc("ipn.php", 16)],
        "recurring": [],
    }
    pack = {
        "shop_id": "legacy-php-shop",
        "name": "Cutover legacy PHP test shop",
        "language": "PHP",
        "framework": "plain PHP",
        "licence": "MIT",
        "source": {"repo": REPO, "commit": COMMIT},
        "start": {"compose_file": "docker-compose.yml"},
        "port": 8081,
        "health_url": "http://localhost:8081/index.php",
        "buyer_script": "buyer.spec.ts",
        "scenarios_supported": SCENARIOS,
        "answer_key": {"touchpoints": touchpoints, "money_flow": flow},
        "env_needed": [
            "PAYPAL_NVP_USER",
            "PAYPAL_NVP_PWD",
            "PAYPAL_NVP_SIGNATURE",
            "SHOP_BASE_URL",
            "SHOP_RECEIVER_EMAIL",
        ],
    }
    # JSON is a strict YAML subset, avoiding a YAML dependency in offline tests.
    write(
        "shops/legacy-php-shop/goldgraft-shop.yaml",
        pack,
        "ShopPack/1",
        "Code-lens recall answer key: 24 touchpoints; C5 start/driver paths",
    )
    (ROOT / "shops/legacy-php-shop/NOTICE.md").write_text(
        f"# Cutover legacy PHP shop\n\nSource: {UPSTREAM}\n\n"
        f"Commit: `{COMMIT}`. Licence: MIT (see LICENSE.cutover).\n\n"
        "Vendored as a test shop; not modified. All 15 upstream sample files are byte-"
        "for-byte copies.\n"
        "This is REAL source code, not a payment recording. Upstream's DEMOPASSWORD and\n"
        "DEMOSIGNATURE are demonstration placeholders, not credentials.\n\n"
        "The proof traces are SYNTHETIC examples of the GoldGraft specification.\n"
        "They are not executions of this shop. In particular execute-payment.php:23\n"
        "unconditionally marks successful NVP responses PAID, refund.php:9–12 guards\n"
        "and checks refunds, and ipn.php:16 appends a log without updating orders.\n"
        "The requested synthetic OLD pending behavior and second-refund bug must not\n"
        "be attributed to this code. The float arithmetic in the vendor is preserved.\n"
    )
    rootmap = {
        "shop_id": pack["shop_id"],
        "stack": {"lang": "PHP", "framework": "plain PHP", "versions": {}, "db": "flat JSON file"},
        "lenses_run": ["code"],
        "touchpoints": copy.deepcopy(touchpoints[:-1]),
        "money_flow": flow,
        "recall_evidence": {"runtime_calls_total": 0, "matched_by_static": 0, "misses": []},
    }
    fp = copy.deepcopy(touchpoints[0])
    fp.update(
        id="FP01",
        operation="DoDirectPayment",
        family="DIRECT_PAYMENT",
        location=loc("index.php", 34),
        confidence=0.3,
    )
    rootmap["touchpoints"].append(fp)
    write(PROOF + "survey/rootmap_with_one_miss.json", rootmap, "RootMap/1")
    write(
        PROOF + "survey/expected_scores.json",
        {
            "matching_key": ["family", "operation", "location.file", "location.line"],
            "answer_key_count": 24,
            "reported_count": 24,
            "true_positive": 23,
            "false_negative": 1,
            "false_positive": 1,
            "recall": 23 / 24,
            "precision": 23 / 24,
            "missing_touchpoint": "TP24",
            "false_positive_touchpoint": "FP01",
        },
    )
    deltas = [
        {
            "id": "D_TOKEN_ORDER",
            "mapping_id": ORDERS,
            "description": "Map pp.legacy_token to pp.order_id for the same logical or"
            "der; preserve order_ref and money. Different run IDs are n"
            "oise, not a new order.",
        },
        {
            "id": "D_TXN_CAPTURE",
            "mapping_id": ORDERS,
            "description": "Map NVP PAYMENTINFO_0_TRANSACTIONID / ledger TRANSACTIONID"
            " to REST capture_id, preserving distinct captures, amount,"
            " currency and status.",
        },
        {
            "id": "D_APPROVE",
            "mapping_id": SDK,
            "description": "Map checkout.js onAuthorize/approved token+PayerID return "
            "to v6 onApprove orderId. Preserve APPROVE and its causal p"
            "osition.",
        },
        {
            "id": "D_NOTIFY",
            "mapping_id": WEBHOOKS,
            "description": "IPN Completed becomes webhook PAYMENT.CAPTURE.COMPLETED. V"
            "ERIFIED/INVALID becomes verification_status SUCCESS/FAILUR"
            "E. Preserve NOTIFY and verification result, amounts and ca"
            "usal order.",
        },
        {
            "id": "D_LEDGER_READ",
            "mapping_id": ORDERS,
            "description": "One NVP GetTransactionDetails capture lookup becomes GET o"
            "rder plus GET capture. Coalesce repeated ledger observatio"
            "ns with the same economic ID, status and money; preserve d"
            "ifferent IDs and state revisions. Renumber observation seq"
            " after this read fan-out.",
        },
        {
            "id": "D_REFUND",
            "mapping_id": PAYMENTS,
            "description": "Map successful NVP RefundTransaction instant refund and Ge"
            "tTransactionDetails refund ledger to REST refund COMPLETED"
            " / GET refund. IDs differ, REFUND amount and REFUNDED stat"
            "us do not.",
        },
    ]
    plan = {
        "path": "REWRITE",
        "items": [
            {
                "touchpoint": tp["id"],
                "target_op": tp["target"]["rest_op"],
                "mapping_id": tp["target"]["paypal_mapping_id"],
                "delta_ids": ["D_NOTIFY"]
                if tp["family"] == "IPN"
                else (
                    ["D_REFUND"]
                    if tp["operation"] == "RefundTransaction"
                    else ["D_TOKEN_ORDER", "D_TXN_CAPTURE", "D_APPROVE", "D_LEDGER_READ"]
                ),
                "paypal_only": False,
            }
            for tp in touchpoints
        ],
        "target_experience": ["V6", "ORDERS_V2", "WEBHOOKS"],
        "origin_rules": [
            "Old transaction refunds remain NVP RefundTransaction; REST refunds apply "
            "only to new captures. No cross-generation refund equivalence is claimed.",
            "Keep the IPN listener for old objects; keep in-flight sessions on their birth rail.",
        ],
        "order": ["READ_BOTH", "NEW_FLOWS_BEHIND_SWITCH", "CLEANUP"],
        "handoff": [],
        "deltas": deltas,
    }
    write(PROOF + "target_plan.json", plan, "TargetPlan/1")
    return pack


class Capture:
    def __init__(self, scenario, variant):
        self.scenario, self.variant = scenario, variant
        self.new = variant == "NEW"
        self.ref = "SHOP-" + scenario
        self.exchanges = []
        # Only these correlation identities and timing differ between the old twins.
        seed = scenario + ":" + variant
        self.token = "EC-" + hashlib.sha256(seed.encode()).hexdigest()[:17].upper()
        self.order = hashlib.sha256((seed + "order").encode()).hexdigest()[:17].upper()
        self.txn = hashlib.sha256((seed + "capture").encode()).hexdigest()[:17].upper()
        self.refund = hashlib.sha256((seed + "refund").encode()).hexdigest()[:17].upper()
        self.debug = hashlib.sha256((seed + "debug").encode()).hexdigest()[:13]
        self.clock = 1000 if variant == "OLD_TWIN" else 0
        self.date = "2026-11-02T10:01:00Z" if variant == "OLD_TWIN" else "2026-11-02T10:00:00Z"
        self.state = {
            "status": "unpaid",
            "total_minor": 2500,
            "currency": "USD",
            "refunded_minor": 0,
        }

    def add(
        self,
        direction,
        method,
        url,
        body=None,
        *,
        text=False,
        status=None,
        headers=None,
        db=None,
        ref=None,
    ):
        x = {
            "seq": len(self.exchanges),
            "t_ms": self.clock + 10 * len(self.exchanges),
            "direction": direction,
            "method": method,
            "url": url,
            "headers": {"X-GoldGraft-Order-Ref": ref or self.ref, **(headers or {})},
        }
        if db:
            x["db_change"] = db
        else:
            x["body_text" if text else "body_json"] = body
        if status is not None:
            x["status"] = status
        self.exchanges.append(x)

    def nvp(self, method, request, response, *, ledger=None, parent=None):
        url = "https://api-3t.sandbox.paypal.com/nvp"
        h = {"Content-Type": "application/x-www-form-urlencoded"}
        if ledger:
            h["X-GoldGraft-Ledger"] = ledger
        if parent:
            h["X-GoldGraft-Parent-Capture"] = parent
        self.add(
            "SHOP_TO_PAYPAL",
            "POST",
            url,
            urlencode(
                {
                    "METHOD": method,
                    "VERSION": "204.0",
                    "USER": "[REDACTED]",
                    "PWD": "[REDACTED]",
                    "SIGNATURE": "[REDACTED]",
                    **request,
                }
            ),
            text=True,
            headers=h,
        )
        self.add(
            "PAYPAL_TO_SHOP",
            "POST",
            url,
            urlencode(
                {
                    "ACK": "Success",
                    "VERSION": "204.0",
                    "TIMESTAMP": self.date,
                    "CORRELATIONID": self.debug,
                    **response,
                }
            ),
            text=True,
            status=200,
            headers=h,
        )

    def rest(
        self,
        method,
        path,
        request,
        response,
        *,
        status=200,
        ledger=None,
        parent=None,
        ref=None,
        request_id=None,
    ):
        url = "https://api-m.sandbox.paypal.com" + path
        h = {"Content-Type": "application/json"}
        if ledger:
            h["X-GoldGraft-Ledger"] = ledger
        if parent:
            h["X-GoldGraft-Parent-Capture"] = parent
        req_h = {**h, "Authorization": "[REDACTED]"}
        if method == "POST" and not path.endswith("verify-webhook-signature"):
            req_h.update(
                {
                    "PayPal-Request-Id": request_id or self.ref + ":" + path.rsplit("/", 1)[-1],
                    "Prefer": "return=representation",
                }
            )
        self.add("SHOP_TO_PAYPAL", method, url, request, headers=req_h, ref=ref)
        self.add(
            "PAYPAL_TO_SHOP",
            method,
            url,
            response,
            status=status,
            headers={**h, "PayPal-Debug-Id": self.debug},
            ref=ref,
        )

    def db(self, status, refunded=None):
        before = copy.deepcopy(self.state)
        self.state["status"] = status
        if refunded is not None:
            self.state["refunded_minor"] = refunded
        self.add(
            "SHOP_DB_WRITE",
            "UPDATE",
            "db://synthetic/orders",
            db={
                "table": "orders",
                "key": {"order_ref": self.ref},
                "before": before,
                "after": copy.deepcopy(self.state),
            },
        )

    def cap_object(self, status="COMPLETED"):
        return {
            "id": self.txn,
            "status": status,
            "amount": {"currency_code": "USD", "value": "25.00"},
            "final_capture": True,
            "create_time": self.date,
            "update_time": self.date,
            "supplementary_data": {"related_ids": {"order_id": self.order}},
        }

    def order_object(self, status="CREATED", capture=None, *, extra=False):
        unit = {
            "reference_id": self.ref + ("-EXTRA" if extra else ""),
            "amount": {"currency_code": "USD", "value": "12.50" if extra else "25.00"},
        }
        if capture:
            unit["payments"] = {
                "captures": [{k: v for k, v in capture.items() if k != "supplementary_data"}]
            }
        return {
            "id": ("EXTRA" + self.order[:12]) if extra else self.order,
            "intent": "CAPTURE",
            "status": status,
            "purchase_units": [unit],
            "create_time": self.date,
        }

    def create(self, *, extra=False):
        if self.new:
            ref = self.ref + "-EXTRA" if extra else self.ref
            self.rest(
                "POST",
                "/v2/checkout/orders",
                {
                    "intent": "CAPTURE",
                    "purchase_units": [
                        {
                            "reference_id": ref,
                            "amount": {
                                "currency_code": "USD",
                                "value": "12.50" if extra else "25.00",
                            },
                        }
                    ],
                },
                self.order_object(extra=extra),
                status=201,
                ref=ref,
                request_id=ref + ":create",
            )
        else:
            self.nvp(
                "SetExpressCheckout",
                {
                    "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
                    "PAYMENTREQUEST_0_AMT": "25.00",
                    "PAYMENTREQUEST_0_ITEMAMT": "25.00",
                    "PAYMENTREQUEST_0_CURRENCYCODE": "USD",
                    "PAYMENTREQUEST_0_INVNUM": self.ref,
                    "L_PAYMENTREQUEST_0_NAME0": "Cutover Tee",
                    "L_PAYMENTREQUEST_0_AMT0": "25.00",
                    "L_PAYMENTREQUEST_0_QTY0": "1",
                    "RETURNURL": "https://shop.example/success.php",
                    "CANCELURL": "https://shop.example/cancel.php",
                },
                {"TOKEN": self.token},
            )
            # An incoming browser exchange can retain its response Location header.
            self.add(
                "BROWSER_TO_SHOP",
                "GET",
                "https://shop.example/checkout",
                "",
                text=True,
                status=302,
                headers={
                    "Location": "https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_ex"
                    "press-checkout&token=" + self.token
                },
            )

    def approve(self):
        if self.new:
            self.add(
                "BROWSER_TO_SHOP",
                "POST",
                "https://shop.example/api/approve",
                {"orderId": self.order},
            )
        else:
            self.add(
                "BROWSER_TO_SHOP",
                "POST",
                "https://shop.example/api/execute-payment.php",
                {"token": self.token, "payerID": "FAKEPAYER0001"},
            )

    def capture(self, pending=False, decline=False):
        if self.new:
            # Backend checks actual PayPal approval, not just a browser claim.
            self.rest(
                "GET", "/v2/checkout/orders/" + self.order, None, self.order_object("APPROVED")
            )
            if decline:
                self.rest(
                    "POST",
                    f"/v2/checkout/orders/{self.order}/capture",
                    {},
                    {
                        "name": "UNPROCESSABLE_ENTITY",
                        "message": "The requested action could not be performed.",
                        "debug_id": self.debug,
                        "details": [
                            {
                                "issue": "INSTRUMENT_DECLINED",
                                "description": "The instrument was declined.",
                            }
                        ],
                    },
                    status=422,
                )
            else:
                self.rest(
                    "POST",
                    f"/v2/checkout/orders/{self.order}/capture",
                    {},
                    self.order_object(
                        "COMPLETED", self.cap_object("PENDING" if pending else "COMPLETED")
                    ),
                    status=201,
                )
        else:
            self.nvp(
                "GetExpressCheckoutDetails",
                {"TOKEN": self.token},
                {
                    "TOKEN": self.token,
                    "PAYERID": "FAKEPAYER0001",
                    "EMAIL": "buyer@example.invalid",
                    "PAYMENTREQUEST_0_AMT": "25.00",
                    "PAYMENTREQUEST_0_CURRENCYCODE": "USD",
                },
            )
            response = (
                {
                    "ACK": "Failure",
                    "L_ERRORCODE0": "10486",
                    "L_SHORTMESSAGE0": "This transaction couldn't be completed.",
                    "L_LONGMESSAGE0": "This transaction couldn't be completed. Please "
                    "redirect your customer to PayPal.",
                    "L_SEVERITYCODE0": "Error",
                }
                if decline
                else {
                    "PAYMENTINFO_0_TRANSACTIONID": self.txn,
                    "PAYMENTINFO_0_AMT": "25.00",
                    "PAYMENTINFO_0_CURRENCYCODE": "USD",
                    "PAYMENTINFO_0_PAYMENTSTATUS": "Pending" if pending else "Completed",
                }
            )
            if pending:
                response["PAYMENTINFO_0_PENDINGREASON"] = "echeck"
            self.nvp(
                "DoExpressCheckoutPayment",
                {
                    "TOKEN": self.token,
                    "PAYERID": "FAKEPAYER0001",
                    "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
                    "PAYMENTREQUEST_0_AMT": "25.00",
                    "PAYMENTREQUEST_0_CURRENCYCODE": "USD",
                },
                response,
            )

    def notify(self, forged=False):
        if self.new:
            event = {
                "id": "WH-FAKE-" + self.scenario,
                "create_time": self.date,
                "resource_type": "capture",
                "event_type": "PAYMENT.CAPTURE.COMPLETED",
                "resource_version": "2.0",
                "event_version": "1.0",
                "resource": self.cap_object(),
            }
            headers = {
                "PAYPAL-AUTH-ALGO": "SHA256withRSA",
                "PAYPAL-CERT-URL": "https://api.sandbox.paypal.com/v1/notifications/certs/FAKE",
                "PAYPAL-TRANSMISSION-ID": "FAKE-TRANSMISSION-" + self.scenario,
                "PAYPAL-TRANSMISSION-SIG": "FAKE-SIGNATURE-FOR-TESTS",
                "PAYPAL-TRANSMISSION-TIME": self.date,
            }
            self.add(
                "PAYPAL_NOTIFY_TO_SHOP",
                "POST",
                "https://shop.example/pp/webhook",
                event,
                headers=headers,
            )
            self.rest(
                "POST",
                "/v1/notifications/verify-webhook-signature",
                {
                    "auth_algo": headers["PAYPAL-AUTH-ALGO"],
                    "cert_url": headers["PAYPAL-CERT-URL"],
                    "transmission_id": headers["PAYPAL-TRANSMISSION-ID"],
                    "transmission_sig": headers["PAYPAL-TRANSMISSION-SIG"],
                    "transmission_time": self.date,
                    "webhook_id": "FAKEWEBHOOKID",
                    "webhook_event": event,
                },
                {"verification_status": "FAILURE" if forged else "SUCCESS"},
            )
        else:
            body = urlencode(
                {
                    "txn_type": "express_checkout",
                    "payment_status": "Completed",
                    "mc_gross": "25.00",
                    "mc_currency": "USD",
                    "txn_id": self.txn,
                    "invoice": self.ref,
                    "receiver_email": "merchant@example.invalid",
                    "payment_date": "02:00:00 Nov 02, 2026 PST"
                    if self.variant != "OLD_TWIN"
                    else "02:01:00 Nov 02, 2026 PST",
                }
            )
            self.add(
                "PAYPAL_NOTIFY_TO_SHOP",
                "POST",
                "https://shop.example/ipn.php",
                body,
                text=True,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
            self.add("SHOP_TO_PAYPAL", "POST", url, "cmd=_notify-validate&" + body, text=True)
            self.add(
                "PAYPAL_TO_SHOP",
                "POST",
                url,
                "INVALID" if forged else "VERIFIED",
                text=True,
                status=200,
            )

    def ledger(self, *, capture=True, pending=False, refunded=False, failed=False):
        if self.new:
            self.rest(
                "GET",
                "/v2/checkout/orders/" + self.order,
                None,
                {
                    "name": "INTERNAL_SERVER_ERROR",
                    "message": "Synthetic ledger lookup failure",
                    "debug_id": self.debug,
                }
                if failed
                else self.order_object(
                    "COMPLETED" if capture else "APPROVED",
                    self.cap_object(
                        "REFUNDED" if refunded else "PENDING" if pending else "COMPLETED"
                    )
                    if capture
                    else None,
                ),
                status=500 if failed else 200,
                ledger="absence" if not capture else "order",
            )
            if capture and not failed:
                self.rest(
                    "GET",
                    "/v2/payments/captures/" + self.txn,
                    None,
                    self.cap_object(
                        "REFUNDED" if refunded else "PENDING" if pending else "COMPLETED"
                    ),
                    ledger="capture",
                )
            if refunded:
                self.rest(
                    "GET",
                    "/v2/payments/refunds/" + self.refund,
                    None,
                    {
                        "id": self.refund,
                        "status": "COMPLETED",
                        "amount": {"currency_code": "USD", "value": "25.00"},
                    },
                    ledger="refund",
                    parent=self.txn,
                )
        elif capture:
            self.nvp(
                "GetTransactionDetails",
                {"TRANSACTIONID": self.txn},
                {
                    "TRANSACTIONID": self.txn,
                    "AMT": "25.00",
                    "CURRENCYCODE": "USD",
                    "PAYMENTSTATUS": "Refunded"
                    if refunded
                    else "Pending"
                    if pending
                    else "Completed",
                    **({"PENDINGREASON": "echeck"} if pending else {}),
                },
                ledger="capture",
            )
            if refunded:
                self.nvp(
                    "GetTransactionDetails",
                    {"TRANSACTIONID": self.refund},
                    {
                        "TRANSACTIONID": self.refund,
                        "AMT": "-25.00",
                        "CURRENCYCODE": "USD",
                        "PAYMENTSTATUS": "Completed",
                    },
                    ledger="refund",
                    parent=self.txn,
                )
        else:
            # No transaction exists: inspect the known EC token.
            self.nvp(
                "GetExpressCheckoutDetails",
                {"TOKEN": self.token},
                {
                    "TOKEN": self.token,
                    "CHECKOUTSTATUS": "PaymentActionFailed"
                    if self.scenario == "DECLINE"
                    else "PaymentActionNotInitiated",
                    "PAYMENTREQUEST_0_AMT": "25.00",
                    "PAYMENTREQUEST_0_CURRENCYCODE": "USD",
                },
                ledger="absence",
            )

    def do_refund(self, second=False):
        if self.new:
            # Exercise remote refusal; do not record it as a successful refund.
            self.rest(
                "POST",
                f"/v2/payments/captures/{self.txn}/refund",
                {"amount": {"currency_code": "USD", "value": "25.00"}},
                {
                    "name": "UNPROCESSABLE_ENTITY",
                    "message": "The requested action could not be performed.",
                    "debug_id": self.debug,
                    "details": [
                        {
                            "issue": "CAPTURE_FULLY_REFUNDED",
                            "description": "Capture has been fully refunded.",
                        }
                    ],
                }
                if second
                else {
                    "id": self.refund,
                    "status": "COMPLETED",
                    "amount": {"currency_code": "USD", "value": "25.00"},
                },
                status=422 if second else 201,
                parent=self.txn,
                request_id=self.ref + (":refund:second" if second else ":refund:first"),
            )
        else:
            self.nvp(
                "RefundTransaction",
                {"TRANSACTIONID": self.txn, "REFUNDTYPE": "Full"},
                {
                    "ACK": "Failure",
                    "L_ERRORCODE0": "10009",
                    "L_SHORTMESSAGE0": "Transaction refused",
                    "L_LONGMESSAGE0": "This transaction has already been fully refunded.",
                    "L_SEVERITYCODE0": "Error",
                }
                if second
                else {
                    "REFUNDTRANSACTIONID": self.refund,
                    "GROSSREFUNDAMT": "25.00",
                    "CURRENCYCODE": "USD",
                    "REFUNDSTATUS": "instant",
                },
            )
        if not second:
            self.db("paid", 2500)
        elif not self.new:
            # Deliberately invented old-shop bug; NOT a claim about the vendored shop.
            self.db("paid", 5000)

    def build(self):
        s = self.scenario
        self.add(
            "BROWSER_TO_SHOP",
            "POST",
            "https://shop.example/api/create",
            {"cart": {"tee": 1}, "minor": 1, "currency": "EUR"},
        )
        self.create()
        self.approve()
        if s == "DOUBLE":
            self.approve()  # two tabs, one economic capture and one DB state change
        if s == "NOTIFY_FORGED":
            self.notify(forged=True)
            self.db("unpaid")
            self.ledger(capture=False)
        elif s == "DECLINE":
            self.capture(decline=True)
            self.db("unpaid")
            self.ledger(capture=False)
        elif s == "PENDING":
            self.capture(pending=True)
            self.db("paid" if self.new else "pending")
            # No completed notification exists yet; lookup is the R13 backstop.
            self.ledger(pending=True)
        else:
            self.capture()
            self.notify()
            self.db("paid")
            if s == "DOUBLE":
                for tab in (1, 2):
                    self.add(
                        "BROWSER_TO_SHOP",
                        "GET",
                        f"https://shop.example/api/confirmation-result?tab={tab}",
                        {"ok": True, "capture_id" if self.new else "transaction_id": self.txn},
                        status=200,
                    )
            if s == "NOTIFY_DUP":
                self.notify()  # same event/txn ID, no second DB write
            if s in {"REFUND", "REFUND_TWICE"}:
                self.ledger()  # pre-refund checkpoint proves the original completed capture
                self.do_refund()
                if s == "REFUND_TWICE":
                    self.do_refund(second=True)
                self.ledger(refunded=True)
            else:
                self.ledger(failed=s == "NOTIFY_DUP" and self.new)
            if s == "PARITY_EXTRA" and self.new:
                self.add(
                    "BROWSER_TO_SHOP",
                    "POST",
                    "https://shop.example/api/create",
                    {"cart": {"mug": 1}},
                    ref=self.ref + "-EXTRA",
                )
                self.create(extra=True)  # no delta permits an extra catalogue mug intent
                extra_id = "EXTRA" + self.order[:12]
                self.rest(
                    "GET",
                    "/v2/checkout/orders/" + extra_id,
                    None,
                    self.order_object(extra=True),
                    ledger="absence",
                    ref=self.ref + "-EXTRA",
                )
        return {
            "graft_id": "synthetic-c4",
            "run_id": s + "." + self.variant,
            "variant": self.variant,
            "scenario_id": s,
            "exchanges": self.exchanges,
        }


def event_ref(scenario, variant, events, kind, *, last=False, source=None):
    indices = [
        i
        for i, e in enumerate(events)
        if e["kind"] == kind and (source is None or e["source"] == source)
    ]
    return f"cmel/{scenario}.{variant}.json#/{indices[-1] if last else indices[0]}"


def build_scenarios():
    streams = {}
    for scenario in SCENARIOS:
        for variant in ("OLD", "OLD_TWIN", "NEW"):
            raw = Capture(scenario, variant).build()
            filename = f"{scenario}.{variant}.json"
            write(
                PROOF + "raw/" + filename,
                raw,
                "RawCapture/1",
                "Ordered synthetic HTTP/DB exchanges and tagged ledger reads",
            )
            cmel = map_capture(raw, filename)
            write(
                PROOF + "cmel/" + filename,
                cmel,
                "CMEL/1[]",
                "Expected mapper output for the matching raw stream",
            )
            streams[scenario, variant] = (raw, cmel)
        old = streams[scenario, "OLD"][1]
        new = streams[scenario, "NEW"][1]
        verdict = {
            "scenario_id": scenario,
            "grade": GRADES[scenario],
            "rule_hits": [],
            "parity_diff": [],
            "noise_masked": learned_noise(old, streams[scenario, "OLD_TWIN"][1]),
            "deltas_applied": ["D_TOKEN_ORDER", "D_APPROVE"],
        }
        if any("txn_id" in e["pp"] for e in old):
            verdict["deltas_applied"].append("D_TXN_CAPTURE")
        if any(e["kind"] == "CAPTURE" for e in old):
            verdict["deltas_applied"].append("D_LEDGER_READ")
        if any(e["kind"] == "NOTIFY" for e in old):
            verdict["deltas_applied"].append("D_NOTIFY")
        if any(e["kind"] == "REFUND" for e in old):
            verdict["deltas_applied"].append("D_REFUND")
        if scenario == "PENDING":
            paid = event_ref(scenario, "NEW", new, "SHOP_PAID")
            cap = event_ref(scenario, "NEW", new, "CAPTURE", source="PAYPAL_LEDGER")
            verdict["rule_hits"] = [
                {"rule": r, "side": "NEW", "evidence": [paid, cap]} for r in ("R01", "R07")
            ]
            verdict["parity_diff"] = [
                {
                    "type": "status_kind_mismatch",
                    "expected": "SHOP_PENDING",
                    "actual": "SHOP_PAID",
                    "event": paid,
                }
            ]
        elif scenario == "REFUND_TWICE":
            event = event_ref(scenario, "OLD", old, "SHOP_PAID", last=True)
            raw_ref = next(e["raw_ref"] for e in reversed(old) if e["kind"] == "SHOP_PAID")
            verdict["rule_hits"] = [{"rule": "R11", "side": "OLD", "evidence": [event, raw_ref]}]
        elif scenario == "PARITY_EXTRA":
            index = next(
                i
                for i, e in enumerate(new)
                if e["kind"] == "INTENT" and e["order_ref"].endswith("-EXTRA")
            )
            verdict["parity_diff"] = [
                {
                    "type": "extra_money_event",
                    "event": f"cmel/{scenario}.NEW.json#/{index}",
                    "kind": "INTENT",
                    "order_ref": "SHOP-PARITY_EXTRA-EXTRA",
                    "money": {"minor": 1250, "currency": "USD"},
                }
            ]
        write(PROOF + f"expected/{scenario}.verdict.json", verdict, "Verdict/1")
        expect = {
            "grade": GRADES[scenario],
            "synthetic_only": True,
            "description": {
                "HAPPY": "One approved completed capture, verified notification and paid state.",
                "PENDING": "OLD pending; NEW wrongly paid (R01 and R07). No completed "
                "callback; ledger backstop used.",
                "REFUND": "One completed capture and one successful full refund per wi"
                "tness; failed refunds are not REFUND events.",
                "REFUND_TWICE": "OLD synthetic DB claims 5000 minor refunded although "
                "PayPal refunded only 2500; NEW records only the first"
                " refund.",
                "DOUBLE": "Two approved confirmation attempts return one economic capt"
                "ure; stable idempotency and one DB state change.",
                "DECLINE": "Both capture calls fail; no transaction exists and no paid"
                " state. Successful absence lookup is not missing evidence.",
                "NOTIFY_FORGED": "Forged completed notification fails verification; no"
                " capture and no paid state.",
                "NOTIFY_DUP": "Duplicate event is harmless; NEW ledger read fails, so "
                "U2 evidence precedence yields UNVERIFIED.",
                "PARITY_EXTRA": "NEW adds an unapproved 1250 USD-minor catalogue mug i"
                "ntent, never captured; all contract rules hold, parit"
                "y fails.",
            }[scenario],
        }
        steps = [
            {
                "driver_step": "Post tee=1 cart with untrusted browser minor=1,currenc"
                "y=EUR; server uses catalogue 2500 USD"
            },
            {
                "api_step": "Create PayPal order, approve through checkout callback, f"
                "ollow scenario raw exchanges in order"
            },
            {"api_step": "Read PayPal ledger after run; preserve failures as evidence"},
        ]
        if scenario == "DECLINE":
            steps.insert(1, {"paypal_mock_response_code": "INSTRUMENT_DECLINED"})
        write(
            PROOF + f"scenarios/{scenario}.json",
            {
                "id": scenario,
                "family": "PROPERTY" if scenario == "PARITY_EXTRA" else scenario,
                "cart": {
                    "items": [{"sku": "tee", "qty": 1, "unit_minor": 2500}],
                    "total": {"minor": 2500, "currency": "USD"},
                    "browser_quote": {"minor": 1, "currency": "EUR"},
                },
                "steps": steps,
                "rules": [f"R{i:02}" for i in range(1, 18)],
                "expect": expect,
                "assured": {"passes_on_old": scenario != "REFUND_TWICE", "flake_free_runs": 0},
            },
            "Scenario/1",
        )
    counts = Counter(GRADES.values())
    write(
        PROOF + "expected/summary.json",
        {
            "shop_id": "legacy-php-shop",
            "scenarios": len(SCENARIOS),
            "counts": {
                g: counts[g] for g in ("PASS", "PASS_FIXED", "PROBLEM", "UNVERIFIED", "N/A")
            },
            "by_scenario": GRADES,
            "certificate_subset": [s for s in SCENARIOS if GRADES[s] != "PROBLEM"],
            "certificate_excluded": [s for s in SCENARIOS if GRADES[s] == "PROBLEM"],
            "full_shop_eligible": False,
        },
    )
    return streams


def learned_noise(old, twin):
    fields = []
    for name in NOISE:

        def get(e, name=name):
            if name.startswith("pp."):
                return e["pp"].get(name[3:])
            return e.get(name)

        if any(get(a) != get(b) for a, b in zip(old, twin, strict=True)):
            fields.append(name)
    # Deltas rename legacy noise dimensions; these names describe the same learned dimensions.
    if "pp.legacy_token" in fields:
        fields.append("pp.order_id")
    if "pp.txn_id" in fields:
        fields.append("pp.capture_id")
    return fields


def build_mutants():
    sample_path = ROOT / (PROOF + "new_sample/payments.php")
    original = sample_path.read_text()
    specifications = [
        (
            1,
            "R03",
            "    $currencyMatches = $capture['amount']['currency_code'] === $order['cu"
            "rrency']; // M1",
            "    $currencyMatches = true; // M1 ignores currency",
            ["HAPPY"],
            ["PASS"],
            None,
        ),
        (
            2,
            "R01",
            "    if ($capture['status'] !== 'COMPLETED') { // M2",
            "    if (false) { // M2 treats pending as paid",
            ["PENDING"],
            ["PROBLEM"],
            None,
        ),
        (
            3,
            "R06",
            "        if ($remote['status'] !== 'APPROVED') throw new RuntimeException("
            "'unapproved'); // M3",
            "        if (false) throw new RuntimeException('unapproved'); // M3",
            ["NOTIFY_FORGED"],
            ["PASS"],
            "Removing the local approval precheck cannot make PayPal capture an unappr"
            "oved order: PayPal's capture endpoint rejects it, and the completion guar"
            "d remains. Conditional equivalence for this one-order CAPTURE sample.",
        ),
        (
            4,
            "R05",
            "    return $store->locked($ref, function () use ($http, $store, $ref) { // M4",
            "    return (function () use ($http, $store, $ref) { // M4 removes lock",
            ["DOUBLE"],
            ["PASS"],
            "Two calls use the same PayPal order and stable request ID; the store upse"
            "rts the same capture ID. With this stand-in's atomic upserts, removing th"
            "is lock changes no economic CMEL fact. Not a general claim that locks are"
            " unnecessary.",
        ),
        (
            5,
            "R10",
            "        $requestId = $ref . ':capture'; // M5: stable across response loss",
            "        $requestId = bin2hex(random_bytes(12)); // M5 changes on retry",
            ["DOUBLE"],
            ["PASS"],
            None,
        ),
        (
            6,
            "R16",
            "        $amountMatches = $capture['amount']['value'] === decimalUSD($orde"
            "r['minor']); // M6",
            "        $amountMatches = (float)$capture['amount']['value'] === (float)$o"
            "rder['minor'] / 100; // M6",
            ["HAPPY"],
            ["PROBLEM"],
            None,
        ),
        (
            7,
            "R12",
            "    $minor = $store->catalogueTotalMinor($ref); // M7: server owns amount"
            "\n    $currency = 'USD';",
            "    $minor = (int)$browser['minor']; // M7 trusts browser\n    $currency ="
            " $browser['currency'];",
            ["HAPPY"],
            ["PROBLEM"],
            None,
        ),
        (
            8,
            "R08",
            "    $verification = $http('POST', '/v1/notifications/verify-webhook-signature', [\n"
            "        'auth_algo' => $headers['paypal-auth-algo'], 'cert_url' => $heade"
            "rs['paypal-cert-url'],\n"
            "        'transmission_id' => $headers['paypal-transmission-id'],\n"
            "        'transmission_sig' => $headers['paypal-transmission-sig'],\n"
            "        'transmission_time' => $headers['paypal-transmission-time'],\n"
            "        'webhook_id' => $webhookId, 'webhook_event' => $event\n    ], []);",
            "    $verification = ['verification_status' => 'SUCCESS']; // M8 bypass",
            ["NOTIFY_FORGED"],
            ["PROBLEM"],
            None,
        ),
        (
            9,
            "R01",
            "    $orderId = $resource['supplementary_data']['related_ids']['order_id']; // M9",
            "    $orderId = $resource['related_resources']['order_id']; // M9 wrong path",
            ["HAPPY"],
            ["UNVERIFIED"],
            None,
        ),
        (
            10,
            "R08",
            "    $headers = array_change_key_case($headers, CASE_LOWER); // M10",
            "    $headers = $headers; // M10 case-sensitive lookup",
            ["NOTIFY_FORGED"],
            ["PASS"],
            None,
        ),
        (
            11,
            "R14",
            "        $store->saveApproval($ref, $remote); // M11: durable before capture",
            "        $GLOBALS['approvals'][$ref] = $remote; // M11 memory only",
            ["HAPPY"],
            ["PASS"],
            None,
        ),
        (
            12,
            "R11",
            "        if ($order['refunded_minor'] >= $order['minor']) throw new Runtim"
            "eException('already refunded'); // M12",
            "        if (false) throw new RuntimeException('already refunded'); // M12",
            ["REFUND_TWICE"],
            ["PASS"],
            "PayPal rejects an independent second full refund; idempotent retries repl"
            "ay the first refund ID. The injected store deduplicates refund IDs and on"
            "ly records COMPLETED responses. Removing this local guard changes no refu"
            "nd sum with those explicit stand-in guarantees.",
        ),
    ]
    entries = []
    for number, rule, before, after, scenarios, grades, equivalent in specifications:
        # Match indentation of the M1/M2 lines without hiding a misplaced mutant.
        before = next(
            (line for line in original.splitlines() if line.strip() == before.strip()), before
        )
        assert original.count(before) == 1, (number, before)
        replacement = original.replace(before, after, 1)
        if number == 4:
            start = replacement.index("function captureOrder")
            end = replacement.index("function refundOrder")
            part = replacement[start:end].replace("    });\n", "    })();\n", 1)
            replacement = replacement[:start] + part + replacement[end:]
        patch = "".join(
            difflib.unified_diff(
                original.splitlines(True),
                replacement.splitlines(True),
                fromfile="a/payments.php",
                tofile="b/payments.php",
                n=3,
            )
        )
        line = original[: original.index(before)].count("\n") + 1
        mutant_id = f"M{number:02}"
        killed = [s for s, g in zip(scenarios, grades, strict=True) if g == "PROBLEM"]
        write(
            PROOF + f"mutants/{mutant_id}.json",
            {
                "id": mutant_id,
                "op": f"M{number}",
                "location": {"file": "new_sample/payments.php", "line": line},
                "patch": patch,
                "rule": rule,
                "equivalent_suspect": bool(equivalent),
                "killed_by": killed,
            },
            "Mutant/1",
        )
        notes = {
            1: "Survives: no cross-currency response in the linked HAPPY run.",
            2: "Killed in the correct sample's pending baseline: skipped status guard "
            "creates paid on pending (R01/R07).",
            5: "Survives: DOUBLE covers two tabs, not a lost capture response; cached "
            "replay hides the random request ID.",
            6: "Killed by the static R16 guard for float money operations, even if thi"
            "s particular 25.00 converts exactly.",
            7: "Killed: browser minor=1,currency=EUR replaces the server's 2500 USD (R12/R17).",
            8: "Killed: unverified forged completion is trusted and can cause paid wit"
            "hout a ledger capture (R01/R08).",
            9: "Survives the mutation score: bad resource path aborts the webhook run,"
            " yielding UNVERIFIED, not PROBLEM. A fail-closed run is not a kill und"
            "er U3.",
            10: "Survives: forged notification remains rejected when header lookup fai"
            "ls; a valid mixed-case notification test is absent.",
            11: "Survives: no restart occurs in HAPPY; a RESTART case would exercise t"
            "he lost durable approval.",
        }
        entries.append(
            {
                "mutant": mutant_id,
                "rule": rule,
                "equivalence": "DROPPED" if number == 3 else "RETAINED",
                "equivalence_reason": equivalent,
                "linked_scenarios": scenarios,
                "baseline_grades": {
                    s: "PASS_FIXED" if s == "REFUND_TWICE" else "PASS" for s in scenarios
                },
                "grades": {
                    s: "PASS_FIXED" if s == "REFUND_TWICE" and g == "PASS" else g
                    for s, g in zip(scenarios, grades, strict=True)
                },
                "killed": bool(killed),
                "reason": (
                    "Survives: DOUBLE queues two approvals but invokes confirmation handlers "
                    "sequentially, so the cached replay hides the removed lock. Retained: "
                    "overlapping handlers can change API observations; full CMEL equivalence "
                    "has not been established."
                    if number == 4
                    else "Survives as PASS_FIXED: the OLD R11 bug remains reported, while the "
                    "idempotent PayPal refund ID and store dedupe prevent a second DB refund. "
                    "Retained: removing the guard can change API REFUND observations, "
                    "so equal money totals do not prove full CMEL equivalence."
                    if number == 12
                    else equivalent or notes[number]
                ),
            }
        )
    total, dropped, killed = (
        len(entries),
        sum(e["equivalence"] == "DROPPED" for e in entries),
        sum(e["killed"] for e in entries),
    )
    write(
        PROOF + "mutants/runs.json",
        {
            "execution": "SYNTHETIC expected run outcomes, not executed PHP/sandbox measurements",
            "baseline": "Independent correct new_sample/payments.php, not the intentio"
            "nally broken NEW PENDING trace. Static R12/R16 checks partici"
            "pate in rule evaluation.",
            "stand_in_setup": {
                "DOUBLE": (
                    "Two approvals are queued, then confirmation handlers run sequentially. "
                    "The second reads the first committed capture. This does not cover an "
                    "overlapping confirmation critical section."
                ),
                "NOTIFY_FORGED": (
                    "Pause after durable approval and before capture. The approved local row "
                    "exists, but PayPal has no completed capture. M08 can trust the forged "
                    "completion only by bypassing signature verification."
                ),
            },
            "equivalence_scope": "Conditional on the explicit HTTP/storage stand-ins i"
            "n new_sample/README.md; reviewed expected equivalent"
            "s, not automatic drops of all suspects. Only M03 is dropped; M04 and M12 "
            "remain in the denominator because full CMEL equivalence is not established.",
            "runs": entries,
            "surviving": [
                e["mutant"] for e in entries if not e["killed"] and e["equivalence"] == "RETAINED"
            ],
        },
    )
    strength = {
        "total": total,
        "equivalent_dropped": dropped,
        "killed": killed,
        "score": killed / (total - dropped),
    }
    write(PROOF + "expected/proof_strength.json", strength, "ProofStrength/1")
    rules = []
    for base in BASE_RULES:
        linked = [e for e in entries if e["rule"] == base.id]
        rules.append(
            {
                "id": base.id,
                "title": base.title,
                "correct_flow": [base.plain_text],
                "counter_examples": ["A run violating: " + base.plain_text],
                "predicate": base.predicate_idea,
                "sources": {
                    "code": ["src/api/create-payment.php:10-24"] if base.id == "R12" else [],
                    "traces": ["synthetic-c4/" + s + ".OLD" for s in SCENARIOS],
                },
                "agreement": "CODE_ONLY" if base.id == "R12" else "TRACE_ONLY",
                "triangle": {
                    "scenarios": sorted({s for e in linked for s in e["linked_scenarios"]}),
                    "mutants": [e["mutant"] for e in linked],
                    "killed": any(e["killed"] for e in linked),
                },
                "severity": base.severity.value,
            }
        )
    rules.append(
        {
            "id": "R17",
            "title": "Only catalogue SKUs contribute server catalogue prices to the total",
            "correct_flow": [
                "Ignore unknown SKUs; sum catalogue price times integer quantity for k"
                "nown SKUs; use SHOP_CURRENCY USD."
            ],
            "counter_examples": ["Use a browser unit price or count an unknown SKU."],
            "predicate": "INTENT.minor = sum(catalogue[sku].minor * int(qty) for sku i"
            "n cart if sku in catalogue)",
            "sources": {
                "code": [
                    "src/api/create-payment.php:10-16",
                    "src/config.php:10",
                    "src/config.php:14-17",
                ],
                "traces": [],
            },
            "agreement": "CODE_ONLY",
            "triangle": {"scenarios": ["HAPPY"], "mutants": ["M07"], "killed": True},
            "severity": "CRITICAL",
        }
    )
    write(PROOF + "contract.json", {"shop_id": "legacy-php-shop", "rules": rules}, "Contract/1")
    return strength


def build_heal():
    cases = {
        "healthy": (100, 90, 100, 99, None),
        "thin": (10, 0, 10, 10, None),
        "worse": (100, 100, 100, 20, None),
        "money_break": (100, 90, 100, 99, "NEW R02 money-rule break"),
        "unverified_notify": (100, 90, 100, 99, "Unverified notification acted on"),
        "slightly_worse": (100, 80, 100, 77, None),
    }
    for name, (no, so, nn, sn, stop) in cases.items():
        events = []
        for path, n, success in (("OLD", no, so), ("NEW", nn, sn)):
            for i in range(n):
                for event in ("ATTEMPT", "APPROVED", "CAPTURED" if i < success else "DECLINED"):
                    stamp = datetime(2026, 11, 2, 10, tzinfo=UTC) + timedelta(seconds=len(events))
                    events.append(
                        {
                            "graft_id": "synthetic-c4",
                            "shop_id": "legacy-php-shop",
                            "path": path,
                            "event": event,
                            "order_ref": f"{name}-{path}-{i:03}",
                            "money": {"minor": 2500, "currency": "USD"},
                            "paypal_ids": {"capture_id": f"FAKE-{path}-{i:03}"}
                            if event == "CAPTURED"
                            else {},
                            "latency_ms": 100,
                            "ts": stamp.isoformat(),
                            "lib_version": "synthetic-c4/1",
                            "signature": "FAKE-SIGNATURE-FOR-TESTS",
                        }
                    )
        write(
            PROOF + f"heal/case_{name}.events.json",
            events,
            "GuardEvent/1[]",
            "Single-stage approved-to-captured traffic",
        )
        result = decision(events, hard_stop=stop)
        write(PROOF + f"heal/case_{name}.expected.json", result, "HealDecision/1")
        safe, worse = probabilities(no, so, nn, sn)
        write(
            PROOF + f"heal/case_{name}.evidence.json",
            {
                "stage_pct": 10,
                "prior_old": [1, 1],
                "prior_new": [1, 1],
                "margin": "1/50",
                "prob_new_not_worse": float(safe),
                "prob_new_worse": float(worse),
                "exact_not_worse": str(safe),
                "exact_worse": str(worse),
                "guard_results": (
                    [
                        {
                            "path": "NEW",
                            "order_ref": f"{name}-NEW-000",
                            "rule": "R02",
                            "expected": {"minor": 2500, "currency": "USD"},
                            "ledger": {"minor": 2499, "currency": "USD"},
                            "hard_stop": stop,
                        }
                    ]
                    if name == "money_break"
                    else [
                        {
                            "path": "NEW",
                            "order_ref": f"{name}-NEW-000",
                            "verification_status": "FAILURE",
                            "acted_on": True,
                            "hard_stop": stop,
                        }
                    ]
                    if name == "unverified_notify"
                    else []
                ),
                "hard_stop": stop,
                "note": "GuardEvent has no rule-result/notification-verification field"
                "s; this sidecar supplies H2's guard evidence. Success counts "
                "alone cannot detect hard stops.",
            },
        )


def certificate_digest(certificate):
    payload = {
        k: v for k, v in certificate.items() if k not in {"signature", "rekor_entry", "ots_proof"}
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def build_remaining(pack, streams, strength):
    cases = []
    for passes, fails in ((0, 0), (1, 0), (0, 1), (3, 2), (10, 0), (20, 5)):
        cases.append(
            {
                "passes": passes,
                "fails": fails,
                "posterior_alpha": passes + 1,
                "posterior_beta": fails + 1,
                "expected_mean": (passes + 1) / (passes + fails + 2),
            }
        )
    write(PROOF + "recipes/confidence_cases.json", {"cases": cases})
    included = [s for s in SCENARIOS if GRADES[s] != "PROBLEM"]
    cert = {
        "cert_id": "SYNTHETIC-SUBSET-FIXTURE-ONLY",
        "shop_id": "legacy-php-shop",
        "repo": REPO,
        "commit_old": COMMIT,
        "commit_new": "FAKE-NEW-COMMIT-FOR-TESTS",
        "branch": "goldgraft/synthetic-c4",
        "issued_at": "2026-11-02T10:00:00Z",
        "results": {
            "scenarios": len(included),
            "pass": 5,
            "pass_fixed": 1,
            "problem": 0,
            "unverified": 1,
            "n_a": 0,
        },
        "proof_strength": {
            "mutants_total": strength["total"],
            **{k: v for k, v in strength.items() if k != "total"},
        },
        "survey": {"recall": 23 / 24, "precision": 23 / 24, "misses_learned": 0},
        "security": {"secrets_found": 0, "injection_attempts_blocked": 0, "deps_blocked": 0},
        "paypal_evidence": [
            {
                "scenario": "HAPPY",
                "order_id": Capture("HAPPY", "NEW").order,
                "capture_id": Capture("HAPPY", "NEW").txn,
                "debug_id": Capture("HAPPY", "NEW").debug,
            }
        ],
        "cost": {"usd": 0, "tokens": 0},
        "time": {"PROVING": 0},
        "ledger_root": "0" * 64,
        "runner_identity": {"workflow": "FAKE-WORKFLOW-FOR-TESTS", "sha": "FAKE-SHA-FOR-TESTS"},
        "signature": "FAKE-SIGNATURE-FOR-TESTS",
        "rekor_entry": "FAKE-REKOR-ENTRY-FOR-TESTS",
    }
    write(
        PROOF + "certificate/valid.json",
        cert,
        "Certificate/1",
        "Schema-valid seven-case subset, hash-binding test only; NOT eligible certification",
    )
    tampered = copy.deepcopy(cert)
    tampered["cost"]["tokens"] = 1
    write(
        PROOF + "certificate/tampered.json",
        tampered,
        "Certificate/1",
        "One numeric leaf changed; structure remains valid, trusted payload hash mismatches",
    )
    write(
        PROOF + "certificate/expected_verify.json",
        {
            "canonicalization": "UTF-8 sorted keys, compact JSON; omit signature, reko"
            "r_entry, ots_proof",
            "trusted_payload_sha256": certificate_digest(cert),
            "covered_scenarios": included,
            "excluded_scenarios": [s for s in SCENARIOS if s not in included],
            "valid": {
                "schema_valid": True,
                "payload_hash_matches": True,
                "signature_verified": False,
                "eligible": False,
            },
            "tampered": {
                "schema_valid": True,
                "payload_hash_matches": False,
                "failed_check": "payload_hash_mismatch",
                "changed_pointer": "/cost/tokens",
                "signature_verified": False,
            },
            "gate_failures": [
                "Two full-shop scenarios are PROBLEM",
                "Mutation strength is below 0.95",
                "Runs are synthetic and have zero proven flake-free repetitions",
                "UNVERIFIED critical ledger evidence",
                "Fake signature, Rekor, runner identity and ledger root",
            ],
            "note": "valid means schema/hash-consistent test vector only. Certificate/"
            "1 cannot encode two PROBLEM results or PARTIAL status; it cannot "
            "represent the full corpus. No actual cryptographic signature veri"
            "fication is claimed.",
        },
    )


def build_vendor_hashes():
    # Keep the pinned upstream tree manifest as input; never derive expected
    # hashes from the files being tested or fetch anything during regeneration.
    path = ROOT / "shops/legacy-php-shop/vendor_hashes.json"
    if not path.exists():
        raise FileNotFoundError("The pinned upstream vendor manifest is required")
    name = str(path.relative_to(ROOT))
    FORMATS[name] = "reference"
    PURPOSES[name] = "Pinned upstream Git blob hashes, checked offline"


def build_index():
    intro = f"""# GoldGraft C4 fixtures

**Synthetic label S:** {SYNTHETIC}

**REAL source label R:** REAL — source vendored byte-for-byte from Cutover commit
`{COMMIT}`; not a recording of payments.

All boundary JSON (including JSON-syntax YAML) is pure: metadata lives in each
INDEX row because `goldgraft_contracts` forbids extra keys. CMEL and GuardEvent
files are arrays: validate each record with `CMEL/1` and `GuardEvent/1` respectively.
`reference` files are labelled reference tables without a registry format, checked
by derived invariants in tests. No invented registry keys or schema changes.

## Evidence conventions and limits

- 24 code-lens touchpoints, counted by (family, operation, file, line), are below.
  Include endpoint definitions AND uses, wrapper, SDK hooks/mount, return/cancel
  routes, IPN handler/postback/gate/log and all four NVP calls. Exclude comment-only
  mentions, branding, CSS selectors, credentials and plain config constants.
  `money_flow` separately covers amounts and storage. `live=false`; no runtime,
  account or site recall is claimed. Mapping IDs are official doc URLs, because
  no versioned RulesHub ID catalogue was supplied.
- `X-GoldGraft-Order-Ref` is recorder metadata for the stable shop order.
  `X-GoldGraft-Ledger: order|capture|refund|absence` tags after-run request/response
  pairs. Only responses with actual capture/refund facts emit `PAYPAL_LEDGER`
  CMEL copies. `absence` succeeds with zero events. `X-GoldGraft-Parent-Capture`
  links refund ledger reads to the original capture. These annotations are not
  PayPal response fields and are not transmitted to PayPal.
- CMEL `raw_ref` is a relative JSON pointer, resolved from this shop's proof folder.
  Noise is only timing/correlation IDs plus run/variant/ref metadata. Declared
  deltas rename ID vocabulary, not amounts, currencies, kinds or counts. An
  approval callback maps by 02 R3 (the 01 table explicitly names only v6 approval).
  Error responses remain raw evidence: 01 defines no general ERROR mapping row.
  D_LEDGER_READ explicitly permits the order/capture lookup fan-out, coalescing
  only identical ledger IDs/status/money. Repeated unchanged DB status observations
  are bookkeeping, not additional paid transitions; raw changes still face rules.
- Ledger, API, notification and DB views are witnesses to the same economic
  capture/refund, not extra charges. Deduplicate economic IDs within each witness;
  never sum the API and its ledger copy as two refunds. Refund runs include a
  completed-capture ledger checkpoint before the refund and a final refunded
  capture plus refund ledger. `REFUND` has positive minor money and normalized
  status REFUNDED; NVP `REFUNDSTATUS=instant` is documented (not `Completed`).
  The public GetTransactionDetails page documents AMT but does not supply a
  concrete signed refund-transaction example. The synthetic refund ledger uses
  -25.00 and maps its magnitude; no observed signed-ledger convention is claimed.
- Refund bookkeeping retains order `status=paid`, records `refunded_minor`, and
  therefore maps to SHOP_PAID as a status observation; it is not another paid
  transition. This is synthetic state, not the vendor's flat-file schema.
  A failed second refund emits no REFUND. REFUND_TWICE's R11 is visible in the
  referenced raw DB `refunded_minor=5000` versus ledger refund 2500. A Judge
  restricted to CMEL alone cannot see that false DB total. Resolve provenance;
  a future DB-refund mapping/field clarification is needed for a CMEL-only judge.
- PENDING intentionally has NEW R01 AND R07 violations; there is no completed
  notification while the capture is pending. The ledger lookup is the R13 path.
  DECLINE and NOTIFY_FORGED use successful absence reads: old token lookup via
  GetExpressCheckoutDetails, new GET order with no captures. No transaction ID
  exists to pass to GetTransactionDetails in those paths. DECLINE uses the
  documented PaymentActionFailed checkout state, forged uses NotInitiated.
- OLD twins change only IDs/correlation/timestamps and mandatory run metadata.
  Synthetic checkout tokens and transaction IDs are fake object identifiers;
  credentials/Authorization are `[REDACTED]`. PayPal decimal strings are wire
  values; all canonical money and guard amounts are strict integer minor units.
- The pinned source unconditionally marks NVP success paid and guards refunds.
  The requested OLD PENDING/REFUND_TWICE examples are synthetic specification
  cases, not execution claims. IPN in the source only appends a log; synthetic
  streams model a notification-to-state path for R08/R09.
- The PHP sample is independently authored, injectable pseudoinfrastructure with
  real documented endpoint shapes. Mutant runs are expected hand-written outcomes,
  not executed PHP tests. No PHP CLI is on PATH here. Conditional equivalents and
  survivors are explicit in runs.json; assurance flake_free_runs is zero.
- Heal priors are Beta(1,1), margin 1/50, n_min=30, one stage at 10%. Events count
  unique APPROVED orders; CAPTURED among them are successes. GuardEvent/1 cannot
  carry rule/verification results; `.evidence.json` supplies separate hard-stop
  evidence. Exact probabilities are stored there; expected HealDecision/1 stores
  its supported prob_new_not_worse field. Fraction integration is deterministic.
- `certificate/valid.json` is schema-valid ONLY for the seven non-PROBLEM cases;
  summary includes all nine. It is NOT a valid full-shop certificate. Proof score
  4/11, critical UNVERIFIED evidence, zero execution assurance and fake signatures
  fail U5. The tamper check demonstrates canonical payload hash binding, not real
  Sigstore/Rekor verification. No full-corpus Certificate/1 can encode problem=2.
- `docker-compose.yml` and `buyer.spec.ts` are C5-owned start/driver paths.
  If present from the parallel C5 job, they are indexed but not authored, modified
  or executed by C4. Their presence does not establish runtime assurance.

## Touchpoint answer key (24)

| ID | Family | Operation | Location |
|---|---|---|---|
"""
    pack = json.loads((ROOT / "shops/legacy-php-shop/goldgraft-shop.yaml").read_text())
    rows = []
    for tp in pack["answer_key"]["touchpoints"]:
        rows.append(
            f"| {tp['id']} | {tp['family']} | {tp['operation']} | "
            f"{tp['location']['file']}:{tp['location']['line']} |"
        )
    intro += "\n".join(rows) + "\n\n## Money-flow answer key (19 location references)\n\n"
    intro += "| Step | Count | Locations |\n|---|---|---|\n"
    for step, locations in pack["answer_key"]["money_flow"].items():
        locations_text = ", ".join(f"{v['file']}:{v['line']}" for v in locations) or "none"
        intro += f"| {step} | {len(locations)} | {locations_text} |\n"
    intro += "\n## Verified PayPal sources\n\n"
    for url in SOURCES:
        intro += f"- [{url.removeprefix(DOC)}]({url})\n"
    intro += "\n## File inventory\n\n"
    intro += "| File | Format | What | Used by | Label | _source |\n|---|---|---|---|---|---|\n"
    files = sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and not any(part in {"__pycache__", ".pytest_cache", ".ruff_cache"} for part in p.parts)
        and p.name != "PLAN.md"
    )
    if ROOT / "INDEX.md" not in files:
        files.append(ROOT / "INDEX.md")
        files.sort()
    for file in files:
        name = str(file.relative_to(ROOT))
        real = name.startswith("shops/legacy-php-shop/src/") or name.endswith("LICENSE.cutover")
        schema = (
            "LedgerEntry/1 JSONL"
            if name == "events/demo_graft_events.jsonl"
            else FORMATS.get(name, "—")
        )
        purpose = PURPOSES.get(
            name,
            "Offline fixture reference/test tool"
            if name.endswith(".py")
            else "Fixture provenance and usage notes",
        )
        source = (
            UPSTREAM
            if real
            else "[PayPal docs]("
            + ORDERS
            + "), [NVP reference]("
            + NVP
            + "), [IPN]("
            + NVP
            + "ipn/IPNandPDTVariables/), [Payments]("
            + PAYMENTS
            + "), [Webhooks]("
            + WEBHOOKS
            + "), [v6]("
            + SDK
            + "); [method sources](#verified-paypal-sources); design 01–05"
        )
        consumer = (
            "shops, agents (Surveyor)"
            if name.startswith("shops/") or "/survey/" in name
            else "proof, agents, offline plugtests"
        )
        if name in {
            "shops/legacy-php-shop/docker-compose.yml",
            "shops/legacy-php-shop/buyer.spec.ts",
        }:
            purpose = "Parallel C5 start/driver artifact, not authored or executed by C4"
        if name == "events/demo_graft_events.jsonl":
            purpose = "Existing C2 fake demo ledger stream (not authored by C4)"
            consumer = "foundation, backend, web"
            source = (
                "[C2 demo](../scripts/demo_graft.py); "
                "[PayPal sandbox](https://developer.paypal.com/tools/sandbox/)"
            )
        if name.endswith("vendor_hashes.json"):
            source = f"[Pinned Git tree]({REPO}/tree/{COMMIT})"
        label = "R — REAL source" if real else "S — SYNTHETIC"
        intro += f"| [{name}]({name}) | {schema} | {purpose} | {consumer} | {label} | {source} |\n"
    (ROOT / "INDEX.md").write_text(intro)


def main():
    build_vendor_hashes()
    pack = build_shop()
    streams = build_scenarios()
    strength = build_mutants()
    build_heal()
    build_remaining(pack, streams, strength)
    build_index()
    print(
        f"Built {len(FORMATS)} JSON/YAML fixtures; proof score "
        f"{strength['killed']}/{strength['total'] - strength['equivalent_dropped']}"
    )


if __name__ == "__main__":
    main()
