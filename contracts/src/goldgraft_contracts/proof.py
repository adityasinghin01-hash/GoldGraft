"""Contracts, scenarios, mutants, verdicts, and certificate (design 01, 04)."""

from enum import StrEnum

from pydantic import Field, StrictBool, model_validator

from .common import Count, Format, JsonValue, NonNegative, Probability, Side, Text, Timestamp
from .survey import FileLocation, Step


class Agreement(StrEnum):
    BOTH = "BOTH"
    CODE_ONLY = "CODE_ONLY"
    TRACE_ONLY = "TRACE_ONLY"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class Triangle(Format):
    scenarios: list[Text]
    mutants: list[Text]
    killed: StrictBool


class RuleSources(Format):
    code: list[Text]
    traces: list[Text]


class Rule(Format):
    id: Text
    title: Text
    correct_flow: list[Text]
    counter_examples: list[Text]
    predicate: Text
    sources: RuleSources
    agreement: Agreement
    triangle: Triangle
    severity: Severity


class MoneyContract(Format):
    shop_id: Text
    rules: list[Rule]

    @model_validator(mode="after")
    def unique_rules(self):
        ids = [rule.id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("rule ids must be unique within a contract")
        return self


Contract = MoneyContract


class ScenarioFamily(StrEnum):
    HAPPY = "HAPPY"
    CANCEL = "CANCEL"
    DECLINE = "DECLINE"
    PAYER_ACTION = "PAYER_ACTION"
    DOUBLE = "DOUBLE"
    LOST_RESPONSE = "LOST_RESPONSE"
    TAMPER = "TAMPER"
    PENDING = "PENDING"
    REFUND = "REFUND"
    REFUND_TWICE = "REFUND_TWICE"
    NOTIFY_FORGED = "NOTIFY_FORGED"
    NOTIFY_DUP = "NOTIFY_DUP"
    RESTART = "RESTART"
    RENEWAL = "RENEWAL"
    EDGE_CURRENCY = "EDGE_CURRENCY"
    PROPERTY = "PROPERTY"


class Assured(Format):
    passes_on_old: StrictBool
    flake_free_runs: Count


class Scenario(Format):
    id: Text
    family: ScenarioFamily
    cart: dict[str, JsonValue]
    steps: list[Step]
    rules: list[Text]
    expect: dict[str, JsonValue]
    assured: Assured


class MutantOp(StrEnum):
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M7 = "M7"
    M8 = "M8"
    M9 = "M9"
    M10 = "M10"
    M11 = "M11"
    M12 = "M12"


class Mutant(Format):
    id: Text
    op: MutantOp
    location: FileLocation
    patch: Text
    rule: Text
    equivalent_suspect: StrictBool
    killed_by: list[Text]


class MutationOperator(Format):
    op: MutantOp
    fault: Text
    rules_broken: list[Text]


class Grade(StrEnum):
    PROBLEM = "PROBLEM"
    UNVERIFIED = "UNVERIFIED"
    PASS = "PASS"
    PASS_FIXED = "PASS_FIXED"
    NOT_APPLICABLE = "N/A"


class RuleHit(Format):
    rule: Text
    side: Side
    evidence: list[Text]


class Verdict(Format):
    scenario_id: Text
    grade: Grade
    rule_hits: list[RuleHit]
    parity_diff: list[JsonValue]
    noise_masked: list[Text]
    deltas_applied: list[Text]


class ProofStrength(Format):
    total: Count
    equivalent_dropped: Count
    killed: Count
    score: Probability

    @model_validator(mode="after")
    def counts(self):
        if (
            self.equivalent_dropped > self.total
            or self.killed > self.total - self.equivalent_dropped
        ):
            raise ValueError("inconsistent mutant counts")
        return self


class CertificateResults(Format):
    scenarios: Count
    pass_: Count = Field(alias="pass")
    pass_fixed: Count
    problem: Count = Field(le=0)
    unverified: Count
    n_a: Count

    @model_validator(mode="after")
    def totals(self):
        if self.scenarios != self.pass_ + self.pass_fixed + self.unverified + self.n_a:
            raise ValueError("scenario result counts do not add up")
        return self


class CertificateStrength(Format):
    mutants_total: Count
    equivalent_dropped: Count
    killed: Count
    score: Probability

    @model_validator(mode="after")
    def counts(self):
        ProofStrength(
            total=self.mutants_total,
            equivalent_dropped=self.equivalent_dropped,
            killed=self.killed,
            score=self.score,
        )
        return self


class CertificateSurvey(Format):
    recall: Probability
    precision: Probability
    misses_learned: Count


class CertificateSecurity(Format):
    secrets_found: Count = Field(le=0)
    injection_attempts_blocked: Count
    deps_blocked: Count


class PayPalEvidence(Format):
    scenario: Text
    order_id: Text
    capture_id: Text
    debug_id: Text


class CertificateCost(Format):
    usd: NonNegative
    tokens: Count


class RunnerIdentity(Format):
    workflow: Text
    sha: Text


class Certificate(Format):
    cert_id: Text
    shop_id: Text
    repo: Text
    commit_old: Text
    commit_new: Text
    branch: Text
    issued_at: Timestamp
    results: CertificateResults
    proof_strength: CertificateStrength
    survey: CertificateSurvey
    security: CertificateSecurity
    paypal_evidence: list[PayPalEvidence]
    cost: CertificateCost
    time: dict[str, NonNegative]
    ledger_root: Text
    runner_identity: RunnerIdentity
    signature: Text
    rekor_entry: Text
    ots_proof: Text | None = None
