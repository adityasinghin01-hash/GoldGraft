"""Executable VJ03/VJ04/VJ05 domain checks, using current shared contracts.

These perform read-only domain checks, not backend fencing/deploy/exit actions.
No receipt/ref/schema alone verifies external facts or grants authority.
"""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path


def _inventory(path):
    spec = importlib.util.spec_from_file_location(
        "candidate_inventory", Path(__file__).parent / "candidate/continuity.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inspect(Path(path))


def _result(name, findings, **observed):
    return {
        "recipe": name,
        "domain_status": "HOLD" if findings else "READY_FOR_BACKEND_QUALIFICATION",
        "findings": sorted(set(findings)),
        "observed": observed,
        "evidence_class": "LOCAL_READ_ONLY_DOMAIN_CHECK",
        "qualified": False,
        "external_service_calls": 0,
        "mutations": 0,
    }


def state_recipe(record, *, candidate_database):
    from goldgraft_contracts.registry import validate

    state = validate("StateCutover/1", record)
    findings = []
    inventory = _inventory(candidate_database)
    if state.state_digest != inventory["snapshot_sha256"]:
        findings.append("state_subject_mismatch")
    if state.schema_digest != inventory["schema_sha256"]:
        findings.append("state_schema_mismatch")
    if state.outcome != "verified":
        findings.append("backend_state_cutover_not_verified")
    if (
        state.pending_external_effect_refs
        or inventory["held_records"]
        or inventory["unresolved_dispatches"]
    ):
        findings.append("unresolved_economic_effects")
    # Ref presence is useful structural preparation only; actual provenance,
    # all-writer fencing and high-water/replay verification remain backend work.
    return _result(
        "state_recipe",
        findings,
        candidate=inventory,
        required_private_state=[
            "candidate.sqlite",
            "merchant_callback_effects",
            "encrypted_callback_inbox",
        ],
        legacy_import_supported=False,
        external_state_facts_verified=False,
    )


def finalisation_recipe(record):
    from goldgraft_contracts.registry import validate

    assets = validate("AssetManifest/1", record)
    findings = []
    required = {
        "runtime",
        "config",
        "state",
        "credential",
        "callback",
        "origin_handler",
        "exit_executor",
    }
    operational = {
        a.kind for a in assets.assets if a.required_for_operation and a.desired == "keep"
    }
    for missing in required - operational:
        findings.append("missing_preserved_" + missing)
    for asset in assets.assets:
        if asset.required_for_operation and asset.ownership != "merchant":
            findings.append("temporary_or_shared_dependency_" + asset.kind)
        if asset.required_for_operation and not asset.evidence_refs:
            findings.append("unobserved_operational_asset_" + asset.kind)
    return _result(
        "finalisation_recipe",
        findings,
        asset_count=len(assets.assets),
        runtime_independence_verified=False,
        historical_origins_must_remain=True,
    )


def exit_check_recipe(record, *, before_database, after_database, now=None):
    from goldgraft_contracts.registry import validate

    plan = validate("ExitCheckPlan/1", record)
    before, after = _inventory(before_database), _inventory(after_database)
    findings = []
    now = now or datetime.now(UTC)
    if plan.deadline <= now:
        findings.append("exit_plan_expired")
    if not plan.criteria_refs or not plan.authority_refs:
        findings.append("exit_criteria_or_authority_missing")
    if before["snapshot_sha256"] != after["snapshot_sha256"]:
        findings.append("economic_state_changed_across_restart")
    if plan.state_digest != before["snapshot_sha256"]:
        findings.append("exit_plan_state_subject_mismatch")
    if after["held_records"] or after["unresolved_dispatches"]:
        findings.append("unresolved_economic_effects")
    return _result(
        "exit_check_recipe",
        findings,
        state_preserved=before["snapshot_sha256"] == after["snapshot_sha256"],
        independent_executor_verified=False,
        revoked_service_credentials_used=False,
        restart_executed_by_this_recipe=False,
    )
