"""Versioned boundary registry. Resolve referenced ledger payloads before validating."""

from typing import Any

from . import (
    agent_runtime,
    agents,
    connection_control,
    connector_adapters,
    delivery,
    ledger,
    lifecycle,
    money,
    plan5_tools,
    proof,
    runner,
    stages,
    survey,
    work_package,
)
from .common import Format
from .plan5_common import Issue, P5Record

_BOUNDARIES: dict[str, type[Format]] = {
    "LedgerEntry": ledger.LedgerEntry,
    "StageChange": stages.StageChange,
    "RootMap": survey.RootMap,
    "CMEL": money.MoneyEvent,
    "Money": money.Money,
    "Rule": proof.Rule,
    "Contract": proof.MoneyContract,
    "Scenario": proof.Scenario,
    "Mutant": proof.Mutant,
    "Verdict": proof.Verdict,
    "ProofStrength": proof.ProofStrength,
    "Certificate": proof.Certificate,
    "Recipe": delivery.Recipe,
    "SwitchConfig": delivery.SwitchConfig,
    "BudgetRecord": delivery.BudgetRecord,
    "HandoffRecord": delivery.HandoffRecord,
    "HandoffPack": delivery.HandoffPack,
    "Connection": survey.Connection,
    "ProbeResult": survey.ProbeResult,
    "RunnableShop": survey.RunnableShop,
    "Driver": survey.Driver,
    "TargetPlan": survey.TargetPlan,
    "LinksPack": survey.LinksPack,
    "Assignment": agents.Assignment,
    "LaneChange": agents.LaneChange,
    "ChangeList": agents.ChangeList,
    "ScenarioSet": agents.ScenarioSet,
    "MutantSet": agents.MutantSet,
    "TriangleRequest": agents.TriangleRequest,
    "HealNote": agents.HealNote,
    "DetectionRule": agents.DetectionRule,
    "HeraldText": agents.HeraldText,
    "DashboardSpec": agents.DashboardSpec,
    "Alert": agents.Alert,
    "JobSpec": runner.JobSpec,
    "JobResult": runner.JobResult,
    "RawCapture": runner.RawCapture,
    "ShopPack": runner.ShopPack,
    "GuardEvent": runner.GuardEvent,
    "HealDecision": runner.HealDecision,
    "MappingRow": money.MappingRow,
    "MutationOperator": proof.MutationOperator,
}
REGISTRY: dict[str, type[Format]] = {
    f"{name}/1": model for name, model in sorted(_BOUNDARIES.items())
}

# Explicit additive version inventory; v1 is not rebound to new meanings.

PLAN5_REGISTRY: dict[str, type[Format]] = {"Issue/1": Issue, "ChangeList/2": agents.ChangeListV2}
for _module in (
    connector_adapters,
    work_package,
    connection_control,
    lifecycle,
    agent_runtime,
    plan5_tools,
):
    for _candidate in vars(_module).values():
        if (
            isinstance(_candidate, type)
            and issubclass(_candidate, P5Record)
            and _candidate is not P5Record
            and _candidate.__module__ == _module.__name__
        ):
            _key = f"{_candidate.__name__}/1"
            if _key in REGISTRY or _key in PLAN5_REGISTRY:
                raise RuntimeError(f"duplicate schema: {_key}")
            PLAN5_REGISTRY[_key] = _candidate
REGISTRY.update(PLAN5_REGISTRY)
for _name, _model in REGISTRY.items():
    _model.schema_name = _name


def validate(schema_name: str, payload: Any, *, context: dict | None = None) -> Format:
    """Validate a decoded JSON payload; errors identify the schema and bad field.

    HeraldText numbers require context={"ledger_entries": {entry_hash: decoded_entry}}.
    Referenced LedgerEntry bodies must be fetched by the ledger and validated here.
    """
    try:
        model = REGISTRY[schema_name]
    except KeyError:
        raise ValueError(f"Unknown schema: {schema_name!r}; known: {', '.join(REGISTRY)}") from None
    return model.model_validate(payload, context=context)
