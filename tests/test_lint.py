from src.static.lint import lint
from src.static.vocabulary import HandlerEntry, Vocabulary


def _vocabulary(*names: str) -> Vocabulary:
    return Vocabulary(
        [
            HandlerEntry(
                name=name,
                file=f"{name}.script",
                line=1,
                signature=f"to {name}",
                params=[],
                purpose="",
            )
            for name in names
        ]
    )


def _codes(source: str, vocabulary: Vocabulary | None = None) -> list[str]:
    return [issue.code for issue in lint(source, vocabulary)]


def test_clean_script_has_no_issues() -> None:
    source = """to cleanHandler
if ImageFound("Save") then
  click "Save"
end if
end cleanHandler
"""

    assert lint(source, _vocabulary("cleanHandler")) == []


def test_missing_end_if() -> None:
    source = "to testHandler\nif ImageFound(\"Save\") then\nend testHandler\n"

    assert "ST001" in _codes(source)


def test_missing_end_repeat() -> None:
    source = "to testHandler\nrepeat 2 times\nlog \"again\"\nend testHandler\n"

    assert "ST001" in _codes(source)


def test_missing_end_try() -> None:
    source = "to testHandler\ntry\nlog \"attempt\"\nend testHandler\n"

    assert "ST001" in _codes(source)


def test_unknown_handler_call() -> None:
    source = "to testHandler\nmysteryHandler\nend testHandler\n"

    issues = lint(source, _vocabulary("testHandler"))

    assert any(issue.code == "ST002" and issue.line == 2 for issue in issues)


def test_builtin_call_is_not_unknown() -> None:
    source = "to testHandler\nclick \"Save\"\nend testHandler\n"

    assert "ST002" not in _codes(source, _vocabulary("testHandler"))


def test_unbalanced_parentheses() -> None:
    source = "to testHandler\nclick (10, 20\nend testHandler\n"

    assert "ST003" in _codes(source)


def test_unbalanced_quotes() -> None:
    source = 'to testHandler\nlog "broken\nend testHandler\n'

    assert "ST004" in _codes(source)


def test_multiple_issues_in_one_script() -> None:
    source = 'to testHandler\nif true then\nmysteryHandler ("broken\n'

    codes = set(_codes(source, _vocabulary("testHandler")))

    assert {"ST001", "ST002", "ST003", "ST004"} <= codes


def test_crossed_block_nesting_is_unbalanced() -> None:
    source = """to testHandler
if true then
repeat 2 times
end if
end repeat
end testHandler
"""

    assert "ST001" in _codes(source)


def test_custom_allowlist_skips_unknown_handler() -> None:
    source = "to testHandler\ntrackBuiltIn\nend testHandler\n"

    assert "ST002" not in [
        issue.code
        for issue in lint(
            source,
            _vocabulary("testHandler"),
            allowlist={"trackBuiltIn"},
        )
    ]