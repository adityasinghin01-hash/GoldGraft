"""An actual source-driven offline agent path, graded against independent labels."""

import json
import subprocess
import sys

import pytest

from pieces.agents.evals.surveyor import load_cases, score_artifact


def run_package(tmp_path, files):
    from goldgraft_foundation.offline_profile import load_runtime_profile

    from pieces.agents.roles import surveyor_configuration
    from pieces.agents.scheduler import tick
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    from .test_runtime import NOW

    package = package_from_sources(shop_id="independent-package", files=files)
    configuration = dict(
        surveyor_configuration(), offline_final_payload=build_static_inventory(package)
    )
    ports = load_runtime_profile(
        "offline",
        tmp_path / "package.sqlite",
        fixture="surveyor_inventory",
        configuration=configuration,
        inputs=package,
        clock=lambda: NOW,
    )
    tick("fake:runtime-run", NOW, ports)
    return ports, package


def test_missing_required_include_is_discovered_before_model_dispatch(tmp_path):
    ports, package = run_package(
        tmp_path,
        {
            "checkout.php": '<?php\nrequire "backend/payments.php";\n',
        },
    )
    result = ports.control.result("survey")
    assert result.outcome == "blocked"
    assert result.issue.code == "MISSING_EVIDENCE"
    assert result.output_refs == []
    assert package["omissions"]["items"][0]["path"] == "backend/payments.php"
    assert ports.model.total_dispatches() == ports.tools.total_dispatches() == 0


def test_include_path_escape_is_a_hold_not_a_host_read(tmp_path):
    ports, package = run_package(
        tmp_path,
        {
            "checkout.php": '<?php\nrequire "../../etc/passwd";\n',
        },
    )
    assert ports.control.result("survey").outcome == "blocked"
    assert package["omissions"]["items"][0]["reason_code"] == "SOURCE_REFERENCE_OUTSIDE_SCOPE"
    assert ports.model.total_dispatches() == 0


def test_nested_include_resolves_inside_authorised_manifest(tmp_path):
    ports, _package = run_package(
        tmp_path,
        {
            "pages/checkout.php": '<?php\nrequire "../lib/payment.php";\n',
            "lib/payment.php": '<?php\n$method = "RefundTransaction";\n',
        },
    )
    assert ports.control.result("survey").outcome == "completed"


def test_repeated_operations_get_distinct_grounded_ids(tmp_path):
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    package = package_from_sources(
        shop_id="repeated",
        files={
            "a.php": '<?php\n$method = "RefundTransaction";\n$again = "RefundTransaction";\n',
            "b.php": '<?php\n$method = "RefundTransaction";\n',
        },
    )
    payload = build_static_inventory(package)
    assert len(payload["touchpoints"]) == 3
    assert len({t["id"] for t in payload["touchpoints"]}) == 3
    ports, _ = run_package(tmp_path, package["files"])
    assert ports.control.result("survey").outcome == "completed"


@pytest.mark.parametrize(
    "files",
    [
        {"../outside.php": "<?php"},
        {"/etc/passwd": "unread"},
        {"link\\escape.php": "unread"},
        {"file.php": 123},
        {"file.php": "a" * 16385},
        {},
    ],
)
def test_unbounded_or_unsafe_packages_are_rejected_before_assembly(files):
    from pieces.agents.source_inventory import package_from_sources

    with pytest.raises((ValueError, TypeError)):
        package_from_sources(shop_id="unsafe-package", files=files)


def test_oversized_inventory_holds_instead_of_omitting_touchpoints():
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    package = package_from_sources(
        shop_id="large-output",
        files={
            "large.php": "<?php\n" + '$call="RefundTransaction";\n' * 30,
        },
    )
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        build_static_inventory(package)


def test_dir_constant_include_is_resolved_without_execution(tmp_path):
    ports, package = run_package(
        tmp_path,
        {
            "pages/checkout.php": '<?php\nrequire __DIR__ . "/lib/payment.php";\n',
            "pages/lib/payment.php": '<?php\n$method="RefundTransaction";\n',
        },
    )
    assert package["omissions"] == {"items": []}
    assert ports.control.result("survey").outcome == "completed"


def test_remote_include_never_causes_network_or_model_dispatch(tmp_path):
    ports, package = run_package(
        tmp_path,
        {
            "checkout.php": '<?php\ninclude "http://169.254.169.254/latest/meta-data";\n',
        },
    )
    assert ports.control.result("survey").outcome == "blocked"
    assert package["omissions"]["items"][0]["path"] is None
    assert ports.model.total_dispatches() == ports.tools.total_dispatches() == 0


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_source_driven_runtime_handles_new_layouts_and_empty_inventory(tmp_path, case):
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pieces.agents.source_inventory",
            "--case",
            case["id"],
            "--state-file",
            str(tmp_path / "inventory.sqlite"),
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    data = json.loads(process.stdout)
    assert data["mode"] == "deterministic_offline"
    assert data["model_api_calls"] == 0
    assert score_artifact(case, data["inventory"])["passed"]
    assert data["inspection"]["output_ref"] == data["result"]["output_refs"][0]
    assert len(data["inspection"]["touchpoints"]) == len(case["expected"])
    assert len(data["result"]["evidence_refs"]) == len(case["files"]) + 2
    assert data["real_model_evaluation"] == "NOT RUN"


def test_source_driven_cli_rejects_unknown_case_without_creating_state(tmp_path):
    state = tmp_path / "must-not-exist.sqlite"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pieces.agents.source_inventory",
            "--case",
            "unapproved-case",
            "--state-file",
            str(state),
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode != 0
    assert not state.exists()


def test_thirteen_short_path_indicators_fit_without_dropping_any_evidence(tmp_path):
    from goldgraft_contracts.plan5_common import canonical_bytes

    files = {"refund.php": "<?php\n" + "$m='RefundTransaction';\n" * 13}
    ports, _ = run_package(tmp_path, files)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    assert task.state == "succeeded"
    descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
    assert descriptor.ref in ports.control.result("survey").output_refs
    assert len(payload["touchpoints"]) == 13
    assert len({t["id"] for t in payload["touchpoints"]}) == 13
    assert payload["money_flow"]["refund"] == [
        {"file": "refund.php", "line": line} for line in range(2, 15)
    ]
    assert len(canonical_bytes(payload)) <= 4000


def test_location_ids_remain_stable_when_an_unrelated_file_is_added():
    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    files = {"refund.php": "<?php\n$m='RefundTransaction';\n"}
    original = build_static_inventory(package_from_sources(shop_id="stable-id", files=files))
    files["a-unrelated.php"] = "<?php\n"
    expanded = build_static_inventory(package_from_sources(shop_id="stable-id", files=files))
    assert original["touchpoints"] == expanded["touchpoints"]


def test_location_id_collision_holds_instead_of_returning_ambiguous_inventory(monkeypatch):
    from pieces.agents import source_inventory

    package = source_inventory.package_from_sources(
        shop_id="collision",
        files={"refund.php": "<?php\n$m='RefundTransaction';\n$m='RefundTransaction';\n"},
    )
    monkeypatch.setattr(source_inventory, "content_digest", lambda value: "a" * 64)
    with pytest.raises(ValueError, match="DENIED"):
        source_inventory.build_static_inventory(package)
