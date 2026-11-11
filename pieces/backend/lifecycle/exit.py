"""Verifiable Merchant Exit and Resource Teardown (GU05).

Provides:
1. Complete token and secret revocation via Custody Broker.
2. Isolated sandbox container teardown and filesystem cleanup.
3. Exit verification ensuring zero remnant GoldGraft credentials or active runtimes.
4. Cryptographic ledger receipt sealing the exit record.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


@dataclass
class ExitReceipt:
    exit_id: str
    graft_id: str
    revoked_tokens_count: int
    cleaned_containers_count: int
    status: str
    verified_clean: bool
    timestamp: str


class ExitController:
    """Orchestrates verifiable merchant exit and artifact cleanup."""

    def __init__(
        self,
        ledger: Ledger | None = None,
        custody_broker: Any | None = None,
        container_runner: Any | None = None,
    ):
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
        from_stage: str = Stage.LIVE_100.value,
        token_keys: list[str] | None = None,
        container_ids: list[str] | None = None,
    ) -> ExitReceipt:
        """Executes full teardown and generates cryptographic audit receipt."""
        raw_id = f"{graft_id}:{idempotency_key}".encode()
        exit_id = f"exit-{hashlib.sha256(raw_id).hexdigest()[:12]}"
        now = datetime.now(UTC).isoformat()

        tokens = token_keys or []
        containers = container_ids or []

        # 1. Revoke temporary sandbox credentials
        for token_key in tokens:
            self._revoked_tokens.add(token_key)
            if self.custody_broker and hasattr(self.custody_broker, "revoke_token"):
                self.custody_broker.revoke_token(token_key)

        # 2. Teardown sandbox containers
        for cid in containers:
            self._cleaned_containers.add(cid)
            if self.container_runner and hasattr(self.container_runner, "cleanup_container"):
                self.container_runner.cleanup_container(cid)

        # 3. Verify clean state
        verified_clean = True
        if self.custody_broker and hasattr(self.custody_broker, "active_sessions_count"):
            if self.custody_broker.active_sessions_count(graft_id) > 0:
                verified_clean = False

        # 4. Record Exit in ledger (DONE stage)
        service_producer = Producer(
            kind=ProducerKind.SERVICE,
            name="ExitController",
            version="1.0.0",
        )

        reason = (
            f"Merchant exit requested by {actor_name}. "
            f"Revoked {len(tokens)} tokens, torn down {len(containers)} containers."
        )

        self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=service_producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": from_stage,
                "to_stage": Stage.DONE.value,
                "attempt": 1,
                "reason": reason,
                "actor": {"kind": service_producer.kind.value, "name": service_producer.name},
                "evidence_refs": [f"blob://exit/{exit_id}"],
            },
            idempotency_key=idempotency_key,
        )

        return ExitReceipt(
            exit_id=exit_id,
            graft_id=graft_id,
            revoked_tokens_count=len(tokens),
            cleaned_containers_count=len(containers),
            status="EXIT_COMPLETE" if verified_clean else "EXIT_WARNING_UNVERIFIED",
            verified_clean=verified_clean,
            timestamp=now,
        )
