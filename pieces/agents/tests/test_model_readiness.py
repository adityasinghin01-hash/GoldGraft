"""Read-only preflight and independent artifact scoring, without model access."""

import json
import os
import subprocess
import sys

import pytest

from pieces.agents.cli import main
from pieces.agents.model_readiness import model_access_report


def test_doctor_explains_whole_project_budget_without_enabling_spend(capsys):
    assert main(["doctor", "--mode", "offline"]) == 0
    report = json.loads(capsys.readouterr().out)
    access = report["model_access"]
    assert access["budget_scope"] == "all_13_agents_and_all_project_api_checks"
    assert access["initial_paid_checkpoint_micro_usd"] == 50000
    assert access["outer_review_checkpoint_micro_usd"] == 5000000
    assert access["project_hard_ceiling_micro_usd"] == 20000000
    assert access["paid_calls_enabled"] is False
    assert access["reservation_ledger"] == "NOT QUALIFIED"


def test_key_presence_alone_never_admits_service_or_displays_key(tmp_path):
    marker = "synthetic-local-presence-canary"
    env = dict(os.environ, ANTHROPIC_API_KEY=marker)
    doctor = subprocess.run(
        [sys.executable, "-m", "pieces.agents.cli", "doctor"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert doctor.returncode == 0
    assert marker not in doctor.stdout + doctor.stderr
    report = json.loads(doctor.stdout)
    assert report["model_access"]["api_key_presence"] == "PRESENT"
    assert report["model_access"]["paid_calls_enabled"] is False
    state = tmp_path / "must-not-exist.sqlite"
    denied = subprocess.run(
        [
            sys.executable,
            "-m",
            "pieces.agents.cli",
            "run",
            "--mode",
            "service",
            "--state-file",
            str(state),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert denied.returncode != 0
    assert marker not in denied.stdout + denied.stderr
    assert not state.exists()


def test_private_local_key_is_reported_without_disclosure_or_environment_loading(
    tmp_path, monkeypatch
):
    marker = "synthetic-local-file-presence-canary"
    key_file = tmp_path / "private.env"
    key_file.write_text("ANTHROPIC_API_KEY=" + marker + "\n")
    key_file.chmod(0o600)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = model_access_report(local_key_file=key_file)
    serialized = json.dumps(report)
    assert marker not in serialized
    assert report["api_key_presence"] == "ABSENT"
    assert report["api_key_presence_scope"] == "current_process_environment_only"
    assert report["local_key_configuration"]["state"] == "PRESENT_UNVALIDATED"
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert report["paid_calls_enabled"] is False
    assert report["reservation_ledger"] == "NOT QUALIFIED"


@pytest.mark.parametrize(
    "contents,mode,expected",
    [
        ("", 0o600, "ABSENT"),
        ("ANTHROPIC_API_KEY=[YOUR_KEY]\n", 0o600, "PLACEHOLDER"),
        ("ANTHROPIC_API_KEY=one\nANTHROPIC_API_KEY=two\n", 0o600, "DUPLICATE_ENTRIES"),
        ("ANTHROPIC_API_KEY=private\n", 0o644, "UNSAFE_PERMISSIONS"),
        ("private-without-assignment\n", 0o600, "ABSENT"),
        ("ANTHROPIC_API_KEY=" + "x" * 16385, 0o600, "OVERSIZED"),
    ],
)
def test_local_key_diagnostic_never_accepts_ambiguous_or_unsafe_configuration(
    tmp_path, contents, mode, expected
):
    path = tmp_path / "private.env"
    path.write_text(contents)
    path.chmod(mode)
    report = model_access_report(local_key_file=path)
    assert report["local_key_configuration"]["state"] == expected
    assert report["paid_calls_enabled"] is False


def test_local_key_diagnostic_rejects_symlink_without_following_it(tmp_path):
    target = tmp_path / "target"
    target.write_text("ANTHROPIC_API_KEY=synthetic-secret\n")
    target.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(target)
    report = model_access_report(local_key_file=link)
    assert report["local_key_configuration"]["state"] == "UNSAFE_FILE_TYPE"
    assert "synthetic-secret" not in json.dumps(report)


def test_doctor_does_not_read_local_key_without_explicit_request():
    assert model_access_report()["local_key_configuration"]["state"] == "NOT_CHECKED"


def test_local_key_option_cannot_activate_a_runtime_or_create_state(tmp_path):
    state = tmp_path / "not-created.sqlite"
    with pytest.raises(SystemExit):
        main(["run", "--check-local-key", "--state-file", str(state)])
    assert not state.exists()


def test_doctor_local_option_checks_only_private_presence(tmp_path, monkeypatch, capsys):
    from pathlib import Path

    directory = tmp_path / ".config" / "goldgraft"
    directory.mkdir(parents=True)
    path = directory / "anthropic.env"
    path.write_text("ANTHROPIC_API_KEY=synthetic-doctor-canary\n")
    path.chmod(0o600)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert main(["doctor", "--check-local-key"]) == 0
    output = capsys.readouterr().out
    assert "synthetic-doctor-canary" not in output
    report = json.loads(output)["model_access"]
    assert report["local_key_configuration"]["state"] == "PRESENT_UNVALIDATED"
    assert report["paid_calls_enabled"] is False
