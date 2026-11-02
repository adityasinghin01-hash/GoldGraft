"""Survey, build, planning and no-code artifacts (design 01–03)."""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, StrictBool, model_validator

from .common import Count, Format, PositiveInt, Probability, Text
from .money import Money


class FileLocation(Format):
    file: Text
    line: PositiveInt


class SiteLocation(Format):
    url: Text
    selector: Text


class AccountLocation(Format):
    tcode: Text


Location = FileLocation | SiteLocation | AccountLocation


class Family(StrEnum):
    WPS = "WPS"
    EC_NVP = "EC_NVP"
    EC_SOAP = "EC_SOAP"
    DIRECT_PAYMENT = "DIRECT_PAYMENT"
    RECURRING_NVP = "RECURRING_NVP"
    BILLING_AGREEMENT = "BILLING_AGREEMENT"
    IPN = "IPN"
    PDT = "PDT"
    CHECKOUT_JS_V4 = "CHECKOUT_JS_V4"
    JS_V5 = "JS_V5"
    REST_V1 = "REST_V1"
    SERVER_SDK_OLD = "SERVER_SDK_OLD"
    PAYFLOW = "PAYFLOW"
    BUTTON_HOSTED = "BUTTON_HOSTED"


class Lens(StrEnum):
    CODE = "code"
    RUNTIME = "runtime"
    SITE = "site"
    ACCOUNT = "account"


class Stack(Format):
    lang: Text
    framework: Text
    versions: dict[str, str]
    db: Text


class TouchpointTarget(Format):
    paypal_mapping_id: Text
    rest_op: Text


class Touchpoint(Format):
    id: Text
    family: Family
    operation: Text
    location: Location
    lenses: list[Lens]
    confidence: Probability
    live: StrictBool
    target: TouchpointTarget
    paypal_only: StrictBool
    money_30d: Money | None = None


class MoneyFlow(Format):
    create: list[Location]
    approve: list[Location]
    capture: list[Location]
    mark_paid: list[Location]
    refund: list[Location]
    notify: list[Location]
    recurring: list[Location]


class RecallEvidence(Format):
    runtime_calls_total: Count
    matched_by_static: Count
    misses: list[Text]

    @model_validator(mode="after")
    def matched_count(self):
        if self.matched_by_static > self.runtime_calls_total:
            raise ValueError("matched_by_static exceeds runtime_calls_total")
        return self


class RootMap(Format):
    shop_id: Text
    stack: Stack
    lenses_run: list[Lens]
    touchpoints: list[Touchpoint]
    money_flow: MoneyFlow
    recall_evidence: RecallEvidence


class ConnectionChecks(Format):
    rest_ok: StrictBool
    nvp_ok: StrictBool
    webhook_ok: StrictBool
    version_match: StrictBool


class Connection(Format):
    shop_id: Text
    repo: Text | None
    site: Text | None
    secrets_ref: Annotated[str, Field(pattern=r"^doppler://\S+$")]
    checks: ConnectionChecks

    @model_validator(mode="after")
    def connected_target(self):
        if self.repo is None and self.site is None:
            raise ValueError("repo or site is required")
        return self


class ProbeResult(Format):
    families_found: list[Family]
    files_or_pages: list[Text]
    official_modern_module_available: StrictBool | None = None
    deadline_notes: list[Text]
    next_step: Text


class RunnableShop(Format):
    compose: Text
    image_digests: dict[str, Text]
    seed: Text
    base_url: Text
    health: dict[str, StrictBool]


# Step shapes live here so drivers and scenarios share the same union.
class DriverStep(Format):
    driver_step: Text


class ApiStep(Format):
    api_step: Text


class MockStep(Format):
    paypal_mock_response_code: Text


Step = DriverStep | ApiStep | MockStep


class Driver(Format):
    steps: list[Step]
    selectors: dict[str, Text]
    proven_runs: Count


class PlanPath(StrEnum):
    OFFICIAL_MODULE = "OFFICIAL_MODULE"
    REWRITE = "REWRITE"
    LINKS = "LINKS"


class TargetExperience(StrEnum):
    V6 = "V6"
    ORDERS_V2 = "ORDERS_V2"
    WEBHOOKS = "WEBHOOKS"
    VAULT = "VAULT"
    PAY_LATER_MSG = "PAY_LATER_MSG"
    PLACEMENT = "PLACEMENT"
    AGENT_READY_CHECK = "AGENT_READY_CHECK"


class PlanOrder(StrEnum):
    READ_BOTH = "READ_BOTH"
    NEW_FLOWS_BEHIND_SWITCH = "NEW_FLOWS_BEHIND_SWITCH"
    CLEANUP = "CLEANUP"


class PlanItem(Format):
    touchpoint: Text
    target_op: Text
    mapping_id: Text
    delta_ids: list[Text]
    paypal_only: StrictBool


class IntentDelta(Format):
    id: Text
    mapping_id: Text
    description: Text


class TargetPlan(Format):
    path: PlanPath
    items: list[PlanItem]
    target_experience: list[TargetExperience]
    origin_rules: list[Text]
    order: list[PlanOrder]
    handoff: list[Text]
    deltas: list[IntentDelta] = Field(default_factory=list)


class LinkButton(Format):
    page: Text
    old_form_fields: dict[str, str] | None = None
    hosted_button_id: Text | None = None
    new_link_url: Text
    snippet_html: Text

    @model_validator(mode="after")
    def old_button(self):
        if (self.old_form_fields is None) == (self.hosted_button_id is None):
            raise ValueError("exactly one of old_form_fields and hosted_button_id required")
        return self


class LinkProof(Format):
    link: Text
    order_id: Text
    capture_id: Text


class UntouchedKind(StrEnum):
    DONATE = "Donate"
    SUBSCRIBE = "Subscribe"


class LinksPack(Format):
    buttons: list[LinkButton]
    proofs: list[LinkProof]
    untouched: list[UntouchedKind]
