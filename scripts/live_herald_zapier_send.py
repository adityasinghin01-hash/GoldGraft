"""Opt-in: send ONE Herald notification about a real Surveyor result through Zapier.

Composition only: a real accepted Surveyor inventory (no new inference) is replayed
through the actual runtime and deterministic Herald; the unsent preview goes to the
local evaluation sender. --dry-run uses a scripted 200 response (no network).
Never prints or stores the hook URL. Notifications are not approvals.
"""

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_fakes.herald_profile import create_collaboration_profile, projection

from pieces.agents.evals.surveyor import load_cases
from pieces.agents.herald import HeraldInputs, deterministic_renderer, notification_preview
from pieces.agents.roles import herald_configuration, surveyor_configuration
from pieces.agents.scheduler import tick
from pieces.agents.source_inventory import package_from_sources
from pieces.backend.notifications.zapier_eval import ZapierSender, https_post

GATEWAY = Path.home() / "reports/goldgraft-model-gateway-20261111"
EVIDENCE = Path.home() / "reports/goldgraft-herald-qualification-20261111/zapier"
CATALOGS = [
    GATEWAY / "continuation-04/c04_model_cases.json",
    GATEWAY / "continuation-05/c05_ceiling_cases.json",
]


def event_time(report):
    """The logical event is the committed Surveyor result: its time is the latest
    recorded provider observation, never the wall clock of this replay."""
    stamps = [
        (turn.get("provider_observation") or {}).get("body", {}).get("recorded_at_utc")
        for turn in report["turns"]
    ]
    stamps = [s for s in stamps if isinstance(s, str)]
    if not stamps:
        raise ValueError("MISSING_EVIDENCE result time")
    return max(datetime.fromisoformat(s) for s in stamps)


def preview_for(report, case, view):
    if not report["passed"]:
        raise ValueError("DENIED unaccepted Surveyor result")
    inputs = package_from_sources(shop_id=case["shop_id"], files=case["files"])
    now = event_time(report)
    with tempfile.TemporaryDirectory() as tmp:
        p = create_collaboration_profile(
            Path(tmp) / "h.sqlite",
            configuration=dict(surveyor_configuration(), offline_final_payload=report["inventory"]),
            herald_configuration=herald_configuration(projection=view),
            renderer=deterministic_renderer,
            inputs=inputs,
            clock=lambda: now,
        )
        if tick("fake:runtime-run", now, p).completed != 2:
            raise ValueError("MISSING_EVIDENCE Surveyor/Herald did not complete")
        task = p.control.snapshot("fake:runtime-run").tasks[1]
        with p.control.store.transaction() as db:
            facts = HeraldInputs.model_validate(
                projection(p.control, db, task, p.herald_configuration)
            )
    return notification_preview(facts, opted_in=True)


def herald_preview(batch, view):
    report = json.loads((GATEWAY / "live" / batch / "result.json").read_text())
    cases = {c["id"]: c for path in CATALOGS for c in load_cases(path)}
    return preview_for(report, cases[report["case_id"]], view)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", default="s5-c05-max-package-c3")
    parser.add_argument(
        "--projection", choices=["private_status", "public_safe"], default="private_status"
    )
    parser.add_argument("--opt-in", metavar="DESTINATION_LABEL")
    parser.add_argument("--opt-out", action="store_true")
    args = parser.parse_args(argv)
    if args.live == args.dry_run:
        parser.error("choose exactly one of --live or --dry-run")
    post = https_post
    outbox = EVIDENCE / "outbox.sqlite"
    hook = Path.home() / ".config/goldgraft/zapier.env"
    if args.dry_run:
        tmp = Path(tempfile.mkdtemp())
        outbox, hook = tmp / "outbox.sqlite", tmp / "zapier.env"
        hook.write_text("ZAPIER_HOOK_URL=https://hooks.zapier.com/hooks/catch/1/dryrun/\n")
        hook.chmod(0o600)

        def post(url, body, timeout):  # noqa: ARG001 - scripted 200, no network
            return 200, b'{"status":"success","id":"dryrun"}'

    sender = ZapierSender(outbox, hook, post=post)
    if args.opt_out:
        sender.opt_out()
        print(json.dumps({"opted_in": False}))
        return 0
    if args.opt_in:
        sender.opt_in(args.opt_in)
    preview = herald_preview(args.batch, args.projection)
    result = sender.send(preview)
    record = {
        "at_utc": datetime.now(UTC).isoformat(),
        "mode": "live" if args.live else "dry_run",
        "surveyor_batch": args.batch,
        "projection": args.projection,
        "event_key": preview["event_key"],
        "text": preview["text"],
        "state": result["state"],
        "attempts": result["attempts"],
        "http_status": result["last_status"],
        "receipt": json.loads(result["receipt"]) if result.get("receipt") else None,
        "deduplicated": bool(result.get("deduplicated")),
        "model_api_calls": 0,
    }
    if args.live:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        with (EVIDENCE / "SENDS.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
    print(json.dumps(record, ensure_ascii=False))
    return 0 if result["state"] == "sent" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(
            json.dumps(
                {"outcome": "held", "reason": str(error).split()[0] if str(error) else "ERROR"}
            )
        )
        raise SystemExit(1) from None
