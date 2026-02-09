from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from interview.engine.dspy_modules import InterviewStepOutput
from interview.main import create_app
from interview.models.ui_blocks import FormBlock, InputElement, TextBlock
from interview.session.store import InMemorySessionStore


def _mock_interview_step() -> MagicMock:
    mock = MagicMock()
    blocks = [
        TextBlock(value="Hello!"),
        FormBlock(
            elements=[
                InputElement(type="text", label="Name", binding="name"),
            ]
        ),
    ]
    mock.return_value.response = InterviewStepOutput(ui_blocks=blocks)
    return mock


def _mock_text_extractor(extracted: dict[str, Any] | None = None) -> MagicMock:
    mock = MagicMock()
    mock.return_value.response.extracted = extracted or {}
    mock.return_value.response.unresolved = None
    return mock


def _create_test_client() -> TestClient:
    """Create a test client with mocked DSPy modules."""
    app = create_app()
    store = InMemorySessionStore()

    from interview.engine.orchestrator import InterviewOrchestrator

    app.state.orchestrator = InterviewOrchestrator(
        store=store,
        interview_step=_mock_interview_step(),
        text_extractor=_mock_text_extractor(),
    )
    app.state.store = store
    return TestClient(app, raise_server_exceptions=False)


SIMPLE_SCHEMA = {
    "fields": {
        "name": {
            "type": "string",
            "label": "Name",
            "validation": [{"type": "required"}],
        },
    }
}


class TestStartEndpoint:
    def test_start_returns_session_and_blocks(self):
        client = _create_test_client()
        response = client.post("/api/interview/start", json={"schema": SIMPLE_SCHEMA})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "blocks" in data
        assert data["is_complete"] is False

    def test_start_with_empty_schema(self):
        client = _create_test_client()
        response = client.post("/api/interview/start", json={"schema": {"fields": {}}})

        assert response.status_code == 200
        data = response.json()
        assert data["is_complete"] is True


class TestSubmitEndpoint:
    def test_submit_form_data(self):
        client = _create_test_client()
        start_resp = client.post("/api/interview/start", json={"schema": SIMPLE_SCHEMA})
        session_id = start_resp.json()["session_id"]

        response = client.post(
            f"/api/interview/{session_id}/submit",
            json={"type": "form", "data": {"name": "John"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_data"] == {"name": "John"}
        assert data["is_complete"] is True

    def test_submit_text_message(self):
        client = _create_test_client()
        start_resp = client.post("/api/interview/start", json={"schema": SIMPLE_SCHEMA})
        session_id = start_resp.json()["session_id"]

        response = client.post(
            f"/api/interview/{session_id}/submit",
            json={"type": "message", "text": "My name is John"},
        )

        assert response.status_code == 200

    def test_submit_to_nonexistent_session(self):
        client = _create_test_client()
        response = client.post(
            "/api/interview/nonexistent/submit",
            json={"type": "form", "data": {"name": "John"}},
        )

        assert response.status_code == 404


class TestStatusEndpoint:
    def test_get_status(self):
        client = _create_test_client()
        start_resp = client.post("/api/interview/start", json={"schema": SIMPLE_SCHEMA})
        session_id = start_resp.json()["session_id"]

        response = client.get(f"/api/interview/{session_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert "current_data" in data
        assert "is_complete" in data
        assert "missing_fields" in data

    def test_get_status_nonexistent_session(self):
        client = _create_test_client()
        response = client.get("/api/interview/nonexistent/status")

        assert response.status_code == 404
