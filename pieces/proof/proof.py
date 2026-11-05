"""Offline implementation of the GoldGraft proof interface."""

from collections.abc import Collection, Mapping, Sequence
from fractions import Fraction

from goldgraft_contracts.api import CertificateVerifyResult, VerifyCheckName
from goldgraft_contracts.interfaces import MutantRuns
from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.proof import (
    Certificate,
    Grade,
    MoneyContract,
    Mutant,
    ProofStrength,
    Verdict,
)
from goldgraft_contracts.runner import GuardEvent, HealDecision, HealStats, RawCapture
from goldgraft_contracts.survey import TargetPlan

from .certificate import CertificateCheck, verify_certificate
from .cmel import to_cmel
from .judge import judge
from .lifecycle import LifecycleEvidence
from .posterior import probabilities

STAGES = (0, 1, 10, 50, 100)
THRESHOLD = Fraction(19, 20)


class Proof:
    def to_cmel(self, capture: RawCapture) -> list[MoneyEvent]:
        return to_cmel(capture)

    def judge(
        self,
        old: Sequence[MoneyEvent],
        old_twin: Sequence[MoneyEvent],
        new: Sequence[MoneyEvent],
        contract: MoneyContract,
        target_plan: TargetPlan,
        *,
        old_capture: RawCapture | None = None,
        new_capture: RawCapture | None = None,
        old_lifecycle: LifecycleEvidence | None = None,
        new_lifecycle: LifecycleEvidence | None = None,
    ) -> Verdict:
        return judge(
            old,
            old_twin,
            new,
            contract,
            target_plan,
            old_capture=old_capture,
            new_capture=new_capture,
            old_lifecycle=old_lifecycle,
            new_lifecycle=new_lifecycle,
        )

    def proof_strength(
        self,
        mutants: Sequence[Mutant],
        runs: MutantRuns,
        *,
        reviewed_equivalent: Collection[str] = (),
    ) -> ProofStrength:
        ids = {mutant.id for mutant in mutants}
        dropped = set(reviewed_equivalent)
        if len(ids) != len(mutants) or dropped - ids or ids - runs.keys():
            raise ValueError("Mutant IDs, run outcomes, and equivalence review must agree")
        killed_ids = {mutant_id for mutant_id in ids if Grade.PROBLEM in runs[mutant_id].values()}
        if dropped & killed_ids:
            raise ValueError("A killed mutant cannot be reviewed as equivalent")
        total, killed = len(ids), len(killed_ids)
        retained = total - len(dropped)
        return ProofStrength(
            total=total,
            equivalent_dropped=len(dropped),
            killed=killed,
            score=killed / retained if retained else 0.0,
        )

    def heal_decide(
        self,
        graft_id: str,
        stage_pct: int,
        events: Sequence[GuardEvent],
        hard_stops: Sequence[str] = (),
    ) -> HealDecision:
        stage_index = STAGES.index(stage_pct)
        approved = {"OLD": set(), "NEW": set()}
        captured = {"OLD": set(), "NEW": set()}
        for event in events:
            if event.graft_id != graft_id:
                continue
            order = (event.shop_id, event.order_ref)
            if event.event == "APPROVED":
                approved[event.path].add(order)
            elif event.event == "CAPTURED":
                captured[event.path].add(order)

        n_old, n_new = len(approved["OLD"]), len(approved["NEW"])
        success_old = len(approved["OLD"] & captured["OLD"])
        success_new = len(approved["NEW"] & captured["NEW"])
        safe, worse = probabilities(n_old, success_old, n_new, success_new)
        hard_stop = next((stop for stop in hard_stops if stop), None)
        if hard_stop:
            action, target, reason = "CUTBACK", 0, hard_stop
        elif worse >= THRESHOLD:
            action, target, reason = "CUTBACK", 0, "Posterior probability of worse exceeds 0.95"
        elif stage_pct < 100 and n_new >= 30 and safe >= THRESHOLD:
            action, target, reason = "STEP_UP", STAGES[stage_index + 1], "Enough safe NEW trials"
        else:
            action, target = "HOLD", stage_pct
            reason = "Thin data" if n_new < 30 else "Posterior inconclusive"
            if stage_pct == 100 and safe >= THRESHOLD:
                reason = "Already at full rollout"
        return HealDecision(
            graft_id=graft_id,
            from_stage_pct=stage_pct,
            to_stage_pct=target,
            action=action,
            reason=reason,
            hard_stop=hard_stop,
            stats=HealStats(
                n_old=n_old,
                n_new=n_new,
                success_old=success_old,
                success_new=success_new,
                prob_new_not_worse=float(safe),
                threshold=float(THRESHOLD),
            ),
        )

    def recipe_confidence(self, passes: int, fails: int) -> float:
        if type(passes) is not int or type(fails) is not int or min(passes, fails) < 0:
            raise ValueError("recipe outcomes must be nonnegative integer counts")
        return (passes + 1) / (passes + fails + 2)

    def verify_certificate(
        self,
        certificate: Certificate,
        *,
        verifiers: Mapping[VerifyCheckName, CertificateCheck] | None = None,
    ) -> CertificateVerifyResult:
        return verify_certificate(certificate, verifiers or {})
