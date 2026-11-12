"""The socket a shop recipe plugs into (Vijay's VJ01-VJ05 piece).

A recipe folder ``pieces/shops/<shop_id>/`` holds only data and contract-typed code:

    goldgraft-shop.yaml     ShopPack/1 (existing shared format)
    scenarios/<ID>.json     Scenario/1 for every id in scenarios_supported
    contract.json           Contract/1, the normative money rules
    target_plan.json        TargetPlan/1, the reference upgrade plan
    source/                 the shop source the recipe runs (licence/notice beside it)
    recipe.py               ``execute(run_dir, output, *, php)`` and, when ready,
                            ``state_recipe`` / ``finalisation_recipe`` /
                            ``exit_check_recipe`` (VJ03-VJ05); absent ones are holds

``execute`` runs OLD, OLD_TWIN and NEW for every scenario and writes one
RawCapture/1 per pair plus REPORT.json with their digests and honest
qualification flags. ``conformance`` is the one check a recipe must pass;
``RecipeProof`` re-checks the bytes and judges them with Singhal's judge.
The reference PHP shop is wired through the same socket as a labelled
stand-in, so Vijay's pack fits the connected run without code changes.
"""

import hashlib
import importlib.util
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from goldgraft_contracts.proof import Grade
from goldgraft_contracts.registry import validate

from integration.local_shop import ROOT, order_listing
from pieces.proof.proof import Proof

VARIANTS = ("OLD", "OLD_TWIN", "NEW")
QUALIFICATION_FLAGS = (
    "real_payment_qualified",
    "isolated_execution_qualified",
    "merchant_delivery_qualified",
)
LATER_GATES = ("state_recipe", "finalisation_recipe", "exit_check_recipe")


@dataclass(frozen=True)
class ShopRecipe:
    shop_id: str
    provenance: str  # "reference_stand_in" or "vijay"
    folder: Path
    source_dir: Path
    pack: object  # ShopPack/1
    scenarios: dict  # id -> Scenario/1, in scenarios_supported order
    contract: object  # Contract/1
    contract_bytes: bytes
    target_plan: object  # TargetPlan/1
    execute: Callable
    # Optional shop-specific hook: (scenario, captures, verdict, report) -> verdict.
    post_judge: Callable | None = None
    later_gates: dict = field(default_factory=dict)  # gate -> callable or None

    def holds(self) -> list[str]:
        return [
            f"{gate}: not supplied by this recipe"
            for gate in LATER_GATES
            if self.later_gates.get(gate) is None
        ]


def _load_common(folder: Path):
    pack = validate("ShopPack/1", json.loads((folder / "goldgraft-shop.yaml").read_bytes()))
    contract_bytes = (folder / "contract.json").read_bytes()
    scenarios = {
        sid: validate("Scenario/1", json.loads((folder / "scenarios" / f"{sid}.json").read_bytes()))
        for sid in pack.scenarios_supported
    }
    return (
        pack,
        scenarios,
        validate("Contract/1", json.loads(contract_bytes)),
        contract_bytes,
        validate("TargetPlan/1", json.loads((folder / "target_plan.json").read_bytes())),
    )


def reference_recipe() -> ShopRecipe:
    """The vendored MIT legacy PHP shop: a stand-in until Vijay's qualified pack lands."""
    from scripts.live_local_shop_proof import check

    shop = ROOT / "fixtures/shops/legacy-php-shop"
    proof_ref = ROOT / "fixtures/proof/legacy-php-shop"
    pack = validate("ShopPack/1", json.loads((shop / "goldgraft-shop.yaml").read_bytes()))
    contract_bytes = (proof_ref / "contract.json").read_bytes()

    def parity(scenario, captures, verdict, report):
        if scenario != "PARITY_EXTRA" or "order_listing_parity_passed" not in report:
            return verdict
        listings = [order_listing(c) for c in captures]
        if not listings[0] == listings[1] == listings[2]:
            verdict.grade = Grade.PROBLEM
            verdict.parity_diff.append({"feature": "order listing", "observations": listings})
        return verdict

    return ShopRecipe(
        shop_id=pack.shop_id,
        provenance="reference_stand_in",
        folder=shop,
        source_dir=shop / "src",
        pack=pack,
        scenarios={
            sid: validate(
                "Scenario/1", json.loads((proof_ref / "scenarios" / f"{sid}.json").read_bytes())
            )
            for sid in pack.scenarios_supported
        },
        contract=validate("Contract/1", json.loads(contract_bytes)),
        contract_bytes=contract_bytes,
        target_plan=validate(
            "TargetPlan/1", json.loads((proof_ref / "target_plan.json").read_bytes())
        ),
        execute=check,
        post_judge=parity,
        later_gates={gate: None for gate in LATER_GATES},
    )


def load_recipe(folder: Path) -> ShopRecipe:
    """Load a recipe from pieces/shops/<shop_id>/ (Vijay's piece)."""
    folder = Path(folder)
    pack, scenarios, contract, contract_bytes, target_plan = _load_common(folder)
    spec = importlib.util.spec_from_file_location(
        f"goldgraft_shop_{pack.shop_id}", folder / "recipe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return ShopRecipe(
        shop_id=pack.shop_id,
        provenance="vijay",
        folder=folder,
        source_dir=folder / "source",
        pack=pack,
        scenarios=scenarios,
        contract=contract,
        contract_bytes=contract_bytes,
        target_plan=target_plan,
        execute=module.execute,
        post_judge=getattr(module, "post_judge", None),
        later_gates={gate: getattr(module, gate, None) for gate in LATER_GATES},
    )


def discover_recipes() -> list[ShopRecipe]:
    """The reference stand-in plus every recipe folder under pieces/shops/."""
    found = [reference_recipe()]
    for folder in sorted((ROOT / "pieces/shops").glob("*/recipe.py")):
        found.append(load_recipe(folder.parent))
    return found


def _digest(path: Path, expected: str):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"recording drift: {path.name}")
    return json.loads(raw)


class RecipeProof:
    """Re-check every recorded byte against REPORT digests, then judge each scenario."""

    def __init__(self, run_dir: Path, recipe: ShopRecipe, *, plan=None):
        self.run_dir = Path(run_dir)
        evidence = self.run_dir / "local-proof"
        report = json.loads((evidence / "REPORT.json").read_bytes())
        self.report = report
        if report["run_id"] != self.run_dir.name:
            raise ValueError("recording run does not match its folder")
        if any(report.get(flag) is not False for flag in QUALIFICATION_FLAGS):
            raise ValueError("a recipe may not self-declare provider/isolation qualification")
        if (
            report.get("normative_contract_sha256")
            != hashlib.sha256(recipe.contract_bytes).hexdigest()
        ):
            raise ValueError("recordings were judged against a different contract")
        names = {f"{s}.{v}.json" for s in recipe.scenarios for v in VARIANTS}
        if set(report["capture_sha256"]) != names:
            raise ValueError("recording set incomplete")
        plan = plan or recipe.target_plan
        proof = Proof()
        self.rows, self.streams, self.capture_run_id = [], {}, None
        for scenario in recipe.scenarios:
            captures = []
            for variant in VARIANTS:
                name = f"{scenario}.{variant}.json"
                capture = validate(
                    "RawCapture/1", _digest(evidence / name, report["capture_sha256"][name])
                )
                if (
                    capture.graft_id != self.run_dir.name
                    or capture.scenario_id != scenario
                    or capture.variant != variant
                    or (self.capture_run_id or capture.run_id) != capture.run_id
                    or not capture.run_id.startswith(self.run_dir.name)
                ):
                    raise ValueError("recording subject mismatch")
                self.capture_run_id = capture.run_id
                captures.append(capture)
            streams = [proof.to_cmel(c) for c in captures]
            self.streams[scenario] = streams
            verdict = proof.judge(
                *streams, recipe.contract, plan, old_capture=captures[0], new_capture=captures[2]
            )
            if recipe.post_judge is not None:
                verdict = recipe.post_judge(scenario, captures, verdict, report)
            self.rows.append({"scenario": recipe.scenarios[scenario], "verdict": verdict})


def conformance(
    recipe: ShopRecipe, workdir: Path, *, agent_run_dir: Path, php: str = "php"
) -> dict:
    """The one check a shop recipe must pass to plug in. Returns failures and holds.

    agent_run_dir supplies the agents' candidate (RESULT/CHANGES/OUTPUTS) that the
    recipe executes as NEW; OLD and OLD_TWIN run the recipe's own source.
    """
    failures, holds = [], recipe.holds()
    if recipe.pack.shop_id != recipe.shop_id:
        failures.append("pack shop_id differs from recipe shop_id")
    if not recipe.source_dir.is_dir() or not any(recipe.source_dir.rglob("*")):
        failures.append("source folder missing or empty")
    if not any(any(recipe.folder.glob(p)) for p in ("LICENSE*", "NOTICE*", "source/LICENSE*")):
        failures.append("no licence or notice beside the source")
    if list(recipe.scenarios) != list(recipe.pack.scenarios_supported):
        failures.append("scenarios do not match scenarios_supported")
    for sid, scenario in recipe.scenarios.items():
        if scenario.id != sid:
            failures.append(f"scenario file {sid} declares id {scenario.id}")
    rule_ids = {r.id for r in recipe.contract.rules}
    covered = {r for s in recipe.scenarios.values() for r in s.rules}
    if covered - rule_ids:
        failures.append(f"scenarios name unknown rules {sorted(covered - rule_ids)}")
    holds += [f"rule {r}: no scenario exercises it" for r in sorted(rule_ids - covered)]
    run_dir = Path(workdir) / f"conformance-{recipe.shop_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    for name in ("RESULT.json", "CHANGES.json", "OUTPUTS.json"):
        if (Path(agent_run_dir) / name).exists():
            (run_dir / name).write_bytes((Path(agent_run_dir) / name).read_bytes())
        else:
            failures.append(f"agent run lacks {name}")
    if not failures:
        try:
            recipe.execute(run_dir, run_dir / "local-proof", php=php)
            proof = RecipeProof(run_dir, recipe)
            graded = {str(r["verdict"].grade) for r in proof.rows}
            if not graded:
                failures.append("no scenario was judged")
        except Exception as exc:  # The recipe's own failure is the conformance answer.
            failures.append(f"execute/judge failed: {exc}")
    return {
        "shop_id": recipe.shop_id,
        "provenance": recipe.provenance,
        "conforms": not failures,
        "failures": failures,
        "holds": holds,
    }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Check every shop recipe against the socket")
    parser.add_argument("--agent-run", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--php", default="php")
    args = parser.parse_args(argv)
    results = [
        conformance(r, args.workdir, agent_run_dir=args.agent_run, php=args.php)
        for r in discover_recipes()
    ]
    print(json.dumps(results, indent=2))
    return 0 if all(r["conforms"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
