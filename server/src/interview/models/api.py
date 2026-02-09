from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from interview.models.schema import InterviewSchema
from interview.models.ui_blocks import UIBlock


class StartRequest(BaseModel):
    schema_: InterviewSchema = Field(default=InterviewSchema(fields={}), alias="schema")
    initial_data: dict[str, Any] = {}

    model_config = {"populate_by_name": True}


class StartResponse(BaseModel):
    session_id: str
    blocks: list[UIBlock]
    is_complete: bool
    current_data: dict[str, Any]


class SubmitRequest(BaseModel):
    type: Literal["form", "message"]
    data: dict[str, Any] | None = None
    text: str | None = None


class SubmitResponse(BaseModel):
    blocks: list[UIBlock]
    is_complete: bool
    current_data: dict[str, Any]
    errors: dict[str, list[str]] = {}


class StatusResponse(BaseModel):
    current_data: dict[str, Any]
    is_complete: bool
    missing_fields: list[str]
