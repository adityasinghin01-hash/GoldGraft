"""Independent guard proposals and disposable-fork requests, never kill verdicts."""

from types import SimpleNamespace

from goldgraft_contracts.plan5_common import Ref, RelativePath, content_digest
from goldgraft_contracts.proof import MoneyContract
from pydantic import Field, StrictBool

from ..component import metadata
from .execution import (
    INLINE as EXECUTION_INLINE,
)
from .execution import (
    ExecutionInput,
    admission,
    catalog_sample,
    execution_calls,
    execution_facts,
    proposal,
    receipt,
    same_proposal,
    valid_metadata,
)
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
    if any(
        r.id in data.mutation_rule_ids and r.predicate != "paid implies capture_status == COMPLETED"
        for r in data.contract.rules
    ):
        raise ValueError("UNSUPPORTED mutation operator for predicate")
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
    if task.task.operation == "run_mutant":
        if not same_proposal(outputs[0]["payload"], draft(task, data)):
            raise ValueError("DENIED mutant execution proposal")
        r = receipt(task, observations)
        if (
            r.get("fork_ref") != data.fork_ref
            or r.get("capture_complete") is not True
            or r.get("candidate_mutated") is not False
        ):
            raise ValueError("MISSING_EVIDENCE isolated mutant capture")
    else:
        expected = {x["schema"]: x["payload"] for x in sets(task, data)}
        if len(outputs) != 2 or {x["schema"] for x in outputs} != set(expected):
            raise ValueError("DENIED guard bundle")
        for item in outputs:
            got, want = item["payload"], expected[item["schema"]]
            # Bundle ids may be unique model-chosen ids, but owner/time/scope
            # and every substantive guard/mutant field remain exact.
            if not got.get("id") or not valid_metadata(got, dict(want, id=got["id"])):
                raise ValueError("DENIED guard metadata")
            if any(
                got.get(k) != value
                for k, value in want.items()
                if k not in {"id", "producer", "created_at"}
            ):
                raise ValueError("DENIED missing guard or self-declared kill/equivalence")
        if len({x["payload"]["id"] for x in outputs}) != 2:
            raise ValueError("DENIED duplicate guard ids")
        v = observations[-1]["value"]["payload"]
        if (
            v.get("drafts") != {x["schema"]: x["payload"] for x in outputs}
            or v.get("candidate_mutated") is not False
            or v.get("status") != "QUARANTINE"
        ):
            raise ValueError("DENIED guard staging")


INLINE = {
    **EXECUTION_INLINE,
    "scenario.stage": {
        "scenario_set_ref": ("scenarios", "ScenarioSet/1"),
        "mutant_set_ref": ("mutants", "MutantSet/1"),
    },
}
PROGRESS = True


def route(data):
    # Haiku invented an unavailable guard and malformed staged calls repeatedly;
    # end that tuning line. Fork requests use the demonstrated Haiku path.
    return "sonnet" if data.fork_ref is None else "haiku8"


def facts(task, data):
    if task.task.operation == "run_mutant":
        facts = execution_facts(
            task,
            ["RawCapture/1"],
            "; fork_ref equals input fork_ref, capture_complete true, candidate_mutated false",
        )
        facts["call_policy"] = (
            "1) execution.request alone with proposal ExecutionProposal/1: task_id, operation, "
            "subject_ref, recipe_ref=catalog.recipe_ref, scenario_ref, variant, "
            "requested_output_schemas=['RawCapture/1'], expected_subject, evidence_refs. "
            "2) execution.status(request_id), never before requesting. "
            "3) If receipt_rule holds submit that same proposal; otherwise report_hold. "
            "Do not read source or catalog for this operation. Never mutate candidate."
        )
        return facts
    return {
        "max_bytes": 4096,
        "bundle_ids": {
            suffix: metadata(task, SimpleNamespace(observed_at=task.created_at), suffix)["id"]
            for suffix in ("scenarios", "mutants")
        },
        "call_policy": "Read source files exactly via unread_reads. Then scenario.stage alone "
        "with scenarios (ScenarioSet/1) and mutants (MutantSet/1) inline, not refs. "
        "Use reference_metadata with unique id per set. Supported operator: for each "
        "Contract rule in mutation_rule_ids create scenario id guard-<rule id>, family PENDING, "
        "cart {fixture:true}, steps [{driver_step:capture_pending}], rules [rule id], expect "
        "{predicate:<unchanged Contract predicate>}, assured "
        "{passes_on_old:false,flake_free_runs:0}; "
        "mutant id mutant-<rule id>, op M1, location first input file line 1, patch exactly "
        "'SYNTHETIC_OPERATOR: allow mark_paid on PENDING capture', rule=<rule id>, "
        "equivalent_suspect:false, killed_by:[]. Every unsupported rule is listed as "
        "unguarded_rule_ids in both sets, never given an invented guard. After staging "
        "submit a bundle of those same two payloads copied from the returned drafts; "
        "never change ids or metadata after staging. Staging must report QUARANTINE and "
        "candidate_mutated false, else report_hold. SH owns all kill/equivalence verdicts.",
    }


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
