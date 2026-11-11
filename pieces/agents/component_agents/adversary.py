"""Independent guard proposals and disposable-fork requests, never kill verdicts."""

from types import SimpleNamespace

from goldgraft_contracts.plan5_common import Ref, RelativePath, content_digest
from goldgraft_contracts.proof import MoneyContract
from pydantic import Field, StrictBool

from ..component import metadata
from .execution import ExecutionInput, admission, catalog_sample, execution_calls, proposal, receipt
from .scribe import sample as scribe_sample


class Input(ExecutionInput):
    source_ref: Ref
    files: dict[RelativePath, str] = Field(min_length=1, max_length=4)
    contract: MoneyContract
    candidate_ref: Ref
    fork_ref: Ref | None
    disposable_fork: StrictBool
    scenario_ref: Ref | None
    variant: str | None
    mutation_rule_ids: list[str] = Field(max_length=8)


def admit(task, data):
    admission(data)
    if not data.contract.rules or set(data.mutation_rule_ids) - {r.id for r in data.contract.rules}:
        raise ValueError("MISSING_EVIDENCE Contract mutation catalog")
    if task.task.operation == "run_mutant" and (
        not data.disposable_fork
        or data.fork_ref != data.subject_ref
        or data.fork_ref == data.candidate_ref
        or data.variant != "NEW"
        or data.scenario_ref is None
    ):
        raise ValueError("DENIED mutant requires separately owned disposable fork")


def schemas(operation, data):
    return (
        ["ExecutionProposal/1"] if operation == "run_mutant" else ["ScenarioSet/1", "MutantSet/1"]
    )


def sets(task, data):
    packet = SimpleNamespace(observed_at=task.created_at)
    scenarios = []
    mutants = []
    unguarded = []
    for r in data.contract.rules:
        if r.id not in data.mutation_rule_ids:
            unguarded.append(r.id)
            continue
        sid = "guard-" + r.id
        scenarios.append(
            dict(
                id=sid,
                family="PENDING",
                cart={"fixture": True},
                steps=[{"driver_step": "capture_pending"}],
                rules=[r.id],
                expect={"predicate": r.predicate},
                assured={"passes_on_old": False, "flake_free_runs": 0},
            )
        )
        mutants.append(
            dict(
                id="mutant-" + r.id,
                op="M1",
                location={"file": next(iter(data.files)), "line": 1},
                patch="SYNTHETIC_OPERATOR: allow mark_paid on PENDING capture",
                rule=r.id,
                equivalent_suspect=False,
                killed_by=[],
            )
        )
    return [
        dict(
            schema="ScenarioSet/1",
            payload={
                **metadata(task, packet, "scenarios"),
                "scenarios": scenarios,
                "unguarded_rule_ids": unguarded,
            },
        ),
        dict(
            schema="MutantSet/1",
            payload={
                **metadata(task, packet, "mutants"),
                "mutants": mutants,
                "unguarded_rule_ids": unguarded,
            },
        ),
    ]


def draft(task, data):
    return proposal(task, data, ["RawCapture/1"], scenario=data.scenario_ref, variant=data.variant)


def requests(task, data):
    if task.task.operation == "run_mutant":
        return execution_calls(task, draft(task, data))
    values = sets(task, data)
    return [
        dict(
            tool="source.read",
            arguments={"snapshot_ref": data.source_ref, "path": p, "max_bytes": 4096},
        )
        for p in data.files
    ] + [
        dict(
            tool="scenario.stage",
            arguments={"scenario_set_ref": "inline:scenarios", "mutant_set_ref": "inline:mutants"},
            drafts={
                "scenario_set_ref": values[0]["payload"],
                "mutant_set_ref": values[1]["payload"],
            },
        )
    ]


def synthesize(task, data, packet, observations):
    return (
        [dict(schema="ExecutionProposal/1", payload=draft(task, data))]
        if task.task.operation == "run_mutant"
        else sets(task, data)
    )


def review(task, data, packet, outputs, observations):
    if outputs != synthesize(task, data, packet, observations):
        raise ValueError("DENIED missing guard or self-declared kill/equivalence")
    if task.task.operation == "run_mutant":
        r = receipt(task, observations)
        if (
            r.get("fork_ref") != data.fork_ref
            or r.get("capture_complete") is not True
            or r.get("candidate_mutated") is not False
        ):
            raise ValueError("MISSING_EVIDENCE isolated mutant capture")
    else:
        v = observations[-1]["value"]["payload"]
        if (
            v.get("drafts") != {x["schema"]: x["payload"] for x in outputs}
            or v.get("candidate_mutated") is not False
            or v.get("status") != "QUARANTINE"
        ):
            raise ValueError("DENIED guard staging")


def inspect(outputs):
    if outputs[0]["schema"] == "ExecutionProposal/1":
        return {
            "fork": outputs[0]["payload"]["subject_ref"],
            "kill_and_equivalence_owner": "SH; NOT EVALUATED",
        }
    return dict(
        scenarios=len(outputs[0]["payload"]["scenarios"]),
        mutants=len(outputs[1]["payload"]["mutants"]),
        unguarded_rule_ids=outputs[0]["payload"]["unguarded_rule_ids"],
        kill_and_equivalence_owner="SH; NOT EVALUATED",
        candidate_mutated=False,
    )


def sample(operation):
    s = scribe_sample("scribe_final")
    return dict(
        subject_ref="fixture:mutant-fork" if operation == "run_mutant" else "fixture:candidate",
        catalog=catalog_sample(),
        source_tree_digest=content_digest("candidate"),
        execution_state="observed",
        execution_result=dict(
            fork_ref="fixture:mutant-fork", capture_complete=True, candidate_mutated=False
        ),
        source_ref="fixture:candidate",
        files=s["files"],
        contract={"shop_id": s["shop_id"], "rules": s["normative_rules"]},
        candidate_ref="fixture:candidate",
        fork_ref="fixture:mutant-fork" if operation == "run_mutant" else None,
        disposable_fork=operation == "run_mutant",
        scenario_ref="fixture:mutant-scenario" if operation == "run_mutant" else None,
        variant="NEW" if operation == "run_mutant" else None,
        mutation_rule_ids=[s["normative_rules"][0]["id"]],
    )
