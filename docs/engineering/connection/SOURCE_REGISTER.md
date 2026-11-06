> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Evidence register

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Public primary sources were searched/opened on 6 November 2026. Search/crawl dates are not substitutes for version/account qualification. Only official technical sources underpin selections. No live authenticated user journey, product scenario, payment or worker ran. Failed exploratory URLs were not treated as evidence. Source statements below are concise paraphrases; GoldGraft policy numbers and protocol decisions are design choices, not provider promises.

### R01 — Render scopes

[Render scopes](https://render.com/docs/scoped-api-keys). Workspace-scoped early-access grants; resource-class reads versus writes/secrets/run. Effective scope assurance and account availability not observed.

### R02 — Render public API/OpenAPI

[Render public API/OpenAPI](https://api-docs.render.com/openapi/render-public-api-1.json). Downloaded public schema and extracted service/deploy/user/member fields. No account endpoint called. Local whole-download SHA-256 in evidence/RENDER_API_EXTRACT.json.

### R03 — Render image deployment

[Render image deployment](https://render.com/docs/deploying-an-image). Image-backed path supports digest input; not a claim a current service or provenance exists.

### R04 — Render deployment behaviour

[Render deployment behaviour](https://render.com/docs/deploys). Push/branch/CI configuration can cause deploys; later publication cannot be treated as harmless. No actual deployment tested.

### R05 — Render user identity

[Render user identity](https://api-docs.render.com/reference/get-user). Key-associated provider user response is read-only identity evidence; independently authenticated matching contact and resource role still required.

### R06 — Render workspace members

[Render workspace members](https://api-docs.render.com/reference/retrieve-owner-members). Member listing supports provider user/role association. Scoped endpoint availability requires live qualification.

### R07 — WorkOS identity

[WorkOS identity](https://workos.com/docs/authkit/modeling-your-app). Magic Auth email code; public documentation explains link-scanner reliability concern. No email/provider configuration or login observed.

### R08 — GitHub installation tokens

[GitHub installation tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app). Restricted installation token mechanism, independent of end-user/resource-controller authority. No App/grant created.

### R09 — GitHub source archive

[GitHub source archive](https://docs.github.com/en/rest/repos/contents). Archive/source access mechanism. Safe extraction, controller binding, narrow brokers are GoldGraft responsibilities.

### R10 — Anthropic commercial terms

[Anthropic commercial terms](https://www.anthropic.com/legal/commercial-terms). Commercial usage/confidentiality/training terms are documentary evidence; no customer agreement verified.

### R11 — Anthropic standard retention

[Anthropic standard retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data). Published default API retention is distinct from ZDR and has exceptions. Actual contract must meet disclosure.

### R12 — Anthropic feature retention

[Anthropic feature retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention). Organisation/model/feature-specific arrangements require qualification; not blanket zero retention.

### R13 — Anthropic model IDs

[Anthropic model IDs](https://platform.claude.com/docs/en/models/overview). Model ID candidate documented; account eligibility/version/retention qualification remains required. No model inference used.

### R14 — E2B isolation

[E2B isolation](https://docs.e2b.dev/faq/security-and-compliance). Vendor documents per-sandbox Firecracker and trust documentation. Not GoldGraft isolation/security certification.

### R15 — E2B network

[E2B network](https://docs.e2b.dev/network/internet-access). Network is permissive by default and must be explicitly constrained. GoldGraft policy/IPv6/escape tests remain requirements.

### R16 — Postgres locking

[Postgres locking](https://www.postgresql.org/docs/current/sql-select.html). Documented locking primitive supports designed transaction/outbox approach; no external exactly-once guarantee.

### R17 — Render roles

[Render roles](https://render.com/docs/team-members). Provider role meaning; live matching ADMIN state must be checked, not assumed from key or workspace email.

Local sources: repository models/routes/guidance/fixture/runtime source at baseline SHA; memory/master/proposal and frozen solution/security/release-gap/accountability notes. GitHub API branch/PR/check-run metadata inspected read-only; PR #1 head is recorded in BASELINE_INVENTORY, not merged or reviewed as complete. Drive sessions unavailable. Backup hashes prove only selected local preservation.


### R18 — Service data/identity mechanisms

[Render OIDC](https://render.com/docs/oidc) documents service workload identities and plan prerequisites. [S3 encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html) and [Secrets Manager access](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html) document storage/credential controls. No resources, roles, encryption keys or identity providers were created or inspected.

### R19 — Browser folders and cloud-file permissions
[Directory read picker](https://developer.mozilla.org/en-US/docs/Web/API/Window/showDirectoryPicker) has browser/permission constraints; [directory input](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/webkitdirectory) supplies relative-path file selection. [Drive scope catalogue](https://developers.google.com/workspace/drive/api/guides/api-specific-auth) does not make selected-file drive.file genuinely read-only; [download documentation](https://developers.google.com/workspace/drive/api/guides/manage-downloads) explains revision/download access. Local/cloud GoldGraft flows are proposed only; no source transfer/provider call executed.

### R20 — Render whole-service delivery constraints
Reopened [deploy behaviour](https://render.com/docs/deploys), [image-backed deployments](https://render.com/docs/deploying-an-image), [scoped keys](https://render.com/docs/scoped-api-keys) and [persistent storage](https://render.com/docs/disks). Requirements distinguish deployed runtime from source/test copy and address state survival, trigger side effects and downtime limits. No account/service test or lifecycle execution occurred.
