"""Replay the offline proof smoke test, or run one real PayPal sandbox payment.

Live mode is a separately authorised sandbox check (play money). It needs
sandbox REST credentials and the explicit ``--authorize-sandbox-payment`` flag.
The flow is the real Orders v2 sequence:

1. create an order (buyer-approval flow, no shipping)
2. the sandbox buyer approves it in a browser (the script prints the link)
3. capture the approved order
4. re-fetch the capture from PayPal
5. refund the capture in full
6. re-fetch the refund from PayPal

Every id, status and timing in the saved ``RawCapture/1`` comes from PayPal's
actual responses. Nothing is defaulted or invented: a missing id or an
unexpected status stops the run. No webhook is claimed: receiving one needs a
registered public listener, which this script does not have.
"""

import argparse
import json
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from goldgraft_contracts.common import Variant
from goldgraft_contracts.runner import Direction, RawCapture, RawExchange

from integration.offline import run_offline
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import REST_SANDBOX, PaymentBroker

DEFAULT_ENV_FILE = Path.home() / ".config/goldgraft/paypal-sandbox.env"
DEFAULT_STATE_DIR = Path.home() / "reports/goldgraft-live-20261112/paypal-sandbox"
ALLOWED_ACTIONS = {"create", "capture", "refund", "get_order", "get_capture", "get_refund"}


def load_credentials(env_file: Path) -> dict[str, str]:
    """Reads PAYPAL_CLIENT_ID/PAYPAL_CLIENT_SECRET from a private env file."""
    values: dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key in {"PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"}:
            values[key] = value.strip()
    if not (values.get("PAYPAL_CLIENT_ID") and values.get("PAYPAL_CLIENT_SECRET")):
        raise ValueError(f"{env_file} lacks PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET")
    return values


def _scoped_authority(graft_id: str, value: str, currency: str):
    """Operator-approved scope for this one run: its graft, its amount, its actions."""

    def authorize(graft: str, operation: str, payload: dict[str, Any], _secret_ref: str) -> bool:
        if graft != graft_id or operation not in ALLOWED_ACTIONS:
            return False
        amounts = [payload.get("amount")] + [
            unit.get("amount") for unit in payload.get("purchase_units", []) or []
        ]
        for amount in amounts:
            if amount is not None and amount != {"currency_code": currency, "value": value}:
                return False
        return True

    return authorize


def _link(data: dict[str, Any], *rels: str) -> str:
    for link in data.get("links", []) or []:
        if link.get("rel") in rels and link.get("href"):
            return link["href"]
    raise RuntimeError(f"PayPal response has no {'/'.join(rels)} link")


def _require(value: Any, what: str) -> Any:
    if not value:
        raise RuntimeError(f"PayPal response has no {what}; stopping without inventing one")
    return value


def run_sandbox_payment(
    *,
    dry_run: bool = False,
    state_dir: Path = Path(".goldgraft/sandbox-dry-run"),
    authorize_payment: bool = False,
    credentials: dict[str, str] | None = None,
    show_approval: Callable[[str], None] | None = None,
    approval_timeout_s: float = 600.0,
    poll_s: float = 5.0,
    value: str = "10.00",
    currency: str = "USD",
    transport: Any | None = None,
) -> dict:
    if dry_run:
        report = run_offline(state_dir)
        return {
            "live": False,
            "evidence_class": report["evidence_class"],
            "provider_calls": report["provider_calls"],
            "fixture_verdicts": {
                verdict["scenario_id"]: verdict["grade"]
                for verdict in report["fixtures"]["verdicts"]
            },
            "simulated_payment_proof": report["payment_recorder"]["proof_status"],
        }

    if not (authorize_payment and credentials):
        raise ValueError(
            "Live sandbox execution requires a qualified payment transport, PayPal sandbox "
            "credentials (--env-file) and the explicit --authorize-sandbox-payment flag; "
            "or run with --dry-run for offline fixture replay."
        )

    run_uuid = uuid.uuid4().hex[:12]
    graft_id = f"graft-live-{run_uuid}"
    state_dir.mkdir(parents=True, exist_ok=True)
    custody = CustodyBroker()
    secret_ref = custody.store_credentials(
        f"sandbox-{run_uuid}",
        {
            "paypal_client_id": credentials["PAYPAL_CLIENT_ID"],
            "paypal_client_secret": credentials["PAYPAL_CLIENT_SECRET"],
        },
    ).to_uri()
    broker = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        database=str(state_dir / f"journal-{run_uuid}.sqlite"),
        authorize=_scoped_authority(graft_id, value, currency),
        **({"transport": transport} if transport is not None else {}),
    )
    started = time.monotonic()
    exchanges: list[RawExchange] = []

    def record(method: str, url: str, request: Any, response) -> dict[str, Any]:
        t_ms = int((time.monotonic() - started) * 1000)
        headers = {"authorization": "[REDACTED]", "content-type": "application/json"}
        exchanges.append(
            RawExchange(
                seq=len(exchanges) + 1,
                t_ms=t_ms,
                direction=Direction.SHOP_TO_PAYPAL,
                method=method,
                url=url,
                headers=headers,
                body_json=request,
            )
        )
        exchanges.append(
            RawExchange(
                seq=len(exchanges) + 1,
                t_ms=t_ms,
                direction=Direction.PAYPAL_TO_SHOP,
                method=method,
                url=url,
                headers={"content-type": "application/json"},
                body_json=response.data,
                status=response.status_code,
            )
        )
        return response.data

    amount = {"currency_code": currency, "value": value}
    try:
        order_body = {
            "intent": "CAPTURE",
            "purchase_units": [{"reference_id": f"ref-{run_uuid}", "amount": amount}],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "PAY_NOW",
                        "return_url": "https://example.com/goldgraft/return",
                        "cancel_url": "https://example.com/goldgraft/cancel",
                    }
                }
            },
        }
        created = record(
            "POST",
            f"{REST_SANDBOX}/v2/checkout/orders",
            order_body,
            broker.execute_orders_v2(
                "create",
                order_body,
                secret_ref=secret_ref,
                idempotency_key=f"create-{run_uuid}",
                graft_id=graft_id,
            ),
        )
        order_id = _require(created.get("id"), "order id")
        approve_url = _link(created, "payer-action", "approve")
        (show_approval or (lambda url: print(f"Approve as the sandbox buyer: {url}", flush=True)))(
            approve_url
        )

        deadline = time.monotonic() + approval_timeout_s
        polls = 0
        while True:
            order = broker.refetch_order(order_id, secret_ref=secret_ref, graft_id=graft_id)
            polls += 1
            if order.data.get("status") == "APPROVED":
                record("GET", f"{REST_SANDBOX}/v2/checkout/orders/{order_id}", None, order)
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Order {order_id} not approved within {approval_timeout_s:.0f}s "
                    f"(last status {order.data.get('status')!r}); nothing was captured"
                )
            time.sleep(poll_s)

        captured = record(
            "POST",
            f"{REST_SANDBOX}/v2/checkout/orders/{order_id}/capture",
            {},
            broker.execute_orders_v2(
                "capture",
                {"order_id": order_id},
                secret_ref=secret_ref,
                idempotency_key=f"capture-{run_uuid}",
                graft_id=graft_id,
            ),
        )
        units = captured.get("purchase_units") or [{}]
        captures = (units[0].get("payments") or {}).get("captures") or [{}]
        capture_id = _require(captures[0].get("id"), "capture id")

        capture_now = record(
            "GET",
            f"{REST_SANDBOX}/v2/payments/captures/{capture_id}",
            None,
            broker.refetch_capture(capture_id, secret_ref=secret_ref, graft_id=graft_id),
        )
        refund_body = {"capture_id": capture_id, "amount": amount}
        refunded = record(
            "POST",
            f"{REST_SANDBOX}/v2/payments/captures/{capture_id}/refund",
            {"amount": amount},
            broker.execute_orders_v2(
                "refund",
                refund_body,
                secret_ref=secret_ref,
                idempotency_key=f"refund-{run_uuid}",
                graft_id=graft_id,
            ),
        )
        refund_id = _require(refunded.get("id"), "refund id")
        refund_now = record(
            "GET",
            f"{REST_SANDBOX}/v2/payments/refunds/{refund_id}",
            None,
            broker.refetch_refund(refund_id, secret_ref=secret_ref, graft_id=graft_id),
        )

        raw_capture = RawCapture(
            graft_id=graft_id,
            run_id=f"run-{run_uuid}",
            variant=Variant.NEW,
            scenario_id="LIVE_PAYPAL_SANDBOX_PAYMENT",
            exchanges=exchanges,
        )
        capture_file = state_dir / f"live-sandbox-{order_id}.json"
        capture_file.write_text(raw_capture.model_dump_json(indent=2, by_alias=True))
        report = {
            "live": True,
            "evidence_class": "real_sandbox",
            "graft_id": graft_id,
            "order_id": order_id,
            "order_status_after_approval": "APPROVED",
            "approval_polls": polls,
            "capture_id": capture_id,
            "capture_status_at_capture": captures[0].get("status"),
            "capture_status_refetched": capture_now.get("status"),
            "capture_amount_refetched": capture_now.get("amount"),
            "refund_id": refund_id,
            "refund_status_at_refund": refunded.get("status"),
            "refund_status_refetched": refund_now.get("status"),
            "refund_amount_refetched": refund_now.get("amount"),
            "exchanges": len(exchanges),
            "raw_capture_file": str(capture_file),
            "holds": [
                "webhook: no registered public listener, so no PayPal notification is claimed",
                "merchant shop: this is GoldGraft's own sandbox app, not a merchant's shop",
            ],
        }
        (state_dir / f"report-{order_id}.json").write_text(json.dumps(report, indent=2) + "\n")
        return report
    finally:
        broker.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Replay without provider calls")
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument(
        "--authorize-sandbox-payment",
        action="store_true",
        help="Explicitly authorise one real sandbox create/capture/refund (play money)",
    )
    parser.add_argument("--approval-timeout", type=float, default=600.0)
    args = parser.parse_args()
    try:
        if args.dry_run:
            result = run_sandbox_payment(
                dry_run=True, state_dir=args.state_dir or Path(".goldgraft/sandbox-dry-run")
            )
        else:
            result = run_sandbox_payment(
                state_dir=args.state_dir or DEFAULT_STATE_DIR,
                authorize_payment=args.authorize_sandbox_payment,
                credentials=load_credentials(args.env_file)
                if args.authorize_sandbox_payment
                else None,
                approval_timeout_s=args.approval_timeout,
            )
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
