"""Actual own loop + actual local gateway; controlled provider/control/tool dependencies."""

import json

import pytest
from goldgraft_contracts.plan5_common import content_digest


class NativeProvider:
    def __init__(self):
        self.calls = 0

    def count(self, wire):
        return 100

    def generate(self, wire):
        self.calls += 1
        context = json.loads(wire["messages"][0]["content"])
        if not context["observations"]:
            blocks = [
                {
                    "name": "source_read",
                    "input": {
                        "snapshot_ref": "fake:survey-source",
                        "path": "refund.php",
                        "max_bytes": 1000,
                    },
                },
                {
                    "name": "analysis_matches",
                    "input": {
                        "snapshot_ref": "fake:survey-source",
                        "rule_ref": "fake:survey-rules:1",
                        "max_matches": 500,
                    },
                },
                {
                    "name": "evidence_read",
                    "input": {"ref": "fake:survey-omissions", "max_bytes": 4096},
                },
            ]
        else:
            blocks = [
                {
                    "name": "submit_inventory",
                    "input": {
                        "shop_id": "test-refund",
                        "stack": {
                            "lang": "synthetic",
                            "framework": "none",
                            "versions": {},
                            "db": "none",
                        },
                        "lenses_run": ["code"],
                        "touchpoints": [
                            {
                                "id": "refund",
                                "family": "EC_NVP",
                                "operation": "RefundTransaction",
                                "location": {"file": "refund.php", "line": 2},
                                "lenses": ["code"],
                                "confidence": 0.5,
                                "live": False,
                                "paypal_only": False,
                                "target": {
                                    "paypal_mapping_id": "nvp-refund",
                                    "rest_op": "unqualified",
                                },
                            }
                        ],
                        "money_flow": {
                            key: ([{"file": "refund.php", "line": 2}] if key == "refund" else [])
                            for key in [
                                "create",
                                "approve",
                                "capture",
                                "mark_paid",
                                "refund",
                                "notify",
                                "recurring",
                            ]
                        },
                        "recall_evidence": {
                            "runtime_calls_total": 0,
                            "matched_by_static": 0,
                            "misses": [],
                        },
                    },
                }
            ]
        return {
            "id": "msg_test",
            "model": "claude-haiku-5-5",
            "content": [
                dict(b, type="tool_use", id="call-" + str(i)) for i, b in enumerate(blocks)
            ],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        }


def test_signed_gateway_drives_existing_runtime_and_actual_accepted_output(tmp_path):
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_surveyor_model_eval import compose

    provider = NativeProvider()
    gateway = Gateway(Ledger(tmp_path / "money.sqlite"), tmp_path / "signing", Profile(), provider)
    package = package_from_sources(
        shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
    )
    ports = compose(tmp_path / "state.sqlite", package, gateway, "test-batch")
    tick("fake:runtime-run", ports.clock(), ports)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    assert task.state == "succeeded"
    descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
    assert descriptor.ref in task.output_refs
    assert payload["touchpoints"][0]["location"] == {"file": "refund.php", "line": 2}
    assert provider.calls == 2
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 40
    before = content_digest(ports.control.result("survey"))
    tick("fake:runtime-run", ports.clock(), ports)
    assert content_digest(ports.control.result("survey")) == before and provider.calls == 2


def sdk_gateway(tmp_path, monkeypatch, handle):
    """Replace only HTTP transport; exercise actual pinned SDK and custody code."""
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv

    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from pieces.backend.model_gateway.provider import AnthropicProvider

    key = tmp_path / "private.env"
    key.write_text("ANTHROPIC_API_KEY=sk-ant-synthetic-test-key\n")
    key.chmod(0o600)
    monkeypatch.setattr(
        "anthropic.DefaultHttpxClient",
        lambda **kwargs: httpx2.Client(
            transport=httpx2.MockTransport(handle), trust_env=False, follow_redirects=False
        ),
    )
    profile = Profile()
    return Gateway(
        Ledger(tmp_path / "money.sqlite"),
        tmp_path / "signing",
        profile,
        AnthropicProvider(key, profile),
    )


def test_operation_name_cannot_replace_observed_catalog_mapping_id(tmp_path):
    from pieces.agents.scheduler import tick
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_surveyor_model_eval import compose

    class WrongMapping(NativeProvider):
        def generate(self, wire):
            response = super().generate(wire)
            if response["content"][0]["name"] == "submit_inventory":
                touchpoint = response["content"][0]["input"]["touchpoints"][0]
                touchpoint["target"]["paypal_mapping_id"] = touchpoint["operation"]
            return response

    provider = WrongMapping()
    gateway = Gateway(Ledger(tmp_path / "money.sqlite"), tmp_path / "signing", Profile(), provider)
    ports = compose(tmp_path / "state.sqlite", refund_package(), gateway, "wrong-mapping")
    tick("fake:runtime-run", ports.clock(), ports)
    result = ports.control.result("survey")
    assert result.outcome == "blocked" and result.issue.code == "MISSING_EVIDENCE"
    assert result.output_refs == [] and provider.calls == 2
    tick("fake:runtime-run", ports.clock(), ports)
    assert provider.calls == 2


def refund_package():
    from pieces.agents.source_inventory import package_from_sources

    return package_from_sources(
        shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
    )


def test_actual_sdk_wire_drives_checked_inventory_and_fresh_instance_resume(tmp_path, monkeypatch):
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv

    from pieces.agents.scheduler import tick
    from pieces.agents.surveyor import inspect_inventory
    from scripts.live_surveyor_model_eval import compose

    seen = []
    scripted = NativeProvider()

    def handle(request):
        wire = json.loads(request.content)
        context = json.loads(wire["messages"][0]["content"])
        if context["observations"]:
            assert context["tool_progress"] == {
                "read_paths": ["refund.php"],
                "matches_observed": True,
                "omissions_observed": True,
                "unread_paths": [],
                "ready_to_submit": True,
                "next_calls": [],
            }
        else:
            assert context["tool_progress"]["unread_paths"] == ["refund.php"]
            assert context["tool_progress"]["ready_to_submit"] is False
        seen.append(request.url.path)
        assert request.url.host == "api.anthropic.com"
        assert wire["model"] == "claude-haiku-5-5"
        assert wire["thinking"] == {"type": "disabled"}
        assert {tool["name"] for tool in wire["tools"]} == {
            "source_read",
            "analysis_matches",
            "evidence_read",
            "submit_inventory",
            "report_hold",
        }
        if request.url.path.endswith("count_tokens"):
            assert "max_tokens" not in wire
            return httpx2.Response(200, json={"input_tokens": 100})
        if "speed" in wire:
            return httpx2.Response(
                400,
                headers={"request-id": "req_speed"},
                json={
                    "type": "error",
                    "error": {
                        "type": "invalid_request_error",
                        "message": "speed is unsupported for this model",
                    },
                },
            )
        assert wire["max_tokens"] == 1536 and wire["service_tier"] == "standard_only"
        response = scripted.generate(wire)
        response.update(
            type="message", role="assistant", stop_reason="tool_use", stop_sequence=None
        )
        response["id"] = "msg_synthetic_" + str(scripted.calls)
        return httpx2.Response(200, headers={"request-id": "req_synthetic"}, json=response)

    gateway = sdk_gateway(tmp_path, monkeypatch, handle)
    package = refund_package()
    ports = compose(tmp_path / "state.sqlite", package, gateway, "sdk-success")
    tick("fake:runtime-run", ports.clock(), ports)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    assert task.state == "succeeded"
    descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
    assert descriptor.ref in task.output_refs
    assert payload["money_flow"]["refund"] == [{"file": "refund.php", "line": 2}]
    inspection = inspect_inventory(
        payload,
        input_refs=task.task.input_refs,
        output_ref=descriptor.ref,
        subject=descriptor.subject_digest,
        evidence_refs=ports.control.result("survey").evidence_refs,
        omissions=package["omissions"],
    )
    assert len(inspection["touchpoints"]) == 1
    assert inspection["touchpoints"][0]["operation"] == "RefundTransaction"
    assert len(seen) == 4 and scripted.calls == 2
    before = content_digest(ports.control.result("survey"))
    restarted = compose(tmp_path / "state.sqlite", package, gateway, "sdk-success")
    tick("fake:runtime-run", restarted.clock(), restarted)
    assert content_digest(restarted.control.result("survey")) == before
    assert len(seen) == 4
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 40


@pytest.mark.parametrize("fault", [400, 401, 429, 500, "timeout", "connection"])
def test_sdk_transport_fault_retains_identity_and_budget_across_restart(
    tmp_path, monkeypatch, fault
):
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv

    from pieces.agents.scheduler import tick
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from scripts.live_surveyor_model_eval import compose

    seen = []

    def handle(request):
        seen.append(request.url.path)
        if request.url.path.endswith("count_tokens"):
            return httpx2.Response(200, json={"input_tokens": 100})
        if fault == "timeout":
            raise httpx2.ReadTimeout("private fault text", request=request)
        if fault == "connection":
            raise httpx2.ConnectError("private fault text", request=request)
        return httpx2.Response(
            fault,
            headers={"request-id": "req_synthetic_fault"},
            json={"type": "error", "error": {"type": "api_error", "message": "private fault text"}},
        )

    gateway = sdk_gateway(tmp_path, monkeypatch, handle)
    package = refund_package()
    ports = compose(tmp_path / "state.sqlite", package, gateway, "sdk-fault")
    tick("fake:runtime-run", ports.clock(), ports)
    assert len(seen) == 2  # One count + one inference attempt; SDK retries disabled.
    with gateway.ledger.transaction() as db:
        turn = db.execute("SELECT id FROM turns").fetchone()[0]
    row = gateway.ledger.turn("sdk-fault", turn)
    assert row["state"] == "unknown" and row["result"] is None and row["usage"] is None
    diagnostic = row["provider_observation"]
    assert diagnostic["signature"] == gateway.signature(diagnostic["body"])
    failure = diagnostic["body"]["failure"]
    assert failure["category"] == ("http_error" if type(fault) is int else fault)
    assert failure["status"] == (fault if type(fault) is int else None)
    assert "private fault text" not in json.dumps(diagnostic)
    snapshot = gateway.ledger.snapshot()
    assert snapshot["spent_micro_usd"] == 0
    assert snapshot["reserved_micro_usd"] == 12672 and snapshot["unknown_micro_usd"] == 3168
    reopened_gateway = Gateway(
        Ledger(gateway.ledger.path), tmp_path / "signing", gateway.profile, gateway.provider
    )
    restarted = compose(tmp_path / "state.sqlite", package, reopened_gateway, "sdk-fault")
    tick("fake:runtime-run", restarted.clock(), restarted)
    with pytest.raises(ValueError, match="UNKNOWN"):
        reopened_gateway.ledger.reserve("replacement", "replacement", 12672)
    assert len(seen) == 2 and reopened_gateway.ledger.snapshot() == snapshot
    assert restarted.control.snapshot("fake:runtime-run").tasks[0].state != "succeeded"


def test_real_model_ticket_above_project_phase_ceiling_is_denied_before_any_provider_call(tmp_path):
    from dataclasses import replace

    from pieces.agents.context import REAL_MODEL_CEILING_MICRO_USD
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_surveyor_model_eval import compose

    assert REAL_MODEL_CEILING_MICRO_USD == 13000000
    provider = NativeProvider()
    gateway = Gateway(Ledger(tmp_path / "money.sqlite"), tmp_path / "signing", Profile(), provider)
    package = package_from_sources(
        shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
    )
    ports = compose(tmp_path / "state.sqlite", package, gateway, "test-batch")
    original = ports.artifacts.ticket

    def over(lease):
        value = original(lease)
        budget = value.budget.model_copy(
            update={
                "ceiling_micro_usd": REAL_MODEL_CEILING_MICRO_USD + 1,
                "target_micro_usd": REAL_MODEL_CEILING_MICRO_USD + 1,
            }
        )
        return replace(value, budget=budget)

    ports.artifacts.ticket = over
    tick("fake:runtime-run", ports.clock(), ports)
    result = ports.control.result("survey")
    assert result.outcome == "blocked" and result.issue.code == "DENIED"
    assert provider.calls == 0


def test_tool_progress_reports_unread_manifest_paths_until_every_read_is_observed(tmp_path):
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_surveyor_model_eval import compose

    package = package_from_sources(
        shop_id="test-two",
        files={"a.php": "<?php\n$m='RefundTransaction';\n", "b.php": "<?php\necho 'x';\n"},
    )
    progress = []

    def read(path):
        return {"snapshot_ref": "fake:survey-source", "path": path, "max_bytes": 1000}

    plan = [
        [{"name": "source_read", "input": read("a.php")}],
        [
            {"name": "source_read", "input": read("b.php")},
            {
                "name": "analysis_matches",
                "input": {
                    "snapshot_ref": "fake:survey-source",
                    "rule_ref": "fake:survey-rules:1",
                    "max_matches": 500,
                },
            },
            {"name": "evidence_read", "input": {"ref": "fake:survey-omissions", "max_bytes": 4096}},
        ],
        [{"name": "submit_inventory", "input": build_static_inventory(package)}],
    ]

    class Partial(NativeProvider):
        def generate(self, wire):
            progress.append(json.loads(wire["messages"][0]["content"])["tool_progress"])
            blocks = plan[self.calls]
            self.calls += 1
            return {
                "id": "msg_partial",
                "model": "claude-haiku-5-5",
                "content": [
                    dict(b, type="tool_use", id=f"c{self.calls}{i}") for i, b in enumerate(blocks)
                ],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            }

    provider = Partial()
    gateway = Gateway(Ledger(tmp_path / "money.sqlite"), tmp_path / "signing", Profile(), provider)
    ports = compose(tmp_path / "state.sqlite", package, gateway, "test-batch")
    tick("fake:runtime-run", ports.clock(), ports)
    assert ports.control.result("survey").outcome == "completed"
    assert [(p["unread_paths"], p["ready_to_submit"]) for p in progress] == [
        (["a.php", "b.php"], False),
        (["b.php"], False),
        ([], True),
    ]
    assert [p["next_calls"] for p in progress] == [
        ["source_read:a.php", "source_read:b.php", "analysis_matches", "evidence_read"],
        ["source_read:b.php", "analysis_matches", "evidence_read"],
        [],
    ]


def test_next_calls_never_exceed_the_enforced_per_response_cap_and_policy_states_it():
    from pieces.backend.model_gateway.broker import MAX_CALLS_PER_RESPONSE, TRANSPORT_POLICY

    assert MAX_CALLS_PER_RESPONSE == 4
    assert "at most 4 tool calls" in TRANSPORT_POLICY
    assert "tool_progress.next_calls" in TRANSPORT_POLICY


def test_sonnet_profile_is_separate_and_sends_between_tools_thinking(tmp_path):
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import PROFILES, Profile, SonnetProfile
    from scripts.live_surveyor_model_eval import compose

    haiku, sonnet = Profile(), SonnetProfile()
    assert haiku.ref == (
        "local:model-profile:59c164262bbdf058559dbeaa25521c4d4bd5645f0c67561cbb9473331cf44ad1"
    )
    assert sonnet.ref != haiku.ref and PROFILES["sonnet"] is SonnetProfile
    assert (sonnet.turn_reservation, sonnet.batch_reservation) == (100000, 800000)
    thinking = []

    class Sonnet(NativeProvider):
        def generate(self, wire):
            thinking.append(wire["thinking"])
            return dict(super().generate(wire), model="claude-sonnet-5-5")

    provider = Sonnet()
    ledger = Ledger(tmp_path / "money.sqlite")
    # A Sonnet batch cannot fit the default $0.05 cap; it needs a recorded raise.
    gateway = Gateway(ledger, tmp_path / "signing", sonnet, provider)
    blocked = compose(
        tmp_path / "blocked.sqlite",
        package_from_sources(
            shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
        ),
        gateway,
        "too-big",
    )
    tick("fake:runtime-run", blocked.clock(), blocked)
    assert blocked.control.result("survey").issue.code == "BUDGET_EXHAUSTED"
    assert provider.calls == 0
    ledger.raise_active_cap(1000000, "e" * 64, limit=1000000)
    package = package_from_sources(
        shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
    )
    ports = compose(tmp_path / "state.sqlite", package, gateway, "test-batch")
    tick("fake:runtime-run", ports.clock(), ports)
    assert ports.control.result("survey").outcome == "completed"
    assert thinking == [{"type": "between_tools"}] * 2
    # Per turn: 100 input x $2/MTok = 200 + 20 output x $10/MTok = 200 micro-USD.
    assert gateway.ledger.snapshot()["spent_micro_usd"] == 2 * 400


def test_route_profile_uses_haiku_only_when_first_wave_reads_fit_one_response():
    from pieces.backend.model_gateway.profile import route_profile

    assert route_profile({"a.php": ""}) == "haiku"
    assert route_profile({"a.php": "", "b.php": ""}) == "haiku"
    assert route_profile({"a.php": "", "b.php": "", "c.php": ""}) == "sonnet"


def test_ceiling_profile_bounds_input_by_provider_count_not_bytes(tmp_path):
    """Bytes far above the old byte bound are admitted when the provider count fits;
    a count within the margin of the cap is refused before any dispatch or spend."""
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile, SonnetProfile
    from scripts.live_surveyor_model_eval import compose

    filler = "".join(f"$line{i} = 'synthetic ceiling filler {i:04d}';\n" for i in range(200))
    files = {"refund.php": "<?php\n$m='RefundTransaction';\n" + filler}
    package = package_from_sources(shop_id="test-refund", files=files)

    def run(profile, counted, path):
        sizes = []

        class Counted(NativeProvider):
            def count(self, wire):
                sizes.append(len(json.dumps(wire)))
                return counted

            def generate(self, wire):
                response = super().generate(wire)
                for block in response["content"]:
                    if block["name"] == "source_read":
                        block["input"]["max_bytes"] = 16384  # read the whole 8.7 KB file
                return dict(response, model=profile.model)

        provider = Counted()
        ledger = Ledger(path / "money.sqlite")
        ledger.raise_active_cap(1000000, "f" * 64, limit=1000000)
        gateway = Gateway(ledger, path / "signing", profile, provider)
        ports = compose(path / "state.sqlite", package, gateway, "b")
        tick("fake:runtime-run", ports.clock(), ports)
        return ports.control.result("survey"), provider, ledger, sizes

    (tmp_path / "haiku").mkdir()
    result, provider, _, _ = run(Profile(), 100, tmp_path / "haiku")
    # Haiku keeps the byte bound: turn 1 dispatches, turn 2 (with the 8 KB excerpt) is refused.
    assert result.outcome == "blocked" and provider.calls == 1
    (tmp_path / "ok").mkdir()
    result, provider, ledger, sizes = run(SonnetProfile(), 9000, tmp_path / "ok")
    # Ceiling profile admits the same turn 2 because the provider count fits.
    assert provider.calls == 2 and max(sizes) > 22976 and result.outcome == "completed"
    (tmp_path / "over").mkdir()
    result, provider, ledger, _ = run(SonnetProfile(), 24000 - 511, tmp_path / "over")
    assert result.outcome == "blocked" and provider.calls == 0
    assert ledger.snapshot()["spent_micro_usd"] == 0


def test_cached_prefix_profile_marks_system_and_prices_writes_and_reads_exactly(tmp_path):
    """Sonnet ceiling caches tools+system; writes 1.25x, reads 0.05x, signed audit."""
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import package_from_sources
    from pieces.backend.model_gateway.broker import Gateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile, SonnetProfile
    from scripts.live_surveyor_model_eval import compose

    systems = []

    class Cached(NativeProvider):
        def generate(self, wire):
            systems.append(wire["system"])
            response = super().generate(wire)
            # Turn 1 writes the 9,000-token prefix; turn 2 reads it.
            first = self.calls == 1
            usage = {
                "input_tokens": 300,
                "output_tokens": 20,
                "cache_creation_input_tokens": 9000 if first else 0,
                "cache_read_input_tokens": 0 if first else 9000,
            }
            return dict(response, model="claude-sonnet-5-5", usage=usage)

    profile = SonnetProfile()
    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.raise_active_cap(1000000, "d" * 64, limit=1000000)
    provider = Cached()
    gateway = Gateway(ledger, tmp_path / "signing", profile, provider)
    package = package_from_sources(
        shop_id="test-refund", files={"refund.php": "<?php\n$m='RefundTransaction';\n"}
    )
    ports = compose(tmp_path / "state.sqlite", package, gateway, "cached")
    tick("fake:runtime-run", ports.clock(), ports)
    assert ports.control.result("survey").outcome == "completed"
    assert all(s[0]["cache_control"] == {"type": "ephemeral"} for s in systems)
    # 300*$2 + 9000*$2.50 + 20*$10 = 600+22500+200 = 23300 ; 300*$2 + 9000*$0.10 + 200 = 1700
    assert ledger.snapshot()["spent_micro_usd"] == 23300 + 1700
    with ledger.transaction() as db:
        usages = [json.loads(r[0]) for r in db.execute("SELECT usage FROM turns")]
    assert sorted(u["cache_read_input_tokens"] for u in usages) == [0, 9000]
    assert all(u["input_tokens"] == 9300 for u in usages)  # total prompt size
    # The worst-case reservation covers any priced turn at the caps.
    assert profile.turn_reservation >= profile.cost_cached(0, 24000, 0, 4000)
    # Haiku keeps an uncached string system prompt and its unchanged profile.
    assert not getattr(Profile(), "cache_prefix", False)
