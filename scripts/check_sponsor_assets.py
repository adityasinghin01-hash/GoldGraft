"""Offline checks for the sponsor preparation assets. No vendor or provider calls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPONSORS = ROOT / "tools/sponsors"
ALLOWED_LOCAL = {"GET /__lab/health", "GET /", "GET /config.php", "POST /api/create-payment.php"}


def validate_local_collection(collection):
    items = collection.get("item", [])
    if len(items) != 5:
        raise ValueError("five_local_checks_required")
    for item in items:
        request = item["request"]
        url = request["url"]
        if not isinstance(url, str) or not url.startswith("{{base_url}}/") or "?" in url:
            raise ValueError("only_fixed_local_urls_allowed")
        if request["method"] + " " + url[len("{{base_url}}") :] not in ALLOWED_LOCAL:
            raise ValueError("unsupported_local_request")
        for header in request.get("header", []):
            if header["key"] == "X-GoldGraft-Lab-Key" and header["value"] != "{{lab_key}}":
                raise ValueError("private_header_value_not_allowed")
        for event in item.get("event", []):
            script = "\n".join(event["script"]["exec"])
            if event["listen"] != "test" or any(
                word in script for word in ["sendRequest", "require(", "eval("]
            ):
                raise ValueError("extra_network_or_dynamic_script_not_allowed")


def validate_scope(scenarios, payment_plan, kernel_plan):
    ids = [s["id"] for s in scenarios]
    if len(ids) != 14 or len(set(ids)) != 14:
        raise ValueError("original_fourteen_scope_required")
    planned = payment_plan["item"]
    if [p["name"].split(" ", 1)[0] for p in planned] != ids or any(
        p.get("item") or "request" in p for p in planned
    ):
        raise ValueError("payment_plan_must_be_same_fourteen_nonexecutable_folders")
    if kernel_plan["scenario_ids"] != ids or [s["id"] for s in kernel_plan["scenarios"]] != ids:
        raise ValueError("kernel_scenario_scope_changed")
    if (
        kernel_plan["permitted_external_sessions"] != 0
        or kernel_plan["guarded_browser_profile_qualified"] is not False
    ):
        raise ValueError("unqualified_kernel_session_claim")


def main():
    collection = json.loads(
        (SPONSORS / "postman/offline-shop.postman_collection.json").read_text(encoding="utf-8")
    )
    validate_local_collection(collection)
    scenarios = json.loads(
        (ROOT / "pieces/shops/legacy-php-shop/phase1/scenarios.json").read_text()
    )["scenarios"]
    plan = json.loads(
        (SPONSORS / "postman/payment-plan.postman_collection.json").read_text(encoding="utf-8")
    )
    kernel = json.loads((SPONSORS / "kernel/scenario-plan.json").read_text(encoding="utf-8"))
    validate_scope(scenarios, plan, kernel)
    environment = json.loads(
        (SPONSORS / "postman/empty.postman_environment.json").read_text(encoding="utf-8")
    )
    if any(v["value"] for v in environment["values"]):
        raise ValueError("environment_template_must_be_empty")
    print(
        json.dumps(
            {
                "status": "PASS",
                "evidence": "OFFLINE_ASSET_VALIDATION",
                "scenario_count": 14,
                "offline_requests": len(collection["item"]),
                "external_sessions": 0,
                "provider_calls": 0,
                "live_sponsor_integrations_qualified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
