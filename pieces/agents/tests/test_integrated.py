"""Offline checks for the integrated thirteen-role run policy (no model, no network)."""

import pytest
from goldgraft_contracts.plan5_common import content_digest

from pieces.agents import integrated
from pieces.agents.scheduler import tick

SURVEY = {
    "accepted": True,
    "output_ref": "fake:root-map:legacy-php-shop",
    "source_digest": content_digest("legacy-php-shop-source"),
}


def _run(path, run):
    p = integrated.create(path)
    w = integrated.WithRun(p, run)
    for _ in range(4):
        if tick(p.run_ref, p.clock(), w).claimed == 0:
            break
    return p, {t.task.task_id: t for t in p.control.snapshot(p.run_ref).tasks}


def test_gardener_admits_only_the_survey_and_the_chain_waits_for_it(tmp_path):
    p, tasks = _run(tmp_path / "b.sqlite", {})
    assert list(tasks) == [integrated.GARDENER]
    assert tasks[integrated.GARDENER].state == "succeeded"
    assert integrated.admitted_survey(p)["node"]["task_id"] == integrated.SURVEY
    assert integrated.advance(p.run_ref, integrated.WithRun(p, {})) is None  # no survey yet


def test_rejected_survey_never_admits_the_baseline(tmp_path):
    _, tasks = _run(tmp_path / "b.sqlite", {"survey": dict(SURVEY, accepted=False)})
    assert integrated.BASE not in tasks


def test_full_chain_and_side_branches_complete_offline(tmp_path):
    run = {"survey": SURVEY, "learning_consent": True, "source_rights": True}
    p, tasks = _run(tmp_path / "b.sqlite", run)
    assert [s[0] for s in integrated.ALL_STAGES if tasks[s[0]].state != "succeeded"] == []
    roles = {t.task.role for t in tasks.values()} | {"Surveyor", "Herald"}
    assert roles == set(integrated.ROLES) and len(roles) == 13


def test_baseline_builds_exactly_the_surveyed_source(tmp_path):
    p, tasks = _run(tmp_path / "b.sqlite", {"survey": SURVEY})
    data = (
        p.artifacts.role_inputs_for(integrated.BASE)
        if hasattr(p.artifacts, "role_inputs_for")
        else None
    )
    edges = {e["task"]: e for e in integrated.edges(p)}
    assert edges[integrated.BASE]["dependencies"] == [integrated.GARDENER]
    assert tasks["baseline-old"].state == "succeeded"
    # every chain task consumed at least one committed predecessor output
    for task_id, *_ in integrated.ALL_STAGES[1:]:
        assert edges[task_id]["predecessor_outputs_consumed"], task_id
    assert data is None or data["source_tree_digest"] == SURVEY["source_digest"]


def test_sentinel_events_are_scoped_to_this_run(tmp_path):
    run = {"survey": SURVEY, "hostile_fingerprint_seed": "x"}
    p, tasks = _run(tmp_path / "b.sqlite", run)
    data = integrated.stage_data(p, "sentinel-audit", "Sentinel", "audit", run)
    head = tasks[integrated.GARDENER]
    assert {(e["case_id"], e["run_id"]) for e in data["events"]} == {(head.case_id, head.run_id)}
    assert data["events"][-1]["kind"] == "secret_attempt"


@pytest.mark.parametrize(
    "codes,expected",
    [
        ([], "haiku8"),
        (["INVALID_MODEL_OUTPUT"], "haiku8"),
        (["INVALID_MODEL_OUTPUT", "TURN_LIMIT"], "sonnet"),
        (["MISSING_EVIDENCE", "DENIED", "BUDGET_EXHAUSTED"], "haiku8"),  # never escalates
    ],
)
def test_two_named_haiku_failures_move_a_shape_to_sonnet(codes, expected):
    routing = {}
    for code in codes:
        integrated.record_failure(routing, "Explorer", "run_scenario", "haiku8", code)
    data = integrated.implementation("Explorer").sample("run_scenario")
    profile, escalated = integrated.route("Explorer", "run_scenario", data, routing)
    assert profile == expected and escalated == (expected == "sonnet")


def test_qualified_sonnet_routes_stay_sonnet():
    data = integrated.implementation("Architect").sample("architect")
    assert integrated.route("Architect", "architect", data, {}) == ("sonnet", False)


@pytest.mark.parametrize(
    "line,held",
    [
        ('$a["NAME$i"] = 1;', False),  # plain variable read: data
        ('$a = "Total $amount for $name";', False),
        ('$a = "x {$obj->call()}";', True),  # complex interpolation keeps the hold
        ('$a = "x ${name}";', True),
        ('$a = "x $obj->prop";', True),
        ('$a = "x $arr[0]";', True),
    ],
)
def test_only_plain_variable_interpolation_counts_as_data(line, held):
    from pieces.agents.source_references import discover_component_gaps

    gaps = discover_component_gaps({"a.php": "<?php\n" + line + "\n"})
    assert bool(gaps) == held


def test_sample_shop_package_is_complete_for_scope():
    from pathlib import Path

    from pieces.agents.source_references import discover_component_gaps

    root = Path(__file__).resolve().parents[3] / "fixtures/shops/legacy-php-shop/src"
    files = {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*.php"))}
    assert discover_component_gaps(files) == []


def _real_run():
    from pathlib import Path

    from pieces.agents.source_inventory import build_static_inventory, package_from_sources

    root = Path(__file__).resolve().parents[3]
    shop = root / "fixtures/shops/legacy-php-shop/src"
    files = {str(p.relative_to(shop)): p.read_text() for p in sorted(shop.rglob("*.php"))}
    inventory = build_static_inventory(package_from_sources(shop_id="legacy-php-shop", files=files))
    lib = root / "fixtures/switch-libs/php"
    return {
        "survey": dict(SURVEY, shop_id="legacy-php-shop", inventory=inventory),
        "files": files,
        "api_reference": (lib / "API.md").read_text(),
        "library": (lib / "paypal_orders.php").read_text(),
        "php_lint": lambda fs: {k: {"ok": True, "error": None} for k in fs},
    }


def test_real_code_chain_plans_from_the_survey_and_authors_the_shop_files(tmp_path):
    run = _real_run()
    p, tasks = _run(tmp_path / "b.sqlite", run)
    assert [s[0] for s in integrated.ALL_STAGES if tasks[s[0]].state != "succeeded"] == []
    root_map, mappings, open_items = integrated.scope(run["survey"]["inventory"])
    assert {m["symbol"] for m in mappings} == set(integrated.RULE_SYMBOL.values())
    assert [o["family"] for o in open_items] == ["CHECKOUT_JS_V4"]  # listed, never dropped
    after = p.artifacts.candidate_files("grafter")
    assert set(after) == {
        "api/create-payment.php",
        "api/execute-payment.php",
        "api/refund.php",
        "ipn.php",
    }
    assert not any("paypal_nvp(" in text for text in after.values())
    # Grounding: the Scribe reads the shop's real capture file and its rule names it; the
    # Adversary attacks the Grafter's real code, capture file first.
    scribe = integrated.stage_data(p, "scribe-final", "Scribe", "scribe_final", run)
    assert scribe["files"] == {"api/execute-payment.php": run["files"]["api/execute-payment.php"]}
    assert {tuple(r["sources"]["code"]) for r in scribe["normative_rules"]} == {
        ("api/execute-payment.php",)
    }
    adversary = integrated.stage_data(p, "adversary-guards", "Adversary", "derive_guards", run)
    assert next(iter(adversary["files"])) == "api/execute-payment.php"
    assert adversary["files"] == {path: after[path] for path in adversary["files"]}


def test_authored_code_review_rejects_old_calls_and_missing_operations():
    from pieces.agents.component_agents import grafter

    run = _real_run()
    data = grafter.Input.model_validate(
        dict(
            grafter.sample("candidate_patch"),
            files={"api/refund.php": run["files"]["api/refund.php"]},
            allowed_paths=["api/refund.php"],
            expected_tree=content_digest({"api/refund.php": run["files"]["api/refund.php"]}),
            replacements=None,
            author=True,
            api_reference="x",
            forbidden_calls=integrated.FORBIDDEN_AFTER,
            target_plan=dict(
                grafter.sample("candidate_patch")["target_plan"],
                items=[
                    dict(
                        touchpoint="t1",
                        target_op="gg_refund_capture",
                        mapping_id="nvp-refund",
                        delta_ids=[],
                        paypal_only=True,
                    )
                ],
            ),
        )
    )
    lib = "<?php\nrequire_once __DIR__ . '/../lib/paypal_orders.php';\n"
    good = (
        lib + "if ($order['status'] !== 'PAID') { exit; }\n"
        "$r = gg_refund_capture($c, $a, 'USD', 'x');\n"
    )
    assert grafter.check_authored(data, {"api/refund.php": good})
    for bad, _why in [
        (good + "paypal_nvp('RefundTransaction', []);\n", "old call left"),
        (lib + "$r = gg_refund_capture($c, $a, 'USD', 'x');\n", "original paid guard dropped"),
        (good + "define('PAYPAL_CLIENT_SECRET', 'EKq9xV3mN7pL2wR8tY4uB6');\n", "secret literal"),
        ("<?php\nrequire_once __DIR__ . '/../lib/paypal_orders.php';\n", "operation missing"),
        ("<?php\n$r = gg_refund_capture($c);\n", "library not loaded"),
    ]:
        with pytest.raises(ValueError):
            grafter.check_authored(data, {"api/refund.php": bad})
    with pytest.raises(ValueError):
        grafter.check_authored(data, {"config.php": good})  # outside the allowed paths


def test_money_rules_catch_planted_bugs_but_not_faithful_rewrites():
    from pieces.agents.component_agents.grafter import check_money_rules

    paid = "<?php\n$s = ($cap['capture_status'] === 'COMPLETED') ? 'PAID' : 'PENDING';\n"
    check_money_rules("x.php", paid)
    block = "<?php\nif ($c['capture_status'] === 'COMPLETED') {\n    $o['status'] = 'PAID';\n}\n"
    check_money_rules("x.php", block)
    hook = "<?php\n$ok = gg_verify_webhook($h, $raw);\nif ($ok && $t === 'X') { log_it(); }\n"
    check_money_rules("ipn.php", hook)
    # A shop whose original refund had no paid check is not failed for keeping it that way.
    check_money_rules("refund.php", "<?php\ngg_refund_capture($c, $a, 'USD', 'r');\n", "<?php\n")
    for bad, before in [
        (paid.replace("===", "!=="), ""),  # a PENDING capture marked PAID
        ("<?php\n$o['status'] = 'PAID';\n", ""),  # PAID with no check at all
        (hook.replace("if ($ok &&", "if (true &&"), ""),  # webhook result ignored
        (
            "<?php\ngg_refund_capture($c, $a, 'USD', 'r');\n",
            "<?php\nif ($o['status'] !== 'PAID') exit;\n",  # original guard dropped
        ),
        ("<?php\n$cfg = ['client_secret' => 'EKq9xV3mN7pL2wR8tY4uB6cD'];\n", ""),
    ]:
        with pytest.raises(ValueError, match="DENIED"):
            check_money_rules("x.php", bad, before)


def test_a_model_fault_hold_gets_one_retry_and_the_chain_continues_on_it(tmp_path, monkeypatch):
    from pieces.agents.component_agents import grafter

    real_review = grafter.review

    def flaky(task, data, packet, outputs, observations):
        if task.task.task_id == "grafter":  # the first attempt's answers are always refused
            raise ValueError("DENIED simulated model slip")
        return real_review(task, data, packet, outputs, observations)

    monkeypatch.setattr(grafter, "review", flaky)
    # Offline, a refused final is reported as DENIED; live, the same slip is INVALID_MODEL_OUTPUT.
    monkeypatch.setattr(integrated, "MODEL_FAILURES", integrated.MODEL_FAILURES | {"DENIED"})
    run = _real_run()
    p, tasks = _run(tmp_path / "b.sqlite", run)
    assert tasks["grafter"].state == "held"
    assert tasks["grafter"].issue.code in integrated.MODEL_FAILURES
    assert tasks["grafter" + integrated.RETRY].state == "succeeded"
    assert tasks["candidate-build"].task.dependencies == ["grafter" + integrated.RETRY]
    stands = {s[0]: integrated.stands_for(tasks, s[0]).state for s in integrated.ALL_STAGES}
    assert set(stands.values()) == {"succeeded"}


def test_deterministic_holds_are_never_retried(tmp_path):
    run = dict(_real_run(), learning_consent=False)  # Librarian must hold (DENIED), not retry
    _, tasks = _run(tmp_path / "b.sqlite", run)
    assert tasks["librarian-recipe"].state == "held"
    assert "librarian-recipe" + integrated.RETRY not in tasks


def test_missing_evidence_after_the_model_ran_is_retried_once(tmp_path, monkeypatch):
    from pieces.agents.component_agents import grafter

    real_review = grafter.review

    def flaky(task, data, packet, outputs, observations):
        if task.task.task_id == "grafter":
            raise ValueError("MISSING_EVIDENCE simulated incomplete reading")
        return real_review(task, data, packet, outputs, observations)

    monkeypatch.setattr(grafter, "review", flaky)
    run = dict(_real_run(), model_ran_holds={"grafter"})  # the driver marks model-ran holds
    _, tasks = _run(tmp_path / "b.sqlite", run)
    assert tasks["grafter"].issue.code == "MISSING_EVIDENCE"
    assert tasks["grafter" + integrated.RETRY].state == "succeeded"
