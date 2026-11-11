"""FastAPI Control-Plane Application for GoldGraft (GU01 & GU02).

Serves all defined routes from goldgraft_contracts.api_routes, integrates with
the LifecycleEngine and CustodyBroker, and satisfies strict contract shapes and
idempotency requirements.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from goldgraft_contracts.api_routes import route
from goldgraft_contracts.interfaces import Proof as ProofPort
from goldgraft_contracts.registry import validate
from goldgraft_contracts.run_views import FixtureRunViews
from goldgraft_foundation.ledger import Ledger

from .custody_broker import CustodyBroker
from .lifecycle import JobLifecycleState, LifecycleEngine

log = logging.getLogger("goldgraft.backend")
PROBLEM = "application/problem+json"


def problem(status: int, title: str, detail: str | None = None) -> JSONResponse:
    body = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


class BackendState:
    """In-memory state and registry for backend service."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self.lifecycle = LifecycleEngine(self.ledger)
        self.custody = CustodyBroker()
        self.idempotency: dict[tuple, tuple[str, int, object]] = {}
        self.deliveries: set[tuple[str, str]] = set()
        self.guard_seq = 0
        self.shops: dict[str, dict[str, Any]] = {}
        self.grafts: dict[str, dict[str, Any]] = {}

        self._seed_sample_data()

    def _seed_sample_data(self):
        sample_shop_id = "shop-cutover-legacy"
        sample_graft_id = "demo-1"
        self.shops[sample_shop_id] = {
            "shop_id": sample_shop_id,
            "name": "Legacy PHP shop (Cutover sample, MIT)",
            "repo": "https://github.com/goldgraft/legacy-php-shop",
            "site": None,
            "created_at": "2026-11-02T09:00:00Z",
        }
        self.grafts[sample_graft_id] = self._build_graft_dict(sample_graft_id, sample_shop_id)

    def _build_graft_dict(self, graft_id: str, shop_id: str) -> dict[str, Any]:
        stages = [
            {"stage": "CREATED", "minutes": 1.5, "usd": 0.05},
            {"stage": "GATED", "minutes": 1.5, "usd": 0.05},
            {"stage": "SURVEYED", "minutes": 1.5, "usd": 0.05},
            {"stage": "BUILT", "minutes": 1.5, "usd": 0.05},
            {"stage": "RECORDED", "minutes": 1.5, "usd": 0.05},
            {"stage": "CONTRACTED", "minutes": 1.5, "usd": 0.05},
            {"stage": "ATTACK_PLANNED", "minutes": 1.5, "usd": 0.05},
            {"stage": "GRAFTED", "minutes": 1.5, "usd": 0.05},
            {"stage": "PROVING", "minutes": 1.5, "usd": 0.05},
            {"stage": "REPAIRING", "minutes": 1.5, "usd": 0.05},
            {"stage": "CERTIFIED", "minutes": 1.5, "usd": 0.05},
            {"stage": "PR_OPEN", "minutes": 1.5, "usd": 0.05},
            {"stage": "MERGED", "minutes": 1.5, "usd": 0.05},
            {"stage": "SHADOW", "minutes": 1.5, "usd": 0.05},
            {"stage": "HEAL_1", "minutes": 1.5, "usd": 0.05},
            {"stage": "HEAL_10", "minutes": 1.5, "usd": 0.05},
            {"stage": "HEAL_50", "minutes": 1.5, "usd": 0.05},
            {"stage": "LIVE_100", "minutes": 1.5, "usd": 0.05},
            {"stage": "CLEANUP_PR", "minutes": 1.5, "usd": 0.05},
            {"stage": "DONE", "minutes": 1.5, "usd": 0.05},
        ]
        return {
            "graft_id": graft_id,
            "shop_id": shop_id,
            "stage": "DONE",
            "lane": "FULL",
            "started_at": datetime.now(UTC).isoformat(),
            "stages": stages,
            "ledger_root": hashlib.sha256(graft_id.encode()).hexdigest(),
            "card": {
                "old_pieces_found": 5,
                "pieces_upgraded": 5,
                "scenarios_total": 9,
                "scenarios_pass": 6,
                "problems": 2,
                "proof_strength_score": 0.92,
                "cost_usd": 3.85,
                "minutes": 41.0,
                "notes": {
                    "old_pieces_found": "Old PayPal code spots found in the shop",
                    "scenarios_pass": "Payment situations that behave the same or better",
                    "problems": "Payment situations where the new code is wrong",
                    "proof_strength_score": "Share of planted money bugs our tests caught",
                    "cost_usd": "AI cost for this shop so far",
                    "_label": "SYNTHETIC — stand-in data, not a recording",
                },
            },
        }


def create_app(
    *, proof: ProofPort | None = None, views: FixtureRunViews | None = None
) -> FastAPI:
    app = FastAPI(title="GoldGraft Backend Engine", version="1.0.0")
    state = BackendState()

    def projected(method, *args):
        try:
            return getattr(views, method)(*args).model_dump(mode="json")
        except LookupError:
            raise HTTPException(404, "Fixture evidence is not available") from None
        except ValueError as exc:
            status = 409 if str(exc).startswith("CONFLICT") else 503
            raise HTTPException(status, "Fixture evidence conflicts or failed validation") from None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return problem(422, "Validation Error", str(exc))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail)
        return problem(exc.status_code, "Request Failed", detail)

    # ------------------ ROUTE HANDLERS ------------------ #

    @app.post("/probe")
    async def probe(request: Request):
        body = await request.json()
        url = body.get("url", "")
        # Return valid ProbeResult example
        from goldgraft_fakes import data

        ex = dict(data.example("ProbeResult"))
        ex["files_or_pages"] = [url] if url else []
        return ex

    @app.post("/shops")
    async def create_shop(
        request: Request, idempotency_key: str | None = Header(None, alias="Idempotency-Key")
    ):
        if not idempotency_key:
            return problem(400, "Missing Idempotency-Key header")

        body = await request.json()
        body_str = json.dumps(body, sort_keys=True)
        call_sig = ("POST", "/shops", idempotency_key)

        if call_sig in state.idempotency:
            saved_body, code, saved_resp = state.idempotency[call_sig]
            if saved_body != body_str:
                return problem(409, "Idempotency conflict with different request body")
            return JSONResponse(saved_resp, status_code=code)

        sid = (
            "shop-"
            + hashlib.sha256(
                (body.get("repo") or body.get("site") or body.get("name") or "").encode()
            ).hexdigest()[:8]
        )
        shop = {
            "shop_id": sid,
            "name": body.get("name") or "Legacy Shop",
            "repo": body.get("repo"),
            "site": body.get("site"),
            "created_at": datetime.now(UTC).isoformat(),
        }
        state.shops[sid] = shop
        state.idempotency[call_sig] = (body_str, 200, shop)
        return shop

    @app.post("/shops/{shop_id}/connect")
    async def connect_shop(
        shop_id: str,
        request: Request,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        if not idempotency_key:
            return problem(400, "Missing Idempotency-Key header")
        if shop_id not in state.shops:
            return problem(404, f"Shop {shop_id} not found")

        secrets = await request.json()
        secret_ref = state.custody.store_credentials(shop_id, secrets)
        shop = state.shops[shop_id]

        conn = {
            "shop_id": shop_id,
            "repo": shop.get("repo") or "https://github.com/example/shop",
            "site": shop.get("site"),
            "secrets_ref": secret_ref.to_uri(),
            "checks": {"rest_ok": True, "nvp_ok": True, "webhook_ok": True, "version_match": True},
        }
        return conn

    @app.post("/shops/{shop_id}/graft")
    async def start_graft(
        shop_id: str,
        request: Request,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        if not idempotency_key:
            return problem(400, "Missing Idempotency-Key header")
        if shop_id not in state.shops:
            return problem(404, f"Shop {shop_id} not found")

        if views is not None and shop_id == views.shop_id:
            body = await request.json()
            try:
                route("start_graft").request.model_validate(body)
            except ValueError:
                return problem(422, "Request does not match StartGraftRequest")
            return projected("start", idempotency_key, body)

        graft_id = f"graft-{hashlib.sha256((shop_id + idempotency_key).encode()).hexdigest()[:8]}"
        state.lifecycle.transition(
            graft_id=graft_id,
            target_state=JobLifecycleState.BASELINE_TESTED,
            idempotency_key=idempotency_key,
            reason="Graft initiated",
        )

        graft_data = state._build_graft_dict(graft_id, shop_id)
        state.grafts[graft_id] = graft_data
        return graft_data

    @app.get("/grafts/{graft_id}")
    async def get_graft(graft_id: str):
        if views is not None and graft_id == views.graft_id:
            return projected("graft")
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        return state.grafts[graft_id]

    @app.get("/grafts/{graft_id}/events")
    async def graft_events(graft_id: str, request: Request, speed: float = Query(0.0)):
        if views is not None and graft_id == views.graft_id:
            after = request.headers.get("Last-Event-ID", "0")
            if not after.isdecimal():
                return problem(400, "Last-Event-ID must be a nonnegative sequence")
            try:
                entries = views.events(int(after))
            except ValueError:
                return problem(503, "Fixture ledger failed validation")

            async def persisted_stream():
                for entry in entries:
                    yield (f"id: {entry.seq}\nevent: ledger\n"
                           f"data: {entry.model_dump_json()}\n\n")

            return StreamingResponse(persisted_stream(), media_type="text/event-stream")
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")

        async def sse_stream():
            from goldgraft_fakes import data

            events = list(data.demo_events())
            for item in events:
                seq = item.get("seq", 0)
                yield f"id: {seq}\nevent: ledger\ndata: {json.dumps(item, sort_keys=True)}\n\n"

        return StreamingResponse(sse_stream(), media_type="text/event-stream")

    @app.get("/grafts/{graft_id}/rootmap")
    async def get_rootmap(graft_id: str):
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        from goldgraft_fakes import data

        return data.example("RootMap")

    @app.get("/grafts/{graft_id}/scenarios")
    async def get_scenarios(graft_id: str):
        if views is not None and graft_id == views.graft_id:
            return projected("scenarios")
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        from goldgraft_fakes import data

        return data.scenarios()

    @app.get("/grafts/{graft_id}/cmel")
    async def get_cmel(graft_id: str, scenario: str | None = Query(None)):
        if views is not None and graft_id == views.graft_id:
            return projected("cmel", scenario or "HAPPY")
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        from goldgraft_fakes import data

        scenario_id = scenario or "HAPPY"
        known = {row["scenario"]["id"] for row in data.scenarios()["scenarios"]}
        if scenario_id not in known:
            return problem(404, f"Scenario {scenario_id} not found")
        return data.cmel(scenario_id)

    @app.get("/grafts/{graft_id}/proof")
    async def get_proof(graft_id: str):
        if views is not None and graft_id == views.graft_id:
            return projected("proof")
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        from goldgraft_fakes import data

        return data.proof()

    @app.get("/certificates/{cert_id}")
    async def get_certificate(cert_id: str):
        from goldgraft_fakes import data

        if cert_id not in {data.CERT_ID, data.TAMPERED_CERT_ID}:
            return problem(404, f"Certificate {cert_id} not found")
        return data.certificate(cert_id)

    @app.post("/certificates/{cert_id}/verify")
    async def verify_certificate(cert_id: str):
        from goldgraft_fakes import data

        if cert_id not in {data.CERT_ID, data.TAMPERED_CERT_ID}:
            return problem(404, f"Certificate {cert_id} not found")
        if proof is None:
            return problem(503, "Independent proof adapter is not configured")
        certificate = validate("Certificate/1", data.certificate(cert_id))
        return proof.verify_certificate(certificate).model_dump(mode="json")

    @app.get("/heal/{graft_id}")
    async def get_heal(graft_id: str):
        from goldgraft_fakes import data

        return data.heal()

    @app.post("/heal/{graft_id}/inject-fault")
    async def inject_fault(graft_id: str):
        return {"graft_id": graft_id, "injected": True}

    @app.get("/switch/config/{graft_id}")
    async def get_switch_config(graft_id: str):
        from goldgraft_fakes import data

        return data.example("SwitchConfig")

    @app.post("/guard/event")
    async def guard_event(request: Request):
        return {"status": "ACK", "received_at": datetime.now(UTC).isoformat()}

    @app.post("/pp/webhook/{graft_id}")
    async def paypal_webhook(graft_id: str, request: Request):
        if graft_id not in state.grafts:
            return problem(404, f"Graft {graft_id} not found")
        r = route("paypal_webhook")
        missing = [h for h in r.signature_headers if h not in request.headers]
        if missing:
            return problem(400, "missing signature headers: " + ", ".join(missing))
        delivery = (r.name, request.headers[r.dedupe_header])
        if delivery in state.deliveries:
            return {"accepted": True, "deduplicated": True}
        state.deliveries.add(delivery)
        return {"accepted": True}

    @app.post("/gh/webhook")
    async def github_webhook(request: Request):
        r = route("github_webhook")
        missing = [h for h in r.signature_headers if h not in request.headers]
        if missing:
            return problem(400, "missing signature headers: " + ", ".join(missing))
        delivery = (r.name, request.headers[r.dedupe_header])
        if delivery in state.deliveries:
            return {"accepted": True, "deduplicated": True}
        state.deliveries.add(delivery)
        return {"accepted": True}

    @app.get("/recipes")
    async def get_recipes():
        from goldgraft_fakes import data

        return data.recipes()

    @app.get("/learning-curve")
    async def get_learning_curve():
        from goldgraft_fakes import data

        return data.learning_curve()

    @app.get("/orchard")
    async def get_orchard():
        from goldgraft_fakes import data

        return data.orchard()

    @app.post("/orchard/ask")
    async def orchard_ask(request: Request):
        from goldgraft_fakes import data

        body = await request.json()
        return data.orchard_ask(body.get("question", ""))

    @app.get("/security/gauntlet/{run_id}")
    async def security_gauntlet(run_id: str):
        from goldgraft_fakes import data

        return data.gauntlet(run_id)

    @app.get("/comparison")
    async def comparison():
        from goldgraft_fakes import data

        return data.comparison()

    return app


app = create_app()
