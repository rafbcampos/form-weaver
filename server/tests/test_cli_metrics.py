from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import dspy

from interview.cli.metrics import (
    _get_bindings_from_blocks,
    _get_collected_field_paths,
    _parse_ui_blocks,
    _score_conciseness,
    _validate_block_structure,
    _values_match,
    interview_step_metric,
    text_extractor_metric,
)


def _make_example(**kwargs: Any) -> dspy.Example:
    inputs = [k for k in kwargs if not k.startswith("expected_")]
    return dspy.Example(**kwargs).with_inputs(*inputs)


class TestGetBindingsFromBlocks:
    def test_extracts_bindings_from_form_elements(self) -> None:
        blocks = [
            {"kind": "text", "value": "Hello"},
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": "Name", "binding": "name"},
                    {"kind": "input", "label": "Age", "binding": "age"},
                ],
            },
        ]
        assert _get_bindings_from_blocks(blocks) == {"name", "age"}

    def test_empty_blocks(self) -> None:
        assert _get_bindings_from_blocks([]) == set()

    def test_text_only_blocks(self) -> None:
        blocks = [{"kind": "text", "value": "Hello"}]
        assert _get_bindings_from_blocks(blocks) == set()

    def test_extracts_from_item_elements(self) -> None:
        blocks = [
            {
                "kind": "form",
                "elements": [
                    {
                        "kind": "array",
                        "label": "Children",
                        "binding": "children",
                        "item_elements": [
                            {"kind": "input", "label": "Child Name", "binding": "children[].name"},
                        ],
                    },
                ],
            },
        ]
        bindings = _get_bindings_from_blocks(blocks)
        assert "children" in bindings
        assert "children[].name" in bindings


class TestParseUiBlocks:
    def test_from_dict_response(self) -> None:
        prediction = MagicMock()
        prediction.response.ui_blocks = [
            MagicMock(model_dump=lambda: {"kind": "text", "value": "Hi"})
        ]
        blocks = _parse_ui_blocks(prediction)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "text"

    def test_from_raw_dict(self) -> None:
        raw = {"ui_blocks": [{"kind": "text", "value": "Hi"}]}
        blocks = _parse_ui_blocks(raw)
        assert len(blocks) == 1

    def test_empty(self) -> None:
        assert _parse_ui_blocks({}) == []


class TestValidateBlockStructure:
    def test_valid_structure(self) -> None:
        blocks = [
            {"kind": "text", "value": "Hello!"},
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": "Name", "binding": "name"},
                ],
            },
        ]
        score = _validate_block_structure(blocks, {"name", "age"})
        assert score == 1.0

    def test_missing_text_start(self) -> None:
        blocks = [
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": "Name", "binding": "name"},
                ],
            },
        ]
        score = _validate_block_structure(blocks, {"name"})
        assert score < 1.0

    def test_empty_blocks(self) -> None:
        assert _validate_block_structure([], set()) == 0.0

    def test_invalid_binding_path(self) -> None:
        blocks = [
            {"kind": "text", "value": "Hello!"},
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": "X", "binding": "nonexistent"},
                ],
            },
        ]
        score = _validate_block_structure(blocks, {"name", "age"})
        assert score < 1.0


class TestScoreConciseness:
    def test_ideal_count(self) -> None:
        blocks = [
            {"kind": "text", "value": "Hi"},
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": f"F{i}", "binding": f"field_{i}"} for i in range(3)
                ],
            },
        ]
        assert _score_conciseness(blocks, set()) == 1.0

    def test_too_many_fields(self) -> None:
        blocks = [
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": f"F{i}", "binding": f"field_{i}"} for i in range(8)
                ],
            },
        ]
        assert _score_conciseness(blocks, set()) < 1.0

    def test_asking_already_collected(self) -> None:
        blocks = [
            {
                "kind": "form",
                "elements": [
                    {"kind": "input", "label": "Name", "binding": "name"},
                ],
            },
        ]
        score = _score_conciseness(blocks, {"name"})
        assert score == 0.0

    def test_no_bindings(self) -> None:
        blocks = [{"kind": "text", "value": "Hello"}]
        assert _score_conciseness(blocks, set()) == 0.5


class TestValuesMatch:
    def test_exact_match(self) -> None:
        assert _values_match("hello", "hello")

    def test_numeric_equivalence(self) -> None:
        assert _values_match(25, 25.0)

    def test_case_insensitive_string(self) -> None:
        assert _values_match("Hello", "hello")

    def test_no_match(self) -> None:
        assert not _values_match("hello", "world")


class TestGetCollectedFieldPaths:
    def test_flat_data(self) -> None:
        data = {"name": "John", "age": 25}
        assert _get_collected_field_paths(data) == {"name", "age"}

    def test_nested_data(self) -> None:
        data = {"address": {"city": "NYC", "zip": ""}}
        paths = _get_collected_field_paths(data)
        assert "address.city" in paths
        assert "address.zip" not in paths  # empty string excluded

    def test_none_excluded(self) -> None:
        data = {"name": "John", "age": None}
        assert _get_collected_field_paths(data) == {"name"}


class TestInterviewStepMetric:
    def test_perfect_score(self) -> None:
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        example = _make_example(
            field_schema=json.dumps(schema),
            current_data=json.dumps({}),
            missing_fields=json.dumps(["name", "age"]),
            conversation_history=json.dumps([]),
            expected_field_bindings=["name", "age"],
        )
        prediction = MagicMock()
        prediction.response.ui_blocks = [
            MagicMock(model_dump=lambda: {"kind": "text", "value": "Let's get started!"}),
            MagicMock(
                model_dump=lambda: {
                    "kind": "form",
                    "elements": [
                        {"kind": "input", "label": "Name", "binding": "name"},
                        {"kind": "input", "label": "Age", "binding": "age"},
                    ],
                }
            ),
        ]
        score = interview_step_metric(example, prediction)
        assert score == 1.0

    def test_zero_score_no_blocks(self) -> None:
        schema = {"name": {"type": "string"}}
        example = _make_example(
            field_schema=json.dumps(schema),
            current_data=json.dumps({}),
            missing_fields=json.dumps(["name"]),
            conversation_history=json.dumps([]),
            expected_field_bindings=["name"],
        )
        prediction = MagicMock()
        prediction.response.ui_blocks = []
        score = interview_step_metric(example, prediction)
        assert score < 0.5


class TestTextExtractorMetric:
    def test_perfect_extraction(self) -> None:
        example = _make_example(
            field_schema="{}",
            current_data="{}",
            missing_fields="[]",
            user_message="I'm 25 years old",
            expected_extracted={"age": 25},
        )
        prediction = MagicMock()
        prediction.response.extracted = {"age": 25}
        score = text_extractor_metric(example, prediction)
        assert score == 1.0

    def test_wrong_extraction(self) -> None:
        example = _make_example(
            field_schema="{}",
            current_data="{}",
            missing_fields="[]",
            user_message="I'm 25",
            expected_extracted={"age": 25},
        )
        prediction = MagicMock()
        prediction.response.extracted = {"age": 30}
        score = text_extractor_metric(example, prediction)
        assert score < 1.0

    def test_spurious_extraction_penalized(self) -> None:
        example = _make_example(
            field_schema="{}",
            current_data="{}",
            missing_fields="[]",
            user_message="I'm 25",
            expected_extracted={"age": 25},
        )
        prediction = MagicMock()
        prediction.response.extracted = {"age": 25, "name": "unknown", "city": "NYC"}
        score = text_extractor_metric(example, prediction)
        assert score < 1.0

    def test_empty_expected(self) -> None:
        example = _make_example(
            field_schema="{}",
            current_data="{}",
            missing_fields="[]",
            user_message="hello",
            expected_extracted={},
        )
        prediction = MagicMock()
        prediction.response.extracted = {}
        score = text_extractor_metric(example, prediction)
        assert score == 1.0
