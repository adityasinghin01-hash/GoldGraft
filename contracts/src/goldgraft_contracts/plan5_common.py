"""Strict additive Plan5 primitives. Legacy formats retain their original semantics."""

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import PurePosixPath
from typing import Annotated, ClassVar, Literal

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BeforeValidator,
    Field,
    StrictStr,
    model_validator,
)

from .common import Count as Count
from .common import Format, PositiveInt

Id = Annotated[StrictStr, Field(min_length=1, max_length=256, pattern=r"^\S+$")]
Ref = Annotated[StrictStr, Field(min_length=1, max_length=1024, pattern=r"^\S+$")]
Digest = Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
Positive = PositiveInt
Text = Annotated[StrictStr, Field(min_length=1, max_length=8192)]
Refs = Annotated[list[Ref], Field(max_length=256)]
Ids = Annotated[list[Id], Field(max_length=256)]
Epochs = Annotated[dict[Id, Positive], Field(max_length=256)]
OciDigest = Annotated[StrictStr, Field(pattern=r"^sha256:[a-f0-9]{64}$")]
GitCommit = Annotated[StrictStr, Field(pattern=r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")]
EvidenceClass = Literal[
    "scripted",
    "component_offline",
    "real_model",
    "real_provider",
    "real_payment",
    "isolation_qualified",
    "merchant_exit",
]
Role = Literal[
    "Gardener",
    "Surveyor",
    "Builder",
    "Explorer",
    "Scribe",
    "Architect",
    "Grafter",
    "Adversary",
    "Healer",
    "Librarian",
    "Herald",
    "Orchard Analyst",
    "Sentinel",
]
Operation = Literal[
    "verify_package",
    "survey",
    "explain_status",
    "audit",
    "propose_plan",
    "build_baseline",
    "build_candidate",
    "validate_driver",
    "run_scenario",
    "scribe_draft",
    "scribe_final",
    "architect",
    "candidate_patch",
    "run_mutant",
    "derive_guards",
    "diagnose",
    "learn",
    "selfcheck_recipe",
    "aggregate",
]
DeliveryOperation = Literal[
    "review_evaluate",
    "plan_apply",
    "reserve_targets",
    "preserve_state",
    "publish_artifact",
    "publish_source",
    "merge_protected",
    "apply_configuration",
    "deploy_exact",
    "reconcile_effect",
    "observe_target",
    "finalise",
    "prepare_exit",
    "run_exit",
    "read_exit_evidence",
    "revoke_exit_evidence",
    "reconcile_cleanup",
]


def timestamp_input(value):
    if not isinstance(value, (str, datetime)):
        raise ValueError("UTC timestamp must be an ISO string or datetime, never a number")
    return value


def utc_only(value):
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC")
    return value


Utc = Annotated[AwareDatetime, BeforeValidator(timestamp_input), AfterValidator(utc_only)]


def relative_path(value):
    if "\\" in value or ":" in value or "\x00" in value or value.startswith("/"):
        raise ValueError("path must be a safe relative POSIX path")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("path traversal/empty components forbidden")
    if unicodedata.normalize("NFC", value) != value or str(PurePosixPath(value)) != value:
        raise ValueError("path must be normalized")
    return value


RelativePath = Annotated[
    StrictStr, Field(min_length=1, max_length=1024), AfterValidator(relative_path)
]


def canonical_bytes(value):
    if isinstance(value, Format):
        value = value.model_dump(mode="json", by_alias=True)
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def content_digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def unique(values, name):
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {name}")


def validate_dag(items, id_field, dependency_field, *, maximum=32, allow_external=False):
    if not items or len(items) > maximum:
        raise ValueError("DAG must have 1..32 nodes")
    ids = [getattr(item, id_field) for item in items]
    unique(ids, id_field)
    edges = {getattr(item, id_field): getattr(item, dependency_field) for item in items}
    visiting, done = set(), set()

    def visit(node):
        if node in visiting:
            raise ValueError("dependency cycle")
        if node in done:
            return
        if node not in edges:
            if allow_external:
                return
            raise ValueError("missing dependency")
        visiting.add(node)
        unique(edges[node], "dependencies")
        for dep in edges[node]:
            visit(dep)
        visiting.remove(node)
        done.add(node)

    for node in ids:
        visit(node)


class P5Record(Format):
    """Closed records with bounded intake; contextual ACL checks belong to accepting services."""

    intake_collection_limit: ClassVar[int] = 256

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        from .plan5_schema import decorate

        return decorate(handler(core_schema), cls.__name__, cls.intake_collection_limit)

    @model_validator(mode="before")
    @classmethod
    def bound_intake(cls, value):
        if isinstance(value, Mapping):
            for item in value.values():
                if isinstance(item, (list, dict)) and len(item) > cls.intake_collection_limit:
                    raise ValueError(f"collection exceeds {cls.intake_collection_limit} items")
                if isinstance(item, str) and len(item) > 32768:
                    raise ValueError("string exceeds intake bound")
        return value

    @model_validator(mode="after")
    def time_order(self):
        for start, end in [
            ("created_at", "expires_at"),
            ("issued_at", "expires_at"),
            ("started_at", "finished_at"),
        ]:
            a, b = getattr(self, start, None), getattr(self, end, None)
            if a is not None and b is not None and a >= b:
                if start == "started_at" and a == b:
                    continue
                raise ValueError(f"{end} must follow {start}")
        return self


class Issue(P5Record):
    code: Id
    input_ref: Ref | None
    owner_role: Id
    recovery: Literal[
        "retry_read",
        "reconnect",
        "supply_input",
        "review_scope",
        "reapprove",
        "await_counterpart",
        "reconcile",
        "unsupported",
    ]
    evidence_refs: Refs


SECRET_NAME = re.compile(
    r"(?i)(?:secret|password|token|private.?key|nvp_(?:user|signature)|credential)"
)
SECRET_VALUE = re.compile(
    r"(?:sk-ant-|gh[pousr]_|github_pat_|AKIA[0-9A-Z]{12}|-----BEGIN .*PRIVATE KEY|Bearer\s+)", re.I
)


def reject_secret(value):
    if SECRET_VALUE.search(value):
        raise ValueError("credential-like values forbidden")
    return value
