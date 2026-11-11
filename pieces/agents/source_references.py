"""Conservative source-reference preflight, never a PHP interpreter or call graph.

Only complete literal include expressions and __DIR__ + literal are resolved.
Unknown expression/lexical forms hold; comments, strings and HTML are data.
Resolution is relative to the supplied file in this synthetic profile. Real PHP
include_path/current-directory/runtime behavior still needs VJ/GU qualification.
"""

import re
from pathlib import PurePosixPath

from goldgraft_contracts.plan5_common import RelativePath, content_digest
from pydantic import TypeAdapter

OPEN_TAG = re.compile(r"<\?(?:php(?=\s|$)|=)", re.IGNORECASE)
INCLUDES = {"require", "require_once", "include", "include_once"}


def _tokens(text):
    """Preserve offsets for omissions; discard no unknown executable context."""
    tokens = []
    index, inside = 0, False
    while index < len(text):
        if not inside:
            index = text.find("<?", index)
            if index < 0:
                break
            opening = OPEN_TAG.match(text, index)
            if opening is None:
                raise ValueError(index)
            index, inside = opening.end(), True
            continue
        if text.startswith("?>", index):
            tokens.append(("boundary", ";", index))
            index, inside = index + 2, False
            continue
        char = text[index]
        if char.isspace():
            index += 1
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise ValueError(index)
            index = end + 2
        elif text.startswith("#[", index):
            # PHP attributes are executable syntax, not a hash comment. This
            # small recognizer does not parse their expressions.
            raise ValueError(index)
        elif text.startswith("//", index) or char == "#":
            ends = [end for end in (text.find("\n", index), text.find("?>", index)) if end >= 0]
            index = min(ends) if ends else len(text)
        elif char in {"'", '"'}:
            start, quote = index, char
            index += 1
            while index < len(text) and text[index] != quote:
                index += 2 if text[index] == "\\" else 1
            if index >= len(text):
                raise ValueError(start)
            value = text[start : index + 1]
            kind = "interpolated" if quote == '"' and "$" in value else "string"
            tokens.append((kind, value, start))
            index += 1
        elif char == "`" or text.startswith("<<<", index):
            raise ValueError(index)
        elif char.isalpha() or char in {"_", "$"}:
            start = index
            index += 1
            while index < len(text) and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(("word", text[start:index], start))
        else:
            operator = next((op for op in ("?->", "->", "::") if text.startswith(op, index)), char)
            tokens.append(("punctuation", operator, index))
            index += len(operator)
    return tokens


def _literal_path(expression):
    while expression and expression[0][1] == "(" and expression[-1][1] == ")":
        depth = 0
        for _position, token in enumerate(expression):
            depth += (token[1] == "(") - (token[1] == ")")
            if depth == 0:
                break
        if _position != len(expression) - 1:
            break
        expression = expression[1:-1]
    directory = False
    if len(expression) == 3 and [t[1].lower() for t in expression[:2]] == ["__dir__", "."]:
        directory, expression = True, expression[2:]
    if len(expression) != 1 or expression[0][0] != "string":
        return None
    quoted = expression[0][1]
    path = quoted[1:-1]
    if not path or (quoted[0] == '"' and "$" in path):
        return None
    return path, directory


SIMPLE_VARIABLE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")


def _simple_interpolation(quoted):
    """True when every `$` in a double-quoted string is a plain variable read ("...$i").

    Plain variable interpolation reads a value; it cannot include a file or call code by
    itself. `{$`, `${`, `->`, `[` and `(` after a variable keep the conservative hold.
    """
    body = quoted[1:-1]
    if "{$" in body or "${" in body:
        return False
    for match in SIMPLE_VARIABLE.finditer(body):
        after = body[match.end() : match.end() + 2]
        if after.startswith(("[", "(")) or after == "->":
            return False
    stripped = SIMPLE_VARIABLE.sub("", body.replace("\\$", ""))
    return "$" not in stripped


def _resolve(name, target, directory):
    parts = name.split("/")[:-1]
    outside = any(char in target for char in ("\\", ":", "\x00"))
    if target.startswith("/"):
        if directory:
            target = target.lstrip("/")
        else:
            outside = True
    for part in target.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            else:
                outside = True
        else:
            parts.append(part)
    resolved = "/".join(parts)
    try:
        TypeAdapter(RelativePath).validate_python(resolved)
    except ValueError:
        outside = True
    return None if outside else resolved


def discover_component_gaps(files):
    """Find required omissions in supplied bytes without accessing any target."""
    omissions = []

    def missing(name, offset, reason, path=None):
        omissions.append(
            {
                "component_id": "source-ref-" + content_digest([name, offset, reason, path])[:16],
                "path": path,
                "reason_code": reason,
                "required_for_scope": True,
                "evidence_refs": ["fake:survey-source"],
            }
        )

    for name, text in sorted(files.items()):
        if PurePosixPath(name).suffix.lower() not in {".php", ".phtml", ".inc", ".php5"}:
            continue
        try:
            tokens = _tokens(text)
        except ValueError as exc:
            missing(name, exc.args[0], "UNSUPPORTED_SOURCE_SYNTAX")
            continue
        for index, (kind, value, offset) in enumerate(tokens):
            if kind == "interpolated" and not _simple_interpolation(value):
                # Complex interpolation ({$...}, ${...}, ->, [], calls) may evaluate
                # expressions. Do not treat it as inert data or claim its coverage.
                missing(name, offset, "UNRESOLVED_SOURCE_REFERENCE")
                continue
            if kind != "word" or (index and tokens[index - 1][1] in {"->", "?->", "::"}):
                continue
            if value.lower() in {"eval", "__halt_compiler"}:
                missing(name, offset, "UNRESOLVED_SOURCE_REFERENCE")
            elif value.lower() in INCLUDES:
                end = index + 1
                while end < len(tokens) and tokens[end][1] != ";":
                    end += 1
                literal = _literal_path(tokens[index + 1 : end])
                if literal is None:
                    missing(name, offset, "UNRESOLVED_SOURCE_REFERENCE")
                    continue
                resolved = _resolve(name, *literal)
                if resolved is None:
                    missing(name, offset, "SOURCE_REFERENCE_OUTSIDE_SCOPE")
                elif resolved not in files:
                    missing(name, offset, "MISSING_REFERENCED_SOURCE_COMPONENT", resolved)
    return omissions
