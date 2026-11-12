"""Explicit synthetic custody counterpart; cannot authenticate provider/payment/exit evidence."""

from dataclasses import dataclass

from goldgraft_contracts.agent_runtime import ArtifactDescriptor
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest


@dataclass(frozen=True)
class FakeStoredArtifact:
    descriptor: ArtifactDescriptor
    payload: bytes


class FakeEvidenceCustody:
    evidence_class = "component_offline"

    def __init__(self, tenant_id, case_id, run_id, generation, resource_epochs):
        self.identity = tenant_id, case_id, run_id, generation, dict(resource_epochs)
        self.records, self.roles = {}, {}
        self.revoked = False

    def register(self, descriptor, payload, owner_role):
        if descriptor.evidence_class not in {"scripted", "component_offline"}:
            raise ValueError("fake custody cannot qualify external evidence")
        raw = canonical_bytes(payload)
        if descriptor.payload_digest != content_digest(payload) or descriptor.byte_count != len(
            raw
        ):
            raise ValueError("fixture bytes mismatch")
        self.records[descriptor.ref] = FakeStoredArtifact(descriptor, raw)
        self.roles[descriptor.ref] = owner_role

    def resolve(self, ref):
        return None if self.revoked else self.records.get(ref)

    def authenticate(self, record, context, role):
        current = (
            context.tenant_id,
            context.case_id,
            context.run_id,
            context.generation,
            context.resource_epochs,
        )
        return (
            not self.revoked
            and current == self.identity
            and self.records.get(record.descriptor.ref) == record
            and self.roles.get(record.descriptor.ref) == role
            and record.descriptor.evidence_class in {"scripted", "component_offline"}
        )
