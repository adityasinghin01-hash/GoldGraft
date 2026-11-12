"""One connected run across the three integrated pieces, on the local profile.

    Gupta   case -> intent -> start -> claim -> authenticated BASELINE_READ
    Singh   executed local PHP captures + agent candidate (Step 2 run directory)
    Singhal judge re-run on every capture, mutation re-judging, lifecycle review,
            public projection
    SI01    ProofPlan -> ProofResult -> PromotionDecision -> Certificate/2 attempt

Optionally a real PayPal sandbox recording (scripts/live_paypal_sandbox_payment)
is added as a non-critical provider check and re-verified from its bytes.

Local profile, stated plainly: one operator host on this Mac. Artifacts are
sealed with an HMAC key that exists only in memory for this run, so the
authenticator proves "stored by this host during this run", not an independent
collector identity. Nothing here creates authority, signs a certificate,
isolates execution or qualifies merchant delivery; those stay explicit holds.
"""

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from goldgraft_contracts.agent_runtime import ArtifactDescriptor, SubjectManifest
from goldgraft_contracts.connection_control import (
    CheckResult,
    ConnectionReadiness,
    CreateActionIntent,
    CreateCase,
    StartWorkRequest,
    WorkerOperation,
)
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_contracts.proof_evidence import ProofCheck, ProofPlan
from goldgraft_contracts.registry import validate
from goldgraft_foundation.ledger import Ledger

from integration.local_proof import LocalProof
from integration.local_shop import ROOT, SCENARIOS
from integration.private_certificates import issue_private_certificate
from integration.promotion import gate_promotion
from integration.proof_evidence import EvidenceContext, StoredArtifact, evaluate_plan
from pieces.backend.connection.service import CaseService, Principal
from pieces.backend.connection.work import WorkControl
from pieces.proof.lifecycle_evidence import (
    EvidenceState,
    Observation,
    ProofSubject,
    Requirement,
    review_lifecycle,
)
from pieces.proof.proof import Proof
from pieces.proof.review_projection import public_proof_view

SHOP_DIR = ROOT / "fixtures/shops/legacy-php-shop"
PROFILE = "local_component_this_mac"
ACCEPTED = {"PASS", "PASS_FIXED"}
PRODUCERS = {
    "collector": "local:php-collector",
    "judge": "local:proof-judge",
    "paypal": "local:paypal-sandbox-recorder",
}


def tree_digest(directory: Path) -> str:
    """Length-delimited digest of every regular file under the shop folder."""
    h = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = path.relative_to(directory).as_posix().encode()
        data = path.read_bytes()
        h.update(len(rel).to_bytes(8, "big") + rel + len(data).to_bytes(8, "big") + data)
    return h.hexdigest()


@dataclass
class LocalHost:
    """The trusted host for this one run: key, artifact store and seals."""

    tenant_id: str
    now: datetime
    key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    store: dict = field(default_factory=dict)
    seals: dict = field(default_factory=dict)

    def tag(self, *parts) -> str:
        return hmac.new(self.key, canonical_bytes(list(parts)), hashlib.sha256).hexdigest()

    def put(self, ref, schema, payload, *, role, trust, evidence_class, binding, subject):
        raw = canonical_bytes(payload)
        descriptor = ArtifactDescriptor(
            ref=ref,
            case_id=binding["case_id"],
            run_id=binding["run_id"],
            generation=binding["generation"],
            schema=schema,
            payload_digest=hashlib.sha256(raw).hexdigest(),
            byte_count=len(raw),
            subject_digest=subject,
            input_digest=binding["work_package_digest"],
            derivation_ref=None,
            producer_identity_ref=PRODUCERS[role],
            trust=trust,
            evidence_class=evidence_class,
            created_at=self.now,
            expires_at=self.now + timedelta(hours=1),
        )
        self.store[ref] = StoredArtifact(descriptor, raw)
        self.seals[ref] = self.tag(descriptor.model_dump(mode="json", by_alias=True), role)

    def resolve(self, ref):
        return self.store.get(ref)

    def authenticate(self, record, context, owner_role):
        d = record.descriptor
        expected = self.seals.get(d.ref)
        return (
            expected is not None
            and context.tenant_id == self.tenant_id
            and d.producer_identity_ref == PRODUCERS.get(owner_role)
            and hmac.compare_digest(
                expected, self.tag(d.model_dump(mode="json", by_alias=True), owner_role)
            )
        )


def _check(check_id, kind, *, schema, cls, trust, critical, owner, subject_ref, sd, wp, rules=()):
    return ProofCheck(
        check_id=check_id,
        flow_id="checkout",
        kind=kind,
        rule_ids=list(rules),
        subject_manifest_ref=subject_ref,
        subject_manifest_digest=sd,
        input_digest=wp,
        required_schema=schema,
        required_evidence_class=cls,
        required_trust=trust,
        critical=critical,
        owner_role=owner,
    )


def _sandbox_ok(capture) -> bool:
    """Re-verify a live sandbox recording from its bytes: approved, captured, refunded."""
    replies = {}
    for ex in capture.exchanges:
        if ex.direction == "PAYPAL_TO_SHOP" and isinstance(ex.body_json, dict):
            replies.setdefault((ex.method, ex.url.rsplit("/", 2)[-2]), []).append(ex.body_json)
    get_capture = replies.get(("GET", "captures"), [{}])[-1]
    get_refund = replies.get(("GET", "refunds"), [{}])[-1]
    order = replies.get(("GET", "orders"), [{}])[-1]
    return (
        order.get("status") == "APPROVED"
        and get_capture.get("status") == "COMPLETED"
        and get_refund.get("status") == "COMPLETED"
        and get_capture.get("amount") == get_refund.get("amount")
        and bool(get_capture.get("id"))
        and bool(get_refund.get("id"))
    )


AGENT_FILES = ("RESULT.json", "CHANGES.json", "OUTPUTS.json", "MUTATIONS.json", "EDGES.json")


def connect_run(
    agent_run_dir: Path,
    state_dir: Path,
    *,
    sandbox_capture: Path | None = None,
    php: str = "php",
    execute=None,
    now=None,
):
    """agent_run_dir holds the agents' candidate (RESULT/CHANGES/OUTPUTS); it is
    executed again here, under the work id Gupta's control issues."""
    agent_run_dir, state_dir = Path(agent_run_dir), Path(state_dir)
    now = now or datetime.now(UTC).replace(microsecond=0)
    state_dir.mkdir(parents=True, exist_ok=True)
    if (state_dir / "control.sqlite").exists():
        raise ValueError(f"{state_dir} already holds a control ledger; use a new folder")
    if execute is None:
        from scripts.live_local_shop_proof import check as execute
    reference = ROOT / "fixtures/proof/legacy-php-shop"

    # --- Gupta: case, readiness from actual digests, start, claim, operation ----------
    tenant = "local-tenant"
    host = LocalHost(tenant, now)
    source = tree_digest(SHOP_DIR)
    work_package = content_digest(
        {
            name: hashlib.sha256((agent_run_dir / name).read_bytes()).hexdigest()
            for name in ("CHANGES.json", "OUTPUTS.json")
        }
    )
    scope = hashlib.sha256((reference / "contract.json").read_bytes()).hexdigest()
    runtime = content_digest({"profile": PROFILE, "paypal": "local simulator"})
    epochs = {"local-shop": 1}
    ledger = Ledger(f"sqlite:///{state_dir / 'control.sqlite'}")
    cases = CaseService(ledger, clock=lambda: now)
    owner = Principal("operator", tenant, now + timedelta(hours=1), "csrf")
    case = cases.create_case(owner, CreateCase(shop_url="https://legacy-php-shop.example"), "case")
    ready_fields = dict(
        readiness_id="local-readiness",
        case_id=case.case_id,
        actor_id="operator",
        work_package_ref="local:work-package",
        work_package_digest=work_package,
        resource_graph_digest=content_digest({"shop": source, "host": PROFILE}),
        source_snapshot_refs=["local:legacy-php-shop"],
        source_manifest_digest=source,
        resource_evidence_digests={"local-shop": source},
        binding_epochs=epochs,
        scope_digest=scope,
        processing_policy_digest=content_digest("no-model-calls-in-proof"),
        runtime_profile_digest=runtime,
        fixture_profile_digest=content_digest(list(SCENARIOS)),
        checks=[
            CheckResult(
                check_id="operator_authority",
                status="pass",
                evidence_refs=["local:operator-run"],
                checked_at=now,
                expires_at=now + timedelta(minutes=30),
                recovery_code=None,
            )
        ],
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    draft = ConnectionReadiness(**ready_fields, readiness_digest="0" * 64)
    readiness = draft.model_copy(
        update={
            "readiness_digest": content_digest(
                draft.model_dump(mode="json", exclude={"readiness_digest"})
            )
        }
    )

    def op_tag(op):
        return "local-hmac:" + host.tag(op.model_dump(mode="json", exclude={"authenticity_ref"}))

    control = WorkControl(
        cases,
        readiness_resolver=lambda *args: readiness,
        required_checks={"operator_authority"},
        authenticate_operation=lambda _p, op: hmac.compare_digest(op.authenticity_ref, op_tag(op)),
        authenticate_termination=lambda *_: False,
    )
    action = control.create_intent(
        owner,
        case.case_id,
        CreateActionIntent(
            readiness_id=readiness.readiness_id, readiness_digest=readiness.readiness_digest
        ),
        "intent",
    )
    receipt = control.start(
        owner,
        case.case_id,
        StartWorkRequest(
            action_id=action.action_id,
            readiness_id=readiness.readiness_id,
            readiness_digest=readiness.readiness_digest,
        ),
        "start",
    )
    assignment = content_digest({"work": receipt.work_id, "worker": "local-php-collector"})
    generation = control.claim(
        case.case_id, receipt.work_id, worker_id="local-php-collector", assignment_digest=assignment
    )
    operation = WorkerOperation(
        operation_id="baseline-read",
        work_id=receipt.work_id,
        generation=generation,
        worker_id="local-php-collector",
        kind="BASELINE_READ",
        assignment_digest=assignment,
        work_package_digest=work_package,
        resource_graph_digest=readiness.resource_graph_digest,
        source_manifest_digest=source,
        scope_digest=scope,
        observed_digest=tree_digest(SHOP_DIR),  # The worker re-reads the source now.
        runtime_profile_digest=runtime,
        started_at=now,
        finished_at=now,
        result="verified",
        evidence_refs=["local:legacy-php-shop"],
        authenticity_ref="local-hmac:pending",
    )
    operation = operation.model_copy(update={"authenticity_ref": op_tag(operation)})
    supervisor = Principal("supervisor", tenant, now + timedelta(hours=1), "csrf", "service")
    collector = control.operation(supervisor, operation)
    status = control.status(owner, case.case_id, action.action_id).status.state
    if status != "operation_started":
        raise ValueError(f"work did not start: {status}")

    # --- The worker executes the agents' candidate under this work id ---------------
    run_dir = state_dir / "runs" / receipt.work_id
    run_dir.mkdir(parents=True)
    for name in AGENT_FILES:
        if (agent_run_dir / name).exists():
            (run_dir / name).write_bytes((agent_run_dir / name).read_bytes())
    report = execute(run_dir, run_dir / "local-proof", php=php)  # Real PHP execution.
    local = LocalProof(run_dir)  # Re-checks every capture digest and re-runs the judge.
    evidence_run = report["run_id"] + "-local-php"

    # --- Evidence: subject + every check's bytes, sealed by this host ---------------
    binding = dict(
        case_id=case.case_id,
        run_id=evidence_run,
        generation=generation,
        resource_epochs=epochs,
        scope_digest=scope,
        work_package_digest=work_package,
        policy_digest=readiness.processing_policy_digest,
    )
    subject = SubjectManifest(
        source_snapshot_refs=["local:legacy-php-shop"],
        source_tree_digest=source,
        oci_manifest_digest=None,  # No image was built: Docker is not on this host.
        config_digest=None,
        runtime_profile_digest=runtime,
        scope_digest=scope,
    )
    sd = content_digest(subject)
    sref = "local:subject"
    put = dict(binding=binding, subject=sd)
    host.put(
        sref,
        "SubjectManifest/1",
        subject,
        role="collector",
        trust="collector_observed",
        evidence_class="component_offline",
        **put,
    )
    common = dict(subject_ref=sref, sd=sd, wp=work_package)
    checks = []
    proof = Proof()
    contract = validate(
        "Contract/1",
        json.loads((ROOT / "fixtures/proof/legacy-php-shop/contract.json").read_bytes()),
    )
    outputs = json.loads((run_dir / "OUTPUTS.json").read_bytes())
    target_plan = validate(
        "TargetPlan/1",
        next(o["payload"] for o in outputs["architect"] if o["schema"] == "TargetPlan/1"),
    )
    for scenario in SCENARIOS:
        for kind, variant in (("baseline", "OLD"), ("candidate", "NEW")):
            ref = f"{kind}:{scenario}"
            name = f"{scenario}.{variant}.json"
            capture = json.loads((run_dir / "local-proof" / name).read_bytes())
            host.put(
                ref,
                "RawCapture/1",
                capture,
                role="collector",
                trust="collector_observed",
                evidence_class="component_offline",
                **put,
            )
            checks.append(
                _check(
                    ref,
                    kind,
                    schema="RawCapture/1",
                    cls="component_offline",
                    trust="collector_observed",
                    critical=True,
                    owner="collector",
                    **common,
                )
            )
        verdict = local.rows[SCENARIOS.index(scenario)]["verdict"]
        ref = f"scenario:{scenario}"
        host.put(
            ref,
            "Verdict/1",
            verdict.model_dump(mode="json", by_alias=True),
            role="judge",
            trust="deterministic_result",
            evidence_class="component_offline",
            **put,
        )
        checks.append(
            _check(
                ref,
                "scenario",
                schema="Verdict/1",
                cls="component_offline",
                trust="deterministic_result",
                critical=True,
                owner="judge",
                rules=sorted({h.rule for h in verdict.rule_hits}),
                **common,
            )
        )
    mutation_grades = {}
    for item in report.get("candidate_mutations", []):
        mutant = validate("Mutant/1", item["mutant"])
        scenario = item["scenario_id"]
        path = run_dir / "local-proof/mutants" / item["capture_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["capture_sha256"]:
            raise ValueError("mutant recording digest mismatch")
        mutated = validate("RawCapture/1", json.loads(path.read_bytes()))
        old, twin, _ = local.streams[scenario]
        regraded = proof.judge(old, twin, proof.to_cmel(mutated), contract, target_plan)
        mutation_grades[mutant.id] = str(regraded.grade)
        ref = f"mutation:{mutant.id}"
        host.put(
            ref,
            "Mutant/1",
            mutant.model_dump(mode="json", by_alias=True),
            role="judge",
            trust="deterministic_result",
            evidence_class="component_offline",
            **put,
        )
        checks.append(
            _check(
                ref,
                "mutation",
                schema="Mutant/1",
                cls="component_offline",
                trust="deterministic_result",
                critical=True,
                owner="judge",
                rules=[mutant.rule],
                **common,
            )
        )
    unguarded = report.get("unguarded_critical_rule_ids", [])
    for rule in unguarded:  # Nothing stored: no executed mutation guards this rule yet.
        checks.append(
            _check(
                f"domain_rule:{rule}",
                "domain_rule",
                schema="Mutant/1",
                cls="component_offline",
                trust="deterministic_result",
                critical=True,
                owner="judge",
                rules=[rule],
                **common,
            )
        )
    # A PayPal sandbox recording is its own run (GoldGraft's sandbox app, not this
    # shop's checkout), so it is re-verified from its bytes as a separate provider
    # check and never counted toward this shop run's plan.
    provider_checks = {}
    if sandbox_capture is not None:
        live = validate("RawCapture/1", json.loads(Path(sandbox_capture).read_bytes()))
        replies = [e.body_json for e in live.exchanges if e.direction == "PAYPAL_TO_SHOP"]
        provider_checks["paypal_sandbox"] = {
            "run_id": live.run_id,
            "evidence_class": "real_provider",
            "reverified_from_recording": _sandbox_ok(live),
            "exchanges": len(live.exchanges),
            "ids": sorted({r["id"] for r in replies if isinstance(r, dict) and r.get("id")}),
            "scope": "GoldGraft sandbox app; not this shop's checkout",
        }
    # Critical gates with no evidence on this host: they must stay visible holds.
    checks.append(
        _check(
            "payment:shop-checkout-paypal",
            "payment",
            schema="RawCapture/1",
            cls="real_payment",
            trust="collector_observed",
            critical=True,
            owner="paypal",
            **common,
        )
    )
    checks.append(
        _check(
            "isolation:runner",
            "isolation",
            schema="RawCapture/1",
            cls="isolation_qualified",
            trust="collector_observed",
            critical=True,
            owner="collector",
            **common,
        )
    )

    plan_fields = dict(
        **binding,
        plan_id=f"plan-{evidence_run}",
        checks=[c.model_dump(mode="json") for c in checks],
        exclusions=[],
        created_at=now.isoformat().replace("+00:00", "Z"),
        expires_at=(now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
    )
    plan = ProofPlan.model_validate({**plan_fields, "plan_digest": content_digest(plan_fields)})
    context = EvidenceContext(
        tenant_id=tenant,
        **binding,
        plan_digest=plan.plan_digest,
        required_checks=tuple(plan.checks),
        now=now + timedelta(seconds=1),
        critical_rule_ids=frozenset(unguarded),
    )

    def verify_check(payload, check, _subject, _context):
        scenario = check.check_id.split(":", 1)[-1]
        if check.kind in {"baseline", "candidate"}:
            variant = "OLD" if check.kind == "baseline" else "NEW"
            return (payload.scenario_id, str(payload.variant)) == (scenario, variant)
        if check.kind == "scenario":
            return str(payload.grade) in ACCEPTED and payload.scenario_id == scenario
        if check.kind == "mutation":
            return mutation_grades.get(payload.id) == "PROBLEM"
        return False

    ports = dict(resolve=host.resolve, authenticate=host.authenticate, verify_check=verify_check)
    result = evaluate_plan(plan, context, **ports)

    # --- Promotion: no live traffic, so the posterior advice itself holds ----------
    advice = proof.heal_decide(evidence_run, 0, [])
    promotion = gate_promotion(advice, plan, result, context, **ports)

    # --- Singhal's lifecycle review and public projection --------------------------
    def subject_for(kind):
        return ProofSubject(
            case_id=case.case_id,
            run_id=evidence_run,
            generation=generation,
            fence=content_digest(epochs),
            scope_digest=scope,
            package_digest=work_package,
            image_digest="",
            config_digest="",  # No image/config identity exists here.
            runtime_identity=PROFILE,
            origin="legacy-php-shop",
        )

    states = {r.check_id: r for r in result.results}
    required = {
        "baseline": Requirement(subject_for("baseline")),
        "candidate": Requirement(subject_for("candidate")),
    }
    observations = [
        Observation(
            kind,
            subject_for(kind),
            EvidenceState.VERIFIED
            if all(states[c.check_id].state == "verified" for c in plan.checks if c.kind == kind)
            else EvidenceState.UNKNOWN,
            content_digest([c.check_id for c in plan.checks if c.kind == kind]),
            False,
        )
        for kind in ("baseline", "candidate")
    ]
    review = review_lifecycle(required, observations)
    public = public_proof_view(review, checked_at=now, public_evidence_ref="public:local-summary")

    # --- Certificate/2 attempt: stops at the first real gate ------------------------
    review_digest = content_digest(
        [
            str(review.disposition),
            review.verified_count,
            [(g.check, str(g.reason)) for g in review.gaps],
        ]
    )
    context_cert = EvidenceContext(
        **{
            **context.__dict__,
            "review_bundle_ref": "local:review",
            "review_bundle_digest": review_digest,
        }
    )
    candidate = [c for c in plan.checks if c.kind == "candidate"][0]
    claims = dict(
        **binding,
        cert_id=f"cert-{evidence_run}",
        review_bundle_ref="local:review",
        review_bundle_digest=review_digest,
        subject_manifest_ref=candidate.subject_manifest_ref,
        subject_manifest_digest=sd,
        proof_plan_ref=plan.plan_id,
        proof_plan_digest=plan.plan_digest,
        proof_result_ref=result.result_id,
        proof_result_digest=result.result_digest,
        ledger_root=content_digest([e.model_dump(mode="json") for e in ledger.read(case.case_id)]),
        source_route="local_folder",
        git_source=None,
        signer_kind="trusted_service",
        signer_identity_ref="local:no-signer",
        workflow_identity=None,
        workflow_sha=None,
        qualification_scope="component_only",
        qualification_evidence_refs=[result.result_id],
        issued_at=context.now,
        expires_at=now + timedelta(minutes=20),
    )
    try:
        issue_private_certificate(claims, plan, result, context_cert, **ports)
        certificate = {"issued": True}
    except ValueError as exc:
        certificate = {"issued": False, "held_at": str(exc)}

    by_state: dict[str, list[str]] = {}
    for r in result.results:
        by_state.setdefault(r.state, []).append(r.check_id)
    for name, record in (
        ("ProofPlan.json", plan),
        ("ProofResult.json", result),
        ("PromotionDecision.json", promotion),
        ("PublicProofView.json", public),
    ):
        (state_dir / name).write_text(record.model_dump_json(indent=2, by_alias=True) + "\n")
    summary = {
        "profile": PROFILE,
        "evidence_run": report["run_id"],
        "gupta_control": {
            "case_id": case.case_id,
            "work_id": receipt.work_id,
            "generation": generation,
            "baseline_read_accepted": collector.operation_id,
            "status": status,
        },
        "proof_plan": {
            "checks": len(plan.checks),
            "critical": sum(c.critical for c in plan.checks),
            "digest": plan.plan_digest,
        },
        "proof_result": {
            "outcome": result.outcome,
            "reason_codes": result.reason_codes,
            "by_state": by_state,
        },
        "mutations_rejudged": mutation_grades,
        "provider_checks": provider_checks,
        "promotion": {
            "action": promotion.action,
            "reason": promotion.reason_code,
            "advice": str(advice.action),
            "advice_reason": advice.reason,
        },
        "lifecycle_review": {
            "disposition": str(review.disposition),
            "gaps": [[g.check, str(g.reason)] for g in review.gaps],
        },
        "public_view": {
            "integrity": public.integrity,
            "metrics": {m.name: m.value for m in public.summary_metrics},
        },
        "certificate": certificate,
        "holds": [
            *(f"{c}: no evidence on this host" for c in by_state.get("missing", [])),
            "image: no OCI image built (Docker not on this host), so the lifecycle review holds",
            "promotion: no live buyer traffic, so the rollout advice is HOLD",
            "signer: no qualified signer attached to this run",
        ],
    }
    (state_dir / "CONNECTED_RUN.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--sandbox-capture", type=Path)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            connect_run(args.run_dir, args.state_dir, sandbox_capture=args.sandbox_capture),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
