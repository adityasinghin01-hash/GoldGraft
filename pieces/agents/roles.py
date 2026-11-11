"""Own role policy; shared catalogs remain capability ceilings, not implementations."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from goldgraft_contracts.plan5_common import content_digest

from .component_agents import ROLE_DEFINITIONS


@dataclass(frozen=True)
class RolePolicy:
    role: str
    operation: str
    schemas: tuple[str, ...]
    tools: tuple[str, ...]
    prompt_ref: str
    policy_ref: str
    additional_operations: tuple[str, ...] = ()


SURVEYOR = RolePolicy(
    "Surveyor",
    "survey",
    ("RootMap/1",),
    ("source.read", "analysis.matches", "evidence.read"),
    "agent:surveyor-prompt:1",
    "agent:surveyor-policy:1",
)
HERALD = RolePolicy(
    "Herald",
    "explain_status",
    ("HeraldText/1",),
    ("status.read", "evidence.summary"),
    "agent:herald-prompt:1",
    "agent:herald-policy:1",
)
COMPONENT_POLICIES = {
    name: RolePolicy(
        name,
        op,
        schemas,
        tools,
        "agent:" + name.lower().replace(" ", "_") + "-prompt:1",
        "agent:" + name.lower().replace(" ", "_") + "-policy:1",
        others,
    )
    for name, (op, others, schemas, tools) in ROLE_DEFINITIONS.items()
}
ROLE_POLICIES = MappingProxyType({"Surveyor": SURVEYOR, "Herald": HERALD, **COMPONENT_POLICIES})
SURVEY_POLICY = {
    "version": 1,
    "role": "Surveyor",
    "operation": "survey",
    "output_schemas": list(SURVEYOR.schemas),
    "tools": list(SURVEYOR.tools),
    "profile": "offline_source_inventory",
    "max_files": 16,
    "max_source_bytes": 16384,
    "lenses": ["code"],
    "model_budget_micro_usd": 0,
    "required_evidence_cannot_be_trimmed": True,
}


def surveyor_configuration():
    prompt = (Path(__file__).parent / "prompts/surveyor.md").read_text()
    return {
        "role": SURVEYOR.role,
        "operation": SURVEYOR.operation,
        "prompt_ref": SURVEYOR.prompt_ref,
        "prompt": prompt,
        "prompt_digest": content_digest(prompt),
        "policy_ref": SURVEYOR.policy_ref,
        "policy": SURVEY_POLICY,
        "policy_digest": content_digest(SURVEY_POLICY),
    }


def herald_configuration(*, projection="private_status"):
    if projection not in {"private_status", "public_safe"}:
        raise ValueError("DENIED projection")
    prompt = (Path(__file__).parent / "prompts/herald.md").read_text()
    policy = {
        "version": 1,
        "role": "Herald",
        "operation": "explain_status",
        "output_schemas": list(HERALD.schemas),
        "tools": list(HERALD.tools),
        "claim_catalog": "closed:herald:1",
        "model_budget_micro_usd": 0,
    }
    return {
        "role": "Herald",
        "operation": "explain_status",
        "prompt_ref": HERALD.prompt_ref,
        "prompt": prompt,
        "prompt_digest": content_digest(prompt),
        "policy_ref": HERALD.policy_ref,
        "policy": policy,
        "policy_digest": content_digest(policy),
        "projection": projection,
    }


def validate_role_task(task):
    # Explicitly retained B3 synthetic compatibility. This is never a B4 acceptance.
    if (task.policy_ref, task.prompt_ref, task.policy_digest, task.prompt_digest) == (
        "fake:offline-policy",
        "fake:no-agent-prompt",
        content_digest("offline-policy"),
        content_digest("scripted-counterpart-only"),
    ):
        return None
    role = ROLE_POLICIES.get(task.task.role)
    if role is None:
        raise ValueError("DENIED unimplemented role")
    config = (
        surveyor_configuration()
        if role.role == "Surveyor"
        else herald_configuration()
        if role.role == "Herald"
        else component_configuration(role.role)
    )
    if (
        task.task.operation not in (role.operation,) + role.additional_operations
        or not set(task.task.expected_schemas) <= set(role.schemas)
        or not set(task.task.allowed_tool_ids) <= set(role.tools)
        or task.task.output_subject_policy
        != ("candidate_child" if role.role == "Grafter" else "same_subject")
        or (
            task.task.workspace_ref is None
            if role.role == "Grafter"
            else task.task.workspace_ref is not None
        )
        or (task.prompt_ref, task.prompt_digest, task.policy_ref, task.policy_digest)
        != (
            config["prompt_ref"],
            config["prompt_digest"],
            config["policy_ref"],
            config["policy_digest"],
        )
    ):
        raise ValueError("DENIED role/prompt/policy binding")
    return role


def component_configuration(name):
    role = COMPONENT_POLICIES.get(name)
    if role is None:
        raise ValueError("DENIED component role")
    slug = name.lower().replace(" ", "_")
    prompt = (Path(__file__).parent / "prompts" / (slug + ".md")).read_text()
    policy = {
        "role": name,
        "version": 1,
        "operations": [role.operation, *role.additional_operations],
        "tools": list(role.tools),
        "schemas": list(role.schemas),
        "model_budget_micro_usd": 0,
        "profile": "component_offline",
        "max_turns": 12,
        "max_tools": 24,
    }
    return {
        "role": name,
        "prompt": prompt,
        "prompt_ref": role.prompt_ref,
        "prompt_digest": content_digest(prompt),
        "policy_ref": role.policy_ref,
        "policy": policy,
        "policy_digest": content_digest(policy),
    }
