"""Versioned boundary registry. Resolve referenced ledger payloads before validating."""

from typing import Any

from . import agents, delivery, ledger, money, proof, runner, stages, survey
from .common import Format

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
