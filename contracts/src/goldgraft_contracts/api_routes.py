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
from typing import Literal

from . import api
from . import connection_control as p5
from . import lifecycle as lc
from .certificate_v2 import CertificateV2, CertificateVerification
from .common import Format
from .delivery import SwitchConfig
from .ledger import LedgerEntry
from .proof import Certificate
from .runner import GuardEvent
from .survey import Connection, ProbeResult, RootMap
from .work_package import ChunkReceipt, UploadSession


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


# Additive v2 contract table. Legacy stand-in/backend handlers continue to consume
# ROUTES only; declaring a v2 route does not install an implementation.


@dataclass(frozen=True)
class Plan5Route:
    method: Literal["GET", "POST"]
    path: str
    name: str
    response: tuple[type[Format], ...]
    request: type[Format] | None = None
    success_status: int = 200
    auth: Literal["session", "draft", "session_and_draft", "service", "public_projection"] = (
        "session"
    )
    request_media: Literal["application/json", "multipart/form-data"] = "application/json"
    sse: bool = False
    query: tuple[str, ...] = ()

    @property
    def csrf(self) -> bool:
        return self.method == "POST" and self.auth != "service"

    @property
    def needs_idempotency_key(self) -> bool:
        return self.method == "POST"


C = "/v2/connection-cases"
R = Plan5Route
PLAN5_ROUTES = (
    R(
        "POST",
        "/v2/connection-drafts",
        "create_draft",
        (p5.DraftCase,),
        p5.CreateDraft,
        201,
        "draft",
    ),
    R(
        "POST",
        "/v2/connection-drafts/{draft_id}/claim",
        "claim_draft",
        (p5.ConnectionCase,),
        p5.ClaimDraft,
        200,
        "session_and_draft",
    ),
    R("POST", C, "create_case", (p5.ConnectionCase,), p5.CreateCase, 201),
    R("GET", C, "list_cases", (p5.CaseList,), query=("cursor", "limit")),
    R("GET", C + "/{case_id}", "get_case", (p5.ConnectionCase,)),
    R("GET", C + "/{case_id}/view", "case_view", (p5.CaseView,)),
    R(
        "POST",
        C + "/{case_id}/provider-intents",
        "provider_intent",
        (p5.ProviderIntent,),
        p5.CreateProviderIntent,
        201,
    ),
    R(
        "POST",
        C + "/{case_id}/invitations",
        "controller_invitation",
        (p5.ControllerInvitation,),
        p5.CreateInvitation,
        201,
    ),
    R(
        "POST",
        C + "/{case_id}/source-uploads",
        "create_upload",
        (UploadSession,),
        p5.CreateUploadRequest,
        201,
    ),
    R("GET", C + "/{case_id}/source-uploads/{upload_id}", "upload_status", (UploadSession,)),
    R(
        "POST",
        C + "/{case_id}/source-uploads/{upload_id}/chunks",
        "upload_chunk",
        (ChunkReceipt,),
        p5.ChunkUploadRequest,
        request_media="multipart/form-data",
    ),
    R(
        "POST",
        C + "/{case_id}/source-uploads/{upload_id}/finalise",
        "finalise_upload",
        (UploadSession,),
        p5.FinaliseUploadRequest,
    ),
    R(
        "POST",
        C + "/{case_id}/source-uploads/{upload_id}/cancel",
        "cancel_upload",
        (UploadSession,),
        p5.CancelUploadRequest,
    ),
    R(
        "POST",
        C + "/{case_id}/action-intents",
        "create_action_intent",
        (p5.ActionIntent,),
        p5.CreateActionIntent,
        201,
    ),
    R(
        "POST",
        C + "/{case_id}/actions",
        "start_work",
        (p5.WorkAcceptance, p5.WorkCancellation),
        p5.StartWorkRequest,
        202,
    ),
    R("GET", C + "/{case_id}/actions/{action_id}", "action_status", (p5.ActionStatusView,)),
    R(
        "POST",
        C + "/{case_id}/actions/{action_id}/cancellation",
        "cancel_work",
        (p5.WorkCancellation,),
        p5.CancelWorkRequest,
        202,
    ),
    R(
        "POST",
        C + "/{case_id}/lifecycle-runs/{run_id}/resume",
        "resume_run",
        (lc.LifecycleRun,),
        p5.ResumeRunRequest,
        202,
    ),
    R(
        "GET",
        C + "/{case_id}/review-bundles/{bundle_id}",
        "private_review",
        (p5.PrivateReviewView,),
    ),
    R(
        "POST",
        C + "/{case_id}/apply-approvals",
        "issue_apply_approval",
        (lc.ApplyApproval,),
        p5.IssueApplyApproval,
        201,
    ),
    R("GET", C + "/{case_id}/events", "case_events", (p5.CaseEvent,), sse=True, query=("after",)),
    R(
        "GET",
        "/v2/public-proof/{public_id}",
        "public_proof",
        (p5.PublicProofView,),
        auth="public_projection",
    ),
    R(
        "POST",
        "/v2/worker-operations",
        "worker_operation",
        (p5.CollectorAcceptance,),
        p5.WorkerOperation,
        201,
        "service",
    ),
    R("GET", C + "/{case_id}/certificates/{cert_id}", "private_certificate", (CertificateV2,)),
    R(
        "GET",
        C + "/{case_id}/certificates/{cert_id}/verification",
        "private_certificate_verification",
        (CertificateVerification,),
    ),
)


def plan5_route(name: str) -> Plan5Route:
    for item in PLAN5_ROUTES:
        if item.name == name:
            return item
    raise KeyError(name)


def service_route(name: str, *, mode: Literal["service", "legacy_demo"]) -> Route | Plan5Route:
    if mode == "legacy_demo":
        return route(name)
    if mode != "service":
        raise ValueError("unknown service mode")
    if any(r.name == name for r in ROUTES):
        raise ValueError("legacy demo route cannot enter v2 service")
    return plan5_route(name)
