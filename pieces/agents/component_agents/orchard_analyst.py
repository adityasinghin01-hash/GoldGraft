"""Optional authorised aggregate question, never per-merchant dispatch or SQL."""

from typing import Literal

from goldgraft_contracts.plan5_common import Count, P5Record, Ref
from pydantic import Field

from ..component import metadata


class Bucket(P5Record):
    stage: Literal["held", "verified", "unverified"]
    cases: Count
    unverified: Count


class Input(P5Record):
    tenant_id: str
    purpose: str
    query_ref: Ref
    projection_ref: Ref
    minimum_cohort: int = Field(ge=5, strict=True)
    metrics: list[str] = Field(min_length=1, max_length=2)
    group_by: list[str] = Field(min_length=1, max_length=1)
    filters: dict[str, str]
    buckets: list[Bucket] = Field(min_length=1, max_length=8)


def admit(task, data):
    if (
        data.tenant_id != "offline"
        or data.purpose != "upgrade_audit"
        or data.query_ref != "catalog:upgrade-counts:1"
        or data.projection_ref != "projection:offline:upgrade:1"
    ):
        raise ValueError("DENIED aggregate tenant/purpose/projection")
    if (
        not set(data.metrics) <= {"cases", "unverified"}
        or data.group_by != ["stage"]
        or data.filters != {"tenant": "offline"}
    ):
        raise ValueError("DENIED aggregate query/filter widening")
    if any(b.cases < data.minimum_cohort or b.unverified > b.cases for b in data.buckets):
        raise ValueError("DENIED small cohort or invalid count")


def schemas(operation, data):
    return ["DashboardSpec/1"]


def requests(task, data):
    return [
        dict(
            tool="aggregate.read",
            arguments={"query_ref": data.query_ref, "projection_ref": data.projection_ref},
        )
    ]


def synthesize(task, data, packet, observations):
    return [
        dict(
            schema="DashboardSpec/1",
            payload={
                **metadata(task, packet),
                "question": "How many authorised synthetic cases are in each stage?",
                "title": "Authorised synthetic upgrade aggregate",
                "metrics": data.metrics,
                "group_by": data.group_by,
                "filters": data.filters,
                "evidence_refs": [data.projection_ref],
            },
        )
    ]


def review(task, data, packet, outputs, observations):
    v = observations[0]["value"]["payload"]
    if (
        v.get("tenant_id"),
        v.get("purpose"),
        v.get("projection_ref"),
        v.get("raw_rows"),
        v.get("buckets"),
    ) != (
        "offline",
        "upgrade_audit",
        data.projection_ref,
        False,
        [b.model_dump(mode="json") for b in data.buckets],
    ):
        raise ValueError("DENIED aggregate observation ACL")
    if outputs != synthesize(task, data, packet, observations):
        raise ValueError("DENIED dashboard scope or unsupported claim")


def inspect(outputs):
    v = outputs[0]["payload"]
    return dict(
        metrics=v["metrics"],
        group_by=v["group_by"],
        filters=v["filters"],
        evidence_refs=v["evidence_refs"],
        raw_rows=False,
        merchant_dispatch=False,
    )


def sample(operation):
    return dict(
        tenant_id="offline",
        purpose="upgrade_audit",
        query_ref="catalog:upgrade-counts:1",
        projection_ref="projection:offline:upgrade:1",
        minimum_cohort=5,
        metrics=["cases", "unverified"],
        group_by=["stage"],
        filters={"tenant": "offline"},
        buckets=[dict(stage="unverified", cases=8, unverified=8)],
    )
