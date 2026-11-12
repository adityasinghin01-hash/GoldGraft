"""Local v1 API for real-model evidence; live dispatch requires explicit opt-in.

Run with ``.venv/bin/python -m integration.agents_app --port 8700 [--live]``.
All other requests retain the strictly offline fixture application's behaviour.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock, Thread

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from goldgraft_contracts.api import (
    GauntletRun,
    Graft,
    OrchardView,
    RecipeList,
    ScenarioList,
    StartGraftRequest,
)
from goldgraft_contracts.registry import validate
from starlette.concurrency import run_in_threadpool

from integration.agent_views import IntegratedRunViews
from integration.app import create_app as offline_app
from integration.local_proof import EVIDENCE_CLASS as LOCAL_PHP_EVIDENCE_CLASS
from integration.local_proof import LocalProof

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = Path.home() / "reports/goldgraft-agents-integration-20261112/runs"
GATEWAY_PYTHON = Path("/Users/aditya/reports/goldgraft-model-gateway-20261111/venv/bin/python")
EVIDENCE_CLASS = "real-models-scripted-runner"
NO_PROOF = (
    "Money events here come from the recorded runner and are not served for real agent runs; "
    "the independent proof has not run on this run's AI-written code yet"
)
NO_ASK = (
    "New questions would each run a paid Orchard Analyst call, which this local service does not "
    "do; the dashboards below are the ones the agent already built from real runs"
)
NO_GOLIVE = (
    "Go-live has not run for this upgrade. The Healer's diagnosis of a controlled fault is on "
    "the Agents tab"
)
log = logging.getLogger(__name__)


def _shop_label(body):
    """A readable name for an unnamed shop: the repo's last path part, else the site host."""
    repo = str(body.get("repo") or "").rstrip("/")
    if repo:
        name = repo.rsplit("/", 1)[-1].removesuffix(".git")
        if name:
            return name
    site = str(body.get("site") or "")
    host = re.sub(r"^[a-z]+://", "", site).split("/", 1)[0]
    return host or None


NOT_YET = "Not available yet"  # the app shows these as a calm note, not an error


def _problem(status, detail, title="Request Failed"):
    return JSONResponse(
        {"type": "about:blank", "title": title, "status": status, "detail": detail},
        status_code=status,
        media_type="application/problem+json",
    )


def _default_runner(runs_dir):
    def run(shop, run_id):
        logs = runs_dir.parent / "web-runs"
        logs.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["PATH"] = "/Library/Developer/CommandLineTools/usr/bin:" + env.get("PATH", "")
        with (logs / f"{run_id}.log").open("wb") as output:
            try:
                subprocess.run(
                    [
                        str(GATEWAY_PYTHON),
                        "-m",
                        "scripts.live_integrated_run",
                        "--live",
                        "--run-id",
                        run_id,
                        "--shop",
                        shop,
                        "--max-usd",
                        "0.60",
                    ],
                    cwd=ROOT,
                    env=env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            finally:
                # The existing driver owns a fixed output path. Custom API evidence
                # directories receive only this newly dispatched run's JSON files.
                if runs_dir != DEFAULT_RUNS_DIR.resolve():
                    source = DEFAULT_RUNS_DIR / run_id
                    for name in ("RESULT.json", "OUTPUTS.json", "EDGES.json", "CHANGES.json"):
                        if (source / name).is_file():
                            destination = runs_dir / run_id
                            destination.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(source / name, destination / name)

    return run


@dataclass
class _LiveRun:
    shop: str
    graft: Graft
    status: str = "starting"
    finished_at: str | None = None


def create_app(
    *, runs_dir: Path, live_enabled: bool = False, runner=None, max_live_runs: int = 3
) -> FastAPI:
    if max_live_runs < 0:
        raise ValueError("max_live_runs must be nonnegative")
    runs_dir = Path(runs_dir).expanduser().resolve()
    app = offline_app()
    cache = TemporaryDirectory(prefix="goldgraft-agent-views-")
    views: dict[str, IntegratedRunViews] = {}
    shops: dict[str, dict] = {}
    live: dict[str, _LiveRun] = {}
    starts: dict[tuple[str, str], tuple[dict, dict]] = {}
    lock = Lock()
    active = None
    admitted_count = 0
    runner = runner if runner is not None else _default_runner(runs_dir)
    previous_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(app):
        try:
            async with previous_lifespan(app):
                yield
        finally:
            for view in views.values():
                view.ledger.engine.dispose()
            cache.cleanup()

    app.router.lifespan_context = lifespan

    def directory(run_id):
        candidate = runs_dir / run_id
        return candidate if candidate.resolve().parent == runs_dir else None

    def get_view(run_id):
        if run_id not in views:
            views[run_id] = IntegratedRunViews(
                directory(run_id), ledger_directory=Path(cache.name) / run_id
            )
        return views[run_id]

    def execute(shop, run_id):
        nonlocal active
        failed = False
        try:
            runner(shop, run_id)
        except Exception:
            # Provider exception text may contain secrets; keep it out of HTTP/logs.
            failed = True
            log.error("Integrated runner failed for %s; inspect its local evidence log", run_id)
        finally:
            with lock:
                record = live[run_id]
                record.status = (
                    "failed"
                    if failed or not (runs_dir / run_id / "RESULT.json").exists()
                    else "finished"
                )
                record.finished_at = datetime.now(UTC).isoformat()
                active = None

    def start_live(request, shop_id, body):
        nonlocal active, admitted_count
        key = request.headers.get("Idempotency-Key")
        if not key:
            return _problem(400, "Missing Idempotency-Key header")
        try:
            StartGraftRequest.model_validate(body)
        except ValueError:
            return _problem(422, "Request does not match StartGraftRequest")
        with lock:
            call = (shop_id, key)
            if call in starts:
                old_body, payload = starts[call]
                return (
                    JSONResponse(payload)
                    if old_body == body
                    else _problem(409, "Idempotency conflict with different request body")
                )
            if active is not None:
                return _problem(409, "A live integrated run is already in progress")
            if admitted_count >= max_live_runs:
                return _problem(429, "Process live-run limit reached")
            shop_name = next(
                name
                for name in ("legacy-php-shop", "eval-nvp")
                if name
                in " ".join(
                    str(shops[shop_id].get(k) or "") for k in ("repo", "site", "name")
                ).lower()
            )
            stamp = datetime.now(UTC)
            while True:
                run_id = f"web-{shop_name}-{stamp:%Y%m%d-%H%M%S}"
                if run_id not in live and not (runs_dir / run_id).exists():
                    break
                stamp += timedelta(seconds=1)
            # No run directory is created here: the driver owns creating it.
            graft = Graft.model_validate(
                {
                    "graft_id": run_id,
                    "shop_id": shop_id,
                    "stage": "CREATED",
                    "lane": "FULL",
                    "started_at": datetime.now(UTC),
                    "stages": [],
                    "ledger_root": "0" * 64,
                    "card": {
                        "old_pieces_found": 0,
                        "pieces_upgraded": 0,
                        "scenarios_total": 0,
                        "scenarios_pass": 0,
                        "problems": 0,
                        "proof_strength_score": None,
                        "cost_usd": 0.0,
                        "minutes": 0.0,
                        "notes": {
                            "_label": "REAL MODELS · starting a real-model run · "
                            "scripted runner, no independent proof yet"
                        },
                    },
                }
            )
            live[run_id] = _LiveRun(shop_name, graft)
            active = run_id
            admitted_count += 1
            payload = graft.model_dump(mode="json")
            starts[call] = (body, payload)
            try:
                Thread(target=execute, args=(shop_name, run_id), daemon=True).start()
            except RuntimeError:
                active = None
                admitted_count -= 1
                del live[run_id]
                del starts[call]
                return _problem(503, "Could not start the integrated runner thread")
        return JSONResponse(payload)

    def list_runs():
        with lock:
            records = dict(live)
        paths = {
            p.parent.name: p.parent
            for p in runs_dir.glob("*/RESULT.json")
            if directory(p.parent.name) is not None
        }
        rows = []
        for run_id in paths.keys() | records.keys():
            record = records.get(run_id)
            path = paths.get(run_id)
            result = json.loads((path / "RESULT.json").read_text()) if path else {}
            tasks = result.get("tasks", [])
            participated = result.get("roles_participated", sorted({r["role"] for r in tasks}))
            passed = result.get(
                "roles_passed", sorted({r["role"] for r in tasks if r.get("passed")})
            )
            rows.append(
                {
                    "run_id": run_id,
                    "shop": result.get("shop", record.shop if record else None),
                    "status": (
                        "failed"
                        if record and record.status == "failed"
                        else result.get("status", record.status if record else "unknown")
                    ),
                    "roles_passed": len(passed),
                    "roles_participated": len(participated),
                    "spent_usd": round(result.get("spent_micro_usd", 0) / 1_000_000, 6),
                    "finished_at": result.get(
                        "finished_at", record.finished_at if record else None
                    ),
                }
            )

        def order(row):
            record = records.get(row["run_id"])
            timestamp = row["finished_at"] or (record.graft.started_at if record else None)
            if timestamp is not None:
                return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).timestamp()
            return (paths[row["run_id"]] / "RESULT.json").stat().st_mtime

        return sorted(rows, key=order, reverse=True)

    def is_run(run_id):
        folder = directory(run_id)
        return folder is not None and (folder / "RESULT.json").is_file()

    def finished_runs():
        """Runs with committed results, newest first."""
        rows = list_runs()
        return [r["run_id"] for r in rows if r["status"] != "running" and is_run(r["run_id"])]

    def gauntlet(run_id):
        """Sentinel's real audit alerts for this run (no hidden-instruction test shop ran here)."""
        alerts = get_view(run_id).outputs_of("Alert/1")
        run = GauntletRun.model_validate({"run_id": run_id, "attempts": [], "alerts": alerts})
        return dict(
            run.model_dump(mode="json"),
            label="Real Sentinel output for this agent run; it audited a controlled hostile event",
        )

    def fleet_recipes():
        """The Librarian's real (quarantined) recipes across runs; newest copy of each id wins."""
        found = {}
        for run_id in reversed(finished_runs()):
            for recipe in get_view(run_id).outputs_of("Recipe/1"):
                found[recipe["id"]] = recipe
        return RecipeList.model_validate({"recipes": list(found.values())}).model_dump(mode="json")

    def fleet_orchard():
        """PayPal-team view from real runs: latest surveyed run per shop + Orchard dashboards."""
        runs = finished_runs()
        latest = {}
        # Each shop's newest completed run (a held run would understate how far it got).
        for want_completed in (True, False):
            for run_id in runs:
                view = get_view(run_id)
                completed = view.agents()["status"] == "completed"
                if view.shop_id not in latest and view.outputs_of("RootMap/1"):
                    if completed or not want_completed:
                        latest[view.shop_id] = view
        shops = []
        for shop_id, view in latest.items():
            spots = view.rootmap().get("touchpoints", [])
            plans = view.outputs_of("TargetPlan/1")
            items = plans[0].get("items", []) if plans else []
            shops.append(
                {
                    "shop_id": shop_id,
                    "stage": str(view.graft().stage),
                    "old_families": sorted({t["family"] for t in spots}),
                    "deadline_risk": "Not assessed in test runs",
                    "paypal_only_items": sum(1 for i in items if i.get("paypal_only")),
                }
            )
        dashboards = {}
        for run_id in reversed(runs):
            for spec in get_view(run_id).outputs_of("DashboardSpec/1"):
                dashboards[spec.get("title") or spec["id"]] = spec
        view = OrchardView.model_validate(
            {
                "shops": shops,
                "dashboards": list(dashboards.values()),
                "label": f"Real Orchard Analyst output over {len(runs)} local test runs",
            }
        )
        return view.model_dump(mode="json")

    def read_run(request, run_id, suffix):
        path = directory(run_id)
        has_local_proof = (path / "local-proof/REPORT.json").is_file()
        if has_local_proof and suffix in {"scenarios", "cmel"}:
            recorded = LocalProof(path)
            if suffix == "scenarios":
                body = recorded.scenarios()
            else:
                try:
                    body = recorded.cmel(request.query_params.get("scenario", "HAPPY").upper())
                except LookupError:
                    return _problem(404, "Unknown local PHP scenario")
            return JSONResponse(
                body.model_dump(mode="json"),
                headers={"X-GoldGraft-Evidence-Class": LOCAL_PHP_EVIDENCE_CLASS},
            )
        if suffix == "connected-proof":
            # The exact signed bytes, so a browser can hash them and compare with the log.
            stored = path / "connected-run/ProofResult.json"
            if not stored.is_file():
                return _problem(404, "No connected run has been recorded for this run yet", NOT_YET)
            raw = stored.read_bytes()
            validate("ProofResult/1", json.loads(raw))
            return Response(raw, media_type="application/json")
        if suffix == "connected":
            connected = path / "connected-run"
            if not (connected / "CONNECTED_RUN.json").is_file():
                return _problem(404, "No connected run has been recorded for this run yet", NOT_YET)
            # Re-validate every stored record on read; a changed file fails closed (503).
            records = {
                name: validate(schema, json.loads((connected / f"{name}.json").read_bytes()))
                for name, schema in (
                    ("ProofPlan", "ProofPlan/1"),
                    ("ProofResult", "ProofResult/1"),
                    ("PromotionDecision", "PromotionDecision/1"),
                    ("PublicProofView", "PublicProofView/1"),
                )
            }
            summary = json.loads((connected / "CONNECTED_RUN.json").read_bytes())
            result = records["ProofResult"]
            if (
                summary["proof_plan"]["digest"] != records["ProofPlan"].plan_digest
                or result.plan_digest != records["ProofPlan"].plan_digest
                or summary["proof_result"]["outcome"] != result.outcome
            ):
                raise ValueError("connected run summary does not match its records")
            signing_file = connected / "SIGNING.json"
            if signing_file.is_file():
                signing = json.loads(signing_file.read_bytes())
                signed = hashlib.sha256((connected / "ProofResult.json").read_bytes()).hexdigest()
                if signing.get("payload_sha256") != signed:
                    raise ValueError("signature record does not match this proof result")
                summary["signing"] = signing
            summary["checks"] = [
                {
                    "check_id": c.check_id,
                    "kind": c.kind,
                    "critical": c.critical,
                    "evidence_class": c.required_evidence_class,
                    "state": r.state,
                    "reason": r.reason_code,
                }
                for c, r in zip(records["ProofPlan"].checks, result.results, strict=True)
            ]
            return JSONResponse(
                summary, headers={"X-GoldGraft-Evidence-Class": "local_component_connected"}
            )
        if suffix == "agents":
            return JSONResponse(get_view(run_id).agents())
        if suffix == "scenarios":
            # The Adversary's real attack scenarios; no independent verdict exists yet.
            rows = [
                {"scenario": sc, "verdict": None}
                for sset in get_view(run_id).outputs_of("ScenarioSet/1")
                for sc in sset.get("scenarios", [])
            ]
            try:
                listed = ScenarioList.model_validate({"graft_id": run_id, "scenarios": rows})
            except ValueError:
                listed = ScenarioList(graft_id=run_id, scenarios=[])
            return JSONResponse(listed.model_dump(mode="json"))
        if suffix in {"cmel", "proof"}:
            if (path / "connected-run/CONNECTED_RUN.json").is_file():
                return _problem(
                    404,
                    "This run's independent proof is its connected run: the AI-written code was "
                    "executed and judged there. The planted-bug replay view is not produced for it",
                    NOT_YET,
                )
            if has_local_proof:
                return _problem(
                    404,
                    "Local PHP verdicts and bounded candidate mutation checks are available; "
                    "complete critical-rule coverage and a qualified certificate "
                    "remain unavailable",
                    NOT_YET,
                )
            return _problem(404, NO_PROOF, NOT_YET)
        if suffix == "changes":
            changes = path / "CHANGES.json"
            if not changes.is_file():
                return _problem(404, "The Grafter has not written code for this run yet", NOT_YET)
            body = json.loads(changes.read_text())
            planted = get_view(run_id).mutations() if is_run(run_id) else None
            if planted is not None:
                body["mutations"] = planted
            return JSONResponse(body)
        if suffix == "events":
            after = request.headers.get("Last-Event-ID", "0")
            if not after.isascii() or not after.isdecimal():
                return _problem(400, "Last-Event-ID must be a nonnegative sequence")

            def still_running():
                with lock:
                    record = live.get(run_id)
                if record is not None and record.status not in {"finished", "failed"}:
                    return True
                result = path / "RESULT.json"
                if not result.exists():
                    return False
                try:
                    return json.loads(result.read_text()).get("status") == "running"
                except ValueError:
                    return True  # being rewritten right now

            def fresh(seq):
                try:
                    return get_view(run_id).events(seq)
                except ValueError:
                    return []  # evidence mid-write; the next poll picks it up

            # Browsers (EventSource) ask for text/event-stream and get a live stream;
            # plain GETs get the ledger so far, once.
            live_stream = "text/event-stream" in request.headers.get("accept", "")

            def frame(entry):
                return f"id: {entry.seq}\nevent: ledger\ndata: {entry.model_dump_json()}\n\n"

            async def stream():
                # A running run keeps the stream open and pushes each step as it lands;
                # a finished run sends its ledger and closes.
                seq, polls = int(after), 0
                while True:
                    for entry in fresh(seq):
                        seq = entry.seq
                        yield frame(entry)
                    if not live_stream or not still_running():
                        for entry in fresh(seq):
                            seq = entry.seq
                            yield frame(entry)
                        if live_stream:
                            # Tell the browser the run is over, so it stops reconnecting.
                            yield "event: end\ndata: {}\n\n"
                        return
                    if await request.is_disconnected():
                        return
                    polls += 1
                    if polls % 10 == 0:
                        yield ": still running\n\n"
                    await asyncio.sleep(1.5)

            return StreamingResponse(stream(), media_type="text/event-stream")
        view = get_view(run_id)
        if suffix == "rootmap":
            try:
                return JSONResponse(view.rootmap())
            except LookupError:
                return _problem(404, "The Surveyor has not finished mapping this shop yet", NOT_YET)
        graft = view.graft()
        with lock:
            record = live.get(run_id)
            if record:
                graft = graft.model_copy(
                    update={"shop_id": record.graft.shop_id, "started_at": record.graft.started_at}
                )
                if record.status == "failed":
                    graft.card.notes["runner"] = "Runner failed; inspect the local run log"
        return JSONResponse(graft.model_dump(mode="json"))

    @app.middleware("http")
    async def integrated_runs(request: Request, call_next):
        path = request.url.path
        if request.method == "POST" and path == "/shops":
            body = await request.json()
            response = await call_next(request)
            content = b"".join([chunk async for chunk in response.body_iterator])
            if 200 <= response.status_code < 300:
                created = json.loads(content)
                shops[created["shop_id"]] = {k: body.get(k) for k in ("name", "repo", "site")}
                label = None if body.get("name") else _shop_label(body)
                if label:
                    # The stand-in names every unnamed shop "Legacy Shop"; name it after its repo.
                    created["name"] = label
                    content = json.dumps(created).encode()
            rebuilt = Response(
                content, status_code=response.status_code, background=response.background
            )
            rebuilt.raw_headers = [
                (k, v) for k, v in response.raw_headers if k.lower() != b"content-length"
            ] + [(b"content-length", str(len(content)).encode())]
            return rebuilt
        start_match = re.fullmatch(r"/shops/([^/]+)/graft", path)
        run_match = re.fullmatch(
            r"/grafts/([^/]+)(?:/(events|rootmap|scenarios|cmel|proof|changes|agents|connected|connected-proof))?",
            path,
        )
        is_start = (
            request.method == "POST"
            and start_match
            and live_enabled
            and any(
                admitted in str(shops.get(start_match[1], {}).get(field) or "").lower()
                for admitted in ("legacy-php-shop", "eval-nvp")
                for field in ("repo", "site", "name")
            )
        )
        is_read = (
            request.method == "GET"
            and run_match
            and directory(run_match[1]) is not None
            and (
                (directory(run_match[1]) / "RESULT.json").is_file()
                or run_match[1] in live
                or (
                    run_match[2] == "changes"
                    and (directory(run_match[1]) / "CHANGES.json").is_file()
                )
            )
        )
        is_listing = request.method == "GET" and path == "/runs"
        heal_match = re.fullmatch(r"/heal/([^/]+)(?:/inject-fault)?", path)
        gauntlet_match = re.fullmatch(r"/security/gauntlet/([^/]+)", path)
        special = None
        if heal_match and is_run(heal_match[1]):
            if "text/event-stream" in request.headers.get("accept", ""):
                # The browser's go-live feed: nothing to stream, so end it instead of retrying.
                special = lambda: Response(  # noqa: E731
                    "event: end\ndata: {}\n\n", media_type="text/event-stream"
                )
            else:
                special = lambda: _problem(404, NO_GOLIVE, NOT_YET)  # noqa: E731
        elif request.method == "GET" and gauntlet_match and is_run(gauntlet_match[1]):
            special = lambda: JSONResponse(gauntlet(gauntlet_match[1]))  # noqa: E731
        elif request.method == "GET" and path == "/recipes":
            special = lambda: JSONResponse(fleet_recipes())  # noqa: E731
        elif request.method == "GET" and path == "/orchard":
            special = lambda: JSONResponse(fleet_orchard())  # noqa: E731
        elif request.method == "POST" and path == "/orchard/ask":
            # The stand-in would answer about invented shops beside the real table.
            special = lambda: _problem(501, NO_ASK, NOT_YET)  # noqa: E731
        elif request.method == "GET" and gauntlet_match:
            # The stand-in security test stays, but says it is a sample in live mode.
            response = await call_next(request)
            content = b"".join([chunk async for chunk in response.body_iterator])
            if response.status_code == 200:
                data = json.loads(content)
                data.setdefault("label", "SYNTHETIC — stand-in security test, not a recording")
                content = json.dumps(data).encode()
            rebuilt = Response(content, status_code=response.status_code)
            rebuilt.raw_headers = [
                (k, v) for k, v in response.raw_headers if k.lower() != b"content-length"
            ] + [(b"content-length", str(len(content)).encode())]
            return rebuilt
        if not (is_listing or is_start or is_read or special):
            return await call_next(request)
        try:
            if is_listing:
                response = JSONResponse(await run_in_threadpool(list_runs))
            elif special:
                response = await run_in_threadpool(special)
            elif is_start:
                try:
                    body = await request.json()
                except ValueError:
                    response = _problem(422, "Request must be JSON")
                else:
                    response = start_live(request, start_match[1], body)
            else:
                # Serialize projections: a run's ledger and cache have one writer per app.
                response = read_run(request, run_match[1], run_match[2])
        except (ValueError, OSError, TypeError, KeyError):
            response = _problem(503, "Integrated run evidence is unavailable or failed validation")
        response.headers.setdefault("X-GoldGraft-Evidence-Class", EVIDENCE_CLASS)
        # Intercepted responses bypass the base application's CORS middleware.
        if "Origin" in request.headers:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "X-GoldGraft-Evidence-Class"
        return response

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8700)
    parser.add_argument("--host", default="127.0.0.1", help="0.0.0.0 on a hosted server")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args(argv)
    import uvicorn

    uvicorn.run(
        create_app(runs_dir=args.runs_dir, live_enabled=args.live), host=args.host, port=args.port
    )


if __name__ == "__main__":
    main()
