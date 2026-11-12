"""Private merchant certificate v2. Public projection uses PublicProofView/1 only."""

from typing import Literal, Protocol

from pydantic import model_validator

from .plan5_common import Digest, GitCommit, Id, P5Record, Ref, Refs, Text, Utc
from .proof_evidence import ProofBinding


class CertificateGitSource(P5Record):
    repository_ref: Ref
    branch: Text
    commit_old: GitCommit
    commit_new: GitCommit


class SignatureMaterial(P5Record):
    signature_ref: Ref
    signature_digest: Digest
    transparency_ref: Ref
    transparency_digest: Digest
    authenticity_ref: Ref


class CertificateClaims(ProofBinding):
    cert_id: Id
    review_bundle_ref: Ref
    review_bundle_digest: Digest
    subject_manifest_ref: Ref
    subject_manifest_digest: Digest
    proof_plan_ref: Ref
    proof_plan_digest: Digest
    proof_result_ref: Ref
    proof_result_digest: Digest
    ledger_root: Digest
    source_route: Literal["git", "local_folder", "cloud_files", "host_export"]
    git_source: CertificateGitSource | None
    signer_kind: Literal["github_actions", "trusted_service"]
    signer_identity_ref: Ref
    workflow_identity: Text | None
    workflow_sha: GitCommit | None
    qualification_scope: Literal["component_only", "sandbox_payment", "merchant_delivery"]
    qualification_evidence_refs: Refs
    issued_at: Utc
    expires_at: Utc

    @model_validator(mode="after")
    def conditional_identity(self):
        if (self.source_route == "git") != (self.git_source is not None):
            raise ValueError("Git identity required only for Git source")
        if self.signer_kind == "github_actions":
            if self.workflow_identity is None or self.workflow_sha is None:
                raise ValueError("GitHub signer requires workflow identity and SHA")
        elif self.workflow_identity is not None or self.workflow_sha is not None:
            raise ValueError("non-GitHub signer cannot claim workflow identity")
        if not self.qualification_evidence_refs:
            raise ValueError("certificate requires scoped qualification evidence")
        return self


class CertificateV2(CertificateClaims):
    signature: SignatureMaterial


class CertificateVerification(P5Record):
    cert_id: Id
    case_id: Id
    run_id: Id
    signature_integrity: Literal["verified", "unverified", "invalid"]
    qualification_scope: Literal["component_only", "sandbox_payment", "merchant_delivery"]
    qualification_state: Literal["verified", "held"]
    reason_codes: Refs
    checked_at: Utc

    @model_validator(mode="after")
    def qualified_integrity(self):
        if not self.reason_codes or (
            self.qualification_state == "verified" and self.signature_integrity != "verified"
        ):
            raise ValueError("qualification requires verified signature and fixed reasons")
        return self


class PrivateCertificatePort(Protocol):
    """Host must check current reviewer grants and private artifact custody per call."""

    def read(
        self, tenant_id: str, actor_id: str, case_id: str, cert_id: str
    ) -> CertificateV2 | None: ...

    def verify(
        self, tenant_id: str, actor_id: str, case_id: str, cert_id: str
    ) -> CertificateVerification | None: ...
