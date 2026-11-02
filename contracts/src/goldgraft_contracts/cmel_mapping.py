"""Design 01 §3 mapping data; alternatives expand to one row per CMEL kind."""

from .money import Kind, MappingRow

CMEL_MAPPING: list[MappingRow] = [
    MappingRow(source=source, signal_fields=fields, cmel_kind=kind, notes=notes)
    for source, fields, kind, notes in [
        (
            "WPS form POST to cgi-bin/webscr",
            ["amount", "amount_n", "currency_code", "invoice", "custom"],
            Kind.INTENT,
            "",
        ),
        (
            "NVP SetExpressCheckout",
            ["PAYMENTREQUEST_0_AMT", "PAYMENTREQUEST_0_CURRENCYCODE", "TOKEN"],
            Kind.INTENT,
            "pp.legacy_token",
        ),
        (
            "NVP DoExpressCheckoutPayment",
            [
                "PAYMENTINFO_0_TRANSACTIONID",
                "PAYMENTINFO_0_AMT",
                "PAYMENTINFO_0_CURRENCYCODE",
                "PAYMENTINFO_0_PAYMENTSTATUS",
            ],
            Kind.CAPTURE,
            "Completed→COMPLETED, Pending→PENDING",
        ),
        ("NVP DoDirectPayment", ["TRANSACTIONID", "AMT", "ACK"], Kind.CAPTURE, ""),
        ("NVP RefundTransaction", ["REFUNDTRANSACTIONID", "GROSSREFUNDAMT"], Kind.REFUND, ""),
        ("NVP CreateRecurringPaymentsProfile", ["PROFILEID"], Kind.RECUR_SETUP, ""),
        (
            "IPN POST",
            ["txn_type", "payment_status", "mc_gross", "mc_currency", "txn_id"],
            Kind.NOTIFY,
            "",
        ),
        ("IPN postback _notify-validate", ["VERIFIED"], Kind.NOTIFY_VERIFIED, "VERIFIED response"),
        ("IPN postback _notify-validate", ["INVALID"], Kind.NOTIFY_REJECTED, "INVALID response"),
        (
            "REST POST /v2/checkout/orders",
            ["id", "purchase_units[0].amount"],
            Kind.INTENT,
            "pp.order_id",
        ),
        ("v6 session onApprove", ["orderId"], Kind.APPROVE, ""),
        (
            "REST capture",
            ["captures[0].id", "captures[0].amount", "captures[0].status"],
            Kind.CAPTURE,
            "",
        ),
        ("REST refund", ["id", "amount", "status"], Kind.REFUND, ""),
        (
            "Webhook PAYMENT.CAPTURE.COMPLETED",
            ["resource.id", "supplementary_data.related_ids.order_id", "amount"],
            Kind.NOTIFY,
            "",
        ),
        ("verify-webhook-signature", ["SUCCESS"], Kind.NOTIFY_VERIFIED, "SUCCESS response"),
        ("verify-webhook-signature", ["FAILURE"], Kind.NOTIFY_REJECTED, "FAILURE response"),
        ("Shop DB write", ["order status"], Kind.SHOP_PAID, "paid"),
        ("Shop DB write", ["order status"], Kind.SHOP_PENDING, "pending"),
        ("Shop DB write", ["order status"], Kind.SHOP_UNPAID, "unpaid"),
        (
            "PayPal ledger read (after run)",
            ["GET order", "GET capture", "GET transaction"],
            Kind.CAPTURE,
            "PAYPAL_LEDGER source copy",
        ),
        (
            "PayPal ledger read (after run)",
            ["GET refund", "GET transaction"],
            Kind.REFUND,
            "PAYPAL_LEDGER source copy",
        ),
    ]
]
MAPPING_ROWS = CMEL_MAPPING
