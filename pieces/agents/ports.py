"""Runtime-owned composition/admission ports over the shared GU contracts."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from goldgraft_contracts.agent_runtime import (
    ArtifactPort,
    ModelBudget,
    ModelPort,
    TaskCheckpoint,
    TaskContext,
    TaskControl,
    TaskLease,
    ToolPort,
)
from goldgraft_contracts.connection_control import WorkAcceptance, WorkerOperation


@dataclass(frozen=True)
class Admission:
    task_id: str
    context: TaskContext
    acceptance: WorkAcceptance
    operation: WorkerOperation | None
    policy_digest: str
    prompt_digest: str
    budget: ModelBudget | None
    authority_current: bool
    evidence_class: str


@dataclass(frozen=True)
class ModelPolicy:
    """Own trusted-port policy after current gateway grant verification, not model JSON."""

    model_profile_ref: str
    budget_reservation_ref: str
    input_token_cap: int
    output_token_cap: int
    max_turns: int

    def __post_init__(self):
        if (
            type(self.input_token_cap) is not int
            or not 1 <= self.input_token_cap <= 24000
            or type(self.output_token_cap) is not int
            or not 1 <= self.output_token_cap <= 4000
            or type(self.max_turns) is not int
            or not 1 <= self.max_turns <= 12
            or not self.model_profile_ref
            or not self.budget_reservation_ref
        ):
            raise ValueError("INVALID model admission policy")


class RuntimeArtifacts(ArtifactPort, Protocol):
    """Trusted adapter supplies bytes/admission; models cannot construct these records."""

    def ticket(self, lease: TaskLease) -> Admission: ...
    def raw(self, ref: str, lease: TaskLease) -> bytes: ...
    def save_state(self, lease: TaskLease, state: dict) -> str: ...
    def checkpoint_value(self, ref: str, lease: TaskLease) -> TaskCheckpoint: ...
    def result_authenticity(self, lease: TaskLease) -> str: ...
    def model_context(
        self, lease: TaskLease, context: TaskContext, observation_refs: list[str]
    ) -> tuple[str, str]: ...
    def authorize_tool(self, lease: TaskLease, tool_id: str, arguments: object) -> None: ...


class RoleArtifacts(RuntimeArtifacts, Protocol):
    """B4 trusted adapter extensions; not new shared wire records or GU mechanisms."""

    def read_artifact(self, ref: str, lease: TaskLease) -> bytes: ...
    def role_inputs(self, lease: TaskLease) -> dict: ...


class RuntimeControl(TaskControl, Protocol):
    def recover_due(self, run_ref: str, now: datetime) -> int: ...


@dataclass(frozen=True)
class RuntimePorts:
    control: RuntimeControl
    artifacts: RuntimeArtifacts
    model: ModelPort
    tools: ToolPort
    clock: Callable[[], datetime]
