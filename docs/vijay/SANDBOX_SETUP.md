# Configure existing sandbox access locally

Use PayPal's sandbox only. Do not paste credentials into chat, GitHub, screenshots or shell arguments. No payment is initiated by the setup wizard. Creating new apps, granting permissions or changing account credentials is separate from reading existing test credentials.

1. Open [PayPal Developer](https://developer.paypal.com/) in your browser and sign in with your real developer login. Choose **Sandbox**, never Live.
2. Open **Apps & Credentials** and the existing sandbox REST app associated with the intended business test account. Obtain its Client ID and Secret privately.
3. Open **Testing Tools → Sandbox Accounts**. On the **business** account, choose **View/Edit Account → API Credentials** to find the legacy NVP username, password and signature if that account exposes them. Its account email is the sandbox recipient. If NVP credentials are unavailable, leave those fields pending; do not substitute REST keys or live credentials.
4. On the **personal** sandbox account, use **View/Edit Account** to obtain the test buyer email and its test password. This is different from your real developer login.
5. Double-click `scripts/configure-sandbox.cmd` on Windows, or run `python scripts/sandbox_config.py --configure` in your own terminal. Paste each value into its named hidden-input prompt. Enter leaves an unavailable field pending. The wizard prints only field-presence status.

On Windows' hidden prompts, use right-click to paste. Ctrl+V can be captured as an invisible control character by the console. The wizard rejects such input and asks again; an existing field with a control character must be replaced. Status reports list only invalid field names. Credential probes block malformed control-character input before any HTTP attempt. No credential value is automatically edited or repaired.

Credentials are saved to ignored `.secrets/sandbox.json`, a plaintext local development file with restricted file mode where supported. This is not a managed vault or encrypted storage. It must stay private and untracked. Scripts load it only with an explicit `--config` argument. The future backend broker remains the production/service boundary.

Check presence safely with `python scripts/sandbox_config.py`. After the operator separately authorizes actual sandbox credential probes, run:

```powershell
python scripts/live_sandbox_probe.py --probe oauth --config .secrets/sandbox.json --live --authority-ref local-sandbox-access
python scripts/live_sandbox_probe.py --probe nvp-balance --config .secrets/sandbox.json --live --authority-ref local-sandbox-access
```

These make only OAuth/GetBalance requests. They do not complete checkout, charge/refund or validate IPN/webhook delivery. PASS here cannot close the Phase 1 end-to-end flow gate. Do not execute without the correct sandbox account authority. No probe is invoked automatically by the wizard or unit tests.

Provider instructions checked 8 November 2026: [REST getting started](https://developer.paypal.com/api/get-started/), [sandbox accounts](https://developer.paypal.com/sandbox-testing/accounts), [NVP test calls](https://developer.paypal.com/sandbox-testing/calls/). Dashboard labels/capability availability must be confirmed in the actual account.
