"""Current HealDecision consumer. Pure proposal only; no proof maths, config signing or apply."""

from goldgraft_contracts.runner import HealDecision


def proposed_stage(payload, *, graft_id, current_stage):
    """Consume an already trusted caller's decision using the actual current schema.

    This does not authenticate a sender, grant authority, check a run generation,
    fetch evidence, sign SwitchConfig, emit events or apply a routing change.
    Those integration prerequisites remain with their actual service owners.
    """
    if (
        type(payload) is not dict
        or type(current_stage) is not int
        or current_stage not in (0, 1, 10, 50, 100)
    ):
        raise ValueError("current_graft_stage_and_typed_decision_required")
    decision = HealDecision.model_validate(payload)
    if decision.graft_id != graft_id or decision.from_stage_pct != current_stage:
        raise ValueError("stale_or_misbound_decision")
    return decision.to_stage_pct
