"""Bounded semantic repair advice; trusted failure evidence, immutable expectations."""

from goldgraft_contracts.plan5_common import Digest, P5Record, RelativePath

from .component import implementation
from .proof_gate import latest
from .proof_gate import request as proof_request
from .roles import component_configuration
from .workflow import candidate


class Failure(P5Record):
    fingerprint: Digest
    candidate_ref: str
    image_digest: str
    required_rule: str
    evidence_class: str


def request(p, failure_port, replacements: dict[RelativePath, str]):
    current = proof_request(p)
    if getattr(failure_port, "identity", None) != "fake:SH":
        raise ValueError("MISSING_EVIDENCE independent failure")
    failure = Failure.model_validate(failure_port.failure(current))
    if (
        failure.evidence_class != "scripted"
        or failure.candidate_ref != current["candidate_ref"]
        or failure.image_digest != current["image_digest"]
        or failure.required_rule not in current["required_rules"]
    ):
        raise ValueError("DENIED exact independent failure scope")
    tasks = p.control.snapshot(p.run_ref).tasks
    previous = [t for t in tasks if t.task.task_id.startswith("repair-grafter-")]
    if len(previous) >= 2:
        raise ValueError("MISSING_EVIDENCE semantic repair limit exhausted")
    prior_fingerprint = (
        p.artifacts.input_data(previous[-1].task.task_id)["failure_fingerprint"]
        if previous
        else None
    )
    if failure.fingerprint == prior_fingerprint:
        raise ValueError("MISSING_EVIDENCE repeated unchanged failure")
    grafter, build, new, guards, mutant = latest(p)
    c = candidate(p, grafter)
    data = implementation("Grafter").sample("candidate_patch")
    data.update(
        source_ref=c["snapshot_ref"],
        files=p.artifacts.candidate_files(grafter),
        expected_tree=c["tree"],
        replacements=replacements,
        repair_round=len(previous) + 1,
        failure_fingerprint=failure.fingerprint,
        previous_failure_fingerprint=prior_fingerprint,
    )
    data["target_plan"] = p.artifacts.committed("architect")[1][0]["payload"]
    typed = implementation("Grafter").Input.model_validate(data)
    # Same deterministic role guard used at runtime; no test/rule widening here.
    if set(replacements) - set(data["allowed_paths"]):
        raise ValueError("DENIED repair path")
    task_id = "repair-grafter-" + str(len(previous) + 1)
    p.artifacts.append_task(
        task_id=task_id,
        configuration=component_configuration("Grafter"),
        operation="candidate_patch",
        data=typed.model_dump(mode="json"),
        schemas=["ChangeList/2"],
        dependencies=[grafter, build, new, guards, mutant],
        output_policy="candidate_child",
        workspace_ref=typed.workspace_ref,
    )
    return task_id
