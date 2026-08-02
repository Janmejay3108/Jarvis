from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass

from src.static.sensetalk_parser import (
    handler_calls,
    handler_defs,
    source_without_comments,
    source_without_strings,
)
from src.static.vocabulary import Vocabulary

DEFAULT_BUILTINS = frozenset(
    {
        "put",
        "set",
        "log",
        "wait",
        "click",
        "doubleclick",
        "rightclick",
        "typetext",
        "moveto",
        "waitfor",
        "readtext",
        "assert",
        "throw",
        "return",
        "exit",
        "repeat",
        "if",
        "run",
        "connect",
        "disconnect",
        "capturescreen",
        "imagefound",
        "imagelocation",
        "remotescreensize",
        "end",
        "else",
        "catch",
    }
)


@dataclass(frozen=True)
class LintIssue:
    line: int
    code: str
    message: str


def _block_issues(script_text: str) -> list[LintIssue]:
    cleaned = source_without_comments(script_text)
    definition_lines = {definition.line for definition in handler_defs(cleaned)}
    stack: list[tuple[str, int]] = []
    issues: list[LintIssue] = []

    for line_number, line in enumerate(cleaned.splitlines(), 1):
        closer: str | None = None
        if re.match(r"^\s*end\s+if\b", line, re.IGNORECASE):
            closer = "if"
        elif re.match(r"^\s*end\s+repeat\b", line, re.IGNORECASE):
            closer = "repeat"
        elif re.match(r"^\s*end\s+try\b", line, re.IGNORECASE):
            closer = "try"
        elif re.match(
            r"^\s*end(?:\s+(?!if\b|repeat\b|try\b)[A-Za-z_]\w*)?\s*$",
            line,
            re.IGNORECASE,
        ):
            closer = "handler"

        if closer is not None:
            if not stack:
                issues.append(
                    LintIssue(
                        line=line_number,
                        code="ST001",
                        message=f"Unmatched {closer} block closer",
                    )
                )
            else:
                opener, _ = stack.pop()
                if opener != closer:
                    issues.append(
                        LintIssue(
                            line=line_number,
                            code="ST001",
                            message=(
                                f"Mismatched block closer: expected {opener}, got {closer}"
                            ),
                        )
                    )
            continue

        if line_number in definition_lines:
            stack.append(("handler", line_number))
        elif re.match(r"^\s*if\b", line, re.IGNORECASE):
            stack.append(("if", line_number))
        elif re.match(r"^\s*repeat\b", line, re.IGNORECASE):
            stack.append(("repeat", line_number))
        elif re.match(r"^\s*try\b", line, re.IGNORECASE):
            stack.append(("try", line_number))

    for block_type, line_number in stack:
        issues.append(
            LintIssue(
                line=line_number,
                code="ST001",
                message=f"Unclosed {block_type} block",
            )
        )
    return issues


def _unknown_handler_issues(
    script_text: str,
    vocabulary: Vocabulary,
    allowlist: Collection[str] | None,
) -> list[LintIssue]:
    builtins = set(DEFAULT_BUILTINS)
    if allowlist is not None:
        builtins.update(name.casefold() for name in allowlist)

    issues: list[LintIssue] = []
    cleaned = source_without_comments(script_text)
    for line_number, line in enumerate(cleaned.splitlines(), 1):
        for call in handler_calls(line):
            if call.casefold() in builtins or vocabulary.exists(call):
                continue
            issues.append(
                LintIssue(
                    line=line_number,
                    code="ST002",
                    message=f"Unknown handler call: {call}",
                )
            )
    return issues


def _parenthesis_issues(script_text: str) -> list[LintIssue]:
    cleaned = source_without_strings(source_without_comments(script_text))
    open_count = cleaned.count("(")
    close_count = cleaned.count(")")
    if open_count == close_count:
        return []
    return [
        LintIssue(
            line=0,
            code="ST003",
            message=(
                f"Unbalanced parentheses: {open_count} opening, {close_count} closing"
            ),
        )
    ]


def _quote_issues(script_text: str) -> list[LintIssue]:
    cleaned = source_without_comments(script_text)
    return [
        LintIssue(
            line=line_number,
            code="ST004",
            message="Unbalanced double quote on line",
        )
        for line_number, line in enumerate(cleaned.splitlines(), 1)
        if line.count('"') % 2 != 0
    ]


def lint(
    script_text: str,
    vocabulary: Vocabulary | None = None,
    allowlist: Collection[str] | None = None,
) -> list[LintIssue]:
    issues = _block_issues(script_text)
    if vocabulary is not None:
        issues.extend(_unknown_handler_issues(script_text, vocabulary, allowlist))
    issues.extend(_parenthesis_issues(script_text))
    issues.extend(_quote_issues(script_text))
    return sorted(issues, key=lambda issue: (issue.line, issue.code, issue.message))
