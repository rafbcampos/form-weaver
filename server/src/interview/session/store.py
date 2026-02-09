from __future__ import annotations

import uuid
from typing import Any, Protocol

from interview.models.schema import InterviewSchema
from interview.models.session import Session


class SessionStore(Protocol):
    def create(self, schema: InterviewSchema, initial_data: dict[str, Any]) -> Session: ...

    def get(self, session_id: str) -> Session | None: ...

    def update(self, session: Session) -> None: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, schema: InterviewSchema, initial_data: dict[str, Any]) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            schema_=schema,
            current_data=initial_data,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def update(self, session: Session) -> None:
        self._sessions[session.id] = session
