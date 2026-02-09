from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InterviewStepExample(BaseModel):
    """A single training example for the InterviewStep module."""

    field_schema: str
    current_data: str
    missing_fields: str
    conversation_history: str
    expected_ui_blocks: list[dict[str, Any]]
    expected_field_bindings: list[str]


class TextExtractorExample(BaseModel):
    """A single training example for the TextDataExtractor module."""

    field_schema: str
    current_data: str
    missing_fields: str
    user_message: str
    expected_extracted: dict[str, Any]
    expected_unresolved: str | None = None


class TrainingDataset(BaseModel):
    """Collection of examples for both modules."""

    interview_step_examples: list[InterviewStepExample] = []
    text_extractor_examples: list[TextExtractorExample] = []
