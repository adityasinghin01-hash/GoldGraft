"""Snapshot-driven recovery; events do not grant authority or dispatch tasks."""

from datetime import timedelta

import pytest

from .test_runtime import NOW, profile


def test_duplicate_outbox_delivery_does_not_repeat_work(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    assert tick("fake:runtime-run", NOW, ports).completed == 2
    events = ports.control.outbox("fake:runtime-run")
    for event in reversed(events + events):
        ports.control.ack_event(event.event_id)
    assert tick("fake:runtime-run", NOW, ports).claimed == 0
    assert ports.model.total_dispatches() == 4
    assert ports.tools.total_dispatches() == 2


def test_expired_lease_cannot_commit_stale_success(tmp_path):
    from goldgraft_fakes.plan5_profile import create_profile

    from pieces.agents.runtime import run_task

    clock = [NOW]
    ports = create_profile(tmp_path / "runtime.sqlite", clock=lambda: clock[0])
    old = ports.control.claim("old", clock[0])
    clock[0] += timedelta(seconds=61)
    current = ports.control.claim("new", clock[0])
    with pytest.raises(ValueError, match="STALE"):
        run_task(old, ports.control, ports.artifacts, ports.model, ports.tools, now=clock[0])
    assert current.lease_epoch == old.lease_epoch + 1
    assert ports.model.total_dispatches() == 0
    assert ports.control.accepted_result_count() == 0


def test_due_timer_rechecked_and_runs_without_agent_dispatch(tmp_path):
    from goldgraft_contracts.registry import validate
    from goldgraft_fakes._fixtures import example
    from goldgraft_fakes.plan5_profile import create_profile

    from pieces.agents.scheduler import tick

    clock = [NOW]
    ports = create_profile(tmp_path / "runtime.sqlite", clock=lambda: clock[0])
    lease = ports.control.claim("old", clock[0])
    wake = example("WakeCondition/1")
    wake.update(
        kind="timer",
        subject_ref="fake:timer",
        due_at=(NOW + timedelta(seconds=10)).isoformat(),
        expected_digest=None,
        minimum_version=0,
    )
    ports.control.wait(
        lease, validate("Issue/1", example("Issue/1")), validate("WakeCondition/1", wake)
    )
    assert not ports.control.wake("fake:runtime-run", "fake:timer", digest="a" * 64, version=0)
    clock[0] += timedelta(seconds=11)
    fresh = create_profile(tmp_path / "runtime.sqlite", clock=lambda: clock[0])
    assert tick("fake:runtime-run", clock[0], fresh).completed == 2


def test_heartbeat_renews_during_blocking_model_call(tmp_path):
    import threading
    from dataclasses import replace

    from goldgraft_fakes.plan5_profile import create_profile

    from pieces.agents.scheduler import tick

    clock = [NOW]
    ports = create_profile(tmp_path / "runtime.sqlite", clock=lambda: clock[0])
    renewed = threading.Event()
    renew = ports.control.renew

    def track(lease, now):
        value = renew(lease, now)
        renewed.set()
        return value

    ports.control.renew = track
    ports.artifacts.heartbeat_seconds = 0.01
    original = ports.model.turn

    def blocking(request):
        if not renewed.is_set():
            clock[0] += timedelta(seconds=16)
            assert renewed.wait(1), "heartbeat did not renew a blocked call"
        return original(request)

    model = type(
        "BlockingModel", (), {"turn": staticmethod(blocking), "reconcile": ports.model.reconcile}
    )()
    assert tick("fake:runtime-run", clock[0], replace(ports, model=model)).completed == 2
    assert renewed.is_set()
