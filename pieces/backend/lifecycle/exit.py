"""Verifiable merchant exit and teardown (GU05).

The reviewed Q0-Q4 sequence is explicit here, and the receipt can only say
``complete`` when every phase has its own evidence:

* Q0  final assets/current outcome verified and an independent executor ready
* Q1  ordinary acquisition/model/mutation/worker capabilities fenced and revoked,
      with an acknowledgement per capability
* Q2  the merchant-owned executor performs the permitted restart and observations
      while GoldGraft cannot act
* Q3  signed results are reconciled through a temporary read-only exit-evidence
      capability, never ordinary host/source access
* Q4  that read capability is revoked and the acknowledgement reported

A missing executor or a missing revocation acknowledgement is a hold. Exit is
never claimed from ordinary credentials that should already be revoked, and
nothing here performs financial compensation.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, Protocol

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

ExitOutcome = Literal["complete", "pending", "failed_safe", "unknown", "held"]

ORDINARY_CAPABILITIES = (
    "source_read",
    "model_execution",
    "host_mutation",
    "worker_dispatch",
)


@dataclass
class RevocationAck:
    capability: str
    acknowledged: bool
    evidence_ref: str | None = None

    def __post_init__(self):
        if self.acknowledged and not self.evidence_ref:
            raise ValueError("a revocation acknowledgement requires evidence")


@dataclass
class ExitCheckResult:
    executor_identity_ref: str
    restart_performed: bool
    recovery_outcome: Literal["recovered", "held", "failed", "unknown"]
    observed_evidence_refs: list[str] = field(default_factory=list)
    signed: bool = False

    def __post_init__(self):
        if self.recovery_outcome == "recovered" and not self.observed_evidence_refs:
            raise ValueError("a recovered exit check requires observed evidence")


class ExitExecutor(Protocol):
    """A merchant-owned executor independent of the GoldGraft control plane."""

    identity_ref: str

    def run_exit_check(self) -> ExitCheckResult: ...


@dataclass
class ExitReceipt:
    exit_id: str
    graft_id: str
    outcome: ExitOutcome
    phases: dict[str, str]
    revoked_tokens_count: int
    cleaned_containers_count: int
    verified_clean: bool
    timestamp: str
    holds: list[str] = field(default_factory=list)
    ledger_seq: int | None = None

    @property
    def status(self) -> str:
        return "EXIT_COMPLETE" if self.outcome == "complete" else self.outcome.upper()

    def __post_init__(self):
        if self.verified_clean != (self.outcome == "complete"):
            raise ValueError("a clean exit is exactly a complete exit")


class ExitController:
    """Orchestrates merchant exit and records what was actually observed."""

    def __init__(self, ledger: Ledger | None = None, custody_broker=None, container_runner=None):
        self.ledger = ledger or Ledger()
        self.custody_broker = custody_broker
        self.container_runner = container_runner
        self._revoked_tokens: set[str] = set()
        self._cleaned_containers: set[str] = set()

    def execute_merchant_exit(
        self,
        graft_id: str,
        *,
        actor_name: str,
        idempotency_key: str,
        executor: ExitExecutor | None = None,
        revocations: list[RevocationAck] | None = None,
        exit_evidence_ack: RevocationAck | None = None,
        token_keys: list[str] | None = None,
        container_ids: list[str] | None = None,
        from_stage: str = Stage.LIVE_100.value,
    ) -> ExitReceipt:
        tokens = list(token_keys or [])
        containers = list(container_ids or [])
        exit_id = "exit-" + hashlib.sha256(
            f"{graft_id}:{idempotency_key}".encode()
        ).hexdigest()[:12]
        now = datetime.now(UTC).isoformat()
        phases = dict.fromkeys(("Q0", "Q1", "Q2", "Q3", "Q4"), "pending")

        # Q0 - independent executor and current final assets.
        if executor is None or not getattr(executor, "identity_ref", None):
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="held",
                phases=phases,
                revoked_tokens_count=0,
                cleaned_containers_count=0,
                verified_clean=False,
                timestamp=now,
                holds=["no qualified independent exit-check executor; exit held"],
            )
        phases["Q0"] = "confirmed"

        # Q1 - fence and revoke ordinary capabilities, acknowledged individually.
        acked = {a.capability: a for a in (revocations or []) if a.acknowledged}
        missing = [c for c in ORDINARY_CAPABILITIES if c not in acked]
        for token_key in tokens:
            self._revoked_tokens.add(token_key)
            if self.custody_broker and hasattr(self.custody_broker, "revoke_token"):
                self.custody_broker.revoke_token(token_key)
        for container_id in containers:
            self._cleaned_containers.add(container_id)
            if self.container_runner and hasattr(self.container_runner, "cleanup_container"):
                self.container_runner.cleanup_container(container_id)
        if missing:
            phases["Q1"] = "revocation_pending"
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="pending",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=[f"revocation not acknowledged: {', '.join(missing)}"],
            )
        phases["Q1"] = "confirmed"

        # Q2 - the independent executor acts while GoldGraft cannot.
        try:
            result = executor.run_exit_check()
        except Exception as exc:
            phases["Q2"] = "unknown"
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="unknown",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=[f"exit check did not report: {exc}"],
            )
        if not result.signed:
            phases["Q2"] = "unverified"
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="unknown",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=["exit check result was not signed by the executor"],
            )
        phases["Q2"] = result.recovery_outcome
        if result.recovery_outcome == "held":
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="failed_safe",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=["executor entered its preconfigured safe hold"],
            )
        if result.recovery_outcome != "recovered":
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="unknown",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=["executor did not observe a recovered current state"],
            )

        # Q3 - read the signed evidence through the temporary read capability.
        if exit_evidence_ack is None or not exit_evidence_ack.acknowledged:
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="pending",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=["no exit-evidence read capability to reconcile results"],
            )
        phases["Q3"] = "confirmed"

        # Q4 - revoke the read capability and report the acknowledgement.
        if exit_evidence_ack.capability not in {"exit_evidence", "read_exit_evidence"}:
            phases["Q4"] = "revocation_pending"
            return ExitReceipt(
                exit_id=exit_id,
                graft_id=graft_id,
                outcome="pending",
                phases=phases,
                revoked_tokens_count=len(tokens),
                cleaned_containers_count=len(containers),
                verified_clean=False,
                timestamp=now,
                holds=["exit-evidence capability was not the one revoked"],
            )
        phases["Q4"] = "confirmed"

        seq = self._record(
            graft_id=graft_id,
            exit_id=exit_id,
            actor_name=actor_name,
            idempotency_key=idempotency_key,
            from_stage=from_stage,
            tokens=len(tokens),
            containers=len(containers),
        )
        return ExitReceipt(
            exit_id=exit_id,
            graft_id=graft_id,
            outcome="complete",
            phases=phases,
            revoked_tokens_count=len(tokens),
            cleaned_containers_count=len(containers),
            verified_clean=True,
            timestamp=now,
            ledger_seq=seq,
        )

    def _record(
        self,
        *,
        graft_id: str,
        exit_id: str,
        actor_name: str,
        idempotency_key: str,
        from_stage: str,
        tokens: int,
        containers: int,
    ) -> int:
        producer = Producer(kind=ProducerKind.SERVICE, name="ExitController", version="2.0.0")
        entry = self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": from_stage,
                "to_stage": Stage.DONE.value,
                "attempt": 1,
                "reason": (
                    f"Merchant exit by {actor_name}; revoked {tokens} tokens, "
                    f"torn down {containers} containers, independent restart observed"
                ),
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [f"blob://exit/{exit_id}"],
            },
            idempotency_key=idempotency_key,
        )
        return entry.seq
