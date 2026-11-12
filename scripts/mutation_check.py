"""Plant known money bugs in a run's AI-written code and count how many the code review catches.

Offline and free (no model calls). For each integrated run with a CHANGES.json, every mutant below
is applied to the Grafter's real output; the Grafter's deterministic review (check_authored) then
judges the mutated patch. A mutant is "caught" when the review refuses it. A mutant whose pattern
is not in that run's code is "not applicable" and is not counted.

Usage: python -m scripts.mutation_check [RUNS_DIR] [--write]
  --write  also saves MUTATIONS.json next to each run's CHANGES.json (the app shows it).
"""

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

from pieces.agents.component_agents.grafter import check_authored
from pieces.agents.integrated import FORBIDDEN_AFTER

DEFAULT = Path.home() / "reports/goldgraft-agents-integration-20261112/runs"
PAID_MARKER = "COMPLETED"
FAKE_SECRET = "EKq9xV3mN7pL2wR8tY4uB6cD1fG5hJ0kZ2sQ"


def _capture(files):
    return next((p for p, t in files.items() if "gg_capture_order(" in t), None)


def _file_with(token):
    return lambda files: next((p for p, t in files.items() if token in t), None)


def _sub(pattern, repl, count=0):
    def apply(text):
        changed, n = re.subn(pattern, repl, text, count=count)
        return changed if n else None

    return apply


def _ignore_webhook_result(text):
    m = re.search(r"(\$\w+)\s*=\s*gg_verify_webhook\s*\(", text)
    if not m:
        return None
    var = re.escape(m.group(1))
    head, tail = text[: m.end()], text[m.end() :]
    changed, n = re.subn(rf"(?<![\w$]){var}(?!\w)", "true", tail)
    return head + changed if n else None


def _insert_secret(text):
    if not text.lstrip().startswith("<?php"):
        return None
    return text.replace("<?php", f"<?php\ndefine('PAYPAL_CLIENT_SECRET', '{FAKE_SECRET}');", 1)


# id, money rule it breaks, plain description, which file, how to mutate it
MUTANTS = [
    (
        "M1",
        "paid-only-when-completed",
        "A PENDING capture is marked PAID",
        _capture,
        _sub(r"===?\s*(['\"])COMPLETED\1", "!== 'COMPLETED'"),
    ),
    (
        "M2",
        "no-old-paypal",
        "The old NVP capture call is left in",
        _capture,
        _sub(r"gg_capture_order\s*\(", "paypal_nvp('DoExpressCheckoutPayment', ", count=1),
    ),
    (
        "M3",
        "verify-webhooks",
        "The webhook signature check is removed",
        _file_with("gg_verify_webhook("),
        _sub(r"gg_verify_webhook\s*\([^;]*\)", "true", count=1),
    ),
    (
        "M4",
        "refund-only-paid",
        "An order that was never paid can be refunded",
        _file_with("gg_refund_capture("),
        _sub(r"!==?\s*(['\"])PAID\1", "=== 'NEVER'"),
    ),
    (
        "M5",
        "library-loaded",
        "The Orders v2 library is no longer loaded",
        _capture,
        _sub(r"(?m)^.*paypal_orders\.php.*\n", "", count=1),
    ),
    (
        "M6",
        "no-secrets-in-code",
        "A PayPal client secret is pasted into the code",
        _capture,
        _insert_secret,
    ),
    (
        "M7",
        "verify-webhooks",
        "The webhook is checked but the result is ignored",
        _file_with("gg_verify_webhook("),
        _ignore_webhook_result,
    ),
]


def review_data(run_dir):
    changes = json.loads((run_dir / "CHANGES.json").read_text())
    outputs = json.loads((run_dir / "OUTPUTS.json").read_text())
    authored = {f["path"]: f for f in changes["files"] if f["author"] == "model"}
    plan = (outputs.get("architect") or outputs.get("architect-retry1"))[0]["payload"]
    data = SimpleNamespace(
        allowed_paths=sorted(authored),
        files={p: f["before"] for p, f in authored.items()},
        target_plan=SimpleNamespace(
            items=[SimpleNamespace(target_op=i["target_op"]) for i in plan["items"]]
        ),
        forbidden_calls=list(FORBIDDEN_AFTER),
        paid_marker=PAID_MARKER,
    )
    return data, {p: f["after"] for p, f in authored.items()}


def judge(data, patch):
    try:
        check_authored(data, patch)
        return None
    except ValueError as error:
        return str(error)


def check_run(run_dir):
    data, patch = review_data(run_dir)
    baseline = judge(data, patch)
    rows = []
    for mid, rule, what, pick, mutate in MUTANTS:
        path = pick(patch)
        mutated = mutate(patch[path]) if path else None
        if mutated is None or mutated == patch.get(path):
            rows.append({"id": mid, "rule": rule, "what": what, "file": path, "applied": False})
            continue
        refusal = judge(data, {**patch, path: mutated})
        rows.append(
            {
                "id": mid,
                "rule": rule,
                "what": what,
                "file": path,
                "applied": True,
                "caught": refusal is not None,
                "refusal": refusal,
            }
        )
    applied = [r for r in rows if r["applied"]]
    return {
        "run_id": run_dir.name,
        "original_passes_review": baseline is None,
        "original_refusal": baseline,
        "planted": len(applied),
        "caught": sum(r["caught"] for r in applied),
        "mutants": rows,
        "note": "Planted bugs in the Grafter's real code, judged by the deterministic code "
        "review only (not the independent proof, not a payment run).",
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    write = "--write" in argv
    args = [a for a in argv if a != "--write"]
    runs = Path(args[0]) if args else DEFAULT
    for changes in sorted(runs.glob("*/CHANGES.json")):
        result = check_run(changes.parent)
        if write:
            (changes.parent / "MUTATIONS.json").write_text(json.dumps(result, indent=2) + "\n")
        missed = [m["id"] for m in result["mutants"] if m["applied"] and not m["caught"]]
        print(
            f"{result['run_id']:40s} original passes: {result['original_passes_review']!s:5s} "
            f"caught {result['caught']}/{result['planted']}  missed: {', '.join(missed) or '-'}"
        )


if __name__ == "__main__":
    main()
