"""Read-only evaluation of reference-shop sandbox recordings; no provider calls.

Internal reports are not new wire contracts. Hashes detect drift, not collector
identity. The connected local host seals its CheckResult/1 after checking bytes.
Original recording run ids remain intact, bound by exact candidate input digests.
"""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from goldgraft_contracts.registry import validate

from integration.shop_sandbox import REAL_SCENARIOS, amount_minor, recorded_resources
from pieces.backend.payment_broker import REST_SANDBOX

PAYMENT_CHECK = "payment:shop-checkout-paypal-sandbox"


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _checkout(raw):
    """Require an actual NEW shop driver, sandbox-only exchanges and approval first."""
    validate("RawCapture/1", raw)
    _require(raw["variant"] == "NEW", "NEW recording required")
    browser_paths = {
        urlsplit(ex["url"]).path
        for ex in raw["exchanges"]
        if ex["direction"] == "BROWSER_TO_SHOP" and ex["method"] == "POST"
    }
    _require(
        {"/api/create-payment.php", "/api/execute-payment.php"} <= browser_paths,
        "shop checkout observations missing",
    )
    approved = set()
    created = set()
    negative = False
    resources = recorded_resources(raw)
    _require(
        not any(ex["direction"] == "PAYPAL_NOTIFY_TO_SHOP" for ex in raw["exchanges"]),
        "simulated notification in real recording",
    )
    for ex in raw["exchanges"]:
        if ex["direction"] not in {"SHOP_TO_PAYPAL", "PAYPAL_TO_SHOP"}:
            continue
        _require(ex["url"].startswith(REST_SANDBOX + "/"), "non-sandbox provider URL")
        path = urlsplit(ex["url"]).path
        body = ex.get("body_json") or {}
        if ex["direction"] == "SHOP_TO_PAYPAL":
            if ex["method"] == "POST" and path.endswith("/capture"):
                _require(path.split("/")[-2] in approved, "capture before recorded approval")
            continue
        status = ex.get("status", 0)
        if ex["method"] == "POST" and path == "/v2/checkout/orders" and status in {200, 201}:
            _require(body.get("id"), "missing create order id")
            created.add(body["id"])
        if ex["method"] == "GET" and path.startswith("/v2/checkout/orders/"):
            oid = path.rsplit("/", 1)[-1]
            if status == 200 and body.get("status") == "APPROVED":
                _require(body.get("id") == oid and oid in created, "approval order mismatch")
                approved.add(oid)
        if path.endswith("/capture") and ex["method"] == "POST":
            _require(path.split("/")[-2] in approved, "capture before recorded approval")
            negative |= status == 422 and any(
                d.get("issue") == "INSTRUMENT_DECLINED" for d in body.get("details", [])
            )
    _require(len(created) == 1 and approved == created, "missing created/approved order")
    if raw["scenario_id"] == "DECLINE":
        _require(negative and not resources, "decline negative response missing or money moved")
        _require(
            any(
                "INSTRUMENT_DECLINED" in ex.get("headers", {}).get("PayPal-Mock-Response", "")
                for ex in raw["exchanges"]
                if ex["direction"] == "SHOP_TO_PAYPAL"
            ),
            "negative test header missing",
        )
    else:
        _require(any(kind == "capture" for kind, _ in resources), "no recorded capture")
    if raw["scenario_id"] in {"REFUND", "REFUND_TWICE"}:
        _require(any(kind == "refund" for kind, _ in resources), "no recorded refund")
    return resources


def shop_sandbox_evidence(directory, candidate_dir):
    """Return verified/missing/failed without trusting report success declarations."""
    if directory is None:
        return {"state": "missing", "reason": "MISSING", "evidence_refs": []}
    directory, candidate_dir = Path(directory), Path(candidate_dir)
    if not (directory / "REPORT.json").exists():
        return {"state": "missing", "reason": "MISSING", "evidence_refs": []}
    refs = []

    def read(name, expected):
        data = (directory / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        _require(digest == expected, "sandbox recording digest mismatch")
        refs.append(f"local:shop-sandbox/{name}#sha256:{digest}")
        return json.loads(data)

    try:
        report_bytes = (directory / "REPORT.json").read_bytes()
        report = json.loads(report_bytes)
        refs.append(
            "local:shop-sandbox/REPORT.json#sha256:" + hashlib.sha256(report_bytes).hexdigest()
        )
        _require(
            report["evidence_class"] == "real_provider"
            and report["provider"] == "paypal_sandbox"
            and report["real_money"] is False,
            "sandbox profile mismatch",
        )
        _require(report["status"] == "RECORDED", "sandbox run failed or incomplete")
        for name, key in (("CHANGES.json", "changes_sha256"), ("OUTPUTS.json", "outputs_sha256")):
            _require(
                hashlib.sha256((candidate_dir / name).read_bytes()).hexdigest() == report[key],
                "sandbox candidate input drift",
            )
        _require(report["graft_id"] == candidate_dir.name, "sandbox graft mismatch")
        requested = report["requested_scenarios"]
        _require(requested and len(requested) == len(set(requested)), "scenario inventory missing")
        real = set(requested) & REAL_SCENARIOS
        _require(real, "no real NEW scenarios")
        rows = {r["scenario"]: r for r in report["scenarios"]}
        _require(
            len(rows) == len(report["scenarios"]) and set(rows) == set(requested),
            "incomplete scenario inventory",
        )
        reads = read("REFETCH.json", report["refetch_sha256"])
        _require(set(reads) == real, "re-fetch scenario inventory mismatch")
        total_captures = 0
        for scenario in sorted(real):
            row = rows[scenario]
            expected_class = (
                "real_provider_negative_test" if scenario == "DECLINE" else "real_provider"
            )
            _require(
                row["status"] == "RECORDED" and row["variants"]["NEW"] == expected_class,
                "NEW scenario was not recorded against real sandbox",
            )
            name = f"{scenario}.NEW.json"
            raw = read(name, report["capture_sha256"][name])
            _require(
                (raw["graft_id"], raw["run_id"], raw["scenario_id"])
                == (report["graft_id"], report["run_id"], scenario),
                "recording subject mismatch",
            )
            resources = _checkout(raw)
            total_captures += sum(kind == "capture" for kind, _ in resources)
            fetched = {(r["kind"], r["id"]): r for r in reads[scenario]}
            _require(
                len(fetched) == len(reads[scenario]) and fetched.keys() == resources.keys(),
                "missing/extra/duplicate resource re-fetch",
            )
            for key, amount in resources.items():
                r = fetched[key]
                _require(
                    "error" not in r
                    and r["evidence_class"] == "real_sandbox"
                    and r["simulated"] is False
                    and r["status_code"] == 200,
                    "re-fetch failed or simulated",
                )
                body = r["body"]
                _require(
                    body.get("id") == key[1] and r["correlation_id"] == key[1],
                    "re-fetch resource id mismatch",
                )
                _require(body.get("status") == "COMPLETED", "re-fetch status is not COMPLETED")
                _require(
                    amount_minor(body.get("amount")) == amount, "re-fetch amount/currency mismatch"
                )
        _require(
            total_captures > 0, "no captured payment; negative tests alone do not qualify checkout"
        )
        return {"state": "verified", "reason": "VERIFIED", "evidence_refs": refs}
    except Exception as exc:
        # Validation diagnostics are fixed local messages; never echo arbitrary body data.
        reason = str(exc) if type(exc) is ValueError else type(exc).__name__
        return {"state": "failed", "reason": reason, "evidence_refs": refs}
