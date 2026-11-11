"""Connection package for GoldGraft backend (GU01 & GU02).

Provides:
- cases.py: ConnectionCase tracking, workspace boundaries, and controller binding (GU01).
- authority.py: Strict role grants, escalation denial, and scope checking (GU01).
- providers.py: Read-provider adapters for GitHub, Render, WorkOS (GU01).
- resource_graph.py: Resource topology and scope boundary mapping (GU01).
- acquisition.py: Source code archive acquisition and quarantine (GU02).
- upload_sessions.py: Chunked uploads with digest verification (GU02).
- readiness.py: Pre-flight readiness and safety inspection (GU02).
"""

from .acquisition import AcquiredAsset, SourceAcquisition
from .authority import (
    AuthorityGrant,
    AuthorityManager,
    CaseRole,
    PermissionDeniedError,
)
from .cases import CaseManager, CaseStatus, ConnectionCase
from .providers import ProviderAdapter, ProviderObservation
from .readiness import ConnectionReadiness, ReadinessCheck, ReadinessInspector
from .resource_graph import ResourceGraph, ResourceNode
from .upload_sessions import UploadChunk, UploadSession, UploadSessionManager

__all__ = [
    "AcquiredAsset",
    "AuthorityGrant",
    "AuthorityManager",
    "CaseManager",
    "CaseRole",
    "CaseStatus",
    "ConnectionCase",
    "ConnectionReadiness",
    "PermissionDeniedError",
    "ProviderAdapter",
    "ProviderObservation",
    "ReadinessCheck",
    "ReadinessInspector",
    "ResourceGraph",
    "ResourceNode",
    "SourceAcquisition",
    "UploadChunk",
    "UploadSession",
    "UploadSessionManager",
]

