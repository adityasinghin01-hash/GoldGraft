"""Deterministic serial task policy over GU-owned TaskControl; no model scheduling."""

from dataclasses import dataclass

from .graph import advance_surveyor_herald
from .runtime import run_task


@dataclass(frozen=True)
class SchedulerReport:
    claimed: int
    completed: int
    waiting: int
    rejected: int
    run_version: int


def tick(run_ref, now, ports):
    claimed = completed = rejected = 0
    ports.control.recover_due(run_ref, ports.clock())
    for _ in range(32):
        snapshot = ports.control.snapshot(run_ref)
        if snapshot.cancellation_ref is not None:
            break
        if getattr(ports, "program", None) == "surveyor_herald":
            advance_surveyor_herald(run_ref, ports)
        elif getattr(ports, "program", None) == "component_workflow":
            from .workflow import advance

            advance(run_ref, ports)
        lease = ports.control.claim("runtime-worker", ports.clock())
        if lease is None:
            break
        claimed += 1
        try:
            result = run_task(
                lease, ports.control, ports.artifacts, ports.model, ports.tools, now=ports.clock()
            )
        except ValueError as exc:
            # A revoked/expired lease cannot even commit a held result; authority owns that state.
            if str(exc).split()[0] not in {"CANCELLED", "STALE", "DENIED"}:
                raise
            rejected += 1
            continue
        if result.outcome == "completed":
            completed += 1
        else:
            rejected += 1
    snapshot = ports.control.snapshot(run_ref)
    return SchedulerReport(
        claimed,
        completed,
        sum(t.state == "waiting" for t in snapshot.tasks),
        rejected,
        snapshot.state_version,
    )
