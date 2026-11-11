"""Own review prerequisite check; independent proof remains an injected SH port."""

from goldgraft_contracts.plan5_common import Digest, OciDigest, P5Record, Ref
from pydantic import Field, StrictBool

from .workflow import candidate, committed, execution, payload


class ProofSummary(P5Record):
    evidence_class: str
    candidate_ref: Ref
    source_tree_digest: Digest
    image_digest: OciDigest
    input_refs: list[Ref]
    required_flows_observed: list[str]
    guarded_rule_ids: list[str]
    unguarded_rule_ids: list[str]
    required_failures: list[str]
    score: float = Field(ge=0, le=1)
    complete: StrictBool


def latest(p):
    tasks = p.control.snapshot(p.run_ref).tasks
    repairs = [t for t in tasks if t.task.task_id.startswith("repair-grafter-")]
    if repairs:
        n = repairs[-1].task.task_id.rsplit("-", 1)[1]
        return (
            "repair-grafter-" + n,
            "repair-build-" + n,
            "repair-new-" + n,
            "repair-guards-" + n,
            "repair-mutant-" + n,
        )
    return "grafter", "candidate-build", "candidate-new", "adversary-guards", "adversary-mutant"


def request(p):
    grafter, build, new, guards, mutant = latest(p)
    c = candidate(p, grafter)
    b = execution(p, build)
    scenario = execution(p, new)
    mutation = execution(p, mutant)
    g = payload(p, guards, "ScenarioSet/1")
    m = payload(p, guards, "MutantSet/1")
    contract = payload(p, "scribe-final", "Contract/1")
    if (
        b["source_tree_digest"] != c["tree"]
        or scenario["source_tree_digest"] != c["tree"]
        or scenario.get("complete") is not True
        or mutation.get("candidate_mutated") is not False
    ):
        raise ValueError("MISSING_EVIDENCE exact candidate execution")
    if g["unguarded_rule_ids"] or m["unguarded_rule_ids"]:
        raise ValueError("MISSING_EVIDENCE required unguarded rule")
    refs = [
        r
        for t in ["scribe-final", grafter, build, new, guards, mutant]
        for r in committed(p, t)[0].output_refs
    ]
    return dict(
        candidate_ref=c["snapshot_ref"],
        source_tree_digest=c["tree"],
        image_digest=b["image_digest"],
        input_refs=refs,
        required_flows=["capture"],
        required_rules=[r["id"] for r in contract["rules"]],
    )


def evaluate(p, proof_port):
    expected = request(p)
    if proof_port is None or getattr(proof_port, "identity", None) != "fake:SH":
        raise ValueError("MISSING_EVIDENCE independent offline proof port")
    result = ProofSummary.model_validate(proof_port.evaluate(expected))
    if result.evidence_class != "scripted" or not result.complete:
        raise ValueError("MISSING_EVIDENCE independent proof completeness")
    for key in ["candidate_ref", "source_tree_digest", "image_digest", "input_refs"]:
        if getattr(result, key) != expected[key]:
            raise ValueError("DENIED proof subject/input binding")
    if (
        set(result.required_flows_observed) != set(expected["required_flows"])
        or set(result.guarded_rule_ids) != set(expected["required_rules"])
        or result.unguarded_rule_ids
        or result.required_failures
    ):
        raise ValueError("MISSING_EVIDENCE required proof; score cannot override")
    return dict(
        evidence_class="scripted",
        offline_proof_prerequisites=True,
        merchant_review_authority=False,
        model_competence="NOT EVALUATED",
    )
