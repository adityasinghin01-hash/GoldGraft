"""Generate synthetic browser boundary fixtures; no frontend or merchant jobs."""

import hashlib
import json
import sys
from pathlib import Path

from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import validate

ROOT = Path(__file__).resolve().parents[1]
MODES = (
    "ready",
    "controller_wait",
    "missing_source",
    "start_response_lost",
    "claimed_no_operation",
    "cancel_before_accept",
    "cancel_pending",
    "event_gap",
    "proof_missing",
    "apply_split_controllers",
    "deploy_unknown_no_id",
    "persistent_config_mismatch",
    "exit_executor_missing",
    "cleanup_pending",
    "synthetic_complete",
)
LABEL = "Mock mode: showing saved sample data, not a live system."


def ex(schema):
    return json.loads(
        (ROOT / "contracts/examples" / (schema.replace("/", ".") + ".json")).read_text()
    )


def records(mode):
    view = ex("CaseView/1")
    view.update(
        processing=ex("ProcessingDisclosure/1"),
        readiness=None,
        action=None,
        lifecycle=None,
        pending_action_id=None,
        delivery_ref=None,
        required_actions=[],
    )
    view["case"]["status"] = "checking"
    view["resources"][0].update(label="Synthetic PHP shop", controller_state="approved")
    bundle = {"CaseView/1": view}
    if mode == "ready":
        view["case"]["status"] = "ready"
        view["readiness"] = ex("ConnectionReadiness/1")
        view["required_actions"] = [
            {"kind": "start", "resource_ids": ["source-demo"], "enabled": True, "reason_code": None}
        ]
    elif mode in {"controller_wait", "missing_source"}:
        view["case"]["status"] = (
            "waiting_controller" if mode == "controller_wait" else "setup_needed"
        )
        view["resources"][0].update(
            controller_state="waiting" if mode == "controller_wait" else "unbound",
            source_snapshot_ref=None,
        )
        view["required_actions"] = [
            {
                "kind": "ask_maintainer" if mode == "controller_wait" else "connect_source",
                "resource_ids": ["source-demo"],
                "enabled": True,
                "reason_code": mode.upper(),
            }
        ]
        if mode == "controller_wait":
            bundle["ControllerInvitation/1"] = ex("ControllerInvitation/1")
    else:
        view["case"]["status"] = "accepted"
        status = ex("WorkStatus/1")
        status.update(work_id="work-demo", generation=1, state="queued")
        view["action"] = {"status": status, "acceptance_ref": "fixture:acceptance:" + mode}
        bundle["WorkAcceptance/1"] = ex("WorkAcceptance/1")
        bundle["WorkAcceptance/1"]["work_id"] = "work-demo"
        if mode == "start_response_lost":
            view["pending_action_id"] = status["action_id"]
        elif mode == "claimed_no_operation":
            status["state"] = "provisioning"
            status["evidence_refs"] = []
        elif mode in {"cancel_before_accept", "cancel_pending"}:
            cancellation = ex("WorkCancellation/1")
            cancellation.update(
                work_id="work-demo",
                generation=1,
                state="termination_pending",
                termination_evidence_refs=[],
            )
            status["state"] = "cancellation_pending"
            if mode == "cancel_before_accept":
                cancellation.update(work_id=None, generation=None, state="confirmed")
                status.update(work_id=None, generation=None, state="cancelled")
                view["case"]["status"] = "closed"
                view["action"]["acceptance_ref"] = None
                bundle.pop("WorkAcceptance/1")
            bundle["WorkCancellation/1"] = cancellation
        elif mode == "event_gap":
            event = ex("CaseEvent/1")
            event["sequence"] = view["last_event_seq"] + 2
            event["state_version"] = view["state_version"] + 1
            bundle["CaseEvent/1"] = event
            view["required_actions"] = [
                {
                    "kind": "start",
                    "resource_ids": [],
                    "enabled": False,
                    "reason_code": "STALE_SNAPSHOT",
                }
            ]
        else:
            lifecycle = ex("LifecycleRun/1")
            lifecycle["work_id"] = "work-demo"
            view["lifecycle"] = lifecycle
            if mode in {"proof_missing", "apply_split_controllers"}:
                review = ex("PrivateReviewView/1")
                review["processing"] = view["processing"]
                lifecycle["stage"] = "HELD" if mode == "proof_missing" else "AWAITING_APPLY"
                review["missing"] = [dict(ex("Issue/1"), code="REQUIRED_PROOF_MISSING")]
                if mode == "apply_split_controllers":
                    review["missing"] = [
                        dict(ex("Issue/1"), code="HOST_CONTROLLER_APPROVAL_MISSING")
                    ]
                    slot = review["plan"]["slots"][0]
                    slot["required_controller_ids"] = ["source-controller", "host-controller"]
                    slot["required_authority_refs"] = [
                        "fixture:source-authority",
                        "fixture:host-authority",
                    ]
                    approval = ex("ApprovalSet/1")
                    approval.update(
                        state="missing",
                        required_controller_ids=slot["required_controller_ids"],
                        approval_refs=[],
                    )
                    review["approval_set"] = approval
                else:
                    review["bundle"]["missing_evidence_refs"] = ["fixture:missing-required-proof"]
                review["plan"]["plan_digest"] = content_digest(
                    {k: v for k, v in review["plan"].items() if k != "plan_digest"}
                )
                if review["approval_set"] is not None:
                    review["approval_set"]["plan_digest"] = review["plan"]["plan_digest"]
                bundle["PrivateReviewView/1"] = review
            else:
                delivery = ex("DeliverySnapshot/1")
                view["delivery_ref"] = "fixture:delivery:" + mode
                if mode in {"deploy_unknown_no_id", "persistent_config_mismatch"}:
                    observation = ex("DeploymentObservation/1")
                    observation.update(
                        provider_deploy_id=None, provider_status="unknown", outcome="unknown"
                    )
                    lifecycle["stage"] = "INCIDENT_UNKNOWN"
                    if mode == "persistent_config_mismatch":
                        observation.update(
                            observed_artifact_digest=observation["submitted_artifact_digest"],
                            observed_config_digest=content_digest("wrong-persistent-config"),
                            provider_status="config_mismatch",
                        )
                        lifecycle["stage"] = "OBSERVING"
                    delivery["pending_effect_refs"] = ["fixture:original-effect-unknown"]
                    bundle["DeploymentObservation/1"] = observation
                elif mode == "exit_executor_missing":
                    lifecycle["stage"] = "HELD"
                    delivery["issue"] = dict(
                        ex("Issue/1"), code="INDEPENDENT_EXECUTOR_MISSING", owner_role="GU"
                    )
                else:
                    exit_manifest = ex("ExitManifest/1")
                    if mode == "cleanup_pending":
                        lifecycle["stage"] = "EXITING"
                        exit_manifest.update(outcome="pending")
                        exit_manifest["cleanup_items"][0].update(state="revocation_pending")
                    else:
                        lifecycle["stage"] = "COMPLETE"
                        exit_manifest["cleanup_items"][0]["state"] = "confirmed"
                        bundle["PublicProofView/1"] = ex("PublicProofView/1")
                        bundle["PublicProofView/1"]["limitations"].append(LABEL)
                    bundle["ExitManifest/1"] = exit_manifest
                bundle["DeliverySnapshot/1"] = delivery
    # Scope-only refs/authenticity in all samples remain explicitly synthetic.
    for schema, payload in bundle.items():
        validate(schema, payload)
    return bundle


def main(check=False):
    index_path = ROOT / "fixtures/plan5/index.json"
    index = json.loads(index_path.read_text())
    entries = [row for row in index["entries"] if row.get("generator") != "make_plan5_views"]
    catalog = []
    for mode in MODES:
        rows = []
        for schema, payload in records(mode).items():
            path = ROOT / "fixtures/plan5/frontend" / mode / (schema.replace("/", ".") + ".json")
            data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
            if check:
                if not path.exists() or path.read_bytes() != data:
                    raise ValueError("stale frontend fixture: " + str(path))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            row = dict(
                schema=schema,
                path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(data).hexdigest(),
                generator="make_plan5_views",
                evidence_class="scripted",
                owner="SI01",
                expected="valid",
                scenario=mode,
                input_refs=[],
                limitation=LABEL,
            )
            entries.append(row)
            rows.append(row)
        catalog.append(
            {"mode": mode, "evidence_class": "scripted", "label": LABEL, "records": rows}
        )
    expected = dict(
        index,
        entries=entries,
        frontend_modes=catalog,
        limitations=[
            "Persistent offline counterpart/sample projections only; "
            "no live backend, model or provider qualification"
        ],
    )
    data = json.dumps(expected, indent=2) + "\n"
    if check:
        if index_path.read_text() != data:
            raise ValueError("stale frontend catalog")
    else:
        index_path.write_text(data)
    print(f"{'Checked' if check else 'Generated'} {len(catalog)} scripted frontend modes")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
