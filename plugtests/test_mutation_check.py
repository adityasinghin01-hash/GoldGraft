"""Planted-bug check on AI-written code (scripts/mutation_check.py): offline, no model calls."""

import json

from scripts.mutation_check import check_run

LIB = "<?php\nrequire_once __DIR__ . '/../lib/paypal_orders.php';\n"
CAPTURE = (
    LIB + "$cap = gg_capture_order($token, 'c');\n"
    "$order['status'] = ($cap['capture_status'] === 'COMPLETED') ? 'PAID' : 'PENDING';\n"
)
REFUND = (
    LIB
    + "if ($order['status'] !== 'PAID') { exit; }\n$r = gg_refund_capture($t, $a, 'USD', 'r');\n"
)
HOOK = (
    "<?php\nrequire_once __DIR__ . '/lib/paypal_orders.php';\n"
    "$ok = gg_verify_webhook(getallheaders(), $raw);\nif ($ok && $type === 'X') { note(); }\n"
)


def write_run(tmp_path, after, ops=("gg_capture_order", "gg_refund_capture", "gg_verify_webhook")):
    run = tmp_path / "run-1"
    run.mkdir()
    before = {
        "api/execute-payment.php": "<?php\npaypal_nvp('DoExpressCheckoutPayment');\n",
        "api/refund.php": (
            "<?php\nif ($order['status'] !== 'PAID') exit;\npaypal_nvp('RefundTransaction');\n"
        ),
        "ipn.php": "<?php\n// cmd=_notify-validate\n",
    }
    files = [
        {"path": p, "before": before[p], "after": a, "author": "model"} for p, a in after.items()
    ]
    (run / "CHANGES.json").write_text(json.dumps({"files": files, "open_items": [], "lint": None}))
    plan = {"items": [{"target_op": op} for op in ops]}
    (run / "OUTPUTS.json").write_text(json.dumps({"architect": [{"payload": plan}]}))
    return run


def test_every_planted_money_bug_is_caught_and_the_faithful_rewrite_passes(tmp_path):
    run = write_run(
        tmp_path,
        {"api/execute-payment.php": CAPTURE, "api/refund.php": REFUND, "ipn.php": HOOK},
    )
    result = check_run(run)
    assert result["original_passes_review"] is True
    assert (result["planted"], result["caught"]) == (7, 7)
    assert {m["id"] for m in result["mutants"] if m["applied"]} == {f"M{i}" for i in range(1, 8)}


def test_mutants_that_do_not_fit_the_code_are_not_counted(tmp_path):
    run = write_run(tmp_path, {"api/execute-payment.php": CAPTURE}, ops=["gg_capture_order"])
    result = check_run(run)
    assert result["original_passes_review"] is True
    skipped = {m["id"] for m in result["mutants"] if not m["applied"]}
    assert skipped == {"M3", "M4", "M7"}  # no webhook or refund file in this rewrite
    assert result["planted"] == result["caught"] == 4
