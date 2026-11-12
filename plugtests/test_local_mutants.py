"""Executable-candidate mutations must change real source with exact diff context."""

import pytest

from integration.local_mutants import build_mutants
from pieces.proof.mutation import apply_mutant


def test_mutants_patch_actual_candidate_and_hold_when_operator_is_unsupported():
    sources = {
        "api/execute-payment.php": "<?php\n$r = gg_capture_order($token);\n"
        "$o['status'] = ($r['capture_status'] === 'COMPLETED') ? 'PAID' : 'PENDING';\n",
        "api/create-payment.php": "<?php\n"
        "$r = gg_create_order($items, $total, SHOP_CURRENCY, $ok, $cancel, $key);\n",
    }
    mutants, missing = build_mutants(sources)
    assert missing == []
    assert {mutant.rule for mutant in mutants} == {"R01", "R03"}
    patched = {m.rule: apply_mutant(sources[m.location.file], m) for m in mutants}
    assert "=== 'PENDING'" in patched["R01"]
    assert "gg_create_order($items, $total, 'EUR'" in patched["R03"]
    with pytest.raises(ValueError, match="context mismatch"):
        apply_mutant("<?php\necho 'different';\n", mutants[0])
    absent, missing = build_mutants({"api/execute-payment.php": "<?php\necho 'no capture';\n"})
    assert absent == []
    assert {row["id"] for row in missing} == {"PHP-PENDING", "PHP-CURRENCY"}
    # A currency constant outside the create call is not this mutation's target.
    _, missing = build_mutants(
        {
            **sources,
            "api/create-payment.php": "<?php\n$r = gg_create_order($items, $total, $currency);\n"
            "$other = SHOP_CURRENCY;\n",
        }
    )
    assert {row["id"] for row in missing} == {"PHP-CURRENCY"}
