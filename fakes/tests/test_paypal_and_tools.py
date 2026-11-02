"""FAKE PayPal sandbox behaves like PayPal's docs say; tool list matches design 06."""

import base64
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.tools import AGENTS, TOOLS, SideEffect, tools_for
from goldgraft_fakes.paypal import FakePayPal

ROOT = Path(__file__).resolve().parents[2]


class Clock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


@pytest.fixture
def pp():
    clock = Clock()
    fake = FakePayPal(clock=clock)
    fake.test_clock = clock
    return fake, TestClient(fake.app)


def nvp(client, **fields):
    resp = client.post("/nvp", content=urlencode(fields),
                       headers={"Content-Type": "application/x-www-form-urlencoded"})
    return dict(parse_qsl(resp.text))


def test_nvp_express_checkout_ipn_refund(pp):
    fake, c = pp
    token = nvp(c, METHOD="SetExpressCheckout", PAYMENTREQUEST_0_AMT="19.99",
                PAYMENTREQUEST_0_CURRENCYCODE="USD")["TOKEN"]
    assert token.startswith("EC-")
    assert nvp(c, METHOD="GetExpressCheckoutDetails", TOKEN=token)["PAYERID"]
    paid = nvp(c, METHOD="DoExpressCheckoutPayment", TOKEN=token, PAYERID="FAKEPAYER01")
    assert paid["ACK"] == "Success" and paid["PAYMENTINFO_0_PAYMENTSTATUS"] == "Completed"
    assert paid["PAYMENTINFO_0_AMT"] == "19.99"
    again = nvp(c, METHOD="DoExpressCheckoutPayment", TOKEN=token, PAYERID="FAKEPAYER01")
    assert again["ACK"] == "Failure" and again["L_ERRORCODE0"] == "10415"
    txn = paid["PAYMENTINFO_0_TRANSACTIONID"]
    ipn = fake.ipn_for(txn)
    ok = c.post("/cgi-bin/webscr", content=urlencode({"cmd": "_notify-validate", **ipn}))
    assert ok.text == "VERIFIED"
    forged = c.post("/cgi-bin/webscr", content=urlencode(
        {"cmd": "_notify-validate", **ipn, "mc_gross": "0.01"}))
    assert forged.text == "INVALID"
    assert nvp(c, METHOD="RefundTransaction", TRANSACTIONID=txn, REFUNDTYPE="Full")[
        "GROSSREFUNDAMT"] == "19.99"
    second = nvp(c, METHOD="RefundTransaction", TRANSACTIONID=txn, REFUNDTYPE="Full")
    assert second["ACK"] == "Failure" and second["L_ERRORCODE0"] == "10009"
    assert nvp(c, METHOD="GetTransactionDetails", TRANSACTIONID=txn)["PAYMENTSTATUS"] == \
        "Refunded"


def test_nvp_pending_is_fake_only_hook(pp):
    _, c = pp
    token = nvp(c, METHOD="SetExpressCheckout", PAYMENTREQUEST_0_AMT="5.00",
                PAYMENTREQUEST_0_CURRENCYCODE="USD")["TOKEN"]
    paid = nvp(c, METHOD="DoExpressCheckoutPayment", TOKEN=token, PAYERID="X",
               X_FAKE_PAYMENTSTATUS="Pending")
    assert paid["PAYMENTINFO_0_PAYMENTSTATUS"] == "Pending"


def _order(c, value="19.99", currency="USD", **headers):
    return c.post("/v2/checkout/orders", headers=headers, json={
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": currency, "value": value}}]})


def test_orders_v2_happy_refund_and_double_capture(pp):
    fake, c = pp
    auth = base64.b64encode(b"id:secret").decode()
    assert c.post("/v1/oauth2/token", headers={"Authorization": f"Basic {auth}"}).json()[
        "token_type"] == "Bearer"
    order = _order(c).json()
    assert order["status"] == "CREATED"
    assert c.post(f"/v2/checkout/orders/{order['id']}/capture").json()["details"][0][
        "issue"] == "ORDER_NOT_APPROVED"
    c.post(f"/fake/approve/{order['id']}")
    done = c.post(f"/v2/checkout/orders/{order['id']}/capture")
    assert done.status_code == 201
    cap = done.json()["purchase_units"][0]["payments"]["captures"][0]
    assert cap["status"] == "COMPLETED" and cap["amount"]["value"] == "19.99"
    twice = c.post(f"/v2/checkout/orders/{order['id']}/capture")
    assert twice.json()["details"][0]["issue"] == "ORDER_ALREADY_CAPTURED"
    assert c.post(f"/v2/payments/captures/{cap['id']}/refund").status_code == 201
    again = c.post(f"/v2/payments/captures/{cap['id']}/refund")
    assert again.json()["details"][0]["issue"] == "CAPTURE_FULLY_REFUNDED"
    headers, body = fake.webhook_for(cap["id"])
    good = c.post("/v1/notifications/verify-webhook-signature", json={
        "transmission_id": headers["PAYPAL-TRANSMISSION-ID"],
        "transmission_sig": headers["PAYPAL-TRANSMISSION-SIG"], "webhook_event": body})
    assert good.json()["verification_status"] == "SUCCESS"
    bad = c.post("/v1/notifications/verify-webhook-signature", json={
        "transmission_id": headers["PAYPAL-TRANSMISSION-ID"], "transmission_sig": "forged"})
    assert bad.json()["verification_status"] == "FAILURE"
    assert body["resource"]["supplementary_data"]["related_ids"]["order_id"] == order["id"]


def test_mock_responses_and_request_id(pp):
    _, c = pp
    first = _order(c, **{"PayPal-Request-Id": "req-1"}).json()
    assert _order(c, value="1.00", **{"PayPal-Request-Id": "req-1"}).json()["id"] == first["id"]
    c.post(f"/fake/approve/{first['id']}")
    declined = c.post(f"/v2/checkout/orders/{first['id']}/capture", headers={
        "PayPal-Mock-Response": json.dumps({"mock_application_codes": "INSTRUMENT_DECLINED"})})
    assert declined.status_code == 422
    assert declined.json()["details"][0]["issue"] == "INSTRUMENT_DECLINED"
    pending = c.post(f"/v2/checkout/orders/{first['id']}/capture", headers={
        "PayPal-Mock-Response": json.dumps({"mock_application_codes": "FAKE_CAPTURE_PENDING"})})
    cap = pending.json()["purchase_units"][0]["payments"]["captures"][0]
    assert cap["status"] == "PENDING"


def test_rate_limit_51st_request_blocks_for_five_minutes(pp):
    fake, c = pp
    for _ in range(50):
        assert c.get("/v2/checkout/orders/none").status_code == 404
    blocked = c.get("/v2/checkout/orders/none")
    assert blocked.status_code == 429 and blocked.json()["name"] == "RATE_LIMIT_REACHED"
    fake.test_clock.now += 299
    assert c.get("/v2/checkout/orders/none").status_code == 429
    fake.test_clock.now += 2
    assert c.get("/v2/checkout/orders/none").status_code == 404


def test_tool_list_matches_design_06():
    text = (ROOT / "docs/design/06_AGENTS_SERVICES.md").read_text()
    design: dict[str, set[str]] = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 4 and cells[1].startswith("**") and "." in cells[3]:
            agent = cells[1].strip("*")
            names = {re.sub(r"\(.*?\)", "", t).strip() for t in cells[3].split(",")}
            design[agent] = {n for n in names if n}
    assert set(design) == set(AGENTS)
    for agent, names in design.items():
        assert {t.name for t in tools_for(agent)} >= names, agent
    assert {t.name for t in TOOLS} == set().union(*design.values())


def test_privileged_tools_are_narrow():
    privileged = {t.name: t.allowed_agents for t in TOOLS if t.side_effect is SideEffect.PRIVILEGED}
    assert privileged == {"repo.write": ("Grafter",), "heal.pause": ("Healer",),
                          "heal.request_cutback": ("Healer",), "agent.halt": ("Sentinel",)}
