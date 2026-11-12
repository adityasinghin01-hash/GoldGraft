# Optional E2B command runner

The runner supports an explicitly authorised, disposable E2B command VM through
`E2BIsolationBackend`. The default constructor refuses remote execution even
when `E2B_API_KEY` exists. There is no host-process fallback. The SDK is optional;
ordinary tests inject a fake SDK and forbid sockets and host subprocesses.

This is a **bounded command primitive**. A successful smoke establishes observed
VM identity, the requested control-plane network/lifecycle policy, command output
and confirmed termination for those commands. It does not qualify PHP shop
execution, payment behaviour, merchant isolation, complete source intake or
working-site delivery. It does not clear the existing `isolation:runner` proof
gate, modify a certificate or replace earlier PHP evidence.

## Install and explicit smoke

From the repository root, using the existing Python 3.12 environment:

```sh
uv pip install --python .venv/bin/python -r requirements-e2b.txt
.venv/bin/python -m scripts.live_e2b_runner --smoke --authorize-e2b \
  --report-dir /Users/aditya/reports/goldgraft-e2b-smoke
```

`requirements-e2b.txt` pins **e2b==2.63.0**. Provision the key separately in
`~/.config/goldgraft/e2b.env` as `E2B_API_KEY=<private value>`; the file must be owned
by the current user, regular, not a symlink, and inaccessible to group/other
(e.g. mode `0600`). The CLI neither evaluates that file as shell code nor prints
its content. `--authorize-e2b` is required before it reads the key or contacts
E2B. It creates at most three VMs, one each for a tiny public Python source,
a deliberate exit 7 and a one-second command deadline. Any failed case or
unconfirmed cleanup stops further VM creation. Reports have unique names;
earlier evidence is never overwritten. Live smoke requires separate external
job authority and is not part of pytest.

SDK adapter use:

```python
from pathlib import Path
from pieces.runner.container_runner import E2BIsolationBackend

backend = E2BIsolationBackend(api_key=private_key, authorize_remote=True)
result = backend.run(
    ["python3", "main.py"],
    cwd=Path("public-smoke-source").resolve(),
    env={"LANG": "C"},
    timeout_s=10,
)
```

## Input and transfer boundary

Prepare a dedicated, reviewed **public/nonsecret** source directory. All files
are inspected and frozen into bytes plus a SHA-256 manifest **before** create.
The entire request is refused if any entry is unsupported; no silently filtered
repository is presented as a complete shop.

- At most **100 regular files**, **2 MiB total**, and 100 directories.
- Reject symlinks (including a source path through a symlink), hardlinks,
  special files, home/root directory selection, dotfiles/directories including
  `.env*` and `.git`, and credential/key/private configuration names.
- Accept UTF-8 source/text files with the explicit extensions in
  `pieces/runner/e2b_backend.py`. Refuse binary content, exact API-key occurrences,
  private-key blocks, common credential assignments and common token patterns.
  This conservative screen may reject harmless source and is not a general
  secret-discovery guarantee. Arbitrary merchant repositories are unsupported.
- Upload only captured bytes to `/tmp/goldgraft-source`; no host environment,
  home directory, original absolute path, external symlink target or credentials
  are transferred. File modes and empty directories are not reproduced; invoke
  scripts through their interpreter.
- Commands must be a nonempty list of strings without NUL or sensitive data.
  Executable names beginning with `-` or containing `=` are unsupported to keep
  `/usr/bin/env` parsing unambiguous. Arguments are shell-quoted independently.
- Candidate execution uses `/usr/bin/env -i` and Linux
  `PATH=/usr/local/bin:/usr/bin:/bin`. Host `PATH`, `TMP`, `TEMP`, and `SYSTEMROOT`
  are ignored. Only explicitly supplied nonsecret environment values follow;
  credential-like names and API-key occurrences are refused.

## Observations, deadlines and cleanup

Each create explicitly requests `template="base"`, internet disabled, a
**180-second maximum VM lifetime**, `on_timeout="kill"` and `auto_resume=False`.
The explicit `base` alias is **not an immutable image pin**. The observed
`template_id` is retained, with `immutable_image_verified=False`.

Before upload or candidate execution the adapter checks `get_info()` for matching
sandbox ID, running state, disabled internet, no custom network exception, the
kill/no-resume lifecycle and an observed lifetime no longer than 180 seconds.
Missing, unsupported or changed observations hold the job. It then sends a fresh
nonce and reads `E2B_SANDBOX_ID` through the guest command transport, requiring an
exact match. Exit zero alone never establishes a boundary. Control-plane network
observation is not an independent packet-level egress audit; no package download
or external-service access is supported by this primitive.

The command timeout must be finite, positive and **at most 120 seconds**. The
SDK receives it as `commands.run(timeout=...)`; the identity probe has ten seconds.
SDK control/file requests have a 15-second request timeout. Actual nonzero command
exit codes and stdout/stderr are preserved. Only an exact SDK `TimeoutException` with positively identified typed
`ConnectError` / `Code.DEADLINE_EXCEEDED` provenance returns `timed_out=True`,
unknown `exit_code=None` and any streamed partial output. The classifier traverses
both cause and context, bounded to 16 distinct exceptions. Missing provenance,
cycles, excessive depth or conflicting RPC codes fail closed. The SDK also maps
server/proxy `CANCELED` to the same timeout class; cancellation must hold the job
and cannot pass the smoke timeout case. No exception-message matching is used.
A classified timeout means the SDK command stream deadline expired; it does not
infer a process exit. Timeout subclasses (including a vanished VM) and other
provider failures raise fixed diagnostics. API-key values are redacted
from returned outputs and never interpolated into error diagnostics.

A `finally` block kills the owned VM and requires `is_running() is False` before
reporting `termination_confirmed=True`, scoped to `owned_e2b_sandbox`. Cleanup
failure overrides a successful command and raises `IsolationNotEstablished`
with the safe owned sandbox ID and `termination_confirmed=False`. Stop and
reconcile that ID in the provider account; do not assume the billable VM stopped.
A create request that fails before returning an ID has unknown provisioning
outcome and requires account reconciliation. The requested 180-second lifetime
is a backstop, not termination evidence. No automatic retries or resume occur.

Results retain source digest/manifest, sandbox/template identity, observed
policy/lifetime, timestamps, actual duration through cleanup and scope
`bounded_command_primitive`. `ContainerRunner.execute_shop_process` preserves
this metadata. Fixture replay and host-process execution retain their existing
honest qualification behaviour.

## Offline checks and provider references

```sh
.venv/bin/pytest -q plugtests/test_e2b_backend.py plugtests/test_connection_and_providers.py
.venv/bin/ruff check pieces/runner/container_runner.py pieces/runner/e2b_backend.py \
  scripts/live_e2b_runner.py plugtests/test_e2b_backend.py
```

The injectable `sdk_factory` (CLI test hook: `sandbox_factory`) returns an object
with `create`, `command_exit`, `command_timeout` and an explicit
`is_command_deadline(exception)` predicate. Test fakes implement the
SDK's info, command, file-write, kill and running-state interfaces. No test
requires a live account. Core fake tests do not require the SDK; optional
compatibility regressions use installed SDK error mapping (with no network) and
are skipped when that optional dependency is absent.

Implementation was checked against the official 2.63.0 SDK source and these
provider references: [sandbox lifecycle](https://docs.e2b.dev/sandbox.md),
[internet access](https://docs.e2b.dev/network/internet-access.md),
[commands](https://docs.e2b.dev/commands.md), and
[file upload](https://docs.e2b.dev/filesystem/upload.md).
