"""Herald uses real claim/metric checks; counterpart and projection are explicit fakes."""

import json
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta

import pytest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes.herald_profile import create_collaboration_profile
from goldgraft_fakes.offline_store import encoded

from pieces.agents.graph import advance_surveyor_herald
from pieces.agents.herald import (
    HeraldInputs,
    deterministic_renderer,
    inspect_text,
    notification_preview,
    render_text,
)
from pieces.agents.roles import herald_configuration, surveyor_configuration
from pieces.agents.runtime import run_task
from pieces.agents.scheduler import tick

from .test_runtime import NOW


def profile(tmp_path, *, projection="private_status", clock=None, **settings):
    config = dict(herald_configuration(projection=projection), **settings)
    return create_collaboration_profile(
        tmp_path / "herald.sqlite",
        configuration=surveyor_configuration(),
        herald_configuration=config,
        renderer=deterministic_renderer,
        clock=clock or (lambda: NOW),
    )


def source_ready(p):
    assert [t.task.task_id for t in p.control.snapshot("fake:runtime-run").tasks] == ["survey"]
    lease = p.control.claim("source-worker", p.clock())
    result = run_task(lease, p.control, p.artifacts, p.model, p.tools, now=p.clock())
    assert result.outcome == "completed"
    advance_surveyor_herald("fake:runtime-run", p)
    return p.control.snapshot("fake:runtime-run").tasks[1]


def execute(p):
    lease = p.control.claim("herald-worker", p.clock())
    assert lease.task_id == "herald"
    return run_task(lease, p.control, p.artifacts, p.model, p.tools, now=p.clock())


def turn_id(p, number):
    t = p.control.snapshot("fake:runtime-run").tasks[1]
    return "turn:" + content_digest(
        {
            "run": t.run_id,
            "generation": t.generation,
            "task": "herald",
            "attempt": 1,
            "turn": number,
        }
    )


def facts_for(p):
    task = p.control.snapshot("fake:runtime-run").tasks[1]
    with p.control.store.transaction() as db:
        from goldgraft_fakes.herald_profile import projection

        value = projection(p.control, db, task, p.herald_configuration)
    return task, HeraldInputs.model_validate(value)


def test_b4_surveyor_advances_to_herald_and_inspects_committed_text(tmp_path):
    state = tmp_path / "herald.sqlite"
    cmd = [sys.executable, "-m", "pieces.agents.cli"]
    args = ["--fixture", "surveyor_herald", "--state-file", str(state)]
    first = subprocess.run(cmd + ["run"] + args, capture_output=True, text=True)
    assert first.returncode == 0, first.stdout + first.stderr
    data = json.loads(first.stdout)
    assert [t["state"] for t in data["snapshot"]["tasks"]] == ["succeeded", "succeeded"]
    inspect = subprocess.run(cmd + ["inspect"] + args, capture_output=True, text=True)
    assert inspect.returncode == 0, inspect.stdout + inspect.stderr
    view = json.loads(inspect.stdout)
    assert "5 source indicators" in view["text"]
    assert view["authoritative_status_changed"] is False
    assert view["model_api_calls"] == 0


def test_current_b4_roles_advance_automatically_without_precomputed_future_refs(tmp_path):
    p = profile(tmp_path)
    assert len(p.control.snapshot("fake:runtime-run").tasks) == 1
    report = tick("fake:runtime-run", NOW, p)
    assert report.completed == 2
    snapshot = p.control.snapshot("fake:runtime-run")
    first, second = snapshot.tasks
    assert second.task.input_refs == first.output_refs
    assert second.task.expected_subject == first.task.expected_subject
    assert second.task.required is False
    assert p.model.total_dispatches() == 5
    assert p.tools.total_dispatches() == 8
    assert len(p.control.result("herald").evidence_refs) == 2
    payload, raw_facts = p.artifacts.inspect_herald(second, p.context_for("herald"))
    facts = HeraldInputs.model_validate(raw_facts)
    number = payload["numbers_used"][0]
    assert number["value"] == 5 and number["json_pointer"] == "/payload/source_indicators"
    assert number["entry_hash"] in facts.ledger_entries
    assert second.prompt_ref == "agent:herald-prompt:1"
    assert second.policy_ref == "agent:herald-policy:1"
    assert all(t.state == "succeeded" for t in snapshot.tasks)


@pytest.mark.parametrize(
    "status,phrase",
    [
        ("queued", "execution is not confirmed"),
        ("working", "not yet verified"),
        ("waiting_input", "waiting for required input"),
        ("held", "held until"),
        ("unknown", "outcome is unknown"),
        ("cancellation_pending", "termination is not yet confirmed"),
        ("cancelled", "earlier effects are not undone"),
        ("delivery_pending", "working merchant outcome is not yet verified"),
        ("synthetic_complete", "no live merchant completion is established"),
    ],
)
def test_supported_states_preserve_uncertainty_and_offline_limitations(tmp_path, status, phrase):
    p = profile(tmp_path, status=status)
    source_ready(p)
    result = execute(p)
    assert result.outcome == "completed"
    task = p.control.snapshot("fake:runtime-run").tasks[1]
    payload, value = p.artifacts.inspect_herald(task, p.context_for("herald"))
    assert phrase in payload["text"]
    assert "Source-only offline evidence" in payload["text"]
    assert payload["numbers_used"] == []
    assert (
        inspect_text(payload, HeraldInputs.model_validate(value))["authoritative_status_changed"]
        is False
    )


@pytest.mark.parametrize("kind", ["GRAFT_CARD", "PR_BODY", "HANDOFF", "VERDICT_EXPLAIN"])
def test_four_draft_formats_use_same_grounded_claims_without_publishing(tmp_path, kind):
    p = profile(tmp_path, kind=kind)
    source_ready(p)
    assert execute(p).outcome == "completed"
    task = p.control.snapshot("fake:runtime-run").tasks[1]
    payload, _ = p.artifacts.inspect_herald(task, p.context_for("herald"))
    assert payload["kind"] == kind
    assert "5 source indicators" in payload["text"]


@pytest.mark.parametrize(
    "reason,phrase",
    [
        ("SOURCE_MISSING", "source controller"),
        ("PROOF_MISSING", "from SH"),
        ("AUTHORITY_REVOKED", "through GU"),
        ("OUTCOME_UNKNOWN", "original request identity"),
        ("BUDGET_EXHAUSTED", "no extra call is authorised"),
        ("TERMINATION_PENDING", "confirm termination"),
        ("EXIT_PENDING", "exit evidence remains pending"),
    ],
)
def test_reason_catalog_names_the_next_owner_or_action(tmp_path, reason, phrase):
    p = profile(tmp_path, status="held", reason_code=reason)
    source_ready(p)
    assert execute(p).outcome == "completed"
    task = p.control.snapshot("fake:runtime-run").tasks[1]
    payload, _ = p.artifacts.inspect_herald(task, p.context_for("herald"))
    assert phrase in payload["text"]


@pytest.mark.parametrize(
    "status,reason",
    [
        ("inventory_ready", "SOURCE_MISSING"),
        ("cancelled", "TERMINATION_PENDING"),
        ("synthetic_complete", "OUTCOME_UNKNOWN"),
        ("unknown", "SOURCE_MISSING"),
    ],
)
def test_conflicting_status_and_reason_hold_before_herald_model(tmp_path, status, reason):
    p = profile(tmp_path, status=status, reason_code=reason)
    source_ready(p)
    result = execute(p)
    assert result.outcome == "blocked"
    assert p.model.total_dispatches() == 3


def test_high_score_or_pr_without_exact_independent_proof_cannot_be_review_ready(tmp_path):
    p = profile(tmp_path, status="review_ready")
    source_ready(p)
    result = execute(p)
    assert result.outcome == "blocked"
    assert result.issue.code == "MISSING_EVIDENCE"
    assert result.output_refs == []
    assert p.model.total_dispatches() == 3


@pytest.mark.parametrize(
    "text",
    [
        "All safe. The merchant upgrade is complete.",
        "The PR proves delivery is done.",
        "Signed proof guarantees payment correctness.",
        "Inventory contains 99 source indicators.",
        "Saved 100 dollars.",
        "Private case-demo is complete.",
        "<script>fetch('https://outside.invalid')</script>",
    ],
)
def test_unsupported_claims_numbers_ids_and_html_are_not_accepted(tmp_path, text):
    p = profile(tmp_path)
    source_ready(p)
    task, facts = facts_for(p)
    payload = render_text(task, facts)
    payload["text"] = text
    p.model.script(turn_id(p, 1), {"kind": "final", "payload": payload})
    result = execute(p)
    assert result.outcome == "blocked"
    assert result.output_refs == []
    assert p.control.snapshot("fake:runtime-run").tasks[0].state == "succeeded"


@pytest.mark.parametrize(
    "tool,args",
    [
        (
            "source.read",
            {"snapshot_ref": "fake:survey-source", "path": "checkout.php", "max_bytes": 4096},
        ),
        ("evidence.read", {"ref": "fake:capture", "max_bytes": 4096}),
        ("status.read", {"run_ref": "fake:other-run"}),
        ("evidence.summary", {"run_ref": "fake:runtime-run", "projection": "public_safe"}),
        ("host.shell", {"command": "unsafe"}),
    ],
)
def test_wrong_role_tool_and_projection_do_not_dispatch(tmp_path, tool, args):
    p = profile(tmp_path)
    source_ready(p)
    p.model.script(
        turn_id(p, 0), {"kind": "tool_calls", "calls": [{"tool": tool, "arguments": args}]}
    )
    result = execute(p)
    assert result.outcome == "blocked"
    assert p.tools.total_dispatches() == 6


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", "wrong-case"),
        ("run_id", "wrong-run"),
        ("generation", 2),
        ("subject_digest", "e" * 64),
        ("producer_identity_ref", "fake:role:Herald"),
    ],
)
def test_wrong_predecessor_binding_denies_before_herald_model(tmp_path, field, value):
    p = profile(tmp_path)
    source_ready(p)
    source = p.control.snapshot("fake:runtime-run").tasks[0]
    with p.control.store.transaction() as db:
        row = db.execute(
            "SELECT descriptor FROM artifacts WHERE ref=?", (source.output_refs[0],)
        ).fetchone()
        descriptor = json.loads(row[0])
        descriptor[field] = value
        db.execute(
            "UPDATE artifacts SET descriptor=? WHERE ref=?",
            (encoded(descriptor), source.output_refs[0]),
        )
    result = execute(p)
    assert result.outcome == "blocked"
    assert p.model.total_dispatches() == 3


def test_missing_projection_journal_cannot_be_invented_by_model(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    with p.control.store.transaction() as db:
        db.execute("DELETE FROM scripts WHERE namespace='herald-journal'")
    result = execute(p)
    assert result.outcome == "blocked" and result.issue.code == "MISSING_EVIDENCE"
    assert p.model.total_dispatches() == 3


@pytest.mark.parametrize(
    "change", ["value", "hash", "pointer", "missing", "bool", "float", "wrong_owner", "wrong_graft"]
)
def test_numeric_and_payload_identity_tampering_cannot_complete(tmp_path, change):
    p = profile(tmp_path)
    source_ready(p)
    task, facts = facts_for(p)
    payload = render_text(task, facts)
    if change == "value":
        payload["numbers_used"][0]["value"] = 99
    elif change == "hash":
        payload["numbers_used"][0]["entry_hash"] = "f" * 64
    elif change == "pointer":
        payload["numbers_used"][0]["json_pointer"] = "/payload/money_saved"
    elif change == "missing":
        payload["numbers_used"] = []
    elif change == "bool":
        payload["numbers_used"][0]["value"] = True
    elif change == "float":
        payload["numbers_used"][0]["value"] = 5.0
    elif change == "wrong_owner":
        payload["producer"]["name"] = "Surveyor"
    else:
        payload["graft_id"] = "other-run"
    p.model.script(turn_id(p, 1), {"kind": "final", "payload": payload})
    p.model.script(turn_id(p, 2), {"kind": "final", "payload": payload})
    result = execute(p)
    assert result.outcome == "blocked"
    assert result.output_refs == []


def test_shared_acceptance_requires_resolved_numeric_context(tmp_path):
    from goldgraft_contracts.plan5_validation import ArtifactBinding, validate_artifact

    from pieces.agents.herald import validation_context

    p = profile(tmp_path)
    assert tick("fake:runtime-run", NOW, p).completed == 2
    task, facts = facts_for(p)
    d = p.artifacts.resolve(task.output_refs[0], p.context_for("herald"))
    payload, _ = p.artifacts.inspect_herald(task, p.context_for("herald"))
    binding = ArtifactBinding(
        "offline",
        task.case_id,
        task.run_id,
        task.generation,
        d.subject_digest,
        task.input_digest,
        "HeraldText/1",
        "fake:role:Herald",
        "Herald",
        frozenset({"model_proposal"}),
    )
    with pytest.raises(ValueError):
        validate_artifact(
            d,
            encoded(payload).encode(),
            binding,
            authenticated_tenant="offline",
            authenticated_producer="fake:role:Herald",
            now=NOW,
        )
    checked = validate_artifact(
        d,
        encoded(payload).encode(),
        binding,
        authenticated_tenant="offline",
        authenticated_producer="fake:role:Herald",
        now=NOW,
        validation_context=validation_context(facts),
    )
    assert checked.numbers_used[0].value == 5


def test_changed_projection_journal_cannot_support_unsigned_number(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    with p.control.store.transaction() as db:
        row = db.execute("SELECT id,body FROM scripts WHERE namespace='herald-journal'").fetchone()
        entry = json.loads(row[1])
        entry["payload"]["source_indicators"] = 999
        db.execute(
            "UPDATE scripts SET body=? WHERE namespace='herald-journal' AND id=?",
            (encoded(entry), row[0]),
        )
    assert execute(p).outcome == "blocked"
    assert p.model.total_dispatches() == 3


@pytest.mark.parametrize(
    "field,value",
    [
        ("producer_identity_ref", "fake:role:Surveyor"),
        ("subject_digest", "f" * 64),
    ],
)
def test_wrong_herald_output_owner_and_subject_are_rejected(tmp_path, field, value):
    p = profile(tmp_path)
    source_ready(p)
    stage = p.artifacts.stage

    def bad_stage(*args):
        ref = stage(*args)
        with p.control.store.transaction() as db:
            row = db.execute("SELECT descriptor FROM artifacts WHERE ref=?", (ref,)).fetchone()
            descriptor = json.loads(row[0])
            descriptor[field] = value
            db.execute("UPDATE artifacts SET descriptor=? WHERE ref=?", (encoded(descriptor), ref))
        return ref

    p.artifacts.stage = bad_stage
    assert execute(p).outcome == "blocked"
    assert p.control.snapshot("fake:runtime-run").tasks[1].output_refs == []


def test_public_view_and_herald_context_exclude_raw_sources_and_private_output_ids(tmp_path):
    p = profile(tmp_path, projection="public_safe")
    assert tick("fake:runtime-run", NOW, p).completed == 2
    task = p.control.snapshot("fake:runtime-run").tasks[1]
    payload, value = p.artifacts.inspect_herald(task, p.context_for("herald"))
    view = encoded(inspect_text(payload, HeraldInputs.model_validate(value)))
    assert "5 source indicators" in view
    assert all(
        word not in view
        for word in ["case-demo", "run-demo", "fake:", "entry_hash", "checkout.php"]
    )
    with p.control.store.transaction() as db:
        for row in db.execute("SELECT request FROM model_turns WHERE task_id='herald'"):
            request = json.loads(row[0])
            context = db.execute(
                "SELECT body FROM contexts WHERE ref=?", (request["context_ref"],)
            ).fetchone()[0]
            assert (
                "checkout.php" not in context
                and "<?php" not in context
                and '"excerpt"' not in context
            )


def test_asset_dispositions_and_preview_are_bounded_and_do_not_send(tmp_path):
    p = profile(
        tmp_path,
        retained=["application_state"],
        removed=["temporary_access"],
        pending=["callback_handler"],
    )
    source_ready(p)
    assert execute(p).outcome == "completed"
    task, facts = facts_for(p)
    text = render_text(task, facts)["text"]
    assert "Retained: application state" in text
    assert "Removed: temporary service access" in text
    assert "Pending: callback handler" in text
    assert notification_preview(facts) is None
    first = notification_preview(facts, opted_in=True)
    assert first == notification_preview(facts, opted_in=True)
    assert first["delivery"] == "NOT SENT" and first["authority"] == "NONE"


def test_notification_preview_key_is_shared_across_draft_formats(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    _task, facts = facts_for(p)
    first = notification_preview(facts, opted_in=True)
    second = notification_preview(facts.model_copy(update={"kind": "HANDOFF"}), opted_in=True)
    assert first == second


def test_conflicting_asset_dispositions_hold_before_model(tmp_path):
    p = profile(tmp_path, retained=["application_state"], removed=["application_state"])
    source_ready(p)
    assert execute(p).outcome == "blocked"
    assert p.model.total_dispatches() == 3


def test_fallback_is_available_without_a_model_and_does_not_change_state(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    task, facts = facts_for(p)
    before = p.control.snapshot("fake:runtime-run").model_dump(mode="json")
    assert "5 source indicators" in render_text(task, facts)["text"]
    assert "Status update:" in render_text(task, facts, detailed=True)["text"]
    assert p.control.snapshot("fake:runtime-run").model_dump(mode="json") == before
    assert p.model.total_dispatches() == 3


@pytest.mark.parametrize("change", ["owner", "graft", "float", "numbers", "kind"])
def test_inspection_view_rechecks_payload_claim_and_identity(tmp_path, change):
    p = profile(tmp_path)
    source_ready(p)
    task, facts = facts_for(p)
    payload = render_text(task, facts)
    if change == "owner":
        payload["producer"]["name"] = "Surveyor"
    elif change == "graft":
        payload["graft_id"] = "other-run"
    elif change == "float":
        payload["numbers_used"][0]["value"] = 5.0
    elif change == "numbers":
        payload["numbers_used"] = []
    else:
        payload["kind"] = "PR_BODY"
    with pytest.raises(ValueError):
        inspect_text(payload, facts)


def test_unknown_herald_model_holds_only_optional_text_and_retains_identity(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    p.model.script(turn_id(p, 0), {"unknown": True})
    assert execute(p).outcome == "unknown"
    fresh = profile(tmp_path)
    assert tick("fake:runtime-run", NOW, fresh).claimed == 0
    assert fresh.model.total_dispatches() == 4
    assert fresh.control.snapshot("fake:runtime-run").tasks[0].state == "succeeded"
    task, facts = facts_for(fresh)
    assert "5 source indicators" in render_text(task, facts)["text"]


def test_changed_projection_during_reads_does_not_accept_stale_text(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    invoke = p.tools.invoke

    def changed(invocation):
        result = invoke(invocation)
        p.herald_configuration["status"] = "held"
        return result

    wrapped = replace(
        p,
        tools=type(
            "ChangingTools", (), {"invoke": staticmethod(changed), "reconcile": p.tools.reconcile}
        )(),
    )
    result = execute(wrapped)
    assert result.outcome == "blocked" and result.issue.code == "STALE"


def test_stop_before_herald_prevents_model_and_output(tmp_path):
    p = profile(tmp_path)
    source_ready(p)
    p.control.cancel("fake:runtime-run", "fake:stop")
    assert tick("fake:runtime-run", NOW, p).claimed == 0
    assert p.model.total_dispatches() == 3
    assert p.control.snapshot("fake:runtime-run").tasks[1].output_refs == []


def test_reordered_and_duplicate_events_do_not_repeat_explanations(tmp_path):
    p = profile(tmp_path)
    assert tick("fake:runtime-run", NOW, p).completed == 2
    events = p.control.outbox("fake:runtime-run")
    for event in reversed(events + events):
        p.control.ack_event(event.event_id)
    assert tick("fake:runtime-run", NOW, p).claimed == 0
    assert p.model.total_dispatches() == 5 and p.tools.total_dispatches() == 8


def test_missing_surveyor_prerequisite_never_admits_herald(tmp_path):
    p = profile(tmp_path)
    ticket = p.artifacts.ticket
    p.artifacts.ticket = lambda lease: replace(ticket(lease), operation=None)
    assert tick("fake:runtime-run", NOW, p).completed == 0
    snapshot = p.control.snapshot("fake:runtime-run")
    assert len(snapshot.tasks) == 1 and snapshot.tasks[0].state == "held"
    assert p.model.total_dispatches() == 0


def test_zero_indicator_source_uses_real_committed_count_without_a_model(tmp_path):
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    inputs = package_from_sources(
        shop_id="empty-indicators", files={"index.php": "<?php echo 'sample';"}
    )
    configuration = dict(
        surveyor_configuration(), offline_final_payload=build_static_inventory(inputs)
    )
    p = create_collaboration_profile(
        tmp_path / "zero.sqlite",
        configuration=configuration,
        herald_configuration=herald_configuration(),
        renderer=deterministic_renderer,
        inputs=inputs,
        clock=lambda: NOW,
    )
    assert tick("fake:runtime-run", NOW, p).completed == 2
    task, facts = facts_for(p)
    assert "0 source indicators" in render_text(task, facts)["text"]
    assert next(iter(facts.ledger_entries.values())).payload["source_indicators"] == 0


def test_restart_between_source_commit_and_graph_extension_advances_automatically(tmp_path):
    state = tmp_path / "gap.sqlite"
    setup = """
import os,sys
from datetime import UTC,datetime
from goldgraft_fakes.herald_profile import create_collaboration_profile
from pieces.agents.roles import surveyor_configuration,herald_configuration
from pieces.agents.herald import deterministic_renderer
from pieces.agents.runtime import run_task
now=datetime(2026,11,10,12,tzinfo=UTC)
p=create_collaboration_profile(sys.argv[1],configuration=surveyor_configuration(),
  herald_configuration=herald_configuration(),renderer=deterministic_renderer,clock=lambda:now)
lease=p.control.claim('source',now)
def fault(point):
    if point=='after_finish':os._exit(73)
run_task(lease,p.control,p.artifacts,p.model,p.tools,now=now,fault=fault)
"""
    process = subprocess.run(
        [sys.executable, "-c", setup, str(state)], capture_output=True, text=True
    )
    assert process.returncode == 73, process.stdout + process.stderr
    fresh = create_collaboration_profile(
        state,
        configuration=surveyor_configuration(),
        herald_configuration=herald_configuration(),
        renderer=deterministic_renderer,
        clock=lambda: NOW + timedelta(seconds=61),
    )
    assert len(fresh.control.snapshot("fake:runtime-run").tasks) == 1
    assert tick("fake:runtime-run", fresh.clock(), fresh).completed == 1
    assert [t.state for t in fresh.control.snapshot("fake:runtime-run").tasks] == [
        "succeeded",
        "succeeded",
    ]
    assert fresh.model.total_dispatches() == 5


@pytest.mark.parametrize(
    "boundary",
    ["before_model", "after_model", "before_tool", "after_tool", "before_finish", "after_finish"],
)
def test_herald_process_crash_recovers_original_identities(tmp_path, boundary):
    state = tmp_path / "crash.sqlite"
    code = """
import json,os,sys
from datetime import UTC,datetime
from goldgraft_fakes.herald_profile import create_collaboration_profile
from pieces.agents.roles import surveyor_configuration,herald_configuration
from pieces.agents.herald import deterministic_renderer
from pieces.agents.runtime import run_task
from pieces.agents.graph import advance_surveyor_herald
now=datetime(2026,11,10,12,tzinfo=UTC)
p=create_collaboration_profile(sys.argv[1],configuration=surveyor_configuration(),herald_configuration=herald_configuration(),renderer=deterministic_renderer,clock=lambda:now)
lease=p.control.claim('source',now)
run_task(lease,p.control,p.artifacts,p.model,p.tools,now=now)
advance_surveyor_herald('fake:runtime-run',p)
lease=p.control.claim('herald',now)
def fault(point):
    if point==sys.argv[2]:os._exit(73)
run_task(lease,p.control,p.artifacts,p.model,p.tools,now=now,fault=fault)
"""
    process = subprocess.run(
        [sys.executable, "-c", code, str(state), boundary], capture_output=True, text=True
    )
    assert process.returncode == 73, process.stdout + process.stderr
    recovery = """
import json,sys
from datetime import UTC,datetime
from goldgraft_fakes.herald_profile import create_collaboration_profile
from pieces.agents.roles import surveyor_configuration,herald_configuration
from pieces.agents.herald import deterministic_renderer
from pieces.agents.scheduler import tick
now=datetime(2026,11,10,12,1,1,tzinfo=UTC)
p=create_collaboration_profile(sys.argv[1],configuration=surveyor_configuration(),herald_configuration=herald_configuration(),renderer=deterministic_renderer,clock=lambda:now)
tick('fake:runtime-run',now,p)
with p.control.store.transaction() as db:
    mm=db.execute('SELECT MAX(dispatch_count) FROM model_turns').fetchone()[0]
    tm=db.execute('SELECT MAX(dispatch_count) FROM tools').fetchone()[0]
snapshot=p.control.snapshot('fake:runtime-run')
print(json.dumps({'states':[t.state for t in snapshot.tasks],
                 'models':p.model.total_dispatches(),'tools':p.tools.total_dispatches(),
                 'mm':mm,'tm':tm}))
"""
    process = subprocess.run(
        [sys.executable, "-c", recovery, str(state)], capture_output=True, text=True
    )
    assert process.returncode == 0, process.stdout + process.stderr
    data = json.loads(process.stdout)
    assert data["mm"] <= 1 and data["tm"] <= 1
    if boundary == "before_tool":
        assert data["states"] == ["succeeded", "held"] and data["tools"] == 6
    else:
        assert data["states"] == ["succeeded", "succeeded"]
        assert data["models"] == 5 and data["tools"] == 8
