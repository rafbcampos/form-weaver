from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import dspy

from interview.cli.schemas import (
    InterviewStepExample,
    TextExtractorExample,
    TrainingDataset,
)


def _interview_step_to_dspy(example: InterviewStepExample) -> dspy.Example:
    """Convert an InterviewStepExample to a dspy.Example."""
    return dspy.Example(
        field_schema=example.field_schema,
        current_data=example.current_data,
        missing_fields=example.missing_fields,
        conversation_history=example.conversation_history,
        response={"ui_blocks": example.expected_ui_blocks},
    ).with_inputs("field_schema", "current_data", "missing_fields", "conversation_history")


def _text_extractor_to_dspy(example: TextExtractorExample) -> dspy.Example:
    """Convert a TextExtractorExample to a dspy.Example."""
    response: dict[str, Any] = {"extracted": example.expected_extracted}
    if example.expected_unresolved is not None:
        response["unresolved"] = example.expected_unresolved
    return dspy.Example(
        field_schema=example.field_schema,
        current_data=example.current_data,
        missing_fields=example.missing_fields,
        user_message=example.user_message,
        response=response,
    ).with_inputs("field_schema", "current_data", "missing_fields", "user_message")


def load_interview_step_examples(path: Path) -> list[dspy.Example]:
    """Load JSON -> list of dspy.Example for InterviewStep."""
    dataset = load_dataset(path)
    return [_interview_step_to_dspy(ex) for ex in dataset.interview_step_examples]


def load_text_extractor_examples(path: Path) -> list[dspy.Example]:
    """Load JSON -> list of dspy.Example for TextDataExtractor."""
    dataset = load_dataset(path)
    return [_text_extractor_to_dspy(ex) for ex in dataset.text_extractor_examples]


def save_dataset(dataset: TrainingDataset, path: Path) -> None:
    """Save TrainingDataset to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset.model_dump(), indent=2))


def load_dataset(path: Path) -> TrainingDataset:
    """Load TrainingDataset from JSON."""
    return TrainingDataset.model_validate_json(path.read_text())
