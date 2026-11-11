"""Payment-only plans grounded in exact inventory and pinned symbols."""

from goldgraft_contracts.plan5_common import P5Record, Ref
from goldgraft_contracts.proof import MoneyContract
from goldgraft_contracts.survey import RootMap, TargetPlan
from pydantic import Field, StrictBool

from .execution import Catalog, catalog_sample
from .scribe import sample as scribe_sample


class Mapping(P5Record):
    touchpoint_id: str
    symbol: str
    mapping_id: str
    payment_only: StrictBool


class Input(P5Record):
    root_map: RootMap
    contract: MoneyContract
    evidence: dict[Ref, dict]
    catalog: Catalog
    mappings: list[Mapping] = Field(min_length=1, max_length=16)
    final_contract: StrictBool


def admit(task, data):
    if (
        not data.final_contract
        or not data.contract.rules
        or data.root_map.shop_id != data.contract.shop_id
    ):
        raise ValueError("MISSING_EVIDENCE final grounded Contract")
    if not data.catalog.qualified_fixture:
        raise ValueError("MISSING_EVIDENCE pinned documentation")
    touches = {t.id: t for t in data.root_map.touchpoints}
    if len(data.mappings) != len(touches) or {m.touchpoint_id for m in data.mappings} != set(
        touches
    ):
        raise ValueError("MISSING_EVIDENCE every touchpoint mapping")
    for m in data.mappings:
        t = touches[m.touchpoint_id]
        if t.family.value not in {"EC_NVP", "IPN"} or not m.payment_only or not t.paypal_only:
            raise ValueError("DENIED unsupported migration or unrelated scope")
        if (
            m.symbol not in data.catalog.installed_symbols
            or m.mapping_id != t.target.paypal_mapping_id
        ):
            raise ValueError("MISSING_EVIDENCE exact API symbol/mapping")


def schemas(operation, data):
    return ["TargetPlan/1"]


def requests(task, data):
    return [
        dict(
            tool="recipe.lookup",
            arguments=dict(catalog_ref=data.catalog.ref, fingerprint=data.catalog.fingerprint),
        ),
        dict(
            tool="docs.lookup",
            arguments=dict(
                catalog_ref=data.catalog.ref, topic=data.catalog.topic, version=data.catalog.version
            ),
        ),
        *[dict(tool="evidence.read", arguments=dict(ref=r, max_bytes=4096)) for r in data.evidence],
    ]


def draft(data):
    return TargetPlan(
        path="REWRITE",
        items=[
            dict(
                touchpoint=m.touchpoint_id,
                target_op=m.symbol,
                mapping_id=m.mapping_id,
                delta_ids=[],
                paypal_only=True,
            )
            for m in data.mappings
        ],
        target_experience=["ORDERS_V2", "WEBHOOKS"],
        origin_rules=[r.id for r in data.contract.rules],
        order=["READ_BOTH", "NEW_FLOWS_BEHIND_SWITCH", "CLEANUP"],
        handoff=["Synthetic pinned docs " + data.catalog.version + "; independent proof required"],
        deltas=[],
    ).model_dump(mode="json")


def synthesize(task, data, packet, observations):
    return [dict(schema="TargetPlan/1", payload=draft(data))]


def review(task, data, packet, outputs, observations):
    if outputs[0]["payload"] != draft(data):
        raise ValueError("DENIED invented API, unrelated change or unapproved delta")


def inspect(outputs):
    p = outputs[0]["payload"]
    return dict(
        path=p["path"],
        changes=p["items"],
        normative_rules=p["origin_rules"],
        apply_authority="NONE",
    )


def sample(operation):
    s = scribe_sample("scribe_final")
    return dict(
        root_map=dict(
            shop_id=s["shop_id"],
            stack=dict(lang="php", framework="fixture", versions={"php": "8"}, db="fixture"),
            lenses_run=["code"],
            touchpoints=[
                dict(
                    id="tp-capture",
                    family="EC_NVP",
                    operation="capture",
                    location=dict(file="checkout.php", line=1),
                    lenses=["code"],
                    confidence=1,
                    live=False,
                    target=dict(paypal_mapping_id="fixture-map-capture", rest_op="capture_order"),
                    paypal_only=True,
                )
            ],
            money_flow={
                k: []
                for k in [
                    "create",
                    "approve",
                    "capture",
                    "mark_paid",
                    "refund",
                    "notify",
                    "recurring",
                ]
            },
            recall_evidence=dict(runtime_calls_total=0, matched_by_static=0, misses=[]),
        ),
        contract=dict(shop_id=s["shop_id"], rules=s["normative_rules"]),
        evidence={"fixture:final-contract": {"final": True}},
        catalog=catalog_sample(),
        mappings=[
            dict(
                touchpoint_id="tp-capture",
                symbol="capture_order",
                mapping_id="fixture-map-capture",
                payment_only=True,
            )
        ],
        final_contract=True,
    )
