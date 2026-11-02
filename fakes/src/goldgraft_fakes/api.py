"""Stand-in control-plane API. Serves the exact contract in goldgraft_contracts.api_routes
from sample data, so the 12 screens (and the switch libraries) work before the real
backend exists.  Run:  uv run python -m goldgraft_fakes.api --port 8700
"""

import argparse
import asyncio
import hashlib
import inspect
import json
import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from goldgraft_contracts.api_routes import ROUTES, Route

from . import data

log = logging.getLogger("goldgraft.fake_api")
PROBLEM = "application/problem+json"


def problem(status: int, title: str, detail: str | None = None) -> JSONResponse:
    body = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


class State:
    """In-memory state of one stand-in server (reset per app instance)."""

    def __init__(self):
        self.idempotency: dict[tuple, tuple[str, int, object]] = {}
        self.deliveries: set[tuple[str, str]] = set()
        self.guard_seq = 0
        self.shops: dict[str, dict] = {data.SHOP_ID: {
            "shop_id": data.SHOP_ID, "name": "Legacy PHP shop (Cutover sample, MIT)",
            "repo": data.SHOP_REPO, "site": None, "created_at": "2026-11-02T09:00:00Z"}}


# ---------------------------------------------------------------- handlers
def _need_graft(graft_id: str):
    if graft_id != data.GRAFT_ID:
        raise HTTPException(404, f"graft {graft_id} not found (stand-in knows {data.GRAFT_ID})")


def _need_shop(state, shop_id: str) -> dict:
    if shop_id not in state.shops:
        raise HTTPException(404, f"shop {shop_id} not found")
    return state.shops[shop_id]


def _need_cert(cert_id: str):
    if cert_id not in {data.CERT_ID, data.TAMPERED_CERT_ID}:
        raise HTTPException(404, f"certificate {cert_id} not found")


def _sse(events: list[dict], *, event: str, after: int, speed: float) -> StreamingResponse:
    delay = 0 if speed <= 0 else 1.0 / speed

    async def stream():
        for item in events:
            seq = item.get("seq", 0)
            if seq <= after:
                continue
            yield f"id: {seq}\nevent: {event}\ndata: {json.dumps(item, sort_keys=True)}\n\n"
            if delay:
                await asyncio.sleep(delay)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


def _last_event_id(request: Request) -> int:
    raw = request.headers.get("Last-Event-ID", "0")
    return int(raw) if raw.isdigit() else 0


def h_probe(state, request, body, **_):
    found = data.example("ProbeResult")
    found["files_or_pages"] = [body.url]
    found["families_found"] = ["EC_NVP", "IPN"]
    found["deadline_notes"] = ["PayPal: WPS buttons may retire after 1 Jan 2027"]
    return found


def h_create_shop(state, request, body, **_):
    sid = "shop-" + hashlib.sha256((body.repo or body.site or body.name or "").encode()
                                   ).hexdigest()[:8]
    shop = {"shop_id": sid, "name": body.name, "repo": body.repo, "site": body.site,
            "created_at": datetime.now(UTC).isoformat()}
    state.shops.setdefault(sid, shop)
    return state.shops[sid]


def h_connect_shop(state, request, body, shop_id, **_):
    # Secrets would go straight to the vault here. Nothing about them is kept or logged.
    shop = _need_shop(state, shop_id)
    return {"shop_id": shop_id, "repo": shop["repo"], "site": shop["site"],
            "secrets_ref": f"doppler://goldgraft/shops/{shop_id}",
            "checks": {"rest_ok": True, "nvp_ok": body.nvp_user is not None,
                       "webhook_ok": body.webhook_id is not None, "version_match": True}}


def h_start_graft(state, request, body, shop_id, **_):
    _need_shop(state, shop_id)
    return data.graft()


def h_get_graft(state, request, graft_id, **_):
    _need_graft(graft_id)
    return data.graft()


def h_graft_events(state, request, graft_id, speed=10.0, **_):
    _need_graft(graft_id)
    return _sse(list(data.demo_events()), event="ledger", after=_last_event_id(request),
                speed=speed)


def h_get_rootmap(state, request, graft_id, **_):
    _need_graft(graft_id)
    return data.override("get_rootmap") or data.example("RootMap")


def h_get_scenarios(state, request, graft_id, **_):
    _need_graft(graft_id)
    return data.scenarios()


def h_get_cmel(state, request, graft_id, scenario, **_):
    _need_graft(graft_id)
    known = {row["scenario"]["id"] for row in data.scenarios()["scenarios"]}
    if scenario not in known:
        raise HTTPException(404, f"scenario {scenario} not found")
    return data.cmel(scenario)


def h_get_proof(state, request, graft_id, **_):
    _need_graft(graft_id)
    return data.proof()


def h_get_certificate(state, request, cert_id, **_):
    _need_cert(cert_id)
    return data.certificate(cert_id)


def h_verify_certificate(state, request, cert_id, **_):
    _need_cert(cert_id)
    return data.verify(cert_id)


def h_get_heal(state, request, graft_id, speed=10.0, **_):
    _need_graft(graft_id)
    snapshot = data.heal()
    if "text/event-stream" in request.headers.get("accept", ""):
        frames = [dict(snapshot, seq=i + 1) for i in range(3)]
        return _sse(frames, event="heal", after=_last_event_id(request), speed=speed)
    return snapshot


def h_inject_fault(state, request, body, graft_id, **_):
    _need_graft(graft_id)
    return {"accepted": True}


def h_get_switch_config(state, request, graft_id, **_):
    _need_graft(graft_id)
    return data.heal()["switch_config"]


def h_guard_event(state, request, body, **_):
    state.guard_seq += 1
    return {"accepted": True, "ledger_seq": state.guard_seq}


def _webhook(state, request, route: Route):
    missing = [h for h in route.signature_headers if h not in request.headers]
    if missing:
        raise HTTPException(400, "missing signature headers: " + ", ".join(missing))
    delivery = (route.name, request.headers[route.dedupe_header])
    if delivery in state.deliveries:
        return {"accepted": True, "deduplicated": True}
    state.deliveries.add(delivery)
    return {"accepted": True}


def h_paypal_webhook(state, request, graft_id, route, **_):
    _need_graft(graft_id)
    return _webhook(state, request, route)


def h_github_webhook(state, request, route, **_):
    return _webhook(state, request, route)


def h_list_recipes(state, request, **_):
    return data.recipes()


def h_learning_curve(state, request, **_):
    return data.learning_curve()


def h_get_orchard(state, request, **_):
    return data.orchard()


def h_orchard_ask(state, request, body, **_):
    return data.orchard_answer(body.question)


def h_get_gauntlet(state, request, run_id, **_):
    return data.gauntlet(run_id)


def h_get_comparison(state, request, **_):
    return data.comparison()


HANDLERS: dict[str, Callable] = {
    name[2:]: fn for name, fn in globals().items() if name.startswith("h_")
}


# ---------------------------------------------------------------- wiring
def _endpoint(route: Route, state: State):
    handler = HANDLERS[route.name]
    path_params = re.findall(r"{(\w+)}", route.path)
    params = [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)]
    params += [inspect.Parameter(p, inspect.Parameter.KEYWORD_ONLY, annotation=str)
               for p in path_params]
    params += [inspect.Parameter(q, inspect.Parameter.KEYWORD_ONLY, annotation=str,
                                 default=Query(...)) for q in route.query]
    if route.sse:
        params.append(inspect.Parameter(
            "speed", inspect.Parameter.KEYWORD_ONLY, annotation=float,
            default=Query(10.0, description="events per second; 0 = no delay")))
    if route.request is not None:
        params.append(inspect.Parameter("body", inspect.Parameter.KEYWORD_ONLY,
                                        annotation=route.request))
    for i, header in enumerate(route.signature_headers):
        params.append(inspect.Parameter(
            f"signature_header_{i}", inspect.Parameter.KEYWORD_ONLY, annotation=str | None,
            default=Header(None, alias=header, description="required; verified + de-duplicated")))
    if route.needs_idempotency_key:
        params.append(inspect.Parameter(
            "idempotency_key", inspect.Parameter.KEYWORD_ONLY, annotation=str,
            default=Header(..., alias="Idempotency-Key", min_length=1)))

    async def endpoint(**kwargs):
        key = kwargs.pop("idempotency_key", None)
        body = kwargs.get("body")
        log.info("%s %s", route.method, route.path)  # never the body: it may hold secrets
        if key is not None:
            body_hash = hashlib.sha256(
                body.model_dump_json().encode() if body is not None else b"").hexdigest()
            slot = (route.name, tuple(kwargs.get(p) for p in path_params), key)
            if slot in state.idempotency:
                seen_hash, status, payload = state.idempotency[slot]
                if seen_hash != body_hash:
                    return problem(409, "Idempotency-Key reused with a different body")
                return JSONResponse(payload, status_code=status)
        try:
            result = handler(state, route=route, **kwargs)
        except HTTPException as exc:
            return problem(exc.status_code, "Error", str(exc.detail))
        if isinstance(result, Response):
            return result
        payload = route.response.model_validate(result).model_dump(mode="json")
        if key is not None:
            state.idempotency[slot] = (body_hash, 200, payload)
        return JSONResponse(payload)

    endpoint.__signature__ = inspect.Signature(params)
    endpoint.__name__ = route.name
    return endpoint


def create_app() -> FastAPI:
    app = FastAPI(title="GoldGraft control-plane API (stand-in)", version="1.0.0",
                  description="Contract: goldgraft_contracts.api_routes. Stand-in data is "
                              "SYNTHETIC. Errors are RFC 7807 problem+json.")
    app.add_middleware(CORSMiddleware,
                       allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
                       allow_methods=["*"], allow_headers=["*"])
    state = State()
    app.state.fake = state

    @app.exception_handler(RequestValidationError)
    async def _invalid(request, exc):
        fields = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
        return problem(422, "Request does not match the contract", "; ".join(fields))

    @app.exception_handler(HTTPException)
    async def _http(request, exc):
        return problem(exc.status_code, "Error", str(exc.detail))

    for route in ROUTES:
        responses = {"4XX": {"model": None, "description": "RFC 7807 problem",
                             "content": {PROBLEM: {}}}}
        if route.sse:
            responses[200] = {"content": {"text/event-stream": {}}}
        extra = None
        if route.signature_headers:  # raw signed body: documented, not parsed into a model
            extra = {"requestBody": {"required": True, "content": {
                "application/json": {"schema": {"type": "object"}}}}}
        app.add_api_route(route.path, _endpoint(route, state), methods=[route.method],
                          name=route.name, summary=route.summary,
                          response_model=route.response, responses=responses,
                          tags=list(route.screens) or ["shop-libs"], openapi_extra=extra)
    return app


app = create_app()


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8700)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
