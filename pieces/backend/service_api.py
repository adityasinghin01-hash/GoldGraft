"""V2 service boundary over actual case storage; unqualified capabilities fail closed.

The host supplies verified identity, never caller-selected actor/tenant headers.
Legacy seeded/demo routes are deliberately absent from this application.
"""

import json
import re
from collections.abc import Callable
from secrets import compare_digest
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from goldgraft_contracts.api_routes import PLAN5_ROUTES
from goldgraft_contracts.connection_control import P5Problem
from goldgraft_contracts.plan5_common import Id, reject_secret
from pydantic import TypeAdapter, ValidationError

from .connection.service import CaseService, Principal, ServiceError


def problem(error):
    value = P5Problem(
        type="about:blank",
        title="Request could not be completed",
        status=error.status,
        detail=None,
        instance=None,
        code=error.code,
        request_id="request-" + uuid4().hex,
        reason_code=error.code,
        retry="safe_read" if error.status == 503 else "never",
        recovery_action=None,
        evidence_refs=[],
    )
    return JSONResponse(
        value.model_dump(mode="json"),
        status_code=error.status,
        media_type="application/problem+json",
        headers={"Cache-Control": "private, no-store"},
    )


async def json_body(request, model, maximum):
    raw = bytearray()
    async for part in request.stream():
        if len(raw) + len(part) > maximum:
            raise ServiceError("REQUEST_TOO_LARGE", 413)
        raw.extend(part)
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise ServiceError("UNSUPPORTED_MEDIA_TYPE", 415)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("nonfinite JSON")

    try:
        body = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
        return model.model_validate(body)
    except (ValueError, TypeError, RecursionError):
        raise ServiceError("INVALID_BODY", 422) from None


def create_service_app(
    service: CaseService,
    *,
    authenticate: Callable[[Request], Principal | None] | None = None,
    allowed_origins=(),
    max_json_bytes=8 * 1024 * 1024,
    work_control=None,
):
    if type(max_json_bytes) is not int or not 1 <= max_json_bytes <= 8 * 1024 * 1024:
        raise ValueError("INVALID service request limit")
    origins = frozenset(allowed_origins)
    if "*" in origins:
        raise ValueError("Wildcard credential origin forbidden")
    app = FastAPI(title="GoldGraft case service", version="2")
    app.state.case_service = service
    if work_control is not None and work_control.cases is not service:
        raise ValueError("Work control must share the same case service")
    app.state.implemented_service_routes = frozenset(
        {
            "create_draft",
            "claim_draft",
            "create_case",
            "list_cases",
            "get_case",
            "case_view",
            "case_events",
        }
    )
    if work_control is not None:
        app.state.implemented_service_routes |= {
            "create_action_intent",
            "start_work",
            "action_status",
            "cancel_work",
            "worker_operation",
        }
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-CSRF-Token", "Last-Event-ID"],
    )

    def identity(request, route):
        try:
            principal = authenticate(request) if authenticate else None
        except Exception:
            raise ServiceError("IDENTITY_UNAVAILABLE", 503) from None
        service.check_principal(principal)
        expected = {"service"} if route.auth == "service" else {"session"}
        if route.auth == "draft":
            expected = {"draft", "session"}
        if principal.kind not in expected:
            raise ServiceError("AUTHORITY_REQUIRED", 403)
        if route.csrf and (
            request.headers.get("origin") not in origins
            or not compare_digest(request.headers.get("x-csrf-token", ""), principal.csrf_token)
        ):
            raise ServiceError("CSRF_DENIED", 403)
        return principal

    def endpoint(route):
        async def handle(request: Request):
            try:
                if route.auth == "public_projection":
                    raise ServiceError("PUBLIC_PROOF_UNAVAILABLE", 404)
                principal = identity(request, route)
                key = None
                if route.needs_idempotency_key:
                    try:
                        key = TypeAdapter(Id).validate_python(
                            request.headers.get("idempotency-key")
                        )
                        reject_secret(key)
                    except (ValidationError, ValueError):
                        raise ServiceError("IDEMPOTENCY_KEY_REQUIRED", 400) from None
                params = request.path_params
                try:
                    for value in params.values():
                        TypeAdapter(Id).validate_python(value)
                except ValidationError:
                    raise ServiceError("INVALID_PATH", 422) from None
                if "case_id" in params:
                    service.get_case(principal, params["case_id"])
                pairs = request.query_params.multi_items()
                if len(pairs) != len({key for key, _ in pairs}) or any(
                    k not in route.query or len(v) > 256 for k, v in pairs
                ):
                    raise ServiceError("INVALID_QUERY", 422)
                body = None
                new_capability = None
                if route.request is not None:
                    if route.request_media != "application/json":
                        raise ServiceError("CAPABILITY_NOT_QUALIFIED", 503)
                    body = await json_body(request, route.request, max_json_bytes)
                if route.name == "create_draft":
                    result, new_capability = service.create_draft(principal, body, key)
                elif route.name == "claim_draft":
                    value = request.cookies.get("gg_draft_" + params["draft_id"], "")
                    if not re.fullmatch(r"[a-f0-9]{64}", value):
                        raise ServiceError("DRAFT_CAPABILITY_REQUIRED", 403)
                    result = service.claim_draft(
                        principal, params["draft_id"], body, key, bytes.fromhex(value)
                    )
                elif route.name == "create_case":
                    result = service.create_case(principal, body, key)
                elif route.name == "list_cases":
                    try:
                        limit = int(request.query_params.get("limit", "20"))
                    except ValueError:
                        raise ServiceError("INVALID_QUERY", 422) from None
                    result = service.list_cases(
                        principal, cursor=request.query_params.get("cursor"), limit=limit
                    )
                elif route.name == "get_case":
                    result = service.get_case(principal, params["case_id"])
                elif route.name == "case_view":
                    result = service.view(principal, params["case_id"])
                elif work_control is not None and route.name == "create_action_intent":
                    result = work_control.create_intent(principal, params["case_id"], body, key)
                elif work_control is not None and route.name == "start_work":
                    result = work_control.start(principal, params["case_id"], body, key)
                elif work_control is not None and route.name == "action_status":
                    result = work_control.status(principal, params["case_id"], params["action_id"])
                elif work_control is not None and route.name == "cancel_work":
                    result = work_control.cancel(
                        principal, params["case_id"], params["action_id"], body.cancel_id
                    )
                elif work_control is not None and route.name == "worker_operation":
                    result = work_control.operation(principal, body)
                elif route.name == "case_events":
                    value = request.query_params.get(
                        "after", request.headers.get("last-event-id", "0")
                    )
                    if len(value) > 20 or not value.isdecimal():
                        raise ServiceError("INVALID_EVENT_CURSOR", 422)
                    values = service.events(principal, params["case_id"], after=int(value))

                    async def stream():
                        for event in values:
                            try:
                                current = identity(request, route)
                                if (current.actor_id, current.tenant_id) != (
                                    principal.actor_id,
                                    principal.tenant_id,
                                ):
                                    return
                                service.get_case(current, params["case_id"])
                            except ServiceError:
                                return
                            yield (
                                f"id: {event.sequence}\nevent: {event.kind}\n"
                                f"data: {event.model_dump_json()}\n\n"
                            )

                    return StreamingResponse(
                        stream(),
                        media_type="text/event-stream",
                        headers={"Cache-Control": "private, no-store"},
                    )
                else:
                    raise ServiceError("CAPABILITY_NOT_QUALIFIED", 503)
                response = JSONResponse(
                    result.model_dump(mode="json"),
                    status_code=route.success_status,
                    headers={
                        "Cache-Control": "private, no-store",
                        "X-GoldGraft-Evidence-Class": service.evidence_class,
                    },
                )
                if new_capability is not None:
                    response.set_cookie(
                        "gg_draft_" + result.draft_id,
                        new_capability.hex(),
                        max_age=1800,
                        secure=True,
                        httponly=True,
                        samesite="strict",
                        path="/v2/connection-drafts",
                    )
                return response
            except ServiceError as exc:
                return problem(exc)

        return handle

    for route in PLAN5_ROUTES:
        app.add_api_route(route.path, endpoint(route), methods=[route.method], name=route.name)
    return app
