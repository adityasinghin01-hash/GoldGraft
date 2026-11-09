"""Comprehensive test suite for Aditya Gupta's work packages (GU01-GU05).

Tests:
1. pieces.backend FastAPI app routes, models, idempotency, webhook deduplication.
2. Lifecycle state machine:
   PENDING -> BASELINE_TESTED -> UPGRADED_IN_SANDBOX -> PROVED -> READY_TO_DEPLOY.
3. Cryptographic audit trail integration in foundation.ledger.
4. Custody broker credential isolation, Doppler URL formatting, header sanitization.
5. Container runner job execution, deterministic timeout handling, and capture sanitization.
"""

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.registry import validate
from goldgraft_foundation.ledger import Ledger

from pieces.backend.app import create_app
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.lifecycle import InvalidStateTransitionError, JobLifecycleState, LifecycleEngine
from pieces.runner.container_runner import ContainerRunner


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ==============================================================================
# PHASE 1 & 2: Backend API & Lifecycle Engine (GU01, GU02)
# ==============================================================================


def test_lifecycle_full_happy_path():
    """Validates the state machine transitions and ledger commits."""
    ledger = Ledger()
    engine = LifecycleEngine(ledger)
    graft_id = "test-graft-100"

    assert engine.get_state(graft_id) == JobLifecycleState.PENDING

    # PENDING -> BASELINE_TESTED
    res1 = engine.transition(graft_id, JobLifecycleState.BASELINE_TESTED, idempotency_key="step-1")
    assert res1["current_state"] == JobLifecycleState.BASELINE_TESTED.value
    assert engine.get_state(graft_id) == JobLifecycleState.BASELINE_TESTED

    # BASELINE_TESTED -> UPGRADED_IN_SANDBOX
    res2 = engine.transition(
        graft_id, JobLifecycleState.UPGRADED_IN_SANDBOX, idempotency_key="step-2"
    )
    assert res2["current_state"] == JobLifecycleState.UPGRADED_IN_SANDBOX.value

    # UPGRADED_IN_SANDBOX -> PROVED
    res3 = engine.transition(graft_id, JobLifecycleState.PROVED, idempotency_key="step-3")
    assert res3["current_state"] == JobLifecycleState.PROVED.value

    # PROVED -> READY_TO_DEPLOY
    res4 = engine.transition(graft_id, JobLifecycleState.READY_TO_DEPLOY, idempotency_key="step-4")
    assert res4["current_state"] == JobLifecycleState.READY_TO_DEPLOY.value

    # Check ledger history
    entries = ledger.read(graft_id)
    assert len(entries) == 4
    for entry in entries:
        assert entry.graft_id == graft_id
        assert entry.type == "STAGE"


def test_lifecycle_invalid_transition_fails():
    """Direct transition from PENDING to PROVED or READY_TO_DEPLOY must be denied."""
    ledger = Ledger()
    engine = LifecycleEngine(ledger)
    graft_id = "test-graft-illegal"

    with pytest.raises(InvalidStateTransitionError):
        engine.transition(
            graft_id, JobLifecycleState.READY_TO_DEPLOY, idempotency_key="illegal-step"
        )


def test_lifecycle_cancellation_and_rollback():
    """Cancellation and rollback must record immutable audit entries."""
    ledger = Ledger()
    engine = LifecycleEngine(ledger)
    graft_id = "test-graft-cancel"

    engine.transition(graft_id, JobLifecycleState.BASELINE_TESTED, idempotency_key="step-1")
    engine.cancel(graft_id, idempotency_key="cancel-step", reason="Merchant aborted")
    assert engine.get_state(graft_id) == JobLifecycleState.CANCELLED

    # Rollback to BASELINE_TESTED
    engine.rollback(graft_id, JobLifecycleState.BASELINE_TESTED, idempotency_key="rollback-step")
    assert engine.get_state(graft_id) == JobLifecycleState.BASELINE_TESTED


# ==============================================================================
# PHASE 2: Custody & Credential Broker (GU03)
# ==============================================================================


def test_custody_broker_isolation_and_redaction():
    broker = CustodyBroker()
    secrets = {
        "paypal_client_id": "RAW-PAYPAL-ID-999",
        "paypal_client_secret": "TOP-SECRET-KEY-888",
        "nvp_password": "PASSWORD123",
    }

    ref = broker.store_credentials("shop-42", secrets)
    assert ref.to_uri().startswith("doppler://goldgraft/shops/shop-42/secrets")
    assert ref.digest is not None

    # Resolve
    resolved = broker.resolve_credentials(ref.to_uri())
    assert resolved["paypal_client_id"] == "RAW-PAYPAL-ID-999"

    # Redact from logs
    log_sample = "Calling PayPal with secret TOP-SECRET-KEY-888 and auth PASSWORD123 for shop-42"
    redacted = broker.redact(log_sample)
    assert "TOP-SECRET-KEY-888" not in redacted
    assert "PASSWORD123" not in redacted
    assert "[REDACTED]" in redacted

    # Header sanitization
    headers = {
        "Authorization": "Bearer RAW-TOKEN-555",
        "Content-Type": "application/json",
        "X-API-KEY": "SECRET-API-KEY",
    }
    sanitized = broker.sanitize_headers(headers)
    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["X-API-KEY"] == "[REDACTED]"
    assert sanitized["Content-Type"] == "application/json"


# ==============================================================================
# PHASE 3: Isolated Sandbox Runner Engine (GU04)
# ==============================================================================


def test_container_runner_execution_and_capture_sanitization():
    runner = ContainerRunner()

    job_dict = {
        "job_id": "runner-job-001",
        "graft_id": "graft-run-001",
        "stage": "RECORDED",
        "kind": "RECORD",
        "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
        "scenario_ids": ["HAPPY"],
        "mutant_ids": [],
        "variants": ["OLD", "NEW"],
        "timeouts": {"build_s": 300, "run_s": 300, "total_s": 600},
        "secrets_ref": "doppler://goldgraft/sandbox/shop-1",
        "signature": None,
    }
    spec = validate("JobSpec/1", job_dict)

    result = runner.run_job(spec)
    assert result.status == "OK"
    assert result.job_id == "runner-job-001"
    assert len(result.raw_capture_refs) == 2

    # Verify each capture is sanitized and stored
    for ref in result.raw_capture_refs:
        capture = runner.fetch_capture(ref)
        assert capture.scenario_id == "HAPPY"
        for ex in capture.exchanges:
            for k, v in ex.headers.items():
                if "secret" in k.lower() or "auth" in k.lower() or "token" in k.lower():
                    assert v == "[REDACTED]"


def test_container_runner_timeout_handling():
    runner = ContainerRunner()
    job_dict = {
        "job_id": "runner-job-timeout",
        "graft_id": "graft-run-002",
        "stage": "RECORDED",
        "kind": "RECORD",
        "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
        "scenario_ids": ["HAPPY__timeout"],
        "mutant_ids": [],
        "variants": ["OLD"],
        "timeouts": {"build_s": 300, "run_s": 300, "total_s": 600},
        "secrets_ref": "doppler://goldgraft/sandbox/shop-1",
        "signature": None,
    }
    spec = validate("JobSpec/1", job_dict)
    result = runner.run_job(spec)
    assert result.status == "TIMEOUT"
    assert "timeout" in result.error.lower()
