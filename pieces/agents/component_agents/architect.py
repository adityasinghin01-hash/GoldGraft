"""Payment-only plans grounded in exact inventory and pinned symbols."""

import re

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
    if any(e.get("final") is False for e in data.evidence.values()):
        raise ValueError("MISSING_EVIDENCE conflicting final Contract evidence")
    got = TargetPlan.model_validate(outputs[0]["payload"]).model_dump(mode="json")
    want = draft(data)
    text = " ".join(got["handoff"])
    if (
        got["path"] != want["path"]
        or sorted(got["items"], key=lambda i: i["touchpoint"])
        != sorted(want["items"], key=lambda i: i["touchpoint"])
        or sorted(got["target_experience"]) != sorted(want["target_experience"])
        or sorted(got["origin_rules"]) != sorted(want["origin_rules"])
        or got["order"] != want["order"]
        or got["deltas"]
        or not 1 <= len(text) <= 800
        or "independent proof required" not in text.lower()
        or re.search(
            r"\b(deployed|published|verified|migrate accounts|switch accounts)\b", text, re.I
        )
    ):
        raise ValueError("DENIED invented API, unrelated change or unapproved delta")


PROGRESS = True


def route(data):
    # Duplicate final calls also recurred twice on single-touchpoint tasks. End
    # Haiku tuning: select the demonstrated Sonnet planner before any dispatch.
    return "sonnet"


def facts(task, data):
    return {
        "max_bytes": 4096,
        "call_policy": "Read recipe.lookup and docs.lookup using the pinned catalog fields, "
        "and every evidence ref with evidence.read(max_bytes=4096). Follow unread_reads; "
        "at most four reads per response. A final_contract flag cannot override conflicting "
        "final evidence: hold if required evidence is missing or contradictory. Otherwise "
        "produce a REWRITE TargetPlan covering every mapping exactly once: touchpoint, "
        "target_op=symbol, mapping_id; paypal_only true, delta_ids empty. Preserve Contract "
        "origin rule ids; target_experience ORDERS_V2 and WEBHOOKS; order READ_BOTH, "
        "NEW_FLOWS_BEHIND_SWITCH, CLEANUP; deltas empty. Handoff must state 'independent "
        "proof required'. Literal wording guard ignores negation: avoid deployed, published, "
        "verified, migrate accounts and switch accounts. No apply authority or account change.",
    }


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
