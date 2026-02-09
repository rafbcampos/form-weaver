from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

import dspy
from pydantic import BaseModel

from interview.cli.schemas import (
    InterviewStepExample,
    TextExtractorExample,
    TrainingDataset,
)
from interview.engine.schema_analyzer import flatten_schema, get_missing_fields
from interview.models.schema import FieldSchema, InterviewSchema

logger = logging.getLogger(__name__)


class SyntheticRecords(BaseModel):
    """Multiple complete data records."""

    records: list[dict[str, Any]]


class SyntheticMessage(BaseModel):
    """A natural language message expressing some field values."""

    message: str


class GenerateRecords(dspy.Signature):  # type: ignore[misc]
    """Generate realistic, diverse synthetic data records for a given schema.

    For each record, generate plausible values that match the field types,
    validation rules, and enum options defined in the schema.
    Vary the data across records — use different names, ages, locations,
    choices, etc. to create diversity.
    Return valid JSON matching the flattened dot-notation paths.
    """

    field_schema: str = dspy.InputField(desc="JSON schema with all field definitions (flattened)")
    count: int = dspy.InputField(desc="Number of records to generate")
    response: SyntheticRecords = dspy.OutputField()


class GenerateMessage(dspy.Signature):  # type: ignore[misc]
    """Generate a natural language message from a user providing some information.

    Given a subset of field values, write a casual, natural message as if a user
    were telling an interviewer these details in conversation. Don't use field names
    or technical terms — write like a real person would speak.
    """

    field_values: str = dspy.InputField(desc="JSON of field path -> value pairs to express")
    field_descriptions: str = dspy.InputField(desc="JSON of field path -> label/description")
    response: SyntheticMessage = dspy.OutputField()


def _build_field_descriptions(flat_schema: dict[str, FieldSchema]) -> dict[str, str]:
    """Build a mapping of field path -> human-readable description."""
    descriptions: dict[str, str] = {}
    for path, field in flat_schema.items():
        desc = field.label or path.split(".")[-1].replace("_", " ").title()
        if field.description:
            desc += f" ({field.description})"
        if field.options:
            desc += f" [options: {', '.join(o.value for o in field.options)}]"
        descriptions[path] = desc
    return descriptions


def _select_field_subset(
    all_fields: list[str],
    min_count: int = 1,
    max_count: int | None = None,
) -> list[str]:
    """Select a random subset of fields."""
    if max_count is None:
        max_count = min(len(all_fields), 5)
    count = random.randint(min_count, max(min_count, max_count))  # noqa: S311
    return random.sample(all_fields, min(count, len(all_fields)))


def _extract_values_for_fields(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Extract values for specific dot-notation field paths from a record."""
    values: dict[str, Any] = {}
    for field in fields:
        if field in record:
            values[field] = record[field]
    return values


def _build_expected_ui_blocks(
    bindings: list[str], flat_schema: dict[str, FieldSchema]
) -> list[dict[str, Any]]:
    """Build expected UI blocks for a set of field bindings."""
    blocks: list[dict[str, Any]] = [
        {"kind": "text", "value": "Let me collect some information from you."}
    ]
    elements: list[dict[str, Any]] = []
    for binding in bindings:
        field = flat_schema.get(binding)
        if not field:
            continue
        element: dict[str, Any] = {"label": field.label or binding, "binding": binding}
        if field.type == "enum" and field.options:
            if len(field.options) <= 4:
                element["kind"] = "radio"
            else:
                element["kind"] = "select"
            element["options"] = [{"value": o.value, "label": o.label} for o in field.options]
        elif field.type == "boolean":
            element["kind"] = "checkbox"
        elif field.type == "text":
            element["kind"] = "textarea"
        elif field.type in ("integer", "float", "date"):
            element["kind"] = "input"
            element["type"] = field.type
        else:
            element["kind"] = "input"
            element["type"] = "text"
        elements.append(element)

    if elements:
        blocks.append({"kind": "form", "elements": elements})
    return blocks


def generate_training_data(
    schema_path: Path,
    count: int = 10,
) -> TrainingDataset:
    """Generate synthetic training examples by simulating interviews.

    1. Load schema and flatten it
    2. Use LLM to generate complete data records
    3. For each record, create interview step examples at various progression stages
    4. Generate text messages and expected extractions
    """
    schema_json = json.loads(schema_path.read_text())
    schema = InterviewSchema.model_validate(schema_json)
    flat_schema = flatten_schema(schema)
    field_descriptions = _build_field_descriptions(flat_schema)

    schema_str = json.dumps({k: v.model_dump() for k, v in flat_schema.items()}, indent=2)
    all_field_paths = list(flat_schema.keys())

    # Generate synthetic records
    logger.info("Generating %d synthetic records...", count)
    record_generator = dspy.ChainOfThought(GenerateRecords)
    result = record_generator(field_schema=schema_str, count=count)
    records = result.response.records

    logger.info("Generated %d records, creating training examples...", len(records))

    interview_examples: list[InterviewStepExample] = []
    text_examples: list[TextExtractorExample] = []
    message_generator = dspy.ChainOfThought(GenerateMessage)

    for record in records:
        # Stage 1: Empty state — all fields missing (first turn)
        missing = get_missing_fields(schema, {})
        if missing:
            bindings_to_ask = missing[:5]
            expected_blocks = _build_expected_ui_blocks(bindings_to_ask, flat_schema)
            interview_examples.append(
                InterviewStepExample(
                    field_schema=schema_str,
                    current_data=json.dumps({}),
                    missing_fields=json.dumps(missing),
                    conversation_history=json.dumps([]),
                    expected_ui_blocks=expected_blocks,
                    expected_field_bindings=bindings_to_ask,
                )
            )

        # Stage 2: Intermediate states — incrementally add fields
        collected: dict[str, Any] = {}
        fields_in_order = list(record.keys())
        random.shuffle(fields_in_order)

        num_stages = min(3, len(fields_in_order) // 2)
        chunk_size = max(1, len(fields_in_order) // (num_stages + 1))

        for stage_idx in range(num_stages):
            # Add a chunk of fields to collected
            start = stage_idx * chunk_size
            end = start + chunk_size
            for field_path in fields_in_order[start:end]:
                if field_path in record:
                    collected[field_path] = record[field_path]

            still_missing = [f for f in all_field_paths if f not in collected]
            if not still_missing:
                break

            bindings_to_ask = still_missing[:5]
            expected_blocks = _build_expected_ui_blocks(bindings_to_ask, flat_schema)
            interview_examples.append(
                InterviewStepExample(
                    field_schema=schema_str,
                    current_data=json.dumps(collected),
                    missing_fields=json.dumps(still_missing),
                    conversation_history=json.dumps([]),
                    expected_ui_blocks=expected_blocks,
                    expected_field_bindings=bindings_to_ask,
                )
            )

        # Stage 3: Generate text extraction examples
        remaining_fields = [f for f in all_field_paths if f not in collected]
        if remaining_fields:
            subset = _select_field_subset(remaining_fields, min_count=1, max_count=3)
            values = _extract_values_for_fields(record, subset)

            if values:
                try:
                    msg_result = message_generator(
                        field_values=json.dumps(values),
                        field_descriptions=json.dumps(
                            {k: field_descriptions[k] for k in values if k in field_descriptions}
                        ),
                    )
                    message = msg_result.response.message

                    text_examples.append(
                        TextExtractorExample(
                            field_schema=schema_str,
                            current_data=json.dumps(collected),
                            missing_fields=json.dumps(remaining_fields),
                            user_message=message,
                            expected_extracted=values,
                        )
                    )
                except Exception:
                    logger.warning("Failed to generate message for record, skipping")

        # Stage 4: Near-completion example (1-2 fields left)
        almost_complete = dict(record)
        fields_to_remove = _select_field_subset(list(record.keys()), min_count=1, max_count=2)
        for f in fields_to_remove:
            almost_complete.pop(f, None)

        still_missing = [f for f in all_field_paths if f not in almost_complete]
        if still_missing:
            bindings_to_ask = still_missing[:5]
            expected_blocks = _build_expected_ui_blocks(bindings_to_ask, flat_schema)
            interview_examples.append(
                InterviewStepExample(
                    field_schema=schema_str,
                    current_data=json.dumps(almost_complete),
                    missing_fields=json.dumps(still_missing),
                    conversation_history=json.dumps([]),
                    expected_ui_blocks=expected_blocks,
                    expected_field_bindings=bindings_to_ask,
                )
            )

    logger.info(
        "Generated %d interview step examples and %d text extractor examples",
        len(interview_examples),
        len(text_examples),
    )

    return TrainingDataset(
        interview_step_examples=interview_examples,
        text_extractor_examples=text_examples,
    )
