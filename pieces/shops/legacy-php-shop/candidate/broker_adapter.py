"""Private in-process PayPalClient.rest -> current PaymentBroker operation adapter.

Source-inspected against 525c22de61b504f67ea633e5aac95b8bed0fda64.
No socket, credentials, authority grant or PHP/Python RPC is implemented here.
Ordinary tests use a scripted counterpart. Real broker qualification is separate.
"""

import re
from copy import deepcopy


class AdapterHold(ValueError):
    pass


class BrokerRestAdapter:
    def __init__(self, broker, *, graft_id, secret_ref, evidence_mode="scripted"):
        if evidence_mode not in ("scripted", "real_sandbox"):
            raise AdapterHold("explicit_evidence_mode_required")
        wanted = "synthetic" if evidence_mode == "scripted" else "sandbox"
        if getattr(broker, "mode", None) != wanted:
            raise AdapterHold("broker_mode_mismatch")
        if (
            not isinstance(graft_id, str)
            or not graft_id
            or not isinstance(secret_ref, str)
            or not secret_ref.startswith("doppler://")
        ):
            raise AdapterHold("bound_backend_references_required")
        self._broker, self._graft, self._secret = broker, graft_id, secret_ref
        self._evidence_mode = evidence_mode
        self._broker_mode = wanted

    def rest(self, method, path, body=None, headers=None):
        if getattr(self._broker, "mode", None) != self._broker_mode:
            raise AdapterHold("broker_mode_changed")
        if not isinstance(method, str) or not isinstance(path, str):
            raise AdapterHold("invalid_request")
        h = dict(headers or {})
        if h.keys() - {"PayPal-Request-Id", "Prefer"}:
            raise AdapterHold("unsupported_shop_header")
        if "Prefer" in h and h["Prefer"] != "return=representation":
            raise AdapterHold("unsupported_preference")
        # The current typed broker does not forward Prefer. The candidate must
        # tolerate minimal replies and GET the resource for its business checks.
        key = h.get("PayPal-Request-Id")
        if method == "POST" and (
            not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,38}", key)
        ):
            raise AdapterHold("stable_mutation_identity_required")
        if method == "GET" and (body is not None or h):
            raise AdapterHold("read_only_request_has_mutation_fields")
        if method == "POST" and path == "/v2/checkout/orders":
            if (
                not isinstance(body, dict)
                or body.get("intent") != "CAPTURE"
                or set(body) != {"intent", "purchase_units"}
            ):
                raise AdapterHold("one_time_capture_body_required")
            units = body["purchase_units"]
            if not isinstance(units, list) or len(units) != 1 or not isinstance(units[0], dict):
                raise AdapterHold("one_purchase_unit_required")
            money = units[0].get("amount")
            if not valid_money(money):
                raise AdapterHold("usd_string_amount_required")
            action, payload = "create", deepcopy(body)
        else:
            match = re.fullmatch(
                r"/v2/(checkout/orders|payments/captures|payments/refunds)/([A-Za-z0-9-]{1,64})(/capture|/refund)?",
                path,
            )
            if not match:
                raise AdapterHold("unsupported_payment_route")
            family, resource, suffix = match.groups()
            if method == "GET" and suffix is None:
                action, field = {
                    "checkout/orders": ("get_order", "order_id"),
                    "payments/captures": ("get_capture", "capture_id"),
                    "payments/refunds": ("get_refund", "refund_id"),
                }[family]
                payload = {field: resource}
            elif (
                method == "POST"
                and family == "checkout/orders"
                and suffix == "/capture"
                and body == {}
            ):
                action, payload = "capture", {"order_id": resource}
            elif method == "POST" and family == "payments/captures" and suffix == "/refund":
                if not isinstance(body, dict) or set(body) != {"amount"}:
                    raise AdapterHold("exact_refund_body_required")
                amount = body["amount"]
                if not valid_money(amount):
                    raise AdapterHold("usd_refund_required")
                action, payload = "refund", {"capture_id": resource, **deepcopy(body)}
            else:
                raise AdapterHold("unsupported_payment_operation")
        result = self._broker.execute_orders_v2(
            action,
            payload,
            secret_ref=self._secret,
            idempotency_key=key if method == "POST" else None,
            graft_id=self._graft,
        )
        if (
            getattr(result, "evidence_class", None) != self._evidence_mode
            or getattr(result, "simulated", None) is not (self._evidence_mode == "scripted")
            or getattr(result, "outcome", None) != "ok"
            or not isinstance(getattr(result, "data", None), dict)
            or type(getattr(result, "status_code", None)) is not int
        ):
            raise AdapterHold("broker_response_not_qualified_for_selected_mode")
        # Raw mapping is preserved; no missing IDs, amounts or statuses defaulted.
        return result.status_code, deepcopy(result.data)


def valid_money(money):
    return (
        isinstance(money, dict)
        and set(money) == {"currency_code", "value"}
        and money["currency_code"] == "USD"
        and isinstance(money["value"], str)
        and re.fullmatch(r"(0|[1-9][0-9]{0,6})\.[0-9]{2}", money["value"]) is not None
        and money["value"] != "0.00"
    )
