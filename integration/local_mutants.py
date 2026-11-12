"""Bounded source mutations (planted bugs) for the admitted local PHP payment profile.

Each is one regex site in the agents' candidate, an operator from the design
catalogue (docs/design/01_DATA.md), the critical rule it breaks, and the
scenario that exercises that rule. A shape that does not match is reported as
unsupported and never counted as a kill.
"""

import difflib
import re

from goldgraft_contracts.proof import Mutant

# The scenario that exercises each planted bug's rule.
SCENARIO_FOR = {
    "R01": "PENDING",
    "R05": "DOUBLE",
    "R06": "DECLINE",
    "R08": "NOTIFY_FORGED",
    "R11": "REFUND_TWICE",
}


def scenario_for(rule):
    return SCENARIO_FOR.get(rule, "HAPPY")


def build_mutants(files):
    specs = (
        (
            "PHP-PENDING",
            "M2",
            "R01",
            "api/execute-payment.php",
            r"===\s*(['\"])COMPLETED\1",
            "=== 'PENDING'",
        ),
        (
            "PHP-CURRENCY",
            "M1",
            "R03",
            "api/create-payment.php",
            r"(gg_create_order\s*\((?:(?!\);)[\s\S])*?)\bSHOP_CURRENCY\b",
            r"\1'EUR'",
        ),
        # R02: the amount sent to PayPal no longer equals the stored order total.
        (
            "PHP-AMOUNT",
            "M6",
            "R02",
            "api/create-payment.php",
            r"(gg_create_order\s*\((?:(?!\);)[\s\S])*?)number_format\(\$total,",
            r"\1number_format($total + 1,",
        ),
        # R04: a completed capture is stored as not paid.
        (
            "PHP-NOTPAID",
            "M2",
            "R04",
            "api/execute-payment.php",
            r"\?\s*'PAID'\s*:\s*'PENDING'",
            "? 'PENDING' : 'PENDING'",
        ),
        # R05: a fresh request id on every click, so a retry is a second capture.
        (
            "PHP-RECAPTURE",
            "M5",
            "R05",
            "api/execute-payment.php",
            r"'capture-'\s*\.\s*\$token",
            "'capture-' . bin2hex(random_bytes(4))",
        ),
        # R06: a failed capture no longer stops the confirmation.
        (
            "PHP-UNAPPROVED",
            "M3",
            "R06",
            "api/execute-payment.php",
            r"if \(empty\(\$pay\['ok'\]\)\)",
            "if (false)",
        ),
        # R08: notifications acted on without the verification result.
        (
            "PHP-UNVERIFIED",
            "M8",
            "R08",
            "ipn.php",
            r"if \(\$verified &&",
            "if (true &&",
        ),
        # R11: no refund-state check, so a second full refund is accepted.
        (
            "PHP-REFUND-AGAIN",
            "M12",
            "R11",
            "api/refund.php",
            r"\|\|\s*\$order\['status'\]\s*!==\s*'PAID'",
            "|| !in_array($order['status'], ['PAID', 'REFUNDED'], true)",
        ),
        # R12: the order total taken from the browser's posted amount.
        (
            "PHP-BROWSER-AMOUNT",
            "M7",
            "R12",
            "api/create-payment.php",
            r"if \(\$total <= 0\)",
            "$total = isset($cart['minor']) ? $cart['minor'] / 100 : $total; if ($total <= 0)",
        ),
        # R17: non-catalogue keys from the browser add to the total.
        (
            "PHP-UNKNOWN-SKU",
            "M7",
            "R17",
            "api/create-payment.php",
            r"if \(!isset\(\$PRODUCTS\[\$sku\]\)\) continue;",
            "if (!isset($PRODUCTS[$sku])) { $total += (float)$qty; continue; }",
        ),
    )
    mutants, missing = [], []
    for mid, operation, rule, path, pattern, replacement in specs:
        source = files.get(path, "")
        match = re.search(pattern, source)
        if match is None:
            missing.append({"id": mid, "reason": "source shape unsupported; not counted as a kill"})
            continue
        changed = re.sub(pattern, replacement, source, count=1)
        patch = "".join(
            difflib.unified_diff(
                source.splitlines(keepends=True),
                changed.splitlines(keepends=True),
                fromfile="a/" + path,
                tofile="b/" + path,
            )
        )
        mutants.append(
            Mutant(
                id=mid,
                op=operation,
                rule=rule,
                location={"file": path, "line": source[: match.start()].count("\n") + 1},
                patch=patch,
                equivalent_suspect=False,
                killed_by=[],
            )
        )
    return mutants, missing
