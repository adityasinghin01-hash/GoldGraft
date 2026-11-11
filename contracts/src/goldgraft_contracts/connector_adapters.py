"""Read-only resource/adapter boundary; no provider client or grant implementation."""

from typing import Literal

from pydantic import StrictBool, model_validator

from .plan5_common import (
    Digest,
    Id,
    P5Record,
    Positive,
    Refs,
    Text,
    Utc,
    content_digest,
    unique,
)


class ProviderRef(P5Record):
    provider_id: Id
    adapter_version: Id
    account_id: Id | None


class SourceRevision(P5Record):
    kind: Literal["git_commit", "provider_revision_set", "capture"]
    value: Id

    @model_validator(mode="after")
    def git_identity(self):
        if self.kind == "git_commit":
            from pydantic import TypeAdapter

            from .plan5_common import GitCommit

            TypeAdapter(GitCommit).validate_python(self.value)
        return self


class ResourceNode(P5Record):
    node_id: Id
    provider: ProviderRef
    kind: Literal[
        "source",
        "frontend",
        "backend",
        "datastore",
        "callback",
        "scheduled_job",
        "external_service",
        "artifact",
    ]
    provider_resource_id: Id | None
    environment_id: Id | None
    revision: SourceRevision | None
    required_for_scope: StrictBool
    binding_refs: Refs
    evidence_refs: Refs


class ResourceEdge(P5Record):
    edge_id: Id
    from_node: Id
    to_node: Id
    relation: Literal[
        "builds_from", "routes_to", "stores_state_in", "receives_callback_from", "depends_on"
    ]
    required_for_scope: StrictBool
    evidence_refs: Refs


class ResourceGraph(P5Record):
    graph_id: Id
    case_id: Id
    nodes: list[ResourceNode]
    edges: list[ResourceEdge]
    graph_digest: Digest

    @model_validator(mode="after")
    def topology(self):
        ids = [n.node_id for n in self.nodes]
        unique(ids, "node IDs")
        unique([e.edge_id for e in self.edges], "edge IDs")
        if not ids or any(e.from_node not in ids or e.to_node not in ids for e in self.edges):
            raise ValueError("graph missing node/edge endpoint")
        body = self.model_dump(mode="json", exclude={"graph_digest"})
        if content_digest(body) != self.graph_digest:
            raise ValueError("graph_digest does not match canonical contents")
        return self


class ResourceRecipient(P5Record):
    principal_id: Id
    role: Literal["requester", "controller", "reviewer"]


class ResourceBinding(P5Record):
    binding_id: Id
    case_id: Id
    node_id: Id
    controller_id: Id
    requester_id: Id
    recipients: list[ResourceRecipient]
    granted_actions: list[Literal["view", "connect", "start", "review"]]
    relation_digest: Digest
    authority_basis: Literal["provider_verified", "controller_attested"]
    authority_evidence_refs: Refs
    checked_at: Utc
    epoch: Positive
    approved_at: Utc
    revoked_at: Utc | None

    @model_validator(mode="after")
    def recipients_bound(self):
        keys = [(r.principal_id, r.role) for r in self.recipients]
        unique(keys, "recipients")
        unique(self.granted_actions, "granted actions")
        if (self.requester_id, "requester") not in keys or (
            self.controller_id,
            "controller",
        ) not in keys:
            raise ValueError("requester and controller recipients required")
        return self


class AdapterCapabilities(P5Record):
    provider: ProviderRef
    operations: list[
        Literal[
            "source_read",
            "deployment_read",
            "artifact_identity",
            "route_read",
            "config_evidence",
            "controller_role",
            "revocation_observation",
        ]
    ]
    qualification: Literal[
        "proposed", "implemented", "account_tested", "correspondence_qualified", "e2e_tested"
    ]
    limitations: list[Text]
    qualification_refs: Refs


class AdapterObservation(P5Record):
    observation_id: Id
    case_id: Id
    node_id: Id
    capability: Id
    status: Literal["available", "changed", "revoked", "unsupported", "unknown"]
    basis: Literal["observed", "provider_reported", "controller_attested"]
    evidence_refs: Refs
    checked_at: Utc
    expires_at: Utc | None
