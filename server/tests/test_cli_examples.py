from __future__ import annotations

import json
from pathlib import Path

from interview.cli.examples import (
    load_dataset,
    load_interview_step_examples,
    load_text_extractor_examples,
    save_dataset,
)
from interview.cli.schemas import (
    InterviewStepExample,
    TextExtractorExample,
    TrainingDataset,
)


def _make_dataset() -> TrainingDataset:
    return TrainingDataset(
        interview_step_examples=[
            InterviewStepExample(
                field_schema=json.dumps({"name": {"type": "string"}}),
                current_data=json.dumps({}),
                missing_fields=json.dumps(["name"]),
                conversation_history=json.dumps([]),
                expected_ui_blocks=[
                    {"kind": "text", "value": "Hello!"},
                    {
                        "kind": "form",
                        "elements": [
                            {"kind": "input", "label": "Name", "binding": "name"},
                        ],
                    },
                ],
                expected_field_bindings=["name"],
            ),
        ],
        text_extractor_examples=[
            TextExtractorExample(
                field_schema=json.dumps({"age": {"type": "integer"}}),
                current_data=json.dumps({}),
                missing_fields=json.dumps(["age"]),
                user_message="I'm 25 years old",
                expected_extracted={"age": 25},
            ),
        ],
    )


class TestSaveLoadDataset:
    def test_round_trip(self, tmp_path: Path) -> None:
        dataset = _make_dataset()
        path = tmp_path / "test.json"
        save_dataset(dataset, path)

        loaded = load_dataset(path)
        assert len(loaded.interview_step_examples) == 1
        assert len(loaded.text_extractor_examples) == 1
        assert loaded.interview_step_examples[0].expected_field_bindings == ["name"]
        assert loaded.text_extractor_examples[0].expected_extracted == {"age": 25}

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        dataset = _make_dataset()
        path = tmp_path / "sub" / "dir" / "test.json"
        save_dataset(dataset, path)
        assert path.exists()


class TestLoadInterviewStepExamples:
    def test_converts_to_dspy_examples(self, tmp_path: Path) -> None:
        dataset = _make_dataset()
        path = tmp_path / "test.json"
        save_dataset(dataset, path)

        examples = load_interview_step_examples(path)
        assert len(examples) == 1

        ex = examples[0]
        assert "field_schema" in ex.inputs()
        assert "current_data" in ex.inputs()
        assert "missing_fields" in ex.inputs()
        assert "conversation_history" in ex.inputs()
        assert ex.response == {
            "ui_blocks": dataset.interview_step_examples[0].expected_ui_blocks,
        }


class TestLoadTextExtractorExamples:
    def test_converts_to_dspy_examples(self, tmp_path: Path) -> None:
        dataset = _make_dataset()
        path = tmp_path / "test.json"
        save_dataset(dataset, path)

        examples = load_text_extractor_examples(path)
        assert len(examples) == 1

        ex = examples[0]
        assert "field_schema" in ex.inputs()
        assert "user_message" in ex.inputs()
        assert ex.response == {"extracted": {"age": 25}}

    def test_includes_unresolved_when_present(self, tmp_path: Path) -> None:
        dataset = TrainingDataset(
            text_extractor_examples=[
                TextExtractorExample(
                    field_schema="{}",
                    current_data="{}",
                    missing_fields="[]",
                    user_message="I'm 25 and like cats",
                    expected_extracted={"age": 25},
                    expected_unresolved="like cats",
                ),
            ],
        )
        path = tmp_path / "test.json"
        save_dataset(dataset, path)

        examples = load_text_extractor_examples(path)
        assert examples[0].response == {"extracted": {"age": 25}, "unresolved": "like cats"}
