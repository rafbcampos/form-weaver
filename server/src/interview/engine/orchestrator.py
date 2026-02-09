from __future__ import annotations

import json
from typing import Any

from interview.engine.dspy_modules import (
    create_interview_step,
    create_text_extractor,
)
from interview.engine.schema_analyzer import (
    flatten_schema,
    get_missing_fields,
    is_complete,
)
from interview.engine.validator import validate_data, validate_field
from interview.models.api import (
    StartResponse,
    SubmitRequest,
    SubmitResponse,
)
from interview.models.schema import InterviewSchema
from interview.models.session import ConversationTurn, Session
from interview.models.ui_blocks import TextBlock, UIBlock
from interview.session.store import SessionStore


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Deep merge updates into base, returning a new dict."""
    result = dict(base)
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _expand_bindings(flat: dict[str, Any]) -> dict[str, Any]:
    """Convert flat dot-notation bindings to nested dict.

    Handles both dot notation (a.b.c) and array indexing (a[0].b).
    """
    result: dict[str, Any] = {}
    for path, value in flat.items():
        _set_by_path(result, path, value)
    return result


def _set_by_path(obj: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict/list structure using dot-notation path."""
    parts = _parse_path(path)
    current: Any = obj

    for i, part in enumerate(parts[:-1]):
        next_part = parts[i + 1]
        if isinstance(part, int):
            while len(current) <= part:
                current.append({} if isinstance(next_part, str) else [])
            current = current[part]
        else:
            if part not in current:
                current[part] = [] if isinstance(next_part, int) else {}
            current = current[part]

    last = parts[-1]
    if isinstance(last, int):
        while len(current) <= last:
            current.append(None)
        current[last] = value
    else:
        current[last] = value


def _parse_path(path: str) -> list[str | int]:
    """Parse 'a.b[0].c' into ['a', 'b', 0, 'c']."""
    parts: list[str | int] = []
    current = ""
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if current:
                parts.append(current)
                current = ""
        elif ch == "[":
            if current:
                parts.append(current)
                current = ""
            j = path.index("]", i)
            parts.append(int(path[i + 1 : j]))
            i = j
        else:
            current += ch
        i += 1
    if current:
        parts.append(current)
    return parts


class InterviewOrchestrator:
    def __init__(
        self,
        store: SessionStore,
        interview_step: Any | None = None,
        text_extractor: Any | None = None,
    ) -> None:
        self._store = store
        self._interview_step = interview_step or create_interview_step()
        self._text_extractor = text_extractor or create_text_extractor()

    def start(
        self,
        schema: InterviewSchema,
        initial_data: dict[str, Any] | None = None,
    ) -> StartResponse:
        session = self._store.create(schema, initial_data or {})

        if is_complete(schema, session.current_data):
            session.is_complete = True
            self._store.update(session)
            return StartResponse(
                session_id=session.id,
                blocks=[TextBlock(value="All information has already been provided. Thank you!")],
                is_complete=True,
                current_data=session.current_data,
            )

        blocks = self._generate_next_step(session)
        session.conversation_history.append(
            ConversationTurn(
                role="assistant",
                content=json.dumps([b.model_dump() for b in blocks]),
            )
        )
        self._store.update(session)

        return StartResponse(
            session_id=session.id,
            blocks=blocks,
            is_complete=False,
            current_data=session.current_data,
        )

    def submit(self, session_id: str, request: SubmitRequest) -> SubmitResponse:
        session = self._store.get(session_id)
        if session is None:
            return SubmitResponse(
                blocks=[TextBlock(value="Session not found.")],
                is_complete=False,
                current_data={},
                errors={"_session": ["Session not found."]},
            )

        if request.type == "form":
            return self._handle_form_submission(session, request.data or {})
        return self._handle_text_message(session, request.text or "")

    def _handle_form_submission(
        self,
        session: Session,
        submitted_data: dict[str, Any],
    ) -> SubmitResponse:
        # Expand flat bindings to nested structure for validation
        expanded = _expand_bindings(submitted_data)

        # Merge with current data first to get the full picture for condition evaluation
        merged_for_validation = _deep_merge(session.current_data, expanded)
        errors = validate_data(submitted_data, session.schema_, merged_for_validation)

        if errors:
            return SubmitResponse(
                blocks=[TextBlock(value="Please fix the errors below and try again.")],
                is_complete=False,
                current_data=session.current_data,
                errors=errors,
            )

        # Merge valid data
        session.current_data = _deep_merge(session.current_data, expanded)

        session.conversation_history.append(
            ConversationTurn(
                role="user",
                content=json.dumps(submitted_data),
            )
        )

        if is_complete(session.schema_, session.current_data):
            session.is_complete = True
            self._store.update(session)
            blocks: list[UIBlock] = [
                TextBlock(
                    value="Thank you! I have all the information I need. "
                    "Here's a summary of what we collected."
                )
            ]
            return SubmitResponse(
                blocks=blocks,
                is_complete=True,
                current_data=session.current_data,
            )

        blocks = self._generate_next_step(session)
        session.conversation_history.append(
            ConversationTurn(
                role="assistant",
                content=json.dumps([b.model_dump() for b in blocks]),
            )
        )
        self._store.update(session)

        return SubmitResponse(
            blocks=blocks,
            is_complete=False,
            current_data=session.current_data,
        )

    def _handle_text_message(
        self,
        session: Session,
        text: str,
    ) -> SubmitResponse:
        missing = get_missing_fields(session.schema_, session.current_data)
        flat_schema = flatten_schema(session.schema_)

        extraction = self._text_extractor(
            field_schema=json.dumps({k: v.model_dump() for k, v in flat_schema.items()}, indent=2),
            current_data=json.dumps(session.current_data, indent=2),
            missing_fields=json.dumps(missing),
            user_message=text,
        )

        extracted = extraction.response.extracted
        if extracted:
            # Only merge fields that pass validation — invalid ones will be
            # re-collected via structured form elements in the next step
            valid_extracted: dict[str, Any] = {}
            for path, value in extracted.items():
                field = flat_schema.get(path)
                if field and not validate_field(value, field):
                    valid_extracted[path] = value

            if valid_extracted:
                expanded = _expand_bindings(valid_extracted)
                session.current_data = _deep_merge(session.current_data, expanded)

        session.conversation_history.append(ConversationTurn(role="user", content=text))
        if extracted:
            session.conversation_history.append(
                ConversationTurn(
                    role="system",
                    content=f"Extracted from message: {json.dumps(extracted)}",
                )
            )

        if is_complete(session.schema_, session.current_data):
            session.is_complete = True
            self._store.update(session)
            blocks: list[UIBlock] = [
                TextBlock(value="Thank you! I have all the information I need.")
            ]
            return SubmitResponse(
                blocks=blocks,
                is_complete=True,
                current_data=session.current_data,
            )

        blocks = self._generate_next_step(session)
        session.conversation_history.append(
            ConversationTurn(
                role="assistant",
                content=json.dumps([b.model_dump() for b in blocks]),
            )
        )
        self._store.update(session)

        return SubmitResponse(
            blocks=blocks,
            is_complete=False,
            current_data=session.current_data,
        )

    def _generate_next_step(self, session: Session) -> list[UIBlock]:
        missing = get_missing_fields(session.schema_, session.current_data)
        flat_schema = flatten_schema(session.schema_)

        schema_for_llm = {k: v.model_dump() for k, v in flat_schema.items()}

        result = self._interview_step(
            field_schema=json.dumps(schema_for_llm, indent=2),
            current_data=json.dumps(session.current_data, indent=2),
            missing_fields=json.dumps(missing),
            conversation_history=json.dumps([t.model_dump() for t in session.conversation_history]),
        )

        return list(result.response.ui_blocks)
