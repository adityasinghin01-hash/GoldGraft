"""Python composition port for existing published API models; no new wire formats."""

from typing import Protocol

from .api import CmelView, Graft, ProofView, ScenarioList
from .ledger import LedgerEntry


class FixtureRunViews(Protocol):
    """Explicit offline fixture scope implemented by repository-level composition."""

    shop_id: str
    graft_id: str

    def start(self, key: str, request: dict) -> Graft: ...
    def graft(self) -> Graft: ...
    def scenarios(self) -> ScenarioList: ...
    def cmel(self, scenario_id: str) -> CmelView: ...
    def proof(self) -> ProofView: ...
    def events(self, after: int = 0) -> list[LedgerEntry]: ...
