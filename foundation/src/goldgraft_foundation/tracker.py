"""Ledger-derived Graft Cycle and durable worker leases/retries.

Workers receive a snapshot and return data. Foundation commits returned artifacts
and the next STAGE atomically. External side effects belong to the worker and
must use StepContext.idempotency_key; arbitrary external effects cannot be made
exactly-once by a database transaction. Timed-out sync workers cannot be killed;
their late return values are discarded and must not perform unguarded effects.
"""

import asyncio
import inspect
import queue
import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from goldgraft_contracts.common import Stage
from goldgraft_contracts.stages import StageChange
from sqlalchemy import and_, select

from .ledger import Ledger, step_runs

STAGES = frozenset({str(stage) for stage in Stage} |
                   {"LANE_NO_CODE", "LANE_NO_RUNTIME", "LANE_MAP_ONLY"})
ARROWS = {stage: frozenset(targets) for stage, targets in {
    "CREATED": {"GATED"},
    "GATED": {"SURVEYED"},
    # Builder works inside SURVEYED: a shop that cannot be run goes straight to
    # LANE_NO_RUNTIME; a built shop that cannot be driven/recorded goes there from BUILT.
    "SURVEYED": {"BUILT", "LANE_NO_CODE", "LANE_NO_RUNTIME", "LANE_MAP_ONLY"},
    "BUILT": {"RECORDED", "LANE_NO_RUNTIME"},
    "LANE_NO_CODE": {"LINKS_PROVEN"},
    "LINKS_PROVEN": {"DELIVERED"},
    "DELIVERED": set(),
    # No runtime: map + plan + rewrite + static checks; certificate is PARTIAL.
    "LANE_NO_RUNTIME": {"PARTIAL"},
    # Map only: the Root Map + Target Plan are the delivery.
    "LANE_MAP_ONLY": {"DELIVERED"},
    "RECORDED": {"CONTRACTED"},
    "CONTRACTED": {"ATTACK_PLANNED"},
    "ATTACK_PLANNED": {"GRAFTED"},
    "GRAFTED": {"PROVING"},
    "PROVING": {"REPAIRING", "CERTIFIED", "PARTIAL", "FAILED"},
    "REPAIRING": {"PROVING"},
    "CERTIFIED": {"PR_OPEN"},
    "PARTIAL": {"PR_OPEN"},
    "PR_OPEN": {"MERGED"},
    "MERGED": {"SHADOW"},
    "SHADOW": {"HEAL_1", "CUTBACK"},
    "HEAL_1": {"HEAL_10", "CUTBACK"},
    "HEAL_10": {"HEAL_50", "CUTBACK"},
    "HEAL_50": {"LIVE_100", "CUTBACK"},
    "LIVE_100": {"CLEANUP_PR", "CUTBACK"},
    "CUTBACK": {"GRAFTED"},
    "CLEANUP_PR": {"DONE"},
    "DONE": set(),
    "FAILED": set(),
}.items()}
# Explicit requirement: any stage may record a reasoned dead letter, including
# terminal stages. FAILED->FAILED records an additional dead-letter reason.
ARROWS = {stage: targets | {"FAILED"} for stage, targets in ARROWS.items()}
PERCENTAGES = {"SHADOW": 0, "HEAL_1": 1, "HEAL_10": 10, "HEAL_50": 50, "LIVE_100": 100}
PRODUCER = {"kind": "service", "name": "step-tracker", "version": "1"}
ACTOR = {"kind": "service", "name": "step-tracker"}


class IllegalTransition(ValueError):
    pass


@dataclass(frozen=True)
class StageResult:
    next_stage: str | None
    reason: str
    artifacts: list[tuple[str, object]] = field(default_factory=list)


@dataclass(frozen=True)
class StepContext:
    graft_id: str
    stage: str
    attempt: int
    idempotency_key: str
    entries: tuple


@dataclass(frozen=True)
class WorkerSpec:
    worker: Callable
    timeout: float
    max_retries: int


class StepTracker:
    runs = step_runs

    def __init__(self, ledger: Ledger, *, max_repair_rounds=2, timeout=60.0,
                 max_retries=2, backoff_base=1.0, backoff_cap=60.0,
                 clock=time.time, jitter=random.random, lease_grace=5.0):
        if max_repair_rounds < 0 or max_retries < 0 or timeout <= 0:
            raise ValueError("invalid repair/retry/timeout policy")
        if backoff_base < 0 or backoff_cap < 0 or lease_grace < 0:
            raise ValueError("invalid backoff/lease policy")
        self.ledger = ledger
        self.max_repair_rounds = max_repair_rounds
        self.timeout, self.max_retries = timeout, max_retries
        self.backoff_base, self.backoff_cap = backoff_base, backoff_cap
        self.clock, self.jitter, self.lease_grace = clock, jitter, lease_grace
        self.workers = {}

    @staticmethod
    def _last(entries):
        return next((entry for entry in reversed(entries)
                     if entry.type == "STAGE" and entry.schema_ == "StageChange/1"), None)

    def current_entry(self, graft_id):
        return self._last(self.ledger.read(graft_id))

    def current_stage(self, graft_id):
        entry = self.current_entry(graft_id)
        return entry.payload["to_stage"] if entry else None

    def start(self, graft_id, *, reason="Graft created", actor=None):
        with self.ledger.transaction(graft_id) as tx:
            previous = self._last(tx.read())
            if previous:
                return previous
            return tx.append("STAGE", PRODUCER, "StageChange/1", payload=dict(
                graft_id=graft_id, from_stage=None, to_stage="CREATED", attempt=1,
                reason=reason, actor=actor or ACTOR, evidence_refs=[]),
                idempotency_key="tracker:start")

    def _transition(self, tx, target, reason, actor=None, evidence_refs=None, key=None):
        history = tx.read()
        current = self._last(history)
        if current is None:
            raise IllegalTransition("graft must be started first")
        source = current.payload["to_stage"]
        if target not in ARROWS[source]:
            raise IllegalTransition(f"illegal arrow {source} -> {target}")
        if target == "REPAIRING" and sum(
            entry.type == "STAGE" and entry.schema_ == "StageChange/1" and
            entry.payload["to_stage"] == "REPAIRING" for entry in history
        ) >= self.max_repair_rounds:
            raise IllegalTransition("repair round limit reached")
        refs = list(evidence_refs or [])
        if source in PERCENTAGES and target in PERCENTAGES:
            proof = next((entry for entry in reversed(history)
                          if entry.seq > current.seq and entry.schema_ == "HealDecision/1"
                          and entry.producer.kind == "service"
                          and (body := self.ledger.payload(entry))["graft_id"] == tx.graft_id
                          and body["action"] == "STEP_UP"
                          and body["from_stage_pct"] == PERCENTAGES[source]
                          and body["to_stage_pct"] == PERCENTAGES[target]), None)
            if proof is None:
                raise IllegalTransition("fresh matching service STEP_UP HealDecision required")
            refs.append(proof.entry_hash)
        if target == "MERGED":
            consent = next((entry for entry in reversed(history)
                            if entry.seq > current.seq and entry.type == "MESSAGE"
                            and entry.schema_ == "StageChange/1"
                            and entry.producer.kind == "service"
                            and entry.producer.name == "merchant-consent"
                            and (body := self.ledger.payload(entry))["graft_id"] == tx.graft_id
                            and body["from_stage"] == "PR_OPEN"
                            and body["to_stage"] == "MERGED"
                            and body["evidence_refs"]), None)
            if consent is None:
                raise IllegalTransition("merchant consent entry required for this PR_OPEN visit")
            refs.append(consent.entry_hash)
        attempt = 1 + sum(entry.type == "STAGE" and entry.schema_ == "StageChange/1" and
                          entry.payload["to_stage"] == target for entry in history)
        change = StageChange(graft_id=tx.graft_id, from_stage=source, to_stage=target,
                             attempt=attempt, reason=reason, actor=actor or ACTOR,
                             evidence_refs=refs)
        return tx.append("STAGE", PRODUCER, "StageChange/1",
                         payload=change.model_dump(mode="json"), inputs=[current.entry_hash],
                         idempotency_key=key)

    def transition(self, graft_id, next_stage, *, reason, actor=None, evidence_refs=None):
        with self.ledger.transaction(graft_id) as tx:
            return self._transition(tx, next_stage, reason, actor, evidence_refs)

    def record_consent(self, graft_id, evidence_ref, *, reason="Merchant consent recorded"):
        """Called only by the authenticated backend after a merchant action.

        Consent is a MESSAGE, using StageChange as a transition intent. It never
        changes stage. evidence_ref identifies the backend's merchant action.
        """
        with self.ledger.transaction(graft_id) as tx:
            current = self._last(tx.read())
            if current is None or current.payload["to_stage"] != "PR_OPEN":
                raise IllegalTransition("consent must be recorded during PR_OPEN")
            return tx.append("MESSAGE", {**PRODUCER, "name": "merchant-consent"},
                             "StageChange/1", payload=dict(
                                 graft_id=graft_id, from_stage="PR_OPEN", to_stage="MERGED",
                                 attempt=current.payload["attempt"], reason=reason,
                                 actor={"kind": "service", "name": "merchant-consent"},
                                 evidence_refs=[evidence_ref]),
                             inputs=[current.entry_hash],
                             idempotency_key=f"consent:{current.seq}")

    def register(self, stage, worker, *, timeout=None, max_retries=None):
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage}")
        policy = WorkerSpec(worker, self.timeout if timeout is None else timeout,
                            self.max_retries if max_retries is None else max_retries)
        if policy.timeout <= 0 or policy.max_retries < 0:
            raise ValueError("invalid worker policy")
        self.workers[stage] = policy

    @staticmethod
    def _invoke(spec, context):
        result_queue = queue.Queue(maxsize=1)
        def execute():
            try:
                result = spec.worker(context)
                if inspect.isawaitable(result):
                    async def wait():
                        return await asyncio.wait_for(result, spec.timeout)
                    result = asyncio.run(wait())
                result_queue.put((True, result))
            except BaseException as exc:
                result_queue.put((False, exc))
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        try:
            success, result = result_queue.get(timeout=spec.timeout)
        except queue.Empty:
            raise TimeoutError("stage worker deadline exceeded") from None
        if not success:
            raise result
        if not isinstance(result, StageResult):
            raise TypeError("worker must return StageResult")
        return result

    @staticmethod
    def _run_key(graft_id, source):
        return and_(step_runs.c.graft_id == graft_id,
                    step_runs.c.stage == source.payload["to_stage"],
                    step_runs.c.attempt == source.payload["attempt"])

    def run_once(self, graft_id):
        owner = uuid.uuid4().hex
        with self.ledger.transaction(graft_id) as tx:
            history = tx.read()
            source = self._last(history)
            if source is None:
                raise IllegalTransition("graft must be started first")
            stage, attempt = source.payload["to_stage"], source.payload["attempt"]
            spec = self.workers.get(stage)
            if spec is None or stage in {"DONE", "FAILED", "DELIVERED"}:
                return None
            key = self._run_key(graft_id, source)
            row = tx.conn.execute(select(step_runs).where(key)).mappings().first()
            now = self.clock()
            if row and (row["retry_at"] > now or row["lease_until"] > now):
                return None
            if not row:
                tx.conn.execute(step_runs.insert().values(
                    graft_id=graft_id, stage=stage, attempt=attempt, failures=0,
                    retry_at=0, lease_until=0))
            tx.conn.execute(step_runs.update().where(key).values(
                lease_owner=owner, lease_until=now + spec.timeout + self.lease_grace))
        context = StepContext(graft_id, stage, attempt,
                              f"{graft_id}:{stage}:{attempt}", tuple(history))
        try:
            result = self._invoke(spec, context)
            with self.ledger.transaction(graft_id) as tx:
                if not self._owns(tx, source, key, owner):
                    return None
                if result.next_stage is None:
                    if result.artifacts:
                        raise ValueError("blocked worker must not return artifacts")
                    tx.conn.execute(step_runs.update().where(key).values(
                        lease_owner=None, lease_until=0))
                    return None
                prefix = f"tracker:{source.seq}:{stage}:{attempt}"
                for index, (schema, payload) in enumerate(result.artifacts):
                    tx.append("ARTIFACT", PRODUCER, schema, payload=payload,
                              inputs=[source.entry_hash], idempotency_key=f"{prefix}:a:{index}")
                entry = self._transition(tx, result.next_stage, result.reason,
                                         key=prefix + ":stage")
                tx.conn.execute(step_runs.update().where(key).values(
                    lease_owner=None, lease_until=0))
                return entry
        except Exception as exc:
            with self.ledger.transaction(graft_id) as tx:
                if not self._owns(tx, source, key, owner):
                    return None
                row = tx.conn.execute(select(step_runs).where(key)).mappings().one()
                failures = row["failures"] + 1
                # Store error class only; exception messages can contain secrets.
                if failures > spec.max_retries:
                    entry = self._transition(tx, "FAILED", f"{stage}: {type(exc).__name__}; "
                                             f"retry budget exhausted after {failures} failures")
                else:
                    entry = None
                delay = min(self.backoff_cap, self.backoff_base * 2 ** min(failures - 1, 30))
                delay = min(self.backoff_cap, delay * (0.5 + self.jitter()))
                tx.conn.execute(step_runs.update().where(key).values(
                    failures=failures, retry_at=self.clock() + delay,
                    lease_owner=None, lease_until=0))
                return entry

    def _owns(self, tx, source, key, owner):
        current = self._last(tx.read())
        row = tx.conn.execute(select(step_runs).where(key)).mappings().first()
        return bool(current and current.seq == source.seq and row and row["lease_owner"] == owner)

    def run_until_blocked(self, graft_id, *, max_steps=1000):
        """Run ready stages; return at missing worker, guard/retry wait, or terminal.

        A retry deadline in the future is blocked. The scheduler calls again
        when due; no sleeping control-plane thread is needed.
        """
        for _ in range(max_steps):
            entry = self.run_once(graft_id)
            if entry is None:
                break
        return self.current_stage(graft_id)
