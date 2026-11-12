"""Two bounded source mutations for the admitted local PHP payment profile."""

import difflib
import re

from goldgraft_contracts.proof import Mutant


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
