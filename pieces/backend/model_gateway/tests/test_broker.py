"""Real gateway orchestration with a controlled provider, never network inference."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from goldgraft_contracts.agent_runtime import ModelTurnRequest
from goldgraft_contracts.plan5_common import content_digest


class Boundary:
    def __init__(self):
        self.current = True
        self.context = {
            "prompt": "Read synthetic source only.",
            "policy": {"approved": True},
            "observations": [],
        }
        self.blobs = {}

    def check(self, scope):
        if not self.current or scope["task_id"] != "survey":
            raise ValueError("STALE")

    def context_bytes(self, request):
        self.check({"task_id": request.task_id})
        return self.context

    def stage(self, payload):
        ref = "test:blob:" + content_digest(payload)
        self.blobs[ref] = payload
        return ref


class Provider:
    def __init__(self, *, unknown=False):
        self.calls = 0
        self.unknown = unknown

    def count(self, wire):
        return 100

    def generate(self, wire):
        self.calls += 1
        if self.unknown:
            raise TimeoutError("untrusted provider body must never be logged")
        return {
            "id": "msg_test",
            "model": "claude-haiku-5-5",
            "content": [
                {
                    "type": "tool_use",
                    "id": "call1",
                    "name": "source_read",
                    "input": {"snapshot_ref": "test:source", "path": "a.php", "max_bytes": 64},
                }
            ],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        }


def setup(tmp_path, *, unknown=False):
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile

    boundary, provider = Boundary(), Provider(unknown=unknown)
    gateway = Gateway(Ledger(tmp_path / "money.sqlite"), tmp_path / "signing", Profile(), provider)
    scope = {
        "task_id": "survey",
        "case_id": "case",
        "run_id": "run",
        "generation": 1,
        "lease_epoch": 1,
        "input_digest": "a" * 64,
        "subject": "b" * 64,
        "prompt_digest": content_digest(boundary.context["prompt"]),
        "policy_digest": content_digest(boundary.context["policy"]),
        "deadline": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        "allowed_tools": ["source.read"],
        "role": "Surveyor",
    }
    grant = gateway.grant("batch", scope)
    port = gateway.port(grant, boundary)
    request = ModelTurnRequest(
        turn_id="turn",
        task_id="survey",
        generation=1,
        lease_epoch=1,
        model_profile_ref=gateway.profile.ref,
        context_ref="test:context",
        context_digest=content_digest(boundary.context),
        allowed_tool_ids=["source.read"],
        output_schema="RootMap/1",
        input_token_cap=24000,
        output_token_cap=1536,
        budget_reservation_ref="batch",
        deadline=datetime.fromisoformat(scope["deadline"]),
    )
    return gateway, port, boundary, provider, request


def test_actual_port_stages_untrusted_tools_and_reconciles_without_dispatching_twice(tmp_path):
    gateway, port, boundary, provider, request = setup(tmp_path)
    result = port.turn(request)
    assert result.calls[0].tool == "source.read"
    assert boundary.blobs[result.calls[0].arguments_ref]["path"] == "a.php"
    assert port.reconcile("turn").state == "observed"
    assert port.turn(request) == result
    assert provider.calls == 1
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 20


@pytest.mark.parametrize("change", ["signature", "generation", "context", "tool", "stale"])
def test_forged_or_stale_scope_never_reaches_provider(tmp_path, change):
    _, port, boundary, provider, request = setup(tmp_path)
    if change == "signature":
        port.grant["signature"] = "forged"
    elif change == "generation":
        request = request.model_copy(update={"generation": 2})
    elif change == "context":
        boundary.context["prompt"] = "changed"
    elif change == "tool":
        request = request.model_copy(update={"allowed_tool_ids": ["candidate.patch"]})
    else:
        boundary.current = False
    with pytest.raises(ValueError):
        port.turn(request)
    assert provider.calls == 0


def test_unknown_call_is_retained_and_cannot_be_replaced(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path, unknown=True)
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    assert port.reconcile("turn").state == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request.model_copy(update={"turn_id": "replacement"}))
    assert provider.calls == 1
    assert gateway.ledger.snapshot()["unknown_micro_usd"] > 0


def test_failed_dispatch_keeps_only_safe_signed_diagnostics_across_restart(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.provider import ProviderFailure

    gateway, port, _, provider, request = setup(tmp_path)

    def failure(wire):
        raise ProviderFailure({"category": "http_error", "status": 400, "request_id": "req_test"})

    provider.generate = failure
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    row = Ledger(gateway.ledger.path).turn("batch", "turn")
    diagnostic = row["provider_observation"]
    assert diagnostic["body"]["failure"] == {
        "category": "http_error",
        "status": 400,
        "request_id": "req_test",
    }
    assert diagnostic["signature"] == gateway.signature(diagnostic["body"])
    assert row["state"] == "unknown"
    assert gateway.ledger.snapshot()["unknown_micro_usd"] == gateway.profile.turn_reservation


def test_rate_reset_metadata_survives_restart_without_clearing_unknown(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.provider import ProviderFailure

    gateway, port, _, provider, request = setup(tmp_path)
    calls = []

    def limited(wire):
        calls.append(1)
        raise ProviderFailure(
            {
                "category": "http_error",
                "status": 429,
                "request_id": "req_rate",
                "retry_after_seconds": 0,
            }
        )

    provider.generate = limited
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    before = gateway.ledger.snapshot()
    gateway.ledger = Ledger(gateway.ledger.path)
    body = gateway.ledger.turn("batch", "turn")["provider_observation"]["body"]
    assert datetime.fromisoformat(body["recorded_at_utc"]).tzinfo is not None
    assert body["failure"]["retry_after_seconds"] == 0
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request.model_copy(update={"turn_id": "new-after-reset"}))
    assert calls == [1] and gateway.ledger.snapshot() == before


def test_signed_http_400_can_resolve_as_rejected_without_inventing_token_usage(tmp_path):
    from pieces.backend.model_gateway.provider import ProviderFailure

    gateway, port, _, provider, request = setup(tmp_path)

    def rejected(wire):
        raise ProviderFailure(
            {"category": "http_error", "status": 400, "request_id": "req_rejected"}
        )

    provider.generate = rejected
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    proof = gateway.reconcile_rejected("batch", request.turn_id)
    assert proof["body"]["charge_micro_usd"] == 0
    assert proof["body"]["token_usage"] is None
    assert proof["signature"] == gateway.signature(proof["body"])
    assert gateway.ledger.turn("batch", request.turn_id)["state"] == "failed"
    assert gateway.reconcile_rejected("batch", request.turn_id) == proof
    gateway.ledger.close("batch")
    assert gateway.ledger.snapshot()["reserved_micro_usd"] == 0


@pytest.mark.parametrize("fault", ["missing", "tampered", "no-id", "timeout", "other-status"])
def test_rejection_reconciliation_cannot_release_uncertain_or_unattributed_calls(tmp_path, fault):
    import json

    from pieces.backend.model_gateway.provider import ProviderFailure

    gateway, port, _, provider, request = setup(tmp_path)

    def rejected(wire):
        raise ProviderFailure(
            {
                "category": "timeout" if fault == "timeout" else "http_error",
                "status": 500 if fault == "other-status" else 400,
                "request_id": None if fault == "no-id" else "req_test",
            }
        )

    provider.generate = rejected
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    if fault in {"missing", "tampered"}:
        record = gateway.ledger.turn("batch", request.turn_id)["provider_observation"]
        with gateway.ledger.transaction() as db:
            if fault == "missing":
                db.execute("DELETE FROM provider_observations")
            else:
                record["body"]["failure"]["status"] = 400
                record["signature"] = "0" * 64
                db.execute("UPDATE provider_observations SET record=?", (json.dumps(record),))
    before = gateway.ledger.snapshot()
    with pytest.raises(ValueError, match="REJECTION"):
        gateway.reconcile_rejected("batch", request.turn_id)
    assert gateway.ledger.snapshot() == before


def test_unqualified_response_preserves_usage_metadata_without_false_pricing(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def different_model(wire):
        response = original(wire)
        response["model"] = "claude-unqualified"
        response["request_id"] = "req_test"
        response["content"].append({"type": "text", "text": "untrusted body never recorded"})
        return response

    provider.generate = different_model
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    row = gateway.ledger.turn("batch", "turn")
    diagnostic = row["provider_observation"]
    assert diagnostic["body"]["response"]["usage"]["input_tokens"] == 100
    assert diagnostic["body"]["response"]["model"] == "claude-unqualified"
    assert "untrusted body" not in str(diagnostic)
    assert diagnostic["signature"] == gateway.signature(diagnostic["body"])
    assert row["state"] == "unknown" and row["actual"] == 0


def test_unrequested_fast_usage_cannot_be_priced_as_standard(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def fast(wire):
        response = original(wire)
        response["usage"]["speed"] = "fast"
        return response

    provider.generate = fast
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    assert gateway.ledger.turn("batch", request.turn_id)["state"] == "unknown"
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 0


def test_stop_prevents_dispatch_and_does_not_erase_reservation(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    gateway.ledger.stop("batch")
    with pytest.raises(ValueError, match="STOPPED"):
        port.turn(request)
    assert provider.calls == 0


def test_provider_cannot_widen_native_tool_scope(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def malicious(wire):
        response = original(wire)
        response["content"][0]["name"] = "host_shell"
        return response

    provider.generate = malicious
    result = port.turn(request)
    assert result.kind == "blocked" and result.issue.code == "INVALID_MODEL_OUTPUT"
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 20


def test_new_context_hash_cannot_replace_the_signed_prompt(tmp_path):
    _, port, boundary, provider, request = setup(tmp_path)
    boundary.context["prompt"] = "unapproved replacement"
    request = request.model_copy(update={"context_digest": content_digest(boundary.context)})
    with pytest.raises(ValueError, match="DENIED"):
        port.turn(request)
    assert provider.calls == 0


def test_tampered_persisted_response_is_not_a_valid_reconciliation_receipt(tmp_path):
    gateway, port, _, _, request = setup(tmp_path)
    result = port.turn(request)
    with gateway.ledger.transaction() as db:
        db.execute("UPDATE turns SET result=? WHERE batch=?", ('{"forged":true}', "batch"))
    with pytest.raises(ValueError, match="DENIED"):
        port.result_bytes(port.result_ref(request.turn_id))
    assert result.kind == "tool_calls"


@pytest.mark.parametrize("field", ["result", "usage"])
def test_reconciliation_denies_tampered_observed_receipt_before_reporting_success(tmp_path, field):
    import json

    from pieces.backend.model_gateway.ledger import Ledger

    gateway, port, _, provider, request = setup(tmp_path)
    port.turn(request)
    row = gateway.ledger.turn("batch", "turn")
    changed = dict(row[field])
    if field == "result":
        changed["usage_receipt_ref"] = "forged:usage"
    else:
        changed["input_tokens"] = 0
    with gateway.ledger.transaction() as db:
        db.execute(f"UPDATE turns SET {field}=? WHERE batch=?", (json.dumps(changed), "batch"))
    gateway.ledger = Ledger(gateway.ledger.path)
    with pytest.raises(ValueError, match="DENIED usage/result receipt"):
        port.reconcile(request.turn_id)
    assert provider.calls == 1


def test_provider_token_overrun_freezes_profile_even_when_cost_fits_reservation(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def overrun(wire):
        response = original(wire)
        response["usage"] = {"input_tokens": 24001, "output_tokens": 0}
        return response

    provider.generate = overrun
    result = port.turn(request)
    assert result.kind == "blocked"
    assert gateway.ledger.snapshot()["frozen"]
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 2401


@pytest.mark.parametrize(
    ("mutate", "label", "blocks"),
    [
        (
            lambda r: r["content"].__setitem__(0, dict(r["content"][0], name="host_shell")),
            "undeclared_tool",
            1,
        ),
        (
            lambda r: r["content"].extend([dict(r["content"][0], id=f"x{i}") for i in range(4)]),
            "tool_call_count",
            5,
        ),
    ],
)
def test_rejected_output_records_only_a_closed_label_and_block_count(
    tmp_path, mutate, label, blocks
):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def faulty(wire):
        response = original(wire)
        mutate(response)
        return response

    provider.generate = faulty
    result = port.turn(request)
    assert result.issue.code == "INVALID_MODEL_OUTPUT"
    usage = gateway.ledger.turn("batch", request.turn_id)["usage"]
    assert (usage["rejection"], usage["tool_use_blocks"]) == (label, blocks)
    assert "host_shell" not in json.dumps(usage)
    # Receipt authenticity still covers the new diagnostic fields.
    assert port.reconcile(request.turn_id).state == "observed"


def test_uncached_profile_never_prices_an_unexpected_cache_write(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)
    original = provider.generate

    def writes_cache(wire):
        response = original(wire)
        response["usage"]["cache_creation_input_tokens"] = 500
        return response

    provider.generate = writes_cache
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    # Held as unknown with its full reservation; nothing priced at a wrong rate.
    assert gateway.ledger.turn("batch", request.turn_id)["state"] == "unknown"
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 0


def test_zero_usage_report_reconciles_only_an_unknown_turn_and_releases_on_close(tmp_path):
    gateway, port, _, provider, request = setup(tmp_path)

    def lost(wire):
        raise ConnectionError("synthetic disconnect")

    provider.generate = lost
    with pytest.raises(ValueError, match="UNKNOWN"):
        port.turn(request)
    evidence = {
        "source": "console usage table",
        "date_utc": "2026-11-10",
        "data_as_of_utc": "2026-11-11T07:38Z",
        "org_tokens_on_date": 0,
        "calibration": "later-day usage present",
    }
    with pytest.raises(ValueError, match="UNPROVEN"):
        gateway.reconcile_zero_usage("batch", request.turn_id, dict(evidence, org_tokens_on_date=5))
    proof = gateway.reconcile_zero_usage("batch", request.turn_id, evidence)
    assert proof["body"]["charge_micro_usd"] == 0 and proof["body"]["token_usage"] is None
    with pytest.raises(ValueError, match="UNPROVEN"):
        gateway.reconcile_zero_usage("batch", request.turn_id, evidence)  # not unknown any more
    gateway.ledger.close("batch")
    snapshot = gateway.ledger.snapshot()
    assert snapshot["reserved_micro_usd"] == 0 and snapshot["spent_micro_usd"] == 0
