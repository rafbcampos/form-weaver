from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from interview.engine.orchestrator import InterviewOrchestrator
from interview.engine.schema_analyzer import get_missing_fields, is_complete
from interview.models.api import (
    StartRequest,
    StartResponse,
    StatusResponse,
    SubmitRequest,
    SubmitResponse,
)
from interview.session.store import SessionStore

router = APIRouter(prefix="/api/interview")


def _get_orchestrator(request: Request) -> InterviewOrchestrator:
    return request.app.state.orchestrator  # type: ignore[no-any-return]


def _get_store(request: Request) -> SessionStore:
    return request.app.state.store  # type: ignore[no-any-return]


@router.post("/start", response_model=StartResponse)
async def start_interview(request: StartRequest, http_request: Request) -> StartResponse:
    orchestrator = _get_orchestrator(http_request)
    return orchestrator.start(request.schema_, request.initial_data)


@router.post("/{session_id}/submit", response_model=SubmitResponse)
async def submit(session_id: str, request: SubmitRequest, http_request: Request) -> SubmitResponse:
    store = _get_store(http_request)
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    orchestrator = _get_orchestrator(http_request)
    return orchestrator.submit(session_id, request)


@router.get("/{session_id}/status", response_model=StatusResponse)
async def get_status(session_id: str, http_request: Request) -> StatusResponse:
    store = _get_store(http_request)
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return StatusResponse(
        current_data=session.current_data,
        is_complete=is_complete(session.schema_, session.current_data),
        missing_fields=get_missing_fields(session.schema_, session.current_data),
    )
