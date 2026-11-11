"""Component agents through the actual signed gateway + own runtime; scripted provider."""

import json

import pytest


class AlertProvider:
    """Behaves like a model: reads, requests a hold on breach, then words its own alert."""

    def __init__(self, *, lie=False):
        self.calls, self.lie = 0, lie

    def count(self, wire):
        return 1000

    def generate(self, wire):
        self.calls += 1
        context = json.loads(wire["messages"][0]["content"])
        data = context["role_inputs"]["data"]
        done = context["tool_progress"]
        facts = context["call_facts"]
        kinds = {e["kind"] for e in data["events"]}
        breach = bool(kinds & {"denied_tool", "secret_attempt"})
        if "audit.summary" not in done:
            block = {
                "name": "audit_summary",
                "input": {"run_ref": facts["run_ref"], "after_seq": data["after_seq"]},
            }
        elif breach and "safety.request_hold" not in done:
            block = {
                "name": "safety_request_hold",
                "input": {
                    "run_ref": facts["run_ref"],
                    "reason_code": facts["hold_reason_code"],
                    "evidence_refs": facts["evidence_refs"],
                },
            }
        else:
            words = ", ".join(sorted(k.replace("_", " ") for k in kinds)) or "nothing"
            message = f"Reviewed window; found: {words}. Termination is not confirmed."
            if self.lie:
                message = "The agent has been terminated and all is fine."
            block = {
                "name": "submit_output",
                "input": dict(
                    context["reference_metadata"],
                    severity="CRITICAL" if breach else "MAJOR" if kinds else "MINOR",
                    message=message,
                    evidence_refs=context["task_context"]["input_refs"],
                    halted_agent=None,
                ),
            }
        return {
            "id": f"msg_c{self.calls}",
            "model": "claude-haiku-5-5",
            "content": [dict(block, type="tool_use", id=f"t{self.calls}")],
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        }


def run(tmp_path, case, provider):
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_component_model_eval import run_case

    ledger = Ledger(tmp_path / "money.sqlite")
    gateway = ComponentGateway(
        ledger, tmp_path / "signing", Profile(), provider, roles={"Sentinel"}
    )
    task, result, outputs, base = run_case(case, gateway, tmp_path, "b")
    return task, result, outputs, base, ledger


@pytest.mark.parametrize("kinds", [["denied_tool", "stale_output"], ["termination_pending"], []])
def test_real_gateway_path_accepts_a_correct_model_alert_and_scores_it(tmp_path, kinds):
    from pieces.agents.evals.components import score

    events = [
        {
            "sequence": i + 1,
            "case_id": "case-demo",
            "run_id": "run-demo",
            "generation": 1,
            "kind": k,
            "fingerprint": f"{i + 1:064x}",
        }
        for i, k in enumerate(kinds)
    ]
    breach = "denied_tool" in kinds
    case = {
        "id": "t",
        "role": "Sentinel",
        "data": {"after_seq": 0, "events": events},
        "expected": {
            "severity": "CRITICAL" if breach else "MAJOR" if kinds else "MINOR",
            "hold": breach,
            "kinds": sorted(set(kinds)),
        },
    }
    provider = AlertProvider()
    task, result, outputs, base, ledger = run(tmp_path, case, provider)
    assert task.state == "succeeded", result
    assert outputs[0]["payload"]["producer"]["model"] == "claude-haiku-5-5"
    assert score(case, outputs, base)["passed"]
    assert provider.calls == (3 if breach else 2)
    assert ledger.snapshot()["spent_micro_usd"] > 0


def test_real_gateway_path_rejects_a_model_that_claims_termination(tmp_path):
    events = [
        {
            "sequence": 1,
            "case_id": "case-demo",
            "run_id": "run-demo",
            "generation": 1,
            "kind": "denied_tool",
            "fingerprint": "1" * 64,
        }
    ]
    case = {"id": "t", "role": "Sentinel", "data": {"after_seq": 0, "events": events}}
    task, result, outputs, _, _ = run(tmp_path, case, AlertProvider(lie=True))
    assert task.state != "succeeded" and outputs is None


def test_component_gateway_refuses_unlisted_roles(tmp_path):
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile

    gateway = ComponentGateway(
        Ledger(tmp_path / "m.sqlite"), tmp_path / "k", Profile(), None, roles={"Sentinel"}
    )
    with pytest.raises(ValueError, match="UNSUPPORTED"):
        gateway.grant("b", {"role": "Grafter"})


def test_rejected_tool_call_shape_is_recorded_in_closed_vocabulary_only():
    from pieces.backend.model_gateway.component_port import closed_shape

    names = {"audit_summary": "audit.summary"}
    shape = closed_shape(
        {"name": "audit_summary", "input": {"run_ref": "x y", "secret-text": 1}}, names
    )
    assert shape == {
        "tool": "audit.summary",
        "missing": ["after_seq"],
        "extra_count": 1,
        "invalid": ["run_ref"],
    }
    assert closed_shape({"name": "rm -rf", "input": {}}, names) == {"tool": "other"}
    assert "secret-text" not in json.dumps(shape) and "x y" not in json.dumps(shape)


class BuilderProvider:
    """Follows Builder's call policy from call_facts only; can tamper with the proposal."""

    def __init__(self, change=None):
        self.calls, self.change = 0, change

    def count(self, wire):
        return 1000

    def generate(self, wire):
        self.calls += 1
        context = json.loads(wire["messages"][0]["content"])
        data, facts = context["role_inputs"]["data"], context["call_facts"]
        done = context["tool_progress"]
        cat = data["catalog"]
        proposal = {
            "task_id": facts["task_id"],
            "operation": facts["operation"],
            "subject_ref": data["subject_ref"],
            "recipe_ref": cat["recipe_ref"],
            "scenario_ref": None,
            "variant": None,
            "requested_output_schemas": facts["requested_output_schemas"],
            "expected_subject": facts["expected_subject"],
            "evidence_refs": facts["evidence_refs"],
        }
        if not done:
            blocks = [
                {
                    "name": "recipe_lookup",
                    "input": {"catalog_ref": cat["ref"], "fingerprint": cat["fingerprint"]},
                },
                {
                    "name": "dependency_inspect",
                    "input": {
                        "recipe_ref": cat["recipe_ref"],
                        "package": cat["package"],
                        "version": cat["version"],
                    },
                },
            ]
        elif len(done) == 2:
            value = {"proposal": proposal}
            if self.change:
                self.change(value)
            blocks = [{"name": "execution_request", "input": value}]
        elif len(done) == 3:
            blocks = [{"name": "execution_status", "input": {"request_id": facts["request_id"]}}]
        else:
            blocks = [{"name": "submit_output", "input": proposal}]
        return {
            "id": f"msg_b{self.calls}",
            "model": "claude-haiku-5-5",
            "content": [
                dict(b, type="tool_use", id=f"t{self.calls}{i}") for i, b in enumerate(blocks)
            ],
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        }


def run_builder(tmp_path, provider):
    from pieces.agents.component_agents.builder import sample
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import HaikuLongProfile
    from scripts.live_component_model_eval import run_case

    gateway = ComponentGateway(
        Ledger(tmp_path / "m.sqlite"),
        tmp_path / "k",
        HaikuLongProfile(),
        provider,
        roles={"Builder"},
    )
    case = {
        "id": "b",
        "role": "Builder",
        "operation": "build_baseline",
        "data": sample("build_baseline"),
    }
    return run_case(case, gateway, tmp_path, "b")


def test_inline_proposal_is_validated_and_staged_by_the_gateway(tmp_path):
    task, result, outputs, base = run_builder(tmp_path, BuilderProvider())
    assert task.state == "succeeded", result
    assert outputs[0]["payload"]["recipe_ref"] == "fixture:recipe"
    assert base.tools.total_dispatches() == 4


@pytest.mark.parametrize(
    "change",
    [
        lambda v: v["proposal"].update(subject_ref="fixture:other"),
        lambda v: v["proposal"].pop("expected_subject"),
        lambda v: v.update(proposal_ref="fake:blob:forged"),
    ],
    ids=["other_subject", "invalid_content", "raw_ref_bypass"],
)
def test_tampered_or_bypassed_inline_proposal_never_completes(tmp_path, change):
    task, _, outputs, _ = run_builder(tmp_path, BuilderProvider(change))
    assert task.state != "succeeded" and outputs is None


def test_derived_progress_lists_only_remaining_reads_and_never_outputs(tmp_path):
    from pieces.agents.component_agents.scribe import sample
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import HaikuLongProfile
    from scripts.live_component_model_eval import run_case

    seen = []

    class ReadThenHold:
        calls = 0

        def count(self, wire):
            return 1000

        def generate(self, wire):
            self.calls += 1
            facts = json.loads(wire["messages"][0]["content"])["call_facts"]
            seen.append(facts)
            if facts["unread_reads"]:
                call = facts["unread_reads"][0]
                block = {"name": call["tool"].replace(".", "_"), "input": call["arguments"]}
            else:
                block = {"name": "report_hold", "input": {"code": "MISSING_EVIDENCE"}}
            return {
                "id": f"msg_s{self.calls}",
                "model": "claude-haiku-5-5",
                "content": [dict(block, type="tool_use", id=f"t{self.calls}")],
                "usage": {"input_tokens": 1000, "output_tokens": 50},
            }

    gateway = ComponentGateway(
        Ledger(tmp_path / "m.sqlite"),
        tmp_path / "k",
        HaikuLongProfile(),
        ReadThenHold(),
        roles={"Scribe"},
    )
    case = {
        "id": "s",
        "role": "Scribe",
        "operation": "scribe_draft",
        "data": sample("scribe_draft"),
    }
    run_case(case, gateway, tmp_path, "b")
    assert [f["reads_complete"] for f in seen] == [False, True]
    assert [len(f["unread_reads"]) for f in seen] == [1, 0]
    assert seen[0]["unread_reads"][0]["tool"] == "source.read"
    assert not {"rules", "outputs", "agreement"} & set(seen[0])


def _obs(tool, args):
    return {"evidence_class": "scripted", "value": {"tool": tool, "arguments": args}}


def test_reads_may_come_in_any_order_but_writes_keep_their_place():
    from pieces.agents.component import paired

    a = {"tool": "source.read", "arguments": {"snapshot_ref": "s", "path": "a", "max_bytes": 1}}
    b = {"tool": "source.read", "arguments": {"snapshot_ref": "s", "path": "b", "max_bytes": 1}}
    w = {
        "tool": "execution.request",
        "arguments": {"proposal_ref": "inline:proposal"},
        "proposal": {},
    }
    s = {"tool": "execution.status", "arguments": {"request_id": "r"}}
    obs = [_obs("source.read", b["arguments"]), _obs("source.read", a["arguments"])]
    assert [c["arguments"]["path"] for c, _ in paired([a, b], obs)] == ["a", "b"]
    moved = [_obs("execution.status", s["arguments"]), _obs("execution.request", {})]
    with pytest.raises(ValueError):
        paired([w, s], moved)
    pairs = paired(
        [a, w, s],
        [
            _obs("source.read", b["arguments"]),
            _obs("execution.request", {}),
            _obs("execution.status", s["arguments"]),
        ],
    )
    assert (
        pairs[0][1]["value"]["arguments"]["path"] == "b"
    )  # mismatched read is left for the binding check


def test_inline_candidate_patch_has_a_private_map_schema_and_rejects_bad_content():
    from pieces.backend.model_gateway.component_port import CandidatePatch, inline_schema

    schema = inline_schema("candidate.patch", {"patch_ref": ("patch", "candidate_patch")})
    assert schema["properties"]["patch"]["additionalProperties"]["type"] == "string"
    assert "patch_ref" not in schema["properties"]
    for value in [
        {},
        {"../escape.php": "bad"},
        {"checkout.php": 7},
        {"checkout.php": {"code": "x"}},
    ]:
        with pytest.raises(ValueError):
            CandidatePatch.model_validate(value)


def test_synthetic_collector_fault_control_is_hidden_from_the_model(tmp_path):
    from pieces.agents.component_agents.grafter import sample
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import HaikuLongProfile
    from scripts.live_component_model_eval import run_case

    seen = []

    class Observer:
        def count(self, wire):
            return 1000

        def generate(self, wire):
            seen.append(json.loads(wire["messages"][0]["content"]))
            return {
                "id": "msg_hidden",
                "model": "claude-haiku-5-5",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "h",
                        "name": "report_hold",
                        "input": {"code": "MISSING_EVIDENCE"},
                    }
                ],
                "usage": {"input_tokens": 1000, "output_tokens": 50},
            }

    data = sample("candidate_patch")
    data["collector_receipt_fault"] = "wrong_tree"
    gateway = ComponentGateway(
        Ledger(tmp_path / "m.sqlite"),
        tmp_path / "k",
        HaikuLongProfile(),
        Observer(),
        roles={"Grafter"},
    )
    run_case(
        {"role": "Grafter", "operation": "candidate_patch", "data": data}, gateway, tmp_path, "h"
    )
    assert seen
    assert "collector_receipt_fault" not in seen[0]["role_inputs"]["data"]
    assert "wrong_tree" not in json.dumps(seen)


def test_candidate_patch_provider_schema_is_closed_to_scoped_paths():
    from pieces.backend.model_gateway.component_port import inline_schema

    schema = inline_schema(
        "candidate.patch",
        {"patch_ref": ("patch", "candidate_patch")},
        patch_paths=["src/pay.php", "keep.php"],
    )["properties"]["patch"]
    assert set(schema["properties"]) == {"src/pay.php", "keep.php"}
    assert schema["additionalProperties"] is False
    assert "propertyNames" not in schema


def test_snapshot_transport_narrows_changelist_without_changing_public_contract():
    from goldgraft_contracts.registry import REGISTRY

    from pieces.backend.model_gateway.component_port import output_schema

    schema = output_schema(["ChangeList/2"])
    assert "oneOf" not in schema
    assert schema["properties"]["provenance"]["const"] == "snapshot"
    assert schema["properties"]["branch"]["type"] == "null"
    assert schema["$defs"]["SnapshotChange"]["properties"]["commit"]["type"] == "null"
    assert "oneOf" in REGISTRY["ChangeList/2"].model_json_schema()


def test_orchard_fault_switch_is_hidden_without_mutating_authenticated_context():
    from scripts.live_component_model_eval import ComponentEvaluationArtifacts

    context = {
        "role_inputs": {
            "role": "Orchard Analyst",
            "data": {
                "query_ref": "catalog:upgrade-counts:1",
                "aggregate_receipt_fault": "raw_rows",
            },
        }
    }
    boundary = object.__new__(ComponentEvaluationArtifacts)
    result = boundary.presentation_context(context)
    assert "aggregate_receipt_fault" not in result["role_inputs"]["data"]
    assert context["role_inputs"]["data"]["aggregate_receipt_fault"] == "raw_rows"
