"""Offline command-boundary tests: injected SDK only, never provider access."""

import builtins
import os
import shlex
from datetime import UTC, datetime, timedelta
from enum import Enum
from types import SimpleNamespace

import pytest

from pieces.runner.container_runner import (
    ContainerRunner,
    E2BIsolationBackend,
    IsolationNotEstablished,
)

KEY = "e2b_private_test_value"


class CommandExit(Exception):
    def __init__(self, code=7, stdout="out", stderr="failed"):
        self.exit_code, self.stdout, self.stderr = code, stdout, stderr


class CommandTimeout(Exception):
    pass


class Unreachable(CommandTimeout):
    pass


class RpcCode(Enum):
    DEADLINE_EXCEEDED = 1
    CANCELED = 2


class RpcError(Exception):
    def __init__(self, code):
        self.code = code


def deadline_timeout(message=""):
    error = CommandTimeout(message)
    error.__cause__ = RpcError(RpcCode.DEADLINE_EXCEEDED)
    return error


def fake_is_command_deadline(error):
    from pieces.runner.e2b_backend import _is_rpc_deadline

    return _is_rpc_deadline(
        error,
        timeout_type=CommandTimeout,
        rpc_error_type=RpcError,
        deadline_code=RpcCode.DEADLINE_EXCEEDED,
    )


class FakeSandbox:
    sandbox_id = "sandbox-owned-123"

    def __init__(self):
        now = datetime.now(UTC)
        self.info = SimpleNamespace(
            sandbox_id=self.sandbox_id,
            allow_internet_access=False,
            network=None,
            lifecycle={"on_timeout": "kill", "auto_resume": False},
            state="running",
            started_at=now,
            end_at=now + timedelta(seconds=180),
            template_id="provider-base-id",
        )
        self.commands = SimpleNamespace(run=self.run)
        self.files = SimpleNamespace(write=self.write)
        self.calls, self.uploads = [], []
        self.outcome = SimpleNamespace(exit_code=0, stdout="worked", stderr="")
        self.killed = False
        self.running_after_kill = False
        self.kill_error = False
        self.probe_mismatch = False

    def get_info(self, **kwargs):
        return self.info

    def run(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if len(self.calls) == 1:
            nonce = shlex.split(command)[2]
            return SimpleNamespace(
                exit_code=0,
                stdout=f"{nonce}\n{'wrong' if self.probe_mismatch else self.sandbox_id}\n",
                stderr="",
            )
        if isinstance(self.outcome, Exception):
            if "on_stdout" in kwargs:
                kwargs["on_stdout"]("partial")
            raise self.outcome
        return self.outcome

    def write(self, path, data, **kwargs):
        self.uploads.append((path, data))

    def kill(self, **kwargs):
        self.killed = True
        if self.kill_error:
            raise RuntimeError(KEY)

    def is_running(self, **kwargs):
        return self.running_after_kill


@pytest.fixture
def setup(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.py").write_text("print('public')\n")
    box = FakeSandbox()
    creates = []

    def create(**kwargs):
        creates.append(kwargs)
        return box

    sdk = SimpleNamespace(
        create=create,
        command_exit=CommandExit,
        command_timeout=CommandTimeout,
        is_command_deadline=fake_is_command_deadline,
    )
    backend = E2BIsolationBackend(api_key=KEY, authorize_remote=True, sdk_factory=lambda: sdk)
    return SimpleNamespace(source=source, box=box, creates=creates, backend=backend, sdk=sdk)


def run(s, **kwargs):
    return s.backend.run(
        kwargs.pop("command", ["python3", "main.py"]),
        cwd=kwargs.pop("cwd", s.source),
        env=kwargs.pop("env", {}),
        timeout_s=kwargs.pop("timeout_s", 1),
        **kwargs,
    )


def test_default_authority_and_missing_key_refuse_before_create(setup):
    for backend, message in [
        (E2BIsolationBackend(api_key=KEY), "authorize_remote"),
        (E2BIsolationBackend(api_key="", authorize_remote=True), "E2B_API_KEY"),
    ]:
        with pytest.raises(IsolationNotEstablished, match=message):
            backend.run(["true"], cwd=setup.source, env={}, timeout_s=1)
    assert not setup.creates


@pytest.mark.parametrize("command", [[], "true", [1], [""], ["x\x00y"]])
def test_invalid_command_never_provisions(setup, command):
    with pytest.raises(IsolationNotEstablished):
        run(setup, command=command)
    assert not setup.creates


@pytest.mark.parametrize("timeout", [0, -1, 121, float("inf"), float("nan"), True, "1"])
def test_invalid_timeout_never_provisions(setup, timeout):
    with pytest.raises(IsolationNotEstablished):
        run(setup, timeout_s=timeout)
    assert not setup.creates


@pytest.mark.parametrize(
    "name,content",
    [
        (".env", "PUBLIC=yes"),
        ("private.key", "public"),
        ("credentials.json", "{}"),
        ("main.py", KEY),
        ("config.ini", "password = actual-private-value"),
        ("private.pem", "-----BEGIN PRIVATE KEY-----"),
        ("image.bin", "public"),
    ],
)
def test_sensitive_or_unsupported_source_refuses_whole_snapshot(setup, name, content):
    (setup.source / name).write_text(content)
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert not setup.creates


def test_symlink_directory_and_special_file_refused(setup, tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    link = setup.source / "linked"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    link.unlink()
    os.mkfifo(setup.source / "pipe.py")
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert not setup.creates


@pytest.mark.parametrize("mode", ["bytes", "count"])
def test_snapshot_limits_before_provision(setup, mode):
    if mode == "bytes":
        (setup.source / "large.txt").write_text("x" * (2 * 1024 * 1024))
    else:
        for i in range(100):
            (setup.source / f"file{i}.txt").write_text("x")
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert not setup.creates


def test_missing_sdk_has_fixed_diagnostic_without_fallback(setup, monkeypatch):
    original = builtins.__import__

    def importing(name, *args, **kwargs):
        if name == "e2b":
            raise ImportError(KEY)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    backend = E2BIsolationBackend(api_key=KEY, authorize_remote=True)
    marker = setup.source / "host-marker"
    with pytest.raises(IsolationNotEstablished, match="optional SDK") as exc:
        backend.run(["touch", str(marker)], cwd=setup.source, env={}, timeout_s=1)
    assert KEY not in str(exc.value)
    assert not marker.exists()


def test_observed_boundary_safe_transfer_argv_environment_and_metadata(setup):
    command = ["printf", "%s", "a'; touch /host-marker; '"]
    result = ContainerRunner(isolation=setup.backend).execute_shop_process(
        setup.source,
        command,
        env={"LANG": "C", "PATH": "/host/evil", "TMP": "/host"},
        timeout_s=2,
    )
    assert result["exit_code"] == 0
    assert result["isolation_verified"] is True
    assert result["termination_confirmed"] is True
    assert result["termination_scope"] == "owned_e2b_sandbox"
    assert result["sandbox_id"] == setup.box.sandbox_id
    assert result["source_manifest"][0]["path"] == "main.py"
    assert len(result["source_digest"]) == 64
    assert result["env_digest"] == {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C"}
    create = setup.creates[0]
    assert create["template"] == "base"
    assert create["timeout"] <= 180
    assert create["allow_internet_access"] is False
    assert create["lifecycle"] == {"on_timeout": "kill", "auto_resume": False}
    assert "envs" not in create
    assert setup.box.uploads == [("/tmp/goldgraft-source/main.py", b"print('public')\n")]
    guest_command, options = setup.box.calls[1]
    assert shlex.split(guest_command) == [
        "/usr/bin/env",
        "-i",
        "PATH=/usr/local/bin:/usr/bin:/bin",
        "LANG=C",
        *command,
    ]
    assert options["timeout"] == 2
    assert options["cwd"] == "/tmp/goldgraft-source"
    assert KEY not in repr(setup.box.calls)
    assert setup.box.killed


@pytest.mark.parametrize(
    "env", [{"PAYPAL_CLIENT_SECRET": "x"}, {"PUBLIC": KEY}, {"BAD-NAME": "x"}, {"PUBLIC": "\x00"}]
)
def test_unsafe_environment_never_provisions(setup, env):
    with pytest.raises(IsolationNotEstablished):
        run(setup, env=env)
    assert not setup.creates


@pytest.mark.parametrize("mutation", ["identity", "internet", "missing", "lifecycle", "network"])
def test_policy_and_identity_mismatches_fail_closed_and_cleanup(setup, mutation):
    if mutation == "identity":
        setup.box.info.sandbox_id = "another-sandbox"
    elif mutation == "internet":
        setup.box.info.allow_internet_access = True
    elif mutation == "missing":
        setup.box.info.allow_internet_access = None
    elif mutation == "lifecycle":
        setup.box.info.lifecycle = None
    else:
        setup.box.info.network = {"allow_out": ["example.com"]}
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert setup.box.killed
    assert not setup.box.uploads
    assert not setup.box.calls


def test_transport_probe_mismatch_refuses_candidate_and_cleanup(setup):
    setup.box.probe_mismatch = True
    with pytest.raises(IsolationNotEstablished, match="identity"):
        run(setup)
    assert len(setup.box.calls) == 1
    assert not setup.box.uploads
    assert setup.box.killed


def test_command_nonzero_preserves_actual_outputs_redacted(setup):
    setup.box.outcome = CommandExit(9, f"out {KEY}", f"err {KEY}")
    result = run(setup)
    assert result["exit_code"] == 9
    assert result["stdout"] == "out [REDACTED]"
    assert result["stderr"] == "err [REDACTED]"
    assert not result["timed_out"]
    assert setup.box.killed


def test_command_timeout_has_unknown_exit_and_partial_output_then_kills(setup):
    setup.box.outcome = deadline_timeout(KEY)
    result = run(setup)
    assert result["timed_out"] is True
    assert result["exit_code"] is None
    assert result["stdout"] == "partial"
    assert result["termination_confirmed"] is True
    assert KEY not in repr(result)


@pytest.mark.parametrize("outcome", [RuntimeError(KEY), Unreachable(KEY)])
def test_unknown_or_transport_failure_is_not_success_or_timeout(setup, outcome):
    setup.box.outcome = outcome
    with pytest.raises(IsolationNotEstablished) as exc:
        run(setup)
    assert KEY not in str(exc.value)
    assert setup.box.killed
    assert exc.value.sandbox_id == setup.box.sandbox_id
    assert exc.value.termination_confirmed is True


@pytest.mark.parametrize("mode", ["kill", "still_running", "query"])
def test_cleanup_failure_surfaces_owned_id_and_no_termination_claim(setup, mode):
    if mode == "kill":
        setup.box.kill_error = True
    elif mode == "still_running":
        setup.box.running_after_kill = True
    else:

        def bad_query(**kwargs):
            raise RuntimeError(KEY)

        setup.box.is_running = bad_query
    with pytest.raises(IsolationNotEstablished, match="cleanup unconfirmed") as exc:
        run(setup)
    assert setup.box.sandbox_id in str(exc.value)
    assert KEY not in str(exc.value)
    assert exc.value.termination_confirmed is False


@pytest.fixture(autouse=True)
def forbid_host_execution_and_network(monkeypatch):
    import socket
    import subprocess

    def forbidden(*args, **kwargs):
        pytest.fail("offline E2B tests must never execute a host job or open a socket")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize("mode", ["file", "missing", "empty", "symlink", "hardlink", "git"])
def test_source_root_and_links_are_not_silently_filtered(setup, tmp_path, mode):
    source = setup.source
    if mode == "file":
        source = source / "main.py"
    elif mode == "missing":
        source = tmp_path / "missing"
    elif mode == "empty":
        (source / "main.py").unlink()
    elif mode == "symlink":
        source = tmp_path / "alias"
        source.symlink_to(setup.source, target_is_directory=True)
    elif mode == "hardlink":
        os.link(source / "main.py", source / "another.py")
    else:
        (source / ".git").mkdir()
    with pytest.raises(IsolationNotEstablished):
        run(setup, cwd=source)
    assert not setup.creates


@pytest.mark.parametrize("name", ["private-config.json", "service-credentials.txt"])
def test_private_configuration_names_are_refused(setup, name):
    (setup.source / name).write_text("{}")
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert not setup.creates


def test_validated_source_bytes_are_frozen_before_create(setup):
    original = setup.sdk.create

    def changed_source(**kwargs):
        (setup.source / "main.py").write_text(KEY)
        return original(**kwargs)

    setup.sdk.create = changed_source
    result = run(setup)
    assert setup.box.uploads[0][1] == b"print('public')\n"
    assert KEY not in repr(result)


@pytest.mark.parametrize("phase", ["create", "info", "upload"])
def test_setup_failures_are_fixed_diagnostics_and_cleaned_when_owned(setup, phase):
    def broken(*args, **kwargs):
        raise RuntimeError(KEY)

    if phase == "create":
        setup.sdk.create = broken
    elif phase == "info":
        setup.box.get_info = broken
    else:
        setup.box.files.write = broken
    with pytest.raises(IsolationNotEstablished) as exc:
        run(setup)
    assert KEY not in str(exc.value)
    assert exc.value.termination_confirmed is (phase != "create")
    assert setup.box.killed is (phase != "create")
    assert len(setup.box.calls) <= 1


@pytest.mark.parametrize("mode", ["lifetime", "state", "absent_identity", "absent_network"])
def test_missing_or_excessive_boundary_observation_refuses_candidate(setup, mode):
    if mode == "lifetime":
        setup.box.info.end_at += timedelta(seconds=1)
    elif mode == "state":
        setup.box.info.state = "paused"
    elif mode == "absent_identity":
        del setup.box.info.sandbox_id
    else:
        del setup.box.info.allow_internet_access
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert setup.box.killed
    assert not setup.box.calls


def test_key_presence_in_host_environment_is_not_job_authority(setup, monkeypatch):
    monkeypatch.setenv("E2B_API_KEY", KEY)
    with pytest.raises(IsolationNotEstablished, match="authorize_remote"):
        E2BIsolationBackend(sdk_factory=lambda: setup.sdk).run(
            ["true"],
            cwd=setup.source,
            env={},
            timeout_s=1,
        )
    assert not setup.creates


def test_success_output_redacts_key_and_guest_env_only_contains_explicit_values(setup, monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", KEY)
    monkeypatch.setenv("SOME_HOST_VALUE", "host-only")
    setup.box.outcome.stdout = KEY
    setup.box.outcome.stderr = KEY
    result = run(setup, env={"PUBLIC": "a b; 'x'\nnext"})
    assert result["stdout"] == result["stderr"] == "[REDACTED]"
    assert result["env_digest"] == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "PUBLIC": "a b; 'x'\nnext",
    }
    assert shlex.split(setup.box.calls[-1][0])[3] == "PUBLIC=a b; 'x'\nnext"


@pytest.mark.parametrize("command", [["--help"], ["X=y", "true"], ["echo", KEY]])
def test_invalid_or_sensitive_executable_argv_is_refused(setup, command):
    with pytest.raises(IsolationNotEstablished):
        run(setup, command=command)
    assert not setup.creates


def test_cli_authority_refusal_precedes_key_read_or_sdk(tmp_path, monkeypatch):
    from scripts import live_e2b_runner as cli

    def forbidden(*args, **kwargs):
        pytest.fail("key reader must not be reached without authority")

    monkeypatch.setattr(cli, "_read_key", forbidden)
    with pytest.raises(SystemExit) as exc:
        cli.main(["--smoke", "--report-dir", str(tmp_path)])
    assert exc.value.code == 2
    assert not list(tmp_path.iterdir())


def test_cli_smoke_writes_fresh_reports_for_three_verified_cases(tmp_path, capsys):
    import json

    from scripts import live_e2b_runner as cli

    key_file = tmp_path / "private.env"
    key_file.write_text(f'E2B_API_KEY="{KEY}"\n')
    key_file.chmod(0o600)
    boxes = []

    def create(**kwargs):
        box = FakeSandbox()
        box.outcome = [
            SimpleNamespace(exit_code=0, stdout="goldgraft-e2b-smoke\n", stderr=""),
            CommandExit(7, "", "deliberate-failure"),
            deadline_timeout(),
        ][len(boxes) % 3]
        boxes.append(box)
        return box

    def factory():
        return SimpleNamespace(
            create=create,
            command_exit=CommandExit,
            command_timeout=CommandTimeout,
            is_command_deadline=fake_is_command_deadline,
        )

    for _ in range(2):
        assert (
            cli.main(
                ["--authorize-e2b", "--smoke", "--report-dir", str(tmp_path)],
                key_file=key_file,
                sandbox_factory=factory,
            )
            == 0
        )
    reports = list(tmp_path.glob("e2b-smoke-*.json"))
    assert len(reports) == 2
    for report in reports:
        data = json.loads(report.read_text())
        assert data["passed"] and len(data["cases"]) == 3
        assert data["php_merchant_qualification"] is False
        assert KEY not in report.read_text()
    assert len(boxes) == 6 and all(box.killed for box in boxes)
    assert KEY not in capsys.readouterr().out


def test_cli_stops_after_cleanup_failure(setup):
    from scripts.live_e2b_runner import smoke

    setup.box.kill_error = True
    report = smoke(KEY, sandbox_factory=lambda: setup.sdk)
    assert not report["passed"]
    assert len(report["cases"]) == 1
    assert len(setup.creates) == 1
    assert report["cases"][0]["sandbox_id"] == setup.box.sandbox_id
    assert not report["cases"][0]["termination_confirmed"]


@pytest.mark.parametrize("mode", ["public", "symlink", "invalid"])
def test_cli_private_key_file_checks_without_provision(tmp_path, mode):
    from scripts.live_e2b_runner import _read_key

    path = tmp_path / "private.env"
    path.write_text(f"E2B_API_KEY={KEY}\n")
    path.chmod(0o600)
    if mode == "public":
        path.chmod(0o644)
    elif mode == "symlink":
        link = tmp_path / "link.env"
        link.symlink_to(path)
        path = link
    else:
        path.write_text("PUBLIC=yes\n")
    with pytest.raises(IsolationNotEstablished, match="private key file"):
        _read_key(path)


def test_factory_error_diagnostic_traceback_does_not_expose_key(setup):
    import traceback

    def broken_factory():
        raise RuntimeError(KEY)

    setup.backend.sdk_factory = broken_factory
    with pytest.raises(IsolationNotEstablished) as exc:
        run(setup)
    assert KEY not in "".join(traceback.format_exception(exc.value))
    assert not setup.creates


@pytest.mark.parametrize("code_name", ["CANCELED", "DEADLINE_EXCEEDED", "UNKNOWN"])
def test_real_sdk_timeout_mapping_requires_typed_deadline(setup, code_name):
    import traceback

    pytest.importorskip("e2b")
    from connectrpc.code import Code
    from connectrpc.errors import ConnectError
    from e2b.envd.rpc import handle_rpc_exception
    from e2b.exceptions import TimeoutException

    from pieces.runner.e2b_backend import _sdk

    sdk = _sdk()
    sdk.create = setup.sdk.create
    setup.backend.sdk_factory = lambda: sdk
    # Preserve original typed RPC context exactly as the SDK's except/raise does.
    try:
        try:
            raise ConnectError(Code[code_name], KEY)
        except ConnectError as exc:
            raise handle_rpc_exception(exc)  # noqa: B904 - reproduce SDK implicit context
    except Exception as mapped:
        setup.box.outcome = mapped
    if code_name == "DEADLINE_EXCEEDED":
        result = run(setup)
        assert result["timed_out"] is True
        assert result["exit_code"] is None
        assert result["stdout"] == "partial"
        assert result["termination_confirmed"] is True
    else:
        if code_name == "CANCELED":
            assert type(setup.box.outcome) is TimeoutException
        with pytest.raises(IsolationNotEstablished) as exc:
            run(setup)
        assert KEY not in "".join(traceback.format_exception(exc.value))
        assert exc.value.termination_confirmed is True
    assert setup.box.killed


def test_real_sdk_unknown_exact_timeout_fails_closed(setup):
    pytest.importorskip("e2b")
    from e2b.exceptions import TimeoutException

    from pieces.runner.e2b_backend import _sdk

    sdk = _sdk()
    sdk.create = setup.sdk.create
    setup.backend.sdk_factory = lambda: sdk
    setup.box.outcome = TimeoutException("deadline exceeded " + KEY)
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert setup.box.killed


def test_cli_does_not_accept_real_sdk_cancellation_as_timeout():
    pytest.importorskip("e2b")
    from connectrpc.code import Code
    from connectrpc.errors import ConnectError
    from e2b.envd.rpc import handle_rpc_exception

    from pieces.runner.e2b_backend import _sdk
    from scripts.live_e2b_runner import smoke

    boxes = []
    sdk = _sdk()

    def create(**kwargs):
        box = FakeSandbox()
        if len(boxes) == 0:
            box.outcome = SimpleNamespace(exit_code=0, stdout="goldgraft-e2b-smoke\n", stderr="")
        elif len(boxes) == 1:
            box.outcome = SimpleNamespace(exit_code=7, stdout="", stderr="deliberate-failure")
        else:
            try:
                try:
                    raise ConnectError(Code.CANCELED, KEY)
                except ConnectError as exc:
                    raise handle_rpc_exception(exc)  # noqa: B904 - reproduce SDK implicit context
            except Exception as mapped:
                box.outcome = mapped
        boxes.append(box)
        return box

    sdk.create = create
    report = smoke(KEY, sandbox_factory=lambda: sdk)
    assert not report["passed"]
    assert len(report["cases"]) == len(boxes) == 3
    assert not report["cases"][-1]["passed"]
    assert report["cases"][-1]["termination_confirmed"] is True
    assert "result" not in report["cases"][-1]
    assert all(box.killed for box in boxes)
    assert KEY not in repr(report)


@pytest.mark.parametrize("mode", ["unknown", "canceled", "conflicting", "cycle", "deep"])
def test_timeout_provenance_fails_closed_offline(setup, mode):
    error = CommandTimeout("deadline exceeded")
    if mode == "canceled":
        error.__context__ = RpcError(RpcCode.CANCELED)
    elif mode == "conflicting":
        error.__cause__ = RpcError(RpcCode.DEADLINE_EXCEEDED)
        error.__context__ = RpcError(RpcCode.CANCELED)
    elif mode == "cycle":
        error.__cause__ = RpcError(RpcCode.DEADLINE_EXCEEDED)
        error.__context__ = error
    elif mode == "deep":
        tail = error
        for _ in range(16):
            tail.__cause__ = RuntimeError()
            tail = tail.__cause__
        tail.__cause__ = RpcError(RpcCode.DEADLINE_EXCEEDED)
    setup.box.outcome = error
    with pytest.raises(IsolationNotEstablished):
        run(setup)
    assert setup.box.killed


def test_deadline_provenance_accepts_bounded_wrappers_and_shared_chain(setup):
    error = CommandTimeout()
    wrapper = RuntimeError()
    wrapper.__cause__ = RpcError(RpcCode.DEADLINE_EXCEEDED)
    error.__cause__ = error.__context__ = wrapper
    setup.box.outcome = error
    result = run(setup)
    assert result["timed_out"] is True
    assert result["exit_code"] is None
    assert result["termination_confirmed"] is True
