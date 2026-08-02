from src.static.sensetalk_parser import handler_calls, handler_defs


def test_all_definition_kinds_and_parameters() -> None:
    source = """to clickElement label,SR,expectation
to handle EnterTextBoxByImage imageTextBox, data, waitTime
function commonScreenPart Portion
on validateValues values,SR:[0,0,1920,1080]
"""

    definitions = handler_defs(source)

    assert [definition.kind for definition in definitions] == [
        "to",
        "to handle",
        "function",
        "on",
    ]
    assert [definition.name for definition in definitions] == [
        "clickElement",
        "EnterTextBoxByImage",
        "commonScreenPart",
        "validateValues",
    ]
    assert [definition.params for definition in definitions] == [
        ["label", "SR", "expectation"],
        ["imageTextBox", "data", "waitTime"],
        ["Portion"],
        ["values", "SR"],
    ]
    assert [definition.line for definition in definitions] == [1, 2, 3, 4]


def test_bare_and_dotted_string_calls() -> None:
    source = """clickElement "Save"
  "CommonEnovia".searchEnovia "Part"
"""

    assert handler_calls(source) == ["clickElement", "searchEnovia"]


def test_comments_and_strings_are_excluded_from_calls() -> None:
    source = """// commentOnly
-- anotherComment
(* blockHandler
stillBlocked *)
log "stringHandler"
realHandler
"""

    calls = handler_calls(source)

    assert "commentOnly" not in calls
    assert "anotherComment" not in calls
    assert "blockHandler" not in calls
    assert "stillBlocked" not in calls
    assert "stringHandler" not in calls
    assert calls == ["log", "realHandler"]


def test_mixed_definitions_and_calls_exclude_definition_name() -> None:
    source = """to outerHandler value
  innerHandler value
end outerHandler
outerHandler "value"
"""

    assert [definition.name for definition in handler_defs(source)] == ["outerHandler"]
    assert handler_calls(source) == ["innerHandler", "end", "outerHandler"]


def test_definition_matching_is_case_insensitive() -> None:
    source = """To Handle FirstHandler
TO HANDLE SecondHandler value
to handle ThirdHandler value:[1,2]
"""

    definitions = handler_defs(source)

    assert [definition.name for definition in definitions] == [
        "FirstHandler",
        "SecondHandler",
        "ThirdHandler",
    ]
    assert all(definition.kind == "to handle" for definition in definitions)


def test_definition_name_is_not_a_call_without_invocation() -> None:
    source = """function calculateValue input
  return input
end function
"""

    assert "calculateValue" not in handler_calls(source)