"""Local v1 API for real-model evidence; live dispatch requires explicit opt-in.

Run with ``.venv/bin/python -m integration.agents_app --port 8700 [--live]``.
All other requests retain the strictly offline fixture application's behaviour.
"""

import argparse
import asyncio
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
from goldgraft_contracts.api import Graft, StartGraftRequest
from starlette.concurrency import run_in_threadpool

from integration.agent_views import IntegratedRunViews
from integration.app import create_app as offline_app

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = Path.home() / "reports/goldgraft-agents-integration-20261112/runs"
GATEWAY_PYTHON = Path("/Users/aditya/reports/goldgraft-model-gateway-20261111/venv/bin/python")
EVIDENCE_CLASS = "real-models-scripted-runner"
NO_PROOF = (
    "scripted runner evidence is not served for real agent runs; independent proof not run yet"
)
log = logging.getLogger(__name__)


def _problem(status, detail):
    return JSONResponse(
        {"type": "about:blank", "title": "Request Failed", "status": status, "detail": detail},
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

    def read_run(request, run_id, suffix):
        path = directory(run_id)
        if suffix == "scenarios":
            # Honest and quiet: no payment scenarios have run on real agent code yet.
            return JSONResponse({"graft_id": run_id, "scenarios": []})
        if suffix in {"cmel", "proof"}:
            return _problem(404, NO_PROOF)
        if suffix == "changes":
            changes = path / "CHANGES.json"
            if not changes.is_file():
                return _problem(404, "No committed CHANGES.json for this run yet")
            return Response(changes.read_bytes(), media_type="application/json")
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
                return _problem(404, "No committed RootMap yet")
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
            rebuilt = Response(
                content, status_code=response.status_code, background=response.background
            )
            rebuilt.raw_headers = response.raw_headers
            return rebuilt
        start_match = re.fullmatch(r"/shops/([^/]+)/graft", path)
        run_match = re.fullmatch(
            r"/grafts/([^/]+)(?:/(events|rootmap|scenarios|cmel|proof|changes))?", path
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
        if not (is_listing or is_start or is_read):
            return await call_next(request)
        try:
            if is_listing:
                response = JSONResponse(await run_in_threadpool(list_runs))
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
        response.headers["X-GoldGraft-Evidence-Class"] = EVIDENCE_CLASS
        # Intercepted responses bypass the base application's CORS middleware.
        if "Origin" in request.headers:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "X-GoldGraft-Evidence-Class"
        return response

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8700)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args(argv)
    import uvicorn

    uvicorn.run(
        create_app(runs_dir=args.runs_dir, live_enabled=args.live), host="127.0.0.1", port=args.port
    )


if __name__ == "__main__":
    main()
