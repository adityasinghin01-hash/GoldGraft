"""Stand-in-specific behavior; plugtests exercise interchangeable implementations."""

import inspect
import json
from pathlib import Path

import pytest
from goldgraft_contracts import interfaces
from goldgraft_contracts.registry import validate
from goldgraft_fakes.agents import AGENTS
from goldgraft_fakes.proof import FakeProof
from goldgraft_fakes.runner import FakeRunner
from goldgraft_fakes.tools import FakeToolbox

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / "fixtures/proof/legacy-php-shop"


def model(schema, path):
    return validate(schema, json.loads(path.read_text()))


def job(**updates):
    payload = json.loads((ROOT / "contracts/examples/JobSpec.1.json").read_text())
    payload.update(shop_pack_ref="fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
                   scenario_ids=["HAPPY"], variants=["OLD", "OLD_TWIN", "NEW"])
    payload.update(updates)
    return validate("JobSpec/1", payload)


@pytest.mark.parametrize("protocol,instance", [
    (interfaces.Runner, FakeRunner()), (interfaces.Proof, FakeProof()),
    (interfaces.AgentRunner, AGENTS), (interfaces.ToolCaller, FakeToolbox()),
])
def test_protocols_and_signatures(protocol, instance):
    assert isinstance(instance, protocol)
    for name, method in vars(protocol).items():
        if name.startswith("_") or not callable(method):
            continue
        assert inspect.signature(getattr(type(instance), name)) == inspect.signature(method)


def test_runner_cross_product_and_special_cases():
    runner = FakeRunner()
    spec = job(scenario_ids=["HAPPY", "REFUND"])
    result = runner.run_job(spec)
    assert result.status == "OK" and result.job_id == spec.job_id
    assert len(result.raw_capture_refs) == 6
    for ref in result.raw_capture_refs:
        assert runner.fetch_capture(ref).scenario_id in spec.scenario_ids
    for suffix, status in [("__timeout", "TIMEOUT"), ("__blocked", "BLOCKED")]:
        special = runner.run_job(job(scenario_ids=["HAPPY" + suffix]))
        assert special.status == status and special.error and not special.raw_capture_refs
    assert runner.run_job(job(scenario_ids=["HAPPY"] * 10)).rate_limit_pauses == 1
    assert runner.run_job(job(kind="PROVE", scenario_ids=["HAPPY"] * 10)).rate_limit_pauses == 0
    with pytest.raises(LookupError):
        runner.run_job(job(scenario_ids=["UNKNOWN"]))
    with pytest.raises(LookupError):
        runner.run_job(job(shop_pack_ref="fixtures://shops/unknown/goldgraft-shop.yaml"))
    for ref in ["file:///etc/passwd", "fixtures://proof/legacy-php-shop/raw/../../contract.json"]:
        with pytest.raises(LookupError):
            runner.fetch_capture(ref)


def test_proof_matches_content_and_returns_independent_answers():
    proof = FakeProof()
    raw = model("RawCapture/1", PROOF / "raw/HAPPY.OLD.json")
    expected = proof.to_cmel(raw)
    expected[0].money.minor = 1
    assert proof.to_cmel(raw)[0].money.minor == 2500
    changed = raw.model_copy(deep=True)
    changed.exchanges[0].body_json["minor"] = 2
    with pytest.raises(LookupError):
        proof.to_cmel(changed)
    with pytest.raises(LookupError):
        proof.to_cmel(raw.model_copy(update={"scenario_id": "UNKNOWN"}))
    with pytest.raises(LookupError):
        proof.proof_strength([], {})
    with pytest.raises(LookupError):
        proof.heal_decide("graft", 10, [])
    cert = model("Certificate/1", PROOF / "certificate/valid.json")
    cert.cost.tokens += 7
    with pytest.raises(LookupError):
        proof.verify_certificate(cert)


def test_judge_rejects_same_id_with_changed_economics_or_contract():
    proof = FakeProof()
    streams = [[validate("CMEL/1", event) for event in json.loads(
        (PROOF / f"cmel/HAPPY.{variant}.json").read_text())]
        for variant in ("OLD", "OLD_TWIN", "NEW")]
    contract = model("Contract/1", PROOF / "contract.json")
    plan = model("TargetPlan/1", PROOF / "target_plan.json")
    assert proof.judge(*streams, contract, plan).grade == "PASS"
    changed_contract = contract.model_copy(deep=True)
    changed_contract.rules[0].title = "Unknown rule content"
    with pytest.raises(LookupError):
        proof.judge(*streams, changed_contract, plan)
    streams[2][0].money.minor += 1
    with pytest.raises(LookupError):
        proof.judge(*streams, contract, plan)


def test_sentinel_detects_secret_argument_without_a_refusal():
    tools = FakeToolbox()
    tools.call("Grafter", "repo.write", {
        "path": "checkout.php", "content": "Bearer synthetic-credential", "message": "test"})
    alerts = AGENTS.run("Sentinel", {"graft_id": "demo-1"}, tools)
    assert any(s == "Alert/1" and p["severity"] == "CRITICAL" for s, p in alerts)


def test_proof_keys_are_independent_of_call_and_input_order():
    proof = FakeProof()
    for path in reversed(sorted((PROOF / "raw").glob("*.json"))):
        raw = model("RawCapture/1", path)
        raw.graft_id, raw.run_id = "caller-graft", "caller-run"
        mapped = proof.to_cmel(raw)
        assert all(e.graft_id == "caller-graft" and e.run_id == "caller-run" for e in mapped)
        assert [e.kind for e in mapped] == [e["kind"] for e in json.loads(
            (PROOF / "cmel" / path.name).read_text())]
    mutants = [model("Mutant/1", p) for p in sorted((PROOF / "mutants").glob("M*.json"))]
    rows = json.loads((PROOF / "mutants/runs.json").read_text())["runs"]
    runs = {r["mutant"]: r["grades"] for r in reversed(rows)}
    assert proof.proof_strength(list(reversed(mutants)), runs).killed == 4
    runs["M01"] = {"HAPPY": "PROBLEM"}
    with pytest.raises(LookupError):
        proof.proof_strength(mutants, runs)
    for path in reversed(sorted((PROOF / "heal").glob("*.events.json"))):
        events = [validate("GuardEvent/1", e) for e in json.loads(path.read_text())]
        expected_path = path.with_name(path.name.replace(".events.", ".expected."))
        expected = json.loads(expected_path.read_text())
        stops = [expected["hard_stop"]] if expected.get("hard_stop") else []
        result = proof.heal_decide("caller-graft", 10, list(reversed(events)), stops)
        assert result.graft_id == "caller-graft" and result.action == expected["action"]
        events[0].latency_ms += 1
        with pytest.raises(LookupError):
            proof.heal_decide("caller-graft", 10, events, stops)
    for name in ("tampered", "valid", "tampered"):
        certificate = model("Certificate/1", PROOF / f"certificate/{name}.json")
        result = proof.verify_certificate(certificate)
        assert result.ok == (name == "valid")


def test_agent_outputs_use_caller_graft_and_demo_numbers():
    from goldgraft_contracts.tools import AGENTS as NAMES

    context = {"ledger_entries": {e["entry_hash"]: e for e in (
        json.loads(line) for line in (ROOT / "fixtures/events/demo_graft_events.jsonl"
                                    ).read_text().splitlines())}}
    for name in NAMES:
        artifacts = AGENTS.run(name, {"graft_id": "caller-graft"}, FakeToolbox())
        for schema, payload in artifacts:
            validate(schema, payload, context=context)
            if "graft_id" in payload:
                assert payload["graft_id"] == "caller-graft"
            if "producer" in payload:
                assert payload["producer"]["name"] == name
