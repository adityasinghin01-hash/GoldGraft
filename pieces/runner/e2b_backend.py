"""Optional, explicitly authorised E2B command primitive; never executes on the host."""

import hashlib
import json
import math
import os
import re
import secrets
import shlex
import stat
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

MAX_FILES = 100
MAX_BYTES = 2 * 1024 * 1024
MAX_LIFETIME_S = 180
GUEST_CWD = "/tmp/goldgraft-source"
GUEST_PATH = "/usr/local/bin:/usr/bin:/bin"
REQUEST_TIMEOUT_S = 15
IGNORED_ENV = {"PATH", "TMP", "TEMP", "SYSTEMROOT"}
SECRET_NAME = re.compile(
    r"secret|token|key|password|passwd|credential|authorization|signature|private", re.I
)
SOURCE_SUFFIXES = {
    ".py",
    ".php",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".sql",
    ".sh",
    ".ini",
    ".cfg",
    ".lock",
}
# Conservative refusal, not a claim that an arbitrary repository contains no secrets.
SECRET_CONTENT = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?:password|passwd|secret|token|api[_-]?key|authorization|credential)"
    r"[\w.-]*[\"']?\s*[:=]\s*[\"']?[^\s\"',;}]+|"
    r"\b(?:AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})\b|"
    r"https?://[^\s/:]+:[^\s/@]+@",
    re.I,
)


class IsolationNotEstablished(RuntimeError):
    """A refused or unverified boundary, with safe reconciliation information."""

    def __init__(self, message, *, sandbox_id=None, termination_confirmed=False):
        super().__init__(message)
        self.sandbox_id = sandbox_id
        self.termination_confirmed = termination_confirmed


def _sdk():
    try:
        from connectrpc.code import Code
        from connectrpc.errors import ConnectError
        from e2b import CommandExitException, Sandbox, TimeoutException
    except ImportError:
        raise IsolationNotEstablished(
            "E2B optional SDK unavailable; install requirements-e2b.txt"
        ) from None
    return SimpleNamespace(
        create=Sandbox.create,
        command_exit=CommandExitException,
        command_timeout=TimeoutException,
        is_command_deadline=lambda exc: _is_rpc_deadline(
            exc,
            timeout_type=TimeoutException,
            rpc_error_type=ConnectError,
            deadline_code=Code.DEADLINE_EXCEEDED,
        ),
    )


def _is_rpc_deadline(error, *, timeout_type, rpc_error_type, deadline_code):
    """Require positive typed deadline provenance; cycles, ambiguity and depth fail closed."""
    if type(error) is not timeout_type:
        return False
    visited, active = set(), set()
    found_deadline = False

    def visit(exc):
        nonlocal found_deadline
        if exc is None:
            return True
        identity = id(exc)
        if identity in active:
            return False
        if identity in visited:
            return True
        if len(visited) >= 16:
            return False
        visited.add(identity)
        active.add(identity)
        if isinstance(exc, rpc_error_type):
            if exc.code is not deadline_code:
                return False
            found_deadline = True
        if not visit(exc.__cause__) or not visit(exc.__context__):
            return False
        active.remove(identity)
        return True

    return visit(error) and found_deadline


def _refuse(message):
    raise IsolationNotEstablished(message) from None


def _validate_text(value, api_key):
    if not isinstance(value, str) or "\x00" in value or api_key in value:
        _refuse("E2B input contains invalid or sensitive data")
    try:
        value.encode("utf-8")
    except UnicodeError:
        _refuse("E2B input must be UTF-8 text")


def _snapshot(cwd, api_key):
    """Open each directory/file without following links; retain validated bytes before create."""
    files = []
    total = 0
    directory_count = 0

    def visit(directory_fd, prefix=""):
        nonlocal total, directory_count
        directory_count += 1
        if directory_count > MAX_FILES:
            _refuse("E2B source directory limit exceeded")
        for name in sorted(os.listdir(directory_fd)):
            _validate_text(name, api_key)
            relative = f"{prefix}{name}"
            if (
                name.startswith(".")
                or SECRET_NAME.search(name)
                or name.lower() in {"config", "id_rsa", "id_ed25519"}
                or "\\" in name
                or any(ord(c) < 32 for c in name)
            ):
                _refuse("E2B sensitive or unsupported source path")
            entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(entry.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd
                )
                try:
                    visit(child, relative + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(entry.st_mode):
                if (
                    entry.st_nlink != 1
                    or Path(name).suffix.lower() not in SOURCE_SUFFIXES
                    or len(files) >= MAX_FILES
                    or entry.st_size > MAX_BYTES - total
                ):
                    _refuse("E2B source file type or snapshot limit refused")
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                with os.fdopen(fd, "rb") as source:
                    opened = os.fstat(source.fileno())
                    if (
                        not stat.S_ISREG(opened.st_mode)
                        or opened.st_nlink != 1
                        or (entry.st_dev, entry.st_ino) != (opened.st_dev, opened.st_ino)
                    ):
                        _refuse("E2B source changed during snapshot")
                    data = source.read(MAX_BYTES - total + 1)
                    after = os.fstat(source.fileno())
                if (
                    len(data) > MAX_BYTES - total
                    or opened.st_size != len(data)
                    or opened.st_mtime_ns != after.st_mtime_ns
                ):
                    _refuse("E2B source changed or snapshot limit exceeded")
                try:
                    content = data.decode("utf-8")
                except UnicodeError:
                    _refuse("E2B source must be public UTF-8 text")
                _validate_text(content, api_key)
                if SECRET_CONTENT.search(content):
                    _refuse("E2B sensitive source content refused")
                total += len(data)
                files.append((relative, data))
            else:
                _refuse("E2B symlinks and special source files are forbidden")

    try:
        path = Path(cwd).absolute()
        if path != path.resolve(strict=True) or path == Path.home() or path == Path("/"):
            _refuse("E2B source must be a dedicated real directory")
        root = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            visit(root)
        finally:
            os.close(root)
    except (OSError, TypeError, ValueError):
        _refuse("E2B source snapshot unavailable")
    if not files:
        _refuse("E2B source snapshot must contain regular source files")
    manifest = [
        {"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for path, data in files
    ]
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return files, manifest, digest


class E2BIsolationBackend:
    """One disposable VM per command. `base` is an alias, not an immutable image pin."""

    name = "e2b_sandbox"

    def __init__(self, api_key=None, *, authorize_remote=False, sdk_factory=None):
        self.api_key = os.environ.get("E2B_API_KEY") if api_key is None else api_key
        self.authorize_remote = authorize_remote
        self.sdk_factory = sdk_factory or _sdk

    def run(
        self, command: list[str], *, cwd: Path, env: dict[str, str], timeout_s: float
    ) -> dict[str, Any]:
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            _refuse("E2BIsolationBackend requires an E2B_API_KEY")
        if self.authorize_remote is not True:
            _refuse("E2B remote execution requires authorize_remote=True")
        if not isinstance(command, list) or not command:
            _refuse("E2B command must be a nonempty list of strings")
        for arg in command:
            _validate_text(arg, self.api_key)
            if SECRET_CONTENT.search(arg):
                _refuse("E2B sensitive command argument refused")
        if not command[0] or command[0].startswith("-") or "=" in command[0]:
            _refuse("E2B executable must be a nonempty command name or path")
        if (
            type(timeout_s) not in (int, float)
            or not math.isfinite(timeout_s)
            or not 0 < timeout_s <= 120
        ):
            _refuse("E2B command timeout must be finite and within 0 < seconds <= 120")
        guest_env = {"PATH": GUEST_PATH}
        if not isinstance(env, dict):
            _refuse("E2B environment must be an explicit mapping")
        for name, value in env.items():
            if isinstance(name, str) and name in IGNORED_ENV:
                continue
            _validate_text(name, self.api_key)
            _validate_text(value, self.api_key)
            if (
                not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
                or SECRET_NAME.search(name)
                or SECRET_CONTENT.search(value)
            ):
                _refuse("E2B guest environment is invalid or sensitive")
            guest_env[name] = value
        files, manifest, digest = _snapshot(cwd, self.api_key)
        try:
            sdk = self.sdk_factory()
        except IsolationNotEstablished:
            raise
        except Exception:
            _refuse("E2B optional SDK unavailable")

        box = None
        sandbox_id = None
        result = None
        failure = None
        cleanup_confirmed = False
        start = time.monotonic()
        started_at = datetime.now(UTC).isoformat()
        try:
            box = sdk.create(
                template="base",
                timeout=MAX_LIFETIME_S,
                api_key=self.api_key,
                allow_internet_access=False,
                lifecycle={"on_timeout": "kill", "auto_resume": False},
                request_timeout=REQUEST_TIMEOUT_S,
            )
            candidate_id = box.sandbox_id
            if (
                not isinstance(candidate_id, str)
                or not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", candidate_id)
                or self.api_key in candidate_id
            ):
                _refuse("E2B sandbox identity unavailable")
            sandbox_id = candidate_id
            info = box.get_info(request_timeout=REQUEST_TIMEOUT_S)
            self._check_info(info, sandbox_id)
            nonce = secrets.token_hex(24)
            probe = box.commands.run(
                "printf '%s\\n%s\\n' " + shlex.quote(nonce) + ' "$E2B_SANDBOX_ID"',
                timeout=10,
                request_timeout=REQUEST_TIMEOUT_S,
            )
            if probe.exit_code != 0 or probe.stdout != f"{nonce}\n{sandbox_id}\n" or probe.stderr:
                _refuse("E2B guest transport identity mismatch")
            for relative, data in files:
                box.files.write(f"{GUEST_CWD}/{relative}", data, request_timeout=REQUEST_TIMEOUT_S)
            argv = ["/usr/bin/env", "-i", *(f"{k}={v}" for k, v in guest_env.items()), *command]
            stdout, stderr = [], []
            timed_out = False
            try:
                outcome = box.commands.run(
                    shlex.join(argv),
                    cwd=GUEST_CWD,
                    timeout=timeout_s,
                    request_timeout=REQUEST_TIMEOUT_S,
                    on_stdout=stdout.append,
                    on_stderr=stderr.append,
                )
            except sdk.command_exit as exc:
                outcome = exc
            except Exception as exc:
                # The exact SDK timeout class also represents server/proxy cancellation.
                # Require typed RPC deadline provenance, never exception-message matching.
                if type(exc) is not sdk.command_timeout or not sdk.is_command_deadline(exc):
                    raise
                outcome = SimpleNamespace(
                    exit_code=None, stdout="".join(stdout), stderr="".join(stderr)
                )
                timed_out = True
            if (
                not isinstance(outcome.stdout, str)
                or not isinstance(outcome.stderr, str)
                or (not timed_out and type(outcome.exit_code) is not int)
            ):
                _refuse("E2B command result unavailable")
            result = {
                "exit_code": outcome.exit_code,
                "stdout": self._redact(outcome.stdout),
                "stderr": self._redact(outcome.stderr),
                "timed_out": timed_out,
                "isolation_verified": True,
                "execution_boundary": self.name,
                "sandbox_id": sandbox_id,
                "source_manifest": manifest,
                "source_digest": digest,
                "env_digest": guest_env,
                "template_requested": "base",
                "template_id": self._redact(info.template_id),
                "immutable_image_verified": False,
                "allow_internet_access": False,
                "max_lifetime_s": MAX_LIFETIME_S,
                "observed_started_at": info.started_at.isoformat(),
                "observed_end_at": info.end_at.isoformat(),
                "identity_verified": True,
                "started_at": started_at,
                "qualification_scope": "bounded_command_primitive",
            }
        except IsolationNotEstablished as exc:
            failure = str(exc)
        except Exception:
            failure = (
                "E2B provisioning outcome unknown; reconcile provider account; no host fallback"
                if box is None
                else "E2B provider or command transport failed; no host fallback"
            )
        finally:
            if box is not None:
                kill_ok = False
                try:
                    box.kill(request_timeout=REQUEST_TIMEOUT_S)
                    kill_ok = True
                except Exception:
                    pass
                try:
                    cleanup_confirmed = box.is_running(request_timeout=REQUEST_TIMEOUT_S) is False
                except Exception:
                    cleanup_confirmed = False
                cleanup_confirmed = kill_ok and cleanup_confirmed
                if not cleanup_confirmed:
                    raise IsolationNotEstablished(
                        f"E2B cleanup unconfirmed; owned sandbox id: {sandbox_id or 'unknown'}",
                        sandbox_id=sandbox_id,
                        termination_confirmed=False,
                    ) from None
        if failure:
            raise IsolationNotEstablished(
                failure, sandbox_id=sandbox_id, termination_confirmed=cleanup_confirmed
            ) from None
        result.update(
            termination_confirmed=cleanup_confirmed,
            termination_scope="owned_e2b_sandbox",
            finished_at=datetime.now(UTC).isoformat(),
            duration_ms=(time.monotonic() - start) * 1000,
        )
        return result

    def _redact(self, value):
        return value.replace(self.api_key, "[REDACTED]")

    @staticmethod
    def _check_info(info, sandbox_id):
        if info.sandbox_id != sandbox_id:
            _refuse("E2B control-plane identity mismatch")
        # Live E2B (12 Nov 2026) reports {"allow_public_traffic": False} for an
        # internet-off VM: stricter, so accepted only when exactly False. Any
        # allow-list, rules, proxy or DNS override stays a mismatch.
        network = dict(info.network) if isinstance(info.network, dict) else info.network
        if isinstance(network, dict) and network.get("allow_public_traffic", False) is False:
            network.pop("allow_public_traffic", None)
        if (
            info.allow_internet_access is not False
            or network not in (None, {}, {"deny_out": ["0.0.0.0/0"]})
            or info.lifecycle != {"on_timeout": "kill", "auto_resume": False}
            or info.state != "running"
        ):
            _refuse("E2B observed network or lifecycle policy mismatch")
        lifetime = (info.end_at - info.started_at).total_seconds()
        if not 0 < lifetime <= MAX_LIFETIME_S or not isinstance(info.template_id, str):
            _refuse("E2B observed lifetime or template unavailable")
