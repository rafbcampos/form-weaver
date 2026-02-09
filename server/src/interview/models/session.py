from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from interview.models.schema import InterviewSchema


class ConversationTurn(BaseModel):
    role: str
    content: str


class Session(BaseModel):
    id: str
    schema_: InterviewSchema = Field(alias="schema")
    current_data: dict[str, Any] = {}
    conversation_history: list[ConversationTurn] = []
    is_complete: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
