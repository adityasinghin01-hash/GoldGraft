"""Typed source/package/upload declarations; no filesystem, custody or uploader service."""

from typing import Annotated, Literal

from pydantic import Field, StrictBool, model_validator

from .connector_adapters import ProviderRef, SourceRevision
from .plan5_common import (
    SECRET_NAME,
    Count,
    Digest,
    Epochs,
    Id,
    Ids,
    Issue,
    P5Record,
    Positive,
    Ref,
    Refs,
    RelativePath,
    Text,
    Utc,
    reject_secret,
    unique,
)


class SourceSnapshot(P5Record):
    snapshot_id: Id
    case_id: Id
    source_kind: Literal["git", "local_folder", "cloud_files", "host_export"]
    provider: ProviderRef
    source_resource_id: Id | None
    revision: SourceRevision
    manifest_digest: Digest
    file_count: Annotated[Count, Field(le=20000)]
    total_bytes: Annotated[Count, Field(le=209715200)]
    captured_at: Utc
    omission_manifest_ref: Ref
    authority_binding_refs: Refs
    provenance_class: Literal["provider_reported", "controller_attested", "verified_build_link"]
    completeness: Literal["complete_for_declared_scope", "incomplete", "unknown"]

    @model_validator(mode="after")
    def source_revision(self):
        if (self.source_kind == "git") != (self.revision.kind == "git_commit"):
            raise ValueError("Git source/revision mismatch")
        if not self.authority_binding_refs:
            raise ValueError("source authority binding required")
        return self


class ManifestEntry(P5Record):
    relative_path: RelativePath
    file_type: Literal["file", "directory"]
    bytes: Annotated[Count, Field(le=20971520)]
    sha256: Digest | None

    @model_validator(mode="after")
    def file_digest(self):
        if self.file_type == "file" and self.sha256 is None:
            raise ValueError("file digest required")
        if self.file_type == "directory" and (self.bytes != 0 or self.sha256 is not None):
            raise ValueError("directory has no file bytes/digest")
        return self


class UploadSession(P5Record):
    intake_collection_limit = 100000
    upload_id: Id
    case_id: Id
    contributor_id: Id
    binding_epochs: Epochs
    expected_manifest_ref: Ref
    expected_manifest_digest: Digest
    expected_total_bytes: Annotated[Count, Field(le=209715200)]
    received_chunk_refs: Annotated[list[Ref], Field(max_length=100000)]
    state: Literal["pending", "receiving", "finalised", "cancelled", "expired"]
    created_at: Utc
    expires_at: Utc
    finalised_snapshot_ref: Ref | None

    @model_validator(mode="after")
    def finalisation(self):
        if (self.state == "finalised") != (self.finalised_snapshot_ref is not None):
            raise ValueError("final snapshot required exactly for finalised upload")
        if not self.binding_epochs:
            raise ValueError("upload authority epochs required")
        return self


class Chunk(P5Record):
    upload_id: Id
    file_path: RelativePath
    offset: Count
    length: Annotated[Positive, Field(le=4194304)]
    sha256: Digest
    blob_ref: Ref


class ChunkReceipt(P5Record):
    upload_id: Id
    file_path: RelativePath
    offset: Count
    length: Annotated[Positive, Field(le=4194304)]
    sha256: Digest
    received_at: Utc


class Component(P5Record):
    node_id: Id
    purpose: Id
    source_snapshot_ref: Ref | None
    build_context_ref: Ref | None
    runtime_profile_ref: Ref
    dependency_manifest_ref: Ref
    configuration_manifest_ref: Ref
    correspondence_evidence_refs: Refs
    controller_binding_refs: Refs


class ComponentManifest(P5Record):
    components: list[Component]


class Dependency(P5Record):
    dependency_id: Id
    component_ids: Ids
    purpose: Id
    access_mode: Literal["fixture", "sandbox_broker", "read_evidence", "unavailable"]
    authority_ref: Ref | None
    test_identity_ref: Ref | None
    limitation: Text


class DependencyManifest(P5Record):
    dependencies: list[Dependency]


class ConfigurationEntry(P5Record):
    name: Id
    kind: Literal["public_value", "secret_reference"]
    value: Text | None
    secret_ref: Ref | None
    required: StrictBool
    evidence_refs: Refs

    @model_validator(mode="after")
    def custody(self):
        if self.kind == "secret_reference":
            if self.secret_ref is None or self.value is not None:
                raise ValueError("secret_reference requires only secret_ref")
        else:
            if self.value is None or self.secret_ref is not None or SECRET_NAME.search(self.name):
                raise ValueError("credential values cannot be public configuration")
            reject_secret(self.value)
        return self


class ConfigurationManifest(P5Record):
    entries: list[ConfigurationEntry]

    @model_validator(mode="after")
    def names(self):
        unique([x.name for x in self.entries], "configuration names")
        return self


class RequiredFlow(P5Record):
    flow_id: Id
    payment_family: Id
    scenario_refs: Refs
    required: StrictBool
    origin_routes: Refs
    acceptance_rule_ids: Ids
    limitation: Text | None


class RequiredFlowManifest(P5Record):
    flows: list[RequiredFlow]


class Omission(P5Record):
    component_id: Id
    path: RelativePath | None
    reason_code: Id
    required_for_scope: StrictBool
    evidence_refs: Refs


class OmissionManifest(P5Record):
    items: list[Omission]


class UnresolvedInputs(P5Record):
    items: list[Issue]


class WorkPackage(P5Record):
    work_package_id: Id
    case_id: Id
    resource_graph_ref: Ref
    resource_graph_digest: Digest
    scope_digest: Digest
    source_snapshot_refs: Refs
    components_ref: Ref
    external_dependencies_ref: Ref
    state_recipe_refs: Refs
    synthetic_seed_refs: Refs
    required_flow_refs: Refs
    processing_policy_digest: Digest
    custody_policy_digest: Digest
    runtime_profile_digest: Digest
    fixture_profile_digest: Digest
    baseline_manifest_digest: Digest
    omission_manifest_ref: Ref
    acquisition_expires_at: Utc
    completeness: Literal["sufficient_for_declared_static_scope", "incomplete", "unknown"]
    unresolved_requirements_ref: Ref
    delivery_feasibility_ref: Ref

    @model_validator(mode="after")
    def complete_inputs(self):
        if self.completeness == "sufficient_for_declared_static_scope" and not (
            self.source_snapshot_refs and self.required_flow_refs and self.state_recipe_refs
        ):
            raise ValueError("complete package requires source, flow and state recipe refs")
        return self
