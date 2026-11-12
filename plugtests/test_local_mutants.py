"""Executable-candidate mutations must change real source with exact diff context."""

import pytest

from integration.local_mutants import build_mutants
from pieces.proof.mutation import apply_mutant

NEW_IDS = {
    "PHP-PENDING",
    "PHP-CURRENCY",
    "PHP-AMOUNT",
    "PHP-NOTPAID",
    "PHP-RECAPTURE",
    "PHP-UNAPPROVED",
    "PHP-UNVERIFIED",
    "PHP-REFUND-AGAIN",
    "PHP-BROWSER-AMOUNT",
    "PHP-UNKNOWN-SKU",
}
CANDIDATE = {
    "api/create-payment.php": "<?php\nforeach ($cart as $sku => $qty) {\n"
    "    if (!isset($PRODUCTS[$sku])) continue;\n    $total += 1;\n}\n"
    "if ($total <= 0) { exit; }\n"
    "$resp = gg_create_order(\n    $items,\n    number_format($total, 2, '.', ''),\n"
    "    SHOP_CURRENCY,\n    $ok\n);\n",
    "api/execute-payment.php": "<?php\n$pay = gg_capture_order($token, 'capture-' . $token);\n"
    "if (empty($pay['ok'])) { exit; }\n"
    "$order['status'] = (($pay['capture_status'] ?? '') === 'COMPLETED') ? 'PAID' : 'PENDING';\n",
    "api/refund.php": "<?php\nif (!$order || $order['status'] !== 'PAID') { exit; }\n",
    "ipn.php": "<?php\nif ($verified && ($event['event_type'] ?? '') === 'X') { log(); }\n",
}
EXPECT = {
    "R01": "=== 'PENDING'",
    "R03": "'EUR'",
    "R02": "number_format($total + 1,",
    "R04": "? 'PENDING' : 'PENDING'",
    "R05": "'capture-' . bin2hex(random_bytes(4))",
    "R06": "if (false)",
    "R08": "if (true &&",
    "R11": "!in_array($order['status'], ['PAID', 'REFUNDED'], true)",
    "R12": "$total = isset($cart['minor'])",
    "R17": "$total += (float)$qty; continue;",
}


def test_every_planted_bug_patches_its_exact_site_and_names_its_scenario():
    from integration.local_mutants import scenario_for

    mutants, missing = build_mutants(CANDIDATE)
    assert missing == []
    assert {m.id for m in mutants} == NEW_IDS
    for m in mutants:
        patched = apply_mutant(CANDIDATE[m.location.file], m)
        assert patched != CANDIDATE[m.location.file]
        assert EXPECT[m.rule] in patched, m.id
    assert scenario_for("R05") == "DOUBLE" and scenario_for("R11") == "REFUND_TWICE"
    assert scenario_for("R02") == "HAPPY"


def test_mutants_patch_actual_candidate_and_hold_when_operator_is_unsupported():
    sources = {
        "api/execute-payment.php": "<?php\n$r = gg_capture_order($token);\n"
        "$o['status'] = ($r['capture_status'] === 'COMPLETED') ? 'PAID' : 'PENDING';\n",
        "api/create-payment.php": "<?php\n"
        "$r = gg_create_order($items, $total, SHOP_CURRENCY, $ok, $cancel, $key);\n",
    }
    mutants, missing = build_mutants(sources)
    assert {mutant.rule for mutant in mutants} == {"R01", "R03", "R04"}
    # Shapes absent from these two lines are reported, never counted as kills.
    built = {"PHP-PENDING", "PHP-CURRENCY", "PHP-NOTPAID"}
    assert {row["id"] for row in missing} == NEW_IDS - built
    patched = {m.rule: apply_mutant(sources[m.location.file], m) for m in mutants}
    assert "=== 'PENDING'" in patched["R01"]
    assert "gg_create_order($items, $total, 'EUR'" in patched["R03"]
    with pytest.raises(ValueError, match="context mismatch"):
        apply_mutant("<?php\necho 'different';\n", mutants[0])
    absent, missing = build_mutants({"api/execute-payment.php": "<?php\necho 'no capture';\n"})
    assert absent == []
    assert {row["id"] for row in missing} == NEW_IDS
    # A currency constant outside the create call is not this mutation's target.
    _, missing = build_mutants(
        {
            **sources,
            "api/create-payment.php": "<?php\n$r = gg_create_order($items, $total, $currency);\n"
            "$other = SHOP_CURRENCY;\n",
        }
    )
    assert "PHP-CURRENCY" in {row["id"] for row in missing}
