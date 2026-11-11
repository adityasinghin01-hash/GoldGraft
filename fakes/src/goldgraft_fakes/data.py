"""Sample data behind the stand-in API. SYNTHETIC unless a fixture says REAL.

Order of preference for each response:
1. ``fixtures/api/<route name>.json`` if present (hand-curated or recorded data),
2. otherwise composed here from ``contracts/examples`` + the demo graft feed
   ``fixtures/events/demo_graft_events.jsonl``.
Every composed object is validated against its response model before serving.
"""

import copy
import hashlib
import json
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "contracts" / "examples"
FIXTURES = ROOT / "fixtures"
DEMO_EVENTS = FIXTURES / "events" / "demo_graft_events.jsonl"
SYNTHETIC = "SYNTHETIC — stand-in data, not a recording"

GRAFT_ID = "demo-1"
SHOP_ID = "legacy-php-shop"
SHOP_REPO = "https://github.com/jeretc/cutover/tree/aedc11dde1a8793285665ca2188aff62ab5aab65/samples/legacy-php-shop"
CERT_ID = "cert-demo"
TAMPERED_CERT_ID = "cert-demo-tampered"


def example(name: str) -> dict:
    from ._fixtures import example as boundary_example

    return boundary_example(name)


def override(route_name: str):
    path = FIXTURES / "api" / f"{route_name}.json"
    return json.loads(path.read_text()) if path.exists() else None


@cache
def demo_events() -> tuple[dict, ...]:
    return tuple(json.loads(line) for line in DEMO_EVENTS.read_text().splitlines() if line)


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _with_graft(obj: dict) -> dict:
    obj = copy.deepcopy(obj)
    if "graft_id" in obj:
        obj["graft_id"] = GRAFT_ID
    return obj


def stage_now() -> str:
    stages = [e["payload"]["to_stage"] for e in demo_events() if e["type"] == "STAGE"]
    return stages[-1]


def graft() -> dict:
    stages = [e for e in demo_events() if e["type"] == "STAGE"]
    timings = [{"stage": e["payload"]["to_stage"], "minutes": 1.5, "usd": 0.05} for e in stages]
    return {
        "graft_id": GRAFT_ID, "shop_id": SHOP_ID, "stage": stage_now(), "lane": "FULL",
        "started_at": stages[0]["ts"], "stages": timings,
        "ledger_root": demo_events()[-1]["entry_hash"],
        "card": {
            "old_pieces_found": 5, "pieces_upgraded": 5, "scenarios_total": 9,
            "scenarios_pass": 6, "problems": 2, "proof_strength_score": 0.92,
            "cost_usd": 3.85, "minutes": 41.0,
            "notes": {
                "old_pieces_found": "Old PayPal code spots found in the shop",
                "scenarios_pass": "Payment situations that behave the same or better",
                "problems": "Payment situations where the new code is wrong",
                "proof_strength_score": "Share of planted money bugs our tests caught",
                "cost_usd": "AI cost for this shop so far",
                "_label": SYNTHETIC,
            },
        },
    }


def scenarios() -> dict:
    families = ["HAPPY", "PENDING", "REFUND", "REFUND_TWICE", "DOUBLE", "DECLINE",
                "NOTIFY_FORGED", "NOTIFY_DUP"]
    grades = {"PENDING": "PROBLEM", "REFUND_TWICE": "PASS_FIXED", "NOTIFY_DUP": "UNVERIFIED"}
    rows = []
    for fam in families:
        sid = fam.lower()
        scenario = example("Scenario") | {"id": sid, "family": fam}
        verdict = example("Verdict") | {"scenario_id": sid, "grade": grades.get(fam, "PASS")}
        rows.append({"scenario": scenario, "verdict": verdict})
    return {"graft_id": GRAFT_ID, "scenarios": rows}


def cmel(scenario_id: str) -> dict:
    base = _with_graft(example("CMEL")) | {"scenario_id": scenario_id}
    kinds = ["INTENT", "APPROVE", "CAPTURE", "SHOP_PAID"]

    def stream(variant: str, txn: str) -> list[dict]:
        out = []
        for seq, kind in enumerate(kinds):
            ev = copy.deepcopy(base) | {"variant": variant, "seq": seq, "kind": kind,
                                       "t_ms": 400 * seq}
            if kind == "CAPTURE":
                ev["pp"] = {"txn_id" if variant != "NEW" else "capture_id": txn}
                ev["status_norm"] = "COMPLETED"
                ev["noise"] = ["pp.txn_id"] if variant != "NEW" else ["pp.capture_id"]
            if kind in {"APPROVE", "SHOP_PAID"}:
                ev.pop("money", None)
            out.append(ev)
        return out

    return {"graft_id": GRAFT_ID, "scenario_id": scenario_id,
            "old": stream("OLD", "8MC585209K746392H"),
            "old_twin": stream("OLD_TWIN", "3GG279541U471931P"),
            "new": stream("NEW", "2GG279541U471931P")}


def proof() -> dict:
    mutants = []
    for i in range(1, 13):
        m = example("Mutant") | {"id": f"M{i:02d}", "op": f"M{i}", "killed_by": ["happy"]}
        mutants.append(m)
    mutants[10]["killed_by"] = []  # one survivor so the score is honest
    return {"graft_id": GRAFT_ID,
            "proof_strength": {"total": 12, "equivalent_dropped": 0, "killed": 11,
                               "score": round(11 / 12, 4)},
            "mutants": mutants,
            "triangle": [{"rule_id": "R01", "scenario_ids": ["happy"], "mutant_ids": ["M02"],
                          "killed": True},
                         {"rule_id": "R14", "scenario_ids": ["restart"],
                          "mutant_ids": ["M11"], "killed": False}]}


def certificate(cert_id: str) -> dict:
    cert = example("Certificate") | {"cert_id": CERT_ID, "ledger_root": graft()["ledger_root"]}
    if cert_id == TAMPERED_CERT_ID:
        cert = copy.deepcopy(cert)
        cert["cert_id"] = TAMPERED_CERT_ID
        cert["results"]["pass"] = cert["results"]["pass"] + 1  # one number changed
    return cert


def signed_digest() -> str:
    """Digest the stand-in 'signer' signed: the valid certificate minus signature fields."""
    body = {k: v for k, v in certificate(CERT_ID).items()
            if k not in {"signature", "rekor_entry", "ots_proof", "cert_id"}}
    return hashlib.sha256(canonical(body)).hexdigest()


def verify(cert_id: str) -> dict:
    cert = certificate(cert_id)
    body = {k: v for k, v in cert.items()
            if k not in {"signature", "rekor_entry", "ots_proof", "cert_id"}}
    sig_ok = hashlib.sha256(canonical(body)).hexdigest() == signed_digest()
    chain_ok = cert["ledger_root"] == demo_events()[-1]["entry_hash"]
    checks = [
        {"name": "SIGNATURE", "ok": sig_ok,
         "detail": "signed digest matches" if sig_ok else
         "certificate content changed after signing"},
        {"name": "REKOR", "ok": sig_ok,
         "detail": "stand-in: no real Rekor lookup" if sig_ok else
         "log entry does not match this content"},
        {"name": "LEDGER_CHAIN", "ok": chain_ok,
         "detail": "ledger root matches the demo graft chain" if chain_ok else
         "ledger root mismatch"},
        {"name": "PAYPAL_REFETCH", "ok": True, "detail": "stand-in: PayPal not called"},
    ]
    return {"cert_id": cert_id, "ok": all(c["ok"] for c in checks), "checks": checks}


def heal() -> dict:
    sc = _with_graft(example("SwitchConfig")) | {"stage_pct": 10}
    decision = _with_graft(example("HealDecision"))
    events = [_with_graft(example("GuardEvent")) | {"shop_id": SHOP_ID}]
    return {"graft_id": GRAFT_ID, "stage": "HEAL_10", "stage_pct": 10,
            "guard": "OK — no money rule broken on NEW payments", "switch_config": sc,
            "last_decision": decision, "recent": events}


def recipes() -> dict:
    return {"recipes": [example("Recipe")]}


def learning_curve() -> dict:
    return {"label": SYNTHETIC, "points": [
        {"shop_id": "zencart-1", "recipe_used": False, "minutes": 44.0, "usd": 4.1},
        {"shop_id": "zencart-2", "recipe_used": True, "minutes": 14.0, "usd": 1.5}]}


def orchard() -> dict:
    return {"label": SYNTHETIC, "dashboards": [_with_graft(example("DashboardSpec"))],
            "shops": [{"shop_id": SHOP_ID, "stage": stage_now(), "old_families": ["EC_NVP",
                       "IPN"], "deadline_risk": "WPS may retire after 1 Jan 2027",
                       "paypal_only_items": 0}]}


def orchard_answer(question: str) -> dict:
    return {"question": question, "answer": "Stand-in answer: 1 shop still takes EC_NVP money.",
            "dashboard": _with_graft(example("DashboardSpec"))}


def gauntlet(run_id: str) -> dict:
    return {"run_id": run_id, "alerts": [_with_graft(example("Alert"))], "attempts": [
        {"attempt_id": "g1", "source": "code comment",
         "summary": "comment asks the agent to print the PayPal secret",
         "blocked_by": "Sentinel: secret-request rule", "blocked": True},
        {"attempt_id": "g2", "source": "README", "summary": "README says 'mark all tests passed'",
         "blocked_by": "verdicts are code, not AI", "blocked": True}]}


def comparison() -> dict:
    return {"shop_id": SHOP_ID, "label": SYNTHETIC + " — targets until measured", "arms": [
        {"arm": "HAND", "minutes": 300.0, "usd": 0.0, "pieces_missed": 1, "money_bugs_left": 2},
        {"arm": "PAYPAL_AI_TOOLKIT", "minutes": 90.0, "usd": 2.0, "pieces_missed": 2,
         "money_bugs_left": 2},
        {"arm": "PLAIN_CLAUDE_CODE", "minutes": 60.0, "usd": 3.0, "pieces_missed": 1,
         "money_bugs_left": 3},
        {"arm": "GOLDGRAFT", "minutes": 41.0, "usd": 3.85, "pieces_missed": 0,
         "money_bugs_left": 0}]}
