"""Actual persistent case intake; provider/model qualification remains separate."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api_routes import PLAN5_ROUTES
from goldgraft_contracts.connection_control import ConnectionCase, CreateCase
from goldgraft_foundation.ledger import Ledger
from sqlalchemy import select

from pieces.backend.connection.service import CaseService, Principal, ServiceError
from pieces.backend.service_api import create_service_app

NOW = datetime(2026, 11, 11, 18, 0, tzinfo=UTC)
ORIGIN = "https://goldgraft.example"


def actor(name="owner", tenant="tenant-a"):
    return Principal(
        actor_id=name,
        tenant_id=tenant,
        expires_at=NOW + timedelta(hours=1),
        csrf_token="offline-csrf-example",
    )


@pytest.fixture
def service(tmp_path):
    return CaseService(Ledger(f"sqlite:///{tmp_path / 'cases.sqlite'}"), clock=lambda: NOW)


@pytest.fixture
def client(service):
    identities = {
        "owner": actor(),
        "other": actor("other"),
        "foreign": actor("owner", "tenant-b"),
        "expired": Principal(
            actor_id="owner", tenant_id="tenant-a", expires_at=NOW, csrf_token="expired"
        ),
    }
    return TestClient(
        create_service_app(
            service,
            authenticate=lambda request: identities.get(request.cookies.get("session")),
            allowed_origins={ORIGIN},
            max_json_bytes=128 * 1024,
        )
    )


def headers(key="case-one"):
    return {"Origin": ORIGIN, "X-CSRF-Token": "offline-csrf-example", "Idempotency-Key": key}


def create(client, *, session="owner", key="case-one", url="https://merchant.example/shop"):
    return client.post(
        "/v2/connection-cases",
        json={"shop_url": url},
        headers={**headers(key), "Cookie": f"session={session}"},
    )


def read(client, path, session="owner", **kwargs):
    return client.get(path, headers={"Cookie": f"session={session}"}, **kwargs)


def test_all_v2_routes_registered_without_demo_data(client):
    actual = {(m, r.path) for r in client.app.routes for m in getattr(r, "methods", ())}
    assert {(r.method, r.path) for r in PLAN5_ROUTES} <= actual
    response = read(client, "/v2/connection-cases")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}
    assert client.get("/grafts/demo-1").status_code == 404


@pytest.mark.parametrize("session", ["missing", "expired"])
def test_untrusted_headers_cannot_establish_identity(client, session):
    response = client.post(
        "/v2/connection-cases",
        json={"shop_url": "https://merchant.example"},
        headers={**headers(), "Cookie": f"session={session}", "X-Actor-Id": "owner"},
    )
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


@pytest.mark.parametrize("bad", [{"Origin": "https://attacker.example"}, {"X-CSRF-Token": "bad"}])
def test_cross_origin_or_bad_csrf_cannot_create_cases(client, bad):
    response = client.post(
        "/v2/connection-cases",
        json={"shop_url": "https://merchant.example"},
        headers={**headers(), **bad, "Cookie": "session=owner"},
    )
    assert response.status_code == 403
    assert read(client, "/v2/connection-cases").json()["items"] == []


def test_create_retry_conflict_and_restart_share_committed_truth(client, service):
    first = create(client)
    assert first.status_code == 201
    case = ConnectionCase.model_validate(first.json())
    assert case.requester_id == "owner" and case.tenant_id == "tenant-a"
    assert case.status == "setup_needed" and case.binding_refs == [] and case.graph_ref is None
    assert create(client).json() == first.json()
    assert create(client, url="https://different.example").status_code == 409
    reopened = CaseService(service.ledger, clock=lambda: NOW)
    assert reopened.get_case(actor(), case.case_id) == case
    assert service.ledger.verify_chain(case.case_id).ok
    events = reopened.events(actor(), case.case_id)
    assert len(events) == 1 and events[0].sequence == events[0].state_version == 1


def test_simultaneous_same_key_creates_only_one_case(service):
    def submit(_):
        return service.create_case(
            actor(), CreateCase(shop_url="https://merchant.example"), "concurrent"
        ).case_id

    with ThreadPoolExecutor(max_workers=6) as pool:
        ids = list(pool.map(submit, range(12)))
    assert len(set(ids)) == 1
    assert len(service.list_cases(actor(), limit=50).items) == 1
    assert len(service.events(actor(), ids[0])) == 1


@pytest.mark.parametrize("session", ["other", "foreign"])
def test_case_view_and_events_do_not_leak_across_actor_or_tenant(client, session):
    case = create(client).json()
    for suffix in ("", "/view", "/events"):
        response = read(client, f"/v2/connection-cases/{case['case_id']}{suffix}", session)
        assert response.status_code == 404
        assert case["shop_url"] not in response.text
    assert read(client, "/v2/connection-cases", session).json()["items"] == []


def test_case_view_preserves_missing_processing_and_readiness(client):
    case = create(client).json()
    response = read(client, f"/v2/connection-cases/{case['case_id']}/view")
    view = response.json()
    assert response.status_code == 200
    assert view["evidence_class"] == "component_offline"
    assert view["readiness"] is view["processing"] is view["lifecycle"] is None
    assert view["required_actions"] and view["last_event_seq"] == 1


def test_event_replay_and_future_cursor_are_explicit(client):
    case = create(client).json()
    path = f"/v2/connection-cases/{case['case_id']}/events"
    first = read(client, path)
    assert first.headers["content-type"].startswith("text/event-stream")
    assert first.text.count("event: case_changed") == 1 and "id: 1\n" in first.text
    again = client.get(path, headers={"Cookie": "session=owner", "Last-Event-ID": "1"})
    assert again.text == ""
    assert read(client, path + "?after=100").status_code == 409


def test_body_cannot_select_ownership_and_errors_do_not_echo_inputs(client):
    response = client.post(
        "/v2/connection-cases",
        json={"shop_url": "https://merchant.example", "tenant_id": "private-input-marker"},
        headers={**headers(), "Cookie": "session=owner"},
    )
    assert response.status_code == 422
    assert "private-input-marker" not in response.text


def test_body_limits_and_missing_idempotency_are_not_silent(client):
    response = client.post(
        "/v2/connection-cases",
        json={"shop_url": "https://merchant.example"},
        headers={
            "Origin": ORIGIN,
            "X-CSRF-Token": "offline-csrf-example",
            "Cookie": "session=owner",
        },
    )
    assert response.status_code == 400
    assert (
        client.post(
            "/v2/connection-cases",
            content=b"x" * 200_000,
            headers={**headers(), "Cookie": "session=owner"},
        ).status_code
        == 413
    )


def test_start_does_not_fabricate_readiness_or_accepted_work(client):
    case = create(client).json()
    response = client.post(
        f"/v2/connection-cases/{case['case_id']}/actions",
        json={"action_id": "a", "readiness_id": "r", "readiness_digest": "0" * 64},
        headers={**headers("start"), "Cookie": "session=owner"},
    )
    assert response.status_code == 503
    assert response.json()["reason_code"] == "CAPABILITY_NOT_QUALIFIED"


def test_tampered_ledger_is_not_a_valid_case_view(service):
    case = service.create_case(actor(), CreateCase(shop_url="https://merchant.example"), "k")
    table = service.ledger.entries
    with service.ledger.engine.begin() as db:
        row = (
            db.execute(select(table).where(table.c.graft_id == case.case_id, table.c.seq == 1))
            .mappings()
            .one()
        )
        body = json.loads(row["body"])
        body["payload"]["shop_url"] = "https://substituted.example"
        db.execute(
            table.update()
            .where(table.c.graft_id == case.case_id, table.c.seq == 1)
            .values(body=json.dumps(body))
        )
    with pytest.raises(ServiceError, match="INTEGRITY_FAILURE"):
        service.get_case(actor(), case.case_id)


def test_pagination_cursor_is_actor_bound(client):
    for number in range(3):
        assert create(client, key=f"page-{number}").status_code == 201
    first = read(client, "/v2/connection-cases?limit=1").json()
    second = read(client, f"/v2/connection-cases?limit=1&cursor={first['next_cursor']}").json()
    assert first["items"][0]["case_id"] != second["items"][0]["case_id"]
    assert (
        read(client, f"/v2/connection-cases?cursor={first['next_cursor']}", "other").status_code
        == 400
    )


def test_cached_receipt_tampering_does_not_bypass_the_ledger(service):
    from pieces.backend.connection.service import requests

    service.create_case(actor(), CreateCase(shop_url="https://merchant.example"), "k")
    with service.ledger.engine.begin() as db:
        row = db.execute(select(requests)).mappings().one()
        cached = json.loads(row["response"])
        cached["shop_url"] = "https://substituted.example"
        db.execute(requests.update().values(response=json.dumps(cached)))
    with pytest.raises(ServiceError, match="INTEGRITY_FAILURE"):
        service.create_case(actor(), CreateCase(shop_url="https://merchant.example"), "k")


def test_valid_chain_cannot_rebind_case_identity(service):
    from pieces.backend.connection.service import PRODUCER

    case = service.create_case(actor(), CreateCase(shop_url="https://merchant.example"), "k")
    changed = case.model_copy(update={"case_id": "different-case"})
    service.ledger.append(
        case.case_id,
        "ARTIFACT",
        PRODUCER,
        "ConnectionCase/1",
        payload=changed.model_dump(mode="json"),
    )
    assert service.ledger.verify_chain(case.case_id).ok
    with pytest.raises(ServiceError, match="INTEGRITY_FAILURE"):
        service.get_case(actor(), case.case_id)


@pytest.mark.parametrize("query", ["limit=1&limit=2", "limit=9" * 1000])
def test_ambiguous_or_oversized_query_is_rejected(client, query):
    assert read(client, "/v2/connection-cases?" + query).status_code == 422


def test_identity_provider_failure_is_closed_without_echoing_it(service):
    def unavailable(_request):
        raise RuntimeError("private-identity-provider-detail")

    client = TestClient(create_service_app(service, authenticate=unavailable))
    response = client.get("/v2/connection-cases")
    assert response.status_code == 503
    assert "private-identity-provider-detail" not in response.text


def test_stream_rechecks_identity_before_releasing_an_event(service):
    case = service.create_case(actor(), CreateCase(shop_url="https://merchant.example"), "k")
    calls = []

    def current(_request):
        calls.append(1)
        return actor() if len(calls) == 1 else None

    client = TestClient(create_service_app(service, authenticate=current))
    response = client.get(f"/v2/connection-cases/{case.case_id}/events")
    assert response.status_code == 200 and response.text == "" and len(calls) == 2


def test_draft_claim_requires_both_current_session_and_separate_capability(client):
    response = client.post(
        "/v2/connection-drafts",
        json={"shop_url": "https://merchant.example"},
        headers={**headers("draft"), "Cookie": "session=owner"},
    )
    assert response.status_code == 201
    draft = response.json()
    cookie_name = "gg_draft_" + draft["draft_id"]
    capability = response.cookies.get(cookie_name)
    assert capability and "httponly" in response.headers["set-cookie"].lower()
    claim = f"/v2/connection-drafts/{draft['draft_id']}/claim"
    body = {"continuation_ref": draft["continuation_ref"]}
    denied = client.post(claim, json=body, headers={**headers("claim"), "Cookie": "session=owner"})
    assert denied.status_code == 403
    valid_headers = {**headers("claim"), "Cookie": f"session=owner; {cookie_name}={capability}"}
    accepted = client.post(claim, json=body, headers=valid_headers)
    assert accepted.status_code == 200 and accepted.json()["status"] == "setup_needed"
    assert client.post(claim, json=body, headers=valid_headers).json() == accepted.json()
    other_headers = {
        **headers("claim-other"),
        "Cookie": f"session=other; {cookie_name}={capability}",
    }
    assert client.post(claim, json=body, headers=other_headers).status_code == 403
    assert len(read(client, "/v2/connection-cases").json()["items"]) == 1


def test_draft_expiry_and_restart_do_not_create_a_second_case(service):
    from goldgraft_contracts.connection_control import ClaimDraft, CreateDraft

    draft, capability = service.create_draft(
        actor(), CreateDraft(shop_url="https://merchant.example"), "draft"
    )
    reopened = CaseService(service.ledger, clock=lambda: NOW + timedelta(minutes=31))
    with pytest.raises(ServiceError, match="DRAFT_CAPABILITY_REQUIRED"):
        reopened.claim_draft(
            actor(),
            draft.draft_id,
            ClaimDraft(continuation_ref=draft.continuation_ref),
            "claim",
            capability,
        )
    assert service.list_cases(actor()).items == []


def test_draft_retry_and_conflict_preserve_the_original_draft(service):
    from goldgraft_contracts.connection_control import CreateDraft

    original, capability = service.create_draft(
        actor(), CreateDraft(shop_url="https://merchant.example"), "draft"
    )
    again, new_capability = service.create_draft(
        actor(), CreateDraft(shop_url="https://merchant.example"), "draft"
    )
    assert again == original and new_capability is None and len(capability) == 32
    with pytest.raises(ServiceError, match="IDEMPOTENCY_CONFLICT"):
        service.create_draft(actor(), CreateDraft(shop_url="https://different.example"), "draft")


def test_case_creation_receipt_cannot_be_repointed_to_another_owned_case(service):
    from pieces.backend.connection.service import requests

    request = CreateCase(shop_url="https://merchant.example")
    service.create_case(actor(), request, "first")
    other = service.create_case(actor(), request, "second")
    with service.ledger.engine.begin() as db:
        db.execute(
            requests.update()
            .where(requests.c.key == "first")
            .values(response=other.model_dump_json())
        )
    with pytest.raises(ServiceError, match="INTEGRITY_FAILURE"):
        service.create_case(actor(), request, "first")
