"""The control-plane API as DATA: one row per endpoint in docs/design/07_FRONTEND_API.md.

The stand-in API (fakes) and the real backend both register routes FROM this
table, so neither can drift from the contract. Rules for every implementation:

* Writes (``needs_idempotency_key``) require an ``Idempotency-Key`` header:
  same key + same body -> same response; same key + different body -> 409 problem.
* Errors are RFC 7807 ``application/problem+json`` (``api.Problem``).
* Webhooks are not keyed; they are signature-verified and de-duplicated by the
  sender's delivery id header (``dedupe_header``).
* ``sse`` routes stream ``text/event-stream``: ``id: <ledger seq>``,
  ``event: <name>``, ``data: <json>``; ``Last-Event-ID`` resumes after that seq.
  ``GET /heal/{graft_id}`` returns JSON by default and streams when the client
  sends ``Accept: text/event-stream``.
* ``secrets_in_request`` routes must never echo, log or store secret values;
  only a ``secrets_ref`` (vault path) is kept.
"""

from dataclasses import dataclass, field

from . import api
from .common import Format
from .delivery import SwitchConfig
from .ledger import LedgerEntry
from .proof import Certificate
from .runner import GuardEvent
from .survey import Connection, ProbeResult, RootMap


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    name: str
    summary: str
    response: type[Format] | None
    request: type[Format] | None = None
    needs_idempotency_key: bool = False
    sse: bool = False
    sse_event: str | None = None
    secrets_in_request: bool = False
    demo_only: bool = False
    public: bool = False
    dedupe_header: str | None = None
    signature_headers: tuple[str, ...] = ()
    query: tuple[str, ...] = ()
    screens: tuple[str, ...] = field(default_factory=tuple)


PAYPAL_WEBHOOK_HEADERS = (
    "PAYPAL-TRANSMISSION-ID", "PAYPAL-TRANSMISSION-TIME", "PAYPAL-TRANSMISSION-SIG",
    "PAYPAL-CERT-URL", "PAYPAL-AUTH-ALGO",
)

ROUTES: tuple[Route, ...] = (
    Route("POST", "/probe", "probe", "Quick scan of a repo or site URL (no keys)",
          ProbeResult, api.ProbeRequest, public=True, screens=("S0",)),
    Route("POST", "/shops", "create_shop", "Create a shop", api.Shop, api.ShopCreate,
          needs_idempotency_key=True, screens=("S1",)),
    Route("POST", "/shops/{shop_id}/connect", "connect_shop",
          "Store sandbox keys in the vault and run connection checks", Connection,
          api.ConnectRequest, needs_idempotency_key=True, secrets_in_request=True,
          screens=("S1",)),
    Route("POST", "/shops/{shop_id}/graft", "start_graft", "Start the Graft Cycle",
          api.Graft, api.StartGraftRequest, needs_idempotency_key=True, screens=("S1", "S2")),
    Route("GET", "/grafts/{graft_id}", "get_graft", "Graft state + Graft Card", api.Graft,
          screens=("S2",)),
    Route("GET", "/grafts/{graft_id}/events", "graft_events",
          "Live ledger feed for one graft (SSE)", LedgerEntry, sse=True,
          sse_event="ledger", screens=("S2",)),
    Route("GET", "/grafts/{graft_id}/rootmap", "get_rootmap", "Root Map", RootMap,
          screens=("S3",)),
    Route("GET", "/grafts/{graft_id}/scenarios", "get_scenarios", "Scenarios + verdicts",
          api.ScenarioList, screens=("S4",)),
    Route("GET", "/grafts/{graft_id}/cmel", "get_cmel",
          "Money events OLD / OLD_TWIN / NEW for one scenario", api.CmelView,
          query=("scenario",), screens=("S4",)),
    Route("GET", "/grafts/{graft_id}/proof", "get_proof", "Proof strength + triangle",
          api.ProofView, screens=("S5",)),
    Route("GET", "/certificates/{cert_id}", "get_certificate", "Public Graft Certificate",
          Certificate, public=True, screens=("S6",)),
    Route("POST", "/certificates/{cert_id}/verify", "verify_certificate",
          "Re-verify signature, Rekor entry, ledger chain and PayPal evidence",
          api.CertificateVerifyResult, public=True, screens=("S6",)),
    Route("GET", "/heal/{graft_id}", "get_heal",
          "Go-live state (JSON) or live go-live feed (SSE)", api.HealState, sse=True,
          sse_event="heal", screens=("S7",)),
    Route("POST", "/heal/{graft_id}/inject-fault", "inject_fault",
          "Demo only: flip one planted bug on the NEW path", api.InjectFaultResult,
          api.InjectFaultRequest, needs_idempotency_key=True, demo_only=True,
          screens=("S7",)),
    Route("GET", "/switch/config/{graft_id}", "get_switch_config",
          "Signed SwitchConfig for shop switch libraries", SwitchConfig),
    Route("POST", "/guard/event", "guard_event", "Money event from a shop switch library",
          api.Ack, GuardEvent, needs_idempotency_key=True),
    Route("POST", "/pp/webhook/{graft_id}", "paypal_webhook", "PayPal webhook receiver",
          api.Ack, None, dedupe_header="PAYPAL-TRANSMISSION-ID",
          signature_headers=PAYPAL_WEBHOOK_HEADERS),
    Route("POST", "/gh/webhook", "github_webhook", "GitHub App webhook receiver", api.Ack,
          None, dedupe_header="X-GitHub-Delivery",
          signature_headers=("X-Hub-Signature-256", "X-GitHub-Event", "X-GitHub-Delivery")),
    Route("GET", "/recipes", "list_recipes", "Scion Bank recipes", api.RecipeList,
          screens=("S8",)),
    Route("GET", "/learning-curve", "learning_curve", "Minutes + $ per shop over time",
          api.LearningCurve, screens=("S8",)),
    Route("GET", "/orchard", "get_orchard", "PayPal-team fleet view", api.OrchardView,
          screens=("S9",)),
    Route("POST", "/orchard/ask", "orchard_ask", "Ask the Orchard Analyst a fleet question",
          api.OrchardAnswer, api.OrchardAsk, needs_idempotency_key=True, screens=("S9",)),
    Route("GET", "/security/gauntlet/{run_id}", "get_gauntlet", "Injection Gauntlet replay",
          api.GauntletRun, screens=("S10",)),
    Route("GET", "/comparison", "get_comparison", "Four-arm comparison", api.Comparison,
          screens=("S11",)),
)


def route(name: str) -> Route:
    for item in ROUTES:
        if item.name == name:
            return item
    raise KeyError(name)
