"""Summarise integrated agent runs into a Markdown results table (offline; reads evidence only).

Usage: python -m scripts.integrated_results [RUNS_DIR] > docs/engineering/plan5/ROUND1_RESULTS.md
"""

import collections
import json
import sys
from pathlib import Path

DEFAULT = Path.home() / "reports/goldgraft-agents-integration-20261112/runs"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    runs_dir = Path(argv[0]) if argv else DEFAULT
    results = []
    for f in sorted(runs_dir.glob("*/RESULT.json")):
        r = json.loads(f.read_text())
        r["_changes"] = (f.parent / "CHANGES.json").is_file()
        results.append(r)
    per = collections.defaultdict(
        lambda: {"runs": 0, "passed": 0, "usd": 0.0, "models": set(), "issues": []}
    )
    out = ["# Integrated agent runs — results", ""]
    out += [
        "Every row is one connected run with real model calls (scripted runner for builds and",
        "payment scenarios). Status follows the agent chain; side branches are reported per agent.",
        "",
        "| Run | Shop | Status | Agents passed | AI cost | Code written |",
        "|---|---|---|---|---|---|",
    ]
    total = 0
    for r in results:
        total += r.get("spent_micro_usd", 0)
        rows = r.get("tasks", [])
        roles = {t["role"] for t in rows}
        passed = {t["role"] for t in rows if t.get("passed")}
        out.append(
            f"| {r['run_id']} | {r.get('shop', '')} | {r['status']} "
            f"| {len(passed)} of {len(roles)} "
            f"| ${r.get('spent_micro_usd', 0) / 1e6:.3f} | {'yes' if r['_changes'] else 'no'} |"
        )
        for t in rows:
            p = per[t["role"]]
            p["runs"] += 1
            p["passed"] += bool(t.get("passed"))
            p["usd"] += (t.get("cost_micro_usd") or 0) / 1e6
            if t.get("model"):
                p["models"].add(t["model"])
            if not t.get("passed") and t.get("issue"):
                p["issues"].append(t["issue"])
    models = collections.defaultdict(lambda: [0, 0])
    for r in results:
        for t in r.get("tasks", []):
            m = models[t.get("model") or "none"]
            m[0] += 1
            m[1] += t.get("cost_micro_usd") or 0
    out += ["", f"Total AI cost of these runs: ${total / 1e6:.6f}", ""]
    out += ["| Model | Agent steps | AI cost | Share |", "|---|---|---|---|"]
    for name, (steps, micro) in sorted(models.items(), key=lambda kv: -kv[1][1]):
        share = micro / total if total else 0
        out.append(f"| {name} | {steps} | ${micro / 1e6:.3f} | {share:.0%} |")
    out += [
        "",
        "(haiku = claude-haiku-5-5 with up to 4 turns; haiku8 = the same model with up to 8 turns;",
        "sonnet = claude-sonnet-5-5. Run totals equal the sum of step costs, which equal the",
        "ledger's change over these runs.)",
        "",
    ]
    out += [
        "| Agent | Passed / attempts | Models | AI cost | Holds (codes) |",
        "|---|---|---|---|---|",
    ]
    for role, p in sorted(per.items()):
        issues = ", ".join(f"{k}×{v}" for k, v in collections.Counter(p["issues"]).items()) or "—"
        out.append(
            f"| {role} | {p['passed']}/{p['runs']} | {', '.join(sorted(p['models']))} "
            f"| ${p['usd']:.3f} | {issues} |"
        )
    out += [
        "",
        "Hold codes: DENIED = a deterministic gate refused (small cohort, no consent: correct);",
        "INVALID_MODEL_OUTPUT / TURN_LIMIT = the model's answer was refused (counts toward the",
        "two-strike Sonnet rule); MISSING_EVIDENCE = required input or reading incomplete.",
    ]
    print("\n".join(out))


if __name__ == "__main__":
    main()
