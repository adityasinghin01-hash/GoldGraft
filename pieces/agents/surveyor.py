"""Bounded source-inventory checks and inspection; no model/client or host IO."""

import hashlib
from typing import Literal

from goldgraft_contracts.agent_runtime import SubjectManifest
from goldgraft_contracts.plan5_common import (
    P5Record,
    RelativePath,
    canonical_bytes,
    content_digest,
    reject_secret,
)
from goldgraft_contracts.survey import Family, RootMap, Stack
from goldgraft_contracts.work_package import ManifestEntry, OmissionManifest, SourceSnapshot
from pydantic import Field

from .source_references import discover_component_gaps


class DetectionRule(P5Record):
    rule_id: str
    needle: str = Field(min_length=1, max_length=128)
    family: Family
    operation: str
    flow: Literal["create", "approve", "capture", "mark_paid", "refund", "notify", "recurring"]
    target_operation: Literal["unqualified"]


class SurveyInputs(P5Record):
    snapshot_ref: str
    omission_ref: str
    rule_ref: str
    snapshot: SourceSnapshot
    omissions: OmissionManifest
    manifest: list[ManifestEntry] = Field(max_length=16)
    files: dict[RelativePath, str] = Field(max_length=16)
    rules: list[DetectionRule] = Field(min_length=1, max_length=64)
    shop_id: str
    stack: Stack
    required_lenses: list[Literal["code", "runtime", "site", "account"]]


def validate_inputs(task, value):
    reject_secret(canonical_bytes(value).decode())
    inputs = SurveyInputs.model_validate(value)
    snapshot = inputs.snapshot
    if (
        snapshot.case_id != task.case_id
        or snapshot.snapshot_id != inputs.snapshot_ref
        or task.task.input_refs != [inputs.snapshot_ref, inputs.omission_ref]
        or snapshot.omission_manifest_ref != inputs.omission_ref
    ):
        raise ValueError("DENIED source input binding")
    if (
        snapshot.completeness != "complete_for_declared_scope"
        or any(item.required_for_scope for item in inputs.omissions.items)
        or set(inputs.required_lenses) != {"code"}
    ):
        raise ValueError("MISSING_EVIDENCE required source/lens")
    entries = {e.relative_path: e for e in inputs.manifest}
    if (
        len(entries) != len(inputs.manifest)
        or not entries
        or any(e.file_type != "file" for e in entries.values())
        or set(entries) != set(inputs.files)
        or snapshot.manifest_digest
        != content_digest([e.model_dump(mode="json") for e in inputs.manifest])
        or snapshot.file_count != len(entries)
    ):
        raise ValueError("MISSING_EVIDENCE source manifest")
    total = 0
    for path, text in inputs.files.items():
        raw = text.encode()
        total += len(raw)
        entry = entries[path]
        if entry.bytes != len(raw) or entry.sha256 != hashlib.sha256(raw).hexdigest():
            raise ValueError("DENIED source bytes")
    if total != snapshot.total_bytes or total > 16384:
        raise ValueError("MISSING_EVIDENCE bounded source context")
    # A caller's complete snapshot/empty omissions cannot hide an unresolved
    # dependency visible in the supplied bytes. Never execute or fetch it.
    if discover_component_gaps(inputs.files):
        raise ValueError("MISSING_EVIDENCE unresolved source reference")
    if len({r.rule_id for r in inputs.rules}) != len(inputs.rules):
        raise ValueError("DENIED duplicate detection rule")
    subject = SubjectManifest(
        source_snapshot_refs=[inputs.snapshot_ref],
        source_tree_digest=snapshot.manifest_digest,
        oci_manifest_digest=None,
        config_digest=None,
        runtime_profile_digest=content_digest("offline-source-inventory:1"),
        scope_digest=content_digest(
            {
                k: inputs.model_dump(mode="json")[k]
                for k in (
                    "snapshot",
                    "omissions",
                    "rules",
                    "rule_ref",
                    "required_lenses",
                    "shop_id",
                    "stack",
                )
            }
        ),
    )
    if task.task.expected_subject != content_digest(subject):
        raise ValueError("DENIED source subject manifest")
    return inputs


def indicators(inputs):
    """Literal catalog observations; not an AST, reachability or live-flow proof."""
    return [
        {
            "rule_id": rule.rule_id,
            "file": path,
            "line": number,
            "family": rule.family.value,
            "operation": rule.operation,
            "flow": rule.flow,
        }
        for path, text in sorted(inputs.files.items())
        for number, line in enumerate(text.splitlines(), 1)
        for rule in inputs.rules
        if rule.needle in line
    ]


def inspect_inventory(root_map, *, input_refs, output_ref, subject, evidence_refs, omissions):
    """Read-only downstream consumer of a validated inventory; no authoritative status."""
    result = RootMap.model_validate(root_map)
    return {
        "role": "Surveyor",
        "evidence_class": "scripted",
        "output_ref": output_ref,
        "input_refs": input_refs,
        "subject_digest": subject,
        "evidence_refs": evidence_refs,
        "shop_id": result.shop_id,
        "touchpoints": [
            {
                "id": t.id,
                "family": t.family.value,
                "operation": t.operation,
                "location": t.location.model_dump(mode="json"),
                "live": t.live,
            }
            for t in result.touchpoints
        ],
        "money_flow": result.money_flow.model_dump(mode="json"),
        "lenses_observed": [lens.value for lens in result.lenses_run],
        "omissions": omissions,
        "limitations": [
            "Scripted model responses; real-model competence NOT EVALUATED.",
            "Literal indicators may include comments/strings; dynamic calls may be missed.",
            "Runtime/site/account lenses unavailable; runtime recall NOT MEASURED.",
            "Target API/SDK mappings unqualified; no payment or merchant-completion proof.",
        ],
    }


def validate_inventory(task, payload, inputs, observations):
    result = RootMap.model_validate(payload)
    if result.shop_id != inputs.shop_id or result.stack != inputs.stack:
        raise ValueError("DENIED inventory identity")
    if [lens.value for lens in result.lenses_run] != ["code"]:
        raise ValueError("MISSING_EVIDENCE unobserved lens")
    reads, matches, omission_seen = set(), False, False
    for envelope in observations:
        if envelope.get("evidence_class") != "scripted":
            raise ValueError("DENIED evidence class")
        value = envelope.get("value", {})
        kind = value.get("kind")
        if kind == "source_excerpt":
            path = value.get("path")
            if (
                path not in inputs.files
                or value.get("snapshot_ref") != inputs.snapshot_ref
                or value.get("excerpt") != inputs.files[path]
                or value.get("sha256") != hashlib.sha256(inputs.files[path].encode()).hexdigest()
            ):
                raise ValueError("DENIED source observation")
            reads.add(path)
        elif kind == "matches":
            if (
                value.get("snapshot_ref") != inputs.snapshot_ref
                or value.get("rule_ref") != inputs.rule_ref
                or value.get("matches") != indicators(inputs)
                or value.get("truncated") is not False
            ):
                raise ValueError("DENIED detection observation")
            matches = True
        elif kind == "omissions":
            if value.get("ref") != inputs.omission_ref or value.get("payload") != (
                inputs.omissions.model_dump(mode="json")
            ):
                raise ValueError("DENIED omission observation")
            omission_seen = True
        else:
            raise ValueError("DENIED unknown observation")
    if reads != set(inputs.files) or not matches or not omission_seen:
        raise ValueError("MISSING_EVIDENCE unread required input")
    expected = {
        (m["file"], m["line"], m["family"], m["operation"], m["rule_id"])
        for m in indicators(inputs)
    }
    observed = set()
    for touchpoint in result.touchpoints:
        location = touchpoint.location.model_dump(mode="json")
        if (
            set(location) != {"file", "line"}
            or touchpoint.live
            or [lens.value for lens in touchpoint.lenses] != ["code"]
            or touchpoint.money_30d is not None
            or touchpoint.confidence > 0.5
            or touchpoint.target.rest_op != "unqualified"
            or touchpoint.paypal_only is not False
        ):
            raise ValueError("MISSING_EVIDENCE unsupported touchpoint claim")
        key = (
            location["file"],
            location["line"],
            touchpoint.family.value,
            touchpoint.operation,
            touchpoint.target.paypal_mapping_id,
        )
        if key in observed:
            raise ValueError("DENIED duplicate touchpoint")
        observed.add(key)
    if observed != expected or len({t.id for t in result.touchpoints}) != len(result.touchpoints):
        raise ValueError("MISSING_EVIDENCE omitted/ungrounded touchpoint")
    for flow, locations in result.money_flow.model_dump(mode="json").items():
        wanted = {(m["file"], m["line"]) for m in indicators(inputs) if m["flow"] == flow}
        actual = {(x.get("file"), x.get("line")) for x in locations}
        if actual != wanted or len(actual) != len(locations):
            raise ValueError("MISSING_EVIDENCE money flow location")
    if result.recall_evidence.model_dump() != {
        "runtime_calls_total": 0,
        "matched_by_static": 0,
        "misses": [],
    }:
        raise ValueError("MISSING_EVIDENCE runtime recall unmeasured")
    # Also bound typed content before it becomes a descriptor.
    if len(canonical_bytes(result)) > 4000:
        raise ValueError("MISSING_EVIDENCE output context capacity")
    return result
