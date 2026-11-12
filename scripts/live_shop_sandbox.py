"""Opt-in NEW PHP checkout on real PayPal sandbox; OLD/OLD_TWIN remain simulated.

Writes RawCapture/1 recordings, independent broker GET results and an internal
REPORT.json. Failure preserves partial evidence and stops subsequent scenarios.
No automatic capture/refund retries, notifications, production money or certificate.
"""

import argparse
import hashlib
import json
import uuid
from pathlib import Path

from goldgraft_contracts.registry import validate

from integration.local_shop import SCENARIOS, resolve_php, run_scenario
from integration.shop_sandbox import (
    REAL_SCENARIOS,
    SandboxHeld,
    SandboxProxy,
    refetch_resources,
    require_refetch_results,
)
from integration.shop_sandbox_evidence import shop_sandbox_evidence
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from scripts.live_local_shop_proof import load_candidate
from scripts.live_paypal_sandbox_payment import DEFAULT_ENV_FILE, load_credentials


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_shop_sandbox(
    directory,
    output,
    *,
    authorize_payment=False,
    credentials=None,
    scenarios=("HAPPY", "REFUND", "REFUND_TWICE", "DOUBLE"),
    php="php",
    show_approval=None,
    approval_timeout_s=600,
    poll_s=5,
    transport=None,
    broker_transport=None,
):
    if not authorize_payment:
        raise ValueError("--authorize-sandbox-payment is required")
    if not credentials or not all(
        credentials.get(k)
        for k in (
            "PAYPAL_CLIENT_ID",
            "PAYPAL_CLIENT_SECRET",
        )
    ):
        raise ValueError("sandbox credentials are required")
    scenarios = list(scenarios)
    if (
        not scenarios
        or len(set(scenarios)) != len(scenarios)
        or not set(scenarios) <= set(SCENARIOS)
    ):
        raise ValueError("unsupported, empty or duplicate scenarios")
    files, _ = load_candidate(directory)
    php = str(resolve_php(php))
    output.mkdir(parents=True, exist_ok=False)
    custody = CustodyBroker()
    secret_ref = custody.store_credentials(
        "shop-sandbox",
        {
            "paypal_client_id": credentials["PAYPAL_CLIENT_ID"],
            "paypal_client_secret": credentials["PAYPAL_CLIENT_SECRET"],
        },
    ).to_uri()
    # This broker has read authority only; all payment writes come from the PHP shop.
    broker = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        database=str(output / "refetch-journal.sqlite"),
        authorize=lambda _g, op, *_: op in {"get_order", "get_capture", "get_refund"},
        **({"transport": broker_transport} if broker_transport else {}),
    )
    run_id = directory.name + "-shop-sandbox-" + uuid.uuid4().hex[:12]
    report = {
        "run_id": run_id,
        "graft_id": directory.name,
        "evidence_class": "real_provider",
        "provider": "paypal_sandbox",
        "real_money": False,
        "changes_sha256": sha(directory / "CHANGES.json"),
        "outputs_sha256": sha(directory / "OUTPUTS.json"),
        "requested_scenarios": scenarios,
        "scenarios": [],
        "capture_sha256": {},
        "status": "HELD",
        "model_calls": 0,
        "simulated_only": {
            s: "requires deterministic pending/notification/parity stand-in"
            for s in SCENARIOS
            if s not in REAL_SCENARIOS
        },
        "holds": [
            "No real webhook listener; notifications are not claimed",
            "No isolation, merchant delivery, production payment or certificate qualification",
        ],
    }
    refetches = {}

    def save_capture(raw, name):
        validate("RawCapture/1", raw)
        path = output / name
        path.write_text(json.dumps(raw, indent=2) + "\n")
        report["capture_sha256"][name] = sha(path)

    try:
        for scenario in scenarios:
            row = {"scenario": scenario, "variants": {}, "status": "RUNNING"}
            report["scenarios"].append(row)
            for variant in ("OLD", "OLD_TWIN", "NEW"):
                real = variant == "NEW" and scenario in REAL_SCENARIOS
                row["variants"][variant] = (
                    "real_provider_negative_test"
                    if real and scenario == "DECLINE"
                    else "real_provider"
                    if real
                    else "simulated_paypal"
                )
                proxy = None
                try:
                    if real:
                        proxy = SandboxProxy(
                            scenario,
                            credentials=credentials,
                            authorize_payment=authorize_payment,
                            transport=transport,
                            show_approval=show_approval,
                            approval_timeout_s=approval_timeout_s,
                            poll_s=poll_s,
                        )
                    raw = run_scenario(
                        scenario,
                        variant,
                        files if variant == "NEW" else {},
                        graft_id=directory.name,
                        run_id=run_id,
                        php=php,
                        **({"paypal": proxy} if proxy else {}),
                    )
                    save_capture(raw, f"{scenario}.{variant}.json")
                except Exception as exc:
                    row.update(status="FAILED", error=type(exc).__name__)
                    if isinstance(exc, SandboxHeld) or type(exc) is TimeoutError:
                        row["detail"] = str(exc)
                    if proxy is not None:
                        # The provider response may already have taken effect. Preserve it.
                        raw = {
                            "graft_id": directory.name,
                            "run_id": run_id,
                            "variant": variant,
                            "scenario_id": scenario,
                            "exchanges": proxy.recorder.exchanges,
                        }
                        save_capture(raw, f"{scenario}.{variant}.json")
                    raise
                finally:
                    if proxy is not None:
                        proxy.close()
                        raw = {"exchanges": proxy.recorder.exchanges}
                        refetches[scenario] = proxy.scrub(
                            refetch_resources(
                                raw, broker, secret_ref=secret_ref, graft_id=directory.name
                            )
                        )
                        try:
                            require_refetch_results(raw, refetches[scenario])
                        except SandboxHeld as exc:
                            row.update(status="FAILED", error=type(exc).__name__, detail=str(exc))
                            raise
            row["status"] = "RECORDED"
        report["status"] = "RECORDED"
    except Exception as exc:
        # Safe diagnostics only; bodies are already in sanitized recordings.
        report["error"] = type(exc).__name__
    finally:
        broker.close()
        (output / "REFETCH.json").write_text(json.dumps(refetches, indent=2) + "\n")
        report["refetch_sha256"] = sha(output / "REFETCH.json")
        (output / "REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
        checked = shop_sandbox_evidence(output, directory)
        report["payment_check"] = {k: checked[k] for k in ("state", "reason")}
        (output / "REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-sandbox-payment", action="store_true", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--scenarios", default="HAPPY,REFUND,REFUND_TWICE,DOUBLE")
    parser.add_argument("--approval-timeout", type=float, default=600)
    parser.add_argument("--php", default="php")
    args = parser.parse_args(argv)
    try:
        report = run_shop_sandbox(
            args.run_dir.resolve(),
            args.output.resolve(),
            authorize_payment=args.authorize_sandbox_payment,
            credentials=load_credentials(args.env_file),
            scenarios=args.scenarios.split(","),
            php=args.php,
            approval_timeout_s=args.approval_timeout,
        )
    except (ValueError, OSError) as exc:
        parser.exit(
            2, f"Sandbox setup held ({type(exc).__name__}); check paths/candidate/credentials\n"
        )
    print(json.dumps(report, indent=2))
    return 0 if report["payment_check"]["state"] == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
