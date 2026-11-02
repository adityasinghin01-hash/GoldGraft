"""Stand-in API honours the contract in goldgraft_contracts.api_routes (no sockets)."""

import json
import logging
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api_routes import ROUTES
from goldgraft_fakes import data
from goldgraft_fakes.api import create_app

ROOT = Path(__file__).resolve().parents[2]
PP_HEADERS = {"PAYPAL-TRANSMISSION-ID": "t-1", "PAYPAL-TRANSMISSION-TIME": "2026-11-02T10:00:00Z",
              "PAYPAL-TRANSMISSION-SIG": "sig", "PAYPAL-CERT-URL": "https://example.test/cert",
              "PAYPAL-AUTH-ALGO": "SHA256withRSA"}
GH_HEADERS = {"X-Hub-Signature-256": "sha256=00", "X-GitHub-Event": "pull_request",
              "X-GitHub-Delivery": "d-1"}
SECRETS = {"paypal_client_id": "CLIENT-ID-VALUE-123", "paypal_client_secret": "SECRET-VALUE-456",
           "webhook_id": "WH-789", "nvp_user": "nvp-user", "nvp_password": "NVP-PASSWORD-000",
           "nvp_signature": "NVP-SIGNATURE-111"}
BODIES = {
    "probe": {"url": "https://github.com/example/old-shop"},
    "create_shop": {"repo": "https://github.com/example/old-shop"},
    "connect_shop": SECRETS,
    "start_graft": {},
    "inject_fault": {"mutant_op": "M1"},
    "guard_event": data.example("GuardEvent"),
    "orchard_ask": {"question": "Which shops still take WPS money?"},
    "paypal_webhook": {"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    "github_webhook": {"action": "closed"},
}
PATH_VALUES = {"graft_id": data.GRAFT_ID, "shop_id": data.SHOP_ID, "cert_id": data.CERT_ID,
               "run_id": "run-1"}


@pytest.fixture
def client():
    return TestClient(create_app())


def call(client, route, key="k-1", body=None, headers=None):
    path = re.sub(r"{(\w+)}", lambda m: PATH_VALUES[m.group(1)], route.path)
    params = {"scenario": "happy"} if route.query else {}
    if route.sse:
        params["speed"] = 0
    hdrs = dict(headers or {})
    if route.needs_idempotency_key:
        hdrs["Idempotency-Key"] = key
    if route.name == "paypal_webhook":
        hdrs |= PP_HEADERS
    if route.name == "github_webhook":
        hdrs |= GH_HEADERS
    if route.method == "GET":
        return client.get(path, params=params, headers=hdrs)
    return client.post(path, params=params, headers=hdrs,
                       json=body if body is not None else BODIES.get(route.name, {}))


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r.name)
def test_every_route_answers_with_its_response_model(client, route):
    resp = call(client, route)
    assert resp.status_code == 200, resp.text
    if resp.headers["content-type"].startswith("text/event-stream"):
        frames = [f for f in resp.text.split("\n\n") if f.strip()]
        assert frames
        payload = json.loads(frames[0].split("data: ", 1)[1])
        if route.name == "graft_events":
            route.response.model_validate(payload)
        return
    route.response.model_validate(resp.json())


def test_route_table_matches_design_07():
    text = (ROOT / "docs/design/07_FRONTEND_API.md").read_text()
    api_part = text.split("## API (control plane)")[1]
    design = set()
    for line in api_part.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 4 or not cells[2].startswith("`"):
            continue
        methods = cells[1].split("/")
        for chunk in re.findall(r"`([^`]+)`", cells[2]):
            design.update((m, chunk) for m in methods)
    ours = {(r.method, r.path) for r in ROUTES}

    def norm(path):
        return re.sub(r"{\w+}", "{}", path)

    ours_norm = {(m, norm(p)) for m, p in ours}
    for method, path in design:
        if path.startswith("/"):
            candidates = {(method, norm(path))}
        else:  # "/scenarios" style suffixes under /grafts/{id}
            candidates = {(method, norm("/grafts/{id}" + path))}
        if not candidates & ours_norm:
            # GET/POST pairs in 07 list the read and the write path together
            assert any(norm(p).endswith(norm(path)) for _, p in ours), (method, path)
    assert ("GET", "/learning-curve") in ours  # named on screen S8


def test_idempotency_replay_and_conflict(client):
    route = next(r for r in ROUTES if r.name == "create_shop")
    first = call(client, route, key="same")
    again = call(client, route, key="same")
    assert first.json() == again.json()
    clash = call(client, route, key="same", body={"repo": "https://github.com/other/shop"})
    assert clash.status_code == 409
    assert clash.headers["content-type"].startswith("application/problem+json")
    missing = client.post("/shops", json={"repo": "https://github.com/x/y"})
    assert missing.status_code == 422
    assert missing.headers["content-type"].startswith("application/problem+json")


def test_connect_never_returns_or_logs_secrets(client, caplog):
    caplog.set_level(logging.DEBUG)
    route = next(r for r in ROUTES if r.name == "connect_shop")
    resp = call(client, route)
    assert resp.status_code == 200
    assert resp.json()["secrets_ref"].startswith("doppler://")
    blob = resp.text + "\n".join(r.getMessage() for r in caplog.records)
    for value in SECRETS.values():
        assert value not in blob


def test_graft_feed_is_ordered_and_resumes(client):
    resp = client.get(f"/grafts/{data.GRAFT_ID}/events", params={"speed": 0})
    ids = [int(line[4:]) for line in resp.text.splitlines() if line.startswith("id: ")]
    assert ids == sorted(ids) and ids[0] == 1 and len(ids) == len(data.demo_events())
    resumed = client.get(f"/grafts/{data.GRAFT_ID}/events", params={"speed": 0},
                         headers={"Last-Event-ID": "30"})
    rids = [int(line[4:]) for line in resumed.text.splitlines() if line.startswith("id: ")]
    assert rids[0] == 31 and rids[-1] == ids[-1]


def test_heal_json_by_default_and_stream_on_request(client):
    snap = client.get(f"/heal/{data.GRAFT_ID}")
    assert snap.headers["content-type"].startswith("application/json")
    stream = client.get(f"/heal/{data.GRAFT_ID}", params={"speed": 0},
                        headers={"Accept": "text/event-stream"})
    assert stream.headers["content-type"].startswith("text/event-stream")


def test_certificate_verify_green_then_red_when_tampered(client):
    good = client.post(f"/certificates/{data.CERT_ID}/verify").json()
    assert good["ok"] is True
    bad = client.post(f"/certificates/{data.TAMPERED_CERT_ID}/verify").json()
    assert bad["ok"] is False
    failed = {c["name"] for c in bad["checks"] if not c["ok"]}
    assert "SIGNATURE" in failed
    assert any("changed after signing" in c["detail"] for c in bad["checks"])


def test_webhooks_need_signature_headers_and_dedupe(client):
    path = f"/pp/webhook/{data.GRAFT_ID}"
    assert client.post(path, json={}).status_code == 400
    first = client.post(path, json={}, headers=PP_HEADERS).json()
    second = client.post(path, json={}, headers=PP_HEADERS).json()
    assert first == {"accepted": True, "deduplicated": False}
    assert second["deduplicated"] is True


def test_unknown_ids_are_problems(client):
    resp = client.get("/grafts/nope")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    cmel = client.get(f"/grafts/{data.GRAFT_ID}/cmel", params={"scenario": "zzz"})
    assert cmel.status_code == 404


def test_openapi_export_is_stable_and_committed():
    from importlib import import_module
    first = create_app().openapi()
    second = create_app().openapi()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    spec = json.loads((ROOT / "contracts/api/openapi.json").read_text())
    assert set(spec["paths"]) == set(first["paths"])
    assert import_module("goldgraft_contracts.api_routes")
