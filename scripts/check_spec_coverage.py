#!/usr/bin/env python3
"""Check field paths and literal enum choices parsed from design 01's code blocks.

This parses the design's small pseudo-schema language, not the prose/tables.
Each nested object is compared within its own format (not a global word bag).
"""

import re
from pathlib import Path

from goldgraft_contracts.registry import REGISTRY

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAMES = {"MoneyEvent": "CMEL"}


def split_fields(body: str) -> list[str]:
    parts, start, depth = [], 0, 0
    for index, char in enumerate(body):
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:index].strip())
            start = index + 1
    parts.append(body[start:].strip())
    return [part for part in parts if part]


def objects(text: str):
    """Yield outer brace contents; callers recurse into each field."""
    start, depth = 0, 0
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index + 1
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                yield text[start:index]
    if depth:
        raise ValueError("Unbalanced design braces")


def spec_fields(body: str, prefix: str = "") -> tuple[set[str], dict[str, set[str]]]:
    fields: set[str] = set()
    enums: dict[str, set[str]] = {}
    for part in split_fields(body):
        match = re.match(r"^(\w+)(\?)?(?=\s*[:=(]|\s*$)", part)
        if not match:
            # Only the `time: {minutes by stage}` prose object is not a field list.
            if part.strip() == "minutes by stage":
                continue
            raise ValueError(f"Unrecognized spec field: {part!r}")
        name = match[1]
        path = f"{prefix}.{name}" if prefix else name
        fields.add(path)
        value = part[match.end() :]
        for nested in objects(value):
            child_fields, child_enums = spec_fields(nested, path)
            fields.update(child_fields)
            enums.update(child_enums)
        # Enumerations are written as literal tokens separated by | (possibly multiline).
        scalar = value
        while "{" in scalar:
            scalar = re.sub(r"\{[^{}]*\}", "", scalar)
        for choices in re.finditer(r"\b([\w/]+(?:\s*\|\s*[\w/]+)+)", scalar):
            options = {token.strip() for token in choices[1].split("|")}
            if all(token.upper() == token for token in options) or options == {"agent", "service"}:
                enums.setdefault(path, set()).update(options)
        if name in {"lenses", "lenses_run"}:
            lens_values = re.search(r"\[([a-z_, ]+)\]", scalar)
            if lens_values:
                enums.setdefault(path, set()).update(
                    token.strip() for token in lens_values[1].split(",")
                )
        op_range = re.search(r"M(\d+)\.\.M(\d+)", scalar)
        if op_range:
            enums.setdefault(path, set()).update(
                f"M{i}" for i in range(int(op_range[1]), int(op_range[2]) + 1)
            )
        # Identity's fields are prose in 01, explicitly confirmed by brief C1.
        if name == "runner_identity":
            fields.update({f"{path}.workflow", f"{path}.sha"})
    return fields, enums


def model_fields(schema: dict) -> tuple[set[str], dict[str, set[str]]]:
    fields: set[str] = set()
    enums: dict[str, set[str]] = {}
    definitions = schema.get("$defs", {})

    def walk(node: dict, prefix: str = "", refs: frozenset = frozenset()):
        if "$ref" in node:
            ref = node["$ref"].rsplit("/", 1)[-1]
            if ref not in refs:
                walk(definitions[ref], prefix, refs | {ref})
            return
        if "enum" in node:
            enums.setdefault(prefix, set()).update(str(item) for item in node["enum"])
        if "const" in node:
            enums.setdefault(prefix, set()).add(str(node["const"]))
        for name, value in node.get("properties", {}).items():
            path = f"{prefix}.{name}" if prefix else name
            fields.add(path)
            walk(value, path, refs)
        for choice in node.get("anyOf", []) + node.get("oneOf", []):
            walk(choice, prefix, refs)
        if isinstance(node.get("items"), dict):
            walk(node["items"], prefix, refs)

    walk(schema)
    return fields, enums


def check_coverage(text: str, registry: dict = REGISTRY) -> tuple[list[str], int, int]:
    errors, field_count, enum_count = [], 0, 0
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        # Strip comments and quoted sample strings before parsing delimiters.
        block = re.sub(r'"[^"\n]*"', '"sample"', block)
        block = re.sub(r"//[^\n]*", "", block)
        matches = list(re.finditer(r"(?m)^(\w+)\s*\{", block))
        for index, match in enumerate(matches):
            name = match[1]
            schema_name = f"{MODEL_NAMES.get(name, name)}/1"
            if schema_name not in registry:
                errors.append(f"{name}: missing model")
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
            bodies = list(objects(block[match.end() - 1 : end]))
            if len(bodies) != 1:
                raise ValueError(f"Expected one body for {name}")
            wanted, choices = spec_fields(bodies[0])
            actual, enums = model_fields(registry[schema_name].model_json_schema(by_alias=True))
            field_count += len(wanted)
            enum_count += sum(map(len, choices.values()))
            errors.extend(f"{name}: missing field {field}" for field in sorted(wanted - actual))
            for path, values in choices.items():
                errors.extend(
                    f"{name}.{path}: missing enum {value}"
                    for value in sorted(values - enums.get(path, set()))
                )
    if field_count == 0:
        errors.append("No design fields parsed")
    return errors, field_count, enum_count


def main() -> int:
    errors, fields, enums = check_coverage((ROOT / "docs/design/01_DATA.md").read_text())
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Spec coverage passed: {fields} field paths, {enums} enum values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
