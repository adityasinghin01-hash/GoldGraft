"""Persistent, explicitly scripted Surveyor counterpart, synthetic MIT test source only.

No provider SDK, network, filesystem-source adapter or merchant authority lives here.
The final response is a hand-authored fixture, independent of the detector below.
"""

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime

from goldgraft_contracts.agent_runtime import ArtifactDescriptor, SubjectManifest
from goldgraft_contracts.plan5_common import content_digest, reject_secret
from goldgraft_contracts.registry import validate

from ._fixtures import example
from .guarded_tools import GuardedOfflineTools
from .model_broker import ScriptedModelBroker
from .offline_store import encoded, fail
from .plan5_profile import RUN, OfflineProfile, RuntimeArtifacts
from .task_control import OfflineTaskControl

SOURCES = {
    "checkout.php": (
        '<?php\n$request = "SetExpressCheckout";\n$capture = "DoExpressCheckoutPayment";\n'
    ),
    "refund.php": '<?php\n$refund = "RefundTransaction";\n',
    "ipn.php": '<?php\n$validation = "cmd=_notify-validate";\n',
    "browser.js": "paypal.Button.render({});\n",
}
# Synthetic detection metadata, not endorsed SDK/API mappings.
RULES = [
    ("nvp-create", "SetExpressCheckout", "EC_NVP", "SetExpressCheckout", "create"),
    ("nvp-capture", "DoExpressCheckoutPayment", "EC_NVP", "DoExpressCheckoutPayment", "capture"),
    ("nvp-refund", "RefundTransaction", "EC_NVP", "RefundTransaction", "refund"),
    ("ipn-notify", "cmd=_notify-validate", "IPN", "IPN validation indicator", "notify"),
    ("checkout-v4", "paypal.Button.render", "CHECKOUT_JS_V4", "paypal.Button.render", "approve"),
]


def fixture_inputs(*, missing_backend=False, required_lenses=None):
    manifest = [
        {
            "relative_path": path,
            "file_type": "file",
            "bytes": len(text.encode()),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        for path, text in sorted(SOURCES.items())
    ]
    snapshot = example("SourceSnapshot/1")
    snapshot.update(
        snapshot_id="fake:survey-source",
        manifest_digest=content_digest(manifest),
        file_count=len(manifest),
        total_bytes=sum(e["bytes"] for e in manifest),
        omission_manifest_ref="fake:survey-omissions",
        completeness="incomplete" if missing_backend else "complete_for_declared_scope",
    )
    omissions = {
        "items": [
            {
                "component_id": "payment-backend",
                "path": "backend/payments.php",
                "reason_code": "SOURCE_NOT_SUPPLIED",
                "required_for_scope": True,
                "evidence_refs": [],
            }
        ]
        if missing_backend
        else []
    }
    return {
        "snapshot_ref": snapshot["snapshot_id"],
        "omission_ref": "fake:survey-omissions",
        "rule_ref": "fake:survey-rules:1",
        "snapshot": snapshot,
        "omissions": omissions,
        "manifest": manifest,
        "files": dict(SOURCES),
        "rules": [
            {
                "rule_id": i,
                "needle": n,
                "family": f,
                "operation": o,
                "flow": flow,
                "target_operation": "unqualified",
            }
            for i, n, f, o, flow in RULES
        ],
        "shop_id": "synthetic-shop",
        "stack": {
            "lang": "php",
            "framework": "synthetic",
            "versions": {"php": "8.3"},
            "db": "none",
        },
        "required_lenses": required_lenses if required_lenses is not None else ["code"],
    }


def fixture_final():
    # Hand-checked source positions. Do not generate this answer using the component under test.
    positions = [
        ("nvp-create", "EC_NVP", "SetExpressCheckout", "checkout.php", 2),
        ("nvp-capture", "EC_NVP", "DoExpressCheckoutPayment", "checkout.php", 3),
        ("nvp-refund", "EC_NVP", "RefundTransaction", "refund.php", 2),
        ("ipn-notify", "IPN", "IPN validation indicator", "ipn.php", 2),
        ("checkout-v4", "CHECKOUT_JS_V4", "paypal.Button.render", "browser.js", 1),
    ]
    return {
        "shop_id": "synthetic-shop",
        "stack": {
            "lang": "php",
            "framework": "synthetic",
            "versions": {"php": "8.3"},
            "db": "none",
        },
        "lenses_run": ["code"],
        "touchpoints": [
            {
                "id": rule,
                "family": family,
                "operation": operation,
                "location": {"file": path, "line": line},
                "lenses": ["code"],
                "confidence": 0.5,
                "live": False,
                "paypal_only": False,
                "target": {"paypal_mapping_id": rule, "rest_op": "unqualified"},
            }
            for rule, family, operation, path, line in positions
        ],
        "money_flow": {
            "create": [{"file": "checkout.php", "line": 2}],
            "approve": [{"file": "browser.js", "line": 1}],
            "capture": [{"file": "checkout.php", "line": 3}],
            "refund": [{"file": "refund.php", "line": 2}],
            "notify": [{"file": "ipn.php", "line": 2}],
            "mark_paid": [],
            "recurring": [],
        },
        "recall_evidence": {"runtime_calls_total": 0, "matched_by_static": 0, "misses": []},
    }


SURVEYOR_CONTEXT_BYTES = 96000


class SurveyArtifacts(RuntimeArtifacts):
    def __init__(self, control, config, bundle):
        super().__init__(control, "surveyor_inventory")
        self.config, self.bundle = config, bundle

    def ticket(self, lease):
        ticket = super().ticket(lease)
        digest = self.bundle["snapshot"]["manifest_digest"]
        package_digest = content_digest(self.bundle)
        accepted = ticket.acceptance.model_copy(
            update={
                "source_manifest_digest": digest,
                "work_package_digest": package_digest,
            }
        )
        operation = ticket.operation.model_copy(
            update={
                "source_manifest_digest": digest,
                "observed_digest": digest,
                "work_package_digest": package_digest,
            }
        )
        return replace(ticket, acceptance=accepted, operation=operation)

    def role_inputs(self, lease):
        task = self.control.load(lease)
        subject = self.resolve("fake:survey-subject-manifest", lease.context_ref)
        if (subject.schema_id, subject.trust, subject.producer_identity_ref) != (
            "SubjectManifest/1",
            "collector_observed",
            "fake:collector",
        ):
            fail("DENIED subject manifest provenance")
        manifest = validate(
            "SubjectManifest/1",
            json.loads(self.read_artifact("fake:survey-subject-manifest", lease)),
        )
        if content_digest(manifest) != task.task.expected_subject:
            fail("DENIED subject manifest bytes")
        if task.task.input_refs != [self.bundle["snapshot_ref"], self.bundle["omission_ref"]]:
            fail("DENIED input refs")
        value = json.loads(encoded(self.bundle))
        for key, refkey, schema in [
            ("snapshot", "snapshot_ref", "SourceSnapshot/1"),
            ("omissions", "omission_ref", "OmissionManifest/1"),
        ]:
            descriptor = self.resolve(value[refkey], lease.context_ref)
            if (
                descriptor.schema_id != schema
                or descriptor.trust != "collector_observed"
                or descriptor.producer_identity_ref != "fake:collector"
            ):
                fail("DENIED input schema/trust")
            value[key] = json.loads(self.read_artifact(value[refkey], lease))
        return value

    def authorize_tool(self, lease, tool_id, arguments):
        task = self.control.load(lease)
        bundle = self.role_inputs(lease)
        authorize(task, bundle, tool_id, arguments)

    def model_context(self, lease, context, observation_refs):
        task = self.control.load(lease)
        inputs = self.role_inputs(lease)
        # Source bytes enter only as bounded tool observations, never as system policy.
        inputs.pop("files")
        envelope = {
            "task_context": context.model_dump(mode="json"),
            "policy": self.config["policy"],
            "prompt": self.config["prompt"],
            "inventory_inputs": inputs,
            "observations": [
                {
                    "ref": ref,
                    "digest": hashlib.sha256(self.raw(ref, lease)).hexdigest(),
                    "trust": "untrusted_tool_observation",
                    "value": json.loads(self.raw(ref, lease)),
                }
                for ref in observation_refs
            ],
        }
        if (content_digest(envelope["policy"]), content_digest(envelope["prompt"])) != (
            task.policy_digest,
            task.prompt_digest,
        ):
            fail("DENIED prompt/policy bytes")
        raw = encoded(envelope)
        reject_secret(raw)
        # Byte sanity bound only (4x the 24k-token turn cap): the model gateway's
        # exact provider token count is the binding input bound (continuation-05).
        if len(raw.encode()) > SURVEYOR_CONTEXT_BYTES:
            fail("MISSING_EVIDENCE required context capacity")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        ref = "fake:model-context:" + digest
        with self.store.transaction() as db:
            self.control._lease(db, lease)
            db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?)", (ref, raw))
        return ref, digest

    def inspect_output(self, task, context_ref):
        current = next(
            t for t in self.control.snapshot(RUN).tasks if t.task.task_id == task.task.task_id
        )
        if current.state != "succeeded" or len(current.output_refs) != 1:
            fail("MISSING_EVIDENCE accepted inventory")
        ref = current.output_refs[0]
        descriptor = self.resolve(ref, context_ref)
        if (
            descriptor.schema_id,
            descriptor.producer_identity_ref,
            descriptor.subject_digest,
            descriptor.input_digest,
        ) != (
            "RootMap/1",
            "fake:role:Surveyor",
            current.task.expected_subject,
            current.input_digest,
        ):
            fail("DENIED inspection binding")
        if descriptor.expires_at is not None and descriptor.expires_at <= self.clock():
            fail("EXPIRED inspection custody")
        with self.store.transaction() as db:
            row = db.execute("SELECT payload FROM artifacts WHERE ref=?", (ref,)).fetchone()
            return descriptor, json.loads(bytes(row[0]))


def authorize(task, bundle, tool, args):
    if task.task.role != "Surveyor" or tool not in task.task.allowed_tool_ids:
        fail("DENIED role/tool")
    if tool in {"source.read", "analysis.matches"}:
        if args.snapshot_ref != bundle["snapshot_ref"]:
            fail("DENIED source scope")
        if tool == "source.read":
            if args.path not in bundle["files"]:
                fail("DENIED path not in pinned manifest")
            if len(bundle["files"][args.path].encode()) > args.max_bytes:
                fail("MISSING_EVIDENCE required excerpt exceeds cap")
        elif args.rule_ref != bundle["rule_ref"]:
            fail("DENIED rule catalog")
    elif tool == "evidence.read":
        if args.ref != bundle["omission_ref"]:
            fail("DENIED evidence scope")
        if len(encoded(bundle["omissions"]).encode()) > args.max_bytes:
            fail("MISSING_EVIDENCE required evidence exceeds cap")
    else:
        fail("DENIED tool")


class SurveyTools(GuardedOfflineTools):
    def __init__(self, control, bundle):
        super().__init__(control)
        self.bundle = bundle

    def _validate(self, db, invocation):
        args = super()._validate(db, invocation)
        authorize(
            self.control._active(db, invocation.task_id), self.bundle, invocation.tool_id, args
        )
        return args

    def invoke(self, invocation):
        with self.store.transaction() as db:
            args = self._validate(db, invocation)
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace='tool' AND id=?", (invocation.invocation_id,)
            ).fetchone()
        if not exists:
            if invocation.tool_id == "source.read":
                text = self.bundle["files"][args.path]
                value = {
                    "kind": "source_excerpt",
                    "snapshot_ref": args.snapshot_ref,
                    "path": args.path,
                    "excerpt": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            elif invocation.tool_id == "analysis.matches":
                found = []
                for path, text in sorted(self.bundle["files"].items()):
                    for number, line in enumerate(text.splitlines(), 1):
                        for rule in self.bundle["rules"]:
                            if rule["needle"] in line:
                                found.append(
                                    {
                                        "rule_id": rule["rule_id"],
                                        "file": path,
                                        "line": number,
                                        "family": rule["family"],
                                        "operation": rule["operation"],
                                        "flow": rule["flow"],
                                    }
                                )
                if len(found) > args.max_matches:
                    fail("MISSING_EVIDENCE match cap")
                value = {
                    "kind": "matches",
                    "snapshot_ref": args.snapshot_ref,
                    "rule_ref": args.rule_ref,
                    "matches": found,
                    "truncated": False,
                }
            else:
                value = {"kind": "omissions", "ref": args.ref, "payload": self.bundle["omissions"]}
            self.script(invocation.invocation_id, {"payload": value})
        return super().invoke(invocation)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM tools").fetchone()[0]


class SurveyModel(ScriptedModelBroker):
    def __init__(self, control, bundle, final_payload=None):
        super().__init__(control)
        self.bundle = bundle
        self.final_payload = final_payload

    def turn(self, request):
        with self.store.transaction() as db:
            context = json.loads(
                db.execute(
                    "SELECT body FROM contexts WHERE ref=?", (request.context_ref,)
                ).fetchone()[0]
            )
            count = len(context["observations"])
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace='model' AND id=?", (request.turn_id,)
            ).fetchone()
        if not exists:
            if count < len(self.bundle["files"]):
                calls = [
                    {
                        "tool": "source.read",
                        "arguments": {
                            "snapshot_ref": self.bundle["snapshot_ref"],
                            "path": path,
                            "max_bytes": max(1, len(self.bundle["files"][path].encode())),
                        },
                    }
                    for path in sorted(self.bundle["files"])[count : count + 4]
                ]
                script = {"kind": "tool_calls", "calls": calls}
            elif count == len(self.bundle["files"]):
                script = {
                    "kind": "tool_calls",
                    "calls": [
                        {
                            "tool": "analysis.matches",
                            "arguments": {
                                "snapshot_ref": self.bundle["snapshot_ref"],
                                "rule_ref": self.bundle["rule_ref"],
                                "max_matches": 500,
                            },
                        },
                        {
                            "tool": "evidence.read",
                            "arguments": {
                                "ref": self.bundle["omission_ref"],
                                "max_bytes": 4096,
                            },
                        },
                    ],
                }
            else:
                script = {
                    "kind": "final",
                    "payload": (
                        self.final_payload if self.final_payload is not None else fixture_final()
                    ),
                }
            self.script(request.turn_id, script)
        return super().turn(request)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM model_turns").fetchone()[
                0
            ]


def create_surveyor_profile(path, *, configuration, clock=None, inputs=None):
    clock = clock or (lambda: datetime.now(UTC))
    bundle = inputs if inputs is not None else fixture_inputs()
    reject_secret(encoded(bundle))
    control = OfflineTaskControl(path, clock=clock)
    identity = {"fixture": "surveyor_inventory", "config": configuration, "bundle": bundle}
    with control.store.transaction() as db:
        row = db.execute(
            "SELECT body FROM scripts WHERE namespace='profile' AND id=?", (RUN,)
        ).fetchone()
        if row and json.loads(row[0]) != identity:
            fail("CONFLICT persisted survey profile")
        seeded = db.execute("SELECT 1 FROM runs").fetchone()
        if not row:
            if seeded:
                fail("CONFLICT existing run has another profile")
            db.execute("INSERT INTO scripts VALUES('profile',?,?)", (RUN, encoded(identity)))
    if not seeded:
        proposal = example("PlanProposal/1")
        spec = proposal["tasks"][0]
        # The exact source manifest and static scope are known before admission.
        subject_manifest = SubjectManifest(
            source_snapshot_refs=[bundle["snapshot_ref"]],
            source_tree_digest=bundle["snapshot"]["manifest_digest"],
            oci_manifest_digest=None,
            config_digest=None,
            runtime_profile_digest=content_digest("offline-source-inventory:1"),
            scope_digest=content_digest(
                {
                    k: bundle[k]
                    for k in (
                        "snapshot",
                        "omissions",
                        "rules",
                        "rule_ref",
                        "required_lenses",
                        "shop_id",
                        "stack",
                    )
                }
            ),
        )
        subject = content_digest(subject_manifest)
        spec.update(
            task_id="survey",
            output_slot="inventory",
            expected_subject=subject,
            input_refs=[bundle["snapshot_ref"], bundle["omission_ref"]],
            allowed_tool_ids=["source.read", "analysis.matches", "evidence.read"],
        )
        task = control.seed(RUN, validate("PlanProposal/1", proposal), "fake:survey-seed")[0]
        with control.store.transaction() as db:
            task = task.model_copy(
                update={
                    k: configuration[k]
                    for k in (
                        "prompt_ref",
                        "prompt_digest",
                        "policy_ref",
                        "policy_digest",
                    )
                }
            )
            control._save_task(db, task)
            for schema, payload, ref in [
                (
                    "SubjectManifest/1",
                    subject_manifest.model_dump(mode="json"),
                    "fake:survey-subject-manifest",
                ),
                ("SourceSnapshot/1", bundle["snapshot"], bundle["snapshot_ref"]),
                ("OmissionManifest/1", bundle["omissions"], bundle["omission_ref"]),
            ]:
                old_ref = control.artifacts._put(
                    db, task, schema, payload, subject, trust="collector_observed"
                )
                row = db.execute(
                    "SELECT descriptor FROM artifacts WHERE ref=?", (old_ref,)
                ).fetchone()
                descriptor = ArtifactDescriptor.model_validate_json(row[0]).model_copy(
                    update={
                        "ref": ref,
                        "producer_identity_ref": "fake:collector",
                    }
                )
                db.execute(
                    "UPDATE artifacts SET ref=?,descriptor=? WHERE ref=?",
                    (ref, encoded(descriptor), old_ref),
                )
    return OfflineProfile(
        control,
        SurveyArtifacts(control, configuration, bundle),
        SurveyModel(control, bundle, configuration.get("offline_final_payload")),
        SurveyTools(control, bundle),
        clock,
    )
