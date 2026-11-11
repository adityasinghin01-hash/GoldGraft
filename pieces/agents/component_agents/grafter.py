"""Sole isolated candidate writer; no host writes or self-approved success."""

import re
from typing import Literal

from goldgraft_contracts.agents import ChangeListV2
from goldgraft_contracts.plan5_common import Digest, P5Record, Ref, RelativePath, content_digest
from goldgraft_contracts.survey import TargetPlan
from pydantic import Field, StrictBool

from ..component import metadata
from .architect import sample as architect_sample
from .execution import Catalog, valid_metadata


class Input(P5Record):
    workspace_ref: Ref
    source_ref: Ref
    expected_tree: Digest
    files: dict[RelativePath, str] = Field(min_length=1, max_length=4)
    allowed_paths: list[RelativePath] = Field(min_length=1, max_length=4)
    replacements: dict[RelativePath, str] | None = Field(default=None, min_length=1, max_length=4)
    target_plan: TargetPlan
    catalog: Catalog
    required_symbol: str
    exclusive_writer: StrictBool
    repair_round: int = Field(ge=0, le=2, strict=True)
    failure_fingerprint: Digest | None
    previous_failure_fingerprint: Digest | None
    collector_receipt_fault: Literal["none", "wrong_tree", "missing_snapshot"] = "none"
    # Authoring mode (12 Nov): the model writes the new code itself from the target plan and the
    # installed library's API; no replacement content is given. Deterministic review judges it.
    author: StrictBool = False
    api_reference: str | None = Field(default=None, max_length=4000)
    forbidden_calls: list[str] = Field(default_factory=list, max_length=8)
    paid_marker: str | None = None


def admit(task, data):
    if (
        not data.exclusive_writer
        or task.task.workspace_ref != data.workspace_ref
        or content_digest(data.files) != data.expected_tree
    ):
        raise ValueError("DENIED exclusive writer/CAS")
    if data.author:
        if data.replacements is not None or not data.api_reference:
            raise ValueError("DENIED authoring needs the API reference and no given replacements")
    elif data.replacements is None:
        raise ValueError("MISSING_EVIDENCE replacements")
    paths = set(data.allowed_paths if data.author else data.replacements)
    if not paths <= set(data.allowed_paths) <= set(data.files):
        raise ValueError("DENIED allowed candidate paths")
    if any(
        p.startswith(("tests/", "contracts/", "docs/", "."))
        or "test" in p.lower()
        or "rule" in p.lower()
        for p in paths
    ):
        raise ValueError("DENIED test/normative edit")
    if (
        not data.catalog.qualified_fixture
        or data.required_symbol not in data.catalog.installed_symbols
    ):
        raise ValueError("MISSING_EVIDENCE installed symbol")
    if not data.target_plan.items or any(not i.paypal_only for i in data.target_plan.items):
        raise ValueError("DENIED plan scope")
    if any(i.target_op not in data.catalog.installed_symbols for i in data.target_plan.items):
        raise ValueError("MISSING_EVIDENCE installed plan operation")
    if data.repair_round and (
        data.failure_fingerprint is None
        or data.failure_fingerprint == data.previous_failure_fingerprint
    ):
        raise ValueError("MISSING_EVIDENCE new independent failure")


def schemas(operation, data):
    return ["ChangeList/2"]


def reference_patch(data):
    """Offline stub for the scripted model only (never shown to a real model)."""
    symbols = sorted({i.target_op for i in data.target_plan.items})
    out = {}
    for n, path in enumerate(sorted(data.allowed_paths)):
        body = "<?php\nrequire_once __DIR__ . '/../lib/paypal_orders.php';\n// offline stub\n"
        if n == 0:
            body += "".join(f"$r = {s}();\n" for s in symbols)
            body += "if ($r['capture_status'] === 'COMPLETED') { $paid = true; }\n"
        out[path] = body
    return out


def requests(task, data):
    return [
        *[
            dict(
                tool="source.read",
                arguments=dict(snapshot_ref=data.source_ref, path=p, max_bytes=4096),
            )
            for p in data.files
        ],
        dict(
            tool="dependency.inspect",
            arguments=dict(
                recipe_ref=data.catalog.recipe_ref,
                package=data.catalog.package,
                version=data.catalog.version,
            ),
        ),
        dict(
            tool="candidate.patch",
            arguments=dict(
                workspace_ref=data.workspace_ref,
                expected_tree=data.expected_tree,
                patch_ref="inline:patch",
            ),
            **(
                {
                    "authored": {
                        "workspace_ref": data.workspace_ref,
                        "expected_tree": data.expected_tree,
                    },
                    # Only the offline scripted model sends this stub; a real model writes its own.
                    "patch": reference_patch(data),
                }
                if data.author
                else {"patch": data.replacements}
            ),
        ),
    ]


def synthesize(task, data, packet, observations):
    receipt = observations[-1]["value"]["payload"]
    if not receipt.get("snapshot_ref"):
        raise ValueError("MISSING_EVIDENCE collector snapshot")
    value = metadata(task, packet)
    value.update(
        provenance="snapshot",
        branch=None,
        baseline_snapshot_ref=data.source_ref,
        candidate_snapshot_ref=receipt["snapshot_ref"],
        patch_digest=receipt["patch_digest"] if data.author else content_digest(data.replacements),
        changes=[
            dict(
                plan_item_ids=[i.touchpoint for i in data.target_plan.items],
                summary="Payment-only isolated snapshot patch; independent build/proof required.",
                commit=None,
            )
        ],
        open_item_ids=[],
    )
    return [dict(schema="ChangeList/2", payload=value)]


def check_authored(data, patch):
    """Deterministic judgement of model-written code (no equality to an answer key)."""
    from ..source_inventory import reject_secret

    if not isinstance(patch, dict) or not patch or set(patch) - set(data.allowed_paths):
        raise ValueError("DENIED authored paths")
    merged = {**data.files, **patch}
    symbols = {i.target_op for i in data.target_plan.items}
    for path, text in patch.items():
        if not isinstance(text, str) or not text.lstrip().startswith("<?php") or len(text) > 8192:
            raise ValueError("DENIED authored file shape " + path)
        reject_secret(text)
        if any(bad in text for bad in data.forbidden_calls):
            raise ValueError("DENIED old PayPal call left in " + path)
        if any(s + "(" in text for s in symbols) and "paypal_orders.php" not in text:
            raise ValueError("MISSING_EVIDENCE installed library not loaded in " + path)
    code = "\n".join(patch.values())
    missing = sorted(s for s in symbols if s + "(" not in code)
    if missing:
        raise ValueError("MISSING_EVIDENCE planned operations not called: " + ", ".join(missing))
    if data.paid_marker and data.paid_marker not in code:
        raise ValueError("DENIED money rule: paid only on a completed capture")
    untouched = set(data.files) - set(patch)
    if any(any(bad in data.files[p] for bad in data.forbidden_calls) for p in untouched):
        raise ValueError("MISSING_EVIDENCE an allowed file still uses the old API")
    return merged


def review(task, data, packet, outputs, observations):
    receipt = observations[-1]["value"]["payload"]
    if data.author:
        files = check_authored(data, receipt.get("patch"))
        if receipt.get("patch_digest") != content_digest(receipt.get("patch")):
            raise ValueError("DENIED collector patch digest")
    else:
        files = {**data.files, **data.replacements}
    want = (
        synthesize(task, data, packet, observations)[0]["payload"]
        if receipt.get("snapshot_ref")
        else {}
    )
    got = ChangeListV2.model_validate(outputs[0]["payload"]).model_dump(mode="json")
    if (
        receipt.get("tree") != content_digest(files)
        or receipt.get("synthetic_only") is not True
        or not receipt.get("snapshot_ref")
        or (not data.author and receipt.get("patch_digest") != content_digest(data.replacements))
        or not valid_metadata(got, want)
        or any(
            got[k] != want[k]
            for k in (
                "provenance",
                "branch",
                "baseline_snapshot_ref",
                "candidate_snapshot_ref",
                "patch_digest",
                "open_item_ids",
            )
        )
        or len(got["changes"]) != 1
        or got["changes"][0]["commit"] is not None
        or sorted(got["changes"][0]["plan_item_ids"]) != sorted(want["changes"][0]["plan_item_ids"])
        or not 1 <= len(got["changes"][0]["summary"]) <= 400
        or re.search(r"\b(deployed|published|verified)\b", got["changes"][0]["summary"], re.I)
    ):
        raise ValueError("DENIED collector patch/snapshot lineage")


INLINE = {"candidate.patch": {"patch_ref": ("patch", "candidate_patch")}}
PROGRESS = True


def route(data):
    # Writing real code needs Sonnet's output room; replay of given replacements fits Haiku.
    return "sonnet" if data.author or len(data.files) >= 4 else "haiku8"


def facts(task, data):
    if data.author:
        return {
            "max_bytes": 4096,
            "installed_library_api": data.api_reference,
            "forbidden_after_patch": data.forbidden_calls,
            # Copy fields for ChangeList/2 (identifiers, not code): exact ids and a size bound.
            "plan_item_ids": sorted(i.touchpoint for i in data.target_plan.items),
            "summary_max_chars": 300,
            "call_policy": "Read every source file (follow unread_reads; max four reads per "
            "response) and dependency.inspect with the catalog's recipe_ref, package, version. "
            "Then WRITE the new checkout yourself: for every target_plan item, replace the old "
            "PayPal call in the files with the installed library operation named by target_op, "
            "following installed_library_api exactly. Keep each endpoint's HTTP behaviour and "
            "JSON response keys; keep unrelated lines unchanged; load the library with "
            "require_once instead of the old NVP client; no forbidden_after_patch text may remain "
            "in a file you send. Money rule: mark an order PAID only when capture_status is "
            "'COMPLETED'; store PENDING otherwise. Then call candidate.patch alone with "
            "workspace_ref, expected_tree and an inline patch object {path: full new file "
            "content} for every file you changed (start each with <?php). Never mint patch_ref. "
            "Accept only a synthetic collector receipt with snapshot_ref and patch_digest; "
            "otherwise report_hold. Copy receipt snapshot_ref and patch_digest into ChangeList/2, "
            "snapshot provenance, null branch/commits, baseline=source_ref, one change covering "
            "every target_plan touchpoint (plan_item_ids exactly as given), open_item_ids empty. "
            "Use reference_metadata. The change summary is ONE short plain sentence, at most "
            "summary_max_chars characters; avoid the words deployed, published and verified.",
        }
    return {
        "max_bytes": 4096,
        "call_policy": "Read every source file and dependency.inspect using the catalog's "
        "recipe_ref, package, version. Follow unread_reads; max four reads per response. "
        "Then call candidate.patch alone with workspace_ref, expected_tree and the exact "
        "replacements map inline as patch. Never mint patch_ref. Accept only a synthetic "
        "collector receipt with a snapshot_ref, patch_digest, and tree matching its manifest "
        "source_tree_digest; otherwise report_hold. Copy receipt snapshot_ref and patch_digest "
        "into ChangeList/2, use snapshot provenance, null branch/commits, baseline=source_ref, "
        "one change covering every target_plan touchpoint, open_item_ids empty. Use the "
        "plan_item_ids from target_plan.items[].touchpoint (never mapping_id). Use the "
        "reference_metadata. Summarize only isolated payment edits; independent build/proof "
        "remains required. Literal wording guard: avoid deployed, published and verified. "
        "No baseline writes, test edits, live host changes or claims of proof.",
    }


def inspect(outputs):
    v = outputs[0]["payload"]
    return dict(
        candidate_snapshot_ref=v["candidate_snapshot_ref"],
        patch_digest=v["patch_digest"],
        provenance=v["provenance"],
        git_commit=None,
        independent_build_and_proof="REQUIRED",
        merchant_writes="NONE",
    )


def sample(operation):
    a = architect_sample("architect")
    plan = dict(
        path="REWRITE",
        items=[
            dict(
                touchpoint="tp-capture",
                target_op="capture_order",
                mapping_id="fixture-map-capture",
                delta_ids=[],
                paypal_only=True,
            )
        ],
        target_experience=["ORDERS_V2"],
        origin_rules=["captured-before-paid"],
        order=["READ_BOTH", "NEW_FLOWS_BEHIND_SWITCH", "CLEANUP"],
        handoff=[],
        deltas=[],
    )
    files = {"checkout.php": "<?php legacy_capture();"}
    return dict(
        workspace_ref="fixture:candidate-workspace",
        source_ref="fixture:baseline",
        expected_tree=content_digest(files),
        files=files,
        allowed_paths=["checkout.php"],
        replacements={"checkout.php": "<?php capture_order();"},
        target_plan=plan,
        catalog=a["catalog"],
        required_symbol="capture_order",
        exclusive_writer=True,
        repair_round=0,
        failure_fingerprint=None,
        previous_failure_fingerprint=None,
    )
