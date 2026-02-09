from __future__ import annotations

from typing import Any

import dspy
from pydantic import BaseModel

from interview.models.ui_blocks import UIBlock


class InterviewStepOutput(BaseModel):
    ui_blocks: list[UIBlock]


class InterviewStep(dspy.Signature):  # type: ignore[misc]
    """Generate the next step in a conversational data-collection interview.

    You are a friendly interviewer collecting information from a user.
    Given a JSON schema of all fields, the data already collected, and
    the list of fields still missing, produce a list of UI blocks that
    combine natural conversational text with embedded form elements.

    Rules for generating UI blocks:
    - Always start with a TextBlock containing a conversational message.
    - Group related missing fields together in a single FormBlock.
    - Do NOT ask for fields already collected unless they have errors.
    - Ask for 3-5 fields at a time maximum to avoid overwhelming the user.
    - Use the correct element kind based on the field schema type:
      * string/text → "input" (type="text") or "textarea" for long text
      * integer → "input" (type="integer")
      * float → "input" (type="float")
      * date → "input" (type="date")
      * boolean → "checkbox"
      * enum → "select" or "radio" (use radio for ≤4 options)
      * array → "array" with item_elements
    - The "binding" field must match the dot-notation path of the schema field.
    - For enum fields, include the options from the schema.
    - Use natural, warm language — you're having a conversation, not filling a form.
    """

    field_schema: str = dspy.InputField(desc="JSON schema with all field definitions")
    current_data: str = dspy.InputField(desc="JSON of data already collected from the user")
    missing_fields: str = dspy.InputField(
        desc="JSON list of dot-notation paths for fields still needed"
    )
    conversation_history: str = dspy.InputField(desc="Previous conversation turns as JSON")
    response: InterviewStepOutput = dspy.OutputField()


class ExtractedData(BaseModel):
    extracted: dict[str, Any]
    unresolved: str | None = None


class TextDataExtractor(dspy.Signature):  # type: ignore[misc]
    """Extract structured data from a user's free-text message.

    Given the schema context and missing fields, parse the user's
    natural language message and extract any field values that can be
    mapped to schema fields.

    Rules:
    - Map extracted values to their dot-notation field paths.
    - Convert values to the correct types (e.g., "25" → 25 for integers).
    - For enum fields, match to the closest option value.
    - If part of the message cannot be mapped, include it in "unresolved".
    - Only extract values you are confident about — do not guess.
    """

    field_schema: str = dspy.InputField(desc="JSON schema with field definitions")
    current_data: str = dspy.InputField(desc="JSON of data already collected")
    missing_fields: str = dspy.InputField(
        desc="JSON list of dot-notation paths for fields still needed"
    )
    user_message: str = dspy.InputField(desc="The user's free-text message to extract data from")
    response: ExtractedData = dspy.OutputField()


def create_interview_step() -> dspy.Module:
    return dspy.ChainOfThought(InterviewStep)


def create_text_extractor() -> dspy.Module:
    return dspy.ChainOfThought(TextDataExtractor)
