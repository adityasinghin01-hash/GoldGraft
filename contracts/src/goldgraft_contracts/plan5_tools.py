"""Closed service tool argument/capability contract. No tools execute here."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import Field

from .plan5_common import Count, Digest, Id, P5Record, Positive, Ref, Refs, RelativePath, Role


class StatusReadArgs(P5Record):
    run_ref: Ref


class SourceReadArgs(P5Record):
    snapshot_ref: Ref
    path: RelativePath
    max_bytes: Annotated[Positive, Field(le=32768)]


class AnalysisMatchesArgs(P5Record):
    snapshot_ref: Ref
    rule_ref: Ref
    max_matches: Annotated[Positive, Field(le=500)]


class EvidenceReadArgs(P5Record):
    ref: Ref
    max_bytes: Annotated[Positive, Field(le=32768)]


class EvidenceSummaryArgs(P5Record):
    run_ref: Ref
    projection: Literal["private_status", "public_safe"]


class RecipeLookupArgs(P5Record):
    catalog_ref: Ref
    fingerprint: Id


class DocsLookupArgs(P5Record):
    catalog_ref: Ref
    topic: Id
    version: Id


class DependencyInspectArgs(P5Record):
    recipe_ref: Ref
    package: Id
    version: Id


class ExecutionRequestArgs(P5Record):
    proposal_ref: Ref


class ExecutionStatusArgs(P5Record):
    request_id: Id


class CandidatePatchArgs(P5Record):
    workspace_ref: Ref
    expected_tree: Digest
    patch_ref: Ref


class ScenarioStageArgs(P5Record):
    scenario_set_ref: Ref
    mutant_set_ref: Ref


class RecipeStageArgs(P5Record):
    recipe_ref: Ref
    detection_rule_ref: Ref | None


class AggregateReadArgs(P5Record):
    query_ref: Ref
    projection_ref: Ref


class AuditSummaryArgs(P5Record):
    run_ref: Ref
    after_seq: Count


class SafetyRequestHoldArgs(P5Record):
    run_ref: Ref
    reason_code: Id
    evidence_refs: Refs


@dataclass(frozen=True)
class GuardedToolSpec:
    tool_id: str
    arguments: type[P5Record]
    roles: tuple[str, ...]
    effect: Literal["read", "sandbox_request", "candidate_cas", "hold_request", "quarantine"]


T = GuardedToolSpec
V2_TOOLS = (
    T("status.read", StatusReadArgs, ("Gardener", "Healer", "Herald"), "read"),
    T("source.read", SourceReadArgs, ("Surveyor", "Scribe", "Grafter", "Adversary"), "read"),
    T("analysis.matches", AnalysisMatchesArgs, ("Surveyor",), "read"),
    T(
        "evidence.read",
        EvidenceReadArgs,
        ("Surveyor", "Builder", "Explorer", "Scribe", "Architect", "Adversary", "Healer"),
        "read",
    ),
    T("evidence.summary", EvidenceSummaryArgs, ("Herald",), "read"),
    T("recipe.lookup", RecipeLookupArgs, ("Builder", "Architect", "Grafter"), "read"),
    T("docs.lookup", DocsLookupArgs, ("Architect", "Grafter"), "read"),
    T("dependency.inspect", DependencyInspectArgs, ("Builder", "Grafter"), "read"),
    T(
        "execution.request",
        ExecutionRequestArgs,
        ("Builder", "Explorer", "Adversary", "Librarian"),
        "sandbox_request",
    ),
    T(
        "execution.status",
        ExecutionStatusArgs,
        ("Builder", "Explorer", "Adversary", "Librarian"),
        "read",
    ),
    T("candidate.patch", CandidatePatchArgs, ("Grafter",), "candidate_cas"),
    T("scenario.stage", ScenarioStageArgs, ("Adversary",), "quarantine"),
    T("recipe.stage", RecipeStageArgs, ("Librarian",), "quarantine"),
    T("aggregate.read", AggregateReadArgs, ("Orchard Analyst",), "read"),
    T("audit.summary", AuditSummaryArgs, ("Sentinel",), "read"),
    T("safety.request_hold", SafetyRequestHoldArgs, ("Healer", "Sentinel"), "hold_request"),
)
TOOL_CATALOG = MappingProxyType({t.tool_id: t for t in V2_TOOLS})

ROLE_OPERATIONS = MappingProxyType(
    {
        "Gardener": frozenset({"propose_plan"}),
        "Surveyor": frozenset({"survey"}),
        "Builder": frozenset({"build_baseline", "build_candidate", "validate_driver"}),
        "Explorer": frozenset({"run_scenario"}),
        "Scribe": frozenset({"scribe_draft", "scribe_final"}),
        "Architect": frozenset({"architect"}),
        "Grafter": frozenset({"candidate_patch"}),
        "Adversary": frozenset({"derive_guards", "run_mutant"}),
        "Healer": frozenset({"diagnose"}),
        "Librarian": frozenset({"learn", "selfcheck_recipe"}),
        "Herald": frozenset({"explain_status"}),
        "Orchard Analyst": frozenset({"aggregate"}),
        "Sentinel": frozenset({"audit"}),
    }
)
ROLE_OUTPUTS = MappingProxyType(
    {
        "Gardener": frozenset({"PlanProposal/1"}),
        "Surveyor": frozenset({"RootMap/1"}),
        "Builder": frozenset(
            {"ExecutionProposal/1", "RunnableShop/1", "Driver/1", "ArtifactBuild/1"}
        ),
        "Explorer": frozenset({"ExecutionProposal/1", "RawCapture/1"}),
        "Scribe": frozenset({"Contract/1", "TriangleRequest/1"}),
        "Architect": frozenset({"TargetPlan/1"}),
        "Grafter": frozenset({"ChangeList/2"}),
        "Adversary": frozenset({"ScenarioSet/1", "MutantSet/1", "ExecutionProposal/1"}),
        "Healer": frozenset({"HealNote/1"}),
        "Librarian": frozenset({"Recipe/1", "DetectionRule/1", "ExecutionProposal/1"}),
        "Herald": frozenset({"HeraldText/1"}),
        "Orchard Analyst": frozenset({"DashboardSpec/1"}),
        "Sentinel": frozenset({"Alert/1"}),
    }
)


def allowed_tools(role: Role) -> frozenset[str]:
    if role not in ROLE_OPERATIONS:
        raise ValueError("unknown role")
    return frozenset(t.tool_id for t in V2_TOOLS if role in t.roles)


def role_operations(role: Role) -> frozenset[str]:
    return ROLE_OPERATIONS.get(role, frozenset())


def output_schemas(role: Role) -> frozenset[str]:
    return ROLE_OUTPUTS.get(role, frozenset())


def validate_tool_arguments(role: Role, tool_id: str, payload: object) -> P5Record:
    if tool_id not in allowed_tools(role):
        raise ValueError("tool forbidden for role in service catalog")
    return TOOL_CATALOG[tool_id].arguments.model_validate(payload)
