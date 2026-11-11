"""Route contracts must describe exact browser/service authority and transport."""

import json
from pathlib import Path

import pytest
from goldgraft_contracts import api_routes

ROOT = Path(__file__).resolve().parents[2]


def test_v2_routes_exist_separately_from_legacy():
    assert hasattr(api_routes, "PLAN5_ROUTES"), "new namespace absent"
    routes = api_routes.PLAN5_ROUTES
    assert len({(r.method, r.path) for r in routes}) == len(routes) == 23
    assert all(r.path.startswith("/v2/") for r in routes)
    assert all(not r.path.startswith("/v2/") for r in api_routes.ROUTES)


def test_route_security_success_and_upload_transport():
    assert hasattr(api_routes, "plan5_route"), "v2 lookup absent"
    start = api_routes.plan5_route("start_work")
    assert start.success_status == 202 and start.auth == "session"
    assert start.csrf and start.needs_idempotency_key
    worker = api_routes.plan5_route("worker_operation")
    assert worker.auth == "service" and not worker.csrf
    chunk = api_routes.plan5_route("upload_chunk")
    assert chunk.request_media == "multipart/form-data"
    claim = api_routes.plan5_route("claim_draft")
    assert claim.auth == "session_and_draft" and claim.csrf
    assert api_routes.plan5_route("case_events").sse


def test_openapi_exact_paths_security_and_errors():
    spec = json.loads((ROOT / "contracts/api/openapi.json").read_text())
    assert "/v2/connection-cases/{case_id}/actions" in spec["paths"]
    start = spec["paths"]["/v2/connection-cases/{case_id}/actions"]["post"]
    assert "202" in start["responses"] and "200" not in start["responses"]
    assert "412" in start["responses"] and "409" in start["responses"]
    assert "application/problem+json" in start["responses"]["412"]["content"]
    assert start["security"] == [{"caseSession": []}]
    worker = spec["paths"]["/v2/worker-operations"]["post"]
    assert worker["security"] == [{"serviceIdentity": []}]
    path = "/v2/connection-cases/{case_id}/source-uploads/{upload_id}/chunks"
    body = spec["paths"][path]["post"]["requestBody"]["content"]["multipart/form-data"]
    assert body["schema"]["properties"]["data"]["format"] == "binary"
    assert body["encoding"]["metadata"]["contentType"] == "application/json"
    events = spec["paths"]["/v2/connection-cases/{case_id}/events"]["get"]
    assert "text/event-stream" in events["responses"]["200"]["content"]
    assert {p["name"] for p in events["parameters"]} >= {"after", "Last-Event-ID"}


@pytest.mark.parametrize("name", ["start_graft", "connect_shop", "inject_fault", "orchard_ask"])
def test_legacy_routes_denied_in_new_service(name):
    assert hasattr(api_routes, "service_route"), "service admission boundary absent"
    with pytest.raises(ValueError, match="legacy"):
        api_routes.service_route(name, mode="service")
    assert api_routes.service_route(name, mode="legacy_demo") == api_routes.route(name)
