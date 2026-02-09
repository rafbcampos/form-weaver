from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from interview.engine.dspy_modules import InterviewStepOutput
from interview.engine.orchestrator import (
    InterviewOrchestrator,
    _deep_merge,
    _expand_bindings,
    _parse_path,
)
from interview.models.schema import FieldSchema, InterviewSchema, ValidationRule
from interview.models.ui_blocks import FormBlock, InputElement, TextBlock
from interview.session.store import InMemorySessionStore

# --- Utility function tests ---


def test_parse_path_simple():
    assert _parse_path("name") == ["name"]


def test_parse_path_nested():
    assert _parse_path("user.name") == ["user", "name"]


def test_parse_path_with_array():
    assert _parse_path("children[0].name") == ["children", 0, "name"]


def test_parse_path_deep():
    assert _parse_path("a.b[2].c.d") == ["a", "b", 2, "c", "d"]


def test_deep_merge_basic():
    base = {"a": 1, "b": {"c": 2}}
    updates = {"b": {"d": 3}, "e": 4}
    result = _deep_merge(base, updates)
    assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}


def test_deep_merge_overwrite():
    base = {"a": {"b": 1}}
    updates = {"a": {"b": 2}}
    result = _deep_merge(base, updates)
    assert result == {"a": {"b": 2}}


def test_deep_merge_no_mutate():
    base = {"a": {"b": 1}}
    updates = {"a": {"c": 2}}
    _deep_merge(base, updates)
    assert base == {"a": {"b": 1}}


def test_expand_bindings_simple():
    flat = {"user.name": "John", "user.age": 25}
    result = _expand_bindings(flat)
    assert result == {"user": {"name": "John", "age": 25}}


def test_expand_bindings_with_array():
    flat = {"children[0].name": "Alice", "children[0].age": 5}
    result = _expand_bindings(flat)
    assert result == {"children": [{"name": "Alice", "age": 5}]}


def test_expand_bindings_nested():
    flat = {"a.b.c": 1}
    result = _expand_bindings(flat)
    assert result == {"a": {"b": {"c": 1}}}


# --- Orchestrator class tests ---


def _simple_schema() -> InterviewSchema:
    return InterviewSchema(
        fields={
            "name": FieldSchema(
                type="string",
                label="Name",
                validation=[ValidationRule(type="required")],
            ),
            "age": FieldSchema(
                type="integer",
                label="Age",
                validation=[ValidationRule(type="required")],
            ),
        }
    )


def _mock_interview_step(ui_blocks: list[Any] | None = None) -> MagicMock:
    """Create a mock DSPy InterviewStep module."""
    mock = MagicMock()
    blocks = ui_blocks or [
        TextBlock(value="Hello! Let me collect some info."),
        FormBlock(
            elements=[
                InputElement(type="text", label="Name", binding="name"),
                InputElement(type="integer", label="Age", binding="age"),
            ]
        ),
    ]
    mock.return_value.response = InterviewStepOutput(ui_blocks=blocks)
    return mock


def _mock_text_extractor(extracted: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock DSPy TextDataExtractor module."""
    mock = MagicMock()
    mock.return_value.response.extracted = extracted or {}
    mock.return_value.response.unresolved = None
    return mock


class TestOrchestratorStart:
    def test_start_creates_session_and_returns_blocks(self):
        store = InMemorySessionStore()
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )
        schema = _simple_schema()

        response = orch.start(schema)

        assert response.session_id
        assert not response.is_complete
        assert len(response.blocks) == 2
        assert response.blocks[0].kind == "text"
        assert response.current_data == {}

    def test_start_with_complete_initial_data(self):
        store = InMemorySessionStore()
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )
        schema = _simple_schema()

        response = orch.start(schema, initial_data={"name": "John", "age": 30})

        assert response.is_complete
        assert response.blocks[0].kind == "text"

    def test_start_stores_session(self):
        store = InMemorySessionStore()
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )
        schema = _simple_schema()

        response = orch.start(schema)
        session = store.get(response.session_id)

        assert session is not None
        assert len(session.conversation_history) == 1
        assert session.conversation_history[0].role == "assistant"


class TestOrchestratorFormSubmission:
    def test_submit_form_data_merges_and_continues(self):
        store = InMemorySessionStore()
        step_mock = _mock_interview_step()
        # Use a schema with two fields, one optional, so partial submit succeeds
        schema = InterviewSchema(
            fields={
                "name": FieldSchema(
                    type="string",
                    label="Name",
                    validation=[ValidationRule(type="required")],
                ),
                "bio": FieldSchema(
                    type="text",
                    label="Bio",
                    validation=[],
                ),
            }
        )
        orch = InterviewOrchestrator(
            store=store,
            interview_step=step_mock,
            text_extractor=_mock_text_extractor(),
        )
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="form", data={"name": "John"})
        response = orch.submit(start_resp.session_id, submit_req)

        assert response.is_complete
        assert response.current_data == {"name": "John"}
        assert not response.errors

    def test_submit_form_completes_when_all_fields_provided(self):
        store = InMemorySessionStore()
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )
        schema = _simple_schema()
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="form", data={"name": "John", "age": 30})
        response = orch.submit(start_resp.session_id, submit_req)

        assert response.is_complete
        assert response.current_data == {"name": "John", "age": 30}

    def test_submit_form_returns_validation_errors(self):
        store = InMemorySessionStore()
        schema = InterviewSchema(
            fields={
                "age": FieldSchema(
                    type="integer",
                    label="Age",
                    validation=[
                        ValidationRule(type="required"),
                        ValidationRule(type="min", param=18, message="Must be 18+"),
                    ],
                ),
            }
        )
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="form", data={"age": 5})
        response = orch.submit(start_resp.session_id, submit_req)

        assert not response.is_complete
        assert "age" in response.errors

    def test_submit_to_nonexistent_session(self):
        store = InMemorySessionStore()
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=_mock_text_extractor(),
        )

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="form", data={"name": "John"})
        response = orch.submit("nonexistent-id", submit_req)

        assert not response.is_complete
        assert "_session" in response.errors


class TestOrchestratorTextMessage:
    def test_text_message_extracts_and_merges_data(self):
        store = InMemorySessionStore()
        extractor = _mock_text_extractor(extracted={"name": "John", "age": 30})
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=extractor,
        )
        schema = _simple_schema()
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="message", text="I'm John, 30 years old")
        response = orch.submit(start_resp.session_id, submit_req)

        assert response.is_complete
        assert response.current_data == {"name": "John", "age": 30}

    def test_text_message_with_no_extraction(self):
        store = InMemorySessionStore()
        extractor = _mock_text_extractor(extracted={})
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=extractor,
        )
        schema = _simple_schema()
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="message", text="hello there")
        response = orch.submit(start_resp.session_id, submit_req)

        assert not response.is_complete
        assert response.current_data == {}

    def test_text_message_partial_extraction_continues(self):
        store = InMemorySessionStore()
        extractor = _mock_text_extractor(extracted={"name": "Alice"})
        orch = InterviewOrchestrator(
            store=store,
            interview_step=_mock_interview_step(),
            text_extractor=extractor,
        )
        schema = _simple_schema()
        start_resp = orch.start(schema)

        from interview.models.api import SubmitRequest

        submit_req = SubmitRequest(type="message", text="My name is Alice")
        response = orch.submit(start_resp.session_id, submit_req)

        assert not response.is_complete
        assert response.current_data == {"name": "Alice"}
        # Should still have blocks for remaining fields
        assert len(response.blocks) > 0
