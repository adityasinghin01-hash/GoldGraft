"""Plug-in test for the backend API (owner: Aditya Gupta).

GOLDGRAFT_API_APP=pieces.backend.app:app uv run pytest plugtests/test_backend_api.py
(the attribute may be a FastAPI app or a zero-argument factory). Without the variable
it runs against the stand-in API. No sockets: FastAPI's TestClient.
"""

import logging
import re

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api_routes import ROUTES, route

from .conftest import load

SECRETS = {"paypal_client_id": "PLUG-CLIENT-ID-1", "paypal_client_secret": "PLUG-SECRET-2",
           "webhook_id": "PLUG-WH-3", "nvp_user": "plug-user", "nvp_password": "PLUG-PWD-4",
           "nvp_signature": "PLUG-SIG-5"}
PROBLEM = "application/problem+json"


@pytest.fixture(scope="module")
def app():
    obj, _ = load("GOLDGRAFT_API_APP", "goldgraft_fakes.api:create_app")
    return obj if hasattr(obj, "router") else obj()


@pytest.fixture
def client(app):
    return TestClient(app)


def is_problem(resp):
    return resp.status_code >= 400 and resp.headers["content-type"].startswith(PROBLEM)


def test_every_contract_route_is_served(app):
    served = {(m, r.path) for r in app.routes for m in getattr(r, "methods", ())}
    missing = [(x.method, x.path) for x in ROUTES if (x.method, x.path) not in served]
    assert not missing, f"routes missing from the backend: {missing}"


@pytest.fixture
def graft(client):
    shop = client.post("/shops", json={"repo": "https://github.com/example/plug-shop"},
                       headers={"Idempotency-Key": "plug-shop"})
    assert shop.status_code == 200, shop.text
    shop_id = route("create_shop").response.model_validate(shop.json()).shop_id
    started = client.post(f"/shops/{shop_id}/graft", json={},
                          headers={"Idempotency-Key": "plug-graft"})
    assert started.status_code == 200, started.text
    return shop_id, route("start_graft").response.model_validate(started.json()).graft_id


def test_writes_need_idempotency_key_and_replay(client):
    body = {"repo": "https://github.com/example/key-shop"}
    assert is_problem(client.post("/shops", json=body))
    first = client.post("/shops", json=body, headers={"Idempotency-Key": "k"})
    again = client.post("/shops", json=body, headers={"Idempotency-Key": "k"})
    assert first.json() == again.json()
    clash = client.post("/shops", json={"repo": "https://github.com/example/other"},
                        headers={"Idempotency-Key": "k"})
    assert clash.status_code == 409 and is_problem(clash)


def test_connect_keeps_secrets_out(client, graft, caplog):
    caplog.set_level(logging.DEBUG)
    shop_id, _ = graft
    resp = client.post(f"/shops/{shop_id}/connect", json=SECRETS,
                       headers={"Idempotency-Key": "plug-connect"})
    assert resp.status_code == 200, resp.text
    conn = route("connect_shop").response.model_validate(resp.json())
    assert conn.secrets_ref.startswith("doppler://")
    seen = resp.text + "\n".join(r.getMessage() for r in caplog.records)
    for value in SECRETS.values():
        assert value not in seen


def test_graft_reads_are_contract_shaped(client, graft):
    _, graft_id = graft
    for r in ROUTES:
        if r.method != "GET" or "{graft_id}" not in r.path or r.sse:
            continue
        path = r.path.replace("{graft_id}", graft_id)
        params = {"scenario": "happy"} if r.query else {}
        resp = client.get(path, params=params)
        if resp.status_code == 200:
            r.response.model_validate(resp.json())
        else:  # artifact not produced yet is allowed, but only as a problem document
            assert resp.status_code == 404 and is_problem(resp), (r.name, resp.text)


def test_live_feeds_stream(client, graft):
    _, graft_id = graft
    resp = client.get(f"/grafts/{graft_id}/events", params={"speed": 0},
                      headers={"Accept": "text/event-stream"})
    assert resp.headers["content-type"].startswith("text/event-stream")


def test_unknown_ids_are_problems(client):
    assert is_problem(client.get("/grafts/does-not-exist"))
    assert is_problem(client.get("/certificates/does-not-exist"))


def test_webhooks_check_headers_and_dedupe(client, graft):
    _, graft_id = graft
    pp = route("paypal_webhook")
    path = pp.path.replace("{graft_id}", graft_id)
    assert is_problem(client.post(path, json={}))
    headers = {h: f"plug-{i}" for i, h in enumerate(pp.signature_headers)}
    first = client.post(path, json={"event_type": "X"}, headers=headers)
    second = client.post(path, json={"event_type": "X"}, headers=headers)
    if first.status_code == 200:  # a real backend may reject our fake signature (4xx problem)
        assert second.json()["deduplicated"] is True
    else:
        assert is_problem(first)


def test_route_paths_use_named_parameters():
    for r in ROUTES:
        assert not re.search(r"{\s*}", r.path)
