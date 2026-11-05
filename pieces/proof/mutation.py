"""Apply one isolated mutant at a time and ask an injected runner for verdicts."""

import re
from collections.abc import Callable, Mapping, Sequence

from goldgraft_contracts.proof import Grade, Mutant

HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?")
type ScenarioRunner = Callable[[Mutant, str, str], Grade]


def apply_mutant(source: str, mutant: Mutant) -> str:
    lines = source.splitlines(keepends=True)
    patch = mutant.patch.splitlines(keepends=True)
    if len(patch) < 4 or not patch[0].startswith("--- ") or not patch[1].startswith("+++ "):
        raise ValueError(f"{mutant.id}: expected a single-file unified diff")
    output = []
    cursor, index = 0, 2
    while index < len(patch):
        header = HUNK.fullmatch(patch[index].rstrip("\r\n"))
        if header is None:
            raise ValueError(f"{mutant.id}: invalid hunk header")
        old_count, new_count = int(header[2] or 1), int(header[4] or 1)
        old_start = int(header[1]) - bool(old_count)
        new_start = int(header[3]) - bool(new_count)
        if not cursor <= old_start <= len(lines):
            raise ValueError(f"{mutant.id}: invalid source range")
        output.extend(lines[cursor:old_start])
        cursor = old_start
        if len(output) != new_start:
            raise ValueError(f"{mutant.id}: invalid target range")
        index += 1
        removed, added = 0, 0
        while index < len(patch) and not patch[index].startswith("@@"):
            marker, content = patch[index][0], patch[index][1:]
            if marker not in {" ", "+", "-"}:
                raise ValueError(f"{mutant.id}: invalid patch line")
            if marker in {" ", "-"}:
                if cursor >= len(lines) or lines[cursor] != content:
                    raise ValueError(f"{mutant.id}: source context mismatch at line {cursor + 1}")
                cursor += 1
                removed += 1
            if marker in {" ", "+"}:
                output.append(content)
                added += 1
            index += 1
        if (removed, added) != (old_count, new_count):
            raise ValueError(f"{mutant.id}: incorrect hunk line counts")
    output.extend(lines[cursor:])
    mutated = "".join(output)
    if mutated == source:
        raise ValueError(f"{mutant.id}: patch leaves source unchanged")
    return mutated


def run_mutants(
    mutants: Sequence[Mutant],
    sources: Mapping[str, str],
    scenarios_by_rule: Mapping[str, Sequence[str]],
    run_scenario: ScenarioRunner,
) -> dict[str, dict[str, Grade]]:
    """The callback receives the patched file content and one linked scenario ID."""
    results: dict[str, dict[str, Grade]] = {}
    for mutant in mutants:
        if mutant.id in results:
            raise ValueError(f"Duplicate mutant ID {mutant.id}")
        mutated = apply_mutant(sources[mutant.location.file], mutant)
        scenarios = scenarios_by_rule[mutant.rule]
        if not scenarios:
            raise ValueError(f"{mutant.id}: no scenarios linked to {mutant.rule}")
        results[mutant.id] = {
            scenario: Grade(run_scenario(mutant, mutated, scenario))
            for scenario in dict.fromkeys(scenarios)
        }
    return results
