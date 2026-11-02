"""The plug-in interfaces. A stand-in (fakes/) and the real piece implement the SAME
Protocol, so swapping one for the other is a one-line change.

Owners: Runner -> backend teammate · Proof -> ML teammate · PayPalClient -> backend +
all-rounder · agent tools (tools.py) -> Aditya.
"""

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from .api import CertificateVerifyResult
from .money import MoneyEvent
from .proof import Certificate, Grade, MoneyContract, Mutant, ProofStrength, Verdict
from .runner import GuardEvent, HealDecision, JobResult, JobSpec, RawCapture
from .survey import TargetPlan

# mutant id -> scenario id -> grade of that scenario when run on NEW + that mutant
MutantRuns = Mapping[str, Mapping[str, Grade]]


@runtime_checkable
class ToolCaller(Protocol):
    """Agent tools enforce their allowlists and schemas before dispatch."""

    def call(self, agent: str, tool: str, args: dict) -> dict: ...


@runtime_checkable
class AgentRunner(Protocol):
    """Registry of the thirteen design-06 agents.

    Returns (versioned schema name, payload) pairs for ledger validation. Attribution
    belongs in LedgerEntry/1; AgentArtifact payloads also carry their own producer.
    """

    def run(self, agent: str, inputs: Mapping[str, object],
            tools: ToolCaller) -> list[tuple[str, dict]]: ...


@runtime_checkable
class Runner(Protocol):
    """Runs shop jobs in the locked box (GitHub Actions VM + gVisor in the real piece)."""

    def run_job(self, spec: JobSpec) -> JobResult: ...

    def fetch_capture(self, ref: str) -> RawCapture: ...


@runtime_checkable
class Proof(Protocol):
    """Deterministic proof library. No AI anywhere in here."""

    def to_cmel(self, capture: RawCapture) -> list[MoneyEvent]:
        """Map one recorded run to money events (mapping table, design 01 §3).
        PayPal ledger reads inside the capture become source=PAYPAL_LEDGER events."""
        ...

    def judge(self, old: Sequence[MoneyEvent], old_twin: Sequence[MoneyEvent],
              new: Sequence[MoneyEvent], contract: MoneyContract,
              target_plan: TargetPlan) -> Verdict:
        """Tri-Witness verdict for one scenario (design 04 U2). Ledger reads are the
        PAYPAL_LEDGER events inside each list; missing evidence -> UNVERIFIED."""
        ...

    def proof_strength(self, mutants: Sequence[Mutant], runs: MutantRuns) -> ProofStrength:
        """score = killed / (total - equivalent_dropped) (design 04)."""
        ...

    def heal_decide(self, graft_id: str, stage_pct: int, events: Sequence[GuardEvent],
                    hard_stops: Sequence[str] = ()) -> HealDecision:
        """Go-live decision for one stage (design 05 H2, Beta-Binomial posterior)."""
        ...

    def recipe_confidence(self, passes: int, fails: int) -> float:
        """Mean of Beta(passes + 1, fails + 1)."""
        ...

    def verify_certificate(self, certificate: Certificate) -> CertificateVerifyResult:
        """Re-check signature, transparency-log entry, ledger chain, PayPal evidence."""
        ...


@runtime_checkable
class PayPalClient(Protocol):
    """Raw access to the PayPal sandbox (or the stand-in sandbox). Returns raw responses
    so the traffic recorder sees exactly what the shop would see."""

    def nvp(self, method: str, params: Mapping[str, str]) -> Mapping[str, str]: ...

    def rest(self, method: str, path: str, body: Mapping | None = None,
             headers: Mapping[str, str] | None = None) -> tuple[int, Mapping]: ...
